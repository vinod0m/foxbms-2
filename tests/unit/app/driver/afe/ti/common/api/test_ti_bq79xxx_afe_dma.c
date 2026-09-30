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
 * @file    test_ti_bq79xxx_afe_dma.c
 * @author  foxBMS Team
 * @date    2023-09-11 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Test of TI BQ97XXX AFE DMA API implementation of the TI AFE DMA API
 * @details TODO
 *
 */

/*========== Includes =======================================================*/
#include "unity.h"
#include "Mockdma.h"
#include "Mockio.h"
#include "Mockmcu.h"
#include "Mockos.h"
#include "Mockspi.h"

#include "afe_dma.h"
#include "test_assert_helper.h"

/*========== Unit Testing Framework Directives ==============================*/
TEST_SOURCE_FILE("ti_bq79xxx_afe_dma.c")

TEST_INCLUDE_PATH("../../src/app/driver/afe/api")
TEST_INCLUDE_PATH("../../src/app/driver/config")
TEST_INCLUDE_PATH("../../src/app/driver/dma")
TEST_INCLUDE_PATH("../../src/app/driver/io")
TEST_INCLUDE_PATH("../../src/app/driver/mcu")
TEST_INCLUDE_PATH("../../src/app/driver/rtc")
TEST_INCLUDE_PATH("../../src/app/driver/spi")
TEST_INCLUDE_PATH("../../src/app/task/config")
TEST_INCLUDE_PATH("../../src/app/task/ftask")
TEST_INCLUDE_PATH("../../src/app/task/os")

/*========== Definitions and Implementations for Unit Test ==================*/

OS_TASK_HANDLE ftsk_taskHandleAfe;

#define TEST_SPI_INTERFACE_1 (0u)
#define TEST_SPI_INTERFACE_2 (1u)
#define TEST_SPI_INTERFACE_3 (2u)
#define TEST_SPI_INTERFACE_4 (3u)
#define TEST_SPI_INTERFACE_5 (4u)

/* clang-format off */
/* The five peripheral shadows below are all-zero register images.
 *
 * They were previously written out as ~105 positional elements in a nested
 * `{ ... }` shape. That shape does not describe the register block this build
 * compiles against: sil/iface/HL_spi.h:114-137 declares spiREG_t as TWENTY-THREE
 * flat uint32_t members (GCR0..ADDR) with no nested structure, so a positional
 * list of that length is 82 elements of excess initialiser, which is what
 * -Wexcess-initializers was reporting at five sites.
 *
 * Every element of the old form was 0u, so `{0}` is the same value: it
 * zero-initialises all members, is independent of how many members the struct
 * has, and cannot drift from the declaration the way a hand-counted list does.
 * A designated initialiser is also what tools/run.sh's own notes call for, for
 * the same reason.
 */
spiBASE_t spiReg1 = {0};
spiBASE_t spiReg2 = {0};
spiBASE_t spiReg3 = {0};
spiBASE_t spiReg4 = {0};
spiBASE_t spiReg5 = {0};
/* clang-format on */

spiBASE_t *dma_spiInterfaces[DMA_NUMBER_SPI_INTERFACES] = {
    NULL_PTR, /* SPI1 */
    NULL_PTR, /* SPI2 */
    NULL_PTR, /* SPI3 */
    NULL_PTR, /* SPI4 */
    NULL_PTR, /* SPI5 */
};

/*========== Setup and Teardown =============================================*/
void setUp(void) {
    dma_spiInterfaces[TEST_SPI_INTERFACE_1] = &spiReg1;
    dma_spiInterfaces[TEST_SPI_INTERFACE_2] = &spiReg2;
    dma_spiInterfaces[TEST_SPI_INTERFACE_3] = &spiReg3;
    dma_spiInterfaces[TEST_SPI_INTERFACE_4] = &spiReg4;
    dma_spiInterfaces[TEST_SPI_INTERFACE_5] = &spiReg5;
}

void tearDown(void) {
}

/*========== Test Cases =====================================================*/

/**
 * @brief   TI_SPI_INDEX is SPI_SPI1_INDEX, which is 0.
 * @details ti_bq79xxx_afe_dma.c:65 defines TI_SPI_INDEX as
 *          `(SPI_SPI1_INDEX)`, and src/app/driver/config/spi_cfg.h:73 defines
 *          SPI_SPI1_INDEX as `(0u)`. The whole body of AFE_DmaCallback compares
 *          against that macro, so its numeric value is the fact every case
 *          below turns on; it is asserted here as a literal.
 */
/* cspell:disable-next-line */
void testTiAfeDmaCallbackExpectsSpiInterfaceOne(void) {
    TEST_ASSERT_EQUAL_UINT8(0u, (uint8_t)SPI_SPI1_INDEX);
}

/**
 * @brief   The one index the callback accepts is accepted silently.
 * @details ti_bq79xxx_afe_dma.c:78-80:
 *              void AFE_DmaCallback(uint8_t spiIndex) {
 *                  FAS_ASSERT(spiIndex == TI_SPI_INDEX);
 *              }
 *          Under UNITY_UNIT_TEST, FAS_ASSERT is `if (!(x)) Throw(0)`
 *          (src/app/main/include/fassert.h:248-252), so a satisfied assertion
 *          returns normally. TEST_ASSERT_PASS_ASSERT from
 *          tests/unit/support/test_assert_helper.h:92-101 is the house helper
 *          for exactly this: it fails the case if a CException escapes.
 *
 *          There is no other behaviour to check - the function body is one
 *          assertion and nothing else - so "returns without throwing" is the
 *          complete claim, and it is falsifiable: see the perturbation evidence
 *          for the case where the comparison is inverted.
 */
