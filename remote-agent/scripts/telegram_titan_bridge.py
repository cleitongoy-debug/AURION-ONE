"""Telegram long-poll bridge to the existing AURION TITAN chat endpoint.

Runs on the user's PC. It does not expose a local port or execute shell commands.
Only TELEGRAM_ALLOWED_CHAT_ID is allowed to send messages to TITAN.
All credentials are read from environment variables and never printed.
"""
from __future__ import annotations

import json
import os
import signal
import sys
import time
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[1]
OFFSET_FILE = ROOT / "data" / "telegram_titan_offset.json"
STOP = False


def stop(_signum: int, _frame: object) -> None:
    global STOP
    STOP = True


def load_env_file() -> None:
    env_path = ROOT / ".env"
    try:
        lines = env_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    for line in lines:
        item = line.strip()
        if not item or item.startswith("#") or "=" not in item:
            continue
        key, value = item.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


def required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Variável obrigatória ausente: {name}")
    return value


def load_offset() -> int:
    try:
        data = json.loads(OFFSET_FILE.read_text(encoding="utf-8"))
        return max(0, int(data.get("offset", 0)))
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return 0


def save_offset(offset: int) -> None:
    OFFSET_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp = OFFSET_FILE.with_suffix(".tmp")
    temp.write_text(json.dumps({"offset": offset}) + "\n", encoding="utf-8")
    temp.replace(OFFSET_FILE)


def telegram_call(client: httpx.Client, token: str, method: str, payload: dict[str, Any]) -> dict[str, Any]:
    # Token lives only in the request URL; never log this URL or exception text.
    url = f"https://api.telegram.org/bot{token}/{method}"
    response = client.post(url, json=payload)
    response.raise_for_status()
    data = response.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram API recusou {method}")
    return data


def send_text(client: httpx.Client, token: str, chat_id: str, text: str) -> None:
    safe_text = text.strip() or "O TITAN não devolveu conteúdo."
    for start in range(0, len(safe_text), 3900):
        telegram_call(
            client,
            token,
            "sendMessage",
            {"chat_id": chat_id, "text": safe_text[start : start + 3900]},
        )


def main() -> int:
    load_env_file()
    try:
        token = required_env("TELEGRAM_BOT_TOKEN")
        allowed_chat_id = required_env("TELEGRAM_ALLOWED_CHAT_ID")
        titan_url = required_env("AURION_TITAN_CHAT_URL")
        api_key = required_env("AURION_API_KEY")
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    mode = os.environ.get("TITAN_CHAT_MODE", "PENSATIVO").strip().upper()
    if mode not in {"CURTO", "PENSATIVO", "PROGRAMADOR"}:
        mode = "PENSATIVO"

    signal.signal(signal.SIGINT, stop)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, stop)

    offset = load_offset()
    timeout = httpx.Timeout(100.0, connect=10.0)
    headers = {"X-API-Key": api_key, "Content-Type": "application/json"}

    print("[TITAN TELEGRAM] ponte iniciada; credenciais ocultas.", flush=True)
    with httpx.Client(timeout=timeout) as client:
        while not STOP:
            try:
                updates = telegram_call(
                    client,
                    token,
                    "getUpdates",
                    {"offset": offset, "timeout": 30, "allowed_updates": ["message"]},
                ).get("result", [])

                for update in updates:
                    update_id = int(update.get("update_id", 0))
                    offset = max(offset, update_id + 1)
                    message = update.get("message") or {}
                    chat = message.get("chat") or {}
                    chat_id = str(chat.get("id", ""))
                    text = str(message.get("text", "")).strip()

                    # Ignore all chats except the explicitly authorized owner chat.
                    if chat_id != allowed_chat_id or not text:
                        save_offset(offset)
                        continue

                    if text in {"/start", "/help"}:
                        send_text(
                            client,
                            token,
                            chat_id,
                            "Canal TITAN conectado. Envie sua mensagem normalmente. "
                            "As respostas vêm do endpoint TITAN configurado; falhas serão informadas.",
                        )
                        save_offset(offset)
                        continue

                    try:
                        response = client.post(
                            titan_url,
                            headers=headers,
                            json={
                                "message": text[:6000],
                                "mode": mode,
                                "conversation_id": f"telegram-{chat_id}",
                            },
                        )
                        data = response.json() if response.content else {}
                        if not response.is_success:
                            detail = (data.get("error") or {}).get("message") or f"HTTP {response.status_code}"
                            send_text(client, token, chat_id, f"TITAN não respondeu: {detail}")
                        else:
                            reply = str(data.get("reply") or "").strip()
                            if not reply:
                                send_text(client, token, chat_id, "TITAN retornou resposta vazia. A falha foi reportada.")
                            else:
                                send_text(client, token, chat_id, reply)
                    except (httpx.HTTPError, ValueError, RuntimeError):
                        send_text(
                            client,
                            token,
                            chat_id,
                            "Não consegui alcançar ou interpretar a resposta do TITAN. "
                            "A ponte continua ativa e tentará receber novas mensagens.",
                        )
                    finally:
                        save_offset(offset)

            except (httpx.HTTPError, ValueError, RuntimeError):
                # No exception text: it could contain the bot token URL.
                print("[TITAN TELEGRAM] falha de conexão/API; nova tentativa em 5s.", flush=True)
                time.sleep(5)

    print("[TITAN TELEGRAM] ponte encerrada.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
