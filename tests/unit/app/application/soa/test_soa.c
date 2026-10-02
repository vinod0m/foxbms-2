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
 * @file    test_soa.c
 * @author  foxBMS Team
 * @date    2020-04-01 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Tests for SOA module responsible for the current, voltage and
 *          temperature checking of the safe operating area.
 *
 */

/*========== Includes =======================================================*/
#include "unity.h"
#include "Mockbms.h"
#include "Mockcontactor.h"
#include "Mockdatabase.h"
#include "Mockdiag.h"
#include "Mockfoxmath.h"
#include "Mocksoa_cfg.h"

#include "soa.h"
#include "test_assert_helper.h"

/*========== Unit Testing Framework Directives ==============================*/
TEST_INCLUDE_PATH("../../src/app/application/bms")
TEST_INCLUDE_PATH("../../src/app/application/soa")
TEST_INCLUDE_PATH("../../src/app/driver/config")
TEST_INCLUDE_PATH("../../src/app/driver/contactor")
TEST_INCLUDE_PATH("../../src/app/driver/foxmath")
TEST_INCLUDE_PATH("../../src/app/driver/sps")
TEST_INCLUDE_PATH("../../src/app/engine/diag")
TEST_INCLUDE_PATH("../../src/app/task/config")

/*========== Definitions and Implementations for Unit Test ==================*/

/*========== Setup and Teardown =============================================*/
void setUp(void) {
}

void tearDown(void) {
}

/*========== Test Cases =====================================================*/
/**
 * @brief   Testing function SOA_CheckVoltages
 * @details The following cases will be tested:
 *          - Argument validation:
 *            - AT1/1: NULL_PTR for pMinimumMaximumCellVoltages &rarr; assert
 *          - Routine validation:
 *            - RT1/1: complete cell voltage measurement &rarr; limit verdict per string
 *            - RT2/1: incomplete cell voltage measurement &rarr; no limit verdict at all
 */
void testSOA_CheckVoltages(void) {
    /* ======= Assertion tests ============================================= */
    DATA_BLOCK_MIN_MAX_s pMinimumMaximumCellVoltages = {.header.uniqueId = DATA_BLOCK_ID_MIN_MAX};
    /* ======= AT1/1: Assertion test */
    TEST_ASSERT_FAIL_ASSERT(SOA_CheckVoltages(NULL_PTR));

    /* ======= Routine tests =============================================== */
    /* ======= RT1/1: complete measurement of every cell of every string */
    for (uint8_t s = 0u; s < BS_NR_OF_STRINGS; s++) {
        pMinimumMaximumCellVoltages.validMeasuredCellVoltages[s] = (uint16_t)BS_NR_OF_CELL_BLOCKS_PER_STRING;
    }
    /* ======= RT1/1: Test implementation */
    for (uint8_t s = 0u; s < BS_NR_OF_STRINGS; s++) {
        DIAG_Handler_ExpectAndReturn(
            DIAG_ID_CELL_VOLTAGE_OVERVOLTAGE_MSL, DIAG_EVENT_OK, DIAG_STRING, s, DIAG_HANDLER_RETURN_OK);
        DIAG_Handler_ExpectAndReturn(
            DIAG_ID_CELL_VOLTAGE_OVERVOLTAGE_RSL, DIAG_EVENT_OK, DIAG_STRING, s, DIAG_HANDLER_RETURN_OK);
        DIAG_Handler_ExpectAndReturn(
            DIAG_ID_CELL_VOLTAGE_OVERVOLTAGE_MOL, DIAG_EVENT_OK, DIAG_STRING, s, DIAG_HANDLER_RETURN_OK);

        DIAG_Handler_ExpectAndReturn(
            DIAG_ID_CELL_VOLTAGE_UNDERVOLTAGE_MOL, DIAG_EVENT_NOT_OK, DIAG_STRING, s, DIAG_HANDLER_RETURN_OK);
        DIAG_Handler_ExpectAndReturn(
            DIAG_ID_CELL_VOLTAGE_UNDERVOLTAGE_RSL, DIAG_EVENT_NOT_OK, DIAG_STRING, s, DIAG_HANDLER_RETURN_OK);
        DIAG_Handler_ExpectAndReturn(
            DIAG_ID_CELL_VOLTAGE_UNDERVOLTAGE_MSL, DIAG_EVENT_NOT_OK, DIAG_STRING, s, DIAG_HANDLER_RETURN_OK);
    }
    /* ======= RT1/1: call function under test */
    SOA_CheckVoltages(&pMinimumMaximumCellVoltages);

    /* ======= RT1/1: test output verification */
    /* all six expected calls per string were consumed, in order, by the mock */
}

/**
 * @brief   Testing function SOA_CheckVoltages with an incomplete measurement
 * @details The minimum/maximum fields are computed over the valid cells only
 *          (MRC_CalculateCellVoltageMinMaxAverage()), so they do not describe the
 *          string unless every cell contributed. SOA_CheckVoltages must then report
 *          no limit verdict for that string: no DIAG_EVENT_OK, because that would
 *          claim "within limits" for cells that were not measured, and no
 *          DIAG_EVENT_NOT_OK, because that would claim a violation that was not
 *          measured. Both a fully and a partially incomplete string are covered,
 *          so the check cannot be satisfied by merely testing for a zero count.
 */
