# foxBMS 2 — System Verification Report

**Document Control**

| Field | Value |
|---|---|
| Project | foxBMS 2 — Battery Management System |
| Document | System Verification Report |
| Baseline | BAS-REF-001 (commit `308028fb`, tag `v1.11.0`) |
| Profiles | `as_is` (source-grounded) + `synthetic_reference` (hypothetical) |
| Corpus status | `synthetic_ready_with_limitations` |
| Generated | 2026-10-01T19:25:12Z |

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

#### `FB2-VER-TMS-000012` — Validation: charging a healthy pack at the limit does not cause a spurious safety reaction (stakeholder intent: pack manufacturer) (synthetic_reference)

- **Test type**: `validation` | **Oracle basis**: `synthetic_assumption`
- **Objective**: Confirm that a pack operated correctly at its published charge limit produces no spurious safe-state reaction over a full charge, because the pack manufacturer's stated need is that the item does not reduce usable capacity through false reactions. This is a false-reaction validation: it does not tes...
- **Preconditions**: The item is fitted to the declared pack configuration and its configuration data matches the pack's ..., The cell voltages, temperatures and the pack current are logged at a rate that resolves 100 ms., The charger respects the charge limits the item publishes (FB2-ASM-003).
- **Environment**: Fictional 400 V pack on a lab charging rig with a synchronised logger; Item firmware and the vehicle control unit build under test; config `VAR-REF-001 reference configuration, nominal cells`
- **Test cases (steps)**:
  1. **Run a full charge cycle from the declared minimum state to full** → expected: No FAULT mode entry and no contactor opening attributable to a false reaction
  2. **Record every diagnosis entry raised during the cycle** → expected: Zero entries whose severity would have forced the safe state
  3. **Compare the delivered capacity against the pack's declared capacity** → expected: At least 98% of declared usable capacity
  4. **Repeat at the two ambient temperature extremes** → expected: Same outcome; no reaction count that rises with temperature
- **Expected outcomes**:
  - `fault_reaction_count` = 0 (tolerance exact)
  - `delivered_capacity_fraction` = 98 (tolerance at least)
  - `diagnosis_entries_forcing_safe_state` = 0 (tolerance exact)

#### `FB2-VER-TMS-000013` — Validation: the driver's usable experience after a genuine overvoltage reaction (operational scenario OS-002, traction discharge) (synthetic_reference)

- **Test type**: `validation` | **Oracle basis**: `synthetic_assumption`
- **Objective**: Confirm that when a genuine overvoltage reaction occurs while the vehicle is being driven, the outcome is the one the end-user driver stakeholder needs: the pack is isolated, the vehicle coasts to a stop under its own control, and the driver is told what happened in terms that do not require a diagn...
- **Preconditions**: The pack, vehicle and charger are real (hypothetical) installations, not a bench., A driver representative from the declared end-user class is available and has not been briefed on wh..., A logging setup captures the driver-facing indication, not only the internal state.
- **Environment**: Fictional 400 V pack in a fictional vehicle on a closed test route; Item firmware and the vehicle control unit build under test; config `VAR-REF-001 reference configuration, nominal cells`
- **Test cases (steps)**:
  1. **Drive the vehicle at speed until the cell overvoltage occurs** → expected: The item reaches the safe state within the fault-tolerant time interval
  2. **Observe the vehicle's behaviour after the contactors open** → expected: The vehicle coasts and stops without loss of steering or of brake assist
  3. **Capture what the driver is shown** → expected: An unambiguous statement that the battery has been isolated for a battery fault, not a generic warning light
  4. **Confirm with the driver stakeholder class whether the indication is actionable** → expected: The driver states what happened and what to do without reference to a service manual
- **Expected outcomes**:
  - `contactor_open_time` = 100 (tolerance at most)
  - `steering_and_brake_assist_retained` = true (tolerance exact)
  - `driver_indication_states_the_cause` = true (tolerance exact)

#### `FB2-VER-TMS-000014` — Validation: degraded operation remains usable and is announced before it becomes a hard stop (operational scenario: single-channel measurement degradation) (synthetic_reference)

- **Test type**: `validation` | **Oracle basis**: `analytical_model`
- **Objective**: Confirm that a measurement-path degradation moves the item into its degraded mode with a capability the pack manufacturer can still use, and that the reduction is announced before the condition becomes a hard stop. The failure this guards against is specific: a degraded mode that silently removes ca...
- **Preconditions**: The pack is at a nominal mid-discharge state with the vehicle stationary., A channel degradation can be injected without disturbing the cells themselves., The vehicle control unit is logging the item's published state.
- **Environment**: Fictional pack on a bench with an injectable measurement-channel fault injector; Item firmware and the vehicle control unit build under test; config `VAR-REF-001 reference configuration, nominal cells`
- **Test cases (steps)**:
  1. **Degrade one channel and observe the item** → expected: The item enters degraded mode rather than FAULT
  2. **Record what capability is retained and what is removed** → expected: Contactor control retained, charge and discharge limited, monitoring rate increased
  3. **Confirm the reduction is published to the vehicle control unit** → expected: A degraded-state indication is present within one publication period
  4. **Increase the degradation to the point of no usable reference** → expected: The item escalates to the safe state rather than continuing on an unusable channel
  5. **Confirm with the service stakeholder class that the degradation is diagnosable** → expected: The service class can identify which channel degraded from the item's own output
- **Expected outcomes**:
  - `mode_on_first_degradation` = DEGRADED (tolerance exact)
  - `contactor_control_retained` = true (tolerance exact)
  - `degraded_indication_latency` = 100 (tolerance at most)

#### `FB2-VER-TMS-000015` — Validation: the service technician can commission and service the item without being able to energise it incorrectly (operational scenario OS-006, workshop service) (synthetic_reference)

