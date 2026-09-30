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
 * @file    test_can_cfg.c
 * @author  foxBMS Team
 * @date    2020-07-28 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Tests of the CAN configuration
 * @details Asserts the CAN node and database-shim configuration can_cfg.c
 *          publishes. can_cfg.c defines no functions; its entire exported
 *          behaviour is
 *
 *            * `can_node1` and `can_node2Isolated`, the two CAN_NODE_s objects
 *              that name the peripheral each node sits on, and
 *            * `can_kShim`, the composite of local database-table handles every
 *              CAN Tx and Rx callback is handed.
 *
 *          The shim is the load-bearing part. Each of its 26 table pointers is
 *          paired with a local data block whose `header.uniqueId` tells the
 *          database which entry that block stands for. A shim field pointing at
 *          the wrong block makes a CAN callback read and write another signal,
 *          so the mapping is worth asserting even though the module contains no
 *          code.
 *
 *          WHERE THE EXPECTED VALUES COME FROM
 *          -------------------------------------
 *          Every expected value below is a macro can_cfg.c itself writes.
 *          can_cfg.c:70 and :74 name the two peripherals; can_cfg.c:79-105 give
 *          each local data block its uniqueId; can_cfg.c:110-135 wire those
 *          blocks into the shim. Each assertion cites the file:line that both
 *          names and assigns the value.
 *
 *            can_node1.canNodeRegister          = canREG1  (can_cfg.c:70)
 *            can_node2Isolated.canNodeRegister  = canREG2  (can_cfg.c:74)
 *            can_kShim.pQueueImd                = &ftsk_imdCanDataQueue (can_cfg.c:109)
 *
 *          and, per shim field, the uniqueId that can_cfg.c places in the block
 *          the field points at:
 *
 *            pTableCellTemperature          DATA_BLOCK_ID_CELL_TEMPERATURE          (:110 / :79)
 *            pTableCellVoltage              DATA_BLOCK_ID_CELL_VOLTAGE              (:111 / :80)
 *            pTableCurrent                  DATA_BLOCK_ID_CURRENT                  (:112 / :81)
 *            pTableCurrentSensorTemperature DATA_BLOCK_ID_CURRENT_SENSOR_TEMPERATURE (:113 / :83)
 *            pTablePower                    DATA_BLOCK_ID_POWER                    (:114 / :84)
 *            pTableCurrentCounter           DATA_BLOCK_ID_CURRENT_COUNTER           (:115 / :85)
 *            pTableEnergyCounter            DATA_BLOCK_ID_ENERGY_COUNTER            (:116 / :86)
 *            pTableSystemVoltage1           DATA_BLOCK_ID_SYSTEM_VOLTAGE_1           (:117 / :87)
 *            pTableSystemVoltage2           DATA_BLOCK_ID_SYSTEM_VOLTAGE_2           (:118 / :88)
 *            pTableSystemVoltage3           DATA_BLOCK_ID_SYSTEM_VOLTAGE_3           (:119 / :89)
 *            pTableErrorState               DATA_BLOCK_ID_ERROR_STATE               (:120 / :90)
 *            pTableInsulation               DATA_BLOCK_ID_INSULATION               (:121 / :91)
 *            pTableMinMax                   DATA_BLOCK_ID_MIN_MAX                   (:122 / :92)
 *            pTableMol                      DATA_BLOCK_ID_MOL_FLAG                  (:123 / :93)
 *            pTableMsl                      DATA_BLOCK_ID_MSL_FLAG                  (:124 / :94)
 *            pTableOpenWire                 DATA_BLOCK_ID_OPEN_WIRE_BASE            (:125 / :95)
 *            pTablePackValues               DATA_BLOCK_ID_PACK_VALUES               (:126 / :96)
 *            pTableRsl                      DATA_BLOCK_ID_RSL_FLAG                  (:127 / :97)
 *            pTableSoc                      DATA_BLOCK_ID_SOC                      (:128 / :98)
 *            pTableSoe                      DATA_BLOCK_ID_SOE                      (:129 / :99)
 *            pTableSof                      DATA_BLOCK_ID_SOF                      (:130 / :100)
 *            pTableSoh                      DATA_BLOCK_ID_SOH                      (:131 / :101)
 *            pTableStateRequest             DATA_BLOCK_ID_STATE_REQUEST             (:132 / :102)
 *            pTableAerosolSensor            DATA_BLOCK_ID_AEROSOL_SENSOR            (:133 / :103)
 *            pTableBalancingControl         DATA_BLOCK_ID_BALANCING_CONTROL         (:134 / :104)
 *            pTablePhy                      DATA_BLOCK_ID_PHY                      (:135 / :105)
 *
 *          The values were derived twice by two methods that share no code:
 *          a parser of the source literals (`tools/derive_cfg_tables.py`), and
 *          the compiled module's objects read through the harness. All 116
 *          derived values agreed.
 *
 *          WHAT THIS DOES NOT ESTABLISH
 *          ----------------------------
 *          canREG1 and canREG2 are ordinary objects in the host shadow memory the
 *          harness declares (sil/iface/HL_can.h); the assertions here check which
 *          object each node names, not where the CAN controller sits in the
 *          address space. Nothing here establishes a register offset, a base
 *          address or a bit mask.
 */

