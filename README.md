# Self-Healing Distribution Network (SHDN) ⚡

![SHDN Architecture](https://img.shields.io/badge/Architecture-Hybrid%20AI%2BPhysics-00d4ff)
![MATLAB](https://img.shields.io/badge/MATLAB-R2025b-orange)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688)
![React](https://img.shields.io/badge/React-Frontend-61dafb)

The **Self-Healing Distribution Network (SHDN)** is an intelligent, real-time microgrid simulation and control platform. It demonstrates the complete lifecycle of a smart grid experiencing a critical fault, autonomously detecting the anomaly using AI, mathematically determining an isolation/restoration path (FLISR), and validating the physics in a MATLAB Simulink digital twin.

This project delivers a state-of-the-art "movie-style" live dashboard to strictly visualize the timeline of: **Healthy ➔ Fault ➔ Isolation ➔ Restoration**.

---

## 🚀 Key Features

### 1. Hybrid AI + Physics Engine
- **Random Forest (RF) & LSTM Models**: AI models trained to predict fault risks based on sensor telemetry and extreme weather data (lightning, wind, rain) and forecast network loads.
- **FLISR Engine**: Advanced graph-routing algorithms (BFS/Dijkstra) instantly compute the exact breakers to trip for isolation, and the optimal backup feeder paths for restoration.
- **MATLAB Real-Time Integration**: The Python backend transparently controls a MATLAB Engine instance, injecting the exact fault into an intricately designed 12-Bus 400V Simulink model. It extracts high-frequency Electromagnetics Transients (EMT) arrays (`V_out`, `I_out`) for authoritative engineering proof.

### 2. High-Performance Dashboard (React + WebSockets)
- **3D Grid Topology**: Live rendering (Three.js/React Three Fiber) of the microgrid displaying smooth power flows, localized fault flashes/sparks, and dynamic line colorations (Green/Red/Grey/Amber).
- **Dual-Layer Visualization Sysyem**:
  - *Main Demo Graph*: A low-frequency (1Hz) React Recharts timeline tracing macrosystem Voltage drops, Current spikes, and color-coded state tracking.
  - *Underlying Physics Data*: Downsampled EMT data natively gathered into `/results/` for rigid technical reporting.
- **Report Generator**: 1-click generation of Markdown incident reports detailing the precise latency, location, AI predictions, and restoration paths of individual faults.

---

## 📂 Project Structure

```text
SHDN/
├── ai_engine/          # Random Forest & LSTM training logic + FLISR routing algorithm
├── backend/            # FastAPI centralized server + State Machine (simulator.py)
├── frontend/           # React / Tailwind CSS / Three.js live dashboard
├── simulink/           # MATLAB R2025b 12-Bus Microgrid model (.slx) & builder scripts
└── results/            # Automated technical incident reports and transient outputs
```

---

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.9+
- Node.js & npm (v18+)
- MATLAB R2025b (with *Simscape Electrical* and *Simulink* toolboxes)
- MATLAB Engine API for Python (`pip install matlabengine`)

### 1. Start the Backend (FastAPI)
The backend coordinates the AI, the MATLAB physics, and emits the 1Hz WebSocket pulse.
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```
> **Note:** The backend contains a 15-second Auto-Run Demo Mode triggering a cascading fault automatically on startup.

### 2. Start the Frontend (React / Vite)
```bash
cd frontend
npm install
npm run dev
```

### 3. MATLAB Configuration (Optional but Recommended)
Ensure your `MATLAB` path is configured correctly in your system environment variables. The `matlab_connector.py` will automatically attempt to open MATLAB in the background and construct the `.slx` model if it does not already exist.

---

## 🎬 The Demonstration Flow
1. Load the UI (`localhost:5173`). The Grid displays as **Healthy (Green)** with smooth UI graphs.
2. At T+15 seconds, the auto-run feature triggers a **Line Fault** on Bus 4.
3. The UI flashes **Red**, the analytical timeline graph plunges voltage and spikes current.
4. The system logs announce the execution of **FLISR**.
5. Breakers trigger. The faulted section turns **Grey (Isolated)**.
6. The routing engine succeeds. A backup path dynamically routes over the grid turning **Amber (Restoration)**.
7. You may click `Download Report` in the UI to collect the physics and AI evidence.

---

*Designed and engineered as a comprehensive solution for modern, self-healing smart grids.*
