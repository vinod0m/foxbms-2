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
 * @file    test_nxp_afe.c
 * @author  foxBMS Team
 * @date    2020-06-10 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Test of the afe.c module
 * @details TODO
 *
 */

/*========== Includes =======================================================*/

#include "unity.h"
#include "MockHL_sys_dma.h"

#include "afe.h"
#include "battery_system_cfg.h"
#include "nxp_afe.h"

#include "test_assert_helper.h"

#include <stdbool.h>
#include <stdint.h>

/*========== Unit Testing Framework Directives ==============================*/
TEST_SOURCE_FILE("nxp_afe.c")

TEST_INCLUDE_PATH("../../src/app/driver/afe/api")
TEST_INCLUDE_PATH("../../src/app/driver/afe/nxp/api")
TEST_INCLUDE_PATH("../../src/app/application/config")

/*========== Definitions and Implementations for Unit Test ==================*/

/*
 * WHY THESE ARE HAND-WRITTEN AND NOT CMock MOCKS
 * ----------------------------------------------
 * The obvious way to test this wrapper is to include "Mocknxp_afe.h" and use
 * NXP_Measure_ExpectAndReturn(). That does not work here, and the reason is
 * worth recording because it is not obvious from the failure.
 *
 * "Mocknxp_afe.h" is CMock's mock OF "nxp_afe.h". The module under test is
 * "nxp_afe.c". Both have the same base name. When Ceedling sees that a test
 * mocks a header, it treats that base name as mocked and does NOT compile the
 * same-named source into the test executable -- so TEST_SOURCE_FILE("nxp_afe.c")
 * is silently ineffective and the link fails with all ten AFE_* wrappers
 * undefined:
 *
 *   Undefined symbols for architecture arm64:
 *     "_AFE_TriggerIc", ... "_AFE_IdentifyAfes"
 *
 * This was confirmed two ways: an #error SIL_PROBE_nxp_afe injected into
 * nxp_afe.c did not stop the build, and no nxp_afe.o was ever produced in
 * test/out/test_nxp_afe/. Removing the mock include and providing the ten
 * NXP_* definitions by hand makes the same TEST_SOURCE_FILE take effect and the
 * wrappers link.
 *
 * Tests that mock one header and compile a differently-named source are
 * unaffected; tests/unit/app/driver/afe/ltc/api/test_ltc_afe.c is the working
 * counter-example, mocking "ltc.h" while compiling "ltc_afe.c".
 *
 * The stubs below are the pattern already used in this suite for a mocked
 * header that would otherwise collide: see test_uart_sci_notification.c
 * ("Manually mocking functions from HL_sci.h") and
 * test_spi_spi_notification.c ("Manually mocking functions from HL_spi.h").
 * Each records the argument it received and returns a value the test sets, so
 * the assertions below check what the wrapper actually forwarded.
 */

/* One recorder PER string-indexed callee, not one shared recorder. A single
 * shared variable cannot tell AFE_RequestEepromRead forwarding to
 * NXP_RequestEepromRead from it forwarding to NXP_RequestEepromWrite, because
 * both record the same value into the same place. That gap was found by
 * perturbing nxp_afe.c:87 to call the write callee instead of the read one --
 * the test stayed green. The separate recorders below are the fix, and
 * testNxpAfeStringIndexedForwardersPassTheIndex asserts each of them. */
/** string argument each NXP_Request* stub was called with */
static uint8_t nxpStubEepromReadArg;
static uint8_t nxpStubEepromWriteArg;
static uint8_t nxpStubTemperatureReadArg;
static uint8_t nxpStubBalancingFeedbackReadArg;
static uint8_t nxpStubOpenWireCheckArg;
/** status the no-argument NXP_* stubs return, set by each test */
static STD_RETURN_TYPE_e nxpStubReturnValue;
/** value NXP_IsFirstMeasurementCycleFinished reports, taken from the status */
static bool nxpStubFirstCycleFinished;
/** sentinel pointer NXP_IdentifyAfes hands back */
static uint64_t nxpStubAfeMask = 0u;
/** call counter, so a wrapper that calls nothing is distinguishable */
static uint32_t nxpStubCallCount;