void testSOA_CheckVoltages_incompleteMeasurementReportsNoVerdict(void) {
    /* ======= Assertion tests ============================================= */
    /* ======= RT2/1: Test implementation, case 1: nothing was measured at all */
    /* Redundancy leaves maximumCellVoltage_mV at INT16_MAX and minimumCellVoltage_mV
     * at INT16_MIN in this case. Both would be evaluated against the limits without
     * the validity check and raise a false over- and undervoltage diagnosis. */
    DATA_BLOCK_MIN_MAX_s nothingMeasured = {
        .header.uniqueId           = DATA_BLOCK_ID_MIN_MAX,
        .maximumCellVoltage_mV     = INT16_MAX,
        .minimumCellVoltage_mV     = INT16_MIN,
        .validMeasuredCellVoltages = {0u},
    };
    /* No DIAG_Handler_Expect* is registered: any call made by the module under test
     * is an unexpected call and fails this test. */
    SOA_CheckVoltages(&nothingMeasured);
    TEST_ASSERT_EQUAL_INT(0, DIAG_Handler_CallCount());

    /* ======= RT2/1: Test implementation, case 2: all but one cell measured */
    DATA_BLOCK_MIN_MAX_s oneCellMissing = {
        .header.uniqueId           = DATA_BLOCK_ID_MIN_MAX,
        .maximumCellVoltage_mV     = INT16_MAX,
        .minimumCellVoltage_mV     = INT16_MIN,
        .validMeasuredCellVoltages = {(uint16_t)(BS_NR_OF_CELL_BLOCKS_PER_STRING - 1u)},
    };
    SOA_CheckVoltages(&oneCellMissing);
    TEST_ASSERT_EQUAL_INT(0, DIAG_Handler_CallCount());
}

/**
 * @brief   Testing function SOA_CheckTemperatures
 * @details The following cases will be tested:
 *          - Argument validation:
 *            - AT1/2: NULL_PTR for pMinimumMaximumCellTemperatures &rarr; assert
 *            - AT2/2: NULL_PTR for pCurrent &rarr; assert
 *          - Routine validation:
 *            - RT1/1: complete cell temperature measurement &rarr; limit verdict per string
 *            - RT2/1: incomplete cell temperature measurement &rarr; no limit verdict at all
 */
void testSOA_CheckTemperatures(void) {
    /* ======= Assertion tests ============================================= */
    DATA_BLOCK_MIN_MAX_s pMinimumMaximumCellVoltages = {.header.uniqueId = DATA_BLOCK_ID_MIN_MAX};
    DATA_BLOCK_PACK_VALUES_s pCurrent                = {.header.uniqueId = DATA_BLOCK_ID_PACK_VALUES};
    int32_t i_current;

    /* ======= AT1/2: Assertion test */
    TEST_ASSERT_FAIL_ASSERT(SOA_CheckTemperatures(NULL_PTR, &pCurrent));
    /* ======= AT2/2: Assertion test */
    TEST_ASSERT_FAIL_ASSERT(SOA_CheckTemperatures(&pMinimumMaximumCellVoltages, NULL_PTR));

    /* ======= Routine tests =============================================== */
    /* ======= RT1/1: complete measurement of every sensor of every string */
    for (uint8_t s = 0u; s < BS_NR_OF_STRINGS; s++) {
        pMinimumMaximumCellVoltages.validMeasuredCellTemperatures[s] = (uint16_t)BS_NR_OF_TEMP_SENSORS_PER_STRING;
    }
    /* ======= RT1/1: Test implementation */
    for (uint8_t s = 0u; s < BS_NR_OF_STRINGS; s++) {
        i_current = pCurrent.stringCurrent_mA[s];
        BMS_GetCurrentFlowDirection_ExpectAndReturn(i_current, BMS_AT_REST);
        DIAG_Handler_ExpectAndReturn(
            DIAG_ID_TEMP_OVERTEMPERATURE_CHARGE_MSL, DIAG_EVENT_OK, DIAG_STRING, s, DIAG_HANDLER_RETURN_OK);
        DIAG_Handler_ExpectAndReturn(
            DIAG_ID_TEMP_OVERTEMPERATURE_CHARGE_RSL, DIAG_EVENT_OK, DIAG_STRING, s, DIAG_HANDLER_RETURN_OK);
        DIAG_Handler_ExpectAndReturn(
            DIAG_ID_TEMP_OVERTEMPERATURE_CHARGE_MOL, DIAG_EVENT_OK, DIAG_STRING, s, DIAG_HANDLER_RETURN_OK);
        BMS_GetCurrentFlowDirection_ExpectAndReturn(i_current, BMS_AT_REST);
        DIAG_Handler_ExpectAndReturn(
            DIAG_ID_TEMP_UNDERTEMPERATURE_CHARGE_MSL, DIAG_EVENT_OK, DIAG_STRING, s, DIAG_HANDLER_RETURN_OK);
        DIAG_Handler_ExpectAndReturn(
            DIAG_ID_TEMP_UNDERTEMPERATURE_CHARGE_RSL, DIAG_EVENT_OK, DIAG_STRING, s, DIAG_HANDLER_RETURN_OK);
        DIAG_Handler_ExpectAndReturn(
            DIAG_ID_TEMP_UNDERTEMPERATURE_CHARGE_MOL, DIAG_EVENT_OK, DIAG_STRING, s, DIAG_HANDLER_RETURN_OK);
    }
    /* ======= RT1/1: call function under test */
    SOA_CheckTemperatures(&pMinimumMaximumCellVoltages, &pCurrent);

    /* ======= RT1/1: test output verification */
    /* all six expected calls per string were consumed, in order, by the mock */
}

