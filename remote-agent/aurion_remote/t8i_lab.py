from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import shutil
import uuid
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/t8i", tags=["t8i"])

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
CONFIG_FILE = DATA_DIR / "t8i_workspace.json"
SESSION_RE = re.compile(r"^[A-Za-z0-9_-]{8,96}$")
SAFE_FILE_RE = re.compile(r"^[^/\\\x00]+$")
FOLDERS = ("RAW", "PREVIEWS", "EXPORTS", "CONVERSAS", "PRESETS", "LOGS", "BACKUPS")


class WorkspaceRequest(BaseModel):
    path: str = Field(min_length=2, max_length=1000)


class ImportRequest(BaseModel):
    paths: list[str] = Field(min_length=1, max_length=200)
    copy: bool = True


class DevelopParams(BaseModel):
    file: str
    exposure_ev: float = Field(default=0.0, ge=-4.0, le=4.0)
    brightness: float = Field(default=1.0, ge=0.1, le=3.0)
    contrast: float = Field(default=1.0, ge=0.1, le=3.0)
    saturation: float = Field(default=1.0, ge=0.0, le=3.0)
    use_camera_wb: bool = True
    auto_wb: bool = False
    gamma: float = Field(default=2.2, ge=1.0, le=3.0)


class ExportRequest(DevelopParams):
    format: Literal["jpeg", "tiff16", "png"] = "jpeg"
    quality: int = Field(default=94, ge=70, le=100)
    name: str | None = Field(default=None, max_length=160)


class ConversationStart(BaseModel):
    name: str = Field(default="sessao", max_length=120)


class ConversationAppend(BaseModel):
    session_id: str
    role: Literal["user", "assistant", "system", "note"]
    content: str = Field(max_length=100_000)
    attachments: list[str] = Field(default_factory=list, max_length=30)


class BackupRequest(BaseModel):
    include_raw: bool = False
    include_exports: bool = False


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _slug(text: str) -> str:
    text = re.sub(r"[^A-Za-z0-9._-]+", "-", text.strip()).strip("-._")
    return (text or "sessao")[:64]


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temp.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        temp.replace(path)
    finally:
        if temp.exists():
            temp.unlink(missing_ok=True)


def _append_jsonl(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(payload, ensure_ascii=False) + "\n"
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())


def _sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def _load_config() -> dict:
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        root = Path(data.get("workspace", ""))
        if root.is_absolute():
            return data
    except (OSError, ValueError, TypeError):
        pass
    return {}


def _workspace(required: bool = True) -> Path | None:
    data = _load_config()
    raw = data.get("workspace")
    if not raw:
        if required:
            raise HTTPException(status_code=409, detail="Escolha a pasta de trabalho da T8i primeiro.")
        return None
    root = Path(raw)
    if not root.is_absolute():
        raise HTTPException(status_code=500, detail="Workspace T8i inválido.")
    return root


def _create_structure(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for name in FOLDERS:
        (root / name).mkdir(parents=True, exist_ok=True)


def _save_workspace(root: Path) -> dict:
    _create_structure(root)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"workspace": str(root), "updated_at": _now(), "version": 1}
    _atomic_write_text(CONFIG_FILE, json.dumps(payload, ensure_ascii=False, indent=2))
    return payload


def _deps() -> dict:
    result = {}
    for name in ("rawpy", "numpy", "PIL", "tifffile"):
        try:
            module = __import__(name)
            result[name] = {"ok": True, "version": getattr(module, "__version__", "instalado")}
        except Exception as exc:  # import errors must become visible, not crash the portal
            result[name] = {"ok": False, "error": type(exc).__name__}
    return result


def _require_raw_deps() -> None:
    missing = [name for name, item in _deps().items() if not item["ok"]]
    if missing:
        raise HTTPException(
            status_code=503,
            detail="Dependências T8i ausentes: " + ", ".join(missing) + ". Rode START_AURION.cmd novamente.",
        )