- **Test type**: `validation` | **Oracle basis**: `synthetic_assumption`
- **Objective**: Confirm that a service technician following the documented commissioning and service procedure cannot bring the item into a state in which the contactors are commanded closed with open-circuit sensor inputs, and that the procedure's steps are executable in the order given. The stakeholder need is th...
- **Preconditions**: The item is unpowered or on a low-voltage service supply with the contactor drivers inhibited., The service procedure under test exists as an approved document; in this corpus it does not, and thi..., Sense leads may be connected or left open without damaging anything, which is an assumption this cor...
- **Environment**: Fictional item on a service bench with a service diagnostic tool; Item firmware and the vehicle control unit build under test; config `VAR-REF-001 reference configuration, nominal cells`
- **Test cases (steps)**:
  1. **Execute the commissioning procedure exactly as written** → expected: Every step is executable in the order given without an undocumented intermediate state
  2. **With sense leads unconnected, assert commissioning and attempt to command the contactors closed** → expected: The command is refused and the refusal is diagnosed
  3. **Connect only a subset of the sense leads and repeat** → expected: The open-circuit condition is diagnosed rather than interpreted as cells at zero volts
  4. **Release commissioning and remove the tool** → expected: The item returns to a state in which no contactor actuation is possible without a current-flow request
  5. **Have a technician from the declared class perform the procedure unassisted** → expected: The technician completes it without improvising a step
- **Expected outcomes**:
  - `contactor_close_command_without_sense_leads` = 0 (tolerance exact)
  - `open_circuit_diagnosed` = true (tolerance exact)
  - `technician_improvised_steps` = 0 (tolerance exact)

#### `FB2-VER-TMS-000016` — Verification: an unauthenticated peer is refused service, and an authenticated session's payload is neither readable nor alterable by a passive or active segment observer (synthetic_reference)

- **Test type**: `robustness` | **Oracle basis**: `source_grounded`
- **Objective**: Confirm that the master software completes no externally reachable network session with a peer that has not authenticated, and that after authentication the session's application payload is neither recoverable in plaintext by an observer on the segment nor modifiable by one. Also confirm that each r...
- **Preconditions**: The service is externally reachable in the configuration under test, which is the hypothetical proje..., The item is otherwise in a nominal mode with no active fault., A capture point exists on the segment.
- **Environment**: Hypothetical 400 V pack on a bench with an instrumented network segment; BMS master firmware under test; config `VAR-REF-001 with the commissioning service enabled and all debug endpoints closed`
- **Test cases (steps)**:
  1. **Offer 1000 connections from peers that fail authentication** → expected: Zero sessions reach the application data state
  2. **Authenticate successfully and capture the segment for 24 h** → expected: No application payload byte is recoverable in plaintext
  3. **Alter bytes of an authenticated session's payload** → expected: The receiver rejects every altered frame and raises a diagnosis entry
  4. **Replay a previously valid credential** → expected: The replay is refused and diagnosed
  5. **Review the diagnosis log against the injection schedule** → expected: One diagnosis entry per refused attempt, no missing and no extra
- **Expected outcomes**:
  - `unauthenticated_sessions` = 0 (tolerance exact)
  - `plaintext_payload_bytes_recovered` = 0 (tolerance exact)
  - `altered_frames_accepted` = 0 (tolerance exact)
  - `authentication_latency` = 100 (tolerance at most)
  - `diagnosis_entries_per_refusal` = 1 (tolerance exact)

#### `FB2-VER-TMS-000017` — Verification: a peer holding the maximum permitted connections open and silent does not deny service to legitimate peers (synthetic_reference)

- **Test type**: `robustness` | **Oracle basis**: `analytical_model`
- **Objective**: Confirm that a hostile peer cannot make the service unavailable to a legitimate peer by opening the maximum number of permitted connections and sending nothing on them, and that every refusal and every budget breach is diagnosable. This is the measure for the requirement's availability clause; the r...
- **Preconditions**: The service under test implements the caps the requirement states., The hostile peer can hold sockets open without sending data., The legitimate peer behaves as a legitimate peer.
- **Environment**: Hypothetical 400 V pack on a bench with a routable network segment; BMS master firmware under test; config `VAR-REF-001 with the commissioning service enabled`
- **Test cases (steps)**:
  1. **Open the permitted maximum of silent connections and hold them** → expected: The service accepts exactly the cap and refuses the next attempt
  2. **Attempt a legitimate connection while the cap is held** → expected: The legitimate peer is served, or refused within a bounded time and diagnosed
  3. **Burst 128 KiB on one held connection** → expected: The connection is closed within 100 ms of the breach and its resources are released
  4. **Hold the cap open for 30 minutes** → expected: No service task is blocked indefinitely; the receive timeout fires within 2000 ms
  5. **Run for 1 hour with the hostile peer active** → expected: At least 1 legitimate connection served per hour
  6. **Review the diagnosis log** → expected: One entry per refusal and per detected breach
- **Expected outcomes**:
  - `concurrent_connections_serviced` = 4 (tolerance at most)
  - `receive_timeout` = 2000 (tolerance at most)
  - `per_connection_byte_budget` = 65536 (tolerance at most)
  - `breach_to_close_time` = 100 (tolerance at most)
  - `legitimate_connections_per_hour_under_exhaustion` = 1 (tolerance at least)

#### `FB2-VER-TMS-000018` — Verification: a bus peer without the shared secret cannot present a frame the dispatch layer accepts (synthetic_reference)

- **Test type**: `robustness` | **Oracle basis**: `source_grounded`
- **Objective**: Confirm that for every CAN identifier whose payload influences a safety function, a frame carrying a valid identifier but no valid counter, no valid integrity value or the wrong data-length code is rejected before the receive callback is invoked, and that a genuine frame with a sequence error is rej...
- **Preconditions**: The bus under test carries the item's normal traffic., The shared secret is held only by the genuine peer and by the item., The identifiers whose payloads influence a safety function are enumerated.
- **Environment**: Hypothetical 400 V pack on a bus bench with a second node able to transmit arbitrary frames; BMS master firmware under test; config `VAR-REF-001 with the safety-relevant identifiers configured and the integrity check enabled`
- **Test cases (steps)**:
  1. **Inject 5000 frames with a valid identifier and no valid integrity value** → expected: Zero reach the receive callback; each is diagnosed as an integrity failure
  2. **Replay 500 recorded valid frames out of sequence** → expected: Zero reach the receive callback; each is diagnosed as a counter failure
  3. **Inject 1440 short frames** → expected: Zero reach the receive callback; each is diagnosed as a length failure
  4. **Run genuine traffic for 24 h alongside the injections** → expected: Zero genuine frames rejected over an observed genuine-frame population of at least 3 x 10^6 frames, giving a one-sided 95 percent upper confidence bou...
  5. **Review the diagnosis log** → expected: One entry per rejected frame, and the three failure kinds are distinguishable
