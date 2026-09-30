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
 * @file    test_boot_cfg.c
 * @author  foxBMS Team
 * @date    2024-09-17 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Test of some module
 * @details TODO
 */

/*========== Includes =======================================================*/
#include "unity.h"

#include "boot_cfg.h"

#include <stdint.h>

/*========== Unit Testing Framework Directives ==============================*/
TEST_SOURCE_FILE("boot_cfg.c")

TEST_INCLUDE_PATH("../../src/bootloader/driver/can")
TEST_INCLUDE_PATH("../../src/bootloader/driver/config")
TEST_INCLUDE_PATH("../../src/bootloader/driver/foxmath")
TEST_INCLUDE_PATH("../../src/bootloader/engine/boot")

/*========== Definitions and Implementations for Unit Test ==================*/

/*========== Setup and Teardown =============================================*/
void setUp(void) {
    /* the module's exported objects are mutable globals, not const, so each
     * case restores the power-on values before it runs. The values are the
     * ones boot_cfg.c:64-70 initialises them to, and they are written here as
     * literals for the same reason: asserting the initialiser against the
     * initialiser would prove nothing. */
    boot_infoOfLastFlashedProgram.programLength           = 0u;
    boot_infoOfLastFlashedProgram.programStartAddress     = 0u;
    boot_infoOfLastFlashedProgram.programCrc8Bytes         = 0u;
    boot_infoOfLastFlashedProgram.vectorTableCrc8Bytes     = 0u;
    boot_infoOfLastFlashedProgram.isProgramAvailable       = 0u;
    boot_state                                          = BOOT_FSM_STATE_WAIT;
    for (uint32_t i = 0u; i < 4u; i++) {
        boot_backupVectorTable.vectorTable[i]  = 0u;
        boot_currentVectorTable.vectorTable[i] = 0u;
    }
}

void tearDown(void) {
}

/*========== Test Cases =====================================================*/

/**
 * @brief   boot_state is the bootloader's state variable. It is initialised to
 *          BOOT_FSM_STATE_WAIT and the state machine advances it, so on a cold
 *          start, before any state transition, it must read WAIT. A bootloader
 *          that begins in RUN would skip the flash checks entirely.
 * @details boot_cfg.c:70
 *              BOOT_FSM_STATES_e boot_state = BOOT_FSM_STATE_WAIT;
 *          BOOT_FSM_STATE_WAIT is 1u, the first enumerator of BOOT_FSM_STATES_e
 *          at boot_cfg.h:206-212. The literal 1 is asserted, not the enumerator,
 *          so a renumbering of the enum that silently changed the entry state
 *          would be caught.
 */
void testBootFsmStartsInWaitState(void) {
    /* ======= Assertion tests ============================================= */
    TEST_ASSERT_EQUAL_UINT32(1u, (uint32_t)BOOT_FSM_STATE_WAIT);
    TEST_ASSERT_EQUAL_UINT32(1u, (uint32_t)boot_state);
    /* the whole enum is numbered 1..5 with no gap and no zero state
     * (boot_cfg.h:207-211), which is what lets the FSM use 0 as "unset" */
    TEST_ASSERT_EQUAL_UINT32(2u, (uint32_t)BOOT_FSM_STATE_RESET);
    TEST_ASSERT_EQUAL_UINT32(3u, (uint32_t)BOOT_FSM_STATE_RUN);
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)BOOT_FSM_STATE_LOAD);
    TEST_ASSERT_EQUAL_UINT32(5u, (uint32_t)BOOT_FSM_STATE_ERROR);
}

/**
 * @brief   boot_infoOfLastFlashedProgram is the image the bootloader validated
 *          and will jump to. All five fields are zero on a cold start, and
 *          isProgramAvailable == 0 is the flag that tells the FSM no program was
 *          found. A stale non-zero isProgramAvailable would make the bootloader
 *          jump to an unvalidated address.
 * @details boot_cfg.c:64
 *              BOOT_PROGRAM_INFO_s boot_infoOfLastFlashedProgram = {0u, 0u, 0u, 0u, 0u};
 *          The field order is the declaration order at boot_cfg.h:192-198:
 *          programLength, programStartAddress, programCrc8Bytes,
 *          vectorTableCrc8Bytes, isProgramAvailable.
 */
