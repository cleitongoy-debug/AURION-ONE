#!/usr/bin/env python3
"""AURION ONE T8i v0.9 — inicializador único e reversível.

Uso no repositório:
    py AURION_ONE_T8I_V09.py

Este arquivo não altera ADAPTA.py nem ADAPTA_BASE_TRAVADA.py.
Cria/usa remote-agent/.venv, instala dependências isoladas e abre /one.
"""

from __future__ import annotations

import os
import secrets
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import venv
import webbrowser
from pathlib import Path
from urllib.parse import quote

VERSION = "0.9.0"
ROOT = Path(__file__).resolve().parent
AGENT_ROOT = ROOT / "remote-agent"
VENV_ROOT = AGENT_ROOT / ".venv"
VENV_PYTHON = VENV_ROOT / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
ENV_FILE = AGENT_ROOT / ".env"
ENV_EXAMPLE = AGENT_ROOT / ".env.example"


def fail(message: str, code: int = 1) -> None:
    print(f"[AURION][ERRO] {message}")
    raise SystemExit(code)


def ensure_repository() -> None:
    required = [
        AGENT_ROOT / "pyproject.toml",
        AGENT_ROOT / "aurion_remote" / "app.py",
        AGENT_ROOT / "aurion_remote" / "one_panel.py",
        AGENT_ROOT / "aurion_remote" / "t8i_lab.py",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if missing:
        fail("Arquivos obrigatórios ausentes: " + ", ".join(missing))


def run_checked(command: list[str], label: str) -> None:
    print(f"[AURION] {label}...")
    completed = subprocess.run(command, cwd=AGENT_ROOT)
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
        venv.EnvBuilder(with_pip=True, clear=False).create(VENV_ROOT)

    run_checked(
        [str(VENV_PYTHON), "-m", "pip", "install", "--disable-pip-version-check", "--no-input", "-e", str(AGENT_ROOT)],
        "Instalação do núcleo",
    )

    print("[AURION][T8I] Instalando suporte CR3 (rawpy, numpy, Pillow e tifffile)...")
    optional = subprocess.run(
        [
            str(VENV_PYTHON),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-input",
            "-e",
            f"{AGENT_ROOT}[t8i]",
        ],
        cwd=AGENT_ROOT,
    )
    if optional.returncode:
        print("[AURION][AVISO] Suporte CR3 não instalou. O painel abrirá e mostrará o diagnóstico real.")

    completed = subprocess.run([str(VENV_PYTHON), str(Path(__file__).resolve()), "--inside-venv"], cwd=ROOT)
    raise SystemExit(completed.returncode)


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
            if line.startswith("AURION_API_TOKEN="):
                updated.append(f"AURION_API_TOKEN={token}")
                replaced = True
            else:
                updated.append(line)
        if not replaced:
            updated.insert(0, f"AURION_API_TOKEN={token}")
        ENV_FILE.write_text("\n".join(updated) + "\n", encoding="utf-8")
        print("[AURION] Token local seguro criado no .env.")
    return token


def open_when_ready(port: int, token: str) -> None:
    health = f"http://127.0.0.1:{port}/health"
    for _ in range(80):
        try:
            with urllib.request.urlopen(health, timeout=1) as response:
                if 200 <= response.status < 500:
                    url = f"http://127.0.0.1:{port}/one#token={quote(token)}"
                    webbrowser.open(url)
                    return
        except (OSError, urllib.error.URLError):
            time.sleep(0.25)
    print(f"[AURION][AVISO] Abra manualmente: http://127.0.0.1:{port}/one")


def main() -> None:
    print(f"[AURION ONE T8i] v{VERSION}")
    ensure_repository()
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
    if "/api/t8i/status" not in registered:
        app.include_router(t8i_router, dependencies=[Depends(require_token)])

    cfg = get_settings()
    threading.Thread(target=open_when_ready, args=(cfg.port, token), daemon=True).start()
    print(f"[AURION] Painel: http://127.0.0.1:{cfg.port}/one")
    print("[AURION] Feche esta janela ou pressione Ctrl+C para encerrar somente este servidor.")
    uvicorn.run(app, host=cfg.bind_host, port=cfg.port, reload=False)


if __name__ == "__main__":
    main()
