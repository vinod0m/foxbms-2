# TASK 1 — classification of the 14 class-A `void *` failures

## The empirical experiment that corrected the prior diagnosis

Applying the `TEST_ASSERT_EQUAL_MEMORY` recipe to
`test_bal_strategy_history.c` **did not make it pass**. It failed with

```
Memory Mismatch. Byte 12 Expected 0x00 Was 0x01 : Function DATA_Read1DataBlock
```

Byte 12 of `DATA_BLOCK_BALANCING_CONTROL_s` is `bool enableBalancing`, and the
test *deliberately sets it to `true`* two lines earlier
(`test_bal_strategy_history.c:101`, `pBalancing->enableBalancing = true;`).

So the content of the two objects genuinely differs, by design. A content
comparison is the **wrong oracle** for this test, and applying the recipe
blindly would have converted one unsatisfiable assertion into a different
unsatisfiable assertion while looking like progress.

The test's own decoy told the real story:

```c
static DATA_BLOCK_BALANCING_CONTROL_s bms_tableControl = {...};   /* line 90  */
...
DATA_Read1DataBlock_ExpectAndReturn(&bms_tableControl, STD_OK); /* line 103 */
DATA_Write1DataBlock_ExpectAndReturn(&bms_tableControl, STD_OK); /* line 104 */
```

`bms_tableControl` is used at **exactly two places, both `_ExpectAndReturn`
arguments, and nowhere else.** It is a dead decoy. The test never passes it to
the code under test.

Meanwhile the test *does* hold the real object:

```c
DATA_BLOCK_BALANCING_CONTROL_s *pBalancing = TEST_BAL_GetBalancingControl(); /* == &bal_balancing */
pBalancing->enableBalancing = true;
BAL_Init(pBalancing);
```

and `BAL_Init` (`src/app/application/bal/bal.c:146-152`) does
`DATA_READ_DATA(pControl); ... DATA_WRITE_DATA(pControl);` — it passes its
**argument** straight through. So the pointer production sends is `pBalancing`,
which the test already had in hand.

**Proof.** Replacing the two decoy arguments with `pBalancing` — changing
nothing else, and *removing* the now-unused decoy, which the compiler then
flagged under `-Werror=unused-variable`, confirming it had been dead:

```
TESTED:  3
PASSED:  3
FAILED:  0
```

Identity was never a silent downgrade here. **Identity was the correct oracle
and the test passed the wrong pointer.** The experiment was then reverted.

## The corrected discriminator

Three cases, not two:

**(A) PROPAGATION — the test holds the real object and passed a decoy.**
Identity is the correct oracle and is *achievable*. The fix is to pass the real
pointer. This *strengthens* the test: it now asserts that `BAL_Init` propagates
the caller's block, which nothing asserted before.

**(B) REACHABLE-STATIC — the code under test owns an internal static the test
cannot address, and the block is unmutated at the call site.** Identity is
impossible; content over the real `sizeof` is the correct and achievable
oracle. This is the genuine silent downgrade the prior task described.

**(C) MUTATED-BEFORE-SEND — the code under test owns an internal static and has
already mutated it before the call.** Identity impossible; a full content
comparison is *also* impossible, because the two objects genuinely differ by
construction. Only the **block identity** — `header.uniqueId`, which is the
field that actually says *which* database entry this is — is both meaningful
and stable. Asserting that is the strongest oracle available through an untyped
pointer.

Per-test verdict, with the evidence for each:

