# foxBMS 2 — Implementation Mapping Document

**Document Control**

| Field | Value |
|---|---|
| Project | foxBMS 2 — Battery Management System |
| Document | Implementation Mapping Document |
| Baseline | BAS-REF-001 (commit `308028fb`, tag `v1.11.0`) |
| Profiles | `as_is` (source-grounded) + `synthetic_reference` (hypothetical) |
| Corpus status | `synthetic_ready_with_limitations` |
| Generated | 2026-10-03T11:20:05Z |

## Scope

Implementation mapping: (1) reverse-engineered module → sources → config → unit-test → documentation mapping for all 40 modules; (2) corpus design → source mappings and requirement → design → source → test chains; (3) the complete requirement-to-test coverage matrix for every requirement artifact in both profiles.

## Reverse-Engineered Module Mapping

Complete mapping of every implemented module to its source files, configuration, unit tests and module documentation (all paths relative to the repository root):

| Module | Main sources | Config | Unit tests | Docs |
|---|---|---|---|---|
| `application/algorithm` | `src/app/application/algorithm/algorithm.c`, `src/app/application/algorithm/algorithm.h`, `src/app/application/algorithm/config/algorithm_cfg.c` … | — | 1 | `docs/software/modules/application/algorithm/algorithm.rst` |
| `application/bal` | `src/app/application/bal/bal.c`, `src/app/application/bal/bal.h`, `src/app/application/bal/history/bal_strategy_history.c` … | `src/app/application/config/bal_cfg.c`, `src/app/application/config/bal_cfg.h` | 1 | `docs/software/modules/application/bal/bal.rst` |
| `application/bms` | `src/app/application/bms/bms.c`, `src/app/application/bms/bms.h` | `src/app/application/config/bms_cfg.h` | 1 | `docs/software/modules/application/bms/bms.rst` |
| `application/ethernet` | `src/app/application/ethernet/ethernet.c`, `src/app/application/ethernet/ethernet.h`, `src/app/application/ethernet/ethernet_freertos.c` … | `src/app/application/config/ethernet_cfg.c`, `src/app/application/config/ethernet_cfg.h` | 2 | `docs/software/modules/application/ethernet/ethernet.rst` |
| `application/plausibility` | `src/app/application/plausibility/plausibility.c`, `src/app/application/plausibility/plausibility.h` | `src/app/application/config/plausibility_cfg.h` | 1 | `docs/software/modules/application/plausibility/plausibility.rst` |
| `application/redundancy` | `src/app/application/redundancy/redundancy.c`, `src/app/application/redundancy/redundancy.h` | — | 1 | `docs/software/modules/application/redundancy/redundancy.rst` |
| `application/soa` | `src/app/application/soa/soa.c`, `src/app/application/soa/soa.h` | `src/app/application/config/soa_cfg.c`, `src/app/application/config/soa_cfg.h` | 1 | `docs/software/modules/application/soa/soa.rst` |
| `driver/adc` | `src/app/driver/adc/adc.c`, `src/app/driver/adc/adc.h` | — | 1 | `docs/software/modules/driver/adc/adc.rst` |
| `driver/can` | `src/app/driver/can/can.c`, `src/app/driver/can/can.h`, `src/app/driver/can/cbs/can_helper.c` … | `src/app/driver/config/can_cfg.c`, `src/app/driver/config/can_cfg.h` | 4 | `docs/software/modules/driver/can/can.rst` |
| `driver/contactor` | `src/app/driver/contactor/contactor.c`, `src/app/driver/contactor/contactor.h` | `src/app/driver/config/contactor_cfg.c`, `src/app/driver/config/contactor_cfg.h` | 1 | `docs/software/modules/driver/contactor/contactor.rst` |
| `driver/crc` | `src/app/driver/crc/crc.c`, `src/app/driver/crc/crc.h` | — | 1 | `docs/software/modules/driver/crc/crc.rst` |
| `driver/dma` | `src/app/driver/dma/dma.c`, `src/app/driver/dma/dma.h` | `src/app/driver/config/dma_cfg.c`, `src/app/driver/config/dma_cfg.h` | 4 | `docs/software/modules/driver/dma/dma.rst` |
| `driver/emac` | `src/app/driver/emac/emac-low-level.c`, `src/app/driver/emac/emac-low-level.h`, `src/app/driver/emac/emac.c` … | `src/app/driver/config/emac_cfg.h` | 2 | `docs/software/modules/driver/emac/emac.rst` |
| `driver/foxmath` | `src/app/driver/foxmath/foxmath.c`, `src/app/driver/foxmath/foxmath.h`, `src/app/driver/foxmath/utils.c` … | — | 2 | `docs/software/modules/driver/foxmath/foxmath.rst` |
| `driver/fram` | `src/app/driver/fram/fram.c`, `src/app/driver/fram/fram.h` | `src/app/driver/config/fram_cfg.c`, `src/app/driver/config/fram_cfg.h` | 1 | `docs/software/modules/driver/fram/fram.rst` |
| `driver/htsensor` | `src/app/driver/htsensor/htsensor.c`, `src/app/driver/htsensor/htsensor.h` | — | 1 | `docs/software/modules/driver/htsensor/htsensor.rst` |
| `driver/i2c` | `src/app/driver/i2c/i2c.c`, `src/app/driver/i2c/i2c.h` | — | 1 | `docs/software/modules/driver/i2c/i2c.rst` |
| `driver/imd` | `src/app/driver/imd/bender/ir155/bender_ir155.c`, `src/app/driver/imd/bender/ir155/bender_ir155.h`, `src/app/driver/imd/bender/ir155/bender_ir155_helper.c` … | — | 1 | `docs/software/modules/driver/imd/imd.rst` |
| `driver/interlock` | `src/app/driver/interlock/interlock.c`, `src/app/driver/interlock/interlock.h` | `src/app/driver/config/interlock_cfg.h` | 1 | `docs/software/modules/driver/interlock/interlock.rst` |
| `driver/io` | `src/app/driver/io/io.c`, `src/app/driver/io/io.h` | — | 1 | `docs/software/modules/driver/io/io.rst` |
| `driver/led` | `src/app/driver/led/led.c`, `src/app/driver/led/led.h` | — | 1 | `docs/software/modules/driver/led/led.rst` |
| `driver/mcu` | `src/app/driver/mcu/mcu.c`, `src/app/driver/mcu/mcu.h` | — | 1 | `docs/software/modules/driver/mcu/mcu.rst` |
| `driver/meas` | `src/app/driver/meas/meas.c`, `src/app/driver/meas/meas.h` | — | 1 | `docs/software/modules/driver/meas/meas.rst` |
| `driver/pex` | `src/app/driver/pex/pex.c`, `src/app/driver/pex/pex.h` | `src/app/driver/config/pex_cfg.c`, `src/app/driver/config/pex_cfg.h` | 1 | `docs/software/modules/driver/pex/pex.rst` |
| `driver/phy` | `src/app/driver/phy/dp83869.c`, `src/app/driver/phy/dp83869.h` | `src/app/driver/config/phy_cfg.h` | 1 | `docs/software/modules/driver/phy/phy.rst` |
| `driver/pwm` | `src/app/driver/pwm/pwm.c`, `src/app/driver/pwm/pwm.h` | — | 1 | `docs/software/modules/driver/pwm/pwm.rst` |
| `driver/rtc` | `src/app/driver/rtc/rtc.c`, `src/app/driver/rtc/rtc.h` | — | 1 | `docs/software/modules/driver/rtc/rtc.rst` |
| `driver/sbc` | `src/app/driver/sbc/fs8x_driver/sbc_fs8x.c`, `src/app/driver/sbc/fs8x_driver/sbc_fs8x.h`, `src/app/driver/sbc/fs8x_driver/sbc_fs8x_assert.h` … | — | 3 | `docs/software/modules/driver/sbc/sbc.rst` |
| `driver/spi` | `src/app/driver/spi/spi.c`, `src/app/driver/spi/spi.h`, `src/app/driver/spi/spi_cfg-helper.h` | `src/app/driver/config/spi_cfg.c`, `src/app/driver/config/spi_cfg.h` | 9 | `docs/software/modules/driver/spi/spi.rst` |
| `driver/sps` | `src/app/driver/sps/sps.c`, `src/app/driver/sps/sps.h`, `src/app/driver/sps/sps_types.h` | `src/app/driver/config/sps_cfg.c`, `src/app/driver/config/sps_cfg.h` | 1 | `docs/software/modules/driver/sps/sps.rst` |
| `driver/ts` | `src/app/driver/ts/api/tsi.h`, `src/app/driver/ts/api/tsi_limits.c`, `src/app/driver/ts/beta.c` … | — | 1 | `docs/software/modules/driver/ts/ts.rst` |
| `driver/uart` | `src/app/driver/uart/uart.c`, `src/app/driver/uart/uart.h` | `src/app/driver/config/uart_cfg.h` | 2 | `docs/software/modules/driver/uart/uart.rst` |
| `engine/database` | `src/app/engine/database/database.c`, `src/app/engine/database/database.h`, `src/app/engine/database/database_helper.c` … | `src/app/engine/config/database_cfg.c`, `src/app/engine/config/database_cfg.h` | 2 | `docs/software/modules/engine/database/database.rst` |
| `engine/diag` | `src/app/engine/diag/cbs/diag_cbs.h`, `src/app/engine/diag/cbs/diag_cbs_aerosol-sensor.c`, `src/app/engine/diag/cbs/diag_cbs_afe.c` … | `src/app/engine/config/diag_cfg.c`, `src/app/engine/config/diag_cfg.h` | 1 | `docs/software/modules/engine/diag/diag.rst` |
| `engine/hw_info` | `src/app/engine/hw_info/master_info.c`, `src/app/engine/hw_info/master_info.h` | — | 1 | `docs/software/modules/engine/hw_info/hw_info.rst` |
| `engine/sys` | `src/app/engine/sys/reset.c`, `src/app/engine/sys/reset.h`, `src/app/engine/sys/sys.c` … | `src/app/engine/config/sys_cfg.c`, `src/app/engine/config/sys_cfg.h` | 2 | `docs/software/modules/engine/sys/sys.rst` |
| `engine/sys_mon` | `src/app/engine/sys_mon/sys_mon.c`, `src/app/engine/sys_mon/sys_mon.h` | `src/app/engine/config/sys_mon_cfg.c`, `src/app/engine/config/sys_mon_cfg.h` | 1 | `docs/software/modules/engine/sys_mon/sys_mon.rst` |
| `task/ftask` | `src/app/task/ftask/freertos/ftask_freertos.c`, `src/app/task/ftask/ftask.c`, `src/app/task/ftask/ftask.h` | `src/app/task/config/ftask_cfg.c`, `src/app/task/config/ftask_cfg.h` | 2 | `docs/software/modules/task/ftask/ftask.rst` |
| `task/os` | `src/app/task/os/freertos/os_freertos.c`, `src/app/task/os/freertos/os_freertos_config-validation.h`, `src/app/task/os/os.c` … | — | 1 | `docs/software/modules/task/os/os.rst` |
| `task/timer` | `src/app/task/timer/timer.c`, `src/app/task/timer/timer.h` | — | 1 | `docs/software/modules/task/timer/timer.rst` |

