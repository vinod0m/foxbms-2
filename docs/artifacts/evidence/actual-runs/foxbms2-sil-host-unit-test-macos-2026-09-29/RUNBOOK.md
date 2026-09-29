# SIL host unit-test harness — runbook

**Read `REPORT.md` first.** This file is the recipe. The report is the finding.

Everything here is disposable and git-ignored
(`docs/artifacts/.gitignore` has `.work/`). No file under `src/`, `tests/`,
`conf/`, `tools/`, `cli/`, `gui/`, `hardware/` or the repository-root `wscript`,
`fox.py`, `fox.sh` is written.

---

## 1. One-time setup

The SIL workspace **reuses** the existing environment's isolated gem install. It
does not create one.

```bash
cd docs/artifacts/.work/verification-env

# Only if .work-gems is absent (the predecessor runbook, §3, creates it):
mkdir -p .work-gems
GEM_HOME="$PWD/.work-gems" GEM_PATH="$PWD/.work-gems" \
    gem install ceedling --no-document
```

Nothing is installed into the user's or system Ruby.

---

## 2. Provision

```bash
cd docs/artifacts/.work/verification-env/sil
./provision.sh app
./provision.sh bootloader     # only if you want the bootloader variant
```

What this does, all inside `sil/build/<variant>_host_unit_test/`:

1. symlinks `src/`, `tests/`, `conf/` to the repository (read-only use);
2. copies the shipped `conf/unit/<variant>_project_posix.yml` to `project.yml`
   **verbatim** and `cmp`s it to prove it;
3. copies `conf/hcg/<variant>.hcg` and `.dil`;
4. runs the predecessor's `make_halcogen_stubs.py` for
   `include/config_cpu_clock_hz.h` and the Mach-O portability shim, then
   **deletes the `HL_spi.h` that script drops in the build root** — `-I"."` is
   searched before `-I"sil_hal"`, so a build-root `HL_spi.h` would shadow the SIL
   interface header and silently strip every declaration CMock needs;
5. copies `iface/HL_*.h` into `sil_hal/`, and `model/*.c` into `sil_model/`.

`run.sh` re-syncs 4 and 5 on **every** invocation, so editing a header in
`sil/iface/` takes effect immediately and can never be masked by a stale copy.

---

## 3. Run one test

```bash
cd docs/artifacts/.work/verification-env/sil
./run.sh test:../../tests/unit/app/driver/spi/test_spi.c
VARIANT=bootloader ./run.sh test:../../tests/unit/bootloader/driver/rti/test_rti.c
```

Expect `TESTED: 19 / PASSED: 19 / FAILED: 0` for `test_spi.c`.

For the edit loop, `tools/errs.sh` prints only the de-duplicated compiler
diagnostics and the summary, which is far more readable than a full Ceedling run:

```bash
./tools/errs.sh ../../tests/unit/app/driver/spi/test_spi.c
```

---

## 4. Run the suite

```bash
cd docs/artifacts/.work/verification-env/sil

# The HALCoGen-blocked tests (the point of the exercise)
python3 tools/run_sil_suite.py --out results-sil-strict.json

# Every test, which is what the regression delta is computed from
python3 tools/run_sil_suite.py --all --out results-sil-all.json

# Narrower
python3 tools/run_sil_suite.py --only test_can_cfg --out probe.json
python3 tools/run_sil_suite.py --relax --out results-sil-relaxed.json
```

Each test gets its own Ceedling invocation, so every verdict is individually
attributable and every raw log is kept under `logs/per-test-<flavour>/`.
Pass/fail is parsed from Ceedling's own `OVERALL TEST SUMMARY` and cross-checked
against the process exit code. **Never** inferred.

Runtime: about 4 minutes for the 313-test `--all` sweep.

`RELAX_CLANG_DIAGNOSTICS=1` additionally silences three diagnostics Apple clang
enables by default and GNU gcc does not, under the shipped
`-std=c11 -Wextra -Wall -pedantic -Werror`. The strict run is the primary result.

---

## 5. Regenerate the analysis

```bash
cd docs/artifacts/.work/verification-env/sil

# PHASE 1: the HL_* surface and the corrected blocked-test count
python3 tools/enumerate_hl_surface.py > logs/hl-surface.json

# The arity of every TI call, from the driver AND from the existing tests
python3 tools/derive_hal_signatures.py > logs/hal-signatures.json

# Clock constants, read out of the repository's own HALCoGen input
python3 tools/gen_clock_constants.py \
    build/app_host_unit_test/app.dil iface/sil_clock_constants.h
```

Expected from the first:

```
identifier_count: 39                 (39 HL_*.h headers, 237 occurrences)
blocked_prior_analysis: 136
blocked_corrected: 200
clean_corrected: 113
undercount_count: 23
```

The second script prints one entry per TI entry point with the arity seen at the
driver call site and the arity seen in the tests' `_Expect` macros, side by side.
It is the arity cross-check. Its `distinct_ti_hal_functions` figure is **not** the
number to quote in a report: the "undeclared callee" heuristic it uses also
sweeps up the vendored FreeRTOS and FreeRTOS+TCP stacks, which are not the TI HAL
and which the harness does not declare. The figures that are safe to quote are in
`REPORT.md` §2.3 and are read mechanically out of `sil/iface/`.

