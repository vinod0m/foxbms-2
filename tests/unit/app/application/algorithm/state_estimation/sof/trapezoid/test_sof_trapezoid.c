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
 * @file    test_sof_trapezoid.c
 * @author  foxBMS Team
 * @date    2020-10-07 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Tests for SOC module responsible for calculation of current derating
 * @details The four static helpers of sof_trapezoid.c are reachable through the
 *          TEST_SOF_* wrappers the module exports under UNITY_UNIT_TEST
 *          (sof_trapezoid.c:438-:471), and SOF_Calculation() reaches the
 *          database through DATA_Read1DataBlock()/DATA_Write1DataBlock()
 *          (sof_trapezoid.c:358, :433).
 *
 */

/*========== Includes =======================================================*/
#include "unity.h"
#include "Mockbms.h"
#include "Mockdatabase.h"
#include "Mockfoxmath.h"
#include "Mockfram.h"

#include "sof_trapezoid_cfg.h"

#include "sof_trapezoid.h"

#include "test_assert_helper.h"

/*========== Unit Testing Framework Directives ==============================*/
TEST_INCLUDE_PATH("../../src/app/application/algorithm/state_estimation")
TEST_INCLUDE_PATH("../../src/app/application/algorithm/state_estimation/sof/trapezoid")
TEST_INCLUDE_PATH("../../src/app/application/bms")
TEST_INCLUDE_PATH("../../src/app/driver/config")
TEST_INCLUDE_PATH("../../src/app/driver/contactor")
TEST_INCLUDE_PATH("../../src/app/driver/foxmath")
TEST_INCLUDE_PATH("../../src/app/driver/fram")
TEST_INCLUDE_PATH("../../src/app/driver/sps")
TEST_INCLUDE_PATH("../../src/app/task/config")

/*========== Definitions and Implementations for Unit Test ==================*/
FRAM_SOC_s fram_soc = {0};

/*========== Setup and Teardown =============================================*/
/* sof_trapezoid.c:438-440 exports the static curve builder under
 * UNITY_UNIT_TEST, but sof_trapezoid.h declares only the other three wrappers
 * (:118, :124, :130). The prototype is repeated here so the test can call it
 * without relying on an implicit declaration. */
extern void TEST_SOF_CalculateCurves(const SOF_CONFIG_s *pConfigurationValues, SOF_CURVE_s *pCalculatedSofCurveValues);

/* Every value the tests assert is read out of the module's own configuration
 * table, sof_recommendedCurrent (sof_trapezoid_cfg.c:66-:81), which is built
 * from these constants:
 *   BC_CURRENT_MAX_CHARGE_MOL_mA            170000  battery_cell_cfg.h:204
 *   BC_CURRENT_MAX_DISCHARGE_MOL_mA         170000  battery_cell_cfg.h:189
 *   BS_NR_OF_PARALLEL_CELLS_PER_CELL_BLOCK      1  battery_system_cfg.h:140
 *   SOF_STRING_CURRENT_LIMP_HOME_mA          20000  sof_trapezoid_cfg.h:63
 *   SOF_TEMPERATURE_LOW_CUTOFF_DISCHARGE      -100  BC_TEMPERATURE_MIN_DISCHARGE_MOL_ddegC
 *   SOF_TEMPERATURE_LOW_LIMIT_DISCHARGE       -200  BC_TEMPERATURE_MIN_DISCHARGE_MSL_ddegC
 *   SOF_TEMPERATURE_LOW_CUTOFF_CHARGE         -100  BC_TEMPERATURE_MIN_CHARGE_MOL_ddegC
 *   SOF_TEMPERATURE_LOW_LIMIT_CHARGE          -200  BC_TEMPERATURE_MIN_CHARGE_MSL_ddegC
 *   SOF_TEMPERATURE_HIGH_CUTOFF_DISCHARGE      450  BC_TEMPERATURE_MAX_DISCHARGE_MOL_ddegC
 *   SOF_TEMPERATURE_HIGH_LIMIT_DISCHARGE       550  BC_TEMPERATURE_MAX_DISCHARGE_MSL_ddegC
 *   SOF_TEMPERATURE_HIGH_CUTOFF_CHARGE         350  BC_TEMPERATURE_MAX_CHARGE_MOL_ddegC
 *   SOF_TEMPERATURE_HIGH_LIMIT_CHARGE          450  BC_TEMPERATURE_MAX_CHARGE_MSL_ddegC
 *   SOF_VOLTAGE_LIMIT_CHARGE_mV                2750  BC_VOLTAGE_MAX_RSL_mV
 *   SOF_VOLTAGE_CUTOFF_CHARGE_mV               2720  BC_VOLTAGE_MAX_MOL_mV
 *   SOF_VOLTAGE_LIMIT_DISCHARGE_mV             1550  BC_VOLTAGE_MIN_RSL_mV
 *   SOF_VOLTAGE_CUTOFF_DISCHARGE_mV            1580  BC_VOLTAGE_MIN_MOL_mV
 */
#define TEST_SOF_MAX_CHARGE_MA           (170000.0f)
#define TEST_SOF_MAX_DISCHARGE_MA        (170000.0f)
#define TEST_SOF_LIMP_HOME_MA            (20000.0f)
#define TEST_SOF_LIMIT_LOW_TEMP_DIS_ddC   ((int16_t)-200)
#define TEST_SOF_CUTOFF_LOW_TEMP_DIS_ddC  ((int16_t)-100)
#define TEST_SOF_LIMIT_LOW_TEMP_CHG_ddC   ((int16_t)-200)
#define TEST_SOF_CUTOFF_LOW_TEMP_CHG_ddC  ((int16_t)-100)
#define TEST_SOF_CUTOFF_HIGH_TEMP_DIS_ddC ((int16_t)450)
#define TEST_SOF_LIMIT_HIGH_TEMP_DIS_ddC  ((int16_t)550)
#define TEST_SOF_CUTOFF_HIGH_TEMP_CHG_ddC ((int16_t)350)
#define TEST_SOF_LIMIT_HIGH_TEMP_CHG_ddC  ((int16_t)450)
#define TEST_SOF_LIMIT_UPPER_VOLT_mV       ((int16_t)2750)
#define TEST_SOF_CUTOFF_UPPER_VOLT_mV      ((int16_t)2720)
#define TEST_SOF_LIMIT_LOWER_VOLT_mV       ((int16_t)1550)
#define TEST_SOF_CUTOFF_LOWER_VOLT_mV      ((int16_t)1580)

/* Tolerance for the two slopes that are not exactly representable in binary
 * floating point. slopeUpperCellVoltage is 170000/30 = 5666.666..., whose float
 * representation is 5666.66650390625; 0.01 is two orders of magnitude tighter
 * than the value and one order looser than the representation error. */
#define TEST_SOF_SLOPE_TOL (0.01f)
#define TEST_SOF_OFFSET_TOL (2.0f)

/* SOF_Calculation() fills a module-static table and hands its address to the
 * database (sof_trapezoid.c:433). DATA_Read1DataBlock() and
 * DATA_Write1DataBlock() both take a void*, for which CMock compares one byte,
 * so neither _Expect nor its call count is used as an oracle here. Instead the
 * two database entry points are routed through callbacks: the read callback
 * fills the minimum/maximum block the way the database would, and the write
 * callback copies the block the module is about to publish so the test can
 * read it back. */
