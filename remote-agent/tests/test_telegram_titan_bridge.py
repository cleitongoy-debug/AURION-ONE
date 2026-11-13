from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from telegram_titan_bridge import format_memory_fallback


def test_fallback_uses_cached_records_and_discloses_offline_state() -> None:
    reply = format_memory_fallback(
        "Qual foi a última descoberta?",
        [
            {
                "type": "knowledge",
                "key": "identity-titan",
                "title": "Quem é o TITAN",
                "body": "Agente com memória persistente.",
                "source": "titan_knowledge",
            }
        ],
    )
    assert "contingência local" in reply
    assert "não é uma nova pesquisa" in reply.lower()
    assert "Quem é o TITAN" in reply
    assert "titan_knowledge" in reply


def test_fallback_without_cache_is_honest() -> None:
    reply = format_memory_fallback("Olá", [])
    assert "memória local ainda não estão disponíveis" in reply
    assert "tentará novamente" in reply


def test_only_captain_chat_id_is_allowed() -> None:
    from telegram_titan_bridge import is_allowed_chat

    assert is_allowed_chat(2028747281)
    assert not is_allowed_chat(2028747282)
    assert not is_allowed_chat("")
