# foxBMS 2 — Software Verification Report

**Document Control**

| Field | Value |
|---|---|
| Project | foxBMS 2 — Battery Management System |
| Document | Software Verification Report |
| Baseline | BAS-REF-001 (commit `308028fb`, tag `v1.11.0`) |
| Profiles | `as_is` (source-grounded) + `synthetic_reference` (hypothetical) |
| Corpus status | `synthetic_ready_with_limitations` |
| Generated | 2026-09-13T15:17:46Z |

## Scope

Software verification by level: (1) reverse-engineered unit verification evidence — the full per-module unit-test inventory from `tests/unit/app/`; (2) corpus test levels (unit, component, integration, HIL) with cases, execution reports, execution_kind labeled; actual vs synthetic distinguished.

## Reverse-Engineered Unit Verification Evidence

The repository carries **313 C unit test files** (Ceedling/Unity, host-based) in `tests/unit/app/`. Per-module inventory:

| Module | Unit test files | Count |
|---|---|---|
| `application/algorithm` | `test_algorithm.c` | 1 |
| `application/bal` | `test_bal.c` | 1 |
| `application/bms` | `test_bms.c` | 1 |
| `application/ethernet` | `test_ethernet.c`, `test_ethernet_freertos.c` | 2 |
| `application/plausibility` | `test_plausibility.c` | 1 |
| `application/redundancy` | `test_redundancy.c` | 1 |
| `application/soa` | `test_soa.c` | 1 |
| `driver/adc` | `test_adc.c` | 1 |
| `driver/can` | `test_can.c`, `test_can_1.c`, `test_can_2.c`, `test_can_can_message_notification.c` | 4 |
| `driver/contactor` | `test_contactor.c` | 1 |
| `driver/crc` | `test_crc.c` | 1 |
| `driver/dma` | `test_dma.c`, `test_dma_dma_group_a_notification.c`, `test_dma_nxp.c`, `test_dma_uart.c` | 4 |
| `driver/emac` | `test_emac-low-level.c`, `test_emac.c` | 2 |
| `driver/foxmath` | `test_foxmath.c`, `test_utils.c` | 2 |
| `driver/fram` | `test_fram.c` | 1 |
| `driver/htsensor` | `test_htsensor.c` | 1 |
| `driver/i2c` | `test_i2c.c` | 1 |
| `driver/imd` | `test_imd.c` | 1 |
| `driver/interlock` | `test_interlock.c` | 1 |
| `driver/io` | `test_io.c` | 1 |
| `driver/led` | `test_led.c` | 1 |
| `driver/mcu` | `test_mcu.c` | 1 |
| `driver/meas` | `test_meas.c` | 1 |
| `driver/pex` | `test_pex.c` | 1 |
| `driver/phy` | `test_dp83869.c` | 1 |
| `driver/pwm` | `test_pwm.c` | 1 |
| `driver/rtc` | `test_rtc.c` | 1 |
| `driver/sbc` | `test_nxpfs85xx.c`, `test_nxpfs85xx_mcu_spi_transfer_data.c`, `test_sbc.c` | 3 |
| `driver/spi` | `test_spi.c`, `test_spi_adi.c`, `test_spi_debug.c`, `test_spi_ltc.c`, `test_spi_mxm.c`, `test_spi_nxp.c` … | 9 |
| `driver/sps` | `test_sps.c` | 1 |
| `driver/ts` | `test_beta.c` | 1 |
| `driver/uart` | `test_uart.c`, `test_uart_sci_notification.c` | 2 |
| `engine/database` | `test_database.c`, `test_database_helper.c` | 2 |
| `engine/diag` | `test_diag.c` | 1 |
| `engine/hw_info` | `test_master_info.c` | 1 |
| `engine/sys` | `test_reset.c`, `test_sys.c` | 2 |
| `engine/sys_mon` | `test_sys_mon.c` | 1 |
| `task/ftask` | `test_ftask.c`, `test_ftask_emac.c` | 2 |
| `task/os` | `test_os.c` | 1 |
| `task/timer` | `test_timer.c` | 1 |

