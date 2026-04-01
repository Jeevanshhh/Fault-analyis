"""
SHDN -- MATLAB Simulink Connector
Provides an interface to the MATLAB Engine to run the Simulink physical model.
"""

import sys
import os
import threading
from pathlib import Path
import time

try:
    import matlab.engine
    import numpy as np
    import json
    MATLAB_AVAILABLE = True
except ImportError:
    MATLAB_AVAILABLE = False


class MATLABConnector:
    def __init__(self, model_name="SHDN_12Bus_Network"):
        self.model_name = model_name
        self.eng = None
        self._lock = threading.Lock()
        self.is_connected = False

    def connect(self) -> bool:
        """Start the MATLAB engine in the background."""
        if not MATLAB_AVAILABLE:
            print("matlabengine package not installed or MATLAB not found.")
            return False
            
        if self.is_connected:
            return True

        print("Starting MATLAB Engine... This may take a minute.")
        try:
            self.eng = matlab.engine.start_matlab()
            # Add simulink model directory to MATLAB path
            simulink_dir = str(Path(__file__).parent.parent / "simulink")
            self.eng.addpath(simulink_dir, nargout=0)
            
            # Build the model if .slx does not exist yet
            slx_path = Path(simulink_dir) / f"{self.model_name}.slx"
            if not slx_path.exists():
                print("Building Simulink model from script...")
                self.eng.eval("build_shdn_simulink", nargout=0)
            
            # Load the model into memory
            self.eng.eval(f"load_system('{self.model_name}')", nargout=0)
            self.is_connected = True
            print("Successfully connected to MATLAB Engine.")
            return True
        except Exception as e:
            print(f"Failed to connect to MATLAB: {e}")
            return False

    def inject_fault(self, fault_type: str, fault_bus: str):
        """
        Configure the Three-Phase Fault block in Simulink.
        Requires the model to have predefined fault blocks or configurable parameters.
        """
        if not self.is_connected:
            return False
            
        with self._lock:
            try:
                # Example: Set a variable in MATLAB workspace that the Simulink model uses
                # In a real model, you would configure specific block parameters using set_param
                is_ground = 1 if "ground" in fault_type else 0
                is_line = 1 if "line" in fault_type else 0
                
                self.eng.workspace['fault_active'] = 1             
                self.eng.workspace['fault_bus'] = fault_bus
                self.eng.workspace['fault_type_gnd'] = is_ground
                self.eng.workspace['fault_type_line'] = is_line
                return True
            except Exception as e:
                print(f"MATLAB fault injection error: {e}")
                return False

    def run_simulation(self, duration_s: float = 2.0) -> dict:
        """
        Run the Simulink model for a given duration.
        """
        if not self.is_connected:
            return {"error": "MATLAB not connected"}
            
        with self._lock:
            try:
                # Run the simulation
                print(f"Running Simulink model '{self.model_name}' for {duration_s}s...")
                self.eng.workspace['sim_time'] = duration_s
                
                # Execute simulation
                cmd = f"out = sim('{self.model_name}', 'StopTime', num2str(sim_time));"
                self.eng.eval(cmd, nargout=0)
                
                # Fetch results from the ToWorkspace blocks
                try:
                    # 'V_out', 'I_out', 'tout' must be configured in Simulink
                    V_out = self.eng.workspace['V_out']
                    I_out = self.eng.workspace['I_out']
                    tout = self.eng.workspace['tout']
                    
                    V_np = np.array(V_out).flatten()
                    I_np = np.array(I_out).flatten()
                    t_np = np.array(tout).flatten()
                    
                    # Downsample to avoid gigantic files
                    V_sampled = V_np[::100].tolist()
                    I_sampled = I_np[::100].tolist()
                    t_sampled = t_np[::100].tolist()
                    
                    # Save to results/matlab_outputs/
                    out_dir = Path(__file__).parent.parent / "results" / "matlab_outputs"
                    out_dir.mkdir(parents=True, exist_ok=True)
                    
                    file_path = out_dir / f"transient_sim_{int(time.time())}.json"
                    with open(file_path, 'w') as f:
                        json.dump({
                            "time": t_sampled,
                            "voltage": V_sampled,
                            "current": I_sampled,
                            "duration_s": duration_s
                        }, f)
                    
                    print(f"MATLAB data extracted and saved to {file_path}")
                except Exception as ex:
                    print(f"Warning: Could not extract V_out/I_out arrays. Ensure 'To Workspace' blocks exist in Simulink model. ({ex})")
                
                return {
                    "status": "success",
                    "duration": duration_s,
                    "model": self.model_name
                }
            except Exception as e:
                print(f"MATLAB simulation error: {e}")
                return {"error": str(e)}

    def disconnect(self):
        """Close the MATLAB engine."""
        if self.eng is not None:
            self.eng.quit()
            self.is_connected = False
            self.eng = None

matlab_connector = MATLABConnector()

if __name__ == "__main__":
    # Test script
    if matlab_connector.connect():
        matlab_connector.inject_fault("line_fault", "bus_4")
        res = matlab_connector.run_simulation(2.0)
        print("Simulation result:", res)
        matlab_connector.disconnect()
    else:
        print("MATLAB connectivity test skipped.")