/* cspell:disable-next-line */
void testTiAfeDmaCallbackAcceptsSpiInterfaceOne(void) {
    TEST_ASSERT_PASS_ASSERT(AFE_DmaCallback(TEST_SPI_INTERFACE_1));
}

/**
 * @brief   Every other interface index is rejected by the assertion.
 * @details Same source. With TI_SPI_INDEX == 0, the indices this driver does
 *          NOT own - SPI2 through SPI5, declared in this file as
 *          TEST_SPI_INTERFACE_2..5 - must each raise a CException.
 *          TEST_ASSERT_FAIL_ASSERT (test_assert_helper.h:74-82) requires the
 *          throw, so a callback that silently accepted a foreign interface
 *          would fail the case rather than pass it quietly.
 *          Each index is asserted separately, so one accepted interface cannot
 *          be masked by the others.
 */
/* cspell:disable-next-line */
void testTiAfeDmaCallbackRejectsEveryOtherSpiInterface(void) {
    TEST_ASSERT_FAIL_ASSERT(AFE_DmaCallback(TEST_SPI_INTERFACE_2));
    TEST_ASSERT_FAIL_ASSERT(AFE_DmaCallback(TEST_SPI_INTERFACE_3));
    TEST_ASSERT_FAIL_ASSERT(AFE_DmaCallback(TEST_SPI_INTERFACE_4));
    TEST_ASSERT_FAIL_ASSERT(AFE_DmaCallback(TEST_SPI_INTERFACE_5));
}

/**
 * @brief   The rejection carries exception id 0, which is what FAS_ASSERT throws.
 * @details src/app/main/include/fassert.h:250-252 expands the failed assertion to `Throw(0)`, so the
 *          caught exception id is 0. Asserting the id rather than merely
 *          "something was thrown" pins the failure to this assertion: an
 *          unrelated CException raised deeper inside would carry a different id
 *          and fail here.
 *          Catch is spelled out rather than using the helper because the helper
 *          discards the id (test_assert_helper.h:80-81 has an empty Catch).
 */
/* cspell:disable-next-line */
void testTiAfeDmaCallbackRejectionThrowsExceptionIdZero(void) {
    CEXCEPTION_T e      = 0x7FFFFFFF;
    bool didThrow       = false;

    Try {
        AFE_DmaCallback(TEST_SPI_INTERFACE_2);
    }
    Catch(e) {
        didThrow = true;
    }
    const CEXCEPTION_T caught = e;

    TEST_ASSERT_TRUE_MESSAGE(didThrow, "AFE_DmaCallback must reject a foreign interface");
    TEST_ASSERT_EQUAL_INT(0, (int)caught);
}

/**
 * @brief   The accepted index produces no exception at all.
 * @details The complement of the case above, asserted explicitly rather than
 *          left to TEST_ASSERT_PASS_ASSERT: if no throw happened then `caught`
 *          must still hold the sentinel it was initialised with, so a silent
 *          path cannot be confused with a throw of id 0.
 */
/* cspell:disable-next-line */
void testTiAfeDmaCallbackAcceptanceThrowsNothing(void) {
    CEXCEPTION_T e      = 0x7FFFFFFF;
    bool didThrow       = false;

    Try {
        AFE_DmaCallback(TEST_SPI_INTERFACE_1);
    }
    Catch(e) {
        didThrow = true;
    }
    const CEXCEPTION_T caught = e;

    TEST_ASSERT_FALSE_MESSAGE(didThrow, "AFE_DmaCallback must accept its own interface");
    TEST_ASSERT_EQUAL_INT(0x7FFFFFFF, (int)caught);
}

/**
 * @brief   The boundary is exactly one index wide, not "index 0 and nothing else".
 * @details Sweeps the whole uint8_t range the parameter admits: 0 is accepted,
 *          every one of the other 255 values is rejected. This is the property
 *          the four cases above sample, expressed without sampling, so an
 *          off-by-one in the comparison (>= instead of ==, or a cast to a
 *          narrower type) cannot hide between the sampled values.
 *          TEST_SPI_INTERFACE_1 is the accepted one because SPI_SPI1_INDEX is 0.
 */
/* cspell:disable-next-line */
void testTiAfeDmaCallbackAcceptsExactlyOneOfAll256Indices(void) {
    uint32_t index;
    uint32_t accepted = 0u;

    for (index = 0u; index < 256u; index++) {
        CEXCEPTION_T e      = 0x7FFFFFFF;
        bool didThrow       = false;
        Try {
            AFE_DmaCallback((uint8_t)index);
        }
        Catch(e) {
            didThrow = true;
        }
        if (!didThrow) {
            accepted++;
            /* the only accepted index must be the configured one */
            TEST_ASSERT_EQUAL_UINT32(0u, index);
        }
    }

    TEST_ASSERT_EQUAL_UINT32(1u, accepted);
}
