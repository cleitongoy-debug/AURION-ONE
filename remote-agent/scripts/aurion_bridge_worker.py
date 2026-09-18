"""AURION ONE bridge: read-only status worker; no tokens, shell execution, or public listeners.

Runs independently of the web portal. Checks local service health and the public
GitHub repository's current main commit, and writes atomic local status JSON.
Google Drive requires an explicitly configured synced folder; it reports only
availability, never filenames or file contents. No paid-app session is reused.
"""
from __future__ import annotations

import json
import os
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "bridge_status.json"
GITHUB_REPO = "cleitongoy-debug/AURION-ONE"
INTERVAL_SECONDS = 60
STOP = False


def stop(_signal: int, _frame: object) -> None:
    global STOP
    STOP = True


def fetch_json(url: str, timeout: int = 4) -> dict:
    req = Request(url, headers={"User-Agent": "AURION-ONE-status-worker/1.0", "Accept": "application/json"})
    with urlopen(req, timeout=timeout) as response:
        data = json.load(response)
    if not isinstance(data, dict):
        raise ValueError("Unexpected JSON response")
    return data


def local_service(url: str) -> dict:
    try:
        fetch_json(url, timeout=2)
        return {"online": True}
    except (OSError, ValueError, json.JSONDecodeError, HTTPError, URLError) as exc:
        return {"online": False, "error_type": type(exc).__name__}


def github_status() -> dict:
    try:
        data = fetch_json(f"https://api.github.com/repos/{GITHUB_REPO}/commits/main", timeout=6)
        sha = str(data.get("sha", ""))
        if len(sha) != 40 or any(c not in "0123456789abcdef" for c in sha.lower()):
            raise ValueError("Commit SHA invalid")
        return {"reachable": True, "branch": "main", "head_sha": sha, "url": f"https://github.com/{GITHUB_REPO}/commit/{sha}"}
    except (OSError, ValueError, json.JSONDecodeError, HTTPError, URLError) as exc:
        return {"reachable": False, "error_type": type(exc).__name__}


def drive_status() -> dict:
    # Explicit opt-in. Never crawl Drive, inspect files or publish personal metadata.
    configured = os.environ.get("AURION_DRIVE_SYNC_DIR", "").strip()
    if not configured:
        return {"configured": False, "connected": False, "reason": "Configure AURION_DRIVE_SYNC_DIR for an authorized synced folder or implement official OAuth."}
    folder = Path(configured).expanduser()
    return {"configured": True, "connected": folder.is_dir(), "mode": "local-sync-folder-presence-only"}


def snapshot() -> dict:
    return {
        "schema_version": 1,
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "worker": "aurion-bridge-status",
        "poll_interval_seconds": INTERVAL_SECONDS,
        "github": github_status(),
        "drive": drive_status(),
        "services": {
            "aurion_pc": local_service("http://127.0.0.1:8765/health"),
            "ollama": local_service("http://127.0.0.1:11434/api/tags"),
            "comfyui": local_service("http://127.0.0.1:8188/system_stats"),
        },
        "limits": "Status only. No ChatGPT/Gemini/Drive OAuth, remote control, auto-repair, or two-way ChatGPT connection.",
    }


def write_snapshot(data: dict) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temp = OUTPUT.with_suffix(".json.tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(OUTPUT)


def main() -> int:
    signal.signal(signal.SIGINT, stop)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, stop)
    once = "--once" in sys.argv[1:]
    while not STOP:
        try:
            data = snapshot()
            write_snapshot(data)
            print("[AURION BRIDGE] Status updated", data["checked_at_utc"], flush=True)
        except Exception as exc:  # never leak request URLs or credentials
            print("[AURION BRIDGE] Status update failed:", type(exc).__name__, flush=True)
        if once:
            break
        for _ in range(INTERVAL_SECONDS):
            if STOP:
                break
            time.sleep(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
