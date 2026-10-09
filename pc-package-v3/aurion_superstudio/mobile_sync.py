"""POCO <-> PC: memoria textual local, opt-in e idempotente.
Nao le Drive, nao executa comandos e nao sincroniza segredos/arquivos.
Somente loopback/USB ADB reverse (autenticacao feita pelo app.py).
"""
from __future__ import annotations
import hashlib
import json
import re
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

ALLOWED = {"memory", "reference", "conversation", "project", "preset", "evidence", "sync_event", "experiment"}
MAX_RECORDS = 4000
MAX_BYTES = 3_000_000
LOCK = threading.RLock()
SENSITIVE = re.compile(r"(?i)(sk-proj-|gsk_[A-Za-z0-9]{12}|nvapi-[A-Za-z0-9]{12}|gh[pousr]_[A-Za-z0-9]{12}|hf_[A-Za-z0-9]{20}|local#server|\.webui_secret_key|(?:api[_ -]?key|access[_ -]?token|password|senha|secret)\s*[:=])")


def _fingerprint(obj: dict) -> str:
    # Mesmo protocolo Android: len em 4 bytes big endian + bytes UTF-8 dos 4 campos.
    h = hashlib.sha256()
    for field in ("type", "title", "body", "meta"):
        raw = str(obj[field]).encode("utf-8")
        h.update(len(raw).to_bytes(4, "big"))
        h.update(raw)
    return h.hexdigest()


def _canonical(item: dict) -> dict:
    if not isinstance(item, dict):
        raise ValueError("registro_nao_objeto")
    ty, title, body, meta = (item.get(k) for k in ("type", "title", "body", "meta"))
    if not all(isinstance(v, str) for v in (ty, title, body, meta)):
        raise ValueError("campos_invalidos")
    if ty not in ALLOWED or not title.strip():
        raise ValueError("tipo_ou_titulo_invalido")
    if len(title) > 200 or len(body) > 15000 or len(meta) > 5000 or len(ty) > 40:
        raise ValueError("registro_muito_grande")
    if SENSITIVE.search(title) or SENSITIVE.search(body) or SENSITIVE.search(meta):
        raise ValueError("segredo_potencial")
    # Timestamps sao apenas metadados historicos; nunca se convertem em horas estudadas.
    created, updated = item.get("createdAt", 0), item.get("updatedAt", 0)
    if not isinstance(created, int) or not isinstance(updated, int):
        raise ValueError("data_invalida")
    return dict(type=ty, title=title, body=body, meta=meta, createdAt=max(0,created), updatedAt=max(0,updated))


def _database(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("""CREATE TABLE IF NOT EXISTS sync_records(
      fingerprint TEXT PRIMARY KEY, payload TEXT NOT NULL, first_seen TEXT NOT NULL
    )""")
    db.commit()
    return db


def state(path: Path) -> dict:
    with LOCK, _database(path) as db:
        n = db.execute("SELECT count(*) FROM sync_records").fetchone()[0]
        stamp = db.execute("SELECT max(first_seen) FROM sync_records").fetchone()[0]
    return dict(ok=True, format="aurion-pc-poco-v1", phoneMirroredRecords=n,
                lastReceivedAt=stamp, phoneConnectedNow=False,
                pcToPhoneExportsVerified=False, physicalTest="PENDENTE")


def exchange(path: Path, request: dict) -> dict:
    if not isinstance(request, dict) or request.get("format") != "aurion-memory-v4" or request.get("profile") != "anark":
        raise ValueError("formato_ou_perfil_invalidos")
    rows=request.get("records")
    if not isinstance(rows, list) or len(rows)>MAX_RECORDS:
        raise ValueError("quantidade_de_registros_invalida")
    if request.get("recordCount") != len(rows):
        raise ValueError("contagem_do_backup_divergente")
    normalized=[_canonical(x) for x in rows]  # Tudo validado ANTES de escrita.
    inserted=0
    now=datetime.now(timezone.utc).isoformat()
    with LOCK, _database(path) as db:
        db.execute("BEGIN IMMEDIATE")
        for item in normalized:
            fp=_fingerprint(item)
            encoded=json.dumps(item,ensure_ascii=False,separators=(",",":"))
            inserted+=db.execute("INSERT OR IGNORE INTO sync_records VALUES(?,?,?)",(fp,encoded,now)).rowcount
        pc_items=[json.loads(x[0]) for x in db.execute("SELECT payload FROM sync_records ORDER BY fingerprint")]
        payload=json.dumps(pc_items,ensure_ascii=False,separators=(",",":"))
        if len(payload.encode("utf-8"))>MAX_BYTES or len(pc_items)>MAX_RECORDS:
            raise ValueError("resposta_excede_limite_sem_truncamento")
        # WITH fecha a transacao so se todos os passos tiverem passado.
        db.commit()
    h=hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return dict(ok=True, format="aurion-pc-poco-v1", profile="anark",
                records=pc_items, recordCount=len(pc_items), received=len(rows),
                pcNew=inserted, pcDuplicates=len(rows)-inserted, responseSha256=h,
                serverReceiptAt=now,
                pcReceipt="COMMIT_SQLITE", phoneReceipt="AGUARDANDO_IMPORTACAO_E_READBACK")


def post_size_ok(content_length: int | None) -> bool:
    return content_length is not None and 0<content_length<=MAX_BYTES