static void NxpStubReset(void) {
    nxpStubEepromReadArg            = 0xFFu;
    nxpStubEepromWriteArg           = 0xFFu;
    nxpStubTemperatureReadArg       = 0xFFu;
    nxpStubBalancingFeedbackReadArg = 0xFFu;
    nxpStubOpenWireCheckArg         = 0xFFu;
    nxpStubReturnValue     = STD_OK;
    nxpStubFirstCycleFinished = false;
    nxpStubCallCount       = 0u;
}

STD_RETURN_TYPE_e NXP_Measure(void) {
    nxpStubCallCount++;
    return nxpStubReturnValue;
}
STD_RETURN_TYPE_e NXP_Initialize(void) {
    nxpStubCallCount++;
    return nxpStubReturnValue;
}
STD_RETURN_TYPE_e NXP_RequestEepromRead(uint8_t string) {
    nxpStubCallCount++;
    nxpStubEepromReadArg = string;
    return nxpStubReturnValue;
}
STD_RETURN_TYPE_e NXP_RequestEepromWrite(uint8_t string) {
    nxpStubCallCount++;
    nxpStubEepromWriteArg = string;
    return nxpStubReturnValue;
}
STD_RETURN_TYPE_e NXP_RequestTemperatureRead(uint8_t string) {
    nxpStubCallCount++;
    nxpStubTemperatureReadArg = string;
    return nxpStubReturnValue;
}
STD_RETURN_TYPE_e NXP_RequestBalancingFeedbackRead(uint8_t string) {
    nxpStubCallCount++;
    nxpStubBalancingFeedbackReadArg = string;
    return nxpStubReturnValue;
}
STD_RETURN_TYPE_e NXP_RequestOpenWireCheck(uint8_t string) {
    nxpStubCallCount++;
    nxpStubOpenWireCheckArg = string;
    return nxpStubReturnValue;
}
STD_RETURN_TYPE_e NXP_StartMeasurement(void) {
    nxpStubCallCount++;
    return nxpStubReturnValue;
}
bool NXP_IsFirstMeasurementCycleFinished(void) {
    nxpStubCallCount++;
    return nxpStubFirstCycleFinished;
}
uint64_t *NXP_IdentifyAfes(void) {
    nxpStubCallCount++;
    return &nxpStubAfeMask;
}

/*========== Setup and Teardown =============================================*/
void setUp(void) {
    NxpStubReset();
}

void tearDown(void) {
}

/*========== Test Cases =====================================================*/

/**
 * @brief   nxp_afe.c is the AFE wrapper layer: ten functions that each
 *          validate their argument and forward to exactly one NXP_* function.
 *          The forwarding is the contract -- this file is the seam the generic
 *          AFE interface (afe.h) is implemented over, so a wrapper that
 *          forwarded to the wrong NXP_* function would send a read to the wrong
 *          place while still returning a plausible status.
 * @details nxp_afe.c:78-121, one wrapper per callee:
 *            AFE_TriggerIc                        -> NXP_Measure()                 :78
 *            AFE_Initialize                       -> NXP_Initialize()              :82
 *            AFE_RequestEepromRead                -> NXP_RequestEepromRead(string) :86
 *            AFE_RequestEepromWrite               -> NXP_RequestEepromWrite(string) :91
 *            AFE_RequestTemperatureRead           -> NXP_RequestTemperatureRead(s)  :96
 *            AFE_RequestBalancingFeedbackRead     -> NXP_RequestBalancingFeedbackRead(s) :101
 *            AFE_RequestOpenWireCheck             -> NXP_RequestOpenWireCheck(s)   :106
 *            AFE_StartMeasurement                 -> NXP_StartMeasurement()        :111
 *            AFE_IsFirstMeasurementCycleFinished  -> NXP_IsFirstMeasurementCycleFinished() :115
 *            AFE_IdentifyAfes                     -> NXP_IdentifyAfes()            :119
 *          The stub return value is pinned before each call and the wrapper's
 *          own return is compared against the LITERAL status, never against the
 *          same variable the stub returns, so a wrapper that discarded the
 *          callee's status and returned a constant would fail here.
 */
