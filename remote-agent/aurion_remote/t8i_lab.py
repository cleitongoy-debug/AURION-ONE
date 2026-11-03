from __future__ import annotations

import asyncio
import json
import math
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field

from .app import require_token

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data" / "t8i_lab"
CONFIG_FILE = DATA_DIR / "config.json"
MANIFEST_FILE = DATA_DIR / "manifest.jsonl"

DEPENDENCIES = ["rawpy", "numpy", "Pillow", "imageio", "tifffile"]
ALLOWED_EXT = {".cr3", ".jpg", ".jpeg", ".png", ".tif", ".tiff"}
SUBFOLDERS = {
    "source": "01_ORIGINAIS",
    "previews": "02_PREVIEWS",
    "exports": "03_EXPORTADOS",
    "conversations": "04_CONVERSAS",
    "presets": "05_PRESETS",
    "sidecars": "06_SIDECARS",
    "logs": "07_LOGS",
}


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _load_config() -> dict[str, Any]:
    if not CONFIG_FILE.is_file():
        return {"workspace": "", "paths": {}, "updated_at": None}
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"workspace": "", "paths": {}, "updated_at": None}


def _save_config(cfg: dict[str, Any]) -> None:
    cfg["updated_at"] = _now()
    _atomic_json(CONFIG_FILE, cfg)


def _append_manifest(event: str, payload: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    record = {"time": _now(), "event": event, **payload}
    with MANIFEST_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def _is_within(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except (ValueError, OSError):
        return False


def _configured_path(key: str) -> Path:
    cfg = _load_config()
    raw = (cfg.get("paths") or {}).get(key)
    if not raw:
        raise HTTPException(status_code=409, detail=f"Pasta '{key}' ainda não configurada")
    return Path(raw)


def _choose_directory(title: str) -> str:
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        chosen = filedialog.askdirectory(title=title, mustexist=True)
        return chosen or ""
    finally:
        root.destroy()


def _require_local(request: Request) -> None:
    if not request.client or request.client.host not in {"127.0.0.1", "::1"}:
        raise HTTPException(status_code=403, detail="Esta ação só pode ser iniciada no próprio PC")


def _dependency_status() -> dict[str, bool]:
    status: dict[str, bool] = {}
    checks = {
        "rawpy": "rawpy",
        "numpy": "numpy",
        "Pillow": "PIL",
        "imageio": "imageio",
        "tifffile": "tifffile",
    }
    for label, module in checks.items():
        try:
            __import__(module)
            status[label] = True
        except Exception:
            status[label] = False
    return status


def _safe_name(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9 _.-]+", "_", name).strip(" .")
    if not cleaned or cleaned in {".", ".."}:
        raise HTTPException(status_code=400, detail="Nome de pasta inválido")
    return cleaned[:96]


class FolderChoice(BaseModel):
    key: str = Field(pattern="^(workspace|source|previews|exports|conversations|presets|sidecars|logs)$")


class NewFolder(BaseModel):
    parent_key: str = Field(pattern="^(workspace|source|previews|exports|conversations|presets|sidecars|logs)$")
    name: str = Field(min_length=1, max_length=96)


class DevelopRequest(BaseModel):
    source: str
    output_name: str | None = None
    export_format: str = Field(default="tiff16", pattern="^(tiff16|jpeg95)$")
    exposure: float = Field(default=0.0, ge=-5.0, le=5.0)
    contrast: float = Field(default=0.0, ge=-100.0, le=100.0)
    saturation: float = Field(default=0.0, ge=-100.0, le=100.0)
    temperature: float = Field(default=0.0, ge=-100.0, le=100.0)
    tint: float = Field(default=0.0, ge=-100.0, le=100.0)
    shadows: float = Field(default=0.0, ge=-100.0, le=100.0)
    highlights: float = Field(default=0.0, ge=-100.0, le=100.0)


class ConversationRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    text: str = Field(default="", max_length=500_000)
    context: dict[str, Any] = Field(default_factory=dict)


@router.get("/api/t8i/config", dependencies=[Depends(require_token)])
async def t8i_config() -> dict[str, Any]:
    return {"config": _load_config(), "dependencies": _dependency_status(), "required": DEPENDENCIES}


@router.post("/api/t8i/install-dependencies", dependencies=[Depends(require_token)])
async def install_dependencies(request: Request) -> dict[str, Any]:
    _require_local(request)

    def run() -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", *DEPENDENCIES],
            text=True,
            capture_output=True,
            timeout=900,
            check=False,
        )

    try:
        proc = await asyncio.to_thread(run)
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(status_code=504, detail="Instalação excedeu 15 minutos") from exc
    _append_manifest("dependencies_install", {"returncode": proc.returncode})
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "status": _dependency_status(),
        "stdout_tail": proc.stdout[-6000:],
        "stderr_tail": proc.stderr[-6000:],
    }


