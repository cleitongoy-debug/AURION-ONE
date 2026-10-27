# -*- coding: utf-8 -*-
"""AURION ONE v0.4 — painel funcional com conexoes elasticas reais.
Paleta da referencia: preto, laranja vibrante, branco e roxo; ciano apenas para status.
Conexoes: curvas bezier visuais entre portas; integracoes Ollama e ComfyUI
por APIs separadas. Estado persistido (F5).
NAO substitui ADAPTA_BASE_TRAVADA.py. Operador: ANARK.
"""
from __future__ import annotations
import json, os, hashlib, difflib, socket, subprocess, sys, threading, time, urllib.request, webbrowser, shutil, tempfile, uuid, traceback, ctypes, string, zipfile, xml.etree.ElementTree as ET, re
from datetime import datetime
from pathlib import Path
from typing import Any
try:
    from flask import Flask, jsonify, request, render_template_string
except ImportError:
    print("Flask ausente neste Python. Use o ambiente Python do painel existente; nenhuma instalacao automatica sera feita.")
    raise

# ---------- BASE (fallbacks reais) ----------
ROOT = Path(__file__).resolve().parent
PROJECT = Path(r"C:\Users\ADM_PESS\Desktop\painelseguro#1 - Copia")
if not PROJECT.exists():
    for c in [Path(r"D:\ATIVACAO#BASE#8#1#26"), Path.home()/"Desktop"/"AURION"]:
        if c.exists(): PROJECT = c; break
MODELS = PROJECT/"models"
LOG_DIR = ROOT/"_aurion_logs"
STATE_FILE = ROOT/"config"/"aurion_one_state.json"
LOG_DIR.mkdir(parents=True, exist_ok=True)
HOST="127.0.0.1"; PORT=5058; COMFY_PORT=8188; OLLAMA_PORT=11434; OPENWEBUI_PORT=8080
COMFY_URL=f"http://127.0.0.1:{COMFY_PORT}"; OLLAMA_URL=f"http://127.0.0.1:{OLLAMA_PORT}"
app = Flask(__name__)
LOCK = threading.RLock()
BOOT={"step":"Inicializando interface", "done":0, "total":8, "ready":False, "details":[], "started":time.time()}
BUILD="2026.09.24-T8I-RAW-LAB-15"
_CACHE = {"comfy":None,"comfy_at":0,"ollama":None,"ollama_at":0}

def log(msg, error=False):
    line=f"[{datetime.now():%H:%M:%S}] {msg}"
    try:
        f=LOG_DIR/("errors.log" if error else "aurion.log")
        with f.open("a",encoding="utf-8") as fh: fh.write(line+"\n")
    except Exception: pass

def port_open(p):
    s=socket.socket(); s.settimeout(.4)
    try: return s.connect_ex(("127.0.0.1",p))==0
    finally: s.close()

def http_json(url, timeout=3):
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"AURION/0.3"}),timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8",errors="ignore"))
    except Exception: return None

