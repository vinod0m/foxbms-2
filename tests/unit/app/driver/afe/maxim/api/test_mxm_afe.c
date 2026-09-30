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
 * @file    test_mxm_afe.c
 * @author  foxBMS Team
 * @date    2020-06-17 (date of creation)
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
#include "Mockmxm_17841b.h"
#include "Mockmxm_1785x.h"
#include "Mockmxm_battery_management.h"
#include "Mockmxm_cfg.h"
#include "Mockos.h"

#include "afe.h"

/* mxm_afe.c takes BS_NR_OF_STRINGS from the battery system configuration
 * (src/app/driver/afe/maxim/api/mxm_afe.c:232); the same header is included here
 * so the bound these tests reject is the bound the product asserts against. */
#include "battery_system_cfg.h"

#include "test_assert_helper.h"

/*========== Unit Testing Framework Directives ==============================*/
TEST_SOURCE_FILE("mxm_afe.c")

TEST_INCLUDE_PATH("../../src/app/driver/afe/api")
TEST_INCLUDE_PATH("../../src/app/driver/afe/maxim/common")
TEST_INCLUDE_PATH("../../src/app/driver/afe/maxim/common/config")
TEST_INCLUDE_PATH("../../src/app/driver/config")
TEST_INCLUDE_PATH("../../src/app/driver/spi")

/*========== Definitions and Implementations for Unit Test ==================*/

/*========== Setup and Teardown =============================================*/
/* MXM_Tick() calls five driver entry points in a fixed order and in between one
 * of them twice (src/app/driver/afe/maxim/api/mxm_afe.c:154-163). mxm_state and
 * the two Maxim instances are module-private statics of mxm_afe.c, so the test
 * cannot address them and uses stubs whose callbacks pin the ORDER and the CALL
 * COUNT with Unity instead. */
static uint8_t test_tickStep;

static void MXM_CheckIfErrorCounterCanBeResetCallback(MXM_MONITORING_INSTANCE_s *pInstance, int n) {
    (void)pInstance;
    (void)n;
    TEST_ASSERT_EQUAL_UINT8(0u, test_tickStep);
    test_tickStep++;
}
static void MXM_StateMachineCallback(MXM_MONITORING_INSTANCE_s *pInstance, int n) {
    (void)pInstance;
    (void)n;
    TEST_ASSERT_EQUAL_UINT8(1u, test_tickStep);
    test_tickStep++;
}
static void MXM_5XStateMachineCallback(MXM_41B_INSTANCE_s *pInstance41b, MXM_5X_INSTANCE_s *pInstance5x, int n) {
    (void)pInstance41b;
    (void)pInstance5x;
    (void)n;
    /* the 5x machine runs first (mxm_afe.c:158) and again after the 41B pass
     * (mxm_afe.c:163) */
    const uint8_t expectedStep = (test_tickStep == 2u) ? 2u : 4u;
    TEST_ASSERT_EQUAL_UINT8(expectedStep, test_tickStep);
    test_tickStep++;
}
static void MXM_41BStateMachineCallback(MXM_41B_INSTANCE_s *pInstance, int n) {
    (void)pInstance;
    (void)n;
    TEST_ASSERT_EQUAL_UINT8(3u, test_tickStep);
    test_tickStep++;
}

void setUp(void) {
    test_tickStep = 0u;
}

void tearDown(void) {
}

/*========== Test Cases =====================================================*/
/* mxm_afe.c is the AFE API wrapper over the Maxim driver. Four of the AFE_Request*
 * entry points exist only to reject a string index and report that the request
 * is not available; the fifth records the open-wire request. All five guard the
 * string index with FAS_ASSERT(string < BS_NR_OF_STRINGS) - mxm_afe.c:232, :237,
 * :242, :247, :252 - and only the open-wire one reports success (:253-258). */

/** @brief   AFE_RequestTemperatureRead() reports "not ok" and rejects an index
 *         outside the configured range (mxm_afe.c:231-234)
 */
void testAFE_RequestTemperatureRead(void) {
    TEST_ASSERT_EQUAL(STD_NOT_OK, AFE_RequestTemperatureRead(0u));
    TEST_ASSERT_EQUAL(STD_NOT_OK, AFE_RequestTemperatureRead(BS_NR_OF_STRINGS - 1u));
    TEST_ASSERT_FAIL_ASSERT(AFE_RequestTemperatureRead(BS_NR_OF_STRINGS));
}

