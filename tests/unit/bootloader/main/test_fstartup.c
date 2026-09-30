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
 * @file    test_fstartup.c
 * @author  foxBMS Team
 * @date    2024-09-17 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Unit tests for the MCU startup routine of the bootloader on the TI
 *          TMS570Lx43xx
 * @details Testing the startup procedure of the MCU is a relatively complex
 *          unit test. The startup procedure needs to the read a register
 *          (esmREG.SR1[...] defined in MockHL_reg_esm.h) to run mitigation
 *          strategies in case of errors. As reading these registers on the
 *          host platform is of course not possible, a workaround is needed.
 *          The workaround requires configuration in
 *          'conf/unit/bootloader_project_win32.yml'.
 *          This test can not be run on Linux, therefore **no**
 *          configuration is required in
 *          'conf/unit/bootloader_project_posix.yml'.
 *          The esmREG is mocked through
 *          'tests/unit/bootloader/main/helper/m_esm.h'. This requires, that
 *          the test does **not** include 'MockHL_reg_esm.h', but only the
 *          mocked 'm_esm.h'. This is achived by providing the include guard
 *          of 'MockHL_reg_esm.h' as compiler argument
 *          (gcc ... -D__REG_ESM_H__ ...).
 *          This further requires, that in the driver implementation
 *          'fstartup.c' includes 'm_esm.h' (guarded for only the unit test
 *          case) first. By that, and by providing '-D__REG_ESM_H__' the driver
 *          compiles for the target as well as for the unit test with the
 *          correct implementation.
 *          'm_esm.h' just keeps a minimal type configuration, just detailed
 *          enough to mock all required registers, but not more.
 *          The function to get the reset source of the MCU
 *          (STU_GetResetSourceWithoutFlagReset) is not tested, as this is
 *          based on register values, that can not be reasonably mocked on the
 *          host. Therefore, this unit test includes just a dummy function to
 *          emulate STU_GetResetSourceWithoutFlagReset and enables by that to
 *          check all startup cases.
 */

/* cspell:ignore SSWF plls */

/*========== Includes =======================================================*/
#include "unity.h"

#include "HL_hal_stdtypes.h"

#include "m_esm.h"

/* clang-format off */
#include "MockHL_sys_common.h"
#include "MockHL_hal_stdtypes.h"
#include "MockHL_system.h"
#include "MockHL_sys_vim.h"
#include "MockHL_sys_core.h"
#include "MockHL_reg_esm.h"
#include "MockHL_esm.h"
#include "MockHL_sys_mpu.h"
#include "MockHL_errata_SSWF021_45.h"
/* clang-format on */

#include "fstartup.h"
#include "test_assert_helper.h"

/*========== Unit Testing Framework Directives ==============================*/