@router.post("/api/t8i/pick-folder", dependencies=[Depends(require_token)])
async def pick_folder(choice: FolderChoice, request: Request) -> dict[str, Any]:
    _require_local(request)
    chosen = await asyncio.to_thread(_choose_directory, f"AURION ONE · T8i · {choice.key}")
    if not chosen:
        return {"cancelled": True}
    path = Path(chosen).resolve()
    cfg = _load_config()
    if choice.key == "workspace":
        paths = {key: str((path / folder).resolve()) for key, folder in SUBFOLDERS.items()}
        for value in paths.values():
            Path(value).mkdir(parents=True, exist_ok=True)
        cfg["workspace"] = str(path)
        cfg["paths"] = paths
    else:
        cfg.setdefault("paths", {})[choice.key] = str(path)
    _save_config(cfg)
    _append_manifest("folder_selected", {"key": choice.key, "path": str(path)})
    return {"cancelled": False, "config": cfg}


@router.post("/api/t8i/create-folder", dependencies=[Depends(require_token)])
async def create_folder(payload: NewFolder) -> dict[str, Any]:
    cfg = _load_config()
    if payload.parent_key == "workspace":
        raw_parent = cfg.get("workspace")
    else:
        raw_parent = (cfg.get("paths") or {}).get(payload.parent_key)
    if not raw_parent:
        raise HTTPException(status_code=409, detail="Configure primeiro a pasta de destino")
    parent = Path(raw_parent).resolve()
    target = (parent / _safe_name(payload.name)).resolve()
    if not _is_within(target, parent):
        raise HTTPException(status_code=400, detail="Destino inválido")
    target.mkdir(parents=True, exist_ok=True)
    _append_manifest("folder_created", {"parent_key": payload.parent_key, "path": str(target)})
    return {"ok": True, "path": str(target)}


@router.get("/api/t8i/files", dependencies=[Depends(require_token)])
async def list_files() -> dict[str, Any]:
    source = _configured_path("source")
    if not source.exists():
        return {"files": []}
    files = []
    for path in source.rglob("*"):
        if path.is_file() and path.suffix.lower() in ALLOWED_EXT:
            stat = path.stat()
            files.append({
                "name": path.name,
                "path": str(path.resolve()),
                "ext": path.suffix.lower(),
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime, UTC).isoformat(),
            })
    files.sort(key=lambda x: x["modified"], reverse=True)
    return {"files": files[:2000], "truncated": len(files) > 2000}


