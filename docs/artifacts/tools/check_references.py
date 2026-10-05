#!/usr/bin/env python3
"""Resolve every ID-shaped cross-reference in the corpus and check the FTTI arithmetic.

This tool exists because the corpus has no rule that resolves the free-string
ID references that live inside payload fields (``safety_allocation.safety_goal_ref``,
``affected_safety_goals_or_requirements``, ``functional_safety_requirements``,
``feasibility_dependencies``, ...). The link validator only resolves ids that are
expressed as links, so a mistyped id in a payload field is invisible to it. That
is the class of defect recorded as finding FB2-REV-FND-000023.

Two checks:

1. REFERENCE RESOLUTION
   Every string anywhere in every corpus/scenario record that has the shape of a
   corpus artifact id (``FB2-<DOMAIN>-<TYPE>-<NNNNNN>``) must resolve to an
   artifact that exists in the index. Source anchors (``FB2-SRC-...``) and
   assumptions (``FB2-ASM-...``) resolve against their own registries. The known
   exceptions are the registries that hold the definitions themselves, and the
   scenario mutation fixtures, which deliberately corrupt a record so the
   detectors have something to find.

2. FTTI ARITHMETIC
   For every safety goal, every timing budget found anywhere in the corpus must
   satisfy ``sum(serial elements) + margin <= FTTI`` and
   ``sum(serial elements) + margin == FTTI`` for a budget that claims to be the
   allocation of that goal's interval. The budget keys that name the interval
   itself (``total_ftti_ms``, ``ftti_ms``) and margin keys are excluded from the
   serial sum, matching the corpus validator's own MUT-006 rule.

Usage:  python3 docs/artifacts/tools/check_references.py [--root PATH]
Exit code 0 when every check passes, 1 otherwise.
"""

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
ARTIFACTS = REPO_ROOT / "docs" / "artifacts"

# FB2-<DOMAIN>-<TYPE>-<digits>; DOMAIN/TYPE are 2-4 upper-case words.
ID_RE = re.compile(r"^FB2-[A-Z0-9]{2,6}(?:-[A-Z0-9]{2,6}){1,2}-\d{4,6}$")
SRC_RE = re.compile(r"^FB2-SRC-[A-Z0-9]+-\d{4,6}$")
ASM_RE = re.compile(r"^FB2-ASM-\d{4,6}$")
LNK_RE = re.compile(r"^FB2-LNK-[A-Z0-9]+-\d{4,6}$")
PRM_RE = re.compile(r"^FB2-PRM-\d{4,6}$")

# Fields whose contents are *declared* by this very registry entry, so an id that
# does not resolve here is not a defect in the referring record.
REGISTRY_SELF_FIELDS = ("artifact_id", "id", "assumption_id", "link_id", "measure_id",
                        "parameter_id", "cell_ref", "element_id", "requirement_id",
                        "interface_id", "link_id")

# Fixtures that must contain a broken reference on purpose.
KNOWN_BROKEN_ALLOWED = (
    "scenarios/mutations/",
    "scenarios/evaluator-only/",
    "scenarios/positive/",
    "corpus/as_is/NOTE-gap",
    ".work/",
)

# References to work products a planning record DECLARES but that the corpus has
# never authored. These are not typos: each names an id that has never existed, so
# they cannot be repaired by correcting a value. They are recorded as finding
# FB2-REV-FND-000030 and listed here so that this tool reports them as declared
# forward references rather than passing them silently or failing as if they were
# transcription errors. Adding an id to this list is a decision to leave a known gap
# visible, not a decision that the gap does not exist.
DECLARED_FORWARD_REFERENCES = {
    "FB2-SW-DSN-000004": (
        "Named by FB2-SW-DSN-000001's decomposition[2].child_id in both the as_is and the "
        "synthetic_reference copies. Only FB2-SW-DSN-000001..000003 exist. "
        "Finding FB2-REV-FND-000030."),
    "FB2-PIM-IMP-000003": (
        "Named by project-plan.json WBS-008 deliverable_records[4] and by "
        "measurement-plan.json MET-06 linked_improvement_records[0]. Only "
        "FB2-PIM-IMP-000001 and FB2-PIM-IMP-000002 exist. Finding FB2-REV-FND-000030."),
}

# Ids that are local to the record that names them, not references to artefacts.
# Note that child_id is NOT in this list: a decomposition entry's child_id is a
# containment edge between two records and must resolve.
LOCAL_ID_FIELDS = ("decision_id", "self_id")


