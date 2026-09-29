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
 * @file    test_soc_lookup-table.c
 * @author  foxBMS Team
 * @date    2025-07-07 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Tests for SOC module responsible for calculation of SOC
 * @details Tests Get state of charge from voltage
 *                check database soc percentage limit
 *                update nvm values
 *
 */

/*========== Includes =======================================================*/
#include "unity.h"
#include "Mockbms.h"
#include "Mockdatabase.h"
#include "Mockfram.h"

#include "battery_cell_cfg.h"
#include "soc_lookup-table_cfg.h"

#include "foxmath.h"
#include "state_estimation.h"
#include "test_assert_helper.h"

#include <math.h>

/*========== Unit Testing Framework Directives ==============================*/
TEST_SOURCE_FILE("soc_lookup-table.c")
TEST_SOURCE_FILE("soe_none.c")
TEST_SOURCE_FILE("soh_none.c")

TEST_INCLUDE_PATH("../../src/app/application/algorithm/state_estimation")
TEST_INCLUDE_PATH("../../src/app/application/algorithm/state_estimation/soc/lookup-table")
TEST_INCLUDE_PATH("../../src/app/application/bms")
TEST_INCLUDE_PATH("../../src/app/driver/config")
TEST_INCLUDE_PATH("../../src/app/driver/contactor")
TEST_INCLUDE_PATH("../../src/app/driver/foxmath")
TEST_INCLUDE_PATH("../../src/app/driver/fram")
TEST_INCLUDE_PATH("../../src/app/driver/sps")
TEST_INCLUDE_PATH("../../src/app/task/config")

/*========== Definitions and Implementations for Unit Test ==================*/
FRAM_SOC_s fram_soc = {0};
/**local copy of DATA_BLOCK_SOC_s table**/
static DATA_BLOCK_SOC_s cp_pTableSoc = {.header.uniqueId = DATA_BLOCK_ID_SOC};

/*========== Content check for the untyped `void *` data-block argument =====
 *
 * #DATA_Read1DataBlock takes an untyped `void *`. CMock cannot size a `void *`,
 * so `:when_ptr: :compare_data` silently degrades to UNITY_TEST_ASSERT_EQUAL_PTR.
 * The block read here is `soc_tableMinMax`, a file-scope static private to
 * soc_lookup-table.c:85, so the test cannot address it and an address
 * comparison can never hold.
 *
 * The fixture this test used, `cp_pTableMinMax`, was declared a
 * #DATA_BLOCK_SOC_s even though the product reads a #DATA_BLOCK_MIN_MAX_s (32
 * bytes vs 52 measured), so it could not be a content comparison of the right
 * type either. The block identity in the header is the one property that an
 * address comparison could ever have been about, and the one that is both
 * meaningful and stable, so it is asserted explicitly. The injected fixture is
 * given the correct #DATA_BLOCK_MIN_MAX_s type so the value written into the
 * product's block is sized correctly.
 *
 * A CMock `_Stub` returns from the callback branch of the generated mock before
 * CMock's own argument, call-count and ordering checks, and it also bypasses
 * the `_ReturnThruPtr` chain, so all of that is put back explicitly:
 *
 *  - the call count is re-asserted by the `_CallCount()` assertion at the end
 *    of the test (the original single `_ExpectAndReturn` pinned exactly one
 *    read);
 *  - the injection the `_ReturnThruPtr` call performed is performed by the
 *    callback instead;
 *  - the ordering is re-pinned by `FRAM_WriteData_AddCallback` below. The
 *    original sequence was
 *        DATA_Read1DataBlock_ExpectAndReturn(...), FRAM_WriteData_ExpectAndReturn(...)
 *    and with `:enforce_strict_ordering` that fixed the read strictly before
 *    the persist. `_Stub` takes the read out of CMock's global
 *    `GlobalVerifyOrder` counter, so the two could be swapped. `_AddCallback`
 *    is used rather than a second `_Stub` precisely because it sets
 *    `CallbackBool`, which makes the generated mock run its ordering and
 *    argument checks *before* calling back -- so the `FRAM_BLOCK_ID_SOC`
 *    argument check and the once-only requirement on `FRAM_WriteData` are kept,
 *    and read-before-write is restored on top.
 */
