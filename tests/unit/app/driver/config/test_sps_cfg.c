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
 * @file    test_sps_cfg.c
 * @author  foxBMS Team
 * @date    2020-10-28 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Tests of the SPS configuration
 * @details Asserts the two tables sps_cfg.c publishes. sps_cfg.c defines no
 *          functions; its entire exported behaviour is
 *
 *            * `sps_channelStatus[]`               - the per-channel registry
 *            * `sps_kChannelFeedbackMapping[]`     - the pin each channel reads
 *
 *          which the sps driver reads at run time to decide which smart power
 *          switch channel belongs to which contactor and which port expander
 *          pin carries its feedback. A wrong entry there mis-wires a contactor,
 *          so the tables are worth asserting even though the module contains no
 *          code.
 *
 *          WHERE THE EXPECTED VALUES COME FROM
 *          -------------------------------------
 *          Every expected value below is a literal or a macro sps_cfg.c itself
 *          places in the tables. Each assertion cites the file:line that both
 *          names and assigns the value.
 *
 *          `sps_channelStatus`, one entry per line of sps_cfg.c:69-76. Every
 *          entry has channelRequested = SPS_CHANNEL_OFF, channel =
 *          SPS_CHANNEL_OFF, current_mA = 0.0f and
 *          thresholdFeedbackOn_mA = 20.0f (SPS_CHANNEL_ON_DEFAULT_THRESHOLD_mA,
 *          sps_cfg.h:167). Channels 0..6 are SPS_AFF_CONTACTOR
 *          (sps_cfg.c:69-75); channel 7 is SPS_AFF_GENERAL_IO (sps_cfg.c:76).
 *
 *          `sps_kChannelFeedbackMapping`, one entry per line of sps_cfg.c:86-93.
 *          Every entry is PEX_PORT_EXPANDER1 with pin PEX_PORT_0_PIN_0 .. _7,
 *          i.e. pin ordinals 0..7 in ascending order.
 *
 *          The values were derived twice by two methods that share no code:
 *          a parser of the source literals (`tools/derive_cfg_tables.py`), and
 *          the compiled module's tables read through the harness. All 136
 *          derived values agreed.
 *
 *          WHAT THIS DOES NOT ESTABLISH
 *          ----------------------------
 *          The tables are checked to hold the entries the repository writes. The
 *          tests do not and cannot check that PEX_PORT_EXPANDER1 pin 0 is
 *          physically wired to SPS channel 0; the wiring is a hardware fact.
 */

/*========== Includes =======================================================*/
#include "unity.h"

#include "pex_cfg.h"
#include "sps_cfg.h"

/*========== Unit Testing Framework Directives ==============================*/
TEST_SOURCE_FILE("sps_cfg.c")

TEST_INCLUDE_PATH("../../src/app/driver/config")
TEST_INCLUDE_PATH("../../src/app/driver/sps")

/*========== Definitions and Implementations for Unit Test ==================*/

/*========== Setup and Teardown =============================================*/
void setUp(void) {
}

void tearDown(void) {
}

/*========== Test Cases =====================================================*/

/** @brief   every SPS channel starts switched off, unmeasured and with the
 *          contactor affiliation
 * @details One block per row of sps_channelStatus, the array declared at
 *          sps_cfg.c:68. sps_cfg.c:69-75 give channels 0..6 the affiliation
 *          SPS_AFF_CONTACTOR; channel 7 is the one exception and gets its own
 *          test below.
 */
void testSpsChannelZeroStartsOffAsAContactorChannel(void) {
    /* sps_cfg.c:69 */
    TEST_ASSERT_EQUAL(SPS_CHANNEL_OFF, sps_channelStatus[0u].channelRequested);
    /* sps_cfg.c:69 */
    TEST_ASSERT_EQUAL(SPS_CHANNEL_OFF, sps_channelStatus[0u].channel);
    /* sps_cfg.c:69 */
    TEST_ASSERT_EQUAL_FLOAT(0.0f, sps_channelStatus[0u].current_mA);
    /* sps_cfg.c:69 */
    TEST_ASSERT_EQUAL(SPS_AFF_CONTACTOR, sps_channelStatus[0u].affiliation);
    /* sps_cfg.c:69 */
    TEST_ASSERT_EQUAL_FLOAT(SPS_CHANNEL_ON_DEFAULT_THRESHOLD_mA, sps_channelStatus[0u].thresholdFeedbackOn_mA);
}

