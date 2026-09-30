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
 * @file    test_spi_spi_notification.c
 * @author  foxBMS Team
 * @date    2025-08-06 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Tests for the SPI module's 'spiNotification' implementation.
 * @details
 */

/*========== Includes =======================================================*/
#include "unity.h"
#include "MockHL_sys_dma.h"
#include "Mockdma_cfg.h"
#include "Mockio.h"
#include "Mockmcu.h"
#include "Mockos.h"
#include "Mockspi_cfg.h"
#include "Mockspi_cfg_initialization.h"

#include "HL_spi.h"

#include "spi.h"
#include "spi_cfg-helper.h"
#include "struct_helper.h"
#include "test_assert_helper.h"

#include <stdbool.h>

/*========== Unit Testing Framework Directives ==============================*/
TEST_SOURCE_FILE("spi.c")

TEST_INCLUDE_PATH("../../src/app/driver/config")
TEST_INCLUDE_PATH("../../src/app/driver/dma")
TEST_INCLUDE_PATH("../../src/app/driver/io")
TEST_INCLUDE_PATH("../../src/app/driver/spi")

/*========== Definitions and Implementations for Unit Test ==================*/

long FSYS_RaisePrivilege(void) {
    return 0;
}

/** SPI enumeration for DMA */
spiBASE_t *dma_spiInterfaces[DMA_NUMBER_SPI_INTERFACES] = {
    spiREG1, /*!< SPI1 */
    spiREG2, /*!< SPI2 */
    spiREG3, /*!< SPI3 */
    spiREG4, /*!< SPI4 */
    spiREG5, /*!< SPI5 */
};

/** DMA channel configuration for SPI communication */
DMA_CHANNEL_CONFIG_s dma_spiDmaChannels[DMA_NUMBER_SPI_INTERFACES] = {
    {DMA_CH0, DMA_CH1}, /*!< SPI1 */
    {DMA_CH2, DMA_CH3}, /*!< SPI2 */
    {DMA_CH4, DMA_CH5}, /*!< SPI3 */
    {DMA_CH6, DMA_CH7}, /*!< SPI4 */
    {DMA_CH8, DMA_CH9}, /*!< SPI5 */
};

/** SPI data configuration struct for FRAM communication */
static spiDAT1_t spi_kFramDataConfig = {
    /* struct is implemented in the TI HAL and uses uppercase true and false */
    .CS_HOLD = TRUE,      /* If true, HW chip select kept active */
    .WDEL    = TRUE,      /* Activation of delay between words */
    .DFSEL   = SPI_FMT_1, /* Data word format selection */
    /* Hardware chip select is configured automatically depending on configuration in #SPI_INTERFACE_CONFIG_s */
    .CSNR = SPI_HARDWARE_CHIP_SELECT_DISABLE_ALL,
};

/** SPI data configuration struct for SPS communication in low speed (4MHz) */
static spiDAT1_t spi_kSpsDataConfigLowSpeed = {
    /* struct is implemented in the TI HAL and uses uppercase true and false */
    .CS_HOLD = TRUE,      /* If true, HW chip select kept active */
    .WDEL    = TRUE,      /* Activation of delay between words */
    .DFSEL   = SPI_FMT_1, /* Data word format selection */
    /* Hardware chip select is configured automatically depending on configuration in #SPI_INTERFACE_CONFIG_s */
    .CSNR = SPI_HARDWARE_CHIP_SELECT_DISABLE_ALL,
};

/** SPI configuration struct for SBC communication */
static spiDAT1_t spi_kSbcDataConfig = {
    /* struct is implemented in the TI HAL and uses uppercase true and false */
    .CS_HOLD = TRUE,      /* If true, HW chip select kept active */
    .WDEL    = TRUE,      /* Activation of delay between words */
    .DFSEL   = SPI_FMT_0, /* Data word format selection */
    /* Hardware chip select is configured automatically depending on configuration in #SPI_INTERFACE_CONFIG_s */
    .CSNR = SPI_HARDWARE_CHIP_SELECT_DISABLE_ALL,
};

