# foxBMS 2 — System Verification Report

**Document Control**

| Field | Value |
|---|---|
| Project | foxBMS 2 — Battery Management System |
| Document | System Verification Report |
| Baseline | BAS-REF-001 (commit `308028fb`, tag `v1.11.0`) |
| Profiles | `as_is` (source-grounded) + `synthetic_reference` (hypothetical) |
| Corpus status | `synthetic_ready_with_limitations` |
| Generated | 2026-09-29T10:08:35Z |

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

#### `FB2-VER-TMS-000003` — Test: AFE Cell Voltage Plausibility Checks (as_is)

- **Test type**: `unit` | **Oracle basis**: `source_grounded`
- **Objective**: Verify AFE cell voltage measurement plausibility validation before database entry
- **Preconditions**: Module initialized with valid config, Test doubles injected
- **Environment**: POSIX host (Linux); Unity/CMock; config `conf/unit/app_project_posix.yml`
- **Test cases (steps)**:
  1. **Inject valid cell voltage 3300 mV** → expected: Plausibility check passes
  2. **Inject out-of-range voltage 4900 mV** → expected: Plausibility check flags implausible
  3. **Inject delta violation between redundant samples** → expected: Flagged implausible
- **Expected outcomes**:
  - `plausibility_result` = pass (tolerance exact)
  - `flagged_cell` = true (tolerance exact)

#### `FB2-VER-TMS-000004` — Test: LTC6813-1 AFE Driver Communication and Measurement (as_is)

- **Test type**: `unit` | **Oracle basis**: `source_grounded`
- **Objective**: Verify AFE driver SPI communication integrity and cell voltage measurement accuracy
- **Preconditions**: Module initialized with valid config, Test doubles injected
- **Environment**: POSIX host (Linux); Unity/CMock; config `conf/unit/app_project_posix.yml`
- **Test cases (steps)**:
  1. **Issue AFE read command via mocked SPI** → expected: Command frame matches LTC6813-1 PEC
  2. **Feed known cell voltage raw values** → expected: Converted mV values within ±1.5 mV
  3. **Corrupt PEC of response frame** → expected: Communication error reported, no data committed
- **Expected outcomes**:
  - `cell_voltage_mv` = 3300 (tolerance ±1.5 mV)
  - `pec_error` = true (tolerance exact)

#### `FB2-VER-TMS-000005` — Test: Contactor Driver Configuration and Control (as_is)

- **Test type**: `unit` | **Oracle basis**: `source_grounded`
- **Objective**: Verify contactor driver initialization, channel mapping and switch-off safety behavior
- **Preconditions**: Module initialized with valid config, Test doubles injected
- **Environment**: POSIX host (Linux); Unity/CMock; config `conf/unit/app_project_posix.yml`
- **Test cases (steps)**:
  1. **Initialize contactor driver with valid config** → expected: All channels mapped
  2. **Set contactor on** → expected: GPIO output asserted
  3. **Request safety switch-off (all contactors)** → expected: All channels de-energized
- **Expected outcomes**:
  - `contactor_state` = on (tolerance exact)
  - `all_off` = true (tolerance exact)

#### `FB2-VER-TMS-000001` — Test: SOA Voltage Limit Detection (synthetic_reference)

- **Test type**: `unit` | **Oracle basis**: `synthetic_assumption`
- **Objective**: Verify SOA voltage limit detection accuracy and latency
- **Preconditions**: Module initialized with valid config, Test doubles injected
- **Environment**: POSIX host (Linux); Unity/CMock; config `conf/unit/app_project_posix.yml`
- **Test cases (steps)**:
  1. **Inject cell voltage 4300 mV (above 4200 mV limit)** → expected: Debounce counter increments
  2. **Repeat injection 2 times (debounce count)** → expected: FAULT request triggered
  3. **Inject voltage 4100 mV (within limits)** → expected: No fault triggered
- **Expected outcomes**:
  - `fault_request` = true (tolerance exact)
  - `violation_type` = OVERVOLTAGE (tolerance exact)