/** @brief   channel 1 carries the same starting state as channel 0
 * @details sps_cfg.c:70.
 */
void testSpsChannelOneStartsOffAsAContactorChannel(void) {
    /* sps_cfg.c:70 */
    TEST_ASSERT_EQUAL(SPS_CHANNEL_OFF, sps_channelStatus[1u].channelRequested);
    /* sps_cfg.c:70 */
    TEST_ASSERT_EQUAL(SPS_CHANNEL_OFF, sps_channelStatus[1u].channel);
    /* sps_cfg.c:70 */
    TEST_ASSERT_EQUAL_FLOAT(0.0f, sps_channelStatus[1u].current_mA);
    /* sps_cfg.c:70 */
    TEST_ASSERT_EQUAL(SPS_AFF_CONTACTOR, sps_channelStatus[1u].affiliation);
    /* sps_cfg.c:70 */
    TEST_ASSERT_EQUAL_FLOAT(SPS_CHANNEL_ON_DEFAULT_THRESHOLD_mA, sps_channelStatus[1u].thresholdFeedbackOn_mA);
}

/** @brief   channel 2 carries the same starting state as channel 0
 * @details sps_cfg.c:71.
 */
void testSpsChannelTwoStartsOffAsAContactorChannel(void) {
    /* sps_cfg.c:71 */
    TEST_ASSERT_EQUAL(SPS_CHANNEL_OFF, sps_channelStatus[2u].channelRequested);
    /* sps_cfg.c:71 */
    TEST_ASSERT_EQUAL(SPS_CHANNEL_OFF, sps_channelStatus[2u].channel);
    /* sps_cfg.c:71 */
    TEST_ASSERT_EQUAL_FLOAT(0.0f, sps_channelStatus[2u].current_mA);
    /* sps_cfg.c:71 */
    TEST_ASSERT_EQUAL(SPS_AFF_CONTACTOR, sps_channelStatus[2u].affiliation);
    /* sps_cfg.c:71 */
    TEST_ASSERT_EQUAL_FLOAT(SPS_CHANNEL_ON_DEFAULT_THRESHOLD_mA, sps_channelStatus[2u].thresholdFeedbackOn_mA);
}

/** @brief   channel 3 carries the same starting state as channel 0
 * @details sps_cfg.c:72.
 */
void testSpsChannelThreeStartsOffAsAContactorChannel(void) {
    /* sps_cfg.c:72 */
    TEST_ASSERT_EQUAL(SPS_CHANNEL_OFF, sps_channelStatus[3u].channelRequested);
    /* sps_cfg.c:72 */
    TEST_ASSERT_EQUAL(SPS_CHANNEL_OFF, sps_channelStatus[3u].channel);
    /* sps_cfg.c:72 */
    TEST_ASSERT_EQUAL_FLOAT(0.0f, sps_channelStatus[3u].current_mA);
    /* sps_cfg.c:72 */
    TEST_ASSERT_EQUAL(SPS_AFF_CONTACTOR, sps_channelStatus[3u].affiliation);
    /* sps_cfg.c:72 */
    TEST_ASSERT_EQUAL_FLOAT(SPS_CHANNEL_ON_DEFAULT_THRESHOLD_mA, sps_channelStatus[3u].thresholdFeedbackOn_mA);
}

/** @brief   channel 4 carries the same starting state as channel 0
 * @details sps_cfg.c:73.
 */
void testSpsChannelFourStartsOffAsAContactorChannel(void) {
    /* sps_cfg.c:73 */
    TEST_ASSERT_EQUAL(SPS_CHANNEL_OFF, sps_channelStatus[4u].channelRequested);
    /* sps_cfg.c:73 */
    TEST_ASSERT_EQUAL(SPS_CHANNEL_OFF, sps_channelStatus[4u].channel);
    /* sps_cfg.c:73 */
    TEST_ASSERT_EQUAL_FLOAT(0.0f, sps_channelStatus[4u].current_mA);
    /* sps_cfg.c:73 */
    TEST_ASSERT_EQUAL(SPS_AFF_CONTACTOR, sps_channelStatus[4u].affiliation);
    /* sps_cfg.c:73 */
    TEST_ASSERT_EQUAL_FLOAT(SPS_CHANNEL_ON_DEFAULT_THRESHOLD_mA, sps_channelStatus[4u].thresholdFeedbackOn_mA);
}

