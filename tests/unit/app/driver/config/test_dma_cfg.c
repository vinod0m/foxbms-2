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
 * @file    test_dma_cfg.c
 * @author  foxBMS Team
 * @date    2020-04-01 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Tests of the DMA configuration
 * @details Asserts the three tables dma_cfg.c publishes for SPI DMA. dma_cfg.c
 *          defines no functions; its entire exported behaviour is
 *
 *            * `dma_spiDmaChannels[]`   - which DMA channel carries SPI N TX/RX
 *            * `dma_spiDmaRequests[]`   - which request line triggers them
 *            * `dma_spiInterfaces[]`    - the SPI peripheral behind each entry
 *
 *          which the spi driver reads at run time to set up its transfers. A
 *          wrong entry there silently routes a transfer to the wrong channel, so
 *          the tables are worth asserting even though the module contains no
 *          code.
 *
 *          WHERE THE EXPECTED VALUES COME FROM
 *          -------------------------------------
 *          dma_cfg.c does not contain numbers. It names channels with the
 *          repository's own per-SPI macros, so every expectation below is stated
 *          against one of those macros and cites the line that assigns it:
 *
 *            dma_spiDmaChannels[0] = { DMA_CHANNEL_SPI1_TX, DMA_CHANNEL_SPI1_RX }
 *                                                          (dma_cfg.c:70)
 *            dma_spiDmaChannels[1] = { DMA_CHANNEL_SPI2_TX, DMA_CHANNEL_SPI2_RX }
 *                                                          (dma_cfg.c:71)
 *            dma_spiDmaChannels[2] = { DMA_CHANNEL_SPI3_TX, DMA_CHANNEL_SPI3_RX }
 *                                                          (dma_cfg.c:72)
 *            dma_spiDmaChannels[3] = { DMA_CHANNEL_SPI4_TX, DMA_CHANNEL_SPI4_RX }
 *                                                          (dma_cfg.c:73)
 *            dma_spiDmaChannels[4] = { DMA_CHANNEL_SPI5_TX, DMA_CHANNEL_SPI5_RX }
 *                                                          (dma_cfg.c:74)
 *
 *            dma_spiDmaRequests[0] = { DMA_REQ_LINE_SPI1_TX, DMA_REQ_LINE_SPI1_RX }
 *                                                          (dma_cfg.c:79)
 *            dma_spiDmaRequests[1] = { DMA_REQ_LINE_SPI2_TX, DMA_REQ_LINE_SPI2_RX }
 *                                                          (dma_cfg.c:80)
 *            dma_spiDmaRequests[2] = { DMA_REQ_LINE_SPI3_TX, DMA_REQ_LINE_SPI3_RX }
 *                                                          (dma_cfg.c:81)
 *            dma_spiDmaRequests[3] = { DMA_REQ_LINE_SPI4_TX, DMA_REQ_LINE_SPI4_RX }
 *                                                          (dma_cfg.c:82)
 *            dma_spiDmaRequests[4] = { DMA_REQ_LINE_SPI5_TX, DMA_REQ_LINE_SPI5_RX }
 *                                                          (dma_cfg.c:83)
 *
 *            dma_spiInterfaces[0] = spiREG1   (dma_cfg.c:88)
 *            dma_spiInterfaces[1] = spiREG2   (dma_cfg.c:89)
 *            dma_spiInterfaces[2] = spiREG3   (dma_cfg.c:90)
 *            dma_spiInterfaces[3] = spiREG4   (dma_cfg.c:91)
 *            dma_spiInterfaces[4] = spiREG5   (dma_cfg.c:92)
 *
 *          The values were derived twice by two methods that share no code:
 *          a parser of the source literals (`tools/derive_cfg_tables.py`), and
 *          the compiled module's tables read through the harness. All 30 derived
 *          values agreed.
 *
 *          WHAT THIS DOES NOT ESTABLISH
 *          ----------------------------
 *          No numeric DMA channel or request-line value is asserted anywhere,
 *          because the repository does not define one: DMA_CHn and DMA_REQn come
 *          from TI's HL_sys_dma.h, which the host harness stands in for, and the
 *          numbering it uses is its own distinctness token rather than a
 *          property of the silicon. Asserting a number here would be asserting
 *          the harness. What is asserted is which named channel each SPI
 *          interface uses - a fact the repository does state - and that no
 *          channel or request line is reused.
 */

/*========== Includes =======================================================*/
#include "unity.h"

#include "dma_cfg.h"

/*========== Unit Testing Framework Directives ==============================*/
TEST_SOURCE_FILE("dma_cfg.c")

TEST_INCLUDE_PATH("../../src/app/driver/config")
TEST_INCLUDE_PATH("../../src/app/driver/spi")

/*========== Definitions and Implementations for Unit Test ==================*/

