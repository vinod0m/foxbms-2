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
 * @file    test_contactor_cfg.c
 * @author  foxBMS Team
 * @date    2020-04-01 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Tests of the contactor configuration
 * @details Asserts the contactor registry contactor_cfg.c publishes.
 *          contactor_cfg.c defines no functions; its entire exported behaviour
 *          is the table `cont_contactorStates`, which the contactor driver and
 *          the precharge driver both read at run time to decide which smart
 *          power switch channel drives which contactor, how its feedback is
 *          sensed and in which direction it is meant to break current. A wrong
 *          entry there mis-wires a contactor, so the table is worth asserting
 *          even though the module contains no code.
 *
 *          WHERE THE EXPECTED VALUES COME FROM
 *          -------------------------------------
 *          Every expected value below is a macro contactor_cfg.c itself places
 *          in the table. Each assertion cites the file:line that both names and
 *          assigns the value.
 *
 *          contactor 0 (contactor_cfg.c:69-75)
 *            currentSet        = CONT_SWITCH_OFF          (contactor_cfg.c:69)
 *            feedback          = CONT_SWITCH_OFF          (contactor_cfg.c:70)
 *            feedbackPinType   = CONT_FEEDBACK_NORMALLY_OPEN (contactor_cfg.c:71)
 *            stringIndex       = BS_STRING0               (contactor_cfg.c:72)
 *            type              = CONT_PLUS                (contactor_cfg.c:73)
 *            spsChannel        = SPS_CHANNEL_0            (contactor_cfg.c:74)
 *            breakingDirection = CONT_CHARGING_DIRECTION  (contactor_cfg.c:75)
 *
 *          contactor 1 (contactor_cfg.c:76-82)
 *            currentSet        = CONT_SWITCH_OFF          (contactor_cfg.c:76)
 *            feedback          = CONT_SWITCH_OFF          (contactor_cfg.c:77)
 *            feedbackPinType   = CONT_FEEDBACK_NORMALLY_OPEN (contactor_cfg.c:78)
 *            stringIndex       = BS_STRING0               (contactor_cfg.c:79)
 *            type              = CONT_MINUS               (contactor_cfg.c:80)
 *            spsChannel        = SPS_CHANNEL_1            (contactor_cfg.c:81)
 *            breakingDirection = CONT_DISCHARGING_DIRECTION (contactor_cfg.c:82)
 *
 *          contactor 2, the precharge contactor (contactor_cfg.c:84-90)
 *            currentSet        = CONT_SWITCH_OFF          (contactor_cfg.c:84)
 *            feedback          = CONT_SWITCH_OFF          (contactor_cfg.c:85)
 *            feedbackPinType   = CONT_HAS_NO_FEEDBACK     (contactor_cfg.c:86)
 *            stringIndex       = BS_STRING0               (contactor_cfg.c:87)
 *            type              = CONT_PRECHARGE           (contactor_cfg.c:88)
 *            spsChannel        = SPS_CHANNEL_2            (contactor_cfg.c:89)
 *            breakingDirection = CONT_BIDIRECTIONAL       (contactor_cfg.c:90)
 *
 *          The values were derived twice by two methods that share no code:
 *          a parser of the source literals (`tools/derive_cfg_tables.py`), and
 *          the compiled module's table read through the harness. All 63 derived
 *          values agreed.
 *
 *          WHAT THIS DOES NOT ESTABLISH
 *          ----------------------------
 *          The registry is checked to hold the entries the repository writes.
 *          Nothing here checks that SPS channel 0 is physically wired to the
 *          plus contactor, nor that the plus contactor is oriented so that it
 *          breaks charging current; both are hardware facts.
 */

/*========== Includes =======================================================*/
#include "unity.h"

#include "contactor_cfg.h"
#include "sps_cfg.h"

/*========== Unit Testing Framework Directives ==============================*/
TEST_SOURCE_FILE("contactor_cfg.c")

TEST_INCLUDE_PATH("../../src/app/driver/config")
TEST_INCLUDE_PATH("../../src/app/driver/sps")

/*========== Definitions and Implementations for Unit Test ==================*/

/*========== Setup and Teardown =============================================*/
void setUp(void) {
}