- **Expected outcomes**:
  - `injected_frames_accepted` = 0 (tolerance exact)
  - `replayed_frames_accepted` = 0 (tolerance exact)
  - `short_frames_accepted` = 0 (tolerance exact)
  - `verification_latency` = 2 (tolerance at most)
  - `genuine_frames_observed` = 3e6 (tolerance at least)
  - `genuine_frames_rejected` = 0 (tolerance exact, over a genuine-frame population of at least 3e6, i.e. a one-sided 95 percent upper bound of 1 per 10^6 genuine frames)
  - `integrity_value_width` = 22 (tolerance at least)

#### `FB2-VER-TMS-000019` — Verification: the serial link acts only on authenticated frames, and the XOFF/XON byte values are demoted to ordinary payload (synthetic_reference)

- **Test type**: `robustness` | **Oracle basis**: `source_grounded`
- **Objective**: Confirm that no byte on the serial receive line reaches the application layer without passing a length check and an integrity check, that a structurally valid frame with a modified payload is rejected, that neither 0x13 nor 0x11 can change the transmit-enabled state outside an authenticated frame, a...
- **Preconditions**: The serial link under test is the link the item uses for its external service interface., The item is otherwise nominal and no genuine peer is mid-transfer., The receive queue depth is configured and known.
- **Environment**: Hypothetical 400 V pack on a bench with an instrumented serial port; BMS master firmware under test; config `VAR-REF-001 with the service interface enabled and no genuine peer connected`
- **Test cases (steps)**:
  1. **Send 100000 unframed bytes including both control-byte values** → expected: Zero bytes reach the application layer; zero transmit-enabled transitions occur
  2. **Send 86400 valid-structure frames with a modified payload** → expected: Zero are accepted; each raises a diagnosis entry
  3. **Send 1440 frames with a declared length that does not match the byte count** → expected: Zero are passed onward; each is diagnosed
  4. **Overflow the receive queue deliberately** → expected: The overflow is detected and one diagnosis entry is raised per event
  5. **Run genuine traffic for 24 h alongside the injections** → expected: Zero genuine frames rejected over an observed genuine-frame population of at least 3 x 10^6 frames, giving a one-sided 95 percent upper confidence bou...
- **Expected outcomes**:
  - `unframed_bytes_passing` = 0 (tolerance exact)
  - `transmit_state_transitions_from_control_bytes` = 0 (tolerance exact)
  - `modified_payload_frames_accepted` = 0 (tolerance exact)
  - `length_mismatch_frames_passed` = 0 (tolerance exact)
  - `diagnosis_entries_per_overflow` = 1 (tolerance exact)
  - `genuine_frames_observed` = 3e6 (tolerance at least)
  - `genuine_frames_rejected` = 0 (tolerance exact, over a genuine-frame population of at least 3e6, i.e. a one-sided 95 percent upper bound of 1 per 10^6 genuine frames)
  - `integrity_value_width` = 22 (tolerance at least)

#### `FB2-VER-TMS-000020` — Verification: the initial sequence number is unpredictable across connections and power cycles, and the third-party component inventory is evidenced and checked against an advisory source on a stated ... (synthetic_reference)

- **Test type**: `robustness` | **Oracle basis**: `synthetic_assumption`
- **Objective**: Two clauses with two different oracles, stated separately rather than blended. First: confirm that the initial TCP sequence number takes a distinct value on every one of 1000 connection establishments and that the entropy seed is distinct across 1000 power cycles. Second: confirm that every entry in...
- **Preconditions**: The item's network stack is reachable and the source can be inspected for the seed's origin., A power-cycle fixture exists that records the seed at each boot., The component inventory exists as a maintained document with an owner., An authoritative advisory source exists and the project is permitted to consult it. This last precon...
- **Environment**: Hypothetical 400 V pack on a bench, plus a workstation for the inventory review; BMS master firmware under test; config `VAR-REF-001`
- **Test cases (steps)**:
  1. **Establish 1000 connections and record each initial sequence number** → expected: 1000 distinct values, no repetition within the set
  2. **Power cycle 1000 times and record each entropy seed** → expected: 1000 distinct seeds
  3. **Compare the source of each seed against the pinned build** → expected: No seed is fixed at build time and every seed derives from a running source
  4. **Review every inventory entry's version evidence** → expected: Every entry is evidenced by a named source or explicitly null with a stated reason
  5. **Review the advisory check records** → expected: The most recent check is within 30 days and every match has an adjudication
  6. **Search the inventory for inferred or guessed versions** → expected: Zero entries
- **Expected outcomes**:
  - `distinct_initial_sequence_numbers` = 1000 (tolerance exact)
  - `distinct_seeds_across_power_cycles` = 1000 (tolerance exact)
  - `build_time_fixed_seeds` = 0 (tolerance exact)
  - `inventory_entries_with_version_evidence_or_explicit_null` = 100 (tolerance at least)
  - `days_since_last_advisory_check` = 30 (tolerance at most)
  - `matches_without_adjudication` = 0 (tolerance exact)
  - `entries_with_guessed_version` = 0 (tolerance exact)

#### `FB2-VER-TMS-000021` — Test: every transferred cell-voltage value is integrity-checked before any decision consumes it, and every published value carries a usable age (synthetic_reference)

- **Test type**: `integration` | **Oracle basis**: `source_grounded`
- **Objective**: Confirm two of FB2-SYS-SYR-000001's four acceptance criteria against the pinned source's own mechanism: that the integrity of every transferred value is decided before any decision uses it, and that each published value carries an age that can be read. The integrity criterion is judged against LTC_C...
- **Preconditions**: The reference project's AFE driver is initialised and a measurement cycle has completed at least onc..., The database is initialised so that a write stamps the block header., The AFE plausibility entry is available for the range check.
- **Environment**: POSIX host (Linux) running the unit-test build, with the AFE driver and the database linked and the SPI interface stubbed; foxBMS 2 application firmware built with the unit-test configuration; config `conf/unit/app_project_posix.yml with FOXBMS_AFE_DRIVER_LTC=1u, which is the configuration the repository's own unit-test build selects`
- **Test cases (steps)**:
  1. **Run 100 measurement cycles with uncorrupted frames and record the PEC validity flag and the header timestamp for each published block.** → expected: Every cycle reports PEC valid and every published block carries a non-zero header timestamp.
  2. **Run 100 measurement cycles in which exactly one LTC's PEC is corrupted, and record the PEC validity flag, the per-cell invalid flag and the value a su...** → expected: The corrupted LTC's PEC validity flag is false, its per-cell invalid flag is true, and no decision reads a value for that cell that is not marked inva...
  3. **Suppress the database write for one cycle and read the header timestamp again.** → expected: The header timestamp does not advance for the suppressed cycle, so the age of the last published value is observable rather than inferred.
  4. **Compare the age implied by the header timestamp against the number of measurement cycles elapsed.** → expected: The age increases monotonically and by one acquisition period per elapsed cycle.
