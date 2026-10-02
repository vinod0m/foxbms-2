# foxBMS 2 host unit tests on macOS — runbook

**Status: working.** The suite was made runnable natively on macOS arm64 and
executed for real. This document is the recipe, the results, and the honest
account of what still does not run and why.

Everything in this workspace is disposable. No file under `src/`, `tests/`,
`conf/`, `tools/`, `cli/`, `gui/`, `hardware/`, nor the repository-root
`wscript`, `fox.py` or `fox.sh`, was created, modified or deleted.

---

## 1. Headline result

Two full sweeps were run, each executing every test in its own Ceedling
invocation so that every verdict is individually attributable and every raw log
is retained.

| | strict (shipped flags) | extended (relaxed clang diagnostics) |
|---|---|---|
| tests attempted | 136 | 136 |
| **tests passed** | **94** | **98** |
| **tests failed** | **5** | **7** |
| tests that do not build | 37 | 31 |
| assertions executed | 332 | 391 |
| **assertions passed** | **323** | **380** |
| **assertions failed** | **8** | **10** |

The 5 strict failures are **not** artifacts of the macOS adaptation. All five
share one root cause, established from the sources, and it reproduces under any
compiler — see §7.

Scope: the repository has 313 `test_*.c` files. 136 of them have an include
closure that touches no HALCoGen-generated header and were therefore in scope.
The other 177 are blocked on proprietary TI code generation and are not
stubbed — see §6.

Raw evidence: `docs/artifacts/evidence/actual-runs/foxbms2-host-unit-test-macos-2026-09-29/`
(`results-strict.json` + `logs-strict/`, and `results-relaxed.json` + `logs-relaxed/`).
The two sweeps write **separate** log trees so a record can never cite the
other run's log; every one of the 16 recorded hashes was re-verified against
the file on disk.

---

## 2. What was actually wrong

The prior corpus note said the suite was blocked on macOS because
"macOS unsupported by fox.sh; Ceedling 1.1.8 confirmed failing config validation
here". Both halves of that are now resolved, and the real cause was different.

### 2.1 `project.yml` was never missing — it is named differently

`conf/unit/app_project_posix.yml` **is** the Ceedling project file. It is
shipped in the repository at HEAD (and in upstream v1.11.0). `fox.py ceedling`
copies it to `build/<variant>_host_unit_test/project.yml` and runs Ceedling
there — see `cli/cmd_embedded_ut/embedded_ut_impl.py:64-120`.

Searching the working tree for `project.yml` finds nothing, because the file
only ever exists under that name in the generated build directory. The older
commits that `git log --diff-filter=D -- '*project.yml'` surfaces are deletions
of Ceedling's **own** example/test `project.yml` files from the previously
vendored `tools/vendor/ceedling/` tree, not of foxBMS's configuration.

The project file is complete and 441 lines: full `:cmock:`, `:gcov:`,
`:command_hooks:`, per-test `:defines:`, and `:tools: :test_linker:`
(`gcc ... -flto`).

### 2.2 The macOS block is a hard `SystemExit` in the CLI, not Ceedling

`cli/cmd_embedded_ut/embedded_ut_impl.py:83-91`:

```python
if get_platform() == "linux":     ...
elif get_platform() == "win32":   ...
else:  # pragma: no cover
    ERR = f"Something went wrong in '{Path(__file__).absolute()}'"
    raise SystemExit(ERR)
```

`get_platform()` returns only `"linux"` or `"win32"`
(`cli/helpers/host_platform.py:49-61`). On Darwin it falls into the `else` and
aborts **at import time**. So `fox.py ceedling ...` cannot run on macOS at all,
before Ceedling is ever reached. This is the actual gate.

`cli/` is protected, so this was **not** changed. The build layout that the
function would have produced was reproduced manually instead.

### 2.3 The suite migrated to waf, and that migration is incomplete in this checkout

`tests/unit/wscript` and `tests/unit/app/wscript` are waf-based and reference
`tools/cmock/vendor/unity/src/unity.c`, `tools/cmock/src/cmock.c`,
`conf/unit/app_cmock.yml`, `conf/unit/unity.yml` and `conf/unit/app_gcovr.cfg`.
**None of those paths exist**, and `git log --all -- tools/cmock conf/unit/app_cmock.yml`
returns nothing, so they never existed in this repository's history either.
Meanwhile `wscript:399-410` still invokes `fox.py ceedling` from its distcheck.

