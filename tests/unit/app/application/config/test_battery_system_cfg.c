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
 * @file    test_battery_system_cfg.c
 * @author  foxBMS Team
 * @date    2020-04-02 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Tests for the battery_system_cfg module
 * @details TODO
 *
 */

/*========== Includes =======================================================*/
#include "unity.h"
#include "Mockdatabase.h"

#include "battery_system_cfg.h"
#include "database_cfg.h"

#include <stdint.h>

/*========== Unit Testing Framework Directives ==============================*/

/*========== Definitions and Implementations for Unit Test ==================*/

/*========== Setup and Teardown =============================================*/
void setUp(void) {
}

void tearDown(void) {
}

/*========== Test Cases =====================================================*/

/**
 * @brief   battery_system_cfg.c exports exactly one object: the per-string flag
 *          saying whether that string may be used for precharging. It is read
 *          by the precharge state machine; a wrong entry attempts a precharge
 *          on a string the hardware cannot precharge.
 * @details battery_system_cfg.c:65-67
 *              BS_STRING_PRECHARGE_PRESENT_e bs_stringsWithPrecharge[BS_NR_OF_STRINGS] = {
 *                  BS_STRING_WITH_PRECHARGE,
 *              };
 *          BS_NR_OF_STRINGS is (1u), so the table has exactly one element and it
 *          is BS_STRING_WITH_PRECHARGE, the first enumerator of the enum at
 *          battery_system_cfg.h:78-81 (value 0).
 * *  NOTE ON THE CITATION: under UNITY_UNIT_TEST, battery_system_cfg.h:342
 * includes battery_system_cfg_unit_test.h, which REDEFINES these macros. The value
 * in force for a unit-test build is the one in battery_system_cfg_unit_test.h, not
 * the identically-valued one in battery_system_cfg.h. Both files are cited because
 * both matter: the unit-test header is what the assertion below actually sees, and
 * battery_system_cfg.h is what the production build sees. Changing only
 * battery_system_cfg.h would leave this test green while the product changed --
 * that was measured, not assumed: perturbing battery_system_cfg.h:109 to (2u)
 * left test_battery_system_cfg.c passing.
 * 
 */
void testBatterySystemStringsWithPrecharge(void) {
    /* ======= Assertion tests ============================================= */
    /* the table is sized by BS_NR_OF_STRINGS, which is 1 for this configuration */
    TEST_ASSERT_EQUAL_UINT32(1u, (uint32_t)(sizeof(bs_stringsWithPrecharge) /
                                            sizeof(bs_stringsWithPrecharge[0])));
    /* entry 0 is BS_STRING_WITH_PRECHARGE; the enumerator is the first of
     * BS_STRING_PRECHARGE_PRESENT_e (battery_system_cfg.h:78-81) so its value
     * is 0, and its complement BS_STRING_WITHOUT_PRECHARGE is 1. */
    TEST_ASSERT_EQUAL_INT(0, (int)bs_stringsWithPrecharge[0]);
    TEST_ASSERT_EQUAL_INT(0, (int)BS_STRING_WITH_PRECHARGE);
    TEST_ASSERT_EQUAL_INT(1, (int)BS_STRING_WITHOUT_PRECHARGE);
    /* assert the identity, not just the number, so a reordering of the enum
     * that happened to keep the table's value at 0 would be caught here */
    TEST_ASSERT_EQUAL_INT((int)BS_STRING_WITH_PRECHARGE, (int)bs_stringsWithPrecharge[0]);
}

/**
 * @brief   The string-count macros this configuration is built on. They size
 *          every array in the data block layer, so a change here is a change
 *          in the memory layout of the whole database, not a tuning value.
 * @details battery_system_cfg.h is overridden for unit-test builds by
 *          battery_system_cfg_unit_test.h (included from battery_system_cfg.h:342), so
 *          the two sets of citations are given side by side:
 *            BS_NR_OF_STRINGS                     battery_system_cfg.h:109  = (1u)
 *                                               battery_system_cfg_unit_test.h:124 = (1u)
 *            BS_NR_OF_MODULES_PER_STRING          battery_system_cfg.h:122  = (1u)
 *                                               battery_system_cfg_unit_test.h:141 = (1u)
 *            BS_NR_OF_CELL_BLOCKS_PER_MODULE      battery_system_cfg.h:132  = (18u)
 *                                               battery_system_cfg_unit_test.h:155 = (18u)
 *            BS_NR_OF_PARALLEL_CELLS_PER_CELL_BLOCK battery_system_cfg.h:140 = (1u)
 *                                               battery_system_cfg_unit_test.h:164 = (1u)
 *          battery_system_cfg.h:153  BS_NR_OF_CELL_BLOCKS_PER_STRING
 *                                       = BS_NR_OF_MODULES_PER_STRING * BS_NR_OF_CELL_BLOCKS_PER_MODULE
 *                                       = 1 * 18 = 18
 *          battery_system_cfg.h:155  BS_NR_OF_CELL_BLOCKS
 *                                       = BS_NR_OF_CELL_BLOCKS_PER_STRING * BS_NR_OF_STRINGS
 *                                       = 18 * 1 = 18
 *          No per-test override in conf/unit/app_project_posix.yml matches
 *          "test_battery_system_cfg", so the 18u at battery_system_cfg_unit_test.h:155
 *          is the value in force.
 *          The two derived counts are written as the LITERAL 18, not as the
 *          macro expression that defines them: comparing a macro against its own
 *          definition cannot fail whatever the macro says.
 */
void testBatterySystemStringCountMacros(void) {
    /* ======= Assertion tests ============================================= */
    TEST_ASSERT_EQUAL_UINT32(1u, (uint32_t)BS_NR_OF_STRINGS);
    TEST_ASSERT_EQUAL_UINT32(1u, (uint32_t)BS_NR_OF_MODULES_PER_STRING);
    TEST_ASSERT_EQUAL_UINT32(18u, (uint32_t)BS_NR_OF_CELL_BLOCKS_PER_MODULE);
    TEST_ASSERT_EQUAL_UINT32(1u, (uint32_t)BS_NR_OF_PARALLEL_CELLS_PER_CELL_BLOCK);
    /* the two derived counts, evaluated from the three factors above */
    TEST_ASSERT_EQUAL_UINT32(18u, (uint32_t)BS_NR_OF_CELL_BLOCKS_PER_STRING);
    TEST_ASSERT_EQUAL_UINT32(18u, (uint32_t)BS_NR_OF_CELL_BLOCKS);
}
