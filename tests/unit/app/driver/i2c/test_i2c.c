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
 * @file    test_i2c.c
 * @author  foxBMS Team
 * @date    2021-07-23 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Tests for the I2C module
 *
 */

/*========== Includes =======================================================*/
#include "unity.h"
#include "MockHL_i2c.h"
#include "MockHL_sys_dma.h"
#include "Mockmcu.h"
#include "Mockos.h"

#include "i2c.h"
#include "test_assert_helper.h"

/*========== Unit Testing Framework Directives ==============================*/
TEST_INCLUDE_PATH("../../src/app/driver/config")
TEST_INCLUDE_PATH("../../src/app/driver/dma")
TEST_INCLUDE_PATH("../../src/app/driver/i2c")
TEST_INCLUDE_PATH("../../src/app/engine/diag")

/*========== Definitions and Implementations for Unit Test ==================*/

long FSYS_RaisePrivilege(void) {
    return 0;
}

/*========== Setup and Teardown =============================================*/
void setUp(void) {
}

void tearDown(void) {
}

/*========== Test Cases =====================================================*/
void testI2C_GetWordTransmitTime(void) {
    /* ======= Assertion tests ============================================= */
    /* ======= AT1/1: Assertion test */
    TEST_ASSERT_FAIL_ASSERT(TEST_I2C_GetWordTransmitTime(NULL_PTR));

    /* ======= Routine tests =============================================== */
    i2cBASE_t pI2cInterface = {0};

    /* ======= RT1/3: Test implementation */
    TEST_I2C_GetWordTransmitTime(&pI2cInterface);

    /* ======= RT2/3: Test implementation */
    pI2cInterface.PSC = (pI2cInterface.PSC & ~0xFF) | 0x01;
    TEST_I2C_GetWordTransmitTime(&pI2cInterface);

    /* ======= RT3/3: Test implementation */
    pI2cInterface.PSC = (pI2cInterface.PSC & ~0xFF) | 0x02;
    TEST_I2C_GetWordTransmitTime(&pI2cInterface);
}

void testI2C_WaitTransmit(void) {
    /* ======= Assertion tests ============================================= */
    /* ======= AT1/1: Assertion test */
    TEST_ASSERT_FAIL_ASSERT(TEST_I2C_WaitTransmit(NULL_PTR, 0u));

    /* ======= Routine tests =============================================== */
    i2cBASE_t pI2cInterface = {0};
    uint32_t timeout_us     = 0u;
    uint32_t startCounter   = 0u;

    /* ======= RT1/3: Test implementation */
    MCU_GetFreeRunningCount_ExpectAndReturn(0u);
    MCU_IsTimeElapsed_ExpectAndReturn(startCounter, timeout_us, true);
    TEST_I2C_WaitTransmit(&pI2cInterface, timeout_us);

    /* ======= RT2/3: Test implementation */
    MCU_GetFreeRunningCount_ExpectAndReturn(0u);
    pI2cInterface.STR = 2u;
    TEST_I2C_WaitTransmit(&pI2cInterface, timeout_us);

    /* ======= RT3/3: Test implementation */
    MCU_GetFreeRunningCount_ExpectAndReturn(0u);
    pI2cInterface.STR = 16u;
    TEST_I2C_WaitTransmit(&pI2cInterface, timeout_us);
}

void testI2C_WaitStop(void) {
    /* ======= Assertion tests ============================================= */
    /* ======= AT1/1: Assertion test */
    TEST_ASSERT_FAIL_ASSERT(TEST_I2C_WaitStop(NULL_PTR, 0u));

    /* ======= Routine tests =============================================== */
    i2cBASE_t pI2cInterface = {0};
    uint32_t timeout_us     = 0u;
    uint32_t startCounter   = 0u;

    /* ======= RT1/2: Test implementation */
    MCU_GetFreeRunningCount_ExpectAndReturn(0u);
    i2cIsStopDetected_ExpectAndReturn(&pI2cInterface, 1u);
    TEST_I2C_WaitStop(&pI2cInterface, timeout_us);

    /* ======= RT2/2: Test implementation */
    MCU_GetFreeRunningCount_ExpectAndReturn(0u);
    i2cIsStopDetected_ExpectAndReturn(&pI2cInterface, 0u);
    MCU_IsTimeElapsed_ExpectAndReturn(startCounter, timeout_us, true);
    i2cIsStopDetected_ExpectAndReturn(&pI2cInterface, 0u);
    TEST_I2C_WaitStop(&pI2cInterface, timeout_us);
}

