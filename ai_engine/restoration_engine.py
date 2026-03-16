"""
SHDN -- Restoration Engine
Graph-based algorithm to find alternate power paths after fault isolation.
Uses NetworkX to model the grid topology and BFS/Dijkstra for path finding.
"""

import pandas as pd
import networkx as nx
from pathlib import Path
from typing import Optional

DATASET_DIR = Path(__file__).parent.parent / "datasets"


def build_grid_graph(topology_csv: Optional[str] = None) -> nx.Graph:
    """Build a weighted undirected graph from grid_topology.csv."""
    if topology_csv is None:
        topology_csv = str(DATASET_DIR / "grid_topology.csv")

    df = pd.read_csv(topology_csv)
    G = nx.Graph()

    # Add nodes with metadata
    node_df = pd.read_csv(DATASET_DIR / "node_data.csv")
    for _, row in node_df.iterrows():
        G.add_node(row["node_id"], **row.to_dict())

    # Add edges; weight = 1/capacity so high-capacity edges are preferred
    for _, row in df.iterrows():
        if row["status"] in ("active", "backup"):
            G.add_edge(
                row["from_node"],
                row["to_node"],
                capacity_kw=row["capacity_kw"],
                status=row["status"],
                weight=1.0 / row["capacity_kw"],
            )
    return G


def find_restoration_path(
    faulted_node: str, G: Optional[nx.Graph] = None, source_node: str = "bus_1"
) -> dict:
    """
    Find the best alternate restoration path for faulted_node.

    Steps:
      1. Remove faulted node from graph.
      2. Find shortest path from source to each neighbor of faulted node.
      3. Return the path, switching sequence, and estimated restoration time.
    """
    if G is None:
        G = build_grid_graph()

    if faulted_node not in G:
        return {"error": f"Node {faulted_node} not in grid graph"}

    # Collect downstream nodes connected through faulted_node
    neighbors = list(G.neighbors(faulted_node))

    # Temporarily remove faulted node
    G_temp = G.copy()
    G_temp.remove_node(faulted_node)

    restoration_paths = []
    for neighbor in neighbors:
        if neighbor == source_node:
            continue
        try:
            path = nx.shortest_path(
                G_temp, source=source_node, target=neighbor, weight="weight"
            )
            path_cap = min(
                G_temp[path[i]][path[i + 1]]["capacity_kw"]
                for i in range(len(path) - 1)
            )
            restoration_paths.append(
                {
                    "target_node": neighbor,
                    "path": path,
                    "path_length": len(path) - 1,
                    "bottleneck_capacity_kw": path_cap,
                }
            )
        except nx.NetworkXNoPath:
            restoration_paths.append(
                {
                    "target_node": neighbor,
                    "path": [],
                    "path_length": None,
                    "bottleneck_capacity_kw": 0,
                }
            )

    # Best path = highest bottleneck capacity
    viable = [p for p in restoration_paths if p["bottleneck_capacity_kw"] > 0]
    if not viable:
        return {
            "faulted_node": faulted_node,
            "status": "no_alternate_path",
            "restoration_paths": restoration_paths,
        }

    best = max(viable, key=lambda p: p["bottleneck_capacity_kw"])

    # Build switching sequence
    switching_ops = []
    for i in range(len(best["path"]) - 1):
        edge_data = G[best["path"][i]][best["path"][i + 1]]
        if edge_data.get("status") == "backup":
            switching_ops.append(
                {
                    "action": "CLOSE",
                    "switch": f"SW_{best['path'][i]}_{best['path'][i + 1]}",
                    "from": best["path"][i],
                    "to": best["path"][i + 1],
                    "type": "backup_feeder",
                }
            )

    # Estimated restoration time (seconds): 5s per hop + 10s per switch operation
    est_time_s = len(best["path"]) * 5 + len(switching_ops) * 10

    return {
        "faulted_node": faulted_node,
        "status": "restoration_path_found",
        "best_path": best,
        "switching_sequence": switching_ops,
        "estimated_restoration_time_s": est_time_s,
        "all_paths": restoration_paths,
    }


def isolate_fault(faulted_node: str, G: Optional[nx.Graph] = None) -> dict:
    """Return upstream breaker and sectionalizers to open for isolation."""
    if G is None:
        G = build_grid_graph()

    isolation_ops = [
        {
            "action": "OPEN",
            "switch": f"BREAKER_upstream_{faulted_node}",
            "node": faulted_node,
            "type": "upstream_breaker",
        }
    ]
    for neighbor in G.neighbors(faulted_node):
        isolation_ops.append(
            {
                "action": "OPEN",
                "switch": f"SECT_{neighbor}_{faulted_node}",
                "node": neighbor,
                "type": "sectionalizer",
            }
        )

    return {
        "faulted_node": faulted_node,
        "isolation_ops": isolation_ops,
        "isolation_time_s": len(isolation_ops) * 3,
    }


if __name__ == "__main__":
    G = build_grid_graph()
    print(f"Grid graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges\n")

    for test_node in ["bus_4", "bus_7", "bus_10"]:
        iso = isolate_fault(test_node, G.copy())
        res = find_restoration_path(test_node, G.copy())
        print(f"Fault @ {test_node}:")
        print(f"  Isolation ops : {len(iso['isolation_ops'])} switches")
        if res["status"] == "restoration_path_found":
            bp = res["best_path"]
            print(f"  Best path     : {' -> '.join(bp['path'])}")
            print(f"  Capacity      : {bp['bottleneck_capacity_kw']} kW")
            print(f"  Est. restore  : {res['estimated_restoration_time_s']}s")
        else:
            print(f"  Status        : {res['status']}")
        print()
