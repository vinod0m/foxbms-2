# foxBMS 2 — System Architecture Specification

**Document Control**

| Field | Value |
|---|---|
| Project | foxBMS 2 — Battery Management System |
| Document | System Architecture Specification |
| Baseline | BAS-REF-001 (commit `308028fb`, tag `v1.11.0`) |
| Profiles | `as_is` (source-grounded) + `synthetic_reference` (hypothetical) |
| Corpus status | `synthetic_ready_with_limitations` |
| Generated | 2026-09-13T15:17:46Z |

## Scope

System architecture viewpoints — context, functional block, dynamic — combining the reverse-engineered software architecture (layers, tasks, state machines, data flow; sources: `src/app`, `docs/software/structure/`) with the per-profile link registries.

## Context Viewpoint

**Caption**: foxBMS 2 system context — BMS-Master and BMS-Slaves with external actors (reverse-engineered from `docs/introduction/bms-overview.rst`, `conf/bms/bms.json`).

```mermaid
flowchart LR
    VCU[VCU / Host\nCAN: 41 msgs] <--> MASTER
    CS[Current Sensor\nivt-s] <--> MASTER
    IMD[IMD\noptional] --- MASTER
    subgraph Item[foxBMS 2 BMS Item]
        MASTER[BMS-Master\nTMS570LC4357 / FreeRTOS\nsrc/app: 40 modules]
        SLAVES[BMS-Slaves\nAFE daisy-chain]
    end
    MASTER <-->|SPI daisy-chain| SLAVES
    SLAVES --- CELLS[Battery Cells / Modules]\nvoltage + temperature + balancing
    MASTER --- CONT[Contactors\nString-/Precharge]
    MASTER --- ILCK[Interlock Circuit]
    CELLS --- LOAD[Load / Charger]
```


## Functional Block Viewpoint

**Caption**: Layered software architecture (source: `docs/software/structure/software-structure.rst`, `src/app/`) — application 7, driver 25, engine 5, task/OS 3 modules.

Design paradigms (from the structure documentation): (1) all application code runs in an operating-system context; (2) MCU and external-hardware dependent drivers are abstracted by wrappers/abstraction layers.

```mermaid
flowchart TB
    subgraph OS[Operating System - FreeRTOS / SafeRTOS path]
        FTSK[ftask - cyclic + continuous tasks]
        OSW[os wrapper / timer]
    end
    subgraph ENG[Engine Layer]
        ENGM[database / diag / hw_info / sys / sys_mon]
    end
    subgraph APP[Application Layer]
        APPM[algorithm / bal / bms / ethernet / plausibility / redundancy / soa]
    end
    subgraph DRV[Driver Layer - MCU wrapper]
        DRVM[adc / can / contactor / crc / dma / emac / foxmath / fram / htsensor / i2c / imd / interlock / io / led / mcu / meas / pex / phy / pwm / rtc / sbc / spi / sps / ts / uart]
    end
    HAL[HAL / TI HALCoGen]
    MCU[TMS570LC4357 Cortex-R5F]
    OS --> ENG --> APP --> DRV --> HAL --> MCU
```

- **Engine layer**: diagnostics, error handling, system monitoring, database (producer/consumer asynchronous data exchange between tasks/modules).
- **Driver layer**: communication interfaces (CAN, UART, SPI, Ethernet/EMAC), measurement control (AFE, ADC, current sensor), hardware supervision (SBC, port expander, RTC, FRAM, interlock, contactors/SPS, IMD, LEDs).

### Task Engineering Viewpoint

**Caption**: Task-function mapping from `src/app/task/config/ftask_cfg.c` (user code functions per task, verified against the source).

| Task | Period / mode | Functions |
|---|---|---|
| 1ms | 1 ms cyclic | `OS_IncrementTimer`, `DIAG_UpdateFlags`, `MEAS_Control (AFE driver type FSM)`, `CAN_ReadRxBuffer` |
| 10ms | 10 ms cyclic | `SYSM_UpdateFramData`, `SYS_Trigger`, `ILCK_Trigger`, `ADC_Control`, `SPS_Ctrl`, `CAN_MainFunction`, `SOF_Calculation`, `ALGO_MonitorExecutionTime`, `SBC_Trigger`, `MRC_ValidateAfeMeasurement / MRC_ValidatePackMeasurement (every 50 ms)`, `BMS_Trigger (last: minimize reaction delay)` |
| 100ms | 100 ms cyclic | `SE_RunStateEstimations (every 1 s)`, `BAL_Trigger`, `IMD_Trigger`, `LED_Trigger`, `MINFO_CheckSupplyVoltageClamp30c` |
| 100ms-algorithm | 100 ms cyclic (algorithms) | `ALGO_MainFunction` |
| i2c (continuous) | continuous, 2 ms delay | `PEX_Trigger`, `HTSEN_Trigger`, `RTC_Trigger` |
| engine (continuous) | continuous, blocking | `SBC state machine / FRAM / engine sequencing` |

