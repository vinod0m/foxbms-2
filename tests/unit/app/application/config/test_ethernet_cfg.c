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
 * @file    test_ethernet_cfg.c
 * @author  foxBMS Team
 * @date    2025-07-24 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Test of the ethernet module configuration
 * @details Tests the exported network configuration tables of ethernet_cfg.c
 *
 */

/*========== Includes =======================================================*/
#include "unity.h"

#include "ethernet_cfg.h"

/*========== Unit Testing Framework Directives ==============================*/
TEST_SOURCE_FILE("ethernet_cfg.c")

/*========== Definitions and Implementations for Unit Test ==================*/

/*========== Setup and Teardown =============================================*/
void setUp(void) {
}

void tearDown(void) {
}

/*========== Test Cases =====================================================*/

/**
 * @brief   The two address-length macros bound the two address tables.
 * @details ethernet_cfg.h:65 and :68. Asserted as literals so that a wrong
 *          value in the header cannot pass this test.
 */
/* cspell:disable-next-line */
void testEthernetAddressLengthsAreSixAndFour(void) {
    /* ETH_HARDWARE_ADDRESS_LENGTH (6u)  ethernet_cfg.h:65 */
    TEST_ASSERT_EQUAL_UINT8(6u, (uint8_t)ETH_HARDWARE_ADDRESS_LENGTH);
    /* ETH_IP_ADDRESS_LENGTH (4u)  ethernet_cfg.h:68 */
    TEST_ASSERT_EQUAL_UINT8(4u, (uint8_t)ETH_IP_ADDRESS_LENGTH);

    /* Both lengths are complete types, so the extents are observable here and
     * are not merely the macro values repeated. */
    TEST_ASSERT_EQUAL_UINT32(6u, (uint32_t)sizeof(eth_emacAddress));
    TEST_ASSERT_EQUAL_UINT32(4u, (uint32_t)sizeof(eth_ipAddress));
}

/**
 * @brief   eth_emacAddress is the station's hardware (MAC) address.
 * @details ethernet_cfg.c:65 initialises all six bytes:
 *            :65  {0x0u, 0x08u, 0xEEu, 0x03u, 0xA6u, 0x6Cu}
 *          The first octet 0x00 marks a unicast address (the two lowest bits
 *          of the first octet are the I/G and U/L bits). Cited as literals.
 */
/* cspell:disable-next-line */
void testEthernetEmacAddressIsTheConfiguredSixOctets(void) {
    TEST_ASSERT_EQUAL_UINT8(0x00u, eth_emacAddress[0]);
    TEST_ASSERT_EQUAL_UINT8(0x08u, eth_emacAddress[1]);
    TEST_ASSERT_EQUAL_UINT8(0xEEu, eth_emacAddress[2]);
    TEST_ASSERT_EQUAL_UINT8(0x03u, eth_emacAddress[3]);
    TEST_ASSERT_EQUAL_UINT8(0xA6u, eth_emacAddress[4]);
    TEST_ASSERT_EQUAL_UINT8(0x6Cu, eth_emacAddress[5]);
}

/**
 * @brief   eth_ipAddress is this interface's own IPv4 address.
 * @details ethernet_cfg.c:66 initialises all four octets:
 *            :66  {169u, 254u, 107u, 24u}
 *          169.254.0.0/16 is the link-local block, so this is a link-local
 *          address rather than a routable one.
 */
/* cspell:disable-next-line */
void testEthernetIpAddressIsTheConfiguredFourOctets(void) {
    TEST_ASSERT_EQUAL_UINT8(169u, eth_ipAddress[0]);
    TEST_ASSERT_EQUAL_UINT8(254u, eth_ipAddress[1]);
    TEST_ASSERT_EQUAL_UINT8(107u, eth_ipAddress[2]);
    TEST_ASSERT_EQUAL_UINT8(24u, eth_ipAddress[3]);
}

/**
 * @brief   eth_netMask is the IPv4 subnet mask.
 * @details ethernet_cfg.c:67 initialises all four octets:
 *            :67  {255u, 255u, 0u, 0u}
 *          That is a /16 prefix, which is what makes the address at :66 fall
 *          inside the link-local block. The length 4u is on the same line.
 */