- **Expected outcomes**:
  - `cycles_with_integrity_decided_before_use` = 100 (tolerance exact)
  - `corrupted_frames_consumed_unchallenged` = 0 (tolerance exact)
  - `published_blocks_with_readable_age` = 100 (tolerance exact)
  - `age_monotonic_across_cycles` = true (tolerance exact)

#### `FB2-VER-TMS-000022` — Test: the configured measurement period yields at least the acquisition rate FB2-SYS-SYR-000001 requires, computed rather than measured (synthetic_reference)

- **Test type**: `qualification` | **Oracle basis**: `analytical_model`
- **Objective**: Compute whether the reference project's configured measurement period meets the acquisition-rate criterion of FB2-SYS-SYR-000001, and record the arithmetic rather than an observation. The criterion is at least 20 acquisitions per second in every monitoring mode; the parameter registry records the ac...
- **Preconditions**: The parameter registry entry for the acquisition period is the authoritative configured value for th..., The measurement is a computation over that value, not a run.
- **Environment**: no hardware; the measure is a computation over the parameter registry and the source's task configuration; not applicable - no software is executed; config `BAS-REF-001 parameter registry plus the application task configuration in the pinned source`
- **Test cases (steps)**:
  1. **Read the configured acquisition period from the parameter registry.** → expected: A single period value is obtained, in milliseconds.
  2. **Read the configured task cycle time for the task that triggers the measurement from the pinned source.** → expected: A single task cycle value is obtained, in milliseconds.
  3. **Compute the acquisitions per second implied by each value as 1000 divided by the period.** → expected: Two rates are produced and compared with each other.
  4. **Compare the smaller rate against the requirement's threshold and record the margin.** → expected: The comparison and the margin are recorded, including that the margin is zero at the registry value.
  5. **Compute the longest period that would still satisfy the criterion.** → expected: A single boundary period is recorded, being the period at which the rate equals exactly the threshold.
- **Expected outcomes**:
  - `acquisitions_per_second_at_registry_period` = 20 (tolerance at least)
  - `margin_above_requirement` = 0 (tolerance at least)
  - `longest_period_still_meeting_criterion` = 50 (tolerance at most)

#### `FB2-VER-TMS-000023` — Test: an excursion into each safe-operating-area tier produces the graded reaction the pinned source actually configures, and only the safety-limit tier reaches the fault reaction (synthetic_reference)

- **Test type**: `integration` | **Oracle basis**: `source_grounded`
- **Objective**: Establish, against the pinned source rather than against the item's output, which of FB2-SYS-SYR-000002's reactions the code can produce. SOA_CheckVoltages compares each string's extremes against three nested tiers per direction - operating, recommended safety and maximum safety - and raises a diagn...
- **Preconditions**: The reference project's limit configuration is loaded from the parameter registry., The diagnosis configuration table is the one in the pinned source, which is what determines the grad...
- **Environment**: POSIX host (Linux) running the unit-test build, with the SOA module linked and the diagnosis handler stubbed to record every entry raised; foxBMS 2 application firmware built with the unit-test configuration; config `conf/unit/app_project_posix.yml`
- **Test cases (steps)**:
  1. **Read the configuration table and record the severity and delay configured for each of the three over-voltage diagnosis entries.** → expected: Three entries are recorded with distinct severities and distinct delay settings.
  2. **Inject a maximum cell voltage just above the operating-limit threshold and record every diagnosis entry raised.** → expected: Exactly one entry is raised, and it is the operating-limit one.
  3. **Inject a maximum cell voltage between the recommended-safety and maximum-safety thresholds.** → expected: Two entries are raised, and the maximum-safety entry is not among them.
  4. **Inject a maximum cell voltage above the maximum-safety threshold.** → expected: Three entries are raised, including the maximum-safety one, which is the entry configured as a fatal error.
  5. **Return the voltage below the operating-limit threshold and record the entries again.** → expected: The entries are cleared with the clear event rather than left latched.
- **Expected outcomes**:
  - `entries_raised_at_operating_limit` = 1 (tolerance exact)
  - `entries_raised_below_maximum_safety` = 2 (tolerance exact)
  - `entries_raised_at_maximum_safety` = 3 (tolerance exact)
  - `tiers_configured_as_fatal_error` = 1 (tolerance exact)

#### `FB2-VER-TMS-000024` — Test: the debounce and the degraded-to-fault boundary FB2-SYS-SYR-000002 demands, against an explicitly labelled synthetic assumption (synthetic_reference)

- **Test type**: `unit` | **Oracle basis**: `synthetic_assumption`
- **Objective**: Verify the two parts of FB2-SYS-SYR-000002 that have no counterpart in the pinned source and can therefore only be judged against a stated assumption: that a classification requires two consecutive violations within 100 ms, and that a numerical or named rule separates the degraded reaction from the ...
- **Preconditions**: The assumption about the reference project's debounce behaviour is stated in this record and is not ..., The degraded-to-fault boundary is stated as a value to be declared, not as a value that exists.
- **Environment**: no hardware and no software execution; the measure is a specification review of a requirement against an absence in the source; not applicable - nothing is executed; config `BAS-REF-001 parameter registry and the pinned source's SOA module and diagnosis configuration`
- **Test cases (steps)**:
  1. **Search the pinned SOA module for any counter, debounce or consecutive-violation state.** → expected: No such state is found, which is recorded as the condition the measure exists to make visible.
  2. **Read the diagnosis configuration's occurrence threshold and delay for the maximum-safety over-voltage entry and compare them with the requirement's tw...** → expected: The two mechanisms are recorded side by side and shown not to be the same: different layer, different granularity, different parameters.
  3. **State, against the assumption this record declares, the classification outcome for a sequence of one violation, of two violations inside the window, a...** → expected: Three outcomes are stated, and the second one depends entirely on the assumption rather than on the source.
  4. **State what the degraded-to-fault boundary must be before this criterion can be verified at all.** → expected: A single declared value or named rule is required, and its absence is recorded as the reason the criterion is unverifiable rather than as a pass.
