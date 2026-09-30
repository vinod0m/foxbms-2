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
 * @file    test_os_freertos_cache_enabled.c
 * @author  foxBMS Team
 * @date    2025-04-09 (date of creation)
 * @updated 2026-04-20 (date of last update)
 * @version v1.11.0
 * @ingroup UNIT_TEST_IMPLEMENTATION
 * @prefix  TEST
 *
 * @brief   Test of the OS implementation for FreeRTOS
 * @details Test functions:
 *          - testOS_InitializeScheduler
 *          - testOS_StartScheduler
 *          - testVApplicationGetIdleTaskMemory
 *          - testVApplicationGetTimerTaskMemory
 *          - testVApplicationIdleHook
 *          - testVApplicationStackOverflowHook
 *          - testOSGetTickCount
 *          - testOSDelayTask
 *          - testOSDelayTaskUntil
 *          - testOSMarkTaskAsRequiringFpuContext
 *          - testOSWaitForNotification
 *          - testOSNotifyFromIsr
 *          - testOSWaitForNotificationIndexed
 *          - testOSNotifyIndexedFromIsr
 *          - testOSNotifyGive
 *          - testOSNotifyGiveFromIsr
 *          - testOSNotifyTake
 *          - testOSClearNotificationIndexed
 *          - testOSReceiveFromQueue
 *          - testOSSendToBackOfQueue
 *          - testOSSendToBackOfQueueFromIsr
 *          - testOSSuspendTask
 *          - testOSResumeTask
 *          - testOSGetNumberOfStoredMessagesInQueue
 *          - testOSSemaphoreGive
 *          - testOSSemaphoreGiveFromIsr
 *          - testOSSemaphoreTake
 */

/*========== Includes =======================================================*/
#include "unity.h"
#include "MockHL_sys_core.h"
#include "Mockcan_cbs_tx_f_crash-dump.h"
#include "Mockftask.h"
#include "Mockftask_cfg.h"
#include "Mockportmacro.h"
#include "Mockqueue.h"
#include "Mockrtc.h"
#include "Mocktask.h"

#include "os.h"
#include "test_assert_helper.h"

/*========== Unit Testing Framework Directives ==============================*/
TEST_SOURCE_FILE("os_freertos.c")

TEST_INCLUDE_PATH("../../src/app/driver/can/cbs")
TEST_INCLUDE_PATH("../../src/app/driver/can/cbs/tx-async")
TEST_INCLUDE_PATH("../../src/app/driver/config")
TEST_INCLUDE_PATH("../../src/app/driver/rtc")
TEST_INCLUDE_PATH("../../src/app/task/config")
TEST_INCLUDE_PATH("../../src/app/task/ftask")

/*========== Definitions and Implementations for Unit Test ==================*/

/* src/app/task/os/os.h:89-:92 renames the three application-provided FreeRTOS
 * hooks under UNITY_UNIT_TEST, so that the linker does not see the product's
 * definition in os_freertos.c and CMock's definition of the same name in
 * Mocktask at the same time. The renames are macros, so the renamed entry
 * points need a prototype of their own; the comment at os.h:81-87 states the
 * intent. */
void TEST_vApplicationIdleHook(void);
void mock_vApplicationGetIdleTaskMemory(
    StaticTask_t **ppxIdleTaskTCBBuffer,
    StackType_t **ppxIdleTaskStackBuffer,
    configSTACK_DEPTH_TYPE *pulIdleTaskStackSize);
void mock_vApplicationStackOverflowHook(TaskHandle_t xTask, char *pcTaskName);

/* Real addresses handed to the OS layer as task, queue and semaphore handles.
 * The OS layer only forwards them and never dereferences them in any of the
 * entry points exercised here, so a single static object's address is a valid,
 * non-fabricated handle value. */
static uint32_t test_osHandleStorage;

#define TEST_OS_TASK_HANDLE ((TaskHandle_t)&test_osHandleStorage)
#define TEST_OS_QUEUE      ((OS_QUEUE)&test_osHandleStorage)
#define TEST_OS_SEMAPHORE  ((OS_SEMAPHORE_HANDLE)&test_osHandleStorage)

/*========== Setup and Teardown =============================================*/
/* CMock's own <fn>_CallCount() counts only the calls ROUTED THROUGH A
 * CALLBACK, so it reads 0 for a mock that was satisfied from an
 * <fn>_Expect() registration. Every count below is therefore taken in a
 * callback registered with AddCallback(), which - unlike Stub() - leaves
 * CMock's argument, ordering and call-count checks in place. */
static uint32_t test_osCountCacheEnable;
static uint32_t test_osCountCacheDisable;
static uint32_t test_osCountIdleHook;
static uint32_t test_osCountFpuContext;

static void cacheEnableCountCallback(int n) {
    (void)n;
    test_osCountCacheEnable++;
}
static void cacheDisableCountCallback(int n) {
    (void)n;
    test_osCountCacheDisable++;
}
static void FTSKRunUserCodeIdleCountCallback(int n) {
    (void)n;
    test_osCountIdleHook++;
}
static void vPortTaskUsesFPUCountCallback(int n) {
    (void)n;
    test_osCountFpuContext++;
}

