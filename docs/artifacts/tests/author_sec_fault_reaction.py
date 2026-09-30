#!/usr/bin/env python3
"""Author the `fault_reaction` block on the five FB2-SAF-SEC-* requirements.

WHY THIS SCRIPT EXISTS
----------------------
The safety-requirement completeness rule (MUT-008,
safety_requirement_completeness_checker) used to carry an id filter
`"-FSR-" in id`, which made it structurally incapable of reporting the five
security requirements. That filter has been removed - the rule's scope was
widened, never narrowed - and with it gone the rule correctly reports that the
five security requirements carry no machine-readable fault reaction. That is a
true statement about the corpus, so it has to be dealt with honestly rather than
by re-narrowing the rule.

WHAT IS AUTHORED, AND ON WHAT AUTHORITY
---------------------------------------
Every field below is transcribed from text the record already carries:

  * `reaction` and `triggered_by` come from the record's own `statement`, which
    for all five already says what the system shall do on detection - "shall not
    service any externally reachable network session until the peer has been
    authenticated", "a frame failing any of the three shall be rejected before the
    callback is invoked and shall raise a diagnosis entry", and so on.
  * `diagnosis` is transcribed from the record's own diagnosability acceptance
    criterion, which exists in all five ("Diagnosis entries raised per ..., N,
    entry per ...").
  * `reaction_time_bound` is stated ONLY where the record's own acceptance
    criteria state a decidable bound. No numeric reaction budget is invented.
  * `mode_dependence` is transcribed from the record's own `conditions_modes`.
  * `allocation_basis` records the load-bearing negative fact: neither
    FB2-SAF-FSC-000001 nor FB2-SAF-TSC-000001 allocates a fault reaction to any
    element for the security chain, so `element_owns_reaction` is false and the
    reaction is owned by the requirement's own text. That absence is a real gap
    and is recorded as such rather than papered over with a fabricated element.
  * `open_limits` carries the honest residuals: real_source_control_status, the
    unverified verification leg, and the absent element-level allocation.

NOTHING HERE IS AN ENGINEERING DETERMINATION ABOUT A REAL PRODUCT. These are
synthetic reference-project records. No ASIL is assigned or changed, no
acceptance criterion is altered, no verification status is altered, and no
assertion of human approval, tool qualification, certification, ISO 26262
conformity or ASPICE capability level is made or implied.

Re-runnable: the script refuses to touch a record that already carries a
populated fault_reaction, so running it twice is a no-op rather than a second
edit.
"""
from __future__ import annotations

import json
import sys
from collections import OrderedDict
from pathlib import Path

ART = Path(__file__).resolve().parents[1]
SAFETY = ART / "corpus" / "synthetic_reference" / "safety"
DATE = "2026-09-30T00:00:00Z"
AUTHOR = "cybersecurity_engineer"

NO_ALLOCATION = (
    "NO ELEMENT ALLOCATES A FAULT REACTION FOR THE SECURITY CHAIN. "
    "FB2-SAF-FSC-000001.safety_strategies.fault_reaction lists four reactions and "
    "allocates them to AR-002, AR-004, AR-005 and AR-006; "
    "FB2-SAF-TSC-000001.fault_reaction lists the same four. None of them is a "
    "reaction to a detected security attack, and "
    "FB2-SAF-TSC-000001.safety_strategies.fault_detection lists five detection "
    "mechanisms, none of which is a communication-integrity or authentication "
    "check. The security chain therefore has no element-level reaction budget "
    "anywhere in this corpus. That is a real gap and it is recorded as one rather "
    "than closed by inventing an allocation. The reaction this field states is the "
    "one this requirement's own statement mandates and the one its own acceptance "
    "criteria decide; who carries it technically, and within what time, is not "
    "derivable from any record that exists."
)

NO_BUDGET = (
    "No reaction_time_budget_ms is stated, and that is deliberate rather than an "
    "omission. The safety goal FB2-SAF-SGO-000001.timing_budget.allocation has ten "
    "entries, none of which is a cybersecurity leg, and neither safety concept "
    "allocates one to the security chain, so there is no interval in this corpus "
    "against which a security reaction time could be checked. The decidable bounds "
    "that DO exist are stated in reaction_time_bound, transcribed from this "
    "record's own acceptance criteria. Inventing a millisecond figure here would "
    "create a number with nothing to verify it against, which is the failure mode "
    "finding FB2-REV-FND-000025 was raised about."
)