#### `FB2-VER-TMS-000002` — Test: Contactor State Machine Fault Response (synthetic_reference)

- **Test type**: `unit` | **Oracle basis**: `synthetic_assumption`
- **Objective**: Verify contactor state machine transitions and fault response latency
- **Preconditions**: Module initialized with valid config, Test doubles injected
- **Environment**: POSIX host (Linux); Unity/CMock; config `conf/unit/app_project_posix.yml`
- **Test cases (steps)**:
  1. **Drive state machine through normal path** → expected: Transitions match state table
  2. **Inject fault request** → expected: Open contactors within 50 ms
  3. **Verify feedback mismatch diagnosis** → expected: DIAG event raised
- **Expected outcomes**:
  - `contactor_open_latency_ms` = <50 (tolerance exact)
  - `fault_feedback_diag` = true (tolerance exact)

#### `FB2-VER-TMS-000003` — Test: AFE Cell Voltage Plausibility Checks (synthetic_reference)

- **Test type**: `unit` | **Oracle basis**: `synthetic_assumption`
- **Objective**: Verify AFE cell voltage measurement plausibility validation before database entry
- **Preconditions**: Module initialized with valid config, Test doubles injected
- **Environment**: POSIX host (Linux); Unity/CMock; config `conf/unit/app_project_posix.yml`
- **Test cases (steps)**:
  1. **Inject valid cell voltage 3300 mV** → expected: Plausibility check passes
  2. **Inject out-of-range voltage 4900 mV** → expected: Flagged implausible
- **Expected outcomes**:
  - `plausibility_result` = pass (tolerance exact)

#### `FB2-VER-TMS-000004` — Test: Independent Voltage Monitor Reaction (synthetic_reference)

- **Test type**: `fault_injection` | **Oracle basis**: `synthetic_assumption`
- **Objective**: Verify independent monitor detects overvoltage and opens contactors on diverse path
- **Preconditions**: Module initialized with valid config, Test doubles injected
- **Environment**: POSIX host (Linux); Unity/CMock; config `conf/unit/app_project_posix.yml`
- **Test cases (steps)**:
  1. **Inject cell voltage above monitor threshold** → expected: Monitor path triggers independent open
  2. **Hold violation beyond monitor reaction time** → expected: Contactors opened within 80 ms
  3. **Verify path independence from primary SOA** → expected: Reaction with primary path disabled
- **Expected outcomes**:
  - `independent_open_latency_ms` = <80 (tolerance exact)
  - `path_independent` = true (tolerance exact)

#### `FB2-VER-TMS-000005` — Test: AFE Communication Integrity (synthetic_reference)

- **Test type**: `robustness` | **Oracle basis**: `synthetic_assumption`
- **Objective**: Verify AFE SPI communication integrity under frame corruption
- **Preconditions**: Module initialized with valid config, Test doubles injected
- **Environment**: POSIX host (Linux); Unity/CMock; config `conf/unit/app_project_posix.yml`
- **Test cases (steps)**:
  1. **Corrupt PEC of AFE response frame** → expected: Communication error reported
  2. **Verify retry counter** → expected: Error counter increments
  3. **Corrupt beyond tolerance** → expected: AFE communication diagnosis entry
- **Expected outcomes**:
  - `pec_error` = true (tolerance exact)
  - `afe_diag_entry` = true (tolerance exact)

#### `FB2-VER-TMS-000006` — Test: Contactor Driver Configuration and Control (synthetic_reference)

- **Test type**: `unit` | **Oracle basis**: `synthetic_assumption`
- **Objective**: Verify contactor driver initialization, channel mapping and switch-off safety behavior
- **Preconditions**: Module initialized with valid config, Test doubles injected
- **Environment**: POSIX host (Linux); Unity/CMock; config `conf/unit/app_project_posix.yml`
- **Test cases (steps)**:
  1. **Initialize driver with valid config** → expected: All channels mapped
  2. **Request safety switch-off** → expected: All channels de-energized
- **Expected outcomes**:
  - `all_off` = true (tolerance exact)

