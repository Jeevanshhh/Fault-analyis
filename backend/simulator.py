"""
SHDN -- Grid Simulator
Background thread that maintains live grid state, injects weather-based faults,
calls the AI engine, and streams updates via WebSocket.
"""

import threading
import time
import random
import math
import sys
import os
from datetime import datetime
from typing import Dict, List, Callable

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ai_engine"))
from flisr_engine import run_flisr
from matlab_connector import matlab_connector

# ─── Grid State ───────────────────────────────────────────────────────────────

NODES = [f"bus_{i}" for i in range(1, 13)]
SOURCE_NODE = "bus_1"

NOMINAL = {
    "voltage_v": 230.0,
    "current_a": 12.0,
    "frequency_hz": 50.0,
}

TOPOLOGY = {
    "bus_1": ["bus_2", "bus_3"],
    "bus_2": ["bus_1", "bus_4", "bus_5"],
    "bus_3": ["bus_1", "bus_6", "bus_7"],
    "bus_4": ["bus_2", "bus_8"],
    "bus_5": ["bus_2", "bus_9"],
    "bus_6": ["bus_3", "bus_10"],
    "bus_7": ["bus_3", "bus_11"],
    "bus_8": ["bus_4", "bus_12"],
    "bus_9": ["bus_5"],
    "bus_10": ["bus_6"],
    "bus_11": ["bus_7"],
    "bus_12": ["bus_8"],
}


def _make_node(node_id: str) -> dict:
    return {
        "node_id": node_id,
        "voltage_v": NOMINAL["voltage_v"] + random.gauss(0, 2),
        "current_a": NOMINAL["current_a"] + random.gauss(0, 0.5),
        "frequency_hz": NOMINAL["frequency_hz"] + random.gauss(0, 0.02),
        "power_kw": 0.0,
        "status": "healthy",
        "fault_type": None,
        "fault_severity": None,
        "load_kw": random.uniform(5, 40),
        "zone": (
            "zone_a"
            if node_id in ("bus_1", "bus_2", "bus_3", "bus_4")
            else (
                "zone_b"
                if node_id in ("bus_5", "bus_6", "bus_7")
                else "zone_c" if node_id in ("bus_8", "bus_9", "bus_10") else "zone_d"
            )
        ),
        "updated_at": datetime.utcnow().isoformat(),
    }


