"""SHDN -- Grid Router"""

from fastapi import APIRouter
from pydantic import BaseModel
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from simulator import simulator

router = APIRouter(prefix="/grid", tags=["Grid"])


class SwitchRequest(BaseModel):
    node_id: str
    action: str  # "open" | "close"


@router.get("/nodes")
def get_nodes():
    state = simulator.get_state()
    return {"nodes": state["nodes"], "timestamp": state["timestamp"]}


@router.get("/topology")
def get_topology():
    import pandas as pd

    topo = pd.read_csv(
        Path(__file__).parent.parent.parent / "datasets" / "grid_topology.csv"
    )
    nodes = pd.read_csv(
        Path(__file__).parent.parent.parent / "datasets" / "node_data.csv"
    )
    return {
        "edges": topo.to_dict(orient="records"),
        "nodes": nodes.to_dict(orient="records"),
    }


@router.get("/stats")
def get_stats():
    return simulator.get_state()["stats"]


@router.post("/switch")
def switch_node(req: SwitchRequest):
    if req.node_id not in simulator.nodes:
        return {"error": "Invalid node_id"}
    with simulator._lock:
        simulator.nodes[req.node_id]["status"] = (
            "healthy" if req.action == "close" else "isolated"
        )
    return {"node_id": req.node_id, "action": req.action, "status": "applied"}