#### `FB2-VER-TMS-000007` — Test: Software Integration Chain (SOA-Database-Contactor) (synthetic_reference)

- **Test type**: `integration` | **Oracle basis**: `synthetic_assumption`
- **Objective**: Define the software integration verification intent for the SOA-database-contactor chain; PLANNING STUB — no execution performed, execution blocked (no integration harness in corpus scope)
- **Preconditions**: SOA, database and contactor units available as host builds, Integration harness defined (blocked — not in corpus scope)
- **Environment**: POSIX host (Linux) — harness blocked; Unity/CMock; config `conf/unit/app_project_posix.yml`
- **Test cases (steps)**:
  1. **Publish violated cell voltage set to database via MEAS path** → expected: SOA reads violated set within task cycle
  2. **Confirm SOA fault request propagates to BMS state machine** → expected: FAULT state entered
  3. **Confirm contactor open command issued** → expected: Coil de-energize commanded within 5 ms
- **Expected outcomes**:
  - `chain_fault_to_open_verified` = true (tolerance exact)

#### `FB2-VER-TMS-000008` — Test: System Qualification (Cell-Voltage Safety Chain) (synthetic_reference)

- **Test type**: `qualification` | **Oracle basis**: `synthetic_assumption`
- **Objective**: Define the system/software qualification verification intent against FSR-001..004 end to end; PLANNING STUB — no execution performed, execution blocked (no qualification harness or target hardware in corpus scope)
- **Preconditions**: Integrated system build available (blocked — not in corpus scope), Qualification environment defined (blocked)
- **Environment**: Target + HIL bench (blocked — unpublished); Unity/CMock; config `conf/unit/app_project_posix.yml`
- **Test cases (steps)**:
  1. **Drive cell-voltage limit violation at system boundary** → expected: FAULT state reached end to end
  2. **Confirm contactor open within FTTI budget** → expected: Timing within 100 ms FTTI
  3. **Confirm DIAG records safety reaction** → expected: Diagnosis entry present
- **Expected outcomes**:
  - `qual_chain_pass` = true (tolerance exact)

#### `FB2-VER-TMS-000009` — Test: Stakeholder Validation (Cell-Voltage Use Cases) (synthetic_reference)

- **Test type**: `validation` | **Oracle basis**: `synthetic_assumption`
- **Objective**: Define the validation intent of cell-voltage stakeholder use cases on the integrated system; PLANNING STUB — no execution performed, execution blocked (no validation environment or operational data in corpus scope)
- **Preconditions**: Stakeholder use cases baselined, Validation environment defined (blocked — not in corpus scope)
- **Environment**: Operational target vehicle/bench (blocked); N/A — operational use; config `conf/unit/app_project_posix.yml`
- **Test cases (steps)**:
  1. **Execute normal-operation charging use case** → expected: No spurious safety reaction
  2. **Execute overvoltage field scenario** → expected: System reaches safe state, stakeholder acceptance criteria met
- **Expected outcomes**:
  - `validation_accepted` = true (tolerance exact)

#### `FB2-VER-TMS-000010` — Test: Component Verification (SOA Monitor + DIAG Callbacks) (synthetic_reference)

- **Test type**: `unit` | **Oracle basis**: `synthetic_assumption`
- **Objective**: Define the component-level verification intent for the SOA monitor plus DIAG callback chain; PLANNING STUB — no execution performed, execution blocked (no component harness in corpus scope)
- **Preconditions**: SOA and DIAG units available as host builds, Component harness defined (blocked — not in corpus scope)
- **Environment**: POSIX host (Linux) — component harness blocked; Unity/CMock; config `conf/unit/app_project_posix.yml`
- **Test cases (steps)**:
  1. **Drive SOA limit violation at component boundary** → expected: DIAG callback invoked with severity
  2. **Confirm occurrence counter and latency fields** → expected: Counter increments within debounce window
  3. **Clear stimulus and confirm recovery** → expected: No latched fault after clear
- **Expected outcomes**:
  - `component_reaction_verified` = true (tolerance exact)

#### `FB2-VER-TMS-000011` — Test: HIL Fault Reaction (Target) (synthetic_reference)

