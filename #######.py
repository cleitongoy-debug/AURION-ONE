# -*- coding: utf-8 -*-
"""AURION DYNAMIC - painel local integrado.
Chat/Agente (Ollama), ComfyUI, modelos, geracao por workflow,
render/CUDA/NVIDIA, Git, dependencias, CMD e logs.
"""
from __future__ import annotations
import json, os, shutil, socket, subprocess, sys, threading, time, urllib.request, webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any
import base64, mimetypes, re
try:
    from werkzeug.utils import secure_filename
except Exception:
    def secure_filename(name):
        return re.sub(r"[^A-Za-z0-9._-]+", "_", str(name or "file"))
try:
    from flask import Flask, jsonify, request, render_template_string
except ImportError:
    subprocess.check_call([sys.executable,"-m","pip","install","flask"])
    from flask import Flask, jsonify, request, render_template_string

PROJECT=Path(r"C:\Users\ADM_PESS\Desktop\painelseguro#1 - Copia")
MODELS=PROJECT/"models"; DOWNLOADS=PROJECT/"_downloads"; LOG_DIR=PROJECT/"_aurion_logs"; WORKFLOWS=PROJECT/"workflows"; SCAN_DIR=PROJECT/"scan"; SCAN_REPORT=SCAN_DIR/"catalogo.json"; SCAN_JSONL=SCAN_DIR/"arquivos.jsonl"
MEMORY_DIR=PROJECT/"memoria"; MENTE_DIR=PROJECT/"mente"; FRAG_DIR=PROJECT/"fragmentos"; CLIENT_DIR=PROJECT/"clientes"; PROJECTS_DIR=PROJECT/"projetos"
AGENTS_DIR=PROJECT/"agentes"; REFERENCES_DIR=PROJECT/"referencias"; REF_INBOX=REFERENCES_DIR/"inbox"; CONFIG_DIR=PROJECT/"config"; AGENT_CONFIG=CONFIG_DIR/"agentes.json"; REF_CONFIG=CONFIG_DIR/"referencias.json"; VIDEO_JOBS=PROJECT/"video_jobs"
HOST="127.0.0.1"; PORT=5000; COMFY_PORT=8188; OLLAMA_PORT=11434; OPENWEBUI_PORT=8080
COMFY_URL=f"http://127.0.0.1:{COMFY_PORT}"; OLLAMA_URL=f"http://127.0.0.1:{OLLAMA_PORT}"; OPENWEBUI_URL=f"http://127.0.0.1:{OPENWEBUI_PORT}"
COMFY_PORTABLE_URL="https://github.com/comfyanonymous/ComfyUI/releases/latest/download/ComfyUI_windows_portable_nvidia.7z"
SEVENZIP_URL="https://www.7-zip.org/a/7zr.exe"
OLLAMA_PREFERRED=["qwen3.5:4b","qwen3:8b","llama3.2:3b","llava:7b","deepseek-r1:7b"]
IGNORE={"Windows","Program Files","Program Files (x86)","Arquivos de Programas","PerfLogs","System","System32","AppData","Microsoft","Microsoft.NET","WindowsApps","$Recycle.Bin","System Volume Information","Recovery","ProgramData","node_modules",".git"}
MODEL_EXT={".safetensors",".ckpt",".pt",".pth",".bin",".gguf",".onnx",".sft"}
app=Flask(__name__)
STATE:dict[str,Any]={"busy":False,"operation":"","progress":0,"message":"AURION pronto.","logs":[],"errors":[],"scan":None,"agent_model":None,"startup_done":False,"startup":{},"image_job":{},"video_job":{}}
LOCK=threading.Lock()

def ensure_dirs():
    for p in (PROJECT,MODELS,DOWNLOADS,LOG_DIR,WORKFLOWS,SCAN_DIR,MEMORY_DIR,MENTE_DIR,FRAG_DIR,CLIENT_DIR,PROJECTS_DIR,AGENTS_DIR,REFERENCES_DIR,REF_INBOX,CONFIG_DIR,VIDEO_JOBS): p.mkdir(parents=True,exist_ok=True)
def ensure_agent_config():
    ensure_dirs()
    if not AGENT_CONFIG.exists():
        data={"AURION":{"model":"","role":"orquestrador","enabled":True,"prompt":"Você é o AURION, coordenador local de produção."},"VISION":{"model":"","role":"análise visual","enabled":False,"prompt":"Analise imagens e vídeos com precisão."},"PROMPT":{"model":"","role":"engenharia de prompt","enabled":False,"prompt":"Crie e refine prompts de produção visual."},"CODE":{"model":"","role":"programação e manutenção","enabled":False,"prompt":"Analise código, dependências e erros sem inventar resultados."}}
        AGENT_CONFIG.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    if not REF_CONFIG.exists():
        REF_CONFIG.write_text(json.dumps({"roots":[str(PROJECT),str(Path.home()/"Desktop")]},ensure_ascii=False,indent=2),encoding="utf-8")

def load_agent_config():
    ensure_agent_config()
    try:return json.loads(AGENT_CONFIG.read_text(encoding="utf-8"))
    except Exception:return {}

def save_agent_config(data):
    ensure_agent_config(); AGENT_CONFIG.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")

def load_ref_config():
    ensure_agent_config()
    try:return json.loads(REF_CONFIG.read_text(encoding="utf-8"))
    except Exception:return {"roots":[str(PROJECT)]}

def safe_inside(base,path):
    try:return Path(path).resolve().is_relative_to(Path(base).resolve())
    except AttributeError:
        try:Path(path).resolve().relative_to(Path(base).resolve());return True
        except Exception:return False

def log(msg,error=False):
    line=f"[{datetime.now():%H:%M:%S}] {msg}"
    with LOCK:
        STATE["logs"]=(STATE["logs"]+[line])[-300:]; STATE["message"]=msg
        if error: STATE["errors"]=(STATE["errors"]+[line])[-150:]
    try:
        (LOG_DIR/"aurion.log").open("a",encoding="utf-8").write(line+"\n")
        if error: (LOG_DIR/"errors.log").open("a",encoding="utf-8").write(line+"\n")
    except Exception: pass
def progress(v,msg=None):
    with LOCK: STATE["progress"]=max(0,min(100,int(v))); STATE["message"]=msg or STATE["message"]
    if msg: log(msg)
def bg(name,fn,*a,**kw):
    with LOCK:
        if STATE["busy"]: return False
        STATE.update(busy=True,operation=name,progress=0)
    def worker():
        try: fn(*a,**kw)
        except Exception as e: log(f"ERRO em {name}: {type(e).__name__}: {e}",True)
        finally:
            with LOCK: STATE.update(busy=False,operation="",progress=100)
    threading.Thread(target=worker,daemon=True).start(); return True
def exists(cmd): return shutil.which(cmd) is not None
def version(cmd):
    try:
        p=subprocess.run(cmd,capture_output=True,text=True,timeout=8,encoding="utf-8",errors="ignore"); return (p.stdout or p.stderr or "").strip().splitlines()[0]
    except Exception:return ""
def port(port):
    s=socket.socket(); s.settimeout(.6)
    try:return s.connect_ex(("127.0.0.1",port))==0
    finally:s.close()
def http_json(url,timeout=5):
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"AURION/2.0"}),timeout=timeout) as r:return json.loads(r.read().decode("utf-8",errors="ignore"))
    except Exception:return None
def post_json(url,payload,timeout=30):
    req=urllib.request.Request(url,data=json.dumps(payload,ensure_ascii=False).encode(),headers={"Content-Type":"application/json","User-Agent":"AURION/2.1"},method="POST")
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:
            raw=r.read().decode("utf-8",errors="ignore")
            try:return json.loads(raw)
            except Exception:return {"raw":raw}
    except urllib.error.HTTPError as e:
        raw=e.read().decode("utf-8",errors="ignore") if e.fp else ""
        detail=raw.strip() or str(e.reason)
        raise RuntimeError(f"HTTP {e.code} em {url}: {detail[:5000]}") from e
def hsize(n):
    x=float(max(0,n))
    for u in ("B","KB","MB","GB","TB"):
        if x<1024:return f"{x:.1f} {u}"
        x/=1024
    return f"{x:.1f} PB"
def rel(p,b):
    try:return str(p.resolve().relative_to(b.resolve()))
    except Exception:return str(p)
def exe(name,extra=None):
    x=shutil.which(name)
    if x:return x
    for p in extra or []:
        if p.exists():return str(p)
    return None

# ---------------- ComfyUI ----------------
def comfy_candidates(max_depth=5):
    roots=[PROJECT,PROJECT.parent,Path.home()/"Desktop",Path.home()/"Downloads",Path.home()/"Documents"]
    for l in "CDEFGHIJKLMNOPQRSTUVWXYZ":
        p=Path(f"{l}:\\")
        if p.exists():roots.append(p)
    out=[]; seen=set()
    def add(d):
        try:d=d.resolve()
        except Exception:pass
        main=d/"main.py"
        if not main.exists() or d.name.lower()!="comfyui":return
        if not any((d/x).exists() for x in ("nodes.py","folder_paths.py","custom_nodes")):return
        k=str(d).lower()
        if k in seen:return
        seen.add(k); py=None
        for x in (d.parent/"python_embeded"/"python.exe",d/"python_embeded"/"python.exe"):
            if x.exists():py=x;break
        if py is None:py=Path(sys.executable)
        out.append({"path":str(d),"main":str(main),"python":str(py),"portable":"python_embeded" in str(py).lower()})
    for root in roots:
        if not root.exists():continue
        try:
            for cur,dirs,files in os.walk(root):
                p=Path(cur)
                try:depth=len(p.relative_to(root).parts)
                except Exception:depth=max_depth+1
                if depth>max_depth:dirs[:]=[];continue
                dirs[:]=[d for d in dirs if d not in IGNORE and not d.startswith('.')]
                if p.name.lower()=="comfyui" and "main.py" in files:add(p)
        except (PermissionError,OSError):pass
    out.sort(key=lambda x:(not x["portable"],PROJECT.as_posix().lower() not in x["path"].lower(),len(x["path"])))
    return out
def comfy():
    cs=comfy_candidates(); c=cs[0] if cs else None
    return ({"found":False,"path":None,"main":None,"python":None,"portable":False,"running":port(COMFY_PORT),"candidates":cs} if not c else {**c,"found":True,"running":port(COMFY_PORT),"candidates":cs})
def configure_comfy():
    c=comfy()
    if not c["found"]:raise RuntimeError("ComfyUI não encontrado.")
    p=Path(c["path"])/"extra_model_paths.yaml"
    text=f'''# AURION DYNAMIC - modelos externos\naurion:\n  base_path: {MODELS.as_posix()}\n  checkpoints: checkpoints/\n  diffusion_models: diffusion_models/\n  vae: vae/\n  text_encoders: text_encoders/\n  loras: loras/\n  controlnet: controlnet/\n  clip: clip/\n  clip_vision: clip_vision/\n  unet: unet/\n  upscale_models: upscale_models/\n  embeddings: embeddings/\n  ipadapter: ipadapter/\n  photomaker: photomaker/\n  style_models: style_models/\n  gligen: gligen/\n  hypernetworks: hypernetworks/\n  vae_approx: vae_approx/\n'''
    if p.exists():
        try:shutil.copy2(p,p.with_name(f"extra_model_paths.yaml.aurion_{datetime.now():%Y%m%d_%H%M%S}.bak"))
        except Exception:pass
    p.write_text(text,encoding="utf-8"); log(f"Modelos externos ligados ao ComfyUI: {MODELS}")
def comfy_stats():return http_json(f"{COMFY_URL}/system_stats",5) if port(COMFY_PORT) else None

