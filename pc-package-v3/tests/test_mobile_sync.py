"""Contract tests: isolated temp SQLite, never touches a Windows PC or phone."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from aurion_superstudio import mobile_sync


class MobileMemoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.mirror=self.root/"mirror.sqlite"
    def tearDown(self):
        self.tmp.cleanup()

    def row(self, index):
        return dict(type="memory",title=f"Estudo {index:04d}",body=f"registro verificavel {index}",
                    meta='{"evidence":"TESTE_SINTETICO"}',createdAt=1780000000000+index,updatedAt=1780000000000+index)
    def payload(self, rows, profile="anark"):
        return dict(format="aurion-memory-v4",profile=profile,recordCount=len(rows),records=rows)

    def test_1001_no_truncation_and_repeat(self):
        rows=[self.row(i) for i in range(1001)]
        first=mobile_sync.exchange(self.mirror,self.payload(rows))
        self.assertEqual(first["recordCount"],1001)
        self.assertEqual(first["pcNew"],1001)
        again=mobile_sync.exchange(self.mirror,self.payload(rows))
        self.assertEqual(again["pcNew"],0)
        self.assertEqual(again["recordCount"],1001)
        self.assertEqual(mobile_sync.state(self.mirror)["phoneMirroredRecords"],1001)

    def test_invalid_source_does_not_modify_database(self):
        one=mobile_sync.exchange(self.mirror,self.payload([self.row(1)]))
        self.assertEqual(one["recordCount"],1)
        with self.assertRaisesRegex(ValueError,"formato_ou_perfil"):
            mobile_sync.exchange(self.mirror,self.payload([self.row(2)],"outro"))
        with self.assertRaisesRegex(ValueError,"segredo_potencial"):
            danger=self.row(5)
            danger["body"]="senha:valor_que_nao_pode_sair"
            mobile_sync.exchange(self.mirror,self.payload([self.row(3),danger]))
        self.assertEqual(mobile_sync.state(self.mirror)["phoneMirroredRecords"],1)

    def test_pc_native_bidirectional(self):
        source=self.root/"pc.sqlite"
        with sqlite3.connect(source) as db:
            db.execute("CREATE TABLE records(id INTEGER PRIMARY KEY,kind TEXT,title TEXT,body TEXT,metadata TEXT,created_at TEXT,updated_at TEXT)")
            db.execute("INSERT INTO records VALUES(1,'memory','Memoria PC','Aprendizado documentado','{}','2026-10-09T10:00:00+00:00','2026-10-09T10:00:00+00:00')")
            db.execute("INSERT INTO records VALUES(2,'memory','Credencial','api_key=SEGREDO','{}','2026-10-09T10:00:00+00:00','2026-10-09T10:00:00+00:00')")
        answer=mobile_sync.exchange(self.mirror,self.payload([self.row(9)]),source)
        self.assertEqual(answer["recordCount"],2)
        self.assertIn("Memoria PC",[r["title"] for r in answer["records"]])
        self.assertNotIn("Credencial",[r["title"] for r in answer["records"]])
        again=mobile_sync.exchange(self.mirror,self.payload([self.row(9)]),source)
        self.assertEqual(again["recordCount"],2)
        self.assertEqual(again["pcNew"],0)


    def test_json_metadata_credentials_are_rejected_before_writes(self):
        baseline=mobile_sync.exchange(self.mirror,self.payload([self.row(1)]))
        self.assertEqual(baseline["recordCount"],1)
        for meta in (
            '{"api_key":"TEST_ONLY_FAKE_VALUE"}',
            '{"nested":{"access_token":"TEST_ONLY_FAKE_VALUE"}}',
            '{"records":[{"client_secret":"TEST_ONLY_FAKE_VALUE"}]}',
            '{"cookie":"TEST_ONLY_FAKE_VALUE"}',
        ):
            dangerous=self.row(77)
            dangerous["meta"]=meta
            with self.subTest(meta=meta), self.assertRaisesRegex(ValueError,"segredo_potencial"):
                mobile_sync.exchange(self.mirror,self.payload([self.row(3),dangerous]))
            self.assertEqual(mobile_sync.state(self.mirror)["phoneMirroredRecords"],1)

    def test_json_metadata_safe_fields_still_sync(self):
        row=self.row(18)
        row["meta"]='{"source":"TESTE_LOCAL","evidence":{"kind":"DOC","date":"2026-10-09"}}'
        result=mobile_sync.exchange(self.mirror,self.payload([row]))
        self.assertEqual(result["recordCount"],1)

    def test_invalid_counts_and_size_guard(self):
        with self.assertRaisesRegex(ValueError,"contagem"):
            mobile_sync.exchange(self.mirror,dict(format="aurion-memory-v4",profile="anark",
                                                   recordCount=900,records=[self.row(1)]))
        self.assertFalse(mobile_sync.post_size_ok(None))
        self.assertFalse(mobile_sync.post_size_ok(3_000_001))
        self.assertTrue(mobile_sync.post_size_ok(123))

    def test_cross_device_record_set_sha256_and_readback(self):
        import hashlib
        rows=[self.row(i) for i in (12,3,42,42)]
        request=mobile_sync.exchange(self.mirror,self.payload(rows))
        self.assertEqual(request["recordCount"],3)
        expected=hashlib.sha256("\n".join(sorted(
            mobile_sync._fingerprint(r) for r in request["records"]
        )).encode("utf-8")).hexdigest()
        self.assertEqual(request["recordsFingerprintSha256"],expected)
        self.assertEqual(mobile_sync.state(self.mirror)["recordsFingerprintSha256"],expected)
        again=mobile_sync.exchange(self.mirror,self.payload(rows))
        self.assertEqual(again["pcNew"],0)
        self.assertEqual(again["recordsFingerprintSha256"],expected)

    def test_sha_content_correct(self):
        rows=[self.row(77)]
        result=mobile_sync.exchange(self.mirror,self.payload(rows))
        import hashlib
        expected=hashlib.sha256(json.dumps(result["records"],ensure_ascii=False,separators=(",",":")).encode()).hexdigest()
        self.assertEqual(result["responseSha256"],expected)


if __name__=="__main__":
    unittest.main()