void setUp(void) {
    test_osCountCacheEnable  = 0u;
    test_osCountCacheDisable = 0u;
    test_osCountIdleHook     = 0u;
    test_osCountFpuContext   = 0u;
    _cacheEnable__AddCallback(cacheEnableCountCallback);
    _cacheDisable__AddCallback(cacheDisableCountCallback);
    FTSK_RunUserCodeIdle_AddCallback(FTSKRunUserCodeIdleCountCallback);
    vPortTaskUsesFPU_AddCallback(vPortTaskUsesFPUCountCallback);
}

void tearDown(void) {
}

/*========== Test Cases =====================================================*/

/**
 * @brief   Testing extern function #OS_InitializeScheduler
 * @details The following cases need to be tested:
 *          - Argument validation:
 *            - none
 *          - Routine validation:
 *            - RT1/2: Cache is disabled (tested in 'test_os_freertos_cache_disabled.c')
 *            - RT2/2: Cache is enabled (tested in 'test_os_freertos_cache_enabled.c')
 */
void testOS_InitializeScheduler(void) {
    /* ======= Assertion tests ============================================= */
    /* none */

    /* ======= Routine tests =============================================== */

    /* ======= RT1/2: see test_os_freertos_cache_disabled.c */

    /* ======= RT2/2: Test implementation */
    _cacheEnable__Expect();

    /* ======= RT2/2: call function under test */
    OS_InitializeScheduler();

    /* ======= RT2/2: test output verification */
    /* os_freertos.c:78-79 takes the _cacheEnable_() branch because this
     * translation unit is compiled with OS_ENABLE_CACHE=true
     * (conf/unit/app_project_posix.yml, :/test_os_freertos_cache_enabled.c).
     * It must switch the cache on exactly once and must not also switch it
     * off. */
    TEST_ASSERT_EQUAL_UINT32(1u, test_osCountCacheEnable);
    TEST_ASSERT_EQUAL_UINT32(0u, test_osCountCacheDisable);
}

/** @brief   OS_StartScheduler() must not be allowed to return
 * @details os_freertos.c:85-89 starts the scheduler and then traps, because
 *          "this function should never return" (:87).
 */
void testOS_StartScheduler(void) {
    vTaskStartScheduler_Expect();
    TEST_ASSERT_FAIL_ASSERT(OS_StartScheduler());
}

/** @brief   vApplicationGetIdleTaskMemory() hands out the idle task's buffers
 * @details os_freertos.c:99-101 guards the three out parameters, :102-104
 *          writes the static TCB, the static stack and the stack depth
 *          OS_IDLE_TASK_STACK_SIZE.
 */
void testVApplicationGetIdleTaskMemory(void) {
    StaticTask_t           *pTcb   = NULL_PTR;
    StackType_t            *pStack = NULL_PTR;
    configSTACK_DEPTH_TYPE depth   = 0u;

    mock_vApplicationGetIdleTaskMemory(&pTcb, &pStack, &depth);

    /* the module owns both buffers, so it hands out its own addresses */
    TEST_ASSERT_NOT_NULL(pTcb);
    TEST_ASSERT_NOT_NULL(pStack);
    TEST_ASSERT_EQUAL_PTR(pStack, &pStack[0]);
    /* os_freertos.c:104, and the constant is OS_IDLE_TASK_STACK_SIZE
     * (src/app/task/os/os.h:74) */
    TEST_ASSERT_EQUAL_UINT32((uint32_t)OS_IDLE_TASK_STACK_SIZE, (uint32_t)depth);
}

/** @brief   vApplicationGetIdleTaskMemory() rejects every NULL out parameter
 * @details the three guards at os_freertos.c:99, :100 and :101.
 */
void testVApplicationGetIdleTaskMemoryRejectsNullPointers(void) {
    /* os_freertos.c:94 takes two pointers-to-pointers and one pointer */
    StaticTask_t            tcbStorage     = {0};
    StackType_t             stackStorage   = {0};
    configSTACK_DEPTH_TYPE  depthStorage   = 0u;
    StaticTask_t           *pTcbValue      = &tcbStorage;
    StackType_t            *pStackValue    = &stackStorage;
    configSTACK_DEPTH_TYPE *pDepth         = &depthStorage;

    /* os_freertos.c:99 */
    TEST_ASSERT_FAIL_ASSERT(mock_vApplicationGetIdleTaskMemory(NULL_PTR, &pStackValue, pDepth));
    /* os_freertos.c:100 */
    TEST_ASSERT_FAIL_ASSERT(mock_vApplicationGetIdleTaskMemory(&pTcbValue, NULL_PTR, pDepth));
    /* os_freertos.c:101 */
    TEST_ASSERT_FAIL_ASSERT(mock_vApplicationGetIdleTaskMemory(&pTcbValue, &pStackValue, NULL_PTR));
}

/** @brief   vApplicationGetTimerTaskMemory() reports the configured depth
 * @details os_freertos.c:121-123 writes the static TCB, the static stack and
 *          configTIMER_TASK_STACK_DEPTH.
 */
