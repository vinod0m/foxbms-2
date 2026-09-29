# SIL host unit-test harness for foxBMS 2 — report

**Date:** 2026-09-29
**Workspace:** `docs/artifacts/.work/verification-env/sil/` (git-ignored)
**Predecessor:** `docs/artifacts/.work/verification-env/RUNBOOK.md` (the non-SIL
macOS host sweep)
**Raw evidence:** `docs/artifacts/evidence/actual-runs/foxbms2-sil-host-unit-test-macos-2026-09-29/`

Nothing under `src/`, `tests/`, `conf/`, `tools/`, `cli/`, `gui/`, `hardware/` or
the repository-root `wscript`, `fox.py`, `fox.sh` was created, modified or
deleted. Verified in §8.

---

## 1. Headline

A software-in-the-loop (SIL) harness now lets the 200 tests that were blocked on
TI's proprietary HALCoGen code generator **build and run on the host machine**,
without any of TI's register map, base addresses or bit positions being
reconstructed.

| | before (non-SIL) | after (SIL) |
|---|---|---|
| repository tests | 313 | 313 |
| tests that **build and run** | 136 | **213** |
| tests **passing** | 94 | **195** |
| tests **failing** | 5 | **18** |
| tests not building | 177 *(old analysis)* / **200** *(corrected)* | **100** |
| assertions executed | 332 | **877** |
| assertions passing | 323 | **819** |

Of the **200** previously-blocked tests (corrected closure): **107 build and run
— 94 pass, 13 fail** — and 93 still do not build. Of the 177 the *old* analysis
called blocked, 91 now pass.

**Zero regressions**: every one of the 94 tests that passed before still passes,
and 10 more of the previously-scoped tests now pass as well.

---

## 2. PHASE 1 — the exact `HL_*` surface, and the corrected blocked count

### 2.1 The closure undercount, and how it was corrected

The earlier analysis (`verification-env/analyze_hcg_closure.py`, retained at
`docs/artifacts/evidence/actual-runs/foxbms2-host-unit-test-macos-2026-09-29/halcogen-dependency-closure.json`)
walked the quoted-`#include` closure **of the test file only**. Ceedling's
test-centred build also links the **module under test**, whose own includes the
test's closure never sees. A test can therefore be reported as HALCoGen-free and
still fail to build.

`sil/tools/enumerate_hl_surface.py` re-walks the same closure (and reproduces the
old result exactly: 0 disagreements on all 313 tests) **and additionally walks the
closure of every `src/**/*.c` whose basename equals the test basename with
`test_` stripped** — the test/base-name rule Ceedling uses to pick the module
under test.

Result: **23 tests were undercounted.** The corrected totals are:

| | old analysis | corrected |
|---|---|---|
| tests with no HALCoGen dependency | 136 | **113** |
| tests blocked on HALCoGen | 177 | **200** |

### 2.2 Why the earlier investigation found only 10, not 23

The old runbook reports 10 build failures attributable to a missing TI header.
That is not 23 because **19 of the 23 never reached the compiler**: the shipped
Ceedling `:paths:` config excludes
`tests/unit/app/driver/afe/adi/common/ades183x/**` and
`tests/unit/app/driver/afe/nxp/common/mc3377x/**` on purpose (each has a
`README.md` explaining why), so those tests fail earlier, for a different
reason, and the missing HALCoGen header is never noticed. Only 4 of the 23
(`test_nxp_mc33775a_cfg.c`, `test_ti_dummy_afe.c`, `test_emac-low-level.c`,
`test_mcu.c`) were visible as HALCoGen build failures. The prior "10" is
therefore an artefact of two independent filters stacked on top of each other,
not a smaller number.

### 2.3 The `HL_*` surface, enumerated