static DATA_BLOCK_MIN_MAX_s tableMinMaxInjected = {
    .header.uniqueId = DATA_BLOCK_ID_MIN_MAX,
    .header.timestamp = 10u};

static STD_RETURN_TYPE_e DATA_Read1DataBlockCallback(void *pDataToReceiver0, int cmock_num_calls) {
    (void)cmock_num_calls;
    TEST_ASSERT_NOT_NULL(pDataToReceiver0);
    DATA_BLOCK_MIN_MAX_s *pMinMax = (DATA_BLOCK_MIN_MAX_s *)pDataToReceiver0;
    TEST_ASSERT_EQUAL(DATA_BLOCK_ID_MIN_MAX, pMinMax->header.uniqueId);
    *pMinMax = tableMinMaxInjected;
    return STD_OK;
}

/* observation-only: re-pins read-before-write, see the block comment */
static FRAM_RETURN_TYPE_e FRAM_WriteDataCallback(FRAM_BLOCK_ID_e blockId, int cmock_num_calls) {
    (void)cmock_num_calls;
    (void)blockId; /* the argument is still checked by the _ExpectAndReturn */
    /* the min/max block must have been read before the result is persisted */
    TEST_ASSERT_EQUAL_INT(1, DATA_Read1DataBlock_CallCount());
    return FRAM_ACCESS_OK;
}
/** Maximum SOC in percentage */
#define SOC_MAXIMUM_SOC_perc (100.0f)
/** Minimum SOC in percentage */
#define SOC_MINIMUM_SOC_perc (0.0f)

/*========== Setup and Teardown =============================================*/
void setUp(void) {
}

void tearDown(void) {
}

/*========== Test Cases =====================================================*/
void testSE_InitializeStateOfCharge(void) {
    TEST_ASSERT_FAIL_ASSERT(SE_InitializeStateOfCharge(NULL_PTR, true, 0));
    TEST_ASSERT_FAIL_ASSERT(SE_InitializeStateOfCharge(&cp_pTableSoc, true, BS_NR_OF_STRINGS));
    SE_InitializeStateOfCharge(&cp_pTableSoc, true, 0);
}

void testSE_CalculateStateOfCharge(void) {

    DATA_Read1DataBlock_Stub(DATA_Read1DataBlockCallback);
    FRAM_WriteData_ExpectAndReturn(FRAM_BLOCK_ID_SOC, FRAM_ACCESS_OK);
    FRAM_WriteData_AddCallback(FRAM_WriteDataCallback);
    SE_CalculateStateOfCharge(&cp_pTableSoc);
    TEST_ASSERT_EQUAL_INT(1, DATA_Read1DataBlock_CallCount());
}
void testSE_GetStateOfChargeFromVoltage(void) {
    /* LUT values*/
    TEST_ASSERT_EQUAL(100.0f, SE_GetStateOfChargeFromVoltage(4123));
    TEST_ASSERT_EQUAL(50.0f, SE_GetStateOfChargeFromVoltage(3636));
    TEST_ASSERT_EQUAL(26.0f, SE_GetStateOfChargeFromVoltage(3461));
    TEST_ASSERT_EQUAL(1.0f, SE_GetStateOfChargeFromVoltage(2716));
    /* Minimum value */
    TEST_ASSERT_EQUAL(SOC_MINIMUM_SOC_perc, SE_GetStateOfChargeFromVoltage(2700));
    /* Maximum value */
    TEST_ASSERT_EQUAL(SOC_MAXIMUM_SOC_perc, SE_GetStateOfChargeFromVoltage(4200));
}

