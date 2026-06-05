"""
Tests d'intégration pour les routes FastAPI.
"""
import os
import httpx
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

os.environ["API_KEY"] = "test-secret-key"

from api.main import app, servers  # noqa: E402

TEST_API_KEY = "test-secret-key"
HEADERS = {"X-API-Key": TEST_API_KEY}
SERVER_PAYLOAD = {"name": "prod-api", "host": "192.168.1.1", "port": 8000}


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def clear_servers():
    """Vide le dictionnaire des serveurs avant/après chaque test."""
    servers.clear()
    yield
    servers.clear()


@pytest.fixture
def created_server(client):
    """Crée un serveur et retourne la réponse JSON."""
    response = client.post("/servers", json=SERVER_PAYLOAD, headers=HEADERS)
    assert response.status_code == 201
    return response.json()


# ── /health ──────────────────────────────────────────────────────────────

def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ── /metrics ─────────────────────────────────────────────────────────────

def test_metrics_status_code(client):
    assert client.get("/metrics").status_code == 200


def test_metrics_required_fields(client):
    data = client.get("/metrics").json()
    for field in ["cpu_percent", "memory_percent", "disk_percent",
                  "memory_total_gb", "memory_used_gb",
                  "disk_total_gb", "disk_used_gb"]:
        assert field in data


def test_metrics_values_in_range(client):
    data = client.get("/metrics").json()
    assert 0 <= data["cpu_percent"] <= 100
    assert 0 <= data["memory_percent"] <= 100
    assert 0 <= data["disk_percent"] <= 100


# ── Auth ─────────────────────────────────────────────────────────────────

def test_post_server_without_api_key_returns_403(client):
    assert client.post("/servers", json=SERVER_PAYLOAD).status_code == 403


def test_post_server_with_wrong_api_key_returns_403(client):
    r = client.post("/servers", json=SERVER_PAYLOAD,
                    headers={"X-API-Key": "wrong-key"})
    assert r.status_code == 403


def test_delete_server_without_api_key_returns_403(client):
    assert client.delete("/servers/some-id").status_code == 403


def test_manual_check_without_api_key_returns_403(client):
    assert client.post("/servers/some-id/check").status_code == 403


# ── POST /servers ─────────────────────────────────────────────────────────

def test_create_server_returns_201(client):
    r = client.post("/servers", json=SERVER_PAYLOAD, headers=HEADERS)
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "prod-api"
    assert data["status"] == "UNKNOWN"
    assert "id" in data
    assert data["base_url"] == "http://192.168.1.1:8000"


def test_create_server_invalid_port(client):
    r = client.post("/servers",
                    json={"name": "test", "host": "localhost", "port": 99999},
                    headers=HEADERS)
    assert r.status_code == 422


def test_create_server_port_zero(client):
    r = client.post("/servers",
                    json={"name": "test", "host": "localhost", "port": 0},
                    headers=HEADERS)
    assert r.status_code == 422


def test_create_multiple_servers_have_unique_ids(client):
    ids = []
    for i in range(3):
        r = client.post("/servers",
                        json={"name": f"srv-{i}", "host": "localhost",
                              "port": 8000 + i},
                        headers=HEADERS)
        assert r.status_code == 201
        ids.append(r.json()["id"])
    assert len(set(ids)) == 3


# ── GET /servers ──────────────────────────────────────────────────────────

def test_list_servers_empty(client):
    r = client.get("/servers")
    assert r.status_code == 200
    assert r.json() == []


def test_list_servers_after_creation(client):
    for i in range(2):
        client.post("/servers",
                    json={"name": f"s{i}", "host": "10.0.0.1", "port": 80 + i},
                    headers=HEADERS)
    assert len(client.get("/servers").json()) == 2


def test_list_servers_contains_base_url(client, created_server):
    data = client.get("/servers").json()
    assert data[0]["base_url"] == "http://192.168.1.1:8000"


# ── DELETE /servers/{id} ──────────────────────────────────────────────────

def test_delete_server_success(client, created_server):
    sid = created_server["id"]
    assert client.delete(f"/servers/{sid}", headers=HEADERS).status_code == 204
    assert client.get("/servers").json() == []


def test_delete_server_not_found(client):
    assert client.delete("/servers/nonexistent-id",
                         headers=HEADERS).status_code == 404


def test_delete_server_twice(client, created_server):
    sid = created_server["id"]
    client.delete(f"/servers/{sid}", headers=HEADERS)
    assert client.delete(f"/servers/{sid}",
                         headers=HEADERS).status_code == 404


# ── POST /servers/{id}/check ─────────────────────────────────────────────

def test_manual_check_not_found(client):
    r = client.post("/servers/nonexistent-id/check", headers=HEADERS)
    assert r.status_code == 404


def test_manual_check_server_up(client, created_server):
    sid = created_server["id"]
    mock_response = AsyncMock()
    mock_response.status_code = 200

    with patch("api.poller.httpx.AsyncClient") as mock_class:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_class.return_value = mock_client
        r = client.post(f"/servers/{sid}/check", headers=HEADERS)

    assert r.status_code == 200
    assert r.json()["status"] == "UP"


def test_manual_check_server_down(client, created_server):
    sid = created_server["id"]

    with patch("api.poller.httpx.AsyncClient") as mock_class:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=httpx.RequestError("Connection refused"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_class.return_value = mock_client
        r = client.post(f"/servers/{sid}/check", headers=HEADERS)

    assert r.status_code == 200
    assert r.json()["status"] == "DOWN"


# ── WebSocket ─────────────────────────────────────────────────────────────

def test_websocket_metrics(client):
    import json
    with client.websocket_connect("/ws/metrics") as ws:
        data = json.loads(ws.receive_text())
        assert "cpu_percent" in data
