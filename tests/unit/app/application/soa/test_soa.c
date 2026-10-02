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

/*========== Recording of the #DIAG_Handler() calls made by the module under test ====
 *
 * #DIAG_Handler_CallCount() in this CMock configuration returns
 * Mock.DIAG_Handler_CallbackCalls, i.e. it counts *callback* invocations, not calls:
 * DIAG_Handler_CmockExpectAndReturn() never touches it. It therefore reads 0 unless a
 * stub is installed, and an assertion of the form
 * TEST_ASSERT_EQUAL_INT(0, DIAG_Handler_CallCount()) is satisfied by every possible
 * behaviour of the module under test and pins nothing. The existing "no verdict"
 * tests above are sound regardless, because they register no expectation at all and an
 * unanticipated call trips CMock's "called more times than expected".
 *
 * To make the *positive* claims below - "exactly these channels, with exactly this event,
 * in this order" - countable, #DIAG_Handler_Stub() is installed for the duration of the
 * test. With a stub in place CMock still checks every registered argument expectation;
 * the stub supplies the return value and its callback is what makes the call counter
 * real. Each test uninstalls the stub again with DIAG_Handler_Stub(NULL_PTR), which
 * restores the mock to the state it had before, so no state leaks into another test.
 */
#define TEST_DIAG_RECORD_MAX (16u)

/** one recorded #DIAG_Handler() call */
typedef struct {
    DIAG_ID_e diagId;
    DIAG_EVENT_e event;
    DIAG_IMPACT_LEVEL_e impact;
    uint32_t data;
} TEST_DIAG_CALL_s;

/** recorded calls, filled by #TEST_DIAG_RecordCallback() in call order */
static TEST_DIAG_CALL_s test_diagCalls[TEST_DIAG_RECORD_MAX];
/** number of recorded calls */
static uint32_t test_diagCallCount = 0u;

/**
 * @brief   Callback that records one #DIAG_Handler() call and returns a benign value
 */
static DIAG_RETURNTYPE_e TEST_DIAG_RecordCallback(
    DIAG_ID_e diagId,
    DIAG_EVENT_e event,
    DIAG_IMPACT_LEVEL_e impact,
    uint32_t data,
    int num_calls) {
    (void)num_calls;
    /* an overrun of the recording buffer is a test failure, not a silent truncation */
    TEST_ASSERT_LESS_OR_EQUAL_UINT32((uint32_t)TEST_DIAG_RECORD_MAX, test_diagCallCount + 1u);
    test_diagCalls[test_diagCallCount].diagId  = diagId;
    test_diagCalls[test_diagCallCount].event   = event;
    test_diagCalls[test_diagCallCount].impact  = impact;
    test_diagCalls[test_diagCallCount].data    = data;
    test_diagCallCount++;
    return DIAG_HANDLER_RETURN_OK;
}

/**
 * @brief   Verify that call number kpIndex was #DIAG_Handler(diagId, event, impact, data)
 */
static void TEST_DIAG_AssertCall(
    uint32_t kpIndex,
    DIAG_ID_e diagId,
    DIAG_EVENT_e event,
    DIAG_IMPACT_LEVEL_e impact,
    uint32_t data) {
    TEST_ASSERT_LESS_THAN_UINT32(test_diagCallCount, kpIndex);
    TEST_ASSERT_EQUAL(diagId, test_diagCalls[kpIndex].diagId);
    TEST_ASSERT_EQUAL(event, test_diagCalls[kpIndex].event);
    TEST_ASSERT_EQUAL(impact, test_diagCalls[kpIndex].impact);
    TEST_ASSERT_EQUAL(data, test_diagCalls[kpIndex].data);
}

/**
 * @brief   Testing function SOA_CheckCurrent with an invalid current measurement
 * @details An invalid string or pack current measurement cannot yield an overcurrent verdict
 *          in either flow direction, because no current was measured. The module must therefore
 *          report the four string overcurrent channels of every invalid string and the two pack
 *          overcurrent channels as #DIAG_EVENT_NOT_EVALUATED, rather than emit nothing at all.
 *
 *          Emitting nothing leaves each channel on whatever its last verdict was. For a channel
 *          that was last cleared that is a latched "within limits" for a quantity that was
 *          never measured; for a channel with a developing overcurrent it freezes the occurrence
 *          counter that DIAG_Handler() decrements on every DIAG_EVENT_OK. Both are wrong, and
 *          neither can be fixed by reporting DIAG_EVENT_NOT_OK, which would open the contactors
 *          on a shunt fault.
 *
 *          #DIAG_EVENT_NOT_EVALUATED itself is verified to have no side effects on a diagnosis
 *          channel in test_diag.c (testDIAG_HandlerNotEvaluatedHoldsState), so it can neither
 *          raise nor clear one. The invalidity of the measurement remains reported by the module
 *          that owns the measurement: the redundancy module sets invalidStringCurrent /
 *          invalidPackCurrent and reports #DIAG_ID_CURRENT_MEASUREMENT_ERROR (redundancy.c).
 *
 *          No #soa_cfg limit helper and no current-flow direction lookup is registered as an
 *          expectation below, so reaching one is an unexpected call and fails the test: nothing
 *          may be derived from a current that does not exist.
 */
