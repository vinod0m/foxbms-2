# foxBMS 2 — Software Requirements Specification

**Document Control**

| Field | Value |
|---|---|
| Project | foxBMS 2 — Battery Management System |
| Document | Software Requirements Specification |
| Baseline | BAS-REF-001 (commit `308028fb`, tag `v1.11.0`) |
| Profiles | `as_is` (source-grounded) + `synthetic_reference` (hypothetical) |
| Corpus status | `synthetic_ready_with_limitations` |
| Generated | 2026-09-13T02:20:37Z |

## Scope

Software requirements of both corpus profiles (SWRs grouped under their parent FSR with allocation rationale) plus software requirements reverse-engineered from the 40 implemented modules and the diagnosis/SOA configuration.

## Reverse-Engineered Software Requirements (module-grounded)

The implemented software directly satisfies the following software requirements. Each requirement cites its implementing module(s) with repository anchors; unit-test evidence is listed per module in the Detailed Design and Implementation Mapping documents.

| ID | Requirement | Implementing modules (anchors) |
|---|---|---|
| `SWR-RE-01` | The software shall acquire cell voltages and cell temperatures via the AFE daisy-chain and validate them (plausibility, redundancy). | `src/app/driver/afe/*` (8 AFE drivers), `src/app/driver/meas/`, `src/app/application/plausibility/`, `src/app/application/redundancy/` |
| `SWR-RE-02` | The software shall evaluate the safe operating area (cell voltage, cell temperature, cell/pack current) against MOL/RSL/MSL limits. | `src/app/application/soa/soa.c` (`SOA_*`), config `battery_cell_cfg.h` |
| `SWR-RE-03` | The software shall detect and classify 85 diagnosis events with configurable severity, latency and occurrence counters. | `src/app/engine/diag/`, `src/app/engine/config/diag_cfg.c` |
| `SWR-RE-04` | The software shall run the BMS state machine (13 states, 34 substates) in the 10 ms task context and reach the safe state (contactors open) on fatal errors. | `src/app/application/bms/`, `src/app/application/config/bms_cfg.h` |
| `SWR-RE-05` | The software shall control string-minus, string-plus and precharge contactors through smart power switches with feedback supervision. | `src/app/driver/contactor/`, `src/app/driver/sps/` |
| `SWR-RE-06` | The software shall supervise the interlock line and open the contactors on interlock faults. | `src/app/driver/interlock/` (ILCK) |
| `SWR-RE-07` | The software shall balance cells passively (reference strategy: voltage-based). | `src/app/application/bal/` (strategies: `none`, `voltage`) |
| `SWR-RE-08` | The software shall estimate SOC/SOE/SOF/SOH (reference: coulomb/energy counting, trapezoid SOF). | `src/app/application/algorithm/state_estimation/`, `algorithm.c` |
| `SWR-RE-09` | The software shall exchange data asynchronously between tasks via the database (single producer, multiple consumers). | `src/app/engine/database/` |
| `SWR-RE-10` | The software shall monitor task execution times and supply voltages (system monitoring, FRAM-persisted). | `src/app/engine/sys_mon/`, `src/app/engine/hw_info/`, `src/app/driver/fram/` |
| `SWR-RE-11` | The software shall communicate on CAN (41 messages) and provide an Ethernet TCP/IP interface for user applications. | `src/app/driver/can/`, `src/app/application/ethernet/`, `tools/dbc/foxbms.dbc` |
| `SWR-RE-12` | The software shall supervise the system basis chip (SBC) and react to FIN/RSTB errors. | `src/app/driver/sbc/` (NXP FS85) |
| `SWR-RE-13` | The software shall provide timekeeping (RTC), port expansion (PEX), humidity/temperature sensing (HTSEN) and debug LEDs on the continuous I2C task. | `src/app/driver/rtc/`, `pex/`, `htsensor/`, `led/` |
| `SWR-RE-14` | The software shall support optional insulation monitoring (IMD). | `src/app/driver/imd/` |
| `SWR-RE-15` | The software shall be unit-testable: 313 C unit tests run in CI with 100% line/branch coverage policy. | `tests/unit/app/**/test_*.c`, `docs/developer-manual/software/software-testing.rst` |

## Profile: `as_is`

### Parent FSR: `FB2-SAF-FSR-000001`

#### `FB2-HW-TSR-000001` — TSR: AFE Cell Voltage Measurement Accuracy