/*========== Includes =======================================================*/
#include "unity.h"
#include "Mockcan.h"
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
TEST_SOURCE_FILE("can_cfg.c")

TEST_INCLUDE_PATH("../../src/app/driver/can")
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

/** @brief   number of database-table handles the shim carries (can_cfg.c:110-135) */
#define TEST_CAN_SHIM_N_TABLES (26u)

/*========== Setup and Teardown =============================================*/
void setUp(void) {
}

void tearDown(void) {
}

/*========== Test Cases =====================================================*/

/** @brief   each CAN node names the peripheral can_cfg.c assigns to it
 * @details can_cfg.c:70 assigns canREG1 to can_node1 and can_cfg.c:74 assigns
 *          canREG2 to can_node2Isolated.
 */
void testCanNodesNameTheirAssignedRegisters(void) {
    /* can_cfg.c:70 */
    TEST_ASSERT_EQUAL_PTR(canREG1, can_node1.canNodeRegister);
    /* can_cfg.c:74 */
    TEST_ASSERT_EQUAL_PTR(canREG2, can_node2Isolated.canNodeRegister);
}

/** @brief   the two CAN nodes are not the same peripheral
 * @details can_cfg.c:70 and :74. Two nodes sharing a register would make the
 *          isolated second CAN unreachable.
 */
void testCanNodesAreDistinctRegisters(void) {
    TEST_ASSERT_TRUE(can_node1.canNodeRegister != can_node2Isolated.canNodeRegister);
}

/** @brief   the IMD message queue handle in the shim is the task's queue
 * @details can_cfg.c:109 assigns &ftsk_imdCanDataQueue, the object the test file
 *          itself defines, so the assertion is identity rather than non-NULL.
 */
void testCanShimImdQueueIsTheTaskQueue(void) {
    /* can_cfg.c:109 */
    TEST_ASSERT_EQUAL_PTR(&ftsk_imdCanDataQueue, can_kShim.pQueueImd);
}

/** @brief   the cell temperature shim entry names the cell temperature block
 * @details can_cfg.c:110 wires can_tableTemperatures into pTableCellTemperature;
 *          can_cfg.c:79 gives that block DATA_BLOCK_ID_CELL_TEMPERATURE.
 */
void testCanShimCellTemperaturePointsAtTheTemperatureBlock(void) {
    /* can_cfg.c:79 */
    TEST_ASSERT_EQUAL(DATA_BLOCK_ID_CELL_TEMPERATURE, can_kShim.pTableCellTemperature->header.uniqueId);
}

/** @brief   the cell voltage shim entry names the cell voltage block
 * @details can_cfg.c:111 wires can_tableCellVoltages into pTableCellVoltage;
 *          can_cfg.c:80 gives that block DATA_BLOCK_ID_CELL_VOLTAGE.
 */
void testCanShimCellVoltagePointsAtTheVoltageBlock(void) {
    /* can_cfg.c:80 */
    TEST_ASSERT_EQUAL(DATA_BLOCK_ID_CELL_VOLTAGE, can_kShim.pTableCellVoltage->header.uniqueId);
}

/** @brief   the current shim entry names the current block
 * @details can_cfg.c:112 wires can_tableCurrent into pTableCurrent;
 *          can_cfg.c:81 gives that block DATA_BLOCK_ID_CURRENT.
 */
void testCanShimCurrentPointsAtTheCurrentBlock(void) {
    /* can_cfg.c:81 */
    TEST_ASSERT_EQUAL(DATA_BLOCK_ID_CURRENT, can_kShim.pTableCurrent->header.uniqueId);
}

