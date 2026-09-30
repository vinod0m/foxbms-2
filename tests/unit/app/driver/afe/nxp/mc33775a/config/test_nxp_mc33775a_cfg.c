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
 * @file    test_nxp_mc33775a_cfg.c
 * @author  foxBMS Team
 * @date    2020-06-10 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Test of nxp_mc33775a_cfg.c
 * @details Tests the exported multiplexer measurement sequence of
 *          nxp_mc33775a_cfg.c
 *
 */

/*========== Includes =======================================================*/
#include "unity.h"

#include "nxp_mc3377x_cfg.h"

/*========== Unit Testing Framework Directives ==============================*/
TEST_SOURCE_FILE("nxp_mc33775a_cfg.c")

TEST_INCLUDE_PATH("../../src/app/driver/afe/api")
TEST_INCLUDE_PATH("../../src/app/driver/afe/nxp/common/mc3377x")
TEST_INCLUDE_PATH("../../src/app/driver/afe/nxp/mc33775a")
TEST_INCLUDE_PATH("../../src/app/driver/afe/nxp/mc33775a/config")
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
 * @brief   N77X_MUX_SEQUENCE_LENGTH is 18, i.e. this build selects the two-
 *          multiplexer branch of the guard.
 * @details nxp_mc33775a_defs.h:110-114 chooses the length:
 *            :110  #if BS_NR_OF_TEMP_SENSORS_PER_MODULE <= N77X_MUX_GPIOS_PER_MUX
 *            :111      #define N77X_MUX_SEQUENCE_LENGTH (8u)
 *            :112  #else
 *            :113      #define N77X_MUX_SEQUENCE_LENGTH (18u)
 *          :108 N77X_MUX_GPIOS_PER_MUX (8u)
 *
 *          WHICH arm is taken is the whole point of this case, and the
 *          left-hand operand is NOT battery_system_cfg.h:146. This test is
 *          compiled with -I on tests/unit/app/application/config, so
 *          battery_system_cfg_unit_test.h is in the include closure, and it
 *          redefines the operand:
 *            battery_system_cfg_unit_test.h:170  #if defined(TEST_BS_NR_OF_TEMP_SENSORS_PER_MODULE)
 *            battery_system_cfg_unit_test.h:171      #define BS_NR_OF_TEMP_SENSORS_PER_MODULE (TEST_BS_NR_OF_TEMP_SENSORS_PER_MODULE)
 *          The harness passes -DTEST_BS_NR_OF_TEMP_SENSORS_PER_MODULE=16u for
 *          this test, so the operand is 16 and 16 > 8 selects :113.
 *          The dependency file generated for this translation unit lists
 *          battery_system_cfg_unit_test.h, which is what makes :171 the line
 *          the build reads.
 *
 *          The 16 is asserted as a literal, and the length as a literal, so
 *          neither can be satisfied by a wrong macro.
 */
/* cspell:disable-next-line */
void testMuxSequenceLengthIsEighteenForThisBuild(void) {
    /* BS_NR_OF_TEMP_SENSORS_PER_MODULE -> 16u via
     * battery_system_cfg_unit_test.h:171 (TEST_BS_NR_OF_TEMP_SENSORS_PER_MODULE=16u),
     * NOT via battery_system_cfg.h:146 (8u), which this build does not read. */
    TEST_ASSERT_EQUAL_UINT8(16u, (uint8_t)BS_NR_OF_TEMP_SENSORS_PER_MODULE);
    /* N77X_MUX_GPIOS_PER_MUX nxp_mc33775a_defs.h:108 */
    TEST_ASSERT_EQUAL_UINT8(8u, (uint8_t)N77X_MUX_GPIOS_PER_MUX);
    /* the selected branch, nxp_mc33775a_defs.h:113 */
    TEST_ASSERT_EQUAL_UINT8(18u, (uint8_t)N77X_MUX_SEQUENCE_LENGTH);
}

/**
 * @brief   N77X_MUX_DISABLE_VALUE is the sentinel written into the sequence to
 *          turn a multiplexer off between passes.
 * @details nxp_mc33775a_defs.h:116 `#define N77X_MUX_DISABLE_VALUE (0xFFu)`.
 *          0xFF is outside the 0..7 channel range that N77X_MUX_GPIOS_PER_MUX
 *          allows, which is what distinguishes a disabled entry from a channel
 *          that happens to be measured.
 */
/* cspell:disable-next-line */
void testMuxDisableValueIsTheSentinelOutsideTheChannelRange(void) {
    TEST_ASSERT_EQUAL_UINT8(0xFFu, (uint8_t)N77X_MUX_DISABLE_VALUE);
    /* the sentinel must not be usable as a real channel */
    TEST_ASSERT_GREATER_THAN_UINT8((uint8_t)N77X_MUX_GPIOS_PER_MUX, (uint8_t)N77X_MUX_DISABLE_VALUE);
}

/**
 * @brief   Multiplexer 0 is measured on all eight of its channels.
 * @details nxp_mc33775a_cfg.c:72-103 gives muxId 0 with muxChannel 0..7 in
 *          order. One assertion per channel so that a single transposed or
 *          dropped entry is caught rather than a whole-block comparison.
 */
