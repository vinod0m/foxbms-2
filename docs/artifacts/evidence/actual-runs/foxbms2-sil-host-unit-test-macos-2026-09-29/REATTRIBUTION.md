# Re-attribution of the SIL build failures — every defect re-derived from the real compiler output

**This document supersedes the prior claim that the build failures were "30 real
defects in foxBMS source".** That claim is withdrawn. It was reached by matching
diagnostic *text* against a list of class names without asking where each
diagnostic came from, and it is wrong for most of them.

Measured on: `docs/artifacts/.work/verification-env/sil`, 313 tests,
Apple clang 17.0.0, Ceedling 1.1.9, CMock 2.7.2, macOS arm64.
Baseline re-measured from scratch before any edit, and it reproduced the
archived result exactly (313 / 222 pass / 7 fail / 84 build failures,
988 assertions tested, 950 passed, 35 failed) — so the comparison below is
against a measured state, not an inherited number.

## How the diagnostics were obtained

The per-test stdout log only captures the LINK step. When a translation unit
fails to compile, Ceedling's link then fails with

    clang: error: no such file or directory: './test/out/<t>/<u>.o'

which names a missing object file and nothing else. The COMPILE diagnostics are
written by the harness's own diagnostics-collecting compiler wrapper
(`sil/tools/sil_cc.py`) into `logs/diag-records/<slug>.jsonl`, one record per
compiler invocation, with the full argv and every `file:line:col` diagnostic.
`sil/tools/dump_diagnostics.py` reads those records. This is a read of what the
compiler actually said, not a re-derivation, and it touches no build tree, so
several tests can be inspected at once without perturbing a measurement.

Signatures were then derived from the repository's own call sites and its own
definitions (`graft grep <fn>`, and reading the function definition in `src/`),
and cross-checked by hand at a sample. No arity was derived by counting commas.

## Classes

| class | meaning |
|---|---|
| **H** | SIL interface-header defect. The arity, type, name or shape in `sil/iface/HL_*.h` — a machine-declared stand-in for TI's absent headers — does not match how the product calls the function. |
| **P** | Product defect. `src/` is genuinely wrong. |
| **T** | Test defect. `tests/` asserts something the product does not do, or has an out-of-bounds or mistyped access. |

## The re-attribution, per test

All 27 tests the previous round placed in `real_defect_*`,
`sil_interface_header_mismatch` or `undeclared_identifier`.

### `real_defect_macro_arity` — 4 tests — **all H**

Root cause: `sil/iface/HL_sys_dma.h` disagreed with the product in **both**
directions on the same three functions.

| symbol | product / test | `sil/iface/HL_sys_dma.h` said |
|---|---|---|
| `dmaEnableInterrupt` | 3 args at `src/app/driver/dma/dma.c:216,227,253,254,255,280,281,282` and `src/bootloader/driver/crc/crc.c:252-254` | 2 args |
| `dmaSetCtrlPacket` | 2 args, second **by value**, at `dma.c:233,236,261,264,288,291,313` | 3 args, third a pointer |
| `dmaDisableInterrupt` | paired with the above | 2 args |

`dmaIntGroup_t` did not exist, and neither did the frame-type enumerators
`BTC` / `LFS` / `FTC` that the product passes as argument 2. The product casts
them itself — `(dmaChannel_t)…, (dmaInterrupt_t)BTC, (dmaIntGroup_t)DMA_INTA` —
so both the third type and the four enumerators are read off the product, not
invented. The harness's `DMA_INTA`/`DMA_INTB` were also typed `dmaInterrupt_t`
where the product casts them to the distinct `dmaIntGroup_t`.

Evidence the compiler pointed at the harness and not at `src/`: the
"expected 3, have 2" note names `sil_hal/HL_sys_dma.h:339`, and the test-side
"too many arguments provided to function-like macro invocation" names
`mocks/test_dma/MockHL_sys_dma.h:68` — a file CMock generated *from* the
interface header.

* `tests/unit/app/driver/dma/test_dma.c` → H
* `tests/unit/app/driver/dma/test_dma_nxp.c` → H
* `tests/unit/app/driver/dma/test_dma_uart.c` → H
* `tests/unit/app/main/test_main.c` → H (plus a separate `getResetSource` defect, below)

### `real_defect_implicit_int` — 2 tests — **all H**