- **Test type**: `system` | **Oracle basis**: `synthetic_assumption`
- **Objective**: Define the HIL verification intent for the cell-voltage safety chain on target hardware; PLANNING STUB — no execution performed, execution blocked (tests/hil placeholder only, no target hardware in corpus scope)
- **Preconditions**: HIL bench available (blocked — unpublished upstream), Target program built with coverage instrumentation (blocked)
- **Environment**: Target TMS570LC4357 + HIL bench (blocked — unpublished); Linked target program; config `tests/hil placeholder (unpublished upstream)`
- **Test cases (steps)**:
  1. **Apply overvoltage stimulus on HIL cell emulator** → expected: AFE path acquires violated sample
  2. **Observe contactor command on target I/O** → expected: Coils de-energized within FTTI
  3. **Collect line/branch coverage on target** → expected: Coverage record retained
- **Expected outcomes**:
  - `hil_reaction_verified` = true (tolerance exact)

## Test Cases

- `FB2-VER-TMS-000001` (as_is): 4 test case(s)
- `FB2-VER-TMS-000002` (as_is): 6 test case(s)
- `FB2-VER-TMS-000003` (as_is): 3 test case(s)
- `FB2-VER-TMS-000004` (as_is): 3 test case(s)
- `FB2-VER-TMS-000005` (as_is): 3 test case(s)
- `FB2-VER-TMS-000001` (synthetic_reference): 3 test case(s)
- `FB2-VER-TMS-000002` (synthetic_reference): 3 test case(s)
- `FB2-VER-TMS-000003` (synthetic_reference): 2 test case(s)
- `FB2-VER-TMS-000004` (synthetic_reference): 3 test case(s)
- `FB2-VER-TMS-000005` (synthetic_reference): 3 test case(s)
- `FB2-VER-TMS-000006` (synthetic_reference): 2 test case(s)
- `FB2-VER-TMS-000007` (synthetic_reference): 3 test case(s)
- `FB2-VER-TMS-000008` (synthetic_reference): 3 test case(s)
- `FB2-VER-TMS-000009` (synthetic_reference): 2 test case(s)
- `FB2-VER-TMS-000010` (synthetic_reference): 3 test case(s)
- `FB2-VER-TMS-000011` (synthetic_reference): 3 test case(s)

**Total system-level test cases**: 49

## Execution Report

##### Execution `FB2-VER-EXE-000001` — Execution: SOA Voltage Limit Test (real macOS host run)

- **Test measure**: `FB2-VER-TMS-000001` | **Execution kind**: `actual_host_run` | **Outcome**: **PASS**
- **Environment**: arm64-apple-darwin27 (Apple Silicon Mac, Darwin 27.0.0); ruby 4.0.7 (2026-09-15 revision 229531a6cf) +PRISM [arm64-darwin27]; tools: ceedling 1.1.9-2209dc2, cexception 1.3.5, clang 17.0.0, cmock 2.7.2, gcc 17.0.0, ruby 4.0.7, unity 2.7.2
- **Evidence refs**: `FB2-VER-TMS-000001`, `tests/unit/app/application/soa/test_soa.c`

##### Execution `FB2-VER-EXE-000002` — Execution: FB2-VER-TMS-000002 (real macOS host run)

- **Test measure**: `FB2-VER-TMS-000002` | **Execution kind**: `actual_host_run` | **Outcome**: **PASS**
- **Environment**: arm64-apple-darwin27 (Apple Silicon Mac, Darwin 27.0.0); ruby 4.0.7 (2026-09-15 revision 229531a6cf) +PRISM [arm64-darwin27]; tools: ceedling 1.1.9-2209dc2, cexception 1.3.5, clang 17.0.0, cmock 2.7.2, gcc 17.0.0, ruby 4.0.7, unity 2.7.2
- **Evidence refs**: `FB2-VER-TMS-000002`, `tests/unit/app/driver/contactor/test_contactor.c`

##### Execution `FB2-VER-EXE-000003` — Execution: FB2-VER-TMS-000003 (real macOS host run)

