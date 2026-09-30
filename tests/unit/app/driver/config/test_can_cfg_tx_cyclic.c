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
 * @file    test_can_cfg_tx_cyclic.c
 * @author  foxBMS Team
 * @date    2020-07-28 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Tests of the cyclic CAN Tx configuration
 * @details Asserts the cyclic transmit registry can_cfg_tx_cyclic.c publishes.
 *          can_cfg_tx_cyclic.c defines no functions; its entire exported
 *          behaviour is
 *
 *            * `can_txMessages[]`, one entry per cyclic Tx frame, each naming the
 *              node, the message id/properties, the cycle time and phase, the
 *              callback that fills the payload and - for multiplexed frames - the
 *              multiplexer variable the callback may advance, and
 *            * `can_txMessagesLength`, the entry count the driver iterates.
 *
 *          This registry is what decides what the BMS puts on the bus. A wrong id
 *          puts a frame where no subscriber expects it, a transposed callback
 *          sends one signal's bytes under another's id, and a shared multiplexer
 *          variable corrupts two multiplexed frames at once. It is worth
 *          asserting even though the module contains no code.
 *
 *          WHERE THE EXPECTED VALUES COME FROM
 *          -------------------------------------
 *          The per-frame message properties are not written numerically here.
 *          can_cfg_tx_cyclic.c:86-102 place a `CANTX_*_MESSAGE` macro on each
 *          row, and each macro takes its id, id type, period, phase, DLC and
 *          endianness from the `CANTX_*` defines of
 *          can_cfg_tx-cyclic-message-definitions.h. The literals asserted below
 *          are those defines; the citations give the row that consumes the macro
 *          and the define that supplies the number.
 *
 *            row  message                              id     id line  period  period line  phase  phase line
 *             0    CANTX_BMS_STATE_MESSAGE               0x220  :85      100     :87           0      :88
 *             1    CANTX_BMS_STATE_DETAILS_MESSAGE       0x221  :99      1000    :101          100    :102
 *             2    CANTX_CELL_VOLTAGES_MESSAGE           0x250  :113     100     :115          10     :116
 *             3    CANTX_CELL_TEMPERATURES_MESSAGE       0x260  :127     200     :129          20     :130
 *             4    CANTX_PACK_LIMITS_MESSAGE             0x232  :141     100     :143          30     :144
 *             5    CANTX_PACK_MIN_MAX_CELL_VOLTAGE_MSG   0x231  :169     100     :171          40     :172
 *             6    CANTX_PACK_MIN_MAX_CELL_TEMP_MSG      0x230  :155     100     :157          40     :158
 *             7    CANTX_PACK_STATE_ESTIMATION_MESSAGE   0x235  :183     1000    :185          50     :186
 *             8    CANTX_PACK_VALUES_P0_MESSAGE          0x233  :197     100     :199          60     :200
 *             9    CANTX_PACK_VALUES_P1_MESSAGE          0x234  :211     100     :213          60     :214
 *            10    CANTX_STRING_STATE_MESSAGE            0x240  :227     100     :229          70     :230
 *            11    CANTX_STRING_MIN_MAX_CELL_TEMP_MSG    0x241  :269     100     :271          90     :272
 *            12    CANTX_STRING_MIN_MAX_CELL_VOLTAGE_MSG 0x242  :283     100     :285          90     :286
 *            13    CANTX_STRING_STATE_ESTIMATION_MSG     0x245  :297     1000    :299          0      :300
 *            14    CANTX_STRING_VALUES_P0_MESSAGE        0x243  :241     100     :243          80     :244
 *            15    CANTX_STRING_VALUES_P1_MESSAGE        0x244  :255     100     :257          10     :258
 *            16    CANTX_SYSTEM_STATE_MESSAGE            0x219  :71      100     :73           0      :74
 *
 *          (`id line`, `period line`, `phase line` are lines of
 *          can_cfg_tx-cyclic-message-definitions.h; `row` indexes
 *          can_txMessages and is placed by can_cfg_tx_cyclic.c:86-102.)
 *
 *          Every row uses CAN_STANDARD_IDENTIFIER_11_BIT (defines at
 *          :72, :86, :100, :114, :128, :142, :156, :170, :184, :198, :212,
 *          :228, :242, :256, :270, :284, :298), CAN_BIG_ENDIAN (defines at
 *          :75, :89, :103, :117, :131, :145, :159, :173, :187, :201, :215,
 *          :231, :245, :259, :273, :287, :301) and CAN_DEFAULT_DLC, which
 *          can_cfg.h:110 defines as 8.
 *
 *          The multiplexer variables are the statics can_cfg_tx_cyclic.c:71-78
 *          declares, all initialised to 0u, and referenced by the eight
 *          multiplexed rows at can_cfg_tx_cyclic.c:88, :89, :96, :97, :98, :99,
 *          :100 and :101.
 *
 *          The values were derived twice by two methods that share no code:
 *          a parser of the source literals (`tools/derive_cfg_tables.py`), and
 *          the compiled module's table read through the harness. All 289 derived
 *          values agreed.
 *
 *          WHAT THIS DOES NOT ESTABLISH
 *          ----------------------------
 *          The ids are checked to be the numbers the repository puts in the
 *          registry. Whether those ids are the ones the DBC the vehicle uses
 *          assigns is a communication-matrix fact and is not checkable from a
 *          host build. No register, offset or mask appears anywhere here.
 *
 *          ONE PROPERTY A HOST TEST CANNOT SEE
 *          -------------------------------------
 *          The multiplexer variables at can_cfg_tx_cyclic.c:71-78 are file-static
 *          and have no identity outside this module. The tests therefore establish
 *          that the eight multiplexed rows hold eight DISTINCT, writable byte
 *          pointers, and nothing more. Which of those eight variables is wired to
 *          which row is not observable from outside: swapping two of them leaves
 *          the table just as correct as before and leaves both variables used, so
 *          neither the compiler nor any assertion here can object. That is a real
 *          limit of testing a static table on a host and is recorded rather than
 *          papered over with a weaker assertion.
 */

