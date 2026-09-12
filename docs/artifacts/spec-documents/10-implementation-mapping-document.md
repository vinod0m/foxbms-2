# foxBMS 2 — Implementation Mapping Document

**Document Control**

| Field | Value |
|---|---|
| Project | foxBMS 2 — Battery Management System |
| Document | Implementation Mapping Document |
| Baseline | BAS-REF-001 (commit `308028fb`, tag `v1.11.0`) |
| Profiles | `as_is` (source-grounded) + `synthetic_reference` (hypothetical) |
| Corpus status | `synthetic_ready_with_limitations` |
| Generated | 2026-09-12T01:01:53Z |

## Scope

Implementation mapping (design → source) and the complete requirement-to-test coverage matrix for every requirement artifact in both profiles.

## Implementation Mapping

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

#### `FB2-SW-SWR-000001` (as_is)

- Design `FB2-SW-DSN-000001` implements `FB2-SW-SWR-000001` → sources: `src/app/driver/afe/ltc/6813-1/ltc_6813-1.c`, `src/app/driver/afe/ltc/common/ltc_afe.c`, `src/app/driver/afe/ltc/common/ltc_afe_dma.c`, `src/app/driver/afe/ltc/common/ltc_pec.c`
- Verifying test measures: **UNCOVERED — no test**

#### `FB2-SW-SWR-000002` (as_is)

- Design `FB2-SW-DSN-000002` implements `FB2-SW-SWR-000002` → sources: `src/app/application/soa/soa.c`, `src/app/engine/diag/cbs/diag_cbs_voltage.c`
- Verifying test measures: `FB2-VER-TMS-000001`

#### `FB2-SW-SWR-000003` (as_is)

- Design `FB2-SW-DSN-000003` implements `FB2-SW-SWR-000003` → sources: `src/app/driver/contactor/contactor.c`, `src/app/driver/sbc/fs8x_driver/sbc_fs8x.c`, `src/app/engine/diag/cbs/diag_cbs_contactor.c`
- Verifying test measures: `FB2-VER-TMS-000002`

#### `FB2-SW-SWR-000001` (synthetic_reference)

- Design `FB2-SW-DSN-000001` implements `FB2-SW-SWR-000001` → sources: `src/app/driver/afe/ltc/6813-1/ltc_6813-1.c`, `src/app/driver/afe/ltc/common/ltc_afe.c`, `src/app/driver/afe/ltc/common/ltc_afe_dma.c`, `src/app/driver/afe/ltc/common/ltc_pec.c`
- Verifying test measures: **UNCOVERED — no test**

#### `FB2-SW-SWR-000002` (synthetic_reference)

- Design `FB2-SW-DSN-000002` implements `FB2-SW-SWR-000002` → sources: `src/app/application/soa/soa.c`, `src/app/engine/diag/cbs/diag_cbs_voltage.c`
- Verifying test measures: **UNCOVERED — no test**

#### `FB2-SW-SWR-000003` (synthetic_reference)

- Design `FB2-SW-DSN-000003` implements `FB2-SW-SWR-000003` → sources: `src/app/driver/contactor/contactor.c`, `src/app/driver/sbc/fs8x_driver/sbc_fs8x.c`, `src/app/engine/diag/cbs/diag_cbs_contactor.c`
- Verifying test measures: **UNCOVERED — no test**

## Requirement-to-Test Coverage Matrix

One row per requirement artifact across FSR/TSR/SWR/management classes, both profiles. Statuses: COVERED-DIRECT (has `verifies` link), COVERED-INDIRECT (allocated child is verified), COVERED-EMBEDDED (TMS references requirement), UNCOVERED (explicit gap).

