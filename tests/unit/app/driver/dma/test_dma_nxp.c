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
 * @file    test_dma_nxp.c
 * @author  foxBMS Team
 * @date    2026-02-12 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Tests for the dma module
 * @details TODO
 *
 */

/* cspell:ignore CHCTRL ELDOFFSET ELSOFFSET FRSOFFSET */

/*========== Includes =======================================================*/
#include "unity.h"
#include "MockHL_i2c.h"
#include "MockHL_spi.h"
#include "MockHL_sys_dma.h"
#include "Mockafe_dma.h"
#include "Mocki2c.h"
#include "Mockio.h"
#include "Mockspi.h"
#include "Mocktask.h"

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

/*========== Setup and Teardown =============================================*/
/* This build has FOXBMS_AFE_DRIVER_NXP=1, so the SPI4 transmit-interrupt skip
 * at src/app/driver/dma/dma.c:208-:223 is compiled. Inside the loop
 * dma.c:214 asks SPI_GetSpiIndex(spiREG4) which index the slave SPI has, once
 * per SPI interface, and arms the block-transfer-complete interrupt on the
 * transmit channel only if this interface is NOT the slave (dma.c:214, :215-
 * :219). SPI_SPI4_INDEX is 3 (src/app/driver/config/spi_cfg.h:76), so the
 * transmit interrupt is armed four times, not five.
 *
 * The counts are taken in callbacks rather than in CMock's own <fn>_CallCount():
 * that counter is the number of calls ROUTED THROUGH A CALLBACK, so it reads 0
 * for a mock that was only satisfied from <fn>_Expect() registrations. An
 * AddCallback() is registered instead of a Stub(), because AddCallback leaves
 * CMock's argument, ordering and call-count checks in place, while a Stub()
 * returns from the mock before them. */
#define TEST_DMA_N_SPI ((uint32_t)DMA_NUMBER_SPI_INTERFACES)

/* dmaEnable(): one call, dma.c:194 */
#define TEST_DMA_N_ENABLE (1u)
/* SPI_GetSpiIndex(): once per SPI interface, dma.c:214 */
#define TEST_DMA_N_GET_SPI_INDEX TEST_DMA_N_SPI
/* dmaReqAssign(): two per SPI interface (dma.c:200, :202) plus two each for
 * I2C1 (:246, :248) and I2C2 (:273, :275) */
#define TEST_DMA_N_REQ_ASSIGN ((2u * TEST_DMA_N_SPI) + 4u)
/* dmaEnableInterrupt(): one transmit interrupt for every interface except the
 * slave SPI4 (dma.c:215-:219) plus one receive interrupt per interface
 * (dma.c:226-:227) plus three each for I2C1 (:253, :254, :255) and I2C2
 * (:280, :281, :282) */
#define TEST_DMA_N_ENABLE_INTR ((TEST_DMA_N_SPI - 1u) + TEST_DMA_N_SPI + 6u)
/* dmaSetCtrlPacket(): two per SPI interface (dma.c:233, :236) plus two each for
 * I2C1 (:261, :264) and I2C2 (:288, :291) */
#define TEST_DMA_N_CTRL_PACKET ((2u * TEST_DMA_N_SPI) + 4u)
/* dmaSetChEnable(): two per SPI interface (dma.c:239, :240) plus two each for
 * I2C1 (:267, :268) and I2C2 (:294, :295) */
#define TEST_DMA_N_CH_ENABLE ((2u * TEST_DMA_N_SPI) + 4u)

#define TEST_DMA_MAX_CTRL_PACKETS TEST_DMA_N_CTRL_PACKET

static uint32_t test_dmaCountEnable;
static uint32_t test_dmaCountReqAssign;
static uint32_t test_dmaCountEnableInterrupt;
static uint32_t test_dmaCountCtrlPacket;
static uint32_t test_dmaCountChEnable;
static uint32_t test_dmaCountGetSpiIndex;

static dmaChannel_t test_dmaPacketChannel[TEST_DMA_MAX_CTRL_PACKETS];
static g_dmaCTRL    test_dmaPacketValue[TEST_DMA_MAX_CTRL_PACKETS];

/* the transmit channels whose block-transfer-complete interrupt was armed */
static dmaChannel_t test_dmaIntrChannel[TEST_DMA_N_ENABLE_INTR];
static dmaInterrupt_t test_dmaIntrType[TEST_DMA_N_ENABLE_INTR];