void testI2C_WaitForTxCompletedNotification(void) {
    /* ======= Routine tests =============================================== */
    uint32_t notifiedValueTx = I2C_NO_NOTIFIED_VALUE;
    /* prevent unused variable */
    notifiedValueTx += 1u;
    notifiedValueTx -= 1u;

    /* ======= RT1/1: Test implementation */
    OS_WaitForNotificationIndexed_ExpectAndReturn(
        I2C_NOTIFICATION_TX_INDEX, &notifiedValueTx, I2C_NOTIFICATION_TIMEOUT_ms, OS_SUCCESS);
    TEST_I2C_WaitForTxCompletedNotification();
}

void testI2C_WaitForRxCompletedNotification(void) {
    /* ======= Routine tests =============================================== */
    uint32_t notifiedValueRx = I2C_NO_NOTIFIED_VALUE;
    /* prevent unused variable */
    notifiedValueRx += 1u;
    notifiedValueRx -= 1u;

    /* ======= RT1/1: Test implementation */
    OS_WaitForNotificationIndexed_ExpectAndReturn(
        I2C_NOTIFICATION_RX_INDEX, &notifiedValueRx, I2C_NOTIFICATION_TIMEOUT_ms, OS_SUCCESS);
    TEST_I2C_WaitForRxCompletedNotification();
}

void testI2C_ClearNotifications(void) {
    /* ======= Routine tests =============================================== */
    /* ======= RT1/1: Test implementation */
    /* OS_ClearNotificationIndexed returns OS_STD_RETURN_e
     * (src/app/task/os/os.h:104-107), whose success value is OS_SUCCESS. STD_OK is
     * an enumerator of the unrelated STD_RETURN_TYPE_e
     * (src/app/main/include/fstd_types.h:82-85) and is rejected by
     * -Wenum-conversion. */
    OS_ClearNotificationIndexed_ExpectAndReturn(I2C_NOTIFICATION_TX_INDEX, OS_SUCCESS);
    OS_ClearNotificationIndexed_ExpectAndReturn(I2C_NOTIFICATION_RX_INDEX, OS_SUCCESS);
    TEST_I2C_ClearNotifications();
}

/** I2C Initialize calls the HAL init function */
void testI2c_Initialize(void) {
    i2cInit_Expect();
    I2C_Initialize();
}

void testI2C_Read(void) {
    i2cBASE_t validI2cInterface;
    uint32_t validSlaveAddress = 0u;
    uint32_t validNrBytesWrite = 1u;
    uint8_t validReadData      = 1u;

    /* ======= Assertion tests ============================================= */
    /* ======= AT1/4: Assertion test */
    TEST_ASSERT_FAIL_ASSERT(I2C_Read(NULL_PTR, validSlaveAddress, validNrBytesWrite, &validReadData));
    /* ======= AT2/4: Assertion test */
    TEST_ASSERT_FAIL_ASSERT(I2C_Read(&validI2cInterface, 128u, validNrBytesWrite, &validReadData));
    /* ======= AT3/4: Assertion test */
    TEST_ASSERT_FAIL_ASSERT(I2C_Read(&validI2cInterface, validSlaveAddress, 0u, &validReadData));
    /* ======= AT4/4: Assertion test */
    TEST_ASSERT_FAIL_ASSERT(I2C_Read(&validI2cInterface, validSlaveAddress, validNrBytesWrite, NULL_PTR));

    /* ======= Routine tests =============================================== */
    i2cBASE_t pI2cInterface = {0};
    uint32_t slaveAddress   = 0u;
    uint32_t nrBytes        = 1u;
    uint8_t readData        = 0u;
    /* ======= RT1/1: Test implementation */
    i2cSetMode_Expect(&pI2cInterface, (uint32_t)I2C_MASTER);
    i2cSetDirection_Expect(&pI2cInterface, (uint32_t)I2C_RECEIVER);
    i2cSetSlaveAdd_Expect(&pI2cInterface, slaveAddress);
    i2cSetStart_Expect(&pI2cInterface);
    i2cSetStop_Expect(&pI2cInterface);

    MCU_GetFreeRunningCount_ExpectAndReturn(0u);
    MCU_GetFreeRunningCount_ExpectAndReturn(0u);
    i2cIsStopDetected_ExpectAndReturn(&pI2cInterface, 1u);

    I2C_Read(&pI2cInterface, slaveAddress, nrBytes, &readData);
}

