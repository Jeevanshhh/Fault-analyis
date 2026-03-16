"""
SHDN -- System Stress Test Runner

Runs 3 Scenarios against the live Backend API:
1. Scenario 1: Severe Storm (Multiple High Severity Faults)
2. Scenario 2: Overload Demand (High Load Injection)
3. Scenario 3: Multiple Simultaneous Faults (bus_4, bus_7, bus_9)
Saves results and response times to results folder.
"""
import time
import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000"
RESULTS_DIR = Path(__file__).parent / "results"

def print_and_save(msg, log_lines):
    print(msg)
    log_lines.append(msg)

def wait_for_restoration(node_id, log_lines, max_wait=20):
    start = time.time()
    while time.time() - start < max_wait:
        resp = requests.get(f"{BASE_URL}/health").json()
        if resp.get("active_faults") == 0:
            print_and_save(f"  [SUCCESS] {node_id} Restored successfully in {round(time.time() - start, 2)}s", log_lines)
            return True
        time.sleep(1)
    print_and_save(f"  [TIMEOUT] {node_id} Failed to restore within {max_wait}s", log_lines)
    return False

def run_stress_tests():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = RESULTS_DIR / "stress_test_report.txt"
    logs = [
        "=========================================",
        "      SHDN SYSTEM STRESS TEST LOG        ",
        "=========================================\n"
    ]
    
    # Wait for backend health
    try:
        requests.get(f"{BASE_URL}/health")
    except:
        print("Backend server is not running on port 8000. Start it first.")
        return

    print_and_save("Starting Stress Tests...", logs)

    # SECNARIO 3 (User requested: bus_4, bus_7, bus_9 test)
    print_and_save("\n[SCENARIO 3] Multiple Simultaneous Faults (bus_4, bus_7, bus_9)", logs)
    
    nodes_to_fault = ["bus_4", "bus_7", "bus_9"]
    for n in nodes_to_fault:
        resp = requests.post(f"{BASE_URL}/faults/inject", json={"node_id": n, "fault_type": "line_fault"})
        print_and_save(f"  Injecting fault at {n}: {resp.status_code}", logs)
        time.sleep(0.5)
        
    print_and_save("  Waiting for algorithms to process restorations...", logs)
    
    # Check restoration status over 30 seconds
    start = time.time()
    all_restored = False
    while time.time() - start < 30:
        resp = requests.get(f"{BASE_URL}/health").json()
        active = resp.get("active_faults")
        if active == 0:
            all_restored = True
            break
        print_and_save(f"  ... active faults remaining: {active}", logs)
        time.sleep(2)
        
    if all_restored:
        print_and_save(f"  [SUCCESS] All simultaneous faults restored in {round(time.time() - start, 2)}s", logs)
    else:
        print_and_save(f"  [WARNING] Multiple simultaneous faults overloaded the 30s timeout.", logs)


    # SCENARIO 2 (Overload)
    print_and_save("\n[SCENARIO 2] Extreme Grid Overload", logs)
    resp = requests.post(f"{BASE_URL}/faults/inject", json={"node_id": "bus_2", "fault_type": "overload"})
    print_and_save(f"  Injecting Overload at Substation Feeder (bus_2): {resp.status_code}", logs)
    
    time.sleep(2)
    stats = requests.get(f"{BASE_URL}/grid/stats").json()
    print_and_save(f"  Grid Stats -> Current: {stats.get('avg_current_a')}A, Load: {stats.get('total_load_kw')}kW", logs)
    
    wait_for_restoration("bus_2", logs, max_wait=30)


    # SCENARIO 1 (Severe Storm / Lightning)
    print_and_save("\n[SCENARIO 1] Severe Storm Fault Cascade", logs)
    print_and_save("  Injecting rapid random faults simulating lightning strikes...", logs)
    import random
    nodes = [f"bus_{i}" for i in range(1, 13)]
    for i in range(5):
        n = random.choice(nodes)
        requests.post(f"{BASE_URL}/faults/inject", json={"node_id": n, "fault_type": "short_circuit"})
        print_and_save(f"  Lightning strike at {n}", logs)
        time.sleep(1)

    print_and_save("  Observing storm cascade...", logs)
    time.sleep(5)
    stats = requests.get(f"{BASE_URL}/health").json()
    print_and_save(f"  Active Faults mid-storm: {stats.get('active_faults')}", logs)
    
    start = time.time()
    while time.time() - start < 45:
        resp = requests.get(f"{BASE_URL}/health").json()
        if resp.get("active_faults") == 0:
            print_and_save(f"  [SUCCESS] Storm cascade mitigated and restored in {round(time.time() - start, 2)}s", logs)
            break
        time.sleep(3)


    print_and_save("\n=========================================", logs)
    print_and_save("  Stress Test Suite Completed", logs)
    
    with open(log_file, "w") as f:
        f.write("\n".join(logs))
        
if __name__ == "__main__":
    run_stress_tests()
