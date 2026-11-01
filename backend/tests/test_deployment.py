"""Public-hosting regressions: embed policy and clean upload contents."""

import importlib.util
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, settings
from app.main import app
from app.llm.client import model


def test_spaces_embed_policy(monkeypatch):
    monkeypatch.setattr(settings, "frame_ancestors", "https://huggingface.co")
    with TestClient(app) as client:
        response = client.get("/api/health")
    policy = response.headers["content-security-policy"]
    assert "frame-ancestors https://huggingface.co;" in policy
    assert "connect-src 'self'" in policy


def test_readiness_requires_successful_inference(monkeypatch):
    async def installed():
        return True

    monkeypatch.setattr(model, "available", installed)
    monkeypatch.setattr(model, "inference_ready", False)
    client = TestClient(app)
    assert client.get("/api/ready").status_code == 503
    monkeypatch.setattr(model, "inference_ready", True)
    assert client.get("/api/ready").status_code == 200


@pytest.mark.parametrize("value", ["*", "https://*.example.com", "http://example.com", "https://example.com;script-src *", "https://example.com\r\nx-test: injected"])
def test_reject_unsafe_frame_policy(value):
    with pytest.raises(ValueError, match="FRAME_ANCESTORS"):
        Settings(frame_ancestors=value)


def test_upload_package_removes_stale_files_and_excludes_secrets(tmp_path):
    script = Path(__file__).resolve().parents[2] / "scripts/prepare_space.py"
    spec = importlib.util.spec_from_file_location("prepare_space", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for directory in ["backend", "frontend", "samples", "deploy/huggingface"]:
        (tmp_path / directory).mkdir(parents=True, exist_ok=True)
    for name in ["Dockerfile", "README.md"]:
        (tmp_path / "deploy/huggingface" / name).write_text(name)
    (tmp_path / ".dockerignore").write_text(".env\n")
    prompt = tmp_path / "backend/example-hi.json"
    prompt.write_text("current prompt")
    (tmp_path / "backend/.env").write_text("SECRET=private")
    output = module.prepare(tmp_path)
    (output / "backend/stale.py").write_text("old code")
    prompt.write_text("updated prompt")
    module.prepare(tmp_path)
    assert (output / "backend/example-hi.json").read_text() == "updated prompt"
    assert not (output / "backend/stale.py").exists()
    assert not (output / "backend/.env").exists()
