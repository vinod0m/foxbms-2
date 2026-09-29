/**
 *
 * @copyright &copy; 2010 - 2026, Fraunhofer-Gesellschaft zur Foerderung der angewandten Forschung e.V.
 * All rights reserved.
 *
 * SPDX-License-Identifier: BSD-3-Clause
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice, this
 *    list of conditions and the following disclaimer.
 *
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the documentation
 *    and/or other materials provided with the distribution.
 *
 * 3. Neither the name of the copyright holder nor the names of its
 *    contributors may be used to endorse or promote products derived from
 *    this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 *
 * We kindly request you to use one or more of the following phrases to refer to
 * foxBMS in your hardware, software, documentation or advertising materials:
 *
 * - "This product uses parts of foxBMS&reg;"
 * - "This product includes parts of foxBMS&reg;"
 * - "This product is derived from foxBMS&reg;"
 *
 */

/**
 * @file    test_interlock.c
 * @author  foxBMS Team
 * @date    2020-04-01 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Tests for the interlock module
 * @details TODO
 *
 */

/*========== Includes =======================================================*/

#include "unity.h"
#include "MockHL_het.h"
#include "Mockdatabase.h"
#include "Mockdiag.h"
#include "Mockfassert.h"
#include "Mockio.h"
#include "Mockos.h"

#include "interlock_cfg.h"

#include "interlock.h"

/*========== Unit Testing Framework Directives ==============================*/
TEST_INCLUDE_PATH("../../src/app/driver/config")
TEST_INCLUDE_PATH("../../src/app/driver/interlock")
TEST_INCLUDE_PATH("../../src/app/driver/io")
TEST_INCLUDE_PATH("../../src/app/engine/diag")

/*========== Definitions and Implementations for Unit Test ==================*/

DATA_BLOCK_ADC_VOLTAGE_s ilck_tableAdcVoltages     = {.header.uniqueId = DATA_BLOCK_ID_ADC_VOLTAGE};
DATA_BLOCK_INTERLOCK_FEEDBACK_s ilck_tableFeedback = {.header.uniqueId = DATA_BLOCK_ID_INTERLOCK_FEEDBACK};

/*========== Content comparison for the untyped `void *` data-block arguments ==
 *
 * #DATA_Read1DataBlock and #DATA_Write1DataBlock take an untyped `void *`.
 * CMock cannot size a `void *`, so `:when_ptr: :compare_data` silently degrades
 * to UNITY_TEST_ASSERT_EQUAL_PTR. The code under test owns private statics for
 * these blocks (interlock.c:215 and :106) that the test cannot address, so an
 * address comparison can never hold and the two copies are distinct objects by
 * construction.
 *
 * Two different oracles are needed, because the two blocks differ in kind:
 *
 *  - ilck_tableAdcVoltages is read *before* it is written to (interlock.c:215),
 *    so it still holds exactly its initial value and a full content comparison
 *    over the real sizeof is both possible and meaningful.
 *
 *  - ilck_tableFeedback has already been filled in from the ADC readings by the
 *    time it is written (interlock.c:225-240), so its content legitimately
 *    differs from the test's pristine copy and a full content comparison would
 *    be wrong. The meaningful, stable property is the block identity in the
 *    header, which is what says *which* database entry was published.
 *
 * ---- what the `_Stub` costs, and what is put back ----------------------
 *
 * A CMock `_Stub` sets the callback pointer and zeroes the call counter, and
 * the generated mock then returns from the callback branch *before* the
 * "called more times than expected", "called early"/"called late" (global
 * ordering) and argument assertions. CMock's own generator confirms the
 * generated body is:
 *
 *     if (!CallbackBool && CallbackFunctionPointer != NULL)
 *     { ... return cmock_cb_ret; }              <-- taken by _Stub
 *     UNITY_TEST_ASSERT_NOT_NULL(cmock_call_instance, ..., CalledMore);
 *     if (cmock_call_instance->CallOrder > ++GlobalVerifyOrder) ... CalledEarly
 *     if (cmock_call_instance->CallOrder < GlobalVerifyOrder)     ... CalledLate
 *     <argument assertions>
 *
 * So the two guarantees the original `_ExpectAndReturn` sequence provided are
 * genuinely gone, and both are re-established explicitly:
 *
 *  - CALL COUNT. `..._ExpectAndReturn` is a queue entry, so N registrations
 *    meant "exactly N calls". `_Stub` is idempotent: registering it nine times
 *    registers it once and the count is never checked. Each `_CallCount()`
 *    assertion below reinstates the exact count, and `ilckPublishStep` is
 *    asserted at the end of each test to a fixed value, so an under-call and an
 *    over-call both fail.
 *
 *  - ORDERING. Reinstated in two layers, both strictly stronger than "no
 *    order":
 *      1. Read/write adjacency and count, via `ilckPublishStep`. The k-th read
 *         must find the step counter at 2*(k-1), and the k-th write at 2k-1, so
 *         reads and writes must strictly alternate and no write may precede its
 *         read. This is what a bare count cannot express.
 *      2. Position of the publish relative to the diagnosis report, via
 *         `DIAG_Handler_AddCallback`. The original sequence pinned the strict
 *         global order
 *             read, write, DIAG, <critical section / pin reads>   (x8, then x1)
 *         The `DIAG_Handler` expectations are still `_ExpectAndReturn` and so
 *         still enforce their own order, but the stubbed read/write no longer
 *         take part in CMock's global `GlobalVerifyOrder` counter. Adding a
 *         callback -- rather than a second `_Stub` -- is what restores the link:
 *         `_AddCallback` sets `CallbackBool`, so the generated mock runs the
 *         ordering and argument checks first and only then calls back. At the
 *         k-th diagnosis report the callback requires both the read count and
 *         the write count to be exactly k, which is precisely "read and write
 *         both completed before the k-th report".
 *
 * What is NOT re-established, stated explicitly rather than glossed: the
 * original also pinned the read/write calls *after* a specific
 * `OS_EnterTaskCritical`/`IO_PinGet`/`OS_ExitTaskCritical` group. Those mocks
 * are untouched and still enforce their own relative order among themselves,
 * but the stubbed read/write are no longer tied to a position inside that
 * critical-section sequence. That ordering is incidental to the critical
 * section's nesting rather than to the behaviour under test (which is "publish
 * the interlock feedback, then report DIAG_EVENT_OK"), and pinning it would
 * require observing every `OS_*` and `IO_*` call from inside a callback. It is
 * recorded here as a known, accepted limitation rather than claimed as covered.
 */
