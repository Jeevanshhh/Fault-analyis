"""
SHDN -- Backend API Entry Point (FastAPI, port 8000)
Provides REST endpoints + WebSocket live grid stream.
"""

import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from simulator import simulator
from digital_twin import digital_twin
from routers import grid, faults, forecast, consumers

# ─── Lifespan ─────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    simulator.start()
    print("Grid simulator started.")
    yield
    simulator.stop()
    print("Grid simulator stopped.")


# ─── App Setup ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="SHDN Backend API",
    version="1.0.0",
    description="Self-Healing Distribution Network Control API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(grid.router)
app.include_router(faults.router)
app.include_router(forecast.router)
app.include_router(consumers.router)


# ─── WebSocket Manager ────────────────────────────────────────────────────────


class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, data: dict):
        payload = json.dumps(data, default=str)
        dead = []
        for ws in self.active:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


# ─── WebSocket Endpoint ───────────────────────────────────────────────────────


@app.websocket("/ws/grid")
async def websocket_grid(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            state = simulator.get_state()
            twin_report = digital_twin.compare(state["nodes"])
            payload = {
                "type": "grid_update",
                **state,
                "digital_twin": twin_report,
            }
            await websocket.send_text(json.dumps(payload, default=str))
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ─── REST Endpoints ───────────────────────────────────────────────────────────


@app.get("/")
def root():
    return {
        "service": "SHDN Backend API",
        "version": "1.0.0",
        "docs": "/docs",
        "websocket": "ws://localhost:8000/ws/grid",
    }


@app.get("/health")
def health():
    state = simulator.get_state()
    return {
        "status": "ok",
        "simulator_tick": state["tick"],
        "active_faults": state["stats"]["active_faults"],
        "healthy_nodes": state["stats"]["healthy_nodes"],
    }


@app.get("/digital-twin")
def get_digital_twin():
    state = simulator.get_state()
    return digital_twin.compare(state["nodes"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
