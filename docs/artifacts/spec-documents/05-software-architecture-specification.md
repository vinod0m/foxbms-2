# foxBMS 2 — Software Architecture Specification

**Document Control**

| Field | Value |
|---|---|
| Project | foxBMS 2 — Battery Management System |
| Document | Software Architecture Specification |
| Baseline | BAS-REF-001 (commit `308028fb`, tag `v1.11.0`) |
| Profiles | `as_is` (source-grounded) + `synthetic_reference` (hypothetical) |
| Corpus status | `synthetic_ready_with_limitations` |
| Generated | 2026-10-01T13:26:59Z |

## Scope

Software architecture viewpoints: reverse-engineered static component viewpoint (40-module inventory across 4 layers with prefixes and unit tests), dynamic viewpoints (BMS/SYS state machines, task model), plus the corpus SWR/DSN relations per profile.

## Static Component Viewpoint — Module Inventory

All software modules reverse-engineered from `src/app/` (layer / module / prefix / brief / sources / unit tests).

### Layer: `engine` (5 modules)

| Module | Prefix | Responsibility (from `@brief`) | Files | Unit tests |
|---|---|---|---|---|
| `engine/database` | `DATA` | Database module header | 4 | 2 |
| `engine/diag` | `DIAG` | Diagnosis driver header | 24 | 1 |
| `engine/hw_info` | `MINFO` | General foxBMS-master system information | 2 | 1 |
| `engine/sys` | `SYS` | Software reset driver header | 4 | 2 |
| `engine/sys_mon` | `SYSM` | System monitoring module | 2 | 1 |

### Layer: `task` (3 modules)

| Module | Prefix | Responsibility (from `@brief`) | Files | Unit tests |
|---|---|---|---|---|
| `task/ftask` | `FTSK` | Header of task driver implementation | 3 | 2 |
| `task/os` | `OS` | Declaration of the OS wrapper interface | 4 | 1 |
| `task/timer` | `TIMER` | Header file for the timer wrapper | 2 | 1 |

### Layer: `application` (7 modules)

| Module | Prefix | Responsibility (from `@brief`) | Files | Unit tests |
|---|---|---|---|---|
| `application/algorithm` | `ALGO` | Algorithms framework: SOX estimation and moving averages | 26 | 1 |
| `application/bal` | `BAL` | Header for the driver for balancing | 5 | 1 |
| `application/bms` | `BMS` | BMS driver header | 2 | 1 |
| `application/ethernet` | `ETH` | Header of the ethernet software | 4 | 2 |
| `application/plausibility` | `PL` | Plausibility checks for cell voltage and cell temperatures | 2 | 1 |
| `application/redundancy` | `MRC` | Header files for handling redundancy between redundant cell voltage | 2 | 1 |
| `application/soa` | `SOA` | Header for SOA module, responsible for checking battery parameters | 2 | 1 |

### Layer: `driver` (25 modules)

| Module | Prefix | Responsibility (from `@brief`) | Files | Unit tests |
|---|---|---|---|---|
| `driver/adc` | `ADC` | Headers for the driver for the ADC module. | 2 | 1 |
| `driver/can` | `CAN` | Header for the driver for the CAN module | 44 | 4 |
| `driver/contactor` | `CONT` | Headers for the driver for the contactors. | 2 | 1 |
| `driver/crc` | `CRC` | CRC module header | 2 | 1 |
| `driver/dma` | `DMA` | Headers for the driver for the DMA module. | 2 | 4 |
| `driver/emac` | `EMAC` | Implementation of emac driver | 4 | 2 |
| `driver/foxmath` | `MATH` | Math library for often used math functions | 4 | 2 |
| `driver/fram` | `FRAM` | Header for the driver for the FRAM module | 2 | 1 |
| `driver/htsensor` | `HTSEN` | Header for the driver for the Sensirion SHT35-DIS I2C humidity/temperature sensor | 2 | 1 |
| `driver/i2c` | `I2C` | Header for the driver for the I2C module | 2 | 1 |
| `driver/imd` | `IMD` | API header for the insulation monitoring device | 12 | 1 |
| `driver/interlock` | `ILCK` | Headers for the driver for the interlock. | 2 | 1 |
| `driver/io` | `IO` | Header for the driver for the IO module | 2 | 1 |
| `driver/led` | `LED` | Header file of the debug LED driver | 2 | 1 |
| `driver/mcu` | `MCU` | Headers for the driver for the MCU module. | 2 | 1 |
| `driver/meas` | `MEAS` | Headers for the driver for the measurements needed by the BMS | 2 | 1 |
| `driver/pex` | `PEX` | Header for the driver for the NXP PCA9539 port expander module | 2 | 1 |
| `driver/phy` | `PHY` | Implementation of physical layer driver | 2 | 1 |
| `driver/pwm` | `PWM` | PWM driver for the TMS570LC43xx. | 2 | 1 |
| `driver/rtc` | `RTC` | Header file of the RTC driver | 2 | 1 |
| `driver/sbc` | `FS85` | Driver for the NXP FS85 SBC (system basis chip) supervisor | 11 | 3 |
| `driver/spi` | `SPI` | Headers for the driver for the SPI module. | 3 | 9 |
| `driver/sps` | `SPS` | Headers for the driver for the smart power switches. | 3 | 1 |
| `driver/ts` | `BETA` | Temperature sensor evaluation (resistive divider, beta model) | 44 | 1 |
| `driver/uart` | `UART` | Drivers for UART RS232 | 2 | 2 |

