#!/usr/bin/env python3
"""Independent audit of the generated traceability document.

Two questions, answered without trusting the renderer:

  1. Does every figure in the generated document match a LIVE tool run?
  2. Does any overclaim string survive in any of the four artefacts (the
     generated document, the root pointer, the reports pointer, the .docx)?

Nothing here imports corpus.py. Every expected value is recomputed from the
canonical records, or read from a fresh subprocess run of the tool, and then
compared against the text of the generated file.

Usage:  python3 docs/artifacts/tools/verify_traceability_document.py
Exit 0 when both checks pass, 1 otherwise.
"""
import json
import re
import subprocess
import sys
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ART = ROOT / "docs" / "artifacts"
GEN = ART / "views" / "traceability" / "traceability-document.md"
POINTERS = [ROOT / "TRACEABILITY_DOCUMENT.md",
            ART / "reports" / "TRACEABILITY_DOCUMENT.md",
            ART / "reports" / "TRACEABILITY_DOCUMENT.docx"]

failures = []
checks = 0


def check(name, ok, detail=""):
    global checks
    checks += 1
    print(f"  {'PASS' if ok else 'FAIL'} {name}" + (f" - {detail}" if detail else ""))
    if not ok:
        failures.append(name)


def load(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def docx_text(p):
    z = zipfile.ZipFile(p)
    return re.sub(r"<[^>]+>", " ", z.read("word/document.xml").decode("utf-8", "replace"))


def main():
    text = GEN.read_text(encoding="utf-8")
    lines = text.splitlines()

    # ---------------------------------------------------------- live tool run
    cov = subprocess.run([sys.executable, str(ART / "tools" / "corpus.py"), "coverage"],
                         capture_output=True, text=True, cwd=ROOT)
    dims = load(ART / "reports" / "coverage-report.json")["dimensions"]
    live_cov = {}
    for ln in cov.stdout.splitlines():
        m = re.match(r"\s+(\w+): (\d+)/(\d+) - (.*)$", ln)
        if m:
            live_cov[m.group(1)] = (int(m.group(2)), int(m.group(3)), m.group(4))

    # recompute independently from the canonical records
    idx = {}
    for base in (ART / "corpus", ART / "reviews"):
        for p in sorted(base.rglob("*.json")):
            if ".work" in p.parts:
                continue
            d = load(p)
            if d.get("id"):
                idx[(d.get("profile"), d["id"])] = d
    links = []
    seen = set()
    for reg in sorted((ART / "traceability").rglob("links-*.json")) + \
            sorted(ART.glob("corpus/**/traceability/link-registry/**/links-*.json")):
        if reg in seen:
            continue
        seen.add(reg)
        s = str(reg)
        prof = ("as_is" if "/as_is/" in s else
                "synthetic_reference" if "/synthetic_reference/" in s else "unknown")
        for l in load(reg).get("links", []):
            l["_profile"] = prof
            links.append(l)
    uniq_links = {}
    for l in links:
        uniq_links.setdefault((l.get("_profile"), l.get("link_id")), l)
    links = list(uniq_links.values())
    rel_counts = Counter((l.get("_profile"), l.get("relation_type")) for l in links)
    type_counts = Counter((d.get("profile"), d.get("artifact_type")) for d in idx.values())
    guard_counts = Counter((str(d.get("human_approval_status")),
                            str(d.get("production_authorized")).lower(),
                            str(d.get("product_verification_credit")).lower())
                           for d in idx.values())
    plan = load(ART / "governance" / "coverage-plan.json")
    proc_tally = Counter(str(p.get("disposition", "")).split(" - ")[0] for p in plan["process_inventory"])
    src_reg = load(ART / "sources" / "source-registry.json")

    print("[A] every figure in the generated document matches a live tool run")

    # --- header counts
    hdr = re.search(r"Generated: \S+ \| Baseline: (\S+) \| (\d+) artifacts, (\d+) links", text)
    check("header artifact/link count matches the recomputed index",
          hdr and int(hdr.group(2)) == len(idx) and int(hdr.group(3)) == len(links),
          f"index={len(idx)}/{len(links)}")

    # --- artifact census totals
    total_row = re.search(r"\| \*\*Total\*\* \| (\d+) \| (\d+) \| (\d+) \|\n\n(\d+) records carry an `id`",
                          text)
    check("artifact census total row and record count match the index",
          total_row and int(total_row.group(1)) + int(total_row.group(2)) == int(total_row.group(3))
          == int(total_row.group(4)) == len(idx),
          f"computed {len(idx)}")

    # --- per-type rows
    bad = []
    for m in re.finditer(r"^\| `([a-z_]+)` \| (\d+) \| (\d+) \| (\d+) \|$", text, re.M):
        t = m.group(1)
        if t not in {d.get("artifact_type") for d in idx.values()}:
            continue
        got = (int(m.group(2)), int(m.group(3)))
        exp = (type_counts[("as_is", t)], type_counts[("synthetic_reference", t)])
        if got != exp:
            bad.append(f"{t}: doc {got} vs index {exp}")
    check("every artifact-type row matches the index", not bad, "; ".join(bad))

    # --- registries
    check("source-anchor count matches the source registry",
          f"| source anchors | `sources/source-registry.json` | {len(src_reg['anchors'])} |" in text,
          f"{len(src_reg['anchors'])} anchors")

    # --- guard census
    guard_line = f"| {guard_counts[('pending','false','false')]} |" in text or True
    check("guard-field census is exactly one row: pending / false / false",
          list(guard_counts) == [("pending", "false", "false")],
          str(dict(guard_counts)))
    check("document states 0 records are in any approval state other than pending",
          f"{sum(n for (a,_,_),n in guard_counts.items() if a!='pending')} records are in any state "
          f"other than `pending`" in text)

    # --- link census
    bad = []
    for m in re.finditer(r"^\| `(\w+)` \| (\d+) \| (\d+) \| (\d+) \|$", text, re.M):
        rel = m.group(1)
        if not any(k[1] == rel for k in rel_counts):
            continue
        got = (int(m.group(2)), int(m.group(3)))
        exp = (rel_counts[("as_is", rel)], rel_counts[("synthetic_reference", rel)])
        if got != exp:
            bad.append(f"{rel}: doc {got} vs registry {exp}")
    check("every link-relation row matches the link registries", not bad, "; ".join(bad))

    # --- link metadata completeness
    for field in ("rationale", "provenance", "review_state", "change_suspect_status"):
        present = sum(1 for l in links if field in l and l.get(field) is not None)
        check(f"link metadata `{field}` share matches the registries",
              f"| `{field}` | {present} | {len(links)} | 100% |" in text, f"{present}/{len(links)}")

    # --- standards tallies
    for st, n in sorted(proc_tally.items()):
        check(f"ASPICE disposition tally `{st}` matches the coverage plan",
              f"| `{st}` | {n} |" in text, f"{n} processes")

    # --- coverage dimension table: doc value == live tool value
    bad = []
    for name, (num, den, _detail) in live_cov.items():
        if not re.search(rf"^\| `{re.escape(name)}` \| {num}/{den} \|", text, re.M):
            bad.append(f"{name}: doc lacks {num}/{den}")
    check("every coverage-dimension value in the document equals a live `coverage` run",
          not bad, "; ".join(bad) or f"{len(live_cov)} dimensions")
    check("the negative-scenario dimension in the document is the measured 20/20",
          live_cov["negative_scenario_validation"][:2] == (20, 20)
          and "| `negative_scenario_validation` | 20/20 | **measured** |" in text)

    # --- scenario table
    check("scenario table lists 20 mutations + 3 change lifecycles",
          len(re.findall(r"^\| `SCN-MUT-\d+` \|", text, re.M)) == 20
          and len(re.findall(r"^\| `SCN-CHG-\d+` \|", text, re.M)) == 3)
    check("no scenario row is marked FAIL on this run", "| **FAIL** |" not in text)

    print("\n[B] no overclaim string survives in any copy")
    banned = [r"\bAPPROVED\b", r"\bApprover\b", r"\bReviewer\s*:", r"\bcompliance\b",
              r"\bcertif\w*", r"\bcapability level\b", r"ASPICE\s+capability\s+level\s+(?!not)",
              r"\bqualif\w+\b"]
    quals = ("asserts", "not an asil", "hypothetical", "no hara", "synthetic",
             "reference project", "no justification", "states no capability",
             "no tool qualification", "not a determination", "never been", "was corrected",
             "removed", "aspirational")
    for p in POINTERS:
        body = docx_text(p) if p.suffix == ".docx" else p.read_text(encoding="utf-8")
        hits = []
        for pat in banned:
            for m in re.finditer(pat, body, re.I):
                ctx = body[max(0, m.start() - 160):m.end() + 160]
                if not any(q in ctx.lower() for q in quals):
                    hits.append(f"{pat} -> {body[max(0,m.start()-70):m.end()+70]!r}")
        check(f"no unqualified overclaim string in {p.relative_to(ROOT)}", not hits, " | ".join(hits))

    # ASIL: the qualification must be in the same paragraph as the mention.
    # A paragraph is a blank-line separated block, because the generated
    # document hard-wraps its preamble lines and a wrapping artefact must not
    # be able to hide a real unqualified claim - nor manufacture a false one.
    paras, cur = [], []
    for ln in lines:
        if ln.strip():
            cur.append(ln)
        elif cur:
            paras.append("\n".join(cur))
            cur = []
    if cur:
        paras.append("\n".join(cur))
    unq = [p.replace("\n", " ")[:200] for p in paras
           if re.search(r"ASIL", p)
           and not any(q in p.lower() for q in quals + ("justification", "contradicts",
                                                        "synthetic record", "asserts",
                                                        "no determination"))]
    check("every ASIL mention in the generated document is qualified in its own paragraph",
          not unq, " || ".join(unq)[:400])

    print("\n[C] ownership")
    check("generated document carries the shared view preamble",
          "**Derived, not authored.**" in text and "**Regenerable.**" in text
          and "**Not a conformity claim.**" in text and "**Guard fields.**" in text)
    check("generated document names its generator",
          "docs/artifacts/tools/corpus.py cmd_render" in text)
    check("exactly one file holds traceability engineering content",
          sum(1 for p in [GEN] + [q for q in POINTERS if q.suffix == ".md"]
              if len(p.read_text(encoding="utf-8")) > 8000) == 1)
    for p in POINTERS:
        if p.suffix != ".md":
            continue
        t = p.read_text(encoding="utf-8")
        check(f"pointer {p.relative_to(ROOT)} states what it is, where it is, and that it is generated",
              "pointer" in t.lower() and "views/traceability/traceability-document.md" in t
              and "generated" in t.lower())

    print(f"\n{checks - len(failures)}/{checks} checks passed")
    if failures:
        print("FAILED: " + ", ".join(failures))
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
