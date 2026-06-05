"""
Tests unitaires pour le module de polling asynchrone.
"""
import asyncio
import pytest
import httpx
from unittest.mock import AsyncMock, patch

from api.models import Server
from api.poller import poll_server, run_poll_loop


@pytest.fixture
def server():
    """Retourne un serveur de test standard."""
    return Server(id="test-id-123", name="test-server",
                  host="localhost", port=8080)


def make_server(host="localhost", port=8080, name="srv", sid="abc"):
    return Server(id=sid, name=name, host=host, port=port)


@pytest.mark.asyncio
async def test_poll_server_status_up(server):
    mock_response = AsyncMock()
    mock_response.status_code = 200

    with patch("api.poller.httpx.AsyncClient") as mock_class:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_class.return_value = mock_client
        await poll_server(server)

    assert server.status == "UP"


@pytest.mark.asyncio
async def test_poll_server_status_degraded_on_500(server):
    mock_response = AsyncMock()
    mock_response.status_code = 500

    with patch("api.poller.httpx.AsyncClient") as mock_class:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_class.return_value = mock_client
        await poll_server(server)

    assert server.status == "DEGRADED"


@pytest.mark.asyncio
async def test_poll_server_status_degraded_on_503(server):
    mock_response = AsyncMock()
    mock_response.status_code = 503

    with patch("api.poller.httpx.AsyncClient") as mock_class:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_class.return_value = mock_client
        await poll_server(server)

    assert server.status == "DEGRADED"


@pytest.mark.asyncio
async def test_poll_server_down_on_connect_error(server):
    with patch("api.poller.httpx.AsyncClient") as mock_class:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=httpx.ConnectError("Connection refused"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_class.return_value = mock_client
        await poll_server(server)

    assert server.status == "DOWN"


@pytest.mark.asyncio
async def test_poll_server_down_on_timeout(server):
    with patch("api.poller.httpx.AsyncClient") as mock_class:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=httpx.TimeoutException("Timeout"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_class.return_value = mock_client
        await poll_server(server)

    assert server.status == "DOWN"


@pytest.mark.asyncio
async def test_poll_server_calls_correct_url(server):
    mock_response = AsyncMock()
    mock_response.status_code = 200

    with patch("api.poller.httpx.AsyncClient") as mock_class:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_class.return_value = mock_client
        await poll_server(server)
        mock_client.get.assert_called_once_with("http://localhost:8080/health")


@pytest.mark.asyncio
async def test_run_poll_loop_calls_poll_server():
    servers = {
        "id1": make_server(sid="id1", name="s1"),
        "id2": make_server(sid="id2", name="s2", port=9000),
    }
    call_count = 0

    async def mock_poll(server):
        nonlocal call_count
        call_count += 1

    with patch("api.poller.poll_server", side_effect=mock_poll), \
         patch("api.poller.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        mock_sleep.side_effect = [None, asyncio.CancelledError()]
        try:
            await run_poll_loop(servers)
        except asyncio.CancelledError:
            pass

    assert call_count >= 2
