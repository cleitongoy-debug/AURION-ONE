from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, Request, status

router = APIRouter(prefix="/api/manual-vault", tags=["manual-vault"])

ROOT = Path(__file__).resolve().parents[1] / "data" / "manual_vault"
OBJECTS = ROOT / "objects"
MANIFESTS = ROOT / "manifests"
MAX_BYTES = 128 * 1024 * 1024
RESTRICTED_NAMES = {
    "yellowstar.exe",
    "yellowstar.xdl64",
    "license",
    "otoy_credentials",
}
SAFE_NAME = re.compile(r"[^A-Za-z0-9._() #+\-]+")


def safe_original_name(value: str) -> str:
    name = Path(value.replace("\\", "/")).name.strip()
    if not name or name in {".", ".."}:
        raise ValueError("Nome de arquivo inválido")
    return SAFE_NAME.sub("_", name)[:180]


def is_restricted(name: str) -> bool:
    return name.casefold() in RESTRICTED_NAMES


def ensure_vault() -> None:
    OBJECTS.mkdir(parents=True, exist_ok=True)
    MANIFESTS.mkdir(parents=True, exist_ok=True)


def write_manifest(record: dict) -> None:
    ensure_vault()
    target = MANIFESTS / f"{record['id']}.json"
    temporary = target.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(target)


@router.get("")
async def list_vault() -> dict:
    ensure_vault()
    records = []
    for path in sorted(MANIFESTS.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        try:
            records.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            continue
    return {
        "mode": "quarantine-only",
        "execution_allowed": False,
        "count": len(records),
        "items": records[:200],
    }


@router.post("/import")
async def import_to_vault(
    request: Request,
    filename: str = Query(min_length=1, max_length=240),
) -> dict:
    try:
        original_name = safe_original_name(filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    declared_size = request.headers.get("x-aurion-file-size") or request.headers.get("content-length")
    if declared_size:
        try:
            if int(declared_size) > MAX_BYTES:
                raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Limite de 128 MB por arquivo")
        except ValueError:
            raise HTTPException(status_code=400, detail="Tamanho declarado inválido")

    ensure_vault()
    item_id = uuid.uuid4().hex
    temporary = OBJECTS / f".{item_id}.part"
    digest = hashlib.sha256()
    size = 0
    try:
        with temporary.open("xb") as handle:
            async for chunk in request.stream():
                size += len(chunk)
                if size > MAX_BYTES:
                    raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Limite de 128 MB por arquivo")
                digest.update(chunk)
                handle.write(chunk)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        temporary.unlink(missing_ok=True)
        raise

    restricted = is_restricted(original_name)
    retained = not restricted
    stored_object = None
    if restricted:
        temporary.unlink(missing_ok=True)
        state = "restricted-inventory-only"
        warning = "Metadados registrados; conteúdo descartado. O AURION não instala nem executa arquivos de licença, credenciais ou ativação."
    else:
        destination = OBJECTS / f"{item_id}.bin"
        temporary.replace(destination)
        try:
            destination.chmod(0o600)
        except OSError:
            pass
        stored_object = destination.name
        state = "quarantined-pending-validation"
        warning = "Arquivo armazenado sem extensão executável. Nenhuma instalação ou execução foi realizada."

    record = {
        "id": item_id,
        "original_name": original_name,
        "size": size,
        "sha256": digest.hexdigest(),
        "state": state,
        "retained": retained,
        "stored_object": stored_object,
        "execution_allowed": False,
        "created_at": datetime.now(UTC).isoformat(),
        "warning": warning,
    }
    write_manifest(record)
    return record