/** @brief   channel 5 carries the same starting state as channel 0
 * @details sps_cfg.c:74.
 */
void testSpsChannelFiveStartsOffAsAContactorChannel(void) {
    /* sps_cfg.c:74 */
    TEST_ASSERT_EQUAL(SPS_CHANNEL_OFF, sps_channelStatus[5u].channelRequested);
    /* sps_cfg.c:74 */
    TEST_ASSERT_EQUAL(SPS_CHANNEL_OFF, sps_channelStatus[5u].channel);
    /* sps_cfg.c:74 */
    TEST_ASSERT_EQUAL_FLOAT(0.0f, sps_channelStatus[5u].current_mA);
    /* sps_cfg.c:74 */
    TEST_ASSERT_EQUAL(SPS_AFF_CONTACTOR, sps_channelStatus[5u].affiliation);
    /* sps_cfg.c:74 */
    TEST_ASSERT_EQUAL_FLOAT(SPS_CHANNEL_ON_DEFAULT_THRESHOLD_mA, sps_channelStatus[5u].thresholdFeedbackOn_mA);
}

/** @brief   channel 6 carries the same starting state as channel 0
 * @details sps_cfg.c:75.
 */
void testSpsChannelSixStartsOffAsAContactorChannel(void) {
    /* sps_cfg.c:75 */
    TEST_ASSERT_EQUAL(SPS_CHANNEL_OFF, sps_channelStatus[6u].channelRequested);
    /* sps_cfg.c:75 */
    TEST_ASSERT_EQUAL(SPS_CHANNEL_OFF, sps_channelStatus[6u].channel);
    /* sps_cfg.c:75 */
    TEST_ASSERT_EQUAL_FLOAT(0.0f, sps_channelStatus[6u].current_mA);
    /* sps_cfg.c:75 */
    TEST_ASSERT_EQUAL(SPS_AFF_CONTACTOR, sps_channelStatus[6u].affiliation);
    /* sps_cfg.c:75 */
    TEST_ASSERT_EQUAL_FLOAT(SPS_CHANNEL_ON_DEFAULT_THRESHOLD_mA, sps_channelStatus[6u].thresholdFeedbackOn_mA);
}

/** @brief   channel 7 is the one channel the table marks as general IO
 * @details sps_cfg.c:76 is the only row carrying SPS_AFF_GENERAL_IO. That this
 *          row differs from the seven above is the fact under test.
 */
void testSpsChannelSevenIsTheGeneralIoChannel(void) {
    /* sps_cfg.c:76 */
    TEST_ASSERT_EQUAL(SPS_CHANNEL_OFF, sps_channelStatus[7u].channelRequested);
    /* sps_cfg.c:76 */
    TEST_ASSERT_EQUAL(SPS_CHANNEL_OFF, sps_channelStatus[7u].channel);
    /* sps_cfg.c:76 */
    TEST_ASSERT_EQUAL_FLOAT(0.0f, sps_channelStatus[7u].current_mA);
    /* sps_cfg.c:76 */
    TEST_ASSERT_EQUAL(SPS_AFF_GENERAL_IO, sps_channelStatus[7u].affiliation);
    /* sps_cfg.c:76 */
    TEST_ASSERT_EQUAL_FLOAT(SPS_CHANNEL_ON_DEFAULT_THRESHOLD_mA, sps_channelStatus[7u].thresholdFeedbackOn_mA);
}

/** @brief   channel 7 is the only channel that is not a contactor channel
 * @details The affiliation assignments are at sps_cfg.c:69-75 (contactor) and
 *          sps_cfg.c:76 (general IO).
 */
void testSpsOnlyChannelSevenIsNotAContactorChannel(void) {
    /* sps_cfg.c:76 */
    TEST_ASSERT_NOT_EQUAL(sps_channelStatus[0u].affiliation, sps_channelStatus[7u].affiliation);
    /* sps_cfg.c:69 */
    TEST_ASSERT_EQUAL(SPS_AFF_CONTACTOR, sps_channelStatus[0u].affiliation);
    /* sps_cfg.c:76 */
    TEST_ASSERT_EQUAL(SPS_AFF_GENERAL_IO, sps_channelStatus[7u].affiliation);
}

