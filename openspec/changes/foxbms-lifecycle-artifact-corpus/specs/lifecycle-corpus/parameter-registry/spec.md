## Purpose

Defines a single coherent parameter registry for the foxBMS 2 lifecycle artifact corpus with units, tolerances, domains, sign conventions, timing budgets, thresholds, hysteresis, debounce, calibration, configuration selection, and assumptions.

## ADDED Requirements

### Requirement: Parameter registry structure
The corpus SHALL maintain a parameter registry (`shared/parameter-registry.json`) with fields: id, name, value, unit, tolerance, domain, sign_convention, timing_budget, thresholds (warning/derating/shutdown), hysteresis, debounce, calibration, configuration_selection, assumptions.

#### Scenario: All parameters reference assumptions
- **WHEN** a parameter is created
- **THEN** it includes assumptions array linking to assumption registry entries

### Requirement: Cell voltage parameters
The corpus SHALL define cell_voltage_max (4200mV ±1mV, warning 4150, derating 4180, shutdown 4200, hysteresis 50mV, debounce 2 counts/100ms) and cell_voltage_min (2500mV ±1mV, warning 2600, derating 2550, shutdown 2500, hysteresis 50mV, debounce 2 counts/100ms).

#### Scenario: Voltage parameters used in SOA and HW TSRs
- **WHEN** SOA config and HW TSR-001 are reviewed
- **THEN** both reference cell_voltage_max/min from parameter registry

### Requirement: Timing budget parameters
The corpus SHALL define ftti_ms (100ms), afe_acquisition_period_ms (50ms), contactor_mechanical_time_ms (30ms), independent_monitor_latency_ms (50ms), soa_debounce_count (2 counts/100ms).

#### Scenario: Timing parameters sum within FTTI
- **WHEN** timing budget is validated
- **THEN** 25+5+5+30+5 = 70ms < 100ms FTTI with 30ms margin

### Requirement: Current and temperature parameters
The corpus SHALL define pack_current_max_charge (200A ±1A, warning 180, derating 190, shutdown 200), pack_current_max_discharge (400A ±2A, warning 360, derating 380, shutdown 400), cell_temperature_max (60°C ±1°C, warning 55, derating 58, shutdown 60, hysteresis 2°C, debounce 3 counts/500ms).

#### Scenario: Current parameters used in SOA and power estimation
- **WHEN** SOA current limits and SOF trapezoid are reviewed
- **THEN** they reference pack_current_max_charge/discharge from parameter registry

### Requirement: Calibration specifications
Each parameter SHALL include calibration method, frequency, and reference standard (e.g., factory_calibration with precision_voltage_source, current_sensor_calibration with calibrated_shunt, ntc_calibration with calibrated_thermal_chamber).

#### Scenario: Calibration traceable to standards
- **WHEN** calibration is reviewed
- **THEN** method, frequency, and reference are specified for each parameter

### Requirement: Variant applicability
Each parameter SHALL specify configuration_selection listing applicable variant IDs from variant-matrix.json.

#### Scenario: Reference configuration parameters apply to VAR-REF-001
- **WHEN** parameter registry is validated
- **THEN** all parameters have configuration_selection including VAR-REF-001

## REMOVED Requirements

None - new capability.