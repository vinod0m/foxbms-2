# foxBMS 2 — Software Verification Report

**Document Control**

| Field | Value |
|---|---|
| Project | foxBMS 2 — Battery Management System |
| Document | Software Verification Report |
| Baseline | BAS-REF-001 (commit `308028fb`, tag `v1.11.0`) |
| Profiles | `as_is` (source-grounded) + `synthetic_reference` (hypothetical) |
| Corpus status | `synthetic_ready_with_limitations` |
| Generated | 2026-09-29T17:10:59Z |

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

### Test Cases

- `FB2-VER-TMS-000001` (as_is): 4 test case(s)
- `FB2-VER-TMS-000002` (as_is): 6 test case(s)
- `FB2-VER-TMS-000003` (as_is): 3 test case(s)
- `FB2-VER-TMS-000004` (as_is): 3 test case(s)
- `FB2-VER-TMS-000005` (as_is): 3 test case(s)
- `FB2-VER-TMS-000001` (synthetic_reference): 3 test case(s)
- `FB2-VER-TMS-000002` (synthetic_reference): 3 test case(s)
- `FB2-VER-TMS-000003` (synthetic_reference): 2 test case(s)
- `FB2-VER-TMS-000006` (synthetic_reference): 2 test case(s)
- `FB2-VER-TMS-000010` (synthetic_reference): 3 test case(s)
**Subtotal test cases**: 32

### Execution Report

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

- **Test measure**: `FB2-VER-TMS-000003` | **Execution kind**: `actual_host_run` | **Outcome**: **PASS**
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

##### Execution `FB2-VER-EXE-000015` — Execution: foxBMS 2 SIL host unit-test sweep, all 313 tests (macOS arm64)

- **Test measure**: `FB2-VER-TMS-000001..000005` | **Execution kind**: `actual_host_run` | **Outcome**: **FAIL**
- **Environment**: arm64-apple-darwin27 (Apple Silicon Mac, Darwin 27.0.0); ruby 4.0.7 (2026-09-15 revision 229531a6cf) +PRISM [arm64-darwin27]; tools: ceedling 1.1.9-2209dc2, cexception 1.3.5, clang 17.0.0, cmock 2.7.2, gcc 17.0.0, ruby 4.0.7, unity 2.7.2
- **Evidence refs**: `tests/unit/app/driver/spi/test_spi.c`, `tests/unit/app/driver/mcu/test_mcu.c`, `src/app/driver/spi/spi.c`, `src/app/driver/mcu/mcu.c`

##### Execution `FB2-VER-EXE-000016` — Execution: 200 HALCoGen-blocked tests under the SIL harness (macOS arm64)

- **Test measure**: `FB2-VER-TMS-000004` | **Execution kind**: `actual_host_run` | **Outcome**: **FAIL**
- **Environment**: arm64-apple-darwin27 (Apple Silicon Mac, Darwin 27.0.0); ruby 4.0.7 (2026-09-15 revision 229531a6cf) +PRISM [arm64-darwin27]; tools: ceedling 1.1.9-2209dc2, cexception 1.3.5, clang 17.0.0, cmock 2.7.2, gcc 17.0.0, ruby 4.0.7, unity 2.7.2
- **Evidence refs**: `FB2-VER-EXE-000015`, `tests/unit/app/driver/afe/ltc/6813-1/test_ltc_6813-1.c`

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

### Test Cases

- `FB2-VER-TMS-000007` (synthetic_reference): 3 test case(s)
**Subtotal test cases**: 3

### Execution Report

No `integration` execution artifacts in the corpus — gap (blocked, not fabricated).

## HIL Testing

### Test Specification

No `hil` test specification artifacts in the corpus — **gap** (blocked, not fabricated).

### Test Cases

**Subtotal test cases**: 0

### Execution Report

No target-HIL executions exist in the corpus — per governance policy, actual product evidence = 0 (blocked, not fabricated).

## Static-Analysis Deviance Evidence

The corpus holds **26 deviation records** (`FB2-SW-DEV-*`) mined from in-source Axivion `Style MisraC2012*` suppression annotations. They are the coding-guideline deviance evidence a software verification report is expected to hold. They are **not** verification results: each record documents an observed, in-source justified exception in the pinned implementation, and none of them is a test, a test result, or a coverage claim.

