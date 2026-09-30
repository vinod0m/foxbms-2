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
 * @file    test_dma.c
 * @author  foxBMS Team
 * @date    2020-04-01 (date of creation)
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
/* Number of hardware calls DMA_Initialize() makes, read out of
 * src/app/driver/dma/dma.c. Only the ones this build compiles are counted;
 * the SCI4 block (:297-:317) needs FOXBMS_UART_SUPPORT and is covered by
 * test_dma_uart.c, the SPI4 transmit-interrupt skip (:208-:223) needs
 * FOXBMS_AFE_DRIVER_NXP and is covered by test_dma_nxp.c.
 *
 * The counts are taken in callbacks rather than in CMock's own
 * <fn>_CallCount(): that counter is the number of calls ROUTED THROUGH A
 * CALLBACK, so it reads 0 for a mock that was only satisfied from
 * <fn>_Expect() registrations. An AddCallback() is registered instead of a
 * Stub(), because AddCallback leaves CMock's argument, ordering and
 * call-count checks in place, while a Stub() returns from the mock before
 * them - so the strict _Expect chain below keeps being the oracle. */
#define TEST_DMA_N_SPI ((uint32_t)DMA_NUMBER_SPI_INTERFACES)

/* dmaEnable(): one call, src/app/driver/dma/dma.c:194 */
#define TEST_DMA_N_ENABLE (1u)
/* dmaReqAssign(): two per SPI interface (dma.c:200, :202) plus two each for
 * I2C1 (:246, :248) and I2C2 (:273, :275) */
#define TEST_DMA_N_REQ_ASSIGN ((2u * TEST_DMA_N_SPI) + 4u)
/* dmaEnableInterrupt(): two per SPI interface (dma.c:222, :227) plus three
 * each for I2C1 (:253, :254, :255) and I2C2 (:280, :281, :282) */
#define TEST_DMA_N_ENABLE_INTR ((2u * TEST_DMA_N_SPI) + 6u)
/* dmaSetCtrlPacket(): two per SPI interface (dma.c:233, :236) plus two each for
 * I2C1 (:261, :264) and I2C2 (:288, :291) */
#define TEST_DMA_N_CTRL_PACKET ((2u * TEST_DMA_N_SPI) + 4u)
/* dmaSetChEnable(): two per SPI interface (dma.c:239, :240) plus two each for
 * I2C1 (:267, :268) and I2C2 (:294, :295) */
#define TEST_DMA_N_CH_ENABLE ((2u * TEST_DMA_N_SPI) + 4u)

/* Highest number of control packets any single DMA_Initialize() hands over */
#define TEST_DMA_MAX_CTRL_PACKETS TEST_DMA_N_CTRL_PACKET

static uint32_t test_dmaCountEnable;
static uint32_t test_dmaCountReqAssign;
static uint32_t test_dmaCountEnableInterrupt;
static uint32_t test_dmaCountCtrlPacket;
static uint32_t test_dmaCountChEnable;

/* the control packets as the driver actually handed them to the HAL */
static dmaChannel_t test_dmaPacketChannel[TEST_DMA_MAX_CTRL_PACKETS];
static g_dmaCTRL    test_dmaPacketValue[TEST_DMA_MAX_CTRL_PACKETS];

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
    (void)channel;
    (void)interrupt;
    (void)intGroup;
    (void)n;
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

void setUp(void) {
    test_dmaCountEnable          = 0u;
    test_dmaCountReqAssign       = 0u;
    test_dmaCountEnableInterrupt = 0u;
    test_dmaCountCtrlPacket      = 0u;
    test_dmaCountChEnable        = 0u;
    dmaEnable_AddCallback(dmaEnableCountCallback);
    dmaReqAssign_AddCallback(dmaReqAssignCountCallback);
    dmaEnableInterrupt_AddCallback(dmaEnableInterruptCountCallback);
    dmaSetChEnable_AddCallback(dmaSetChEnableCountCallback);
    dmaSetCtrlPacket_AddCallback(dmaSetCtrlPacketRecordCallback);
}

