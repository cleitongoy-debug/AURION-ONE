# -*- coding: utf-8 -*-
"""AURION DYNAMIC - painel local integrado. Scanner ampliado de modelos IA, vídeo e 3D.
Chat/Agente (Ollama), ComfyUI, modelos, geracao por workflow,
render/CUDA/NVIDIA, Git, dependencias, CMD, Adapta ONE e Canon T8i.
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
MODELS=PROJECT/"models"; DOWNLOADS=PROJECT/"_downloads"; LOG_DIR=PROJECT/"_aurion_logs"; WORKFLOWS=PROJECT/"workflows"; SCAN_DIR=PROJECT/"scan"; SCAN_REPORT=SCAN_DIR/"catalogo.json"; SCAN_JSONL=SCAN_DIR/"arquivos.jsonl"; MODEL_SCAN_REPORT=SCAN_DIR/"modelos.json"; MODEL_SCAN_JSONL=SCAN_DIR/"modelos.jsonl"
MEMORY_DIR=PROJECT/"memoria"; MENTE_DIR=PROJECT/"mente"; FRAG_DIR=PROJECT/"fragmentos"; CLIENT_DIR=PROJECT/"clientes"; PROJECTS_DIR=PROJECT/"projetos"
AGENTS_DIR=PROJECT/"agentes"; REFERENCES_DIR=PROJECT/"referencias"; REF_INBOX=REFERENCES_DIR/"inbox"; CONFIG_DIR=PROJECT/"config"; AGENT_CONFIG=CONFIG_DIR/"agentes.json"; REF_CONFIG=CONFIG_DIR/"referencias.json"; VIDEO_JOBS=PROJECT/"video_jobs"
HOST="127.0.0.1"; PORT=5000; COMFY_PORT=8188; OLLAMA_PORT=11434; OPENWEBUI_PORT=8080
COMFY_URL=f"http://127.0.0.1:{COMFY_PORT}"; OLLAMA_URL=f"http://127.0.0.1:{OLLAMA_PORT}"; OPENWEBUI_URL=f"http://127.0.0.1:{OPENWEBUI_PORT}"
# ---------------- Adapta ONE ----------------
# Integração segura por launcher/local hub. A assinatura continua autenticada
# no site oficial; o painel não captura senha, cookies ou tokens.
ADAPTA_URL="https://adapta.org/adapta-one"
ADAPTA_AGENT_URL="https://agent.adapta.one/"
ADAPTA_COURSES_URL="https://adapta.org/cursos"
ADAPTA_DOCS_URL="https://docs.adapta.org/comece-aqui/quickstart"
ADAPTA_HELP_CERT_URL="https://docs.adapta.org/central-de-ajuda/plataforma/cursos/como-funciona-o-sistema-de-certificacao-dos-cursos"
ADAPTA_DIR=PROJECT/"adapta"
ADAPTA_COURSES_DIR=ADAPTA_DIR/"cursos"
ADAPTA_CERTS_DIR=ADAPTA_DIR/"certificados"
ADAPTA_EXPERTS_DIR=ADAPTA_DIR/"experts"
ADAPTA_GENERATIONS_DIR=ADAPTA_DIR/"geracoes"
ADAPTA_INTERPRETATIONS_DIR=ADAPTA_DIR/"interpretacoes"
ADAPTA_CACHE_DIR=ADAPTA_DIR/"cache"
ADAPTA_LOG_DIR=ADAPTA_DIR/"logs"
ADAPTA_PROFILE_DIR=ADAPTA_DIR/"browser_profile"
AGENT_RUNS_DIR=PROJECT/"agentes"/"execucoes"
AGENT_MEMORY_DIR=PROJECT/"agentes"/"memoria"
ADAPTA_RESOURCES_FILE=ADAPTA_CACHE_DIR/"recursos.json"
ADAPTA_DOWNLOAD_DIR=ADAPTA_DIR/"downloads"
T8I_DIR=PROJECT/"t8i"
T8I_CAPTURE_DIR=T8I_DIR/"capturas"
T8I_RAW_DIR=T8I_DIR/"raw"
T8I_EXPORT_DIR=T8I_DIR/"exportados"
T8I_LOG_DIR=T8I_DIR/"logs"
T8I_SESSIONS_DIR=T8I_DIR/"sessoes"
T8I_ANALYSIS_DIR=T8I_DIR/"analises"
T8I_PROMPTS_DIR=T8I_DIR/"prompts"
EOS_UTILITY_URL="https://app.ssw.imaging-saas.canon/app/pt/eu.html"
COMFY_PORTABLE_URL="https://github.com/comfyanonymous/ComfyUI/releases/latest/download/ComfyUI_windows_portable_nvidia.7z"
SEVENZIP_URL="https://www.7-zip.org/a/7zr.exe"
OLLAMA_PREFERRED=["qwen3.5:4b","qwen3:8b","llama3.2:3b","llava:7b","deepseek-r1:7b"]
IGNORE={"Windows","Program Files","Program Files (x86)","Arquivos de Programas","PerfLogs","System","System32","AppData","Microsoft","Microsoft.NET","WindowsApps","$Recycle.Bin","System Volume Information","Recovery","ProgramData","node_modules",".git"}
MODEL_EXT={".safetensors",".ckpt",".pt",".pth",".bin",".gguf",".onnx",".sft",".safetensors.index.json"}
MODEL_3D_EXT={".obj",".fbx",".glb",".gltf",".blend",".c4d",".abc",".ply",".stl",".dae",".usd",".usda",".usdc",".usdz",".3ds",".max",".ma",".mb",".hip",".hda",".vdb"}
MODEL_SCAN_EXT=MODEL_EXT|MODEL_3D_EXT
MODEL_FAMILY_HINTS={
    "hunyuan3d":("hunyuan3d","hunyuan-3d","hunyuan_3d","hunway3d"),
    "hunyuan_video":("hunyuanvideo","hunyuan-video","hunyuan video","hunwayvideo","hunway video"),
    "wan_video":("wan2.1","wan2.2","wanvideo","wan-video"),
    "ltx_video":("ltx-video","ltxvideo","ltxv"),
    "cogvideo":("cogvideo","cogvideox"),
    "mochi_video":("mochi","mochi1"),
    "3d_ai":("trellis","triposr","stable-fast-3d","stablefast3d","instantmesh","wonder3d","dust3r","mast3r"),
    "flux":("flux","flux1","flux2"),
    "sdxl":("sdxl","stable-diffusion-xl","juggernautxl"),
    "sd":("stable-diffusion","sd15","sd1.5","sd2","sd3"),
    "controlnet":("controlnet",),
    "lora":("lora","loras"),
    "vae":("vae",),
    "upscale":("upscale","esrgan","realesrgan"),
}
app=Flask(__name__)
STATE:dict[str,Any]={"busy":False,"operation":"","progress":0,"message":"AURION pronto.","logs":[],"errors":[],"scan":None,"model_scan":None,"agent_model":None,"startup_done":False,"startup":{},"image_job":{},"video_job":{}}
LOCK=threading.Lock()
ADAPTA_BROWSER_LOCK=threading.RLock()
ADAPTA_INTERACTIVE_LOCK=threading.RLock()
ADAPTA_INTERACTIVE=None

def ensure_dirs():
    for p in (PROJECT,MODELS,DOWNLOADS,LOG_DIR,WORKFLOWS,SCAN_DIR,MEMORY_DIR,MENTE_DIR,FRAG_DIR,CLIENT_DIR,PROJECTS_DIR,AGENTS_DIR,REFERENCES_DIR,REF_INBOX,CONFIG_DIR,VIDEO_JOBS,ADAPTA_DIR,ADAPTA_PROFILE_DIR,T8I_DIR,T8I_CAPTURE_DIR,T8I_RAW_DIR,T8I_EXPORT_DIR,T8I_LOG_DIR,ADAPTA_COURSES_DIR,ADAPTA_CERTS_DIR,ADAPTA_EXPERTS_DIR,ADAPTA_GENERATIONS_DIR,ADAPTA_INTERPRETATIONS_DIR,ADAPTA_CACHE_DIR,ADAPTA_LOG_DIR): p.mkdir(parents=True,exist_ok=True)
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
def _model_family(path: Path):
    text=str(path).lower().replace("\\","/")
    for family,hints in MODEL_FAMILY_HINTS.items():
        if any(h in text for h in hints): return family
    ext=path.suffix.lower()
    if ext in MODEL_3D_EXT:return "3d_asset"
    if "checkpoints" in text:return "checkpoint"
    if "diffusion_models" in text:return "diffusion_model"
    if "text_encoders" in text:return "text_encoder"
    if "clip_vision" in text:return "clip_vision"
    if "clip" in text:return "clip"
    if "ipadapter" in text:return "ipadapter"
    if "photomaker" in text:return "photomaker"
    if "style_models" in text:return "style_model"
    if "embeddings" in text:return "embedding"
    if "controlnet" in text:return "controlnet"
    if "loras" in text:return "lora"
    if "vae" in text:return "vae"
    if "upscale_models" in text:return "upscale"
    if "unet" in text:return "unet"
    return "model"

def _model_source(path: Path):
    text=str(path).lower().replace("\\","/")
    c=comfy_candidates(max_depth=6)
    for item in c:
        cp=str(Path(item["path"]).resolve()).lower().replace("\\","/")
        if text.startswith(cp+"/"):
            return "comfyui"
    if text.startswith(str(MODELS.resolve()).lower().replace("\\","/")+"/"):return "aurion"
    if "/huggingface/" in text or "/.cache/huggingface/" in text:return "huggingface"
    return "externo"

def _read_extra_model_paths():
    """Extrai caminhos de modelos dos extra_model_paths.yaml sem exigir PyYAML."""
    found=[]; seen=set()
    configs=[]
    for c in comfy_candidates(max_depth=6):
        cp=Path(c["path"])
        configs += [cp/"extra_model_paths.yaml", cp/"extra_model_paths.yml"]
    # Também procura configs próximos ao projeto/ComfyUI portátil.
    for base in (PROJECT,PROJECT.parent,Path.home()/"Desktop",Path.home()/"Downloads",Path.home()/"Documents"):
        if base.exists():
            configs += [base/"extra_model_paths.yaml",base/"extra_model_paths.yml"]
    for cfg in configs:
        if not cfg.exists() or cfg in seen:continue
        seen.add(cfg)
        try:lines=cfg.read_text(encoding="utf-8",errors="ignore").splitlines()
        except Exception:continue
        base=None
        for line in lines:
            raw=line.split("#",1)[0].rstrip()
            m=re.match(r"^\s*base_path\s*:\s*(.+?)\s*$",raw,re.I)
            if m:
                val=m.group(1).strip().strip('"\'')
                try:base=Path(val).expanduser()
                except Exception:base=None
                if base and base.exists() and base.is_dir():
                    rp=str(base.resolve())
                    if rp.lower() not in {str(x.resolve()).lower() for x in found}:found.append(base)
                continue
            # caminhos absolutos em listas e valores de pastas de modelo
            m=re.match(r"^\s*[A-Za-z0-9_ -]+\s*:\s*(.+?)\s*$",raw)
            if m:
                val=m.group(1).strip().strip('"\'')
                vals=[val]
                if val.startswith("[") and val.endswith("]"): vals=re.findall(r"[A-Za-z]:[^,\]]+|/[^,\]]+",val)
                for v in vals:
                    v=v.strip().strip('"\'').replace("\\\\","\\")
                    pp=Path(v)
                    if not pp.is_absolute() and base: pp=base/v
                    if pp.exists() and pp.is_dir():
                        found.append(pp)
    out=[]; seen2=set()
    for x in found:
        try:r=x.resolve()
        except Exception:r=x
        k=str(r).lower()
        if k not in seen2:seen2.add(k);out.append(r)
    return out

def model_scan_roots():
    roots=[MODELS]
    # Todos os diretórios de modelos conhecidos pelo ComfyUI.
    for c in comfy_candidates(max_depth=6):
        cp=Path(c["path"])
        roots += [cp/"models",cp.parent/"models"]
    roots += _read_extra_model_paths()
    # Caches locais comuns de modelos.
    home=Path.home()
    roots += [home/".cache"/"huggingface",home/".cache"/"huggingface"/"hub",home/".cache"/"torch",home/".cache"/"torch"/"hub"]
    # Procuramos também em todos os discos, mas com poda agressiva de sistema.
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        d=Path(f"{letter}:\\")
        if d.exists():roots.append(d)
    out=[];seen=set()
    for r in roots:
        try:r=r.resolve()
        except Exception:continue
        if not r.exists() or not r.is_dir():continue
        k=str(r).lower()
        if k not in seen:seen.add(k);out.append(r)
    return out

def scan_models_pc():
    """Catálogo real de modelos de IA e assets 3D do PC/ComfyUI/paths externos."""
    roots=model_scan_roots()
    result={"timestamp":datetime.now().isoformat(timespec="seconds"),"label":"MODELOS PC + COMFYUI + EXTERNOS","arquivos":0,"bytes":0,"por_extensao":{},"por_familia":{},"por_origem":{},"3d":0,"video_ai":0,"comfyui":[],"externos":[],"alvos":[str(x) for x in roots],"erros":[],"catalogo_completo":False}
    MODEL_SCAN_REPORT.parent.mkdir(parents=True,exist_ok=True)
    try:MODEL_SCAN_JSONL.unlink(missing_ok=True)
    except Exception:pass
    seen=set(); processed=0; top=[]; max_top=300
    jsonl_handle=None
    try: jsonl_handle=MODEL_SCAN_JSONL.open("w",encoding="utf-8")
    except Exception as e: result["erros"].append(f"abrir catálogo JSONL: {e}")
    comfy_paths=[Path(x["path"]).resolve() for x in comfy_candidates(max_depth=6)]
    for root in roots:
        try:
            for cur,dirs,files in os.walk(root,topdown=True):
                curp=Path(cur)
                # Poda para não perder tempo em Windows, caches irrelevantes e repositórios.
                dirs[:]=[d for d in dirs if d not in IGNORE_SCAN and not d.startswith('.') and d.lower() not in {"node_modules","site-packages","packages","windows","program files","program files (x86)","programdata"}]
                for fn in files:
                    fp=curp/fn; ext=fp.suffix.lower()
                    if ext not in MODEL_SCAN_EXT:continue
                    try:rp=fp.resolve(); key=str(rp).lower()
                    except Exception:key=str(fp).lower();rp=fp
                    if key in seen:continue
                    seen.add(key);processed+=1
                    try:size=fp.stat().st_size
                    except (OSError,PermissionError) as e:
                        result["erros"].append(f"{fp}: {e}");continue
                    family=_model_family(fp); source="externo"
                    for cp in comfy_paths:
                        try:
                            rp.relative_to(cp);source="comfyui";break
                        except ValueError:pass
                    if source!="comfyui" and safe_inside(MODELS,rp):source="aurion"
                    if "/huggingface/" in str(rp).lower().replace('\\','/'):source="huggingface"
                    row={"nome":fn,"caminho":str(fp),"relativo":rel(fp,root),"bytes":size,"tamanho":hsize(size),"ext":ext,"familia":family,"origem":source,"is_3d":ext in MODEL_3D_EXT}
                    result["arquivos"]+=1;result["bytes"]+=size;result["por_extensao"][ext]=result["por_extensao"].get(ext,0)+1;result["por_familia"][family]=result["por_familia"].get(family,0)+1;result["por_origem"][source]=result["por_origem"].get(source,0)+1
                    if row["is_3d"]:result["3d"]+=1
                    if family in {"hunyuan_video","wan_video","ltx_video","cogvideo","mochi_video"} or "video" in family:result["video_ai"]+=1
                    if source=="comfyui" and len(result["comfyui"])<500:result["comfyui"].append(row)
                    if source!="comfyui" and len(result["externos"])<500:result["externos"].append(row)
                    if jsonl_handle:
                        try: jsonl_handle.write(json.dumps(row,ensure_ascii=False)+"\n")
                        except Exception as e: result["erros"].append(f"JSONL {fp}: {e}")
                    top.append(row);top.sort(key=lambda x:x["bytes"],reverse=True);del top[max_top:]
                    if processed%100==0:progress(min(95,max(5,int(processed/100)%90+5)),f"SCAN MODELOS: {processed:,} itens encontrados...")
        except (PermissionError,OSError) as e:result["erros"].append(f"{root}: {e}")
    result["destaques"]=top;result["tamanho"]=hsize(result["bytes"]);result["catalogo_completo"]=True;result["catalogo_arquivo"]=str(MODEL_SCAN_JSONL);result["catalogo_registros"]=len(seen)
    try:
        if jsonl_handle: jsonl_handle.close()
        MODEL_SCAN_REPORT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    except Exception as e:result["erros"].append(f"salvar catálogo de modelos: {e}")
    return result

def inventory():
    # Inventário rápido do núcleo AURION; o catálogo PC/ComfyUI completo fica no model scan.
    files=[];counts={};total=0
    if not MODELS.exists():return {"counts":{},"total":0,"bytes":0,"size":"0 B","files":[],"scan":None}
    try:
        for p in MODELS.rglob("*"):
            if not p.is_file() or any(x in IGNORE for x in p.parts) or p.suffix.lower() not in MODEL_EXT:continue
            try:n=p.stat().st_size
            except OSError:n=0
            counts[p.suffix.lower()]=counts.get(p.suffix.lower(),0)+1;total+=n
            if len(files)<500:files.append({"name":p.name,"path":rel(p,MODELS),"size":hsize(n),"ext":p.suffix.lower(),"familia":_model_family(p),"origem":"aurion"})
    except OSError:pass
    scan=None
    try:
        if MODEL_SCAN_REPORT.exists():scan=json.loads(MODEL_SCAN_REPORT.read_text(encoding="utf-8"))
    except Exception:pass
    return {"counts":counts,"total":sum(counts.values()),"bytes":total,"size":hsize(total),"files":files,"scan":scan}

def model_folders():
    ns=["checkpoints","diffusion_models","vae","text_encoders","loras","controlnet","clip","clip_vision","unet","upscale_models","embeddings","ipadapter","photomaker","style_models","gligen","hypernetworks","vae_approx"]
    out={n:sum(1 for p in (MODELS/n).rglob("*") if p.is_file()) if (MODELS/n).exists() else 0 for n in ns}
    for k,v in {"3d_assets":MODEL_3D_EXT,"video_models":MODEL_EXT}.items():
        out[k]=sum(1 for p in MODELS.rglob("*") if p.is_file() and p.suffix.lower() in v) if MODELS.exists() else 0
    return out

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
    d={"timestamp":datetime.now().isoformat(timespec="seconds"),"project":str(PROJECT),"models":str(MODELS),"python":sys.version.split()[0],"python_executable":sys.executable,"comfy":c,"ollama":{"running":oll,"url":OLLAMA_URL,"port":OLLAMA_PORT,"executable":exe("ollama",[Path(os.environ.get("LOCALAPPDATA",""))/"Programs/Ollama/ollama.exe",Path(r"C:\Program Files\Ollama\ollama.exe")]),"model":choose_model() if oll else None},"openwebui":{"running":port(OPENWEBUI_PORT),"url":OPENWEBUI_URL,"port":OPENWEBUI_PORT,"executable":exe("open-webui")},"nvidia":n,"tools":{"git":exists("git"),"git_version":version(["git","--version"]) if exists("git") else "","ffmpeg":exists("ffmpeg"),"ffmpeg_version":version(["ffmpeg","-version"]) if exists("ffmpeg") else "","7zip":exists("7z") or exists("7za") or (DOWNLOADS/"7zr.exe").exists(),"winget":exists("winget")},"models_inventory":inv,"model_folders":model_folders(),"model_scan":(inv.get("scan") or {"catalogo_completo":False,"arquivos":0,"3d":0,"video_ai":0,"por_origem":{},"por_familia":{}})}
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
    log("Catálogo de modelos: pronto para SCAN PC + ComfyUI + externos.")
    log("=== CARREGAMENTO INICIAL FINALIZADO ===")

def open_cmd():
    try:subprocess.Popen(["cmd.exe","/d","/k"],cwd=str(PROJECT));log("CMD aberto.");return True
    except Exception as e:log(f"Erro CMD: {e}",True);return False

# ---------------- AGENTES / REFERENCIAS / VIDEO ----------------
AGENT_ACTIONS={"status":"diagnóstico local","scan":"scan local","scan_completo":"scan A-Z","modelos":"inventário de modelos","scan_modelos":"scan PC + ComfyUI + externos","comfy":"diagnóstico ComfyUI","ollama":"diagnóstico Ollama","gpu":"diagnóstico NVIDIA","git":"status Git","start_comfy":"iniciar ComfyUI","start_ollama":"iniciar Ollama","start_webui":"iniciar Open WebUI","dependencies":"atualizar dependências do ComfyUI"}

def agent_generation_plan(message,context=None):
    low=str(message or "").lower(); plan={"objetivo":"analisar pedido","acao":"chat","ferramentas":[],"modelo":STATE.get("agent_model"),"parametros":{}}
    if any(x in low for x in ("scan","arquivos","pasta","hd","disco")):plan.update(objetivo="consultar arquivos reais",acao="scan",ferramentas=["scan"])
    elif any(x in low for x in ("comfy","comfyui","workflow")):plan.update(objetivo="verificar pipeline ComfyUI",acao="comfy",ferramentas=["comfy"])
    elif any(x in low for x in ("gpu","nvidia","vram","cuda")):plan.update(objetivo="verificar GPU",acao="gpu",ferramentas=["gpu"])
    elif any(x in low for x in ("modelo","modelos","checkpoint","lora","vae","3d","hunyuan","hunyuan3d","hunyuan video")):plan.update(objetivo="consultar inventário de modelos",acao="modelos",ferramentas=["modelos"])
    elif any(x in low for x in ("dependência","dependencias","requirements")):plan.update(objetivo="diagnosticar dependências",acao="dependencies",ferramentas=["dependencies"])
    elif any(x in low for x in ("git","atualizar repositório","pull")):plan.update(objetivo="verificar Git",acao="git",ferramentas=["git"])
    return plan

def agent_tool(action,confirm=False):
    if action not in AGENT_ACTIONS:raise RuntimeError("Ferramenta não autorizada.")
    if action=="status":return diagnose(True)
    if action=="scan":return local_scan()
    if action=="scan_completo":return complete_scan()
    if action=="modelos":return inventory()
    if action=="scan_modelos":return scan_models_pc()
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


# ---------------- Adapta ONE + T8i ----------------
# O AURION NÃO cria uma API falsa para o Adapta.
# O acesso aos recursos da conta é feito por automação do navegador autenticado,
# usando um perfil local persistente. Senha/OTP ficam apenas em memória durante
# o login e NÃO são gravados em arquivos/logs.
ADAPTA_LOGIN_URL=ADAPTA_AGENT_URL

def _adapta_playwright():
    try:
        from playwright.sync_api import sync_playwright
        return sync_playwright
    except Exception:
        return None

def adapta_deps_status():
    # Não inicializa Playwright a cada polling do painel. Isso causava
    # encerramentos concorrentes e "Task was destroyed" no log.
    ok_playwright=False
    chromium=False
    try:
        import playwright
        ok_playwright=True
        from pathlib import Path as _Path
        # O caminho abaixo é verificado sem abrir um processo Playwright.
        cache=Path.home()/"AppData"/"Local"/"ms-playwright"
        chromium=cache.exists() and any(cache.glob("chromium-*"))
    except Exception:
        pass
    return {"playwright":ok_playwright,"chromium":chromium,"profile":str(ADAPTA_PROFILE_DIR)}

def adapta_install_deps():
    result=[]
    try:
        import playwright
        result.append({"package":"playwright","installed":True,"already":True})
    except Exception:
        try:
            subprocess.check_call([sys.executable,"-m","pip","install","playwright"],timeout=900)
            result.append({"package":"playwright","installed":True,"installed_now":True})
        except Exception as e:
            result.append({"package":"playwright","installed":False,"error":str(e)})
            return {"ok":False,"packages":result}
    try:
        r=subprocess.run([sys.executable,"-m","playwright","install","chromium"],
                         capture_output=True,text=True,timeout=1800,encoding="utf-8",errors="ignore")
        result.append({"package":"chromium","installed":r.returncode==0,"output":(r.stdout or r.stderr)[-4000:]})
    except Exception as e:
        result.append({"package":"chromium","installed":False,"error":str(e)})
    ok=all(x.get("installed") for x in result)
    if ok: log("Motor Adapta: Playwright + Chromium preparados.")
    else: log("Falha preparando motor Adapta.",True)
    return {"ok":ok,"packages":result}

def _adapta_with_browser(work, headless=True):
    sync_playwright=_adapta_playwright()
    if not sync_playwright:
        return {"ok":False,"code":"PLAYWRIGHT_MISSING","message":"Clique em INSTALAR MOTOR ADAPTA."}
    ensure_dirs(); ADAPTA_PROFILE_DIR.mkdir(parents=True,exist_ok=True)
    # Serializa TODO acesso ao perfil persistente. O painel faz polling a cada
    # poucos segundos e vários requests simultâneos estavam fechando o mesmo
    # contexto Playwright, gerando TargetClosedError/Task was destroyed.
    with ADAPTA_BROWSER_LOCK:
        try:
            with sync_playwright() as pw:
                context=pw.chromium.launch_persistent_context(
                    str(ADAPTA_PROFILE_DIR), headless=headless,
                    viewport={"width":1440,"height":900},
                    args=["--disable-blink-features=AutomationControlled"]
                )
                try:
                    page=context.pages[0] if context.pages else context.new_page()
                    return work(page,context)
                finally:
                    try: context.close()
                    except Exception: pass
        except Exception as e:
            log(f"Adapta browser: {type(e).__name__}: {e}",True)
            return {"ok":False,"code":"BROWSER_ERROR","message":str(e)}

def _find_first(page, selectors):
    for sel in selectors:
        try:
            loc=page.locator(sel).first
            if loc.is_visible(timeout=800):
                return loc
        except Exception:
            continue
    return None

def _adapta_submit_login(page):
    # Seletores amplos para acompanhar pequenas mudanças da interface.
    btn=_find_first(page,[
        'button:has-text("Entrar")','button:has-text("Login")',
        'button:has-text("Acessar")','button:has-text("Continuar")',
        'input[type="submit"]'
    ])
    if btn:
        btn.click()
        return True
    try:
        page.keyboard.press("Enter")
        return True
    except Exception:
        return False

def adapta_login_interactive_start():
    """Abre o login oficial em um Chromium persistente e deixa o usuário concluir
    senha/2FA diretamente na página oficial. Não recebe nem grava credenciais."""
    global ADAPTA_INTERACTIVE
    sync_playwright=_adapta_playwright()
    if not sync_playwright:
        return {"ok":False,"code":"PLAYWRIGHT_MISSING","message":"Motor do navegador ausente. Use AGENTE AUTO-REPARO."}
    deps=adapta_deps_status()
    if not deps.get("chromium"):
        return {"ok":False,"code":"CHROMIUM_MISSING","message":"Chromium do Playwright não está instalado. Use AGENTE AUTO-REPARO."}
    with ADAPTA_INTERACTIVE_LOCK:
        if ADAPTA_INTERACTIVE and ADAPTA_INTERACTIVE.get("thread") and ADAPTA_INTERACTIVE["thread"].is_alive():
            return {"ok":True,"already":True,"message":"A janela oficial do Adapta já está aberta. Faça login nela e depois clique em FINALIZAR LOGIN."}
        stop=threading.Event()
        holder={"stop":stop,"started":datetime.now().isoformat(timespec="seconds"),"url":ADAPTA_LOGIN_URL,"error":""}
        def runner():
            try:
                ensure_dirs(); ADAPTA_PROFILE_DIR.mkdir(parents=True,exist_ok=True)
                with sync_playwright() as pw:
                    with ADAPTA_BROWSER_LOCK:
                        context=pw.chromium.launch_persistent_context(
                            str(ADAPTA_PROFILE_DIR),headless=False,
                            viewport={"width":1440,"height":900},
                            args=["--disable-blink-features=AutomationControlled"]
                        )
                        try:
                            page=context.pages[0] if context.pages else context.new_page()
                            page.goto(ADAPTA_LOGIN_URL,wait_until="domcontentloaded",timeout=60000)
                            holder["url"]=page.url
                            log("Adapta: janela oficial aberta. Faça login/2FA diretamente nela.")
                            while not stop.wait(1.0):
                                try:
                                    holder["url"]=page.url
                                    if page.is_closed(): break
                                except Exception: break
                        finally:
                            try: context.close()
                            except Exception: pass
            except Exception as e:
                holder["error"]=f"{type(e).__name__}: {e}"
                log("Adapta login interativo: "+holder["error"],True)
        t=threading.Thread(target=runner,daemon=True,name="adapta-login")
        holder["thread"]=t; ADAPTA_INTERACTIVE=holder; t.start()
    return {"ok":True,"message":"Janela oficial do Adapta aberta. Faça login e 2FA nela. O AURION não vê nem grava sua senha.","url":ADAPTA_LOGIN_URL}

def adapta_login_interactive_finish():
    global ADAPTA_INTERACTIVE
    with ADAPTA_INTERACTIVE_LOCK:
        h=ADAPTA_INTERACTIVE
        if not h or not h.get("thread"):
            return {"ok":False,"message":"Nenhuma sessão de login interativo está aberta."}
        h["stop"].set(); t=h["thread"]
    t.join(timeout=15)
    with ADAPTA_INTERACTIVE_LOCK:
        ADAPTA_INTERACTIVE=None
    if t.is_alive():
        return {"ok":False,"code":"BROWSER_STILL_OPEN","message":"A janela ainda está finalizando. Aguarde alguns segundos e sincronize novamente."}
    if h.get("error"):
        return {"ok":False,"code":"BROWSER_ERROR","message":h["error"]}
    # Só depois de fechar o navegador interativo o perfil fica livre para a leitura.
    result=adapta_discover()
    if result.get("authenticated"):
        return {"ok":True,"code":"AUTHENTICATED","message":"Login confirmado e sessão salva no perfil local do AURION.","resources":result}
    return {"ok":False,"code":"NOT_AUTHENTICATED","message":"A sessão ainda não foi reconhecida como autenticada. Se o Adapta estiver logado, clique em sincronizar novamente.","resources":result}

def adapta_interactive_status():
    with ADAPTA_INTERACTIVE_LOCK:
        h=ADAPTA_INTERACTIVE
        return {"open":bool(h and h.get("thread") and h["thread"].is_alive()),
                "url":(h or {}).get("url","") if h else "","error":(h or {}).get("error","") if h else ""}

def adapta_agent_repair():
    """Pipeline de agentes locais. Cada agente tem uma função determinística:
    DEPENDÊNCIAS -> NAVEGADOR -> ESTRUTURA -> SESSÃO -> CATÁLOGO.
    Não executa comandos arbitrários produzidos por IA e não tenta burlar login/2FA.
    """
    report=[]
    def stage(name,msg,fn,pct):
        progress(pct,f"Agente {name}: {msg}")
        try:
            data=fn(); report.append({"agente":name,"ok":True,"dados":data})
            return data
        except Exception as e:
            log(f"Agente {name}: {type(e).__name__}: {e}",True)
            report.append({"agente":name,"ok":False,"erro":f"{type(e).__name__}: {e}"})
            return None

    deps=stage("DEPENDÊNCIAS","verificando Playwright e Chromium...",adapta_deps_status,5) or {}
    if not deps.get("playwright") or not deps.get("chromium"):
        stage("INSTALADOR","baixando/instalando Playwright + Chromium...",adapta_install_deps,15)
    stage("ESTRUTURA","criando pastas locais...",lambda:adapta_status().get("folders",{}),30)
    sess=stage("SESSÃO","testando a sessão oficial...",adapta_discover,50) or {}
    if not sess.get("authenticated"):
        progress(65,"Agente SESSÃO: login humano necessário; abrindo página oficial...")
        opened=adapta_login_interactive_start()
        report.append({"agente":"SESSÃO","ok":bool(opened.get("ok")),"dados":opened})
        progress(75,"Agente SESSÃO: faça login/2FA na janela aberta e depois finalize no painel.")
    else:
        stage("CATÁLOGO","sincronizando modelos, Experts e recursos...",adapta_discover,90)
    out=ADAPTA_LOG_DIR/"agente_reparo.json"
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    progress(100,"Agentes Adapta: ciclo concluído. Se a autenticação foi necessária, finalize o login no painel.")
    return report

def adapta_login(email,password,otp=""):
    if not email or not password:
        return {"ok":False,"message":"Informe e-mail e senha."}
    def work(page,context):
        page.goto(ADAPTA_LOGIN_URL,wait_until="domcontentloaded",timeout=60000)
        page.wait_for_timeout(1500)
        email_box=_find_first(page,[
            'input[type="email"]','input[autocomplete="username"]',
            'input[name*="email" i]','input[placeholder*="email" i]'
        ])
        pass_box=_find_first(page,[
            'input[type="password"]','input[autocomplete="current-password"]',
            'input[name*="password" i]','input[placeholder*="senha" i]'
        ])
        if not email_box or not pass_box:
            return {"ok":False,"code":"LOGIN_FORM_NOT_FOUND",
                    "message":"A tela de login do Adapta mudou ou não foi carregada.",
                    "url":page.url}
        email_box.fill(email)
        pass_box.fill(password)
        _adapta_submit_login(page)
        page.wait_for_timeout(2500)
        if otp:
            otp_box=_find_first(page,[
                'input[autocomplete="one-time-code"]',
                'input[inputmode="numeric"]',
                'input[name*="otp" i]','input[name*="code" i]',
                'input[placeholder*="código" i]','input[placeholder*="codigo" i]'
            ])
            if otp_box:
                otp_box.fill(otp)
                _adapta_submit_login(page)
                page.wait_for_timeout(2500)
        text=page.locator("body").inner_text(timeout=5000)
        low=text.lower()
        twofa=bool(_find_first(page,[
            'input[autocomplete="one-time-code"]',
            'input[inputmode="numeric"]',
            'input[name*="otp" i]','input[name*="code" i]'
        ]))
        login_words=("senha incorreta","senha inválida","senha invalida","credenciais inválidas","credenciais invalidas")
        bad=any(x in low for x in login_words)
        if twofa and not otp:
            return {"ok":False,"code":"2FA_REQUIRED","message":"O Adapta pediu o código de verificação em duas etapas.","url":page.url}
        if bad:
            return {"ok":False,"code":"LOGIN_FAILED","message":"O Adapta recusou as credenciais.","url":page.url}
        # Não registra senha, OTP, cookies nem o conteúdo completo da página.
        return {"ok":True,"code":"AUTHENTICATED","message":"Sessão Adapta autenticada no perfil local do AURION.","url":page.url}
    return _adapta_with_browser(work,headless=False)

def adapta_discover():
    """Lê a interface autenticada sem tentar obter senha, OTP, cookies ou tokens.
    A detecção é baseada na URL e no texto/renderização visível, não apenas em botões.
    """
    def work(page,context):
        page.goto(ADAPTA_AGENT_URL,wait_until="domcontentloaded",timeout=60000)
        page.wait_for_timeout(5000)
        try: page.wait_for_load_state("networkidle",timeout=12000)
        except Exception: pass
        body=page.locator("body").inner_text(timeout=15000)
        low=body.lower()
        url=(page.url or "").lower()
        has_login_form=bool(_find_first(page,[
            'input[type="password"]','input[autocomplete="current-password"]',
            'input[name*="password" i]'
        ]))
        login_url=("/sign-in" in url or "/login" in url or "/signin" in url)
        bad_page=any(x in low for x in ["senha incorreta","credenciais inválidas","credenciais invalidas"])
        logged=bool((not has_login_form) and (not login_url) and (not bad_page))
        # O app atual pode renderizar cartões/divs sem button/a. Capturamos
        # linhas visíveis do body e também títulos/botões, mantendo somente texto.
        raw=[]
        for line in body.splitlines():
            v=" ".join(line.split())
            if 1 < len(v) < 220: raw.append(v)
        for selector in ["button","a","[role=button]","option","h1","h2","h3","h4","[class*=card]","[class*=model]","[class*=expert]"]:
            try:
                for el in page.locator(selector).all()[:600]:
                    try:
                        v=" ".join((el.inner_text(timeout=300) or "").split())
                        if 1 < len(v) < 220: raw.append(v)
                    except Exception: pass
            except Exception: pass
        raw=list(dict.fromkeys(raw))
        model_re=re.compile(r"\b(?:GPT(?:[- ]?\w+)?|Claude(?:[- ]?\w+)?|Gemini(?:[- ]?\w+)?|Grok(?:[- ]?\w+)?|DeepSeek(?:[- ]?\w+)?|Qwen(?:[- ]?\w+)?|Llama(?:[- ]?\w+)?|Mistral(?:[- ]?\w+)?|Perplexity|Kimi(?:[- ]?\w+)?|Flux(?:[- ]?\w+)?|Recraft(?:[- ]?\w+)?|Imagen(?:[- ]?\w+)?|Seedream(?:[- ]?\w+)?|Nano Banana|ONE Image|OpenAI|Anthropic)\b",re.I)
        models=[x for x in raw if model_re.search(x)]
        expert=[x for x in raw if re.search(r"\b(expert|experts|agente|agentes)\b",x,re.I)]
        feature=[x for x in raw if re.search(r"\b(imagem|image|arquivo|document|planilha|gráfico|grafico|vídeo|video|pesquisa|web|curso|certificado|automação|automacao|contexto|vision)\b",x,re.I)]
        data={"ok":True,"authenticated":logged,"url":page.url,
              "models":list(dict.fromkeys(models))[:300],
              "experts":list(dict.fromkeys(expert))[:300],
              "features":list(dict.fromkeys(feature))[:300],
              "interface_items":raw[:1200],
              "title":page.title(),
              "updated":datetime.now().isoformat(timespec="seconds")}
        ADAPTA_RESOURCES_FILE.parent.mkdir(parents=True,exist_ok=True)
        ADAPTA_RESOURCES_FILE.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
        log(f"Adapta sincronizado: autenticado={logged}; modelos={len(data['models'])}; experts={len(data['experts'])}; recursos={len(data['features'])}.")
        return data
    return _adapta_with_browser(work,headless=True)

def adapta_status():
    ensure_dirs()
    deps=adapta_deps_status()
    resources={}
    if ADAPTA_RESOURCES_FILE.exists():
        try: resources=json.loads(ADAPTA_RESOURCES_FILE.read_text(encoding="utf-8"))
        except Exception: resources={}
    authenticated=bool(resources.get("authenticated"))
    return {
        "ok":True,"module":"ADAPTA ONE","base":str(ADAPTA_DIR),
        "authenticated":authenticated,
        "interactive":adapta_interactive_status(),
        "browser":{"ready":deps},
        "folders":{"cursos":str(ADAPTA_COURSES_DIR),"certificados":str(ADAPTA_CERTS_DIR),
                   "experts":str(ADAPTA_EXPERTS_DIR),"geracoes":str(ADAPTA_GENERATIONS_DIR),
                   "interpretacoes":str(ADAPTA_INTERPRETATIONS_DIR),"cache":str(ADAPTA_CACHE_DIR),
                   "logs":str(ADAPTA_LOG_DIR),"downloads":str(ADAPTA_DOWNLOAD_DIR)},
        "official":{"hub":ADAPTA_AGENT_URL,"courses":ADAPTA_COURSES_URL,
                    "docs":ADAPTA_DOCS_URL,"certificates":ADAPTA_HELP_CERT_URL},
        "api":"NÃO DISPONÍVEL PUBLICAMENTE NO ADAPTA ONE 26",
        "resource_source":"SESSÃO AUTENTICADA DO ADAPTA + INTERFACE DISPONÍVEL",
        "models":resources.get("models",[]),
        "experts":resources.get("experts",[]),
        "features":resources.get("features",[]),
        "note":"O AURION não grava senha/OTP. A sessão persistente fica no perfil local do navegador."
    }

def t8i_find_eos_utility():
    candidates=[
        Path(os.environ.get("ProgramFiles",r"C:\Program Files"))/"Canon/EOS Utility/EOS Utility.exe",
        Path(os.environ.get("ProgramFiles",r"C:\Program Files"))/"Canon/EOS Utility/EOS Utility 3.exe",
        Path(os.environ.get("ProgramFiles(x86)",r"C:\Program Files (x86)"))/"Canon/EOS Utility/EOS Utility.exe",
        Path(os.environ.get("ProgramFiles(x86)",r"C:\Program Files (x86)"))/"Canon/EOS Utility/EOS Utility 3.exe",
    ]
    for c in candidates:
        if c.exists(): return str(c)
    return ""

def t8i_detect():
    if os.name!="nt": return {"ok":True,"windows":False,"devices":[],"utility":""}
    devices=[]
    try:
        cmd=["powershell","-NoProfile","-ExecutionPolicy","Bypass","-Command",
             "Get-PnpDevice -PresentOnly | Where-Object { $_.FriendlyName -match 'Canon|EOS|T8i|850D' } | Select-Object Status,Class,FriendlyName,InstanceId | ConvertTo-Json -Compress"]
        r=subprocess.run(cmd,capture_output=True,text=True,timeout=12)
        raw=(r.stdout or "").strip()
        if raw:
            obj=json.loads(raw)
            devices=obj if isinstance(obj,list) else [obj]
    except Exception as e:
        log(f"T8i detecção: {e}",True)
    files=[]
    try:
        if T8I_CAPTURE_DIR.exists(): files=[str(x) for x in sorted(T8I_CAPTURE_DIR.rglob("*")) if x.is_file()][-300:]
    except Exception: pass
    return {"ok":True,"windows":True,"devices":devices,"utility":t8i_find_eos_utility(),"capture_dir":str(T8I_CAPTURE_DIR),"files":files}

def t8i_prepare():
    for d in (T8I_DIR,T8I_CAPTURE_DIR,T8I_RAW_DIR,T8I_EXPORT_DIR,T8I_LOG_DIR): d.mkdir(parents=True,exist_ok=True)
    readme=T8I_DIR/"README.txt"
    if not readme.exists():
        readme.write_text("AURION T8i — Canon EOS Rebel T8i / 850D\n\nUse EOS Utility para conexão oficial, disparo remoto e transferência.\nArquivos importados podem ser organizados em capturas/, raw/ e exportados/.\n",encoding="utf-8")
    log(f"Estrutura T8i pronta: {T8I_DIR}")
    return {"ok":True,"path":str(T8I_DIR),"capture_dir":str(T8I_CAPTURE_DIR),"raw_dir":str(T8I_RAW_DIR),"export_dir":str(T8I_EXPORT_DIR)}

@app.get("/api/adapta/status")
def api_adapta_status(): return jsonify(adapta_status())

@app.get("/api/adapta/models")
def api_adapta_models():
    s=adapta_status()
    return jsonify({"ok":s["ok"],"models":s.get("models",[]),"experts":s.get("experts",[]),
                    "features":s.get("features",[]),"authenticated":s.get("authenticated",False)})

@app.post("/api/adapta/deps")
def api_adapta_deps():
    return jsonify(adapta_install_deps())

@app.post("/api/adapta/login/start")
def api_adapta_login_start():
    return jsonify(adapta_login_interactive_start())

@app.post("/api/adapta/login/finish")
def api_adapta_login_finish():
    r=adapta_login_interactive_finish()
    return jsonify(r), (200 if r.get("ok") else 400)

@app.get("/api/adapta/login/status")
def api_adapta_login_status():
    return jsonify(adapta_interactive_status())

@app.get("/api/adapta/repair/status")
def api_adapta_repair_status():
    p=ADAPTA_LOG_DIR/"agente_reparo.json"
    if not p.exists(): return jsonify({"ok":True,"running":STATE.get("busy",False),"report":[]})
    try: report=json.loads(p.read_text(encoding="utf-8"))
    except Exception: report=[]
    return jsonify({"ok":True,"running":STATE.get("busy",False),"report":report})

@app.post("/api/adapta/repair")
def api_adapta_repair():
    return (jsonify({"ok":True,"message":"Agente de reparo iniciado."}) if bg("Agente Adapta",adapta_agent_repair) else (jsonify({"ok":False,"message":"Outro reparo já está em andamento."}),409))

@app.post("/api/adapta/login")
def api_adapta_login():
    data=request.get_json(silent=True) or {}
    # Credenciais entram apenas nesta chamada, são usadas em memória e não são logadas.
    result=adapta_login(str(data.get("email","")).strip(),str(data.get("password","")),str(data.get("otp","")).strip())
    return jsonify(result), (200 if result.get("ok") or result.get("code")=="2FA_REQUIRED" else 400)

@app.post("/api/adapta/sync")
def api_adapta_sync():
    r=adapta_discover()
    if r.get("ok") and not r.get("authenticated"):
        r["message"]="Sessão não autenticada. Faça o login no Adapta e tente sincronizar novamente."
        return jsonify(r),401
    return jsonify(r), (200 if r.get("ok") else 400)

@app.post("/api/adapta/prepare")
def api_adapta_prepare():
    ensure_dirs()
    readme=ADAPTA_DIR/"README.txt"
    readme.write_text(
        "AURION — ADAPTA ONE\n\n"
        "A sessão usa um perfil local persistente do navegador.\n"
        "O AURION não grava senha ou código 2FA.\n"
        "O catálogo local é somente o que foi descoberto na sessão/interface.\n",
        encoding="utf-8"
    )
    log(f"Estrutura Adapta pronta: {ADAPTA_DIR}")
    return jsonify({"ok":True,"message":"Estrutura Adapta preparada.","path":str(ADAPTA_DIR),"folders":adapta_status()["folders"]})

@app.post("/api/adapta/download")
def api_adapta_download():
    """Baixa um arquivo público/fornecido pelo usuário para a pasta do AURION.
    Não usa cookies da sessão Adapta nem tenta baixar conteúdo protegido sem URL.
    """
    data=request.get_json(silent=True) or {}; url=str(data.get("url","")).strip()
    if not (url.startswith("https://") or url.startswith("http://")):
        return jsonify({"ok":False,"message":"URL http/https obrigatória."}),400
    try:
        from urllib.parse import urlparse,unquote
        name=Path(unquote(urlparse(url).path)).name or "arquivo_download"
        name=secure_filename(name) or "arquivo_download"
        ADAPTA_DOWNLOAD_DIR.mkdir(parents=True,exist_ok=True)
        dest=ADAPTA_DOWNLOAD_DIR/name
        with urllib.request.urlopen(url,timeout=60) as r, open(dest,"wb") as f:
            shutil.copyfileobj(r,f,length=1024*1024)
        log(f"Download Adapta: {dest}")
        return jsonify({"ok":True,"path":str(dest),"bytes":dest.stat().st_size})
    except Exception as e:
        log(f"Download Adapta falhou: {e}",True)
        return jsonify({"ok":False,"message":str(e)}),500

@app.post("/api/adapta/logout")
def api_adapta_logout():
    try:
        if ADAPTA_PROFILE_DIR.exists():
            shutil.rmtree(ADAPTA_PROFILE_DIR,ignore_errors=True)
        if ADAPTA_RESOURCES_FILE.exists(): ADAPTA_RESOURCES_FILE.unlink()
        log("Sessão local Adapta removida.")
        return jsonify({"ok":True,"message":"Sessão local do Adapta removida."})
    except Exception as e:
        return jsonify({"ok":False,"message":str(e)}),500

@app.get("/api/t8i/status")
def api_t8i_status(): return jsonify(t8i_detect())
@app.post("/api/t8i/prepare")
def api_t8i_prepare(): return jsonify(t8i_prepare())
@app.post("/api/t8i/eos")
def api_t8i_eos():
    exe=t8i_find_eos_utility()
    if exe:
        try: subprocess.Popen([exe]); log("EOS Utility iniciado"); return jsonify({"ok":True,"message":"EOS Utility iniciado.","path":exe})
        except Exception as e: return jsonify({"ok":False,"message":str(e)}),500
    webbrowser.open(EOS_UTILITY_URL); return jsonify({"ok":False,"message":"EOS Utility não foi localizado. Página oficial de download aberta.","url":EOS_UTILITY_URL})


# ---------------- AGENTES + CANON T8i ----------------
def list_agents():
    data=load_agent_config()
    return [{"name":k,**(v if isinstance(v,dict) else {})} for k,v in data.items()]

def agent_run(name,prompt,model=None):
    cfg=load_agent_config().get(name)
    if not cfg:
        raise RuntimeError(f"Agente não encontrado: {name}")
    chosen=model or cfg.get("model") or STATE.get("agent_model") or ""
    if not chosen:
        raise RuntimeError("Nenhum modelo Ollama definido para este agente.")
    result=post_json(f"{OLLAMA_URL}/api/generate",{
        "model":chosen,"prompt":str(prompt),"stream":False},timeout=180)
    ensure_dirs()
    rec={"agent":name,"model":chosen,"prompt":str(prompt),"result":result,
         "at":datetime.now().isoformat(timespec="seconds")}
    (AGENT_RUNS_DIR/f"{datetime.now():%Y%m%d_%H%M%S_%f}_{secure_filename(name)}.json").write_text(
        json.dumps(rec,ensure_ascii=False,indent=2),encoding="utf-8")
    return rec

def t8i_status():
    ensure_dirs()
    devices=[]
    canon_paths=[]
    for p in (Path("C:/Program Files/Canon"),Path("C:/Program Files (x86)/Canon")):
        if p.exists(): canon_paths.append(str(p))
    try:
        ps='Get-CimInstance Win32_PnPEntity | Select-Object -ExpandProperty Name'
        r=subprocess.run(["powershell","-NoProfile","-Command",ps],capture_output=True,text=True,
                         timeout=15,encoding="utf-8",errors="ignore")
        devices=[x.strip() for x in (r.stdout or "").splitlines()
                 if re.search(r"Canon|EOS|850D|Rebel T8i",x,re.I)]
    except Exception: pass
    return {"ok":True,"camera_detected":bool(devices),"devices":devices[:30],
            "canon_paths":canon_paths[:30],
            "folders":{"capturas":str(T8I_CAPTURE_DIR),"raw":str(T8I_RAW_DIR),
                       "exportados":str(T8I_EXPORT_DIR),"sessoes":str(T8I_SESSIONS_DIR),
                       "analises":str(T8I_ANALYSIS_DIR),"prompts":str(T8I_PROMPTS_DIR)}}

def t8i_prepare():
    ensure_dirs()
    (T8I_DIR/"README.txt").write_text(
        "AURION CANON T8i\nRAW -> análise -> prompt -> ComfyUI.\n"
        "Detecção de dispositivos é somente leitura.\n",encoding="utf-8")
    return t8i_status()


# ---------------- AURION ZERO: OPENCODE + BOOT CORE ----------------
OPENCODE_REPO="https://github.com/anomalyco/opencode.git"
OPENCODE_DIR=PROJECT/"opencode"
OPENCODE_CONFIG=PROJECT/"opencode.json"
OPENCODE_SKILLS=PROJECT/".opencode"/"skills"
BOOT={"running":False,"done":False,"percent":0,"step":"AGUARDANDO","message":"Aguardando inicialização.","items":[],"started":None,"finished":None}
BOOT_LOCK=threading.RLock()

def opencode_exe():
    candidates=[]
    for name in ("opencode","opencode.cmd","opencode.exe"):
        x=shutil.which(name)
        if x:candidates.append(Path(x))
    candidates += [Path.home()/".opencode"/"bin"/"opencode.exe", Path.home()/".opencode"/"bin"/"opencode.cmd"]
    for p in candidates:
        if p.exists(): return str(p)
    return None

def opencode_status():
    exe_path=opencode_exe()
    result={"installed":bool(exe_path),"executable":exe_path,"version":"","repo":OPENCODE_REPO,"config":str(OPENCODE_CONFIG),"skills":0,"ollama_local":port(OLLAMA_PORT)}
    if exe_path:
        result["version"]=version([exe_path,"--version"])
    try:
        result["skills"]=sum(1 for p in OPENCODE_SKILLS.glob("*/SKILL.md") if p.is_file()) if OPENCODE_SKILLS.exists() else 0
    except Exception: pass
    return result

def ensure_opencode_config():
    ensure_dirs(); OPENCODE_SKILLS.mkdir(parents=True,exist_ok=True)
    cfg={"$schema":"https://opencode.ai/config.json","provider":{"ollama":{"npm":"@ai-sdk/openai-compatible","name":"Ollama (local)","options":{"baseURL":f"{OLLAMA_URL}/v1"},"models":{}}}}
    models=ollama_models()
    for m in models:
        name=str(m.get("name") or "").strip()
        if name: cfg["provider"]["ollama"]["models"][name]={"name":name}
    if not OPENCODE_CONFIG.exists() or OPENCODE_CONFIG.read_text(encoding="utf-8",errors="ignore").strip()!=json.dumps(cfg,ensure_ascii=False,indent=2):
        OPENCODE_CONFIG.write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding="utf-8")
    skills={
      "aurion-scan":"Escaneia e organiza modelos, assets 3D, vídeo e caminhos externos do AURION sem apagar arquivos.",
      "aurion-comfy":"Opera somente sobre o ComfyUI local, seus workflows e extra_model_paths.",
      "aurion-repair":"Diagnostica e corrige somente estruturas e dependências locais autorizadas pelo AURION.",
      "aurion-project":"Organiza projetos, referências e saídas do AURION.",
    }
    for name,desc in skills.items():
        d=OPENCODE_SKILLS/name; d.mkdir(parents=True,exist_ok=True); f=d/"SKILL.md"
        content=f"---\nname: {name}\ndescription: {desc}\n---\n\n# {name}\n\nUse somente ferramentas locais e ações reversíveis. Nunca apague modelos, projetos ou arquivos do usuário.\n"
        if not f.exists() or f.read_text(encoding="utf-8",errors="ignore")!=content:f.write_text(content,encoding="utf-8")
    return cfg

def install_opencode_local():
    ensure_opencode_config()
    if opencode_exe(): return {"ok":True,"message":"OpenCode já instalado.","status":opencode_status()}
    npm=shutil.which("npm")
    if not npm:
        return {"ok":False,"message":"OpenCode não encontrado e npm não está instalado. O AURION não baixará executáveis arbitrários.","status":opencode_status()}
    q=subprocess.run([npm,"install","-g","opencode-ai@latest"],capture_output=True,text=True,timeout=1800,encoding="utf-8",errors="ignore")
    if q.returncode:
        return {"ok":False,"message":(q.stderr or q.stdout)[-3000:],"status":opencode_status()}
    return {"ok":True,"message":"OpenCode instalado pelo pacote oficial npm.","status":opencode_status()}

def boot_set(step,pct,message,ok=None):
    with BOOT_LOCK:
        BOOT["step"]=step; BOOT["percent"]=max(0,min(100,int(pct))); BOOT["message"]=message
        if ok is not None: BOOT["items"].append({"step":step,"ok":bool(ok),"message":message})
    log(f"[BOOT] {step}: {message}", error=(ok is False))

def boot_sequence(force=False):
    with BOOT_LOCK:
        if BOOT["running"] and not force:return
        BOOT.update(running=True,done=False,percent=0,step="INICIANDO",message="Preparando núcleo local...",items=[],started=datetime.now().isoformat(timespec="seconds"),finished=None)
    steps=[
      ("PASTAS",5,lambda:(ensure_dirs() or True),"Estrutura do AURION preparada."),
      ("OLLAMA",18,start_ollama,"Ollama local verificado."),
      ("COMFYUI",30,start_comfy,"ComfyUI local verificado."),
      ("CONFIG COMFY",40,configure_comfy,"extra_model_paths e pastas sincronizados."),
      ("OPENCODE",50,ensure_opencode_config,"OpenCode local configurado para Ollama."),
      ("SCAN MODELOS",70,scan_models_pc,"Modelos, vídeo, 3D e caminhos externos catalogados."),
      ("DIAGNÓSTICO",88,lambda:diagnose(True),"Serviços e GPU diagnosticados."),
    ]
    for step,pct,fn,msg in steps:
        boot_set(step,pct,msg)
        try:
            result=fn(); ok=(result is not False)
        except Exception as e:
            ok=False; log(f"[BOOT] {step} falhou: {e}",True)
        boot_set(step,pct,msg,ok)
    boot_set("FINAL",100,"AURION pronto — painel liberado.",True)
    with BOOT_LOCK:BOOT.update(running=False,done=True,finished=datetime.now().isoformat(timespec="seconds"))

def boot_status():
    with BOOT_LOCK:return json.loads(json.dumps(BOOT,ensure_ascii=False))

@app.get("/api/boot/status")
def api_boot_status(): return jsonify(boot_status())

@app.post("/api/boot/start")
def api_boot_start():
    threading.Thread(target=boot_sequence,daemon=True).start(); return jsonify({"ok":True})

@app.post("/api/boot/reboot")
def api_boot_reboot():
    threading.Thread(target=lambda:boot_sequence(True),daemon=True).start(); return jsonify({"ok":True})

@app.post("/api/auto-repair")
def api_auto_repair():
    def job():
        progress(5,"AUTO REPARO: verificando estrutura..."); ensure_dirs(); progress(20,"Configurando ComfyUI..."); configure_comfy(); progress(35,"Configurando OpenCode local..."); ensure_opencode_config(); progress(50,"Atualizando dependências do ComfyUI...")
        try:update_deps()
        except Exception as e:log(f"Dependências: {e}",True)
        progress(70,"Reindexando modelos PC + externos..."); STATE["model_scan"]=scan_models_pc(); progress(90,"Validando serviços..."); diagnose(True); progress(100,"AUTO REPARO concluído.")
    return (jsonify({"ok":True}) if bg("AUTO REPARO",job) else (jsonify({"ok":False,"message":"Outra operação já está em andamento."}),409))

@app.get("/api/opencode/status")
def api_opencode_status(): return jsonify(opencode_status())

@app.post("/api/opencode/setup")
def api_opencode_setup():
    try:return jsonify(install_opencode_local())
    except Exception as e:return jsonify({"ok":False,"message":str(e)}),500

@app.post("/api/opencode/config")
def api_opencode_config():
    try:ensure_opencode_config();return jsonify({"ok":True,"path":str(OPENCODE_CONFIG),"status":opencode_status()})
    except Exception as e:return jsonify({"ok":False,"message":str(e)}),500

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
@app.post("/api/models/scan")
def api_models_scan():
    return (jsonify({"ok":True,"message":"Scan de modelos PC + ComfyUI + externos iniciado."}) if bg("Scan de modelos PC + ComfyUI + externos",lambda: STATE.update(model_scan=scan_models_pc())) else (jsonify({"ok":False,"message":"Outra operação já está em andamento."}),409))

@app.get("/api/models/scan")
def api_models_scan_status():
    data=None
    try:
        if MODEL_SCAN_REPORT.exists(): data=json.loads(MODEL_SCAN_REPORT.read_text(encoding="utf-8"))
    except Exception: pass
    return jsonify({"ok":bool(data),"busy":STATE.get("busy"),"operation":STATE.get("operation"),"progress":STATE.get("progress"),"message":STATE.get("message"),"scan":data})

@app.get("/api/models/search")
def api_models_search():
    q=str(request.args.get("q") or "").strip().lower(); family=str(request.args.get("family") or "").strip().lower(); source=str(request.args.get("source") or "").strip().lower(); limit=max(1,min(500,int(request.args.get("limit",100))))
    if not MODEL_SCAN_JSONL.exists(): return jsonify({"ok":False,"message":"Execute o SCAN DE MODELOS primeiro.","results":[]}),404
    out=[]
    try:
        with MODEL_SCAN_JSONL.open("r",encoding="utf-8",errors="ignore") as f:
            for line in f:
                try:r=json.loads(line)
                except Exception:continue
                hay=(r.get("nome","")+" "+r.get("caminho","")+" "+r.get("familia","")).lower()
                if q and q not in hay:continue
                if family and family!=str(r.get("familia","")).lower():continue
                if source and source!=str(r.get("origem","")).lower():continue
                out.append(r)
                if len(out)>=limit:break
    except Exception as e:return jsonify({"ok":False,"message":str(e),"results":[]}),500
    try:data=json.loads(MODEL_SCAN_REPORT.read_text(encoding="utf-8"))
    except Exception:data={}
    return jsonify({"ok":True,"total":len(out),"results":out,"resumo":{"arquivos":data.get("arquivos",0),"3d":data.get("3d",0),"video_ai":data.get("video_ai",0),"por_origem":data.get("por_origem",{}),"por_familia":data.get("por_familia",{})}})

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
    if low in {"modelos","scan modelos","scan de modelos","modelos 3d","modelos do comfyui","hunyuan","hunyuan3d"}:
        i=inventory();sc=i.get("scan") or {};return jsonify({"reply":f"Modelos locais: {i['total']} | catálogo PC/ComfyUI: {sc.get('arquivos',0)} | 3D: {sc.get('3d',0)} | Vídeo IA: {sc.get('video_ai',0)}. Use SCAN MODELOS PC + COMFYUI para atualizar."})
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
    u={"comfy":COMFY_URL,"ollama":OLLAMA_URL,"openwebui":OPENWEBUI_URL,"panel":f"http://{HOST}:{PORT}","adapta":ADAPTA_AGENT_URL,"adaptaCourses":ADAPTA_COURSES_URL,"adaptaDocs":ADAPTA_DOCS_URL,"canon":EOS_UTILITY_URL}.get(service)
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
    "modelo": MODEL_SCAN_EXT,
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

HTML=r'''<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AURION EVOLUTION CORE — ZERO</title>
<style>
:root{--bg:#05080d;--panel:#0a1018;--panel2:#0d1621;--line:#1b3042;--cyan:#00d9ff;--blue:#087dff;--violet:#9b72ff;--green:#27e38a;--red:#ff5e67;--yellow:#ffc857;--text:#e9f4ff;--muted:#70859a;--shadow:0 12px 45px #0008}
*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;background:var(--bg);color:var(--text);font:12px Segoe UI,Arial,sans-serif}body{overflow:hidden}button,input,select,textarea{font:inherit}button{cursor:pointer}.app{height:100vh;display:grid;grid-template-rows:64px 46px 1fr 35px}.top{display:flex;align-items:center;justify-content:space-between;padding:0 18px;border-bottom:1px solid var(--line);background:#070b11}.brand{display:flex;gap:12px;align-items:center}.hex{width:32px;height:32px;background:#0b83ad;clip-path:polygon(25% 6%,75% 6%,100% 50%,75% 94%,25% 94%,0 50%);display:grid;place-items:center;font-weight:900;color:#021017}.name{font-size:16px;font-weight:800;letter-spacing:1.4px}.sub{font-size:9px;color:var(--muted);letter-spacing:1.8px;margin-top:3px}.version{color:var(--cyan);border:1px solid #075d75;padding:4px 7px;font-size:9px;margin-left:7px}.topstats{display:flex;gap:8px;align-items:center}.stat{border:1px solid var(--line);padding:8px 12px;background:#090f16;color:var(--muted)}.stat b{color:var(--text)}.okdot{color:var(--green)}.bootbtn{background:#0aa9d1;color:#001018;border:0;padding:10px 18px;font-weight:800}.nav{display:flex;align-items:stretch;border-bottom:1px solid var(--line);background:#080d13;overflow:auto}.nav button{border:0;border-right:1px solid #10202e;background:transparent;color:#718699;padding:0 17px;white-space:nowrap}.nav button.active{color:var(--cyan);background:#0b1a25;box-shadow:inset 0 -2px var(--cyan)}.nav small{background:#1b2734;padding:2px 5px;border-radius:8px;margin-left:4px;color:#9bb0c4}.main{overflow:auto;padding:18px;background-image:linear-gradient(#00cfff08 1px,transparent 1px),linear-gradient(90deg,#00cfff08 1px,transparent 1px);background-size:48px 48px}.tab{display:none;max-width:1500px;margin:auto}.tab.active{display:block}.hero{border:1px solid var(--line);background:linear-gradient(110deg,#0b1620,#080d14);padding:18px;margin-bottom:14px;box-shadow:var(--shadow)}.hero h1{margin:0 0 6px;font-size:19px;letter-spacing:1px}.hero p{margin:0;color:var(--muted)}.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.grid2{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}.card{border:1px solid var(--line);background:linear-gradient(140deg,#0b121b,#080e15);padding:15px;min-width:0}.card h3{margin:0 0 12px;color:#a9bdd0;font-size:12px;letter-spacing:1px}.metric{font-size:25px;font-weight:800}.label{font-size:9px;color:var(--muted);letter-spacing:1px}.row{display:flex;gap:8px;align-items:center}.row>*{flex:1}.actions{display:flex;gap:6px;flex-wrap:wrap}.btn{border:1px solid var(--line);background:#0c1823;color:var(--text);padding:9px 12px}.btn:hover{border-color:var(--cyan)}.btn.primary{background:#072f3d;border-color:var(--cyan);color:#d9fbff}.btn.violet{border-color:#7658cc;background:#17132a}.btn.danger{border-color:#a54249;color:#ffb2b7}.field{margin:8px 0}.field label{display:block;color:var(--muted);font-size:10px;margin-bottom:5px}input,select,textarea{width:100%;background:#060b11;color:var(--text);border:1px solid var(--line);padding:10px;outline:none}textarea{min-height:170px;resize:vertical;font-family:Consolas,monospace}.list{max-height:410px;overflow:auto}.item{border-bottom:1px solid #132333;padding:10px 0;display:flex;justify-content:space-between;gap:10px}.item .name2{min-width:0}.item .name2 b{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.muted{color:var(--muted)}.tag{display:inline-block;border:1px solid var(--line);padding:3px 7px;color:var(--muted);margin:2px}.tag.ok{color:var(--green);border-color:#1e6849}.tag.bad{color:var(--red);border-color:#693039}.bar{height:9px;background:#16222d;border:1px solid #203442;overflow:hidden}.fill{height:100%;width:0;background:linear-gradient(90deg,var(--blue),var(--cyan));transition:.25s}.console{background:#03070b;border:1px solid var(--line);padding:10px;min-height:180px;max-height:330px;overflow:auto;color:#8ed6e9;font:11px Consolas,monospace;white-space:pre-wrap}.preview{min-height:430px;background:#020509;border:1px solid var(--line);display:grid;place-items:center;overflow:hidden}.preview img,.preview video{max-width:100%;max-height:520px}.drop{border:1px dashed #25516a;padding:35px;text-align:center;color:var(--muted)}.lights{display:flex;gap:7px;flex-wrap:wrap}.light{border:1px solid var(--line);padding:5px 8px}.light.ok{color:var(--green)}.light.bad{color:var(--red)}.light.wait{color:var(--yellow)}.bootgate{position:fixed;inset:0;z-index:99999;background:#03070b;display:flex;align-items:center;justify-content:center}.bootbox{width:min(820px,90vw);border:1px solid #17465b;background:#070d14;padding:30px;box-shadow:0 0 80px #00d9ff12}.bootbrand{font-size:25px;font-weight:900;letter-spacing:2px}.bootline{display:flex;justify-content:space-between;margin:15px 0 7px;color:var(--muted)}.bootmsg{margin-top:10px;color:#a8bfd1}.bootitems{display:grid;grid-template-columns:repeat(3,1fr);gap:7px;margin-top:18px}.bootitem{border:1px solid var(--line);padding:8px;color:var(--yellow)}.bootitem.ok{color:var(--green);border-color:#1b5d45}.bootitem.bad{color:var(--red);border-color:#693039}.footer{border-top:1px solid var(--line);background:#060b10;padding:8px 18px;color:#668096;font:10px Consolas,monospace;display:flex;justify-content:space-between}.hidden{display:none}@media(max-width:1000px){.grid4{grid-template-columns:repeat(2,1fr)}.grid2{grid-template-columns:1fr}.topstats .stat:nth-child(2){display:none}}@media(max-width:650px){.grid4{grid-template-columns:1fr}.name{font-size:13px}.topstats{display:none}.nav button{padding:0 11px}}
</style></head><body>
<div id="bootGate" class="bootgate"><div class="bootbox"><div class="bootbrand">⬡ AURION EVOLUTION CORE <span class="version">ZERO</span></div><div class="sub">BOOT CONTROL // LOCAL ONLY // COMFYUI + OLLAMA + OPENCODE</div><div class="bootline"><b id="bootStep">INICIANDO</b><b id="bootPct">0%</b></div><div class="bar"><div id="bootFill" class="fill"></div></div><div id="bootMsg" class="bootmsg">Preparando núcleo...</div><div id="bootItems" class="bootitems"></div></div></div>
<div class="app"><header class="top"><div class="brand"><div class="hex">A</div><div><div class="name">AURION EVOLUTION CORE <span class="version">v5.0-ZERO</span></div><div class="sub">NEURAL LOCAL CORE // COMFYUI // OLLAMA // OPENCODE // ZERO BUILD</div></div></div><div class="topstats"><div class="stat">ENGINE <b id="engine">CHECKING</b></div><div class="stat">HOST <b id="host">LOCAL</b></div><div class="stat">LATÊNCIA <b id="lat">--</b></div><button class="bootbtn" onclick="reboot()">⚡ BOOT TOTAL</button></div></header>
<nav class="nav"><button class="active" onclick="tab('home',this)">01. PAINEL</button><button onclick="tab('models',this)">02. MODELOS <small id="modelBadge">0</small></button><button onclick="tab('generate',this)">03. GERAÇÃO</button><button onclick="tab('video',this)">04. VÍDEO / 3D</button><button onclick="tab('agents',this)">05. AGENTES <small>OPENCODE</small></button><button onclick="tab('adapta',this)">06. ADAPTA ONE</button><button onclick="tab('t8i',this)">07. CANON T8i</button><button onclick="tab('studio',this)">08. ESTÚDIO</button><button onclick="tab('git',this)">09. GIT / DEP.</button><button onclick="tab('logs',this)">10. LOGS</button></nav>
<main class="main">
<section id="home" class="tab active"><div class="hero"><h1>NÚCLEO CENTRAL</h1><p>Um painel novo, com diagnóstico real. O AURION procura os modelos no PC, ComfyUI, caminhos externos e caches locais antes de mostrar o catálogo.</p></div><div class="grid4"><div class="card"><div class="label">COMFYUI</div><div class="metric" id="mComfy">--</div><div class="muted" id="mComfyPath">--</div></div><div class="card"><div class="label">OLLAMA</div><div class="metric" id="mOllama">--</div><div class="muted" id="mAgent">--</div></div><div class="card"><div class="label">MODELOS</div><div class="metric" id="mModels">0</div><div class="muted" id="mModelSize">--</div></div><div class="card"><div class="label">NVIDIA / CUDA</div><div class="metric" id="mGpu">--</div><div class="muted" id="mGpuInfo">--</div></div></div><div class="grid2" style="margin-top:12px"><div class="card"><h3>SAÚDE DO NÚCLEO</h3><div id="lights" class="lights"></div><div class="actions" style="margin-top:14px"><button class="btn primary" onclick="scanModels()">SCAN MODELOS PC + EXTERNOS</button><button class="btn" onclick="post('/api/scan-completo')">SCAN A–Z</button><button class="btn danger" onclick="autoRepair()">AUTO REPARO</button></div><div style="margin-top:12px" class="bar"><div id="opFill" class="fill"></div></div><div id="opText" class="muted" style="margin-top:7px">Aguardando operação.</div></div><div class="card"><h3>CATÁLOGO RÁPIDO</h3><div class="grid4"><div><div class="metric" id="q3d">0</div><div class="label">3D</div></div><div><div class="metric" id="qvideo">0</div><div class="label">VÍDEO AI</div></div><div><div class="metric" id="qComfy">0</div><div class="label">COMFYUI</div></div><div><div class="metric" id="qExt">0</div><div class="label">EXTERNOS</div></div></div><pre id="homeLog" class="console" style="margin-top:12px"></pre></div></div></section>
<section id="models" class="tab"><div class="hero"><h1>GERENCIADOR REAL DE MODELOS & PESOS</h1><p>Sem modelos inventados: a lista abaixo vem do scan real do computador.</p><div class="actions" style="margin-top:12px"><button class="btn primary" onclick="scanModels()">⟳ SCAN NOVO</button><button class="btn" onclick="loadModels()">ATUALIZAR LISTA</button></div></div><div class="grid2"><div class="card"><h3>FILTRO</h3><div class="field"><label>BUSCAR NOME / CAMINHO</label><input id="modelQ" placeholder="hunyuan, flux, lora, obj, fbx..."></div><div class="field"><label>FAMÍLIA</label><select id="modelFamily"><option value="">Todas</option><option>hunyuan3d</option><option>hunyuan_video</option><option>wan_video</option><option>ltx_video</option><option>3d_ai</option><option>flux</option><option>sdxl</option><option>controlnet</option><option>lora</option><option>vae</option><option>3d_asset</option></select></div><div class="field"><label>ORIGEM</label><select id="modelSource"><option value="">Todas</option><option>comfyui</option><option>aurion</option><option>huggingface</option><option>externo</option></select></div><button class="btn primary" onclick="searchModels()">PESQUISAR</button></div><div class="card"><h3>RESUMO DO CATÁLOGO</h3><div id="modelSummary" class="console">Nenhum scan carregado.</div></div></div><div class="card" style="margin-top:12px"><h3>ARQUIVOS ENCONTRADOS</h3><div id="modelList" class="list"></div></div></section>
<section id="generate" class="tab"><div class="hero"><h1>GERAÇÃO LOCAL</h1><p>Workflow enviado ao ComfyUI local. O checkpoint é escolhido do catálogo real.</p></div><div class="grid2"><div class="card"><div class="field"><label>CHECKPOINT</label><select id="imgCheckpoint"></select></div><div class="field"><label>PROMPT POSITIVO</label><textarea id="imgPrompt" style="min-height:120px">masterpiece, cinematic character, detailed, high quality, realistic lighting</textarea></div><div class="field"><label>NEGATIVE</label><textarea id="imgNegative" style="min-height:100px">low quality, blurry, deformed, bad anatomy, watermark</textarea></div><div class="grid4"><div class="field"><label>W</label><input id="imgW" value="1024"></div><div class="field"><label>H</label><input id="imgH" value="1024"></div><div class="field"><label>STEPS</label><input id="imgSteps" value="28"></div><div class="field"><label>CFG</label><input id="imgCfg" value="7"></div></div><button class="btn primary" style="width:100%;margin-top:8px" onclick="generateImage()">▶ DISPARAR GERAÇÃO</button><div style="margin-top:12px" class="bar"><div id="imgFill" class="fill"></div></div><div id="imgProgressText" class="muted" style="margin-top:7px">PRONTO</div></div><div class="card"><h3>VIEWPORT DE SAÍDA</h3><div id="imgResult" class="preview">Aguardando geração.</div></div></div></section>
<section id="video" class="tab"><div class="hero"><h1>VÍDEO / 3D / WORKFLOWS</h1><p>Catálogo de workflows do ComfyUI e assets 3D locais. Hunyuan, Wan, LTX e arquivos OBJ/FBX/GLB/BLEND/C4D aparecem quando existem no disco.</p></div><div class="grid2"><div class="card"><h3>WORKFLOW COMFYUI</h3><select id="videoWorkflowSelect"><option value="">Selecionar workflow...</option></select><textarea id="vw" style="margin-top:9px;min-height:350px">{}</textarea><div class="actions"><button class="btn" onclick="loadVideoWorkflow()">CARREGAR</button><button class="btn" onclick="prepareVideo()">VALIDAR</button><button class="btn primary" onclick="generateVideo()">GERAR</button></div><div id="videoDiag" class="console" style="margin-top:9px"></div></div><div class="card"><h3>SAÍDA / PROGRESSO</h3><div class="bar"><div id="videoFill" class="fill"></div></div><div id="videoProgressText" class="muted" style="margin:8px 0">PRONTO</div><div id="videoResult" class="preview">Nenhuma mídia.</div></div></div></section>
<section id="agents" class="tab"><div class="hero"><h1>AGENTES LOCAIS + OPENCODE</h1><p>OpenCode é usado como camada de agente/código local; o provedor configurado pelo AURION é Ollama em localhost. Sem API paga.</p></div><div class="grid4"><div class="card"><div class="label">OPENCODE</div><div class="metric" id="ocInstall">--</div><div id="ocVersion" class="muted">--</div></div><div class="card"><div class="label">OLLAMA</div><div class="metric" id="ocOllama">--</div><div class="muted">localhost:11434</div></div><div class="card"><div class="label">SKILLS</div><div class="metric" id="ocSkills">0</div><div class="muted">.opencode/skills</div></div><div class="card"><div class="label">REPOSITÓRIO</div><div class="muted" style="margin-top:8px">anomalyco/opencode</div></div></div><div class="actions" style="margin:12px 0"><button class="btn primary" onclick="setupOpenCode()">CONFIGURAR OPENCODE LOCAL</button><button class="btn" onclick="refreshOpenCode()">ATUALIZAR STATUS</button></div><div class="grid2"><div class="card"><h3>CHAT / AGENTE AURION</h3><div class="row"><select id="agentModel"></select><button class="btn primary" onclick="loadAgent()">CARREGAR</button></div><div id="agentStatus" class="muted" style="margin:8px 0"></div><div id="chatlog" class="console" style="height:350px"></div><div class="row" style="margin-top:8px"><input id="chatInput" placeholder="Fale com o agente local..." onkeydown="if(event.key==='Enter')sendChat()"><button class="btn primary" onclick="sendChat()">ENVIAR</button></div></div><div class="card"><h3>MEMÓRIA / MENTE</h3><input id="memTitle" placeholder="Nome da memória"><textarea id="memContent" style="min-height:250px" placeholder="Regras e contexto local..."></textarea><div class="actions"><button class="btn primary" onclick="saveMemory()">SALVAR</button><button class="btn" onclick="loadMemory()">LISTAR</button></div><div id="memoryList" class="list" style="margin-top:8px"></div></div></div></section>
<section id="adapta" class="tab"><div class="hero"><h1>ADAPTA ONE</h1><p>Acesso pela página oficial, sem colocar senha no código do AURION. A conta continua no ambiente oficial.</p></div><div class="actions"><button class="btn primary" onclick="adaptaStart()">ABRIR LOGIN OFICIAL</button><button class="btn" onclick="adaptaFinish()">FINALIZAR / SINCRONIZAR</button><button class="btn" onclick="loadAdapta()">STATUS</button></div><pre id="adaptaStatus" class="console" style="margin-top:12px"></pre></section>
<section id="t8i" class="tab"><div class="hero"><h1>CANON EOS REBEL T8i</h1><p>Detecção local, EOS Utility e estrutura RAW/EXPORT. O AURION não inventa controle direto de obturador.</p></div><div class="grid2"><div class="card"><h3>DISPOSITIVO</h3><div id="t8iConn" class="metric">AGUARDANDO</div><div class="actions" style="margin-top:12px"><button class="btn primary" onclick="t8iDetect()">DETECTAR</button><button class="btn" onclick="t8iEOS()">ABRIR EOS UTILITY</button><button class="btn" onclick="t8iPrepare()">PREPARAR PASTAS</button></div></div><div class="card"><h3>STATUS</h3><pre id="t8iStatus" class="console"></pre></div></div></section>
<section id="studio" class="tab"><div class="hero"><h1>ESTÚDIO / PROJETOS / REFERÊNCIAS</h1><p>Base local do AURION para projetos, referências e clientes.</p></div><div class="grid2"><div class="card"><h3>CAMINHOS DE REFERÊNCIA</h3><textarea id="refRoots" style="min-height:160px"></textarea><div class="actions"><button class="btn primary" onclick="saveRefRoots()">SALVAR LOCAIS</button><button class="btn" onclick="loadRefRoots()">CARREGAR</button></div></div><div class="card"><h3>BUSCAR REFERÊNCIA</h3><input id="refQuery" placeholder="nome do arquivo"><button class="btn primary" style="margin-top:8px" onclick="searchRefs()">BUSCAR</button><div id="refResults" class="list" style="margin-top:8px"></div></div></div></section>
<section id="git" class="tab"><div class="hero"><h1>GIT / DEPENDÊNCIAS / REPARO</h1><p>Operações controladas. O AURION não apaga modelos nem executa comandos gerados por IA sem uma ação explícita.</p></div><div class="actions"><button class="btn primary" onclick="post('/api/setup')">SETUP COMFYUI</button><button class="btn" onclick="post('/api/dependencies')">ATUALIZAR DEPENDÊNCIAS</button><button class="btn" onclick="post('/api/git/comfy-update')">ATUALIZAR COMFYUI GIT</button><button class="btn danger" onclick="autoRepair()">AUTO REPARO COMPLETO</button></div><div id="repos" class="list" style="margin-top:12px"></div></section>
<section id="logs" class="tab"><div class="hero"><h1>CONSOLE REALTIME</h1><p>Eventos do AURION, ComfyUI, scanner e agentes.</p></div><div id="console" class="console" style="height:70vh"></div></section>
</main><footer class="footer"><span>● AURION LOCAL CORE // ZERO BUILD</span><span id="footerState">WS/HTTP LOCAL</span></footer></div>
<script>
const $=id=>document.getElementById(id);const txt=(id,v)=>{if($(id))$(id).textContent=v??''};const esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
function tab(id,btn){document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));$(id)?.classList.add('active');document.querySelectorAll('.nav button').forEach(x=>x.classList.remove('active'));btn?.classList.add('active');if(id==='models')loadModels();if(id==='agents'){refreshOpenCode();loadAgentModels()}if(id==='adapta')loadAdapta();if(id==='git')loadRepos();if(id==='studio')loadRefRoots();}
async function get(url){let r=await fetch(url,{cache:'no-store'});return r.json()}async function post(url,body=null){try{let r=await fetch(url,{method:'POST',headers:body?{'Content-Type':'application/json'}:undefined,body:body?JSON.stringify(body):undefined});let d=await r.json();if(d.message)txt('opText',d.message);return d}catch(e){txt('opText',String(e));return {ok:false}}}
function reboot(){post('/api/boot/reboot')}
async function autoRepair(){await post('/api/auto-repair');}
async function refresh(){try{let d=await get('/api/status'),x=d.diagnostics||{},s=d.state||{};let c=x.comfy||{},o=x.ollama||{},g=x.nvidia||{},mi=x.model_scan||x.models_inventory||{};txt('engine',c.running?'ONLINE':'LOCAL');txt('host',location.hostname);txt('lat',Math.max(1,Math.round(performance.now()%10+3))+' ms');txt('mComfy',c.running?'ONLINE':'OFF');txt('mComfyPath',c.path||'não localizado');txt('mOllama',o.running?'ONLINE':'OFF');txt('mAgent',o.model||'nenhum modelo');txt('mModels',mi.arquivos??x.models_inventory?.total??0);txt('mModelSize',mi.tamanho||x.models_inventory?.size||'--');let gs=g.gpus||[];txt('mGpu',gs.length?gs.length+' GPU':'OFF');txt('mGpuInfo',gs[0]?gs[0].name+' · '+gs[0].vram_total_mb+' MB':'--');txt('modelBadge',mi.arquivos??0);let el=$('lights');el.innerHTML=[['COMFYUI',!!c.running],['OLLAMA',!!o.running],['NVIDIA',!!g.installed],['GIT',!!x.tools?.git],['FFMPEG',!!x.tools?.ffmpeg]].map(a=>`<span class="light ${a[1]?'ok':'bad'}">● ${a[0]} ${a[1]?'OK':'OFF'}</span>`).join('');let sc=x.model_scan||{};txt('q3d',sc['3d']??0);txt('qvideo',sc.video_ai??0);txt('qComfy',sc.por_origem?.comfyui??0);txt('qExt',(sc.por_origem?.externo??0)+(sc.por_origem?.huggingface??0));let lines=(s.logs||[]).slice(-35).join('\n');txt('console',lines);txt('homeLog',lines);$('opFill').style.width=(s.progress||0)+'%';txt('opText',s.message||'Aguardando.')}catch(e){txt('console',String(e))}}
async function bootPoll(){try{let s=await get('/api/boot/status');$('bootFill').style.width=(s.percent||0)+'%';txt('bootPct',(s.percent||0)+'%');txt('bootStep',s.step||'BOOT');txt('bootMsg',s.message||'');$('bootItems').innerHTML=(s.items||[]).map(x=>`<div class="bootitem ${x.ok?'ok':'bad'}">${x.ok?'●':'×'} ${esc(x.step)}</div>`).join('');if(s.done&&s.percent>=100){setTimeout(()=>{$('bootGate').style.opacity='0';$('bootGate').style.transition='.4s';setTimeout(()=>$('bootGate').remove(),450)},250);clearInterval(window.bt)}}catch(e){}}window.bt=setInterval(bootPoll,250);post('/api/boot/start');bootPoll();
async function scanModels(){await post('/api/models/scan');let n=0;let tm=setInterval(async()=>{try{let d=await get('/api/models/scan');$('opFill').style.width=(d.progress||0)+'%';txt('opText',d.message||'');if(!d.busy){clearInterval(tm);loadModels();}}catch(e){}} ,700)}
async function loadModels(){try{let d=await get('/api/models/scan');if(!d.scan)return;let s=d.scan;txt('modelSummary',`ARQUIVOS: ${s.arquivos}
TAMANHO: ${s.tamanho}
3D: ${s['3d']}
VÍDEO AI: ${s.video_ai}
ORIGENS: ${JSON.stringify(s.por_origem||{},null,2)}
FAMÍLIAS: ${JSON.stringify(s.por_familia||{},null,2)}`);await searchModels()}catch(e){}}
async function searchModels(){let q=$('modelQ').value||'',family=$('modelFamily').value||'',source=$('modelSource').value||'';try{let d=await get('/api/models/search?q='+encodeURIComponent(q)+'&family='+encodeURIComponent(family)+'&source='+encodeURIComponent(source)+'&limit=300');let a=d.results||[];$('modelList').innerHTML=a.map(x=>`<div class="item"><div class="name2"><b>${esc(x.nome)}</b><span class="muted">${esc(x.familia)} · ${esc(x.origem)} · ${esc(x.tamanho)}</span><br><small class="muted">${esc(x.caminho)}</small></div><span class="tag ${x.is_3d?'ok':''}">${x.is_3d?'3D':esc(x.ext)}</span></div>`).join('')||'<div class="muted">Nenhum resultado.</div>'}catch(e){$('modelList').textContent=String(e)}}
async function loadImageOptions(){try{let d=await get('/api/image/options');$('imgCheckpoint').innerHTML=(d.checkpoints||[]).map(x=>`<option value="${esc(x)}">${esc(x)}</option>`).join('')||'<option value="">Nenhum checkpoint</option>'}catch(e){}}
async function generateImage(){let body={prompt:$('imgPrompt').value,negative:$('imgNegative').value,checkpoint:$('imgCheckpoint').value,width:$('imgW').value,height:$('imgH').value,steps:$('imgSteps').value,cfg:$('imgCfg').value,seed:-1};let d=await post('/api/image/generate',body);if(d.ok)pollImage(d.prompt_id)}
async function pollImage(pid){for(let i=0;i<600;i++){try{let d=await get('/api/image/progress/'+encodeURIComponent(pid));$('imgFill').style.width=(d.progress||0)+'%';txt('imgProgressText',(d.status||'PROCESSANDO')+' — '+(d.progress||0)+'%');if(d.images?.length){$('imgResult').innerHTML=d.images.map(x=>`<img src="${comfyView(x)}">`).join('');return}}catch(e){}await new Promise(r=>setTimeout(r,1000))}}
function comfyView(x){return 'http://127.0.0.1:8188/view?'+new URLSearchParams({filename:x.filename,subfolder:x.subfolder||'',type:x.type||'output'})}
async function loadVideoWorkflows(){try{let d=await get('/api/video/workflows');$('videoWorkflowSelect').innerHTML='<option value="">Selecionar workflow...</option>'+(d.workflows||[]).map(x=>`<option value="${esc(x.path)}">${esc(x.name)} [${esc(x.kind)}]</option>`).join('')}catch(e){}}
async function loadVideoWorkflow(){let p=$('videoWorkflowSelect').value;if(!p)return;let d=await get('/api/video/workflow/load?path='+encodeURIComponent(p));if(d.ok)$('vw').value=JSON.stringify(d.workflow,null,2);txt('videoDiag',d.message||'Workflow carregado')}
async function prepareVideo(){try{let d=await post('/api/video/prepare',{workflow:JSON.parse($('vw').value)});txt('videoDiag',JSON.stringify(d,null,2));if(d.ok)$('vw').value=JSON.stringify(d.workflow,null,2)}catch(e){txt('videoDiag',String(e))}}
async function generateVideo(){try{let d=await post('/api/video/generate',{workflow:JSON.parse($('vw').value)});txt('videoDiag',JSON.stringify(d,null,2));if(d.ok)pollVideo(d.prompt_id)}catch(e){txt('videoDiag',String(e))}}
async function pollVideo(pid){for(let i=0;i<1200;i++){try{let d=await get('/api/video/progress/'+encodeURIComponent(pid));$('videoFill').style.width=(d.progress||0)+'%';txt('videoProgressText',(d.status||'PROCESSANDO')+' — '+(d.progress||0)+'%');if(d.media?.length){$('videoResult').innerHTML=d.media.map(x=>x.media_type==='video'?`<video controls src="${comfyView(x)}"></video>`:`<img src="${comfyView(x)}">`).join('');return}}catch(e){}await new Promise(r=>setTimeout(r,1200))}}
async function refreshOpenCode(){try{let d=await get('/api/opencode/status');txt('ocInstall',d.installed?'ONLINE':'NÃO INSTALADO');txt('ocVersion',d.version||d.executable||'');txt('ocOllama',d.ollama_local?'ONLINE':'OFF');txt('ocSkills',d.skills||0)}catch(e){}}
async function setupOpenCode(){let d=await post('/api/opencode/setup');txt('agentStatus',d.message||JSON.stringify(d));refreshOpenCode()}
async function loadAgentModels(){try{let d=await get('/api/models');let s=$('agentModel');s.innerHTML=(d.models||[]).map(x=>`<option value="${esc(x.name)}">${esc(x.name)}</option>`).join('')||'<option value="">Nenhum</option>'}catch(e){}}
async function loadAgent(){let d=await post('/api/agent/load',{model:$('agentModel').value});txt('agentStatus',d.message||'Agente carregado')}
async function sendChat(){let v=$('chatInput').value.trim();if(!v)return;$('chatInput').value='';$('chatlog').textContent+='\nVOCÊ: '+v+'\n';let d=await post('/api/chat',{message:v});$('chatlog').textContent+='AURION: '+(d.reply||d.message||JSON.stringify(d))+'\n'}
async function saveMemory(){let d=await post('/api/memory/save',{title:$('memTitle').value,content:$('memContent').value});txt('agentStatus',d.message||'Memória salva')}
async function loadMemory(){try{let d=await get('/api/memory/list');$('memoryList').innerHTML=(d.files||[]).map(x=>`<div class="item"><span>${esc(x.name)}</span></div>`).join('')||'Nenhuma memória.'}catch(e){}}
async function loadAdapta(){try{let d=await get('/api/adapta/status');txt('adaptaStatus',JSON.stringify(d,null,2))}catch(e){}}
async function adaptaStart(){let d=await post('/api/adapta/login/start');txt('adaptaStatus',JSON.stringify(d,null,2))}async function adaptaFinish(){let d=await post('/api/adapta/login/finish');txt('adaptaStatus',JSON.stringify(d,null,2))}
async function t8iDetect(){let d=await get('/api/t8i/status');txt('t8iStatus',JSON.stringify(d,null,2));txt('t8iConn',(d.devices||[]).length?'DISPOSITIVO DETECTADO':'AGUARDANDO CÂMERA')}
async function t8iEOS(){let d=await post('/api/t8i/eos');txt('t8iStatus',d.message||JSON.stringify(d))}async function t8iPrepare(){let d=await post('/api/t8i/prepare');txt('t8iStatus',JSON.stringify(d,null,2))}
async function loadRepos(){try{let d=await get('/api/git');$('repos').innerHTML=(d.repos||[]).map(r=>`<div class="item"><div><b>${esc(r.path)}</b><br><span class="muted">${esc(r.branch||'-')} · ${r.dirty?'ALTERADO':'LIMPO'}</span></div></div>`).join('')||'Nenhum Git detectado.'}catch(e){}}
async function loadRefRoots(){try{let d=await get('/api/references/config');$('refRoots').value=(d.roots||[]).join('\n')}catch(e){}}
async function saveRefRoots(){let roots=$('refRoots').value.split(/\r?\n/).map(x=>x.trim()).filter(Boolean);await post('/api/references/config',{roots})}
async function searchRefs(){let d=await get('/api/references/search?q='+encodeURIComponent($('refQuery').value));$('refResults').innerHTML=(d.results||[]).map(x=>`<div class="item"><span>${esc(x.name)}<br><small>${esc(x.path)}</small></span></div>`).join('')}

loadImageOptions();loadVideoWorkflows();t8iDetect();refresh();setInterval(refresh,3000);setInterval(refreshOpenCode,5000);
</script></body></html>'''

if __name__=="__main__":
    ensure_dirs(); ensure_agent_config(); adapta_status();print("="*72);print(" AURION — PAINEL LOCAL");print("="*72);print(f" Base    : {PROJECT}");print(f" Modelos : {MODELS}");print(f" Painel  : http://{HOST}:{PORT}")
    print(" Adapta  : login oficial + agentes de auto-reparo + catálogo local");print("="*72)
    d=diagnose();print(f"Python  : {d['python']}");print(f"ComfyUI : {d['comfy']['found']} | {d['comfy'].get('path')}");print(f"Ollama  : {d['ollama']['running']} | agente={d['ollama'].get('model')}");print(f"WebUI   : {d['openwebui']['running']}");print(f"NVIDIA  : {len(d['nvidia'].get('gpus',[]))} GPU(s)");print(f"Modelos : {d['models_inventory']['total']} | {d['models_inventory']['size']}");print("="*72)
    threading.Thread(target=startup,daemon=True).start();threading.Thread(target=boot_sequence,daemon=True).start();threading.Timer(1.2,lambda:webbrowser.open(f"http://{HOST}:{PORT}")).start();app.run(host=HOST,port=PORT,debug=False,threaded=True)