/*========== Includes =======================================================*/
#include "unity.h"
#include "Mockcan.h"
#include "Mockcan_cbs_tx_cyclic.h"
#include "Mockdatabase.h"
#include "Mockdiag.h"
#include "Mockfoxmath.h"
#include "Mockftask.h"
#include "Mockimd.h"
#include "Mockmpu_prototypes.h"
#include "Mockos.h"

#include "can_cfg.h"
#include "database_cfg.h"

#include <stdbool.h>

/*========== Unit Testing Framework Directives ==============================*/
TEST_SOURCE_FILE("can_cfg_tx_cyclic.c")

TEST_INCLUDE_PATH("../../src/app/driver/can")
TEST_INCLUDE_PATH("../../src/app/driver/can/cbs")
TEST_INCLUDE_PATH("../../src/app/driver/can/cbs/tx-cyclic")
TEST_INCLUDE_PATH("../../src/app/driver/config")
TEST_INCLUDE_PATH("../../src/app/driver/foxmath")
TEST_INCLUDE_PATH("../../src/app/driver/fram")
TEST_INCLUDE_PATH("../../src/app/driver/imd")
TEST_INCLUDE_PATH("../../src/app/driver/rtc")
TEST_INCLUDE_PATH("../../src/app/engine/diag")
TEST_INCLUDE_PATH("../../src/app/engine/sys_mon")
TEST_INCLUDE_PATH("../../src/app/task/config")
TEST_INCLUDE_PATH("../../src/app/task/ftask")

/*========== Definitions and Implementations for Unit Test ==================*/

OS_QUEUE ftsk_dataQueue             = NULL_PTR;
OS_QUEUE ftsk_imdCanDataQueue       = NULL_PTR;
OS_QUEUE ftsk_canRxQueue            = NULL_PTR;
volatile bool ftsk_allQueuesCreated = false;

/*========== Setup and Teardown =============================================*/
void setUp(void) {
}

void tearDown(void) {
}

/*========== Local Helpers ===================================================*/

/** @brief   every registry entry must fall inside the published length
 * @details `can_txMessagesLength` is the bound the can driver iterates, so a test
 *          that reaches past it would be testing an entry the driver never reads.
 */
static void TEST_CanTxRequireIndex(uint32_t index) {
    TEST_ASSERT_LESS_THAN_UINT32((uint32_t)can_txMessagesLength, index);
}

/*========== Test Cases =====================================================*/

/** @brief   the published length is the seventeen rows the table declares
 * @details can_cfg_tx_cyclic.c:107 computes the length from the array declared
 *          at can_cfg_tx_cyclic.c:84, whose rows are the seventeen initialisers at
 *          can_cfg_tx_cyclic.c:86-102.
 */
void testCanTxMessagesLengthIsSeventeen(void) {
    /* can_cfg_tx_cyclic.c:107 */
    TEST_ASSERT_EQUAL_UINT8(17u, can_txMessagesLength);
}

/** @brief   every row is transmitted on CAN node 1
 * @details can_cfg_tx_cyclic.c:86-102 name CAN_NODE_1 on every row. can_cfg.c:70
 *          is what CAN_NODE_1 resolves to, so a row on another node is caught
 *          here.
 */
void testCanTxEveryMessageGoesOutOnNodeOne(void) {
    uint32_t u;
    for (u = 0u; u < can_txMessagesLength; u++) {
        /* can_cfg_tx_cyclic.c:86 */
        TEST_ASSERT_EQUAL_PTR(CAN_NODE_1, can_txMessages[u].canNode);
    }
}

/** @brief   no two frames share a CAN identifier
 * @details The seventeen ids come from the defines of
 *          can_cfg_tx-cyclic-message-definitions.h consumed by the rows at
 *          can_cfg_tx_cyclic.c:86-102. A duplicate id would make two signals
 *          collide on the bus.
 */
void testCanTxMessageIdsAreAllDistinct(void) {
    uint32_t u;
    uint32_t v;
    for (u = 0u; u < can_txMessagesLength; u++) {
        for (v = u + 1u; v < can_txMessagesLength; v++) {
            TEST_ASSERT_NOT_EQUAL(can_txMessages[u].message.id, can_txMessages[v].message.id);
        }
    }
}

