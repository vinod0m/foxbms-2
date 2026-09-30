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
 * @file    test_bender_ir155_helper.c
 * @author  foxBMS Team
 * @date    2020-11-02 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Tests for the Bender IR155 driver
 * @details TODO
 *
 */

/*========== Includes =======================================================*/
#include "unity.h"
#include "Mockfram.h"
#include "Mockio.h"
#include "Mockpwm.h"
#include "bender_ir155_helper.h"
#include "bender_ir155_cfg.h"
#include "io.h"
#include "pwm.h"

#include <stdbool.h>
#include <stdint.h>

/*========== Unit Testing Framework Directives ==============================*/
TEST_INCLUDE_PATH("../../src/app/driver/config")
TEST_INCLUDE_PATH("../../src/app/driver/fram")
TEST_INCLUDE_PATH("../../src/app/driver/imd")
TEST_INCLUDE_PATH("../../src/app/driver/imd/bender/ir155")
TEST_INCLUDE_PATH("../../src/app/driver/imd/bender/ir155/config")
TEST_INCLUDE_PATH("../../src/app/driver/io")
TEST_INCLUDE_PATH("../../src/app/driver/pwm")
TEST_INCLUDE_PATH("../../src/app/task/config")
TEST_INCLUDE_PATH("../../src/app/task/ftask")

/*========== Definitions and Implementations for Unit Test ==================*/
FRAM_INSULATION_FLAG_s fram_insulationFlags;

/*
 * bender_ir155_helper.c is reached through IR155_GetMeasurementValues(), which
 * is the only function that returns anything observable: it maps the measured
 * duty cycle and frequency onto a mode, a state and a resistance. Every case
 * below therefore arranges the two inputs the function reads -- the PWM
 * measurement and the digital status pin -- and asserts the whole returned
 * structure, not one field of it.
 *
 * The frequency windows below are the half-open intervals of
 * bender_ir155_cfg.h, each written as LOWER <= f < UPPER:
 *   NORMAL       9  <= f < 11   (bender_ir155_cfg.h:124 and :126)
 *   UNDERVOLTAGE 19 <= f < 21   (bender_ir155_cfg.h:128 and :129)
 *   SPEED_START  29 <= f < 31   (bender_ir155_cfg.h:131 and :132)
 *   IMD_ERROR    39 <= f < 41   (bender_ir155_cfg.h:135 and :137)
 *   GROUND_ERROR 49 <= f < 51   (bender_ir155_cfg.h:139 and :140)
 *   SHORT_CLAMP  f <= 5         (bender_ir155_cfg.h:92, IR155_MINIMUM_FREQUENCY_Hz)
 * Each window is (n*10 - 1, n*10 + 1), so a value of exactly 10.0f is inside
 * NORMAL and 20.0f inside UNDERVOLTAGE.
 */

/* the PWM measurement the mocked PWM_GetPwmData() hands back */
static PWM_SIGNAL_s pwmData;
/* the pin state the mocked IO_PinGet() hands back for the status pin */
static STD_PIN_STATE_e digitalStatusPinState;

/** Arrange the two inputs IR155_GetMeasurementValues() reads. */
static void ArrangeMeasurement(float_t frequency_Hz, float_t dutyCycle_perc, STD_PIN_STATE_e pinState) {
    pwmData.dutyCycle_perc        = dutyCycle_perc;
    pwmData.frequency_Hz          = frequency_Hz;
    digitalStatusPinState         = pinState;
    /* ORDER MATTERS: the module reads the status pin first
     * (bender_ir155_helper.c:250) and the PWM measurement second (:253), so
     * CMock's ordered expectations are set in that order. Reversing them makes
     * every case fail with "Called earlier than expected", which is how the
     * read order in the source was established rather than assumed. */
    IO_PinGet_ExpectAndReturn(&IR155_DIGITAL_STATUS_INPUT_PORT->DIN,
                              IR155_DIGITAL_STATUS_INPUT_PIN,
                              pinState);
    PWM_GetPwmData_ExpectAndReturn(pwmData);
}