/** @brief   the current sensor temperature entry names its own block
 * @details can_cfg.c:113 wires can_tableCurrentSensorTemperature into
 *          pTableCurrentSensorTemperature; can_cfg.c:83 gives that block
 *          DATA_BLOCK_ID_CURRENT_SENSOR_TEMPERATURE. This is the entry most
 *          likely to be confused with the plain cell temperature block, so it is
 *          asserted against both ids.
 */
void testCanShimCurrentSensorTemperaturePointsAtItsOwnBlock(void) {
    /* can_cfg.c:83 */
    TEST_ASSERT_EQUAL(DATA_BLOCK_ID_CURRENT_SENSOR_TEMPERATURE,
                          can_kShim.pTableCurrentSensorTemperature->header.uniqueId);
    TEST_ASSERT_NOT_EQUAL(DATA_BLOCK_ID_CELL_TEMPERATURE,
                              can_kShim.pTableCurrentSensorTemperature->header.uniqueId);
}

/** @brief   the power shim entry names the power block
 * @details can_cfg.c:114 wires can_tablePower into pTablePower;
 *          can_cfg.c:84 gives that block DATA_BLOCK_ID_POWER.
 */
void testCanShimPowerPointsAtThePowerBlock(void) {
    /* can_cfg.c:84 */
    TEST_ASSERT_EQUAL(DATA_BLOCK_ID_POWER, can_kShim.pTablePower->header.uniqueId);
}

/** @brief   the two counter entries name their own counter blocks
 * @details can_cfg.c:115 and :116 wire the current and energy counters;
 *          can_cfg.c:85 and :86 give those blocks their ids.
 */
void testCanShimCountersPointAtTheirOwnBlocks(void) {
    /* can_cfg.c:85 */
    TEST_ASSERT_EQUAL(DATA_BLOCK_ID_CURRENT_COUNTER, can_kShim.pTableCurrentCounter->header.uniqueId);
    /* can_cfg.c:86 */
    TEST_ASSERT_EQUAL(DATA_BLOCK_ID_ENERGY_COUNTER, can_kShim.pTableEnergyCounter->header.uniqueId);
}

/** @brief   the three system-voltage entries name the three system-voltage blocks
 * @details can_cfg.c:117, :118 and :119 wire the three system voltage blocks;
 *          can_cfg.c:87, :88 and :89 give them DATA_BLOCK_ID_SYSTEM_VOLTAGE_1/2/3.
 *          All three ids are distinct, so each entry is checked against the other
 *          two as well.
 */
void testCanShimSystemVoltagesPointAtThreeDistinctBlocks(void) {
    /* can_cfg.c:87 */
    TEST_ASSERT_EQUAL(DATA_BLOCK_ID_SYSTEM_VOLTAGE_1, can_kShim.pTableSystemVoltage1->header.uniqueId);
    /* can_cfg.c:88 */
    TEST_ASSERT_EQUAL(DATA_BLOCK_ID_SYSTEM_VOLTAGE_2, can_kShim.pTableSystemVoltage2->header.uniqueId);
    /* can_cfg.c:89 */
    TEST_ASSERT_EQUAL(DATA_BLOCK_ID_SYSTEM_VOLTAGE_3, can_kShim.pTableSystemVoltage3->header.uniqueId);
    TEST_ASSERT_NOT_EQUAL(can_kShim.pTableSystemVoltage1->header.uniqueId,
                              can_kShim.pTableSystemVoltage2->header.uniqueId);
    TEST_ASSERT_NOT_EQUAL(can_kShim.pTableSystemVoltage2->header.uniqueId,
                              can_kShim.pTableSystemVoltage3->header.uniqueId);
    TEST_ASSERT_NOT_EQUAL(can_kShim.pTableSystemVoltage1->header.uniqueId,
                              can_kShim.pTableSystemVoltage3->header.uniqueId);
}

/** @brief   the error-state entry names the error-state block
 * @details can_cfg.c:120 wires can_tableErrorState into pTableErrorState;
 *          can_cfg.c:90 gives that block DATA_BLOCK_ID_ERROR_STATE.
 */
void testCanShimErrorStatePointsAtTheErrorStateBlock(void) {
    /* can_cfg.c:90 */
    TEST_ASSERT_EQUAL(DATA_BLOCK_ID_ERROR_STATE, can_kShim.pTableErrorState->header.uniqueId);
}

/** @brief   the insulation entry names the insulation block
 * @details can_cfg.c:121 wires can_tableInsulation into pTableInsulation;
 *          can_cfg.c:91 gives that block DATA_BLOCK_ID_INSULATION.
 */
