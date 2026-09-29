# `RELAX_CLANG_DIAGNOSTICS` — every flag, and why it is allowed

**Scope.** These flags are added only to the SIL harness's *isolated copy* of
`conf/unit/<variant>_project_posix.yml` (`sil/build/<variant>_host_unit_test/
project.yml`), which `sil/run.sh` rewrites on every invocation. The shipped
`conf/unit/app_project_posix.yml` and `conf/unit/bootloader_project_posix.yml`
are byte-for-byte unmodified — `sil/provision.sh` copies them and `cmp`s them
to prove it, and Task 8 of the delivery re-checks the whole protected path set.

**The rule being applied.** A diagnostic may be silenced here only if BOTH of
the following are established:

1. it is a diagnostic Apple clang emits that GNU gcc does not emit under the
   project's shipped `-std=c11 -Wextra -Wall -pedantic -Werror`; and
2. the construct it fires on is *correct*, with evidence.

A flag that fails either test is not added. A diagnostic that denotes a real
defect is never silenced, even when a flag would have silenced it, and even
when silencing it would have increased the pass count.

**Honest limit on the evidence.** There is no GNU gcc on this host: `/usr/bin/
gcc` is a symlink to Apple clang (`Apple clang version 17.0.0`). So "gcc would
not emit this" cannot be demonstrated by *running* gcc here. It is established
instead by the diagnostic's own membership:

* whether **clang** knows the group, tested directly —
  `clang -std=c11 -fsyntax-only -W<name> -x c <non-empty .c>`; and
* whether the group is one gcc documents as not enabled by `-Wall`/`-Wextra`.

Where neither test settles the question, the flag is **not** added and the
diagnostic is reported as a finding instead. Section 4 lists those cases.

---

## 1. The flags that are added

### `-Wno-enum-conversion`

**What fires.** `implicit conversion from enumeration type 'STD_RETURN_TYPE_e'
to different enumeration type 'DIAG_RETURNTYPE_e'`, 54 occurrences across 12
tests.

**Why gcc does not emit it.** gcc has `-Wenum-conversion`, but it is a
*conversion* warning: gcc's documentation places it in the group enabled by
`-Wconversion`, **not** by `-Wall` or `-Wextra`. Clang's `-Wenum-conversion`
covers the "different enumeration type" case and **is** on by default. Under
gcc, `-std=c11 -Wextra -Wall -pedantic` therefore stays silent; under clang it
fires and the shipped `-Werror` turns it into an error.

**Why the construct is correct.** Every occurrence is a *value-preserving*
conversion between two of foxBMS's per-module return-type enums, both of which
have `OK` as their first enumerator and therefore value 0:

* `src/app/main/include/fstd_types.h:82-85` — `STD_RETURN_TYPE_e { STD_OK, STD_NOT_OK }`
* `src/app/engine/diag/diag.h:68-78` — `DIAG_RETURNTYPE_e { DIAG_HANDLER_RETURN_OK, ... }`

Representative site, `tests/unit/app/application/bms/test_bms.c:655`:
`DIAG_Handler_ExpectAndReturn(DIAG_ID_AFE_OPEN_WIRE, DIAG_EVENT_OK, DIAG_STRING, s, STD_OK);`
`DIAG_Handler` returns `DIAG_RETURNTYPE_e` (`src/app/engine/diag/diag.h:121`),
so the mock's return slot is `DIAG_RETURNTYPE_e`, and the test supplies `STD_OK`.
Both are 0. The test then asserts the resulting state machine transition, so
if the value were wrong the test would fail — which is the runtime oracle for
this claim, and it is checked in §3.

*This is a type-hygiene observation about the test code, not a behaviour
defect, and it is reported as such. `tests/` is upstream's and out of scope, so
nothing is changed.*

### `-Wno-parentheses-equality`

**What fires.** `equality comparison with extraneous parentheses`
(`tests/unit/app/engine/diag/test_diag.c`, 1 test).