## Corpus Implementation Mapping

### `FB2-SW-DSN-000001` (as_is) — Design: AFE Driver Architecture (LTC Family)

| Source file | Symbol | Status |
|---|---|---|
| `src/app/driver/afe/ltc/common/ltc_afe.c` | `LTC_AFE_TriggerMeasurement` | `implemented` |
| `src/app/driver/afe/ltc/common/ltc_afe_dma.c` | `LTC_AFE_DMA_RxCallback` | `implemented` |
| `src/app/driver/afe/ltc/common/ltc_pec.c` | `LTC_PEC_Calculate` | `implemented` |
| `src/app/driver/afe/ltc/6813-1/ltc_6813-1.c` | `LTC_6813_ReadVoltages` | `implemented` |

### `FB2-SW-DSN-000002` (as_is) — Design: SOA Voltage Monitoring Module

| Source file | Symbol | Status |
|---|---|---|
| `src/app/application/soa/soa.c` | `SOA_CheckVoltageLimits` | `implemented` |
| `src/app/application/soa/soa.c` | `SOA_CheckCurrentLimits` | `implemented` |
| `src/app/application/soa/soa.c` | `SOA_CheckTemperatureLimits` | `implemented` |
| `src/app/engine/diag/cbs/diag_cbs_voltage.c` | `DIAG_CBS_Voltage` | `implemented` |

### `FB2-SW-DSN-000003` (as_is) — Design: Contactor State Machine

| Source file | Symbol | Status |
|---|---|---|
| `src/app/driver/contactor/contactor.c` | `CONTACTOR_StateMachine` | `implemented` |
| `src/app/driver/contactor/contactor.c` | `CONTACTOR_CheckFeedback` | `implemented` |
| `src/app/driver/sbc/fs8x_driver/sbc_fs8x.c` | `SBC_FS8X_SetContactor` | `implemented` |
| `src/app/engine/diag/cbs/diag_cbs_contactor.c` | `DIAG_CBS_Contactor` | `implemented` |

### `FB2-SW-DSN-000001` (synthetic_reference) — Design: AFE Driver Architecture (LTC Family)

| Source file | Symbol | Status |
|---|---|---|
| `src/app/driver/afe/ltc/common/ltc_afe.c` | `LTC_AFE_TriggerMeasurement` | `implemented` |
| `src/app/driver/afe/ltc/common/ltc_afe_dma.c` | `LTC_AFE_DMA_RxCallback` | `implemented` |
| `src/app/driver/afe/ltc/common/ltc_pec.c` | `LTC_PEC_Calculate` | `implemented` |
| `src/app/driver/afe/ltc/6813-1/ltc_6813-1.c` | `LTC_6813_ReadVoltages` | `implemented` |

### `FB2-SW-DSN-000002` (synthetic_reference) — Design: SOA Voltage Monitoring Module

| Source file | Symbol | Status |
|---|---|---|
| `src/app/application/soa/soa.c` | `SOA_CheckVoltageLimits` | `implemented` |
| `src/app/application/soa/soa.c` | `SOA_CheckCurrentLimits` | `implemented` |
| `src/app/application/soa/soa.c` | `SOA_CheckTemperatureLimits` | `implemented` |
| `src/app/engine/diag/cbs/diag_cbs_voltage.c` | `DIAG_CBS_Voltage` | `implemented` |

### `FB2-SW-DSN-000003` (synthetic_reference) — Design: Contactor State Machine

