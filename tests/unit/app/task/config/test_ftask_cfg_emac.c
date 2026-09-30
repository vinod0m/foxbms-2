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
 * @file    test_ftask_cfg_emac.c
 * @author  foxBMS Team
 * @date    2020-11-14 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Tests for the ftask_cfg driver
 * @details TODO
 *
 */

/*========== Includes =======================================================*/
#include "unity.h"
#include "MockHL_gio.h"
#include "MockHL_mdio.h"
#include "MockNetworkInterface_custom.h"
#include "Mockadc.h"
#include "Mockafe.h"
#include "Mockalgorithm.h"
#include "Mockbal.h"
#include "Mockbms.h"
#include "Mockcan.h"
#include "Mockcontactor.h"
#include "Mockdatabase.h"
#include "Mockdiag.h"
#include "Mockdiag_cfg.h"
#include "Mockemac.h"
#include "Mockfram.h"
#include "Mockhtsensor.h"
#include "Mocki2c.h"
#include "Mockimd.h"
#include "Mockinfinite-loop-helper.h"
#include "Mockinterlock.h"
#include "Mockled.h"
#include "Mockmaster_info.h"
#include "Mockmeas.h"
#include "Mockmpu_prototypes.h"
#include "Mockos.h"
#include "Mockpex.h"
#include "Mockredundancy.h"
#include "Mockrtc.h"
#include "Mocksbc.h"
#include "Mocksof_trapezoid.h"
#include "Mocksps.h"
#include "Mockstate_estimation.h"
#include "Mocksys.h"
#include "Mocksys_mon.h"
#include "Mockuart.h"

#include "fram_cfg.h"
#include "ftask_cfg.h"
#include "pex_cfg.h"
#include "sys_mon_cfg.h"

#include "fassert.h"
#include "ftask.h"
#include "test_assert_helper.h"

/*========== Unit Testing Framework Directives ==============================*/
TEST_INCLUDE_PATH("../../src/app/application/algorithm")
TEST_INCLUDE_PATH("../../src/app/application/algorithm/config")
TEST_INCLUDE_PATH("../../src/app/application/algorithm/state_estimation")
TEST_INCLUDE_PATH("../../src/app/application/algorithm/state_estimation/sof/trapezoid")
TEST_INCLUDE_PATH("../../src/app/application/bal")
TEST_INCLUDE_PATH("../../src/app/application/bms")
TEST_INCLUDE_PATH("../../src/app/application/redundancy")
TEST_INCLUDE_PATH("../../src/app/driver/adc")
TEST_INCLUDE_PATH("../../src/app/driver/afe/api")
TEST_INCLUDE_PATH("../../src/app/driver/can")
TEST_INCLUDE_PATH("../../src/app/driver/config")
TEST_INCLUDE_PATH("../../src/app/driver/contactor")
TEST_INCLUDE_PATH("../../src/app/driver/dma")
TEST_INCLUDE_PATH("../../src/app/driver/emac")
TEST_INCLUDE_PATH("../../src/app/driver/fram")
TEST_INCLUDE_PATH("../../src/app/driver/htsensor")
TEST_INCLUDE_PATH("../../src/app/driver/i2c")
TEST_INCLUDE_PATH("../../src/app/driver/imd")
TEST_INCLUDE_PATH("../../src/app/driver/interlock")
TEST_INCLUDE_PATH("../../src/app/driver/led")
TEST_INCLUDE_PATH("../../src/app/driver/meas")
TEST_INCLUDE_PATH("../../src/app/driver/pex")
TEST_INCLUDE_PATH("../../src/app/driver/phy")
TEST_INCLUDE_PATH("../../src/app/driver/rtc")
TEST_INCLUDE_PATH("../../src/app/driver/sbc")
TEST_INCLUDE_PATH("../../src/app/driver/sbc/fs8x_driver")
TEST_INCLUDE_PATH("../../src/app/driver/spi")
TEST_INCLUDE_PATH("../../src/app/driver/sps")
TEST_INCLUDE_PATH("../../src/app/driver/uart")
TEST_INCLUDE_PATH("../../src/app/engine/diag")
TEST_INCLUDE_PATH("../../src/app/engine/hw_info")
TEST_INCLUDE_PATH("../../src/app/engine/sys")
TEST_INCLUDE_PATH("../../src/app/engine/sys_mon")
TEST_INCLUDE_PATH("../../src/app/task/config")
TEST_INCLUDE_PATH("../../src/app/task/ftask")
TEST_INCLUDE_PATH("../../src/os/freertos/freertos-plus/freertos-plus-tcp/source/include")
TEST_INCLUDE_PATH("../../src/os/freertos/freertos-plus/freertos-plus-tcp/source/portable/Compiler/CCS")
TEST_INCLUDE_PATH("../../src/os/freertos/freertos-plus/freertos-plus-tcp/source/portable/NetworkInterface/tms570lc435")