static DATA_BLOCK_MIN_MAX_s test_sofMinMax;
static DATA_BLOCK_SOF_s     test_sofPublished;
static uint32_t             test_sofReadCount;
static uint32_t             test_sofWriteCount;

static STD_RETURN_TYPE_e sofReadCallback(void *pDataToReceiver, int n) {
    (void)n;
    test_sofReadCount++;
    if (pDataToReceiver != NULL) {
        *((DATA_BLOCK_MIN_MAX_s *)(void *)pDataToReceiver) = test_sofMinMax;
    }
    return STD_OK;
}

static STD_RETURN_TYPE_e sofWriteCallback(void *pDataFromSender, int n) {
    (void)n;
    test_sofWriteCount++;
    if (pDataFromSender != NULL) {
        test_sofPublished = *((const DATA_BLOCK_SOF_s *)(const void *)pDataFromSender);
    }
    return STD_OK;
}

/* MATH_MinimumOfTwoFloats() is a product function, here mocked, so the test
 * supplies the real minimum through an AddCallback. AddCallback is used rather
 * than Stub on purpose: a Stub returns from the mock before CMock's ordering
 * counter is advanced, so the eight registered calls of SOF_Calculation() would
 * not be seen at all. With AddCallback, CMock still checks the operands against
 * the _ExpectAndReturn registrations and still checks the call order, and the
 * value the module then stores is the registered return value. */
static float_t sofMinimumCallback(const float_t value1, const float_t value2, int n) {
    (void)n;
    return (value1 < value2) ? value1 : value2;
}

void setUp(void) {
    test_sofMinMax    = (DATA_BLOCK_MIN_MAX_s){0};
    test_sofPublished = (DATA_BLOCK_SOF_s){0};
    test_sofReadCount  = 0u;
    test_sofWriteCount = 0u;
    DATA_Read1DataBlock_AddCallback(sofReadCallback);
    DATA_Write1DataBlock_AddCallback(sofWriteCallback);
    MATH_MinimumOfTwoFloats_AddCallback(sofMinimumCallback);
}

void tearDown(void) {
}

/** @brief   registers exactly one database read and one database write, which
 *          is what SOF_Calculation() performs (sof_trapezoid.c:358, :433)
 * @details the arguments are void*, for which CMock compares a single byte, so
 *          the expected pointer is deliberately NULL and then ignored; the
 *          pointer the module actually passes is captured by the callbacks
 *          above instead of being compared.
 */
static void test_sofExpectDatabaseRead(void) {
    DATA_Read1DataBlock_ExpectAndReturn(NULL_PTR, STD_OK);
    DATA_Read1DataBlock_IgnoreArg_pDataToReceiver0();
}

static void test_sofExpectDatabaseWrite(void) {
    DATA_Write1DataBlock_ExpectAndReturn(NULL_PTR, STD_OK);
    DATA_Write1DataBlock_IgnoreArg_pDataFromSender0();
}

/*========== Test Cases =====================================================*/

/** @brief   the SOF curve is the straight line through the configured limit and
 *           cutoff points
 * @details sof_trapezoid.c:148-:188 builds a slope and an offset per limit so
 *          that the curve passes through the limit point and reaches the cutoff
 *          value. With the shipped configuration the twelve results are
 *          exactly representable except the two voltage slopes.
 */
void testSOFCalculateCurvesMatchesTheConfiguredLimitAndCutoffPoints(void) {
    SOF_CURVE_s curve = {0};

    TEST_SOF_CalculateCurves(&sof_recommendedCurrent, &curve);

    /* sof_trapezoid.c:148-151: (170000 - 20000) / (-100 - (-200)) = 150000/100 */
    TEST_ASSERT_EQUAL_FLOAT(1500.0f, curve.slopeLowTemperatureDischarge);
    /* sof_trapezoid.c:152-154: 20000 - 1500 * (-200) */
    TEST_ASSERT_EQUAL_FLOAT(320000.0f, curve.offsetLowTemperatureDischarge);
    /* sof_trapezoid.c:156-159: (0 - 170000) / (550 - 450) = -170000/100. The
     * denominator is limit minus cutoff here, the opposite order from the
     * low-temperature line at :150-:151. */
    TEST_ASSERT_EQUAL_FLOAT(-1700.0f, curve.slopeHighTemperatureDischarge);
    /* sof_trapezoid.c:160-162: 0 - (-1700 * 550) */
    TEST_ASSERT_EQUAL_FLOAT(935000.0f, curve.offsetHighTemperatureDischarge);
    /* sof_trapezoid.c:164-166: (170000 - 0) / (-100 - (-200)) = 170000/100 */
    TEST_ASSERT_EQUAL_FLOAT(1700.0f, curve.slopeLowTemperatureCharge);
    /* sof_trapezoid.c:167-169: 0 - 1700 * (-200) */
    TEST_ASSERT_EQUAL_FLOAT(340000.0f, curve.offsetLowTemperatureCharge);
    /* sof_trapezoid.c:171-173: (0 - 170000) / (450 - 350) = -170000/100 */
    TEST_ASSERT_EQUAL_FLOAT(-1700.0f, curve.slopeHighTemperatureCharge);
    /* sof_trapezoid.c:174-176: 0 - (-1700 * 450) */
    TEST_ASSERT_EQUAL_FLOAT(765000.0f, curve.offsetHighTemperatureCharge);
    /* sof_trapezoid.c:178-180: (170000 - 0) / (1580 - 1550) = 170000/30 */
    TEST_ASSERT_FLOAT_WITHIN(TEST_SOF_SLOPE_TOL, 5666.66650390625f, curve.slopeUpperCellVoltage);
    /* sof_trapezoid.c:181-182: 0 - slope * 1550 */
    TEST_ASSERT_FLOAT_WITHIN(TEST_SOF_OFFSET_TOL, -8783333.0f, curve.offsetUpperCellVoltage);
    /* sof_trapezoid.c:184-186: (170000 - 0) / (2720 - 2750) = 170000/-30 */
    TEST_ASSERT_FLOAT_WITHIN(TEST_SOF_SLOPE_TOL, -5666.66650390625f, curve.slopeLowerCellVoltage);
    /* sof_trapezoid.c:187-188: 0 - slope * 1550. The offset is taken at the
     * LOWER voltage limit here, not at limitUpperCellVoltage_mV. */
    TEST_ASSERT_FLOAT_WITHIN(TEST_SOF_OFFSET_TOL, 8783333.0f, curve.offsetLowerCellVoltage);
}

/** @brief   the curve is evaluated at the limit and at the cutoff point
 * @details the invariant the slope/offset pair is built for: at the limit the
 *          derating is 0 and at the cutoff it is the maximum current. This
 *          checks the arithmetic of sof_trapezoid.c:148-:188 rather than
 *          re-stating its twelve constants.
 */
