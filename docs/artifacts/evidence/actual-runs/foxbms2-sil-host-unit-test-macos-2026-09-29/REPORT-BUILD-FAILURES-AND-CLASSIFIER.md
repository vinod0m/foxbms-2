# Build-failure and measurement work on the SIL host harness

**Date:** 2026-09-30
**Workspace:** `docs/artifacts/.work/verification-env/sil/` (git-ignored)
**Predecessor:** `REPORT.md` in this directory (2026-09-29)
**Supplementary:** `RELAXED-DIAGNOSTICS.md` — per-flag justification for every
silenced diagnostic. Read that alongside this file; the flag list alone is not
the evidence.

Nothing under `src/`, `tests/`, `conf/`, `tools/`, `cli/`, `gui/`, `hardware/`
or the repository-root `wscript`, `fox.py`, `fox.sh` was created, modified or
deleted. `git status --porcelain -- src tests conf tools cli gui hardware
wscript fox.py fox.sh` is EMPTY (§9).

---

## 1. Headline

| | before | after |
|---|---|---|
| repository tests | 313 | 313 |
| **passing** | 208 | **233** |
| **failing** | 5 | **13** |
| **not building** | 100 | **67** |
| assertions tested | 877 | **1239** |
| assertions passing | 847 | **1188** |
| assertions failing | 27 | **48** |

**Zero regressions.** Every one of the 208 tests that passed before still
passes. Verified programmatically against a baseline re-measured with the
*pre-existing* harness immediately before any of this work, not taken from the
recorded file, so the whole delta is attributable.

* The 8 extra failures are tests that previously **did not build at all** and
  now build and fail. They are findings, reported (§4.3), not worked around.
* The failing count rising 5 → 13 is therefore *more* coverage, not less: 33
  more tests execute, and 8 of them discover real failures.
* Build failures fell 100 → 67 because 25 build failures now build (25 pass)
  and because 8 `build:other` cases are reclassified into precise, honest
  classes rather than a catch-all (§2.3).

**No MISRA conformance, tool qualification, certification or ASPICE capability
is claimed or implied.** The harness mocks the HAL: it verifies no register
map, timing, clocking, interrupt behaviour, DMA transfer, electrical behaviour
or device identity.

---

## 2. The measurement defect came first

An unstable classifier makes every future before/after comparison unreliable,
and a corpus that reports unstable numbers is worse than one that reports
nothing. So this was fixed before any diagnostic was touched — and fixing it
properly changed the diagnosis of several build failures.

### 2.1 What was wrong, and the evidence

The classifier keyed on `first_error`: **the first compiler message**. Two
things make that unstable.

1. Ceedling compiles a test's translation units in an order that **is not
   stable** across runs.
2. Ceedling **aborts at the first failing translation unit.**

Together those make *which* message arrives first a function of compile order.
`test_os_freertos.c` flipped between `build:other` and
`build:ceedling_cmock_config_quirk`. Measured over 24 clean runs
(`rm -rf mocks test/out test/dependencies` before each):

```
22/24 runs -> { Mockqueue.c: expected identifier or '('  (x3) }
 2/24 runs -> { test_os_freertos.c:400: -Wnon-literal-null-conversion }
```

The compiler itself is **not** the variable: invoking the identical `gcc` argv
6/6 times gave byte-identical output, 1 error, every time. The generated mocks
are byte-identical across runs too. So the variance is entirely in *what gets
reported*, not in what is produced.

### 2.2 Why sorting was not enough

The obvious fix — key on the sorted, deduped **set** of error codes — is
correct in principle, and it is what the classifier does now. But it is **not
sufficient on its own here**, and that is worth recording: because Ceedling
aborts early, the surfaced set is sometimes a strict subset. The measurement
above shows the set itself flipping 22/2, not just its order.

So the variability had to be removed **at the source**, not filtered downstream.

### 2.3 The fix

`sil/tools/sil_cc.py`, installed as the project's `:test_compiler:` (isolated
copy only). It runs the real compiler with the exact argv it was given, and
when `SIL_DIAG_COLLECT=1` and the compile **failed**, it returns 0 anyway — so
Ceedling carries on and compiles **every remaining translation unit**. The
recorded diagnostic set is then a union over all units, and is therefore
order-independent *by construction*. Each invocation appends one structured
JSON record (source, rc, every diagnostic) to a per-test `.jsonl`.

Three properties worth stating, because they are the ones that make this safe:

