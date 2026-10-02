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
 * @file    test_diag.c
 * @author  foxBMS Team
 * @date    2020-04-02 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Tests for the diag module
 * @details Test functions:
 *          - testDIAG_Reset
 *          - testDIAG_Initialize
 *
 */

/*========== Includes =======================================================*/
#include "unity.h"
#include "Mockcan_cbs_tx_f_fatal-error.h"
#include "Mockdatabase.h"
#include "Mockdiag_cbs.h"
#include "Mocktimer.h"

#include "diag_cfg.h"

#include "diag.h"
#include "test_assert_helper.h"

/*========== Unit Testing Framework Directives ==============================*/
TEST_INCLUDE_PATH("../../src/app/engine/diag")
TEST_INCLUDE_PATH("../../src/app/engine/diag/cbs")
TEST_INCLUDE_PATH("../../src/app/driver/can/cbs/tx-async")
TEST_INCLUDE_PATH("../../src/os/freertos")
TEST_INCLUDE_PATH("../../src/app/task/timer")

/*========== Definitions and Implementations for Unit Test ==================*/
#define NUM_DATA_READ_SUB_CALLS (2)

/** timer to periodically resend the fatal errors*/
static TimerHandle_t diag_fatalErrorResendTimer = {0};

/** fatal error resend period*/
static uint32_t diag_fatalErrorResendPeriod = 100;

/** fatal error resend period*/
static uint32_t diag_fatalErrorResendTimerID = DIAG_FatalErrorResendTimerID;

static DATA_BLOCK_ERROR_STATE_s diag_tableErrorFlags = {.header.uniqueId = DATA_BLOCK_ID_ERROR_STATE};
static DATA_BLOCK_MOL_FLAG_s diag_tableMolFlags      = {.header.uniqueId = DATA_BLOCK_ID_MOL_FLAG};
static DATA_BLOCK_MSL_FLAG_s diag_tableMslFlags      = {.header.uniqueId = DATA_BLOCK_ID_MSL_FLAG};
static DATA_BLOCK_RSL_FLAG_s diag_tableRslFlags      = {.header.uniqueId = DATA_BLOCK_ID_RSL_FLAG};

/*========== Setup and Teardown =============================================*/
void setUp(void) {
    TEST_DIAG_SetActiveFatalErrorArray(0);
    TEST_DIAG_SetActiveFatalErrorCounter(0);
}

void tearDown(void) {
}

/*========== Test Cases =====================================================*/
/**
 * @brief   Iterate over a callback that supplies various scenarios and check if they work as expected
 * @details This function uses the callback #MockTIMER_Create_Callback() in order to correctly compare
 * callback functions in the parameter list.
 */
TimerHandle_t MockTIMER_Create_Callback(
    const char *cpxTimerName,
    uint32_t uxTimerPeriodInMS,
    const UBaseType_t cuxAutoReload,
    void *const cpxTimerID,
    TimerCallbackFunction_t pxCallbackFunction,
    StaticTimer_t *pxTimerBuffer,
    int num_calls) {
    /* determine a value depending on num_calls (has to be synchronized with test) */
    switch (num_calls) {
        case 0:
            TEST_ASSERT_EQUAL_STRING("fatal_error_resend", cpxTimerName);
            TEST_ASSERT_EQUAL_UINT32(diag_fatalErrorResendPeriod, uxTimerPeriodInMS);
            TEST_ASSERT_TRUE(cuxAutoReload);
            TEST_ASSERT_EQUAL_HEX8_ARRAY(&diag_fatalErrorResendTimerID, cpxTimerID, 1);
            /* No CallbackFunction comparison */
            /* No StaticTimer comparison */
            break;
        default:
            TEST_FAIL_MESSAGE("DATA_ReadBlock_Callback was called too often");
    }
    /* ENTER HIGHEST CASE NUMBER IN EXPECT; checks whether all cases are used */
    TEST_ASSERT_EQUAL_MESSAGE(0, (NUM_DATA_READ_SUB_CALLS - 2), "Check code of stub. Something does not fit.");

    if (num_calls >= NUM_DATA_READ_SUB_CALLS) {
        TEST_FAIL_MESSAGE("This stub is fishy");
    }

    /* Return a dummy timer handle */
    return (TimerHandle_t)pxTimerBuffer;
}

