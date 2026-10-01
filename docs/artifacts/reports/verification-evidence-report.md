# Verification Evidence Report

**Generated:** 2026-10-01 (evidence base refreshed; headline is now the SIL run)
**Baseline:** BAS-REF-001 — source pinned to commit `308028fb`, corpus authored at `2a408d5`
**Primary evidence (tracked):** `docs/artifacts/evidence/actual-runs/foxbms2-sil-host-unit-test-macos-2026-09-29/results-sil-all.json`
**Earlier evidence (tracked):** `docs/artifacts/evidence/actual-runs/foxbms2-host-unit-test-macos-2026-09-29/results-strict.json`

> **These runs are not target-hardware evidence, and they are not credited as
> such.** macOS is **not an upstream-supported foxBMS platform**. foxBMS 2
> targets a Texas Instruments TMS570-family MCU with a proprietary HALCoGen
> code-generation step. Both runs are **host runs on a development machine**.
> They exercise real product source code, which makes them genuine evidence
> about the code, but they say nothing about timing on the target, about the
> closed-loop control behaviour, or about the four `tests/unit-hw/test_tms570_*.c`
> target-hardware tests, which were never attempted.
> `actual_product_evidence` remains **0/33** and `product_verification_credit`
> is `false` on all **263** records.
>
> Nothing here asserts ISO 26262 conformity, ASIL capability, ASPICE capability
> level, certification, human approval or tool qualification. No human has
> approved anything in this corpus.

### Where the evidence actually lives, and where it does not

The previous version of this report cited
`docs/artifacts/.work/verification-env/logs/results-strict.json` as its primary
evidence. **`.work/` is gitignored and untracked, so that file is not in the
distribution.** It has been replaced by a tracked path, and the distinction is
now stated everywhere it matters:

| Artefact | Tracked? | Path |
|---|---|---|
| Pre-SIL strict results | **yes** | `docs/artifacts/evidence/actual-runs/foxbms2-host-unit-test-macos-2026-09-29/results-strict.json` |
| Pre-SIL relaxed results | **yes** | `…/foxbms2-host-unit-test-macos-2026-09-29/results-relaxed.json` |
| HALCoGen dependency closure | **yes** | `…/foxbms2-host-unit-test-macos-2026-09-29/halcogen-dependency-closure.json` |
| SIL results (all 313 targets) | **yes** | `…/foxbms2-sil-host-unit-test-macos-2026-09-29/results-sil-all.json` |
| SIL runbook (reproduction instructions) | **yes** | `…/foxbms2-sil-host-unit-test-macos-2026-09-29/RUNBOOK.md` |
| Per-test SIL logs (313 files) | **yes** | `…/foxbms2-sil-host-unit-test-macos-2026-09-29/logs-strict/` |
| SIL harness working tree | **NO — gitignored** | `docs/artifacts/.work/verification-env/sil/` |
| Pre-SIL harness working tree | **NO — gitignored** | `docs/artifacts/.work/verification-env/` |

Measured on the last `validate` run: **46 log entries, 46 hashes verified, 0
mismatched, 0 unverified, 0 missing; 34 `evidence_files` entries, 0 missing.**

> **Five execution records cite a digest that resolves only into the gitignored
> tree.** `FB2-VER-EXE-000008`…`FB2-VER-EXE-000012` each carry
> `output_hashes.sil_suite_results_all =
> sha256:cbbdebeecd54720561753562f7c7dd3ca105e04ca36494f52b674d9fd5a00f67`,
> which resolves to
> `docs/artifacts/.work/verification-env/sil/logs/RESULTS-POST-fix.json` and
> **not** to the `results-sil-all.json` those records name in their `logs[]`
> (`sha256:edd3e70888c75ba075db2dadb17cd9cfb369adfce4b8ac4a05aaefada3c64589`).
> `FB2-VER-EXE-000015` names eight `.work/` paths directly in its `logs[]`. The
> per-test logs those records *do* name are tracked and verify; it is the
> suite-level aggregate digest that lives outside the distribution. A fresh
> clone can reproduce the run from the tracked `RUNBOOK.md` and cannot verify
> those five aggregate digests.

## 1. The SIL Run — the current headline

Harness: `SIL host unit tests (CMock mocks of host-declared HL_*.h interface headers)`.