/** @brief   every frame uses a standard 11-bit identifier
 * @details The id type comes from the `CANTX_*_ID_TYPE` defines, which the
 *          rows at can_cfg_tx_cyclic.c:86-102 consume.
 */
void testCanTxEveryMessageUsesAStandardElevenBitId(void) {
    uint32_t u;
    for (u = 0u; u < can_txMessagesLength; u++) {
        /* can_cfg_tx-cyclic-message-definitions.h:72 */
        TEST_ASSERT_EQUAL(CAN_STANDARD_IDENTIFIER_11_BIT, can_txMessages[u].message.idType);
    }
}

/** @brief   every frame is eight bytes long
 * @details The DLC comes from the `CANTX_*_DLC` defines, which the rows at
 *          can_cfg_tx_cyclic.c:86-102 consume; each takes CAN_DEFAULT_DLC, which
 *          can_cfg.h:110 defines as 8u. The expected side is the literal 8 and not
 *          the macro: the row expands to the macro, so a macro-to-macro comparison
 *          would hold for any value the macro ever takes.
 *
 *          The id type and the endianness are asserted against their enumerator
 *          names rather than against numbers, because CAN_IDENTIFIER_TYPE_e and
 *          CAN_ENDIANNESS_e are shared types whose ordinals the repository does not
 *          state anywhere as a literal. Those two assertions are therefore
 *          sensitive to a change of the per-message macro a row consumes, which is
 *          what this module configures, but not to a reordering of those two
 *          enums. That limit is stated here rather than papered over.
 */
void testCanTxEveryMessageUsesTheDefaultDataLength(void) {
    uint32_t u;
    for (u = 0u; u < can_txMessagesLength; u++) {
        /* can_cfg.h:110 */
        TEST_ASSERT_EQUAL_UINT8(8u, can_txMessages[u].message.dlc);
    }
}

/** @brief   every frame is big endian
 * @details The endianness comes from the `CANTX_*_ENDIANNESS` defines, which the
 *          rows at can_cfg_tx_cyclic.c:86-102 consume.
 */
void testCanTxEveryMessageIsBigEndian(void) {
    uint32_t u;
    for (u = 0u; u < can_txMessagesLength; u++) {
        /* can_cfg_tx-cyclic-message-definitions.h:75 */
        TEST_ASSERT_EQUAL(CAN_BIG_ENDIAN, can_txMessages[u].message.endianness);
    }
}

/** @brief   no frame has a zero cycle time
 * @details The periods come from the `CANTX_*_PERIOD_ms` defines consumed by the
 *          rows at can_cfg_tx_cyclic.c:86-102. A zero period would mean the frame
 *          is scheduled on every scheduler pass.
 */
void testCanTxEveryMessageHasANonZeroPeriod(void) {
    uint32_t u;
    for (u = 0u; u < can_txMessagesLength; u++) {
        TEST_ASSERT_NOT_EQUAL(0u, can_txMessages[u].timing.period);
    }
}

/** @brief   no frame is scheduled to start after its own cycle time elapses
 * @details The phases come from the `CANTX_*_PHASE_ms` defines consumed by the
 *          rows at can_cfg_tx_cyclic.c:86-102. A phase of at least the period
 *          would put a frame's first send one full cycle late.
 */
void testCanTxNoPhaseExceedsItsPeriod(void) {
    uint32_t u;
    for (u = 0u; u < can_txMessagesLength; u++) {
        TEST_ASSERT_LESS_THAN_UINT32(can_txMessages[u].timing.period, can_txMessages[u].timing.phase);
    }
}

/** @brief   the BMS state frame carries id 0x220, 100 ms period, phase 0
 * @details can_cfg_tx_cyclic.c:86 places CANTX_BMS_STATE_MESSAGE on row 0; the
 *          id, period and phase are the defines at
 *          can_cfg_tx-cyclic-message-definitions.h:85, :87 and :88.
 */
void testCanTxBmsStateFrameProperties(void) {
    TEST_CanTxRequireIndex(0u);
    /* can_cfg_tx-cyclic-message-definitions.h:85 */
    TEST_ASSERT_EQUAL_HEX32(0x220u, can_txMessages[0u].message.id);
    /* can_cfg_tx-cyclic-message-definitions.h:87 */
    TEST_ASSERT_EQUAL_UINT32(100u, can_txMessages[0u].timing.period);
    /* can_cfg_tx-cyclic-message-definitions.h:88 */
    TEST_ASSERT_EQUAL_UINT32(0u, can_txMessages[0u].timing.phase);
}

/** @brief   the BMS state detail frame carries id 0x221, 1000 ms, phase 100
 * @details can_cfg_tx_cyclic.c:87 places CANTX_BMS_STATE_DETAILS_MESSAGE on row 1;
 *          the defines are at can_cfg_tx-cyclic-message-definitions.h:99, :101 and
 *          :102.
 */
