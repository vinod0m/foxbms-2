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
 * @file    test_state_estimation.c
 * @author  foxBMS Team
 * @date    2020-10-14 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Tests for SOH module responsible for calculation of state-of-health
 * @details Tests for Invalid Inputs
 *
 */

/*========== Includes =======================================================*/
#include "unity.h"
#include "Mockdatabase.h"

#include "state_estimation.h"
#include "test_assert_helper.h"

#include <stdbool.h>

/*========== Unit Testing Framework Directives ==============================*/
TEST_SOURCE_FILE("soc_none.c")
TEST_SOURCE_FILE("soe_none.c")
TEST_SOURCE_FILE("soh_none.c")

TEST_INCLUDE_PATH("../../src/app/application/algorithm/state_estimation")

/*========== Definitions and Implementations for Unit Test ==================*/


/*========== Content check for the untyped `void *` data-block arguments ====
 *
 * #DATA_Write1DataBlock and #DATA_Write3DataBlocks take untyped `void *`
 * pointers. CMock cannot size a `void *`, so `:when_ptr: :compare_data`
 * silently degrades to UNITY_TEST_ASSERT_EQUAL_PTR. These blocks are file-scope
 * statics of state_estimation.c:66-68, private to that translation unit, so the
 * test cannot address them and an address comparison can never hold.
 *
 * A full content comparison is also impossible here, and would be wrong: each
 * #SE_Initialize* / #SE_RunStateEstimations call *writes into* its block before
 * publishing it (state_estimation.c:79-80, :85-86, :91-92, :96-100), so the
 * published content legitimately differs from this file's pristine copies by
 * construction. What is both meaningful and stable is the block identity in the
 * header, which is what records *which* database entry was published.
 *
 * A CMock `_Stub` returns from the callback branch of the generated mock before
 * CMock's own argument, call-count and ordering assertions, so what those
 * provided is re-established explicitly:
 *
 *  - CALL COUNT, by the `_CallCount()` assertion at the end of each test. The
 *    original registered exactly one expectation per test, so each pins 1.
 *  - PUBLISH IDENTITY AND EXACTLY-ONCE, by the per-block step counters: each of
 *    `DATA_BLOCK_ID_SOC`, `_SOH` and `_SOE` has its own counter that must be 0 on
 *    arrival and is set to 1, and an unrecognised id fails the callback. So no
 *    block may be published twice, none may be skipped, and no other block may
 *    be published in its place.
 *  - ARGUMENT ORDER, for the one call that carries three blocks:
 *    `DATA_Write3DataBlocksCallback` asserts the SOC/SOH/SOE ids in the order
 *    state_estimation.c:100 passes them.
 *
 * What is not restored, stated rather than glossed: the original
 * `_ExpectAndReturn` registrations also took part in CMock's global
 * `GlobalVerifyOrder` counter, so they additionally pinned the relative order of
 * these publish calls against any other mock in the same test. Each of the four
 * tests here drives exactly one of the four functions and no other mock, so
 * with a single call in play a global order counter carries no information the
 * assertions above do not already carry.
 */
static uint8_t stepSoc = 0u;
static uint8_t stepSoh = 0u;
static uint8_t stepSoe = 0u;

static STD_RETURN_TYPE_e DATA_Write1DataBlockCallback(
    void *pDataFromSender0,
    uint32_t dataLength0,
    int cmock_num_calls) {
    (void)cmock_num_calls;
    (void)dataLength0;
    const DATA_BLOCK_HEADER_s *pHeader = (const DATA_BLOCK_HEADER_s *)pDataFromSender0;
    TEST_ASSERT_NOT_NULL(pHeader);
    switch (pHeader->uniqueId) {
        case DATA_BLOCK_ID_SOC:
            TEST_ASSERT_EQUAL_UINT8(0u, stepSoc);
            stepSoc = 1u;
            break;
        case DATA_BLOCK_ID_SOH:
            TEST_ASSERT_EQUAL_UINT8(0u, stepSoh);
            stepSoh = 1u;
            break;
        case DATA_BLOCK_ID_SOE:
            TEST_ASSERT_EQUAL_UINT8(0u, stepSoe);
            stepSoe = 1u;
            break;
        default:
            TEST_FAIL_MESSAGE("DATA_Write1DataBlock published an unexpected data block");
            break;
    }
    return STD_OK;
}

