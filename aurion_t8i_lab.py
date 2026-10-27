# -*- coding: utf-8 -*-
"""AURION ONE · T8I RAW LAB

Camada local e aditiva para organizar, preservar e revelar arquivos RAW/CR3.
O arquivo original nunca e alterado. Todo projeto cria trilha persistente com
manifesto, indice, conversas, logs, ajustes, snapshots e artefatos derivados.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LOCK = threading.RLock()
RAW_EXTS = {".cr3", ".cr2"}
MEDIA_EXTS = RAW_EXTS | {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".mp4", ".mov"}
PROJECT_DIRNAME = ".aurion_t8i"


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _safe_name(value: str) -> str:
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", str(value or "").strip())
    value = re.sub(r"\s+", " ", value).strip(" .")
    return value[:120] or "Projeto_T8I"


def _atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=str(path.parent),
            prefix=path.stem + "_",
            suffix=".tmp",
            delete=False,
        ) as fh:
            temp = Path(fh.name)
            json.dump(payload, fh, ensure_ascii=False, indent=2)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(temp, path)
    finally:
        if temp and temp.exists():
            temp.unlink(missing_ok=True)


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def _read_json(path: Path, default: Any) -> Any:
    try:
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    return default


def _read_jsonl(path: Path, limit: int = 200) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    continue
    except OSError:
        return []
    return rows[-max(1, min(int(limit), 2000)):]


def sha256_file(path: Path, block_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            block = fh.read(block_size)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def dependency_status() -> dict[str, Any]:
    modules: dict[str, Any] = {}
    for name, import_name in (("rawpy", "rawpy"), ("Pillow", "PIL"), ("numpy", "numpy")):
        try:
            mod = importlib.import_module(import_name)
            modules[name] = {"ok": True, "version": getattr(mod, "__version__", "instalado")}
        except Exception as exc:
            modules[name] = {"ok": False, "error": str(exc)[:300]}
    exiftool = shutil.which("exiftool") or shutil.which("exiftool.exe")
    return {
        "python": sys.executable,
        "python_version": sys.version.split()[0],
        "modules": modules,
        "exiftool": exiftool,
        "ready": all(v.get("ok") for v in modules.values()),
        "note": "ExifTool e opcional; RAW T8i/CR3 e revelado por rawpy/LibRaw.",
    }


def install_dependencies(timeout: int = 900) -> dict[str, Any]:
    before = dependency_status()
    if before["ready"]:
        return {"ok": True, "changed": False, "before": before, "after": before, "output": "Dependencias T8I ja presentes."}
    cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--disable-pip-version-check",
        "--no-input",
        "rawpy>=0.25,<0.28",
        "Pillow>=10,<12",
        "numpy>=1.26,<3",
    ]
    try:
        cp = subprocess.run(cmd, capture_output=True, text=True, timeout=max(60, min(int(timeout), 1200)), shell=False)
        importlib.invalidate_caches()
        after = dependency_status()
        out = (cp.stdout or "") + ("\n" + cp.stderr if cp.stderr else "")
        return {
            "ok": cp.returncode == 0 and after["ready"],
            "changed": True,
            "returncode": cp.returncode,
            "command": [str(x) for x in cmd],
            "before": before,
            "after": after,
            "output": out[-12000:],
        }
    except Exception as exc:
        return {"ok": False, "changed": False, "before": before, "after": dependency_status(), "error": str(exc)[:1000]}


def pick_directory(initial: str = "") -> dict[str, Any]:
    initial_path = str(Path(initial).expanduser()) if initial else str(Path.home())
    script = (
        "import json, tkinter as tk\n"
        "from tkinter import filedialog\n"
        "root=tk.Tk(); root.withdraw(); root.attributes('-topmost', True)\n"
        f"p=filedialog.askdirectory(initialdir={json.dumps(initial_path)})\n"
        "print(json.dumps({'path':p}, ensure_ascii=False))\n"
        "root.destroy()\n"
    )
    try:
        cp = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, timeout=180, shell=False)
        if cp.returncode != 0:
            return {"ok": False, "error": (cp.stderr or "Seletor de pasta falhou.")[-2000:]}
        data = json.loads((cp.stdout or "{}").strip().splitlines()[-1])
        path = str(data.get("path", "")).strip()
        return {"ok": bool(path), "path": path, "cancelled": not bool(path)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:1000]}


def _workspace_root(workspace: str | Path) -> Path:
    root = Path(workspace).expanduser().resolve()
    marker = root / PROJECT_DIRNAME / "manifest.json"
    if not marker.is_file():
        raise ValueError("Workspace T8I invalido: manifesto nao encontrado.")
    return root


def create_workspace(base_dir: str, name: str) -> dict[str, Any]:
    base = Path(base_dir).expanduser().resolve()
    if not base.is_dir():
        raise ValueError("Pasta base inexistente.")
    root = base / _safe_name(name)
    meta = root / PROJECT_DIRNAME
    with LOCK:
        for folder in (
            root,
            meta,
            root / "originals",
            root / "previews",
            root / "exports",
            root / "metadata",
            root / "conversations",
            root / "logs",
            root / "snapshots",
        ):
            folder.mkdir(parents=True, exist_ok=True)
        manifest_path = meta / "manifest.json"
        manifest = _read_json(
            manifest_path,
            {
                "schema": 1,
                "project": root.name,
                "created_at": _now(),
                "workspace": str(root),
                "camera_family": "Canon EOS 850D / Rebel T8i",
                "source_policy": "originais preservados; derivados gravados separadamente",
            },
        )
        manifest["last_opened_at"] = _now()
        _atomic_json(manifest_path, manifest)
        settings = meta / "settings.json"
        if not settings.exists():
            _atomic_json(
                settings,
                {
                    "wb_mode": "camera",
                    "exposure_ev": 0.0,
                    "contrast": 0,
                    "saturation": 0,
                    "temperature": 0,
                    "tint": 0,
                    "sharpness": 0,
                    "half_size": True,
                    "output_format": "JPEG",
                    "jpeg_quality": 92,
                    "copy_original": True,
                },
            )
        _append_jsonl(root / "logs" / "actions.jsonl", {"at": _now(), "action": "workspace_create_or_open", "workspace": str(root)})
    return load_workspace(str(root))


def discover_cr3(folder: str, max_files: int = 1200) -> dict[str, Any]:
    root = Path(folder).expanduser().resolve()
    if not root.is_dir():
        raise ValueError("Pasta de origem inexistente.")
    cap = max(1, min(int(max_files), 5000))
    items: list[dict[str, Any]] = []
    errors: list[str] = []
    for current, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d.lower() not in {"$recycle.bin", "system volume information", "node_modules", ".git", "__pycache__"}]
        for name in files:
            if Path(name).suffix.lower() not in RAW_EXTS:
                continue
            p = Path(current) / name
            try:
                st = p.stat()
                items.append({"path": str(p), "name": p.name, "bytes": st.st_size, "modified": datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds")})
            except OSError as exc:
                errors.append(f"{p}: {exc}")
            if len(items) >= cap:
                return {"ok": True, "root": str(root), "files": items, "truncated": True, "errors": errors[-50:]}
    return {"ok": True, "root": str(root), "files": items, "truncated": False, "errors": errors[-50:]}


def _unique_target(folder: Path, name: str) -> Path:
    target = folder / name
    if not target.exists():
        return target
    stem, suffix = target.stem, target.suffix
    for i in range(1, 10000):
        candidate = folder / f"{stem}_{i:03d}{suffix}"
        if not candidate.exists():
            return candidate
    raise RuntimeError("Nao foi possivel criar nome unico para o arquivo.")


def ingest_files(workspace: str, files: list[str], copy_original: bool = True) -> dict[str, Any]:
    root = _workspace_root(workspace)
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    index_path = root / PROJECT_DIRNAME / "files.jsonl"
    with LOCK:
        for raw_value in files[:2000]:
            src = Path(str(raw_value)).expanduser().resolve()
            if not src.is_file():
                rejected.append({"path": str(src), "error": "arquivo inexistente"})
                continue
            if src.suffix.lower() not in MEDIA_EXTS:
                rejected.append({"path": str(src), "error": "extensao nao suportada nesta aba"})
                continue
            try:
                src_hash = sha256_file(src)
                dest = src
                copied = False
                if copy_original:
                    dest = _unique_target(root / "originals", src.name)
                    shutil.copy2(src, dest)
                    copied = True
                st = src.stat()
                rec = {
                    "at": _now(),
                    "source": str(src),
                    "stored": str(dest),
                    "copied": copied,
                    "name": src.name,
                    "extension": src.suffix.lower(),
                    "bytes": st.st_size,
                    "sha256": src_hash,
                }
                _append_jsonl(index_path, rec)
                accepted.append(rec)
            except Exception as exc:
                rejected.append({"path": str(src), "error": str(exc)[:500]})
        _append_jsonl(root / "logs" / "actions.jsonl", {"at": _now(), "action": "ingest", "accepted": len(accepted), "rejected": len(rejected), "copy_original": bool(copy_original)})
    return {"ok": not rejected or bool(accepted), "workspace": str(root), "accepted": accepted, "rejected": rejected}


def _exiftool_json(path: Path) -> dict[str, Any] | None:
    exe = shutil.which("exiftool") or shutil.which("exiftool.exe")
    if not exe:
        return None
    try:
        cp = subprocess.run([exe, "-json", "-n", str(path)], capture_output=True, text=True, timeout=30, shell=False)
        if cp.returncode == 0:
            data = json.loads(cp.stdout or "[]")
            if isinstance(data, list) and data:
                return data[0]
    except Exception:
        return None
    return None


def raw_metadata(path: str) -> dict[str, Any]:
    src = Path(path).expanduser().resolve()
    if not src.is_file():
        raise ValueError("RAW inexistente.")
    try:
        import rawpy
    except Exception as exc:
        raise RuntimeError("rawpy nao instalado. Use INSTALAR/CORRIGIR DEPENDENCIAS.") from exc
    with rawpy.imread(str(src)) as raw:
        sizes = raw.sizes
        basic = {
            "raw_type": str(raw.raw_type),
            "visible_width": int(sizes.width),
            "visible_height": int(sizes.height),
            "raw_width": int(sizes.raw_width),
            "raw_height": int(sizes.raw_height),
            "flip": int(sizes.flip),
            "black_level_per_channel": [int(x) for x in raw.black_level_per_channel],
            "white_level": int(raw.white_level),
            "camera_whitebalance": [float(x) for x in (raw.camera_whitebalance or [])],
            "daylight_whitebalance": [float(x) for x in (raw.daylight_whitebalance or [])],
            "color_desc": bytes(raw.color_desc).decode("ascii", errors="ignore") if raw.color_desc is not None else "",
        }
    exif = _exiftool_json(src)
    return {"source": str(src), "sha256": sha256_file(src), "raw": basic, "exif": exif, "exiftool_available": exif is not None}


def _clamp(value: Any, low: float, high: float, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default
    return max(low, min(high, number))


def render_preview(workspace: str, source: str, settings: dict[str, Any] | None = None) -> dict[str, Any]:
    root = _workspace_root(workspace)
    src = Path(source).expanduser().resolve()
    if not src.is_file() or src.suffix.lower() not in RAW_EXTS:
        raise ValueError("Selecione um arquivo .CR3 ou .CR2 real.")
    settings = dict(settings or {})
    try:
        import numpy as np
        import rawpy
        from PIL import Image, ImageEnhance
    except Exception as exc:
        raise RuntimeError("Dependencias RAW ausentes. Use INSTALAR/CORRIGIR DEPENDENCIAS.") from exc

    ev = _clamp(settings.get("exposure_ev", 0), -2.0, 3.0)
    wb_mode = str(settings.get("wb_mode", "camera")).lower()
    params: dict[str, Any] = {
        "output_color": rawpy.ColorSpace.sRGB,
        "output_bps": 8,
        "half_size": bool(settings.get("half_size", True)),
        "no_auto_bright": True,
        "exp_shift": max(0.25, min(8.0, 2.0 ** ev)),
        "exp_preserve_highlights": _clamp(settings.get("highlight_preserve", 0.65), 0.0, 1.0, 0.65),
        "gamma": (2.222, 4.5),
    }
    if wb_mode == "auto":
        params["use_auto_wb"] = True
        params["use_camera_wb"] = False
    elif wb_mode == "daylight":
        params["use_auto_wb"] = False
        params["use_camera_wb"] = False
    else:
        params["use_camera_wb"] = True
        params["use_auto_wb"] = False

    with rawpy.imread(str(src)) as raw:
        rgb = raw.postprocess(**params)

    temperature = _clamp(settings.get("temperature", 0), -100, 100) / 100.0
    tint = _clamp(settings.get("tint", 0), -100, 100) / 100.0
    if abs(temperature) > 0.0001 or abs(tint) > 0.0001:
        arr = rgb.astype(np.float32)
        arr[..., 0] *= 1.0 + 0.14 * temperature + 0.05 * tint
        arr[..., 1] *= 1.0 - 0.10 * tint
        arr[..., 2] *= 1.0 - 0.14 * temperature + 0.05 * tint
        rgb = np.clip(arr, 0, 255).astype(np.uint8)

    img = Image.fromarray(rgb)
    contrast = _clamp(settings.get("contrast", 0), -100, 100) / 100.0
    saturation = _clamp(settings.get("saturation", 0), -100, 100) / 100.0
    sharpness = _clamp(settings.get("sharpness", 0), -100, 100) / 100.0
    if abs(contrast) > 0.0001:
        img = ImageEnhance.Contrast(img).enhance(max(0.0, 1.0 + contrast))
    if abs(saturation) > 0.0001:
        img = ImageEnhance.Color(img).enhance(max(0.0, 1.0 + saturation))
    if abs(sharpness) > 0.0001:
        img = ImageEnhance.Sharpness(img).enhance(max(0.0, 1.0 + sharpness))

    output_format = str(settings.get("output_format", "JPEG")).upper()
    suffix = ".png" if output_format == "PNG" else ".jpg"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    dest = root / "previews" / f"{_safe_name(src.stem)}_{stamp}{suffix}"
    save_kwargs: dict[str, Any] = {}
    if suffix == ".jpg":
        save_kwargs.update({"quality": int(_clamp(settings.get("jpeg_quality", 92), 70, 100, 92)), "subsampling": 0, "optimize": True})
    img.save(dest, **save_kwargs)

    metadata = raw_metadata(str(src))
    sidecar = root / "metadata" / (dest.stem + ".json")
    record = {
        "at": _now(),
        "source": str(src),
        "source_sha256": metadata["sha256"],
        "preview": str(dest),
        "preview_sha256": sha256_file(dest),
        "settings": settings,
        "metadata": metadata,
    }
    _atomic_json(sidecar, record)
    save_settings(str(root), settings, snapshot=False)
    _append_jsonl(root / "logs" / "actions.jsonl", {"at": _now(), "action": "raw_render", "source": str(src), "output": str(dest), "settings": settings})
    return {
        "ok": True,
        "workspace": str(root),
        "source": str(src),
        "preview": str(dest),
        "relative_preview": str(dest.relative_to(root)).replace("\\", "/"),
        "metadata_file": str(sidecar),
        "width": img.width,
        "height": img.height,
        "sha256": record["preview_sha256"],
        "raw_metadata": metadata,
    }


def save_settings(workspace: str, settings: dict[str, Any], snapshot: bool = True) -> dict[str, Any]:
    root = _workspace_root(workspace)
    path = root / PROJECT_DIRNAME / "settings.json"
    previous = _read_json(path, {})
    clean = dict(previous)
    allowed = {
        "wb_mode", "exposure_ev", "contrast", "saturation", "temperature", "tint",
        "sharpness", "half_size", "output_format", "jpeg_quality", "copy_original",
        "source_folder", "last_source", "project_note",
    }
    for key, value in dict(settings or {}).items():
        if key in allowed:
            clean[key] = value
    with LOCK:
        if snapshot and path.is_file():
            snap = root / "snapshots" / f"settings_{datetime.now():%Y%m%d_%H%M%S_%f}.json"
            _atomic_json(snap, previous)
        _atomic_json(path, clean)
        _append_jsonl(root / "logs" / "actions.jsonl", {"at": _now(), "action": "settings_save", "keys": sorted(clean)})
    return {"ok": True, "settings": clean}


def save_conversation(workspace: str, role: str, text: str, model: str | None = None, kind: str = "chat") -> dict[str, Any]:
    root = _workspace_root(workspace)
    message = str(text or "").strip()
    if not message:
        raise ValueError("Mensagem vazia.")
    rec = {
        "at": _now(),
        "role": str(role or "user")[:40],
        "kind": str(kind or "chat")[:40],
        "model": str(model or "")[:180] or None,
        "text": message[:50000],
    }
    with LOCK:
        _append_jsonl(root / "conversations" / "conversation.jsonl", rec)
        _append_jsonl(root / "logs" / "actions.jsonl", {"at": _now(), "action": "conversation_append", "role": rec["role"], "kind": rec["kind"]})
    return {"ok": True, "record": rec}


def load_workspace(workspace: str) -> dict[str, Any]:
    root = _workspace_root(workspace)
    settings = _read_json(root / PROJECT_DIRNAME / "settings.json", {})
    indexed = _read_jsonl(root / PROJECT_DIRNAME / "files.jsonl", 500)
    conversations = _read_jsonl(root / "conversations" / "conversation.jsonl", 200)
    previews = []
    for p in sorted((root / "previews").glob("*"), key=lambda x: x.stat().st_mtime if x.exists() else 0, reverse=True)[:120]:
        if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png"}:
            try:
                previews.append({"name": p.name, "path": str(p), "rel": str(p.relative_to(root)).replace("\\", "/"), "bytes": p.stat().st_size})
            except OSError:
                pass
    originals = []
    for p in sorted((root / "originals").glob("*"))[:1000]:
        if p.is_file() and p.suffix.lower() in MEDIA_EXTS:
            try:
                originals.append({"name": p.name, "path": str(p), "bytes": p.stat().st_size, "extension": p.suffix.lower()})
            except OSError:
                pass
    return {
        "ok": True,
        "workspace": str(root),
        "manifest": _read_json(root / PROJECT_DIRNAME / "manifest.json", {}),
        "settings": settings,
        "indexed": indexed,
        "originals": originals,
        "previews": previews,
        "conversations": conversations,
        "paths": {
            "originals": str(root / "originals"),
            "previews": str(root / "previews"),
            "exports": str(root / "exports"),
            "metadata": str(root / "metadata"),
            "conversations": str(root / "conversations"),
            "logs": str(root / "logs"),
            "snapshots": str(root / "snapshots"),
        },
    }


def snapshot_workspace(workspace: str, label: str = "manual") -> dict[str, Any]:
    root = _workspace_root(workspace)
    state = load_workspace(str(root))
    payload = {
        "at": _now(),
        "label": _safe_name(label),
        "manifest": state["manifest"],
        "settings": state["settings"],
        "indexed_tail": state["indexed"][-100:],
        "conversation_tail": state["conversations"][-100:],
        "original_count": len(state["originals"]),
        "preview_count": len(state["previews"]),
    }
    dest = root / "snapshots" / f"snapshot_{datetime.now():%Y%m%d_%H%M%S_%f}_{_safe_name(label)}.json"
    _atomic_json(dest, payload)
    _append_jsonl(root / "logs" / "actions.jsonl", {"at": _now(), "action": "snapshot", "file": str(dest)})
    return {"ok": True, "snapshot": str(dest)}


def artifact_path(workspace: str, rel: str) -> Path:
    root = _workspace_root(workspace)
    target = (root / rel).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError("Artefato fora do workspace.") from exc
    if not target.is_file() or target.suffix.lower() not in {".jpg", ".jpeg", ".png", ".json"}:
        raise ValueError("Artefato invalido.")
    return target


def open_workspace(workspace: str) -> dict[str, Any]:
    root = _workspace_root(workspace)
    try:
        if os.name == "nt":
            os.startfile(str(root))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(root)])
        else:
            subprocess.Popen(["xdg-open", str(root)])
        _append_jsonl(root / "logs" / "actions.jsonl", {"at": _now(), "action": "open_workspace"})
        return {"ok": True, "workspace": str(root)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:1000]}