def start_comfy():
    c=comfy()
    if not c["found"]:log("ComfyUI não encontrado.",True);return False
    if c["running"]:log("ComfyUI já está ONLINE.");return True
    configure_comfy(); cmd=[c["python"],c["main"],"--listen","127.0.0.1","--port",str(COMFY_PORT)]
    log("Iniciando ComfyUI...")
    subprocess.Popen(cmd,cwd=c["path"],creationflags=getattr(subprocess,"CREATE_NEW_PROCESS_GROUP",0),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    for _ in range(40):
        if port(COMFY_PORT):log(f"ComfyUI ONLINE: {COMFY_URL}");return True
        time.sleep(1)
    log("ComfyUI não respondeu.",True);return False

# ---------------- Models / Ollama ----------------
def inventory():
    files=[];counts={};total=0
    if not MODELS.exists():return {"counts":{},"total":0,"bytes":0,"size":"0 B","files":[]}
    try:
        for p in MODELS.rglob("*"):
            if not p.is_file() or any(x in IGNORE for x in p.parts) or p.suffix.lower() not in MODEL_EXT:continue
            try:n=p.stat().st_size
            except OSError:n=0
            counts[p.suffix.lower()]=counts.get(p.suffix.lower(),0)+1;total+=n
            if len(files)<500:files.append({"name":p.name,"path":rel(p,MODELS),"size":hsize(n),"ext":p.suffix.lower()})
    except OSError:pass
    return {"counts":counts,"total":sum(counts.values()),"bytes":total,"size":hsize(total),"files":files}
def model_folders():
    ns=["checkpoints","diffusion_models","vae","text_encoders","loras","controlnet","clip","clip_vision","unet","upscale_models","embeddings","ipadapter","photomaker","style_models","gligen","hypernetworks","vae_approx"]
    return {n:sum(1 for p in (MODELS/n).rglob("*") if p.is_file()) if (MODELS/n).exists() else 0 for n in ns}
def ollama_models():
    d=http_json(f"{OLLAMA_URL}/api/tags",5);return d.get("models",[]) if isinstance(d,dict) else []
def choose_model():
    ms=ollama_models();names=[m.get("name") for m in ms if m.get("name")]
    if not names:return None
    with LOCK:cur=STATE.get("agent_model")
    chosen=cur if cur in names else next((x for x in OLLAMA_PREFERRED if x in names),names[0])
    with LOCK:STATE["agent_model"]=chosen
    return chosen
def start_ollama():
    if port(OLLAMA_PORT):choose_model();log(f"Ollama ONLINE — agente carregado: {STATE.get('agent_model')}");return True
    x=exe("ollama",[Path(os.environ.get("LOCALAPPDATA",""))/"Programs/Ollama/ollama.exe",Path(r"C:\Program Files\Ollama\ollama.exe")])
    if not x:log("Ollama não encontrado.",True);return False
    log("Iniciando Ollama...");subprocess.Popen([x,"serve"],creationflags=getattr(subprocess,"CREATE_NEW_PROCESS_GROUP",0),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    for _ in range(25):
        if port(OLLAMA_PORT):choose_model();log(f"Agente carregado: {STATE.get('agent_model')}");return True
        time.sleep(1)
    log("Ollama não respondeu.",True);return False
def start_webui():
    if port(OPENWEBUI_PORT):log("Open WebUI já está ONLINE.");return True
    x=exe("open-webui")
    if not x:log("open-webui não encontrado no PATH.",True);return False
    log("Iniciando Open WebUI...");subprocess.Popen([x,"serve"],cwd=str(PROJECT),creationflags=getattr(subprocess,"CREATE_NEW_PROCESS_GROUP",0),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    for _ in range(35):
        if port(OPENWEBUI_PORT):log(f"Open WebUI ONLINE: {OPENWEBUI_URL}");return True
        time.sleep(1)
    log("Open WebUI não respondeu.",True);return False

def load_scan_summary_for_agent(message=""):
    """Entrega ao agente apenas fatos encontrados pelo AURION."""
    data={}
    try:
        if SCAN_REPORT.exists(): data=json.loads(SCAN_REPORT.read_text(encoding="utf-8"))
    except Exception: data={}
    if not data: return {"status":"SEM_SCAN_SALVO"}
    low=message.lower()
    ctx={"timestamp":data.get("timestamp"),"label":data.get("label"),"arquivos":data.get("arquivos",0),"pastas":data.get("pastas",0),"tamanho":data.get("tamanho","0 B"),"por_tipo":data.get("por_tipo",{}),"clientes":data.get("clientes",{}),"projetos":data.get("projetos",{}),"repositorios":data.get("repositorios",[])[:100]}
    if any(k in low for k in ("arquivo","arquivos","projeto","projetos","cliente","clientes","scan","pasta","pastas")):
        q=message.strip()
        terms=[x for x in q.replace("?"," ").replace(","," ").split() if len(x)>2]
        rows=[]
        if SCAN_JSONL.exists():
            try:
                with SCAN_JSONL.open("r",encoding="utf-8",errors="ignore") as f:
                    for line in f:
                        if not line.strip(): continue
                        item=json.loads(line)
                        hay=(item.get("nome","")+" "+item.get("caminho","")).lower()
                        if not terms or any(t.lower() in hay for t in terms):
                            rows.append(item)
                            if len(rows)>=200: break
            except Exception: pass
        ctx["arquivos_relevantes"]=rows
    return ctx

def clean_agent_reply(text):
    text=str(text or "").strip()
    import re
    text=re.sub(r"<think>.*?</think>","",text,flags=re.I|re.S).strip()
    text=re.sub(r"^\s*(thinking|reasoning)\s*:.*?(?=\n\S|$)","",text,flags=re.I|re.S).strip()
    return text[:6000]

def chat(message,model=None):
    if not port(OLLAMA_PORT):return None,"Ollama offline."
    model=model or choose_model()
    if not model:return None,"Nenhum modelo Ollama instalado."
    d=diagnose(True)
    plan=agent_generation_plan(message)
    scanctx=load_scan_summary_for_agent(message)
    memory=[]
    for folder in (MEMORY_DIR,MENTE_DIR,FRAG_DIR):
        if folder.exists():
            for p in sorted(folder.glob("*.md"),key=lambda x:x.stat().st_mtime if x.exists() else 0,reverse=True)[:20]:
                try: memory.append({"arquivo":p.name,"conteudo":p.read_text(encoding="utf-8",errors="replace")[:4000]})
                except Exception: pass
    system="""Você é o AGENTE AURION DYNAMIC LOCAL. Responda SOMENTE em português do Brasil. Seja curto, direto e útil. NÃO mostre raciocínio interno, pensamento, cadeia de pensamento ou texto <think>. NÃO invente arquivos, projetos, clientes, programas, versões ou capacidades. Quando a pergunta for sobre o PC, use apenas DIAGNÓSTICO LOCAL. Quando for sobre arquivos/projetos/clientes, use SCAN REAL. Se o dado não estiver no diagnóstico/scan, diga 'Não encontrei esse dado no scan'. Não afirme que executou uma ação se não houver resultado real. Preserve caminhos e nomes exatamente quando forem dados pelo sistema."""
    prompt=(system+"\n\nPLANO DE AÇÃO: "+json.dumps(plan,ensure_ascii=False)+"\n\nDIAGNÓSTICO LOCAL:\n"+json.dumps(d,ensure_ascii=False,indent=2)+"\n\nSCAN:\n"+json.dumps(scanctx,ensure_ascii=False,indent=2)+"\n\nMEMÓRIAS LOCAIS:\n"+json.dumps(memory,ensure_ascii=False,indent=2)+"\n\nUSUÁRIA:\n"+message)
    try:
        r=post_json(f"{OLLAMA_URL}/api/generate",{"model":model,"prompt":prompt,"stream":False,"keep_alive":"10m","options":{"temperature":0.1,"num_predict":350}},120)
        return clean_agent_reply(r.get("response") if isinstance(r,dict) else r),None
    except Exception as e:log(f"Erro no chat Ollama: {e}",True);return None,str(e)

# ---------------- NVIDIA / CUDA ----------------
def nvidia():
    x=exe("nvidia-smi",[Path(r"C:\Windows\System32\nvidia-smi.exe"),Path(r"C:\Program Files\NVIDIA Corporation\NVSMI\nvidia-smi.exe")])
    if not x:return {"installed":False,"message":"nvidia-smi não encontrado."}
    try:
        p=subprocess.run([x,"--query-gpu=name,driver_version,memory.total,memory.used,utilization.gpu,temperature.gpu","--format=csv,noheader,nounits"],capture_output=True,text=True,timeout=8,encoding="utf-8",errors="ignore")
        gs=[]
        for line in p.stdout.splitlines():
            a=[z.strip() for z in line.split(",")]
            if len(a)>=6:gs.append({"name":a[0],"driver":a[1],"vram_total_mb":a[2],"vram_used_mb":a[3],"gpu_percent":a[4],"temperature_c":a[5]})
        return {"installed":p.returncode==0,"executable":x,"gpus":gs,"raw":(p.stdout or p.stderr).strip()}
    except Exception as e:return {"installed":False,"message":str(e),"executable":x}
def cuda_py():
    try:
        p=subprocess.run([sys.executable,"-c","import torch; print('TORCH='+torch.__version__); print('CUDA='+str(torch.version.cuda)); print('AVAILABLE='+str(torch.cuda.is_available())); print('GPUS='+str(torch.cuda.device_count()))"],capture_output=True,text=True,timeout=15,encoding="utf-8",errors="ignore")
        return {"ok":p.returncode==0,"output":(p.stdout or p.stderr).strip()}
    except Exception as e:return {"ok":False,"output":str(e)}

def diagnose(light=False):
    c=comfy(); n=nvidia(); inv=inventory(); oll=port(OLLAMA_PORT)
    d={"timestamp":datetime.now().isoformat(timespec="seconds"),"project":str(PROJECT),"models":str(MODELS),"python":sys.version.split()[0],"python_executable":sys.executable,"comfy":c,"ollama":{"running":oll,"url":OLLAMA_URL,"port":OLLAMA_PORT,"executable":exe("ollama",[Path(os.environ.get("LOCALAPPDATA",""))/"Programs/Ollama/ollama.exe",Path(r"C:\Program Files\Ollama\ollama.exe")]),"model":choose_model() if oll else None},"openwebui":{"running":port(OPENWEBUI_PORT),"url":OPENWEBUI_URL,"port":OPENWEBUI_PORT,"executable":exe("open-webui")},"nvidia":n,"tools":{"git":exists("git"),"git_version":version(["git","--version"]) if exists("git") else "","ffmpeg":exists("ffmpeg"),"ffmpeg_version":version(["ffmpeg","-version"]) if exists("ffmpeg") else "","7zip":exists("7z") or exists("7za") or (DOWNLOADS/"7zr.exe").exists(),"winget":exists("winget")},"models_inventory":inv,"model_folders":model_folders()}
    if not light:d["cuda_python"]=cuda_py()
    return d

# ---------------- Git / dependencies / install ----------------
def git_root(p):
    if not exists("git") or not p.exists():return None
    try:
        q=subprocess.run(["git","-C",str(p),"rev-parse","--show-toplevel"],capture_output=True,text=True,timeout=10,encoding="utf-8",errors="ignore");o=q.stdout.strip();return Path(o) if q.returncode==0 and o else None
    except Exception:return None
def git_status(p):
    r=git_root(p)
    if not r:return {"path":str(p),"is_repo":False}
    def run(a):
        q=subprocess.run(["git","-C",str(r)]+a,capture_output=True,text=True,timeout=15,encoding="utf-8",errors="ignore");return (q.stdout or q.stderr).strip()
    branch=run(["branch","--show-current"])
    head=run(["rev-parse","--abbrev-ref","HEAD"])
    if head=="HEAD": branch="(DETACHED HEAD)"
    return {"path":str(r),"is_repo":True,"branch":branch,"head":run(["rev-parse","--short","HEAD"]),"detached":head=="HEAD","dirty":bool(run(["status","--porcelain"])),"status":run(["status","--short"]),"remote":run(["remote","-v"])}

def git_default_branch(r):
    # Primeiro tenta a referencia local origin/HEAD; depois consulta o remoto.
    for args in (["symbolic-ref","--short","refs/remotes/origin/HEAD"],):
        q=subprocess.run(["git","-C",str(r)]+args,capture_output=True,text=True,timeout=15,encoding="utf-8",errors="ignore")
        if q.returncode==0 and q.stdout.strip():
            v=q.stdout.strip()
            return v.split("origin/",1)[1] if v.startswith("origin/") else v
    q=subprocess.run(["git","-C",str(r),"ls-remote","--symref","origin","HEAD"],capture_output=True,text=True,timeout=30,encoding="utf-8",errors="ignore")
    for line in (q.stdout or "").splitlines():
        if line.startswith("ref:") and "refs/heads/" in line:
            return line.split("refs/heads/",1)[1].split("\t",1)[0].strip()
    for name in ("main","master"):
        q=subprocess.run(["git","-C",str(r),"show-ref","--verify",f"refs/remotes/origin/{name}"],capture_output=True,text=True,timeout=10,encoding="utf-8",errors="ignore")
        if q.returncode==0:return name
    return None

def git_repair_branch(r):
    r=Path(r)
    if not git_root(r):raise RuntimeError(f"Repositório Git não encontrado: {r}")
    status=git_status(r)
    if status.get("dirty"):
        raise RuntimeError("ComfyUI possui alterações locais. O AURION não fará checkout automático para não apagar trabalho local. Faça backup/commit/stash e tente novamente.")
    if not status.get("detached"):return status.get("branch") or ""
    log("Git em DETACHED HEAD. Corrigindo para a branch principal...")
    q=subprocess.run(["git","-C",str(r),"fetch","origin","--prune"],capture_output=True,text=True,timeout=300,encoding="utf-8",errors="ignore")
    out=((q.stdout or "")+"\n"+(q.stderr or "")).strip()
    for line in out.splitlines()[-60:]:log(line)
    if q.returncode:raise RuntimeError("git fetch origin falhou: "+(out[-1500:] or str(q.returncode)))
    branch=git_default_branch(r)
    if not branch:raise RuntimeError("Não foi possível descobrir a branch padrão do origin (main/master).")
    exists_local=subprocess.run(["git","-C",str(r),"show-ref","--verify",f"refs/heads/{branch}"],capture_output=True,timeout=10).returncode==0
    if exists_local:
        cmd=["git","-C",str(r),"checkout",branch]
    else:
        cmd=["git","-C",str(r),"checkout","-b",branch,"--track",f"origin/{branch}"]
    q=subprocess.run(cmd,capture_output=True,text=True,timeout=60,encoding="utf-8",errors="ignore")
    out=((q.stdout or "")+"\n"+(q.stderr or "")).strip()
    for line in out.splitlines()[-40:]:log(line)
    if q.returncode:raise RuntimeError("Não foi possível sair do DETACHED HEAD: "+(out[-2000:] or str(q.returncode)))
    log(f"Git reparado: branch {branch}")
    return branch
def repo_report():
    c=comfy();ps=[PROJECT]
    if c["found"]:ps.append(Path(c["path"]))
    if c["found"] and (Path(c["path"])/"custom_nodes").exists():
        try:ps += [x for x in (Path(c["path"])/"custom_nodes").iterdir() if x.is_dir()]
        except OSError:pass
    out=[];seen=set()
    for p in ps:
        r=git_root(p)
        if r and str(r).lower() not in seen:seen.add(str(r).lower());out.append(git_status(r))
    return out
def git_pull(p):
    r=git_root(p)
    if not r:raise RuntimeError(f"Repositório não encontrado: {p}")
    git_repair_branch(r)
    q=subprocess.run(["git","-C",str(r),"pull","--ff-only"],capture_output=True,text=True,timeout=900,encoding="utf-8",errors="ignore")
    out=((q.stdout or "")+"\n"+(q.stderr or "")).strip()
    for line in out.splitlines()[-100:]:log(line)
    if q.returncode:raise RuntimeError(f"git pull falhou ({q.returncode}): {out[-2500:]}")
    log(f"Git atualizado com sucesso: {r}")
    return True
def update_comfy_git():
    c=comfy()
    if not c["found"]:raise RuntimeError("ComfyUI não encontrado.")
    return git_pull(Path(c["path"]))
def update_deps():
    c=comfy()
    if not c["found"]:raise RuntimeError("ComfyUI não encontrado.")
    py=Path(c["python"]);req=Path(c["path"])/"requirements.txt"
    subprocess.run([str(py),"-m","pip","install","--upgrade","pip"],cwd=c["path"],timeout=900)
    if req.exists() and subprocess.run([str(py),"-m","pip","install","-r",str(req)],cwd=c["path"],timeout=1800).returncode:raise RuntimeError("requirements falhou")
    log("Dependências do ComfyUI atualizadas.")
def download(url,dest,label):
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 AURION"});dest.parent.mkdir(parents=True,exist_ok=True)
    with urllib.request.urlopen(req,timeout=90) as r:
        total=int(r.headers.get("Content-Length","0") or 0);done=0
        with dest.open("wb") as f:
            while True:
                ch=r.read(1024*1024)
                if not ch:break
                f.write(ch);done+=len(ch)
                progress(int(done/total*100) if total else 0,f"{label}: {hsize(done)}"+(f" / {hsize(total)}" if total else ""))
    log(f"Download concluído: {dest}")
def install_comfy():
    if comfy()["found"]:log("ComfyUI já localizado.");return True
    arc=DOWNLOADS/"ComfyUI_windows_portable_nvidia.7z";seven=DOWNLOADS/"7zr.exe"
    if not arc.exists():download(COMFY_PORTABLE_URL,arc,"ComfyUI Portable NVIDIA")
    if not seven.exists():download(SEVENZIP_URL,seven,"7zr.exe")
    target=PROJECT/"ComfyUI_Portable";target.mkdir(parents=True,exist_ok=True)
    q=subprocess.run([str(seven),"x",str(arc),f"-o{target}","-y"],capture_output=True,text=True,timeout=3600,encoding="utf-8",errors="ignore")
    if q.returncode:log((q.stderr or "Falha na extração")[-3000:],True);return False
    return comfy()["found"]
def full_setup():
    log("=== CORREÇÃO COMPLETA ===");progress(5,"Verificando ComfyUI...")
    if not comfy()["found"]:
        progress(15,"ComfyUI não encontrado. Baixando...")
        if not install_comfy():raise RuntimeError("Não foi possível instalar/localizar ComfyUI.")
    progress(35,"Configurando modelos...");configure_comfy();progress(50,"Atualizando dependências...")
    try:update_deps()
    except Exception as e:log(f"Dependências: {e}",True)
    progress(75,"Atualizando Git do ComfyUI...")
    try:update_comfy_git()
    except Exception as e:log(f"Git ComfyUI: {e}",True)
    progress(100,"Correção completa finalizada.");log("=== CORREÇÃO COMPLETA FINALIZADA ===")

def startup():
    log("=== CARREGAMENTO INICIAL DO AURION ===")
    for name,fn in (("ollama",start_ollama),("comfyui",start_comfy),("openwebui",start_webui)):
        try:ok=fn()
        except Exception as e:ok=False;log(f"{name}: {e}",True)
        with LOCK:STATE["startup"][name]=ok
    with LOCK:STATE["startup_done"]=True
    log("=== CARREGAMENTO INICIAL FINALIZADO ===")

def open_cmd():
    try:subprocess.Popen(["cmd.exe","/d","/k"],cwd=str(PROJECT));log("CMD aberto.");return True
    except Exception as e:log(f"Erro CMD: {e}",True);return False

# ---------------- AGENTES / REFERENCIAS / VIDEO ----------------
AGENT_ACTIONS={"status":"diagnóstico local","scan":"scan local","scan_completo":"scan A-Z","modelos":"inventário de modelos","comfy":"diagnóstico ComfyUI","ollama":"diagnóstico Ollama","gpu":"diagnóstico NVIDIA","git":"status Git","start_comfy":"iniciar ComfyUI","start_ollama":"iniciar Ollama","start_webui":"iniciar Open WebUI","dependencies":"atualizar dependências do ComfyUI"}

def agent_generation_plan(message,context=None):
    low=str(message or "").lower(); plan={"objetivo":"analisar pedido","acao":"chat","ferramentas":[],"modelo":STATE.get("agent_model"),"parametros":{}}
    if any(x in low for x in ("scan","arquivos","pasta","hd","disco")):plan.update(objetivo="consultar arquivos reais",acao="scan",ferramentas=["scan"])
    elif any(x in low for x in ("comfy","comfyui","workflow")):plan.update(objetivo="verificar pipeline ComfyUI",acao="comfy",ferramentas=["comfy"])
    elif any(x in low for x in ("gpu","nvidia","vram","cuda")):plan.update(objetivo="verificar GPU",acao="gpu",ferramentas=["gpu"])
    elif any(x in low for x in ("modelo","checkpoint","lora","vae")):plan.update(objetivo="consultar inventário de modelos",acao="modelos",ferramentas=["modelos"])
    elif any(x in low for x in ("dependência","dependencias","requirements")):plan.update(objetivo="diagnosticar dependências",acao="dependencies",ferramentas=["dependencies"])
    elif any(x in low for x in ("git","atualizar repositório","pull")):plan.update(objetivo="verificar Git",acao="git",ferramentas=["git"])
    return plan

def agent_tool(action,confirm=False):
    if action not in AGENT_ACTIONS:raise RuntimeError("Ferramenta não autorizada.")
    if action=="status":return diagnose(True)
    if action=="scan":return local_scan()
    if action=="scan_completo":return complete_scan()
    if action=="modelos":return inventory()
    if action=="comfy":return comfy()
    if action=="ollama":return {"online":port(OLLAMA_PORT),"model":choose_model() if port(OLLAMA_PORT) else None,"models":ollama_models()}
    if action=="gpu":return nvidia()
    if action=="git":return repo_report()
    if action=="start_comfy":return {"ok":start_comfy()}
    if action=="start_ollama":return {"ok":start_ollama()}
    if action=="start_webui":return {"ok":start_webui()}
    if action=="dependencies":
        if not confirm:return {"ok":False,"requires_confirmation":True,"message":"Atualização de dependências requer confirmação."}
        update_deps();return {"ok":True}

def agent_decide(message,model=None):
    plan=agent_generation_plan(message)
    if plan["acao"]!="chat":return plan
    model=model or choose_model()
    if not model:return plan
    tools="\n".join(f"- {k}: {v}" for k,v in AGENT_ACTIONS.items())
    prompt=f"Você é o AURION, agente operacional local. Responda em JSON válido, sem markdown.\nPedido: {message}\nFerramentas autorizadas:\n{tools}\nEscolha uma ação apenas se realmente ajudar. Nunca use terminal arbitrário. Formato: {{\"objetivo\":\"...\",\"acao\":\"chat|status|scan|scan_completo|modelos|comfy|ollama|gpu|git|start_comfy|start_ollama|start_webui|dependencies\",\"motivo\":\"...\"}}"
    try:
        r=post_json(f"{OLLAMA_URL}/api/generate",{"model":model,"prompt":prompt,"stream":False,"format":"json","options":{"temperature":0.1,"num_predict":220}},60); obj=json.loads(r.get("response","{}")) if isinstance(r,dict) else {}
        if obj.get("acao") in AGENT_ACTIONS:return obj
    except Exception as e:log(f"Decisão do agente falhou: {e}",True)
    return plan

def agent_vision_model():
    for m in ollama_models():
        name=m.get("name")
        if not name:continue
        try:
            d=post_json(f"{OLLAMA_URL}/api/show",{"model":name},20)
            if "vision" in (d.get("capabilities",[]) if isinstance(d,dict) else []):return name
        except Exception:pass
    for m in ollama_models():
        n=m.get("name","")
        if any(x in n.lower() for x in ("llava","gemma3","qwen")):return n
    return None

def read_reference_text(limit=12000):
    chunks=[]
    for folder in (MEMORY_DIR,MENTE_DIR,FRAG_DIR,REF_INBOX):
        if not folder.exists():continue
        for p in sorted(folder.rglob("*"),key=lambda x:x.stat().st_mtime if x.exists() else 0,reverse=True):
            if not p.is_file() or p.suffix.lower() not in {".txt",".md",".json"}:continue
            try:chunks.append(f"[{p.name}]\n{p.read_text(encoding='utf-8',errors='replace')[:3000]}")
            except Exception:pass
            if sum(map(len,chunks))>=limit:return "\n\n".join(chunks)[:limit]
    return ""

def fetch_link_context(url):
    if not re.match(r"^https?://",str(url or ""),re.I):return {"ok":False,"message":"Use uma URL http/https."}
    try:
        req=urllib.request.Request(str(url),headers={"User-Agent":"Mozilla/5.0 AURION"})
        with urllib.request.urlopen(req,timeout=20) as r:raw=r.read(500000).decode("utf-8",errors="ignore")
        title=re.search(r"<title[^>]*>(.*?)</title>",raw,re.I|re.S);clean=re.sub(r"<script.*?</script>|<style.*?</style>|<[^>]+>"," ",raw,flags=re.I|re.S);clean=re.sub(r"\s+"," ",clean).strip()
        return {"ok":True,"url":str(url),"title":re.sub(r"\s+"," ",title.group(1)).strip() if title else "","text":clean[:12000]}
    except Exception as e:return {"ok":False,"message":str(e)}

def analyze_image_bytes(data,filename="referencia"):
    model=agent_vision_model()
    if not model:return {"ok":False,"message":"Nenhum modelo com visão foi detectado no Ollama."}
    b64=base64.b64encode(data).decode("ascii")
    try:
        r=post_json(f"{OLLAMA_URL}/api/generate",{"model":model,"prompt":"Analise esta referência para produção de imagem/vídeo. Descreva composição, personagem/objeto, câmera, luz, cores, materiais, cenário, continuidade e o que não pode ser alterado. Termine com ficha para prompt.","images":[b64],"stream":False,"keep_alive":"10m","options":{"temperature":0.15,"num_predict":700}},120)
        return {"ok":True,"model":model,"filename":filename,"analysis":clean_agent_reply(r.get("response") if isinstance(r,dict) else r)}
    except Exception as e:return {"ok":False,"message":str(e)}

def discover_workflows():
    roots=[WORKFLOWS,PROJECT/"workflow",Path.home()/"Documents"/"ComfyUI"/"workflows"];c=comfy()
    if c.get("found"):
        cp=Path(c["path"]);roots += [cp/"workflows",cp/"user"/"default"/"workflows",cp.parent/"user"/"default"/"workflows"]
    paths=[];seen=set()
    for root in roots:
        if not root.exists():continue
        try:
            for p in root.rglob("*.json"):
                k=str(p).lower()
                if k not in seen:seen.add(k);paths.append(p)
        except OSError:pass
    out=[]
    for p in sorted(paths,key=lambda x:x.stat().st_mtime if x.exists() else 0,reverse=True)[:200]:
        try:
            d=json.loads(p.read_text(encoding="utf-8",errors="ignore"));kind="api" if isinstance(d,dict) and ("prompt" in d or all(isinstance(v,dict) and "class_type" in v for v in d.values())) else "visual" if isinstance(d,dict) and "nodes" in d else "json";out.append({"name":p.name,"path":str(p),"kind":kind,"size":hsize(p.stat().st_size)})
        except Exception:pass
    return out

def visual_to_api(wf):
    if not isinstance(wf,dict) or "nodes" not in wf:return wf
    links={str(x[0]):x for x in (wf.get("links") or []) if isinstance(x,list) and len(x)>=6};api={}
    for node in wf.get("nodes") or []:
        if not isinstance(node,dict) or node.get("type") in {"MarkdownNote","Note","PrimitiveNode"}:continue
        nid=str(node.get("id"));typ=node.get("type");inputs={};widgets=list(node.get("widgets_values") or []);wi=0
        if not nid or not typ:continue
        for inp in node.get("inputs") or []:
            name=inp.get("name");lid=inp.get("link")
            if not name:continue
            if lid is not None and str(lid) in links:
                lk=links[str(lid)];inputs[name]=[str(lk[1]),int(lk[2])]
            elif inp.get("widget") is not None:
                if wi<len(widgets):inputs[name]=widgets[wi];wi+=1
        api[nid]={"class_type":typ,"inputs":inputs}
    return api

def normalize_video_workflow(data):
    if isinstance(data,str):data=json.loads(data)
    if isinstance(data,dict) and "prompt" in data and isinstance(data["prompt"],dict):return data["prompt"]
    if isinstance(data,dict) and data.get("nodes"):return visual_to_api(data)
    if isinstance(data,dict) and data and all(isinstance(v,dict) and "class_type" in v for v in data.values()):return data
    raise ValueError("Workflow não reconhecido. Use API JSON ou workflow visual do ComfyUI.")

def extract_history_media(hist):
    found=[]
    if not isinstance(hist,dict):return found
    for item in hist.values():
        outputs=item.get("outputs",{}) if isinstance(item,dict) else {}
        for node in outputs.values():
            if not isinstance(node,dict):continue
            for key in ("images","gifs","videos","video"):
                vals=node.get(key,[]); vals=[vals] if isinstance(vals,dict) else vals
                for x in vals if isinstance(vals,list) else []:
                    if isinstance(x,dict) and x.get("filename"):found.append({**x,"media_type":"video" if key!="images" or str(x.get("filename","")).lower().endswith((".mp4",".webm",".mov",".mkv",".gif")) else "image"})
    return found

@app.get("/api/agent/config")
def api_agent_config():return jsonify({"ok":True,"agents":load_agent_config(),"models":[m.get("name") for m in ollama_models() if m.get("name")]})
@app.post("/api/agent/config")
def api_agent_config_save():
    data=request.get_json(silent=True) or {};current=load_agent_config()
    for name,cfg in data.items():
        if name in current and isinstance(cfg,dict):current[name].update({k:cfg[k] for k in ("model","role","enabled","prompt") if k in cfg})
    save_agent_config(current);return jsonify({"ok":True,"agents":current})
@app.get("/api/references/config")
def api_ref_config():return jsonify({"ok":True,**load_ref_config()})
@app.post("/api/references/config")
def api_ref_config_save():
    data=request.get_json(silent=True) or {};roots=[str(Path(x).expanduser()) for x in data.get("roots",[]) if str(x).strip()];REF_CONFIG.write_text(json.dumps({"roots":roots},ensure_ascii=False,indent=2),encoding="utf-8");return jsonify({"ok":True,"roots":roots})
@app.get("/api/references/search")
def api_ref_search():
    q=str(request.args.get("q") or "").strip().lower();limit=max(1,min(500,int(request.args.get("limit",100))));roots=[Path(x) for x in load_ref_config().get("roots",[])];out=[];seen=set()
    for root in roots:
        if not root.exists():continue
        try:
            for p in root.rglob("*"):
                if len(out)>=limit:break
                if not p.is_file() or str(p).lower() in seen:continue
                seen.add(str(p).lower())
                if q and q not in (p.name+" "+str(p.parent)).lower():continue
                if p.suffix.lower() not in {".png",".jpg",".jpeg",".webp",".bmp",".gif",".mp4",".mov",".mkv",".webm",".txt",".md",".json",".pdf"}:continue
                try:out.append({"name":p.name,"path":str(p),"type":p.suffix.lower(),"size":hsize(p.stat().st_size)})
                except OSError:pass
        except OSError:pass
    return jsonify({"ok":True,"results":out})
@app.post("/api/references/upload")
def api_ref_upload():
    f=request.files.get("file")
    if not f:return jsonify({"ok":False,"message":"Nenhum arquivo enviado."}),400
    name=secure_filename(f.filename or "referencia");dest=REF_INBOX/name;dest.parent.mkdir(parents=True,exist_ok=True);f.save(dest);return jsonify({"ok":True,"path":str(dest),"name":name})
@app.get("/api/chips")
def api_chips():
    ensure_agent_config();out=[]
    for p in AGENTS_DIR.rglob("*"):
        if p.is_file() and p.suffix.lower() in {".txt",".md",".json",".png",".jpg",".jpeg",".webp"}:out.append({"name":p.name,"path":str(p),"agent":p.parent.name,"type":p.suffix.lower()})
    return jsonify({"ok":True,"files":out})
@app.post("/api/agent/upload")
def api_agent_upload():
    agent=secure_filename(str(request.form.get("agent") or "AURION")) or "AURION";folder=AGENTS_DIR/agent;folder.mkdir(parents=True,exist_ok=True);saved=[]
    for f in request.files.getlist("files"):
        if f.filename:
            name=secure_filename(f.filename);dest=folder/name;f.save(dest);saved.append(str(dest))
    return jsonify({"ok":True,"saved":saved})
@app.post("/api/agent/decide")
def api_agent_decide():
    data=request.get_json(silent=True) or {};return jsonify({"ok":True,"plan":agent_decide(str(data.get("message") or ""),data.get("model"))})
@app.post("/api/agent/tool")
def api_agent_tool():
    data=request.get_json(silent=True) or {}
    try:return jsonify({"ok":True,"action":data.get("action"),"result":agent_tool(str(data.get("action") or ""),bool(data.get("confirm")))})
    except Exception as e:return jsonify({"ok":False,"message":str(e)}),400
@app.post("/api/agent/prompt")
def api_agent_prompt():
    data=request.get_json(silent=True) or {};goal=str(data.get("prompt") or "").strip();refs=str(data.get("references") or "");url=str(data.get("url") or "").strip();mode=str(data.get("mode") or "refinar")
    if url:refs += "\n\nLINK:\n"+json.dumps(fetch_link_context(url),ensure_ascii=False)[:12000]
    refs += "\n\nMEMÓRIA/MENTE:\n"+read_reference_text(12000);model=str(data.get("model") or choose_model() or "")
    if not model:return jsonify({"ok":False,"message":"Nenhum modelo Ollama disponível."}),503
    system="Você é o agente PROMPT do AURION. Trabalhe em PT-BR. Não invente referências. Transforme o material recebido em um prompt de produção executável. Preserve identidade, continuidade e restrições. Entregue PROMPT FINAL, NEGATIVE, CÂMERA/MOVIMENTO, LUZ/COR e OBSERVAÇÕES."
    try:
        r=post_json(f"{OLLAMA_URL}/api/generate",{"model":model,"system":system,"prompt":f"MODO: {mode}\nOBJETIVO:\n{goal}\nREFERÊNCIAS:\n{refs[:24000]}","stream":False,"keep_alive":"10m","options":{"temperature":0.25,"num_predict":1000}},120)
        return jsonify({"ok":True,"model":model,"result":clean_agent_reply(r.get("response") if isinstance(r,dict) else r)})
    except Exception as e:return jsonify({"ok":False,"message":str(e)}),500
@app.post("/api/agent/analyze-image")
def api_agent_analyze_image():
    f=request.files.get("file")
    if not f:return jsonify({"ok":False,"message":"Envie uma imagem."}),400
    return jsonify(analyze_image_bytes(f.read(),f.filename))
@app.post("/api/video/upload")
def api_video_upload():
    f=request.files.get("file")
    if not f:return jsonify({"ok":False,"message":"Nenhuma referência enviada."}),400
    name=secure_filename(f.filename or "video_ref");dest=REF_INBOX/name;dest.parent.mkdir(parents=True,exist_ok=True);f.save(dest);return jsonify({"ok":True,"path":str(dest),"name":name})

@app.get("/api/video/workflows")
def api_video_workflows():return jsonify({"ok":True,"workflows":discover_workflows()})
@app.post("/api/video/prepare")
def api_video_prepare():
    data=request.get_json(silent=True) or {}
    try:
        wf=normalize_video_workflow(data.get("workflow"));info=http_json(f"{COMFY_URL}/object_info",30) if port(COMFY_PORT) else None;missing=[]
        if isinstance(info,dict):missing=[str(v.get("class_type")) for v in wf.values() if isinstance(v,dict) and v.get("class_type") not in info]
        return jsonify({"ok":True,"nodes":len(wf),"missing_nodes":sorted(set(missing)),"workflow":wf})
    except Exception as e:return jsonify({"ok":False,"message":str(e)}),400
@app.get("/api/video/workflow/load")
def api_video_workflow_load():
    raw=str(request.args.get("path") or "")
    if not raw:return jsonify({"ok":False,"message":"Caminho não informado."}),400
    try:
        path=Path(raw).resolve()
        allowed=[WORKFLOWS.resolve(),PROJECT.resolve()]
        if not any(safe_inside(a,path) for a in allowed):return jsonify({"ok":False,"message":"Workflow fora da base autorizada."}),403
        if not path.exists() or path.suffix.lower()!='.json':return jsonify({"ok":False,"message":"Workflow não encontrado."}),404
        data=json.loads(path.read_text(encoding="utf-8",errors="ignore"))
        return jsonify({"ok":True,"name":path.name,"kind":"visual" if isinstance(data,dict) and "nodes" in data else "api","workflow":data})
    except Exception as e:return jsonify({"ok":False,"message":str(e)}),400

@app.post("/api/video/generate")
def api_video_generate():
    data=request.get_json(silent=True) or {}
    if not port(COMFY_PORT):return jsonify({"ok":False,"message":"ComfyUI offline."}),503
    try: wf=normalize_video_workflow(data.get("workflow"))
    except Exception as e:return jsonify({"ok":False,"message":str(e)}),400
    info=http_json(f"{COMFY_URL}/object_info",30) or {};missing=[str(v.get("class_type")) for v in wf.values() if isinstance(v,dict) and v.get("class_type") not in info]
    if missing:return jsonify({"ok":False,"message":"Nós ausentes no ComfyUI.","missing_nodes":sorted(set(missing))}),400
    try:
        client_id=f"aurion-video-{int(time.time()*1000)}";r=post_json(f"{COMFY_URL}/prompt",{"prompt":wf,"client_id":client_id},60);pid=r.get("prompt_id") if isinstance(r,dict) else None
        if not pid:return jsonify({"ok":False,"message":"ComfyUI não retornou prompt_id.","result":r}),500
        with LOCK:STATE["video_job"]={"prompt_id":pid,"client_id":client_id,"started":time.time()}
        log(f"Vídeo enviado ao ComfyUI: {pid}");return jsonify({"ok":True,"prompt_id":pid,"client_id":client_id})
    except Exception as e:log(f"Falha vídeo: {e}",True);return jsonify({"ok":False,"message":str(e)}),500
@app.get("/api/video/progress/<prompt_id>")
def api_video_progress(prompt_id):
    hist=comfy_history(prompt_id)
    if isinstance(hist,dict) and prompt_id in hist:return jsonify({"ok":True,"status":"concluido","progress":100,"media":extract_history_media(hist),"history":hist})
    q=http_json(f"{COMFY_URL}/queue",5) or {};running=q.get("queue_running",[]) if isinstance(q,dict) else [];pending=q.get("queue_pending",[]) if isinstance(q,dict) else [];status="executando" if any(isinstance(x,list) and len(x)>1 and x[1]==prompt_id for x in running) else "fila" if any(isinstance(x,list) and len(x)>1 and x[1]==prompt_id for x in pending) else "processando"
    with LOCK:job=STATE.get("video_job",{}).copy()
    elapsed=max(0,time.time()-float(job.get("started",time.time())));return jsonify({"ok":True,"status":status,"progress":min(95,int(elapsed/5)),"elapsed":round(elapsed,1),"media":[]})

# ---------------- API ----------------
@app.get("/")
def index():return render_template_string(HTML)
@app.get("/api/status")
def api_status():
    d=diagnose()
    with LOCK:s={"busy":STATE["busy"],"operation":STATE["operation"],"progress":STATE["progress"],"message":STATE["message"],"logs":STATE["logs"][-100:],"errors":STATE["errors"][-60:],"agent_model":STATE.get("agent_model"),"startup_done":STATE["startup_done"],"startup":STATE["startup"],"scan":STATE.get("scan"),"image_job":STATE.get("image_job") }
    return jsonify({"diagnostics":d,"state":s})
@app.get("/api/diagnose")
def api_diag():return jsonify(diagnose())
@app.get("/api/models")
def api_models():return jsonify({"local":inventory(),"folders":model_folders(),"ollama":ollama_models(),"agent_model":choose_model() if port(OLLAMA_PORT) else None})
@app.post("/api/agent/model")
def api_agent_model():
    m=str((request.get_json(silent=True) or {}).get("model","")).strip();names=[x.get("name") for x in ollama_models()]
    if m not in names:return jsonify({"ok":False,"message":"Modelo Ollama não encontrado."}),404
    with LOCK:STATE["agent_model"]=m
    log(f"Agente carregado: {m}");return jsonify({"ok":True,"model":m})
@app.post("/api/chat")
def api_chat():
    data=request.get_json(silent=True) or {};msg=str(data.get("message","")).strip();m=str(data.get("model","")).strip() or None
    if not msg:return jsonify({"reply":"Digite uma pergunta ou comando."})
    low=msg.lower()
    if low in {"status","diagnostico","diagnóstico"}:
        d=diagnose();return jsonify({"reply":f"AGENTE: {d['ollama']['model'] or 'não carregado'} | ComfyUI: {'ONLINE' if d['comfy']['running'] else 'OFFLINE'} | Ollama: {'ONLINE' if d['ollama']['running'] else 'OFFLINE'} | NVIDIA: {len(d['nvidia'].get('gpus',[]))} GPU(s) | Modelos: {d['models_inventory']['total']}"})
    if low in {"comfy","comfyui"}:
        c=comfy();return jsonify({"reply":f"ComfyUI: {'encontrado' if c['found'] else 'não encontrado'} | {c.get('path') or '-'} | ONLINE={c['running']}"})
    if low=="modelos":
        i=inventory();return jsonify({"reply":f"{i['total']} modelos locais — {i['size']} em {MODELS}"})
    if low in {"cuda","nvidia","gpu"}:return jsonify({"reply":json.dumps(nvidia(),ensure_ascii=False,indent=2)})
    if low=="git":return jsonify({"reply":json.dumps(repo_report(),ensure_ascii=False,indent=2)})
    if low in {"cmd","terminal"}:open_cmd();return jsonify({"reply":"CMD aberto."})
    ai,err=chat(msg,m)
    return jsonify({"reply":ai or f"Agente indisponível: {err or 'erro desconhecido'}","model":STATE.get("agent_model")})
@app.post("/api/setup")
def api_setup():return (jsonify({"ok":True,"message":"Correção completa iniciada."}) if bg("Correção completa",full_setup) else (jsonify({"ok":False,"message":"Outra operação já está em andamento."}),409))
@app.post("/api/restart-services")
def api_restart():return (jsonify({"ok":True}) if bg("Recarregar serviços",startup) else (jsonify({"ok":False}),409))
@app.post("/api/start/<service>")
def api_start(service):
    fn={"comfy":start_comfy,"ollama":start_ollama,"openwebui":start_webui}.get(service)
    if not fn:return jsonify({"ok":False}),404
    return (jsonify({"ok":True}) if bg("Iniciar "+service,fn) else (jsonify({"ok":False}),409))
@app.post("/api/open/<service>")
def api_open(service):
    u={"comfy":COMFY_URL,"ollama":OLLAMA_URL,"openwebui":OPENWEBUI_URL,"panel":f"http://{HOST}:{PORT}"}.get(service)
    if not u:return jsonify({"ok":False}),404
    webbrowser.open(u);log(f"Abrindo {service}: {u}");return jsonify({"ok":True})
@app.post("/api/cmd")
def api_cmd():return jsonify({"ok":open_cmd()})
@app.post("/api/configure-models")
def api_cfg():return (jsonify({"ok":True}) if bg("Configurar modelos",configure_comfy) else (jsonify({"ok":False}),409))
@app.post("/api/dependencies")
def api_dep():return (jsonify({"ok":True}) if bg("Dependências",update_deps) else (jsonify({"ok":False}),409))
@app.post("/api/download-comfy")
def api_down():return (jsonify({"ok":True}) if bg("Baixar ComfyUI",install_comfy) else (jsonify({"ok":False}),409))
@app.post("/api/git/comfy-update")
def api_git_comfy():return (jsonify({"ok":True}) if bg("Atualizar ComfyUI via Git",update_comfy_git) else (jsonify({"ok":False}),409))
@app.post("/api/git/update")
def api_git_update():
    p=Path(str(request.args.get("path") or PROJECT))
    return (jsonify({"ok":True}) if bg("Git Pull",git_pull,p) else (jsonify({"ok":False}),409))
@app.get("/api/git")
def api_git():return jsonify({"repos":repo_report(),"project":git_status(PROJECT)})
@app.get("/api/comfy/stats")
def api_stats():
    x=comfy_stats()
    if x is None:return jsonify({"ok":False,"message":"ComfyUI offline."}),503
    return jsonify({"ok":True,"stats":x})
@app.post("/api/comfy/queue")
def api_queue():
    data=request.get_json(silent=True) or {};text=str(data.get("workflow","")).strip()
    if not text:return jsonify({"ok":False,"message":"Cole o workflow/API JSON do ComfyUI."}),400
    if not port(COMFY_PORT):return jsonify({"ok":False,"message":"ComfyUI offline."}),503
    try:
        wf=json.loads(text)
        if not isinstance(wf,dict):raise ValueError("O JSON precisa ser um objeto.")
        # O endpoint /prompt aceita o formato API: {node_id: {class_type, inputs}}.
        # Se o usuário colar o JSON já encapsulado, preservamos o campo prompt.
        if "prompt" in wf and isinstance(wf.get("prompt"),dict):
            payload=wf
        elif "nodes" in wf and "links" in wf:
            raise ValueError("Você colou o workflow visual do ComfyUI. Exporte pelo menu 'Save (API Format)' e cole o JSON API aqui.")
        elif all(isinstance(v,dict) and "class_type" in v for v in wf.values()):
            payload={"prompt":wf}
        else:
            raise ValueError("Formato não reconhecido. Use o JSON exportado em 'Save (API Format)' no ComfyUI.")
        r=post_json(f"{COMFY_URL}/prompt",payload,60)
        log(f"Workflow enviado ao ComfyUI: {r}")
        return jsonify({"ok":True,"result":r})
    except Exception as e:
        log(f"Workflow inválido/falha: {type(e).__name__}: {e}",True)
        return jsonify({"ok":False,"message":str(e)}),500 if "HTTP " in str(e) else 400

# ---------------- Memória / MENTE ----------------
def safe_filename(name,default="memoria"):
    name=str(name or "").strip() or default
    keep="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_ ."
    name="".join(c if c in keep else "_" for c in name).strip(" ._") or default
    return name if name.lower().endswith(".md") else name+".md"

def list_memory_files():
    out=[]
    for folder,label in ((MEMORY_DIR,"memoria"),(MENTE_DIR,"mente"),(FRAG_DIR,"fragmentos")):
        if not folder.exists(): continue
        for p in folder.glob("*.md"):
            try: out.append({"name":p.name,"path":str(p),"category":label,"size":p.stat().st_size,"modified":datetime.fromtimestamp(p.stat().st_mtime).strftime("%d/%m/%Y %H:%M")})
            except OSError: pass
    return sorted(out,key=lambda x:x["modified"],reverse=True)

def comfy_checkpoint_choices():
    if not port(COMFY_PORT): return []
    d=http_json(f"{COMFY_URL}/object_info",15)
    try:
        vals=d["CheckpointLoaderSimple"]["input"] ["required"]["ckpt_name"][0]
        return [str(x) for x in vals if x]
    except Exception: return []

def build_sdxl_workflow(prompt,negative,checkpoint,width,height,steps,cfg,seed):
    if seed<0: seed=int(time.time()*1000)%2147483647
    return {
      "3":{"class_type":"KSampler","inputs":{"seed":seed,"steps":steps,"cfg":cfg,"sampler_name":"euler","scheduler":"normal","denoise":1.0,"model":["4",0],"positive":["6",0],"negative":["7",0],"latent_image":["5",0]}},
      "4":{"class_type":"CheckpointLoaderSimple","inputs":{"ckpt_name":checkpoint}},
      "5":{"class_type":"EmptyLatentImage","inputs":{"width":width,"height":height,"batch_size":1}},
      "6":{"class_type":"CLIPTextEncode","inputs":{"text":prompt,"clip":["4",1]}},
      "7":{"class_type":"CLIPTextEncode","inputs":{"text":negative,"clip":["4",1]}},
      "8":{"class_type":"VAEDecode","inputs":{"samples":["3",0],"vae":["4",2]}},
      "9":{"class_type":"SaveImage","inputs":{"filename_prefix":"AURION" ,"images":["8",0]}}
    }

def comfy_history(prompt_id):
    return http_json(f"{COMFY_URL}/history/{prompt_id}",5)

def extract_history_images(hist):
    found=[]
    if not isinstance(hist,dict): return found
    for item in hist.values():
        outputs=item.get("outputs",{}) if isinstance(item,dict) else {}
        for node in outputs.values():
            for img in node.get("images",[]) if isinstance(node,dict) else []:
                if isinstance(img,dict) and img.get("filename"):
                    found.append(img)
    return found

@app.get("/api/memory/list")
def api_memory_list(): return jsonify({"ok":True,"files":list_memory_files()})
@app.post("/api/memory/save")
def api_memory_save():
    data=request.get_json(silent=True) or {}; title=safe_filename(data.get("title")); content=str(data.get("content") or "").strip()
    if not content:return jsonify({"ok":False,"message":"Digite o conteúdo da memória."}),400
    path=MEMORY_DIR/title; path.write_text(content,encoding="utf-8"); log(f"Memória salva: {path.name}"); return jsonify({"ok":True,"path":str(path),"message":"Memória salva."})
@app.post("/api/memory/load")
def api_memory_load():
    data=request.get_json(silent=True) or {}; raw=str(data.get("path") or "");
    if not raw:return jsonify({"ok":False,"message":"Caminho não informado."}),400
    try: path=Path(raw).resolve(); path.relative_to(PROJECT.resolve())
    except Exception:return jsonify({"ok":False,"message":"Arquivo fora da base do AURION."}),403
    if not path.exists() or not path.is_file():return jsonify({"ok":False,"message":"Memória não encontrada."}),404
    return jsonify({"ok":True,"path":str(path),"content":path.read_text(encoding="utf-8",errors="replace")[:200000]})
@app.post("/api/agent/load")
def api_agent_load():
    data=request.get_json(silent=True) or {}; requested=str(data.get("model") or "").strip()
    if not start_ollama():return jsonify({"ok":False,"message":"Ollama não está disponível."}),503
    names=[x.get("name") for x in ollama_models() if x.get("name")]
    model=requested if requested in names else choose_model()
    if not model:return jsonify({"ok":False,"message":"Nenhum modelo Ollama encontrado."}),404
    with LOCK: STATE["agent_model"]=model
    try:
        post_json(f"{OLLAMA_URL}/api/generate",{"model":model,"prompt":"Responda apenas OK.","stream":False,"keep_alive":"10m","options":{"num_predict":2,"temperature":0}},30)
        log(f"Agente carregado e aquecido: {model}"); return jsonify({"ok":True,"model":model,"message":f"Agente carregado: {model}"})
    except Exception as e:log(f"Falha ao aquecer agente: {e}",True);return jsonify({"ok":False,"message":str(e)}),500

@app.get("/api/image/options")
def api_image_options():
    choices=comfy_checkpoint_choices()
    if not choices:
        i=inventory(); choices=[x["path"] for x in i.get("files",[]) if x.get("ext")==".safetensors" and "checkpoints" in x.get("path","").lower()]
    return jsonify({"ok":True,"checkpoints":choices,"running":port(COMFY_PORT)})

@app.post("/api/image/generate")
def api_image_generate():
    data=request.get_json(silent=True) or {}
    prompt=str(data.get("prompt") or "").strip(); negative=str(data.get("negative") or "low quality, blurry, distorted, duplicate, watermark").strip()
    if not prompt:return jsonify({"ok":False,"message":"Digite o prompt da imagem."}),400
    if not port(COMFY_PORT):return jsonify({"ok":False,"message":"ComfyUI offline."}),503
    choices=comfy_checkpoint_choices(); checkpoint=str(data.get("checkpoint") or "").strip()
    if not checkpoint and choices: checkpoint=choices[0]
    if not checkpoint: return jsonify({"ok":False,"message":"Nenhum checkpoint foi encontrado no ComfyUI."}),400
    try:
        width=max(256,min(2048,int(data.get("width",1024)))); height=max(256,min(2048,int(data.get("height",1024)))); steps=max(1,min(100,int(data.get("steps",28)))); cfg=max(0.1,min(30,float(str(data.get("cfg",7)).replace(",",".")))); seed=int(data.get("seed",-1))
    except Exception:return jsonify({"ok":False,"message":"Parâmetros de geração inválidos."}),400
    wf=build_sdxl_workflow(prompt,negative,checkpoint,width,height,steps,cfg,seed)
    try:
        client_id=f"aurion-{int(time.time()*1000)}"
        r=post_json(f"{COMFY_URL}/prompt",{"prompt":wf,"client_id":client_id},30)
        pid=r.get("prompt_id") if isinstance(r,dict) else None
        if not pid:return jsonify({"ok":False,"message":"ComfyUI não retornou prompt_id.","result":r}),500
        with LOCK: STATE["image_job"]={"prompt_id":pid,"client_id":client_id,"prompt":prompt,"started":time.time(),"steps":steps,"checkpoint":checkpoint}
        log(f"Geração iniciada: {pid} | {checkpoint}")
        return jsonify({"ok":True,"prompt_id":pid,"client_id":client_id,"steps":steps,"checkpoint":checkpoint})
    except Exception as e:log(f"Falha ao iniciar geração: {e}",True);return jsonify({"ok":False,"message":str(e)}),500

@app.get("/api/image/progress/<prompt_id>")
def api_image_progress(prompt_id):
    hist=comfy_history(prompt_id)
    if isinstance(hist,dict) and prompt_id in hist:
        imgs=extract_history_images(hist)
        with LOCK: STATE["image_job"]={**STATE.get("image_job",{}),"done":True,"progress":100,"images":imgs}
        return jsonify({"ok":True,"status":"concluido","progress":100,"images":imgs,"history":hist})
    q=http_json(f"{COMFY_URL}/queue",5) or {}
    running=q.get("queue_running",[]) if isinstance(q,dict) else []; pending=q.get("queue_pending",[]) if isinstance(q,dict) else []
    if any(isinstance(x,list) and len(x)>1 and x[1]==prompt_id for x in running): status="executando"
    elif any(isinstance(x,list) and len(x)>1 and x[1]==prompt_id for x in pending): status="fila"
    else: status="processando"
    with LOCK: job=STATE.get("image_job",{}).copy()
    started=float(job.get("started",time.time())); elapsed=max(0,time.time()-started); steps=int(job.get("steps",28)); estimate=max(8,steps*1.8); pct=min(95,int((elapsed/estimate)*95))
    return jsonify({"ok":True,"status":status,"progress":pct,"elapsed":round(elapsed,1),"images":[]})

# ---------------- Scan / organização ----------------
SCAN_EXT={
    "codigo": {".py",".js",".ts",".jsx",".tsx",".ps1",".bat",".cmd",".sh",".cpp",".c",".h",".hpp",".java",".cs"},
    "imagem": {".png",".jpg",".jpeg",".webp",".bmp",".gif",".tif",".tiff",".psd",".ai",".svg"},
    "video": {".mp4",".mov",".mkv",".avi",".webm",".m4v",".mts"},
    "audio": {".mp3",".wav",".flac",".ogg",".m4a",".aac"},
    "documento": {".pdf",".doc",".docx",".txt",".md",".rtf",".odt"},
    "planilha": {".xlsx",".xls",".csv",".ods"},
    "projeto": {".aep",".aet",".c4d",".blend",".prproj",".drp",".fcpxml",".psd",".ai"},
    "workflow": {".json",".yaml",".yml",".workflow"},
    "modelo": MODEL_EXT,
}
CLIENT_HINTS=("cliente","clientes","client","clients","tomim","banda","marca","empresa","contrato","orcamento","orçamento")
PROJECT_HINTS=("projeto","projetos","project","projects","job","jobs","campanha","campanhas","video","vídeo","clipe","clip","animfruts","frutinhas","storyboard","render","3d","ensaio","fotografia","foto")
IGNORE_SCAN=IGNORE | {"cache","temp","tmp","__pycache__","venv",".venv","dist","build"}

def classify_path(path: Path, root: Path, is_dir=False):
    text=" ".join(path.parts).lower()
    name=path.name.lower()
    ext=path.suffix.lower()
    if is_dir:
        if any(k in text for k in CLIENT_HINTS): return "cliente"
        if any(k in text for k in PROJECT_HINTS): return "projeto"
        return "pasta"
    for cat,exts in SCAN_EXT.items():
        if ext in exts: return cat
    if name.startswith("client_") or "cliente" in text: return "cliente"
    return "outro"

def scan_roots(roots, label="SCAN"):
    result={"timestamp":datetime.now().isoformat(timespec="seconds"),"label":label,"arquivos":0,"pastas":0,"bytes":0,"por_tipo":{},"alvos":[],"clientes":{},"projetos":{},"repositorios":[],"arquivos_destaque":[],"erros":[],"catalogo_completo":False}
    normalized=[]
    for root in roots:
        try:r=Path(root).resolve()
        except Exception:continue
        if not r.exists() or not r.is_dir():continue
        if any(r==x or safe_inside(x,r) for x in normalized):continue
        normalized=[x for x in normalized if not safe_inside(r,x)]
        normalized.append(r)
    normalized.sort(key=lambda x:len(x.parts)); result["alvos"]=[str(x) for x in normalized]
    seen_files=set(); entity_dirs=[]; top=[]; processed=0
    SCAN_DIR.mkdir(parents=True,exist_ok=True)
    try:SCAN_JSONL.unlink(missing_ok=True)
    except Exception:pass
    def add_entity(kind,name,path):
        rp=path.resolve(); key=(kind,name.lower(),str(rp).lower())
        if any((a,b.lower(),str(c).lower())==key for a,b,c in entity_dirs):return
        d=result[kind].setdefault(name,{"pasta":str(path),"arquivos":0,"bytes":0,"tipo":kind[:-1],"confianca":0})
        d["confianca"]=max(d.get("confianca",0),80 if kind=="clientes" else 70); entity_dirs.append((kind,name,rp))
    for root in normalized:
        try:
            for cur,dirs,files in os.walk(root,topdown=True):
                curp=Path(cur); dirs[:]=[d for d in dirs if d not in IGNORE_SCAN and not d.startswith('.')]; result["pastas"]+=len(dirs)
                if (curp/".git").is_dir():result["repositorios"].append(str(curp))
                for d in dirs:
                    dp=curp/d; low=d.lower()
                    if low in {"clientes","cliente","clients","client"}:continue
                    if any(k in low for k in CLIENT_HINTS):add_entity("clientes",d,dp)
                    if any(k in low for k in PROJECT_HINTS):add_entity("projetos",d,dp)
                for fn in files:
                    fp=curp/fn
                    try:fpr=fp.resolve()
                    except Exception:fpr=fp
                    key=str(fpr).lower()
                    if key in seen_files:continue
                    seen_files.add(key); processed+=1
                    try:size=fp.stat().st_size
                    except (OSError,PermissionError) as e:result["erros"].append(f"{fp}: {e}");continue
                    result["arquivos"]+=1; result["bytes"]+=size; cat=classify_path(fp,root); result["por_tipo"][cat]=result["por_tipo"].get(cat,0)+1
                    associations=[]
                    for kind,name,ep in entity_dirs:
                        try:
                            fpr.relative_to(ep); result[kind][name]["arquivos"]+=1; result[kind][name]["bytes"]+=size; associations.append({"tipo":kind[:-1],"nome":name})
                        except ValueError:pass
                    row={"nome":fn,"caminho":str(fp),"tipo":cat,"bytes":size,"tamanho":hsize(size),"ext":fp.suffix.lower(),"clientes":[a["nome"] for a in associations if a["tipo"]=="cliente"],"projetos":[a["nome"] for a in associations if a["tipo"]=="projeto"]}
                    try:
                        with SCAN_JSONL.open("a",encoding="utf-8") as jf:jf.write(json.dumps(row,ensure_ascii=False)+"\n")
                    except Exception as e:result["erros"].append(f"JSONL {fp}: {e}")
                    top.append(row); top.sort(key=lambda x:x["bytes"],reverse=True); del top[500:]
                    if processed%250==0:progress(min(95,max(5,(processed%9500)//100+5)),f"{label}: {processed:,} arquivos indexados...")
        except (PermissionError,OSError) as e:result["erros"].append(f"{root}: {e}")
    result["tamanho"]=hsize(result["bytes"]); result["clientes"]=dict(sorted(result["clientes"].items(),key=lambda x:(-x[1]["arquivos"],x[0].lower()))); result["projetos"]=dict(sorted(result["projetos"].items(),key=lambda x:(-x[1]["arquivos"],x[0].lower()))); result["repositorios"]=sorted(set(result["repositorios"])); result["arquivos_destaque"]=top; result["catalogo_completo"]=True; result["catalogo_arquivo"]=str(SCAN_JSONL); result["catalogo_registros"]=result["arquivos"]
    try:SCAN_REPORT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    except Exception as e:result["erros"].append(f"Não foi possível salvar relatório: {e}")
    return result

def local_scan():
    home=Path.home()
    roots=[PROJECT,home/"Desktop",home/"Documents",home/"Downloads"]
    return scan_roots(roots,"LOCAL")

def complete_scan():
    drives=[Path(f"{x}:\\") for x in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if Path(f"{x}:\\").exists()]
    return scan_roots(drives,"COMPLETO")

@app.post("/api/scan")
def api_scan():
    def job():
        progress(5,"SCAN LOCAL: indexando projetos, clientes e arquivos...")
        r=local_scan()
        with LOCK: STATE["scan"]=r
        progress(100,f"Scan local finalizado: {r['arquivos']} arquivos.")
        log(f"Scan local: {r['arquivos']} arquivos | {len(r['clientes'])} clientes | {len(r['projetos'])} projetos")
    return (jsonify({"ok":True}) if bg("Scan local",job) else (jsonify({"ok":False}),409))

@app.post("/api/scan-completo")
def api_scan_completo():
    def job():
        progress(2,"SCAN COMPLETO: examinando discos...")
        r=complete_scan()
        with LOCK: STATE["scan"]=r
        progress(100,f"Scan completo finalizado: {r['arquivos']} arquivos.")
        log(f"Scan completo: {r['arquivos']} arquivos | {len(r['clientes'])} clientes | {len(r['projetos'])} projetos")
    return (jsonify({"ok":True}) if bg("Scan completo",job) else (jsonify({"ok":False}),409))

@app.get("/api/scan/report")
def api_scan_report():
    if not SCAN_REPORT.exists(): return jsonify({"ok":False,"message":"Nenhum scan salvo ainda."}),404
    try: return jsonify(json.loads(SCAN_REPORT.read_text(encoding="utf-8")))
    except Exception as e: return jsonify({"ok":False,"message":str(e)}),500

@app.get("/api/scan/search")
def api_scan_search():
    q=str(request.args.get("q") or "").strip().lower(); client=str(request.args.get("client") or "").strip().lower(); project=str(request.args.get("project") or "").strip().lower(); typ=str(request.args.get("type") or "").strip().lower(); limit=max(1,min(500,int(request.args.get("limit",100))))
    if not SCAN_JSONL.exists(): return jsonify({"ok":False,"message":"Execute um scan primeiro.","results":[]}),404
    out=[]
    try:
        with SCAN_JSONL.open("r",encoding="utf-8",errors="ignore") as f:
            for line in f:
                try:r=json.loads(line)
                except Exception:continue
                if q and q not in (r.get("nome","")+" "+r.get("caminho","")).lower():continue
                if client and client not in " ".join(r.get("clientes",[])).lower():continue
                if project and project not in " ".join(r.get("projetos",[])).lower():continue
                if typ and typ!=str(r.get("tipo","")).lower():continue
                out.append(r)
                if len(out)>=limit:break
    except Exception as e:return jsonify({"ok":False,"message":str(e),"results":[]}),500
    return jsonify({"ok":True,"total":len(out),"results":out})

HTML=r'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AURION DYNAMIC</title><style>
:root{--bg:#080c11;--side:#0d141d;--p:#111a25;--p2:#172231;--line:#253446;--txt:#eef5ff;--muted:#8ea0b5;--cyan:#55c8ff;--ok:#4cda86;--warn:#ffd166;--bad:#ff6277}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--txt);font:14px Segoe UI,Arial,sans-serif;overflow:hidden}.app{display:flex;height:100vh}.side{width:245px;flex:none;background:var(--side);border-right:1px solid var(--line);padding:18px 12px;overflow:auto}.brand{font-size:22px;font-weight:800;padding:6px 10px}.brand small{display:block;font-size:10px;color:var(--muted);letter-spacing:2px;margin-top:4px}.nav{margin-top:18px}.nav button{width:100%;text-align:left;margin:4px 0;padding:11px 12px;background:transparent;border:1px solid transparent;color:var(--muted);border-radius:9px;cursor:pointer;font-weight:600}.nav button:hover,.nav button.active{background:var(--p2);border-color:var(--line);color:var(--txt)}.side-status{margin-top:18px;padding:12px;border:1px solid var(--line);border-radius:10px;background:#0a1119}.dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--bad);margin-right:7px}.dot.ok{background:var(--ok)}.main{flex:1;min-width:0;display:flex;flex-direction:column}.top{height:64px;flex:none;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;padding:0 22px;background:#0b1118}.title{font-size:17px;font-weight:700}.topright{color:var(--muted)}.content{flex:1;overflow:auto;padding:20px}.tab{display:none;max-width:1500px;margin:auto}.tab.active{display:block}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.grid2{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}.card{background:var(--p);border:1px solid var(--line);border-radius:13px;padding:15px;margin-bottom:14px}.card h3{margin:0 0 11px;font-size:13px;color:var(--muted);letter-spacing:.4px}.big{font-size:21px;font-weight:800}.hero{padding:18px;border:1px solid var(--line);border-radius:14px;background:linear-gradient(135deg,#101a26,#0c121a);margin-bottom:14px}.hero h2{margin:0 0 6px}.hero p{margin:0;color:var(--muted)}button.action{background:var(--p2);border:1px solid var(--line);color:var(--txt);padding:10px 12px;border-radius:9px;cursor:pointer;font-weight:600;margin:3px}button.action:hover{border-color:var(--cyan)}button.primary{border-color:var(--cyan);background:#102b3b}.actions{display:flex;flex-wrap:wrap;gap:4px}.bar{height:10px;background:#202b38;border-radius:99px;overflow:hidden}.fill{height:100%;width:0;background:var(--cyan);transition:.25s}.row{display:flex;gap:9px;align-items:center}.row>*{flex:1}input,select,textarea{width:100%;background:#080e15;color:var(--txt);border:1px solid var(--line);border-radius:8px;padding:10px;outline:none}textarea{min-height:240px;font:12px Consolas,monospace}.chatlog{height:440px;overflow:auto;background:#080d13;border:1px solid var(--line);border-radius:10px;padding:13px;margin-bottom:10px}.msg{padding:9px 11px;border-radius:9px;margin:7px 0;white-space:pre-wrap;word-break:break-word}.user{background:#13283a}.agent{background:#151d28}.sys{background:#241d12;color:var(--warn)}pre{background:#080d13;border:1px solid var(--line);border-radius:10px;padding:12px;max-height:420px;overflow:auto;white-space:pre-wrap;word-break:break-word;font:12px Consolas,monospace}label{display:block;color:var(--muted);font-size:12px;margin:9px 0 5px}.progressbox{margin-top:18px;padding:12px;border:1px solid var(--line);border-radius:10px;background:#09111a}.result{min-height:280px;display:flex;align-items:center;justify-content:center;text-align:center;color:var(--muted);flex-wrap:wrap}.pill{display:inline-block;padding:3px 7px;border-radius:99px;border:1px solid var(--line);color:var(--muted);font-size:11px}.model-list{max-height:420px;overflow:auto}.model{display:flex;justify-content:space-between;align-items:center;padding:9px;border-bottom:1px solid var(--line)}.model span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.floating-chat{position:fixed;right:18px;bottom:18px;width:420px;height:520px;min-width:300px;min-height:220px;max-width:80vw;max-height:80vh;resize:both;overflow:hidden;background:#0c141e;border:1px solid var(--cyan);border-radius:14px;box-shadow:0 16px 60px #000a;z-index:9999;display:flex;flex-direction:column}.floating-chat.min{height:52px!important;width:330px!important;resize:none}.fc-head{height:52px;flex:none;display:flex;align-items:center;justify-content:space-between;padding:0 12px;background:#111c29;border-bottom:1px solid var(--line);cursor:move}.fc-body{flex:1;min-height:0;display:flex;flex-direction:column;padding:10px}.fc-log{flex:1;min-height:0;overflow:auto}.fc-input{display:flex;gap:7px;margin-top:8px}.fc-input input{min-width:0}.agent-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}.agent-box{padding:12px;border:1px solid var(--line);border-radius:10px;background:#0b121a}.drop{border:1px dashed #3c5870;padding:20px;border-radius:10px;text-align:center;color:var(--muted)}video.media{max-width:100%;max-height:520px;border-radius:10px;margin:6px}img.media{max-width:100%;max-height:520px;border-radius:10px}@media(max-width:950px){.side{width:195px}.grid{grid-template-columns:repeat(2,1fr)}}@media(max-width:650px){.side{width:64px;padding:10px 5px}.brand{font-size:0}.brand:before{content:'⚡';font-size:24px}.nav button{font-size:0;text-align:center}.grid,.grid2,.agent-grid{grid-template-columns:1fr}.topright{display:none}.floating-chat{right:6px;bottom:6px;width:calc(100vw - 12px);max-width:none}}
</style></head><body><div class="app"><aside class="side"><div class="brand">⚡ AURION<small>DYNAMIC LOCAL CORE</small></div><div class="nav">
<button class="active" onclick="tab('home',this)">⌂ &nbsp; PAINEL</button><button onclick="tab('chat',this)">◉ &nbsp; AGENTE / CHAT</button><button onclick="tab('prompt',this)">✦ &nbsp; AGENTE / PROMPT</button><button onclick="tab('models',this)">◆ &nbsp; MODELOS</button><button onclick="tab('scan',this)">▦ &nbsp; SCAN / PROJETOS</button><button onclick="tab('image',this)">▣ &nbsp; GERAR IMAGEM</button><button onclick="tab('video',this)">▶ &nbsp; GERAR VÍDEO</button><button onclick="tab('agents',this)">♟ &nbsp; AGENTES DA FIRMA</button><button onclick="tab('refs',this)">⌕ &nbsp; REFERÊNCIAS</button><button onclick="tab('render',this)">◈ &nbsp; RENDER / CUDA</button><button onclick="tab('repo',this)">⌘ &nbsp; REPOSITÓRIO / GIT</button><button onclick="tab('drivers',this)">⚙ &nbsp; DRIVERS / DEP.</button><button onclick="tab('cmd',this)">▤ &nbsp; CMD</button><button onclick="tab('logs',this)">☷ &nbsp; LOG / ERROS</button></div><div class="side-status"><div><span id="dotA" class="dot"></span>Agente <b id="sideAgent">...</b></div><div style="margin-top:8px"><span id="dotC" class="dot"></span>ComfyUI</div><div style="margin-top:8px"><span id="dotG" class="dot"></span>NVIDIA</div></div></aside><main class="main"><header class="top"><div class="title" id="title">PAINEL</div><div class="topright" id="global">Carregando núcleo...</div></header><div class="content">
<section id="home" class="tab active"><div class="hero"><h2>AURION DYNAMIC</h2><p>Central local: agente + modelos + ComfyUI + produção + referências + manutenção.</p></div><div class="grid"><div class="card"><h3>AGENTE</h3><div id="hA" class="big">...</div><small>Ollama</small></div><div class="card"><h3>COMFYUI</h3><div id="hC" class="big">...</div><small id="hCP">...</small></div><div class="card"><h3>NVIDIA / CUDA</h3><div id="hG" class="big">...</div><small id="hGN">...</small></div><div class="card"><h3>MODELOS</h3><div id="hM" class="big">...</div><small id="hMS">...</small></div></div><div class="card"><h3>CARREGAMENTO</h3><div id="op">...</div><div class="bar" style="margin-top:9px"><div id="fill" class="fill"></div></div></div><div class="card"><h3>AÇÕES RÁPIDAS</h3><div class="actions"><button class="action primary" onclick="post('/api/setup')">CORRIGIR TUDO</button><button class="action" onclick="post('/api/restart-services')">RECARREGAR SERVIÇOS</button><button class="action" onclick="post('/api/start/comfy')">INICIAR COMFYUI</button><button class="action" onclick="post('/api/start/ollama')">INICIAR AGENTE</button><button class="action" onclick="post('/api/start/openwebui')">INICIAR OPEN WEBUI</button><button class="action" onclick="post('/api/cmd')">ABRIR CMD</button><button class="action" onclick="post('/api/scan')">SCAN LOCAL</button><button class="action primary" onclick="post('/api/scan-completo')">SCAN A:–Z:</button></div></div></section>
<section id="chat" class="tab"><div class="card"><h3>AGENTE AURION — CHAT LOCAL</h3><div class="row"><select id="agentModel"><option>Carregando...</option></select><button class="action primary" onclick="loadAgent()">CARREGAR AGENTE</button><button class="action" onclick="decideAgent()">ANALISAR DECISÃO</button></div><div id="agentStatus" class="notice">Aguardando agente...</div><pre id="decisionBox">Nenhum plano ainda.</pre></div><div class="grid2"><div class="card"><div id="chatlog" class="chatlog"><div class="msg sys">AURION: preparando o agente local...</div></div><div class="row"><input id="chatInput" placeholder="Fale com o agente AURION..." onkeydown="if(event.key==='Enter')sendChat()"><button class="action primary" onclick="sendChat()">ENVIAR</button></div></div><div class="card"><h3>🧠 MEMÓRIA / MENTE</h3><input id="memTitle" placeholder="Nome da memória"><textarea id="memContent" style="min-height:170px" placeholder="Cole regras, contexto, roteiro ou informações para o agente..."></textarea><div class="actions"><button class="action primary" onclick="saveMemory()">💾 SALVAR MEMÓRIA</button><button class="action" onclick="clearMemory()">LIMPAR</button></div><div id="memoryList" class="model-list">Carregando memórias...</div></div></div></section>
<section id="prompt" class="tab"><div class="hero"><h2>AGENTE / PROMPT — CENTRAL DE PRODUÇÃO</h2><p>Interpretação de referências, links, imagens e refinamento de prompts para imagem e vídeo.</p></div><div class="grid2"><div class="card"><h3>ENTRADA</h3><label>Objetivo / ideia</label><textarea id="promptGoal" placeholder="Explique o que você quer produzir..."></textarea><label>Link de referência</label><input id="promptUrl" placeholder="https://..."><label>Referências de texto</label><textarea id="promptRefs" style="min-height:150px" placeholder="Cole briefing, roteiro, referências, restrições..."></textarea><label>Imagem para interpretar</label><input id="visionFile" type="file" accept="image/*"><div class="actions"><button class="action" onclick="analyzeVision()">ANALISAR IMAGEM</button><button class="action primary" onclick="refinePrompt('criar')">CRIAR PROMPT</button><button class="action" onclick="refinePrompt('refinar')">REFINAR PROMPT</button></div><pre id="visionResult">Nenhuma análise.</pre></div><div class="card"><h3>SAÍDA DO AGENTE PROMPT</h3><pre id="promptResult" style="min-height:500px">Aguardando...</pre><div class="actions"><button class="action" onclick="copyText('promptResult')">COPIAR</button></div></div></div><div class="card"><h3>DECISÃO CONTROLADA</h3><div class="actions"><button class="action" onclick="agentTool('status')">STATUS</button><button class="action" onclick="agentTool('comfy')">COMFYUI</button><button class="action" onclick="agentTool('scan')">SCAN</button><button class="action" onclick="agentTool('modelos')">MODELOS</button><button class="action" onclick="agentTool('gpu')">GPU</button><button class="action" onclick="agentTool('git')">GIT</button><button class="action" onclick="agentTool('dependencies')">DEPENDÊNCIAS</button></div><pre id="toolResult">Nenhuma ferramenta executada.</pre></div></section>
<section id="models" class="tab"><div class="grid2"><div class="card"><h3>MODELOS LOCAIS — COMFYUI</h3><div id="localModels" class="model-list">...</div></div><div class="card"><h3>MODELOS DO AGENTE — OLLAMA</h3><div id="ollamaModels" class="model-list">...</div></div></div><div class="card"><h3>AÇÕES</h3><div class="actions"><button class="action primary" onclick="post('/api/configure-models')">LIGAR MODELOS AO COMFYUI</button><button class="action" onclick="post('/api/download-comfy')">BAIXAR COMFYUI</button><button class="action" onclick="post('/api/dependencies')">ATUALIZAR DEPENDÊNCIAS</button></div></div></section>
<section id="scan" class="tab"><div class="hero"><h2>SCAN / PROJETOS / CLIENTES</h2><p>Indexação deduplicada: raízes sobrepostas não contam os mesmos arquivos duas vezes.</p><div class="actions"><button class="action primary" onclick="post('/api/scan')">SCAN LOCAL</button><button class="action" onclick="post('/api/scan-completo')">SCAN A:–Z:</button><button class="action" onclick="loadScan()">ATUALIZAR RELATÓRIO</button></div></div><div class="grid"><div class="card"><h3>ARQUIVOS</h3><div id="scFiles" class="big">0</div></div><div class="card"><h3>CLIENTES</h3><div id="scClients" class="big">0</div></div><div class="card"><h3>PROJETOS</h3><div id="scProjects" class="big">0</div></div><div class="card"><h3>TAMANHO</h3><div id="scSize" class="big">0 B</div></div></div><div class="grid2"><div class="card"><h3>CLIENTES</h3><pre id="scClientList">Nenhum scan.</pre></div><div class="card"><h3>PROJETOS</h3><pre id="scProjectList">Nenhum scan.</pre></div></div><div class="grid2"><div class="card"><h3>TIPOS DE ARQUIVO</h3><pre id="scTypes">Nenhum scan.</pre></div><div class="card"><h3>ARQUIVOS DE MAIOR TAMANHO</h3><pre id="scTop">Nenhum scan.</pre></div></div></section>
<section id="image" class="tab"><div class="hero"><h2>GERAR IMAGEM</h2><p>Base funcional preservada: fila, progresso e resultado pelo ComfyUI.</p></div><div class="grid2"><div class="card"><h3>PARÂMETROS</h3><label>Modelo / Checkpoint</label><select id="imgCheckpoint"><option>Carregando...</option></select><label>LoRA (opcional)</label><select id="imgLora"><option value="">Nenhuma</option></select><label>VAE (catálogo)</label><select id="imgVae"><option value="">Automático do checkpoint</option></select><label>ControlNet (catálogo)</label><select id="imgControl"><option value="">Nenhum</option></select><label>Imagem de referência</label><input id="imgRef" type="file" accept="image/*"><label>Prompt</label><textarea id="imgPrompt" placeholder="Descreva a imagem..."></textarea><label>Negative Prompt</label><textarea id="imgNegative" style="min-height:90px">low quality, blurry, distorted, duplicate, watermark</textarea></div><div class="card"><h3>GERAÇÃO</h3><div class="grid2"><div><label>Largura</label><input id="imgW" type="number" value="1024"></div><div><label>Altura</label><input id="imgH" type="number" value="1024"></div><div><label>Steps</label><input id="imgSteps" type="number" value="28"></div><div><label>CFG</label><input id="imgCfg" value="7"></div></div><label>Seed (-1 = aleatória)</label><input id="imgSeed" type="number" value="-1"><label><input id="agentBest" type="checkbox" checked style="width:auto"> AGENTE DECIDE O MELHOR MODELO/PARÂMETROS</label><div class="actions"><button class="action primary" onclick="generateImage()">⚡ GERAR IMAGEM</button><button class="action" onclick="openUrl('comfy')">ABRIR COMFYUI</button></div><div class="progressbox"><div class="bar"><div id="imgFill" class="fill"></div></div><div id="imgProgressText">AGUARDANDO — 0%</div><small id="imgProgressDetail">Nenhuma geração ativa.</small></div></div></div><div class="card"><h3>RESULTADO</h3><div id="imgResult" class="result">A imagem aparecerá aqui quando o ComfyUI terminar.</div></div></section>
<section id="video" class="tab"><div class="hero"><h2>GERAR VÍDEO — PIPELINE REAL</h2><p>Workflow API ou workflow visual do ComfyUI. O AURION valida nós antes de enviar.</p></div><div class="card"><h3>WORKFLOW</h3><div class="row"><select id="videoWorkflowSelect"><option value="">Selecionar workflow salvo...</option></select><button class="action" onclick="loadVideoWorkflow()">CARREGAR</button><button class="action" onclick="loadVideoWorkflows()">ATUALIZAR</button></div><label>JSON do workflow</label><textarea id="vw" placeholder="Cole o API JSON. Também aceitamos workflow visual exportado pelo ComfyUI e tentamos convertê-lo."></textarea><div class="actions"><button class="action" onclick="prepareVideo()">VALIDAR / CONVERTER</button><button class="action primary" onclick="generateVideo()">▶ ENVIAR PARA RENDER</button><button class="action" onclick="openUrl('comfy')">ABRIR COMFYUI</button></div><pre id="videoDiag">Aguardando workflow.</pre><div class="progressbox"><div class="bar"><div id="videoFill" class="fill"></div></div><div id="videoProgressText">AGUARDANDO — 0%</div><small id="videoProgressDetail">Nenhum vídeo em execução.</small></div></div><div class="grid2"><div class="card"><h3>REFERÊNCIA / PRODUÇÃO</h3><input id="videoRef" type="file" accept="image/*,video/*"><div class="drop" style="margin-top:10px">Referência local para o projeto. O workflow deve possuir um nó de entrada compatível.</div></div><div class="card"><h3>SAÍDA</h3><div id="videoResult" class="result">O resultado aparecerá aqui.</div></div></div><div class="card"><h3>GPU / COMFYUI</h3><pre id="vg">...</pre></div></section>
<section id="agents" class="tab"><div class="hero"><h2>AGENTES DA FIRMA</h2><p>AURION, VISION, PROMPT e CODE. Cada agente possui prompt, modelo, CHIP e memória próprios.</p></div><div id="agentsGrid" class="agent-grid">Carregando...</div><div class="card"><h3>CHIPS / MEMÓRIA / IMAGEM DO AGENTE</h3><div class="row"><select id="agentUploadName"><option>AURION</option><option>VISION</option><option>PROMPT</option><option>CODE</option></select><input id="agentFiles" type="file" multiple accept=".txt,.md,.json,image/*"><button class="action primary" onclick="uploadAgentFiles()">CARREGAR</button></div><pre id="chipList">...</pre></div></section>
<section id="refs" class="tab"><div class="hero"><h2>REFERÊNCIAS / PC / HD</h2><p>Defina locais que o agente pode consultar e procure arquivos reais sem copiar ou mover seu material.</p></div><div class="card"><h3>LOCAIS AUTORIZADOS</h3><textarea id="refRoots" style="min-height:130px" placeholder="Uma pasta por linha"></textarea><button class="action primary" onclick="saveRefRoots()">SALVAR LOCAIS</button></div><div class="card"><h3>BUSCA DE REFERÊNCIAS</h3><div class="row"><input id="refQuery" placeholder="nome, projeto, personagem, vídeo..."><button class="action primary" onclick="searchRefs()">BUSCAR</button></div><div id="refResults" class="model-list" style="margin-top:10px">Nenhuma busca.</div></div><div class="card"><h3>ENVIAR REFERÊNCIA</h3><input id="refUpload" type="file"><button class="action" onclick="uploadRef()">CARREGAR PARA AURION</button></div></section>
<section id="render" class="tab"><div class="grid2"><div class="card"><h3>NVIDIA / CUDA</h3><pre id="gpu">...</pre></div><div class="card"><h3>COMFYUI / RENDER</h3><pre id="cs">...</pre></div></div><div class="card"><h3>AÇÕES DE RENDER</h3><div class="actions"><button class="action primary" onclick="refresh()">ATUALIZAR GPU</button><button class="action" onclick="openUrl('comfy')">ABRIR COMFYUI</button></div></div></section>
<section id="repo" class="tab"><div class="card"><h3>REPOSITÓRIOS / GIT</h3><div id="repos">...</div></div><div class="card"><h3>AÇÕES</h3><div class="actions"><button class="action primary" onclick="post('/api/git/comfy-update')">ATUALIZAR COMFYUI — GIT PULL</button><button class="action" onclick="post('/api/git/update')">ATUALIZAR PROJETO</button><button class="action" onclick="post('/api/download-comfy')">BAIXAR / INSTALAR COMFYUI</button></div></div></section>
<section id="drivers" class="tab"><div class="grid2"><div class="card"><h3>DRIVER NVIDIA</h3><pre id="driver">...</pre></div><div class="card"><h3>DEPENDÊNCIAS</h3><pre id="deps">...</pre></div></div><div class="card"><h3>MANUTENÇÃO</h3><div class="actions"><button class="action primary" onclick="post('/api/dependencies')">ATUALIZAR DEPENDÊNCIAS</button><button class="action" onclick="openCmd()">CMD</button><button class="action" onclick="refresh()">DIAGNÓSTICO</button></div></div></section>
<section id="cmd" class="tab"><div class="hero"><h2>CMD / TERMINAL LOCAL</h2><p>Abre o terminal diretamente na pasta base do AURION.</p></div><div class="card"><div class="actions"><button class="action primary" onclick="openCmd()">ABRIR CMD</button><button class="action" onclick="openUrl('panel')">PAINEL</button><button class="action" onclick="openUrl('comfy')">COMFYUI</button><button class="action" onclick="openUrl('openwebui')">OPEN WEBUI</button></div></div></section>
<section id="logs" class="tab"><div class="grid2"><div class="card"><h3>LOG DO AURION</h3><pre id="logs">...</pre></div><div class="card"><h3>LOG DE ERROS</h3><pre id="errors">...</pre></div></div><div class="card"><h3>DIAGNÓSTICO JSON</h3><pre id="diag">...</pre></div></section>
</div></main></div><div id="floatingChat" class="floating-chat"><div class="fc-head"><b>⚡ AURION · CHAT</b><div><button class="action" onclick="toggleFloatChat()">—</button><button class="action" onclick="closeFloatChat()">×</button></div></div><div class="fc-body"><div id="fcLog" class="fc-log"><div class="msg sys">Chat flutuante. Arraste pela barra e redimensione pelo canto inferior direito.</div></div><div class="fc-input"><input id="fcInput" placeholder="Fale com o AURION..." onkeydown="if(event.key==='Enter')sendFloatChat()"><button class="action primary" onclick="sendFloatChat()">ENVIAR</button></div></div></div>
<script>
const titles={home:'PAINEL',chat:'AGENTE / CHAT',prompt:'AGENTE / PROMPT',models:'MODELOS',scan:'SCAN / PROJETOS',image:'GERAR IMAGEM',video:'GERAR VÍDEO',agents:'AGENTES DA FIRMA',refs:'REFERÊNCIAS',render:'RENDER / CUDA',repo:'REPOSITÓRIO / GIT',drivers:'DRIVERS / DEPENDÊNCIAS',cmd:'CMD',logs:'LOG / ERROS'};function tab(id,b){document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));document.getElementById(id).classList.add('active');document.querySelectorAll('.nav button').forEach(x=>x.classList.remove('active'));if(b)b.classList.add('active');document.getElementById('title').textContent=titles[id]||id}function txt(id,v){let e=document.getElementById(id);if(e)e.textContent=v??''}function esc(v){return String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]))}async function post(u){try{let r=await fetch(u,{method:'POST'}),d=await r.json();txt('global',d.message||d.reply||(d.ok?'OK':'Falhou'))}catch(e){txt('global','Erro: '+e)}setTimeout(refresh,500)}function openCmd(){post('/api/cmd')}function openUrl(n){fetch('/api/open/'+n,{method:'POST'})}
async function refresh(){try{let d=await (await fetch('/api/status',{cache:'no-store'})).json(),x=d.diagnostics,s=d.state;txt('hA',x.ollama.model||'não carregado');txt('sideAgent',x.ollama.model||'não carregado');txt('hC',x.comfy.running?'ONLINE':(x.comfy.found?'ENCONTRADO':'NÃO ENCONTRADO'));txt('hCP',x.comfy.path||'nenhum caminho');txt('hG',x.nvidia.gpus?.length?'ONLINE':'NÃO DETECTADA');txt('hGN',x.nvidia.gpus?.map(g=>g.name).join(' | ')||'nvidia-smi');txt('hM',x.models_inventory.total+' arquivos');txt('hMS',x.models_inventory.size);txt('op',(s.busy?s.operation+' — ':'')+s.message);document.getElementById('fill').style.width=s.progress+'%';txt('global',s.message);document.getElementById('dotA').className='dot '+(x.ollama.running?'ok':'');document.getElementById('dotC').className='dot '+(x.comfy.running?'ok':'');document.getElementById('dotG').className='dot '+(x.nvidia.gpus?.length?'ok':'');txt('gpu',JSON.stringify(x.nvidia,null,2));txt('vg',JSON.stringify(x.nvidia,null,2));txt('driver',JSON.stringify(x.nvidia,null,2));txt('deps',JSON.stringify(x.tools,null,2));txt('diag',JSON.stringify(x,null,2));txt('logs',(s.logs||[]).join('\n')||'Sem logs.');txt('errors',(s.errors||[]).join('\n')||'Sem erros.');if(d.state.video_job?.prompt_id&&!window.videoPolling)pollVideo(d.state.video_job.prompt_id);try{let z=await (await fetch('/api/comfy/stats')).json();txt('cs',JSON.stringify(z,null,2))}catch(e){txt('cs','ComfyUI offline.')}loadModels();loadRepos();loadScan()}catch(e){txt('global','Aguardando serviços...')}}
async function loadModels(){try{let d=await (await fetch('/api/models',{cache:'no-store'})).json(),lm=d.local.files||[],om=d.ollama||[];document.getElementById('localModels').innerHTML=lm.length?lm.map(m=>`<div class="model"><span>${esc(m.name)}<br><small>${esc(m.path)} · ${esc(m.size)}</small></span><span class="pill">${esc(m.ext)}</span></div>`).join(''):'Nenhum modelo local.';document.getElementById('ollamaModels').innerHTML=om.length?om.map(m=>`<div class="model"><span>${esc(m.name)}<br><small>${esc(m.size||'')}</small></span><button class="action" onclick="setModel(${JSON.stringify(m.name)})">CARREGAR</button></div>`).join(''):'Nenhum modelo Ollama.';let s=document.getElementById('agentModel'),current=d.agent_model||'';s.innerHTML=om.length?om.map(m=>`<option value="${esc(m.name)}">${esc(m.name)}</option>`).join(''):'<option value="">Nenhum modelo</option>';if(current)s.value=current;loadImageOptions();loadMemory();loadAgents();loadChips()}catch(e){txt('agentStatus','Falha ao carregar modelos: '+e)}}async function setModel(m){let r=await fetch('/api/agent/model',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({model:m})});let d=await r.json();txt('agentStatus',d.message||'Modelo selecionado.');refresh()}async function loadAgent(){let m=document.getElementById('agentModel').value;try{let r=await fetch('/api/agent/load',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({model:m})}),d=await r.json();txt('agentStatus',d.message||d.model||'Agente carregado.');await loadModels()}catch(e){txt('agentStatus','Erro: '+e)}}
async function sendChat(){let i=document.getElementById('chatInput'),m=i.value.trim();if(!m)return;let b=document.getElementById('chatlog');b.innerHTML+=`<div class="msg user"><b>VOCÊ</b><br>${esc(m)}</div><div class="msg sys">AURION: processando...</div>`;i.value='';try{let r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:m,model:document.getElementById('agentModel').value})}),d=await r.json();b.lastElementChild.remove();b.innerHTML+=`<div class="msg agent"><b>AURION</b><br>${esc(d.reply||'Sem resposta.')}</div>`}catch(e){b.lastElementChild.remove();b.innerHTML+=`<div class="msg sys">ERRO: ${esc(e)}</div>`}b.scrollTop=b.scrollHeight}async function sendFloatChat(){let i=document.getElementById('fcInput'),m=i.value.trim();if(!m)return;let b=document.getElementById('fcLog');b.innerHTML+=`<div class="msg user"><b>VOCÊ</b><br>${esc(m)}</div><div class="msg sys" id="fcWait">AURION: processando...</div>`;i.value='';try{let r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:m,model:document.getElementById('agentModel')?.value||''})}),d=await r.json();document.getElementById('fcWait')?.remove();b.innerHTML+=`<div class="msg agent"><b>AURION</b><br>${esc(d.reply||'Sem resposta.')}</div>`}catch(e){document.getElementById('fcWait')?.remove();b.innerHTML+=`<div class="msg sys">ERRO: ${esc(e)}</div>`}b.scrollTop=b.scrollHeight}function toggleFloatChat(){document.getElementById('floatingChat').classList.toggle('min')}function closeFloatChat(){document.getElementById('floatingChat').style.display='none'}
async function decideAgent(){let m=document.getElementById('chatInput').value.trim();if(!m)return;let r=await fetch('/api/agent/decide',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:m,model:document.getElementById('agentModel').value})}),d=await r.json();txt('decisionBox',JSON.stringify(d.plan||d,null,2))}async function agentTool(a){let c=a==='dependencies';if(c&&!confirm('Atualizar dependências pode alterar o ambiente do ComfyUI. Continuar?'))return;let r=await fetch('/api/agent/tool',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:a,confirm:c})}),d=await r.json();txt('toolResult',JSON.stringify(d,null,2));refresh()}
async function refinePrompt(mode){let r=await fetch('/api/agent/prompt',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mode,prompt:document.getElementById('promptGoal').value,references:document.getElementById('promptRefs').value,url:document.getElementById('promptUrl').value,model:document.getElementById('agentModel')?.value||''})}),d=await r.json();txt('promptResult',d.ok?d.result:d.message||'Falha')}async function analyzeVision(){let f=document.getElementById('visionFile').files[0];if(!f)return;let fd=new FormData();fd.append('file',f);let r=await fetch('/api/agent/analyze-image',{method:'POST',body:fd}),d=await r.json();txt('visionResult',d.ok?d.analysis:d.message||'Falha')}function copyText(id){navigator.clipboard?.writeText(document.getElementById(id)?.textContent||'')}
async function loadAgents(){try{let d=await (await fetch('/api/agent/config')).json(),a=d.agents||{},e=document.getElementById('agentsGrid');e.innerHTML=Object.entries(a).map(([n,c])=>`<div class="agent-box"><b>${esc(n)}</b> <span class="pill">${esc(c.role||'agente')}</span><label>Modelo</label><select id="ag_${esc(n)}"><option value="">Automático</option>${(d.models||[]).map(x=>`<option value="${esc(x)}" ${x===c.model?'selected':''}>${esc(x)}</option>`).join('')}</select><label>Prompt</label><textarea id="pr_${esc(n)}" style="min-height:110px">${esc(c.prompt||'')}</textarea><label><input type="checkbox" id="en_${esc(n)}" ${c.enabled?'checked':''} style="width:auto"> Ativo</label><button class="action primary" onclick="saveAgent('${esc(n)}')">SALVAR AGENTE</button></div>`).join('')}catch(e){}}async function saveAgent(n){let r=await fetch('/api/agent/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({[n]:{prompt:document.getElementById('pr_'+n).value,enabled:document.getElementById('en_'+n).checked,model:document.getElementById('ag_'+n).value,role:n}})});txt('global',(await r.json()).ok?'Agente salvo.':'Falha')}async function uploadAgentFiles(){let fs=document.getElementById('agentFiles').files;if(!fs.length)return;let fd=new FormData();fd.append('agent',document.getElementById('agentUploadName').value);for(let f of fs)fd.append('files',f);let r=await fetch('/api/agent/upload',{method:'POST',body:fd});txt('global',JSON.stringify(await r.json()));loadChips()}async function loadChips(){try{let d=await (await fetch('/api/chips')).json();txt('chipList',(d.files||[]).map(x=>x.agent+' | '+x.type+' | '+x.path).join('\n')||'Nenhum CHIP/arquivo de agente.')}catch(e){}}
async function loadScan(){try{let d=await (await fetch('/api/scan/report',{cache:'no-store'})).json();if(!d.ok)return;txt('scFiles',d.arquivos);txt('scClients',Object.keys(d.clientes||{}).length);txt('scProjects',Object.keys(d.projetos||{}).length);txt('scSize',d.tamanho||'0 B');txt('scClientList',Object.entries(d.clientes||{}).slice(0,200).map(([n,x])=>n+' | '+x.arquivos+' arquivos | '+hsizeJS(x.bytes)+' | '+x.pasta).join('\n')||'Nenhum');txt('scProjectList',Object.entries(d.projetos||{}).slice(0,200).map(([n,x])=>n+' | '+x.arquivos+' arquivos | '+hsizeJS(x.bytes)+' | '+x.pasta).join('\n')||'Nenhum');txt('scTypes',JSON.stringify(d.por_tipo||{},null,2));txt('scTop',(d.arquivos_destaque||[]).slice(0,100).map(x=>x.tamanho+' | '+x.tipo+' | '+x.caminho).join('\n')||'Nenhum')}catch(e){}}function hsizeJS(n){n=Number(n)||0;let u=['B','KB','MB','GB','TB'];let i=0;while(n>=1024&&i<u.length-1){n/=1024;i++}return n.toFixed(1)+' '+u[i]}
async function loadImageOptions(){try{let d=await (await fetch('/api/image/options')).json(),s=document.getElementById('imgCheckpoint');if(s){s.innerHTML=(d.checkpoints||[]).map(x=>`<option value="${esc(x)}">${esc(x)}</option>`).join('')||'<option value="">Nenhum checkpoint</option>'}}catch(e){}}async function generateImage(){let p=document.getElementById('imgPrompt').value.trim();if(!p)return;txt('imgProgressText','ENVIANDO — 0%');document.getElementById('imgFill').style.width='2%';let body={prompt:p,negative:document.getElementById('imgNegative').value,checkpoint:document.getElementById('imgCheckpoint').value,width:document.getElementById('imgW').value,height:document.getElementById('imgH').value,steps:document.getElementById('imgSteps').value,cfg:document.getElementById('imgCfg').value,seed:document.getElementById('imgSeed').value};try{let r=await fetch('/api/image/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}),d=await r.json();if(!d.ok){txt('imgProgressText','ERRO');txt('imgProgressDetail',d.message||'Falha');return}pollImage(d.prompt_id)}catch(e){txt('imgProgressText','ERRO');txt('imgProgressDetail',String(e))}}async function pollImage(pid){for(let i=0;i<600;i++){try{let d=await (await fetch('/api/image/progress/'+encodeURIComponent(pid),{cache:'no-store'})).json();document.getElementById('imgFill').style.width=(d.progress||0)+'%';txt('imgProgressText',(d.status||'PROCESSANDO').toUpperCase()+' — '+(d.progress||0)+'%');txt('imgProgressDetail',(d.elapsed||0)+'s · prompt_id: '+pid);if(d.images?.length){document.getElementById('imgFill').style.width='100%';txt('imgProgressText','CONCLUÍDO — 100%');document.getElementById('imgResult').innerHTML=d.images.map(x=>`<img class="media" src="${COMFY_VIEW(x)}">`).join('');return}}catch(e){}await new Promise(r=>setTimeout(r,1200))}txt('imgProgressText','TIMEOUT — verifique o ComfyUI')}function COMFY_VIEW(x){let q=new URLSearchParams({filename:x.filename,subfolder:x.subfolder||'',type:x.type||'output'});return 'http://127.0.0.1:8188/view?'+q.toString()}
document.getElementById('videoRef')?.addEventListener('change',async()=>{let f=document.getElementById('videoRef').files[0];if(!f)return;let fd=new FormData();fd.append('file',f);try{let d=await (await fetch('/api/video/upload',{method:'POST',body:fd})).json();txt('videoDiag',d.ok?'Referência salva: '+d.path:d.message||'Falha')}catch(e){txt('videoDiag',String(e))}});async function loadVideoWorkflows(){try{let d=await (await fetch('/api/video/workflows')).json(),s=document.getElementById('videoWorkflowSelect');s.innerHTML='<option value="">Selecionar workflow salvo...</option>'+(d.workflows||[]).map(x=>`<option value="${esc(x.path)}">${esc(x.name)} [${esc(x.kind)}]</option>`).join('')}catch(e){}}async function loadVideoWorkflow(){let p=document.getElementById('videoWorkflowSelect').value;if(!p)return;try{let d=await (await fetch('/api/video/workflow/load?path='+encodeURIComponent(p))).json();if(!d.ok){txt('videoDiag',d.message||'Falha');return}document.getElementById('vw').value=JSON.stringify(d.workflow,null,2);txt('videoDiag','Workflow carregado: '+d.name+' ['+d.kind+']\nClique VALIDAR / CONVERTER antes de renderizar.')}catch(e){txt('videoDiag',String(e))}}async function prepareVideo(){let t=document.getElementById('vw').value.trim();if(!t)return;try{let r=await fetch('/api/video/prepare',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({workflow:JSON.parse(t)})}),d=await r.json();txt('videoDiag',JSON.stringify(d,null,2));if(d.ok)document.getElementById('vw').value=JSON.stringify(d.workflow,null,2)}catch(e){txt('videoDiag',String(e))}}async function generateVideo(){let t=document.getElementById('vw').value.trim();if(!t)return;try{let r=await fetch('/api/video/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({workflow:JSON.parse(t)})}),d=await r.json();txt('videoDiag',JSON.stringify(d,null,2));if(d.ok)pollVideo(d.prompt_id)}catch(e){txt('videoDiag',String(e))}}window.videoPolling=false;async function pollVideo(pid){if(window.videoPolling)return;window.videoPolling=true;for(let i=0;i<1200;i++){try{let d=await (await fetch('/api/video/progress/'+encodeURIComponent(pid),{cache:'no-store'})).json();document.getElementById('videoFill').style.width=(d.progress||0)+'%';txt('videoProgressText',(d.status||'PROCESSANDO').toUpperCase()+' — '+(d.progress||0)+'%');txt('videoProgressDetail',(d.elapsed||0)+'s · prompt_id: '+pid);if(d.media?.length){document.getElementById('videoFill').style.width='100%';txt('videoProgressText','CONCLUÍDO — 100%');document.getElementById('videoResult').innerHTML=d.media.map(x=>x.media_type==='video'?`<video class="media" controls src="${COMFY_VIEW(x)}"></video>`:`<img class="media" src="${COMFY_VIEW(x)}">`).join('');window.videoPolling=false;return}}catch(e){}await new Promise(r=>setTimeout(r,1500))}window.videoPolling=false;txt('videoProgressText','TIMEOUT — verifique o ComfyUI')}
async function saveRefRoots(){let roots=document.getElementById('refRoots').value.split(/\r?\n/).map(x=>x.trim()).filter(Boolean);let r=await fetch('/api/references/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({roots})});txt('global',(await r.json()).ok?'Locais salvos.':'Falha')}async function loadRefRoots(){try{let d=await (await fetch('/api/references/config')).json();document.getElementById('refRoots').value=(d.roots||[]).join('\n')}catch(e){}}async function searchRefs(){let q=document.getElementById('refQuery').value,r=await fetch('/api/references/search?q='+encodeURIComponent(q)),d=await r.json();document.getElementById('refResults').innerHTML=(d.results||[]).map(x=>`<div class="model"><span>${esc(x.name)}<br><small>${esc(x.path)} · ${esc(x.size)}</small></span></div>`).join('')||'Nenhuma referência encontrada.'}async function uploadRef(){let f=document.getElementById('refUpload').files[0];if(!f)return;let fd=new FormData();fd.append('file',f);let r=await fetch('/api/references/upload',{method:'POST',body:fd});txt('global',JSON.stringify(await r.json()))}
async function loadRepos(){try{let d=await (await fetch('/api/git')).json(),rs=d.repos||[];document.getElementById('repos').innerHTML=rs.length?rs.map(r=>`<div class="card"><b>${esc(r.path)}</b><br>branch: ${esc(r.branch||'-')}<pre>${esc(r.status||r.remote||'')}</pre></div>`).join(''):'Nenhum repositório Git detectado.'}catch(e){}}async function loadMemory(){try{let d=await (await fetch('/api/memory/list')).json();let e=document.getElementById('memoryList');e.innerHTML=(d.files||[]).map(x=>`<div class="model" onclick='openMemory(${JSON.stringify(x.path)})'><span>${esc(x.name)}<br><small>${esc(x.category)} · ${esc(x.modified)}</small></span></div>`).join('')||'Nenhuma memória salva.'}catch(e){}}async function openMemory(path){let r=await fetch('/api/memory/load',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({path})}),d=await r.json();if(d.ok){document.getElementById('memContent').value=d.content;document.getElementById('memTitle').value=path.split(/[\/]/).pop().replace(/\.md$/i,'')}}async function saveMemory(){let r=await fetch('/api/memory/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title:document.getElementById('memTitle').value,content:document.getElementById('memContent').value})}),d=await r.json();txt('agentStatus',d.message||d.error||'');loadMemory()}function clearMemory(){document.getElementById('memTitle').value='';document.getElementById('memContent').value=''}refresh();loadRefRoots();loadVideoWorkflows();setInterval(refresh,3000);
</script></body></html>'''


if __name__=="__main__":
    ensure_dirs(); ensure_agent_config();print("="*72);print(" AURION — PAINEL LOCAL");print("="*72);print(f" Base    : {PROJECT}");print(f" Modelos : {MODELS}");print(f" Painel  : http://{HOST}:{PORT}");print("="*72)
    d=diagnose();print(f"Python  : {d['python']}");print(f"ComfyUI : {d['comfy']['found']} | {d['comfy'].get('path')}");print(f"Ollama  : {d['ollama']['running']} | agente={d['ollama'].get('model')}");print(f"WebUI   : {d['openwebui']['running']}");print(f"NVIDIA  : {len(d['nvidia'].get('gpus',[]))} GPU(s)");print(f"Modelos : {d['models_inventory']['total']} | {d['models_inventory']['size']}");print("="*72)
    threading.Thread(target=startup,daemon=True).start();threading.Timer(1.2,lambda:webbrowser.open(f"http://{HOST}:{PORT}")).start();app.run(host=HOST,port=PORT,debug=False,threaded=True)