- **Test measure**: `FB2-VER-TMS-000003` | **Execution kind**: `actual_host_run` | **Outcome**: **PASS**
- **Environment**: arm64-apple-darwin27 (Apple Silicon Mac, Darwin 27.0.0); ruby 4.0.7 (2026-09-15 revision 229531a6cf) +PRISM [arm64-darwin27]; tools: ceedling 1.1.9-2209dc2, cexception 1.3.5, clang 17.0.0, cmock 2.7.2, gcc 17.0.0, ruby 4.0.7, unity 2.7.2
- **Evidence refs**: `FB2-VER-TMS-000003`, `tests/unit/app/driver/afe/api/test_afe_plausibility.c`

##### Execution `FB2-VER-EXE-000004` — Execution: FB2-VER-TMS-000004 (still blocked: HALCoGen unavailable)

- **Test measure**: `FB2-VER-TMS-000004` | **Execution kind**: `none` | **Outcome**: **BLOCKED**
- **Environment**: arm64-apple-darwin27 (Apple Silicon Mac, Darwin 27.0.0); ruby 4.0.7 (2026-09-15 revision 229531a6cf) +PRISM [arm64-darwin27]; tools: ceedling 1.1.9-2209dc2, cexception 1.3.5, clang 17.0.0, cmock 2.7.2, gcc 17.0.0, ruby 4.0.7, unity 2.7.2
- **Evidence refs**: `FB2-VER-TMS-000004`, `tests/unit/app/driver/afe/ltc/6813-1/test_ltc_6813-1.c`

##### Execution `FB2-VER-EXE-000005` — Execution: FB2-VER-TMS-000005 (real macOS host run)

- **Test measure**: `FB2-VER-TMS-000005` | **Execution kind**: `actual_host_run` | **Outcome**: **PASS**
- **Environment**: arm64-apple-darwin27 (Apple Silicon Mac, Darwin 27.0.0); ruby 4.0.7 (2026-09-15 revision 229531a6cf) +PRISM [arm64-darwin27]; tools: ceedling 1.1.9-2209dc2, cexception 1.3.5, clang 17.0.0, cmock 2.7.2, gcc 17.0.0, ruby 4.0.7, unity 2.7.2
- **Evidence refs**: `FB2-VER-TMS-000005`, `tests/unit/app/driver/contactor/test_contactor.c`

##### Execution `FB2-VER-EXE-000006` — Execution: foxBMS 2 host unit test sweep, strict shipped flag set (136 tests, macOS arm64)

- **Test measure**: `FB2-VER-TMS-000001..000005` | **Execution kind**: `actual_host_run` | **Outcome**: **FAIL**
- **Environment**: arm64-apple-darwin27 (Apple Silicon Mac, Darwin 27.0.0); ruby 4.0.7 (2026-09-15 revision 229531a6cf) +PRISM [arm64-darwin27]; tools: ceedling 1.1.9-2209dc2, cexception 1.3.5, clang 17.0.0, cmock 2.7.2, gcc 17.0.0, ruby 4.0.7, unity 2.7.2
- **Evidence refs**: `tests/unit/app/driver/foxmath/test_foxmath.c`, `src/app/engine/database/database.h`, `src/os/freertos/freertos/include/mpu_wrappers.h`

##### Execution `FB2-VER-EXE-000007` — Execution: foxBMS 2 host unit test sweep, extended clang diagnostic set (136 tests, macOS arm64)

- **Test measure**: `FB2-VER-TMS-000001..000005` | **Execution kind**: `actual_host_run` | **Outcome**: **FAIL**
- **Environment**: arm64-apple-darwin27 (Apple Silicon Mac, Darwin 27.0.0); ruby 4.0.7 (2026-09-15 revision 229531a6cf) +PRISM [arm64-darwin27]; tools: ceedling 1.1.9-2209dc2, cexception 1.3.5, clang 17.0.0, cmock 2.7.2, gcc 17.0.0, ruby 4.0.7, unity 2.7.2
- **Evidence refs**: `tests/unit/app/driver/foxmath/test_foxmath.c`, `src/app/engine/database/database.h`, `src/os/freertos/freertos/include/mpu_wrappers.h`

