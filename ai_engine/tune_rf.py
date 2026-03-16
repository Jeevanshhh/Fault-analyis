"""
SHDN -- Tune Random Forest Classifier
Tunes the Random Forest using GridSearchCV and generates evaluation metrics.
Saves metrics and confusion matrix to the results folder.
"""

import sys
from pathlib import Path
import json

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    precision_score,
    recall_score,
)
import joblib

sys.path.insert(0, str(Path(__file__).parent))
from data_processor import get_train_test

RESULTS_DIR = Path(__file__).parent.parent / "results"
MODEL_PATH = Path(__file__).parent / "models" / "fault_classifier.pkl"


def tune_and_train():
    print("Loading scaled dataset (this may take a moment) ...")
    X_train, X_test, y_train, y_test = get_train_test(test_size=0.2)
    print(f"Dataset loaded. Train shape: {X_train.shape}, Test shape: {X_test.shape}")

    # Use a smaller subset for grid search to save time if dataset is huge,
    # but here we'll use a subset of 50k samples for the grid search itself.
    search_size = min(50000, X_train.shape[0])
    indices = np.random.choice(X_train.shape[0], search_size, replace=False)
    X_search, y_search = X_train[indices], y_train[indices]

    param_grid = {
        "n_estimators": [200, 300],
        "max_depth": [15, 25],
        "min_samples_split": [2, 5],
    }

    print("Starting GridSearchCV on Random Forest...")
    rf = RandomForestClassifier(random_state=42, class_weight="balanced", n_jobs=-1)
    grid_search = GridSearchCV(
        estimator=rf,
        param_grid=param_grid,
        cv=3,
        scoring="f1_macro",
        verbose=2,
        n_jobs=-1,
    )

    grid_search.fit(X_search, y_search)

    print(f"\nBest parameters found: {grid_search.best_params_}")

    # Train final model on full train set with best params
    print("Training final model on full training set...")
    best_model = grid_search.best_estimator_
    best_model.fit(X_train, y_train)

    # Evaluation
    print("Evaluating final model on test set...")
    y_pred = best_model.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, average="macro", zero_division=0)
    rec = recall_score(y_test, y_pred, average="macro", zero_division=0)
    cm = confusion_matrix(y_test, y_pred)
    report = classification_report(y_test, y_pred, target_names=["Normal", "Fault"])

    # Output metrics
    metrics = {
        "Accuracy": round(acc, 4),
        "Precision (Macro)": round(prec, 4),
        "Recall (Macro)": round(rec, 4),
        "Best_Params": grid_search.best_params_,
        "Confusion_Matrix": cm.tolist(),
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_DIR / "rf_metrics.json", "w") as f:
        json.dump(metrics, f, indent=4)

    with open(RESULTS_DIR / "rf_report.txt", "w") as f:
        f.write("Random Forest Evaluation Report\n")
        f.write("===============================\n\n")
        f.write(f"Accuracy:  {acc:.4f}\n")
        f.write(f"Precision: {prec:.4f}\n")
        f.write(f"Recall:    {rec:.4f}\n\n")
        f.write("Classification Report:\n")
        f.write(report)
        f.write("\n\nConfusion Matrix:\n")
        f.write(np.array2string(cm))

    print("\nEvaluation Metrics saved to results/ directory.")
    print(report)

    # Save model
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_model, MODEL_PATH)
    print(f"Tuned Model saved -> {MODEL_PATH}")


if __name__ == "__main__":
    tune_and_train()