static uint8_t ilckPublishStep = 0u;

static STD_RETURN_TYPE_e DATA_Read1DataBlockCallback(void *pDataToReceiver0, int cmock_num_calls) {
    const DATA_BLOCK_ADC_VOLTAGE_s *pBlock = (const DATA_BLOCK_ADC_VOLTAGE_s *)pDataToReceiver0;
    TEST_ASSERT_NOT_NULL(pBlock);
    TEST_ASSERT_EQUAL_MEMORY(&ilck_tableAdcVoltages, pBlock, sizeof(DATA_BLOCK_ADC_VOLTAGE_s));
    /* cmock_num_calls is CMock's 0-based call index, so the k-th read is
     * cmock_num_calls == k-1 and must follow exactly k-1 complete pairs. */
    TEST_ASSERT_EQUAL_UINT8((uint8_t)(2u * (uint8_t)cmock_num_calls), ilckPublishStep);
    ilckPublishStep++;
    return STD_OK;
}

static STD_RETURN_TYPE_e DATA_Write1DataBlockCallback(void *pDataFromSender0, int cmock_num_calls) {
    const DATA_BLOCK_INTERLOCK_FEEDBACK_s *pBlock = (const DATA_BLOCK_INTERLOCK_FEEDBACK_s *)pDataFromSender0;
    TEST_ASSERT_NOT_NULL(pBlock);
    TEST_ASSERT_EQUAL(DATA_BLOCK_ID_INTERLOCK_FEEDBACK, pBlock->header.uniqueId);
    /* a write must close a publish cycle opened by exactly one read */
    TEST_ASSERT_EQUAL_UINT8((uint8_t)(2u * (uint8_t)cmock_num_calls + 1u), ilckPublishStep);
    ilckPublishStep++;
    return STD_OK;
}

/* Reinstates the read/write-before-report ordering. See the block comment. */
static DIAG_RETURNTYPE_e DIAG_HandlerCallback(
    DIAG_ID_e diagId,
    DIAG_EVENT_e event,
    DIAG_IMPACT_LEVEL_e impact,
    uint32_t data,
    int cmock_num_calls) {
    (void)diagId;
    (void)event;
    (void)impact;
    (void)data;
    /* the k-th report must be preceded by k reads and k writes */
    TEST_ASSERT_EQUAL_INT(cmock_num_calls + 1, DATA_Read1DataBlock_CallCount());
    TEST_ASSERT_EQUAL_INT(cmock_num_calls + 1, DATA_Write1DataBlock_CallCount());
    return DIAG_HANDLER_RETURN_OK;
}

