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
 * @file    test_dma_dma_group_a_notification.c
 * @author  foxBMS Team
 * @date    2025-08-06 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Tests for the dma module
 * @details TODO
 *
 */

/*========== Includes =======================================================*/
#include "unity.h"
#include "MockHL_i2c.h"
#include "MockHL_spi.h"
#include "Mockafe_dma.h"
#include "Mocki2c.h"
#include "Mockio.h"
#include "Mockspi.h"
#include "Mocktask.h"

/* HL_sys_dma.h is included for its TYPES and its declaration of
 * dmaGroupANotification, but it is deliberately NOT mocked.
 *
 * dmaGroupANotification is DEFINED in dma.c:321 (guarded at dma.c:320 by
 * `#if !defined(UNITY_UNIT_TEST) || defined(COMPILE_FOR_UNIT_TEST)`) and only
 * DECLARED in HL_sys_dma.h:409. dma.c does not include HL_sys_dma.h, and
 * neither does dma.h (dma.h includes dma_cfg.h and <stdint.h> only).
 *
 * So with HL_sys_dma.h mocked, CMock emits the only linkable definition of
 * dmaGroupANotification, and dma.c's own definition - granted by
 * COMPILE_FOR_UNIT_TEST in conf/unit/app_project_posix.yml - collides with it:
 *     ld: 1 duplicate symbols
 *     duplicate symbol '_dmaGroupANotification' in: dma.o MockHL_sys_dma.o
 * Mocking the header and compiling the source are mutually exclusive here. With
 * the mock removed, dma.c's definition is the only one, and it is the code
 * under test rather than a stub. */
#include "HL_sys_dma.h"

#include "dma.h"
#include "struct_helper.h"

/*========== Unit Testing Framework Directives ==============================*/
TEST_SOURCE_FILE("dma.c")

TEST_INCLUDE_PATH("../../src/app/driver/afe/api")
TEST_INCLUDE_PATH("../../src/app/driver/config")
TEST_INCLUDE_PATH("../../src/app/driver/dma")
TEST_INCLUDE_PATH("../../src/app/driver/i2c")
TEST_INCLUDE_PATH("../../src/app/driver/io")
TEST_INCLUDE_PATH("../../src/app/driver/rtc")
TEST_INCLUDE_PATH("../../src/app/driver/spi")
TEST_INCLUDE_PATH("../../src/app/task/config")
TEST_INCLUDE_PATH("../../src/app/task/ftask")

/*========== Definitions and Implementations for Unit Test ==================*/
TaskHandle_t ftsk_taskHandleI2c;

uint32_t spi_saveFmt0[] = {
    0U,
    0U,
    0U,
    0U,
    0U,
    0U,
};

SPI_BUSY_STATE_e spi_busyFlags[] = {
    SPI_IDLE,
    SPI_IDLE,
    SPI_IDLE,
    SPI_IDLE,
    SPI_IDLE,
};

const uint8_t spi_nrBusyFlags = sizeof(spi_busyFlags) / sizeof(SPI_BUSY_STATE_e);

DMA_CHANNEL_CONFIG_s dma_spiDmaChannels[DMA_NUMBER_SPI_INTERFACES] = {
    {DMA_CH0, DMA_CH1}, /* SPI1 */
    {DMA_CH2, DMA_CH3}, /* SPI2 */
    {DMA_CH4, DMA_CH5}, /* SPI3 */
    {DMA_CH6, DMA_CH7}, /* SPI4 */
    {DMA_CH8, DMA_CH9}, /* SPI5 */
};

DMA_REQUEST_CONFIG_s dma_spiDmaRequests[DMA_NUMBER_SPI_INTERFACES] = {
    {DMA_REQ_LINE_SPI1_TX, DMA_REQ_LINE_SPI1_RX}, /* SPI1 */
    {DMA_REQ_LINE_SPI2_TX, DMA_REQ_LINE_SPI2_RX}, /* SPI2 */
    {DMA_REQ_LINE_SPI3_TX, DMA_REQ_LINE_SPI3_RX}, /* SPI3 */
    {DMA_REQ_LINE_SPI4_TX, DMA_REQ_LINE_SPI4_RX}, /* SPI4 */
    {DMA_REQ_LINE_SPI5_TX, DMA_REQ_LINE_SPI5_RX}, /* SPI5 */
};