- **Allocated to**: `FB2-SAF-FSR-000001` (link `FB2-LNK-SAF-000005`, rationale: "Hardware requirement allocated from functional safety requirement")
- **Statement**: The AFE shall measure cell voltages with ±1.5 mV accuracy (including calibration) over -40°C to +85°C for 2.5V-4.2V range.
- **Rationale**: Required to support SOA limit detection with 1 mV threshold accuracy (FSR-002)
- **Classification**: `safety`
- **ASIL**: `ASIL_D`
- **Acceptance criteria**:
  - Measurement accuracy: Total error (offset + gain + temp drift) ≤ 1.5 mV
  - Resolution: LSB size ≤ 0.5 mV
  - PEC error detection: Single-bit error detection ≤ 100% %
- **Source references**: `FB2-SRC-HW-000002`, `FB2-SRC-COD-000001`
- **Assumption references**: `FB2-ASM-007`

#### `FB2-HW-TSR-000002` — TSR: AFE isoSPI Communication Integrity

- **Allocated to**: `FB2-SAF-FSR-000001` (link `FB2-LNK-SAF-000006`, rationale: "Hardware requirement allocated from functional safety requirement")
- **Statement**: The isoSPI interface shall provide communication with BER < 10^-9 and detect communication failures within 5 ms.
- **Rationale**: Communication failures must be detected within FTTI budget for AFE data
- **Classification**: `safety`
- **ASIL**: `ASIL_D`
- **Acceptance criteria**:
  - Bit error rate: BER under EMC conditions ≤ 1E-9 errors/bit
  - Failure detection time: Time from communication loss to SW notification ≤ 5 ms
  - CRC coverage: CRC polynomial coverage ≤ 100% %
- **Source references**: `FB2-SRC-HW-000003`, `FB2-SRC-COD-000021`, `FB2-SRC-COD-000023`
- **Assumption references**: `FB2-ASM-008`

#### `FB2-SW-SWR-000001` — SWR: AFE Driver - Cell Voltage Acquisition

- **Allocated to**: `FB2-SAF-FSR-000001` (link `FB2-LNK-SAF-000008`, rationale: "Software requirement allocated from functional safety requirement")
- **Statement**: The AFE driver shall trigger SPI/DMA acquisition of all cell voltages at 20 Hz, validate PEC/CRC, and publish to database within 5 ms of acquisition complete.
- **Rationale**: Software must acquire and validate AFE data within FTTI budget
- **Classification**: `safety`
- **ASIL**: `ASIL_D`
- **Acceptance criteria**:
  - Acquisition period: Timer period ≤ 50 ms
  - PEC/CRC validation: Error detection before database write ≤ 100% %
  - Database publish latency: Time from SPI complete to database write ≤ 5 ms
- **Source references**: `FB2-SRC-COD-000001`, `FB2-SRC-COD-000002`, `FB2-SRC-COD-000021`, `FB2-SRC-COD-000023`
- **Assumption references**: `FB2-ASM-010`

### Parent FSR: `FB2-SAF-FSR-000002`

#### `FB2-SW-SWR-000002` — SWR: SOA Voltage Limit Monitoring

- **Allocated to**: `FB2-SAF-FSR-000002` (link `FB2-LNK-SAF-000009`, rationale: "Software requirement allocated from functional safety requirement")
- **Statement**: The SOA module shall read cell voltages from database and compare against configured limits within 10 ms of data availability, triggering FAULT state on confirmed violation.
- **Rationale**: SOA software must detect violations and trigger contactor opening within FTTI
- **Classification**: `safety`
- **ASIL**: `ASIL_D`
- **Acceptance criteria**:
  - Limit check latency: Time from database read to violation classification ≤ 10 ms
  - Threshold accuracy: Comparison accuracy vs config ≤ 1 mV
  - FAULT state transition: Time from violation to SYS state FAULT ≤ 5 ms
- **Source references**: `FB2-SRC-COD-000004`, `FB2-SRC-COD-000009`, `FB2-SRC-COD-000010`
- **Assumption references**: `FB2-ASM-011`

### Parent FSR: `FB2-SAF-FSR-000003`

#### `FB2-HW-TSR-000003` — TSR: Contactor Driver and Feedback

- **Allocated to**: `FB2-SAF-FSR-000003` (link `FB2-LNK-SAF-000007`, rationale: "Hardware requirement allocated from functional safety requirement")
- **Statement**: The SBC (FS85xx) shall drive contactor coils with controlled slew rate and monitor auxiliary feedback contacts with < 2 ms latency.
- **Rationale**: Contactor control and feedback monitoring must meet FSR-003 30 ms latency budget
- **Classification**: `safety`
- **ASIL**: `ASIL_D`
- **Acceptance criteria**:
  - Coil drive slew rate: dV/dt at coil terminals ≤ 50 V/ms
  - Feedback latency: Time from contactor state change to SW notification ≤ 2 ms
  - Weld detection: Feedback mismatch detection time ≤ 100 ms
