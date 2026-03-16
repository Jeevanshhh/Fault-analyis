"""
SHDN -- Load Forecaster
LSTM model for 24-hour (48 step) load forecasting.
"""

import numpy as np
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from data_processor import get_load_sequences

MODEL_PATH = Path(__file__).parent / "models" / "load_forecaster.h5"
SCALE_PATH = Path(__file__).parent / "models" / "load_scale.json"
SEQ_LEN = 48


def build_model(seq_len: int = SEQ_LEN):
    from tensorflow import keras
    from tensorflow.keras import layers

    model = keras.Sequential(
        [
            layers.Input(shape=(seq_len, 1)),
            layers.LSTM(128, return_sequences=True),
            layers.Dropout(0.2),
            layers.LSTM(64),
            layers.Dropout(0.2),
            layers.Dense(32, activation="relu"),
            layers.Dense(1),
        ]
    )
    model.compile(optimizer="adam", loss="mse", metrics=["mae"])
    return model


def train():
    print("Preparing LSTM sequences ...")
    X, y, scale = get_load_sequences(seq_len=SEQ_LEN)

    split = int(len(X) * 0.8)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    print(
        f"Training LSTM: {X_train.shape[0]} train, {X_test.shape[0]} test samples ..."
    )
    model = build_model(SEQ_LEN)
    model.summary()

    from tensorflow.keras.callbacks import EarlyStopping

    cb = EarlyStopping(patience=5, restore_best_weights=True)
    model.fit(
        X_train,
        y_train,
        validation_data=(X_test, y_test),
        epochs=30,
        batch_size=64,
        callbacks=[cb],
        verbose=1,
    )

    loss, mae = model.evaluate(X_test, y_test, verbose=0)
    print(f"\nTest MAE: {mae * scale:.2f} kW  (normalised MAE: {mae:.4f})")

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(MODEL_PATH))
    with open(SCALE_PATH, "w") as f:
        json.dump({"max_load_kw": float(scale)}, f)
    print(f"Model saved -> {MODEL_PATH}")
    return model, scale


def load_model():
    from tensorflow import keras

    if not MODEL_PATH.exists():
        print("LSTM model not found, training now ...")
        return train()
    model = keras.models.load_model(str(MODEL_PATH))
    with open(SCALE_PATH) as f:
        scale = json.load(f)["max_load_kw"]
    return model, scale


def predict_next_24h(recent_loads_kw: list) -> dict:
    """
    recent_loads_kw: list of last SEQ_LEN load values in kW.
    Returns 48-step (24h) forecast in kW.
    """
    model, scale = load_model()
    seq = np.array(recent_loads_kw[-SEQ_LEN:], dtype=np.float32) / scale
    seq = seq.reshape(1, SEQ_LEN, 1)

    # Autoregressive rollout for 48 steps
    preds = []
    current = seq.copy()
    for _ in range(48):
        p = model.predict(current, verbose=0)[0, 0]
        preds.append(float(p) * scale)
        current = np.roll(current, -1, axis=1)
        current[0, -1, 0] = p

    return {
        "forecast_kw": [round(v, 2) for v in preds],
        "peak_kw": round(max(preds), 2),
        "avg_kw": round(sum(preds) / len(preds), 2),
        "horizon_hours": 24,
    }


if __name__ == "__main__":
    train()
