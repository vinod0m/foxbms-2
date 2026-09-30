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
 * @file    test_sys_cfg.c
 * @author  foxBMS Team
 * @date    2020-04-02 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Tests for the sys_cfg
 * @details Tests sending a sys boot message
 *
 */

/*========== Includes =======================================================*/
#include "unity.h"
#include "Mockcan_cbs_tx_f_debug-response.h"
#include "Mockcan_cfg.h"

#include "sys_cfg.h"

#include "test_assert_helper.h"

/*========== Unit Testing Framework Directives ==============================*/
TEST_INCLUDE_PATH("../../src/app/driver/can/cbs/tx-async")
TEST_INCLUDE_PATH("../../src/app/driver/config")
TEST_INCLUDE_PATH("../../tests/unit/support")

/*========== Definitions and Implementations for Unit Test ==================*/

/*========== Setup and Teardown =============================================*/
void setUp(void) {
}

void tearDown(void) {
}

/*========== Test Cases =====================================================*/
void testSysSendBootMessage(void) {
    /* all debug responses are ok */
    CANTX_DebugResponse_ExpectAndReturn(CANTX_DEBUG_RESPONSE_TRANSMIT_BOOT_MAGIC_START, STD_OK);
    CANTX_DebugResponse_ExpectAndReturn(CANTX_DEBUG_RESPONSE_TRANSMIT_BMS_VERSION_INFO, STD_OK);
    CANTX_DebugResponse_ExpectAndReturn(CANTX_DEBUG_RESPONSE_TRANSMIT_COMMIT_HASH, STD_OK);
    CANTX_DebugResponse_ExpectAndReturn(CANTX_DEBUG_RESPONSE_TRANSMIT_MCU_UNIQUE_DIE_ID, STD_OK);
    CANTX_DebugResponse_ExpectAndReturn(CANTX_DEBUG_RESPONSE_TRANSMIT_MCU_LOT_NUMBER, STD_OK);
    CANTX_DebugResponse_ExpectAndReturn(CANTX_DEBUG_RESPONSE_TRANSMIT_MCU_WAFER_INFORMATION, STD_OK);
    CANTX_DebugResponse_ExpectAndReturn(CANTX_DEBUG_RESPONSE_TRANSMIT_BOOT_TIMESTAMP, STD_OK);
    CANTX_DebugResponse_ExpectAndReturn(CANTX_DEBUG_RESPONSE_TRANSMIT_BOOT_MAGIC_END, STD_OK);
    SYS_SendBootMessage();

    /* all debug responses are not ok and trigger trap */
    CANTX_DebugResponse_ExpectAndReturn(CANTX_DEBUG_RESPONSE_TRANSMIT_BOOT_MAGIC_START, STD_NOT_OK);
    CANTX_DebugResponse_ExpectAndReturn(CANTX_DEBUG_RESPONSE_TRANSMIT_BMS_VERSION_INFO, STD_NOT_OK);
    CANTX_DebugResponse_ExpectAndReturn(CANTX_DEBUG_RESPONSE_TRANSMIT_COMMIT_HASH, STD_NOT_OK);
    CANTX_DebugResponse_ExpectAndReturn(CANTX_DEBUG_RESPONSE_TRANSMIT_MCU_UNIQUE_DIE_ID, STD_NOT_OK);
    CANTX_DebugResponse_ExpectAndReturn(CANTX_DEBUG_RESPONSE_TRANSMIT_MCU_LOT_NUMBER, STD_NOT_OK);
    CANTX_DebugResponse_ExpectAndReturn(CANTX_DEBUG_RESPONSE_TRANSMIT_MCU_WAFER_INFORMATION, STD_NOT_OK);
    CANTX_DebugResponse_ExpectAndReturn(CANTX_DEBUG_RESPONSE_TRANSMIT_BOOT_TIMESTAMP, STD_NOT_OK);
     CANTX_DebugResponse_ExpectAndReturn(CANTX_DEBUG_RESPONSE_TRANSMIT_BOOT_MAGIC_END, STD_NOT_OK);
    SYS_SendBootMessage();
}

