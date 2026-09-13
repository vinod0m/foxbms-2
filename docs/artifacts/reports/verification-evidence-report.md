# Verification Evidence Report

**Generated:** 2026-09-13  
**Baseline:** BAS-REF-001  
**Profile:** synthetic_reference (primary), as_is (comparison)

## Overview

This report documents the verification evidence for all requirements in the corpus, distinguishing between execution kinds and evidence classifications per corpus policy. With the test-measure expansion all FSRs, SWRs and hardware TSRs in the synthetic_reference profile now have dedicated test measures and (synthetic fixture) executions; the as_is profile carries the source-grounded unit-test measures extracted from the real foxBMS 2 test suite.

## Evidence Classification Framework

| Execution Kind | Description | Examples |
|----------------|-------------|---------|
| `none` | No execution planned or performed | Planned test measures not yet executed |
| `actual_host_run` | Executed on development host (x86_64 Linux) | Unity/CMock unit tests |
| `actual_simulation_run` | Executed on simulator with captured logs | Not used |
| `synthetic_fixture` | Synthetic test data/fixture for corpus validation | Synthetic execution set EXE-001..006 |

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
| FSR-001: Cell Voltage Acquisition | test | TMS-003 | EXE-003 (synthetic_fixture) | pass | synthetic_fixture |
| FSR-002: SOA Voltage Monitoring | test | TMS-001 | EXE-001 (synthetic_fixture; as_is: actual_host_run) | pass | synthetic_fixture / actual_host_run (as_is) |
| FSR-003: Contactor Opening | test | TMS-002 | EXE-002 (synthetic_fixture) | pass | synthetic_fixture |
| FSR-004: Independent Monitor | test (fault_injection) | TMS-004 | EXE-004 (synthetic_fixture) | pass | synthetic_fixture |

### Hardware TSRs

| TSR | Verification Approach | Test Measure | Execution | Outcome | Evidence Class |
|-----|----------------------|--------------|-----------|---------|----------------|
| TSR-001: AFE Accuracy | test | TMS-003 | EXE-003 (synthetic_fixture) | pass | synthetic_fixture (unit-level model; target measurement blocked) |
| TSR-002: isoSPI Integrity | test (robustness) | TMS-005 | EXE-005 (synthetic_fixture) | pass | synthetic_fixture (unit-level model; target measurement blocked) |
| TSR-003: Contactor Driver | test | TMS-006 | EXE-006 (synthetic_fixture) | pass | synthetic_fixture (unit-level model; target measurement blocked) |
| TSR-004: Independent Monitor HW | test (fault_injection) | TMS-004 | EXE-004 (synthetic_fixture) | pass | synthetic_fixture |

### Software SWRs

| SWR | Verification Approach | Test Measure | Execution | Outcome | Evidence Class |
|-----|----------------------|--------------|-----------|---------|----------------|
| SWR-001: AFE Driver | test | TMS-003 | EXE-003 | pass | synthetic_fixture |
| SWR-002: SOA Monitor | test | TMS-001 | EXE-001 | pass | synthetic_fixture |
| SWR-003: Contactor SM | test | TMS-002 | EXE-002 | pass | synthetic_fixture |

## Test Measures Detail

| ID | Title | Type | Requirements | Oracle Basis | Profile |
|----|-------|------|--------------|--------------|---------|
| FB2-VER-TMS-000001 | SOA Voltage Limit Detection | unit | FSR-002, SWR-002 | source_grounded (as_is: test_soa.c) | both |
| FB2-VER-TMS-000002 | Contactor State Machine Fault Response | unit | FSR-003, SWR-003 | source_grounded (as_is: test_contactor.c) | both |
| FB2-VER-TMS-000003 | AFE Cell Voltage Plausibility Checks | unit | FSR-001, SWR-001, TSR-001 | source_grounded (as_is: test_afe_plausibility.c) | both |
| FB2-VER-TMS-000004 | Independent Voltage Monitor Reaction | fault_injection | FSR-004, TSR-004 | synthetic_assumption | synthetic_reference |
| FB2-VER-TMS-000005 | AFE Communication Integrity | robustness | TSR-002 | source_grounded (as_is: test_ltc_6813-1.c) | both |
| FB2-VER-TMS-000006 | Contactor Driver Configuration and Control | unit | TSR-003 | source_grounded (as_is: test_contactor.c) | synthetic_reference |

## Execution Records