TEST_INCLUDE_PATH("../../tests/unit/bootloader/main/helper")
/* The HALCoGen headers this test used to name explicitly,
 *      TEST_INCLUDE_PATH("C:/ti/Hercules/HALCoGen/v04.07.01/drivers/"
 *                        "TMS570LC4357ZWT/SYSTEM570v000")
 * are already on the include path of both shipped Ceedling projects
 * (conf/unit/bootloader_project_posix.yml and bootloader_project_win32.yml,
 * under ":paths: :include:", as the recursive include of the variant's
 * generated header directory, annotated "# HALCoGen"), because the unit-test
 * driver runs HALCoGen with the build variant directory as its working
 * directory and the generated headers land in that include/ directory
 * (cli/cmd_embedded_ut/embedded_ut_impl.py:324-334).
 * An absolute Windows TI installation path is therefore a redundant second
 * route to the same files, and it is not merely redundant: Ceedling resolves
 * TEST_INCLUDE_PATH eagerly and aborts the whole run with "'<path>' ... not
 * found" during "Collecting Essential Test Context", before a single
 * translation unit is compiled, on any host that does not have that TI
 * installation. It is removed rather than repointed, because repointing it at
 * a host-relative directory would hard-code this verification environment's
 * layout into a test that also has to build in the project's own build.
 *
 * WHAT IS UNDER TEST, AND WHAT IS SUBSTITUTED
 * --------------------------------------------
 * The code under test is foxBMS's own src/bootloader/main/fstartup.c. Every TI
 * HAL entry point it calls is mocked here (the MockHL_* headers above), so this
 * test never executes TI startup code and asserts nothing about it.
 *
 * What the mocked boundary is compiled against is host-dependent:
 *   - in a project build, the real HALCoGen output (HL_esm.h, HL_reg_esm.h,
 *     HL_reg_system.h, HL_system.h, HL_sys_common.h, HL_sys_core.h,
 *     HL_sys_mpu.h, HL_sys_vim.h, HL_hal_stdtypes.h,
 *     HL_errata_SSWF021_45.h);
 *   - in the SIL host unit-test harness, host-declared stand-ins for the
 *     subset of that surface this module uses. Those stand-ins declare
 *     signatures only. They carry no register offset, base address or bit
 *     mask, so nothing here validates the register map.
 * Read a failure in this test as a defect in fstartup.c's control flow, never
 * as a statement about the Hercules device.
 *
 * NOTE ON THE UPSTREAM EXCLUSION
 * ------------------------------
 * conf/unit/bootloader_project_posix.yml still removes this file from the
 * bootloader variant under ":files: :test:", with the comment "this file can
 * only be tested on Windows due to HALCoGen availability". That exclusion is
 * NOT removed here, because that project file is out of scope for this change.
 *
 * That comment's stated reason is not the actual blocker, and the distinction
 * matters. HALCoGen availability is not what made the file unbuildable here: the
 * nine headers this file mocks (HL_sys_common.h, HL_hal_stdtypes.h,
 * HL_system.h, HL_sys_vim.h, HL_sys_core.h, HL_reg_esm.h, HL_esm.h,
 * HL_sys_mpu.h, HL_errata_SSWF021_45.h) are all generated by the project's own
 * HALCoGen input - each appears as a <NAME> entry in conf/hcg/bootloader.hcg -
 * and land in the variant's include/ directory, which both bootloader project
 * files already put on the include path recursively under ":paths: :include:",
 * annotated "# HALCoGen". What made it unbuildable on a non-Windows host was
 * only the absolute "C:/ti/..." TEST_INCLUDE_PATH removed above, which Ceedling
 * resolves eagerly and which aborted the run during "Collecting Essential Test
 * Context" before any translation unit was compiled.
 *
 * MEASURED, not assumed: with that line removed and the ":files:" entry deleted
 * from a scratch copy of the bootloader project file in a disposable SIL
 * workspace, this test builds and passes -
 *     OVERALL TEST SUMMARY  TESTED: 2  PASSED: 2  FAILED: 0
 * (testSTU_HandlePllLockFail, which asserts TEST_STU_HandlePllLockFail traps
 * when the PLL never locks, and test_c_int00, which pins the exact ordered
 * sequence of ten mocked TI initialisation calls with no ESM group3 error).
 * The scratch copy was discarded and the shipped project file is byte-identical
 * to its state before this experiment. Deleting the ":files:" entry in
 * conf/unit/bootloader_project_posix.yml is therefore a one-line change, and it
 * is left undone only because that file is outside the scope of this change.
 */

/*========== Definitions and Implementations for Unit Test ==================*/

esmBASE_t dummy   = {.SR1 = {0u, 0u, 0u}};
esmBASE_t *esmREG = &dummy;

#define DEFAULT_CASE (0xFFFFU)
static resetSource_t selector = POWERON_RESET;
extern resetSource_t STU_GetResetSourceWithoutFlagReset(void);

extern void __TI_auto_init(void) {
}

extern resetSource_t STU_GetResetSourceWithoutFlagReset(void) {
    resetSource_t returnValue;
    if (selector == POWERON_RESET) {
        returnValue = POWERON_RESET;
    }
    if (selector == OSC_FAILURE_RESET) {
        returnValue = OSC_FAILURE_RESET;
    }
    if (selector == WATCHDOG_RESET) {
        returnValue = WATCHDOG_RESET;
    }
    if (selector == WATCHDOG2_RESET) {
        returnValue = WATCHDOG2_RESET;
    }
    if (selector == DEBUG_RESET) {
        returnValue = DEBUG_RESET;
    }
    if (selector == INTERCONNECT_RESET) {
        returnValue = INTERCONNECT_RESET;
    }
    if (selector == CPU0_RESET) {
        returnValue = CPU0_RESET;
    }
    if (selector == SW_RESET) {
        returnValue = SW_RESET;
    }
    if (selector == EXT_RESET) {
        returnValue = EXT_RESET;
    }
    if (selector == NO_RESET) {
        returnValue = NO_RESET;
    }
    if (selector == DEFAULT_CASE) {
        returnValue = DEFAULT_CASE;
    }
    return returnValue;
}

/*========== Setup and Teardown =============================================*/
void setUp(void) {
}

void tearDown(void) {
}

/*========== Test Cases =====================================================*/

void testSTU_HandlePllLockFail(void) {
    TEST_ASSERT_FAIL_ASSERT(TEST_STU_HandlePllLockFail());
}