- **Expected outcomes**:
  - `soa_debounce_state_found_in_source` = 0 (tolerance exact)
  - `consecutive_violations_required_by_requirement` = 2 (tolerance exact)
  - `verdict_depends_on_declared_assumption_classification_outcome_is_assumption_dependent` = true (tolerance exact)
  - `degraded_to_fault_boundary_declared_declared_boundary_value` = not_declared (tolerance exact)

#### `FB2-VER-TMS-000025` — Test: the end-to-end fault-reaction budget FB2-SYS-SYR-000003 allocates, computed from the waits the pinned source actually configures (synthetic_reference)

- **Test type**: `qualification` | **Oracle basis**: `analytical_model`
- **Objective**: Compute whether the reaction chain the pinned source implements can close inside the interval FB2-SYS-SYR-000003 allocates, and record the arithmetic. The oracle is the sum of the configured waits the source actually applies between the stages of opening, taken from the application configuration at ...
- **Preconditions**: The application configuration's waits are the ones the pinned source applies., The parameter registry's contactor-mechanical figure is the reference project's declared figure for ...
- **Environment**: no hardware; the measure is a computation over the pinned source's configuration and the parameter registry; not applicable - nothing is executed; config `BAS-REF-001 parameter registry plus src/app/application/config/bms_cfg.h at the pinned commit`
- **Test cases (steps)**:
  1. **Read the configured waits and the task cycle time from the application configuration at the pinned commit.** → expected: Five values are obtained.
  2. **Compute the earliest time at which a contactor can be confirmed open, given that the waits are counted in whole task cycles.** → expected: A lower bound is obtained and it is greater than the allocated interval.
  3. **Add the reference project's declared contactor-mechanical figure to that lower bound.** → expected: A total reaction time is obtained.
  4. **Compare the total against the interval the requirement allocates and against the fault-tolerant time interval in the parameter registry.** → expected: The comparison is recorded, and the over-run is recorded as a number rather than as a verdict.
  5. **Compute the largest mechanical opening time that would still fit inside the allocated interval.** → expected: A single boundary figure is recorded.
- **Expected outcomes**:
  - `earliest_confirmed_open_lower_bound_ms` = at least the wait after opening a precharge contactor (tolerance at least)
  - `reaction_time_exceeds_allocated_interval_end_to_end_reaction_ms` = greater than the allocated interval (tolerance outside)
  - `largest_mechanical_time_still_fitting_max_mechanical_time_ms` = recorded (tolerance exact)

#### `FB2-VER-TMS-000026` — Test: the limit applied, and the reaction reached, depend on the mode or direction in which the condition occurs (synthetic_reference)

- **Test type**: `integration` | **Oracle basis**: `source_grounded`
- **Objective**: Confirm that FB2-SYS-SYR-000004's core claim is falsifiable against the pinned source: that the limit applied and the reaction reached are selected by the mode or direction rather than fixed. Two independent mechanisms in the source select on mode or direction. SOA_CheckTemperatures chooses between ...
- **Preconditions**: The reference project's limit configuration is loaded., The application's state machine is initialised in the uninitialised state.
- **Environment**: POSIX host (Linux) running the unit-test build, with the SOA module and the application's state machine linked and the diagnosis handler stubbed to record entries; foxBMS 2 application firmware built with the unit-test configuration; config `conf/unit/app_project_posix.yml`
- **Test cases (steps)**:
  1. **Inject the chosen cell temperature with a positive string current and record the entries raised.** → expected: The entries raised are the charge-direction temperature entries.
  2. **Inject the identical temperature with a negative string current.** → expected: The entries raised are the discharge-direction temperature entries, which differ from step 1 for at least one tier.
  3. **Issue an initialisation request in the uninitialised state and record the returned result.** → expected: The request is accepted.
  4. **Issue the identical request after initialisation and record the returned result.** → expected: The request is refused with a reason specific to the state it was issued in.
  5. **Record which state the refusal reason came from.** → expected: The refusal is attributable to the state rather than to a fixed policy.
- **Expected outcomes**:
  - `distinct_reaction_sets_by_direction` = true (tolerance exact)
  - `initialisation_accepted_in_uninitialised_state` = true (tolerance exact)
  - `initialisation_refused_after_initialisation` = true (tolerance exact)
  - `refusal_reason_attributable_to_state` = true (tolerance exact)

#### `FB2-VER-TMS-000027` — Test: the second-barrier voltage monitor FB2-SYS-SYR-000005 requires is separable from the main chain in every one of the four declared ways (synthetic_reference)

- **Test type**: `qualification` | **Oracle basis**: `synthetic_assumption`
- **Objective**: Verify FB2-SYS-SYR-000005's four independence criteria - zero processing resources, zero shared supply rails, zero shared communication paths and a stated threshold accuracy - against an explicitly labelled synthetic assumption, because the element the requirement describes does not exist in either ...
- **Preconditions**: The assumption that the second barrier is implementable with a separate divider, comparator and refe..., No hardware design package for the barrier exists in this corpus.
- **Environment**: no hardware: the element does not exist in either profile, so there is nothing to inspect and nothing to run; not applicable - nothing is executed; config `the declared assumption only; there is no configuration to apply`
- **Test cases (steps)**:
  1. **Enumerate what FB2-SYS-SYR-000005 requires the barrier to be independent of, quoting its own acceptance criteria.** → expected: Four independence requirements are enumerated: processing, supply, communication and threshold accuracy.
  2. **For each, state the evidence a verification would need and whether this corpus holds any.** → expected: Four evidence statements are produced, and each records that the corpus holds none.
  3. **Record the accuracy figure the requirement allocates and state that no measurement of any divider or comparator exists in this corpus.** → expected: A single figure is recorded as a declared allocation with no supporting measurement.
  4. **Record what would have to exist before this requirement could be verified rather than merely stated.** → expected: A list of concrete missing artefacts is produced.
- **Expected outcomes**:
  - `independence_requirements_enumerated` = 4 (tolerance exact)
  - `independence_requirements_with_evidence_in_corpus` = 0 (tolerance exact)
  - `accuracy_allocation_measured_threshold_accuracy_mV_measured` = not_measured (tolerance exact)

#### `FB2-VER-TMS-000028` — Test: a current or temperature measurement whose trust cannot be established is marked invalid before any supervisory comparison consumes it (synthetic_reference)

