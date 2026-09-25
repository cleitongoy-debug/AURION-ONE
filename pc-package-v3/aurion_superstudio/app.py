from __future__ import annotations

import json
import os
import secrets
import shutil
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from . import __version__
from .creative3d import BLENDER_EXE, C4D_EXE, blender_status, c4d_status, ensure_3d_workspace, launch, open_path, start_blender_render
from .services import develop_cr3, inventory_base, process_image, run_ffmpeg, safe_name, service_status, sha256, unique_path
from .store import Store

MODULE_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PANEL = Path(r"C:\Users\ADM_PESS\Desktop\painelseguro#1 - Copia")
BASE_ROOT = Path(os.environ.get("AURION_PANEL_ROOT", str(DEFAULT_PANEL if DEFAULT_PANEL.exists() else MODULE_ROOT))).resolve()
DATA_ROOT = BASE_ROOT / "_aurion_superstudio"
WORKSPACE = DATA_ROOT / "workspace"
for name in ("RAW", "PREVIEWS", "EXPORTS", "CONVERSAS", "PRESETS", "LOGS", "PROJETOS", "IMPORTS"):
    (WORKSPACE / name).mkdir(parents=True, exist_ok=True)
ensure_3d_workspace(WORKSPACE)

BLENDER_JOBS: dict = {}
BLENDER_PROCESSES: dict = {}

TOKEN_FILE = DATA_ROOT / "session.token"
if not TOKEN_FILE.exists():
    TOKEN_FILE.write_text(secrets.token_urlsafe(32), encoding="utf-8")
TOKEN = TOKEN_FILE.read_text(encoding="utf-8").strip()
STORE = Store(DATA_ROOT / "aurion_memory.sqlite3")
CONFIG_FILE = DATA_ROOT / "settings.json"
DEFAULT_CONFIG = {
    "panel": "http://127.0.0.1:5058",
    "ollama": "http://127.0.0.1:11434",
    "comfy": "http://127.0.0.1:8188",
    "ffmpeg": "ffmpeg",
}


def load_config() -> dict:
    try:
        return {**DEFAULT_CONFIG, **json.loads(CONFIG_FILE.read_text(encoding="utf-8"))}
    except (OSError, json.JSONDecodeError):
        return dict(DEFAULT_CONFIG)


app = Flask(__name__, template_folder="templates", static_folder="static")
app.config.update(MAX_CONTENT_LENGTH=2 * 1024 * 1024 * 1024, JSON_AS_ASCII=False)


@app.before_request
def protect_mutations():
    protected_mobile = request.path.startswith("/api/mobile/")
    if request.method == "OPTIONS":
        return None
    if (protected_mobile or request.method not in {"GET", "HEAD"}) and request.headers.get("X-Aurion-Token") != TOKEN:
        return jsonify(ok=False, error="Token local inválido."), 401


@app.after_request
def mobile_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-Aurion-Token"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@app.get("/")
def index():
    return render_template("index.html", token=TOKEN, version=__version__, base_root=str(BASE_ROOT))


@app.get("/api/health")
def health():
    return jsonify(ok=True, status="online", version=__version__, base_root=str(BASE_ROOT), time=datetime.now(timezone.utc).isoformat())


@app.get("/api/mobile/status")
def mobile_status():
    payload = service_status(load_config())
    return jsonify(ok=True, version=__version__, ollama=payload.get("ollama"), comfy=payload.get("comfy"), computer=os.environ.get("COMPUTERNAME", "PC AURION"))


