"""SHDN -- Faults Router"""

from fastapi import APIRouter
from pydantic import BaseModel
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from simulator import simulator

router = APIRouter(prefix="/faults", tags=["Faults"])


class InjectRequest(BaseModel):
    node_id: str
    fault_type: str = "line_fault"


@router.get("/active")
def get_active_faults():
    return {"faults": simulator.active_faults, "count": len(simulator.active_faults)}


@router.get("/history")
def get_fault_history(limit: int = 100):
    return {"faults": simulator.fault_history[:limit]}


@router.post("/inject")
def inject_fault(req: InjectRequest):
    event = simulator.inject_fault_manual(req.node_id, req.fault_type)
    return {"injected": event}


@router.get("/stats")
def fault_stats():
    history = simulator.fault_history
    by_type = {}
    by_severity = {}
    for f in history:
        ftype = f.get("fault_type", "unknown")
        sev = f.get("severity", "unknown")
        by_type[ftype] = by_type.get(ftype, 0) + 1
        by_severity[sev] = by_severity.get(sev, 0) + 1
    return {
        "total": len(history),
        "active": len(simulator.active_faults),
        "by_type": by_type,
        "by_severity": by_severity,
    }