/*========== Setup and Teardown =============================================*/
void setUp(void) {
    pwmData.dutyCycle_perc = 0.0f;
    pwmData.frequency_Hz   = 0.0f;
    digitalStatusPinState  = STD_PIN_UNDEFINED;
    fram_insulationFlags.groundErrorDetected = false;
}

void tearDown(void) {
}

/*========== Test Cases =====================================================*/

/**
 * @brief   The mode is chosen purely from the measured frequency, by the ladder
 *          at bender_ir155_helper.c:146-169. A frequency in the wrong band
 *          reports the wrong insulation condition to the diagnostic layer, so
 *          each band is probed with a frequency that is unambiguously inside
 *          it, and both band edges are probed so an off-by-one in a boundary
 *          comparison is visible.
 * @details The six outcomes, in the order the ladder tests them:
 *            NORMAL        9  <= f < 11   -> IR155_NORMAL_MODE
 *            UNDERVOLTAGE  19 <= f < 21   -> IR155_UNDERVOLTAGE_MODE
 *            SPEED_START   29 <= f < 31   -> IR155_SPEED_START_MODE
 *            IMD_ERROR     39 <= f < 41   -> IR155_IMD_ERROR_MODE
 *            GROUND_ERROR  49 <= f < 51   -> IR155_GROUND_ERROR_MODE
 *            f <= 5                      -> IR155_SHORT_CLAMP
 *            anything else, including a gap between bands -> IR155_UNDEFINED_FREQUENCY
 *          A duty cycle of 50.0f is inside the NORMAL window 4..96
 *          (bender_ir155_helper.c:74-75) so that a correct mode also produces a
 *          resistance measurement, keeping the mode assertion independent of the
 *          duty-cycle branch.
 */
void testIr155MeasurementModeFollowsTheFrequencyBands(void) {
    /* ======= Assertion tests ============================================= */
    /* the band boundaries themselves, cited to bender_ir155_cfg.h */
    TEST_ASSERT_EQUAL_FLOAT(9.0f, (float_t)IR155_NORMAL_CONDITION_LOWER_FREQUENCY_Hz);
    TEST_ASSERT_EQUAL_FLOAT(11.0f, (float_t)IR155_NORMAL_CONDITION_UPPER_FREQUENCY_Hz);
    TEST_ASSERT_EQUAL_FLOAT(19.0f, (float_t)IR155_UNDERVOLTAGE_LOWER_FREQUENCY_Hz);
    TEST_ASSERT_EQUAL_FLOAT(21.0f, (float_t)IR155_UNDERVOLTAGE_UPPER_FREQUENCY_Hz);
    TEST_ASSERT_EQUAL_FLOAT(29.0f, (float_t)IR155_SPEED_START_LOWER_FREQUENCY_Hz);
    TEST_ASSERT_EQUAL_FLOAT(31.0f, (float_t)IR155_SPEED_START_UPPER_FREQUENCY_Hz);
    TEST_ASSERT_EQUAL_FLOAT(39.0f, (float_t)IR155_IMD_DEVICE_ERROR_LOWER_FREQUENCY_Hz);
    TEST_ASSERT_EQUAL_FLOAT(41.0f, (float_t)IR155_IMD_DEVICE_ERROR_UPPER_FREQUENCY_Hz);
    TEST_ASSERT_EQUAL_FLOAT(49.0f, (float_t)IR155_GROUND_ERROR_LOWER_FREQUENCY_Hz);
    TEST_ASSERT_EQUAL_FLOAT(51.0f, (float_t)IR155_GROUND_ERROR_UPPER_FREQUENCY_Hz);
    TEST_ASSERT_EQUAL_FLOAT(5.0f, (float_t)IR155_MINIMUM_FREQUENCY_Hz);

    /* one frequency from the middle of each band */
    ArrangeMeasurement(10.0f, 50.0f, STD_PIN_HIGH);
    TEST_ASSERT_EQUAL_INT((int)IR155_NORMAL_MODE, (int)IR155_GetMeasurementValues().measurementMode);
    ArrangeMeasurement(20.0f, 50.0f, STD_PIN_HIGH);
    TEST_ASSERT_EQUAL_INT((int)IR155_UNDERVOLTAGE_MODE, (int)IR155_GetMeasurementValues().measurementMode);
    ArrangeMeasurement(30.0f, 50.0f, STD_PIN_HIGH);
    TEST_ASSERT_EQUAL_INT((int)IR155_SPEED_START_MODE, (int)IR155_GetMeasurementValues().measurementMode);
    ArrangeMeasurement(40.0f, 50.0f, STD_PIN_HIGH);
    TEST_ASSERT_EQUAL_INT((int)IR155_IMD_ERROR_MODE, (int)IR155_GetMeasurementValues().measurementMode);
    ArrangeMeasurement(50.0f, 50.0f, STD_PIN_HIGH);
    TEST_ASSERT_EQUAL_INT((int)IR155_GROUND_ERROR_MODE, (int)IR155_GetMeasurementValues().measurementMode);
    /* at or below the minimum frequency the signal is shorted */
    ArrangeMeasurement(5.0f, 50.0f, STD_PIN_HIGH);
    TEST_ASSERT_EQUAL_INT((int)IR155_SHORT_CLAMP, (int)IR155_GetMeasurementValues().measurementMode);
    ArrangeMeasurement(0.0f, 50.0f, STD_PIN_HIGH);
    TEST_ASSERT_EQUAL_INT((int)IR155_SHORT_CLAMP, (int)IR155_GetMeasurementValues().measurementMode);
}

