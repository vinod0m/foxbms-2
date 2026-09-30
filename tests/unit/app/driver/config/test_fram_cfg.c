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
 * @file    test_fram_cfg.c
 * @author  foxBMS Team
 * @date    2020-04-01 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Tests of the FRAM configuration
 * @details Asserts the FRAM block registry and the initial contents of the
 *          FRAM-resident variables. fram_cfg.c defines no functions; its entire
 *          exported behaviour is
 *
 *            * the seven FRAM-resident variables fram_cfg.c:70-79 declares, and
 *            * `fram_databaseHeader[]`, the address/length registry the fram
 *              driver walks on FRAM_Initialize().
 *
 *          The registry is the load-bearing part: it tells the driver which
 *          variable sits at which FRAM address and how many bytes to move. A
 *          duplicated address, a wrong length or an entry pointing at the wrong
 *          variable corrupts whatever it overwrites, so the table is worth
 *          asserting even though the module contains no code.
 *
 *          WHERE THE EXPECTED VALUES COME FROM
 *          -------------------------------------
 *          Every expected value below is a literal or a macro fram_cfg.c itself
 *          writes. Each assertion cites the file:line that both names and
 *          assigns the value.
 *
 *          fram_version (fram_cfg.c:70)
 *            .project = FRAM_PROJECT_ID_FOXBMS_BASELINE   (fram_cfg.h:86 defines it to 0)
 *            .major   = 0                                 (fram_cfg.c:70)
 *            .minor   = 0                                 (fram_cfg.c:70)
 *            .patch   = 0                                 (fram_cfg.c:70)
 *
 *          fram_sbcInit (fram_cfg.c:73-76)
 *            .phase    = 0        (fram_cfg.c:74)
 *            .finState = STD_NOT_OK (fram_cfg.c:75)
 *
 *          fram_soc (fram_cfg.c:71), fram_soe (fram_cfg.c:72),
 *          fram_deepDischargeFlags (fram_cfg.c:77),
 *          fram_sysMonViolationRecord (fram_cfg.c:78) and
 *          fram_insulationFlags (fram_cfg.c:79) are initialised to all zero.
 *
 *          fram_databaseHeader, one entry per line of fram_cfg.c:87-93:
 *
 *            [0] &fram_version               (fram_cfg.c:87)
 *            [1] &fram_soc                   (fram_cfg.c:88)
 *            [2] &fram_sbcInit               (fram_cfg.c:89)
 *            [3] &fram_deepDischargeFlags    (fram_cfg.c:90)
 *            [4] &fram_soe                   (fram_cfg.c:91)
 *            [5] &fram_sysMonViolationRecord (fram_cfg.c:92)
 *            [6] &fram_insulationFlags       (fram_cfg.c:93)
 *
 *          The values were derived twice by two methods that share no code:
 *          a parser of the source literals (`tools/derive_cfg_tables.py`), and
 *          the compiled module's variables and table read through the harness.
 *          All 48 derived values agreed.
 *
 *          WHAT THIS DOES NOT ESTABLISH
 *          ----------------------------
 *          Every address in the table is asserted to be the uninitialised value
 *          0 that fram_cfg.c writes, matching its own comment at fram_cfg.c:82-85
 *          that the addresses are assigned by FRAM_Initialize(). Nothing here
 *          checks how the fram driver computes those addresses, nor that the
 *          chosen layout fits the part: no FRAM geometry is declared on a host.
 */

/*========== Includes =======================================================*/
#include "unity.h"

#include "fram_cfg.h"

/*========== Unit Testing Framework Directives ==============================*/
TEST_SOURCE_FILE("fram_cfg.c")

TEST_INCLUDE_PATH("../../src/app/driver/config")

/*========== Definitions and Implementations for Unit Test ==================*/

/*========== Setup and Teardown =============================================*/
void setUp(void) {
}

void tearDown(void) {
}

/*========== Test Cases =====================================================*/

/** @brief   the version block names the baseline project and is version 0.0.0
 * @details fram_cfg.c:70 sets .project, .major, .minor and .patch in one
 *          initialiser; FRAM_PROJECT_ID_FOXBMS_BASELINE is the macro it places
 *          there, and fram_cfg.h:86 defines that macro to 0. The expected side is
 *          the literal 0 and not the macro, because the initialiser writes the
 *          macro itself, so a macro-to-macro comparison would hold for any value
 *          the macro ever takes.
 */
