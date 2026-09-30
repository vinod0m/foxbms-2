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
 * @file    test_ltc_afe_dma.c
 * @author  foxBMS Team
 * @date    2020-06-10 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Test of the ltc_afe_dma.c module in ltc
 * @details TODO
 *
 */

/*========== Includes =======================================================*/
#include "unity.h"
#include "MockHL_sys_dma.h"
#include "Mockfassert.h"
#include "Mockio.h"
#include "Mockltc.h"
#include "Mockspi.h"

#include "ltc_cfg.h"
#include "spi_cfg.h"

#include "ltc_afe_dma.h"

#include "test_assert_helper.h"

#include <stdbool.h>
#include <stdint.h>

/*========== Unit Testing Framework Directives ==============================*/
TEST_SOURCE_FILE("ltc_afe_dma.c")

TEST_INCLUDE_PATH("../../src/app/driver/afe/api")
TEST_INCLUDE_PATH("../../src/app/driver/afe/ltc/common")
TEST_INCLUDE_PATH("../../src/app/driver/afe/ltc/common/config")
TEST_INCLUDE_PATH("../../src/app/driver/config")
TEST_INCLUDE_PATH("../../src/app/driver/io")
TEST_INCLUDE_PATH("../../src/app/driver/spi")
TEST_INCLUDE_PATH("../../tests/unit/support")

/*========== Definitions and Implementations for Unit Test ==================*/
uint8_t ltc_RXPECbuffer[LTC_N_BYTES_FOR_DATA_TRANSMISSION] = {0};
uint8_t ltc_TXPECbuffer[LTC_N_BYTES_FOR_DATA_TRANSMISSION] = {0};

#define DMA_REQ_LINE_SPI1_TX (DMA_REQ1)
#define DMA_REQ_LINE_SPI1_RX (DMA_REQ0)
#define DMA_REQ_LINE_SPI2_TX (DMA_REQ3)
#define DMA_REQ_LINE_SPI2_RX (DMA_REQ2)
#define DMA_REQ_LINE_SPI3_TX (DMA_REQ15)
#define DMA_REQ_LINE_SPI3_RX (DMA_REQ14)

#define BIG_ENDIAN    (3u)
#define ELEMENT_COUNT (1u)

#define DMA_REQ_LINE_TX (DMA_REQ_LINE_SPI1_TX)
#define DMA_REQ_LINE_RX (DMA_REQ_LINE_SPI1_RX)

LTC_STATE_s ltc_stateBase = {
    .timer                   = 0,
    .statereq                = LTC_STATE_NO_REQUEST,
    .state                   = LTC_STATEMACH_UNINITIALIZED,
    .substate                = 0,
    .lastState               = LTC_STATEMACH_UNINITIALIZED,
    .lastSubstate            = 0,
    .adcModeRequest          = LTC_ADCMODE_FAST_DCP0,
    .adcMode                 = LTC_ADCMODE_FAST_DCP0,
    .adcMeasChannelRequest   = LTC_ADCMEAS_UNDEFINED,
    .adcMeasCh               = LTC_ADCMEAS_UNDEFINED,
    .numberOfMeasuredMux     = 32,
    .triggerentry            = 0,
    .ErrRetryCounter         = 0,
    .ErrRequestCounter       = 0,
    .VoltageSampleTime       = 0,
    .muxSampleTime           = 0,
    .commandDataTransferTime = 3,
    .commandTransferTime     = 3,
    .gpioClocksTransferTime  = 3,
    .muxmeas_seqptr          = NULL_PTR,
    .muxmeas_seqendptr       = NULL_PTR,
    .muxmeas_nr_end          = 0,
    .first_measurement_made  = false,
    .ltc_muxcycle_finished   = STD_NOT_OK,
    .check_spi_flag          = STD_NOT_OK,
    .balance_control_done    = STD_NOT_OK,
    .transmit_ongoing        = false,
    .dummyByte_ongoing       = STD_NOT_OK,
};

/* AFE_DmaCallback() compares the reported spi index against the index of the
 * SPI node the LTC is configured on (src/app/driver/afe/ltc/common/ltc_afe_dma.c:90-92),
 * so the fixture has to give ltc_stateBase a non-null SPI interface. */
SPI_INTERFACE_CONFIG_s test_ltcSpiInterface = {0};

/* - configuring dma control packets   */
g_dmaCTRL afe_ltcDmaControlPacketTx = {
    .SADD      = 0u,                                /* source address             */
    .DADD      = 0u,                                /* destination  address       */
    .CHCTRL    = 0U,                                /* channel control            */
    .FRCNT     = LTC_N_BYTES_FOR_DATA_TRANSMISSION, /* frame count                */
    .ELCNT     = ELEMENT_COUNT,                     /* element count              */
    .ELDOFFSET = 0U,                                /* element destination offset */
    .ELSOFFSET = 0U,                                /* element destination offset */
    .FRDOFFSET = 0U,                                /* frame destination offset   */
    .FRSOFFSET = 0U,                                /* frame destination offset   */
    .PORTASGN  = PORTA_READ_PORTB_WRITE,            /* port assignment            */
    .RDSIZE    = ACCESS_8_BIT,                      /* read size                  */
    .WRSIZE    = ACCESS_8_BIT,                      /* write size                 */
    .TTYPE     = FRAME_TRANSFER,                    /* transfer type              */
    .ADDMODERD = ADDR_INC1,                         /* address mode read          */
    .ADDMODEWR = ADDR_FIXED,                        /* address mode write         */
    .AUTOINIT  = AUTOINIT_OFF,                      /* autoinit                   */
};

