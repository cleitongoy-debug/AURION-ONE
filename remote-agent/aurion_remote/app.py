from __future__ import annotations

import asyncio
import secrets
import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from xml.etree import ElementTree

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.responses import HTMLResponse

from .config import Settings, get_settings
from .models import DeviceState, PromptRequest, PromptResponse
from .manual_vault import router as manual_vault_router
from .c4d_diagnostics import router as c4d_diagnostics_router\nfrom .blender_studio import router as blender_studio_router

app = FastAPI(title="AURION ONE Home Node", version="0.1.1")
device_states: dict[str, dict] = {}
scan_lock = asyncio.Lock()


def load_context(path: Path) -> str:
    if not path.is_file():
        return "Você é o nó local AURION ONE. Seja preciso, seguro e auditável."
    if path.suffix.lower() == ".docx":
        try:
            with zipfile.ZipFile(path) as archive:
                root = ElementTree.fromstring(archive.read("word/document.xml"))
            text = "\n".join(node.text for node in root.iter() if node.tag.endswith("}t") and node.text)
            return text[:50000]
        except (OSError, KeyError, zipfile.BadZipFile, ElementTree.ParseError):
            return "Você é o nó local AURION ONE. Seja preciso, seguro e auditável."
    return path.read_text(encoding="utf-8", errors="replace")[:50000]