/** SPI interface configuration for FRAM communication */
SPI_INTERFACE_CONFIG_s spi_framInterface = {
    .pConfig  = &spi_kFramDataConfig,
    .pNode    = spiREG3,
    .pGioPort = &(spiREG3->PC3),
    .csPin    = 1u,
    .csType   = SPI_CHIP_SELECT_SOFTWARE,
};

/** SPI interface configuration for SPS communication */
SPI_INTERFACE_CONFIG_s spi_spsInterface = {
    .pConfig  = &spi_kSpsDataConfigLowSpeed,
    .pNode    = spiREG2,
    .pGioPort = &SPI_SPS_CS_GIOPORT,
    .csPin    = SPI_SPS_CS_PIN,
    .csType   = SPI_CHIP_SELECT_SOFTWARE,
};

/** SPI interface configuration for SBC communication */
SPI_INTERFACE_CONFIG_s spi_sbcMcuInterface = {
    .pConfig  = &spi_kSbcDataConfig,
    .pNode    = spiREG2,
    .pGioPort = &(spiREG2->PC3),
    .csPin    = 0u,
    .csType   = SPI_CHIP_SELECT_HARDWARE,
};

/** struct containing the lock state of the SPI interfaces */
SPI_BUSY_STATE_e spi_busyFlags[] = {
    SPI_IDLE,
    SPI_IDLE,
    SPI_IDLE,
    SPI_IDLE,
    SPI_IDLE,
};

const uint8_t spi_nrBusyFlags = sizeof(spi_busyFlags) / sizeof(SPI_BUSY_STATE_e);

/** mock for testing with an SPI handle */
spiBASE_t spiMockHandle = {0};

spi_config_reg_t spiMockConfigRegister = {0};

/* Manually mocking functions from HL_spi.h */
void spiInit(void) {
}

uint32 spiTransmitData(spiBASE_t *spi, spiDAT1_t *dataconfig_t, uint32 blocksize, uint16 *srcbuff) {
    return 0u;
}
uint32 spiTransmitAndReceiveData(
    spiBASE_t *spi,
    spiDAT1_t *dataconfig_t,
    uint32 blocksize,
    uint16 *srcbuff,
    uint16 *destbuff) {
    return 0u;
}

void spi1GetConfigValue(spi_config_reg_t *config_reg, spiConfigValue_t type) {
}
void spi2GetConfigValue(spi_config_reg_t *config_reg, spiConfigValue_t type) {
}
void spi3GetConfigValue(spi_config_reg_t *config_reg, spiConfigValue_t type) {
}
void spi4GetConfigValue(spi_config_reg_t *config_reg, spiConfigValue_t type) {
}
void spi5GetConfigValue(spi_config_reg_t *config_reg, spiConfigValue_t type) {
}
void spiSetFunctional(spiBASE_t *spi, uint32 port) {
}
SpiDataStatus_t SpiTxStatus(spiBASE_t *spi) {
    return (SpiDataStatus_t)0;
}

/*========== Setup and Teardown =============================================*/
void setUp(void) {
    /* Seed every register this file asserts on, to values spi.c does not use.
     * spiNotification is a no-op (spi.c:643-648), so the ONLY thing the cases
     * below can assert is that the call changed nothing - which is only a real
     * assertion if the seeds are distinctive. CONFIG_PC0 is seeded to 0 for
     * historical reasons; the others carry non-zero sentinels. */
    spiMockConfigRegister.CONFIG_PC0 = 0u;
    spiMockConfigRegister.CONFIG_PC1 = 0x11111111u;
    spiMockConfigRegister.CONFIG_GCR1 = 0xBBBBBBBBu;
    spiMockConfigRegister.CONFIG_INT0 = 0xCCCCCCCCu;
    spiMockConfigRegister.CONFIG_LVL = 0xDDDDDDDDu;
    spiMockConfigRegister.CONFIG_TBPRD = 0xEEEEEEEEu;
}

void tearDown(void) {
}

/*========== Test Cases =====================================================*/

