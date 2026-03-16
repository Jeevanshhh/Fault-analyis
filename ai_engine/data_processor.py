"""
SHDN -- Data Processor
Loads, merges, and feature-engineers all datasets for model training.
"""

import pandas as pd
import numpy as np
from pathlib import Path

DATASET_DIR = Path(__file__).parent.parent / "datasets"


def load_and_merge() -> pd.DataFrame:
    """Load sensor + weather datasets and merge on nearest timestamp."""
    sensor = pd.read_csv(DATASET_DIR / "sensor_data.csv", parse_dates=["timestamp"])
    weather = pd.read_csv(DATASET_DIR / "weather_data.csv", parse_dates=["timestamp"])
    load = pd.read_csv(DATASET_DIR / "load_data.csv", parse_dates=["timestamp"])

    # Aggregate load per node per 10-second window
    load_agg = (
        load.groupby(["timestamp", "node_id"])["load_kw"]
        .sum()
        .reset_index()
        .rename(columns={"load_kw": "total_load_kw"})
    )

    # Merge sensor with load
    df = sensor.merge(load_agg, on=["timestamp", "node_id"], how="left")
    df["total_load_kw"] = df["total_load_kw"].fillna(df["power_kw"])

    # Merge weather -- forward fill since weather is at 30-min intervals
    weather_sorted = weather.sort_values("timestamp")
    df = pd.merge_asof(
        df.sort_values("timestamp"),
        weather_sorted,
        on="timestamp",
        direction="backward",
    )
    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create engineered features matching the fault classifier input spec."""
    nominal_voltage = 230.0

    df["voltage_drop_pct"] = (
        (nominal_voltage - df["voltage_v"]) / nominal_voltage * 100
    ).clip(lower=0)
    df["current_spike"] = (df["current_a"] - df["current_a"].mean()) / df[
        "current_a"
    ].std()
    df["rain_mm"] = df["rain_mm"].fillna(0)
    df["wind_kmh"] = df["wind_kmh"].fillna(20)
    df["lightning_risk"] = df["lightning_risk"].fillna(0)

    # Rolling averages (window = 6 rows = 60 seconds)
    for col in ["voltage_v", "current_a", "frequency_hz"]:
        df[f"{col}_roll6"] = df[col].rolling(6, min_periods=1).mean()

    df = df.dropna(
        subset=[
            "voltage_drop_pct",
            "current_spike",
            "power_kw",
            "temperature_c",
            "wind_kmh",
            "rain_mm",
            "total_load_kw",
        ]
    )
    return df


FEATURE_COLS = [
    "voltage_drop_pct",
    "current_spike",
    "power_kw",
    "temperature_c",
    "wind_kmh",
    "rain_mm",
    "lightning_risk",
    "total_load_kw",
    "voltage_v_roll6",
    "current_a_roll6",
    "frequency_hz_roll6",
]

TARGET_COL = "fault_flag"


def get_train_test(test_size: float = 0.2):
    """Return (X_train, X_test, y_train, y_test) ready for model training."""
    from sklearn.model_selection import train_test_split

    df = engineer_features(load_and_merge())
    X = df[FEATURE_COLS].values
    y = df[TARGET_COL].values
    return train_test_split(X, y, test_size=test_size, random_state=42, stratify=y)


def get_load_sequences(node_id: str = None, seq_len: int = 48):
    """Return (X_seq, y_seq) for LSTM training. Each sample: seq_len -> next value."""
    load = pd.read_csv(DATASET_DIR / "load_data.csv", parse_dates=["timestamp"])
    if node_id:
        load = load[load["node_id"] == node_id]

    series = (
        load.groupby("timestamp")["load_kw"]
        .sum()
        .sort_index()
        .values.astype(np.float32)
    )

    # Normalize
    max_val = series.max() if series.max() > 0 else 1.0
    series = series / max_val

    X, y = [], []
    for i in range(len(series) - seq_len):
        X.append(series[i : i + seq_len])
        y.append(series[i + seq_len])

    return np.array(X)[..., np.newaxis], np.array(y), max_val


if __name__ == "__main__":
    X_tr, X_te, y_tr, y_te = get_train_test()
    print(f"Train: {X_tr.shape}, Test: {X_te.shape}")
    print(f"Fault rate train: {y_tr.mean():.3f}")
    Xs, ys, scale = get_load_sequences()
    print(f"LSTM sequences: {Xs.shape}, scale={scale:.1f} kW")
