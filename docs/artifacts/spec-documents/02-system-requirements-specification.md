# foxBMS 2 — System Requirements Specification

**Document Control**

| Field | Value |
|---|---|
| Project | foxBMS 2 — Battery Management System |
| Document | System Requirements Specification |
| Baseline | BAS-REF-001 (commit `308028fb`, tag `v1.11.0`) |
| Profiles | `as_is` (source-grounded) + `synthetic_reference` (hypothetical) |
| Corpus status | `synthetic_ready_with_limitations` |
| Generated | 2026-09-12T01:01:53Z |

## Scope

System-level requirements: safety goals and functional safety requirements (FSRs) of both profiles with full attribute sets.

## Profile: `as_is`

### Safety Goals

#### `FB2-SAF-SGO-000001` — Cell Voltage Safety Goal

- **Statement**: The BMS shall detect cell voltage limit violations and open HV contactors within the fault tolerant time interval (FTTI = 100 ms) to prevent cell overvoltage/undervoltage hazardous events.
- **Rationale**: Hazard mitigation for FB2-SAF-HAZ-000001
- **ASIL**: `ASIL_D`
- **FTTI (total)**: ? ms
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

*Generated: 2026-09-12T01:01:53Z — auto-generated from the machine-verifiable corpus. Regenerate with `python3 docs/artifacts/tools/render_spec_documents.py`.*