/* Number of CANTX_DebugResponse() requests SYS_SendBootMessage() makes, and the
 * response each one must be for, in the order src/app/engine/config/sys_cfg.c
 * asks for them. A CMock `_Stub` returns from the callback branch of the
 * generated mock before CMock's own argument, call-count and ordering checks,
 * so all three are put back here: the response identity is asserted inside the
 * callback, and the number of responses consumed is asserted with Unity after
 * the call. */
#define TEST_SYS_N_BOOT_RESPONSES (8u)

static uint8_t test_sysCalls;

static CANTX_DEBUG_RESPONSE_ACTIONS_e test_sysExpected[TEST_SYS_N_BOOT_RESPONSES] = {
    CANTX_DEBUG_RESPONSE_TRANSMIT_BOOT_MAGIC_START,
    CANTX_DEBUG_RESPONSE_TRANSMIT_BMS_VERSION_INFO,
    CANTX_DEBUG_RESPONSE_TRANSMIT_COMMIT_HASH,
    CANTX_DEBUG_RESPONSE_TRANSMIT_MCU_UNIQUE_DIE_ID,
    CANTX_DEBUG_RESPONSE_TRANSMIT_MCU_LOT_NUMBER,
    CANTX_DEBUG_RESPONSE_TRANSMIT_MCU_WAFER_INFORMATION,
    CANTX_DEBUG_RESPONSE_TRANSMIT_BOOT_TIMESTAMP,
    CANTX_DEBUG_RESPONSE_TRANSMIT_BOOT_MAGIC_END,
};

/** @brief   answers the first rejected response with STD_NOT_OK and the rest
 *          with STD_OK, so SYS_SendBootMessage() traps at position @p rejectedAt
 */
static STD_RETURN_TYPE_e CANTX_DebugResponseBootSequenceCallback(
    CANTX_DEBUG_RESPONSE_ACTIONS_e action,
    uint8_t rejectedAt,
    int cmock_num_calls) {
    (void)cmock_num_calls;
    TEST_ASSERT_LESS_THAN_UINT8(TEST_SYS_N_BOOT_RESPONSES, test_sysCalls);
    TEST_ASSERT_EQUAL(test_sysExpected[test_sysCalls], action);
    const STD_RETURN_TYPE_e retval =
        (test_sysCalls == rejectedAt) ? STD_NOT_OK : STD_OK;
    test_sysCalls++;
    return retval;
}

static STD_RETURN_TYPE_e CANTX_DebugResponseCallback0(CANTX_DEBUG_RESPONSE_ACTIONS_e action, int n) {
    return CANTX_DebugResponseBootSequenceCallback(action, 0u, n);
}
static STD_RETURN_TYPE_e CANTX_DebugResponseCallback1(CANTX_DEBUG_RESPONSE_ACTIONS_e action, int n) {
    return CANTX_DebugResponseBootSequenceCallback(action, 1u, n);
}
static STD_RETURN_TYPE_e CANTX_DebugResponseCallback2(CANTX_DEBUG_RESPONSE_ACTIONS_e action, int n) {
    return CANTX_DebugResponseBootSequenceCallback(action, 2u, n);
}
static STD_RETURN_TYPE_e CANTX_DebugResponseCallback3(CANTX_DEBUG_RESPONSE_ACTIONS_e action, int n) {
    return CANTX_DebugResponseBootSequenceCallback(action, 3u, n);
}
static STD_RETURN_TYPE_e CANTX_DebugResponseCallback4(CANTX_DEBUG_RESPONSE_ACTIONS_e action, int n) {
    return CANTX_DebugResponseBootSequenceCallback(action, 4u, n);
}
static STD_RETURN_TYPE_e CANTX_DebugResponseCallback5(CANTX_DEBUG_RESPONSE_ACTIONS_e action, int n) {
    return CANTX_DebugResponseBootSequenceCallback(action, 5u, n);
}
static STD_RETURN_TYPE_e CANTX_DebugResponseCallback6(CANTX_DEBUG_RESPONSE_ACTIONS_e action, int n) {
    return CANTX_DebugResponseBootSequenceCallback(action, 6u, n);
}
static STD_RETURN_TYPE_e CANTX_DebugResponseCallback7(CANTX_DEBUG_RESPONSE_ACTIONS_e action, int n) {
    return CANTX_DebugResponseBootSequenceCallback(action, 7u, n);
}