/**
 * @brief   Testing function SOA_CheckTemperatures with an incomplete measurement
 * @details The full sensor count for temperatures is BS_NR_OF_TEMP_SENSORS_PER_STRING,
 *          which differs from BS_NR_OF_CELL_BLOCKS_PER_STRING used for cell voltages.
 *          A measurement that is complete for voltages must therefore still be
 *          treated as incomplete for temperatures unless every sensor contributed.
 *          Neither the current flow direction lookup nor any limit verdict may be
 *          derived from such a measurement.
 */
void testSOA_CheckTemperatures_incompleteMeasurementReportsNoVerdict(void) {
    /* ======= RT2/1: Test implementation, case 1: nothing was measured at all */
    DATA_BLOCK_MIN_MAX_s nothingMeasured = {
        .header.uniqueId             = DATA_BLOCK_ID_MIN_MAX,
        .maximumTemperature_ddegC    = INT16_MAX,
        .minimumTemperature_ddegC    = INT16_MIN,
        .validMeasuredCellTemperatures = {0u},
    };
    DATA_BLOCK_PACK_VALUES_s pCurrent = {.header.uniqueId = DATA_BLOCK_ID_PACK_VALUES};
    SOA_CheckTemperatures(&nothingMeasured, &pCurrent);
    TEST_ASSERT_EQUAL_INT(0, DIAG_Handler_CallCount());
    TEST_ASSERT_EQUAL_INT(0, BMS_GetCurrentFlowDirection_CallCount());

    /* ======= RT2/1: Test implementation, case 2: a sensor count that is complete
     * for cell voltages but one short for temperatures */
    DATA_BLOCK_MIN_MAX_s oneSensorMissing = {
        .header.uniqueId             = DATA_BLOCK_ID_MIN_MAX,
        .maximumTemperature_ddegC    = INT16_MAX,
        .minimumTemperature_ddegC    = INT16_MIN,
        .validMeasuredCellTemperatures = {(uint16_t)(BS_NR_OF_TEMP_SENSORS_PER_STRING - 1u)},
    };
    SOA_CheckTemperatures(&oneSensorMissing, &pCurrent);
    TEST_ASSERT_EQUAL_INT(0, DIAG_Handler_CallCount());
    TEST_ASSERT_EQUAL_INT(0, BMS_GetCurrentFlowDirection_CallCount());
}

/**
 * @brief   Testing function SOA_CheckCurrent with an invalid current measurement
 * @details An invalid string or pack current measurement must not produce an
 *          overcurrent verdict in either direction, because no current was
 *          measured. The invalidity of the measurement is reported by the module
 *          that owns the measurement: the redundancy module sets
 *          invalidStringCurrent and reports #DIAG_ID_CURRENT_MEASUREMENT_ERROR
 *          (redundancy.c), the AFE driver reports
 *          #DIAG_ID_AFE_CELL_VOLTAGE_MEAS_ERROR for the cell voltages. This test
 *          pins that the skip in SOA_CheckCurrent() is total and one-sided, so it
 *          cannot drift into either silently reporting OK or silently reporting
 *          NOT_OK for a quantity that was not measured.
 */
void testSOA_CheckCurrent_invalidMeasurementReportsNoVerdict(void) {
    DATA_BLOCK_PACK_VALUES_s invalidStringAndPackCurrent = {
        .header.uniqueId          = DATA_BLOCK_ID_PACK_VALUES,
        .stringCurrent_mA         = {INT32_MAX},
        .invalidStringCurrent     = {1u},
        .packCurrent_mA           = INT32_MAX,
        .invalidPackCurrent       = 1u,
    };
    /* No expectation is registered on any mock: the module under test must not
     * call DIAG_Handler nor any soa_cfg helper for an unmeasured current. */
    SOA_CheckCurrent(&invalidStringAndPackCurrent);
    TEST_ASSERT_EQUAL_INT(0, DIAG_Handler_CallCount());
    TEST_ASSERT_EQUAL_INT(0, SOA_IsStringCurrentLimitViolated_CallCount());
    TEST_ASSERT_EQUAL_INT(0, SOA_IsPackCurrentLimitViolated_CallCount());
    TEST_ASSERT_EQUAL_INT(0, SOA_IsCurrentOnOpenString_CallCount());
}
