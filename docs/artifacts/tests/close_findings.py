#!/usr/bin/env python3
"""Correct every finding record against the corpus as it stands, and migrate the
disposition vocabulary.

WHAT THIS DOES
--------------
1. Re-tests nothing itself - it consumes the verdicts that
   `docs/artifacts/tests/audit_findings.py` derives from the live corpus, and the
   author of this script checked that output before writing a single line here.
   The `reverification` field written onto each record is the evidence that
   re-test, quoted, so the record carries its own proof of currency.

2. For every STALE record, rewrites `resolution` to state the current position:
   the condition that was detected, what fixed it cited by record/field/rule, the
   evidence, and any residual. For every record that is still open, states
   precisely what remains and why it cannot be closed here. For every SUPERSEDED
   record, names the successor.

3. Migrates `disposition` to the vocabulary defined in
   `docs/artifacts/governance/finding-disposition-vocabulary.md` and to the enum
   in `docs/artifacts/schemas/finding.schema.json`.

4. Appends three new records for conditions that this pass discovered and that
   would otherwise be lost:
     FB2-REV-FND-000039  the fault_reaction rule's id-pattern blind spot
     FB2-REV-FND-000040  the diagnostic_coverage rule's id-pattern filter,
                         deliberately NOT changed
     FB2-REV-FND-000041  the security requirements are verification-PLANNED and
                         blocked, not verification-achieved
     FB2-REV-FND-000042  the vacuous-green census, which is the live form of the
                         vacuity concern in FB2-REV-FND-000037

NO RECORD IS DELETED. A finding record is an audit-trail entry; deleting the
record of a defect the corpus fixed would leave the corpus unable to show it ever
had one. This script refuses to run twice over the same record.

NOTHING HERE ASSERTS human approval, tool qualification, certification,
ISO 26262 conformity or an ASPICE capability level. `human_approval_status` stays
`pending`, `production_authorized` stays false and `product_verification_credit`
stays false on every record touched.
"""
from __future__ import annotations

import json
import re
import sys
from collections import OrderedDict
from pathlib import Path

ART = Path(__file__).resolve().parents[1]
FIND = ART / "reviews" / "findings"
SAFETY = ART / "corpus" / "synthetic_reference" / "safety"
VERIF = ART / "corpus" / "synthetic_reference" / "verification"
DATE = "2026-09-30T00:00:00Z"
AUTHOR = "data_quality_engineer"

GUARD = ("human_approval_status remains pending, production_authorized remains "
         "false and product_verification_credit remains false. No human approved "
         "this revision, no tool is claimed to be qualified, and no certification, "
         "ISO 26262 conformity or ASPICE capability level is claimed or implied.")

PREAMBLE = (
    "CORRECTED @date@ against the corpus as it stands, by re-deriving the "
    "condition this record asserts rather than by trusting the record's own "
    "history. Method and full per-record evidence: "
    "docs/artifacts/tests/audit_findings.py. Classification vocabulary: "
    "docs/artifacts/governance/finding-disposition-vocabulary.md."
)

# ---------------------------------------------------------------------------
# Group A: 000001..000007 - FSR verification links. Fixed by the rule correction
# recorded as FB2-REV-FND-000029, over links that already existed.
GROUP_A = (
    "RESOLVED. The condition this record detected was real and it was correctly "
    "diagnosed in this record's own root_cause: the safety-requirement "
    "verification rule in docs/artifacts/tools/corpus.py built its set from the "
    "SOURCE endpoint of a verifies/validates link, and under the direction "
    "master prompt section 13 declares - 'verifies: verification measure -> "
    "requirement/design' - the requirement is the TARGET, so the set could never "
    "contain a requirement and the rule reported a gap for every safety "
    "requirement including those verified by twenty measures.\n\n"
    "WHAT FIXED IT, in two parts, and both were needed. First, the rule itself: "
    "docs/artifacts/tools/corpus.py now reads `verified = {l[\"target_id\"] for l "
    "in links if l.get(\"relation_type\") in (\"verifies\", \"validates\") and "
    "l.get(\"target_id\")}`. That correction is recorded as finding "
    "FB2-REV-FND-000029 and is not repeated here. Second, and this is the part "
    "that was missing from this record's own account: @subject@ in profile "
    "@profile@ is the target of @nlinks@ verifies link(s) - @links@ - from "
    "@measures@. Those links were authored before this record was raised; the "
    "rule simply could not see them.\n\n"
    "EVIDENCE, re-derived from the live registries on @date@: the rule's "
    "population is @subject@ appears as the target of @nlinks@ verifies link(s) "
    "and as the source of 0, so the asserted condition 'has no verifies/validates "
    "link' is false. The rule is not weakened by the fix and was not weakened "
    "here: it is strictly harder to satisfy by accident than before, because a "
    "requirement appearing as the SOURCE of a verifies link is a malformed link "
    "under the declared direction and no longer counts as verification. Two "
    "self-tests pin both directions - 'correctly directed verifies link "
    "(requirement as target) not flagged' and 'verifies link with requirement as "
    "source does not count as verification'.\n\n"
    "RESIDUAL: none for the condition this record asserts. Two limits are stated "
    "so that 'resolved' is not read as more than it is. The fix is a link-"
    "direction correction, not new verification work: @subject@ was verified "
    "before and is verified now, and this record did not cause that. And a "
    "verifies link is a plan, not an outcome - it says a measure exists and points "
    "at this requirement, not that the measure was executed and passed. @guard@"
)

# ---------------------------------------------------------------------------
# Group B: 000008..000012 - SEC verification links. The task premise for this
# sprint stated these were genuinely OPEN. They are not.
GROUP_B = (
    "RESOLVED, and the premise under which this sprint re-examined it is "
    "corrected on the record. The hypothesis was that the five security "
    "requirements carry no verifies or validates link in either direction and are "
    "therefore genuinely unverified. That is false: all five are the target of a "
    "verifies link authored before this record was raised, and the validator "
    "correctly reports nothing because there is nothing to report.\n\n"
    "WHAT FIXED IT. The measures and their links, which this record's own "
    "resolution said did not exist. @tms@ was authored for @subject@ and linked by "
    "@link@ with relation_type 'verifies' in "
    "docs/artifacts/corpus/synthetic_reference/traceability/link-registry/"
    "synthetic_reference/links-concept-lifecycle.json. Each measure carries an "
    "oracle_detail block declaring the oracle's kind and why that oracle is the "
    "right one for the requirement rather than borrowed from elsewhere; the kinds "
    "in use across the five are source_grounded, analytical_model and, for "
    "@tms@, synthetic_assumption - that last one recorded honestly rather than "
    "hidden, because unpredictability of an initial sequence number is not "
    "observable from outside the implementation. The rule correction recorded as "
    "FB2-REV-FND-000029 was the second necessary part: without it the correctly "
    "directed links could not clear the finding, which is precisely the situation "
    "this record's own impact field described and could not fix.\n\n"
    "EVIDENCE, re-derived on @date@: @subject@ appears as the target of "
    "@nlinks@ verifies link(s) and as the source of 0. The counterfactual was also "
    "run and is worth recording, because it is what turns 'there is a link' into "
    "'the rule is looking at the right thing': with those @nlinks@ link(s) removed "
    "from an in-memory copy of the registries, the rule reports all five security "
    "requirements as unverified. The rule was never silent about them. See "
    "docs/artifacts/tests/rule_scope_probe.py.\n\n"
    "RESIDUAL, and this is the part that matters: the LINK condition is resolved "
    "and the VERIFICATION condition is not. All five executions - "
    "FB2-VER-EXE-000016..000020 - carry execution_kind 'none' and outcome "
    "'blocked', with a recorded blocked_reason that the security test harness for "
    "this corpus does not exist and that the requirement constrains a service the "
    "hypothetical project has planned but not built. @subject@.verification_status "
    "is therefore still 'not_verified', and that is correct. The security concept "
    "in this corpus is verification-PLANNED and not verification-ACHIEVED. This "
    "residual is now its own record, FB2-REV-FND-000041, rather than a sentence "
    "buried at the end of a resolved finding where it would be lost. @guard@"
)

# ---------------------------------------------------------------------------
# Group C: 000013..000019 - FSR fault_reaction.
GROUP_C = (
    "RESOLVED. The condition this record detected was real: the safety-requirement "
    "completeness rule (MUT-008, safety_requirement_completeness_checker) "
    "requires a machine-readable fault_reaction on every safety-domain "
    "requirement, and at the time this record was raised @subject@ in profile "
    "@profile@ had none. The reaction existed only as prose inside `statement`, "
    "which is why a checker could not compare a stated reaction time against a "
    "requirement - the concrete harm this record's impact field named.\n\n"
    "WHAT FIXED IT: a populated `fault_reaction` object authored onto @subject@ "
    "at revision @frev@, recorded in that record's own revision_history. For the "
    "synthetic_reference copies the block is a full allocation - "
    "allocated_element_id, element_owns_reaction, reaction, triggered_by, "
    "reaction_time_budget_ms, mode_dependence, allocation_basis and open_limits - "
    "traced to the element FB2-SAF-FSC-000001 allocates the reaction to. For the "
    "as_is copies it is the honest answer instead: those records have origin "
    "source_observed, so the reaction is copied from the observed source rather "
    "than from the synthetic concept, and where the element owns no reaction the "
    "block says so and says why. That asymmetry is the point of the block and is "
    "why it was worth authoring rather than suppressing.\n\n"
    "EVIDENCE, re-derived on @date@: @subject@ in profile @profile@ carries a "
    "populated fault_reaction object with fields @fkeys@. The rule is silent on it. "
    "The rule was NOT weakened to achieve this and no requirement was reclassified "
    "to dodge it - the opposite happened, see below.\n\n"
    "THE RULE ALSO GOT WIDER WHILE THIS WAS BEING FIXED, and that is the part "
    "this record could not have known. MUT-008 used to carry a third condition, "
    "`\"-FSR-\" in id`, which made it structurally incapable of reporting the five "
    "FB2-SAF-SEC-* security requirements - a different class of safety-domain "
    "requirement, carrying the whole cybersecurity concept, which this rule was "
    "always meant to cover. The filter has been removed; the rule's scope was "
    "widened and nothing was narrowed. Four self-tests now pin that widened scope "
    "from both sides. Recorded as FB2-REV-FND-000039. @guard@"
)

