# foxBMS 2 — System Requirements Specification

**Document Control**

| Field | Value |
|---|---|
| Project | foxBMS 2 — Battery Management System |
| Document | System Requirements Specification |
| Baseline | BAS-REF-001 (commit `308028fb`, tag `v1.11.0`) |
| Profiles | `as_is` (source-grounded) + `synthetic_reference` (hypothetical) |
| Corpus status | `synthetic_ready_with_limitations` |
| Generated | 2026-09-13T04:11:53Z |

## Scope

System-level requirements: safety goals and functional safety requirements (FSRs) of both corpus profiles with full attribute sets, plus system requirements reverse-engineered from the implementation (SOA limits, diagnosis entries, timing budgets, communication).

## Reverse-Engineered System Requirements (implementation-grounded)

The following system requirements are extracted from the actual repository configuration and code. They hold for the reference build; each row carries its repository anchor.

### Safe Operating Area Limits

Source: `src/app/application/config/battery_cell_cfg.h`, `battery_system_cfg.h`; evaluated by `src/app/application/soa/soa.c`. Three error levels per parameter: MOL (maximum operating limit), RSL (recommended safety limit), MSL (maximum safety limit — opens contactors).

| Parameter | MOL | RSL | MSL | Unit | Anchor |
|---|---|---|---|---|---|
| Cell voltage, maximum | 2720 | 2750 | 2800 | mV | `BC_VOLTAGE_MAX_MOL_mV`-family |
| Cell voltage, minimum | 1580 | 1550 | 1500 | mV | `BC_VOLTAGE_MIN_MOL_mV`-family |
| Cell temperature, charge, maximum | 350 | 400 | 450 | 0.1 °C | `BC_TEMPERATURE_MAX_CHARGE_MOL_ddegC`-family |
| Cell temperature, charge, minimum | -100 | -150 | -200 | 0.1 °C | `BC_TEMPERATURE_MIN_CHARGE_MOL_ddegC`-family |
| Cell temperature, discharge, maximum | 450 | 500 | 550 | 0.1 °C | `BC_TEMPERATURE_MAX_DISCHARGE_MOL_ddegC`-family |
| Cell temperature, discharge, minimum | -100 | -150 | -200 | 0.1 °C | `BC_TEMPERATURE_MIN_DISCHARGE_MOL_ddegC`-family |
| Cell current, charge, maximum | 170000 | 175000 | 180000 | mA | `BC_CURRENT_MAX_CHARGE_MOL_mA`-family |
| Cell current, discharge, maximum | 170000 | 175000 | 180000 | mA | `BC_CURRENT_MAX_DISCHARGE_MOL_mA`-family |
| Pack current, maximum | — | — | ? | mA | `BS_MAXIMUM_PACK_CURRENT_mA` |
| Main contactor break current | — | — | 3500 | mA | `BS_MAIN_CONTACTORS_MAXIMUM_BREAK_CURRENT_mA` |
| Main fuse trigger duration | — | — | 3000 | ms | `BS_MAIN_FUSE_MAXIMUM_TRIGGER_DURATION_ms` |

Reference cell: nominal 2500 mV (`BC_VOLTAGE_NOMINAL_mV`, LFP-class cell), 18 cell blocks total.

### Diagnosis and Error Handling Requirements

The diagnosis engine tracks **85 diagnosis entries** (`DIAG_ID_*` in `src/app/engine/config/diag_cfg.h`), each with severity (OK/WARNING/ERROR/FATAL), enabling, occurrence counter, latency and delay (`diag_diagnosisIdConfiguration` in `diag_cfg.c`). Error-table documentation: `docs/system/system-error-table.csv`. Selected groups:

- **AFE integrity**: `DIAG_ID_AFE_SPI`, `DIAG_ID_AFE_COMMUNICATION_INTEGRITY`, `DIAG_ID_AFE_MUX`, `DIAG_ID_AFE_CONFIG`, `DIAG_ID_AFE_OPEN_WIRE`, `DIAG_ID_AFE_ALARM`, `DIAG_ID_AFE_CELL_VOLTAGE_MEAS_ERROR`, `DIAG_ID_AFE_CELL_TEMPERATURE_MEAS_ERROR`
- **Cell voltage SOA**: `DIAG_ID_CELL_VOLTAGE_OVERVOLTAGE_MSL`, `DIAG_ID_CELL_VOLTAGE_OVERVOLTAGE_RSL`, `DIAG_ID_CELL_VOLTAGE_OVERVOLTAGE_MOL`, `DIAG_ID_CELL_VOLTAGE_UNDERVOLTAGE_MSL`, `DIAG_ID_CELL_VOLTAGE_UNDERVOLTAGE_RSL`, `DIAG_ID_CELL_VOLTAGE_UNDERVOLTAGE_MOL`
- **Temperature SOA**: `DIAG_ID_TEMP_OVERTEMPERATURE_CHARGE_MSL`, `DIAG_ID_TEMP_OVERTEMPERATURE_CHARGE_RSL`, `DIAG_ID_TEMP_OVERTEMPERATURE_CHARGE_MOL`, `DIAG_ID_TEMP_UNDERTEMPERATURE_DISCHARGE_MSL`, `DIAG_ID_TEMP_OVERTEMPERATURE_DISCHARGE_MSL`
- **Overcurrent**: `DIAG_ID_OVERCURRENT_CHARGE_CELL_MSL`, `DIAG_ID_OVERCURRENT_DISCHARGE_CELL_MSL`, `DIAG_ID_STRING_OVERCURRENT_CHARGE_MSL`, `DIAG_ID_STRING_OVERCURRENT_DISCHARGE_MSL`, `DIAG_ID_PACK_OVERCURRENT_CHARGE_MSL`, `DIAG_ID_PACK_OVERCURRENT_DISCHARGE_MSL`, `DIAG_ID_CURRENT_ON_OPEN_STRING`
- **Current sensor**: `DIAG_ID_CURRENT_SENSOR_RESPONDING`, `DIAG_ID_CURRENT_SENSOR_CC_RESPONDING`, `DIAG_ID_CURRENT_SENSOR_EC_RESPONDING`, `DIAG_ID_CURRENT_MEASUREMENT_TIMEOUT`, `DIAG_ID_CURRENT_MEASUREMENT_ERROR`, `DIAG_ID_CURRENT_SENSOR_V1_MEASUREMENT_TIMEOUT`, `DIAG_ID_POWER_MEASUREMENT_ERROR`
- **Plausibility / redundancy**: `DIAG_ID_PLAUSIBILITY_CELL_VOLTAGE`, `DIAG_ID_PLAUSIBILITY_CELL_TEMP`, `DIAG_ID_PLAUSIBILITY_CELL_VOLTAGE_SPREAD`, `DIAG_ID_PLAUSIBILITY_CELL_TEMPERATURE_SPREAD`, `DIAG_ID_PLAUSIBILITY_PACK_VOLTAGE`, `DIAG_ID_BASE_CELL_VOLTAGE_MEASUREMENT_TIMEOUT`, `DIAG_ID_REDUNDANCY0_CELL_VOLTAGE_MEASUREMENT_TIMEOUT`
- **Contactor / interlock / SBC**: `DIAG_ID_INTERLOCK_FEEDBACK`, `DIAG_ID_STRING_MINUS_CONTACTOR_FEEDBACK`, `DIAG_ID_STRING_PLUS_CONTACTOR_FEEDBACK`, `DIAG_ID_PRECHARGE_CONTACTOR_FEEDBACK`, `DIAG_ID_SBC_FIN_ERROR`, `DIAG_ID_SBC_RSTB_ERROR`, `DIAG_ID_SUPPLY_VOLTAGE_CLAMP_30C_LOST`
- **CAN**: `DIAG_ID_CAN_TIMING`, `DIAG_ID_CAN_RX_QUEUE_FULL`, `DIAG_ID_CAN_TX_QUEUE_FULL`
- **Insulation (IMD)**: `DIAG_ID_INSULATION_MEASUREMENT_VALID`, `DIAG_ID_LOW_INSULATION_RESISTANCE_ERROR`, `DIAG_ID_LOW_INSULATION_RESISTANCE_WARNING`, `DIAG_ID_INSULATION_GROUND_ERROR`
- **Other**: `DIAG_ID_DEEP_DISCHARGE_DETECTED`, `DIAG_ID_ALERT_MODE`, `DIAG_ID_AEROSOL_ALERT`, `DIAG_ID_SYSTEM_MONITORING`, `DIAG_ID_I2C_PEX_ERROR`, `DIAG_ID_FRAM_READ_CRC_ERROR`, `DIAG_ID_RTC_CLOCK_INTEGRITY_ERROR`

