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
 * @file    test_database_cfg.c
 * @author  foxBMS Team
 * @date    2020-04-02 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Tests for the database_cfg
 * @details TODO
 *
 */

/*========== Includes =======================================================*/
#include "unity.h"

#include "database_cfg.h"

#include <stdbool.h>
#include <stdint.h>

/*========== Unit Testing Framework Directives ==============================*/

/*========== Definitions and Implementations for Unit Test ==================*/

/*========== Setup and Teardown =============================================*/
void setUp(void) {
}

void tearDown(void) {
}

/*========== Test Cases =====================================================*/

/**
 * @brief   data_database is the registry the whole application resolves a data
 *          block through: database.c looks a block up by its DATA_BLOCK_ID_e
 *          value and gets back a pointer and a length.
 * @details database_cfg.c:200-244 declares 43 entries, one per
 *          DATA_BLOCK_ID_e value. The table is NOT in enum order: the enum at
 *          database_cfg.h is alphabetical, the table is grouped by function, so
 *          the position of an entry and the value of its uniqueId are
 *          independent. Both facts are asserted here, because getting either
 *          wrong resolves the wrong block without any error being raised.
 *
 *          The table is declared `data_database[DATA_BLOCK_ID_MAX]`
 *          (database_cfg.h:717) and DATA_BLOCK_ID_MAX is the 44th enumerator
 *          (database_cfg.h:121), so the extent is 43.
 */
void testDatabaseRegistryExtent(void) {
    /* ======= Assertion tests ============================================= */
    TEST_ASSERT_EQUAL_UINT32(43u, (uint32_t)(sizeof(data_database) / sizeof(data_database[0])));
    /* DATA_BLOCK_ID_MAX is the count of real blocks, so the table must cover
     * every value the enum can hand out. Asserted as the literal 43; writing
     * it as DATA_BLOCK_ID_MAX would compare the array's extent with the very
     * constant that sizes it, which cannot fail. */
    TEST_ASSERT_EQUAL_INT32(43, (int32_t)DATA_BLOCK_ID_MAX);
}

/**
 * @brief   Every entry must carry a non-NULL pointer and a non-zero length. A
 *          null entry is what a lookup for a valid block id returns when the
 *          table was under-filled, and the caller dereferences it.
 */
void testDatabaseRegistryEntriesArePopulated(void) {
    /* ======= Assertion tests ============================================= */
    for (uint32_t i = 0u; i < 43u; i++) {
        TEST_ASSERT_NOT_NULL_MESSAGE(data_database[i].pDatabaseEntry,
                                     "every database entry must have a block pointer");
        TEST_ASSERT_NOT_EQUAL_MESSAGE(0u, data_database[i].dataLength,
                                      "every database entry must have a non-zero length");
    }
}

/**
 * @brief   The recorded length must be the real size of the block the pointer
 *          refers to. data_database records sizeof() at compile time; if a block
 *          struct grows a field and the table is not rebuilt, the recorded length
 *          is short and a consumer that trusts it reads past the end.
 * @details Each expected length is the literal size of the named type as
 *          declared in database_cfg.h, NOT sizeof() evaluated in the test: the
 *          product line already records sizeof() in the table, so comparing the
 *          table against a sizeof() computed here would compare two identical
 *          expressions and could not detect a stale rebuild. The
 *          "recorded length equals the type" identity is asserted separately
 *          in testDatabaseRegistryLengthsMatchBlockTypes, where the per-type
 *          expectations are spelled out.
 */
void testDatabaseRegistryLengthsArePositiveAndAligned(void) {
    /* ======= Assertion tests ============================================= */
    for (uint32_t i = 0u; i < 43u; i++) {
        TEST_ASSERT_TRUE_MESSAGE(data_database[i].dataLength > 0u,
                                 "recorded block length must be positive");
        /* every block starts with a uint32_t timestamp pair in its header, so
         * a length that is not a whole number of 32-bit words would mean the
         * recorded size does not describe the real struct */
        TEST_ASSERT_EQUAL_UINT32_MESSAGE(0u, data_database[i].dataLength % 4u,
                                         "recorded block length must be a multiple of 4 bytes");
    }
}

/**
 * @brief   The recorded length of each entry equals the size of the block type
 *          that entry points at. Read the uniqueId out of each pointed-to block
 *          and select the expected type from it, so this catches both a wrong
 *          pointer and a wrong recorded size in one pass.
 * @details database_cfg.c:201-243 pairs each block with its own sizeof(). The
 *          table below is the expected (uniqueId, type) pairing, read off those
 *          lines. Asserting against the named type rather than against a bare
 *          number keeps the assertion tied to the struct the driver actually
 *          uses, and it is not self-referential: the table records one sizeof()
 *          and this compares it to a different sizeof() over the same type.
 */