void testSOFCalculateCurvesEvaluatesToZeroAtTheLimitAndFullAtTheCutoff(void) {
    SOF_CURVE_s curve = {0};

    TEST_SOF_CalculateCurves(&sof_recommendedCurrent, &curve);

    /* The four temperature offsets are the ones the module actually reads back:
     * offsetLowTemperatureDischarge at sof_trapezoid.c:257,
     * offsetLowTemperatureCharge at :274, offsetHighTemperatureDischarge at
     * :290 and offsetHighTemperatureCharge at :314. Each is checked here at the
     * point its own slope/offset pair is anchored on, and at the far end of the
     * interval. */
    TEST_ASSERT_FLOAT_WITHIN(
        TEST_SOF_OFFSET_TOL,
        TEST_SOF_LIMP_HOME_MA,
        (curve.slopeLowTemperatureDischarge * (float_t)TEST_SOF_LIMIT_LOW_TEMP_DIS_ddC) +
            curve.offsetLowTemperatureDischarge);
    TEST_ASSERT_FLOAT_WITHIN(
        TEST_SOF_OFFSET_TOL,
        TEST_SOF_MAX_DISCHARGE_MA,
        (curve.slopeLowTemperatureDischarge * (float_t)TEST_SOF_CUTOFF_LOW_TEMP_DIS_ddC) +
            curve.offsetLowTemperatureDischarge);
    TEST_ASSERT_FLOAT_WITHIN(
        TEST_SOF_OFFSET_TOL,
        0.0f,
        (curve.slopeLowTemperatureCharge * (float_t)TEST_SOF_LIMIT_LOW_TEMP_CHG_ddC) +
            curve.offsetLowTemperatureCharge);
    TEST_ASSERT_FLOAT_WITHIN(
        TEST_SOF_OFFSET_TOL,
        TEST_SOF_MAX_CHARGE_MA,
        (curve.slopeLowTemperatureCharge * (float_t)TEST_SOF_CUTOFF_LOW_TEMP_CHG_ddC) +
            curve.offsetLowTemperatureCharge);
    TEST_ASSERT_FLOAT_WITHIN(
        TEST_SOF_OFFSET_TOL,
        0.0f,
        (curve.slopeHighTemperatureDischarge * (float_t)TEST_SOF_LIMIT_HIGH_TEMP_DIS_ddC) +
            curve.offsetHighTemperatureDischarge);
    TEST_ASSERT_FLOAT_WITHIN(
        TEST_SOF_OFFSET_TOL,
        TEST_SOF_MAX_DISCHARGE_MA,
        (curve.slopeHighTemperatureDischarge * (float_t)TEST_SOF_CUTOFF_HIGH_TEMP_DIS_ddC) +
            curve.offsetHighTemperatureDischarge);
    TEST_ASSERT_FLOAT_WITHIN(
        TEST_SOF_OFFSET_TOL,
        0.0f,
        (curve.slopeHighTemperatureCharge * (float_t)TEST_SOF_LIMIT_HIGH_TEMP_CHG_ddC) +
            curve.offsetHighTemperatureCharge);
    TEST_ASSERT_FLOAT_WITHIN(
        TEST_SOF_OFFSET_TOL,
        TEST_SOF_MAX_CHARGE_MA,
        (curve.slopeHighTemperatureCharge * (float_t)TEST_SOF_CUTOFF_HIGH_TEMP_CHG_ddC) +
            curve.offsetHighTemperatureCharge);
}

/** @brief   the two voltage offsets are written and never read
 * @details offsetUpperCellVoltage (sof_trapezoid.c:181-:182) and
 *          offsetLowerCellVoltage (:187-:188) are the only two members of
 *          SOF_CURVE_s that the module never reads back: the voltage derating
 *          evaluates the slope against a voltage measured from the LIMIT, not
 *          from zero (:209-:211 and :225-:227), so it has no use for an offset.
 *          That is a fact read out of the module, not a defect claim, and it is
 *          why no line property is asserted for the two voltage slopes: a line
 *          through (limit, 0) and (cutoff, current) does not exist in this
 *          source. Their values are still pinned by
 *          testSOFCalculateCurvesMatchesTheConfiguredLimitAndCutoffPoints.
 */
void testSOFCalculateCurvesVoltageOffsetsAreWrittenButNeverRead(void) {
    SOF_CURVE_s curve = {0};

    TEST_SOF_CalculateCurves(&sof_recommendedCurrent, &curve);

    /* sof_trapezoid.c:209-211 evaluates the slope against the voltage measured
     * from limitLowerCellVoltage_mV, so the derating is 0 at the lower limit */
    TEST_ASSERT_FLOAT_WITHIN(
        TEST_SOF_OFFSET_TOL,
        0.0f,
        curve.slopeUpperCellVoltage * (float_t)(TEST_SOF_LIMIT_LOWER_VOLT_mV - TEST_SOF_LIMIT_LOWER_VOLT_mV));
    /* and the full discharge current at the lower cutoff */
    TEST_ASSERT_FLOAT_WITHIN(
        TEST_SOF_OFFSET_TOL,
        TEST_SOF_MAX_DISCHARGE_MA,
        curve.slopeUpperCellVoltage *
            (float_t)(TEST_SOF_CUTOFF_LOWER_VOLT_mV - TEST_SOF_LIMIT_LOWER_VOLT_mV));
    /* sof_trapezoid.c:225-227 does the same for the charge current, from
     * limitUpperCellVoltage_mV downwards */
    TEST_ASSERT_FLOAT_WITHIN(
        TEST_SOF_OFFSET_TOL,
        0.0f,
        curve.slopeLowerCellVoltage * (float_t)(TEST_SOF_LIMIT_UPPER_VOLT_mV - TEST_SOF_LIMIT_UPPER_VOLT_mV));
    TEST_ASSERT_FLOAT_WITHIN(
        TEST_SOF_OFFSET_TOL,
        TEST_SOF_MAX_CHARGE_MA,
        curve.slopeLowerCellVoltage *
            (float_t)(TEST_SOF_CUTOFF_UPPER_VOLT_mV - TEST_SOF_LIMIT_UPPER_VOLT_mV));
}

/** @brief   the curve builder rejects NULL configuration and NULL result
 * @details the two guards at sof_trapezoid.c:144 and :145.
 */
void testSOFCalculateCurvesRejectsNullPointers(void) {
    SOF_CURVE_s curve = {0};
    /* sof_trapezoid.c:144 */
    TEST_ASSERT_FAIL_ASSERT(TEST_SOF_CalculateCurves(NULL_PTR, &curve));
    /* sof_trapezoid.c:145 */
    TEST_ASSERT_FAIL_ASSERT(TEST_SOF_CalculateCurves(&sof_recommendedCurrent, NULL_PTR));
}

/** @brief   a cell voltage at or below the limit forbids any discharge current
 * @details sof_trapezoid.c:204-206 zeroes both discharge currents when the
 *          minimum cell voltage is at or below limitLowerCellVoltage_mV.
 */
void testSOFVoltageLimitBelowTheLowerVoltageLimitForbidsDischarge(void) {
    SOF_CURVE_s           curve    = {0};
    SOF_CURRENT_LIMITS_s  allowed  = {1.0f, 1.0f, 1.0f, 1.0f};
    TEST_SOF_CalculateCurves(&sof_recommendedCurrent, &curve);

    /* the boundary value itself, sof_trapezoid.c:204 uses <= */
    TEST_SOF_CalculateVoltageBasedCurrentLimit(
        TEST_SOF_LIMIT_LOWER_VOLT_mV, 2000, &allowed, &sof_recommendedCurrent, &curve);
    TEST_ASSERT_EQUAL_FLOAT(0.0f, allowed.continuousDischargeCurrent_mA);
    TEST_ASSERT_EQUAL_FLOAT(0.0f, allowed.peakDischargeCurrent_mA);

    /* one millivolt below the boundary */
    allowed = (SOF_CURRENT_LIMITS_s){1.0f, 1.0f, 1.0f, 1.0f};
    TEST_SOF_CalculateVoltageBasedCurrentLimit(
        (int16_t)(TEST_SOF_LIMIT_LOWER_VOLT_mV - 1), 2000, &allowed, &sof_recommendedCurrent, &curve);
    TEST_ASSERT_EQUAL_FLOAT(0.0f, allowed.continuousDischargeCurrent_mA);
    TEST_ASSERT_EQUAL_FLOAT(0.0f, allowed.peakDischargeCurrent_mA);
}

