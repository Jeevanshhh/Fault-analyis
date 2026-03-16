"""SHDN -- Forecast Router"""

from fastapi import APIRouter
import random
import math
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from simulator import simulator

router = APIRouter(prefix="/forecast", tags=["Forecast"])


@router.get("/load")
def get_load_forecast():
    """
    Return a 48-step (24-hour) load forecast.
    Uses mock sine-wave pattern when LSTM model is not yet trained.
    """
    state = simulator.get_state()
    base_load = state["stats"]["total_load_kw"]
    now = datetime.utcnow()

    forecast = []
    for i in range(48):
        t = now + timedelta(minutes=30 * i)
        hour = t.hour + t.minute / 60
        # Sine-wave daily load pattern
        load = base_load * (0.6 + 0.4 * math.sin(math.pi * (hour - 6) / 12))
        load += random.gauss(0, base_load * 0.05)
        forecast.append(
            {
                "timestamp": t.isoformat(),
                "load_kw": round(max(0, load), 2),
            }
        )

    return {
        "horizon_hours": 24,
        "step_minutes": 30,
        "forecast": forecast,
        "peak_kw": round(max(f["load_kw"] for f in forecast), 2),
        "avg_kw": round(sum(f["load_kw"] for f in forecast) / len(forecast), 2),
    }


@router.get("/risk")
def get_fault_risk():
    """Return predicted fault risk per zone based on weather + load."""
    weather = simulator.weather
    zones = ["zone_a", "zone_b", "zone_c", "zone_d"]
    risks = []
    for zone in zones:
        # Weighted risk score
        base = 0.05
        risk = base
        risk += weather["lightning_risk"] * 0.4
        risk += min(weather["wind_kmh"] / 100, 0.3)
        risk += min(weather["rain_mm"] / 20, 0.2)
        risk += random.uniform(-0.02, 0.05)  # zone variation
        risk = round(min(1.0, max(0.0, risk)), 3)
        risks.append(
            {
                "zone": zone,
                "risk_score": risk,
                "risk_level": (
                    "high" if risk > 0.6 else "medium" if risk > 0.3 else "low"
                ),
            }
        )
    return {"weather": weather, "zone_risks": risks}


@router.get("/weather")
def get_weather():
    return simulator.weather