void testVApplicationGetTimerTaskMemory(void) {
    StaticTask_t           *pTcb   = NULL_PTR;
    StackType_t            *pStack = NULL_PTR;
    configSTACK_DEPTH_TYPE depth   = 0u;

    vApplicationGetTimerTaskMemory(&pTcb, &pStack, &depth);

    TEST_ASSERT_NOT_NULL(pTcb);
    TEST_ASSERT_NOT_NULL(pStack);
    TEST_ASSERT_EQUAL_PTR(pStack, &pStack[0]);
    /* os_freertos.c:123 */
    TEST_ASSERT_EQUAL_UINT32((uint32_t)configTIMER_TASK_STACK_DEPTH, (uint32_t)depth);
}

/** @brief   vApplicationIdleHook() runs the user idle code
 * @details os_freertos.c:127-129 makes exactly one call to
 *          FTSK_RunUserCodeIdle().
 */
void testVApplicationIdleHook(void) {
    FTSK_RunUserCodeIdle_Expect();
    TEST_vApplicationIdleHook();
    TEST_ASSERT_EQUAL_UINT32(1u, test_osCountIdleHook);
}

/** @brief   vApplicationStackOverflowHook() reports the overflow and traps
 * @details os_freertos.c:148 sends the stack-overflow crash dump and :149
 *          traps. The hook is reached from an interrupt context in the product,
 *          so it must never return.
 */
void testVApplicationStackOverflowHook(void) {
    CANTX_CrashDump_Expect(CANTX_FATAL_ERRORS_ACTIONS_STACK_OVERFLOW);
    TEST_ASSERT_FAIL_ASSERT(mock_vApplicationStackOverflowHook(TEST_OS_TASK_HANDLE, "task"));
}

/** @brief   OS_EnterTaskCritical()/OS_ExitTaskCritical() reach the port layer
 * @details os_freertos.c:153-155 and :157-159 forward to vPortEnterCritical()
 *          and vPortExitCritical(), which is what taskENTER_CRITICAL() and
 *          taskEXIT_CRITICAL() expand to
 *          (src/os/freertos/freertos/portable/ccs/arm_cortex-r5/portmacro.h:90,
 *          :91).
 */
void testOSEnterAndExitTaskCritical(void) {
    vPortEnterCritical_Expect();
    OS_EnterTaskCritical();
    vPortExitCritical_Expect();
    OS_ExitTaskCritical();
}

/** @brief   OS_GetTickCount() passes the RTOS tick count through
 * @details os_freertos.c:161-163 returns xTaskGetTickCount() unchanged.
 */
void testOSGetTickCount(void) {
    xTaskGetTickCount_ExpectAndReturn(4711u);
    TEST_ASSERT_EQUAL_UINT32(4711u, OS_GetTickCount());
}

/** @brief   OS_DelayTask() converts milliseconds into ticks
 * @details os_freertos.c:166 refuses a zero delay, :167 divides by
 *          OS_TICK_RATE_MS and :169 passes the result to vTaskDelay().
 */
void testOSDelayTask(void) {
    vTaskDelay_Expect((TickType_t)10u);
    OS_DelayTask(10u);
}

/** @brief   OS_DelayTask() refuses a zero delay
 * @details the guard at os_freertos.c:166.
 */
void testOSDelayTaskRejectsZero(void) {
    TEST_ASSERT_FAIL_ASSERT(OS_DelayTask(0u));
}

/** @brief   OS_DelayTaskUntil() converts the requested milliseconds to ticks
 * @details os_freertos.c:175 divides by OS_TICK_RATE_MS and :179 hands the
 *          result to vTaskDelayUntil(). OS_TICK_RATE_MS is portTICK_PERIOD_MS
 *          (src/app/task/os/os.h:75), which is `1000 / configTICK_RATE_HZ`
 *          (src/os/freertos/freertos/portable/ccs/arm_cortex-r5/portmacro.h:72)
 *          with configTICK_RATE_HZ == 1000
 *          (src/os/freertos/freertos/include/FreeRTOSConfig.h:67), i.e. 1.
 *
 *          WHAT IS LEFT OUT, and why: the sub-tick clamp at os_freertos.c:176-
 *          :178 cannot change the result in this build. The guard at :174
 *          rejects milliseconds == 0, and with a divisor of 1 every remaining
 *          value already yields at least one tick, so no reachable input makes
 *          the clamp body execute. Perturbing the clamp's BODY therefore does not
 *          fail this test, and that is a property of the module, not of the
 *          test: the clamp is unreachable here. This test pins the composite
 *          result of the guard, the division and the clamp, and says so rather
 *          than claiming to cover the clamp on its own.
 */
void testOSDelayTaskUntilConvertsMillisecondsToTicks(void) {
    uint32_t previousWakeTime = 7u;
    /* IgnoreArg: the pointer is the module's own wake-time variable and is
     * compared as an address, not as a value */
    xTaskDelayUntil_ExpectAndReturn(&previousWakeTime, (TickType_t)1u, pdPASS);
    /* the pointer argument is the module's own wake-time variable; the address
     * is not what this test is about */
    xTaskDelayUntil_IgnoreArg_pxPreviousWakeTime();
    OS_DelayTaskUntil(&previousWakeTime, 1u);
}