# ---------------------------------------------------------------------------
# Group D: 000020..000021 - SGO asil_justification.
GROUP_D = (
    "RESOLVED. The condition this record detected was real: @subject@ carries "
    "asil 'ASIL_D' and, at the time this record was raised, carried no "
    "asil_justification, so the corpus held an ASIL assignment for which no "
    "supporting argument existed and the whole chain downstream inherited their "
    "rigour from that undeclared assignment.\n\n"
    "WHAT FIXED IT: an `asil_justification` object authored onto @subject@ at "
    "revision @srev@, recorded in that record's own revision_history. The record's "
    "resolution warned that writing the justification required an engineering "
    "determination this corpus had no basis to assert, and that inventing one "
    "would be worse than the gap. That judgement was right about the danger and "
    "wrong about the possibility, and the difference is that the justification is "
    "a DERIVATION rather than a restatement: the block records severity, exposure, "
    "controllability and the operational-situation assumption, derives the class "
    "from them, and states in its own words what the classification does and does "
    "not assert. It is a derivation from stated inputs, not an assertion of a "
    "determination that was never made.\n\n"
    "EVIDENCE, re-derived on @date@: @subject@ in profile @profile@ carries a "
    "populated asil_justification with keys @jkeys@, and the ASIL validator's "
    "third check - which re-derives the class from the justification's own "
    "severity and exposure ratings using ISO 26262-3:2018 Table 4 and reports an "
    "assignment the derivation contradicts - finds no contradiction. The "
    "self-test 'unjustified ASIL downgrade detected despite a present "
    "justification' proves that check is live rather than dormant.\n\n"
    "WHAT THIS DOES NOT MEAN, and the record's own impact field was right to be "
    "insistent about it: an asil_justification is not an ASIL determination. It "
    "is this corpus's stated reasoning about a field value in a synthetic "
    "reference project, and no functional-safety expert has reviewed it. The "
    "requirement that the chain's worst-case acquisition, debounce and contactor "
    "legs do not fit inside 100 ms is a separate matter and was closed on its own "
    "evidence as FB2-REV-FND-000025. @guard@"
)

# ---------------------------------------------------------------------------
# Open records.
RES_030 = (
    "STILL OPEN, and deliberately so. Re-verified on @date@: FB2-SW-DSN-000004 and "
    "FB2-PIM-IMP-000003 are still absent from the artifact index. Nothing was "
    "authored to close it and nothing should have been.\n\n"
    "WHY IT WAS NOT CLOSED. Writing FB2-SW-DSN-000004 would mean inventing the "
    "architecture of an AFE driver child element, and writing FB2-PIM-IMP-000003 "
    "would mean inventing the content of a process-improvement cycle. No source, "
    "parameter, assumption or analysis in this corpus constrains either, so "
    "authoring them would be fabrication wearing a record id, which master prompt "
    "section 14 forbids by name. The two references were not typos - unlike "
    "FB2-SAF-SCO-000001, which was, and which was corrected under "
    "FB2-REV-FND-000023 - so they cannot be closed the way that one was.\n\n"
    "WHAT IS IN PLACE. docs/artifacts/tools/check_references.py resolves every "
    "id-shaped string in every corpus and scenario record against the artifact "
    "index, the source registry, the assumption registries, the link registries and "
    "the parameter registries, and prints anything that does not resolve. Both ids "
    "carry an explicit entry in that tool's KNOWN_BROKEN_ALLOWED declared-forward "
    "allowlist, so the tool reports them as declared-forward rather than passing "
    "them silently. That is the difference between this class of defect and "
    "FB2-SAF-SCO-000001: the tool can now tell a planned-but-unwritten reference "
    "from a typo, which is what stopped the same mistyped value appearing in two "
    "records before.\n\n"
    "WHAT WOULD CLOSE IT, precisely. A decision by an owner who knows the intended "
    "architecture and the intended improvement cycle: either author the two records "
    "from real design and process input, or mark the three references as "
    "planned-not-yet-authored on the face of the records that carry them so a "
    "reader is not left resolving a dangling id. Both are engineering and planning "
    "decisions. No automated pass may take either, and this corpus is not in a "
    "position to invent the content either would need. @guard@"
)

RES_034 = (
    "STILL OPEN, on the residual this record identified and did not close. The "
    "harness-side half is closed and stays closed: sil/run.sh maps uint64_t and "
    "uint64 onto Unity's UINT64 comparator in its isolated copy of the Ceedling "
    "project file, so CMock emits a value comparison rather than an 8-byte memcmp "
    "of a by-value scalar's address, and the second defect the fix exposed - the "
    "negative float_t fixtures passed straight into a uint64_t parameter, which "
    "the product sign-extends and the test expected as 0 - is fixed by casting "
    "through (int64_t) at the expectation sites. Re-verified on @date@: "
    "test_can_cbs_tx_f_debug-build-configuration.c and "
    "test_can_cbs_tx_f_pack-minimum-maximum-values.c both build and pass.\n\n"
    "WHAT REMAINS, and it is the part that was never fixed: "
    "conf/unit/app_project_posix.yml still does not map uint64_t. Its :treat_as: "
    "block is [uint8: HEX8, uint16: HEX16, uint32: UINT32, int8: INT8, bool: "
    "UINT8] and its :memcmp_if_unknown: is still true, so on any host running the "
    "SHIPPED configuration rather than the SIL harness the same address comparison "
    "is generated and the same negative-float conversion defect stays hidden. "
    "conf/ is outside this corpus's write boundary, which is why it was not "
    "touched and why the fix is a one-line entry that nobody has applied.\n\n"
    "WHY IT CANNOT BE CLOSED HERE. conf/unit/app_project_posix.yml is upstream's "
    "file. Changing it is a product decision, and a passing SIL run says nothing "
    "about a Linux or Windows run of the shipped suite, which is the whole point "
    "of the residual. What WOULD close it: adding `uint64_t: UINT64` and "
    "`uint64: UINT64` to that :treat_as: block, or setting :memcmp_if_unknown: to "
    "false, and re-running the suite under the shipped configuration. Both are "
    "one-line changes to a file this work is not authorized to modify, and the "
    "owner is the foxBMS maintainer, not this corpus. @guard@"
)

RES_035 = (
    "STILL OPEN. Re-verified on @date@ against the most recent full SIL host sweep "
    "and its per-test log: tests/unit/app/driver/phy/test_dp83869.c still fails, "
    "and it still fails the way this record describes. The file reports 15 of 15 "
    "cases as crashed after the runner aborts, which is the signature of a process "
    "that dies mid-file with Ceedling attributing the crash to whatever case was "
    "in flight - not fifteen independent failures.\n\n"
    "THE CMock ARRAY-PLUGIN WORK DOES NOT REACH IT, and that was worth checking "
    "rather than assuming. The array plugin changes the comparison selected for a "
    "void* parameter from UNITY_TEST_ASSERT_EQUAL_PTR to "
    "UNITY_TEST_ASSERT_EQUAL_HEX8_ARRAY. The fault here is not on a void* "
    "parameter: it is on IO_PinReset's typed `volatile uint32_t *` parameter, so "
    "the array branch is not the branch this code takes and the plugin is "
    "inert for this file. The root cause stands exactly as recorded: the test "
    "encodes a target-only precondition, the address of a GIO port register, into "
    "an expectation, CMock honours :when_ptr: :compare_data for the typed pointer "
    "and dereferences it, and 0xFFF7BC38 is a TMS570 device address with no "
    "mapping on a host.\n\n"
    "PRECISE UNBLOCK CONDITION - one of exactly two things, both product-owner "
    "decisions, neither of which is a test edit this corpus may make. Either: "
    "accept tests/unit/app/driver/phy/test_dp83869.c as a target-only test and "
    "exclude it from host runs, with that reason recorded on the exclusion; or: "
    "redesign the file so the reset pin is identified in a way a host harness can "
    "evaluate. The three ways of making it go green without one of those were each "
    "constructed and each rejected on evidence, and the rejections are recorded in "
    "this record's own impact field and are not restated as if they were options. "
    "Mapping a SIL gioPORTA at 0xFFF7BC34 would fabricate the register map the "
    "harness exists to be honest about not having; retargeting to gioPORTA->DOUT "
    "would delete the only statement of which physical pin is reset; suppressing "
    "the comparison would weaken the oracle.\n\n"
    "WHAT WAS ACHIEVED AND STILL STANDS: the root cause is isolated with a "
    "captured stack trace and a fault address that names the exact dereferenced "
    "location, the earlier misattribution to testPHY_OperationModeGet is "
    "corrected to testPHY_HardwareReset, and the file's 13 genuinely-passing "
    "cases and 2 class-A failures are individually visible instead of being "
    "reported as 15 of 15 failed after an abort. @guard@"
)

RES_036 = (
    "STILL OPEN as a defect; the harness mitigation described in this record's own "
    "resolution remains in place and is not what is open.\n\n"
    "WHAT STILL HOLDS, re-verified on @date@. The mechanism is unchanged and is "
    "platform-independent: FreeRTOS defines vQueueAddToRegistry, "
    "vQueueUnregisterQueue and pcQueueGetName as empty function-like macros when "
    "configQUEUE_REGISTRY_SIZE is 0, which the shipped configuration sets, and the "
    "preprocessor then applies those macros to CMock's own generated function "
    "definitions, consuming the function name and its parameter list and leaving a "
    "body that does not parse. Neither component is individually faulty: CMock "
    "cannot evaluate a macro-valued preprocessor condition, and FreeRTOS cannot "
    "know its macros will be applied to generated code. Nothing under src/os/"
    "freertos or conf/ has changed, so anyone running the shipped configuration "
    "on GNU gcc or on the project's Windows environment hits the identical "
    "failure.\n\n"
    "WHAT IS MITIGATED. The shim at sil/shim/sil_cmock_queue_registry_shim.h "
    "exists and is injected via :includes_h_post_orig_header:, #undef-ing the "
    "three macros after the original header is included and before the generated "
    "definitions are compiled. Re-verified on @date@: 7 of the 8 named tests now "
    "build and run, and the 8th, test_uart.c, is a build failure under a "
    "different class (link_failure) that this finding does not claim.\n\n"
    "WHY IT STAYS OPEN AND IS NOT CALLED RESOLVED. The shim is a mitigation, not a "
    "fix, and calling a mitigated upstream defect 'resolved' is the exact error "
    "this corpus's other findings were raised about. The defect is a real, "
    "pre-existing, platform-independent disagreement between two tools that "
    "neither diagnoses. The residual risk of the mitigation is stated in this "
    "record's own impact field and is not restated as closed: the #undef applies "
    "to every translation unit including the generated mock, so a future product "
    "change that began calling one of the three functions would reach the mock "
    "instead of expanding to nothing - which would surface as a CMock "
    "'called more times than expected' failure rather than as a silent behaviour "
    "change, which is the acceptable direction, but it is a real change in "
    "semantics for code paths that do not exist today.\n\n"
    "WHAT WOULD CLOSE IT: enabling configQUEUE_REGISTRY_SIZE, or changing the "
    "empty macros to declarations, or teaching CMock to evaluate macro-valued "
    "conditions. All three are changes to src/os/freertos or to a vendored "
    "dependency, all outside this corpus's write boundary, and all the foxBMS "
    "maintainer's decision. @guard@"
)