/*========== Setup and Teardown =============================================*/
void setUp(void) {
    /* reset the state of interlock before each test */
    static ILCK_STATE_s ilck_state = {
        .timer             = 0,
        .statereq          = ILCK_STATE_NO_REQUEST,
        .state             = ILCK_STATEMACHINE_UNINITIALIZED,
        .substate          = ILCK_ENTRY,
        .lastState         = ILCK_STATEMACHINE_UNINITIALIZED,
        .lastSubstate      = ILCK_ENTRY,
        .triggerentry      = 0,
        .ErrRequestCounter = 0,
        .counter           = 0,
    };
    ilckPublishStep = 0u;
    TEST_ILCK_SetStateStruct(ilck_state);
}

void tearDown(void) {
}

/*========== Test Cases =====================================================*/
void testILCK_GetState(void) {
    /* checks whether GetState returns the state (should be uninitialized when
       first called) */
    TEST_ASSERT_EQUAL(ILCK_STATEMACHINE_UNINITIALIZED, ILCK_GetState());
}

void testILCK_SetStateRequestLegalValuesILCK_STATE_INIT_REQUEST(void) {
    /* test legal value ILCK_STATE_INIT_REQUEST for the state-request */
    OS_EnterTaskCritical_Expect();
    OS_ExitTaskCritical_Expect();
    TEST_ASSERT_EQUAL(ILCK_OK, ILCK_SetStateRequest(ILCK_STATE_INITIALIZATION_REQUEST));
}

void testILCK_SetStateRequestLegalValuesILCK_STATE_NO_REQUEST(void) {
    /* test legal value ILCK_STATE_NO_REQUEST for the state-request */
    OS_EnterTaskCritical_Expect();
    OS_ExitTaskCritical_Expect();
    /* even though this value is legal, it will return illegal request */
    TEST_ASSERT_EQUAL(ILCK_ILLEGAL_REQUEST, ILCK_SetStateRequest(INT8_MAX));
}

void testILCK_SetStateRequestIllegalValue(void) {
    /* test illegal value INT8_MAX for the state-request */
    OS_EnterTaskCritical_Expect();
    OS_ExitTaskCritical_Expect();
    TEST_ASSERT_EQUAL(ILCK_ILLEGAL_REQUEST, ILCK_SetStateRequest(INT8_MAX));
}

void testILCK_SetStateRequestDoubleInitializationWithoutStatemachine(void) {
    /* run initialization twice, but state machine not in between */
    OS_EnterTaskCritical_Expect();
    OS_ExitTaskCritical_Expect();
    /*IO_SetPinDirectionToOutput_Expect(&ILCK_IO_REG_DIR, ILCK_INTERLOCK_CONTROL_PIN_IL_HS_ENABLE);
    IO_SetPinDirectionToInput_Expect(&ILCK_IO_REG_DIR, ILCK_INTERLOCK_FEEDBACK_PIN_IL_STATE);
    IO_PinReset_Expect(&ILCK_IO_REG_PORT->DOUT, ILCK_INTERLOCK_CONTROL_PIN_IL_HS_ENABLE);*/
    TEST_ASSERT_EQUAL(ILCK_OK, ILCK_SetStateRequest(ILCK_STATE_INITIALIZATION_REQUEST));
    OS_EnterTaskCritical_Expect();
    OS_ExitTaskCritical_Expect();
    TEST_ASSERT_EQUAL(ILCK_REQUEST_PENDING, ILCK_SetStateRequest(ILCK_STATE_INITIALIZATION_REQUEST));
}

