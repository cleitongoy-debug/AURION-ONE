"""Regression checks for the existing POCO-to-PC contract.

Run from remote-agent with: python -m pytest tests/test_mobile_contract_regression.py -q
These checks never contact Ollama, ComfyUI, a phone or a public network.
"""

from fastapi.testclient import TestClient

from aurion_remote.app import app
from aurion_remote.config import Settings, get_settings


def _settings():
    return Settings(
        api_token="test-only-not-a-real-secret",
        ollama_model="",
        allow_remote_prompts=False,
    )


def test_mobile_contract_and_bearer():
    app.dependency_overrides[get_settings] = _settings
    try:
        with TestClient(app) as client:
            assert client.get("/health").status_code == 200
            payload = {"text": "teste", "device_id": "poco-mobile", "moving": False}
            assert client.post("/api/prompt", json=payload).status_code == 401
            assert client.post("/api/prompt", json=payload, headers={"Authorization": "Bearer wrong"}).status_code == 401
            headers = {"Authorization": "Bearer test-only-not-a-real-secret"}
            assert client.post("/api/prompt", json={"device_id": "poco-mobile", "moving": False}, headers=headers).status_code == 422
            response = client.post("/api/prompt", json=payload, headers=headers)
            assert response.status_code == 200
            assert response.json()["status"] == "disabled"  # no model configured; never fake an inference
            assert client.get("/api/inventory").status_code == 401
            assert client.get("/api/inventory", headers=headers).status_code == 200
    finally:
        app.dependency_overrides.clear()