/**
 * @brief   Iterate over a callback that supplies various scenarios and check if they work as expected
 * @details This function uses the callback #MockTIMER_Start_Callback() in order to correctly compare
 * callback functions in the parameter list.
 */
STD_RETURN_TYPE_e MockTIMER_Start_Callback(TimerHandle_t timerHandle, uint32_t ticks2wait, int num_calls) {
    /* determine a value depending on num_calls (has to be synchronized with test) */
    switch (num_calls) {
        case 0:
            /* No TimerHandle comparison */
            TEST_ASSERT_EQUAL_HEX32(0u, ticks2wait);
            break;
        default:
            TEST_FAIL_MESSAGE("DATA_ReadBlock_Callback was called too often");
    }
    /* ENTER HIGHEST CASE NUMBER IN EXPECT; checks whether all cases are used */
    TEST_ASSERT_EQUAL_MESSAGE(0, (NUM_DATA_READ_SUB_CALLS - 2), "Check code of stub. Something does not fit.");

    if (num_calls >= NUM_DATA_READ_SUB_CALLS) {
        TEST_FAIL_MESSAGE("This stub is fishy");
    }

    /* Return a dummy timer handle */
    return STD_OK;
}

/**
 * @brief   Callback for #TIMER_Stop() used by testDIAG_HandlerNotEvaluatedHoldsState
 * @details DIAG_ClearFatalErrorById() calls TIMER_Stop() with the timer handle that
 *          DIAG_Initialize() obtained from the #TIMER_Create() mock. That handle is a static of
 *          diag.c and therefore not addressable from this test, so the call cannot be matched by
 *          argument. The stub is installed only immediately before the one call the test expects,
 *          which is the last step of testDIAG_HandlerNotEvaluatedHoldsState() and is the positive
 *          counterpart of the assertion that no TIMER_Stop() was expected anywhere before it.
 */
static STD_RETURN_TYPE_e MockTIMER_Stop_Callback(TimerHandle_t timerHandle, uint32_t ticks2wait, int num_calls) {
    (void)timerHandle;
    (void)ticks2wait;
    (void)num_calls;
    return STD_OK;
}

void testDIAG_ResetErrorCount(void) {
    /* ======= Assertion tests ============================================= */

    /* ======= AT1/1 ======= */
    TEST_DIAG_SetDiagTotalErrorCount(3u);
    TEST_DIAG_Reset();
    TEST_ASSERT_EQUAL(0u, TEST_DIAG_GetDiag()->totalErrorCount);
}

void testDIAG_ResetOccurrenceCounter(void) {
    TEST_DIAG_SetDiagOccurrenceCounter(3u);
    TEST_DIAG_Reset();
    for (uint8_t s = 0u; s < BS_NR_OF_STRINGS; s++) {
        for (uint32_t i = 0u; i < DIAG_ID_MAX; i++) {
            TEST_ASSERT_EQUAL(0u, TEST_DIAG_GetDiag()->occurrenceCounter[s][i]);
        }
    }
}

void testDIAG_SetFatalErrorByIdOutOfRange(void) {
    TEST_ASSERT_FAIL_ASSERT(TEST_DIAG_SetFatalErrorById(DIAG_ID_MAX + 1));
}

void testDIAG_SetFatalErrorByIdOnce(void) {
    CANTX_SendFatalErrorId_ExpectAndReturn(DIAG_ID_SYSTEM_MONITORING, STD_OK);
    TIMER_Start_ExpectAndReturn(diag_fatalErrorResendTimer, 0u, STD_OK);
    TEST_DIAG_SetFatalErrorById(DIAG_ID_SYSTEM_MONITORING);
    TEST_ASSERT_EQUAL(TEST_DIAG_GetFatalErrorCount(), 1);
    TEST_ASSERT_EQUAL(TEST_DIAG_GetFatalErrorArrayCount(DIAG_ID_SYSTEM_MONITORING), 1);
}