* **It cannot manufacture a pass.** On a failed compile the wrapper writes no
  object file, so the link fails, Ceedling produces no `OVERALL TEST SUMMARY`,
  and the runner treats a missing summary as a build failure. Independently,
  the runner now forces `build_failure` whenever *any* translation unit of the
  test failed, even if some other unit produced a summary.
* **It is transparent when not collecting.** With `SIL_DIAG_COLLECT` unset,
  `./run.sh` behaves exactly as before: same argv, same stdout, same stderr,
  same exit code.
* **The argument list is Ceedling's own.** `DEFAULT_TEST_COMPILER_TOOL`
  (ceedling-1.1.9/lib/ceedling/defaults.rb:22-32) verbatim, including the
  per-test `-I`/`-D` parameters `${5}` and `${6}` — an omission of which
  silently breaks every compile and was caught here.

The classifier now keys on the set, where a code is
`severity | -W flag | normalised message`, and **every rule is a predicate over
the whole set**, evaluated in a fixed order. Line and column numbers are
deliberately *not* part of a code, so a class survives an unrelated edit
shifting a line above it.

### 2.4 Determinism, proven

`test_os_freertos.c`, 10 consecutive runs through the full runner:

```
run  1..10: build_failure  build:clang_only_diagnostic  hash=e55d261d340b40f9
distinct (outcome, class, set-hash, set) across 10 runs: 1
```

10/10 identical outcome, class, error-set hash and error set. The
previously-recorded nondeterminism of `test_rtc.c` is gone for the same reason
and no other.

### 2.5 The recorded evidence was re-classified

`sil/tools/reclassify.py` re-derives the class for every build failure in an
existing results file. Applied to
`docs/artifacts/evidence/actual-runs/foxbms2-sil-host-unit-test-macos-2026-09-29/results-sil-all.json`:
**100 build failures re-classified.**

Every re-derived record carries
`reclassified_from_incomplete_diagnostic_set: true`, because the archived
per-test logs were recorded by the *old* harness and surface only what that run
happened to reach. That is unavoidable when re-classifying evidence gathered
without the collection wrapper, and it is marked rather than hidden. A
trustworthy set requires a re-run.

---

## 3. Task 1 — the Apple-clang-only diagnostics

Full per-flag evidence is in **`RELAXED-DIAGNOSTICS.md`**. Summary:

| flag | status | the one-line evidence |
|---|---|---|
| `-Wno-enum-conversion` | kept | GCC's equivalent needs `-Wconversion`, not `-Wall`/`-Wextra`; every site is value-preserving (both enums' first enumerator is 0) |
| `-Wno-parentheses-equality` | kept | Clang-only group; redundant parentheses change nothing |
| `-Wno-unknown-warning-option` | **added** | 3 repo `#pragma GCC diagnostic` lines name `-Wmaybe-uninitialized` / `-Wdiscarded-qualifiers`; both verified **absent from clang**, both real GCC groups |
| `-Wno-pragma-pack` | **added** | pragma **measured load-bearing** (8 of 22 structs change size without it); the flag mutes the warning, not the pragma |
| `-Wno-literal-conversion` | kept | GCC's is `-Wfloat-conversion`, not in `-Wall`/`-Wextra`; the truncation is a C semantic, identical on both |
| `-Wno-non-literal-null-conversion` | **added** | C11 6.3.2.3p3 makes `((BaseType_t)0)` a valid null pointer constant; clang adds an extra style check |
| `-Wno-incompatible-pointer-types-discards-qualifiers` | **added** | reproduces a suppression the repository itself authors in the very files that trigger it |
| `-Wno-array-bounds` | **REMOVED** | **real out-of-bounds access**, §3.2 |

**Honest limit.** There is no GNU gcc on this host — `/usr/bin/gcc` is a
symlink to Apple clang. "gcc would not emit this" is therefore established from
the diagnostic's own group membership (tested directly with clang) plus GCC's
documented default-enablement — **not** by running gcc. Where neither settles
it, the flag is **not** added and the diagnostic is reported.

### 3.1 The `#pragma pack` case, measured rather than argued

Seven tests, 133 occurrences, all in the vendored FreeRTOS+TCP stack. The
stack splits its packing into `pack_struct_start.h` / `pack_struct_end.h` so the
pragma can bracket a struct declared in a third header — which is exactly what
`-Wpragma-pack` complains about.