/**
 * @brief   Testing extern function #I2C_Write
 * @details The following cases need to be tested:
 *          - Argument validation:
 *            - AT1/4: NULL_PTR for pI2cInterface &rarr; assert
 *            - AT2/4: invalid slaveAddress &rarr; assert
 *            - AT3/4: invalid nrBytes &rarr; assert
 *            - AT4/4: NULL_PTR for writeData &rarr; assert
 *          - Routine validation:
 *            - RT1/x: TODO
 */
void testI2C_Write(void) {
    i2cBASE_t validI2cInterface;
    uint32_t validSlaveAddress = 0u;
    uint32_t validNrBytesWrite = 1u;
    uint8_t validWriteData     = 1u;
    /* ======= AT1/4: Assertion test */
    TEST_ASSERT_FAIL_ASSERT(I2C_Write(NULL_PTR, validSlaveAddress, validNrBytesWrite, &validWriteData));
    /* ======= AT2/4: Assertion test */
    TEST_ASSERT_FAIL_ASSERT(I2C_Write(&validI2cInterface, 130u, validNrBytesWrite, &validWriteData));
    /* ======= AT3/4: Assertion test */
    TEST_ASSERT_FAIL_ASSERT(I2C_Write(&validI2cInterface, validSlaveAddress, 0u, &validWriteData));
    /* ======= AT4/4: Assertion test */
    TEST_ASSERT_FAIL_ASSERT(I2C_Write(&validI2cInterface, validSlaveAddress, validNrBytesWrite, NULL_PTR));

    /* ======= Routine tests =============================================== */
    i2cBASE_t pI2cInterface = {0};
    uint32_t slaveAddress   = 0u;
    uint32_t nrBytes        = 1u;
    uint8_t writeData       = 0u;
    /* ======= RT1/1: Test implementation */
    i2cSetMode_Expect(&pI2cInterface, (uint32_t)I2C_MASTER);
    i2cSetDirection_Expect(&pI2cInterface, (uint32_t)I2C_TRANSMITTER);
    i2cSetSlaveAdd_Expect(&pI2cInterface, slaveAddress);
    i2cSetStop_Expect(&pI2cInterface);
    i2cSetCount_Expect(&pI2cInterface, nrBytes);
    i2cSetStart_Expect(&pI2cInterface);

    MCU_GetFreeRunningCount_ExpectAndReturn(0u);
    MCU_GetFreeRunningCount_ExpectAndReturn(0u);
    i2cIsStopDetected_ExpectAndReturn(&pI2cInterface, 1u);

    I2C_Write(&pI2cInterface, slaveAddress, nrBytes, &writeData);
}

/**
 * @brief   Testing extern function #I2C_WriteRead
 * @details The following cases need to be tested:
 *          - Argument validation:
 *            - AT1/6: NULL_PTR for I2cInterface &rarr; assert
 *            - AT2/6: invalid slaveAddress &rarr; assert
 *            - AT3/6: invalid nrBytesWrite &rarr; assert
 *            - AT4/6: NULL_PTR for writeData &rarr; assert
 *            - AT5/6: invalid nrBytesRead &rarr; assert
 *            - AT6/6: NULL_PTR for readData &rarr; assert
 *          - Routine validation:
 *            - RT1/x: TODO
 */