void testDIAG_SetFatalErrorByIdDoubled(void) {
    CANTX_SendFatalErrorId_ExpectAndReturn(DIAG_ID_SYSTEM_MONITORING, STD_OK);
    TIMER_Start_ExpectAndReturn(diag_fatalErrorResendTimer, 0u, STD_OK);
    TEST_DIAG_SetFatalErrorById(DIAG_ID_SYSTEM_MONITORING);
    TEST_ASSERT_EQUAL(TEST_DIAG_GetFatalErrorCount(), 1);
    TEST_ASSERT_EQUAL(TEST_DIAG_GetFatalErrorArrayCount(DIAG_ID_SYSTEM_MONITORING), 1);

    TEST_DIAG_SetFatalErrorById(DIAG_ID_SYSTEM_MONITORING);
    TEST_ASSERT_EQUAL(TEST_DIAG_GetFatalErrorCount(), 1);
    TEST_ASSERT_EQUAL(TEST_DIAG_GetFatalErrorArrayCount(DIAG_ID_SYSTEM_MONITORING), 1);
}

void testDIAG_ClearFatalErrorByIdOutOfRange(void) {
    TEST_ASSERT_FAIL_ASSERT(TEST_DIAG_ClearFatalErrorById(DIAG_ID_MAX + 1));
}

void testDIAG_ClearFatalErrorByIdOnce(void) {
    CANTX_SendFatalErrorId_ExpectAndReturn(DIAG_ID_SYSTEM_MONITORING, STD_OK);
    TIMER_Start_ExpectAndReturn(diag_fatalErrorResendTimer, 0u, STD_OK);
    TEST_DIAG_SetFatalErrorById(DIAG_ID_SYSTEM_MONITORING);
    TEST_ASSERT_EQUAL(TEST_DIAG_GetFatalErrorCount(), 1);
    TEST_ASSERT_EQUAL(TEST_DIAG_GetFatalErrorArrayCount(DIAG_ID_SYSTEM_MONITORING), 1);

    CANTX_SendFatalErrorId_ExpectAndReturn(DIAG_ID_MAX, STD_OK);
    TIMER_Stop_ExpectAndReturn(diag_fatalErrorResendTimer, 0u, STD_OK);
    TEST_DIAG_ClearFatalErrorById(DIAG_ID_SYSTEM_MONITORING);
    TEST_ASSERT_EQUAL(TEST_DIAG_GetFatalErrorCount(), 0);
    TEST_ASSERT_EQUAL(TEST_DIAG_GetFatalErrorArrayCount(DIAG_ID_SYSTEM_MONITORING), 0);
}

void testDIAG_ClearFatalErrorByIdDoubled(void) {
    CANTX_SendFatalErrorId_ExpectAndReturn(DIAG_ID_SYSTEM_MONITORING, STD_OK);
    TIMER_Start_ExpectAndReturn(diag_fatalErrorResendTimer, 0u, STD_OK);
    TEST_DIAG_SetFatalErrorById(DIAG_ID_SYSTEM_MONITORING);
    TEST_ASSERT_EQUAL(TEST_DIAG_GetFatalErrorCount(), 1);
    TEST_ASSERT_EQUAL(TEST_DIAG_GetFatalErrorArrayCount(DIAG_ID_SYSTEM_MONITORING), 1);

    CANTX_SendFatalErrorId_ExpectAndReturn(DIAG_ID_MAX, STD_OK);
    TIMER_Stop_ExpectAndReturn(diag_fatalErrorResendTimer, 0u, STD_OK);
    TEST_DIAG_ClearFatalErrorById(DIAG_ID_SYSTEM_MONITORING);
    TEST_ASSERT_EQUAL(TEST_DIAG_GetFatalErrorCount(), 0);
    TEST_ASSERT_EQUAL(TEST_DIAG_GetFatalErrorArrayCount(DIAG_ID_SYSTEM_MONITORING), 0);

    TEST_DIAG_ClearFatalErrorById(DIAG_ID_SYSTEM_MONITORING);
    TEST_ASSERT_EQUAL(TEST_DIAG_GetFatalErrorCount(), 0);
    TEST_ASSERT_EQUAL(TEST_DIAG_GetFatalErrorArrayCount(DIAG_ID_SYSTEM_MONITORING), 0);
}

