# Verification Evidence Report

**Generated:** 2026-09-13  
**Baseline:** BAS-REF-001  
**Profile:** synthetic_reference (primary), as_is (comparison)

## Overview

This report documents the verification evidence for all requirements in the corpus, distinguishing between execution kinds and evidence classifications per corpus policy. With the test-measure expansion all FSRs, SWRs and hardware TSRs in the synthetic_reference profile now have dedicated test measures and (synthetic fixture) executions; the as_is profile carries the source-grounded unit-test measures extracted from the real foxBMS 2 test suite.

## Evidence Classification Framework

| Execution Kind | Description | Examples |
|----------------|-------------|---------|
| `none` | No execution planned or performed | Planned test measures not yet executed |
| `actual_host_run` | Executed on development host (x86_64 Linux) | Unity/CMock unit tests |
| `actual_simulation_run` | Executed on simulator with captured logs | Not used |
| `synthetic_fixture` | Synthetic test data/fixture for corpus validation | Synthetic execution set EXE-001..006 |

| Outcome | Description |
|---------|-------------|
| `pass` | All acceptance criteria met |
| `fail` | One or more acceptance criteria not met |
| `inconclusive` | Execution incomplete or ambiguous |
| `not_run` | Planned but not executed |
| `blocked` | Cannot execute (missing hardware, tools, etc.) |

## Verification Evidence by Requirement

### Safety Goal: FB2-SAF-SGO-000001 (Cell Voltage)

| FSR | Verification Approach | Test Measure | Execution | Outcome | Evidence Class |
|-----|----------------------|--------------|-----------|---------|----------------|
| FSR-001: Cell Voltage Acquisition | test | TMS-003 | EXE-003 (synthetic_fixture) | pass | synthetic_fixture |
| FSR-002: SOA Voltage Monitoring | test | TMS-001 | EXE-001 (synthetic_fixture; as_is: actual_host_run) | pass | synthetic_fixture / actual_host_run (as_is) |
| FSR-003: Contactor Opening | test | TMS-002 | EXE-002 (synthetic_fixture) | pass | synthetic_fixture |
| FSR-004: Independent Monitor | test (fault_injection) | TMS-004 | EXE-004 (synthetic_fixture) | pass | synthetic_fixture |

### Hardware TSRs

| TSR | Verification Approach | Test Measure | Execution | Outcome | Evidence Class |
|-----|----------------------|--------------|-----------|---------|----------------|
| TSR-001: AFE Accuracy | test | TMS-003 | EXE-003 (synthetic_fixture) | pass | synthetic_fixture (unit-level model; target measurement blocked) |
| TSR-002: isoSPI Integrity | test (robustness) | TMS-005 | EXE-005 (synthetic_fixture) | pass | synthetic_fixture (unit-level model; target measurement blocked) |
| TSR-003: Contactor Driver | test | TMS-006 | EXE-006 (synthetic_fixture) | pass | synthetic_fixture (unit-level model; target measurement blocked) |
| TSR-004: Independent Monitor HW | test (fault_injection) | TMS-004 | EXE-004 (synthetic_fixture) | pass | synthetic_fixture |

### Software SWRs

| SWR | Verification Approach | Test Measure | Execution | Outcome | Evidence Class |
|-----|----------------------|--------------|-----------|---------|----------------|
| SWR-001: AFE Driver | test | TMS-003 | EXE-003 | pass | synthetic_fixture |
| SWR-002: SOA Monitor | test | TMS-001 | EXE-001 | pass | synthetic_fixture |
| SWR-003: Contactor SM | test | TMS-002 | EXE-002 | pass | synthetic_fixture |

## Test Measures Detail

