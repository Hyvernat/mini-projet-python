import pytest
from fastapi.testclient import TestClient
from api.main import app, _store, _counter

client = TestClient(app)
VALID_KEY = "dev-secret-key"


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_metrics_returns_cpu():
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "cpu_percent" in r.json()


def test_post_server_without_key_returns_403():
    r = client.post("/servers", json={"name": "test", "host": "localhost", "port": 8080})
    assert r.status_code == 403


def test_post_server_with_key_returns_201():
    r = client.post(
        "/servers",
        json={"name": "test-server", "host": "localhost", "port": 9090},
        headers={"X-API-Key": VALID_KEY},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "test-server"
    assert data["status"] == "unknown"


def test_server_appears_in_list():
    client.post(
        "/servers",
        json={"name": "list-test", "host": "10.0.0.1", "port": 8080},
        headers={"X-API-Key": VALID_KEY},
    )
    r = client.get("/servers")
    assert r.status_code == 200
    names = [s["name"] for s in r.json()]
    assert "list-test" in names


def test_get_nonexistent_server_returns_404():
    r = client.get("/servers/99999")
    assert r.status_code == 404