/** @brief   a cell voltage above the lower cutoff allows the full discharge
 *          current
 * @details sof_trapezoid.c:214-217.
 */
void testSOFVoltageAboveTheLowerCutoffAllowsFullDischarge(void) {
    SOF_CURVE_s          curve   = {0};
    SOF_CURRENT_LIMITS_s allowed = {0};
    TEST_SOF_CalculateCurves(&sof_recommendedCurrent, &curve);

    /* the cutoff value itself, sof_trapezoid.c:208 uses <= */
    TEST_SOF_CalculateVoltageBasedCurrentLimit(
        TEST_SOF_CUTOFF_LOWER_VOLT_mV, 2000, &allowed, &sof_recommendedCurrent, &curve);
    TEST_ASSERT_EQUAL_FLOAT(TEST_SOF_MAX_DISCHARGE_MA, allowed.continuousDischargeCurrent_mA);
    TEST_ASSERT_EQUAL_FLOAT(TEST_SOF_MAX_DISCHARGE_MA, allowed.peakDischargeCurrent_mA);

    /* and one millivolt above it */
    TEST_SOF_CalculateVoltageBasedCurrentLimit(
        (int16_t)(TEST_SOF_CUTOFF_LOWER_VOLT_mV + 1), 2000, &allowed, &sof_recommendedCurrent, &curve);
    TEST_ASSERT_EQUAL_FLOAT(TEST_SOF_MAX_DISCHARGE_MA, allowed.continuousDischargeCurrent_mA);
    TEST_ASSERT_EQUAL_FLOAT(TEST_SOF_MAX_DISCHARGE_MA, allowed.peakDischargeCurrent_mA);
}

/** @brief   between limit and cutoff the discharge current follows the curve,
 *          and the peak current equals the continuous one
 * @details sof_trapezoid.c:208-213.
 */
void testSOFVoltageBetweenLimitAndCutoffDeratesTheDischargeCurrent(void) {
    SOF_CURVE_s          curve   = {0};
    SOF_CURRENT_LIMITS_s allowed = {0};
    TEST_SOF_CalculateCurves(&sof_recommendedCurrent, &curve);

    /* half way between limitLowerCellVoltage_mV (1550) and
     * cutoffLowerCellVoltage_mV (1580) is 1565, so the curve gives half the
     * maximum discharge current */
    TEST_SOF_CalculateVoltageBasedCurrentLimit(
        (int16_t)(TEST_SOF_LIMIT_LOWER_VOLT_mV + 15), 2000, &allowed, &sof_recommendedCurrent, &curve);
    TEST_ASSERT_FLOAT_WITHIN(1.0f, 85000.0f, allowed.continuousDischargeCurrent_mA);
    /* sof_trapezoid.c:212-213: the peak current is the continuous one here */
    TEST_ASSERT_EQUAL_FLOAT(allowed.continuousDischargeCurrent_mA, allowed.peakDischargeCurrent_mA);
}

/** @brief   a maximum cell voltage at or above the limit forbids any charge
 *          current
 * @details sof_trapezoid.c:220-222.
 */
void testSOFVoltageAtOrAboveTheUpperVoltageLimitForbidsCharge(void) {
    SOF_CURVE_s          curve   = {0};
    SOF_CURRENT_LIMITS_s allowed = {0};
    TEST_SOF_CalculateCurves(&sof_recommendedCurrent, &curve);

    /* the boundary value itself, sof_trapezoid.c:220 uses >= */
    TEST_SOF_CalculateVoltageBasedCurrentLimit(
        2000, TEST_SOF_LIMIT_UPPER_VOLT_mV, &allowed, &sof_recommendedCurrent, &curve);
    TEST_ASSERT_EQUAL_FLOAT(0.0f, allowed.continuousChargeCurrent_mA);
    TEST_ASSERT_EQUAL_FLOAT(0.0f, allowed.peakChargeCurrent_mA);

    /* one millivolt above the boundary */
    TEST_SOF_CalculateVoltageBasedCurrentLimit(
        2000, (int16_t)(TEST_SOF_LIMIT_UPPER_VOLT_mV + 1), &allowed, &sof_recommendedCurrent, &curve);
    TEST_ASSERT_EQUAL_FLOAT(0.0f, allowed.continuousChargeCurrent_mA);
    TEST_ASSERT_EQUAL_FLOAT(0.0f, allowed.peakChargeCurrent_mA);
}

/** @brief   below the upper cutoff the full charge current is allowed
 * @details sof_trapezoid.c:229-232.
 */
void testSOFVoltageBelowTheUpperCutoffAllowsFullCharge(void) {
    SOF_CURVE_s          curve   = {0};
    SOF_CURRENT_LIMITS_s allowed = {0};
    TEST_SOF_CalculateCurves(&sof_recommendedCurrent, &curve);

    /* the cutoff value itself, sof_trapezoid.c:224 uses >= */
    TEST_SOF_CalculateVoltageBasedCurrentLimit(
        2000, TEST_SOF_CUTOFF_UPPER_VOLT_mV, &allowed, &sof_recommendedCurrent, &curve);
    TEST_ASSERT_EQUAL_FLOAT(TEST_SOF_MAX_CHARGE_MA, allowed.continuousChargeCurrent_mA);
    TEST_ASSERT_EQUAL_FLOAT(TEST_SOF_MAX_CHARGE_MA, allowed.peakChargeCurrent_mA);
}

/** @brief   between cutoff and limit the charge current follows the curve
 * @details sof_trapezoid.c:224-228. slopeLowerCellVoltage is negative and the
 *          charge current falls as the cell voltage rises towards the limit.
 */
void testSOFVoltageBetweenCutoffAndLimitDeratesTheChargeCurrent(void) {
    SOF_CURVE_s          curve   = {0};
    SOF_CURRENT_LIMITS_s allowed = {0};
    TEST_SOF_CalculateCurves(&sof_recommendedCurrent, &curve);

    /* half way between cutoffUpperCellVoltage_mV (2720) and
     * limitUpperCellVoltage_mV (2750) is 2735 */
    TEST_SOF_CalculateVoltageBasedCurrentLimit(
        2000, (int16_t)(TEST_SOF_CUTOFF_UPPER_VOLT_mV + 15), &allowed, &sof_recommendedCurrent, &curve);
    TEST_ASSERT_FLOAT_WITHIN(1.0f, 85000.0f, allowed.continuousChargeCurrent_mA);
    TEST_ASSERT_EQUAL_FLOAT(allowed.continuousChargeCurrent_mA, allowed.peakChargeCurrent_mA);
}

