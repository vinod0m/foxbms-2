# foxBMS 2 — Implementation Mapping Document

**Document Control**

| Field | Value |
|---|---|
| Project | foxBMS 2 — Battery Management System |
| Document | Implementation Mapping Document |
| Baseline | BAS-REF-001 (commit `308028fb`, tag `v1.11.0`) |
| Profiles | `as_is` (source-grounded) + `synthetic_reference` (hypothetical) |
| Corpus status | `synthetic_ready_with_limitations` |
| Generated | 2026-09-13T15:17:46Z |

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

### Requirement → Design → Source → Test Chains

`implements` / `verifies` / `result_of` link IDs in parentheses. `verifies` links target requirements, never DSNs. Upstream parent chain shared by all rows: `SGO-000001` `mitigates` `HAZ-000001` (`LNK-001`); `FSR-000001/002/003` `refines` `SGO-000001` (`LNK-002/003/004`); `FSR-000004` `refines` `SGO-000001` (`LNK-021`, `synthetic_reference` only).

#### Chains (`as_is`, test measures `source_grounded`)

- `FB2-SW-SWR-000001` ←implements— `FB2-SW-DSN-000001` (`FB2-LNK-SAF-000011`) → sources: `src/app/driver/afe/ltc/6813-1/ltc_6813-1.c`, `src/app/driver/afe/ltc/common/ltc_afe.c`, `src/app/driver/afe/ltc/common/ltc_afe_dma.c`, `src/app/driver/afe/ltc/common/ltc_pec.c` — allocation `SWR-000001` → `FSR-000001` (`LNK-008`); verified by `FB2-VER-TMS-000003` (`LNK-021/022`); execution: none recorded.
- `FB2-SW-SWR-000002` ←implements— `FB2-SW-DSN-000002` (`FB2-LNK-SAF-000012`) → sources: `src/app/application/soa/soa.c`, `src/app/engine/diag/cbs/diag_cbs_voltage.c` — allocation `SWR-000002` → `FSR-000002` (`LNK-009`); verified by `FB2-VER-TMS-000001` (`LNK-014/015`); execution `FB2-VER-EXE-000001` (`LNK-018`), `actual_host_run`, `pass` — hashes `sha256:placeholder`, `output_hashes` empty.
- `FB2-SW-SWR-000003` ←implements— `FB2-SW-DSN-000003` (`FB2-LNK-SAF-000013`) → sources: `src/app/driver/contactor/contactor.c`, `src/app/driver/sbc/fs8x_driver/sbc_fs8x.c`, `src/app/engine/diag/cbs/diag_cbs_contactor.c` — allocation `SWR-000003` → `FSR-000003` (`LNK-010`); verified by `FB2-VER-TMS-000002` (`LNK-016/017`); execution: none recorded.
- `FB2-HW-TSR-000001` / `FB2-HW-TSR-000002` (allocation `LNK-005/006`) verified by `FB2-VER-TMS-000004` (`LNK-023/024`); `FB2-HW-TSR-000003` (allocation `LNK-007`) verified by `FB2-VER-TMS-000005` (`LNK-025`); execution: none recorded.

#### Chains (`synthetic_reference`, test measures `synthetic_assumption`, executions `synthetic_fixture`)