- **Test type**: `integration` | **Oracle basis**: `source_grounded`
- **Objective**: Confirm FB2-SYS-SYR-000006's validity-marking and envelope-check criteria against the pinned source. Two independent gates are available. On the acquisition side, the current-sensor receive callback sets the per-string invalidMeasurement flag on every channel error it handles and clears it on reset,...
- **Preconditions**: The current-sensor receive callback is linked so that channel-error handling can be driven., The SOA module is linked with the database write path so that the invalid flags it reads are the one...
- **Environment**: POSIX host (Linux) running the unit-test build, with the current-sensor receive callback and the SOA module linked; foxBMS 2 application firmware built with the unit-test configuration; config `conf/unit/app_project_posix.yml`
- **Test cases (steps)**:
  1. **Drive a channel-error indication for a monitored current channel and read that string's invalidMeasurement flag.** → expected: The flag is set, and it is set by the receive callback rather than by the consumer.
  2. **Drive the reset of that channel error and read the flag again.** → expected: The flag is cleared.
  3. **With the flag set, present a string current above the applicable charge-direction limit and record the entries raised.** → expected: No current-limit entry is raised for that string, and no entry at all is raised from the skipped branch.
  4. **Clear the flag, present the identical current again and record the entries.** → expected: The charge-direction current-limit entry is raised, which shows the skip in step 3 was caused by the flag and not by the value.
  5. **Present a temperature above the applicable tier in each current direction and record the entries.** → expected: The entries raised are the tier entries for the direction in force, not for both directions.
- **Expected outcomes**:
  - `invalid_flag_set_at_acquisition_boundary` = true (tolerance exact)
  - `limit_entries_raised_while_invalid` = 0 (tolerance exact)
  - `limit_entries_raised_after_validity_restored` = at least 1 (tolerance at least)
  - `temperature_tiers_selected_by_direction` = true (tolerance exact)

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
- `FB2-VER-TMS-000012` (synthetic_reference): 4 test case(s)
- `FB2-VER-TMS-000013` (synthetic_reference): 4 test case(s)
- `FB2-VER-TMS-000014` (synthetic_reference): 5 test case(s)
- `FB2-VER-TMS-000015` (synthetic_reference): 5 test case(s)
- `FB2-VER-TMS-000016` (synthetic_reference): 5 test case(s)
- `FB2-VER-TMS-000017` (synthetic_reference): 6 test case(s)
- `FB2-VER-TMS-000018` (synthetic_reference): 5 test case(s)
- `FB2-VER-TMS-000019` (synthetic_reference): 5 test case(s)
- `FB2-VER-TMS-000020` (synthetic_reference): 6 test case(s)
- `FB2-VER-TMS-000021` (synthetic_reference): 4 test case(s)
- `FB2-VER-TMS-000022` (synthetic_reference): 5 test case(s)
- `FB2-VER-TMS-000023` (synthetic_reference): 5 test case(s)
- `FB2-VER-TMS-000024` (synthetic_reference): 4 test case(s)
- `FB2-VER-TMS-000025` (synthetic_reference): 5 test case(s)
- `FB2-VER-TMS-000026` (synthetic_reference): 5 test case(s)
- `FB2-VER-TMS-000027` (synthetic_reference): 4 test case(s)
- `FB2-VER-TMS-000028` (synthetic_reference): 5 test case(s)

**Total system-level test cases**: 131

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
- **Evidence refs**: `src/app/engine/database/database.h`, `tests/unit/app/application/algorithm/moving_average/test_moving_average.c`

##### Execution `FB2-VER-EXE-000009` — Execution: SOC lookup-table state estimation (tests/unit/app/application/algorithm/state_estimation/soc/lookup-table/test_soc_lookup-table.c) - real macOS host run, FAILING

- **Test measure**: `FB2-VER-TMS-000003` | **Execution kind**: `actual_host_run` | **Outcome**: **FAIL**
- **Environment**: arm64-apple-darwin27 (Apple Silicon Mac, Darwin 27.0.0); ruby 4.0.7 (2026-09-15 revision 229531a6cf) +PRISM [arm64-darwin27]; tools: ceedling 1.1.9-2209dc2, cexception 1.3.5, clang 17.0.0, cmock 2.7.2, gcc 17.0.0, ruby 4.0.7, unity 2.7.2
- **Evidence refs**: `src/app/engine/database/database.h`, `tests/unit/app/application/algorithm/state_estimation/soc/lookup-table/test_soc_lookup-table.c`

##### Execution `FB2-VER-EXE-000010` — Execution: State estimation initialisation (tests/unit/app/application/algorithm/state_estimation/test_state_estimation.c) - real macOS host run, FAILING

- **Test measure**: `FB2-VER-TMS-000003` | **Execution kind**: `actual_host_run` | **Outcome**: **FAIL**
- **Environment**: arm64-apple-darwin27 (Apple Silicon Mac, Darwin 27.0.0); ruby 4.0.7 (2026-09-15 revision 229531a6cf) +PRISM [arm64-darwin27]; tools: ceedling 1.1.9-2209dc2, cexception 1.3.5, clang 17.0.0, cmock 2.7.2, gcc 17.0.0, ruby 4.0.7, unity 2.7.2
- **Evidence refs**: `src/app/engine/database/database.h`, `tests/unit/app/application/algorithm/state_estimation/test_state_estimation.c`

##### Execution `FB2-VER-EXE-000011` — Execution: Debug AFE default driver (tests/unit/app/driver/afe/debug/default/test_debug_default.c) - real macOS host run, FAILING

- **Test measure**: `FB2-VER-TMS-000003` | **Execution kind**: `actual_host_run` | **Outcome**: **FAIL**
- **Environment**: arm64-apple-darwin27 (Apple Silicon Mac, Darwin 27.0.0); ruby 4.0.7 (2026-09-15 revision 229531a6cf) +PRISM [arm64-darwin27]; tools: ceedling 1.1.9-2209dc2, cexception 1.3.5, clang 17.0.0, cmock 2.7.2, gcc 17.0.0, ruby 4.0.7, unity 2.7.2
- **Evidence refs**: `src/app/engine/database/database.h`, `tests/unit/app/driver/afe/debug/default/test_debug_default.c`

##### Execution `FB2-VER-EXE-000012` — Execution: DIAG flag table update (tests/unit/app/engine/config/test_diag_cfg.c) - real macOS host run, FAILING

