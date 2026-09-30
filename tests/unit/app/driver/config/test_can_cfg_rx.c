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
 * @file    test_can_cfg_rx.c
 * @author  foxBMS Team
 * @date    2020-07-28 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Tests for the CAN driver
 * @details TODO
 *
 */

/*========== Includes =======================================================*/
#include "unity.h"
#include "Mockcan.h"
/* can_cbs_rx.h is included for real rather than mocked.
 *
 * can_cfg_rx.c builds a REGISTRY (can_cfg_rx.c:74-106): each entry holds the
 * ADDRESS of a CANRX_* callback, e.g. :76 `&CANRX_BmsStateRequest`. The module
 * never calls them, so the link only needs the symbols to exist.
 *
 * Mocking the header does not work here. The type
 * CAN_CAN2AFE_CELL_TEMPERATURES_QUEUE_s lives inside
 *   src/app/driver/config/can_cfg.h:195
 *     #if (defined(FOXBMS_AFE_DRIVER_DEBUG_CAN) && (FOXBMS_AFE_DRIVER_DEBUG_CAN == 1))
 * and can_cbs_rx.h:314 guards the matching TEST_CANRX_* declarations with the
 * same macro - but CMock still emits the DEBUG_CAN functions into
 * Mockcan_cbs_rx.c, which is then compiled WITHOUT the macro (it is granted
 * only to test_can_cbs_rx_afe_cell-temperatures.c, cell-voltages.c and
 * test_debug_can.c). The result is 15 diagnostics of the form
 * "unknown type name 'CAN_CAN2AFE_CELL_TEMPERATURES_QUEUE_s'".
 * This is not specific to this file: test_bender_iso165c.c, which mocks the
 * same header without that macro, fails the same way.
 *
 * Including the real header and defining the two symbols this configuration
 * references is both smaller and correct. */
#include "can_cbs_rx.h"
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
TEST_SOURCE_FILE("can_cfg_rx.c")

TEST_INCLUDE_PATH("../../src/app/driver/can")
TEST_INCLUDE_PATH("../../src/app/driver/can/cbs/rx")
TEST_INCLUDE_PATH("../../src/app/driver/config")
TEST_INCLUDE_PATH("../../src/app/driver/foxmath")
TEST_INCLUDE_PATH("../../src/app/driver/imd")
TEST_INCLUDE_PATH("../../src/app/driver/rtc")
TEST_INCLUDE_PATH("../../src/app/engine/diag")
TEST_INCLUDE_PATH("../../src/app/task/config")
TEST_INCLUDE_PATH("../../src/app/task/ftask")

/*========== Definitions and Implementations for Unit Test ==================*/

OS_QUEUE ftsk_dataQueue             = NULL_PTR;
OS_QUEUE ftsk_imdCanDataQueue       = NULL_PTR;
OS_QUEUE ftsk_canRxQueue            = NULL_PTR;
volatile bool ftsk_allQueuesCreated = false;

/* The two callbacks the registry references in THIS configuration. Neither is
 * ever called - can_cfg_rx.c only stores their addresses - so an empty body is
 * the whole definition. They are the two unconditional entries at
 * can_cfg_rx.c:76-77; every other entry in that table is behind a per-test
 * macro this test does not grant, so it contributes nothing here and needs no
 * symbol. Signatures copied from can_cbs_rx.h:77-79 and :88-90. */
uint32_t CANRX_Debug(
    CAN_MESSAGE_PROPERTIES_s message,
    const uint8_t *const kpkCanData,
    const CAN_SHIM_s *const kpkCanShim) {
    (void)message;
    (void)kpkCanData;
    (void)kpkCanShim;
    return 0u;
}

uint32_t CANRX_BmsStateRequest(
    CAN_MESSAGE_PROPERTIES_s message,
    const uint8_t *const kpkCanData,
    const CAN_SHIM_s *const kpkCanShim) {
    (void)message;
    (void)kpkCanData;
    (void)kpkCanShim;
    return 0u;
}