void testSOA_CheckCurrent_invalidMeasurementReportsNotEvaluated(void) {
    DATA_BLOCK_PACK_VALUES_s invalidStringAndPackCurrent = {
        .header.uniqueId      = DATA_BLOCK_ID_PACK_VALUES,
        .stringCurrent_mA     = {INT32_MAX},
        .invalidStringCurrent = {1u},
        .packCurrent_mA       = INT32_MAX,
        .invalidPackCurrent   = 1u,
    };
    /* ======= RT1/1: Test implementation */
    test_diagCallCount = 0u;
    DIAG_Handler_Stub(TEST_DIAG_RecordCallback);
    SOA_CheckCurrent(&invalidStringAndPackCurrent);
    DIAG_Handler_Stub(NULL_PTR);

    /* ======= RT1/1: test output verification */
    TEST_ASSERT_EQUAL_UINT32(((uint32_t)BS_NR_OF_STRINGS * 4u) + 2u, test_diagCallCount);
    /* channel by channel: every one of them held, none of them cleared, none of them raised */
    for (uint8_t s = 0u; s < BS_NR_OF_STRINGS; s++) {
        TEST_DIAG_AssertCall(
            ((uint32_t)s * 4u) + 0u, DIAG_ID_STRING_OVERCURRENT_CHARGE_MSL, DIAG_EVENT_NOT_EVALUATED, DIAG_STRING, s);
        TEST_DIAG_AssertCall(
            ((uint32_t)s * 4u) + 1u, DIAG_ID_OVERCURRENT_CHARGE_CELL_MSL, DIAG_EVENT_NOT_EVALUATED, DIAG_STRING, s);
        TEST_DIAG_AssertCall(
            ((uint32_t)s * 4u) + 2u,
            DIAG_ID_STRING_OVERCURRENT_DISCHARGE_MSL,
            DIAG_EVENT_NOT_EVALUATED,
            DIAG_STRING,
            s);
        TEST_DIAG_AssertCall(
            ((uint32_t)s * 4u) + 3u, DIAG_ID_OVERCURRENT_DISCHARGE_CELL_MSL, DIAG_EVENT_NOT_EVALUATED, DIAG_STRING, s);
    }
    TEST_DIAG_AssertCall(
        (uint32_t)BS_NR_OF_STRINGS * 4u + 0u,
        DIAG_ID_PACK_OVERCURRENT_CHARGE_MSL,
        DIAG_EVENT_NOT_EVALUATED,
        DIAG_SYSTEM,
        0u);
    TEST_DIAG_AssertCall(
        (uint32_t)BS_NR_OF_STRINGS * 4u + 1u,
        DIAG_ID_PACK_OVERCURRENT_DISCHARGE_MSL,
        DIAG_EVENT_NOT_EVALUATED,
        DIAG_SYSTEM,
        0u);
}

/**
 * @brief   Testing that SOA_CheckCurrent never reports an OK verdict for an unmeasured current
 * @details The scenario is an overcurrent that is still developing. Cycle 1 has a measurable
 *          current below every limit, so the module reports DIAG_EVENT_OK on all six
 *          overcurrent channels. Cycle 2 has an unmeasurable current on string 0 and on the
 *          pack, and every affected channel must report #DIAG_EVENT_NOT_EVALUATED.
 *
 *          The claim is asserted per channel and per event, not as a call count, because the
 *          failure this pins is a *wrong* event rather than a missing one. An unmeasured
 *          current reported as DIAG_EVENT_OK is exactly what keeps a stale "within limits"
 *          verdict alive, and DIAG_Handler() decrements the occurrence counter of a developing
 *          diagnosis on every DIAG_EVENT_OK - so a single channel drifting to DIAG_EVENT_OK in
 *          either flow direction fails this test. Only string 0 and the pack lost their
 *          measurement, so no other string may report anything at all in cycle 2.
 */