static void dmaEnableCountCallback(int n) {
    (void)n;
    test_dmaCountEnable++;
}
static void dmaReqAssignCountCallback(dmaChannel_t channel, dmaRequest_t req, int n) {
    (void)channel;
    (void)req;
    (void)n;
    test_dmaCountReqAssign++;
}
static void dmaEnableInterruptCountCallback(
    dmaChannel_t channel,
    dmaInterrupt_t interrupt,
    dmaIntGroup_t intGroup,
    int n) {
    (void)intGroup;
    (void)n;
    TEST_ASSERT_LESS_THAN_UINT32(TEST_DMA_N_ENABLE_INTR, test_dmaCountEnableInterrupt);
    test_dmaIntrChannel[test_dmaCountEnableInterrupt] = channel;
    test_dmaIntrType[test_dmaCountEnableInterrupt]   = interrupt;
    test_dmaCountEnableInterrupt++;
}
static void dmaSetChEnableCountCallback(dmaChannel_t channel, dmaTriggerType_t trigger, int n) {
    (void)channel;
    (void)trigger;
    (void)n;
    test_dmaCountChEnable++;
}
static void dmaSetCtrlPacketRecordCallback(dmaChannel_t channel, g_dmaCTRL controlPacket, int n) {
    (void)n;
    TEST_ASSERT_LESS_THAN_UINT32(TEST_DMA_MAX_CTRL_PACKETS, test_dmaCountCtrlPacket);
    test_dmaPacketChannel[test_dmaCountCtrlPacket] = channel;
    test_dmaPacketValue[test_dmaCountCtrlPacket]  = controlPacket;
    test_dmaCountCtrlPacket++;
}
static uint8_t SPI_GetSpiIndexCountCallback(spiBASE_t *pNode, int n) {
    (void)n;
    TEST_ASSERT_EQUAL_PTR(spiREG4, pNode);
    test_dmaCountGetSpiIndex++;
    return SPI_SPI4_INDEX;
}

void setUp(void) {
    test_dmaCountEnable          = 0u;
    test_dmaCountReqAssign       = 0u;
    test_dmaCountEnableInterrupt = 0u;
    test_dmaCountCtrlPacket      = 0u;
    test_dmaCountChEnable        = 0u;
    test_dmaCountGetSpiIndex     = 0u;
    dmaEnable_AddCallback(dmaEnableCountCallback);
    dmaReqAssign_AddCallback(dmaReqAssignCountCallback);
    dmaEnableInterrupt_AddCallback(dmaEnableInterruptCountCallback);
    dmaSetChEnable_AddCallback(dmaSetChEnableCountCallback);
    dmaSetCtrlPacket_AddCallback(dmaSetCtrlPacketRecordCallback);
    SPI_GetSpiIndex_AddCallback(SPI_GetSpiIndexCountCallback);
}

void tearDown(void) {
}

/*========== Test Cases =====================================================*/

/** @brief   registers the exact HAL call sequence DMA_Initialize() makes, so
 *           every test case runs the same single code path
 * @details the sequence is the one already spelled out in this file, taken
 *          from src/app/driver/dma/dma.c: the SPI loop at :198-:241, I2C1 at
 *          :246-:268 and I2C2 at :273-:295. Keeping it in one helper means a
 *          change in the driver's order or arguments still fails every case.
 */