| Source file | Symbol | Status |
|---|---|---|
| `src/app/driver/contactor/contactor.c` | `CONTACTOR_StateMachine` | `implemented` |
| `src/app/driver/contactor/contactor.c` | `CONTACTOR_CheckFeedback` | `implemented` |
| `src/app/driver/sbc/fs8x_driver/sbc_fs8x.c` | `SBC_FS8X_SetContactor` | `implemented` |
| `src/app/engine/diag/cbs/diag_cbs_contactor.c` | `DIAG_CBS_Contactor` | `implemented` |

### `FB2-SW-DSN-000004` (synthetic_reference) — Detailed Design: LTC 6813-1 AFE measurement driver - internal units, PEC contrac...

| Source file | Symbol | Status |
|---|---|---|
| `src/app/driver/afe/ltc/api/ltc_afe.c` | `AFE_StartMeasurement` | `implemented` |
| `src/app/driver/afe/ltc/api/ltc_afe.c` | `AFE_RequestTemperatureRead` | `implemented` |
| `src/app/driver/afe/ltc/api/ltc_afe.c` | `AFE_RequestBalancingFeedbackRead` | `implemented` |
| `src/app/driver/afe/ltc/api/ltc_afe.c` | `AFE_RequestOpenWireCheck` | `implemented` |
| `src/app/driver/afe/ltc/api/ltc_afe.c` | `AFE_TriggerIc` | `implemented` |
| `src/app/driver/afe/ltc/6813-1/ltc_6813-1.c` | `LTC_Trigger` | `implemented` |
| `src/app/driver/afe/ltc/6813-1/ltc_6813-1.c` | `LTC_CheckPec` | `implemented` |
| `src/app/driver/afe/ltc/6813-1/ltc_6813-1.c` | `LTC_StateTransition` | `implemented` |
| `src/app/driver/afe/ltc/6813-1/ltc_6813-1.c` | `LTC_CondBasedStateTransition` | `implemented` |
| `src/app/driver/afe/ltc/6813-1/ltc_6813-1.c` | `LTC_SaveVoltages` | `implemented` |
| `src/app/driver/afe/ltc/6813-1/ltc_6813-1.c` | `LTC_ResetErrorTable` | `implemented` |
| `src/app/driver/afe/ltc/6813-1/ltc_6813-1.c` | `ltc_RxPecBuffer` | `implemented` |
| `src/app/driver/afe/ltc/6813-1/ltc_6813-1.c` | `ltc_TxPecBuffer` | `implemented` |
| `src/app/driver/afe/ltc/6813-1/ltc_6813-1.c` | `ltc_errorTable` | `implemented` |
| `src/app/driver/afe/ltc/common/ltc_pec.c` | `LTC_CalculatePec15` | `implemented` |
| `src/app/driver/afe/ltc/common/ltc_pec.h` | `LTC_PEC_PRECOMPUTED_TABLE_SIZE` | `implemented` |
| `src/app/driver/afe/ltc/common/ltc_pec.h` | `LTC_PEC15_MASK` | `implemented` |
| `src/app/driver/afe/ltc/common/ltc_afe_dma.c` | `AFE_DmaCallback` | `implemented` |
| `src/app/driver/afe/ltc/common/ltc_afe_dma.c` | `AFE_IsTransmitOngoing` | `implemented` |
| `src/app/driver/afe/ltc/common/ltc_afe_dma.c` | `AFE_SetTransmitOngoing` | `implemented` |
| `src/app/driver/afe/ltc/common/ltc_defs.h` | `LTC_DATA_SIZE_IN_BYTES` | `implemented` |
| `src/app/driver/afe/ltc/common/config/ltc_cfg.h` | `LTC_N_BYTES_FOR_DATA_TRANSMISSION` | `implemented` |
| `src/app/driver/afe/ltc/6813-1/config/ltc_6813-1_cfg.h` | `LTC_TRANSMISSION_TIMEOUT` | `implemented` |
| `src/app/driver/afe/ltc/6813-1/config/ltc_6813-1_cfg.h` | `LTC_DISCARD_PEC` | `implemented` |
| `src/app/driver/afe/ltc/6813-1/config/ltc_6813-1_cfg.h` | `LTC_NUMBER_OF_CELL_VOLTAGES_PER_REGISTER` | `implemented` |
| `src/app/driver/meas/meas.c` | `MEAS_Control` | `implemented` |
| `src/app/task/config/ftask_cfg.h` | `FTSK_TASK_AFE_STACK_SIZE_IN_BYTES` | `implemented` |
| `src/app/task/config/ftask_cfg.h` | `FTSK_TASK_AFE_CYCLE_TIME` | `implemented` |
| `tools/waf-tools/bms_config_validator.py` | `afe_driver_type` | `implemented` |
| `src/app/driver/afe/api/afe_plausibility.h` | `AFE_PlausibilityCheckVoltageMeasurementRange` | `not_in_source` |

### `FB2-SW-DSN-000005` (synthetic_reference) — Detailed Design: SOA monitoring - tiered limit evaluation, limit-provider split,...

| Source file | Symbol | Status |
|---|---|---|
| `src/app/application/soa/soa.c` | `SOA_CheckVoltages` | `implemented` |
| `src/app/application/soa/soa.c` | `SOA_CheckTemperatures` | `implemented` |
| `src/app/application/soa/soa.c` | `SOA_CheckCurrent` | `implemented` |
| `src/app/application/soa/soa.c` | `SOA_CheckSlaveTemperatures` | `not_in_source` |
| `src/app/application/soa/soa.h` | `SOA_CheckVoltages` | `implemented` |
| `src/app/application/config/soa_cfg.c` | `SOA_IsPackCurrentLimitViolated` | `implemented` |
| `src/app/application/config/soa_cfg.c` | `SOA_IsStringCurrentLimitViolated` | `implemented` |
| `src/app/application/config/soa_cfg.c` | `SOA_IsCellCurrentLimitViolated` | `implemented` |
| `src/app/application/config/soa_cfg.c` | `SOA_IsCurrentOnOpenString` | `implemented` |
| `src/app/application/soa/soa.c` | `DIAG_Handler` | `implemented` |
| `src/app/application/bms/bms.c` | `BMS_Trigger` | `implemented` |
| `src/app/application/bms/bms.c` | `BMS_GetCurrentFlowDirection` | `implemented` |
| `src/app/task/config/ftask_cfg.c` | `FTSK_RunUserCodeCyclic10ms` | `implemented` |
| `src/app/engine/diag/diag.h` | `DIAG_HANDLER_RETURN_ERR_OCCURRED` | `implemented` |
| `src/app/engine/diag/diag.h` | `extern DIAG_RETURNTYPE_e DIAG_Handler` | `implemented` |
| `src/app/engine/config/database_cfg.h` | `invalidStringCurrent` | `implemented` |
| `src/app/engine/config/database_cfg.h` | `invalidPackCurrent` | `implemented` |
| `src/app/application/config/battery_system_cfg.h` | `BS_NR_OF_STRINGS` | `implemented` |
| `src/app/application/config/battery_system_cfg.h` | `BS_REST_CURRENT_mA` | `implemented` |
| `src/app/application/config/battery_system_cfg.h` | `BS_MAXIMUM_STRING_CURRENT_mA` | `implemented` |
| `src/app/application/config/battery_system_cfg.h` | `BS_MAXIMUM_PACK_CURRENT_mA` | `implemented` |
| `src/app/application/config/battery_system_cfg.h` | `BS_NR_OF_PARALLEL_CELLS_PER_CELL_BLOCK` | `implemented` |
| `src/app/application/config/battery_system_cfg.h` | `BS_POSITIVE_DISCHARGE_CURRENT` | `implemented` |
| `src/app/application/config/battery_cell_cfg.h` | `BC_VOLTAGE_MAX_MOL_mV` | `implemented` |
| `src/app/application/config/battery_cell_cfg.h` | `BC_VOLTAGE_DEEP_DISCHARGE_mV` | `implemented` |
| `src/app/application/config/battery_cell_cfg.h` | `BC_TEMPERATURE_MAX_DISCHARGE_MSL_ddegC` | `implemented` |
| `src/app/application/config/battery_cell_cfg.h` | `BC_TEMPERATURE_MIN_CHARGE_MOL_ddegC` | `implemented` |
| `src/app/application/config/battery_cell_cfg.h` | `BC_CURRENT_MAX_CHARGE_MSL_mA` | `implemented` |