| Record | Rule | Suppression | Affected lines | File | Symbol |
|---|---|---|---|---|---|
| `FB2-SW-DEV-000001` | Directive-4.1 (advisory_directive) | disable_enable_block | `658-662,669-673` | `src/app/application/redundancy/redundancy.c` | MRC_ValidateBatteryVoltageMeasurement |
| `FB2-SW-DEV-000002` | 1.2 (rule) | disable_enable_block | `86-91` | `src/app/driver/afe/adi/common/ades183x/adi_ades183x.c` | adi_bufferRxPec / adi_bufferTxPec |
| `FB2-SW-DEV-000003` | 1.2 (rule) | disable_enable_block | `110-115` | `src/app/driver/afe/ltc/6806/ltc_6806.c` | ltc_RxPecBuffer / ltc_TxPecBuffer |
| `FB2-SW-DEV-000004` | 1.2 (rule) | disable_enable_block | `112-117` | `src/app/driver/afe/ltc/6813-1/ltc_6813-1.c` | ltc_RxPecBuffer / ltc_TxPecBuffer |
| `FB2-SW-DEV-000005` | 2.5 (rule) | disable_enable_block | `80-332` | `src/app/driver/afe/maxim/common/mxm_41b_register_map.h` | module level (MXM_41B register address defines) |
| `FB2-SW-DEV-000006` | 2.5 (rule) | disable_enable_block | `70-110` | `src/app/driver/afe/maxim/common/mxm_bit_extract.h` | module level (MXM_41B_REG_BIT_VALUE defines) |
| `FB2-SW-DEV-000007` | 2.2 (rule) | disable_enable_block | `279-562` | `src/app/driver/can/can.c` | CAN_ConfigureRxMailboxesForExtendedIdentifiers |
| `FB2-SW-DEV-000008` | 2.5 (rule) | disable_enable_block | `73-97` | `src/app/driver/config/pex_cfg.h` | PEX_PORT_EXPANDER1 / PEX_PORT_EXPANDER2 / PEX_PORT_EXPANDER3 and PEX_PORT_0_PIN_0 .. PEX_PORT_1_PIN_7 |
| `FB2-SW-DEV-000009` | 1.2 (rule) | disable_enable_block | `581-584` | `src/app/driver/emac/emac.c` | EMAC_TxInterruptServiceRoutine |
| `FB2-SW-DEV-000010` | 1.2 (rule) | disable_enable_block | `597-600` | `src/app/driver/emac/emac.c` | EMAC_RxInterruptServiceRoutine |
| `FB2-SW-DEV-000011` | 1.1 (rule) | disable_enable_block | `454-456` | `src/app/driver/i2c/i2c.c` | I2C_ReadDma |
| `FB2-SW-DEV-000012` | 1.1 (rule) | disable_enable_block | `548-550` | `src/app/driver/i2c/i2c.c` | I2C_WriteDma |
| `FB2-SW-DEV-000013` | 1.1 (rule) | disable_enable_block | `645-647,698-700` | `src/app/driver/i2c/i2c.c` | I2C_WriteReadDma |
| `FB2-SW-DEV-000014` | 21.10 (rule) | disable_enable_block | `70-653` | `src/app/driver/rtc/rtc.c` | module level (whole rtc.c module body, Disable at line 70 / matching Enable at line 653) |
| `FB2-SW-DEV-000015` | 1.2 (rule) | disable_enable_block | `77-84` | `src/app/driver/rtc/rtc.c` | rtc_i2cWriteBuffer / rtc_i2cReadBuffer |
| `FB2-SW-DEV-000016` | 2.2 (rule) | disable_enable_block | `79-89,93-103,107-117,121-131,135-145,149-159,163-173` | `src/app/driver/spi/spi_cfg-helper.h` | module level (SPI_HARDWARE_CHIP_SELECT_*_ACTIVE defines) |
| `FB2-SW-DEV-000017` | Directive-1.1 (advisory_directive) | disable_enable_block | `97-120` | `src/app/main/include/fassert.h` | FAS_DisableInterrupts |
| `FB2-SW-DEV-000018` | Directive-1.1 (advisory_directive) | disable_enable_block | `66-119` | `src/app/main/include/fsystem.h` | FSYS_RaisePrivilege |
| `FB2-SW-DEV-000019` | 10.4 (rule) | disable_enable_block | `94-102` | `src/app/main/include/general.h` | module level (FAS_STATIC_ASSERT datatype invariants) |
| `FB2-SW-DEV-000020` | 20.10 (rule) | disable_enable_block | `212-214` | `src/app/main/include/general.h` | GEN_REPEAT_Ux |
| `FB2-SW-DEV-000021` | Directive-4.9 (advisory_directive) | disable_enable_block | `248-255` | `src/app/main/include/general.h` | GEN_STRIP |
| `FB2-SW-DEV-000022` | 11.4 (rule) | disable_enable_block | `68-402` | `src/bootloader/driver/config/flash_cfg.c` | module level (FLASH_FLASH_BANK_s / FLASH_FLASH_SECTOR_s tables) |
| `FB2-SW-DEV-000023` | Directive-4.1 (advisory_directive) | disable_enable_block | `237-245` | `src/bootloader/driver/crc/crc.c` | CRC_SemiAutoCrcCalculation |
| `FB2-SW-DEV-000024` | Directive-1.1 (advisory_directive) | disable_enable_block | `97-120` | `src/bootloader/main/include/fassert.h` | FAS_DisableInterrupts |
| `FB2-SW-DEV-000025` | Directive-1.1 (advisory_directive) | disable_enable_block | `101-145` | `src/bootloader/main/include/fsystem.h` | FSYS_RaisePrivilegeToSystemModeSWI |
| `FB2-SW-DEV-000026` | 10.4 (rule) | disable_enable_block | `68-76` | `src/bootloader/main/include/general.h` | module level (FAS_STATIC_ASSERT datatype invariants) |

Every record carries `lifecycle_status: draft`, `human_approval_status: pending`, `production_authorized: false` and `product_verification_credit: false`; the table above records their existence and location only and asserts no conformance, no tool qualification and no completed ISO 26262 or ASPICE assessment.


---

*Generated: 2026-09-29T17:10:59Z — auto-generated from the machine-verifiable corpus. Regenerate with `python3 docs/artifacts/tools/render_spec_documents.py`.*