void testCanShimInsulationPointsAtTheInsulationBlock(void) {
    /* can_cfg.c:91 */
    TEST_ASSERT_EQUAL(DATA_BLOCK_ID_INSULATION, can_kShim.pTableInsulation->header.uniqueId);
}

/** @brief   the min/max entry names the min/max block
 * @details can_cfg.c:122 wires can_tableMinimumMaximumValues into pTableMinMax;
 *          can_cfg.c:92 gives that block DATA_BLOCK_ID_MIN_MAX.
 */
void testCanShimMinMaxPointsAtTheMinMaxBlock(void) {
    /* can_cfg.c:92 */
    TEST_ASSERT_EQUAL(DATA_BLOCK_ID_MIN_MAX, can_kShim.pTableMinMax->header.uniqueId);
}

/** @brief   the three safety-flag entries name their own flag blocks
 * @details can_cfg.c:123, :124 and :127 wire the MOL, MSL and RSL flags;
 *          can_cfg.c:93, :94 and :97 give those blocks their ids. The three ids
 *          are distinct, so the entries are checked against each other too.
 */
void testCanShimSafetyFlagsPointAtThreeDistinctBlocks(void) {
    /* can_cfg.c:93 */
    TEST_ASSERT_EQUAL(DATA_BLOCK_ID_MOL_FLAG, can_kShim.pTableMol->header.uniqueId);
    /* can_cfg.c:94 */
    TEST_ASSERT_EQUAL(DATA_BLOCK_ID_MSL_FLAG, can_kShim.pTableMsl->header.uniqueId);
    /* can_cfg.c:97 */
    TEST_ASSERT_EQUAL(DATA_BLOCK_ID_RSL_FLAG, can_kShim.pTableRsl->header.uniqueId);
    TEST_ASSERT_NOT_EQUAL(can_kShim.pTableMol->header.uniqueId, can_kShim.pTableMsl->header.uniqueId);
    TEST_ASSERT_NOT_EQUAL(can_kShim.pTableMsl->header.uniqueId, can_kShim.pTableRsl->header.uniqueId);
    TEST_ASSERT_NOT_EQUAL(can_kShim.pTableMol->header.uniqueId, can_kShim.pTableRsl->header.uniqueId);
}

/** @brief   the open-wire entry names the open-wire base block
 * @details can_cfg.c:125 wires can_tableOpenWire into pTableOpenWire;
 *          can_cfg.c:95 gives that block DATA_BLOCK_ID_OPEN_WIRE_BASE. That is the
 *          _BASE id and not one of the redundancy-specific ones, so the assertion
 *          pins the base variant specifically.
 */
void testCanShimOpenWirePointsAtTheBaseBlock(void) {
    /* can_cfg.c:95 */
    TEST_ASSERT_EQUAL(DATA_BLOCK_ID_OPEN_WIRE_BASE, can_kShim.pTableOpenWire->header.uniqueId);
}

/** @brief   the pack-values entry names the pack-values block
 * @details can_cfg.c:126 wires can_tablePackValues into pTablePackValues;
 *          can_cfg.c:96 gives that block DATA_BLOCK_ID_PACK_VALUES.
 */
void testCanShimPackValuesPointsAtThePackValuesBlock(void) {
    /* can_cfg.c:96 */
    TEST_ASSERT_EQUAL(DATA_BLOCK_ID_PACK_VALUES, can_kShim.pTablePackValues->header.uniqueId);
}

/** @brief   the SOC, SOE, SOF and SOH entries each name their own block
 * @details can_cfg.c:128-131 wire the four state-of blocks; can_cfg.c:98-101
 *          give them DATA_BLOCK_ID_SOC, _SOE, _SOF and _SOH. These four names are
 *          easy to transpose, so each entry is also checked against the others.
 */
void testCanShimStateOfBlocksPointAtFourDistinctBlocks(void) {
    /* can_cfg.c:98 */
    TEST_ASSERT_EQUAL(DATA_BLOCK_ID_SOC, can_kShim.pTableSoc->header.uniqueId);
    /* can_cfg.c:99 */
    TEST_ASSERT_EQUAL(DATA_BLOCK_ID_SOE, can_kShim.pTableSoe->header.uniqueId);
    /* can_cfg.c:100 */
    TEST_ASSERT_EQUAL(DATA_BLOCK_ID_SOF, can_kShim.pTableSof->header.uniqueId);
    /* can_cfg.c:101 */
    TEST_ASSERT_EQUAL(DATA_BLOCK_ID_SOH, can_kShim.pTableSoh->header.uniqueId);
    TEST_ASSERT_NOT_EQUAL(can_kShim.pTableSoc->header.uniqueId, can_kShim.pTableSoe->header.uniqueId);
    TEST_ASSERT_NOT_EQUAL(can_kShim.pTableSoe->header.uniqueId, can_kShim.pTableSof->header.uniqueId);
    TEST_ASSERT_NOT_EQUAL(can_kShim.pTableSof->header.uniqueId, can_kShim.pTableSoh->header.uniqueId);
}