void tearDown(void) {
}

/*========== Test Cases =====================================================*/

void testDMA_Initialize(void) {

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

        dmaEnableInterrupt_Expect(
            (dmaChannel_t)(dmaChannel_t)dma_spiDmaChannels[i].txChannel, (dmaInterrupt_t)BTC, (dmaIntGroup_t)DMA_INTA);

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

    DMA_Initialize();

    /* ======= test output verification ==================================== */
    /* How many times DMA_Initialize() switches the DMA peripheral on: exactly
     * once, from the single dmaEnable() at dma.c:194. */
    TEST_ASSERT_EQUAL_UINT32(TEST_DMA_N_ENABLE, test_dmaCountEnable);
    /* One dmaReqAssign() per DMA request line: the Tx and the Rx line of each
     * SPI interface (dma.c:200, :202) and the Tx and the Rx line of I2C1 and
     * I2C2 (dma.c:246, :248, :273, :275). */
    TEST_ASSERT_EQUAL_UINT32(TEST_DMA_N_REQ_ASSIGN, test_dmaCountReqAssign);
    /* One dmaEnableInterrupt() per interrupt that is armed: block-transfer-
     * complete on the Tx and on the Rx channel of every SPI interface
     * (dma.c:222, :227) and block-transfer-complete plus last-frame-sync on
     * the Rx channel plus block-transfer-complete on the Tx channel of I2C1
     * and I2C2 (dma.c:253, :254, :255, :280, :281, :282). */
    TEST_ASSERT_EQUAL_UINT32(TEST_DMA_N_ENABLE_INTR, test_dmaCountEnableInterrupt);
    /* One control packet per channel: the Tx and the Rx channel of every SPI
     * interface (dma.c:233, :236) and of I2C1 and I2C2 (dma.c:261, :264,
     * :288, :291). */
    TEST_ASSERT_EQUAL_UINT32(TEST_DMA_N_CTRL_PACKET, test_dmaCountCtrlPacket);
    /* One hardware trigger per channel, taken from dma.c:239, :240, :267,
     * :268, :294 and :295. */
    TEST_ASSERT_EQUAL_UINT32(TEST_DMA_N_CH_ENABLE, test_dmaCountChEnable);

    /* This build has no FOXBMS_AFE_DRIVER_NXP, so the only place that consults
     * SPI_GetSpiIndex() - the SPI4 transmit-interrupt skip at dma.c:214 - is
     * not compiled, and the function under test must not ask which SPI node is
     * the slave at all. */
    TEST_ASSERT_EQUAL_INT32(0, SPI_GetSpiIndex_CallCount());
}

/** @brief   the SPI transmit control packet takes its destination from the
 *           transmit data register of the interface it configures
 * @details dma.c:229 sets the destination of the SPI transmit packet to
 *          `&(dma_spiInterfaces[i]->DAT1) + DMA_BIG_ENDIAN_ADDRESS_16BIT`,
 *          the access sizes and the address modes come from the initialiser at
 *          dma.c:105-111.
 */