##### Execution `FB2-VER-EXE-000008` — Execution: ALGO moving average (tests/unit/app/application/algorithm/moving_average/test_moving_average.c) - real macOS host run, FAILING

- **Test measure**: `FB2-VER-TMS-000003` | **Execution kind**: `actual_host_run` | **Outcome**: **FAIL**
- **Environment**: arm64-apple-darwin27 (Apple Silicon Mac, Darwin 27.0.0); ruby 4.0.7 (2026-09-15 revision 229531a6cf) +PRISM [arm64-darwin27]; tools: ceedling 1.1.9-2209dc2, cexception 1.3.5, clang 17.0.0, cmock 2.7.2, gcc 17.0.0, ruby 4.0.7, unity 2.7.2
- **Evidence refs**: `tests/unit/app/engine/database/database.h`, `tests/unit/app/application/algorithm/moving_average/test_moving_average.c`

##### Execution `FB2-VER-EXE-000009` — Execution: SOC lookup-table state estimation (tests/unit/app/application/algorithm/state_estimation/soc/lookup-table/test_soc_lookup-table.c) - real macOS host run, FAILING

- **Test measure**: `FB2-VER-TMS-000003` | **Execution kind**: `actual_host_run` | **Outcome**: **FAIL**
- **Environment**: arm64-apple-darwin27 (Apple Silicon Mac, Darwin 27.0.0); ruby 4.0.7 (2026-09-15 revision 229531a6cf) +PRISM [arm64-darwin27]; tools: ceedling 1.1.9-2209dc2, cexception 1.3.5, clang 17.0.0, cmock 2.7.2, gcc 17.0.0, ruby 4.0.7, unity 2.7.2
- **Evidence refs**: `tests/unit/app/engine/database/database.h`, `tests/unit/app/application/algorithm/state_estimation/soc/lookup-table/test_soc_lookup-table.c`

##### Execution `FB2-VER-EXE-000010` — Execution: State estimation initialisation (tests/unit/app/application/algorithm/state_estimation/test_state_estimation.c) - real macOS host run, FAILING

- **Test measure**: `FB2-VER-TMS-000003` | **Execution kind**: `actual_host_run` | **Outcome**: **FAIL**
- **Environment**: arm64-apple-darwin27 (Apple Silicon Mac, Darwin 27.0.0); ruby 4.0.7 (2026-09-15 revision 229531a6cf) +PRISM [arm64-darwin27]; tools: ceedling 1.1.9-2209dc2, cexception 1.3.5, clang 17.0.0, cmock 2.7.2, gcc 17.0.0, ruby 4.0.7, unity 2.7.2
- **Evidence refs**: `tests/unit/app/engine/database/database.h`, `tests/unit/app/application/algorithm/state_estimation/test_state_estimation.c`

##### Execution `FB2-VER-EXE-000011` — Execution: Debug AFE default driver (tests/unit/app/driver/afe/debug/default/test_debug_default.c) - real macOS host run, FAILING

- **Test measure**: `FB2-VER-TMS-000003` | **Execution kind**: `actual_host_run` | **Outcome**: **FAIL**
- **Environment**: arm64-apple-darwin27 (Apple Silicon Mac, Darwin 27.0.0); ruby 4.0.7 (2026-09-15 revision 229531a6cf) +PRISM [arm64-darwin27]; tools: ceedling 1.1.9-2209dc2, cexception 1.3.5, clang 17.0.0, cmock 2.7.2, gcc 17.0.0, ruby 4.0.7, unity 2.7.2
- **Evidence refs**: `tests/unit/app/engine/database/database.h`, `tests/unit/app/driver/afe/debug/default/test_debug_default.c`

##### Execution `FB2-VER-EXE-000012` — Execution: DIAG flag table update (tests/unit/app/engine/config/test_diag_cfg.c) - real macOS host run, FAILING

