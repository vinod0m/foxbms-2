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
 * @file    test_adi_ades1830_buffers.c
 * @author  foxBMS Team
 * @date    2022-12-07 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Test of some module
 * @details TODO
 *
 */

/*========== Includes =======================================================*/
#include "unity.h"

#include "adi_ades183x_buffers.h"

#include <stdint.h>

/*========== Unit Testing Framework Directives ==============================*/
TEST_SOURCE_FILE("adi_ades183x_buffers.c")

TEST_INCLUDE_PATH("../../src/app/driver/afe/adi/ades1830")
TEST_INCLUDE_PATH("../../src/app/driver/afe/adi/common/ades183x")
TEST_INCLUDE_PATH("../../src/app/driver/afe/adi/common/ades183x/config")
TEST_INCLUDE_PATH("../../src/app/driver/afe/adi/common/ades183x/diag")
TEST_INCLUDE_PATH("../../src/app/driver/afe/api")
TEST_INCLUDE_PATH("../../src/app/driver/config")
TEST_INCLUDE_PATH("../../src/app/driver/spi")

/*========== Definitions and Implementations for Unit Test ==================*/

/*========== Setup and Teardown =============================================*/
void setUp(void) {
}

void tearDown(void) {
}

/*========== Test Cases =====================================================*/

/**
 * @brief   adi_ades183x_buffers.c owns the driver's scratch memory: the command
 *          staging word, the per-string configuration register images, the
 *          transmit/receive staging areas and the global-write scratch buffer.
 *          Every one of them is handed to SPI with a length, so the declared
 *          extent of each array is part of the interface -- an array one element
 *          short is a buffer overrun the moment the driver fills it.
 * @details adi_ades183x_buffers.c:71-88, with the dimensions taken from
 *          adi_ades183x_defs.h and battery_system_cfg.h:
 *            BS_NR_OF_STRINGS                    = (1u)  battery_system_cfg.h:109
 *            BS_NR_OF_MODULES_PER_STRING         = (1u)  battery_system_cfg.h:122
 *            ADI_MAX_REGISTER_SIZE_IN_BYTES       = (6u)  adi_ades183x_defs.h:315
 *            ADI_COMMAND_DEFINITION_LENGTH       = (4u)  adi_ades183x_defs.h:554
 *            ADI_CLRFLAG_DATA_LENGTH             = (6u)  adi_ades183x_defs.h:872
 *          so 1 * 1 * 6 = 6 is the per-string register image extent, and the
 *          dimensions are asserted as the LITERAL 6 rather than as the macro
 *          product, which would be a comparison of a macro with its own
 *          definition and could not fail.
 */
void testAdiBufferExtents(void) {
    /* ======= Assertion tests ============================================= */
    /* per-string configuration register images: [1 string][1 module * 6 bytes] */
    TEST_ASSERT_EQUAL_UINT32(6u, (uint32_t)sizeof(adi_configurationRegisterAgroup[0]));
    TEST_ASSERT_EQUAL_UINT32(6u, (uint32_t)sizeof(adi_configurationRegisterBgroup[0]));
    TEST_ASSERT_EQUAL_UINT32(6u, (uint32_t)sizeof(adi_readConfigurationRegisterAgroup[0]));
    TEST_ASSERT_EQUAL_UINT32(6u, (uint32_t)sizeof(adi_readConfigurationRegisterBgroup[0]));
    /* the string axis is 1, so each image is exactly 6 bytes in total */
    TEST_ASSERT_EQUAL_UINT32(6u, (uint32_t)sizeof(adi_configurationRegisterAgroup));
    TEST_ASSERT_EQUAL_UINT32(6u, (uint32_t)sizeof(adi_configurationRegisterBgroup));
    TEST_ASSERT_EQUAL_UINT32(6u, (uint32_t)sizeof(adi_readConfigurationRegisterAgroup));
    TEST_ASSERT_EQUAL_UINT32(6u, (uint32_t)sizeof(adi_readConfigurationRegisterBgroup));

    /* command staging word: ADI_COMMAND_DEFINITION_LENGTH = 4u */
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_command) / sizeof(adi_command[0])));
    /* per-module transmit/receive staging: 1 module * 6 bytes */
    TEST_ASSERT_EQUAL_UINT32(6u, (uint32_t)sizeof(adi_dataTransmit));
    TEST_ASSERT_EQUAL_UINT32(6u, (uint32_t)sizeof(adi_dataReceive));
    /* global-write scratch: ADI_MAX_REGISTER_SIZE_IN_BYTES = 6u */
    TEST_ASSERT_EQUAL_UINT32(6u, (uint32_t)sizeof(adi_writeGlobal));
    /* clear-flag payload: ADI_CLRFLAG_DATA_LENGTH = 6u */
    TEST_ASSERT_EQUAL_UINT32(6u, (uint32_t)sizeof(adi_clearFlagData));
}

/**
 * @brief   The buffers are declared with a zero initialiser (the `= {0}` on
 *          every line of adi_ades183x_buffers.c:71-88), so at first use every
 *          byte is zero. The command word and the clear-flag payload are the
 *          two the driver fills from a table before a transaction; a non-zero
 *          byte here would be a byte the driver believes it wrote but did not.
 * @details Read off the `= {0}` initialisers at adi_ades183x_buffers.c:81,83,84,86,88.
 *          setUp() runs this once per case, and the module has no initialiser
 *          that runs afterwards, so the buffers are still in their reset state.
 */
void testAdiBuffersStartZeroed(void) {
    /* ======= Assertion tests ============================================= */
    for (uint32_t i = 0u; i < 4u; i++) {
        TEST_ASSERT_EQUAL_UINT16_MESSAGE(0u, adi_command[i],
                                        "adi_command must start zeroed (adi_ades183x_buffers.c:81)");
    }
    for (uint32_t i = 0u; i < 6u; i++) {
        TEST_ASSERT_EQUAL_UINT8_MESSAGE(0u, adi_dataTransmit[i],
                                        "adi_dataTransmit must start zeroed (:83)");
        TEST_ASSERT_EQUAL_UINT8_MESSAGE(0u, adi_dataReceive[i],
                                        "adi_dataReceive must start zeroed (:84)");
        TEST_ASSERT_EQUAL_UINT8_MESSAGE(0u, adi_writeGlobal[i],
                                        "adi_writeGlobal must start zeroed (:86)");
        TEST_ASSERT_EQUAL_UINT8_MESSAGE(0u, adi_clearFlagData[i],
                                        "adi_clearFlagData must start zeroed (:88)");
        TEST_ASSERT_EQUAL_UINT8_MESSAGE(0u, adi_configurationRegisterAgroup[0][i],
                                        "configuration register A image must start zeroed (:71)");
        TEST_ASSERT_EQUAL_UINT8_MESSAGE(0u, adi_configurationRegisterBgroup[0][i],
                                        "configuration register B image must start zeroed (:73)");
        TEST_ASSERT_EQUAL_UINT8_MESSAGE(0u, adi_readConfigurationRegisterAgroup[0][i],
                                        "read register A image must start zeroed (:76)");
        TEST_ASSERT_EQUAL_UINT8_MESSAGE(0u, adi_readConfigurationRegisterBgroup[0][i],
                                        "read register B image must start zeroed (:78)");
    }
}