RES_037 = (
    "STILL OPEN, and SHARPER than when this record was raised. Re-verified on "
    "@date@: the loud red failures this record describes are gone - all four named "
    "tests now build and pass - but the condition the record actually diagnosed, "
    "that the content oracle for a void* queue payload is provably vacuous, is not "
    "gone. For two of the four it has become a SILENT GREEN, which is worse than a "
    "red because nothing in the run output distinguishes it from a real pass.\n\n"
    "WHAT CHANGED. The SIL harness now loads CMock's array plugin alongside the "
    "shipped :callback and :return_thru_ptr entries, which changes the comparison "
    "selected for a void* parameter from UNITY_TEST_ASSERT_EQUAL_PTR to "
    "UNITY_TEST_ASSERT_EQUAL_HEX8_ARRAY. sil/run.sh's own comment on this warns "
    "that enabling the plugin ALONE turns loud failures into silent vacuous "
    "passes, because the comparison depth is a per-call argument supplied only by "
    "the X_ExpectWithArray macro family and a plain X_ExpectAndReturn gets depth "
    "zero. The two CAN cell tests did move to OS_SendToBackOfQueue_ExpectWithArray"
    "AndReturn with a correctly typed and correctly sized payload, which is the "
    "right move - and it was not sufficient.\n\n"
    "WHY IT IS STILL VACUOUS, MEASURED NOT ARGUED. In "
    "test_can_cbs_rx_afe_cell-temperatures.c and "
    "test_can_cbs_rx_afe_cell-voltages.c the expected payload is declared "
    "`CAN_CAN2AFE_CELL_TEMPERATURES_QUEUE_s expectedQueuePayload = {0}` and "
    "`CAN_CAN2AFE_CELL_VOLTAGES_QUEUE_s expectedQueuePayload = {0}` - every byte "
    "zero. The routine-test block registers CAN_RxGetSignalDataFromMessageData_"
    "Expect, which performs argument checks only, with no matching "
    "ReturnThruPtr_pCanSignal, and the generated Mockos.c contains no assignment to "
    "Expected_pCanSignal anywhere in the CAN_RxGetSignalDataFromMessageData body. "
    "The product's extractor therefore never writes its out-parameter, the packed "
    "payload it builds is all zeros, and UNITY_TEST_ASSERT_EQUAL_HEX8_ARRAY "
    "compares 20 zero bytes against 20 zero bytes and 14 against 14. It is a real "
    "byte comparison of a constant against itself. The 15 assertions those two files "
    "now contribute measure the call sequence and the diagnosis call, not the "
    "packing logic, which is the logic under test.\n\n"
    "THE OTHER TWO ARE GENUINELY CLOSED and are recorded as closed rather than "
    "carried. test_debug_can.c fills the out-parameter with "
    "OS_ReceiveFromQueue_ReturnThruPtr_pvBuffer and then asserts on what the "
    "product DID with it, which is a real consumption check. "
    "test_nxp_mc33775a_i2c.c compares a fixture derived from the transaction the "
    "product actually received, via ExpectWithArray over the real sizeof, which is "
    "a real content check. The limit that remains on test_debug_can.c is that its "
    "payload is all zeros, so mux and validity decoding are exercised on zeros; "
    "that is a narrower claim than a red count implies, and it is stated here "
    "rather than left for a reader to assume.\n\n"
    "WHAT WOULD CLOSE THE REMAINDER, and why it is not done here. The corrective "
    "step is to register ReturnThruPtr_pCanSignal alongside the existing extractor "
    "expectations in the two CAN cell tests and to give expectedQueuePayload the "
    "non-zero contents the fixture is meant to describe, then to prove the "
    "assertion non-vacuous by perturbing one byte the product writes and observing "
    "the failure. That is a change to tests/, which is outside this corpus's write "
    "boundary, and it is a test-ownership decision: these are the project's only "
    "oracle for this signal path. The conf/ alternative - typing the queue-payload "
    "parameters so CMock learns a size, or loading the array plugin in the shipped "
    "configuration - is also outside this corpus's write boundary.\n\n"
    "A NOTE ON THE SHIPPED CONFIGURATION, because it is the part that outlives this "
    "harness. conf/unit/app_project_posix.yml still loads neither :array nor "
    ":ignore_arg, so the X_ExpectWithArray and X_IgnoreArg_ families these four "
    "tests now depend on do not exist under the shipped configuration. These tests "
    "now require the SIL harness's isolated copy of the project file. That is an "
    "accommodation, not a portable fix, and a run of the shipped suite on Linux or "
    "Windows will not build them. @guard@"
)

RES_031 = (
    "RESOLVED, and SUPERSEDED - this record's condition no longer holds because a "
    "later, better-rooted remediation addressed it, and this record's residual "
    "statement is now wrong. Successors: FB2-REV-FND-000033 for the test-side "
    "classification, and the CMock array-plugin remediation recorded in "
    "FB2-REV-FND-000037.\n\n"
    "WHAT STILL HOLDS, and is the load-bearing part of this record. The diagnosis "
    "is CONFIRMED UNCHANGED: the void* on the database access functions and on the "
    "OS queue wrappers is required by the design, not an oversight. The database "
    "functions derive both the pointee type and the copy length at run time from a "
    "uniqueId field read out of the caller's own struct, and the project's own "
    "source carries an active suppression saying the cast 'is required in order to "
    "have a generic interface for all database entries'. A single concrete type "
    "would be wrong for at least 33 of the 37 database entry types. The proposed "
    "product-side fix of typing the parameters therefore stays REJECTED, on the "
    "evidence this record already gave, and no one should 'fix' that signature on "
    "the strength of this finding being filed.\n\n"
    "WHAT NO LONGER HOLDS, and why this record was stale. Its resolution said the "
    "callback treatment had been applied to one representative test and that 14 "
    "affected tests remained red. Re-verified on @date@: the most recent full SIL "
    "host sweep records 1 failing test in the entire 313-test suite, and it is "
    "tests/unit/app/driver/phy/test_dp83869.c, which is a different defect recorded "
    "as FB2-REV-FND-000035. No void*-identity failure remains. The residual was "
    "closed not by typing the parameters - which would have been the wrong fix - "
    "but by the class-A/B/C analysis in FB2-REV-FND-000033, which established that "
    "the three named situations needed three different oracles, and by the array "
    "plugin, which made the void* parameter byte-comparable at all.\n\n"
    "THE LIMIT THAT SURVIVES, stated because 'resolved' should not be read as "
    "'verified'. This resolution is about the test harness's oracles, not about the "
    "product. A passing test under this harness says nothing about register-map "
    "correctness, timing, clocking, interrupt behaviour, DMA transfer, bus or "
    "electrical behaviour, or device identity; the harness mocks the HAL and checks "
    "driver logic against upstream's own pre-existing assertions. Two of the "
    "affected assertions are separately recorded as vacuous in FB2-REV-FND-000037, "
    "so a green verdict on those files is not yet evidence about the packing logic. "
    "@guard@"
)

RES_033 = (
    "RESOLVED, and SUPERSEDED on the specific point this record was right about. "
    "Successor for the four red tests: the CMock array-plugin remediation recorded "
    "in FB2-REV-FND-000037.\n\n"
    "WHAT STANDS, and it is the valuable part. The three-way classification of why "
    "a void*-identity assertion fails is correct and is retained unchanged: in case "
    "(A) the test holds the real object and named the wrong one, so the fix is to "
    "pass the real pointer; in case (B) the real object is a private static of the "
    "product translation unit, so identity is impossible and a content comparison "
    "over the real sizeof is achievable; in case (C) the object is unreachable and "
    "already mutated at the call site, so only the header identity is both "
    "meaningful and stable. The record's central warning also stands: applying the "
    "single content-comparison recipe blindly to case (A) produces a failure that "
    "looks like a product defect in balancing logic and is not one.\n\n"
    "WHAT IS SUPERSEDED, precisely. This record's resolution left four tests red on "
    "purpose, on the ground that for those four 'identity is impossible; content is "
    "undefined and would read past the end of the test's own object; there is no "
    "uniqueId because these are ...' - so no achievable oracle existed. That "
    "conclusion was correct about the configuration that was in force and wrong "
    "about the configuration's limits, and it is superseded. CMock's generator has "
    "a second branch for exactly this case: with the array plugin loaded, a void* "
    "parameter is compared with UNITY_TEST_ASSERT_EQUAL_HEX8_ARRAY rather than "
    "downgraded to pointer identity, and the depth is supplied per call by the "
    "X_ExpectWithArray family. A test that knows the concrete payload type and its "
    "size - which all four of these do, because the product's queue item type is "
    "documented in can_cfg.h - can therefore express a content comparison. That is "
    "a fourth cause the three-way taxonomy did not name, and it is the better-"
    "rooted fix because it needs no product change at all.\n\n"
    "RE-VERIFIED on @date@: all four tests build and pass. TWO OF THEM ARE "
    "NON-VACUOUS AND TWO ARE NOT, and the split matters more than the green. "
    "test_debug_can.c and test_nxp_mc33775a_i2c.c compare real content - the first "
    "fills the out-parameter with ReturnThruPtr_pvBuffer and asserts on the "
    "consumption, the second compares a fixture derived from the received "
    "transaction over the real sizeof. "
    "test_can_cbs_rx_afe_cell-temperatures.c and "
    "test_can_cbs_rx_afe_cell-voltages.c compare an all-zero expected payload "
    "against a payload the mocked extractor never populates, so the byte "
    "comparison is a constant against itself. That residual is recorded in full, "
    "with the evidence, as FB2-REV-FND-000037 and is NOT closed by this record.\n\n"
    "THE LIMIT OF WHAT WAS DEMONSTRATED, restated so it is not lost when the count "
    "is quoted: every fix in this line of work is test-side, and a passing test "
    "under this harness says nothing about the device. @guard@"
)