/** @brief   the voltage derating rejects NULL results, NULL configuration and
 *          NULL curve
 * @details the three guards at sof_trapezoid.c:197, :198 and :199.
 */
void testSOFVoltageBasedCurrentLimitRejectsNullPointers(void) {
    SOF_CURVE_s          curve   = {0};
    SOF_CURRENT_LIMITS_s allowed = {0};
    /* sof_trapezoid.c:197 */
    TEST_ASSERT_FAIL_ASSERT(TEST_SOF_CalculateVoltageBasedCurrentLimit(
        2000, 2000, NULL_PTR, &sof_recommendedCurrent, &curve));
    /* sof_trapezoid.c:198 */
    TEST_ASSERT_FAIL_ASSERT(
        TEST_SOF_CalculateVoltageBasedCurrentLimit(2000, 2000, &allowed, NULL_PTR, &curve));
    /* sof_trapezoid.c:199 */
    TEST_ASSERT_FAIL_ASSERT(
        TEST_SOF_CalculateVoltageBasedCurrentLimit(2000, 2000, &allowed, &sof_recommendedCurrent, NULL_PTR));
}

/** @brief   a cell temperature at or below the low limit limits discharge to
 *          the limp-home current and forbids charging
 * @details sof_trapezoid.c:250-252 for the discharge side and :267-269 for
 *          the charge side.
 */
void testSOFTemperatureBelowTheLowLimitGivesLimpHomeDischargeAndNoCharge(void) {
    SOF_CURVE_s          curve   = {0};
    SOF_CURRENT_LIMITS_s allowed = {0};
    TEST_SOF_CalculateCurves(&sof_recommendedCurrent, &curve);

    /* the high-temperature branches still run: 0 ddegC is below both high
     * cutoffs, so :294-:295 and :318-:319 set the temporary value to the full
     * current and :300-:305 / :324-:328 take the smaller of it and of the value
     * the low-temperature branches produced (limpHome for discharge, 0 for
     * charge) */
    MATH_MinimumOfTwoFloats_ExpectAndReturn(
        TEST_SOF_LIMP_HOME_MA, TEST_SOF_MAX_DISCHARGE_MA, TEST_SOF_LIMP_HOME_MA);
    MATH_MinimumOfTwoFloats_ExpectAndReturn(
        TEST_SOF_LIMP_HOME_MA, TEST_SOF_MAX_DISCHARGE_MA, TEST_SOF_LIMP_HOME_MA);
    MATH_MinimumOfTwoFloats_ExpectAndReturn(0.0f, TEST_SOF_MAX_CHARGE_MA, 0.0f);
    MATH_MinimumOfTwoFloats_ExpectAndReturn(0.0f, TEST_SOF_MAX_CHARGE_MA, 0.0f);

    /* sof_trapezoid.c:250 and :267 both use <=, so the boundary value takes
     * this branch for both directions */
    TEST_SOF_CalculateTemperatureBasedCurrentLimit(
        TEST_SOF_LIMIT_LOW_TEMP_DIS_ddC, 0, &allowed, &sof_recommendedCurrent, &curve);
    TEST_ASSERT_EQUAL_FLOAT(TEST_SOF_LIMP_HOME_MA, allowed.continuousDischargeCurrent_mA);
    TEST_ASSERT_EQUAL_FLOAT(TEST_SOF_LIMP_HOME_MA, allowed.peakDischargeCurrent_mA);
    TEST_ASSERT_EQUAL_FLOAT(0.0f, allowed.continuousChargeCurrent_mA);
    TEST_ASSERT_EQUAL_FLOAT(0.0f, allowed.peakChargeCurrent_mA);
}

/** @brief   between the low limit and the low cutoff the discharge current
 *          follows the curve
 * @details sof_trapezoid.c:254-259. The curve reaches limpHomeCurrent_mA at
 *          the low cutoff and 0 at the low limit, so the value at the low limit
 *          plus one tenth of the span is 20000 * 0.9.
 */
void testSOFTemperatureBetweenLowLimitAndCutoffDeratesDischarge(void) {
    SOF_CURVE_s          curve   = {0};
    SOF_CURRENT_LIMITS_s allowed = {0};
    TEST_SOF_CalculateCurves(&sof_recommendedCurrent, &curve);

    /* the high-temperature branches make four product-minimum calls, see the
     * previous test; here the low-temperature side produced 35000 for discharge
     * and 17000 for charge */
    MATH_MinimumOfTwoFloats_ExpectAndReturn(35000.0f, TEST_SOF_MAX_DISCHARGE_MA, 35000.0f);
    MATH_MinimumOfTwoFloats_ExpectAndReturn(35000.0f, TEST_SOF_MAX_DISCHARGE_MA, 35000.0f);
    MATH_MinimumOfTwoFloats_ExpectAndReturn(17000.0f, TEST_SOF_MAX_CHARGE_MA, 17000.0f);
    MATH_MinimumOfTwoFloats_ExpectAndReturn(17000.0f, TEST_SOF_MAX_CHARGE_MA, 17000.0f);

    /* -190 ddegC is one tenth of the way from limitLowTemperatureDischarge_ddegC
     * (-200) to cutoffLowTemperatureDischarge_ddegC (-100), so the line runs
     * from limpHomeCurrent_mA (20000) to the maximum discharge current (170000)
     * and gives 20000 + 0.1 * 150000 = 35000 there */
    TEST_SOF_CalculateTemperatureBasedCurrentLimit(
        (int16_t)(TEST_SOF_LIMIT_LOW_TEMP_DIS_ddC + 10), 0, &allowed, &sof_recommendedCurrent, &curve);
    TEST_ASSERT_FLOAT_WITHIN(1.0f, 35000.0f, allowed.continuousDischargeCurrent_mA);
    TEST_ASSERT_EQUAL_FLOAT(allowed.continuousDischargeCurrent_mA, allowed.peakDischargeCurrent_mA);
}

/** @brief   a cell temperature at or above the high limit forbids both
 *          directions
 * @details sof_trapezoid.c:283-285 for the discharge side and :307-309 for
 *          the charge side.
 */
void testSOFTemperatureAtOrAboveTheHighLimitForbidsBothDirections(void) {
    SOF_CURVE_s          curve   = {0};
    SOF_CURRENT_LIMITS_s allowed = {0};
    TEST_SOF_CalculateCurves(&sof_recommendedCurrent, &curve);

    /* 550 ddegC is limitHighTemperatureDischarge_ddegC, so it is at or above
     * the discharge limit (:283 uses >=) AND at or above the charge limit of
     * 450 (:307 uses >=). Both branches therefore take their zero case, and
     * neither of them calls the product minimum. */
    TEST_SOF_CalculateTemperatureBasedCurrentLimit(
        0, TEST_SOF_LIMIT_HIGH_TEMP_DIS_ddC, &allowed, &sof_recommendedCurrent, &curve);
    TEST_ASSERT_EQUAL_FLOAT(0.0f, allowed.continuousDischargeCurrent_mA);
    TEST_ASSERT_EQUAL_FLOAT(0.0f, allowed.peakDischargeCurrent_mA);
    TEST_ASSERT_EQUAL_FLOAT(0.0f, allowed.continuousChargeCurrent_mA);
    TEST_ASSERT_EQUAL_FLOAT(0.0f, allowed.peakChargeCurrent_mA);
}