void testBootProgramInfoStartsCleared(void) {
    /* ======= Assertion tests ============================================= */
    TEST_ASSERT_EQUAL_UINT32(0u, boot_infoOfLastFlashedProgram.programLength);
    TEST_ASSERT_EQUAL_UINT32(0u, boot_infoOfLastFlashedProgram.programStartAddress);
    TEST_ASSERT_EQUAL_UINT64(0u, boot_infoOfLastFlashedProgram.programCrc8Bytes);
    TEST_ASSERT_EQUAL_UINT64(0u, boot_infoOfLastFlashedProgram.vectorTableCrc8Bytes);
    TEST_ASSERT_EQUAL_UINT32(0u, boot_infoOfLastFlashedProgram.isProgramAvailable);
}

/**
 * @brief   The bootloader keeps two vector tables: the one it read from flash
 *          (backup) and the one it is about to run (current). Both start zeroed
 *          and each holds BOOT_NUM_OF_VECTOR_TABLE_8_BYTES eight-byte words, so
 *          a 32-byte region. The word count is asserted as the literal 4,
 *          because BOOT_NUM_OF_VECTOR_TABLE_8_BYTES is exactly the constant that
 *          sizes the array and comparing the two would be a tautology.
 * @details boot_cfg.c:66-68
 *              BOOT_VECTOR_TABLE_s boot_backupVectorTable  = {{0u, 0u, 0u, 0u}};
 *              BOOT_VECTOR_TABLE_s boot_currentVectorTable = {{0u, 0u, 0u, 0u}};
 *          boot_cfg.h:184 defines BOOT_NUM_OF_VECTOR_TABLE_8_BYTES as (4u) and
 *          boot_cfg.h:198-200 the struct as uint64_t vectorTable[4].
 */
void testBootVectorTablesStartClearedAndSized(void) {
    /* ======= Assertion tests ============================================= */
    /* four eight-byte words per table (boot_cfg.h:184) */
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)BOOT_NUM_OF_VECTOR_TABLE_8_BYTES);
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(boot_backupVectorTable.vectorTable) /
                                            sizeof(boot_backupVectorTable.vectorTable[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(boot_currentVectorTable.vectorTable) /
                                            sizeof(boot_currentVectorTable.vectorTable[0])));
    /* each table is entirely zero on a cold start */
    for (uint32_t i = 0u; i < 4u; i++) {
        TEST_ASSERT_EQUAL_UINT64_MESSAGE(0u, boot_backupVectorTable.vectorTable[i],
                                         "backup vector table must start zeroed");
        TEST_ASSERT_EQUAL_UINT64_MESSAGE(0u, boot_currentVectorTable.vectorTable[i],
                                         "current vector table must start zeroed");
    }
    /* the two tables are distinct objects, not aliases of one buffer: writing
     * one must not be visible through the other */
    TEST_ASSERT_TRUE(boot_backupVectorTable.vectorTable != boot_currentVectorTable.vectorTable);
}

/**
 * @brief   The state variable is a mutable global, so a test can drive it; the
 *          point of this case is that the value the module leaves behind is
 *          readable and is what a subsequent state-machine step would consume.
 *          It also pins the fact that writing the global does not disturb the
 *          program-info block, i.e. the two exports are independent.
 * @details boot_cfg.c:64 and :70 are separate objects with separate storage.
 */
void testBootStateAndProgramInfoAreIndependent(void) {
    /* ======= Assertion tests ============================================= */
    boot_state = BOOT_FSM_STATE_LOAD;
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)boot_state);
    /* moving the FSM did not create a program image */
    TEST_ASSERT_EQUAL_UINT32(0u, boot_infoOfLastFlashedProgram.isProgramAvailable);
    TEST_ASSERT_EQUAL_UINT32(0u, boot_infoOfLastFlashedProgram.programStartAddress);
}