static void test_dmaExpectInitializationSequence(void) {

    /* DMA control packets configuration for SPI  */
    g_dmaCTRL dma_controlPacketSpiTx = {
        .SADD      = 0u,                               /* source address             */
        .DADD      = 0u,                               /* destination  address       */
        .CHCTRL    = 0u,                               /* channel chain control      */
        .FRCNT     = 0u,                               /* frame count                */
        .ELCNT     = 1u,                               /* element count              */
        .ELDOFFSET = 0u,                               /* element destination offset */
        .ELSOFFSET = 0u,                               /* element destination offset */
        .FRDOFFSET = 0u,                               /* frame destination offset   */
        .FRSOFFSET = 0u,                               /* frame destination offset   */
        .PORTASGN  = (uint32_t)PORTA_READ_PORTB_WRITE, /* port assignment            */
        .RDSIZE    = (uint32_t)ACCESS_16_BIT,          /* read size                  */
        .WRSIZE    = (uint32_t)ACCESS_16_BIT,          /* write size                 */
        .TTYPE     = (uint32_t)FRAME_TRANSFER,         /* transfer type              */
        .ADDMODERD = (uint32_t)ADDR_INC1,              /* address mode read          */
        .ADDMODEWR = (uint32_t)ADDR_FIXED,             /* address mode write         */
        .AUTOINIT  = (uint32_t)AUTOINIT_OFF            /* autoinit                   */
    };

    g_dmaCTRL dma_controlPacketSpiRx = {
        .SADD      = 0u,                               /* source address             */
        .DADD      = 0u,                               /* destination  address       */
        .CHCTRL    = 0u,                               /* channel chain control      */
        .FRCNT     = 0u,                               /* frame count                */
        .ELCNT     = 1u,                               /* element count              */
        .ELDOFFSET = 0u,                               /* element destination offset */
        .ELSOFFSET = 0u,                               /* element destination offset */
        .FRDOFFSET = 0u,                               /* frame destination offset   */
        .FRSOFFSET = 0u,                               /* frame destination offset   */
        .PORTASGN  = (uint32_t)PORTB_READ_PORTA_WRITE, /* port assignment            */
        .RDSIZE    = (uint32_t)ACCESS_16_BIT,          /* read size                  */
        .WRSIZE    = (uint32_t)ACCESS_16_BIT,          /* write size                 */
        .TTYPE     = (uint32_t)FRAME_TRANSFER,         /* transfer type              */
        .ADDMODERD = (uint32_t)ADDR_FIXED,             /* address mode read          */
        .ADDMODEWR = (uint32_t)ADDR_INC1,              /* address mode write         */
        .AUTOINIT  = (uint32_t)AUTOINIT_OFF            /* autoinit                   */
    };

    /* DMA control packets configuration for I2C1  */
    g_dmaCTRL dma_controlPacketI2cTx = {
        .SADD      = 0u,                               /* source address             */
        .DADD      = 0u,                               /* destination  address       */
        .CHCTRL    = 0u,                               /* channel chain control      */
        .FRCNT     = 0u,                               /* frame count                */
        .ELCNT     = 1u,                               /* element count              */
        .ELDOFFSET = 0u,                               /* element destination offset */
        .ELSOFFSET = 0u,                               /* element destination offset */
        .FRDOFFSET = 0u,                               /* frame destination offset   */
        .FRSOFFSET = 0u,                               /* frame destination offset   */
        .PORTASGN  = (uint32_t)PORTA_READ_PORTB_WRITE, /* port assignment            */
        .RDSIZE    = (uint32_t)ACCESS_8_BIT,           /* read size                  */
        .WRSIZE    = (uint32_t)ACCESS_8_BIT,           /* write size                 */
        .TTYPE     = (uint32_t)FRAME_TRANSFER,         /* transfer type              */
        .ADDMODERD = (uint32_t)ADDR_INC1,              /* address mode read          */
        .ADDMODEWR = (uint32_t)ADDR_FIXED,             /* address mode write         */
        .AUTOINIT  = (uint32_t)AUTOINIT_OFF            /* autoinit                   */
    };

    g_dmaCTRL dma_controlPacketI2cRx = {
        .SADD      = 0u,                               /* source address             */
        .DADD      = 0u,                               /* destination  address       */
        .CHCTRL    = 0u,                               /* channel chain control      */
        .FRCNT     = 0u,                               /* frame count                */
        .ELCNT     = 1u,                               /* element count              */
        .ELDOFFSET = 0u,                               /* element destination offset */
        .ELSOFFSET = 0u,                               /* element destination offset */
        .FRDOFFSET = 0u,                               /* frame destination offset   */
        .FRSOFFSET = 0u,                               /* frame destination offset   */
        .PORTASGN  = (uint32_t)PORTB_READ_PORTA_WRITE, /* port assignment            */
        .RDSIZE    = (uint32_t)ACCESS_8_BIT,           /* read size                  */
        .WRSIZE    = (uint32_t)ACCESS_8_BIT,           /* write size                 */
        .TTYPE     = (uint32_t)FRAME_TRANSFER,         /* transfer type              */
        .ADDMODERD = (uint32_t)ADDR_FIXED,             /* address mode read          */
        .ADDMODEWR = (uint32_t)ADDR_INC1,              /* address mode write         */
        .AUTOINIT  = (uint32_t)AUTOINIT_OFF            /* autoinit                   */
    };

    dmaEnable_Expect();

    /* Test SPI */

    for (uint8_t i = 0u; i < DMA_NUMBER_SPI_INTERFACES; i++) {
        dmaReqAssign_Expect(
            (dmaChannel_t)dma_spiDmaChannels[i].txChannel, (dmaRequest_t)dma_spiDmaRequests[i].txRequest);
        dmaReqAssign_Expect(
            (dmaChannel_t)dma_spiDmaChannels[i].rxChannel, (dmaRequest_t)dma_spiDmaRequests[i].rxRequest);
        /* dma.c:214 consults the slave node once per interface */
        SPI_GetSpiIndex_ExpectAndReturn(spiREG4, SPI_SPI4_INDEX);


        if (i != SPI_SPI4_INDEX) {
            dmaEnableInterrupt_Expect(
                (dmaChannel_t)(dmaChannel_t)dma_spiDmaChannels[i].txChannel,
                (dmaInterrupt_t)BTC,
                (dmaIntGroup_t)DMA_INTA);
        }

        dma_controlPacketSpiTx.DADD = (uint32_t)(&(dma_spiInterfaces[i]->DAT1)) + DMA_BIG_ENDIAN_ADDRESS_16BIT;
        dma_controlPacketSpiRx.SADD = (uint32_t)(&(dma_spiInterfaces[i]->BUF)) + DMA_BIG_ENDIAN_ADDRESS_16BIT;

        dmaEnableInterrupt_Expect(
            (dmaChannel_t)(dmaChannel_t)dma_spiDmaChannels[i].rxChannel, (dmaInterrupt_t)BTC, (dmaIntGroup_t)DMA_INTA);
        dmaSetCtrlPacket_Expect((dmaChannel_t)dma_spiDmaChannels[i].txChannel, dma_controlPacketSpiTx);
        dmaSetCtrlPacket_Expect((dmaChannel_t)dma_spiDmaChannels[i].rxChannel, dma_controlPacketSpiRx);
        dmaSetChEnable_Expect((dmaChannel_t)dma_spiDmaChannels[i].txChannel, (dmaTriggerType_t)DMA_HW);
        dmaSetChEnable_Expect((dmaChannel_t)dma_spiDmaChannels[i].rxChannel, (dmaTriggerType_t)DMA_HW);
    }

    /* Test I2C1 */

    dmaReqAssign_Expect((dmaChannel_t)DMA_CHANNEL_I2C1_TX, (dmaRequest_t)DMA_REQ_LINE_I2C1_TX);
    dmaReqAssign_Expect((dmaChannel_t)DMA_CHANNEL_I2C1_RX, (dmaRequest_t)DMA_REQ_LINE_I2C1_RX);
    dmaEnableInterrupt_Expect(
        (dmaChannel_t)(dmaChannel_t)DMA_CHANNEL_I2C1_TX, (dmaInterrupt_t)BTC, (dmaIntGroup_t)DMA_INTA);
    dmaEnableInterrupt_Expect(
        (dmaChannel_t)(dmaChannel_t)DMA_CHANNEL_I2C1_RX, (dmaInterrupt_t)BTC, (dmaIntGroup_t)DMA_INTA);
    dmaEnableInterrupt_Expect(
        (dmaChannel_t)(dmaChannel_t)DMA_CHANNEL_I2C1_RX, (dmaInterrupt_t)LFS, (dmaIntGroup_t)DMA_INTA);

    dma_controlPacketI2cTx.DADD = (uint32_t)(&(i2cREG1->DXR)) + DMA_BIG_ENDIAN_ADDRESS_8BIT;
    dma_controlPacketI2cRx.SADD = (uint32_t)(&(i2cREG1->DRR)) + DMA_BIG_ENDIAN_ADDRESS_8BIT;

    dmaSetCtrlPacket_Expect((dmaChannel_t)DMA_CHANNEL_I2C1_TX, dma_controlPacketI2cTx);
    dmaSetCtrlPacket_Expect((dmaChannel_t)DMA_CHANNEL_I2C1_RX, dma_controlPacketI2cRx);
    dmaSetChEnable_Expect((dmaChannel_t)DMA_CHANNEL_I2C1_TX, (dmaTriggerType_t)DMA_HW);
    dmaSetChEnable_Expect((dmaChannel_t)DMA_CHANNEL_I2C1_RX, (dmaTriggerType_t)DMA_HW);

    /* Test for I2C2 */

    dmaReqAssign_Expect((dmaChannel_t)DMA_CHANNEL_I2C2_TX, (dmaRequest_t)DMA_REQ_LINE_I2C2_TX);
    dmaReqAssign_Expect((dmaChannel_t)DMA_CHANNEL_I2C2_RX, (dmaRequest_t)DMA_REQ_LINE_I2C2_RX);

    dmaEnableInterrupt_Expect(
        (dmaChannel_t)(dmaChannel_t)DMA_CHANNEL_I2C2_TX, (dmaInterrupt_t)BTC, (dmaIntGroup_t)DMA_INTA);
    dmaEnableInterrupt_Expect(
        (dmaChannel_t)(dmaChannel_t)DMA_CHANNEL_I2C2_RX, (dmaInterrupt_t)BTC, (dmaIntGroup_t)DMA_INTA);
    dmaEnableInterrupt_Expect(
        (dmaChannel_t)(dmaChannel_t)DMA_CHANNEL_I2C2_RX, (dmaInterrupt_t)LFS, (dmaIntGroup_t)DMA_INTA);

    dma_controlPacketI2cTx.DADD = (uint32_t)(&(i2cREG2->DXR)) + DMA_BIG_ENDIAN_ADDRESS_8BIT;
    dma_controlPacketI2cRx.SADD = (uint32_t)(&(i2cREG2->DRR)) + DMA_BIG_ENDIAN_ADDRESS_8BIT;

    dmaSetCtrlPacket_Expect((dmaChannel_t)DMA_CHANNEL_I2C2_TX, dma_controlPacketI2cTx);
    dmaSetCtrlPacket_Expect((dmaChannel_t)DMA_CHANNEL_I2C2_RX, dma_controlPacketI2cRx);
    dmaSetChEnable_Expect((dmaChannel_t)DMA_CHANNEL_I2C2_TX, (dmaTriggerType_t)DMA_HW);
    dmaSetChEnable_Expect((dmaChannel_t)DMA_CHANNEL_I2C2_RX, (dmaTriggerType_t)DMA_HW);

}

