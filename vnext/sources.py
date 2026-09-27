"""Índice local e limitado de documentos AURION, sem rede ou embeddings."""
from __future__ import annotations

import os
import re
import threading
import unicodedata
import zipfile
from pathlib import Path
from xml.etree import ElementTree

HERE = Path(__file__).resolve().parent
KNOWN = (
    "README.md",
    "LABORATORIO_IA.md",
    "Biblia_da_Inteligencia_Artificial_AURION_ONE.docx",
    "docs/REUNIAO_OFICIAL_IA.md",
    "docs/REUNIAO_OPERACIONAL_2026-09-19.md",
    "docs/REUNIAO_OPERACIONAL_2026-09-21_EVOLUCAO_PAINEL.md",
    "docs/REUNIAO_AUTORIZACAO_NOVA_PROGRAMACAO_PAINEL_2026-09-24.md",
    "docs/AUDITORIA_BIBLIA_REUNIAO_PAINEL_2026-09-19.md",
    "docs/REFERENCIA_VISUAL_PRINCIPAL_AURION_ONE_2026-09-21.md",
)
EXT = {".md", ".txt", ".docx"}
MAX_FILE = 2 * 1024 * 1024
MAX_TOTAL = 6 * 1024 * 1024
TERM = re.compile(r"[\wÀ-ÿ]{3,}", re.UNICODE)


def terms(text):
    folded = unicodedata.normalize("NFKD", text.casefold())
    plain = "".join(ch for ch in folded if not unicodedata.combining(ch))
    return set(TERM.findall(plain))


def repository():
    choices = [
        Path(os.environ["AURION_CONTEXT_ROOT"]) if os.environ.get("AURION_CONTEXT_ROOT") else None,
        Path(r"C:\AURION-ONE"),
        HERE.parent if (HERE.parent / "LABORATORIO_IA.md").is_file() else None,
    ]
    return next((p for p in choices if p and (p / "LABORATORIO_IA.md").is_file()), None)


def read_document(path):
    if path.suffix.lower() == ".docx":
        with zipfile.ZipFile(path) as archive:
            if archive.getinfo("word/document.xml").file_size > MAX_TOTAL:
                raise ValueError("DOCX excede limite de texto")
            root = ElementTree.fromstring(archive.read("word/document.xml"))
        return " ".join(node.text for node in root.iter() if node.tag.endswith("}t") and node.text)
    return path.read_text(encoding="utf-8-sig", errors="replace")


def chunks(text, max_chars=1150):
    text = re.sub(r"\s+", " ", text).strip()
    for start in range(0, len(text), max_chars):
        part = text[start:start + max_chars]
        if part:
            yield part


class SourceIndex:
    def __init__(self):
        self.lock = threading.RLock()
        self.documents = []
        self.parts = []
        self.errors = []
        self.checked = None
        self.scan()

    def scan(self):
        from datetime import datetime, timezone
        repo = repository()
        files = [HERE / "knowledge" / "PROJECT_CONTEXT.md"]
        if repo:
            files += [repo / name for name in KNOWN]
        folder = HERE / "data" / "context"
        folder.mkdir(parents=True, exist_ok=True)
        # Importação explícita: apenas arquivos soltos nesta pasta, sem recursão.
        files += sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in EXT)[:40]
        docs, parts, errors, total = [], [], [], 0
        for path in files:
            if not path.is_file():
                continue
            try:
                size = path.stat().st_size
                if size > MAX_FILE or total + size > MAX_TOTAL:
                    errors.append(f"{path.name}: limite de tamanho")
                    continue
                value = read_document(path)
                total += size
                label = str(path.relative_to(repo)) if repo and path.is_relative_to(repo) else path.name
                docs.append({"name": label, "bytes": size, "chunks": 0})
                for n, part in enumerate(chunks(value)):
                    parts.append((label, n, part, terms(part)))
                    docs[-1]["chunks"] += 1
            except (OSError, ValueError, KeyError, zipfile.BadZipFile, ElementTree.ParseError) as exc:
                errors.append(f"{path.name}: {type(exc).__name__}")
        with self.lock:
            self.documents, self.parts, self.errors = docs, parts, errors
            self.checked = datetime.now(timezone.utc).isoformat(timespec="seconds")
        return self.summary()

    def summary(self):
        with self.lock:
            return {"checked_at": self.checked, "documents": list(self.documents),
                    "chunks": len(self.parts), "errors": list(self.errors),
                    "repository_found": repository() is not None}

    def search(self, question, limit=5):
        words = terms(question)
        with self.lock:
            scored = []
            for label, n, text, indexed_terms in self.parts:
                score = len(words & indexed_terms)
                if score:
                    scored.append((score, label, n, text))
        scored.sort(key=lambda item: (-item[0], item[1], item[2]))
        # Evitar repetição excessiva de um único arquivo.
        result, seen = [], {}
        for score, label, n, text in scored:
            if seen.get(label, 0) >= 2:
                continue
            result.append({"source": label, "section": n + 1, "excerpt": text, "score": score})
            seen[label] = seen.get(label, 0) + 1
            if len(result) >= limit:
                break
        return result