void testDMA_InitializeSpiTxPacketDestinationComesFromEachInterfacesDat1(void) {
    /* the strict _Expect chain of testDMA_Initialize() is reproduced here
     * without the per-argument structs, so the only thing asserted is what the
     * driver actually handed to the HAL */
    dmaEnable_Expect();
    for (uint32_t i = 0u; i < TEST_DMA_N_SPI; i++) {
        dmaReqAssign_Expect(
            (dmaChannel_t)dma_spiDmaChannels[i].txChannel, (dmaRequest_t)dma_spiDmaRequests[i].txRequest);
        dmaReqAssign_Expect(
            (dmaChannel_t)dma_spiDmaChannels[i].rxChannel, (dmaRequest_t)dma_spiDmaRequests[i].rxRequest);
        dmaEnableInterrupt_Expect(
            (dmaChannel_t)dma_spiDmaChannels[i].txChannel, (dmaInterrupt_t)BTC, (dmaIntGroup_t)DMA_INTA);
        dmaEnableInterrupt_Expect(
            (dmaChannel_t)dma_spiDmaChannels[i].rxChannel, (dmaInterrupt_t)BTC, (dmaIntGroup_t)DMA_INTA);
        g_dmaCTRL anyPacket = {0};
        /* the channel stays checked; the struct is left to the field-by-field
         * assertions below so that a wrong field is reported as a wrong field
         * and not as an opaque memory mismatch */
        dmaSetCtrlPacket_Expect((dmaChannel_t)dma_spiDmaChannels[i].txChannel, anyPacket);
        dmaSetCtrlPacket_IgnoreArg_controlPacket();
        dmaSetCtrlPacket_Expect((dmaChannel_t)dma_spiDmaChannels[i].rxChannel, anyPacket);
        dmaSetCtrlPacket_IgnoreArg_controlPacket();
        dmaSetChEnable_Expect((dmaChannel_t)dma_spiDmaChannels[i].txChannel, (dmaTriggerType_t)DMA_HW);
        dmaSetChEnable_Expect((dmaChannel_t)dma_spiDmaChannels[i].rxChannel, (dmaTriggerType_t)DMA_HW);
    }
    dmaReqAssign_Expect((dmaChannel_t)DMA_CHANNEL_I2C1_TX, (dmaRequest_t)DMA_REQ_LINE_I2C1_TX);
    dmaReqAssign_Expect((dmaChannel_t)DMA_CHANNEL_I2C1_RX, (dmaRequest_t)DMA_REQ_LINE_I2C1_RX);
    dmaEnableInterrupt_Expect(
        (dmaChannel_t)DMA_CHANNEL_I2C1_TX, (dmaInterrupt_t)BTC, (dmaIntGroup_t)DMA_INTA);
    dmaEnableInterrupt_Expect(
        (dmaChannel_t)DMA_CHANNEL_I2C1_RX, (dmaInterrupt_t)BTC, (dmaIntGroup_t)DMA_INTA);
    dmaEnableInterrupt_Expect(
        (dmaChannel_t)DMA_CHANNEL_I2C1_RX, (dmaInterrupt_t)LFS, (dmaIntGroup_t)DMA_INTA);
    g_dmaCTRL anyPacket = {0};
    dmaSetCtrlPacket_Expect((dmaChannel_t)DMA_CHANNEL_I2C1_TX, anyPacket);
    dmaSetCtrlPacket_IgnoreArg_controlPacket();
    dmaSetCtrlPacket_Expect((dmaChannel_t)DMA_CHANNEL_I2C1_RX, anyPacket);
    dmaSetCtrlPacket_IgnoreArg_controlPacket();
    dmaSetChEnable_Expect((dmaChannel_t)DMA_CHANNEL_I2C1_TX, (dmaTriggerType_t)DMA_HW);
    dmaSetChEnable_Expect((dmaChannel_t)DMA_CHANNEL_I2C1_RX, (dmaTriggerType_t)DMA_HW);

    dmaReqAssign_Expect((dmaChannel_t)DMA_CHANNEL_I2C2_TX, (dmaRequest_t)DMA_REQ_LINE_I2C2_TX);
    dmaReqAssign_Expect((dmaChannel_t)DMA_CHANNEL_I2C2_RX, (dmaRequest_t)DMA_REQ_LINE_I2C2_RX);
    dmaEnableInterrupt_Expect(
        (dmaChannel_t)DMA_CHANNEL_I2C2_TX, (dmaInterrupt_t)BTC, (dmaIntGroup_t)DMA_INTA);
    dmaEnableInterrupt_Expect(
        (dmaChannel_t)DMA_CHANNEL_I2C2_RX, (dmaInterrupt_t)BTC, (dmaIntGroup_t)DMA_INTA);
    dmaEnableInterrupt_Expect(
        (dmaChannel_t)DMA_CHANNEL_I2C2_RX, (dmaInterrupt_t)LFS, (dmaIntGroup_t)DMA_INTA);
    dmaSetCtrlPacket_Expect((dmaChannel_t)DMA_CHANNEL_I2C2_TX, anyPacket);
    dmaSetCtrlPacket_IgnoreArg_controlPacket();
    dmaSetCtrlPacket_Expect((dmaChannel_t)DMA_CHANNEL_I2C2_RX, anyPacket);
    dmaSetCtrlPacket_IgnoreArg_controlPacket();
    dmaSetChEnable_Expect((dmaChannel_t)DMA_CHANNEL_I2C2_TX, (dmaTriggerType_t)DMA_HW);
    dmaSetChEnable_Expect((dmaChannel_t)DMA_CHANNEL_I2C2_RX, (dmaTriggerType_t)DMA_HW);

    DMA_Initialize();

    /* two control packets per SPI interface, transmit first (dma.c:233, :236) */
    for (uint32_t i = 0u; i < TEST_DMA_N_SPI; i++) {
        const g_dmaCTRL txPacket = test_dmaPacketValue[(2u * i)];
        const g_dmaCTRL rxPacket = test_dmaPacketValue[(2u * i) + 1u];

        TEST_ASSERT_EQUAL_UINT32(
            (uint32_t)dma_spiDmaChannels[i].txChannel, (uint32_t)test_dmaPacketChannel[(2u * i)]);
        TEST_ASSERT_EQUAL_UINT32(
            (uint32_t)dma_spiDmaChannels[i].rxChannel, (uint32_t)test_dmaPacketChannel[(2u * i) + 1u]);

        /* the destination is the data register of THIS interface (dma.c:229) */
        TEST_ASSERT_EQUAL_UINT32(
            (uint32_t)(&(dma_spiInterfaces[i]->DAT1)) + DMA_BIG_ENDIAN_ADDRESS_16BIT, txPacket.DADD);
        /* the source is the buffer register of THIS interface (dma.c:230) */
        TEST_ASSERT_EQUAL_UINT32(
            (uint32_t)(&(dma_spiInterfaces[i]->BUF)) + DMA_BIG_ENDIAN_ADDRESS_16BIT, rxPacket.SADD);

        /* SPI works 16 bit wide in both directions (dma.c:106, :107, :125, :126) */
        TEST_ASSERT_EQUAL_UINT32((uint32_t)ACCESS_16_BIT, txPacket.RDSIZE);
        TEST_ASSERT_EQUAL_UINT32((uint32_t)ACCESS_16_BIT, txPacket.WRSIZE);
        TEST_ASSERT_EQUAL_UINT32((uint32_t)ACCESS_16_BIT, rxPacket.RDSIZE);
        TEST_ASSERT_EQUAL_UINT32((uint32_t)ACCESS_16_BIT, rxPacket.WRSIZE);

        /* transmit reads with a moving pointer and writes to a fixed one, the
         * receive packet is the other way round (dma.c:109, :110, :128, :129) */
        TEST_ASSERT_EQUAL_UINT32((uint32_t)PORTA_READ_PORTB_WRITE, txPacket.PORTASGN);
        TEST_ASSERT_EQUAL_UINT32((uint32_t)ADDR_INC1, txPacket.ADDMODERD);
        TEST_ASSERT_EQUAL_UINT32((uint32_t)ADDR_FIXED, txPacket.ADDMODEWR);
        TEST_ASSERT_EQUAL_UINT32((uint32_t)PORTB_READ_PORTA_WRITE, rxPacket.PORTASGN);
        TEST_ASSERT_EQUAL_UINT32((uint32_t)ADDR_FIXED, rxPacket.ADDMODERD);
        TEST_ASSERT_EQUAL_UINT32((uint32_t)ADDR_INC1, rxPacket.ADDMODEWR);

        /* single element, hardware triggered, no auto-initialisation
         * (dma.c:100, :108, :111) */
        TEST_ASSERT_EQUAL_UINT32(1u, txPacket.ELCNT);
        TEST_ASSERT_EQUAL_UINT32((uint32_t)FRAME_TRANSFER, txPacket.TTYPE);
        TEST_ASSERT_EQUAL_UINT32((uint32_t)AUTOINIT_OFF, txPacket.AUTOINIT);
    }
}