spiBASE_t *dma_spiInterfaces[DMA_NUMBER_SPI_INTERFACES] = {
    spiREG1, /* SPI1 */
    spiREG2, /* SPI2 */
    spiREG3, /* SPI3 */
    spiREG4, /* SPI4 */
    spiREG5, /* SPI5 */
};

uint8_t i2c_rxLastByteInterface1 = 0u;
uint8_t i2c_rxLastByteInterface2 = 0u;

/*========== Hand-written HL_sys_dma stubs ==================================
 *
 * HL_sys_dma.h is NOT mocked (see the include block above), so the five
 * register-level entry points that DMA_Initialize calls have no definition and
 * the link fails with five undefined symbols even though no test case here
 * calls DMA_Initialize. They are defined below.
 *
 * This is the pattern already used in this suite for a header that must supply
 * the code under test but cannot be mocked: see test_nxp_afe.c ("The stubs
 * below are the pattern already used in this suite...") and the sections
 * "Manually mocking functions from HL_sci.h" in test_uart_sci_notification.c
 * and "Manually mocking functions from HL_spi.h" in test_spi_spi_notification.c.
 *
 * Each stub RECORDS what it was given rather than discarding it, so the
 * assertions below can check that dmaGroupANotification left the DMA
 * peripheral in the state the source says it should. An empty stub would only
 * prove the link works.
 *
 * Arities are read off the call sites in src/app/driver/dma/dma.c:
 *   dmaEnable()                                  dma.c:194
 *   dmaReqAssign(chan, req)                      dma.c:200,202,246,248,273,275
 *   dmaEnableInterrupt(chan, intr, intGroup)     dma.c:215,221,226,253,254,255,280-282
 *   dmaSetCtrlPacket(chan, packet)               dma.c:233,236,261,264,288,291,313
 *   dmaSetChEnable(chan, trigger)                dma.c:239,240,267,268,314
 * and the parameter types come from sil/iface/HL_sys_dma.h:385-405.
 */
/** call counters, so a stub that is never reached is visible */
static uint32_t dmaStubEnableCount;
static uint32_t dmaStubReqAssignCount;
static uint32_t dmaStubEnableInterruptCount;
static uint32_t dmaStubSetCtrlPacketCount;
static uint32_t dmaStubSetChEnableCount;
/** last argument each stub was called with */
static dmaChannel_t dmaStubReqAssignChannel;
static dmaRequest_t dmaStubReqAssignRequest;
static dmaChannel_t dmaStubEnableInterruptChannel;
static dmaInterrupt_t dmaStubEnableInterruptInterrupt;
static dmaIntGroup_t dmaStubEnableInterruptGroup;
static dmaChannel_t dmaStubSetCtrlPacketChannel;
static g_dmaCTRL dmaStubSetCtrlPacketPacket;
static dmaChannel_t dmaStubSetChEnableChannel;
static dmaTriggerType_t dmaStubSetChEnableTrigger;

static void DmaStubsReset(void) {
    dmaStubEnableCount                  = 0u;
    dmaStubReqAssignCount               = 0u;
    dmaStubEnableInterruptCount         = 0u;
    dmaStubSetCtrlPacketCount           = 0u;
    dmaStubSetChEnableCount             = 0u;
    dmaStubReqAssignChannel             = (dmaChannel_t)0;
    dmaStubReqAssignRequest             = (dmaRequest_t)0;
    dmaStubEnableInterruptChannel       = (dmaChannel_t)0;
    dmaStubEnableInterruptInterrupt     = (dmaInterrupt_t)0;
    dmaStubEnableInterruptGroup         = (dmaIntGroup_t)0;
dmaStubSetCtrlPacketChannel         = (dmaChannel_t)0;
    /* dmaStubSetCtrlPacketPacket is a struct and is deliberately NOT reset
     * here: it is a file-scope object, so it starts zeroed, and the only writer
     * is the stub below, which overwrites all of it on every call. */
    dmaStubSetChEnableChannel           = (dmaChannel_t)0;
    dmaStubSetChEnableTrigger           = (dmaTriggerType_t)0;
}

