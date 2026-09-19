"""Read-only ComfyUI API probe. Never starts services or edits model configuration."""
from __future__ import annotations

import httpx


async def probe_comfyui(url: str = "http://127.0.0.1:8188") -> dict:
    """Report API evidence separately from unverified installation/process state.

    `found` and `running` are None unless a successful API response proves both.
    An unreachable API cannot prove that ComfyUI is absent or its process stopped.
    """
    result = {"found": None, "running": None, "api_online": False, "url": url}
    try:
        async with httpx.AsyncClient(timeout=2.0, trust_env=False) as client:
            response = await client.get(f"{url.rstrip('/')}/system_stats")
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict) or "system" not in payload:
                return result
    except (httpx.HTTPError, ValueError, TypeError):
        return result
    result.update(found=True, running=True, api_online=True)
    return result