**Why gcc does not emit it.** `-Wparentheses-equality` is a Clang group. gcc has
no diagnostic by that name and no equivalent for a comparison whose only
defect is redundant parentheses; gcc's `-Wparentheses` covers a different set
(missing parentheses after a keyword, and `if (a = b)`).

**Why the construct is correct.** Redundant parentheses around a comparison
change no parse, no type and no value. The test that contains it passes.

### `-Wno-unknown-warning-option`

**What fires.** `unknown warning group '-Wmaybe-uninitialized', ignored` and
`unknown warning group '-Wdiscarded-qualifiers', ignored`, 3 tests. This is the
one case the task calls out specifically, so it is treated strictly.

**Why gcc does not emit it — verified, not asserted.** These come from
`#pragma GCC diagnostic ignored` lines *in the repository*:

| file:line | pragma names |
|---|---|
| `tests/unit/app/driver/afe/maxim/common/test_mxm_1785x_tools.c:57` | `-Wmaybe-uninitialized` |
| `tests/unit/app/driver/can/cbs/tx-async/test_can_cbs_tx_f_debug-response.c:165` | `-Wdiscarded-qualifiers` |
| `tests/unit/bootloader/driver/can/test_can_bootloader-version-info.c` | `-Wdiscarded-qualifiers` |

Both names are **GCC** warning groups. Neither exists in clang, tested
directly on a non-empty translation unit:

```
$ for f in -Wmaybe-uninitialized -Wdiscarded-qualifiers; do
    clang -std=c11 -fsyntax-only $f -x c w.c; done
-Wmaybe-uninitialized          NOT a clang group   (unknown warning option)
-Wdiscarded-qualifiers         NOT a clang group   (unknown warning option)
```

clang's own spellings of the same ideas — `-Wconditional-uninitialized` and
`-Wignored-qualifiers` — **are** accepted. So the two names in the repository
are gcc spellings of warnings clang has under different names, and the
repository is asking gcc to silence them. Under gcc the pragma is honoured.
Under clang the pragma is a no-op *except* that clang's own "I do not know
this group" notice is itself a diagnostic, which the shipped `-Werror` promotes
to an error. That is the whole mechanism.

A repository-wide sweep (`rg '#pragma GCC diagnostic' src/ tests/ conf/`) found
these **three** occurrences of the two GCC-only names and no others;
`tests/unit/support/test_ignore_list.h` names seven further groups
(`-Wunknown-pragmas`, `-Wunused-parameter`, `-Wmissing-braces`,
`-Wpointer-to-int-cast`, `-Wswitch`, `-Wpointer-arith`, `-Wint-to-pointer-cast`),
all of which clang does know and which compile today.

**Why the construct is correct.** The pragmas request suppression of a warning
about a specific construct. They are upstream's own decision about upstream's
own code, they are valid where upstream builds, and silencing clang's
"I don't recognise this name" notice neither enables nor suppresses any
diagnostic about the code itself. Note the residual property honestly: this
flag would also mute a genuinely misspelled warning-group name elsewhere. That
is why the three occurrences are enumerated above rather than left implicit.

### `-Wno-pragma-pack`

**What fires.** `the current #pragma pack alignment value is modified in the
included file`, 133 occurrences across 7 tests, all inside the vendored
FreeRTOS+TCP stack.

**Why gcc does not emit it.** `-Wpragma-pack` is a Clang group. gcc's `-Wall`
`-Wpragmas` warns about pragmas it does not *recognise*; `#pragma pack` is one it
does, and gcc keeps its pack stack across file boundaries without comment.

**Why the construct is correct — measured, not assumed.** Reproducible with
`sil/tools/probe_pragma_pack.sh`. The script extracts all 22
`pack_struct_start.h`-bracketed struct bodies from the vendored stack by regex
(not transcribed), compiles them twice — once with the repository's own pragma
headers, once with the `#pragma pack` lines stripped — and diffs `sizeof`:

```
ARPPacket_t          packed=42   natural=44   *** DIFFERENT
DHCPMessage_IPv4_t   packed=230  natural=232  *** DIFFERENT
ICMPPacket_t         packed=42   natural=44   *** DIFFERENT
ICMPPacket_IPv6_t    packed=86   natural=88   *** DIFFERENT
IPPacket_t           packed=34   natural=36   *** DIFFERENT
TCPPacket_t          packed=54   natural=56   *** DIFFERENT
TCPPacket_IPv6_t     packed=74   natural=76   *** DIFFERENT
UDPPacket_t          packed=42   natural=44   *** DIFFERENT
(14 others identical; 8 of 22 differ)
```

Two conclusions, and the second is the one that matters:

1. **The pragma is load-bearing.** Eight of the 22 structs change size without
   it, so the packing is doing real work and must not be removed.
2. **`-Wno-pragma-pack` does not remove it.** The flag suppresses the
   *diagnostic*; the `#pragma pack(push,1)` / `#pragma pack(pop)` pair stays in
   force. The packed sizes are the canonical IPv4 wire sizes —
   `EthernetHeader_t` 14, `IPHeader_t` 20, `TCPHeader_t` 20, `UDPHeader_t` 8,
   `ICMPHeader_t` 8.

**The negative control, stated because it matters.** An earlier version of this
probe checked three structs' offsets and *passed even with the pragma removed* —
i.e. it was vacuous, and on this ABI those particular structs are naturally
aligned anyway. The measurement was rebuilt to compare all 22 both ways so that
a vacuous result would be visible. It is not vacuous: 8 differences. Had it come
out at 0, the correct action would have been to *drop the flag* as unnecessary.

**Limit, stated plainly.** This verifies the compiler's layout, not the
receiver's. It says nothing about the wire, and this harness verifies no
timing, no DMA, no clocking and no device behaviour.

### `-Wno-literal-conversion`

**What fires.** `implicit conversion from 'float' to 'uint32_t' changes value
from 55.5 to 55` (`tests/unit/app/driver/can/cbs/tx-cyclic/
test_can_cbs_tx_f_pack-state-estimation.c:158,672,676,...`), 1 test.

**Why gcc does not emit it.** `-Wliteral-conversion` is a Clang group. gcc's
nearest equivalent is `-Wfloat-conversion`, which gcc documents as enabled by
`-Wconversion`, not by `-Wall`/`-Wextra`.

**Why the construct is correct.** The site is
`can_tableSoe.minimumSoe_Wh[0u] = 55.5f;` where `minimumSoe_Wh` is a
`uint32_t` array. The truncation to 55 is a **C conversion semantic**, fixed by
the standard and therefore *identical* on gcc and clang. Silencing the
diagnostic cannot change the value the field ends up holding — only whether the
compiler mentions it. The test's own assertions are calibrated to the truncated
value, because upstream's gcc build compiles the same line silently. §3 records
what the test actually does once it builds.

*Residual, reported rather than hidden: a test fixture writing `55.5f` into a
`uint32_t` field is a smell, and the value it means is not the value it stores.
`tests/` is upstream's and out of scope.*

---

## 2. The flag that was REMOVED

### `-Wno-array-bounds` — removed, and this is the important one

The inherited list contained `-Wno-array-bounds`. **It was removed, because
every single site it was hiding is a genuine out-of-bounds array access.**

The construct is the test file's own fixture, indexed past its end. Clang is
right at every site:

| test | array | indices used | bound |
|---|---|---|---|
| `test_can_cbs_tx_f_cell-temperatures.c:93` declares `float_t testSignalData[3u]`, used at `:381,382,420,421,431,432,442,443,453,454,464,465` | `float_t[3]` | 4, 6, 8, 10, 12 | **out of bounds by up to 9 elements** |
| `test_can_cbs_tx_f_cell-temperatures_3-temp-sensors.c` | `float_t[3]` | 4, 6 | out of bounds |
| `test_can_cbs_tx_f_cell-temperatures_4-temp-sensors.c` | `float_t[3]` | 4, 6, 8 | out of bounds |
| `test_can_cbs_tx_f_cell-temperatures_5-temp-sensors.c` | `float_t[3]` | 4, 6, 8, 10 | out of bounds |
| `test_can_cbs_tx_f_cell-voltages.c:92` declares `float_t testSignalData[4u]`, used at `:367,379` | `float_t[4]` | 6, 8 | out of bounds |
| `test_diag_cbs_current.c:112-117` | `uint8_t[1]` | `BS_NR_OF_STRINGS` = 1 | out of bounds by 1 |

The `test_diag_cbs_current.c` case is a genuine off-by-one: the test intends to
exercise the out-of-range string index, and
`tests/unit/app/application/config/battery_system_cfg_unit_test.h:124` sets
`BS_NR_OF_STRINGS (1u)` for the default unit-test build, so
`cellChargeOvercurrent[BS_NR_OF_STRINGS]` is `[1]` into a one-element array.

A test that reads and writes out of bounds is a test whose result is not
trustworthy, and `gcc`'s `-Warray-bounds` **is** in `-Wall`, so gcc would have
flagged it too. This is not a platform difference and it is reported as a
finding. 6 tests are affected.

---

## 3. Problems that were fixed at the source instead of silenced

Silencing is the wrong tool when the complaint is accurate and the *cause* is
in the harness. Two were fixed that way, and both turned build failures into
passes with **no** warning flag added.

### 3.1 CMock misplacing `GEN_MUST_CHECK_RETURN` → 5+ tests, now passing

`src/app/main/include/general.h:87` defines
`#define GEN_MUST_CHECK_RETURN __attribute__((warn_unused_result))`, applied to
real product functions. CMock's `:strippables:` list only strips attributes
spelled out literally, so it never sees the `__attribute__` text, keeps the
macro name as part of the parsed return type, and emits it into a **parameter**
position in the generated mock:

```c
void MXM_HandleStateReadall_CMockExpectAndReturn(..., bool GEN_MUST_CHECK_RETURN cmock_to_return);
```

Apple clang rejects that under `-Wignored-attributes`; gcc tolerates an
attribute on a parameter. So it *is* a clang-only diagnostic — but the offending
declaration is in **generated** code, and no repository file is wrong.

The fix is CMock's own extension point, and upstream already uses it:
`conf/unit/app_project_posix.yml:341-348` already strips `.FREERTOS_SYSTEM_CALL`,
`.PRIVILEGED_FUNCTION`, `(portDONT_DISCARD)` and the `TEST_LTC_*` accessor
macros. `"GEN_MUST_CHECK_RETURN"` was added to that same list, so CMock strips it
before parsing and generates a correct prototype.

This is strictly better than `-Wno-ignored-attributes`: it fixes the generated
code rather than muting a complaint about it, and it leaves the product source's
own diagnostic coverage intact. `GEN_ALWAYS_INLINE` was added at the same time
for the same reason (`src/app/main/include/general.h` defines it the same way).

### 3.2 The harness's own `BIG_ENDIAN` colliding with a test → 2 tests

The SIL interface header defined `LITTLE_ENDIAN`/`BIG_ENDIAN`. It also had
`tests/unit/app/driver/afe/ltc/api/test_ltc_afe.c:86`, which carries its own
`#define BIG_ENDIAN (3u)` — a copy-paste leftover from another test's DMA setup
boilerplate, **never used** in that file. Clang reports the differing
redefinition under `-Wmacro-redefined`, which `-Werror` promotes; gcc silently
accepts a differing redefinition of an ordinary macro.

Both macros were **deleted from the harness header**, not suppressed, for two
reasons: they were a fact about the device bus that the harness has no business
stating (its own rule), and nothing in `sil/iface/` or `sil/model/` ever
referenced them. The correct response to "my header collides with a test" is to
delete the duplicate.

---

## 4. Diagnostics deliberately NOT silenced