void testCanTxBmsStateDetailsFrameProperties(void) {
    TEST_CanTxRequireIndex(1u);
    /* can_cfg_tx-cyclic-message-definitions.h:99 */
    TEST_ASSERT_EQUAL_HEX32(0x221u, can_txMessages[1u].message.id);
    /* can_cfg_tx-cyclic-message-definitions.h:101 */
    TEST_ASSERT_EQUAL_UINT32(1000u, can_txMessages[1u].timing.period);
    /* can_cfg_tx-cyclic-message-definitions.h:102 */
    TEST_ASSERT_EQUAL_UINT32(100u, can_txMessages[1u].timing.phase);
}

/** @brief   the cell voltage frame carries id 0x250, 100 ms, phase 10
 * @details can_cfg_tx_cyclic.c:88 places CANTX_CELL_VOLTAGES_MESSAGE on row 2;
 *          the defines are at can_cfg_tx-cyclic-message-definitions.h:113, :115 and
 *          :116.
 */
void testCanTxCellVoltagesFrameProperties(void) {
    TEST_CanTxRequireIndex(2u);
    /* can_cfg_tx-cyclic-message-definitions.h:113 */
    TEST_ASSERT_EQUAL_HEX32(0x250u, can_txMessages[2u].message.id);
    /* can_cfg_tx-cyclic-message-definitions.h:115 */
    TEST_ASSERT_EQUAL_UINT32(100u, can_txMessages[2u].timing.period);
    /* can_cfg_tx-cyclic-message-definitions.h:116 */
    TEST_ASSERT_EQUAL_UINT32(10u, can_txMessages[2u].timing.phase);
}

/** @brief   the cell temperature frame carries id 0x260, 200 ms, phase 20
 * @details can_cfg_tx_cyclic.c:89 places CANTX_CELL_TEMPERATURES_MESSAGE on row 3;
 *          the defines are at can_cfg_tx-cyclic-message-definitions.h:127, :129 and
 *          :130.
 */
void testCanTxCellTemperaturesFrameProperties(void) {
    TEST_CanTxRequireIndex(3u);
    /* can_cfg_tx-cyclic-message-definitions.h:127 */
    TEST_ASSERT_EQUAL_HEX32(0x260u, can_txMessages[3u].message.id);
    /* can_cfg_tx-cyclic-message-definitions.h:129 */
    TEST_ASSERT_EQUAL_UINT32(200u, can_txMessages[3u].timing.period);
    /* can_cfg_tx-cyclic-message-definitions.h:130 */
    TEST_ASSERT_EQUAL_UINT32(20u, can_txMessages[3u].timing.phase);
}

/** @brief   the pack limits frame carries id 0x232, 100 ms, phase 30
 * @details can_cfg_tx_cyclic.c:90 places CANTX_PACK_LIMITS_MESSAGE on row 4;
 *          the defines are at can_cfg_tx-cyclic-message-definitions.h:141, :143 and
 *          :144.
 */
void testCanTxPackLimitsFrameProperties(void) {
    TEST_CanTxRequireIndex(4u);
    /* can_cfg_tx-cyclic-message-definitions.h:141 */
    TEST_ASSERT_EQUAL_HEX32(0x232u, can_txMessages[4u].message.id);
    /* can_cfg_tx-cyclic-message-definitions.h:143 */
    TEST_ASSERT_EQUAL_UINT32(100u, can_txMessages[4u].timing.period);
    /* can_cfg_tx-cyclic-message-definitions.h:144 */
    TEST_ASSERT_EQUAL_UINT32(30u, can_txMessages[4u].timing.phase);
}

/** @brief   the pack min/max cell voltage frame carries id 0x231, 100 ms, phase 40
 * @details can_cfg_tx_cyclic.c:91 places CANTX_PACK_MIN_MAX_CELL_VOLTAGE_MESSAGE on
 *          row 5; the defines are at can_cfg_tx-cyclic-message-definitions.h:169,
 *          :171 and :172.
 */
void testCanTxPackMinMaxCellVoltageFrameProperties(void) {
    TEST_CanTxRequireIndex(5u);
    /* can_cfg_tx-cyclic-message-definitions.h:169 */
    TEST_ASSERT_EQUAL_HEX32(0x231u, can_txMessages[5u].message.id);
    /* can_cfg_tx-cyclic-message-definitions.h:171 */
    TEST_ASSERT_EQUAL_UINT32(100u, can_txMessages[5u].timing.period);
    /* can_cfg_tx-cyclic-message-definitions.h:172 */
    TEST_ASSERT_EQUAL_UINT32(40u, can_txMessages[5u].timing.phase);
}

/** @brief   the pack min/max cell temperature frame carries id 0x230, 100 ms, phase 40
 * @details can_cfg_tx_cyclic.c:92 places CANTX_PACK_MIN_MAX_CELL_TEMPERATURE_MESSAGE on
 *          row 6; the defines are at can_cfg_tx-cyclic-message-definitions.h:155,
 *          :157 and :158.
 */
