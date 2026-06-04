import asyncio
import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from api.auth import verify_api_key
from api.metrics import get_system_metrics
from api.models import Server, ServerIn, ServerOut
from api.poller import run_poll_loop

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s — %(message)s")

_store: dict[int, Server] = {}
_counter = 0
_poll_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _poll_task
    _poll_task = asyncio.create_task(run_poll_loop(_store))
    logging.info("Background poller started.")
    yield
    if _poll_task:
        _poll_task.cancel()
        logging.info("Background poller stopped.")


app = FastAPI(title="DevOps Monitoring API", version="1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System"])
async def health():
    return {"status": "ok", "servers_monitored": len(_store)}


@app.get("/metrics", tags=["System"])
async def metrics():
    return get_system_metrics()


@app.websocket("/ws/metrics")
async def ws_metrics(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.send_text(json.dumps(get_system_metrics()))
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass


@app.post("/servers", response_model=ServerOut, status_code=201, tags=["Servers"])
async def register_server(body: ServerIn, _: str = Depends(verify_api_key)):
    global _counter
    _counter += 1
    server = Server(id=_counter, name=body.name, host=body.host, port=body.port, tags=body.tags)
    _store[_counter] = server
    return server


@app.get("/servers", response_model=list[ServerOut], tags=["Servers"])
async def list_servers(status: str | None = None):
    servers = list(_store.values())
    if status:
        servers = [s for s in servers if s.status == status]
    return servers


@app.get("/servers/{server_id}", response_model=ServerOut, tags=["Servers"])
async def get_server(server_id: int):
    if server_id not in _store:
        raise HTTPException(status_code=404, detail="Server not found")
    return _store[server_id]


@app.delete("/servers/{server_id}", status_code=204, tags=["Servers"])
async def delete_server(server_id: int, _: str = Depends(verify_api_key)):
    if server_id not in _store:
        raise HTTPException(status_code=404, detail="Server not found")
    del _store[server_id]


@app.post("/servers/{server_id}/check", response_model=ServerOut, tags=["Servers"])
async def trigger_check(server_id: int):
    if server_id not in _store:
        raise HTTPException(status_code=404, detail="Server not found")
    from api.poller import poll_server
    await poll_server(server_id, _store[server_id].base_url(), _store)
    return _store[server_id]