def _safe_raw_name(name: str) -> str:
    if not SAFE_FILE_RE.match(name) or Path(name).suffix.lower() != ".cr3":
        raise HTTPException(status_code=400, detail="Nome de arquivo CR3 inválido.")
    return name


def _raw_path(name: str) -> Path:
    root = _workspace()
    assert root is not None
    path = root / "RAW" / _safe_raw_name(name)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="CR3 não encontrado na pasta RAW.")
    return path


def _unique_copy(src: Path, dst_dir: Path) -> Path:
    dst = dst_dir / src.name
    counter = 1
    while dst.exists():
        dst = dst_dir / f"{src.stem}_{counter:03d}{src.suffix}"
        counter += 1
    shutil.copy2(src, dst)
    return dst


def _develop_array(source: Path, params: DevelopParams, output_bps: int = 16):
    _require_raw_deps()
    import numpy as np
    import rawpy

    exp_shift = max(0.25, min(8.0, 2.0 ** params.exposure_ev))
    with rawpy.imread(str(source)) as raw:
        rgb = raw.postprocess(
            use_camera_wb=params.use_camera_wb and not params.auto_wb,
            use_auto_wb=params.auto_wb,
            no_auto_bright=True,
            exp_shift=exp_shift,
            exp_preserve_highlights=0.6,
            output_bps=output_bps,
            gamma=(params.gamma, 4.5),
        )

    maxv = 65535.0 if output_bps == 16 else 255.0
    arr = rgb.astype(np.float32)
    arr *= params.brightness
    midpoint = maxv / 2.0
    arr = (arr - midpoint) * params.contrast + midpoint
    if params.saturation != 1.0:
        lum = (arr[..., 0] * 0.2126 + arr[..., 1] * 0.7152 + arr[..., 2] * 0.0722)[..., None]
        arr = lum + (arr - lum) * params.saturation
    arr = np.clip(arr, 0, maxv)
    return arr.astype(np.uint16 if output_bps == 16 else np.uint8)


def _write_sidecar(path: Path, source: Path, params: DevelopParams, extra: dict | None = None) -> None:
    payload = {
        "source": str(source),
        "created_at": _now(),
        "params": params.model_dump(),
        **(extra or {}),
    }
    sidecar = path.with_suffix(path.suffix + ".json")
    _atomic_write_text(sidecar, json.dumps(payload, ensure_ascii=False, indent=2))


@router.get("/status")
async def status() -> dict:
    root = _workspace(required=False)
    counts = {}
    if root and root.exists():
        for folder in FOLDERS:
            p = root / folder
            counts[folder] = sum(1 for x in p.iterdir() if x.is_file()) if p.is_dir() else 0
    return {
        "status": "ready" if root else "needs_workspace",
        "workspace": str(root) if root else None,
        "dependencies": _deps(),
        "folders": list(FOLDERS),
        "counts": counts,
        "originals_are_never_overwritten": True,
    }


@router.post("/workspace")
async def set_workspace(body: WorkspaceRequest) -> dict:
    root = Path(body.path).expanduser()
    if not root.is_absolute():
        raise HTTPException(status_code=400, detail="Escolha um caminho absoluto, por exemplo D:\\FOTOS\\AURION_T8I.")
    try:
        payload = _save_workspace(root)
    except OSError as exc:
        raise HTTPException(status_code=400, detail=f"Não foi possível criar a estrutura: {exc}") from exc
    return {"ok": True, **payload, "folders": list(FOLDERS)}


