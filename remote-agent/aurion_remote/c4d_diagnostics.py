from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request

router = APIRouter(prefix="/api/c4d", tags=["c4d-diagnostics"])

DATA_ROOT = Path(__file__).resolve().parents[1] / "data" / "c4d_diagnostics"
ACTION_LOG = DATA_ROOT / "actions.jsonl"
EXPECTED_PLUGIN = "c4dOctane-R2023.xdl64"
ERROR_WORDS = ("error", "exception", "crash", "failed", "failure", "octane", "plugin", "res:")
_last_signature: str | None = None


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def program_root() -> Path:
    base = Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
    return base / "Maxon Cinema 4D 2023"


def preference_roots() -> list[Path]:
    roaming = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    maxon = roaming / "Maxon"
    if not maxon.is_dir():
        return []
    return sorted(
        (p for p in maxon.glob("Maxon Cinema 4D 2023_*") if p.is_dir() and not re.search(r"_[cswxp]$", p.name, re.I)),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )


def candidate_plugin_roots() -> list[Path]:
    root = program_root()
    candidates = [
        root / "plugins" / "c4doctane",
        root / "Exchange Plugins" / "octane",
    ]
    for pref in preference_roots():
        candidates.extend([pref / "plugins" / "c4doctane", pref / "plugins" / "octane"])
    unique: list[Path] = []
    seen: set[str] = set()
    for path in candidates:
        key = str(path).casefold()
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return unique


def discover_plugins() -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for root in candidate_plugin_roots():
        if not root.is_dir():
            continue
        for binary in sorted(root.glob("c4dOctane-*.xdl64")):
            found.append({
                "name": binary.name,
                "path": str(binary),
                "expected_for_c4d_2023": binary.name.casefold() == EXPECTED_PLUGIN.casefold(),
                "size": binary.stat().st_size,
                "modified_at": datetime.fromtimestamp(binary.stat().st_mtime, UTC).isoformat(),
            })
    return found


def process_running() -> tuple[bool, str]:
    if os.name != "nt":
        return False, "Monitor de processo disponível somente no Windows"
    try:
        completed = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq Cinema 4D.exe", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            errors="replace",
            timeout=5,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"tasklist indisponível: {type(exc).__name__}"
    active = '"Cinema 4D.exe"' in completed.stdout
    return active, completed.stdout.strip() if active else "Cinema 4D.exe não encontrado na lista de processos"


def latest_bugreport() -> Path | None:
    reports: list[Path] = []
    for pref in preference_roots():
        reports.extend(path for path in pref.glob("_bugreports/**/*") if path.is_file() and "bugreport" in path.name.casefold())
    return max(reports, key=lambda p: p.stat().st_mtime) if reports else None


def error_excerpt(path: Path | None) -> list[str]:
    if path is None or not path.is_file():
        return []
    try:
        with path.open("rb") as handle:
            size = path.stat().st_size
            handle.seek(max(0, size - 512_000))
            text = handle.read().decode("utf-8", errors="replace")
    except OSError as exc:
        return [f"Não foi possível ler BugReport: {type(exc).__name__}"]
    lines = []
    for raw in text.splitlines():
        line = raw.strip()
        if line and any(word in line.casefold() for word in ERROR_WORDS):
            lines.append(line[:500])
    return lines[-40:]


def action(message: str, **details: Any) -> None:
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    record = {"time": now_iso(), "message": message, **details}
    with ACTION_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def recent_actions(limit: int = 40) -> list[str]:
    if not ACTION_LOG.is_file():
        return []
    try:
        lines = ACTION_LOG.read_text(encoding="utf-8", errors="replace").splitlines()[-limit:]
    except OSError:
        return []
    output = []
    for line in lines:
        try:
            item = json.loads(line)
            output.append(f"{item.get('time', '?')} · {item.get('message', line)}")
        except ValueError:
            output.append(line[:500])
    return output


def paths_snapshot(report: Path | None) -> dict[str, Any]:
    root = program_root()
    prefs = preference_roots()
    return {
        "cinema4d_install": str(root),
        "cinema4d_executable": str(root / "Cinema 4D.exe"),
        "primary_plugin_folder": str(root / "plugins" / "c4doctane"),
        "expected_octane_binary": str(root / "plugins" / "c4doctane" / EXPECTED_PLUGIN),
        "preference_folders": [str(p) for p in prefs],
        "latest_bugreport": str(report) if report else None,
        "action_log": str(ACTION_LOG),
    }