- `FB2-SW-SWR-000001` ←implements— `FB2-SW-DSN-000001` (`FB2-LNK-SAF-000011`) → sources: `src/app/driver/afe/ltc/6813-1/ltc_6813-1.c`, `src/app/driver/afe/ltc/common/ltc_afe.c`, `src/app/driver/afe/ltc/common/ltc_afe_dma.c`, `src/app/driver/afe/ltc/common/ltc_pec.c` — allocation (`LNK-008`); verified by `FB2-VER-TMS-000003` (`LNK-026/027/028`); execution `FB2-VER-EXE-000003` (`LNK-035`), `pass`.
- `FB2-SW-SWR-000002` ←implements— `FB2-SW-DSN-000002` (`FB2-LNK-SAF-000012`) → sources: `src/app/application/soa/soa.c`, `src/app/engine/diag/cbs/diag_cbs_voltage.c` — allocation (`LNK-009`); verified by `FB2-VER-TMS-000001` (`LNK-022/023`); execution `FB2-VER-EXE-000001` (`LNK-033`), `pass`.
- `FB2-SW-SWR-000003` ←implements— `FB2-SW-DSN-000003` (`FB2-LNK-SAF-000013`) → sources: `src/app/driver/contactor/contactor.c`, `src/app/driver/sbc/fs8x_driver/sbc_fs8x.c`, `src/app/engine/diag/cbs/diag_cbs_contactor.c` — allocation (`LNK-010`); verified by `FB2-VER-TMS-000002` (`LNK-024/025`); execution `FB2-VER-EXE-000002` (`LNK-034`), `pass`.
- `FB2-HW-TSR-000002` verified by `FB2-VER-TMS-000005` (`LNK-031`) → `FB2-VER-EXE-000005` (`LNK-037`), `pass`; `FB2-HW-TSR-000003` verified by `FB2-VER-TMS-000006` (`LNK-032`) → `FB2-VER-EXE-000006` (`LNK-038`), `pass`.
- `FB2-SAF-FSR-000004` / `FB2-HW-TSR-000004`: no allocated SWR or DSN exists; verified by `FB2-VER-TMS-000004` (`LNK-029/030`) → `FB2-VER-EXE-000004` (`LNK-036`), `pass`. TSR-004 `allocated_to` FSR-004 (`LNK-058`).

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
| `synthetic_reference` | `FB2-MAN-SCO-000001` | MGT | **COVERED-DIRECT** | `FB2-VER-TMS-000009` (`validates`, `LNK-047`) | — | `FB2-VER-TMS-000009` | Draft planning stub; no execution |
| `synthetic_reference` | `FB2-SAF-FSR-000001` | FSR | **COVERED-DIRECT** | `FB2-VER-TMS-000003` | `FB2-HW-TSR-000001`←FB2-VER-TMS-000003, `FB2-HW-TSR-000002`←FB2-VER-TMS-000005, `FB2-SW-SWR-000001`←FB2-VER-TMS-000003 | `FB2-VER-TMS-000003`, `FB2-VER-TMS-000005` |  |
| `synthetic_reference` | `FB2-SAF-FSR-000002` | FSR | **COVERED-DIRECT** | `FB2-VER-TMS-000001` | `FB2-SW-SWR-000002`←FB2-VER-TMS-000001 | `FB2-VER-TMS-000001` |  |
| `synthetic_reference` | `FB2-SAF-FSR-000003` | FSR | **COVERED-DIRECT** | `FB2-VER-TMS-000002` | `FB2-HW-TSR-000003`←FB2-VER-TMS-000006, `FB2-SW-SWR-000003`←FB2-VER-TMS-000002 | `FB2-VER-TMS-000002`, `FB2-VER-TMS-000006` |  |
| `synthetic_reference` | `FB2-SAF-FSR-000004` | FSR | **COVERED-DIRECT** | `FB2-VER-TMS-000004` | — | `FB2-VER-TMS-000004` |  |
| `synthetic_reference` | `FB2-SW-SWR-000001` | SWR | **COVERED-DIRECT** | `FB2-VER-TMS-000003` | — | `FB2-VER-TMS-000003` |  |
| `synthetic_reference` | `FB2-SW-SWR-000002` | SWR | **COVERED-DIRECT** | `FB2-VER-TMS-000001` | — | `FB2-VER-TMS-000001` |  |
| `synthetic_reference` | `FB2-SW-SWR-000003` | SWR | **COVERED-DIRECT** | `FB2-VER-TMS-000002` | — | `FB2-VER-TMS-000002` |  |

### Coverage Summary

- **Total requirement artifacts**: 21
- **Covered (any status)**: 21 (100%)
- **UNCOVERED**: 0

Statuses above mean test-measure linkage only (see Evidence limits); execution coverage is tracked separately per test measure.

UNCOVERED requirements are the honest corpus state; the gaps are tracked by review dispositions in `FB2-REV-000001` and the gap report. No coverage is fabricated.

### Evidence limits

- COVERED in the matrix above means test-measure linkage (`verifies`), not execution evidence. Execution credit requires a `result_of`-linked execution record with retained, checkable evidence.
- In `as_is`, only `FB2-VER-TMS-000001` has an execution record (`actual_host_run`, `pass`), which is not independently substantiated (hashes `sha256:placeholder`, `output_hashes` empty, no retained per-run logs); `FB2-VER-TMS-000002` through `FB2-VER-TMS-000005` have no execution records.
- In `synthetic_reference`, all executions are `synthetic_fixture` `pass` results demonstrating corpus structure only (`product_verification_credit: false`, `human_approval_status: pending`).

---

*Generated: 2026-09-13T15:17:46Z — auto-generated from the machine-verifiable corpus. Regenerate with `python3 docs/artifacts/tools/render_spec_documents.py`.*