In other words the Ceedling path is the only one that can actually work here,
and it is the path this runbook uses.

---

## 3. Environment recipe

```bash
cd docs/artifacts/.work/verification-env

# 1. Ceedling into an isolated GEM_HOME. Nothing is installed into the user
#    or system Ruby.
mkdir -p .work-gems
GEM_HOME="$PWD/.work-gems" GEM_PATH="$PWD/.work-gems" \
    gem install ceedling --no-document

# 2. Build layout: project.yml, HALCoGen inputs and generated stand-ins.
./provision.sh app
./provision.sh bootloader

# 3. A single test.
./run.sh test:../../tests/unit/app/driver/foxmath/test_foxmath.c

# 4. A whole sweep, one Ceedling invocation per test.
python3 analyze_hcg_closure.py > logs/hcg-closure.json
./run_suite.py --out results-strict.json
./run_suite.py --relax --out results-relaxed.json
```

Files:

| file | purpose |
|---|---|
| `provision.sh` | builds `build/<variant>_host_unit_test/` and proves `project.yml` is byte-identical to the shipped file |
| `make_halcogen_stubs.py` | generates `config_cpu_clock_hz.h`, the `HL_spi.h` stand-in and the portability shim |
| `run.sh` | applies the isolated `project.yml` rewrites, then execs Ceedling |
| `analyze_hcg_closure.py` | per-test include-closure analysis; selects the 136 in-scope tests |
| `run_suite.py` | runs each test separately, captures per-run logs under `logs/strict` or `logs/relaxed`, writes `results-*.json` |
| `make_corpus_records.py` | generates the corpus `execution` artifacts from the captured results |
| `bin/gdb` | gdb→LLDB shim, see §5.4 |

### Toolchain actually used

```
uname    : Darwin ... arm64, Darwin Kernel 27.0.0
ruby     : ruby 4.0.7 (2026-09-15 revision 229531a6cf) +PRISM [arm64-darwin27]
ceedling : 1.1.9-2209dc2
cmock    : 2.7.2
unity    : 2.7.2
cexception: 1.3.5
gcc      : /usr/bin/gcc -> Apple clang version 17.0.0 (clang-1700.0.13.5)
```

Ruby 4.0.7 is far newer than the ruby 3.1.2 the project documents, and Ceedling
1.1.9 runs on it without complaint. `ceedling check` (full configuration
validation) passes on the unmodified shipped `app_project_posix.yml`.

Note that `/usr/bin/gcc` **is** the Apple clang driver, so the project file's
`:tools: :test_linker: :executable: gcc` produces Mach-O binaries. The project
is nominally GCC-on-Linux; everything below follows from that mismatch.

---

## 4. The four isolated `project.yml` rewrites

`provision.sh` copies the shipped file unmodified and `cmp`s it. `run.sh` then
applies four changes **to the isolated copy only**, delimited by marker comments
so repeated runs stay consistent. No test source changes.

1. **`:use_test_preprocessor: :all` → `:none`.**
   With `:all`, Ceedling 1.1.9 aborts on this tree in the preprocessor's
   directive-only pass:
   `Failed to read './test/preprocess/files/test_database/directives_only/raw/ftask.h' for comment stripping ... No such file or directory`.
   `:none` selects Ceedling's own documented source-scan fallback, which
   resolves the same headers. Without this, **no** test builds.

2. **`-include foxbms_host_port_shim.h`.** See §5.1.

3. **`-Wno-strict-prototypes -Wno-deprecated-non-prototype`.**
   Apple clang enables these by default; GNU gcc does not under
   `-std=c11 -Wextra -Wall -pedantic -Werror`. Without them,
   `src/app/driver/foxmath/utils.h:120` (`extern uint32_t UTIL_GetSeed();`)
   fails the build on a compiler difference alone. These suppress diagnostics
   only — they cannot mask an error, a wrong value or a type error.

4. **Optional, `RELAX_CLANG_DIAGNOSTICS=1` only:**
   `-Wno-enum-conversion -Wno-array-bounds -Wno-parentheses-equality`.
   These unblock six further tests. Reported separately because relaxing them
   did not only reveal passes: it revealed two additional **failures** that the
   strict build gate was hiding. The strict run is the primary result.

---

## 5. The four real macOS/Linux portability barriers

### 5.1 TI section attributes are invalid for Mach-O

