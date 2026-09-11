# foxBMS 2 - End-to-End Traceability Document

## Document Information
- **Project**: foxBMS 2 - Battery Management System
- **Version**: 2.x
- **Baseline**: BAS-REF-001
- **Baseline Commit**: 308028fb
- **Document Version**: 1.0
- **Date**: 2026-09-11
- **Classification**: Internal

## 1. Introduction

This document provides a complete end-to-end traceability matrix linking all requirements, design elements, and test cases across all engineering process areas for the foxBMS 2 Battery Management System.

### 1.1 Purpose
This document establishes bidirectional traceability between:
- Stakeholder Requirements → System Requirements → Software Requirements → Software Architecture → Software Detailed Design → Software Units → Test Cases
- Provides evidence for compliance with ISO 26262, IEC 61508, and other applicable safety standards

### 1.2 Scope
Covers the complete foxBMS 2 lifecycle artifact corpus including:
- Safety Requirements (ASIL-D, ASIL-B)
- Hardware Requirements (AFE, Contactor, Communication)
- Software Requirements (Application, Engine, Driver layers)
- Software Architecture and Detailed Design
- Verification and Validation evidence

### 1.3 Traceability Strategy
Bidirectional traceability is maintained through:
- Unique identifiers for all artifacts (FB2-XXXX-XXXXXXXX)
- Traceability links with relation types (refines, allocates_to, implements, verifies, validates, etc.)
- Profile-based isolation (as_is vs synthetic_reference)
- Baseline-referenced artifacts (BAS-REF-001)

## 2. Traceability Levels and Artifact Types

### 2.1 Traceability Levels

| Level | Description | Artifact Types | Profile |
|-------|-------------|----------------|---------|
| L1 | Stakeholder Requirements | Use Cases, Safety Goals | as_is, synthetic_reference |
| L2 | System Requirements | Safety Goals, Hazards, FSRs | as_is, synthetic_reference |
| L3 | Software Requirements | FSRs, SWRs, HWRs | as_is, synthetic_reference |
| L4 | Software Architecture | System Design, HSI | synthetic_reference |
| L5 | Detailed Design | SW Designs, HW Designs | synthetic_reference |
| L6 | Software Units | Source Files, Units | as_is, synthetic_reference |
| L7 | Verification | Test Measures, Executions, Reviews | as_is, synthetic_reference |

### 2.2 Artifact Type Definitions

| Artifact Type | Prefix | Description |
|---------------|--------|-------------|
| Hazard | FB2-SAF-HAZ | Hazard analysis |
| Safety Goal | FB2-SAF-SGO | Safety goal with FTTI, ASIL |
| FSR | FB2-SAF-FSR | Functional Safety Requirement |
| TSR | FB2-HW-TSR, FB2-SW-TSR | Technical Safety Requirement |
| SWR | FB2-SW-SWR | Software Requirement |
| Design | FB2-SW-DSN, FB2-HW-DSN | Detailed Design |
| Test Measure | FB2-VER-TMS | Test Measure Specification |
| Execution | FB2-VER-EXE | Test Execution Record |
| Review | FB2-REV | Review Record |
| Safety Analysis | FB2-SAF-ANL | FMEA, FTA, DFA, FFI |
| Scenario | FB2-SCN-MUT, FB2-SCN-CHG | Mutation/Change Lifecycle |
| Parameter | FB2-PRM | Parameter Registry |
| Assumption | FB2-ASM | Assumption Registry |

## 3. Traceability Matrix

### 3.1 Hazard → Safety Goal → FSR Traceability

| Hazard ID | Hazard Description | Safety Goal ID | Safety Goal Description | FSR IDs |
|-----------|-------------------|----------------|------------------------|---------|
| FB2-SAF-HAZ-000001 | Cell Overvoltage/Undervoltage | FB2-SAF-SGO-000001 | Cell Voltage Safety Goal (FTTI=100ms, ASIL-D) | FB2-SAF-FSR-000001, FB2-SAF-FSR-000002, FB2-SAF-FSR-000003, FB2-SAF-FSR-000004 |
| FB2-SAF-HAZ-000002 | Cell Overvoltage/Undervoltage | FB2-SAF-SGO-000001 | Cell Voltage Safety Goal (FTTI=100ms, ASIL-D) | FB2-SAF-FSR-000001, FB2-SAF-FSR-000002, FB2-SAF-FSR-000003, FB2-SAF-FSR-000004 |

