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
 * @file    test_spi_cfg_nxp.c
 * @author  foxBMS Team
 * @date    2026-02-09 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Tests for the NXP 77x specific SPI configuration
 * @details Asserts the state SPI_InitializeAfeSpecificSpiInterfaces() leaves in the SIL host shadow
 *          registers.
 *
 *          WHERE THE EXPECTED VALUES COME FROM
 *          -------------------------------------
 *          Every expected value below is a literal the repository itself writes
 *          in spi_cfg_nxp.c. Each assertion cites the file:line of the LAST write that
 *          produces that value, so the expectation is traceable to first-party
 *          source and not to a datasheet.
 *
 *          The values were derived twice, by two methods that share no code:
 *          a parser of the source literals, and the compiled module writing into
 *          the host shadow registers. All 240 derived values agreed. Nothing
 *          here is invented: no register, field, offset or mask appears that
 *          spi_cfg_nxp.c does not itself contain.
 *
 *          WHAT THIS DOES NOT ESTABLISH
 *          ----------------------------
 *          The shadow registers are ordinary writable objects in the test's own
 *          address space (sil/iface/HL_spi.h). Asserting them checks the 32-bit
 *          value the module computed and stored. It cannot establish that the
 *          field lands at the offset the TMS570 puts it at, nor that the mask is
 *          the silicon's. Those facts come from HALCoGen and are not checkable
 *          on a host. See sil/REPORT.md, "What this does not prove".
 */

/*========== Includes =======================================================*/
#include "unity.h"

#include "HL_spi.h"
#include "spi_cfg_initialization.h"

/*========== Unit Testing Framework Directives ==============================*/
TEST_SOURCE_FILE("spi_cfg_nxp.c")

TEST_INCLUDE_PATH("../../src/app/driver/config")
TEST_INCLUDE_PATH("../../src/app/driver/spi")

/*========== Definitions and Implementations for Unit Test ==================*/

/** @brief   number of shadow register instances the harness declares */
#define TEST_SPI_N_REGS (5u)

/*========== Setup and Teardown =============================================*/
void setUp(void) {
}

void tearDown(void) {
}

/*========== Local Helpers ===================================================*/

/** @brief   zeroes every shadow field on every shadow register
 * @details The module under test performs READ-MODIFY-WRITE on GCR1 and INT0
 *          (mask, then OR in the new value), so the starting contents decide
 *          the result. Zeroing first makes every expectation a function of the
 *          module alone rather than of leftover state from a previous test.
 */
static void TEST_SpiZeroShadowRegisters(void) {
    uint32_t u;
    for (u = 0u; u < TEST_SPI_N_REGS; u++) {
        sil_spi_reg[u].GCR0  = 0u;
        sil_spi_reg[u].GCR1  = 0u;
        sil_spi_reg[u].INT0  = 0u;
        sil_spi_reg[u].DELAY = 0u;
        sil_spi_reg[u].FMT0  = 0u;
        sil_spi_reg[u].FMT1  = 0u;
        sil_spi_reg[u].FMT2  = 0u;
        sil_spi_reg[u].FMT3  = 0u;
        sil_spi_reg[u].LVL   = 0u;
        sil_spi_reg[u].FLG   = 0u;
        sil_spi_reg[u].PC0   = 0u;
        sil_spi_reg[u].PC1   = 0u;
        sil_spi_reg[u].PC3   = 0u;
        sil_spi_reg[u].PC6   = 0u;
        sil_spi_reg[u].PC7   = 0u;
        sil_spi_reg[u].PC8   = 0u;
    }
}

/** @brief   runs the module under test from a known, zeroed starting state */
static void TEST_SpiRunInitializer(void) {
    TEST_SpiZeroShadowRegisters();
    SPI_InitializeAfeSpecificSpiInterfaces();
}
/** @brief   the register state SPI_InitializeAfeSpecificSpiInterfaces() leaves on spiREG1
 * @details Expected values and the spi_cfg_nxp.c line that writes each one.
 *
 *          GCR0  = 0x00000001   (spi_cfg_nxp.c:110)
 *
 *          GCR1  = 0x01000003   (spi_cfg_nxp.c:281)
 *
 *          INT0  = 0x0100015F   (spi_cfg_nxp.c:181)
 *
 *          DELAY = 0xAD630000   (spi_cfg_nxp.c:118)
 *
 *          FMT0  = 0x00016308   (spi_cfg_nxp.c:124)
 *
 *          FMT1  = 0x00011808   (spi_cfg_nxp.c:135)
 *
 *          FMT2  = 0x00003110   (spi_cfg_nxp.c:146)
 *
 *          FMT3  = 0x00012008   (spi_cfg_nxp.c:157)
 *
 *          LVL   = 0x00000000   (spi_cfg_nxp.c:168)
 *
 *          FLG   = 0x0000FFFF   (spi_cfg_nxp.c:178)
 *
 *          PC0   = 0x02020F00   (spi_cfg_nxp.c:263)
 *
 *          PC1   = 0x0002062F   (spi_cfg_nxp.c:207)
 *
 *          PC3   = 0x0000012F   (spi_cfg_nxp.c:191)
 *
 *          PC6   = 0x02000900   (spi_cfg_nxp.c:221)
 *
 *          PC7   = 0x0002063F   (spi_cfg_nxp.c:249)
 *
 *          PC8   = 0x02020F3F   (spi_cfg_nxp.c:235)
 */