### `FB2-SW-DSN-000006` (synthetic_reference) — Detailed Design: contactor actuation and auxiliary feedback - registry, command/...

| Source file | Symbol | Status |
|---|---|---|
| `src/app/driver/contactor/contactor.c` | `CONT_CheckFeedback` | `implemented` |
| `src/app/driver/contactor/contactor.c` | `CONT_GetFeedbackOfAllContactors` | `implemented` |
| `src/app/driver/contactor/contactor.c` | `CONT_InitializationCheckOfContactorRegistry` | `implemented` |
| `src/app/driver/contactor/contactor.c` | `CONT_OpenContactor` | `implemented` |
| `src/app/driver/contactor/contactor.c` | `CONT_CloseContactor` | `implemented` |
| `src/app/driver/contactor/contactor.c` | `CONT_ClosePrecharge` | `implemented` |
| `src/app/driver/contactor/contactor.c` | `CONT_OpenPrecharge` | `implemented` |
| `src/app/driver/contactor/contactor.c` | `CONT_OpenAllPrechargeContactors` | `implemented` |
| `src/app/driver/contactor/contactor.c` | `CONT_OpenAllContactors` | `implemented` |
| `src/app/driver/contactor/contactor.c` | `CONT_GetContactorState` | `implemented` |
| `src/app/driver/contactor/contactor.c` | `CONT_Initialize` | `implemented` |
| `src/app/driver/contactor/contactor.c` | `TEST_CONT_InitializationCheckOfContactorRegistry` | `implemented` |
| `src/app/driver/contactor/contactor.c` | `FAS_ASSERT(FAS_TRAP)` | `implemented` |
| `src/app/driver/contactor/contactor.c` | `SPS_NR_OF_AVAILABLE_SPS_CHANNELS` | `implemented` |
| `src/app/driver/contactor/contactor.h` | `CONT_OpenContactor` | `implemented` |
| `src/app/driver/contactor/contactor.h` | `CONT_GetContactorState` | `implemented` |
| `src/app/driver/contactor/contactor.h` | `CONT_CheckFeedback` | `implemented` |
| `src/app/driver/config/contactor_cfg.h` | `cont_contactorStates` | `implemented` |
| `src/app/driver/config/contactor_cfg.h` | `CONT_CONTACTOR_INDEX` | `implemented` |
| `src/app/driver/config/contactor_cfg.h` | `CONT_FEEDBACK_NORMALLY_CLOSED` | `implemented` |
| `src/app/driver/config/contactor_cfg.h` | `CONT_BIDIRECTIONAL` | `implemented` |
| `src/app/driver/config/contactor_cfg.c` | `cont_contactorStates` | `implemented` |
| `src/app/driver/config/sps_cfg.h` | `SPS_NR_OF_AVAILABLE_SPS_CHANNELS` | `implemented` |
| `src/app/driver/config/sps_cfg.h` | `SPS_NR_OF_REQUIRED_CONTACTOR_CHANNELS` | `implemented` |
| `src/app/application/config/battery_system_cfg.h` | `BS_NR_OF_CONTACTORS` | `implemented` |
| `src/app/application/config/battery_system_cfg.h` | `BS_NR_OF_CONTACTORS_OUTSIDE_STRINGS` | `implemented` |
| `src/app/application/bms/bms.c` | `CONT_OpenAllContactors` | `implemented` |
| `src/app/application/bms/bms.c` | `BMS_Trigger` | `implemented` |
| `src/app/task/config/ftask_cfg.c` | `FTSK_RunUserCodeCyclic10ms` | `implemented` |

### Requirement → Design → Source → Test Chains

#### `FB2-SW-SWR-000001` (as_is)

- Design `FB2-SW-IMP-000001` implements `FB2-SW-SWR-000001` → sources: —
- Verifying test measures: `FB2-VER-TMS-000003`

#### `FB2-SW-SWR-000002` (as_is)

- Design `FB2-SW-IMP-000002` implements `FB2-SW-SWR-000002` → sources: —
- Verifying test measures: `FB2-VER-TMS-000001`

#### `FB2-SW-SWR-000003` (as_is)

- Design `FB2-SW-IMP-000003` implements `FB2-SW-SWR-000003` → sources: —
- Verifying test measures: `FB2-VER-TMS-000002`

#### `FB2-SW-SWR-000001` (synthetic_reference)

- Design `FB2-SW-IMP-000001` implements `FB2-SW-SWR-000001` → sources: —
- Verifying test measures: `FB2-VER-SQP-000001`, `FB2-VER-TMS-000003`, `FB2-VER-TMS-000007`

#### `FB2-SW-SWR-000002` (synthetic_reference)

- Design `FB2-SW-IMP-000002` implements `FB2-SW-SWR-000002` → sources: —
- Verifying test measures: `FB2-VER-SQP-000001`, `FB2-VER-TMS-000001`, `FB2-VER-TMS-000007`, `FB2-VER-TMS-000010`

#### `FB2-SW-SWR-000003` (synthetic_reference)

- Design `FB2-SW-IMP-000003` implements `FB2-SW-SWR-000003` → sources: —
- Verifying test measures: `FB2-VER-SQP-000001`, `FB2-VER-TMS-000002`, `FB2-VER-TMS-000007`

## Requirement-to-Test Coverage Matrix

One row per requirement artifact across FSR/TSR/SWR/management classes, both profiles. Statuses: COVERED-DIRECT (has `verifies` link), COVERED-INDIRECT (allocated child is verified), COVERED-EMBEDDED (TMS references requirement), UNCOVERED (explicit gap).