/** @brief   rejects the boot magic start (src/app/engine/config/sys_cfg.c:86-87)
 * @details SYS_SendBootMessage() guards each of its eight debug responses with
 *          `if (CANTX_DebugResponse(x) != STD_OK) { FAS_ASSERT(FAS_TRAP); }`
 *          (sys_cfg.c:86-108). This test rejects the FIRST response and requires
 *          that the call traps there and that no second response is requested.
 */
void testSysSendBootMessageRejectsFirstResponse(void) {
    test_sysCalls = 0u;
    CANTX_DebugResponse_Stub(CANTX_DebugResponseCallback0);
    TEST_ASSERT_FAIL_ASSERT(SYS_SendBootMessage());
    TEST_ASSERT_EQUAL_UINT8(1u, test_sysCalls);
}

/** @brief   rejects the BMS version info (sys_cfg.c:89-90) */
void testSysSendBootMessageRejectsSecondResponse(void) {
    test_sysCalls = 0u;
    CANTX_DebugResponse_Stub(CANTX_DebugResponseCallback1);
    TEST_ASSERT_FAIL_ASSERT(SYS_SendBootMessage());
    TEST_ASSERT_EQUAL_UINT8(2u, test_sysCalls);
}

/** @brief   rejects the commit hash (sys_cfg.c:92-93) */
void testSysSendBootMessageRejectsThirdResponse(void) {
    test_sysCalls = 0u;
    CANTX_DebugResponse_Stub(CANTX_DebugResponseCallback2);
    TEST_ASSERT_FAIL_ASSERT(SYS_SendBootMessage());
    TEST_ASSERT_EQUAL_UINT8(3u, test_sysCalls);
}

/** @brief   rejects the MCU die id (sys_cfg.c:95-96) */
void testSysSendBootMessageRejectsFourthResponse(void) {
    test_sysCalls = 0u;
    CANTX_DebugResponse_Stub(CANTX_DebugResponseCallback3);
    TEST_ASSERT_FAIL_ASSERT(SYS_SendBootMessage());
    TEST_ASSERT_EQUAL_UINT8(4u, test_sysCalls);
}

/** @brief   rejects the MCU lot number (sys_cfg.c:98-99) */
void testSysSendBootMessageRejectsFifthResponse(void) {
    test_sysCalls = 0u;
    CANTX_DebugResponse_Stub(CANTX_DebugResponseCallback4);
    TEST_ASSERT_FAIL_ASSERT(SYS_SendBootMessage());
    TEST_ASSERT_EQUAL_UINT8(5u, test_sysCalls);
}

/** @brief   rejects the MCU wafer information (sys_cfg.c:101-102) */
void testSysSendBootMessageRejectsSixthResponse(void) {
    test_sysCalls = 0u;
    CANTX_DebugResponse_Stub(CANTX_DebugResponseCallback5);
    TEST_ASSERT_FAIL_ASSERT(SYS_SendBootMessage());
    TEST_ASSERT_EQUAL_UINT8(6u, test_sysCalls);
}

/** @brief   rejects the boot timestamp (sys_cfg.c:104-105) */
void testSysSendBootMessageRejectsSeventhResponse(void) {
    test_sysCalls = 0u;
    CANTX_DebugResponse_Stub(CANTX_DebugResponseCallback6);
    TEST_ASSERT_FAIL_ASSERT(SYS_SendBootMessage());
    TEST_ASSERT_EQUAL_UINT8(7u, test_sysCalls);
}

/** @brief   rejects the magic boot end (sys_cfg.c:107-108) */
void testSysSendBootMessageRejectsEighthResponse(void) {
    test_sysCalls = 0u;
    CANTX_DebugResponse_Stub(CANTX_DebugResponseCallback7);
    TEST_ASSERT_FAIL_ASSERT(SYS_SendBootMessage());
    TEST_ASSERT_EQUAL_UINT8(8u, test_sysCalls);
}