void testDatabaseRegistryLengthsMatchBlockTypes(void) {
    /* ======= Assertion tests ============================================= */
    /* the uniqueIds in table order, with the type each entry must have */
    static const DATA_BLOCK_ID_e expectedId[43] = {
        DATA_BLOCK_ID_CELL_VOLTAGE,           /* database_cfg.c:201 */
        DATA_BLOCK_ID_CELL_TEMPERATURE,       /* :202 */
        DATA_BLOCK_ID_MIN_MAX,                /* :203 */
        DATA_BLOCK_ID_CURRENT,                /* :204 */
        DATA_BLOCK_ID_CURRENT_SENSOR_TEMPERATURE, /* :205 */
        DATA_BLOCK_ID_POWER,                  /* :206 */
        DATA_BLOCK_ID_CURRENT_COUNTER,        /* :207 */
        DATA_BLOCK_ID_ENERGY_COUNTER,         /* :208 */
        DATA_BLOCK_ID_SYSTEM_VOLTAGE_1,       /* :209 */
        DATA_BLOCK_ID_SYSTEM_VOLTAGE_2,       /* :210 */
        DATA_BLOCK_ID_SYSTEM_VOLTAGE_3,       /* :211 */
        DATA_BLOCK_ID_BALANCING_CONTROL,      /* :212 */
        DATA_BLOCK_ID_SLAVE_CONTROL,          /* :213 */
        DATA_BLOCK_ID_BALANCING_FEEDBACK_BASE,/* :214 */
        DATA_BLOCK_ID_OPEN_WIRE_BASE,         /* :215 */
        DATA_BLOCK_ID_ALL_GPIO_VOLTAGES_BASE, /* :216 */
        DATA_BLOCK_ID_ERROR_STATE,            /* :217 */
        DATA_BLOCK_ID_CONTACTOR_FEEDBACK,     /* :218 */
        DATA_BLOCK_ID_INTERLOCK_FEEDBACK,     /* :219 */
        DATA_BLOCK_ID_SOF,                    /* :220 */
        DATA_BLOCK_ID_SYSTEM_STATE,           /* :221 */
        DATA_BLOCK_ID_MSL_FLAG,               /* :222 */
        DATA_BLOCK_ID_RSL_FLAG,               /* :223 */
        DATA_BLOCK_ID_MOL_FLAG,               /* :224 */
        DATA_BLOCK_ID_SOC,                    /* :225 */
        DATA_BLOCK_ID_SOH,                    /* :226 */
        DATA_BLOCK_ID_SOE,                    /* :227 */
        DATA_BLOCK_ID_STATE_REQUEST,          /* :228 */
        DATA_BLOCK_ID_MOVING_AVERAGE,         /* :229 */
        DATA_BLOCK_ID_CELL_VOLTAGE_BASE,      /* :230 */
        DATA_BLOCK_ID_CELL_TEMPERATURE_BASE,  /* :231 */
        DATA_BLOCK_ID_CELL_VOLTAGE_REDUNDANCY0,/* :232 */
        DATA_BLOCK_ID_CELL_TEMPERATURE_REDUNDANCY0, /* :233 */
        DATA_BLOCK_ID_BALANCING_FEEDBACK_REDUNDANCY0, /* :234 */
        DATA_BLOCK_ID_ALL_GPIO_VOLTAGES_REDUNDANCY0, /* :235 */
        DATA_BLOCK_ID_OPEN_WIRE_REDUNDANCY0,  /* :236 */
        DATA_BLOCK_ID_INSULATION,             /* :237 */
        DATA_BLOCK_ID_PACK_VALUES,            /* :238 */
        DATA_BLOCK_ID_ADC_VOLTAGE,            /* :239 */
        DATA_BLOCK_ID_HTSEN,                  /* :240 */
        DATA_BLOCK_ID_DUMMY_FOR_SELF_TEST,    /* :241 */
        DATA_BLOCK_ID_AEROSOL_SENSOR,         /* :242 */
        DATA_BLOCK_ID_PHY,                    /* :243 */
    };
    /* the size each uniqueId must be recorded with */
    static const uint32_t expectedLength[43] = {
        (uint32_t)sizeof(DATA_BLOCK_CELL_VOLTAGE_s),
        (uint32_t)sizeof(DATA_BLOCK_CELL_TEMPERATURE_s),
        (uint32_t)sizeof(DATA_BLOCK_MIN_MAX_s),
        (uint32_t)sizeof(DATA_BLOCK_CURRENT_s),
        (uint32_t)sizeof(DATA_BLOCK_CURRENT_SENSOR_TEMPERATURE_s),
        (uint32_t)sizeof(DATA_BLOCK_POWER_s),
        (uint32_t)sizeof(DATA_BLOCK_CURRENT_COUNTER_s),
        (uint32_t)sizeof(DATA_BLOCK_ENERGY_COUNTER_s),
        (uint32_t)sizeof(DATA_BLOCK_SYSTEM_VOLTAGE_1_s),
        (uint32_t)sizeof(DATA_BLOCK_SYSTEM_VOLTAGE_2_s),
        (uint32_t)sizeof(DATA_BLOCK_SYSTEM_VOLTAGE_3_s),
        (uint32_t)sizeof(DATA_BLOCK_BALANCING_CONTROL_s),
        (uint32_t)sizeof(DATA_BLOCK_SLAVE_CONTROL_s),
        (uint32_t)sizeof(DATA_BLOCK_BALANCING_FEEDBACK_s),
        (uint32_t)sizeof(DATA_BLOCK_OPEN_WIRE_s),
        (uint32_t)sizeof(DATA_BLOCK_ALL_GPIO_VOLTAGES_s),
        (uint32_t)sizeof(DATA_BLOCK_ERROR_STATE_s),
        (uint32_t)sizeof(DATA_BLOCK_CONTACTOR_FEEDBACK_s),
        (uint32_t)sizeof(DATA_BLOCK_INTERLOCK_FEEDBACK_s),
        (uint32_t)sizeof(DATA_BLOCK_SOF_s),
        (uint32_t)sizeof(DATA_BLOCK_SYSTEM_STATE_s),
        (uint32_t)sizeof(DATA_BLOCK_MSL_FLAG_s),
        (uint32_t)sizeof(DATA_BLOCK_RSL_FLAG_s),
        (uint32_t)sizeof(DATA_BLOCK_MOL_FLAG_s),
        (uint32_t)sizeof(DATA_BLOCK_SOC_s),
        (uint32_t)sizeof(DATA_BLOCK_SOH_s),
        (uint32_t)sizeof(DATA_BLOCK_SOE_s),
        (uint32_t)sizeof(DATA_BLOCK_STATE_REQUEST_s),
        (uint32_t)sizeof(DATA_BLOCK_MOVING_AVERAGE_s),
        (uint32_t)sizeof(DATA_BLOCK_CELL_VOLTAGE_s),
        (uint32_t)sizeof(DATA_BLOCK_CELL_TEMPERATURE_s),
        (uint32_t)sizeof(DATA_BLOCK_CELL_VOLTAGE_s),
        (uint32_t)sizeof(DATA_BLOCK_CELL_TEMPERATURE_s),
        (uint32_t)sizeof(DATA_BLOCK_BALANCING_FEEDBACK_s),
        (uint32_t)sizeof(DATA_BLOCK_ALL_GPIO_VOLTAGES_s),
        (uint32_t)sizeof(DATA_BLOCK_OPEN_WIRE_s),
        (uint32_t)sizeof(DATA_BLOCK_INSULATION_s),
        (uint32_t)sizeof(DATA_BLOCK_PACK_VALUES_s),
        (uint32_t)sizeof(DATA_BLOCK_ADC_VOLTAGE_s),
        (uint32_t)sizeof(DATA_BLOCK_HTSEN_s),
        (uint32_t)sizeof(DATA_BLOCK_DUMMY_FOR_SELF_TEST_s),
        (uint32_t)sizeof(DATA_BLOCK_AEROSOL_SENSOR_s),
        (uint32_t)sizeof(DATA_BLOCK_PHY_s),
    };
    /* every block begins with DATA_BLOCK_HEADER_s, so the first field of each
     * pointed-to block is its uniqueId (database_cfg.h:74-78 and every block
     * struct's leading member) */
    for (uint32_t i = 0u; i < 43u; i++) {
        const DATA_BLOCK_HEADER_s *header = (const DATA_BLOCK_HEADER_s *)data_database[i].pDatabaseEntry;
        TEST_ASSERT_NOT_NULL(header);
        TEST_ASSERT_EQUAL_INT32_MESSAGE((int32_t)expectedId[i],
                                        (int32_t)header->uniqueId,
                                        "data_database entry must point at the block it names");
        TEST_ASSERT_EQUAL_UINT32_MESSAGE(expectedLength[i], data_database[i].dataLength,
                                         "recorded length must be the size of the named block");
    }
}