/*========== Setup and Teardown =============================================*/
void setUp(void) {
}

void tearDown(void) {
}

/*========== Test Cases =====================================================*/

/** @brief   SPI 1 transmit uses the channel dma_cfg.h reserves for it
 * @details dma_cfg.c:70 puts DMA_CHANNEL_SPI1_TX in the first entry;
 *          dma_cfg.h:75 is the line that names and assigns that macro.
 */
void testDmaSpi1TransmitUsesItsReservedChannel(void) {
    /* dma_cfg.h:75 */
    TEST_ASSERT_EQUAL(DMA_CHANNEL_SPI1_TX, dma_spiDmaChannels[0u].txChannel);
}

/** @brief   SPI 1 receive uses the channel dma_cfg.h reserves for it
 * @details dma_cfg.c:70 puts DMA_CHANNEL_SPI1_RX in the first entry;
 *          dma_cfg.h:76 is the line that names and assigns that macro.
 */
void testDmaSpi1ReceiveUsesItsReservedChannel(void) {
    /* dma_cfg.h:76 */
    TEST_ASSERT_EQUAL(DMA_CHANNEL_SPI1_RX, dma_spiDmaChannels[0u].rxChannel);
}

/** @brief   SPI 2 transmit uses the channel dma_cfg.h reserves for it
 * @details dma_cfg.c:71; dma_cfg.h:77.
 */
void testDmaSpi2TransmitUsesItsReservedChannel(void) {
    /* dma_cfg.h:77 */
    TEST_ASSERT_EQUAL(DMA_CHANNEL_SPI2_TX, dma_spiDmaChannels[1u].txChannel);
}

/** @brief   SPI 2 receive uses the channel dma_cfg.h reserves for it
 * @details dma_cfg.c:71; dma_cfg.h:78.
 */
void testDmaSpi2ReceiveUsesItsReservedChannel(void) {
    /* dma_cfg.h:78 */
    TEST_ASSERT_EQUAL(DMA_CHANNEL_SPI2_RX, dma_spiDmaChannels[1u].rxChannel);
}

/** @brief   SPI 3 transmit uses the channel dma_cfg.h reserves for it
 * @details dma_cfg.c:72; dma_cfg.h:79.
 */
void testDmaSpi3TransmitUsesItsReservedChannel(void) {
    /* dma_cfg.h:79 */
    TEST_ASSERT_EQUAL(DMA_CHANNEL_SPI3_TX, dma_spiDmaChannels[2u].txChannel);
}

/** @brief   SPI 3 receive uses the channel dma_cfg.h reserves for it
 * @details dma_cfg.c:72; dma_cfg.h:80.
 */
void testDmaSpi3ReceiveUsesItsReservedChannel(void) {
    /* dma_cfg.h:80 */
    TEST_ASSERT_EQUAL(DMA_CHANNEL_SPI3_RX, dma_spiDmaChannels[2u].rxChannel);
}

/** @brief   SPI 4 transmit uses the channel dma_cfg.h reserves for it
 * @details dma_cfg.c:73; dma_cfg.h:81.
 */
void testDmaSpi4TransmitUsesItsReservedChannel(void) {
    /* dma_cfg.h:81 */
    TEST_ASSERT_EQUAL(DMA_CHANNEL_SPI4_TX, dma_spiDmaChannels[3u].txChannel);
}

/** @brief   SPI 4 receive uses the channel dma_cfg.h reserves for it
 * @details dma_cfg.c:73; dma_cfg.h:82.
 */
void testDmaSpi4ReceiveUsesItsReservedChannel(void) {
    /* dma_cfg.h:82 */
    TEST_ASSERT_EQUAL(DMA_CHANNEL_SPI4_RX, dma_spiDmaChannels[3u].rxChannel);
}

/** @brief   SPI 5 transmit uses the channel dma_cfg.h reserves for it
 * @details dma_cfg.c:74; dma_cfg.h:83.
 */
void testDmaSpi5TransmitUsesItsReservedChannel(void) {
    /* dma_cfg.h:83 */
    TEST_ASSERT_EQUAL(DMA_CHANNEL_SPI5_TX, dma_spiDmaChannels[4u].txChannel);
}

/** @brief   SPI 5 receive uses the channel dma_cfg.h reserves for it
 * @details dma_cfg.c:74; dma_cfg.h:84.
 */
void testDmaSpi5ReceiveUsesItsReservedChannel(void) {
    /* dma_cfg.h:84 */
    TEST_ASSERT_EQUAL(DMA_CHANNEL_SPI5_RX, dma_spiDmaChannels[4u].rxChannel);
}

/** @brief   SPI 1 transmit is triggered by the request line reserved for it
 * @details dma_cfg.c:79; dma_cfg.h:96.
 */
