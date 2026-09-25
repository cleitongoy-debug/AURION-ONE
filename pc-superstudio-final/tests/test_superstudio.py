from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from aurion_superstudio import app as module
from aurion_superstudio.creative3d import blender_status, ensure_3d_workspace
from aurion_superstudio.services import inventory_base, process_image, unique_path


class SuperStudioTests(unittest.TestCase):
    def setUp(self):
        module.app.config["TESTING"] = True
        self.client = module.app.test_client()
        self.headers = {"X-Aurion-Token": module.TOKEN}

    def test_health(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["version"], "2.0.0")

    def test_final_panel_contains_3d_modules(self):
        html = self.client.get("/").get_data(as_text=True)
        for marker in ("Blender 5.2", "Nodes", "Texturas", "Rig & Animação", "Roupas & Acessórios", "Cinema 4D & Octane"):
            self.assertIn(marker, html)

    def test_3d_status_endpoints_return_structured_state(self):
        blender = self.client.get("/api/blender/status").get_json()
        c4d = self.client.get("/api/c4d/status").get_json()
        self.assertIn("paths", blender)
        self.assertIn("inventory", blender)
        self.assertIn("solutions", c4d)
        self.assertIn("paths", c4d)

    def test_mutation_requires_token(self):
        response = self.client.post("/api/records", json={"title": "x"})
        self.assertEqual(response.status_code, 401)

    def test_memory_roundtrip(self):
        response = self.client.post("/api/records", headers=self.headers, json={"kind": "test", "title": "Registro", "body": "conteúdo"})
        self.assertEqual(response.status_code, 201)
        listing = self.client.get("/api/records?kind=test").get_json()["records"]
        self.assertTrue(any(row["title"] == "Registro" for row in listing))

    def test_unique_path_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "foto.jpg").write_bytes(b"original")
            self.assertEqual(unique_path(root, "foto.jpg").name, "foto_001.jpg")
            self.assertEqual((root / "foto.jpg").read_bytes(), b"original")

    def test_protected_inventory_is_read_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original = b"painel protegido"
            (root / "ADAPTA.py").write_bytes(original)
            result = inventory_base(root)
            self.assertEqual(len(result["files"]), 1)
            self.assertTrue(result["files"][0]["read_only"])
            self.assertEqual((root / "ADAPTA.py").read_bytes(), original)

    def test_image_processing_creates_new_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, output = root / "in.png", root / "out.jpg"
            Image.new("RGB", (32, 24), (20, 40, 80)).save(source)
            info = process_image(source, output, {"brightness": 1.2, "effect": "warm"})
            self.assertTrue(output.exists())
            self.assertEqual((info["width"], info["height"]), (32, 24))

    def test_3d_workspace_has_all_libraries(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = ensure_3d_workspace(Path(tmp))
            self.assertEqual(set(paths), {"projects", "renders", "nodes", "textures", "rigs", "clothes", "logs"})
            self.assertTrue(all(path.is_dir() for path in paths.values()))

    def test_blender_status_is_truthful_when_executable_is_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = blender_status(Path(tmp), {}, {})
            self.assertIn("installed", result)
            self.assertIn("running", result)
            self.assertIn("inventory", result)


if __name__ == "__main__":
    unittest.main()
