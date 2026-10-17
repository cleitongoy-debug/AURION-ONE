"""Read-only Lovart/Instagram reference catalog for the local AURION panel.

The catalog is OFFLINE and never opens sessions, calls provider APIs, reads
credentials, rotates keys, or consumes Lovart credits. The JSON manifest is
private and excluded from Git; a public template is shipped separately.
"""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

DEFAULT_MANIFEST = Path(__file__).resolve().parents[1] / "data" / "lovart_manifest.json"
MAX_BYTES = 512_000
MAX_ASSETS = 100


def safe_link(value: object) -> str | None:
    """Allow only public-looking https links without credentials or parameters."""
    if not isinstance(value, str) or len(value) > 2048:
        return None
    try:
        parsed = urlsplit(value.strip())
        host = (parsed.hostname or "").lower().rstrip(".")
        if (
            parsed.scheme.lower() != "https"
            or not host
            or parsed.username is not None
            or parsed.password is not None
            or host in {"localhost", "127.0.0.1", "::1"}
            or host.endswith((".local", ".internal"))
            or host.startswith(("10.", "192.168.", "172.16.", "169.254."))
        ):
            return None
        return urlunsplit(("https", parsed.netloc, parsed.path, "", ""))
    except ValueError:
        return None


def _short(value: object, limit: int = 120) -> str:
    return value.strip()[:limit] if isinstance(value, str) else ""


def load_catalog(path: Path = DEFAULT_MANIFEST) -> dict:
    """Load a bounded local manifest; never return unrecognized JSON keys."""
    output = {
        "source": "local_manifest_only",
        "status": "manifest_missing",
        "lovart_api_connected": False,
        "instagram_api_connected": False,
        "credits_remaining": None,
        "last_live_ack": None,
        "instagram_profile": "https://www.instagram.com/studio.digitalpen/",
        "assets": [],
        "asset_count": 0,
        "note": "Links históricos não comprovam sessão conectada ou geração nova.",
    }
    try:
        if not path.is_file():
            return output
        if path.stat().st_size > MAX_BYTES:
            output["status"] = "manifest_invalid"
            return output
        raw = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(raw, dict) or not isinstance(raw.get("assets", []), list):
            output["status"] = "manifest_invalid"
            return output
        filtered = []
        for item in raw.get("assets", [])[:MAX_ASSETS]:
            if not isinstance(item, dict):
                continue
            url = safe_link(item.get("url"))
            title = _short(item.get("title"))
            if not url or not title:
                continue
            filtered.append({
                "title": title,
                "url": url,
                "kind": _short(item.get("kind"), 30) or "referencia",
                "source": _short(item.get("source"), 60) or "manifesto_local",
                "verification": "referencia_nao_validada",
            })
        profile = safe_link(raw.get("instagram_profile"))
        if profile and urlsplit(profile).hostname in {"instagram.com", "www.instagram.com"}:
            output["instagram_profile"] = profile
        output["assets"] = filtered
        output["asset_count"] = len(filtered)
        output["status"] = "catalog_loaded"
    except (OSError, ValueError, UnicodeError):
        output["status"] = "manifest_invalid"
    return output
