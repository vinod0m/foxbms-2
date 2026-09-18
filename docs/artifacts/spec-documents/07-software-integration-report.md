# foxBMS 2 — Software Integration Report

**Document Control**

| Field | Value |
|---|---|
| Project | foxBMS 2 — Battery Management System |
| Document | Software Integration Report |
| Baseline | BAS-REF-001 (commit `308028fb`, tag `v1.11.0`) |
| Profiles | `as_is` (source-grounded) + `synthetic_reference` (hypothetical) |
| Corpus status | `synthetic_ready_with_limitations` |
| Generated | 2026-09-13T15:17:46Z |

## Scope

Integrated software components of the foxBMS 2 build: (1) reverse-engineered integration facts — build system (waf), linked programs (application, bootloader, unit-test variants), CAN/DBC interface integration, unit-test harness integration; (2) corpus `implements` links and integration evidence; (3) explicit integration gaps. Per governance policy, missing evidence is blocked, not fabricated.

## Reverse-Engineered Integration Facts

### Build System and Linked Programs

The repository builds with the **waf** build tool (`waf-tools/`, per-module `wscript` files). Linked programs and build entry points (from the repository structure and `conf/`):

| Program | Build root | Description |
|---|---|---|
| foxBMS application | `src/app` (wscript at repo root) | Embedded BMS application, linked against `foxbms-afe` (selected AFE driver), `foxbms-driver`, engine, application layers and FreeRTOS |
| Bootloader | `src/bootloader` | Field-update bootloader for the TMS570LC4357, CAN-based, PC application in the CLI (`fox bootloader`) |
| Unit tests | `tests/unit` + `conf/unit/*.yml` | Ceedling/Unity host-based unit tests (313 C test files), build variants `app_project_posix`, `app_project_win32` |
| CLI tool | `cli/` (`fox` command) | Repository interaction: build, flash, bootloader, diagnostics (Click-based Python) |

Per-module wscript libraries integrate each module into the linked programs (driver layer `foxbms-driver`, AFE library `foxbms-afe` per `src/app/driver/afe/README.md`).

### Configuration Integration

The BMS hardware/software configuration is integrated through `conf/bms/bms.json` → generated `*_cfg` sources; unit-test and variant configurations through `conf/unit/` and `conf/env/`. Compiler configurations: `conf/cc/` (TI CGT for target, GCC for host tests).

### Interface Integration

- **CAN**: 41 messages of `tools/dbc/foxbms.dbc` are implemented as callbacks in `src/app/driver/can/cbs/` (tx/rx message sets, period monitoring `DIAG_ID_CAN_TIMING`).
- **AFE daisy-chain**: AFE drivers implement the AFE API (`src/app/driver/afe/api/afe.h`); supported chips: adi (ades1830), ltc (6804-1, 6806, 6811-1, 6812-1, 6813-1), maxim (max17852), nxp (mc33775a), ti (dummy).
- **Interlock, contactors/SPS, SBC, PEX/HTSEN/RTC (I2C task), IMD**: driver modules integrated into the task engine as listed in the task model.

## Profile: `as_is`

### Integrated Components

| Design | Implements SWR | Link rationale |
|---|---|---|
| `FB2-SW-DSN-000001` | `FB2-SW-SWR-000001` | Design implements software requirement |
| `FB2-SW-DSN-000002` | `FB2-SW-SWR-000002` | Design implements software requirement |
| `FB2-SW-DSN-000003` | `FB2-SW-SWR-000003` | Design implements software requirement |

### Integration Evidence

- `FB2-VER-EXE-000001` (`result_of` → `FB2-VER-TMS-000001`, `FB2-LNK-SAF-000018`): kind=`actual_host_run`, outcome=`pass` — unit-level execution only (SOA voltage test); hashes `sha256:placeholder`, `output_hashes` empty, not independently substantiated. No component/integration-level executions exist in `as_is`.

### Integration Gaps

| Gap | Disposition |
|---|---|
| No component-level test measures | Gap documented; synthetic_reference to add per review disposition FB2-FND-000005 |
| No integration-level executions (only unit `actual_host_run` exists) | Per governance policy: actual product evidence = 0 — blocked, not fabricated |
| No target-hardware integration runs | as_is gap documented in review `FB2-REV-000001` (finding FB2-FND-000002) |

## Profile: `synthetic_reference`

### Integrated Components

| Design | Implements SWR | Link rationale |
|---|---|---|
| `FB2-SW-DSN-000001` | `FB2-SW-SWR-000001` | Design implements software requirement |
| `FB2-SW-DSN-000002` | `FB2-SW-SWR-000002` | Design implements software requirement |
| `FB2-SW-DSN-000003` | `FB2-SW-SWR-000003` | Design implements software requirement |

### Integration Evidence

All six executions are unit-level `synthetic_fixture` results (`result_of` links `FB2-LNK-SAF-000033..038`), demonstrating corpus structure only — no component/integration-level test measures exist in `synthetic_reference`.

- `FB2-VER-EXE-000001`: kind=`synthetic_fixture`, outcome=`pass`
- `FB2-VER-EXE-000002`: kind=`synthetic_fixture`, outcome=`pass`
- `FB2-VER-EXE-000003`: kind=`synthetic_fixture`, outcome=`pass`
- `FB2-VER-EXE-000004`: kind=`synthetic_fixture`, outcome=`pass`
- `FB2-VER-EXE-000005`: kind=`synthetic_fixture`, outcome=`pass`
- `FB2-VER-EXE-000006`: kind=`synthetic_fixture`, outcome=`pass`

### Integration Gaps

| Gap | Disposition |
|---|---|
| No component-level test measures | Gap documented; synthetic_reference to add per review disposition FB2-FND-000005 |
| No integration-level executions (only unit `actual_host_run` exists) | Per governance policy: actual product evidence = 0 — blocked, not fabricated |
| No target-hardware integration runs | as_is gap documented in review `FB2-REV-000001` (finding FB2-FND-000002) |


---

*Generated: 2026-09-13T15:17:46Z — auto-generated from the machine-verifiable corpus. Regenerate with `python3 docs/artifacts/tools/render_spec_documents.py`.*
