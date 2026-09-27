"""AURION ONE vNext: painel local paralelo, somente biblioteca padrão."""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import sqlite3
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
PROJECTS = DATA / "projects"
RENDERS = DATA / "renders"
LOGS = DATA / "logs"
for folder in (DATA, PROJECTS, RENDERS, LOGS):
    folder.mkdir(parents=True, exist_ok=True)
DB = sqlite3.connect(DATA / "aurion.sqlite3", check_same_thread=False)
DB.execute("CREATE TABLE IF NOT EXISTS chat(id INTEGER PRIMARY KEY, ts TEXT, role TEXT, model TEXT, text TEXT)")
DB.execute("CREATE TABLE IF NOT EXISTS notes(id INTEGER PRIMARY KEY, ts TEXT, text TEXT)")
DB.commit()
LOCK = threading.RLock()
TOKEN = secrets.token_urlsafe(32)
JOB = {"state": "untested", "progress": None, "message": "Selecione uma cena em data/projects.", "file": None}
PORT = int(os.environ.get("AURION_VNEXT_PORT", "8766"))
LOCAL = f"http://127.0.0.1:{PORT}"
C4D = Path(os.environ.get("AURION_C4D_HOME", r"C:\Program Files\Maxon Cinema 4D 2023"))
PLUGIN = C4D / "plugins" / "c4doctane" / "c4dOctane-R2023.xdl64"


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def get_json(url, timeout=2):
    with urllib.request.urlopen(url, timeout=timeout) as response:
        if response.status != 200:
            raise ValueError(f"HTTP {response.status}")
        return json.load(response)


def probe(url, timeout=2):
    with urllib.request.urlopen(url, timeout=timeout) as response:
        if response.status != 200:
            raise ValueError(f"HTTP {response.status}")
        return response.read(1)


def status():
    services = {}
    for name, url in {
        "ollama": "http://127.0.0.1:11434/api/tags",
        "comfyui": "http://127.0.0.1:8188/system_stats",
        "webui": "http://127.0.0.1:8080/health",
    }.items():
        try:
            data = get_json(url) if name == "ollama" else None
            if name != "ollama":
                probe(url)
            services[name] = {"state": "online", "checked_at": now(), "models": len(data.get("models", [])) if name == "ollama" else None}
        except Exception as exc:
            services[name] = {"state": "offline", "checked_at": now(), "reason": type(exc).__name__}
    return {
        "services": services,
        "c4d": {"state": "detected" if (C4D / "Cinema 4D.exe").is_file() else "absent"},
        "octane": {"state": "detected" if PLUGIN.is_file() else "absent"},
        "render": dict(JOB),
        "scenes": [p.name for p in sorted(PROJECTS.glob("*.c4d")) if p.is_file()],
        "version": "0.4.0",
    }


def models():
    return [m.get("name") for m in get_json("http://127.0.0.1:11434/api/tags").get("models", []) if m.get("name")]


def chat(message, model):
    available = models()
    if model not in available:
        raise ValueError("Modelo não disponível no Ollama local.")
    with LOCK:
        rows = DB.execute("SELECT role,text FROM chat ORDER BY id DESC LIMIT 12").fetchall()
    messages = [{"role": "system", "content": "Você é AURION ONE, assistente local. Seja preciso. Não afirme executar ações que não executou."}]
    messages += [{"role": role, "content": content} for role, content in reversed(rows)]
    messages.append({"role": "user", "content": message})
    payload = json.dumps({"model": model, "messages": messages, "stream": False}).encode()
    request = urllib.request.Request("http://127.0.0.1:11434/api/chat", data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=180) as response:
        answer = json.load(response).get("message", {}).get("content", "")
    if not answer:
        raise ValueError("Ollama não devolveu texto.")
    with LOCK:
        DB.executemany("INSERT INTO chat(ts,role,model,text) VALUES (?,?,?,?)",
                       [(now(), "user", model, message), (now(), "assistant", model, answer)])
        DB.commit()
    return {"answer": answer, "model": model, "saved": True}