void testDMA_Initialize(void) {
    test_dmaExpectInitializationSequence();
    DMA_Initialize();

    /* ======= test output verification ==================================== */
    /* dmaEnable() is called exactly once, dma.c:194 */
    TEST_ASSERT_EQUAL_UINT32(TEST_DMA_N_ENABLE, test_dmaCountEnable);
    /* SPI_GetSpiIndex(spiREG4) is asked once per SPI interface to find out
     * whether this interface is the slave node, dma.c:214 */
    TEST_ASSERT_EQUAL_UINT32(TEST_DMA_N_GET_SPI_INDEX, test_dmaCountGetSpiIndex);
    /* One dmaReqAssign() per DMA request line: Tx and Rx of every SPI
     * interface (dma.c:200, :202) plus Tx and Rx of I2C1 and I2C2 (dma.c:246,
     * :248, :273, :275). */
    TEST_ASSERT_EQUAL_UINT32(TEST_DMA_N_REQ_ASSIGN, test_dmaCountReqAssign);
    /* The transmit interrupt of the slave SPI4 is deliberately NOT armed
     * (dma.c:214, :215-:219), so there is one transmit interrupt fewer than
     * there are interfaces. */
    TEST_ASSERT_EQUAL_UINT32(TEST_DMA_N_ENABLE_INTR, test_dmaCountEnableInterrupt);
    /* One control packet per channel: Tx and Rx of every SPI interface
     * (dma.c:233, :236) plus Tx and Rx of I2C1 and I2C2 (dma.c:261, :264, :288,
     * :291). */
    TEST_ASSERT_EQUAL_UINT32(TEST_DMA_N_CTRL_PACKET, test_dmaCountCtrlPacket);
    /* One hardware trigger per channel, dma.c:239, :240, :267, :268, :294, :295 */
    TEST_ASSERT_EQUAL_UINT32(TEST_DMA_N_CH_ENABLE, test_dmaCountChEnable);
}

