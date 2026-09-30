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
 * @file    test_battery_cell_cfg.c
 * @author  foxBMS Team
 * @date    2020-10-08 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Test for the battery cell configuration
 * @details TODO
 *
 */

/*========== Includes =======================================================*/
#include "unity.h"

#include "battery_cell_cfg.h"

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
 * @brief   The state-of-charge and state-of-energy lookup tables are the
 *          interpolation input for the SOC/SOE estimators. A wrong entry moves
 *          the reported state of charge without any error being raised.
 * @details The tables are written as 100 entries, one per percent, from 100%
 *          down to 1% (battery_cell_cfg.c:67-83 and :86-102). The two exported
 *          length symbols at :104-105 are sizeof()/sizeof() of those same
 *          tables, so they are asserted against the literal 100.
 *
 *          Endpoints and the mid-table row, cited to the initialiser lines:
 *            bc_stateOfChargeLookupTable[0]  = {4123, 100.0f}  (:68)
 *            bc_stateOfChargeLookupTable[50] = {3636,  50.0f}  (:75)
 *            bc_stateOfChargeLookupTable[99] = {2716,   1.0f}  (:82)
 *            bc_stateOfEnergyLookupTable[0]  = {4163, 100.0f}  (:87)
 *            bc_stateOfEnergyLookupTable[50] = {3726,  50.0f}  (:94)
 *            bc_stateOfEnergyLookupTable[99] = {2572,   1.0f}  (:101)
 */
void testBatteryCellLookupTableLengths(void) {
    /* ======= Assertion tests ============================================= */
    TEST_ASSERT_EQUAL_UINT16(100, bc_stateOfChargeLookupTableLength);
    TEST_ASSERT_EQUAL_UINT16(100, bc_stateOfEnergyLookupTableLength);
}

void testBatteryCellLookupTableEndpoints(void) {
    /* ======= Assertion tests ============================================= */
    /* state of charge: 100% -> 0% direction, endpoints and midpoint */
    TEST_ASSERT_EQUAL_INT16(4123, bc_stateOfChargeLookupTable[0].voltage_mV);
    TEST_ASSERT_EQUAL_FLOAT(100.0f, bc_stateOfChargeLookupTable[0].value);
    TEST_ASSERT_EQUAL_INT16(3636, bc_stateOfChargeLookupTable[50].voltage_mV);
    TEST_ASSERT_EQUAL_FLOAT(50.0f, bc_stateOfChargeLookupTable[50].value);
    TEST_ASSERT_EQUAL_INT16(2716, bc_stateOfChargeLookupTable[99].voltage_mV);
    TEST_ASSERT_EQUAL_FLOAT(1.0f, bc_stateOfChargeLookupTable[99].value);

    /* state of energy */
    TEST_ASSERT_EQUAL_INT16(4163, bc_stateOfEnergyLookupTable[0].voltage_mV);
    TEST_ASSERT_EQUAL_FLOAT(100.0f, bc_stateOfEnergyLookupTable[0].value);
    TEST_ASSERT_EQUAL_INT16(3726, bc_stateOfEnergyLookupTable[50].voltage_mV);
    TEST_ASSERT_EQUAL_FLOAT(50.0f, bc_stateOfEnergyLookupTable[50].value);
    TEST_ASSERT_EQUAL_INT16(2572, bc_stateOfEnergyLookupTable[99].voltage_mV);
    TEST_ASSERT_EQUAL_FLOAT(1.0f, bc_stateOfEnergyLookupTable[99].value);
}

/**
 * @brief   Both tables are consumed by a linear interpolation that assumes a
 *          strictly decreasing voltage axis and a strictly decreasing value
 *          column. An out-of-order row would make the interpolation search
 *          return the wrong segment. Assert the property over all 100 rows,
 *          not just sampled ones.
 * @details The initialisers at battery_cell_cfg.c:68-82 and :87-101 are
 *          written in descending order; the loop checks the whole table.
 */
void testBatteryCellLookupTablesAreStrictlyDescending(void) {
    /* ======= Assertion tests ============================================= */
    for (uint16_t i = 0u; i < (uint16_t)(bc_stateOfChargeLookupTableLength - 1u); i++) {
        TEST_ASSERT_TRUE_MESSAGE(
            bc_stateOfChargeLookupTable[i].voltage_mV > bc_stateOfChargeLookupTable[i + 1u].voltage_mV,
            "state-of-charge voltage axis must be strictly descending");
        TEST_ASSERT_TRUE_MESSAGE(
            bc_stateOfChargeLookupTable[i].value > bc_stateOfChargeLookupTable[i + 1u].value,
            "state-of-charge value column must be strictly descending");
    }
    for (uint16_t i = 0u; i < (uint16_t)(bc_stateOfEnergyLookupTableLength - 1u); i++) {
        TEST_ASSERT_TRUE_MESSAGE(
            bc_stateOfEnergyLookupTable[i].voltage_mV > bc_stateOfEnergyLookupTable[i + 1u].voltage_mV,
            "state-of-energy voltage axis must be strictly descending");
        TEST_ASSERT_TRUE_MESSAGE(
            bc_stateOfEnergyLookupTable[i].value > bc_stateOfEnergyLookupTable[i + 1u].value,
            "state-of-energy value column must be strictly descending");
    }
}

/**
 * @brief   The value column is a percentage in 1% steps, so row i carries
 *          100-i. That identity is what the interpolation relies on, and it is
 *          not implied by monotonicity alone.
 * @details Read off the second column of battery_cell_cfg.c:68-82 / :87-101.
 */
void testBatteryCellLookupTableValueColumnIsOnePercentSteps(void) {
    /* ======= Assertion tests ============================================= */
    for (uint16_t i = 0u; i < bc_stateOfChargeLookupTableLength; i++) {
        TEST_ASSERT_EQUAL_FLOAT((float_t)(100u - i), bc_stateOfChargeLookupTable[i].value);
    }
    for (uint16_t i = 0u; i < bc_stateOfEnergyLookupTableLength; i++) {
        TEST_ASSERT_EQUAL_FLOAT((float_t)(100u - i), bc_stateOfEnergyLookupTable[i].value);
    }
}