- **Source references**: `FB2-SRC-HW-000001`, `FB2-SRC-COD-000007`, `FB2-SRC-COD-000008`, `FB2-SRC-COD-000027`
- **Assumption references**: `FB2-ASM-009`

#### `FB2-SW-SWR-000003` — SWR: Contactor State Machine and Fault Response

- **Allocated to**: `FB2-SAF-FSR-000003` (link `FB2-LNK-SAF-000010`, rationale: "Software requirement allocated from functional safety requirement")
- **Statement**: The contactor driver shall execute state machine (OPEN -> PRECHARGE -> CLOSE -> HOLD) and open contactors within 5 ms of FAULT state request from SOA/DIAG.
- **Rationale**: Contactor software must respond to SOA violations within FTTI budget
- **Classification**: `safety`
- **ASIL**: `ASIL_D`
- **Acceptance criteria**:
  - Fault response latency: Time from FAULT request to coil de-energize command ≤ 5 ms
  - Feedback verification: Auxiliary contact readback after command ≤ 100% %
  - State machine correctness: Valid transitions only ≤ 100% %
- **Source references**: `FB2-SRC-COD-000007`, `FB2-SRC-COD-000008`, `FB2-SRC-COD-000009`, `FB2-SRC-COD-000013`
- **Assumption references**: `FB2-ASM-012`

## Profile: `synthetic_reference`

### Parent FSR: `FB2-SAF-FSR-000001`

#### `FB2-HW-TSR-000001` — TSR: AFE Cell Voltage Measurement Accuracy

- **Allocated to**: `FB2-SAF-FSR-000001` (link `FB2-LNK-SAF-000005`, rationale: "Hardware requirement allocated from functional safety requirement")
- **Statement**: The AFE shall measure cell voltages with ±1.5 mV accuracy (including calibration) over -40°C to +85°C for 2.5V-4.2V range.
- **Rationale**: Required to support SOA limit detection with 1 mV threshold accuracy (FSR-002)
- **Classification**: `safety`
- **ASIL**: `ASIL_D`
- **Acceptance criteria**:
  - Measurement accuracy: Total error (offset + gain + temp drift) ≤ 1.5 mV
  - Resolution: LSB size ≤ 0.5 mV
  - PEC error detection: Single-bit error detection ≤ 100% %
- **Source references**: `FB2-SRC-HW-000002`, `FB2-SRC-COD-000001`
- **Assumption references**: `FB2-ASM-007`

#### `FB2-HW-TSR-000002` — TSR: AFE isoSPI Communication Integrity

- **Allocated to**: `FB2-SAF-FSR-000001` (link `FB2-LNK-SAF-000006`, rationale: "Hardware requirement allocated from functional safety requirement")
- **Statement**: The isoSPI interface shall provide communication with BER < 10^-9 and detect communication failures within 5 ms.
- **Rationale**: Communication failures must be detected within FTTI budget for AFE data
- **Classification**: `safety`
- **ASIL**: `ASIL_D`
- **Acceptance criteria**:
  - Bit error rate: BER under EMC conditions ≤ 1E-9 errors/bit
  - Failure detection time: Time from communication loss to SW notification ≤ 5 ms
  - CRC coverage: CRC polynomial coverage ≤ 100% %
- **Source references**: `FB2-SRC-HW-000003`, `FB2-SRC-COD-000021`, `FB2-SRC-COD-000023`
- **Assumption references**: `FB2-ASM-008`

#### `FB2-SW-SWR-000001` — SWR: AFE Driver - Cell Voltage Acquisition

- **Allocated to**: `FB2-SAF-FSR-000001` (link `FB2-LNK-SAF-000008`, rationale: "Software requirement allocated from functional safety requirement")
- **Statement**: The AFE driver shall trigger SPI/DMA acquisition of all cell voltages at 20 Hz, validate PEC/CRC, and publish to database within 5 ms of acquisition complete.
- **Rationale**: Software must acquire and validate AFE data within FTTI budget
- **Classification**: `safety`
- **ASIL**: `ASIL_D`
- **Acceptance criteria**:
  - Acquisition period: Timer period ≤ 50 ms
  - PEC/CRC validation: Error detection before database write ≤ 100% %
  - Database publish latency: Time from SPI complete to database write ≤ 25 ms
- **Source references**: `FB2-SRC-COD-000001`, `FB2-SRC-COD-000002`, `FB2-SRC-COD-000021`, `FB2-SRC-COD-000023`
- **Assumption references**: `FB2-ASM-010`