/** @brief   the high-temperature discharge derating is combined with the
 *          low-temperature one by taking the smaller value
 * @details sof_trapezoid.c:300-305 calls MATH_MinimumOfTwoFloats() on the
 *          value the minimum temperature produced and the value the maximum
 *          temperature produced. This requires the product minimum twice and
 *          checks that the smaller of the two is what is stored.
 */
void testSOFTemperatureHighDischargeDeratingIsTheSmallerOfTheTwo(void) {
    SOF_CURVE_s          curve   = {0};
    SOF_CURRENT_LIMITS_s allowed = {0};
    TEST_SOF_CalculateCurves(&sof_recommendedCurrent, &curve);

    /* a minimum temperature far enough above the low cutoff that the
     * low-temperature branch yields the full discharge current
     * (sof_trapezoid.c:260-263), and a maximum temperature inside the
     * high-temperature derating band, i.e. at or above
     * cutoffHighTemperatureDischarge_ddegC (450) and below
     * limitHighTemperatureDischarge_ddegC (550), so that :287-:291 runs */
    const int16_t  maxTemperature = (int16_t)(TEST_SOF_CUTOFF_HIGH_TEMP_DIS_ddC + 50);
    const float_t  fromLow        = TEST_SOF_MAX_DISCHARGE_MA;
    const float_t  fromHigh = (curve.slopeHighTemperatureDischarge * (float_t)maxTemperature) +
                       curve.offsetHighTemperatureDischarge;
    /* the high-temperature value is the smaller one here, so the product
     * minimum must return it */
    TEST_ASSERT_TRUE(fromHigh < fromLow);
    /* sof_trapezoid.c:300-305, called once for the continuous and once for the
     * peak current (:300, :303) */
    MATH_MinimumOfTwoFloats_ExpectAndReturn(fromLow, fromHigh, fromHigh);
    MATH_MinimumOfTwoFloats_ExpectAndReturn(fromLow, fromHigh, fromHigh);

    TEST_SOF_CalculateTemperatureBasedCurrentLimit(
        0, maxTemperature, &allowed, &sof_recommendedCurrent, &curve);
    TEST_ASSERT_EQUAL_FLOAT(fromHigh, allowed.continuousDischargeCurrent_mA);
    TEST_ASSERT_EQUAL_FLOAT(fromHigh, allowed.peakDischargeCurrent_mA);
}

/** @brief   the temperature derating rejects NULL results, NULL configuration
 *          and NULL curve
 * @details the three guards at sof_trapezoid.c:243, :244 and :245.
 */
void testSOFTemperatureBasedCurrentLimitRejectsNullPointers(void) {
    SOF_CURVE_s          curve   = {0};
    SOF_CURRENT_LIMITS_s allowed = {0};
    /* sof_trapezoid.c:243 */
    TEST_ASSERT_FAIL_ASSERT(TEST_SOF_CalculateTemperatureBasedCurrentLimit(
        0, 0, NULL_PTR, &sof_recommendedCurrent, &curve));
    /* sof_trapezoid.c:244 */
    TEST_ASSERT_FAIL_ASSERT(
        TEST_SOF_CalculateTemperatureBasedCurrentLimit(0, 0, &allowed, NULL_PTR, &curve));
    /* sof_trapezoid.c:245 */
    TEST_ASSERT_FAIL_ASSERT(
        TEST_SOF_CalculateTemperatureBasedCurrentLimit(0, 0, &allowed, &sof_recommendedCurrent, NULL_PTR));
}

/** @brief   the combined limit is the smaller value in each of the four fields
 * @details sof_trapezoid.c:338-345 takes the minimum of the voltage-based and
 *          the temperature-based value of each of the four current limits, one
 *          pair at a time, in this order: continuous charge, peak charge,
 *          continuous discharge, peak discharge.
 */
void testSOFMinimumOfTwoSofValuesTakesTheSmallerOfEachPair(void) {
    SOF_CURRENT_LIMITS_s voltageBased = {11.0f, 22.0f, 33.0f, 44.0f};
    SOF_CURRENT_LIMITS_s temperatureBased = {110.0f, 220.0f, 330.0f, 440.0f};

    /* sof_trapezoid.c:338-339 */
    MATH_MinimumOfTwoFloats_ExpectAndReturn(11.0f, 110.0f, 11.0f);
    /* sof_trapezoid.c:340-341 */
    MATH_MinimumOfTwoFloats_ExpectAndReturn(22.0f, 220.0f, 22.0f);
    /* sof_trapezoid.c:342-343 */
    MATH_MinimumOfTwoFloats_ExpectAndReturn(33.0f, 330.0f, 33.0f);
    /* sof_trapezoid.c:344-345 */
    MATH_MinimumOfTwoFloats_ExpectAndReturn(44.0f, 440.0f, 44.0f);

    const SOF_CURRENT_LIMITS_s result = TEST_SOF_MinimumOfTwoSofValues(voltageBased, temperatureBased);
    TEST_ASSERT_EQUAL_FLOAT(11.0f, result.continuousChargeCurrent_mA);
    TEST_ASSERT_EQUAL_FLOAT(22.0f, result.peakChargeCurrent_mA);
    TEST_ASSERT_EQUAL_FLOAT(33.0f, result.continuousDischargeCurrent_mA);
    TEST_ASSERT_EQUAL_FLOAT(44.0f, result.peakDischargeCurrent_mA);
}

/** @brief   the temperature-based value wins whenever it is the smaller one
 * @details the mirror of the previous case, so that the choice is shown not to
 *          be a fixed preference for one of the two inputs.
 */
void testSOFMinimumOfTwoSofValuesTakesTheTemperatureValueWhenItIsSmaller(void) {
    SOF_CURRENT_LIMITS_s voltageBased      = {110.0f, 220.0f, 330.0f, 440.0f};
    SOF_CURRENT_LIMITS_s temperatureBased = {11.0f, 22.0f, 33.0f, 44.0f};

    MATH_MinimumOfTwoFloats_ExpectAndReturn(110.0f, 11.0f, 11.0f);
    MATH_MinimumOfTwoFloats_ExpectAndReturn(220.0f, 22.0f, 22.0f);
    MATH_MinimumOfTwoFloats_ExpectAndReturn(330.0f, 33.0f, 33.0f);
    MATH_MinimumOfTwoFloats_ExpectAndReturn(440.0f, 44.0f, 44.0f);

    const SOF_CURRENT_LIMITS_s result = TEST_SOF_MinimumOfTwoSofValues(voltageBased, temperatureBased);
    TEST_ASSERT_EQUAL_FLOAT(11.0f, result.continuousChargeCurrent_mA);
    TEST_ASSERT_EQUAL_FLOAT(22.0f, result.peakChargeCurrent_mA);
    TEST_ASSERT_EQUAL_FLOAT(33.0f, result.continuousDischargeCurrent_mA);
    TEST_ASSERT_EQUAL_FLOAT(44.0f, result.peakDischargeCurrent_mA);
}

/** @brief   SOF_Calculation() reads the minimum/maximum block once and writes
 *          the SOF block once
 * @details sof_trapezoid.c:358 reads the table and :433 writes it.
 */