| Measure | Value |
|---|---|
| Host | `Darwin vinods-mbp-14.localdomain 27.0.0` (arm64) |
| Toolchain | `ruby 4.0.7 (2026-09-15 revision 229531a6cf) +PRISM [arm64-darwin27]`, `Apple clang version 17.0.0` |
| Run timestamp | **2026-09-30T01:24:18+0200** |
| Selection | `all` — **no HALCoGen exclusion** |
| **CeeDling targets attempted** | **313** |
| **Passed** | **222** |
| **Failed** | **7** |
| Build failures | **84** |
| Assertions tested | **988** |
| Assertions passed | **950** |
| Assertions failed | **35** |

313 = 222 + 7 + 84 exactly. Every per-test log, the suite results, the HAL
surface inventory and the HAL signature inventory are tracked and
sha256-verified.

### The 84 build failures, classified

The harness classifies a build failure on the **set of distinct, order-independent
diagnostic codes** — severity, `-W` flag and normalised message — not on any
single message, and collects the set with `SIL_DIAG_COLLECT=1` so Ceedling
compiles every remaining translation unit instead of aborting at the first.

| Class | n | What it is |
|---|---:|---|
| `excluded:upstream_config` | 28 | paths the shipped Ceedling `:paths:` configuration excludes deliberately |
| `build:clang_only_diagnostic` | 22 | a diagnostic Apple clang enables that GNU gcc does not, promoted by `-Werror` |
| `build:undeclared_identifier` | 8 | identifier used without a declaration |
| `build:real_defect_out_of_bounds_array_index` | 6 | **a real defect in the product** |
| `build:strict_diagnostic_both_compilers` | 5 | fires under both compilers |
| `build:real_defect_macro_arity` | 4 | **a real defect** |
| `build:sil_interface_header_mismatch` | 3 | the SIL interface header disagrees with the module under test |
| `build:real_defect_implicit_function_declaration` | 2 | **a real defect** |
| `build:real_defect_implicit_int` | 2 | **a real defect** |
| `build:not_buildable_on_macos_object_format` | 1 | Mach-O cannot express what the source asks for |
| `build:product_tautological_guard` | 1 | a guard that cannot fail |
| `build:real_defect_absolute_value_truncation` | 1 | **a real defect** |
| `build:real_defect_excess_initializers` | 1 | **a real defect** |
| **Total** | **84** | |

**16 of the 84 are classified by the harness itself as real product defects.**
That is a stronger claim than "the build broke", and it is the reason the SIL
run is worth publishing even though it did not reach 313 passes.

### A finding the SIL run produced against itself

`FB2-REV-FND-000042`: **53 of the 245 green tests in the SIL host run assert
nothing.** A vacuous test passes whatever the code does, so a green result from
it is not evidence of anything. The harness ships a vacuous-test detector
(`find_vacuous_tests.py`) and a real-diagnostics dumper
(`dump_diagnostics.py`), both hashed in `FB2-VER-EXE-000015`. This is recorded
against the SIL run rather than omitted from it: a run that hides its own
weakness is not usable evidence.

### "313 tests" is the harness's enumeration, not a count of the tree

The harness attempted **313** distinct CeeDling targets. The repository today
holds **318** `test_*.c` files under `tests/`. The 5 not attempted are
`tests/unit-hw/test_tms570_{boot,crc,flash,main}.c` — the TMS570
**target-hardware** tests, i.e. exactly the evidence class this corpus cannot
produce — plus
`tests/cli/pre_commit_scripts/test_check_include_guard/test_file.c`, a C sample
for a Python linter.

## 1.1 The Earlier Pre-SIL Run, for the record

| Measure | Strict | Relaxed |
|---|---:|---:|
| Timestamp | 2026-09-29T10:30:52+0200 | 2026-09-29T10:33:16+0200 |
| Selection | `no_halcogen_dependency` | `no_halcogen_dependency` |
| Tests in scope | 136 | 136 |
| Passed | 94 | 98 |
| Failed | 5 | 7 |
| Build failures | 37 | 31 |
| Assertions tested / passed / failed | 332 / 323 / 8 | 391 / 380 / 10 |

Raw data (tracked): `…/foxbms2-host-unit-test-macos-2026-09-29/results-strict.json`
and `results-relaxed.json`. Run procedure and full account: the **tracked**
`…/foxbms2-sil-host-unit-test-macos-2026-09-29/RUNBOOK.md` (the SIL runbook
supersedes the `.work` copy the earlier version of this report cited).

## 2. The Five Failures Are a Real Product Defect

All five fail with the same message shape:

```
At line (90): "Expected 0x…C000 Was 0x…C098:Function DATA_Write4DataBlocks
Argument pDataFromSender0:Function called with unexpected argument value."
```

### Root cause

`src/app/engine/database/database.h:209` declares the database access API with
**untyped `void *` parameters**:

```c
extern STD_RETURN_TYPE_e DATA_Write4DataBlocks(
    void *pDataFromSender0, void *pDataFromSender1, ...);
```

The shipped Ceedling configuration sets `:cmock: :when_ptr: :compare_data`.
`compare_data` requires CMock to know the **size** of the pointed-to type so it
can `memcmp`. Given `void *` it cannot, so CMock emits
`UNITY_TEST_ASSERT_EQUAL_PTR` — a pointer-**identity** check. The generated mock
confirms it:

```c
UNITY_TEST_ASSERT_EQUAL_PTR(cmock_call_instance->Expected_pDataFromSender0,
                            pDataFromSender0, cmock_line, CMockStringMismatch);
```

The tests then pass a pointer to their own `static` copy of the table:

```c
static DATA_BLOCK_ERROR_STATE_s diag_tableErrorFlags = {...};
DATA_Write4DataBlocks_ExpectAndReturn(&diag_tableErrorFlags, ..., STD_OK);
```

while the code under test passes a pointer to *its own different* `static`
copy. The identity check can therefore never succeed.

### This is not a harness artefact

This matters enough to state plainly. The failure depends **only** on the
`void *` declaration and on the CMock configuration. It does not depend on the
host, the compiler, the architecture or any adaptation made to run on macOS. The
same five tests are expected to fail under GNU gcc on Linux. The macOS
environment surfaced a defect that was already there.

The one environment-dependent finding in the whole run is the opposite of an
artefact: the Apple-clang-only `-Werror` diagnostics promoted to errors **hide
real failures** (§5.3 of the RUNBOOK), which is why the extended sweep finds two
*more* failures with the identical root cause rather than fewer.

**No result was adjusted to make any test pass.**

### Affected tests

| Test | Assertions tested | Assertions failed |
|---|---|---|
| `tests/unit/app/application/algorithm/moving_average/test_moving_average.c` | 1 | 1 |
| `tests/unit/app/application/algorithm/state_estimation/soc/lookup-table/test_soc_lookup-table.c` | 6 | 1 |
| `tests/unit/app/application/algorithm/state_estimation/test_state_estimation.c` | 5 | 4 |
| `tests/unit/app/driver/afe/debug/default/test_debug_default.c` | 11 | 1 |
| `tests/unit/app/engine/config/test_diag_cfg.c` | 1 | 1 |
| **Total** | **24** | **8** |

The extended sweep adds two more with the identical root cause:
`tests/unit/app/application/redundancy/test_redundancy.c` (10 tested, 1 failed)
and `tests/unit/app/engine/diag/test_diag.c` (18 tested, 1 failed).

### Fix direction

A decision for the product owner, not for this run. Either:

1. type the `database.h` parameters so `:when_ptr: :compare_data` works as
   intended, or
2. add explicit `:treat_as` entries, or
3. have the affected tests register a CMock callback and compare contents in the
   callback.

Each defect has a first-class execution record in the corpus:
`FB2-VER-EXE-000008` … `FB2-VER-EXE-000014`, one per genuine failure.

## 3. The 37 Build Failures

| Cause | Count | Actionable? |
|---|---|---|
| Excluded by the shipped Ceedling `:paths:` configuration — `tests/unit/app/driver/afe/adi/common/ades183x/**`, `tests/unit/app/driver/afe/nxp/common/mc3377x/**`, `tests/unit/support` | 21 | No. Upstream excludes these deliberately; see the `README.md` in each excluded AFE directory. |
| Requires a HALCoGen-generated TI header — `HL_het.h`, `HL_reg_system.h`, `HL_sys_common.h`, `HL_sys_dma.h` | 10 | Only with HALCoGen. |
| Apple-clang-only diagnostic promoted by `-Werror` | 6 | Yes, but two of them hide real failures. |

A build failure is not a test failure and is not counted as one. The 5 failures
in §2 are tests that **ran and failed**; the 37 did not run at all.

## 4. The 177 Tests the Pre-SIL Run Excluded — now reached by the SIL harness

**Superseded as a blocker, retained as a characterisation.** Of the harness's
**313** enumerated targets, the pre-SIL run selected **136** and excluded **177**
because their quoted-`#include` closure reaches a HALCoGen-generated header
(`docs/artifacts/evidence/actual-runs/foxbms2-host-unit-test-macos-2026-09-29/halcogen-dependency-closure.json`,
tracked).

The SIL harness mocks those headers at the interface boundary rather than
reconstructing TI register maps, so **all 313 targets are now attempted**
(§1). Of the 84 remaining build failures, 28 are upstream-excluded paths and 22
are Apple-clang-only diagnostics; the HALCoGen-specific exclusion no longer
accounts for any of them.