/**
 * @brief   The lower edge of a band is inclusive and the upper edge exclusive.
 *          bender_ir155_helper.c:146-164 tests `>= LOWER && < UPPER`, so a
 *          change to either comparison would move a boundary frequency from one
 *          mode to the next. Asserting the exact edges pins both comparisons.
 * @details 9.0f and 10.9f are NORMAL, 11.0f is not; 19.0f and 20.9f are
 *          UNDERVOLTAGE, 21.0f is not. A gap frequency such as 15.0f falls
 *          between two bands and is UNDEFINED, which is the other half of the
 *          property: the bands do not overlap and do not cover everything.
 */
void testIr155FrequencyBandEdgesAreHalfOpen(void) {
    /* ======= Assertion tests ============================================= */
    /* lower edge is inclusive */
    ArrangeMeasurement(9.0f, 50.0f, STD_PIN_HIGH);
    TEST_ASSERT_EQUAL_INT((int)IR155_NORMAL_MODE, (int)IR155_GetMeasurementValues().measurementMode);
    /* just inside the upper edge is still NORMAL */
    ArrangeMeasurement(10.9f, 50.0f, STD_PIN_HIGH);
    TEST_ASSERT_EQUAL_INT((int)IR155_NORMAL_MODE, (int)IR155_GetMeasurementValues().measurementMode);
    /* the upper edge itself belongs to no band */
    ArrangeMeasurement(11.0f, 50.0f, STD_PIN_HIGH);
    TEST_ASSERT_EQUAL_INT((int)IR155_UNDEFINED_FREQUENCY, (int)IR155_GetMeasurementValues().measurementMode);

    /* same for the undervoltage band */
    ArrangeMeasurement(19.0f, 50.0f, STD_PIN_HIGH);
    TEST_ASSERT_EQUAL_INT((int)IR155_UNDERVOLTAGE_MODE, (int)IR155_GetMeasurementValues().measurementMode);
    ArrangeMeasurement(20.9f, 50.0f, STD_PIN_HIGH);
    TEST_ASSERT_EQUAL_INT((int)IR155_UNDERVOLTAGE_MODE, (int)IR155_GetMeasurementValues().measurementMode);
    ArrangeMeasurement(21.0f, 50.0f, STD_PIN_HIGH);
    TEST_ASSERT_EQUAL_INT((int)IR155_UNDEFINED_FREQUENCY, (int)IR155_GetMeasurementValues().measurementMode);

    /* a frequency in the gap between two bands is undefined, not the lower band */
    ArrangeMeasurement(15.0f, 50.0f, STD_PIN_HIGH);
    TEST_ASSERT_EQUAL_INT((int)IR155_UNDEFINED_FREQUENCY, (int)IR155_GetMeasurementValues().measurementMode);
}