void testDIAG_ClearFatalErrorByIdNotSetBefore(void) {
    TEST_DIAG_ClearFatalErrorById(DIAG_ID_SYSTEM_MONITORING);
    TEST_ASSERT_EQUAL(TEST_DIAG_GetFatalErrorCount(), 0);
    TEST_ASSERT_EQUAL(TEST_DIAG_GetFatalErrorArrayCount(DIAG_ID_SYSTEM_MONITORING), 0);
}

void test_DIAG_ResendFatalErrorsThree(void) {
    CANTX_SendFatalErrorId_ExpectAndReturn(DIAG_ID_SYSTEM_MONITORING, STD_OK);
    TIMER_Start_ExpectAndReturn(diag_fatalErrorResendTimer, 0u, STD_OK);
    TEST_DIAG_SetFatalErrorById(DIAG_ID_SYSTEM_MONITORING);

    CANTX_SendFatalErrorId_ExpectAndReturn(DIAG_ID_AFE_SPI, STD_OK);
    TEST_DIAG_SetFatalErrorById(DIAG_ID_AFE_SPI);

    CANTX_SendFatalErrorId_ExpectAndReturn(DIAG_ID_AFE_COMMUNICATION_INTEGRITY, STD_OK);
    TEST_DIAG_SetFatalErrorById(DIAG_ID_AFE_COMMUNICATION_INTEGRITY);

    CANTX_SendFatalErrorId_ExpectAndReturn(DIAG_ID_SYSTEM_MONITORING, STD_OK);
    CANTX_SendFatalErrorId_ExpectAndReturn(DIAG_ID_AFE_SPI, STD_OK);
    CANTX_SendFatalErrorId_ExpectAndReturn(DIAG_ID_AFE_COMMUNICATION_INTEGRITY, STD_OK);
    TEST_DIAG_ResendFatalErrors();
}

void test_DIAG_ResendFatalErrorsNone(void) {
    TEST_DIAG_ResendFatalErrors();
}

void testDIAG_Initialize(void) {
    /* ======= Assertion tests ============================================= */

    /* ======= AT1/1 ======= */
    TEST_ASSERT_FAIL_ASSERT(DIAG_Initialize(NULL_PTR));

    /* ======= Routine tests ============================================= */
    DIAG_ID_CFG_s entry = {.id = DIAG_ID_MAX};
    DIAG_DEV_s dev_ptr  = {.nrOfConfiguredDiagnosisEntries = 1, .pConfigurationOfDiagnosisEntries = &entry};
    /* ======= RT1/1 ======= */
    TIMER_Create_Stub(MockTIMER_Create_Callback);
    DIAG_Initialize(&dev_ptr);
}

void testDiag_UpdateFlags(void) {
    /* ======= Assertion tests ============================================= */

    /* ======= AT1/1 ======= */
    DATA_Write4DataBlocks_ExpectAndReturn(
        &diag_tableErrorFlags, &diag_tableMolFlags, &diag_tableRslFlags, &diag_tableMslFlags, STD_OK);
    TEST_ASSERT_PASS_ASSERT(DIAG_UpdateFlags());
}

void testDIAG_SendOneFatalError(void) {
    TEST_DIAG_Reset();
    /* The Create expect tries to compare the Callback given to the memory address from the tested file
    * this normally leads to a failure of the test.
    * In such cases we can create a callback for the Expect function as we have done here.
    * This is also mentioned in the documentation for CMock as Option 4:
    * https://github.com/ThrowTheSwitch/CMock/blob/master/docs/CMock_ArgumentValidation.md
    */
    TIMER_Create_Stub(MockTIMER_Create_Callback);

    TEST_ASSERT_EQUAL(DIAG_Initialize(&diag_device), STD_OK);
    TEST_ASSERT_FALSE(DIAG_IsAnyFatalErrorSet());

    CANTX_SendFatalErrorId_ExpectAndReturn(DIAG_ID_SYSTEM_MONITORING, STD_OK);
    TIMER_Start_Stub(MockTIMER_Start_Callback);
    DIAG_ErrorSystemMonitoring_Expect(DIAG_ID_SYSTEM_MONITORING, DIAG_EVENT_NOT_OK, &diag_kDatabaseShim, 0);
    DIAG_Handler(DIAG_ID_SYSTEM_MONITORING, DIAG_EVENT_NOT_OK, DIAG_SYSTEM, 0);

    TEST_ASSERT(DIAG_IsAnyFatalErrorSet());
}