That is plausible, not evidence. `sil/tools/probe_pragma_pack.sh` extracts all
22 pack-bracketed struct bodies from the tree **by regex, not transcription**,
compiles them twice — with the repo's pragma and with it stripped — and diffs
`sizeof`:

```
ARPPacket_t        packed=42  natural=44   *** DIFFERENT
DHCPMessage_IPv4_t packed=230 natural=232  *** DIFFERENT
ICMPPacket_t       packed=42  natural=44   *** DIFFERENT
ICMPPacket_IPv6_t  packed=86  natural=88   *** DIFFERENT
IPPacket_t         packed=34  natural=36   *** DIFFERENT
TCPPacket_t        packed=54  natural=56   *** DIFFERENT
TCPPacket_IPv6_t   packed=74  natural=76   *** DIFFERENT
UDPPacket_t        packed=42  natural=44   *** DIFFERENT
(14 others identical; 8 of 22 differ)
```

Two conclusions. The pragma is **load-bearing** and must stay; and
`-Wno-pragma-pack` mutes the *diagnostic*, leaving the pragma in force, so the
packed layout is exactly the wire layout (`EthernetHeader_t` 14, `IPHeader_t` 20,
`TCPHeader_t` 20, `UDPHeader_t` 8, `ICMPHeader_t` 8).

**The negative control is reported because it changed the conclusion.** A first
version of this probe checked three structs' offsets and *passed even with the
pragma removed* — it was vacuous, because on this ABI those particular structs
are naturally aligned anyway. It was rebuilt to compare all 22 both ways
specifically so a vacuous result would be visible. It is not vacuous. Had it
come out at 0, the correct action would have been to **drop the flag** as
unnecessary.

### 3.2 `-Wno-array-bounds` removed: it was masking a real defect

This is the most important result in this file. The inherited list silenced
`-Warray-bounds`, which **is not a clang-only diagnostic** — GCC's is enabled by
`-Wall`, so it is not a platform artefact. Every one of the 25 sites it hid is a
genuine out-of-bounds access, verified by hand against each declaration:

| test | declaration | indices used | bound |
|---|---|---|---|
| `test_can_cbs_tx_f_cell-temperatures.c:93` | `float_t testSignalData[3u]` | 4, 6, 8, 10, 12 | **+9 past the end** |
| `…_3-temp-sensors.c`, `…_4-…`, `…_5-…` | `float_t testSignalData[3u]` | 4 … 10 | out of bounds |
| `test_can_cbs_tx_f_cell-voltages.c:92` | `float_t testSignalData[4u]` | 6, 8 | out of bounds |
| `test_diag_cbs_current.c:112-117` | `uint8_t[1]` | `BS_NR_OF_STRINGS` = 1 | off-by-one |

The `test_diag_cbs_current.c` case reads like a test author meaning to exercise
the out-of-range string index and instead writing outside the array:
`battery_system_cfg_unit_test.h:124` sets `BS_NR_OF_STRINGS (1u)`.

A build that compiles because a real warning was silenced **is a failure**, and
had this stood, 6 tests would have been reported as building while asserting on
whatever the linker placed next. Recorded as
**`FB2-REV-FND-000038`**.

### 3.3 Two problems fixed at the cause instead of suppressed

Better than any flag, because the generated/colliding code is made correct:

* **CMock misplacing `GEN_MUST_CHECK_RETURN`.** `general.h:87` hides
  `__attribute__((warn_unused_result))` behind a macro, so CMock's
  `:strippables:` (which only matches literal `__attribute__` text) keeps the
  macro name as part of the return type and emits it into a **parameter**
  position, which clang rejects. Adding `"GEN_MUST_CHECK_RETURN"` (and
  `"GEN_ALWAYS_INLINE"`) to the `:strippables:` list **upstream already uses**
  for `.FREERTOS_SYSTEM_CALL`, `(portDONT_DISCARD)` and the `TEST_LTC_*`
  macros makes CMock emit a correct prototype. **6 tests: build_failure → pass.**
* **The harness's own `BIG_ENDIAN`.** `HL_hal_stdtypes.h` defined
  `LITTLE_ENDIAN`/`BIG_ENDIAN`, which are a device fact the harness has no
  business stating, were referenced nowhere, and collided with a copy-paste
  leftover in `test_ltc_afe.c:86`. Both **deleted**; the response to "my header
  collides with a test" is to remove the duplicate, not to mute the warning.

