"""AURION offline tests; no live Ollama, network, PC scan or real Bible needed.
Run from repo root: python tools/test_aurion_memory.py
"""
import contextlib
import io
import pathlib
import tempfile
import unittest
import zipfile
from unittest.mock import patch

import aurion_memory as mem
import aurion_chat_local as chat


class PersistentMemoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = pathlib.Path(self.tmp.name)
        self.data_patch = patch.object(mem, 'DATA', root / 'private')
        self.db_patch = patch.object(mem, 'DB', root / 'private' / 'memory.sqlite3')
        self.bible_patch = patch.object(mem, 'BIBLE', root / 'example.docx')
        for item in (self.data_patch, self.db_patch, self.bible_patch):
            item.start()
            self.addCleanup(item.stop)

    def test_explicit_memory_survives_new_connection(self):
        added, _ = mem.remember('Meu projeto usa RTX 2060')
        self.assertTrue(added)
        results = mem.recall('RTX 2060')
        self.assertEqual(results[0]['content'], 'Meu projeto usa RTX 2060')
        self.assertTrue(mem.DB.exists())
        self.assertFalse(mem.remember('Meu projeto usa RTX 2060')[0])
        self.assertTrue(mem.forget(results[0]['id']))
        self.assertEqual(mem.recall('RTX 2060'), [])

    def test_refuses_obvious_secrets(self):
        self.assertFalse(mem.remember('senha: segredo123')[0])
        self.assertFalse(mem.remember('sk-' + 'a' * 28)[0])
        self.assertEqual(mem.list_user(), [])

    def test_bible_index_and_reindex(self):
        xml = ('<?xml version="1.0"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
               '<w:body><w:p><w:r><w:t>AURION projeto de memoria</w:t></w:r></w:p>'
               '<w:p><w:r><w:t>Modelo local Ollama</w:t></w:r></w:p></w:body></w:document>')
        with zipfile.ZipFile(mem.BIBLE, 'w') as archive:
            archive.writestr('word/document.xml', xml)
        first = mem.index_bible()
        self.assertEqual(first['status'], 'indexada')
        self.assertTrue(mem.bible_status()['indexed'])
        self.assertIn('Biblia_da_Inteligencia_Artificial_AURION_ONE.docx', mem.recall('AURION memoria')[0]['source'])
        self.assertEqual(mem.index_bible()['status'], 'ja_indexada')
        self.assertFalse(mem.forget(mem.recall('AURION memoria')[0]['id']))

    def test_bible_missing_does_not_claim_indexed(self):
        with self.assertRaises(FileNotFoundError):
            mem.index_bible()
        self.assertFalse(mem.bible_status()['indexed'])

    def test_chat_system_source_not_remote_agents(self):
        self.assertIn('chat_local_private.json', str(chat.HISTORY))
        self.assertEqual(chat.BASE, 'http://127.0.0.1:11434')
        with patch.object(chat.memory, 'list_user', return_value=[]):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(chat.commands('/memorias'), 'handled')
            self.assertIn('[MEMORIAS]', output.getvalue())


if __name__ == '__main__':
    unittest.main(verbosity=2)
