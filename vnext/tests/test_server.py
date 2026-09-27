import json
import sys
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server


class LocalPanelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.http = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.url = "http://127.0.0.1:" + str(cls.http.server_port)
        cls.thread = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()

    def request(self, path, method="GET", payload=None, authorized=True):
        headers = {"Authorization": "Bearer " + server.TOKEN} if authorized else {}
        data = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(self.url + path, method=method, headers=headers, data=data)
        return urllib.request.urlopen(req, timeout=5)

    def test_auth_blocks_data(self):
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.request("/api/history", authorized=False)
        self.assertEqual(error.exception.code, 401)

    def test_chat_rejects_unlisted_model(self):
        with patch.object(server, "models", return_value=["local:one"]):
            with self.assertRaises(urllib.error.HTTPError) as error:
                self.request("/api/chat", "POST", {"message": "oi", "model": "inventado"})
            self.assertEqual(error.exception.code, 400)

    def test_render_rejects_path_traversal(self):
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.request("/api/render", "POST", {"scene": "../../Windows/test.c4d"})
        self.assertEqual(error.exception.code, 400)

    def test_health_is_evidence_based(self):
        with patch.object(server, "get_json", side_effect=OSError), patch.object(server, "probe", side_effect=OSError):
            result = json.load(self.request("/api/status"))
        self.assertEqual(result["services"]["ollama"]["state"], "offline")
        self.assertEqual(result["services"]["comfyui"]["state"], "offline")

    def test_memory_persists(self):
        self.assertTrue(json.load(self.request("/api/notes", "POST", {"text": "teste local"}))["saved"])
        self.assertTrue(any(row["text"] == "teste local" for row in json.load(self.request("/api/notes"))["notes"]))


if __name__ == "__main__":
    unittest.main()
