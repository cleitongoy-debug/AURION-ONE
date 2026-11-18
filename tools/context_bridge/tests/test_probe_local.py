"""Synthetic tests for private, read-only presence probe. No network needed."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

FILE = Path(__file__).resolve().parents[1] / "probe_local.py"
SPEC = importlib.util.spec_from_file_location("aurion_probe_local", FILE)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class PresenceTests(unittest.TestCase):
    def test_tailnet_summarizes_no_secret_peer_fields(self):
        snapshot = {
            "BackendState": "Running",
            "Self": {"Online": True, "DNSName": "private.example",
                     "TailscaleIPs": ["100.9.8.7"]},
            "Peer": {
                "key-a": {"Online": True, "HostName": "private-PC",
                          "TailscaleIPs": ["100.1.2.3"]},
                "key-b": {"Online": False, "HostName": "another-person"},
            },
        }
        result = module.parse_tailnet_status(json.dumps(snapshot))
        self.assertEqual(result["peers_listed"], 2)
        self.assertEqual(result["peers_online_reported"], 1)
        self.assertTrue(result["self_online"])
        self.assertNotIn("100.1.2.3", json.dumps(result))
        self.assertNotIn("private-PC", json.dumps(result))
        self.assertNotIn("private.example", json.dumps(result))

    def test_missing_tailscale_client_is_not_online(self):
        with patch.object(module.shutil, "which", return_value=None):
            r = module.probe_tailscale()
        self.assertEqual(r["status"], "CLIENT_NOT_FOUND")

    def test_no_live_device_ack_is_inferred(self):
        with patch.object(module, "probe_tailscale", return_value={"status": "CLI_REPLIED"}):
            with patch.object(module, "probe_service", return_value="HTTP_200"):
                r = module.generate_report()
        self.assertEqual(r["services"]["aurion_portal"], "HTTP_200")
        self.assertEqual(r["other_devices"]["poco"], "NO_DEVICE_ACK_TESTED")
        self.assertEqual(r["other_devices"]["notify_band"], "NO_DEVICE_ACK_TESTED")
        self.assertFalse(r["delivered_to_drive"])
        self.assertFalse(r["delivered_to_github"])

    def test_local_atomic_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "status" / "presence.json"
            module.write_private_json(dest, {"event_id": "test", "status": "NOT_SENT"})
            self.assertTrue(dest.exists())
            self.assertEqual(json.loads(dest.read_text())["status"], "NOT_SENT")

    def test_service_failure_is_not_online(self):
        with patch.object(module, "urlopen", side_effect=OSError("connection refused")):
            self.assertEqual(module.probe_service("http://127.0.0.1:8765/health"),
                             "UNREACHABLE")


if __name__ == "__main__":
    unittest.main()