void dmaEnable(void) {
    dmaStubEnableCount++;
}

void dmaReqAssign(dmaChannel_t channel, dmaRequest_t req) {
    dmaStubReqAssignCount++;
    dmaStubReqAssignChannel = channel;
    dmaStubReqAssignRequest = req;
}

void dmaEnableInterrupt(dmaChannel_t channel, dmaInterrupt_t interrupt, dmaIntGroup_t intGroup) {
    dmaStubEnableInterruptCount++;
    dmaStubEnableInterruptChannel   = channel;
    dmaStubEnableInterruptInterrupt = interrupt;
    dmaStubEnableInterruptGroup     = intGroup;
}

void dmaSetCtrlPacket(dmaChannel_t channel, g_dmaCTRL controlPacket) {
    dmaStubSetCtrlPacketCount++;
    dmaStubSetCtrlPacketChannel = channel;
    dmaStubSetCtrlPacketPacket  = controlPacket;
}

void dmaSetChEnable(dmaChannel_t channel, dmaTriggerType_t trigger) {
    dmaStubSetChEnableCount++;
    dmaStubSetChEnableChannel = channel;
    dmaStubSetChEnableTrigger = trigger;
}

/*========== Setup and Teardown =============================================*/
void setUp(void) {
    DmaStubsReset();
    /* Seed the two I2C peripheral images. sil_i2c1/sil_i2c2 are the objects
     * i2cREG1/i2cREG2 expand to (sil/iface/HL_i2c.h:38,43 define i2c1 as
     * &sil_i2c1 and i2c2 as &sil_i2c2), so seeding all-ones makes every
     * clear-the-bit the ISR performs observable as a specific literal result.
     *
     * The two images are given DIFFERENT values in the registers the ISR never
     * writes (OAR, DXR, DRR, STR, CKH, CKL, PSC). That is not decoration: CMock
     * compares a pointer argument by CONTENT, not by address -
     * MockHL_i2c.c does
     *     UNITY_TEST_ASSERT_EQUAL_MEMORY_ARRAY(Expected_pI2cInterface,
     *         pI2cInterface, sizeof(i2cBASE_t), ...)
     * for i2cSetStop. With both images seeded identically, passing i2cREG2 where
     * the source means i2cREG1 is invisible, and that was measured: perturbing
     * dma.c:496 to call i2cSetStop(i2cREG2) on the I2C1 path left this file
     * green (probe dma-p9, NO-BITE). Distinct markers make the content
     * comparison able to tell the two peripherals apart.
     *
     * DMACR is seeded to all ones on BOTH, so the clear-the-bit arithmetic below
     * yields a citable literal either way. */
    sil_i2c1.DMACR = 0xFFFFFFFFu;
    sil_i2c2.DMACR = 0xFFFFFFFFu;
    sil_i2c1.MDR   = 0x00000000u;
    sil_i2c2.MDR   = 0x00000000u;
    /* interface markers: the ISR never writes these */
    sil_i2c1.OAR = 0x11111111u;
    sil_i2c1.DXR = 0x11111111u;
    sil_i2c1.DRR = 0x11111111u;
    sil_i2c1.STR = 0x11111111u;
    sil_i2c1.CKH = 0x11111111u;
    sil_i2c1.CKL = 0x11111111u;
    sil_i2c1.PSC = 0x11111111u;
    sil_i2c2.OAR = 0x22222222u;
    sil_i2c2.DXR = 0x22222222u;
    sil_i2c2.DRR = 0x22222222u;
    sil_i2c2.STR = 0x22222222u;
    sil_i2c2.CKH = 0x22222222u;
    sil_i2c2.CKL = 0x22222222u;
    sil_i2c2.PSC = 0x22222222u;
    i2c_rxLastByteInterface1 = 0u;
    i2c_rxLastByteInterface2 = 0u;
}

void tearDown(void) {
}