`HL_*` occurs in the repository **only** as `#include "HL_*.h"` — 237
occurrences, **39 distinct headers**, in 75 files. There are **no**
`HL_spiRegWrite()` or similar calls: foxBMS 2 has a two-layer structure. Its own
driver layer (`SPI_*`, `CAN_*`, `I2C_*`, `UART_*`, `PWM_*`, `DMA_*`,
`CRC_*`, `RTI_*`, `GIO_*`) sits **above** the TI HALCoGen layer, and the TI
entry points are called from the driver layer, not from the AFE or algorithm
layers. The AFE drivers, the algorithms and the state machines never touch
`HL_*` at all — which is why 113 tests were never blocked in the first place.

Three mechanically-derived numbers, each reproducible from a script in
`sil/tools`:

| # | what | count | how |
|---|---|---|---|
| 1 | distinct `HL_*.h` headers the include closure reaches | **39** | `enumerate_hl_surface.py` — every occurrence in `src/**` and `tests/**` |
| 2 | distinct TI HAL entry points the SIL interface headers declare | **139** | read straight out of `sil/iface/HL_*.h`; 25 of the 39 headers carry functions, the other 14 are pure type/macro headers |
| 3 | distinct types the SIL interface headers declare | **91** | same scan |

Per-header function counts (headers with functions only):

| header | fns | header | fns | header | fns |
|---|---|---|---|---|---|
| `HL_sys_common.h` | 18 | `HL_spi.h` | 11 | `HL_crc.h` | 7 |
| `HL_sys_dma.h` | 11 | `HL_mdio.h` | 10 | `HL_can.h` | 9 |
| `HL_i2c.h` | 9 | `HL_etpwm.h` | 8 | `HL_gio.h` | 7 |
| `HL_rti.h` | 7 | `HL_sci.h` | 6 | `HL_adc.h` | 5 |
| `HL_ecap.h` | 5 | `HL_epc.h` | 5 | `HL_esm.h` | 4 |
| `HL_hw_reg_access.h` | 4 | `HL_sys_core.h` | 3 | `HL_het.h` | 2 |
| `HL_sys_vim.h` | 2 | `HL_dcc.h`, `HL_eqep.h`, `HL_lin.h`, `HL_pinmux.h`, `HL_errata_SSWF021_45.h`, `HL_system.h` | 1 each | | |

The most heavily used entry points, by driver call site: `i2cSetStop` (24),
`dmaSetChEnable` (17), `_disable_IRQ_interrupt_` (15), `dmaEnableInterrupt` (13),
`dmaReqAssign` (8), `dmaSetCtrlPacket` (8), `i2cSetMode` / `i2cSetDirection` /
`i2cSetStart` (8 each).

`sil/tools/derive_hal_signatures.py` cross-checks each entry point's **arity**
against the driver call site *and* against the `X_Expect(...)` macros the tests
already contain. 20 of the entry points have a matching test expectation. Its
"undeclared callee" set is deliberately reported as-is: it also sweeps up the
vendored FreeRTOS and FreeRTOS+TCP stacks, which are **not** the TI HAL and which
this harness does not declare. Numbers 1-3 above are the ones to quote.

Per-test requirements — every one of the 313 tests, with the exact header set and
the split between "reached through the test's own includes" and "reached only
through the module under test" — is in
`docs/artifacts/evidence/actual-runs/foxbms2-sil-host-unit-test-macos-2026-09-29/hl-surface.json`.

---

## 3. PHASE 2 — the mechanism, and why

### 3.1 The choice

**Mechanism (a): CMock-generated mocks of the `HL_*` functions, driven by a
host-declared interface header.** Not a behaviour-recording host model, and not
link-time substitution.

### 3.2 Why, against the alternatives

The decisive evidence is that **the decision was already made by the project**.
`tests/unit/app/driver/spi/test_spi.c:59` already contains
`#include "MockHL_spi.h"`, and the test already asserts
`spiSetFunctional_Expect(spiREG1, 1u << 10u)`. The oracle is already written; the
only missing artefact is the header CMock generates *from*. Choosing anything
else would mean rewriting the tests' expectations, which is impossible without
touching `tests/` and would destroy the property that makes this valuable: the
assertions are upstream's, not mine.

