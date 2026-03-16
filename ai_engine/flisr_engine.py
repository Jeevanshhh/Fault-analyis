"""
SHDN -- FLISR Engine (Fault Location, Isolation, Service Restoration)
Calculates isolation boundaries and alternate restoration paths.
"""

import sys
from pathlib import Path
import networkx as nx

sys.path.insert(0, str(Path(__file__).parent))
from restoration_engine import build_grid_graph, isolate_fault, find_restoration_path


def run_flisr(fault_node: str, G: nx.Graph = None) -> dict:
    """
    Executes the FLISR workflow for a given fault location.

    1. F - Location (Assume fault_node is the located fault based on sensor/AI)
    2. I - Isolation: Find upstream breakers and downstream sectionalizers to open.
    3. SR - Service Restoration: Find backup feeders to close for out-of-service neighbors.
    """
    if G is None:
        G = build_grid_graph()

    report = {
        "fault_node": fault_node,
        "isolation": {},
        "restoration": {},
        "status": "pending",
    }

    # 2. ISOLATION
    iso_result = isolate_fault(fault_node, G)
    report["isolation"] = iso_result

    # 3. RESTORATION
    restore_result = find_restoration_path(fault_node, G.copy())
    report["restoration"] = restore_result

    if restore_result["status"] == "restoration_path_found":
        report["status"] = "success"
    else:
        report["status"] = "partial_or_failed"

    return report


if __name__ == "__main__":
    import json

    res = run_flisr("bus_4")
    print(json.dumps(res, indent=2))
