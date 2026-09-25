from __future__ import annotations

import json
import os
import re
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BLENDER_ROOT = Path(os.environ.get("AURION_BLENDER_HOME", r"C:\Program Files\Blender Foundation\Blender 5.2"))
BLENDER_EXE = BLENDER_ROOT / "blender.exe"
C4D_ROOT = Path(os.environ.get("AURION_C4D_HOME", r"C:\Program Files\Maxon Cinema 4D 2023"))
C4D_EXE = C4D_ROOT / "Cinema 4D.exe"
EXPECTED_OCTANE = "c4dOctane-R2023.xdl64"
SAFE_NAME = re.compile(r"[^A-Za-z0-9._ -]+")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_3d_workspace(workspace: Path) -> dict[str, Path]:
    names = {
        "projects": "3D/PROJETOS",
        "renders": "3D/RENDERS",
        "nodes": "3D/NODES",
        "textures": "3D/TEXTURAS",
        "rigs": "3D/RIGS",
        "clothes": "3D/ROUPAS_E_ACESSORIOS",
        "logs": "3D/LOGS",
    }
    paths = {key: workspace / value for key, value in names.items()}
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths


def process_running(image: str) -> tuple[bool, str]:
    if os.name != "nt":
        return False, "Disponível somente no Windows"
    try:
        result = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {image}", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            errors="replace",
            timeout=5,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return f'"{image.casefold()}"' in result.stdout.casefold(), result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"tasklist falhou: {type(exc).__name__}"


def _assets(root: Path, extensions: set[str]) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.casefold() not in extensions:
            continue
        try:
            stat = path.stat()
        except OSError:
            continue
        found.append({"name": path.name, "path": str(path), "size": stat.st_size, "modified": stat.st_mtime})
    found.sort(key=lambda item: item["modified"], reverse=True)
    return found[:200]


def blender_status(workspace: Path, jobs: dict[str, dict[str, Any]], processes: dict[str, subprocess.Popen]) -> dict[str, Any]:
    for job_id, process in list(processes.items()):
        code = process.poll()
        if code is None:
            jobs[job_id]["status"] = "running"
        else:
            jobs[job_id].update(status="completed" if code == 0 else "failed", return_code=code, finished_at=now())
            processes.pop(job_id, None)
    paths = ensure_3d_workspace(workspace)
    running, detail = process_running("blender.exe")
    ext = {
        "projects": {".blend"},
        "renders": {".png", ".jpg", ".jpeg", ".exr", ".tif", ".tiff", ".webp", ".mp4"},
        "nodes": {".blend", ".json", ".osl"},
        "textures": {".png", ".jpg", ".jpeg", ".exr", ".hdr", ".tif", ".tiff", ".webp"},
        "rigs": {".blend", ".fbx", ".gltf", ".glb", ".bvh"},
        "clothes": {".blend", ".fbx", ".obj", ".gltf", ".glb", ".abc", ".usd", ".usdc", ".usdz"},
    }
    inventory = {key: _assets(paths[key], values) for key, values in ext.items()}
    return {
        "ok": BLENDER_EXE.is_file(), "installed": BLENDER_EXE.is_file(), "running": running,
        "process": detail, "version_target": "5.2", "executable": str(BLENDER_EXE),
        "paths": {key: str(value) for key, value in paths.items()},
        "inventory": inventory, "counts": {key: len(value) for key, value in inventory.items()},
        "jobs": list(jobs.values())[-30:], "checked_at": now(),
    }


def launch(executable: Path) -> dict[str, Any]:
    if not executable.is_file():
        raise FileNotFoundError(str(executable))
    subprocess.Popen(
        [str(executable)], cwd=str(executable.parent), stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
    )
    return {"ok": True, "path": str(executable), "time": now()}