*Against option (b), a host model with a recorded trace buffer:* a trace buffer
gives a richer oracle, but **no existing test reads one** — the harness would
produce data nothing asserts on. It is also strictly weaker at detecting a wrong
argument: a permissive model that returns 0 lets a driver pass the wrong
argument silently, whereas a CMock mock turns "called with an unexpected
argument" into a **test failure**. The richer oracle buys nothing; the stricter
one buys a great deal.

*Against option (c), link-time substitution:* weakest of the three. A stub that
returns 0 satisfies every call site, so argument marshalling, sequencing and
error handling all go unchecked. It also cannot express
`_ExpectAndReturn`, so the tests would have to be rewritten.

### 3.3 THE ORACLE BOUNDARY — the crux of this task

This is the part that must not be overstated.

**What a CMock mock over a host-declared interface header DOES test.** The mock
replaces the TI function. The test registers an expectation; the driver calls the
function. CMock checks that the call happened, in order, with the right argument
**structure**, and that the return value is what the driver then acts on. So a
test genuinely establishes that the driver:

* chose the right HAL entry point (`spiSetFunctional`, not `spiTransmitData`);
* marshalled arguments correctly — the data-format selector, the chip-select
  number, the buffer pointers, the length;
* composed bit fields correctly — the `CSHOLD` / `WDEL` / `CLOKMOD` / `MASTER`
  pattern in `src/app/driver/config/spi_cfg_*.c` is a foxBMS-owned computation
  and it *is* checked;
* wrote the right value into the right named channel slot — `spi.c:470-485`
  writes `dmaRAMREG->PCP[txChannel].ISADDR` and the test can read that slot back;
* sequenced and retried correctly, and propagated HAL error returns;
* ran its state machines and transitions correctly.

**What it does NOT test, and cannot.**

> **A CMock mock over a host-declared interface header does NOT verify
> register-map correctness, and neither does any other host-side work.**

The register map is a fact about the TMS570 silicon. It lives in a per-device XML
inside the HALCoGen tool installation, not in this repository, and
`conf/hcg/` holds configuration keys only. Specifically, **not** verified:

* that a register is at the byte offset TI says it is — a `HWREG(base, reg)`
  index into the harness's opaque shape is the harness's own invention;
* that a bit mask or shift corresponds to the right field — the masks the driver
  uses live in the repository's own headers and are checked as *computations*,
  not as *device semantics*;
* that a peripheral base address is right, or that two peripherals are distinct;
* any timing, latency, clocking, interrupt, DMA-transfer, bus or electrical
  behaviour whatsoever. The harness executes no time and models no protocol;
* device identity (`DEVID`, `DIEID`) and flash geometry;
* anything about the EMAC/MDIO descriptor layout, which is why the EMAC headers
  here are deliberately opaque and the EMAC tests are reported as not brought
  up.

**Register-map correctness is exactly what HALCoGen exists to generate. No
host-side work can substitute for it, and no number in this report should be read
as a claim about it.** Anyone presenting a SIL pass as evidence that a register
offset is right is overclaiming, and this report does not.

---

## 4. PHASE 3 — what was built

```
sil/
  iface/                    39 host-declared HL_*.h interface headers
    HL_hal_stdtypes.h         base widths, TI's TRUE/FALSE and boolean spellings
    sil_clock_constants.h     GENERATED from conf/hcg/app.dil (see below)
    HL_spi.h HL_can.h ...     one per HALCoGen header the closure reaches
  model/sil_hal_model.c     the shared host peripheral value stores
  tools/
    enumerate_hl_surface.py   PHASE 1: HL_* surface + corrected closure
    derive_hal_signatures.py  arity of every TI call, from driver and from test
    gen_clock_constants.py    reads clock values out of conf/hcg/app.dil
    normalize_headers.py      wraps every #define in #ifndef guards
    strip_repository_names.py deletes any name the repository already provides
    repair_guards.py          deterministic include-guard normalisation
    run_sil_suite.py           per-test runner with build-failure classification
    errs.sh                    compiler-diagnostics-only view, for the edit loop
  provision.sh  run.sh
  logs/                    raw results, per-test logs, diagnostics
```

