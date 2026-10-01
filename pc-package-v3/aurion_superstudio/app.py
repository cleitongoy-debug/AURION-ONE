from __future__ import annotations

import importlib.util
import json
import os
import re
import secrets
import shutil
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file

from . import __version__
from .creative3d import BLENDER_EXE, C4D_EXE, blender_status, c4d_status, ensure_3d_workspace, launch, open_path, start_blender_render
from .services import develop_cr3, inventory_base, process_image, run_ffmpeg, safe_name, service_status, sha256, unique_path
from .store import Store

MODULE_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PANEL = Path(r"C:\Users\ADM_PESS\Desktop\painelseguro#1 - Copia")
BASE_ROOT = Path(os.environ.get("AURION_PANEL_ROOT", str(DEFAULT_PANEL if DEFAULT_PANEL.exists() else MODULE_ROOT))).resolve()
DATA_ROOT = BASE_ROOT / "_aurion_superstudio"
WORKSPACE = DATA_ROOT / "workspace"
for name in ("RAW", "PREVIEWS", "EXPORTS", "CONVERSAS", "PRESETS", "LOGS", "PROJETOS", "IMPORTS", "MANIFESTOS", "BACKUPS"):
    (WORKSPACE / name).mkdir(parents=True, exist_ok=True)
ensure_3d_workspace(WORKSPACE)

T8I_SETTINGS_FILE = DATA_ROOT / "t8i-settings.json"
T8I_PATH_KEYS = (
    "raw_dir",
    "export_dir",
    "conversation_dir",
    "project_dir",
    "preset_dir",
    "log_dir",
    "manifest_dir",
    "backup_dir",
)


def _t8i_default_settings() -> dict:
    return {
        "raw_dir": str(WORKSPACE / "RAW"),
        "export_dir": str(WORKSPACE / "EXPORTS"),
        "conversation_dir": str(WORKSPACE / "CONVERSAS"),
        "project_dir": str(WORKSPACE / "PROJETOS"),
        "preset_dir": str(WORKSPACE / "PRESETS"),
        "log_dir": str(WORKSPACE / "LOGS"),
        "manifest_dir": str(WORKSPACE / "MANIFESTOS"),
        "backup_dir": str(WORKSPACE / "BACKUPS"),
    }