| diagnostic | tests | why it is not silenced |
|---|---|---|
| `-Warray-bounds` | 6 | **Real out-of-bounds access.** gcc's `-Warray-bounds` is in `-Wall`, so it is not a platform difference. Reported as a finding. |
| `-Wtautological-pointer-compare` | 1 | `src/app/driver/afe/maxim/common/mxm_17841b.c:707`: `if ((pInstance->spiRxBuffer != NULL_PTR) && ...)` — `spiRxBuffer` is an **array** member, so the comparison is always true. Behaviour is unchanged, but gcc's `-Waddress` is in `-Wall` and plausibly covers this, so a clang/gcc difference is *not* established. Reported as a finding: a tautological guard in product source. |
| `-Wmissing-field-initializers` | 3 | `{NULL}` partial initialisers of `StaticTask_t`. This group is enabled by `-Wextra` in **both** compilers, so it is not a platform difference by default-enablement. Whether gcc names fewer fields for this specific nested-struct pattern could not be tested on this host (no gcc; `/usr/bin/gcc` is Apple clang), so no difference is claimed. Reported as a finding. |
| `argument to 'section' attribute is not valid for this target` | 1 | `src/version/version.h:83` — `__attribute__((section(".versionInformation")))`, a bare ELF section name. Mach-O requires `__SEG,__sect`. This is **not a warning**: it is a hard error that **no `-W` flag can suppress** (tested: `-Wno-section` and `-Wno-ignored-attributes` both leave it). The construct is correct ELF and simply has no Mach-O spelling. Reported as a finding rather than patched, because overriding `VER_VERSION_INFORMATION` would delete a product annotation whose whole purpose is telling the *target* linker script where to place the version block — the one thing the host cannot verify. |
| `-Wexcess-initializers` | 1 | More initialiser elements than the struct has fields. Real, and gcc flags it too. |
| `-Wimplicit-function-declaration` | 2 | C99 removed implicit declarations. An error on both compilers. |
| too many/few arguments to a function-like macro | 4 | Real macro-arity mismatch in the test or product code. |
| `use of undeclared identifier`, `unknown type name` | 6 | A missing declaration, not a diagnostic about a construct. Where the missing name is a device fact the harness must not invent, the test is reported as not brought up. |
| `expected identifier or '('` in a generated mock | 9 | CMock/FreeRTOS macro erasure — see the dedicated finding. Not a diagnostic about correct code. |

---

## 5. Summary

| flag | status | evidence |
|---|---|---|
| `-Wno-enum-conversion` | kept | clang default, not in gcc's `-Wall`/`-Wextra`; value-preserving, both enums' `OK` == 0; runtime oracle |
| `-Wno-parentheses-equality` | kept | Clang-only group; redundant parentheses change nothing |
| `-Wno-unknown-warning-option` | **added** | 3 repo pragmas name GCC-only groups, verified absent from clang; clang's own spellings accepted |
| `-Wno-pragma-pack` | **added** | Clang-only group; pragma measured load-bearing (8/22 structs); the flag does not remove the pragma |
| `-Wno-literal-conversion` | kept | gcc's equivalent is `-Wfloat-conversion`, not in `-Wall`/`-Wextra`; the truncation is a C semantic, identical on both |
| `-Wno-array-bounds` | **REMOVED** | every site is a real out-of-bounds access; gcc's is in `-Wall` |
| `-Wno-strict-prototypes` | unconditional (pre-existing) | the offenders are CMock-generated K&R-style prototypes and `void`-parameter prototypes in generated code, not repository code |
| `-Wno-deprecated-non-prototype` | unconditional (pre-existing) | Apple-clang synonym of `-Wstrict-prototypes`; not a separate diagnostic |

**No MISRA conformance, tool qualification, certification or ASPICE capability
is claimed or implied anywhere in this file.** The harness mocks the HAL; it
verifies no register map, timing, clocking, interrupt behaviour, DMA transfer,
electrical behaviour or device identity.