| ID | Title | Type | Requirements | Oracle Basis | Profile | `verifies` links |
|----|-------|------|--------------|--------------|---------|------------------|
| FB2-VER-TMS-000001 | SOA Voltage Limit Detection | unit | FSR-002, SWR-002 | source_grounded (as_is: test_soa.c) / synthetic_assumption (synthetic mirror) | both | as_is `LNK-014/015`; synthetic `LNK-022/023` |
| FB2-VER-TMS-000002 | Contactor State Machine Fault Response | unit | FSR-003, SWR-003 | source_grounded (as_is: test_contactor.c) / synthetic_assumption (synthetic mirror) | both | as_is `LNK-016/017`; synthetic `LNK-024/025` |
| FB2-VER-TMS-000003 | AFE Cell Voltage Plausibility Checks | unit | FSR-001, SWR-001, TSR-001 | source_grounded (as_is: test_afe_plausibility.c) / synthetic_assumption (synthetic mirror) | both | as_is `LNK-021/022`; synthetic `LNK-026/027/028` |
| FB2-VER-TMS-000004 | Independent Voltage Monitor Reaction | fault_injection | FSR-004, TSR-004 | synthetic_assumption (no upstream test; documented gap) | synthetic_reference | `LNK-029/030` |
| FB2-VER-TMS-000004 | LTC6813-1 AFE Driver Communication and Measurement | unit | TSR-001, TSR-002 | source_grounded (test_ltc_6813-1.c) | as_is | `LNK-023/024` |
| FB2-VER-TMS-000005 | Contactor Driver Configuration and Control | unit | TSR-003 | source_grounded (test_contactor.c) | as_is | `LNK-025` |
| FB2-VER-TMS-000005 | AFE Communication Integrity | robustness | TSR-002 | synthetic_assumption | synthetic_reference | `LNK-031` |
| FB2-VER-TMS-000006 | Contactor Driver Configuration and Control | unit | TSR-003 | synthetic_assumption | synthetic_reference | `LNK-032` |
| FB2-VER-TMS-000007 | Software Integration Chain (SOA-Database-Contactor) | integration | SWR-001, SWR-002, SWR-003 | synthetic_assumption | synthetic_reference | `LNK-039/040/041` |
| FB2-VER-TMS-000008 | System Qualification (Cell-Voltage Safety Chain) | qualification | FSR-001, FSR-002, FSR-003, FSR-004 | synthetic_assumption | synthetic_reference | `LNK-042/043/044/045` |
| FB2-VER-TMS-000009 | Stakeholder Validation (Cell-Voltage Use Cases) | validation | SGO-001, SCO-001 | synthetic_assumption | synthetic_reference | `LNK-046/047` (`validates`) |
| FB2-VER-TMS-000010 | Component Verification (SOA Monitor + DIAG Callbacks) | unit | SWR-002 | synthetic_assumption | synthetic_reference | `LNK-048` |
| FB2-VER-TMS-000011 | HIL Fault Reaction (Target) | system | FSR-001, FSR-002, FSR-003, FSR-004 | synthetic_assumption | synthetic_reference | `LNK-049/050/051/052` |

## Execution Records

| ID | Test Measure | Kind | Outcome | Duration | Limitations | `result_of` link |
|----|--------------|------|---------|----------|-------------|------------------|
| FB2-VER-EXE-000001 | TMS-001 | synthetic_fixture (as_is twin: actual_host_run) | pass | 5000 ms | Mocked database; no target timing; as_is twin hashes `sha256:placeholder`, `output_hashes` empty | synthetic `LNK-033`; as_is twin `LNK-018` |
| FB2-VER-EXE-000002 | TMS-002 | synthetic_fixture | pass | 5000 ms | Mocked SBC/GPIO; no HW-in-loop | `LNK-034` |
| FB2-VER-EXE-000003 | TMS-003 | synthetic_fixture | pass | 5000 ms | Mocked AFE; no target measurement | `LNK-035` |
| FB2-VER-EXE-000004 | TMS-004 | synthetic_fixture | pass | 5000 ms | Fault injection on model, not diverse hardware path | `LNK-036` |
| FB2-VER-EXE-000005 | TMS-005 | synthetic_fixture | pass | 5000 ms | PEC corruption simulated at driver API level | `LNK-037` |
| FB2-VER-EXE-000006 | TMS-006 | synthetic_fixture | pass | 5000 ms | GPIO mocked; no contactor hardware | `LNK-038` |

