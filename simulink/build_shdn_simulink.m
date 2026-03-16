% MATLAB Script to Programmatically Build the SHDN 12-Bus Simulink Model
% This script uses the set_param and add_block functions to generate an .slx model.
% Requirements: MATLAB R2022b or later + Simscape Electrical

disp('Starting SHDN Simulink Model Generation...');

sys = 'SHDN_12Bus_Network';
if bdIsLoaded(sys)
    close_system(sys, 0);
end
new_system(sys);
open_system(sys);

% Set solver to ode23tb, suitable for power systems (EMT)
set_param(sys, 'Solver', 'ode23tb');
set_param(sys, 'MaxStep', '1e-4');

disp('Adding powergui block...');
add_block('powerlib/powergui', [sys '/powergui'], 'Position', [30, 30, 100, 70]);
set_param([sys '/powergui'], 'SimulationMode', 'Discrete', 'SampleTime', '1e-4');

% Source / Substation
disp('Adding Three-Phase Source (Substation)...');
add_block('powerlib/Electrical Sources/Three-Phase Source', [sys '/Substation_Source'], ...
    'Position', [50, 150, 130, 210]);
set_param([sys '/Substation_Source'], 'Voltage', '11000', 'Frequency', '50');

% Add a transformer to step down to 400V Distribution
add_block('powerlib/Elements/Three-Phase Transformer (Two Windings)', ...
    [sys '/StepDown_Transformer'], ...
    'Position', [180, 150, 260, 210]);

% Main Distribution Bus (Bus 1)
add_block('powerlib/Elements/Three-Phase V-I Measurement', [sys '/Sensor_Bus1'], ...
    'Position', [320, 150, 360, 210]);

% Connect Source to Transformer, Transformer to Bus 1
add_line(sys, 'Substation_Source/1', 'StepDown_Transformer/1', 'autorouting', 'on');
add_line(sys, 'Substation_Source/2', 'StepDown_Transformer/2', 'autorouting', 'on');
add_line(sys, 'Substation_Source/3', 'StepDown_Transformer/3', 'autorouting', 'on');
% Note: Connecting exactly via port handles is more robust, but this script 
% provides the scaffold for the user's simulation.

% Define 11 Load Buses
x_start = 450;
y_pos = 150;
disp('Adding 11 Feeder Buses, Lines, and Fault blocks...');

for i = 2:12
    bus_name = sprintf('Bus_%d', i);
    line_name = sprintf('Line_1_to_%d', i);
    fault_name = sprintf('Fault_%d', i);
    load_name = sprintf('Load_%d', i);
    
    % Transmission Line (Pi Section)
    add_block('powerlib/Elements/Three-Phase PI Section Line', [sys '/' line_name], ...
        'Position', [x_start, y_pos, x_start+60, y_pos+50]);
    set_param([sys '/' line_name], 'Length', '2', 'Resistances', '[0.01273]', 'Inductances', '[0.9337e-3]');
    
    % V-I Measurement Sensor
    sensor_name = sprintf('Sensor_%d', i);
    add_block('powerlib/Elements/Three-Phase V-I Measurement', [sys '/' sensor_name], ...
        'Position', [x_start+100, y_pos, x_start+140, y_pos+50]);
        
    % Three-Phase Breaker for Isolation
    breaker_name = sprintf('Breaker_%d', i);
    add_block('powerlib/Elements/Three-Phase Breaker', [sys '/' breaker_name], ...
        'Position', [x_start+180, y_pos, x_start+220, y_pos+50]);
    
    % Three-Phase Fault block for testing
    add_block('powerlib/Elements/Three-Phase Fault', [sys '/' fault_name], ...
        'Position', [x_start+280, y_pos+80, x_start+320, y_pos+130]);
        
    % Three-Phase Dynamic Load
    add_block('powerlib/Elements/Three-Phase Dynamic Load', [sys '/' load_name], ...
        'Position', [x_start+280, y_pos, x_start+320, y_pos+50]);
    set_param([sys '/' load_name], 'ActivePower', num2str(randi([100 500]) * 1000)); % random 100-500kW load
    
    % Incremental positioning for UI layout
    x_start = x_start + 400;
    if mod(i, 4) == 0
        x_start = 450;
        y_pos = y_pos + 200;
    end
end

disp('Saving Model...');
save_system(sys, 'SHDN_12Bus_Network.slx');
disp('Model Generation Complete! Output: SHDN_12Bus_Network.slx');