static STD_RETURN_TYPE_e DATA_Write3DataBlocksCallback(
    void *pDataFromSender0,
    uint32_t dataLength0,
    void *pDataFromSender1,
    uint32_t dataLength1,
    void *pDataFromSender2,
    uint32_t dataLength2,
    int cmock_num_calls) {
    (void)cmock_num_calls;
    (void)dataLength0;
    (void)dataLength1;
    (void)dataLength2;
    const DATA_BLOCK_HEADER_s *pHeader0 = (const DATA_BLOCK_HEADER_s *)pDataFromSender0;
    const DATA_BLOCK_HEADER_s *pHeader1 = (const DATA_BLOCK_HEADER_s *)pDataFromSender1;
    const DATA_BLOCK_HEADER_s *pHeader2 = (const DATA_BLOCK_HEADER_s *)pDataFromSender2;
    TEST_ASSERT_NOT_NULL(pHeader0);
    TEST_ASSERT_NOT_NULL(pHeader1);
    TEST_ASSERT_NOT_NULL(pHeader2);
    /* published in the order state_estimation.c:100 passes them */
    TEST_ASSERT_EQUAL(DATA_BLOCK_ID_SOC, pHeader0->uniqueId);
    TEST_ASSERT_EQUAL(DATA_BLOCK_ID_SOH, pHeader1->uniqueId);
    TEST_ASSERT_EQUAL(DATA_BLOCK_ID_SOE, pHeader2->uniqueId);
    return STD_OK;
}

/*========== Setup and Teardown =============================================*/
void setUp(void) {
}

void tearDown(void) {
}

/*========== Test Cases =====================================================*/
/** test invalid input on interfaces */
void testInvalidInput(void) {
    DATA_BLOCK_SOC_s table_testSoc = {.header.uniqueId = DATA_BLOCK_ID_SOC};
    DATA_BLOCK_SOH_s table_testSoh = {.header.uniqueId = DATA_BLOCK_ID_SOH};
    DATA_BLOCK_SOE_s table_testSoe = {.header.uniqueId = DATA_BLOCK_ID_SOE};
    TEST_ASSERT_FAIL_ASSERT(SE_InitializeSoc(true, BS_NR_OF_STRINGS));

    TEST_ASSERT_FAIL_ASSERT(SE_InitializeSoe(true, BS_NR_OF_STRINGS));

    TEST_ASSERT_FAIL_ASSERT(SE_InitializeSoh(BS_NR_OF_STRINGS));

    TEST_ASSERT_FAIL_ASSERT(SE_InitializeStateOfCharge(NULL_PTR, true, BS_NR_OF_STRINGS - 1u));
    TEST_ASSERT_FAIL_ASSERT(SE_InitializeStateOfCharge(&table_testSoc, true, BS_NR_OF_STRINGS));

    TEST_ASSERT_FAIL_ASSERT(SE_CalculateStateOfCharge(NULL_PTR));

    TEST_ASSERT_FAIL_ASSERT(SE_InitializeStateOfEnergy(NULL_PTR, true, BS_NR_OF_STRINGS - 1u));
    TEST_ASSERT_FAIL_ASSERT(SE_InitializeStateOfEnergy(&table_testSoe, true, BS_NR_OF_STRINGS));

    TEST_ASSERT_FAIL_ASSERT(SE_CalculateStateOfEnergy(NULL_PTR));

    TEST_ASSERT_FAIL_ASSERT(SE_InitializeStateOfHealth(NULL_PTR, BS_NR_OF_STRINGS - 1u));
    TEST_ASSERT_FAIL_ASSERT(SE_InitializeStateOfHealth(&table_testSoh, BS_NR_OF_STRINGS));

    TEST_ASSERT_FAIL_ASSERT(SE_CalculateStateOfHealth(NULL_PTR));
}

void testSE_InitializeSoc(void) {
    bool ccPresent       = true;
    uint8_t stringNumber = 0u;
    DATA_Write1DataBlock_Stub(DATA_Write1DataBlockCallback);
    SE_InitializeSoc(ccPresent, stringNumber);
    TEST_ASSERT_EQUAL_UINT8(1u, stepSoc);
    TEST_ASSERT_EQUAL_INT(1, DATA_Write1DataBlock_CallCount());
}

void testSE_InitializeSoe(void) {
    bool ecPresent       = true;
    uint8_t stringNumber = 0u;
    DATA_Write1DataBlock_Stub(DATA_Write1DataBlockCallback);
    SE_InitializeSoe(ecPresent, stringNumber);
    TEST_ASSERT_EQUAL_UINT8(1u, stepSoe);
    TEST_ASSERT_EQUAL_INT(1, DATA_Write1DataBlock_CallCount());
}

void testSE_InitializeSoh(void) {
    uint8_t stringNumber = 0u;
    DATA_Write1DataBlock_Stub(DATA_Write1DataBlockCallback);
    SE_InitializeSoh(stringNumber);
    TEST_ASSERT_EQUAL_UINT8(1u, stepSoh);
    TEST_ASSERT_EQUAL_INT(1, DATA_Write1DataBlock_CallCount());
}

void testSE_RunStateEstimations(void) {
    DATA_Write3DataBlocks_Stub(DATA_Write3DataBlocksCallback);
    SE_RunStateEstimations();
    TEST_ASSERT_EQUAL_INT(1, DATA_Write3DataBlocks_CallCount());
}