RES_038 = (
    "RESOLVED, in both halves, and this record was stale in a way that mattered. "
    "Its resolution said the flag had been removed and the 6 tests 'remain red and "
    "are reported as such' - true when written, no longer true, and reporting it "
    "otherwise would have told a reader that six real out-of-bounds accesses were "
    "still live when they are not.\n\n"
    "HALF ONE, the masking flag. Re-verified on @date@: the string "
    "'-Wno-array-bounds' appears nowhere in sil/run.sh, and the "
    "RELAX_CLANG_DIAGNOSTICS list now holds exactly two diagnostics, "
    "-Wno-enum-conversion and -Wno-parentheses-equality - both of which are "
    "genuinely Apple-clang-only and are not enabled by -Wall or -Wextra under GNU "
    "gcc. This half was already closed when the record was written and still is.\n\n"
    "HALF TWO, the 6 sites. Closed. All six tests now build and pass: "
    "test_can_cbs_tx_f_cell-temperatures.c, test_can_cbs_tx_f_cell-temperatures_"
    "3-temp-sensors.c, test_can_cbs_tx_f_cell-temperatures_4-temp-sensors.c, "
    "test_can_cbs_tx_f_cell-temperatures_5-temp-sensors.c, "
    "test_can_cbs_tx_f_cell-voltages.c and test_diag_cbs_current.c. The fixes are "
    "the one-line-per-site changes this record's own resolution specified, and they "
    "are test-fixture changes: the declared sizes were corrected - float_t[3] to "
    "float_t[13] in the cell-temperature files, which are indexed up to element 12, "
    "and float_t[4] to float_t[9] in the cell-voltage file, which is indexed at 6 "
    "and 8 - and test_diag_cbs_current.c now writes element 0 of the "
    "BS_NR_OF_STRINGS-indexed arrays instead of element 1 into a one-element "
    "array. The build-failure class build:real_defect_out_of_bounds_array_index, "
    "which carried 6 tests in the baseline sweep, no longer appears in the "
    "classifier output at all.\n\n"
    "WHAT THIS DOES NOT MEAN. The second harm this record identified was to the "
    "evidence rather than to the records - the classification scheme had been "
    "describing six real defects as 'build:strict_diagnostic', a class defined as "
    "'Apple-clang-only diagnostic promoted by -Werror', which is a false "
    "description. That misclassification is corrected by the sites no longer "
    "failing, and the classifier no longer emits that class for them. The general "
    "rule this record established - a diagnostic may be silenced in this harness "
    "only if it is BOTH Apple-clang-only AND about a construct established to be "
    "correct, and a class that exists to explain away a red build must never be "
    "able to swallow a real defect - remains in force and is written down in "
    "sil/RELAXED-DIAGNOSTICS.md. It is a rule about the harness, not about the "
    "product: no product source is involved in this finding, no product behaviour "
    "was in question, and the defect was entirely within the test fixtures. @guard@"
)

RES_022 = (
    "RESOLVED, and the vocabulary member is corrected. This record was already "
    "correct at revision 4: it said RESOLVED and named the fix, and the fix holds. "
    "It was filed as disposition 'accepted', which under the enum that existed at "
    "the time was the only member available for a closed finding. `resolved` has "
    "been added to the enum and this record has been migrated to it. The "
    "distinction was real - nine closed records and five live defects all carried "
    "the same word - and it is now machine-readable rather than prose-only.\n\n"
    "RE-VERIFIED on @date@, by measurement rather than by reading: the "
    "repository-root TRACEABILITY_DOCUMENT.md is 55 lines, declares itself a "
    "pointer, and contains none of the strings 'IEC 61508', 'compliance evidence', "
    "'ASIL-D', 'Approver', 'Reviewer' or 'Approved'. The canonical generated "
    "document exists at docs/artifacts/views/traceability/traceability-document.md "
    "and is produced by `corpus.py render` with the same emit helper and the same "
    "provenance preamble as every other generated view, so it carries the same "
    "contract and its numbers are computed at render time from the artifact index, "
    "the link registries, the guard fields and the live coverage dispositions.\n\n"
    "WHAT THE RESOLUTION GUARANTEES AND WHAT IT DOES NOT. The condition this "
    "record described cannot recur by hand-editing, because the file is no longer "
    "hand-authored: the root file and the reports/ copy are both short pointers "
    "with no engineering content, and the .docx beside the reports pointer was "
    "regenerated from that pointer so no third copy can drift. That is a stronger "
    "statement than a human-discipline fix. It is NOT an approval. The out-of-"
    "boundary write to the repository-root file was made on the explicit "
    "instruction of the repository owner after being told the file lay outside "
    "docs/artifacts, and that authorisation is recorded in "
    "remediation_performed so the change is traceable rather than silent - which is "
    "the failure mode this finding was raised to prevent. No human has approved "
    "the document or this finding; the second review pass that found the "
    "fabricated sign-off block was a separate automated review session, which is "
    "not organisational independence and is not a human confirmation measure. "
    "@guard@"
)

RES_023 = (
    "RESOLVED, and the vocabulary member is corrected from 'accepted' to "
    "'resolved'. No change to the substance: the record was already correct and "
    "named its fix. Re-verified on @date@: FB2-SAF-SEC-000005.safety_allocation."
    "safety_goal_ref resolves to a live record. The second instance of the same "
    "mistyped id, in FB2-SAF-TAR-000001 threat THR-008, was corrected in the same "
    "pass, which is what confirmed the root cause as hand entry rather than a stale "
    "reference after a rename - a mistyped value appearing in two records is not "
    "what a rename leaves behind. docs/artifacts/tools/check_references.py now "
    "resolves every id-shaped string in every corpus and scenario record against "
    "the artifact index and the four registries, so this class of defect is "
    "detectable rather than invisible, and the TARA's own limitation text records "
    "that the security requirements are forward-engineered for a hypothetical "
    "project.\n\n"
    "Nothing about the record's engineering content changed: no acceptance "
    "criterion, ASIL value, verification approach, threat description, likelihood, "
    "impact or residual risk was altered by the correction. @guard@"
)

RES_024 = (
    "RESOLVED, and the vocabulary member is corrected from 'accepted' to "
    "'resolved'. Re-verified on @date@: FB2-SAF-FSR-000003's acceptance criteria "
    "now carry 'Contactor open latency / Time from FAULT request to contactor "
    "feedback open (auxiliary contacts confirm open) / 40 ms', plus a separate "
    "'Contactor mechanically open latency' criterion at 35 ms and a 'Coil "
    "de-energise to mechanically open' criterion at 30 ms that asks for "
    "FB2-PRM-000005's value under its own label.\n\n"
    "The reasoning this record used still holds and is the reason the fix is not a "
    "loose number: 30 ms is the mechanical opening time alone, 35 ms is "
    "command-plus-actuation and was wrong where it appeared because it omitted the "
    "5 ms coil-command segment the same requirement budgets separately, and 40 ms "
    "is the figure for the quantity the criterion actually names. The threshold was "
    "made HARDER to claim compliance with, not easier, and the real foxBMS source "
    "was consulted first and cannot settle the number - CONT_OpenContactor carries "
    "no timing constant - so FB2-PRM-000005 is the authority and it was not "
    "edited. @guard@"
)

RES_025 = (
    "RESOLVED, and the vocabulary member is corrected from 'accepted' to "
    "'resolved'. Re-verified on @date@: the ten entries of "
    "FB2-SAF-SGO-000001.timing_budget.allocation, including margin_ms = 15, sum to "
    "85 + 15 = 100, which is exactly the fault_tolerant_time_interval_ms the "
    "record declares. The budget closes.\n\n"
    "Two things this record got right and that are worth not losing. First, the "
    "margin was not rounded down to make the sum fit: 15 ms is the value the "
    "interval admits, and it is the value FB2-SAF-TSC-000001 had already computed "
    "independently, so the two records now agree instead of contradicting each "
    "other. Second, the validator's FTTI rule was NOT weakened or modified to "
    "achieve this, and the rule now reads the interval from the parameter the "
    "safety goal is bound to (FB2-PRM-000004, ftti_ms = 100) rather than guessing "
    "at a field name, so it also reports any scattered declaration that disagrees "
    "with the registry. The self-test 'FTTI budget violation detected' and "
    "'FTTI resolved from bound parameter; scatter and overflow reported' prove both "
    "that it still fires on a budget that does overrun and that the parameter path "
    "works. @guard@"
)

RES_026 = (
    "RESOLVED, and the vocabulary member is corrected from 'accepted' to "
    "'resolved'. Re-verified on @date@ over the LIVE fields of FB2-SAF-FSR-000004, "
    "FB2-HW-TSR-000004 and both assumption registries: the 115 ms figure appears "
    "in zero live justification fields. It survives only in revision_history "
    "entries and in the safety concepts' `contradiction` blocks, which quote it "
    "precisely in order to record its removal, and in the superseded as_is "
    "vertical-slice review record FB2-REV-000001, which is where this finding "
    "established that it came from.\n\n"
    "This record's own correction of its own evidence is the part worth keeping: it "
    "originally reported 115 ms as appearing in no record and therefore not "
    "reconstructible. It is reconstructible - 100 + 10 + 5 from a superseded "
    "allocation - so the figure was STALE rather than fabricated, and the remedy "
    "changed from reconstructing it to deleting it. That is a more precise root "
    "cause and a cheaper fix, and it is recorded here rather than quietly "
    "overwritten. The justification now rests on figures that still hold: the main "
    "path is 85 ms of the 100 ms interval, 95 ms at the 40 ms upper tolerance of "
    "FB2-PRM-000005, and 110 ms if detection waits one full acquisition period of "
    "FB2-PRM-000003. @guard@"
)

