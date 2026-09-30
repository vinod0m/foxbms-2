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
 * @file    test_spi_cfg_generic.c
 * @author  foxBMS Team
 * @date    2026-02-09 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Tests for the generic SPI2/SPI3/SPI5 specific SPI configuration
 * @details Asserts the state SPI_InitializeSpiInterfaces() leaves in the SIL host shadow
 *          registers.
 *
 *          WHERE THE EXPECTED VALUES COME FROM
 *          -------------------------------------
 *          Every expected value below is a literal the repository itself writes
 *          in spi_cfg_generic.c. Each assertion cites the file:line of the LAST write that
 *          produces that value, so the expectation is traceable to first-party
 *          source and not to a datasheet.
 *
 *          The values were derived twice, by two methods that share no code:
 *          a parser of the source literals, and the compiled module writing into
 *          the host shadow registers. All 240 derived values agreed. Nothing
 *          here is invented: no register, field, offset or mask appears that
 *          spi_cfg_generic.c does not itself contain.
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
TEST_SOURCE_FILE("spi_cfg_generic.c")

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
    SPI_InitializeSpiInterfaces();
}
/** @brief   the register state SPI_InitializeSpiInterfaces() leaves on spiREG2
 * @details Expected values and the spi_cfg_generic.c line that writes each one.
 *
 *          GCR0  = 0x00000001   (spi_cfg_generic.c:113)
 *
 *          GCR1  = 0x01000003   (spi_cfg_generic.c:247)
 *
 *          INT0  = 0x0100015F   (spi_cfg_generic.c:183)
 *
 *          DELAY = 0x00000000   (spi_cfg_generic.c:121)
 *
 *          FMT0  = 0x00000908   (spi_cfg_generic.c:127)
 *
 *          FMT1  = 0x00001810   (spi_cfg_generic.c:138)
 *
 *          FMT2  = 0x00000910   (spi_cfg_generic.c:148)
 *
 *          FMT3  = 0x00006310   (spi_cfg_generic.c:159)
 *
 *          LVL   = 0x00000000   (spi_cfg_generic.c:170)
 *
 *          FLG   = 0x0000FFFF   (spi_cfg_generic.c:180)
 *
 *          PC0   = 0x00000F00   (spi_cfg_generic.c:235)
 *
 *          PC1   = 0x00000603   (spi_cfg_generic.c:203)
 *
 *          PC3   = 0x00000003   (spi_cfg_generic.c:193)
 *
 *          PC6   = 0x00000900   (spi_cfg_generic.c:211)
 *
 *          PC7   = 0x00000603   (spi_cfg_generic.c:227)
 *
 *          PC8   = 0x00000F03   (spi_cfg_generic.c:219)
 */
void testSpiInitializeLeavesExpectedStateOnspiREG2(void) {
    volatile spiREG_t *const pReg = spiREG2;
    TEST_SpiRunInitializer();
    /* spi_cfg_generic.c:113 */
    TEST_ASSERT_EQUAL_HEX32(0x00000001u, pReg->GCR0);
    /* spi_cfg_generic.c:247 */
    TEST_ASSERT_EQUAL_HEX32(0x01000003u, pReg->GCR1);
    /* spi_cfg_generic.c:183 */
    TEST_ASSERT_EQUAL_HEX32(0x0100015Fu, pReg->INT0);
    /* spi_cfg_generic.c:121 */
    TEST_ASSERT_EQUAL_HEX32(0x00000000u, pReg->DELAY);
    /* spi_cfg_generic.c:127 */
    TEST_ASSERT_EQUAL_HEX32(0x00000908u, pReg->FMT0);
    /* spi_cfg_generic.c:138 */
    TEST_ASSERT_EQUAL_HEX32(0x00001810u, pReg->FMT1);
    /* spi_cfg_generic.c:148 */
    TEST_ASSERT_EQUAL_HEX32(0x00000910u, pReg->FMT2);
    /* spi_cfg_generic.c:159 */
    TEST_ASSERT_EQUAL_HEX32(0x00006310u, pReg->FMT3);
    /* spi_cfg_generic.c:170 */
    TEST_ASSERT_EQUAL_HEX32(0x00000000u, pReg->LVL);
    /* spi_cfg_generic.c:180 */
    TEST_ASSERT_EQUAL_HEX32(0x0000FFFFu, pReg->FLG);
    /* spi_cfg_generic.c:235 */
    TEST_ASSERT_EQUAL_HEX32(0x00000F00u, pReg->PC0);
    /* spi_cfg_generic.c:203 */
    TEST_ASSERT_EQUAL_HEX32(0x00000603u, pReg->PC1);
    /* spi_cfg_generic.c:193 */
    TEST_ASSERT_EQUAL_HEX32(0x00000003u, pReg->PC3);
    /* spi_cfg_generic.c:211 */
    TEST_ASSERT_EQUAL_HEX32(0x00000900u, pReg->PC6);
    /* spi_cfg_generic.c:227 */
    TEST_ASSERT_EQUAL_HEX32(0x00000603u, pReg->PC7);
    /* spi_cfg_generic.c:219 */
    TEST_ASSERT_EQUAL_HEX32(0x00000F03u, pReg->PC8);
}

