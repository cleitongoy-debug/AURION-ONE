from __future__ import annotations

import importlib.util
import json
import os
import secrets
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file

from . import __version__
from .creative3d import BLENDER_EXE, C4D_EXE, blender_status, c4d_status, ensure_3d_workspace, launch, open_path, start_blender_render
from .services import develop_cr3, inventory_base, process_image, run_ffmpeg, safe_name, service_status, sha256, unique_path
from .store import Store
from . import mobile_sync

MODULE_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PANEL = Path(r"C:\Users\ADM_PESS\Desktop\painelseguro#1 - Copia")
BASE_ROOT = Path(os.environ.get("AURION_PANEL_ROOT", str(DEFAULT_PANEL if DEFAULT_PANEL.exists() else MODULE_ROOT))).resolve()
DATA_ROOT = BASE_ROOT / "_aurion_superstudio"
WORKSPACE = DATA_ROOT / "workspace"
for name in ("RAW", "PREVIEWS", "EXPORTS", "CONVERSAS", "PRESETS", "LOGS", "PROJETOS", "IMPORTS", "CERTIFICADOS"):
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


# Mesmo quando a conexao TCP chega pelo loopback, nunca aceitar Host externo:
# bloqueia DNS rebinding que poderia expor a home contendo o token de sessao.
_LOCAL_HOST = re.compile(r"^(?:localhost|127\\.0\\.0\\.1|\\[::1\\])(?::506[0-9])?$", re.IGNORECASE)

@app.before_request
def protect_mutations():
    host = request.host
    if not _LOCAL_HOST.fullmatch(host):
        return jsonify(ok=False, error="Host fora do loopback autorizado."), 403
    # HttpURLConnection do APK nao envia Origin; navegadores de sites externos sim.
    origin = request.headers.get("Origin")
    if origin and origin.lower() != "http://" + host.lower():
        return jsonify(ok=False, error="Origem do navegador nao autorizada."), 403
    protected_mobile = request.path.startswith("/api/mobile/")
    if request.method == "OPTIONS":
        return None
    if (protected_mobile or request.method not in {"GET", "HEAD"}) and request.headers.get("X-Aurion-Token") != TOKEN:
        return jsonify(ok=False, error="Token local inválido."), 401


@app.after_request
def same_origin_only(response):
    # A interface do PC e local, e a ponte USB usa HttpURLConnection nativo.
    # CORS permissivo permitiria que sites externos lessem a home com token.
    response.headers.pop("Access-Control-Allow-Origin", None)
    response.headers.pop("Access-Control-Allow-Credentials", None)
    return response


@app.get("/")
def index():
    if request.remote_addr not in {"127.0.0.1","::1"}:
        return jsonify(ok=False,error="Interface com token disponivel somente localmente."), 403
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


def _bounded_manifest(root: Path, limit: int = 240) -> list[dict]:
    rows = []
    allowed_hash = {".py", ".js", ".html", ".css", ".md", ".json", ".txt", ".cmd", ".bat", ".ps1", ".yml", ".yaml"}
    blocked_parts = {".git", ".venv", "node_modules", "__pycache__", "secrets", "credentials"}
    try:
        candidates = [p for p in root.rglob("*") if p.is_file()]
        candidates.sort(key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)
        for path in candidates:
            if len(rows) >= limit:
                break
            try:
                if any(part.lower() in blocked_parts for part in path.parts):
                    continue
                st = path.stat()
                rel = str(path.relative_to(root))
                row = {"path": rel, "bytes": st.st_size, "mtime": st.st_mtime}
                if path.suffix.lower() in allowed_hash and st.st_size <= 2 * 1024 * 1024:
                    row["sha256"] = sha256(path)
                rows.append(row)
            except (OSError, ValueError):
                continue
    except OSError:
        pass
    return rows


