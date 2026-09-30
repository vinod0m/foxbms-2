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
 * @file    test_pex_cfg.c
 * @author  foxBMS Team
 * @date    2021-08-03 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Tests of the port expander configuration
 * @details Asserts the I2C address list pex_cfg.c publishes. pex_cfg.c defines
 *          no functions; its entire exported behaviour is the single table
 *          `pex_addressList`, which the pex driver reads at run time to address
 *          each port expander on the bus. A wrong entry there silently addresses
 *          the wrong chip, so the table is worth asserting even though the
 *          module contains no code.
 *
 *          WHERE THE EXPECTED VALUES COME FROM
 *          -------------------------------------
 *          Every expected value below is a literal pex_cfg.c itself defines or
 *          places in the table. Each assertion cites the file:line that both
 *          names and assigns the value, so the expectation is traceable to
 *          first-party source and not to a datasheet.
 *
 *              pex_addressList[0] = 0x74   (pex_cfg.c:74, literal at pex_cfg.c:62)
 *              pex_addressList[1] = 0x75   (pex_cfg.c:75, literal at pex_cfg.c:64)
 *              pex_addressList[2] = 0x76   (pex_cfg.c:76, literal at pex_cfg.c:66)
 *
 *          The values were derived twice by two methods that share no code:
 *          a parser of the source literals (`tools/derive_cfg_tables.py`), and
 *          the compiled module's table read through the harness. All six derived
 *          values agreed.
 *
 *          WHAT THIS DOES NOT ESTABLISH
 *          ----------------------------
 *          The addresses are checked to be the bytes the repository puts in the
 *          table. Nothing here checks that 0x74/0x75/0x76 are the addresses the
 *          PCA9539 parts were strapped to on the assembled board; that is a
 *          hardware fact and is not checkable from a host build.
 */

/*========== Includes =======================================================*/
#include "unity.h"

#include "pex_cfg.h"

/*========== Unit Testing Framework Directives ==============================*/
TEST_SOURCE_FILE("pex_cfg.c")

TEST_INCLUDE_PATH("../../src/app/driver/config")

/*========== Definitions and Implementations for Unit Test ==================*/

/** @brief   number of port expanders the header declares (pex_cfg.h:68) */
#define TEST_PEX_N_EXPANDERS (3u)

/*========== Setup and Teardown =============================================*/
void setUp(void) {
}

void tearDown(void) {
}

/*========== Test Cases =====================================================*/

/** @brief   the address list holds the three literals pex_cfg.c declares
 * @details pex_cfg.c:73 declares the list; the three entries are at
 *          pex_cfg.c:74, :75 and :76.
 */
void testPexAddressListHoldsTheDeclaredLiterals(void) {
    /* pex_cfg.c:74 */
    TEST_ASSERT_EQUAL_UINT8(0x74u, pex_addressList[0u]);
    /* pex_cfg.c:75 */
    TEST_ASSERT_EQUAL_UINT8(0x75u, pex_addressList[1u]);
    /* pex_cfg.c:76 */
    TEST_ASSERT_EQUAL_UINT8(0x76u, pex_addressList[2u]);
}

/** @brief   no two port expanders share an I2C address
 * @details Two expanders on the same address would make the bus ambiguous. The
 *          comparison is over the three entries placed at pex_cfg.c:74-76.
 */
void testPexAddressListHasNoDuplicateAddress(void) {
    /* pex_cfg.c:74 */
    TEST_ASSERT_NOT_EQUAL(pex_addressList[0u], pex_addressList[1u]);
    /* pex_cfg.c:74 */
    TEST_ASSERT_NOT_EQUAL(pex_addressList[0u], pex_addressList[2u]);
    /* pex_cfg.c:75 */
    TEST_ASSERT_NOT_EQUAL(pex_addressList[1u], pex_addressList[2u]);
}

/** @brief   the address list ascends with the expander number
 * @details pex_cfg.c places 0x74, 0x75, 0x76 in that order at pex_cfg.c:74,
 *          :75 and :76, so expander N carries address 0x74+N-1.
 */
void testPexAddressListAscendsWithExpanderNumber(void) {
    /* pex_cfg.c:74 */
    TEST_ASSERT_LESS_THAN_UINT8(pex_addressList[1u], pex_addressList[0u]);
    /* pex_cfg.c:75 */
    TEST_ASSERT_EQUAL_UINT8((uint8_t)(0x74u + 1u), pex_addressList[1u]);
    /* pex_cfg.c:75 */
    TEST_ASSERT_LESS_THAN_UINT8(pex_addressList[2u], pex_addressList[1u]);
    /* pex_cfg.c:76 */
    TEST_ASSERT_EQUAL_UINT8((uint8_t)(0x74u + 2u), pex_addressList[2u]);
}