g_dmaCTRL afe_ltcDmaControlPacketRx = {
    .SADD      = 0u,                                /* source address             */
    .DADD      = 0u,                                /* destination  address       */
    .CHCTRL    = 0U,                                /* channel control            */
    .FRCNT     = LTC_N_BYTES_FOR_DATA_TRANSMISSION, /* frame count                */
    .ELCNT     = ELEMENT_COUNT,                     /* element count              */
    .ELDOFFSET = 0U,                                /* element destination offset */
    .ELSOFFSET = 0U,                                /* element destination offset */
    .FRDOFFSET = 0U,                                /* frame destination offset   */
    .FRSOFFSET = 0U,                                /* frame destination offset   */
    .PORTASGN  = PORTB_READ_PORTA_WRITE,            /* port assignment            */
    .RDSIZE    = ACCESS_8_BIT,                      /* read size                  */
    .WRSIZE    = ACCESS_8_BIT,                      /* write size                 */
    .TTYPE     = FRAME_TRANSFER,                    /* transfer type              */
    .ADDMODERD = ADDR_FIXED,                        /* address mode read          */
    .ADDMODEWR = ADDR_INC1,                         /* address mode write         */
    .AUTOINIT  = AUTOINIT_OFF,                      /* autoinit                   */
};

/*========== Setup and Teardown =============================================*/
void setUp(void) {
    ltc_stateBase.transmit_ongoing      = false;
    ltc_stateBase.ltcData.pSpiInterface = &test_ltcSpiInterface;
}

void tearDown(void) {
}

/*========== Test Cases =====================================================*/
/** @brief   AFE_IsTransmitOngoing() rejects a null state (ltc_afe_dma.c:78) and
 *          otherwise reports the stored flag (:79)
 */
void testAFE_IsTransmitOngoing(void) {
    TEST_ASSERT_FAIL_ASSERT(AFE_IsTransmitOngoing(NULL_PTR));

    ltc_stateBase.transmit_ongoing = false;
    TEST_ASSERT_FALSE(AFE_IsTransmitOngoing(&ltc_stateBase));

    ltc_stateBase.transmit_ongoing = true;
    TEST_ASSERT_TRUE(AFE_IsTransmitOngoing(&ltc_stateBase));
}

/** @brief   AFE_SetTransmitOngoing() rejects a null state (ltc_afe_dma.c:83) and
 *          otherwise raises the flag and never lowers it (:84)
 */
void testAFE_SetTransmitOngoing(void) {
    TEST_ASSERT_FAIL_ASSERT(AFE_SetTransmitOngoing(NULL_PTR));

    ltc_stateBase.transmit_ongoing = false;
    AFE_SetTransmitOngoing(&ltc_stateBase);
    TEST_ASSERT_TRUE(AFE_IsTransmitOngoing(&ltc_stateBase));

    /* the setter only ever sets; a second call must not clear the flag */
    AFE_SetTransmitOngoing(&ltc_stateBase);
    TEST_ASSERT_TRUE(AFE_IsTransmitOngoing(&ltc_stateBase));
}

/** @brief   AFE_DmaCallback() only accepts the SPI index of SPI1 or SPI4
 *         (ltc_afe_dma.c:89) and clears the transmit flag only for the SPI node
 *         the LTC runs on (:90-92)
 */
void testAFE_DmaCallbackAcceptsOnlySpi1AndSpi4(void) {
    /* SPI_GetSpiIndex(spiREG1) and SPI_GetSpiIndex(spiREG4) are both evaluated
     * by the guard, so both are answered on every call */
    SPI_GetSpiIndex_ExpectAndReturn(spiREG1, 0u);
    SPI_GetSpiIndex_ExpectAndReturn(spiREG4, 1u);
    TEST_ASSERT_FAIL_ASSERT(AFE_DmaCallback(2u));
}

/** @brief   the completion interrupt of the SPI node the LTC runs on clears the
 *         transmit flag (ltc_afe_dma.c:90-92)
 * @details The LTC is configured on the node whose index SPI_GetSpiIndex()
 *          answers 0 here, and the reported completion index is 0, so the
 *          `if` in the module is taken.
 */
void testAFE_DmaCallbackClearsTransmitOngoingForConfiguredNode(void) {
    /* the guard compares against SPI1 first; that comparison succeeds, so the
     * SPI4 comparison is short-circuited away */
    SPI_GetSpiIndex_ExpectAndReturn(spiREG1, 0u);
    /* the `if` compares against the configured node, which also reports 0 */
    SPI_GetSpiIndex_ExpectAndReturn(test_ltcSpiInterface.pNode, 0u);

    ltc_stateBase.transmit_ongoing = true;
    AFE_DmaCallback(0u);
    TEST_ASSERT_FALSE(AFE_IsTransmitOngoing(&ltc_stateBase));
}

/** @brief   a completion interrupt of the other accepted SPI node leaves the
 *         transmit flag alone (ltc_afe_dma.c:89 passes, :91 does not match)
 */
void testAFE_DmaCallbackLeavesTransmitOngoingForOtherAcceptedNode(void) {
    /* SPI1 does not match the reported index 1, so SPI4 is evaluated and matches */
    SPI_GetSpiIndex_ExpectAndReturn(spiREG1, 0u);
    SPI_GetSpiIndex_ExpectAndReturn(spiREG4, 1u);
    /* the `if` compares index 1 against the configured node, which is 0 */
    SPI_GetSpiIndex_ExpectAndReturn(test_ltcSpiInterface.pNode, 0u);

    ltc_stateBase.transmit_ongoing = true;
    AFE_DmaCallback(1u);
    TEST_ASSERT_TRUE(AFE_IsTransmitOngoing(&ltc_stateBase));
}
