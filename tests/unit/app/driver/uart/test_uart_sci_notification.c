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
 * @file    test_uart_sci_notification.c
 * @author  foxBMS Team
 * @date    2025-09-29 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Tests for the SCI module's 'sciNotification' implementation.
 * @details TODO
 *
 */

/*========== Includes =======================================================*/
#include "unity.h"
#include "MockHL_reg_sci.h"
#include "MockHL_sys_dma.h"
#include "Mockftask.h"
#include "Mockmpu_prototypes.h"
#include "Mockos.h"
#include "Mockportmacro.h"
/* Mockqueue.h is what supplies xQueueGenericCreateStatic, which UART_Initialize
 * (src/app/driver/uart/uart.c) calls via the xQueueCreateStatic macro
 * (src/os/freertos/freertos/include/queue.h:235). Without it the link fails
 * with one undefined symbol, _xQueueGenericCreateStatic. This is the same
 * arrangement test_can_2.c uses (its line 72 is #include "Mockqueue.h").
 *
 * It is included BEFORE the real queue.h below, which is the include order
 * test_can_2.c also uses, so the mock's declarations and the real header agree. */
#include "Mockqueue.h"

#include "uart_cfg.h"

#include "HL_sci.h"

#include "FreeRTOS.h"
#include "FreeRTOSIPConfig.h"
#include "queue.h"
#include "semphr.h"

#include "test_assert_helper.h"
#include "uart.h"

/*========== Unit Testing Framework Directives ==============================*/
TEST_SOURCE_FILE("uart.c")

TEST_INCLUDE_PATH("../../src/app/driver/uart")
TEST_INCLUDE_PATH("../../src/app/driver/config")
TEST_INCLUDE_PATH("../../src/app/driver/dma")
TEST_INCLUDE_PATH("../../src/app/driver/rtc")
TEST_INCLUDE_PATH("../../src/app/driver/spi")
TEST_INCLUDE_PATH("../../src/app/task/config")
TEST_INCLUDE_PATH("../../src/app/task/ftask")
TEST_INCLUDE_PATH("../../src/os/freertos/freertos-plus/freertos-plus-tcp/source/include")

/*========== Definitions and Implementations for Unit Test ==================*/

OS_QUEUE ftsk_uartRxQueue           = NULL_PTR;
volatile bool ftsk_allQueuesCreated = false; /* false so that UART_RxInterrupt quickly returns */

TaskHandle_t ftsk_taskHandleUart;

static uint8_t fsysRaisePrivilegeReturnValue = 0u;

long FSYS_RaisePrivilege(void) {
    return fsysRaisePrivilegeReturnValue;
}

/** Manually mocking functions from HL_sci.h */

void sciInit(void) {
}
/* Return type and width follow the interface declaration, not an earlier
 * spelling: sil/iface/HL_sci.h:86-87 declares
 *     bool sciSendByte(sciBASE_t *pSci, uint8_t byte);
 *     bool sciReceive(sciBASE_t *pSci, uint8_t length, uint8_t *pData);
 * The product's own call sites agree on the second parameter's width -
 * src/app/driver/uart/uart.c:163 and :279 pass a length of 1 - so the width is
 * uint8_t, not uint32_t. A `void` stub for a `bool` function is a conflicting
 * declaration, which is the build failure this file had.
 *
 * Both stubs report false: nothing was transferred, because these stubs only
 * exist so uart.c links, and sciNotification does not call them. */
bool sciSendByte(sciBASE_t *sci, uint8_t byte) {
    (void)sci;
    (void)byte;
    return false;
}
/* sciReceive is the point at which the hardware hands over the byte, so the
 * stub records where it was told to put it and writes the byte the test chose.
 * That is what lets a case seed uart_rxData, which is `static` in
 * src/app/driver/uart/uart.c:108 and has no setter: sciNotification passes
 * &uart_rxData to this function at uart.c:279, so writing through the pointer
 * the driver itself supplies is the only way in, and it is faithful - the real
 * HL_sci.h entry point fills the caller's buffer too. */
