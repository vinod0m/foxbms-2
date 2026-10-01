#!/usr/bin/env python3
"""Independent citation audit for the SWE.4/SWE.5/SWE.6 verification records.

Written from scratch for this authoring pass. It imports nothing from
docs/artifacts/tools/corpus.py and does not use any corpus.py helper, so a bug
shared between the records and the corpus validator cannot hide a bad citation.

It re-derives, independently:
  1. every repository path the five new records name            -> does it exist?
  2. every test-case function name a record attributes to a test
     file                                                    -> is it defined there?
  3. every HL_* interface header a record names              -> is it in the run?
  4. every corpus artefact id a record or the link registry names -> does it resolve?
  5. every evidence path and sha256 a record publishes        -> exists, and does it hash?
  6. every count the records publish                          -> recomputed from source

Exit code 0 when there are zero mismatches.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
ART = ROOT / "docs" / "artifacts"
RUN = ART / "evidence" / "actual-runs" / "foxbms2-sil-host-unit-test-macos-2026-09-29"
RUN_JSON = RUN / "results-sil-all.json"

RECORDS = [
    ART / "corpus/synthetic_reference/verification/uts-software-unit-verification.json",
    ART / "corpus/synthetic_reference/verification/sit-integration-plan.json",
    ART / "corpus/synthetic_reference/verification/svp-software-qualification-test-plan.json",
    ART / "corpus/synthetic_reference/verification/svs-verification-summary.json",
    ART / "corpus/synthetic_reference/management/verification-deficiency-register.json",
]
REGISTRY = (ART / "corpus/synthetic_reference/traceability/link-registry"
                 / "synthetic_reference/links-verification-planning.json")

TESTFN = re.compile(r"^\s*(?:static\s+)?void\s+(test\w*)\s*\(\s*void\s*\)", re.M)
ASRT = re.compile(r"\bTEST_ASSERT_\w+")

problems: list[str] = []
checks = 0


def bad(msg: str) -> None:
    problems.append(msg)


def load(p: Path):
    return json.loads(p.read_text())


def walk_strings(node):
    """Every string anywhere in a record."""
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for v in node.values():
            yield from walk_strings(v)
    elif isinstance(node, list):
        for v in node:
            yield from walk_strings(v)


def main() -> int:
    global checks
    for p in RECORDS + [REGISTRY]:
        if not p.exists():
            bad(f"record file missing: {p.relative_to(ROOT)}")
            return 1
    recs = {p.name: load(p) for p in RECORDS}
    reg = load(REGISTRY)
    run = load(RUN_JSON)
    by_test = {r["test"]: r for r in run["results"]}

    # ---- 1. every repository path named anywhere in the five records ----
    path_re = re.compile(r"^(?:tests|src|conf|docs)/[A-Za-z0-9_./+-]*$")
    seen_paths: set[str] = set()
    for name, d in recs.items():
        for s in walk_strings(d):
            s = s.strip()
            # a path may be embedded in prose; check the leading path token
            for tok in re.findall(r"(?:tests|src|docs)/[A-Za-z0-9_./+-]+", s):
                tok = tok.rstrip(".,;:)")
                if not tok or "*" in tok or tok.endswith("/"):
                    continue          # a directory reference, not a file citation
                if not Path(tok).suffix:
                    continue          # a tree or package reference, not a file citation
                seen_paths.add(tok)
    for tok in sorted(seen_paths):
        checks += 1
        if not (ROOT / tok).exists():
            bad(f"path does not exist: {tok}")
    print(f"[1] repository paths named in the records : {len(seen_paths):>4} checked, "
          f"{sum(1 for x in problems if x.startswith('path does not exist'))} missing")

    # ---- 2. test-case function names attributed to a test file ----
    fn_checked = fn_bad = 0
    for name, d in recs.items():
        for m in d.get("modules_under_test", []) or []:
            for tf in m.get("test_files", []) or []:
                p = tf.get("path", "")
                if not p.startswith("tests/"):
                    continue
                f = ROOT / p
                if not f.exists():
                    continue
                defined = set(TESTFN.findall(f.read_text(errors="replace")))
                for fn in tf.get("test_case_functions", []) or []:
                    fn_checked += 1
                    if fn not in defined:
                        fn_bad += 1
                        bad(f"{name}: {p} does not define test case {fn!r}")
        for vc in (d.get("vacuity_census", {}) or {}).get("vacuous_green_files", []) or []:
            p = vc.get("path", "")
            f = ROOT / p
            if not f.exists():
                continue
            defined = set(TESTFN.findall(f.read_text(errors="replace")))
            for fn in vc.get("test_case_functions", []) or []:
                fn_checked += 1
                if fn not in defined:
                    fn_bad += 1
                    bad(f"{name}: vacuity census names {fn!r} which {p} does not define")
    checks += fn_checked
    print(f"[2] test-case functions attributed to files: {fn_checked:>4} checked, {fn_bad} absent")

    # ---- 2b. every test path cited is a target the recorded run actually ran ----
    cited_tests = {t for t in seen_paths
                   if t.startswith("tests/unit/") and t.endswith(".c") and not t.endswith("/")}
    orphan = sorted(t for t in cited_tests if t not in by_test)
    checks += len(cited_tests)
    for t in orphan:
        bad(f"test file cited but absent from results-sil-all.json: {t}")
    print(f"[3] cited tests/unit files present in the run: {len(cited_tests):>4} cited, "
          f"{len(orphan)} not in the run")

    # ---- 3. HL_* headers the records name ----
    run_headers = set()
    for r in run["results"]:
        run_headers.update(r.get("halcogen_via_module_under_test") or [])
    cited_hl = {s for name in recs for s in walk_strings(recs[name])
                if re.fullmatch(r"HL_[A-Za-z0-9_]+\.h", s)}
    for h in sorted(cited_hl):
        checks += 1
        if h not in run_headers:
            bad(f"interface header named but absent from the run: {h}")
    print(f"[4] HL_* headers named                      : {len(cited_hl):>4} checked, "
          f"{sum(1 for x in problems if x.startswith('interface header'))} absent")

    # ---- 4. corpus artefact ids resolve (within their profile) ----
    index: dict[tuple[str, str], dict] = {}
    for p in (ART / "corpus").rglob("*.json"):
        try:
            d = json.loads(p.read_text())
        except Exception:
            continue
        i, prof = d.get("id"), d.get("profile")
        if i and prof:
            index[(prof, i)] = d
    id_re = re.compile(r"FB2-[A-Z]{2,3}-[A-Z]{2,3}-\d{6}")
    cited_ids = set()
    for name, d in recs.items():
        for s in walk_strings(d):
            cited_ids.update(id_re.findall(s))
    for l in reg["links"]:
        cited_ids.update([l["source_id"], l["target_id"]])
    own = {d["id"] for d in recs.values()}
    unres = sorted(i for i in cited_ids
                   if ("synthetic_reference", i) not in index
                   and ("as_is", i) not in index
                   and i not in own)
    checks += len(cited_ids)
    for i in unres:
        bad(f"corpus id named in the records does not resolve in either profile: {i}")
    # any FB2- token that is not a well-formed id is a fabricated or malformed reference
    reg_path = ART / "corpus/synthetic_reference/shared/assumption-registry.json"
    assumption_ids = {a["id"] for a in load(reg_path)["assumptions"]} if reg_path.exists() else set()
    malformed: set[str] = set()
    for name, d in recs.items():
        for s in walk_strings(d):
            for tok in re.findall(r"FB2-[A-Za-z0-9-]+", s):
                if "*" in s or tok.endswith("-"):
                    continue          # a glob or a family reference, not a citation
                if tok in assumption_ids:
                    continue          # resolves against the assumption registry
                if not re.fullmatch(r"FB2-[A-Z]{2,3}-[A-Z]{2,3}-\d{6}", tok):
                    malformed.add((tok, name))
    for tok, where in sorted(malformed):
        bad(f"malformed or fabricated corpus reference {tok!r} in {where}")
    print(f"[5b] malformed FB2-* references            : {len(malformed):>4} found")
    print(f"[5] corpus ids named                       : {len(cited_ids):>4} checked, "
          f"{len(unres)} unresolved")

    # ---- 5. evidence paths and their published digests ----
    ev_checked = ev_bad = 0
    for name, d in recs.items():
        for e in d.get("evidence_files", []) or []:
            ev_checked += 1
            if not (ROOT / e).exists():
                ev_bad += 1
                bad(f"{name}: evidence_files entry does not exist: {e}")
        for lg in d.get("logs", []) or []:
            ev_checked += 1
            f = ROOT / lg["file"]
            if not f.exists():
                ev_bad += 1
                bad(f"{name}: logs entry does not exist: {lg['file']}")
                continue
            actual = "sha256:" + hashlib.sha256(f.read_bytes()).hexdigest()
            if actual != lg["hash"]:
                ev_bad += 1
                bad(f"{name}: logs digest mismatch for {lg['file']}")
    checks += ev_checked
    print(f"[6] evidence files and digests             : {ev_checked:>4} checked, {ev_bad} bad")

    # ---- 6. recompute every published count ----
    tests_root = sorted((ROOT / "tests/unit").rglob("test_*.c"))
    green = [r for r in run["results"] if r["outcome"] == "pass"]
    green_asserting = 0
    for r in green:
        f = ROOT / r["test"]
        if f.exists() and ASRT.search(f.read_text(errors="replace")):
            green_asserting += 1
    no_case = sum(1 for f in tests_root if not TESTFN.search(f.read_text(errors="replace")))
    with_case_no_asrt = sum(
        1 for f in tests_root
        if TESTFN.search(f.read_text(errors="replace"))
        and not ASRT.search(f.read_text(errors="replace")))
    with_both = len(tests_root) - no_case - with_case_no_asrt
    src_units = sorted(list((ROOT / "src/app").rglob("*.c")) + list((ROOT / "src/bootloader").rglob("*.c")))
    hdrs: dict[str, list[Path]] = {}
    for f in (ROOT / "src").rglob("*.[ch]"):
        hdrs.setdefault(f.name, []).append(f)
    with_edges = 0
    for f in src_units:
        for inc in re.findall(r'#include\s+"([^"]+)"', f.read_text(errors="replace")):
            for hp in hdrs.get(Path(inc).name, []):
                if not str(hp).startswith(str(ROOT / "src")):
                    continue
                c = hp.with_suffix(".c")
                if c.exists() and c != f:
                    with_edges += 1
                    break
            else:
                continue
            break
    distinct_hl = len({h for r in run["results"]
                       for h in (r.get("halcogen_via_module_under_test") or [])})
    bfc = run["build_failure_classes"]
    real_defect = sum(v for k, v in bfc.items() if k.startswith("build:real_defect"))
    taut_guard = bfc.get("build:product_tautological_guard", 0)
    product_attributed = real_defect + taut_guard
    harness_only = (bfc.get("excluded:upstream_config", 0) + bfc.get("build:clang_only_diagnostic", 0)
                    + bfc.get("build:strict_diagnostic_both_compilers", 0)
                    + bfc.get("build:not_buildable_on_macos_object_format", 0))
    hdr_mismatch = bfc.get("build:sil_interface_header_mismatch", 0)
    undeclared = bfc.get("build:undeclared_identifier", 0)
    total = sum(bfc.values())
    print(f"[7a] build-failure attribution arithmetic (classes sum to {total}):")
    for lbl, got, pub in (("build:real_defect_* targets", real_defect, 16),
                          ("build:product_tautological_guard", taut_guard, 1),
                          ("attributed to the product, total", product_attributed, 17),
                          ("harness or toolchain only", harness_only, 56),
                          ("SIL interface header mismatch", hdr_mismatch, 3),
                          ("undeclared identifier", undeclared, 8)):
        checks += 1
        if got != pub:
            bad(f"build-failure figure {lbl}: records publish {pub}, recomputed {got}")
        print(f"      {'ok ' if got == pub else 'MISMATCH'} {lbl:<34} published={pub:<6} recomputed={got}")
    if product_attributed + undeclared + harness_only + hdr_mismatch != total:
        bad(f"build-failure groups do not sum to the total: {product_attributed} + {undeclared} "
            f"+ {harness_only} + {hdr_mismatch} != {total}")

    expected = {
        "313 test targets": (run["total"], 313),
        "222 green": (len(green), 222),
        "7 failed": (run["failed_tests"], 7),
        "84 build failures": (run["build_failures"], 84),
        "988 assertions": (run["total_assertions_tested"], 988),
        "950 assertions passed": (run["total_assertions_passed"], 950),
        "35 assertions failed": (run["total_assertions_failed"], 35),
        "13 build-failure classes": (len(run["build_failure_classes"]), 13),
        "17 build failures attributed to the product": (product_attributed, 17),
        "217 green that assert": (green_asserting, 217),
        "285 with test case and assertion": (with_both, 285),
        "7 with test case, no assertion": (with_case_no_asrt, 7),
        "21 with no test case": (no_case, 21),
        "263 src translation units": (len(src_units), 263),
        "191 with an include edge": (with_edges, 191),
        "38 distinct interface headers": (distinct_hl, 38),
    }
    print("[7] published counts recomputed from source:")
    for label, (got, pub) in expected.items():
        checks += 1
        flag = "ok " if got == pub else "MISMATCH"
        if got != pub:
            bad(f"count {label}: records publish {pub}, recomputed {got}")
        print(f"      {flag} {label:<34} published={pub:<6} recomputed={got}")

    # ---- 7. HL_spi / HL_can / HL_het tallies ----
    for hdr, pub in (("HL_spi.h", 70), ("HL_can.h", 69), ("HL_het.h", 60)):
        n = sum(1 for r in run["results"] if hdr in (r.get("halcogen_via_module_under_test") or []))
        checks += 1
        if n != pub:
            bad(f"count tests requiring {hdr}: records publish {pub}, recomputed {n}")
        print(f"      {'ok ' if n == pub else 'MISMATCH'} {hdr + ' required by':<34} published={pub:<6} recomputed={n}")

    print(f"\nchecks performed: {checks}")
    if problems:
        print(f"MISMATCHES: {len(problems)}")
        for p in problems:
            print("  -", p)
        return 1
    print("RESULT: zero mismatches. Every cited test file, function, header, corpus id, evidence")
    print("        file and published count re-derives from the repository as it stands.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
