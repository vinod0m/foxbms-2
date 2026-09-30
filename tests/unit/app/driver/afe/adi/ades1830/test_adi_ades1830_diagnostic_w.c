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
 * @file    test_adi_ades1830_diagnostic_w.c
 * @author  foxBMS Team
 * @date    2023-10-09 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Test of some module
 * @details TODO
 *
 */

/*========== Includes =======================================================*/
#include "unity.h"
#include "Mockdiag.h"
#include "Mockos.h"

#include "adi_ades183x_defs.h"
#include "adi_ades183x_diagnostic.h"

#include "test_assert_helper.h"

#include <stdint.h>
#include <string.h>

/*========== Unit Testing Framework Directives ==============================*/
TEST_SOURCE_FILE("adi_ades183x_diagnostic_w.c")

TEST_INCLUDE_PATH("../../src/app/driver/afe/adi/ades1830")
TEST_INCLUDE_PATH("../../src/app/driver/afe/adi/common/ades183x")
TEST_INCLUDE_PATH("../../src/app/driver/afe/adi/common/ades183x/config")
TEST_INCLUDE_PATH("../../src/app/driver/afe/adi/common/ades183x/diag")
TEST_INCLUDE_PATH("../../src/app/driver/config")
TEST_INCLUDE_PATH("../../src/app/driver/spi")
TEST_INCLUDE_PATH("../../src/app/engine/config")
TEST_INCLUDE_PATH("../../src/app/engine/diag")
TEST_INCLUDE_PATH("../../src/app/task/os")
TEST_INCLUDE_PATH("../../tests/unit/support")

/*========== Definitions and Implementations for Unit Test ==================*/
/* The three ADI_Evaluate* functions read exactly two or three flags of
 * adiState->data.errorTable, indexed [adiState->currentString][moduleNumber],
 * and (for the cell-voltage and GPIO variants) report the outcome to the
 * diagnostic handler. The fixture below therefore only has to provide an error
 * table and a current string; everything asserted is read out of
 * src/app/driver/afe/adi/common/ades183x/adi_ades183x_diagnostic_w.c. */
static ADI_ERROR_TABLE_s test_errorTable;
static ADI_STATE_s        test_adiState;

static void Test_SetErrorFlags(uint8_t string, uint16_t module, bool crc, bool notStuck, bool auxNotStuck) {
    test_errorTable.crcIsOk[string][module]                            = crc;
    test_errorTable.voltageRegisterContentIsNotStuck[string][module]   = notStuck;
    test_errorTable.auxiliaryRegisterContentIsNotStuck[string][module] = auxNotStuck;
}

/*========== Setup and Teardown =============================================*/
void setUp(void) {
    memset(&test_adiState, 0, sizeof(test_adiState));
    memset(&test_errorTable, 0, sizeof(test_errorTable));
    /* ADI_STATE_s::data is a set of pointers; the diagnostic functions read
     * through data.errorTable (adi_ades183x_diagnostic_w.c:117), so the fixture
     * has to point it at the table the test fills in. */
    test_adiState.data.errorTable = &test_errorTable;
}

void tearDown(void) {
}

/*========== Test Cases =====================================================*/

/** @brief   the first-diagnostic-cycle flag reads back what was stored
 *         (adi_ades183x_diagnostic_w.c:89-91 and :157-159)
 */
void testADI_FirstDiagnosticCycleFinishedIsStoredAndReadBack(void) {
    test_adiState.firstDiagnosticMade = false;
    TEST_ASSERT_FALSE(TEST_ADI_IsFirstDiagnosticCycleFinished(&test_adiState));

    OS_EnterTaskCritical_Expect();
    OS_ExitTaskCritical_Expect();
    TEST_ADI_SetFirstDiagnosticCycleFinished(&test_adiState);
    TEST_ASSERT_TRUE(TEST_ADI_IsFirstDiagnosticCycleFinished(&test_adiState));
}

/** @brief   both first-diagnostic-cycle helpers reject a null state
 *         (adi_ades183x_diagnostic_w.c:90 and :99)
 */