Configuration is separated from module logic into per-layer `config/` directories (`src/app/*/config/*_cfg.c|h`) — each module pairs with a `*_cfg` file (see Detailed Design).

## Dynamic Viewpoint — Task Model

**Caption**: RTOS task set (FreeRTOS): four cyclic tasks (1 ms, 10 ms, 100 ms, 100 ms algorithm) plus continuous blocking tasks (I2C, engine). Source: `src/app/task/ftask/ftask.c`, `src/app/task/config/ftask_cfg.c`.

```mermaid
flowchart TD
    OS[FreeRTOS Scheduler]
    1ms["1ms (4 functions)"]
    OS --> 1ms
    10ms["10ms (11 functions)"]
    OS --> 10ms
    100ms["100ms (5 functions)"]
    OS --> 100ms
    100ms_algorithm["100ms-algorithm (1 functions)"]
    OS --> 100ms_algorithm
    i2c_continuous["i2c (continuous) (3 functions)"]
    OS --> i2c_continuous
    engine_continuous["engine (continuous) (1 functions)"]
    OS --> engine_continuous
```


## Data Exchange Viewpoint

**Caption**: Producer/consumer database (engine layer) — asynchronous data exchange between tasks; single producer, multiple consumers, integrity ensured (source: `docs/software/structure/application.rst`, `src/app/engine/database/`).

```mermaid
flowchart LR
    MEAS[MEAS_Control\n1ms] --> DB[(Database DATA)]
    CANRX[CAN_ReadRxBuffer\n1ms] --> DB
    ADC[ADC_Control\n10ms] --> DB
    SPS[SPS_Ctrl\n10ms] --> DB
    MRC[MRC_Validate*\n50ms] --> DB
    DB --> SOA[SOA evaluation]
    DB --> ALGO[SE_RunStateEstimations\n1s]
    DB --> BMS[BMS_Trigger\n10ms]
    BMS --> CAN_TX[CAN_MainFunction\n10ms]
    DIAG[DIAG_UpdateFlags\n1ms] --> DB
```


## Profile: `as_is` — Traceability Viewpoints

### Static Component Viewpoint (corpus)

**Caption**: SW requirements, designs, and implements/allocated_to relations.

