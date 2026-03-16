# Simulink Model Report — SHDN

## Model Overview

| Parameter | Value |
|-----------|-------|
| **Model Name** | SHDN_12Bus_Network |
| **File** | `simulink/build_shdn_simulink.m` |
| **Solver** | ode23tb (EMT-suitable) |
| **Max Step Size** | 1e-4 s |
| **Simulation Mode** | Discrete (Ts = 1e-4) |
| **MATLAB Version** | R2022b or later |
| **Toolbox Required** | Simscape Electrical |

---

## Network Architecture

```
Three-Phase Source (11kV, 50Hz)
        │
Step-Down Transformer (11kV → 415V, 500 kVA)
        │
   Main Bus (Bus 1) ──── Sensor_Bus1
        │
   ┌────┴────┐
   │         │
 Bus_2     Bus_3
   │         │
 ┌─┴─┐   ┌──┴──┐
Bus4 Bus5 Bus6 Bus7
 │    │    │    │
Bus8 Bus9 Bus10 Bus11
 │
Bus12
```

---

## Simulink Block Inventory

| Block Type | Count | Purpose |
|------------|-------|---------|
| Three-Phase Source | 1 | Substation power supply |
| Three-Phase Transformer | 1 | 11kV → 415V step-down |
| Three-Phase PI Section Line | 11 | Transmission lines (2 km each) |
| Three-Phase V-I Measurement | 12 | Voltage/current sensors per bus |
| Three-Phase Breaker | 11 | Circuit isolation switches |
| Three-Phase Fault | 11 | Fault injection blocks |
| Three-Phase Dynamic Load | 11 | Consumer loads (100-500 kW) |
| powergui | 1 | Simulation solver configuration |

**Total blocks**: 59

---

## Line Parameters

| Parameter | Value |
|-----------|-------|
| Line length | 2 km per segment |
| Resistance | 0.01273 Ω/km |
| Inductance | 0.9337 mH/km |

---

## Fault Configuration

Each bus (2-12) has a configurable Three-Phase Fault block:

| Fault Type | Configuration |
|------------|---------------|
| Line-to-Ground (L-G) | Single phase shorted to ground |
| Line-to-Line (L-L) | Two phases shorted |
| Line-Line-Ground (L-L-G) | Two phases + ground |
| Three-Phase | All three phases shorted |

---

## Python Integration

### MATLAB Engine API (Primary)
```python
import matlab.engine
eng = matlab.engine.start_matlab()
eng.addpath('F:/Fault analyis/SHDN/simulink')
eng.sim('SHDN_12Bus_Network', 2.0)
```

### MAT File Exchange (Alternative)
```python
from scipy.io import loadmat
data = loadmat('simulation_results.mat')
voltage = data['v_rms']
current = data['i_rms']
```

---

## AI Controller (MATLAB Function Block)

```matlab
function [fault_flag, isolation_cmd, restore_cmd] = ai_controller(v_rms, i_rms, freq)
    V_NOM = 230;
    I_MAX = 30;
    V_DROP_THRESHOLD = 0.30;
    voltage_drop = (V_NOM - v_rms) / V_NOM;
    fault_flag = (voltage_drop > V_DROP_THRESHOLD) | (i_rms > I_MAX);
    isolation_cmd = fault_flag;
    restore_cmd = fault_flag;
end
```

---

## Integration with Backend

The `backend/matlab_connector.py` provides:
1. **connect()**: Starts MATLAB Engine and loads the Simulink model
2. **inject_fault()**: Configures fault parameters in MATLAB workspace
3. **run_simulation()**: Executes the EMT simulation for a specified duration
4. **disconnect()**: Terminates the MATLAB Engine

Every fault event in the Python simulator triggers an asynchronous MATLAB simulation in parallel with the FLISR algorithm.
