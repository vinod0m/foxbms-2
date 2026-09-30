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
 * @file    test_adi_ades1830_commands.c
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

#include "adi_ades183x_commands.h"

#include <stdint.h>

/*========== Unit Testing Framework Directives ==============================*/
TEST_SOURCE_FILE("adi_ades183x_commands.c")
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
 * @brief   Every table in adi_ades183x_commands.c encodes one command as
 *          {register byte 0, register byte 1, increment flag, length} in a
 *          four-element uint16_t. These are the configuration, status, auxiliary, clear/mute and cell-voltage command words. A wrong entry addresses
 *          the wrong ADI register, so the driver reads back a plausible-looking
 *          but incorrect measurement with no error raised anywhere.
 * @details All 35 tables, each asserted as four LITERAL values. The macros
 *          are deliberately not used in the assertions: the source line writes
 *          the macro, so comparing against the macro would be self-referential
 *          and could not fail. Each literal is cited to the initialiser line in
 *          adi_ades183x_commands.c and, in the trailing comment, to the ADI_* macro it came
 *          from; every one of those macros is a #define in
 *          adi_ades183x_defs.h. The dimension is
 *          ADI_COMMAND_DEFINITION_LENGTH = (4u) at adi_ades183x_defs.h:554.
 */
void testAdiCommandTableRegisterAddresses(void) {
    /* adi_cmdAdax  [adi_ades183x_commands.c:127]  {ADI_ADAX_BYTE0=4 ADI_ADAX_BYTE1=16 ADI_ADAX_INC=1 ADI_ADAX_LEN=0} */
    TEST_ASSERT_EQUAL_UINT16(4, adi_cmdAdax[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(16, adi_cmdAdax[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(1, adi_cmdAdax[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdAdax[3]);  /* LEN */
    /* adi_cmdAdax2  [adi_ades183x_commands.c:132]  {ADI_ADAX2_BYTE0=4 ADI_ADAX2_BYTE1=0 ADI_ADAX2_INC=1 ADI_ADAX2_LEN=0} */
    TEST_ASSERT_EQUAL_UINT16(4, adi_cmdAdax2[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdAdax2[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(1, adi_cmdAdax2[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdAdax2[3]);  /* LEN */
    /* adi_cmdAdcv  [adi_ades183x_commands.c:67]  {ADI_ADCV_BYTE0=2 ADI_ADCV_BYTE1=96 ADI_ADCV_INC=1 ADI_ADCV_LEN=0} */
    TEST_ASSERT_EQUAL_UINT16(2, adi_cmdAdcv[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(96, adi_cmdAdcv[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(1, adi_cmdAdcv[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdAdcv[3]);  /* LEN */
    /* adi_cmdAdsv  [adi_ades183x_commands.c:72]  {ADI_ADSV_BYTE0=1 ADI_ADSV_BYTE1=104 ADI_ADSV_INC=1 ADI_ADSV_LEN=0} */
    TEST_ASSERT_EQUAL_UINT16(1, adi_cmdAdsv[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(104, adi_cmdAdsv[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(1, adi_cmdAdsv[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdAdsv[3]);  /* LEN */
    /* adi_cmdClraux  [adi_ades183x_commands.c:185]  {ADI_CLRAUX_BYTE0=7 ADI_CLRAUX_BYTE1=18 ADI_CLRAUX_INC=1 ADI_CLRAUX_LEN=0} */
    TEST_ASSERT_EQUAL_UINT16(7, adi_cmdClraux[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(18, adi_cmdClraux[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(1, adi_cmdClraux[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdClraux[3]);  /* LEN */
    /* adi_cmdClrcell  [adi_ades183x_commands.c:217]  {ADI_CLRCELL_BYTE0=7 ADI_CLRCELL_BYTE1=17 ADI_CLRCELL_INC=1 ADI_CLRCELL_LEN=0} */
    TEST_ASSERT_EQUAL_UINT16(7, adi_cmdClrcell[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(17, adi_cmdClrcell[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(1, adi_cmdClrcell[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdClrcell[3]);  /* LEN */
    /* adi_cmdClrflag  [adi_ades183x_commands.c:222]  {ADI_CLRFLAG_BYTE0=7 ADI_CLRFLAG_BYTE1=23 ADI_CLRFLAG_INC=1 ADI_CLRFLAG_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(7, adi_cmdClrflag[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(23, adi_cmdClrflag[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(1, adi_cmdClrflag[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdClrflag[3]);  /* LEN */
    /* adi_cmdMute  [adi_ades183x_commands.c:110]  {ADI_MUTE_BYTE0=0 ADI_MUTE_BYTE1=40 ADI_MUTE_INC=1 ADI_MUTE_LEN=0} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdMute[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(40, adi_cmdMute[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(1, adi_cmdMute[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdMute[3]);  /* LEN */
    /* adi_cmdRdauxa  [adi_ades183x_commands.c:138]  {ADI_RDAUXA_BYTE0=0 ADI_RDAUXA_BYTE1=25 ADI_RDAUXA_INC=0 ADI_RDAUXA_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdauxa[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(25, adi_cmdRdauxa[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdauxa[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdRdauxa[3]);  /* LEN */
    /* adi_cmdRdauxb  [adi_ades183x_commands.c:143]  {ADI_RDAUXB_BYTE0=0 ADI_RDAUXB_BYTE1=26 ADI_RDAUXB_INC=0 ADI_RDAUXB_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdauxb[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(26, adi_cmdRdauxb[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdauxb[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdRdauxb[3]);  /* LEN */
    /* adi_cmdRdauxc  [adi_ades183x_commands.c:148]  {ADI_RDAUXC_BYTE0=0 ADI_RDAUXC_BYTE1=27 ADI_RDAUXC_INC=0 ADI_RDAUXC_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdauxc[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(27, adi_cmdRdauxc[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdauxc[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdRdauxc[3]);  /* LEN */
    /* adi_cmdRdauxd  [adi_ades183x_commands.c:153]  {ADI_RDAUXD_BYTE0=0 ADI_RDAUXD_BYTE1=31 ADI_RDAUXD_INC=0 ADI_RDAUXD_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdauxd[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(31, adi_cmdRdauxd[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdauxd[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdRdauxd[3]);  /* LEN */
    /* adi_cmdRdauxe  [adi_ades183x_commands.c:158]  {ADI_RDAUXE_BYTE0=0 ADI_RDAUXE_BYTE1=54 ADI_RDAUXE_INC=0 ADI_RDAUXE_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdauxe[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(54, adi_cmdRdauxe[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdauxe[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdRdauxe[3]);  /* LEN */
    /* adi_cmdRdcfga  [adi_ades183x_commands.c:88]  {ADI_RDCFGA_BYTE0=0 ADI_RDCFGA_BYTE1=2 ADI_RDCFGA_INC=0 ADI_RDCFGA_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdcfga[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(2, adi_cmdRdcfga[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdcfga[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdRdcfga[3]);  /* LEN */
    /* adi_cmdRdcfgb  [adi_ades183x_commands.c:93]  {ADI_RDCFGB_BYTE0=0 ADI_RDCFGB_BYTE1=38 ADI_RDCFGB_INC=0 ADI_RDCFGB_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdcfgb[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(38, adi_cmdRdcfgb[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdcfgb[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdRdcfgb[3]);  /* LEN */
    /* adi_cmdRdpwma  [adi_ades183x_commands.c:238]  {ADI_RDPWMA_BYTE0=0 ADI_RDPWMA_BYTE1=34 ADI_RDPWMA_INC=0 ADI_RDPWMA_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdpwma[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(34, adi_cmdRdpwma[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdpwma[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdRdpwma[3]);  /* LEN */
    /* adi_cmdRdraxa  [adi_ades183x_commands.c:164]  {ADI_RDRAXA_BYTE0=0 ADI_RDRAXA_BYTE1=28 ADI_RDRAXA_INC=0 ADI_RDRAXA_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdraxa[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(28, adi_cmdRdraxa[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdraxa[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdRdraxa[3]);  /* LEN */
    /* adi_cmdRdraxb  [adi_ades183x_commands.c:169]  {ADI_RDRAXB_BYTE0=0 ADI_RDRAXB_BYTE1=29 ADI_RDRAXB_INC=0 ADI_RDRAXB_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdraxb[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(29, adi_cmdRdraxb[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdraxb[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdRdraxb[3]);  /* LEN */
    /* adi_cmdRdraxc  [adi_ades183x_commands.c:174]  {ADI_RDRAXC_BYTE0=0 ADI_RDRAXC_BYTE1=30 ADI_RDRAXC_INC=0 ADI_RDRAXC_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdraxc[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(30, adi_cmdRdraxc[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdraxc[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdRdraxc[3]);  /* LEN */
    /* adi_cmdRdraxd  [adi_ades183x_commands.c:179]  {ADI_RDRAXD_BYTE0=0 ADI_RDRAXD_BYTE1=37 ADI_RDRAXD_INC=0 ADI_RDRAXD_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdraxd[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(37, adi_cmdRdraxd[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdraxd[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdRdraxd[3]);  /* LEN */
    /* adi_cmdRdsid  [adi_ades183x_commands.c:244]  {ADI_RDSID_BYTE0=0 ADI_RDSID_BYTE1=44 ADI_RDSID_INC=0 ADI_RDSID_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdsid[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(44, adi_cmdRdsid[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdsid[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdRdsid[3]);  /* LEN */
    /* adi_cmdRdstata  [adi_ades183x_commands.c:191]  {ADI_RDSTATA_BYTE0=0 ADI_RDSTATA_BYTE1=48 ADI_RDSTATA_INC=0 ADI_RDSTATA_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdstata[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(48, adi_cmdRdstata[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdstata[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdRdstata[3]);  /* LEN */
    /* adi_cmdRdstatb  [adi_ades183x_commands.c:196]  {ADI_RDSTATB_BYTE0=0 ADI_RDSTATB_BYTE1=49 ADI_RDSTATB_INC=0 ADI_RDSTATB_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdstatb[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(49, adi_cmdRdstatb[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdstatb[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdRdstatb[3]);  /* LEN */
    /* adi_cmdRdstatc  [adi_ades183x_commands.c:201]  {ADI_RDSTATC_BYTE0=0 ADI_RDSTATC_BYTE1=50 ADI_RDSTATC_INC=0 ADI_RDSTATC_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdstatc[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(50, adi_cmdRdstatc[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdstatc[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdRdstatc[3]);  /* LEN */
    /* adi_cmdRdstatd  [adi_ades183x_commands.c:206]  {ADI_RDSTATD_BYTE0=0 ADI_RDSTATD_BYTE1=51 ADI_RDSTATD_INC=0 ADI_RDSTATD_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdstatd[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(51, adi_cmdRdstatd[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdstatd[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdRdstatd[3]);  /* LEN */
    /* adi_cmdRdstate  [adi_ades183x_commands.c:211]  {ADI_RDSTATE_BYTE0=0 ADI_RDSTATE_BYTE1=52 ADI_RDSTATE_INC=0 ADI_RDSTATE_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdstate[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(52, adi_cmdRdstate[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRdstate[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdRdstate[3]);  /* LEN */
    /* adi_cmdRstcc  [adi_ades183x_commands.c:121]  {ADI_RSTCC_BYTE0=0 ADI_RSTCC_BYTE1=46 ADI_RSTCC_INC=0 ADI_RSTCC_LEN=0} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRstcc[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(46, adi_cmdRstcc[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRstcc[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdRstcc[3]);  /* LEN */
    /* adi_cmdSnap  [adi_ades183x_commands.c:99]  {ADI_SNAPSHOT_BYTE0=0 ADI_SNAPSHOT_BYTE1=45 ADI_SNAPSHOT_INC=1 ADI_SNAPSHOT_LEN=0} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdSnap[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(45, adi_cmdSnap[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(1, adi_cmdSnap[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdSnap[3]);  /* LEN */
    /* adi_cmdSrst  [adi_ades183x_commands.c:250]  {ADI_SRST_BYTE0=0 ADI_SRST_BYTE1=39 ADI_SRST_INC=0 ADI_SRST_LEN=0} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdSrst[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(39, adi_cmdSrst[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdSrst[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdSrst[3]);  /* LEN */
    /* adi_cmdUnmute  [adi_ades183x_commands.c:115]  {ADI_UNMUTE_BYTE0=0 ADI_UNMUTE_BYTE1=41 ADI_UNMUTE_INC=1 ADI_UNMUTE_LEN=0} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdUnmute[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(41, adi_cmdUnmute[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(1, adi_cmdUnmute[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdUnmute[3]);  /* LEN */
    /* adi_cmdUnsnap  [adi_ades183x_commands.c:104]  {ADI_UNSNAPSHOT_BYTE0=0 ADI_UNSNAPSHOT_BYTE1=47 ADI_UNSNAPSHOT_INC=1 ADI_UNSNAPSHOT_LEN=0} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdUnsnap[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(47, adi_cmdUnsnap[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(1, adi_cmdUnsnap[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdUnsnap[3]);  /* LEN */
    /* adi_cmdWrcfga  [adi_ades183x_commands.c:78]  {ADI_WRCFGA_BYTE0=0 ADI_WRCFGA_BYTE1=1 ADI_WRCFGA_INC=1 ADI_WRCFGA_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdWrcfga[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(1, adi_cmdWrcfga[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(1, adi_cmdWrcfga[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdWrcfga[3]);  /* LEN */
    /* adi_cmdWrcfgb  [adi_ades183x_commands.c:83]  {ADI_WRCFGB_BYTE0=0 ADI_WRCFGB_BYTE1=36 ADI_WRCFGB_INC=1 ADI_WRCFGB_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdWrcfgb[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(36, adi_cmdWrcfgb[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(1, adi_cmdWrcfgb[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdWrcfgb[3]);  /* LEN */
    /* adi_cmdWrpwma  [adi_ades183x_commands.c:228]  {ADI_WRPWMA_BYTE0=0 ADI_WRPWMA_BYTE1=32 ADI_WRPWMA_INC=1 ADI_WRPWMA_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdWrpwma[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(32, adi_cmdWrpwma[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(1, adi_cmdWrpwma[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdWrpwma[3]);  /* LEN */
    /* adi_cmdWrpwmb  [adi_ades183x_commands.c:233]  {ADI_WRPWMB_BYTE0=0 ADI_WRPWMB_BYTE1=33 ADI_WRPWMB_INC=1 ADI_WRPWMB_LEN=6} */
    TEST_ASSERT_EQUAL_UINT16(0, adi_cmdWrpwmb[0]);  /* BYTE0 */
    TEST_ASSERT_EQUAL_UINT16(33, adi_cmdWrpwmb[1]);  /* BYTE1 */
    TEST_ASSERT_EQUAL_UINT16(1, adi_cmdWrpwmb[2]);  /* INC */
    TEST_ASSERT_EQUAL_UINT16(6, adi_cmdWrpwmb[3]);  /* LEN */
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
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdAdax) / sizeof(adi_cmdAdax[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdAdax2) / sizeof(adi_cmdAdax2[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdAdcv) / sizeof(adi_cmdAdcv[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdAdsv) / sizeof(adi_cmdAdsv[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdClraux) / sizeof(adi_cmdClraux[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdClrcell) / sizeof(adi_cmdClrcell[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdClrflag) / sizeof(adi_cmdClrflag[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdMute) / sizeof(adi_cmdMute[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdRdauxa) / sizeof(adi_cmdRdauxa[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdRdauxb) / sizeof(adi_cmdRdauxb[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdRdauxc) / sizeof(adi_cmdRdauxc[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdRdauxd) / sizeof(adi_cmdRdauxd[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdRdauxe) / sizeof(adi_cmdRdauxe[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdRdcfga) / sizeof(adi_cmdRdcfga[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdRdcfgb) / sizeof(adi_cmdRdcfgb[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdRdpwma) / sizeof(adi_cmdRdpwma[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdRdraxa) / sizeof(adi_cmdRdraxa[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdRdraxb) / sizeof(adi_cmdRdraxb[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdRdraxc) / sizeof(adi_cmdRdraxc[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdRdraxd) / sizeof(adi_cmdRdraxd[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdRdsid) / sizeof(adi_cmdRdsid[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdRdstata) / sizeof(adi_cmdRdstata[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdRdstatb) / sizeof(adi_cmdRdstatb[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdRdstatc) / sizeof(adi_cmdRdstatc[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdRdstatd) / sizeof(adi_cmdRdstatd[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdRdstate) / sizeof(adi_cmdRdstate[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdRstcc) / sizeof(adi_cmdRstcc[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdSnap) / sizeof(adi_cmdSnap[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdSrst) / sizeof(adi_cmdSrst[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdUnmute) / sizeof(adi_cmdUnmute[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdUnsnap) / sizeof(adi_cmdUnsnap[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdWrcfga) / sizeof(adi_cmdWrcfga[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdWrcfgb) / sizeof(adi_cmdWrcfgb[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdWrpwma) / sizeof(adi_cmdWrpwma[0])));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)(sizeof(adi_cmdWrpwmb) / sizeof(adi_cmdWrpwmb[0])));
}
