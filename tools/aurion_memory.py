"""AURION persistent LOCAL memory. Python standard library only.

Private SQLite lives in remote-agent/data (gitignored); no network or shell.
Remember explicitly, retrieve using lexical overlap, and index the Bible only on
explicit /biblia command. Never put file contents or secrets in public GitHub.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sqlite3
import time
import zipfile
from collections import Counter
from xml.etree import ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / 'remote-agent' / 'data'
DB = DATA / 'aurion_memory.sqlite3'
BIBLE = ROOT / 'Biblia_da_Inteligencia_Artificial_AURION_ONE.docx'
NS = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
SENSITIVE = re.compile(r'(?i)(?:sk-[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9_]{12,}|github_pat_[A-Za-z0-9_]{12,}|AIza[A-Za-z0-9_-]{20,}|\b(?:password|senha|token|api[_ -]?key|chave[_ -]?api|cookie|authorization)\s*[:=]\s*\S+)')
WORDS = re.compile(r'[\wÀ-ÿ]{3,}', re.UNICODE)


def connection():
    DATA.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(DB), timeout=5)
    db.execute('CREATE TABLE IF NOT EXISTS memory (id INTEGER PRIMARY KEY, kind TEXT NOT NULL, source TEXT NOT NULL, content TEXT NOT NULL, digest TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)')
    db.execute('CREATE INDEX IF NOT EXISTS memory_kind ON memory(kind)')
    db.commit()
    return db


def safe(text):
    return bool(text.strip()) and len(text) <= 4000 and not SENSITIVE.search(text)


def remember(text, kind='user', source='explicit_user'):
    text = text.strip()
    if not safe(text):
        return False, 'Texto vazio, acima do limite ou possivelmente contendo credenciais; nada salvo.'
    digest = hashlib.sha256((kind + '\0' + source + '\0' + text).encode('utf-8')).hexdigest()
    with connection() as db:
        cur = db.execute('INSERT OR IGNORE INTO memory(kind,source,content,digest) VALUES(?,?,?,?)', (kind, source, text, digest))
        return bool(cur.rowcount), 'Memoria privada salva.' if cur.rowcount else 'Esta memoria ja existia.'


def forget(memory_id):
    with connection() as db:
        cur = db.execute('DELETE FROM memory WHERE id=? AND kind=?', (memory_id, 'user'))
        return bool(cur.rowcount)


def tokens(text):
    return set(WORDS.findall(text.casefold())) - {'para', 'com', 'uma', 'que', 'por', 'dos', 'das', 'isso', 'esta', 'este', 'como', 'sobre', 'voce', 'você', 'qual', 'quais', 'aqui', 'mais', 'onde'}


def recall(query, limit=5):
    target = tokens(query)
    if not target:
        return []
    with connection() as db:
        rows = db.execute('SELECT id,kind,source,content FROM memory ORDER BY id DESC LIMIT 3000').fetchall()
    matches = []
    for memory_id, kind, source, content in rows:
        overlap = len(target & tokens(content))
        if overlap:
            matches.append((overlap, memory_id, kind, source, content))
    matches.sort(key=lambda row: (row[0], row[1]), reverse=True)
    return [{'id': mid, 'kind': kind, 'source': source, 'content': content} for _, mid, kind, source, content in matches[:limit]]


def list_user(limit=12):
    with connection() as db:
        rows = db.execute("SELECT id,created_at,content FROM memory WHERE kind='user' ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [{'id': row[0], 'created_at': row[1], 'content': row[2]} for row in rows]


def bible_paragraphs():
    if not BIBLE.is_file():
        raise FileNotFoundError('Biblia nao encontrada no repositorio local.')
    if BIBLE.stat().st_size > 25_000_000:
        raise ValueError('DOCX grande demais para leitura limitada (25 MB).')
    with zipfile.ZipFile(BIBLE) as archive:
        document = archive.getinfo('word/document.xml')
        if document.file_size > 35_000_000:
            raise ValueError('XML do DOCX excede limite de 35 MB.')
        xml = archive.read(document)
    tree = ET.fromstring(xml)
    paragraphs = []
    for paragraph in tree.iter(NS + 'p'):
        value = ''.join(node.text or '' for node in paragraph.iter(NS + 't')).strip()
        if value:
            paragraphs.append(value)
    return paragraphs


def index_bible():
    paragraphs = bible_paragraphs()
    if not paragraphs:
        raise ValueError('Nao foi encontrado texto em paragrafos da Biblia. Tabelas/imagens podem exigir outro leitor.')
    chunks = []
    part = []
    size = 0
    for paragraph in paragraphs:
        for start in range(0, len(paragraph), 1000):
            segment = paragraph[start:start + 1000]
            if part and size + len(segment) > 1500:
                chunks.append('\n'.join(part))
                part, size = [], 0
            part.append(segment)
            size += len(segment)
    if part:
        chunks.append('\n'.join(part))
    if len(chunks) > 1500:
        raise ValueError('Biblia excede limite de 1500 trechos; indexacao interrompida.')
    digest = hashlib.sha256(BIBLE.read_bytes()).hexdigest()
    with connection() as db:
        old = db.execute("SELECT content FROM memory WHERE kind='bible_meta' LIMIT 1").fetchone()
        if old and old[0] == digest:
            count = db.execute("SELECT COUNT(*) FROM memory WHERE kind='bible'").fetchone()[0]
            return {'status': 'ja_indexada', 'chunks': count, 'sha256': digest[:12]}
        db.execute("DELETE FROM memory WHERE kind IN ('bible','bible_meta')")
        for i, chunk in enumerate(chunks, 1):
            db.execute('INSERT INTO memory(kind,source,content,digest) VALUES(?,?,?,?)', ('bible', 'Biblia_da_Inteligencia_Artificial_AURION_ONE.docx trecho ' + str(i), chunk, hashlib.sha256(('bible\0' + digest + '\0' + str(i)).encode('utf-8')).hexdigest()))
        db.execute('INSERT INTO memory(kind,source,content,digest) VALUES(?,?,?,?)', ('bible_meta', 'sha256', digest, hashlib.sha256(('bible_meta\0' + digest).encode('utf-8')).hexdigest()))
        db.commit()
    return {'status': 'indexada', 'chunks': len(chunks), 'paragraphs': len(paragraphs), 'sha256': digest[:12]}


def bible_status():
    with connection() as db:
        count = db.execute("SELECT COUNT(*) FROM memory WHERE kind='bible'").fetchone()[0]
        meta = db.execute("SELECT content FROM memory WHERE kind='bible_meta' LIMIT 1").fetchone()
    return {'indexed': bool(count), 'chunks': count, 'source': BIBLE.name, 'sha256': meta[0][:12] if meta else None}
