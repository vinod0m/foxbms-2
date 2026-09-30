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
 * @file    test_ti_dummy.c
 * @author  foxBMS Team
 * @date    2023-09-11 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Test of TI dummy AFE API implementation of the TI AFE API
 * @details TODO
 */

/*========== Includes =======================================================*/
#include "unity.h"

#include "ti_dummy.h"

#include "test_assert_helper.h"

#include <stdint.h>

/*========== Unit Testing Framework Directives ==============================*/
TEST_SOURCE_FILE("ti_dummy.c")

TEST_INCLUDE_PATH("../../src/app/driver/afe/api")
TEST_INCLUDE_PATH("../../src/app/driver/afe/ti/api")
TEST_INCLUDE_PATH("../../src/app/driver/afe/ti/dummy")
TEST_INCLUDE_PATH("../../tests/unit/support")

/*========== Definitions and Implementations for Unit Test ==================*/

/*========== Setup and Teardown =============================================*/
void setUp(void) {
}

void tearDown(void) {
}

/*========== Test Cases =====================================================*/
/* The TI dummy AFE is the no-hardware stand-in for a real TI AFE. Every entry
 * point answers STD_OK unconditionally and reports the first measurement cycle
 * as finished; that is the whole contract, so it is asserted here rather than
 * left to a test case that calls the functions and asserts nothing. */

/** @brief   TIDUM_Measure() reports success (ti_dummy.c:77-78) */
void testTIDUM_MeasureReturnsOk(void) {
    TEST_ASSERT_EQUAL(STD_OK, TIDUM_Measure());
}

/** @brief   TIDUM_Initialize() reports success (ti_dummy.c:80-81) */
void testTIDUM_InitializeReturnsOk(void) {
    TEST_ASSERT_EQUAL(STD_OK, TIDUM_Initialize());
}

/** @brief   TIDUM_RequestEepromRead() reports success for any string
 *         (ti_dummy.c:83-85)
 */
void testTIDUM_RequestEepromReadReturnsOk(void) {
    TEST_ASSERT_EQUAL(STD_OK, TIDUM_RequestEepromRead(0u));
    TEST_ASSERT_EQUAL(STD_OK, TIDUM_RequestEepromRead(UINT8_MAX));
}

/** @brief   TIDUM_RequestEepromWrite() reports success for any string
 *         (ti_dummy.c:87-89)
 */
void testTIDUM_RequestEepromWriteReturnsOk(void) {
    TEST_ASSERT_EQUAL(STD_OK, TIDUM_RequestEepromWrite(0u));
    TEST_ASSERT_EQUAL(STD_OK, TIDUM_RequestEepromWrite(UINT8_MAX));
}

/** @brief   TIDUM_RequestTemperatureRead() reports success for any string
 *         (ti_dummy.c:91-93)
 */
void testTIDUM_RequestTemperatureReadReturnsOk(void) {
    TEST_ASSERT_EQUAL(STD_OK, TIDUM_RequestTemperatureRead(0u));
    TEST_ASSERT_EQUAL(STD_OK, TIDUM_RequestTemperatureRead(UINT8_MAX));
}

/** @brief   TIDUM_RequestBalancingFeedbackRead() reports success for any string
 *         (ti_dummy.c:95-97)
 */
void testTIDUM_RequestBalancingFeedbackReadReturnsOk(void) {
    TEST_ASSERT_EQUAL(STD_OK, TIDUM_RequestBalancingFeedbackRead(0u));
    TEST_ASSERT_EQUAL(STD_OK, TIDUM_RequestBalancingFeedbackRead(UINT8_MAX));
}

/** @brief   TIDUM_RequestOpenWireCheck() reports success for any string
 *         (ti_dummy.c:99-101)
 */
void testTIDUM_RequestOpenWireCheckReturnsOk(void) {
    TEST_ASSERT_EQUAL(STD_OK, TIDUM_RequestOpenWireCheck(0u));
    TEST_ASSERT_EQUAL(STD_OK, TIDUM_RequestOpenWireCheck(UINT8_MAX));
}

/** @brief   TIDUM_StartMeasurement() reports success (ti_dummy.c:103-104) */
void testTIDUM_StartMeasurementReturnsOk(void) {
    TEST_ASSERT_EQUAL(STD_OK, TIDUM_StartMeasurement());
}

/** @brief   TIDUM_IsFirstMeasurementCycleFinished() is unconditionally true
 *         (ti_dummy.c:106-107)
 */
void testTIDUM_IsFirstMeasurementCycleFinishedIsAlwaysTrue(void) {
    TEST_ASSERT_TRUE(TIDUM_IsFirstMeasurementCycleFinished());
    TEST_ASSERT_TRUE(TIDUM_IsFirstMeasurementCycleFinished());
}
