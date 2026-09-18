"""Regression tests for the opt-in authenticated inventory scan.

These tests never scan or modify the operator's real PC.
"""
import json
from pathlib import Path

from fastapi.testclient import TestClient

import aurion_remote.app as module
from aurion_remote.app import app, scan_lock
from aurion_remote.config import Settings, get_settings


def settings_for_scan() -> Settings:
    return Settings(api_token="scan-test-token")


def restore_settings(previous):
    if previous is None:
        app.dependency_overrides.pop(get_settings, None)
    else:
        app.dependency_overrides[get_settings] = previous


def test_scan_requires_authentication():
    previous = app.dependency_overrides.get(get_settings)
    app.dependency_overrides[get_settings] = settings_for_scan
    try:
        with TestClient(app) as client:
            assert client.post("/api/scan").status_code == 401
            assert client.post("/api/scan", headers={"Authorization": "Bearer incorrect"}).status_code == 401
    finally:
        restore_settings(previous)


def test_scan_returns_new_inventory(monkeypatch):
    previous = app.dependency_overrides.get(get_settings)
    app.dependency_overrides[get_settings] = settings_for_scan
    path = Path(module.__file__).resolve().parents[1] / "data" / "inventory.json"
    path.parent.mkdir(exist_ok=True)
    original = path.read_bytes() if path.exists() else None

    class FakeProcess:
        returncode = 0

        async def wait(self):
            path.write_text(json.dumps({"scanned_at": "mocked-scan", "services": {}}), encoding="utf-8")

    async def fake_spawn(*args, **kwargs):
        assert kwargs["stdout"] == module.asyncio.subprocess.DEVNULL
        assert kwargs["stderr"] == module.asyncio.subprocess.DEVNULL
        return FakeProcess()

    monkeypatch.setattr(module.asyncio, "create_subprocess_exec", fake_spawn)
    try:
        with TestClient(app) as client:
            response = client.post("/api/scan", headers={"Authorization": "Bearer scan-test-token"})
            assert response.status_code == 200, response.text
            assert response.json()["scanned_at"] == "mocked-scan"
            assert "Iniciar scan do PC" in client.get("/").text
    finally:
        if original is None:
            path.unlink(missing_ok=True)
        else:
            path.write_bytes(original)
        restore_settings(previous)


def test_scan_rejects_concurrent_run():
    import asyncio

    async def check():
        async with scan_lock:
            try:
                await module.run_inventory_scan()
            except module.HTTPException as exc:
                assert exc.status_code == 409
            else:
                raise AssertionError("Scan should reject a concurrent request")

    asyncio.run(check())
