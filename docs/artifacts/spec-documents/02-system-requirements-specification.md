# foxBMS 2 — System Requirements Specification

**Document Control**

| Field | Value |
|---|---|
| Project | foxBMS 2 — Battery Management System |
| Document | System Requirements Specification |
| Baseline | BAS-REF-001 (commit `308028fb`, tag `v1.11.0`) |
| Profiles | `as_is` (source-grounded) + `synthetic_reference` (hypothetical) |
| Corpus status | `synthetic_ready_with_limitations` |
| Generated | 2026-10-01T05:09:49Z |

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
- **ASIL classification status**: `hypothetical` (hypothetical; not an ASIL determination for the real product)
- **ASIL derivation**: ISO 26262-3:2018, hazard analysis and functional safety concept (Part 3, clause 6) followed by the definition of the safety goal and its ASIL (Part 3, clause 7). The clause references are the ones this record's own standards_mappings already carries and the one FB2-SAF-HAZ-000001 carries; they are recorded from the locked standards baseline in docs/artifacts/governance and no clause text was consu...
  - hazardous event `HE-01` of `FB2-SAF-HAZ-000001`, operational situation: CHARGING mode, high SOC, fast charge
  - **severity** `S3`: S3 is the life-threatening-or-fatal band. The consequence recorded for this hazardous event is thermal runaway, and FB2-SAF-HAZ-000001 states its outcome as fire or explosion with fatal injuries, which places it above the severe-but-survivable band that S2 denotes. It is not S0 or S1 because the record does not describe an injury that is light or absent. Severity is judged on the most credible outcome of the hazardou...
  - **exposure** `E4`: E4 is the highest exposure band and the one that applies when the operational situation is continuously or very frequently present. The situation recorded here is not a transient manoeuvre but the ordinary state of a pack while it is being charged at high state of charge and high rate, which recurs on every charge cycle and persists for as long as the charge lasts, and the hazard record's own rationale says the expos... Evidence status: NOT EVIDENCED. The hazard record states no duty cycle, no mission profile, no fleet statistic and no charge-cycle data. The rating is an authored input. This ma...
  - **controllability** `C3`: C3 is the largely-uncontrollable band, and the hazard record's rationale gives the reason: the driver cannot detect or control an individual cell's overvoltage. There is no indication available to a person in the vehicle of which cell is at what voltage, and no action they could take would change it.
  1. 1. Malfunctioning behaviour to hazardous event: the malfunctioning behaviour recorded in FB2-SAF-HAZ-000001 - the front end reports an incorrect cell voltage, or the safe-operating-area check fails to detect the limit violation, or the contactor fails to open on the violation, or the BMS fails to request the opening - leads to the hazardous event HE-01, cell overvoltage during charging leading to thermal runaway.
  2. 2. Operational situation: CHARGING mode, high SOC, fast charge.
  3. 3. Severity S3, exposure E4, controllability C3, reasoned above.
  4. 4. ASIL from the Part 3 determination table, severity row S3 and exposure column E4: ASIL_D. The rest of the S3 row, so that the sensitivity of the answer is visible, is S3/E1 gives ASIL_A, S3/E2 gives ASIL_B, S3/E3 gives ASIL_C, S3/E4 gives ASIL_D.
  5. 5. The second hazardous event covered by the same goal, HE-02, is S2/E3, which the same table gives ASIL_B; the hazard record already records that, so the two events are consistent with one table and not with two.
  6. 6. The safety goal inherits the highest ASIL among the hazardous events it covers. The goal's statement names both cell overvoltage and cell undervoltage, so it covers HE-01 and HE-02, and the highest is ASIL_D. Had the goal been scoped to the undervoltage event alone it would be ASIL_B; it is not scoped that way.
  7. 7. Consistency of the ASIL with the allocation beneath it: an ASIL D goal requires strategies of ASIL D, and permits elements of a lower ASIL class only where they are not the sole means of achieving the goal. FB2-SAF-TSC-000001 allocates the main path (AR-001 to AR-004) at ASIL D and the independent path AR-005 at ASIL B, and states that difference in terms as the decomposition the ASIL D goal rests on. That is consistent: AR-005 is a second barrier and not the primary means of achieving the go...
  - derived ASIL `ASIL_D`; matches the recorded `ASIL_D`: True
  - **This classification does not assert:**
    - It does not assert an ASIL for the real foxBMS 2 product. The real product has never had a hazard analysis and risk assessment, and this classification does not substitute for one or make one unnecessary.
    - It does not assert that the S3, E4 and C3 ratings are correct. They are authored inputs of a synthetic record describing a fictional reference project - FB2-SAF-FSC-000001 and FB2-SAF-TSC-000001 both carry concept_identity.fictional = true - and they were not obtained from an exposure analysis, a mission profile, a fleet statistic, an FMEA of a real cell, a pack design study, or any measurement of any item.
    - It does not assert that any design meets ASIL D. The classification creates an obligation on the design below it; it is not evidence that the obligation is discharged. In particular it is not evidence that the reaction fits the 100 ms interval this goal allocates, and the source-observed records in the as_is profile record a reaction chain that is longer than that interval - see the fault_reaction fields of FB2-SAF-F...
    - It does not assert conformity with ISO 26262, and it is not a certification, a type approval, or evidence of one. No part of ISO 26262-3 was audited to produce it.
    - It does not assert tool qualification. No tool used anywhere in this corpus has been qualified for a safety purpose, and an automated validation pass is not a qualified tool and not an independent functional-safety confirmation.
    - It does not assert an ASPICE capability level for anything.
    - It does not assert human approval. human_approval_status on this record and on every record named in it is pending, production_authorized is false and product_verification_credit is false, and no functional-safety expert has confirmed any of it.
    - It does not establish independence of the second barrier. The ASIL B allocation of AR-005 that the derivation relies on rests on FB2-ASM-008, which is a declared assumption, and FB2-SAF-TSC-000001 states that the absence of a demonstration of that independence is the largest open assumption of the ASIL D allocation.
  - **What would change the answer**: Two inputs decide this classification and neither is evidenced. If the exposure of the charging situation were established as E3 rather than E4 - for example by a mission profile showing a materially shorter or rarer high-SOC high-rate charging exposure - the same table would give ASIL_C, and the allocation beneath it would have to be revisited. If the pack chemistry limited the credible consequence to a severe but survivable injury, the severity would be S2 and the same table would give ASIL_C ...
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
- **Fault reaction** (allocated element `AR-001`, owns reaction: False): No reaction is allocated to AR-001, and the reason is structural rather than an omission: FB2-SAF-FSC-000001 places fault_detection on AR-001 and allocates its four reactions to AR-002, AR-004, AR-005 and AR-006, and FB2-SAF-TSC-000001 says the same thing in its strategy_allocation. What the real implementation does when this chain fails is stated here so the requirement is not read as reactionless, and it splits by DIAG severity rather than uniformly. A measurement that fails its own validity check is reported as DIAG_ID_AFE_CELL_VOLTAGE_MEAS_ERROR, which src/app/engine/config/diag_cfg.c:180 configures at severity DIAG_WARNING with sensitivity DIAG_SEN_EVENT_1 and delay DIAG_DELAY_DISCARD, ...
  - triggered by: A cell-voltage word the AFE driver reports as invalid via DIAG_CheckEvent(cellVoltageMeasurementValid, DIAG_ID_AFE_CELL_VOLTAGE_MEAS_ERROR, ...) at src/app/driver/afe/ltc/ltc_6806.c:457 (severity WARNING - no contactor opening), or an SPI / communication-integrity failure reported as DIAG_ID_AFE_SPI or DIAG_ID_AFE_COMMUNICATION_INTEGRITY at ltc_6806.c:699-961 (severity FATAL - contactors open afte...
  - reaction held by `AR-002`: Aggregate the fatal diagnosis flags and, after the configured delay, drive the state machine into BMS_FSM_STATE_OPEN_CONTACTORS within 100 ms (allocated by FB2-SAF-FSC-000001.fault_reaction entry 3; FB2-SAF-TSC-000001.fault_reaction)
  - reaction held by `AR-004`: Execute the opening sequence and confirm by auxiliary feedback within 40 ms (allocated by FB2-SAF-FSC-000001.fault_reaction entry 1; FB2-SAF-TSC-000001.fault_reaction)
  - mode dependence: Mode-independent on the detection side: the integrity check and the SPI/communication diagnosis run the same way in every mode. The reaction is mode-dependent in the sense FB2-SAF-FSC-000001 records for AR-004: entering the safe state in MOD-004 removes propulsion from a moving vehicle.
  - allocation basis: FB2-SAF-FSC-000001.safety_strategies.fault_reaction allocates no reaction to AR-001; FB2-SAF-TSC-000001.safety_strategies.strategy_allocation states 'AR-001 and AR-005 detect, AR-002 confirms, AR-004 acts and confirms the action'. The severities and delays quoted above are read from src/app/engine/config/diag_cfg.c at the pinned commit recorded in docs/artifacts/sources/source-registry.json, and the aggregation and state transition are read from src/app/application/bms/bms.c.
  - open limits: Four limits are recorded and none is closed by this field. First, the DIAG severity split is not uniform across the failure modes of this chain and is not a property of this requirement: DIAG_ID_AFE_CELL_VOLTAGE_MEAS_ERROR is only a WARNING, so a measurement the driver knows to be invalid does not by itself reach the safe state, and what does reach it is the link failure that usually accompanies it. Nothing in this corpus analyses that pairing. Second, the sensitivity of a DIAG_SEN_EVENT_5 entry is a COUNT of DIAG_Handler calls, not a time window (DIAG_GetDiagnosisEntryState at src/app/engine/diag/diag.c:287-301 compares an occurrence counter against the configured threshold), so the wall-clock time of the debounce depends on how often SOA and the AFE drivers are called, which is the BMS task period BMS_STATEMACHINE_TASK_CYCLE_CONTEXT_MS = 10 (src/app/application/config/bms_cfg.h:100) an...
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
- **Fault reaction** (allocated element `AR-002`, owns reaction: True): Set the corresponding diagnosis entry, and if that entry's configured severity is DIAG_FATAL_ERROR, drive the battery state machine into the latched error state, which opens the HV contactors. The path is: SOA_CheckVoltages() in src/app/application/soa/soa.c:81 compares the per-string minimum and maximum cell voltages against the three-tier limits and calls DIAG_Handler for the tier that was crossed; the DIAG module latches the entry once its occurrence counter passes the configured sensitivity; BMS_IsAnyFatalErrorFlagSet() at src/app/application/bms/bms.c:515-531 walks the fatal-error table built at src/app/engine/diag/diag.c:254-260; BMS_IsBatterySystemStateOkay() at bms.c:534-575 returns ...
  - triggered by: A cell voltage crossing BC_VOLTAGE_MAX_MOL_mV, BC_VOLTAGE_MAX_RSL_mV or BC_VOLTAGE_MAX_MSL_mV, or the corresponding minimum limits, evaluated in SOA_CheckVoltages() at src/app/application/soa/soa.c:89-131. Whether the crossing produces a reaction at all, and which one, is decided by the configured severity of the corresponding entry, not by the comparison.
  - reaction time budget: 200 ms — basis: DIAG_DELAY_200ms from diag_cfg.c:126 and diag_cfg.c:129. This is the delay between the entry becoming active and the state request, and it is the delay for a DIAG_FATAL_ERROR entry, not the whole reaction. The debounce in front of it is a count, not a time: DIAG_SEN_EVENT_50 is a threshold of 49 and DIAG_GetDiagnosisEntryState at src/app/engine/diag/diag.c:287-301 activates the entry when occurren...
  - mode dependence: Mode-independent as to the mechanism: SOA_CheckVoltages() is called on every BMS_Trigger regardless of mode (bms.c:911-917). The consequence is mode-dependent: opening the contactors in MOD-004, where current is flowing to a moving vehicle, removes propulsion, which is the caveat FB2-SAF-FSC-000001 records against the AR-004 reaction.
  - allocation basis: FB2-SAF-FSC-000001.fault_reaction entry 3 and FB2-SAF-TSC-000001.fault_reaction allocate the latched FAULT mode to AR-002 at 3 ms. The 3 ms is the synthetic_reference allocation and does NOT describe the real implementation, which has no equivalent 3 ms step: the real path from a sustained excursion to a state request is a counter threshold plus a configured delay, configured at src/app/engine/config/diag_cfg.c:126 and read at bms.c:534-575. Both figures are recorded here rather than one being d...
  - open limits: One contradiction is recorded and it is NOT resolved by this field, because resolving it is a different piece of work with its own evidence requirement. This record's statement specifies 'a debounce of 2 consecutive violations within 100 ms' and 'classify violations within 5 ms of data availability', and FB2-PRM-000006 records soa_debounce_count = 2, which is where those figures come from. The source does not implement them. src/app/application/soa/soa.c implements a three-tier MOL/RSL/MSL comparison with no counter in the SOA module at all, and the debounce that does exist is the DIAG occurrence counter, configured at 50 events for the MSL tier (diag_cfg.c:126). There is no 5 ms classification figure in either bms_cfg.h or diag_cfg.c. The statement, the acceptance criteria and the parameter registry have NOT been edited, because the statement is a requirement and a requirement that does...
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
- **Fault reaction** (allocated element `AR-004`, owns reaction: True): The battery state machine runs a sequenced opening, not a single command, and the real reaction is that sequence. On a FAULT request the state machine enters BMS_FSM_STATE_OPEN_CONTACTORS and first calls CONT_OpenAllPrechargeContactors(), because the precharge resistor limits the maximum current and those contactors can always be opened (src/app/application/bms/bms.c:1042-1052). It then waits BMS_TIME_WAIT_AFTER_OPENING_PRECHARGE (50 ms) and opens the strings one at a time starting from the highest string index (bms.c:1053-1165). Per string it opens the first contactor, waits BMS_WAIT_TIME_AFTER_OPENING_STRING_CONTACTOR (10 ms), reads back CONT_GetContactorState and BMS_IsContactorFeedbackVa...
  - triggered by: A FAULT state request from the SOA monitor or from a diagnosis entry, surfaced as BMS_IsBatterySystemStateOkay() returning STD_NOT_OK; or a state of the auxiliary feedback that disagrees with the commanded state, which is the weld-detection path and which is also why this branch re-issues rather than proceeds.
  - reaction time budget: 35 ms — basis: The 35 ms is the synthetic_reference allocation from FB2-SAF-FSC-000001.fault_reaction entry 1 and FB2-SAF-TSC-000001.fault_reaction, being contactor_command 5 ms plus contactor_mechanical 30 ms from FB2-PRM-000005. It is recorded here because the ASIL and safety goal this record refines are the synthetic_reference ones, and dropping it would leave the record citing a reaction it does not state. I...
  - mode dependence: Mode-dependent, and in the real implementation the dependence is visible in the code rather than in a comment. The opening sequence is entered from any state that receives a FAULT or error request, and FB2-SAF-FSC-000001 records that in MOD-004, with the contactors closed and current flowing, reaching the safe state removes propulsion from a moving vehicle. The real sequence makes one further mode-dependent decision inside it: a contactor is not opened while the string current is at or above BS_...
  - allocation basis: FB2-SAF-FSC-000001.fault_reaction entry 1 and FB2-SAF-TSC-000001.fault_reaction entry 1 both allocate this reaction to AR-004 at 35 ms, realised by FB2-SW-SWR-000003 in software and FB2-HW-TSR-000003 in hardware. The 40 ms end-to-end figure is FB2-SAF-SGO-000001.timing_budget.allocation (contactor_command_ms 5 + contactor_mechanical_ms 30 + feedback_verification_ms 5) and is reconciled against this record's acceptance criteria under FB2-REV-FND-000024. The real source anchors are FB2-SRC-COD-000...
  - open limits: Four limits are recorded. First, the 30 ms feedback-open criterion and the 100 ms feedback-confirmed criterion in this record's acceptance criteria do not distinguish the mechanically open point from the feedback-confirmed point the way the synthetic_reference copy of this requirement now does, and they carry a 100 ms weld-detection figure against FB2-HW-TSR-000003's 100 ms while the synthetic copy carries 50 ms; neither copy of the weld figure was changed here and the disagreement recorded against FB2-REV-FND-000024 is still open. Second, the real reaction is bounded by a per-string timeout rather than by a total reaction time, and the source carries an unresolved 'TODO: add timeout' on the re-issue branch, so the retry count is unbounded in the code. Third, the 30 ms mechanical figure is FB2-PRM-000005 with an upper tolerance of 40 ms, and FB2-ASM-006 is an assumption about the contact...
- **Source references**: `FB2-SRC-COD-000008`, `FB2-SRC-COD-000009`, `FB2-SRC-COD-000013`
- **Assumption references**: `FB2-ASM-001` (Lithium-ion cell chemistry with nominal voltage 3.7V, operat...), `FB2-ASM-006` (Contactor mechanical opening time <= 30 ms (worst case) at -...), `FB2-ASM-007` (SBC (FS85xx) watchdog is independent of main MCU and can tri...)

## Profile: `synthetic_reference`

### Safety Goals

#### `FB2-SAF-SGO-000001` — Cell Voltage Safety Goal

- **Statement**: The BMS shall detect cell voltage limit violations and open all HV contactors within the fault tolerant time interval (FTTI = 100 ms) to prevent cell overvoltage/undervoltage hazardous events, with a target diagnostic test interval of 10 ms, a target contactor mechanical opening time of 30 ms (FB2-PRM-000005 / FB2-ASM-006) and a resulting 40 ms from the fault request to feedback-confirmed contacto...
- **Rationale**: Hazard mitigation for FB2-SAF-HAZ-000001
- **ASIL**: `ASIL_D`
- **ASIL classification status**: `hypothetical` (hypothetical; not an ASIL determination for the real product)
- **ASIL derivation**: ISO 26262-3:2018, hazard analysis and functional safety concept (Part 3, clause 6) followed by the definition of the safety goal and its ASIL (Part 3, clause 7). The clause references are the ones this record's own standards_mappings already carries and the one FB2-SAF-HAZ-000001 carries; they are recorded from the locked standards baseline in docs/artifacts/governance and no clause text was consu...
  - hazardous event `HE-01` of `FB2-SAF-HAZ-000001`, operational situation: CHARGING mode, high SOC (>90%), fast charge (>1C), ambient > 45°C
  - **severity** `S3`: S3 is the life-threatening-or-fatal band. The consequence recorded for this hazardous event is thermal runaway, and FB2-SAF-HAZ-000001 states its outcome as fire or explosion with fatal injuries, which places it above the severe-but-survivable band that S2 denotes. It is not S0 or S1 because the record does not describe an injury that is light or absent. Severity is judged on the most credible outcome of the hazardou...
  - **exposure** `E4`: E4 is the highest exposure band and the one that applies when the operational situation is continuously or very frequently present. The situation recorded here is not a transient manoeuvre but the ordinary state of a pack while it is being charged at high state of charge and high rate, which recurs on every charge cycle and persists for as long as the charge lasts, and the hazard record's own rationale says the expos... Evidence status: NOT EVIDENCED. The hazard record states no duty cycle, no mission profile, no fleet statistic and no charge-cycle data. The rating is an authored input. This ma...
  - **controllability** `C3`: C3 is the largely-uncontrollable band, and the hazard record's rationale gives the reason: the driver cannot detect or control an individual cell's overvoltage. There is no indication available to a person in the vehicle of which cell is at what voltage, and no action they could take would change it.
  1. 1. Malfunctioning behaviour to hazardous event: the malfunctioning behaviour recorded in FB2-SAF-HAZ-000001 - the front end reports an incorrect cell voltage, or the safe-operating-area check fails to detect the limit violation, or the contactor fails to open on the violation, or the BMS fails to request the opening - leads to the hazardous event HE-01, cell overvoltage during charging leading to thermal runaway.
  2. 2. Operational situation: CHARGING mode, high SOC (>90%), fast charge (>1C), ambient > 45°C.
  3. 3. Severity S3, exposure E4, controllability C3, reasoned above.
  4. 4. ASIL from the Part 3 determination table, severity row S3 and exposure column E4: ASIL_D. The rest of the S3 row, so that the sensitivity of the answer is visible, is S3/E1 gives ASIL_A, S3/E2 gives ASIL_B, S3/E3 gives ASIL_C, S3/E4 gives ASIL_D.
  5. 5. The second hazardous event covered by the same goal, HE-02, is S2/E3, which the same table gives ASIL_B; the hazard record already records that, so the two events are consistent with one table and not with two.
  6. 6. The safety goal inherits the highest ASIL among the hazardous events it covers. The goal's statement names both cell overvoltage and cell undervoltage, so it covers HE-01 and HE-02, and the highest is ASIL_D. Had the goal been scoped to the undervoltage event alone it would be ASIL_B; it is not scoped that way.
  7. 7. Consistency of the ASIL with the allocation beneath it: an ASIL D goal requires strategies of ASIL D, and permits elements of a lower ASIL class only where they are not the sole means of achieving the goal. FB2-SAF-TSC-000001 allocates the main path (AR-001 to AR-004) at ASIL D and the independent path AR-005 at ASIL B, and states that difference in terms as the decomposition the ASIL D goal rests on. That is consistent: AR-005 is a second barrier and not the primary means of achieving the go...
  - derived ASIL `ASIL_D`; matches the recorded `ASIL_D`: True
  - **This classification does not assert:**
    - It does not assert an ASIL for the real foxBMS 2 product. The real product has never had a hazard analysis and risk assessment, and this classification does not substitute for one or make one unnecessary.
    - It does not assert that the S3, E4 and C3 ratings are correct. They are authored inputs of a synthetic record describing a fictional reference project - FB2-SAF-FSC-000001 and FB2-SAF-TSC-000001 both carry concept_identity.fictional = true - and they were not obtained from an exposure analysis, a mission profile, a fleet statistic, an FMEA of a real cell, a pack design study, or any measurement of any item.
    - It does not assert that any design meets ASIL D. The classification creates an obligation on the design below it; it is not evidence that the obligation is discharged. In particular it is not evidence that the reaction fits the 100 ms interval this goal allocates, and the source-observed records in the as_is profile record a reaction chain that is longer than that interval - see the fault_reaction fields of FB2-SAF-F...
    - It does not assert conformity with ISO 26262, and it is not a certification, a type approval, or evidence of one. No part of ISO 26262-3 was audited to produce it.
    - It does not assert tool qualification. No tool used anywhere in this corpus has been qualified for a safety purpose, and an automated validation pass is not a qualified tool and not an independent functional-safety confirmation.
    - It does not assert an ASPICE capability level for anything.
    - It does not assert human approval. human_approval_status on this record and on every record named in it is pending, production_authorized is false and product_verification_credit is false, and no functional-safety expert has confirmed any of it.
    - It does not establish independence of the second barrier. The ASIL B allocation of AR-005 that the derivation relies on rests on FB2-ASM-008, which is a declared assumption, and FB2-SAF-TSC-000001 states that the absence of a demonstration of that independence is the largest open assumption of the ASIL D allocation.
  - **What would change the answer**: Two inputs decide this classification and neither is evidenced. If the exposure of the charging situation were established as E3 rather than E4 - for example by a mission profile showing a materially shorter or rarer high-SOC high-rate charging exposure - the same table would give ASIL_C, and the allocation beneath it would have to be revisited. If the pack chemistry limited the credible consequence to a severe but survivable injury, the severity would be S2 and the same table would give ASIL_C ...
- **FTTI (total)**: 100 ms
- **Timing budget allocation**: `afe_acquisition_ms`=25ms, `contactor_command_ms`=5ms, `contactor_mechanical_ms`=30ms, `database_publish_ms`=3ms, `fault_classification_ms`=2ms, `feedback_verification_ms`=5ms, `margin_ms`=15ms, `pec_validation_ms`=2ms, `soa_limit_check_ms`=5ms, `spi_transfer_ms`=5ms, `sys_state_transition_ms`=3ms
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
- **Fault reaction** (allocated element `AR-001`, owns reaction: False): No reaction is allocated to this element, and the reason is structural rather than an omission. FB2-SAF-FSC-000001 places fault_detection on AR-001 and allocates its four fault reactions to AR-002, AR-004, AR-005 and AR-006, and its strategy_allocation says so in words: 'Detection is split so that no single element both detects and acts: AR-001 and AR-005 detect, AR-002 confirms, AR-004 acts and confirms the action, AR-003 carries the decision, AR-006 acts only when the others have failed.' This requirement is the detection side, so the reaction to a failure of this chain is owned elsewhere and is named here so the requirement is not read as reactionless. A transferred word that fails its in...
  - triggered by: A transferred cell-voltage word whose front-end integrity code does not validate; a slave-link or SPI transfer failure reported by the acquisition driver; or a measurement that is not published because it could not be validated.
  - reaction held by `AR-002`: Enter the latched FAULT mode and refuse to leave it without authorised service action within 3 ms (allocated by FB2-SAF-FSC-000001.fault_reaction entry 3; identical entry in FB2-SAF-TSC-000001.fault_reaction)
  - reaction held by `AR-005`: Open the contactors through the independent path, without waiting for the main microcontroller within 50 ms (allocated by FB2-SAF-FSC-000001.fault_reaction entry 2; identical entry in FB2-SAF-TSC-000001.fault_reaction)
  - mode dependence: Mode-independent on the detection side: the integrity check runs the same way in every mode. The reaction AR-002 reaches is mode-dependent, and FB2-SAF-FSC-000001 records that as the load-bearing caveat of the concept: in MOD-004, where the contactors are closed and current is flowing, reaching FAULT removes propulsion from a moving vehicle. That is why AR-002's latch is allocated to a condition whose severity requires the safe state and not to a degraded condition, and why this requirement's ro...
  - allocation basis: FB2-SAF-FSC-000001.safety_strategies.fault_reaction lists four reactions and allocates none to AR-001. FB2-SAF-TSC-000001.safety_strategies.strategy_allocation states the same split in prose. The detection that this requirement carries is the 'Front-end integrity code on every transferred word' mechanism in FB2-SAF-TSC-000001.fault_detection, allocated to AR-001 with detection_time_budget_ms = 2, which equals the pec_validation_ms entry of FB2-SAF-SGO-000001.timing_budget.allocation. The 25 ms a...
  - open limits: Three limits are recorded and none of them is closed by this field. First, the plausibility and redundancy comparison that lets AR-002 tell a failed measurement from a genuine excursion appears in FB2-SAF-TSC-000001.fault_detection with an empty coverage_claim_evidence list, so its coverage is not quantified anywhere in this corpus. Second, no timing measurement of AR-001 exists: the 25 ms, 2 ms and 3 ms figures are allocations of intent in FB2-SAF-SGO-000001.timing_budget.allocation and FB2-SAF-TSC-000001 states in its own limitations that the budget is not a worst-case analysis - no WCET, no queueing analysis and no measured execution time for any of its ten entries. Third, the independence of AR-005 on which the last-resort reaction depends is assumed (FB2-ASM-008) and not demonstrated.
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
- **Fault reaction** (allocated element `AR-002`, owns reaction: True): Enter the latched FAULT mode and refuse to leave it without authorised service action, and request the safe state. This is this element's own reaction and FB2-SAF-FSC-000001 allocates it to AR-002 at 3 ms, which is the fault_classification_ms entry of FB2-SAF-SGO-000001.timing_budget.allocation. The request is not the whole reaction: AR-004 executes it. FB2-SAF-SGO-000001 allocates the remainder of the chain to AR-004 as contactor_command 5 ms + contactor_mechanical 30 ms + feedback_verification 5 ms, so the reaction this requirement triggers is complete 40 ms after the classification it produces, inside the 100 ms interval. The latch is what makes the safe state persistent rather than a tra...
  - triggered by: Two consecutive samples of the same cell beyond the configured limit within 100 ms (FB2-PRM-000006, soa_debounce_count = 2, tolerance min = max = 2), classified within 5 ms of data availability. A single sample beyond the limit that the second sample does not confirm produces no reaction at all, and that is the whole function of the debounce.
  - reaction time budget: 3 ms
  - mode dependence: Mode-independent in the sense FB2-SAF-FSC-000001 uses for AR-002: the latch is entered the same way in every mode. What differs by mode is whether entering it is the right action. In MOD-004, with the contactors closed and current flowing, entering it removes propulsion from a moving vehicle, and FB2-SAF-FSC-000001 states that the item must therefore distinguish a genuine limit violation from a degraded condition and must not enter FAULT for the latter. The debounce is therefore not only a false...
  - allocation basis: FB2-SAF-FSC-000001.fault_reaction entry 3 ('Enter the latched FAULT mode and refuse to leave it without authorised service action', element_id AR-002, reaction_time_budget_ms 3, mode_dependence 'Mode-independent'). The same entry with the same 3 ms appears in FB2-SAF-TSC-000001.fault_reaction. The 3 ms equals fault_classification_ms in FB2-SAF-SGO-000001.timing_budget.allocation, and the 5 ms limit check this requirement carries equals soa_limit_check_ms in the same allocation. The reaction is r...
  - open limits: Two limits are recorded. First, the 1e-6 per hour false-positive rate in this requirement's rationale and acceptance criteria is an analytical estimate conditional on FB2-ASM-005, a Gaussian noise assumption with sigma 5 mV, and it is not a measurement. FB2-SAF-TSC-000001.diagnostic_coverage_assumptions records the two assumptions that estimate rests on - that consecutive samples are independent, which nothing in this corpus establishes, and that a threshold several sigma from the noise mean is a correct model of the operating point - and records that the same entry's common-cause note is that a debounce protects against noise and makes a systematic offset WORSE, because a real offset produces a confident, repeated violation. Second, no measurement exists of the 5 ms classification or of the 3 ms latch transition; both are allocations.
- **Source references**: `FB2-SRC-COD-000004`, `FB2-SRC-COD-000005`, `FB2-SRC-COD-000006`
- **Assumption references**: `FB2-ASM-001` (Lithium-ion cell chemistry with nominal voltage 3.7V, operat...), `FB2-ASM-005` (Cell voltage measurement noise follows Gaussian distribution...), `FB2-ASM-006` (Contactor mechanical opening time <= 30 ms (worst case) at -...)

#### `FB2-SAF-FSR-000003` — FSR: Contactor Opening on SOA Violation

- **Statement**: The BMS shall command all HV contactors to open within 5 ms of a FAULT state request from SOA/DIAG, shall reach the mechanically open state within 35 ms of that request, and shall confirm the commanded state from the auxiliary feedback within 40 ms of that request.
- **Rationale**: Contactor opening is the primary risk reduction measure. The chain is three segments, and each segment has its own bound: the coil command within 5 ms, the mechanical opening within 30 ms (FB2-PRM-000005, FB2-ASM-006, worst case over -40 to +85 degC), and the auxiliary feedback confirmation within a further 5 ms. From the FAULT request the mechanically open point is therefore 5 + 30 = 35 ms and th...
- **ASIL**: `ASIL_D`
- **Safety goal reference**: `FB2-SAF-SGO-000001`
- **Acceptance criteria**:
  - Contactor open latency: Time from FAULT request to contactor feedback open (auxiliary contacts confirm open) ≤ 40 ms
  - Contactor mechanically open latency: Time from FAULT request to contactor mechanically open, independent of the feedback segment ≤ 35 ms
  - Feedback verification: Auxiliary contact confirmation ≤ 100% %
  - Weld detection: Weld detection latency ≤ 50 ms
  - Coil de-energize command: Time from FAULT request to SBC coil command ≤ 5 ms
  - Coil de-energise to mechanically open: Time from SBC coil de-energise command to contactor mechanically open, against the 30 ms worst-case mechanical opening time of FB2-PRM-000005 ≤ 30 ms
- **Conditions/modes**: `NORMAL`, `CHARGING`, `PRECHARGE`, `DERATING`, `FAULT`
- **Fault reaction** (allocated element `AR-004`, owns reaction: True): De-energise every HV contactor coil through the safe base controller, confirm the commanded state from the auxiliary feedback, latch the fault and log it. This is the reaction FB2-SAF-FSC-000001 allocates to AR-004, and it is the only reaction on the main path that actually reaches the safe state. Both concepts give it 35 ms, which is the coil command at 5 ms plus the mechanical opening at 30 ms from FB2-PRM-000005; the confirmation of the commanded state is a further 5 ms that neither concept's 35 ms figure includes. Measured from the FAULT request the reaction is therefore complete at 40 ms, which is the figure this requirement's own acceptance criteria now ask for and the figure FB2-SAF-S...
  - triggered by: A FAULT state request from the SOA monitor (FB2-SAF-FSR-000002) or from a diagnosis entry; and, independently of that request, any state of the auxiliary feedback that disagrees with the commanded state, which is the weld-detection path.
  - reaction time budget: 35 ms
  - mode dependence: Mode-dependent, and this is the load-bearing caveat of the concept. In MOD-004, with the contactors closed and current flowing, opening them removes propulsion from a moving vehicle, so the item must distinguish a genuine limit violation from a degraded condition and must not enter FAULT for the latter. In MOD-001, MOD-002 and MOD-007 the reaction is unambiguous and immediate; in MOD-006 the state is already latched. Disconnecting a battery is itself an action with consequences and is not uncond...
  - allocation basis: FB2-SAF-FSC-000001.fault_reaction entry 1 ('Open all high-voltage contactors, disable charging, latch the fault and log it', element_id AR-004, reaction_time_budget_ms 35). The same element and budget appear in FB2-SAF-TSC-000001.fault_reaction, which adds that the reaction is realised by FB2-SW-SWR-000003 in software and FB2-HW-TSR-000003 in hardware and that the watchdog that makes it work after a software hang is independent of the main microcontroller (FB2-ASM-007). The five segments come fr...
  - open limits: Three limits are recorded and none is closed by this field. First, this record states a 50 ms weld-detection latency and FB2-HW-TSR-000003 states 100 ms for the same quantity. No record in this corpus decides which is intended, so neither figure was changed and the disagreement was left open rather than harmonised by editing one of the two numbers; FB2-REV-FND-000024 records it as deliberately not resolved. Second, FB2-ASM-007 assumes the safe base controller's watchdog is independent of the main microcontroller and can actuate the contactors on its own; FB2-SAF-TSC-000001.hardware_interfaces_and_assumptions records that this independence is read out of the source and that its behaviour over the full supply and temperature range is not measured, and that if it does not hold, a software hang leaves the contactors in their last commanded state with AR-005 the only remaining path. Third, th...
- **Source references**: `FB2-SRC-COD-000008`, `FB2-SRC-COD-000009`, `FB2-SRC-COD-000013`
- **Assumption references**: `FB2-ASM-001` (Lithium-ion cell chemistry with nominal voltage 3.7V, operat...), `FB2-ASM-006` (Contactor mechanical opening time <= 30 ms (worst case) at -...), `FB2-ASM-007` (SBC (FS85xx) watchdog is independent of main MCU and can tri...)

#### `FB2-SAF-FSR-000004` — FSR: Independent Hardware Voltage Monitor

- **Statement**: The item shall maintain, as a second barrier to the ASIL D cell-voltage safety goal FB2-SAF-SGO-000001, a cell-overvoltage detection and HV-contactor-opening capability that is independent of the main measurement, decision and command path, so that a failure confined to the main path does not remove the overvoltage reaction; the capability shall be allocated ASIL B and shall produce its contactor-open request within 50 ms of the overvoltage it detects.
- **Rationale**: Provides freedom from interference for the ASIL D safety goal: a main-path-only reaction leaves no tolerance in the 100 ms interval. As allocated in FB2-SAF-SGO-000001 the main path is 85 ms (25 acquisition + 5 SPI + 2 PEC + 3 publish + 5 SOA check + 2 classification + 3 state transition + 5 coil command + 30 mechanical + 5 feedback), which leaves 15 ms. At the 40 ms upper tolerance of FB2-PRM-000...
- **ASIL**: `ASIL_B`
- **Safety goal reference**: `FB2-SAF-SGO-000001`
- **Acceptance criteria**:
  - Reaction retained under main-path failure: Overvoltage test points at which the contactor-open request is still produced while the main microcontroller is held in reset, with no processing resource, no supply rail and no communication path of ... ≤ 100 % of test points
  - Independent detection latency: Time from the overvoltage being detected by the independent capability to its contactor-open request ≤ 50 ms
  - Overvoltage threshold accuracy: Difference between the overvoltage threshold the independent capability realises and the configured cell shutdown threshold ≤ 50 mV
- **Conditions/modes**: `NORMAL`, `CHARGING`, `PRECHARGE`, `DERATING`, `FAULT`
- **Fault reaction** (allocated element `AR-005`, owns reaction: True): Open the HV contactors directly from the independent path, without passing through the main microcontroller and without waiting for the main path's decision. This is the reaction FB2-SAF-FSC-000001 allocates to AR-005 at 50 ms, and it is the reason AR-005 exists: if the main path AR-001 to AR-004 fails, this is the only reaction left that still opens the contactors. Its 50 ms budget is FB2-PRM-000007 (independent_monitor_latency_ms = 50, tolerance 40..60) and it is an ALTERNATIVE to the main path's budget, not an addition to it - FB2-SAF-TSC-000001.ftti_and_timing_budget.arithmetic_check says so in words: the two budgets are alternatives, not a sum. Adding them would give 135 ms against a 10...
  - triggered by: The independent monitor's own hardware threshold being exceeded, measured through its own dividers and compared by its own comparator. It is not triggered by the main path's classification and it does not wait for one.
  - reaction time budget: 50 ms
  - mode dependence: No mode arbitration exists in this path, and both concepts record that as a property to be stated rather than assumed. It acts whenever its own threshold is exceeded. In MOD-004 that means a hardware false positive disconnects a moving vehicle with no arbitration, no confirmation step and no way for software to intervene, which is why the 50 mV threshold accuracy acceptance criterion of this requirement is a safety requirement in its own right and not only a specification detail. It is also why ...
  - allocation basis: FB2-SAF-FSC-000001.fault_reaction entry 2 ('Open the contactors through the independent path, without waiting for the main MCU', element_id AR-005, reaction_time_budget_ms 50). The same element and budget appear in FB2-SAF-TSC-000001.fault_reaction, which adds that the actuation output is separate from the main chain. The 50 ms is FB2-PRM-000007 and is the budget FB2-HW-TSR-000004 carries. The argument for the barrier is the arithmetic in this record's rationale: the main path is 85 ms of the 10...
  - open limits: The independence this reaction depends on is an assumption and is not demonstrated anywhere in this corpus. FB2-ASM-008 records that separate dividers, a separate power domain and separate actuation are required and that feasibility is to be confirmed. FB2-SAF-TSC-000001.hardware_interfaces_and_assumptions states the consequence if it is unmet - the independent monitor becomes a second channel with the same failure modes as the first, two agreeing channels would be read as corroboration when they are one channel twice, and the safety goal would have no surviving barrier - and states in the same entry that the absence of a demonstration is the largest open assumption of the ASIL D allocation. FB2-SAF-TSC-000001.diagnostic_coverage_assumptions gives this mechanism a justification_basis of synthetic_assumption with an empty verification_record_refs list. FB2-SAF-ANL-000003 is the dependent-...
- **Source references**: —
- **Assumption references**: `FB2-ASM-008` (Independent hardware voltage monitor (ASIL B) can be impleme...)

## Profile: `synthetic_reference` — System requirements (SYS.2)

These are system-level requirements: what the integrated item must do. Each refines a stakeholder need, a use-case obligation or the safety goal, and allocates to the existing hardware technical requirements (`FB2-HW-TSR-*`) and software requirements (`FB2-SW-SWR-*`) rather than restating them, which is why the requirement-to-test coverage matrix reports them as covered indirectly through those allocations.

### `FB2-SYS-SYR-000001` — SYR: every monitored cell voltage shall be acquired, validated and published with its age

- **Statement**: The item shall acquire the voltage of every monitored cell, validate the integrity of every transferred value before it is used by any decision, and publish each validated value together with the age of the acquisition that produced it, at a rate of at least 20 acquisitions per second in every mode in which the item is monitoring.
- **Rationale**: This is the system-level statement of what FB2-HW-TSR-000001 and FB2-SW-SWR-000001 together achieve. It is not a restatement of either: the hardware record states the measurement accuracy and the error-detection capability of the analogue chain, and the software record states the transfer scheduling and the publication latency. Neither states the age of the data, and the age is what makes every downstream timeout meaningful: a value without an ag...
- **Classification**: `interface` · **ASIL allocation**: `ASIL_D` · **safety goal**: `FB2-SAF-SGO-000001`
- **Refines**: `arch_elements`, `why_system_level`
- **Allocated to**: `FB2-SYS-NED-000001`, `FB2-SYS-NED-000004`
- **Architecture elements**: —
- **Verification approach**: `test`
- **Acceptance criteria**:
  - Acquisition rate: Acquisitions per second per monitored cell ≤ >= 20 Hz
  - Integrity validation coverage: Transferred values whose integrity was checked before any decision used them ≤ 100 %
  - Data age published: Published values carrying a valid age stamp ≤ 100 %
  - Stale-data rejection: Values older than the freshness limit that reach a decision unchallenged ≤ 0 values

### `FB2-SYS-SYR-000002` — SYR: the item shall enforce the configured safe operating area, and shall distinguish a recoverable measurement degradation from a limit violation

- **Statement**: The item shall compare every monitored cell voltage against the configured maximum and minimum limits, shall require two consecutive violations within 100 ms before classifying a violation, and shall move to its degraded mode rather than to the safe state when a measurement channel's disagreement is explainable by a degradation within the declared plausibility envelope, escalating to the safe state only when the degradation removes the reference the item needs.
- **Rationale**: The first half of this requirement restates the enforcement the safety goal needs. The second half is new at system level and is the boundary the stakeholder need FB2-SYS-NED-000002 depends on: the difference between a degraded item that stays usable and an item that disconnects on the first channel disagreement. Neither the existing SOA software requirement nor the plausibility requirement states that boundary, because in both cases the boundary...
- **Classification**: `safety` · **ASIL allocation**: `ASIL_D` · **safety goal**: `FB2-SAF-SGO-000001`
- **Refines**: `arch_elements`, `open_point`
- **Allocated to**: `FB2-SYS-NED-000001`, `FB2-SYS-NED-000002`
- **Architecture elements**: —
- **Verification approach**: `test`
- **Acceptance criteria**:
  - Debounce: Consecutive violations required within the window ≤ 2 violations per 100 ms
  - Classification latency: Time from a value being available to its classification being available ≤ <= 5 ms
  - Degradation reaction: Moderate channel disagreement producing a degraded state rather than a safe state ≤ 100 % of injected cases
  - Escalation on loss of reference: Total loss of the reference channel producing the safe state ≤ 100 % of injected cases
  - Degraded-to-fault boundary declared: Numerical value or named rule separating degraded from fault ≤ 1 declared value

### `FB2-SYS-SYR-000003` — SYR: the item shall reach and confirm the safe state within the fault-tolerant time interval, and shall latch the condition that required it

- **Statement**: On a confirmed safe-operating-area violation the item shall open all high-voltage contactors, disable charging and log the fault within 100 ms of the condition becoming measurable, shall confirm the open state by auxiliary feedback, and shall not leave that state on the fault disappearing.
- **Rationale**: The system-level statement of the safety goal's objective. It is written at this level because the obligation spans three allocated requirements - the software state machine, the hardware driver path and the hardware feedback path - and a requirement that any one of them could claim to satisfy would let the end-to-end timing go unstated. The figure here is the safety goal's own fault-tolerant time interval; the way that interval is spent is the t...
- **Classification**: `safety` · **ASIL allocation**: `ASIL_D` · **safety goal**: `FB2-SAF-SGO-000001`
- **Refines**: `arch_elements`, `known_conflict`
- **Allocated to**: `FB2-SYS-NED-000003`, `FB2-SAF-SGO-000001`
- **Architecture elements**: —
- **Verification approach**: `test`
- **Acceptance criteria**:
  - End-to-end reaction time: Time from the condition becoming measurable to the open state being confirmed ≤ <= 100 ms
  - Contactor state confirmation: Open states confirmed by auxiliary feedback ≤ 100 %
  - Latch behaviour: Faults that do not clear on the disappearance of the condition ≤ 100 %

### `FB2-SYS-SYR-000004` — SYR: the fault reaction shall be selected by mode, and a degraded condition shall never be reacted to as if it were a safe-operating-area violation

- **Statement**: The item shall select its reaction according to the mode it is in and the nature of the condition, shall reach the safe state on a confirmed safe-operating-area violation in every mode, and shall enter its degraded mode rather than the safe state on a condition that its own monitoring has classified as degraded. The item shall publish the mode it is in and the reason for any departure from normal operation.
- **Rationale**: This requirement exists because the master prompt states that one contactor action is not unconditionally safe in every operating situation, and because the two other requirements in this set are silent about it. Opening the contactors in the traction mode removes propulsion; opening them in the charging mode removes a hazard; opening them in commissioning mode is not reachable at all. A requirement that says 'open the contactors on a violation' ...
- **Classification**: `safety` · **ASIL allocation**: `ASIL_D` · **safety goal**: `FB2-SAF-SGO-000001`
- **Refines**: `arch_elements`, `verification_note`
- **Allocated to**: `FB2-SYS-NED-000002`, `FB2-SYS-NED-000003`
- **Architecture elements**: —
- **Verification approach**: `analysis`
- **Acceptance criteria**:
  - Mode-appropriate reaction: Reaction type selected matching the mode's specified behaviour ≤ 100 % of mode/condition combinations
  - No false escalation: Degraded conditions reacted to as safe-state conditions ≤ 0 events
  - Mode publication: Mode and departure reason published to the vehicle control unit ≤ within one publication period —

### `FB2-SYS-SYR-000005` — SYR: the item shall include a hardware voltage monitor that can detect an overvoltage and open the contactors without the main microcontroller

- **Statement**: The item shall include a cell-voltage monitor that measures through its own divider and comparator chain, holds its own threshold reference and its own supply, and commands the contactors open within 50 ms of detecting an overvoltage, using no processing resource, no supply rail and no communication path of the main microcontroller.
- **Rationale**: The system-level statement of the independent path. The functional safety requirement FB2-SAF-FSR-000004 and the hardware requirement FB2-HW-TSR-000004 state the same intent in identical words, which is a defect in the corpus rather than in the design: two records at two different ISO 26262 levels cannot be the same sentence. This record separates them by saying what is technically required, namely the separation of supply, reference, computation...
- **Classification**: `safety` · **ASIL allocation**: `ASIL_B` · **safety goal**: `FB2-SAF-SGO-000001`
- **Refines**: `arch_elements`, `independence_is_assumed`, `coverage_gap`
- **Allocated to**: `FB2-SAF-SGO-000001`, `FB2-SAF-FSR-000004`
- **Architecture elements**: —
- **Verification approach**: `test`
- **Acceptance criteria**:
  - Detection-to-command latency: Time from the hardware threshold being exceeded to the contactor command ≤ <= 50 ms
  - Processing independence: Processing resources of the main microcontroller used by the monitor path ≤ 0 resources
  - Supply independence: Supply rails shared with the main chain ≤ 0 rails
  - Communication independence: Communication paths shared with the main chain ≤ 0 paths
  - Threshold accuracy: Overvoltage threshold accuracy ≤ <= 50 mV

### `FB2-SYS-SYR-000006` — SYR: pack current and cell temperature shall be acquired, plausibility-checked and supplied to the item's supervisory functions

- **Statement**: The item shall acquire the pack current and the temperature of every monitored cell group, shall mark a measurement invalid when it cannot be trusted, and shall compare each valid value against the plausible operating envelope before using it in a supervisory decision.
- **Rationale**: The safety chain in this corpus is entirely a cell-voltage chain: the hazard, the safety goal and all four functional safety requirements concern cell voltage. Current and temperature supervision are system-level requirements nonetheless, because the item publishes charge and discharge limits that the converter is assumed to respect (FB2-ASM-003), and a limit published from an untrustworthy measurement is not a limit. This requirement is stated a...
- **Classification**: `interface` · **ASIL allocation**: `not_applicable` · **safety goal**: `N/A - no safety goal is assigned to the current and temperature paths in this corpus`
- **Refines**: `arch_elements`, `open_gap`
- **Allocated to**: `FB2-SYS-NED-000004`
- **Architecture elements**: —
- **Verification approach**: `test`
- **Acceptance criteria**:
  - Measurement validity marking: Acquisitions whose trust status is decided before use ≤ 100 %
  - Envelope check: Valid measurements compared against the envelope before supervisory use ≤ 100 %
  - Invalid data use: Invalid measurements reaching a supervisory decision unchallenged ≤ 0 values

### `FB2-SYS-SYR-000007` — SYR: the item shall publish its state and shall not accept a request that contradicts its own safety evaluation

- **Statement**: The item shall publish its mode, its charge and discharge limits and its active fault condition to the vehicle control unit, and shall act on a state request from that unit only when the request is consistent with the item's own safety evaluation; where it is not, the item shall refuse the request and publish the refusal with its reason.
- **Rationale**: The system-level statement of the integration contract with the vehicle manufacturer. It resolves the tension named in the stakeholder need FB2-SYS-NED-000004 in one direction and states the direction explicitly, because a requirement that said only 'the item honours state requests' would leave the safety case resting on the item being overridden cleanly, and 'cleanly' is not a property any record here establishes. The publication half is separat...
- **Classification**: `interface` · **ASIL allocation**: `not_applicable` · **safety goal**: `N/A - the interface itself is not allocated an ASIL; its integrity is bounded by the cybersecurity requirements FB2-SAF-SEC-000003 and FB2-SAF-SEC-000004`
- **Refines**: `arch_elements`, `dependency_direction`
- **Allocated to**: `FB2-SYS-NED-000004`
- **Architecture elements**: —
- **Verification approach**: `test`
- **Acceptance criteria**:
  - State publication completeness: Modes and active faults published in every mode ≤ 100 %
  - Limit publication: Charge and discharge limits published to the control unit ≤ 100 %
  - Refusal of inconsistent requests: Requests contradicting the item's own evaluation that were acted on ≤ 0 requests
  - Refusal diagnosability: Refusals published with a reason ≤ 100 %

### `FB2-SYS-SYR-000008` — SYR: commissioning and service shall not permit the item to energise on unconnected or untrusted inputs

- **Statement**: While the item is in its commissioning mode, no high-voltage contactor shall be commanded closed unless an explicit commissioning command is present, and an open-circuit or unconnected sensor input shall be diagnosed as such and shall not be interpreted as a cell at a limit; on leaving commissioning, the item shall return to a state in which no contactor actuation is possible without a current-flow request. Bytes received on a service link shall be acted upon only inside a validated, authenticated frame.
- **Rationale**: The system-level requirement behind the commissioning mode, and the one that carries the service-class stakeholder need FB2-SYS-NED-000005 into the item's architecture. Its second half is deliberately a cybersecurity requirement appearing at system level: the framing and authorisation of the service link is a property of the integrated item's interfaces, not of one module, and the security requirement FB2-SAF-SEC-000004 constrains the same link f...
- **Classification**: `safety` · **ASIL allocation**: `not_applicable` · **safety goal**: `N/A - commissioning is a service and production activity; its failure is a production escape rather than a runtime hazard, which is why it is not allocated an ASIL here`
- **Refines**: `arch_elements`, `why_not_asil`
- **Allocated to**: `FB2-SYS-NED-000005`
- **Architecture elements**: —
- **Verification approach**: `test`
- **Acceptance criteria**:
  - Actuation inhibition: Contactor close commands accepted while commissioning with no explicit commissioning command ≤ 0 commands
  - Open-circuit interpretation: Unconnected sense inputs interpreted as cell limit violations ≤ 0 interpretations
  - Return to inert state: States reachable after leaving commissioning that permit actuation without a current-flow request ≤ 0 states
  - Service-link framing: Bytes acted upon outside a validated, authenticated frame ≤ 0 bytes

---

## Profile: `synthetic_reference` — ISO 26262 Part 3 safety concepts

### `FB2-SAF-FSC-000001` — Functional Safety Concept: allocation of the cell-voltage safety goal to the architectural elements of the item

- **Concept stage**: `functional_safety_concept`
- **Item**: `FB2-SAF-ITE-000001` · **hypothetical**: `true`
- **Clause reference**: ISO 26262-3:2018 Clause 7 (working title: functional safety concept). The clause reference is recorded from the locked standards baseline; no clause text was consulted or reproduced.
- **Derived from**: `FB2-SAF-HAZ-000001`, `FB2-SAF-SGO-000001`, `FB2-SAF-FSR-000001`, `FB2-SAF-FSR-000002`, `FB2-SAF-FSR-000003`, `FB2-SAF-FSR-000004`, `FB2-SAF-ANL-000001`, `FB2-SAF-ANL-000004`, `FB2-SAF-SCS-000001`
- **Guard**: profile=`synthetic_reference`, origin=`synthetic`, human_approval_status=`pending`, production_authorized=`false`

**Scope boundary**

- Inside: Acquisition, validation and age-stamping of cell voltage and cell temperature
- Inside: Safe-operating-area monitoring, debounce, classification and the latched reaction
- Inside: Measurement plausibility and redundancy evaluation
- Inside: Contactor and precharge sequencing, actuation and feedback confirmation
- Inside: The independent hardware monitor and its own actuation path
- Inside: Supply and watchdog supervision as a barrier
- Inside: The integrity of the internal data path, to the extent that a forged or stale value could defeat a detection
- Outside (inherent_battery_hazard_outside_fuSaS_scope): Thermal runaway from cell chemistry — A property of the cells, not of an E/E system. No requirement in this concept can prevent it, and pretending otherwise would inflate the ASIL of the item over a hazard it does not ...
- Outside (inherent_battery_hazard_outside_fuSaS_scope): Mechanical protection of the pack — Venting and enclosure are mechanical. Their adequacy is the pack integrator's safety case.
- Outside (external_system_behaviour): Converter and charger control strategy — The item publishes limits and assumes they are respected (FB2-ASM-003). A converter that ignores them is an external-system behaviour failure, and the item's response to it is the ...
- Outside (external_system_behaviour): Vehicle-level crash isolation policy — Whether a collision requires isolation is a vehicle-level decision. The item supervises the interlock it is given.
- Outside (production_or_service_process): Production programming and end-of-line test execution — A lifecycle process, not a function. A wrongly configured item is a production escape, and it is handled by the production records, not by a functional requirement.
- Outside (environmental): Electromagnetic robustness of the item under the full test level — An environmental property. The concept assumes a level of robustness and does not claim to establish it.

- **Boundary argument**: The scope is the set of failures the item can cause or detect-and-react to. Every element inside the boundary can produce the hazardous event by failing to report an overvoltage, failing to report it in time, or failing to open the contactor. Every element outside the boundary either cannot produce the event at all, or produces it through a route that passes back into one of the inside elements (for example a converter that overdrives a cell produces an overvoltage, which AR-001 then detects and AR-004 then reacts to, so the requirement lands inside the boundary even though the cause does not). The argument is drawn at the item's electrical interfaces, not at its functions, because the item'...

**Architectural elements and their roles**

| Element | Name | Kind | Role | Owns objective part | Independence note |
|---|---|---|---|---|---|
| `AR-001` | Measurement acquisition and validation c... | hardware_and_software | Convert the cell voltages on the sense leads into validated, age-stamped values in the shared data store, or d... | Detection of the condition. It is the only element that can observe an out-of-range cell voltage in the first ... | Shares the supply and the MCU with AR-002 to AR-004. It is not independent of them; AR-005 is the independent ... |
| `AR-002` | Safe-operating-area decision function | software | Compare acquired values against the configured limits with a debounce, apply plausibility and redundancy check... | Confirmation. It decides that the condition is real rather than a measurement artefact, and it is the element ... | Runs on the main MCU. A failure of this element leaves AR-005 as the only barrier, which is the reason AR-005 ... |
| `AR-003` | Shared data and communication path | software | Carry measurements, ages and decisions between elements with a defined freshness and integrity, and exchange s... | Chain integrity. It holds no part of the objective on its own, but a stale or forged value crossing it invalid... | This is also the attack surface the cybersecurity concept bounds. Its integrity is assumed by FB2-SAF-SEC-0000... |
| `AR-004` | Contactor actuation and feedback path | hardware_and_software | Command the contactor drivers into the safe state, confirm by auxiliary feedback that the contactor actually o... | Actuation and confirmation. Without it the safe state is commanded but not achieved, which is a different outc... | Its controller has its own watchdog independent of the main MCU (FB2-ASM-007), which makes this element's actu... |
| `AR-005` | Independent hardware voltage monitor | hardware | Measure a subset of the cell voltages through its own dividers and comparator and open the contactors on its o... | A second, independent realisation of detection and actuation. It is the element that makes the ASIL D objectiv... | This is the element whose independence FB2-SAF-FSR-000004 claims. The claim is recorded as an assumption (FB2-... |
| `AR-006` | Supply and watchdog supervision | hardware | Detect an out-of-range or unstable supply and force the safe base controller into its defined state when the M... | None of the safety goal's objective is allocated to it. This is a deliberate statement: a design in which ever... | Its failure mode is benign to the goal: losing supply supervision means the watchdog no longer acts, which is ... |

**Safety strategies**

| Kind | Mechanism or reaction | Element | Budget (ms) | Note |
|---|---|---|---|---|
| detection | Front-end error-detection code on every measurement transfer | `AR-001` | 2 | Single-bit and double-bit errors in the transferred word |
| detection | Measurement plausibility and spread checks against independent channel... | `AR-002` | 5 | Front-end gain, offset and open-sense-line failures |
| detection | Safe-operating-area comparison with debounce | `AR-002` | 5 | Confirmed limit violations after two consecutive samples within 100 ms |
| detection | Contactor auxiliary feedback and weld detection | `AR-004` | 5 | Coil-path failure and welded contacts |
| detection | Independent hardware threshold monitor | `AR-005` | 50 | Every cell the item monitors, detected by the independent hardware monitor independently o... |
| detection | Link and watchdog supervision | `AR-003` | 5 | Not quantified |
| reaction | Open all high-voltage contactors, disable charging, latch the fault an... | `AR-004` | 35 | Mode-dependent, and this is the load-bearing caveat of the concept. In MOD-004 (closed, current flowing) opening the contactors removes propulsion fro... |
| reaction | Open the contactors through the independent path, without waiting for ... | `AR-005` | 50 | The independent path has no mode arbitration. It opens the contactors whenever its threshold is exceeded. In MOD-004 that means a hardware false posit... |
| reaction | Enter the latched FAULT mode and refuse to leave it without an authori... | `AR-002` | 3 | Mode-independent. The latch is what makes the safe state persistent rather than a transient that a clearing condition would undo. |
| reaction | Force the safe base controller into its defined state | `AR-006` | 5 | Mode-independent, and it is the reaction that still works when AR-002 has failed, which is the reason it exists. |

- **Degraded mode** `Derated charge and discharge with enhanced monitoring`: keeps Monitoring at a higher rate, charge and discharge within reduced limits, contactor control...; removes Full-rate charge and discharge, and the ability to claim the item is healthy; enters on A diagnosis entry whose severity permits operation but forbids full-rate transfer; duration Until the degraded condition is cleared by service or exceeds the vehicle's own derating t...
- **Degraded mode** `Reduced-rate monitoring after a measurement-path degradation`: keeps Contactor control and a coarser measurement set; removes Fast detection on the degraded channel; enters on Plausibility or redundancy detects a disagreement between channels; duration Until service; a degraded channel is not cleared by the condition disappearing

- **Safe state**: All high-voltage contactors open, charging disabled, propulsion disabled, fault logged and latched. The safe state is reachable from every mode and is identical in every mode; what differs between modes is how much capability is lost by reaching it, which is why the fault reaction above is stated per mode.
- **Strategy allocation**: Detection is split so that no single element both detects and acts: AR-001 and AR-005 detect, AR-002 confirms, AR-004 acts and confirms the action, AR-003 carries the decision, AR-006 acts only when the others have failed. A failure of AR-001 to AR-004 together is covered by AR-005, which shares nothing with them. A failure of AR-005 costs a barrier but does not cause the hazard, because the goal's objective is still achieved by AR-001 to AR-004 in that case. That asymmetry is the allocation's load-bearing property and it is what the ASIL D assignment rests on.

**Item-related assumptions**

- (synthetic_assumption) A cell can leave its safe operating area at any time without warning, and the item will observe it as a voltage outside the configured limit. — *if false:* If a cell failed in a way that stayed inside the limit while being dangerous (a chemistry failure at nominal voltage), every requirement in the concept would be satisfied and the hazard would still occur. The concept's coverage would be an illusion.
- (synthetic_assumption) Cell-voltage measurement noise is Gaussian with sigma not exceeding 5 mV. — *if false:* The debounce strategy in FB2-SAF-FSR-000002 is dimensioned on this figure. A heavier-tailed or correlated noise distribution would produce either late detection or a false reaction, and the recorded false-positive rate of 1e-6 per hour would be wrong...
- (synthetic_assumption) The contactor opens mechanically within 30 ms worst case over the whole temperature range. — *if false:* The mechanical part of the timing budget is spent before the item has finished deciding, and the whole FTTI is lost.
- (synthetic_assumption) The external converter respects the charge and discharge limits the item publishes. — *if false:* The item's safe operating area is not enforced by anyone; the item detects the excursion but the cause is outside its control, and the reaction is a protective disconnect rather than a correction.
- (synthetic_assumption) The independent hardware monitor can be built with a separate divider, comparator and supply, and can actuate the contactors without passing through the main MCU. — *if false:* The independent path is not independent, the ASIL D objective has no second barrier, and the freedom-from-interference claim in FB2-SAF-FSR-000004 is false.
- (source_observed) The real foxBMS source at commit 308028fb implements the observed measurement, SOA, contactor and diagnosis behaviour, so that grounding this concept on it grounds the concept on something that exists. — *if false:* The concept's grounding becomes an invention. The observed behaviour is recorded in the as_is profile and is not restated here as if it were the hypothetical item's verified behaviour.

**Interfaces to other safety-related items**

- **Vehicle high-voltage safety monitor** — Interlock assertion into the item and item state and insulation diagnosis out of it *Shared objective:* Shared objective in MOD-004 and MOD-006: both items may require the pack to be isolated. Neither coordinates with the other; both act independently.
- **Cell protection circuit embedded in each cell** — The cell's own overvoltage protection acts on the cell independently of the item *Shared objective:* Shared objective for overvoltage. Two independent mechanisms pursue the same safe outcome with thresholds the item does not control.
- **Cell-sensing front end and its analogue network** — The cell input network, its protection and its calibration are inside the item but are supplied by a component vendor *Shared objective:* None. The item owns the objective; the vendor owns the component's behaviour within its specification.

**External measures relied upon**

- Cell-level overvoltage protection inside each cell — owner Cell supplier (fictional role: cell_supplier_quality_engineer); why not the item: The cell protection is inside the cell, physically unreachable from the item, and reacts even with the item unpowered. It is a second barrier the item does not control and could no...
- Cell chemistry limits and the cell supplier's own safety case — owner Cell supplier (fictional role: cell_supplier_quality_engineer); why not the item: The safe operating area of the chemistry is a property of the chemistry. The item monitors against limits it is given; it cannot widen them.
- Vehicle high-voltage isolation on collision — owner Vehicle manufacturer (fictional role: vehicle_safety_owner); why not the item: The item supervises the interlock line. Whether a collision warrants isolation depends on vehicle-level information the item does not have.
- Certified recycling handling of an energised pack — owner Recycler (fictional role: recycler_safety_officer); why not the item: The item is removed from the vehicle before end of life. It contributes no control once it is disconnected.

**Contradictions found in the records this concept was written from**

These are recorded rather than absorbed. Neither the concept nor the conflicting record was edited to make them agree; each names the finding that carries it.

- **Contradiction**: The safety goal's timing budget allocation sums to 85 ms and its recorded margin is 20 ms, giving 105 ms against a fault-tolerant time interval of 100 ms. The margin is therefore larger than the time available, which means it is an overrun rather than a margin.
  - **Records in conflict**: `FB2-SAF-SGO-000001`, `FB2-SAF-FSC-000001`
  - **How this concept handles it**: RESOLVED at source. The safety goal's margin is now 15 ms, so its budget closes: 85 ms serial + 15 ms = 100 ms against the 100 ms interval, which is the figure this concept and FB2-SAF-TSC-000001 had already computed independently. The safety goal was revised rather than left in contradiction, and the two records no longer depart from one another. Finding FB2-REV-FND-000025.
  - **Finding**: `FB2-REV-FND-000025`
- **Contradiction**: FB2-SAF-FSR-000003 requires the contactors open within 30 ms of the fault request with feedback confirmation within a further 5 ms, so its own acceptance criterion (30 ms to feedback open) contradicts its own rationale (30 ms mechanical plus 5 ms feedback, i.e. 35 ms), and the safety goal allocates 5 ms of command plus 30 ms of mechanical time plus 5 ms of feedback verification, i.e. 40 ms, before detection.
  - **Records in conflict**: `FB2-SAF-FSR-000003`, `FB2-SAF-SGO-000001`
  - **How this concept handles it**: RESOLVED at source. FB2-SAF-FSR-000003 now states the three points of the chain separately: 5 ms to the coil command, 35 ms to the mechanically open contactor and 40 ms to the feedback-confirmed contactor, which is the 40 ms end-to-end figure this concept identified. Its 'Contactor open latency' criterion, which measures from the fault request to feedback open, now carries the 40 ms it was spending from rather than the 30 ms mechanical figure. Th...
  - **Finding**: `FB2-REV-FND-000024`
- **Contradiction**: FB2-SAF-FSR-000004 states a functional safety requirement whose text is identical, word for word, to the hardware technical safety requirement FB2-HW-TSR-000004, including the ASIL B allocation and the acceptance criteria.
  - **Records in conflict**: `FB2-SAF-FSR-000004`, `FB2-HW-TSR-000004`
  - **How this concept handles it**: RESOLVED at source. FB2-SAF-FSR-000004 and FB2-HW-TSR-000004 no longer carry the same text. The Part 4 record now states the safety intent and carries only behaviourally decidable criteria; the Part 5 record states the hardware obligation and carries the structural independence and coverage criteria, aligned with the statement this concept already published for FB2-HW-TSR-000004 in the technical concept's technical_safety_requirements block. AR-0...
  - **Finding**: `FB2-REV-FND-000027`
- **Contradiction**: FB2-SAF-FSR-000004 justifies the independent monitor by a main-path figure of 115 ms against the 100 ms FTTI. No record in the corpus contains 115 ms; the safety goal's own allocation for the main path sums to 85 ms.
  - **Records in conflict**: `FB2-SAF-FSR-000004`, `FB2-SAF-SGO-000001`
  - **How this concept handles it**: RESOLVED at source, and this block's premise is corrected. The 115 ms figure is not unsourced: it is the sum of a superseded allocation recorded in FB2-REV-000001 (as_is vertical-slice review, embedded finding FB2-FND-000001) as 'FSR-001 specifies 10 Hz (100 ms); FSR-002 specifies 10 ms check; FSR-003 specifies 5 ms contactor; sum = 115 ms'. It is stale, not fabricated, and it described an allocation the corpus has since replaced. FB2-SAF-FSR-000...
  - **Finding**: `FB2-REV-FND-000026`

**What this concept does not establish**

- This concept is synthetic and describes a hypothetical programme. It establishes no property of the real foxBMS project and asserts no ASIL capability.
- No diagnostic coverage figure in this concept is measured. Every one is either a requirement-side claim, an analytical estimate on an assumed noise distribution, or an assumption about a component that this corpus has not measured.
- The independence of the hardware monitor is assumed (FB2-ASM-008), not demonstrated. An independent-monitor concept that had been analysed for common-cause failure would state which failures it does and does not cover; this one states that no such analysis exists in the corpus, which is why the dependent-failure analysis FB2-SAF-ANL-000003 exists and is referenced rather than replaced.
- This concept does not verify anything. Verification is planned and, where a fixture exists, executed, in the FB2-VER-* records; none of that evidence is product evidence.
- The architecture is a high-level functional decomposition. It says what each element is accountable for and not how any of them is built, and it does not establish that the elements as described can be built within the stated timing.
- Human approval of this concept is pending. No functional-safety expert has confirmed it, and an automated review pass is not the independent confirmation an ASIL D concept requires.

### `FB2-SAF-TSC-000001` — Technical Safety Concept: hardware/software allocation, technical safety requirements, timing budget and diagnostic-coverage assumptions for the cell-voltage safety goal

- **Concept stage**: `technical_safety_concept`
- **Item**: `FB2-SAF-ITE-000001` · **hypothetical**: `true`
- **Clause reference**: ISO 26262-4:2018 Clause 7 (working title: technical safety concept), recorded from the locked standards baseline. No clause text was consulted or reproduced.
- **Derived from**: `FB2-SAF-FSC-000001`, `FB2-SAF-SGO-000001`, `FB2-SAF-FSR-000001`, `FB2-SAF-FSR-000002`, `FB2-SAF-FSR-000003`, `FB2-SAF-FSR-000004`, `FB2-HW-TSR-000001`, `FB2-HW-TSR-000002`, `FB2-HW-TSR-000003`, `FB2-HW-TSR-000004`, `FB2-SW-SWR-000001`, `FB2-SW-SWR-000002`, `FB2-SW-SWR-000003`, `FB2-SAF-ANL-000002`, `FB2-SAF-ANL-000003`
- **Guard**: profile=`synthetic_reference`, origin=`synthetic`, human_approval_status=`pending`, production_authorized=`false`

**Scope boundary**

- Inside: The technical realisation of acquisition, validation and age-stamping (AR-001)
- Inside: The technical realisation of limit comparison, debounce and classification (AR-002)
- Inside: The integrity and freshness of the path between them (AR-003)
- Inside: The technical realisation of actuation and its confirmation (AR-004)
- Inside: The independent hardware detection and actuation path (AR-005)
- Inside: Supply and watchdog supervision as a barrier (AR-006)
- Outside (inherent_battery_hazard_outside_fuSaS_scope): Thermal runaway from cell chemistry — No circuit in this concept can prevent it. It is inherited from the functional concept's scope statement and restated here so that no reader of the technical concept mistakes the A...
- Outside (inherent_battery_hazard_outside_fuSaS_scope): Pack mechanical protection — Mechanical, not technical.
- Outside (external_system_behaviour): Converter and charger control strategies — External-system behaviour; the item's technical responsibility stops at publishing limits and reacting to the excursion.
- Outside (environmental): Electromagnetic robustness of the item — An environmental property this concept assumes and does not establish. No requirement in it states an EMC level.

- **Boundary argument**: Inherited from FB2-SAF-FSC-000001 and unchanged by it: the technical scope follows the functional scope element for element. The technical concept adds nothing to the boundary and removes nothing from it; where the two could have diverged - for instance by placing the independent monitor outside the scope because it is a redundant path rather than a function - this concept keeps it inside, because a redundant safety path is inside the scope precisely because it carries part of the objective.

**Architectural elements and their roles**

| Element | Name | Kind | Role | Owns objective part | Independence note |
|---|---|---|---|---|---|
| `AR-001` | Measurement acquisition and validation c... | hardware_and_software | Acquire and validate every cell voltage and publish it with its age. | Technical detection of the condition. | Shares the MCU, the supply and the store with AR-002 to AR-004. |
| `AR-002` | Safe-operating-area decision function | software | Compare against limits with debounce, apply plausibility and redundancy, classify and request the safe state. | Technical confirmation of the condition. | Main MCU. Its failure leaves AR-005 as the only barrier. |
| `AR-003` | Shared data and communication path | software | Carry measurements, ages and decisions with defined freshness and integrity. | Technical chain integrity between detection, decision and actuation. | Assumed by the safety requirements; its integrity is bounded by the cybersecurity requirements FB2-SAF-SEC-000... |
| `AR-004` | Contactor actuation and feedback path | hardware_and_software | Command the drivers into the safe state, confirm by auxiliary feedback, detect a welded contactor. | Technical actuation and confirmation of the safe state. | The watchdog is independent of the main MCU (FB2-ASM-007). |
| `AR-005` | Independent hardware voltage monitor | hardware | Measure through its own dividers and comparator and actuate the contactors without passing through the main MC... | The independent technical realisation of detection and actuation. | Assumed by FB2-ASM-008 and not demonstrated anywhere in this corpus. |
| `AR-006` | Supply and watchdog supervision | hardware | Detect supply out of range and force the controller into its defined state when the MCU stops servicing it. | No part of the goal's objective. Retained deliberately so that at least one element's failure is harmless to t... | Hardware only; a failure here loses a barrier rather than causing the hazard. |

**Safety strategies**

| Kind | Mechanism or reaction | Element | Budget (ms) | Note |
|---|---|---|---|---|
| detection | Front-end integrity code on every transferred word | `AR-001` | 2 | Single-bit transfer errors |
| detection | Limit comparison with debounce | `AR-002` | 5 | Confirmed violations after two samples within 100 ms |
| detection | Plausibility and redundancy comparison | `AR-002` | 5 | Not quantified anywhere in this corpus |
| detection | Auxiliary contact feedback and weld detection | `AR-004` | 5 | Coil-path failure and welded contacts |
| detection | Independent hardware threshold monitor | `AR-005` | 50 | Every cell the main measurement chain monitors, measured by the independent divider networ... |
| reaction | Open all high-voltage contactors, disable charging, latch and log | `AR-004` | 35 | Realised by FB2-SW-SWR-000003 in software and FB2-HW-TSR-000003 in hardware. Mode-dependent: in MOD-004 this removes propulsion, so the software state... |
| reaction | Open the contactors from the independent path without the main MCU | `AR-005` | 50 | No mode arbitration exists in this path. It acts whenever its threshold is exceeded, which is why its threshold accuracy is a safety requirement and w... |
| reaction | Enter the latched FAULT mode and refuse to leave it without authorised... | `AR-002` | 3 | Mode-independent. |
| reaction | Force the controller into its defined state | `AR-006` | 5 | Mode-independent; this is the reaction that still works when AR-002 has failed. |

- **Degraded mode** `Derated charge and discharge with enhanced monitoring`: keeps Contactor control, reduced-rate transfer, increased monitoring rate; removes Full-rate transfer and any claim of item health; enters on A diagnosis entry permitting operation but forbidding full rate; duration Until cleared by service or until the vehicle's derating limit expires
- **Degraded mode** `Reduced-rate monitoring after a measurement-path degradation`: keeps Contactor control and a coarser measurement set; removes Fast detection on the degraded channel; enters on Plausibility or redundancy detects channel disagreement; duration Until service; a degraded channel is not cleared by the condition disappearing

- **Safe state**: All high-voltage contactors open, charging disabled, propulsion disabled, fault logged and latched. Reachable from every mode; what differs between modes is the capability lost by reaching it.
- **Strategy allocation**: Each strategy above names the requirement that carries it technically. The technical allocation is deliberately not uniform: the independent path AR-005 is hardware-only and ASIL B, the main path is split hardware/software and ASIL D, and AR-006 is hardware-only with no part of the objective. A concept in which every strategy were realised by the same kind of element in the same way would have no independence argument at all.

**FTTI and timing budget**

| Element | Budget (ms) |
|---|---|
| afe_acquisition_ms (`AR-001`) | 25 |
| spi_transfer_ms (`AR-001`) | 5 |
| pec_validation_ms (`AR-001`) | 2 |
| database_publish_ms (`AR-001`) | 3 |
| soa_limit_check_ms (`AR-002`) | 5 |
| fault_classification_ms (`AR-002`) | 2 |
| sys_state_transition_ms (`AR-002`) | 3 |
| contactor_command_ms (`AR-004`) | 5 |
| contactor_mechanical_ms (`AR-004`) | 30 |
| feedback_verification_ms (`AR-004`) | 5 |
| **FTTI** | **100** |

- Serial sum: 85 ms · margin: 15 ms
- **Arithmetic statement**: 25 + 5 + 2 + 3 + 5 + 2 + 3 + 5 + 30 + 5 = 85 ms of serial work. The fault-tolerant time interval is 100 ms, so the margin available is 100 - 85 = 15 ms, and this concept allocates exactly 15 ms of it. The budget therefore closes with no deficit. This concept originally recorded that allocation as a deliberate departure from FB2-SAF-SGO-000001, which then carried a 20 ms margin and therefore a 105 ms total against the same 100 ms interval. That departure no longer exists: FB2-SAF-SGO-000001 now records the 15 ms margin as well, so the two records agree and the safety goal's budget closes. The 105 ms was not rounded to 100 ms; the margin was corrected to the value the interval admits, and 85 + 15 = 100. The reaction chain at the end of the budget is 5 ms coil command + 30 ms mechanical opening + 5 ms feedback verification = 40 ms, and FB2-SAF-FSR-000003 now states those three points separa...

**Hardware / software allocation**

| Element | Allocated to | Responsibility | Why the split |
|---|---|---|---|
| `AR-001` | split | The front end, its dividers, the isolation and the measurement chain are hardware; the transfer scheduling, the error-code validat... | The accuracy and the error-detection capability are properties of the analogue chain and cannot be implemented in software, while the guarantee that a... |
| `AR-002` | software | Limit comparison, debounce, plausibility, redundancy, severity classification and the request for the safe state. | These are decisions over a data set that only exists in memory. There is no hardware implementation of a debounce that would be cheaper or safer here;... |
| `AR-003` | software | The shared store, its consistency mechanism, the age stamp on every entry and the message-level integrity and freshness of the ext... | The integrity mechanism is a protocol and a dispatch policy. The hardware can guarantee that bytes arrive; only the software can decide which bytes ar... |
| `AR-004` | split | The safe base controller, its independent watchdog and the coil drivers are hardware; the state machine that decides when to comma... | The actuation must work when the MCU has stopped, so the watchdog and the final driver stage are hardware (FB2-ASM-007). The decision to act is a soft... |
| `AR-005` | hardware | The independent dividers, the comparator, its threshold reference and its own actuation output. Entirely hardware. | The whole point of this element is that it does not pass through the main MCU. Any software in it would share the failure domain it exists to escape. ... |
| `AR-006` | hardware | Supply supervision, the watchdog window and the reset path. Entirely hardware. | It must act when the software cannot run, which rules out any software dependency. |

**Technical safety requirements carried by this allocation**

| Requirement | Type | Element | Verification | Statement |
|---|---|---|---|---|
| `FB2-HW-TSR-000001` | hardware | `AR-001` | test | The cell-voltage measurement chain measures with 1.5 mV total error including calibration over -40 to +85 degC, with 0.5... |
| `FB2-HW-TSR-000002` | hardware | `AR-001` | test | The slave link provides a bit error rate below 1e-9, detects communication failure within 5 ms and covers the transfer w... |
| `FB2-HW-TSR-000003` | hardware | `AR-004` | test | The safe base controller drives the contactor coils at a controlled slew rate and reports the auxiliary feedback to soft... |
| `FB2-HW-TSR-000004` | hardware | `AR-005` | test | An independent hardware voltage monitor measures cell voltages through its own dividers and opens the contactors within ... |
| `FB2-SW-SWR-000001` | software | `AR-001` | test | The acquisition driver triggers the transfer at 20 Hz, validates the integrity code on every word and publishes validate... |
| `FB2-SW-SWR-000002` | software | `AR-002` | test | The safe-operating-area monitor compares every cell voltage against the configured limits with a debounce of two consecu... |
| `FB2-SW-SWR-000003` | software | `AR-004` | test | The contactor state machine executes OPEN to PRECHARGE to CLOSE to HOLD, de-energises the coils within 5 ms of a fault r... |

**Diagnostic-coverage assumptions**

| Mechanism | Claimed coverage | Basis | Independence assumption | Verification records |
|---|---|---|---|---|
| Front-end integrity code on every measurement transfer (AR-0... | Every single-bit error in a transferred cell-voltage word is detected before the value reaches the d... | `analytical_model` | The check is performed in AR-001, the same element that produced the value. A front end that both corrupts a v... | `FB2-VER-TMS-000001`, `FB2-VER-EXE-000001` |
| Debounce on the limit comparison (AR-002) | A false reaction rate below 1e-6 per hour for Gaussian measurement noise with sigma 5 mV, while dete... | `analytical_model` | Consecutive samples are treated as independent. Correlated noise would change the rate materially and nothing ... | `FB2-VER-TMS-000005`, `FB2-VER-EXE-000005` |
| Measurement plausibility and redundancy comparison (AR-002) | A front-end gain error, an offset error and an open sense line are detected because each produces a ... | `synthetic_assumption` | The redundant channel must be genuinely independent of the channel it checks. FB2-SAF-ANL-000003 records that ... | **none** |
| Contactor auxiliary feedback and weld detection (AR-004) | A welded contactor is detected within 100 ms of the commanded state disagreeing with the feedback. | `analytical_model` | The auxiliary contact path and the coil drive path share no element that can fail open in both. | `FB2-VER-TMS-000003`, `FB2-VER-EXE-000003` |
| Independent hardware threshold monitor (AR-005) | Every cell the main measurement chain monitors is also measured by the independent divider network a... | `synthetic_assumption` | Assumed (FB2-ASM-008): separate dividers, separate comparator, separate supply and no communication with the m... | **none** |

- *Front-end integrity code on every measurement transfer (AR-0...* — A parity or CRC of the width the front end specifies, applied to every word. The detection property of such a code is a property of its polynomial and width, which is a matter of arithmetic rather than of measurement.
- *Debounce on the limit comparison (AR-002)* — For a threshold placed several sigma from the noise mean, the probability that two consecutive samples both fall beyond the threshold is the square of the single-sample tail probability. At 20 Hz that yields the stated rate. The arithmetic is a property of the assumed distribution, which is itself an assumption (FB2-ASM-005), so the figure is conditional on that assumption and is not a measurement of the real item.
- *Measurement plausibility and redundancy comparison (AR-002)* — The mechanisms are self-evident from their design intent and are implemented in the observed source. What is NOT established is their coverage: the corpus contains no fault-injection campaign that quantifies which injected faults are detected and which are not, and no plausibility limit is expressed as a diagnostic-coverage figure.
- *Contactor auxiliary feedback and weld detection (AR-004)* — The auxiliary contacts are wired independently of the coil drive, so a welded contactor produces a state disagreement that no failure of the drive path can mask. This is a wiring argument, and its validity depends on the wiring being as described, which no inspection record in this corpus establishes.
- *Independent hardware threshold monitor (AR-005)* — The requirement FB2-HW-TSR-000004 now states this coverage as 100 percent of the main chain's monitored cell set, which is decidable on hardware: measure which cells the independent divider network reaches and divide by which cells the main chain reaches. The previous wording of this entry carried the requirement's own disjunction ('all monitored cells, or a representative subset of at least 50%') forward, which was not a measurable coverage statement; finding FB2-REV-FND-000027 recorded that an...

**Hardware interfaces and assumptions**

| Element | Assumption | Basis | If unmet |
|---|---|---|---|
| `AR-005` | AR-005 shares no MCU, no supply rail and no communication path with AR-001 to AR-004. | FB2-ASM-008, a declared assumption. It is the assumption the whole ASIL D allocation leans on and it is not demonstrated anywhere ... | The independent monitor becomes a second channel with the same failure modes as the first. Two agreeing channels would then be read as corroboration when in fact they are one chann... |
| `AR-004` | The safe base controller's watchdog is independent of the main MCU and can actuate the contactors on its own. | FB2-ASM-007, grounded in the observed watchdog arrangement in the pinned source. The independence is read out of the source; its b... | A software hang leaves the contactors in their last commanded state and the software-side fault reaction never runs. The hardware monitor AR-005 would then be the only remaining pa... |
| `AR-001` | The cell input network and its calibration deliver the stated 1.5 mV total error over the full temperature range. | The requirement FB2-HW-TSR-000001 states the figure. No measurement of it exists in this corpus; the closest related record is a h... | A total error comparable to the margin between the configured limit and the last cell that must remain in service would make the limit boundary ambiguous, and the 1 mV threshold ac... |
| `AR-006` | The supply rails stay inside their specified range for long enough for the watchdog to act deliberately. | Engineering assumption. The observed source contains supply supervision and a supply-related diagnosis entry, but no characterisat... | A supply collapse faster than the watchdog window produces an uncontrolled shutdown of the contactor drivers. Whether that is safe depends on the driver's fail state, which this co... |
| `AR-003` | Every value in the shared store carries an age, and a value older than its consumer's freshness limit is rejected rather than used. | FB2-SAF-FSR-000001 states a freshness criterion of 30 ms and FB2-SAF-SEC-000003 requires freshness verification on the external in... | A decision is taken on a value from an earlier acquisition period. The effect is a detection that is late by exactly the staleness, which is spent from the same 100 ms budget. |

**Interfaces to other safety-related items**

- **Cell protection circuit embedded in each cell** — The cell's own protection opens the cell on overvoltage independently of the item's contactors. *Shared objective:* Shared objective. Two mechanisms with thresholds the item does not control act on the same physical quantity.
- **Vehicle high-voltage safety monitor** — Interlock assertion into the item; item state and insulation diagnosis out of it. *Shared objective:* Shared objective in the fault and closed modes.
- **Component vendor for the cell-sensing front end** — The front end, its error-detection code and its accuracy specification. *Shared objective:* None; the item owns the objective and the vendor owns the component's behaviour within its specification.

**External measures relied upon**

- Cell-level overvoltage protection inside each cell — owner Cell supplier (fictional role: cell_supplier_quality_engineer); why not the item: Physically inside the cell and active with the item unpowered. The technical concept depends on it existing; it cannot verify it and does not claim to.
- Fuse and pyro-fuse in the pack for overcurrent events outside the item's measurement bandwidth — owner Pack integrator (fictional role: pack_safety_owner); why not the item: A short-circuit event can develop faster than any measurement-and-react cycle. The item's reaction is supplementary for these events, not primary.
- Vehicle-level insulation monitoring and crash isolation — owner Vehicle manufacturer (fictional role: vehicle_safety_owner); why not the item: The item supervises the interlock; it does not decide vehicle-level isolation.

**Contradictions found in the records this concept was written from**

These are recorded rather than absorbed. Neither the concept nor the conflicting record was edited to make them agree; each names the finding that carries it.

- **Contradiction**: The timing budget of FB2-SAF-SGO-000001 sums to 105 ms against a 100 ms FTTI (85 ms serial plus a 20 ms margin).
  - **Records in conflict**: `FB2-SAF-SGO-000001`, `FB2-SAF-TSC-000001`
  - **How this concept handles it**: RESOLVED at source. FB2-SAF-SGO-000001 now records a 15 ms margin, so its budget closes at 100 ms and this concept's allocation is no longer a departure from it but a restatement of it. The safety goal was revised rather than left in contradiction. Finding FB2-REV-FND-000025.
  - **Finding**: `FB2-REV-FND-000025`
- **Contradiction**: FB2-SAF-FSR-000003's acceptance criterion (contactors open within 30 ms of the fault request) contradicts its own rationale (30 ms mechanical plus 5 ms feedback, 35 ms) and contradicts this concept's allocation (5 ms command plus 30 ms mechanical plus 5 ms feedback, 40 ms end to end).
  - **Records in conflict**: `FB2-SAF-FSR-000003`, `FB2-SAF-TSC-000001`
  - **How this concept handles it**: RESOLVED at source. FB2-SAF-FSR-000003's 'Contactor open latency' criterion now reads 40 ms, which is the end-to-end figure this concept computed, and a separate criterion states the 35 ms mechanically-open point. The concept's own allocation is unchanged. Finding FB2-REV-FND-000024.
  - **Finding**: `FB2-REV-FND-000024`
- **Contradiction**: FB2-HW-TSR-000004 restates FB2-SAF-FSR-000004 word for word, so the two records cannot be at different ISO 26262 levels.
  - **Records in conflict**: `FB2-SAF-FSR-000004`, `FB2-HW-TSR-000004`
  - **How this concept handles it**: RESOLVED at source. FB2-HW-TSR-000004's statement now matches the statement_summary this concept already published for it in the technical_safety_requirements block, and FB2-SAF-FSR-000004 carries a different statement with the functional-level criteria. The two records are now reviewable as two distinct obligations. Finding FB2-REV-FND-000027.
  - **Finding**: `FB2-REV-FND-000027`
- **Contradiction**: FB2-SAF-FSR-000004's justification cites a 115 ms main path that appears in no record; the safety goal's own allocation for that path is 85 ms.
  - **Records in conflict**: `FB2-SAF-FSR-000004`, `FB2-SAF-SGO-000001`
  - **How this concept handles it**: RESOLVED at source, and this block's premise is corrected. The 115 ms is the sum of a superseded allocation recorded in FB2-REV-000001 embedded finding FB2-FND-000001 (100 ms acquisition period at 10 Hz + 10 ms SOA check + 5 ms contactor), not an unsourced figure. It is stale, not fabricated, and has been removed from FB2-SAF-FSR-000004, FB2-HW-TSR-000004 and FB2-ASM-008. The justification is now stated on the 85 ms figure that does exist and on ...
  - **Finding**: `FB2-REV-FND-000026`
- **Contradiction**: FB2-SAF-FSR-000004's monitoring-coverage acceptance criterion is a disjunction ('all cells or representative subset >= 50%') and is not measurable.
  - **Records in conflict**: `FB2-SAF-FSR-000004`, `FB2-HW-TSR-000004`
  - **How this concept handles it**: RESOLVED at source. The coverage criterion is no longer carried unchanged and no longer labelled synthetic_assumption. FB2-HW-TSR-000004 now states coverage as 100 percent of the cells the main measurement chain monitors, with the population named, and FB2-SAF-FSR-000004 no longer carries a coverage criterion at all because coverage is a hardware allocation property rather than a functional one. The 100 percent figure follows the precedent of FB2...
  - **Finding**: `FB2-REV-FND-000027`

**What this concept does not establish**

- This concept is synthetic and establishes no ASIL capability for any real product. Human approval is pending and no independent functional-safety confirmation exists.
- No diagnostic coverage figure here is measured. Two entries are analytical models whose validity rests on stated assumptions, two are synthetic assumptions with no evidence at all, and one is a wiring argument that no inspection record supports.
- The technical safety requirements listed here are the ones that already exist in the corpus. This concept does not derive new technical requirements, so parts of the allocation above are covered by requirement text written before the allocation was made. That is a real limitation and it is why the AR-005 coverage claim could not be improved here.
- The timing budget is an allocation of intent. It is not a worst-case analysis: no WCET, no queueing analysis and no measured execution time for any of its ten entries exists in this corpus. A budget that is internally consistent is not the same as a budget that is met.
- The independent hardware monitor has no schematic, no BOM and no analysis in this corpus. Its allocation to AR-005 is a statement of where the concept wants it, not a description of a circuit that exists.
- No requirement in this concept has been verified against the real product. The existing executions that touch these elements are synthetic fixtures or blocked records; see the FB2-VER-EXE-* set.

## Cybersecurity Work Products (Threat Analysis and Derived Security Requirements)

This section carries the corpus' cybersecurity work products. They are placed in the System Requirements Specification rather than in the Software Requirements Specification because they are system-level work products: the threat set is drawn from system-level assets (CAN bus, Ethernet interface, serial link, commissioning toolchain), and the mitigations they carry protect system-level safety goals. Both are `synthetic_reference` artifacts; the `as_is` profile contains none, because the real foxBMS 2 project holds no threat analysis and no cybersecurity work product.

**Guard flags — read before using anything in this section:**

- The threat analysis below is a **corpus-local simplified threat and risk analysis**. Its `method.is_iso_21434_tara` field is machine-pinned to `false` by schema. It is **not** an ISO/SAE 21434 TARA and no ISO/SAE 21434 work product exists in this corpus.
- No TARA in this corpus has been **reviewed or approved** by any cybersecurity, functional-safety or vehicle-level authority. `human_approval_status` is `pending` and `production_authorized` is `false` on every record below.
- **No residual risk is accepted.** `residual_risk_acceptance.acceptance_exists` is machine-pinned to `false` and `accepted_by` to `none` on the TARA record.
- No **penetration test, exploit, fuzzing campaign or CVSS assessment** was performed in producing any record below. A threat listed here is a static reading of code, not a demonstrated exploitable weakness.
- A requirement marked *control absent* below means the corresponding control is **not present in the real foxBMS 2 source at commit 308028fb**. It does not mean the control is absent from any hypothetical product, and no statement here should be read as a claim that the real foxBMS product is secure or insecure in absolute terms.

### `FB2-SAF-TAR-000001` — TARA: foxBMS 2 master external communication attack surface (CAN, Ethernet/TCP, RS485/UART)

- **Profile**: `synthetic_reference` · **Origin**: `synthetic` · **Owner role**: `cybersecurity_engineer` · **Lifecycle**: `draft` · **Human approval**: `pending` · **Production authorized**: `false` · **Product verification credit**: `false`
- **Method**: Corpus-local asset-driven threat enumeration and risk tabulation (source-evidence-first)
- **Is an ISO/SAE 21434 TARA**: `false` (schema-pinned to `false`)
- **Residual risk accepted**: `false` by `none`
- **Item under analysis**: foxBMS 2 BMS master communication stack: the CAN interface, the FreeRTOS-Plus-TCP Ethernet/TCP application layer (EMAC + PHY + FreeRTOS_Sockets), and the SCI/UART serial interface, together with the host-side engineering toolchain that can write to the target.
- **Declared limitations of the analysis**: 9 — see the record for the full list

**Threats (8 total, 6 evidenced in the pinned source, 2 hypothetical-project judgements):**

| Threat | Origin | Observed in source | Target assets | Residual risk | Mitigations |
|---|---|---|---|---|---|
| `THR-001` | `source_observed` | yes | `AST-001`, `AST-002`, `AST-009` | `medium` | `MIT-001`, `MIT-002` |
| `THR-002` | `source_observed` | yes | `AST-002` | `low` | `MIT-001`, `MIT-002` |
| `THR-003` | `source_observed` | yes | `AST-001`, `AST-002` | `low` | `MIT-002`, `MIT-008` |
| `THR-004` | `source_observed` | yes | `AST-005` | `medium` | `MIT-006` |
| `THR-005` | `source_observed` | yes | `AST-003` | `medium` | `MIT-004`, `MIT-007` |
| `THR-006` | `source_observed` | yes | `AST-004`, `AST-007` | `low` | `MIT-005`, `MIT-008` |
| `THR-007` | `synthetic` | no | `AST-008` | `not_rated` | `MIT-001`, `MIT-002` |
| `THR-008` | `synthetic` | no | `AST-006` | `not_rated` | `MIT-009` |

**Mitigations (9 total, 3 present or partially present in the pinned source, 6 absent or forward-engineered):**

| Mitigation | Type | Status | Verification status | Maps to |
|---|---|---|---|---|
| `MIT-001` | preventive | `absent_in_source` | `not_verified` | `FB2-SAF-SEC-000001` |
| `MIT-002` | preventive | `absent_in_source` | `not_verified` | `FB2-SAF-SEC-000002` |
| `MIT-003` | preventive | `present_in_source` | `verified_by_inspection_of_source` | `FB2-SAF-SEC-000002` |
| `MIT-004` | preventive | `absent_in_source` | `not_verified` | `FB2-SAF-SEC-000003` |
| `MIT-005` | preventive | `absent_in_source` | `not_verified` | `FB2-SAF-SEC-000004` |
| `MIT-006` | preventive | `absent_in_source` | `not_verified` | `FB2-SAF-SEC-000005` |
| `MIT-007` | detective | `present_in_source` | `verified_by_inspection_of_source` | `FB2-SAF-SEC-000003` |
| `MIT-008` | reactive | `absent_in_source` | `not_verified` | `FB2-SAF-SEC-000002`, `FB2-SAF-SEC-000004` |
| `MIT-009` | preventive | `partially_present_in_source` | `not_verified` | `FB2-SAF-SEC-000005` |

Mitigation status is the load-bearing column. `present_in_source` means the mechanism was read out of the pinned source; `absent_in_source` means the record establishes by reading the source that the mechanism is **not** there; `forward_engineered_synthetic` means the mitigation is a proposal of the hypothetical project with no verification evidence.

### Derived Security Requirements

5 security requirement artifacts, all `origin: synthetic` and all `verification_status: not_verified`. Each states in its own `real_source_presence` field whether the corresponding control exists in the real foxBMS 2 source.

| Requirement | Title | Class | Control present in the real foxBMS 2 source? | Verification |
|---|---|---|---|---|
| `FB2-SAF-SEC-000001` | SEC-000001: Authenticated and confidential transport for externally reachable network serv... | `security` | **NO — absent** | `not_verified` |
| `FB2-SAF-SEC-000002` | SEC-000002: Bounded connection admission and per-service resource budget | `security` | **PARTIAL** — see record | `not_verified` |
| `FB2-SAF-SEC-000003` | SEC-000003: Message-level integrity and freshness for safety-relevant CAN messages | `security` | **NO — absent** | `not_verified` |
| `FB2-SAF-SEC-000004` | SEC-000004: Framing, integrity and authorisation on the serial link, and demotion of the X... | `security` | **NO — absent** | `not_verified` |
| `FB2-SAF-SEC-000005` | SEC-000005: Cryptographically strong entropy for network security parameters, and governed... | `security` | **PARTIAL** — see record | `not_verified` |

The *control present* column is read from the machine-readable `real_source_control_status` field of each record, not inferred from prose. `absent` means the record establishes by reading the pinned source that the control is not there. `partially_present` means part of the capability is there and part is not, and the record's `real_source_presence` field gives the itemised split.

Every requirement above carries `human_approval_status: pending`, `production_authorized: false` and `product_verification_credit: false`. No requirement has verification evidence in this corpus, and none has been approved. The related third-party component inventory is `docs/artifacts/sources/sbom.json`; it deliberately records **no** vulnerability status for any component, because no advisory source was consulted. Absence of an advisory there means the question was not asked, not that the answer is negative.


---

*Generated: 2026-10-01T05:09:49Z — auto-generated from the machine-verifiable corpus. Regenerate with `python3 docs/artifacts/tools/render_spec_documents.py`.*