void testSOFCalculationReadsAndWritesTheDatabaseExactlyOnce(void) {
    /* a cell voltage of 2000 mV is above cutoffLowerCellVoltage_mV and below
     * cutoffUpperCellVoltage_mV, and cell temperatures of 0 and 1000 ddegC are
     * above both low cutoffs and above limitHighTemperatureDischarge_ddegC, so
     * none of the derating branches is reached. The combination helper
     * sof_trapezoid.c:338-345 still calls the product minimum once per field,
     * and the high temperature makes the temperature-based value 0 in all four
     * (sof_trapezoid.c:284-285, :308-309), so the smaller value is 0 each time. */
    test_sofMinMax.minimumCellVoltage_mV[0]    = 2000;
    test_sofMinMax.maximumCellVoltage_mV[0]    = 2000;
    test_sofMinMax.minimumTemperature_ddegC[0]  = 0;
    test_sofMinMax.maximumTemperature_ddegC[0]  = 1000;
    test_sofExpectDatabaseRead();
    BMS_IsStringClosed_ExpectAndReturn(0u, true);
    /* sof_trapezoid.c:338-345, once per field, voltage first */
    MATH_MinimumOfTwoFloats_ExpectAndReturn(TEST_SOF_MAX_CHARGE_MA, 0.0f, 0.0f);
    MATH_MinimumOfTwoFloats_ExpectAndReturn(TEST_SOF_MAX_CHARGE_MA, 0.0f, 0.0f);
    MATH_MinimumOfTwoFloats_ExpectAndReturn(TEST_SOF_MAX_DISCHARGE_MA, 0.0f, 0.0f);
    MATH_MinimumOfTwoFloats_ExpectAndReturn(TEST_SOF_MAX_DISCHARGE_MA, 0.0f, 0.0f);
    BMS_IsTransitionToErrorStateActive_ExpectAndReturn(false);
    test_sofExpectDatabaseWrite();

    SOF_Calculation();

    TEST_ASSERT_EQUAL_UINT32(1u, test_sofReadCount);
    TEST_ASSERT_EQUAL_UINT32(1u, test_sofWriteCount);
}

/** @brief   a string the BMS reports as open is published with all four
 *          per-string currents at zero
 * @details sof_trapezoid.c:402-407 writes 0.0f into all four per-string
 *          entries for an open string. BS_NR_OF_STRINGS is 1
 *          (src/app/application/config/battery_system_cfg.h:109), so the single
 *          string is the open one.
 */
void testSOFCalculationPublishesZeroForAnOpenString(void) {
    /* a cell in the middle of both voltage windows and both temperature
     * windows would otherwise be published with the full currents, so a zero
     * here can only come from the open-string branch */
    test_sofMinMax.minimumCellVoltage_mV[0]    = 2000;
    test_sofMinMax.maximumCellVoltage_mV[0]    = 2000;
    test_sofMinMax.minimumTemperature_ddegC[0]  = 0;
    test_sofMinMax.maximumTemperature_ddegC[0]  = 0;

    test_sofExpectDatabaseRead();
    BMS_IsStringClosed_ExpectAndReturn(0u, false);
    BMS_IsTransitionToErrorStateActive_ExpectAndReturn(false);
    test_sofExpectDatabaseWrite();

    SOF_Calculation();

    /* sof_trapezoid.c:403-406 */
    TEST_ASSERT_EQUAL_FLOAT(0.0f, test_sofPublished.recommendedContinuousChargeCurrent_mA[0]);
    TEST_ASSERT_EQUAL_FLOAT(0.0f, test_sofPublished.recommendedPeakChargeCurrent_mA[0]);
    TEST_ASSERT_EQUAL_FLOAT(0.0f, test_sofPublished.recommendedContinuousDischargeCurrent_mA[0]);
    TEST_ASSERT_EQUAL_FLOAT(0.0f, test_sofPublished.recommendedPeakDischargeCurrent_mA[0]);
    /* sof_trapezoid.c:410-415: with no closed string the running minimum is
     * still FLT_MAX, so the clamp at :410-412 puts the string current at
     * BS_MAXIMUM_STRING_CURRENT_mA; sof_trapezoid.c:418-421 multiplies it by
     * the number of closed strings, which is 0 */
    TEST_ASSERT_EQUAL_FLOAT(0.0f, test_sofPublished.recommendedContinuousPackChargeCurrent_mA);
    TEST_ASSERT_EQUAL_FLOAT(0.0f, test_sofPublished.recommendedPeakPackChargeCurrent_mA);
    TEST_ASSERT_EQUAL_FLOAT(0.0f, test_sofPublished.recommendedContinuousPackDischargeCurrent_mA);
    TEST_ASSERT_EQUAL_FLOAT(0.0f, test_sofPublished.recommendedPeakPackDischargeCurrent_mA);
}

/** @brief   a closed string inside both voltage and both temperature windows
 *          is published with the configured maximum currents
 * @details the four helpers all take their "full current" branch for a cell
 *          voltage of 2000 mV and a cell temperature of 0 ddegC:
 *          sof_trapezoid.c:215-216 (discharge), :230-231 (charge),
 *          :261-262 (low-temperature discharge), :278-279 (low-temperature
 *          charge); the high-temperature branches add no smaller value because
 *          the maximum temperature of 0 ddegC is below both high cutoffs
 *          (:287-295 and :311-319, the else sides that set the full current).
 */