void testADI_FirstDiagnosticCycleFinishedRejectsNullState(void) {
    TEST_ASSERT_FAIL_ASSERT(TEST_ADI_IsFirstDiagnosticCycleFinished(NULL_PTR));
    TEST_ASSERT_FAIL_ASSERT(TEST_ADI_SetFirstDiagnosticCycleFinished(NULL_PTR));
}

/** @brief   ADI_Diagnostic() rejects a null state and does nothing otherwise
 *         (adi_ades183x_diagnostic_w.c:108-110)
 */
void testADI_DiagnosticGuardsStateAndIsOtherwiseInert(void) {
    TEST_ASSERT_FAIL_ASSERT(ADI_Diagnostic(NULL_PTR));
    test_adiState.currentString = 0u;
    ADI_Diagnostic(&test_adiState);
    /* the function body after the guard is empty, so no diagnostic is raised */
    TEST_ASSERT_EQUAL(0, DIAG_Handler_CallCount());
}

/** @brief   a good CRC alone is not enough for the cell-voltage diagnostic: the
 *         voltage register must also have changed (adi_ades183x_diagnostic_w.c:117-118)
 */
void testADI_EvaluateDiagnosticCellVoltagesNeedsCrcAndUnstuckRegister(void) {
    test_adiState.currentString = 0u;
    /* crc ok but register stuck -> not ok */
    Test_SetErrorFlags(0u, 0u, true, false, true);
    DIAG_Handler_ExpectAndReturn(DIAG_ID_AFE_COMMUNICATION_INTEGRITY, DIAG_EVENT_NOT_OK, DIAG_STRING, 0u, DIAG_HANDLER_RETURN_OK);
    TEST_ASSERT_FALSE(ADI_EvaluateDiagnosticCellVoltages(&test_adiState, 0u));

    /* crc not ok -> not ok, independently of the register flag */
    Test_SetErrorFlags(0u, 1u, false, true, true);
    DIAG_Handler_ExpectAndReturn(DIAG_ID_AFE_COMMUNICATION_INTEGRITY, DIAG_EVENT_NOT_OK, DIAG_STRING, 0u, DIAG_HANDLER_RETURN_OK);
    TEST_ASSERT_FALSE(ADI_EvaluateDiagnosticCellVoltages(&test_adiState, 1u));

    /* both good -> ok */
    Test_SetErrorFlags(0u, 2u, true, true, false);
    DIAG_Handler_ExpectAndReturn(DIAG_ID_AFE_COMMUNICATION_INTEGRITY, DIAG_EVENT_OK, DIAG_STRING, 0u, DIAG_HANDLER_RETURN_OK);
    TEST_ASSERT_TRUE(ADI_EvaluateDiagnosticCellVoltages(&test_adiState, 2u));
}

/** @brief   the cell-voltage diagnostic reads the row of the current string and
 *         reports that string (adi_ades183x_diagnostic_w.c:117-124)
 */
void testADI_EvaluateDiagnosticCellVoltagesUsesCurrentStringRow(void) {
    /* string 0 is bad, string 1 is good, module 0 in each */
    Test_SetErrorFlags(0u, 0u, false, true, true);
    Test_SetErrorFlags(1u, 0u, true, true, true);

    test_adiState.currentString = 0u;
    DIAG_Handler_ExpectAndReturn(DIAG_ID_AFE_COMMUNICATION_INTEGRITY, DIAG_EVENT_NOT_OK, DIAG_STRING, 0u, DIAG_HANDLER_RETURN_OK);
    TEST_ASSERT_FALSE(ADI_EvaluateDiagnosticCellVoltages(&test_adiState, 0u));

    test_adiState.currentString = 1u;
    DIAG_Handler_ExpectAndReturn(DIAG_ID_AFE_COMMUNICATION_INTEGRITY, DIAG_EVENT_OK, DIAG_STRING, 1u, DIAG_HANDLER_RETURN_OK);
    TEST_ASSERT_TRUE(ADI_EvaluateDiagnosticCellVoltages(&test_adiState, 0u));
}

/** @brief   the GPIO-voltage diagnostic only looks at the CRC
 *         (adi_ades183x_diagnostic_w.c:131-137)
 */
