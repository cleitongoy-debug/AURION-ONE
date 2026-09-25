from __future__ import annotations

import json
import os
import re
import subprocess
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/blender", tags=["blender-studio"])

BLENDER_ROOT = Path(os.environ.get("AURION_BLENDER_HOME", r"C:\Program Files\Blender Foundation\Blender 5.2"))
BLENDER_EXE = BLENDER_ROOT / "blender.exe"
DATA_ROOT = Path(__file__).resolve().parents[1] / "data" / "blender_studio"
ACTION_LOG = DATA_ROOT / "actions.jsonl"
CATEGORIES = {
    "projects": "PROJETOS",
    "renders": "RENDERS",
    "nodes": "NODES",
    "textures": "TEXTURAS",
    "rigs": "RIGS",
    "clothes": "ROUPAS_E_ACESSORIOS",
    "logs": "LOGS",
}
ASSET_EXTENSIONS = {
    "projects": {".blend"},
    "renders": {".png", ".jpg", ".jpeg", ".exr", ".tif", ".tiff", ".webp", ".mp4"},
    "nodes": {".blend", ".json", ".osl"},
    "textures": {".png", ".jpg", ".jpeg", ".exr", ".hdr", ".tif", ".tiff", ".webp"},
    "rigs": {".blend", ".fbx", ".gltf", ".glb", ".bvh"},
    "clothes": {".blend", ".fbx", ".obj", ".gltf", ".glb", ".abc", ".usd", ".usdc", ".usdz"},
}
SAFE_NAME = re.compile(r"[^A-Za-z0-9._ -]+")

_jobs: dict[str, dict[str, Any]] = {}
_processes: dict[str, subprocess.Popen] = {}


class RenderRequest(BaseModel):
    blend_file: str = Field(min_length=1, max_length=1024)
    mode: Literal["still", "animation"] = "still"
    frame: int = Field(default=1, ge=0, le=1_000_000)
    output_name: str = Field(default="aurion_render", min_length=1, max_length=100)


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def local_request(request: Request) -> bool:
    return bool(request.client and request.client.host in {"127.0.0.1", "::1"})


def require_local(request: Request) -> None:
    if not local_request(request):
        raise HTTPException(status_code=403, detail="Ações no Blender são permitidas somente no próprio PC")


def folders() -> dict[str, Path]:
    return {key: DATA_ROOT / name for key, name in CATEGORIES.items()}


def ensure_workspace() -> dict[str, Path]:
    paths = folders()
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths


def log_action(message: str, **details: Any) -> None:
    ensure_workspace()
    record = {"time": now_iso(), "message": message, **details}
    with ACTION_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def recent_actions(limit: int = 40) -> list[dict[str, Any]]:
    if not ACTION_LOG.is_file():
        return []
    output: list[dict[str, Any]] = []
    try:
        lines = ACTION_LOG.read_text(encoding="utf-8", errors="replace").splitlines()[-limit:]
    except OSError:
        return []
    for line in lines:
        try:
            output.append(json.loads(line))
        except ValueError:
            continue
    return output


def blender_running() -> tuple[bool, str]:
    if os.name != "nt":
        return False, "Monitor de processo disponível somente no Windows"
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq blender.exe", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            errors="replace",
            timeout=5,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"tasklist indisponível: {type(exc).__name__}"
    active = '"blender.exe"' in result.stdout.casefold()
    return active, result.stdout.strip() if active else "blender.exe não encontrado na lista de processos"


def asset_inventory() -> dict[str, list[dict[str, Any]]]:
    paths = ensure_workspace()
    result: dict[str, list[dict[str, Any]]] = {}
    for category, root in paths.items():
        if category == "logs":
            continue
        allowed = ASSET_EXTENSIONS.get(category, set())
        items: list[dict[str, Any]] = []
        for path in sorted(root.rglob("*"), key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True):
            if not path.is_file() or (allowed and path.suffix.casefold() not in allowed):
                continue
            try:
                stat = path.stat()
            except OSError:
                continue
            items.append({
                "name": path.name,
                "path": str(path),
                "size": stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime, UTC).isoformat(),
            })
            if len(items) >= 100:
                break
        result[category] = items
    return result


def refresh_jobs() -> None:
    for job_id, process in list(_processes.items()):
        code = process.poll()
        if code is None:
            _jobs[job_id]["status"] = "running"
            continue
        _jobs[job_id]["status"] = "completed" if code == 0 else "failed"
        _jobs[job_id]["return_code"] = code
        _jobs[job_id]["finished_at"] = now_iso()
        _processes.pop(job_id, None)
        log_action("Render Blender finalizado", job_id=job_id, return_code=code)


