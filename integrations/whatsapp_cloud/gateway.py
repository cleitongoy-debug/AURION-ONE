"""AURION WhatsApp Cloud API webhook gateway. No device control; opt-in replies."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import sqlite3
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen

MAX_BODY = 128 * 1024
PHONE_RE = re.compile(r"^[0-9]{8,16}$")


class Settings:
    def __init__(self, env=None):
        env = os.environ if env is None else env
        self.verify_token = env.get("AURION_WA_VERIFY_TOKEN", "")
        self.app_secret = env.get("AURION_WA_APP_SECRET", "")
        self.access_token = env.get("AURION_WA_ACCESS_TOKEN", "")
        self.phone_number_id = env.get("AURION_WA_PHONE_NUMBER_ID", "")
        self.graph_api_version = env.get("AURION_WA_GRAPH_VERSION", "")
        self.reply_enabled = env.get("AURION_WA_ENABLE_REPLIES", "false").lower() == "true"
        self.allowlist = {p.strip() for p in env.get("AURION_WA_ALLOWED_CONTACTS", "").split(",") if PHONE_RE.fullmatch(p.strip())}
        self.db_path = env.get("AURION_WA_DB", "aurion_whatsapp_events.sqlite3")
        if not self.verify_token or not self.app_secret:
            raise ValueError("Configure VERIFY_TOKEN e APP_SECRET via variaveis de ambiente")
        if self.reply_enabled and not all([self.access_token, self.phone_number_id, self.graph_api_version, self.allowlist]):
            raise ValueError("Respostas exigem token, numero, versao Graph e contatos autorizados")
        if self.graph_api_version and not re.fullmatch(r"v[0-9]+\.[0-9]+", self.graph_api_version):
            raise ValueError("Versao Graph invalida")


class Ledger:
    def __init__(self, path):
        self.lock = threading.Lock()
        self.conn = sqlite3.connect(str(path), check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("CREATE TABLE IF NOT EXISTS inbound (message_id TEXT PRIMARY KEY, received_at TEXT DEFAULT CURRENT_TIMESTAMP)")
        self.conn.commit()

    def mark_once(self, message_id):
        with self.lock:
            cursor = self.conn.execute("INSERT OR IGNORE INTO inbound(message_id) VALUES(?)", (message_id,))
            self.conn.commit()
            return cursor.rowcount == 1

    def close(self):
        with self.lock:
            self.conn.close()


def signature_valid(raw, header, app_secret):
    if not header or not header.startswith("sha256="):
        return False
    candidate = header.split("=", 1)[1]
    if len(candidate) != 64 or not re.fullmatch("[0-9a-fA-F]{64}", candidate):
        return False
    digest = hmac.new(app_secret.encode("utf-8"), raw, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, candidate.lower())


def eligible_replies(payload, settings, ledger):
    """Safely acknowledge allowlisted inbound text. Never execute remote commands."""
    output = []
    if not isinstance(payload, dict) or payload.get("object") != "whatsapp_business_account":
        return output
    for entry in payload.get("entry", []):
        if not isinstance(entry, dict):
            continue
        for change in entry.get("changes", []):
            if not isinstance(change, dict) or change.get("field") != "messages":
                continue
            value = change.get("value", {})
            if not isinstance(value, dict):
                continue
            for item in value.get("messages", []):
                if not isinstance(item, dict):
                    continue
                msg_id, number = item.get("id"), item.get("from")
                if not isinstance(msg_id, str) or not msg_id or len(msg_id) > 256 or not isinstance(number, str):
                    continue
                if not ledger.mark_once(msg_id):
                    continue
                if not settings.reply_enabled or number not in settings.allowlist or item.get("type") != "text":
                    continue
                text = (item.get("text") or {}).get("body", "")
                if not isinstance(text, str):
                    continue
                command = text.strip().casefold()
                if command == "status":
                    output.append((number, "AURION: canal WhatsApp ativo. Estado dos dispositivos ainda nao verificado."))
                elif command in ("ajuda", "menu"):
                    output.append((number, "AURION: comandos disponiveis: status, ajuda. Comandos do PC permanecem desativados."))
    return output


def send_whatsapp_text(settings, number, body):
    url = f"https://graph.facebook.com/{settings.graph_api_version}/{settings.phone_number_id}/messages"
    payload = json.dumps({"messaging_product": "whatsapp", "to": number, "type": "text", "text": {"body": body}}).encode()
    req = Request(url, data=payload, method="POST", headers={"Authorization": f"Bearer {settings.access_token}", "Content-Type": "application/json"})
    with urlopen(req, timeout=5) as response:
        if response.status not in (200, 201):
            raise RuntimeError("Meta API did not accept the message")


def make_handler(settings, ledger, sender=send_whatsapp_text):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            # Do not log phone numbers, URL tokens or payloads.
            return

        def reply(self, status, data, mimetype="text/plain; charset=utf-8"):
            self.send_response(status)
            self.send_header("Content-Type", mimetype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            from urllib.parse import parse_qs, urlsplit
            url = urlsplit(self.path)
            if url.path == "/health":
                self.reply(200, b'{"service":"aurion-whatsapp-gateway","status":"ready-for-meta-configuration"}', "application/json")
                return
            if url.path != "/webhook":
                self.reply(404, b"not found")
                return
            q = parse_qs(url.query)
            tokens_ok = (q.get("hub.mode") == ["subscribe"] and q.get("hub.verify_token") == [settings.verify_token])
            challenge = q.get("hub.challenge", [""])[0]
            if not tokens_ok or not challenge.isdecimal() or len(challenge) > 100:
                self.reply(403, b"forbidden")
                return
            self.reply(200, challenge.encode())

        def do_POST(self):
            if self.path != "/webhook":
                self.reply(404, b"not found")
                return
            try:
                length = int(self.headers.get("Content-Length", "-1"))
            except ValueError:
                length = -1
            if length < 0 or length > MAX_BODY:
                self.reply(413, b"invalid body length")
                return
            raw = self.rfile.read(length)
            if not signature_valid(raw, self.headers.get("X-Hub-Signature-256", ""), settings.app_secret):
                self.reply(403, b"forbidden")
                return
            try:
                payload = json.loads(raw)
            except (ValueError, UnicodeDecodeError):
                self.reply(400, b"invalid json")
                return
            replies = eligible_replies(payload, settings, ledger)
            # This prototype performs bounded synchronous delivery. Production needs durable outbox/retry.
            for number, body in replies:
                try:
                    sender(settings, number, body)
                except Exception:
                    self.reply(503, b"reply delivery failed")
                    return
            self.reply(200, b"ok")
    return Handler


def main():
    settings = Settings()
    host = os.environ.get("AURION_WA_BIND", "127.0.0.1")
    port = int(os.environ.get("AURION_WA_PORT", "8780"))
    ledger = Ledger(Path(settings.db_path))
    server = ThreadingHTTPServer((host, port), make_handler(settings, ledger))
    try:
        print(f"AURION WhatsApp gateway running on {host}:{port}; replies_enabled={settings.reply_enabled}", flush=True)
        server.serve_forever(poll_interval=0.25)
    finally:
        server.server_close()
        ledger.close()


if __name__ == "__main__":
    main()