void testDIAG_SendMultipleFatalErrors(void) {
    TEST_DIAG_Reset();

    TIMER_Create_Stub(MockTIMER_Create_Callback);

    TEST_ASSERT_EQUAL(DIAG_Initialize(&diag_device), STD_OK);

    TEST_ASSERT_FALSE(DIAG_IsAnyFatalErrorSet());

    CANTX_SendFatalErrorId_ExpectAndReturn(DIAG_ID_SYSTEM_MONITORING, STD_OK);
    TIMER_Start_Stub(MockTIMER_Start_Callback);
    DIAG_ErrorSystemMonitoring_Expect(DIAG_ID_SYSTEM_MONITORING, DIAG_EVENT_NOT_OK, &diag_kDatabaseShim, 0);
    DIAG_Handler(DIAG_ID_SYSTEM_MONITORING, DIAG_EVENT_NOT_OK, DIAG_SYSTEM, 0);

    CANTX_SendFatalErrorId_ExpectAndReturn(DIAG_ID_POWER_MEASUREMENT_ERROR, STD_OK);
    DIAG_ErrorPowerMeasurement_Expect(DIAG_ID_POWER_MEASUREMENT_ERROR, DIAG_EVENT_NOT_OK, &diag_kDatabaseShim, 0);
    DIAG_Handler(DIAG_ID_POWER_MEASUREMENT_ERROR, DIAG_EVENT_NOT_OK, DIAG_SYSTEM, 0);

    TEST_ASSERT(DIAG_IsAnyFatalErrorSet());
    TEST_ASSERT_EQUAL(2, TEST_DIAG_GetFatalErrorCount());
}

void testDIAG_PrintErrors(void) {
    DIAG_PrintErrors();
}

void testDIAG_CheckEvent(void) {
    /* ======= Routine tests ============================================= */

    /* ======= RT1/2 ======= */
    /* Condition is STD_OK */
    DIAG_ErrorSystemMonitoring_Expect(DIAG_ID_SYSTEM_MONITORING, DIAG_EVENT_RESET, &diag_kDatabaseShim, 0u);
    DIAG_CheckEvent(STD_OK, DIAG_ID_SYSTEM_MONITORING, DIAG_SYSTEM, 0u);

    /* ======= RT2/2 ======= */
    /* Condition is STD_NOT_OK */
    CANTX_SendFatalErrorId_ExpectAndReturn(DIAG_ID_SYSTEM_MONITORING, STD_NOT_OK);
    TIMER_Start_Stub(MockTIMER_Start_Callback);
    DIAG_ErrorSystemMonitoring_Expect(DIAG_ID_SYSTEM_MONITORING, DIAG_EVENT_NOT_OK, &diag_kDatabaseShim, 0u);
    DIAG_CheckEvent(STD_NOT_OK, DIAG_ID_SYSTEM_MONITORING, DIAG_SYSTEM, 0u);
}

void testDIAG_GetDelay(void) {
    TEST_ASSERT_FAIL_ASSERT(DIAG_GetDelay(DIAG_ID_MAX));
    DIAG_GetDelay(DIAG_ID_SYSTEM_MONITORING);
}