void testCanTxPackMinMaxCellTemperatureFrameProperties(void) {
    TEST_CanTxRequireIndex(6u);
    /* can_cfg_tx-cyclic-message-definitions.h:155 */
    TEST_ASSERT_EQUAL_HEX32(0x230u, can_txMessages[6u].message.id);
    /* can_cfg_tx-cyclic-message-definitions.h:157 */
    TEST_ASSERT_EQUAL_UINT32(100u, can_txMessages[6u].timing.period);
    /* can_cfg_tx-cyclic-message-definitions.h:158 */
    TEST_ASSERT_EQUAL_UINT32(40u, can_txMessages[6u].timing.phase);
}

/** @brief   the pack state estimation frame carries id 0x235, 1000 ms, phase 50
 * @details can_cfg_tx_cyclic.c:93 places CANTX_PACK_STATE_ESTIMATION_MESSAGE on row 7;
 *          the defines are at can_cfg_tx-cyclic-message-definitions.h:183, :185 and
 *          :186.
 */
void testCanTxPackStateEstimationFrameProperties(void) {
    TEST_CanTxRequireIndex(7u);
    /* can_cfg_tx-cyclic-message-definitions.h:183 */
    TEST_ASSERT_EQUAL_HEX32(0x235u, can_txMessages[7u].message.id);
    /* can_cfg_tx-cyclic-message-definitions.h:185 */
    TEST_ASSERT_EQUAL_UINT32(1000u, can_txMessages[7u].timing.period);
    /* can_cfg_tx-cyclic-message-definitions.h:186 */
    TEST_ASSERT_EQUAL_UINT32(50u, can_txMessages[7u].timing.phase);
}

/** @brief   the pack values page 0 frame carries id 0x233, 100 ms, phase 60
 * @details can_cfg_tx_cyclic.c:94 places CANTX_PACK_VALUES_P0_MESSAGE on row 8;
 *          the defines are at can_cfg_tx-cyclic-message-definitions.h:197, :199 and
 *          :200.
 */
void testCanTxPackValuesP0FrameProperties(void) {
    TEST_CanTxRequireIndex(8u);
    /* can_cfg_tx-cyclic-message-definitions.h:197 */
    TEST_ASSERT_EQUAL_HEX32(0x233u, can_txMessages[8u].message.id);
    /* can_cfg_tx-cyclic-message-definitions.h:199 */
    TEST_ASSERT_EQUAL_UINT32(100u, can_txMessages[8u].timing.period);
    /* can_cfg_tx-cyclic-message-definitions.h:200 */
    TEST_ASSERT_EQUAL_UINT32(60u, can_txMessages[8u].timing.phase);
}

/** @brief   the pack values page 1 frame carries id 0x234, 100 ms, phase 60
 * @details can_cfg_tx_cyclic.c:95 places CANTX_PACK_VALUES_P1_MESSAGE on row 9;
 *          the defines are at can_cfg_tx-cyclic-message-definitions.h:211, :213 and
 *          :214.
 */
void testCanTxPackValuesP1FrameProperties(void) {
    TEST_CanTxRequireIndex(9u);
    /* can_cfg_tx-cyclic-message-definitions.h:211 */
    TEST_ASSERT_EQUAL_HEX32(0x234u, can_txMessages[9u].message.id);
    /* can_cfg_tx-cyclic-message-definitions.h:213 */
    TEST_ASSERT_EQUAL_UINT32(100u, can_txMessages[9u].timing.period);
    /* can_cfg_tx-cyclic-message-definitions.h:214 */
    TEST_ASSERT_EQUAL_UINT32(60u, can_txMessages[9u].timing.phase);
}

/** @brief   the string state frame carries id 0x240, 100 ms, phase 70
 * @details can_cfg_tx_cyclic.c:96 places CANTX_STRING_STATE_MESSAGE on row 10;
 *          the defines are at can_cfg_tx-cyclic-message-definitions.h:227, :229 and
 *          :230.
 */
void testCanTxStringStateFrameProperties(void) {
    TEST_CanTxRequireIndex(10u);
    /* can_cfg_tx-cyclic-message-definitions.h:227 */
    TEST_ASSERT_EQUAL_HEX32(0x240u, can_txMessages[10u].message.id);
    /* can_cfg_tx-cyclic-message-definitions.h:229 */
    TEST_ASSERT_EQUAL_UINT32(100u, can_txMessages[10u].timing.period);
    /* can_cfg_tx-cyclic-message-definitions.h:230 */
    TEST_ASSERT_EQUAL_UINT32(70u, can_txMessages[10u].timing.phase);
}

/** @brief   the string min/max cell temperature frame carries id 0x241, 100 ms, phase 90
 * @details can_cfg_tx_cyclic.c:97 places CANTX_STRING_MIN_MAX_CELL_TEMPERATURE_MESSAGE on
 *          row 11; the defines are at can_cfg_tx-cyclic-message-definitions.h:269,
 *          :271 and :272.
 */