void testSOC_UpdateNvmValues(void) {
    TEST_ASSERT_FAIL_ASSERT(TEST_SOC_UpdateNvmValues(&cp_pTableSoc, BS_NR_OF_STRINGS));
    for (uint8_t s = 0; s < BS_NR_OF_STRINGS; s++) {
        TEST_ASSERT_FAIL_ASSERT(TEST_SOC_UpdateNvmValues(NULL_PTR, s));
        TEST_ASSERT_PASS_ASSERT(TEST_SOC_UpdateNvmValues(&cp_pTableSoc, s));

        cp_pTableSoc.averageSoc_perc[s] = 1.0f;
        TEST_SOC_UpdateNvmValues(&cp_pTableSoc, s);
        TEST_ASSERT_EQUAL_FLOAT(1.0f, fram_soc.averageSoc_perc[s]);

        cp_pTableSoc.minimumSoc_perc[s] = 1.0f;
        TEST_SOC_UpdateNvmValues(&cp_pTableSoc, s);
        TEST_ASSERT_EQUAL_FLOAT(1.0f, fram_soc.minimumSoc_perc[s]);

        cp_pTableSoc.maximumSoc_perc[s] = 1.0f;
        TEST_SOC_UpdateNvmValues(&cp_pTableSoc, s);
        TEST_ASSERT_EQUAL_FLOAT(1.0f, fram_soc.maximumSoc_perc[s]);

        cp_pTableSoc.chargeThroughput_As[s] = 1.0f;
        TEST_SOC_UpdateNvmValues(&cp_pTableSoc, s);
        TEST_ASSERT_EQUAL_FLOAT(1.0f, fram_soc.chargeThroughput_As[s]);

        cp_pTableSoc.dischargeThroughput_As[s] = 1.0f;
        TEST_SOC_UpdateNvmValues(&cp_pTableSoc, s);
        TEST_ASSERT_EQUAL_FLOAT(1.0f, fram_soc.dischargeThroughput_As[s]);
    }
}

void testSE_GetSocStateInitialized(void) {
    TEST_ASSERT_EQUAL(true, TEST_SE_GetSocStateInitialized());
}

void testSOC_CheckDatabaseSocPercentageLimits(void) {
    TEST_ASSERT_FAIL_ASSERT(TEST_SOC_CheckDatabaseSocPercentageLimits(&cp_pTableSoc, BS_NR_OF_STRINGS));
    for (uint8_t s = 0; s < BS_NR_OF_STRINGS; s++) {
        TEST_ASSERT_FAIL_ASSERT(TEST_SOC_CheckDatabaseSocPercentageLimits(NULL_PTR, s));
        TEST_ASSERT_PASS_ASSERT(TEST_SOC_CheckDatabaseSocPercentageLimits(&cp_pTableSoc, s));

        cp_pTableSoc.averageSoc_perc[s] = 101.0f;
        TEST_SOC_CheckDatabaseSocPercentageLimits(&cp_pTableSoc, s);
        TEST_ASSERT_EQUAL_FLOAT(SOC_MAXIMUM_SOC_perc, cp_pTableSoc.averageSoc_perc[s]);
        cp_pTableSoc.averageSoc_perc[s] = -1.0f;
        TEST_SOC_CheckDatabaseSocPercentageLimits(&cp_pTableSoc, s);
        TEST_ASSERT_EQUAL_FLOAT(SOC_MINIMUM_SOC_perc, cp_pTableSoc.averageSoc_perc[s]);

        cp_pTableSoc.minimumSoc_perc[s] = 101.0f;
        TEST_SOC_CheckDatabaseSocPercentageLimits(&cp_pTableSoc, s);
        TEST_ASSERT_EQUAL_FLOAT(SOC_MAXIMUM_SOC_perc, cp_pTableSoc.minimumSoc_perc[s]);
        cp_pTableSoc.minimumSoc_perc[s] = -1.0f;
        TEST_SOC_CheckDatabaseSocPercentageLimits(&cp_pTableSoc, s);
        TEST_ASSERT_EQUAL_FLOAT(SOC_MINIMUM_SOC_perc, cp_pTableSoc.minimumSoc_perc[s]);

        cp_pTableSoc.maximumSoc_perc[s] = 101.0f;
        TEST_SOC_CheckDatabaseSocPercentageLimits(&cp_pTableSoc, s);
        TEST_ASSERT_EQUAL_FLOAT(SOC_MAXIMUM_SOC_perc, cp_pTableSoc.maximumSoc_perc[s]);
        cp_pTableSoc.maximumSoc_perc[s] = -1.0f;
        TEST_SOC_CheckDatabaseSocPercentageLimits(&cp_pTableSoc, s);
        TEST_ASSERT_EQUAL_FLOAT(SOC_MINIMUM_SOC_perc, cp_pTableSoc.maximumSoc_perc[s]);
    }
}