This is the single most mis-attributed item in the list.

`sil/iface/HL_reg_sci.h` contained

    #define Fapi_FlashSectorType  (0U)
    #define config_value_type_t  (0U)
    #define dmaIntGroup_t         (0U)
    #define dmaFlg_t              (0U)
    #define SpiDataStatus_t       (0U)

while `sil/iface/HL_sys_common.h` and `HL_sys_dma.h` and `HL_spi.h` contain
`typedef`s of exactly those names. A `#define` textually replaces every later
occurrence, so `typedef uint32_t Fapi_FlashSectorType;` became
`typedef uint32_t (0U);`. clang then reported the *cascade* — 56 diagnostics in
`test_uart.c`, 57 in `test_uart_sci_notification.c`, none of which names the
macro that caused them — and the previous round classified them as
`real_defect_implicit_int`, i.e. as a defect in `src/app/driver/uart/uart.c`,
which is innocent.

* `tests/unit/app/driver/uart/test_uart.c` → H
* `tests/unit/app/driver/uart/test_uart_sci_notification.c` → H

### A larger, previously invisible instance of the same defect

Fixing the two files above exposed a systematic version of the same hazard:
**77 `#define`s in `sil/iface/HL_reg_*.h` shared a name with a struct member
declared in a different harness header.** `HL_reg_sci.h` alone defined `CTL`,
`ES`, `ABOTR`, `DADD`, `DAT1`, `CHCTRL`, `ELDOFFSET` … as macros, which replaced
every `->CTL`, `->DADD`, `->DAT1` member access in `HL_can.h`, `HL_spi.h` and
`HL_sys_dma.h`. Detected mechanically by
`sil/tools/find_macro_type_collisions.py`, and cross-checked against the
repository with `sil/tools/collision_code_uses.py`, which strips comments and
string literals and reports the real code uses: **all 77 have zero code uses in
`src/` or `tests/`**, so all 77 were deleted. The deleter refuses to remove any
macro that has a code use, so the rule cannot damage a macro the product needs.
This is the hazard `sil/RUNBOOK.md` §6 already describes for the repository's own
names ("a `#define` of the same name would textually replace every use of it —
`#ifndef` does not help"); it had simply never been checked *between harness
headers*.

### `real_defect_out_of_bounds_array_index` — 6 tests — **all T**

Every one of the six `-Warray-bounds` diagnostics is located in `tests/unit/**`.
Not one is in `src/`.

| test | declaration | highest index used | verdict |
|---|---|---|---|
| `test_can_cbs_tx_f_cell-temperatures.c:381` | `float_t testSignalData[3u]` | 12 | T |
| `..._3-temp-sensors.c:198` | `[3u]` | 6 | T |
| `..._4-temp-sensors.c:199` | `[3u]` | 8 | T |
| `..._5-temp-sensors.c:200` | `[3u]` | 10 | T |
| `test_can_cbs_tx_f_cell-voltages.c:367` | `[4u]` | 8 | T |
| `test_diag_cbs_current.c:112-117` | `uint8_t cellChargeOvercurrent[BS_NR_OF_STRINGS]` = `uint8_t[1]` | `BS_NR_OF_STRINGS` = 1 | T |

The product never touches `testSignalData`; it is the test's own fixture, passed
by address to `CAN_TxPrepareSignalData_ReturnThruPtr_pSignal`. The product's own
loop is correctly guarded — `can_cbs_tx_f_cell-temperatures.c:343-379` nests each
`CANTX_TemperatureSetData()` behind `if (temperatureSensorId < BS_NR_OF_TEMP_SENSORS)`.

`test_diag_cbs_current.c:112-117` is an off-by-one in the *test*: the arrays are
`uint8_t cellChargeOvercurrent[BS_NR_OF_STRINGS]`
(`src/app/engine/config/database_cfg.h:521,541,561`), and the comment on line 111
says "Start with 1 as we test reset first" — i.e. element 0.

Fixed by sizing the fixtures to the highest index used and by changing the six
`[BS_NR_OF_STRINGS]` to `[0u]`.

### `real_defect_implicit_function_declaration` — 2 tests — **all H**

* `tests/unit/app/driver/adc/test_adc.c`
  `src/app/driver/adc/adc.c:141` reads `adc_adc1RawVoltages[i].value`, but the
  harness declared `typedef uint16_t adcData_t;`. clang: *"member reference base
  type 'adcData_t' (aka 'unsigned short') is not a structure or union"*, which
  names the harness typedef. The third diagnostic
  (`adcGetData_ReturnArrayThruPtr_data` undeclared) is the array plugin, fixed
  under Phase 2. → H
* `tests/unit/app/driver/emac/test_emac-low-level.c`
  Needs `EMAC_MACCONTROL`, `EMAC_RXHDP`, `EMAC_TXHDP`, `HWREG` — a register map
  the repository does not record. **H, and NOT FIXED.** Writing those macros
  would fabricate the register offsets the harness exists to be honest about
  not having; `sil/RUNBOOK.md` §6 names this exact anti-pattern. Reported, not
  worked around.

### `real_defect_excess_initializers` — 1 test — **H, NOT FIXED**

`tests/unit/app/driver/afe/ti/common/api/test_ti_bq79xxx_afe_dma.c:92`
positional-initialises a `spiBASE_t` with 28 top-level members, of which one is a
nested brace group of 75 elements. The harness's `spiREG_t` has 23. Closing the
gap requires asserting TI's real `spiREG_t` member count and a 75-member nested
struct, and the **only** evidence for either is a zero-filled initialiser in a
test. The product uses the handle for identity only (`src/app/driver/spi/spi.c:660-680`
compares `pNode == spiREG1`) and never dereferences a member, so a widened shadow
struct would be inert — but it would still be a fabricated layout, invented to
make a test compile. **H, not brought up, reported.**

### `real_defect_absolute_value_truncation` — 1 test — **P (the one product defect)**

`src/app/driver/rtc/rtc.c:272`:

    if (abs(rtcTimeFromIcEpochFormat - rtcTimeFromTimerEpochFormat) > RTC_MAX_DIFFERENCE_BETWEEN_TIMER_AND_IC_s)

`rtcTimeFromIcEpochFormat` and `rtcTimeFromTimerEpochFormat` are both `time_t`
(a `long` here); `abs()` takes an `int`. clang: *"absolute value function 'abs'
given an argument of type 'time_t' (aka 'long') but has parameter of type 'int'
which may cause truncation of value"*. The truncation and the `abs(INT_MIN)`
undefined result are real on every platform; GCC simply does not implement
`-Wabsolute-value`, which is why it survived every upstream gcc build.

**Blast radius, enumerated.** `RTC_AdjustTime()` is `static`, declared at
`rtc.c:133`, defined at `rtc.c:252`, and called from exactly one place,
`rtc.c:441` inside `RTC_Trigger()`. `RTC_Trigger()` is declared at
`rtc.h:269` and called from exactly one place, `src/app/task/config/ftask_cfg.c:318`.
No signature changes, no header change, no other caller, no interface touched.
Covered by `tests/unit/app/driver/rtc/test_rtc.c`.

**Fix applied:** compare the two signed directions instead of calling `abs`, which
removes both the truncation and the `abs(INT_MIN)` undefined result. For every
representable difference other than `INT_MIN` the result is identical to
`abs(d) > LIMIT`; at `INT_MIN`, where the old expression was undefined, the new
one is correct. This is the only `src/` change in the whole session.

### `sil_interface_header_mismatch` — 3 tests — **all H**

Every one is a notification entry point whose arity or type in `sil/iface` did not
match the product's own **definition** in
`src/app/hal/app-hl_notification.c` and
`src/bootloader/hal/bootloader-hl_notification.c`:

| function | product definition | harness said |
|---|---|---|
| `canErrorNotification` | `(canBASE_t *node, uint32_t notification)` — `:108`, `:99` | 3 args |
| `gioNotification` | `(gioPORT_t *port, uint32_t bit)` — `:117`, `:105` | `(gioBASE_t *, uint32_t)` |
| `pwmNotification` | `(hetBASE_t *hetREG, uint32_t pwm, uint32_t notification)` — `:136` | 1 arg |
| `edgeNotification` | `(hetBASE_t *hetREG, uint32_t edge)` — `:139` | 1 arg |
| `crcNotification` | `(crcBASE_t *crc, uint32_t flags)` — `:145` | 1 arg |
| `etpwmNotification` | `(etpwmBASE_t *node)` — `:148` | 2 args |
| `etpwmTripNotification` | `(etpwmBASE_t *node, uint16_t flags)` — `:151` | `uint32_t` 2nd arg |
| `eqepNotification` | `(eqepBASE_t *eqep, uint16_t flags)` — `:154` | `uint32_t` 2nd arg |
| `rtiNotification` | `(rtiBASE_t *rtiREG, uint32_t notification)` — `:96` | 1 arg |
| `epcCAMFullNotification` | `(void)` — `:157`, `:108` | 1 arg |
| `ecapNotification` | `(ecapBASE_t *ecap, uint16_t flags)` — `pwm.c:176` | `uint32_t` 2nd arg |
| `ecapGetCAP1/2/3` | return `uint32_t` — `pwm.c:181,183,185`, `test_pwm.c:89,92,95` | `int32_t` |
| `dmaGroupANotification` | `(dmaInterrupt_t, uint32_t)` — `bootloader-hl_notification.c:93` | `(uint32_t, uint32_t)` |

* `tests/unit/app/driver/pwm/test_pwm.c` → H
* `tests/unit/app/hal/test_app-hl_notification.c` → H
* `tests/unit/bootloader/hal/test_bootloader-hl_notification.c` → H

### `undeclared_identifier` — 8 tests

| test | missing name | verdict |
|---|---|---|
| `test_nxp_mc33775a_alarm.c` | `gioPORT_t` | H — a shared TI type the harness declared only in `HL_gio.h`; the product names it at `nxp_mc33775a_alarm.c:188` from a unit whose only TI-facing include is behind a disabled `#if`. Also `PULDIS`, a member the product writes at `:238`, was missing from the shadow struct. |
| `test_can_cfg_rx.c` | `CAN_CAN2AFE_CELL_{TEMPERATURES,VOLTAGES}_QUEUE_s` | H (CMock limitation) — see below. |
| `test_bender_iso165c.c` | same two types | H (CMock limitation) — same cause. |
| `test_crc.c`, `test_crc_semi_auto_crc_calculation.c` | `crcREG1`, `ACCESS_64_BIT`, `crcConfig_t`, `FTC` | H, partially fixed — `FTC` came with the DMA fix. The rest needs `crcConfig_t`'s field layout, which is a TI fact; **not brought up.** |
| `test_spi_spi_notification.c` | `config_value_type_t` | H — declared in `HL_sys_common.h`, which the test's include chain does not reach. |
| `test_master_info.c` | `INTERCONNECT_RESET` | H — a reset-reason enumerator the repository's own test switches over; nine siblings already existed. |
| `test_dma_dma_group_a_notification.c` | same DMA arity as above | H |

**The two queue-type cases are a CMock limitation, not a foxBMS defect.**
`src/app/driver/config/can_cfg.h:195` puts `CAN_CAN2AFE_CELL_TEMPERATURES_QUEUE_s`
behind `#if (defined(FOXBMS_AFE_DRIVER_DEBUG_CAN) && (…==1))`, and
`src/app/driver/can/cbs/rx/can_cbs_rx.h:314` guards the matching prototypes
behind the same condition — the repository is internally consistent. CMock's
header parser does not evaluate that condition. CMock 2.7.2,
`lib/cmock_header_parser.rb:86-88`:

    elsif stripped =~ /^#\s*if/
      stack.push([emit, emit, false])
      # emit unchanged: unknown condition, keep both branches

so CMock mocks the guarded functions regardless, while the C preprocessor hides
the typedef along with them, and the generated mock references a type that does
not exist. Making the parser and the preprocessor agree needs either a CMock
change or an `#if`-aware mock set; neither is available from `conf/`, which is
out of scope. **Reported, not worked around.**

## Tally

| verdict | count |
|---|---|
| **H** — SIL interface-header defect | 21 of 27 tests |
| **T** — test defect | 6 of 27 tests (all in the array-bounds class) |
| **P** — product defect | 1 test (`test_rtc.c`, `src/app/driver/rtc/rtc.c:272`) |
| H, identified but deliberately NOT fixed because closing it means fabricating a device fact | 3 tests (`test_emac-low-level.c`, `test_ti_bq79xxx_afe_dma.c`, `test_crc*.c`) |

**Of the build failures the previous round called "real defects in foxBMS
source", one is a product defect.** The prior report's own headline number — "30
real defects in foxBMS source" — is withdrawn.