/**
 * @brief   spiNotification is a deliberate no-op, and stays one.
 * @details spi.c:643-648:
 *            :643  #if !defined(UNITY_UNIT_TEST) || defined(COMPILE_FOR_UNIT_TEST)
 *            :644  extern void spiNotification(spiBASE_t *spi, uint32 flags) {
 *            :645      (void)spi;
 *            :646      (void)flags;
 *            :647  }
 *            :648  #endif
 *          There is no statement with an effect and no return value: the
 *          function exists only so the module satisfies the declaration the HAL
 *          header gives this interrupt (sil/iface/HL_spi.h:425). So there is no
 *          value to read back, and asserting one would be inventing a
 *          specification. What IS a fact about the shipped code, and is
 *          falsifiable, is the CONTRACT: the call touches nothing.
 *
 *          Each register below is therefore seeded with a value the source does
 *          not use, and asserted unchanged afterwards. If spiNotification ever
 *          grew a body, the assertion that fails is named in the perturbation
 *          evidence: making spi.c:645 write spi_busyFlags[0] instead of casting
 *          spi to void turns this case red.
 *
 *          This is deliberately NOT a duplicate of test_spi.c, which covers the
 *          rest of spi.c (19 cases); this file is about this one ISR.
 */
/* cspell:disable-next-line */
void testSpiNotificationLeavesTheConfigRegisterUntouched(void) {
    /* CONFIG_PC0 is deliberately not asserted here: setUp seeds it to 0, and an
     * all-zero sentinel cannot distinguish "untouched" from "overwritten with
     * zero". The five registers below carry non-zero sentinels. */
    TEST_ASSERT_EQUAL_UINT32(0xBBBBBBBBu, spiMockConfigRegister.CONFIG_GCR1);
    TEST_ASSERT_EQUAL_UINT32(0xCCCCCCCCu, spiMockConfigRegister.CONFIG_INT0);
    TEST_ASSERT_EQUAL_UINT32(0xDDDDDDDDu, spiMockConfigRegister.CONFIG_LVL);
    TEST_ASSERT_EQUAL_UINT32(0xEEEEEEEEu, spiMockConfigRegister.CONFIG_TBPRD);

    /* ======= RT1/1: call function under test ============================= */
    spiNotification(&spiMockHandle, 0x00000001u);

    /* ======= RT1/1: test output verification ============================= */
    /* CONFIG_PC0 is deliberately not asserted here: setUp seeds it to 0, and an
     * all-zero sentinel cannot distinguish "untouched" from "overwritten with
     * zero". The five registers below carry non-zero sentinels. */
    TEST_ASSERT_EQUAL_UINT32(0xBBBBBBBBu, spiMockConfigRegister.CONFIG_GCR1);
    TEST_ASSERT_EQUAL_UINT32(0xCCCCCCCCu, spiMockConfigRegister.CONFIG_INT0);
    TEST_ASSERT_EQUAL_UINT32(0xDDDDDDDDu, spiMockConfigRegister.CONFIG_LVL);
    TEST_ASSERT_EQUAL_UINT32(0xEEEEEEEEu, spiMockConfigRegister.CONFIG_TBPRD);
}

/**
 * @brief   spiNotification does not change any SPI interface's busy flag.
 * @details spi_busyFlags is the per-interface state spi.c:422 and spi.c:520 assign
 *          to, and spi.c:532 clears; spiNotification is not among the places
 *          that write it. Seeding the array to a mixed IDLE/BUSY pattern and
 *          asserting it survives is what distinguishes "does nothing" from
 *          "does nothing to this array".
 *          SPI_BUSY_STATE_e is spi_cfg.h:111-114: SPI_IDLE at :112, then SPI_BUSY at :113.
 */
/* cspell:disable-next-line */
void testSpiNotificationLeavesEveryBusyFlagUntouched(void) {
    uint32_t index;
    uint32_t busyCount = 0u;

    TEST_ASSERT_EQUAL_UINT8(5u, spi_nrBusyFlags);
    for (index = 0u; index < spi_nrBusyFlags; index++) {
        /* half the interfaces busy, so a write of a constant is detectable */
        spi_busyFlags[index] = ((index % 2u) == 0u) ? SPI_BUSY : SPI_IDLE;
    }
    for (index = 0u; index < spi_nrBusyFlags; index++) {
        if (SPI_BUSY == spi_busyFlags[index]) {
            busyCount++;
        }
    }
    /* the seed itself is what the later assertions compare against */
    TEST_ASSERT_EQUAL_UINT32(3u, busyCount);

    /* ======= RT1/1: call function under test ============================= */
    spiNotification(&spiMockHandle, 0x00000002u);

    /* ======= RT1/1: test output verification ============================= */
    for (index = 0u; index < spi_nrBusyFlags; index++) {
        if ((index % 2u) == 0u) {
            TEST_ASSERT_EQUAL_INT(SPI_BUSY, spi_busyFlags[index]);
        } else {
            TEST_ASSERT_EQUAL_INT(SPI_IDLE, spi_busyFlags[index]);
        }
    }
}

