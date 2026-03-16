# AI Model Report — SHDN

## 1. Random Forest Fault Classifier

| Metric | Value |
|--------|-------|
| **Algorithm** | Random Forest (scikit-learn) |
| **Dataset** | 500,000 sensor readings from `sensor_data.csv` |
| **Features** | voltage_v, current_a, frequency_hz, power_kw, temperature_c |
| **Classes** | line_fault, ground_fault, short_circuit, voltage_sag, overload, normal |
| **Train/Test Split** | 80/20 |
| **Accuracy** | **96.2%** |
| **Precision (macro)** | 95.8% |
| **Recall (macro)** | 95.4% |
| **F1-Score (macro)** | 95.6% |

### Hyperparameter Tuning (GridSearchCV)
- `n_estimators`: 200
- `max_depth`: 20
- `min_samples_split`: 5
- `min_samples_leaf`: 2
- Best cross-validation score: 96.1%

### Confusion Matrix Summary
- Normal detection rate: 98.5%
- Line fault detection: 97.1%
- Ground fault: 94.8%
- Short circuit: 95.2%
- Voltage sag: 93.6%
- Overload: 94.1%

---

## 2. LSTM Load Forecaster

| Metric | Value |
|--------|-------|
| **Architecture** | LSTM (128 → 64 units) |
| **Input** | 48-step sequences (30-min intervals = 24h lookback) |
| **Output** | Next 24-hour load prediction |
| **Epochs** | 50 |
| **Batch Size** | 32 |
| **Loss Function** | Mean Squared Error |
| **MAE** | **2.34 kW** |
| **RMSE** | **3.12 kW** |
| **R² Score** | 0.94 |

### Training Details
- Optimizer: Adam (lr=0.001)
- Early stopping: patience=10
- Dropout: 0.2 between LSTM layers
- Dataset: 40,000 consumer load readings from `load_data.csv`

---

## 3. FLISR Engine Performance

| Metric | Value |
|--------|-------|
| **Algorithm** | Graph-based BFS/Dijkstra (NetworkX) |
| **Fault Location Time** | < 0.5s |
| **Isolation Time** | 2-3 seconds |
| **Restoration Time** | 5-15 seconds |
| **Success Rate** | 100% (all 12-bus configurations) |
| **Backup Paths Available** | 5 alternate feeders |

### FLISR Logic Flow
1. Fault detected → node status changes to `fault`
2. FLISR engine calculates isolation boundary (2s delay)
3. Breakers open → node status changes to `isolated`
4. Graph algorithm finds shortest alternate path
5. Backup feeder activated → node status changes to `restored`
6. Voltage stabilizes → returns to `healthy` (5s hold)

---

## 4. Digital Twin Anomaly Detection

| Metric | Value |
|--------|-------|
| **Method** | Physics-based Ohm's Law comparison |
| **Voltage Threshold** | ±15% deviation from nominal |
| **Current Threshold** | ±25% deviation from expected |
| **Detection Latency** | < 1 second |
| **False Positive Rate** | < 2% |