@app.get("/api/preflight")
def preflight_state():
    report = DATA_ROOT / "preflight-latest.json"
    try:
        return jsonify(ok=True, report=json.loads(report.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError) as exc:
        return jsonify(ok=False, error=f"Pré-voo ainda não disponível: {type(exc).__name__}"), 404


@app.get("/api/status")
def status():
    payload = service_status(load_config())
    payload.update({"ok": True, "version": __version__, "base": inventory_base(BASE_ROOT), "workspace": str(WORKSPACE)})
    payload["blender"] = blender_status(WORKSPACE, BLENDER_JOBS, BLENDER_PROCESSES)
    payload["c4d_octane"] = c4d_status()
    try:
        import psutil
        payload["system"] = {"cpu": psutil.cpu_percent(.2), "ram": psutil.virtual_memory().percent, "disk": psutil.disk_usage(str(BASE_ROOT.anchor)).percent}
    except Exception as exc:
        payload["system"] = {"error": str(exc)}
    return jsonify(payload)


@app.route("/api/settings", methods=["GET", "POST"])
def settings():
    if request.method == "GET":
        return jsonify(ok=True, settings=load_config())
    incoming = request.get_json(force=True) or {}
    allowed = {key: str(incoming[key]).strip() for key in DEFAULT_CONFIG if key in incoming}
    config = {**load_config(), **allowed}
    CONFIG_FILE.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    STORE.add("evidence", "Configuração atualizada", "Endpoints locais atualizados.", {"keys": list(allowed)})
    return jsonify(ok=True, settings=config)


@app.route("/api/records", methods=["GET", "POST"])
def records():
    if request.method == "GET":
        return jsonify(ok=True, records=STORE.list(request.args.get("kind", ""), request.args.get("q", "")))
    body = request.get_json(force=True) or {}
    if not str(body.get("title", "")).strip():
        return jsonify(ok=False, error="Título obrigatório."), 400
    row = STORE.add(str(body.get("kind", "memory")), str(body["title"]), str(body.get("body", "")), body.get("metadata") or {})
    return jsonify(ok=True, record=row), 201


@app.post("/api/files/import")
def import_file():
    uploaded = request.files.get("file")
    category = request.form.get("category", "IMPORTS").upper()
    if not uploaded or category not in {"RAW", "IMPORTS", "PROJETOS"}:
        return jsonify(ok=False, error="Arquivo ou categoria inválida."), 400
    target = unique_path(WORKSPACE / category, uploaded.filename or "arquivo")
    uploaded.save(target)
    result = {"name": target.name, "path": str(target), "size": target.stat().st_size, "sha256": sha256(target)}
    STORE.add("evidence", f"Importado: {target.name}", json.dumps(result, ensure_ascii=False), {"category": category})
    return jsonify(ok=True, file=result)


@app.post("/api/image/process")
def image_process():
    uploaded = request.files.get("file")
    if not uploaded:
        return jsonify(ok=False, error="Selecione uma imagem."), 400
    source = unique_path(WORKSPACE / "IMPORTS", uploaded.filename or "imagem.jpg")
    uploaded.save(source)
    output = unique_path(WORKSPACE / "EXPORTS", f"{source.stem}_AURION.jpg")
    params = json.loads(request.form.get("params", "{}"))
    info = process_image(source, output, params)
    result = {"name": output.name, "path": str(output), "sha256": sha256(output), **info}
    STORE.add("evidence", f"Imagem exportada: {output.name}", json.dumps(result, ensure_ascii=False), params)
    return jsonify(ok=True, result=result)


@app.post("/api/image/convert")
def image_convert():
    uploaded = request.files.get("file")
    output_format = request.form.get("format", "PNG").upper()
    formats = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp", "PDF": ".pdf"}
    if not uploaded or output_format not in formats:
        return jsonify(ok=False, error="Arquivo ou formato inválido."), 400
    source = unique_path(WORKSPACE / "IMPORTS", uploaded.filename or "imagem")
    uploaded.save(source)
    output = unique_path(WORKSPACE / "EXPORTS", f"{source.stem}_AURION{formats[output_format]}")
    info = process_image(source, output, {"quality": int(request.form.get("quality", 95))})
    result = {"name": output.name, "path": str(output), "format": output_format, "sha256": sha256(output), **info}
    STORE.add("evidence", f"Imagem convertida: {output.name}", json.dumps(result, ensure_ascii=False), {"format": output_format})
    return jsonify(ok=True, result=result)


@app.post("/api/t8i/develop")
def t8i_develop():
    uploaded = request.files.get("file")
    if not uploaded or Path(uploaded.filename or "").suffix.lower() != ".cr3":
        return jsonify(ok=False, error="Selecione um arquivo .CR3."), 400
    source = unique_path(WORKSPACE / "RAW", uploaded.filename)
    uploaded.save(source)
    output = unique_path(WORKSPACE / "EXPORTS", f"{source.stem}_AURION.jpg")
    try:
        result = develop_cr3(source, output, json.loads(request.form.get("params", "{}")))
    except RuntimeError as exc:
        return jsonify(ok=False, error=str(exc), imported=str(source)), 424
    STORE.add("evidence", f"CR3 revelado: {source.name}", json.dumps(result, ensure_ascii=False), {})
    return jsonify(ok=True, result=result, original=str(source))


@app.post("/api/media/convert")
def media_convert():
    uploaded = request.files.get("file")
    mode = request.form.get("mode", "")
    if not uploaded or mode not in {"audio-wav", "video-mp4"}:
        return jsonify(ok=False, error="Arquivo ou modo inválido."), 400
    source = unique_path(WORKSPACE / "IMPORTS", uploaded.filename or "midia")
    uploaded.save(source)
    suffix = ".wav" if mode == "audio-wav" else ".mp4"
    output = unique_path(WORKSPACE / "EXPORTS", f"{source.stem}_AURION{suffix}")
    try:
        result = run_ffmpeg(load_config()["ffmpeg"], source, output, mode, float(request.form.get("start", 0)), float(request.form.get("end", 60)))
    except (RuntimeError, ValueError) as exc:
        return jsonify(ok=False, error=str(exc), imported=str(source)), 424
    STORE.add("evidence", f"Mídia convertida: {output.name}", json.dumps(result, ensure_ascii=False), {"mode": mode})
    return jsonify(ok=True, result=result)


@app.post("/api/ollama/chat")
def ollama_chat():
    from .services import http_json
    body = request.get_json(force=True) or {}
    prompt, model = str(body.get("prompt", "")).strip(), str(body.get("model", "")).strip()
    if not prompt or not model:
        return jsonify(ok=False, error="Prompt e modelo são obrigatórios."), 400
    payload = {"model": model, "prompt": prompt, "stream": False}
    result = http_json(load_config()["ollama"].rstrip("/") + "/api/generate", "POST", payload, timeout=180)
    if result.get("ok"):
        STORE.add("conversation", f"Ollama · {model}", prompt + "\n\n" + str(result.get("data", {}).get("response", "")), {"model": model})
    return jsonify(result)


@app.post("/api/comfy/queue")
def comfy_queue():
    from .services import http_json
    body = request.get_json(force=True) or {}
    workflow = body.get("workflow")
    if not isinstance(workflow, dict) or not workflow:
        return jsonify(ok=False, error="Workflow API JSON obrigatório."), 400
    result = http_json(load_config()["comfy"].rstrip("/") + "/prompt", "POST", {"prompt": workflow}, timeout=20)
    if result.get("ok"):
        STORE.add("evidence", "Workflow ComfyUI enfileirado", json.dumps(result.get("data"), ensure_ascii=False), {})
    return jsonify(result)


@app.get("/api/blender/status")
def blender_state():
    return jsonify(blender_status(WORKSPACE, BLENDER_JOBS, BLENDER_PROCESSES))


@app.post("/api/blender/setup")
def blender_setup():
    paths = ensure_3d_workspace(WORKSPACE)
    STORE.add("evidence", "Workspace Blender verificado", json.dumps({key: str(value) for key, value in paths.items()}, ensure_ascii=False), {})
    return jsonify(ok=True, paths={key: str(value) for key, value in paths.items()})


@app.post("/api/blender/launch")
def blender_launch():
    try:
        result = launch(BLENDER_EXE)
    except (FileNotFoundError, OSError) as exc:
        return jsonify(ok=False, error=str(exc)), 424
    STORE.add("evidence", "Blender aberto", result["path"], result)
    return jsonify(result)


@app.post("/api/blender/open/<target>")
def blender_open(target: str):
    paths = ensure_3d_workspace(WORKSPACE)
    if target not in paths:
        return jsonify(ok=False, error="Pasta Blender inválida."), 400
    try:
        return jsonify(open_path(paths[target]))
    except (FileNotFoundError, OSError) as exc:
        return jsonify(ok=False, error=str(exc)), 424


@app.post("/api/blender/render")
def blender_render():
    try:
        job = start_blender_render(WORKSPACE, request.get_json(force=True) or {}, BLENDER_JOBS, BLENDER_PROCESSES)
    except (FileNotFoundError, OSError, ValueError) as exc:
        return jsonify(ok=False, error=str(exc)), 424
    STORE.add("evidence", "Render Blender iniciado", json.dumps(job, ensure_ascii=False), {"job": job["id"]})
    return jsonify(ok=True, job=job), 202


@app.get("/api/c4d/status")
def c4d_state():
    return jsonify(c4d_status())


@app.post("/api/c4d/launch")
def c4d_launch():
    try:
        result = launch(C4D_EXE)
    except (FileNotFoundError, OSError) as exc:
        return jsonify(ok=False, error=str(exc)), 424
    STORE.add("evidence", "Cinema 4D aberto", result["path"], result)
    return jsonify(result)


@app.errorhandler(413)
def too_large(_):
    return jsonify(ok=False, error="Arquivo excede 2 GB."), 413


def run() -> None:
    app.run(host=os.environ.get("AURION_BIND_HOST", "0.0.0.0"), port=int(os.environ.get("AURION_STUDIO_PORT", "5060")), debug=False, threaded=True)


if __name__ == "__main__":
    run()