/*========== Setup and Teardown =============================================*/
void setUp(void) {
}

void tearDown(void) {
}

/*========== Test Cases =====================================================*/

/**
 * @brief   The registry holds exactly the two unconditional messages.
 * @details can_cfg_rx.c:74-106 is one table whose entries are individually
 *          guarded by the per-test macros. This test grants none of them, so
 *          only the two unconditional entries at :76 and :77 are compiled:
 *            :76  {CAN_NODE_1, CANRX_BMS_STATE_REQUEST_MESSAGE, &CANRX_BmsStateRequest}
 *            :77  {CAN_NODE_DEBUG_MESSAGE, CANRX_DEBUG_MESSAGE, &CANRX_Debug}
 *          Every other entry sits behind FOXBMS_IMD_BENDER_ISO165C (:79),
 *          FOXBMS_CS_ISABELLENHUETTE_IVT_S (:83),
 *          FOXBMS_AS_HONEYWELL_BAS6C_X00 (:92),
 *          FOXBMS_AFE_DRIVER_DEBUG_CAN (:95) or FOXBMS_CS_LEM_CAB500 (:99),
 *          none of which conf/unit/app_project_posix.yml grants to this test.
 *
 *          can_rxMessages is declared `extern const CAN_RX_MESSAGE_TYPE_s
 *          can_rxMessages[];` - an incomplete array type - so its extent cannot
 *          be taken with sizeof() here. The count the source itself publishes is
 *          can_rxMessagesLength, computed at can_cfg_rx.c:106 as
 *          sizeof(can_rxMessages)/sizeof(can_rxMessages[0]).
 */
/* cspell:disable-next-line */
void testCanRxRegistryHoldsOnlyTheUnconditionalMessages(void) {
    TEST_ASSERT_EQUAL_UINT8(2u, can_rxMessagesLength);
}

/**
 * @brief   The BMS state request entry: node, identifier, framing and callback.
 * @details can_cfg_rx.c:76. The identifier is CANRX_BMS_STATE_REQUEST_ID
 *          (0x210u) at can_cfg_rx-message-definitions.h:74; the id type is
 *          CAN_STANDARD_IDENTIFIER_11_BIT, the FIRST enumerator of the enum at
 *          src/app/driver/config/can_cfg.h:181-184 and therefore 0; the DLC is CAN_DEFAULT_DLC (8u)
 *          at src/app/driver/config/can_cfg.h:110; the endianness is CAN_BIG_ENDIAN, the SECOND
 *          enumerator of the enum at src/app/driver/config/can_cfg.h:175-178 and therefore 1.
 *          The node is CAN_NODE_1, which is ((CAN_NODE_s *)&can_node1) at
 *          src/app/driver/config/can_cfg.h:79.
 *          All asserted as literals so a wrong macro cannot pass.
 */
/* cspell:disable-next-line */
void testCanRxRegistryBmsStateRequestEntry(void) {
    TEST_ASSERT_EQUAL_PTR((CAN_NODE_s *)&can_node1, can_rxMessages[0].canNode);
    TEST_ASSERT_EQUAL_HEX32(0x210u, can_rxMessages[0].message.id);
    TEST_ASSERT_EQUAL_INT32(0, (int32_t)can_rxMessages[0].message.idType);
    TEST_ASSERT_EQUAL_UINT8(8u, can_rxMessages[0].message.dlc);
    TEST_ASSERT_EQUAL_INT32(1, (int32_t)can_rxMessages[0].message.endianness);
    /* the callback is the function itself, not a copy of it */
    TEST_ASSERT_EQUAL_PTR(
        (CAN_RxCallbackFunction_f)CANRX_BmsStateRequest, can_rxMessages[0].callbackFunction);
}