/*========== #DIAG_EVENT_NOT_EVALUATED =========================================
 *
 * #DIAG_EVENT_NOT_EVALUATED is the event a caller reports for a channel whose quantity could
 * not be measured. Its entire safety claim is that it does nothing: it neither raises a
 * diagnosis nor clears a latched one. Both halves are asserted here against the module's own
 * state, reached through #TEST_DIAG_GetDiag(), not merely against the source.
 *
 * The channel is #DIAG_ID_STRING_OVERCURRENT_CHARGE_MSL configured by the shipped
 * diag_device, so its threshold is DIAG_SEN_EVENT_10 and its severity is #DIAG_FATAL_ERROR -
 * which diag_cfg.h documents as leading to an opening of the contactors. Ten #DIAG_EVENT_NOT_OK
 * raise it, ten #DIAG_EVENT_OK clear it again one counter step at a time. The real
 * configuration is used rather than a synthetic one on purpose: DIAG_Handler() resolves the
 * threshold, the severity and the callback through diag.id2ch[] into diag_diagnosisIdConfiguration[],
 * so a device configuration that does not describe that table would silently substitute another
 * channel's parameters.
 *
 * CANNOT OPEN A CONTACTOR. Raising a diagnosis happens in exactly one place, the
 * #DIAG_EVENT_NOT_OK branch of DIAG_Handler(), which increments the occurrence counter, sets the
 * errflag bit, calls DIAG_SetFatalErrorById() and records an entry. On a channel with a
 * developing overcurrent, #DIAG_EVENT_NOT_EVALUATED leaves the counter where it stood and records
 * nothing: it is not evaluated as a further NOT_OK, which would have advanced the counter towards
 * the threshold on the strength of a measurement that does not exist.
 *
 * CANNOT CLOSE A CONTACTOR. Clearing happens in the #DIAG_EVENT_OK branch, which clears the
 * errflag and warnflag bits, zeroes the occurrence counter, calls DIAG_EntryWrite() and calls
 * DIAG_ClearFatalErrorById(), or in the #DIAG_EVENT_RESET branch, which clears the same bits and
 * the counter. On a channel that holds a raised diagnosis, after #DIAG_EVENT_NOT_EVALUATED the
 * errflag bit is still set, the occurrence counter still stands, no error-memory entry was
 * written and the active fatal error entry is still active.
 *
 * No *_CallCount() assertion is used anywhere in this test. In this CMock configuration
 * DIAG_Handler_CallCount() and its siblings return Mock.<fn>_CallbackCalls, which only the
 * *_Stub() path increments, so a count of zero is what they report for any behaviour whatsoever.
 * The absence of a *_Expect() registration is what pins "this call must not happen": an
 * unanticipated call trips CMock's "called more times than expected".
 */