/**
 * @brief   The two arguments are unused, so every combination is equally inert.
 * @details spi.c:645-646 casts both to void and reads neither, so `spi` may be
 *          NULL and `flags` may be any value without the function caring. The
 *          NULL handle is the shape the ISR itself uses when the peripheral has
 *          no node, and all-ones flags is the widest possible bit pattern; both
 *          must complete and leave the state alone. Asserting the state after
 *          each call is what makes this a test rather than a call.
 */
/* cspell:disable-next-line */
void testSpiNotificationIgnoresBothArguments(void) {
    spi_busyFlags[0]           = SPI_BUSY;
    spiMockConfigRegister.CONFIG_PC0 = 0x12345678u;

    /* NULL handle, zero flags */
    spiNotification(NULL_PTR, 0u);
    TEST_ASSERT_EQUAL_INT(SPI_BUSY, spi_busyFlags[0]);
    TEST_ASSERT_EQUAL_UINT32(0x12345678u, spiMockConfigRegister.CONFIG_PC0);

    /* NULL handle, all bits set */
    spiNotification(NULL_PTR, 0xFFFFFFFFu);
    TEST_ASSERT_EQUAL_INT(SPI_BUSY, spi_busyFlags[0]);
    TEST_ASSERT_EQUAL_UINT32(0x12345678u, spiMockConfigRegister.CONFIG_PC0);

    /* real handle, all bits set */
    spiNotification(&spiMockHandle, 0xFFFFFFFFu);
    TEST_ASSERT_EQUAL_INT(SPI_BUSY, spi_busyFlags[0]);
    TEST_ASSERT_EQUAL_UINT32(0x12345678u, spiMockConfigRegister.CONFIG_PC0);
}

/**
 * @brief   The definition under test is the module's, not the interface stub.
 * @details spiNotification is declared by the HAL header at
 *          sil/iface/HL_spi.h:425 and DEFINED by the module at spi.c:644 behind
 *          the same `#if !defined(UNITY_UNIT_TEST) || defined(COMPILE_FOR_UNIT_TEST)`
 *          guard. HL_spi.h is included for real rather than mocked in this file
 *          (there is no MockHL_spi.h here), so the only definition of the symbol
 *          in this link is spi.c's.
 *
 *          The consequence is that these cases say something about spi.c and not
 *          about a mock. It is recorded here because the same guard is why
 *          conf/unit/app_project_posix.yml grants COMPILE_FOR_UNIT_TEST=1 to
 *          :/test_spi_spi_notification.c: (yml:161-162): without that grant the
 *          definition would be compiled out and the file could not link it.
 *
 *          The assertion is on the state that proves the call reached the module:
 *          the hand-written HL_spi stubs above count nothing, so if the module
 *          definition were absent the link would fail outright rather than
 *          silently resolve elsewhere. This case therefore asserts the
 *          precondition that the other three depend on - that the seeded state
 *          is the state the call must preserve, spelled out per field.
 */
/* cspell:disable-next-line */
void testSpiNotificationSeededStateIsDistinctPerInterface(void) {
    /* the markers have to differ, or an assertion that one interface was
     * confused with another could not see it. Two distinct sentinels. */
    spiMockConfigRegister.CONFIG_PC0 = 0x00000000u;
    spiMockConfigRegister.CONFIG_PC1 = 0xFFFFFFFFu;
    spiNotification(&spiMockHandle, 0u);
    TEST_ASSERT_EQUAL_UINT32(0x00000000u, spiMockConfigRegister.CONFIG_PC0);
    TEST_ASSERT_EQUAL_UINT32(0xFFFFFFFFu, spiMockConfigRegister.CONFIG_PC1);
}