/**
 * @brief   The debug message entry: node, identifier, framing and callback.
 * @details can_cfg_rx.c:77. CANRX_DEBUG_ID is (0x300u) at
 *          can_cfg_rx-message-definitions.h:87, with the same id type, DLC and
 *          endianness as the entry above - the same four macros, so the values
 *          are asserted per entry rather than once. The node is
 *          CAN_NODE_DEBUG_MESSAGE, which src/app/driver/config/can_cfg.h:82 defines as (CAN_NODE_1),
 *          i.e. the SAME peripheral as entry 0; asserting the pointer identity
 *          here pins that alias down instead of leaving it implied.
 */
/* cspell:disable-next-line */
void testCanRxRegistryDebugMessageEntry(void) {
    TEST_ASSERT_EQUAL_PTR((CAN_NODE_s *)&can_node1, can_rxMessages[1].canNode);
    TEST_ASSERT_EQUAL_HEX32(0x300u, can_rxMessages[1].message.id);
    TEST_ASSERT_EQUAL_INT32(0, (int32_t)can_rxMessages[1].message.idType);
    TEST_ASSERT_EQUAL_UINT8(8u, can_rxMessages[1].message.dlc);
    TEST_ASSERT_EQUAL_INT32(1, (int32_t)can_rxMessages[1].message.endianness);
    TEST_ASSERT_EQUAL_PTR(
        (CAN_RxCallbackFunction_f)CANRX_Debug, can_rxMessages[1].callbackFunction);
}

/**
 * @brief   The two registry entries are distinguishable by identifier.
 * @details Cross-checks the two rows rather than restating either. Two entries
 *          with the same CAN id would make the registry ambiguous, so the
 *          identifiers must differ; and because both entries are standard
 *          11-bit identifiers, both must fit in 11 bits, which bounds them.
 *          A registry that grew a duplicate row with a clashing id is what this
 *          catches.
 */
/* cspell:disable-next-line */
void testCanRxRegistryIdentifiersAreUniqueAndElevenBit(void) {
    uint32_t first  = (uint32_t)can_rxMessages[0].message.id;
    uint32_t second = (uint32_t)can_rxMessages[1].message.id;

    TEST_ASSERT_NOT_EQUAL_MESSAGE(first, second, "CAN rx identifiers must be unique");
    /* CAN_STANDARD_IDENTIFIER_11_BIT is set on both, so 0x800 is out of range */
    TEST_ASSERT_LESS_THAN_UINT32(0x800u, first);
    TEST_ASSERT_LESS_THAN_UINT32(0x800u, second);
}

/**
 * @brief   Every entry in the registry declares the same framing.
 * @details Asserts the property over the whole published extent rather than
 *          naming rows, so it keeps holding if a macro is granted later and the
 *          table grows. The values are the ones derived for entry 0 above and
 *          re-asserted per row: 11-bit standard id, DLC 8, big endian.
 *          Looping to can_rxMessagesLength - not a literal 2 - is what makes the
 *          case survive the table growing.
 */
/* cspell:disable-next-line */
void testCanRxRegistryEveryEntryUsesTheSameFraming(void) {
    uint32_t index;
    for (index = 0u; index < (uint32_t)can_rxMessagesLength; index++) {
        TEST_ASSERT_EQUAL_INT32_MESSAGE(0, (int32_t)can_rxMessages[index].message.idType, "idType must be standard 11-bit");
        TEST_ASSERT_EQUAL_UINT8_MESSAGE(8u, can_rxMessages[index].message.dlc, "dlc must be CAN_DEFAULT_DLC");
        TEST_ASSERT_EQUAL_INT32_MESSAGE(1, (int32_t)can_rxMessages[index].message.endianness, "endianness must be big");
        /* every entry must name a callback, not a null pointer */
        TEST_ASSERT_NOT_NULL_MESSAGE(can_rxMessages[index].callbackFunction, "every registry entry needs a callback");
        /* and every entry must name the one configured node */
        TEST_ASSERT_EQUAL_PTR_MESSAGE((CAN_NODE_s *)&can_node1, can_rxMessages[index].canNode, "all rx messages arrive on node 1");
    }
}
