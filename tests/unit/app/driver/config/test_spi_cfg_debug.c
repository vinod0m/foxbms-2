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
 * @file    test_spi_cfg_debug.c
 * @author  foxBMS Team
 * @date    2026-02-09 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Tests for the debug specific SPI configuration
 * @details Asserts that SPI_InitializeAfeSpecificSpiInterfaces() modifies no
 *          SPI shadow register.
 *
 *          WHY THERE IS NO EXPECTED REGISTER VALUE HERE
 *          ------------------------------------------
 *          The other seven modules in this family write 16 fields on each of two
 *          or three SPI instances. spi_cfg_debug.c does not: the function body
 *          at spi_cfg_debug.c:75-76 is empty, and the file states the reason at
 *          spi_cfg_debug.c:52 -- "The debug AFEs do not need SPI". The
 *          enumeration of touched members over all eight files finds zero
 *          spiREGn->FIELD accesses in this one, so there is no value to assert
 *          positive and none is invented.
 *
 *          WHAT IS ASSERTED INSTEAD
 *          -------------------------
 *          The absence of side effects: every shadow register on all five
 *          instances is seeded to a NON-ZERO sentinel, the call is made, and
 *          every field is required to still hold that sentinel. A single added
 *          write would break this, so the assertion has teeth.
 *
 *          WHAT THIS DOES NOT ESTABLISH
 *          ----------------------------
 *          The shadow registers are ordinary writable objects in the test's own
 *          address space (sil/iface/HL_spi.h). See sil/REPORT.md, "What this
 *          does not prove".
 */

/*========== Includes =======================================================*/
#include "unity.h"

#include "HL_spi.h"
#include "spi_cfg_initialization.h"

/*========== Unit Testing Framework Directives ==============================*/
TEST_SOURCE_FILE("spi_cfg_debug.c")

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

/*========== Test Cases =====================================================*/

/** @brief   SPI_InitializeAfeSpecificSpiInterfaces() writes NO SPI register at all
 * @details spi_cfg_debug.c:75-76 defines
 *
 *              void SPI_InitializeAfeSpecificSpiInterfaces(void) {
 *              }
 *
 *          an empty body, and the file's own header comment states the intent at
 *          spi_cfg_debug.c:52 -- "The debug AFEs do not need SPI". There is no register
 *          value to assert positive here, so this test asserts the property the
 *          empty body actually has: not one shadow register on any of the five
 *          instances is modified.
 *
 *          This is a real assertion and not a tautology. The registers are
 *          seeded to a NON-ZERO sentinel first; were the body to contain a
 *          single write, the sentinel would be overwritten or the register
 *          would become non-zero, and the comparison below would fail.
 */
void testSpiDebugInitializerLeavesEveryShadowRegisterUntouched(void) {
    uint32_t u;
    const uint32_t TEST_SPI_SENTINEL = 0xDEADBEEFu;

    for (u = 0u; u < TEST_SPI_N_REGS; u++) {
        sil_spi_reg[u].GCR0  = TEST_SPI_SENTINEL;
        sil_spi_reg[u].GCR1  = TEST_SPI_SENTINEL;
        sil_spi_reg[u].INT0  = TEST_SPI_SENTINEL;
        sil_spi_reg[u].DELAY = TEST_SPI_SENTINEL;
        sil_spi_reg[u].FMT0  = TEST_SPI_SENTINEL;
        sil_spi_reg[u].FMT1  = TEST_SPI_SENTINEL;
        sil_spi_reg[u].FMT2  = TEST_SPI_SENTINEL;
        sil_spi_reg[u].FMT3  = TEST_SPI_SENTINEL;
        sil_spi_reg[u].LVL   = TEST_SPI_SENTINEL;
        sil_spi_reg[u].FLG   = TEST_SPI_SENTINEL;
        sil_spi_reg[u].PC0   = TEST_SPI_SENTINEL;
        sil_spi_reg[u].PC1   = TEST_SPI_SENTINEL;
        sil_spi_reg[u].PC3   = TEST_SPI_SENTINEL;
        sil_spi_reg[u].PC6   = TEST_SPI_SENTINEL;
        sil_spi_reg[u].PC7   = TEST_SPI_SENTINEL;
        sil_spi_reg[u].PC8   = TEST_SPI_SENTINEL;
    }

    SPI_InitializeAfeSpecificSpiInterfaces();

    /* still the sentinel: the empty body wrote nothing */
    for (u = 0u; u < TEST_SPI_N_REGS; u++) {
        TEST_ASSERT_EQUAL_HEX32(TEST_SPI_SENTINEL, sil_spi_reg[u].GCR0);
        TEST_ASSERT_EQUAL_HEX32(TEST_SPI_SENTINEL, sil_spi_reg[u].GCR1);
        TEST_ASSERT_EQUAL_HEX32(TEST_SPI_SENTINEL, sil_spi_reg[u].INT0);
        TEST_ASSERT_EQUAL_HEX32(TEST_SPI_SENTINEL, sil_spi_reg[u].DELAY);
        TEST_ASSERT_EQUAL_HEX32(TEST_SPI_SENTINEL, sil_spi_reg[u].FMT0);
        TEST_ASSERT_EQUAL_HEX32(TEST_SPI_SENTINEL, sil_spi_reg[u].FMT1);
        TEST_ASSERT_EQUAL_HEX32(TEST_SPI_SENTINEL, sil_spi_reg[u].FMT2);
        TEST_ASSERT_EQUAL_HEX32(TEST_SPI_SENTINEL, sil_spi_reg[u].FMT3);
        TEST_ASSERT_EQUAL_HEX32(TEST_SPI_SENTINEL, sil_spi_reg[u].LVL);
        TEST_ASSERT_EQUAL_HEX32(TEST_SPI_SENTINEL, sil_spi_reg[u].FLG);
        TEST_ASSERT_EQUAL_HEX32(TEST_SPI_SENTINEL, sil_spi_reg[u].PC0);
        TEST_ASSERT_EQUAL_HEX32(TEST_SPI_SENTINEL, sil_spi_reg[u].PC1);
        TEST_ASSERT_EQUAL_HEX32(TEST_SPI_SENTINEL, sil_spi_reg[u].PC3);
        TEST_ASSERT_EQUAL_HEX32(TEST_SPI_SENTINEL, sil_spi_reg[u].PC6);
        TEST_ASSERT_EQUAL_HEX32(TEST_SPI_SENTINEL, sil_spi_reg[u].PC7);
        TEST_ASSERT_EQUAL_HEX32(TEST_SPI_SENTINEL, sil_spi_reg[u].PC8);
    }
}