void testSOFCalculationPublishesTheMaximumCurrentsInsideTheAllowedWindow(void) {
    test_sofMinMax.minimumCellVoltage_mV[0]   = 2000;
    test_sofMinMax.maximumCellVoltage_mV[0]   = 2000;
    test_sofMinMax.minimumTemperature_ddegC[0] = 0;
    test_sofMinMax.maximumTemperature_ddegC[0] = 0;

    test_sofExpectDatabaseRead();
    BMS_IsStringClosed_ExpectAndReturn(0u, true);
    /* the high-temperature discharge branch calls the product minimum once for
     * the continuous and once for the peak current (sof_trapezoid.c:300, :303),
     * and the high-temperature charge branch once more each (:324, :327) */
    MATH_MinimumOfTwoFloats_ExpectAndReturn(TEST_SOF_MAX_DISCHARGE_MA, TEST_SOF_MAX_DISCHARGE_MA, TEST_SOF_MAX_DISCHARGE_MA);
    MATH_MinimumOfTwoFloats_ExpectAndReturn(TEST_SOF_MAX_DISCHARGE_MA, TEST_SOF_MAX_DISCHARGE_MA, TEST_SOF_MAX_DISCHARGE_MA);
    MATH_MinimumOfTwoFloats_ExpectAndReturn(TEST_SOF_MAX_CHARGE_MA, TEST_SOF_MAX_CHARGE_MA, TEST_SOF_MAX_CHARGE_MA);
    MATH_MinimumOfTwoFloats_ExpectAndReturn(TEST_SOF_MAX_CHARGE_MA, TEST_SOF_MAX_CHARGE_MA, TEST_SOF_MAX_CHARGE_MA);
    /* the combination of the two sets (sof_trapezoid.c:338-345) */
    MATH_MinimumOfTwoFloats_ExpectAndReturn(TEST_SOF_MAX_CHARGE_MA, TEST_SOF_MAX_CHARGE_MA, TEST_SOF_MAX_CHARGE_MA);
    MATH_MinimumOfTwoFloats_ExpectAndReturn(TEST_SOF_MAX_CHARGE_MA, TEST_SOF_MAX_CHARGE_MA, TEST_SOF_MAX_CHARGE_MA);
    MATH_MinimumOfTwoFloats_ExpectAndReturn(TEST_SOF_MAX_DISCHARGE_MA, TEST_SOF_MAX_DISCHARGE_MA, TEST_SOF_MAX_DISCHARGE_MA);
    MATH_MinimumOfTwoFloats_ExpectAndReturn(TEST_SOF_MAX_DISCHARGE_MA, TEST_SOF_MAX_DISCHARGE_MA, TEST_SOF_MAX_DISCHARGE_MA);
    BMS_IsTransitionToErrorStateActive_ExpectAndReturn(false);
    test_sofExpectDatabaseWrite();

    SOF_Calculation();

    /* sof_trapezoid.c:389-393 */
    TEST_ASSERT_EQUAL_FLOAT(TEST_SOF_MAX_CHARGE_MA, test_sofPublished.recommendedContinuousChargeCurrent_mA[0]);
    TEST_ASSERT_EQUAL_FLOAT(TEST_SOF_MAX_CHARGE_MA, test_sofPublished.recommendedPeakChargeCurrent_mA[0]);
    TEST_ASSERT_EQUAL_FLOAT(
        TEST_SOF_MAX_DISCHARGE_MA, test_sofPublished.recommendedContinuousDischargeCurrent_mA[0]);
    TEST_ASSERT_EQUAL_FLOAT(TEST_SOF_MAX_DISCHARGE_MA, test_sofPublished.recommendedPeakDischargeCurrent_mA[0]);

    /* sof_trapezoid.c:367-368 initialises the running minimum to FLT_MAX and
     * :410-415 clamps it to BS_MAXIMUM_STRING_CURRENT_mA. In a unit-test build
     * that macro comes from tests/unit/app/application/config/
     * battery_system_cfg_unit_test.h:230, which src/app/application/config/
     * battery_system_cfg.h:342 includes under UNITY_UNIT_TEST, and it is 10000
     * there, not the 2400 of battery_system_cfg.h:198. sof_trapezoid.c:418-:421
     * then multiplies the clamp by the single closed string. */
    TEST_ASSERT_EQUAL_FLOAT(10000.0f, test_sofPublished.recommendedContinuousPackChargeCurrent_mA);
    TEST_ASSERT_EQUAL_FLOAT(10000.0f, test_sofPublished.recommendedPeakPackChargeCurrent_mA);
    TEST_ASSERT_EQUAL_FLOAT(10000.0f, test_sofPublished.recommendedContinuousPackDischargeCurrent_mA);
    TEST_ASSERT_EQUAL_FLOAT(10000.0f, test_sofPublished.recommendedPeakPackDischargeCurrent_mA);
}

/** @brief   a transition into the BMS error state zeroes the pack currents
 * @details sof_trapezoid.c:426-431 overwrites all four pack currents with 0.0f
 *          when BMS_IsTransitionToErrorStateActive() is true, after the per
 *          string values have already been written at :389-393.
 */
void testSOFCalculationZeroesThePackCurrentsWhileTransitioningToTheErrorState(void) {
    test_sofMinMax.minimumCellVoltage_mV[0]   = 2000;
    test_sofMinMax.maximumCellVoltage_mV[0]   = 2000;
    test_sofMinMax.minimumTemperature_ddegC[0] = 0;
    test_sofMinMax.maximumTemperature_ddegC[0] = 0;

    test_sofExpectDatabaseRead();
    BMS_IsStringClosed_ExpectAndReturn(0u, true);
    MATH_MinimumOfTwoFloats_ExpectAndReturn(TEST_SOF_MAX_DISCHARGE_MA, TEST_SOF_MAX_DISCHARGE_MA, TEST_SOF_MAX_DISCHARGE_MA);
    MATH_MinimumOfTwoFloats_ExpectAndReturn(TEST_SOF_MAX_DISCHARGE_MA, TEST_SOF_MAX_DISCHARGE_MA, TEST_SOF_MAX_DISCHARGE_MA);
    MATH_MinimumOfTwoFloats_ExpectAndReturn(TEST_SOF_MAX_CHARGE_MA, TEST_SOF_MAX_CHARGE_MA, TEST_SOF_MAX_CHARGE_MA);
    MATH_MinimumOfTwoFloats_ExpectAndReturn(TEST_SOF_MAX_CHARGE_MA, TEST_SOF_MAX_CHARGE_MA, TEST_SOF_MAX_CHARGE_MA);
    MATH_MinimumOfTwoFloats_ExpectAndReturn(TEST_SOF_MAX_CHARGE_MA, TEST_SOF_MAX_CHARGE_MA, TEST_SOF_MAX_CHARGE_MA);
    MATH_MinimumOfTwoFloats_ExpectAndReturn(TEST_SOF_MAX_CHARGE_MA, TEST_SOF_MAX_CHARGE_MA, TEST_SOF_MAX_CHARGE_MA);
    MATH_MinimumOfTwoFloats_ExpectAndReturn(TEST_SOF_MAX_DISCHARGE_MA, TEST_SOF_MAX_DISCHARGE_MA, TEST_SOF_MAX_DISCHARGE_MA);
    MATH_MinimumOfTwoFloats_ExpectAndReturn(TEST_SOF_MAX_DISCHARGE_MA, TEST_SOF_MAX_DISCHARGE_MA, TEST_SOF_MAX_DISCHARGE_MA);
    /* sof_trapezoid.c:426, the state machine reports the transition */
    BMS_IsTransitionToErrorStateActive_ExpectAndReturn(true);
    test_sofExpectDatabaseWrite();

    SOF_Calculation();

    /* sof_trapezoid.c:427-430 */
    TEST_ASSERT_EQUAL_FLOAT(0.0f, test_sofPublished.recommendedContinuousPackChargeCurrent_mA);
    TEST_ASSERT_EQUAL_FLOAT(0.0f, test_sofPublished.recommendedContinuousPackDischargeCurrent_mA);
    TEST_ASSERT_EQUAL_FLOAT(0.0f, test_sofPublished.recommendedPeakPackChargeCurrent_mA);
    TEST_ASSERT_EQUAL_FLOAT(0.0f, test_sofPublished.recommendedPeakPackDischargeCurrent_mA);
    /* the per-string values were written before the overwrite (sof_trapezoid.c:389-393) */
    TEST_ASSERT_EQUAL_FLOAT(TEST_SOF_MAX_CHARGE_MA, test_sofPublished.recommendedContinuousChargeCurrent_mA[0]);
}

/** @brief   SOF_Init() computes the curve of the recommended operating current
 * @details sof_trapezoid.c:350-353 is the only statement of SOF_Init(): it
 *          builds sof_curveRecommendedOperatingCurrent from
 *          sof_recommendedCurrent. The curve is not readable from outside, so
 *          what is asserted is the observable consequence - SOF_Init() must
 *          reach SOF_CalculateCurves(), which the following test pins - and
 *          that the function has no other effect on the database.
 */
void testSOFInitDoesNotTouchTheDatabase(void) {
    SOF_Init();
    TEST_ASSERT_EQUAL_UINT32(0u, test_sofReadCount);
    TEST_ASSERT_EQUAL_UINT32(0u, test_sofWriteCount);
}


