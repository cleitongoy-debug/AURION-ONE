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
CACHE_FILE = ROOT / "data" / "titan_memory_cache.json"
CACHE_REFRESH_SECONDS = 300
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


def load_cache() -> list[dict[str, Any]]:
    try:
        payload = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        items = payload.get("items", [])
        return items if isinstance(items, list) else []
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return []


def save_cache(items: list[dict[str, Any]], generated_at: str = "") -> None:
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp = CACHE_FILE.with_suffix(".tmp")
    temp.write_text(
        json.dumps({"generated_at": generated_at, "items": items}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temp.replace(CACHE_FILE)


def refresh_cache(client: httpx.Client, cache_url: str, api_key: str) -> bool:
    if not cache_url or not api_key:
        return False
    try:
        response = client.get(cache_url, headers={"X-API-Key": api_key}, timeout=5.0)
        response.raise_for_status()
        payload = response.json()
        items = payload.get("items", [])
        if not isinstance(items, list):
            return False
        save_cache(items, str(payload.get("generated_at", "")))
        return True
    except (httpx.HTTPError, ValueError, TypeError):
        return False


def format_memory_fallback(message: str, items: list[dict[str, Any]]) -> str:
    selected = items[:8]
    if not selected:
        return (
            "TITAN em contingência: painel/API e memória local ainda não estão disponíveis. "
            "A ponte Telegram segue online e tentará novamente."
        )
    lines = [
        "TITAN em contingência local. A base profunda/servidor está offline; esta resposta usa "
        "somente o cache consolidado neste computador. Não é uma nova pesquisa.",
        "",
        "Registros disponíveis:",
    ]
    for item in selected:
        title = str(item.get("title") or item.get("key") or "Registro")[:120]
        body = str(item.get("body") or "")[:500]
        source = str(item.get("source") or "")
        lines.append(f"- {title}: {body}" + (f" [origem: {source}]" if source else ""))
    lines.extend(["", f"Mensagem recebida: {message[:500]}"])
    return "\n".join(lines)


def ask_local_ollama(
    client: httpx.Client, message: str, items: list[dict[str, Any]], ollama_url: str, model: str
) -> str:
    if not ollama_url:
        return ""
    context = json.dumps(items[:30], ensure_ascii=False)[:18000]
    try:
        response = client.post(
            ollama_url,
            timeout=25.0,
            json={
                "model": model,
                "stream": False,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Você é o TITAN em contingência local. A base profunda e o painel podem estar offline. "
                            "Use apenas o cache fornecido; não invente fatos nem alegue pesquisa nova. "
                            "Avise que a resposta veio do cache local e diferencie fato de hipótese. Cache: " + context
                        ),
                    },
                    {"role": "user", "content": message[:6000]},
                ],
            },
        )
        response.raise_for_status()
        data = response.json()
        return str((data.get("message") or {}).get("content") or "").strip()
    except (httpx.HTTPError, ValueError, TypeError):
        return ""


def main() -> int:
    load_env_file()
    try:
        token = required_env("TELEGRAM_BOT_TOKEN")
        allowed_chat_id = required_env("TELEGRAM_ALLOWED_CHAT_ID")
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    titan_url = os.environ.get("AURION_TITAN_CHAT_URL", "").strip()
    cache_url = os.environ.get("AURION_TITAN_CACHE_URL", "").strip()
    api_key = os.environ.get("AURION_API_KEY", "").strip()
    ollama_url = os.environ.get("TITAN_OLLAMA_URL", "http://127.0.0.1:11434/api/chat").strip()
    ollama_model = os.environ.get("TITAN_OLLAMA_MODEL", "llama3.1:8b").strip()

    mode = os.environ.get("TITAN_CHAT_MODE", "PENSATIVO").strip().upper()
    if mode not in {"CURTO", "PENSATIVO", "PROGRAMADOR"}:
        mode = "PENSATIVO"

    signal.signal(signal.SIGINT, stop)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, stop)

    offset = load_offset()
    timeout = httpx.Timeout(35.0, connect=5.0)
    headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
    cached_items = load_cache()
    last_cache_refresh = 0.0

    print("[TITAN TELEGRAM] ponte independente iniciada; credenciais ocultas.", flush=True)
    with httpx.Client(timeout=timeout) as client:
        while not STOP:
            try:
                now = time.monotonic()
                if cache_url and api_key and now - last_cache_refresh >= CACHE_REFRESH_SECONDS:
                    if refresh_cache(client, cache_url, api_key):
                        cached_items = load_cache()
                        print("[TITAN TELEGRAM] cache local atualizado.", flush=True)
                    last_cache_refresh = now
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
                            "Se o painel cair, tentarei usar o cache local e o Ollama deste PC.",
                        )
                        save_offset(offset)
                        continue

                    reply = ""
                    if titan_url and api_key:
                        try:
                            response = client.post(
                                titan_url,
                                headers=headers,
                                json={
                                    "message": text[:6000],
                                    "mode": mode,
                                    "conversation_id": f"telegram-{chat_id}",
                                },
                                timeout=8.0,
                            )
                            data = response.json() if response.content else {}
                            if response.is_success:
                                reply = str(data.get("reply") or "").strip()
                        except (httpx.HTTPError, ValueError):
                            pass

                    # Painel/API fora do ar? O bot continua via cache local e Ollama.
                    if not reply:
                        reply = ask_local_ollama(client, text, cached_items, ollama_url, ollama_model)
                    if not reply:
                        reply = format_memory_fallback(text, cached_items)
                    send_text(client, token, chat_id, reply)
                    save_offset(offset)

            except (httpx.HTTPError, ValueError, RuntimeError):
                # No exception text: it could contain the bot token URL.
                print("[TITAN TELEGRAM] falha de conexão/API; nova tentativa em 5s.", flush=True)
                time.sleep(5)

    print("[TITAN TELEGRAM] ponte encerrada.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