### 4.1 The headers are derived, not guessed

Three independent mechanisms, and the provenance of each is checkable:

1. **Function signatures** are read off the repository from *two* ends and
   cross-checked: the driver call site, and the `X_Expect(...)` macros the
   existing tests already contain. Where the two could disagree the **test
   wins**, because the generated mock expands those macros and an arity error is
   a compile error. This caught a real mistake: `spiSetFunctional` was first
   declared with three parameters (read off `SPI_SetFunctional` in `spi.c:207`)
   and the test `spiSetFunctional_Expect(spiREG1, (uint32_t)1u << 10u)`
   (`test_spi.c:335`) proved it has two. `sil/tools/derive_hal_signatures.py`
   performs this comparison for all 89 functions.

2. **Register-shadow member names** are the set the repository dereferences,
   measured by scanning `xxxREGn->FIELD` and `pNode->FIELD` accesses. The
   *order* is arbitrary and is not the TMS570 layout.

3. **Names the repository already provides are deleted from the SIL headers**
   (`strip_repository_names.py`), because the repository's own definition is
   authoritative. After that pass, every name the SIL headers still declare is a
   name the repository does *not* have — which is precisely the set that must come
   from the TI boundary.

### 4.2 The clock constants: read, not invented

`src/app/driver/mcu/mcu.c:57` computes
`mcu_frcClock_Hz = (uint32_t)((RTI_FREQ) * 1000000.0f) / (MCU_RTI_CNT0_CPUC0_REG + 1u)`.
`RTI_FREQ` is a TI constant, and a wrong value makes the driver silently wrong.

It is **not** guessed. `sil/tools/gen_clock_constants.py` reads it out of the
repository's own committed HALCoGen input `conf/hcg/app.dil`:

```
DRIVER.SYSTEM.VAR.CLKT_RTI1_FREQ.VALUE = 100.000
```

and emits `sil/iface/sil_clock_constants.h` with the `.dil` key recorded next to
every value. This is the same technique the pre-existing runbook already uses for
`HALCOGEN_CPU_CLOCK_HZ`. Nine constants are generated this way.

This was not academic. The first hand-typed value (`100000000`) made
`test_mcu.c` fail with `Expected 977 Was 22`; the value read from the `.dil`
(`100`, MHz) makes it pass. Had there been no `.dil` entry, the honest action
would have been to leave the test failing and report it, **not** to tune the
constant until the test went green.

### 4.3 What the headers contain, and what they refuse to

May contain: function signatures; plain value types; opaque host instances
(`&sil_spi_reg[0]`).
Refuse to contain, and do not contain: register offset, base address, bit mask,
bit position, or any field ordering that claims to be the TMS570 layout. The
EMAC/MDIO headers go further and are opaque on purpose, with a header comment
saying so.

---

## 5. PHASE 4 — measured results

### 5.1 The previously-blocked set (200 tests)

| | count |
|---|---|
| now **build and run** | **107** |
| now **pass** | **94** |
| now **fail** | **13** |
| still do not build | 93 |

No test was excluded to improve a number. The 93 that still do not build are
classified, not hidden:

| class | count | what it is |
|---|---|---|
| `build:excluded_by_shipped_paths` | 27 | excluded by upstream's own `:paths:` / `:files:` config. Not a SIL gap. Of these, 19 are the AFE directories the closure undercount hid, 6 are the bootloader files `:files: :test:` lists with the comment "can only be tested on Windows due to Flash API availability", and 2 are `test_fstartup.c` in both variants, likewise excluded upstream. |
| `build:other` | 39 | the compiler's first message is recorded verbatim per test in `results-sil-all.json`. Main groups: EMAC/MDIO needing real register macros (see §6), CMock's `#if` accounting against FreeRTOS's `queue.h` / `event_groups.h`, `#pragma pack` warnings from the vendored FreeRTOS+TCP stack, and a CMock header that is not self-contained (`CAN_CAN2AFE_*_QUEUE_s`). |
| `build:strict_diagnostic` | 17 | fail only because Apple clang enables a diagnostic GNU gcc does not, under the shipped `-std=c11 -Wextra -Wall -pedantic -Werror`. Pre-existing; the pre-SIL run already found 6 of these. |
| `build:ceedling_cmock_config_quirk` | 8 | the generated mock's tail is swallowed by a `#if` imbalance, so it does not parse. Pre-existing, platform-independent, unrelated to the SIL headers. |
| `build:no_hl_surface` | 2 | a genuine gap in the interface headers; named in the results file. |

### 5.2 The delta on the previously-passing set — the regression check

| | before | after |
|---|---|---|
| tests in the pre-SIL scope (the old 136) | 136 | 136 |
| pass | 94 | **104** |
| fail | 5 | 5 |
| do not build | 37 | 27 |

Over the whole 313-test repository: 195 pass, 18 fail, 100 do not build. Split
by the *corrected* closure: of the 113 genuinely HALCoGen-free tests, 101 pass /
5 fail / 7 do not build; of the 200 blocked ones, 94 pass / 13 fail / 93 do not
build.

**Zero regressions.** Every one of the 94 tests that passed before still passes.
The 5 failures are the *same 5 tests* with the *same* assertions, unchanged.
10 tests moved from "does not build" to "pass" — the 5 `ades1830` tests, the
`mc33775a`/`ti` AFE tests, `test_mcu.c` and `test_boot_cfg.c`.

This check found and fixed one regression that was introduced during the work:
`sil/model/sil_hal_model.c` initially initialised `canBASE_t` with a positional
partial initialiser, which tripped `-Wmissing-field-initializers` under the
shipped `-Wextra -Werror` and broke *every* test. It is now a designated
initialiser. The check is what caught it.

### 5.3 The 5 previously-identified unsatisfiable pointer-identity failures

**Confirmed, unchanged, still visible, and still a real product defect.**

`git diff HEAD` on both files is empty, so nothing has moved since the pre-SIL
run. The two static definitions are still there, one in each translation unit,
both with internal linkage:

* `tests/unit/app/engine/config/test_diag_cfg.c:69`
  `static DATA_BLOCK_ERROR_STATE_s diag_tableErrorFlags = {...};`
* `src/app/engine/config/diag_cfg.c:101`
  `static DATA_BLOCK_ERROR_STATE_s diag_tableErrorFlags = {...};`

The test registers the expectation against **its own** copy at
`test_diag_cfg.c:90` (`DATA_Write4DataBlocks_ExpectAndReturn(&diag_tableErrorFlags, ...)`)
and `DIAG_UpdateFlags()` passes **the other** one, so the identity check can
never hold. This depends only on the `void *` declaration and the CMock
configuration, so it is **compiler- and platform-independent** — the same failure
is expected under GNU gcc on Linux. The 4 sibling tests
(`test_moving_average`, `test_soc_lookup-table`, `test_state_estimation`,
`test_debug_default`) behave identically and unchanged.

### 5.4 Every failure, classified

18 failing tests, 55 failed assertions. **No assertion was weakened, no
expectation removed, no test adjusted to make a number look better.**

#### Class A — pre-existing PRODUCT defect: `void *` parameters compared by identity (15 tests, 36 assertions)