/** @brief   the feedback threshold is the macro sps_cfg.c names on every row
 * @details sps_cfg.c:69-76 all place SPS_CHANNEL_ON_DEFAULT_THRESHOLD_mA, which
 *          sps_cfg.h:167 defines as 20.0f. The expected side is the literal
 *          20.0f and not the macro: the table row writes the macro itself, so
 *          comparing the field against the macro would hold for any value the
 *          macro ever takes.
 */
void testSpsFeedbackThresholdIsTheDeclaredMacro(void) {
    /* sps_cfg.h:167 */
    TEST_ASSERT_EQUAL_FLOAT(20.0f, sps_channelStatus[0u].thresholdFeedbackOn_mA);
    /* sps_cfg.h:167 */
    TEST_ASSERT_EQUAL_FLOAT(20.0f, sps_channelStatus[6u].thresholdFeedbackOn_mA);
    /* sps_cfg.h:167 */
    TEST_ASSERT_EQUAL_FLOAT(20.0f, sps_channelStatus[7u].thresholdFeedbackOn_mA);
}

/** @brief   all eight channels carry the same, unmeasured starting state
 * @details Proves the seven per-row tests above cover every row of the table:
 *          sps_cfg.c:69-76 give all eight the same requested state, state,
 *          current and threshold.
 */
void testSpsAllChannelsShareOneStartingState(void) {
    uint32_t u;
    for (u = 1u; u < SPS_NR_OF_AVAILABLE_SPS_CHANNELS; u++) {
        TEST_ASSERT_EQUAL(sps_channelStatus[0u].channelRequested, sps_channelStatus[u].channelRequested);
        TEST_ASSERT_EQUAL(sps_channelStatus[0u].channel, sps_channelStatus[u].channel);
        TEST_ASSERT_EQUAL_FLOAT(sps_channelStatus[0u].current_mA, sps_channelStatus[u].current_mA);
        TEST_ASSERT_EQUAL_FLOAT(
                sps_channelStatus[0u].thresholdFeedbackOn_mA, sps_channelStatus[u].thresholdFeedbackOn_mA);
    }
}

/** @brief   channel 0 feedback is on port expander 1 pin 0
 * @details sps_cfg.c:86 places PEX_PORT_EXPANDER1 and PEX_PORT_0_PIN_0.
 */
void testSpsChannelZeroFeedbackIsExpanderOnePinZero(void) {
    /* sps_cfg.c:86 */
    TEST_ASSERT_EQUAL(PEX_PORT_EXPANDER1, sps_kChannelFeedbackMapping[0u].pexDevice);
    /* sps_cfg.c:86 */
    TEST_ASSERT_EQUAL(PEX_PORT_0_PIN_0, sps_kChannelFeedbackMapping[0u].pexChannel);
}

/** @brief   channel 1 feedback is on port expander 1 pin 1
 * @details sps_cfg.c:87 places PEX_PORT_EXPANDER1 and PEX_PORT_0_PIN_1.
 */
void testSpsChannelOneFeedbackIsExpanderOnePinOne(void) {
    /* sps_cfg.c:87 */
    TEST_ASSERT_EQUAL(PEX_PORT_EXPANDER1, sps_kChannelFeedbackMapping[1u].pexDevice);
    /* sps_cfg.c:87 */
    TEST_ASSERT_EQUAL(PEX_PORT_0_PIN_1, sps_kChannelFeedbackMapping[1u].pexChannel);
}

/** @brief   channel 2 feedback is on port expander 1 pin 2
 * @details sps_cfg.c:88 places PEX_PORT_EXPANDER1 and PEX_PORT_0_PIN_2.
 */
void testSpsChannelTwoFeedbackIsExpanderOnePinTwo(void) {
    /* sps_cfg.c:88 */
    TEST_ASSERT_EQUAL(PEX_PORT_EXPANDER1, sps_kChannelFeedbackMapping[2u].pexDevice);
    /* sps_cfg.c:88 */
    TEST_ASSERT_EQUAL(PEX_PORT_0_PIN_2, sps_kChannelFeedbackMapping[2u].pexChannel);
}

