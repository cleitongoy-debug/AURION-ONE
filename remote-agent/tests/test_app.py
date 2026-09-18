from fastapi.testclient import TestClient

from aurion_remote.app import app
from aurion_remote.config import Settings, get_settings


def override_settings() -> Settings:
    return Settings(api_token="test-token", allow_remote_prompts=False)


app.dependency_overrides[get_settings] = override_settings
client = TestClient(app)


def test_health_is_public() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "online"


def test_private_status_requires_token() -> None:
    assert client.get("/api/status").status_code == 401


def test_motion_lock_blocks_prompt() -> None:
    response = client.post(
        "/api/prompt",
        headers={"Authorization": "Bearer test-token"},
        json={"text": "status", "device_id": "poco-x7", "moving": True},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "blocked"