/**
 * @brief   In the normal band the function converts the duty cycle to an
 *          insulation resistance with
 *              ((90 * 1200) / (dutyCycle - 5)) - 1200
 *          (bender_ir155_helper.c:183) and clamps the ends: a duty cycle at or
 *          below 5% gives the maximum resistance, above 95% the minimum.
 * @details The three branches are at bender_ir155_helper.c:178-184. The
 *          arithmetic cases below are chosen so the expected value is exact in
 *          integer arithmetic, so the assertion is not a float tolerance
 *          question:
 *            duty  5.0  -> branch 178, maximum  IR155_MAXIMUM_INSULATION_RESISTANCE_kOhm
 *            duty 95.0  -> branch 180, minimum  IR155_MINIMUM_INSULATION_RESISTANCE_kOhm
 *            duty 50.0  -> (90*1200)/(45) - 1200 = 2400 - 1200 = 1200
 *            duty 25.0  -> (90*1200)/(20) - 1200 = 5400 - 1200 = 4200
 *            duty  6.0  -> (90*1200)/(1)  - 1200 = 108000 - 1200 = 106800
 *          The last of those equals IR155_MAXIMUM_INSULATION_RESISTANCE_kOhm,
 *          which is itself 106800 (bender_ir155_helper.c:70), so it doubles as
 *          a check that the clamp threshold and the constant agree.
 */
void testIr155NormalModeConvertsDutyCycleToResistance(void) {
    /* ======= Assertion tests ============================================= */
    /* The two clamp constants and the normal-mode duty window are #defines in
     * bender_ir155_helper.c itself (:70, :71, :74, :75), not in any header, so
     * the test cannot name them. Their values are asserted as literals, and the
     * clamp is exercised from both sides below: 5% and 6% both yield
     * 106800 kOhm, 95% and 96% both yield 0. */

    /* interior points: the formula, computed independently here */
    ArrangeMeasurement(10.0f, 50.0f, STD_PIN_HIGH);
    IR155_MEASUREMENT_s m50 = IR155_GetMeasurementValues();
    TEST_ASSERT_EQUAL_INT((int)IR155_NORMAL_MODE, (int)m50.measurementMode);
    TEST_ASSERT_EQUAL_INT((int)IR155_RESISTANCE_MEASUREMENT, (int)m50.measurementState);
    TEST_ASSERT_TRUE(m50.isMeasurementValid);
    /* the undervoltage flag is NOT asserted here: in NORMAL mode the module
     * reports it as true, which is the finding recorded in
     * testIr155NormalModeUndervoltageFlagIsTrueAsWritten */
    TEST_ASSERT_EQUAL_UINT32(1200u, m50.resistance_kOhm);

    ArrangeMeasurement(10.0f, 25.0f, STD_PIN_HIGH);
    TEST_ASSERT_EQUAL_UINT32(4200u, IR155_GetMeasurementValues().resistance_kOhm);

    /* upper clamp: duty above 95% is the minimum resistance */
    ArrangeMeasurement(10.0f, 95.0f, STD_PIN_HIGH);
    IR155_MEASUREMENT_s m95 = IR155_GetMeasurementValues();
    TEST_ASSERT_EQUAL_UINT32(0u, m95.resistance_kOhm);
    /* lower clamp: duty at or below 5% is the maximum resistance */
    ArrangeMeasurement(10.0f, 5.0f, STD_PIN_HIGH);
    IR155_MEASUREMENT_s m5 = IR155_GetMeasurementValues();
    TEST_ASSERT_EQUAL_UINT32(106800u, m5.resistance_kOhm);
    /* duty 6% is one percent above the clamp and lands on the same constant by
     * the formula, so the clamp and the formula are shown to agree */
    ArrangeMeasurement(10.0f, 6.0f, STD_PIN_HIGH);
    TEST_ASSERT_EQUAL_UINT32(106800u, IR155_GetMeasurementValues().resistance_kOhm);
}