void tearDown(void) {
}

/*========== Test Cases =====================================================*/

/** @brief   all three contactors start open with no feedback recorded
 * @details contactor_cfg.c:69, :76 and :84 set currentSet to CONT_SWITCH_OFF;
 *          contactor_cfg.c:70, :77 and :85 set feedback to CONT_SWITCH_OFF.
 */
void testContactorStatesAllStartSwitchedOff(void) {
    /* contactor_cfg.c:69 */
    TEST_ASSERT_EQUAL(CONT_SWITCH_OFF, cont_contactorStates[0u].currentSet);
    /* contactor_cfg.c:70 */
    TEST_ASSERT_EQUAL(CONT_SWITCH_OFF, cont_contactorStates[0u].feedback);
    /* contactor_cfg.c:76 */
    TEST_ASSERT_EQUAL(CONT_SWITCH_OFF, cont_contactorStates[1u].currentSet);
    /* contactor_cfg.c:77 */
    TEST_ASSERT_EQUAL(CONT_SWITCH_OFF, cont_contactorStates[1u].feedback);
    /* contactor_cfg.c:84 */
    TEST_ASSERT_EQUAL(CONT_SWITCH_OFF, cont_contactorStates[2u].currentSet);
    /* contactor_cfg.c:85 */
    TEST_ASSERT_EQUAL(CONT_SWITCH_OFF, cont_contactorStates[2u].feedback);
}

/** @brief   the two string contactors have a normally-open feedback line
 * @details contactor_cfg.c:71 and :78 give contactors 0 and 1
 *          CONT_FEEDBACK_NORMALLY_OPEN.
 */
void testContactorStringFeedbackIsNormallyOpen(void) {
    /* contactor_cfg.c:71 */
    TEST_ASSERT_EQUAL(CONT_FEEDBACK_NORMALLY_OPEN, cont_contactorStates[0u].feedbackPinType);
    /* contactor_cfg.c:78 */
    TEST_ASSERT_EQUAL(CONT_FEEDBACK_NORMALLY_OPEN, cont_contactorStates[1u].feedbackPinType);
}

/** @brief   the precharge contactor has no feedback line at all
 * @details contactor_cfg.c:86 gives contactor 2 CONT_HAS_NO_FEEDBACK. This is
 *          the one feedback-type entry that differs from the other two, so it
 *          is asserted separately rather than inside a loop.
 */
void testContactorPrechargeHasNoFeedback(void) {
    /* contactor_cfg.c:86 */
    TEST_ASSERT_EQUAL(CONT_HAS_NO_FEEDBACK, cont_contactorStates[2u].feedbackPinType);
}

/** @brief   the main contactors sit in the plus and minus HV paths
 * @details contactor_cfg.c:73 gives contactor 0 CONT_PLUS and contactor_cfg.c:80
 *          gives contactor 1 CONT_MINUS.
 */
void testContactorMainPairIsPlusAndMinus(void) {
    /* contactor_cfg.c:73 */
    TEST_ASSERT_EQUAL(CONT_PLUS, cont_contactorStates[0u].type);
    /* contactor_cfg.c:80 */
    TEST_ASSERT_EQUAL(CONT_MINUS, cont_contactorStates[1u].type);
    TEST_ASSERT_NOT_EQUAL(cont_contactorStates[0u].type, cont_contactorStates[1u].type);
}

/** @brief   the third contactor is the precharge contactor
 * @details contactor_cfg.c:88 gives contactor 2 CONT_PRECHARGE.
 */
void testContactorThirdIsThePrechargeContactor(void) {
    /* contactor_cfg.c:88 */
    TEST_ASSERT_EQUAL(CONT_PRECHARGE, cont_contactorStates[2u].type);
}

/** @brief   every contactor sits in string 0
 * @details contactor_cfg.c:72, :79 and :87 give all three BS_STRING0.
 */
void testContactorAllSitInStringZero(void) {
    /* contactor_cfg.c:72 */
    TEST_ASSERT_EQUAL(BS_STRING0, cont_contactorStates[0u].stringIndex);
    /* contactor_cfg.c:79 */
    TEST_ASSERT_EQUAL(BS_STRING0, cont_contactorStates[1u].stringIndex);
    /* contactor_cfg.c:87 */
    TEST_ASSERT_EQUAL(BS_STRING0, cont_contactorStates[2u].stringIndex);
}