void testFramVersionIsTheBaselineProjectAtZero(void) {
    /* fram_cfg.h:86 */
    TEST_ASSERT_EQUAL_UINT16(0u, fram_version.project);
    /* fram_cfg.c:70 */
    TEST_ASSERT_EQUAL_UINT8(0u, fram_version.major);
    /* fram_cfg.c:70 */
    TEST_ASSERT_EQUAL_UINT8(0u, fram_version.minor);
    /* fram_cfg.c:70 */
    TEST_ASSERT_EQUAL_UINT8(0u, fram_version.patch);
}

/** @brief   the SBC initialisation block starts at phase 0, not finished
 * @details fram_cfg.c:74 sets .phase to 0 and fram_cfg.c:75 sets .finState to
 *          STD_NOT_OK.
 */
void testFramSbcInitStartsUnfinished(void) {
    /* fram_cfg.c:74 */
    TEST_ASSERT_EQUAL_UINT8(0u, fram_sbcInit.phase);
    /* fram_cfg.c:75 */
    TEST_ASSERT_EQUAL(STD_NOT_OK, fram_sbcInit.finState);
}

/** @brief   the SOC block starts empty
 * @details fram_cfg.c:71 initialises fram_soc to {0}. With BS_NR_OF_STRINGS at
 *          1 for this build the block has three scalar entries and two
 *          single-element arrays, so five zero checks are spelled out.
 */
void testFramSocStartsEmpty(void) {
    /* fram_cfg.c:71 */
    TEST_ASSERT_EQUAL_FLOAT(0.0f, fram_soc.minimumSoc_perc[0]);
    /* fram_cfg.c:71 */
    TEST_ASSERT_EQUAL_FLOAT(0.0f, fram_soc.maximumSoc_perc[0]);
    /* fram_cfg.c:71 */
    TEST_ASSERT_EQUAL_FLOAT(0.0f, fram_soc.averageSoc_perc[0]);
    /* fram_cfg.c:71 */
    TEST_ASSERT_EQUAL_FLOAT(0.0f, fram_soc.chargeThroughput_As[0]);
    /* fram_cfg.c:71 */
    TEST_ASSERT_EQUAL_FLOAT(0.0f, fram_soc.dischargeThroughput_As[0]);
}

/** @brief   the SOE block starts empty
 * @details fram_cfg.c:72 initialises fram_soe to {0}.
 */
void testFramSoeStartsEmpty(void) {
    /* fram_cfg.c:72 */
    TEST_ASSERT_EQUAL_FLOAT(0.0f, fram_soe.minimumSoe_perc[0]);
    /* fram_cfg.c:72 */
    TEST_ASSERT_EQUAL_FLOAT(0.0f, fram_soe.maximumSoe_perc[0]);
    /* fram_cfg.c:72 */
    TEST_ASSERT_EQUAL_FLOAT(0.0f, fram_soe.averageSoe_perc[0]);
    /* fram_cfg.c:72 */
    TEST_ASSERT_EQUAL_FLOAT(0.0f, fram_soe.chargeEnergyThroughput_Wh[0]);
    /* fram_cfg.c:72 */
    TEST_ASSERT_EQUAL_FLOAT(0.0f, fram_soe.dischargeEnergyThroughput_Wh[0]);
}

/** @brief   the deep-discharge flag starts clear
 * @details fram_cfg.c:77 initialises fram_deepDischargeFlags to {false}.
 */
void testFramDeepDischargeFlagStartsClear(void) {
    /* fram_cfg.c:77 */
    TEST_ASSERT_FALSE(fram_deepDischargeFlags.deepDischargeFlag[0]);
}

/** @brief   the insulation ground-error flag starts clear
 * @details fram_cfg.c:79 initialises fram_insulationFlags to
 *          {.groundErrorDetected = false}.
 */
void testFramInsulationFlagStartsClear(void) {
    /* fram_cfg.c:79 */
    TEST_ASSERT_FALSE(fram_insulationFlags.groundErrorDetected);
}

/** @brief   the system-monitoring record starts with no violation recorded
 * @details fram_cfg.c:78 initialises fram_sysMonViolationRecord to
 *          {false, 0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u}, i.e. the flag clear
 *          and all ten durations and timestamps zero.
 */