MSL violations set fatal-error-linked diagnosis entries that force the BMS state machine into `BMS_FSM_STATE_ERROR` → `BMS_FSM_STATE_OPEN_CONTACTORS`.

### Measurement and Timing Requirements

| Requirement | Value | Anchor |
|---|---|---|
| Current measurement response timeout | 200 ms | `BS_CURRENT_MEASUREMENT_RESPONSE_TIMEOUT_ms` |
| Coulomb counting response timeout | 2000 ms | `BS_COULOMB_COUNTING_MEASUREMENT_RESPONSE_TIMEOUT_ms` |
| Energy counting response timeout | 2000 ms | `BS_ENERGY_COUNTING_MEASUREMENT_RESPONSE_TIMEOUT_ms` |
| BMS state machine task context | 10 ms | `BMS_STATEMACHINE_TASK_CYCLE_CONTEXT_MS` (`bms_cfg.h`) |
| Temp sensors per module | 8 | `BS_NR_OF_TEMP_SENSORS_PER_MODULE` |
| Task model | 1 ms / 10 ms / 100 ms / 100 ms-algorithm cyclic + continuous I2C, engine | `src/app/task/ftask/ftask.c`, `docs/software/structure/operating-system-configuration.rst` |

### Communication Requirements

- **CAN**: 41 messages defined in `tools/dbc/foxbms.dbc` (e.g. `AFE_CellVoltages`, `AFE_CellTemperatures`, `f_BmsState`, `f_BmsStateRequest`, `f_BmsFatalError`); implemented by `src/app/driver/can/`.
- **Ethernet**: plain TCP/IP stack (FreeRTOS+TCP) for user-defined application tasks (`src/app/application/ethernet/`), echo server as reference.
- **AFE daisy-chain**: SPI-based interface to BMS-Slaves via BMS-Interface board (supported AFEs: adi (ades1830), ltc (6804-1, 6806, 6811-1, 6812-1, 6813-1), maxim (max17852), nxp (mc33775a), ti (dummy)).

## Profile: `as_is`

### Safety Goals

#### `FB2-SAF-SGO-000001` — Cell Voltage Safety Goal

- **Statement**: The BMS shall detect cell voltage limit violations and open HV contactors within the fault tolerant time interval (FTTI = 100 ms) to prevent cell overvoltage/undervoltage hazardous events.
- **Rationale**: Hazard mitigation for FB2-SAF-HAZ-000001
- **ASIL**: `ASIL_D`
- **FTTI (total)**: 100 ms
- **Safe state**: HV contactors open, charging disabled
- **Degraded state**: Derated charging, balancing disabled
- **Source references**: `FB2-SRC-COD-000004`, `FB2-SRC-COD-000005`, `FB2-SRC-COD-000006`
- **Assumption references**: `FB2-ASM-001`, `FB2-ASM-002`, `FB2-ASM-003`

### Functional Safety Requirements

#### `FB2-SAF-FSR-000001` — FSR: Cell Voltage Acquisition and Validation

