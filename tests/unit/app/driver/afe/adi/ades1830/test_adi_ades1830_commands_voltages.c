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
 * @file    test_adi_ades1830_commands_voltages.c
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

#include "adi_ades183x_commands_voltages.h"
/* The six cell-voltage command words (adi_cmdRdcva..f) are declared in the base
 * command header, not in the voltages header, even though their initialisers
 * live in adi_ades183x_commands_voltages.c. Both headers are needed to name
 * every table this file asserts. */
#include "adi_ades183x_commands.h"

#include <stdint.h>

/*========== Unit Testing Framework Directives ==============================*/
TEST_SOURCE_FILE("adi_ades183x_commands_voltages.c")
TEST_INCLUDE_PATH("../../src/app/driver/afe/adi/ades1830")
TEST_INCLUDE_PATH("../../src/app/driver/afe/adi/common/ades183x")
TEST_INCLUDE_PATH("../../src/app/driver/afe/adi/common/ades183x/diag")
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
 * @brief   Every table in adi_ades183x_commands_voltages.c encodes one command as
 *          {register byte 0, register byte 1, increment flag, length} in a
 *          four-element uint16_t. These are the auxiliary-voltage and die-temperature command words. A wrong entry addresses
 *          the wrong ADI register, so the driver reads back a plausible-looking
 *          but incorrect measurement with no error raised anywhere.
 * @details All 24 tables, each asserted as four LITERAL values. The macros
 *          are deliberately not used in the assertions: the source line writes
 *          the macro, so comparing against the macro would be self-referential
 *          and could not fail. Each literal is cited to the initialiser line in
 *          adi_ades183x_commands_voltages.c and, in the trailing comment, to the ADI_* macro it came
 *          from; every one of those macros is a #define in
 *          adi_ades183x_defs.h. The dimension is
 *          ADI_COMMAND_DEFINITION_LENGTH = (4u) at adi_ades183x_defs.h:554.
 */