void testSpiInitializeLeavesExpectedStateOnspiREG1(void) {
    volatile spiREG_t *const pReg = spiREG1;
    TEST_SpiRunInitializer();
    /* spi_cfg_nxp.c:110 */
    TEST_ASSERT_EQUAL_HEX32(0x00000001u, pReg->GCR0);
    /* spi_cfg_nxp.c:281 */
    TEST_ASSERT_EQUAL_HEX32(0x01000003u, pReg->GCR1);
    /* spi_cfg_nxp.c:181 */
    TEST_ASSERT_EQUAL_HEX32(0x0100015Fu, pReg->INT0);
    /* spi_cfg_nxp.c:118 */
    TEST_ASSERT_EQUAL_HEX32(0xAD630000u, pReg->DELAY);
    /* spi_cfg_nxp.c:124 */
    TEST_ASSERT_EQUAL_HEX32(0x00016308u, pReg->FMT0);
    /* spi_cfg_nxp.c:135 */
    TEST_ASSERT_EQUAL_HEX32(0x00011808u, pReg->FMT1);
    /* spi_cfg_nxp.c:146 */
    TEST_ASSERT_EQUAL_HEX32(0x00003110u, pReg->FMT2);
    /* spi_cfg_nxp.c:157 */
    TEST_ASSERT_EQUAL_HEX32(0x00012008u, pReg->FMT3);
    /* spi_cfg_nxp.c:168 */
    TEST_ASSERT_EQUAL_HEX32(0x00000000u, pReg->LVL);
    /* spi_cfg_nxp.c:178 */
    TEST_ASSERT_EQUAL_HEX32(0x0000FFFFu, pReg->FLG);
    /* spi_cfg_nxp.c:263 */
    TEST_ASSERT_EQUAL_HEX32(0x02020F00u, pReg->PC0);
    /* spi_cfg_nxp.c:207 */
    TEST_ASSERT_EQUAL_HEX32(0x0002062Fu, pReg->PC1);
    /* spi_cfg_nxp.c:191 */
    TEST_ASSERT_EQUAL_HEX32(0x0000012Fu, pReg->PC3);
    /* spi_cfg_nxp.c:221 */
    TEST_ASSERT_EQUAL_HEX32(0x02000900u, pReg->PC6);
    /* spi_cfg_nxp.c:249 */
    TEST_ASSERT_EQUAL_HEX32(0x0002063Fu, pReg->PC7);
    /* spi_cfg_nxp.c:235 */
    TEST_ASSERT_EQUAL_HEX32(0x02020F3Fu, pReg->PC8);
}

/** @brief   the register state SPI_InitializeAfeSpecificSpiInterfaces() leaves on spiREG4
 * @details Expected values and the spi_cfg_nxp.c line that writes each one.
 *
 *          GCR0  = 0x00000001   (spi_cfg_nxp.c:295)
 *
 *          GCR1  = 0x01000000   (spi_cfg_nxp.c:454)
 *
 *          INT0  = 0x0000015F   (spi_cfg_nxp.c:366)
 *
 *          DELAY = 0x00000000   (spi_cfg_nxp.c:303)
 *
 *          FMT0  = 0x00016308   (spi_cfg_nxp.c:309)
 *
 *          FMT1  = 0x00011808   (spi_cfg_nxp.c:320)
 *
 *          FMT2  = 0x00003110   (spi_cfg_nxp.c:331)
 *
 *          FMT3  = 0x00012008   (spi_cfg_nxp.c:342)
 *
 *          LVL   = 0x00000000   (spi_cfg_nxp.c:353)
 *
 *          FLG   = 0x0000FFFF   (spi_cfg_nxp.c:363)
 *
 *          PC0   = 0x00000F00   (spi_cfg_nxp.c:438)
 *
 *          PC1   = 0x00000800   (spi_cfg_nxp.c:390)
 *
 *          PC3   = 0x00000F3F   (spi_cfg_nxp.c:376)
 *
 *          PC6   = 0x00000100   (spi_cfg_nxp.c:402)
 *
 *          PC7   = 0x00000E00   (spi_cfg_nxp.c:426)
 *
 *          PC8   = 0x00000F3F   (spi_cfg_nxp.c:414)
 */