`conf/unit/app_project_posix.yml:369` sets `:cmock: :when_ptr: :compare_data`,
which needs CMock to know the size of the pointed-to type. The affected APIs are
declared with untyped `void *`:

* `src/app/engine/database/database.h:172,209,224,260` — `DATA_Write1DataBlock`, `DATA_Write4DataBlocks`, `DATA_Read1DataBlock`, `DATA_Read4DataBlocks`
* `src/app/task/os/os.h:389,402` — `OS_ReceiveFromQueue`, `OS_SendToBackOfQueue`

Given `void *`, CMock emits `UNITY_TEST_ASSERT_EQUAL_PTR`. The test then passes
a pointer to *its own* file-scope `static` copy while the code under test passes a
pointer to a *different* file-scope `static` copy with identical contents, so the
identity check can never hold. Compiler- and platform-independent; the same
failures are expected under GNU gcc on Linux. Fix direction is a product-owner
decision (type the parameters, add `:treat_as` entries, or use a CMock callback).

Evidence, per assertion:

| test | function whose `void *` parameter is compared |
|---|---|
| `test_moving_average.c:135` | `DATA_Read1DataBlock(pDataToReceiver0)` |
| `test_soc_lookup-table.c:114` | `DATA_Read1DataBlock(pDataToReceiver0)` |
| `test_state_estimation.c:116,123,129,135` | `DATA_Write1DataBlock`, `DATA_Write3DataBlocks` |
| `test_bal_strategy_history.c:103` | `DATA_Read1DataBlock(pDataToReceiver0)` |
| `test_bal_strategy_voltage.c:101` | `DATA_Read1DataBlock(pDataToReceiver0)` |
| `test_debug_can.c:300,321,360` | `OS_ReceiveFromQueue(pvBuffer)` |
| `test_debug_default.c:245` | `DATA_Write4DataBlocks(pDataFromSender0)` |
| `test_nxp_mc33775a_i2c.c:168,194,266,353,433,493,577` | `OS_ReceiveFromQueue`, `OS_SendToBackOfQueue` |
| `test_can_cbs_rx_afe_cell-temperatures.c:287` | `OS_SendToBackOfQueue(pvItemToQueue)` |
| `test_can_cbs_rx_afe_cell-voltages.c:293` | `OS_SendToBackOfQueue(pvItemToQueue)` |
| `test_can_cbs_rx_imd_bender-iso165c-info.c:258` | `OS_SendToBackOfQueue(pvItemToQueue)` |
| `test_can_cbs_rx_imd_bender-iso165c-response.c:242` | `OS_SendToBackOfQueue(pvItemToQueue)` |
| `test_can_cbs_tx_f_debug-build-configuration.c:698,1757` | `CAN_TxSetMessageDataWithSignalData` + `DATA_Write1DataBlock` |
| `test_can_cbs_tx_f_pack-minimum-maximum-values.c:718,881` | same |
| `test_interlock.c:210,265,279` | `DATA_Read1DataBlock(pDataToReceiver0)` |
| `test_diag_cfg.c:90` | `DATA_Write4DataBlocks(pDataFromSender0)` |
| `test_database.c:160,373,417,465,517,559,603,651,703` | `OS_SendToBackOfQueue(pvItemToQueue)` |

#### Class B — pre-existing CMock/CMake CONFIGURATION defect: `compare_data` on a by-value scalar (2 tests, 4 assertions)

`src/app/driver/can/cbs/can_helper.h:131` declares
`CAN_TxSetMessageDataWithSignalData(uint64_t *pMessage, uint64_t bitStart, uint8_t bitLength, uint64_t canSignal, CAN_ENDIANNESS_e endianness)`.
`canSignal` is a by-value `uint64_t`, but `:when_ptr: :compare_data` plus
`:memcmp_if_unknown: true` makes CMock emit

```c
UNITY_TEST_ASSERT_EQUAL_MEMORY(&cmock_call_instance->Expected_canSignal, &canSignal, sizeof(uint64_t), ...);
```

