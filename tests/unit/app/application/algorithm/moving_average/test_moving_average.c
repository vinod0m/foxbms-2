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
 * @file    test_moving_average.c
 * @author  foxBMS Team
 * @date    2020-07-01 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Test of the algorithm module
 * @details TODO
 *
 */

/*========== Includes =======================================================*/
#include "unity.h"
#include "Mockdatabase.h"
#include "Mockos.h"

#include "moving_average.h"

/*========== Unit Testing Framework Directives ==============================*/
TEST_INCLUDE_PATH("../../src/app/application/algorithm/config")
TEST_INCLUDE_PATH("../../src/app/application/algorithm/moving_average")

TEST_SOURCE_FILE("moving_average.c")

/*========== Definitions and Implementations for Unit Test ==================*/
#define NUM_DATA_READ_SUB_CALLS (1)

typedef struct {
    DATA_BLOCK_CURRENT_s *cur;
    DATA_BLOCK_POWER_s *pow;
    DATA_BLOCK_MOVING_AVERAGE_s *movingAvg;
} DATA_BLOCKS;

DATA_BLOCK_CURRENT_s cur_tab                  = {.header.uniqueId = DATA_BLOCK_ID_CURRENT};
DATA_BLOCK_POWER_s pow_tab                    = {.header.uniqueId = DATA_BLOCK_ID_POWER};
DATA_BLOCK_MOVING_AVERAGE_s movingAverage_tab = {.header.uniqueId = DATA_BLOCK_ID_MOVING_AVERAGE};

/*========== Content check for the untyped `void *` data-block argument =====
 *
 * #DATA_Read1DataBlock and #DATA_Write1DataBlock take an untyped `void *`.
 * CMock cannot size a `void *`, so `:when_ptr: :compare_data` silently degrades
 * to UNITY_TEST_ASSERT_EQUAL_PTR. The block is a function-local static of
 * moving_average.c:187, private to that translation unit, so the test cannot
 * address it and an address comparison can never hold.
 *
 * The two calls need different oracles, because the block is in a different
 * state at each:
 *
 *  - the read (moving_average.c:195) happens before anything writes the block,
 *    so it still holds exactly its initial value and a full content comparison
 *    over the real sizeof is possible and meaningful;
 *
 *  - the write (moving_average.c:438) happens after the averaging arithmetic
 *    has filled the block in, so its content legitimately differs from this
 *    file's pristine copy and a full comparison would be wrong. The meaningful,
 *    stable property is the block identity in the header.
 *
 * A CMock `_Stub` returns from the callback branch of the generated mock before
 * CMock's own argument, call-count and ordering assertions, so both guarantees
 * the original single `_ExpectAndReturn` pair provided are re-established
 * explicitly, and the replacement is not a weakening:
 *
 *  - CALL COUNT, by `TEST_ASSERT_EQUAL_INT(1, ..._CallCount())` for each of the
 *    two functions at the end of the test.
 *  - ORDER, by `stepMovingAverage`: the read sets it to 1 and the write requires
 *    it to be 1 before setting it to 2, and the test asserts 2. So the write
 *    cannot run before its read, which the count alone would not catch.
 *
 * (The `DATA_Read2DataBlocks_Stub` further down is pre-existing and unrelated to
 * this change: it replaced no `_ExpectAndReturn` here and lost nothing.)
 */
static uint8_t stepMovingAverage = 0u;

static STD_RETURN_TYPE_e DATA_Read1DataBlockCallback(void *pDataToReceiver0, int cmock_num_calls) {
    (void)cmock_num_calls;
    const DATA_BLOCK_MOVING_AVERAGE_s *pBlock = (const DATA_BLOCK_MOVING_AVERAGE_s *)pDataToReceiver0;
    TEST_ASSERT_NOT_NULL(pBlock);
    TEST_ASSERT_EQUAL_MEMORY(&movingAverage_tab, pBlock, sizeof(DATA_BLOCK_MOVING_AVERAGE_s));
    stepMovingAverage = 1u;
    return STD_OK;
}

static STD_RETURN_TYPE_e DATA_Write1DataBlockCallback(void *pDataFromSender0, int cmock_num_calls) {
    (void)cmock_num_calls;
    const DATA_BLOCK_MOVING_AVERAGE_s *pBlock = (const DATA_BLOCK_MOVING_AVERAGE_s *)pDataFromSender0;
    TEST_ASSERT_NOT_NULL(pBlock);
    /* the read must have happened first */
    TEST_ASSERT_EQUAL_UINT8(1u, stepMovingAverage);
    TEST_ASSERT_EQUAL(DATA_BLOCK_ID_MOVING_AVERAGE, pBlock->header.uniqueId);
    stepMovingAverage = 2u;
    return STD_OK;
}

DATA_BLOCKS blocks = {
    .cur       = &cur_tab,
    .pow       = &pow_tab,
    .movingAvg = &movingAverage_tab,
};

/*========== Setup and Teardown =============================================*/
void setUp(void) {
    cur_tab.newCurrent = 1;
    pow_tab.newPower   = 1;
}

void tearDown(void) {
}

/*========== Test Cases =====================================================*/
/**
 * @brief   Iterate over a callback that supplies various scenarios and check if they work as expected
 * @details This function uses the callback #MockDATA_ReadBlocks_Callback() in order to inject
 *          other values into the returned database tables.
 */
STD_RETURN_TYPE_e MockDATA_ReadBlocks_Callback(void *pDataToReceiver1, void *pDataToReceiver2, int num_calls) {
    uint8_t newCurrent = 0;
    uint8_t newPower   = 0;

    /* determine a value depending on num_calls (has to be synchronized with test) */
    switch (num_calls) {
        case 0:
            /* Set to new current value */
            newCurrent = 1;
            newPower   = 1;
            break;
        default:
            TEST_FAIL_MESSAGE("DATA_ReadBlocks_Callback was called too often");
    }
    /* ENTER HIGHEST CASE NUMBER IN EXPECT; checks whether all cases are used */
    TEST_ASSERT_EQUAL_MESSAGE(0, (NUM_DATA_READ_SUB_CALLS - 1), "Check code of stub. Something does not fit.");

    if (num_calls >= NUM_DATA_READ_SUB_CALLS) {
        TEST_FAIL_MESSAGE("This stub is fishy");
    }

    /* cast to correct struct */
    ((DATA_BLOCK_CURRENT_s *)pDataToReceiver1)->newCurrent = newCurrent;
    ((DATA_BLOCK_POWER_s *)pDataToReceiver2)->newPower     = newPower;

    return STD_OK;
}

void testALGO_MovingAverage(void) {
    /* tell CMock to use our callback */
    DATA_Read2DataBlocks_Stub(MockDATA_ReadBlocks_Callback);

    DATA_Read1DataBlock_Stub(DATA_Read1DataBlockCallback);
    DATA_Write1DataBlock_Stub(DATA_Write1DataBlockCallback);

    ALGO_MovingAverage();
    TEST_ASSERT_EQUAL_UINT8(2u, stepMovingAverage);
    TEST_ASSERT_EQUAL_INT(1, DATA_Read1DataBlock_CallCount());
    TEST_ASSERT_EQUAL_INT(1, DATA_Write1DataBlock_CallCount());
}