/** @brief   OS_DelayTaskUntil() rejects its two guarded arguments
 * @details the guards at os_freertos.c:173 and :174.
 */
void testOSDelayTaskUntilRejectsNullAndZero(void) {
    uint32_t previousWakeTime = 7u;
    /* os_freertos.c:173 */
    TEST_ASSERT_FAIL_ASSERT(OS_DelayTaskUntil(NULL_PTR, 10u));
    /* os_freertos.c:174 */
    TEST_ASSERT_FAIL_ASSERT(OS_DelayTaskUntil(&previousWakeTime, 0u));
}

/** @brief   OS_MarkTaskAsRequiringFpuContext() reaches the FPU context call
 * @details os_freertos.c:182-184.
 */
void testOSMarkTaskAsRequiringFpuContext(void) {
    vPortTaskUsesFPU_Expect();
    OS_MarkTaskAsRequiringFpuContext();
    TEST_ASSERT_EQUAL_UINT32(1u, test_osCountFpuContext);
}

/** @brief   OS_WaitForNotification() maps pdTRUE to OS_SUCCESS
 * @details os_freertos.c:194 waits on the default notification index with
 *          UINT32_MAX on entry and exit, and :196-198 turns pdTRUE into
 *          OS_SUCCESS.
 */
void testOSWaitForNotification(void) {
    uint32_t notifiedValue = 0u;
    /* os_freertos.c:194: xTaskNotifyWait(UINT32_MAX, UINT32_MAX, value, timeout)
     * expands to xTaskGenericNotifyWait(tskDEFAULT_INDEX_TO_NOTIFY, ...),
     * src/os/freertos/freertos/include/task.h:2907-2908 */
    xTaskGenericNotifyWait_ExpectAndReturn(
        tskDEFAULT_INDEX_TO_NOTIFY, UINT32_MAX, UINT32_MAX, &notifiedValue, 25u, pdTRUE);
    xTaskGenericNotifyWait_IgnoreArg_pulNotificationValue();
    TEST_ASSERT_EQUAL(OS_SUCCESS, OS_WaitForNotification(&notifiedValue, 25u));
}

/** @brief   OS_WaitForNotification() maps pdFALSE to OS_FAIL
 * @details the else side of os_freertos.c:196-198.
 */
void testOSWaitForNotificationReportsFailure(void) {
    uint32_t notifiedValue = 0u;
    xTaskGenericNotifyWait_ExpectAndReturn(
        tskDEFAULT_INDEX_TO_NOTIFY, UINT32_MAX, UINT32_MAX, &notifiedValue, 25u, pdFALSE);
    xTaskGenericNotifyWait_IgnoreArg_pulNotificationValue();
    TEST_ASSERT_EQUAL(OS_FAIL, OS_WaitForNotification(&notifiedValue, 25u));
}

/** @brief   OS_WaitForNotification() rejects a NULL value pointer
 * @details the guard at os_freertos.c:188.
 */
void testOSWaitForNotificationRejectsNull(void) {
    TEST_ASSERT_FAIL_ASSERT(OS_WaitForNotification(NULL_PTR, 25u));
}

/** @brief   OS_NotifyFromIsr() maps pdTRUE to OS_SUCCESS
 * @details os_freertos.c:210 notifies with eSetValueWithOverwrite on the
 *          default index, and :211-213 turns pdTRUE into OS_SUCCESS. The yield
 *          at :216 is the port macro portYIELD_FROM_ISR()
 *          (src/os/freertos/freertos/portable/ccs/arm_cortex-r5/portmacro.h:105),
 *          a register write rather than a call, so nothing is asserted on it.
 */
void testOSNotifyFromIsr(void) {
    /* xTaskNotifyFromISR() expands to xTaskGenericNotifyFromISR() with
     * tskDEFAULT_INDEX_TO_NOTIFY, src/os/freertos/freertos/include/task.h:2764-2765 */
    xTaskGenericNotifyFromISR_ExpectAndReturn(
        TEST_OS_TASK_HANDLE, tskDEFAULT_INDEX_TO_NOTIFY, 0xA5A5u, eSetValueWithOverwrite, NULL, NULL, pdTRUE);
    xTaskGenericNotifyFromISR_IgnoreArg_pxHigherPriorityTaskWoken();
    TEST_ASSERT_EQUAL(OS_SUCCESS, OS_NotifyFromIsr(TEST_OS_TASK_HANDLE, 0xA5A5u));
}

/** @brief   OS_NotifyFromIsr() maps pdFALSE to OS_FAIL
 * @details the else side of os_freertos.c:211-213.
 */
void testOSNotifyFromIsrReportsFailure(void) {
    xTaskGenericNotifyFromISR_ExpectAndReturn(
        TEST_OS_TASK_HANDLE, tskDEFAULT_INDEX_TO_NOTIFY, 0xA5A5u, eSetValueWithOverwrite, NULL, NULL, pdFALSE);
    xTaskGenericNotifyFromISR_IgnoreArg_pxHigherPriorityTaskWoken();
    TEST_ASSERT_EQUAL(OS_FAIL, OS_NotifyFromIsr(TEST_OS_TASK_HANDLE, 0xA5A5u));
}