/* cspell:disable-next-line */
void testEthernetNetMaskIsSixteenBitPrefix(void) {
    TEST_ASSERT_EQUAL_UINT8(255u, eth_netMask[0]);
    TEST_ASSERT_EQUAL_UINT8(255u, eth_netMask[1]);
    TEST_ASSERT_EQUAL_UINT8(0u, eth_netMask[2]);
    TEST_ASSERT_EQUAL_UINT8(0u, eth_netMask[3]);
}

/**
 * @brief   eth_gatewayAddress is the default gateway.
 * @details ethernet_cfg.c:68 initialises all four octets:
 *            :68  {169u, 254u, 107u, 1u}
 *          It shares the /16 prefix with eth_ipAddress, so both octets 0 and 1
 *          below are equal on purpose and are asserted separately so that a
 *          change to only one of them is caught.
 */
/* cspell:disable-next-line */
void testEthernetGatewayAddressIsTheConfiguredFourOctets(void) {
    TEST_ASSERT_EQUAL_UINT8(169u, eth_gatewayAddress[0]);
    TEST_ASSERT_EQUAL_UINT8(254u, eth_gatewayAddress[1]);
    TEST_ASSERT_EQUAL_UINT8(107u, eth_gatewayAddress[2]);
    TEST_ASSERT_EQUAL_UINT8(1u, eth_gatewayAddress[3]);
}

/**
 * @brief   eth_dnsServerAddress is all zero: no DNS server is configured.
 * @details ethernet_cfg.c:69 initialises all four octets:
 *            :69  {0u, 0u, 0u, 0u}
 *          Asserting the zeros is not vacuous here: an all-zero table and an
 *          uninitialised table read identically through `extern`, so the only
 *          evidence that this table is deliberately zeroed is that it was
 *          written down. This test is that evidence.
 */
/* cspell:disable-next-line */
void testEthernetDnsServerAddressIsAllZero(void) {
    TEST_ASSERT_EQUAL_UINT8(0u, eth_dnsServerAddress[0]);
    TEST_ASSERT_EQUAL_UINT8(0u, eth_dnsServerAddress[1]);
    TEST_ASSERT_EQUAL_UINT8(0u, eth_dnsServerAddress[2]);
    TEST_ASSERT_EQUAL_UINT8(0u, eth_dnsServerAddress[3]);
}

/**
 * @brief   The station's address and the gateway lie in the same subnet, share
 *          the first three octets, and differ in the host octet.
 * @details Cross-checks the two tables at ethernet_cfg.c:66 and :68 rather than
 *          restating either. The configured pair is
 *            station  ethernet_cfg.c:66  169. 254. 107.  24
 *            gateway  ethernet_cfg.c:68  169. 254. 107.   1
 *          so octets 0..2 are equal and octet 3 differs. Octet 2 being equal
 *          places both hosts on the same /24, which is narrower than the /16
 *          the mask at :67 declares; that is a property of the shipped
 *          configuration and is asserted here as written rather than judged.
 *          Each octet is compared separately so that a change to only one of
 *          them is caught.
 */
/* cspell:disable-next-line */
void testEthernetGatewaySharesSubnetWithStationAddressAndDiffersInHostOctet(void) {
    /* octets 0,1,2 - same /24 subnet on both sides */
    TEST_ASSERT_EQUAL_UINT8(eth_ipAddress[0], eth_gatewayAddress[0]);
    TEST_ASSERT_EQUAL_UINT8(eth_ipAddress[1], eth_gatewayAddress[1]);
    TEST_ASSERT_EQUAL_UINT8(eth_ipAddress[2], eth_gatewayAddress[2]);
    /* octet 3 - the two hosts are distinct, so this one must differ.
     * ethernet_cfg.c:66 gives 24 and :68 gives 1. */
    TEST_ASSERT_EQUAL_UINT8(24u, eth_ipAddress[3]);
    TEST_ASSERT_EQUAL_UINT8(1u, eth_gatewayAddress[3]);
    TEST_ASSERT_NOT_EQUAL(eth_ipAddress[3], eth_gatewayAddress[3]);
}