@app.get("/api/mobile/snapshot")
def mobile_snapshot():
    services = service_status(load_config())
    return jsonify(
        ok=True,
        time=datetime.now(timezone.utc).isoformat(),
        version=__version__,
        computer=os.environ.get("COMPUTERNAME", "PC AURION"),
        services={"panel": services.get("panel"), "ollama": services.get("ollama"), "comfy": services.get("comfy")},
        workspace=_bounded_manifest(WORKSPACE, 240),
        code_manifest=_bounded_manifest(BASE_ROOT, 180),
        records=len(STORE.list("", limit=500)),
    )


# Sincronizacao SOMENTE via loopback/USB. Porta 5060 do Super Studio;
# nao existe acesso remoto implicito, nem dependencia do V14 original.
SYNC_DB = DATA_ROOT / "mobile_sync" / "mirror.sqlite3"
SYNC_INTENT = DATA_ROOT / "mobile_sync" / "requested.flag"


@app.route("/api/mobile/memory-sync", methods=["GET", "POST"])
def mobile_memory_sync():
    if request.remote_addr not in {"127.0.0.1", "::1"}:
        return jsonify(ok=False, error="SYNC requer loopback/USB; LAN bloqueada."), 403
    if request.method == "GET":
        status = mobile_sync.state(SYNC_DB)
        status["syncRequested"] = SYNC_INTENT.exists()
        status["pcPort"] = int(os.environ.get("AURION_STUDIO_PORT", "5060"))
        return jsonify(status)
    if not mobile_sync.post_size_ok(request.content_length):
        return jsonify(ok=False, error="Payload ausente ou acima de 3MB."), 413
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise ValueError("JSON invalido")
        outcome = mobile_sync.exchange(SYNC_DB, data, STORE.database)
        SYNC_INTENT.unlink(missing_ok=True)
        return jsonify(outcome)
    except (ValueError, TypeError) as exc:
        return jsonify(ok=False, error=str(exc)), 400


@app.post("/api/mobile/memory-sync/request")
def request_memory_sync():
    if request.remote_addr not in {"127.0.0.1", "::1"}:
        return jsonify(ok=False, error="Operacao local apenas."), 403
    SYNC_INTENT.parent.mkdir(parents=True, exist_ok=True)
    SYNC_INTENT.write_text(datetime.now(timezone.utc).isoformat(), encoding="utf-8")
    return jsonify(ok=True, requested=True,
                   message="Pedido local registrado; o POCO fara sync ao conectar e conferir o pedido.")


@app.route("/api/mobile/dedication", methods=["GET", "POST"])
def dedication():
    if request.method == "POST":
        body = request.get_json(silent=True) or {}
        events = body.get("events", [])
        if not isinstance(events, list) or len(events) > 200:
            return jsonify(ok=False, error="Lote inválido (máximo 200 registros)."), 400
        inserted = STORE.put_dedication(events)
        return jsonify(ok=True, inserted=inserted, events=STORE.dedication())
    return jsonify(ok=True, events=STORE.dedication())


@app.route("/api/mobile/certificates", methods=["GET", "POST"])
def certificates():
    if request.method == "GET":
        return jsonify(ok=True, certificates=STORE.list("certificate", limit=500))
    uploaded = request.files.get("file")
    if not uploaded or not uploaded.filename:
        return jsonify(ok=False, error="Escolha o certificado ou print."), 400
    original = uploaded.filename
    if Path(original).suffix.lower() not in {".pdf", ".png", ".jpg", ".jpeg", ".webp"}:
        return jsonify(ok=False, error="Formato aceito: PDF, PNG, JPG ou WebP."), 400
    target = unique_path(WORKSPACE / "CERTIFICADOS", original)
    target.parent.mkdir(parents=True, exist_ok=True)
    uploaded.save(target)
    try:
        hours = float(request.form.get("hours", "0") or 0)
        if not 0 <= hours <= 100000:
            raise ValueError()
    except ValueError:
        target.unlink(missing_ok=True)
        return jsonify(ok=False, error="Horas documentadas inválidas."), 400
    metadata = {"course": request.form.get("course", "")[:200], "project": request.form.get("project", "")[:200],
                "hours": hours, "hoursBasis": request.form.get("hours_basis", "não indicado")[:200],
                "sha256": sha256(target), "bytes": target.stat().st_size, "file": str(target), "source": "pc"}
    for existing in STORE.list("certificate", limit=500):
        if existing["metadata"].get("sha256") == metadata["sha256"]:
            target.unlink(missing_ok=True)
            return jsonify(ok=True, certificate=existing, duplicate=True)
    record = STORE.add("certificate", original, "Documento fornecido pelo operador; dados aguardam conferência humana.", metadata)
    return jsonify(ok=True, certificate=record), 201


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
    return jsonify(ok=True, result=result, original=str(source), download_name=output.name)