def _apply_adjustments(rgb: Any, req: DevelopRequest) -> Any:
    import numpy as np

    arr = rgb.astype(np.float32) / 65535.0
    arr *= 2.0 ** req.exposure

    temp = req.temperature / 100.0
    tint = req.tint / 100.0
    arr[..., 0] *= 1.0 + max(temp, 0) * 0.18
    arr[..., 2] *= 1.0 + max(-temp, 0) * 0.18
    arr[..., 2] *= 1.0 - max(temp, 0) * 0.10
    arr[..., 0] *= 1.0 - max(-temp, 0) * 0.10
    arr[..., 1] *= 1.0 - tint * 0.10
    arr[..., 0] *= 1.0 + tint * 0.05
    arr[..., 2] *= 1.0 + tint * 0.05

    contrast = 1.0 + req.contrast / 100.0
    arr = (arr - 0.5) * contrast + 0.5

    luma = arr[..., 0] * 0.2126 + arr[..., 1] * 0.7152 + arr[..., 2] * 0.0722
    sat = 1.0 + req.saturation / 100.0
    arr = luma[..., None] + (arr - luma[..., None]) * sat

    if req.shadows:
        amount = req.shadows / 100.0
        mask = np.clip((0.55 - luma) / 0.55, 0, 1)[..., None]
        arr += mask * amount * 0.22
    if req.highlights:
        amount = req.highlights / 100.0
        mask = np.clip((luma - 0.45) / 0.55, 0, 1)[..., None]
        arr += mask * amount * 0.22

    return np.clip(arr, 0, 1)


def _decode_16bit(source: Path) -> Any:
    import numpy as np

    if source.suffix.lower() == ".cr3":
        import rawpy
        with rawpy.imread(str(source)) as raw:
            return raw.postprocess(
                use_camera_wb=True,
                no_auto_bright=True,
                output_bps=16,
                gamma=(2.222, 4.5),
            )

    from PIL import Image
    with Image.open(source) as im:
        im = im.convert("RGB")
        return np.asarray(im, dtype=np.uint16) * 257


def _develop_sync(req: DevelopRequest, preview: bool = False) -> dict[str, Any]:
    import numpy as np
    import imageio.v3 as iio
    from PIL import Image

    source_root = _configured_path("source")
    source = Path(req.source).resolve()
    if not _is_within(source, source_root) or not source.is_file():
        raise HTTPException(status_code=400, detail="Arquivo fora da pasta de originais configurada")
    if source.suffix.lower() not in ALLOWED_EXT:
        raise HTTPException(status_code=415, detail="Formato não suportado nesta aba")

    rgb16 = _decode_16bit(source)
    adjusted = _apply_adjustments(rgb16, req)

    if preview:
        preview_root = _configured_path("previews")
        preview_root.mkdir(parents=True, exist_ok=True)
        out = preview_root / f"{source.stem}__preview.jpg"
        arr8 = (adjusted * 255.0 + 0.5).astype(np.uint8)
        image = Image.fromarray(arr8, "RGB")
        image.thumbnail((1800, 1800))
        image.save(out, quality=90, optimize=True)
        return {"output": str(out), "preview": True}

    export_root = _configured_path("exports")
    sidecar_root = _configured_path("sidecars")
    export_root.mkdir(parents=True, exist_ok=True)
    sidecar_root.mkdir(parents=True, exist_ok=True)

    stem = _safe_name(req.output_name or (source.stem + "__AURION"))
    if req.export_format == "tiff16":
        out = export_root / f"{stem}.tif"
        iio.imwrite(out, (adjusted * 65535.0 + 0.5).astype(np.uint16), plugin="tifffile")
    else:
        out = export_root / f"{stem}.jpg"
        arr8 = (adjusted * 255.0 + 0.5).astype(np.uint8)
        Image.fromarray(arr8, "RGB").save(out, quality=95, subsampling=0, optimize=True)

    sidecar = sidecar_root / f"{stem}.json"
    payload = {
        "source": str(source),
        "output": str(out),
        "created_at": _now(),
        "settings": req.model_dump(),
        "note": "CR3 é RAW fotográfico; esta etapa não aplica Canon Log/C-Log.",
    }
    _atomic_json(sidecar, payload)
    _append_manifest("developed", {"source": str(source), "output": str(out), "sidecar": str(sidecar)})
    return {"output": str(out), "sidecar": str(sidecar), "preview": False}


