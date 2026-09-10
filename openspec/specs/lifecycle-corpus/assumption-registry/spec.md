# assumption-registry Specification

## Purpose

Defines an explicit assumption registry for the foxBMS 2 lifecycle artifact corpus with validity conditions, invalidation consequences, and review status for all critical engineering assumptions.

## Requirements

### Requirement: Assumption registry structure
The corpus SHALL maintain an assumption registry (`shared/assumption-registry.json`) with fields: id, statement, rationale, affected_scope, source (source_observed|derived|synthetic), validity_conditions, invalidation_consequence, review_status.

#### Scenario: All assumptions linked to affected artifacts
- **WHEN** an assumption is created
- **THEN** affected_scope lists all artifact IDs that depend on this assumption

### Requirement: Chemistry and thermal assumptions
The corpus SHALL define ASM-001 (Li-ion chemistry 2.5V-4.2V), ASM-002 (thermal runaway >4.3V/60°C), ASM-003 (charger respects BMS limits), ASM-005 (measurement noise Gaussian sigma≤5mV).

#### Scenario: Chemistry assumption affects voltage limits
- **WHEN** ASM-001 is reviewed
- **THEN** affected_scope includes cell_voltage_max/min parameters and SOA thresholds

### Requirement: Communication and timing assumptions
The corpus SHALL define ASM-004 (AFE SPI latency <5ms), ASM-011 (FreeRTOS scheduling deterministic <2ms).

#### Scenario: SPI latency assumption affects FTTI budget
- **WHEN** ASM-004 is reviewed
- **THEN** invalidation_consequence states "FTTI budget exceeded; acquisition period must increase"

### Requirement: Hardware independence assumptions
The corpus SHALL define ASM-006 (contactor mechanical time ≤30ms), ASM-007 (SBC watchdog independent), ASM-008 (independent HW monitor feasible), ASM-012 (FRAM endurance 10^12 cycles).

#### Scenario: Contactor timing assumption affects FTTI
- **WHEN** ASM-006 is reviewed
- **THEN** invalidation_consequence states "FTTI budget exceeded; independent monitor required"

### Requirement: Sensor accuracy assumptions
The corpus SHALL define ASM-009 (current sensor ±0.5% accuracy), ASM-010 (NTC temperature ±1°C accuracy).

#### Scenario: Current sensor assumption affects SOA and power estimation
- **WHEN** ASM-009 is reviewed
- **THEN** invalidation_consequence states "SOA current limits may be inaccurate; power estimation affected"

### Requirement: Assumption review status tracking
Each assumption SHALL have review_status (draft|reviewed|accepted|challenged|invalidated) tracking its validation state.

#### Scenario: Assumptions reviewed before corpus baseline
- **WHEN** corpus baseline is created
- **THEN** all assumptions have review_status=accepted

### Requirement: Assumption traceability to artifacts
The corpus SHALL maintain traceability from assumptions to all affected artifacts via assumption_refs fields in requirements, designs, parameters, and other artifacts.

#### Scenario: Parameter references assumptions
- **WHEN** parameter registry is validated
- **THEN** each parameter's assumptions array links to assumption registry entries
