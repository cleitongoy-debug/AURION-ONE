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

    def test_external_origin_never_receives_token_cors_access(self):
        malicious={"Origin":"https://outside.example"}
        home=self.client.get("/",headers=malicious)
        self.assertEqual(home.status_code,403)
        self.assertNotIn("Access-Control-Allow-Origin",home.headers)
        probe=self.client.options("/api/mobile/memory-sync",headers={
            **malicious,"Access-Control-Request-Method":"POST",
            "Access-Control-Request-Headers":"X-Aurion-Token"})
        self.assertEqual(probe.status_code,403)
        self.assertNotIn("Access-Control-Allow-Origin",probe.headers)

    def test_dns_rebinding_is_denied_even_from_loopback(self):
        # Rebinding still arrives from 127.0.0.1, but Host stays attacker-controlled.
        bad_host={"Host":"outside.example:5060"}
        home=self.client.get("/",headers=bad_host)
        self.assertEqual(home.status_code,403)
        self.assertNotIn(TOKEN,home.get_data(as_text=True))
        sync=self.client.get("/api/mobile/memory-sync",
                             headers={**bad_host,**self.headers})
        self.assertEqual(sync.status_code,403)
        good=self.client.get("/",headers={"Host":"127.0.0.1:5060"})
        self.assertEqual(good.status_code,200)
        alternate=self.client.get("/api/mobile/memory-sync",
            headers={**self.headers,"Host":"localhost:5069"})
        self.assertEqual(alternate.status_code,200)

    def test_reject_site_origin_despite_valid_host_and_token(self):
        headers={**self.headers,"Host":"localhost:5060",
                 "Origin":"https://outside.example"}
        self.assertEqual(self.client.post("/api/mobile/memory-sync/request",
                                          headers=headers,json={}).status_code,403)
        headers["Origin"]="http://localhost:5060"
        self.assertEqual(self.client.post("/api/mobile/memory-sync/request",
                                          headers=headers,json={}).status_code,200)

    def test_bad_profile_no_write(self):
        before=self.client.get("/api/mobile/memory-sync",headers=self.headers).json["phoneMirroredRecords"]
        invalid=self.payload();invalid["profile"]="outro"
        a=self.client.post("/api/mobile/memory-sync",headers=self.headers,json=invalid)
        self.assertEqual(a.status_code,400)
        self.assertEqual(self.client.get("/api/mobile/memory-sync",headers=self.headers).json["phoneMirroredRecords"],before)

if __name__=="__main__":unittest.main()
