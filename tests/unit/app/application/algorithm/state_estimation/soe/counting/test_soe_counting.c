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
 * @file    test_soe_counting.c
 * @author  foxBMS Team
 * @date    2020-10-07 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Test for the configuration for SOE
 * @details TODO
 *
 */

/*========== Includes =======================================================*/
#include "unity.h"
#include "Mockbms.h"
#include "Mockdatabase.h"
#include "Mockfram.h"

#include "battery_cell_cfg.h"

#include "foxmath.h"
#include "state_estimation.h"

#include "battery_system_cfg.h"

#include "test_assert_helper.h"

/*========== Unit Testing Framework Directives ==============================*/
TEST_SOURCE_FILE("soc_none.c")
TEST_SOURCE_FILE("soe_counting.c")
TEST_SOURCE_FILE("soh_none.c")

TEST_INCLUDE_PATH("../../src/app/application/algorithm/state_estimation")
TEST_INCLUDE_PATH("../../src/app/application/bms")
TEST_INCLUDE_PATH("../../src/app/driver/config")
TEST_INCLUDE_PATH("../../src/app/driver/contactor")
TEST_INCLUDE_PATH("../../src/app/driver/foxmath")
TEST_INCLUDE_PATH("../../src/app/driver/fram")
TEST_INCLUDE_PATH("../../src/app/driver/sps")
TEST_INCLUDE_PATH("../../src/app/task/config")

/*========== Definitions and Implementations for Unit Test ==================*/
FRAM_SOE_s fram_soe = {0};

/*========== Setup and Teardown =============================================*/
void setUp(void) {
}

void tearDown(void) {
}

/*========== Test Cases =====================================================*/
/* This file builds soc_none.c, soe_counting.c and soh_none.c. The two "none"
 * drivers are the stand-ins used when no state estimation is configured, and
 * their whole contract is what the guards and the single returned value below
 * pin:
 *   SE_InitializeStateOfCharge  soc_none.c:72-76
 *   SE_CalculateStateOfCharge   soc_none.c:78-80
 *   SE_GetStateOfChargeFromVoltage soc_none.c:81-84
 *   SE_InitializeStateOfHealth  soh_none.c:71-74
 *   SE_CalculateStateOfHealth   soh_none.c:76-78 */

/** @brief   SE_InitializeStateOfCharge() rejects a null data block and a string
 *         index outside the configured range (soc_none.c:73 and :75)
 */
void testSE_InitializeStateOfChargeGuardsItsArguments(void) {
    DATA_BLOCK_SOC_s socValues = {.header.uniqueId = DATA_BLOCK_ID_SOC};

    TEST_ASSERT_FAIL_ASSERT(SE_InitializeStateOfCharge(NULL_PTR, true, 0u));
    TEST_ASSERT_FAIL_ASSERT(SE_InitializeStateOfCharge(&socValues, true, BS_NR_OF_STRINGS));
}

/** @brief   SE_InitializeStateOfCharge() accepts the last configured string and
 *         does not write anything into the data block (soc_none.c:72-76)
 */
void testSE_InitializeStateOfChargeAcceptsTheLastString(void) {
    DATA_BLOCK_SOC_s socValues = {.header.uniqueId = DATA_BLOCK_ID_SOC};

    SE_InitializeStateOfCharge(&socValues, true, BS_NR_OF_STRINGS - 1u);
    SE_InitializeStateOfCharge(&socValues, false, 0u);
}

/** @brief   SE_CalculateStateOfCharge() rejects a null data block (soc_none.c:79)
 */
void testSE_CalculateStateOfChargeGuardsItsArgument(void) {
    DATA_BLOCK_SOC_s socValues = {.header.uniqueId = DATA_BLOCK_ID_SOC};

    TEST_ASSERT_FAIL_ASSERT(SE_CalculateStateOfCharge(NULL_PTR));
    SE_CalculateStateOfCharge(&socValues);
}

/** @brief   SE_GetStateOfChargeFromVoltage() reports 0 % for any cell voltage,
 *         because no estimation is configured (soc_none.c:82)
 */
void testSE_GetStateOfChargeFromVoltageIsZero(void) {
    TEST_ASSERT_EQUAL_FLOAT(0.0f, SE_GetStateOfChargeFromVoltage(0));
    TEST_ASSERT_EQUAL_FLOAT(0.0f, SE_GetStateOfChargeFromVoltage(4200));
    TEST_ASSERT_EQUAL_FLOAT(0.0f, SE_GetStateOfChargeFromVoltage(-1000));
}

/** @brief   SE_InitializeStateOfHealth() rejects a null data block and a string
 *         index outside the configured range (soh_none.c:72 and :73)
 */
void testSE_InitializeStateOfHealthGuardsItsArguments(void) {
    DATA_BLOCK_SOH_s sohValues = {.header.uniqueId = DATA_BLOCK_ID_SOH};

    TEST_ASSERT_FAIL_ASSERT(SE_InitializeStateOfHealth(NULL_PTR, 0u));
    TEST_ASSERT_FAIL_ASSERT(SE_InitializeStateOfHealth(&sohValues, BS_NR_OF_STRINGS));
    SE_InitializeStateOfHealth(&sohValues, BS_NR_OF_STRINGS - 1u);
}

/** @brief   SE_CalculateStateOfHealth() rejects a null data block (soh_none.c:77)
 */
void testSE_CalculateStateOfHealthGuardsItsArgument(void) {
    DATA_BLOCK_SOH_s sohValues = {.header.uniqueId = DATA_BLOCK_ID_SOH};

    TEST_ASSERT_FAIL_ASSERT(SE_CalculateStateOfHealth(NULL_PTR));
    SE_CalculateStateOfHealth(&sohValues);
}