| # | test | line(s) | decoy used only as Expect arg? | real object reachable? | block mutated before send? | verdict |
|---|---|---|---|---|---|---|
| 1 | `test_bal_strategy_history.c` | 103 | **yes** — 2 uses, both Expect | **yes** — `TEST_BAL_GetBalancingControl()` | no (arg passed through) | **A** |
| 2 | `test_bal_strategy_voltage.c` | 101 | **yes** — same shape | **yes** — same accessor | no | **A** |
| 3 | `test_moving_average.c` | 135 | yes, but also in dead `blocks` struct | no — function-local static in `moving_average.c:187` | read is pristine, write is mutated | **B** for the read, **C** for the write |
| 4 | `test_state_estimation.c` | 116,123,129 | yes | no — file-scope statics, no accessor | **yes** — `SE_Initialize*` mutates then writes | **C** |
| 5 | `test_state_estimation.c` | 135 | yes (×3) | no | **yes** | **C** |
| 6 | `test_interlock.c` | 210,265,279 | yes | no — function-local static `interlock.c:215` | read-only, unmutated | **B** |
| 7 | `test_database.c` | 160,373,…,703 | yes | no — function-local `database.c:150` | populated by the test itself before each call | **B** |
| 8 | `test_debug_default.c` | 245 | yes | no — `debug_default.c:104-111` | no | **B** |
| 9 | `test_debug_can.c` | 300,321,360 | n/a — passes a **`uint64_t`** | n/a | n/a | see "wrong type" |
| 10 | `test_nxp_mc33775a_i2c.c` | 168…577 | passes `&transactionData` | no — function-local in product | yes | **C** |
| 11 | `test_can_cbs_rx_afe_cell-temperatures.c` | 287 | n/a — passes a **`uint64_t`** | n/a | n/a | wrong type |
| 12 | `test_can_cbs_rx_afe_cell-voltages.c` | 293 | n/a — passes a **`uint64_t`** | n/a | n/a | wrong type |
| 13 | `test_can_cbs_rx_imd_bender-iso165c-info.c` | 258 | yes | no — function-local `canBuffer` | yes, filled by product | **C** |
| 14 | `test_can_cbs_rx_imd_bender-iso165c-response.c` | 242 | yes | no — function-local `canBuffer` | yes | **C** |

### The "wrong type" cases cannot be fixed at all, and must keep failing

`test_debug_can.c`, `test_can_cbs_rx_afe_cell-temperatures.c` and
`test_can_cbs_rx_afe_cell-voltages.c` pass a **`uint64_t`** where the code under
test passes a queue-item struct:

| test object | size | product object | size |
|---|---|---|---|
| `uint64_t messageData` | 8 | `CAN_CAN2AFE_CELL_TEMPERATURES_QUEUE_s` | 20 |
| `uint64_t messageData` | 8 | `CAN_CAN2AFE_CELL_VOLTAGES_QUEUE_s` | 14 |

Sizes measured with a standalone probe compiled against the repository's own
headers, not assumed.

* Identity can never hold (different objects).
* Content is **undefined**: comparing 8 bytes of a `uint64_t` against 20 bytes
  of a queue-item struct would read past the end of the test's object.
* `uniqueId` does not apply: these are not database blocks.

There is no correct oracle for the buffer argument at all. The tests would need
a correctly-typed local of the queue-item struct to say anything meaningful,
and the buffer is an out-parameter the test never reads back — so the
information the test wants is not there to assert. **These three are left
failing and are reported as defects.**

## Sizes (measured)

```
DATA_BLOCK_SOC_s                       = 32
DATA_BLOCK_MIN_MAX_s                   = 52
DATA_BLOCK_MOVING_AVERAGE_s            = 60
DATA_BLOCK_BALANCING_CONTROL_s         = 112
DATA_BLOCK_CELL_VOLTAGE_s              = 88
DATA_BLOCK_ADC_VOLTAGE_s               = 140
DATA_QUEUE_MESSAGE_s                   = 40
CAN_BUFFER_ELEMENT_s                   = 24
CAN_CAN2AFE_CELL_TEMPERATURES_QUEUE_s  = 20
CAN_CAN2AFE_CELL_VOLTAGES_QUEUE_s      = 14
```

## Why `_Stub` is the weakest available construction

`test_diag_cfg.c` uses `DATA_Write4DataBlocks_Stub(cb)`. From the generated
mock, `_Stub` sets `CallbackBool = 0`, and the mock then does:

```c
if (!Mock.X_CallbackBool && Mock.X.X_CallbackFunctionPointer != NULL)
{
    Mock.X.X_CallbackFunctionPointer(...);
    return;                                  /* <-- before ALL expectation checks */
}
UNITY_TEST_ASSERT_NOT_NULL(cmock_call_instance, ... CMockStringCalledMore);
... call-order checks ...
... argument checks ...
```

So a `_Stub` loses CMock's **call counting**, **strict ordering** and
**return-value** assertion. It is weaker than the `_ExpectAndReturn` it
replaces, even where the latter would have worked.

Every callback used below therefore re-establishes those three explicitly, so
the replacement is **not** a weakening:

* a `step` variable pins the call count *and* the inter-call order, asserted
  inside the callbacks;
* the callback's return value is asserted against what the test declared;
* `_CallCount()` is asserted at the end of the test, so "called fewer times
  than expected" is caught — which `_Stub` alone would not catch.

## Non-vacuity

Every recipe is proven non-vacuous by flipping one bit in the test's fixture,
re-running, and observing the comparison fail, then reverting — the same
procedure that was used for `test_diag_cfg.c`. Results are in §2 of the
delivery report.
