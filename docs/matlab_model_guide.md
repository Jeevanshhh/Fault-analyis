# MATLAB Simulink Model Guide for SHDN

## Overview

This guide describes the Simulink model structure for the Self-Healing Distribution Network (SHDN) and how to connect it to the Python backend.

## Model Architecture

```
Three-Phase Source (Simscape)
       |
Transmission Line Block (Pi-section model)
       |
Substation Bus (Three-Phase Transformer)
       |
Distribution Feeders
  +--------+--------+--------+
  |        |        |        |
Load A  Load B   Load C   Load D
  |
Smart Sensors (V/I Measurement)
  |
Fault Detection Subsystem
  |
AI Controller (MATLAB Function Block)
  |
Circuit Breaker Switching Logic
```

## Simulink Block List

### Power Source
- **Three-Phase Source** - `Simscape > Electrical > Specialized Power Systems > Sources`
- Parameters: 230V L-N, 50Hz, Phase angle 0/120/240

### Transmission
- **Three-Phase PI Section Line** - Models impedance per km
- Length: 10 km, R = 0.01273 Ohm/km, L = 0.9337 mH/km

### Transformer
- **Three-Phase Transformer (Two Windings)** - 11kV/415V step-down
- Rating: 500 kVA, Wye-Delta connection

### Loads
- **Three-Phase Series RLC Load** - Models consumer loads
- Bus 1-4: 500 kW, Bus 5-8: 300 kW, Bus 9-12: 150 kW

### Measurement Blocks
- **Three-Phase V-I Measurement** - Sensor at each bus
- **RMS** - Computes RMS values from instantaneous measurements
- **Scope** - Visualization in Simulink

### Fault Simulation
- **Three-Phase Fault** - Configurable: L-G, L-L, L-L-G, 3-phase
- Fault onset time: configurable (e.g. t = 0.1s)
- Fault duration: configurable (e.g. 0.05s = 3 cycles at 50Hz)

### Protection / Switching
- **Three-Phase Breaker** - At each feeder connection
- **Ideal Switch** - Sectionalizer simulation
- **Timer** - For recloser logic (trip + reclose after dead time)

### Control Logic Subsystem
```
Voltage RMS  --> Threshold Comparator
                      |
Current RMS  --> Threshold Comparator --> AND --> Fault Flag
                      |
                 Time Delay (debounce)
                      |
               Isolation Logic --> Breaker Open Signal
                      |
               Restoration Logic --> Alt Feeder Close Signal
```

## MATLAB Function Block (AI Controller)

```matlab
function [fault_flag, isolation_cmd, restore_cmd] = ai_controller(v_rms, i_rms, freq)
    % Fault detection thresholds
    V_NOM = 230;
    I_MAX = 30;
    V_DROP_THRESHOLD = 0.30; % 30% drop

    voltage_drop = (V_NOM - v_rms) / V_NOM;
    fault_flag = (voltage_drop > V_DROP_THRESHOLD) | (i_rms > I_MAX);

    % Isolation: open upstream breaker
    isolation_cmd = fault_flag;

    % Restoration: close alternate feeder (simplified)
    restore_cmd = fault_flag; % In production, call Python AI engine
end
```

## Connecting to Python Backend

### Using MATLAB Engine API for Python

```python
import matlab.engine

eng = matlab.engine.start_matlab()
eng.addpath(r'F:\Fault analyis\SHDN\simulink_model')

# Run simulation
eng.sim('shdn_grid_model', 1.0)  # 1 second simulation

# Get results
v_data = eng.evalin('base', 'v_rms_data')
i_data = eng.evalin('base', 'i_rms_data')
```

### Alternative: MAT File Exchange

1. MATLAB simulation writes results to `.mat` file
2. Python reads with `scipy.io.loadmat()`
3. Backend processes and sends to dashboard via WebSocket

```python
from scipy.io import loadmat

data = loadmat('simulation_results.mat')
voltage = data['v_rms']
current = data['i_rms']
```

## Simulation Modes

### Mode 1 - Visualization (No Simscape)
- Uses **Transfer Function** blocks to simulate power flow
- Lightweight, runs in real-time
- For dashboard demo purposes

### Mode 2 - Full Simulation (Simscape Electrical)
- Uses **Simscape Electrical / Specialized Power Systems**
- Requires Simscape licence
- Realistic EMT (Electromagnetic Transient) simulation
- Used for algorithm validation

## How to Set Up

1. Open MATLAB R2022b or later
2. Install **Simscape Electrical** toolbox
3. Open the `.slx` model file
4. Set simulation parameters: Solver = ode23tb, Step = 1e-5
5. Configure Three-Phase Fault block for desired fault type
6. Run simulation
7. Export results to Python via MAT file or MATLAB Engine API

## References

- [MathWorks: Smart Grid Solutions](https://www.mathworks.com/solutions/electrification/microgrid-smart-grid-charging-infrastructure.html)
- [Electrical Fault Detection & Classification (GitHub)](https://github.com/KingArthur000/Electrical-Fault-detection-and-classification)
- [IEEE 1547: Standard for Interconnection](https://standards.ieee.org/standard/1547-2018.html)