def post_json(url, payload, timeout=30):
    req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers={"Content-Type":"application/json","User-Agent":"AURION/0.3"},method="POST")
    with urllib.request.urlopen(req,timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8",errors="ignore"))

# ---------- ESTADO PERSISTENTE ----------
DEFAULT_STATE = {
    "nodes": [
        {"id":"ollama","label":"Ollama","kind":"service","x":80,"y":100,"port":11434,"inputs":[],"outputs":["out"]},
        {"id":"comfy","label":"ComfyUI","kind":"service","x":80,"y":280,"port":8188,"inputs":[],"outputs":["out"]},
        {"id":"agente","label":"Agente","kind":"agent","x":430,"y":100,"port":None,"inputs":["in"],"outputs":[]},
        {"id":"geracao","label":"Gerar Imagem","kind":"action","x":430,"y":280,"port":None,"inputs":["in"],"outputs":[]},
        {"id":"modelos","label":"Modelos","kind":"data","x":430,"y":460,"port":None,"inputs":[],"outputs":[]},
    ],
    "connections": [["ollama","out","agente","in"],["comfy","out","geracao","in"]],
    "spaces": [
        {"id":"s1","name":"Projetos","items":[]},
        {"id":"s2","name":"Referencias","items":[]},
        {"id":"s3","name":"Geracao","items":[]},
    ],
    "jobs": [],
    "operators": [{"name": n, "hours": None, "status": "NÃO VERIFICADO"} for n in ("JSON13", "DS20", "GB", "BB", "JR")],
}
def load_state():
    with LOCK:
        try:
            if STATE_FILE.exists():
                data=json.loads(STATE_FILE.read_text(encoding="utf-8"))
                if isinstance(data,dict): return data
        except Exception as e: log(f"Falha ao ler estado: {e}",True)
        return json.loads(json.dumps(DEFAULT_STATE))
def save_state(st):
    with LOCK:
        tmp=None
        try:
            STATE_FILE.parent.mkdir(parents=True,exist_ok=True)
            with tempfile.NamedTemporaryFile(mode="w",encoding="utf-8",dir=str(STATE_FILE.parent),prefix="aurion_",suffix=".tmp",delete=False) as f:
                tmp=Path(f.name); json.dump(st,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
            os.replace(tmp,STATE_FILE)
            return True
        except Exception as e:
            log(f"save_state: {e}",True)
            return False
        finally:
            if tmp and tmp.exists(): tmp.unlink(missing_ok=True)

# ---------- HEALTH (3 estados: OFFLINE/PORT/ONLINE) ----------
def health():
    h={}
    # painel
    if port_open(PORT): h["painel"]="ONLINE" if http_json(f"http://127.0.0.1:{PORT}/api/one/boot",2) else "PORT"
    else: h["painel"]="OFFLINE"
    # comfy
    now=time.time()
    if now-_CACHE["comfy_at"]>3:
        if port_open(COMFY_PORT):
            _CACHE["comfy"]="ONLINE" if http_json(f"{COMFY_URL}/system_stats",2) else "PORT"
        else: _CACHE["comfy"]="OFFLINE"
        _CACHE["comfy_at"]=now
    h["comfy"]=_CACHE["comfy"]
    # ollama
    if now-_CACHE["ollama_at"]>3:
        if port_open(OLLAMA_PORT):
            _CACHE["ollama"]="ONLINE" if http_json(f"{OLLAMA_URL}/api/tags",2) else "PORT"
        else: _CACHE["ollama"]="OFFLINE"
        _CACHE["ollama_at"]=now
    h["ollama"]=_CACHE["ollama"]
    h["webui"]="ONLINE" if http_json(f"http://127.0.0.1:{OPENWEBUI_PORT}/api/models",2) else ("PORT" if port_open(OPENWEBUI_PORT) else "OFFLINE")
    return h

def ollama_models():
    d=http_json(f"{OLLAMA_URL}/api/tags",3)
    return [m.get("name") for m in d.get("models",[]) if isinstance(m,dict) and m.get("name")] if isinstance(d,dict) else []

def comfy_checkpoints():
    # Consultar apenas o nó necessário; algumas instalações não respondem a /object_info completo.
    d=http_json(f"{COMFY_URL}/object_info/CheckpointLoaderSimple",8)
    if not isinstance(d,dict) or "CheckpointLoaderSimple" not in d:
        d=http_json(f"{COMFY_URL}/object_info",10)
    try: return [str(x) for x in d["CheckpointLoaderSimple"]["input"]["required"]["ckpt_name"][0] if x]
    except (KeyError,IndexError,TypeError):return []

def comfy_loader_models():
    """Modelos de difusão expostos pelo ComfyUI; não são checkpoints SDXL."""
    result=[]
    for node,field in (("UNETLoader","unet_name"),("DiffusionModelLoader","unet_name")):
        data=http_json(f"{COMFY_URL}/object_info/{node}",5) or {}
        try:
            values=data[node]["input"]["required"][field][0]
            result.extend(str(v) for v in values if isinstance(v,str))
        except (KeyError,IndexError,TypeError):pass
    return list(dict.fromkeys(result))

# ---------- FLUXOS REAIS ----------
def local_context(query, limit=10):
    """Somente metadados previamente catalogados; nenhuma execução/leitura de documentos."""
    cache=ROOT/"config"/"aurion_library_private.json"
    if not cache.is_file(): return "Catálogo local ausente; use BIBLIOTECA > CATALOGAR para autorizar o inventário."
    try:
        data=json.loads(cache.read_text(encoding="utf-8"))
        files=data.get("files",[])
        words=[w for w in re.findall(r"[\wÀ-ÿ#.-]{3,}",query.casefold()) if w not in {"aurion","sistema","arquivo","arquivos","meu","minha","quero","sobre","investiga","investigar","externo","externos","favor","pode","oque","qual","como","tudo"}][:10]
        matches=[]
        for item in files:
            if not isinstance(item,dict):continue
            text=" ".join(str(item.get(k,"")) for k in ("name","path","category","subject","origin")).casefold()
            score=sum(1 for w in words if w in text)
            if score:matches.append((score,item))
        matches.sort(key=lambda x:-x[0])
        lines=[f"Catálogo: {len(files)} itens; busca por {words or '[sem termo específico]'}; resultados {len(matches)}; inventário limitado={data.get('limited',False)}."]
        for _,item in matches[:limit]:lines.append(str(item.get("path",item.get("name","")))[:350])
        if not matches:lines.append("Nenhum arquivo correspondente encontrado no catálogo salvo. Não significa ausência no PC.")
        return "\n".join(lines)
    except (OSError,ValueError,TypeError) as exc:return "Catálogo indisponível: "+type(exc).__name__

def run_agent_chat(msg, model=None):
    if not port_open(OLLAMA_PORT): return None,"Ollama offline."
    ms=ollama_models()
    if not ms: return None,"Nenhum modelo Ollama instalado."
    m=model if model in ms else ms[0]
    try:
        r=post_json(f"{OLLAMA_URL}/api/generate",{"model":m,"prompt":("Você é o agente local AURION ONE. Responda sempre em português brasileiro. Você não tem acesso direto ao PC nem permissão para executar comandos; apenas conhece informações fornecidas pelo painel. Se o usuário pedir investigação, indique que precisa acionar a ferramenta de catálogo pelo botão ou comando /biblioteca. Não invente diagnósticos ou arquivos.\n\nUsuário: "+msg+"\n\nEVIDÊNCIA LOCAL (metadados; não conteúdo):\n"+local_context(msg)),"stream":False,"options":{"temperature":0.1,"num_predict":300}},120)
        return r.get("response",""),m
    except Exception as e: return None,str(e)

def run_image_gen(prompt, checkpoint=None, width=1024, height=1024, steps=28, cfg=7, seed=-1, negative=""):
    if not (64<=width<=2048 and 64<=height<=2048 and width%8==0 and height%8==0 and 1<=steps<=100 and 0.1<=cfg<=30):
        return None,"Parâmetros inválidos: dimensões 64–2048 múltiplas de 8, passos 1–100, CFG 0,1–30."
    if not port_open(COMFY_PORT): return None,"ComfyUI offline."
    ck=checkpoint or (comfy_checkpoints() or [None])[0]
    if not ck: return None,"Nenhum checkpoint encontrado."
    if seed<0: seed=int(time.time()*1000)%2147483647
    if ck not in comfy_checkpoints(): return None,"Checkpoint nao reconhecido pelo ComfyUI; fluxo SDXL nao e compativel com todo modelo (Flux/GGUF exige workflow proprio)."
    info=http_json(COMFY_URL+"/object_info",6) or {}
    needed=("KSampler","CheckpointLoaderSimple","EmptyLatentImage","CLIPTextEncode","VAEDecode","SaveImage")
    missing=[name for name in needed if name not in info]
    if missing:return None,"Nós necessários ausentes no ComfyUI: "+", ".join(missing)
    wf={"3":{"class_type":"KSampler","inputs":{"seed":seed,"steps":steps,"cfg":cfg,"sampler_name":"euler","scheduler":"normal","denoise":1.0,"model":["4",0],"positive":["6",0],"negative":["7",0],"latent_image":["5",0]}},
        "4":{"class_type":"CheckpointLoaderSimple","inputs":{"ckpt_name":ck}},
        "5":{"class_type":"EmptyLatentImage","inputs":{"width":width,"height":height,"batch_size":1}},
        "6":{"class_type":"CLIPTextEncode","inputs":{"text":prompt,"clip":["4",1]}},
        "7":{"class_type":"CLIPTextEncode","inputs":{"text":negative[:3000] if negative else "low quality, blurry, distorted, watermark","clip":["4",1]}},
        "8":{"class_type":"VAEDecode","inputs":{"samples":["3",0],"vae":["4",2]}},
        "9":{"class_type":"SaveImage","inputs":{"filename_prefix":"AURION","images":["8",0]}}}
    try:
        r=post_json(f"{COMFY_URL}/prompt",{"prompt":wf,"client_id":f"aurion-{int(time.time()*1000)}"},30)
        pid=r.get("prompt_id") if isinstance(r,dict) else None
        return pid,ck
    except Exception as e: return None,str(e)

def image_progress(pid):
    hist=http_json(f"{COMFY_URL}/history/{pid}",5)
    if isinstance(hist,dict) and pid in hist:
        item=hist[pid]
        if item.get("status",{}).get("status_str")=="error": return {"status":"erro","progress":0,"images":[],"message":"ComfyUI informou erro; veja log do ComfyUI"}
        imgs=[]
        for item in hist.values():
            for node in (item.get("outputs",{}) or {}).values():
                for img in (node.get("images",[]) or []):
                    if img.get("filename"): imgs.append(img)
        media=[]
        for completed in hist.values():
            for node in (completed.get("outputs",{}) or {}).values():
                for field in ("gifs","videos","animated"):
                    for item in (node.get(field,[]) or []):
                        if isinstance(item,dict) and item.get("filename"):media.append(item)
        status="concluido" if imgs or media else "concluido_sem_imagem"
        return {"status":status,"progress":100,"images":imgs,"media":media,"message":"Workflow não retornou arquivo de imagem/vídeo" if not imgs and not media else ""}
    q=http_json(f"{COMFY_URL}/queue",5) or {}
    running=q.get("queue_running",[]) or []; pending=q.get("queue_pending",[]) or []
    if any(isinstance(x,list) and len(x)>1 and x[1]==pid for x in running): st="executando"
    elif any(isinstance(x,list) and len(x)>1 and x[1]==pid for x in pending): st="fila"
    else: st="processando"
    return {"status":st,"progress":None,"images":[]}

# ---------- T8I RAW / CR3 ----------
try:
    from aurion_t8i_web import register_t8i
    register_t8i(app, log)
    log("T8I RAW LAB carregado")
except Exception as exc:
    log("T8I RAW LAB indisponivel: " + str(exc), True)

# ---------- ROTAS ----------
@app.get("/assets/Mesa_de_Operacao_REAL_AURION_v2.png")
def historic_orb():
    from flask import send_file
    return send_file(ROOT/"assets"/"Mesa_de_Operacao_REAL_AURION_v2.png",mimetype="image/png")

@app.get("/")
def index(): return render_template_string(HTML)
@app.get("/api/one/boot")
def boot(): return jsonify({"ok":True,"build":BUILD,**BOOT})
@app.get("/api/one/diagnostico")
def diagnostico(): return jsonify({"ok":True,"build":BUILD,"health":health(),"base_existe":PROJECT.exists(),"modelos_ollama":ollama_models(),"checkpoints_comfy":comfy_checkpoints(),"logs":str(LOG_DIR)})
@app.get("/api/one/state")
def api_state(): return jsonify({"ok":True,"state":load_state()})
@app.post("/api/one/state")
def api_save():
    st=request.get_json(silent=True) or {}
    if not isinstance(st,dict): return jsonify({"ok":False,"error":"JSON invalido"}),400
    with LOCK:
        cur=load_state()
        for k in ("nodes","connections","spaces","jobs","operators"):
            if k in st: cur[k]=st[k]
        ok=save_state(cur)
    return (jsonify({"ok":True}) if ok else (jsonify({"ok":False,"error":"falha ao salvar"}),500))
@app.get("/api/one/health")
def api_health(): return jsonify({"ok":True,"health":health()})
@app.get("/api/one/nodes")
def api_nodes():
    return jsonify({"ok":True,"health":health(),"ollama_models":ollama_models(),"checkpoints":comfy_checkpoints(),"diffusion_models":comfy_loader_models()})
@app.get("/api/one/library")
def api_library():
    import aurion_library
    roots=[Path(x) for x in scan_roots() if Path(x).is_dir()]
    # O scan completo é acionado pelo operador; cache não publica dados no Git.
    cache=ROOT/"config"/"aurion_library_private.json"
    if cache.is_file():
        try:
            d=json.loads(cache.read_text(encoding="utf-8"));return jsonify({"ok":True,"catalog":d})
        except (OSError,ValueError):pass
    return jsonify({"ok":True,"catalog":None,"roots":len(roots),"message":"Clique em CATALOGAR para varrer os discos acessíveis."})

@app.post("/api/one/library/scan")
def api_library_scan():
    import aurion_library
    roots=scan_roots()
    d=aurion_library.catalog(roots)
    atomic_json(ROOT/"config"/"aurion_library_private.json",d)
    log(f"Biblioteca: {d['checked']} arquivos examinados, {len(d['files'])} catalogados, {len(d['crossings'])} cruzamentos")
    return jsonify({"ok":True,"catalog":d})

@app.post("/api/one/chat")
def api_chat():
    d=request.get_json(silent=True) or {}
    msg=str(d.get("message","")).strip()
    if not msg: return jsonify({"reply":"Digite algo.","model":None})
    if msg.casefold() in ("/biblioteca", "/catalogo", "/catálogo", "/diagnostico", "/diagnóstico"):
        cache=ROOT/"config"/"aurion_library_private.json"
        if not cache.is_file():return jsonify({"reply":"Catálogo ainda não criado. Abra BIBLIOTECA e clique CATALOGAR DISCO LOCAL E EXTERNO.","model":"ferramenta local · somente leitura"})
        try:
            c=json.loads(cache.read_text(encoding="utf-8"))
            report={"arquivos_catalogados":len(c.get("files",[])),"categorias":c.get("counts",{}),"assuntos":{k:v.get("count",0) for k,v in c.get("subjects",{}).items()},"meses":dict(list(c.get("months",{}).items())[:12]),"cruzamentos":len(c.get("crossings",[])),"limite_atingido":c.get("limited",False),"aviso":"metadados; não é acesso irrestrito ao PC nem Drive remoto"}
            return jsonify({"reply":json.dumps(report,ensure_ascii=False,indent=2),"model":"ferramenta local · somente leitura"})
        except (OSError,ValueError) as exc:return jsonify({"reply":"Falha ao ler catálogo: "+str(exc)[:160],"model":None}),500
    reply,model=run_agent_chat(msg,d.get("model"))
    if reply is None: return jsonify({"reply":model,"model":None}),502
    return jsonify({"reply":reply,"model":model})
@app.post("/api/one/image")
def api_image():
    d=request.get_json(silent=True) or {}
    prompt=str(d.get("prompt","")).strip()
    if not prompt: return jsonify({"ok":False,"message":"Digite o prompt"}),400
    try:
        width=int(d.get("width",1024));height=int(d.get("height",1024));steps=int(d.get("steps",28));cfg=float(d.get("cfg",7));seed=int(d.get("seed",-1))
    except (TypeError,ValueError):return jsonify({"ok":False,"message":"Dimensão, passos, CFG ou seed inválidos"}),400
    pid,ck=run_image_gen(prompt[:4000],d.get("checkpoint"),width,height,steps,cfg,seed,str(d.get("negative","")))
    if pid is None: return jsonify({"ok":False,"message":ck}),502
    return jsonify({"ok":True,"prompt_id":pid,"checkpoint":ck})
@app.get("/api/one/image/<pid>")
def api_img_progress(pid): return jsonify(image_progress(pid))
@app.post("/api/one/space")
def api_space_add():
    d=request.get_json(silent=True) or {}
    sid=str(d.get("space","")); item=str(d.get("item","")).strip()
    if not sid or not item: return jsonify({"ok":False}),400
    with LOCK:
        st=load_state()
        for space in st.get("spaces",[]):
            if space["id"]==sid and item not in space["items"]: space["items"].append(item)
        ok=save_state(st)
    return (jsonify({"ok":True}) if ok else (jsonify({"ok":False,"error":"Falha ao gravar"}),500))

@app.get("/api/one/operators")
def operators_get():
    return jsonify({"operators":load_state().get("operators",DEFAULT_STATE["operators"])})

@app.post("/api/one/operators")
def operators_save():
    payload=request.get_json(silent=True) or {}
    people=payload.get("operators")
    names=("JSON13","DS20","GB","BB","JR")
    if not isinstance(people,list) or len(people)!=len(names):
        return jsonify({"error":"Lista de operadores inválida"}),400
    cleaned=[]
    for name,item in zip(names,people):
        if not isinstance(item,dict) or item.get("name")!=name: return jsonify({"error":"Operador inválido"}),400
        h=item.get("hours")
        if h not in (None,""):
            try: h=float(h)
            except (ValueError,TypeError): return jsonify({"error":"Horas inválidas"}),400
            if not 0<=h<=1000000: return jsonify({"error":"Horas fora do limite"}),400
        else: h=None
        status=str(item.get("status","NÃO VERIFICADO"))[:60]
        cleaned.append({"name":name,"hours":h,"status":status})
    state=load_state();state["operators"]=cleaned
    if not save_state(state): return jsonify({"error":"Falha ao gravar"}),500
    return jsonify({"ok":True,"operators":cleaned})

@app.get("/api/one/inventory")
def inventory():
    # Inventário deliberadamente limitado: nunca afirma varredura completa de discos.
    paths=[ROOT,PROJECT,Path(r"C:\COMFYUI\ComfyUI_windows_portable\ComfyUI"),Path(r"C:\######AGENTE#####STATUS######\base#777\models")]
    return jsonify({"scope":"caminhos conhecidos, não scan integral", "paths":[{"path":str(x),"exists":x.exists()} for x in paths],"python":sys.executable,"ollama":shutil.which("ollama"),"git":shutil.which("git")})


# ---------- EXPANSAO ADITIVA: inventario, configuracoes, integracoes ----------
SCAN_LOCK=threading.Lock()
SCAN_STATUS={"running":False,"phase":"Aguardando","folders":0,"files":0,"found":[],"errors":[],"truncated":False,"finished":False}
SCAN_FILE=ROOT/"config"/"aurion_scan_report.json"
SETTINGS_FILE=ROOT/"config"/"aurion_settings.json"
DEFAULT_SETTINGS={"accent":"#ff7300","purple":"#923de2","cyan":"#38cfff","orb_name":"AURION","orb_motion":True,"cover":"","paths":{},"selected_model":""}
APP_EXES={"photoshop":{"photoshop.exe"},"after_effects":{"afterfx.exe"},"cinema4d":{"cinema 4d.exe","cinema4d.exe"},"unreal":{"unrealeditor.exe"},"blender":{"blender.exe"},"davinci":{"resolve.exe"},"lmstudio":{"lm studio.exe","lmstudio.exe"},"nuke":{"nuke.exe","nuke15.0.exe","nuke14.0.exe"},"nuke_studio":{"nukestudio.exe"},"premiere":{"adobe premiere pro.exe"},"illustrator":{"illustrator.exe"},"substance_painter":{"adobe substance 3d painter.exe"},"houdini":{"houdini.exe","houdinifx.exe"},"obs":{"obs64.exe"}}
ALLOWED_KINDS={"ollama","comfy","python","git","base","models","skill","workflow","launcher","history",*APP_EXES.keys()}

EXTS={".safetensors",".ckpt",".gguf",".pt",".pth",".onnx",".json",".jsonl",".yaml",".yml",".bat",".cmd",".ps1"}
KEYWORDS=("aurion","adapta","comfy","ollama","lumen","model","workflow","skill","scan","history","jarvis","neutron","openwebui","python")
APP_EXE_TO_KIND={exe:kind for kind,names in APP_EXES.items() for exe in names}

def load_settings():
    try:
        d=json.loads(SETTINGS_FILE.read_text(encoding="utf-8"));return {**DEFAULT_SETTINGS,**d} if isinstance(d,dict) else dict(DEFAULT_SETTINGS)
    except Exception:return dict(DEFAULT_SETTINGS)
def atomic_json(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=None
    try:
        with tempfile.NamedTemporaryFile(mode="w",encoding="utf-8",dir=str(path.parent),delete=False,suffix=".tmp") as f:
            tmp=Path(f.name);json.dump(data,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if tmp and tmp.exists():tmp.unlink(missing_ok=True)
def scan_roots():
    roots=[ROOT,PROJECT,Path.home()/"Desktop",Path.home()/"Downloads",Path(r"C:\COMFYUI"),Path(r"D:\ComfyUI"),Path(r"C:\######AGENTE#####STATUS######"),Path(r"D:\ATIVACAO#BASE#8#1#26")]
    # Prioridade absoluta para os diretórios reais de modelos, antes de atingir o limite do scan geral.
    roots=[Path(r"C:\######AGENTE#####STATUS######\base#777\models"),Path(r"C:\COMFYUI\ComfyUI_windows_portable\ComfyUI\models"),Path(r"D:\ComfyUI\ComfyUI\models"),PROJECT/"models",ROOT/"models"]+roots
    if os.name=="nt":
        mask=ctypes.windll.kernel32.GetLogicalDrives()
        for i,letter in enumerate(string.ascii_uppercase):
            if mask & (1<<i):
                drive=Path(letter+":\\")
                try:
                    kind=ctypes.windll.kernel32.GetDriveTypeW(str(drive))
                    if kind in (2,3):roots.append(drive)
                except Exception:pass
    roots.extend(Path(x) for x in load_settings().get("paths",{}).values() if isinstance(x,str) and x.strip())
    return list(dict.fromkeys(str(p) for p in roots if p.exists()))
def do_scan():
    global SCAN_STATUS
    with SCAN_LOCK:
        SCAN_STATUS={"running":True,"phase":"Recuperando rastros anteriores","folders":0,"files":0,"found":[],"errors":[],"truncated":False,"finished":False,"started":time.time()}
    found=[];seen=set();deadline=time.monotonic()+180;max_dirs=35000;max_files=180000
    def add(path,kind,source):
        key=str(path).lower()
        if key not in seen and len(found)<12000:
            seen.add(key);found.append({"path":str(path),"kind":kind,"source":source})
    for f in (SCAN_FILE,ROOT/"scan_report.json",ROOT/"remote-agent"/"data"/"history_scan.json",PROJECT/"scan_report.json"):
        if f.is_file():
            add(f,"history","rastro anterior")
            try:
                data=json.loads(f.read_text(encoding="utf-8"))
                def walk(x,depth=0):
                    if depth>5:return
                    if isinstance(x,dict):
                        for k,v in list(x.items())[:400]:
                            if isinstance(v,str) and ("path" in k.lower() or "caminho" in k.lower() or k.lower() in ("python","comfy","ollama")) and Path(v).exists():add(Path(v),"history","rastro validado")
                            elif isinstance(v,(dict,list)):walk(v,depth+1)
                    elif isinstance(x,list):
                        for v in x[:400]:walk(v,depth+1)
                walk(data)
            except Exception as e:SCAN_STATUS["errors"].append("Rastro ilegível: "+f.name+" "+type(e).__name__)
    roots=scan_roots();SCAN_STATUS["roots"]=roots
    for root in roots:
        if time.monotonic()>deadline or SCAN_STATUS["folders"]>=max_dirs or SCAN_STATUS["files"]>=max_files:break
        SCAN_STATUS["phase"]="Inventariando "+root
        def onerror(e):
            if len(SCAN_STATUS["errors"])<35:SCAN_STATUS["errors"].append(str(e)[:170])
        for base,dirs,files in os.walk(root,topdown=True,onerror=onerror,followlinks=False):
            if time.monotonic()>deadline or SCAN_STATUS["folders"]>=max_dirs or SCAN_STATUS["files"]>=max_files:
                SCAN_STATUS["truncated"]=True;break
            SCAN_STATUS["folders"]+=1
            dirs[:]=[d for d in dirs if d.lower() not in ("$recycle.bin","system volume information","node_modules",".git","__pycache__","windows","winsxs","appdata") and not d.startswith(".")]
            for d in dirs:
                if any(k in d.lower() for k in KEYWORDS):add(Path(base)/d,"base","nome de pasta")
            for name in files:
                SCAN_STATUS["files"]+=1
                n=name.lower();path=Path(base)/name
                if n in APP_EXE_TO_KIND:
                    add(path,"program","executável de programa reconhecido: "+APP_EXE_TO_KIND[n])
                elif n in ("ollama.exe","python.exe","git.exe","main.py","adapta.py","funcionando.py","aurion_one.py","aurion_one_hud.py","skill.md","skill.txt"):
                    add(path,"launcher" if path.suffix.lower() in (".exe",".py") else "skill","nome exato")
                elif path.suffix.lower() in (".safetensors",".ckpt",".gguf",".onnx"):
                    # Um checkpoint pode ter qualquer nome; não depender de 'aurion' ou 'model'.
                    add(path,"models","extensão de modelo; uso ainda não validado")
                elif path.suffix.lower() == ".docx" and any(k in n for k in ("biblia","bíblia","reuniao","reunião","historia","história","aurion","lumen","digitalpen")):
                    add(path,"knowledge","documento DOCX identificado por nome")
                elif any(k in n for k in KEYWORDS) and path.suffix.lower() in EXTS:
                    kind="workflow" if "workflow" in n else "history"
                    add(path,kind,"nome compatível")
                if SCAN_STATUS["files"]>=max_files:break
            if SCAN_STATUS["folders"]%75==0:SCAN_STATUS["found"]=found[-120:]
    SCAN_STATUS["phase"]="Conferindo APIs e salvando relatório"
    report={"date":time.strftime("%Y-%m-%d %H:%M:%S"),"roots":roots,"folders":SCAN_STATUS["folders"],"files":SCAN_STATUS["files"],"found":found,"errors":SCAN_STATUS["errors"],"truncated":SCAN_STATUS["truncated"] or time.monotonic()>deadline,"services":health(),"models_ollama":ollama_models()}
    try:atomic_json(SCAN_FILE,report)
    except Exception as e:SCAN_STATUS["errors"].append("Falha ao salvar relatório: "+str(e)[:120])
    SCAN_STATUS.update({"running":False,"finished":True,"phase":"Concluído" if not report["truncated"] else "Concluído com limites","found":found[-250:],"total_found":len(found),"truncated":report["truncated"],"report":str(SCAN_FILE)})
    log("Scan concluído: "+str(SCAN_STATUS["folders"])+" pastas, "+str(len(found))+" vestígios")
@app.post("/api/one/scan/start")
def scan_start():
    if SCAN_STATUS["running"]:return jsonify({"ok":True,"already_running":True})
    threading.Thread(target=do_scan,daemon=True,name="aurion-inventory").start()
    return jsonify({"ok":True,"started":True})
@app.get("/api/one/scan/progress")
def scan_progress():return jsonify({"ok":True,**SCAN_STATUS})
@app.get("/api/one/settings")
def settings_get():return jsonify({"ok":True,"settings":load_settings()})
@app.post("/api/one/settings")
def settings_save():
    d=request.get_json(silent=True) or {};new=dict(load_settings())
    for k in ("accent","purple","cyan"):
        v=d.get(k)
        if isinstance(v,str) and len(v)==7 and v.startswith("#") and all(c in string.hexdigits for c in v[1:]):new[k]=v
    for k in ("orb_name","cover","selected_model"):
        if isinstance(d.get(k),str):new[k]=d[k][:180]
    if isinstance(d.get("orb_motion"),bool):new["orb_motion"]=d["orb_motion"]
    if isinstance(d.get("paths"),dict):
        new["paths"]={str(k)[:40]:str(v)[:500] for k,v in d["paths"].items() if k in ALLOWED_KINDS and isinstance(v,str)}
    try:atomic_json(SETTINGS_FILE,new);return jsonify({"ok":True,"settings":new})
    except Exception as e:return jsonify({"ok":False,"error":str(e)[:150]}),500
@app.get("/api/one/integrations")
def integrations():
    paths=load_settings().get("paths",{});r={}
    for kind in sorted(ALLOWED_KINDS):
        path=paths.get(kind,"");r[kind]={"path":path,"exists":bool(path and Path(path).exists())}
    r["services"]=health();r["ollama_models"]=ollama_models();r["comfy_checkpoints"]=comfy_checkpoints()
    r["devices"]={"poco":"PAREAMENTO PENDENTE","band":"INTEGRAÇÃO PENDENTE","fone":"INTEGRAÇÃO PENDENTE"}
    return jsonify({"ok":True,"integrations":r})
@app.post("/api/one/service/start")
def service_start():
    kind=str((request.get_json(silent=True) or {}).get("service",""))
    if kind not in ("ollama","comfy"):return jsonify({"error":"Serviço não permitido"}),400
    if health().get(kind)=="ONLINE":return jsonify({"ok":True,"status":"já online"})
    paths=load_settings().get("paths",{});exe=Path(paths.get(kind,"")) if paths.get(kind) else None
    if kind=="ollama":
        if not exe or not exe.is_file():return jsonify({"error":"Configure o caminho do ollama.exe antes de iniciar"}),409
        cmd=[str(exe),"serve"];cwd=exe.parent
    else:
        if not exe:return jsonify({"error":"Configure o caminho da pasta ComfyUI"}),409
        main=exe/"main.py" if exe.is_dir() else exe
        portable=main.parent.parent/"python_embeded"/"python.exe"
        python=portable if portable.is_file() else Path(sys.executable)
        if not main.is_file() or main.name.lower()!="main.py":return jsonify({"error":"main.py do ComfyUI não localizado"}),409
        cmd=[str(python),"-s",str(main)] if portable.is_file() else [str(python),str(main)]
        cmd += ["--listen","127.0.0.1","--port","8188"]
        if portable.is_file():cmd.append("--windows-standalone-build")
        prepared=ROOT/"config"/"extra_model_paths_aurion.yaml"
        if prepared.is_file():cmd.extend(["--extra-model-paths-config",str(prepared)])
        cwd=main.parent
    try:
        dest=LOG_DIR/(kind+"_servico.log");dest.parent.mkdir(parents=True,exist_ok=True)
        with dest.open("ab") as out:subprocess.Popen(cmd,cwd=str(cwd),stdin=subprocess.DEVNULL,stdout=out,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        log("Inicialização solicitada: "+kind)
        return jsonify({"ok":True,"status":"iniciando; aguarde verificação HTTP","log":str(dest)}),202
    except Exception as e:return jsonify({"error":str(e)[:180]}),500


# ---------- CENTRAL ADITIVA: fontes locais, workflows e edicao reversivel ----------
KNOWLEDGE_DIR=ROOT/"conhecimento"; KNOWLEDGE_DIR.mkdir(exist_ok=True)
PATCH_DIR=ROOT/"_aurion_backups"; PATCH_DIR.mkdir(exist_ok=True)
ALLOWED_TEXT={".txt",".md",".json",".py",".log",".csv",".docx"}
def knowledge_files():
    roots=[KNOWLEDGE_DIR,PROJECT/"docs",ROOT/"docs",PROJECT/"SKILL#PAINEL",PROJECT/"SKILL#PAINEL"/"SKILL 1",ROOT/"docs"/"reunioes",Path(r"C:\AURION-ONE")/"docs",Path(r"C:\AURION-ONE")]
    # DOCX original costuma ficar em pastas já conhecidas; não exige digitação ou upload.
    candidate_dirs=[PROJECT,PROJECT/"documentos",PROJECT/"docs",Path(r"C:\AURION-ONE"),Path.home()/"Documents",ROOT]

    # Reutiliza o inventário existente em vez de exigir que o operador digite ou importe a Bíblia.
    discovered=[]
    try:
        report=json.loads(SCAN_FILE.read_text(encoding="utf-8"))
        discovered=[Path(x["path"]) for x in report.get("found",[]) if isinstance(x,dict) and x.get("kind")=="knowledge" and isinstance(x.get("path"),str)][:350]
    except (OSError,ValueError,TypeError,KeyError):pass
    files=[];seen=set()
    for base in candidate_dirs:
        if not base.is_dir():continue
        try:
            for p in base.iterdir():
                if p.is_file() and p.suffix.lower()==".docx" and any(k in p.name.casefold() for k in ("biblia","bíblia","aurion","reuniao","reunião","historia","história")) and p.stat().st_size<=8_000_000:
                    discovered.append(p)
        except OSError:pass
    for p in discovered:
        try:
            if p.is_file() and p.suffix.lower() in ALLOWED_TEXT and p.stat().st_size<=8_000_000 and str(p).lower() not in seen:
                files.append({"name":p.name,"path":str(p),"bytes":p.stat().st_size,"origin":"scan"});seen.add(str(p).lower())
        except OSError:pass
    for base in roots:
        if not base.is_dir():continue
        try:
            for i,p in enumerate(base.rglob("*")):
                if i>=6000:break
                if p.is_file() and p.suffix.lower() in ALLOWED_TEXT and p.stat().st_size<=8_000_000 and len(files)<400 and str(p).lower() not in seen:
                    files.append({"name":p.name,"path":str(p),"bytes":p.stat().st_size,"origin":"pasta"});seen.add(str(p).lower())
        except OSError:pass
    return files
@app.get("/api/one/knowledge")
def knowledge_list():return jsonify({"ok":True,"files":knowledge_files()})
@app.post("/api/one/knowledge/import")
def knowledge_import():
    f=request.files.get("file")
    if not f or not f.filename:return jsonify({"error":"Escolha um arquivo"}),400
    name=Path(f.filename.replace("\\","/")).name
    if not name or Path(name).suffix.lower() not in ALLOWED_TEXT:return jsonify({"error":"Formato não aceito"}),400
    raw=f.read(8_000_001)
    if len(raw)>8_000_000:return jsonify({"error":"Limite 8 MB"}),413
    if Path(name).suffix.lower() != ".docx":
        try:raw.decode("utf-8")
        except UnicodeDecodeError:return jsonify({"error":"Arquivo textual precisa estar em UTF-8"}),400
    elif not zipfile.is_zipfile(__import__('io').BytesIO(raw)):
        return jsonify({"error":"DOCX inválido"}),400
    dest=KNOWLEDGE_DIR/(str(int(time.time()*1000))+"_"+name)
    dest.write_bytes(raw);log("Documento importado por acao do operador: "+name)
    return jsonify({"ok":True,"name":name,"path":str(dest)})
@app.post("/api/one/knowledge/read")
def knowledge_read():
    path=str((request.get_json(silent=True) or {}).get("path",""))
    allowed={f["path"] for f in knowledge_files()}
    if path not in allowed:return jsonify({"error":"Arquivo fora da biblioteca"}),403
    p=Path(path)
    if p.suffix.lower()==".docx":
        try:
            with zipfile.ZipFile(p) as z:
                item=z.getinfo("word/document.xml")
                if item.file_size>24_000_000:return jsonify({"error":"DOCX excede limite descompactado"}),413
                with z.open(item) as f: xml=f.read(24_000_001)
            if len(xml)>24_000_000:return jsonify({"error":"DOCX excede limite"}),413
            root=ET.fromstring(xml)
            ns="{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
            text="\n".join("".join(t.text or "" for t in para.iter(ns+"t")) for para in root.iter(ns+"p"))
        except (OSError,ValueError,KeyError,zipfile.BadZipFile,ET.ParseError) as e:
            return jsonify({"error":"Não foi possível ler DOCX: "+type(e).__name__}),422
    else:text=p.read_text(encoding="utf-8",errors="replace")
    return jsonify({"ok":True,"text":text[:100000],"characters":len(text),"truncated":len(text)>100000,"origin":str(p)})
@app.get("/api/one/catalog")
def catalog():
    obj=http_json(COMFY_URL+"/object_info",8) or {}
    report={}
    for key in ("CheckpointLoaderSimple","UNETLoader","LoraLoader","VAELoader","ControlNetLoader"):
        info=obj.get(key,{}) if isinstance(obj,dict) else {}
        report[key]=info.get("input",{}).get("required",{}) if isinstance(info,dict) else {}
    inv=[]
    try:
        data=json.loads(SCAN_FILE.read_text(encoding="utf-8"))
        inv=[x for x in data.get("found",[]) if x.get("kind") in ("models","workflow")][:300]
    except (OSError,ValueError,TypeError):pass
    return jsonify({"ok":True,"comfy_online":bool(obj),"comfy_inputs":report,"scan_matches":inv,"ollama":ollama_models(),"note":"Arquivo localizado não é modelo carregado: ComfyUI precisa reconhecer o caminho."})
@app.get("/api/one/workflows/local")
def local_workflows():
    """Somente caminhos já inventariados; não executa arquivos ao listar."""
    found=[]
    try:
        report=json.loads(SCAN_FILE.read_text(encoding="utf-8"))
        for entry in report.get("found",[]):
            if entry.get("kind")=="workflow":
                path=Path(str(entry.get("path","")))
                if path.suffix.lower()==".json" and path.is_file() and path.stat().st_size<=2_000_000:
                    found.append({"path":str(path),"name":path.name})
    except (OSError,ValueError,TypeError):pass
    return jsonify({"ok":True,"workflows":found[:250]})

@app.post("/api/one/workflows/local/read")
def read_local_workflow():
    requested=str((request.get_json(silent=True) or {}).get("path",""))
    try:
        report=json.loads(SCAN_FILE.read_text(encoding="utf-8"))
        allowed={str(x.get("path","")) for x in report.get("found",[]) if x.get("kind")=="workflow"}
        if requested not in allowed:return jsonify({"ok":False,"error":"Workflow fora do inventário; execute SCAN GERAL."}),403
        p=Path(requested)
        if p.suffix.lower()!=".json" or p.stat().st_size>2_000_000:return jsonify({"ok":False,"error":"Arquivo inválido ou maior que 2 MB."}),413
        wf=json.loads(p.read_text(encoding="utf-8-sig"))
        if not isinstance(wf,dict):return jsonify({"ok":False,"error":"JSON não é objeto."}),422
        if "nodes" in wf and "links" in wf:return jsonify({"ok":False,"error":"Workflow visual detectado. Exporte no ComfyUI em formato API antes de executar; arquivo original preservado."}),422
        if not wf or not all(isinstance(v,dict) and isinstance(v.get("class_type"),str) and isinstance(v.get("inputs"),dict) for v in wf.values()):
            return jsonify({"ok":False,"error":"Workflow não está no formato API do ComfyUI."}),422
        return jsonify({"ok":True,"workflow":wf,"path":requested})
    except (OSError,ValueError,TypeError) as exc:return jsonify({"ok":False,"error":type(exc).__name__}),422

@app.post("/api/one/workflow/submit")
def workflow_submit():
    data=request.get_json(silent=True) or {}; wf=data.get("workflow")
    if not isinstance(wf,dict) or not 1<=len(wf)<=300:return jsonify({"error":"Importe JSON de workflow em formato API com 1 a 300 nós"}),400
    for key,node in wf.items():
        if not isinstance(key,str) or not isinstance(node,dict) or not isinstance(node.get("class_type"),str) or not isinstance(node.get("inputs"),dict):return jsonify({"error":"Workflow não está no formato API do ComfyUI"}),400
    if not http_json(COMFY_URL+"/system_stats",3):return jsonify({"error":"ComfyUI offline"}),503
    try:
        result=post_json(COMFY_URL+"/prompt",{"prompt":wf,"client_id":"aurion-central-"+uuid.uuid4().hex},25)
        if not isinstance(result,dict) or not result.get("prompt_id"):return jsonify({"error":"ComfyUI rejeitou workflow","detail":result}),422
        log("Workflow API enviado explicitamente: "+str(result["prompt_id"]))
        return jsonify({"ok":True,"prompt_id":result["prompt_id"],"node_errors":result.get("node_errors",{})})
    except Exception as exc:return jsonify({"error":str(exc)[:300]}),502
@app.post("/api/one/image/workflow")
def image_workflow_from_catalog():
    """Run an existing API workflow after explicit selection; replace only plain CLIPTextEncode prompts."""
    data=request.get_json(silent=True) or {}
    path=str(data.get("path", "")); prompt=str(data.get("prompt", "")).strip()
    if not prompt or len(prompt)>4000:return jsonify({"ok":False,"error":"Prompt vazio ou muito longo"}),400
    try:
        report=json.loads(SCAN_FILE.read_text(encoding="utf-8"))
        allowed={str(x.get("path","")) for x in report.get("found",[]) if x.get("kind")=="workflow"}
        if path not in allowed:return jsonify({"ok":False,"error":"Selecione workflow do inventário existente"}),403
        file=Path(path)
        if not file.is_file() or file.suffix.lower()!=".json" or file.stat().st_size>2_000_000:return jsonify({"ok":False,"error":"Workflow não disponível ou excede 2 MB"}),422
        wf=json.loads(file.read_text(encoding="utf-8-sig"))
        if not isinstance(wf,dict) or not 1<=len(wf)<=300 or not all(isinstance(n,dict) and isinstance(n.get("class_type"),str) and isinstance(n.get("inputs"),dict) for n in wf.values()):
            return jsonify({"ok":False,"error":"Arquivo não é workflow API; exporte formato API no ComfyUI"}),422
        targets=[n for n in wf.values() if n["class_type"]=="CLIPTextEncode" and isinstance(n["inputs"].get("text"),str)]
        if not targets:return jsonify({"ok":False,"error":"Workflow sem CLIPTextEncode simples: abra VÍDEO & WORKFLOWS e ajuste o prompt manualmente; não modificamos nós desconhecidos"}),422
        targets[0]["inputs"]["text"]=prompt
        if len(targets)>1 and isinstance(data.get("negative"),str):targets[1]["inputs"]["text"]=data["negative"][:3000]
        if not http_json(COMFY_URL+"/system_stats",3):return jsonify({"ok":False,"error":"ComfyUI API não respondeu"}),503
        result=post_json(COMFY_URL+"/prompt",{"prompt":wf,"client_id":"aurion-image-"+uuid.uuid4().hex},25)
        if not isinstance(result,dict) or not result.get("prompt_id"):
            return jsonify({"ok":False,"error":"ComfyUI rejeitou o workflow","node_errors":result.get("node_errors",{}) if isinstance(result,dict) else {}}),422
        log("Imagem via workflow selecionado: "+str(result["prompt_id"]))
        return jsonify({"ok":True,"prompt_id":result["prompt_id"],"workflow":file.name})
    except urllib.error.HTTPError as exc:
        detail=exc.read(12000).decode("utf-8",errors="replace")
        return jsonify({"ok":False,"error":"ComfyUI HTTP "+str(exc.code),"detail":detail[:6000]}),502
    except (OSError,ValueError,TypeError) as exc:return jsonify({"ok":False,"error":type(exc).__name__+": "+str(exc)[:250]}),422

@app.get("/api/one/workflow/<pid>")
def workflow_status(pid):
    if not all(c in "0123456789abcdef-" for c in pid.lower()) or len(pid)>60:return jsonify({"error":"ID inválido"}),400
    return jsonify({"ok":True,**image_progress(pid)})
@app.get("/api/one/source")
def source_info():
    p=Path(__file__).resolve();raw=p.read_bytes()
    return jsonify({"ok":True,"path":str(p),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw),"backup_dir":str(PATCH_DIR)})
@app.post("/api/one/source/preview")
def source_preview():
    data=request.get_json(silent=True) or {};new=data.get("source","")
    if not isinstance(new,str) or len(new.strip())<1000 or len(new)>450000:return jsonify({"ok":False,"error":"Proposta vazia ou incompleta: não é permitido apagar o painel."}),400
    try:compile(new,"AURION_ONE.py","exec")
    except SyntaxError as exc:return jsonify({"ok":False,"error":str(exc)}),422
    old=Path(__file__).read_text(encoding="utf-8")
    diff="".join(list(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile="atual",tofile="proposta"))[:300])
    return jsonify({"ok":True,"diff":diff,"sha256_atual":hashlib.sha256(old.encode()).hexdigest(),"note":"Prévia somente. Não executa nem substitui o painel."})
@app.post("/api/one/source/stage")
def source_stage():
    data=request.get_json(silent=True) or {};new=data.get("source","");expected=data.get("sha256_atual","")
    if not isinstance(new,str) or not 1000<=len(new.strip())<=450000:return jsonify({"error":"Proposta vazia ou incompleta bloqueada"}),400
    try:compile(new,"AURION_ONE.py","exec")
    except SyntaxError as exc:return jsonify({"error":str(exc)}),422
    p=Path(__file__).resolve();original=p.read_bytes()
    if hashlib.sha256(original).hexdigest()!=expected:return jsonify({"error":"Versão mudou. Refaça a prévia."}),409
    stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
    backup=PATCH_DIR/("AURION_ONE_"+stamp+"_"+uuid.uuid4().hex[:6]+".py")
    staged=PATCH_DIR/("PROPOSTA_"+stamp+"_"+uuid.uuid4().hex[:6]+".py")
    backup.write_bytes(original);staged.write_text(new,encoding="utf-8")
    log("Proposta salva sem aplicar; backup: "+backup.name)
    return jsonify({"ok":True,"backup":str(backup),"proposta":str(staged),"note":"Não aplicado ao processo atual. Teste a proposta separadamente; aplicação automática desativada."})

# ---------- PONTE DE DESCOBERTA: arquivos encontrados vs. APIs que realmente os carregam ----------
def _model_category(path):
    parts=[x.lower() for x in path.parts]
    for kind in ("checkpoints","diffusion_models","unet","loras","vae","text_encoders","controlnet","upscale_models","embeddings"):
        if kind in parts:return "diffusion_models" if kind=="unet" else kind
    return "não classificado"

def _discovered_models():
    try:
        report=json.loads(SCAN_FILE.read_text(encoding="utf-8"))
        return [Path(x["path"]) for x in report.get("found",[]) if isinstance(x,dict) and x.get("kind")=="models" and isinstance(x.get("path"),str)][:2500]
    except (OSError,ValueError,TypeError,KeyError):return []

@app.get("/api/one/models/bridge")
def models_bridge():
    obj=http_json(COMFY_URL+"/object_info",8)
    registered={}
    if isinstance(obj,dict):
        for cat,node in (("checkpoints","CheckpointLoaderSimple"),("diffusion_models","UNETLoader"),("loras","LoraLoader"),("vae","VAELoader"),("controlnet","ControlNetLoader"),("upscale_models","UpscaleModelLoader")):
            try:
                required=obj[node]["input"]["required"]
                key={"checkpoints":"ckpt_name","diffusion_models":"unet_name","loras":"lora_name","vae":"vae_name","controlnet":"control_net_name","upscale_models":"model_name"}[cat]
                registered[cat]=required[key][0]
            except (KeyError,IndexError,TypeError):registered[cat]=[]
    discovered=[]
    for p in _discovered_models():
        cat=_model_category(p)
        seen=registered.get(cat,[])
        discovered.append({"name":p.name,"path":str(p),"category":cat,"exists":p.is_file(),"recognized_by_comfy":p.name in seen if cat in registered else None,"note":"GGUF exige carregador compatível" if p.suffix.lower()==".gguf" else ""})
    return jsonify({"ok":True,"comfy_online":isinstance(obj,dict),"ollama_models":ollama_models(),"comfy_registered":registered,"discovered":discovered,"count":len(discovered),"note":"Descoberta não instala nós nem registra modelo. Confira diretórios e reinicie ComfyUI somente depois de configurar caminhos."})

@app.post("/api/one/models/prepare-paths")
def prepare_model_paths():
    paths={}; excluded=[]
    for p in _discovered_models():
        if not p.is_file():continue
        if p.suffix.lower()==".gguf":excluded.append(p.name+" (requer loader) ");continue
        cat=_model_category(p)
        if cat=="não classificado":excluded.append(p.name+" (categoria desconhecida)");continue
        # extra_model_paths_config utiliza base_path como diretório-pai das categorias.
        parts=list(p.parts);i=next((i for i,x in enumerate(parts) if x.lower()==cat or (cat=="diffusion_models" and x.lower()=="unet")),-1)
        if i<1:continue
        parent=str(Path(*parts[:i]));subdir=parts[i]
        paths.setdefault(parent,set()).add((cat,subdir))
    lines=["# GERADO PELO AURION ONE; NÃO ALTERA COMFYUI AUTOMATICAMENTE"]
    for i,(parent,cats) in enumerate(sorted(paths.items()),1):
        lines.append("aurion_%02d:"%i)
        lines.append("  base_path: "+json.dumps(parent,ensure_ascii=False))
        for cat,subdir in sorted(cats):lines.append("  "+cat+": "+json.dumps(subdir,ensure_ascii=False))
    dest=ROOT/"config"/"extra_model_paths_aurion.yaml"
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text("\n".join(lines)+"\n",encoding="utf-8")
    return jsonify({"ok":True,"path":str(dest),"bases":len(paths),"excluded":excluded[:40],"message":"Config preparado, NÃO aplicado. Revise no painel e configure o ComfyUI antes de reiniciar."})

def _registry_programs():
    """Somente LEITURA de entradas App Paths do Windows; sem execução ou busca recursiva."""
    found={}
    if os.name!="nt":return found
    try:import winreg
    except ImportError:return found
    for kind,names in APP_EXES.items():
        for exe in sorted(names):
            keypath="SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\"+exe
            for hive in (winreg.HKEY_CURRENT_USER,winreg.HKEY_LOCAL_MACHINE):
                try:
                    with winreg.OpenKey(hive,keypath) as key:raw=winreg.QueryValueEx(key,None)[0]
                    path=Path(os.path.expandvars(str(raw)).strip('"'))
                    if path.is_file() and path.name.lower() in names:found[kind]=str(path);break
                except (OSError,ValueError,TypeError):pass
            if kind in found:break
    return found

@app.get("/api/one/programs")
def programs():
    settings=load_settings().get("paths",{})
    discovered={}
    try:
        report=json.loads(SCAN_FILE.read_text(encoding="utf-8"))
        for x in report.get("found",[]):
            if isinstance(x,dict) and x.get("kind")=="program" and isinstance(x.get("path"),str):
                file=Path(x["path"]);kind=APP_EXE_TO_KIND.get(file.name.lower())
                if kind and file.is_file():discovered.setdefault(kind,str(file))
    except (OSError,ValueError,TypeError):pass
    result={};registry=_registry_programs()
    for kind,names in APP_EXES.items():
        configured=settings.get(kind,"")
        valid_config=bool(configured and Path(configured).is_file() and Path(configured).name.lower() in names)
        path=configured if valid_config else discovered.get(kind) or registry.get(kind,"")
        origin="configuração" if valid_config else "scan" if discovered.get(kind) else "registro Windows" if registry.get(kind) else "não localizado"
        result[kind]={"path":path,"exists":bool(path and Path(path).is_file()),"configured":valid_config,"source":origin}
    for kind in ("ollama","comfy"):
        result[kind]={"path":settings.get(kind,""),"exists":bool(settings.get(kind) and Path(settings[kind]).exists()),"configured":bool(settings.get(kind)),"source":"configuração"}
    return jsonify({"ok":True,"programs":result,"note":"Abertura apenas com clique explícito. Nenhuma execução automática."})

@app.post("/api/one/programs/open")
def program_open():
    kind=str((request.get_json(silent=True) or {}).get("program",""))
    if kind not in APP_EXES:return jsonify({"error":"Use a aba Ligações para iniciar Ollama ou ComfyUI; este botão só abre programas gráficos conhecidos."}),400
    paths=load_settings().get("paths",{})
    configured=paths.get(kind,"")
    path=Path(configured) if configured else None
    if not path or not path.is_file():
        # Descoberta não é autorização automática: um clique escolhe o programa exato validado.
        result=programs().get_json()["programs"].get(kind,{})
        path=Path(result.get("path","")) if result.get("path") else None
    if not path or not path.is_file() or path.name.lower() not in APP_EXES[kind]:
        return jsonify({"error":"Executável não verificado; configure o caminho correto em Ligações"}),409
    if os.name!="nt":return jsonify({"error":"Abertura de programas gráficos disponível somente no Windows"}),409
    try:
        # O executable inicia SEM parâmetros fornecidos pelo navegador.
        subprocess.Popen([str(path)],cwd=str(path.parent),stdin=subprocess.DEVNULL,creationflags=getattr(subprocess,"CREATE_NEW_PROCESS_GROUP",0))
        log("Abertura solicitada por clique: "+kind)
        return jsonify({"ok":True,"message":"Abertura solicitada; verifique a janela do programa.","program":kind}),202
    except (OSError,ValueError) as e:return jsonify({"error":"Falha ao abrir: "+str(e)[:180]}),502

# ---------- HTML ----------
HTML = r"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AURION ONE · 2026.09.21-PALETA-FANTA</title><meta http-equiv="Cache-Control" content="no-store"><style>
:root{--bg:#050505;--side:#101010;--p:#151116;--line:#513048;--txt:#ffffff;--muted:#c5b7c6;--cyan:#38cfff;--orange:#ff7300;--ok:#4cda86;--warn:#ffd166;--bad:#ff6277}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--txt);font:14px Segoe UI,Arial,sans-serif;overflow:hidden}.app{display:flex;height:100vh}.side{width:200px;flex:none;background:var(--side);border-right:1px solid var(--line);padding:16px 10px}.brand{font-size:20px;font-weight:800;color:var(--orange)}.brand small{display:block;font-size:10px;color:var(--muted);letter-spacing:2px}.nav button{width:100%;text-align:left;margin:4px 0;padding:10px;background:transparent;border:1px solid transparent;color:var(--muted);border-radius:8px;cursor:pointer;font-weight:600}.nav button:hover,.nav button.active{background:#2c1625;border-color:var(--orange);color:var(--txt)}.main{flex:1;min-width:0;display:flex;flex-direction:column}.top{height:56px;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;padding:0 18px}.content{flex:1;overflow:auto;padding:16px}.tab{display:none}.tab.active{display:block}.card{background:var(--p);border:1px solid var(--line);border-radius:12px;padding:14px;margin-bottom:12px}.card h3{margin:0 0 10px;font-size:12px;color:var(--muted);letter-spacing:.4px}.dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:6px}.dot.on{background:var(--ok)}.dot.warn{background:var(--warn)}.dot.off{background:var(--bad)}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.node{position:absolute;width:170px;background:linear-gradient(140deg,#281525,#0e0c11);border:1px solid var(--line);border-radius:10px;padding:10px;cursor:grab;user-select:none;z-index:10}.node.dragging{z-index:100;opacity:.85;border-color:var(--orange)}.node .lbl{font-weight:700}.node .st{font-size:11px;color:var(--muted)}.port{display:inline-block;width:12px;height:12px;border-radius:50%;background:var(--orange);border:2px solid #000;cursor:crosshair;margin:2px}.port.out{background:var(--cyan)}#canvas{position:relative;height:560px;background:radial-gradient(circle at 50% 30%,#281323,#050505 70%);border:1px solid var(--line);border-radius:12px;overflow:hidden}svg{position:absolute;top:0;left:0;width:100%;height:100%;pointer-events:none}textarea,input,select{width:100%;background:#120d13;color:var(--txt);border:1px solid var(--line);border-radius:8px;padding:9px;outline:none}textarea{min-height:120px}.row{display:flex;gap:8px;align-items:center}.row>*{flex:1}button{background:#291622;border:1px solid var(--line);color:var(--txt);padding:9px 12px;border-radius:8px;cursor:pointer;font-weight:600;margin:3px}button:hover{border-color:var(--orange)}button.primary{border-color:var(--orange);background:#b94e00;color:#fff}.chatlog{height:280px;overflow:auto;background:#0a0a0a;border:1px solid var(--line);border-radius:10px;padding:10px;margin-bottom:8px}.msg{padding:8px;border-radius:8px;margin:5px 0;white-space:pre-wrap}.user{background:#1a1a1a}.agent{background:#141414;border-left:3px solid var(--orange)}.result{min-height:200px;display:flex;align-items:center;justify-content:center;text-align:center;color:var(--muted)}.bar{height:8px;background:#1a1a1a;border-radius:99px;overflow:hidden}.fill{height:100%;width:0;background:var(--orange);transition:.2s}

/* HUD PRINCIPAL: preserva a composição da referência e usa paleta configurável */
:root{--accent:#ff7300;--purple:#923de2;--hudblue:#38cfff;--panelbg:#0d1015}
body{background:repeating-linear-gradient(0deg,transparent 0 39px,#ffffff05 40px),repeating-linear-gradient(90deg,transparent 0 39px,#ffffff05 40px),#07090d!important}
.app{background:transparent!important}.side,.top,.hudcard{background:linear-gradient(145deg,#161a21,#090b10 75%)!important;border:1px solid #55402d!important;box-shadow:inset 0 0 0 1px #27202a,0 0 12px #ff730010}
.side .brand{color:#fff!important}.side button.active,.primary{background:linear-gradient(110deg,#5c260b,#ff7300)!important;color:white!important}
.hero{display:grid;grid-template-columns:1.1fr 1fr .78fr 1.1fr;gap:10px;margin-bottom:10px}.hudcard{min-width:0;padding:14px;border-radius:8px;position:relative}.hudcard:before{content:'';position:absolute;left:0;top:0;width:38px;height:2px;background:var(--accent);box-shadow:0 0 9px var(--accent)}.hudcard h3{color:#fff;letter-spacing:1px;font-size:15px;margin:3px 0 12px}.hudcard p{color:#b6bac8;font-size:12px}.hudcard button{margin:4px}.spherebox{text-align:center}.sphere{width:min(100%,230px);aspect-ratio:1;border-radius:50%;margin:5px auto;display:grid;place-items:center;cursor:pointer;border:2px solid var(--accent);background:repeating-radial-gradient(circle,#121017 0 12px,#301b13 13px 15px,#0b1018 16px 25px);box-shadow:0 0 25px #ff730055,inset 0 0 35px #ff730066;animation:orbpulse 4s ease-in-out infinite}.symbol{font-size:100px;color:#fff;text-shadow:0 0 18px var(--accent)}@keyframes orbpulse{50%{box-shadow:0 0 42px #ff730077,inset 0 0 45px #ff730088}}.spherebox h1{color:var(--accent);margin:7px 0}.operators{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:8px;margin:12px 0}.operator{padding:10px;background:#11151e;border:1px solid #513c30;border-radius:8px}.operator strong{color:var(--accent)}.operator input,.operator select{width:100%;margin-top:5px;background:#090d14;color:white;border:1px solid #5b4550;padding:6px}.bottomhud{display:grid;grid-template-columns:1.5fr 1fr 1fr;gap:10px;margin-top:10px}#hudlog{height:145px;overflow:auto;white-space:pre-wrap;color:#a6d8f4;font:12px Consolas,monospace}#resources{white-space:pre-line;line-height:1.8}.hero .card{margin:4px 0;padding:8px}.hero .card .dot{margin-right:5px}button:hover{border-color:var(--accent)!important}@media(max-width:1100px){.hero{grid-template-columns:repeat(2,minmax(0,1fr))}.operators{grid-template-columns:repeat(3,1fr)}}@media(max-width:700px){.hero,.bottomhud{grid-template-columns:1fr}.operators{grid-template-columns:repeat(2,1fr)}}

.aurionFloat{position:fixed;z-index:999;right:16px;bottom:16px;width:min(395px,95vw);max-height:76vh;border:1px solid var(--accent);border-radius:12px;background:#101117;box-shadow:0 6px 44px #000b,0 0 24px #ff73003b;overflow:hidden;color:white}.aurionFloat.expanded{width:min(660px,96vw);max-height:88vh}.floatHead{height:39px;display:flex;justify-content:space-between;align-items:center;padding:3px 8px;background:linear-gradient(100deg,#371b14,#222133);cursor:move;user-select:none}.floatHead button{margin:0 2px;padding:3px 10px}.floatLog{height:125px;overflow-y:auto;white-space:pre-wrap;background:#07090d;border:1px solid #513048;margin:8px 0;padding:8px;font-size:12px}.aurionFloat.expanded .floatLog{height:280px}#floatBody{padding:8px}#floatBubble{position:fixed;bottom:14px;right:14px;z-index:998;background:var(--accent);display:none}.schoolPair{display:flex;gap:10px;align-items:center;border:1px solid #504055;border-radius:8px;margin:8px 0;padding:8px}.schoolPair img{width:140px;max-height:110px;object-fit:contain;border:1px solid #403048}.schoolPair small{display:block;color:#c4b9c9}.metric{min-width:120px;flex:1;background:#1c1620;border:1px solid #63452f;padding:10px;border-radius:7px}.metric strong{display:block;font-size:22px;color:var(--accent)}
</style></head><body><div class="app"><aside class="side"><div class="brand">◈ AURION ONE<small>EVOLUTION CORE · 2026.09.21</small></div><div class="nav">
<button class="active" onclick="tab('home',this)">PAINEL</button>
<button onclick="tab('conn',this)">CONEXOES</button>
<button onclick="tab('discovery',this)">SCAN GERAL & RASTROS</button><button onclick="tab('visual',this)">ESFERA & VISUAL</button><button onclick="tab('integrations',this)">LIGAÇÕES & DISPOSITIVOS</button><button onclick="tab('library',this)">SKILLS & BIBLIOTECA</button>
<button onclick="tab('central',this)">+ CENTRAL & @</button><button onclick="tab('bridge',this);loadBridge()">MODELOS · ENCAIXE REAL</button><button onclick="tab('programas',this);loadPrograms()">PROGRAMAS & LOGIN</button><button onclick="tab('knowledge',this)">BÍBLIA & REUNIÕES</button><button onclick="tab('video',this)">VÍDEO & WORKFLOWS</button><button onclick="tab('marketing',this)">COR & MARKETING</button><button onclick="tab('editor',this)">EDITOR PY SEGURO</button><button onclick="tab('spaces',this)">ESPACOS</button><button onclick="tab('library',this);libraryLoad()">BIBLIOTECA</button><button onclick="tab('favorites',this);favLoad()">FAVORITOS & ESTUDOS</button><button onclick="tab('poco',this)">POCO · CONEXÃO</button><button onclick="tab('band',this)">MI BAND · CONEXÃO</button>
<button onclick="tab('school',this);schoolLoad()">ESCOLA · MAPA & SKILLS</button><button onclick="tab('sessions',this);studyLoad()">ESTUDO · RELÓGIO</button>
<button onclick="tab('chat',this)">AGENTE</button>
<button onclick="tab('image',this)">GERAR IMAGEM</button><button onclick="window.location.href='/t8i'">T8I · RAW / CR3</button><button onclick="tab('comfy',this)">COMFYUI REAL</button><button onclick="tab('manager',this)">MANAGER / SCAN</button>
</div></aside><main class="main"><header class="top"><div class="title">AURION ONE</div><div class="topright" id="global">Carregando...</div></header><div class="content">
<section id="school" class="tab"><div class="card"><h3>ESCOLA · INSPEÇÃO DE MÓDULOS, VISUAL E SKILLS</h3><p>Conferência limitada dos diretórios conhecidos. Imagem parecida com um TXT/PY é hipótese, nunca fusão automática. ADAPTA protegida.</p><button onclick="schoolLoad(true)">RECONFERIR PASTAS E REFERÊNCIAS</button><div class="row" id="schoolMetrics"></div><div class="bar"><div id="schoolBar" style="width:0%"></div></div><div id="schoolPairs"></div><h3>ESFERA HISTÓRICA · REFERÊNCIA ORIGINAL</h3><div class="schoolPair"><img src="/assets/Mesa_de_Operacao_REAL_AURION_v2.png" loading="lazy" alt="Esfera histórica AURION"><div><b>Mesa_de_Operacao_REAL_AURION_v2.png</b><small>Referência visual localizada no Drive autorizado; reproduzida como referência, não como status ativo.</small></div></div><h3>SKILLS · LOCALIZADAS, NÃO EXECUTADAS</h3><div id="schoolSkills"></div><pre id="schoolResult" style="white-space:pre-wrap;max-height:300px;overflow:auto"></pre><h3>DISPOSITIVOS E PROGRAMAS</h3><div id="schoolDevices"></div></div></section>
<section id="sessions" class="tab"><div class="card"><h3>ESTUDOS · RELÓGIO & DIÁRIO</h3><p>Abra o curso por aqui para registrar a primeira visita e iniciar uma sessão. A duração é registrada até você finalizar. Plataformas externas não fornecem conclusão automaticamente sem integração autorizada.</p><div class="hero"><div class="hudcard"><h3>SESSÃO ATIVA</h3><div style="font-size:28px;color:var(--accent)" id="studyClock">00:00:00</div><small id="studyActive">Nenhuma sessão iniciada</small></div><div class="hudcard"><h3>SESSÕES FINALIZADAS</h3><strong id="studyCount" style="font-size:28px">0</strong></div><div class="hudcard"><h3>TEMPO REGISTRADO</h3><strong id="studyHours" style="font-size:28px">0 h</strong></div><div class="hudcard"><h3>ORIGEM</h3><small>Relógio do painel; não mede atenção nem compra.</small></div></div><input id="studyTitle" placeholder="Curso ou livro: título" maxlength="180"><input id="studyUrl" placeholder="https://... link oficial do curso ou aula"><button class="primary" onclick="studyStart()">ABRIR CURSO E INICIAR RELÓGIO ↗</button><div class="row"><input id="studyChapter" placeholder="Módulo / capítulo / versículo"><input id="studyProgress" type="number" min="0" max="100" placeholder="Progresso informado 0–100%"></div><textarea id="studyNotes" placeholder="Anotações, técnica aprendida, data, referência" style="min-height:75px"></textarea><button onclick="studyFinish()">FINALIZAR SESSÃO E SALVAR</button><pre id="studyFeedback" style="white-space:pre-wrap"></pre><div id="studyHistory"></div></div></section>
<section id="poco" class="tab"><div class="card"><h3>POCO · CONEXÃO LOCAL</h3><p>Estado: NÃO VERIFICADO. Acesso ao telefone depende de pareamento, autorização no aparelho e integração específica. Este painel não lê mensagens, fotos ou dados do POCO automaticamente.</p><button onclick="tab('integrations')">VER CONEXÕES DISPONÍVEIS</button><pre>Diagnóstico: nenhuma API de pareamento POCO validada nesta versão.</pre></div></section><section id="band" class="tab"><div class="card"><h3>MI BAND 9 PRO · CONEXÃO</h3><p>Estado: NÃO VERIFICADO. Dados da pulseira dependem de sincronização autorizada pelo aplicativo compatível no telefone. Bluetooth detectado não comprova acesso aos dados.</p><button onclick="tab('integrations')">VER CONEXÕES DISPONÍVEIS</button><pre>Diagnóstico: nenhuma API da pulseira autenticada nesta versão.</pre></div></section><section id="home" class="tab active"><div class="hero"><div class="hudcard"><h3>◈ AURION CORE</h3><p>SISTEMA OPERACIONAL</p><div id="lights"></div><p id="bootState">Verificando serviços...</p><div class="bar"><div class="fill" id="bootFill"></div></div><button onclick="scanNow();tab('manager')">DIAGNÓSTICO</button></div><div class="hudcard spherebox"><div class="sphere" onclick="tab('chat')" title="Abrir chat do agente"><div class="symbol">◭</div></div><h1>AURION ONE</h1><p>HUMAN × AI × CREATIVE</p><button onclick="tab('chat')">CONVERSAR COM O AGENTE</button></div><div class="hudcard"><h3>RECURSOS DO SISTEMA</h3><p id="resources">Aguardando diagnóstico real...</p><button onclick="scanNow();tab('manager')">SCAN & DIAGNÓSTICO</button></div><div class="hudcard"><h3>CHAT DO AGENTE</h3><p>Ollama local • respostas reais, sem simulação</p><button onclick="tab('chat')">ABRIR CHAT & AGENTES →</button><h3>ATALHOS</h3><button onclick="tab('image')">GERAR IMAGEM</button><button onclick="tab('comfy')">COMFYUI</button></div></div><div class="hudcard"><h3>OPERADORES · STATUS E HORAS</h3><p>JSON13, DS20, GB, BB e JR são operadores. Horas e status editáveis; sem inventar presença.</p><div class="operators" id="operators"></div><button onclick="saveOperators()">SALVAR STATUS E HORAS</button><span id="operatorMessage"></span></div><div class="bottomhud"><div class="hudcard"><h3>LOG DO SISTEMA</h3><pre id="hudlog">Aguardando...</pre></div><div class="hudcard"><h3>GERAÇÃO EM TEMPO REAL</h3><p>Geração via ComfyUI disponível na aba GERAR IMAGEM, se a API e um workflow compatível estiverem disponíveis.</p><button onclick="tab('image')">ABRIR GERAÇÃO</button></div><div class="hudcard"><h3>VISÃO DO PROJETO</h3><p>IA DESIGN LAB</p><p>PROJETO INFANTIL · TOMIM (cliente, não operador)</p><p>AURION ONE · PAINEL E ECOSSISTEMA</p><button onclick="tab('spaces')">SPACES & PROJETOS</button></div></div></section>
<section id="conn" class="tab"><div class="card"><h3>CONEXOES — arraste da porta laranja (entrada) ou ciano (saida); curva elastica visual; chat e geracao usam APIs reais</h3><div class="row" style="margin-bottom:8px"><select id="nodeType"><option value="agent">Agente Ollama</option><option value="service">Servico Ollama</option><option value="comfy">ComfyUI</option><option value="action">Gerar imagem</option><option value="data">Referencia / anotacao</option></select><button onclick="addNode()">+ ADICIONAR NO</button><button onclick="resetConnections()">LIMPAR LIGACOES</button></div><small>Clique duas vezes no no para editar. Arraste da saida ciano ate a entrada laranja.</small><div id="canvas"><svg id="svg"></svg><div id="nodes"></div></div></section>
<section id="spaces" class="tab"><div class="card"><h3>ESPACOS (adicionar itens; persistido)</h3><div id="spaces"></div></div></section>
<section id="chat" class="tab"><div class="card"><h3>AGENTE (Ollama real)</h3><select id="agentModel"></select><div id="chatlog" class="chatlog"><div class="msg agent">AURION ONE: agente via Ollama.</div></div><div class="row"><input id="chatInput" placeholder="Fale com o agente..." onkeydown="if(event.key==='Enter')sendChat()"><button class="primary" onclick="sendChat()">ENVIAR</button></div></div></section>
<section id="comfy" class="tab"><div class="card"><h3>COMFYUI ORIGINAL · EDITOR COMPLETO DE WORKFLOWS</h3><p>Editor oficial incorporado: modelos, nodes, filas, referencias e Manager reais. Se o ComfyUI bloquear incorporacao, use o botao abaixo.</p><button onclick="window.open('http://127.0.0.1:8188/','_blank')">ABRIR COMFYUI</button><iframe title="ComfyUI" src="http://127.0.0.1:8188/" style="width:100%;height:72vh;border:1px solid var(--line);border-radius:10px"></iframe></div></section><section id="manager" class="tab"><div class="card"><h3>SCAN REAL, SEM MODIFICAR ARQUIVOS</h3><button onclick="scanNow()">VERIFICAR SERVICOS E MODELOS</button><pre id="scanOutput" style="white-space:pre-wrap;overflow:auto"></pre><small>Inventario HTTP dos servicos e modelos; nao e varredura integral do PC nem auto-reparo.</small></div></section><section id="image" class="tab"><div class="card"><h3>GERAR IMAGEM (ComfyUI real)</h3><p id="imgModelNotice">O gerador rápido exige checkpoint compatível; FLUX, GGUF e modelos de difusão usam workflow API próprio.</p><button onclick="loadModels()">ATUALIZAR MODELOS</button><p><b>Workflow de imagem existente (FLUX / Z-IMAGE / SDXL):</b></p><button onclick="loadImageWorkflows()">LISTAR WORKFLOWS JÁ ENCONTRADOS</button><select id="imgWorkflow"><option value="">Geração rápida por checkpoint SDXL</option></select><small>Selecionar workflow usa os nós e modelos já definidos nele; altera somente texto CLIPTextEncode simples. Outros workflows devem ser revisados no editor.</small><select id="imgCheckpoint"></select><p>Modelos de difusão reconhecidos: <span id="diffusionList">Consultando...</span></p><button onclick="tab('video');loadLocalWorkflows()">USAR WORKFLOW FLUX / Z-IMAGE / OUTRO →</button><textarea id="imgPrompt" placeholder="Prompt positivo: descreva a imagem..."></textarea><textarea id="imgNegative" placeholder="Prompt negativo (opcional)" style="min-height:60px"></textarea><div class="row"><div><label>Largura</label><input id="imgW" type="number" value="1024"></div><div><label>Altura</label><input id="imgH" type="number" value="1024"></div><div><label>Steps</label><input id="imgSteps" type="number" value="28"></div><div><label>CFG</label><input id="imgCfg" value="7"></div></div><button class="primary" onclick="generateImage()">GERAR</button><button onclick="tab('video');loadLocalWorkflows()">FLUX / Z-IMAGE · SELECIONAR WORKFLOW EXISTENTE ↗</button><div class="bar" style="margin-top:10px"><div id="imgFill" class="fill"></div></div><div id="imgResult" class="result">A imagem aparecera aqui.</div></div></section>
<section id="discovery" class="tab"><div class="card"><h3>SCAN GERAL · DISCOS E RASTROS</h3><p>Busca em segundo plano com limites explícitos. Não instala nem modifica arquivos encontrados.</p><button onclick="startDeepScan()">INICIAR SCAN GERAL</button><div id="deepStatus" style="white-space:pre-wrap;margin:12px 0">Aguardando.</div><div class="bar"><div class="fill" id="deepBar" style="width:0%"></div></div><pre id="deepResults" style="white-space:pre-wrap;overflow:auto;max-height:340px"></pre></div></section>
<section id="visual" class="tab"><div class="card"><h3>ESFERA & VISUAL · SEM REMOVER ELEMENTOS</h3><p>Personalize o representante visual do agente. Voz depende dos recursos do navegador; a esfera não possui sensores físicos.</p><div class="row"><label>Cor principal <input type="color" id="vAccent" value="#ff7300"></label><label>Roxo <input type="color" id="vPurple" value="#923de2"></label><label>Ciano técnico <input type="color" id="vCyan" value="#38cfff"></label></div><div class="row"><label>Nome da esfera <input id="vName" value="AURION"></label><label>Modelo Ollama <select id="vModel"></select></label></div><div class="row"><label>Capa (URL http/https ou caminho de referência para inventário) <input id="vCover" placeholder="Referência da capa"></label><label>Movimento <input id="vMotion" type="checkbox" checked></label></div><button onclick="saveVisual()">SALVAR VISUAL</button><button onclick="speakOrb()">TESTAR VOZ DO NAVEGADOR</button><p id="vFeedback"></p></div></section>
<section id="integrations" class="tab"><div class="card"><h3>LIGAÇÕES · SERVIÇOS REAIS E DISPOSITIVOS</h3><p>Configure executáveis encontrados no scan. Iniciar é uma ação explícita; não executa scripts desconhecidos.</p><div id="integrationFields"></div><button onclick="savePaths()">SALVAR CAMINHOS</button><button onclick="startService('ollama')">INICIAR OLLAMA</button><button onclick="startService('comfy')">INICIAR COMFYUI</button><button onclick="showIntegrations()">ATUALIZAR STATUS</button><pre id="integrationStatus" style="white-space:pre-wrap;overflow:auto;max-height:320px"></pre></div></section>
<section id="library" class="tab"><div class="card"><h3>SKILLS, WORKFLOWS E BIBLIOTECA</h3><p>Inventário dos caminhos identificados. Nenhuma skill encontrada é executada automaticamente.</p><button onclick="showLibrary()">MOSTRAR ARQUIVOS ENCONTRADOS</button><pre id="libraryResults" style="white-space:pre-wrap;overflow:auto;max-height:480px"></pre></div></section>

<section id="bridge" class="tab"><div class="card"><h3>MODELOS · ENCAIXE REAL COM COMFYUI E OLLAMA</h3><p>O scan encontra arquivos. Aqui você confere se o ComfyUI os registrou e prepara caminhos SEM sobrescrever configurações.</p><button onclick="loadBridge()">ATUALIZAR MODELOS DAS APIs</button><button onclick="preparePaths()">PREPARAR YAML DOS MODELOS ENCONTRADOS</button><button onclick="loadModels()">ATUALIZAR SELETORES DE IMAGEM E CHAT</button><p id="bridgeSummary"></p><div id="bridgeModels" class="grid2"></div><pre id="bridgeDetail" style="white-space:pre-wrap;overflow-wrap:anywhere;max-height:260px;overflow:auto"></pre></div></section>
<section id="programas" class="tab"><div class="card"><h3>PROGRAMAS REAIS E LOGIN NAS PÁGINAS OFICIAIS</h3><p>ChatGPT, Gemini e Drive NÃO permitem login dentro de iframe do painel. Abra no navegador e autentique-se diretamente no serviço; nenhuma senha entra no AURION.</p><div id="programList" class="grid2"></div><p id="programFeedback"></p><button onclick="tab('integrations')">CONFIGURAR EXECUTÁVEIS E LIGAR SERVIÇOS</button></div></section>
<section id="central" class="tab"><div class="card"><h3>+ CENTRAL · @ FERRAMENTAS</h3><p>Serviços externos exigem login no site oficial, em aba do seu navegador. O iframe não oferece login integrado. + mostra as opções; @ abre o destino escolhido.</p><div class="row"><select id="hubPick" onchange="hubChoose()"></select><button onclick="hubOpen()">ABRIR SITE / PROGRAMA</button><button onclick="hubEmbed()">EMBUTIR (SE PERMITIDO)</button><button onclick="tab('programas');loadPrograms()">PROGRAMAS E LOGIN</button></div><div class="row"><input id="hubAt" placeholder="@comfy @ollama @gpt @gemini @drive @adapta" onkeydown="if(event.key==='Enter')hubAtGo()"><button onclick="hubAtGo()">@ IR</button><button onclick="document.getElementById('hubOptions').hidden=!document.getElementById('hubOptions').hidden">+ OPÇÕES</button></div><div id="hubOptions" hidden class="grid2"></div><p id="hubFeedback"></p><iframe id="hubFrame" title="Ferramenta selecionada" style="width:100%;height:65vh;border:1px solid var(--line)" sandbox="allow-scripts allow-forms allow-same-origin allow-popups" referrerpolicy="no-referrer"></iframe><p>Visão 3D e controle de tela por agente exigem ponte de captura, permissões e testes separados. Esta versão não assiste nem controla sua tela.</p></div></section>
<section id="knowledge" class="tab"><div class="card"><h3>BÍBLIA · HISTÓRIA · REUNIÕES · LABORATÓRIO</h3><p>Localiza automaticamente TXT, Markdown e DOCX nas pastas conhecidas e no inventário. Lê DOCX sem instalar pacote extra. PDF ainda não tem extrator. Os documentos permanecem locais; só o trecho enviado por você ao chat segue ao Ollama.</p><input id="knowledgeUpload" type="file" accept=".txt,.md,.json,.py,.log,.csv,.docx"><button onclick="importKnowledge()">+ IMPORTAR DOCUMENTO</button><button onclick="listKnowledge()">ATUALIZAR BIBLIOTECA</button><select id="knowledgePick"></select><button onclick="readKnowledge()">LER AQUI</button><button onclick="askKnowledge()">@ ENVIAR TRECHO AO CHAT LOCAL</button><pre id="knowledgeText" style="white-space:pre-wrap;max-height:65vh;overflow:auto"></pre></div></section>
<section id="video" class="tab"><div class="card"><h3>GERAÇÃO DE VÍDEO · WORKFLOW API REAL</h3><p>Importe um workflow API de vídeo compatível com seus nós instalados. O painel envia ao ComfyUI, acompanha fila e mostra arquivos retornados; não inventa vídeo nem instala modelos.</p><button onclick="loadLocalWorkflows()">BUSCAR WORKFLOWS DO SCAN</button><select id="localWorkflowPick"><option value="">Selecione workflow encontrado</option></select><button onclick="readLocalWorkflow()">CARREGAR WORKFLOW LOCAL</button><input type="file" id="workflowFile" accept=".json"><button onclick="loadWorkflowFile()">+ CARREGAR WORKFLOW</button><textarea id="workflowJson" style="min-height:180px" placeholder="JSON workflow API do ComfyUI"></textarea><button onclick="submitWorkflow()">EXECUTAR WORKFLOW NO COMFYUI</button><button onclick="showCatalog()">@ MODELOS E NÓS RECONHECIDOS</button><pre id="workflowResult" style="white-space:pre-wrap;overflow:auto"></pre></div></section>
<section id="marketing" class="tab"><div class="card"><h3>TRATAMENTO DE COR · COMPOSIÇÃO · MARKETING</h3><p>Briefing e biblioteca de prompts; execução de composição depende de workflow ComfyUI ou programa instalado.</p><div class="row"><select id="marketingFormat"><option>Instagram 1080x1350</option><option>Story 1080x1920</option><option>Vídeo 1920x1080</option><option>Quadrado 1080x1080</option></select><select id="marketingTone"><option>Fanta · laranja / roxo / preto</option><option>Azul / ciano / roxo</option><option>Neutro / institucional</option></select></div><textarea id="marketingBrief" placeholder="Produto, mensagem, público, materiais e referências"></textarea><button onclick="marketingPrompt()">CRIAR BRIEFING PARA O AGENTE</button><button onclick="tab('image')">GERAR IMAGEM</button><button onclick="tab('video')">WORKFLOW VÍDEO</button><pre id="marketingOutput" style="white-space:pre-wrap"></pre></div></section>
<section id="library" class="tab"><div class="card"><h3>◈ BIBLIOTECA · CATÁLOGO CRUZADO</h3><p>Metadados de discos acessíveis; pares por nome semelhante são hipóteses, não provas. Nenhum arquivo é executado ou enviado ao Git.</p><button onclick="libraryScan()">CATALOGAR DISCO LOCAL E EXTERNO</button><button onclick="libraryLoad()">ABRIR CATÁLOGO SALVO</button><input id="libraryQuery" placeholder="Filtrar catálogo" oninput="libraryRender()"><pre id="librarySummary">Aguardando...</pre><div id="libraryItems"></div></div></section><section id="favorites" class="tab"><div class="card"><h3>FAVORITOS & ESTUDOS · INVENTÁRIO PRIVADO</h3><p>Importa marcadores Chrome/Edge/Brave, sem ler cookies, senhas ou histórico. Clique ESTUDAR AGORA para abrir o curso e iniciar o relógio; finalização é manual. Favorito não comprova compra, matrícula nem conclusão. Dados permanecem neste PC.</p><button onclick="favImport()">LOCALIZAR E IMPORTAR FAVORITOS</button><button onclick="favLoad()">ATUALIZAR LISTA</button><input id="favQuery" placeholder="Filtrar título, pasta, endereço" oninput="favRender()"><select id="favFilter" onchange="favRender()"><option value="">Todos</option><option value="curso">Cursos identificados para revisão</option><option value="outro">Outros favoritos</option></select><p id="favSummary"></p><div id="favItems"></div><pre id="favFeedback" style="white-space:pre-wrap"></pre></div></section><section id="editor" class="tab"><div class="card"><h3>EDITOR PY · BACKUP + PRÉVIA + PROPOSTA</h3><p>Não altera o PY em execução. Prévia compila sem executar; salva backup e proposta separados para teste e retorno. Base ADAPTA protegida.</p><button onclick="sourceInfo()">IDENTIFICAR VERSÃO</button><div class="card"><h3>EVOLUÇÃO · ESTUDAR PY ANTIGOS</h3><p>Busca limitada nas pastas conhecidas, compara funções, preserva a versão atual e cria uma proposta a partir de uma versão histórica selecionada. F5 reconsulta o estudo; não executa código desconhecido nem substitui o painel automaticamente.</p><button onclick="evolveStudy()">ESTUDAR VERSÕES E SKILLS</button><select id="evolveVersions" style="width:100%"><option value="">Clique em ESTUDAR VERSÕES</option></select><button onclick="evolveStage()">CRIAR NOVA VERSÃO + BACKUP</button><pre id="evolveResult" style="white-space:pre-wrap;max-height:320px;overflow:auto"></pre></div><textarea id="sourceCode" style="min-height:200px" placeholder="Cole a versão proposta do AURION_ONE.py (não ADAPTA)"></textarea><button onclick="sourcePreview()">1 · VERIFICAR E COMPARAR</button><button onclick="sourceStage()">2 · SALVAR BACKUP + PROPOSTA</button><pre id="sourceResult" style="white-space:pre-wrap;max-height:45vh;overflow:auto"></pre></div></section>
</div></main></div>
<div id="aurionFloat" class="aurionFloat"><div class="floatHead" id="floatHandle"><b>◉ AURION · AGENTE LOCAL</b><span><button onclick="floatToggle()" title="Expandir/recolher">▣</button><button onclick="floatClose()" title="Recolher">−</button></span></div><div id="floatBody"><div id="floatLog" class="floatLog">Conectando ao Ollama somente ao enviar mensagem. Ações no PC exigem autorização e integração própria.</div><div class="row"><select id="floatModel"><option value="">Detectando modelos...</option></select></div><textarea id="floatInput" placeholder="Pergunte ao seu agente Ollama" style="min-height:55px"></textarea><button class="primary" onclick="floatSend()">ENVIAR AO AGENTE</button></div></div><button id="floatBubble" onclick="floatClose()" title="Abrir agente">◉ AGENTE</button>
<script>
let STATE=null, HEALTH=null, _dragging=false, _saving=false, _linkFrom=null, _editing=false;
let LIBRARY=null;
async function libraryLoad(){const el=document.getElementById('librarySummary');try{const r=await fetch('/api/one/library');const d=await r.json();LIBRARY=d.catalog;libraryRender();if(!LIBRARY)el.textContent=d.message||'Catálogo vazio';}catch(e){el.textContent='Erro: '+e.message}}
async function libraryScan(){const el=document.getElementById('librarySummary');el.textContent='Varrendo pastas acessíveis... pode levar até 35 segundos. Aguarde.';try{const r=await fetch('/api/one/library/scan',{method:'POST'});const d=await r.json();if(!r.ok)throw Error(d.error||r.status);LIBRARY=d.catalog;libraryRender()}catch(e){el.textContent='Falha: '+e.message}}
function libraryRender(){const el=document.getElementById('librarySummary'),box=document.getElementById('libraryItems');if(!LIBRARY){box.textContent='';return}const q=document.getElementById('libraryQuery').value.toLowerCase();el.textContent=JSON.stringify({examinados:LIBRARY.checked,catalogados:LIBRARY.files.length,pastas:LIBRARY.folders,categorias:LIBRARY.counts,assuntos:LIBRARY.subjects,por_mes:LIBRARY.months,por_origem:LIBRARY.sources,nomes_repetidos:(LIBRARY.duplicates||[]).length,cruzamentos:LIBRARY.crossings.length,limite_atingido:LIBRARY.limited,erros:LIBRARY.errors,escopo:LIBRARY.scope},null,2);const matched=LIBRARY.files.filter(x=>(x.name+' '+x.path+' '+x.category+' '+(x.subjects||[]).join(' ')+' '+(x.date||'')).toLowerCase().includes(q)).slice(0,180);const crosses=LIBRARY.crossings.filter(x=>(x.key+' '+x.files.join(' ')).toLowerCase().includes(q)).slice(0,80);box.innerHTML='<h3>CRUZAMENTOS · '+crosses.length+' exibidos</h3>'+crosses.map(x=>'<div class="card"><b>'+esc(x.key)+'</b><br>'+esc(x.categories.join(' · '))+'<br><small>'+esc(x.evidence)+'</small><pre>'+esc(x.files.join('\n'))+'</pre></div>').join('')+'<h3>ARQUIVOS · '+matched.length+' exibidos</h3>'+matched.map(x=>'<div class="card">'+esc(x.category+' · '+x.name)+'<br><small>'+esc((x.date||'sem data')+' · '+(x.subjects||[]).join(', '))+'</small><br><small>'+esc(x.path)+'</small></div>').join('')}
async function scanNow(){let el=document.getElementById("scanOutput");el.textContent="Consultando APIs e relatório de arquivos...";try{let r=await fetch("/api/one/diagnostico",{cache:"no-store"});let d=await r.json();let b=await(await fetch('/api/one/models/bridge',{cache:'no-store'})).json();el.textContent=JSON.stringify({diagnostico:d,modelos:{comfy_online:b.comfy_online,registrados:b.comfy_registered,arquivos_encontrados:b.count,ollama:b.ollama_models},proximo_passo:b.count?'Abra MODELOS · ENCAIXE REAL para ver arquivos e categorias':'Abra SCAN GERAL & RASTROS e execute a varredura para localizar arquivos'},null,2)}catch(e){el.textContent="Falha: "+e}}
function tab(id,b){document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));document.getElementById(id).classList.add('active');document.querySelectorAll('.nav button').forEach(x=>x.classList.remove('active'));if(b)b.classList.add('active');}
function esc(v){return String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]))}
function dotClass(s){if(s==='ONLINE')return 'on';if(s==='PORT')return 'warn';return 'off'}
async function refresh(){
  if(_dragging||_saving||_editing) return;
  try{
    const s=await (await fetch('/api/one/state',{cache:'no-store'})).json(); STATE=s.state;
    const h=await (await fetch('/api/one/health',{cache:'no-store'})).json(); HEALTH=h.health;
    renderLights(); renderNodes(); renderSpaces(); loadModels();
    document.getElementById('global').textContent='F5 preserva estado.';
  }catch(e){document.getElementById('global').textContent='Erro: '+e;}
}
function renderLights(){const el=document.getElementById('lights');if(!HEALTH)return;const map={painel:'PAINEL',comfy:'COMFYUI',ollama:'OLLAMA',webui:'WEBUI'};el.innerHTML=Object.entries(map).map(([k,l])=>`<div class="card"><span class="dot ${dotClass(HEALTH[k])}"></span>${l}<br><small>${HEALTH[k]}</small></div>`).join('');}
function nodePos(id){const n=STATE.nodes.find(x=>x.id===id);return n?{x:n.x+85,y:n.y+30}:null;}
function drawLines(){
  const svg=document.getElementById('svg'); if(!STATE) return; svg.innerHTML='';
  STATE.connections.forEach(c=>{
    const a=nodePos(c[0]), b=nodePos(c[2]); if(!a||!b) return;
    const dx=Math.max(40,Math.abs(b.x-a.x)*0.5);
    const p=document.createElementNS('http://www.w3.org/2000/svg','path');
    p.setAttribute('d',`M ${a.x} ${a.y} C ${a.x+dx} ${a.y}, ${b.x-dx} ${b.y}, ${b.x} ${b.y}`);
    p.setAttribute('stroke',c[1]==='out'?'#55c8ff':'#FF7300'); p.setAttribute('stroke-width','3'); p.setAttribute('fill','none');
    svg.appendChild(p);
  });
}
function renderNodes(){
  const wrap=document.getElementById('nodes'),svg=document.getElementById('svg'); if(!STATE) return;
  wrap.innerHTML=''; svg.innerHTML='';
  STATE.nodes.forEach(n=>{
    const d=document.createElement('div'); d.className='node'; d.style.left=n.x+'px'; d.style.top=n.y+'px';
    let ports='';
    (n.inputs||[]).forEach(p=>ports+=`<span class="port" data-node="${n.id}" data-port="${p}" title="entrada ${p}"></span>`);
    ports+='<div class="lbl">'+esc(n.label)+'</div><div class="st">'+esc(n.kind)+(n.model?' · '+esc(n.model):'')+(n.port?' · '+n.port:'')+'</div>';
    (n.outputs||[]).forEach(p=>ports+=`<span class="port out" data-node="${n.id}" data-port="${p}" title="saida ${p}"></span>`);
    d.innerHTML=ports;
    d.addEventListener('dblclick',e=>{if(!e.target.classList.contains('port'))editNode(n)});
    d.addEventListener('mousedown',e=>{
      if(e.target.classList.contains('port') || _editing) return;
      _dragging=true; d.classList.add('dragging');
      const sx=e.clientX-n.x, sy=e.clientY-n.y;
      const mv=ev=>{n.x=ev.clientX-sx; n.y=ev.clientY-sy; d.style.left=n.x+'px'; d.style.top=n.y+'px'; drawLines();};
      const up=async()=>{document.removeEventListener('mousemove',mv);document.removeEventListener('mouseup',up);d.classList.remove('dragging');await saveNow();_dragging=false;};
      document.addEventListener('mousemove',mv); document.addEventListener('mouseup',up);
    });
    d.querySelectorAll('.port').forEach(p=>{
      p.addEventListener('mousedown',e=>{e.stopPropagation(); _linkFrom={node:p.dataset.node,port:p.dataset.port,isOut:p.classList.contains('out')};});
      p.addEventListener('mouseup',e=>{
        e.stopPropagation();
        if(_linkFrom && (_linkFrom.node!==p.dataset.node) && (_linkFrom.isOut!==p.classList.contains('out'))){
          const a=_linkFrom, b={node:p.dataset.node,port:p.dataset.port};
          const conn=(a.isOut?[a.node,a.port,b.node,b.port]:[b.node,b.port,a.node,a.port]);
          STATE.connections=STATE.connections.filter(c=>!(c[0]===conn[0]&&c[2]===conn[2]));
          if(!STATE.connections.some(c=>JSON.stringify(c)===JSON.stringify(conn)))STATE.connections.push(conn); drawLines(); saveNow();
        }
        _linkFrom=null;
      });
    });
    wrap.appendChild(d);
  });
  drawLines();
}
function addNode(){
 if(!STATE)return;
 const kind=document.getElementById('nodeType').value;
 const defaults={agent:['Agente Ollama',['in'],[]],service:['Ollama',[],['out']],comfy:['ComfyUI',[],['out']],action:['Gerar imagem',['in'],[]],data:['Referencia',[],['out']]};
 const [label,inputs,outputs]=defaults[kind];
 const id='node_'+(globalThis.crypto?.randomUUID?.()||String(Date.now())+Math.random().toString(16).slice(2));
 STATE.nodes.push({id,label,kind,x:80+(STATE.nodes.length%5)*45,y:80+(STATE.nodes.length%5)*55,port:kind==='service'?11434:kind==='comfy'?8188:null,inputs,outputs,model:''});
 renderNodes();saveNow();
}
function editNode(n){
 _editing=true;
 const label=prompt('Nome do no:',n.label);
 if(label!==null&&label.trim())n.label=label.trim().slice(0,100);
 if(n.kind==='agent'){
   const models=Array.from(document.getElementById('agentModel').options).map(o=>o.value).filter(Boolean);
   const model=prompt('Modelo Ollama instalado (opcoes: '+(models.join(', ')||'nenhum detectado')+'):',n.model||models[0]||'');
   if(model!==null){if(model&&!models.includes(model))alert('Modelo nao confirmado no Ollama; nao sera selecionado.');else n.model=model;}
 }
 if(n.kind==='data'){
   const ref=prompt('Referencia / anotacao (nao envia arquivos automaticamente):',n.reference||'');
   if(ref!==null)n.reference=ref.slice(0,1000);
 }
 if(confirm('Excluir este no? OK exclui; Cancelar mantem.')){
   STATE.nodes=STATE.nodes.filter(x=>x.id!==n.id);
   STATE.connections=STATE.connections.filter(c=>c[0]!==n.id&&c[2]!==n.id);
 }
 renderNodes();saveNow().finally(()=>{_editing=false});
}
function resetConnections(){if(!STATE||!confirm('Remover somente as ligacoes visuais?'))return;STATE.connections=[];drawLines();saveNow()}
function renderSpaces(){
  const el=document.getElementById('spaces'); if(!STATE) return;
  el.innerHTML=STATE.spaces.map(s=>`<div class="card"><h3>${esc(s.name)}</h3>${(s.items||[]).map(i=>`<div>• ${esc(i)}</div>`).join('')||'<small>vazio</small>'}<div class="row"><input id="in_${s.id}" placeholder="adicionar item..."><button onclick="addItem('${s.id}')">+</button></div></div>`).join('');
}
async function addItem(sid){const i=document.getElementById('in_'+sid);const v=i.value.trim();if(!v)return;await fetch('/api/one/space',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({space:sid,item:v})});i.value='';refresh();}
async function loadModels(){
  try{
    const n=await (await fetch('/api/one/nodes',{cache:'no-store'})).json();
    const om=n.ollama_models||[];
    document.getElementById('ollamaList').textContent=om.length?om.join('\n'):'Nenhum modelo Ollama instalado.';
    const s=document.getElementById('agentModel'); const selected=s.value; s.innerHTML=om.length?om.map(m=>`<option value="${esc(m)}">${esc(m)}</option>`).join(''):'<option value="">Nenhum modelo</option>'; if(om.includes(selected))s.value=selected;else {const preferred=window.AURION_SELECTED_MODEL||'';if(om.includes(preferred))s.value=preferred;}
    document.getElementById("diffusionList").textContent=(n.diffusion_models||[]).join(", ")||"Nenhum modelo de difusão registrado na API consultada";const ck=document.getElementById('imgCheckpoint');const chosen=ck.value;ck.innerHTML=(n.checkpoints||[]).map(x=>`<option value="${esc(x)}">${esc(x)}</option>`).join('')||'<option value="">Nenhum checkpoint</option>';if((n.checkpoints||[]).includes(chosen))ck.value=chosen;
  }catch(e){document.getElementById('imgResult').textContent='Falha ao consultar modelos: '+e.message;}
}
async function saveNow(){if(!STATE)return;_saving=true;try{const r=await fetch('/api/one/state',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(STATE)});const d=await r.json();document.getElementById('global').textContent=(r.ok&&d.ok)?'Salvo em disco.':'ERRO ao salvar: '+(d.error||r.status);}catch(e){document.getElementById('global').textContent='ERRO: '+e;}finally{_saving=false}}
async function sendChat(){
  const i=document.getElementById('chatInput'),m=i.value.trim(); if(!m) return;
  const b=document.getElementById('chatlog'); b.innerHTML+=`<div class="msg user">VOCE<br>${esc(m)}</div>`; i.value='';
  b.innerHTML+=`<div class="msg agent">AURION: processando...</div>`; b.scrollTop=b.scrollHeight;
  try{
    const r=await fetch('/api/one/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:m,model:document.getElementById('agentModel').value})});
    const d=await r.json(); b.lastElementChild.remove();
    if(!r.ok)throw Error(d.reply||d.error||('HTTP '+r.status));
    b.innerHTML+=`<div class="msg agent"><b>AURION · ${esc(d.model||'agente')}</b><br>${esc(d.reply)}</div>`;
  }catch(e){b.lastElementChild.remove(); b.innerHTML+=`<div class="msg agent">ERRO: ${esc(e)}</div>`;}
  b.scrollTop=b.scrollHeight;
}
async function loadImageWorkflows(){const sel=document.getElementById('imgWorkflow');try{let r=await fetch('/api/one/workflows/local');let d=await r.json();sel.replaceChildren();let opt=document.createElement('option');opt.value='';opt.textContent='Geração rápida por checkpoint SDXL';sel.append(opt);for(let x of (d.workflows||[])){let o=document.createElement('option');o.value=x.path;o.textContent=x.name;sel.append(o)}document.getElementById('imgResult').textContent=(d.workflows||[]).length+' workflows catalogados; selecione um fluxo API de imagem.'}catch(e){document.getElementById('imgResult').textContent='Falha ao listar workflows: '+e}}
async function generateImage(){
  const p=document.getElementById('imgPrompt').value.trim(); if(!p){alert('Digite um prompt');return;}
  document.getElementById('imgResult').textContent='Enviando...'; document.getElementById('imgFill').style.width='5%';
  try{
    const selected=document.getElementById('imgWorkflow').value;const payload=selected?{path:selected,prompt:p,negative:document.getElementById('imgNegative').value}:{prompt:p,checkpoint:document.getElementById('imgCheckpoint').value,width:document.getElementById('imgW').value,height:document.getElementById('imgH').value,steps:document.getElementById('imgSteps').value,cfg:document.getElementById('imgCfg').value,negative:document.getElementById('imgNegative').value};
    const r=await fetch(selected?'/api/one/image/workflow':'/api/one/image',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    const d=await r.json(); if(!d.ok){document.getElementById('imgFill').style.width='0%';document.getElementById('imgResult').textContent='ERRO: '+(d.message||d.error||'HTTP '+r.status)+' '+(d.detail||JSON.stringify(d.node_errors||{}))+' — confira MODELOS · ENCAIXE REAL e COMFYUI REAL.';return;}
    pollImage(d.prompt_id);
  }catch(e){document.getElementById('imgResult').textContent='ERRO: '+e;}
}
async function pollImage(pid){
  for(let i=0;i<120;i++){
    try{
      const d=await (await fetch('/api/one/image/'+pid,{cache:'no-store'})).json();
      if(d.status==='erro'||d.status==='concluido_sem_imagem'){
        document.getElementById('imgResult').textContent='A geração terminou sem imagem disponível: '+(d.message||d.status);return;
      }
      if(d.status==='concluido'&&d.images.length){
        document.getElementById('imgFill').style.width='100%';
        const img=d.images[0]; const q=new URLSearchParams({filename:img.filename,subfolder:img.subfolder||'',type:img.type||'output'});
        document.getElementById('imgResult').innerHTML=`<img src="http://127.0.0.1:8188/view?${q.toString()}" style="max-width:100%;border-radius:10px">`;
        return;
      }
      document.getElementById('imgFill').style.width='12%'; document.getElementById('imgResult').textContent='ComfyUI: '+d.status+' (progresso exato indisponivel nesta API)';
    }catch(e){}
    await new Promise(r=>setTimeout(r,1500));
  }
  document.getElementById('imgResult').textContent='Tempo esgotado; veja o ComfyUI.';
}
async function bootRefresh(){try{const d=await (await fetch("/api/one/boot",{cache:"no-store"})).json();document.getElementById("bootState").textContent=d.step+" · "+d.done+"/"+d.total;document.getElementById("bootFill").style.width=(100*d.done/d.total)+"%";}catch(e){}}

function renderOperators(){
 const list=(STATE&&STATE.operators)||[{name:'JSON13'},{name:'DS20'},{name:'GB'},{name:'BB'},{name:'JR'}];
 document.getElementById('operators').innerHTML=list.map((o,i)=>`<div class="operator"><strong>${esc(o.name)}</strong><label>STATUS<input id="opstatus${i}" value="${esc(o.status||'NÃO VERIFICADO')}"></label><label>HORAS<input type="number" min="0" step="0.1" id="ophours${i}" placeholder="Não informado" value="${o.hours==null?'':esc(o.hours)}"></label></div>`).join('');
}
async function saveOperators(){let list=['JSON13','DS20','GB','BB','JR'].map((name,i)=>({name,status:document.getElementById('opstatus'+i).value,hours:document.getElementById('ophours'+i).value}));try{let r=await fetch('/api/one/operators',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({operators:list})});let d=await r.json();if(!r.ok)throw Error(d.error||r.status);STATE.operators=d.operators;document.getElementById('operatorMessage').textContent=' Salvo em disco.'}catch(e){document.getElementById('operatorMessage').textContent=' Erro: '+e.message}}
async function updateHud(){try{let r=await fetch('/api/one/diagnostico',{cache:'no-store'}),d=await r.json();document.getElementById('resources').textContent='PAINEL: ativo\nCOMFYUI: '+(d.health.comfy||'verificando')+'\nOLLAMA: '+(d.health.ollama||'verificando')+'\nMODELOS OLLAMA: '+(d.modelos_ollama||[]).length+'\nCHECKPOINTS COMFY: '+(d.checkpoints_comfy||[]).length;let b=await(await fetch('/api/one/boot',{cache:'no-store'})).json();document.getElementById('hudlog').textContent=(b.details||[]).map(x=>`${x.ok?'OK':'PENDENTE'} · ${x.item}`).join('\n')+'\n'+b.step}catch(e){document.getElementById('hudlog').textContent='Diagnóstico indisponível: '+e.message}}

refresh().then(()=>renderOperators());bootRefresh();updateHud();setInterval(()=>{refresh().then(()=>{if(!document.activeElement.closest?.(".operator"))renderOperators()});updateHud()},12000);setInterval(bootRefresh,1000);

// Expansões aditivas — preservam HUD, nós, Spaces, chat e operadores.
const _newKinds=['ollama','comfy','python','git','base','models','skill','workflow','launcher','history','photoshop','after_effects','cinema4d','unreal','blender','davinci','lmstudio','obs'];
async function startDeepScan(){let r=await fetch('/api/one/scan/start',{method:'POST'});let d=await r.json();document.getElementById('deepStatus').textContent=d.started?'Scan iniciado.':'Scan já em andamento.';}
let LAST_SCAN_IMPORTED='';
async function pollDeepScan(){try{let d=await(await fetch('/api/one/scan/progress',{cache:'no-store'})).json();document.getElementById('deepStatus').textContent=d.phase+'\nPastas: '+d.folders+' · Arquivos: '+d.files+' · Vestígios exibidos: '+d.found.length+(d.truncated?' · LIMITE ATINGIDO':'')+'\n'+(d.report||'');document.getElementById('deepBar').style.width=d.finished?'100%':d.running?'48%':'0%';document.getElementById('deepResults').textContent=(d.found||[]).slice(-45).map(x=>x.kind+' · '+x.path).join('\n');
if(d.finished&&d.report&&LAST_SCAN_IMPORTED!==d.report+'#'+d.started){LAST_SCAN_IMPORTED=d.report+'#'+d.started;Promise.allSettled([loadModels(),listKnowledge(),loadBridge(),loadPrograms()]).then(()=>{document.getElementById('deepStatus').textContent+='\nCATÁLOGOS E ABAS ATUALIZADOS. Veja MODELOS · ENCAIXE REAL.'})}
}catch(e){document.getElementById('deepStatus').textContent='Falha de consulta: '+e.message}}
async function loadVisual(){try{let d=await(await fetch('/api/one/settings')).json(),s=d.settings;document.getElementById('vAccent').value=s.accent;document.getElementById('vPurple').value=s.purple;document.getElementById('vCyan').value=s.cyan;document.getElementById('vName').value=s.orb_name;document.getElementById('vCover').value=s.cover;document.getElementById('vMotion').checked=s.orb_motion;document.documentElement.style.setProperty('--accent',s.accent);document.documentElement.style.setProperty('--purple',s.purple);document.documentElement.style.setProperty('--hudblue',s.cyan);const m=await(await fetch('/api/one/integrations')).json();document.getElementById('vModel').innerHTML=(m.integrations.ollama_models||[]).map(x=>'<option>'+esc(x)+'</option>').join('');document.getElementById('vModel').value=s.selected_model||'';document.getElementById('integrationFields').innerHTML=_newKinds.map(k=>'<label style="display:block;margin:7px">'+k.toUpperCase()+' <input id="path_'+k+'" style="width:85%" placeholder="Caminho existente"></label>').join('');_newKinds.forEach(k=>document.getElementById('path_'+k).value=s.paths[k]||'');}catch(e){document.getElementById('vFeedback').textContent='Configuração indisponível: '+e.message}}
async function saveVisual(){let d={accent:document.getElementById('vAccent').value,purple:document.getElementById('vPurple').value,cyan:document.getElementById('vCyan').value,orb_name:document.getElementById('vName').value,cover:document.getElementById('vCover').value,orb_motion:document.getElementById('vMotion').checked,selected_model:document.getElementById('vModel').value};let r=await fetch('/api/one/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)});document.getElementById('vFeedback').textContent=r.ok?'Salvo em disco. F5 preserva as cores.':'Falha ao salvar: HTTP '+r.status;if(r.ok)loadVisual();}
function speakOrb(){if(!('speechSynthesis' in window)){document.getElementById('vFeedback').textContent='Voz indisponível neste navegador.';return;}let u=new SpeechSynthesisUtterance('AURION ONE. Painel disponível. Serviços em verificação.');u.lang='pt-BR';speechSynthesis.speak(u)}
async function savePaths(){let paths={};_newKinds.forEach(k=>paths[k]=document.getElementById('path_'+k).value);let r=await fetch('/api/one/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({paths})});document.getElementById('integrationStatus').textContent=r.ok?'Caminhos salvos; existência será conferida.':'Falha HTTP '+r.status;await showIntegrations()}
async function showIntegrations(){try{let d=await(await fetch('/api/one/integrations',{cache:'no-store'})).json();document.getElementById('integrationStatus').textContent=JSON.stringify(d.integrations,null,2)}catch(e){document.getElementById('integrationStatus').textContent=e.message}}
async function startService(service){let r=await fetch('/api/one/service/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({service})});let d=await r.json();document.getElementById('integrationStatus').textContent=JSON.stringify(d,null,2);setTimeout(showIntegrations,3500)}
async function showLibrary(){let r=await fetch('/api/one/scan/progress');let d=await r.json();document.getElementById('libraryResults').textContent=(d.found||[]).filter(x=>['skill','workflow','models','history'].includes(x.kind)).map(x=>x.kind+' · '+x.path).join('\n')||'Inicie o scan geral para descobrir arquivos.'}
loadVisual();pollDeepScan();setInterval(pollDeepScan,1800);

// Central aditiva: nenhum serviço externo é declarado conectado sem teste.
const HUB=[['ComfyUI local','http://127.0.0.1:8188/','comfy'],['Ollama local','http://127.0.0.1:11434/','ollama'],['Open WebUI local','http://127.0.0.1:8080/','webui'],['ChatGPT','https://chatgpt.com/','gpt'],['Gemini','https://gemini.google.com/','gemini'],['Google Drive','https://drive.google.com/','drive'],['Google','https://www.google.com/','google'],['GitHub AURION ONE','https://github.com/cleitongoy-debug/AURION-ONE','git'],['Hugging Face Spaces','https://huggingface.co/spaces','spaces'],['ADAPTA · painel local','http://127.0.0.1:5000/','adapta']];
let SOURCE_HASH='',KNOWLEDGE_TEXT='';
function hubChoose(){let i=Number(document.getElementById('hubPick').value);document.getElementById('hubFeedback').textContent=HUB[i][0]+' · conexão e login não verificados';}
function hubOpen(){let i=Number(document.getElementById('hubPick').value);let url=HUB[i][1];
  // Login funciona na página oficial, e não em iframe. Abrir pela navegação normal permite ao navegador usar sua sessão.
  let a=document.createElement('a');a.href=url;a.target='_blank';a.rel='noopener noreferrer';document.body.appendChild(a);a.click();a.remove();
  document.getElementById('hubFeedback').textContent='Abriu o destino no navegador. Faça login diretamente no serviço oficial se solicitado. Se o navegador bloquear a aba, permita pop-ups para 127.0.0.1.';
}
function hubEmbed(){let i=Number(document.getElementById('hubPick').value);document.getElementById('hubFrame').src=HUB[i][1];document.getElementById('hubFeedback').textContent='Tentativa de incorporação: se o site bloquear, use ABRIR SITE. Login não é compartilhado.';}
function hubAtGo(){let v=document.getElementById('hubAt').value.toLowerCase().trim().replace(/^@/,'');let i=HUB.findIndex(x=>x[2]===v);if(i<0){document.getElementById('hubFeedback').textContent='Atalho desconhecido. Abra + OPÇÕES.';return;}document.getElementById('hubPick').value=String(i);hubChoose();if(HUB[i][1].startsWith('https://'))hubOpen();else hubEmbed();}
function hubInit(){document.getElementById('hubPick').innerHTML=HUB.map((x,i)=>'<option value="'+i+'">'+esc(x[0])+'</option>').join('');document.getElementById('hubOptions').innerHTML=HUB.map((x,i)=>'<button onclick="document.getElementById(\'hubPick\').value='+i+';hubChoose();hubOpen()">@'+esc(x[2])+'</button>').join('');}
async function loadBridge(){let out=document.getElementById('bridgeDetail');out.textContent='Consultando ComfyUI, Ollama e relatório do scan...';try{
  let r=await fetch('/api/one/models/bridge',{cache:'no-store'});let d=await r.json();
  let recognized=d.discovered.filter(x=>x.recognized_by_comfy===true).length;
  document.getElementById('bridgeSummary').textContent='Arquivos encontrados: '+d.count+' · reconhecidos por API: '+recognized+' · ComfyUI: '+(d.comfy_online?'online':'offline')+' · Ollama: '+d.ollama_models.length+' modelos';
  document.getElementById('bridgeModels').innerHTML=d.discovered.slice(0,120).map(x=>'<div class="card"><b>'+esc(x.name)+'</b><p>'+esc(x.category)+'</p><small>'+esc(x.recognized_by_comfy===true?'REGISTRADO NA API (não carregado na GPU)':x.recognized_by_comfy===false?'ARQUIVO NÃO REGISTRADO':'SEM VALIDAÇÃO')+'</small><p style="overflow-wrap:anywhere">'+esc(x.path)+'</p></div>').join('')||'<p>Sem arquivos no último scan. Use SCAN GERAL primeiro.</p>';
  out.textContent=d.note+'\nModelos Ollama: '+d.ollama_models.join(', ')+'\nReconhecidos: '+JSON.stringify(d.comfy_registered,null,2);
}catch(e){out.textContent='Erro: '+e.message}}
async function preparePaths(){if(!confirm('Preparar arquivo de caminhos sem alterar o ComfyUI?'))return;let r=await fetch('/api/one/models/prepare-paths',{method:'POST'});let d=await r.json();document.getElementById('bridgeDetail').textContent=JSON.stringify(d,null,2);}
async function loadPrograms(){let el=document.getElementById('programList');try{let d=await(await fetch('/api/one/programs')).json();el.innerHTML=Object.entries(d.programs).map(([k,v])=>'<div class="card"><b>'+esc(k.toUpperCase())+'</b><p style="overflow-wrap:anywhere">'+esc(v.path||'Não localizado')+'</p><small>'+esc(v.exists?'LOCALIZADO · '+v.source:'NÃO LOCALIZADO')+'</small><br><button '+(v.exists&&k!=='ollama'&&k!=='comfy'?'':'disabled')+' onclick="launchProgram(\''+esc(k)+'\')">ABRIR PROGRAMA</button></div>').join('');}catch(e){el.textContent='Erro: '+e.message}}
async function launchProgram(kind){if(!confirm('Abrir '+kind+' no PC?'))return;let r=await fetch('/api/one/programs/open',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({program:kind})});let d=await r.json();document.getElementById('programFeedback').textContent=d.message||d.error||'HTTP '+r.status;}
async function listKnowledge(){let d=await(await fetch('/api/one/knowledge')).json();document.getElementById('knowledgePick').innerHTML=d.files.map(x=>'<option value="'+esc(x.path)+'">'+esc(x.name)+'</option>').join('');document.getElementById('knowledgeText').textContent=d.files.length+' documentos localizados (incluindo DOCX do scan, se encontrado). Selecione e clique LER; não precisa digitar sua Bíblia.';}
async function importKnowledge(){let f=document.getElementById('knowledgeUpload').files[0];if(!f)return;let fd=new FormData();fd.append('file',f);let r=await fetch('/api/one/knowledge/import',{method:'POST',body:fd});let d=await r.json();document.getElementById('knowledgeText').textContent=JSON.stringify(d,null,2);if(d.ok)listKnowledge();}
async function readKnowledge(){let path=document.getElementById('knowledgePick').value;if(!path)return;let d=await(await fetch('/api/one/knowledge/read',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({path})})).json();KNOWLEDGE_TEXT=d.text||'';document.getElementById('knowledgeText').textContent=(d.text||d.error||'')+(d.truncated?'\n[PRÉVIA LIMITADA; documento completo permanece intacto]':'');}
function askKnowledge(){if(!KNOWLEDGE_TEXT){alert('Leia um documento primeiro');return;}document.getElementById('chatInput').value='Estude este trecho do documento fornecido pelo operador; se faltar contexto, diga:\n'+KNOWLEDGE_TEXT.slice(0,9000);tab('chat');}
async function showCatalog(){let d=await(await fetch('/api/one/catalog')).json();document.getElementById('workflowResult').textContent=JSON.stringify(d,null,2);}
async function loadLocalWorkflows(){const pick=document.getElementById('localWorkflowPick');try{const r=await fetch('/api/one/workflows/local');const d=await r.json();pick.innerHTML='<option value="">Selecione workflow encontrado ('+(d.workflows||[]).length+')</option>'+(d.workflows||[]).map(x=>'<option value="'+esc(x.path)+'">'+esc(x.name)+'</option>').join('');document.getElementById('workflowResult').textContent=(d.workflows||[]).length+' workflows encontrados. Se não aparecerem, execute SCAN GERAL; limite atingido pode omitir arquivos.';}catch(e){document.getElementById('workflowResult').textContent='Falha ao listar workflows: '+e.message;}}
async function readLocalWorkflow(){const path=document.getElementById('localWorkflowPick').value;if(!path)return;const out=document.getElementById('workflowResult');try{const r=await fetch('/api/one/workflows/local/read',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({path})});const d=await r.json();if(!d.ok){out.textContent=d.error||'Erro';return;}document.getElementById('workflowJson').value=JSON.stringify(d.workflow,null,2);out.textContent='Workflow API carregado para revisão; execução só ocorre ao clicar EXECUTAR. '+d.path;}catch(e){out.textContent='Falha: '+e.message;}}
async function loadWorkflowFile(){let f=document.getElementById('workflowFile').files[0];if(!f)return;document.getElementById('workflowJson').value=await f.text();}
async function submitWorkflow(){let out=document.getElementById('workflowResult');try{let workflow=JSON.parse(document.getElementById('workflowJson').value);let r=await fetch('/api/one/workflow/submit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({workflow})});let d=await r.json();out.textContent=JSON.stringify(d,null,2);if(d.prompt_id){let id=d.prompt_id;let poll=setInterval(async()=>{try{let z=await(await fetch('/api/one/workflow/'+encodeURIComponent(id))).json();out.textContent=JSON.stringify(z,null,2);if(z.status==='concluido'||z.status==='erro'||z.status==='concluido_sem_imagem'){
  clearInterval(poll);if(z.status==='concluido'&&(z.images||[]).length){let img=z.images[0];let q=new URLSearchParams({filename:img.filename,subfolder:img.subfolder||'',type:img.type||'output'});out.innerHTML='<p>Imagem gerada:</p><img alt="Prévia ComfyUI" style="max-width:100%" src="http://127.0.0.1:8188/view?'+q.toString()+'">';}
  else if(z.status==='concluido'&&(z.media||[]).length){let v=z.media[0];let q=new URLSearchParams({filename:v.filename,subfolder:v.subfolder||'',type:v.type||'output'});out.innerHTML='<p>Arquivo de vídeo gerado:</p><video controls style="max-width:100%" src="http://127.0.0.1:8188/view?'+q.toString()+'"></video>';}
}}catch(e){clearInterval(poll);out.textContent=String(e)}},2500);setTimeout(()=>clearInterval(poll),180000);}}catch(e){out.textContent='JSON inválido ou erro: '+e;}}
function marketingPrompt(){let brief=document.getElementById('marketingBrief').value;let prompt='Crie uma proposta de composição e direção de arte para '+document.getElementById('marketingFormat').value+'; paleta '+document.getElementById('marketingTone').value+'; briefing: '+brief+'. Preserve personagens e referências fornecidas; detalhe luz, contraste, tipografia e camadas. Não invente arquivos existentes.';document.getElementById('marketingOutput').textContent=prompt;document.getElementById('chatInput').value=prompt;}
async function sourceInfo(){let d=await(await fetch('/api/one/source')).json();SOURCE_HASH=d.sha256;document.getElementById('sourceResult').textContent=JSON.stringify(d,null,2);}
async function sourcePreview(){let d=await(await fetch('/api/one/source/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({source:document.getElementById('sourceCode').value})})).json();SOURCE_HASH=d.sha256_atual||'';document.getElementById('sourceResult').textContent=d.diff||JSON.stringify(d,null,2);}
async function sourceStage(){if(!SOURCE_HASH){alert('Faça a prévia primeiro');return;}if(!confirm('Salvar backup e proposta separados? O painel atual não será alterado.'))return;let d=await(await fetch('/api/one/source/stage',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({source:document.getElementById('sourceCode').value,sha256_atual:SOURCE_HASH})})).json();document.getElementById('sourceResult').textContent=JSON.stringify(d,null,2);}
let EVOLVE_HASH='';
async function evolveStudy(){let out=document.getElementById('evolveResult');out.textContent='Estudando arquivos locais sem executá-los...';try{let r=await fetch('/api/one/evolve/study');let d=await r.json();if(!d.ok)throw Error(d.error);EVOLVE_HASH=d.current_sha256;let sel=document.getElementById('evolveVersions');sel.replaceChildren();let count=0;for(let x of d.candidates){if(x.current||x.same_content)continue;let opt=document.createElement('option');opt.value=x.path;opt.textContent=x.name+' · '+x.missing_functions.length+' funções não presentes · '+x.path;sel.appendChild(opt);count++;}out.textContent=JSON.stringify({versoes_encontradas:d.candidates.length,opcoes_diferentes:count,arquivos_verificados:d.files_checked,busca_limitada:d.limited,origens:d.roots,nota:d.note},null,2);}catch(e){out.textContent='Falha no estudo: '+e;}}
async function evolveStage(){let sel=document.getElementById('evolveVersions'),out=document.getElementById('evolveResult');if(!EVOLVE_HASH||!sel.value){out.textContent='Estude e selecione uma versão primeiro.';return;}if(!confirm('Criar backup e proposta da versão histórica selecionada? Nada será aplicado ao painel atual.'))return;try{let r=await fetch('/api/one/evolve/stage',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({path:sel.value,sha256_atual:EVOLVE_HASH})});let d=await r.json();out.textContent=JSON.stringify(d,null,2);}catch(e){out.textContent='Erro: '+e;}}

let FAVS=[];
async function favLoad(){try{let d=await(await fetch('/api/one/favorites')).json();if(!d.ok)throw Error(d.error);FAVS=d.items;document.getElementById('favSummary').textContent=`${FAVS.length} favoritos • ${FAVS.filter(x=>x.category==='curso').length} candidatos a cursos • horas e progresso: somente registros seus`;favRender();}catch(e){document.getElementById('favFeedback').textContent=String(e);}}
async function favImport(){let el=document.getElementById('favFeedback');el.textContent='Localizando marcadores locais...';try{let d=await(await fetch('/api/one/favorites/import',{method:'POST'})).json();el.textContent=JSON.stringify({importados:d.imported,fontes:d.sources,avisos:d.warnings},null,2);await favLoad();}catch(e){el.textContent=String(e);}}
function favRender(){let q=document.getElementById('favQuery').value.toLowerCase(),filter=document.getElementById('favFilter').value,box=document.getElementById('favItems');box.replaceChildren();for(let x of FAVS.filter(x=>(!filter||x.category===filter)&&[x.title,x.folder,x.url].join(' ').toLowerCase().includes(q)).slice(0,350)){let div=document.createElement('div');div.className='card';let title=document.createElement('strong');title.textContent=x.title;div.append(title);let meta=document.createElement('p');meta.textContent=`${x.folder} · ${x.category} · ${x.status||'NÃO VERIFICADO'}`;div.append(meta);let a=document.createElement('a');a.href=x.url;a.target='_blank';a.rel='noopener noreferrer';a.textContent='ABRIR FAVORITO ↗';div.append(a);let study=document.createElement('button');study.textContent='▶ ESTUDAR AGORA · INICIAR RELÓGIO';study.onclick=()=>{document.getElementById('studyTitle').value=x.title;document.getElementById('studyUrl').value=x.url;tab('sessions');studyStart()};div.append(study);let progress=document.createElement('input');progress.type='number';progress.min=0;progress.max=100;progress.value=x.progress??'';progress.placeholder='Progresso % (se souber)';progress.style.maxWidth='160px';let hours=document.createElement('input');hours.type='number';hours.min=0;hours.step=.25;hours.value=x.hours??'';hours.placeholder='Horas registradas';hours.style.maxWidth='160px';let save=document.createElement('button');save.textContent='SALVAR ESTUDO';save.onclick=async()=>{let payload={id:x.id,progress:progress.value===''?null:Number(progress.value),hours:hours.value===''?null:Number(hours.value)};let d=await(await fetch('/api/one/favorites/progress',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)})).json();document.getElementById('favFeedback').textContent=d.ok?'Estudo salvo localmente.':JSON.stringify(d);if(d.ok)await favLoad();};div.append(progress,hours,save);box.append(div);}}


/* Escola e sessões: consulta ao PC local; registros não sincronizados/publicados. */
let SCHOOL=null, STUDY=[], ACTIVE=null, _clockInterval=null;
function metric(k,v){return '<div class="metric"><small>'+esc(k)+'</small><strong>'+esc(v)+'</strong></div>'}
async function schoolLoad(force=false){let e=document.getElementById('schoolMetrics');e.innerHTML=metric('INSPEÇÃO','consultando...');try{
 if(force)await fetch('/api/one/school/recheck',{method:'POST'});
 let r=await fetch('/api/one/school/attendance',{cache:'no-store'});let d=await r.json();if(!r.ok||!d.ok)throw Error(d.error||r.status);SCHOOL=d;
 e.innerHTML=metric('ARQUIVOS CONFERIDOS',d.files)+metric('PARES VISUAIS',d.pairs.length)+metric('SKILLS LOCALIZADAS',d.skills.length)+metric('ESCOPO',d.limited?'LIMITADO':'DIRETÓRIOS CONHECIDOS');
 document.getElementById('schoolBar').style.width=Math.min(100,Math.round(d.files/6500*100))+'%';
 document.getElementById('schoolPairs').innerHTML=d.pairs.slice(0,18).map((p,i)=>'<div class="schoolPair"><img src="/api/one/school/visual/'+i+'" loading="lazy" alt="Referência encontrada"><div><b>'+esc(p.image.name)+'</b><small>'+esc(p.image.path)+'</small><small>'+esc(p.note)+'</small><small>Referências: '+esc(p.references.map(x=>x.name).join(' • ')||'não encontrada')+'</small><button data-school-pair="'+i+'">LER CRUZAMENTO</button></div></div>').join('')||'<p>Nenhum par por nome encontrado neste escopo; nada foi descartado ou sobrescrito.</p>';
 document.getElementById('schoolSkills').innerHTML=d.skills.slice(0,25).map((s,i)=>'<div class="card"><b>'+esc(s.name)+'</b><small> · '+esc(s.path)+'</small><button data-school-skill="'+i+'">LER SKILL</button></div>').join('')||'<p>SKILL 1 ainda não localizada neste escopo.</p>';
 let devices=await(await fetch('/api/one/school/diagnostics')).json();document.getElementById('schoolDevices').innerHTML=[...devices.devices,...devices.apps].map(x=>'<div class="card"><b>'+esc(x.name)+'</b> · '+esc(x.state)+'<small> '+esc(x.note)+'</small></div>').join('');
}catch(err){e.innerHTML=metric('ERRO DE INSPEÇÃO',String(err))}}
document.getElementById('schoolPairs').addEventListener('click',async e=>{let btn=e.target.closest('[data-school-pair]');if(!btn)return;let d=await(await fetch('/api/one/school/pair/'+btn.dataset.schoolPair)).json();document.getElementById('schoolResult').textContent=JSON.stringify(d,null,2)});
document.getElementById('schoolSkills').addEventListener('click',async e=>{let btn=e.target.closest('[data-school-skill]');if(!btn)return;let d=await(await fetch('/api/one/school/skill/'+btn.dataset.schoolSkill)).json();document.getElementById('schoolResult').textContent=d.ok?d.content:JSON.stringify(d);if(d.ok){document.getElementById('floatInput').value='Leia esta skill como referência local, não execute ações sem autorização.\n'+d.content.slice(0,7000)}});
function fmtSecs(n){let s=Math.max(0,Math.floor(n||0));return [Math.floor(s/3600),Math.floor(s/60)%60,s%60].map(x=>String(x).padStart(2,'0')).join(':')}
function studyTick(){let sec=ACTIVE?Math.max(0,(Date.now()-Date.parse(ACTIVE.started))/1000):0;document.getElementById('studyClock').textContent=fmtSecs(sec)}
async function studyLoad(){try{let d=await(await fetch('/api/one/study/sessions',{cache:'no-store'})).json();STUDY=d.sessions||[];ACTIVE=STUDY.find(s=>s.finished===null)||null;document.getElementById('studyActive').textContent=ACTIVE?(ACTIVE.title+' · início '+new Date(ACTIVE.started).toLocaleString('pt-BR')):'Nenhuma sessão em andamento';let finished=STUDY.filter(s=>s.finished),sec=finished.reduce((n,s)=>n+(s.seconds||0),0);document.getElementById('studyCount').textContent=finished.length;document.getElementById('studyHours').textContent=(sec/3600).toFixed(2)+' h';document.getElementById('studyHistory').innerHTML=finished.slice(-18).reverse().map(s=>'<div class="card"><b>'+esc(s.title)+'</b><small> · '+fmtSecs(s.seconds)+' · '+esc(s.chapter||'sem capítulo')+' · '+esc(s.progress===null?'progresso não informado':s.progress+'%')+'</small><p>'+esc(s.notes||'')+'</p></div>').join('');studyTick();if(!_clockInterval)_clockInterval=setInterval(studyTick,1000)}catch(e){document.getElementById('studyFeedback').textContent=String(e)}}
async function studyStart(){let title=document.getElementById('studyTitle').value.trim(),url=document.getElementById('studyUrl').value.trim();let out=document.getElementById('studyFeedback');try{let p=await fetch('/api/one/study/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title,url})});let d=await p.json();if(!p.ok)throw Error(d.error||p.status);out.textContent=d.note;await studyLoad();window.open(url,'_blank','noopener,noreferrer')}catch(e){out.textContent=String(e)}}
async function studyFinish(){let out=document.getElementById('studyFeedback');if(!ACTIVE){out.textContent='Nenhuma sessão aberta.';return}try{let p=await fetch('/api/one/study/finish',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:ACTIVE.id,chapter:document.getElementById('studyChapter').value,notes:document.getElementById('studyNotes').value,progress:document.getElementById('studyProgress').value})});let d=await p.json();if(!p.ok)throw Error(d.error||p.status);out.textContent=d.note;await studyLoad()}catch(e){out.textContent=String(e)}}
async function floatModels(){try{let d=await(await fetch('/api/one/nodes')).json();let sel=document.getElementById('floatModel');sel.innerHTML=(d.ollama_models||[]).map(m=>'<option>'+esc(m)+'</option>').join('')||'<option value="">Ollama sem modelos detectados</option>'}catch(e){document.getElementById('floatLog').textContent='Modelo indisponível: '+e}}
async function floatSend(){let el=document.getElementById('floatInput'),log=document.getElementById('floatLog'),v=el.value.trim();if(!v)return;el.value='';log.textContent+='\n\nVOCÊ: '+v+'\nAGENTE: consultando Ollama...';try{let r=await fetch('/api/one/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:v,model:document.getElementById('floatModel').value})});let d=await r.json();log.textContent=log.textContent.replace(/AGENTE: consultando Ollama\.\.\.$/,'AGENTE: '+(d.reply||d.error||'Sem resposta'));log.scrollTop=log.scrollHeight}catch(e){log.textContent+='\nFalha: '+e}}
function floatClose(){let a=document.getElementById('aurionFloat'),b=document.getElementById('floatBubble');a.style.display=a.style.display==='none'?'block':'none';b.style.display=a.style.display==='none'?'block':'none';localStorage.setItem('aurion-float-open',a.style.display==='none'?'0':'1')}
function floatToggle(){document.getElementById('aurionFloat').classList.toggle('expanded')}
(function floatDrag(){let h=document.getElementById('floatHandle'),box=document.getElementById('aurionFloat'),start=null;h.addEventListener('pointerdown',e=>{if(e.target.closest('button'))return;start={x:e.clientX,y:e.clientY,left:box.getBoundingClientRect().left,top:box.getBoundingClientRect().top};h.setPointerCapture(e.pointerId)});h.addEventListener('pointermove',e=>{if(!start)return;box.style.right='auto';box.style.bottom='auto';box.style.left=Math.max(0,Math.min(innerWidth-70,start.left+e.clientX-start.x))+'px';box.style.top=Math.max(0,Math.min(innerHeight-40,start.top+e.clientY-start.y))+'px'});h.addEventListener('pointerup',()=>{start=null})})();
if(localStorage.getItem('aurion-float-open')==='0'){document.getElementById('aurionFloat').style.display='none';document.getElementById('floatBubble').style.display='block'}
floatModels();studyLoad();schoolLoad();

hubInit();listKnowledge();loadPrograms();loadBridge();
</script></body></html>"""

# Módulo de evolução: estudo sob demanda, sem executar versões antigas.
try:
    import aurion_evolver
    aurion_evolver.register(app,ROOT,PROJECT,Path(__file__).resolve())
except Exception as exc:
    log('Evolução indisponível: '+str(exc)[:180],True)


# Favoritos locais: importação somente por ação explícita; nenhum acesso a senhas/cookies.
try:
    import aurion_favorites
    aurion_favorites.register(app, ROOT)
except Exception as exc:
    log('Favoritos indisponíveis: '+str(exc)[:180],True)

# Inventário seletivo das skills, imagens + documentação e sessões de estudo locais.
try:
    import aurion_school
    aurion_school.register(app, ROOT, PROJECT)
except Exception as exc:
    log('Escola indisponível: '+str(exc)[:180], True)

# Boot guiado: percorre SOMENTE diretórios conhecidos; não repete o scan histórico do PC.
def quick_discovery():
    previous={}
    if SCAN_FILE.is_file():
        try:
            loaded=json.loads(SCAN_FILE.read_text(encoding="utf-8"))
            if isinstance(loaded,dict) and isinstance(loaded.get("found"),list):previous=loaded
        except (OSError,ValueError):pass
    roots=[Path(r"C:\######AGENTE#####STATUS######\base#777\models"),Path(r"C:\COMFYUI\ComfyUI_windows_portable\ComfyUI\models"),Path(r"D:\ComfyUI\ComfyUI\models"),PROJECT/"models",ROOT/"models",PROJECT,ROOT,PROJECT/"docs",Path(r"C:\AURION-ONE")/"docs",PROJECT/"SKILL#PAINEL"]
    found=[];deadline=time.monotonic()+15;visited=0
    for root in roots:
        if not root.is_dir() or time.monotonic()>deadline:continue
        try:
            for folder in [root]+[x for x in root.iterdir() if x.is_dir()][:45]:
                if time.monotonic()>deadline or visited>7000:break
                for f in folder.iterdir():
                    visited+=1
                    if visited>7000 or time.monotonic()>deadline:break
                    if not f.is_file():continue
                    ext=f.suffix.lower();name=f.name.casefold()
                    kind="models" if ext in (".safetensors",".ckpt",".gguf",".onnx") else "knowledge" if ext in (".docx",".md",".txt") and any(x in name for x in ("biblia","bíblia","reuniao","reunião","aurion","historia","história","laboratorio","laboratório")) else None
                    if kind:found.append({"path":str(f),"kind":kind,"source":"boot guiado"})
        except OSError:continue
    try:
        old_found=previous.get("found",[]);all_found=[];seen=set()
        for entry in old_found+found:
            if not isinstance(entry,dict) or not isinstance(entry.get("path"),str):continue
            key=entry["path"].casefold()
            if key not in seen and len(all_found)<12000:all_found.append(entry);seen.add(key)
        report={**previous,"date":time.strftime("%Y-%m-%d %H:%M:%S"),"found":all_found,"boot_scan":{"date":time.strftime("%Y-%m-%d %H:%M:%S"),"files_checked":visited,"new_entries":len(all_found)-len(old_found),"limited":visited>=7000 or time.monotonic()>deadline},"scan_type":previous.get("scan_type","boot guiado; não cobre todos os discos")}
        if not previous:report.update({"roots":[str(x) for x in roots if x.is_dir()],"folders":0,"files":visited,"errors":[],"truncated":visited>=7000 or time.monotonic()>deadline})
        atomic_json(SCAN_FILE,report)
        log("Boot guiado: "+str(len(found))+" modelos/documentos; "+str(len(all_found))+" entradas preservadas/atualizadas")
        return True
    except OSError as e:
        log("Boot guiado falhou ao salvar: "+str(e)[:120],True);return False

# Ollama: inicialização local opcional, sem baixar modelos nem abrir portas externas.
def ensure_ollama_local():
    if ollama_models():return True
    configured=load_settings().get("paths",{}).get("ollama","")
    candidates=[Path(configured)] if configured else []
    which=shutil.which("ollama")
    if which:candidates.append(Path(which))
    candidates.extend([Path(os.environ.get("LOCALAPPDATA",""))/"Programs"/"Ollama"/"ollama.exe",Path(os.environ.get("PROGRAMFILES",""))/"Ollama"/"ollama.exe"])
    for exe in candidates:
        if not exe.is_file() or exe.name.lower() not in ("ollama.exe","ollama"):continue
        try:
            dest=LOG_DIR/"ollama_servico.log"
            with dest.open("ab") as out:subprocess.Popen([str(exe),"serve"],cwd=str(exe.parent),stdin=subprocess.DEVNULL,stdout=out,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
            log("Ollama local: inicialização solicitada; verificando /api/tags")
            for _ in range(12):
                time.sleep(1)
                if ollama_models():return True
            log("Ollama iniciado, mas nenhum modelo respondeu; confira ollama list e logs",True)
            return False
        except OSError as exc:log("Ollama: "+str(exc),True)
    log("Ollama não encontrado nos caminhos conhecidos; configurar executável em LIGAÇÕES",True)
    return False

# Boot sem instalar pacotes, sem abrir o painel antigo e sem iniciar outro Flask na 5000.
def _startup():
    checks=[("Base e estado",lambda: PROJECT.exists()),
            ("Inventário guiado de modelos e documentos",quick_discovery),
            ("Skills e referências visuais",lambda: bool(aurion_school.inventory(ROOT,PROJECT,maximum=2500,seconds=3).get("roots")) if "aurion_school" in globals() else False),
            ("Rastros anteriores",lambda: SCAN_FILE.exists() or (ROOT/"scan_report.json").exists()),
            ("Painel legado (somente verificar)",lambda: bool(http_json("http://127.0.0.1:5000/api/status",2))),
            ("Ollama e modelos",ensure_ollama_local),
            ("ComfyUI e GPU",lambda: bool(http_json(COMFY_URL+"/system_stats",4))),
            ("Inventario ComfyUI",lambda: bool(http_json(COMFY_URL+"/object_info",6)))]
    for label,fn in checks:
        BOOT["step"]="Verificando "+label
        try: result=fn()
        except Exception as e: result=False;log(f"{label}: {e}",True)
        BOOT["details"].append({"item":label,"ok":bool(result)})
        BOOT["done"]+=1
        log(f"{label}: {'OK' if result else 'PENDENTE'}")
    BOOT["step"]="Verificacao concluida. Servicos pendentes estao sinalizados; nenhuma instalacao automatica."
    BOOT["ready"]=True

if __name__=="__main__":
    print("AURION ONE · BUILD",BUILD,flush=True)
    print("Painel unico: http://127.0.0.1:5058/",flush=True)
    print("Logs:",LOG_DIR,flush=True)
    print("Nao abre navegador antigo nem instala dependencias.",flush=True)
    if port_open(PORT):
        print("Porta 5058 ocupada. Encerre a instancia anterior ANTES de iniciar esta versao.",flush=True)
        sys.exit(2)
    threading.Thread(target=_startup,daemon=True).start()
    def _open_once():
        for _ in range(120):
            if BOOT["ready"] and http_json(f"http://{HOST}:{PORT}/api/one/boot",1):
                webbrowser.open(f"http://{HOST}:{PORT}/?build={BUILD}");return
            time.sleep(.3)
    threading.Thread(target=_open_once,daemon=True).start()
    app.run(host=HOST,port=PORT,debug=False,threaded=True,use_reloader=False)