---

## 6. Editing the interface headers

Order matters, and the order is enforced by the tools:

```bash
cd docs/artifacts/.work/verification-env/sil
python3 tools/repair_guards.py          # deterministic include-guard shape
python3 tools/normalize_headers.py      # wrap every #define in #ifndef
python3 tools/strip_repository_names.py # drop names the repository provides
```

`strip_repository_names.py` is the important one. A name can collide with the
repository as a macro, an **enumerator** (a `#define` of the same name would
textually replace every use of it — `#ifndef` does not help), a typedef, a
struct member, a function or an object. After the strip pass, every name the SIL
headers still declare is a name the repository does **not** have, which is
exactly the set that must come from the TI boundary.

`repair_guards.py` exists because hand-editing these files repeatedly produced a
duplicated `#ifndef`, a prematurely closed guard, or a missing final `#endif`.
Run it after any bulk edit.

### How to add a declaration

1. Find what the compiler demands. `tools/errs.sh` shows the diagnostic; the
   requirement is then traceable to a repository line.
2. **Decide the arity from the test, not from the driver.** The generated mock
   expands the test's `X_Expect(...)` macros, so a wrong arity is a compile
   error. `tools/derive_hal_signatures.py` prints both ends side by side.
3. Write the signature, and **no register offset, base address or bit mask**.
   If a value is a fact about the silicon, do not write it — report the test as
   not brought up.
4. If a value *is* recorded in the repository (e.g. a clock frequency in
   `conf/hcg/app.dil`), read it with `gen_clock_constants.py` rather than typing
   it.
5. Re-run the three tools, then the test.

### Anti-patterns, and what they look like

* **Do not** invent `EMAC_MACCONTROL`-style offset macros to make
  `test_emac-low-level.c` compile. That is fabricating the register map the
  harness exists to be honest about not having.
* **Do not** tune a constant until a failing test goes green. The `RTI_FREQ`
  case is the counter-example done correctly: the value came from the
  repository's own `.dil`, and if it had not been there the test would have been
  left failing and reported.
* **Do not** give every shadow struct a `static` copy in the header. The driver
  compares peripheral handles for identity across translation units
  (`spi.c:661`, `can.c:632`), so the stores must have external linkage and
  exactly one definition — hence `model/sil_hal_model.c`, linked into every test
  via `:support:`.
* **Do not** use a positional partial initialiser in `sil_hal_model.c`. Under the
  shipped `-Wextra -Werror` it trips `-Wmissing-field-initializers` and breaks
  every test in the suite. Use a designated initialiser.

---

## 7. Reading the results

```bash
cd docs/artifacts/.work/verification-env/sil
python3 - <<'PY'
import json
d = json.load(open('logs/results-sil-all.json'))
for k, v in d.items():
    if k != 'results': print(f'{k}: {v}')
PY
```

Build failures are classified, because "does not build" is not one thing:

| class | meaning |
|---|---|
| `build:excluded_by_shipped_paths` | excluded by upstream's `:paths:` / `:files:`. Not a SIL gap. |
| `build:strict_diagnostic` | Apple-clang-only diagnostic promoted by `-Werror`. Pre-existing. |
| `build:ceedling_cmock_config_quirk` | the generated mock does not parse; CMock's `#if` accounting against FreeRTOS's conditional blocks. Pre-existing. |
| `build:no_hl_surface` | a genuine remaining gap in `sil/iface/`. **This is the one to fix.** |
| `build:other` | anything else; the compiler's first message is recorded verbatim per test. |

Each result record also carries `first_error` and `first_error_lines`, and the
full stdout+stderr of that one invocation under `logs/per-test-strict/`.

To compare against the pre-SIL baseline:

```bash
python3 - <<'PY'
import json
pre = json.load(open('../../../evidence/actual-runs/'
                         'foxbms2-host-unit-test-macos-2026-09-29/results-strict.json'))
sil = json.load(open('logs/results-sil-all.json'))
P = {r['test']: r for r in pre['results']}
S = {r['test']: r for r in sil['results']}
reg = [(t, r['outcome'], S[t]['outcome'])
       for t, r in P.items() if r['outcome'] == 'pass' and S[t]['outcome'] != 'pass']
print('regressions:', len(reg))
for x in reg: print('  ', x)
PY
```

Must print `regressions: 0`. If it does not, that is a real regression and takes
priority over everything else here.

---

## 8. Known non-goals

* **Register-map correctness** is out of scope and not achievable here. See
  `REPORT.md` §7.
* **The bootloader variant** is wired up (`VARIANT=bootloader`, `test_rti.c`
  passes 3/3) but the flash driver needs TI's Fapi geometry, and 6 bootloader
  tests are excluded upstream as Windows-only.
* `lldb` is broken on this host and the predecessor's `bin/gdb` shim has a
  Python 3 syntax error at line 64. Neither was fixed: they live in the
  predecessor workspace, and neither affects a pass/fail verdict — both run only
  when a test binary crashes.