**Coverage of the module inventory**: 40/40 modules have direct unit tests; config files are covered by `*/config` test folders (e.g. `tests/unit/app/application/config/`, `driver/config/`, `engine/config/`, `task/config/`).

CI enforces the run of these tests for every revision; the coverage report MUST reach 100% line and branch coverage (`docs/developer-manual/software/software-testing.rst`, `docs/software/unit-tests/unit-tests.rst`).

## Unit Testing

### Test Specification

Upstream `verifies` links per test measure (`result_of` execution links in Execution Report). Full requirement chain above each measure: `HAZ-000001` ← `SGO-000001` (`LNK-001`) ← FSR (`LNK-002/003/004`, `LNK-021` synthetic FSR-004) ← TSR/SWR allocation (`LNK-005..010`).

| Test measure | Verifies (`verifies` links) |
|---|---|
| `FB2-VER-TMS-000001` (as_is) | `FSR-000002` + `SWR-000002` (`LNK-014/015`) |
| `FB2-VER-TMS-000002` (as_is) | `FSR-000003` + `SWR-000003` (`LNK-016/017`) |
| `FB2-VER-TMS-000003` (as_is) | `FSR-000001` + `SWR-000001` (`LNK-021/022`) |
| `FB2-VER-TMS-000004` (as_is) | `TSR-000001` + `TSR-000002` (`LNK-023/024`) |
| `FB2-VER-TMS-000005` (as_is) | `TSR-000003` (`LNK-025`) |
| `FB2-VER-TMS-000001` (synthetic) | `FSR-000002` + `SWR-000002` (`LNK-022/023`) |
| `FB2-VER-TMS-000002` (synthetic) | `FSR-000003` + `SWR-000003` (`LNK-024/025`) |
| `FB2-VER-TMS-000003` (synthetic) | `FSR-000001` + `SWR-000001` + `TSR-000001` (`LNK-026/027/028`) |
| `FB2-VER-TMS-000004` (synthetic) | `FSR-000004` + `TSR-000004` (`LNK-029/030`) |
| `FB2-VER-TMS-000005` (synthetic) | `TSR-000002` (`LNK-031`) |
| `FB2-VER-TMS-000006` (synthetic) | `TSR-000003` (`LNK-032`) |
| `FB2-VER-TMS-000007` (synthetic, draft stub) | `SWR-000001/002/003` (`LNK-039/040/041`) |
| `FB2-VER-TMS-000008` (synthetic, draft stub) | `FSR-000001/002/003/004` (`LNK-042/043/044/045`) |
| `FB2-VER-TMS-000009` (synthetic, draft stub) | `SGO-000001` + `SCO-000001` (`LNK-046/047`, `validates`) |

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

#### `FB2-VER-TMS-000007` — Test: Software Integration Chain (synthetic_reference, draft planning stub)

- **Test type**: `integration` | **Oracle basis**: `synthetic_assumption`
- **Objective**: Define the software integration verification intent for the SOA-database-contactor chain; no execution performed (harness blocked)
- **Preconditions**: SOA, database and contactor units available as host builds; integration harness defined (blocked)
- **Environment**: POSIX host (Linux); Unity/CMock; config `conf/unit/app_project_posix.yml`
- **Test cases (steps)**:
  1. **Publish violated cell voltage set to database via MEAS path** → expected: SOA reads violated set within task cycle
  2. **Confirm SOA fault request propagates to BMS state machine** → expected: FAULT state entered
  3. **Confirm contactor open command issued** → expected: Coil de-energize commanded within 5 ms
- **Expected outcomes**:
  - `chain_fault_to_open_verified` = true (tolerance exact)

#### `FB2-VER-TMS-000008` — Test: System Qualification (synthetic_reference, draft planning stub)

- **Test type**: `qualification` | **Oracle basis**: `synthetic_assumption`
- **Objective**: Define the system/software qualification verification intent against FSR-001..004 end to end; no execution performed (harness/target blocked)
- **Preconditions**: Integrated system build available (blocked); qualification environment defined (blocked)
- **Environment**: Target + HIL bench (blocked — unpublished); Unity/CMock
- **Test cases (steps)**:
  1. **Drive cell-voltage limit violation at system boundary** → expected: FAULT state reached end to end
  2. **Confirm contactor open within FTTI budget** → expected: Timing within 100 ms FTTI
  3. **Confirm DIAG records safety reaction** → expected: Diagnosis entry present