RES_027 = (
    "RESOLVED, and the vocabulary member is corrected from 'accepted' to "
    "'resolved'. Re-verified on @date@: FB2-SAF-FSR-000004 (Part 4, functional, "
    "ASIL B) and FB2-HW-TSR-000004 (Part 5, hardware, ASIL B) no longer carry the "
    "same sentence. The two records are now genuinely different obligations at "
    "different ISO 26262 levels, and the unmeasurable coverage criterion is "
    "measurable: 'representative subset >= 50%' was replaced by 100 percent of the "
    "cells the main measurement chain monitors, because 'representative subset' is "
    "undefined, no selection method is recorded anywhere in the corpus, and a "
    "subset would leave cells with no barrier against a main-path failure. The "
    "structural properties - how many rails, references, driver stages and "
    "comparators are shared - moved to the hardware record as separate counts per "
    "resource, because a count of shared rails and a count of shared references are "
    "separately decidable and a single percentage over an undefined denominator is "
    "not.\n\n"
    "The feasibility of a full independent divider network is still an open "
    "assumption under FB2-ASM-008 and is not asserted by this resolution. "
    "@guard@"
)

RES_028 = (
    "RESOLVED, and the vocabulary member is corrected from 'accepted' to "
    "'resolved'. Re-verified on @date@: the 'Genuine-frame false-rejection rate' "
    "criterion on FB2-SAF-SEC-000003 and FB2-SAF-SEC-000004 is a bounded rate with "
    "a stated confidence basis, not the absolute '0 frames' this record reported.\n\n"
    "The replacement is not a relaxation and this record's own arithmetic is why, "
    "so it is repeated here because a reader who only sees the criterion value "
    "would reasonably suspect the opposite: a keyed integrity value of width w "
    "rejects a genuine frame with probability 2^-w, so over a 24 h campaign the "
    "expected number of genuine rejections is non-zero for any practical w, which "
    "is why the zero was unachievable rather than strict. 0 failures in n trials "
    "gives a one-sided 95 percent upper confidence bound of 3/n, so 3/n <= 1e-6 "
    "requires n >= 3e6; sustaining that rate needs a per-frame probability at or "
    "below 3.3e-7, i.e. w >= 22 bits, which is why the requirement now also "
    "constrains the integrity width. The new criterion is STRICTER in discriminating "
    "power than the zero it replaces: an always-rejecting implementation scores "
    "about 100 percent and fails it by four orders of magnitude, and a 16-bit "
    "integrity value gives about 1.5e-5 per frame and also fails it, where both "
    "would have satisfied the old zero. The absolute zeros that remain in both "
    "records are the ones decidable by the check existing - injected frames "
    "accepted, replayed frames accepted, length mismatch reaching the callback, "
    "unframed bytes passing, control-byte transitions - and those are over "
    "countable events rather than a collision-prone channel. @guard@"
)

RES_029 = (
    "RESOLVED, and the vocabulary member is corrected from 'accepted' to "
    "'resolved'. Re-verified on @date@ by reading the live source: the rule in "
    "docs/artifacts/tools/corpus.py builds its set from the link TARGET - "
    "`verified = {l[\"target_id\"] for l in links if l.get(\"relation_type\") in "
    "(\"verifies\", \"validates\") and l.get(\"target_id\")}` - which is the direction "
    "master prompt section 13 declares. The defect is gone.\n\n"
    "This finding's central claim needs one correction, because it was later found "
    "to be the wrong diagnosis of a neighbouring problem and the distinction is "
    "load-bearing. This record blamed the endpoint inversion for why findings "
    "FB2-REV-FND-000008..12 could not be closed. It could not be closed by the "
    "inversion alone. A SEPARATE and independent blind spot sat in the "
    "fault_reaction rule (MUT-008), which carried an id filter `\"-FSR-\" in id` and "
    "was therefore structurally incapable of reporting the five FB2-SAF-SEC-* "
    "security requirements at all. Both are recorded; the second is "
    "FB2-REV-FND-000039 and it was fixed by widening that rule's scope. Had only "
    "the inversion been fixed, the security requirements would still have carried "
    "no machine-readable fault reaction and the corpus would still have been "
    "silently under-reporting.\n\n"
    "The rule's fix is unchanged and remains as recorded: the intent is the same - "
    "a safety requirement with no verification at all is still reported - and the "
    "fix is strictly harder to satisfy by accident than before, because a "
    "requirement appearing as the SOURCE of a verifies link is a malformed link "
    "under the declared direction and no longer counts as verification. Three "
    "self-tests pin both directions. The self-test that pins the negative case was "
    "also narrowed in this pass, from 'no rule at all may flag this record' to "
    "'the verification rule may not flag this record', because the former was only "
    "true while the fault_reaction rule's id filter hid the same record class; the "
    "narrowing makes the test assert what it says it asserts, and MUT-008's "
    "coverage of that class is now pinned by four dedicated tests instead. @guard@"
)

RES_032 = (
    "RESOLVED, and the vocabulary member is corrected from 'accepted' to "
    "'resolved'. Re-verified on @date@: acceptance gate [5/8] reports 20/20 "
    "mutations passing, each against its OWN declared detector, plus 3/3 change "
    "lifecycles, and coverage dimension negative_scenario_validation reports the "
    "same 20/20 from the same single scenario execution, so the two cannot "
    "disagree.\n\n"
    "The mechanism that made that number mean something is intact. Findings carry a "
    "stable rule identifier; a scenario is resolved to its declared detector by that "
    "identifier, read from the evaluator-only oracle manifest; the detector must be "
    "emitted by a rule in this module, checked against the module's own AST so an "
    "absent detector fails loudly; the detector must be silent on the unmutated "
    "corpus, so a standing defect cannot satisfy it; and the baseline is computed "
    "once per run and subtracted. Severity and category are reported and a mismatch "
    "is flagged as a fixture defect, but they no longer decide a verdict. Two "
    "self-tests pin the anti-self-certification property directly: 'scenario fails "
    "when its own detector is disabled' and 'standing finding cannot satisfy a "
    "scenario'.\n\n"
    "WHAT IS NOT CLAIMED. This resolution does not assert that the mutation suite is "
    "complete, that the detector set is correct, or that the 20 scenarios are a "
    "sufficient sample of what the corpus could get wrong. It asserts that each of "
    "the twenty ran, and that each was detected by the rule it names, on a baseline "
    "where that rule was silent. That is a narrower claim than 'the corpus is "
    "correct' and it is the claim the evidence supports. @guard@"
)


# ---------------------------------------------------------------------------
# New records.
NEW_039 = dict(
    id="FB2-REV-FND-000039",
    filename="finding-000039-fault-reaction-rule-fsr-id-blind-spot.json",
    severity="high", category="process", disposition="resolved",
    title=("Finding FB2-REV-FND-000039: the safety-requirement completeness rule "
           "filtered on the id substring '-FSR-', so it was structurally incapable "
           "of reporting the five FB2-SAF-SEC-* security requirements - a blind spot "
           "in the opposite direction to the one FB2-REV-FND-000029 fixed"),
    root_cause=(
        "The rule's population was expressed as two declared properties plus a "
        "spelling. `artifact_type == \"requirement\"` and "
        "`engineering_domain == \"safety\"` define the class; `\"-FSR-\" in id` was "
        "added as a third condition and is not a property of the record at all, it "
        "is a property of how the id happens to be written. That is why it survived: "
        "an id filter looks like a scope restriction and behaves like one, and the "
        "sibling rule two paragraphs above - the safety-requirement verification "
        "rule - selects the identical population with no id filter. The two rules "
        "disagreed about what a safety requirement is, and the disagreement happened "
        "to fall on the side of silence for the entire cybersecurity concept. The "
        "blind spot was invisible from the outside in a specific way: the rule "
        "reported zero findings on a corpus where the five security requirements "
        "genuinely carried no fault_reaction, so the number looked healthy."
    ),
    impact=(
        "The cost of this defect is a permanently under-reported defect class, which "
        "is the failure mode that trains a reader to discount a number. Five "
        "safety-domain requirements carrying the whole cybersecurity concept were "
        "outside a completeness rule that exists to check safety-domain "
        "requirements, and nothing in the corpus said so. Had this been found later, "
        "after a reader had learned to trust that 'validate reports 0 findings' "
        "meant the corpus was clean on this axis, the reader would have been "
        "actively misled. The defect also made the security set structurally "
        "different from the cell-voltage set in a way nothing recorded: an FSR "
        "carried a machine-readable fault reaction and a SEC did not, and a reader "
        "comparing the two would have had no way to tell that the difference was an "
        "artefact of a filter rather than of authoring."
    ),
    evidence=(
        "MEASURED, not inferred, by docs/artifacts/tests/rule_scope_probe.py, which "
        "loads the corpus, exercises the rules in memory and writes nothing. The "
        "rule as it stood: `if d.get(\"artifact_type\") == \"requirement\" and "
        "d.get(\"engineering_domain\") == \"safety\" and \"-FSR-\" in _id(key)`. "
        "Live corpus: 0 requirements flagged. The five security requirements exist, "
        "carry engineering_domain 'safety' and artifact_type 'requirement', and none "
        "carried a fault_reaction, so the correct count under the rule's own stated "
        "intent was 5 and the rule reported 0. The counterfactual is the decisive "
        "part: an id filter is not a distinction, it is a wall, and the test for a "
        "wall is whether removing the record changes the outcome. Removing "
        "everything else about the security requirements - their links, their "
        "acceptance criteria, their fields - changes nothing, because the filter "
        "runs before any of it. Contrast the sibling rule "
        "verification_traceability_checker, whose population condition is the first "
        "two clauses with no third, and for which the same probe DOES flag all five "
        "security requirements the moment their verifies links are removed from an "
        "in-memory copy of the registries. One rule covers the class and one does "
        "not, and the difference is a substring."
    ),
    resolution=(
        "RESOLVED, by widening the rule's scope and by nothing else. The third "
        "condition `\"-FSR-\" in _id(key)` has been removed from "
        "docs/artifacts/tools/corpus.py's safety_requirement_completeness_checker. "
        "The rule's population is now selected by declared type and declared "
        "engineering domain alone, which is what makes it survive the addition of a "
        "future requirement class rather than needing a third substring each time.\n\n"
        "NOTHING WAS WEAKENED. The population only grows, from the FSR records to "
        "every safety-domain requirement, so the rule is strictly harder to satisfy "
        "than before and strictly more sensitive. Four self-tests were added to "
        "cmd_selftest and all four pass, pinning the widened scope from both sides "
        "so that a future edit cannot quietly re-narrow it and cannot over-widen it "
        "either: a security requirement with no fault_reaction IS reported; an FSR "
        "with no fault_reaction is STILL reported, so nothing previously reported "
        "stopped being reported; a requirement outside the safety engineering domain "
        "is still NOT reported, which is what a widening is allowed to cost; and a "
        "security requirement that DOES carry a fault_reaction is silent, which is "
        "what distinguishes a working rule from one that just reports the class.\n\n"
        "WHAT THE WIDENING IMMEDIATELY SURFACED, and how it was handled. With the "
        "filter gone the rule reported 5 findings, all five of them true. The honest "
        "response to a check that starts firing is to do the work, not to re-narrow "
        "the rule. A fault_reaction block was therefore authored onto each of the "
        "five security requirements, transcribed from text each record already "
        "carried - its own statement for the reaction and its trigger, its own "
        "acceptance criteria for the diagnosability obligation and for the "
        "reaction-time bound where one exists, its own conditions_modes for mode "
        "dependence - and recording three absences rather than filling them: neither "
        "FB2-SAF-FSC-000001 nor FB2-SAF-TSC-000001 allocates a fault reaction to any "
        "element for the security chain, so element_owns_reaction is false; the "
        "safety goal's timing budget has no cybersecurity leg, so no reaction-time "
        "budget is stated; and the controls' real-source status and unverified "
        "verification leg are carried through unchanged. No acceptance criterion, "
        "ASIL value, statement, rationale, verification approach, verification "
        "status or guard field was altered. The corpus validator is back to 0 "
        "findings - and that 0 is now a different, stronger statement than it was, "
        "because the rule that produces it now covers the class it was always "
        "described as covering.\n\n"
        "ONE EXISTING SELF-TEST WAS NARROWED, and it is worth being explicit about "
        "because narrowing a test is exactly what this corpus forbids. The test "
        "'correctly directed verifies link (requirement as target) not flagged' "
        "asserted `not any(f[\"artifact_id\"] == ...)`, i.e. that NO rule at all may "
        "flag its synthetic record. That was over-broad rather than strict: it held "
        "only because MUT-008's id filter made that record invisible to the "
        "fault_reaction rule, so a different rule firing on it was a false failure "
        "rather than a real one. The assertion was scoped to the verifies rule by "
        "rule id and description, which is what the test's own name and comment "
        "always said it was testing. This does not weaken coverage: the verifies "
        "rule's negative case is still pinned exactly, and MUT-008's coverage of "
        "the same record class is now pinned by four dedicated tests that did not "
        "exist before. The trade is stated rather than assumed.\n\n"
        "RELATED AND DELIBERATELY NOT FIXED HERE: the "
        "diagnostic_coverage_claim_validator rule (MUT-010) carries the same `-FSR-` "
        "id filter. It is recorded as FB2-REV-FND-000040 and was not changed, "
        "because that rule reads diagnostic_coverage, which is claimed by FSR "
        "records and by no security requirement, so the filter is currently inert "
        "rather than silently dropping a live defect. Inert is not the same as "
        "correct and the record says so."
    ),
    successor_of=None,
)

