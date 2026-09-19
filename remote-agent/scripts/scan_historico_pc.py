"""Inventario HISTORICO local e opt-in. Metadados apenas; nunca le conteudo de arquivos.
Nao publica caminhos, nomes de arquivos, tokens, documentos ou dados de saude.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

AGENT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT = AGENT_ROOT / 'data' / 'history_scan.json'
SKIP_DIRS = {'windows', 'program files', 'program files (x86)', 'programdata',
             'system volume information', '$recycle.bin', 'appdata', '.git',
             '.venv', 'venv', 'node_modules', 'site-packages', '.cache'}
TYPES = {'.py', '.ps1', '.cmd', '.bat', '.json', '.json13', '.md', '.txt', '.log',
         '.aep', '.c4d', '.blend', '.safetensors', '.ckpt', '.pt', '.pth',
         '.png', '.jpg', '.jpeg', '.mp4', '.mov', '.wav', '.html', '.js'}
MARKERS = ('aurion', 'digitalpen', 'lumen', 'comfyui', 'ollama', 'ds20', 'json13')


def bound_int(name: str, default: int, maximum: int) -> int:
    try:
        return max(1, min(int(os.environ.get(name, default)), maximum))
    except ValueError:
        return default


def roots() -> list[Path]:
    requested = os.environ.get('AURION_HISTORY_ROOTS')
    if requested:
        return [Path(x).expanduser() for x in requested.split(os.pathsep) if x]
    if os.name == 'nt':
        return [Path(f'{letter}:\\') for letter in 'CDEFGHIJKLMNOPQRSTUVWXYZ'
                if Path(f'{letter}:\\').exists()]
    return []  # Never scan a non-Windows host implicitly.


def git_count() -> int | None:
    repo = AGENT_ROOT.parent
    if not (repo / '.git').exists():
        return None
    try:
        proc = subprocess.run(['git', '-C', str(repo), 'rev-list', '--count', 'HEAD'],
                              capture_output=True, text=True, timeout=8, check=False)
        return int(proc.stdout.strip()) if proc.returncode == 0 else None
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return None


def scan() -> dict:
    started = time.monotonic()
    file_limit = bound_int('AURION_HISTORY_MAX_FILES', 250000, 2000000)
    time_limit = bound_int('AURION_HISTORY_MAX_SECONDS', 120, 900)
    counters: Counter[str] = Counter()
    years: Counter[str] = Counter()
    files = 0
    candidates = 0
    errors = 0
    earliest: float | None = None
    latest: float | None = None
    scanned_roots = 0
    partial = False
    # Only unique canonical root locations; never follow symlinks or junctions.
    root_list = list(dict.fromkeys(str(p.absolute()).casefold() for p in roots()))
    for root in root_list:
        if not Path(root).is_dir():
            continue
        scanned_roots += 1
        stack = [root]
        while stack:
            if files >= file_limit or time.monotonic() - started >= time_limit:
                partial = True
                break
            current = stack.pop()
            try:
                with os.scandir(current) as entries:
                    for entry in entries:
                        if files >= file_limit or time.monotonic() - started >= time_limit:
                            partial = True
                            break
                        try:
                            stat = entry.stat(follow_symlinks=False)
                            if entry.is_symlink() or (getattr(stat, 'st_file_attributes', 0) & 0x400):
                                continue  # Windows reparse points / junctions.
                            if entry.is_dir(follow_symlinks=False):
                                if entry.name.casefold() not in SKIP_DIRS:
                                    stack.append(entry.path)
                                continue
                            if not entry.is_file(follow_symlinks=False):
                                continue
                            files += 1
                            ext = Path(entry.name).suffix.casefold()
                            if ext in TYPES:
                                counters[ext] += 1
                            if any(marker in entry.path.casefold() for marker in MARKERS):
                                candidates += 1
                                if 0 < stat.st_mtime < time.time() + 86400:
                                    earliest = stat.st_mtime if earliest is None else min(earliest, stat.st_mtime)
                                    latest = stat.st_mtime if latest is None else max(latest, stat.st_mtime)
                                    years[str(datetime.fromtimestamp(stat.st_mtime, UTC).year)] += 1
                        except (OSError, ValueError):
                            errors += 1
            except (OSError, PermissionError):
                errors += 1
        if partial:
            break
    stamp = lambda v: datetime.fromtimestamp(v, UTC).isoformat() if v is not None else None
    result = {
        'schema_version': 1,
        'observed_at': datetime.now(UTC).isoformat(),
        'scope': 'local_drive_metadata_only',
        'complete': bool(scanned_roots and not partial and errors == 0),
        'partial': bool(partial or errors),
        'roots_scanned': scanned_roots,
        'files_examined': files,
        'aurion_related_files': candidates,
        'file_types': dict(sorted(counters.items())),
        'aurion_related_modified_years': dict(sorted(years.items())),
        'earliest_related_file_modified_at': stamp(earliest),
        'latest_related_file_modified_at': stamp(latest),
        'repo_git_commits_local': git_count(),
        'scan_errors_count': errors,
        'limits': {'files': file_limit, 'seconds': time_limit},
        'warning': 'Datas de modificacao, commits e uptime NAO sao horas de trabalho; copias podem existir. Nenhum conteudo de arquivo foi lido.',
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return result


if __name__ == '__main__':
    r = scan()
    print(f"[AURION] Metadados locais: {r['files_examined']} arquivos, {r['aurion_related_files']} candidatos; parcial={r['partial']}.")
    print('[AURION] Agregado privado salvo no PC; nenhum arquivo enviado ao GitHub.')