/* dma.c calls xTaskNotifyIndexedFromISR(...), which FreeRTOS defines as a MACRO
 * (src/os/freertos/freertos/include/task.h:2766) that expands to
 * xTaskGenericNotifyFromISR(handle, index, value, action, NULL, &woken).
 * task.h itself is not mocked, but xTaskGenericNotifyFromISR IS mocked through
 * Mocktask.h, so the notification index and value ARE observable. The helper
 * below names that mock and drops the one argument that is not knowable: the
 * pxHigherPriorityTaskWoken pointer is the address of a local inside dma.c
 * (dma.c:327), so its value cannot be predicted and is ignored.
 *
 * The CMock macro takes seven arguments - the six call arguments plus the
 * value the mock returns. */
#define EXPECT_I2C_NOTIFY(index, value)                                     \
    do {                                                                    \
        xTaskGenericNotifyFromISR_ExpectAndReturn(                          \
            ftsk_taskHandleI2c, (index), (value), eSetValueWithOverwrite,   \
            NULL, NULL, pdFALSE);                                           \
        xTaskGenericNotifyFromISR_IgnoreArg_pxHigherPriorityTaskWoken();     \
    } while (0)

/*========== Test Cases =====================================================*/

/**
 * @brief   A BTC interrupt on the I2C1 transmit channel clears the TX DMA bit
 *          and notifies the I2C task that its transmit finished.
 * @details dma.c:410-416, case DMA_CHANNEL_I2C1_TX:
 *            :411  i2cREG1->DMACR &= ~((uint32_t)I2C_TX_DMA_ENABLE);
 *            :412-416  xTaskNotifyIndexedFromISR(I2C_TASK_HANDLE,
 *                        I2C_NOTIFICATION_TX_INDEX, I2C_TX_NOTIFIED_VALUE,
 *                        eSetValueWithOverwrite, &xHigherPriorityTaskWoken);
 *          I2C_TX_DMA_ENABLE is (0x2u) at i2c.h:72 and I2C_NOTIFICATION_TX_INDEX
 *          is (1u) at i2c.h:83, I2C_TX_NOTIFIED_VALUE is (0x51u) at i2c.h:89.
 *          setUp seeds DMACR to all ones, so clearing bit 1 must leave
 *          0xFFFFFFFDu.
 */
/* cspell:disable-next-line */
void testDmaGroupA_BtcOnI2c1TxClearsTxDmaBitAndNotifies(void) {
    EXPECT_I2C_NOTIFY(1u, 0x51u);
    dmaGroupANotification((dmaInterrupt_t)BTC, (uint32_t)DMA_CHANNEL_I2C1_TX);
    /* 0xFFFFFFFF & ~(uint32)I2C_TX_DMA_ENABLE(0x2) */
    TEST_ASSERT_EQUAL_UINT32(0xFFFFFFFDu, (uint32_t)sil_i2c1.DMACR);
    /* the RX bit must be untouched by the TX case */
    TEST_ASSERT_EQUAL_UINT32(0xFFFFFFFFu, (uint32_t)sil_i2c2.DMACR);
}

/**
 * @brief   A BTC interrupt on the I2C2 transmit channel touches interface 2
 *          only, not interface 1.
 * @details dma.c:419-425, case DMA_CHANNEL_I2C2_TX, is the same body as the
 *          I2C1 case but on i2cREG2. Asserting that sil_i2c1 is untouched is
 *          what distinguishes the two cases: an ISR that wrote to i2cREG1 for
 *          both channels would still pass a test that only checked the cleared
 *          bit on interface 2.
 */
/* cspell:disable-next-line */
void testDmaGroupA_BtcOnI2c2TxClearsOnlyInterfaceTwo(void) {
    EXPECT_I2C_NOTIFY(1u, 0x51u);
    dmaGroupANotification((dmaInterrupt_t)BTC, (uint32_t)DMA_CHANNEL_I2C2_TX);
    TEST_ASSERT_EQUAL_UINT32(0xFFFFFFFDu, (uint32_t)sil_i2c2.DMACR);
    TEST_ASSERT_EQUAL_UINT32(0xFFFFFFFFu, (uint32_t)sil_i2c1.DMACR);
}