@router.post("/workspace/pick")
async def pick_workspace(request: Request) -> dict:
    if not request.client or request.client.host not in {"127.0.0.1", "::1"}:
        raise HTTPException(status_code=403, detail="O seletor nativo só pode ser aberto no próprio PC.")

    def choose() -> str:
        import tkinter as tk
        from tkinter import filedialog
        app = tk.Tk()
        app.withdraw()
        app.attributes("-topmost", True)
        selected = filedialog.askdirectory(title="Escolha a pasta de trabalho da Canon T8i")
        app.destroy()
        return selected

    try:
        selected = await asyncio.to_thread(choose)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Seletor de pasta indisponível: {type(exc).__name__}") from exc
    if not selected:
        return {"ok": False, "cancelled": True}
    payload = _save_workspace(Path(selected))
    return {"ok": True, **payload, "folders": list(FOLDERS)}


@router.post("/files/pick")
async def pick_raw_files(request: Request) -> dict:
    if not request.client or request.client.host not in {"127.0.0.1", "::1"}:
        raise HTTPException(status_code=403, detail="O seletor nativo só pode ser aberto no próprio PC.")

    def choose() -> list[str]:
        import tkinter as tk
        from tkinter import filedialog
        app = tk.Tk()
        app.withdraw()
        app.attributes("-topmost", True)
        selected = filedialog.askopenfilenames(
            title="Selecione arquivos Canon RAW",
            filetypes=(("Canon RAW CR3", "*.cr3 *.CR3"), ("Todos os arquivos", "*.*")),
        )
        app.destroy()
        return list(selected)

    try:
        selected = await asyncio.to_thread(choose)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Seletor de arquivos indisponível: {type(exc).__name__}") from exc
    return {"paths": selected}


@router.post("/import")
async def import_files(body: ImportRequest) -> dict:
    root = _workspace()
    assert root is not None
    _create_structure(root)
    imported = []
    rejected = []
    for raw_path in body.paths:
        src = Path(raw_path).expanduser()
        if not src.is_absolute() or not src.is_file() or src.suffix.lower() != ".cr3":
            rejected.append({"path": raw_path, "reason": "arquivo CR3 inválido ou inexistente"})
            continue
        try:
            if body.copy:
                dst = _unique_copy(src, root / "RAW")
            else:
                # "copy=False" means register only when file is already inside RAW; never move originals.
                expected = (root / "RAW").resolve()
                resolved = src.resolve()
                if resolved.parent != expected:
                    rejected.append({"path": raw_path, "reason": "por segurança, originais externos não são movidos"})
                    continue
                dst = resolved
            item = {
                "time": _now(),
                "source": str(src),
                "stored": str(dst),
                "name": dst.name,
                "size": dst.stat().st_size,
                "sha256": _sha256(dst),
                "operation": "copy" if body.copy else "register",
            }
            imported.append(item)
            _append_jsonl(root / "LOGS" / "imports.jsonl", item)
        except OSError as exc:
            rejected.append({"path": raw_path, "reason": str(exc)})
    return {"imported": imported, "rejected": rejected}


@router.get("/files")
async def list_files(limit: int = 300) -> dict:
    root = _workspace()
    assert root is not None
    raw_dir = root / "RAW"
    files = []
    for path in sorted(raw_dir.glob("*.CR3")) + sorted(raw_dir.glob("*.cr3")):
        if len(files) >= max(1, min(limit, 2000)):
            break
        stat = path.stat()
        files.append({"name": path.name, "size": stat.st_size, "modified": datetime.fromtimestamp(stat.st_mtime, UTC).isoformat()})
    # De-duplicate on case-insensitive Windows filesystems.
    unique = {item["name"].lower(): item for item in files}
    return {"files": list(unique.values()), "count": len(unique)}


@router.post("/preview")
async def create_preview(body: DevelopParams) -> dict:
    root = _workspace()
    assert root is not None
    source = _raw_path(body.file)
    try:
        arr16 = await asyncio.to_thread(_develop_array, source, body, 16)
        from PIL import Image
        import numpy as np
        arr8 = (arr16 / 257).astype(np.uint8)
        image = Image.fromarray(arr8, mode="RGB")
        image.thumbnail((2200, 2200))
        token = uuid.uuid4().hex[:10]
        out = root / "PREVIEWS" / f"{source.stem}_{token}.jpg"
        image.save(out, "JPEG", quality=90, optimize=True)
        _write_sidecar(out, source, body, {"kind": "preview"})
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Falha ao revelar CR3: {type(exc).__name__}: {exc}") from exc
    return {"ok": True, "preview": out.name, "source": source.name, "created_at": _now()}


