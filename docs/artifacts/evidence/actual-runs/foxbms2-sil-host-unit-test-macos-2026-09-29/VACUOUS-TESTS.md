# Vacuous green tests — finding

**Status: reported, deliberately not "fixed" by writing tests.**
A test whose verdict cannot fail is not evidence. Counting it as a pass inflates
every headline number derived from the sweep, and nothing in the run output
distinguishes it from a real one-test pass.

## The file named in the task

`tests/unit/app/driver/afe/nxp/mc33775a/config/test_nxp_mc33775a_cfg.c` — 78 lines:

```
/**
 * @file    test_nxp_mc33775a_cfg.c
 * @brief   Test of nxp_mc33775a_cfg.c
 * @details TODO
 */
...
void setUp(void) { }
void tearDown(void) { }
/*========== Test Cases =====================================================*/
```

`setUp()`, `tearDown()`, `@details TODO`, and **zero** `void test*(void)`
functions. Ceedling builds it, links it, runs it, finds no test case, and prints
an overall PASS. It therefore contributes one to the pass count and no coverage
at all.

## What it should cover — and why no test was written for it

The module under test, `src/app/driver/afe/nxp/mc33775a/config/nxp_mc33775a_cfg.c`
(190 lines), contains **no functions at all**. It defines data only:

    N77X_MUX_CH_CFG_s n77x_muxSequence[N77X_MUX_SEQUENCE_LENGTH] = { … };

i.e. a default multiplexer measurement sequence of `{muxId, muxChannel}` pairs,
with entries whose `muxChannel` is `N77X_MUX_DISABLE_VALUE` when
`BS_NR_OF_TEMP_SENSORS_PER_MODULE > N77X_MUX_GPIOS_PER_MUX`, and whatever else
the file declares. `grep -cE '^[a-zA-Z_].*\(.*\) *\{'` over the module returns 0.

So there is no behaviour to exercise. A test here could only assert structural
invariants of a constant table — that every `muxId` and `muxChannel` is within
its declared range, that the table length agrees with `N77X_MUX_SEQUENCE_LENGTH`,
that disabled entries carry the sentinel, and that the table matches the
configured sensor count. Which of those are *required* to hold, and which are
incidental to this one AFE's wiring, is a decision about intent, not a mechanical
derivation from the code. Writing cases would be inventing the specification.

**A human must decide:**

1. Is a structural test on `n77x_muxSequence[]` wanted at all, or is a constant
   table better left to review than to unit test?
2. If wanted, which invariants are contractual, and what is the expected
   behaviour when `BS_NR_OF_TEMP_SENSORS_PER_MODULE` is not a multiple of
   `N77X_MUX_GPIOS_PER_MUX`?
3. Should the file be marked explicitly ignored (`TEST_IGNORE_MESSAGE`) so the
   sweep can tell "empty on purpose" from "empty and not marked as such"?

## The rest of the suite — 46 more files in the same condition

The inventory is mechanical: `sil/tools/find_vacuous_tests.py` reads every
`test_*.c` under `tests/unit/` and classifies it. It does not run anything, so it
cannot be perturbed by a concurrent build.

**82 of the 313 test files are vacuous.** 30 of those are build failures or
excluded upstream, so they inflate nothing today.

| state | green files | of which assert nothing | of which carry a real assertion |
|---|---|---|---|
| before this session's work | 222 | 47 | **175** |
| after | 245 | 53 | **192** |

The after-state count is higher, not lower, and that needs saying plainly:
**6 of the 23 tests that newly went from build failure to pass are themselves
vacuous** — `test_dma.c`, `test_dma_nxp.c`, `test_dma_uart.c`,
`test_dma_dma_group_a_notification.c`, `test_app-hl_notification.c` and
`test_bootloader-hl_notification.c`. Bringing those up is real progress (they now
compile, link and execute the product code rather than failing to build) but it
adds **no assertion coverage**, and quoting "23 tests fixed" without this
qualifier would overstate the result. The honest coverage delta is 175 → 192
green files that actually assert something.

### Class A — 24 files with zero Unity test cases

3 of the 24 are currently green; 21 are build failures or excluded. Only the 3
green ones inflate a pass count:

| file | lines | verdict reported |
|---|---|---|
| `tests/unit/app/application/config/test_ethernet_cfg.c` | 72 | pass (tested=1, passed=0) |
| `tests/unit/app/driver/afe/adi/ades1830/test_adi_ades1830_diagnostic_w.c` | 84 | pass (tested=1, passed=0) |
| `tests/unit/app/driver/afe/nxp/mc33775a/config/test_nxp_mc33775a_cfg.c` | 79 | pass (tested=1, passed=0) |

`test_nxp_mc33775a_cfg.c` is the one named in the task. The other two are
found by the same sweep and were not previously reported.

### Class B — 58 files with test cases but zero assertions