## Hardware-in-the-Loop (HIL) Disposition

The upstream foxBMS 2 repository prescribes HIL testing with **100% line and branch
coverage** for the linked program on target hardware
(`docs/developer-manual/software/software-testing.rst`,
`docs/developer-manual/software/software-verification.rst`), but the HIL test setup
itself is **not published** in the repository (`tests/hil` contains a placeholder only).

Corpus disposition for this gap:

1. **as_is profile** — the gap is *documented, not bridged*: no HIL artifacts are
   fabricated. Unit-test coverage (313 C test files under `tests/unit/app/`) is the
   observable evidence; HIL evidence is explicitly classified `blocked`
   (missing target hardware and test setup).
2. **synthetic_reference profile** — hardware TSR verification planning uses
   *host-based models with mocked hardware boundaries* (TMS-003/004/005/006).
   The associated `synthetic_fixture` records demonstrate corpus structure, not
   independently verified test execution or target measurement. `product_verification_credit` remains `false` for every
   artifact by governance policy.
3. **No execution claims HIL.** The `execution_kind` vocabulary contains no HIL entry;
   target-hardware verification would require `actual_hardware_run` evidence (logs,
   hashes, tool versions) that does not exist and is therefore not invented.

## Coverage Analysis

### By Requirement (synthetic_reference)

This table shows test-measure and synthetic-fixture coverage, not verified product
behavior. A fixture `pass` does not establish that the requirement was satisfied
on a host or target; product verification credit remains false.

| Requirement | Test Measure / Fixture Present? | Evidence Class | Notes |
|-------------|-----------|----------------|-------|
| FSR-001 | Yes | synthetic_fixture | TMS-003/EXE-003 |
| FSR-002 | Yes | synthetic_fixture | TMS-001/EXE-001 |
| FSR-003 | Yes | synthetic_fixture | TMS-002/EXE-002 |
| FSR-004 | Yes | synthetic_fixture | TMS-004/EXE-004 |
| TSR-001 | Yes (unit-level) | synthetic_fixture | TMS-003/EXE-003; target measurement blocked |
| TSR-002 | Yes (unit-level) | synthetic_fixture | TMS-005/EXE-005; target measurement blocked |
| TSR-003 | Yes (unit-level) | synthetic_fixture | TMS-006/EXE-006; target measurement blocked |
| TSR-004 | Yes (unit-level) | synthetic_fixture | TMS-004/EXE-004; target measurement blocked |
| SWR-001 | Yes | synthetic_fixture | TMS-003/EXE-003 |
| SWR-002 | Yes | synthetic_fixture | TMS-001/EXE-001 |
| SWR-003 | Yes | synthetic_fixture | TMS-002/EXE-002 |
| SCO-001 (management) | Planning stub only | synthetic_assumption | TMS-009 (`validates`, `LNK-047`), draft, no execution |

### Recorded Execution Coverage (as_is)

| Scope | Test Measure | Execution Record | Evidence Status |
|-------|--------------|------------------|-----------------|
| SOA voltage limits | FB2-VER-TMS-000001 | FB2-VER-EXE-000001 | Recorded as actual_host_run/pass; execution evidence not independently verified |
| Contactor state machine, AFE plausibility, LTC6813-1 driver, contactor driver | FB2-VER-TMS-000002..000005 | No corresponding execution records in as_is/verification | Test planning/source references only; no execution credit inferred |

The SOA execution record contains `sha256:placeholder` log and coverage hashes,
empty `output_hashes`, and a note that per-run logs were not retained. Its recorded
`pass` is not independently substantiated by those fields. Source test files and
`source_grounded` oracle labels do not establish that tests ran. Feature-wide test
counts and host-run claims are therefore not inferred from source availability.

