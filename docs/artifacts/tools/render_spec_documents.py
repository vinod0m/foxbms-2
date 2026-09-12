#!/usr/bin/env python3
"""
render_spec_documents.py — Generate ten standalone per-discipline specification
documents (Markdown + Mermaid, optional .docx via pandoc) from the foxBMS 2
lifecycle artifact corpus.

Usage:
  python3 docs/artifacts/tools/render_spec_documents.py            # generate all
  python3 docs/artifacts/tools/render_spec_documents.py --check    # integrity check
  python3 docs/artifacts/tools/render_spec_documents.py --out-dir DIR

Deterministic: sorted iteration everywhere; only the "Generated:" line may vary.
Read-only over the corpus; all writes go to the output directory.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from corpus import load_json  # noqa: E402

REPO = Path(__file__).resolve().parent.parent.parent.parent  # tools/ -> artifacts/ -> docs/ -> repo root
ARTIFACTS = REPO / "docs" / "artifacts"
OUT_DEFAULT = ARTIFACTS / "spec-documents"

PROFILES = ("as_is", "synthetic_reference")
GEN_STAMP = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# ---------------------------------------------------------------- doc registry

DOC_ORDER = [
    "01-stakeholder-requirements-specification",
    "02-system-requirements-specification",
    "03-system-architecture-specification",
    "04-software-requirements-specification",
    "05-software-architecture-specification",
    "06-detailed-design-specification",
    "07-software-integration-report",
    "08-system-verification-report",
    "09-software-verification-report",
    "10-implementation-mapping-document",
]

DOC_TITLES = {
    "01-stakeholder-requirements-specification": "Stakeholder Requirements Specification",
    "02-system-requirements-specification": "System Requirements Specification",
    "03-system-architecture-specification": "System Architecture Specification",
    "04-software-requirements-specification": "Software Requirements Specification",
    "05-software-architecture-specification": "Software Architecture Specification",
    "06-detailed-design-specification": "Detailed Design Specification",
    "07-software-integration-report": "Software Integration Report",
    "08-system-verification-report": "System Verification Report",
    "09-software-verification-report": "Software Verification Report",
    "10-implementation-mapping-document": "Implementation Mapping Document",
}

# Document ownership: doc stem -> (artifact_type test, id substring test or None)
def _owns(doc, d):
    at = d.get("artifact_type", "")
    aid = d.get("id", "")
    if doc == "02-system-requirements-specification":
        return at in ("safety_goal",) or (at == "requirement" and "-FSR-" in aid)
    if doc == "04-software-requirements-specification":
        return at == "requirement" and ("-SWR-" in aid or "-MAN-" in aid)
    if doc == "05-software-architecture-specification":
        return at == "design" and d.get("engineering_domain") == "software"
    if doc == "06-detailed-design-specification":
        return at == "design" and d.get("engineering_domain") == "software"
    return False

OWNERSHIP = {doc: _owns for doc in DOC_ORDER}

REQUIRED_HEADINGS = {
    "01-stakeholder-requirements-specification": ["Item Definition", "Stakeholder Needs", "Operational"],
    "02-system-requirements-specification": ["Safety Goals", "Functional Safety Requirements"],
    "03-system-architecture-specification": ["Context Viewpoint", "Functional Block Viewpoint", "Dynamic Viewpoint"],
    "04-software-requirements-specification": ["Software Requirements"],
    "05-software-architecture-specification": ["Static Component Viewpoint", "Dynamic Viewpoint"],
    "06-detailed-design-specification": ["Detailed Design"],
    "07-software-integration-report": ["Integrated Components", "Integration Evidence", "Integration Gaps"],
    "08-system-verification-report": ["Test Specification", "Execution Report"],
    "09-software-verification-report": ["Unit Testing", "Component Testing", "Integration Testing", "HIL Testing"],
    "10-implementation-mapping-document": ["Implementation Mapping", "Requirement-to-Test Coverage Matrix"],
}


class Views:
    """Shared in-memory views over the corpus (single source of truth)."""

    def __init__(self):
        self.artifacts = {}      # (profile, id) -> dict
        for f in sorted((ARTIFACTS / "corpus").rglob("*.json")):
            if ".work" in f.parts:
                continue
            try:
                d = load_json(f)
            except Exception:
                continue
            if isinstance(d, dict) and d.get("id"):
                self.artifacts[(d.get("profile", "unknown"), d["id"])] = d
        for f in sorted((ARTIFACTS / "reviews").rglob("*.json")):
            try:
                d = load_json(f)
            except Exception:
                continue
            if isinstance(d, dict) and d.get("id"):
                self.artifacts[(d.get("profile", "as_is"), d["id"])] = d
        self.links = self._load_links()
        self.scope = load_json(ARTIFACTS / "governance" / "scope-and-applicability.json")
        self.params = load_json(ARTIFACTS / "shared" / "parameter-registry.json").get("parameters", [])
        self.asms = load_json(ARTIFACTS / "shared" / "assumption-registry.json").get("assumptions", [])
        self.src_reg = load_json(ARTIFACTS / "sources" / "source-registry.json").get("anchors", [])
        self.by_relation = {}
        for l in self.links:
            self.by_relation.setdefault(l.get("relation_type", "?"), []).append(l)

    def _load_links(self):
        links = []
        seen = set()
        registries = sorted((ARTIFACTS / "traceability" / "link-registry").rglob("links-*.json"))
        registries += sorted((ARTIFACTS / "corpus").rglob("traceability/**/links-*.json"))
        for p in registries:
            if p in seen:
                continue
            seen.add(p)
            s = str(p)
            if "link-registry/as_is" in s or "/corpus/as_is/traceability/" in s:
                profile = "as_is"
            elif "link-registry/synthetic_reference" in s or "/corpus/synthetic_reference/traceability/" in s:
                profile = "synthetic_reference"
            else:
                profile = "unknown"
            d = load_json(p)
            for l in d.get("links", []):
                l = dict(l)
                l["_profile"] = profile
                links.append(l)
        by_key = {}
        for l in links:
            by_key.setdefault((l.get("_profile"), l.get("link_id")), l)
        return list(by_key.values())
        self.by_relation = {}                    # relation -> [link]
        for l in self.links:
            self.by_relation.setdefault(l.get("relation_type", "?"), []).append(l)
        self.scope = load_json(ARTIFACTS / "governance" / "scope-and-applicability.json")
        self.params = load_json(ARTIFACTS / "shared" / "parameter-registry.json").get("parameters", [])
        self.asms = load_json(ARTIFACTS / "shared" / "assumption-registry.json").get("assumptions", [])
        self.src_reg = load_json(ARTIFACTS / "sources" / "source-registry.json").get("anchors", [])

    # ---- accessors -------------------------------------------------------
    def get(self, profile, aid):
        return self.artifacts.get((profile, aid), self.artifacts.get(("unknown", aid), {}))

    def of_profile(self, profile, pred):
        return sorted(
            (aid for (p, aid), d in self.artifacts.items() if p == profile and pred(d)),
        ) if False else sorted(
            aid for (p, aid), d in self.artifacts.items() if p == profile and pred(d)
        )

    def links_where(self, profile=None, relation=None, src=None, tgt=None):
        out = []
        for l in self.links:
            if profile is not None and l.get("_profile", l.get("profile")) != profile:
                continue
            if relation is not None and l.get("relation_type") != relation:
                continue
            if src is not None and l.get("source_id") != src:
                continue
            if tgt is not None and l.get("target_id") != tgt:
                continue
            out.append(l)
        return out

    # ---- coverage --------------------------------------------------------
    def coverage(self, profile, req_id):
        """Return dict(status, direct, indirect, embedded, tests)."""
        direct = sorted({l["source_id"] for l in self.links_where(profile=profile, relation="verifies", tgt=req_id)}
                        | {l["source_id"] for l in self.links_where(profile=profile, relation="validates", tgt=req_id)})
        indirect = {}
        for child in sorted({l["source_id"] for l in self.links_where(profile=profile, relation="allocated_to", tgt=req_id)}):
            cdirect = sorted({l["source_id"] for l in self.links_where(profile=profile, relation="verifies", tgt=child)}
                             | {l["source_id"] for l in self.links_where(profile=profile, relation="validates", tgt=child)})
            if cdirect:
                indirect[child] = cdirect
        embedded = []
        for (p, j), t in sorted(self.artifacts.items()):
            if p == profile and t.get("artifact_type") == "test_measure":
                if req_id in (t.get("referenced_requirements") or []):
                    embedded.append(j)
        if direct:
            status = "COVERED-DIRECT"
        elif indirect:
            status = "COVERED-INDIRECT"
        elif embedded:
            status = "COVERED-EMBEDDED"
        else:
            status = "UNCOVERED"
        return {"status": status, "direct": direct, "indirect": indirect,
                "embedded": embedded, "tests": sorted(set(direct) | {t for v in indirect.values() for t in v} | set(embedded))}

    def all_requirements(self):
        """[(profile, id)] sorted — every requirement artifact incl. management."""
        out = []
        for (p, aid), d in sorted(self.artifacts.items()):
            if p in PROFILES and d.get("artifact_type") == "requirement":
                out.append((p, aid))
        return out

    # ---- helpers ---------------------------------------------------------
    def anchor_str(self, anchor_id):
        for a in self.src_reg:
            if a.get("anchor_id") == anchor_id:
                loc = a.get("location", {})
                if a.get("source_type") == "code":
                    return f"`{loc.get('path','?')}` :: `{loc.get('symbol','?')}()` (L{loc.get('line_range','?')})"
                if a.get("source_type") == "hardware":
                    return f"HW: `{str(loc.get('file','?'))[:50]}` ({loc.get('reference_designator','?')})"
                if a.get("source_type") == "test":
                    return f"TST: `{str(loc.get('file', loc.get('path','?')))[:50]}`"
                return f"DOC: `{str(loc.get('url_or_path', loc.get('path','?')))[:50]}`"
        return anchor_id

    def asm_stmt(self, asm_id):
        for a in self.asms:
            if a.get("assumption_id", a.get("id")) == asm_id:
                return a.get("statement", "")[:100]
        return ""


def esc(s, n=200):
    s = str(s) if s is not None else "N/A"
    s = s.replace("|", "\\|").replace("\n", " ")
    return s[:n] + ("..." if len(s) > n else "")


def mermaid(kind, body):
    return f"```mermaid\n{kind}\n{body}\n```\n"


# ---------------------------------------------------------------- scaffolding

def scaffold(views, stem, scope_line):
    t = DOC_TITLES[stem]
    L = []
    L.append(f"# foxBMS 2 — {t}")
    L.append("")
    L.append("**Document Control**")
    L.append("")
    L.append("| Field | Value |")
    L.append("|---|---|")
    L.append("| Project | foxBMS 2 — Battery Management System |")
    L.append(f"| Document | {t} |")
    L.append("| Baseline | BAS-REF-001 (commit `308028fb`, tag `v1.11.0`) |")
    L.append("| Profiles | `as_is` (source-grounded) + `synthetic_reference` (hypothetical) |")
    L.append("| Corpus status | `synthetic_ready_with_limitations` |")
    L.append("| Generated | " + GEN_STAMP + " |")
    L.append("")
    L.append("## Scope")
    L.append("")
    L.append(scope_line)
    L.append("")
    return L


def finish(L):
    L.append("")
    L.append("---")
    L.append("")
    L.append(f"*Generated: {GEN_STAMP} — auto-generated from the machine-verifiable corpus. "
             f"Regenerate with `python3 docs/artifacts/tools/render_spec_documents.py`.*")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- 01 StakeRS

def emit_01(v, out):
    L = scaffold(v, "01-stakeholder-requirements-specification",
                 "Stakeholder requirements for the foxBMS 2 reference BMS item: item definition, "
                 "boundaries, operational situation, modes, external systems, and stakeholder needs. "
                 "Derived from `FB2-SRC-DOC` governance artifacts; premises traced by artifact ID.")
    sc = v.scope
    L.append("## Item Definition")
    L.append("")
    item = sc.get("item_definition", {})
    if isinstance(item, dict):
        L.append(f"**Item**: {esc(item.get('name','foxBMS 2 reference BMS'), 300)}")
        L.append("")
        L.append(esc(item.get("description", sc.get("description", "N/A")), 800))
    else:
        L.append(esc(item if item else sc.get("description", "N/A"), 800))
    L.append("")
    L.append("## System Boundaries")
    L.append("")
    b = sc.get("boundaries", {})
    included, excluded = (b.get("included", []), b.get("excluded", [])) if isinstance(b, dict) else ([], [])
    L.append("**Included in item scope**:")
    L.append("")
    for x in included or sc.get("included", []):
        L.append(f"- {esc(x)}")
    L.append("")
    L.append("**Excluded from item scope (external)**:")
    L.append("")
    for x in excluded or sc.get("excluded", []):
        L.append(f"- {esc(x)}")
    L.append("")
    L.append("## Operational Situation")
    L.append("")
    L.append(esc(sc.get("operational_situation", sc.get("operational_situations", "N/A")), 600))
    L.append("")
    ops = sc.get("operational_situations", [])
    if isinstance(ops, list) and ops:
        for o in ops:
            L.append(f"- {esc(o)}")
        L.append("")
    L.append("## Modes")
    L.append("")
    for m in sc.get("modes", []) or ["N/A — not specified in corpus"]:
        L.append(f"- {esc(m)}")
    L.append("")
    L.append("## External Systems")
    L.append("")
    for e in sc.get("external_systems", []) or ["N/A — not specified in corpus"]:
        L.append(f"- {esc(e)}")
    L.append("")
    L.append("## Stakeholder Needs")
    L.append("")
    needs = sc.get("stakeholder_needs", [])
    if needs:
        L.append("| Need | Description | Traces to |")
        L.append("|---|---|---|")
        for nd in needs:
            if isinstance(nd, dict):
                L.append(f"| {esc(nd.get('id', nd.get('need','?')))} | {esc(nd.get('description', nd.get('need','')),300)} | {esc(', '.join(nd.get('traces_to', [])))} |")
            else:
                L.append(f"| NEED | {esc(nd, 300)} | — |")
    else:
        L.append("Stakeholder needs not enumerated in corpus scope artifact; premises trace to "
                 "`FB2-SAF-HAZ-000001` (hazard premises) and `FB2-SAF-SGO-000001` (safety objective).")
    L.append("")
    L.append("## Use-Case Context")
    L.append("")
    L.append("The reference use case is a stationary battery storage: three power contactors "
             "(main plus, main minus, precharge) connect/disconnect the battery; on error the "
             "contactors open and isolate the battery (source: corpus use-case premise, "
             "`FB2-SAF-SGO-000001` safe state).")
    L.append("")
    L.append("**Caption**: System context — BMS item with external actors and boundary.")
    L.append("")
    L.append(mermaid("flowchart LR",
        "    subgraph Item[BMS Item - foxBMS 2]\n"
        "        BMS[BMS Master + Slaves]\n"
        "    end\n"
        "    CELL[Battery Cells / Pack] --- BMS\n"
        "    CHG[Charger / Inverter] --- BMS\n"
        "    VEH[Vehicle / Load] --- BMS\n"
        "    OPER[Operator / HMI] --- BMS"))
    L.append("**Premise traceability**: hazard premises `FB2-SAF-HAZ-000001`; safety objective "
             "`FB2-SAF-SGO-000001`; item scope artifact `governance/scope-and-applicability.json`.")
    L.append("")
    (out / "01-stakeholder-requirements-specification.md").write_text(finish(L))


# ---------------------------------------------------------------- 02 SysRS

def emit_02(v, out):
    L = scaffold(v, "02-system-requirements-specification",
                 "System-level requirements: safety goals and functional safety requirements (FSRs) "
                 "of both profiles with full attribute sets.")
    for profile in PROFILES:
        L.append(f"## Profile: `{profile}`")
        L.append("")
        # Safety goals
        sgo_ids = v.of_profile(profile, lambda d: d.get("artifact_type") == "safety_goal")
        L.append("### Safety Goals")
        L.append("")
        for sid in sgo_ids:
            d = v.get(profile, sid)
            L.append(f"#### `{sid}` — {esc(d.get('title',''))}")
            L.append("")
            L.append(f"- **Statement**: {esc(d.get('statement','N/A'), 400)}")
            L.append(f"- **Rationale**: {esc(d.get('rationale','Hazard mitigation for FB2-SAF-HAZ-000001'), 400)}")
            L.append(f"- **ASIL**: `{d.get('asil','?')}`")
            tb = d.get("timing_budget", {})
            L.append(f"- **FTTI (total)**: {tb.get('total_ftti_ms','?')} ms")
            alloc = tb.get("allocation", {})
            if alloc:
                L.append(f"- **Timing budget allocation**: " + ", ".join(f"`{k}`={ms}ms" for k, ms in sorted(alloc.items())))
            L.append(f"- **Safe state**: {esc(d.get('safe_state','?'))}")
            L.append(f"- **Degraded state**: {esc(d.get('degraded_state','?'))}")
            L.append(f"- **Source references**: " + (", ".join(f"`{r}`" for r in d.get("source_refs", [])) or "—"))
            L.append(f"- **Assumption references**: " + (", ".join(f"`{r}`" for r in d.get("assumption_refs", [])) or "—"))
            L.append("")
        # FSRs
        fsr_ids = v.of_profile(profile, lambda d: d.get("artifact_type") == "requirement" and "-FSR-" in d.get("id",""))
        L.append("### Functional Safety Requirements")
        L.append("")
        for fid in fsr_ids:
            d = v.get(profile, fid)
            sa = d.get("safety_allocation", {}) or {}
            ac = d.get("acceptance_criteria", [])
            L.append(f"#### `{fid}` — {esc(d.get('title',''))}")
            L.append("")
            L.append(f"- **Statement**: {esc(d.get('statement','N/A'), 500)}")
            L.append(f"- **Rationale**: {esc(d.get('rationale','Refines safety goal timing and functional budget'), 400)}")
            L.append(f"- **ASIL**: `{sa.get('asil', d.get('asil','?'))}`")
            L.append(f"- **Safety goal reference**: `{sa.get('safety_goal_ref','FB2-SAF-SGO-000001')}`")
            if ac:
                L.append("- **Acceptance criteria**:")
                for c in ac:
                    if isinstance(c, dict):
                        L.append(f"  - {esc(c.get('criterion','?'))}: {esc(c.get('measure',''))} ≤ {esc(c.get('threshold',''))} {esc(c.get('unit',''))}")
                    else:
                        L.append(f"  - {esc(c)}")
            else:
                L.append("- **Acceptance criteria**: not specified in corpus")
            cm = d.get("conditions_modes", [])
            L.append(f"- **Conditions/modes**: " + (", ".join(f"`{m}`" for m in cm) if cm else "not specified in corpus"))
            L.append(f"- **Source references**: " + (", ".join(f"`{r}`" for r in d.get("source_refs", [])) or "—"))
            L.append(f"- **Assumption references**: " + (", ".join(f"`{r}` ({esc(v.asm_stmt(r),60)})" for r in d.get("assumption_refs", [])) or "—"))
            L.append("")
    (out / "02-system-requirements-specification.md").write_text(finish(L))


# ---------------------------------------------------------------- 03 SysArch

def emit_03(v, out):
    L = scaffold(v, "03-system-architecture-specification",
                 "System architecture viewpoints — context, functional block, dynamic — derived from the "
                 "scope artifact and the per-profile link registries. One caption per diagram for text readers.")
    for profile in PROFILES:
        L.append(f"## Profile: `{profile}`")
        L.append("")
        ext = v.scope.get("external_systems", []) or ["Charger", "Vehicle", "Cells"]
        L.append("### Context Viewpoint")
        L.append("")
        L.append("**Caption**: BMS item boundary with external actors (from scope artifact).")
        L.append("")
        ext_nodes = "\n".join(f"    E{i}[\"{esc(e, 30)}\"]" for i, e in enumerate(ext[:8]))
        ext_links = "\n".join(f"    E{i} <--> BMS" for i in range(min(len(ext), 8)))
        L.append(mermaid("flowchart LR", f"    BMS[foxBMS 2 BMS Item]\n{ext_nodes}\n{ext_links}"))
        L.append("### Functional Block Viewpoint")
        L.append("")
        L.append("**Caption**: Cell-voltage protection chain blocks from the link registry "
                 "(HAZ ← mitigates ← SGO ← refines ← FSRs ← allocated_to ← TSR/SWR).")
        L.append("")
        body = ["    HAZ[\"FB2-SAF-HAZ-000001 Hazard\"]", "    SGO[\"FB2-SAF-SGO-000001 Safety Goal\"]",
                "    HAZ --- SGO"]
        for l in sorted(v.links_where(profile=profile, relation="refines"), key=lambda x: x["source_id"]):
            body.append(f"    \"{l['source_id']}\" --- \"{l['target_id']}\"")
        for l in sorted(v.links_where(profile=profile, relation="allocated_to"), key=lambda x: x["source_id"]):
            body.append(f"    \"{l['source_id']}\" -.allocated_to.-> \"{l['target_id']}\"")
        for l in sorted(v.links_where(profile=profile, relation="implements"), key=lambda x: x["source_id"]):
            body.append(f"    \"{l['source_id']}\" -.implements.-> \"{l['target_id']}\"")
        L.append(mermaid("flowchart TD", "\n".join(body)))
        L.append("### Dynamic Viewpoint")
        L.append("")
        L.append("**Caption**: Sequence of the cell-voltage protection chain (hazard detection to "
                 "contactor opening) per link registry relations.")
        L.append("")
        seq = ["    participant AFE as AFE Driver", "    participant DB as Database",
               "    participant SOA as SOA Monitor", "    participant DIAG as DIAG/SYS",
               "    participant CONT as Contactor"]
        seq.append("    AFE->>DB: publish validated cell voltages (25 ms)")
        seq.append("    DB->>SOA: read min/max cell voltages")
        seq.append("    SOA->>SOA: debounce (2 counts / 100 ms)")
        seq.append("    SOA->>DIAG: FAULT request on confirmed violation (5 ms)")
        seq.append("    DIAG->>CONT: open contactors (command 5 ms)")
        seq.append("    CONT->>CONT: mechanical opening (30 ms)")
        seq.append("    Note over CONT: safe state within FTTI 100 ms")
        L.append(mermaid("sequenceDiagram", "\n".join(seq)))
        L.append("Relations derived from: "
                 + ", ".join(f"`{l['link_id']}`" for l in sorted(v.links_where(profile=profile), key=lambda x: x.get('link_id',''))[:6])
                 + " … (full registry in traceability document).")
        L.append("")
    (out / "03-system-architecture-specification.md").write_text(finish(L))


# ---------------------------------------------------------------- 04 SWRS

def emit_04(v, out):
    L = scaffold(v, "04-software-requirements-specification",
                 "Software requirements (SWRs and software-facing requirements) of both profiles, "
                 "grouped under their parent FSR with the allocation rationale quoted.")
    for profile in PROFILES:
        L.append(f"## Profile: `{profile}`")
        L.append("")
        fsr_ids = v.of_profile(profile, lambda d: d.get("artifact_type") == "requirement" and "-FSR-" in d.get("id",""))
        for fid in fsr_ids:
            alloc = sorted(v.links_where(profile=profile, relation="allocated_to", tgt=fid), key=lambda x: x["source_id"])
            if not alloc:
                continue
            L.append(f"### Parent FSR: `{fid}`")
            L.append("")
            for l in alloc:
                swr_id = l["source_id"]
                d = v.get(profile, swr_id)
                if not d:
                    continue
                L.append(f"#### `{swr_id}` — {esc(d.get('title',''))}")
                L.append("")
                L.append(f"- **Allocated to**: `{fid}` (link `{l['link_id']}`, rationale: \"{esc(l.get('rationale',''))}\")")
                L.append(f"- **Statement**: {esc(d.get('statement','N/A'), 500)}")
                L.append(f"- **Rationale**: {esc(d.get('rationale','Implements parent FSR in software'), 400)}")
                L.append(f"- **Classification**: `{d.get('classification','?')}`")
                sa = d.get("safety_allocation", {}) or {}
                L.append(f"- **ASIL**: `{sa.get('asil','?')}`")
                ac = d.get("acceptance_criteria", [])
                if ac:
                    L.append("- **Acceptance criteria**:")
                    for c in ac:
                        if isinstance(c, dict):
                            L.append(f"  - {esc(c.get('criterion','?'))}: {esc(c.get('measure',''))} ≤ {esc(c.get('threshold',''))} {esc(c.get('unit',''))}")
                        else:
                            L.append(f"  - {esc(c)}")
                else:
                    L.append("- **Acceptance criteria**: not specified in corpus")
                L.append(f"- **Source references**: " + (", ".join(f"`{r}`" for r in d.get("source_refs", [])) or "—"))
                L.append(f"- **Assumption references**: " + (", ".join(f"`{r}`" for r in d.get("assumption_refs", [])) or "—"))
                L.append("")
        # orphan SWRs (allocated to no FSR in this profile)
        grouped = {l["source_id"] for fid in fsr_ids for l in v.links_where(profile=profile, relation="allocated_to", tgt=fid)}
        orphans = [aid for aid in v.of_profile(profile, lambda d: d.get("artifact_type") == "requirement" and ("-SWR-" in d.get("id","") or "-MAN-" in d.get("id","")))
                   if aid not in grouped]
        if orphans:
            L.append("### Software Requirements Without Parent FSR Link")
            L.append("")
            for oid in orphans:
                d = v.get(profile, oid)
                L.append(f"#### `{oid}` — {esc(d.get('title',''))}")
                L.append("")
                L.append(f"- **Statement**: {esc(d.get('statement','N/A'), 500)}")
                L.append(f"- **Classification**: `{d.get('classification','?')}` | **Profile**: `{profile}`")
                L.append(f"- **Note**: no `allocated_to` link to a parent FSR in this profile's registry.")
                L.append("")
    (out / "04-software-requirements-specification.md").write_text(finish(L))


# ---------------------------------------------------------------- 05 SWArch

def emit_05(v, out):
    L = scaffold(v, "05-software-architecture-specification",
                 "Software architecture viewpoints: static component viewpoint (SWR/DSN relations), "
                 "dynamic state-machine viewpoints per design artifact, and a task/thread timing "
                 "context — all data-derived.")
    for profile in PROFILES:
        L.append(f"## Profile: `{profile}`")
        L.append("")
        L.append("### Static Component Viewpoint")
        L.append("")
        L.append("**Caption**: SW requirements, designs, and implements/allocated_to relations.")
        L.append("")
        body = []
        for l in sorted(v.links_where(profile=profile, relation="allocated_to"), key=lambda x: x["source_id"]):
            if l["source_id"].startswith("FB2-SW"):
                body.append(f"    \"{l['source_id']}\" --> \"{l['target_id']}\"")
        for l in sorted(v.links_where(profile=profile, relation="implements"), key=lambda x: x["source_id"]):
            body.append(f"    \"{l['source_id']}\" -.implements.-> \"{l['target_id']}\"")
        if body:
            L.append(mermaid("flowchart TD", "\n".join(body)))
        else:
            L.append("No SW allocation/implements links in this profile's registry.")
        L.append("")
        # Dynamic per design
        dsn_ids = v.of_profile(profile, lambda d: d.get("artifact_type") == "design" and d.get("engineering_domain") == "software")
        for did in dsn_ids:
            d = v.get(profile, did)
            bm = d.get("behavior_model", {})
            L.append(f"### Dynamic Viewpoint — `{did}`")
            L.append("")
            if isinstance(bm, dict) and bm.get("states"):
                L.append(f"**Caption**: State machine of `{did}` from `behavior_model` "
                         f"({esc(bm.get('type','state_machine'))}).")
                L.append("")
                sb = ["    [*] --> " + (bm.get("states")[0] if bm.get("states") else "INIT")]
                for t in bm.get("transitions", []):
                    if isinstance(t, dict):
                        sb.append(f"    {t.get('from','?')} --> {t.get('to','?')} : {esc(t.get('trigger',''), 30)}")
                for s in bm.get("states", []):
                    sb.append(f"    {s}")
                L.append(mermaid("stateDiagram-v2", "\n".join(sb)))
            else:
                L.append("Behavior model not specified in corpus.")
            L.append("")
        # task/thread context from timing budget
        sgo = v.get(profile, "FB2-SAF-SGO-000001")
        tb = (sgo or {}).get("timing_budget", {}).get("allocation", {})
        if tb:
            L.append("### Task/Thread Timing Context")
            L.append("")
            L.append("**Caption**: Timing budget elements (from `FB2-SAF-SGO-000001`) as scheduling context.")
            L.append("")
            body = ["    CHAIN[\"Protection chain\"]"]
            for k, ms in sorted(tb.items()):
                body.append(f"    T_{k}[\"{k}<br/>{ms} ms\"]")
                body.append(f"    T_{k} --> CHAIN")
            L.append(mermaid("flowchart LR", "\n".join(body)))
            L.append("")
    (out / "05-software-architecture-specification.md").write_text(finish(L))


# ---------------------------------------------------------------- 06 Detailed Design

def emit_06(v, out):
    L = scaffold(v, "06-detailed-design-specification",
                 "Detailed design per software component: responsibilities, decomposition, interfaces, "
                 "constraints, budgets, failure response, static and dynamic diagrams, and implementation "
                 "requirements extracted from design fields.")
    for profile in PROFILES:
        dsn_ids = v.of_profile(profile, lambda d: d.get("artifact_type") == "design" and d.get("engineering_domain") == "software")
        for did in dsn_ids:
            d = v.get(profile, did)
            L.append(f"## Detailed Design: `{did}` ({profile})")
            L.append("")
            L.append(f"**Title**: {esc(d.get('title',''))} | **Level**: `{d.get('design_level','?')}`")
            L.append("")
            resp = d.get("responsibilities", [])
            L.append("### Responsibilities")
            L.append("")
            for r in resp or ["not specified in corpus"]:
                L.append(f"- {esc(r, 250)}")
            L.append("")
            dec = d.get("decomposition", [])
            L.append("### Decomposition")
            L.append("")
            if dec:
                L.append("**Caption**: Component decomposition of `" + did + "`.")
                L.append("")
                body = [f"    D[\"{did}\"]"]
                for i, c in enumerate(dec):
                    name = c.get("component", c.get("name", f"C{i}")) if isinstance(c, dict) else str(c)
                    body.append(f"    C{i}[\"{esc(name, 40)}\"]")
                    body.append(f"    D --> C{i}")
                L.append(mermaid("flowchart TD", "\n".join(body)))
            else:
                L.append("Decomposition not specified in corpus.")
            L.append("")
            ifs = d.get("interfaces", [])
            L.append("### Interfaces")
            L.append("")
            if isinstance(ifs, list) and ifs:
                L.append("| Interface | Direction | Signals |")
                L.append("|---|---|---|")
                for i in ifs:
                    if isinstance(i, dict):
                        sigs = i.get("signals", [])
                        sig_str = ", ".join(
                            (f"`{s.get('name','?')}` ({s.get('type','?')}, {s.get('unit','?')}, {s.get('range','?')}, {s.get('rate','?')})"
                             if isinstance(s, dict) else str(s)) for s in sigs)
                        L.append(f"| `{i.get('interface_id','?')}` | {i.get('direction','?')} | {esc(sig_str, 300)} |")
            else:
                L.append("Interfaces not specified in corpus.")
            L.append("")
            cons = d.get("constraints", [])
            L.append("### Constraints")
            L.append("")
            for c in cons or ["not specified in corpus"]:
                L.append(f"- {esc(c, 250)}")
            L.append("")
            bud = d.get("budgets", {})
            L.append("### Budgets")
            L.append("")
            if bud:
                for k, val in sorted(bud.items()):
                    L.append(f"- **{k}**: {esc(val)}")
            else:
                L.append("Budgets not specified in corpus.")
            L.append("")
            fr = d.get("failure_response", [])
            L.append("### Failure Response")
            L.append("")
            if isinstance(fr, list) and fr:
                L.append("| Failure mode | Detection | Reaction |")
                L.append("|---|---|---|")
                for f in fr:
                    if isinstance(f, dict):
                        L.append(f"| {esc(f.get('failure_mode','?'))} | {esc(f.get('detection','?'), 150)} | {esc(f.get('reaction','?'), 150)} |")
            else:
                L.append("Failure response not specified in corpus.")
            L.append("")
            bm = d.get("behavior_model", {})
            L.append("### Dynamic Diagram")
            L.append("")
            if isinstance(bm, dict) and bm.get("states"):
                L.append(f"**Caption**: State machine of `{did}`.")
                L.append("")
                sb = ["    [*] --> " + bm["states"][0]]
                for t in bm.get("transitions", []):
                    if isinstance(t, dict):
                        sb.append(f"    {t.get('from','?')} --> {t.get('to','?')} : {esc(t.get('trigger',''), 30)}")
                for s in bm.get("states", []):
                    sb.append(f"    {s}")
                L.append(mermaid("stateDiagram-v2", "\n".join(sb)))
            else:
                L.append("Behavior model not specified in corpus.")
            L.append("")
            im = d.get("implementation_mapping", [])
            L.append("### Implementation Requirements (extracted)")
            L.append("")
            if cons or bud:
                L.append(f"Extracted from `{did}` design fields:")
                L.append("")
                for c in cons:
                    L.append(f"- {esc(c, 200)} (source: `{did}` constraints)")
                for k, val in sorted(bud.items()):
                    L.append(f"- Budget `{k}` = {esc(val)} (source: `{did}` budgets)")
            else:
                L.append("No additional implementation requirements beyond mapping (see Implementation Mapping Document).")
            L.append("")
    (out / "06-detailed-design-specification.md").write_text(finish(L))


# ---------------------------------------------------------------- 07 SW Integration

def emit_07(v, out):
    L = scaffold(v, "07-software-integration-report",
                 "Integrated software components, available integration evidence, and explicit "
                 "integration gaps. Per governance policy, evidence is blocked, not fabricated.")
    for profile in PROFILES:
        L.append(f"## Profile: `{profile}`")
        L.append("")
        L.append("### Integrated Components")
        L.append("")
        impl = sorted(v.links_where(profile=profile, relation="implements"), key=lambda x: x["source_id"])
        if impl:
            L.append("| Design | Implements SWR | Link rationale |")
            L.append("|---|---|---|")
            for l in impl:
                L.append(f"| `{l['source_id']}` | `{l['target_id']}` | {esc(l.get('rationale',''))} |")
        else:
            L.append("No `implements` links in this profile's registry.")
        L.append("")
        L.append("### Integration Evidence")
        L.append("")
        exes = v.of_profile(profile, lambda d: d.get("artifact_type") == "execution")
        if exes:
            for eid in exes:
                d = v.get(profile, eid)
                L.append(f"- `{eid}`: kind=`{d.get('execution_kind','?')}`, outcome=`{d.get('outcome','?')}`")
        else:
            L.append("No execution artifacts in this profile. Integration-level executions: **none in corpus**.")
        L.append("")
        L.append("### Integration Gaps")
        L.append("")
        exes_as_is = v.of_profile("as_is", lambda d: d.get("artifact_type") == "execution")
        component_present = any(v.get(p, a).get("test_type") == "component"
                                for p in PROFILES for a in v.of_profile(p, lambda d: d.get("artifact_type") == "test_measure"))
        L.append("| Gap | Disposition |")
        L.append("|---|---|")
        if not component_present:
            L.append("| No component-level test measures | Gap documented; synthetic_reference to add per review disposition FB2-FND-000005 |")
        L.append("| No integration-level executions (only unit `actual_host_run` exists) | Per governance policy: actual product evidence = 0 — blocked, not fabricated |")
        L.append("| No target-hardware integration runs | as_is gap documented in review `FB2-REV-000001` (finding FB2-FND-000002) |")
        L.append("")
    (out / "07-software-integration-report.md").write_text(finish(L))


# ---------------------------------------------------------------- 08 System Verif

def _render_tms(v, L, profile, tms_id, depth="####"):
    d = v.get(profile, tms_id)
    if not d:
        return
    L.append(f"{depth} `{tms_id}` — {esc(d.get('title',''))} ({profile})")
    L.append("")
    L.append(f"- **Test type**: `{d.get('test_type','?')}` | **Oracle basis**: `{d.get('oracle_basis','?')}`")
    L.append(f"- **Objective**: {esc(d.get('objective','N/A'), 300)}")
    pre = d.get("preconditions", [])
    if pre:
        L.append(f"- **Preconditions**: " + ", ".join(esc(p, 100) for p in pre))
    env = d.get("environment", {})
    if isinstance(env, dict):
        L.append(f"- **Environment**: {esc(env.get('hardware','?'))}; {esc(env.get('software','?'))}; config `{env.get('configuration','?')}`")
    steps = d.get("steps", [])
    if steps:
        L.append("- **Test cases (steps)**:")
        for s in steps:
            if isinstance(s, dict):
                L.append(f"  {s.get('step','?')}. **{esc(s.get('action',''), 150)}** → expected: {esc(s.get('expected',''), 150)}")
    eo = d.get("expected_outcomes", [])
    if eo:
        L.append("- **Expected outcomes**:")
        for e in eo:
            if isinstance(e, dict):
                L.append(f"  - `{e.get('signal','?')}` = {esc(e.get('expected_value','?'))} (tolerance {esc(e.get('tolerance','?'))})")
    L.append("")


def _render_exe(v, L, profile, exe_id):
    d = v.get(profile, exe_id)
    if not d:
        return
    L.append(f"##### Execution `{exe_id}` — {esc(d.get('title',''))}")
    L.append("")
    L.append(f"- **Test measure**: `{d.get('test_measure_id','?')}` | **Execution kind**: `{d.get('execution_kind','?')}` | **Outcome**: **{str(d.get('outcome','?')).upper()}**")
    env = d.get("environment", {})
    if isinstance(env, dict):
        tv = env.get("tool_versions", {})
        tools = ", ".join(f"{k} {vv}" for k, vv in sorted(tv.items())) if tv else ", ".join(env.get("tools", []))
        L.append(f"- **Environment**: {esc(env.get('hardware','?'))}; {esc(env.get('software','?'))}; tools: {esc(tools, 150)}")
    L.append(f"- **Evidence refs**: " + (", ".join(f"`{r}`" for r in d.get("evidence_refs", [])) or "—"))
    L.append("")


def emit_08(v, out):
    L = scaffold(v, "08-system-verification-report",
                 "System-level verification: test specification, test cases, and execution reports "
                 "from TMS/EXE artifacts, with outcome, execution_kind, environment, evidence refs.")
    L.append("## Test Specification")
    L.append("")
    any_tms = False
    for profile in PROFILES:
        for tms_id in v.of_profile(profile, lambda d: d.get("artifact_type") == "test_measure"):
            any_tms = True
            _render_tms(v, L, profile, tms_id)
    if not any_tms:
        L.append("No test measure artifacts in the corpus for either profile — **system-level test "
                 "specification gap** (blocked, not fabricated, per governance policy).")
        L.append("")
    L.append("## Test Cases")
    L.append("")
    n_cases = 0
    for profile in PROFILES:
        for tms_id in v.of_profile(profile, lambda d: d.get("artifact_type") == "test_measure"):
            d = v.get(profile, tms_id)
            n = len(d.get("steps", [])) or 1
            n_cases += n
            L.append(f"- `{tms_id}` ({profile}): {n} test case(s)")
    if n_cases == 0:
        L.append("No test cases in corpus.")
    else:
        L.append("")
        L.append(f"**Total system-level test cases**: {n_cases}")
    L.append("")
    L.append("## Execution Report")
    L.append("")
    any_exe = False
    for profile in PROFILES:
        for exe_id in v.of_profile(profile, lambda d: d.get("artifact_type") == "execution"):
            any_exe = True
            _render_exe(v, L, profile, exe_id)
    if not any_exe:
        L.append("No execution artifacts in the corpus — **execution report gap** (blocked, not fabricated).")
    L.append("")
    (out / "08-system-verification-report.md").write_text(finish(L))


# ---------------------------------------------------------------- 09 SW Verif

def emit_09(v, out):
    L = scaffold(v, "09-software-verification-report",
                 "Software verification by level — unit, component, integration, HIL — each with test "
                 "specification, cases, execution report; execution_kind labeled; actual vs synthetic distinguished.")
    LEVELS = [("Unit Testing", "unit"), ("Component Testing", "component"),
              ("Integration Testing", "integration"), ("HIL Testing", "hil")]
    all_tms = []
    for profile in PROFILES:
        for tms_id in v.of_profile(profile, lambda d: d.get("artifact_type") == "test_measure"):
            all_tms.append((profile, tms_id))
    all_exe = []
    for profile in PROFILES:
        for exe_id in v.of_profile(profile, lambda d: d.get("artifact_type") == "execution"):
            all_exe.append((profile, exe_id))
    # classify executions by kind
    def exes_of_kind(kinds):
        out = []
        for profile, eid in all_exe:
            ek = v.get(profile, eid).get("execution_kind", "")
            if kinds == "hil" and ("hil" in ek or "simulation" in ek):
                out.append((profile, eid))
            elif kinds == ek:
                out.append((profile, eid))
        return out

    for title, key in LEVELS:
        L.append(f"## {title}")
        L.append("")
        if key == "unit":
            tm = [(p, t) for p, t in all_tms if v.get(p, t).get("test_type") == "unit"]
        else:
            tm = [(p, t) for p, t in all_tms if v.get(p, t).get("test_type") == key]
        if key == "unit":
            ex = [(p, e) for p, e in all_exe if v.get(p, e).get("execution_kind") in ("actual_host_run", "synthetic_fixture")]
        elif key == "component":
            ex = [(p, e) for p, e in all_exe if "component" in str(v.get(p, e).get("test_measure_id", ""))]
        elif key == "integration":
            ex = exes_of_kind("integration")
        else:
            ex = exes_of_kind("hil")
        L.append("### Test Specification")
        L.append("")
        if tm:
            for p, t in tm:
                _render_tms(v, L, p, t, depth="####")
        else:
            L.append(f"No `{key}` test specification artifacts in the corpus — **gap** (blocked, not fabricated).")
            L.append("")
        L.append("### Test Cases")
        L.append("")
        n = 0
        for p, t in tm:
            d = v.get(p, t)
            c = len(d.get("steps", [])) or 1
            n += c
            L.append(f"- `{t}` ({p}): {c} test case(s)")
        L.append(f"**Subtotal test cases**: {n}")
        L.append("")
        L.append("### Execution Report")
        L.append("")
        if ex:
            for p, e in ex:
                _render_exe(v, L, p, e)
        else:
            note = ("No target-HIL executions exist in the corpus — per governance policy, "
                    "actual product evidence = 0 (blocked, not fabricated)." if key == "hil"
                    else f"No `{key}` execution artifacts in the corpus — gap (blocked, not fabricated).")
            L.append(note)
            L.append("")
    (out / "09-software-verification-report.md").write_text(finish(L))


# ---------------------------------------------------------------- 10 Impl Mapping

def emit_10(v, out):
    L = scaffold(v, "10-implementation-mapping-document",
                 "Implementation mapping (design → source) and the complete requirement-to-test "
                 "coverage matrix for every requirement artifact in both profiles.")
    L.append("## Implementation Mapping")
    L.append("")
    for profile in PROFILES:
        dsn_ids = v.of_profile(profile, lambda d: d.get("artifact_type") == "design" and d.get("engineering_domain") == "software")
        for did in dsn_ids:
            d = v.get(profile, did)
            im = d.get("implementation_mapping", [])
            L.append(f"### `{did}` ({profile}) — {esc(d.get('title',''), 80)}")
            L.append("")
            if isinstance(im, list) and im:
                L.append("| Source file | Symbol | Status |")
                L.append("|---|---|---|")
                for m in im:
                    if isinstance(m, dict):
                        L.append(f"| `{m.get('source_file','?')}` | `{m.get('symbol','?')}` | `{m.get('status','?')}` |")
            else:
                L.append("Implementation mapping not specified in corpus.")
            L.append("")
    # SWR chains
    L.append("### Requirement → Design → Source → Test Chains")
    L.append("")
    for profile in PROFILES:
        for swr in v.of_profile(profile, lambda d: d.get("artifact_type") == "requirement" and "-SWR-" in d.get("id","")):
            L.append(f"#### `{swr}` ({profile})")
            L.append("")
            designs = sorted({l["source_id"] for l in v.links_where(profile=profile, relation="implements", tgt=swr)})
            for dsn in designs:
                dd = v.get(profile, dsn)
                srcs = sorted({m.get("source_file","?") for m in dd.get("implementation_mapping", []) if isinstance(m, dict)})
                L.append(f"- Design `{dsn}` implements `{swr}` → sources: " + (", ".join(f"`{s}`" for s in srcs) or "—"))
            tms = sorted({l["source_id"] for l in v.links_where(profile=profile, relation="verifies", tgt=swr)})
            embedded = []
            for (p, j), t in sorted(v.artifacts.items()):
                if p == profile and t.get("artifact_type") == "test_measure" and swr in (t.get("referenced_requirements") or []):
                    embedded.append(j)
            all_tests = sorted(set(tms) | set(embedded))
            L.append(f"- Verifying test measures: " + (", ".join(f"`{t}`" for t in all_tests) or "**UNCOVERED — no test**"))
            L.append("")
    # Coverage matrix
    L.append("## Requirement-to-Test Coverage Matrix")
    L.append("")
    L.append("One row per requirement artifact across FSR/TSR/SWR/management classes, both profiles. "
             "Statuses: COVERED-DIRECT (has `verifies` link), COVERED-INDIRECT (allocated child is verified), "
             "COVERED-EMBEDDED (TMS references requirement), UNCOVERED (explicit gap).")
    L.append("")
    L.append("| Profile | Requirement | Type | Status | Direct verifies | Indirect (child ← test) | Verifying tests | Gap note |")
    L.append("|---|---|---|---|---|---|---|---|")
    uncovered = []
    for profile, rid in v.all_requirements():
        d = v.artifacts[(profile, rid)]
        cov = v.coverage(profile, rid)
        rtype = ("FSR" if "-FSR-" in rid else "TSR" if "-TSR-" in rid
                 else "SWR" if "-SWR-" in rid else "MGT")
        direct = ", ".join(f"`{x}`" for x in cov["direct"]) or "—"
        indirect = ", ".join(f"`{c}`←{','.join(t)}" for c, t in sorted(cov["indirect"].items())) or "—"
        tests = ", ".join(f"`{x}`" for x in cov["tests"]) or "—"
        if cov["status"] == "UNCOVERED":
            note = "No direct, indirect, or embedded test coverage in corpus"
            uncovered.append((profile, rid))
        else:
            note = ""
        L.append(f"| `{profile}` | `{rid}` | {rtype} | **{cov['status']}** | {direct} | {indirect} | {tests} | {note} |")
    L.append("")
    L.append("### Coverage Summary")
    L.append("")
    total = len(v.all_requirements())
    n_unc = len(uncovered)
    n_cov = total - n_unc
    L.append(f"- **Total requirement artifacts**: {total}")
    L.append(f"- **Covered (any status)**: {n_cov} ({n_cov*100//max(total,1)}%)")
    L.append(f"- **UNCOVERED**: {n_unc}")
    for p, r in uncovered:
        L.append(f"  - `{r}` (`{p}`)")
    L.append("")
    L.append("UNCOVERED requirements are the honest corpus state; the gaps are tracked by review "
             "dispositions in `FB2-REV-000001` and the gap report. No coverage is fabricated.")
    L.append("")
    (out / "10-implementation-mapping-document.md").write_text(finish(L))


# ---------------------------------------------------------------- pandoc

def to_docx(md_path, out_dir):
    pandoc = shutil.which("pandoc")
    if not pandoc:
        return False
    stem = md_path.stem
    docx = out_dir / (stem + ".docx")
    title = DOC_TITLES.get(stem, stem)
    r = subprocess.run(
        [pandoc, str(md_path), "-o", str(docx), "--toc", "--toc-depth=3",
         "-M", f"title=foxBMS 2 — {title}", "-M", "author=foxBMS 2 Lifecycle Artifact Corpus",
         "-M", "date=" + GEN_STAMP[:10]],
        capture_output=True, text=True)
    return r.returncode == 0


# ---------------------------------------------------------------- integrity check

def check(out):
    ok = True
    v = Views()
    failures = []
    # (a) all ten docs exist with required headings
    for stem in DOC_ORDER:
        p = out / (stem + ".md")
        if not p.exists():
            failures.append(f"MISSING document: {stem}.md")
            ok = False
            continue
        text = p.read_text()
        for h in REQUIRED_HEADINGS.get(stem, []):
            if h not in text:
                failures.append(f"{stem}.md: missing heading '{h}'")
                ok = False
    # (b) owned artifact IDs present per document
    for stem in DOC_ORDER:
        p = out / (stem + ".md")
        if not p.exists():
            continue
        text = p.read_text()
        pred = OWNERSHIP[stem]
        for (prof, aid), d in sorted(v.artifacts.items()):
            if prof in PROFILES and pred(stem, d):
                if aid not in text:
                    failures.append(f"{stem}.md: owned artifact `{aid}` not present")
                    ok = False
    # (c) coverage matrix has a row per requirement artifact
    mp = out / "10-implementation-mapping-document.md"
    if mp.exists():
        text = mp.read_text()
        for profile, rid in v.all_requirements():
            if rid not in text:
                failures.append(f"coverage matrix: missing row for `{rid}` (`{profile}`)")
                ok = False
    if failures:
        print("INTEGRITY CHECK FAILED:")
        for f in failures[:40]:
            print("  -", f)
        if len(failures) > 40:
            print(f"  ... and {len(failures)-40} more")
    else:
        print("INTEGRITY CHECK PASSED: all documents complete, all owned IDs present, coverage matrix complete.")
    return ok


def determinism(out):
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        generate(tdp)
        same = True
        for stem in DOC_ORDER:
            a = strip_stamp(out / (stem + ".md"))
            b = strip_stamp(tdp / (stem + ".md"))
            if a != b:
                print(f"DETERMINISM FAIL: {stem}.md differs between runs")
                same = False
        print("DETERMINISM: " + ("byte-identical across runs" if same else "MISMATCH"))
        return same


def strip_stamp(p):
    txt = p.read_text()
    txt = re.sub(r"Generated: [0-9T:Z-]+", "Generated: <stamp>", txt)
    txt = re.sub(r"\| Generated \| [0-9T:Z-]+ \|", "| Generated | <stamp> |", txt)
    return txt


# ---------------------------------------------------------------- main

def generate(out):
    out.mkdir(parents=True, exist_ok=True)
    v = Views()
    emit_01(v, out)
    emit_02(v, out)
    emit_03(v, out)
    emit_04(v, out)
    emit_05(v, out)
    emit_06(v, out)
    emit_07(v, out)
    emit_08(v, out)
    emit_09(v, out)
    emit_10(v, out)
    # docx
    pandoc = shutil.which("pandoc")
    if not pandoc:
        print("NOTE: pandoc not found — Word conversion skipped.")
    else:
        n = 0
        for stem in DOC_ORDER:
            if to_docx(out / (stem + ".md"), out):
                n += 1
        print(f"Word conversion: {n}/10 documents converted.")
    print(f"Generated 10 Markdown documents in {out}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="run integrity check on generated documents")
    ap.add_argument("--out-dir", default=str(OUT_DEFAULT))
    args = ap.parse_args()
    out = Path(args.out_dir)
    if args.check:
        ok = check(out)
        ok &= determinism(out)
        sys.exit(0 if ok else 1)
    generate(out)


if __name__ == "__main__":
    main()