- **Expected outcomes**:
  - `qual_chain_pass` = true (tolerance exact)

#### `FB2-VER-TMS-000009` — Test: Stakeholder Validation (synthetic_reference, draft planning stub)

- **Test type**: `validation` | **Oracle basis**: `synthetic_assumption`
- **Objective**: Define the validation intent of cell-voltage stakeholder use cases; no execution performed (environment blocked)
- **Preconditions**: Stakeholder use cases baselined; validation environment defined (blocked)
- **Environment**: Operational target vehicle/bench (blocked)
- **Test cases (steps)**:
  1. **Execute normal-operation charging use case** → expected: No spurious safety reaction
  2. **Execute overvoltage field scenario** → expected: System reaches safe state, stakeholder acceptance criteria met
- **Expected outcomes**:
  - `validation_accepted` = true (tolerance exact)

### Test Cases

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
- `FB2-VER-TMS-000007` (synthetic_reference, draft stub): 3 test case(s)
- `FB2-VER-TMS-000008` (synthetic_reference, draft stub): 3 test case(s)
- `FB2-VER-TMS-000009` (synthetic_reference, draft stub): 2 test case(s)
**Subtotal test cases**: 43

### Execution Report

##### Execution `FB2-VER-EXE-000001` — Execution: SOA Voltage Limit Test

- **Test measure**: `FB2-VER-TMS-000001` | **Execution kind**: `actual_host_run` | **Outcome**: **PASS**
- **Environment**: x86_64 Linux host; Unity 2.5.2, CMock 2.4.0; tools: cmake 3.22.1, cmock 2.4.0, gcc 11.4.0, unity 2.5.2
- **Evidence refs**: `FB2-VER-TMS-000001`, `tests/unit/app/application/soa/test_soa.c`

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

## Component Testing

### Test Specification

No `component` test specification artifacts in the corpus — **gap** (blocked, not fabricated).

### Test Cases

**Subtotal test cases**: 0

### Execution Report

No `component` execution artifacts in the corpus — gap (blocked, not fabricated).

## Integration Testing

### Test Specification

No `integration` test specification artifacts in the corpus — **gap** (blocked, not fabricated).

### Test Cases

**Subtotal test cases**: 0

### Execution Report

No `integration` execution artifacts in the corpus — gap (blocked, not fabricated).

## HIL Testing

### Test Specification

No `hil` test specification artifacts in the corpus — **gap** (blocked, not fabricated).

### Test Cases

**Subtotal test cases**: 0

### Execution Report

No target-HIL executions exist in the corpus — per governance policy, actual product evidence = 0 (blocked, not fabricated).

## Execution Traceability and Evidence Limits

`result_of` links (execution → test measure): as_is `FB2-VER-EXE-000001` → `FB2-VER-TMS-000001` (`FB2-LNK-SAF-000018`); synthetic `FB2-VER-EXE-000001..000006` → `FB2-VER-TMS-000001..000006` (`FB2-LNK-SAF-000033..038`).

- as_is `actual_host_run` PASS (`FB2-VER-EXE-000001`) is not independently substantiated: log/coverage hashes are `sha256:placeholder`, `output_hashes` empty, per-run logs not retained. `FB2-VER-TMS-000002` through `FB2-VER-TMS-000005` have no execution records — no execution credit inferred.
- All synthetic executions are `synthetic_fixture` PASS results demonstrating corpus structure only (`product_verification_credit: false`, `human_approval_status: pending`).
- Planning stubs `FB2-VER-TMS-000007` (integration), `FB2-VER-TMS-000008` (qualification), `FB2-VER-TMS-000009` (validation) have `verifies`/`validates` links but no execution records. Component-level measures remain absent; component, integration, and HIL executions are all zero (blocked, not fabricated).

---

*Generated: 2026-09-13T15:17:46Z — auto-generated from the machine-verifiable corpus. Regenerate with `python3 docs/artifacts/tools/render_spec_documents.py`.*