- **Test measure**: `FB2-VER-TMS-000003` | **Execution kind**: `actual_host_run` | **Outcome**: **FAIL**
- **Environment**: arm64-apple-darwin27 (Apple Silicon Mac, Darwin 27.0.0); ruby 4.0.7 (2026-09-15 revision 229531a6cf) +PRISM [arm64-darwin27]; tools: ceedling 1.1.9-2209dc2, cexception 1.3.5, clang 17.0.0, cmock 2.7.2, gcc 17.0.0, ruby 4.0.7, unity 2.7.2
- **Evidence refs**: `tests/unit/app/engine/database/database.h`, `tests/unit/app/engine/config/test_diag_cfg.c`

##### Execution `FB2-VER-EXE-000013` — Execution: Redundancy layer (tests/unit/app/application/redundancy/test_redundancy.c) - real macOS host run, FAILING

- **Test measure**: `FB2-VER-TMS-000003` | **Execution kind**: `actual_host_run` | **Outcome**: **FAIL**
- **Environment**: arm64-apple-darwin27 (Apple Silicon Mac, Darwin 27.0.0); ruby 4.0.7 (2026-09-15 revision 229531a6cf) +PRISM [arm64-darwin27]; tools: ceedling 1.1.9-2209dc2, cexception 1.3.5, clang 17.0.0, cmock 2.7.2, gcc 17.0.0, ruby 4.0.7, unity 2.7.2
- **Evidence refs**: `tests/unit/app/engine/database/database.h`, `tests/unit/app/application/redundancy/test_redundancy.c`

##### Execution `FB2-VER-EXE-000014` — Execution: DIAG engine (tests/unit/app/engine/diag/test_diag.c) - real macOS host run, FAILING

- **Test measure**: `FB2-VER-TMS-000003` | **Execution kind**: `actual_host_run` | **Outcome**: **FAIL**
- **Environment**: arm64-apple-darwin27 (Apple Silicon Mac, Darwin 27.0.0); ruby 4.0.7 (2026-09-15 revision 229531a6cf) +PRISM [arm64-darwin27]; tools: ceedling 1.1.9-2209dc2, cexception 1.3.5, clang 17.0.0, cmock 2.7.2, gcc 17.0.0, ruby 4.0.7, unity 2.7.2
- **Evidence refs**: `tests/unit/app/engine/database/database.h`, `tests/unit/app/engine/diag/test_diag.c`

##### Execution `FB2-VER-EXE-000001` — Execution: FB2-VER-TMS-000001 (synthetic_fixture)

- **Test measure**: `FB2-VER-TMS-000001` | **Execution kind**: `synthetic_fixture` | **Outcome**: **PASS**
- **Environment**: x86_64 Linux host (simulated); Unity 2.5.2, CMock 2.4.0; tools: cmake 3.22.1, cmock 2.4.0, gcc 11.4.0, unity 2.5.2
- **Evidence refs**: `FB2-VER-TMS-000001`, `tests/unit/app/application/soa/test_soa.c`

##### Execution `FB2-VER-EXE-000002` — Execution: FB2-VER-TMS-000002 (synthetic_fixture)

- **Test measure**: `FB2-VER-TMS-000002` | **Execution kind**: `synthetic_fixture` | **Outcome**: **PASS**
- **Environment**: x86_64 Linux host (simulated); Unity 2.5.2, CMock 2.4.0; tools: cmake 3.22.1, cmock 2.4.0, gcc 11.4.0, unity 2.5.2
- **Evidence refs**: `FB2-VER-TMS-000002`, `tests/unit/app/driver/contactor/test_contactor.c`

##### Execution `FB2-VER-EXE-000003` — Execution: FB2-VER-TMS-000003 (synthetic_fixture)

- **Test measure**: `FB2-VER-TMS-000003` | **Execution kind**: `synthetic_fixture` | **Outcome**: **PASS**
- **Environment**: x86_64 Linux host (simulated); Unity 2.5.2, CMock 2.4.0; tools: cmake 3.22.1, cmock 2.4.0, gcc 11.4.0, unity 2.5.2
- **Evidence refs**: `FB2-VER-TMS-000003`, `tests/unit/app/driver/afe/api/test_afe_plausibility.c`