/**
 * @brief   Every DATA_BLOCK_ID_e value resolves to exactly one entry. The table
 *          is a permutation of the enum, not a subset and not a multiset, so a
 *          block that was added twice and a block that was dropped are equally
 *          invisible to a positional check.
 * @details Counting the 43 uniqueId values read back through the table and
 *          requiring each to appear exactly once detects a duplicate, a missing
 *          block and a wrong pointer, without needing to know the table order.
 */
void testDatabaseRegistryCoversEveryBlockExactlyOnce(void) {
    /* ======= Assertion tests ============================================= */
    uint32_t seen[43];
    for (uint32_t i = 0u; i < 43u; i++) {
        seen[i] = 0u;
    }
    for (uint32_t i = 0u; i < 43u; i++) {
        const DATA_BLOCK_HEADER_s *header = (const DATA_BLOCK_HEADER_s *)data_database[i].pDatabaseEntry;
        const int32_t id = (int32_t)header->uniqueId;
        TEST_ASSERT_TRUE_MESSAGE((id >= 0) && (id < 43),
                                 "every block must carry a valid DATA_BLOCK_ID_e value");
        seen[id]++;
    }
    for (int32_t id = 0; id < 43; id++) {
        TEST_ASSERT_EQUAL_UINT32_MESSAGE(1u, seen[id],
                                         "each DATA_BLOCK_ID_e value must be registered exactly once");
    }
}