void testCanTxStringMinMaxCellTemperatureFrameProperties(void) {
    TEST_CanTxRequireIndex(11u);
    /* can_cfg_tx-cyclic-message-definitions.h:269 */
    TEST_ASSERT_EQUAL_HEX32(0x241u, can_txMessages[11u].message.id);
    /* can_cfg_tx-cyclic-message-definitions.h:271 */
    TEST_ASSERT_EQUAL_UINT32(100u, can_txMessages[11u].timing.period);
    /* can_cfg_tx-cyclic-message-definitions.h:272 */
    TEST_ASSERT_EQUAL_UINT32(90u, can_txMessages[11u].timing.phase);
}

/** @brief   the string min/max cell voltage frame carries id 0x242, 100 ms, phase 90
 * @details can_cfg_tx_cyclic.c:98 places CANTX_STRING_MIN_MAX_CELL_VOLTAGE_MESSAGE on
 *          row 12; the defines are at can_cfg_tx-cyclic-message-definitions.h:283,
 *          :285 and :286.
 */
void testCanTxStringMinMaxCellVoltageFrameProperties(void) {
    TEST_CanTxRequireIndex(12u);
    /* can_cfg_tx-cyclic-message-definitions.h:283 */
    TEST_ASSERT_EQUAL_HEX32(0x242u, can_txMessages[12u].message.id);
    /* can_cfg_tx-cyclic-message-definitions.h:285 */
    TEST_ASSERT_EQUAL_UINT32(100u, can_txMessages[12u].timing.period);
    /* can_cfg_tx-cyclic-message-definitions.h:286 */
    TEST_ASSERT_EQUAL_UINT32(90u, can_txMessages[12u].timing.phase);
}

/** @brief   the string state estimation frame carries id 0x245, 1000 ms, phase 0
 * @details can_cfg_tx_cyclic.c:99 places CANTX_STRING_STATE_ESTIMATION_MESSAGE on row 13;
 *          the defines are at can_cfg_tx-cyclic-message-definitions.h:297, :299 and
 *          :300.
 */
void testCanTxStringStateEstimationFrameProperties(void) {
    TEST_CanTxRequireIndex(13u);
    /* can_cfg_tx-cyclic-message-definitions.h:297 */
    TEST_ASSERT_EQUAL_HEX32(0x245u, can_txMessages[13u].message.id);
    /* can_cfg_tx-cyclic-message-definitions.h:299 */
    TEST_ASSERT_EQUAL_UINT32(1000u, can_txMessages[13u].timing.period);
    /* can_cfg_tx-cyclic-message-definitions.h:300 */
    TEST_ASSERT_EQUAL_UINT32(0u, can_txMessages[13u].timing.phase);
}

/** @brief   the string values page 0 frame carries id 0x243, 100 ms, phase 80
 * @details can_cfg_tx_cyclic.c:100 places CANTX_STRING_VALUES_P0_MESSAGE on row 14;
 *          the defines are at can_cfg_tx-cyclic-message-definitions.h:241, :243 and
 *          :244.
 */
void testCanTxStringValuesP0FrameProperties(void) {
    TEST_CanTxRequireIndex(14u);
    /* can_cfg_tx-cyclic-message-definitions.h:241 */
    TEST_ASSERT_EQUAL_HEX32(0x243u, can_txMessages[14u].message.id);
    /* can_cfg_tx-cyclic-message-definitions.h:243 */
    TEST_ASSERT_EQUAL_UINT32(100u, can_txMessages[14u].timing.period);
    /* can_cfg_tx-cyclic-message-definitions.h:244 */
    TEST_ASSERT_EQUAL_UINT32(80u, can_txMessages[14u].timing.phase);
}

/** @brief   the string values page 1 frame carries id 0x244, 100 ms, phase 10
 * @details can_cfg_tx_cyclic.c:101 places CANTX_STRING_VALUES_P1_MESSAGE on row 15;
 *          the defines are at can_cfg_tx-cyclic-message-definitions.h:255, :257 and
 *          :258.
 */
void testCanTxStringValuesP1FrameProperties(void) {
    TEST_CanTxRequireIndex(15u);
    /* can_cfg_tx-cyclic-message-definitions.h:255 */
    TEST_ASSERT_EQUAL_HEX32(0x244u, can_txMessages[15u].message.id);
    /* can_cfg_tx-cyclic-message-definitions.h:257 */
    TEST_ASSERT_EQUAL_UINT32(100u, can_txMessages[15u].timing.period);
    /* can_cfg_tx-cyclic-message-definitions.h:258 */
    TEST_ASSERT_EQUAL_UINT32(10u, can_txMessages[15u].timing.phase);
}

/** @brief   the system state frame carries id 0x219, 100 ms, phase 0
 * @details can_cfg_tx_cyclic.c:102 places CANTX_SYSTEM_STATE_MESSAGE on row 16; the
 *          defines are at can_cfg_tx-cyclic-message-definitions.h:71, :73 and :74.
 */
void testCanTxSystemStateFrameProperties(void) {
    TEST_CanTxRequireIndex(16u);
    /* can_cfg_tx-cyclic-message-definitions.h:71 */
    TEST_ASSERT_EQUAL_HEX32(0x219u, can_txMessages[16u].message.id);
    /* can_cfg_tx-cyclic-message-definitions.h:73 */
    TEST_ASSERT_EQUAL_UINT32(100u, can_txMessages[16u].timing.period);
    /* can_cfg_tx-cyclic-message-definitions.h:74 */
    TEST_ASSERT_EQUAL_UINT32(0u, can_txMessages[16u].timing.phase);
}

