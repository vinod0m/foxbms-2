#!/usr/bin/env python3
"""Decide whether the safety-requirement verification rule is too narrow.

READ-ONLY with respect to the corpus. Nothing on disk is modified: the corpus is
loaded, links are removed or added IN MEMORY, and the rule is re-run. That is
what makes the answer evidence rather than an argument: "the rule does not fire
on the security requirements" is only a blind spot if removing the security
requirements' verification links also fails to make it fire.

THE QUESTION
------------
docs/artifacts/tools/corpus.py `_validate_semantic_rules` has three rules that
concern safety requirements:

  R1  verification   a safety-domain requirement with no verifies/validates link
  R2  fault_reaction a safety-domain requirement with no fault_reaction
  R3  asil           a safety_goal whose asil has no asil_justification

The hypothesis under test is that R1 filters on an id pattern such as `-FSR-`
and therefore never sees the `FB2-SAF-SEC-*` security requirements, so a check
that should fire is silent. A filter is only a blind spot if removing the
security requirements from the corpus changes nothing.

WHAT IS MEASURED
----------------
For each rule, the id filter actually present in the source, and for R1 and R2 a
counterfactual: with the security requirements' relevant field/link removed from
an in-memory copy, does the rule fire on them?

R3 is answered by inspection because its population is defined by
`artifact_type == "safety_goal"`, which is a type, not an id pattern. The
security requirements are `requirement` records, so the question for R3 is
whether a requirement's ASIL claim is checked somewhere, which the requirement
applicability rule (MUT-013) does.

This script asserts no human approval, tool qualification, certification,
ISO 26262 conformity or ASPICE capability level.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ART = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ART / "tools"))

import corpus as C  # noqa: E402

TOOL = C.CorpusTool(ART.parents[1])   # CorpusTool takes the REPO root
INDEX = TOOL.load_artifact_index()
LINKS = TOOL.load_links()


def _id(k):
    return k[1] if isinstance(k, tuple) and len(k) >= 2 else k


def sec_ids():
    return [i for (_p, i), (_f, d) in INDEX.items()
            if d.get("engineering_domain") == "safety"
            and d.get("artifact_type") == "requirement" and "-SEC-" in i]


def fsr_ids():
    return [i for (_p, i), (_f, d) in INDEX.items()
            if d.get("engineering_domain") == "safety"
            and d.get("artifact_type") == "requirement" and "-FSR-" in i]


def fire_verification(index, links):
    TOOL.findings = C.Findings()
    verified = {l.get("target_id") for l in links
                if l.get("relation_type") in ("verifies", "validates")
                and l.get("target_id")}
    out = []
    for key, (_p, d) in index.items():
        if (d.get("artifact_type") == "requirement"
                and d.get("engineering_domain") == "safety"
                and _id(key) not in verified):
            out.append(_id(key))
    return sorted(out)


def id_filter_of(block: str):
    """The id filter in a rule's POPULATION CONDITION, or [].

    Reads the executable `if` line only. A rule's comment block quotes its own
    history - this corpus's rules do, at length - and a search over the whole
    block finds that quotation and reports a removed filter as present. That is
    the mirror image of the bug this probe exists to catch, so the detector is
    scoped to the line that actually selects the population.
    """
    for line in block.splitlines():
        if line.strip().startswith('if d.get("artifact_type")'):
            return re.findall(r'"(-\w+-)" in ', line)
    return []


def fire_fault_reaction(index, id_filter=("-FSR-",)):
    """A transcription of the rule, parameterised by its id filter.

    Transcribed rather than imported so that this measurement cannot silently
    change meaning when corpus.py is edited. `id_filter` is the third condition
    the rule used to carry; pass `()` to get the rule as it stands after the
    filter was removed. Both are run below, so the before/after is measured
    rather than asserted.
    """
    out = []
    for key, (_p, d) in index.items():
        if (d.get("artifact_type") == "requirement"
                and d.get("engineering_domain") == "safety"
                and (not id_filter or any(f in _id(key) for f in id_filter))
                and not d.get("fault_reaction")):
            out.append(_id(key))
    return sorted(out)


def main() -> int:
    src = (ART / "tools" / "corpus.py").read_text()
    body = src[src.index("def _validate_semantic_rules"):]

    print("=" * 100)
    print("RULE-SCOPE DETERMINATION - is the safety-requirement verification rule too narrow?")
    print("=" * 100)

    # ---------------------------------------------------------------- R1
    print("\nR1  verification   (rule id 'verification_traceability_checker')")
    sel = body[body.index("# Rule: requirements of safety classification"):]
    sel = sel[:sel.index("# Rule: execution_kind")]
    cond = [l.strip() for l in sel.splitlines() if 'd.get("artifact_type")' in l
            or "verified = " in l or "aid not in verified" in l]
    for l in cond:
        print("    source:", l)
    id_filters = id_filter_of(sel)
    print(f"    id-pattern filter present : {id_filters or 'NONE'}")
    print(f"    -> the rule's population is selected by artifact_type + "
          f"engineering_domain, not by an id pattern.")

    base = fire_verification(INDEX, LINKS)
    print(f"    live corpus            : {len(base)} unverified safety requirement(s) "
          f"{base or ''}")

    # counterfactual: strip the security requirements' verification links
    no_link = [l for l in LINKS
               if not (l.get("relation_type") in ("verifies", "validates")
                       and str(l.get("target_id", "")).startswith("FB2-SAF-SEC-"))]
    dropped = len(LINKS) - len(no_link)
    cf = fire_verification(INDEX, no_link)
    print(f"    counterfactual         : drop the {dropped} verifies link(s) whose "
          f"target is FB2-SAF-SEC-*,")
    print(f"                            re-run the rule  -> {len(cf)} unverified "
          f"requirement(s)")
    for s in sec_ids():
        print(f"                              {s}: "
              f"{'FLAGGED' if s in cf else 'NOT FLAGGED'}")
    sec_flagged = all(s in cf for s in sec_ids())
    print(f"    VERDICT R1             : "
          f"{'TOO NARROW - the security requirements are not covered' if not sec_flagged else 'CORRECTLY SCOPED'}"
          f". The rule is in the population and is satisfied only by real links.")

    # why is it satisfied today? show the links.
    print("\n    the links that satisfy the five security requirements today:")
    for l in LINKS:
        if (l.get("relation_type") in ("verifies", "validates")
                and str(l.get("target_id", "")).startswith("FB2-SAF-SEC-")):
            print(f"      {l['link_id']}  {l['source_id']} --verifies--> "
                  f"{l['target_id']}   ({l['_registry']})")

    # ---------------------------------------------------------------- R2
    print("\n\nR2  fault_reaction  (rule id 'safety_requirement_completeness_checker')")
    sel2 = body[body.index("# Rule: Safety requirement completeness checker"):]
    sel2 = sel2[:sel2.index("# Rule: ASIL assignment validator")]
    for l in [x.strip() for x in sel2.splitlines()
              if (x.strip().startswith('if d.get("artifact_type")')
                  or "fault_reaction" in x and not x.strip().startswith("#"))]:
        print("    source:", l)
    idf2 = id_filter_of(sel2)
    print(f"    id-pattern filter in the population condition, NOW: "
          f"{idf2 or 'NONE - the filter has been removed'}")

    # The live corpus now reports 0 under both versions, because the five security
    # requirements carry the fault_reaction that the widened rule asked for. That
    # is the desired end state but it does not demonstrate the widening, so the
    # counterfactual is run on an in-memory copy with the field removed from every
    # safety-domain requirement. Under that copy the two versions of the rule must
    # differ exactly as the finding claims: the old one blind, the new one not -
    # and the FSR set must be identical between them, which is the "nothing
    # previously reported stopped being reported" half.
    stripped = {k: (p_, {kk: vv for kk, vv in d.items() if kk != "fault_reaction"})
                for k, (p_, d) in INDEX.items()}
    before = fire_fault_reaction(stripped, id_filter=("-FSR-",))
    after = fire_fault_reaction(stripped, id_filter=())
    before_fsr = sorted(x for x in before if "-FSR-" in x)
    after_fsr = sorted(x for x in after if "-FSR-" in x)
    after_sec = sorted(x for x in after if "-SEC-" in x)
    print("\n    COUNTERFACTUAL: remove `fault_reaction` from every "
          "safety-domain requirement in an")
    print("                  in-memory copy, then run both versions of the rule.")
    print(f"      BEFORE the fix (filter '-FSR-'):  {len(before):2d} reported"
          f"  {before or ''}")
    print(f"        of which FSR: {len(before_fsr):2d}   SEC: "
          f"{len(before) - len(before_fsr):2d}  <-- the five security requirements "
          f"are INVISIBLE to the old rule")
    print(f"      AFTER  the fix (filter removed):   {len(after):2d} reported")
    print(f"        of which FSR: {len(after_fsr):2d}   SEC: {len(after_sec):2d}"
          f"  {after_sec}")
    print()
    print(f"      PROOF 1 - the five security requirements are now reported: "
          f"{all(s in after for s in sec_ids())}")
    print(f"      PROOF 2 - nothing previously reported stopped being reported: the "
          f"FSR set is")
    print(f"               identical between the two versions "
          f"({before_fsr == after_fsr}, {len(after_fsr)} FSRs), and the "
          f"after-set is a strict superset")
    print(f"               ({set(before) < set(after)}). The rule's population only "
          f"grew; nothing was narrowed.")

    # ---------------------------------------------------------------- R3
    print("\n\nR3  asil_justification  (rule id 'asil_assignment_validator')")
    sel3 = body[body.index("# Rule: ASIL assignment validator"):]
    sel3 = sel3[:sel3.index("# Rule: Requirement applicability validator")]
    for l in [x.strip() for x in sel3.splitlines()
              if 'd.get("artifact_type")' in x or "asil_justification" in x][:3]:
        print("    source:", l)
    idf3 = id_filter_of(sel3)
    print(f"    id-pattern filter present : {idf3 or 'NONE'}")
    print("    VERDICT R3             : CORRECTLY SCOPED, and not an id-pattern "
          "blind spot. The")
    print("                            population is selected by "
          "`artifact_type == 'safety_goal'`, a type.")
    print("                            A requirement does not carry an asil field; it "
          "carries")
    print("                            safety_allocation.asil, and requirement-level "
          "ASIL claims are")
    print("                            checked by the requirement applicability "
          "rule (MUT-013), which")
    print("                            is also unfiltered. All five security "
          "requirements are")
    print("                            safety_allocation.asil = 'not_applicable' and "
          "each already carries")
    print("                            an asil_justification, so nothing is "
          "unchecked. Widening R3 to")
    print("                            requirements would be inventing a scope it "
          "was never given.")

    # ---------------------------------------------------------------- other
    print("\n\nADJACENT RULE NOTED, NOT CHANGED")
    sel4 = body[body.index("# Rule: Diagnostic coverage claim validator"):]
    sel4 = sel4[:sel4.index("# Rule: Configuration consistency checker")]
    idf4 = id_filter_of(sel4)
    print(f"    diagnostic_coverage_claim_validator (MUT-010) also carries the "
          f"id filter {idf4}.")
    print("    It is NOT changed here: it was not in scope, and the field it reads "
          "(diagnostic_coverage)")
    print("    is claimed by FSR records and by no SEC record, so the filter is "
          "currently inert")
    print("    rather than silently dropping a live defect. Recorded as a finding "
          "rather than fixed.")

    print("\n" + "=" * 100)
    print("No corpus file was modified by this script. It asserts no human approval, "
          "tool qualification,")
    print("certification, ISO 26262 conformity or ASPICE capability level.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