static uint8_t *sciStubRxDestination;
static uint8_t sciStubRxByte;
static uint32_t sciStubRxCallCount;
static sciBASE_t *sciStubRxInterface;
static uint8_t sciStubRxLength;

bool sciReceive(sciBASE_t *sci, uint8_t length, uint8_t *data) {
    sciStubRxCallCount++;
    sciStubRxInterface  = sci;
    sciStubRxLength     = length;
    sciStubRxDestination = data;
    if ((NULL_PTR != data) && (0u < (uint32_t)length)) {
        data[0] = sciStubRxByte;
    }
    return true;
}
void sciEnableNotification(sciBASE_t *sci, uint32 flags) {
}

static void SciStubReset(void) {
    sciStubRxCallCount   = 0u;
    sciStubRxInterface   = NULL_PTR;
    sciStubRxLength      = 0u;
    sciStubRxDestination = NULL_PTR;
    sciStubRxByte        = 0x00u;
}

/*========== Setup and Teardown =============================================*/
void setUp(void) {
    SciStubReset();
    /* start from the state uart.c:103 initialises it to: sending allowed */
    TEST_UART_SetSending(true);
}

void tearDown(void) {
}

/*========== Test Cases =====================================================*/

/*========== Test Cases =====================================================*/

/**
 * @brief   A byte delivered by one receive interrupt is acted on by the NEXT
 *          one, because the driver handles the interrupt before it fetches.
 * @details uart.c:277-279 is, in this order:
 *            :277      UART_RxInterrupt(sci);
 *            :279      sciReceive(sci, 1, &uart_rxData);
 *          UART_RxInterrupt reads uart_rxData at :247 and only afterwards does
 *          sciReceive refill that same variable. So the byte the hardware hands
 *          over during interrupt N is the byte interrupt N+1 dispatches on.
 *          There is exactly one byte of latency.
 *
 *          That ordering is a fact about the code and is what the three cases
 *          below are built around; each calls the ISR twice and says which call
 *          is expected to change the flag. Asserting it after only ONE call
 *          would have been wrong, and was: the first version of these cases did
 *          that and failed, which is how the ordering was established.
 */
/* cspell:disable-next-line */
void testSciNotificationActsOnTheByteFromThePreviousInterrupt(void) {
    TEST_UART_SetSending(true);
    sciStubRxByte = 0x13u; /* XOFF */

    /* ======= RT1/1: call 1 - delivers the byte, dispatches on the old one == */
    sciNotification(UART_REG, (uint32)SCI_RX_INT);
    /* nothing has been dispatched yet: the flag is unchanged after call 1 */
    TEST_ASSERT_TRUE(TEST_UART_GetSending());
    TEST_ASSERT_EQUAL_UINT32(1u, sciStubRxCallCount);
    TEST_ASSERT_EQUAL_UINT8(0x13u, sciStubRxDestination[0]);

    /* ======= RT1/1: call 2 - now dispatches on the byte call 1 delivered == */
    sciNotification(UART_REG, (uint32)SCI_RX_INT);
    /* uart.c:248 fires on this call, because uart_rxData now holds 0x13 */
    TEST_ASSERT_FALSE(TEST_UART_GetSending());
    TEST_ASSERT_EQUAL_UINT32(2u, sciStubRxCallCount);
}

