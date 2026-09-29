/*
 * sil_cmock_queue_registry_shim.h -- injected into every CMock-generated mock
 * header, immediately AFTER the original header, via CMock's
 * :includes_h_post_orig_header: option.
 *
 * WHAT IT IS FOR
 * --------------
 * src/os/freertos/freertos/include/FreeRTOS.h:589-591 declares three queue
 * registry functions as EMPTY function-like macros when the registry is off:
 *
 *     #if ( configQUEUE_REGISTRY_SIZE < 1 )
 *         #define vQueueAddToRegistry( xQueue, pcName )
 *         #define vQueueUnregisterQueue( xQueue )
 *         #define pcQueueGetName( xQueue )
 *     #endif
 *
 * configQUEUE_REGISTRY_SIZE is defined NOWHERE in the repository (verified by
 * rg over src/, tests/ and conf/), so FreeRTOS.h:585 defaults it to 0U and
 * those three functions are compiled out on every platform, including the
 * Windows and Linux gcc builds upstream develops against. That is why this is
 * a pre-existing, platform-independent condition and not a SIL artefact.
 *
 * CMock nonetheless mocks them, because it parses the DECLARATIONS in
 * queue.h and cannot know the preprocessor will later delete the bodies. It
 * emits real definitions:
 *
 *     void vQueueAddToRegistry(QueueHandle_t xQueue, const char *pcName) { ... }
 *
 * and the preprocessor then treats that whole declaration as a macro
 * invocation and replaces it with nothing, leaving the opening brace stranded:
 *
 *     Mockqueue.c:3487:1: error: expected identifier or '('
 *     Mockqueue.c:3562:1: error: expected identifier or '('
 *     Mockqueue.c:3632:1: error: expected identifier or '('
 *
 * Three errors, three macros. This is a disagreement between FreeRTOS and
 * CMock, not a CMock bug and not a defect in any foxBMS file.
 *
 * WHY #undef IS THE RIGHT HARNESS FIX
 * ----------------------------------
 * The declarations CMock is mocking are unreachable code: the product has
 * compiled them out, so nothing in the repository calls them, and the tests
 * never mention them (verified: rg over the three affected tests finds no
 * reference to any of the three names). CMock's definition is pure dead
 * weight that happens to be preprocessed away.
 *
 * Undefining the macros AFTER the original header has been included, but
 * BEFORE the generated definitions are compiled, lets CMock's already-correct
 * definitions survive. Nothing is suppressed, no diagnostic is muted, and the
 * repository's FreeRTOS.h is not touched: this is CMock configuration in the
 * SIL harness's isolated project.yml only.
 *
 * LIMITS, STATED PLAINLY
 * ----------------------
 *  - This is a harness accommodation for a third-party disagreement. It is not
 *    a claim that the queue registry works; the registry is compiled out and
 *    this harness therefore verifies NOTHING about it.
 *  - The #undef applies to every translation unit that includes the generated
 *    mock, so a call to one of the three from product code would reach the
 *    mock rather than expanding to nothing. Whether that matters is decided by
 *    the runtime result, not assumed: if it mattered, the affected tests would
 *    fail with CMock's "called more times than expected", and they do not.
 */
#ifndef FOXBMS_SIL_CMOCK_QUEUE_REGISTRY_SHIM_H_
#define FOXBMS_SIL_CMOCK_QUEUE_REGISTRY_SHIM_H_

/*
 * Undefine only if they are currently the empty function-like macros. Guarding
 * on the definition keeps this a no-op for any build that DOES enable the
 * registry, so the shim cannot silently change a configuration it was not
 * written for.
 */
#ifdef vQueueAddToRegistry
#undef vQueueAddToRegistry
#endif
#ifdef vQueueUnregisterQueue
#undef vQueueUnregisterQueue
#endif
#ifdef pcQueueGetName
#undef pcQueueGetName
#endif

#endif /* FOXBMS_SIL_CMOCK_QUEUE_REGISTRY_SHIM_H_ */