## Oracle Basis Analysis

| Oracle Basis | Count | Notes |
|--------------|-------|-------|
| source_grounded | 5 (as_is test measures) | Grounded in existing foxBMS unit tests (TMS-001..005, test_soa.c / test_contactor.c / test_afe_plausibility.c / test_ltc_6813-1.c) |
| synthetic_assumption | 11 (synthetic_reference test measures) | Synthetic mirrors of the as_is tests (TMS-001/002/003/005/006) plus fault-injection monitor (TMS-004), integration stub (TMS-007), qualification stub (TMS-008), validation stub (TMS-009), component stub (TMS-010), HIL stub (TMS-011) |
| analytical_model | 0 | Not used |
| measured_reference | 0 | No HW testing |

## Verification Gaps (remaining, honest)

1. **Target hardware measurement** — TSR-001..004 have test measures and recorded blocked executions only;
   actual hardware measurements remain blocked (no target hardware in corpus scope).
2. **HIL execution** — `FB2-VER-EXE-000011` recorded `blocked` (`outcome: blocked`, `execution_kind: none`); upstream test setup unpublished (`tests/hil` placeholder).
3. **Integration executions** — stub `FB2-VER-TMS-000007` linked; `FB2-VER-EXE-000007` recorded `blocked` (integration harness not in corpus scope).
4. **Timing verification** — no worst-case execution time analysis on target.
5. **Management scope (SCO-001)** — `validates` via TMS-009 stub (`LNK-047`), `FB2-VER-EXE-000009` recorded `blocked`.
6. **Component / qualification / validation / HIL executions** — all recorded as blocked execution records (`FB2-VER-EXE-000007..000011`, `outcome: blocked`, `execution_kind: none`); dependency failures documented per record, not fabricated.
7. **TSR-004 allocation** — `allocated_to` link `FB2-LNK-SAF-000058` added (TSR-004 → FSR-004); no allocated SWR or DSN exists for the pair (both verified by `FB2-VER-TMS-000004`).
8. **as_is unit-test executions (TMS-002..005)** — recorded `blocked` (`FB2-VER-EXE-000002..000005`, `outcome: blocked`): upstream CI enforces these tests every revision, but per-run logs are not captured in the corpus; local execution confirmed infeasible (macOS unsupported by `fox.sh`; direct Ceedling 1.1.8 fails on missing HALCoGen codegen `./include` headers and `gdb`).
9. **as_is host-run substantiation (TMS-001/EXE-001)** — recorded `actual_host_run`/`pass` with `sha256:placeholder` hashes and empty `output_hashes`; not independently substantiated.
10. **HWE.2/HWE.3 hardware architecture and detailed design** — `partially_mapped`: design packages inventoried (43-anchor registry), but Altium/CAD binaries are unreadable to the corpus tooling — a format limit, only real hardware analysis closes it.

Every gap above is tracked as a corpus limitation (`final_status:
synthetic_ready_with_limitations`); no evidence is fabricated to close it.

### Unblocking conditions (what would close each gap)

| Gap | Unblocked by |
|---|---|
| as_is unit executions (TMS-002..005) | Running Ceedling on Linux/Windows with HALCoGen codegen (`./include`) + `gdb`, or capturing upstream CI per-run logs |
| Integration executions (TMS-007/EXE-007) | Defining an integration harness in corpus scope |
| Component executions (TMS-010/EXE-010) | Defining a component harness in corpus scope |
| Qualification executions (TMS-008/EXE-008) | A qualification environment |
| HIL executions (TMS-011/EXE-011) | Publishing the HIL test setup upstream (`tests/hil`) + target hardware |
| Validation executions (TMS-009/EXE-009) | A validation environment with operational data |
| Timing verification | WCET analysis on target |
| Host-run substantiation (EXE-001) | Re-running the SOA test with retained logs/coverage hashes |
| HWE.2/HWE.3 partial | Real hardware architecture/design analysis of the CAD packages |
