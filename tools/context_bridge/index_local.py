#!/usr/bin/env python3
"""Read-only local AURION context inventory. No network, no AI calls, no original changes."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

TEXT_EXT = {".txt", ".md", ".json", ".jsonl", ".py", ".ps1", ".log", ".csv",
            ".html", ".htm", ".yaml", ".yml"}
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", "System32",
             "AppData", "Program Files", "Windows", "$RECYCLE.BIN", ".Trash", "cache"}
SENSITIVE = re.compile(
    r"(?:^|[.#_\- ])(?:local.?server|\.env|secrets?|creds?|credentials?|tokens?|"
    r"passwords?|api.?keys?|id_rsa|private.?key)(?:[.#_\- ]|$)", re.I
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def extract(path: Path, max_pdf_pages: int) -> tuple[str, str]:
    if path.suffix.lower() != ".pdf":
        return path.read_text(encoding="utf-8-sig", errors="replace"), "TEXT_READ"
    try:
        from pypdf import PdfReader
    except ImportError:
        return "", "PDF_NEEDS_PYPDF"
    reader = PdfReader(str(path), strict=False)
    if reader.is_encrypted:
        return "", "PDF_ENCRYPTED"
    page_count = len(reader.pages)
    content = "\n".join(reader.pages[i].extract_text() or ""
                        for i in range(min(page_count, max_pdf_pages)))
    if not content.strip():
        return "", "PDF_NEEDS_OCR"
    return content, "PDF_TEXT_PARTIAL" if page_count > max_pdf_pages else "PDF_TEXT"


def main(argv=None):
    parser = argparse.ArgumentParser(description="AURION: inventário privado de pasta local")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--include-text", action="store_true",
                        help="Opt-in; grava fragmentos de conteúdo privado somente no disco")
    parser.add_argument("--max-file-mb", type=int, default=20)
    parser.add_argument("--max-pdf-pages", type=int, default=200)
    parser.add_argument("--max-chars-per-file", type=int, default=2000000)
    parser.add_argument("--chunk-chars", type=int, default=2400)
    parser.add_argument("--limit-files", type=int, default=30000)
    args = parser.parse_args(argv)

    root = args.root.expanduser().resolve(strict=True)
    output = args.output.expanduser().resolve()
    if not root.is_dir():
        parser.error("--root precisa ser uma pasta")
    if root == output or output in root.parents or root in output.parents:
        parser.error("--output deve estar fora da árvore de entrada")
    if (args.max_file_mb < 1 or args.max_pdf_pages < 1
            or args.max_chars_per_file < 1 or args.chunk_chars < 300
            or args.limit_files < 1):
        parser.error("Limites inválidos")

    output.mkdir(parents=True, exist_ok=True)
    manifest = output / "manifest.jsonl"
    private = output / "chunks_privados.jsonl"
    counts = Counter(chunks=0)
    seen = set()
    files_considered = 0

    with manifest.open("w", encoding="utf-8") as manifest_out:
        private_out = private.open("w", encoding="utf-8") if args.include_text else None
        try:
            for parent, folders, names in os.walk(root, followlinks=False):
                folders[:] = sorted(d for d in folders
                                    if d not in SKIP_DIRS
                                    and not Path(parent, d).is_symlink())
                for name in sorted(names):
                    if files_considered >= args.limit_files:
                        counts["limit_reached"] += 1
                        break
                    path = Path(parent) / name
                    if path.is_symlink() or not path.is_file():
                        continue
                    ext = path.suffix.lower()
                    if ext not in TEXT_EXT | {".pdf"}:
                        counts["unsupported"] += 1
                        continue
                    relative = path.relative_to(root).as_posix()
                    if any(SENSITIVE.search(part) for part in path.relative_to(root).parts):
                        counts["sensitive_skipped"] += 1
                        continue

                    files_considered += 1
                    row = {"relative_path": relative, "extension": ext, "status": "PENDING"}
                    try:
                        stat = path.stat()
                        row["bytes"] = stat.st_size
                        row["modified_at_utc"] = datetime.fromtimestamp(
                            stat.st_mtime, timezone.utc).isoformat()
                        if stat.st_size > args.max_file_mb * 1024 * 1024:
                            row["status"] = "OVERSIZE_SKIPPED"
                        else:
                            digest = sha256(path)
                            row["sha256"] = digest
                            row["source_id"] = digest[:24]
                            if digest in seen:
                                row["status"] = "DUPLICATE_SHA_SKIPPED"
                            else:
                                seen.add(digest)
                                if args.include_text:
                                    text, row["status"] = extract(path, args.max_pdf_pages)
                                    if len(text) > args.max_chars_per_file:
                                        text = text[:args.max_chars_per_file]
                                        row["status"] += "_TRUNCATED"
                                    row["chars_extracted"] = len(text)
                                    for offset in range(0, len(text), args.chunk_chars):
                                        chunk_no = offset // args.chunk_chars
                                        payload = {
                                            "source_id": digest[:24],
                                            "relative_path": relative,
                                            "chunk_id": f"{digest[:24]}:{chunk_no}",
                                            "text": text[offset:offset + args.chunk_chars]
                                        }
                                        private_out.write(json.dumps(payload, ensure_ascii=False) + "\n")
                                        counts["chunks"] += 1
                                else:
                                    row["status"] = "HASH_ONLY"
                    except (OSError, ValueError, RuntimeError) as error:
                        row["status"] = "ERROR_" + type(error).__name__
                    counts[row["status"]] += 1
                    manifest_out.write(json.dumps(row, ensure_ascii=False) + "\n")
                if files_considered >= args.limit_files:
                    break
        finally:
            if private_out is not None:
                private_out.close()

    report = {
        "schema": "aurion-local-context-index-v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "root": str(root), "output": str(output),
        "files_considered": files_considered,
        "unique_hashes": len(seen),
        "include_text": args.include_text,
        "counts": dict(counts),
        "privacy": "Private local files; no auto upload or external AI request.",
        "scope": "Only files under --root; does not count any other PC, Drive or platform."
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"status": "LOCAL_INDEX_OK", "files_considered": files_considered,
                      "unique_hashes": len(seen), "chunks": counts["chunks"]},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