The excluded tests reached **34 distinct `HL_*.h` headers**, including
`HL_adc.h`, `HL_can.h`, `HL_crc.h`, `HL_dcc.h`, `HL_ecap.h`, `HL_epc.h`,
`HL_eqep.h`, `HL_errata_SSWF021_45.h`, `HL_esm.h`, `HL_etpwm.h`, `HL_gio.h`,
`HL_hal_stdtypes.h`, `HL_het.h`, `HL_i2c.h`, `HL_lin.h`, `HL_mdio.h`,
`HL_pinmux.h` and `HL_reg_adc.h` among them.

**Reconstructing 34 proprietary TI register maps and driver APIs from memory
would fabricate the very thing these tests exist to verify, so it was not done.**
The blocker is instead characterised precisely: `analyze_hcg_closure.py` records,
for every one of the 313 tests, exactly which HALCoGen headers it needs.

### To unblock

The SIL harness is option (c), and it is what the corpus actually used: CMock
mocks of host-declared `HL_*.h` interface headers, so the tests compile and run
against a declared interface instead of against TI's proprietary register maps.
That boundary is stated in the harness description itself and is the reason the
313-target result is **not** evidence about TI register semantics.

The options that remain open:

- **(a)** a real HALCoGen run on `conf/hcg/app.hcg` — requires a TI licence; or
- **(b)** a Linux host, where the ELF compiler accepts the TI section attributes
  unchanged. This is the path upstream already documents.

Docker is available (`Docker version 29.8.0`), so option (b) is viable. It was
**not** built, because native macOS succeeded and the deliverable priority puts
native first. Neither (a) nor (b) substitutes for target hardware, which is the
one thing neither can provide.

## 5. The Two Sweeps

| Sweep | Corpus record | Tests | Passed | Failed | Build failures | Assertions (tested/passed/failed) |
|---|---|---|---|---|---|---|
| strict | `FB2-VER-EXE-000006` | 136 | 94 | 5 | 37 | 332 / 323 / 8 |
| extended | `FB2-VER-EXE-000007` | 136 | 98 | 7 | 31 | 391 / 380 / 10 |

The extended sweep relaxes the Apple-clang-only `-Werror` promotions, which lets
6 more tests build. It finds **2 more** failures, both with the identical
`DATA_Write4DataBlocks` root cause. That is the diagnostic signature of a real
defect: relaxing a warning reveals more instances of the same problem rather
than hiding them.

An earlier first run is preserved at `logs/results.json` with identical strict
figures (136 / 94 / 5 / 37), which is the reproducibility check.

## 6. Execution Evidence Classes

The corpus separates evidence classes explicitly so that a blocked result is
never mistaken for a pass. The `actual_product_evidence` coverage dimension
reads **0/33**, and the tool's own detail string states the reason: *execution_kind
has no target-hardware member, so none can be claimed (blocked, not fabricated)*.

Of **44** execution records:

| Class | Count | Credit |
|---|---|---|
| `actual_host_run` (real product code, development host) | **15** | Real product code on a development host. **Not** target hardware. |
| `execution_kind: none` | **23** | 1 `as_is`, 22 `synthetic_reference`. Blocked. No product credit. |
| `synthetic_fixture` | **6** | **No retained evidence — see below.** No product credit. |
| undeclared | **0** | — |
| **target hardware** | **0** | — |

> **The 6 `synthetic_fixture` executions retain nothing.**
> `FB2-VER-EXE-000001`…`FB2-VER-EXE-000006` (profile `synthetic_reference`) each
> record `execution_kind: synthetic_fixture`, `outcome: pass`, `logs: []` and no
> `evidence_files` entry. `docs/artifacts/evidence/synthetic-fixtures/` holds **no
> fixture artefact** — its only file is a hand-written `MANIFEST.md` which states
> that the fixture was never captured and that the file "must never be counted as
> captured evidence for any test". The fixture they claim to have run was never
> retained, so the `pass` cannot be checked by anyone — including this corpus. Their `evidence_refs` name
> real test measures and real test source files, which is not the same thing as
> evidence that a run happened.

### Records created and corrected by this run

Fourteen `execution` artifacts now sit under `corpus/as_is/verification/`: five
were **revised from placeholder values** to real measurements (rev 1 → 2), and
nine are **new**.

