# -*- coding: utf-8 -*-
"""
AURION ONE — trabalhador isolado da aba Canon T8i.
Este arquivo roda dentro de .venv_t8i e NUNCA move/apaga o RAW original.
"""
from __future__ import annotations
import argparse, hashlib, json, sys
from datetime import datetime
from pathlib import Path

def sha256_file(path: Path, block: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(block), b""):
            h.update(chunk)
    return h.hexdigest()

def _imports():
    import numpy as np
    import rawpy
    from PIL import Image, ImageEnhance
    return np, rawpy, Image, ImageEnhance

def probe(src: Path) -> dict:
    np, rawpy, Image, ImageEnhance = _imports()
    if not src.exists() or not src.is_file():
        raise FileNotFoundError(src)
    out = {
        "ok": True,
        "source": str(src),
        "name": src.name,
        "ext": src.suffix.lower(),
        "bytes": src.stat().st_size,
        "sha256": sha256_file(src),
    }
    if src.suffix.lower() in {".cr3", ".cr2", ".nef", ".arw", ".dng", ".raf", ".rw2", ".orf"}:
        with rawpy.imread(str(src)) as raw:
            out.update({
                "raw_type": str(getattr(raw, "raw_type", "")),
                "sizes": {
                    "raw_width": int(raw.sizes.raw_width),
                    "raw_height": int(raw.sizes.raw_height),
                    "width": int(raw.sizes.width),
                    "height": int(raw.sizes.height),
                },
                "camera_whitebalance": [float(x) for x in (raw.camera_whitebalance or [])],
                "daylight_whitebalance": [float(x) for x in (raw.daylight_whitebalance or [])],
            })
    return out

def develop(src: Path, dst: Path, params: dict) -> dict:
    np, rawpy, Image, ImageEnhance = _imports()
    if src.suffix.lower() not in {".cr3", ".cr2", ".nef", ".arw", ".dng", ".raf", ".rw2", ".orf"}:
        raise ValueError("Arquivo não reconhecido como RAW fotográfico suportado pelo worker.")
    dst.parent.mkdir(parents=True, exist_ok=True)

    use_camera_wb = bool(params.get("use_camera_wb", True))
    no_auto_bright = bool(params.get("no_auto_bright", False))
    output_bps = 16 if str(params.get("format", "")).upper() == "TIFF" else 8

    with rawpy.imread(str(src)) as raw:
        rgb = raw.postprocess(
            use_camera_wb=use_camera_wb,
            no_auto_bright=no_auto_bright,
            output_bps=output_bps,
            gamma=(2.222, 4.5),
        )

    # Ajustes simples, não destrutivos, aplicados apenas ao derivado.
    ev = float(params.get("exposure", 0.0) or 0.0)
    if ev:
        maxv = 65535.0 if rgb.dtype.itemsize > 1 else 255.0
        rgb = np.clip(rgb.astype(np.float32) * (2.0 ** ev), 0, maxv).astype(rgb.dtype)

    if rgb.dtype.itemsize > 1:
        # Pillow trabalha de forma mais previsível em 8 bit para preview/JPEG/PNG.
        pil = Image.fromarray((rgb / 257).astype("uint8"), mode="RGB")
    else:
        pil = Image.fromarray(rgb, mode="RGB")

    contrast = max(0.0, float(params.get("contrast", 1.0) or 1.0))
    saturation = max(0.0, float(params.get("saturation", 1.0) or 1.0))
    brightness = max(0.0, float(params.get("brightness", 1.0) or 1.0))
    pil = ImageEnhance.Contrast(pil).enhance(contrast)
    pil = ImageEnhance.Color(pil).enhance(saturation)
    pil = ImageEnhance.Brightness(pil).enhance(brightness)

    fmt = str(params.get("format") or dst.suffix.lstrip(".") or "JPEG").upper()
    if fmt == "JPG":
        fmt = "JPEG"
    save_kwargs = {}
    if fmt == "JPEG":
        save_kwargs.update({"quality": int(params.get("quality", 94)), "subsampling": 0})
    elif fmt == "TIFF":
        save_kwargs.update({"compression": "tiff_deflate"})
    pil.save(str(dst), format=fmt, **save_kwargs)

    return {
        "ok": True,
        "source": str(src),
        "output": str(dst),
        "format": fmt,
        "sha256_source": sha256_file(src),
        "params": params,
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "width": pil.width,
        "height": pil.height,
    }

def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    pp = sub.add_parser("probe")
    pp.add_argument("--input", required=True)

    pd = sub.add_parser("develop")
    pd.add_argument("--input", required=True)
    pd.add_argument("--output", required=True)
    pd.add_argument("--params-json", default="{}")

    args = p.parse_args()
    try:
        if args.cmd == "probe":
            result = probe(Path(args.input))
        else:
            params = json.loads(args.params_json or "{}")
            result = develop(Path(args.input), Path(args.output), params)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except Exception as e:
        print(json.dumps({"ok": False, "error": f"{type(e).__name__}: {e}"}, ensure_ascii=False))
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