void testI2C_WriteRead(void) {
    /* ======= Assertion tests ============================================= */
    i2cBASE_t validI2cInterface;
    uint32_t validSlaveAddress = 0u;
    uint32_t validNrBytesWrite = 1u;
    uint8_t validWriteData     = 1u;
    uint32_t validNrBytesRead  = 2u;
    uint8_t validReadData      = 1u;
    /* ======= AT1/6: Assertion test */
    TEST_ASSERT_FAIL_ASSERT(I2C_WriteRead(
        NULL_PTR, validSlaveAddress, validNrBytesWrite, &validWriteData, validNrBytesRead, &validReadData));
    /* ======= AT2/6: Assertion test */
    TEST_ASSERT_FAIL_ASSERT(
        I2C_WriteRead(&validI2cInterface, 130u, validNrBytesWrite, &validWriteData, validNrBytesRead, &validReadData));
    /* ======= AT3/6: Assertion test */
    TEST_ASSERT_FAIL_ASSERT(
        I2C_WriteRead(&validI2cInterface, validSlaveAddress, 0u, &validWriteData, validNrBytesRead, &validReadData));
    /* ======= AT4/6: Assertion test */
    TEST_ASSERT_FAIL_ASSERT(I2C_WriteRead(
        &validI2cInterface, validSlaveAddress, validNrBytesWrite, NULL_PTR, validNrBytesRead, &validReadData));
    /* ======= AT5/6: Assertion test */
    TEST_ASSERT_FAIL_ASSERT(
        I2C_WriteRead(&validI2cInterface, validSlaveAddress, validNrBytesWrite, &validWriteData, 0u, &validReadData));
    /* ======= AT6/6: Assertion test */
    TEST_ASSERT_FAIL_ASSERT(I2C_WriteRead(
        &validI2cInterface, validSlaveAddress, validNrBytesWrite, &validWriteData, validNrBytesRead, NULL_PTR));

    /* ======= Routine tests =============================================== */
    i2cBASE_t pI2cInterface = {0};
    uint32_t slaveAddress   = 0u;
    uint32_t nrBytesWrite   = 1u;
    uint8_t writeData       = 0u;
    uint32_t nrBytesRead    = 1u;
    uint8_t readData        = 0u;
    /* ======= RT1/1: Test implementation */
    i2cSetMode_Expect(&pI2cInterface, (uint32_t)I2C_MASTER);
    i2cSetDirection_Expect(&pI2cInterface, (uint32_t)I2C_TRANSMITTER);
    i2cSetSlaveAdd_Expect(&pI2cInterface, slaveAddress);
    i2cSetStart_Expect(&pI2cInterface);

    MCU_GetFreeRunningCount_ExpectAndReturn(0u);
    i2cSetMode_Expect(&pI2cInterface, (uint32_t)I2C_MASTER);
    i2cSetDirection_Expect(&pI2cInterface, (uint32_t)I2C_RECEIVER);
    i2cSetStart_Expect(&pI2cInterface);
    i2cSetStop_Expect(&pI2cInterface);
    MCU_GetFreeRunningCount_ExpectAndReturn(0u);

    MCU_GetFreeRunningCount_ExpectAndReturn(0u);
    i2cIsStopDetected_ExpectAndReturn(&pI2cInterface, 1u);

    I2C_WriteRead(&pI2cInterface, slaveAddress, nrBytesWrite, &writeData, nrBytesRead, &readData);
}

/**
 * @brief   Testing extern function #I2C_WriteReadDma
 * @details The following cases need to be tested:
 *          - Argument validation:
 *            - AT1/6: NULL_PTR for I2cInterface &rarr; assert
 *            - AT2/6: invalid slaveAddress &rarr; assert
 *            - AT3/6: invalid nrBytesWrite &rarr; assert
 *            - AT4/6: NULL_PTR for writeData &rarr; assert
 *            - AT5/6: invalid nrBytesRead &rarr; assert
 *            - AT6/6: NULL_PTR for readData &rarr; assert
 *          - Routine validation:
 *            - RT1/x: TODO
 */