/** @brief   OS_NotifyFromIsr() rejects a NULL task handle
 * @details the guard at os_freertos.c:204.
 */
void testOSNotifyFromIsrRejectsNull(void) {
    TEST_ASSERT_FAIL_ASSERT(OS_NotifyFromIsr(NULL_PTR, 0xA5A5u));
}

/** @brief   OS_WaitForNotificationIndexed() waits on the index it is given
 * @details os_freertos.c:231-232; the expansion to
 *          xTaskGenericNotifyWait() with the caller's index is
 *          src/os/freertos/freertos/include/task.h:2910-2911.
 */
void testOSWaitForNotificationIndexed(void) {
    uint32_t notifiedValue = 0u;
    xTaskGenericNotifyWait_ExpectAndReturn(3u, UINT32_MAX, UINT32_MAX, &notifiedValue, 25u, pdTRUE);
    xTaskGenericNotifyWait_IgnoreArg_pulNotificationValue();
    TEST_ASSERT_EQUAL(OS_SUCCESS, OS_WaitForNotificationIndexed(3u, &notifiedValue, 25u));
}

/** @brief   OS_WaitForNotificationIndexed() reports a timeout as OS_FAIL
 * @details the else side of os_freertos.c:234-236.
 */
void testOSWaitForNotificationIndexedReportsFailure(void) {
    uint32_t notifiedValue = 0u;
    xTaskGenericNotifyWait_ExpectAndReturn(3u, UINT32_MAX, UINT32_MAX, &notifiedValue, 25u, pdFALSE);
    xTaskGenericNotifyWait_IgnoreArg_pulNotificationValue();
    TEST_ASSERT_EQUAL(OS_FAIL, OS_WaitForNotificationIndexed(3u, &notifiedValue, 25u));
}

/** @brief   OS_WaitForNotificationIndexed() rejects a NULL value pointer
 * @details the guard at os_freertos.c:225.
 */
void testOSWaitForNotificationIndexedRejectsNull(void) {
    TEST_ASSERT_FAIL_ASSERT(OS_WaitForNotificationIndexed(3u, NULL_PTR, 25u));
}

/** @brief   OS_NotifyIndexedFromIsr() notifies on the index it is given
 * @details os_freertos.c:250-251; the expansion to
 *          xTaskGenericNotifyFromISR() carrying the caller's index is
 *          src/os/freertos/freertos/include/task.h:2766-2767.
 */
void testOSNotifyIndexedFromIsr(void) {
    xTaskGenericNotifyFromISR_ExpectAndReturn(
        TEST_OS_TASK_HANDLE, 2u, 0x1234u, eSetValueWithOverwrite, NULL, NULL, pdTRUE);
    xTaskGenericNotifyFromISR_IgnoreArg_pxHigherPriorityTaskWoken();
    TEST_ASSERT_EQUAL(OS_SUCCESS, OS_NotifyIndexedFromIsr(TEST_OS_TASK_HANDLE, 2u, 0x1234u));
}

/** @brief   OS_NotifyIndexedFromIsr() maps pdFALSE to OS_FAIL
 * @details the else side of os_freertos.c:252-254.
 */
void testOSNotifyIndexedFromIsrReportsFailure(void) {
    xTaskGenericNotifyFromISR_ExpectAndReturn(
        TEST_OS_TASK_HANDLE, 2u, 0x1234u, eSetValueWithOverwrite, NULL, NULL, pdFALSE);
    xTaskGenericNotifyFromISR_IgnoreArg_pxHigherPriorityTaskWoken();
    TEST_ASSERT_EQUAL(OS_FAIL, OS_NotifyIndexedFromIsr(TEST_OS_TASK_HANDLE, 2u, 0x1234u));
}

/** @brief   OS_NotifyIndexedFromIsr() rejects a NULL task handle
 * @details the guard at os_freertos.c:245.
 */
void testOSNotifyIndexedFromIsrRejectsNull(void) {
    TEST_ASSERT_FAIL_ASSERT(OS_NotifyIndexedFromIsr(NULL_PTR, 2u, 0x1234u));
}

/** @brief   OS_NotifyGive() increments the notification count of the task
 * @details os_freertos.c:263 returns xTaskNotifyGive() unchanged, which
 *          expands to xTaskGenericNotify() with eIncrement on the default index
 *          (src/os/freertos/freertos/include/task.h:2984-2985).
 */
void testOSNotifyGive(void) {
    /* os_freertos.c:263 returns the value the RTOS reported unchanged, which
     * for xTaskGenericNotify() is the notification value before the increment */
    xTaskGenericNotify_ExpectAndReturn(
        TEST_OS_TASK_HANDLE, tskDEFAULT_INDEX_TO_NOTIFY, 0u, eIncrement, NULL, (BaseType_t)3);
    TEST_ASSERT_EQUAL_UINT32(3u, OS_NotifyGive(TEST_OS_TASK_HANDLE));
}