Two more harness-header defects, same category: `TRUE`/`FALSE` were defined as
`((bool)true)`/`((bool)false)`, which is **not valid in `#if`**, and the
repository uses `TRUE` in `#if` directly (`bms.c:1188,1242,1489,1523`); and
`NULL_PTR` is now taken from the repository's own `fstd_types.h:78` by
`#include` rather than declared by the harness, which is what
`strip_repository_names.py` requires (5 tests were blocked on it).

### 3.4 Deliberately not silenced

| diagnostic | why not |
|---|---|
| `-Warray-bounds` (6 tests) | real OOB; GCC's is in `-Wall` |
| `-Wtautological-pointer-compare` (1) | `mxm_17841b.c:707` compares an **array** member against `NULL`, always true. gcc's `-Waddress` is in `-Wall` and plausibly covers it, so no difference is established |
| `-Wmissing-field-initializers` (3) | in `-Wextra` in **both** compilers, so not a platform difference by default-enablement |
| `-Wunused-but-set-variable` (3) | same — in `-Wall` in both |
| `-Wabsolute-value` (1) | `rtc.c:272` calls `abs()` on a `time_t` difference: benign on the 32-bit target, truncating on a 64-bit host. Real; a product change |
| `section` attribute (1) | `version.h:83` is a bare ELF section name; Mach-O cannot express it. A hard error that **no `-W` flag can suppress** (tested). Not worked around by overriding the macro, because its purpose is telling the *target* linker script where to place the version block — the one thing the host cannot verify |

---

## 4. Task 2 — the 8 FreeRTOS/CMock tests: **resolved, 7 of 8**

### 4.1 The mechanism, confirmed

`FreeRTOS.h:589-591` declares three functions as **empty function-like
macros** when `configQUEUE_REGISTRY_SIZE < 1`. That macro is defined
**nowhere in the repository** (verified by search over `src/`, `tests/`,
`conf/`), so `FreeRTOS.h:585` defaults it to `0U` and the three are compiled
out **on every platform, including upstream's gcc builds**. CMock cannot
evaluate that macro-valued condition, correctly generates mocks for all three,
and the preprocessor then applies the empty macros to CMock's own definitions —
consuming the function name and its parameter list and leaving three stranded
braces. Neither component is individually faulty; they disagree and neither
diagnoses it. This part of the recorded analysis stands.

### 4.2 Why it *is* resolvable in the harness

The recorded verdict was "the fix belongs to the project's Ceedling or FreeRTOS
configuration — a product decision". On inspection that was **too strong**, for
a reason the earlier analysis did not have: because the functions are compiled
out, the declarations CMock is mocking are **unreachable**, and the tests
reference **none** of the three names (verified: zero hits). CMock's definitions
are pure dead weight that happens to be preprocessed away.

CMock's `:includes_h_post_orig_header:` injects a header immediately **after**
the original one — the only point at which the macros are defined and the
generated definitions are not yet compiled (`cmock_generator.rb:163-164`).
`sil/shim/sil_cmock_queue_registry_shim.h` `#undef`s them there, each guarded on
the macro being defined, so it is inert for any build that enables the registry.

**Result: 7 of 8 now build and pass** — `test_os.c` (10 assertions),
`test_os_freertos.c` (26), both `test_os_freertos_cache_*` (1 each). The 8th,
`test_uart.c`, fails for a **different** and separately reported reason
(`-Wimplicit-int` and a parse error in a generated mock) and is not counted.

**Stated plainly, so "resolved" is not over-read:** this is a harness
accommodation for a third-party disagreement. It is **not** a claim that the
queue registry works — the registry is compiled out and this harness verifies
**nothing** about it. `FB2-REV-FND-000036` updated to revision 2, withdrawing
its "deferred" verdict for this half.

---

## 5. Task 4 — the 28 exclusions, verified

Not asserted: `sil/tools/verify_exclusions.py` loads
`conf/unit/<variant>_project_posix.yml`, collects the negative `:paths:` and
`:files: :test:` entries, and matches each test against the config for **its own
variant** (borrowing the other variant's entries would be exactly the unfounded
match this exists to catch).

| | count | what |
|---|---|---|
| **genuine upstream exclusions** | **27** | see below |
| **not a test at all** | **1** | `tests/unit/support/test_fake_functions.c` |
| **genuine failures among the 28** | **0** | |

The 27, by the exact config entry that causes each:

| n | config entry | justification |
|---|---|---|
| 13 | `app_project_posix.yml:68` `ades183x/**` | `ades183x/README.md`: *"All test files in this directory are dummy test files"* |
| 6 | `app_project_posix.yml:71` `mc3377x/**` | `mc3377x/README.md`: same wording |
| 1 | `app_project_posix.yml:100` `app/main/test_fstartup.c` | *"can only be tested on Windows due to HALCoGen availability"* |
| 7 | `bootloader_project_posix.yml:78-84` | `main/test_fstartup.c` (same comment), `driver/config/test_flash_cfg.c`, `driver/flash/test_flash.c`, `engine/boot/test_boot.c`, `engine/boot/test_boot_helper.c`, `engine/can/test_can_cbs.c` (*"can only be tested on Windows due to Flash API availability"*), `main/test_main.c` |

**The 28th is not an upstream exclusion and not a failure.**
`tests/unit/support/test_fake_functions.c` matches no negative entry. It lives
in the `:support:` tree, declares **no Unity test function** (only
`FAKE_Memset` / `FAKE_Memcpy` and an empty Test Cases section), and
`conf/unit` removes `tests/unit/support` from `:paths: :test:` while adding it as
`:support:`. It is enumerated **only because the harness globs `test_*.c`**. It
is a harness enumeration artefact and should never have been counted as a test.

The class is renamed `build:excluded_by_shipped_paths` →
`excluded:upstream_config`, because these are not build failures and must not
be counted as such in any report.

---

## 6. Before/after: every `build_failure_class` accounted for

| before (n) | after (n) | what happened to it |
|---|---|---|
| `build:other` **39** | `build:other` 0 | **dispersed**, into precise classes below. Not one test changed status for this reason; the bucket was a catch-all that hid the real causes. |
| — | `excluded:upstream_config` **28** | was `build:excluded_by_shipped_paths`. Renamed, and now **verified** (§5): 27 upstream + 1 not-a-test, 0 real failures |
| — | `build:real_defect_out_of_bounds_array_index` **6** | was hidden by `-Wno-array-bounds` / mis-bucketed as `strict_diagnostic`. **Real defect**, now visible as one |
| — | `build:undeclared_identifier` **8** | was spread across `no_hl_surface` (2) + `other`. Missing declarations: device facts the harness must not invent |
| — | `build:real_defect_macro_arity` **5** | was in `other`. Real wrong-arity function-like macro invocation |
| — | `build:strict_diagnostic_both_compilers` **6** | **new class, deliberately**: `-Wmissing-field-initializers` (3) and `-Wunused-but-set-variable` (3) are in `-Wall`/`-Wextra` in **both** compilers, so they were never the clang-only thing this bucket claimed |
| — | `build:real_defect_implicit_function_declaration` **3** | was in `other`. C99 removed implicit declarations; an error on both compilers |
| — | `build:sil_interface_header_mismatch` **3** | was in `other`. A gap or error in `sil/iface/`, not a diagnostic about repository code |
| — | `build:real_defect_implicit_int` **2** | was in `other`. Invalid in C99+ on both compilers |
| — | `build:link_failure` **2** | was in `other`. Every TU compiled; the **link** failed. Distinct cause, own bucket |
| `build:strict_diagnostic` **23** | `build:clang_only_diagnostic` **0** | **fully eliminated.** 25 of the tests in and behind this class now build; the 8 that were *mislabelled* (see below) moved to the both-compilers and real-defect classes, and the genuinely clang-only remainder is silenced and passes. Final measured count in this class: **0** |
| `build:ceedling_cmock_config_quirk` **7** | `build:cmock_freertos_macro_erasure` **0** | **eliminated** by the CMock post-orig shim (§4). 7 of 7 resolved |
| `build:no_hl_surface` **1** | `build:no_hl_surface` **0** | folded into `build:undeclared_identifier`; the name claimed a cause the classifier could not actually distinguish |
| — | `build:product_tautological_guard` **1** | **new class**, for a real smell: `mxm_17841b.c:707` compares an array member to `NULL` |
| — | `build:real_defect_absolute_value_truncation` **1** | **new class**: `rtc.c:272` `abs()` on `time_t` |
| — | `build:real_defect_excess_initializers` **1** | was in `other` |
| — | `build:not_buildable_on_macos_object_format` **1** | **new class**: `version.h:83` ELF section on Mach-O |

Note the two rows that did **not** simply shrink:

* `build:strict_diagnostic` was a class defined as *"Apple-clang-only
  diagnostic promoted by `-Werror`"*. That description was **false for 8 of its
  23 members** — they were `-Wmissing-field-initializers` (3) and
  `-Wunused-but-set-variable` (3) and 2 more, all of which are in
  `-Wall`/`-Wextra` in **both** compilers. Those 8 now sit in
  `build:strict_diagnostic_both_compilers`, where the class name cannot mislead.
* `build:other` went 39 → 0, but **not** because those tests were fixed. It was a
  catch-all; the same 39 tests are still mostly not building, now in 12 named
  classes each with a documented cause. The count falling is a gain in
  *attribution*, not in *coverage* — stated plainly because a 39 → 0 line in a
  before/after table would otherwise read as 39 tests fixed.

**Net:** 100 → 67 build failures, and the 67 are now in 12 named, honest classes
with a documented cause each, instead of 5 buckets one of which was a catch-all.

---

## 7. The 13 failing tests

The 5 previously-red tests are unchanged and still red
(`test_debug_can.c`, `test_nxp_mc33775a_i2c.c`,
`test_can_cbs_rx_f_afe_cell-temperatures.c`, `…_voltages.c`, `test_dp83869.c`).

The 8 new ones **now build and fail**, and are reported rather than worked
around: `test_bms.c` (3), `test_redundancy.c` (1), `test_adi_ades1830.c` (3),
`test_can_cbs_rx_f_debug.c` (2), `test_can.c` (5), `test_i2c.c` (4),
`test_diag.c` (1), `test_NetworkInterface.c` (2). Most are the already-recorded
`void *`-identity and `compare_data` defects, now visible because the build
problems that masked them are fixed. **No assertion was weakened, no
expectation removed, no threshold adjusted.**

---

## 8. Two harness defects worth recording

**`sil/run.sh`'s `project.yml` rewrite was not correctly idempotent, and the
same mistake was made three times in three places.** A cleanup step removed a
YAML **key line** but left its **body**; the orphan parsed as a sibling of the
parent mapping and Ceedling reported `Malformed YAML content ... line 16`,
which points nowhere near the cause. One variant silently dropped the
`sil_model` support path, removing `sil_hal_model.o` from the link line and
producing a **62-test "regression" that was not a regression at all**; another
*replaced* the shipped `:cmock: :strippables:` list instead of extending it,
discarding five entries the project ships and costing a `test_timer.c`
regression.

Fixed: `drop_key_any()` / `read_key_region()` remove a key together with its
body and handle both YAML shapes the two variants use; `:strippables:` is now
**extended**; the rewrite **parses its own output** and aborts with a precise
message if the YAML is invalid; and it **asserts** that every SIL entry point
(`sil_hal`, `sil_shim`, `sil_model`, `FOXBMS_HOST_SIL`, the port shim) and every
shipped strippable survived. Verified idempotent over 8 consecutive cycles
against **both** `conf/unit` configs with no duplicates. This is exactly the
drift that produces irreproducible results, so it is recorded rather than
quietly repaired.

*(Process note, recorded because it produced a bad measurement: two full sweeps
in this work were run while harness inputs were being edited, which contaminated
both. The numbers in §1 are from a final sweep run with **no** concurrent
edits.)*

---

## 9. Constraint compliance

* `git status --porcelain -- src tests conf tools cli gui hardware wscript
  fox.py fox.sh` → **EMPTY**. The Ceedling project file is a copy inside
  `docs/artifacts/.work/`; `provision.sh` `cmp`s it against the shipped file
  and the rewrite only ever edits the copy.
* `git checkout`, `git restore`, `git stash`, `git reset`, `git clean` were
  **never** run.
* No commit, push or branch switch.
* `conf/unit/app_project_posix.yml` and `conf/unit/bootloader_project_posix.yml`
  unmodified.
* No TI register offset, base address or bit mask was reconstructed. Where a
  value could only come from the device it is absent and the test is reported
  as not brought up.
* Two modifications visible in `git status` are **not** mine and were left
  alone: `.gitignore` (a `/graft/` line, mtime 23:33, before this work began)
  and `graphify-out/cache/last_query_stamp` (a cache stamp).
* **No MISRA conformance, tool qualification, certification or ASPICE
  capability claim is made or implied.** The harness mocks the HAL and
  verifies no register map, timing, clocking, interrupts, DMA, electrical
  behaviour or device identity.