/** @brief   the register state SPI_InitializeSpiInterfaces() leaves on spiREG3
 * @details Expected values and the spi_cfg_generic.c line that writes each one.
 *
 *          GCR0  = 0x00000001   (spi_cfg_generic.c:255)
 *
 *          GCR1  = 0x01000003   (spi_cfg_generic.c:414)
 *
 *          INT0  = 0x0100015F   (spi_cfg_generic.c:326)
 *
 *          DELAY = 0x00000000   (spi_cfg_generic.c:263)
 *
 *          FMT0  = 0x00001810   (spi_cfg_generic.c:269)
 *
 *          FMT1  = 0x00000208   (spi_cfg_generic.c:280)
 *
 *          FMT2  = 0x00000310   (spi_cfg_generic.c:291)
 *
 *          FMT3  = 0x00006310   (spi_cfg_generic.c:302)
 *
 *          LVL   = 0x00000000   (spi_cfg_generic.c:313)
 *
 *          FLG   = 0x0000FFFF   (spi_cfg_generic.c:323)
 *
 *          PC0   = 0x00000F00   (spi_cfg_generic.c:398)
 *
 *          PC1   = 0x0000063F   (spi_cfg_generic.c:350)
 *
 *          PC3   = 0x00000F3F   (spi_cfg_generic.c:336)
 *
 *          PC6   = 0x00000900   (spi_cfg_generic.c:362)
 *
 *          PC7   = 0x0000063F   (spi_cfg_generic.c:386)
 *
 *          PC8   = 0x00000F3F   (spi_cfg_generic.c:374)
 */
void testSpiInitializeLeavesExpectedStateOnspiREG3(void) {
    volatile spiREG_t *const pReg = spiREG3;
    TEST_SpiRunInitializer();
    /* spi_cfg_generic.c:255 */
    TEST_ASSERT_EQUAL_HEX32(0x00000001u, pReg->GCR0);
    /* spi_cfg_generic.c:414 */
    TEST_ASSERT_EQUAL_HEX32(0x01000003u, pReg->GCR1);
    /* spi_cfg_generic.c:326 */
    TEST_ASSERT_EQUAL_HEX32(0x0100015Fu, pReg->INT0);
    /* spi_cfg_generic.c:263 */
    TEST_ASSERT_EQUAL_HEX32(0x00000000u, pReg->DELAY);
    /* spi_cfg_generic.c:269 */
    TEST_ASSERT_EQUAL_HEX32(0x00001810u, pReg->FMT0);
    /* spi_cfg_generic.c:280 */
    TEST_ASSERT_EQUAL_HEX32(0x00000208u, pReg->FMT1);
    /* spi_cfg_generic.c:291 */
    TEST_ASSERT_EQUAL_HEX32(0x00000310u, pReg->FMT2);
    /* spi_cfg_generic.c:302 */
    TEST_ASSERT_EQUAL_HEX32(0x00006310u, pReg->FMT3);
    /* spi_cfg_generic.c:313 */
    TEST_ASSERT_EQUAL_HEX32(0x00000000u, pReg->LVL);
    /* spi_cfg_generic.c:323 */
    TEST_ASSERT_EQUAL_HEX32(0x0000FFFFu, pReg->FLG);
    /* spi_cfg_generic.c:398 */
    TEST_ASSERT_EQUAL_HEX32(0x00000F00u, pReg->PC0);
    /* spi_cfg_generic.c:350 */
    TEST_ASSERT_EQUAL_HEX32(0x0000063Fu, pReg->PC1);
    /* spi_cfg_generic.c:336 */
    TEST_ASSERT_EQUAL_HEX32(0x00000F3Fu, pReg->PC3);
    /* spi_cfg_generic.c:362 */
    TEST_ASSERT_EQUAL_HEX32(0x00000900u, pReg->PC6);
    /* spi_cfg_generic.c:386 */
    TEST_ASSERT_EQUAL_HEX32(0x0000063Fu, pReg->PC7);
    /* spi_cfg_generic.c:374 */
    TEST_ASSERT_EQUAL_HEX32(0x00000F3Fu, pReg->PC8);
}

