"""AURION context bridge: isolated offline tests, no personal files used."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "index_local.py"


class ContextIndexTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "fontes"
        self.out = Path(self.tmp.name) / "saida_privada"
        self.root.mkdir()
        (self.root / "documento.txt").write_text("ABC " * 250, encoding="utf-8")
        (self.root / "copia.md").write_text("ABC " * 250, encoding="utf-8")
        (self.root / "outro.json").write_text('{"estado":"teste"}', encoding="utf-8")
        (self.root / "LOCAL#SERVER.txt").write_text("SEGREDO", encoding="utf-8")

    def run_index(self, *flags, output=None, expected=0):
        command = [sys.executable, str(SCRIPT), "--root", str(self.root),
                   "--output", str(output or self.out), *flags]
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        if expected == 0:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
        return result

    def test_metadata_and_dedup(self):
        self.run_index()
        report = json.loads((self.out / "report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["files_considered"], 3)
        self.assertEqual(report["unique_hashes"], 2)
        self.assertEqual(report["counts"]["sensitive_skipped"], 1)
        self.assertEqual(report["counts"]["DUPLICATE_SHA_SKIPPED"], 1)
        self.assertEqual(report["counts"]["chunks"], 0)
        self.assertFalse((self.out / "chunks_privados.jsonl").exists())

    def test_explicit_private_chunks(self):
        self.run_index("--include-text", "--chunk-chars", "300")
        rows = [json.loads(line) for line in
                (self.out / "chunks_privados.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(rows), 5)
        self.assertEqual(sum(len(r["text"]) for r in rows), 1018)
        self.assertTrue(all(len(r["text"]) <= 300 for r in rows))
        self.assertNotIn("SEGREDO", json.dumps(rows))

    def test_output_overlap_denied(self):
        self.run_index(output=self.root / "inside", expected=1)
        self.run_index(output=self.root.parent, expected=1)

    def test_original_files_unchanged(self):
        before = (self.root / "documento.txt").read_bytes()
        self.run_index()
        self.assertEqual((self.root / "documento.txt").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