void testAdiCommandTableRegisterAddresses(void) {
    /* adi_cmdRdaca  [adi_ades183x_commands_voltages.c:98]  {ADI_RDACA_BYTE0=0 ADI_RDACA_BYTE1=68 ADI_RDACA_INC=0 ADI_RDACA_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdaca[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(68, adi_cmdRdaca[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdaca[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdRdaca[3]);  /* LEN */
    /* adi_cmdRdacb  [adi_ades183x_commands_voltages.c:103]  {ADI_RDACB_BYTE0=0 ADI_RDACB_BYTE1=70 ADI_RDACB_INC=0 ADI_RDACB_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdacb[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(70, adi_cmdRdacb[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdacb[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdRdacb[3]);  /* LEN */
    /* adi_cmdRdacc  [adi_ades183x_commands_voltages.c:108]  {ADI_RDACC_BYTE0=0 ADI_RDACC_BYTE1=72 ADI_RDACC_INC=0 ADI_RDACC_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdacc[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(72, adi_cmdRdacc[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdacc[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdRdacc[3]);  /* LEN */
    /* adi_cmdRdacd  [adi_ades183x_commands_voltages.c:113]  {ADI_RDACD_BYTE0=0 ADI_RDACD_BYTE1=74 ADI_RDACD_INC=0 ADI_RDACD_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdacd[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(74, adi_cmdRdacd[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdacd[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdRdacd[3]);  /* LEN */
    /* adi_cmdRdace  [adi_ades183x_commands_voltages.c:118]  {ADI_RDACE_BYTE0=0 ADI_RDACE_BYTE1=73 ADI_RDACE_INC=0 ADI_RDACE_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdace[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(73, adi_cmdRdace[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdace[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdRdace[3]);  /* LEN */
    /* adi_cmdRdacf  [adi_ades183x_commands_voltages.c:123]  {ADI_RDACF_BYTE0=0 ADI_RDACF_BYTE1=75 ADI_RDACF_INC=0 ADI_RDACF_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdacf[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(75, adi_cmdRdacf[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdacf[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdRdacf[3]);  /* LEN */
    /* adi_cmdRdcva  [adi_ades183x_commands_voltages.c:67]  {ADI_RDCVA_BYTE0=0 ADI_RDCVA_BYTE1=4 ADI_RDCVA_INC=0 ADI_RDCVA_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdcva[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(4, adi_cmdRdcva[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdcva[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdRdcva[3]);  /* LEN */
    /* adi_cmdRdcvb  [adi_ades183x_commands_voltages.c:72]  {ADI_RDCVB_BYTE0=0 ADI_RDCVB_BYTE1=6 ADI_RDCVB_INC=0 ADI_RDCVB_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdcvb[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdRdcvb[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdcvb[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdRdcvb[3]);  /* LEN */
    /* adi_cmdRdcvc  [adi_ades183x_commands_voltages.c:77]  {ADI_RDCVC_BYTE0=0 ADI_RDCVC_BYTE1=8 ADI_RDCVC_INC=0 ADI_RDCVC_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdcvc[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(8, adi_cmdRdcvc[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdcvc[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdRdcvc[3]);  /* LEN */
    /* adi_cmdRdcvd  [adi_ades183x_commands_voltages.c:82]  {ADI_RDCVD_BYTE0=0 ADI_RDCVD_BYTE1=10 ADI_RDCVD_INC=0 ADI_RDCVD_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdcvd[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(10, adi_cmdRdcvd[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdcvd[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdRdcvd[3]);  /* LEN */
    /* adi_cmdRdcve  [adi_ades183x_commands_voltages.c:87]  {ADI_RDCVE_BYTE0=0 ADI_RDCVE_BYTE1=9 ADI_RDCVE_INC=0 ADI_RDCVE_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdcve[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(9, adi_cmdRdcve[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdcve[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdRdcve[3]);  /* LEN */
    /* adi_cmdRdcvf  [adi_ades183x_commands_voltages.c:92]  {ADI_RDCVF_BYTE0=0 ADI_RDCVF_BYTE1=11 ADI_RDCVF_INC=0 ADI_RDCVF_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdcvf[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(11, adi_cmdRdcvf[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdcvf[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdRdcvf[3]);  /* LEN */
    /* adi_cmdRdfca  [adi_ades183x_commands_voltages.c:129]  {ADI_RDFCA_BYTE0=0 ADI_RDFCA_BYTE1=18 ADI_RDFCA_INC=0 ADI_RDFCA_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdfca[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(18, adi_cmdRdfca[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdfca[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdRdfca[3]);  /* LEN */
    /* adi_cmdRdfcb  [adi_ades183x_commands_voltages.c:134]  {ADI_RDFCB_BYTE0=0 ADI_RDFCB_BYTE1=19 ADI_RDFCB_INC=0 ADI_RDFCB_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdfcb[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(19, adi_cmdRdfcb[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdfcb[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdRdfcb[3]);  /* LEN */
    /* adi_cmdRdfcc  [adi_ades183x_commands_voltages.c:139]  {ADI_RDFCC_BYTE0=0 ADI_RDFCC_BYTE1=20 ADI_RDFCC_INC=0 ADI_RDFCC_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdfcc[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(20, adi_cmdRdfcc[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdfcc[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdRdfcc[3]);  /* LEN */
    /* adi_cmdRdfcd  [adi_ades183x_commands_voltages.c:144]  {ADI_RDFCD_BYTE0=0 ADI_RDFCD_BYTE1=21 ADI_RDFCD_INC=0 ADI_RDFCD_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdfcd[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(21, adi_cmdRdfcd[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdfcd[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdRdfcd[3]);  /* LEN */
    /* adi_cmdRdfce  [adi_ades183x_commands_voltages.c:149]  {ADI_RDFCE_BYTE0=0 ADI_RDFCE_BYTE1=22 ADI_RDFCE_INC=0 ADI_RDFCE_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdfce[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(22, adi_cmdRdfce[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdfce[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdRdfce[3]);  /* LEN */
    /* adi_cmdRdfcf  [adi_ades183x_commands_voltages.c:154]  {ADI_RDFCF_BYTE0=0 ADI_RDFCF_BYTE1=23 ADI_RDFCF_INC=0 ADI_RDFCF_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdfcf[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(23, adi_cmdRdfcf[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdfcf[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdRdfcf[3]);  /* LEN */
    /* adi_cmdRdsva  [adi_ades183x_commands_voltages.c:160]  {ADI_RDSVA_BYTE0=0 ADI_RDSVA_BYTE1=3 ADI_RDSVA_INC=0 ADI_RDSVA_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdsva[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(3, adi_cmdRdsva[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdsva[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdRdsva[3]);  /* LEN */
    /* adi_cmdRdsvb  [adi_ades183x_commands_voltages.c:165]  {ADI_RDSVB_BYTE0=0 ADI_RDSVB_BYTE1=5 ADI_RDSVB_INC=0 ADI_RDSVB_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdsvb[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(5, adi_cmdRdsvb[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdsvb[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdRdsvb[3]);  /* LEN */
    /* adi_cmdRdsvc  [adi_ades183x_commands_voltages.c:170]  {ADI_RDSVC_BYTE0=0 ADI_RDSVC_BYTE1=7 ADI_RDSVC_INC=0 ADI_RDSVC_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdsvc[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(7, adi_cmdRdsvc[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdsvc[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdRdsvc[3]);  /* LEN */
    /* adi_cmdRdsvd  [adi_ades183x_commands_voltages.c:175]  {ADI_RDSVD_BYTE0=0 ADI_RDSVD_BYTE1=13 ADI_RDSVD_INC=0 ADI_RDSVD_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdsvd[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(13, adi_cmdRdsvd[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdsvd[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdRdsvd[3]);  /* LEN */
    /* adi_cmdRdsve  [adi_ades183x_commands_voltages.c:180]  {ADI_RDSVE_BYTE0=0 ADI_RDSVE_BYTE1=14 ADI_RDSVE_INC=0 ADI_RDSVE_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdsve[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(14, adi_cmdRdsve[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdsve[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdRdsve[3]);  /* LEN */
    /* adi_cmdRdsvf  [adi_ades183x_commands_voltages.c:185]  {ADI_RDSVF_BYTE0=0 ADI_RDSVF_BYTE1=15 ADI_RDSVF_INC=0 ADI_RDSVF_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdsvf[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(15, adi_cmdRdsvf[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdsvf[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdRdsvf[3]);  /* LEN */
}

