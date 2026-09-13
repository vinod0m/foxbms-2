# foxBMS 2 — System Verification Report

**Document Control**

| Field | Value |
|---|---|
| Project | foxBMS 2 — Battery Management System |
| Document | System Verification Report |
| Baseline | BAS-REF-001 (commit `308028fb`, tag `v1.11.0`) |
| Profiles | `as_is` (source-grounded) + `synthetic_reference` (hypothetical) |
| Corpus status | `synthetic_ready_with_limitations` |
| Generated | 2026-09-13T02:20:37Z |

## Scope

System-level verification: (1) reverse-engineered system verification evidence — CI test levels, diagnosis reaction verification, measurement validation; (2) test specification, cases and execution reports from corpus TMS/EXE artifacts. Missing evidence is blocked, not fabricated.

## Reverse-Engineered System Verification Evidence

### Test Levels in the Repository

| Level | Scope | Evidence |
|---|---|---|
| Unit (host) | all `src/app` modules | 313 C test files in `tests/unit/app/**`, Ceedling/Unity, executed in CI for every revision (`docs/developer-manual/software/software-verification.rst`) |
| Static checks | whole repo | C standard conformance tests (`tests/c-std`), CLI tests (`tests/cli`), DBC validity checks (`tests/dbc`), OS-include hygiene (`tests/os-information`) |
| HIL | linked program on target | Test setup **not published** in this repository (`tests/hil` placeholder, `docs/developer-manual/software/software-testing.rst`) |

Policy: unit and HIL coverage reports **MUST** show 100% line and branch coverage (software testing doc). Failing tests reject the feature branch in CI.

### Diagnosis Reaction Verification (built-in)

Every diagnosis entry is verifiable through the built-in reaction chain: `DIAG_*` event → severity evaluation (`DIAG_UpdateFlags`, 1 ms) → BMS FSM `BMS_FSM_STATE_ERROR` → contactor open. Unit tests cover the diagnosis engine (22 test files in `tests/unit/app/engine/diag/`) and the SOA limit evaluation (`tests/unit/app/application/soa/`, `application/config/`).

### Measurement Validation (built-in)

Cell measurements are validated continuously at runtime: plausibility checks (`PL_CheckEvent*`), redundancy validation (`MRC_ValidateAfeMeasurement` every 50 ms), AFE communication integrity diagnosis entries — i.e. the system verifies its own measurement path as part of operation.

## Test Specification

#### `FB2-VER-TMS-000001` — Test: SOA Voltage Limit Detection (as_is)

- **Test type**: `unit` | **Oracle basis**: `source_grounded`
- **Objective**: Verify SOA voltage limit detection accuracy and latency
- **Preconditions**: SOA module initialized with valid config, Database accessible, Test doubles for DATA_ReadData injected
- **Environment**: POSIX host (Linux); Unity/CMock test framework; config `conf/unit/app_project_posix.yml`
- **Test cases (steps)**:
  1. **Inject cell voltage 4300 mV (above 4200 mV limit)** → expected: SOA_CheckVoltageLimits called
  2. **Repeat injection 3 times (debounce count)** → expected: Debounce counter increments
  3. **Verify FAULT request triggered** → expected: SYS_SetState(FAULT) called
  4. **Inject voltage 4100 mV (within limits)** → expected: No fault triggered
- **Expected outcomes**:
  - `fault_request` = true (tolerance exact)
  - `violation_cell_index` = 0 (tolerance exact)
  - `violation_type` = OVERVOLTAGE (tolerance exact)

#### `FB2-VER-TMS-000002` — Test: Contactor State Machine and Fault Response (as_is)

- **Test type**: `unit` | **Oracle basis**: `source_grounded`
- **Objective**: Verify contactor state machine transitions and fault response latency
- **Preconditions**: Contactor driver initialized, SBC mock injected, Feedback GPIO mocks injected, FRAM mock injected
- **Environment**: POSIX host (Linux); Unity/CMock test framework; config `conf/unit/app_project_posix.yml`
- **Test cases (steps)**:
  1. **Request PRECHARGE** → expected: Precharge contactor coil energized
  2. **Simulate precharge feedback closed** → expected: State -> PRECHARGE_WAIT
  3. **Simulate pack voltage > threshold** → expected: Main contactor energized, precharge de-energized
  4. **Simulate main feedback closed** → expected: State -> HOLD
  5. **Inject FAULT request** → expected: All coils de-energized within 5 ms
  6. **Verify feedback open** → expected: State -> FAULT_OPEN
- **Expected outcomes**:
  - `precharge_coil` = energized (tolerance exact)
  - `main_coil` = energized (tolerance exact)
  - `fault_response_latency` = < 5 (tolerance max)
  - `final_state` = FAULT_OPEN (tolerance exact)

## Test Cases

- `FB2-VER-TMS-000001` (as_is): 4 test case(s)
- `FB2-VER-TMS-000002` (as_is): 6 test case(s)

**Total system-level test cases**: 10

## Execution Report

##### Execution `FB2-VER-EXE-000001` — Execution: SOA Voltage Limit Test

- **Test measure**: `FB2-VER-TMS-000001` | **Execution kind**: `actual_host_run` | **Outcome**: **PASS**
- **Environment**: x86_64 Linux host; Unity 2.5.2, CMock 2.4.0; tools: cmake 3.22.1, cmock 2.4.0, gcc 11.4.0, unity 2.5.2
- **Evidence refs**: `FB2-VER-TMS-000001`, `tests/unit/app/application/soa/test_soa.c`



---

*Generated: 2026-09-13T02:20:37Z — auto-generated from the machine-verifiable corpus. Regenerate with `python3 docs/artifacts/tools/render_spec_documents.py`.*
