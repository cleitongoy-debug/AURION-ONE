"""AURION 5058: sondas read-only de rede, PC e nuvem. NUNCA le nem publica chaves."""
from __future__ import annotations
import json, os, subprocess, urllib.error, urllib.request
from datetime import datetime, timezone

SERVICES = {
    "evolution_5058": ("http://127.0.0.1:5058/api/one/boot", "evolution"),
    "comfyui_8188": ("http://127.0.0.1:8188/system_stats", "comfyui"),
    "ollama_11434": ("http://127.0.0.1:11434/api/tags", "ollama"),
    "openwebui_8080": ("http://127.0.0.1:8080/api/models", "webui"),
    "remote_agent_8765": ("http://127.0.0.1:8765/health", "remote_agent"),
    "quantum_8777": ("http://127.0.0.1:8777/api/status", "quantum"),
    "quantum_q2_8778": ("http://127.0.0.1:8778/api/status", "quantum"),
}

def _identity_valid(body, service):
    if not isinstance(body, dict): return service == "webui" and isinstance(body, list)
    if service == "evolution": return body.get("ok") is True and str(body.get("build", "")).startswith("2026.09.21-")
    if service == "comfyui": return "system" in body or "devices" in body
    if service == "ollama": return isinstance(body.get("models"), list)
    if service == "remote_agent": return body.get("service") == "aurion-home-node" and body.get("status") == "online"
    if service == "quantum": return "ok" in body or "study" in body or "services" in body
    return service == "webui"

def probe(url, service, *, opener=None):
    if (url, service) not in SERVICES.values(): return {"status": "BLOCKED", "http": None}
    opener = opener or urllib.request.urlopen
    req = urllib.request.Request(url, headers={"User-Agent":"AURION-ReadOnlyHealth/1"})
    try:
        with opener(req, timeout=1.2) as r:
            code = int(r.status)
            if code != 200: return {"status": "HTTP_ERROR", "http": code}
            data = json.loads(r.read(65536).decode("utf-8"))
            return {"status":"ONLINE" if _identity_valid(data,service) else "UNVERIFIED", "http":code}
    except urllib.error.HTTPError as ex:
        return {"status":"AUTH_REQUIRED" if ex.code in (401,403) else "HTTP_ERROR", "http":ex.code}
    except (OSError, ValueError, UnicodeError, TimeoutError):
        return {"status":"NO_RESPONSE", "http":None}

def _command(argv, *, runner=None):
    runner = runner or subprocess.run
    try:
        r = runner(argv, shell=False, capture_output=True, text=True, timeout=2, encoding="utf-8", errors="replace")
        return r.returncode, (r.stdout or "")[:250000]
    except (OSError, subprocess.TimeoutExpired, ValueError): return 127, ""

def tailscale_probe(*, runner=None):
    code, output = _command(["tailscale","status","--json"], runner=runner)
    if code != 0: return {"status":"UNVERIFIED","peer_count":None}
    try:
        obj = json.loads(output)
        peers = obj.get("Peer") or {}
        return {"status":"CONNECTED" if obj.get("BackendState")=="Running" else "NOT_CONNECTED",
                "peer_count":len(peers) if isinstance(peers,dict) else None}
    except (ValueError,AttributeError): return {"status":"UNVERIFIED","peer_count":None}

def adb_probe(*, runner=None):
    code,out=_command(["adb","devices"],runner=runner)
    if code != 0: return {"status":"UNVERIFIED","authorized":None}
    rows=[line.split("\t",1) for line in out.splitlines() if "\t" in line]
    ok=sum(1 for row in rows if len(row)==2 and row[1].strip()=="device")
    unauth=sum(1 for row in rows if len(row)==2 and row[1].strip()=="unauthorized")
    return {"status":"ANDROID_ADB_CONNECTED" if ok else "NO_AUTHORIZED_ANDROID",
            "authorized":ok,"unauthorized":unauth,"poco_identified":False}

def snapshot(*, opener=None, runner=None, env=None):
    env=os.environ if env is None else env
    local={name:probe(url,kind,opener=opener) for name,(url,kind) in SERVICES.items()}
    keys={"nvidia":"NVIDIA_API_KEY","groq":"GROQ_API_KEY","openai":"OPENAI_API_KEY","huggingface":"HF_TOKEN"}
    providers={name:{"configured":bool(env.get(key)),"auth":"NOT_TESTED"} for name,key in keys.items()}
    return {"build":"tri-phase-readonly-v1",
            "checked_utc":datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "trifase":{"local":local,
                "rede":{"tailscale":tailscale_probe(runner=runner),"android_adb":adb_probe(runner=runner),
                        "poco":{"status":"NOT_IDENTIFIED"},"mi_band":{"status":"NO_NOTIFY_BRIDGE"}},
                "nuvem":{"github":"CONNECTOR_SEPARATE","drive":"CONNECTOR_SEPARATE","providers":providers}},
            "agent_presence":"NOT_AUTHENTICATED","read_only":True}