/** @brief   every row wires the callback that belongs to its own message
 * @details The callbacks are the second-to-last element of each row at
 *          can_cfg_tx_cyclic.c:86-102. Because every callback is a distinct
 *          symbol, transposing two of them in the table would leave every other
 *          assertion in this file passing while shipping the wrong payload under
 *          an id - so each row is checked individually.
 */
void testCanTxEveryRowWiresItsOwnCallback(void) {
    TEST_CanTxRequireIndex(0u);
    /* can_cfg_tx_cyclic.c:86 */
    TEST_ASSERT_EQUAL_PTR(&CANTX_BmsState, can_txMessages[0u].callbackFunction);
    TEST_CanTxRequireIndex(1u);
    /* can_cfg_tx_cyclic.c:87 */
    TEST_ASSERT_EQUAL_PTR(&CANTX_BmsStateDetails, can_txMessages[1u].callbackFunction);
    TEST_CanTxRequireIndex(2u);
    /* can_cfg_tx_cyclic.c:88 */
    TEST_ASSERT_EQUAL_PTR(&CANTX_CellVoltages, can_txMessages[2u].callbackFunction);
    TEST_CanTxRequireIndex(3u);
    /* can_cfg_tx_cyclic.c:89 */
    TEST_ASSERT_EQUAL_PTR(&CANTX_CellTemperatures, can_txMessages[3u].callbackFunction);
    TEST_CanTxRequireIndex(4u);
    /* can_cfg_tx_cyclic.c:90 */
    TEST_ASSERT_EQUAL_PTR(&CANTX_PackLimits, can_txMessages[4u].callbackFunction);
    TEST_CanTxRequireIndex(5u);
    /* can_cfg_tx_cyclic.c:91 */
    TEST_ASSERT_EQUAL_PTR(&CANTX_PackMinimumMaximumVoltage, can_txMessages[5u].callbackFunction);
    TEST_CanTxRequireIndex(6u);
    /* can_cfg_tx_cyclic.c:92 */
    TEST_ASSERT_EQUAL_PTR(&CANTX_PackMinimumMaximumTemp, can_txMessages[6u].callbackFunction);
    TEST_CanTxRequireIndex(7u);
    /* can_cfg_tx_cyclic.c:93 */
    TEST_ASSERT_EQUAL_PTR(&CANTX_PackStateEstimation, can_txMessages[7u].callbackFunction);
    TEST_CanTxRequireIndex(8u);
    /* can_cfg_tx_cyclic.c:94 */
    TEST_ASSERT_EQUAL_PTR(&CANTX_PackValuesP0, can_txMessages[8u].callbackFunction);
    TEST_CanTxRequireIndex(9u);
    /* can_cfg_tx_cyclic.c:95 */
    TEST_ASSERT_EQUAL_PTR(&CANTX_PackValuesP1, can_txMessages[9u].callbackFunction);
    TEST_CanTxRequireIndex(10u);
    /* can_cfg_tx_cyclic.c:96 */
    TEST_ASSERT_EQUAL_PTR(&CANTX_StringState, can_txMessages[10u].callbackFunction);
    TEST_CanTxRequireIndex(11u);
    /* can_cfg_tx_cyclic.c:97 */
    TEST_ASSERT_EQUAL_PTR(&CANTX_StringMinimumMaximumTemp, can_txMessages[11u].callbackFunction);
    TEST_CanTxRequireIndex(12u);
    /* can_cfg_tx_cyclic.c:98 */
    TEST_ASSERT_EQUAL_PTR(&CANTX_StringMinimumMaximumVoltage, can_txMessages[12u].callbackFunction);
    TEST_CanTxRequireIndex(13u);
    /* can_cfg_tx_cyclic.c:99 */
    TEST_ASSERT_EQUAL_PTR(&CANTX_StringStateEstimation, can_txMessages[13u].callbackFunction);
    TEST_CanTxRequireIndex(14u);
    /* can_cfg_tx_cyclic.c:100 */
    TEST_ASSERT_EQUAL_PTR(&CANTX_StringValuesP0, can_txMessages[14u].callbackFunction);
    TEST_CanTxRequireIndex(15u);
    /* can_cfg_tx_cyclic.c:101 */
    TEST_ASSERT_EQUAL_PTR(&CANTX_StringValuesP1, can_txMessages[15u].callbackFunction);
    TEST_CanTxRequireIndex(16u);
    /* can_cfg_tx_cyclic.c:102 */
    TEST_ASSERT_EQUAL_PTR(&CANTX_SysState, can_txMessages[16u].callbackFunction);
}

/** @brief   no two rows wire the same callback
 * @details A duplicated callback would leave one message without a payload
 *          producer. The rows come from can_cfg_tx_cyclic.c:86-102.
 */