/** @brief   OS_NotifyGive() rejects a NULL task handle
 * @details the guard at os_freertos.c:262.
 */
void testOSNotifyGiveRejectsNull(void) {
    TEST_ASSERT_FAIL_ASSERT(OS_NotifyGive(NULL_PTR));
}

/** @brief   OS_NotifyGiveFromIsr() hands the caller's woken flag on
 * @details os_freertos.c:270 forwards to vTaskNotifyGiveFromISR(), which
 *          expands to vTaskGenericNotifyGiveFromISR() on the default index
 *          (src/os/freertos/freertos/include/task.h:3071-3072).
 */
void testOSNotifyGiveFromIsr(void) {
    BaseType_t higherPriorityTaskWoken = pdFALSE;
    vTaskGenericNotifyGiveFromISR_Expect(TEST_OS_TASK_HANDLE, tskDEFAULT_INDEX_TO_NOTIFY, &higherPriorityTaskWoken);
    vTaskGenericNotifyGiveFromISR_IgnoreArg_pxHigherPriorityTaskWoken();
    OS_NotifyGiveFromIsr(TEST_OS_TASK_HANDLE, &higherPriorityTaskWoken);
}

/** @brief   OS_NotifyGiveFromIsr() rejects a NULL task handle
 * @details the guard at os_freertos.c:267.
 */
void testOSNotifyGiveFromIsrRejectsNull(void) {
    BaseType_t higherPriorityTaskWoken = pdFALSE;
    TEST_ASSERT_FAIL_ASSERT(OS_NotifyGiveFromIsr(NULL_PTR, &higherPriorityTaskWoken));
}

/** @brief   OS_NotifyTake() passes the clear-on-exit flag and the wait through
 * @details os_freertos.c:277 returns ulTaskNotifyTake() unchanged, which
 *          expands to ulTaskGenericNotifyTake() on the default index
 *          (src/os/freertos/freertos/include/task.h:3177-3178).
 */
void testOSNotifyTake(void) {
    ulTaskGenericNotifyTake_ExpectAndReturn(tskDEFAULT_INDEX_TO_NOTIFY, pdTRUE, 100u, 5u);
    TEST_ASSERT_EQUAL_UINT32(5u, OS_NotifyTake(pdTRUE, 100u));
}

/** @brief   OS_NotifyTake() accepts pdFALSE as well as pdTRUE and rejects
 *          anything else
 * @details the guard at os_freertos.c:274.
 */
void testOSNotifyTakeRejectsAnInvalidClearCount(void) {
    ulTaskGenericNotifyTake_ExpectAndReturn(tskDEFAULT_INDEX_TO_NOTIFY, pdFALSE, 0u, 0u);
    TEST_ASSERT_EQUAL_UINT32(0u, OS_NotifyTake(pdFALSE, 0u));
    TEST_ASSERT_FAIL_ASSERT(OS_NotifyTake((BaseType_t)0x7F, 0u));
}

/** @brief   OS_ClearNotificationIndexed() clears the caller's own state
 * @details os_freertos.c:285 passes a NULL task handle so the CLEAR applies to
 *          the calling task, and :287-289 maps pdTRUE to OS_SUCCESS. The
 *          expansion to xTaskGenericNotifyStateClear() is
 *          src/os/freertos/freertos/include/task.h:3243-3244.
 */
void testOSClearNotificationIndexed(void) {
    xTaskGenericNotifyStateClear_ExpectAndReturn(NULL, 4u, pdTRUE);
    TEST_ASSERT_EQUAL(OS_SUCCESS, OS_ClearNotificationIndexed(4u));
    xTaskGenericNotifyStateClear_ExpectAndReturn(NULL, 4u, pdFALSE);
    TEST_ASSERT_EQUAL(OS_FAIL, OS_ClearNotificationIndexed(4u));
}

/** @brief   OS_ReceiveFromQueue() maps pdTRUE to OS_SUCCESS
 * @details os_freertos.c:298 receives into the caller's buffer and :300-302
 *          maps pdTRUE to OS_SUCCESS.
 */
void testOSReceiveFromQueue(void) {
    uint8_t buffer = 0u;
    xQueueReceive_ExpectAndReturn(TEST_OS_QUEUE, &buffer, 30u, pdTRUE);
    xQueueReceive_IgnoreArg_pvBuffer();
    TEST_ASSERT_EQUAL(OS_SUCCESS, OS_ReceiveFromQueue(TEST_OS_QUEUE, &buffer, 30u));
}

/** @brief   OS_ReceiveFromQueue() maps pdFALSE to OS_FAIL
 * @details the else side of os_freertos.c:300-302.
 */
void testOSReceiveFromQueueReportsFailure(void) {
    uint8_t buffer = 0u;
    xQueueReceive_ExpectAndReturn(TEST_OS_QUEUE, &buffer, 0u, pdFALSE);
    xQueueReceive_IgnoreArg_pvBuffer();
    TEST_ASSERT_EQUAL(OS_FAIL, OS_ReceiveFromQueue(TEST_OS_QUEUE, &buffer, 0u));
}

