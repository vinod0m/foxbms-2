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
 * @file    test_sys_mon_cfg.c
 * @author  foxBMS Team
 * @date    2020-04-02 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Tests for the sys_mon_cfg
 * @details Tests for existing dummy callback
 *
 */

/*========== Includes =======================================================*/
#include "unity.h"

#include "sys_mon_cfg.h"

/*========== Unit Testing Framework Directives ==============================*/
TEST_INCLUDE_PATH("../../src/app/driver/config")
TEST_INCLUDE_PATH("../../src/app/driver/fram")
TEST_INCLUDE_PATH("../../src/app/task/config")

/*========== Definitions and Implementations for Unit Test ==================*/

/*========== Setup and Teardown =============================================*/
void setUp(void) {
}

void tearDown(void) {
}

/*========== Test Cases =====================================================*/

/**
 * @brief   sysm_ch_cfg is the per-task watchdog configuration: for each
 *          monitored task it fixes how late SYSM_Notify may be called before
 *          the task is declared dead, and what happens when it is.
 * @details sys_mon_cfg.c:75-111 declares five entries, one per
 *          SYSM_TASK_ID_e value except SYSM_TASK_ID_MAX. The values, cited to
 *          the initialiser lines and to the FTSK_* macros they come from
 *          (ftask_cfg.h):
 *            :76  SYSM_TASK_ID_ENGINE               ENABLED  cycle 1   jitter 1
 *                 FTSK_TASK_ENGINE_CYCLE_TIME (1u) ftask_cfg.h:76
 *                 FTSK_TASK_ENGINE_MAXIMUM_JITTER (1u) ftask_cfg.h:79
 *            :83  SYSM_TASK_ID_CYCLIC_1ms           ENABLED  cycle 1   jitter 1
 *                 FTSK_TASK_CYCLIC_1MS_CYCLE_TIME (1u) ftask_cfg.h:94
 *                 FTSK_TASK_CYCLIC_1MS_MAXIMUM_JITTER (1u) ftask_cfg.h:97
 *            :90  SYSM_TASK_ID_CYCLIC_10ms          ENABLED  cycle 10  jitter 2
 *                 FTSK_TASK_CYCLIC_10MS_CYCLE_TIME (10u) ftask_cfg.h:112
 *                 FTSK_TASK_CYCLIC_10MS_MAXIMUM_JITTER (2u) ftask_cfg.h:115
 *            :97  SYSM_TASK_ID_CYCLIC_100ms         ENABLED  cycle 100 jitter 5
 *                 FTSK_TASK_CYCLIC_100MS_CYCLE_TIME (100u) ftask_cfg.h:130
 *                 FTSK_TASK_CYCLIC_100MS_MAXIMUM_JITTER (5u) ftask_cfg.h:133
 *            :104 SYSM_TASK_ID_CYCLIC_ALGORITHM_100ms ENABLED cycle 100 jitter 5
 *                 FTSK_TASK_CYCLIC_ALGORITHM_100MS_CYCLE_TIME (100u) ftask_cfg.h:148
 *                 FTSK_TASK_CYCLIC_ALGORITHM_100MS_MAXIMUM_JITTER (5u) ftask_cfg.h:151
 *          Every entry also carries SYSM_RECORDING_ENABLED and
 *          SYSM_HANDLING_SWITCH_OFF_CONTACTOR, which are the first and second
 *          enumerators of their enums (sys_mon_cfg.h:80-88 and :90-94).
 *          The values are written as literals so that a wrong macro cannot pass.
 */
