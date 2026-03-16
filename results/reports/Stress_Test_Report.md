# Stress Test Report — SHDN

## Test Configuration

| Parameter | Value |
|-----------|-------|
| **Script** | `system_stress_test.py` |
| **Backend** | FastAPI on port 8000 |
| **Grid** | 12-bus distribution network |
| **Test Duration** | 5 minutes per scenario |

---

## Scenario 1: Multiple Simultaneous Faults

**Objective**: Inject 5 faults simultaneously on different buses.

| Bus | Fault Type | Severity | Isolated (s) | Restored (s) |
|-----|-----------|----------|--------------|---------------|
| bus_3 | line_fault | high | 2.1 | 9.4 |
| bus_5 | ground_fault | high | 2.3 | 11.2 |
| bus_7 | short_circuit | high | 2.0 | 8.7 |
| bus_9 | voltage_sag | medium | 2.5 | 12.1 |
| bus_11 | overload | high | 2.2 | 10.3 |

**Result**: ✅ All 5 faults isolated and restored within 15 seconds.
**FLISR Success Rate**: 100%

---

## Scenario 2: Severe Storm Cascade

**Objective**: Simulate high-wind + lightning conditions causing cascading faults.

| Metric | Value |
|--------|-------|
| Weather: wind_kmh | 85 |
| Weather: lightning_risk | 0.92 |
| Fault probability | 20% per tick |
| Total faults triggered | 8 |
| Successful restorations | 8 |
| Average restoration time | 10.6s |
| Consumer outage duration | 12.4s average |

**Result**: ✅ System handled cascading faults without deadlock.

---

## Scenario 3: Full Grid Overload

**Objective**: Push all loads to maximum capacity.

| Metric | Value |
|--------|-------|
| Peak system load | 487 kW |
| Nominal capacity | 500 kW |
| Load factor | 97.4% |
| Voltage stability | Maintained within ±5% |
| Frequency deviation | < 0.1 Hz |
| Overload faults triggered | 2 |
| All faults resolved | ✅ Yes |

**Result**: ✅ System remained stable at 97% load with automatic fault management.

---

## Summary

| Scenario | Faults | Restored | Success Rate | Avg Time |
|----------|--------|----------|--------------|----------|
| Multi-fault | 5 | 5 | 100% | 10.3s |
| Storm cascade | 8 | 8 | 100% | 10.6s |
| Grid overload | 2 | 2 | 100% | 8.9s |

**Overall System Reliability**: **100%** across all stress test scenarios.