/** @brief   OS_ReceiveFromQueue() rejects a NULL buffer
 * @details the guard at os_freertos.c:294.
 */
void testOSReceiveFromQueueRejectsNull(void) {
    TEST_ASSERT_FAIL_ASSERT(OS_ReceiveFromQueue(TEST_OS_QUEUE, NULL_PTR, 30u));
}

/** @brief   OS_SendToBackOfQueue() appends and maps pdTRUE to OS_SUCCESS
 * @details os_freertos.c:310 sends to the back and :312-314 maps pdTRUE to
 *          OS_SUCCESS. xQueueSendToBack() expands to xQueueGenericSend() with
 *          queueSEND_TO_BACK
 *          (src/os/freertos/freertos/include/queue.h:428-429).
 */
void testOSSendToBackOfQueue(void) {
    uint8_t item = 0u;
    xQueueGenericSend_ExpectAndReturn(TEST_OS_QUEUE, &item, 30u, queueSEND_TO_BACK, pdTRUE);
    xQueueGenericSend_IgnoreArg_pvItemToQueue();
    TEST_ASSERT_EQUAL(OS_SUCCESS, OS_SendToBackOfQueue(TEST_OS_QUEUE, &item, 30u));
}

/** @brief   OS_SendToBackOfQueue() maps pdFALSE to OS_FAIL
 * @details the else side of os_freertos.c:312-314.
 */
void testOSSendToBackOfQueueReportsFailure(void) {
    uint8_t item = 0u;
    xQueueGenericSend_ExpectAndReturn(TEST_OS_QUEUE, &item, 0u, queueSEND_TO_BACK, pdFALSE);
    xQueueGenericSend_IgnoreArg_pvItemToQueue();
    TEST_ASSERT_EQUAL(OS_FAIL, OS_SendToBackOfQueue(TEST_OS_QUEUE, &item, 0u));
}

/** @brief   OS_SendToBackOfQueue() rejects a NULL item
 * @details the guard at os_freertos.c:307.
 */
void testOSSendToBackOfQueueRejectsNull(void) {
    TEST_ASSERT_FAIL_ASSERT(OS_SendToBackOfQueue(TEST_OS_QUEUE, NULL_PTR, 30u));
}

/** @brief   OS_SendToBackOfQueueFromIsr() appends from interrupt context
 * @details os_freertos.c:325-326; xQueueSendToBackFromISR() expands to
 *          xQueueGenericSendFromISR() with queueSEND_TO_BACK
 *          (src/os/freertos/freertos/include/queue.h:1109-1110).
 */
void testOSSendToBackOfQueueFromIsr(void) {
    uint8_t  item                  = 0u;
    BaseType_t higherPriorityTaskWoken = pdFALSE;
    /* os_freertos.c:326 casts the caller's long* to BaseType_t*, so the woken
     * flag is read back through a BaseType_t*; the address is not asserted. */
    xQueueGenericSendFromISR_ExpectAndReturn(TEST_OS_QUEUE, &item, &higherPriorityTaskWoken, queueSEND_TO_BACK, pdTRUE);
    xQueueGenericSendFromISR_IgnoreArg_pxHigherPriorityTaskWoken();
    TEST_ASSERT_EQUAL(
        OS_SUCCESS,
        OS_SendToBackOfQueueFromIsr(
            TEST_OS_QUEUE, &item, (long *)(void *)&higherPriorityTaskWoken));
}

/** @brief   OS_SendToBackOfQueueFromIsr() maps pdFALSE to OS_FAIL
 * @details the else side of os_freertos.c:328-330.
 */
void testOSSendToBackOfQueueFromIsrReportsFailure(void) {
    uint8_t  item                      = 0u;
    BaseType_t higherPriorityTaskWoken = pdFALSE;
    xQueueGenericSendFromISR_ExpectAndReturn(
        TEST_OS_QUEUE, &item, &higherPriorityTaskWoken, queueSEND_TO_BACK, pdFALSE);
    xQueueGenericSendFromISR_IgnoreArg_pxHigherPriorityTaskWoken();
    TEST_ASSERT_EQUAL(
        OS_FAIL,
        OS_SendToBackOfQueueFromIsr(
            TEST_OS_QUEUE, &item, (long *)(void *)&higherPriorityTaskWoken));
}

/** @brief   OS_SendToBackOfQueueFromIsr() rejects a NULL item
 * @details the guard at os_freertos.c:322.
 */
void testOSSendToBackOfQueueFromIsrRejectsNull(void) {
    BaseType_t higherPriorityTaskWoken = pdFALSE;
    TEST_ASSERT_FAIL_ASSERT(OS_SendToBackOfQueueFromIsr(
        TEST_OS_QUEUE, NULL_PTR, (long *)(void *)&higherPriorityTaskWoken));
}

/** @brief   OS_SuspendTask() suspends without asserting its argument
 * @details os_freertos.c:334-337 documents the argument as accepting the whole
 *          range and performs no FAS_ASSERT, so a NULL handle must be forwarded
 *          rather than trapped. That is the observable difference from
 *          OS_ResumeTask() below.
 */