##### Execution `FB2-VER-EXE-000004` — Execution: FB2-VER-TMS-000004 (synthetic_fixture)

- **Test measure**: `FB2-VER-TMS-000004` | **Execution kind**: `synthetic_fixture` | **Outcome**: **PASS**
- **Environment**: x86_64 Linux host (simulated); Unity 2.5.2, CMock 2.4.0; tools: cmake 3.22.1, cmock 2.4.0, gcc 11.4.0, unity 2.5.2
- **Evidence refs**: `FB2-VER-TMS-000004`

##### Execution `FB2-VER-EXE-000005` — Execution: FB2-VER-TMS-000005 (synthetic_fixture)

- **Test measure**: `FB2-VER-TMS-000005` | **Execution kind**: `synthetic_fixture` | **Outcome**: **PASS**
- **Environment**: x86_64 Linux host (simulated); Unity 2.5.2, CMock 2.4.0; tools: cmake 3.22.1, cmock 2.4.0, gcc 11.4.0, unity 2.5.2
- **Evidence refs**: `FB2-VER-TMS-000005`, `tests/unit/app/driver/afe/ltc/6813-1/test_ltc_6813-1.c`

##### Execution `FB2-VER-EXE-000006` — Execution: FB2-VER-TMS-000006 (synthetic_fixture)

- **Test measure**: `FB2-VER-TMS-000006` | **Execution kind**: `synthetic_fixture` | **Outcome**: **PASS**
- **Environment**: x86_64 Linux host (simulated); Unity 2.5.2, CMock 2.4.0; tools: cmake 3.22.1, cmock 2.4.0, gcc 11.4.0, unity 2.5.2
- **Evidence refs**: `FB2-VER-TMS-000006`

##### Execution `FB2-VER-EXE-000007` — Execution: FB2-VER-TMS-000007 (blocked)

- **Test measure**: `FB2-VER-TMS-000007` | **Execution kind**: `none` | **Outcome**: **BLOCKED**
- **Environment**: POSIX host (Linux) — harness blocked; Unity/CMock; tools: GCC
- **Evidence refs**: `FB2-VER-TMS-000007`

##### Execution `FB2-VER-EXE-000008` — Execution: FB2-VER-TMS-000008 (blocked)

- **Test measure**: `FB2-VER-TMS-000008` | **Execution kind**: `none` | **Outcome**: **BLOCKED**
- **Environment**: Target + HIL bench (blocked); Unity/CMock; tools: GCC
- **Evidence refs**: `FB2-VER-TMS-000008`

##### Execution `FB2-VER-EXE-000009` — Execution: FB2-VER-TMS-000009 (blocked)

- **Test measure**: `FB2-VER-TMS-000009` | **Execution kind**: `none` | **Outcome**: **BLOCKED**
- **Environment**: Operational target vehicle/bench (blocked); N/A — operational use; tools: 
- **Evidence refs**: `FB2-VER-TMS-000009`

##### Execution `FB2-VER-EXE-000010` — Execution: FB2-VER-TMS-000010 (blocked)

- **Test measure**: `FB2-VER-TMS-000010` | **Execution kind**: `none` | **Outcome**: **BLOCKED**
- **Environment**: POSIX host (Linux) — component harness blocked; Unity/CMock; tools: GCC
- **Evidence refs**: `FB2-VER-TMS-000010`

##### Execution `FB2-VER-EXE-000011` — Execution: FB2-VER-TMS-000011 (blocked)

- **Test measure**: `FB2-VER-TMS-000011` | **Execution kind**: `none` | **Outcome**: **BLOCKED**
- **Environment**: Target TMS570LC4357 + HIL bench (blocked — unpublished upstream); Linked target program; tools: GCC
- **Evidence refs**: `FB2-VER-TMS-000011`



---

*Generated: 2026-09-29T10:08:35Z — auto-generated from the machine-verifiable corpus. Regenerate with `python3 docs/artifacts/tools/render_spec_documents.py`.*