void testNxpAfeNoArgumentForwardersReturnTheCalleeStatus(void) {
    /* ======= Assertion tests ============================================= */
    nxpStubReturnValue = STD_NOT_OK;
    TEST_ASSERT_EQUAL_INT((int)STD_NOT_OK, (int)AFE_TriggerIc());
    TEST_ASSERT_EQUAL_UINT32(1u, nxpStubCallCount);

    nxpStubReturnValue = STD_OK;
    TEST_ASSERT_EQUAL_INT((int)STD_OK, (int)AFE_Initialize());
    TEST_ASSERT_EQUAL_UINT32(2u, nxpStubCallCount);

    nxpStubReturnValue = STD_NOT_OK;
    TEST_ASSERT_EQUAL_INT((int)STD_NOT_OK, (int)AFE_StartMeasurement());
    TEST_ASSERT_EQUAL_UINT32(3u, nxpStubCallCount);
}

/**
 * @brief   The boolean wrapper must forward the callee's bool unchanged, in
 *          both directions. A wrapper that hard-coded either value would pass a
 *          test that exercised only one of them.
 * @details nxp_afe.c:115-117 is a bare `return NXP_IsFirstMeasurementCycleFinished();`
 */
void testNxpAfeFirstMeasurementCycleFinishedForwardsBothValues(void) {
    /* ======= Assertion tests ============================================= */
    nxpStubFirstCycleFinished = false;
    TEST_ASSERT_FALSE(AFE_IsFirstMeasurementCycleFinished());
    nxpStubFirstCycleFinished = true;
    TEST_ASSERT_TRUE(AFE_IsFirstMeasurementCycleFinished());
    /* one call each, so neither value came from a cached result */
    TEST_ASSERT_EQUAL_UINT32(2u, nxpStubCallCount);
}

/**
 * @brief   The five string-indexed wrappers must pass the index through
 *          unchanged. The stub records the argument it received, and the test
 *          compares that recording against the literal 0, so a wrapper that
 *          forwarded a different index, or forwarded it to the wrong callee,
 *          fails.
 * @details nxp_afe.c:86-109. BS_NR_OF_STRINGS is (1u)
 *          (battery_system_cfg.h:109), so 0 is the only valid index and the
 *          rejection of an out-of-range index is asserted separately below.
 */
void testNxpAfeStringIndexedForwardersPassTheIndex(void) {
    /* ======= Assertion tests ============================================= */
    /* only string 0 exists in this configuration; BS_NR_OF_STRINGS is (1u) from
     * battery_system_cfg_unit_test.h:124, the unit-test override of
     * battery_system_cfg.h:109 (included at battery_system_cfg.h:342) */
    TEST_ASSERT_EQUAL_UINT32(1u, (uint32_t)BS_NR_OF_STRINGS);

    /* Each block resets the recorders first, then asserts BOTH that the wrapper
     * returned the callee's status and that the callee the wrapper SHOULD have
     * called received the index. After a reset every recorder is 0xFF, so the
     * pair of assertions per block is a wrong-callee detector: had
     * AFE_RequestEepromRead forwarded to NXP_RequestEepromWrite, then
     * nxpStubEepromWriteArg would read 0 and nxpStubEepromReadArg would still
     * read 0xFF, and both assertions would fail.
     *
     * The reset is what makes the second assertion valid. Without it the
     * recorder of a callee invoked earlier in the same case legitimately holds
     * its value, and asserting it still held 0xFF would be asserting something
     * false rather than something strong. */
    nxpStubReturnValue = STD_OK;
    NxpStubReset();
    nxpStubReturnValue = STD_OK;
    TEST_ASSERT_EQUAL_INT((int)STD_OK, (int)AFE_RequestEepromRead(0u));
    TEST_ASSERT_EQUAL_UINT8(0u, nxpStubEepromReadArg);
    TEST_ASSERT_EQUAL_UINT8(0xFFu, nxpStubEepromWriteArg);

    nxpStubReturnValue = STD_NOT_OK;
    NxpStubReset();
    nxpStubReturnValue = STD_NOT_OK;
    TEST_ASSERT_EQUAL_INT((int)STD_NOT_OK, (int)AFE_RequestEepromWrite(0u));
    TEST_ASSERT_EQUAL_UINT8(0u, nxpStubEepromWriteArg);
    TEST_ASSERT_EQUAL_UINT8(0xFFu, nxpStubEepromReadArg);

    nxpStubReturnValue = STD_OK;
    NxpStubReset();
    nxpStubReturnValue = STD_OK;
    TEST_ASSERT_EQUAL_INT((int)STD_OK, (int)AFE_RequestTemperatureRead(0u));
    TEST_ASSERT_EQUAL_UINT8(0u, nxpStubTemperatureReadArg);
    TEST_ASSERT_EQUAL_UINT8(0xFFu, nxpStubEepromWriteArg);

    nxpStubReturnValue = STD_NOT_OK;
    NxpStubReset();
    nxpStubReturnValue = STD_NOT_OK;
    TEST_ASSERT_EQUAL_INT((int)STD_NOT_OK, (int)AFE_RequestBalancingFeedbackRead(0u));
    TEST_ASSERT_EQUAL_UINT8(0u, nxpStubBalancingFeedbackReadArg);
    TEST_ASSERT_EQUAL_UINT8(0xFFu, nxpStubTemperatureReadArg);

    nxpStubReturnValue = STD_OK;
    NxpStubReset();
    nxpStubReturnValue = STD_OK;
    TEST_ASSERT_EQUAL_INT((int)STD_OK, (int)AFE_RequestOpenWireCheck(0u));
    TEST_ASSERT_EQUAL_UINT8(0u, nxpStubOpenWireCheckArg);
    TEST_ASSERT_EQUAL_UINT8(0xFFu, nxpStubBalancingFeedbackReadArg);

    /* the last block's reset zeroed the counter, so exactly one forward is
     * counted for the last call; the earlier four are covered by the four
     * status assertions above, each of which fails if its callee is not called */
    TEST_ASSERT_EQUAL_UINT32(1u, nxpStubCallCount);
}