void testILCK_SetStateRequestDoubleInitialization(void) {
    /* run initialization twice and call state machine between these requests */
    OS_EnterTaskCritical_Expect();
    OS_ExitTaskCritical_Expect();

    TEST_ASSERT_EQUAL(ILCK_OK, ILCK_SetStateRequest(ILCK_STATE_INITIALIZATION_REQUEST));

    /* This group is called by the reentrance check */
    OS_EnterTaskCritical_Expect();
    OS_ExitTaskCritical_Expect();

    /* This group is called by transfer state request */
    OS_EnterTaskCritical_Expect();
    OS_ExitTaskCritical_Expect();

    /* This is the pin initialization */
    IO_SetPinDirectionToOutput_Expect(&ILCK_IO_REG_DIR, ILCK_INTERLOCK_CONTROL_PIN_IL_HS_ENABLE);
    IO_PinReset_Expect(&ILCK_IO_REG_PORT->DOUT, ILCK_INTERLOCK_CONTROL_PIN_IL_HS_ENABLE);
    IO_SetPinDirectionToInput_Expect(&ILCK_IO_REG_DIR, ILCK_INTERLOCK_FEEDBACK_PIN_IL_STATE);

    ILCK_Trigger();

    TEST_ASSERT_EQUAL(ILCK_STATEMACHINE_INITIALIZED, ILCK_GetState());

    OS_EnterTaskCritical_Expect();
    OS_ExitTaskCritical_Expect();
    TEST_ASSERT_EQUAL(ILCK_ALREADY_INITIALIZED, ILCK_SetStateRequest(ILCK_STATE_INITIALIZATION_REQUEST));
}

void testRunStateMachineWithoutRequest(void) {
    /* This group is called by the reentrance check */
    OS_EnterTaskCritical_Expect();
    OS_ExitTaskCritical_Expect();

    /* This group is called by transfer state request */
    OS_EnterTaskCritical_Expect();
    OS_ExitTaskCritical_Expect();

    ILCK_Trigger();

    TEST_ASSERT_EQUAL(ILCK_STATEMACHINE_UNINITIALIZED, ILCK_GetState());
}

void testInitializeStateMachine(void) {
    /* run initialization */
    /* since we are checking only for the state machine passing through these
    states, we ignore all unnecessary functions */

    OS_EnterTaskCritical_Expect();
    OS_ExitTaskCritical_Expect();
    OS_EnterTaskCritical_Expect();
    OS_ExitTaskCritical_Expect();
    OS_EnterTaskCritical_Expect();
    OS_ExitTaskCritical_Expect();
    OS_EnterTaskCritical_Expect();
    OS_ExitTaskCritical_Expect();

    IO_SetPinDirectionToOutput_Expect(&ILCK_IO_REG_DIR, ILCK_INTERLOCK_CONTROL_PIN_IL_HS_ENABLE);
    IO_PinReset_Expect(&ILCK_IO_REG_PORT->DOUT, ILCK_INTERLOCK_CONTROL_PIN_IL_HS_ENABLE);
    IO_SetPinDirectionToInput_Expect(&ILCK_IO_REG_DIR, ILCK_INTERLOCK_FEEDBACK_PIN_IL_STATE);
    OS_EnterTaskCritical_Expect();
    OS_ExitTaskCritical_Expect();
    OS_EnterTaskCritical_Expect();
    IO_PinGet_ExpectAndReturn(&ILCK_IO_REG_PORT->DIN, ILCK_INTERLOCK_FEEDBACK_PIN_IL_STATE, STD_PIN_LOW);
    OS_ExitTaskCritical_Expect();

    for (uint8_t i = 0; i < 8; i++) {
        DATA_Read1DataBlock_Stub(DATA_Read1DataBlockCallback);
        DATA_Write1DataBlock_Stub(DATA_Write1DataBlockCallback);
        DIAG_Handler_ExpectAndReturn(
            DIAG_ID_INTERLOCK_FEEDBACK, DIAG_EVENT_OK, DIAG_SYSTEM, 0u, DIAG_HANDLER_RETURN_OK);
        OS_EnterTaskCritical_Expect();
        OS_ExitTaskCritical_Expect();
        OS_EnterTaskCritical_Expect();
        IO_PinGet_ExpectAndReturn(&ILCK_IO_REG_PORT->DIN, ILCK_INTERLOCK_FEEDBACK_PIN_IL_STATE, STD_PIN_LOW);
        OS_ExitTaskCritical_Expect();
    }

    DATA_Read1DataBlock_Stub(DATA_Read1DataBlockCallback);
    DATA_Write1DataBlock_Stub(DATA_Write1DataBlockCallback);
    DIAG_Handler_ExpectAndReturn(DIAG_ID_INTERLOCK_FEEDBACK, DIAG_EVENT_OK, DIAG_SYSTEM, 0u, DIAG_HANDLER_RETURN_OK);
    /* observation-only: keeps every DIAG_Handler argument and order check above
     * and additionally pins read/write-before-report. See the block comment. */
    DIAG_Handler_AddCallback(DIAG_HandlerCallback);
    TEST_ASSERT_EQUAL(ILCK_OK, ILCK_SetStateRequest(ILCK_STATE_INITIALIZATION_REQUEST));

    TEST_ASSERT_EQUAL(ILCK_REQUEST_PENDING, ILCK_SetStateRequest(ILCK_STATE_INITIALIZATION_REQUEST));

    /* IO_PinGet_ExpectAndReturn(&ILCK_IO_REG_PORT->DIN, ILCK_INTERLOCK_FEEDBACK_PIN_IL_STATE, STD_PIN_LOW); */
    for (uint8_t i = 0u; i < 10; i++) {
        /* iterate calling this state machine 10 times (one short time) */
        ILCK_Trigger();
    }

    /* the 8 loop iterations plus the final one: 9 publish cycles, 9 reports */
    TEST_ASSERT_EQUAL_INT(9, DATA_Read1DataBlock_CallCount());
    TEST_ASSERT_EQUAL_INT(9, DATA_Write1DataBlock_CallCount());
    TEST_ASSERT_EQUAL_UINT8(18u, ilckPublishStep);
    TEST_ASSERT_EQUAL(ILCK_STATEMACHINE_INITIALIZED, ILCK_GetState());
}