/**
 * @brief   The tables are declared with the shared dimension
 *          ADI_COMMAND_DEFINITION_LENGTH. The driver indexes element 3 (LEN)
 *          without bounds checking, so a table declared shorter than the driver
 *          assumes would read past its end. Assert the dimension of every table
 *          in this file, as the literal 4.
 * @details adi_ades183x_defs.h:554 defines ADI_COMMAND_DEFINITION_LENGTH as
 *          (4u). Written as a literal rather than as
 *          sizeof(adi_cmdX)/sizeof(adi_cmdX[0]) == ADI_COMMAND_DEFINITION_LENGTH,
 *          because that comparison is a macro against its own definition.
 */
void testAdiCommandTablesHaveUniformLength(void) {
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdRdaca) / sizeof(adi_cmdRdaca[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdRdacb) / sizeof(adi_cmdRdacb[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdRdacc) / sizeof(adi_cmdRdacc[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdRdacd) / sizeof(adi_cmdRdacd[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdRdace) / sizeof(adi_cmdRdace[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdRdacf) / sizeof(adi_cmdRdacf[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdRdcva) / sizeof(adi_cmdRdcva[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdRdcvb) / sizeof(adi_cmdRdcvb[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdRdcvc) / sizeof(adi_cmdRdcvc[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdRdcvd) / sizeof(adi_cmdRdcvd[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdRdcve) / sizeof(adi_cmdRdcve[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdRdcvf) / sizeof(adi_cmdRdcvf[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdRdfca) / sizeof(adi_cmdRdfca[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdRdfcb) / sizeof(adi_cmdRdfcb[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdRdfcc) / sizeof(adi_cmdRdfcc[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdRdfcd) / sizeof(adi_cmdRdfcd[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdRdfce) / sizeof(adi_cmdRdfce[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdRdfcf) / sizeof(adi_cmdRdfcf[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdRdsva) / sizeof(adi_cmdRdsva[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdRdsvb) / sizeof(adi_cmdRdsvb[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdRdsvc) / sizeof(adi_cmdRdsvc[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdRdsvd) / sizeof(adi_cmdRdsvd[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdRdsve) / sizeof(adi_cmdRdsve[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdRdsvf) / sizeof(adi_cmdRdsvf[0])));
}
