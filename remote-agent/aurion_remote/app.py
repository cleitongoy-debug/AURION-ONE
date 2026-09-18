from __future__ import annotations

import secrets
from datetime import UTC, datetime

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.responses import HTMLResponse

from .config import Settings, get_settings
from .models import DeviceState, PromptRequest, PromptResponse

app = FastAPI(title="AURION ONE Home Node", version="0.1.0")
device_states: dict[str, dict] = {}


def require_token(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    expected = f"Bearer {settings.api_token}"
    if not authorization or not secrets.compare_digest(authorization, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")


@app.get("/health")
async def health() -> dict:
    return {"service": "aurion-home-node", "status": "online", "time": datetime.now(UTC).isoformat()}


@app.get("/api/status", dependencies=[Depends(require_token)])
async def system_status(settings: Settings = Depends(get_settings)) -> dict:
    ollama = "offline"
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{settings.ollama_url.rstrip('/')}/api/tags")
            if response.is_success:
                ollama = "online"
    except httpx.HTTPError:
        pass
    return {
        "aurion": "online",
        "ollama": ollama,
        "remote_prompts": settings.allow_remote_prompts,
        "motion_lock": settings.motion_lock,
        "devices": list(device_states.values()),
    }


@app.post("/api/device", dependencies=[Depends(require_token)])
async def update_device(state: DeviceState) -> dict:
    payload = state.model_dump()
    payload["updated_at"] = datetime.now(UTC).isoformat()
    device_states[state.device_id] = payload
    return {"accepted": True, "device": payload}


@app.post("/api/prompt", response_model=PromptResponse, dependencies=[Depends(require_token)])
async def prompt(request: PromptRequest, settings: Settings = Depends(get_settings)) -> PromptResponse:
    if settings.motion_lock and request.moving:
        return PromptResponse(status="blocked", answer="Comando bloqueado enquanto o dispositivo está em movimento.")
    if not settings.allow_remote_prompts:
        return PromptResponse(status="disabled", answer="Prompts remotos ainda não foram liberados pelo operador.")
    if not settings.ollama_model:
        return PromptResponse(status="disabled", answer="Defina AURION_OLLAMA_MODEL antes de liberar prompts.")

    context = ""
    if settings.context_file.is_file():
        context = settings.context_file.read_text(encoding="utf-8")[:50000]
    payload = {
        "model": settings.ollama_model,
        "stream": False,
        "messages": [
            {"role": "system", "content": context or "Você é o nó local AURION ONE. Seja preciso e seguro."},
            {"role": "user", "content": request.text},
        ],
    }
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(f"{settings.ollama_url.rstrip('/')}/api/chat", json=payload)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Ollama indisponível: {type(exc).__name__}") from exc
    answer = response.json().get("message", {}).get("content", "")
    return PromptResponse(status="completed", answer=answer)


@app.get("/", response_class=HTMLResponse)
async def panel() -> str:
    return """<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'><title>AURION ONE</title>
<style>body{font:16px system-ui;background:#07182d;color:#fff;max-width:760px;margin:40px auto;padding:20px}
.card{background:#102b4b;border:1px solid #1d6fd8;border-radius:16px;padding:24px}code{color:#e3b83f}</style></head>
<body><div class='card'><h1>AURION ONE</h1><p>Nó doméstico online.</p>
<p>Use <code>/health</code> para verificação pública e <code>/api/status</code> com token para o estado privado.</p>
<p>O painel móvel completo será conectado na próxima fase.</p></div></body></html>"""