/**
 * @brief   Each string-indexed wrapper guards its argument with
 *          FAS_ASSERT(string < BS_NR_OF_STRINGS). Under UNITY_UNIT_TEST that
 *          macro is `if (!(x)) Throw(0)` (fassert.h:250-252), so an
 *          out-of-range string raises a CException. Asserting the throw is what
 *          distinguishes a wrapper that validates from one that only forwards.
 * @details nxp_afe.c:87, 92, 97, 102 and 107 each carry the guard. BS_NR_OF_STRINGS
 *          is 1u, so index 1 is the first invalid one, and 0xFF the largest.
 *          The stub call counter is asserted to be zero afterwards, which is
 *          what proves the guard fires BEFORE the forward rather than after it.
 */
/* cspell:disable-next-line */
void testNxpAfeRejectsOutOfRangeStringIndex(void) {
    /* ======= Assertion tests ============================================= */
    TEST_ASSERT_FAIL_ASSERT(AFE_RequestEepromRead(1u));
    TEST_ASSERT_FAIL_ASSERT(AFE_RequestEepromWrite(1u));
    TEST_ASSERT_FAIL_ASSERT(AFE_RequestTemperatureRead(1u));
    TEST_ASSERT_FAIL_ASSERT(AFE_RequestBalancingFeedbackRead(1u));
    TEST_ASSERT_FAIL_ASSERT(AFE_RequestOpenWireCheck(1u));
    TEST_ASSERT_FAIL_ASSERT(AFE_RequestEepromRead(0xFFu));
    /* the guard fired before any forward: no stub was ever entered */
    TEST_ASSERT_EQUAL_UINT32_MESSAGE(0u, nxpStubCallCount,
                                     "an out-of-range string must not reach the NXP layer");
}

/**
 * @brief   AFE_IdentifyAfes returns a pointer rather than a status, so the
 *          wrapper's contract is that the pointer the callee produced is the
 *          pointer the caller receives. The identity is asserted, not a
 *          dereferenced value: dereferencing would be reading whatever the mask
 *          happens to hold, which is not what the wrapper promises, and
 *          inventing a mask value would be fabricating a device reading.
 * @details nxp_afe.c:119-121 is a bare `return NXP_IdentifyAfes();`. The
 *          sentinel is a file-static object in this test, so its address is
 *          known without any assumption about the driver's own storage.
 */
void testNxpAfeIdentifyAfesReturnsTheCalleePointer(void) {
    /* ======= Assertion tests ============================================= */
    uint64_t *const pResult = AFE_IdentifyAfes();
    TEST_ASSERT_EQUAL_PTR(&nxpStubAfeMask, pResult);
    TEST_ASSERT_EQUAL_UINT32(1u, nxpStubCallCount);
}
