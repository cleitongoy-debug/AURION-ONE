# -*- coding: utf-8 -*-
"""AURION ONE · Canon EOS Rebel T8i RAW lab.

Additive module for CR3/CR2/DNG still-photo development.
Never edits the original upload in place. Every import, render and conversation
gets a timestamped local record inside a user-selected workspace.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import jsonify, request, send_file

REQS = {
    "rawpy": "rawpy>=0.25,<1",
    "numpy": "numpy>=2,<3",
    "PIL": "Pillow>=11,<13",
    "tifffile": "tifffile>=2025.2,<2027",
}
SUBDIRS = ("ORIGINAIS", "REVELADOS", "EXPORTADOS", "CONVERSAS", "PRESETS", "LOGS", "BACKUPS")
_ALLOWED_RAW = {".cr3", ".cr2", ".dng"}
_INSTALL_STATE: dict[str, Any] = {"running": False, "done": False, "error": "", "started": None, "finished": None}


def _now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


def _clean_name(name: str) -> str:
    base = Path(name or "arquivo").name
    stem = re.sub(r"[^A-Za-z0-9._#() -]+", "_", base).strip(" .")
    return stem[:180] or "arquivo"


def _unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    return path.with_name(f"{path.stem}__{_now_stamp()}{path.suffix}")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _atomic_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def _default_workspace() -> Path:
    return Path.home() / "Pictures" / "AURION_T8I"


def _deps() -> dict[str, bool]:
    return {name: importlib.util.find_spec(name) is not None for name in REQS}


def _install_missing(log) -> None:
    if _INSTALL_STATE["running"]:
        return
    missing = [pkg for mod, pkg in REQS.items() if importlib.util.find_spec(mod) is None]
    if not missing:
        _INSTALL_STATE.update({"done": True, "error": "", "finished": time.time()})
        return
    _INSTALL_STATE.update({"running": True, "done": False, "error": "", "started": time.time()})
    try:
        cmd = [sys.executable, "-m", "pip", "install", "--disable-pip-version-check", *missing]
        log("T8I RAW: instalando dependências: " + ", ".join(missing))
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
        if proc.returncode != 0:
            raise RuntimeError((proc.stderr or proc.stdout or "pip falhou")[-1600:])
        _INSTALL_STATE.update({"done": True, "error": ""})
        log("T8I RAW: dependências instaladas.")
    except Exception as exc:
        _INSTALL_STATE.update({"done": False, "error": f"{type(exc).__name__}: {exc}"[:1800]})
        log("T8I RAW: falha ao instalar dependências: " + _INSTALL_STATE["error"], True)
    finally:
        _INSTALL_STATE["running"] = False
        _INSTALL_STATE["finished"] = time.time()


def register_t8i(app, root: Path, log_fn=None) -> None:
    root = Path(root)
    cfg_file = root / "config" / "t8i_raw_lab.json"
    log = log_fn or (lambda msg, error=False: None)

    def load_cfg() -> dict[str, Any]:
        try:
            data = json.loads(cfg_file.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except Exception:
            pass
        return {"workspace": str(_default_workspace()), "last_raw": "", "last_render": ""}

    def save_cfg(data: dict[str, Any]) -> None:
        _atomic_json(cfg_file, data)

    def workspace(create: bool = True) -> Path:
        cfg = load_cfg()
        p = Path(str(cfg.get("workspace") or _default_workspace())).expanduser()
        if create:
            p.mkdir(parents=True, exist_ok=True)
            for name in SUBDIRS:
                (p / name).mkdir(parents=True, exist_ok=True)
        return p

    def backup_cfg() -> None:
        if not cfg_file.is_file():
            return
        try:
            dst = _unique_path(workspace(True) / "BACKUPS" / f"t8i_raw_lab__{_now_stamp()}.json")
            shutil.copy2(cfg_file, dst)
        except Exception as exc:
            log("T8I RAW: backup de configuração falhou: " + str(exc)[:300], True)

    def within(base: Path, path: Path) -> bool:
        try:
            path.resolve().relative_to(base.resolve())
            return True
        except Exception:
            return False

    threading.Thread(target=_install_missing, args=(log,), daemon=True, name="aurion-t8i-deps").start()

    @app.get("/api/one/t8i/status")
    def t8i_status():
        w = workspace(True)
        deps = _deps()
        versions = {}
        if deps.get("rawpy"):
            try:
                import rawpy
                versions["rawpy"] = getattr(rawpy, "__version__", "instalado")
                versions["libraw"] = str(getattr(rawpy, "libraw_version", ""))
            except Exception:
                pass
        return jsonify({
            "ok": True,
            "workspace": str(w),
            "folders": {x: str(w / x) for x in SUBDIRS},
            "dependencies": deps,
            "versions": versions,
            "installer": dict(_INSTALL_STATE),
            "note": "CR3 de foto é RAW de sensor. C-Log é uma curva de vídeo; esta aba revela RAW estático sem alterar o original.",
        })

    @app.post("/api/one/t8i/install")
    def t8i_install():
        if _INSTALL_STATE["running"]:
            return jsonify({"ok": True, "status": "instalando"})
        threading.Thread(target=_install_missing, args=(log,), daemon=True, name="aurion-t8i-deps-manual").start()
        return jsonify({"ok": True, "status": "iniciado"})

    @app.post("/api/one/t8i/workspace")
    def t8i_workspace():
        d = request.get_json(silent=True) or {}
        raw = str(d.get("path", "")).strip()
        if not raw:
            return jsonify({"ok": False, "error": "Informe uma pasta."}), 400
        p = Path(raw).expanduser()
        if p == Path(p.anchor):
            return jsonify({"ok": False, "error": "Escolha uma pasta de projeto, não a raiz do disco."}), 400
        try:
            backup_cfg()
            p.mkdir(parents=True, exist_ok=True)
            for name in SUBDIRS:
                (p / name).mkdir(parents=True, exist_ok=True)
            cfg = load_cfg()
            cfg["workspace"] = str(p.resolve())
            save_cfg(cfg)
            return jsonify({"ok": True, "workspace": str(p.resolve()), "folders": list(SUBDIRS)})
        except Exception as exc:
            return jsonify({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), 500

    @app.post("/api/one/t8i/pick-folder")
    def t8i_pick_folder():
        if os.name != "nt":
            return jsonify({"ok": False, "error": "Seletor nativo disponível apenas no Windows; digite o caminho."}), 409
        try:
            import tkinter as tk
            from tkinter import filedialog
            top = tk.Tk()
            top.withdraw()
            top.attributes("-topmost", True)
            chosen = filedialog.askdirectory(title="AURION ONE · escolher pasta do laboratório T8i")
            top.destroy()
            if not chosen:
                return jsonify({"ok": True, "cancelled": True})
            return jsonify({"ok": True, "path": chosen})
        except Exception as exc:
            return jsonify({"ok": False, "error": f"Seletor indisponível: {type(exc).__name__}: {exc}"}), 500

    @app.post("/api/one/t8i/open-workspace")
    def t8i_open_workspace():
        p = workspace(True)
        try:
            if os.name == "nt":
                os.startfile(str(p))  # type: ignore[attr-defined]
            else:
                return jsonify({"ok": False, "error": "Abertura automática implementada apenas no Windows."}), 409
            return jsonify({"ok": True, "workspace": str(p)})
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 500

    @app.post("/api/one/t8i/import")
    def t8i_import():
        f = request.files.get("file")
        if not f or not f.filename:
            return jsonify({"ok": False, "error": "Selecione um arquivo RAW."}), 400
        suffix = Path(f.filename).suffix.lower()
        if suffix not in _ALLOWED_RAW:
            return jsonify({"ok": False, "error": "Formato aceito nesta aba: CR3, CR2 ou DNG."}), 415
        w = workspace(True)
        dst = _unique_path(w / "ORIGINAIS" / _clean_name(f.filename))
        try:
            f.save(dst)
            stat = dst.stat()
            manifest = {
                "kind": "import",
                "created": datetime.now().isoformat(timespec="seconds"),
                "original_name": f.filename,
                "stored": str(dst),
                "bytes": stat.st_size,
                "sha256": _sha256(dst),
            }
            _atomic_json(w / "LOGS" / f"import__{_now_stamp()}.json", manifest)
            cfg = load_cfg()
            cfg["last_raw"] = str(dst)
            save_cfg(cfg)
            return jsonify({"ok": True, "source": str(dst), "name": dst.name, "bytes": stat.st_size, "sha256": manifest["sha256"]})
        except Exception as exc:
            return jsonify({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), 500

    @app.post("/api/one/t8i/develop")
    def t8i_develop():
        if not all(_deps().values()):
            return jsonify({"ok": False, "error": "Motor RAW ainda não está instalado. Aguarde ou clique INSTALAR/REPARAR."}), 503
        d = request.get_json(silent=True) or {}
        cfg = load_cfg()
        src = Path(str(d.get("source") or cfg.get("last_raw") or "")).expanduser()
        w = workspace(True)
        if not src.is_file() or src.suffix.lower() not in _ALLOWED_RAW:
            return jsonify({"ok": False, "error": "RAW importado não localizado."}), 404
        if not within(w / "ORIGINAIS", src):
            return jsonify({"ok": False, "error": "Por segurança, revele primeiro uma cópia importada em ORIGINAIS."}), 400
        try:
            ev = max(-5.0, min(5.0, float(d.get("exposure", 0))))
            contrast = max(0.25, min(3.0, float(d.get("contrast", 1.0))))
            saturation = max(0.0, min(3.0, float(d.get("saturation", 1.0))))
            wb = str(d.get("white_balance", "camera"))
        except (TypeError, ValueError):
            return jsonify({"ok": False, "error": "Parâmetros inválidos."}), 400

        try:
            import numpy as np
            import rawpy
            import tifffile
            from PIL import Image

            use_camera_wb = wb == "camera"
            use_auto_wb = wb == "auto"
            with rawpy.imread(str(src)) as raw:
                rgb = raw.postprocess(
                    use_camera_wb=use_camera_wb,
                    use_auto_wb=use_auto_wb,
                    no_auto_bright=False,
                    output_color=rawpy.ColorSpace.sRGB,
                    output_bps=16,
                    highlight_mode=rawpy.HighlightMode.Blend,
                )
            arr = rgb.astype(np.float32) / 65535.0
            arr *= float(2.0 ** ev)
            arr = (arr - 0.5) * contrast + 0.5
            lum = arr[..., 0] * 0.2126 + arr[..., 1] * 0.7152 + arr[..., 2] * 0.0722
            arr = lum[..., None] + (arr - lum[..., None]) * saturation
            arr = np.clip(arr, 0.0, 1.0)
            out16 = np.rint(arr * 65535.0).astype(np.uint16)
            out8 = np.rint(arr * 255.0).astype(np.uint8)

            stamp = _now_stamp()
            stem = re.sub(r"[^A-Za-z0-9._-]+", "_", src.stem)[:120]
            tiff = _unique_path(w / "REVELADOS" / f"{stem}__AURION_T8I__{stamp}.tif")
            jpg = _unique_path(w / "REVELADOS" / f"{stem}__AURION_T8I__{stamp}.jpg")
            tifffile.imwrite(tiff, out16, photometric="rgb")
            Image.fromarray(out8, mode="RGB").save(jpg, quality=95, subsampling=0, optimize=True)

            manifest = {
                "kind": "develop",
                "created": datetime.now().isoformat(timespec="seconds"),
                "source": str(src),
                "source_sha256": _sha256(src),
                "outputs": {"tiff16": str(tiff), "preview_jpeg": str(jpg)},
                "settings": {"exposure_ev": ev, "contrast": contrast, "saturation": saturation, "white_balance": wb},
                "engine": {"rawpy": getattr(rawpy, "__version__", ""), "libraw": str(getattr(rawpy, "libraw_version", ""))},
            }
            _atomic_json(w / "LOGS" / f"develop__{stamp}.json", manifest)
            cfg["last_render"] = str(jpg)
            save_cfg(cfg)
            return jsonify({
                "ok": True,
                "source": str(src),
                "tiff16": str(tiff),
                "jpeg": str(jpg),
                "preview_url": "/api/one/t8i/media/REVELADOS/" + jpg.name,
                "manifest": manifest,
            })
        except Exception as exc:
            log("T8I RAW: revelação falhou: " + traceback_text(exc), True)
            return jsonify({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), 500

    @app.get("/api/one/t8i/files")
    def t8i_files():
        w = workspace(True)
        def listing(name: str):
            p = w / name
            items = []
            for x in sorted(p.iterdir(), key=lambda q: q.stat().st_mtime, reverse=True)[:120]:
                if x.is_file():
                    items.append({"name": x.name, "path": str(x), "bytes": x.stat().st_size, "modified": x.stat().st_mtime})
            return items
        return jsonify({"ok": True, "workspace": str(w), "originals": listing("ORIGINAIS"), "revealed": listing("REVELADOS"), "conversations": listing("CONVERSAS")})

    @app.get("/api/one/t8i/media/<path:rel>")
    def t8i_media(rel: str):
        w = workspace(True)
        target = (w / rel).resolve()
        if not within(w, target) or not target.is_file():
            return jsonify({"ok": False, "error": "Arquivo não encontrado."}), 404
        return send_file(target)

    @app.post("/api/one/t8i/conversation")
    def t8i_conversation():
        d = request.get_json(silent=True) or {}
        text = str(d.get("text", "")).strip()
        title = str(d.get("title", "Conversa T8i")).strip()[:120] or "Conversa T8i"
        if not text:
            return jsonify({"ok": False, "error": "Nada para salvar."}), 400
        w = workspace(True)
        stamp = _now_stamp()
        safe_title = re.sub(r"[^A-Za-z0-9._-]+", "_", title)[:80] or "conversa"
        md = _unique_path(w / "CONVERSAS" / f"{stamp}__{safe_title}.md")
        js = md.with_suffix(".json")
        body = f"# {title}\n\nSalvo em: {datetime.now().isoformat(timespec='seconds')}\n\n{text}\n"
        md.write_text(body, encoding="utf-8")
        _atomic_json(js, {"title": title, "created": datetime.now().isoformat(timespec="seconds"), "text": text, "metadata": d.get("metadata", {})})
        return jsonify({"ok": True, "markdown": str(md), "json": str(js)})

    @app.post("/api/one/t8i/session-snapshot")
    def t8i_snapshot():
        d = request.get_json(silent=True) or {}
        w = workspace(True)
        stamp = _now_stamp()
        payload = {
            "created": datetime.now().isoformat(timespec="seconds"),
            "workspace": str(w),
            "config": load_cfg(),
            "dependencies": _deps(),
            "ui": d,
        }
        path = w / "LOGS" / f"session__{stamp}.json"
        _atomic_json(path, payload)
        return jsonify({"ok": True, "snapshot": str(path)})


def traceback_text(exc: Exception) -> str:
    return f"{type(exc).__name__}: {exc}"[:1200]