**50 are currently green** (44 before this session's work; the six added are
listed at the end of this document). These compile, link, and run a test function that
cannot fail. Most are `void testDummy(void) { }` — literally empty. Two are
worth naming because they have real bodies and are still unasserted:

* `tests/unit/app/driver/can/cbs/tx-cyclic/test_can_cbs_tx_f_bms-state-details.c`
  — 295 lines, 2 test cases, **0 assertions**.
* `tests/unit/app/driver/afe/ltc/common/test_ltc_afe_dma.c`
  — 180 lines, 1 test case, **0 assertions**.

and two whose only case exercises a callback that is expected to do nothing:

* `tests/unit/app/driver/afe/debug/can/api/test_debug_can_afe_dma.c` — `testAFE_DmaCallback`
* `tests/unit/app/driver/afe/debug/default/api/test_debug_default_afe_dma.c` — `testAFE_DmaCallback`

Full inventory: `logs/vacuous-inventory.json`, regenerated by
`python3 tools/find_vacuous_tests.py --json`.

The complete list of the 44 green ones, grouped:

* **21 `*_cfg.c` config-module tests** — `test_spi_cfg_{adi,debug,dtnxp,generic,mxm,nxp,st,ti}.c`,
  `test_can_cfg.c`, `test_can_cfg_tx_cyclic.c`, `test_contactor_cfg.c`,
  `test_dma_cfg.c`, `test_fram_cfg.c`, `test_pex_cfg.c`, `test_sps_cfg.c`,
  `test_database_cfg.c`, `test_sys_cfg.c`, `test_sys_mon_cfg.c`,
  `test_battery_cell_cfg.c`, `test_battery_system_cfg.c`, `test_ltc_6806_cfg.c`,
  `test_boot_cfg.c` — each a single `testDummy(void) { }`.
* **9 `*_dma.c` / AFE-driver stubs** — `test_adi_ades1830_{buffers,commands,commands_voltages}.c`,
  `test_nxp_afe.c`, `test_mxm_afe.c`, `test_ti_dummy_afe.c`, `test_ti_dummy.c`,
  `test_debug_can_afe_dma.c`, `test_debug_default_afe_dma.c`, `test_ltc_afe_dma.c`.
* **3 state-estimation placeholders** — `test_soe_counting.c`, `test_sof_trapezoid.c`,
  `test_sof_trapezoid_cfg.c` (`testDummy` / `test_Dummy`).
* **the rest** — `test_can_cbs_tx_f_bms-state-details.c`,
  `test_can_cbs_tx_f_debug-unsupported-multiplexer-values.c`,
  `test_can_can_message_notification.c`, `test_bender_ir155_helper.c`,
  `test_reset.c`, `test_fassert.c` (app and bootloader),
  `test_os_freertos_cache_{enabled,disabled}.c`.

## Consequence for the reported numbers

The headline pass count must be read as *"tests whose harness verdict was
green"*, never as *"tests that verify something"*. Any statement of the form
"N tests pass" that does not carry this qualifier overstates the result.

## What was NOT done, and why

No test case was written for any of the 47. For the `*_cfg.c` files the module
under test is a constant table with no functions, so any test would be an
invented specification. For the `*_dma.c` and state-estimation files the intended
coverage is not derivable from what is there. The correct remedy is a decision by
someone who knows what each module is supposed to guarantee, followed by tests
written against that decision — and, until then, an explicit marker so the sweep
reports these as `passes_with_no_test_cases` / `passes_with_no_assertions`
rather than as passes.


## The six newly-passing tests that are themselves vacuous

Bringing these up from build failure to pass is real progress — they now compile,
link and execute the product under test instead of failing to build — but each one
asserts nothing, so none of them adds coverage:

* `tests/unit/app/driver/dma/test_dma.c` — 1 test case, 0 assertions
* `tests/unit/app/driver/dma/test_dma_nxp.c` — 1 test case, 0 assertions
* `tests/unit/app/driver/dma/test_dma_uart.c` — 1 test case, 0 assertions
* `tests/unit/app/driver/dma/test_dma_dma_group_a_notification.c` — 0 assertions
* `tests/unit/app/hal/test_app-hl_notification.c` — 20 test cases, 0 assertions
* `tests/unit/bootloader/hal/test_bootloader-hl_notification.c` — 10 test cases, 0 assertions

`test_app-hl_notification.c` is the starkest: 20 test functions that call a
notification entry point and assert nothing about what it did (and its 10-case
bootloader twin is the same). Those 20 cases
exercise the arity of the calls — which is exactly the defect class this session
fixed in the interface headers — and the mock verifies the arguments, so the
arities are genuinely checked by CMock. But no test asserts an *effect*.

A human should decide what these are for. If the intent is "these entry points
must exist with these signatures and must not fault", the CMock argument checks
already do that and the file should say so. If the intent is coverage of the
notification bodies in `src/app/hal/app-hl_notification.c`, the tests need
assertions about what each one does.