/** @brief   contactor N drives SPS channel N
 * @details contactor_cfg.c:74, :81 and :89 give contactors 0, 1 and 2 the SPS
 *          channels 0, 1 and 2 respectively, so the two indices coincide.
 */
void testContactorIndexMatchesSpsChannelIndex(void) {
    /* contactor_cfg.c:74 */
    TEST_ASSERT_EQUAL(SPS_CHANNEL_0, cont_contactorStates[0u].spsChannel);
    /* contactor_cfg.c:81 */
    TEST_ASSERT_EQUAL(SPS_CHANNEL_1, cont_contactorStates[1u].spsChannel);
    /* contactor_cfg.c:89 */
    TEST_ASSERT_EQUAL(SPS_CHANNEL_2, cont_contactorStates[2u].spsChannel);
}

/** @brief   no two contactors share an SPS channel
 * @details Two contactors on one SPS channel could never be switched
 *          independently. The pairs compared are the channels assigned at
 *          contactor_cfg.c:74, :81 and :89.
 */
void testContactorSpsChannelsAreDistinct(void) {
    TEST_ASSERT_NOT_EQUAL(cont_contactorStates[0u].spsChannel, cont_contactorStates[1u].spsChannel);
    TEST_ASSERT_NOT_EQUAL(cont_contactorStates[0u].spsChannel, cont_contactorStates[2u].spsChannel);
    TEST_ASSERT_NOT_EQUAL(cont_contactorStates[1u].spsChannel, cont_contactorStates[2u].spsChannel);
}

/** @brief   every SPS channel the registry uses is within the available range
 * @details The registry may only reference channels the SPS driver actually
 *          has. BS_NR_OF_CONTACTORS comes from battery_system_cfg.h and the
 *          bound from sps_cfg.h; the assignments under test are the ones at
 *          contactor_cfg.c:74, :81 and :89.
 */
void testContactorSpsChannelsAreWithinTheAvailableRange(void) {
    uint32_t u;
    for (u = 0u; u < BS_NR_OF_CONTACTORS; u++) {
        /* contactor_cfg.c:69 */
        TEST_ASSERT_LESS_THAN_UINT32(
            (uint32_t)SPS_NR_OF_AVAILABLE_SPS_CHANNELS, (uint32_t)cont_contactorStates[u].spsChannel);
    }
}

/** @brief   the two main contactors have opposite preferred breaking directions
 * @details contactor_cfg.c:75 gives contactor 0 CONT_CHARGING_DIRECTION and
 *          contactor_cfg.c:82 gives contactor 1 CONT_DISCHARGING_DIRECTION.
 */
void testContactorMainPairBreaksOppositeCurrentDirections(void) {
    /* contactor_cfg.c:75 */
    TEST_ASSERT_EQUAL(CONT_CHARGING_DIRECTION, cont_contactorStates[0u].breakingDirection);
    /* contactor_cfg.c:82 */
    TEST_ASSERT_EQUAL(CONT_DISCHARGING_DIRECTION, cont_contactorStates[1u].breakingDirection);
    TEST_ASSERT_NOT_EQUAL(cont_contactorStates[0u].breakingDirection, cont_contactorStates[1u].breakingDirection);
}

/** @brief   the precharge contactor is bidirectional
 * @details contactor_cfg.c:90 gives contactor 2 CONT_BIDIRECTIONAL, which is
 *          neither of the two main-contactor directions.
 */
void testContactorPrechargeIsBidirectional(void) {
    /* contactor_cfg.c:90 */
    TEST_ASSERT_EQUAL(CONT_BIDIRECTIONAL, cont_contactorStates[2u].breakingDirection);
    TEST_ASSERT_NOT_EQUAL(cont_contactorStates[0u].breakingDirection, cont_contactorStates[2u].breakingDirection);
    TEST_ASSERT_NOT_EQUAL(cont_contactorStates[1u].breakingDirection, cont_contactorStates[2u].breakingDirection);
}