/** @brief   the state-request entry names the state-request block
 * @details can_cfg.c:132 wires can_tableStateRequest into pTableStateRequest;
 *          can_cfg.c:102 gives that block DATA_BLOCK_ID_STATE_REQUEST.
 */
void testCanShimStateRequestPointsAtTheStateRequestBlock(void) {
    /* can_cfg.c:102 */
    TEST_ASSERT_EQUAL(DATA_BLOCK_ID_STATE_REQUEST, can_kShim.pTableStateRequest->header.uniqueId);
}

/** @brief   the aerosol-sensor entry names the aerosol-sensor block
 * @details can_cfg.c:133 wires can_tableAerosolSensor into pTableAerosolSensor;
 *          can_cfg.c:103 gives that block DATA_BLOCK_ID_AEROSOL_SENSOR.
 */
void testCanShimAerosolSensorPointsAtTheAerosolBlock(void) {
    /* can_cfg.c:103 */
    TEST_ASSERT_EQUAL(DATA_BLOCK_ID_AEROSOL_SENSOR, can_kShim.pTableAerosolSensor->header.uniqueId);
}

/** @brief   the balancing-control entry names the balancing-control block
 * @details can_cfg.c:134 wires can_tableBalancingControl into
 *          pTableBalancingControl; can_cfg.c:104 gives that block
 *          DATA_BLOCK_ID_BALANCING_CONTROL.
 */
void testCanShimBalancingControlPointsAtTheBalancingBlock(void) {
    /* can_cfg.c:104 */
    TEST_ASSERT_EQUAL(DATA_BLOCK_ID_BALANCING_CONTROL, can_kShim.pTableBalancingControl->header.uniqueId);
}

/** @brief   the PHY entry names the PHY block
 * @details can_cfg.c:135 wires can_tablePhy into pTablePhy;
 *          can_cfg.c:105 gives that block DATA_BLOCK_ID_PHY.
 */
void testCanShimPhyPointsAtThePhyBlock(void) {
    /* can_cfg.c:105 */
    TEST_ASSERT_EQUAL(DATA_BLOCK_ID_PHY, can_kShim.pTablePhy->header.uniqueId);
}

/** @brief   every shim table pointer is populated
 * @details The 26 handles are wired at can_cfg.c:110-135. A NULL handle would
 *          make every CAN callback touching that signal dereference NULL.
 */
void testCanShimEveryTablePointerIsPopulated(void) {
    const void *const kpkTables[TEST_CAN_SHIM_N_TABLES] = {
        can_kShim.pTableCellTemperature,
            can_kShim.pTableCellVoltage,
            can_kShim.pTableCurrent,
            can_kShim.pTableCurrentSensorTemperature,
            can_kShim.pTablePower,
            can_kShim.pTableCurrentCounter,
            can_kShim.pTableEnergyCounter,
            can_kShim.pTableSystemVoltage1,
            can_kShim.pTableSystemVoltage2,
            can_kShim.pTableSystemVoltage3,
            can_kShim.pTableErrorState,
            can_kShim.pTableInsulation,
            can_kShim.pTableMinMax,
            can_kShim.pTableMol,
            can_kShim.pTableMsl,
            can_kShim.pTableOpenWire,
            can_kShim.pTablePackValues,
            can_kShim.pTableRsl,
            can_kShim.pTableSoc,
            can_kShim.pTableSoe,
            can_kShim.pTableSof,
            can_kShim.pTableSoh,
            can_kShim.pTableStateRequest,
            can_kShim.pTableAerosolSensor,
            can_kShim.pTableBalancingControl,
            can_kShim.pTablePhy};
    uint32_t u;
    for (u = 0u; u < TEST_CAN_SHIM_N_TABLES; u++) {
        TEST_ASSERT_NOT_NULL(kpkTables[u]);
    }
}

/** @brief   no two shim table pointers name the same database block
 * @details Two shim fields pointing at one block would make two different CAN
 *          signals read and write the same entry. The 26 handles come from
 *          can_cfg.c:110-135.
 */