def load_t8i_settings() -> dict:
    base = _t8i_default_settings()
    try:
        payload = json.loads(T8I_SETTINGS_FILE.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            for key in T8I_PATH_KEYS:
                value = str(payload.get(key, "")).strip()
                if value:
                    base[key] = value
    except (OSError, json.JSONDecodeError):
        pass
    return base


def save_t8i_settings(incoming: dict) -> dict:
    current = load_t8i_settings()
    for key in T8I_PATH_KEYS:
        if key not in incoming:
            continue
        raw = os.path.expandvars(str(incoming.get(key, "")).strip())
        if not raw:
            raise ValueError(f"Pasta vazia: {key}")
        path = Path(raw).expanduser()
        if not path.is_absolute():
            raise ValueError(f"Use caminho absoluto para {key}.")
        path.mkdir(parents=True, exist_ok=True)
        current[key] = str(path.resolve())
    T8I_SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = T8I_SETTINGS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(T8I_SETTINGS_FILE)
    return current


def t8i_path(key: str) -> Path:
    if key not in T8I_PATH_KEYS:
        raise KeyError(key)
    path = Path(load_t8i_settings()[key]).expanduser()
    path.mkdir(parents=True, exist_ok=True)
    return path.resolve()


def _safe_folder_name(value: str) -> str:
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", str(value or "").strip()).strip(" .")
    if not name or name in {".", ".."}:
        raise ValueError("Nome de pasta inválido.")
    return name[:120]


def _append_t8i_conversation(model: str, prompt: str, response: str) -> dict:
    folder = t8i_path("conversation_dir")
    now = datetime.now(timezone.utc)
    day = now.strftime("%Y-%m-%d")
    md = folder / f"{day}_AURION_T8I.md"
    jsonl = folder / f"{day}_AURION_T8I.jsonl"
    entry = {
        "created_at": now.isoformat(),
        "model": model,
        "prompt": prompt,
        "response": response,
    }
    with jsonl.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    with md.open("a", encoding="utf-8") as handle:
        handle.write(
            f"\n## {now.isoformat()} · {model}\n\n"
            f"### Entrada\n{prompt}\n\n"
            f"### Resposta\n{response}\n"
        )
    return {"markdown": str(md), "jsonl": str(jsonl)}


def _write_t8i_manifest(kind: str, payload: dict) -> Path:
    folder = t8i_path("manifest_dir")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = unique_path(folder, f"{stamp}_{safe_name(kind)}.json")
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def _choose_folder_windows(initial: str) -> str:
    if os.name != "nt":
        raise RuntimeError("O seletor gráfico de pastas está disponível somente no Windows.")
    env = os.environ.copy()
    env["AURION_PICK_INITIAL"] = initial
    script = (
        "Add-Type -AssemblyName System.Windows.Forms; "
        "$d=New-Object System.Windows.Forms.FolderBrowserDialog; "
        "$d.Description='AURION T8i - escolha a pasta'; "
        "if(Test-Path $env:AURION_PICK_INITIAL){$d.SelectedPath=$env:AURION_PICK_INITIAL}; "
        "if($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK){Write-Output $d.SelectedPath}"
    )
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-STA", "-Command", script],
        capture_output=True,
        text=True,
        timeout=180,
        shell=False,
        env=env,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Falha ao abrir seletor de pastas.")
    return result.stdout.strip()

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
    protected_private = (
        request.path.startswith("/api/mobile/")
        or request.path.startswith("/api/t8i/")
        or request.path.startswith("/api/records")
    )
    if request.method == "OPTIONS":
        return None
    if (protected_private or request.method not in {"GET", "HEAD"}) and request.headers.get("X-Aurion-Token") != TOKEN:
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


@app.route("/api/t8i/settings", methods=["GET", "POST"])
def t8i_settings():
    if request.method == "GET":
        settings = load_t8i_settings()
        return jsonify(
            ok=True,
            settings=settings,
            exists={key: Path(value).is_dir() for key, value in settings.items()},
        )
    body = request.get_json(silent=True) or {}
    try:
        settings = save_t8i_settings(body)
    except (OSError, ValueError) as exc:
        return jsonify(ok=False, error=str(exc)), 400
    STORE.add("evidence", "T8i · depósitos atualizados", json.dumps(settings, ensure_ascii=False), {})
    return jsonify(ok=True, settings=settings)


@app.post("/api/t8i/folder/select")
def t8i_select_folder():
    body = request.get_json(silent=True) or {}
    key = str(body.get("key", "")).strip()
    if key not in T8I_PATH_KEYS:
        return jsonify(ok=False, error="Depósito inválido."), 400
    try:
        selected = _choose_folder_windows(load_t8i_settings()[key])
        if not selected:
            return jsonify(ok=False, cancelled=True, error="Seleção cancelada."), 409
        settings = save_t8i_settings({key: selected})
    except (OSError, RuntimeError, ValueError) as exc:
        return jsonify(ok=False, error=str(exc)), 424
    STORE.add("evidence", "T8i · pasta escolhida", settings[key], {"key": key})
    return jsonify(ok=True, key=key, path=settings[key], settings=settings)


@app.post("/api/t8i/folder/create")
def t8i_create_folder():
    body = request.get_json(silent=True) or {}
    key = str(body.get("key", "")).strip()
    if key not in T8I_PATH_KEYS:
        return jsonify(ok=False, error="Depósito inválido."), 400
    try:
        child = t8i_path(key) / _safe_folder_name(body.get("name", ""))
        child.mkdir(parents=True, exist_ok=True)
    except (OSError, ValueError) as exc:
        return jsonify(ok=False, error=str(exc)), 400
    STORE.add("evidence", "T8i · subpasta criada", str(child), {"key": key})
    return jsonify(ok=True, path=str(child))


@app.post("/api/t8i/folder/open")
def t8i_open_folder():
    body = request.get_json(silent=True) or {}
    key = str(body.get("key", "")).strip()
    if key not in T8I_PATH_KEYS:
        return jsonify(ok=False, error="Depósito inválido."), 400
    try:
        return jsonify(open_path(t8i_path(key)))
    except (OSError, FileNotFoundError) as exc:
        return jsonify(ok=False, error=str(exc)), 424


def _t8i_list(root: Path, suffixes: tuple[str, ...] = (), limit: int = 80) -> list[dict]:
    rows = []
    try:
        files = [p for p in root.iterdir() if p.is_file() and (not suffixes or p.suffix.lower() in suffixes)]
        files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        for item in files[:limit]:
            stat = item.stat()
            rows.append({
                "name": item.name,
                "path": str(item),
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
            })
    except OSError:
        return []
    return rows


@app.get("/api/t8i/library")
def t8i_library():
    return jsonify(
        ok=True,
        raw=_t8i_list(t8i_path("raw_dir"), (".cr3",)),
        exports=_t8i_list(t8i_path("export_dir"), (".jpg", ".jpeg", ".png", ".tif", ".tiff")),
        conversations=_t8i_list(t8i_path("conversation_dir"), (".md", ".jsonl", ".txt")),
        projects=_t8i_list(t8i_path("project_dir")),
        manifests=_t8i_list(t8i_path("manifest_dir"), (".json",)),
    )


@app.post("/api/t8i/note")
def t8i_note():
    body = request.get_json(silent=True) or {}
    title = str(body.get("title", "")).strip() or "Nota T8i"
    text = str(body.get("body", "")).strip()
    if not text:
        return jsonify(ok=False, error="Escreva a nota antes de salvar."), 400
    record = STORE.add("conversation", title, text, {"context": "T8i"})
    files = _append_t8i_conversation("NOTA T8I", title, text)
    return jsonify(ok=True, record=record, files=files), 201


@app.post("/api/t8i/snapshot")
def t8i_snapshot():
    body = request.get_json(silent=True) or {}
    if body.get("confirm") != "SNAPSHOT_T8I":
        return jsonify(ok=False, confirmation_required=True, error="Confirmação explícita exigida: SNAPSHOT_T8I"), 409
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_dir = t8i_path("backup_dir")
    db_copy = backup_dir / f"aurion_memory_{stamp}.sqlite3"
    STORE.backup_to(db_copy)
    zip_path = unique_path(backup_dir, f"AURION_T8I_SNAPSHOT_{stamp}.zip")
    settings = load_t8i_settings()
    included = []
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(db_copy, arcname=db_copy.name)
        included.append(db_copy.name)
        if T8I_SETTINGS_FILE.exists():
            archive.write(T8I_SETTINGS_FILE, arcname="t8i-settings.json")
            included.append("t8i-settings.json")
        for key in ("conversation_dir", "preset_dir", "log_dir", "manifest_dir"):
            root = Path(settings[key])
            if not root.is_dir():
                continue
            for item in root.rglob("*"):
                if not item.is_file():
                    continue
                try:
                    rel = item.relative_to(root)
                except ValueError:
                    continue
                archive.write(item, arcname=f"{key}/{rel}")
                included.append(f"{key}/{rel}")
    try:
        db_copy.unlink()
    except OSError:
        pass
    manifest = _write_t8i_manifest(
        "snapshot_t8i",
        {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "snapshot": str(zip_path),
            "sha256": sha256(zip_path),
            "includes_media": False,
            "included_count": len(included),
            "settings": settings,
        },
    )
    STORE.add("evidence", "T8i · snapshot documental", str(zip_path), {"manifest": str(manifest)})
    return jsonify(ok=True, path=str(zip_path), sha256=sha256(zip_path), manifest=str(manifest), includes_media=False)


@app.post("/api/t8i/develop")
def t8i_develop():
    uploaded = request.files.get("file")
    if not uploaded or Path(uploaded.filename or "").suffix.lower() != ".cr3":
        return jsonify(ok=False, error="Selecione um arquivo .CR3."), 400
    params = json.loads(request.form.get("params", "{}"))
    source = unique_path(t8i_path("raw_dir"), uploaded.filename)
    uploaded.save(source)
    output_format = str(params.get("format", "JPEG")).upper()
    suffix = ".tif" if output_format == "TIFF" else ".jpg"
    output = unique_path(t8i_path("export_dir"), f"{source.stem}_AURION{suffix}")
    try:
        result = develop_cr3(source, output, params)
    except RuntimeError as exc:
        return jsonify(ok=False, error=str(exc), imported=str(source)), 424
    manifest_payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "original": str(source),
        "original_sha256": sha256(source),
        "output": str(output),
        "output_sha256": sha256(output),
        "params": params,
        "result": result,
    }
    manifest = _write_t8i_manifest("cr3_develop", manifest_payload)
    STORE.add(
        "evidence",
        f"CR3 revelado: {source.name}",
        json.dumps(manifest_payload, ensure_ascii=False),
        {"manifest": str(manifest)},
    )
    return jsonify(ok=True, result=result, original=str(source), manifest=str(manifest), download_name=output.name)


