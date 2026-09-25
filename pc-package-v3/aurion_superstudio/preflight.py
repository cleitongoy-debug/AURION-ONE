from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


KNOWN_PROGRAMS: dict[str, list[str]] = {
    "python": ["python.exe", "python"],
    "git": ["git.exe", "git"],
    "ffmpeg": ["ffmpeg.exe", "ffmpeg"],
    "ollama": ["ollama.exe", "ollama"],
    "adb": ["adb.exe", "adb"],
    "hugo": ["hugo.exe", "hugo"],
}

WINDOWS_CANDIDATES: dict[str, list[str]] = {
    "blender": [r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"],
    "cinema4d": [r"C:\Program Files\Maxon Cinema 4D 2023\Cinema 4D.exe"],
    "ollama": [r"%LOCALAPPDATA%\Programs\Ollama\ollama.exe", r"%LOCALAPPDATA%\Ollama\ollama.exe"],
    "ffmpeg": [r"C:\ffmpeg\bin\ffmpeg.exe", r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"],
    "adb": [r"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe"],
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hidden_flags() -> int:
    return getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0


def _http_ok(url: str, timeout: float = 1.5) -> bool:
    try:
        return requests.get(url, timeout=timeout).status_code < 500
    except requests.RequestException:
        return False


def discover_programs() -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    for name, commands in KNOWN_PROGRAMS.items():
        path = next((shutil.which(command) for command in commands if shutil.which(command)), None)
        found[name] = {"found": bool(path), "path": path}
    if os.name == "nt":
        for name, candidates in WINDOWS_CANDIDATES.items():
            for raw in candidates:
                candidate = Path(os.path.expandvars(raw))
                if candidate.is_file():
                    found[name] = {"found": True, "path": str(candidate)}
                    break
            else:
                found.setdefault(name, {"found": False, "path": None})
    return found


def discover_drives() -> list[dict[str, Any]]:
    drives: list[dict[str, Any]] = []
    try:
        import psutil

        seen: set[str] = set()
        for part in psutil.disk_partitions(all=False):
            mount = part.mountpoint
            if mount.casefold() in seen:
                continue
            seen.add(mount.casefold())
            item: dict[str, Any] = {"mount": mount, "device": part.device, "filesystem": part.fstype, "options": part.opts}
            try:
                usage = psutil.disk_usage(mount)
                item.update(total=usage.total, free=usage.free, used_percent=usage.percent, accessible=True)
            except OSError as exc:
                item.update(accessible=False, error=f"{type(exc).__name__}: {exc}")
            drives.append(item)
    except Exception as exc:
        drives.append({"accessible": False, "error": f"Inventário de discos falhou: {type(exc).__name__}: {exc}"})
    return drives


def scan_aurion_files(panel_root: Path, drives: list[dict[str, Any]]) -> dict[str, Any]:
    """Inventário limitado e somente leitura; não percorre discos inteiros por horas."""
    wanted = {
        "ADAPTA.py", "ADAPTA_BASE_TRAVADA.py", "FUNCIONANDO.py",
        "AURION_ONE_FUNCIONANDO_v2.py", "main.py", "run_nvidia_gpu.bat",
        "run_cpu.bat", "extra_model_paths.yaml", "ffmpeg.exe", "ollama.exe",
    }
    roots: list[Path] = [panel_root]
    home = Path.home()
    roots += [home / "Desktop", home / "Downloads"]
    for drive in drives:
        mount = drive.get("mount")
        if mount:
            root = Path(str(mount))
            roots += [root / "AURION-ONE", root / "ComfyUI", root / "AI", root / "Projetos"]

    results: list[dict[str, Any]] = []
    checked: set[str] = set()
    deadline = time.monotonic() + 18
    max_files = 20_000
    inspected = 0
    for root in roots:
        if time.monotonic() >= deadline or inspected >= max_files:
            break
        try:
            resolved = root.resolve()
        except OSError:
            continue
        key = str(resolved).casefold()
        if key in checked or not resolved.exists():
            continue
        checked.add(key)
        if resolved.is_file():
            paths = [resolved]
        else:
            try:
                paths = resolved.rglob("*")
            except OSError:
                continue
        try:
            for path in paths:
                if time.monotonic() >= deadline or inspected >= max_files:
                    break
                inspected += 1
                try:
                    if path.is_file() and path.name.casefold() in {name.casefold() for name in wanted}:
                        stat = path.stat()
                        results.append({"name": path.name, "path": str(path), "size": stat.st_size, "modified": stat.st_mtime})
                except OSError:
                    continue
        except OSError:
            continue
    return {"files": results[:500], "inspected": inspected, "roots": [str(root) for root in roots], "limited": True}


def _detached(command: list[str], cwd: Path | None = None) -> subprocess.Popen:
    flags = _hidden_flags()
    if os.name == "nt":
        flags |= getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    return subprocess.Popen(command, cwd=str(cwd) if cwd else None, stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=flags)


def start_infrastructure(programs: dict[str, dict[str, Any]], panel_root: Path, config: dict[str, str], scan: dict[str, Any]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []

    if _http_ok(config["ollama"].rstrip("/") + "/api/tags"):
        actions.append({"service": "ollama", "status": "already_online"})
    elif programs.get("ollama", {}).get("found"):
        try:
            proc = _detached([str(programs["ollama"]["path"]), "serve"])
            actions.append({"service": "ollama", "status": "started", "pid": proc.pid})
        except OSError as exc:
            actions.append({"service": "ollama", "status": "failed", "error": str(exc)})
    else:
        actions.append({"service": "ollama", "status": "not_found"})

    panel_url = config["panel"].rstrip("/") + "/health"
    if _http_ok(panel_url):
        actions.append({"service": "painel_real", "status": "already_online"})
    else:
        entry = next((panel_root / name for name in ("FUNCIONANDO.py", "AURION_ONE_FUNCIONANDO_v2.py", "ADAPTA.py") if (panel_root / name).is_file()), None)
        if entry:
            try:
                command = ["py", "-3", str(entry)] if os.name == "nt" and shutil.which("py") else [sys.executable, str(entry)]
                proc = _detached(command, panel_root)
                actions.append({"service": "painel_real", "status": "started", "pid": proc.pid, "entry": str(entry)})
            except OSError as exc:
                actions.append({"service": "painel_real", "status": "failed", "error": str(exc)})
        else:
            actions.append({"service": "painel_real", "status": "entry_not_found"})

    comfy_url = config["comfy"].rstrip("/") + "/system_stats"
    if _http_ok(comfy_url):
        actions.append({"service": "comfyui", "status": "already_online"})
    else:
        candidates = [Path(item["path"]) for item in scan.get("files", []) if "comfy" in item.get("path", "").casefold()]
        launcher = next((path for path in candidates if path.name.casefold() == "run_nvidia_gpu.bat"), None)
        main_py = next((path for path in candidates if path.name.casefold() == "main.py"), None)
        try:
            if launcher and os.name == "nt":
                proc = _detached(["cmd", "/d", "/c", str(launcher)], launcher.parent)
                actions.append({"service": "comfyui", "status": "started", "pid": proc.pid, "entry": str(launcher)})
            elif main_py:
                command = ["py", "-3", str(main_py), "--listen", "127.0.0.1"] if os.name == "nt" and shutil.which("py") else [sys.executable, str(main_py), "--listen", "127.0.0.1"]
                proc = _detached(command, main_py.parent)
                actions.append({"service": "comfyui", "status": "started", "pid": proc.pid, "entry": str(main_py)})
            else:
                actions.append({"service": "comfyui", "status": "not_started_no_verified_launcher"})
        except OSError as exc:
            actions.append({"service": "comfyui", "status": "failed", "error": str(exc)})
    return actions


def warm_services(config: dict[str, str], seconds: int = 20) -> dict[str, Any]:
    endpoints = {
        "painel_real": config["panel"].rstrip("/") + "/health",
        "ollama": config["ollama"].rstrip("/") + "/api/tags",
        "comfyui": config["comfy"].rstrip("/") + "/system_stats",
    }
    state = {name: False for name in endpoints}
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline and not all(state.values()):
        for name, url in endpoints.items():
            if not state[name]:
                state[name] = _http_ok(url, 1)
        if not all(state.values()):
            time.sleep(0.5)
    return {name: {"online": state[name], "url": url} for name, url in endpoints.items()}


def run_preflight(panel_root: Path, data_root: Path, config: dict[str, str]) -> dict[str, Any]:
    started = time.perf_counter()
    print("[AURION][1/5] Inventariando programas instalados...")
    programs = discover_programs()
    print("[AURION][2/5] Identificando discos internos e externos...")
    drives = discover_drives()
    print("[AURION][3/5] Fazendo scan seguro e limitado de arquivos importantes...")
    scan = scan_aurion_files(panel_root, drives)
    print("[AURION][4/5] Ativando infraestrutura local reconhecida...")
    actions = start_infrastructure(programs, panel_root, config, scan)
    print("[AURION][5/5] Aquecendo e confirmando APIs...")
    services = warm_services(config)
    report = {
        "ok": True, "started_at": utc_now(), "duration_seconds": round(time.perf_counter() - started, 2),
        "panel_root": str(panel_root), "programs": programs, "drives": drives, "scan": scan,
        "actions": actions, "services": services,
        "policy": "Somente leitura no scan; nenhum programa foi apagado, atualizado ou substituído.",
    }
    data_root.mkdir(parents=True, exist_ok=True)
    target = data_root / "preflight-latest.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[AURION] Relatório de pré-voo: {target}")
    return report