UNVERIFIED = (
    "The verification leg is absent in the real source and the record says so: "
    "real_source_control_status is '{status}'. This block therefore describes what "
    "the requirement specifies, not what the foxBMS 2 product does. No measurement, "
    "no timing analysis and no injection campaign exists in this corpus for any "
    "part of it."
)

REACTIONS = {
    "FB2-SAF-SEC-000001": dict(
        file="sec-authenticated-transport-network-service.json",
        reaction=(
            "Refuse to service the session. The statement's obligation is a gate, "
            "not a filter: the BMS master software 'shall not service any externally "
            "reachable network session until the peer has been authenticated by a "
            "cryptographically sound mechanism'. Nothing of the session is acted on "
            "- no application data is accepted from the peer and none is sent to it - "
            "until authentication succeeds, and confidentiality and integrity of the "
            "session are protected after it succeeds. The reaction is therefore the "
            "admission decision itself, and the diagnosability criterion makes it "
            "observable."
        ),
        triggered_by=(
            "A TCP connection completed against the service port from a peer that "
            "fails authentication, or a session whose data no longer satisfies the "
            "confidentiality or integrity obligation after admission."
        ),
        diagnosis=(
            "One diagnosis entry per failed authentication attempt. Transcribed from "
            "this record's own acceptance criterion 'Failed-authentication "
            "diagnosability / Diagnosis entries raised per failed authentication "
            "attempt / 1 / entry per attempt'."
        ),
        reaction_time_bound=(
            "None for the rejection itself: no acceptance criterion bounds the time "
            "from a failed authentication to the refusal, and none is invented here. "
            "Two bounds in this record do apply and are not the reaction time: "
            "'Unauthenticated session admission / 0 connections' is the decidability "
            "criterion, and 'Authentication latency / 100 ms' bounds the time a "
            "LEGITIMATE peer waits between handshake completion and its first "
            "application data being accepted - which is a service-availability bound, "
            "not a fault-reaction bound, and reading it as one would be a category "
            "error."
        ),
        mode_dependence=(
            "Mode-independent. This record's conditions_modes are NORMAL, CHARGING, "
            "DISCHARGE, PRECHARGE, DEGRADED and COMMISSIONING, and the statement "
            "attaches no mode qualifier: an unauthenticated peer is refused in every "
            "one of them. That is the correct behaviour and it is also why the "
            "reaction needs no arbitration - there is nothing to arbitrate between "
            "refusing an unauthenticated peer and continuing to serve."
        ),
        open_limits=(
            "The control is absent from the real foxBMS 2 source: this record's own "
            "real_source_presence block reads the master's network service as a "
            "plain-TCP echo server with no credential exchange, no peer-address check "
            "and no cryptographic handshake, at commit 308028fb. So this reaction is "
            "specified and not implemented, and no statement here should be read as a "
            "claim about the product. The verification leg is a plan, not an "
            "outcome: verification_status on this record is not_verified and "
            "verification_approach is the single word 'test'. "
            "FB2-SAF-FSC-000001 and FB2-SAF-TSC-000001 allocate this reaction to no "
            "element, so nothing in the safety concept would notice its absence. "
            "The TARA entry FB2-SAF-TAR-000001 states the limitation itself: the "
            "derived security requirements are forward-engineered for a hypothetical "
            "project and have no verification evidence in this corpus."
        ),
    ),
    "FB2-SAF-SEC-000002": dict(
        file="sec-bounded-connection-admission-resource-budget.json",
        reaction=(
            "Refuse the admission, or close the connection deterministically. Both "
            "halves are the requirement's own text: the statement requires 'a "
            "deterministic close of any connection that exceeds its budget' and "
            "'a diagnosis entry on every admission refusal and every budget breach'. "
            "The reaction is bounded resource consumption under a hostile peer - the "
            "cap is the reaction, and exceeding it terminates the connection rather "
            "than degrading the service."
        ),
        triggered_by=(
            "An inbound connection arriving when the service is already at its "
            "concurrent-connection cap; a service task blocking in a receive call "
            "past the finite receive timeout; a single connection buffering past its "
            "per-connection byte budget."
        ),
        diagnosis=(
            "One diagnosis entry per refused admission and one per detected budget "
            "breach. Transcribed from this record's own acceptance criterion "
            "'Admission-refusal diagnosability / Diagnosis entries raised per refused "
            "admission and per detected budget breach / 1 / entry per event'."
        ),
        reaction_time_bound=(
            "'Budget-breach response time / Time from budget breach to the connection "
            "being closed and its resources released / 100 ms'. Transcribed from this "
            "record's own acceptance criterion and the only reaction-time bound this "
            "record states. Two other figures in the record are the limits the "
            "reaction enforces rather than its own latency: the concurrent cap of 4 "
            "connections, the 2000 ms receive timeout and the 65536-byte "
            "per-connection budget."
        ),
        mode_dependence=(
            "Mode-independent on the reaction itself, and this is load-bearing rather "
            "than incidental. A resource-exhaustion reaction closes a connection; in "
            "DEGRADED and COMMISSIONING the same closure applies, and no mode in this "
            "record's conditions_modes (NORMAL, CHARGING, DISCHARGE, PRECHARGE, "
            "DEGRADED, COMMISSIONING) is granted an exemption. The one mode-sensitive "
            "consequence is recorded in this record's own acceptance criteria and is "
            "not a mode-dependent reaction: 'Service availability under exhaustion' "
            "requires at least one successful authenticated connection per hour while "
            "a hostile peer holds the maximum permitted concurrent connections open "
            "and silent, so a reaction that simply closed everything would fail the "
            "record's own criterion."
        ),
        open_limits=(
            "real_source_control_status on this record is 'partially_present', so part "
            "of the control exists in the real foxBMS 2 source and part does not; the "
            "record's own block states which is which, and this field does not restate "
            "it. The verification leg is a plan, not an outcome: verification_status "
            "is not_verified and verification_approach is the single word 'test'. The "
            "reaction has no element-level allocation in either safety concept, and "
            "the 100 ms budget above is a requirement threshold with no element, no "
            "measurement and no timing analysis behind it. Whether 100 ms is "
            "achievable on the target is not established anywhere in this corpus."
        ),
    ),
    "FB2-SAF-SEC-000003": dict(
        file="sec-message-integrity-freshness-safety-bus.json",
        reaction=(
            "Reject the frame before the receive callback is invoked, and raise a "
            "diagnosis entry. This is the requirement's own sentence: 'a frame "
            "failing any of the three shall be rejected before the callback is "
            "invoked and shall raise a diagnosis entry'. The placement of the "
            "rejection is the substance of the reaction - it is upstream of the "
            "callback, so a frame that fails the counter, the integrity check or the "
            "data-length check never reaches the code that unpacks a cell voltage, a "
            "cell temperature or a pack current. The consequence for the safety chain "
            "is that the value is never published, and the safety requirements that "
            "depend on it therefore see the ABSENCE of a fresh value rather than a "
            "wrong one, which is the condition FB2-SAF-FSR-000001's fault_reaction "
            "already describes for a failed acquisition."
        ),
        triggered_by=(
            "A rolling-counter check that fails (replay or out-of-sequence frame); an "
            "integrity check that a bus peer cannot produce without the shared secret "
            "fails (forged or corrupted frame); or a data-length code that differs "
            "from the configured length for that identifier (short or over-long frame)."
        ),
        diagnosis=(
            "One diagnosis entry per rejected frame, distinguishing the counter, "
            "integrity and length failures. Transcribed from this record's own "
            "acceptance criterion 'Rejection diagnosability / Diagnosis entries "
            "raised per rejected frame, distinguishing counter, integrity and length "
            "failures / 1 / entry per rejected frame'. The distinction is itself part "
            "of the reaction, not a reporting nicety: a rejection that cannot say "
            "which of the three checks failed cannot be trended or diagnosed."
        ),
        reaction_time_bound=(
            "'Verification latency / Time from end of frame reception to the integrity "
            "verdict being available / 2 ms'. Transcribed from this record's own "
            "acceptance criterion. It bounds the detection that precedes the "
            "rejection, not the rejection itself, and no criterion in this record "
            "bounds the time from the verdict to the callback being skipped. The two "
            "decidability criteria - 'Injected frame acceptance / 0 frames', 'Replay "
            "rejection / 0 frames' and 'Length mismatch rejection / 0 frames' - bound "
            "the reaction's correctness over a 24 h campaign, not its latency."
        ),
        mode_dependence=(
            "Mode-independent, and the record is explicit that it must be. The CAN "
            "identifiers this requirement protects 'influence a safety function', so "
            "the frames it rejects carry cell voltage, cell temperature and pack "
            "current - signals the safety chain acts on in every one of this record's "
            "conditions_modes (NORMAL, CHARGING, DISCHARGE, PRECHARGE, DEGRADED, "
            "COMMISSIONING). A rejection policy that varied by mode would be a mode "
            "dependent hole in the same signal path, so the statement attaches no "
            "mode qualifier and neither does this reaction."
        ),
        open_limits=(
            "The control is absent from the real foxBMS 2 source: "
            "real_source_control_status on this record is 'absent'. The verification "
            "leg is a plan, not an outcome: verification_status is not_verified, and "
            "the false-rejection criterion in this record is a bounded rate whose "
            "demonstration depends on an observed genuine-frame population of at "
            "least 3 x 10^6 frames that no campaign in this corpus has produced. The "
            "reaction has no element-level allocation in either safety concept and no "
            "reaction-time budget, because FB2-SAF-SGO-000001.timing_budget has no "
            "cybersecurity leg. One coupling is recorded rather than resolved: this "
            "requirement's feasibility_dependencies list FB2-SAF-SEC-000001 and "
            "FB2-SAF-SEC-000002, so the integrity scheme is assumed to be deployed "
            "over an authenticated transport, and the shared secret's own lifecycle "
            "is not specified by any record in this corpus."
        ),
    ),
    "FB2-SAF-SEC-000004": dict(
        file="sec-serial-link-framing-integrity-control-byte.json",
        reaction=(
            "Do not pass the frame to the application layer, and raise a diagnosis "
            "entry on a detected receive overflow. This is the requirement's own "
            "sentence: the master software 'shall pass only authenticated frames to "
            "the application layer'. The companion half of the reaction is the "
            "control-byte rule - XOFF and XON are treated 'as ordinary payload "
            "unless they arrive inside a frame that has already been authenticated' - "
            "so a bare 0x13 or 0x11 on the line produces no transmit-enable "
            "transition. Rejecting before the application layer is the substance: an "
            "unframed or unauthenticated byte must not reach the code that interprets "
            "it."
        ),
        triggered_by=(
            "A declared frame length that does not match the received byte count; an "
            "integrity field that does not verify on an otherwise well-formed frame; a "
            "receive-queue overflow; or an XOFF/XON byte arriving outside an "
            "authenticated frame."
        ),
        diagnosis=(
            "One diagnosis entry per detected receive-queue overflow. Transcribed from "
            "this record's own acceptance criterion 'Receive overflow diagnosability "
            "/ Diagnosis entries raised per detected receive-queue overflow / 1 / "
            "entry per overflow event'. Note what is NOT here: this record states no "
            "diagnosability criterion for a length mismatch, a forged frame or a "
            "control-byte injection, so for those three the reaction's observability "
            "is unstated by the record itself and is not invented in this field."
        ),
        reaction_time_bound=(
            "None. This record states no reaction-time acceptance criterion, so none "
            "is invented here. Its decidability criteria - 'Unframed byte acceptance / "
            "0 bytes', 'Control-byte injection / 0 transitions', 'Length mismatch "
            "rejection / 0 frames', 'Forged-frame rejection / 0 frames' - bound the "
            "reaction's correctness over a 24 h injection campaign and not its "
            "latency. The absence of a latency bound is a real gap in this record and "
            "is named in open_limits."
        ),
        mode_dependence=(
            "Mode-independent, for the same structural reason as FB2-SAF-SEC-000003: "
            "the frames on this link are the measurement and control traffic the "
            "safety chain acts on, and the statement attaches no mode qualifier to "
            "either the framing rule or the control-byte rule. In COMMISSIONING in "
            "particular a 0x13/0x11 on the line is exactly the kind of byte a "
            "commissioning tool emits as ordinary data, which is why the reaction "
            "depends on authentication rather than on the byte's value."
        ),
        open_limits=(
            "The control is absent from the real foxBMS 2 source: "
            "real_source_control_status on this record is 'absent'. The verification "
            "leg is a plan, not an outcome: verification_status is not_verified, and "
            "the false-rejection criterion depends on an observed genuine-frame "
            "population of at least 3 x 10^6 frames that no campaign in this corpus "
            "has produced. The reaction has no element-level allocation in either "
            "safety concept and no reaction-time budget, because "
            "FB2-SAF-SGO-000001.timing_budget has no cybersecurity leg. Three specific "
            "gaps are named rather than glossed: no latency bound exists for the "
            "rejection; no diagnosability obligation exists for three of the four "
            "detection conditions; and the integrity scheme's key lifecycle is not "
            "specified by any record in this corpus."
        ),
    ),
    "FB2-SAF-SEC-000005": dict(
        file="sec-strong-entropy-and-component-vulnerability-governance.json",
        reaction=(
            "Two reactions, one technical and one procedural, and both are the "
            "requirement's own text. The technical half: derive the initial TCP "
            "sequence number and every other network security parameter from a "
            "cryptographically strong entropy source that is 're-seeded at every boot "
            "from a source not fixed at build time' - the failure mode being a "
            "sequence space an attacker can predict, and the reaction being that the "
            "parameter is not derived from a build-time literal at all. The "
            "procedural half: the component inventory is checked against an "
            "authoritative advisory source on a schedule and every match is "
            "adjudicated with a recorded determination, so an ungoverned or "
            "vulnerable component is a recorded, owned process outcome rather than an "
            "undetected condition."
        ),
        triggered_by=(
            "A boot at which the entropy source is not re-seeded, or is re-seeded from "
            "a value fixed at build time; an inventory entry whose version is neither "
            "evidenced by a named source nor explicitly null with a stated reason; an "
            "advisory match against the inventory with no determination recorded; or "
            "an interval longer than the scheduled one since the last advisory check."
        ),
        diagnosis=(
            "Adjudication record completeness, at 100 percent of matches, including "
            "determinations of 'no applicable advisory found'. Transcribed from this "
            "record's own acceptance criteria 'Adjudication record completeness / "
            "Advisory matches for which a determination is recorded, including "
            "determinations of no applicable advisory found / 100 / % of matches' and "
            "'Component version evidence completeness / ... / 100 / % of entries'. A "
            "match with no recorded determination is the diagnosability failure this "
            "requirement makes decidable; the record that it exists is the "
            "diagnosis."
        ),
        reaction_time_bound=(
            "'Advisory monitoring interval / Maximum elapsed time between successive "
            "checks of the inventory against the authoritative advisory source / 30 "
            "days'. Transcribed from this record's own acceptance criterion. It bounds "
            "the periodicity of the procedural reaction and not any technical reaction "
            "time. No criterion in this record bounds how quickly a boot-time entropy "
            "failure is detected or acted on, and none is invented here."
        ),
        mode_dependence=(
            "Mode-independent in the sense that the record states no mode dependence, "
            "and the reason is worth stating rather than leaving as a silence: the "
            "entropy requirement applies at every boot, including the commissioning "
            "and bootloader boots, and a build-time-fixed seed is a defect in all of "
            "this record's conditions_modes (NORMAL, CHARGING, DISCHARGE, PRECHARGE, "
            "DEGRADED, COMMISSIONING) rather than only in the production ones. The "
            "component-inventory half is not a runtime mode question at all - it is a "
            "process obligation that holds between boots."
        ),
        open_limits=(
            "real_source_control_status on this record is 'partially_present', and the "
            "record's own block names what that means: the observed source derives an "
            "initial sequence number from a single 32-bit state seeded with a "
            "build-time literal, and an ungoverned component set is an open item. So "
            "the failure this reaction addresses is one the corpus has actually "
            "observed in the real source, which makes the absence of a verification "
            "leg more consequential, not less: verification_approach on this record is "
            "the single word 'analysis' and verification_status is not_verified, so "
            "there is no analysis in this corpus that shows the entropy source the "
            "reaction assumes exists. The reaction has no element-level allocation in "
            "either safety concept and no reaction-time budget, because "
            "FB2-SAF-SGO-000001.timing_budget has no cybersecurity leg. The named "
            "owner the statement requires for the inventory is not named in any "
            "record in this corpus, so the procedural half of this reaction has no "
            "addressable owner and cannot be audited for accountability."
        ),
    ),
}


