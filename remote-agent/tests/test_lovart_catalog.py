import json
from pathlib import Path

from fastapi.testclient import TestClient
from aurion_remote.app import app
from aurion_remote.config import Settings, get_settings
from aurion_remote.lovart_catalog import load_catalog, safe_link


def test_missing_manifest_is_not_online(tmp_path: Path):
    report = load_catalog(tmp_path / "none.json")
    assert report["status"] == "manifest_missing"
    assert report["lovart_api_connected"] is False
    assert report["instagram_api_connected"] is False
    assert report["credits_remaining"] is None


def test_catalog_strips_secrets_and_unsafe_links(tmp_path: Path):
    target = tmp_path / "catalog.json"
    target.write_text(json.dumps({
        "instagram_profile": "https://www.instagram.com/studio.digitalpen/?igsh=tracking",
        "api_key": "DO_NOT_EXPOSE",
        "assets": [
            {"title": "Projeto", "url": "https://example.com/art.png?token=DO_NOT_EXPOSE", "kind": "visual", "secret": "DO_NOT_EXPOSE"},
            {"title": "Local", "url": "http://127.0.0.1/admin"},
            {"title": "Bad", "url": "https://user:password@example.com/private"}
        ]
    }), encoding="utf-8")
    report = load_catalog(target)
    assert report["status"] == "catalog_loaded"
    assert report["asset_count"] == 1
    assert report["assets"][0]["url"] == "https://example.com/art.png"
    assert report["instagram_profile"] == "https://www.instagram.com/studio.digitalpen/"
    assert "DO_NOT_EXPOSE" not in json.dumps(report)


def test_invalid_manifest_never_crashes(tmp_path: Path):
    target = tmp_path / "catalog.json"
    target.write_text("{broken", encoding="utf-8")
    assert load_catalog(target)["status"] == "manifest_invalid"
    assert safe_link("javascript:alert(1)") is None


def test_lovart_endpoint_requires_token():
    app.dependency_overrides[get_settings] = lambda: Settings(api_token="lovart-test-token")
    try:
        client = TestClient(app)
        assert client.get("/api/lovart").status_code == 401
        res = client.get("/api/lovart", headers={"Authorization": "Bearer lovart-test-token"})
        assert res.status_code == 200
        assert res.json()["lovart_api_connected"] is False
    finally:
        app.dependency_overrides.pop(get_settings, None)