| Profile | Requirement | Type | Status | Direct verifies | Indirect (child ← test) | Verifying tests | Gap note |
|---|---|---|---|---|---|---|---|
| `as_is` | `FB2-HW-TSR-000001` | TSR | **COVERED-DIRECT** | `FB2-VER-TMS-000004` | — | `FB2-VER-TMS-000004` |  |
| `as_is` | `FB2-HW-TSR-000002` | TSR | **COVERED-DIRECT** | `FB2-VER-TMS-000004` | — | `FB2-VER-TMS-000004` |  |
| `as_is` | `FB2-HW-TSR-000003` | TSR | **COVERED-DIRECT** | `FB2-VER-TMS-000005` | — | `FB2-VER-TMS-000005` |  |
| `as_is` | `FB2-SAF-FSR-000001` | FSR | **COVERED-DIRECT** | `FB2-VER-TMS-000003` | `FB2-HW-TSR-000001`←FB2-VER-TMS-000004, `FB2-HW-TSR-000002`←FB2-VER-TMS-000004, `FB2-SW-SWR-000001`←FB2-VER-TMS-000003 | `FB2-VER-TMS-000003`, `FB2-VER-TMS-000004` |  |
| `as_is` | `FB2-SAF-FSR-000002` | FSR | **COVERED-DIRECT** | `FB2-VER-TMS-000001` | `FB2-SW-SWR-000002`←FB2-VER-TMS-000001 | `FB2-VER-TMS-000001` |  |
| `as_is` | `FB2-SAF-FSR-000003` | FSR | **COVERED-DIRECT** | `FB2-VER-TMS-000002` | `FB2-HW-TSR-000003`←FB2-VER-TMS-000005, `FB2-SW-SWR-000003`←FB2-VER-TMS-000002 | `FB2-VER-TMS-000002`, `FB2-VER-TMS-000005` |  |
| `as_is` | `FB2-SW-SWR-000001` | SWR | **COVERED-DIRECT** | `FB2-VER-TMS-000003` | — | `FB2-VER-TMS-000003` |  |
| `as_is` | `FB2-SW-SWR-000002` | SWR | **COVERED-DIRECT** | `FB2-VER-TMS-000001` | — | `FB2-VER-TMS-000001` |  |
| `as_is` | `FB2-SW-SWR-000003` | SWR | **COVERED-DIRECT** | `FB2-VER-TMS-000002` | — | `FB2-VER-TMS-000002` |  |
| `synthetic_reference` | `FB2-HW-TSR-000001` | TSR | **COVERED-DIRECT** | `FB2-VER-TMS-000003` | — | `FB2-VER-TMS-000003` |  |
| `synthetic_reference` | `FB2-HW-TSR-000002` | TSR | **COVERED-DIRECT** | `FB2-VER-TMS-000005` | — | `FB2-VER-TMS-000005` |  |
| `synthetic_reference` | `FB2-HW-TSR-000003` | TSR | **COVERED-DIRECT** | `FB2-VER-TMS-000006` | — | `FB2-VER-TMS-000006` |  |
| `synthetic_reference` | `FB2-HW-TSR-000004` | TSR | **COVERED-DIRECT** | `FB2-VER-TMS-000004` | — | `FB2-VER-TMS-000004` |  |
| `synthetic_reference` | `FB2-MAN-SCO-000001` | MGT | **COVERED-DIRECT** | `FB2-VER-TMS-000009` | — | `FB2-VER-TMS-000009` |  |
| `synthetic_reference` | `FB2-SAF-FSR-000001` | FSR | **COVERED-DIRECT** | `FB2-VER-TMS-000003`, `FB2-VER-TMS-000008`, `FB2-VER-TMS-000011` | `FB2-HW-TSR-000001`←FB2-VER-TMS-000003, `FB2-HW-TSR-000002`←FB2-VER-TMS-000005, `FB2-SW-SWR-000001`←FB2-VER-SQP-000001,FB2-VER-TMS-000003,FB2-VER-TMS-000007 | `FB2-VER-SQP-000001`, `FB2-VER-TMS-000003`, `FB2-VER-TMS-000005`, `FB2-VER-TMS-000007`, `FB2-VER-TMS-000008`, `FB2-VER-TMS-000011` |  |
| `synthetic_reference` | `FB2-SAF-FSR-000002` | FSR | **COVERED-DIRECT** | `FB2-VER-TMS-000001`, `FB2-VER-TMS-000008`, `FB2-VER-TMS-000011` | `FB2-SW-SWR-000002`←FB2-VER-SQP-000001,FB2-VER-TMS-000001,FB2-VER-TMS-000007,FB2-VER-TMS-000010 | `FB2-VER-SQP-000001`, `FB2-VER-TMS-000001`, `FB2-VER-TMS-000007`, `FB2-VER-TMS-000008`, `FB2-VER-TMS-000010`, `FB2-VER-TMS-000011` |  |
| `synthetic_reference` | `FB2-SAF-FSR-000003` | FSR | **COVERED-DIRECT** | `FB2-VER-TMS-000002`, `FB2-VER-TMS-000008`, `FB2-VER-TMS-000011` | `FB2-HW-TSR-000003`←FB2-VER-TMS-000006, `FB2-SW-SWR-000003`←FB2-VER-SQP-000001,FB2-VER-TMS-000002,FB2-VER-TMS-000007 | `FB2-VER-SQP-000001`, `FB2-VER-TMS-000002`, `FB2-VER-TMS-000006`, `FB2-VER-TMS-000007`, `FB2-VER-TMS-000008`, `FB2-VER-TMS-000011` |  |
| `synthetic_reference` | `FB2-SAF-FSR-000004` | FSR | **COVERED-DIRECT** | `FB2-VER-TMS-000004`, `FB2-VER-TMS-000008`, `FB2-VER-TMS-000011` | `FB2-HW-TSR-000004`←FB2-VER-TMS-000004 | `FB2-VER-TMS-000004`, `FB2-VER-TMS-000008`, `FB2-VER-TMS-000011` |  |
| `synthetic_reference` | `FB2-SAF-SEC-000001` | SEC | **COVERED-DIRECT** | `FB2-VER-TMS-000016` | — | `FB2-VER-TMS-000016` |  |
| `synthetic_reference` | `FB2-SAF-SEC-000002` | SEC | **COVERED-DIRECT** | `FB2-VER-TMS-000017` | — | `FB2-VER-TMS-000017` |  |
| `synthetic_reference` | `FB2-SAF-SEC-000003` | SEC | **COVERED-DIRECT** | `FB2-VER-TMS-000018` | — | `FB2-VER-TMS-000018` |  |
| `synthetic_reference` | `FB2-SAF-SEC-000004` | SEC | **COVERED-DIRECT** | `FB2-VER-TMS-000019` | — | `FB2-VER-TMS-000019` |  |
| `synthetic_reference` | `FB2-SAF-SEC-000005` | SEC | **COVERED-DIRECT** | `FB2-VER-TMS-000020` | — | `FB2-VER-TMS-000020` |  |
| `synthetic_reference` | `FB2-SW-SIR-000001` | MGT | **UNCOVERED** | — | — | — | No direct, indirect, or embedded test coverage in corpus |
| `synthetic_reference` | `FB2-SW-SIR-000002` | MGT | **COVERED-DIRECT** | `FB2-SW-SIR-000005` | — | `FB2-SW-SIR-000005` |  |
| `synthetic_reference` | `FB2-SW-SIR-000003` | MGT | **COVERED-DIRECT** | `FB2-SW-SIR-000005` | — | `FB2-SW-SIR-000005` |  |
| `synthetic_reference` | `FB2-SW-SIR-000004` | MGT | **COVERED-DIRECT** | `FB2-SW-SIR-000005` | — | `FB2-SW-SIR-000005` |  |
| `synthetic_reference` | `FB2-SW-SIR-000005` | MGT | **UNCOVERED** | — | — | — | No direct, indirect, or embedded test coverage in corpus |
| `synthetic_reference` | `FB2-SW-SIR-000006` | MGT | **UNCOVERED** | — | — | — | No direct, indirect, or embedded test coverage in corpus |
| `synthetic_reference` | `FB2-SW-SWR-000001` | SWR | **COVERED-DIRECT** | `FB2-VER-SQP-000001`, `FB2-VER-TMS-000003`, `FB2-VER-TMS-000007` | — | `FB2-VER-SQP-000001`, `FB2-VER-TMS-000003`, `FB2-VER-TMS-000007` |  |
| `synthetic_reference` | `FB2-SW-SWR-000002` | SWR | **COVERED-DIRECT** | `FB2-VER-SQP-000001`, `FB2-VER-TMS-000001`, `FB2-VER-TMS-000007`, `FB2-VER-TMS-000010` | — | `FB2-VER-SQP-000001`, `FB2-VER-TMS-000001`, `FB2-VER-TMS-000007`, `FB2-VER-TMS-000010` |  |
| `synthetic_reference` | `FB2-SW-SWR-000003` | SWR | **COVERED-DIRECT** | `FB2-VER-SQP-000001`, `FB2-VER-TMS-000002`, `FB2-VER-TMS-000007` | — | `FB2-VER-SQP-000001`, `FB2-VER-TMS-000002`, `FB2-VER-TMS-000007` |  |
| `synthetic_reference` | `FB2-SYS-SYR-000001` | SYR | **COVERED-DIRECT** | `FB2-VER-TMS-000021`, `FB2-VER-TMS-000022` | `FB2-HW-TSR-000001`←FB2-VER-TMS-000003, `FB2-SW-SWR-000001`←FB2-VER-SQP-000001,FB2-VER-TMS-000003,FB2-VER-TMS-000007 | `FB2-VER-SQP-000001`, `FB2-VER-TMS-000003`, `FB2-VER-TMS-000007`, `FB2-VER-TMS-000021`, `FB2-VER-TMS-000022` |  |
| `synthetic_reference` | `FB2-SYS-SYR-000002` | SYR | **COVERED-DIRECT** | `FB2-VER-TMS-000023`, `FB2-VER-TMS-000024` | `FB2-HW-TSR-000001`←FB2-VER-TMS-000003, `FB2-SW-SWR-000001`←FB2-VER-SQP-000001,FB2-VER-TMS-000003,FB2-VER-TMS-000007, `FB2-SW-SWR-000002`←FB2-VER-SQP-000001,FB2-VER-TMS-000001,FB2-VER-TMS-000007,FB2-VER-TMS-000010 | `FB2-VER-SQP-000001`, `FB2-VER-TMS-000001`, `FB2-VER-TMS-000003`, `FB2-VER-TMS-000007`, `FB2-VER-TMS-000010`, `FB2-VER-TMS-000023`, `FB2-VER-TMS-000024` |  |
| `synthetic_reference` | `FB2-SYS-SYR-000003` | SYR | **COVERED-DIRECT** | `FB2-VER-TMS-000025` | `FB2-HW-TSR-000003`←FB2-VER-TMS-000006, `FB2-HW-TSR-000004`←FB2-VER-TMS-000004, `FB2-SW-SWR-000003`←FB2-VER-SQP-000001,FB2-VER-TMS-000002,FB2-VER-TMS-000007 | `FB2-VER-SQP-000001`, `FB2-VER-TMS-000002`, `FB2-VER-TMS-000004`, `FB2-VER-TMS-000006`, `FB2-VER-TMS-000007`, `FB2-VER-TMS-000025` |  |
| `synthetic_reference` | `FB2-SYS-SYR-000004` | SYR | **COVERED-DIRECT** | `FB2-VER-TMS-000026` | `FB2-HW-TSR-000003`←FB2-VER-TMS-000006, `FB2-SW-SWR-000003`←FB2-VER-SQP-000001,FB2-VER-TMS-000002,FB2-VER-TMS-000007 | `FB2-VER-SQP-000001`, `FB2-VER-TMS-000002`, `FB2-VER-TMS-000006`, `FB2-VER-TMS-000007`, `FB2-VER-TMS-000026` |  |
| `synthetic_reference` | `FB2-SYS-SYR-000005` | SYR | **COVERED-DIRECT** | `FB2-VER-TMS-000027` | `FB2-HW-TSR-000004`←FB2-VER-TMS-000004 | `FB2-VER-TMS-000004`, `FB2-VER-TMS-000027` |  |
| `synthetic_reference` | `FB2-SYS-SYR-000006` | SYR | **COVERED-DIRECT** | `FB2-VER-TMS-000028` | `FB2-HW-TSR-000002`←FB2-VER-TMS-000005, `FB2-SW-SWR-000001`←FB2-VER-SQP-000001,FB2-VER-TMS-000003,FB2-VER-TMS-000007 | `FB2-VER-SQP-000001`, `FB2-VER-TMS-000003`, `FB2-VER-TMS-000005`, `FB2-VER-TMS-000007`, `FB2-VER-TMS-000028` |  |
| `synthetic_reference` | `FB2-SYS-SYR-000007` | SYR | **COVERED-DIRECT** | `FB2-VER-TMS-000016`, `FB2-VER-TMS-000017`, `FB2-VER-TMS-000018`, `FB2-VER-TMS-000019`, `FB2-VER-TMS-000020` | `FB2-HW-TSR-000002`←FB2-VER-TMS-000005, `FB2-SW-SWR-000001`←FB2-VER-SQP-000001,FB2-VER-TMS-000003,FB2-VER-TMS-000007 | `FB2-VER-SQP-000001`, `FB2-VER-TMS-000003`, `FB2-VER-TMS-000005`, `FB2-VER-TMS-000007`, `FB2-VER-TMS-000016`, `FB2-VER-TMS-000017`, `FB2-VER-TMS-000018`, `FB2-VER-TMS-000019`, `FB2-VER-TMS-000020` |  |
| `synthetic_reference` | `FB2-SYS-SYR-000008` | SYR | **COVERED-DIRECT** | `FB2-VER-TMS-000016`, `FB2-VER-TMS-000017`, `FB2-VER-TMS-000018`, `FB2-VER-TMS-000019`, `FB2-VER-TMS-000020` | `FB2-SAF-SEC-000001`←FB2-VER-TMS-000016, `FB2-SAF-SEC-000004`←FB2-VER-TMS-000019, `FB2-SW-SWR-000003`←FB2-VER-SQP-000001,FB2-VER-TMS-000002,FB2-VER-TMS-000007 | `FB2-VER-SQP-000001`, `FB2-VER-TMS-000002`, `FB2-VER-TMS-000007`, `FB2-VER-TMS-000016`, `FB2-VER-TMS-000017`, `FB2-VER-TMS-000018`, `FB2-VER-TMS-000019`, `FB2-VER-TMS-000020` |  |