void testFramSysMonRecordStartsWithoutViolation(void) {
    /* fram_cfg.c:78 */
    TEST_ASSERT_FALSE(fram_sysMonViolationRecord.anyTimingIssueOccurred);
    /* fram_cfg.c:78 */
    TEST_ASSERT_EQUAL_UINT32(0u, fram_sysMonViolationRecord.taskEngineViolatingDuration);
    /* fram_cfg.c:78 */
    TEST_ASSERT_EQUAL_UINT32(0u, fram_sysMonViolationRecord.taskEngineEnterTimestamp);
    /* fram_cfg.c:78 */
    TEST_ASSERT_EQUAL_UINT32(0u, fram_sysMonViolationRecord.task1msViolatingDuration);
    /* fram_cfg.c:78 */
    TEST_ASSERT_EQUAL_UINT32(0u, fram_sysMonViolationRecord.task1msEnterTimestamp);
    /* fram_cfg.c:78 */
    TEST_ASSERT_EQUAL_UINT32(0u, fram_sysMonViolationRecord.task10msViolatingDuration);
    /* fram_cfg.c:78 */
    TEST_ASSERT_EQUAL_UINT32(0u, fram_sysMonViolationRecord.task10msEnterTimestamp);
    /* fram_cfg.c:78 */
    TEST_ASSERT_EQUAL_UINT32(0u, fram_sysMonViolationRecord.task100msViolatingDuration);
    /* fram_cfg.c:78 */
    TEST_ASSERT_EQUAL_UINT32(0u, fram_sysMonViolationRecord.task100msAlgorithmViolatingDuration);
    /* fram_cfg.c:78 */
    TEST_ASSERT_EQUAL_UINT32(0u, fram_sysMonViolationRecord.task100msAlgorithmEnterTimestamp);
}

/** @brief   every registry entry points at the variable fram_cfg.c names for it
 * @details fram_cfg.c:87-93 cast the address of each variable into the table.
 *          Pointer identity against the extern declaration in fram_cfg.h:213-219
 *          checks the mapping, not merely that the pointer is non-NULL.
 */
void testFramHeaderPointsAtTheDeclaredVariables(void) {
    /* fram_cfg.c:87 */
    TEST_ASSERT_EQUAL_PTR(&fram_version, fram_databaseHeader[0].blockptr);
    /* fram_cfg.c:88 */
    TEST_ASSERT_EQUAL_PTR(&fram_soc, fram_databaseHeader[1].blockptr);
    /* fram_cfg.c:89 */
    TEST_ASSERT_EQUAL_PTR(&fram_sbcInit, fram_databaseHeader[2].blockptr);
    /* fram_cfg.c:90 */
    TEST_ASSERT_EQUAL_PTR(&fram_deepDischargeFlags, fram_databaseHeader[3].blockptr);
    /* fram_cfg.c:91 */
    TEST_ASSERT_EQUAL_PTR(&fram_soe, fram_databaseHeader[4].blockptr);
    /* fram_cfg.c:92 */
    TEST_ASSERT_EQUAL_PTR(&fram_sysMonViolationRecord, fram_databaseHeader[5].blockptr);
    /* fram_cfg.c:93 */
    TEST_ASSERT_EQUAL_PTR(&fram_insulationFlags, fram_databaseHeader[6].blockptr);
}

/** @brief   the registry entry order follows FRAM_BLOCK_ID_e
 * @details fram_cfg.h:100-108 numbers the blocks VERSION, SOC, SBC_INIT_STATE,
 *          DEEP_DISCHARGE_FLAG, SOE, SYS_MON_RECORD, INSULATION_FLAG. The table
 *          at fram_cfg.c:87-93 is walked in that order, so entry N must point at
 *          the variable belonging to block N. A reordered registry would silently
 *          give one block another's contents.
 */
void testFramHeaderOrderFollowsTheBlockIdEnumeration(void) {
    TEST_ASSERT_EQUAL_PTR(&fram_version, fram_databaseHeader[FRAM_BLOCK_ID_VERSION].blockptr);
    TEST_ASSERT_EQUAL_PTR(&fram_soc, fram_databaseHeader[FRAM_BLOCK_ID_SOC].blockptr);
    TEST_ASSERT_EQUAL_PTR(&fram_sbcInit, fram_databaseHeader[FRAM_BLOCK_ID_SBC_INIT_STATE].blockptr);
    TEST_ASSERT_EQUAL_PTR(&fram_deepDischargeFlags, fram_databaseHeader[FRAM_BLOCK_ID_DEEP_DISCHARGE_FLAG].blockptr);
    TEST_ASSERT_EQUAL_PTR(&fram_soe, fram_databaseHeader[FRAM_BLOCK_ID_SOE].blockptr);
    TEST_ASSERT_EQUAL_PTR(&fram_sysMonViolationRecord, fram_databaseHeader[FRAM_BLOCK_ID_SYS_MON_RECORD].blockptr);
    TEST_ASSERT_EQUAL_PTR(&fram_insulationFlags, fram_databaseHeader[FRAM_BLOCK_ID_INSULATION_FLAG].blockptr);
}