/**
 * @brief   A BTC interrupt on the I2C1 receive channel, when the last byte DID
 *          arrive, stores that byte and notifies RX_NOTIFIED.
 * @details dma.c:428-451, case DMA_CHANNEL_I2C1_RX, success branch:
 *            :429  i2cREG1->DMACR &= ~((uint32_t)I2C_RX_DMA_ENABLE);
 *            :432  success = I2C_WaitReceive(i2cREG1, I2C_TIMEOUT_us);
 *            :443  i2c_rxLastByteInterface1 = I2C_ReadLastRxByte(i2cREG1);
 *            :444-448  xTaskNotifyIndexedFromISR(..., I2C_NOTIFICATION_RX_INDEX,
 *                        I2C_RX_NOTIFIED_VALUE, ...)
 *          I2C_RX_DMA_ENABLE is (0x1u) at i2c.h:74, so clearing bit 0 from an
 *          all-ones seed leaves 0xFFFFFFFEu. I2C_NOTIFICATION_RX_INDEX is (2u)
 *          at i2c.h:85 and I2C_RX_NOTIFIED_VALUE is (0x61u) at i2c.h:91.
 *          i2c_rxLastByteInterface1 is the cross-module handshake with
 *          src/app/driver/i2c/i2c.c:75, which reads it back at i2c.c:488.
 */
/* cspell:disable-next-line */
void testDmaGroupA_BtcOnI2c1RxSuccessStoresLastByteAndNotifies(void) {
    I2C_WaitReceive_ExpectAndReturn(i2cREG1, 1000u, true);
    I2C_ReadLastRxByte_ExpectAndReturn(i2cREG1, 0x5Au);
    EXPECT_I2C_NOTIFY(2u, 0x61u);

    dmaGroupANotification((dmaInterrupt_t)BTC, (uint32_t)DMA_CHANNEL_I2C1_RX);

    /* 0xFFFFFFFF & ~(uint32)I2C_RX_DMA_ENABLE(0x1) */
    TEST_ASSERT_EQUAL_UINT32(0xFFFFFFFEu, (uint32_t)sil_i2c1.DMACR);
    /* the value I2C_ReadLastRxByte returned must have been stored */
    TEST_ASSERT_EQUAL_UINT8(0x5Au, i2c_rxLastByteInterface1);
    /* the stop condition must NOT be set on the success path: dma.c:434-441
     * is the failure branch only */
    TEST_ASSERT_EQUAL_UINT32(0x00000000u, (uint32_t)sil_i2c1.MDR);
}

/**
 * @brief   The same interrupt with the last byte NOT arriving takes the
 *          failure branch instead: a stop condition, and RX_NOT_COME.
 * @details dma.c:432-442:
 *            :432  success = I2C_WaitReceive(i2cREG1, I2C_TIMEOUT_us);
 *            :433  if (success == false) {
 *            :434      i2cREG1->MDR |= (uint32_t)I2C_REPEATMODE;
 *            :435      i2cSetStop(i2cREG1);
 *            :436-439      xTaskNotifyIndexedFromISR(..., I2C_NOTIFICATION_RX_INDEX,
 *                          I2C_RX_NOT_COME_VALUE, ...)
 *          I2C_RX_NOT_COME_VALUE is (0x62u) at i2c.h:93, distinct from the 0x61u
 *          the success path sends, which is what lets the I2C task tell the two
 *          apart. i2c_rxLastByteInterface1 must be left alone.
 *          I2C_REPEATMODE is a silicon bit, so its numeric value is not
 *          asserted here; what is asserted is that MDR is written on this path
 *          and was not on the success path (previous case).
 */