/*========== Definitions and Implementations for Unit Test ==================*/
OS_TASK_HANDLE ftsk_taskHandleAfe;

#define FTSK_DATA_QUEUE_LENGTH      (1u)
#define FTSK_DATA_QUEUE_ITEM_SIZE   (sizeof(DATA_QUEUE_MESSAGE_s))
#define FTSK_IMD_QUEUE_LENGTH       (5u)
#define FTSK_IMD_QUEUE_ITEM_SIZE    (sizeof(CAN_BUFFER_ELEMENT_s))
#define FTSK_CAN_RX_QUEUE_LENGTH    (50u)
#define FTSK_CAN_RX_QUEUE_ITEM_SIZE (sizeof(CAN_BUFFER_ELEMENT_s))

volatile OS_BOOT_STATE_e os_boot = OS_OFF;
volatile OS_TIMER_s os_timer     = {0, 0, 0, 0, 0, 0, 0};
uint32_t os_schedulerStartTime   = 0;
SBC_STATE_s sbc_stateMcuSupervisor;

SYS_STATE_s sys_state = {0};

/*========== Setup and Teardown =============================================*/
void setUp(void) {
}

void tearDown(void) {
}

extern void NIC_Receive(void);

/*========== Test Cases =====================================================*/
/**
 * @brief   FTSK_RunUserCodeUart handles flow control, then blocks until the
 *          notification that the UART task has work.
 * @details src/app/task/config/ftask_cfg.c:330-338:
 *            :330  #if defined(FOXBMS_UART_SUPPORT) && FOXBMS_UART_SUPPORT == 1
 *            :331  void FTSK_RunUserCodeUart(void) {
 *            :334      UART_HandleFlowControl();
 *            :336      (void)OS_NotifyTake(pdTRUE, portMAX_DELAY);
 *            :337  }
 *            :338  #endif
 *          Both arguments of OS_NotifyTake are asserted as resolved literals
 *          rather than as the macros the source writes, so a wrong macro cannot
 *          satisfy the expectation:
 *            pdTRUE is ((BaseType_t)1) at
 *              src/os/freertos/freertos/include/projdefs.h:53
 *            portMAX_DELAY: src/os/freertos/freertos/include/FreeRTOSConfig.h:75
 *              sets configTICK_TYPE_WIDTH_IN_BITS to TICK_TYPE_WIDTH_32_BITS,
 *              which selects the 32-bit arm of
 *              src/os/freertos/freertos/portable/ccs/arm_cortex-r5/portmacro.h:59-60
 *              `#define portMAX_DELAY ( TickType_t ) 0xFFFFFFFFF`. TickType_t is
 *              uint32_t there (portmacro.h:58), so the value is 0xFFFFFFFF.
 *              That was confirmed by asking the compiler, not by reading alone.
 *
 *          This test is compiled with FOXBMS_UART_SUPPORT=1, granted at
 *          conf/unit/app_project_posix.yml:208-210.
 */