/** @brief   the I2C control packets take their registers from the interface
 *           they configure and work 8 bit wide
 * @details dma.c:257 and :258 use i2cREG1, dma.c:284 and :285 use i2cREG2; the
 *          8 bit access sizes come from dma.c:145, :146, :164 and :165.
 */
void testDMA_InitializeI2cPacketAddressesComeFromTheConfiguredInterface(void) {
    testDMA_InitializeSpiTxPacketDestinationComesFromEachInterfacesDat1();

    /* packets 0..(2*5-1) are the SPI ones (dma.c:233, :236), the I2C1 pair is
     * next (dma.c:261, :264) and the I2C2 pair after it (dma.c:288, :291) */
    const uint32_t i2c1Tx = (2u * TEST_DMA_N_SPI);
    const uint32_t i2c1Rx = (2u * TEST_DMA_N_SPI) + 1u;
    const uint32_t i2c2Tx = (2u * TEST_DMA_N_SPI) + 2u;
    const uint32_t i2c2Rx = (2u * TEST_DMA_N_SPI) + 3u;

    TEST_ASSERT_EQUAL_UINT32((uint32_t)DMA_CHANNEL_I2C1_TX, (uint32_t)test_dmaPacketChannel[i2c1Tx]);
    TEST_ASSERT_EQUAL_UINT32((uint32_t)DMA_CHANNEL_I2C1_RX, (uint32_t)test_dmaPacketChannel[i2c1Rx]);
    TEST_ASSERT_EQUAL_UINT32((uint32_t)DMA_CHANNEL_I2C2_TX, (uint32_t)test_dmaPacketChannel[i2c2Tx]);
    TEST_ASSERT_EQUAL_UINT32((uint32_t)DMA_CHANNEL_I2C2_RX, (uint32_t)test_dmaPacketChannel[i2c2Rx]);

    /* the transmit destination is the data register of the configured
     * interface (dma.c:257, :284) and the receive source its receive register
     * (dma.c:258, :285) */
    TEST_ASSERT_EQUAL_UINT32(
        (uint32_t)(&(i2cREG1->DXR)) + DMA_BIG_ENDIAN_ADDRESS_8BIT, test_dmaPacketValue[i2c1Tx].DADD);
    TEST_ASSERT_EQUAL_UINT32(
        (uint32_t)(&(i2cREG1->DRR)) + DMA_BIG_ENDIAN_ADDRESS_8BIT, test_dmaPacketValue[i2c1Rx].SADD);
    TEST_ASSERT_EQUAL_UINT32(
        (uint32_t)(&(i2cREG2->DXR)) + DMA_BIG_ENDIAN_ADDRESS_8BIT, test_dmaPacketValue[i2c2Tx].DADD);
    TEST_ASSERT_EQUAL_UINT32(
        (uint32_t)(&(i2cREG2->DRR)) + DMA_BIG_ENDIAN_ADDRESS_8BIT, test_dmaPacketValue[i2c2Rx].SADD);

    /* I2C works 8 bit wide in both directions (dma.c:145, :146, :164, :165) */
    TEST_ASSERT_EQUAL_UINT32((uint32_t)ACCESS_8_BIT, test_dmaPacketValue[i2c1Tx].RDSIZE);
    TEST_ASSERT_EQUAL_UINT32((uint32_t)ACCESS_8_BIT, test_dmaPacketValue[i2c1Tx].WRSIZE);
    TEST_ASSERT_EQUAL_UINT32((uint32_t)ACCESS_8_BIT, test_dmaPacketValue[i2c2Rx].RDSIZE);
    TEST_ASSERT_EQUAL_UINT32((uint32_t)ACCESS_8_BIT, test_dmaPacketValue[i2c2Rx].WRSIZE);
}
