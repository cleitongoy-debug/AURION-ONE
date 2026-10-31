#!/usr/bin/env python3
"""AURION PC-side presence probe.

READ ONLY. No ports, credentials, remote commands, restarts or data uploads.
Results are PRIVATE and apply only to the PC where executed.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# Fixed loopback endpoints. Avoid scanning an IP range or publishing inventories.
SERVICES = {
    "aurion_portal": "http://127.0.0.1:8765/health",
    "ollama_api": "http://127.0.0.1:11434/api/tags",
    "comfyui_api": "http://127.0.0.1:8188/system_stats",
}


def parse_tailnet_status(text: str) -> dict:
    """Summarize Tailscale's report without retaining any IP, DNS name or ID."""
    obj = json.loads(text)
    peers = obj.get("Peer") or {}
    if not isinstance(peers, dict):
        peers = {}
    online = sum(1 for peer in peers.values() if isinstance(peer, dict) and peer.get("Online") is True)
    own = obj.get("Self") or {}
    return {
        "source": "tailscale_status_json_LOCAL_PC",
        "backend_state": obj.get("BackendState") or "UNKNOWN",
        "self_online": own.get("Online") if isinstance(own.get("Online"), bool) else None,
        "peers_listed": len(peers),
        "peers_online_reported": online,
        "limits": "Tailnet CLI status is NOT HTTP application health or receipt from POCO/Band.",
    }


def probe_tailscale(binary: str | None = None) -> dict:
    cli = binary or shutil.which("tailscale")
    if not cli:
        return {"source": "tailscale_status_json_LOCAL_PC", "status": "CLIENT_NOT_FOUND"}
    try:
        process = subprocess.run([cli, "status", "--json"], capture_output=True,
                                 text=True, timeout=8, check=False)
        if process.returncode:
            return {"source": "tailscale_status_json_LOCAL_PC", "status": "COMMAND_FAILED"}
        return {"status": "CLI_REPLIED", **parse_tailnet_status(process.stdout)}
    except (subprocess.TimeoutExpired, OSError, UnicodeError, ValueError, KeyError):
        return {"source": "tailscale_status_json_LOCAL_PC", "status": "UNKNOWN_OR_ERROR"}


def probe_service(url: str, timeout: float = 2.5) -> str:
    # URLs are constants: loopback only. Never read or preserve response bodies.
    try:
        with urlopen(Request(url, method="GET"), timeout=timeout) as r:
            code = r.status
    except HTTPError as e:
        code = e.code
    except (OSError, URLError, TimeoutError, ValueError):
        return "UNREACHABLE"
    if code == 200:
        return "HTTP_200"
    if code in (401, 403):
        return "AUTH_REQUIRED_REACHABLE"
    return "HTTP_REACHABLE_NOT_200"


def generate_report(tailscale_binary: str | None = None) -> dict:
    return {
        "schema": "AURION_NODE_PRESENCE_V1",
        "event_id": "aurion-pc-probe-" + uuid.uuid4().hex,
        "occurred_at_utc": datetime.now(timezone.utc).isoformat(),
        "origin": "LOCAL_PC_SELF_REPORT",
        "tailscale": probe_tailscale(tailscale_binary),
        "services": {name: probe_service(url) for name, url in SERVICES.items()},
        "other_devices": {
            "poco": "NO_DEVICE_ACK_TESTED",
            "headset": "NO_DEVICE_ACK_TESTED",
            "notify_band": "NO_DEVICE_ACK_TESTED",
            "second_pc": "NO_DEVICE_ACK_TESTED",
        },
        "delivered_to_drive": False,
        "delivered_to_github": False,
        "limits": "One-time read-only local probe; online of a tailnet peer does not prove AURION service availability. This does not keep services running.",
    }


def write_private_json(out: Path, report: dict) -> None:
    target = out.expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".aurion_presence_", suffix=".tmp", dir=target.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        try:
            os.chmod(temp_name, 0o600)
        except OSError:
            pass
        os.replace(temp_name, target)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path,
                        help="Private local JSON path, not under a public Git repository")
    parser.add_argument("--tailscale-bin", default=None,
                        help="Optional local path to tailscale executable if not on PATH")
    args = parser.parse_args()
    report = generate_report(args.tailscale_bin)
    write_private_json(args.output, report)
    print("AURION_NODE_PROBE_DONE: local report created. No remote sync or device ACK inferred.")


if __name__ == "__main__":
    main()