| Profile | Requirement | Type | Status | Direct verifies | Indirect (child ← test) | Verifying tests | Gap note |
|---|---|---|---|---|---|---|---|
| `as_is` | `FB2-HW-TSR-000001` | TSR | **UNCOVERED** | — | — | — | No direct, indirect, or embedded test coverage in corpus |
| `as_is` | `FB2-HW-TSR-000002` | TSR | **UNCOVERED** | — | — | — | No direct, indirect, or embedded test coverage in corpus |
| `as_is` | `FB2-HW-TSR-000003` | TSR | **UNCOVERED** | — | — | — | No direct, indirect, or embedded test coverage in corpus |
| `as_is` | `FB2-SAF-FSR-000001` | FSR | **UNCOVERED** | — | — | — | No direct, indirect, or embedded test coverage in corpus |
| `as_is` | `FB2-SAF-FSR-000002` | FSR | **COVERED-DIRECT** | `FB2-VER-TMS-000001` | `FB2-SW-SWR-000002`←FB2-VER-TMS-000001 | `FB2-VER-TMS-000001` |  |
| `as_is` | `FB2-SAF-FSR-000003` | FSR | **COVERED-DIRECT** | `FB2-VER-TMS-000002` | `FB2-SW-SWR-000003`←FB2-VER-TMS-000002 | `FB2-VER-TMS-000002` |  |
| `as_is` | `FB2-SW-SWR-000001` | SWR | **UNCOVERED** | — | — | — | No direct, indirect, or embedded test coverage in corpus |
| `as_is` | `FB2-SW-SWR-000002` | SWR | **COVERED-DIRECT** | `FB2-VER-TMS-000001` | — | `FB2-VER-TMS-000001` |  |
| `as_is` | `FB2-SW-SWR-000003` | SWR | **COVERED-DIRECT** | `FB2-VER-TMS-000002` | — | `FB2-VER-TMS-000002` |  |
| `synthetic_reference` | `FB2-HW-TSR-000001` | TSR | **UNCOVERED** | — | — | — | No direct, indirect, or embedded test coverage in corpus |
| `synthetic_reference` | `FB2-HW-TSR-000002` | TSR | **UNCOVERED** | — | — | — | No direct, indirect, or embedded test coverage in corpus |
| `synthetic_reference` | `FB2-HW-TSR-000003` | TSR | **UNCOVERED** | — | — | — | No direct, indirect, or embedded test coverage in corpus |
| `synthetic_reference` | `FB2-HW-TSR-000004` | TSR | **UNCOVERED** | — | — | — | No direct, indirect, or embedded test coverage in corpus |
| `synthetic_reference` | `FB2-MAN-SCO-000001` | MGT | **UNCOVERED** | — | — | — | No direct, indirect, or embedded test coverage in corpus |
| `synthetic_reference` | `FB2-SAF-FSR-000001` | FSR | **UNCOVERED** | — | — | — | No direct, indirect, or embedded test coverage in corpus |
| `synthetic_reference` | `FB2-SAF-FSR-000002` | FSR | **UNCOVERED** | — | — | — | No direct, indirect, or embedded test coverage in corpus |
| `synthetic_reference` | `FB2-SAF-FSR-000003` | FSR | **UNCOVERED** | — | — | — | No direct, indirect, or embedded test coverage in corpus |
| `synthetic_reference` | `FB2-SAF-FSR-000004` | FSR | **UNCOVERED** | — | — | — | No direct, indirect, or embedded test coverage in corpus |
| `synthetic_reference` | `FB2-SW-SWR-000001` | SWR | **UNCOVERED** | — | — | — | No direct, indirect, or embedded test coverage in corpus |
| `synthetic_reference` | `FB2-SW-SWR-000002` | SWR | **UNCOVERED** | — | — | — | No direct, indirect, or embedded test coverage in corpus |
| `synthetic_reference` | `FB2-SW-SWR-000003` | SWR | **UNCOVERED** | — | — | — | No direct, indirect, or embedded test coverage in corpus |

### Coverage Summary

- **Total requirement artifacts**: 21
- **Covered (any status)**: 4 (19%)
- **UNCOVERED**: 17
  - `FB2-HW-TSR-000001` (`as_is`)
  - `FB2-HW-TSR-000002` (`as_is`)
  - `FB2-HW-TSR-000003` (`as_is`)
  - `FB2-SAF-FSR-000001` (`as_is`)
  - `FB2-SW-SWR-000001` (`as_is`)
  - `FB2-HW-TSR-000001` (`synthetic_reference`)
  - `FB2-HW-TSR-000002` (`synthetic_reference`)
  - `FB2-HW-TSR-000003` (`synthetic_reference`)
  - `FB2-HW-TSR-000004` (`synthetic_reference`)
  - `FB2-MAN-SCO-000001` (`synthetic_reference`)
  - `FB2-SAF-FSR-000001` (`synthetic_reference`)
  - `FB2-SAF-FSR-000002` (`synthetic_reference`)
  - `FB2-SAF-FSR-000003` (`synthetic_reference`)
  - `FB2-SAF-FSR-000004` (`synthetic_reference`)
  - `FB2-SW-SWR-000001` (`synthetic_reference`)
  - `FB2-SW-SWR-000002` (`synthetic_reference`)
  - `FB2-SW-SWR-000003` (`synthetic_reference`)

UNCOVERED requirements are the honest corpus state; the gaps are tracked by review dispositions in `FB2-REV-000001` and the gap report. No coverage is fabricated.


---

*Generated: 2026-09-12T01:01:53Z — auto-generated from the machine-verifiable corpus. Regenerate with `python3 docs/artifacts/tools/render_spec_documents.py`.*
