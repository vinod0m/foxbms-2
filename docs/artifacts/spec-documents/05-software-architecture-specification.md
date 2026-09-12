# foxBMS 2 — Software Architecture Specification

**Document Control**

| Field | Value |
|---|---|
| Project | foxBMS 2 — Battery Management System |
| Document | Software Architecture Specification |
| Baseline | BAS-REF-001 (commit `308028fb`, tag `v1.11.0`) |
| Profiles | `as_is` (source-grounded) + `synthetic_reference` (hypothetical) |
| Corpus status | `synthetic_ready_with_limitations` |
| Generated | 2026-09-12T01:01:53Z |

## Scope

Software architecture viewpoints: static component viewpoint (SWR/DSN relations), dynamic state-machine viewpoints per design artifact, and a task/thread timing context — all data-derived.

## Profile: `as_is`

### Static Component Viewpoint

**Caption**: SW requirements, designs, and implements/allocated_to relations.

```mermaid
flowchart TD
    "FB2-SW-SWR-000001" --> "FB2-SAF-FSR-000001"
    "FB2-SW-SWR-000002" --> "FB2-SAF-FSR-000002"
    "FB2-SW-SWR-000003" --> "FB2-SAF-FSR-000003"
    "FB2-SW-DSN-000001" -.implements.-> "FB2-SW-SWR-000001"
    "FB2-SW-DSN-000002" -.implements.-> "FB2-SW-SWR-000002"
    "FB2-SW-DSN-000003" -.implements.-> "FB2-SW-SWR-000003"
```


### Dynamic Viewpoint — `FB2-SW-DSN-000001`

**Caption**: State machine of `FB2-SW-DSN-000001` from `behavior_model` (state_machine).

```mermaid
stateDiagram-v2
    [*] --> INIT
    INIT --> WAKEUP : driver_init
    WAKEUP --> READ_VOLTAGES : wakeup_done
    READ_VOLTAGES --> READ_TEMPERATURES : voltages_done
    READ_TEMPERATURES --> BALANCING : temps_done
    BALANCING --> READ_VOLTAGES : cycle_timer
    * --> ERROR : pec_failure
    ERROR --> INIT : reinit_request
    INIT
    WAKEUP
    READ_VOLTAGES
    READ_TEMPERATURES
    BALANCING
    ERROR
    SLEEP
```


### Dynamic Viewpoint — `FB2-SW-DSN-000002`

**Caption**: State machine of `FB2-SW-DSN-000002` from `behavior_model` (state_machine).

```mermaid
stateDiagram-v2
    [*] --> IDLE
    IDLE --> CHECKING : database_updated
    CHECKING --> DEBOUNCING : limit_exceeded
    DEBOUNCING --> VIOLATION_CONFIRMED : debounce_complete
    DEBOUNCING --> IDLE : back_in_limits
    VIOLATION_CONFIRMED --> FAULT_TRIGGERED : fault_callback
    FAULT_TRIGGERED --> IDLE : system_reset
    IDLE
    CHECKING
    DEBOUNCING
    VIOLATION_CONFIRMED
    FAULT_TRIGGERED
```


### Dynamic Viewpoint — `FB2-SW-DSN-000003`

**Caption**: State machine of `FB2-SW-DSN-000003` from `behavior_model` (state_machine).

```mermaid
stateDiagram-v2
    [*] --> OPEN
    OPEN --> PRECHARGE : request_precharge
    PRECHARGE --> PRECHARGE_WAIT : precharge_contactor_closed
    PRECHARGE_WAIT --> CLOSE : voltage_threshold_reached
    CLOSE --> HOLD : main_contactor_closed
    HOLD --> FAULT_OPEN : fault_request
    HOLD --> OPEN : request_open
    * --> FAULT_OPEN : fault_request
    HOLD --> WELD_DETECTED : feedback_mismatch
    HOLD --> STUCK_OPEN : feedback_mismatch
    OPEN
    PRECHARGE
    PRECHARGE_WAIT
    CLOSE
    HOLD
    FAULT_OPEN
    WELD_DETECTED
    STUCK_OPEN
```


## Profile: `synthetic_reference`

### Static Component Viewpoint

**Caption**: SW requirements, designs, and implements/allocated_to relations.

```mermaid
flowchart TD
    "FB2-SW-SWR-000001" --> "FB2-SAF-FSR-000001"
    "FB2-SW-SWR-000002" --> "FB2-SAF-FSR-000002"
    "FB2-SW-SWR-000003" --> "FB2-SAF-FSR-000003"
    "FB2-SW-DSN-000001" -.implements.-> "FB2-SW-SWR-000001"
    "FB2-SW-DSN-000002" -.implements.-> "FB2-SW-SWR-000002"
    "FB2-SW-DSN-000003" -.implements.-> "FB2-SW-SWR-000003"
```