### Coverage Summary

- **Total requirement artifacts**: 40
- **Covered (any status)**: 37 (92%)
- **UNCOVERED**: 3
  - `FB2-SW-SIR-000001` (`synthetic_reference`)
  - `FB2-SW-SIR-000005` (`synthetic_reference`)
  - `FB2-SW-SIR-000006` (`synthetic_reference`)

3 requirement artifact(s) remain UNCOVERED and that is the honest corpus state; the gaps are tracked by review dispositions and by the gap report. No coverage is fabricated.

## Change Impact Mapping

The corpus holds **3 canonical change records** (`FB2-MAN-CHG-*`) for the synthetic-reference project. Each is the change-management record of record for one change request and carries the full chain: trigger, impact analysis, decision, the artifacts moved to a new revision, the links placed under suspicion, the required updates, the re-verification selection, and the planned post-change baseline.

They are **change-management records, not verification results**. None of the three has been executed, none of the revisions it names has been raised, and none of the post-change baselines it names exists. A row below is a statement of intended work, not a report of work done.

These are not the change-lifecycle *demonstrations*. The demonstrations are `FB2-SCN-CHG-000001`, `FB2-SCN-CHG-000002` and `FB2-SCN-CHG-000003` under `docs/artifacts/scenarios/change-lifecycles/`, which exist to exercise the corpus scenario gate and are checked for structural completeness only. The records below describe the same three subjects as engineering work; the two sets are deliberately separate artifacts with different jobs, and each record states its own relationship to its demonstration in its `relationship_to_scenario_fixture` field.

