"""Flask route checks in CI sandbox; no PC program, ADB or API is started."""
import os
import tempfile
import unittest
from pathlib import Path

ROOT=tempfile.TemporaryDirectory(prefix="aurion_pc_sync_ci_")
os.environ["AURION_PANEL_ROOT"]=ROOT.name
from aurion_superstudio.app import app,TOKEN,SYNC_DB

class MobileSyncEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client=app.test_client()
        self.headers={"X-Aurion-Token":TOKEN}

    def payload(self):
        return dict(format="aurion-memory-v4", profile="anark", recordCount=1,
                    records=[dict(type="memory",title="Teste do cabo",body="memoria local de regressao",
                        meta="{}",createdAt=1780000000000,updatedAt=1780000000000)])

    def test_auth_and_usb_only(self):
        self.assertEqual(self.client.get("/api/mobile/memory-sync").status_code,401)
        denied=self.client.get("/api/mobile/memory-sync",headers=self.headers,
            environ_base={"REMOTE_ADDR":"192.168.1.25"})
        self.assertEqual(denied.status_code,403)
        allowed=self.client.get("/api/mobile/memory-sync",headers=self.headers)
        self.assertEqual(allowed.status_code,200)
        self.assertTrue(allowed.json["ok"])

    def test_request_two_way_receipt(self):
        a=self.client.post("/api/mobile/memory-sync/request",headers=self.headers,json={})
        self.assertEqual(a.status_code,200)
        self.assertTrue(self.client.get("/api/mobile/memory-sync",headers=self.headers).json["syncRequested"])
        first=self.client.post("/api/mobile/memory-sync",headers=self.headers,json=self.payload())
        self.assertEqual(first.status_code,200)
        self.assertEqual(first.json["received"],1)
        self.assertEqual(first.json["recordCount"],1)
        again=self.client.post("/api/mobile/memory-sync",headers=self.headers,json=self.payload())
        self.assertEqual(again.status_code,200)
        self.assertEqual(again.json["pcNew"],0)
        current=self.client.get("/api/mobile/memory-sync",headers=self.headers).json
        self.assertFalse(current["syncRequested"])
        self.assertEqual(current["phoneMirroredRecords"],1)

    def test_bad_profile_no_write(self):
        invalid=self.payload();invalid["profile"]="outro"
        a=self.client.post("/api/mobile/memory-sync",headers=self.headers,json=invalid)
        self.assertEqual(a.status_code,400)
        self.assertEqual(self.client.get("/api/mobile/memory-sync",headers=self.headers).json["phoneMirroredRecords"],1)

if __name__=="__main__":unittest.main()
