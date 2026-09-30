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
 * @file    test_sof_trapezoid_cfg.c
 * @author  foxBMS Team
 * @date    2020-10-07 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Test for the configuration for SOF
 * @details TODO
 *
 */

/*========== Includes =======================================================*/
#include "unity.h"

#include "sof_trapezoid_cfg.h"

/*========== Unit Testing Framework Directives ==============================*/
TEST_INCLUDE_PATH("../../src/app/application/algorithm/state_estimation/sof/trapezoid")

/*========== Definitions and Implementations for Unit Test ==================*/

/*========== Setup and Teardown =============================================*/
void setUp(void) {
}

void tearDown(void) {
}

/*========== Test Cases =====================================================*/

/**
 * @brief   The recommended current table is the input the trapezoid SOF
 *          estimator runs on, so a wrong literal here silently changes the
 *          charge/discharge limits the BMS enforces.
 * @details Every expected value is written as a LITERAL, never as the macro
 *          the product line uses. A macro would make the assertion
 *          self-referential: it would compare the table against the same macro
 *          that built it, so a wrong macro could never fail. Each literal is
 *          cited to the macro that resolves to it, and the resolution chain is
 *          reproduced in the comment.
 *
 *          Sources, all in sof_trapezoid_cfg.h and battery_cell_cfg.h:
 *            SOF_STRING_CURRENT_CONTINUOUS_CHARGE_mA    sof_trapezoid_cfg.h:73
 *              = (float_t)BC_CURRENT_MAX_CHARGE_MOL_mA * BS_NR_OF_PARALLEL_CELLS_PER_CELL_BLOCK
 *              = 170000u * 1u                                       = 170000
 *            SOF_STRING_CURRENT_CONTINUOUS_DISCHARGE_mA sof_trapezoid_cfg.h:80      = 170000
 *            SOF_STRING_CURRENT_LIMP_HOME_mA            sof_trapezoid_cfg.h:87      = 20000
 *            SOF_TEMPERATURE_LOW_CUTOFF_DISCHARGE_ddegC  sof_trapezoid_cfg.h:94
 *              = BC_TEMPERATURE_MIN_DISCHARGE_MOL_ddegC = -100
 *            SOF_TEMPERATURE_LOW_LIMIT_DISCHARGE_ddegC   sof_trapezoid_cfg.h:101     = -200
 *            SOF_TEMPERATURE_LOW_CUTOFF_CHARGE_ddegC     sof_trapezoid_cfg.h:108     = -100
 *            SOF_TEMPERATURE_LOW_LIMIT_CHARGE_ddegC      sof_trapezoid_cfg.h:115     = -200
 *            SOF_TEMPERATURE_HIGH_CUTOFF_DISCHARGE_ddegC sof_trapezoid_cfg.h:122     =  450
 *            SOF_TEMPERATURE_HIGH_LIMIT_DISCHARGE_ddegC  sof_trapezoid_cfg.h:129     =  550
 *            SOF_TEMPERATURE_HIGH_CUTOFF_CHARGE_ddegC    sof_trapezoid_cfg.h:136     =  350
 *            SOF_TEMPERATURE_HIGH_LIMIT_CHARGE_ddegC     sof_trapezoid_cfg.h:143     =  450
 *            SOF_VOLTAGE_LIMIT_CHARGE_mV                 sof_trapezoid_cfg.h:153
 *              = BC_VOLTAGE_MAX_RSL_mV                   = 2750
 *            SOF_VOLTAGE_CUTOFF_CHARGE_mV                sof_trapezoid_cfg.h:148
 *              = BC_VOLTAGE_MAX_MSL_mV                   = 2720
 *            SOF_VOLTAGE_LIMIT_DISCHARGE_mV              sof_trapezoid_cfg.h:163     = 1550
 *            SOF_VOLTAGE_CUTOFF_DISCHARGE_mV             sof_trapezoid_cfg.h:158
 *              = BC_VOLTAGE_MIN_MOL_mV                   = 1580
 */
