# foxBMS 2 — Software Verification Report

**Document Control**

| Field | Value |
|---|---|
| Project | foxBMS 2 — Battery Management System |
| Document | Software Verification Report |
| Baseline | BAS-REF-001 (commit `308028fb`, tag `v1.11.0`) |
| Profiles | `as_is` (source-grounded) + `synthetic_reference` (hypothetical) |
| Corpus status | `synthetic_ready_with_limitations` |
| Generated | 2026-09-13T02:20:37Z |

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

### Test Cases

- `FB2-VER-TMS-000001` (as_is): 4 test case(s)
- `FB2-VER-TMS-000002` (as_is): 6 test case(s)
**Subtotal test cases**: 10

### Execution Report

##### Execution `FB2-VER-EXE-000001` — Execution: SOA Voltage Limit Test

- **Test measure**: `FB2-VER-TMS-000001` | **Execution kind**: `actual_host_run` | **Outcome**: **PASS**
- **Environment**: x86_64 Linux host; Unity 2.5.2, CMock 2.4.0; tools: cmake 3.22.1, cmock 2.4.0, gcc 11.4.0, unity 2.5.2
- **Evidence refs**: `FB2-VER-TMS-000001`, `tests/unit/app/application/soa/test_soa.c`

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


---

*Generated: 2026-09-13T02:20:37Z — auto-generated from the machine-verifiable corpus. Regenerate with `python3 docs/artifacts/tools/render_spec_documents.py`.*