def load_json(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def artifact_index():
    """(profile, id) -> path, built the same way corpus.py builds it.

    corpus.py indexes corpus/ and reviews/ together, then the scenario tree
    separately (minus evaluator-only). This mirrors that so the sweep sees the
    same population of records the validator does.
    """
    index = {}
    bases = [ARTIFACTS / "corpus", ARTIFACTS / "reviews"]
    scen = ARTIFACTS / "scenarios"
    if scen.exists():
        bases.append(scen)
    for base in bases:
        if not base.exists():
            continue
        for p in sorted(base.rglob("*.json")):
            if ".work" in p.parts or "evaluator-only" in p.parts:
                continue
            try:
                d = load_json(p)
            except Exception:
                continue
            if not isinstance(d, dict):
                continue
            prof = d.get("profile")
            aid = d.get("id")
            if prof and aid:
                index.setdefault((prof, aid), p)
                index.setdefault(("*", aid), p)
    return index


def finding_index():
    """finding_id -> (path, owning review id), from the findings review OUTPUT.

    A finding is not an indexed artefact: it is nested inside the review record
    that raised it, and the artifact index keys on the record's own `id`. So
    before this existed, ANY record that carried a bare `FB2-REV-FND-...` string
    in an id-shaped field was reported as dangling - including references to
    findings that exist. That is the same class of error as reading a coverage
    figure out of a report instead of the JSON: the reference resolves and the
    tool had no registry to resolve it against.

    Both the findings and the dispositions are collected, because a disposition
    names the finding it answers and a finding may be recorded without one.
    Resolving them is strictly more checking, not less: a mistyped finding id
    now fails where it previously would not have been looked at.
    """
    findings = set()
    recs = ARTIFACTS / "reviews" / "records"
    if not recs.exists():
        return findings
    for p in sorted(recs.glob("*.json")):
        try:
            d = load_json(p)
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        for entry in (d.get("findings") or []) + (d.get("dispositions") or []):
            if isinstance(entry, dict) and entry.get("finding_id"):
                findings.add(str(entry["finding_id"]).strip())
    return findings


def registries():
    anchors, assumptions, links, params = set(), set(), set(), set()
    sr = ARTIFACTS / "sources" / "source-registry.json"
    if sr.exists():
        for a in load_json(sr).get("anchors", []):
            anchors.add(a.get("anchor_id"))
    for ar in (ARTIFACTS / "shared" / "assumption-registry.json",
               ARTIFACTS / "corpus" / "synthetic_reference" / "shared" / "assumption-registry.json"):
        if ar.exists():
            for a in load_json(ar).get("assumptions", []):
                assumptions.add(a.get("assumption_id", a.get("id")))
    for lr in (ARTIFACTS / "traceability", ARTIFACTS / "corpus"):
        for p in sorted(lr.rglob("links-*.json")):
            d = load_json(p)
            entries = d if isinstance(d, list) else d.get("links", [])
            for l in entries:
                links.add(l.get("link_id"))
    for pr in (ARTIFACTS / "shared" / "parameter-registry.json",
               ARTIFACTS / "corpus" / "synthetic_reference" / "shared" / "parameter-registry.json"):
        if pr.exists():
            for a in load_json(pr).get("parameters", []):
                params.add(a.get("id", a.get("parameter_id")))
    return anchors, assumptions, links, params


def walk(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from walk(v, f"{path}.{k}" if path else k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk(v, f"{path}[{i}]")
    else:
        yield path, node


def check_references():
    index = artifact_index()
    anchors, assumptions, links, params = registries()
    findings = finding_index()
    known = anchors | assumptions | links | params | findings
    all_ids = {k[1] for k in index}
    dangling = []
    declared_forward = []
    files_scanned = 0
    strings_checked = 0

    for base in (ARTIFACTS / "corpus", ARTIFACTS / "scenarios"):
        if not base.exists():
            continue
        for p in sorted(base.rglob("*.json")):
            rel = str(p.relative_to(ARTIFACTS))
            if any(rel.startswith(k) or k in rel for k in KNOWN_BROKEN_ALLOWED):
                continue
            try:
                d = load_json(p)
            except Exception:
                continue
            if not isinstance(d, dict):
                continue
            files_scanned += 1
            for field, value in walk(d):
                if not isinstance(value, str):
                    continue
                v = value.strip()
                if not ID_RE.match(v):
                    continue
                leaf = field.split(".")[-1].split("[")[0]
                if leaf in REGISTRY_SELF_FIELDS or leaf in LOCAL_ID_FIELDS:
                    continue
                strings_checked += 1
                if v in known or v in all_ids:
                    continue
                if v in DECLARED_FORWARD_REFERENCES:
                    declared_forward.append((rel, field, v,
                                            DECLARED_FORWARD_REFERENCES[v]))
                    continue
                dangling.append((rel, field, v))

    return dangling, declared_forward, files_scanned, strings_checked


#: Field names that hold a serial timing allocation, as opposed to a per-signal
#: timing table. A per-signal table lists many independent transfers and summing it
#: is meaningless; a serial allocation is one chain from the fault request to the
#: safe state.
BUDGET_CONTAINER_KEYS = ("allocation", "timing_budget", "timing_budget_allocation",
                         "ftti_and_timing_budget")


def _budgets(doc, where, out):
    """Collect every serial timing allocation in a document.

    Yields (path, budget_dict, enclosing_dict) so that a budget's own FTTI can be
    read from the object that contains it - a concept puts ``ftti_ms`` on the
    ``ftti_and_timing_budget`` object while the allocation itself is one level in.
    """
    def rec(node, path, parent):
        if isinstance(node, dict):
            for k, v in node.items():
                if k in BUDGET_CONTAINER_KEYS and isinstance(v, dict) \
                        and any(str(x).endswith("_ms") for x in v):
                    out.append((f"{where}:{path}.{k}", v, node))
                elif k in BUDGET_CONTAINER_KEYS and isinstance(v, dict) \
                        and "allocation" in v and isinstance(v["allocation"], dict):
                    out.append((f"{where}:{path}.{k}.allocation", v["allocation"], v))
                rec(v, f"{path}.{k}" if path else k, node)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                rec(v, f"{path}[{i}]", parent)
    rec(doc, "", None)


def _ftti_of(*docs):
    for d in docs:
        if not isinstance(d, dict):
            continue
        v = d.get("fault_tolerant_time_interval_ms") or d.get("ftti_ms")
        if v is None:
            f = d.get("ftti")
            v = f.get("value") if isinstance(f, dict) else f
        if v is not None:
            return v
    return None


def _serial_and_margin(budget):
    """Split a serial allocation into its work elements, its margin and its total.

    Only ``*_ms`` keys count: a ``*_us`` entry in the same table is a different
    unit and a serial budget expressed in microseconds alongside milliseconds is
    not a budget this check can adjudicate, so it is excluded and reported by the
    unit check the corpus validator already runs (MUT-004). Keys naming the total
    or the interval itself are excluded, which is what the corpus validator's own
    MUT-006 rule does.
    """
    serial_keys, serial = [], 0
    margin = None
    for k, v in budget.items():
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            continue
        ks = str(k)
        if not ks.endswith("_ms"):
            continue
        if ks.startswith("total_") or "ftti" in ks or "interval" in ks:
            continue
        if "margin" in ks:
            margin = v if margin is None else margin + v
            continue
        if "parallel" in ks:
            continue
        serial_keys.append(ks)
        serial += v
    return serial_keys, serial, margin


def check_ftti():
    """Every serial timing allocation anywhere in the corpus must close against its FTTI.

    Scans every record, not only the safety goals, because a budget can be
    published in a concept or an analysis as well as in the goal it allocates, and
    a budget that closes in one record and not in the other is exactly the class
    of defect this tool exists to find.
    """
    rows, failures = [], []
    seen_paths = set()
    for prof, path in sorted({(k[0], str(v)) for k, v in artifact_index().items() if k[0] != "*"}):
        if path in seen_paths or any(x in path for x in KNOWN_BROKEN_ALLOWED):
            continue
        seen_paths.add(path)
        try:
            doc = load_json(path)
        except Exception:
            continue
        if not isinstance(doc, dict) or not doc.get("id"):
            continue
        aid = doc["id"]
        rel = str(Path(path).relative_to(ARTIFACTS))
        budgets = []
        _budgets(doc, f"{aid} ({rel})", budgets)
        for where, b, enclosing in budgets:
            serial_keys, serial, margin = _serial_and_margin(b)
            if not serial_keys:
                continue
            declared = b.get("total_ftti_ms")
            ftti = _ftti_of(enclosing, doc)
            if ftti is None and declared is not None:
                ftti = declared
            total = serial + (margin or 0)
            rows.append({"budget": where, "ftti_ms": ftti, "serial_ms": serial,
                         "margin_ms": margin, "total_ms": total,
                         "serial_keys": serial_keys,
                         "declared_total_ftti_ms": declared})
            if ftti is None:
                failures.append((where, f"serial {serial} ms cannot be checked: the record states no "
                                        f"fault-tolerant time interval for it to close against"))
            elif total > ftti:
                failures.append((where, f"serial {serial} ms + margin {margin or 0} ms = {total} ms "
                                        f"exceeds the FTTI of {ftti} ms"))
            if declared is not None and total != declared:
                failures.append((where, f"serial {serial} ms + margin {margin or 0} ms = {total} ms "
                                        f"!= the record's own declared total_ftti_ms of {declared} ms"))
        # A record that publishes its own arithmetic_check must state arithmetic
        # that closes. This is the block FB2-SAF-TSC-000001 uses, and it is checked
        # here so that a concept cannot publish a self-consistent check against a
        # budget that does not close.
        for ac_path, ac, ac_parent in _arithmetic_checks(doc, f"{aid} ({rel})"):
            s = ac.get("serial_sum_ms")
            m = ac.get("margin_ms")
            ftti = _ftti_of(ac, ac_parent, doc)
            if s is None or ftti is None:
                continue
            t = s + (m or 0)
            rows.append({"budget": ac_path, "ftti_ms": ftti, "serial_ms": s, "margin_ms": m,
                         "total_ms": t, "serial_keys": ["serial_sum_ms"],
                         "declared_total_ftti_ms": None})
            if t > ftti:
                failures.append((ac_path, f"declared serial {s} ms + margin {m or 0} ms = {t} ms "
                                          f"exceeds the FTTI of {ftti} ms"))
            if t != ftti:
                failures.append((ac_path, f"declared serial {s} ms + margin {m or 0} ms = {t} ms "
                                          f"does not equal the FTTI of {ftti} ms that the same record "
                                          f"claims to close at"))
    return rows, failures


def _arithmetic_checks(doc, where, out=None):
    out = [] if out is None else out
    def rec(node, path, parent):
        if isinstance(node, dict):
            for k, v in node.items():
                if k == "arithmetic_check" and isinstance(v, dict):
                    out.append((f"{where}:{path}.arithmetic_check" if path else
                                f"{where}:arithmetic_check", v, node))
                rec(v, f"{path}.{k}" if path else k, node)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                rec(v, f"{path}[{i}]", node)
    rec(doc, "", None)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=None, help="repository root (default: auto-detect)")
    args = ap.parse_args()
    if args.root:
        global ARTIFACTS, REPO_ROOT
        REPO_ROOT = Path(args.root).resolve()
        ARTIFACTS = REPO_ROOT / "docs" / "artifacts"

    print("=" * 78)
    print("CHECK 1 - cross-reference resolution")
    print("=" * 78)
    dangling, declared_forward, files, strings = check_references()
    print(f"  corpus/scenario records scanned : {files}")
    print(f"  id-shaped strings resolved       : {strings}")
    if dangling:
        print(f"  UNRESOLVED REFERENCES            : {len(dangling)}")
        for rel, field, v in dangling:
            print(f"    {rel} :: {field} -> {v}")
    else:
        print("  unresolved references            : 0  (every safety_goal_ref and")
        print("                                      cross-reference resolves)")
    print()
    if declared_forward:
        print(f"  declared forward references      : {len(declared_forward)} occurrence(s) of "
              f"{len({v for _, _, v, _ in declared_forward})} distinct id(s).")
        print("    These are NOT typos: each names a work product a planning record declares")
        print("    and the corpus has never authored, so they cannot be repaired by correcting")
        print("    a value. They are recorded as finding FB2-REV-FND-000030 and are reported")
        print("    here rather than passed silently.")
        for rel, field, v, why in declared_forward:
            print(f"    {v}")
            print(f"      at   {rel} :: {field}")
            print(f"      why  {why}")
    else:
        print("  declared forward references      : 0")

    print()
    print("=" * 78)
    print("CHECK 2 - FTTI arithmetic")
    print("=" * 78)
    rows, failures = check_ftti()
    if not rows:
        print("  no timing budgets found")
    for r in rows:
        print(f"  {r['budget']}")
        print(f"    FTTI              = {r['ftti_ms']} ms")
        print(f"    serial work       = {r['serial_ms']} ms  "
              f"({len(r['serial_keys'])} elements)")
        print(f"    margin            = {r['margin_ms']} ms")
        print(f"    serial + margin   = {r['total_ms']} ms")
        if r["declared_total_ftti_ms"] is not None:
            print(f"    declared total    = {r['declared_total_ftti_ms']} ms")
        if r["ftti_ms"] is None:
            verdict = "NOT CHECKABLE (no FTTI stated)"
        elif r["total_ms"] > r["ftti_ms"]:
            verdict = "DOES NOT CLOSE"
        elif r["total_ms"] == r["ftti_ms"]:
            verdict = "CLOSES (exactly, zero residual)"
        else:
            verdict = f"CLOSES ({r['ftti_ms'] - r['total_ms']} ms residual)"
        print(f"    verdict           = {verdict}")
    if failures:
        print(f"  ARITHMETIC FAILURES               : {len(failures)}")
        for where, why in failures:
            print(f"    {where}: {why}")
    else:
        print("  arithmetic failures              : 0  (every budget closes)")

    ok = not dangling and not failures
    print()
    print(f"RESULT: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