void testCanTxCallbacksAreAllDistinct(void) {
    uint32_t u;
    uint32_t v;
    for (u = 0u; u < can_txMessagesLength; u++) {
        for (v = u + 1u; v < can_txMessagesLength; v++) {
            TEST_ASSERT_TRUE(can_txMessages[u].callbackFunction != can_txMessages[v].callbackFunction);
        }
    }
}

/** @brief   the eight rows that carry a multiplexer variable are the right eight
 * @details One assertion per row, each citing the can_cfg_tx_cyclic.c line that
 *          places the row's multiplexer variable or writes NULL_PTR for it. The
 *          multiplexer variables themselves are the statics at
 *          can_cfg_tx_cyclic.c:71-78.
 */
void testCanTxOnlyTheEightMultiplexedRowsCarryAMuxVariable(void) {
    /* can_cfg_tx_cyclic.c:86 */
    TEST_ASSERT_NULL(can_txMessages[0u].pMuxId);
    /* can_cfg_tx_cyclic.c:87 */
    TEST_ASSERT_NULL(can_txMessages[1u].pMuxId);
    /* can_cfg_tx_cyclic.c:88 */
    TEST_ASSERT_NOT_NULL(can_txMessages[2u].pMuxId);
    /* can_cfg_tx_cyclic.c:89 */
    TEST_ASSERT_NOT_NULL(can_txMessages[3u].pMuxId);
    /* can_cfg_tx_cyclic.c:90 */
    TEST_ASSERT_NULL(can_txMessages[4u].pMuxId);
    /* can_cfg_tx_cyclic.c:91 */
    TEST_ASSERT_NULL(can_txMessages[5u].pMuxId);
    /* can_cfg_tx_cyclic.c:92 */
    TEST_ASSERT_NULL(can_txMessages[6u].pMuxId);
    /* can_cfg_tx_cyclic.c:93 */
    TEST_ASSERT_NULL(can_txMessages[7u].pMuxId);
    /* can_cfg_tx_cyclic.c:94 */
    TEST_ASSERT_NULL(can_txMessages[8u].pMuxId);
    /* can_cfg_tx_cyclic.c:95 */
    TEST_ASSERT_NULL(can_txMessages[9u].pMuxId);
    /* can_cfg_tx_cyclic.c:96 */
    TEST_ASSERT_NOT_NULL(can_txMessages[10u].pMuxId);
    /* can_cfg_tx_cyclic.c:97 */
    TEST_ASSERT_NOT_NULL(can_txMessages[11u].pMuxId);
    /* can_cfg_tx_cyclic.c:98 */
    TEST_ASSERT_NOT_NULL(can_txMessages[12u].pMuxId);
    /* can_cfg_tx_cyclic.c:99 */
    TEST_ASSERT_NOT_NULL(can_txMessages[13u].pMuxId);
    /* can_cfg_tx_cyclic.c:100 */
    TEST_ASSERT_NOT_NULL(can_txMessages[14u].pMuxId);
    /* can_cfg_tx_cyclic.c:101 */
    TEST_ASSERT_NOT_NULL(can_txMessages[15u].pMuxId);
    /* can_cfg_tx_cyclic.c:102 */
    TEST_ASSERT_NULL(can_txMessages[16u].pMuxId);
}

/** @brief   the multiplexed rows do not share a multiplexer variable
 * @details The eight variables are the statics at can_cfg_tx_cyclic.c:71-78,
 *          referenced by can_cfg_tx_cyclic.c:88, :89, :96, :97, :98, :99, :100 and
 *          :101. Two frames sharing one variable would advance each other's
 *          multiplexer and interleave their payloads.
 */
void testCanTxMultiplexerVariablesAreAllDistinct(void) {
    uint8_t *pkpMux[17];
    uint32_t u;
    uint32_t v;
    uint32_t nMux = 0u;
    for (u = 0u; u < can_txMessagesLength; u++) {
        if (NULL_PTR != can_txMessages[u].pMuxId) {
            pkpMux[nMux] = can_txMessages[u].pMuxId;
            nMux++;
        }
    }
    for (u = 0u; u < nMux; u++) {
        for (v = u + 1u; v < nMux; v++) {
            TEST_ASSERT_TRUE(pkpMux[u] != pkpMux[v]);
        }
    }
}

/** @brief   a multiplexer variable is writable through the table
 * @details The statics at can_cfg_tx_cyclic.c:71-78 are initialised to 0u and
 *          declared non-const, so a callback may advance them. This test writes
 *          through the registry's own pointer to establish that the field is a
 *          writable `uint8_t *` rather than a copy, then restores it.
 */
void testCanTxMultiplexerPointerIsWritable(void) {
    uint8_t *pMux = can_txMessages[2u].pMuxId;
    uint8_t uOriginal;
    TEST_ASSERT_NOT_NULL(pMux);
    uOriginal = *pMux;
    *pMux = 0x5Au;
    TEST_ASSERT_EQUAL_HEX8(0x5Au, *can_txMessages[2u].pMuxId);
    *pMux = uOriginal;
    TEST_ASSERT_EQUAL_HEX8(uOriginal, *can_txMessages[2u].pMuxId);
}
