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
 * @file    test_ti_dummy_afe.c
 * @author  foxBMS Team
 * @date    2023-09-11 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Test of the wrapper of the TI dummy AFE API implementation of the
 *          TI AFE API
 * @details TODO
 */

/*========== Includes =======================================================*/

#include "unity.h"

#include "ti_afe.h"

/* ti_dummy_afe.c reaches BS_NR_OF_STRINGS through afe_dma.h -> dma_cfg.h ->
 * battery_system_cfg.h; the same header is included here so the bound the
 * tests use is the same bound the product asserts against. */
#include "afe_dma.h"

#include "test_assert_helper.h"

#include <stdint.h>

/*========== Unit Testing Framework Directives ==============================*/
TEST_SOURCE_FILE("ti_dummy.c")
TEST_SOURCE_FILE("ti_dummy_afe.c")

TEST_INCLUDE_PATH("../../src/app/driver/afe/api")
TEST_INCLUDE_PATH("../../src/app/driver/afe/ti/api")
TEST_INCLUDE_PATH("../../src/app/driver/afe/ti/dummy")
TEST_INCLUDE_PATH("../../src/app/driver/config")
TEST_INCLUDE_PATH("../../tests/unit/support")

/*========== Definitions and Implementations for Unit Test ==================*/

/*========== Setup and Teardown =============================================*/
void setUp(void) {
}

void tearDown(void) {
}

/*========== Test Cases =====================================================*/
/* ti_dummy_afe.c is the TI AFE API wrapper over the TI dummy driver. It is
 * compiled here without any mock, so TIDUM_* are the real dummy driver
 * (src/app/driver/afe/ti/dummy/ti_dummy.c) and every TI_* return value is
 * established by the real chain, not by a stub the test supplies. */

/** @brief   TI_Measure() forwards to TIDUM_Measure(), which reports success
 *         (ti_dummy_afe.c:74-75 -> ti_dummy.c:77-78)
 */
void testTI_MeasureReturnsOk(void) {
    TEST_ASSERT_EQUAL(STD_OK, TI_Measure());
}

/** @brief   TI_Initialize() forwards to TIDUM_Initialize(), which reports
 *         success (ti_dummy_afe.c:77-78 -> ti_dummy.c:80-81)
 */
void testTI_InitializeReturnsOk(void) {
    TEST_ASSERT_EQUAL(STD_OK, TI_Initialize());
}

/** @brief   TI_RequestEepromRead() rejects a string index outside the configured
 *         range (ti_dummy_afe.c:80) and otherwise forwards to the dummy driver,
 *         which reports success (ti_dummy.c:83-85)
 */
void testTI_RequestEepromRead(void) {
    TEST_ASSERT_EQUAL(STD_OK, TI_RequestEepromRead(0u));
    TEST_ASSERT_EQUAL(STD_OK, TI_RequestEepromRead(BS_NR_OF_STRINGS - 1u));
    TEST_ASSERT_FAIL_ASSERT(TI_RequestEepromRead(BS_NR_OF_STRINGS));
}

/** @brief   TI_RequestEepromWrite() rejects a string index outside the configured
 *         range (ti_dummy_afe.c:84) and otherwise forwards to the dummy driver
 *         (ti_dummy.c:87-89)
 */
void testTI_RequestEepromWrite(void) {
    TEST_ASSERT_EQUAL(STD_OK, TI_RequestEepromWrite(0u));
    TEST_ASSERT_EQUAL(STD_OK, TI_RequestEepromWrite(BS_NR_OF_STRINGS - 1u));
    TEST_ASSERT_FAIL_ASSERT(TI_RequestEepromWrite(BS_NR_OF_STRINGS));
}

/** @brief   TI_RequestTemperatureRead() rejects a string index outside the
 *         configured range (ti_dummy_afe.c:88) and otherwise forwards to the
 *         dummy driver (ti_dummy.c:91-93)
 */
void testTI_RequestTemperatureRead(void) {
    TEST_ASSERT_EQUAL(STD_OK, TI_RequestTemperatureRead(0u));
    TEST_ASSERT_EQUAL(STD_OK, TI_RequestTemperatureRead(BS_NR_OF_STRINGS - 1u));
    TEST_ASSERT_FAIL_ASSERT(TI_RequestTemperatureRead(BS_NR_OF_STRINGS));
}

/** @brief   TI_RequestBalancingFeedbackRead() rejects a string index outside the
 *         configured range (ti_dummy_afe.c:92) and otherwise forwards to the
 *         dummy driver (ti_dummy.c:95-97)
 */
void testTI_RequestBalancingFeedbackRead(void) {
    TEST_ASSERT_EQUAL(STD_OK, TI_RequestBalancingFeedbackRead(0u));
    TEST_ASSERT_EQUAL(STD_OK, TI_RequestBalancingFeedbackRead(BS_NR_OF_STRINGS - 1u));
    TEST_ASSERT_FAIL_ASSERT(TI_RequestBalancingFeedbackRead(BS_NR_OF_STRINGS));
}

/** @brief   TI_RequestOpenWireCheck() rejects a string index outside the
 *         configured range (ti_dummy_afe.c:96) and otherwise forwards to the
 *         dummy driver (ti_dummy.c:99-101)
 */
void testTI_RequestOpenWireCheck(void) {
    TEST_ASSERT_EQUAL(STD_OK, TI_RequestOpenWireCheck(0u));
    TEST_ASSERT_EQUAL(STD_OK, TI_RequestOpenWireCheck(BS_NR_OF_STRINGS - 1u));
    TEST_ASSERT_FAIL_ASSERT(TI_RequestOpenWireCheck(BS_NR_OF_STRINGS));
}

/** @brief   TI_StartMeasurement() forwards to the dummy driver, which reports
 *         success (ti_dummy_afe.c:101-102 -> ti_dummy.c:103-104)
 */
void testTI_StartMeasurementReturnsOk(void) {
    TEST_ASSERT_EQUAL(STD_OK, TI_StartMeasurement());
}

/** @brief   TI_IsFirstMeasurementCycleFinished() forwards to the dummy driver,
 *         which reports the cycle as finished unconditionally
 *         (ti_dummy_afe.c:104-105 -> ti_dummy.c:106-107)
 */
void testTI_IsFirstMeasurementCycleFinishedIsAlwaysTrue(void) {
    TEST_ASSERT_TRUE(TI_IsFirstMeasurementCycleFinished());
}