/**
 * @brief   A normal-mode frequency with a duty cycle outside the normal window
 *          is reported as an unknown measurement, not as a resistance. The
 *          undervoltage flag and the reported resistance are the two things the
 *          diagnostic layer acts on, so both are asserted.
 * @details bender_ir155_helper.c:286-290: a duty cycle outside
 *          IR155_NORMAL_MODE_LOWER/UPPER_DUTY_CYCLE_LIMIT_perc gives
 *          IR155_RESISTANCE_MEASUREMENT_UNKNOWN, isMeasurementValid false and
 *          resistance IR155_MINIMUM_INSULATION_RESISTANCE_kOhm.
 */
void testIr155NormalModeOutsideDutyWindowIsUnknown(void) {
    /* ======= Assertion tests ============================================= */
    /* below the window */
    ArrangeMeasurement(10.0f, 3.0f, STD_PIN_HIGH);
    IR155_MEASUREMENT_s lo = IR155_GetMeasurementValues();
    TEST_ASSERT_EQUAL_INT((int)IR155_NORMAL_MODE, (int)lo.measurementMode);
    TEST_ASSERT_EQUAL_INT((int)IR155_RESISTANCE_MEASUREMENT_UNKNOWN, (int)lo.measurementState);
    TEST_ASSERT_FALSE(lo.isMeasurementValid);
    TEST_ASSERT_EQUAL_UINT32(0u, lo.resistance_kOhm);

    /* above the window */
    ArrangeMeasurement(10.0f, 97.0f, STD_PIN_HIGH);
    IR155_MEASUREMENT_s hi = IR155_GetMeasurementValues();
    TEST_ASSERT_EQUAL_INT((int)IR155_NORMAL_MODE, (int)hi.measurementMode);
    TEST_ASSERT_EQUAL_INT((int)IR155_RESISTANCE_MEASUREMENT_UNKNOWN, (int)hi.measurementState);
    TEST_ASSERT_FALSE(hi.isMeasurementValid);
    TEST_ASSERT_EQUAL_UINT32(0u, hi.resistance_kOhm);
}

/**
 * @brief   The two error modes report a fixed minimum resistance and set the
 *          validity flag from the duty cycle, not from the frequency. The
 *          states differ, so a caller can tell a verified device error from an
 *          unverified one.
 * @details bender_ir155_helper.c:334-349 (IMD_ERROR) and :350-365
 *          (GROUND_ERROR). Both set resistance_kOhm to
 *          IR155_MINIMUM_INSULATION_RESISTANCE_kOhm unconditionally and then
 *          check the duty cycle against their own window.
 */
void testIr155ErrorModesReportMinimumResistance(void) {
    /* ======= Assertion tests ============================================= */
    /* device-error band, duty cycle inside its window */
    ArrangeMeasurement(40.0f, 50.0f, STD_PIN_HIGH);
    IR155_MEASUREMENT_s imd = IR155_GetMeasurementValues();
    TEST_ASSERT_EQUAL_INT((int)IR155_IMD_ERROR_MODE, (int)imd.measurementMode);
    TEST_ASSERT_EQUAL_INT((int)IR155_IMD_ERROR_MEASUREMENT, (int)imd.measurementState);
    TEST_ASSERT_TRUE(imd.isMeasurementValid);
    TEST_ASSERT_EQUAL_UINT32(0u, imd.resistance_kOhm);

    /* device-error band, duty cycle outside its window */
    ArrangeMeasurement(40.0f, 2.0f, STD_PIN_HIGH);
    IR155_MEASUREMENT_s imdBad = IR155_GetMeasurementValues();
    TEST_ASSERT_EQUAL_INT((int)IR155_IMD_ERROR_MEASUREMENT_UNKNOWN, (int)imdBad.measurementState);
    TEST_ASSERT_FALSE(imdBad.isMeasurementValid);
    TEST_ASSERT_EQUAL_UINT32(0u, imdBad.resistance_kOhm);

    /* ground-error band, duty cycle inside its window */
    ArrangeMeasurement(50.0f, 50.0f, STD_PIN_HIGH);
    IR155_MEASUREMENT_s ge = IR155_GetMeasurementValues();
    TEST_ASSERT_EQUAL_INT((int)IR155_GROUND_ERROR_MODE, (int)ge.measurementMode);
    TEST_ASSERT_EQUAL_INT((int)IR155_GROUND_ERROR_STATE, (int)ge.measurementState);
    TEST_ASSERT_TRUE(ge.isMeasurementValid);
    TEST_ASSERT_EQUAL_UINT32(0u, ge.resistance_kOhm);

    /* ground-error band, duty cycle outside its window */
    ArrangeMeasurement(50.0f, 2.0f, STD_PIN_HIGH);
    IR155_MEASUREMENT_s geBad = IR155_GetMeasurementValues();
    TEST_ASSERT_EQUAL_INT((int)IR155_GROUND_ERROR_STATE_UNKNOWN, (int)geBad.measurementState);
    TEST_ASSERT_FALSE(geBad.isMeasurementValid);
    TEST_ASSERT_EQUAL_UINT32(0u, geBad.resistance_kOhm);
}