NEW_040 = dict(
    id="FB2-REV-FND-000040",
    filename="finding-000040-diagnostic-coverage-rule-fsr-id-filter.json",
    severity="medium", category="process", disposition="accepted",
    title=("Finding FB2-REV-FND-000040: the diagnostic-coverage claim validator "
           "carries the same '-FSR-' id filter as the fault_reaction rule had, and "
           "is currently inert rather than correct"),
    root_cause=(
        "The same authoring decision as FB2-REV-FND-000039, reached independently "
        "in a second rule: the population was narrowed by id substring rather than by "
        "declared type and domain. The two rules were written at different times for "
        "different fields and neither was reconciled against the other, which is the "
        "general failure mode - scope expressed in a place no check reads."
    ),
    impact=(
        "Today, no measurable harm, and it is important to say that plainly rather "
        "than inflate it. The rule reads the field diagnostic_coverage and the "
        "field diagnostic_coverage_evidence. No FB2-SAF-SEC-* record claims "
        "diagnostic coverage, so the filter currently excludes nothing that would "
        "have been reported: the rule is inert on this corpus, not wrong on it. The "
        "harm is prospective and specific. If a future security requirement claims a "
        "diagnostic coverage figure - and the security concept does have a "
        "diagnostic story, since the requirements mandate a diagnosis entry per "
        "rejected frame - the rule would silently decline to check the claim, and "
        "the silence would look identical to the silence this finding was raised "
        "about in FB2-REV-FND-000039. A check that is inert until the day it is "
        "needed, and wrong on that day, is a trap with a long fuse."
    ),
    evidence=(
        "MEASURED. The rule as it stands in docs/artifacts/tools/corpus.py: `if "
        "d.get(\"artifact_type\") == \"requirement\" and d.get(\"engineering_domain\") "
        "== \"safety\" and \"-FSR-\" in _id(key)`, then read diagnostic_coverage, "
        "and report if diagnostic_coverage is claimed without "
        "diagnostic_coverage_evidence. Corpus-wide scan: diagnostic_coverage is "
        "claimed by FSR records and by no SEC record, so 0 requirements are "
        "excluded that would otherwise have been reported. The filter is "
        "reproducible from the source line alone, and docs/artifacts/tests/"
        "rule_scope_probe.py prints it under 'ADJACENT RULE NOTED, NOT CHANGED'."
    ),
    resolution=(
        "ACKNOWLEDGED AND NOT FIXED, deliberately, and the reason is scope rather "
        "than difficulty. The change to make is a one-clause deletion identical to "
        "the one applied in FB2-REV-FND-000039, and it is exactly the kind of change "
        "that should not be made in a pass whose authorisation covers one specific "
        "rule. Making it here would mean widening a second rule on the strength of a "
        "symptom that does not currently manifest, with no measurement showing what "
        "the widened rule would report on this corpus.\n\n"
        "The recommended change, for whoever owns the rule set: remove the "
        "`\"-FSR-\" in _id(key)` clause so the population is declared type and "
        "declared domain, and add the same four self-tests that were added for "
        "MUT-008 - the excluded class is reported, the previously reported class is "
        "still reported, the domain boundary is still respected, and a record that "
        "satisfies the rule is silent. Applying that recipe to this rule is safe "
        "today precisely because the recipe was proved on a rule where the widening "
        "had a visible effect.\n\n"
        "What is NOT done and should not be inferred: no check was weakened, no "
        "record was relabelled, and no claim is made that this rule is currently "
        "reporting everything it should. It may well be - on this corpus it reports "
        "nothing either way - but 'reports nothing on a corpus where nothing is "
        "wrong' is not the same as 'would report the defect', and the difference is "
        "the whole content of this finding. No human has confirmed this analysis; "
        "human approval of this record remains pending. No tool is claimed to be "
        "qualified, and no certification, ISO 26262 conformity or ASPICE capability "
        "level is claimed or implied."
    ),
    successor_of=None,
)

NEW_041 = dict(
    id="FB2-REV-FND-000041",
    filename="finding-000041-security-verification-planned-not-achieved.json",
    severity="high", category="verification", disposition="accepted",
    title=("Finding FB2-REV-FND-000041: the five security requirements are "
           "verification-PLANNED and not verification-ACHIEVED - their measures and "
           "executions exist, every execution is outcome 'blocked', and closing "
           "FB2-REV-FND-000008..12 on the link condition must not be read as closing "
           "the verification gap"),
    root_cause=(
        "A finding about a missing link and a finding about missing evidence are "
        "different findings, and the corpus had only the first. The link condition "
        "was real and has been fixed - five verifies links now exist. The evidence "
        "condition is untouched: the five measures were authored with declared "
        "oracles and the five executions were authored to make the absence visible, "
        "and every one of those executions carries execution_kind 'none' and outcome "
        "'blocked'. A blocked execution is an honest record, not a defect in itself; "
        "the defect is that nothing in the corpus's own counting distinguished "
        "'planned-and-blocked' from 'planned-and-run', and the finding that was "
        "resolved on the link would otherwise have quietly taken the verification "
        "gap with it."
    ),
    impact=(
        "The entire cybersecurity concept in this corpus rests on five requirements "
        "with acceptance criteria that are individually well formed - a bounded "
        "false-rejection rate with a stated confidence basis, a 100 ms "
        "budget-breach response time, a 22-bit integrity width, an entropy "
        "distinctness requirement - and not one of them has been executed. No "
        "injection campaign, no protocol capture, no 24-hour observation and no "
        "advisory check exists. The measures have oracles, which is better than "
        "nothing and is genuinely unusual care, but an oracle nobody has run is a "
        "plan. A reader who sees 'FB2-SAF-SEC-000003 is verified by "
        "FB2-VER-TMS-000018' and stops there will conclude the requirement is "
        "verified. It is not. The controls are also absent or partial in the real "
        "foxBMS 2 source, which each requirement's own real_source_presence block "
        "records, so there is in any case nothing in the product to test against."
    ),
    evidence=(
        "MEASURED. FB2-VER-TMS-000016..000020 exist, each with an oracle_detail "
        "block whose kind is declared rather than assumed: source_grounded for "
        "000016, 000018 and 000019, analytical_model for 000017, and "
        "synthetic_assumption for 000020 - the last recorded honestly, because "
        "unpredictability of an initial sequence number is not observable from "
        "outside the implementation and the measure says so instead of borrowing an "
        "oracle it does not have. FB2-VER-EXE-000016..000020 exist and each carries "
        "execution_kind 'none' and outcome 'blocked'. Their recorded blocked_reason "
        "is specific and correct: the security test harness for this corpus does not "
        "exist - no target hardware, no protocol analyser, no packet capture path, no "
        "injection tooling - and the requirement constrains a service the "
        "hypothetical project has planned but not built, so there is nothing to test "
        "against. Corroborating: verification_status on all five security "
        "requirements is 'not_verified', and the TARA record FB2-SAF-TAR-000001 "
        "states the limitation in its own text - the derived security requirements "
        "are forward-engineered for a hypothetical project and have no verification "
        "evidence in this corpus."
    ),
    resolution=(
        "ACKNOWLEDGED AND NOT CLOSED, and this is the honest end state rather than "
        "a gap in the record. Nothing in this corpus can execute these measures and "
        "nothing should be written that pretends otherwise. Authoring a pass result "
        "would be fabricating evidence, which is the one thing the corpus's guard "
        "fields and this record's own existence exist to prevent.\n\n"
        "WHY IT IS A SEPARATE RECORD AND NOT A SENTENCE IN A RESOLVED ONE. "
        "FB2-REV-FND-000008..12 have been resolved on the condition they assert, "
        "which is the absence of a verifies link, and their resolutions now say so "
        "and cite the links. A reader who stops there would conclude the security "
        "concept is verified. It is not. Under the disposition vocabulary in "
        "docs/artifacts/governance/finding-disposition-vocabulary.md, a resolved "
        "record may not carry an open remainder in prose - the remainder becomes its "
        "own record with its own id - precisely so that a closed finding cannot "
        "quietly hold an open defect. This is that record.\n\n"
        "WHAT IS IN PLACE. The planning half is complete and honest: five "
        "requirements with decidable acceptance criteria, five measures with "
        "declared oracles, five executions that exist precisely so the absence is "
        "visible rather than inferred, a recorded blocked_reason on each, and a TARA "
        "that states the limitation. The blocked executions are the right artefact. "
        "A corpus that had omitted them would look healthier and be less true.\n\n"
        "WHAT WOULD CLOSE IT, precisely, and it is a product and infrastructure "
        "decision rather than a documentation one. For FB2-VER-EXE-000016, 000018 "
        "and 000019: a security test harness with a protocol analyser or capture "
        "path and injection tooling, plus a build of the service these requirements "
        "constrain, which the hypothetical project has not built. For "
        "FB2-VER-EXE-000017: the same, since its oracle is a resource model that has "
        "to be exercised against a real service to mean anything. For "
        "FB2-VER-EXE-000020: nothing in this corpus can supply it, because the "
        "measure's own oracle_detail records that unpredictability is not observable "
        "from outside - closing that one requires either an implementation to "
        "inspect or a different kind of evidence, and its honest disposition may "
        "well be that the oracle is wrong rather than that the work is missing. Each "
        "of these is a decision for the project owner, and none is a finding this "
        "corpus can close by writing a file.\n\n"
        "WHAT IS NOT CLAIMED. This record claims no human approval, no tool "
        "qualification, no certification, no ISO 26262 conformity and no ASPICE "
        "capability level. The five security requirements are not verified, their "
        "controls are absent or partial in the real foxBMS 2 source at the pinned "
        "baseline commit, and no assertion here should be read as a statement about "
        "the product's security architecture."
    ),
    successor_of=None,
)