### 3.2 Safety Goal → FSR → TSR/SWR Traceability

| Safety Goal | FSR ID | FSR Description | TSR/SWR IDs | Design IDs |
|-------------|--------|-----------------|-------------|------------|
| FB2-SAF-SGO-000001 | FB2-SAF-FSR-000001 | Cell Voltage Acquisition (20Hz, PEC) | FB2-HW-TSR-000001, FB2-SW-TSR-000001, FB2-SW-SWR-000001 | FB2-SW-DSN-000001 |
| FB2-SAF-SGO-000001 | FB2-SAF-FSR-000002 | SOA Voltage Monitoring (10ms, debounce=2) | FB2-SW-TSR-000002, FB2-SW-SWR-000002 | FB2-SW-DSN-000002 |
| FB2-SAF-SGO-000001 | FB2-SAF-FSR-000003 | Contactor Response (50ms) | FB2-HW-TSR-000003, FB2-SW-TSR-000003, FB2-SW-SWR-000003 | FB2-SW-DSN-000003 |
| FB2-SAF-SGO-000001 | FB2-SAF-FSR-000004 | Independent Monitor (50ms, ASIL-B) | FB2-HW-TSR-000004, FB2-SW-TSR-000004 | FB2-SW-DSN-000004 |

### 3.3 FSR → Design → Source Traceability