/**
 * @brief   A receive interrupt on the configured interface stops sending, when
 *          the byte delivered was XOFF.
 * @details The whole chain, from src/app/driver/uart/uart.c:
 *            :269  extern void sciNotification(sciBASE_t *sci, uint32 flags) {
 *            :275      if ((sci == UART_REG) && (flags == (uint32)SCI_RX_INT)) {
 *            :277          UART_RxInterrupt(sci);
 *            :279          sciReceive(sci, 1, &uart_rxData);
 *            :280      }
 *            and UART_RxInterrupt at :244-262:
 *            :245      FAS_ASSERT(pSciInterface == UART_REG);
 *            :247      if (uart_rxData == UART_XOFF) {
 *            :248          uart_softwareFlowControlSending = false;
 *            UART_REG is (sciREG4) at src/app/driver/config/uart_cfg.h:67 and
 *            UART_XOFF is (0x13u) at src/app/driver/uart/uart.h:68.
 *
 *            The byte is placed by the sciReceive stub above, through the very
 *            pointer uart.c:279 hands it, because uart_rxData is static
 *            (uart.c:108) and has no setter. The assertion is on
 *            uart_softwareFlowControlSending, which the module externalises for
 *            tests at uart.c:333 as TEST_UART_GetSending.
 *
 *            SCI_RX_INT is deliberately NOT asserted as a literal: its value in
 *            this build comes from sil/iface/HL_reg_sci.h:40, whose own comment
 *            says the numeric selectors are "not verified against the device".
 *            The macro is used for the call and the flag VALUE the driver checks
 *            is asserted to be the macro, so a divergence between the two is
 *            still caught.
 */
/* cspell:disable-next-line */
void testSciNotificationXoffStopsSending(void) {
    /* deliver an XOFF byte through the stub */
    sciStubRxByte = 0x13u;
    TEST_ASSERT_TRUE(TEST_UART_GetSending());

    /* ======= RT1/1: call function under test =============================
     * Two calls, because uart.c:277 dispatches on the byte uart.c:279 fetched
     * on the PREVIOUS call - see
     * testSciNotificationActsOnTheByteFromThePreviousInterrupt. */
    sciNotification(UART_REG, (uint32)SCI_RX_INT);
    sciNotification(UART_REG, (uint32)SCI_RX_INT);

    /* ======= RT1/1: test output verification ============================= */
    /* uart.c:248 */
    TEST_ASSERT_FALSE(TEST_UART_GetSending());
    /* the driver asked for exactly one byte, into its own buffer */
    TEST_ASSERT_EQUAL_UINT32(2u, sciStubRxCallCount);
    TEST_ASSERT_EQUAL_UINT8(1u, sciStubRxLength);
    TEST_ASSERT_EQUAL_PTR(UART_REG, sciStubRxInterface);
    /* and the byte really did land where the driver will read it back */
    TEST_ASSERT_NOT_NULL(sciStubRxDestination);
    TEST_ASSERT_EQUAL_UINT8(0x13u, sciStubRxDestination[0]);
}

/**
 * @brief   The same interrupt resumes sending when the byte delivered was XON.
 * @details uart.c:249-250, the second arm of the same chain. Asserting both
 *          directions matters because a defect that simply cleared the flag
 *          would satisfy the XOFF case and fail this one.
 */
/* cspell:disable-next-line */
void testSciNotificationXonResumesSending(void) {
    /* start from stopped, so the XON case has to move it */
    TEST_UART_SetSending(false);
    sciStubRxByte = 0x11u; /* UART_XON, uart.h:69 */

    /* ======= RT1/1: call function under test =============================
     * Two calls: uart.c:250 dispatches on the byte fetched by the first. */
    sciNotification(UART_REG, (uint32)SCI_RX_INT);
    sciNotification(UART_REG, (uint32)SCI_RX_INT);

    /* ======= RT1/1: test output verification ============================= */
    /* uart.c:250 */
    TEST_ASSERT_TRUE(TEST_UART_GetSending());
    TEST_ASSERT_EQUAL_UINT32(2u, sciStubRxCallCount);
    TEST_ASSERT_EQUAL_UINT8(0x11u, sciStubRxDestination[0]);
}

/**
 * @brief   An ordinary data byte does not touch the flow-control flag.
 * @details uart.c:247-250 match only UART_XOFF and UART_XON; any other value
 *          falls through to the queue branch at :251. With
 *          ftsk_allQueuesCreated false the else arm at :259 does nothing, so
 *          the flag must be exactly what it was. 0x41u is 'A', which is neither
 *          0x13u nor 0x11u.
 */
