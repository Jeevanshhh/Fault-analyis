"""SHDN -- Consumers Router"""

from fastapi import APIRouter
import pandas as pd
import random
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from simulator import simulator

router = APIRouter(prefix="/consumers", tags=["Consumers"])
DATASET_DIR = Path(__file__).parent.parent.parent / "datasets"


@router.get("")
def get_consumers():
    """Return all consumers with live status derived from their node's grid status."""
    try:
        load_df = pd.read_csv(DATASET_DIR / "load_data.csv", parse_dates=["timestamp"])
        # Latest snapshot per consumer
        latest = (
            load_df.sort_values("timestamp").groupby("consumer_id").last().reset_index()
        )
    except Exception:
        latest = pd.DataFrame()

    node_status = {n["node_id"]: n["status"] for n in simulator.nodes.values()}
    consumers = []

    if not latest.empty:
        for _, row in latest.iterrows():
            nid = row.get("node_id", "bus_1")
            status = node_status.get(nid, "healthy")
            consumers.append(
                {
                    "consumer_id": row["consumer_id"],
                    "node_id": nid,
                    "area": row.get("area", "zone_a"),
                    "load_kw": round(
                        float(row["load_kw"]) * random.uniform(0.9, 1.1), 2
                    ),
                    "peak_load_kw": float(row["peak_load_kw"]),
                    "avg_load_kw": float(row["avg_load_kw"]),
                    "status": "outage" if status == "fault" else "active",
                }
            )
    return {"consumers": consumers, "count": len(consumers)}


@router.get("/{consumer_id}/analytics")
def get_consumer_analytics(consumer_id: str):
    try:
        load_df = pd.read_csv(DATASET_DIR / "load_data.csv", parse_dates=["timestamp"])
        cdf = load_df[load_df["consumer_id"] == consumer_id].sort_values("timestamp")
        if cdf.empty:
            return {"error": "Consumer not found"}
        recent = cdf.tail(48)
        series = [
            {"timestamp": str(r["timestamp"]), "load_kw": round(float(r["load_kw"]), 2)}
            for _, r in recent.iterrows()
        ]
        return {
            "consumer_id": consumer_id,
            "node_id": cdf["node_id"].iloc[0],
            "area": cdf["area"].iloc[0],
            "peak_load_kw": round(float(cdf["load_kw"].max()), 2),
            "avg_load_kw": round(float(cdf["load_kw"].mean()), 2),
            "load_series": series,
        }
    except Exception as e:
        return {"error": str(e)}