`src/os/freertos/freertos/include/mpu_wrappers.h` defines:

```c
#define PRIVILEGED_FUNCTION  __attribute__( ( section( ".kernelTEXT" ) ) )
#define PRIVILEGED_DATA      __attribute__( ( section( ".kernelBSS" ) ) )
#define FREERTOS_SYSTEM_CALL __attribute__( ( section( ".syscallTEXT" ) ) )
```

Apple clang rejects these:

```
error: argument to 'section' attribute is not valid for this target:
mach-o section specifier requires a segment and section separated by a comma
```

GNU/Linux ELF accepts a bare dotted section name, so this only ever appears on
macOS. These three definitions are the **only** TI section attributes anywhere
under `src/os/freertos` and `src/app` (verified by
`grep -rho 'section( *"\.…"' src/os/freertos/ src/app/ | sort -u`).

`mpu_wrappers.h` is included by `task.h` and `list.h`, which sit in the *same*
directory, and a quoted `#include` always searches the including file's own
directory first — so a `-I` shadow directory cannot intercept them. The shim
instead **pre-defines the header's include guard**:

```c
#define MPU_WRAPPERS_H      /* the real header is then skipped whole */
#define PRIVILEGED_FUNCTION /* empty */
#define PRIVILEGED_DATA     /* empty */
#define FREERTOS_SYSTEM_CALL/* empty */
```

The attributes only control where a function lands in the *target* image. They
change no observable behaviour, no foxBMS logic and no Unity assertion. The
shipped project file already declares
`:cmock: :strippables: ["(.FREERTOS_SYSTEM_CALL)", "(.PRIVILEGED_FUNCTION)", ...]`,
i.e. upstream already strips these before parsing mocked code.

Verified independently: the whole FreeRTOS include chain (`FreeRTOS.h`,
`task.h`, `list.h`, `queue.h`, `semphr.h`, `event_groups.h`, `stream_buffer.h`)
compiles with `-std=c11 -Wextra -Wall -pedantic -Werror` under the shim.

### 5.2 HALCoGen

HALCoGen is proprietary Texas Instruments code generation software. It is not
available here and cannot be redistributed. The repository ships its **inputs**
(`conf/hcg/app.hcg`, `conf/hcg/app.dil`) but not its **output**:
`conf/hcg/include/` and `conf/hcg/source/` are gitignored and empty, and
`which halcogen` finds nothing. `_run_halcogen()` in the CLI tolerates this and
logs *"Assuming HALCoGen sources are available..."*.

The good news, from `tools/waf-tools/f_hcg.py:150-157`, is that the host build
needs **exactly one** thing from HALCoGen: `include/config_cpu_clock_hz.h`.
Every other generated file is on the `conf/hcg/app-remove.yml` removal list, and
the FreeRTOS sources HALCoGen would emit are already shipped in
`src/os/freertos/freertos/`. That header is written byte-for-byte as
`embedded_ut_impl.py:_cleanup_hcg_sources` writes it, and the clock value is
**read out of the repository's own committed DIL file**, not guessed:

```
conf/hcg/app.dil:1280:  DRIVER.OS.VAR.OS_CPUCLOCKHZ.VALUE=100000000
```

`configCPU_CLOCK_HZ` is referenced in exactly one place in the whole tree,
`src/os/freertos/freertos/portable/ccs/arm_cortex-r5/port.c:341-342`, which is
the TI RTI port and is not part of any host build.

One further stand-in is required: `tests/unit/support/struct_helper.h`
`#include "HL_spi.h"` and uses exactly one type from it, `spi_config_reg_t`.
A shadow copy providing **only** that type is written to the build root, whose
member set is exactly what the repository references:

```
grep -rho '\.CONFIG_[A-Za-z0-9_]*' src/ tests/ | sort -u
# CONFIG_DELAY CONFIG_FMT0..3 CONFIG_GCR1 CONFIG_INT0 CONFIG_LVL
# CONFIG_PC0 CONFIG_PC1 CONFIG_PC6 CONFIG_PC7 CONFIG_PC8 CONFIG_TBPRD
```

> **This is a reconstruction, not the TI original.** It provides no register
> offsets, no functions, no enums and no macros. On a host the struct is never
> memory-mapped — it is used as a plain value buffer — so only the field names
> and their integer width are load-bearing. A test that needs a real TI SPI
> function from this header will fail to compile, which is intended: that is
> reported as an infrastructure gap rather than hidden.