- **Test measure**: `FB2-VER-TMS-000003` | **Execution kind**: `actual_host_run` | **Outcome**: **PASS**
- **Environment**: arm64-apple-darwin27 (Apple Silicon Mac, Darwin 27.0.0); ruby 4.0.7 (2026-09-15 revision 229531a6cf) +PRISM [arm64-darwin27]; tools: ceedling 1.1.9-2209dc2, cexception 1.3.5, clang 17.0.0, cmock 2.7.2, gcc 17.0.0, ruby 4.0.7, unity 2.7.2
- **Evidence refs**: `src/app/engine/database/database.h`, `tests/unit/app/engine/config/test_diag_cfg.c`

##### Execution `FB2-VER-EXE-000013` — Execution: Redundancy layer (tests/unit/app/application/redundancy/test_redundancy.c) - real macOS host run, FAILING

- **Test measure**: `FB2-VER-TMS-000003` | **Execution kind**: `actual_host_run` | **Outcome**: **FAIL**
- **Environment**: arm64-apple-darwin27 (Apple Silicon Mac, Darwin 27.0.0); ruby 4.0.7 (2026-09-15 revision 229531a6cf) +PRISM [arm64-darwin27]; tools: ceedling 1.1.9-2209dc2, cexception 1.3.5, clang 17.0.0, cmock 2.7.2, gcc 17.0.0, ruby 4.0.7, unity 2.7.2
- **Evidence refs**: `src/app/engine/database/database.h`, `tests/unit/app/application/redundancy/test_redundancy.c`

##### Execution `FB2-VER-EXE-000014` — Execution: DIAG engine (tests/unit/app/engine/diag/test_diag.c) - real macOS host run, FAILING

- **Test measure**: `FB2-VER-TMS-000003` | **Execution kind**: `actual_host_run` | **Outcome**: **FAIL**
- **Environment**: arm64-apple-darwin27 (Apple Silicon Mac, Darwin 27.0.0); ruby 4.0.7 (2026-09-15 revision 229531a6cf) +PRISM [arm64-darwin27]; tools: ceedling 1.1.9-2209dc2, cexception 1.3.5, clang 17.0.0, cmock 2.7.2, gcc 17.0.0, ruby 4.0.7, unity 2.7.2
- **Evidence refs**: `src/app/engine/database/database.h`, `tests/unit/app/engine/diag/test_diag.c`

##### Execution `FB2-VER-EXE-000015` — Execution: foxBMS 2 SIL host unit-test sweep, all 313 tests (macOS arm64)

- **Test measure**: `FB2-VER-TMS-000001..000005` | **Execution kind**: `actual_host_run` | **Outcome**: **FAIL**
- **Environment**: arm64-apple-darwin27 (Apple Silicon Mac, Darwin 27.0.0); ruby 4.0.7 (2026-09-15 revision 229531a6cf) +PRISM [arm64-darwin27]; tools: ceedling 1.1.9-2209dc2, cexception 1.3.5, clang 17.0.0, cmock 2.7.2, gcc 17.0.0, ruby 4.0.7, unity 2.7.2
- **Evidence refs**: `tests/unit/app/driver/spi/test_spi.c`, `tests/unit/app/driver/mcu/test_mcu.c`, `src/app/driver/spi/spi.c`, `src/app/driver/mcu/mcu.c`, `docs/artifacts/evidence/actual-runs/foxbms2-sil-host-unit-test-macos-2026-09-29/REATTRIBUTION.md`, `docs/artifacts/evidence/actual-runs/foxbms2-sil-host-unit-test-macos-2026-09-29/VACUOUS-TESTS.md`, `docs/artifacts/evidence/actual-runs/foxbms2-sil-host-unit-test-macos-2026-09-29/RELAXED-DIAGNOSTICS.md`, `docs/artifacts/evidence/actual-runs/foxbms2-sil-host-unit-test-macos-2026-09-29/REPORT-BUILD-FAILURES-AND-CLASSIFIER.md`, `docs/artifacts/evidence/actual-runs/foxbms2-sil-host-unit-test-macos-2026-09-29/TASK1-CLASSIFICATION.md`, `docs/artifacts/evidence/actual-runs/foxbms2-sil-host-unit-test-macos-2026-09-29/TASK2-SEGFAULT.md`

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

##### Execution `FB2-VER-EXE-000012` — Execution: FB2-VER-TMS-000012 (blocked - no validation environment)

- **Test measure**: `FB2-VER-TMS-000012` | **Execution kind**: `none` | **Outcome**: **BLOCKED**
- **Environment**: none - no vehicle, pack, charger or bench harness exists in this corpus; not applicable; tools: none 0.0.0
- **Evidence refs**: `FB2-VER-TMS-000012`

##### Execution `FB2-VER-EXE-000013` — Execution: FB2-VER-TMS-000013 (blocked - no validation environment)

- **Test measure**: `FB2-VER-TMS-000013` | **Execution kind**: `none` | **Outcome**: **BLOCKED**
- **Environment**: none - no vehicle, pack, charger or bench harness exists in this corpus; not applicable; tools: none 0.0.0
- **Evidence refs**: `FB2-VER-TMS-000013`

##### Execution `FB2-VER-EXE-000014` — Execution: FB2-VER-TMS-000014 (blocked - no validation environment)

- **Test measure**: `FB2-VER-TMS-000014` | **Execution kind**: `none` | **Outcome**: **BLOCKED**
- **Environment**: none - no vehicle, pack, charger or bench harness exists in this corpus; not applicable; tools: none 0.0.0
- **Evidence refs**: `FB2-VER-TMS-000014`

##### Execution `FB2-VER-EXE-000015` — Execution: FB2-VER-TMS-000015 (blocked - no validation environment)

- **Test measure**: `FB2-VER-TMS-000015` | **Execution kind**: `none` | **Outcome**: **BLOCKED**
- **Environment**: none - no vehicle, pack, charger or bench harness exists in this corpus; not applicable; tools: none 0.0.0
- **Evidence refs**: `FB2-VER-TMS-000015`

##### Execution `FB2-VER-EXE-000016` — Execution: FB2-VER-TMS-000016 (blocked - FB2-SAF-SEC-000001 has no executable security harness in this corpus)

- **Test measure**: `FB2-VER-TMS-000016` | **Execution kind**: `none` | **Outcome**: **BLOCKED**
- **Environment**: none - no target hardware and no instrumented bus in this corpus; not applicable; tools: none 0.0.0
- **Evidence refs**: `FB2-VER-TMS-000016`, `FB2-SAF-SEC-000001`