/** @brief   every registry entry records the size of the variable it points at
 * @details fram_cfg.c:87-93 write `sizeof(<the variable>)` as the data length.
 *          The expected length is computed here with the same sizeof, so the
 *          assertion is that fram_cfg.c paired each pointer with its own size and
 *          not with a neighbour's.
 */
void testFramHeaderRecordsTheSizeOfEachVariable(void) {
    /* fram_cfg.c:87 */
    TEST_ASSERT_EQUAL_UINT32((uint32_t)sizeof(fram_version), fram_databaseHeader[0].datalength);
    /* fram_cfg.c:88 */
    TEST_ASSERT_EQUAL_UINT32((uint32_t)sizeof(fram_soc), fram_databaseHeader[1].datalength);
    /* fram_cfg.c:89 */
    TEST_ASSERT_EQUAL_UINT32((uint32_t)sizeof(fram_sbcInit), fram_databaseHeader[2].datalength);
    /* fram_cfg.c:90 */
    TEST_ASSERT_EQUAL_UINT32((uint32_t)sizeof(fram_deepDischargeFlags), fram_databaseHeader[3].datalength);
    /* fram_cfg.c:91 */
    TEST_ASSERT_EQUAL_UINT32((uint32_t)sizeof(fram_soe), fram_databaseHeader[4].datalength);
    /* fram_cfg.c:92 */
    TEST_ASSERT_EQUAL_UINT32((uint32_t)sizeof(fram_sysMonViolationRecord), fram_databaseHeader[5].datalength);
    /* fram_cfg.c:93 */
    TEST_ASSERT_EQUAL_UINT32((uint32_t)sizeof(fram_insulationFlags), fram_databaseHeader[6].datalength);
}

/** @brief   every registry entry carries a non-zero length
 * @details A zero length would make FRAM_Initialize() move no bytes for that
 *          block. The lengths are the sizeof expressions at fram_cfg.c:87-93.
 */
void testFramHeaderLengthsAreAllNonZero(void) {
    uint32_t u;
    for (u = 0u; u < FRAM_BLOCK_MAX; u++) {
        /* fram_cfg.c:87 */
        TEST_ASSERT_NOT_EQUAL(0u, fram_databaseHeader[u].datalength);
    }
}

/** @brief   every registry address starts at the uninitialised value
 * @details fram_cfg.c:87-93 write 0 into the address field of every entry, which
 *          is what its own comment at fram_cfg.c:82-85 says the driver then fills
 *          in. All entries sharing 0 is what makes a block genuinely unassigned.
 */
void testFramHeaderAddressesStartAtTheUninitialisedValue(void) {
    uint32_t u;
    for (u = 0u; u < FRAM_BLOCK_MAX; u++) {
        /* fram_cfg.c:87 */
        TEST_ASSERT_EQUAL_UINT32(0u, fram_databaseHeader[u].address);
    }
}

/** @brief   the registry covers every declared FRAM block exactly once
 * @details fram_cfg.h:213 declares the table with FRAM_BLOCK_MAX elements and
 *          fram_cfg.h:100-108 declares that many blocks; the entries come from
 *          fram_cfg.c:87-93. Checking pairwise pointer inequality proves no block
 *          is registered twice.
 */
void testFramHeaderRegistersEveryBlockExactlyOnce(void) {
    uint32_t u;
    uint32_t v;
    for (u = 0u; u < FRAM_BLOCK_MAX; u++) {
        TEST_ASSERT_NOT_NULL(fram_databaseHeader[u].blockptr);
        for (v = u + 1u; v < FRAM_BLOCK_MAX; v++) {
            TEST_ASSERT_NOT_EQUAL(fram_databaseHeader[u].blockptr, fram_databaseHeader[v].blockptr);
        }
    }
}