### 5.3 clang versus gcc diagnostic strictness

Six tests do not compile under the shipped strict flag set purely because the
compiler changed:

| diagnostic | count | example |
|---|---|---|
| `-Wenum-conversion` | 4 | `test_sys_mon.c:226` passes `STD_RETURN_TYPE_e` where `FRAM_RETURN_TYPE_e` is expected |
| `-Warray-bounds` | 1 | `test_diag_cbs_current.c`, `array index 1 is past the end of the array` |
| `-Wparentheses-equality` | 1 | `test_diag.c`, `equality comparison with extraneous parentheses` |

These are worth reviewing on their own merits: `-Wno-enum-conversion` on
`test_redundancy` and `test_diag` is not what unblocks them — the extended run
is what *reveals* that they then fail.

### 5.4 gdb

The shipped project file sets `:use_backtrace: :gdb`, and Ceedling aborts
configuration validation unless an executable named `gdb` is on `PATH`:

```
🪲 ERROR: :tools ↳ :test_backtrace_gdb ↳ :executable ➡️ `gdb` does not exist in system search paths
```

GNU gdb does not ship with macOS. `bin/gdb` is a small shim that translates the
gdb backtrace command line to LLDB. It runs only when a test binary crashes and
never influences a pass/fail verdict, which Ceedling derives from the test
runner's exit code and Unity's assertion output.

---

## 6. What does not run, and why

Of 313 repository tests, 136 were in scope. The other 177 are blocked on
HALCoGen. The 37 build failures in the strict sweep break down as:

| cause | count | actionable? |
|---|---|---|
| Excluded by the shipped Ceedling `:paths:` configuration — `tests/unit/app/driver/afe/adi/common/ades183x/**`, `tests/unit/app/driver/afe/nxp/common/mc3377x/**`, `tests/unit/support` | 21 | No. Upstream excludes these deliberately; see the `README.md` in each excluded AFE directory. |
| Requires a HALCoGen-generated TI header — `HL_het.h`, `HL_reg_system.h`, `HL_sys_common.h`, `HL_sys_dma.h` | 10 | Only with HALCoGen. |
| Apple-clang-only diagnostic promoted by `-Werror` | 6 | Yes, but see §5.3 — two of them hide real failures. |

The 177 out-of-scope tests reach **34 distinct** `HL_*.h` headers. Reconstructing
34 proprietary TI register maps and driver APIs from memory would be fabricating
the very thing these tests are meant to verify, so it was not done. The blocker
is precisely characterised instead: `analyze_hcg_closure.py` records, for every
test, exactly which HALCoGen headers it needs.

**To unblock the rest you need either:**

- **(a)** a real HALCoGen run on `conf/hcg/app.hcg` (TI licence required), or
- **(b)** a Linux host, where the ELF compiler accepts the TI section attributes
  unchanged — this is the path upstream already documents, and the reconstruction
  in §5.2 would not be needed there.

Docker was checked and is available (`Docker version 29.8.0`), so option (b) is
viable. It was **not** built, because native macOS succeeded and the deliverable
priority puts native first; a Linux container would in any case need the same
HALCoGen output for the 177 remaining tests.

---

## 7. The five strict failures — a real, reproducible product defect

All five fail with the same message shape:

```
At line (90): "Expected 0x…C000 Was 0x…C098:Function DATA_Write4DataBlocks
Argument pDataFromSender0:Function called with unexpected argument value."
```

Root cause, established from the sources — **not** from the host environment:

`src/app/engine/database/database.h:209` declares the database access API with
**untyped `void *` parameters**:

```c
extern STD_RETURN_TYPE_e DATA_Write4DataBlocks(
    void *pDataFromSender0, void *pDataFromSender1, ...);
```

The shipped Ceedling configuration sets `:cmock: :when_ptr: :compare_data`,
which requires CMock to know the **size** of the pointed-to type so it can
`memcmp`. Given `void *` it cannot, so CMock emits
`UNITY_TEST_ASSERT_EQUAL_PTR` — a pointer-**identity** check. The generated
mock confirms it:

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

This is **compiler- and platform-independent**: it depends only on the
`void *` declaration and the CMock configuration, so the same five tests are
expected to fail under GNU gcc on Linux. It was not caused by the macOS
adaptation, and it is a genuine test-suite defect that had no record in the
corpus.

