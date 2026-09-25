from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
import socket
from pathlib import Path

from aurion_superstudio import __version__
from aurion_superstudio.preflight import run_preflight


ROOT = Path(__file__).resolve().parent
PANEL_ROOT = Path(os.environ.get("AURION_PANEL_ROOT", str(ROOT))).resolve()
DATA_ROOT = PANEL_ROOT / "_aurion_superstudio"
CONFIG_FILE = DATA_ROOT / "settings.json"
DEFAULT_CONFIG = {
    "panel": "http://127.0.0.1:5058",
    "ollama": "http://127.0.0.1:11434",
    "comfy": "http://127.0.0.1:8188",
    "ffmpeg": "ffmpeg",
}


def config() -> dict[str, str]:
    try:
        return {**DEFAULT_CONFIG, **json.loads(CONFIG_FILE.read_text(encoding="utf-8"))}
    except (OSError, json.JSONDecodeError):
        return dict(DEFAULT_CONFIG)


def studio_ready(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=1) as response:
            payload = json.loads(response.read().decode("utf-8", errors="replace"))
            return response.status == 200 and payload.get("version") == __version__
    except (OSError, ValueError, urllib.error.URLError):
        return False


def port_in_use(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=1):
            return True
    except (OSError, urllib.error.URLError):
        return False


def main() -> int:
    print("[AURION] PRÉ-VOO v3.0 — a página só abrirá após o servidor responder.")
    run_preflight(PANEL_ROOT, DATA_ROOT, config())
    preferred_port = int(os.environ.get("AURION_STUDIO_PORT", "5060"))
    port = preferred_port
    if port_in_use(port) and studio_ready(port):
        print("[AURION] Esta versão do painel já está ligada; abrindo a janela existente.")
        webbrowser.open(f"http://127.0.0.1:{port}/")
        return 0
    while port_in_use(port) and port < preferred_port + 10:
        print(f"[AURION] Porta {port} ocupada por outra versão; tentando {port + 1}.")
        port += 1
    if port_in_use(port):
        print(f"[ERRO] As portas {preferred_port} a {port} estão ocupadas. Consulte logs\\startup.log.")
        return 2
    os.environ["AURION_STUDIO_PORT"] = str(port)
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    token = (DATA_ROOT / "session.token").read_text(encoding="utf-8").strip() if (DATA_ROOT / "session.token").exists() else "será criado no primeiro início"
    try:
        ip = socket.gethostbyname(socket.gethostname())
    except OSError:
        ip = "IP-DO-PC"
    (ROOT / "CONECTAR_CELULAR.txt").write_text(f"ENDERECO=http://{ip}:{port}\nTOKEN={token}\n", encoding="utf-8")
    log = (DATA_ROOT / "LOGS" / "server.log")
    log.parent.mkdir(parents=True, exist_ok=True)
    stream = log.open("a", encoding="utf-8")
    process = subprocess.Popen([sys.executable, "-m", "aurion_superstudio.app"], cwd=str(ROOT), stdout=stream, stderr=subprocess.STDOUT)
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline:
        if process.poll() is not None:
            print(f"[ERRO] O servidor encerrou com código {process.returncode}.")
            return process.returncode or 1
        if studio_ready(port):
            url = f"http://127.0.0.1:{port}/"
            print(f"[AURION] Servidor confirmado. Abrindo {url}")
            token_file = DATA_ROOT / "session.token"
            if token_file.exists():
                (ROOT / "CONECTAR_CELULAR.txt").write_text(f"ENDERECO=http://{ip}:{port}\nTOKEN={token_file.read_text(encoding='utf-8').strip()}\n", encoding="utf-8")
            webbrowser.open(url)
            return process.wait()
        time.sleep(0.25)
    process.terminate()
    print(f"[ERRO] O servidor não respondeu em 45 segundos. Consulte {log}.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