/** @brief   the register state SPI_InitializeSpiInterfaces() leaves on spiREG5
 * @details Expected values and the spi_cfg_generic.c line that writes each one.
 *
 *          GCR0  = 0x00000001   (spi_cfg_generic.c:425)
 *
 *          GCR1  = 0x01000002   (spi_cfg_generic.c:620)
 *
 *          INT0  = 0x0100015F   (spi_cfg_generic.c:496)
 *
 *          DELAY = 0x00000000   (spi_cfg_generic.c:433)
 *
 *          FMT0  = 0x00003110   (spi_cfg_generic.c:439)
 *
 *          FMT1  = 0x00006310   (spi_cfg_generic.c:450)
 *
 *          FMT2  = 0x00006310   (spi_cfg_generic.c:461)
 *
 *          FMT3  = 0x00006310   (spi_cfg_generic.c:472)
 *
 *          LVL   = 0x00000000   (spi_cfg_generic.c:483)
 *
 *          FLG   = 0x0000FFFF   (spi_cfg_generic.c:493)
 *
 *          PC0   = 0x0E0E0F3F   (spi_cfg_generic.c:598)
 *
 *          PC1   = 0x000E063F   (spi_cfg_generic.c:526)
 *
 *          PC3   = 0x0E0E0F3F   (spi_cfg_generic.c:506)
 *
 *          PC6   = 0x0E000900   (spi_cfg_generic.c:544)
 *
 *          PC7   = 0x000E063F   (spi_cfg_generic.c:580)
 *
 *          PC8   = 0x0E0E0F3F   (spi_cfg_generic.c:562)
 */
void testSpiInitializeLeavesExpectedStateOnspiREG5(void) {
    volatile spiREG_t *const pReg = spiREG5;
    TEST_SpiRunInitializer();
    /* spi_cfg_generic.c:425 */
    TEST_ASSERT_EQUAL_HEX32(0x00000001u, pReg->GCR0);
    /* spi_cfg_generic.c:620 */
    TEST_ASSERT_EQUAL_HEX32(0x01000002u, pReg->GCR1);
    /* spi_cfg_generic.c:496 */
    TEST_ASSERT_EQUAL_HEX32(0x0100015Fu, pReg->INT0);
    /* spi_cfg_generic.c:433 */
    TEST_ASSERT_EQUAL_HEX32(0x00000000u, pReg->DELAY);
    /* spi_cfg_generic.c:439 */
    TEST_ASSERT_EQUAL_HEX32(0x00003110u, pReg->FMT0);
    /* spi_cfg_generic.c:450 */
    TEST_ASSERT_EQUAL_HEX32(0x00006310u, pReg->FMT1);
    /* spi_cfg_generic.c:461 */
    TEST_ASSERT_EQUAL_HEX32(0x00006310u, pReg->FMT2);
    /* spi_cfg_generic.c:472 */
    TEST_ASSERT_EQUAL_HEX32(0x00006310u, pReg->FMT3);
    /* spi_cfg_generic.c:483 */
    TEST_ASSERT_EQUAL_HEX32(0x00000000u, pReg->LVL);
    /* spi_cfg_generic.c:493 */
    TEST_ASSERT_EQUAL_HEX32(0x0000FFFFu, pReg->FLG);
    /* spi_cfg_generic.c:598 */
    TEST_ASSERT_EQUAL_HEX32(0x0E0E0F3Fu, pReg->PC0);
    /* spi_cfg_generic.c:526 */
    TEST_ASSERT_EQUAL_HEX32(0x000E063Fu, pReg->PC1);
    /* spi_cfg_generic.c:506 */
    TEST_ASSERT_EQUAL_HEX32(0x0E0E0F3Fu, pReg->PC3);
    /* spi_cfg_generic.c:544 */
    TEST_ASSERT_EQUAL_HEX32(0x0E000900u, pReg->PC6);
    /* spi_cfg_generic.c:580 */
    TEST_ASSERT_EQUAL_HEX32(0x000E063Fu, pReg->PC7);
    /* spi_cfg_generic.c:562 */
    TEST_ASSERT_EQUAL_HEX32(0x0E0E0F3Fu, pReg->PC8);
}

/** @brief   SPI_InitializeSpiInterfaces() touches no shadow register other than
 *          {spiREG2, spiREG3, spiREG5}
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
    SPI_InitializeSpiInterfaces();
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG1->GCR0);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG1->GCR1);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG1->INT0);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG1->DELAY);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG1->FMT0);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG1->FMT1);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG1->FMT2);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG1->FMT3);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG1->LVL);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG1->FLG);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG1->PC0);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG1->PC1);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG1->PC3);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG1->PC6);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG1->PC7);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG1->PC8);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG4->GCR0);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG4->GCR1);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG4->INT0);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG4->DELAY);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG4->FMT0);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG4->FMT1);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG4->FMT2);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG4->FMT3);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG4->LVL);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG4->FLG);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG4->PC0);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG4->PC1);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG4->PC3);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG4->PC6);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG4->PC7);
    TEST_ASSERT_EQUAL_HEX32(0xDEADBEEFu, spiREG4->PC8);
}

