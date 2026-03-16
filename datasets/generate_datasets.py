"""
SHDN -- Dataset Generator
Generates all 6 synthetic datasets for the Self-Healing Distribution Network.
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os

np.random.seed(42)
ROWS = 500000
START = datetime(2024, 1, 1)
NODES = [f"bus_{i}" for i in range(1, 13)]
ZONES = {
    "bus_1": "zone_a", "bus_2": "zone_a", "bus_3": "zone_a", "bus_4": "zone_a",
    "bus_5": "zone_b", "bus_6": "zone_b", "bus_7": "zone_b",
    "bus_8": "zone_c", "bus_9": "zone_c", "bus_10": "zone_c",
    "bus_11": "zone_d", "bus_12": "zone_d"
}

timestamps = [START + timedelta(seconds=i * 10) for i in range(ROWS)]

# --- 1. sensor_data.csv -------------------------------------------------------
print("Generating sensor_data.csv ...")
node_ids = np.random.choice(NODES, size=ROWS)
voltage = np.random.normal(230, 5, ROWS)
current = np.random.normal(12, 2, ROWS)
frequency = np.random.normal(50, 0.05, ROWS)
temperature_c = np.random.normal(30, 8, ROWS)

# Inject faults (5% of rows)
fault_mask = np.random.random(ROWS) < 0.05
voltage[fault_mask] *= np.random.uniform(0.3, 0.7, fault_mask.sum())
current[fault_mask] *= np.random.uniform(1.5, 3.0, fault_mask.sum())
power_kw = voltage * current / 1000

sensor_df = pd.DataFrame({
    "timestamp": timestamps,
    "node_id": node_ids,
    "voltage_v": np.round(voltage, 2),
    "current_a": np.round(current, 2),
    "frequency_hz": np.round(frequency, 3),
    "power_kw": np.round(power_kw, 2),
    "temperature_c": np.round(temperature_c, 1),
    "fault_flag": fault_mask.astype(int)
})
sensor_df.to_csv("sensor_data.csv", index=False, encoding="utf-8")
print(f"  >> {len(sensor_df):,} rows written to sensor_data.csv")

# --- 2. fault_data.csv --------------------------------------------------------
print("Generating fault_data.csv ...")
FAULT_TYPES = ["line_fault", "ground_fault", "short_circuit", "voltage_sag", "overload", "normal"]
FAULT_WEIGHTS = [0.15, 0.12, 0.10, 0.18, 0.10, 0.35]
N_FAULTS = 20000
rng_idx = np.random.randint(0, ROWS * 10, size=N_FAULTS)
fault_ts = [START + timedelta(seconds=int(s)) for s in rng_idx]
fault_types = np.random.choice(FAULT_TYPES, size=N_FAULTS, p=FAULT_WEIGHTS)
fault_locations = np.random.choice(NODES, size=N_FAULTS)

is_normal = fault_types == "normal"
v_drop = np.where(is_normal, np.random.uniform(0, 5, N_FAULTS), np.random.uniform(20, 70, N_FAULTS))
c_spike = np.where(is_normal, np.random.uniform(0, 2, N_FAULTS), np.random.uniform(10, 80, N_FAULTS))
duration = np.where(is_normal, 0.0, np.random.exponential(30, N_FAULTS))
severity = np.select(
    [is_normal,
     np.isin(fault_types, ["voltage_sag"]),
     np.isin(fault_types, ["overload", "ground_fault"]),
     np.isin(fault_types, ["line_fault", "short_circuit"])],
    ["none", "low", "medium", "high"],
    default="medium"
)

fault_df = pd.DataFrame({
    "timestamp": fault_ts,
    "fault_type": fault_types,
    "location": fault_locations,
    "voltage_drop_pct": np.round(v_drop, 2),
    "current_spike_a": np.round(c_spike, 2),
    "duration_s": np.round(duration, 1),
    "severity": severity
})
fault_df.to_csv("fault_data.csv", index=False, encoding="utf-8")
print(f"  >> {len(fault_df):,} rows written to fault_data.csv")

# --- 3. weather_data.csv ------------------------------------------------------
print("Generating weather_data.csv ...")
W = 100000
w_timestamps = [START + timedelta(minutes=i * 30) for i in range(W)]
w_temp = 30 + 10 * np.sin(np.linspace(0, 6 * np.pi, W)) + np.random.normal(0, 3, W)
w_wind = np.abs(np.random.normal(20, 15, W))
w_rain = np.random.exponential(2, W) * (np.random.random(W) < 0.3)
w_lightning = np.clip(w_rain / 10 + w_wind / 100 + np.random.uniform(0, 0.3, W), 0, 1)
w_humidity = np.clip(50 + w_rain * 3 + np.random.normal(0, 10, W), 20, 100)

weather_df = pd.DataFrame({
    "timestamp": w_timestamps,
    "temp_c": np.round(w_temp, 1),
    "wind_kmh": np.round(w_wind, 1),
    "rain_mm": np.round(w_rain, 2),
    "lightning_risk": np.round(w_lightning, 3),
    "humidity_pct": np.round(w_humidity, 1)
})
weather_df.to_csv("weather_data.csv", index=False, encoding="utf-8")
print(f"  >> {len(weather_df):,} rows written to weather_data.csv")

# --- 4. load_data.csv ---------------------------------------------------------
print("Generating load_data.csv ...")
N_CONSUMERS = 250
consumer_ids = [f"C{str(i).zfill(3)}" for i in range(1, N_CONSUMERS + 1)]
consumer_nodes = np.random.choice(NODES, size=N_CONSUMERS)
consumer_areas = [ZONES[n] for n in consumer_nodes]

load_rows = []
for cid, cnode, carea in zip(consumer_ids, consumer_nodes, consumer_areas):
    peak = np.random.uniform(5, 50)
    for i in range(800):
        t = START + timedelta(minutes=i * 30)
        hour = (i // 2) % 24
        base = peak * (0.5 + 0.5 * np.sin(np.pi * hour / 12))
        load = max(0.0, base + np.random.normal(0, peak * 0.1))
        load_rows.append({
            "timestamp": t,
            "consumer_id": cid,
            "node_id": cnode,
            "area": carea,
            "load_kw": round(load, 2),
            "peak_load_kw": round(peak, 2),
            "avg_load_kw": round(peak * 0.6, 2)
        })

load_df = pd.DataFrame(load_rows)
load_df.to_csv("load_data.csv", index=False, encoding="utf-8")
print(f"  >> {len(load_df):,} rows written to load_data.csv")

# --- 5. grid_topology.csv -----------------------------------------------------
print("Generating grid_topology.csv ...")
topo_rows = [
    ("bus_1",  "bus_2",  1000, "active"),
    ("bus_1",  "bus_3",   800, "active"),
    ("bus_2",  "bus_4",   500, "active"),
    ("bus_2",  "bus_5",   400, "active"),
    ("bus_3",  "bus_6",   350, "active"),
    ("bus_3",  "bus_7",   300, "active"),
    ("bus_4",  "bus_8",   250, "active"),
    ("bus_5",  "bus_9",   200, "active"),
    ("bus_6",  "bus_10",  200, "active"),
    ("bus_7",  "bus_11",  150, "active"),
    ("bus_8",  "bus_12",  120, "active"),
    # Backup / alternate paths for restoration
    ("bus_4",  "bus_6",  180, "backup"),
    ("bus_5",  "bus_7",  160, "backup"),
    ("bus_9",  "bus_10", 140, "backup"),
    ("bus_10", "bus_11", 130, "backup"),
    ("bus_11", "bus_12", 100, "backup"),
]
topology_df = pd.DataFrame(topo_rows, columns=["from_node", "to_node", "capacity_kw", "status"])
topology_df.to_csv("grid_topology.csv", index=False, encoding="utf-8")
print(f"  >> {len(topology_df)} rows written to grid_topology.csv")

# --- 6. node_data.csv ---------------------------------------------------------
print("Generating node_data.csv ...")
node_rows = [
    ("bus_1",  "substation", 2000, "zone_a", True,  3.0, 0.0),
    ("bus_2",  "feeder",     1000, "zone_a", False, 2.5, 1.0),
    ("bus_3",  "feeder",      800, "zone_a", False, 2.0, 1.0),
    ("bus_4",  "feeder",      500, "zone_b", False, 1.5, 2.0),
    ("bus_5",  "feeder",      400, "zone_b", False, 1.5, 2.0),
    ("bus_6",  "feeder",      350, "zone_b", False, 0.5, 2.0),
    ("bus_7",  "feeder",      300, "zone_c", False, 0.0, 1.5),
    ("bus_8",  "load_node",   250, "zone_c", False, 1.0, 3.0),
    ("bus_9",  "load_node",   200, "zone_c", False, 2.0, 2.5),
    ("bus_10", "load_node",   200, "zone_d", False, 3.0, 1.5),
    ("bus_11", "load_node",   150, "zone_d", False, 2.5, 0.5),
    ("bus_12", "load_node",   120, "zone_d", False, 1.5, 0.0),
]
node_df = pd.DataFrame(node_rows, columns=[
    "node_id", "type", "capacity_kw", "zone", "is_source", "pos_x", "pos_y"
])
node_df.to_csv("node_data.csv", index=False, encoding="utf-8")
print(f"  >> {len(node_df)} rows written to node_data.csv")

print("\nAll 6 datasets generated successfully!")