| Record | Change type | Trigger class | Affected artifacts | New revisions | Suspect links | Re-verification | Post-change baseline |
|---|---|---|---|---|---|---|---|
| `FB2-MAN-CHG-000001` (synthetic_reference) | `safety_threshold` | external_mandatory | `FB2-SAF-FSR-000002`, `FB2-SAF-HAZ-000001`, `FB2-HW-TSR-000001`, `FB2-SW-DSN-000002`, `FB2-VER-TMS-000001` | `FB2-SAF-FSR-000002` 1→2, `FB2-SAF-HAZ-000001` 1→2, `FB2-HW-TSR-000001` 1→2, `FB2-SW-DSN-000002` 1→2, `FB2-VER-TMS-000001` 1→2 | `FB2-LNK-SAF-000001`, `FB2-LNK-SAF-000003`, `FB2-LNK-SAF-000009`, `FB2-LNK-SAF-000012`, `FB2-LNK-SAF-000022`, `FB2-LNK-SAF-000023`, `FB2-LNK-SAF-000033` | `FB2-VER-TMS-000001`, `FB2-VER-TMS-000002`, `FB2-VER-TMS-000003` | `BAS-REF-002` |
| `FB2-MAN-CHG-000002` (synthetic_reference) | `hsi_interface` | external_mandatory | `FB2-SYS-HSI-000001`, `FB2-HW-TSR-000001`, `FB2-HW-TSR-000002`, `FB2-SW-SWR-000001`, `FB2-SW-DSN-000001`, `FB2-VER-TMS-000003`, `FB2-VER-TMS-000005` | `FB2-SYS-HSI-000001` 1→2, `FB2-HW-TSR-000001` 1→2, `FB2-HW-TSR-000002` 1→2, `FB2-SW-SWR-000001` 1→2, `FB2-SW-DSN-000001` 1→2, `FB2-VER-TMS-000003` 1→2, `FB2-VER-TMS-000005` 1→2 | `FB2-LNK-SAF-000005`, `FB2-LNK-SAF-000006`, `FB2-LNK-SAF-000008`, `FB2-LNK-SAF-000011`, `FB2-LNK-SAF-000027`, `FB2-LNK-SAF-000028`, `FB2-LNK-SAF-000031` | `FB2-VER-TMS-000003`, `FB2-VER-TMS-000005`, `FB2-VER-TMS-000001`, `FB2-VER-TMS-000002` | `BAS-REF-003` |
| `FB2-MAN-CHG-000003` (synthetic_reference) | `software_behavior` | internal_defect | `FB2-SAF-FSR-000002`, `FB2-SW-DSN-000002`, `FB2-SW-SWR-000002`, `FB2-VER-TMS-000001` | `FB2-SAF-FSR-000002` 1→2, `FB2-SW-SWR-000002` 1→2, `FB2-VER-TMS-000001` 1→2 | `FB2-LNK-SAF-000009`, `FB2-LNK-SAF-000012`, `FB2-LNK-SAF-000022`, `FB2-LNK-SAF-000023`, `FB2-LNK-SAF-000033` | `FB2-VER-TMS-000001`, `FB2-VER-TMS-000002` | `BAS-REF-004` |

### Suspect Links

`suspect_links` names links whose endpoint revisions or whose claims the change puts in question. The baseline link registry still records `change_suspect_status: false` on every one of them, and that is the correct state: the decisions below are fictional workflow outcomes, no affected artifact has been revised, and no post-change baseline exists. The flag becomes true as part of establishing the post-change baseline, at which point the registry flag and the record's suspect list must agree. Note that all of these links have existing endpoints at existing revisions, so no dangling-endpoint check will ever flag them - they are the links that survive a change unnoticed.