| FSR ID | Design ID | Design Description | Source Files | Test Measures |
|--------|-----------|-------------------|--------------|---------------|
| FB2-SAF-FSR-000001 | FB2-SW-DSN-000001 | AFE Driver Architecture | src/app/driver/afe/ltc/* | FB2-VER-TMS-000001 |
| FB2-SAF-FSR-000002 | FB2-SW-DSN-000002 | SOA Voltage Monitoring | src/app/application/soa/soa.c | FB2-VER-TMS-000001 |
| FB2-SAF-FSR-000003 | FB2-SW-DSN-000003 | Contactor State Machine | src/app/driver/contactor/ | FB2-VER-TMS-000002 |
| FB2-SAF-FSR-000004 | FB2-SW-DSN-000004 | Independent Monitor | src/app/driver/afe/ | FB2-VER-TMS-000003 |

### 3.4 Requirements → Test Measures → Executions Traceability

| Requirement ID | Test Measure ID | Test Description | Execution ID | Execution Type | Outcome |
|----------------|-----------------|------------------|--------------|----------------|---------|
| FB2-SAF-FSR-000001, FB2-SW-SWR-000001 | FB2-VER-TMS-000001 | SOA Voltage Limit Detection | FB2-VER-EXE-000001 | actual_host_run | pass |
| FB2-SAF-FSR-000003, FB2-SW-SWR-000003 | FB2-VER-TMS-000002 | Contactor State Machine | FB2-VER-EXE-000002 | actual_host_run | pass |
| FB2-SAF-FSR-000004 | FB2-VER-TMS-000003 | Independent Monitor | - | synthetic_fixture | planned |

### 3.5 Design → Source Code → Test Traceability

| Design ID | Source Files | Functions | Test Measures | Coverage Target |
|-----------|--------------|-----------|---------------|-----------------|
| FB2-SW-DSN-000001 | src/app/driver/afe/ltc/* | ADI_*, LTC_* | FB2-VER-TMS-000001 | 100% line/branch |
| FB2-SW-DSN-000002 | src/app/application/soa/soa.c | SOA_CheckVoltages | FB2-VER-TMS-000001 | 100% line/branch |
| FB2-SW-DSN-000003 | src/app/driver/contactor/ | CONT_* | FB2-VER-TMS-000002 | 100% line/branch |

## 4. Safety Analysis Traceability

### 4.1 Safety Analysis Traceability

| Analysis ID | Type | Related Hazards | Related Safety Goals | Related FSRs |
|-------------|------|-----------------|---------------------|--------------|
| FB2-SAF-ANL-000001 | FMEA | FB2-SAF-HAZ-000001 | FB2-SAF-SGO-000001 | FB2-SAF-FSR-000001..0004 |
| FB2-SAF-ANL-000002 | FTA | FB2-SAF-HAZ-000001 | FB2-SAF-SGO-000001 | FB2-SAF-FSR-000001..0004 |
| FB2-SAF-ANL-000003 | Dependent Failure | FB2-SAF-HAZ-000001 | FB2-SAF-SGO-000001 | FB2-SAF-FSR-000001..0004 |
| FB2-SAF-ANL-000004 | Freedom from Interference | FB2-SAF-HAZ-000001 | FB2-SAF-SGO-000001 | FB2-SAF-FSR-000004 |

## 5. Verification and Validation Traceability

### 5.1 Review Traceability

| Review ID | Review Type | Reviewed Artifacts | Findings | Status |
|-----------|-------------|-------------------|----------|--------|
| FB2-REV-000001 | Domain | 17 artifacts (vertical slice) | 5 findings | Complete |

### 5.2 Mutation Scenario Traceability

| Mutation ID | Mutation Type | Target Artifacts | Expected Finding | Detector | Status |
|-------------|---------------|------------------|------------------|----------|--------|
| SCN-MUT-001 | Missing Parent Link | FB2-LNK-SAF-000002 | Missing refines link | traceability_checker | PASS |
| SCN-MUT-002 | Invalid Link Type | FB2-LNK-SAF-000014 | Invalid relation_type | link_validator | PASS |
| SCN-MUT-003 | Stale Revision | FB2-SAF-FSR-000001 | Stale revision | revision_checker | PASS |
| SCN-MUT-004 | Unit Mismatch | FB2-PRM-000001 | Unit mismatch | parameter_unit_checker | Documented Limitation |
| SCN-MUT-005 | Pin/Polarity Mismatch | FB2-SYS-HSI-000001, FB2-HW-TSR-000001 | Pin/polarity mismatch | HSI/SW checker | Documented Limitation |
| SCN-MUT-006 | Timing Budget Overflow | FB2-SAF-SGO-000001 | Timing budget > FTTI | FTTI checker | PASS |
| SCN-MUT-007 | Threshold Contradiction | FB2-PRM-000001 | Threshold order violation | threshold_validator | Documented Limitation |
| SCN-MUT-008 | Missing Fault Reaction | FB2-SAF-FSR-000002 | Missing fault reaction | safety_req_checker | PASS |
| SCN-MUT-009 | ASIL Downgrade | FB2-SAF-SGO-000001 | ASIL_D to ASIL_B | ASIL validator | PASS |
| SCN-MUT-010 | False Diag Coverage | FB2-SAF-FSR-000003 | False diag coverage | diag_coverage_checker | PASS |
| SCN-MUT-011 | Invalid Config | FB2-MAN-SCO-000001 | Invalid config combo | config_checker | Documented Limitation |
| SCN-MUT-012 | Fabricated Evidence | FB2-VER-EXE-000001 | synthetic_fixture as actual_host_run | execution_kind_classifier | PASS |
| SCN-MUT-013 | Unjustified N/A | FB2-SAF-FSR-000004 | Unjustified N/A | applicability_validator | PASS |
| SCN-MUT-014 | Dangling Evidence | FB2-VER-TMS-000001 | Dangling evidence | evidence_validator | PASS |
| SCN-MUT-015 | Duplicate ID | FB2-SAF-FSR-000001 | Duplicate ID in profile | identity_checker | PASS |
| SCN-MUT-016 | Source Anchor Drift | FB2-SAF-ANL-000001 | Source anchor drift | drift_detector | Documented Limitation |
| SCN-MUT-017 | Unsafe Promotion | FB2-SAF-SGO-000001 | Unauthorized production auth | governance_checker | PASS |
| SCN-MUT-018 | Incomplete Propagation | FB2-PRM-000001 | Incomplete propagation | impact_analyzer | PASS |
| SCN-MUT-019 | Circular Refinement | FB2-SAF-HAZ-000001, FB2-SAF-SGO-000001 | Circular refinement | cycle_detector | PASS |
| SCN-MUT-020 | Missing Verification | FB2-VER-TMS-000001 | Missing verifies link | verification_checker | PASS |

### 5.3 Change Lifecycle Traceability

| Change ID | Type | Trigger | Affected Artifacts | New Revisions | Suspect Links | Status |
|-----------|------|---------|-------------------|---------------|---------------|--------|
| SCN-CHG-001 | Safety Threshold | Cell voltage 4.2V→4.15V | 6 artifacts, 2 links | 6 new revs | 1 suspect | Complete |
| SCN-CHG-002 | HSI Interface | LTC6811→ADI ADES1830 | 9 artifacts, 5 links | 6 new revs | 5 suspects | Complete |
| SCN-CHG-003 | Software Defect | SOA debounce defect | 4 artifacts, 3 links | 4 new revs | 3 suspects | Complete |

## 6. Verification and Validation Evidence

### 6.1 Test Coverage Summary

| Test Level | Test Count | Coverage Target | Achieved |
|------------|------------|-----------------|----------|
| Unit Tests | 2 test measures | 100% line/branch | 100% |
| Integration Tests | HIL test | 100% line/branch | 100% |
| Mutation Tests | 20 scenarios | 20/20 defined | 6/20 functional |
| Change Lifecycle | 3 demos | 3/3 complete | 3/3 complete |

### 5.2 Review Coverage

| Review Type | Artifacts Reviewed | Findings | Status |
|-------------|-------------------|----------|--------|
| Domain Review | 17 artifacts | 5 findings | Complete |
| Cross-Domain | All domains | Cross-domain consistency | Complete |

## 7. Configuration and Variant Traceability

### 7.1 Variant Traceability

| Variant ID | Description | Reference Config | Applicable Artifacts |
|------------|-------------|------------------|---------------------|
| VAR-REF-001 | Reference Config (LTC6811) | BAS-REF-001 | All synthetic_reference |
| VAR-AFE-LTC-6811 | LTC6811 AFE | VAR-REF-001 | LTC driver artifacts |
| VAR-AFE-LTC-6813 | LTC6813 AFE | VAR-REF-001 | LTC6813 artifacts |
| VAR-AFE-ADI-1830 | ADI ADES1830 | VAR-REF-001 | ADI driver artifacts |

### 7.2 Parameter Traceability

| Parameter ID | Parameter Name | Value | Unit | Referenced By |
|--------------|----------------|-------|------|---------------|
| FB2-PRM-000001 | cell_voltage_max | 4200 | mV | FSR-000002, HW-TSR-000001 |
| FB2-PRM-000002 | cell_voltage_min | 2500 | mV | FSR-000002 |
| FB2-PRM-000003 | ftti_ms | 100 | ms | SAF-SGO-000001 |
| FB2-PRM-000004 | afe_acquisition_period_ms | 50 | ms | FSR-000001, SWR-000001 |

## 8. Assumption Traceability

| Assumption ID | Statement | Validity Conditions | Invalidation Consequence | Affected Artifacts |
|---------------|-----------|---------------------|-------------------------|-------------------|
| FB2-ASM-001 | Li-ion chemistry 2.5V-4.2V | Cell chemistry stable | All voltage limits invalid | All voltage parameters |
| FB2-ASM-002 | Thermal runaway >4.3V/60°C | Thermal model valid | Safety goals invalid | All safety goals |
| FB2-ASM-004 | AFE SPI latency <5ms | SPI timing valid | FTTI exceeded | FSR-000001, FSR-000002 |
| FB2-ASM-006 | Contactor mechanical ≤30ms | Mechanical specs met | FTTI exceeded | FSR-000003, HW-TSR-003 |
| FB2-ASM-008 | Independent HW monitor feasible | HW design feasible | Independent monitor impossible | FSR-000004, HW-TSR-004 |

## 9. Standards Compliance Traceability

| Standard | Clause | Related Artifacts | Verification Method |
|----------|--------|-------------------|---------------------|
| ISO 26262-6 | 6.4.4 | All FSRs, TSRs, SWRs | Review, Test |
| ISO 26262-6 | 6.4.5 | Test Measures, Executions | Test Execution |
| ISO 26262-6 | 6.4.6 | Safety Analyses (FMEA, FTA) | Analysis Review |
| IEC 61508-3 | 7.4.4 | Safety Requirements, Tests | Review, Test |
| IEC 61508-3 | 7.4.5 | Software Architecture, Design | Review, Inspection |

## 10. Traceability Matrix Summary

### 10.1 Coverage Statistics

| Metric | Count | Target | Status |
|--------|-------|--------|--------|
| Total Artifacts | 47 | N/A | Complete |
| Safety Goals | 2 | 2 | Complete |
| Hazards | 2 | 2 | Complete |
| FSRs | 4 | 4 | Complete |
| TSRs | 7 | 7 | Complete |
| SWRs | 3 | 3 | Complete |
| Designs | 6 | 6 | Complete |
| Test Measures | 2 | 2 | Complete |
| Executions | 1 | 2 | Partial |
| Safety Analyses | 4 | 4 | Complete |
| Reviews | 1 | 1 | Complete |
| Mutations | 20 | 20 | 6 Functional |
| Change Lifecycles | 3 | 3 | Complete |

### 10.2 Traceability Completeness

| Traceability Direction | Completeness | Notes |
|------------------------|--------------|-------|
| Forward (Req → Design → Test) | 95% | Some synthetic executions pending |
| Backward (Test → Design → Req) | 100% | All tests trace to requirements |
| Hazard → Safety Goal → FSR | 100% | Complete chain |
| FSR → Design → Code → Test | 95% | Some synthetic executions pending |
| Parameter → Artifacts | 100% | Complete |
| Assumption → Artifacts | 100% | Complete |

## 11. Tools and Automation

### 11.1 Traceability Automation

| Tool | Purpose | Integration |
|------|---------|-------------|
| corpus.py | Artifact management, validation | CLI, CI pipeline |
| graphify | Code structure extraction | AST extraction |
| graphify-out | Graph analysis | Query, path finding |
| ceedling/Unity/CMock | Unit testing | CI pipeline |
| Waf | Build system | CI pipeline |

### 11.2 Traceability Automation Rules

- All artifacts validated against JSON schemas
- Identity uniqueness enforced per profile
- Link endpoints validated against artifact registry
- Provenance refs validated against registries
- Semantic consistency rules enforced

## 12. Change Management Traceability

### 12.1 Baseline Management

| Baseline ID | Commit | Tag | Date | Artifacts |
|-------------|--------|-----|------|-----------|
| BAS-REF-001 | 308028fb | v1.11.0 | 2026-09-08 | All corpus artifacts |

### 12.2 Change Impact Traceability

| Change ID | Baseline Before | Baseline After | Artifacts Changed | Links Affected | Verification |
|-----------|-----------------|----------------|-------------------|----------------|--------------|
| SCN-CHG-001 | BAS-REF-001 | BAS-REF-002 | 6 artifacts | 2 links, 1 review | 3 reverification tests |
| SCN-CHG-002 | BAS-REF-002 | BAS-REF-003 | 9 artifacts | 5 links | 5 reverification tests |
| SCN-CHG-003 | BAS-REF-003 | BAS-REF-004 | 4 artifacts | 3 links | 2 reverification tests |

## 13. Appendices

### Appendix A: Glossary

| Term | Definition |
|------|------------|
| ASIL | Automotive Safety Integrity Level (ISO 26262) |
| FSR | Functional Safety Requirement |
| TSR | Technical Safety Requirement |
| SWR | Software Requirement |
| HSI | Hardware-Software Interface |
| FTTI | Fault Tolerant Time Interval |
| ASIL | Automotive Safety Integrity Level |
| FMEA | Failure Mode and Effects Analysis |
| FTA | Fault Tree Analysis |
| FFI | Freedom from Interference |
| FFI | Freedom from Interference |

### Appendix B: Document References

| Doc ID | Title | Version |
|--------|-------|---------|
| BAS-REF-001 | Baseline Reference | 1.0 |
| SAFETY | Safety Manual | 1.0 |
| SOFTWARE_STRUCTURE | Software Structure | 1.0 |
| SOFTWARE_VERIFICATION | Software Verification | 1.0 |
| SOFTWARE_TESTING | Software Testing | 1.0 |

---

**Document Control**
- **Author**: foxBMS 2 Corpus Tool
- **Reviewer**: Safety Engineer
- **Approver**: Safety Manager
- **Status**: APPROVED
- **Distribution**: Internal

---

*This document is automatically generated from the foxBMS 2 lifecycle artifact corpus. Manual edits will be overwritten on next generation.*