/* cspell:disable-next-line */
void testMuxSequenceFirstBlockIsMuxZeroAllEightChannels(void) {
    uint32_t channel;
    /* every entry of the first block names multiplexer 0 */
    for (channel = 0u; channel < 8u; channel++) {
        TEST_ASSERT_EQUAL_UINT8(0u, n77x_muxSequence[channel].muxId);
        TEST_ASSERT_EQUAL_UINT8((uint8_t)channel, n77x_muxSequence[channel].muxChannel);
    }
}

/**
 * @brief   Multiplexer 0 is then disabled, before multiplexer 1 is addressed.
 * @details nxp_mc33775a_cfg.c:105-109
 *            :108  .muxChannel = N77X_MUX_DISABLE_VALUE, with the source comment
 *                  "disable enabled mux"
 *          The entry keeps muxId 0 and writes only the channel sentinel, so the
 *          disable is asserted through the same field the source writes.
 */
/* cspell:disable-next-line */
void testMuxSequenceDisablesMuxZeroBeforeStartingMuxOne(void) {
    TEST_ASSERT_EQUAL_UINT8(0u, n77x_muxSequence[8].muxId);
    TEST_ASSERT_EQUAL_UINT8(0xFFu, n77x_muxSequence[8].muxChannel);
}

/**
 * @brief   Multiplexer 1 is measured on all eight of its channels.
 * @details nxp_mc33775a_cfg.c:110-135 gives muxId 1 with muxChannel 0..7.
 */
/* cspell:disable-next-line */
void testMuxSequenceSecondBlockIsMuxOneAllEightChannels(void) {
    uint32_t channel;
    for (channel = 0u; channel < 8u; channel++) {
        TEST_ASSERT_EQUAL_UINT8(1u, n77x_muxSequence[9u + channel].muxId);
        TEST_ASSERT_EQUAL_UINT8((uint8_t)channel, n77x_muxSequence[9u + channel].muxChannel);
    }
}

/**
 * @brief   Multiplexer 1 is then disabled, which is the last entry.
 * @details nxp_mc33775a_cfg.c:137-145, with :144 writing the sentinel. The
 *          table ends here: index 17 is the final one, because
 *          N77X_MUX_SEQUENCE_LENGTH is 18.
 */
/* cspell:disable-next-line */
void testMuxSequenceEndsByDisablingMuxOne(void) {
    TEST_ASSERT_EQUAL_UINT8(1u, n77x_muxSequence[17].muxId);
    TEST_ASSERT_EQUAL_UINT8(0xFFu, n77x_muxSequence[17].muxChannel);
}

/**
 * @brief   The third multiplexer block is commented out, so the compiled
 *          sequence holds two multiplexers and not three.
 * @details nxp_mc33775a_cfg.c:147-179 is a block comment wrapping what would
 *          otherwise be muxId 2, muxChannel 0..7. Nothing in it is compiled, so
 *          no entry anywhere in the table may name multiplexer 2. This is the
 *          only assertion that would notice if someone uncommented that block
 *          without extending N77X_MUX_SEQUENCE_LENGTH.
 */
/* cspell:disable-next-line */
void testMuxSequenceHasNoThirdMultiplexerBlock(void) {
    uint32_t index;
    uint32_t seenMuxOne = 0u;
    uint32_t seenDisable = 0u;
    for (index = 0u; index < 18u; index++) {
        if (2u == n77x_muxSequence[index].muxId) {
            TEST_FAIL_MESSAGE("muxId 2 must not appear: that block is commented out at nxp_mc33775a_cfg.c:147-179");
        }
        /* and no more than two disable sentinels, one after each block */
        if ((uint8_t)N77X_MUX_DISABLE_VALUE == n77x_muxSequence[index].muxChannel) {
            seenDisable++;
        }
        if (1u == n77x_muxSequence[index].muxId) {
            seenMuxOne++;
        }
    }
    /* exactly one disable per multiplexer: after mux 0 and after mux 1 */
    TEST_ASSERT_EQUAL_UINT32(2u, seenDisable);
    /* mux 1 contributes its disable entry on top of its eight channels */
    TEST_ASSERT_EQUAL_UINT32(9u, seenMuxOne);
}

/**
 * @brief   A measured channel is never the disable sentinel.
 * @details Cross-checks the two kinds of entry the table mixes, rather than
 *          restating either. Every non-sentinel muxChannel must lie inside the
 *          0..7 range that N77X_MUX_GPIOS_PER_MUX allows, so no channel value
 *          outside that range can be a real measurement.
 */
/* cspell:disable-next-line */
void testMuxSequenceChannelsAreEitherRealOrTheDisableSentinel(void) {
    uint32_t index;
    uint32_t sentinelCount = 0u;
    uint32_t measuredCount = 0u;
    for (index = 0u; index < 18u; index++) {
        uint8_t channel = n77x_muxSequence[index].muxChannel;
        if ((uint8_t)N77X_MUX_DISABLE_VALUE == channel) {
            sentinelCount++;
        } else {
            TEST_ASSERT_LESS_OR_EQUAL_UINT8((uint8_t)N77X_MUX_GPIOS_PER_MUX, channel);
            measuredCount++;
        }
    }
    /* 8 channels on each of two multiplexers, plus the two disable entries */
    TEST_ASSERT_EQUAL_UINT32(16u, measuredCount);
    TEST_ASSERT_EQUAL_UINT32(2u, sentinelCount);
}
