#!/usr/bin/env python3
"""AURION ONE T8i v0.9.1 — inicializador único, local e reversível.

Pode ficar na raiz do repositório, em Downloads ou no Desktop.
Ele procura a instalação AURION-ONE, cria um ambiente Python isolado,
instala as dependências e abre a aba /one sem alterar ADAPTA.py nem
ADAPTA_BASE_TRAVADA.py.
"""

from __future__ import annotations

import json
import os
import secrets
import shutil
import subprocess
import sys
import threading
import time
import traceback
import urllib.error
import urllib.request
import venv
import webbrowser
from pathlib import Path
from urllib.parse import quote

VERSION = "0.9.1"
SCRIPT_FILE = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_FILE.parent
ERROR_LOG = SCRIPT_DIR / "AURION_T8I_STARTUP_ERROR.log"


def is_repo_root(path: Path) -> bool:
    return all(
        item.is_file()
        for item in (
            path / "remote-agent" / "pyproject.toml",
            path / "remote-agent" / "aurion_remote" / "app.py",
            path / "remote-agent" / "aurion_remote" / "one_panel.py",
            path / "remote-agent" / "aurion_remote" / "t8i_lab.py",
        )
    )


def discover_root() -> Path:
    candidates: list[Path] = []
    configured = os.environ.get("AURION_ONE_HOME", "").strip()
    if configured:
        candidates.append(Path(configured))

    candidates.extend([SCRIPT_DIR, Path.cwd()])
    candidates.extend(SCRIPT_DIR.parents)
    candidates.extend(Path.cwd().parents)

    if os.name == "nt":
        candidates.extend(
            [
                Path(r"C:\AURION-ONE"),
                Path(r"D:\AURION-ONE"),
                Path(r"E:\AURION-ONE"),
                Path(r"C:\AURION-QB-QUANTUN"),
                Path(r"D:\AURION-QB-QUANTUN"),
            ]
        )

    checked: set[str] = set()
    for candidate in candidates:
        try:
            resolved = candidate.expanduser().resolve()
        except OSError:
            continue
        key = str(resolved).casefold()
        if key in checked:
            continue
        checked.add(key)
        if is_repo_root(resolved):
            return resolved

    locations = "\n".join(f"  - {path}" for path in candidates[:12])
    raise FileNotFoundError(
        "Não encontrei a pasta completa do AURION-ONE.\n"
        "O arquivo pode estar em Downloads, mas a pasta C:\\AURION-ONE precisa conter remote-agent.\n"
        "Locais verificados:\n" + locations
    )


ROOT = discover_root()
AGENT_ROOT = ROOT / "remote-agent"
VENV_ROOT = AGENT_ROOT / ".venv"
VENV_PYTHON = VENV_ROOT / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
ENV_FILE = AGENT_ROOT / ".env"
ENV_EXAMPLE = AGENT_ROOT / ".env.example"


def pause() -> None:
    if os.name == "nt" and sys.stdin and sys.stdin.isatty():
        try:
            input("\nPressione ENTER para fechar...")
        except (EOFError, KeyboardInterrupt):
            pass


def fail(message: str, code: int = 1) -> None:
    text = f"[AURION][ERRO] {message}"
    print(text)
    try:
        ERROR_LOG.write_text(text + "\n", encoding="utf-8")
        print(f"[AURION] Diagnóstico salvo em: {ERROR_LOG}")
    except OSError:
        pass
    pause()
    raise SystemExit(code)


def run_checked(command: list[str], label: str) -> None:
    print(f"[AURION] {label}...")
    try:
        completed = subprocess.run(command, cwd=AGENT_ROOT)
    except OSError as exc:
        fail(f"{label}: não foi possível iniciar o processo: {exc}")
    if completed.returncode:
        fail(f"{label} falhou com código {completed.returncode}.")


def ensure_venv_and_relaunch() -> None:
    try:
        same_python = VENV_PYTHON.exists() and Path(sys.executable).resolve() == VENV_PYTHON.resolve()
    except OSError:
        same_python = False
    if same_python:
        return

    if not VENV_PYTHON.exists():
        print(f"[AURION] Criando ambiente isolado em {VENV_ROOT}...")
        try:
            venv.EnvBuilder(with_pip=True, clear=False).create(VENV_ROOT)
        except Exception as exc:
            fail(f"Não consegui criar o ambiente Python: {type(exc).__name__}: {exc}")

    run_checked(
        [
            str(VENV_PYTHON), "-m", "pip", "install",
            "--disable-pip-version-check", "--no-input", "-e", str(AGENT_ROOT),
        ],
        "Instalação do núcleo",
    )

    print("[AURION][T8I] Instalando suporte CR3...")
    optional = subprocess.run(
        [
            str(VENV_PYTHON), "-m", "pip", "install",
            "--disable-pip-version-check", "--no-input", "-e", f"{AGENT_ROOT}[t8i]",
        ],
        cwd=AGENT_ROOT,
    )
    if optional.returncode:
        print("[AURION][AVISO] O suporte CR3 falhou, mas o painel será aberto com diagnóstico.")

    completed = subprocess.run(
        [str(VENV_PYTHON), str(SCRIPT_FILE), "--inside-venv"],
        cwd=ROOT,
    )
    if completed.returncode:
        fail(f"A execução dentro do ambiente isolado terminou com código {completed.returncode}.")
    raise SystemExit(0)