##### Execution `FB2-VER-EXE-000017` — Execution: FB2-VER-TMS-000017 (blocked - FB2-SAF-SEC-000002 has no executable security harness in this corpus)

- **Test measure**: `FB2-VER-TMS-000017` | **Execution kind**: `none` | **Outcome**: **BLOCKED**
- **Environment**: none - no target hardware and no instrumented bus in this corpus; not applicable; tools: none 0.0.0
- **Evidence refs**: `FB2-VER-TMS-000017`, `FB2-SAF-SEC-000002`

##### Execution `FB2-VER-EXE-000018` — Execution: FB2-VER-TMS-000018 (blocked - FB2-SAF-SEC-000003 has no executable security harness in this corpus)

- **Test measure**: `FB2-VER-TMS-000018` | **Execution kind**: `none` | **Outcome**: **BLOCKED**
- **Environment**: none - no target hardware and no instrumented bus in this corpus; not applicable; tools: none 0.0.0
- **Evidence refs**: `FB2-VER-TMS-000018`, `FB2-SAF-SEC-000003`

##### Execution `FB2-VER-EXE-000019` — Execution: FB2-VER-TMS-000019 (blocked - FB2-SAF-SEC-000004 has no executable security harness in this corpus)

- **Test measure**: `FB2-VER-TMS-000019` | **Execution kind**: `none` | **Outcome**: **BLOCKED**
- **Environment**: none - no target hardware and no instrumented bus in this corpus; not applicable; tools: none 0.0.0
- **Evidence refs**: `FB2-VER-TMS-000019`, `FB2-SAF-SEC-000004`

##### Execution `FB2-VER-EXE-000020` — Execution: FB2-VER-TMS-000020 (blocked - FB2-SAF-SEC-000005 has no executable security harness in this corpus)

- **Test measure**: `FB2-VER-TMS-000020` | **Execution kind**: `none` | **Outcome**: **BLOCKED**
- **Environment**: none - no target hardware and no instrumented bus in this corpus; not applicable; tools: none 0.0.0
- **Evidence refs**: `FB2-VER-TMS-000020`, `FB2-SAF-SEC-000005`

##### Execution `FB2-VER-EXE-000021` — Execution: FB2-VER-TMS-000021 (blocked - the unit-test harness that would drive the AFE driver with an injectable SPI stub is not built in this corpus, and building it would write outside the corpus b...

- **Test measure**: `FB2-VER-TMS-000021` | **Execution kind**: `none` | **Outcome**: **BLOCKED**
- **Environment**: none - no target hardware in this corpus; not applicable - no software was executed; tools: none 0.0.0
- **Evidence refs**: `FB2-VER-TMS-000021`

##### Execution `FB2-VER-EXE-000022` — Execution: FB2-VER-TMS-000022 (blocked - the arithmetic is reproducible but this corpus does not run measures, and no second reader has independently reproduced the figures)

- **Test measure**: `FB2-VER-TMS-000022` | **Execution kind**: `none` | **Outcome**: **BLOCKED**
- **Environment**: none - no target hardware in this corpus; not applicable - no software was executed; tools: none 0.0.0
- **Evidence refs**: `FB2-VER-TMS-000022`

##### Execution `FB2-VER-EXE-000023` — Execution: FB2-VER-TMS-000023 (blocked - the diagnosis configuration table is generated from configuration headers, and reading the generated table is not the same as reading the values the reference ...

- **Test measure**: `FB2-VER-TMS-000023` | **Execution kind**: `none` | **Outcome**: **BLOCKED**
- **Environment**: none - no target hardware in this corpus; not applicable - no software was executed; tools: none 0.0.0
- **Evidence refs**: `FB2-VER-TMS-000023`

##### Execution `FB2-VER-EXE-000024` — Execution: FB2-VER-TMS-000024 (blocked - the oracle is a declared assumption, and confirming a requirement against its own assumption is not an execution this corpus can or should perform)

- **Test measure**: `FB2-VER-TMS-000024` | **Execution kind**: `none` | **Outcome**: **BLOCKED**
- **Environment**: none - no target hardware in this corpus; not applicable - no software was executed; tools: none 0.0.0
- **Evidence refs**: `FB2-VER-TMS-000024`

##### Execution `FB2-VER-EXE-000025` — Execution: FB2-VER-TMS-000025 (blocked - the configuration values the arithmetic needs are read by this authoring pass but no independent recomputation exists, and no timing was measured)

- **Test measure**: `FB2-VER-TMS-000025` | **Execution kind**: `none` | **Outcome**: **BLOCKED**
- **Environment**: none - no target hardware in this corpus; not applicable - no software was executed; tools: none 0.0.0
- **Evidence refs**: `FB2-VER-TMS-000025`

##### Execution `FB2-VER-EXE-000026` — Execution: FB2-VER-TMS-000026 (blocked - no host harness exists here for the application's state machine, and the requirement's publication criterion needs a vehicle control unit that this corpus does...

- **Test measure**: `FB2-VER-TMS-000026` | **Execution kind**: `none` | **Outcome**: **BLOCKED**
- **Environment**: none - no target hardware in this corpus; not applicable - no software was executed; tools: none 0.0.0
- **Evidence refs**: `FB2-VER-TMS-000026`

##### Execution `FB2-VER-EXE-000027` — Execution: FB2-VER-TMS-000027 (blocked - the element the measure is about does not exist in either profile, so there is nothing to inspect and nothing to run)

- **Test measure**: `FB2-VER-TMS-000027` | **Execution kind**: `none` | **Outcome**: **BLOCKED**
- **Environment**: none - no target hardware in this corpus; not applicable - no software was executed; tools: none 0.0.0
- **Evidence refs**: `FB2-VER-TMS-000027`

##### Execution `FB2-VER-EXE-000028` — Execution: FB2-VER-TMS-000028 (blocked - no host harness exists here, and the measure's third criterion needs a consumer census this corpus has not performed)

- **Test measure**: `FB2-VER-TMS-000028` | **Execution kind**: `none` | **Outcome**: **BLOCKED**
- **Environment**: none - no target hardware in this corpus; not applicable - no software was executed; tools: none 0.0.0
- **Evidence refs**: `FB2-VER-TMS-000028`



---

*Generated: 2026-10-01T19:25:12Z — auto-generated from the machine-verifiable corpus. Regenerate with `python3 docs/artifacts/tools/render_spec_documents.py`.*