Priority order (from the docs): database/engine context highest, then 1 ms task (time-sensitive: diagnostics, measurement, CAN RX), 10 ms task (CAN TX, interlock, SPS, ADC, BMS trigger), 100 ms task (state estimation, balancing, IMD, LED), 100 ms algorithm task (user algorithms).

## Dynamic Viewpoint

### BMS State Machine (application core)

**Caption**: BMS FSM — 13 states (`src/app/application/bms/bms.h`), triggered every 10 ms by `BMS_Trigger()` in the 10 ms task.

```mermaid
stateDiagram-v2
    [*] --> BMS_FSM_STATE_UNINITIALIZED
    BMS_FSM_STATE_UNINITIALIZED --> BMS_FSM_STATE_INITIALIZATION : initialization request
    BMS_FSM_STATE_INITIALIZATION --> BMS_FSM_STATE_INITIALIZED : init done
    BMS_FSM_STATE_INITIALIZED --> BMS_FSM_STATE_IDLE : standby
    BMS_FSM_STATE_IDLE --> BMS_FSM_STATE_STANDBY : close contactors request
    BMS_FSM_STATE_STANDBY --> BMS_FSM_STATE_PRECHARGE : precharge request
    BMS_FSM_STATE_PRECHARGE --> BMS_FSM_STATE_NORMAL : precharge finished
    BMS_FSM_STATE_NORMAL --> BMS_FSM_STATE_DISCHARGE : discharge power path
    BMS_FSM_STATE_NORMAL --> BMS_FSM_STATE_CHARGE : charge power path
    BMS_FSM_STATE_ERROR_STATE[BMS_FSM_STATE_ERROR] : any state on fatal diagnosis
    BMS_FSM_STATE_ERROR --> BMS_FSM_STATE_OPEN_CONTACTORS : open contactors
    BMS_FSM_STATE_OPEN_CONTACTORS --> BMS_FSM_STATE_STANDBY : contactors open (safe state)
    BMS_FSM_STATE_UNINITIALIZED
    BMS_FSM_STATE_INITIALIZATION
    BMS_FSM_STATE_INITIALIZED
    BMS_FSM_STATE_IDLE
    BMS_FSM_STATE_OPEN_CONTACTORS
    BMS_FSM_STATE_STANDBY
    BMS_FSM_STATE_PRECHARGE
    BMS_FSM_STATE_NORMAL
    BMS_FSM_STATE_DISCHARGE
    BMS_FSM_STATE_CHARGE
    BMS_FSM_STATE_ERROR
    BMS_FSM_STATE_UNDEFINED
    BMS_FSM_STATE_RESERVED1
```

Substates (34) implement the entry checks (interlock, state requests, balancing requests, error flags) and the precharge sequences (close minus → close precharge → check → open precharge → close plus; second-string variants included).

### SYS State Machine (engine startup sequencing)

**Caption**: SYS FSM — 7 states (`src/app/engine/sys/sys.h`), sequencing the startup: FRAM deep-discharge check, SBC init, interlock init, CAN init, RTC, built-in self-test, boot message, balancing init, first measurement cycle, current-sensor presence check, IMD init.

```mermaid
stateDiagram-v2
    [*] --> SYS_FSM_STATE_HAS_NEVER_RUN
    SYS_FSM_STATE_HAS_NEVER_RUN --> SYS_FSM_STATE_UNINITIALIZED
    SYS_FSM_STATE_UNINITIALIZED --> SYS_FSM_STATE_INITIALIZATION
    SYS_FSM_STATE_INITIALIZATION --> SYS_FSM_STATE_PRE_RUNNING
    SYS_FSM_STATE_PRE_RUNNING --> SYS_FSM_STATE_RUNNING
    SYS_FSM_STATE_RUNNING --> SYS_FSM_STATE_ERROR : fatal error
    SYS_FSM_STATE_DUMMY
    SYS_FSM_STATE_HAS_NEVER_RUN
    SYS_FSM_STATE_UNINITIALIZED
    SYS_FSM_STATE_INITIALIZATION
    SYS_FSM_STATE_PRE_RUNNING
    SYS_FSM_STATE_RUNNING
    SYS_FSM_STATE_ERROR
```


### Protection Chain Sequence (cell voltage)