class GridSimulator:
    def __init__(self):
        self.nodes: Dict[str, dict] = {n: _make_node(n) for n in NODES}
        self.active_faults: List[dict] = []
        self.fault_history: List[dict] = []
        self.system_logs: List[dict] = []
        self.weather = self._gen_weather()
        self.broadcast_callbacks: List[Callable] = []
        self._lock = threading.Lock()
        self._running = False
        self._tick = 0

    # ── Logs ──────────────────────────────────────────────────────────────────

    def _add_log(self, message: str):
        with self._lock:
            ts = datetime.utcnow().strftime("%H:%M:%S")
            self.system_logs.insert(0, {"timestamp": ts, "message": message})
            if len(self.system_logs) > 50:
                self.system_logs.pop()

    # ── Weather ───────────────────────────────────────────────────────────────

    def _gen_weather(self) -> dict:
        hour = datetime.utcnow().hour
        temp = 28 + 8 * math.sin(math.pi * hour / 12)
        wind = abs(random.gauss(20, 12))
        rain = max(0, random.gauss(0, 3)) if random.random() < 0.3 else 0
        lightning = min(1.0, rain / 10 + wind / 100 + random.uniform(0, 0.2))
        return {
            "temp_c": round(temp, 1),
            "wind_kmh": round(wind, 1),
            "rain_mm": round(rain, 2),
            "lightning_risk": round(lightning, 3),
            "humidity_pct": round(min(100, 50 + rain * 5 + random.gauss(0, 5)), 1),
        }

    # ── Fault Probability (weather-based) ─────────────────────────────────────

    def _fault_probability(self) -> float:
        base = 0.005  # 0.5% per tick baseline
        w = self.weather
        if w["lightning_risk"] > 0.7:
            base *= 4
        if w["wind_kmh"] > 60:
            base *= 2
        if w["rain_mm"] > 5:
            base *= 1.5
        return min(base, 0.20)

    # ── Fault Injection ───────────────────────────────────────────────────────

    def _inject_fault(self):
        if random.random() > self._fault_probability():
            return

        # Pick a non-source node that is currently healthy
        candidates = [
            n
            for n in NODES
            if n != SOURCE_NODE and self.nodes[n]["status"] == "healthy"
        ]
        if not candidates:
            return

        # Auto-Demo System: Ensure smooth clean run for the first 15 seconds
        if self._tick < 20: 
            return

        target = random.choice(candidates)
        fault_types = [
            "line_fault",
            "ground_fault",
            "short_circuit",
            "voltage_sag",
            "overload",
        ]
        weights = [0.30, 0.20, 0.15, 0.25, 0.10]
        ftype = random.choices(fault_types, weights)[0]
        severity = random.choice(["low", "medium", "high"])

        with self._lock:
            node = self.nodes[target]
            node["status"] = "fault"
            node["fault_type"] = ftype
            node["fault_severity"] = severity
            if ftype in ("line_fault", "short_circuit"):
                node["voltage_v"] = NOMINAL["voltage_v"] * random.uniform(0.1, 0.4)
                node["current_a"] = NOMINAL["current_a"] * random.uniform(2.0, 4.0)
            elif ftype == "voltage_sag":
                node["voltage_v"] = NOMINAL["voltage_v"] * random.uniform(0.6, 0.8)
            elif ftype == "overload":
                node["current_a"] = NOMINAL["current_a"] * random.uniform(1.5, 2.5)

            event = {
                "id": f"fault_{self._tick}_{target}",
                "timestamp": datetime.utcnow().isoformat(),
                "node_id": target,
                "fault_type": ftype,
                "severity": severity,
                "weather": self.weather.copy(),
                "status": "active",
            }
            self.active_faults.append(event)
            self.fault_history.insert(0, event)
            if len(self.fault_history) > 200:
                self.fault_history.pop()

            self._add_log(f"Fault detected at {target} ({severity} {ftype})")

        # Try to execute the EMT simulation via MATLAB in parallel
        def _run_matlab_emt():
            if matlab_connector.connect():
                matlab_connector.inject_fault(ftype, target)
                res = matlab_connector.run_simulation(2.0)
                print(f"[MATLAB] Simulation finished for {target} ({ftype}): {res}")
                
        threading.Thread(target=_run_matlab_emt, daemon=True).start()

        # Phase 1: Call FLISR Engine to simulate real logic
        self._add_log("Running FLISR")
        threading.Timer(2.0, self._trigger_flisr, args=[target, event["id"]]).start()

    # ── FLISR & Restoration ───────────────────────────────────────────────────

    def _trigger_flisr(self, node_id: str, fault_id: str):
        # AI calculates isolation and restoration
        report = run_flisr(node_id)

        # Phase 2: Isolation
        iso_time = report["isolation"].get("isolation_time_s", 2)
        threading.Timer(
            iso_time, self._isolate_node, args=[node_id, fault_id, report]
        ).start()

    def _isolate_node(self, node_id: str, fault_id: str, report: dict):
        with self._lock:
            # Change status to isolated
            if self.nodes[node_id]["status"] == "fault":
                self.nodes[node_id]["status"] = "isolated"
                self.nodes[node_id]["voltage_v"] = 0.0
                self.nodes[node_id]["current_a"] = 0.0
            self._add_log(f"Opening breakers around {node_id}")
            self._add_log("Isolation complete")
            self._add_log("Searching alternate feeder")

        # Phase 3: Restoration
        rest_time = min(
            15, report["restoration"].get("estimated_restoration_time_s", 10)
        )
        threading.Timer(rest_time, self._restore_node, args=[node_id, fault_id]).start()

    def _restore_node(self, node_id: str, fault_id: str):
        with self._lock:
            node = self.nodes[node_id]
            node["status"] = "restored"
            node["voltage_v"] = NOMINAL["voltage_v"] + random.gauss(0, 1)
            node["current_a"] = NOMINAL["current_a"] + random.gauss(0, 0.3)
            node["fault_type"] = None
            node["fault_severity"] = None
            self.active_faults = [f for f in self.active_faults if f["id"] != fault_id]
            for h in self.fault_history:
                if h["id"] == fault_id:
                    h["status"] = "restored"
                    break
            self._add_log("Restoration path found")
            self._add_log(f"Power rerouted to {node_id}. System stabilized.")

        # Return to healthy after another few seconds showing it holding
        threading.Timer(5.0, self._clear_restored, args=[node_id]).start()

    def _clear_restored(self, node_id: str):
        with self._lock:
            if self.nodes[node_id]["status"] == "restored":
                self.nodes[node_id]["status"] = "healthy"

    # ── Tick ─────────────────────────────────────────────────────────────────

    def _tick_update(self):
        """Update sensor readings with small noise each tick."""
        with self._lock:
            for node in self.nodes.values():
                if node["status"] == "healthy":
                    node["voltage_v"] = NOMINAL["voltage_v"] + random.gauss(0, 2)
                    node["current_a"] = NOMINAL["current_a"] + random.gauss(0, 0.5)
                    node["frequency_hz"] = NOMINAL["frequency_hz"] + random.gauss(
                        0, 0.02
                    )
                    node["load_kw"] += random.gauss(0, 0.5)
                    node["load_kw"] = max(1, min(50, node["load_kw"]))
                node["power_kw"] = round(
                    node["voltage_v"] * node["current_a"] / 1000, 2
                )
                node["updated_at"] = datetime.utcnow().isoformat()

        # Refresh weather every 60 ticks (1 minute)
        if self._tick % 60 == 0:
            self.weather = self._gen_weather()

    def get_state(self) -> dict:
        with self._lock:
            return {
                "tick": self._tick,
                "timestamp": datetime.utcnow().isoformat(),
                "weather": self.weather.copy(),
                "nodes": list(self.nodes.values()),
                "active_faults": list(self.active_faults),
                "system_logs": list(self.system_logs),
                "stats": self._compute_stats(),
            }

    def _compute_stats(self) -> dict:
        healthy = sum(1 for n in self.nodes.values() if n["status"] == "healthy")
        total_load = sum(n["load_kw"] for n in self.nodes.values())
        avg_v = sum(n["voltage_v"] for n in self.nodes.values()) / len(self.nodes)
        avg_c = sum(n["current_a"] for n in self.nodes.values()) / len(self.nodes)
        avg_f = sum(n["frequency_hz"] for n in self.nodes.values()) / len(self.nodes)
        return {
            "healthy_nodes": healthy,
            "fault_nodes": len(NODES) - healthy,
            "total_load_kw": round(total_load, 2),
            "avg_voltage_v": round(avg_v, 2),
            "avg_current_a": round(avg_c, 2),
            "avg_frequency_hz": round(avg_f, 3),
            "active_faults": len(self.active_faults),
        }

    # ── Manual Control ────────────────────────────────────────────────────────

    def inject_fault_manual(self, node_id: str, fault_type: str) -> dict:
        if node_id not in self.nodes:
            return {"error": "Invalid node_id"}
        with self._lock:
            node = self.nodes[node_id]
            node["status"] = "fault"
            node["fault_type"] = fault_type
            node["fault_severity"] = "high"
            node["voltage_v"] = NOMINAL["voltage_v"] * 0.2
            node["current_a"] = NOMINAL["current_a"] * 3.0
            event = {
                "id": f"manual_{self._tick}_{node_id}",
                "timestamp": datetime.utcnow().isoformat(),
                "node_id": node_id,
                "fault_type": fault_type,
                "severity": "high",
                "weather": self.weather.copy(),
                "status": "active",
            }
            self.active_faults.append(event)
            self.fault_history.insert(0, event)
            self._add_log(f"Fault detected at {node_id} ({fault_type})")
            
        def _run_matlab_emt():
            if matlab_connector.connect():
                matlab_connector.inject_fault(fault_type, node_id)
                res = matlab_connector.run_simulation(2.0)
                print(f"[MATLAB] Manual simulation finished for {node_id} ({fault_type}): {res}")
                
        threading.Thread(target=_run_matlab_emt, daemon=True).start()

        # Call FLISR manually
        threading.Timer(2.0, self._trigger_flisr, args=[node_id, event["id"]]).start()
        return event

    # ── Run Loop ─────────────────────────────────────────────────────────────

    def _run(self):
        while self._running:
            self._tick += 1
            self._tick_update()
            
            # --- Auto Demo Sequence ---
            # Automatically trigger a structured fault at exactly 15 seconds
            # for the cinematic recording sequence as requested in the Master Workflow
            if self._tick == 15 and len(self.active_faults) == 0:
                self._add_log("Auto-Demo: Triggering scheduled fault")
                self.inject_fault_manual("bus_4", "line_fault")
            else:
                self._inject_fault()
                
            time.sleep(1.0)  # 1-second tick

    def start(self):
        self._running = True
        t = threading.Thread(target=self._run, daemon=True)
        t.start()

    def stop(self):
        self._running = False


# Singleton instance
simulator = GridSimulator()