def _t8i_dependency_state() -> dict:
    modules = ("rawpy", "numpy", "imageio", "tifffile")
    return {name: bool(importlib.util.find_spec(name)) for name in modules}


@app.get("/api/mobile/t8i/status")
def t8i_status_mobile():
    state = _t8i_dependency_state()
    python_exe = MODULE_ROOT / ".venv" / "Scripts" / "python.exe"
    settings = load_t8i_settings()
    return jsonify(
        ok=True,
        ready=all(state.values()),
        modules=state,
        python=str(python_exe),
        python_exists=python_exe.is_file(),
        settings=settings,
        raw_dir=settings["raw_dir"],
        export_dir=settings["export_dir"],
        conversation_dir=settings["conversation_dir"],
        note="CR3 é RAW fotográfico; não é C-Log de vídeo. Revelação usa rawpy/LibRaw e preserva o original.",
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
    target = (t8i_path("export_dir") / filename).resolve()
    exports = t8i_path("export_dir")
    if target.parent != exports or not target.is_file():
        return jsonify(ok=False, error="Exportação T8i não encontrada."), 404
    return send_file(target, as_attachment=True, download_name=target.name)



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
        response_text = str(result.get("data", {}).get("response", ""))
        STORE.add("conversation", f"Ollama · {model}", prompt + "\n\n" + response_text, {"model": model})
        try:
            result["conversation_files"] = _append_t8i_conversation(model, prompt, response_text)
        except OSError as exc:
            result["conversation_save_warning"] = str(exc)
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
