# Verification Evidence Report

**Generated:** 2026-09-29
**Baseline:** BAS-REF-001 (pinned source commit `308028fb`)
**Primary evidence:** `docs/artifacts/.work/verification-env/logs/results-strict.json`

> **This run is not target-hardware evidence, and it is not credited as such.**
> macOS is **not an upstream-supported foxBMS platform**. foxBMS 2 targets a
> Texas Instruments TMS570-family MCU with a proprietary HALCoGen code-generation
> step. The run described below is a **host run on a development machine**. It
> exercises real product source code, which makes it genuine evidence about the
> code, but it says nothing about timing on the target, about the AFE drivers, or
> about the closed-loop control behaviour. `actual_product_evidence` remains
> **0/16** and `product_verification_credit` is `false` on all 153 records.
>
> Nothing here asserts ISO 26262 conformity, ASIL capability, ASPICE capability
> level, certification, human approval or tool qualification. No human has
> approved anything in this corpus.

## 1. The Run

| Measure | Value |
|---|---|
| Host | `Darwin vinods-mbp-14.localdomain 27.0.0 Darwin Kernel Version 27.0.0` (arm64) |
| Toolchain | `ruby 4.0.7 (2026-09-15 revision 229531a6cf) +PRISM [arm64-darwin27]` |
| Run timestamp | 2026-09-29T10:30:52+0200 |
| Selection | `no_halcogen_dependency` |
| **Tests in scope** | **136** |
| **Passed** | **94** |
| **Failed** | **5** |
| Build failures | 37 |
| Assertions tested | 332 |
| Assertions passed | 323 |
| Assertions failed | 8 |

Raw data: `docs/artifacts/.work/verification-env/logs/results-strict.json`.
Run procedure and full account: `docs/artifacts/.work/verification-env/RUNBOOK.md`.

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

## 4. The 177 Blocked Tests

Of **313** repository tests, **136** were in scope and **177 are blocked** on
HALCoGen (`docs/artifacts/.work/verification-env/logs/hcg-closure.json`).

The blocked tests reach **34 distinct `HL_*.h` headers**, including
`HL_adc.h`, `HL_can.h`, `HL_crc.h`, `HL_dcc.h`, `HL_ecap.h`, `HL_epc.h`,
`HL_eqep.h`, `HL_errata_SSWF021_45.h`, `HL_esm.h`, `HL_etpwm.h`, `HL_gio.h`,
`HL_hal_stdtypes.h`, `HL_het.h`, `HL_i2c.h`, `HL_lin.h`, `HL_mdio.h`,
`HL_pinmux.h` and `HL_reg_adc.h` among them.

**Reconstructing 34 proprietary TI register maps and driver APIs from memory
would fabricate the very thing these tests exist to verify, so it was not done.**
The blocker is instead characterised precisely: `analyze_hcg_closure.py` records,
for every one of the 313 tests, exactly which HALCoGen headers it needs.

### To unblock

- **(a)** a real HALCoGen run on `conf/hcg/app.hcg` — requires a TI licence; or
- **(b)** a Linux host, where the ELF compiler accepts the TI section attributes
  unchanged. This is the path upstream already documents, and the
  reconstruction in §5.2 of the RUNBOOK would not be needed there.

Docker is available (`Docker version 29.8.0`), so option (b) is viable. It was
**not** built, because native macOS succeeded and the deliverable priority puts
native first. A Linux container would in any case need the same HALCoGen output
for the 177 remaining tests, so it would not unblock them by itself.

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
reads **0/16**, and the tool's own detail string states the reason: *execution_kind
has no target-hardware member, so none can be claimed (blocked, not fabricated)*.

Of **25** execution records:

| Class | Count | Credit |
|---|---|---|
| host / simulation | 13 | Real product code on a development host. **Not** target hardware. |
| `synthetic_fixture` or `none` | 12 | Synthetic or blocked. No product credit. |
| undeclared | **0** | — |
| **target hardware** | **0** | — |

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

16 test measures cover 7 distinct FSRs (`verification_planning` = 16/7, a ratio
rather than a score).

- **`as_is`:** 5 test measures, 14 execution records.
- **`synthetic_reference`:** 11 test measures, 11 execution records.

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

20 mutation scenarios, **20/20 detected**, and **3/3** change lifecycles
structurally complete. Recorded in `reports/scenario-validation-report.json`.

Each mutation injects a specific defect and asserts the validator catches it, so
the detectors the corpus relies on — including the `verifies`-direction rule —
are shown to be live rather than dormant.

## 9. What This Report Does and Does Not Establish

| Established | Not established |
|---|---|
| 94 of 136 in-scope tests pass on a real host | Anything about behaviour on the TMS570 target |
| 5 tests fail, root-caused to a `void *` / CMock interaction | That the 94 passes are sufficient |
| The failure is compiler- and platform-independent | That macOS is a supported foxBMS platform — it is not |
| 177 tests are blocked on proprietary HALCoGen output | Anything about those 177 tests, which did not run |
| 0 target-hardware executions exist | Any target-hardware claim |
| Blocked and failed results are recorded, not hidden | That any verification has been approved by a human |

`human_approval_status` is `pending` and `production_authorized` is `false` for
all 153 records. This run is evidence about the product's source code on a
development host, and about the honesty of the corpus recording it — nothing
more.