| ID | Test Measure | Kind | Outcome | Duration | Limitations |
|----|--------------|------|---------|----------|-------------|
| FB2-VER-EXE-000001 | TMS-001 | synthetic_fixture (as_is twin: actual_host_run) | pass | 5000 ms | Mocked database; no target timing |
| FB2-VER-EXE-000002 | TMS-002 | synthetic_fixture | pass | 5000 ms | Mocked SBC/GPIO; no HW-in-loop |
| FB2-VER-EXE-000003 | TMS-003 | synthetic_fixture | pass | 5000 ms | Mocked AFE; no target measurement |
| FB2-VER-EXE-000004 | TMS-004 | synthetic_fixture | pass | 5000 ms | Fault injection on model, not diverse hardware path |
| FB2-VER-EXE-000005 | TMS-005 | synthetic_fixture | pass | 5000 ms | PEC corruption simulated at driver API level |
| FB2-VER-EXE-000006 | TMS-006 | synthetic_fixture | pass | 5000 ms | GPIO mocked; no contactor hardware |

## Hardware-in-the-Loop (HIL) Disposition

The upstream foxBMS 2 repository prescribes HIL testing with **100% line and branch
coverage** for the linked program on target hardware
(`docs/developer-manual/software/software-testing.rst`,
`docs/developer-manual/software/software-verification.rst`), but the HIL test setup
itself is **not published** in the repository (`tests/hil` contains a placeholder only).

Corpus disposition for this gap:

1. **as_is profile** — the gap is *documented, not bridged*: no HIL artifacts are
   fabricated. Unit-test coverage (313 C test files under `tests/unit/app/`) is the
   observable evidence; HIL evidence is explicitly classified `blocked`
   (missing target hardware and test setup).
2. **synthetic_reference profile** — hardware TSR verification is demonstrated at the
   *unit level with mocked hardware boundaries* (TMS-003/005/006). These executions
   are honest about their class (`synthetic_fixture`); they do not claim target
   measurement credit. `product_verification_credit` remains `false` for every
   artifact by governance policy.
3. **No execution claims HIL.** The `execution_kind` vocabulary contains no HIL entry;
   target-hardware verification would require `actual_hardware_run` evidence (logs,
   hashes, tool versions) that does not exist and is therefore not invented.

## Coverage Analysis

### By Requirement (synthetic_reference)

| Requirement | Verified? | Evidence Class | Notes |
|-------------|-----------|----------------|-------|
| FSR-001 | Yes | synthetic_fixture | TMS-003/EXE-003 |
| FSR-002 | Yes | synthetic_fixture | TMS-001/EXE-001 |
| FSR-003 | Yes | synthetic_fixture | TMS-002/EXE-002 |
| FSR-004 | Yes | synthetic_fixture | TMS-004/EXE-004 |
| TSR-001 | Yes (unit-level) | synthetic_fixture | TMS-003/EXE-003; target measurement blocked |
| TSR-002 | Yes (unit-level) | synthetic_fixture | TMS-005/EXE-005; target measurement blocked |
| TSR-003 | Yes (unit-level) | synthetic_fixture | TMS-006/EXE-006; target measurement blocked |
| TSR-004 | Yes (unit-level) | synthetic_fixture | TMS-004/EXE-004; target measurement blocked |
| SWR-001 | Yes | synthetic_fixture | TMS-003/EXE-003 |
| SWR-002 | Yes | synthetic_fixture | TMS-001/EXE-001 |
| SWR-003 | Yes | synthetic_fixture | TMS-002/EXE-002 |
| SCO-001 (management) | No | N/A | Management scope item; verification by process audit, not test |

### By Feature (as_is, real repository unit tests)

| Feature | Unit Tests | Integration Tests | Target Testing | Evidence Class |
|---------|------------|-------------------|---------------|----------------|
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

| Oracle Basis | Count | Notes |
|--------------|-------|-------|
| source_grounded | 5 (as_is) / 4 (synthetic mirrors) | Grounded in existing foxBMS unit tests |
| synthetic_assumption | 2 | TMS-004, TMS-005 (synthetic profile robustness/fault-injection designs) |
| analytical_model | 0 | Not used |
| measured_reference | 0 | No HW testing |

## Verification Gaps (remaining, honest)

1. **Target hardware measurement** — TSR-001/002/004 verified at unit level only;
   actual hardware measurements remain blocked (no target hardware in corpus scope).
2. **HIL execution** — no HIL runs; upstream test setup unpublished (see disposition above).
3. **Integration test measures** — no dedicated integration-level test measures in the corpus.
4. **Timing verification** — no worst-case execution time analysis on target.
5. **Management scope (SCO-001)** — verified by process audit only, no test measure (by nature of the artifact).

Every gap above is tracked as a corpus limitation (`final_status:
synthetic_ready_with_limitations`); no evidence is fabricated to close it.