/** @brief   AFE_RequestBalancingFeedbackRead() reports "not ok" and guards the
 *         string index (mxm_afe.c:236-239)
 */
void testAFE_RequestBalancingFeedbackRead(void) {
    TEST_ASSERT_EQUAL(STD_NOT_OK, AFE_RequestBalancingFeedbackRead(0u));
    TEST_ASSERT_FAIL_ASSERT(AFE_RequestBalancingFeedbackRead(BS_NR_OF_STRINGS));
}

/** @brief   AFE_RequestEepromRead() reports "not ok" and guards the string index
 *         (mxm_afe.c:241-244)
 */
void testAFE_RequestEepromRead(void) {
    TEST_ASSERT_EQUAL(STD_NOT_OK, AFE_RequestEepromRead(0u));
    TEST_ASSERT_FAIL_ASSERT(AFE_RequestEepromRead(BS_NR_OF_STRINGS));
}

/** @brief   AFE_RequestEepromWrite() reports "not ok" and guards the string index
 *         (mxm_afe.c:246-249)
 */
void testAFE_RequestEepromWrite(void) {
    TEST_ASSERT_EQUAL(STD_NOT_OK, AFE_RequestEepromWrite(0u));
    TEST_ASSERT_FAIL_ASSERT(AFE_RequestEepromWrite(BS_NR_OF_STRINGS));
}

/** @brief   AFE_RequestOpenWireCheck() is the one request the driver accepts: it
 *         reports success inside a task-critical section (mxm_afe.c:251-259)
 */
void testAFE_RequestOpenWireCheck(void) {
    TEST_ASSERT_FAIL_ASSERT(AFE_RequestOpenWireCheck(BS_NR_OF_STRINGS));
    /* the accepted path raises no task-critical section, it only sets the flag */
    TEST_ASSERT_EQUAL(STD_OK, AFE_RequestOpenWireCheck(0u));
    TEST_ASSERT_EQUAL(STD_OK, AFE_RequestOpenWireCheck(BS_NR_OF_STRINGS - 1u));
}

/** @brief   AFE_StartMeasurement() raises allowStartup and operationRequested
 *         inside a task-critical section and reports success (mxm_afe.c:213-222)
 */
void testAFE_StartMeasurement(void) {
    OS_EnterTaskCritical_Expect();
    OS_ExitTaskCritical_Expect();
    TEST_ASSERT_EQUAL(STD_OK, AFE_StartMeasurement());
}

/** @brief   AFE_IsFirstMeasurementCycleFinished() reads the flag inside a
 *         task-critical section (mxm_afe.c:224-229); the driver state starts out
 *         zero-initialised, so no measurement cycle has been made yet
 */
void testAFE_IsFirstMeasurementCycleFinished(void) {
    OS_EnterTaskCritical_Expect();
    OS_ExitTaskCritical_Expect();
    TEST_ASSERT_FALSE(AFE_IsFirstMeasurementCycleFinished());
}

/** @brief   AFE_TriggerIc() advances the driver state exactly once and reports
 *         success while no reset is pending (mxm_afe.c:180-202)
 * @details MXM_Tick() (mxm_afe.c:154-171) resets the error counter, advances the
 *          Maxim state machine, and runs the 5x state machine twice with one
 *          41B pass in between. The state-machine state is zero-initialised, i.e.
 *          MXM_STATEMACHINE_STATES_UNINITIALIZED (mxm_1785x_tools.h:80), which is
 *          why the "stuck in init" branch at mxm_afe.c:165-169 is not taken.
 */
void testAFE_TriggerIcRunsOneTick(void) {
    MXM_CheckIfErrorCounterCanBeReset_Stub(MXM_CheckIfErrorCounterCanBeResetCallback);
    MXM_StateMachine_Stub(MXM_StateMachineCallback);
    MXM_5XStateMachine_Stub(MXM_5XStateMachineCallback);
    MXM_41BStateMachine_Stub(MXM_41BStateMachineCallback);
    TEST_ASSERT_EQUAL(STD_OK, AFE_TriggerIc());
    /* exactly the five calls of MXM_Tick() (mxm_afe.c:155-163) */
    TEST_ASSERT_EQUAL_UINT8(5u, test_tickStep);
}