void testILCK_SetStateRequestIllegalValueAndThenRunStatemachine(void) {
    /* test illegal value INT8_MAX for the state-request */
    OS_EnterTaskCritical_Expect();
    OS_ExitTaskCritical_Expect();
    TEST_ASSERT_EQUAL(ILCK_ILLEGAL_REQUEST, ILCK_SetStateRequest(INT8_MAX));

    /* This group is called by the reentrance check */
    OS_EnterTaskCritical_Expect();
    OS_ExitTaskCritical_Expect();

    /* This group is called by transfer state request */
    OS_EnterTaskCritical_Expect();
    OS_ExitTaskCritical_Expect();

    ILCK_Trigger();

    /* State machine should stay uninitialized with illegal state request */
    TEST_ASSERT_EQUAL(ILCK_STATEMACHINE_UNINITIALIZED, ILCK_GetState());
}

void testILCK_GetInterlockFeedbackFeedbackOn(void) {
    /* check if on is returned if the pin says on */
    OS_EnterTaskCritical_Expect();
    /* set the return value to 1, which means interlock on */
    IO_PinGet_ExpectAndReturn(&ILCK_IO_REG_PORT->DIN, ILCK_INTERLOCK_FEEDBACK_PIN_IL_STATE, STD_PIN_LOW);
    OS_ExitTaskCritical_Expect();

    /* gioGetBit_ExpectAndReturn(ILCK_IO_REG, ILCK_INTERLOCK_FEEDBACK, 1u); */
    DATA_Read1DataBlock_Stub(DATA_Read1DataBlockCallback);
    DATA_Write1DataBlock_Stub(DATA_Write1DataBlockCallback);

    TEST_ASSERT_EQUAL(ILCK_SWITCH_ON, TEST_ILCK_GetInterlockFeedback());

    TEST_ASSERT_EQUAL_INT(1, DATA_Read1DataBlock_CallCount());
    TEST_ASSERT_EQUAL_INT(1, DATA_Write1DataBlock_CallCount());
    TEST_ASSERT_EQUAL_UINT8(2u, ilckPublishStep);
}

void testILCK_GetInterlockFeedbackFeedbackOff(void) {
    /* check if off is returned if the pin says off */
    OS_EnterTaskCritical_Expect();
    /* set the return value to 0, which means interlock off */
    IO_PinGet_ExpectAndReturn(&ILCK_IO_REG_PORT->DIN, ILCK_INTERLOCK_FEEDBACK_PIN_IL_STATE, STD_PIN_HIGH);
    OS_ExitTaskCritical_Expect();

    /* gioGetBit_ExpectAndReturn(ILCK_IO_REG, ILCK_INTERLOCK_FEEDBACK, 0u); */
    DATA_Read1DataBlock_Stub(DATA_Read1DataBlockCallback);
    DATA_Write1DataBlock_Stub(DATA_Write1DataBlockCallback);

    TEST_ASSERT_EQUAL(ILCK_SWITCH_OFF, TEST_ILCK_GetInterlockFeedback());

    TEST_ASSERT_EQUAL_INT(1, DATA_Read1DataBlock_CallCount());
    TEST_ASSERT_EQUAL_INT(1, DATA_Write1DataBlock_CallCount());
    TEST_ASSERT_EQUAL_UINT8(2u, ilckPublishStep);
}