def ensure_env() -> str:
    if not ENV_FILE.exists():
        if ENV_EXAMPLE.is_file():
            shutil.copy2(ENV_EXAMPLE, ENV_FILE)
        else:
            ENV_FILE.write_text("", encoding="utf-8")

    lines = ENV_FILE.read_text(encoding="utf-8-sig").splitlines()
    values: dict[str, str] = {}
    for line in lines:
        if line.strip() and not line.lstrip().startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()

    token = values.get("AURION_API_TOKEN", "")
    if len(token) < 32 or token.startswith("troque-por-"):
        token = secrets.token_hex(32)
        replaced = False
        updated: list[str] = []
        for line in lines:
            if line.strip().startswith("AURION_API_TOKEN="):
                updated.append(f"AURION_API_TOKEN={token}")
                replaced = True
            else:
                updated.append(line)
        if not replaced:
            updated.insert(0, f"AURION_API_TOKEN={token}")
        ENV_FILE.write_text("\n".join(updated) + "\n", encoding="utf-8")
        print("[AURION] Token local seguro criado.")
    return token


def endpoint_json(url: str, timeout: float = 1.5) -> dict | None:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8", errors="replace"))
    except (OSError, ValueError, urllib.error.URLError):
        return None


def server_has_t8i(port: int) -> bool:
    spec = endpoint_json(f"http://127.0.0.1:{port}/openapi.json")
    return bool(spec and "/api/t8i/status" in spec.get("paths", {}))


def open_panel(port: int, token: str) -> None:
    url = f"http://127.0.0.1:{port}/one#token={quote(token)}"
    print(f"[AURION] Abrindo: http://127.0.0.1:{port}/one")
    if not webbrowser.open(url):
        print(f"[AURION][AVISO] Abra manualmente: {url}")


def open_when_ready(port: int, token: str) -> None:
    for _ in range(120):
        if server_has_t8i(port):
            open_panel(port, token)
            return
        time.sleep(0.25)
    print(f"[AURION][AVISO] O servidor não confirmou a rota T8i. Veja {ERROR_LOG}.")


def main() -> None:
    print(f"[AURION ONE T8i] v{VERSION}")
    print(f"[AURION] Repositório encontrado: {ROOT}")
    ensure_venv_and_relaunch()
    token = ensure_env()

    os.chdir(AGENT_ROOT)
    sys.path.insert(0, str(AGENT_ROOT))

    import uvicorn
    from fastapi import Depends
    from aurion_remote.app import app, require_token
    from aurion_remote.config import get_settings
    from aurion_remote.one_panel import router as one_router
    from aurion_remote.t8i_lab import router as t8i_router

    registered = {getattr(route, "path", "") for route in app.routes}
    if "/one" not in registered:
        app.include_router(one_router)
    registered = {getattr(route, "path", "") for route in app.routes}
    if "/api/t8i/status" not in registered:
        app.include_router(t8i_router, dependencies=[Depends(require_token)])

    cfg = get_settings()

    existing_health = endpoint_json(f"http://127.0.0.1:{cfg.port}/health")
    if existing_health:
        if server_has_t8i(cfg.port):
            print("[AURION] A versão T8i já está rodando; apenas abrindo o painel.")
            open_panel(cfg.port, token)
            return
        fail(
            f"A porta {cfg.port} está ocupada por uma versão antiga. "
            "Feche a janela anterior do AURION e execute este arquivo novamente."
        )

    threading.Thread(target=open_when_ready, args=(cfg.port, token), daemon=True).start()
    print(f"[AURION] Servidor iniciando em http://127.0.0.1:{cfg.port}")
    print("[AURION] Esta janela precisa permanecer aberta.")
    uvicorn.run(app, host=cfg.bind_host, port=cfg.port, reload=False)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        details = traceback.format_exc()
        print("\n[AURION][FALHA NÃO TRATADA]\n" + details)
        try:
            ERROR_LOG.write_text(details, encoding="utf-8")
            print(f"[AURION] Erro completo salvo em: {ERROR_LOG}")
        except OSError:
            pass
        pause()
        raise SystemExit(1)