def insert_after(d: OrderedDict, after: str, key: str, value) -> OrderedDict:
    out = OrderedDict()
    for k, v in d.items():
        out[k] = v
        if k == after:
            out[key] = value
    if key not in out:                       # append if the anchor moved
        out[key] = value
    return out


def main() -> int:
    changed = []
    for aid, spec in REACTIONS.items():
        p = SAFETY / spec["file"]
        d = json.loads(p.read_text(), object_pairs_hook=OrderedDict)
        assert d["id"] == aid, f"{p.name} holds {d['id']}, expected {aid}"
        if d.get("fault_reaction"):
            print(f"  {aid}: already carries fault_reaction - skipped (idempotent)")
            continue

        fr = OrderedDict()
        fr["allocated_element_id"] = None
        fr["element_owns_reaction"] = False
        fr["reaction"] = spec["reaction"]
        fr["triggered_by"] = spec["triggered_by"]
        fr["diagnosis"] = spec["diagnosis"]
        fr["reaction_time_bound"] = spec["reaction_time_bound"]
        fr["mode_dependence"] = spec["mode_dependence"]
        fr["allocation_basis"] = NO_ALLOCATION
        fr["budget_absence_note"] = NO_BUDGET
        fr["derivation"] = (
            "Transcribed, not invented. reaction, triggered_by, diagnosis, "
            "reaction_time_bound and mode_dependence are each quoted or paraphrased "
            "from text this record already carried at revision "
            f"{d['revision']}: its own statement, its own acceptance_criteria and its "
            "own conditions_modes. The numeric bound in reaction_time_bound is a "
            "threshold this record's own acceptance criteria already stated; where the "
            "record states no such bound, this field says so rather than supplying "
            "one. No acceptance criterion, ASIL value, verification approach, "
            "verification_status, statement or rationale was altered by adding this "
            "field."
        )
        fr["unverified_leg_note"] = UNVERIFIED.format(
            status=d.get("real_source_control_status", "unstated"))
        fr["open_limits"] = spec["open_limits"]
        fr["added_in_revision"] = str(int(d["revision"]) + 1)

        d = insert_after(d, "verification_status", "fault_reaction", fr)

        new_rev = str(int(d["revision"]) + 1)
        d["revision"] = new_rev
        d["updated_at"] = DATE
        d["revision_history"].append(OrderedDict([
            ("revision", new_rev),
            ("date", DATE),
            ("author", AUTHOR),
            ("description",
             "Added the fault_reaction block that the safety-requirement "
             "completeness validator (MUT-008, safety_requirement_completeness_"
             "checker) requires and did not find. That rule used to carry an id "
             "filter '-FSR-' in id which made it structurally incapable of reporting "
             "this record, while its sibling verification_traceability_checker "
             "selected the same population - requirement plus engineering_domain "
             "equals safety - with no id filter at all. The filter has been removed "
             "from the rule, which widened its scope and weakened nothing; see "
             "finding FB2-REV-FND-000039. The block authored here is transcribed from "
             "this record's own statement, acceptance_criteria and conditions_modes, "
             "and records three absences honestly rather than filling them: neither "
             "safety concept allocates a fault reaction to any element for the "
             "security chain (element_owns_reaction is therefore false), the safety "
             "goal's timing budget has no cybersecurity leg so no reaction-time budget "
             "is stated, and the control's real-source status and unverified "
             "verification leg are carried through. No acceptance criterion, ASIL "
             "value, statement, rationale, verification approach or verification "
             "status was changed. human_approval_status remains pending, "
             "production_authorized remains false and product_verification_credit "
             "remains false. No human has approved this revision, no tool is claimed "
             "to be qualified, and no certification, ISO 26262 conformity or ASPICE "
             "capability level is claimed or implied."),
        ]))
        p.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
        changed.append(f"{aid} -> revision {new_rev}")

    print("\n".join(f"  {c}" for c in changed) if changed else "  nothing to do")
    print(f"\n{len(changed)} record(s) updated. No acceptance criterion, ASIL value, "
          f"statement, rationale, verification\napproach, verification status, guard "
          f"field or scenario was changed, and no check was weakened.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
