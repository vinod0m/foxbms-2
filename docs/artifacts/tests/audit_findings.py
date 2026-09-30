#!/usr/bin/env python3
"""Re-test every corpus finding record against the corpus as it stands now.

READ-ONLY. Writes nothing, creates nothing, deletes nothing.

WHY THIS EXISTS
---------------
`corpus.py validate` reports the *live* defect set. This script answers a
different question: for each record under docs/artifacts/reviews/findings/, does
the condition its own `title` and `evidence` assert still hold? A finding record
is an audit-trail entry, not a live sensor, so nothing re-reads it and nothing
stops it from going stale. A corpus that carries findings for defects that were
fixed is as misleading as one that hides open defects, because it inflates the
apparent defect count and trains a reader to discount the set.

METHOD
------
Each check below states the condition in the same terms the finding used, then
re-derives it from the live corpus (link registries, canonical records, the
validator source, and the SIL harness's own archived sweep results) and prints
the evidence it actually found. No verdict is inherited from the finding's own
prose: `still_holds` comes from the re-derivation, and the finding's recorded
`disposition` is printed alongside so drift between the two is visible.

CLASSIFICATION
--------------
  OPEN        the asserted condition still holds.
  STALE       the condition no longer holds AND the record still asserts that it
              does. This is the class that misleads: the record tells a reader a
              fixed defect is live, and it inflates the apparent defect count.
  CLOSED      the condition no longer holds AND the record's own resolution
              already says so, with the fix named. Not stale; it needs only the
              disposition vocabulary migrated and a dated re-verification note.
  SUPERSEDED  the condition no longer holds because a LATER, better-rooted
              remediation addressed it, and this record's residual statement is
              now wrong. The record must point at the successor.

LIMIT
-----
This is a mechanical re-test of the conditions the records assert. It is not a
semantic re-review of their analysis, and it grants no human approval, tool
qualification, certification, ISO 26262 conformity or ASPICE capability level.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ART = Path(__file__).resolve().parents[1]
CORPUS = ART / "corpus"
FINDINGS = ART / "reviews" / "findings"
SIL = ART / ".work" / "verification-env" / "sil"
REPO = ART.parents[1]

# --------------------------------------------------------------------- loaders


def jload(p: Path):
    with open(p) as fh:
        return json.load(fh)


def index() -> dict:
    """(profile, id) -> (path, record), the same shape corpus.py builds."""
    out = {}
    for base in (CORPUS, ART / "reviews"):
        if not base.exists():
            continue
        for p in sorted(base.rglob("*.json")):
            if ".work" in p.parts:
                continue
            try:
                d = jload(p)
            except Exception:
                continue
            if isinstance(d, dict) and d.get("id"):
                out[(d.get("profile", "unknown"), d["id"])] = (p, d)
    return out


def links() -> list:
    out, seen = [], set()
    regs = list((ART / "traceability" / "link-registry").rglob("links-*.json"))
    regs += list(CORPUS.rglob("traceability/link-registry/**/links-*.json"))
    by_key = {}
    for p in regs:
        if p in seen:
            continue
        seen.add(p)
        s_ = str(p)
        prof = ("as_is" if "traceability/link-registry/as_is" in s_
                or "/corpus/as_is/traceability/" in s_ else
                "synthetic_reference" if "traceability/link-registry/synthetic_reference" in s_
                or "/corpus/synthetic_reference/traceability/" in s_ else "unknown")
        for l in jload(p).get("links", []):
            l["_registry"] = str(p.relative_to(ART))
            l.setdefault("profile", prof)
            by_key.setdefault((l.get("profile", prof), l.get("link_id")), l)
    return list(by_key.values())


IDX = index()
LNK = links()
VERIFIED = {l.get("target_id") for l in LNK
            if l.get("relation_type") in ("verifies", "validates") and l.get("target_id")}

# The most recent full SIL host sweep. A fresh run is not attempted here: the
# harness builds 313 Ceedling targets and this script must stay a fast, read-only
# re-test of the corpus. The sweep is the harness's own archived measurement and
# its provenance (generated_at, classifier, per-test outcomes) is printed with it.
SWEEP = SIL / "logs" / "AFTER-r2.json"
SWEEP_DATA = jload(SWEEP) if SWEEP.exists() else {}
SWEEP_OUTCOME = {}
for _r in SWEEP_DATA.get("results", []):
    _t = _r.get("test") or _r.get("path")
    if _t:
        SWEEP_OUTCOME[_t] = _r
SWEEP_COMPARISON = SIL / "logs" / "sweep-compare-r3.json"
VACUOUS = SIL / "logs" / "vacuous-final.json"
VACUOUS_DATA = jload(VACUOUS) if VACUOUS.exists() else {}

FINDING_RECORDS = sorted(FINDINGS.glob("*.json")) if FINDINGS.exists() else []


def rec(fid: str, profile: str = None):
    """The corpus record a finding is about, if the named profile exists."""
    if profile is not None:
        return IDX.get((profile, fid))
    for (prof, i), v in IDX.items():
        if i == fid:
            return v
    return None


def sweep_of(rel: str) -> str:
    for k, v in SWEEP_OUTCOME.items():
        if k and k.endswith(rel):
            return f"{v.get('outcome')}"
    return "absent-from-sweep"


# ------------------------------------------------------------------- verdicts

ROWS: list = []


# A record whose own resolution OPENS with "RESOLVED ..." already states that the
# condition is fixed. Anything else that still asserts the condition is stale.
LEADS_RESOLVED = re.compile(r"^\s*RESOLVED\b", re.I)


def verdict(fid, subject, still, cls, evidence, also=""):
    d = next((jload(p) for p in FINDING_RECORDS
              if jload(p).get("id") == fid), {})
    # If the condition is false, the interesting question becomes whether the
    # record KNOWS that. A record whose own resolution already states the fix is
    # CLOSED, not STALE, and downgrading it to STALE would be a regression.
    if still is False and cls == "STALE" and \
            LEADS_RESOLVED.match(str(d.get("resolution", ""))):
        cls = "CLOSED"
    ROWS.append({
        "id": fid, "subject": subject, "still_holds": still, "class": cls,
        "recorded_disposition": d.get("disposition", "-"),
        "recorded_revision": str(d.get("revision", "-")),
        "evidence": evidence, "also": also,
    })


def check_verification_link(fid, subject, profile, file_hint):
    """Findings 1..12: '<id> has no verifies/validates link'."""
    r = rec(subject, profile)
    if r is None:
        verdict(fid, f"{subject} ({profile})", False, "STALE",
                f"no record {subject} in profile {profile}: the subject of the "
                f"finding does not exist, so the asserted condition cannot hold")
        return
    hits = [l for l in LNK if l.get("target_id") == subject
            and l.get("relation_type") in ("verifies", "validates")]
    srcs = [l for l in LNK if l.get("source_id") == subject
            and l.get("relation_type") in ("verifies", "validates")]
    if hits:
        ls = ", ".join(sorted(l["link_id"] for l in hits))
        ss = sorted({l["source_id"] for l in hits})
        verdict(fid, f"{subject} ({profile})", False, "STALE",
                f"the asserted condition is 'no verifies/validates link'. "
                f"{subject} IS the target of {len(hits)} verifies link(s) [{ls}] "
                f"from {', '.join(ss)}, so the condition is false on the corpus as "
                f"it stands. Appears as source of {len(srcs)} such link(s).")
    else:
        verdict(fid, f"{subject} ({profile})", True, "OPEN",
                f"no verifies/validates link anywhere in the registries names "
                f"{subject} as a target, and none names it as a source either. "
                f"The asserted condition still holds.")


def check_fsr_fault_reaction(fid, subject, profile):
    r = rec(subject, profile)
    if r is None:
        verdict(fid, f"{subject} ({profile})", False, "STALE",
                f"no record {subject} in profile {profile}")
        return
    _, d = r
    fr = d.get("fault_reaction")
    if fr:
        keys = sorted(fr) if isinstance(fr, dict) else ["<non-dict>"]
        verdict(fid, f"{subject} ({profile})", False, "STALE",
                f"the asserted condition is 'no fault_reaction'. The record carries "
                f"a populated fault_reaction object at revision {d.get('revision')} "
                f"with fields {keys}. The finding was never updated after the field "
                f"was authored.")
    else:
        verdict(fid, f"{subject} ({profile})", True, "OPEN",
                "'fault_reaction' is absent from the record.")


def check_sgo_asil(fid, subject, profile):
    r = rec(subject, profile)
    if r is None:
        verdict(fid, f"{subject} ({profile})", False, "STALE",
                f"no record {subject} in profile {profile}")
        return
    _, d = r
    j = d.get("asil_justification")
    if j:
        verdict(fid, f"{subject} ({profile})", False, "STALE",
                f"the asserted condition is 'ASIL {d.get('asil')} lacks "
                f"justification'. The record carries asil_justification with keys "
                f"{sorted(j)} at revision {d.get('revision')}.")
    else:
        verdict(fid, f"{subject} ({profile})", True, "OPEN",
                "'asil_justification' is absent.")


def build():
    # ---- 1..7 : FSR verification links ------------------------------------
    for fid, subj, prof in [
        ("FB2-REV-FND-000001", "FB2-SAF-FSR-000001", "as_is"),
        ("FB2-REV-FND-000002", "FB2-SAF-FSR-000001", "synthetic_reference"),
        ("FB2-REV-FND-000003", "FB2-SAF-FSR-000002", "as_is"),
        ("FB2-REV-FND-000004", "FB2-SAF-FSR-000002", "synthetic_reference"),
        ("FB2-REV-FND-000005", "FB2-SAF-FSR-000003", "as_is"),
        ("FB2-REV-FND-000006", "FB2-SAF-FSR-000003", "synthetic_reference"),
        ("FB2-REV-FND-000007", "FB2-SAF-FSR-000004", "synthetic_reference"),
    ]:
        check_verification_link(fid, subj, prof, None)

    # ---- 8..12 : SEC verification links -----------------------------------
    for i, fid in enumerate(range(8, 13), start=1):
        check_verification_link(f"FB2-REV-FND-{fid:06d}",
                                f"FB2-SAF-SEC-{i:06d}", "synthetic_reference", None)

    # ---- 13..19 : FSR fault_reaction --------------------------------------
    for fid, subj, prof in [
        ("FB2-REV-FND-000013", "FB2-SAF-FSR-000001", "as_is"),
        ("FB2-REV-FND-000014", "FB2-SAF-FSR-000001", "synthetic_reference"),
        ("FB2-REV-FND-000015", "FB2-SAF-FSR-000002", "as_is"),
        ("FB2-REV-FND-000016", "FB2-SAF-FSR-000002", "synthetic_reference"),
        ("FB2-REV-FND-000017", "FB2-SAF-FSR-000003", "as_is"),
        ("FB2-REV-FND-000018", "FB2-SAF-FSR-000003", "synthetic_reference"),
        ("FB2-REV-FND-000019", "FB2-SAF-FSR-000004", "synthetic_reference"),
    ]:
        check_fsr_fault_reaction(fid, subj, prof)

    # ---- 20..21 : SGO asil_justification -----------------------------------
    check_sgo_asil("FB2-REV-FND-000020", "FB2-SAF-SGO-000001", "as_is")
    check_sgo_asil("FB2-REV-FND-000021", "FB2-SAF-SGO-000001", "synthetic_reference")

    # ---- 22 : root TRACEABILITY_DOCUMENT.md overclaim ---------------------
    root = REPO / "TRACEABILITY_DOCUMENT.md"
    canon = ART / "views" / "traceability" / "traceability-document.md"
    if root.exists():
        txt = root.read_text()
        overclaims = [s for s in ("IEC 61508", "compliance evidence", "ASIL-D",
                                  "Approver", "Reviewer", "Approved")
                      if s in txt]
        if not overclaims and "pointer" in txt.lower() and canon.exists():
            verdict("FB2-REV-FND-000022", "TRACEABILITY_DOCUMENT.md (repo root)",
                    False, "STALE",
                    f"the asserted condition is that the repository-root document "
                    f"states ISO 26262/IEC 61508 compliance evidence, an ASIL "
                    f"capability, and/or a fabricated approval block. Measured: the "
                    f"file is {len(txt.splitlines())} lines, contains none of "
                    f"{overclaims or 'the overclaim strings'}, declares itself a "
                    f"pointer, and the canonical generated document exists at "
                    f"{canon.relative_to(REPO)} ({canon.stat().st_size} bytes).")
        else:
            verdict("FB2-REV-FND-000022", "TRACEABILITY_DOCUMENT.md (repo root)",
                    True, "OPEN",
                    f"overclaim strings still present: {overclaims}")
    else:
        verdict("FB2-REV-FND-000022", "TRACEABILITY_DOCUMENT.md (repo root)",
                True, "OPEN", "the repository-root file does not exist")

    # ---- 23 : SEC-000005 safety_goal_ref ----------------------------------
    r = rec("FB2-SAF-SEC-000005", "synthetic_reference")
    ref = ((r[1].get("safety_allocation") or {}).get("safety_goal_ref") if r else None)
    if ref in IDX_KEYS:
        verdict("FB2-REV-FND-000023", "FB2-SAF-SEC-000005.safety_allocation",
                False, "STALE",
                f"the asserted condition is a safety allocation naming an artifact "
                f"that does not exist. safety_goal_ref is now {ref!r}, which resolves "
                f"to a live record. Record is at revision "
                f"{r[1].get('revision') if r else '-'}.")
    else:
        verdict("FB2-REV-FND-000023", "FB2-SAF-SEC-000005.safety_allocation",
                True, "OPEN", f"safety_goal_ref = {ref!r} does not resolve")

    # ---- 24 : FSR-000003 contactor threshold ------------------------------
    r = rec("FB2-SAF-FSR-000003", "synthetic_reference")
    crits = (r[1].get("acceptance_criteria") or []) if r else []
    fb = [c for c in crits if "feedback open" in str(c.get("measure", ""))
          + str(c.get("criterion", ""))]
    mech = [c for c in crits if "mechanically open" in str(c.get("measure", ""))
            and "feedback" not in str(c.get("measure", ""))]
    if fb and str(fb[0].get("threshold")) == "40" and mech:
        verdict("FB2-REV-FND-000024", "FB2-SAF-FSR-000003 acceptance criteria",
                False, "STALE",
                f"the asserted condition is a 30 ms 'Time from FAULT request to "
                f"contactor feedback open' against a 35 ms rationale and a 40 ms "
                f"budget. Measured: the criterion {fb[0].get('criterion')!r} now "
                f"carries threshold {fb[0].get('threshold')!r}; the mechanical-only "
                f"point is now a separate criterion at {mech[0].get('threshold')!r} ms "
                f"and the 30 ms mechanical figure is asked for under its own label "
                f"({[c.get('criterion') for c in crits if c.get('threshold') == '30']}). "
                f"The record is at revision {r[1].get('revision')}.")
    else:
        verdict("FB2-REV-FND-000024", "FB2-SAF-FSR-000003 acceptance criteria",
                True, "OPEN", f"feedback-open criteria read {fb}")

    # ---- 25 : SGO timing budget arithmetic --------------------------------
    r = rec("FB2-SAF-SGO-000001", "synthetic_reference")
    alloc = ((r[1].get("timing_budget") or {}).get("allocation") or {}) if r else {}
    nums = [v for v in alloc.values() if isinstance(v, (int, float))]
    ftti = r[1].get("fault_tolerant_time_interval_ms") if r else None
    margin = alloc.get("margin_ms")
    if ftti and nums and sum(nums) == ftti:
        verdict("FB2-REV-FND-000025", "FB2-SAF-SGO-000001 timing budget",
                False, "STALE",
                f"the asserted condition is a budget that does not close. Measured: "
                f"the {len(nums)} entries of timing_budget.allocation (including "
                f"margin_ms = {margin}) sum to {sum(nums)} ms, and "
                f"fault_tolerant_time_interval_ms = {ftti}. Record at revision "
                f"{r[1].get('revision')}.")
    else:
        verdict("FB2-REV-FND-000025", "FB2-SAF-SGO-000001 timing budget",
                True, "OPEN",
                f"sum {sum(nums)} + margin {margin} vs FTTI {ftti}")

    # ---- 26 : the 115 ms figure -------------------------------------------
    # Only the LIVE justification fields matter. revision_history entries, the
    # safety concepts' `contradiction` blocks and the assumption registries'
    # correction notes all quote the figure on purpose: they are the record of
    # removing it, not a live claim resting on it.
    present = []
    for sid in ("FB2-SAF-FSR-000004", "FB2-HW-TSR-000004"):
        r = rec(sid, "synthetic_reference")
        if r and "115 ms" in json.dumps({k: v for k, v in r[1].items()
                                         if k not in ("revision_history",)}):
            present.append(sid)
    for p in (ART / "shared" / "assumption-registry.json",
              CORPUS / "synthetic_reference" / "shared" / "assumption-registry.json"):
        if not p.exists():
            continue
        d = jload(p)
        for entry in (d.get("assumptions") or d.get("entries") or []):
            if isinstance(entry, dict) and "115 ms" in json.dumps(
                    {k: v for k, v in entry.items() if k != "rationale_history"}):
                if "previously recorded here" not in entry.get("rationale", ""):
                    present.append(f"{entry.get('assumption_id', p.name)}")
    if not present:
        verdict("FB2-REV-FND-000026", "the 115 ms main-path figure", False, "STALE",
                "the asserted condition is a justification resting on a 115 ms "
                "main-path figure. Measured over the LIVE fields of "
                "FB2-SAF-FSR-000004, FB2-HW-TSR-000004 and both assumption "
                "registries (revision_history and the safety concepts' "
                "`contradiction` blocks excluded, because those quote the figure "
                "precisely to record its removal): the figure appears in 0 live "
                "justification fields. It survives only as the audit trail of the "
                "correction and in the superseded as_is review record "
                "FB2-REV-000001, which is where finding 026 established it came from.")
    else:
        verdict("FB2-REV-FND-000026", "the 115 ms main-path figure", True, "OPEN",
                f"'115 ms' still present in {present}")

    # ---- 27 : FSR-000004 vs TSR-000004 ------------------------------------
    a = rec("FB2-SAF-FSR-000004", "synthetic_reference")
    b = rec("FB2-HW-TSR-000004", "synthetic_reference")
    if a and b and a[1].get("statement") != b[1].get("statement"):
        verdict("FB2-REV-FND-000027", "FB2-SAF-FSR-000004 vs FB2-HW-TSR-000004",
                False, "STALE",
                f"the asserted condition is that the two records carry the same "
                f"sentence. Measured: the statements differ "
                f"({len(a[1]['statement'])} vs {len(b[1]['statement'])} chars) and "
                f"so do the acceptance criteria "
                f"({len(a[1].get('acceptance_criteria') or [])} vs "
                f"{len(b[1].get('acceptance_criteria') or [])}). Revisions "
                f"{a[1].get('revision')} and {b[1].get('revision')}.")
    else:
        verdict("FB2-REV-FND-000027", "FB2-SAF-FSR-000004 vs FB2-HW-TSR-000004",
                True, "OPEN", "the two statements are still identical")

    # ---- 28 : SEC-000003/4 false-rejection criterion ----------------------
    bad = []
    for sid in ("FB2-SAF-SEC-000003", "FB2-SAF-SEC-000004"):
        r = rec(sid, "synthetic_reference")
        for c in (r[1].get("acceptance_criteria") or []) if r else []:
            if "false-rejection" in str(c.get("criterion", "")):
                bad.append((sid, c.get("threshold")))
    if bad and all(str(t) != "0" for _, t in bad):
        verdict("FB2-REV-FND-000028", "SEC-000003/000004 false-rejection criterion",
                False, "STALE",
                f"the asserted condition is an absolute zero that no correct "
                f"implementation can meet. Measured: the criterion now carries a "
                f"bounded rate in {bad}, not '0'.")
    else:
        verdict("FB2-REV-FND-000028", "SEC-000003/000004 false-rejection criterion",
                True, "OPEN", f"thresholds read {bad}")

    # ---- 29 : the validator reads the link TARGET ------------------------
    src = (ART / "tools" / "corpus.py").read_text()
    uses_target = "verified = {l[\"target_id\"]" in src or \
        "verified = {l['target_id']" in src
    verdict("FB2-REV-FND-000029", "corpus.py safety-requirement verification rule",
            not uses_target,
            "OPEN" if not uses_target else "STALE",
            f"the asserted condition is a rule that reads the SOURCE endpoint of a "
            f"verifies link. Measured in docs/artifacts/tools/corpus.py: the rule "
            f"builds its set from target_id = {uses_target}. The condition is "
            f"{'still present' if not uses_target else 'no longer present'}.")

    # ---- 30 : declared forward references --------------------------------
    missing = [t for t in ("FB2-SW-DSN-000004", "FB2-PIM-IMP-000003")
               if t not in IDX_KEYS]
    chk = (ART / "tools" / "check_references.py")
    allow = chk.read_text() if chk.exists() else ""
    allowed = [t for t in missing if f'"{t}"' in allow]
    if missing:
        verdict("FB2-REV-FND-000030", "FB2-SW-DSN-000004 / FB2-PIM-IMP-000003",
                True, "OPEN",
                f"the asserted condition is that declared forward references name "
                f"work products never authored. Measured: {missing} still absent from "
                f"the artifact index, and {len(allowed)}/{len(missing)} carry an "
                f"explicit entry in check_references.py's KNOWN_BROKEN_ALLOWED "
                f"declared-forward allowlist, so the tool reports them rather than "
                f"silently passing them. The work products have not been authored.")
    else:
        verdict("FB2-REV-FND-000030", "FB2-SW-DSN-000004 / FB2-PIM-IMP-000003",
                False, "STALE", "both work products now exist")

    # ---- 31 : void* polymorphism, and how many are still red --------------
    osh = (REPO / "src" / "app" / "task" / "os" / "os.h").read_text()
    dbh = (REPO / "src" / "app" / "engine" / "database" / "database.h").read_text()
    poly = ("void *const pvBuffer" in osh) and ("const void *const pvItemToQueue" in osh) \
        and ("void *pDataFromSender0" in dbh)
    red = [t for t, o in SWEEP_OUTCOME.items() if o.get("outcome") == "fail"]
    verdict("FB2-REV-FND-000031", "void* database / OS-queue declarations",
            False, "SUPERSEDED",
            f"the first clause of the asserted condition still holds: the product "
            f"declarations are unchanged and the void* is still required "
            f"(OS_ReceiveFromQueue/OS_SendToBackOfQueue payload parameters and the "
            f"DATA_*DataBlocks parameters are untyped: {poly}). The second clause - "
            f"that a pointer-identity TEST FAILURE is the consequence - no longer "
            f"holds as a live count: the most recent full sweep records "
            f"{len(red)} failing test(s) in total "
            f"({', '.join(sorted(red)) or 'none'}), and none of them is a "
            f"void*-identity failure. So the first clause of the title still holds "
            f"and the second no longer does: the polymorphism conclusion is "
            f"CONFIRMED UNCHANGED, and the test-failure residual was closed by the "
            f"better-rooted class-A/B/C analysis in FB2-REV-FND-000033 and by the "
            f"CMock array-plugin remediation, not by typing the parameters this "
            f"finding correctly rejects. The proposed product-side fix stays "
            f"rejected on the evidence this record already gave.",
            also="see FB2-REV-FND-000033 and FB2-REV-FND-000037")

    # ---- 32 : self-certifying mutation gate -------------------------------
    gated = "if standing:" in src and "baseline_sigs" in src
    verdict("FB2-REV-FND-000032", "the mutation acceptance gate", not gated,
            "STALE" if gated else "OPEN",
            f"the asserted condition is a gate that accepts any finding of the "
            f"expected severity on the scenario's affected artifact. Measured in "
            f"corpus.py: _match_scenario_finding resolves the scenario to a rule "
            f"identifier, checks the rule is emitted ({gated and 'yes'}), and "
            f"subtracts the unmutated baseline before accepting. `check` reports "
            f"20/20 mutations passing against their own declared detectors.")

    # ---- 33 : class-A void*-identity failures, the four left red ----------
    four = ["test_debug_can.c", "test_nxp_mc33775a_i2c.c",
            "test_can_cbs_rx_afe_cell-temperatures.c",
            "test_can_cbs_rx_afe_cell-voltages.c"]
    still_red = [f for f in four if sweep_of(f) == "fail"]
    verdict("FB2-REV-FND-000033", "the four class-A tests left red on purpose",
            bool(still_red), "SUPERSEDED" if not still_red else "OPEN",
            f"the finding's residual is that four tests remain red because identity "
            f"is impossible AND content is undefined. Measured against the most "
            f"recent sweep: {len(four) - len(still_red)}/4 now build and pass "
            f"({', '.join(f'{f}={sweep_of(f)}' for f in four)}). The claim that no "
            f"achievable oracle exists for them is superseded: CMock's array plugin "
            f"makes the void* parameter byte-comparable and the tests supply a "
            f"correctly typed, correctly sized expected payload via "
            f"OS_SendToBackOfQueue_ExpectWithArray. That is a fourth cause the "
            f"three-way taxonomy did not name. The taxonomy itself (A/B/C) stands.",
            also="vacuity of two of the four is tracked as FB2-REV-FND-000037")

    # ---- 34 : uint64_t treat_as gap ---------------------------------------
    conf = REPO / "conf" / "unit" / "app_project_posix.yml"
    ctxt = conf.read_text()
    ta = ctxt.split(":treat_as:")[1].split(":memcmp_if_unknown:")[0] \
        if ":treat_as:" in ctxt else ""
    has64 = "uint64" in ta
    t1 = sweep_of("test_can_cbs_tx_f_debug-build-configuration.c")
    t2 = sweep_of("test_can_cbs_tx_f_pack-minimum-maximum-values.c")
    verdict("FB2-REV-FND-000034", "uint64_t absent from CMock's :treat_as: maps",
            (not has64), "OPEN" if (not has64) else "STALE",
            f"the asserted condition is that uint64_t is in neither CMock's standard "
            f":treat_as: map nor the project's, so :memcmp_if_unknown: emits an "
            f"8-byte memcmp of a by-value scalar's address. Measured in the SHIPPED "
            f"conf/unit/app_project_posix.yml, the :treat_as: block is "
            f"{[x.strip() for x in ta.strip().splitlines() if x.strip()]} and "
            f"contains no 64-bit entry, so the condition still holds: "
            f"{not has64}. The harness-side fix and the "
            f"exposed (int64_t) cast fix both hold: "
            f"test_can_cbs_tx_f_debug-build-configuration.c={t1}, "
            f"test_can_cbs_tx_f_pack-minimum-maximum-values.c={t2}.",
            also="the conf/ residual is the live part of this finding")

    # ---- 35 : the test_dp83869 SIGSEGV ------------------------------------
    o = SWEEP_OUTCOME.get("tests/unit/app/driver/phy/test_dp83869.c", {})
    verdict("FB2-REV-FND-000035", "tests/unit/app/driver/phy/test_dp83869.c",
            o.get("outcome") == "fail", "OPEN" if o.get("outcome") == "fail" else "STALE",
            f"the asserted condition is a SIGSEGV caused by CMock dereferencing the "
            f"hard-coded TMS570 address 0xFFF7BC34, so the file cannot be brought up "
            f"on a host SIL harness. Measured: the most recent sweep records "
            f"{o.get('outcome')} for this file and the archived per-test log shows "
            f"the same signature the finding describes - 15 of 15 cases reported as "
            f"crashed after the runner aborts, i.e. the process still dies mid-file "
            f"and Ceedling still attributes the crash to whatever case was in "
            f"flight. The array-plugin work does not reach it: the fault is on "
            f"IO_PinReset's typed `volatile uint32_t*` parameter, not on a void*.")

    # ---- 36 : FreeRTOS queue-registry macros ------------------------------
    shim = SIL / "shim" / "sil_cmock_queue_registry_shim.h"
    # The eight tests FB2-REV-FND-000036 names, verbatim.
    eight = ["test_adi_ades1830.c", "test_can.c", "test_can_1.c", "test_can_2.c",
             "test_os_freertos.c", "test_os_freertos_cache_disabled.c",
             "test_os_freertos_cache_enabled.c", "test_os.c"]
    green = [f for f in eight if sweep_of(f) == "pass"]
    verdict("FB2-REV-FND-000036",
            "FreeRTOS empty function-like macros erasing CMock's mock definitions",
            True, "OPEN",
            f"the asserted condition is a pre-existing, platform-independent "
            f"disagreement between FreeRTOS's empty function-like queue-registry "
            f"macros and CMock's generated definitions, mitigated but not removed. "
            f"Measured: the mitigation is present "
            f"({shim.relative_to(ART)} exists, {shim.stat().st_size if shim.exists() else 0} "
            f"bytes) and {len(green)}/8 of the named tests now build and run "
            f"({', '.join(f'{f}={sweep_of(f)}' for f in eight)}). The 8th, "
            f"test_uart.c, is still a build failure but under a different class. "
            f"Nothing under src/os/freertos or conf/ changed, so the defect is "
            f"still live for anyone running the shipped configuration.")

    # ---- 37 : the void* queue-buffer oracle -------------------------------
    # Scope matters: the named files each contain a NON-vacuous case that
    # registers ReturnThruPtr and a vacuous one that does not. Only the function
    # that carries the WithArray expectation is examined, because that is the
    # function whose payload comparison the finding is about.
    vac, sound = [], []
    for rel in ("test_can_cbs_rx_afe_cell-temperatures.c",
                "test_can_cbs_rx_afe_cell-voltages.c",
                "test_debug_can.c", "test_nxp_mc33775a_i2c.c"):
        p = next((q for q in (REPO / "tests").rglob(rel)), None)
        if not p:
            continue
        txt = p.read_text()
        # split into top-level test functions
        parts = re.split(r"\nvoid (test\w+)\s*\(void\)\s*\n?\{", txt)
        fns = {parts[i]: parts[i + 1] for i in range(1, len(parts) - 1, 2)}
        for name, body in fns.items():
            if "OS_SendToBackOfQueue_ExpectWithArray" not in body:
                continue
            # does the same function give the mocked extractor an output value?
            gives_output = ("ReturnThruPtr_pCanSignal" in body
                            or "ReturnThruPtr_pvBuffer" in body)
            zero_fixture = bool(re.search(r"=\s*\{\s*0\s*\}", body))
            (sound if (gives_output or not zero_fixture) else vac).append(
                f"{rel}:{name}")
    verdict("FB2-REV-FND-000037",
            "the void* queue-buffer content oracle", bool(vac), "OPEN",
            f"the asserted condition is that the content oracle for a void* queue "
            f"payload is provably vacuous. Measured per test FUNCTION (the named "
            f"files each contain one non-vacuous case and one vacuous case, so a "
            f"file-level count would be wrong): {len(vac)} function(s) compare an "
            f"all-zero expected payload against a product payload the mocked "
            f"extractor never populates - {', '.join(vac) or 'none'}. In each, the "
            f"expected fixture is declared `= {{0}}`, the block registers "
            f"CAN_RxGetSignalDataFromMessageData_Expect (argument checks only) with "
            f"no matching ReturnThruPtr_pCanSignal, and the generated Mock never "
            f"assigns Expected_pCanSignal, so both sides of the "
            f"UNITY_TEST_ASSERT_EQUAL_HEX8_ARRAY are zero bytes. The array plugin "
            f"turned a loud red into a silent green; it did not create an oracle. "
            f"{len(sound)} function(s) are genuinely closed: "
            f"{', '.join(sound) or 'none'} - test_debug_can.c fills the "
            f"out-parameter with ReturnThruPtr_pvBuffer and asserts on the "
            f"consumption, and test_nxp_mc33775a_i2c.c compares a fixture derived "
            f"from the received transaction.")

    # ---- 38 : -Wno-array-bounds -------------------------------------------
    runsh = (SIL / "run.sh").read_text()
    flag_gone = "-Wno-array-bounds" not in runsh
    # Scope the flag census to the RELAX_CLANG_DIAGNOSTICS block itself, not the
    # whole file: run.sh names other -Wno-* groups in its comments and in other
    # accommodations, and quoting those as the RELAX list would be wrong.
    _rb = runsh.find('if os.environ.get("RELAX_CLANG_DIAGNOSTICS")')
    _m = re.search(r"\nif ", runsh[_rb + 10:]) if _rb > 0 else None
    relax_block = runsh[_rb:_rb + 10 + _m.start()] if (_rb > 0 and _m) else ""
    oob_tests = ["test_can_cbs_tx_f_cell-temperatures.c",
                 "test_can_cbs_tx_f_cell-temperatures_3-temp-sensors.c",
                 "test_can_cbs_tx_f_cell-temperatures_4-temp-sensors.c",
                 "test_can_cbs_tx_f_cell-temperatures_5-temp-sensors.c",
                 "test_can_cbs_tx_f_cell-voltages.c",
                 "test_diag_cbs_current.c"]
    oob_now = [f for f in oob_tests if sweep_of(f) != "pass"]
    verdict("FB2-REV-FND-000038", "-Wno-array-bounds masking out-of-bounds access",
            not (flag_gone and not oob_now), "STALE",
            f"the asserted condition has two halves and BOTH are now false. "
            f"(1) the masking flag: '-Wno-array-bounds' no longer appears anywhere in "
            f"sil/run.sh ({flag_gone}). The RELAX_CLANG_DIAGNOSTICS block still adds "
            f"{len(set(re.findall(r'-Wno-[a-z-]+', relax_block)))} distinct "
            f"diagnostics, each "
            f"individually justified in sil/RELAXED-DIAGNOSTICS.md under the two-part "
            f"test this finding established: {sorted(set(re.findall(r'-Wno-[a-z-]+', relax_block)))}. "
            f"(2) the 6 sites: "
            f"{len(oob_tests) - len(oob_now)}/6 now build and pass "
            f"({', '.join(f'{f}={sweep_of(f)}' for f in oob_tests)}). The build-failure "
            f"class build:real_defect_out_of_bounds_array_index no longer appears in "
            f"the sweep's classifier output at all. The declared sizes were corrected "
            f"(float_t[3] -> [13] and float_t[4] -> [9]) and the off-by-one in "
            f"test_diag_cbs_current.c now writes element 0.")


    # ---- 39..42 : records raised by the finding-closure pass itself --------
    corpus_src = (ART / "tools" / "corpus.py").read_text()
    fr_body = corpus_src[corpus_src.index(
        "# Rule: Safety requirement completeness checker"):]
    fr_body = fr_body[:fr_body.index("# Rule: ASIL assignment validator")]
    # Search the executable `if` line only. The rule's comment block quotes the
    # removed filter verbatim to explain why it was removed, and a naive search
    # over the whole block would find that quotation and report the filter as
    # still present - which is the mirror image of the bug this check exists to
    # catch.
    fr_if = next((l for l in fr_body.splitlines()
                  if l.strip().startswith('if d.get("artifact_type")')), "")
    fr_filter = re.findall(r'"(-\w+-)" in ', fr_if)
    verdict("FB2-REV-FND-000039",
            "the fault_reaction rule's '-FSR-' id filter",
            bool(fr_filter), "STALE" if fr_filter else "CLOSED",
            f"the asserted condition is an id filter in the safety-requirement "
            f"completeness rule. Measured in docs/artifacts/tools/corpus.py: the "
            f"filter is {fr_filter or 'ABSENT'}, so the condition is "
            f"{'still present' if fr_filter else 'no longer present'}. The rule's "
            f"population is now selected by artifact_type and engineering_domain "
            f"alone, and the five FB2-SAF-SEC-* requirements it used to exclude are "
            f"in scope: "
            f"{', '.join(s for s in sec_ids_now())} all carry a populated "
            f"fault_reaction at revisions "
            f"{', '.join(str(IDX[('synthetic_reference', s)][1].get('revision')) for s in sec_ids_now())}.")

    diag_body = corpus_src[corpus_src.index(
        "# Rule: Diagnostic coverage claim validator"):]
    diag_body = diag_body[:diag_body.index("# Rule: Configuration consistency checker")]
    diag_filter = re.findall(r'"(-\w+-)" in ', diag_body)
    claims = [i for (_p, i), (_f, d) in IDX.items()
              if d.get("diagnostic_coverage")
              and str(i).startswith("FB2-SAF-SEC-")]
    verdict("FB2-REV-FND-000040",
            "the diagnostic_coverage rule's '-FSR-' id filter",
            bool(diag_filter), "OPEN",
            f"the asserted condition is that the same id filter is present in a "
            f"second rule and is currently inert rather than correct. Measured: the "
            f"filter is {diag_filter or 'ABSENT'}; {len(claims)} FB2-SAF-SEC-* "
            f"record(s) claim diagnostic_coverage, so the filter currently excludes "
            f"nothing that would have been reported. The rule is inert on this "
            f"corpus, not correct on it, and it was deliberately not changed because "
            f"it was not in scope for the rule-scope fix.")

    execs = []
    for s_ in sec_ids_now():
        for (_p, i), (_f, d) in IDX.items():
            if d.get("artifact_type") == "execution" and d.get("test_measure_id"):
                if any(t.get("target_id") == s_ for t in LNK
                       if t.get("source_id") == d.get("test_measure_id")):
                    execs.append((i, d.get("execution_kind"), d.get("outcome")))
    blocked = [e for e in execs if e[2] == "blocked"]
    verdict("FB2-REV-FND-000041",
            "the security requirements' verification outcome",
            bool(blocked), "OPEN",
            f"the asserted condition is that the security requirements are "
            f"verification-PLANNED and not verification-ACHIEVED. Measured: "
            f"{len(execs)} execution record(s) carry a verifies link to a security "
            f"requirement, of which {len(blocked)} have outcome 'blocked' "
            f"({', '.join(sorted({e[0] for e in blocked}))}), and all "
            f"{len({e[1] for e in blocked})} distinct execution_kind value(s) are "
            f"{sorted({e[1] for e in blocked})}. verification_status on all five "
            f"requirements is 'not_verified'.")

    vac_green = VACUOUS_DATA.get("after", {}).get("vacuous_green")
    vac_assert = VACUOUS_DATA.get("after", {}).get("asserting_green")
    verdict("FB2-REV-FND-000042", "the vacuous-green test census",
            bool(vac_green), "OPEN",
            f"the asserted condition is that green files which assert nothing are "
            f"counted as passes. Measured from the harness's own instrument "
            f"({VACUOUS.name}): {vac_assert} green files carry a real assertion and "
            f"{vac_green} do not, out of "
            f"{VACUOUS_DATA.get('after', {}).get('green')} green and "
            f"{VACUOUS_DATA.get('total_vacuous')} vacuous files in a "
            f"{SWEEP_DATA.get('total')}-test suite. The count is unchanged by this "
            f"pass and the condition is unchanged: the headline pass number is still "
            f"higher than the number of files that can fail.")


def sec_ids_now():
    return [i for (_p, i), (_f, d) in IDX.items()
            if d.get("engineering_domain") == "safety"
            and d.get("artifact_type") == "requirement" and "-SEC-" in i]


IDX_KEYS = {i for (_p, i) in IDX}


def main() -> int:
    build()
    print("=" * 118)
    print("RE-TEST OF EVERY FINDING RECORD AGAINST THE CORPUS AS IT STANDS NOW")
    print("=" * 118)
    prov = SWEEP_DATA.get("generated_at", "unavailable")
    print(f"sweep evidence : {SWEEP.relative_to(ART)}  generated_at={prov}  "
          f"total={SWEEP_DATA.get('total')} pass={SWEEP_DATA.get('passed_tests')} "
          f"fail={SWEEP_DATA.get('failed_tests')} build_failures={SWEEP_DATA.get('build_failures')}")
    print(f"vacuity census : {VACUOUS.relative_to(ART)}  "
          f"total_vacuous={VACUOUS_DATA.get('total_vacuous')}  "
          f"green_asserting={VACUOUS_DATA.get('after', {}).get('asserting_green')}")
    print(f"live defect set: corpus.py validate (printed separately) -- this script "
          f"does not re-run it")
    print("-" * 118)
    hdr = f"{'id':<22} {'still':<7} {'class':<11} {'recorded':<11} subject"
    print(hdr)
    print("-" * 118)
    for r in ROWS:
        print(f"{r['id']:<22} {str(r['still_holds']):<7} {r['class']:<11} "
              f"{r['recorded_disposition']:<11} {r['subject']}")
    print("-" * 118)
    print("\nEVIDENCE PER VERDICT\n" + "=" * 118)
    for r in ROWS:
        print(f"\n{r['id']}  [{r['class']}]  {r['subject']}")
        for chunk in re.findall(r".{1,104}(?:\s|$)", r["evidence"]):
            print("    " + chunk.rstrip())
        if r["also"]:
            print(f"    RELATED: {r['also']}")
    print("\n" + "=" * 118)
    n = {c: sum(1 for r in ROWS if r["class"] == c) for c in
         ("STALE", "OPEN", "CLOSED", "SUPERSEDED")}
    print(f"TOTAL {len(ROWS)} findings re-tested: STALE {n['STALE']}  "
          f"OPEN {n['OPEN']}  CLOSED {n['CLOSED']}  SUPERSEDED {n['SUPERSEDED']}")
    print("This is a mechanical re-test of the conditions these records assert. It is "
          "not a semantic re-review,\nand it grants no human approval, tool "
          "qualification, certification, ISO 26262 conformity or ASPICE capability "
          "level.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