- **Statement**: The BMS shall acquire all cell voltages from AFE slaves at a minimum rate of 20 Hz with PEC/CRC validation, and publish validated data to the database within 25 ms of acquisition trigger.
- **Rationale**: Required for SOA monitoring to detect overvoltage/undervoltage within FTTI
- **ASIL**: `ASIL_D`
- **Safety goal reference**: `FB2-SAF-SGO-000001`
- **Acceptance criteria**:
  - All cell voltages acquired: Cell count match ≤ 100% %
  - Acquisition period: Period ≤ 50 ms
  - PEC/CRC validation: Error detection before database write ≤ 100% %
  - Database publish latency: Time from SPI complete to database write ≤ 25 ms
- **Conditions/modes**: `NORMAL`, `CHARGING`, `PRECHARGE`, `DERATING`
- **Source references**: `FB2-SRC-COD-000001`, `FB2-SRC-COD-000002`, `FB2-SRC-COD-000021`, `FB2-SRC-COD-000023`
- **Assumption references**: `FB2-ASM-001` (Lithium-ion cell chemistry with nominal voltage 3.7V, operat...), `FB2-ASM-004` (AFE SPI communication latency < 5 ms (including DMA transfer...), `FB2-ASM-005` (Cell voltage measurement noise follows Gaussian distribution...)

#### `FB2-SAF-FSR-000002` — FSR: SOA Voltage Limit Monitoring with Debounce

- **Statement**: The BMS shall monitor each cell voltage against configured minimum and maximum limits with a debounce of 2 consecutive violations within 100 ms, and classify violations within 5 ms of data availability, triggering FAULT state request on confirmed violation.
- **Rationale**: SOA monitoring must detect limit violations fast enough to meet FTTI
- **ASIL**: `ASIL_D`
- **Safety goal reference**: `FB2-SAF-SGO-000001`
- **Acceptance criteria**:
  - Limit check latency: Time from database read to violation classification ≤ 5 ms
  - Limit accuracy: Threshold comparison accuracy ≤ 1 mV
  - Debounce filtering: False positive rate ≤ 0 events/hour
- **Conditions/modes**: `NORMAL`, `CHARGING`, `PRECHARGE`, `DERATING`
- **Source references**: `FB2-SRC-COD-000004`, `FB2-SRC-COD-000005`, `FB2-SRC-COD-000006`
- **Assumption references**: `FB2-ASM-001` (Lithium-ion cell chemistry with nominal voltage 3.7V, operat...), `FB2-ASM-005` (Cell voltage measurement noise follows Gaussian distribution...), `FB2-ASM-006` (Contactor mechanical opening time <= 30 ms (worst case) at -...)

#### `FB2-SAF-FSR-000003` — FSR: Contactor Opening on SOA Violation

- **Statement**: The BMS shall open all HV contactors within 30 ms of FAULT state request from SOA/DIAG, with auxiliary feedback confirmation within 5 ms of coil de-energization.
- **Rationale**: Contactor opening is the primary risk reduction measure; must complete within FTTI budget
- **ASIL**: `ASIL_D`
- **Safety goal reference**: `FB2-SAF-SGO-000001`
- **Acceptance criteria**:
  - Contactor open latency: Time from FAULT request to contactor feedback open ≤ 30 ms
  - Feedback verification: Auxiliary contact confirmation ≤ 100% %
  - Weld detection: Weld detection latency ≤ 100 ms
- **Conditions/modes**: `NORMAL`, `CHARGING`, `PRECHARGE`, `DERATING`, `FAULT`
- **Source references**: `FB2-SRC-COD-000007`, `FB2-SRC-COD-000008`, `FB2-SRC-COD-000009`, `FB2-SRC-COD-000013`
- **Assumption references**: `FB2-ASM-001` (Lithium-ion cell chemistry with nominal voltage 3.7V, operat...), `FB2-ASM-006` (Contactor mechanical opening time <= 30 ms (worst case) at -...), `FB2-ASM-007` (SBC (FS85xx) watchdog is independent of main MCU and can tri...)

## Profile: `synthetic_reference`

### Safety Goals

#### `FB2-SAF-SGO-000001` — Cell Voltage Safety Goal

- **Statement**: The BMS shall detect cell voltage limit violations and open all HV contactors within the fault tolerant time interval (FTTI = 100 ms) to prevent cell overvoltage/undervoltage hazardous events, with a target diagnostic test interval of 10 ms and a target contactor opening time of 30 ms.
- **Rationale**: Hazard mitigation for FB2-SAF-HAZ-000001
- **ASIL**: `ASIL_D`
- **FTTI (total)**: 100 ms
- **Timing budget allocation**: `afe_acquisition_ms`=25ms, `contactor_command_ms`=5ms, `contactor_mechanical_ms`=30ms, `database_publish_ms`=3ms, `fault_classification_ms`=2ms, `feedback_verification_ms`=5ms, `margin_ms`=20ms, `pec_validation_ms`=2ms, `soa_limit_check_ms`=5ms, `spi_transfer_ms`=5ms, `sys_state_transition_ms`=3ms
- **Safe state**: All HV contactors open, charging disabled, propulsion disabled, fault logged
- **Degraded state**: Derated charging (0.1C), reduced discharge (0.5C), enhanced monitoring (1 Hz)
- **Source references**: `FB2-SRC-COD-000004`, `FB2-SRC-COD-000005`, `FB2-SRC-COD-000006`
- **Assumption references**: `FB2-ASM-001`, `FB2-ASM-002`, `FB2-ASM-003`, `FB2-ASM-004`

### Functional Safety Requirements

#### `FB2-SAF-FSR-000001` — FSR: Cell Voltage Acquisition and Validation

- **Statement**: The BMS shall acquire all cell voltages from AFE slaves at a minimum rate of 20 Hz with PEC/CRC validation, and publish validated data to the database within 25 ms of acquisition trigger.
- **Rationale**: Required for SOA monitoring to detect overvoltage/undervoltage within FTTI (100 ms). 20 Hz provides margin over minimum 10 Hz.
- **ASIL**: `ASIL_D`
- **Safety goal reference**: `FB2-SAF-SGO-000001`
- **Acceptance criteria**:
  - All cell voltages acquired: Cell count match ≤ 100% %
  - Acquisition period: Period ≤ 50 ms
  - PEC/CRC validation: Error detection before database write ≤ 100% %
  - Database publish latency: Time from SPI complete to database write ≤ 25 ms
  - Data freshness: Max age of data at SOA read ≤ 30 ms
- **Conditions/modes**: `NORMAL`, `CHARGING`, `PRECHARGE`, `DERATING`
- **Source references**: `FB2-SRC-COD-000001`, `FB2-SRC-COD-000002`, `FB2-SRC-COD-000021`, `FB2-SRC-COD-000023`
- **Assumption references**: `FB2-ASM-001` (Lithium-ion cell chemistry with nominal voltage 3.7V, operat...), `FB2-ASM-004` (AFE SPI communication latency < 5 ms (including DMA transfer...), `FB2-ASM-005` (Cell voltage measurement noise follows Gaussian distribution...)

#### `FB2-SAF-FSR-000002` — FSR: SOA Voltage Limit Monitoring with Debounce

- **Statement**: The BMS shall monitor each cell voltage against configured minimum and maximum limits with a debounce of 2 consecutive violations within 100 ms, and classify violations within 5 ms of data availability, triggering FAULT state request on confirmed violation.
- **Rationale**: SOA monitoring must detect limit violations fast enough to meet FTTI. Debounce of 2 violations in 100 ms balances false positives vs detection latency (statistical analysis shows < 1e-6 false positive rate for Gaussian noise sigma=5mV).
- **ASIL**: `ASIL_D`
- **Safety goal reference**: `FB2-SAF-SGO-000001`
- **Acceptance criteria**:
  - Limit check latency: Time from database read to violation classification ≤ 5 ms
  - Limit accuracy: Threshold comparison accuracy ≤ 1 mV
  - Debounce filtering: False positive rate (Gaussian noise, sigma=5mV) ≤ 1E-6 events/hour
  - FAULT request latency: Time from confirmed violation to SYS fault request ≤ 2 ms
- **Conditions/modes**: `NORMAL`, `CHARGING`, `PRECHARGE`, `DERATING`
- **Source references**: `FB2-SRC-COD-000004`, `FB2-SRC-COD-000005`, `FB2-SRC-COD-000006`
- **Assumption references**: `FB2-ASM-001` (Lithium-ion cell chemistry with nominal voltage 3.7V, operat...), `FB2-ASM-005` (Cell voltage measurement noise follows Gaussian distribution...), `FB2-ASM-006` (Contactor mechanical opening time <= 30 ms (worst case) at -...)

#### `FB2-SAF-FSR-000003` — FSR: Contactor Opening on SOA Violation

- **Statement**: The BMS shall open all HV contactors within 30 ms of FAULT state request from SOA/DIAG, with auxiliary feedback confirmation within 5 ms of coil de-energization.
- **Rationale**: Contactor opening is the primary risk reduction measure; 30 ms mechanical opening + 5 ms feedback = 35 ms within FTTI budget
- **ASIL**: `ASIL_D`
- **Safety goal reference**: `FB2-SAF-SGO-000001`
- **Acceptance criteria**:
  - Contactor open latency: Time from FAULT request to contactor feedback open ≤ 30 ms
  - Feedback verification: Auxiliary contact confirmation ≤ 100% %
  - Weld detection: Weld detection latency ≤ 50 ms
  - Coil de-energize command: Time from FAULT request to SBC coil command ≤ 5 ms
- **Conditions/modes**: `NORMAL`, `CHARGING`, `PRECHARGE`, `DERATING`, `FAULT`
- **Source references**: `FB2-SRC-COD-000007`, `FB2-SRC-COD-000008`, `FB2-SRC-COD-000009`, `FB2-SRC-COD-000013`
- **Assumption references**: `FB2-ASM-001` (Lithium-ion cell chemistry with nominal voltage 3.7V, operat...), `FB2-ASM-006` (Contactor mechanical opening time <= 30 ms (worst case) at -...), `FB2-ASM-007` (SBC (FS85xx) watchdog is independent of main MCU and can tri...)

#### `FB2-SAF-FSR-000004` — FSR: Independent Hardware Voltage Monitor

- **Statement**: The BMS shall include an independent hardware voltage monitor (ASIL B) that continuously monitors cell voltages and can open HV contactors independently of the main MCU within 50 ms of overvoltage detection.
- **Rationale**: Provides freedom from interference for ASIL D safety goal; addresses timing budget violation in main path (115 ms > 100 ms FTTI) by providing parallel safety channel
- **ASIL**: `ASIL_B`
- **Safety goal reference**: `FB2-SAF-SGO-000001`
- **Acceptance criteria**:
  - Independent detection latency: Time from overvoltage to contactor command ≤ 50 ms
  - Independence: No shared MCU, power supply, or communication with main path ≤ 100% %
  - Monitoring coverage: Cells monitored ≤ All cells (or representative subset >= 50%) %
  - Threshold accuracy: Overvoltage threshold accuracy ≤ 50 mV
- **Conditions/modes**: `NORMAL`, `CHARGING`, `PRECHARGE`, `DERATING`, `FAULT`
- **Source references**: —
- **Assumption references**: `FB2-ASM-008` (Independent hardware voltage monitor (ASIL B) can be impleme...)


---

*Generated: 2026-09-13T04:11:53Z — auto-generated from the machine-verifiable corpus. Regenerate with `python3 docs/artifacts/tools/render_spec_documents.py`.*