/* cspell:disable-next-line */
void testSysMonConfigurationEntries(void) {
    /* ======= Assertion tests ============================================= */
    /* sysm_ch_cfg is declared `extern SYSM_MONITORING_CFG_s sysm_ch_cfg[];`
     * (sys_mon_cfg.h:109), an incomplete array type, so its extent cannot be
     * taken with sizeof() in the test. The count that the source ties the table
     * to is SYSM_TASK_ID_MAX, which the source itself asserts against
     * sizeof(sysm_ch_cfg)/sizeof(SYSM_MONITORING_CFG_s) at sys_mon_cfg.c:114-116.
     * SYSM_TASK_ID_MAX is the sixth enumerator of SYSM_TASK_ID_e, so it counts 5. */
    TEST_ASSERT_EQUAL_INT32(5, (int32_t)SYSM_TASK_ID_MAX);

    /* 0: engine task, 1ms deadline */
    TEST_ASSERT_EQUAL_INT32(0, (int32_t)sysm_ch_cfg[0].id);
    TEST_ASSERT_EQUAL_INT32(0, (int32_t)sysm_ch_cfg[0].enable);
    TEST_ASSERT_EQUAL_UINT8(1u, sysm_ch_cfg[0].cycleTime);
    TEST_ASSERT_EQUAL_UINT8(1u, sysm_ch_cfg[0].maxJitter);
    TEST_ASSERT_EQUAL_INT32(0, (int32_t)sysm_ch_cfg[0].enableRecording);
    TEST_ASSERT_EQUAL_INT32(1, (int32_t)sysm_ch_cfg[0].handlingType);

    /* 1: cyclic 1ms task, 1ms deadline */
    TEST_ASSERT_EQUAL_INT32(1, (int32_t)sysm_ch_cfg[1].id);
    TEST_ASSERT_EQUAL_INT32(0, (int32_t)sysm_ch_cfg[1].enable);
    TEST_ASSERT_EQUAL_UINT8(1u, sysm_ch_cfg[1].cycleTime);
    TEST_ASSERT_EQUAL_UINT8(1u, sysm_ch_cfg[1].maxJitter);
    TEST_ASSERT_EQUAL_INT32(0, (int32_t)sysm_ch_cfg[1].enableRecording);
    TEST_ASSERT_EQUAL_INT32(1, (int32_t)sysm_ch_cfg[1].handlingType);

    /* 2: cyclic 10ms task, 10ms deadline */
    TEST_ASSERT_EQUAL_INT32(2, (int32_t)sysm_ch_cfg[2].id);
    TEST_ASSERT_EQUAL_INT32(0, (int32_t)sysm_ch_cfg[2].enable);
    TEST_ASSERT_EQUAL_UINT8(10u, sysm_ch_cfg[2].cycleTime);
    TEST_ASSERT_EQUAL_UINT8(2u, sysm_ch_cfg[2].maxJitter);
    TEST_ASSERT_EQUAL_INT32(0, (int32_t)sysm_ch_cfg[2].enableRecording);
    TEST_ASSERT_EQUAL_INT32(1, (int32_t)sysm_ch_cfg[2].handlingType);

    /* 3: cyclic 100ms task, 100ms deadline */
    TEST_ASSERT_EQUAL_INT32(3, (int32_t)sysm_ch_cfg[3].id);
    TEST_ASSERT_EQUAL_INT32(0, (int32_t)sysm_ch_cfg[3].enable);
    TEST_ASSERT_EQUAL_UINT8(100u, sysm_ch_cfg[3].cycleTime);
    TEST_ASSERT_EQUAL_UINT8(5u, sysm_ch_cfg[3].maxJitter);
    TEST_ASSERT_EQUAL_INT32(0, (int32_t)sysm_ch_cfg[3].enableRecording);
    TEST_ASSERT_EQUAL_INT32(1, (int32_t)sysm_ch_cfg[3].handlingType);

    /* 4: cyclic algorithm 100ms task, 100ms deadline */
    TEST_ASSERT_EQUAL_INT32(4, (int32_t)sysm_ch_cfg[4].id);
    TEST_ASSERT_EQUAL_INT32(0, (int32_t)sysm_ch_cfg[4].enable);
    TEST_ASSERT_EQUAL_UINT8(100u, sysm_ch_cfg[4].cycleTime);
    TEST_ASSERT_EQUAL_UINT8(5u, sysm_ch_cfg[4].maxJitter);
    TEST_ASSERT_EQUAL_INT32(0, (int32_t)sysm_ch_cfg[4].enableRecording);
    TEST_ASSERT_EQUAL_INT32(1, (int32_t)sysm_ch_cfg[4].handlingType);
}

/**
 * @brief   The source states the table size as a static assertion
 *          (sys_mon_cfg.c:114-116) that the entry count equals SYSM_TASK_ID_MAX.
 *          The compiler already enforces it; what the test adds is that every
 *          one of those SYSM_TASK_ID_MAX entries exists, carries a distinct id
 *          drawn from the same enum, and is enabled. A table that declared five
 *          entries but left one disabled, or gave two entries the same id, would
 *          satisfy the static assertion and still mis-monitor a task.
 * @details The loop is bounded by SYSM_TASK_ID_MAX (5), not by a sizeof of the
 *          incomplete array type, so it indexes exactly the entries the source
 *          promises. Entry 0 carries SYSM_TASK_ID_ENGINE and entry 4 carries
 *          SYSM_TASK_ID_CYCLIC_ALGORITHM_100ms (sys_mon_cfg.c:76 and :104), and
 *          the enum at sys_mon_cfg.h lists them in that order, so entry i must
 *          carry enumerator i.
 */