def do_render(scene_name):
    global JOB
    filename = Path(scene_name).name
    scene = PROJECTS / filename
    if filename != scene_name or not filename.lower().endswith(".c4d") or not scene.is_file():
        raise ValueError("Cena inválida. Use uma cena .c4d em data/projects.")
    commandline = C4D / "Commandline.exe"
    if not commandline.is_file() or not PLUGIN.is_file():
        raise ValueError("Commandline.exe ou plugin Octane R2023 ausente.")
    if JOB["state"] == "running":
        raise ValueError("Um render já está em andamento.")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = RENDERS / f"octane_{stamp}"
    logpath = LOGS / f"render_{stamp}.txt"
    JOB = {"state": "running", "progress": None, "message": "Inicializando Commandline.exe", "file": None}

    def worker():
        global JOB
        args = [str(commandline), "g_modulePath=%{g_startupPath}/corelibs;%{g_startupPath}/plugins",
                "-render", str(scene), "-frame", "0", "0", "1", "-oimage", str(prefix), "-oformat", "PNG"]
        try:
            with logpath.open("w", encoding="utf-8", errors="replace") as log:
                proc = subprocess.Popen(args, cwd=C4D, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                        text=True, encoding="utf-8", errors="replace")
                octane_seen = False
                for line in proc.stdout:
                    log.write(line)
                    log.flush()
                    if re.search("octane|c4doctane", line, re.I):
                        octane_seen = True
                    match = re.search(r"(?<!\d)(\d{1,3})\s*%", line)
                    if match:
                        JOB["progress"] = min(99, int(match.group(1)))
                code = proc.wait()
            pngs = sorted(RENDERS.glob(prefix.name + "*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
            def is_png(path):
                with path.open("rb") as image:
                    return image.read(8) == b"\x89PNG\r\n\x1a\n"
            valid = next((p for p in pngs if is_png(p)), None)
            if code == 0 and valid and octane_seen:
                JOB = {"state": "confirmed", "progress": 100, "message": "PNG válido; Octane no log.", "file": valid.name}
            else:
                JOB = {"state": "unconfirmed", "progress": None,
                       "message": f"Saída {code}; PNG={bool(valid)}; Octane no log={octane_seen}. Veja {logpath.name}.",
                       "file": valid.name if valid else None}
        except Exception as exc:
            JOB = {"state": "error", "progress": None, "message": f"{type(exc).__name__}: {exc}", "file": None}

    threading.Thread(target=worker, daemon=True).start()
    return dict(JOB)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        # Nunca gravar token ou mensagens do agente no stdout.
        pass

    def send(self, code, value, content_type="application/json"):
        raw = json.dumps(value, ensure_ascii=False).encode() if content_type == "application/json" else value
        self.send_response(code)
        self.send_header("Content-Type", content_type + ("; charset=utf-8" if content_type.startswith("text/") else ""))
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(raw)

    def authorized(self):
        return secrets.compare_digest(self.headers.get("Authorization", ""), f"Bearer {TOKEN}")

    def do_GET(self):
        path = urllib.parse.urlsplit(self.path).path
        if path == "/":
            html = (ROOT / "index.html").read_text(encoding="utf-8").replace("__LOCAL_TOKEN__", TOKEN)
            return self.send(200, html.encode(), "text/html")
        if not self.authorized():
            return self.send(401, {"error": "Sessão inválida"})
        try:
            if path == "/api/status":
                return self.send(200, status())
            if path == "/api/models":
                return self.send(200, {"models": models()})
            if path == "/api/history":
                with LOCK:
                    rows = DB.execute("SELECT ts,role,model,text FROM chat ORDER BY id DESC LIMIT 100").fetchall()
                return self.send(200, {"messages": [dict(zip(("ts", "role", "model", "text"), row)) for row in reversed(rows)]})
            if path == "/api/notes":
                with LOCK:
                    rows = DB.execute("SELECT id,ts,text FROM notes ORDER BY id DESC LIMIT 100").fetchall()
                return self.send(200, {"notes": [dict(zip(("id", "ts", "text"), row)) for row in rows]})
            if path.startswith("/api/render/file/"):
                name = path.rsplit("/", 1)[-1]
                file = RENDERS / name
                if name != file.name or not name.endswith(".png") or not file.is_file():
                    return self.send(404, {"error": "Arquivo ausente"})
                return self.send(200, file.read_bytes(), "image/png")
            self.send(404, {"error": "Rota ausente"})
        except Exception as exc:
            self.send(503, {"error": f"{type(exc).__name__}: {exc}"})

    def do_POST(self):
        origin = self.headers.get("Origin")
        if origin and origin != LOCAL:
            return self.send(403, {"error": "Origem não permitida"})
        if not self.authorized():
            return self.send(401, {"error": "Sessão inválida"})
        length = int(self.headers.get("Content-Length", "0"))
        if length > 65536:
            return self.send(413, {"error": "Requisição grande demais"})
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
            path = urllib.parse.urlsplit(self.path).path
            if path == "/api/chat":
                message = str(body.get("message", "")).strip()
                if not message or len(message) > 12000:
                    raise ValueError("Mensagem vazia ou muito longa.")
                return self.send(200, chat(message, str(body.get("model", ""))))
            if path == "/api/notes":
                note = str(body.get("text", "")).strip()
                if not note or len(note) > 12000:
                    raise ValueError("Nota vazia ou muito longa.")
                with LOCK:
                    DB.execute("INSERT INTO notes(ts,text) VALUES (?,?)", (now(), note))
                    DB.commit()
                return self.send(200, {"saved": True})
            if path == "/api/render":
                return self.send(202, do_render(str(body.get("scene", ""))))
            return self.send(404, {"error": "Rota ausente"})
        except (ValueError, json.JSONDecodeError) as exc:
            self.send(400, {"error": str(exc)})
        except Exception as exc:
            self.send(503, {"error": f"{type(exc).__name__}: {exc}"})


def main():
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"AURION vNext local: {LOCAL}", flush=True)
    if os.environ.get("AURION_NO_BROWSER") != "1":
        webbrowser.open(LOCAL)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        DB.close()


if __name__ == "__main__":
    main()
