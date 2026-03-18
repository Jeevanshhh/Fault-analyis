"""
SHDN -- MATLAB Simulink Connector
Provides an interface to the MATLAB Engine to run the Simulink physical model.
"""

import sys
import os
import threading
from pathlib import Path

try:
    import matlab.engine
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
                
                # Setup out=sim(...) in MATLAB workspace
                cmd = f"out = sim('{self.model_name}', 'StopTime', num2str(sim_time));"
                self.eng.eval(cmd, nargout=0)
                
                # Fetch results from the Outport or ToWorkspace blocks
                # V_rms and I_rms arrays assuming they were logged
                # We'll return a simulated summary dict here
                
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
