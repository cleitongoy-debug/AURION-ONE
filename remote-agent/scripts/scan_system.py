from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "inventory.json"


def command(args: list[str]) -> str:
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=8, check=False).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""


def existing(paths: list[str]) -> list[str]:
    return [str(Path(p)) for p in paths if Path(p).exists()]


def ollama_models() -> list[str]:
    try:
        with urlopen("http://127.0.0.1:11434/api/tags", timeout=2) as response:
            data = json.load(response)
        return [m.get("name", "") for m in data.get("models", []) if m.get("name")]
    except Exception:
        return []


drives = [f"{letter}:\\" for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ" if Path(f"{letter}:\\").exists()]
common = []
for drive in drives:
    common.extend([
        f"{drive}COMFYUI", f"{drive}ComfyUI", f"{drive}AURION-QB-QUANTUN",
        f"{drive}AURION-QB-QUANTUN-FUSION", f"{drive}LUMEN#QUANTUM#AURION#Q6",
    ])

inventory = {
    "scanned_at": datetime.now(UTC).isoformat(),
    "computer": platform.node(),
    "os": platform.platform(),
    "python": platform.python_version(),
    "drives": drives,
    "gpu": command(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"]),
    "ollama": {"executable": shutil.which("ollama"), "models": ollama_models()},
    "git": shutil.which("git"),
    "ffmpeg": shutil.which("ffmpeg"),
    "known_projects": existing(common),
    "services": {
        "ollama_11434": bool(ollama_models()),
        "comfyui_8188": False,
    },
}
try:
    with urlopen("http://127.0.0.1:8188/system_stats", timeout=1):
        inventory["services"]["comfyui_8188"] = True
except Exception:
    pass

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"[AURION] Inventario salvo: {OUT}")