```mermaid
flowchart TD
    "FB2-SW-SWR-000001" --> "FB2-SAF-FSR-000001"
    "FB2-SW-SWR-000001" --> "FB2-SW-DSN-000001"
    "FB2-SW-SWR-000002" --> "FB2-SAF-FSR-000002"
    "FB2-SW-SWR-000002" --> "FB2-SW-DSN-000002"
    "FB2-SW-SWR-000003" --> "FB2-SAF-FSR-000003"
    "FB2-SW-SWR-000003" --> "FB2-SW-DSN-000003"
    "FB2-SW-IMP-000001" -.implements.-> "FB2-SW-DSN-000001"
    "FB2-SW-IMP-000001" -.implements.-> "FB2-SW-SWR-000001"
    "FB2-SW-IMP-000002" -.implements.-> "FB2-SW-DSN-000002"
    "FB2-SW-IMP-000002" -.implements.-> "FB2-SW-SWR-000002"
    "FB2-SW-IMP-000003" -.implements.-> "FB2-SW-DSN-000003"
    "FB2-SW-IMP-000003" -.implements.-> "FB2-SW-SWR-000003"
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


## Profile: `synthetic_reference` — Traceability Viewpoints

### Static Component Viewpoint (corpus)

**Caption**: SW requirements, designs, and implements/allocated_to relations.

```mermaid
flowchart TD
    "FB2-SW-SWR-000001" --> "FB2-SAF-FSR-000001"
    "FB2-SW-SWR-000001" --> "FB2-SW-DSN-000001"
    "FB2-SW-SWR-000001" --> "FB2-SYS-SYR-000001"
    "FB2-SW-SWR-000001" --> "FB2-SYS-SYR-000002"
    "FB2-SW-SWR-000001" --> "FB2-SYS-SYR-000006"
    "FB2-SW-SWR-000001" --> "FB2-SYS-SYR-000007"
    "FB2-SW-SWR-000002" --> "FB2-SAF-FSR-000002"
    "FB2-SW-SWR-000002" --> "FB2-SW-DSN-000002"
    "FB2-SW-SWR-000002" --> "FB2-SYS-SYR-000002"
    "FB2-SW-SWR-000003" --> "FB2-SAF-FSR-000003"
    "FB2-SW-SWR-000003" --> "FB2-SW-DSN-000003"
    "FB2-SW-SWR-000003" --> "FB2-SYS-SYR-000003"
    "FB2-SW-SWR-000003" --> "FB2-SYS-SYR-000004"
    "FB2-SW-SWR-000003" --> "FB2-SYS-SYR-000008"
    "FB2-SW-IMP-000001" -.implements.-> "FB2-SW-DSN-000001"
    "FB2-SW-IMP-000001" -.implements.-> "FB2-SW-SWR-000001"
    "FB2-SW-IMP-000001" -.implements.-> "FB2-SW-DSN-000004"
    "FB2-SW-IMP-000002" -.implements.-> "FB2-SW-DSN-000002"
    "FB2-SW-IMP-000002" -.implements.-> "FB2-SW-SWR-000002"
    "FB2-SW-IMP-000002" -.implements.-> "FB2-SW-DSN-000005"
    "FB2-SW-IMP-000003" -.implements.-> "FB2-SW-DSN-000003"
    "FB2-SW-IMP-000003" -.implements.-> "FB2-SW-SWR-000003"
    "FB2-SW-IMP-000003" -.implements.-> "FB2-SW-DSN-000006"
    "FB2-SW-IMP-000004" -.implements.-> "FB2-SYS-SYR-000007"
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


### Dynamic Viewpoint — `FB2-SW-DSN-000004`

**Caption**: State machine of `FB2-SW-DSN-000004` from `behavior_model` (state_machine).

```mermaid
stateDiagram-v2
    [*] --> LTC_STATEMACH_UNINITIALIZED
    LTC_STATEMACH_UNINITIALIZED --> LTC_STATEMACH_INITIALIZATION : LTC_Trigger entry with substat...
    LTC_STATEMACH_INITIALIZATION --> LTC_STATEMACH_INITIALIZATION : LTC_CHECK_INITIALIZATION
    LTC_STATEMACH_INITIALIZATION --> LTC_STATEMACH_INITIALIZATION : LTC_EXIT_INITIALIZATION
    any state with a non-STD_OK operation result --> LTC_STATEMACH_ERROR_SPIFAILED : LTC_CondBasedStateTransition w...
    any state with a STD_OK operation result --> caller-supplied state_ok : LTC_CondBasedStateTransition w...
    LTC_STATEMACH_MEASCYCLE_FINISHED --> LTC_STATEMACH_IDLE : completion of a measurement cy...
    any state, on every LTC_Trigger entry --> unchanged : entry-time timer gate
    LTC_STATEMACH_UNINITIALIZED
    LTC_STATEMACH_INITIALIZATION
    LTC_STATEMACH_REINIT
    LTC_STATEMACH_INITIALIZED
    LTC_STATEMACH_IDLE
    LTC_STATEMACH_STARTMEAS
    LTC_STATEMACH_READVOLTAGE
    LTC_STATEMACH_MUXMEASUREMENT
    LTC_STATEMACH_MUXMEASUREMENT_FINISHED
    LTC_STATEMACH_BALANCE_CONTROL
    LTC_STATEMACH_ALL_GPIO_MEASUREMENT
    LTC_STATEMACH_READALLGPIO
    LTC_STATEMACH_READVOLTAGE_2CELLS
    LTC_STATEMACH_STARTMEAS_2CELLS
    LTC_STATEMACH_USER_IO_CONTROL
    LTC_STATEMACH_USER_IO_FEEDBACK
    LTC_STATEMACH_EEPROM_READ
    LTC_STATEMACH_EEPROM_WRITE
    LTC_STATEMACH_TEMP_SENS_READ
    LTC_STATEMACH_BALANCE_FEEDBACK
    LTC_STATEMACH_OPENWIRE_CHECK
    LTC_STATEMACH_DEVICE_PARAMETER
    LTC_STATEMACH_ADC_ACCURACY
    LTC_STATEMACH_DIGITAL_FILTER
    LTC_STATEMACH_VOLTAGE_MEASURE_SUM_OF_CELLS
    LTC_STATEMACH_EEPROM_READ_UID
    LTC_STATEMACH_USER_IO_CONTROL_TI
    LTC_STATEMACH_USER_IO_FEEDBACK_TI
    LTC_STATEMACH_STARTMEAS_CONTINUE
    LTC_STATEMACH_MEASCYCLE_FINISHED
    LTC_STATEMACH_UNDEFINED
    LTC_STATEMACH_RESERVED1
    LTC_STATEMACH_ERROR_SPIFAILED
    LTC_STATEMACH_ERROR_PEC_FAILED
    LTC_STATEMACH_ERROR_MULTIPLEXER_FAILED
    LTC_STATEMACH_ERROR_INITIALIZATION
```