/* cspell:disable-next-line */
void testSciNotificationDataByteLeavesFlowControlAlone(void) {
    TEST_UART_SetSending(true);
    sciStubRxByte = 0x41u;

    /* ======= RT1/1: call function under test =============================
     * Two calls, so the second one dispatches on the 'A' the first fetched. */
    sciNotification(UART_REG, (uint32)SCI_RX_INT);
    sciNotification(UART_REG, (uint32)SCI_RX_INT);

    /* ======= RT1/1: test output verification ============================= */
    TEST_ASSERT_TRUE(TEST_UART_GetSending());
    /* the byte was still fetched - only the flow-control flag is conditional */
    TEST_ASSERT_EQUAL_UINT32(2u, sciStubRxCallCount);
    TEST_ASSERT_EQUAL_UINT8(0x41u, sciStubRxDestination[0]);
}

/**
 * @brief   An interrupt from an interface other than UART_REG does nothing.
 * @details uart.c:275 tests `sci == UART_REG` first, and the whole body is
 *          inside that test. So a notification carrying any other handle must
 *          not reach sciReceive and must not change the flow-control flag. The
 *          handle used here is NULL_PTR, which is what the module's own callers
 *          can produce when no node is attached.
 */
/* cspell:disable-next-line */
void testSciNotificationIgnoresAnInterfaceOtherThanUartReg(void) {
    TEST_UART_SetSending(true);
    sciStubRxByte = 0x13u; /* would stop sending IF the handle were accepted */

    /* ======= RT1/1: call function under test ============================= */
    sciNotification(NULL_PTR, (uint32)SCI_RX_INT);

    /* ======= RT1/1: test output verification ============================= */
    /* no sciReceive: this is the observable proof the guard rejected the call */
    TEST_ASSERT_EQUAL_UINT32(0u, sciStubRxCallCount);
    TEST_ASSERT_NULL(sciStubRxDestination);
    /* and therefore no XOFF was seen */
    TEST_ASSERT_TRUE(TEST_UART_GetSending());
}

/**
 * @brief   An interrupt that is not the receive interrupt does nothing.
 * @details uart.c:275 also requires `flags == (uint32)SCI_RX_INT`. A different
 *          flag must be rejected the same way. The value used is the one the
 *          module's sibling test uses for a non-receive line, and it is
 *          deliberately NOT the receive value; the assertion is that nothing
 *          happened, so the exact number is not load-bearing.
 */
/* cspell:disable-next-line */
void testSciNotificationIgnoresANonReceiveInterrupt(void) {
    TEST_UART_SetSending(true);
    sciStubRxByte = 0x13u;

    /* ======= RT1/1: call function under test ============================= */
    sciNotification(UART_REG, (uint32)(SCI_RX_INT + 1u));

    /* ======= RT1/1: test output verification ============================= */
    TEST_ASSERT_EQUAL_UINT32(0u, sciStubRxCallCount);
    TEST_ASSERT_NULL(sciStubRxDestination);
    TEST_ASSERT_TRUE(TEST_UART_GetSending());
}

/**
 * @brief   The flag the driver compares against is the one the interface
 *          declares, cast to the width the comparison uses.
 * @details uart.c:275 compares `(uint32)SCI_RX_INT`, i.e. the value widened to
 *          uint32. If the build's SCI_RX_INT did not survive that cast, every
 *          case above would silently stop exercising the body. Asserting the
 *          widening here makes that precondition visible instead of implicit.
 */
/* cspell:disable-next-line */
void testSciNotificationUsesTheDeclaredReceiveFlag(void) {
    /* the driver narrows nothing and widens to uint32 at uart.c:275 */
    TEST_ASSERT_EQUAL_UINT32((uint32)SCI_RX_INT, (uint32)((sciField_t)SCI_RX_INT));
    /* and the value used in the negative cases really is different */
    TEST_ASSERT_NOT_EQUAL((uint32)SCI_RX_INT, (uint32)(SCI_RX_INT + 1u));
}
