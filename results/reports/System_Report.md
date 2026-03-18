# Self-Healing Distribution Network (SHDN)
## Final System Architecture & Operational Report

This document provides a comprehensive overview of the Self-Healing Distribution Network (SHDN) project. It outlines the master workflow, individual component responsibilities, and the complete end-to-end system validation.

---

### 1. Complete System Flow (How It Works)

The SHDN architecture orchestrates multiple advanced layers—from real-time sensor ingestion to AI-driven decision making, deep execution via a physics engine, and dynamic user visualization. 

**Full System Lifecycle:**
`Sensor Data` ➔ `AI Detection` ➔ `Fault Identified` ➔ `FLISR Activated` ➔ `Isolation` ➔ `Alternate Path Calculation` ➔ `MATLAB Simulation` ➔ `Frontend Visualization` ➔ `System Restored`

---

### 2. Individual Component Flow

#### A. Datasets Layer
The foundation of the system is built on realistic simulated data.
- **Inputs:** Provides raw environmental and electrical data.
- **Components:** Sensor readings (voltage, current), weather data (lightning probability, temp, wind), and consumption loads.

#### B. AI & Machine Learning Models
- **Random Forest (RF):** Monitors incoming sensor sequences to classifying fault anomalies with >96% accuracy. It precisely detects fault types (e.g., line faults, short circuits).
- **LSTM Neural Network:** Predicts future consumer power demand to prevent cascading grid overloads and balance distribution.

#### C. FLISR Engine
The core intelligence logic: Fault Location, Isolation, and Service Restoration.
- **Finds Fault:** Locates the specific grid bus experiencing the event.
- **Isolates It:** Calculates which breakers to trip to contain the fault.
- **Restores Power:** Executes graph algorithms (BFS/Dijkstra) to locate the fastest alternate route from backup feeders.

#### D. Backend Control System (FastAPI)
The central nervous system.
- **Orchestration:** Manages API routes, state synchronization, and background threads.
- **Communication:** Serves live telemetry at 1Hz over WebSockets to the frontend.
- **Automation:** Includes an auto-trigger mechanism to automatically launch fault demo scenarios without manual injection.

#### E. Electrical Physics (MATLAB / Simulink)
The Digital Twin verification layer.
- **Simulation:** A fully modeled 12-bus 400V microgrid inside MATLAB Simulink R2025b.
- **Role:** Simulates the actual physics of the fault and validates that voltage/current transients behave correctly during isolation and restoration.

#### F. Frontend Visual Intelligence (React + Three.js)
The human-in-the-loop dashboard.
- **Visualization:** Real-time 3D rendering of the topology.
- **Dynamic States:** 
  - **Healthy:** Green nodes with smooth power flow particles.
  - **Fault:** Red nodes with rapid sparking animations.
  - **Isolation:** Grey disconnected sub-grids.
  - **Restoration:** Amber nodes with high-speed reroute particles.

---

### 3. Demo Recording & Evidence Collection Guidelines

The project is fully prepared for cinematic presentation. Evaluators will observe a flawless execution of the SHDN lifecycle via the `GridMap3D.jsx` and `SystemLogPanel.jsx` components.

**Demonstration Sequence:**
1. **Scene 1 (System Running):** The dashboard loads instantly (no blank data). The 3D grid shows healthy green nodes and stable system stats.
2. **Scene 2 (Auto Fault):** At T+15 seconds, the backend automatically triggers a line fault at `bus_4`. The node immediately flashes red, voltage plummets, and electric spark particles orbit the bus.
3. **Scene 3 (AI Response):** The System Log sequentially outputs:
   - `[timestamp] Fault detected at Bus_4`
   - `[timestamp] Running FLISR`
4. **Scene 4 (Isolation):** Breakers trip. The log outputs `[timestamp] Opening breakers` and `Isolation complete`. `bus_4` turns grey.
5. **Scene 5 (Restoration):** The backend discovers a backup feeder. `[timestamp] Alternate path found`. The backup network glows AMBER, routing power to the isolated zone.
6. **Scene 6 (Recovery):** The logs read `[timestamp] Power restored`. The network stabilizes back to normal green visual states.

**Evidence Artifacts Available:**
- This Report (`System_Report.md`)
- `AI_Model_Report.md`
- `Stress_Test_Report.md`
- `Simulink_Model_Report.md`
- Codebase on GitHub repository (Commits verified)