def open_path(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(str(path))
    if os.name != "nt":
        raise OSError("Abertura disponível somente no Windows")
    os.startfile(str(path))  # type: ignore[attr-defined]
    return {"ok": True, "path": str(path), "time": now()}


def start_blender_render(workspace: Path, payload: dict[str, Any], jobs: dict[str, dict[str, Any]], processes: dict[str, subprocess.Popen]) -> dict[str, Any]:
    if not BLENDER_EXE.is_file():
        raise FileNotFoundError(str(BLENDER_EXE))
    blend = Path(str(payload.get("blend_file", ""))).expanduser()
    if not blend.is_file() or blend.suffix.casefold() != ".blend":
        raise ValueError(f"Projeto .blend inválido: {blend}")
    mode = str(payload.get("mode", "still"))
    if mode not in {"still", "animation"}:
        raise ValueError("Modo inválido")
    frame = max(0, min(1_000_000, int(payload.get("frame", 1))))
    output_name = SAFE_NAME.sub("_", str(payload.get("output_name", "aurion_render"))).strip(" ._") or "aurion_render"
    paths = ensure_3d_workspace(workspace)
    job_id = uuid.uuid4().hex[:12]
    output = paths["renders"] / f"{output_name}_{job_id}_####"
    log = paths["logs"] / f"render_{job_id}.log"
    command = [str(BLENDER_EXE), "--background", str(blend), "--render-output", str(output)]
    command += ["--render-anim"] if mode == "animation" else ["--render-frame", str(frame)]
    handle = log.open("wb")
    try:
        process = subprocess.Popen(command, cwd=str(BLENDER_ROOT), stdin=subprocess.DEVNULL, stdout=handle, stderr=subprocess.STDOUT, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    finally:
        handle.close()
    job = {"id": job_id, "status": "running", "mode": mode, "frame": frame, "blend_file": str(blend), "output": str(output), "log": str(log), "pid": process.pid, "started_at": now()}
    jobs[job_id], processes[job_id] = job, process
    return job


def _preference_roots() -> list[Path]:
    appdata = Path(os.environ.get("APPDATA", str(Path.home() / "AppData/Roaming"))) / "Maxon"
    return sorted((p for p in appdata.glob("Maxon Cinema 4D 2023_*") if p.is_dir()), key=lambda p: p.stat().st_mtime, reverse=True) if appdata.is_dir() else []


def c4d_status() -> dict[str, Any]:
    roots = [C4D_ROOT / "plugins" / "c4doctane", C4D_ROOT / "Exchange Plugins" / "octane"]
    for pref in _preference_roots():
        roots += [pref / "plugins" / "c4doctane", pref / "plugins" / "octane"]
    plugins = []
    for root in roots:
        if root.is_dir():
            for binary in root.glob("c4dOctane-*.xdl64"):
                plugins.append({"name": binary.name, "path": str(binary), "expected": binary.name.casefold() == EXPECTED_OCTANE.casefold(), "size": binary.stat().st_size})
    reports = [p for pref in _preference_roots() for p in pref.glob("_bugreports/**/*") if p.is_file() and "bugreport" in p.name.casefold()]
    report = max(reports, key=lambda p: p.stat().st_mtime) if reports else None
    errors: list[str] = []
    if report:
        try:
            with report.open("rb") as handle:
                handle.seek(max(0, report.stat().st_size - 512_000))
                text = handle.read().decode("utf-8", errors="replace")
            errors = [line.strip()[:500] for line in text.splitlines() if any(key in line.casefold() for key in ("error", "exception", "crash", "failed", "octane", "plugin", "res:"))][-40:]
        except OSError as exc:
            errors = [f"BugReport indisponível: {type(exc).__name__}"]
    running, detail = process_running("Cinema 4D.exe")
    expected = [p for p in plugins if p["expected"]]
    wrong = [p for p in plugins if not p["expected"]]
    solutions = []
    if not C4D_EXE.is_file(): solutions.append(f"Cinema 4D não encontrado: {C4D_EXE}")
    if not expected: solutions.append(f"Binário oficial compatível esperado não encontrado: {EXPECTED_OCTANE}")
    if len(expected) > 1: solutions.append("Mais de uma cópia R2023 encontrada. Isole duplicatas antes de testar.")
    if wrong: solutions.append("Binários de outras versões encontrados: " + ", ".join(sorted({p["name"] for p in wrong})))
    joined = "\n".join(errors).casefold()
    if "res:" in joined: solutions.append("Há indício de recursos incompatíveis. Mantenha res e Lib300 do mesmo pacote oficial.")
    if "octane" in joined: solutions.append("O relatório cita Octane. Confirme plugin oficial, driver NVIDIA e compatibilidade antes de reabrir.")
    if not solutions: solutions.append("Nenhuma incompatibilidade conhecida foi reconhecida no trecho atual.")
    return {"ok": C4D_EXE.is_file(), "installed": C4D_EXE.is_file(), "running": running, "process": detail, "plugins": plugins, "errors": errors, "solutions": solutions, "paths": {"install": str(C4D_ROOT), "executable": str(C4D_EXE), "plugin": str(C4D_ROOT / "plugins" / "c4doctane"), "bugreport": str(report) if report else None}, "checked_at": now()}