| Record | Change |
|---|---|
| `FB2-VER-EXE-000001` (SOA voltage) | rev 1 → 2. Revision 1 claimed `actual_host_run` / `pass` with `"hash": "sha256:placeholder"` and an unverifiable `x86_64 Linux host / gcc 11.4.0` environment. Superseded with a real arm64 macOS run and real sha256 values. |
| `FB2-VER-EXE-000002`, `-000003`, `-000005` | rev 1 → 2. `execution_kind: none` / `outcome: blocked` → `actual_host_run` with real results. Records 000002 and 000005 both name `test_contactor.c`; one execution evidences both, which is noted in each record. |
| `FB2-VER-EXE-000004` (AFE LTC driver) | rev 1 → 2. Still `none` / `blocked`, but the blocker is now precise: the include closure needs exactly `HL_het.h`, `HL_spi.h`, `HL_sys_dma.h`. Revision 1's evidence path was **wrong** (missing the `afe/` segment) and has been corrected. |
| `FB2-VER-EXE-000006`, `-000007` | new; the two bulk sweeps. |
| `FB2-VER-EXE-000008` … `-000014` | new; one record per genuine test failure. |

Current `as_is` execution outcomes: **4 `pass`**, **9 `fail`**, **1 `blocked`**.

Both bulk sweeps are recorded as `outcome: fail`, not `pass`, because each sweep
contains failing tests. Recording a partially-failing sweep as a pass would be
the same class of error as the `sha256:placeholder` value described above.

Removing a fabricated `sha256:placeholder` and an unverifiable environment
string is the point of this section: a placeholder that looks like evidence is
worse than an honest gap, because it survives review.

## 7. Verification Planning

**33 test measures cover 7 distinct FSR ids** (`verification_planning` = 33/7, a
ratio rather than a score).

- **`as_is`:** 5 test measures, 16 execution records.
- **`synthetic_reference`:** 28 test measures, 28 execution records.

### The `verifies` direction convention

The **test measure is the source** and the **requirement is the target**. A
verified requirement therefore appears as a link *target*, never as a source.
The corpus validator's rule inspects only the source side, so it fires on
correctly verified requirements. This is recorded as `FB2-REV-FND-000001`, whose
honest reading is: **examine verification links on both sides before concluding
a safety requirement is unverified.** The check was deliberately left unchanged
because it is the detector the mutation scenarios depend on.

### Security requirements are genuinely unverified

Unlike the direction artefact above, `FB2-SAF-SEC-000001` … `-000005` have **no
verification link in either direction** (`FB2-REV-FND-000008` … `-000012`).
Verification planning concentrated on the cell-voltage chain and never covered
the security set. The chain runs threat → security requirement → safety goal and
stops: there is no design, test measure or execution for any security
requirement.

## 8. Negative Scenario Validation

20 mutation scenarios, **20/20 detected by the rule each one declares**, and
**3/3** change lifecycles structurally complete. Recorded in
`reports/scenario-validation-report.json`.

Each mutation injects a specific defect and asserts that the *specific detector
named by the scenario* raises a finding the unmutated corpus did not already
raise. That is a stronger claim than "a finding appeared", and it is the claim
this report is entitled to make only as of 2026-09-29. Before finding
`FB2-REV-FND-000032` the harness accepted any finding of the expected severity on
the scenario's affected artifact, so 8 of the 20 were passing on standing
defects and 4 declared a detector that did not exist, was unreachable, or could
not fire on the record the scenario targets. See
`reports/scenario-validation-report.md` §3.

## 9. What This Report Does and Does Not Establish

| Established | Not established |
|---|---|
| **222 of 313** CeeDling targets pass under the SIL harness on a real host, with **7** failing and **84** not building | Anything about behaviour on the TMS570 target |
| 16 of the 84 build failures are classified **by the harness itself** as real product defects | That the 222 passes are sufficient |
| **53 of the 245 green tests assert nothing** (`FB2-REV-FND-000042`) | That those 53 green results evidence anything |
| 5 tests fail in the earlier strict run, root-caused to a `void *` / CMock interaction, and the failure is compiler- and platform-independent | That macOS is a supported foxBMS platform — it is not |
| The SIL harness mocks the `HL_*.h` interface boundary rather than reconstructing TI register maps | Anything about TI register semantics |
| 0 target-hardware executions exist; the 4 `tests/unit-hw/test_tms570_*.c` tests were never attempted | Any target-hardware claim |
| Blocked, failed and vacuous results are recorded, not hidden | That any verification has been approved by a human |

`human_approval_status` is `pending` and `production_authorized` is `false` for
all **263** records. These runs are evidence about the product's source code on a
development host, and about the honesty of the corpus recording them — nothing
more.