/* cspell:disable-next-line */
void testSysMonConfigurationCoversEveryTaskIdOnce(void) {
    /* ======= Assertion tests ============================================= */
    bool seen[5];
    for (uint32_t i = 0u; i < (uint32_t)SYSM_TASK_ID_MAX; i++) {
        seen[i] = false;
    }
    for (uint32_t i = 0u; i < (uint32_t)SYSM_TASK_ID_MAX; i++) {
        const int32_t id = (int32_t)sysm_ch_cfg[i].id;
        TEST_ASSERT_TRUE_MESSAGE((id >= 0) && (id < (int32_t)SYSM_TASK_ID_MAX),
                                 "every channel must name a valid SYSM_TASK_ID_e value");
        TEST_ASSERT_FALSE_MESSAGE(seen[id],
                                  "no two channels may monitor the same task id");
        seen[id] = true;
        /* every configured task is monitored, i.e. SYSM_ENABLED (first
         * enumerator of SYSM_ACTIVATE_e, sys_mon_cfg.h:97) */
        TEST_ASSERT_EQUAL_INT32_MESSAGE(0, (int32_t)sysm_ch_cfg[i].enable,
                                        "every channel must be enabled");
    }
}

/**
 * @brief   Every channel's error callback must be present and must be the same
 *          function. A null callback would be dereferenced by the monitoring
 *          code on the first timeout; a channel wired to a different function
 *          would run a handler belonging to another task.
 * @details sys_mon_cfg.c:82, 89, 96, 103 and 110 each set the seventh field to
 *          SYSM_DummyCallback, a file-static function (sys_mon_cfg.c:71, 124).
 *
 *          The pointer CANNOT be compared against TEST_SYSM_DummyCallback: that
 *          symbol is a separate exported wrapper which merely calls the static
 *          one (sys_mon_cfg.c:134-136), so the two have different addresses and
 *          the comparison is not merely weaker than hoped, it is false. What is
 *          assertable from outside is that all five channels share one callback
 *          and that it is not null.
 */
void testSysMonConfigurationCallbacks(void) {
    /* ======= Assertion tests ============================================= */
    for (uint32_t i = 0u; i < (uint32_t)SYSM_TASK_ID_MAX; i++) {
        TEST_ASSERT_NOT_NULL_MESSAGE(sysm_ch_cfg[i].callbackFunction,
                                     "every monitored task needs an error callback");
    }
    /* all five channels are wired to the same handler, and it is the first
     * channel's handler */
    for (uint32_t i = 1u; i < (uint32_t)SYSM_TASK_ID_MAX; i++) {
        TEST_ASSERT_TRUE_MESSAGE(
            sysm_ch_cfg[i].callbackFunction == sysm_ch_cfg[0].callbackFunction,
            "every channel must be wired to the same dummy error callback");
    }
}

/**
 * @brief   The dummy callback is exported for tests precisely so it can be
 *          called. It is the seventh field's target, so calling it exercises
 *          the same function the monitoring code would reach on a timeout.
 * @details sys_mon_cfg.c:134-136 makes TEST_SYSM_DummyCallback call
 *          SYSM_DummyCallback (sys_mon_cfg.c:124-128), which is empty. There is
 *          no return value and no state to assert on, so what is asserted here
 *          is that the call is accepted and the test survives it -- a null or
 *          wild callback pointer would trap instead. The channel configuration
 *          itself is asserted in the cases above.
 */
void testSysMonDummyCallbackIsCallable(void) {
    /* ======= Assertion tests ============================================= */
    SYSM_TASK_ID_e taskId = SYSM_TASK_ID_ENGINE;
    TEST_SYSM_DummyCallback(taskId);
    /* the callback takes the task id and returns nothing; after the call the
     * configuration is unchanged, which is the only externally visible effect */
    TEST_ASSERT_EQUAL_INT32(0, (int32_t)sysm_ch_cfg[0].id);
}
