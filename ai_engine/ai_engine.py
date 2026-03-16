"""
SHDN -- AI Engine (FastAPI Microservice, port 8001)
Unified inference API for fault detection, load forecasting, and grid restoration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

app = FastAPI(title="SHDN AI Engine", version="1.0.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

# Lazy-load models to avoid startup delay during development
_fault_model = None
_lstm_model = None
_lstm_scale = None
_grid_graph = None


def get_fault_model():
    global _fault_model
    if _fault_model is None:
        from fault_classifier import load_model

        _fault_model = load_model()
    return _fault_model


def get_lstm():
    global _lstm_model, _lstm_scale
    if _lstm_model is None:
        from load_forecaster import load_model as lstm_load

        _lstm_model, _lstm_scale = lstm_load()
    return _lstm_model, _lstm_scale


def get_graph():
    global _grid_graph
    if _grid_graph is None:
        from restoration_engine import build_grid_graph

        _grid_graph = build_grid_graph()
    return _grid_graph


# ─── Schemas ─────────────────────────────────────────────────────────────────


class FaultFeatures(BaseModel):
    voltage_drop_pct: float = 0.0
    current_spike: float = 0.0
    power_kw: float = 0.0
    temperature_c: float = 30.0
    wind_kmh: float = 20.0
    rain_mm: float = 0.0
    lightning_risk: float = 0.0
    total_load_kw: float = 0.0
    voltage_v_roll6: float = 230.0
    current_a_roll6: float = 12.0
    frequency_hz_roll6: float = 50.0


class LoadForecastRequest(BaseModel):
    recent_loads_kw: List[float]


class RestoreRequest(BaseModel):
    faulted_node: str
    source_node: str = "bus_1"


# ─── Endpoints ────────────────────────────────────────────────────────────────


@app.get("/health")
def health():
    return {"status": "ok", "service": "SHDN AI Engine"}


@app.post("/predict/fault")
def predict_fault(features: FaultFeatures):
    from fault_classifier import predict

    result = predict(features.model_dump())
    return result


@app.post("/predict/load")
def predict_load(req: LoadForecastRequest):
    from load_forecaster import predict_next_24h

    return predict_next_24h(req.recent_loads_kw)


@app.post("/restore")
def restore(req: RestoreRequest):
    from restoration_engine import find_restoration_path, isolate_fault


    G = get_graph()
    isolation = isolate_fault(req.faulted_node, G.copy())
    restoration = find_restoration_path(req.faulted_node, G.copy(), req.source_node)
    return {"isolation": isolation, "restoration": restoration}


@app.get("/graph/nodes")
def graph_nodes():
    G = get_graph()
    nodes = []
    for node_id, data in G.nodes(data=True):
        nodes.append({"node_id": node_id, **data})
    return {"nodes": nodes}


@app.get("/graph/edges")
def graph_edges():
    G = get_graph()
    edges = []
    for u, v, data in G.edges(data=True):
        edges.append({"from": u, "to": v, **data})
    return {"edges": edges}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
