import asyncio
import logging
import httpx
from api.models import Server

logger = logging.getLogger(__name__)


async def poll_server(server_id: int, url: str, store: dict[int, Server]) -> None:
    """Check a single server's /health endpoint and update its status in store."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{url}/health")
        store[server_id].status = "UP" if resp.status_code == 200 else "DEGRADED"
        logger.info("%-20s → %s", store[server_id].name, store[server_id].status)
    except Exception as e:
        if server_id in store:
            store[server_id].status = "DOWN"
        logger.warning("%-20s → DOWN (%s)", url, e)


async def run_poll_loop(store: dict[int, Server], interval: int = 10) -> None:
    """Infinite loop: poll all servers concurrently every `interval` seconds."""
    while True:
        if store:
            await asyncio.gather(
                *[poll_server(sid, s.base_url(), store) for sid, s in store.items()]
            )
        await asyncio.sleep(interval)
