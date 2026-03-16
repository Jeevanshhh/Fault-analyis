"""
SHDN -- Digital Twin
Simulates expected grid behavior using physics-based equations.
Compares predictions with actual simulator readings to detect anomalies early.
"""

from datetime import datetime
from typing import Dict, List


class DigitalTwin:
    """
    Physics-based representation of the grid.
    Expected values are computed from Ohm's law + load-flow approximations.
    Anomaly = |actual - expected| / expected > threshold
    """

    # Grid parameters
    NOMINAL_VOLTAGE = 230.0  # V (line-to-neutral)
    NOMINAL_FREQUENCY = 50.0  # Hz
    LINE_RESISTANCE = {  # Ohm per segment
        ("bus_1", "bus_2"): 0.05,
        ("bus_1", "bus_3"): 0.07,
        ("bus_2", "bus_4"): 0.10,
        ("bus_2", "bus_5"): 0.12,
        ("bus_3", "bus_6"): 0.09,
        ("bus_3", "bus_7"): 0.11,
        ("bus_4", "bus_8"): 0.15,
        ("bus_5", "bus_9"): 0.18,
        ("bus_6", "bus_10"): 0.14,
        ("bus_7", "bus_11"): 0.16,
        ("bus_8", "bus_12"): 0.20,
    }
    ANOMALY_THRESHOLD = 0.15  # 15% deviation triggers anomaly

    def __init__(self):
        self._expected: Dict[str, dict] = {}
        self._anomalies: List[dict] = []
        self._update_expected()

    def _update_expected(self):
        """Compute expected voltage at each node using simplified voltage-drop model."""
        v_source = self.NOMINAL_VOLTAGE
        v_map = {"bus_1": v_source}

        # BFS from source
        from collections import deque

        queue = deque(["bus_1"])
        adjacency = {
            "bus_1": ["bus_2", "bus_3"],
            "bus_2": ["bus_4", "bus_5"],
            "bus_3": ["bus_6", "bus_7"],
            "bus_4": ["bus_8"],
            "bus_5": ["bus_9"],
            "bus_6": ["bus_10"],
            "bus_7": ["bus_11"],
            "bus_8": ["bus_12"],
        }

        while queue:
            node = queue.popleft()
            children = adjacency.get(node, [])
            for child in children:
                key = (
                    (node, child)
                    if (node, child) in self.LINE_RESISTANCE
                    else (child, node)
                )
                r = self.LINE_RESISTANCE.get(key, 0.10)
                assumed_current = 12.0  # A nominal
                v_map[child] = v_map[node] - assumed_current * r
                queue.append(child)

        for node_id, v_exp in v_map.items():
            self._expected[node_id] = {
                "expected_voltage_v": round(v_exp, 3),
                "expected_current_a": 12.0,
                "expected_frequency_hz": 50.0,
                "expected_power_kw": round(v_exp * 12.0 / 1000, 3),
            }

    def compare(self, actual_nodes: List[dict]) -> dict:
        """
        Compare actual sensor readings against expected values.
        Returns anomalies with severity scores.
        """
        anomalies = []
        twin_state = []

        for node in actual_nodes:
            node_id = node["node_id"]
            exp = self._expected.get(node_id, {})
            if not exp:
                continue

            ev = exp["expected_voltage_v"]
            av = node.get("voltage_v", ev)
            v_dev = abs(av - ev) / ev if ev else 0

            ec = exp["expected_current_a"]
            ac = node.get("current_a", ec)
            c_dev = abs(ac - ec) / ec if ec else 0

            ef = exp["expected_frequency_hz"]
            af = node.get("frequency_hz", ef)
            f_dev = abs(af - ef) / ef if ef else 0

            max_dev = max(v_dev, c_dev, f_dev)
            is_anomaly = max_dev > self.ANOMALY_THRESHOLD

            twin_entry = {
                "node_id": node_id,
                **exp,
                "actual_voltage_v": round(av, 2),
                "actual_current_a": round(ac, 2),
                "actual_frequency_hz": round(af, 3),
                "voltage_deviation_pct": round(v_dev * 100, 2),
                "current_deviation_pct": round(c_dev * 100, 2),
                "frequency_deviation_pct": round(f_dev * 100, 2),
                "max_deviation_pct": round(max_dev * 100, 2),
                "anomaly_detected": is_anomaly,
            }
            twin_state.append(twin_entry)

            if is_anomaly and node.get("status") == "healthy":
                anomalies.append(
                    {
                        "node_id": node_id,
                        "deviation_pct": round(max_dev * 100, 2),
                        "predicted_fault_risk": min(1.0, round(max_dev * 4, 3)),
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

        self._anomalies = anomalies
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "twin_state": twin_state,
            "anomalies": anomalies,
            "anomaly_count": len(anomalies),
        }

    def get_expected(self, node_id: str) -> dict:
        return self._expected.get(node_id, {})

    def get_all_expected(self) -> dict:
        return self._expected

    def get_anomalies(self) -> list:
        return self._anomalies


# Singleton
digital_twin = DigitalTwin()