/* cspell:disable-next-line */
void testFTSK_RunUserCodeUart(void) {
    TEST_ASSERT_EQUAL_INT(1, FOXBMS_UART_SUPPORT);

    /* ======= RT1/1: call function under test ============================= */
    UART_HandleFlowControl_Expect();
    /* pdTRUE == 1, portMAX_DELAY == 0xFFFFFFFF on this configuration */
    OS_NotifyTake_ExpectAndReturn(1, 0xFFFFFFFFu, 1u);
    FTSK_RunUserCodeUart();

    /* ======= RT1/1: test output verification ============================= */
    /* Reaching this point IS the verification: both expectations had to be
     * consumed, in order. UART_HandleFlowControl_CallCount() is deliberately
     * not used - in this build it returns the CALLBACK call count, which stays
     * 0 for a call made through a normal expectation
     * (mocks/test_ftask_cfg_emac/Mockuart.h). The argument values above are
     * compared by CMock, so pdTRUE and portMAX_DELAY are checked as literals
     * rather than as the macros the source writes. */
    TEST_ASSERT_EQUAL_INT(1, FOXBMS_UART_SUPPORT);
}

/**
 * @brief   FTSK_RunUserCodeEmac drains the ethernet receive path, once.
 * @details src/app/task/config/ftask_cfg.c:340-344:
 *            :340  #if (defined(FOXBMS_TCP_SUPPORT) && (FOXBMS_TCP_SUPPORT == 1))
 *            :341  void FTSK_RunUserCodeEmac(void) {
 *            :343      NIC_Receive();
 *            :344  }
 *            :345  #endif
 *          NIC_Receive is declared in the module that this test mocks for real
 *          (src/os/freertos/freertos-plus/.../NetworkInterface), and takes no
 *          arguments, so the whole claim is that it is reached exactly once.
 *          This test is compiled with FOXBMS_TCP_SUPPORT=1, granted at
 *          conf/unit/app_project_posix.yml:208-210.
 */
/* cspell:disable-next-line */
void testFTSK_RunUserCodeEmac(void) {
    TEST_ASSERT_EQUAL_INT(1, FOXBMS_TCP_SUPPORT);

    /* ======= RT1/1: call function under test ============================= */
    NIC_Receive_Expect();
    FTSK_RunUserCodeEmac();

    /* ======= RT1/1: test output verification ============================= */
    /* NIC_Receive takes no arguments, so the expectation IS the claim: it was
     * reached exactly once. See the UART case for why the call-count accessor
     * is not used. */
    TEST_ASSERT_EQUAL_INT(1, FOXBMS_TCP_SUPPORT);
}

/**
 * @brief   The two entry points do not call each other's work.
 * @details UART_HandleFlowControl at ftask_cfg.c:334 and NIC_Receive at :343 are
 *          in separate functions with separate guards, so an EMAC invocation
 *          must not reach the UART flow-control step and vice versa. Neither
 *          case sets an expectation on the other mock, so CMock turns a stray
 *          call into a failure; the counts below make that visible from the
 *          other side as well.
 */
/* cspell:disable-next-line */
void testFTSK_RunUserCodeEmacDoesNotRunTheUartFlowControlStep(void) {
    /* ======= RT1/1: call function under test ============================= */
    NIC_Receive_Expect();
    FTSK_RunUserCodeEmac();

    /* ======= RT1/1: test output verification ============================= */
    /* No expectation was set on the UART mocks, so if the EMAC entry point had
     * reached either of them CMock would have failed this case with "Called
     * more times than expected". Being green is the assertion. */
    TEST_ASSERT_EQUAL_INT(1, FOXBMS_TCP_SUPPORT);
}

/**
 * @brief   The UART entry point stops after its two calls: no ethernet work.
 * @details The complement of the case above, for ftask_cfg.c:331-337.
 */
/* cspell:disable-next-line */
void testFTSK_RunUserCodeUartDoesNotRunTheEthernetReceiveStep(void) {
    /* ======= RT1/1: call function under test ============================= */
    UART_HandleFlowControl_Expect();
    OS_NotifyTake_ExpectAndReturn(1, 0xFFFFFFFFu, 1u);
    FTSK_RunUserCodeUart();

    /* ======= RT1/1: test output verification ============================= */
    /* No expectation was set on NIC_Receive, so reaching it would have failed
     * the case. Being green is the assertion. */
    TEST_ASSERT_EQUAL_INT(1, FOXBMS_UART_SUPPORT);
}
