"""AURION SPYDR — leitor incremental do acervo local e das novidades do GitHub.

Companion da AURION_COLETOR/SPYDR original, NAO substitui o motor historico.
Nao executa arquivos coletados, nao le conteudo, nao expande diretorios de sistema,
nao transmite nomes/paths, nao grava no Github, nao roda em redes de terceiros.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import stat
import sys
import time
import uuid
from collections import Counter, deque
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

VERSION = "SPYDR-RECUPERACAO-1.0"
REPO = "cleitongoy-debug/AURION-ONE"
API_BASE = f"https://api.github.com/repos/{REPO}"
DENY_DIR = {
    "windows", "program files", "program files (x86)", "programdata", "appdata",
    ".git", "node_modules", ".venv", "venv", "__pycache__", ".vs", ".gradle",
    "system volume information", "$recycle.bin", "onedrive", ".ssh", ".aws", ".config",
    "aurion_coleta", "dcim", "pictures", "downloads", "desktop_backups_sensitive"
}
DENY_FILE = re.compile(r"(?i)(\.env($|\.)|private.?key|password|senha|token|credential|secret|chaves.?privad|LOCAL#SERVER|\.pem$|\.pfx$|\.p12$|\.jks$|\.keystore$|id_rsa|\.sqlite$|\.db$)")
TARGET_EXTENSIONS = {".py", ".ps1", ".cmd", ".bat", ".md", ".json", ".js", ".html", ".yaml", ".yml", ".txt", ".log", ".kt", ".java", ".sh", ".zip", ".png", ".jpg"}
PROJECT_TERMS = ("aurion", "spydr", "aranha", "lumen", "painel", "comfy", "poco", "laboratorio", "estud", "t8i", "coletor", "morph", "china", "agente", "historia", "eu3")
MAX_FILES = 14000
MAX_FOLDERS = 3500
MAX_SECONDS = 45
MAX_MANIFEST = 12000
MAX_GH_RESULTS = 50
MAX_GH_BYTES = 350_000


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", "surrogatepass")).hexdigest()[:20]


def safe_root(root: Path) -> bool:
    try:
        r = root.resolve(strict=True)
        if not r.is_dir() or r.is_symlink():
            return False
        # Disallow scanning an entire drive/root and known sensitive system parents.
        if len(r.parts) < 2:
            return False
        return not any(p.casefold() in DENY_DIR for p in r.parts)
    except (OSError, ValueError):
        return False


def scan_roots(roots: list[Path], previous: dict, *, max_files=MAX_FILES, max_folders=MAX_FOLDERS,
               max_seconds=MAX_SECONDS) -> tuple[dict, dict]:
    seen, extensions, owners = {}, Counter(), Counter()
    before = previous.get("files", {}) if isinstance(previous, dict) else {}
    queue = deque()
    valid = []
    for path in roots:
        if safe_root(path):
            actual = str(path.resolve())
            if actual not in valid:
                valid.append(actual)
                queue.append(Path(actual))
    file_count = dir_count = errors = excluded = 0
    new = changed = unchanged = 0
    start = time.monotonic()
    names = []
    visited = set()
    while queue and file_count < max_files and dir_count < max_folders and time.monotonic() - start < max_seconds:
        current = queue.popleft()
        # Never follow symbolic links or Windows junctions.
        try:
            if current.is_symlink():
                excluded += 1
                continue
            c = str(current.resolve())
            if c in visited:
                continue
            visited.add(c)
            dir_count += 1
            with os.scandir(current) as it:
                for item in it:
                    if file_count >= max_files or time.monotonic()-start >= max_seconds:
                        break
                    try:
                        if item.is_symlink():
                            excluded += 1
                            continue
                        if item.is_dir(follow_symlinks=False):
                            if item.name.casefold() not in DENY_DIR:
                                queue.append(Path(item.path))
                            else:
                                excluded += 1
                            continue
                        if not item.is_file(follow_symlinks=False):
                            continue
                        file_count += 1
                        if DENY_FILE.search(item.name):
                            excluded += 1
                            continue
                        ext=Path(item.name).suffix.lower()
                        if ext not in TARGET_EXTENSIONS:
                            continue
                        lower=item.name.casefold()
                        if not any(term in lower or term in c.casefold() for term in PROJECT_TERMS):
                            continue
                        st=item.stat(follow_symlinks=False)
                        # Stable key without raw pathname. Never read the source bytes.
                        key=digest(os.path.normcase(os.path.abspath(item.path)).casefold())
                        sign=f"{st.st_size}:{st.st_mtime_ns}"
                        seen[key]={"sig":sign,"extension":ext,"category":"ARANHA","path_digest":key}
                        extensions[ext]+=1
                        if key not in before: new += 1
                        elif before[key].get("sig") != sign: changed += 1
                        else: unchanged += 1
                        if len(names)<25 and (key not in before or before[key].get("sig")!=sign):
                            # Only local brief filenames, no paths. These are never posted to GitHub.
                            names.append(item.name[:125])
                    except (OSError, ValueError):
                        errors += 1
        except (OSError, ValueError):
            errors += 1
    limited=bool(queue or file_count>=max_files or dir_count>=max_folders or time.monotonic()-start>=max_seconds)
    removed= len(set(before) - set(seen)) if not limited else None
    # A partial scan cannot establish deletion: retain unseen entries until a complete pass.
    persisted_files = {**before, **seen} if limited else seen
    summary={"source":"local_metadata_only","scanned_utc":utc_now(),"roots_count":len(valid),
             "folders":dir_count,"files_examined":file_count,"matched_files":len(seen),
             "new":new,"changed":changed,"unchanged":unchanged,"removed_if_complete":removed,
             "errors":errors,"skipped":excluded,"limited":limited,
             "extensions":dict(extensions),"new_filenames_local_only":names,
             "privacy":"no contents, secrets, filesystem roots, device identifiers or tokens transmitted"}
    return summary, {"files":persisted_files,"utc":summary["scanned_utc"],"limited":limited}


def github_json(url: str, opener=None):
    if not url.startswith(API_BASE+"/"):
        raise ValueError("GitHub allowlist violation")
    op = opener or urlopen
    req=Request(url,headers={"Accept":"application/vnd.github+json", "User-Agent":"AURION-SPYDR-VIGIA/1.0"})
    with op(req,timeout=6) as response:
        data=response.read(MAX_GH_BYTES+1)
    if len(data)>MAX_GH_BYTES:
        raise ValueError("GitHub response exceeded bound")
    return json.loads(data)


def github_updates(previous: dict, *, fetch=github_json) -> tuple[dict, dict]:
    # Scan MAIN and open PR HEADS, not only main. No authenticated API, no payload upload.
    try:
        meta=fetch(API_BASE+"/commits/main")
        prs=fetch(API_BASE+"/pulls?state=open&per_page=50")
        if not isinstance(prs,list): raise ValueError("Expected list")
        records={"main":str(meta["sha"])}
        entries=[]
        for pr in prs[:MAX_GH_RESULTS]:
            n=pr.get("number")
            sha=pr.get("head",{}).get("sha","")
            if not isinstance(n,int) or not re.fullmatch(r"[0-9a-f]{40}",str(sha)):
                continue
            key=f"pr-{n}"
            records[key]=sha
            if previous.get(key)!=sha:
                entries.append({"pr":n,"url":f"https://github.com/{REPO}/pull/{n}",
                                "commit_short":sha[:12],"kind":"NEW" if key not in previous else "UPDATED"})
        if previous.get("main")!=records["main"]:
            entries.append({"branch":"main","kind":"NEW_HEAD","commit_short":records["main"][:12]})
        return {"status":"REACHED","open_pr_count":len(prs),"new_or_changed":entries,
                "changed_count":len(entries),"source":"GitHub public API; does not prove PC deployment"}, records
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
        reason = "RESPONSE_TOO_LARGE" if isinstance(exc, ValueError) and "exceeded bound" in str(exc) else ("INVALID_RESPONSE" if isinstance(exc, (ValueError, KeyError, TypeError, json.JSONDecodeError)) else "NETWORK_OR_HTTP")
        return {"status":"UNREACHABLE","error_type":type(exc).__name__,"reason":reason,"changed_count":None,
                "source":"GitHub read not verified"}, previous


def read_json(path: Path, default=None):
    if default is None: default={}
    try:
        obj=json.loads(path.read_text(encoding="utf-8"))
        return obj if isinstance(obj,dict) else default
    except (OSError,ValueError):
        return default


def write_json_atomic(path: Path, obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+".pending")
    tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    os.replace(tmp,path)


def run(roots:list[Path],out:Path,*,skip_network=False,git_fetch=github_json,limits=None):
    if limits is None: limits={}
    out.mkdir(parents=True,exist_ok=True)
    # A previous snapshot that reached limits must not mark missing files as deleted.
    previous=read_json(out/"ARANHA_INDEX_PRIVADO.json")
    s,state=scan_roots(roots,previous,**limits)
    github_prev=read_json(out/"GITHUB_HEADS_PRIVADO.json")
    gh,heads=({"status":"NOT_TESTED","changed_count":None},github_prev) if skip_network else github_updates(github_prev,fetch=git_fetch)
    when=utc_now()
    report={"schema":"SPYDR_VIGIA_V1","event_id":"SPYDR_"+when[:19].replace("-","").replace(":","").replace("T","_")+"Z_"+uuid.uuid4().hex[:8],
            "time_utc":when,"build":VERSION,"read_only":True,"scan":s,"github":gh,
            "execution":{"pc":"LOCAL_SCAN_EXECUTED","drive":"NOT_CONFIRMED","poco":"NOT_CHECKED","band":"NO_BRIDGE","agents":"NO_AUTHENTICATED_ACK"}}
    write_json_atomic(out/"ARANHA_INDEX_PRIVADO.json",state)
    if gh["status"]=="REACHED":write_json_atomic(out/"GITHUB_HEADS_PRIVADO.json",heads)
    write_json_atomic(out/"RESUMO_ATUAL.json",report)
    with (out/"EVENTOS_SPYDR.jsonl").open("a",encoding="utf-8") as f:
        f.write(json.dumps({"event_id":report["event_id"],"time_utc":when,
                           "new":s["new"],"changed":s["changed"],"gh_changed":gh.get("changed_count"),"status":gh["status"]},ensure_ascii=False)+"\n")
    return report


def main():
    p=argparse.ArgumentParser(description="SPYDR / ARANHA incremental, somente leitura nas fontes")
    p.add_argument("--root",action="append",default=[],help="Raiz autorizada; nao percorre drives completos")
    p.add_argument("--out",default=str(Path(os.environ.get("LOCALAPPDATA") or Path.home())/"AURION_PRIVATE"/"SPYDR"))
    p.add_argument("--no-network",action="store_true")
    args=p.parse_args()
    report=run([Path(r) for r in args.root],Path(args.out),skip_network=args.no_network)
    print(json.dumps({"event_id":report["event_id"],"new":report["scan"]["new"],
                      "changed":report["scan"]["changed"],"folders":report["scan"]["folders"],
                      "files_examined":report["scan"]["files_examined"],"limited":report["scan"]["limited"],
                      "github_status":report["github"]["status"],"github_updates":report["github"].get("changed_count"),
                      "local_report":str(Path(args.out)/"RESUMO_ATUAL.json")},ensure_ascii=False,indent=2))

if __name__=="__main__": main()