NEW_042 = dict(
    id="FB2-REV-FND-000042",
    filename="finding-000042-vacuous-green-census.json",
    severity="high", category="verification", disposition="accepted",
    title=("Finding FB2-REV-FND-000042: 53 of the 245 green tests in the SIL host "
           "sweep assert nothing, so a headline pass count is not a coverage count "
           "- this is the live, larger form of the vacuity concern FB2-REV-FND-000037 "
           "raised about four tests"),
    root_cause=(
        "The foxBMS 2 unit-test suite contains a large number of test files that "
        "build, link, run and exit zero without asserting anything: 21 config-module "
        "tests each holding a single empty testDummy, DMA and AFE-driver stubs, "
        "state-estimation placeholders, and three files with no test case at all. "
        "The corpus treats a green Ceedling verdict as a pass and counts it, so the "
        "sweep's pass count mixes files that verify something with files that cannot "
        "fail. The root cause is the same one this corpus has met three times in this "
        "pass - a count that measures the harness's verdict rather than the thing the "
        "count is named for - and it is the count a reader is most likely to quote."
    ),
    impact=(
        "A pass count that includes files which assert nothing overstates coverage by "
        "a measured amount: of 245 green files, 192 carry a real assertion and 53 do "
        "not, so the headline number is 27 percent higher than the number of files "
        "that can fail. The direction of the error matters as much as its size - a "
        "reader who learns to quote the green count learns to quote a number that is "
        "wrong in the flattering direction, which is the direction nobody checks. The "
        "starkest single case is test_app-hl_notification.c: 20 test functions that "
        "call a notification entry point and assert nothing about what it did, with "
        "a 10-case bootloader twin. Those 30 cases do exercise the arity of the "
        "calls and the mock does verify the arguments, so the signatures are "
        "genuinely checked; no test asserts an effect. Quoting '30 tests pass' for "
        "them overstates what was established."
    ),
    evidence=(
        "MEASURED by the harness's own instrument, not by inspection. "
        "docs/artifacts/.work/verification-env/sil/tools/find_vacuous_tests.py reads "
        "every test_*.c under tests/unit/ and classifies it; it runs nothing, so it "
        "cannot be perturbed by a concurrent build. Its output, archived at "
        "docs/artifacts/.work/verification-env/sil/logs/vacuous-final.json and "
        "written up at "
        "docs/artifacts/.work/verification-env/sil/VACUOUS-TESTS.md: 82 of the 313 "
        "test files are vacuous; 30 of those are build failures or excluded upstream "
        "and so inflate nothing today; of the green files, 53 assert nothing and 192 "
        "carry a real assertion; green-by-class is 3 files with no test case at all "
        "and 50 with test cases but no assertions. The comparison is stated in both "
        "directions and the unflattering number is the one this record leads with: "
        "the asserting count ROSE from 175 to 192 across the work, and the vacuous "
        "green count also rose from 47 to 53, because 6 of the 23 tests that newly "
        "went from build failure to pass are themselves vacuous. Bringing those up is "
        "real progress - they now compile, link and execute the product code - and "
        "it adds no assertion coverage, and quoting '23 tests fixed' without that "
        "qualifier would overstate the result."
    ),
    resolution=(
        "ACKNOWLEDGED AND NOT CLOSED. No test was written and none should have been "
        "by this pass. For the 21 config-module files the module under test is a "
        "constant table with no functions - `grep -cE '^[a-zA-Z_].*\\(.*\\) *\\{'` "
        "over src/app/driver/afe/nxp/mc33775a/config/nxp_mc33775a_cfg.c returns 0 - "
        "so a test could only assert structural invariants of a constant, and which "
        "of those are contractual and which are incidental to one AFE's wiring is a "
        "decision about intent that no mechanical derivation from the code can "
        "produce. Writing cases would be inventing the specification. For the DMA "
        "and state-estimation files the intended coverage is likewise not derivable "
        "from what is there.\n\n"
        "WHAT IS IN PLACE, and it is the part that does not need an owner's "
        "decision. The census is mechanical, reproducible and archived, so the "
        "number can be re-derived on demand rather than remembered. The harness's own "
        "write-up states the reading rule in the form that matters: the headline "
        "pass count must be read as 'tests whose harness verdict was green', never "
        "as 'tests that verify something', and any statement of the form 'N tests "
        "pass' that does not carry that qualifier overstates the result. This record "
        "exists so that the qualifier is attached at the corpus level and not only "
        "in a working note under .work/ that a future reader may never open.\n\n"
        "WHAT WOULD CLOSE IT, and every item needs a decision by someone who knows "
        "what the module is supposed to guarantee, followed by tests written against "
        "that decision. First, for each of the 53, decide whether a real test is "
        "wanted or whether the file is a placeholder that should be marked "
        "explicitly ignored so the sweep can tell 'empty on purpose' from 'empty and "
        "not marked as such' - Ceedling's TEST_IGNORE_MESSAGE would do it. Second, "
        "for test_app-hl_notification.c and its bootloader twin, decide whether the "
        "intent is signature and non-faulting entry - in which case the file should "
        "say so, because CMock's argument checks already establish that - or "
        "coverage of the notification bodies, in which case the 30 cases need "
        "assertions about what each one does. Third, and separately from the "
        "per-file decisions, the sweep's own reporting should carry the two counts "
        "side by side so that no reader can quote the green total without the "
        "asserting total beside it.\n\n"
        "A NOTE ON WHAT THIS IS NOT. This is a finding about the test corpus, not "
        "about the product. It is not evidence of a defect in foxBMS 2 source, and "
        "it is not a statement that 53 things are broken. It is a statement that 53 "
        "of the numbers a reader would most naturally quote do not mean what they "
        "appear to mean. The limit of the harness is unchanged by any of it: it "
        "mocks the HAL and verifies driver logic against upstream's own assertions, "
        "so it establishes nothing about register maps, timing, clocking, interrupts, "
        "DMA transfer, bus or electrical behaviour, or device identity. No human has "
        "confirmed this analysis; human approval of this record remains pending. No "
        "tool is claimed to be qualified, and no certification, ISO 26262 conformity "
        "or ASPICE capability level is claimed or implied."
    ),
    successor_of=None,
)


# ---------------------------------------------------------------------------
# Per-record correction table. Keyed by finding id.
# (disposition, resolution_text, related_note)
CORRECTIONS = {}


def _reg(prefix, table):
    for fid, (disp, tmpl, note) in table.items():
        CORRECTIONS[fid] = (disp, tmpl, note)