/* cspell:disable-next-line */
void testSofRecommendedCurrentMatchesConfiguredLimits(void) {
    /* ======= Assertion tests ============================================= */
    TEST_ASSERT_EQUAL_FLOAT(170000.0f, sof_recommendedCurrent.maximumChargeCurrent_mA);
    TEST_ASSERT_EQUAL_FLOAT(170000.0f, sof_recommendedCurrent.maximumDischargeCurrent_mA);
    TEST_ASSERT_EQUAL_FLOAT(20000.0f, sof_recommendedCurrent.limpHomeCurrent_mA);

    TEST_ASSERT_EQUAL_INT16(-100, sof_recommendedCurrent.cutoffLowTemperatureDischarge_ddegC);
    TEST_ASSERT_EQUAL_INT16(-200, sof_recommendedCurrent.limitLowTemperatureDischarge_ddegC);
    TEST_ASSERT_EQUAL_INT16(-100, sof_recommendedCurrent.cutoffLowTemperatureCharge_ddegC);
    TEST_ASSERT_EQUAL_INT16(-200, sof_recommendedCurrent.limitLowTemperatureCharge_ddegC);
    TEST_ASSERT_EQUAL_INT16(450, sof_recommendedCurrent.cutoffHighTemperatureDischarge_ddegC);
    TEST_ASSERT_EQUAL_INT16(550, sof_recommendedCurrent.limitHighTemperatureDischarge_ddegC);
    TEST_ASSERT_EQUAL_INT16(350, sof_recommendedCurrent.cutoffHighTemperatureCharge_ddegC);
    TEST_ASSERT_EQUAL_INT16(450, sof_recommendedCurrent.limitHighTemperatureCharge_ddegC);

    TEST_ASSERT_EQUAL_INT16(2750, sof_recommendedCurrent.limitUpperCellVoltage_mV);
    TEST_ASSERT_EQUAL_INT16(2720, sof_recommendedCurrent.cutoffUpperCellVoltage_mV);
    TEST_ASSERT_EQUAL_INT16(1550, sof_recommendedCurrent.limitLowerCellVoltage_mV);
    TEST_ASSERT_EQUAL_INT16(1580, sof_recommendedCurrent.cutoffLowerCellVoltage_mV);
}

/**
 * @brief   The ordering of the cutoff/limit pair is the whole point of the
 *          structure: a cutoff beyond its limit would let the estimator run in
 *          a band the caller believes is closed. Assert the ordering itself,
 *          not just the four numbers, so a later edit that swaps two fields
 *          cannot pass.
 * @details Derived from the values at sof_trapezoid_cfg.h:72-163 as written
 *          above; the invariant is a property of those literals.
 */
/* cspell:disable-next-line */
void testSofRecommendedCurrentCutoffAndLimitOrdering(void) {
    /* ======= Assertion tests ============================================= */
    /* low side: the cutoff sits inside the limit on both directions */
    TEST_ASSERT_TRUE(sof_recommendedCurrent.cutoffLowTemperatureDischarge_ddegC >
                     sof_recommendedCurrent.limitLowTemperatureDischarge_ddegC);
    TEST_ASSERT_TRUE(sof_recommendedCurrent.cutoffLowTemperatureCharge_ddegC >
                     sof_recommendedCurrent.limitLowTemperatureCharge_ddegC);

    /* high side: the cutoff sits below its limit on both directions */
    TEST_ASSERT_TRUE(sof_recommendedCurrent.cutoffHighTemperatureDischarge_ddegC <
                     sof_recommendedCurrent.limitHighTemperatureDischarge_ddegC);
    TEST_ASSERT_TRUE(sof_recommendedCurrent.cutoffHighTemperatureCharge_ddegC <
                     sof_recommendedCurrent.limitHighTemperatureCharge_ddegC);

    /* charge window sits above the discharge window on the voltage axis:
     * a BMS may only charge above the voltage at which it stops discharging. */
    TEST_ASSERT_TRUE(sof_recommendedCurrent.limitUpperCellVoltage_mV >
                     sof_recommendedCurrent.limitLowerCellVoltage_mV);
    TEST_ASSERT_TRUE(sof_recommendedCurrent.cutoffUpperCellVoltage_mV >
                     sof_recommendedCurrent.cutoffLowerCellVoltage_mV);

    /* limp-home current is a reduced limit, never a raised one */
    TEST_ASSERT_TRUE(sof_recommendedCurrent.limpHomeCurrent_mA <
                     sof_recommendedCurrent.maximumChargeCurrent_mA);
    TEST_ASSERT_TRUE(sof_recommendedCurrent.limpHomeCurrent_mA <
                     sof_recommendedCurrent.maximumDischargeCurrent_mA);
}

/*========== Test Cases =====================================================*/
