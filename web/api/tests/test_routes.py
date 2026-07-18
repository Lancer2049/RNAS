"""Route-level auth + validation tests — sync TestClient for reliability."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

_proj = Path(__file__).parent.parent.parent
if str(_proj) not in sys.path:
    sys.path.insert(0, str(_proj))

from main import app


@pytest.fixture
def client():
    from api.auth import create_access_token
    token = create_access_token("test_admin", "admin")
    c = TestClient(app)
    c.headers["Authorization"] = f"Bearer {token}"
    return c


@pytest.fixture
def anon():
    return TestClient(app)


class TestAuth:
    def test_health_no_auth(self, anon):
        resp = anon.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_status_rejects_no_auth(self, anon):
        resp = anon.get("/api/v1/status")
        assert resp.status_code == 401

    def test_status_accepts_valid_token(self, client):
        resp = client.get("/api/v1/status")
        assert resp.status_code in (200, 500)

    def test_invalid_token_rejected(self, anon):
        resp = anon.get("/api/v1/status", headers={"Authorization": "Bearer bad.token"})
        assert resp.status_code == 401


class TestValidators:
    def test_rejects_flag_injection(self):
        from api.validators import validate_ip_or_hostname
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            validate_ip_or_hostname("-c evil.com")
        assert exc.value.status_code == 400

    def test_accepts_valid_ip(self):
        from api.validators import validate_ip_or_hostname
        assert validate_ip_or_hostname("127.0.0.1") == "127.0.0.1"

    def test_accepts_valid_hostname(self):
        from api.validators import validate_ip_or_hostname
        assert validate_ip_or_hostname("google.com") == "google.com"
