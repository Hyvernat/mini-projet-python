import pytest
from fastapi.testclient import TestClient
from api.main import app, _store

client = TestClient(app)
VALID_KEY = "dev-secret-key"


def setup_function():
    _store.clear()


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


def test_get_server_by_id():
    r = client.post(
        "/servers",
        json={"name": "get-test", "host": "localhost", "port": 8080},
        headers={"X-API-Key": VALID_KEY},
    )
    server_id = r.json()["id"]
    r2 = client.get(f"/servers/{server_id}")
    assert r2.status_code == 200
    assert r2.json()["name"] == "get-test"


def test_delete_server():
    r = client.post(
        "/servers",
        json={"name": "to-delete", "host": "localhost", "port": 8080},
        headers={"X-API-Key": VALID_KEY},
    )
    server_id = r.json()["id"]
    r2 = client.delete(f"/servers/{server_id}", headers={"X-API-Key": VALID_KEY})
    assert r2.status_code == 204
    r3 = client.get(f"/servers/{server_id}")
    assert r3.status_code == 404


def test_delete_server_without_key_returns_403():
    r = client.post(
        "/servers",
        json={"name": "protected", "host": "localhost", "port": 8080},
        headers={"X-API-Key": VALID_KEY},
    )
    server_id = r.json()["id"]
    r2 = client.delete(f"/servers/{server_id}")
    assert r2.status_code == 403


def test_delete_nonexistent_server_returns_404():
    r = client.delete("/servers/99999", headers={"X-API-Key": VALID_KEY})
    assert r.status_code == 404


def test_list_servers_filter_by_status():
    client.post(
        "/servers",
        json={"name": "filter-test", "host": "localhost", "port": 8080},
        headers={"X-API-Key": VALID_KEY},
    )
    r = client.get("/servers?status=UP")
    assert r.status_code == 200
    assert all(s["status"] == "UP" for s in r.json())


def test_trigger_check_nonexistent_returns_404():
    r = client.post("/servers/99999/check")
    assert r.status_code == 404


def test_websocket_metrics():
    with client.websocket_connect("/ws/metrics") as ws:
        import json
        data = json.loads(ws.receive_text())
        assert "cpu_percent" in data