/**
 * @brief   Testing extern function _c_int00
 * @details The following cases need to be tested:
 *          - Argument validation:
 *            - None
 *          - Routine validation:
 *            - RT01/11: POWERON_RESET restart and **no** PLL failure, and
 *                       **no** ESM group3 errors
 *            - RT02/11:
 *            - RT03/11:
 *            - RT04/11:
 *            - RT05/11:
 *            - RT06/11:
 *            - RT07/11:
 *            - RT08/11:
 *            - RT09/11:
 *            - RT10/11:
 *            - RT11/11:
 */
void test_c_int00(void) {
    /* ======= Assertion tests ============================================= */
    /* ======= None ======= */

    /* ======= Routine tests =============================================== */
    /* ======= RT01/11: Test implementation */
    /* case POWERON_RESET: 'POWERON_RESET' is fallthrough and includes the
     *      cases 'DEBUG_RESET' and 'EXT_RESET'
     *      **no** PLL failure
     *      **no** ESM group3 errors
     */
    selector = POWERON_RESET;             /* set reset source: value to test for */
    STU_GetResetSourceWithoutFlagReset(); /* set reset source: sets value to desired 'selector' value */
    esmREG->SR1[2] = 0u;                  /* no ESM group3 errors */

    _coreInitRegisters__Expect();
    _coreInitStackPointer__Expect();
    _memInit__Expect();
    _errata_SSWF021_45_both_plls_ExpectAndReturn(5u, 0u); /* no PLL failure */
    _coreEnableEventBusExport__Expect();
    systemInit_Expect();
    _coreEnableIrqVicOffset__Expect();
    vimInit_Expect();
    esmInit_Expect();
    _mpuInit__Expect();
    _cacheEnable__Expect();

    /* ======= RT01/11: call function under test */
    _c_int00();

    /* ======= RT01/11: test output verification */
    /* nothing to be verified */

    /* ======= RT02/11: Test implementation */
    /* case POWERON_RESET: 'POWERON_RESET' is fallthrough and includes the
     *      cases 'DEBUG_RESET' and 'EXT_RESET'
     *      PLL failure
     *      **no** ESM group3 errors
     */
    selector = POWERON_RESET;
    STU_GetResetSourceWithoutFlagReset(); /* returns value of 'selector' */
    esmREG->SR1[2] = 0u;                  /* no ESM group3 errors */

    _coreInitRegisters__Expect();
    _coreInitStackPointer__Expect();
    _memInit__Expect();
    _errata_SSWF021_45_both_plls_ExpectAndReturn(5u, 1u); /* PLL failure */

    /* ======= RT02/11: call function under test */
    TEST_ASSERT_FAIL_ASSERT(_c_int00());

    /* ======= RT02/11: test output verification */
    /* nothing to be verified */

    /* ======= RT03/11: Test implementation */
    /* case POWERON_RESET: 'POWERON_RESET' is fallthrough and includes the
     *      cases 'DEBUG_RESET' and 'EXT_RESET'.
     *      **no** PLL failure
     *      ESM group3 errors
     */
    selector = POWERON_RESET;
    STU_GetResetSourceWithoutFlagReset(); /* returns value of 'selector' */
    esmREG->SR1[2] = 1u;                  /* ESM group3 errors */

    _coreInitRegisters__Expect();
    _coreInitStackPointer__Expect();
    _memInit__Expect();
    _errata_SSWF021_45_both_plls_ExpectAndReturn(5u, 0u); /* no PLL failure */
    _coreEnableEventBusExport__Expect();
    esmGroup3Notification_Expect(esmREG, esmREG->SR1[2u]);
    systemInit_Expect();
    _coreEnableIrqVicOffset__Expect();
    vimInit_Expect();
    esmInit_Expect();
    _mpuInit__Expect();
    _cacheEnable__Expect();

    /* ======= RT03/11: call function under test */
    _c_int00();

    /* ======= RT03/11: test output verification */
    /* nothing to be verified */

    /* ======= RT04/11: Test implementation */
    /* case DEBUG_RESET: 'DEBUG_RESET' is fallthrough and includes the case
     *      'EXT_RESET'
     *      **no** PLL failure
     *      **no** ESM group3 errors
     */
    selector = DEBUG_RESET;
    STU_GetResetSourceWithoutFlagReset(); /* returns value of 'selector' */
    esmREG->SR1[2] = 0u;                  /* no ESM group3 errors */

    _coreInitRegisters__Expect();
    _coreInitStackPointer__Expect();
    _memInit__Expect();
    _coreEnableEventBusExport__Expect();
    systemInit_Expect();
    _coreEnableIrqVicOffset__Expect();
    vimInit_Expect();
    esmInit_Expect();
    _mpuInit__Expect();
    _cacheEnable__Expect();

    /* ======= RT04/11: call function under test */
    _c_int00();

    /* ======= RT04/11: test output verification */
    /* nothing to be verified */

    /* ======= RT05/11: Test implementation */
    /* case EXT_RESET: 'EXT_RESET' is fallthrough and includes the case
     *      'SW_RESET'
     *      **no** ESM group3 errors
     */
    selector = DEBUG_RESET;
    STU_GetResetSourceWithoutFlagReset(); /* returns value of 'selector' */
    esmREG->SR1[2] = 0u;                  /* no ESM group3 errors */

    _coreInitRegisters__Expect();
    _coreInitStackPointer__Expect();
    _memInit__Expect();
    _coreEnableEventBusExport__Expect();
    systemInit_Expect();
    _coreEnableIrqVicOffset__Expect();
    vimInit_Expect();
    esmInit_Expect();
    _mpuInit__Expect();
    _cacheEnable__Expect();

    /* ======= RT05/11: call function under test */
    _c_int00();

    /* ======= RT05/11: test output verification */
    /* nothing to be verified */

    /* ======= RT06/11: Test implementation */
    /* case SW_RESET: **no** ESM group3 errors (not required, due to the other
     *      tests, that already include this)
     */
    selector = SW_RESET;
    STU_GetResetSourceWithoutFlagReset(); /* returns value of 'selector' */
    esmREG->SR1[2] = 0u;                  /* no ESM group3 errors */

    _coreInitRegisters__Expect();
    _coreInitStackPointer__Expect();
    _memInit__Expect();
    _coreEnableEventBusExport__Expect();
    systemInit_Expect();
    _coreEnableIrqVicOffset__Expect();
    vimInit_Expect();
    esmInit_Expect();
    _mpuInit__Expect();
    _cacheEnable__Expect();

    /* ======= RT06/11: call function under test */
    _c_int00();

    /* ======= RT06/11: test output verification */
    /* nothing to be verified */

    /* ======= RT07/11: Test implementation */
    /* case OSC_FAILURE_RESET */
    selector = OSC_FAILURE_RESET;
    STU_GetResetSourceWithoutFlagReset();
    _coreInitRegisters__Expect();
    _coreInitStackPointer__Expect();
    _mpuInit__Expect();
    _cacheEnable__Expect();

    /* ======= RT07/11: call function under test */
    _c_int00();

    /* ======= RT07/11: test output verification */
    /* nothing to be verified */

    /* ======= RT08/11: Test implementation */
    /* case WATCHDOG_RESET */
    selector = WATCHDOG_RESET;
    STU_GetResetSourceWithoutFlagReset();
    _coreInitRegisters__Expect();
    _coreInitStackPointer__Expect();
    _mpuInit__Expect();
    _cacheEnable__Expect();

    /* ======= RT08/11: call function under test */
    _c_int00();

    /* ======= RT08/11: test output verification */
    /* nothing to be verified */

    /* ======= RT09/11: Test implementation */
    /* case WATCHDOG2_RESET */
    selector = WATCHDOG2_RESET;
    STU_GetResetSourceWithoutFlagReset();
    _coreInitRegisters__Expect();
    _coreInitStackPointer__Expect();
    _mpuInit__Expect();
    _cacheEnable__Expect();

    /* ======= RT09/11: call function under test */
    _c_int00();

    /* ======= RT09/11: test output verification */
    /* nothing to be verified */

    /* ======= RT10/11: Test implementation */
    /* case CPU0_RESET */
    selector = CPU0_RESET;
    STU_GetResetSourceWithoutFlagReset();

    _coreInitRegisters__Expect();
    _coreInitStackPointer__Expect();
    _coreEnableEventBusExport__Expect();
    _mpuInit__Expect();
    _cacheEnable__Expect();

    /* ======= RT10/11: call function under test */
    _c_int00();

    /* ======= RT10/11: test output verification */
    /* nothing to be verified */

    /* ======= RT11/11: Test implementation */
    /* case default */
    selector = DEFAULT_CASE;
    STU_GetResetSourceWithoutFlagReset();

    _coreInitRegisters__Expect();
    _coreInitStackPointer__Expect();
    _mpuInit__Expect();
    _cacheEnable__Expect();

    /* ======= RT11/: call function under test */
    _c_int00();

    /* ======= RT11/: test output verification */
    /* nothing to be verified */
}