**Caption**: Sequence of the cell-voltage protection chain (AFE → database → SOA plausibility → diagnosis → BMS FSM → contactors), matching the module call graph and the corpus FTTI allocation.

```mermaid
sequenceDiagram
    participant AFE as AFE Driver (MEAS, 1ms task)
    participant DB as Database (DATA)
    participant PL as Plausibility / Redundancy (MRC)
    participant SOA as SOA Monitor
    participant DIAG as Diagnosis (DIAG)
    participant BMS as BMS FSM (10ms task)
    participant SPS as Contactor Ctrl (SPS)
    AFE->>DB: publish validated cell voltages
    DB->>PL: MRC_ValidateAfeMeasurement (every 50 ms)
    DB->>SOA: SOA evaluation (10 ms context)
    SOA->>DIAG: MSL violation event
    DIAG->>BMS: fatal error flag set
    BMS->>BMS: transition to ERROR state
    BMS->>SPS: open string contactors (safe state)
    Note over BMS,SPS: within FTTI budget (corpus: 100 ms total)
```


## Profile: `as_is` — Traceability Viewpoint

**Caption**: Cell-voltage protection chain blocks from the link registry (HAZ ← mitigates ← SGO ← refines ← FSRs ← allocated_to ← TSR/SWR).

```mermaid
flowchart TD
    HAZ["FB2-SAF-HAZ-000001 Hazard"]
    SGO["FB2-SAF-SGO-000001 Safety Goal"]
    HAZ --- SGO
    "FB2-SAF-FSR-000001" --- "FB2-SAF-SGO-000001"
    "FB2-SAF-FSR-000002" --- "FB2-SAF-SGO-000001"
    "FB2-SAF-FSR-000003" --- "FB2-SAF-SGO-000001"
    "FB2-HW-TSR-000001" -.allocated_to.-> "FB2-SAF-FSR-000001"
    "FB2-HW-TSR-000002" -.allocated_to.-> "FB2-SAF-FSR-000001"
    "FB2-HW-TSR-000003" -.allocated_to.-> "FB2-SAF-FSR-000003"
    "FB2-SW-SWR-000001" -.allocated_to.-> "FB2-SAF-FSR-000001"
    "FB2-SW-SWR-000002" -.allocated_to.-> "FB2-SAF-FSR-000002"
    "FB2-SW-SWR-000003" -.allocated_to.-> "FB2-SAF-FSR-000003"
    "FB2-SW-DSN-000001" -.implements.-> "FB2-SW-SWR-000001"
    "FB2-SW-DSN-000002" -.implements.-> "FB2-SW-SWR-000002"
    "FB2-SW-DSN-000003" -.implements.-> "FB2-SW-SWR-000003"
```


## Profile: `synthetic_reference` — Traceability Viewpoint

**Caption**: Cell-voltage protection chain blocks from the link registry (HAZ ← mitigates ← SGO ← refines ← FSRs ← allocated_to ← TSR/SWR).

```mermaid
flowchart TD
    HAZ["FB2-SAF-HAZ-000001 Hazard"]
    SGO["FB2-SAF-SGO-000001 Safety Goal"]
    HAZ --- SGO
    "FB2-SAF-FSR-000001" --- "FB2-SAF-SGO-000001"
    "FB2-SAF-FSR-000002" --- "FB2-SAF-SGO-000001"
    "FB2-SAF-FSR-000003" --- "FB2-SAF-SGO-000001"
    "FB2-SAF-FSR-000004" --- "FB2-SAF-SGO-000001"
    "FB2-HW-TSR-000001" -.allocated_to.-> "FB2-SAF-FSR-000001"
    "FB2-HW-TSR-000002" -.allocated_to.-> "FB2-SAF-FSR-000001"
    "FB2-HW-TSR-000003" -.allocated_to.-> "FB2-SAF-FSR-000003"
    "FB2-SW-SWR-000001" -.allocated_to.-> "FB2-SAF-FSR-000001"
    "FB2-SW-SWR-000002" -.allocated_to.-> "FB2-SAF-FSR-000002"
    "FB2-SW-SWR-000003" -.allocated_to.-> "FB2-SAF-FSR-000003"
    "FB2-SW-DSN-000001" -.implements.-> "FB2-SW-SWR-000001"
    "FB2-SW-DSN-000002" -.implements.-> "FB2-SW-SWR-000002"
    "FB2-SW-DSN-000003" -.implements.-> "FB2-SW-SWR-000003"
```



---

*Generated: 2026-09-13T15:17:46Z — auto-generated from the machine-verifiable corpus. Regenerate with `python3 docs/artifacts/tools/render_spec_documents.py`.*