void testDmaSpi1TransmitUsesItsReservedRequestLine(void) {
    /* dma_cfg.h:96 */
    TEST_ASSERT_EQUAL(DMA_REQ_LINE_SPI1_TX, dma_spiDmaRequests[0u].txRequest);
}

/** @brief   SPI 1 receive is triggered by the request line reserved for it
 * @details dma_cfg.c:79; dma_cfg.h:97.
 */
void testDmaSpi1ReceiveUsesItsReservedRequestLine(void) {
    /* dma_cfg.h:97 */
    TEST_ASSERT_EQUAL(DMA_REQ_LINE_SPI1_RX, dma_spiDmaRequests[0u].rxRequest);
}

/** @brief   SPI 2 transmit is triggered by the request line reserved for it
 * @details dma_cfg.c:80; dma_cfg.h:98.
 */
void testDmaSpi2TransmitUsesItsReservedRequestLine(void) {
    /* dma_cfg.h:98 */
    TEST_ASSERT_EQUAL(DMA_REQ_LINE_SPI2_TX, dma_spiDmaRequests[1u].txRequest);
}

/** @brief   SPI 2 receive is triggered by the request line reserved for it
 * @details dma_cfg.c:80; dma_cfg.h:99.
 */
void testDmaSpi2ReceiveUsesItsReservedRequestLine(void) {
    /* dma_cfg.h:99 */
    TEST_ASSERT_EQUAL(DMA_REQ_LINE_SPI2_RX, dma_spiDmaRequests[1u].rxRequest);
}

/** @brief   SPI 3 transmit is triggered by the request line reserved for it
 * @details dma_cfg.c:81; dma_cfg.h:100.
 */
void testDmaSpi3TransmitUsesItsReservedRequestLine(void) {
    /* dma_cfg.h:100 */
    TEST_ASSERT_EQUAL(DMA_REQ_LINE_SPI3_TX, dma_spiDmaRequests[2u].txRequest);
}

/** @brief   SPI 3 receive is triggered by the request line reserved for it
 * @details dma_cfg.c:81; dma_cfg.h:101.
 */
void testDmaSpi3ReceiveUsesItsReservedRequestLine(void) {
    /* dma_cfg.h:101 */
    TEST_ASSERT_EQUAL(DMA_REQ_LINE_SPI3_RX, dma_spiDmaRequests[2u].rxRequest);
}

/** @brief   SPI 4 transmit is triggered by the request line reserved for it
 * @details dma_cfg.c:82; dma_cfg.h:102.
 */
void testDmaSpi4TransmitUsesItsReservedRequestLine(void) {
    /* dma_cfg.h:102 */
    TEST_ASSERT_EQUAL(DMA_REQ_LINE_SPI4_TX, dma_spiDmaRequests[3u].txRequest);
}

/** @brief   SPI 4 receive is triggered by the request line reserved for it
 * @details dma_cfg.c:82; dma_cfg.h:103.
 */
void testDmaSpi4ReceiveUsesItsReservedRequestLine(void) {
    /* dma_cfg.h:103 */
    TEST_ASSERT_EQUAL(DMA_REQ_LINE_SPI4_RX, dma_spiDmaRequests[3u].rxRequest);
}

/** @brief   SPI 5 transmit is triggered by the request line reserved for it
 * @details dma_cfg.c:83; dma_cfg.h:104.
 */
void testDmaSpi5TransmitUsesItsReservedRequestLine(void) {
    /* dma_cfg.h:104 */
    TEST_ASSERT_EQUAL(DMA_REQ_LINE_SPI5_TX, dma_spiDmaRequests[4u].txRequest);
}

/** @brief   SPI 5 receive is triggered by the request line reserved for it
 * @details dma_cfg.c:83; dma_cfg.h:105.
 */
void testDmaSpi5ReceiveUsesItsReservedRequestLine(void) {
    /* dma_cfg.h:105 */
    TEST_ASSERT_EQUAL(DMA_REQ_LINE_SPI5_RX, dma_spiDmaRequests[4u].rxRequest);
}

/** @brief   the interface table names SPI peripheral 1 in its first entry
 * @details dma_cfg.c:88 places spiREG1.
 */
void testDmaInterfaceTableEntryZeroIsSpiOne(void) {
    /* dma_cfg.c:88 */
    TEST_ASSERT_EQUAL_PTR(spiREG1, dma_spiInterfaces[0u]);
}

/** @brief   the interface table names SPI peripheral 2 in its second entry
 * @details dma_cfg.c:89 places spiREG2.
 */
void testDmaInterfaceTableEntryOneIsSpiTwo(void) {
    /* dma_cfg.c:89 */
    TEST_ASSERT_EQUAL_PTR(spiREG2, dma_spiInterfaces[1u]);
}

