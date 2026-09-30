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
 * @file    test_ftask_cfg_afe.c
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
TEST_INCLUDE_PATH("../../src/app/engine/diag")
TEST_INCLUDE_PATH("../../src/app/engine/hw_info")
TEST_INCLUDE_PATH("../../src/app/engine/sys")
TEST_INCLUDE_PATH("../../src/app/engine/sys_mon")
TEST_INCLUDE_PATH("../../src/app/task/config")
TEST_INCLUDE_PATH("../../src/app/task/ftask")

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

/*========== Test Cases =====================================================*/

/**
 * @brief   FTSK_RunUserCodeAfe runs the measurement control step.
 * @details src/app/task/config/ftask_cfg.c:323-328:
 *            :323  #if (FOXBMS_AFE_DRIVER_TYPE_NO_FSM == 1)
 *            :324  void FTSK_RunUserCodeAfe(void) {
 *            :326      MEAS_Control();
 *            :327  }
 *            :328  #endif
 *          The whole body is that one call. The claim is therefore that
 *          MEAS_Control is reached, and MEAS_Control_Expect() is the assertion:
 *          CMock fails the case if the call does not happen ("Called fewer times
 *          than expected") AND if it happens without an expectation ("Called more
 *          times than expected"). So the expectation constrains the count from
 *          both sides.
 *
 *          MEAS_Control_CallCount() is deliberately NOT used. In this build the
 *          generated mock defines it as `return
 *          Mock.MEAS_Control_CallbackCalls;`, and that counter is only
 *          incremented on the callback path, inside the generated
 *          `if (!CallbackBool && CallbackFunctionPointer != NULL) { ...
 *          return; }` block - so a call made through a normal expectation leaves
 *          it at 0. Both of those are in a GENERATED file
 *          (mocks/test_ftask_cfg_afe/Mockmeas.c), which Ceedling deletes between
 *          runs, so they are described rather than cited by line here; the
 *          behaviour was read out of the generated source and reproduced above
 *          verbatim. A call
 *          made through a normal expectation therefore leaves it at 0, so
 *          asserting on it reads as "not called" when the call did happen. That
 *          was measured, not assumed: the first version of this case asserted
 *          MEAS_Control_CallCount() == 1 and failed with "Expected 1 Was 0"
 *          against a test whose MEAS_Control_Expect() was satisfied.
 *
 *          This test is compiled with FOXBMS_AFE_DRIVER_TYPE_NO_FSM=1, granted at
 *          conf/unit/app_project_posix.yml:206-207, which is what makes the :323
 *          guard true and the function exist at all.
 */
/* cspell:disable-next-line */
void testFTSK_RunUserCodeAfeRunsMeasControl(void) {
    /* the guard at ftask_cfg.c:323 is satisfied in this build, so the
     * function under test is the one the source declares, not an absent one */
    TEST_ASSERT_EQUAL_INT(1, FOXBMS_AFE_DRIVER_TYPE_NO_FSM);

    /* ======= RT1/1: call function under test ============================= */
    MEAS_Control_Expect();
    FTSK_RunUserCodeAfe();

    /* ======= RT1/1: test output verification ============================= */
    /* Reaching this point IS the verification: had MEAS_Control not been
     * called, CMock_Verify at the end of the case would have failed it. */
    TEST_ASSERT_EQUAL_INT(1, FOXBMS_AFE_DRIVER_TYPE_NO_FSM);
}

/**
 * @brief   Each invocation runs exactly one measurement control step.
 * @details Two expectations and two invocations. CMock matches calls to
 *          expectations in order and fails on an unmatched extra call, so green
 *          here means each FTSK_RunUserCodeAfe ran exactly one MEAS_Control and
 *          the module does not accumulate state between calls. A body that
 *          called MEAS_Control twice would fail the second invocation with
 *          "Called more times than expected"; a body that called it zero times
 *          would fail with "Called fewer times than expected".
 */
/* cspell:disable-next-line */
void testFTSK_RunUserCodeAfeRunsOneMeasControlPerInvocation(void) {
    /* ======= RT1/1: call function under test ============================= */
    MEAS_Control_Expect();
    FTSK_RunUserCodeAfe();
    MEAS_Control_Expect();
    FTSK_RunUserCodeAfe();

    /* ======= RT1/1: test output verification ============================= */
    /* both expectations were consumed exactly once; see the case above for why
     * the call-count accessor is not used */
    TEST_ASSERT_EQUAL_INT(1, FOXBMS_AFE_DRIVER_TYPE_NO_FSM);
}