void testDIAG_HandlerNotEvaluatedHoldsState(void) {
    /* ======= RT1/1: bring the module up with the shipped configuration */
    TIMER_Create_Stub(MockTIMER_Create_Callback);
    DIAG_Initialize(&diag_device);
    TEST_DIAG_SetActiveFatalErrorArray(0u);
    TEST_DIAG_SetActiveFatalErrorCounter(0u);
    TIMER_Start_Stub(MockTIMER_Start_Callback);

    const uint32_t errorFlagIndex = (uint32_t)DIAG_ID_STRING_OVERCURRENT_CHARGE_MSL / 32u;
    const uint32_t errorFlagBitmask = 1u << ((uint32_t)DIAG_ID_STRING_OVERCURRENT_CHARGE_MSL % 32u);
    DIAG_DIAGNOSIS_STATE_s *pDiag = TEST_DIAG_GetDiag();
    /* the occurrence counter of the channel under test, for brevity below */
    uint16_t *pCounter = &pDiag->occurrenceCounter[0u][(uint16_t)DIAG_ID_STRING_OVERCURRENT_CHARGE_MSL];

    /* Put the channel into a known, cleared state through the public API. DIAG_EVENT_RESET is the
     * one event that clears errflag, warnflag and the occurrence counter unconditionally, so this
     * makes the test independent of what any earlier test left behind. */
    DIAG_ErrorOvercurrentCharge_Expect(
        DIAG_ID_STRING_OVERCURRENT_CHARGE_MSL, DIAG_EVENT_RESET, &diag_kDatabaseShim, 0u);
    (void)DIAG_Handler(DIAG_ID_STRING_OVERCURRENT_CHARGE_MSL, DIAG_EVENT_RESET, DIAG_STRING, 0u);
    TEST_ASSERT_EQUAL_UINT32(0u, pDiag->errflag[errorFlagIndex] & errorFlagBitmask);
    TEST_ASSERT_EQUAL_UINT32(0u, pDiag->warnflag[errorFlagIndex] & errorFlagBitmask);
    TEST_ASSERT_EQUAL_UINT32(0u, *pCounter);
    /* diag is module-static and is not reset between test cases, so the error-memory entry count is
     * only usable as a delta. This is the baseline every assertion below compares against. */
    const uint32_t entriesBaseline = pDiag->totalErrorCount;

    /* ======= RT2/1: an overcurrent develops but is not yet raised */
    /* The threshold is DIAG_SEN_EVENT_10, so the first nine NOT_OK only advance the counter. No
     * callback, no entry and no fatal error is expected for any of them: an unanticipated call
     * would fail this test. */
    for (uint8_t i = 0u; i < DIAG_SEN_EVENT_10; i++) {
        (void)DIAG_Handler(DIAG_ID_STRING_OVERCURRENT_CHARGE_MSL, DIAG_EVENT_NOT_OK, DIAG_STRING, 0u);
    }
    TEST_ASSERT_EQUAL_UINT32(DIAG_SEN_EVENT_10, *pCounter);
    TEST_ASSERT_EQUAL_UINT32(0u, pDiag->errflag[errorFlagIndex] & errorFlagBitmask);
    TEST_ASSERT_EQUAL_UINT32(entriesBaseline, pDiag->totalErrorCount);
    TEST_ASSERT_EQUAL_UINT32(0, TEST_DIAG_GetFatalErrorArrayCount(DIAG_ID_STRING_OVERCURRENT_CHARGE_MSL));

    /* ======= RT3/1: the current became unmeasurable */
    (void)DIAG_Handler(DIAG_ID_STRING_OVERCURRENT_CHARGE_MSL, DIAG_EVENT_NOT_EVALUATED, DIAG_STRING, 0u);

    /* ======= RT3/1: test output verification, CANNOT OPEN A CONTACTOR */
    /* The counter still stands where the last verdict left it. A DIAG_EVENT_NOT_OK here would have
     * advanced it to the threshold and raised the diagnosis; a DIAG_EVENT_OK would have decremented
     * it. Neither happened and nothing was recorded. */
    TEST_ASSERT_EQUAL_UINT32(DIAG_SEN_EVENT_10, *pCounter);
    TEST_ASSERT_EQUAL_UINT32(0u, pDiag->errflag[errorFlagIndex] & errorFlagBitmask);
    TEST_ASSERT_EQUAL_UINT32(0u, pDiag->warnflag[errorFlagIndex] & errorFlagBitmask);
    TEST_ASSERT_EQUAL_UINT32(entriesBaseline, pDiag->totalErrorCount);
    TEST_ASSERT_EQUAL_UINT32(0, TEST_DIAG_GetFatalErrorArrayCount(DIAG_ID_STRING_OVERCURRENT_CHARGE_MSL));

    /* ======= RT4/1: the overcurrent reaches its threshold and is latched */
    CANTX_SendFatalErrorId_ExpectAndReturn(DIAG_ID_STRING_OVERCURRENT_CHARGE_MSL, STD_OK);
    DIAG_ErrorOvercurrentCharge_Expect(
        DIAG_ID_STRING_OVERCURRENT_CHARGE_MSL, DIAG_EVENT_NOT_OK, &diag_kDatabaseShim, 0u);
    (void)DIAG_Handler(DIAG_ID_STRING_OVERCURRENT_CHARGE_MSL, DIAG_EVENT_NOT_OK, DIAG_STRING, 0u);
    TEST_ASSERT_NOT_EQUAL(0u, pDiag->errflag[errorFlagIndex] & errorFlagBitmask);
    TEST_ASSERT_EQUAL_UINT32(0u, pDiag->warnflag[errorFlagIndex] & errorFlagBitmask);
    TEST_ASSERT_EQUAL_UINT32(DIAG_SEN_EVENT_10 + 1u, *pCounter);
    TEST_ASSERT_EQUAL_UINT32(1, TEST_DIAG_GetFatalErrorArrayCount(DIAG_ID_STRING_OVERCURRENT_CHARGE_MSL));
    TEST_ASSERT_EQUAL_UINT32(1, TEST_DIAG_GetFatalErrorCount());
    const uint32_t entriesWithError = entriesBaseline + 1u;

    /* ======= RT5/1: the current is still unmeasurable, so the raised diagnosis is held */
    (void)DIAG_Handler(DIAG_ID_STRING_OVERCURRENT_CHARGE_MSL, DIAG_EVENT_NOT_EVALUATED, DIAG_STRING, 0u);

    /* ======= RT5/1: test output verification, CANNOT CLOSE A CONTACTOR */
    /* the errflag bit is still set and the counter unchanged, so neither the DIAG_EVENT_OK branch
     * nor the DIAG_EVENT_RESET branch was executed */
    TEST_ASSERT_NOT_EQUAL(0u, pDiag->errflag[errorFlagIndex] & errorFlagBitmask);
    TEST_ASSERT_EQUAL_UINT32(0u, pDiag->warnflag[errorFlagIndex] & errorFlagBitmask);
    TEST_ASSERT_EQUAL_UINT32(DIAG_SEN_EVENT_10 + 1u, *pCounter);
    /* no entry was written, so the error was not reported as recovered */
    TEST_ASSERT_EQUAL_UINT32(entriesWithError, pDiag->totalErrorCount);
    /* DIAG_ClearFatalErrorById() was not reached: it is the only user of TIMER_Stop(), it sends
     * CANTX_SendFatalErrorId(DIAG_ID_MAX) and it clears the active fatal error entry. No
     * expectation is registered for any of those three, so reaching one would already have failed
     * this test. */
    TEST_ASSERT_EQUAL_UINT32(1, TEST_DIAG_GetFatalErrorArrayCount(DIAG_ID_STRING_OVERCURRENT_CHARGE_MSL));
    TEST_ASSERT_EQUAL_UINT32(1, TEST_DIAG_GetFatalErrorCount());

    /* ======= RT6/1: repeated hold events do not drift the channel either */
    for (uint8_t i = 0u; i < 5u; i++) {
        (void)DIAG_Handler(DIAG_ID_STRING_OVERCURRENT_CHARGE_MSL, DIAG_EVENT_NOT_EVALUATED, DIAG_STRING, 0u);
    }
    TEST_ASSERT_NOT_EQUAL(0u, pDiag->errflag[errorFlagIndex] & errorFlagBitmask);
    TEST_ASSERT_EQUAL_UINT32(DIAG_SEN_EVENT_10 + 1u, *pCounter);
    TEST_ASSERT_EQUAL_UINT32(entriesWithError, pDiag->totalErrorCount);
    TEST_ASSERT_EQUAL_UINT32(1, TEST_DIAG_GetFatalErrorArrayCount(DIAG_ID_STRING_OVERCURRENT_CHARGE_MSL));

    /* ======= RT7/1: the hold event is not an OK event, and this channel really is clearable */
    /* Ten explicit DIAG_EVENT_OK decrement the counter from ten to zero and clear the channel on
     * the last one. That is the same transition the latched channel would have undergone had
     * DIAG_EVENT_NOT_EVALUATED reached the DIAG_EVENT_OK branch, which is what makes the
     * assertions above meaningful. */
    for (uint8_t i = 0u; i < DIAG_SEN_EVENT_10; i++) {
        (void)DIAG_Handler(DIAG_ID_STRING_OVERCURRENT_CHARGE_MSL, DIAG_EVENT_OK, DIAG_STRING, 0u);
    }
    TEST_ASSERT_NOT_EQUAL(0u, pDiag->errflag[errorFlagIndex] & errorFlagBitmask);
    TEST_ASSERT_EQUAL_UINT32(1u, *pCounter);
    /* The DIAG_EVENT_OK branch calls DIAG_ClearFatalErrorById() before it invokes the channel
     * callback, so the two expectations are registered in that order. */
    TIMER_Stop_Stub(MockTIMER_Stop_Callback);
    CANTX_SendFatalErrorId_ExpectAndReturn(DIAG_ID_MAX, STD_OK);
    DIAG_ErrorOvercurrentCharge_Expect(
        DIAG_ID_STRING_OVERCURRENT_CHARGE_MSL, DIAG_EVENT_RESET, &diag_kDatabaseShim, 0u);
    (void)DIAG_Handler(DIAG_ID_STRING_OVERCURRENT_CHARGE_MSL, DIAG_EVENT_OK, DIAG_STRING, 0u);
    TEST_ASSERT_EQUAL_UINT32(0u, pDiag->errflag[errorFlagIndex] & errorFlagBitmask);
    TEST_ASSERT_EQUAL_UINT32(0u, *pCounter);
    TEST_ASSERT_EQUAL_UINT32(0, TEST_DIAG_GetFatalErrorArrayCount(DIAG_ID_STRING_OVERCURRENT_CHARGE_MSL));
    TEST_ASSERT_EQUAL_UINT32(0, TEST_DIAG_GetFatalErrorCount());
}
