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
 * @file    test_ltc_6806_cfg.c
 * @author  foxBMS Team
 * @date    2020-04-01 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Tests of the LTC LTC6806 configuration
 * @details TODO
 *
 */

/*========== Includes =======================================================*/
#include "unity.h"

#include "ltc_6806_cfg.h"

/*========== Unit Testing Framework Directives ==============================*/
TEST_INCLUDE_PATH("../../src/app/driver/afe/api")
TEST_INCLUDE_PATH("../../src/app/driver/afe/ltc/6806/config")
TEST_INCLUDE_PATH("../../src/app/driver/afe/ltc/common")
TEST_INCLUDE_PATH("../../src/app/driver/afe/ltc/common/config")
TEST_INCLUDE_PATH("../../src/app/driver/config")
TEST_INCLUDE_PATH("../../src/app/driver/spi")

/*========== Definitions and Implementations for Unit Test ==================*/

/*========== Setup and Teardown =============================================*/
void setUp(void) {
}

void tearDown(void) {
}

/*========== Test Cases =====================================================*/

/**
 * @brief   ltc_voltage_input_used is the per-cell table that tells the LTC
 *          measurement state machine which of the 18 amplifier inputs are
 *          wired to cells on this board.
 * @details ltc_6806_cfg.c:66-69
 *              const uint8_t ltc_voltage_input_used[LTC_6806_MAX_SUPPORTED_CELLS] = {
 *                  1u, 1u, ... (36 entries, all 1u)
 *              };
 *          LTC_6806_MAX_SUPPORTED_CELLS is (36u) at ltc_6806_cfg.h:88, so the
 *          table has 36 elements. The configured pack has 18 cells per module
 *          (BS_NR_OF_CELL_BLOCKS_PER_MODULE = 18u, battery_system_cfg_unit_test.h:155;
 *          battery_system_cfg.h:132 carries the same value but is overridden for unit-test
 *          builds by the include at battery_system_cfg.h:342), so
 *          the table is deliberately larger than the pack: entries 18..35 are
 *          spare capacity and must still be 1, because the state machine walks
 *          the whole declared table and a 0 there would read a floating input.
 *          The 36 figure is cited, not taken from the macro, so that a change
 *          to the macro cannot silently resize the table under this test.
 */
void testLtc6806VoltageInputUsedTable(void) {
    /* ======= Assertion tests ============================================= */
    /* the table is sized by LTC_6806_MAX_SUPPORTED_CELLS = 36u (ltc_6806_cfg.h:88) */
    TEST_ASSERT_EQUAL_UINT32(36u, (uint32_t)(sizeof(ltc_voltage_input_used) /
                                             sizeof(ltc_voltage_input_used[0])));
    /* every one of the 36 declared inputs is marked as used */
    for (uint32_t i = 0u; i < 36u; i++) {
        TEST_ASSERT_EQUAL_UINT8_MESSAGE(1u, ltc_voltage_input_used[i],
                                        "every declared LTC6806 voltage input must be marked used");
    }
}

/**
 * @brief   The first 18 entries are the cells actually wired on this
 *          configuration and the remaining 18 are spare. Both halves are
 *          asserted explicitly so a truncation of the table, which would leave
 *          the first half intact, cannot pass.
 * @details battery_system_cfg.h:132 sets 18 cell blocks per module; the table
 *          at ltc_6806_cfg.c:67-68 lists 18 values on the first line and 18 on
 *          the second, all 1u.
 */
void testLtc6806VoltageInputUsedCoversPackAndSpare(void) {
    /* ======= Assertion tests ============================================= */
    /* the 18 cells of the configured pack */
    for (uint32_t i = 0u; i < 18u; i++) {
        TEST_ASSERT_EQUAL_UINT8(1u, ltc_voltage_input_used[i]);
    }
    /* the 18 spare inputs beyond the pack */
    for (uint32_t i = 18u; i < 36u; i++) {
        TEST_ASSERT_EQUAL_UINT8(1u, ltc_voltage_input_used[i]);
    }
    /* the pack in force is 18 cell blocks per module, from
     * battery_system_cfg_unit_test.h:155, which overrides battery_system_cfg.h:132
     * for unit-test builds (included at battery_system_cfg.h:342) */
    TEST_ASSERT_EQUAL_UINT32(18u, (uint32_t)BS_NR_OF_CELL_BLOCKS_PER_MODULE);
}