def solutions_for(plugins: list[dict[str, Any]], errors: list[str], exe_exists: bool) -> list[str]:
    solutions: list[str] = []
    if not exe_exists:
        solutions.append("Cinema 4D 2023 não foi encontrado no caminho padrão. Confirme a instalação ou registre o caminho correto.")
    expected = [item for item in plugins if item["expected_for_c4d_2023"]]
    wrong = [item for item in plugins if not item["expected_for_c4d_2023"]]
    if not expected:
        solutions.append(f"Ausente: {EXPECTED_PLUGIN}. Use um pacote oficial compatível com Cinema 4D 2023.")
    if len(expected) > 1:
        solutions.append("Há mais de uma cópia do binário R2023 em caminhos de plugin. Mantenha somente uma instalação ativa e mova as duplicatas para backup.")
    if wrong:
        names = ", ".join(sorted({item["name"] for item in wrong}))
        solutions.append(f"Binários de outras versões detectados: {names}. Isole-os fora das pastas pesquisadas pelo Cinema 4D.")
    joined = "\n".join(errors).casefold()
    if "c4doctane" in joined or "octane" in joined:
        solutions.append("O BugReport cita Octane. Compare plugin, Cinema 4D, driver NVIDIA, res e Lib300 do mesmo pacote antes de reabrir.")
    if "res:" in joined:
        solutions.append("Erro de recurso detectado. Evite misturar a pasta res ou Lib300 entre builds diferentes do plugin.")
    if "3rd party plugin" in joined or "third party plugin" in joined:
        solutions.append("Falha de plugin de terceiros detectada. Teste o C4D com a pasta do plugin isolada e restaure apenas após validar a versão correta.")
    if not solutions:
        solutions.append("Nenhuma incompatibilidade conhecida foi reconhecida. Abra o C4D, reproduza o erro e atualize o diagnóstico.")
    return solutions


def build_snapshot(record_change: bool = True) -> dict[str, Any]:
    global _last_signature
    root = program_root()
    exe = root / "Cinema 4D.exe"
    running, process_detail = process_running()
    plugins = discover_plugins()
    report = latest_bugreport()
    errors = error_excerpt(report)
    snapshot = {
        "checked_at": now_iso(),
        "process": {"running": running, "detail": process_detail},
        "cinema4d": {"installed": exe.is_file(), "version_target": "2023", "executable": str(exe)},
        "octane": {
            "expected_binary": EXPECTED_PLUGIN,
            "plugin_count": len(plugins),
            "plugins": plugins,
            "compatible_binary_present": any(item["expected_for_c4d_2023"] for item in plugins),
        },
        "paths": paths_snapshot(report),
        "errors": errors,
        "solutions": solutions_for(plugins, errors, exe.is_file()),
    }
    signature = json.dumps({
        "running": running,
        "installed": exe.is_file(),
        "plugins": [(item["name"], item["path"], item["size"]) for item in plugins],
        "report": str(report) if report else None,
        "errors": errors[-5:],
    }, ensure_ascii=False, sort_keys=True)
    if record_change and signature != _last_signature:
        action("Estado C4D/Octane alterado", running=running, plugin_count=len(plugins), bugreport=str(report) if report else None)
        _last_signature = signature
    snapshot["actions"] = recent_actions()
    return snapshot


def local_request(request: Request) -> bool:
    return bool(request.client and request.client.host in {"127.0.0.1", "::1"})


@router.get("/status")
async def status_snapshot() -> dict[str, Any]:
    return build_snapshot()


@router.post("/launch")
async def launch_c4d(request: Request) -> dict[str, Any]:
    if not local_request(request):
        raise HTTPException(status_code=403, detail="Abertura permitida somente no próprio PC")
    exe = program_root() / "Cinema 4D.exe"
    if not exe.is_file():
        action("Abertura falhou: executável ausente", path=str(exe))
        raise HTTPException(status_code=404, detail=f"Executável não encontrado: {exe}")
    try:
        subprocess.Popen(
            [str(exe)],
            cwd=str(exe.parent),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        )
    except OSError as exc:
        action("Abertura falhou", error=type(exc).__name__, path=str(exe))
        raise HTTPException(status_code=503, detail=f"Falha ao abrir Cinema 4D: {type(exc).__name__}") from exc
    action("Cinema 4D iniciado manualmente", path=str(exe))
    return {"started": True, "path": str(exe), "time": now_iso()}


@router.post("/open")
async def open_known_path(request: Request, target: str = Query(pattern="^(plugin|preferences|bugreport|install|actionlog)$")) -> dict[str, Any]:
    if not local_request(request):
        raise HTTPException(status_code=403, detail="Abertura permitida somente no próprio PC")
    report = latest_bugreport()
    prefs = preference_roots()
    mapping: dict[str, Path | None] = {
        "plugin": program_root() / "plugins" / "c4doctane",
        "preferences": prefs[0] if prefs else None,
        "bugreport": report,
        "install": program_root(),
        "actionlog": ACTION_LOG,
    }
    path = mapping[target]
    if path is None or not path.exists():
        action("Abertura de caminho falhou", target=target, path=str(path) if path else None)
        raise HTTPException(status_code=404, detail=f"Caminho indisponível para: {target}")
    if os.name != "nt":
        raise HTTPException(status_code=501, detail="Abertura de caminho disponível somente no Windows")
    try:
        os.startfile(str(path))  # type: ignore[attr-defined]
    except OSError as exc:
        action("Abertura de caminho falhou", target=target, path=str(path), error=type(exc).__name__)
        raise HTTPException(status_code=503, detail=f"Falha ao abrir caminho: {type(exc).__name__}") from exc
    action("Caminho aberto manualmente", target=target, path=str(path))
    return {"opened": True, "target": target, "path": str(path), "time": now_iso()}