/** @brief   the transmit interrupt is skipped on exactly the slave SPI node
 * @details dma.c:214 skips dmaEnableInterrupt() on the transmit channel when the
 *          interface is the one SPI_GetSpiIndex(spiREG4) names, and the comment
 *          at dma.c:210-212 says why: the last word must be sent manually so
 *          that CSHOLD can be written, which a slave node must not do.
 *          The recorded interrupt channels are required to contain every
 *          transmit channel EXCEPT the one of SPI_SPI4_INDEX, and to contain
 *          every receive channel (dma.c:226-:227 arms those unconditionally).
 */
void testDMA_InitializeSkipsTheTransmitInterruptOnTheSlaveSpiNode(void) {
    test_dmaExpectInitializationSequence();
    DMA_Initialize();

    /* dma.c:215-:219 arms the transmit interrupt for i == 0, 1, 2 and 4 only */
    for (uint32_t i = 0u; i < TEST_DMA_N_SPI; i++) {
        bool transmitChannelArmed = false;
        for (uint32_t k = 0u; k < test_dmaCountEnableInterrupt; k++) {
            if ((test_dmaIntrChannel[k] == (dmaChannel_t)dma_spiDmaChannels[i].txChannel) &&
                (test_dmaIntrType[k] == (dmaInterrupt_t)BTC)) {
                transmitChannelArmed = true;
            }
        }
        if (i == SPI_SPI4_INDEX) {
            TEST_ASSERT_FALSE(transmitChannelArmed);
        } else {
            TEST_ASSERT_TRUE(transmitChannelArmed);
        }
    }

    /* dma.c:226-:227 arms the receive interrupt on every interface */
    for (uint32_t i = 0u; i < TEST_DMA_N_SPI; i++) {
        bool receiveChannelArmed = false;
        for (uint32_t k = 0u; k < test_dmaCountEnableInterrupt; k++) {
            if ((test_dmaIntrChannel[k] == (dmaChannel_t)dma_spiDmaChannels[i].rxChannel) &&
                (test_dmaIntrType[k] == (dmaInterrupt_t)BTC)) {
                receiveChannelArmed = true;
            }
        }
        TEST_ASSERT_TRUE(receiveChannelArmed);
    }
}