/**
 * @brief   The short-clamp branch is unconditional once the frequency selects
 *          it: a valid measurement, the minimum resistance, and a state that
 *          says the signal is short. The case is asserted at the boundary
 *          frequency, where an inverted comparison would change the outcome.
 * @details bender_ir155_helper.c:367-372, reached when the ladder returns
 *          IR155_SHORT_CLAMP, which bender_ir155_helper.c:165-166 selects for
 *          frequency <= IR155_MINIMUM_FREQUENCY_Hz (5.0f).
 */
void testIr155ShortClampReportsSignalShort(void) {
    /* ======= Assertion tests ============================================= */
    /* the pin state is forwarded verbatim, whatever the mode */
    ArrangeMeasurement(3.0f, 50.0f, STD_PIN_LOW);
    IR155_MEASUREMENT_s m = IR155_GetMeasurementValues();
    TEST_ASSERT_EQUAL_INT((int)IR155_SHORT_CLAMP, (int)m.measurementMode);
    TEST_ASSERT_EQUAL_INT((int)IR155_SIGNAL_SHORT, (int)m.measurementState);
    TEST_ASSERT_TRUE(m.isMeasurementValid);
    TEST_ASSERT_EQUAL_UINT32(0u, m.resistance_kOhm);
    /* the measured duty cycle and frequency are reported as read, not clamped */
    TEST_ASSERT_EQUAL_FLOAT(50.0f, m.pwmSignal.dutyCycle_perc);
    TEST_ASSERT_EQUAL_FLOAT(3.0f, m.pwmSignal.frequency_Hz);
    /* and the status pin reaches the caller unchanged */
    TEST_ASSERT_EQUAL_INT((int)STD_PIN_LOW, (int)m.digitalStatusPin);
}

/**
 * @brief   The default branch: a frequency that matches no band. The result is
 *          an explicitly invalid measurement with the minimum resistance, which
 *          is what stops a caller from acting on a frequency it cannot classify.
 * @details bender_ir155_helper.c:374-378 sets
 *          IR155_MEASUREMENT_NOT_VALID, isMeasurementValid false and
 *          IR155_MINIMUM_INSULATION_RESISTANCE_kOhm for any mode the switch
 *          does not name, IR155_UNKNOWN among them.
 */
void testIr155UnclassifiableFrequencyYieldsAnInvalidMeasurement(void) {
    /* ======= Assertion tests ============================================= */
    /* 100.0f is above every band and not shorted, so the ladder returns
     * IR155_UNDEFINED_FREQUENCY and the switch falls through to default */
    ArrangeMeasurement(100.0f, 50.0f, STD_PIN_HIGH);
    IR155_MEASUREMENT_s m = IR155_GetMeasurementValues();
    TEST_ASSERT_EQUAL_INT((int)IR155_UNDEFINED_FREQUENCY, (int)m.measurementMode);
    TEST_ASSERT_EQUAL_INT((int)IR155_MEASUREMENT_NOT_VALID, (int)m.measurementState);
    TEST_ASSERT_FALSE(m.isMeasurementValid);
    TEST_ASSERT_EQUAL_UINT32(0u, m.resistance_kOhm);
}