### Dynamic Viewpoint — `FB2-SW-DSN-000001`

**Caption**: State machine of `FB2-SW-DSN-000001` from `behavior_model` (state_machine).

```mermaid
stateDiagram-v2
    [*] --> INIT
    INIT --> WAKEUP : driver_init
    WAKEUP --> READ_VOLTAGES : wakeup_done
    READ_VOLTAGES --> READ_TEMPERATURES : voltages_done
    READ_TEMPERATURES --> BALANCING : temps_done
    BALANCING --> READ_VOLTAGES : cycle_timer
    * --> ERROR : pec_failure
    ERROR --> INIT : reinit_request
    INIT
    WAKEUP
    READ_VOLTAGES
    READ_TEMPERATURES
    BALANCING
    ERROR
    SLEEP
```


### Dynamic Viewpoint — `FB2-SW-DSN-000002`

**Caption**: State machine of `FB2-SW-DSN-000002` from `behavior_model` (state_machine).

```mermaid
stateDiagram-v2
    [*] --> IDLE
    IDLE --> CHECKING : database_updated
    CHECKING --> DEBOUNCING : limit_exceeded
    DEBOUNCING --> VIOLATION_CONFIRMED : debounce_complete
    DEBOUNCING --> IDLE : back_in_limits
    VIOLATION_CONFIRMED --> FAULT_TRIGGERED : fault_callback
    FAULT_TRIGGERED --> IDLE : system_reset
    IDLE
    CHECKING
    DEBOUNCING
    VIOLATION_CONFIRMED
    FAULT_TRIGGERED
```


### Dynamic Viewpoint — `FB2-SW-DSN-000003`

**Caption**: State machine of `FB2-SW-DSN-000003` from `behavior_model` (state_machine).

```mermaid
stateDiagram-v2
    [*] --> OPEN
    OPEN --> PRECHARGE : request_precharge
    PRECHARGE --> PRECHARGE_WAIT : precharge_contactor_closed
    PRECHARGE_WAIT --> CLOSE : voltage_threshold_reached
    CLOSE --> HOLD : main_contactor_closed
    HOLD --> FAULT_OPEN : fault_request
    HOLD --> OPEN : request_open
    * --> FAULT_OPEN : fault_request
    HOLD --> WELD_DETECTED : feedback_mismatch
    HOLD --> STUCK_OPEN : feedback_mismatch
    OPEN
    PRECHARGE
    PRECHARGE_WAIT
    CLOSE
    HOLD
    FAULT_OPEN
    WELD_DETECTED
    STUCK_OPEN
```


### Task/Thread Timing Context

**Caption**: Timing budget elements (from `FB2-SAF-SGO-000001`) as scheduling context.

```mermaid
flowchart LR
    CHAIN["Protection chain"]
    T_afe_acquisition_ms["afe_acquisition_ms<br/>25 ms"]
    T_afe_acquisition_ms --> CHAIN
    T_contactor_command_ms["contactor_command_ms<br/>5 ms"]
    T_contactor_command_ms --> CHAIN
    T_contactor_mechanical_ms["contactor_mechanical_ms<br/>30 ms"]
    T_contactor_mechanical_ms --> CHAIN
    T_database_publish_ms["database_publish_ms<br/>3 ms"]
    T_database_publish_ms --> CHAIN
    T_fault_classification_ms["fault_classification_ms<br/>2 ms"]
    T_fault_classification_ms --> CHAIN
    T_feedback_verification_ms["feedback_verification_ms<br/>5 ms"]
    T_feedback_verification_ms --> CHAIN
    T_margin_ms["margin_ms<br/>20 ms"]
    T_margin_ms --> CHAIN
    T_pec_validation_ms["pec_validation_ms<br/>2 ms"]
    T_pec_validation_ms --> CHAIN
    T_soa_limit_check_ms["soa_limit_check_ms<br/>5 ms"]
    T_soa_limit_check_ms --> CHAIN
    T_spi_transfer_ms["spi_transfer_ms<br/>5 ms"]
    T_spi_transfer_ms --> CHAIN
    T_sys_state_transition_ms["sys_state_transition_ms<br/>3 ms"]
    T_sys_state_transition_ms --> CHAIN
```



---

*Generated: 2026-09-12T01:01:53Z — auto-generated from the machine-verifiable corpus. Regenerate with `python3 docs/artifacts/tools/render_spec_documents.py`.*