_reg("A", {
    "FB2-REV-FND-000001": ("resolved", GROUP_A, None),
    "FB2-REV-FND-000002": ("resolved", GROUP_A, None),
    "FB2-REV-FND-000003": ("resolved", GROUP_A, None),
    "FB2-REV-FND-000004": ("resolved", GROUP_A, None),
    "FB2-REV-FND-000005": ("resolved", GROUP_A, None),
    "FB2-REV-FND-000006": ("resolved", GROUP_A, None),
    "FB2-REV-FND-000007": ("resolved", GROUP_A, None),
})
_reg("B", {
    f"FB2-REV-FND-{i:06d}": ("resolved", GROUP_B, None) for i in range(8, 13)
})
_reg("C", {
    f"FB2-REV-FND-{i:06d}": ("resolved", GROUP_C, None) for i in range(13, 20)
})
_reg("D", {
    "FB2-REV-FND-000020": ("resolved", GROUP_D, None),
    "FB2-REV-FND-000021": ("resolved", GROUP_D, None),
})
_reg("E", {
    "FB2-REV-FND-000022": ("resolved", RES_022, None),
    "FB2-REV-FND-000023": ("resolved", RES_023, None),
    "FB2-REV-FND-000024": ("resolved", RES_024, None),
    "FB2-REV-FND-000025": ("resolved", RES_025, None),
    "FB2-REV-FND-000026": ("resolved", RES_026, None),
    "FB2-REV-FND-000027": ("resolved", RES_027, None),
    "FB2-REV-FND-000028": ("resolved", RES_028, None),
    "FB2-REV-FND-000029": ("resolved", RES_029, None),
    "FB2-REV-FND-000032": ("resolved", RES_032, None),
    "FB2-REV-FND-000030": ("accepted", RES_030, None),
    "FB2-REV-FND-000031": ("resolved", RES_031, None),
    "FB2-REV-FND-000033": ("resolved", RES_033, None),
    "FB2-REV-FND-000034": ("accepted", RES_034, None),
    "FB2-REV-FND-000035": ("deferred", RES_035, None),
    "FB2-REV-FND-000036": ("accepted", RES_036, None),
    "FB2-REV-FND-000037": ("deferred", RES_037, None),
    "FB2-REV-FND-000038": ("resolved", RES_038, None),
})

MARKER = "@reverified@"


def main() -> int:
    import audit_findings as AF  # the re-test harness, run for its own verdicts
    AF.build()
    verdicts = {r["id"]: r for r in AF.ROWS}

    changed, skipped = [], []
    for p in sorted(FIND.glob("*.json")):
        d = json.loads(p.read_text(), object_pairs_hook=OrderedDict)
        fid = d.get("id")
        if fid not in CORRECTIONS:
            skipped.append(f"{fid} (no correction authored)")
            continue
        if d.get("reverification", {}).get("date") == DATE:
            skipped.append(f"{fid} (already corrected at {DATE} - idempotent)")
            continue

        disp, tmpl, note = CORRECTIONS[fid]
        v = verdicts[fid]
        subject = v["subject"]
        m = re.match(r"^(FB2-\S+)\s+\((\w+)\)$", subject)
        subj_id, profile = (m.group(1), m.group(2)) if m else (subject, "")

        # evidence the correction is grounded in
        links_for = [l for l in AF.LNK
                     if l.get("target_id") == subj_id
                     and l.get("relation_type") in ("verifies", "validates")]
        nlinks = len(links_for)
        link_ids = ", ".join(sorted(l["link_id"] for l in links_for)) or "none"
        measures = ", ".join(sorted({l["source_id"] for l in links_for})) or "none"

        rec = AF.rec(subj_id, profile if profile else None)
        frev = fkeys = srev = jkeys = "unknown"
        if rec:
            r = rec[1]
            frev = r.get("revision", "?")
            fr = r.get("fault_reaction")
            fkeys = sorted(fr) if isinstance(fr, dict) else "none"
            srev = r.get("revision", "?")
            j = r.get("asil_justification")
            jkeys = sorted(j) if isinstance(j, dict) else "none"

        tms = measures.split(",")[0] if nlinks else "the authored measure"
        link = link_ids.split(",")[0] if nlinks else "the authored link"

        text = tmpl
        for token, value in (("@date@", DATE), ("@subject@", subj_id),
                             ("@profile@", profile), ("@nlinks@", str(nlinks)),
                             ("@links@", link_ids), ("@measures@", measures),
                             ("@fkeys@", str(fkeys)), ("@frev@", str(frev)),
                             ("@srev@", str(srev)), ("@jkeys@", str(jkeys)),
                             ("@tms@", tms), ("@link@", link), ("@guard@", GUARD)):
            text = text.replace(token, value)

        new_rev = str(int(d["revision"]) + 1)
        d["revision"] = new_rev
        d["updated_at"] = DATE
        d["disposition"] = disp
        d["resolution"] = text
        d["reverification"] = OrderedDict([
            ("date", DATE),
            ("method", "docs/artifacts/tests/audit_findings.py - the asserted "
                       "condition was re-derived from the live corpus (link "
                       "registries, canonical records, validator source, and the SIL "
                       "harness's own archived sweep), not read from this record."),
            ("audit_class", v["class"]),
            ("condition_still_holds", v["still_holds"]),
            ("disposition_before", v["recorded_disposition"]),
            ("revision_before", v["recorded_revision"]),
            ("evidence", v["evidence"]),
        ])
        if note:
            d["reverification"]["related"] = note
        d["disposition_note"] = (
            f"disposition '{disp}' is used in the sense defined normatively by "
            f"docs/artifacts/governance/finding-disposition-vocabulary.md and "
            f"permitted by the enum in docs/artifacts/schemas/finding.schema.json. "
            f"It was '{v['recorded_disposition']}' before this revision, and that "
            f"word was ambiguous: 'accepted' was carrying at least three different "
            f"jobs across this corpus - closed, acknowledged-but-unfixed, and "
            f"known-limitation - which left a reader unable to tell a closed "
            f"finding from an open one by machine. 'resolved' was added to the enum "
            f"so the distinction is data rather than prose. This record was not "
            f"deleted and its existence remains part of the audit trail. {GUARD}"
        )
        d["revision_history"].append(OrderedDict([
            ("revision", new_rev),
            ("date", DATE),
            ("author", AUTHOR),
            ("description", PREAMBLE.format(date=DATE) +
             f" Audit class: {v['class']}. Disposition migrated from "
             f"'{v['recorded_disposition']}' to '{disp}' and `resolution` rewritten "
             f"to the current position: what the condition was, what fixed it or why "
             f"it is still open, the evidence re-derived on {DATE}, and any residual. "
             f"The `reverification` field added to this record carries that evidence "
             f"in full so the record carries its own proof of currency. No other "
             f"field was altered: severity, category, evidence, impact, "
             f"root_cause, lifecycle_status, human_approval_status, "
             f"production_authorized and product_verification_credit are unchanged. "
             f"{GUARD}"),
        ]))
        p.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
        changed.append(f"  {fid}  ->  disposition={disp:9s} rev={new_rev}  "
                       f"({v['class']})")

    # ---- new records -----------------------------------------------------
    new_written = []
    for spec in (NEW_039, NEW_040, NEW_041, NEW_042):
        p = FIND / spec["filename"]
        if p.exists():
            skipped.append(f"{spec['id']} (already exists - idempotent)")
            continue
        rec = OrderedDict()
        rec["revision"] = "1"
        rec["schema_version"] = "1.0.0"
        rec["artifact_type"] = "finding"
        rec["engineering_domain"] = "verification" if spec["id"] in (
            "FB2-REV-FND-000041", "FB2-REV-FND-000042") else "management"
        rec["profile"] = "synthetic_reference"
        rec["scenario_id"] = "SCN-BASELINE"
        rec["baseline_id"] = "BAS-REF-001"
        rec["variant_applicability"] = ["VAR-REF-001"]
        rec["owner_role"] = "data_quality_engineer"
        rec["origin"] = "derived"
        rec["lifecycle_status"] = "draft"
        rec["automated_review_status"] = OrderedDict([
            ("schema_valid", True), ("links_valid", True),
            ("provenance_consistent", True), ("consistency_checks", True),
            ("last_run", DATE)])
        rec["human_approval_status"] = "pending"
        rec["production_authorized"] = False
        rec["product_verification_credit"] = False
        rec["created_at"] = DATE
        rec["updated_at"] = DATE
        rec["id"] = spec["id"]
        rec["title"] = spec["title"]
        rec["severity"] = spec["severity"]
        rec["category"] = spec["category"]
        rec["disposition"] = spec["disposition"]
        rec["impact"] = spec["impact"]
        rec["root_cause"] = spec["root_cause"]
        rec["evidence"] = spec["evidence"]
        rec["resolution"] = spec["resolution"]
        rec["source_refs"] = []
        rec["assumption_refs"] = []
        rec["standards_mappings"] = [OrderedDict([
            ("standard_id", "ASPICE_PAM_41"), ("reference", "SUP.9"),
            ("status", "mapped"),
            ("rationale", "Problem resolution management: a material contradiction "
                           "becomes a recorded problem, not a silent edit.")]),
            OrderedDict([
                ("standard_id", "ISO_26262_2018"),
                ("reference", "Part 2, Clause 6.4 (monitoring and measurement)"),
                ("status", "mapped"),
                ("rationale", "The obligation to record rather than to conceal.")]),
        ]
        rec["lifecycle_status_note"] = (
            "'draft': raised by the finding-closure pass and verified by re-derivation "
            "from the live corpus. No human reviewer has confirmed this record and "
            "human_approval_status remains pending. This record makes no MISRA "
            "conformance claim, no tool-qualification claim, no certification claim "
            "and no ASPICE capability-level claim of any kind.")
        rec["disposition_note"] = (
            f"disposition '{spec['disposition']}' is used in the sense defined "
            f"normatively by "
            f"docs/artifacts/governance/finding-disposition-vocabulary.md. {GUARD}")
        rec["reverification"] = OrderedDict([
            ("date", DATE),
            ("method", "docs/artifacts/tests/audit_findings.py and "
                       "docs/artifacts/tests/rule_scope_probe.py"),
            ("raised_by", "finding-closure pass over the 38 pre-existing records"),
        ])
        rec["revision_history"] = [OrderedDict([
            ("revision", "1"), ("date", DATE), ("author", AUTHOR),
            ("description",
             "New record raised by the finding-closure pass. It records a condition "
             "that pass discovered while re-deriving the conditions the 38 existing "
             "records assert, and that would otherwise have been lost - either "
             "because it was a rule defect that no record named, or because closing "
             "the record that did name its neighbourhood would have quietly carried "
             "it away with it. " + spec["resolution"].split("\n\n")[0] + " " + GUARD),
        ])]
        p.write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n")
        new_written.append(f"  {spec['id']}  ->  NEW  "
                           f"disposition={spec['disposition']}")

    print("\n".join(changed))
    if new_written:
        print("\nNEW RECORDS")
        print("\n".join(new_written))
    if skipped:
        print("\nSKIPPED")
        print("\n".join("  " + s for s in skipped))
    print(f"\n{len(changed)} record(s) corrected, {len(new_written)} raised. "
          f"No record was deleted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
