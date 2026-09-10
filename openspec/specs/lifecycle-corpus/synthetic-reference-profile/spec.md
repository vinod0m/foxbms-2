# synthetic-reference-profile Specification

## Purpose

Defines the `synthetic_reference` profile artifacts - a complete, coherent hypothetical automotive BMS development project grounded in foxBMS, with fictional item, vehicle context, operating assumptions, selected hardware/software baseline, stakeholders, responsibilities, lifecycle, and parameter set.

## Requirements

### Requirement: Hazard analysis (synthetic_reference)
The corpus SHALL create complete hazard analyses with malfunctioning behaviors, hazardous events, operational scenarios, severity/exposure/controllability reasoning, illustrative ASIL assignments with verified methodology, safety goals, and safe/degraded states.

#### Scenario: Cell overvoltage hazard with ASIL_D assignment
- **WHEN** hazard analysis is reviewed
- **THEN** HE-01 (cell overvoltage during charging) has S3/E4/C3 = ASIL_D with rationale

### Requirement: Safety goals (synthetic_reference)
The corpus SHALL create safety goals with fault tolerant time intervals, timing budget allocations, and explicit functional safety requirement traceability.

#### Scenario: Safety goal includes timing budget
- **WHEN** safety goal is reviewed
- **THEN** it includes FTTI=100ms with allocation: AFE 25ms, SOA 5ms, contactor 30ms, margin 20ms

### Requirement: Functional safety requirements (synthetic_reference)
The corpus SHALL create forward-engineered FSRs with quantitative acceptance criteria, timing budgets, debounce rationale, and explicit assumption dependencies.

#### Scenario: FSR includes statistical debounce justification
- **WHEN** FSR-002 (SOA monitoring) is reviewed
- **THEN** debounce count=2 justified by statistical analysis (Gaussian noise sigma=5mV, false positive rate <1e-6/hr)

### Requirement: Technical safety requirements - Hardware (synthetic_reference)
The corpus SHALL create HW TSRs with timing budgets, measurement accuracy allocations, diagnostic coverage assumptions, and independence requirements.

#### Scenario: Independent HW monitor addresses FTTI violation
- **WHEN** HW TSR-004 is reviewed
- **THEN** it specifies ASIL_B independent voltage monitor with 50ms latency, parallel to main path

### Requirement: Technical safety requirements - Software (synthetic_reference)
The corpus SHALL create SW SWRs with timing budgets, task scheduling constraints, watchdog independence, and explicit assumption dependencies.

#### Scenario: SW SWR includes FreeRTOS scheduling constraints
- **WHEN** SW SWR-001 is reviewed
- **THEN** it specifies task priority, period, and worst-case execution time bounds

### Requirement: System architecture and HSI (synthetic_reference)
The corpus SHALL create a system-owned HSI/interface authority linking system, hardware, and software with electrical/logical signal definitions, timing, fault indications, and variant applicability.

#### Scenario: HSI defines SPI signal timing budgets
- **WHEN** HSI is reviewed
- **THEN** it specifies SPI_CLK max 1MHz, t_setup/t_hold, freshness <30ms

### Requirement: Parameter registry (synthetic_reference)
The corpus SHALL create a single coherent parameter registry with units, tolerances, domains, sign conventions, timing budgets, thresholds, hysteresis, debounce, calibration, configuration selection, and assumptions.

#### Scenario: Parameter used consistently across artifacts
- **WHEN** parameter cell_voltage_max is referenced
- **THEN** it has value=4200mV, tolerance ±1mV, thresholds warning=4150, derating=4180, shutdown=4200

### Requirement: Assumption registry (synthetic_reference)
The corpus SHALL create explicit assumptions with validity conditions, invalidation consequences, and review status for all critical engineering assumptions.

#### Scenario: Assumption invalidation consequence documented
- **WHEN** assumption ASM-004 (AFE SPI latency <5ms) is reviewed
- **THEN** invalidation_consequence states "FTTI budget exceeded; acquisition period must increase"

### Requirement: Safety analyses (synthetic_reference)
The corpus SHALL create FMEA, FTA, dependent failure analysis, freedom-from-interference analysis tied to identified elements, assumptions, mechanisms, requirements, and verification measures.

#### Scenario: FMEA linked to requirements and verification
- **WHEN** FMEA is reviewed
- **THEN** each failure mode references affected requirements and verification measures

### Requirement: Safety case skeleton (synthetic_reference)
The corpus SHALL create a structured safety case with claims, arguments, evidence/gap links, assumptions, defeaters, unresolved concerns, and release recommendation (never actual safety approval).

#### Scenario: Safety case includes release recommendation
- **WHEN** safety case is reviewed
- **THEN** it has release_recommendation for fictional corpus scenario with production_authorized=false

### Requirement: Management artifacts (synthetic_reference)
The corpus SHALL create project scope, safety plan, roles/RACI, fictional competence records, resource estimates, milestones, toolchain inventory, supplier management, and process records.

#### Scenario: Safety plan defines confirmation measures
- **WHEN** safety plan is reviewed
- **THEN** it specifies independence requirements for ASIL_D (separate challenge pass)
