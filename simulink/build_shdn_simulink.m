% MATLAB Script to Build the SHDN 12-Bus Simulink Model
% Compatible with: MATLAB R2025b + Simscape Electrical
% This script uses Specialized Power Systems (SPS) blocks from powerlib
%
% In R2025b the library is still 'powerlib' but some block paths
% have moved. This script uses try/catch to resolve the correct paths.

disp('Starting SHDN Simulink Model Generation (R2025b)...');

sys = 'SHDN_12Bus_Network';
if bdIsLoaded(sys)
    close_system(sys, 0);
end
new_system(sys);
open_system(sys);

% Set solver to ode23tb, suitable for power systems (EMT)
set_param(sys, 'Solver', 'ode23tb');
set_param(sys, 'MaxStep', '1e-4');

% ───────────────────────── Helper: find correct block path ──────────────
function blk = resolve_block(candidates)
    for k = 1:numel(candidates)
        try
            find_system(candidates{k}, 'SearchDepth', 0);
            blk = candidates{k};
            return;
        catch
        end
    end
    % Fallback: just use the first candidate and let MATLAB error with a clear message
    blk = candidates{1};
end

% ───────────────────────── Resolve block paths for R2025b ───────────────
% powergui
pgui_path = resolve_block({'powerlib/powergui', 'simscapeelectrical/powergui'});

% Three-Phase Source
src_path = resolve_block({ ...
    'powerlib/Electrical Sources/Three-Phase Source', ...
    'powerlib/Electrical Sources/Three-Phase Programmable Voltage Source'});

% Three-Phase Transformer (Two Windings)
xfmr_path = resolve_block({ ...
    'powerlib/Elements/Three-Phase Transformer (Two Windings)', ...
    'powerlib/Power Electronics/Three-Phase Transformer (Two Windings)', ...
    'ee_lib/Transformers & Gyrators/Three-Phase Transformer (Two Windings)'});

% Three-Phase PI Section Line
pi_line_path = resolve_block({ ...
    'powerlib/Elements/Three-Phase PI Section Line', ...
    'powerlib/Elements/Pi Section Line', ...
    'powerlib/Elements/Three-Phase Series RLC Branch'});

% Three-Phase Breaker
breaker_path = resolve_block({ ...
    'powerlib/Elements/Three-Phase Breaker', ...
    'powerlib/Elements/Breaker'});

% Three-Phase Fault
fault_path = resolve_block({ ...
    'powerlib/Elements/Three-Phase Fault', ...
    'powerlib/Elements/Fault'});

% V-I Measurement
vi_meas_path = resolve_block({ ...
    'powerlib/Measurements/Three-Phase V-I Measurement', ...
    'powerlib/Elements/Three-Phase V-I Measurement', ...
    'powerlib/Measurements/Voltage Measurement'});

% Three-Phase Dynamic Load
load_path = resolve_block({ ...
    'powerlib/Elements/Three-Phase Dynamic Load', ...
    'powerlib/Elements/Three-Phase Series RLC Load', ...
    'powerlib/Elements/Three-Phase Parallel RLC Load'});

fprintf('Resolved block paths for R2025b:\n');
fprintf('  powergui:    %s\n', pgui_path);
fprintf('  Source:      %s\n', src_path);
fprintf('  Transformer: %s\n', xfmr_path);
fprintf('  PI Line:     %s\n', pi_line_path);
fprintf('  Breaker:     %s\n', breaker_path);
fprintf('  Fault:       %s\n', fault_path);
fprintf('  V-I Meas:    %s\n', vi_meas_path);
fprintf('  Load:        %s\n', load_path);

% ───────────────────────── Build the model ──────────────────────────────

disp('Adding powergui block...');
add_block(pgui_path, [sys '/powergui'], 'Position', [30, 30, 100, 70]);
try
    set_param([sys '/powergui'], 'SimulationMode', 'Discrete', 'SampleTime', '1e-4');
catch
    % Some versions use different parameter names
    disp('Note: powergui parameters set to defaults.');
end

% Source / Substation
disp('Adding Three-Phase Source (Substation)...');
add_block(src_path, [sys '/Substation_Source'], ...
    'Position', [50, 150, 130, 210]);
try
    set_param([sys '/Substation_Source'], 'Voltage', '11000', 'Frequency', '50');
catch
    disp('Note: Source voltage/frequency set to defaults (may need manual adjustment).');
end

% Add a transformer to step down to 400V Distribution
disp('Adding Step-Down Transformer...');
add_block(xfmr_path, [sys '/StepDown_Transformer'], ...
    'Position', [180, 150, 260, 210]);

% Main Distribution Bus (Bus 1) — Sensor
disp('Adding Bus 1 Sensor...');
add_block(vi_meas_path, [sys '/Sensor_Bus1'], ...
    'Position', [320, 150, 360, 210]);

% Connect Source to Transformer
try
    add_line(sys, 'Substation_Source/1', 'StepDown_Transformer/1', 'autorouting', 'on');
catch
    disp('Note: Auto-connection of Source → Transformer may need manual wiring.');
end

% Define 11 Load Buses
x_start = 450;
y_pos = 150;
disp('Adding 11 Feeder Buses, Lines, Breakers, Fault blocks, and Loads...');

for i = 2:12
    bus_name = sprintf('Bus_%d', i);
    line_name = sprintf('Line_1_to_%d', i);
    fault_name = sprintf('Fault_%d', i);
    load_name = sprintf('Load_%d', i);
    sensor_name = sprintf('Sensor_%d', i);
    breaker_name = sprintf('Breaker_%d', i);

    fprintf('  Building %s...\n', bus_name);

    % Transmission Line (Pi Section or Series RLC Branch)
    add_block(pi_line_path, [sys '/' line_name], ...
        'Position', [x_start, y_pos, x_start+60, y_pos+50]);

    % V-I Measurement Sensor
    add_block(vi_meas_path, [sys '/' sensor_name], ...
        'Position', [x_start+100, y_pos, x_start+140, y_pos+50]);

    % Three-Phase Breaker for Isolation
    add_block(breaker_path, [sys '/' breaker_name], ...
        'Position', [x_start+180, y_pos, x_start+220, y_pos+50]);

    % Three-Phase Fault block for testing
    add_block(fault_path, [sys '/' fault_name], ...
        'Position', [x_start+280, y_pos+80, x_start+320, y_pos+130]);

    % Three-Phase Load
    add_block(load_path, [sys '/' load_name], ...
        'Position', [x_start+280, y_pos, x_start+320, y_pos+50]);

    % Incremental positioning for UI layout
    x_start = x_start + 400;
    if mod(i, 4) == 0
        x_start = 450;
        y_pos = y_pos + 200;
    end
end

disp('Saving Model...');
save_system(sys, fullfile(pwd, 'SHDN_12Bus_Network.slx'));
disp('Model Generation Complete! Output: SHDN_12Bus_Network.slx');
disp('All blocks placed successfully. Note: Wire connections between feeder');
disp('buses may need manual routing in the Simulink editor for full simulation.');