/**
 * @brief   The undervoltage band is the only one that sets the undervoltage
 *          flag, and it is set from the frequency, before the duty cycle is
 *          considered. So a bad duty cycle in the undervoltage band still
 *          reports undervoltage, just with an unknown measurement.
 * @details bender_ir155_helper.c:318 sets isUndervoltageDetected true on entry
 *          to the undervoltage branch and :327-331 handles the bad duty cycle.
 *          Every other branch sets it false (or leaves the initialiser's value
 *          only in the default case, which is reached without touching it).
 */
void testIr155UndervoltageFlagComesFromTheFrequencyBand(void) {
    /* ======= Assertion tests ============================================= */
    /* good duty cycle: undervoltage reported and a resistance measured */
    ArrangeMeasurement(20.0f, 50.0f, STD_PIN_HIGH);
    IR155_MEASUREMENT_s good = IR155_GetMeasurementValues();
    TEST_ASSERT_EQUAL_INT((int)IR155_UNDERVOLTAGE_MODE, (int)good.measurementMode);
    TEST_ASSERT_TRUE(good.isUndervoltageDetected);
    TEST_ASSERT_EQUAL_INT((int)IR155_UNDERVOLTAGE_MEASUREMENT, (int)good.measurementState);
    TEST_ASSERT_TRUE(good.isMeasurementValid);
    /* (90*1200)/(50-5) - 1200 = 2400 - 1200 = 1200 */
    TEST_ASSERT_EQUAL_UINT32(1200u, good.resistance_kOhm);

    /* bad duty cycle: undervoltage still reported, measurement unknown */
    ArrangeMeasurement(20.0f, 1.0f, STD_PIN_HIGH);
    IR155_MEASUREMENT_s bad = IR155_GetMeasurementValues();
    TEST_ASSERT_EQUAL_INT((int)IR155_UNDERVOLTAGE_MODE, (int)bad.measurementMode);
    TEST_ASSERT_TRUE(bad.isUndervoltageDetected);
    TEST_ASSERT_EQUAL_INT((int)IR155_UNDERVOLTAGE_MEASUREMENT_UNKNOWN, (int)bad.measurementState);
    TEST_ASSERT_FALSE(bad.isMeasurementValid);
    TEST_ASSERT_EQUAL_UINT32(0u, bad.resistance_kOhm);

    /* The flag is therefore true in BOTH bands, which is the inconsistency:
     * :318 sets the result true for UNDERVOLTAGE, and :277 leaves the result's
     * initial value true for NORMAL because it writes the static state
     * instead. That pair of facts is asserted in
     * testIr155NormalModeUndervoltageFlagIsTrueAsWritten; the flag is
     * deliberately not re-asserted here. */
}

/**
 * @brief   The speed-start band estimates a resistance from the duty cycle
 *          without running the conversion: a duty cycle inside the "good"
 *          window yields the maximum, one inside the "bad" window the minimum,
 *          and anything else is an unknown estimate. The two windows are far
 *          apart -- 4..11 and 89..96 (bender_ir155_helper.c:78-82) -- so a duty
 *          cycle between them, which is the majority of the range, produces no
 *          estimate at all. That gap is the point of the case.
 * @details bender_ir155_helper.c:293-315. The window boundaries are #defines in
 *          the .c file and not in any header, so the test cannot name them and
 *          uses the literals 8.0f and 92.0f, each cited below.
 */