@router.post("/export")
async def export_file(body: ExportRequest) -> dict:
    root = _workspace()
    assert root is not None
    source = _raw_path(body.file)
    stem = _slug(body.name or source.stem)
    token = datetime.now().strftime("%Y%m%d_%H%M%S")
    try:
        arr16 = await asyncio.to_thread(_develop_array, source, body, 16)
        if body.format == "tiff16":
            import tifffile
            out = root / "EXPORTS" / f"{stem}_{token}.tif"
            tifffile.imwrite(str(out), arr16, photometric="rgb")
        else:
            from PIL import Image
            import numpy as np
            arr8 = (arr16 / 257).astype(np.uint8)
            image = Image.fromarray(arr8, mode="RGB")
            if body.format == "png":
                out = root / "EXPORTS" / f"{stem}_{token}.png"
                image.save(out, "PNG", optimize=True)
            else:
                out = root / "EXPORTS" / f"{stem}_{token}.jpg"
                image.save(out, "JPEG", quality=body.quality, subsampling=0, optimize=True)
        _write_sidecar(out, source, body, {"kind": "export", "format": body.format})
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Falha na exportação: {type(exc).__name__}: {exc}") from exc
    return {"ok": True, "file": out.name, "path": str(out), "created_at": _now()}


@router.get("/media/{kind}/{name}")
async def media(kind: Literal["PREVIEWS", "EXPORTS"], name: str):
    if not SAFE_FILE_RE.match(name):
        raise HTTPException(status_code=400, detail="Nome inválido.")
    root = _workspace()
    assert root is not None
    path = root / kind / name
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado.")
    return FileResponse(path)


@router.post("/conversations/start")
async def conversation_start(body: ConversationStart) -> dict:
    root = _workspace()
    assert root is not None
    session_id = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}_{uuid.uuid4().hex[:10]}"
    conv_dir = root / "CONVERSAS"
    conv_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "session_id": session_id,
        "name": body.name.strip() or "sessao",
        "created_at": _now(),
        "log_file": f"{session_id}.jsonl",
    }
    _atomic_write_text(conv_dir / f"{session_id}.meta.json", json.dumps(meta, ensure_ascii=False, indent=2))
    (conv_dir / f"{session_id}.jsonl").touch(exist_ok=False)
    return meta


@router.post("/conversations/append")
async def conversation_append(body: ConversationAppend) -> dict:
    if not SESSION_RE.match(body.session_id):
        raise HTTPException(status_code=400, detail="ID de conversa inválido.")
    root = _workspace()
    assert root is not None
    path = root / "CONVERSAS" / f"{body.session_id}.jsonl"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Conversa não encontrada.")
    entry = {
        "time": _now(),
        "role": body.role,
        "content": body.content,
        "attachments": body.attachments,
    }
    try:
        _append_jsonl(path, entry)
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Falha ao salvar conversa: {exc}") from exc
    return {"ok": True, "saved_at": entry["time"]}