@router.post("/api/t8i/preview", dependencies=[Depends(require_token)])
async def preview(req: DevelopRequest) -> dict[str, Any]:
    missing = [name for name, ok in _dependency_status().items() if not ok]
    if missing:
        raise HTTPException(status_code=409, detail=f"Dependências ausentes: {', '.join(missing)}")
    return await asyncio.to_thread(_develop_sync, req, True)


@router.post("/api/t8i/develop", dependencies=[Depends(require_token)])
async def develop(req: DevelopRequest) -> dict[str, Any]:
    missing = [name for name, ok in _dependency_status().items() if not ok]
    if missing:
        raise HTTPException(status_code=409, detail=f"Dependências ausentes: {', '.join(missing)}")
    return await asyncio.to_thread(_develop_sync, req, False)


@router.get("/api/t8i/file", dependencies=[Depends(require_token)])
async def get_generated_file(path: str) -> FileResponse:
    cfg = _load_config()
    allowed = []
    for key in ("previews", "exports", "sidecars", "conversations"):
        raw = (cfg.get("paths") or {}).get(key)
        if raw:
            allowed.append(Path(raw))
    target = Path(path).resolve()
    if not target.is_file() or not any(_is_within(target, root) for root in allowed):
        raise HTTPException(status_code=404, detail="Arquivo não autorizado")
    return FileResponse(target)


@router.post("/api/t8i/conversations", dependencies=[Depends(require_token)])
async def save_conversation(req: ConversationRequest) -> dict[str, Any]:
    root = _configured_path("conversations")
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = _safe_name(req.title)
    json_path = root / f"{stamp}_{stem}.json"
    md_path = root / f"{stamp}_{stem}.md"
    payload = {
        "title": req.title,
        "saved_at": _now(),
        "text": req.text,
        "context": req.context,
    }
    _atomic_json(json_path, payload)
    tmp = md_path.with_suffix(".md.tmp")
    tmp.write_text(f"# {req.title}\n\nSalvo em: {_now()}\n\n{req.text}\n", encoding="utf-8")
    tmp.replace(md_path)
    _append_manifest("conversation_saved", {"json": str(json_path), "markdown": str(md_path)})
    return {"ok": True, "json": str(json_path), "markdown": str(md_path)}


@router.get("/api/t8i/conversations", dependencies=[Depends(require_token)])
async def list_conversations() -> dict[str, Any]:
    root = _configured_path("conversations")
    if not root.exists():
        return {"items": []}
    items = []
    for path in root.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        items.append({
            "file": path.name,
            "path": str(path.resolve()),
            "title": data.get("title", path.stem),
            "saved_at": data.get("saved_at"),
        })
    items.sort(key=lambda x: x.get("saved_at") or "", reverse=True)
    return {"items": items[:500]}


@router.get("/api/t8i/conversations/load", dependencies=[Depends(require_token)])
async def load_conversation(path: str) -> dict[str, Any]:
    root = _configured_path("conversations")
    target = Path(path).resolve()
    if not target.is_file() or not _is_within(target, root):
        raise HTTPException(status_code=404, detail="Conversa não encontrada")
    return json.loads(target.read_text(encoding="utf-8"))


@router.get("/one/t8i", response_class=HTMLResponse)
async def t8i_panel() -> str:
    return r"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AURION ONE · Canon T8i RAW LAB</title><style>