/** @brief   the SPI control packets are built from each interface's own
 *           registers, and the access width is 16 bit in both directions
 * @details dma.c:229 and :230 take the destination and the source from
 *          dma_spiInterfaces[i]; the 16 bit access and the fixed/moving
 *          address modes come from the initialiser at dma.c:105-111 and
 *          :124-130.
 */
void testDMA_InitializeSpiControlPacketsUseTheAddressOfEachInterface(void) {
    test_dmaExpectInitializationSequence();
    DMA_Initialize();

    for (uint32_t i = 0u; i < TEST_DMA_N_SPI; i++) {
        const g_dmaCTRL txPacket = test_dmaPacketValue[(2u * i)];
        const g_dmaCTRL rxPacket = test_dmaPacketValue[(2u * i) + 1u];

        TEST_ASSERT_EQUAL_UINT32(
            (uint32_t)dma_spiDmaChannels[i].txChannel, (uint32_t)test_dmaPacketChannel[(2u * i)]);
        TEST_ASSERT_EQUAL_UINT32(
            (uint32_t)dma_spiDmaChannels[i].rxChannel, (uint32_t)test_dmaPacketChannel[(2u * i) + 1u]);
        TEST_ASSERT_EQUAL_UINT32(
            (uint32_t)(&(dma_spiInterfaces[i]->DAT1)) + DMA_BIG_ENDIAN_ADDRESS_16BIT, txPacket.DADD);
        TEST_ASSERT_EQUAL_UINT32(
            (uint32_t)(&(dma_spiInterfaces[i]->BUF)) + DMA_BIG_ENDIAN_ADDRESS_16BIT, rxPacket.SADD);
        TEST_ASSERT_EQUAL_UINT32((uint32_t)ACCESS_16_BIT, txPacket.RDSIZE);
        TEST_ASSERT_EQUAL_UINT32((uint32_t)ACCESS_16_BIT, rxPacket.WRSIZE);
        TEST_ASSERT_EQUAL_UINT32((uint32_t)ADDR_INC1, txPacket.ADDMODERD);
        TEST_ASSERT_EQUAL_UINT32((uint32_t)ADDR_FIXED, txPacket.ADDMODEWR);
        TEST_ASSERT_EQUAL_UINT32((uint32_t)ADDR_FIXED, rxPacket.ADDMODERD);
        TEST_ASSERT_EQUAL_UINT32((uint32_t)ADDR_INC1, rxPacket.ADDMODEWR);
    }
}