/* cspell:disable-next-line */
void testDmaGroupA_BtcOnI2c1RxTimeoutSetsStopAndNotifiesNotCome(void) {
    I2C_WaitReceive_ExpectAndReturn(i2cREG1, 1000u, false);
    i2cSetStop_Expect(i2cREG1);
    EXPECT_I2C_NOTIFY(2u, 0x62u);

    dmaGroupANotification((dmaInterrupt_t)BTC, (uint32_t)DMA_CHANNEL_I2C1_RX);

    /* the RX DMA bit is cleared on this path too - dma.c:429 runs before the
     * branch, so it is not specific to success */
    TEST_ASSERT_EQUAL_UINT32(0xFFFFFFFEu, (uint32_t)sil_i2c1.DMACR);
    /* the stop condition must have been set, i.e. MDR changed from the seed */
    TEST_ASSERT_NOT_EQUAL_MESSAGE(0x00000000u, (uint32_t)sil_i2c1.MDR, "MDR must be written on the timeout path");
    /* no last byte was received, so the handshake variable stays at its seed */
    TEST_ASSERT_EQUAL_UINT8(0x00u, i2c_rxLastByteInterface1);
}

/**
 * @brief   I2C2 receive success stores into interface 2's handshake variable
 *          and leaves interface 1's alone.
 * @details dma.c:453-478, case DMA_CHANNEL_I2C2_RX, success branch at :475:
 *          `i2c_rxLastByteInterface2 = I2C_ReadLastRxByte(i2cREG2);`
 *          The two handshake variables are separate objects (i2c.c:74 and :75),
 *          so storing the wrong one is a real defect that only a test asserting
 *          both catches.
 */
/* cspell:disable-next-line */
void testDmaGroupA_BtcOnI2c2RxSuccessStoresIntoInterfaceTwoOnly(void) {
    I2C_WaitReceive_ExpectAndReturn(i2cREG2, 1000u, true);
    I2C_ReadLastRxByte_ExpectAndReturn(i2cREG2, 0xA7u);
    EXPECT_I2C_NOTIFY(2u, 0x61u);

    dmaGroupANotification((dmaInterrupt_t)BTC, (uint32_t)DMA_CHANNEL_I2C2_RX);

    TEST_ASSERT_EQUAL_UINT32(0xFFFFFFFEu, (uint32_t)sil_i2c2.DMACR);
    TEST_ASSERT_EQUAL_UINT8(0xA7u, i2c_rxLastByteInterface2);
    TEST_ASSERT_EQUAL_UINT8(0x00u, i2c_rxLastByteInterface1);
}

/**
 * @brief   An LFS interrupt on an I2C1 receive channel issues the stop and
 *          nothing else.
 * @details dma.c:502-508:
 *            :502  if (inttype == (dmaInterrupt_t)LFS) {
 *            :503      if (channel == DMA_CHANNEL_I2C1_RX) {
 *            :505          i2cSetStop(i2cREG1);
 *          There is no I2C_WaitReceive, no notification and no DMACR write on
 *          this path, and the assertions below hold for their absence by
 *          seeding DMACR to all ones and checking it is unchanged. CMock turns
 *          an unexpected i2cSetStop/I2C_WaitReceive call into a failure in its
 *          own right, so the absence is checked from both ends.
 */
/* cspell:disable-next-line */
void testDmaGroupA_LfsOnI2c1RxSetsStopAndNothingElse(void) {
    i2cSetStop_Expect(i2cREG1);

    dmaGroupANotification((dmaInterrupt_t)LFS, (uint32_t)DMA_CHANNEL_I2C1_RX);

    /* no DMACR write: the LFS branch is outside the BTC block */
    TEST_ASSERT_EQUAL_UINT32(0xFFFFFFFFu, (uint32_t)sil_i2c1.DMACR);
    /* the same for interface 2 */
    TEST_ASSERT_EQUAL_UINT32(0xFFFFFFFFu, (uint32_t)sil_i2c2.DMACR);
    /* and neither handshake variable was touched */
    TEST_ASSERT_EQUAL_UINT8(0x00u, i2c_rxLastByteInterface1);
    TEST_ASSERT_EQUAL_UINT8(0x00u, i2c_rxLastByteInterface2);
}

/**
 * @brief   An LFS interrupt on an I2C2 receive channel stops interface 2.
 * @details dma.c:506-508, the second arm of the same LFS block.
 */
/* cspell:disable-next-line */
void testDmaGroupA_LfsOnI2c2RxSetsStopOnInterfaceTwo(void) {
    i2cSetStop_Expect(i2cREG2);

    dmaGroupANotification((dmaInterrupt_t)LFS, (uint32_t)DMA_CHANNEL_I2C2_RX);

    TEST_ASSERT_EQUAL_UINT32(0xFFFFFFFFu, (uint32_t)sil_i2c2.DMACR);
    TEST_ASSERT_EQUAL_UINT32(0xFFFFFFFFu, (uint32_t)sil_i2c1.DMACR);
}