### Parent FSR: `FB2-SAF-FSR-000002`

#### `FB2-SW-SWR-000002` — SWR: SOA Voltage Limit Monitoring

- **Allocated to**: `FB2-SAF-FSR-000002` (link `FB2-LNK-SAF-000009`, rationale: "Software requirement allocated from functional safety requirement")
- **Statement**: The SOA module shall read cell voltages from database and compare against configured minimum (2.5V) and maximum (4.2V) limits with a debounce of 2 consecutive violations within 100 ms, and classify violations within 5 ms of data availability, triggering FAULT state request on confirmed violation.
- **Rationale**: SOA monitoring must detect limit violations fast enough to meet FTTI. Debounce of 2 violations in 100 ms balances false positives vs detection latency (statistical analysis shows < 1e-6 false positive rate for Gaussian noise sigma=5mV).
- **Classification**: `safety`
- **ASIL**: `ASIL_D`
- **Acceptance criteria**:
  - Limit check latency: Time from database read to violation classification ≤ 5 ms
  - Limit accuracy: Threshold comparison accuracy ≤ 1 mV
  - Debounce filtering: False positive rate (Gaussian noise, sigma=5mV) ≤ 1E-6 events/hour
  - FAULT request latency: Time from confirmed violation to SYS fault request ≤ 2 ms
- **Source references**: `FB2-SRC-COD-000004`, `FB2-SRC-COD-000005`, `FB2-SRC-COD-000006`
- **Assumption references**: `FB2-ASM-001`, `FB2-ASM-005`, `FB2-ASM-006`

### Parent FSR: `FB2-SAF-FSR-000003`

#### `FB2-HW-TSR-000003` — TSR: Contactor Driver and Feedback

- **Allocated to**: `FB2-SAF-FSR-000003` (link `FB2-LNK-SAF-000007`, rationale: "Hardware requirement allocated from functional safety requirement")
- **Statement**: The SBC (FS85xx) shall drive contactor coils with controlled slew rate and monitor auxiliary feedback contacts with < 2 ms latency.
- **Rationale**: Contactor control and feedback monitoring must meet FSR-003 30 ms latency budget
- **Classification**: `safety`
- **ASIL**: `ASIL_D`
- **Acceptance criteria**:
  - Coil drive slew rate: dV/dt at coil terminals ≤ 50 V/ms
  - Feedback latency: Time from contactor state change to SW notification ≤ 2 ms
  - Weld detection: Feedback mismatch detection time ≤ 100 ms
- **Source references**: `FB2-SRC-HW-000001`, `FB2-SRC-COD-000007`, `FB2-SRC-COD-000008`, `FB2-SRC-COD-000027`
- **Assumption references**: `FB2-ASM-009`

#### `FB2-SW-SWR-000003` — SWR: Contactor State Machine and Fault Response

- **Allocated to**: `FB2-SAF-FSR-000003` (link `FB2-LNK-SAF-000010`, rationale: "Software requirement allocated from functional safety requirement")
- **Statement**: The contactor driver shall execute state machine (OPEN -> PRECHARGE -> CLOSE -> HOLD) and open contactors within 5 ms of FAULT state request from SOA/DIAG.
- **Rationale**: Contactor software must respond to SOA violations within FTTI budget
- **Classification**: `safety`
- **ASIL**: `ASIL_D`
- **Acceptance criteria**:
  - Fault response latency: Time from FAULT request to coil de-energize command ≤ 5 ms
  - Feedback verification: Auxiliary contact readback after command ≤ 100% %
  - State machine correctness: Valid transitions only ≤ 100% %
- **Source references**: `FB2-SRC-COD-000007`, `FB2-SRC-COD-000008`, `FB2-SRC-COD-000009`, `FB2-SRC-COD-000013`
- **Assumption references**: `FB2-ASM-012`

### Software Requirements Without Parent FSR Link

#### `FB2-MAN-SCO-000001` — Project Scope: foxBMS 2 Reference BMS Development

- **Statement**: Develop a reference implementation of a production-intent BMS based on the foxBMS 2 platform, covering all safety-critical functions for a hypothetical 400V/100kWh EV battery pack with ASIL D cell voltage monitoring.
- **Classification**: `management` | **Profile**: `synthetic_reference`
- **Note**: no `allocated_to` link to a parent FSR in this profile's registry.


---

*Generated: 2026-09-13T02:20:37Z — auto-generated from the machine-verifiable corpus. Regenerate with `python3 docs/artifacts/tools/render_spec_documents.py`.*