void testADI_EvaluateDiagnosticGpioVoltagesOnlyChecksCrc(void) {
    test_adiState.currentString = 0u;

    /* crc not ok -> not ok, even though the voltage register is unstuck */
    Test_SetErrorFlags(0u, 0u, false, true, true);
    DIAG_Handler_ExpectAndReturn(DIAG_ID_AFE_COMMUNICATION_INTEGRITY, DIAG_EVENT_NOT_OK, DIAG_STRING, 0u, DIAG_HANDLER_RETURN_OK);
    TEST_ASSERT_FALSE(ADI_EvaluateDiagnosticGpioVoltages(&test_adiState, 0u));

    /* crc ok -> ok, even though the voltage register is stuck: this variant does
     * not read that flag */
    Test_SetErrorFlags(0u, 1u, true, false, true);
    DIAG_Handler_ExpectAndReturn(DIAG_ID_AFE_COMMUNICATION_INTEGRITY, DIAG_EVENT_OK, DIAG_STRING, 0u, DIAG_HANDLER_RETURN_OK);
    TEST_ASSERT_TRUE(ADI_EvaluateDiagnosticGpioVoltages(&test_adiState, 1u));
}

/** @brief   the string/module-voltage diagnostic reads the CRC and the
 *         auxiliary register, and raises no diagnostic event of its own
 *         (adi_ades183x_diagnostic_w.c:144-149)
 */
void testADI_EvaluateDiagnosticStringAndModuleVoltagesChecksCrcAndAuxiliary(void) {
    test_adiState.currentString = 0u;

    /* crc ok but auxiliary register stuck -> not ok */
    Test_SetErrorFlags(0u, 0u, true, true, false);
    TEST_ASSERT_FALSE(ADI_EvaluateDiagnosticStringAndModuleVoltages(&test_adiState, 0u));

    /* crc not ok but auxiliary register unstuck -> not ok */
    Test_SetErrorFlags(0u, 1u, false, true, true);
    TEST_ASSERT_FALSE(ADI_EvaluateDiagnosticStringAndModuleVoltages(&test_adiState, 1u));

    /* both good -> ok */
    Test_SetErrorFlags(0u, 2u, true, true, true);
    TEST_ASSERT_TRUE(ADI_EvaluateDiagnosticStringAndModuleVoltages(&test_adiState, 2u));

    /* this variant never calls the diagnostic handler */
    TEST_ASSERT_EQUAL(0, DIAG_Handler_CallCount());
}

/** @brief   every ADI_Evaluate* variant guards the state pointer and the module
 *         index (adi_ades183x_diagnostic_w.c:113-114, :127-128, :140-141)
 */
void testADI_EvaluateDiagnosticGuardsStateAndModuleIndex(void) {
    test_adiState.currentString = 0u;

    TEST_ASSERT_FAIL_ASSERT(ADI_EvaluateDiagnosticCellVoltages(NULL_PTR, 0u));
    TEST_ASSERT_FAIL_ASSERT(ADI_EvaluateDiagnosticGpioVoltages(NULL_PTR, 0u));
    TEST_ASSERT_FAIL_ASSERT(ADI_EvaluateDiagnosticStringAndModuleVoltages(NULL_PTR, 0u));

    Test_SetErrorFlags(0u, BS_NR_OF_MODULES_PER_STRING - 1u, true, true, true);
    DIAG_Handler_ExpectAndReturn(DIAG_ID_AFE_COMMUNICATION_INTEGRITY, DIAG_EVENT_OK, DIAG_STRING, 0u, DIAG_HANDLER_RETURN_OK);
    TEST_ASSERT_TRUE(ADI_EvaluateDiagnosticCellVoltages(&test_adiState, BS_NR_OF_MODULES_PER_STRING - 1u));

    TEST_ASSERT_FAIL_ASSERT(ADI_EvaluateDiagnosticCellVoltages(&test_adiState, BS_NR_OF_MODULES_PER_STRING));
    TEST_ASSERT_FAIL_ASSERT(ADI_EvaluateDiagnosticGpioVoltages(&test_adiState, BS_NR_OF_MODULES_PER_STRING));
    TEST_ASSERT_FAIL_ASSERT(
        ADI_EvaluateDiagnosticStringAndModuleVoltages(&test_adiState, BS_NR_OF_MODULES_PER_STRING));
}