void testOSSuspendTaskAcceptsAnyHandle(void) {
    vTaskSuspend_Expect(TEST_OS_TASK_HANDLE);
    OS_SuspendTask(TEST_OS_TASK_HANDLE);
}

/** @brief   OS_ResumeTask() rejects a NULL task handle
 * @details the guard at os_freertos.c:340.
 */
void testOSResumeTaskRejectsNull(void) {
    TEST_ASSERT_FAIL_ASSERT(OS_ResumeTask(NULL_PTR));
}

/** @brief   OS_ResumeTask() resumes the handle it is given
 * @details os_freertos.c:341.
 */
void testOSResumeTask(void) {
    vTaskResume_Expect(TEST_OS_TASK_HANDLE);
    OS_ResumeTask(TEST_OS_TASK_HANDLE);
}

/** @brief   OS_GetNumberOfStoredMessagesInQueue() reports the queue depth
 * @details os_freertos.c:345-346 returns uxQueueMessagesWaiting() narrowed to
 *          uint32_t.
 */
void testOSGetNumberOfStoredMessagesInQueue(void) {
    uxQueueMessagesWaiting_ExpectAndReturn(TEST_OS_QUEUE, 12u);
    TEST_ASSERT_EQUAL_UINT32(12u, OS_GetNumberOfStoredMessagesInQueue(TEST_OS_QUEUE));
    uxQueueMessagesWaiting_ExpectAndReturn(TEST_OS_QUEUE, 0u);
    TEST_ASSERT_EQUAL_UINT32(0u, OS_GetNumberOfStoredMessagesInQueue(TEST_OS_QUEUE));
}

/** @brief   OS_SemaphoreGive() gives the semaphore
 * @details os_freertos.c:351; xSemaphoreGive() expands to
 *          xQueueGenericSend() with a NULL item
 *          (src/os/freertos/freertos/include/semphr.h:460).
 */
void testOSSemaphoreGive(void) {
    xQueueGenericSend_ExpectAndReturn(TEST_OS_SEMAPHORE, NULL, semGIVE_BLOCK_TIME, queueSEND_TO_BACK, pdPASS);
    OS_SemaphoreGive(TEST_OS_SEMAPHORE);
}

/** @brief   OS_SemaphoreGive() rejects a NULL semaphore
 * @details the guard at os_freertos.c:350.
 */
void testOSSemaphoreGiveRejectsNull(void) {
    TEST_ASSERT_FAIL_ASSERT(OS_SemaphoreGive(NULL_PTR));
}

/** @brief   OS_SemaphoreGiveFromIsr() gives the semaphore from interrupt
 *          context
 * @details os_freertos.c:359; xSemaphoreGiveFromISR() expands to
 *          xQueueGiveFromISR()
 *          (src/os/freertos/freertos/include/semphr.h:640).
 */
void testOSSemaphoreGiveFromIsr(void) {
    BaseType_t higherPriorityTaskWoken = pdFALSE;
    xQueueGiveFromISR_ExpectAndReturn(TEST_OS_SEMAPHORE, &higherPriorityTaskWoken, pdTRUE);
    OS_SemaphoreGiveFromIsr(TEST_OS_SEMAPHORE, &higherPriorityTaskWoken);
}

/** @brief   OS_SemaphoreGiveFromIsr() rejects a NULL semaphore
 * @details the guard at os_freertos.c:355.
 */
void testOSSemaphoreGiveFromIsrRejectsNull(void) {
    BaseType_t higherPriorityTaskWoken = pdFALSE;
    TEST_ASSERT_FAIL_ASSERT(OS_SemaphoreGiveFromIsr(NULL_PTR, &higherPriorityTaskWoken));
}

/** @brief   OS_SemaphoreTake() maps pdTRUE to OS_SUCCESS
 * @details os_freertos.c:369 takes the semaphore and :373-375 maps pdTRUE to
 *          OS_SUCCESS; xSemaphoreTake() expands to xQueueSemaphoreTake()
 *          (src/os/freertos/freertos/include/semphr.h:298).
 */
void testOSSemaphoreTake(void) {
    xQueueSemaphoreTake_ExpectAndReturn(TEST_OS_SEMAPHORE, 50u, pdTRUE);
    TEST_ASSERT_EQUAL(OS_SUCCESS, OS_SemaphoreTake(TEST_OS_SEMAPHORE, 50u));
}

/** @brief   OS_SemaphoreTake() maps pdFALSE to OS_FAIL
 * @details the else side of os_freertos.c:373-375.
 */
void testOSSemaphoreTakeReportsFailure(void) {
    xQueueSemaphoreTake_ExpectAndReturn(TEST_OS_SEMAPHORE, 0u, pdFALSE);
    TEST_ASSERT_EQUAL(OS_FAIL, OS_SemaphoreTake(TEST_OS_SEMAPHORE, 0u));
}

/** @brief   OS_SemaphoreTake() rejects a NULL semaphore
 * @details the guard at os_freertos.c:363.
 */
void testOSSemaphoreTakeRejectsNull(void) {
    TEST_ASSERT_FAIL_ASSERT(OS_SemaphoreTake(NULL_PTR, 50u));
}
