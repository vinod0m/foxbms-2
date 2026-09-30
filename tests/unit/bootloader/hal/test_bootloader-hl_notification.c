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
 * @file    test_bootloader-hl_notification.c
 * @author  foxBMS Team
 * @date    2025-08-05 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   TODO
 * @details TODO
 */

/*========== Includes =======================================================*/

#include "unity.h"

/* clang-format off */
#include "HL_esm.h"
#include "HL_can.h"
#include "HL_gio.h"
#include "HL_rti.h"
#include "HL_crc.h"
#include "HL_epc.h"
#include "HL_sys_dma.h"
#include "HL_hal_stdtypes.h"
/* clang-format on */

#include "Mockinfinite-loop-helper.h"

/*========== Unit Testing Framework Directives ==============================*/
TEST_SOURCE_FILE("bootloader-hl_notification.c")

/*========== Definitions and Implementations for Unit Test ==================*/

/*========== Setup and Teardown =============================================*/
/* 9 of the 10 notification entry points of
 * src/bootloader/hal/bootloader-hl_notification.c have an empty body (:84-111);
 * only esmGroup3Notification() blocks, in `while (FOREVER())` (:88-91). The
 * unused notifications are therefore required to be INERT: if one of them ever
 * entered the trap loop, or gained any other observable effect, FOREVER() would
 * be called. The FOREVER() call count is the observable that distinguishes them.
 *
 * CMock's own FOREVER_CallCount() counts only calls routed through a callback,
 * not calls served from an _Expect registration, so the count is taken here.
 * The stub answers false once its script is exhausted, so an accidental call
 * inside a notification that was supposed to be inert ends any loop instead of
 * hanging the suite, and still shows up in the count.
 */
#define TEST_N_FOREVER_SCRIPT (8u)

static uint8_t test_foreverCalls;
static bool    test_foreverReturns[TEST_N_FOREVER_SCRIPT];
static uint8_t test_foreverReturnsLen;

static bool FOREVERCallback(int cmock_num_calls) {
    (void)cmock_num_calls;
    test_foreverCalls++;
    if (test_foreverCalls > test_foreverReturnsLen) {
        return false;
    }
    return test_foreverReturns[test_foreverCalls - 1u];
}

#define TEST_ASSERT_NOTIFICATION_INERT() TEST_ASSERT_EQUAL_UINT32(0u, test_foreverCalls)

void setUp(void) {
    test_foreverCalls      = 0u;
    test_foreverReturnsLen = 0u;
    FOREVER_Stub(FOREVERCallback);
}

void tearDown(void) {
}

/*========== Test Cases =====================================================*/
void testesmGroup1Notification(void) {
    esmGroup1Notification(NULL_PTR, 0u); /* arguments do not matter as unused */
    TEST_ASSERT_NOTIFICATION_INERT();
}

void testesmGroup2Notification(void) {
    esmGroup2Notification(NULL_PTR, 0u); /* arguments do not matter as unused */
    TEST_ASSERT_NOTIFICATION_INERT();
}

void testesmGroup3Notification(void) {
    /* a FOREVER() that answers false immediately ends the trap loop at once, so
     * esmGroup3Notification() asks exactly once (module :89-90) */
    test_foreverReturns[0] = false;
    test_foreverReturnsLen = 1u;
    test_foreverCalls      = 0u;
    esmGroup3Notification(NULL_PTR, 0u);
    TEST_ASSERT_EQUAL_UINT32(1u, test_foreverCalls);

    /* a FOREVER() that answers true once keeps the loop alive for one more
     * iteration, so two calls are needed to get out of it */
    test_foreverReturns[0] = true;
    test_foreverReturns[1] = false;
    test_foreverReturnsLen = 2u;
    test_foreverCalls      = 0u;
    esmGroup3Notification(NULL_PTR, 0u);
    TEST_ASSERT_EQUAL_UINT32(2u, test_foreverCalls);

    /* three true answers before the loop is left, so four calls in total */
    test_foreverReturns[0] = true;
    test_foreverReturns[1] = true;
    test_foreverReturns[2] = true;
    test_foreverReturns[3] = false;
    test_foreverReturnsLen = 4u;
    test_foreverCalls      = 0u;
    esmGroup3Notification(NULL_PTR, 0u);
    TEST_ASSERT_EQUAL_UINT32(4u, test_foreverCalls);
}

void testdmaGroupANotification(void) {
    dmaGroupANotification((dmaInterrupt_t)0, 0u); /* arguments do not matter as unused */
    TEST_ASSERT_NOTIFICATION_INERT();
}

void testrtiNotification(void) {
    rtiNotification(NULL_PTR, 0u); /* arguments do not matter as unused */
    TEST_ASSERT_NOTIFICATION_INERT();
}

void testcanErrorNotification(void) {
    canErrorNotification(NULL_PTR, 0u); /* arguments do not matter as unused */
    TEST_ASSERT_NOTIFICATION_INERT();
}

void testcanStatusChangeNotification(void) {
    canStatusChangeNotification(NULL_PTR, 0u); /* arguments do not matter as unused */
    TEST_ASSERT_NOTIFICATION_INERT();
}

void testgioNotification(void) {
    gioNotification(NULL_PTR, 0u); /* arguments do not matter as unused */
    TEST_ASSERT_NOTIFICATION_INERT();
}

void testepcCAMFullNotification(void) {
    epcCAMFullNotification(); /* arguments do not matter as unused */
    TEST_ASSERT_NOTIFICATION_INERT();
}

void testepcFIFOFullNotification(void) {
    epcFIFOFullNotification(0u); /* arguments do not matter as unused */
    TEST_ASSERT_NOTIFICATION_INERT();
}