| Record | Link | Relation | Endpoints | Why it is suspect |
|---|---|---|---|---|
| `FB2-MAN-CHG-000001` | `FB2-LNK-SAF-000001` | `mitigates` | FB2-SAF-SGO-000001 -> FB2-SAF-HAZ-000001 | The goal mitigates the hazard by making contactors open on a confirmed limit violation. The mechanism is unchanged, but the value at which it fires moves, so the goal's adequacy argument is re-argued at the new margin (150 mV instead of 100 mV to the FB2-ASM-002 boundary). Suspect means 'the reasoning must be re-shown'... |
| `FB2-MAN-CHG-000001` | `FB2-LNK-SAF-000003` | `refines` | FB2-SAF-FSR-000002 -> FB2-SAF-SGO-000001 | The FSR's derivation from the goal rests on detecting an overvoltage within the hazard's operational situation. The FSR statement changes (debounce count), so the refinement must be re-derived rather than inherited. |
| `FB2-MAN-CHG-000001` | `FB2-LNK-SAF-000009` | `allocated_to` | FB2-SW-SWR-000002 -> FB2-SAF-FSR-000002 | The software requirement hard-codes both the 4.2 V ceiling and the 2-consecutive debounce in its own statement. The allocation is by statement, so once the FSR says 3, this link asserts an allocation to text that no longer says what the FSR says. The link's endpoints are both unchanged, which is exactly why it is easy ... |
| `FB2-MAN-CHG-000001` | `FB2-LNK-SAF-000012` | `implements` | FB2-SW-DSN-000002 -> FB2-SW-SWR-000002 | The design's default debounce count is the number this change moves. An implements link whose design still says 2 while the requirement says 3 is a live claim that the design does not satisfy the requirement. |
| `FB2-MAN-CHG-000001` | `FB2-LNK-SAF-000022` | `verifies` | FB2-VER-TMS-000001 -> FB2-SAF-FSR-000002 | The only direct verifies link to the ASIL D limit-monitoring requirement, and the test stimulus names the old ceiling. The link currently asserts coverage that the stimulus no longer provides. |
| `FB2-MAN-CHG-000001` | `FB2-LNK-SAF-000023` | `verifies` | FB2-VER-TMS-000001 -> FB2-SW-SWR-000002 | Same test, second target. The software requirement duplicates the ceiling and debounce count in its own text, so the test must be re-checked against both targets, not one. |
| `FB2-MAN-CHG-000001` | `FB2-LNK-SAF-000033` | `result_of` | FB2-VER-EXE-000001 -> FB2-VER-TMS-000001 | The execution record is the evidence that the verifies links above rested on. If the measure changes, the result is no longer a result of the new measure; this is the link that carries the evidence invalidation. |
| `FB2-MAN-CHG-000002` | `FB2-LNK-SAF-000005` | `allocated_to` | FB2-HW-TSR-000001 -> FB2-SAF-FSR-000001 | The accuracy requirement is the hardware element that carries the ASIL D acquisition requirement. After the migration the FSR is satisfied by two requirements rather than one, and the link asserts that one requirement is its allocation. The allocation is incomplete, not wrong, and incompleteness in an allocation is the... |
| `FB2-MAN-CHG-000002` | `FB2-LNK-SAF-000006` | `allocated_to` | FB2-HW-TSR-000002 -> FB2-SAF-FSR-000001 | Same incompleteness, and more sharply: the requirement being allocated is entirely about an isoSPI link that the new front end does not have. After this change, asserting that HW-TSR-000002 alone covers the ASIL D acquisition requirement would be false for the new configuration. |
| `FB2-MAN-CHG-000002` | `FB2-LNK-SAF-000008` | `allocated_to` | FB2-SW-SWR-000001 -> FB2-SAF-FSR-000001 | The software requirement is the element that actually enforces 'no database write without validation' for the acquisition path. Two drivers means two enforcement points, and a single allocated_to link does not say which driver enforces it in which configuration. |
| `FB2-MAN-CHG-000002` | `FB2-LNK-SAF-000011` | `implements` | FB2-SW-DSN-000001 -> FB2-SW-SWR-000001 | An implements link asserts that this design satisfies this requirement. After a second driver is raised, this link is only true of one of them, and a reader of the link alone cannot tell which. The corpus validator's dangling-endpoint check will not catch this: both endpoints still exist. |
| `FB2-MAN-CHG-000002` | `FB2-LNK-SAF-000027` | `verifies` | FB2-VER-TMS-000003 -> FB2-SW-SWR-000001 | The plausibility test verifies the driver requirement. Its stimulus was derived from the retained front end's error budget, so after the migration it verifies the requirement for a configuration it no longer represents. |
| `FB2-MAN-CHG-000002` | `FB2-LNK-SAF-000028` | `verifies` | FB2-VER-TMS-000003 -> FB2-HW-TSR-000001 | Same test, hardware target. The 4900 mV implausibility case sits far outside both devices' ranges, so this link can be satisfied by a test that discriminates nothing between them. |
| `FB2-MAN-CHG-000002` | `FB2-LNK-SAF-000031` | `verifies` | FB2-VER-TMS-000005 -> FB2-HW-TSR-000002 | The only direct verification of the communication-integrity requirement, and the injection mechanism is tied to the isolated link's framing. A pass after the migration would be evidence about the harness. |
| `FB2-MAN-CHG-000003` | `FB2-LNK-SAF-000009` | `allocated_to` | FB2-SW-SWR-000002 -> FB2-SAF-FSR-000002 | The allocation is between two requirements that are both being clarified in the same way, and today they are clear in the same way: neither mentions the reset. An allocation between two identically incomplete requirements is internally consistent and externally wrong, which is the hardest kind of traceability defect to... |
| `FB2-MAN-CHG-000003` | `FB2-LNK-SAF-000012` | `implements` | FB2-SW-DSN-000002 -> FB2-SW-SWR-000002 | This is the link that should have caught the defect and did not. The design specifies the reset action; the requirement does not mention it; the implementation does not perform it. The link asserts the design implements the requirement, which was true, while the design also specified something the requirement never ask... |
| `FB2-MAN-CHG-000003` | `FB2-LNK-SAF-000022` | `verifies` | FB2-VER-TMS-000001 -> FB2-SAF-FSR-000002 | The link asserts that the requirement is verified. It was verified only on the confirmation path, and the requirement's acceptance criteria contain nothing about recovery, so the link asserted more coverage than the test provided. This is the specific reason a behavioural defect reached a baselined design: the link exi... |
| `FB2-MAN-CHG-000003` | `FB2-LNK-SAF-000023` | `verifies` | FB2-VER-TMS-000001 -> FB2-SW-SWR-000002 | The same measure against the software requirement, and therefore the same overstatement of coverage. Both verifies links must be re-affirmed together or the requirement is left half-verified, which is worse than leaving both suspect. |
| `FB2-MAN-CHG-000003` | `FB2-LNK-SAF-000033` | `result_of` | FB2-VER-EXE-000001 -> FB2-VER-TMS-000001 | The execution evidence rests on a measure that cannot express the defect. It is therefore not evidence that the behaviour is correct; it is evidence that the measure was run. Keeping it as live coverage is how a defect survives a passing test suite. |

### Decision and Approval State

| Record | Decision id | Decision maker | Disposition | Approvals recorded | Re-verification executed |
|---|---|---|---|---|---|
| `FB2-MAN-CHG-000001` | `FB2-CHG-REF-000001` | change_control_board chair, fictional role identity 'A. Renner' (synthetic scenario character; not a... | `approved` | 0 of 5 | no |
| `FB2-MAN-CHG-000002` | `FB2-CHG-REF-000002` | change_control_board chair, fictional role identity 'A. Renner' (synthetic scenario character; not a... | `partial` | 0 of 7 | no |
| `FB2-MAN-CHG-000003` | `FB2-CHG-REF-000003` | change_control_board chair, fictional role identity 'A. Renner' (synthetic scenario character; not a... | `approved` | 0 of 4 | no |

Every record carries `profile: synthetic_reference`, `origin: synthetic`, `human_approval_status: pending`, `production_authorized: false` and `product_verification_credit: false`. Each `decision_maker` is a fictional role identity in the synthetic project and each `disposition` is a `synthetic_decision` in the sense of `governance/corpus-policy.json` (`synthetic_decision:{fictional_role}:{decision_id}`): not a human approval, not a foxBMS maintainer decision, and not a SoftwareDevLabs decision. All three records are `implementation_status: not_in_source`, and no file under `src/`, `tests/`, `conf/` or `wscript` is touched by them. No row in this section asserts that any change was made, approved or verified in any real project, and no row asserts a measured test result.

### Corpus-Consistency Notes

Three slots in these records are empty by schema rather than by omission, and the reasoning is recorded in the records themselves so the emptiness is not read as an incomplete analysis:

- `impact_analysis.affected_reviews` is empty in all three. The change schema admits only ids matching `^FB2-REV-[A-Z]{2,4}-[0-9]{6}$`, i.e. a review id carrying a two-to-four letter type segment. The corpus contains exactly one review artifact, `FB2-REV-000001`, which has no such segment and belongs to the `as_is` profile as an automated review of the reconstructed foxBMS artifacts. There is therefore no review in the `synthetic_reference` profile for these changes to invalidate, and the review work they do require is enumerated in each record's `re_review_scope` field.
- `impact_analysis.affected_evidence` is empty in all three, for the same shape of reason: the schema admits only `^FB2-EVD-[A-Z]{2,4}-[0-9]{6}$` and no `FB2-EVD-` artifact exists in either profile. The executions these changes really do invalidate (`FB2-VER-EXE-000001`, and for `FB2-MAN-CHG-000002` also `FB2-VER-EXE-000003` and `FB2-VER-EXE-000005`) do exist in `synthetic_reference` and are named in each record's `evidence_invalidation` field instead.
- `FB2-PRM-000001` (parameter-registry entry), the `FB2-SRC-*` identifiers (source anchors) and `VAR-AFE-ADI-1830` (a variant-matrix row) all resolve, but as rows of registries rather than as artifacts with revisions and lifecycle states. A `changes` link pointed at any of them would dangle, so each is recorded in a typed sibling field of the record that concerns it. Several of them even satisfy the change schema's id pattern, which makes this the easiest category error in the corpus to commit.


---

*Generated: 2026-10-03T11:20:05Z — auto-generated from the machine-verifiable corpus. Regenerate with `python3 docs/artifacts/tools/render_spec_documents.py`.*
