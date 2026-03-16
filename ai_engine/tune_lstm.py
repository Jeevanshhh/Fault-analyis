"""
SHDN -- Tune LSTM Load Forecaster
Advanced LSTM architecture for 24-hour load forecasting.
Trains for 50 epochs and outputs MAE, RMSE, and MAPE metrics.
"""

import json
import math
import sys
from pathlib import Path

import numpy as np
from tensorflow import keras
from tensorflow.keras import layers

sys.path.insert(0, str(Path(__file__).parent))
from data_processor import get_load_sequences

RESULTS_DIR = Path(__file__).parent.parent / "results"
MODEL_PATH = Path(__file__).parent / "models" / "load_forecaster.h5"
SCALE_PATH = Path(__file__).parent / "models" / "load_scale.json"
SEQ_LEN = 48


def build_advanced_model(seq_len: int = SEQ_LEN):
    model = keras.Sequential(
        [
            layers.Input(shape=(seq_len, 1)),
            layers.LSTM(128, return_sequences=True),
            layers.Dropout(0.2),
            layers.LSTM(64),
            layers.Dense(32, activation="relu"),
            layers.Dense(1),
        ]
    )
    model.compile(optimizer="adam", loss="mse", metrics=["mae"])
    return model


def tune_and_train():
    print("Loading scaled load sequences ...")
    X, y, scale = get_load_sequences(seq_len=SEQ_LEN)

    # Split
    split = int(len(X) * 0.8)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    print(f"Dataset loaded. Train shape: {X_train.shape}, Test shape: {X_test.shape}")

    model = build_advanced_model(SEQ_LEN)
    model.summary()

    from tensorflow.keras.callbacks import EarlyStopping

    cb_es = EarlyStopping(patience=8, restore_best_weights=True)

    print("\nTraining LSTM for up to 50 epochs...")
    history = model.fit(
        X_train,
        y_train,
        validation_data=(X_test, y_test),
        epochs=50,
        batch_size=128,  # Larger batch size for faster training on large dataset
        callbacks=[cb_es],
        verbose=1,
    )

    # Evaluation
    print("\nRunning Evaluation...")
    y_pred = model.predict(X_test)

    # Rescale back to kW
    y_test_kw = y_test * scale
    y_pred_kw = y_pred.flatten() * scale

    from sklearn.metrics import mean_absolute_error, mean_squared_error

    mae = mean_absolute_error(y_test_kw, y_pred_kw)
    rmse = math.sqrt(mean_squared_error(y_test_kw, y_pred_kw))

    # Avoid zero division for MAPE
    non_zero = y_test_kw > 0
    mape = (
        np.mean(
            np.abs((y_test_kw[non_zero] - y_pred_kw[non_zero]) / y_test_kw[non_zero])
        )
        * 100
    )

    metrics = {
        "MAE_kW": round(float(mae), 4),
        "RMSE_kW": round(float(rmse), 4),
        "MAPE_pct": round(float(mape), 4),
        "ScaleFactor_kW": float(scale),
        "EpochsTrained": len(history.epoch),
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_DIR / "lstm_metrics.json", "w") as f:
        json.dump(metrics, f, indent=4)

    with open(RESULTS_DIR / "lstm_report.txt", "w") as f:
        f.write("LSTM Load Forecaster Evaluation Report\n")
        f.write("======================================\n\n")
        f.write(f"Mean Absolute Error (MAE):    {mae:.2f} kW\n")
        f.write(f"Root Mean Squared Error (RMSE): {rmse:.2f} kW\n")
        f.write(f"Mean Absolute Pct Error (MAPE): {mape:.2f}%\n\n")
        f.write(f"Scale Factor applied: {scale:.1f} kW peak\n")
        f.write(f"Total Epochs Trained: {len(history.epoch)}\n")

    print(f"\nCompleted! MAE: {mae:.2f} kW, RMSE: {rmse:.2f} kW, MAPE: {mape:.2f}%")
    print("Evaluation Metrics saved to results/ directory.")

    # Save model
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(MODEL_PATH))
    with open(SCALE_PATH, "w") as f:
        json.dump({"max_load_kw": float(scale)}, f)
    print(f"Tuned Model saved -> {MODEL_PATH}")


if __name__ == "__main__":
    tune_and_train()