def _t8i_dependency_state() -> dict:
    modules = ("rawpy", "numpy", "imageio", "tifffile")
    return {name: bool(importlib.util.find_spec(name)) for name in modules}


@app.get("/api/mobile/t8i/status")
def t8i_status_mobile():
    state = _t8i_dependency_state()
    python_exe = MODULE_ROOT / ".venv" / "Scripts" / "python.exe"
    return jsonify(
        ok=True,
        ready=all(state.values()),
        modules=state,
        python=str(python_exe),
        python_exists=python_exe.is_file(),
        raw_dir=str(WORKSPACE / "RAW"),
        export_dir=str(WORKSPACE / "EXPORTS"),
        note="CR3 é RAW de fotografia; revelação usa rawpy/LibRaw e preserva o original.",
    )


@app.post("/api/mobile/t8i/deps/install")
def t8i_install_deps_mobile():
    body = request.get_json(silent=True) or {}
    if body.get("confirm") != "INSTALAR_T8I":
        return jsonify(ok=False, confirmation_required=True, error="Confirmação explícita exigida: INSTALAR_T8I"), 409
    python_exe = MODULE_ROOT / ".venv" / "Scripts" / "python.exe"
    requirements = MODULE_ROOT / "requirements-t8i.txt"
    if not python_exe.is_file():
        return jsonify(ok=False, error="Ambiente .venv do Super Studio não encontrado. Execute a instalação base primeiro."), 424
    if not requirements.is_file():
        return jsonify(ok=False, error="requirements-t8i.txt não encontrado."), 424
    command = [
        str(python_exe), "-m", "pip", "install",
        "--disable-pip-version-check", "--no-input",
        "-r", str(requirements),
    ]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=900,
            shell=False,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        STORE.add("evidence", "Suporte T8i · instalação falhou", str(exc), {"command": command})
        return jsonify(ok=False, error=f"{type(exc).__name__}: {exc}"), 424
    state = _t8i_dependency_state()
    evidence = {
        "returncode": result.returncode,
        "modules": state,
        "stdout_tail": result.stdout[-4000:],
        "stderr_tail": result.stderr[-4000:],
    }
    STORE.add("evidence", "Suporte T8i · instalação", json.dumps(evidence, ensure_ascii=False), {"command": command})
    return jsonify(ok=result.returncode == 0 and all(state.values()), ready=all(state.values()), **evidence), (200 if result.returncode == 0 else 424)


@app.get("/api/mobile/t8i/export/<path:name>")
def t8i_export_mobile(name: str):
    filename = safe_name(name)
    target = (WORKSPACE / "EXPORTS" / filename).resolve()
    exports = (WORKSPACE / "EXPORTS").resolve()
    if target.parent != exports or not target.is_file():
        return jsonify(ok=False, error="Exportação T8i não encontrada."), 404
    return send_file(target, as_attachment=True, download_name=target.name, mimetype="image/jpeg")


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
    app.run(host=os.environ.get("AURION_BIND_HOST", "127.0.0.1"), port=int(os.environ.get("AURION_STUDIO_PORT", "5060")), debug=False, threaded=True)


if __name__ == "__main__":
    run()
