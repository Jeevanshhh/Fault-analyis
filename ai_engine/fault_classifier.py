"""
SHDN -- Fault Classifier
Random Forest model to classify 6 fault types from engineered grid features.
"""

import joblib
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
import sys

sys.path.insert(0, str(Path(__file__).parent))
from data_processor import get_train_test, FEATURE_COLS

MODEL_PATH = Path(__file__).parent / "models" / "fault_classifier.pkl"
ENCODER_PATH = Path(__file__).parent / "models" / "fault_encoder.pkl"


def train():
    print("Loading and preparing data ...")
    X_train, X_test, y_train, y_test = get_train_test()

    print(f"Training RandomForest on {X_train.shape[0]:,} samples ...")
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=15,
        min_samples_leaf=5,
        n_jobs=-1,
        random_state=42,
        class_weight="balanced",
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"\nAccuracy: {acc:.4f}")
    print(classification_report(y_test, y_pred, target_names=["Normal", "Fault"]))

    # Feature importances
    importances = sorted(
        zip(FEATURE_COLS, model.feature_importances_), key=lambda x: -x[1]
    )
    print("\nTop feature importances:")
    for feat, imp in importances[:5]:
        print(f"  {feat}: {imp:.4f}")

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"\nModel saved -> {MODEL_PATH}")
    return model


def load_model():
    if not MODEL_PATH.exists():
        print("Model not found, training now ...")
        return train()
    return joblib.load(MODEL_PATH)


def predict(features: dict) -> dict:
    """
    features: dict with keys matching FEATURE_COLS.
    Returns: {fault_detected: bool, probability: float, confidence: float}
    """
    model = load_model()
    x = np.array([[features.get(f, 0.0) for f in FEATURE_COLS]])
    proba = model.predict_proba(x)[0]
    fault_prob = proba[1] if len(proba) > 1 else proba[0]
    pred = int(model.predict(x)[0])
    return {
        "fault_detected": bool(pred),
        "fault_probability": round(float(fault_prob), 4),
        "confidence": round(float(max(proba)), 4),
        "raw_probabilities": proba.tolist(),
    }


if __name__ == "__main__":
    train()