void testI2C_WriteReadDma(void) {
    /* ======= Assertion tests ============================================= */
    i2cBASE_t validI2cInterface;
    uint32_t validSlaveAddress = 0u;
    uint32_t validNrBytesWrite = 1u;
    uint8_t validWriteData     = 1u;
    uint32_t validNrBytesRead  = 2u;
    uint8_t validReadData      = 1u;
    /* ======= AT1/6: Assertion test */
    TEST_ASSERT_FAIL_ASSERT(I2C_WriteReadDma(
        NULL_PTR, validSlaveAddress, validNrBytesWrite, &validWriteData, validNrBytesRead, &validReadData));
    /* ======= AT2/6: Assertion test */
    TEST_ASSERT_FAIL_ASSERT(I2C_WriteReadDma(
        &validI2cInterface, 130u, validNrBytesWrite, &validWriteData, validNrBytesRead, &validReadData));
    /* ======= AT3/6: Assertion test */
    TEST_ASSERT_FAIL_ASSERT(
        I2C_WriteReadDma(&validI2cInterface, validSlaveAddress, 0u, &validWriteData, validNrBytesRead, &validReadData));
    /* ======= AT4/6: Assertion test */
    TEST_ASSERT_FAIL_ASSERT(I2C_WriteReadDma(
        &validI2cInterface, validSlaveAddress, validNrBytesWrite, NULL_PTR, validNrBytesRead, &validReadData));
    /* ======= AT5/6: Assertion test */
    TEST_ASSERT_FAIL_ASSERT(I2C_WriteReadDma(
        &validI2cInterface, validSlaveAddress, validNrBytesWrite, &validWriteData, 1u, &validReadData));
    /* ======= AT6/6: Assertion test */
    TEST_ASSERT_FAIL_ASSERT(I2C_WriteReadDma(
        &validI2cInterface, validSlaveAddress, validNrBytesWrite, &validWriteData, validNrBytesRead, NULL_PTR));

    /* ======= Routine tests =============================================== */
    /* ======= RT1/x: Test implementation */
}

/**
 * @brief   Put the interface in the state that makes the driver skip a transfer
 * @param  pI2cInterface interface to drive
 * @details The bus-busy bit is taken from the same macro the driver itself tests
 *          at src/app/driver/i2c/i2c.c:237 and its five siblings, and is never
 *          written out as a literal, so this test cannot encode a register value
 *          of its own.
 */
static void TEST_I2CbusBusy_SetBusBusy(i2cBASE_t *const pI2cInterface) {
    pI2cInterface->STR = (uint32_t)I2C_BUSBUSY;
}

/*
 * ==========================================================================
 * A skipped transfer must be reported as a failure
 * ==========================================================================
 *
 * Every public entry point of src/app/driver/i2c/i2c.c gates the whole transfer
 * on the bus not being busy and returns STD_NOT_OK from the `else` arm when it
 * is. The six cases below assert that return.
 *
 * Two things are asserted at once, and the second is what makes the first
 * meaningful: the return value is STD_NOT_OK, AND not a single i2c* call is
 * made. The second is not written as a count - it is asserted by leaving zero
 * `i2cSet*_Expect` calls on the mocks. Had the driver transferred anything,
 * CMock would abort with an unexpected-call failure. So a STD_NOT_OK return
 * cannot be bought by doing the work anyway.
 *
 * The three DMA entry points additionally clear the TX/RX notifications
 * before they test the bus (i2c.c:426 for I2C_ReadDma, :521 for I2C_WriteDma,
 * :616 for I2C_WriteReadDma). That is bookkeeping, not a transfer, and those two
 * calls are the only ones those three make on this path.
 */

/** A read that was never started must not report success */
void testI2C_busBusy_I2C_Read_reportsFailure(void) {
    i2cBASE_t pI2cInterface = {0};
    uint32_t slaveAddress   = 0u;
    uint32_t nrBytes        = 1u;
    uint8_t readData        = 0u;

    TEST_I2CbusBusy_SetBusBusy(&pI2cInterface);

    TEST_ASSERT_EQUAL(STD_NOT_OK, I2C_Read(&pI2cInterface, slaveAddress, nrBytes, &readData));
}

/** A write that was never started must not report success */
void testI2C_busBusy_I2C_Write_reportsFailure(void) {
    i2cBASE_t pI2cInterface = {0};
    uint32_t slaveAddress   = 0u;
    uint32_t nrBytes        = 1u;
    uint8_t writeData       = 0u;

    TEST_I2CbusBusy_SetBusBusy(&pI2cInterface);

    TEST_ASSERT_EQUAL(STD_NOT_OK, I2C_Write(&pI2cInterface, slaveAddress, nrBytes, &writeData));
}

/** A combined write-then-read that was never started must not report success */
void testI2C_busBusy_I2C_WriteRead_reportsFailure(void) {
    i2cBASE_t pI2cInterface = {0};
    uint32_t slaveAddress   = 0u;
    uint32_t nrBytesWrite   = 1u;
    uint8_t writeData       = 0u;
    uint32_t nrBytesRead    = 1u;
    uint8_t readData        = 0u;

    TEST_I2CbusBusy_SetBusBusy(&pI2cInterface);

    TEST_ASSERT_EQUAL(
        STD_NOT_OK, I2C_WriteRead(&pI2cInterface, slaveAddress, nrBytesWrite, &writeData, nrBytesRead, &readData));
}

