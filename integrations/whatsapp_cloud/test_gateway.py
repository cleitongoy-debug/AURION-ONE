"""Offline, loopback-only regression tests. No WhatsApp or device credentials."""
import hashlib
import hmac
import http.client
import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlencode

from gateway import Ledger, Settings, make_handler, signature_valid


class GatewayTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.conf = Settings({"AURION_WA_VERIFY_TOKEN": "testverify", "AURION_WA_APP_SECRET": "fake-app-secret",
                              "AURION_WA_ALLOWED_CONTACTS": "5511999999999", "AURION_WA_ENABLE_REPLIES": "false",
                              "AURION_WA_DB": str(Path(self.tmp.name)/"events.sqlite")})
        self.ledger = Ledger(self.conf.db_path)
        self.sent = []
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(self.conf, self.ledger,
                            sender=lambda settings, number, body: self.sent.append((number, body))))
        self.worker = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.worker.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.worker.join(timeout=2)
        self.ledger.close()
        self.tmp.cleanup()

    def req(self, method, target, body=b"", headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=2)
        conn.request(method, target, body=body, headers=headers or {})
        result = conn.getresponse()
        status, data = result.status, result.read()
        conn.close()
        return status, data

    def payload(self, msg_id="wamid.001", command="status"):
        return {"object":"whatsapp_business_account", "entry":[{"changes":[{"field":"messages", "value":{
              "messages":[{"id":msg_id, "from":"5511999999999", "type":"text", "text":{"body":command}}]}}]}]}

    def signed_post(self, payload):
        data=json.dumps(payload).encode()
        sig=hmac.new(b"fake-app-secret", data, hashlib.sha256).hexdigest()
        return self.req("POST", "/webhook", data, {"Content-Length":str(len(data)), "X-Hub-Signature-256":"sha256="+sig})

    def test_get_challenge(self):
        q=urlencode({"hub.mode":"subscribe", "hub.verify_token":"testverify", "hub.challenge":"12345"})
        self.assertEqual(self.req("GET", "/webhook?"+q), (200,b"12345"))
        self.assertEqual(self.req("GET", "/webhook?hub.mode=subscribe&hub.verify_token=wrong&hub.challenge=12345")[0],403)

    def test_post_signature_required(self):
        data=json.dumps(self.payload()).encode()
        self.assertEqual(self.req("POST", "/webhook", data, {"Content-Length":str(len(data))})[0],403)
        self.assertFalse(signature_valid(data,"sha256="+"0"*64,"fake-app-secret"))

    def test_no_replies_default(self):
        self.assertEqual(self.signed_post(self.payload()), (200,b"ok"))
        self.assertEqual(self.sent, [])
        self.assertEqual(self.signed_post(self.payload()), (200,b"ok"))
        self.assertEqual(self.sent, [])

    def test_opt_in_allowlist_command(self):
        self.conf.reply_enabled=True
        status,_=self.signed_post(self.payload())
        self.assertEqual(status,200)
        self.assertEqual(len(self.sent),1)
        self.assertIn("Estado dos dispositivos",self.sent[0][1])
        self.assertEqual(self.signed_post(self.payload())[0],200)
        self.assertEqual(len(self.sent),1)
        self.assertEqual(self.signed_post(self.payload("wamid.002", "sudo apaga tudo"))[0],200)
        self.assertEqual(len(self.sent),1)

    def test_invalid_post_json(self):
        body=b"notjson"
        sig=hmac.new(b"fake-app-secret",body,hashlib.sha256).hexdigest()
        self.assertEqual(self.req("POST", "/webhook", body, {"Content-Length":str(len(body)), "X-Hub-Signature-256":"sha256="+sig})[0],400)

    def test_oversized_body(self):
        self.assertEqual(self.req("POST", "/webhook", b"", {"Content-Length":str(200000)})[0],413)

    def test_ledger_persists_across_reopen(self):
        self.assertTrue(self.ledger.mark_once("durable-wamid"))
        self.ledger.close()
        self.ledger=Ledger(self.conf.db_path)
        self.assertFalse(self.ledger.mark_once("durable-wamid"))


if __name__ == "__main__":
    unittest.main()