void testSOA_CheckCurrent_unmeasuredCurrentIsNeverReportedOk(void) {
    DATA_BLOCK_PACK_VALUES_s measurableCurrent = {
        .header.uniqueId          = DATA_BLOCK_ID_PACK_VALUES,
        .stringCurrent_mA         = {0},
        .invalidStringCurrent     = {0u},
        .packCurrent_mA           = 0,
        .invalidPackCurrent       = 0u,
    };
    /* ======= RT1/1: cycle 1, the current is measurable and below every limit */
    for (uint8_t s = 0u; s < BS_NR_OF_STRINGS; s++) {
        BMS_GetCurrentFlowDirection_ExpectAndReturn(0, BMS_AT_REST);
        SOA_IsStringCurrentLimitViolated_ExpectAndReturn(0u, BMS_AT_REST, false);
        SOA_IsCellCurrentLimitViolated_ExpectAndReturn(0u, BMS_AT_REST, false);
        DIAG_Handler_ExpectAndReturn(
            DIAG_ID_STRING_OVERCURRENT_CHARGE_MSL, DIAG_EVENT_OK, DIAG_STRING, s, DIAG_HANDLER_RETURN_OK);
        DIAG_Handler_ExpectAndReturn(
            DIAG_ID_OVERCURRENT_CHARGE_CELL_MSL, DIAG_EVENT_OK, DIAG_STRING, s, DIAG_HANDLER_RETURN_OK);
        DIAG_Handler_ExpectAndReturn(
            DIAG_ID_STRING_OVERCURRENT_DISCHARGE_MSL, DIAG_EVENT_OK, DIAG_STRING, s, DIAG_HANDLER_RETURN_OK);
        DIAG_Handler_ExpectAndReturn(
            DIAG_ID_OVERCURRENT_DISCHARGE_CELL_MSL, DIAG_EVENT_OK, DIAG_STRING, s, DIAG_HANDLER_RETURN_OK);
        SOA_IsCurrentOnOpenString_ExpectAndReturn(BMS_AT_REST, s, false);
        DIAG_Handler_ExpectAndReturn(
            DIAG_ID_CURRENT_ON_OPEN_STRING, DIAG_EVENT_OK, DIAG_STRING, s, DIAG_HANDLER_RETURN_OK);
    }
    BMS_GetCurrentFlowDirection_ExpectAndReturn(0, BMS_AT_REST);
    SOA_IsPackCurrentLimitViolated_ExpectAndReturn(0u, BMS_AT_REST, false);
    DIAG_Handler_ExpectAndReturn(
        DIAG_ID_PACK_OVERCURRENT_CHARGE_MSL, DIAG_EVENT_OK, DIAG_SYSTEM, 0u, DIAG_HANDLER_RETURN_OK);
    DIAG_Handler_ExpectAndReturn(
        DIAG_ID_PACK_OVERCURRENT_DISCHARGE_MSL, DIAG_EVENT_OK, DIAG_SYSTEM, 0u, DIAG_HANDLER_RETURN_OK);
    SOA_CheckCurrent(&measurableCurrent);

    /* ======= RT2/1: cycle 2, the current of string 0 and of the pack became unmeasurable */
    measurableCurrent.invalidStringCurrent[0] = 1u;
    measurableCurrent.invalidPackCurrent         = 1u;
    test_diagCallCount = 0u;
    DIAG_Handler_Stub(TEST_DIAG_RecordCallback);
    /* no #soa_cfg limit helper and no direction lookup is registered for this cycle: reaching
     * one is an unexpected call and fails the test */
    SOA_CheckCurrent(&measurableCurrent);
    DIAG_Handler_Stub(NULL_PTR);

    /* ======= RT2/1: test output verification */
    TEST_ASSERT_EQUAL_UINT32(6u, test_diagCallCount);
    TEST_DIAG_AssertCall(0u, DIAG_ID_STRING_OVERCURRENT_CHARGE_MSL, DIAG_EVENT_NOT_EVALUATED, DIAG_STRING, 0u);
    TEST_DIAG_AssertCall(1u, DIAG_ID_OVERCURRENT_CHARGE_CELL_MSL, DIAG_EVENT_NOT_EVALUATED, DIAG_STRING, 0u);
    TEST_DIAG_AssertCall(2u, DIAG_ID_STRING_OVERCURRENT_DISCHARGE_MSL, DIAG_EVENT_NOT_EVALUATED, DIAG_STRING, 0u);
    TEST_DIAG_AssertCall(3u, DIAG_ID_OVERCURRENT_DISCHARGE_CELL_MSL, DIAG_EVENT_NOT_EVALUATED, DIAG_STRING, 0u);
    TEST_DIAG_AssertCall(4u, DIAG_ID_PACK_OVERCURRENT_CHARGE_MSL, DIAG_EVENT_NOT_EVALUATED, DIAG_SYSTEM, 0u);
    TEST_DIAG_AssertCall(5u, DIAG_ID_PACK_OVERCURRENT_DISCHARGE_MSL, DIAG_EVENT_NOT_EVALUATED, DIAG_SYSTEM, 0u);
}