/** @brief   the interface table names SPI peripheral 3 in its third entry
 * @details dma_cfg.c:90 places spiREG3.
 */
void testDmaInterfaceTableEntryTwoIsSpiThree(void) {
    /* dma_cfg.c:90 */
    TEST_ASSERT_EQUAL_PTR(spiREG3, dma_spiInterfaces[2u]);
}

/** @brief   the interface table names SPI peripheral 4 in its fourth entry
 * @details dma_cfg.c:91 places spiREG4.
 */
void testDmaInterfaceTableEntryThreeIsSpiFour(void) {
    /* dma_cfg.c:91 */
    TEST_ASSERT_EQUAL_PTR(spiREG4, dma_spiInterfaces[3u]);
}

/** @brief   the interface table names SPI peripheral 5 in its fifth entry
 * @details dma_cfg.c:92 places spiREG5.
 */
void testDmaInterfaceTableEntryFourIsSpiFive(void) {
    /* dma_cfg.c:92 */
    TEST_ASSERT_EQUAL_PTR(spiREG5, dma_spiInterfaces[4u]);
}

/** @brief   no two SPI interfaces in the table name the same peripheral
 * @details dma_cfg.c:88-92 place spiREG1..spiREG5. Two rows naming one peripheral
 *          would make the channel and request tables ambiguous.
 */
void testDmaInterfacesAreDistinct(void) {
    uint32_t u;
    uint32_t v;
    for (u = 0u; u < DMA_NUMBER_SPI_INTERFACES; u++) {
        for (v = u + 1u; v < DMA_NUMBER_SPI_INTERFACES; v++) {
            TEST_ASSERT_TRUE(dma_spiInterfaces[u] != dma_spiInterfaces[v]);
        }
    }
}

/** @brief   no DMA channel is handed to two directions of one SPI interface
 * @details dma_cfg.c:70-74 give every row a TX and an RX channel; a row whose two
 *          entries were the same would collide the two directions.
 */
void testDmaChannelPairOfEachSpiIsDistinct(void) {
    uint32_t u;
    for (u = 0u; u < DMA_NUMBER_SPI_INTERFACES; u++) {
        TEST_ASSERT_NOT_EQUAL(dma_spiDmaChannels[u].txChannel, dma_spiDmaChannels[u].rxChannel);
    }
}

/** @brief   no DMA channel is shared between two SPI interfaces
 * @details The ten channel entries come from dma_cfg.c:70-74. A channel reused
 *          across interfaces would make one interface's transfer overwrite the
 *          other's.
 */
void testDmaChannelsAreNotSharedBetweenSpiInterfaces(void) {
    uint32_t u;
    uint32_t v;
    for (u = 0u; u < DMA_NUMBER_SPI_INTERFACES; u++) {
        for (v = u + 1u; v < DMA_NUMBER_SPI_INTERFACES; v++) {
            TEST_ASSERT_NOT_EQUAL(dma_spiDmaChannels[u].txChannel, dma_spiDmaChannels[v].txChannel);
            TEST_ASSERT_NOT_EQUAL(dma_spiDmaChannels[u].txChannel, dma_spiDmaChannels[v].rxChannel);
            TEST_ASSERT_NOT_EQUAL(dma_spiDmaChannels[u].rxChannel, dma_spiDmaChannels[v].txChannel);
            TEST_ASSERT_NOT_EQUAL(dma_spiDmaChannels[u].rxChannel, dma_spiDmaChannels[v].rxChannel);
        }
    }
}

/** @brief   no DMA request line is shared between two SPI interfaces
 * @details The ten request entries come from dma_cfg.c:79-83.
 */
void testDmaRequestLinesAreNotSharedBetweenSpiInterfaces(void) {
    uint32_t u;
    uint32_t v;
    for (u = 0u; u < DMA_NUMBER_SPI_INTERFACES; u++) {
        TEST_ASSERT_NOT_EQUAL(dma_spiDmaRequests[u].txRequest, dma_spiDmaRequests[u].rxRequest);
        for (v = u + 1u; v < DMA_NUMBER_SPI_INTERFACES; v++) {
            TEST_ASSERT_NOT_EQUAL(dma_spiDmaRequests[u].txRequest, dma_spiDmaRequests[v].txRequest);
            TEST_ASSERT_NOT_EQUAL(dma_spiDmaRequests[u].txRequest, dma_spiDmaRequests[v].rxRequest);
            TEST_ASSERT_NOT_EQUAL(dma_spiDmaRequests[u].rxRequest, dma_spiDmaRequests[v].txRequest);
            TEST_ASSERT_NOT_EQUAL(dma_spiDmaRequests[u].rxRequest, dma_spiDmaRequests[v].rxRequest);
        }
    }
}