def require_token(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    expected = f"Bearer {settings.api_token}"
    if not authorization or not secrets.compare_digest(authorization, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")


app.include_router(manual_vault_router, dependencies=[Depends(require_token)])
app.include_router(c4d_diagnostics_router, dependencies=[Depends(require_token)])\napp.include_router(blender_studio_router, dependencies=[Depends(require_token)])


@app.get("/health")
async def health() -> dict:
    return {"service": "aurion-home-node", "status": "online", "time": datetime.now(UTC).isoformat()}


@app.get("/api/inventory", dependencies=[Depends(require_token)])
async def inventory() -> dict:
    path = Path(__file__).resolve().parents[1] / "data" / "inventory.json"
    if not path.is_file():
        return {"status": "pending"}
    return json.loads(path.read_text(encoding="utf-8"))


@app.post("/api/scan", dependencies=[Depends(require_token)])
async def run_inventory_scan() -> dict:
    """Run only the fixed read-only inventory script, once at a time.

    This endpoint accepts no command, paths, or script arguments. It never
    starts/stops services, scans private file contents, or publishes inventory.
    """
    if scan_lock.locked():
        raise HTTPException(status_code=409, detail="Um scan já está em andamento")
    async with scan_lock:
        script = Path(__file__).resolve().parents[1] / "scripts" / "scan_system.py"
        if not script.is_file():
            raise HTTPException(status_code=503, detail="Scanner não instalado")
        import sys
        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, str(script),
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
        except OSError as exc:
            raise HTTPException(status_code=503, detail="Scanner indisponível") from exc
        try:
            await asyncio.wait_for(proc.wait(), timeout=35)
        except asyncio.TimeoutError as exc:
            proc.kill()
            await proc.wait()
            raise HTTPException(status_code=504, detail="Scan excedeu 35 segundos") from exc
        if proc.returncode != 0:
            raise HTTPException(status_code=503, detail="Falha no scan; consulte o log local do PC")
        path = Path(__file__).resolve().parents[1] / "data" / "inventory.json"
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise HTTPException(status_code=503, detail="Inventário não pôde ser lido") from exc


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
async def prompt(request: PromptRequest, http_request: Request, settings: Settings = Depends(get_settings)) -> PromptResponse:
    if settings.motion_lock and request.moving:
        return PromptResponse(status="blocked", answer="Comando bloqueado enquanto o dispositivo está em movimento.")
    # O próprio PC pode usar o agente imediatamente. Dispositivos externos
    # continuam bloqueados até o operador habilitar a rede privada.
    is_local = bool(http_request.client and http_request.client.host in {"127.0.0.1", "::1"})
    if is_local and not settings.allow_local_prompts:
        return PromptResponse(status="disabled", answer="Prompts locais estão desativados.")
    if not is_local and not settings.allow_remote_prompts:
        return PromptResponse(status="disabled", answer="Prompts remotos ainda não foram liberados pelo operador.")
    if not settings.ollama_model:
        return PromptResponse(status="disabled", answer="Defina AURION_OLLAMA_MODEL antes de liberar prompts.")

    context = load_context(settings.context_file)
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
<style>body{font:16px system-ui;background:#07182d;color:#fff;max-width:900px;margin:30px auto;padding:20px}
.card{background:#102b4b;border:1px solid #1d6fd8;border-radius:16px;padding:22px;margin:14px 0}code{color:#e3b83f}
pre{white-space:pre-wrap;color:#bde5ff}input,button,textarea{box-sizing:border-box;width:100%;padding:12px;margin:6px 0;border-radius:8px;border:1px solid #2782dc}
button{background:#1d6fd8;color:#fff;font-weight:700}</style></head>
<body><div id='login' class='card'><h1>Login AURION ONE</h1><p>No primeiro acesso, cole com Ctrl+V a chave copiada pelo inicializador.</p><input id='token' type='password' placeholder='Chave local'><button onclick='loginPortal()'>Entrar</button><pre id='loginStatus'></pre></div>
<main id='portal' style='display:none'><div class='card'><h1>AURION ONE</h1><p>Nó doméstico online, autenticado e com inventário carregado.</p></div>
<div class='card'><button onclick='runScan()'>Iniciar scan do PC</button><button onclick='loadInventory()'>Ver inventário salvo</button><pre id='scanStatus' aria-live='polite'></pre></div>
<div class='card'><h2>Inventário automático</h2><pre id='inventory'>Informe o token para carregar.</pre></div>
<div class='card'><h2>Comando local</h2>
<textarea id='prompt' rows='4' placeholder='Escreva uma tarefa para o agente'></textarea><button onclick='sendPrompt()'>Executar</button>
<pre id='answer'></pre></div><script>
function savedToken(){return localStorage.getItem('aurion_token')||token.value}
async function loginPortal(){const r=await fetch('/api/inventory',{headers:{'Authorization':'Bearer '+token.value.trim()}});if(!r.ok){localStorage.removeItem('aurion_token');loginStatus.textContent='Chave inválida. Execute o inicializador novamente e cole a nova chave.';return}localStorage.setItem('aurion_token',token.value.trim());login.style.display='none';portal.style.display='block';inventory.textContent=JSON.stringify(await r.json(),null,2)}
async function runScan(){
scanStatus.textContent='Escaneando PC...';
try{const r=await fetch('/api/scan',{method:'POST',headers:{'Authorization':'Bearer '+savedToken()}});
const data=await r.json();if(!r.ok)throw Error(data.detail||'Erro HTTP '+r.status);
inventory.textContent=JSON.stringify(data,null,2);scanStatus.textContent='Scan concluído: '+(data.scanned_at||'sem horário');
}catch(e){scanStatus.textContent='Falha no scan: '+e.message;}
}
async function loadInventory(){const r=await fetch('/api/inventory',{headers:{'Authorization':'Bearer '+savedToken()}});inventory.textContent=JSON.stringify(await r.json(),null,2)}
async function sendPrompt(){answer.textContent='Processando...';const r=await fetch('/api/prompt',{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+savedToken()},body:JSON.stringify({text:prompt.value,device_id:'portal-pc',moving:false})});answer.textContent=JSON.stringify(await r.json(),null,2)}
const fragment=new URLSearchParams(location.hash.slice(1));const incoming=fragment.get('token');if(incoming){localStorage.setItem('aurion_token',incoming);history.replaceState(null,'',location.pathname)}const prior=localStorage.getItem('aurion_token');if(prior){token.value=prior;loginPortal()}
</script></main></body></html>"""