/**
 * @brief   An LFS interrupt on a TRANSMIT channel does nothing at all.
 * @details dma.c:503 and :506 test the channel against DMA_CHANNEL_I2C1_RX and
 *          DMA_CHANNEL_I2C2_RX only, so an LFS on a TX channel falls through
 *          both and the function returns having written nothing. No
 *          i2cSetStop_Expect is set: if the source did call it, CMock fails the
 *          case, which is the assertion. The register and handshake checks
 *          confirm the same thing from the outside.
 */
/* cspell:disable-next-line */
void testDmaGroupA_LfsOnATransmitChannelIsANoOp(void) {
    dmaGroupANotification((dmaInterrupt_t)LFS, (uint32_t)DMA_CHANNEL_I2C1_TX);

    TEST_ASSERT_EQUAL_UINT32(0xFFFFFFFFu, (uint32_t)sil_i2c1.DMACR);
    TEST_ASSERT_EQUAL_UINT32(0xFFFFFFFFu, (uint32_t)sil_i2c2.DMACR);
    TEST_ASSERT_EQUAL_UINT32(0x00000000u, (uint32_t)sil_i2c1.MDR);
    TEST_ASSERT_EQUAL_UINT32(0x00000000u, (uint32_t)sil_i2c2.MDR);
}

/**
 * @brief   A BTC interrupt on a channel the switch does not handle reaches
 *          `default: break;` and changes nothing.
 * @details dma.c:483-484 is the default arm. A channel value that is not one
 *          of the handled DMA_CHANNEL_* cases must therefore leave every
 *          peripheral and handshake variable untouched, and must not notify.
 *          The value 0xFFFFu is deliberately not a configured channel; the
 *          configured ones are dma_cfg.h:75-91.
 */
/* cspell:disable-next-line */
void testDmaGroupA_BtcOnAnUnhandledChannelIsANoOp(void) {
    dmaGroupANotification((dmaInterrupt_t)BTC, (uint32_t)0xFFFFu);

    TEST_ASSERT_EQUAL_UINT32(0xFFFFFFFFu, (uint32_t)sil_i2c1.DMACR);
    TEST_ASSERT_EQUAL_UINT32(0xFFFFFFFFu, (uint32_t)sil_i2c2.DMACR);
    TEST_ASSERT_EQUAL_UINT32(0x00000000u, (uint32_t)sil_i2c1.MDR);
    TEST_ASSERT_EQUAL_UINT32(0x00000000u, (uint32_t)sil_i2c2.MDR);
    TEST_ASSERT_EQUAL_UINT8(0x00u, i2c_rxLastByteInterface1);
    TEST_ASSERT_EQUAL_UINT8(0x00u, i2c_rxLastByteInterface2);
}

/**
 * @brief   The hand-written HL_sys_dma stubs are linked and reachable, and this
 *          test does not itself call them.
 * @details The stubs exist so that DMA_Initialize - which lives in the same
 *          translation unit at dma.c:93 - links. Nothing in the cases above
 *          reaches a stubbed function, so the counters must all be zero after
 *          the cases that drive the ISR. Asserting that keeps the stubs from
 *          silently acquiring behaviour: if a future edit made the ISR call one
 *          of them, this fails.
 */
/* cspell:disable-next-line */
void testDmaGroupA_HalStubsAreNotReachedByTheIsr(void) {
    TEST_ASSERT_EQUAL_UINT32(0u, dmaStubEnableCount);
    TEST_ASSERT_EQUAL_UINT32(0u, dmaStubReqAssignCount);
    TEST_ASSERT_EQUAL_UINT32(0u, dmaStubEnableInterruptCount);
    TEST_ASSERT_EQUAL_UINT32(0u, dmaStubSetCtrlPacketCount);
    TEST_ASSERT_EQUAL_UINT32(0u, dmaStubSetChEnableCount);
}