### Dynamic Viewpoint — `FB2-SW-DSN-000005`

**Caption**: State machine of `FB2-SW-DSN-000005` from `behavior_model` (combination).

```mermaid
stateDiagram-v2
    [*] --> string voltage evaluated
    string voltage evaluated --> string voltage evaluated : maximumCellVoltage_mV >= BC_VO...
    string voltage evaluated --> string voltage evaluated : maximumCellVoltage_mV < BC_VOL...
    string voltage evaluated --> string voltage evaluated : minimumCellVoltage_mV <= BC_VO...
    string voltage evaluated --> string voltage evaluated : minimumCellVoltage_mV <= BC_VO...
    string temperature evaluated against the discharge limit set --> string temperature evaluated against the charge limit set : BMS_GetCurrentFlowDirection(st...
    string current valid and evaluated --> string current valid and evaluated : SOA_IsStringCurrentLimitViolat...
    string current valid and evaluated --> string current valid and evaluated : SOA_IsCurrentOnOpenString(curr...
    string current invalid and skipped --> pack current valid and evaluated : end of the string loop
    any state --> slave temperature not evaluated : BMS_Trigger calls SOA_CheckSla...
    string voltage evaluated
    string temperature evaluated against the discharge limit set
    string temperature evaluated against the charge limit set
    string current valid and evaluated
    string current invalid and skipped
    pack current valid and evaluated
    pack current invalid and skipped
    current direction unresolved at rest and exempt from all current limits
    slave temperature not evaluated
```


### Dynamic Viewpoint — `FB2-SW-DSN-000006`

**Caption**: State machine of `FB2-SW-DSN-000006` from `behavior_model` (combination).

```mermaid
stateDiagram-v2
    [*] --> command recorded, feedback not yet sampled
    command recorded, feedback not yet sampled --> command recorded, feedback sampled and matching : CONT_OpenContactor or CONT_Clo...
    command recorded, feedback not yet sampled --> command recorded, feedback sampled and mismatching : CONT_OpenContactor or CONT_Clo...
    any state --> contactor configured without feedback : CONT_GetFeedbackOfAllContactor...
    no registry entry matched the request --> no registry entry matched the request : the linear scan over BS_NR_OF_...
    string without a precharge contactor --> string without a precharge contactor : CONT_ClosePrecharge or CONT_Op...
    any state --> command recorded, feedback not yet sampled : CONT_OpenAllContactors from th...
    registry unvalidated --> registry validated : CONT_Initialize calls the regi...
    command recorded, feedback not yet sampled
    command recorded, feedback sampled and matching
    command recorded, feedback sampled and mismatching
    contactor configured without feedback
    no registry entry matched the request
    string without a precharge contactor
    registry unvalidated
    registry validated
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
    T_margin_ms["margin_ms<br/>15 ms"]
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

*Generated: 2026-10-01T13:26:59Z — auto-generated from the machine-verifiable corpus. Regenerate with `python3 docs/artifacts/tools/render_spec_documents.py`.*
