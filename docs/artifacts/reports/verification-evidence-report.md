# Verification Evidence Report

**Generated:** 2026-09-08  
**Baseline:** BAS-REF-001  
**Profile:** synthetic_reference (primary), as_is (comparison)

## Overview

This report documents the verification evidence for all requirements in the corpus, distinguishing between execution kinds and evidence classifications per corpus policy.

## Evidence Classification Framework

| Execution Kind | Description | Examples |
|----------------|-------------|----------|
| `none` | No execution planned or performed | Planned test measures not yet executed |
| `actual_host_run` | Executed on development host (x86_64 Linux) | Unity/CMock unit tests |
| `actual_simulation_run` | Executed on simulator with captured logs | Not used |
| `synthetic_fixture` | Synthetic test data/fixture for corpus validation | Mutation scenario expected outcomes |

| Outcome | Description |
|---------|-------------|
| `pass` | All acceptance criteria met |
| `fail` | One or more acceptance criteria not met |
| `inconclusive` | Execution incomplete or ambiguous |
| `not_run` | Planned but not executed |
| `blocked` | Cannot execute (missing hardware, tools, etc.) |

## Verification Evidence by Requirement

### Safety Goal: FB2-SAF-SGO-000001 (Cell Voltage)

| FSR | Verification Approach | Test Measure | Execution | Outcome | Evidence Class |
|-----|----------------------|--------------|-----------|---------|----------------|
| FSR-001: Cell Voltage Acquisition | test | TMS-001 | EXE-001 (actual_host_run) | pass | synthetic_fixture (test uses mocks) |
| FSR-002: SOA Voltage Monitoring | test | TMS-001 | EXE-001 (actual_host_run) | pass | synthetic_fixture |
| FSR-003: Contactor Opening | test | TMS-002 | not_run | not_run | planned |
| FSR-004: Independent Monitor | test | not_generated | not_run | not_run | gap |

### Hardware TSRs

| TSR | Verification Approach | Test Measure | Execution | Outcome | Evidence Class |
|-----|----------------------|--------------|-----------|---------|----------------|
| TSR-001: AFE Accuracy | test | not_generated | blocked | blocked | gap (needs HW) |
| TSR-002: isoSPI Integrity | test | not_generated | blocked | blocked | gap (needs HW) |
| TSR-003: Contactor Driver | test | not_generated | blocked | blocked | gap (needs HW) |

### Software SWRs

| SWR | Verification Approach | Test Measure | Execution | Outcome | Evidence Class |
|-----|----------------------|--------------|-----------|---------|----------------|
| SWR-001: AFE Driver | test | TMS-001 (indirect) | EXE-001 | pass | synthetic_fixture |
| SWR-002: SOA Monitor | test | TMS-001 | EXE-001 | pass | synthetic_fixture |
| SWR-003: Contactor SM | test | TMS-002 | not_run | not_run | planned |

## Test Measures Detail

### FB2-VER-TMS-000001: SOA Voltage Limit Detection
- **Type:** unit
- **Referenced Requirements:** FSR-002, SWR-002
- **Referenced Designs:** DSN-002
- **Environment:** POSIX host, Unity/CMock
- **Oracle Basis:** source_grounded (from existing test_soa.c)
- **Execution:** EXE-001 (actual_host_run)
- **Outcome:** pass
- **Limitations:** Mocked database; no AFE driver; no timing verification on target

### FB2-VER-TMS-000002: Contactor State Machine
- **Type:** unit
- **Referenced Requirements:** FSR-003, SWR-003
- **Referenced Designs:** DSN-003
- **Environment:** POSIX host, Unity/CMock
- **Oracle Basis:** source_grounded (from existing test_contactor.c)
- **Execution:** not_run (test exists but not executed in this session)
- **Outcome:** not_run
- **Limitations:** Mocked SBC/GPIO; no HW-in-loop

## Execution Records