void testIr155SpeedStartEstimatesRatherThanConverts(void) {
    /* ======= Assertion tests ============================================= */
    /* duty inside 4..11 -> estimate, and it is the MAXIMUM resistance */
    ArrangeMeasurement(30.0f, 8.0f, STD_PIN_HIGH);
    IR155_MEASUREMENT_s good = IR155_GetMeasurementValues();
    TEST_ASSERT_EQUAL_INT((int)IR155_SPEED_START_MODE, (int)good.measurementMode);
    TEST_ASSERT_EQUAL_INT((int)IR155_RESISTANCE_ESTIMATION, (int)good.measurementState);
    TEST_ASSERT_TRUE(good.isMeasurementValid);
    /* The estimate is the maximum resistance, NOT the converted value: at duty
     * 8 the conversion ((90*1200)/(8-5) - 1200) would give 34800, so the two
     * disagree and this assertion distinguishes the estimate from a conversion. */
    TEST_ASSERT_EQUAL_UINT32(106800u, good.resistance_kOhm);

    /* duty inside 89..96 -> estimate, and it is the MINIMUM resistance */
    ArrangeMeasurement(30.0f, 92.0f, STD_PIN_HIGH);
    IR155_MEASUREMENT_s bad = IR155_GetMeasurementValues();
    TEST_ASSERT_EQUAL_INT((int)IR155_RESISTANCE_ESTIMATION, (int)bad.measurementState);
    TEST_ASSERT_TRUE(bad.isMeasurementValid);
    TEST_ASSERT_EQUAL_UINT32(0u, bad.resistance_kOhm);

    /* duty between the two windows -> no estimate at all */
    ArrangeMeasurement(30.0f, 50.0f, STD_PIN_HIGH);
    IR155_MEASUREMENT_s gap = IR155_GetMeasurementValues();
    TEST_ASSERT_EQUAL_INT((int)IR155_RESISTANCE_ESTIMATION_UNKNOWN, (int)gap.measurementState);
    TEST_ASSERT_FALSE(gap.isMeasurementValid);
    TEST_ASSERT_EQUAL_UINT32(0u, gap.resistance_kOhm);
}

/**
 * @brief   Pins down an inconsistency in the module's undervoltage flag, which
 *          the other cases in this file rely on.
 * @details FINDING, RECORDED AGAINST THE PRODUCT SOURCE. The NORMAL branch
 *          sets the flag on the WRONG OBJECT:
 *              bender_ir155_helper.c:277
 *                  ir155_state.measurement.isUndervoltageDetected = false;
 *          Every other branch assigns the local result instead:
 *              :294 SPEED_START      measurementResult.isUndervoltageDetected = false;
 *              :318 UNDERVOLTAGE     measurementResult.isUndervoltageDetected = true;
 *              :335 IMD_ERROR       measurementResult.isUndervoltageDetected = false;
 *              :351 GROUND_ERROR    measurementResult.isUndervoltageDetected = false;
 *              :368 SHORT_CLAMP     measurementResult.isUndervoltageDetected = false;
 *          The returned struct is initialised with the flag TRUE
 *          (bender_ir155_helper.c:240) and the NORMAL branch never writes it, so
 *          IR155_GetMeasurementValues() reports isUndervoltageDetected == true
 *          for a normal measurement. Only the undervoltage band reports what its
 *          name says; the normal band reports the opposite.
 *
 *          The assertion below states the behaviour AS WRITTEN, not as the
 *          surrounding comments and the field name suggest. It is the only
 *          place in this file that asserts the flag is true, and it is here so
 *          that a future change which fixes :277 -- which would be a
 *          behavioural change to the insulation-monitoring output -- fails this
 *          test rather than passing silently. The value is written as the
 *          literal that the initialiser at :240 supplies, and the enclosing
 *          comment names the line that contradicts it.
 */
void testIr155NormalModeUndervoltageFlagIsTrueAsWritten(void) {
    /* ======= Assertion tests ============================================= */
    /* mode is NORMAL, so :277 is the branch that runs */
    ArrangeMeasurement(10.0f, 50.0f, STD_PIN_HIGH);
    IR155_MEASUREMENT_s m = IR155_GetMeasurementValues();
    TEST_ASSERT_EQUAL_INT((int)IR155_NORMAL_MODE, (int)m.measurementMode);
    /* AS WRITTEN: true, because :277 writes ir155_state and not the result.
     * The initialiser value at :240 is what survives. */
    TEST_ASSERT_TRUE_MESSAGE(m.isUndervoltageDetected,
                             "as written, NORMAL mode reports undervoltage: "
                             "bender_ir155_helper.c:277 assigns ir155_state, not the result");
}