void testCanShimTablePointersAreDistinct(void) {
    const void *const kpkTables[TEST_CAN_SHIM_N_TABLES] = {
        can_kShim.pTableCellTemperature,
            can_kShim.pTableCellVoltage,
            can_kShim.pTableCurrent,
            can_kShim.pTableCurrentSensorTemperature,
            can_kShim.pTablePower,
            can_kShim.pTableCurrentCounter,
            can_kShim.pTableEnergyCounter,
            can_kShim.pTableSystemVoltage1,
            can_kShim.pTableSystemVoltage2,
            can_kShim.pTableSystemVoltage3,
            can_kShim.pTableErrorState,
            can_kShim.pTableInsulation,
            can_kShim.pTableMinMax,
            can_kShim.pTableMol,
            can_kShim.pTableMsl,
            can_kShim.pTableOpenWire,
            can_kShim.pTablePackValues,
            can_kShim.pTableRsl,
            can_kShim.pTableSoc,
            can_kShim.pTableSoe,
            can_kShim.pTableSof,
            can_kShim.pTableSoh,
            can_kShim.pTableStateRequest,
            can_kShim.pTableAerosolSensor,
            can_kShim.pTableBalancingControl,
            can_kShim.pTablePhy};
    uint32_t u;
    uint32_t v;
    for (u = 0u; u < TEST_CAN_SHIM_N_TABLES; u++) {
        for (v = u + 1u; v < TEST_CAN_SHIM_N_TABLES; v++) {
            TEST_ASSERT_TRUE(kpkTables[u] != kpkTables[v]);
        }
    }
}

/** @brief   every shim table block carries a valid database-entry id
 * @details The ids come from the initialisers at can_cfg.c:79-105. DATA_BLOCK_ID_MAX
 *          is the first invalid value (database_cfg.h:121), so no block may reach
 *          or exceed it.
 */
void testCanShimEveryBlockIdIsWithinTheDatabaseEnumeration(void) {
    const uint32_t kpkIds[TEST_CAN_SHIM_N_TABLES] = {
        (uint32_t)can_kShim.pTableCellTemperature->header.uniqueId,
        (uint32_t)can_kShim.pTableCellVoltage->header.uniqueId,
        (uint32_t)can_kShim.pTableCurrent->header.uniqueId,
        (uint32_t)can_kShim.pTableCurrentSensorTemperature->header.uniqueId,
        (uint32_t)can_kShim.pTablePower->header.uniqueId,
        (uint32_t)can_kShim.pTableCurrentCounter->header.uniqueId,
        (uint32_t)can_kShim.pTableEnergyCounter->header.uniqueId,
        (uint32_t)can_kShim.pTableSystemVoltage1->header.uniqueId,
        (uint32_t)can_kShim.pTableSystemVoltage2->header.uniqueId,
        (uint32_t)can_kShim.pTableSystemVoltage3->header.uniqueId,
        (uint32_t)can_kShim.pTableErrorState->header.uniqueId,
        (uint32_t)can_kShim.pTableInsulation->header.uniqueId,
        (uint32_t)can_kShim.pTableMinMax->header.uniqueId,
        (uint32_t)can_kShim.pTableMol->header.uniqueId,
        (uint32_t)can_kShim.pTableMsl->header.uniqueId,
        (uint32_t)can_kShim.pTableOpenWire->header.uniqueId,
        (uint32_t)can_kShim.pTablePackValues->header.uniqueId,
        (uint32_t)can_kShim.pTableRsl->header.uniqueId,
        (uint32_t)can_kShim.pTableSoc->header.uniqueId,
        (uint32_t)can_kShim.pTableSoe->header.uniqueId,
        (uint32_t)can_kShim.pTableSof->header.uniqueId,
        (uint32_t)can_kShim.pTableSoh->header.uniqueId,
        (uint32_t)can_kShim.pTableStateRequest->header.uniqueId,
        (uint32_t)can_kShim.pTableAerosolSensor->header.uniqueId,
        (uint32_t)can_kShim.pTableBalancingControl->header.uniqueId,
        (uint32_t)can_kShim.pTablePhy->header.uniqueId};
    uint32_t u;
    for (u = 0u; u < TEST_CAN_SHIM_N_TABLES; u++) {
        /* database_cfg.h:121 */
        TEST_ASSERT_LESS_THAN_UINT32(DATA_BLOCK_ID_MAX, kpkIds[u]);
    }
}