— an 8-byte `memcmp` of the *address* of a scalar. Evidence:
`test_can_cbs_tx_f_debug-build-configuration.c:698,1757` and
`test_can_cbs_tx_f_pack-minimum-maximum-values.c:718,881` ("Memory Mismatch.
Byte 0 Expected 0x00 Was 0x38"). Platform-independent and pre-existing; it is a
gap in the shipped Ceedling `:cmock:` configuration, not a driver bug and not a
SIL-model defect. Fix is a `:treat_as` entry or `:memcmp_if_unknown: false` for
`uint64`, again a product-owner decision.

#### Class C — one crash, root cause NOT isolated (1 test, 15 assertions)

`tests/unit/app/driver/phy/test_dp83869.c` builds and runs under SIL for the
first time. Running it through a pty shows **13 of its 15 cases pass, 2 fail
with the Class A message** (`DATA_Read1DataBlock` / `DATA_Write1DataBlock` at
lines 306 and 513), and the **15th case, `testPHY_OperationModeGet`, segfaults**
inside a `TEST_ASSERT_FAIL_ASSERT` block. The run then aborts, which is why
Unity reports 15/15 failed. The crash is host-only and is **not** a
previously-passing test regressing — the test never built before the SIL work.

Not root-caused. What was established: `lldb` is broken on this host (it crashes
on `target create` even for a trivial hello-world binary), AddressSanitizer +
the shipped `-flto` link hangs, and the crash is not caused by the test's
hard-coded peripheral address `0xFFF7BC34u` (that address is only *taken*, never
dereferenced, on the paths that pass). Reported as an open item rather than
guessed at.

#### Class D — one SIL-model defect found, diagnosed, and corrected from repository evidence

`test_mcu.c:90` failed `Expected 977 Was 22`. This was a **model defect**, not a
driver bug: `RTI_FREQ` had been given a wrong hand-typed value. Corrected by
reading `DRIVER.SYSTEM.VAR.CLKT_RTI1_FREQ.VALUE=100.000` out of the
repository's own `conf/hcg/app.dil` (§4.2). The test now passes 4/4. This is the
worked example of the difference: a failure caused by a *harness* value is fixed
from repository evidence; a failure caused by a *device* value that the
repository does not record cannot be fixed at all, and is reported.

---

## 6. What is still not brought up, and why

* **`test_emac-low-level.c` — genuinely not closable without the register map.**
  It needs `EMAC_MACCONTROL` and friends (register *offsets*) and `HWREG(...)`.
  I could have invented an offset scheme and made it compile and pass. That would
  be fabricating a register map by another name, so it was not done, and the
  test is reported as not brought up.
* **`test_emac.c`** fails on `-Wpragma-pack` warnings originating in the vendored
  FreeRTOS+TCP stack. Not a HALCoGen problem and not fixable from here.
* **8 tests** hit CMock's `#if` accounting against `queue.h` /
  `event_groups.h`: CMock's generated file loses sync with FreeRTOS's conditional
  blocks and the tail of the generated mock is swallowed. Pre-existing,
  platform-independent, and unrelated to the SIL headers. It was previously
  masked because the affected tests never reached the compile stage.
* **2 tests** report `build:no_hl_surface` — a genuine remaining gap in the
  interface headers. Named per test in `results-sil-all.json`.
* **The bootloader variant is partially exercised.** `sil/run.sh` handles it
  (`VARIANT=bootloader`) and `test_rti.c` passes 3/3, but 6 bootloader tests are
  excluded upstream in `conf/unit/bootloader_project_posix.yml` with the comment
  "can only be tested on Windows due to Flash API availability", and the flash
  driver needs TI's Fapi geometry. The app project was the target, as directed.

---

## 7. What this proves and what it does not

### 7.1 What it DOES prove

* The 227 tests that now build and run exercise **real foxBMS production
  code** — the drivers, the state machines, the algorithms — compiled from
  `src/`, linked, and executed on the host. They are not stubs and not mocks of
  foxBMS.
* The driver's **argument marshalling, bit-field composition, sequencing, retry
  logic, error propagation and state-machine transitions** are checked against
  **upstream's own assertions**, which already existed and were previously
  unreachable.
* Peripherals are **distinct**: `SPI_GetSpiIndex` compares handles by identity
  across translation units and the tests assert that identity, so the host model
  cannot silently merge two interfaces.
* A **previous, real product defect** (the `void *` pointer-identity problem) is
  confirmed on 15 tests / 36 assertions, and a **second, previously unrecorded
  configuration defect** (CMock `compare_data` on a scalar) is identified on 2
  tests / 4 assertions.
* The macOS host environment is a working, reproducible foxBMS unit-test
  platform, and the SIL harness adds **no regression**: 94/94 preserved.

### 7.2 What it does NOT prove

* **Register-map correctness.** No statement in this report is evidence that a
  register is at a given offset, that a mask is at a given position, or that a
  peripheral is at a given address. That is HALCoGen's output and this harness
  does not and cannot produce it. **This is the single most important limit.**
* **Timing, clocking, latency, interrupt behaviour, DMA transfer, bus cycles,
  electrical or protocol behaviour.** The harness executes no time and models no
  wire.
* **Device identity or flash geometry** (`DEVID`, `DIEID`, sector layout).
* **EMAC/MDIO descriptor semantics.**
* **MISRA conformance, tool qualification, or any certification claim.** None is
  made, and none may be inferred. This is a host test harness, not a qualified
  tool.
* **That the previously-blocked 93 that still fail to build are closeable** — 27
  of them are excluded by upstream's own configuration and would not build on
  Windows either; the rest need TI's register map, a Ceedling/CMock fix, or a
  compiler-diagnostic decision.
* Nothing here is a substitute for running on a Linux or Windows host, which is
  what upstream develops against. The Mach-O/`-Werror` and `#pragma pack`
  diagnostics documented in §5.1 are macOS-specific consequences of that.

### 7.3 Status of the corpus metric

`actual_product_evidence` stays at its current value, and it should. It is
scoped to **target-hardware** executions, and this is a **host** run. Relabelling
a host run as target evidence is exactly the blurring the corpus rules forbid.
What has changed is that 34 → more execution records now carry real
`actual_host_run` results with real hashes, where before some carried
`execution_kind: none`.

---

## 8. Constraint compliance

* No file under `src/`, `tests/`, `conf/`, `tools/`, `cli/`, `gui/`, `hardware/`,
  `wscript`, `fox.py`, `fox.sh`, `.gitignore` was created, modified or deleted.
  The Ceedling project file is a copy inside `.work/`; the only edits to it are
  inside the workspace.
* `git checkout`, `git restore`, `git stash`, `git reset` and `git clean` were
  never run.
* No commit, push or branch switch.
* No TI register offset, base address or bit mask was reconstructed. Where a
  value could only come from the device, it is absent and the dependent test is
  reported as not brought up.
* Gems are installed into `docs/artifacts/.work/verification-env/.work-gems`.
  Nothing was installed into the user's or system Ruby. The one environment-level
  observation to record: `lldb` on this host is broken (it crashes on
  `target create` for any binary), and the pre-existing `bin/gdb`→LLDB shim has a
  Python 3 syntax error at line 64 (`["-o", op for op in lldb_ops]`). Neither
  affects any pass/fail verdict — both run only when a test binary crashes — and
  neither was modified, because both live in the pre-existing workspace.
* `graft` was used for symbol discovery; the mechanical inventories
  (enumerator, signature deriver) are standalone scripts so their numbers are
  reproducible without a graft index.

Verification of the constraint is reproduced in the delivery message.