def status_snapshot() -> dict[str, Any]:
    refresh_jobs()
    running, detail = blender_running()
    inventory = asset_inventory()
    return {
        "checked_at": now_iso(),
        "installed": BLENDER_EXE.is_file(),
        "running": running,
        "process_detail": detail,
        "version_target": "5.2",
        "paths": {
            "install": str(BLENDER_ROOT),
            "executable": str(BLENDER_EXE),
            **{key: str(value) for key, value in folders().items()},
            "action_log": str(ACTION_LOG),
        },
        "inventory": inventory,
        "counts": {key: len(value) for key, value in inventory.items()},
        "jobs": list(_jobs.values())[-20:],
        "actions": recent_actions(),
        "capabilities": {
            "background_render": True,
            "arbitrary_scripts": False,
            "nodes_library": True,
            "textures_library": True,
            "rig_library": True,
            "clothes_accessories_library": True,
        },
    }


@router.get("/status")
async def get_status() -> dict[str, Any]:
    return status_snapshot()


@router.post("/setup")
async def setup_workspace(request: Request) -> dict[str, Any]:
    require_local(request)
    paths = ensure_workspace()
    log_action("Workspace Blender verificado/criado")
    return {"created": True, "paths": {key: str(value) for key, value in paths.items()}}


@router.post("/launch")
async def launch_blender(request: Request) -> dict[str, Any]:
    require_local(request)
    if not BLENDER_EXE.is_file():
        raise HTTPException(status_code=404, detail=f"Blender não encontrado: {BLENDER_EXE}")
    try:
        subprocess.Popen(
            [str(BLENDER_EXE)],
            cwd=str(BLENDER_ROOT),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        )
    except OSError as exc:
        log_action("Falha ao abrir Blender", error=type(exc).__name__)
        raise HTTPException(status_code=503, detail=f"Falha ao abrir Blender: {type(exc).__name__}") from exc
    log_action("Blender aberto manualmente", path=str(BLENDER_EXE))
    return {"started": True, "path": str(BLENDER_EXE), "time": now_iso()}


@router.post("/open")
async def open_workspace(
    request: Request,
    target: str = Query(pattern="^(projects|renders|nodes|textures|rigs|clothes|logs|install)$"),
) -> dict[str, Any]:
    require_local(request)
    if os.name != "nt":
        raise HTTPException(status_code=501, detail="Abertura de pasta disponível somente no Windows")
    paths = ensure_workspace()
    path = BLENDER_ROOT if target == "install" else paths[target]
    try:
        os.startfile(str(path))  # type: ignore[attr-defined]
    except OSError as exc:
        log_action("Falha ao abrir pasta Blender", target=target, error=type(exc).__name__)
        raise HTTPException(status_code=503, detail=f"Falha ao abrir pasta: {type(exc).__name__}") from exc
    log_action("Pasta Blender aberta", target=target, path=str(path))
    return {"opened": True, "target": target, "path": str(path)}


@router.post("/render")
async def start_render(payload: RenderRequest, request: Request) -> dict[str, Any]:
    require_local(request)
    if not BLENDER_EXE.is_file():
        raise HTTPException(status_code=404, detail=f"Blender não encontrado: {BLENDER_EXE}")
    blend_file = Path(payload.blend_file).expanduser()
    if not blend_file.is_file() or blend_file.suffix.casefold() != ".blend":
        raise HTTPException(status_code=400, detail=f"Projeto .blend inválido ou ausente: {blend_file}")
    paths = ensure_workspace()
    safe_name = SAFE_NAME.sub("_", payload.output_name).strip(" ._") or "aurion_render"
    job_id = uuid.uuid4().hex[:12]
    output_pattern = paths["renders"] / f"{safe_name}_{job_id}_####"
    log_path = paths["logs"] / f"render_{job_id}.log"
    command = [str(BLENDER_EXE), "--background", str(blend_file), "--render-output", str(output_pattern)]
    if payload.mode == "animation":
        command.append("--render-anim")
    else:
        command.extend(["--render-frame", str(payload.frame)])
    try:
        log_handle = log_path.open("wb")
        process = subprocess.Popen(
            command,
            cwd=str(BLENDER_ROOT),
            stdin=subprocess.DEVNULL,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        log_handle.close()
    except OSError as exc:
        raise HTTPException(status_code=503, detail=f"Falha ao iniciar render: {type(exc).__name__}") from exc
    job = {
        "id": job_id,
        "status": "running",
        "mode": payload.mode,
        "frame": payload.frame,
        "blend_file": str(blend_file),
        "output_pattern": str(output_pattern),
        "log": str(log_path),
        "pid": process.pid,
        "started_at": now_iso(),
    }
    _jobs[job_id] = job
    _processes[job_id] = process
    log_action("Render Blender iniciado", job_id=job_id, blend_file=str(blend_file), mode=payload.mode)
    return job


@router.get("/jobs/{job_id}")
async def job_status(job_id: str) -> dict[str, Any]:
    refresh_jobs()
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Render não encontrado nesta sessão")
    output = dict(job)
    log_path = Path(str(job["log"]))
    if log_path.is_file():
        try:
            with log_path.open("rb") as handle:
                size = log_path.stat().st_size
                handle.seek(max(0, size - 64_000))
                output["log_tail"] = handle.read().decode("utf-8", errors="replace")[-12000:]
        except OSError:
            output["log_tail"] = "Log indisponível"
    return output