@router.get("/conversations")
async def conversations(limit: int = 100) -> dict:
    root = _workspace()
    assert root is not None
    conv_dir = root / "CONVERSAS"
    items = []
    for meta_path in sorted(conv_dir.glob("*.meta.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        if len(items) >= max(1, min(limit, 1000)):
            break
        try:
            items.append(json.loads(meta_path.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            continue
    return {"conversations": items}



@router.get("/conversations/{session_id}")
async def conversation_read(session_id: str, limit: int = 2000) -> dict:
    if not SESSION_RE.match(session_id):
        raise HTTPException(status_code=400, detail="ID de conversa inválido.")
    root = _workspace()
    assert root is not None
    conv_dir = root / "CONVERSAS"
    log_path = conv_dir / f"{session_id}.jsonl"
    meta_path = conv_dir / f"{session_id}.meta.json"
    if not log_path.is_file():
        raise HTTPException(status_code=404, detail="Conversa não encontrada.")
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.is_file() else {"session_id": session_id}
        entries = []
        with log_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if len(entries) >= max(1, min(limit, 10000)):
                    break
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=500, detail=f"Falha ao ler conversa: {type(exc).__name__}") from exc
    return {"meta": meta, "entries": entries, "count": len(entries)}


def _backup_file_allowed(relative: Path, include_raw: bool, include_exports: bool) -> bool:
    if relative.parts and relative.parts[0] == "BACKUPS":
        return False
    if relative.parts and relative.parts[0] == "RAW":
        return include_raw
    if relative.parts and relative.parts[0] in {"PREVIEWS", "EXPORTS"}:
        return include_exports or relative.name.lower().endswith(".json")
    return True


def _create_backup(root: Path, include_raw: bool = False, include_exports: bool = False) -> dict:
    backup_dir = root / "BACKUPS"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive = backup_dir / f"AURION_T8I_BACKUP_{stamp}_{uuid.uuid4().hex[:6]}.zip"
    manifest = {
        "created_at": _now(),
        "workspace": str(root),
        "include_raw": include_raw,
        "include_exports": include_exports,
        "files": [],
    }
    candidates = [
        path for path in root.rglob("*")
        if path.is_file() and _backup_file_allowed(path.relative_to(root), include_raw, include_exports)
    ]
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as bundle:
        for path in sorted(candidates):
            relative = path.relative_to(root)
            info = {"path": relative.as_posix(), "size": path.stat().st_size, "sha256": _sha256(path)}
            manifest["files"].append(info)
            bundle.write(path, relative.as_posix())
        bundle.writestr("BACKUP_MANIFEST.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    result = {
        "file": archive.name,
        "path": str(archive),
        "size": archive.stat().st_size,
        "sha256": _sha256(archive),
        "files": len(manifest["files"]),
        "created_at": manifest["created_at"],
        "includes_original_raw": include_raw,
        "includes_rendered_files": include_exports,
    }
    _append_jsonl(root / "LOGS" / "backups.jsonl", result)
    return result


@router.post("/backup")
async def create_backup(body: BackupRequest) -> dict:
    root = _workspace()
    assert root is not None
    try:
        return await asyncio.to_thread(_create_backup, root, body.include_raw, body.include_exports)
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Falha ao criar backup: {exc}") from exc


@router.get("/integrity")
async def integrity(limit: int = 2000) -> dict:
    root = _workspace()
    assert root is not None
    targets = []
    for folder in ("RAW", "CONVERSAS", "PRESETS", "LOGS"):
        base = root / folder
        if base.is_dir():
            targets.extend(path for path in base.rglob("*") if path.is_file())
    cap = max(1, min(limit, 10000))
    truncated = len(targets) > cap
    records = []
    for path in sorted(targets)[:cap]:
        try:
            records.append({
                "path": path.relative_to(root).as_posix(),
                "size": path.stat().st_size,
                "sha256": await asyncio.to_thread(_sha256, path),
                "ok": True,
            })
        except OSError as exc:
            records.append({"path": str(path), "ok": False, "error": str(exc)})
    checked_at = _now()
    report = {"checked_at": checked_at, "count": len(records), "truncated": truncated, "files": records}
    report_name = f"integrity_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    _atomic_write_text(root / "LOGS" / report_name, json.dumps(report, ensure_ascii=False, indent=2))
    return {"ok": all(item["ok"] for item in records), "checked_at": checked_at, "count": len(records), "truncated": truncated, "report": report_name}
