# as-is-profile Specification

## Purpose

Defines the `as_is` profile artifacts - a faithful reconstruction of what the pinned foxBMS 2 sources (commit 308028fb, v1.11.0) demonstrate, including observed behavior, existing artifacts/tests, justified inferences, evidence gaps, contradictions, and proposed changes.

## Requirements

### Requirement: Safety hazard analysis (as_is)
The corpus SHALL create hazard analyses derived from observed foxBMS behavior, labeled as reconstructed behavior descriptions (not historical approved specifications), with explicit evidence gaps and contradictions preserved.

#### Scenario: Cell voltage hazard back-inferred from SOA implementation
- **WHEN** hazard analysis is reviewed
- **THEN** it references SOA implementation (soa.c) as source evidence with origin=derived

### Requirement: Safety goals (as_is)
The corpus SHALL create safety goals back-inferred from observed safety mechanisms, with ASIL assignments based on available methodology where available.

#### Scenario: Safety goal ASIL derived from observed mechanisms
- **WHEN** safety goal is reviewed
- **THEN** it has origin=derived and cites SOA, contactor, diagnostic implementations as premises

### Requirement: Functional safety requirements (as_is)
The corpus SHALL create FSRs back-inferred from observed foxBMS safety functions (AFE acquisition, SOA monitoring, contactor control, diagnostics), labeled as reconstructed behavior descriptions.

#### Scenario: FSRs reference actual source code
- **WHEN** FSR is reviewed
- **THEN** source_refs point to actual foxBMS source files (soa.c, contactor.c, diag.c) with origin=source_observed

### Requirement: Technical safety requirements - Hardware (as_is)
The corpus SHALL create HW TSRs derived from observed hardware capabilities (AFE accuracy from datasheets, isoSPI integrity, contactor driver timing) with explicit gaps where production evidence is unavailable.

#### Scenario: HW TSRs cite datasheets as source
- **WHEN** HW TSR is reviewed
- **THEN** it has origin=derived with datasheet and driver config as premises

### Requirement: Technical safety requirements - Software (as_is)
The corpus SHALL create SW SWRs back-inferred from observed software implementation (AFE driver, SOA module, contactor state machine, diagnostic framework).

#### Scenario: SW SWRs reference actual implementation
- **WHEN** SW SWR is reviewed
- **THEN** it has origin=source_observed with implementation_mapping to actual source symbols

### Requirement: Software architecture and detailed design (as_is)
The corpus SHALL extract software designs from actual source code (AFE driver state machine, SOA limit checking, contactor state machine) with implementation_status: implemented.

#### Scenario: Designs map to actual source symbols
- **WHEN** design is reviewed
- **THEN** implementation_mapping lists actual source files and symbols with status=implemented

### Requirement: Verification measures (as_is)
The corpus SHALL map existing unit tests (120 Unity/CMock tests) to requirements with execution_kind=actual_host_run and oracle_basis=source_grounded.

#### Scenario: Unit tests linked to back-inferred requirements
- **WHEN** verification measure is reviewed
- **THEN** it references actual test files in tests/unit/ with execution records

### Requirement: Evidence gaps and contradictions preserved
The corpus SHALL explicitly record where foxBMS evidence is missing (e.g., no system qualification tests, no HW FMEDA, no calibration procedures) and preserve source contradictions as gaps in as_is.

#### Scenario: Missing evidence recorded as gaps
- **WHEN** gap analysis runs
- **THEN** missing work products are listed with rationale and no synthetic substitution