:root{color-scheme:dark;font:15px system-ui;--bg:#05090e;--panel:#0d1822;--line:#1b4052;--cyan:#00d9ff;--amber:#ffb33b;--green:#62f5b0;--muted:#96adba}
*{box-sizing:border-box}body{margin:0;background:linear-gradient(180deg,#04080c,#07131a);color:#eef9ff}header{position:sticky;top:0;z-index:5;background:#071017;border-bottom:1px solid var(--line);padding:12px 18px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}header a{color:var(--cyan);text-decoration:none;font-weight:800}header b{font-size:1.05rem}.pill{border:1px solid var(--line);padding:7px 10px;border-radius:999px;color:var(--muted)}
main{max-width:1400px;margin:auto;padding:16px;display:grid;grid-template-columns:340px 1fr;gap:14px}.card{background:rgba(13,24,34,.96);border:1px solid var(--line);border-radius:14px;padding:14px;min-width:0}.wide{grid-column:1/-1}h2{margin:0 0 10px;font-size:1rem;color:#dff9ff}button,input,select,textarea{font:inherit;background:#08131b;color:#fff;border:1px solid #2b586a;border-radius:8px;padding:9px}button{cursor:pointer;background:#103b4d}button.primary{background:#075b68;border-color:#00aac2}.row{display:flex;gap:8px;flex-wrap:wrap}.row>*{flex:1}.stack{display:grid;gap:8px}.muted{color:var(--muted);font-size:.9rem}.ok{color:var(--green)}.warn{color:var(--amber)}code{color:#ffe095}.files{max-height:320px;overflow:auto;border:1px solid #193948;border-radius:9px}.file{padding:8px;border-bottom:1px solid #173542;cursor:pointer}.file:hover,.file.sel{background:#123344}.sliders{display:grid;grid-template-columns:repeat(2,minmax(180px,1fr));gap:9px}.slider label{display:flex;justify-content:space-between;color:#c7dce7}.slider input{width:100%;padding:0}.preview{min-height:420px;display:grid;place-items:center;background:#020508;border:1px dashed #245267;border-radius:10px;overflow:hidden}.preview img{max-width:100%;max-height:70vh}.status{white-space:pre-wrap;max-height:220px;overflow:auto;background:#03080b;padding:10px;border-radius:8px}.folders{font-size:.84rem;word-break:break-all;display:grid;gap:5px}.conversation textarea{min-height:220px;width:100%}@media(max-width:850px){main{grid-template-columns:1fr}.wide{grid-column:auto}.sliders{grid-template-columns:1fr}}</style></head>
<body><header><a href="/one">← AURION ONE</a><b>CANON T8i · RAW LAB</b><span class="pill">originais preservados</span><span class="pill">sidecar + manifesto</span></header>
<main>
<section class="card"><h2>1 · Cofre de pastas</h2><div class="stack">
<button class="primary" onclick="pick('workspace')">Escolher PASTA-MÃE e criar estrutura</button>
<div class="row"><button onclick="pick('source')">Originais</button><button onclick="pick('exports')">Exportados</button></div>
<div class="row"><button onclick="pick('conversations')">Conversas</button><button onclick="pick('presets')">Presets</button></div>
<div class="row"><select id="parentKey"><option value="workspace">Pasta-mãe</option><option value="source">Originais</option><option value="exports">Exportados</option><option value="conversations">Conversas</option><option value="presets">Presets</option></select><input id="newFolder" placeholder="Nome da nova pasta"><button onclick="makeFolder()">+ pasta</button></div>
<div id="folders" class="folders muted">Carregando...</div></div></section>

<section class="card"><h2>2 · Dependências</h2><p class="muted">Instala somente o pacote Python declarado para esta aba. Não roda no F5.</p><div id="deps"></div><button onclick="installDeps()">Baixar / instalar dependências</button><pre id="depLog" class="status"></pre></section>

<section class="card"><h2>3 · Arquivos T8i</h2><div class="row"><button onclick="loadFiles()">Atualizar lista</button><span id="selected" class="muted">nenhum selecionado</span></div><div id="files" class="files"></div><p class="muted">CR3 aqui é RAW fotográfico. A aba não trata CR3 como Canon Log/C-Log.</p></section>

<section class="card"><h2>4 · Revelação não destrutiva</h2><div class="sliders">
<div class="slider"><label>Exposição <span id="vExposure">0</span></label><input id="exposure" type="range" min="-5" max="5" step=".1" value="0"></div>
<div class="slider"><label>Contraste <span id="vContrast">0</span></label><input id="contrast" type="range" min="-100" max="100" value="0"></div>
<div class="slider"><label>Saturação <span id="vSaturation">0</span></label><input id="saturation" type="range" min="-100" max="100" value="0"></div>
<div class="slider"><label>Temperatura <span id="vTemperature">0</span></label><input id="temperature" type="range" min="-100" max="100" value="0"></div>
<div class="slider"><label>Matiz <span id="vTint">0</span></label><input id="tint" type="range" min="-100" max="100" value="0"></div>
<div class="slider"><label>Sombras <span id="vShadows">0</span></label><input id="shadows" type="range" min="-100" max="100" value="0"></div>
<div class="slider"><label>Realces <span id="vHighlights">0</span></label><input id="highlights" type="range" min="-100" max="100" value="0"></div>
</div><div class="row" style="margin-top:10px"><input id="outputName" placeholder="Nome de saída (opcional)"><select id="format"><option value="tiff16">TIFF 16-bit</option><option value="jpeg95">JPEG 95</option></select></div>
<div class="row" style="margin-top:8px"><button onclick="doPreview()">Gerar prévia</button><button class="primary" onclick="doDevelop()">REVELAR E SALVAR CÓPIA</button></div><pre id="processLog" class="status"></pre></section>

<section class="card wide"><h2>5 · Prévia</h2><div id="preview" class="preview"><span class="muted">Selecione um arquivo e gere a prévia.</span></div></section>

<section class="card wide conversation"><h2>6 · Depósito de conversas / caderno da sessão</h2><div class="row"><input id="convTitle" placeholder="Título da sessão"><button onclick="saveConversation()">Salvar conversa</button><button onclick="listConversations()">Abrir salvas</button></div><textarea id="convText" placeholder="Cole aqui decisões, prompts, passos, observações e respostas. Rascunho também fica salvo no navegador."></textarea><div id="conversations" class="files"></div><pre id="convLog" class="status"></pre></section>
</main><script>
'use strict'; const $=id=>document.getElementById(id); let key=sessionStorage.getItem('aurion_one_session_token')||localStorage.getItem('aurion_token')||''; let config={}, chosen='';
async function api(path,opts={}){if(!key)throw Error('Abra /one, conecte o token e volte para esta aba.');const r=await fetch(path,{...opts,headers:{...(opts.headers||{}),Authorization:'Bearer '+key}});let d;try{d=await r.json()}catch{throw Error('Resposta inválida ('+r.status+')')}if(!r.ok)throw Error(d.detail||'HTTP '+r.status);return d}
function showFolders(){const p=config.paths||{};$('folders').innerHTML=['workspace','source','previews','exports','conversations','presets','sidecars','logs'].map(k=>'<div><b>'+k+':</b> '+(k==='workspace'?(config.workspace||'—'):(p[k]||'—'))+'</div>').join('')}
async function loadConfig(){try{const d=await api('/api/t8i/config');config=d.config||{};showFolders();$('deps').innerHTML=Object.entries(d.dependencies||{}).map(([k,v])=>'<div class="'+(v?'ok':'warn')+'">'+(v?'●':'○')+' '+k+'</div>').join('')}catch(e){$('folders').textContent=e.message}}
async function pick(keyName){try{const d=await api('/api/t8i/pick-folder',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({key:keyName})});if(!d.cancelled){config=d.config;showFolders();if(keyName==='workspace'||keyName==='source')loadFiles()}}catch(e){alert(e.message)}}
async function makeFolder(){try{const d=await api('/api/t8i/create-folder',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({parent_key:$('parentKey').value,name:$('newFolder').value})});$('newFolder').value='';$('folders').insertAdjacentHTML('beforeend','<div class="ok">Criada: '+d.path+'</div>')}catch(e){alert(e.message)}}
async function installDeps(){$('depLog').textContent='Instalando...';try{const d=await api('/api/t8i/install-dependencies',{method:'POST'});$('depLog').textContent=(d.ok?'OK':'FALHOU')+'\n'+(d.stdout_tail||'')+'\n'+(d.stderr_tail||'');await loadConfig()}catch(e){$('depLog').textContent=e.message}}
async function loadFiles(){try{const d=await api('/api/t8i/files');$('files').innerHTML=(d.files||[]).map((f,i)=>'<div class="file" data-path="'+encodeURIComponent(f.path)+'" onclick="chooseFile(this)">'+f.name+' <span class="muted">· '+(f.size/1048576).toFixed(1)+' MB</span></div>').join('')||'<div class="file">Nenhum arquivo suportado.</div>'}catch(e){$('files').innerHTML='<div class="file">'+e.message+'</div>'}}
function chooseFile(el){document.querySelectorAll('.file.sel').forEach(x=>x.classList.remove('sel'));el.classList.add('sel');chosen=decodeURIComponent(el.dataset.path);$('selected').textContent=chosen.split(/[/\\]/).pop()}
for(const id of ['exposure','contrast','saturation','temperature','tint','shadows','highlights']){$(id).oninput=()=>{$('v'+id[0].toUpperCase()+id.slice(1)).textContent=$(id).value}}
function payload(){if(!chosen)throw Error('Selecione um arquivo.');return{source:chosen,output_name:$('outputName').value||null,export_format:$('format').value,exposure:+$('exposure').value,contrast:+$('contrast').value,saturation:+$('saturation').value,temperature:+$('temperature').value,tint:+$('tint').value,shadows:+$('shadows').value,highlights:+$('highlights').value}}
async function doPreview(){try{$('processLog').textContent='Gerando prévia...';const d=await api('/api/t8i/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload())});$('processLog').textContent='Prévia: '+d.output;const url='/api/t8i/file?path='+encodeURIComponent(d.output);const r=await fetch(url,{headers:{Authorization:'Bearer '+key}});if(!r.ok)throw Error('Falha ao abrir prévia');const blob=await r.blob();const src=URL.createObjectURL(blob);$('preview').innerHTML='<img alt="Prévia revelada">';$('preview').querySelector('img').src=src}catch(e){$('processLog').textContent='ERRO: '+e.message}}
async function doDevelop(){try{$('processLog').textContent='Revelando sem alterar o original...';const d=await api('/api/t8i/develop',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload())});$('processLog').textContent='SALVO\n'+d.output+'\nSIDECAR\n'+d.sidecar}catch(e){$('processLog').textContent='ERRO: '+e.message}}
const draftKey='aurion_t8i_conversation_draft';$('convText').value=localStorage.getItem(draftKey)||'';$('convText').addEventListener('input',()=>localStorage.setItem(draftKey,$('convText').value));
async function saveConversation(){try{const title=$('convTitle').value.trim()||('T8i '+new Date().toLocaleString());const d=await api('/api/t8i/conversations',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title,text:$('convText').value,context:{selected_file:chosen,develop_settings:chosen?payload():null}})});$('convLog').textContent='SALVO\n'+d.json+'\n'+d.markdown;localStorage.removeItem(draftKey);await listConversations()}catch(e){$('convLog').textContent=e.message}}
async function listConversations(){try{const d=await api('/api/t8i/conversations');$('conversations').innerHTML=(d.items||[]).map(x=>'<div class="file" data-path="'+encodeURIComponent(x.path)+'" onclick="loadConversation(this)"><b>'+x.title+'</b><br><span class="muted">'+(x.saved_at||'')+'</span></div>').join('')||'<div class="file">Nenhuma conversa salva.</div>'}catch(e){$('convLog').textContent=e.message}}
async function loadConversation(el){try{const d=await api('/api/t8i/conversations/load?path='+encodeURIComponent(decodeURIComponent(el.dataset.path)));$('convTitle').value=d.title||'';$('convText').value=d.text||'';localStorage.setItem(draftKey,$('convText').value)}catch(e){$('convLog').textContent=e.message}}
loadConfig().then(loadFiles).then(listConversations);
</script></body></html>"""


