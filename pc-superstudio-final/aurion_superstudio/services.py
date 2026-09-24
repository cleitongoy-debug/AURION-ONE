from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from PIL import Image, ImageEnhance, ImageFilter, ImageOps


def safe_name(name: str) -> str:
    keep = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
    cleaned = "".join(ch if ch in keep else "_" for ch in Path(name).name)
    return cleaned[:180] or f"arquivo_{int(time.time())}"


def unique_path(folder: Path, filename: str) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / safe_name(filename)
    if not target.exists():
        return target
    for number in range(1, 10000):
        candidate = target.with_name(f"{target.stem}_{number:03d}{target.suffix}")
        if not candidate.exists():
            return candidate
    raise RuntimeError("Não foi possível criar um nome de arquivo único.")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def http_json(url: str, method: str = "GET", payload: dict | None = None, timeout: float = 3) -> dict:
    started = time.perf_counter()
    try:
        response = requests.request(method, url, json=payload, timeout=timeout)
        elapsed = round((time.perf_counter() - started) * 1000)
        data = response.json() if response.content else {}
        return {"ok": response.ok, "status": response.status_code, "ms": elapsed, "data": data}
    except Exception as exc:
        return {"ok": False, "status": None, "ms": None, "error": f"{type(exc).__name__}: {exc}"}


def service_status(config: dict) -> dict:
    ollama = http_json(config["ollama"].rstrip("/") + "/api/tags", timeout=2)
    comfy_stats = http_json(config["comfy"].rstrip("/") + "/system_stats", timeout=2)
    original = http_json(config["panel"].rstrip("/") + "/health", timeout=2)
    models = []
    if ollama.get("ok"):
        models = [m.get("name") for m in ollama.get("data", {}).get("models", []) if m.get("name")]
    checkpoints = []
    object_info = None
    if comfy_stats.get("ok"):
        object_info = http_json(config["comfy"].rstrip("/") + "/object_info/CheckpointLoaderSimple", timeout=4)
        try:
            checkpoints = object_info["data"]["CheckpointLoaderSimple"]["input"]["required"]["ckpt_name"][0]
        except (KeyError, TypeError, IndexError):
            checkpoints = []
    return {
        "panel": original,
        "ollama": {**ollama, "models": models},
        "comfy": {**comfy_stats, "checkpoints": checkpoints, "catalog_ok": bool(object_info and object_info.get("ok"))},
    }


def inventory_base(base_root: Path) -> dict:
    names = ["ADAPTA.py", "ADAPTA_BASE_TRAVADA.py", "FUNCIONANDO.py", "AURION_ONE_FUNCIONANDO_v2.py"]
    files = []
    for name in names:
        path = base_root / name
        if path.is_file():
            files.append({"name": name, "size": path.stat().st_size, "sha256": sha256(path), "read_only": True})
    return {"root": str(base_root), "files": files, "protected": ["ADAPTA.py", "ADAPTA_BASE_TRAVADA.py"]}


def process_image(source: Path, output: Path, params: dict) -> dict:
    with Image.open(source) as original:
        image = ImageOps.exif_transpose(original).convert("RGB")
        image = ImageEnhance.Brightness(image).enhance(float(params.get("brightness", 1)))
        image = ImageEnhance.Contrast(image).enhance(float(params.get("contrast", 1)))
        image = ImageEnhance.Color(image).enhance(float(params.get("saturation", 1)))
        sharpness = float(params.get("sharpness", 1))
        image = ImageEnhance.Sharpness(image).enhance(sharpness)
        effect = params.get("effect", "none")
        if effect == "noir":
            image = ImageOps.grayscale(image).convert("RGB")
        elif effect == "warm":
            r, g, b = image.split()
            image = Image.merge("RGB", (r.point(lambda x: min(255, x * 1.08)), g, b.point(lambda x: x * .92)))
        elif effect == "cool":
            r, g, b = image.split()
            image = Image.merge("RGB", (r.point(lambda x: x * .92), g, b.point(lambda x: min(255, x * 1.08))))
        elif effect == "soft":
            image = image.filter(ImageFilter.GaussianBlur(radius=1.2))
        quality = max(40, min(100, int(params.get("quality", 95))))
        output.parent.mkdir(parents=True, exist_ok=True)
        image.save(output, quality=quality)
        return {"width": image.width, "height": image.height, "mode": image.mode, "quality": quality}


def develop_cr3(source: Path, output: Path, params: dict) -> dict:
    try:
        import rawpy
        import imageio.v3 as iio
    except ImportError as exc:
        raise RuntimeError("Suporte CR3 opcional ausente. Execute INSTALAR_SUPORTE_T8I.cmd.") from exc
    with rawpy.imread(str(source)) as raw:
        rgb = raw.postprocess(
            use_camera_wb=True,
            no_auto_bright=False,
            bright=float(params.get("brightness", 1.0)),
            output_bps=8,
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    iio.imwrite(output, rgb, quality=max(40, min(100, int(params.get("quality", 95)))))
    return {"output": str(output), "sha256": sha256(output)}


def validate_local_url(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return host in {"127.0.0.1", "localhost", "::1"} or host.startswith("192.168.") or host.startswith("10.") or host.endswith(".ts.net")


def run_ffmpeg(ffmpeg: str, source: Path, output: Path, mode: str, start: float, end: float) -> dict:
    if not shutil.which(ffmpeg):
        raise RuntimeError("FFmpeg não encontrado no PATH.")
    duration = max(0.1, end - start)
    cmd = [ffmpeg, "-hide_banner", "-y", "-ss", str(max(0, start)), "-i", str(source), "-t", str(duration)]
    if mode == "audio-wav":
        cmd += ["-vn", "-c:a", "pcm_s16le", str(output)]
    elif mode == "video-mp4":
        cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-c:a", "aac", "-b:a", "192k", str(output)]
    else:
        raise ValueError("Modo de conversão inválido.")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    if result.returncode:
        raise RuntimeError(result.stderr[-2000:] or "FFmpeg retornou erro.")
    return {"output": str(output), "sha256": sha256(output), "command": cmd}