/** A DMA read that was never started must not report success */
void testI2C_busBusy_I2C_ReadDma_reportsFailure(void) {
    i2cBASE_t pI2cInterface = {0};
    uint32_t slaveAddress   = 0u;
    uint32_t nrBytes        = 2u;
    uint8_t readData[2]     = {0u, 0u};

    TEST_I2CbusBusy_SetBusBusy(&pI2cInterface);
    OS_ClearNotificationIndexed_ExpectAndReturn(I2C_NOTIFICATION_TX_INDEX, OS_SUCCESS);
    OS_ClearNotificationIndexed_ExpectAndReturn(I2C_NOTIFICATION_RX_INDEX, OS_SUCCESS);

    TEST_ASSERT_EQUAL(STD_NOT_OK, I2C_ReadDma(&pI2cInterface, slaveAddress, nrBytes, readData));
}

/** A DMA write that was never started must not report success */
void testI2C_busBusy_I2C_WriteDma_reportsFailure(void) {
    i2cBASE_t pI2cInterface = {0};
    uint32_t slaveAddress   = 0u;
    uint32_t nrBytes        = 2u;
    uint8_t writeData[2]    = {0u, 0u};

    TEST_I2CbusBusy_SetBusBusy(&pI2cInterface);
    OS_ClearNotificationIndexed_ExpectAndReturn(I2C_NOTIFICATION_TX_INDEX, OS_SUCCESS);
    OS_ClearNotificationIndexed_ExpectAndReturn(I2C_NOTIFICATION_RX_INDEX, OS_SUCCESS);

    TEST_ASSERT_EQUAL(STD_NOT_OK, I2C_WriteDma(&pI2cInterface, slaveAddress, nrBytes, writeData));
}

/** A combined DMA write-then-read that was never started must not report success */
void testI2C_busBusy_I2C_WriteReadDma_reportsFailure(void) {
    i2cBASE_t pI2cInterface = {0};
    uint32_t slaveAddress   = 0u;
    uint32_t nrBytesWrite   = 2u;
    uint8_t writeData[2]    = {0u, 0u};
    uint32_t nrBytesRead    = 2u;
    uint8_t readData[2]     = {0u, 0u};

    TEST_I2CbusBusy_SetBusBusy(&pI2cInterface);
    OS_ClearNotificationIndexed_ExpectAndReturn(I2C_NOTIFICATION_TX_INDEX, OS_SUCCESS);
    OS_ClearNotificationIndexed_ExpectAndReturn(I2C_NOTIFICATION_RX_INDEX, OS_SUCCESS);

    TEST_ASSERT_EQUAL(
        STD_NOT_OK,
        I2C_WriteReadDma(&pI2cInterface, slaveAddress, nrBytesWrite, writeData, nrBytesRead, readData));
}

/**
 * @brief   The busy-bus arm is reachable, so the six cases above are not vacuous
 * @details Guards them against silently becoming so. If I2C_BUSBUSY were ever
 *          zero, the condition at i2c.c:237 and its five siblings would always
 *          take the transfer arm, and the six cases above would then be
 *          asserting against a transfer path their mocks do not describe. This
 *          asserts the precondition directly so that such a failure is named
 *          here rather than surfacing as a confusing mock mismatch elsewhere.
 */
void testI2C_busBusy_bitIsNonZero(void) {
    TEST_ASSERT_NOT_EQUAL_MESSAGE(
        0u, (uint32_t)I2C_BUSBUSY, "I2C_BUSBUSY is zero: the bus-busy gate cannot be exercised");

    i2cBASE_t busy = {0};
    i2cBASE_t idle = {0};

    TEST_I2CbusBusy_SetBusBusy(&busy);

    /* The exact condition the driver evaluates at i2c.c:237 and its five
     * siblings: false for a busy bus, true for an idle one. */
    TEST_ASSERT_EQUAL(0u, (uint32_t)((busy.STR & (uint32_t)I2C_BUSBUSY) == 0u));
    TEST_ASSERT_EQUAL(1u, (uint32_t)((idle.STR & (uint32_t)I2C_BUSBUSY) == 0u));
}