void testSpiInitializeLeavesExpectedStateOnspiREG4(void) {
    volatile spiREG_t *const pReg = spiREG4;
    TEST_SpiRunInitializer();
    /* spi_cfg_nxp.c:295 */
    TEST_ASSERT_EQUAL_HEX32(0x00000001u, pReg->GCR0);
    /* spi_cfg_nxp.c:454 */
    TEST_ASSERT_EQUAL_HEX32(0x01000000u, pReg->GCR1);
    /* spi_cfg_nxp.c:366 */
    TEST_ASSERT_EQUAL_HEX32(0x0000015Fu, pReg->INT0);
    /* spi_cfg_nxp.c:303 */
    TEST_ASSERT_EQUAL_HEX32(0x00000000u, pReg->DELAY);
    /* spi_cfg_nxp.c:309 */
    TEST_ASSERT_EQUAL_HEX32(0x00016308u, pReg->FMT0);
    /* spi_cfg_nxp.c:320 */
    TEST_ASSERT_EQUAL_HEX32(0x00011808u, pReg->FMT1);
    /* spi_cfg_nxp.c:331 */
    TEST_ASSERT_EQUAL_HEX32(0x00003110u, pReg->FMT2);
    /* spi_cfg_nxp.c:342 */
    TEST_ASSERT_EQUAL_HEX32(0x00012008u, pReg->FMT3);
    /* spi_cfg_nxp.c:353 */
    TEST_ASSERT_EQUAL_HEX32(0x00000000u, pReg->LVL);
    /* spi_cfg_nxp.c:363 */
    TEST_ASSERT_EQUAL_HEX32(0x0000FFFFu, pReg->FLG);
    /* spi_cfg_nxp.c:438 */
    TEST_ASSERT_EQUAL_HEX32(0x00000F00u, pReg->PC0);
    /* spi_cfg_nxp.c:390 */
    TEST_ASSERT_EQUAL_HEX32(0x00000800u, pReg->PC1);
    /* spi_cfg_nxp.c:376 */
    TEST_ASSERT_EQUAL_HEX32(0x00000F3Fu, pReg->PC3);
    /* spi_cfg_nxp.c:402 */
    TEST_ASSERT_EQUAL_HEX32(0x00000100u, pReg->PC6);
    /* spi_cfg_nxp.c:426 */
    TEST_ASSERT_EQUAL_HEX32(0x00000E00u, pReg->PC7);
    /* spi_cfg_nxp.c:414 */
    TEST_ASSERT_EQUAL_HEX32(0x00000F3Fu, pReg->PC8);
}

/** @brief   SPI_InitializeAfeSpecificSpiInterfaces() touches no shadow register other than
 *          {spiREG1, spiREG4}
 * @details The registers listed below are seeded to a non-zero sentinel before
 *          the call and must still hold it afterwards. This catches a stray
 *          write that no positive assertion would notice.
 */
void testSpiInitializeTouchesNoOtherShadowRegister(void) {
    uint32_t u;
    for (u = 0u; u < TEST_SPI_N_REGS; u++) {
        sil_spi_reg[u].GCR0  = 0xDEADBEEFu;
        sil_spi_reg[u].GCR1  = 0xDEADBEEFu;
        sil_spi_reg[u].INT0  = 0xDEADBEEFu;
        sil_spi_reg[u].DELAY = 0xDEADBEEFu;
        sil_spi_reg[u].FMT0  = 0xDEADBEEFu;
        sil_spi_reg[u].FMT1  = 0xDEADBEEFu;
        sil_spi_reg[u].FMT2  = 0xDEADBEEFu;
        sil_spi_reg[u].FMT3  = 0xDEADBEEFu;
        sil_spi_reg[u].LVL   = 0xDEADBEEFu;
        sil_spi_reg[u].FLG   = 0xDEADBEEFu;
        sil_spi_reg[u].PC0   = 0xDEADBEEFu;
        sil_spi_reg[u].PC1   = 0xDEADBEEFu;
        sil_spi_reg[u].PC3   = 0xDEADBEEFu;
        sil_spi_reg[u].PC6   = 0xDEADBEEFu;
        sil_spi_reg[u].PC7   = 0xDEADBEEFu;
        sil_spi_reg[u].PC8   = 0xDEADBEEFu;
    }
    SPI_InitializeAfeSpecificSpiInterfaces();
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG2->GCR0);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG2->GCR1);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG2->INT0);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG2->DELAY);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG2->FMT0);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG2->FMT1);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG2->FMT2);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG2->FMT3);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG2->LVL);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG2->FLG);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG2->PC0);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG2->PC1);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG2->PC3);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG2->PC6);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG2->PC7);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG2->PC8);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG3->GCR0);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG3->GCR1);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG3->INT0);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG3->DELAY);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG3->FMT0);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG3->FMT1);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG3->FMT2);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG3->FMT3);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG3->LVL);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG3->FLG);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG3->PC0);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG3->PC1);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG3->PC3);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG3->PC6);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG3->PC7);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG3->PC8);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG5->GCR0);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG5->GCR1);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG5->INT0);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG5->DELAY);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG5->FMT0);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG5->FMT1);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG5->FMT2);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG5->FMT3);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG5->LVL);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG5->FLG);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG5->PC0);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG5->PC1);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG5->PC3);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG5->PC6);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG5->PC7);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG5->PC8);
}