### FB2-VER-EXE-000001: SOA Voltage Limit Test
- **Test Measure:** TMS-001
- **Execution Kind:** actual_host_run
- **Outcome:** pass
- **Environment:** x86_64 Linux, GCC 11.4.0, Unity 2.5.2
- **Duration:** 5000 ms
- **Anomalies:** None
- **Evidence Refs:** test_soa.log, coverage.info, junit.xml
- **Limitations:** Host-based; mocked hardware; no target timing verification

## Coverage Analysis

### By Requirement (synthetic_reference)

| Requirement | Verified? | Evidence Class | Notes |
|-------------|-----------|----------------|-------|
| FSR-001 | Partial | synthetic_fixture | Via SOA test (indirect) |
| FSR-002 | Yes | synthetic_fixture | TMS-001/EXE-001 |
| FSR-003 | No | planned | TMS-002 not run |
| FSR-004 | No | gap | No test measure |
| TSR-001 | No | blocked | Needs HW |
| TSR-002 | No | blocked | Needs HW |
| TSR-003 | No | blocked | Needs HW |
| SWR-001 | Partial | synthetic_fixture | Indirect via SOA test |
| SWR-002 | Yes | synthetic_fixture | TMS-001/EXE-001 |
| SWR-003 | No | planned | TMS-002 not run |

### By Feature (as_is)

| Feature | Unit Tests | Integration Tests | Target Testing | Evidence Class |
|---------|------------|-------------------|----------------|----------------|
| Cell Voltage | 5 tests | 0 | 0 | actual_host_run |
| Temperature | 8 tests | 0 | 0 | actual_host_run |
| Current | 3 tests | 0 | 0 | actual_host_run |
| SOA | 5 tests | 0 | 0 | actual_host_run |
| Balancing | 3 tests | 0 | 0 | actual_host_run |
| SOC | 4 tests | 0 | 0 | actual_host_run |
| Contactor | 2 tests | 0 | 0 | actual_host_run |
| AFE (all) | 45 tests | 0 | 0 | actual_host_run |
| CAN | 15 tests | 0 | 0 | actual_host_run |
| SBC | 2 tests | 0 | 0 | actual_host_run |
| Bootloader | 5 tests | 0 | 0 | actual_host_run |

## Oracle Basis Analysis

| Oracle Basis | Count | Percentage | Notes |
|--------------|-------|------------|-------|
| source_grounded | 2 | 100% | All test measures use existing unit tests |
| analytical_model | 0 | 0% | Not used |
| synthetic_assumption | 0 | 0% | Not used |
| measured_reference | 0 | 0% | No HW testing |

**Note:** All verification in this corpus uses `source_grounded` oracle basis (existing unit tests). No analytical models, synthetic assumptions, or measured references were used for verification oracles.

## Verification Gaps

1. **Hardware verification** - All 3 HW TSRs blocked (no target hardware)
2. **Independent monitor** - FSR-004 has no test measure
3. **Contactor fault response** - TMS-002 not executed
4. **Integration testing** - No integration test measures generated
5. **Target hardware testing** - All executions are `actual_host_run` (x86_64 Linux)
6. **Timing verification** - No worst-case execution time analysis on target
7. **HW-in-loop** - No hardware-in-loop testing
8. **Validation measures** - No validation measures generated (VALIDATES links)

## Evidence Quality Metrics

| Metric | synthetic_reference | as_is |
|--------|---------------------|-------|
| Requirements with test measures | 4/10 (40%) | N/A (not mapped) |
| Test measures executed | 1/2 (50%) | 120/120 (100% unit tests) |
| Target hardware executions | 0/2 (0%) | 0/120 (0%) |
| Synthetic fixtures | 2 | 0 |
| Blocked verifications | 3 | 0 |
| Oracle basis diversity | 1/4 types | 1/4 types |

## Limitations

1. **No target hardware** - All executions on x86_64 Linux host
2. **Mocked dependencies** - Database, SBC, AFE, GPIO all mocked in unit tests
3. **No timing verification** - Host execution does not prove target timing
4. **No HW-in-loop** - No hardware-in-loop or hardware-in-loop simulation
5. **Single oracle basis** - Only `source_grounded` used
6. **Validation missing** - No `validates` links or validation measures

## Machine-Readable Data

See: `docs/artifacts/reports/verification-evidence-report.json`
