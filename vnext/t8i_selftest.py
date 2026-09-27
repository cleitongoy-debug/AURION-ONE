# -*- coding: utf-8 -*-
from pathlib import Path
import json, subprocess, sys

root = Path(__file__).resolve().parents[1]
venv = root / ".venv_t8i" / "Scripts" / "python.exe"
worker = root / "vnext" / "t8i_worker.py"
print("root:", root)
print("worker:", worker.exists())
print("venv:", venv.exists())
if venv.exists():
    p = subprocess.run([str(venv), "-c", "import rawpy,PIL,numpy,exifread; print('imports-ok')"], capture_output=True, text=True)
    print(p.stdout.strip() or p.stderr.strip())
    raise SystemExit(p.returncode)
print("Ambiente ainda não instalado. Execute vnext\\INSTALAR_T8I.cmd ou use o botão da aba T8i.")