/** @brief   channel 3 feedback is on port expander 1 pin 3
 * @details sps_cfg.c:89 places PEX_PORT_EXPANDER1 and PEX_PORT_0_PIN_3.
 */
void testSpsChannelThreeFeedbackIsExpanderOnePinThree(void) {
    /* sps_cfg.c:89 */
    TEST_ASSERT_EQUAL(PEX_PORT_EXPANDER1, sps_kChannelFeedbackMapping[3u].pexDevice);
    /* sps_cfg.c:89 */
    TEST_ASSERT_EQUAL(PEX_PORT_0_PIN_3, sps_kChannelFeedbackMapping[3u].pexChannel);
}

/** @brief   channel 4 feedback is on port expander 1 pin 4
 * @details sps_cfg.c:90 places PEX_PORT_EXPANDER1 and PEX_PORT_0_PIN_4.
 */
void testSpsChannelFourFeedbackIsExpanderOnePinFour(void) {
    /* sps_cfg.c:90 */
    TEST_ASSERT_EQUAL(PEX_PORT_EXPANDER1, sps_kChannelFeedbackMapping[4u].pexDevice);
    /* sps_cfg.c:90 */
    TEST_ASSERT_EQUAL(PEX_PORT_0_PIN_4, sps_kChannelFeedbackMapping[4u].pexChannel);
}

/** @brief   channel 5 feedback is on port expander 1 pin 5
 * @details sps_cfg.c:91 places PEX_PORT_EXPANDER1 and PEX_PORT_0_PIN_5.
 */
void testSpsChannelFiveFeedbackIsExpanderOnePinFive(void) {
    /* sps_cfg.c:91 */
    TEST_ASSERT_EQUAL(PEX_PORT_EXPANDER1, sps_kChannelFeedbackMapping[5u].pexDevice);
    /* sps_cfg.c:91 */
    TEST_ASSERT_EQUAL(PEX_PORT_0_PIN_5, sps_kChannelFeedbackMapping[5u].pexChannel);
}

/** @brief   channel 6 feedback is on port expander 1 pin 6
 * @details sps_cfg.c:92 places PEX_PORT_EXPANDER1 and PEX_PORT_0_PIN_6.
 */
void testSpsChannelSixFeedbackIsExpanderOnePinSix(void) {
    /* sps_cfg.c:92 */
    TEST_ASSERT_EQUAL(PEX_PORT_EXPANDER1, sps_kChannelFeedbackMapping[6u].pexDevice);
    /* sps_cfg.c:92 */
    TEST_ASSERT_EQUAL(PEX_PORT_0_PIN_6, sps_kChannelFeedbackMapping[6u].pexChannel);
}

/** @brief   channel 7 feedback is on port expander 1 pin 7
 * @details sps_cfg.c:93 places PEX_PORT_EXPANDER1 and PEX_PORT_0_PIN_7.
 */
void testSpsChannelSevenFeedbackIsExpanderOnePinSeven(void) {
    /* sps_cfg.c:93 */
    TEST_ASSERT_EQUAL(PEX_PORT_EXPANDER1, sps_kChannelFeedbackMapping[7u].pexDevice);
    /* sps_cfg.c:93 */
    TEST_ASSERT_EQUAL(PEX_PORT_0_PIN_7, sps_kChannelFeedbackMapping[7u].pexChannel);
}

/** @brief   the feedback pins are distinct
 * @details Two channels sharing a feedback pin would make the feedback
 *          ambiguous. The pairs compared come from sps_cfg.c:86-93.
 */
void testSpsFeedbackPinsAreDistinct(void) {
    uint32_t u;
    uint32_t v;
    for (u = 0u; u < SPS_NR_OF_AVAILABLE_SPS_CHANNELS; u++) {
        for (v = u + 1u; v < SPS_NR_OF_AVAILABLE_SPS_CHANNELS; v++) {
            TEST_ASSERT_NOT_EQUAL(sps_kChannelFeedbackMapping[u].pexChannel,
                                      sps_kChannelFeedbackMapping[v].pexChannel);
        }
    }
}