Affected tests, with the assertion counts from the real run:

| test | tested | failed |
|---|---|---|
| `tests/unit/app/application/algorithm/moving_average/test_moving_average.c` | 1 | 1 |
| `tests/unit/app/application/algorithm/state_estimation/soc/lookup-table/test_soc_lookup-table.c` | 6 | 1 |
| `tests/unit/app/application/algorithm/state_estimation/test_state_estimation.c` | 5 | 4 |
| `tests/unit/app/driver/afe/debug/default/test_debug_default.c` | 11 | 1 |
| `tests/unit/app/engine/config/test_diag_cfg.c` | 1 | 1 |

The extended run adds two more with the identical root cause:
`tests/unit/app/application/redundancy/test_redundancy.c` (10 tested, 1 failed)
and `tests/unit/app/engine/diag/test_diag.c` (18 tested, 1 failed).

The fix direction is a decision for the product owner, not for this run: either
type the `database.h` parameters so `:when_ptr: :compare_data` works as
intended, or add explicit `:treat_as` entries, or have the affected tests
register a CMock callback and compare contents in the callback. **No result was
adjusted to make any test pass.**

---

## 8. Corpus artifacts

14 `execution` artifacts under `docs/artifacts/corpus/as_is/verification/`:

- `execution-soa-voltage.json` (FB2-VER-EXE-000001) — **rev 1 → 2**. Revision 1
  claimed `actual_host_run` / `pass` with `"hash": "sha256:placeholder"` and an
  unverifiable `x86_64 Linux host / gcc 11.4.0` environment. Superseded with a
  real arm64 macOS run and real sha256 values.
- `execution-contactor-statemachine.json` (000002), `execution-afe-plausibility.json`
  (000003), `execution-contactor-driver.json` (000005) — **rev 1 → 2**,
  `execution_kind: none` / `outcome: blocked` → `actual_host_run` with real
  results. 000002 and 000005 both name `test_contactor.c`; one execution
  evidences both, which is noted in each record.
- `execution-afe-ltc-driver.json` (000004) — **rev 1 → 2**, still
  `none` / `blocked`, but the blocker is now precise: the include closure needs
  exactly `HL_het.h`, `HL_spi.h`, `HL_sys_dma.h`. Revision 1's evidence path
  `tests/unit/app/driver/ltc/6813-1/test_ltc_6813-1.c` was **wrong** (missing
  the `afe/` segment) and has been corrected.
- `execution-host-unit-test-sweep-strict.json` (000006) and
  `-relaxed.json` (000007) — new; the two bulk sweeps.
- `execution-defect-*.json` (000008–000014) — new; one record per genuine
  failure, with the Unity text verbatim.

`execution_kind` and `outcome` were kept orthogonal throughout: every record
that ran is `actual_host_run`; its `outcome` is the real `pass`/`fail`; the one
record that could not run stayed `none` / `blocked` rather than being dressed
up. Revisions were appended to `revision_history`, never overwritten.

### `actual_product_evidence` did not move, and should not have

`docs/artifacts/tools/corpus.py:920` computes it as:

```python
dims["actual_product_evidence"] = {"numerator": 0, "denominator": len(tms),
    "detail": "no target-hardware executions (policy: blocked, not fabricated)"}
```

The numerator is a hard-coded `0` and the dimension is scoped to
**target-hardware** executions. This run is a **host** run, not a target
execution, so it does not satisfy that dimension and the metric stays
`0/16`. `corpus.py` was deliberately **not** edited to make the number move;
doing so would relabel host runs as target evidence, which is exactly the
blurring the corpus rules forbid. What did change is that 14 corpus records now
carry real `actual_host_run` results with real hashes, where before there were
none.

---

## 9. Reproducing

```bash
cd docs/artifacts/.work/verification-env
./provision.sh app && ./provision.sh bootloader
python3 analyze_hcg_closure.py > logs/hcg-closure.json
./run_suite.py --out results-strict.json      # expect 94 pass / 5 fail / 37 build-fail
./run_suite.py --relax --out results-relaxed.json   # expect 98 / 7 / 31
python3 make_corpus_records.py                 # regenerate the execution artifacts
cd ../../..
python3 docs/artifacts/tools/corpus.py validate
python3 docs/artifacts/tools/corpus.py check
```

Expect `errors=0` and `Acceptance suite: PASSED`. The sweep numbers above were
reproduced identically across two independent strict runs.
