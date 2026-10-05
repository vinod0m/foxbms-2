#!/usr/bin/env python3
"""
render_e2e_html.py — generate the single-file end-to-end HTML engineering
document for the foxBMS 2 lifecycle artifact corpus.

The output is `docs/artifacts/reports/e2e-engineering-document.html`: one
self-contained file that presents every engineering process level, from the
item definition and stakeholder needs down to verification evidence, with
per-record guard fields, data-derived Mermaid diagrams, and the complete
traceability matrix.

Content sources (all canonical corpus JSON, loaded through corpus.py so the
document can never disagree with the validator's view of the corpus):

  1. the artifact index (both profiles, every artifact type)
  2. both per-profile link registries
  3. the shared parameter and assumption registries
  4. the source anchor registry
  5. governance/scope-and-applicability.json (item boundaries, external
     systems, modes, applicability decisions)

What this file is NOT:

  * not a hand-authored document. Every table, card and diagram below is
    generated from the records above. No fact is introduced that is not
    derivable from them.
  * not a conformity claim. It asserts no ISO 26262 conformity, no ASIL
    capability level, no Automotive SPICE assessment, and no human approval.
    ASIL values appear only as values recorded in corpus records, and the
    `synthetic_reference` profile is a fictional project.
  * not a claim of diagram validation. Mermaid blocks are emitted as source
    and rendered client-side; the syntax check is a separate, explicitly
    invoked post-generation step (`--validate-mermaid`) whose real result is
    reported to the operator and never embedded here, because embedding it
    would make the file non-deterministic and non-offline.

Usage:
  python3 docs/artifacts/tools/render_e2e_html.py                  # generate
  python3 docs/artifacts/tools/render_e2e_html.py --check          # integrity + determinism
  python3 docs/artifacts/tools/render_e2e_html.py --audit-guard    # guard-field / conformity audit
  python3 docs/artifacts/tools/render_e2e_html.py --validate-mermaid
  python3 docs/artifacts/tools/render_e2e_html.py --out PATH

Deterministic: every collection is iterated in sorted order, embedded data is
serialised with sort_keys=True, and the template is fixed. The single
run-varying field is the `data-generated-at` attribute in <head>, which
`strip_stamp()` normalises before the byte comparison.

Read-only over the corpus. The only write is the output file.
"""

import argparse
import html as html_mod
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from corpus import CorpusTool, Findings, load_json  # noqa: E402

REPO = Path(__file__).resolve().parent.parent.parent.parent
ARTIFACTS = REPO / "docs" / "artifacts"
OUT_DEFAULT = ARTIFACTS / "reports" / "e2e-engineering-document.html"

PROFILES = ("as_is", "synthetic_reference")

# The exact wording required wherever the corpus holds no model, value or
# evidence for something the engineering process expects. It is never
# replaced with a plausible substitute and it is never left implicit.
GAP_PHRASE = "not specified in corpus"

# corpus.py records these rules when a corpus input cannot be read at all.
FATAL_LOAD_RULES = ("json_unparseable",)

# Test types that this document places at system verification. The corpus
# test_type vocabulary is: unit, component, integration, hil, fault_injection,
# robustness, validation, qualification, system. `component` and `hil` occur in
# no record, which is a declared gap rather than an empty section. The mapping
# below is stated in the rendered document so a reader never has to guess.
SYSTEM_TEST_TYPES = ("system", "validation", "qualification")
SOFTWARE_TEST_TYPES = ("unit", "component", "integration", "hil",
                       "fault_injection", "robustness")
HIL_LIKE_EXECUTION_KINDS = ("hil", "target_hardware_run", "simulation")

# Link relations that express a coverage/traceability relationship between a
# test and what it covers, as opposed to review bookkeeping.
COVERAGE_RELATIONS = ("verifies", "validates")

# ---------------------------------------------------------------- sections

# (section id, heading text) in engineering order. --check requires every one
# of these anchors and headings to be present.
SECTIONS = [
    ("sec-00-about", "0. What this document is, and what it is not"),
    ("sec-01-stakeholder", "1. Item Definition and Stakeholder Requirements"),
    ("sec-02-system-requirements", "2. System Requirements and Safety Concept"),
    ("sec-03-system-architecture", "3. System Architecture"),
    ("sec-04-software-requirements", "4. Software Requirements"),
    ("sec-05-software-architecture", "5. Software Architecture"),
    ("sec-06-detailed-design", "6. Detailed Design"),
    ("sec-07-implementation-mapping", "7. Implementation Mapping"),
    ("sec-08-software-integration", "8. Software Integration Report"),
    ("sec-09-system-verification", "9. System Verification"),
    ("sec-10-software-verification", "10. Software Verification"),
    ("sec-11-traceability", "11. Traceability Matrix"),
    ("sec-12-gaps", "12. Declared Gaps"),
    ("sec-13-diagram-validation", "13. Diagram Validation"),
    ("sec-14-guard-audit", "14. Guard-Field Audit"),
    ("sec-15-appendix", "15. Appendix: Registries, Plans and Supporting Records"),
]

# Headings that must appear inside a given section. --check requires each.
REQUIRED_SUBHEADINGS = {
    "sec-01-stakeholder": ["Governance Scope and Applicability",
                           "Item Definition", "Stakeholder Needs", "Use Cases"],
    "sec-02-system-requirements": ["Hazards", "Safety Goals", "Safety Concept",
                                   "Threat Analysis and Risk Assessment",
                                   "Safety Analyses", "Safety Case",
                                   "System and Technical Requirements"],
    "sec-03-system-architecture": ["Context Viewpoint", "Functional Block Viewpoint",
                                   "Dynamic Viewpoint", "Viewpoint Derivation"],
    "sec-05-software-architecture": ["Static Component Viewpoint", "Dynamic Viewpoint",
                                     "Architecture Decisions"],
    "sec-06-detailed-design": ["Responsibilities", "Decomposition", "Interfaces",
                               "Constraints", "Budgets", "Failure Response",
                               "Static Diagram", "Dynamic Diagram"],
    "sec-07-implementation-mapping": ["Implementation Mapping",
                                       "Requirement to Design to Source to Test Chains",
                                       "Change Records"],
    "sec-08-software-integration": ["Integrated Components", "Integration Evidence",
                                     "Integration Gaps"],
    "sec-09-system-verification": ["Test Specification", "Test Cases", "Execution Report"],
    "sec-10-software-verification": ["Unit Testing", "Component Testing",
                                     "Integration Testing", "HIL Testing",
                                     "Fault Injection and Robustness Testing",
                                     "Static-Analysis Deviance Evidence"],
    "sec-11-traceability": ["Link Registry", "Requirement Coverage Matrix",
                            "Review Coverage", "Findings", "Scenario Fixtures"],
    "sec-12-gaps": ["Gap Registry"],
    "sec-13-diagram-validation": ["Diagram Inventory", "How validation is performed"],
    "sec-14-guard-audit": ["Guard-Field Census", "Declarations"],
    "sec-15-appendix": ["Parameter Registry", "Assumption Registry", "Source Registry",
                        "Management and Supporting Records", "Corpus Census",
                        "Regeneration and Integrity"],
}

# ---------------------------------------------------------------- escaping


def esc(value, limit=None):
    """HTML-escape a corpus value for element content."""
    if value is None:
        return ""
    if isinstance(value, bool):
        s = "true" if value else "false"
    elif isinstance(value, (dict, list)):
        s = json.dumps(value, sort_keys=True, ensure_ascii=False)
    else:
        s = str(value)
    s = " ".join(s.split())
    if limit is not None and len(s) > limit:
        s = s[:limit].rstrip() + "…"
    return html_mod.escape(s, quote=True)


def esc_mm(value, limit=None):
    """Escape Mermaid source for a <pre> block, preserving its line structure.

    Mermaid source is line-oriented: every statement must stay on its own line.
    esc() deliberately collapses whitespace for prose, so it cannot be used
    here; this escapes only the three characters that would otherwise become
    markup (&, <, >) and leaves newlines, leading indentation and quotes
    intact, so the block stays both valid HTML and valid Mermaid.
    """
    s = str(value)
    if limit is not None and len(s) > limit:
        s = s[:limit].rstrip() + "…"
    return html_mod.escape(s, quote=False)


def mlabel(value, limit=60):
    """A Mermaid-safe quoted label: one line, no embedded double quotes.

    No HTML escaping happens here. The finished diagram body is escaped once by
    esc_mm(), so escaping a label and then escaping the body would double-encode
    the markup characters; only the Mermaid-level rules (one line, no double
    quotes inside a quoted label) are applied at this stage.
    """
    s = " ".join(str(value if value is not None else "").split()).replace('"', "'")
    if len(s) > limit:
        s = s[:limit].rstrip() + "…"
    return '"' + s + '"'


def mid(value):
    """A Mermaid-safe node identifier."""
    s = re.sub(r"[^A-Za-z0-9_]", "_", str(value))
    if not s or not (s[0].isalpha() or s[0] == "_"):
        s = "n_" + s
    return s


# Characters that terminate or open a Mermaid construct when they appear inside
# an edge label, a transition label or a sequence message. They are removed from
# label text rather than escaped, because Mermaid has no escape for them and a
# label that silently renders as broken markup is worse than one that reads
# slightly flatter.
_MM_STRIP = "\"'`;:()[]{}<>|#\\"


def mv(value, limit=40):
    """A Mermaid-safe edge or transition label.

    Parentheses in particular break the flowchart edge grammar
    (`A -->|label (x)| B` is a parse error), and semicolons and colons terminate
    statements, so they are dropped here rather than at the call sites.
    """
    s = " ".join(str(value if value is not None else "").split())
    s = "".join(ch for ch in s if ch not in _MM_STRIP)
    s = " ".join(s.split())
    if len(s) > limit:
        s = s[:limit].rstrip() + "…"
    return s or "relation"


def mseq(value, limit=80):
    """A Mermaid-safe sequence-diagram message or note body.

    In a sequence diagram the text after the first colon is free text, but an
    arrow token inside it is still parsed as an arrow, so `State -> PRECHARGE`
    in a recorded expected result breaks the parse. Arrows are therefore spelled
    out and the remaining statement terminators are dropped.
    """
    s = " ".join(str(value if value is not None else "").split())
    for token, word in (("->>", " to "), ("-->", " to "), ("->", " to "),
                        ("<-", " from "), ("<--", " from "), ("<->", " to and from "),
                        (">>", " "), ("&gt;", " to "), ("&lt;", " from ")):
        s = s.replace(token, word)
    s = "".join(ch for ch in s if ch not in "\"'`;#<>")
    s = " ".join(s.split())
    if len(s) > limit:
        s = s[:limit].rstrip() + "…"
    return s or "step"


# ---------------------------------------------------------------- guard fields

GUARD_FIELDS = ("profile", "origin", "human_approval_status", "production_authorized")


def guard_tuple(d):
    """The four guard fields of a record, plus the verification-credit flag."""
    return {
        "profile": d.get("profile", "unknown"),
        "origin": d.get("origin", "not specified in corpus"),
        "human_approval_status": d.get("human_approval_status", "not specified in corpus"),
        "production_authorized": ("true" if d.get("production_authorized") is True else "false"),
        "product_verification_credit": ("true" if d.get("product_verification_credit") is True
                                        else "false"),
    }


GUARD_ATTR_FIELDS = GUARD_FIELDS + ("product_verification_credit",)


def guard_attr(g):
    return esc("; ".join(f"{k}={g[k]}" for k in GUARD_ATTR_FIELDS), 400)


def guard_html(g):
    """The visible guard line. Its text repeats every value in data-guard so a
    reader who cannot see attributes still sees the fields, and so the audit
    can verify the rendered text against the corpus values."""
    inner = " · ".join(f"{k} <code>{esc(g[k])}</code>" for k in GUARD_FIELDS)
    inner += f" · product_verification_credit <code>{esc(g['product_verification_credit'])}</code>"
    return (f'<p class="guard" data-guard="{guard_attr(g)}">{inner}</p>')


# ---------------------------------------------------------------- views

class CorpusView:
    """Read-only views over the corpus, built on corpus.py's own loaders.

    `load_artifact_index` and `load_links` are the validator's loaders, used
    unmodified, so this document and `corpus.py check` cannot disagree about
    what records and links exist. `load_json` is the shared JSON reader.
    """

    def __init__(self, root=None):
        self.root = Path(root) if root else REPO
        self.artifacts_dir = self.root / "docs" / "artifacts"
        self.findings = Findings()
        self.load_errors = []
        self.tool = CorpusTool(root=self.root)

        # (profile, artifact_id) -> (path, dict)
        self.index = self.tool.load_artifact_index()
        # list of link dicts, each tagged with _profile by the loader
        self.links = self.tool.load_links()

        # The loader records these when a corpus input cannot be read. A
        # generator that cannot read the corpus cannot honestly render it, so
        # these are fatal; the identity-duplicate rule the same loader raises
        # is a property of the corpus, not a load failure, and is rendered as a
        # declared gap instead.
        for f in self.tool.findings.items:
            if f.get("rule") in FATAL_LOAD_RULES:
                self.load_errors.append(f"{f['rule']}: {f['artifact_id']}: {f['description']}")

        self.scope = self._must_load(self.artifacts_dir / "governance" / "scope-and-applicability.json")
        params = self._must_load(self.artifacts_dir / "shared" / "parameter-registry.json")
        asms = self._must_load(self.artifacts_dir / "shared" / "assumption-registry.json")
        srcs = self._must_load(self.artifacts_dir / "sources" / "source-registry.json")
        self.params = params.get("parameters", []) if isinstance(params, dict) else []
        self.assumptions = asms.get("assumptions", []) if isinstance(asms, dict) else []
        self.source_anchors = srcs.get("anchors", []) if isinstance(srcs, dict) else []

        self._param_by_id = {p.get("id"): p for p in self.params if p.get("id")}
        self._asm_by_id = {a.get("id"): a for a in self.assumptions if a.get("id")}
        self._src_by_id = {a.get("anchor_id"): a for a in self.source_anchors if a.get("anchor_id")}

        # Side effects accumulated while rendering. The gap registry and the
        # diagram inventory are built from these, and --check compares the
        # rendered file against them, so a dropped gap or a dropped phrase is
        # a check failure rather than a silent omission.
        self.gaps = []
        self.gap_phrase_sites = 0
        self.diagrams = []
        self.rendered_artifact_ids = set()

    def _must_load(self, path):
        if not path.exists():
            self.load_errors.append(f"missing required corpus input: {path}")
            return {}
        try:
            return load_json(path)
        except Exception as e:  # noqa: BLE001 - any parse failure is fatal here
            self.load_errors.append(f"unparseable corpus input {path}: {e}")
            return {}

    # ---- gap registry ---------------------------------------------------

    def gap(self, kind, subject, statement, consulted):
        """Record a named, explicit gap. Every gap in the document originates
        here, so the registry in section 12 cannot disagree with the body."""
        self.gaps.append({
            "gap_id": f"GAP-{len(self.gaps) + 1:04d}",
            "kind": kind,
            "subject": subject,
            "statement": statement,
            "consulted": consulted,
        })

    def gap_phrase(self, what):
        """Render an absent model with the mandated phrasing, and count the site
        so --check can prove the phrasing was not dropped."""
        self.gap_phrase_sites += 1
        return f'<span class="gap-phrase">{GAP_PHRASE}</span>'

    # ---- artifact access ------------------------------------------------

    def get(self, profile, aid):
        entry = self.index.get((profile, aid))
        return entry[1] if entry else None

    def path_of(self, profile, aid):
        entry = self.index.get((profile, aid))
        return entry[0] if entry else None

    def ids_where(self, profile, pred):
        return sorted(aid for (p, aid), (_path, d) in self.index.items()
                      if p == profile and pred(d))

    def records(self, pred, profiles=PROFILES):
        """[(profile, id, dict)] sorted, for any predicate over the record."""
        return sorted(
            (p, aid, d) for (p, aid), (_path, d) in self.index.items()
            if p in profiles and pred(d)
        )

    def count_where(self, pred):
        return sum(1 for (_p, _a, d) in self.records(pred))

    # ---- anchors --------------------------------------------------------

    def anchor(self, profile, aid):
        return f"art-{profile}-{aid}"

    def anchor_exists(self, profile, aid):
        return (profile, aid) in self.index

    def home_profile(self, aid):
        """Which profile an unqualified id reference resolves to.

        The same identifier in both profiles is two different records by corpus
        design, so a bare id cannot be a single anchor. The rule is fixed and
        stated in the document: a bare reference resolves to the as_is record
        when one exists, otherwise to the synthetic_reference record, and the
        reader is told when both exist.
        """
        for p in PROFILES:
            if self.anchor_exists(p, aid):
                return p
        return None

    def href(self, aid):
        p = self.home_profile(aid)
        if p is None:
            return f'<code>{esc(aid)}</code>'
        return f'<a href="#{self.anchor(p, aid)}"><code>{esc(aid)}</code></a>'

    def aref(self, profile, aid, label=None):
        if not self.anchor_exists(profile, aid):
            return f'<code>{esc(aid)}</code>'
        return (f'<a href="#{self.anchor(profile, aid)}" title="profile: {esc(profile)}">'
                f'<code>{esc(label or aid)}</code></a>')

    def ref_list(self, profile, ids, what="cross-references"):
        """Hyperlinked references, or the mandated gap phrasing when the record
        names none. An em dash here would silently omit an absent model, which
        the corpus's own rules forbid."""
        if not ids:
            return [self.gap_phrase(what)]
        out = []
        for i in ids:
            if self.anchor_exists(profile, i):
                out.append(self.aref(profile, i))
            else:
                out.append(f'<code>{esc(i)}</code>')
        return out

    def id_list(self, ids):
        return [esc(i) for i in sorted(ids)] if ids else ["—"]

    def joined(self, items, sep=", "):
        items = [i for i in items if i]
        return sep.join(items) if items else "—"

    # ---- source / assumption / parameter resolution ---------------------

    def src_ref_html(self, ids):
        """Resolve source_refs to their registered anchor strings."""
        if not ids:
            return self.gap_phrase("source references")
        out = []
        for aid in sorted(ids):
            a = self._src_by_id.get(aid)
            if not a:
                out.append(f"<code>{esc(aid)}</code> (unresolved in source registry)")
                continue
            out.append(f"<code>{esc(aid)}</code>: {esc(source_anchor_str(a))}")
        return self.joined(out, "<br>")

    def asm_ref_html(self, ids):
        if not ids:
            return self.gap_phrase("assumption references")
        out = []
        for aid in sorted(ids):
            a = self._asm_by_id.get(aid)
            if not a:
                out.append(f"<code>{esc(aid)}</code> (unresolved in assumption registry)")
                continue
            out.append(f"<code>{esc(aid)}</code>: {esc(a.get('statement'))}")
        return self.joined(out, "<br>")

    def par_ref_html(self, ids):
        if not ids:
            return self.gap_phrase("parameter references")
        out = []
        for pid in sorted(ids):
            p = self._param_by_id.get(pid)
            if not p:
                out.append(f"<code>{esc(pid)}</code> (unresolved in parameter registry)")
                continue
            out.append(f"<code>{esc(pid)}</code>: {esc(p.get('name'))} = "
                       f"{esc(p.get('value'))} {esc(p.get('unit'))}")
        return self.joined(out, "<br>")

    # ---- links ----------------------------------------------------------

    def links_where(self, profile=None, relation=None, src=None, tgt=None):
        out = []
        for l in self.links:
            if profile is not None and l.get("_profile") != profile:
                continue
            if relation is not None and l.get("relation_type") != relation:
                continue
            if src is not None and l.get("source_id") != src:
                continue
            if tgt is not None and l.get("target_id") != tgt:
                continue
            out.append(l)
        return sorted(out, key=lambda l: (l.get("_profile", ""), l.get("link_id", "")))

    def chain_endpoints(self, relation):
        return self.links_where(relation=relation)

    # ---- coverage -------------------------------------------------------

    def coverage(self, profile, req_id):
        """Verification reachability of a requirement, computed from the link
        registry and the test measures' own referenced_requirements field."""
        direct = sorted({l["source_id"] for l in self.links_where(profile=profile, tgt=req_id)
                         if l.get("relation_type") in COVERAGE_RELATIONS})
        indirect = {}
        for child in sorted({l["source_id"] for l in self.links_where(profile=profile, tgt=req_id)
                             if l.get("relation_type") == "allocated_to"}):
            cdirect = sorted({l["source_id"] for l in self.links_where(profile=profile, tgt=child)
                              if l.get("relation_type") in COVERAGE_RELATIONS})
            if cdirect:
                indirect[child] = cdirect
        embedded = sorted(
            aid for aid in self.ids_where(profile, lambda d: d.get("artifact_type") == "test_measure")
            if req_id in (self.get(profile, aid).get("referenced_requirements") or [])
        )
        if direct:
            status = "COVERED-DIRECT"
        elif indirect:
            status = "COVERED-INDIRECT"
        elif embedded:
            status = "COVERED-EMBEDDED"
        else:
            status = "UNCOVERED"
        return {"status": status, "direct": direct, "indirect": indirect,
                "embedded": embedded,
                "tests": sorted(set(direct) | {t for v in indirect.values() for t in v} | set(embedded))}

    def coverage_links(self, profile, req_id):
        """The full registry metadata for every coverage link touching a
        requirement, so the matrix can show rationale and not just a count."""
        out = [l for l in self.links_where(profile=profile, tgt=req_id)
               if l.get("relation_type") in COVERAGE_RELATIONS]
        for child in sorted({l["source_id"] for l in self.links_where(profile=profile, tgt=req_id)
                             if l.get("relation_type") == "allocated_to"}):
            out += [l for l in self.links_where(profile=profile, tgt=child)
                    if l.get("relation_type") in COVERAGE_RELATIONS]
        return sorted(out, key=lambda l: l.get("link_id", ""))

    def requirements(self):
        return sorted((p, aid) for (p, aid), (_path, d) in self.index.items()
                      if d.get("artifact_type") == "requirement" and p in PROFILES)


def source_anchor_str(anchor):
    """One-line resolution of a source-registry anchor to a human location."""
    loc = anchor.get("location") or {}
    stype = anchor.get("source_type", "unknown")
    if stype == "code":
        parts = [f"`{loc.get('path', '?')}`"]
        if loc.get("symbol"):
            parts.append(f":: `{loc['symbol']}()`")
        if loc.get("line_range"):
            parts.append(f"(L{loc['line_range']})")
        return " ".join(parts)
    if stype == "hardware":
        bits = [f"`{loc.get('file', '?')}`"]
        if loc.get("reference_designator"):
            bits.append(f"({loc['reference_designator']})")
        return " ".join(bits)
    if stype == "test":
        return f"TST: `{loc.get('file', loc.get('path', '?'))}`"
    for k in ("url_or_path", "path", "file", "repository"):
        if loc.get(k):
            return f"DOC: `{loc[k]}`"
    return json.dumps(loc, sort_keys=True)


def requirement_class(aid):
    for marker, label in (("-SWR-", "SWR"), ("-TSR-", "TSR"), ("-FSR-", "FSR"),
                          ("-SEC-", "SEC"), ("-SYR-", "SYR"), ("-SCO-", "SCO")):
        if marker in aid:
            return label
    return "REQ"


def is_software_requirement(d):
    return "-SWR-" in d.get("id", "") or d.get("engineering_domain") == "software"


def verification_section_for(profile, aid, v):
    """Which verification section owns a test measure or an execution record.

    Test measures are placed by their own test_type. Executions inherit the
    placement of the measure they execute, resolved through
    test_measure_id; a range-style id is resolved by its leading member, and an
    unresolvable id is placed in system verification with a declared gap rather
    than being dropped.
    """
    d = v.get(profile, aid)
    if not d:
        return "sec-09-system-verification"
    if d.get("artifact_type") == "test_measure":
        tt = d.get("test_type")
        return ("sec-09-system-verification" if tt in SYSTEM_TEST_TYPES
                else "sec-10-software-verification")
    tmid = d.get("test_measure_id")
    if isinstance(tmid, str):
        member = tmid.split("..")[0].strip()
        measure = v.get(profile, member)
        if measure is not None:
            tt = measure.get("test_type")
            return ("sec-09-system-verification" if tt in SYSTEM_TEST_TYPES
                    else "sec-10-software-verification")
        v.gap("unresolvable-test-reference",
              f"{profile}/{aid}",
              f"The execution record names test measure `{esc(tmid)}`, which the artifact index "
              f"does not hold, so its verification level cannot be derived from the corpus.",
              "execution.test_measure_id")
    return "sec-09-system-verification"


def owning_section(profile, aid, d, v):
    """Map every record type to the section that renders it.

    Ownership and rendering are the same decision, so --check can require that
    every artifact the index holds is anchored somewhere in the document. A
    type with no mapping returns None, which fails the check loudly instead of
    silently disappearing.
    """
    at = d.get("artifact_type")
    if at in ("item_definition", "stakeholder_need", "use_case"):
        return "sec-01-stakeholder"
    if at in ("hazard", "safety_goal", "tara", "safety_concept",
              "safety_case", "safety_analysis"):
        return "sec-02-system-requirements"
    if at == "requirement":
        return "sec-04-software-requirements" if is_software_requirement(d) \
            else "sec-02-system-requirements"
    if at == "design":
        return "sec-05-software-architecture" if d.get("design_level") == "architecture" \
            else "sec-06-detailed-design"
    if at in ("test_measure", "execution"):
        return verification_section_for(profile, aid, v)
    if at == "implementation":
        # an implementation element realises a design, so it belongs with the
        # design it realises: architecture-level implementations with the
        # architecture, the rest with the detailed design.
        return "sec-05-software-architecture" if d.get("design_level") == "architecture" \
            else "sec-06-detailed-design"
    if at == "deviation":
        return "sec-10-software-verification"
    if at == "change":
        return "sec-07-implementation-mapping"
    if at in ("review", "finding", "scenario"):
        return "sec-11-traceability"
    if at in ("project_plan", "measurement_plan", "process_record",
              "process_improvement", "risk_register", "post_development_record"):
        return "sec-15-appendix"
    return None


# ---------------------------------------------------------------- HTML blocks

def table(headers, rows, row_id_fn=None, css_class="", caption=None):
    """A table of already-escaped HTML cells. `rows` is a list of lists."""
    out = []
    if caption:
        out.append(f"<p class=\"tbl-cap\">{caption}</p>")
    cls = f' class="{esc(css_class)}"' if css_class else ""
    out.append(f"<table{cls}>")
    out.append("<thead><tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr></thead>")
    out.append("<tbody>")
    for i, row in enumerate(rows):
        rid = row_id_fn(i, row) if row_id_fn else None
        idattr = f' id="{esc(rid)}"' if rid else ""
        out.append(f"<tr{idattr}>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>")
    out.append("</tbody></table>")
    return out


def kv(label, value_html):
    return f"<p class=\"kv\"><span class=\"k\">{label}</span>{value_html}</p>"


def fv(v, value, what, limit=None):
    """A scalar corpus value, or the mandated gap phrasing when it is absent.

    Every field the engineering process expects is either shown with its corpus
    value or reported as a gap; an empty cell would be neither.
    """
    if value is None or value == "" or value == [] or value == {}:
        return v.gap_phrase(what)
    return esc(value, limit)


def bullets(items, empty=("—",)):
    if not items:
        items = list(empty)
    return ["<ul class=\"bul\">"] + [f"<li>{i}</li>" for i in items] + ["</ul>"]


def card_open(v, profile, aid, d, kind):
    v.rendered_artifact_ids.add((profile, aid))
    g = guard_tuple(d)
    return (f'<article class="card {esc(kind)}" id="{v.anchor(profile, aid)}" '
            f'data-artifact-type="{esc(d.get("artifact_type"))}" '
            f'data-profile="{esc(profile)}" data-revision="{esc(d.get("revision", ""))}">')


def card_head(v, profile, aid, d, kind_label):
    return [
        f"<h4>{v.aref(profile, aid)} — {esc(d.get('title') or aid)}</h4>",
        kv("Record class", f"<code>{esc(kind_label)}</code>"),
        guard_html(guard_tuple(d)),
    ]


def diagram(v, diagram_id, kind, viewpoint, caption, derived_from, body_lines):
    """Emit one Mermaid figure and record it in the diagram inventory.

    The source is placed in a <pre class="mermaid">, which is plain readable
    text. If the client-side renderer is unavailable the reader still gets the
    diagram source, the caption and the derivation note. No <noscript> is
    needed for the source itself; the <noscript> block states the offline
    position explicitly.
    """
    body = "\n".join(body_lines)
    n = len(v.diagrams) + 1
    v.diagrams.append({
        "diagram_id": diagram_id,
        "mermaid_type": kind,
        "viewpoint": viewpoint,
        "caption": caption,
        "derived_from": derived_from,
        "source_lines": len(body_lines),
    })
    out = [
        f'<figure class="diagram" data-diagram-id="{esc(diagram_id)}" '
        f'data-diagram-type="{esc(kind)}" data-diagram-viewpoint="{esc(viewpoint)}">',
        f'<figcaption><span class="dg-id">{esc(diagram_id)}</span> — {esc(caption)}</figcaption>',
        f'<pre class="mermaid" id="mermaid-{n}">{esc_mm(body)}</pre>',
        f'<p class="dg-src"><strong>Derived from</strong>: {esc(derived_from)}</p>',
        '<noscript><p class="noscript">Scripting is off. The Mermaid source above is shown as '
        'readable text, and the caption and the data tables in this section carry the same content. '
        'No diagram in this document is required to read any other part of it.</p></noscript>',
        "</figure>",
    ]
    return out


def sub(heading, level=3, anchor=None):
    a = anchor or re.sub(r"[^a-z0-9]+", "-", heading.lower()).strip("-")
    return f'<h{level} id="{esc(a)}">{esc(heading)}</h{level}>'


def note(text, css_class="note"):
    return f'<p class="{esc(css_class)}">{text}</p>'


def bullets_html(items):
    return ["<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>"]


def ul(items):
    if not items:
        items = ["<em>—</em>"]
    return ["<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>"]


def scalar_list_html(v, values, what):
    """A list of corpus scalars as <li> items, or the mandated gap phrasing.

    Every absent-model site goes through CorpusView.gap_phrase, which counts
    the site, so --check can prove the mandated phrasing survived rendering
    instead of trusting that the renderer remembered to use it.
    """
    if values is None or values == [] or values == "" or values == {}:
        return [f"<p>{v.gap_phrase(what)}</p>"]
    if isinstance(values, (str, int, float, bool)):
        return [f"<p>{esc(values)}</p>"]
    if isinstance(values, dict):
        return ["<ul>" + "".join(
            f"<li><code>{esc(k)}</code>: {esc(val, 300)}</li>" for k, val in sorted(values.items()))
            + "</ul>"]
    return ["<ul>" + "".join(f"<li>{esc(x, 400)}</li>" for x in values) + "</ul>"]


def standards_table(d, v):
    sm = d.get("standards_mappings") or []
    if not sm:
        return f"<p>{v.gap_phrase('standards mappings')}</p>"
    rows = []
    for m in sorted(sm, key=lambda m: (str(m.get("standard_id")), str(m.get("reference")))):
        rows.append([
            f"<code>{esc(m.get('standard_id'))}</code>",
            esc(m.get("reference")),
            f"<code>{esc(m.get('status'))}</code>",
            esc(m.get("rationale")),
        ])
    return "\n".join(table(["Standard / model", "Reference", "Status", "Corpus rationale"], rows,
                           css_class="std"))


def limitation_block(d, v):
    """The record's own limitations/notes, which are the corpus's own caveats."""
    bits = []
    for key in ("limitations", "limitation", "lifecycle_status_note", "latent_defect_note",
                "real_source_control_status_note", "real_source_presence", "notes",
                "measurement_caveat", "evidence_refs_note", "contradictions_found_while_authoring"):
        val = d.get(key)
        if not val:
            continue
        if isinstance(val, list):
            bits.append(f"<li><strong>{esc(key)}</strong>: " +
                        "; ".join(esc(x) for x in val) + "</li>")
        else:
            bits.append(f"<li><strong>{esc(key)}</strong>: {esc(val)}</li>")
    if not bits:
        return f"<p>{v.gap_phrase('record limitations')}</p>"
    return "<ul>" + "".join(bits) + "</ul>"


# ---------------------------------------------------------------- 0. about

def sec_00(v, stamp):
    L = []
    L.append(note(
        "<strong>Derived, not authored.</strong> Every table, card and diagram in this file is "
        "generated by <code>docs/artifacts/tools/render_e2e_html.py</code> from the canonical "
        "corpus JSON under <code>docs/artifacts/</code>. No statement, figure, count or edge in "
        "this document was written by hand, and nothing here is an independent source of truth. "
        "Where the corpus holds no value for something the engineering process expects, this "
        f"document says <span class=\"phrase-ref\">{GAP_PHRASE}</span> and records a named gap in "
        "section&nbsp;12 rather than supplying a plausible substitute.", "callout"))

    L.append(sub("Status of the whole corpus", anchor="status-of-corpus"))
    hs, asp = guard_census(v)
    L.append(kv("Distinct <code>human_approval_status</code> across every record shown",
                esc(", ".join(hs))))
    L.append(kv("Distinct <code>production_authorized</code> across every record shown",
                esc(", ".join(asp))))
    L.append(kv("Distinct <code>profile</code> values", esc(", ".join(sorted(
        {guard_tuple(d)["profile"] for (_p, _a, d) in v.records(lambda _d: True)})))))
    L.append(kv("Records in the artifact index", esc(str(len(v.index)))))
    L.append(kv("Links in both link registries", esc(str(len(v.links)))))
    L.append(note(
        "Every record in this document is printed with its own <code>profile</code>, "
        "<code>origin</code>, <code>human_approval_status</code> and "
        "<code>production_authorized</code> value on a <code>guard</code> line directly beneath "
        "its title, and the same four values are repeated in the <code>data-guard</code> "
        "attribute of that line. The census that produces those two rows is recomputed at render "
        "time from the records themselves; it is not a fixed statement about the corpus."))

    L.append(sub("What this document does not assert", anchor="what-this-is-not"))
    L.append("<ul>")
    L.append("<li>It makes <strong>no ISO 26262 conformity claim</strong>. Structural mapping of a "
             "record to a clause reference is not conformity, and the corpus states that "
             "distinction on its own coverage records.</li>")
    L.append("<li>It states <strong>no ASIL capability level</strong> for any product, process or "
             "organisation. ASIL values appear only as fields recorded inside individual corpus "
             "records, attributed to the record that carries them.</li>")
    L.append("<li>It records <strong>no Automotive SPICE assessment</strong> and no process "
             "capability rating.</li>")
    L.append("<li>It asserts <strong>no human approval</strong> and no review sign-off. Every "
             "record in the corpus carries <code>human_approval_status: pending</code>; an "
             "automated review is not an organisational or human confirmation measure.</li>")
    L.append("<li>It is <strong>not authorised for production use</strong>. Every record carries "
             "<code>production_authorized: false</code>.</li>")
    L.append("</ul>")
    L.append(note(
        "<strong>The two profiles.</strong> <code>as_is</code> is a reconstruction of what the "
        "pinned foxBMS 2 sources demonstrate. <code>synthetic_reference</code> is a "
        "<strong>fictional, hypothetical automotive BMS development project</strong> grounded in "
        "foxBMS. Every ASIL value, hazard, safety goal, item, stakeholder, use case and test "
        "record in the <code>synthetic_reference</code> profile belongs to that fictional project. "
        "No ASIL determination, hazard analysis or safety concept shown here is a determination "
        "for the real foxBMS product, and nothing in this document transfers a requirement, a "
        "limit or a classification from one profile to the other.", "callout"))

    L.append(sub("How to navigate this document", anchor="navigation"))
    L.append("<ul>")
    L.append("<li>Every artifact has an anchor of the form "
             "<code>id=\"art-&lt;profile&gt;-&lt;artifact id&gt;\"</code>. The profile is part of "
             "the anchor because the same artifact identifier exists in both profiles as two "
             "different records by corpus design; a single un-namespaced anchor could not address "
             "both.</li>")
    L.append("<li>A bare identifier in prose is hyperlinked to the <code>as_is</code> record when "
             "one exists and otherwise to the <code>synthetic_reference</code> record. Where both "
             "exist, the text says so, so a reader never mistakes one profile's record for the "
             "other's.</li>")
    L.append("<li>Every link registry entry has an anchor of the form "
             "<code>id=\"lnk-&lt;profile&gt;-&lt;link id&gt;\"</code> and every coverage-matrix row "
             "an anchor <code>id=\"cov-&lt;profile&gt;-&lt;requirement id&gt;\"</code>.</li>")
    L.append("<li>Each section is a collapsible <code>&lt;details&gt;</code> block. Diagrams are "
             "rendered client-side; with scripting or a network unavailable, the Mermaid source "
             "stays readable as text and no other part of the document depends on a diagram "
             "rendering.</li>")
    L.append("</ul>")

    L.append(sub("Regeneration, integrity and determinism", anchor="regeneration"))
    L.append(table(["Purpose", "Command"], [
        ["Regenerate this file",
         "<code>python3 docs/artifacts/tools/render_e2e_html.py</code>"],
        ["Verify integrity and determinism",
         "<code>python3 docs/artifacts/tools/render_e2e_html.py --check</code>"],
        ["Audit guard fields and scan for conformity claims",
         "<code>python3 docs/artifacts/tools/render_e2e_html.py --audit-guard</code>"],
        ["Syntax-check every embedded Mermaid diagram",
         "<code>python3 docs/artifacts/tools/render_e2e_html.py --validate-mermaid</code>"],
        ["Validate and check the underlying corpus",
         "<code>python3 docs/artifacts/tools/corpus.py check</code>"],
    ]))
    L.append(note(
        "Regeneration is deterministic: every collection is iterated in sorted order, embedded "
        "data is serialised with sorted keys, and the template is fixed. The only field that may "
        "differ between two runs against an unchanged corpus is the "
        "<code>data-generated-at</code> attribute in this file's <code>&lt;head&gt;</code>, which "
        "carries the wall-clock time of the run. The integrity check generates the document a "
        "second time into a temporary directory and byte-compares the two after normalising that "
        "one attribute; every other byte must match or the check fails.", "callout"))
    return L


def guard_census(v):
    hs, asp = set(), set()
    for (_p, _a, d) in v.records(lambda _d: True):
        g = guard_tuple(d)
        hs.add(str(g["human_approval_status"]))
        asp.add(g["production_authorized"])
    return sorted(hs), sorted(asp)


# ---------------------------------------------------------------- 1. stakeholder

def sec_01(v):
    L = []
    L.append(note(
        "The stakeholder level of the engineering process: what the item is, what the stakeholders "
        "need from it, and the situations in which they need it. Item definition, stakeholder needs "
        "and use cases exist in the corpus only in the <code>synthetic_reference</code> profile; "
        "the <code>as_is</code> profile holds no record at this level, because the pinned foxBMS "
        "sources do not contain one, and reconstructing one would be inventing a requirement "
        "history the sources do not support.", "callout"))

    # ---- governance scope and applicability
    L.append(sub("Governance Scope and Applicability", anchor="governance-scope"))
    sc = v.scope
    item = sc.get("item_definition") or {}
    L.append(kv("Governance record",
                f"<code>{esc(item.get('id'))}</code> — {esc(item.get('name'))}"))
    L.append(kv("Boundary items included", esc(str(len(item.get("boundaries", {}).get("included", []))))))
    L.append(kv("Boundary items excluded", esc(str(len(item.get("boundaries", {}).get("excluded", []))))))
    L.append(kv("Functions listed", esc(str(len(item.get("functions", []))))))
    L.append(kv("Operating modes listed", esc(str(len(item.get("modes", []))))))
    L.append(kv("Operational situations listed", esc(str(len(item.get("operational_situations", []))))))
    L.append(kv("External systems listed", esc(str(len(item.get("external_systems", []))))))
    if item.get("safety_scope"):
        ss = item["safety_scope"]
        L.append(kv("Functional-safety scope statement", esc(ss.get("functional_safety"))))
        L.append(kv("Hazards addressed by the governance record",
                    esc(", ".join(ss.get("hazards_addressed", [])))))
        L.append(kv("Inherent battery hazards explicitly outside the scope",
                    esc(", ".join(ss.get("inherent_battery_hazards_excluded", [])))))
    ad = sc.get("applicability_decisions") or []
    if ad:
        L.append(sub("Applicability decisions", level=4, anchor="applicability-decisions"))
        rows = []
        for a in sorted(ad, key=lambda a: str(a.get("id"))):
            rows.append([
                f"<code>{esc(a.get('id'))}</code>",
                f"<code>{esc(a.get('standard'))}</code>",
                esc(a.get("part") or ", ".join(a.get("processes", []) or [])),
                f"<code>{esc(a.get('decision'))}</code>",
                esc(a.get("rationale")),
                esc(a.get("responsible_role")),
                esc(a.get("review_record")),
                esc(a.get("conditions_to_change")),
            ])
        L += table(["Decision", "Standard", "Part / processes", "Decision value",
                    "Corpus rationale", "Responsible role", "Review record",
                    "Conditions to change"], rows, css_class="std")
        L.append(note(
            "These are applicability decisions recorded in the corpus: a decision that a part or "
            "process does not apply is a recorded decision with a stated rationale and a stated "
            "condition under which it would change. It is not an assessment of any product.",
            "callout"))
    else:
        v.gap("absent-governance-section", "governance/scope-and-applicability.json",
              "The governance scope record holds no applicability decisions.",
              "scope-and-applicability.json.applicability_decisions")
        L.append(f"<p>{v.gap_phrase('applicability decisions')}</p>")

    # ---- item definition
    L.append(sub("Item Definition", anchor="item-definition"))
    for profile, aid, d in v.records(lambda d: d.get("artifact_type") == "item_definition"):
        L.append(card_open(v, profile, aid, d, "item-definition"))
        L += card_head(v, profile, aid, d, "Item definition")
        ident = d.get("item_identity") or {}
        L.append(kv("Item name", esc(ident.get("item_name"))))
        L.append(kv("Item purpose", esc(ident.get("item_purpose"))))
        if ident.get("fictional"):
            L.append(note(
                "<strong>This item is fictional.</strong> The record's own "
                "<code>item_identity.fictional</code> flag is true. It describes a hypothetical "
                "automotive BMS project, not a real product.", "warn"))
        dc = ident.get("development_context") or {}
        for k in ("vehicle_platform", "development_stage", "reference_implementation", "grounding_note"):
            if dc.get(k):
                L.append(kv(esc(k.replace("_", " ")), esc(dc[k])))
        L.append(sub("In scope", level=4, anchor=f"{aid}-in-scope"))
        L += scalar_list_html(v, d.get("in_scope"), "item scope")
        L.append(sub("Out of scope", level=4, anchor=f"{aid}-out-of-scope"))
        L += scalar_list_html(v, d.get("out_of_scope"), "item out-of-scope")
        L.append(sub("Operating modes", level=4, anchor=f"{aid}-modes"))
        modes = d.get("operating_modes") or []
        if modes:
            L += table(["Mode", "Name", "Entry condition", "Exit condition", "Safe state in this mode"],
                       [[f"<code>{esc(m.get('mode_id'))}</code>", esc(m.get("mode_name")),
                         esc(m.get("entry_condition")), esc(m.get("exit_condition")),
                         esc(m.get("safe_state_in_this_mode"))] for m in modes])
        else:
            L += scalar_list_html(v, [], "operating modes")
        L.append(sub("Operational situations", level=4, anchor=f"{aid}-situations"))
        sits = d.get("operational_situations") or []
        if sits:
            L += table(["Situation", "Description", "In/out", "Corpus argument for the decision"],
                       [[f"<code>{esc(s.get('situation_id'))}</code>", esc(s.get("description")),
                         f"<code>{esc(s.get('including_or_excluding'))}</code>",
                         esc(s.get("argument_for_the_decision"))] for s in sits])
        else:
            L += scalar_list_html(v, [], "operational situations")
        env = d.get("operating_envelope") or {}
        if env:
            L.append(sub("Operating envelope", level=4, anchor=f"{aid}-envelope"))
            for k, val in sorted(env.items()):
                if k == "parameter_refs":
                    L.append(kv("Parameter references", v.par_ref_html(val)))
                else:
                    L.append(kv(esc(k.replace("_", " ")), esc(val)))
        envc = d.get("environmental_conditions") or []
        L.append(sub("Environmental conditions", level=4, anchor=f"{aid}-environment"))
        if envc:
            L += table(["Parameter", "Unit", "Range or limit", "Source of the assumption"],
                       [[esc(e.get("parameter")), esc(e.get("unit")),
                         esc(e.get("range_or_limit")),
                         f"<code>{esc(e.get('source_of_the_assumption'))}</code>"] for e in envc])
        else:
            L += scalar_list_html(v, [], "environmental conditions")
        ext = d.get("external_systems") or []
        L.append(sub("External systems", level=4, anchor=f"{aid}-external-systems"))
        if ext:
            rows = []
            for e in ext:
                rows.append([
                    f"<code>{esc(e.get('system_id'))}</code>",
                    esc(e.get("system_name")),
                    f"<code>{esc(e.get('direction_of_interaction'))}</code>",
                    esc("; ".join(e.get("assumptions_on_the_external_system", []))),
                ])
            L += table(["External system", "Name", "Direction of interaction",
                        "Assumptions on the external system"], rows)
        else:
            L += scalar_list_html(v, [], "external systems")
        ifs = d.get("interfaces_to_other_safety_related_items") or []
        L.append(sub("Interfaces to other safety-related items", level=4,
                     anchor=f"{aid}-other-items"))
        if ifs:
            L += table(["Other item", "Interface description", "Assumption dependence",
                        "Effect if the assumption fails"],
                       [[esc(i.get("other_item")), esc(i.get("interface_description")),
                         esc(i.get("assumption_dependence")),
                         esc(i.get("effect_if_the_assumption_fails"))] for i in ifs])
        else:
            L += scalar_list_html(v, [], "interfaces to other safety-related items")
        L.append(sub("Misuse and service assumptions", level=4, anchor=f"{aid}-misuse"))
        mis = d.get("misuse_and_service_assumptions") or []
        if mis:
            L += table(["Assumption", "Kind", "Who may violate it", "Mitigation or declaration"],
                       [[esc(m.get("assumption")), f"<code>{esc(m.get('kind'))}</code>",
                         esc(m.get("who_may_violate_it")),
                         esc(m.get("mitigation_or_declaration"))] for m in mis])
        else:
            L += scalar_list_html(v, [], "misuse and service assumptions")
        L.append(sub("References", level=4, anchor=f"{aid}-refs"))
        L.append(kv("Stakeholder needs raised", v.joined(v.ref_list(profile, d.get("stakeholder_needs_raised", [])))))
        L.append(kv("Use cases enabled", v.joined(v.ref_list(profile, d.get("use_cases_enabled", [])))))
        L.append(kv("Assumptions on the item", v.asm_ref_html(d.get("assumption_refs"))))
        L.append(kv("Source references", v.src_ref_html(d.get("source_refs"))))
        L.append(kv("Standards mappings", standards_table(d, v)))
        L.append(kv("Record limitations", limitation_block(d, v)))
        L.append("</article>")

    # ---- stakeholder needs
    L.append(sub("Stakeholder Needs", anchor="stakeholder-needs"))
    needs = v.records(lambda d: d.get("artifact_type") == "stakeholder_need")
    if not needs:
        v.gap("absent-record-family", "stakeholder needs",
              "The artifact index holds no stakeholder-need record in either profile.",
              "artifact index, artifact_type == stakeholder_need")
    for profile, aid, d in needs:
        L.append(card_open(v, profile, aid, d, "stakeholder-need"))
        L += card_head(v, profile, aid, d, "Stakeholder need")
        L.append(kv("Need identifier", f"<code>{esc(d.get('need_id'))}</code>"))
        L.append(kv("Stakeholder", esc(d.get("stakeholder"))))
        L.append(kv("Need statement", esc(d.get("need_statement"))))
        L.append(kv("Origin of the need", esc(d.get("origin_of_the_need"))))
        L.append(kv("Rationale", esc(d.get("rationale"))))
        L.append(kv("Priority", f"<code>{esc(d.get('priority'))}</code>"))
        L.append(kv("Operational situations referenced",
                    v.joined(v.ref_list(profile, d.get("operational_situation_refs", [])))))
        L.append(kv("Derived requirements",
                    v.joined(v.ref_list(profile, d.get("derived_requirements", [])))))
        L.append(kv("Validation measures",
                    v.joined(v.ref_list(profile, d.get("validation_measures", [])))))
        L.append(kv("Assumptions", v.asm_ref_html(d.get("assumption_refs"))))
        L.append(kv("Source references", v.src_ref_html(d.get("source_refs"))))
        L.append(kv("Standards mappings", standards_table(d, v)))
        L.append(kv("Record limitations", limitation_block(d, v)))
        L.append("</article>")

    # ---- use cases
    L.append(sub("Use Cases", anchor="use-cases"))
    ucs = v.records(lambda d: d.get("artifact_type") == "use_case")
    if not ucs:
        v.gap("absent-record-family", "use cases",
              "The artifact index holds no use-case record in either profile.",
              "artifact index, artifact_type == use_case")
    for profile, aid, d in ucs:
        L.append(card_open(v, profile, aid, d, "use-case"))
        L += card_head(v, profile, aid, d, "Use case")
        L.append(kv("Use case identifier", f"<code>{esc(d.get('use_case_id'))}</code>"))
        L.append(kv("Use case name", esc(d.get("use_case_name"))))
        L.append(kv("Primary stakeholders", esc(d.get("primary_stakeholders"))))
        L.append(sub("Preconditions", level=4, anchor=f"{aid}-pre"))
        L += scalar_list_html(v, d.get("preconditions"), "use-case preconditions")
        L.append(sub("Main success scenario", level=4, anchor=f"{aid}-main"))
        L += scalar_list_html(v, d.get("main_success_scenario"), "main success scenario")
        L.append(sub("Operational scenarios", level=4, anchor=f"{aid}-ops"))
        L += scalar_list_html(v, d.get("operational_scenarios"), "operational scenarios")
        L.append(sub("Postconditions", level=4, anchor=f"{aid}-post"))
        L += scalar_list_html(v, d.get("postconditions"), "use-case postconditions")
        L.append(kv("Validation measures",
                    v.joined(v.ref_list(profile, d.get("validation_measures", [])))))
        L.append(kv("Assumptions", v.asm_ref_html(d.get("assumption_refs"))))
        L.append(kv("Source references", v.src_ref_html(d.get("source_refs"))))
        L.append(kv("Standards mappings", standards_table(d, v)))
        L.append(kv("Record limitations", limitation_block(d, v)))
        L.append("</article>")
    return L


# ---------------------------------------------------------------- requirement card

def asil_note(d):
    """The ASIL field as the corpus records it, with the mandatory framing."""
    sa = d.get("safety_allocation")
    if not isinstance(sa, dict) or not sa.get("asil"):
        return None
    val = sa.get("asil")
    return (f"<code>{esc(val)}</code> — recorded in this corpus record as the value of "
            f"<code>safety_allocation.asil</code>. It is a value held by a record, not a "
            f"determination made by this document, and for the "
            f"<code>synthetic_reference</code> profile it belongs to a fictional project. "
            f"No ASIL is claimed for the real foxBMS product, and no capability to work at this "
            f"level is claimed for any process or organisation.")


def requirement_card(v, profile, aid, d, heading_level=4):
    """The full attribute set required for any corpus requirement record."""
    L = [card_open(v, profile, aid, d, f"requirement {requirement_class(aid)}")]
    L += card_head(v, profile, aid, d, f"Requirement ({requirement_class(aid)})")
    if v.anchor_exists("as_is", aid) and v.anchor_exists("synthetic_reference", aid) \
            and profile != "as_is":
        L.append(note(
            f"This identifier also exists in the <code>as_is</code> profile as a different "
            f"record: {v.aref('as_is', aid)}.", "warn"))

    L.append(sub("Statement", level=heading_level, anchor=f"{profile}-{aid}-statement"))
    L += scalar_list_html(v, d.get("statement"), "requirement statement")
    L.append(sub("Rationale", level=heading_level, anchor=f"{profile}-{aid}-rationale"))
    L += scalar_list_html(v, d.get("rationale"), "requirement rationale")
    L.append(sub("Classification and allocation", level=heading_level,
                 anchor=f"{profile}-{aid}-classification"))
    L.append(kv("Classification",
                f"<code>{esc(d.get('classification'))}</code>" if d.get("classification")
                else v.gap_phrase("classification")))
    L.append(kv("Engineering domain",
                f"<code>{esc(d.get('engineering_domain'))}</code>" if d.get("engineering_domain")
                else v.gap_phrase("engineering domain")))
    L.append(kv("Requirement level",
                f"<code>{esc(d.get('requirement_level'))}</code>" if d.get("requirement_level")
                else v.gap_phrase("requirement level")))
    L.append(kv("Owner role",
                f"<code>{esc(d.get('owner_role'))}</code>" if d.get("owner_role")
                else v.gap_phrase("owner role")))
    L.append(kv("Lifecycle status",
                f"<code>{esc(d.get('lifecycle_status'))}</code>" if d.get("lifecycle_status")
                else v.gap_phrase("lifecycle status")))
    an = asil_note(d)
    if an:
        L.append(kv("ASIL allocation", an))
        sa = d.get("safety_allocation") or {}
        if sa.get("safety_goal_ref"):
            L.append(kv("Safety goal referenced", v.href(sa["safety_goal_ref"])))
        if sa.get("mitigation"):
            L.append(kv("Recorded mitigation", esc(sa["mitigation"])))
    elif d.get("asil"):
        L.append(kv("ASIL field", f"<code>{esc(d.get('asil'))}</code> — recorded on the record "
                                  f"itself, with the same framing as an allocated ASIL."))
    else:
        L.append(kv("ASIL allocation", v.gap_phrase("ASIL allocation")))
    aj = d.get("asil_justification")
    if aj:
        L.append(kv("ASIL justification", esc(aj)))

    L.append(sub("Acceptance criteria", level=heading_level, anchor=f"{profile}-{aid}-acceptance"))
    ac = d.get("acceptance_criteria") or []
    if ac:
        L += table(["Criterion", "Measure", "Threshold", "Unit"], [
            [esc(a.get("criterion")), esc(a.get("measure")), esc(a.get("threshold")),
             esc(a.get("unit"))] if isinstance(a, dict) else [esc(a), "—", "—", "—"] for a in ac])
    else:
        L += scalar_list_html(v, [], "acceptance criteria")

    L.append(sub("Conditions and modes", level=heading_level, anchor=f"{profile}-{aid}-conditions"))
    L += scalar_list_html(v, d.get("conditions_modes"), "conditions and modes")

    L.append(sub("Verification", level=heading_level, anchor=f"{profile}-{aid}-verification"))
    L.append(kv("Verification approach",
                f"<code>{esc(d.get('verification_approach'))}</code>"
                if d.get("verification_approach") else v.gap_phrase("verification approach")))
    if d.get("verification_status"):
        L.append(kv("Verification status", esc(d["verification_status"])))
    cov = v.coverage(profile, aid)
    L.append(kv("Coverage status derived from the link registry",
                f"<code>{esc(cov['status'])}</code>"))
    cl = v.coverage_links(profile, aid)
    if cl:
        rows = []
        for l in cl:
            rows.append([
                f"<a href=\"#lnk-{esc(l.get('_profile'))}-{esc(l.get('link_id'))}\">"
                f"<code>{esc(l.get('link_id'))}</code></a>",
                v.aref(profile, l.get("source_id")),
                f"<code>{esc(l.get('relation_type'))}</code>",
                v.aref(profile, aid),
                esc(l.get("rationale")),
                f"<code>{esc(l.get('provenance'))}</code>",
                f"<code>{esc(l.get('review_state'))}</code>",
                f"<code>{esc('true' if l.get('change_suspect_status') else 'false')}</code>",
            ])
        L += table(["Link", "From", "Relation", "To", "Rationale", "Provenance",
                    "Review state", "Change-suspect"], rows, css_class="links")
    else:
        L += scalar_list_html(v, [], "coverage links for this requirement")

    L.append(sub("Derivation and dependencies", level=heading_level,
                 anchor=f"{profile}-{aid}-derivation"))
    for label, field, what in (
            ("Refines from", "refines_from", "refines-from references"),
            ("Derived from", "derived_from", "derived-from references"),
            ("Allocated to requirements", "allocated_to_requirements",
             "allocated-to requirements"),
            ("Traces to architecture elements", "trace_to_architecture_elements",
             "architecture-element references"),
            ("Feasibility dependencies", "feasibility_dependencies",
             "feasibility dependencies")):
        L.append(kv(label, v.joined(v.ref_list(profile, d.get(field, []), what))))
    L.append(kv("Parameter references", v.par_ref_html(d.get("parameter_refs"))))
    L.append(kv("Assumption references", v.asm_ref_html(d.get("assumption_refs"))))
    if d.get("assumptions"):
        L.append(kv("Inline assumption references",
                    v.joined(v.ref_list(profile, d.get("assumptions", [])))))
    L.append(kv("Source references", v.src_ref_html(d.get("source_refs"))))

    if d.get("fault_reaction"):
        L.append(kv("Fault reaction", esc(d["fault_reaction"])))
    sd = d.get("signal_definitions")
    if sd:
        L.append(kv("Signal definitions", esc(sd)))
    if d.get("real_source_presence"):
        L.append(kv("Real source presence", esc(d["real_source_presence"])))

    L.append(sub("Standards mappings and record limitations", level=heading_level,
                 anchor=f"{profile}-{aid}-std"))
    L.append(kv("Standards mappings", standards_table(d, v)))
    L.append(kv("Record limitations", limitation_block(d, v)))
    L.append("</article>")
    return L


# ---------------------------------------------------------------- 2. system requirements

def sec_02(v):
    L = []
    L.append(note(
        "The system level: what can go wrong, what must be achieved, how the concept achieves it, "
        "and the requirements derived from it. Technical (TSR), functional-safety (FSR), security "
        "(SEC), system (SYR) and management (SCO) requirement records all appear here, because they "
        "are all derived from or bound to the safety goals rather than allocated to software. "
        "Software requirements appear in section&nbsp;4.", "callout"))

    simple = [
        ("hazard", "Hazards", "hazard"),
        ("safety_goal", "Safety Goals", "safety-goal"),
        ("safety_concept", "Safety Concept", "safety-concept"),
        ("tara", "Threat Analysis and Risk Assessment", "tara"),
        ("safety_analysis", "Safety Analyses", "safety-analysis"),
        ("safety_case", "Safety Case", "safety-case"),
    ]
    for atype, heading, css in simple:
        L.append(sub(heading, anchor=heading.lower().replace(" ", "-")))
        recs = v.records(lambda d, a=atype: d.get("artifact_type") == a)
        if not recs:
            v.gap("absent-record-family", atype,
                  f"The artifact index holds no <code>{esc(atype)}</code> record in either profile, "
                  f"so the corpus provides no {esc(heading.lower())} content at this level.",
                  f"artifact index, artifact_type == {atype}")
            L.append(f"<p>{v.gap_phrase(heading.lower())}</p>")
            continue
        for profile, aid, d in recs:
            L.append(card_open(v, profile, aid, d, css))
            L += card_head(v, profile, aid, d, heading.rstrip("s") if heading != "Safety Case" else "Safety case")
            _generic_fields(v, L, profile, aid, d)
            if atype == "hazard":
                L.append(kv("Hazardous events", esc(d.get("hazardous_events"))))
                L.append(kv("Malfunctioning behaviour", esc(d.get("malfunctioning_behavior"))))
                L.append(kv("Safe states", esc(d.get("safe_states"))))
                L.append(kv("Degraded states", esc(d.get("degraded_states"))))
                L.append(kv("Assumptions", esc(d.get("assumptions"))))
            elif atype == "safety_goal":
                L.append(kv("Statement", esc(d.get("statement"))))
                L.append(kv("ASIL recorded on the record",
                            f"<code>{esc(d.get('asil'))}</code> — recorded on this record, with the "
                            f"same framing as an allocated ASIL: a value held by a record of a "
                            f"fictional project, not a determination for the real product."))
                if d.get("asil_justification"):
                    L.append(kv("ASIL justification", esc(d["asil_justification"])))
                L.append(kv("Fault tolerant time interval", esc(d.get("ftti"))))
                L.append(kv("Fault tolerant time interval (ms)",
                            esc(d.get("fault_tolerant_time_interval_ms"))))
                L.append(kv("Safe state", esc(d.get("safe_state"))))
                L.append(kv("Degraded state", esc(d.get("degraded_state"))))
                L.append(kv("Timing budget", esc(d.get("timing_budget"))))
                L.append(kv("Hazards referenced", v.joined(v.ref_list(profile, d.get("hazard_refs", [])))))
                L.append(kv("Functional safety requirements derived",
                            v.joined(v.ref_list(profile, d.get("functional_safety_requirements", [])))))
            elif atype == "safety_concept":
                ident = d.get("concept_identity") or {}
                L.append(kv("Concept identity", esc(ident.get("concept_name") or ident.get("name"))))
                L.append(kv("Concept stage", f"<code>{esc(d.get('concept_stage'))}</code>"))
                L.append(kv("Scope statement", esc(d.get("scope_statement"))))
                for key, label in (("safety_goals_addressed", "Safety goals addressed"),
                                   ("safety_strategies", "Safety strategies"),
                                   ("architectural_elements", "Architectural elements"),
                                   ("technical_safety_requirements", "Technical safety requirements"),
                                   ("hardware_software_allocation", "Hardware/software allocation"),
                                   ("external_measures", "External measures"),
                                   ("hardware_interfaces_and_assumptions",
                                    "Hardware interfaces and assumptions"),
                                   ("concept_assumptions", "Concept assumptions"),
                                   ("item_related_assumptions", "Item-related assumptions"),
                                   ("diagnostic_coverage_assumptions",
                                    "Diagnostic coverage assumptions"),
                                   ("ftti_and_timing_budget", "FTTI and timing budget"),
                                   ("verification_and_validation_criteria",
                                    "Verification and validation criteria"),
                                   ("interfaces_to_other_safety_related_items",
                                    "Interfaces to other safety-related items")):
                    val = d.get(key)
                    if not val:
                        continue
                    if isinstance(val, list) and all(isinstance(x, str) for x in val):
                        L.append(kv(label, esc("; ".join(val))))
                    else:
                        L.append(kv(label, esc(val)))
            elif atype == "tara":
                L.append(kv("Item and scope", esc(d.get("item_and_scope"))))
                L.append(kv("Method", esc(d.get("method"))))
                L.append(kv("Assets or entry points", esc(d.get("assets_or_entry_points"))))
                L.append(kv("Out of scope", esc(d.get("out_of_scope"))))
                L.append(kv("Related sources", esc(d.get("related_sources"))))
                L.append(kv("Residual risk acceptance", esc(d.get("residual_risk_acceptance"))))
                L.append(kv("Security requirements derived",
                            v.joined(v.ref_list(profile, d.get("security_requirements_refs", [])))))
                _list_kv(L, "Threats", d.get("threats"))
                _list_kv(L, "Mitigations", d.get("mitigations"))
                _list_kv(L, "Assumptions", d.get("assumptions"))
            L.append(kv("Assumption references", v.asm_ref_html(d.get("assumption_refs"))))
            L.append(kv("Source references", v.src_ref_html(d.get("source_refs"))))
            L.append(kv("Standards mappings", standards_table(d, v)))
            L.append(kv("Record limitations", limitation_block(d, v)))
            L.append("</article>")

    # ---- system and technical requirements
    L.append(sub("System and Technical Requirements", anchor="system-and-technical-requirements"))
    groups = [
        ("Functional Safety Requirements (FSR)", lambda aid: "-FSR-" in aid),
        ("Security Requirements (SEC)", lambda aid: "-SEC-" in aid),
        ("System Requirements (SYR)", lambda aid: "-SYR-" in aid),
        ("Technical System Requirements (TSR)", lambda aid: "-TSR-" in aid),
        ("Management and Process Requirements (SCO)", lambda aid: "-SCO-" in aid),
    ]
    any_group = False
    for title, pred in groups:
        recs = v.records(lambda d, p=pred: d.get("artifact_type") == "requirement" and p(d.get("id", "")))
        if not recs:
            v.gap("absent-requirement-class", title,
                  f"The artifact index holds no {esc(title)} record in either profile.",
                  "artifact index, artifact_type == requirement")
            L.append(sub(title, level=4, anchor=re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")))
            L.append(f"<p>{v.gap_phrase(title)}</p>")
            continue
        any_group = True
        L.append(sub(title, level=4, anchor=re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")))
        L.append(note(f"{len(recs)} record(s) in the corpus at this class.", "meta"))
        for profile, aid, d in recs:
            L += requirement_card(v, profile, aid, d, heading_level=5)
    if not any_group:
        L.append(f"<p>{v.gap_phrase('system and technical requirements')}</p>")
    return L


def _generic_fields(v, L, profile, aid, d):
    L.append(kv("Engineering domain", f"<code>{esc(d.get('engineering_domain'))}</code>"))
    L.append(kv("Owner role", f"<code>{esc(d.get('owner_role'))}</code>"))
    L.append(kv("Lifecycle status", f"<code>{esc(d.get('lifecycle_status'))}</code>"))
    L.append(kv("Scenario", f"<code>{esc(d.get('scenario_id'))}</code>"))
    L.append(kv("Baseline", f"<code>{esc(d.get('baseline_id'))}</code>"))
    L.append(kv("Variant applicability", esc(", ".join(d.get("variant_applicability", []) or []))))


def _list_kv(L, label, val):
    if not val:
        return
    if isinstance(val, list) and all(isinstance(x, str) for x in val):
        L.append(kv(label, esc("; ".join(val))))
        return
    L.append(kv(label, esc(val)))


# ---------------------------------------------------------------- 3. system architecture

def chain_ids(v, profile):
    """The allocation/derivation chain, in engineering order, derived only from
    the link registry of one profile.

    Order: hazards <-mitigates- safety goals <-refines- functional safety
    requirements <-allocated_to- technical/software requirements <-implements-
    designs, plus the measures that verify any of them. `reviewed_by` links are
    excluded: they are review bookkeeping, not an engineering allocation, and
    including 229 of them would make the blocks unreadable. The exclusion is
    stated in the diagram's derivation note.
    """
    chain_relations = ("mitigates", "refines", "allocated_to", "implements")
    cov_relations = COVERAGE_RELATIONS
    links = [l for l in v.links
             if l.get("_profile") == profile and l.get("relation_type") in chain_relations]
    covlinks = [l for l in v.links
                if l.get("_profile") == profile and l.get("relation_type") in cov_relations]
    return sorted(links, key=lambda l: (l.get("source_id", ""), l.get("target_id", ""))), \
        sorted(covlinks, key=lambda l: (l.get("source_id", ""), l.get("target_id", "")))


def protection_chain(v, profile):
    """The cell-voltage protection chain for one profile, walked from the link
    registry. Returns an ordered dict of stage -> [ids] and the links used."""
    hazards = v.ids_where(profile, lambda d: d.get("artifact_type") == "hazard")
    out = {"hazard": [], "safety_goal": [], "fsr": [], "tsr": [], "swr": [],
           "design": [], "test_measure": []}
    used = []
    for h in hazards:
        out["hazard"].append(h)
    for l in v.links_where(profile=profile, relation="mitigates"):
        if l["target_id"] in out["hazard"]:
            out["safety_goal"].append(l["source_id"])
            used.append(l)
    goals = set(out["safety_goal"])
    for l in v.links_where(profile=profile, relation="refines"):
        if l["target_id"] in goals:
            out["fsr"].append(l["source_id"])
            used.append(l)
    fsrs = set(out["fsr"])
    for l in v.links_where(profile=profile, relation="allocated_to"):
        if l["target_id"] in fsrs:
            tid = l["source_id"]
            if "-TSR-" in tid:
                out["tsr"].append(tid)
            elif "-SWR-" in tid:
                out["swr"].append(tid)
            used.append(l)
    reqs = set(out["tsr"]) | set(out["swr"])
    for l in v.links_where(profile=profile, relation="implements"):
        if l["target_id"] in reqs:
            out["design"].append(l["source_id"])
            used.append(l)
    designs = set(out["design"])
    for l in v.links_where(profile=profile, relation=COVERAGE_RELATIONS[0]):
        if l["target_id"] in reqs or l["target_id"] in designs:
            out["test_measure"].append(l["source_id"])
            used.append(l)
    for k in out:
        out[k] = sorted(set(out[k]))
    return out, sorted(used, key=lambda l: l.get("link_id", ""))


def sec_03(v):
    L = []
    L.append(note(
        "Three system viewpoints. Every diagram below is generated from corpus "
        "records — the item definition's structured external-system and "
        "safety-related-item lists, and the per-profile link registries — and "
        "every figure states which records produced it. No node and no edge in "
        "any diagram was chosen by hand.", "callout"))

    # ---- (a) context viewpoint
    L.append(sub("Context Viewpoint", anchor="context-viewpoint"))
    item = v.records(lambda d: d.get("artifact_type") == "item_definition")
    if not item:
        v.gap("absent-record-family", "system context",
              "No item-definition record exists, so the system boundary and the external "
              "actors cannot be derived.", "artifact index, artifact_type == item_definition")
        L.append(f"<p>{v.gap_phrase('system context viewpoint')}</p>")
    for profile, aid, d in item:
        ext = d.get("external_systems") or []
        other = d.get("interfaces_to_other_safety_related_items") or []
        ident = (d.get("item_identity") or {})
        body = [f"  ITEM[{mlabel(ident.get('item_name') or aid)}]"]
        for e in ext:
            sid = e.get("system_id")
            body.append(f"  {mid(sid)}[{mlabel(f'{sid} {e.get('system_name')}', 70)}]")
        for i, o in enumerate(other):
            body.append(f"  OTH{i}[{mlabel(o.get('other_item'), 70)}]")
        for e in ext:
            sid = e.get("system_id")
            direction = e.get("direction_of_interaction")
            if direction == "external_to_item":
                body.append(f"  {mid(sid)} -->|{mv(direction)}| ITEM")
            elif direction == "item_to_external":
                body.append(f"  ITEM -->|{mv(direction)}| {mid(sid)}")
            else:
                body.append(f"  ITEM <-->|{mv(direction or 'interaction')}| {mid(sid)}")
        for i, _o in enumerate(other):
            body.append(f"  ITEM -.->|interface recorded on {aid}| OTH{i}")
        L += diagram(
            v, f"system.context.{profile}", "flowchart LR", "System context viewpoint",
            f"System boundary of {aid} and the external systems and other safety-related items "
            f"the record itself lists, with the direction of interaction it records.",
            f"{profile} artifact index: {aid} → external_systems[].direction_of_interaction, "
            f"interfaces_to_other_safety_related_items[]",
            ["flowchart LR"] + body)
        L.append(sub("Boundary exclusions declared in the governance record", level=4,
                     anchor="boundary-exclusions"))
        gitem = (v.scope.get("item_definition") or {})
        exc = (gitem.get("boundaries") or {}).get("excluded") or []
        inc = (gitem.get("boundaries") or {}).get("included") or []
        if exc or inc:
            L += table(["Boundary", "Declaration"], [
                ["included"] + [f"<code>{esc(x)}</code>" for x in inc],
                ["excluded"] + [f"<code>{esc(x)}</code>" for x in exc],
            ], css_class="wide")
        else:
            L.append(f"<p>{v.gap_phrase('boundary inclusions and exclusions')}</p>")

    # ---- (b) functional block viewpoint
    L.append(sub("Functional Block Viewpoint", anchor="functional-block-viewpoint"))
    for profile in PROFILES:
        links, covlinks = chain_ids(v, profile)
        if not links:
            v.gap("absent-link-relations", f"functional block viewpoint ({profile})",
                  f"The {profile} link registry holds no refines, mitigates, allocated_to or "
                  f"implements link, so no block structure can be derived for this profile.",
                  f"{profile} link registry")
            L.append(f"<p>{v.gap_phrase(f'functional block viewpoint ({profile})')}</p>")
            continue
        body = []
        seen = set()
        for l in links + covlinks:
            for endpoint in (l.get("source_id"), l.get("target_id")):
                if endpoint and endpoint not in seen:
                    seen.add(endpoint)
                    body.append(f"  {mid(endpoint)}[{mlabel(short_id(endpoint), 46)}]")
        for l in links:
            body.append(f"  {mid(l['source_id'])} -->|{mv(l['relation_type'])}| {mid(l['target_id'])}")
        for l in covlinks:
            body.append(f"  {mid(l['source_id'])} -->|{mv(l['relation_type'])}| {mid(l['target_id'])}")
        L += diagram(
            v, f"system.functional-block.{profile}", "flowchart TD",
            "System functional block viewpoint",
            f"Blocks and allocation flows of the {profile} profile, one node per artifact that "
            f"takes part in a derivation, allocation, implementation or verification link, "
            f"labelled with the relation type the registry records.",
            f"{profile} link registry, relation_type in "
            f"{{mitigates, refines, allocated_to, implements, verifies, validates}}; "
            f"reviewed_by links excluded as review bookkeeping "
            f"({len([l for l in v.links if l.get('_profile') == profile and l.get('relation_type') == 'reviewed_by'])} "
            f"in this profile)",
            ["flowchart TD"] + body)

    # ---- (c) dynamic viewpoint
    L.append(sub("Dynamic Viewpoint", anchor="dynamic-viewpoint"))
    for profile in PROFILES:
        chain, used = protection_chain(v, profile)
        if not chain["hazard"] and not chain["safety_goal"]:
            v.gap("absent-derivation-chain", f"protection chain ({profile})",
                  f"The {profile} link registry holds no hazard and no mitigates link, so no "
                  f"protection chain can be derived for this profile.",
                  f"{profile} link registry, relation_type in {{mitigates, refines, allocated_to, implements, verifies}}")
            L.append(f"<p>{v.gap_phrase(f'protection chain flow ({profile})')}</p>")
            continue
        stages = [
            ("hazard", "Hazard"),
            ("safety_goal", "Safety goal"),
            ("fsr", "Functional safety requirement"),
            ("tsr", "Technical system requirement"),
            ("swr", "Software requirement"),
            ("design", "Design"),
        ]
        body = []
        for key, label in stages:
            for i, rid in enumerate(chain[key]):
                d = v.get(profile, rid) or {}
                body.append(f"  {mid(key + str(i))}[{mlabel(f'{label}: {short_id(rid)}', 64)}]")
        for i, rid in enumerate(chain["hazard"]):
            body.append(f"  {mid('hazard' + str(i))} --> {mid('sg0')}")
        for i, rid in enumerate(chain["safety_goal"]):
            body.append(f"  {mid('sg' + str(i))} --> {mid('fsr0')}")
        for i, rid in enumerate(chain["fsr"]):
            body.append(f"  {mid('fsr' + str(i))} --> {mid('tsr0')}")
        for i, rid in enumerate(chain["tsr"]):
            body.append(f"  {mid('tsr' + str(i))} --> {mid('swr0')}")
        for i, rid in enumerate(chain["swr"]):
            body.append(f"  {mid('swr' + str(i))} --> {mid('dsn0')}")
        for i, rid in enumerate(chain["design"]):
            body.append(f"  {mid('dsn' + str(i))} --> {mid('tm0')}")
        for i, mid_ in enumerate(chain["test_measure"]):
            exes = [e for e in v.ids_where(profile, lambda d: d.get("artifact_type") == "execution")
                    if _measure_of(v, profile, e) == mid_]
            label = f"Test measure: {short_id(mid_)}"
            if exes:
                outcomes = sorted({(v.get(profile, e) or {}).get("outcome", "unknown") for e in exes})
                label += f" — outcome: {', '.join(outcomes)}"
            body.append(f"  {mid('tm' + str(i))}[{mlabel(label, 76)}]")
        L += diagram(
            v, f"system.protection-chain.{profile}", "flowchart TD",
            "System dynamic viewpoint (protection chain)",
            f"The {profile} cell-voltage protection chain as a flow, walked from the hazard to the "
            f"test measures that verify it, ending at the recorded outcome of the executions of "
            f"those measures.",
            f"{profile} link registry (hazard, mitigates, refines, allocated_to, implements, "
            f"verifies) joined to execution records by execution.test_measure_id",
            ["flowchart TD"] + body)
        # sequence diagram from the measures' own steps
        seq = _sequence_for_chain(v, profile, chain)
        L += seq
    L += sec_03_derivation(v)
    return L


def _measure_of(v, profile, exe_id):
    d = v.get(profile, exe_id) or {}
    tmid = d.get("test_measure_id")
    if not isinstance(tmid, str):
        return None
    return tmid.split("..")[0].strip()


def short_id(aid):
    """Readable node label: the stable numeric tail of a corpus identifier."""
    if not aid:
        return "?"
    parts = str(aid).split("-")
    return "-".join(parts[-2:]) if len(parts) >= 2 else str(aid)


def _sequence_for_chain(v, profile, chain):
    """A test-procedure sequence diagram built from the corpus test measures'
    own step lists. Every message is a step the corpus records; no step is
    invented, and a measure with no steps is reported as absent."""
    out = []
    for tmid in chain["test_measure"]:
        d = v.get(profile, tmid)
        steps = (d or {}).get("steps") or []
        if not steps:
            v.gap("absent-test-steps", f"{profile}/{tmid}",
                  f"The test measure records no steps, so no procedure sequence can be derived "
                  f"from it for the protection-chain sequence diagram.",
                  "test_measure.steps")
            out.append(note(
                f"Sequence for {v.href(tmid)}: {v.gap_phrase('test steps')}", "warn"))
            continue
        refs = (d or {}).get("referenced_requirements") or []
        designs = (d or {}).get("referenced_designs") or []
        sut_parts = [short_id(r) for r in sorted(refs)] + [short_id(x) for x in sorted(designs)]
        sut = ", ".join(sut_parts) if sut_parts else "the implementation under test"
        body = ["sequenceDiagram", "  autonumber",
                f"  participant H as {mlabel(mseq('test measure ' + short_id(tmid), 44))}",
                f"  participant S as {mlabel(mseq('subject ' + sut, 60))}"]
        for s in steps:
            if not isinstance(s, dict):
                continue
            n = s.get("step", "?")
            action = s.get("action", "")
            expected = s.get("expected", "")
            body.append(f"  H->>S: step {esc_mm(mv(n, 4))} — {esc_mm(mseq(action, 80))}")
            if expected:
                body.append(f"  Note right of S: expected {esc_mm(mseq(expected, 80))}")
        out += diagram(
            v, f"system.protection-chain-sequence.{profile}.{short_id(tmid)}",
            "sequenceDiagram", "System dynamic viewpoint (test procedure sequence)",
            f"Test procedure of {tmid} as a sequence, one message per step the record lists, with "
            f"its own expected result as a note.",
            f"{profile} artifact index: {tmid} → steps[].step/action/expected, "
            f"referenced_requirements, referenced_designs",
            body)
    if not out:
        v.gap("absent-test-procedure", f"protection chain sequence ({profile})",
              "No test measure in the derived protection chain records any steps, so no procedure "
              "sequence diagram can be derived.", f"{profile} artifact index, test_measure.steps")
        out.append(f"<p>{v.gap_phrase(f'test procedure sequence ({profile})')}</p>")
    return out


def sec_03_derivation(v):
    """Section 3's derivation table, rendered after the diagrams."""
    L = [sub("Viewpoint Derivation", anchor="viewpoint-derivation")]
    rows = []
    for d in v.diagrams:
        if not d["diagram_id"].startswith("system."):
            continue
        rows.append([f"<code>{esc(d['diagram_id'])}</code>", f"<code>{esc(d['mermaid_type'])}</code>",
                     esc(d["viewpoint"]), esc(d["derived_from"]), esc(str(d["source_lines"]))])
    L += table(["Diagram identifier", "Mermaid type", "Viewpoint", "Corpus records it is derived from",
                "Source lines"], rows, css_class="wide")
    return L


# ---------------------------------------------------------------- 4. software requirements

def sec_04(v):
    L = []
    L.append(note(
        "Software requirements: the requirements allocated to software, rendered with the same "
        "complete attribute set as the system requirements in section&nbsp;2. Every field the "
        "engineering process expects is either shown with its corpus value or reported as "
        f"<span class=\"phrase-ref\">{GAP_PHRASE}</span>.", "callout"))
    recs = v.records(lambda d: d.get("artifact_type") == "requirement" and is_software_requirement(d))
    if not recs:
        v.gap("absent-record-family", "software requirements",
              "The artifact index holds no software requirement record in either profile.",
              "artifact index, artifact_type == requirement and software domain")
        L.append(f"<p>{v.gap_phrase('software requirements')}</p>")
    for profile, aid, d in recs:
        L += requirement_card(v, profile, aid, d, heading_level=4)
    return L


# ---------------------------------------------------------------- 5/6. design

def design_summary(v, L, profile, aid, d):
    L.append(kv("Title", esc(d.get("title"))))
    L.append(kv("Design level", f"<code>{esc(d.get('design_level'))}</code>"))
    L.append(kv("Engineering domain", f"<code>{esc(d.get('engineering_domain'))}</code>"))
    L.append(kv("Owner role", f"<code>{esc(d.get('owner_role'))}</code>"))
    L.append(kv("Lifecycle status", f"<code>{esc(d.get('lifecycle_status'))}</code>"))
    L.append(kv("Variant applicability", esc(", ".join(d.get("variant_applicability", []) or []))))
    vat = d.get("variant_applicability_table")
    if vat:
        L.append(kv("Variant applicability table", esc(vat)))


def design_links_table(v, profile, aid):
    out = []
    for direction, pred in (("incoming", lambda l: l.get("target_id") == aid),
                            ("outgoing", lambda l: l.get("source_id") == aid)):
        for l in v.links_where(profile=profile):
            if not pred(l):
                continue
            if l.get("relation_type") == "reviewed_by":
                continue
            out.append([
                direction,
                f"<a href=\"#lnk-{esc(l.get('_profile'))}-{esc(l.get('link_id'))}\">"
                f"<code>{esc(l.get('link_id'))}</code></a>",
                f"<code>{esc(l.get('relation_type'))}</code>",
                v.href(l.get("source_id")),
                v.href(l.get("target_id")),
                esc(l.get("rationale")),
                f"<code>{esc(l.get('provenance'))}</code>",
                f"<code>{esc(l.get('review_state'))}</code>",
                f"<code>{esc('true' if l.get('change_suspect_status') else 'false')}</code>",
            ])
    return out


def sec_05(v):
    L = []
    L.append(note(
        "Software architecture: the static component viewpoint derived from the "
        "<code>implements</code> and <code>allocated_to</code> links, and the dynamic state "
        "viewpoint derived from each design record's own <code>behavior_model</code>. A design "
        "with no behaviour model in the corpus produces a state diagram stating so, never an "
        "invented one.", "callout"))

    arch = v.records(lambda d: d.get("artifact_type") == "design"
                     and d.get("design_level") == "architecture")
    other_dsns = v.records(lambda d: d.get("artifact_type") == "design"
                           and d.get("design_level") != "architecture")
    L.append(kv("Architecture-level design records", esc(str(len(arch)))))
    L.append(kv("Design records at other levels, shown in section 6", esc(str(len(other_dsns)))))

    # ---- static component viewpoint
    L.append(sub("Static Component Viewpoint", anchor="static-component-viewpoint"))
    for profile in PROFILES:
        links = [l for l in v.links_where(profile=profile)
                 if l.get("relation_type") in ("implements", "allocated_to")]
        if not links:
            v.gap("absent-link-relations", f"static component viewpoint ({profile})",
                  f"The {profile} link registry holds no implements or allocated_to link, so no "
                  f"component structure can be derived for this profile.",
                  f"{profile} link registry")
            L.append(f"<p>{v.gap_phrase(f'static component viewpoint ({profile})')}</p>")
            continue
        body = []
        seen = set()
        for l in links:
            for endpoint in (l.get("source_id"), l.get("target_id")):
                if endpoint not in seen:
                    seen.add(endpoint)
                    body.append(f"  {mid(endpoint)}[{mlabel(short_id(endpoint), 40)}]")
        for l in links:
            body.append(f"  {mid(l['source_id'])} -->|{mv(l['relation_type'])}| {mid(l['target_id'])}")
        L += diagram(
            v, f"software.static-component.{profile}", "flowchart TD",
            "Software static component viewpoint",
            f"Software requirements, the requirements they are allocated to, and the designs that "
            f"implement them, in the {profile} profile, with the relation the registry records.",
            f"{profile} link registry, relation_type in {{implements, allocated_to}}",
            ["flowchart TD"] + body)
        rows = []
        for l in links:
            rows.append([
                v.aref(profile, l["source_id"]),
                f"<code>{esc(l['relation_type'])}</code>",
                v.aref(profile, l["target_id"]),
                esc(l.get("rationale")),
                f"<code>{esc(l.get('provenance'))}</code>",
                f"<code>{esc(l.get('review_state'))}</code>",
            ])
        L += table(["From", "Relation", "To", "Rationale", "Provenance", "Review state"], rows,
                   css_class="links")
    for profile, aid, d in arch:
        dec = d.get("decomposition") or []
        if not dec:
            v.gap("absent-decomposition", f"{profile}/{aid}",
                  "The architecture design record declares no decomposition, so no component tree "
                  "can be derived from it.", f"{profile} artifact index: {aid} → decomposition")
            L.append(note(f"Component tree of {v.aref(profile, aid)}: "
                          f"{v.gap_phrase('decomposition')}", "warn"))
            continue
        body = [f"  {mid(aid)}[{mlabel(f'{short_id(aid)} {d.get("title") or aid}', 60)}]"]
        for i, c in enumerate(dec):
            if isinstance(c, dict):
                cid = c.get("child_id") or c.get("component") or c.get("name") or f"child-{i}"
                rel = c.get("relationship") or "contains"
                cd = v.get(profile, cid) or {}
                label = f"{short_id(cid)} {cd.get('title')}" if cd.get("title") else short_id(cid)
                body.append(f"  {mid(str(cid))}[{mlabel(label, 56)}]")
                body.append(f"  {mid(aid)} -->|{mv(rel)}| {mid(str(cid))}")
            else:
                body.append(f"  C{i}[{mlabel(c, 50)}]")
                body.append(f"  {mid(aid)} -->|contains| C{i}")
        L += diagram(
            v, f"software.static-decomposition.{profile}.{short_id(aid)}", "flowchart TD",
            "Software static component viewpoint (declared decomposition)",
            f"The component tree {aid} itself declares, one node per declared child with the "
            f"relationship the record gives for it.",
            f"{profile} artifact index: {aid} → decomposition[].child_id, "
            f"decomposition[].relationship",
            ["flowchart TD"] + body)

    # ---- dynamic viewpoint
    L.append(sub("Dynamic Viewpoint", anchor="dynamic-viewpoint"))
    L.append(note(
        "The dynamic viewpoint of the architecture level: one state machine per "
        "architecture-level design record, taken from that record's own "
        "<code>behavior_model</code>. Detailed-design records carry their own dynamic diagram in "
        "section 6, and are not repeated here.", "meta"))
    for profile, aid, d in arch:
        bm = d.get("behavior_model")
        if not isinstance(bm, dict) or not bm.get("states"):
            v.gap("absent-behaviour-model", f"{profile}/{aid}",
                  f"The design record holds no behavior_model with states, so no state diagram can "
                  f"be derived for it.",
                  f"{profile} artifact index: {aid} → behavior_model.states/transitions")
            L.append(note(f"State model of {v.aref(profile, aid)}: "
                          f"{v.gap_phrase('behaviour model')}", "warn"))
            continue
        states = [s for s in bm.get("states", []) if isinstance(s, str)]
        trans = [t for t in (bm.get("transitions") or []) if isinstance(t, dict)]
        body = [f"  [*] --> {mid(states[0])}"]
        for t in trans:
            f_, t_ = t.get("from"), t.get("to")
            if not f_ or not t_:
                continue
            trig = t.get("trigger")
            guard = t.get("guard")
            label_bits = [x for x in (mv(trig, 40) if trig else None,
                                      mv(guard, 30) if guard else None) if x]
            suffix = f" : {' / '.join(label_bits)}" if label_bits else ""
            body.append(f"  {mid(f_)} --> {mid(t_)}{suffix}")
        for s in states:
            body.append(f"  {mid(s)}")
        L += diagram(
            v, f"software.state.{profile}.{short_id(aid)}", "stateDiagram-v2",
            "Software dynamic state-machine viewpoint",
            f"State machine of {aid}, containing exactly the states and transitions the design "
            f"record declares ({len(states)} states, {len(trans)} transitions).",
            f"{profile} artifact index: {aid} → behavior_model.states[], "
            f"behavior_model.transitions[].from/to/trigger/guard",
            ["stateDiagram-v2"] + body)
        L.append(note(
            f"Declared model type: <code>{esc(bm.get('type'))}</code>. "
            f"States: {esc(', '.join(states))}. "
            f"Transitions present in the record: {esc(str(len(trans)))}; transitions drawn: "
            f"{esc(str(sum(1 for t in trans if t.get('from') and t.get('to'))))}.", "meta"))

    # ---- architecture decisions
    L.append(sub("Architecture Decisions", anchor="architecture-decisions"))
    if not arch:
        v.gap("absent-design-level", "software architecture",
              "The artifact index holds no design record with design_level == architecture.",
              "artifact index, design.design_level")
        L.append(f"<p>{v.gap_phrase('architecture-level design records')}</p>")
    for profile, aid, d in arch:
        L.append(card_open(v, profile, aid, d, "design-architecture"))
        L += card_head(v, profile, aid, d, "Architecture design")
        design_summary(v, L, profile, aid, d)
        L.append(sub("Responsibilities", level=4, anchor=f"{profile}-{aid}-resp"))
        L += scalar_list_html(v, d.get("responsibilities"), "design responsibilities")
        L.append(sub("Interfaces", level=4, anchor=f"{profile}-{aid}-ifaces"))
        L += interface_table(v, d)
        L.append(sub("Constraints", level=4, anchor=f"{profile}-{aid}-cons"))
        L += scalar_list_html(v, d.get("constraints"), "design constraints")
        L.append(sub("Decisions", level=4, anchor=f"{profile}-{aid}-dec"))
        _list_kv(L, "Recorded decisions", d.get("decisions"))
        L.append(sub("Registry links", level=4, anchor=f"{profile}-{aid}-links"))
        rows = design_links_table(v, profile, aid)
        if rows:
            L += table(["Direction", "Link", "Relation", "Source", "Target", "Rationale",
                        "Provenance", "Review state", "Change-suspect"], rows, css_class="links")
        else:
            L.append(f"<p>{v.gap_phrase('derivation links for this design')}</p>")
        L.append(kv("Assumption references", v.asm_ref_html(d.get("assumption_refs"))))
        L.append(kv("Source references", v.src_ref_html(d.get("source_refs"))))
        L.append(kv("Standards mappings", standards_table(d, v)))
        L.append(kv("Record limitations", limitation_block(d, v)))
        L.append("</article>")
    return L


def interface_table(v, d):
    ifs = d.get("interfaces") or []
    if not ifs:
        return [f"<p>{v.gap_phrase('interfaces')}</p>"]
    rows = []
    for i in ifs:
        if not isinstance(i, dict):
            rows.append([esc(i), "—", "—", "—"])
            continue
        sigs = i.get("signals") or []
        sig_rows = []
        for s in sigs:
            if isinstance(s, dict):
                sig_rows.append(
                    f"<code>{esc(s.get('name'))}</code> — {esc(s.get('type'))}, "
                    f"{esc(s.get('unit'))}, range {esc(s.get('range'))}, rate {esc(s.get('rate'))}")
            else:
                sig_rows.append(esc(s))
        rows.append([f"<code>{esc(i.get('interface_id'))}</code>",
                     esc(i.get("direction")),
                     "<br>".join(sig_rows) if sig_rows else "—",
                     esc(i.get("protocol") or i.get("notes") or "not specified in corpus")])
    return table(["Interface", "Direction", "Signals", "Notes"], rows, css_class="wide")


def sec_06(v):
    L = []
    L.append(note(
        "Detailed design, one subsection per design record. Each subsection shows the record's own "
        "decomposition, interfaces, constraints, budgets and failure response, plus a static and a "
        "dynamic diagram derived from those same fields. A field the record does not hold is "
        f"reported as <span class=\"phrase-ref\">{GAP_PHRASE}</span> and registered in "
        "section&nbsp;12.", "callout"))
    # Implementation elements: emitted with the design section they belong to, so
    # the ownership map's claim that they are rendered there is true.
    imps = v.records(lambda d: d.get("artifact_type") == "implementation"
                     and d.get("design_level") != "architecture")
    if imps:
        L.append(sub("Implementation elements", level=3,
                     anchor="implementation-elements-detailed"))
        L.append('<p class="note">Each element below is a code location that realises a '
                 'design. Location, symbol and hash were read from the pinned source; '
                 '<code>implementation_status</code> states whether the element is present '
                 'in that source or is proposed and absent from it.</p>')
    for profile, aid, d in imps:
        L.append(f'<article class="card implementation" id="{v.anchor(profile, aid)}" '
                 f'data-artifact-type="implementation" data-profile="{esc(profile)}" '
                 f'data-revision="{esc(d.get("revision", ""))}">')
        v.rendered_artifact_ids.add((profile, aid))
        L += card_head(v, profile, aid, d, "Implementation element")
        L.append(sub("Code locations", level=4, anchor=f"{profile}-{aid}-locations"))
        locs = d.get("code_locations") or []
        if not locs:
            L.append(f"<p>{v.gap_phrase('implementation code locations')}</p>")
        else:
            L.append("<table class=\"kv\"><thead><tr><th>path</th><th>symbol</th>"
                     "<th>lines</th><th>role</th><th>verified</th>"
                     "<th>pinned parts</th></tr></thead><tbody>")
            for loc in locs:
                if not isinstance(loc, dict):
                    continue
                # `verified` was the field name read here and NO code_location
                # has ever carried it, so the column rendered empty on every row
                # of every implementation card. The aggregate is
                # `verified_against_pinned_source`, and since FB2-REV-FND-000173
                # it is only the conjunction of four named parts, so both are
                # rendered: a reader who sees the aggregate without the parts is
                # back to reading one boolean as four checks.
                parts = [loc.get(f) for f in ("pinned_file_exists",
                                              "pinned_content_hash_matches",
                                              "line_range_within_file",
                                              "symbol_within_line_range")]
                parts_txt = ("".join("Y" if v is True else ("n" if v is False else "?"))
                             for v in parts)
                agg = loc.get('verified_against_pinned_source')
                L.append("<tr>"
                         f"<td><code>{esc(loc.get('path', ''))}</code></td>"
                         f"<td><code>{esc(loc.get('symbol', ''))}</code></td>"
                         f"<td>{esc(loc.get('line_range', ''))}</td>"
                         f"<td>{esc(loc.get('symbol_role', ''))}</td>"
                         f"<td>{'' if agg is None else esc(agg)}</td>"
                         f"<td>{esc(parts_txt)}</td></tr>")
            L.append("</tbody></table>")
        imp = d.get("implements") or {}
        L.append(sub("What it implements", level=4, anchor=f"{profile}-{aid}-implements"))
        L.append(scalar_list_html(v, [
            f"design: {imp.get('design_id')}" if imp.get("design_id") else
            "design: none in corpus (recorded as a coverage gap)",
            f"design level: {imp.get('design_level', 'unspecified')}",
            f"relationship: {imp.get('relationship', '')}",
        ], "implementation mapping"))
        reqs = d.get("realises_requirements") or []
        L.append(scalar_list_html(v, reqs or ["no requirement realised in corpus"],
                                  "requirements realised"))
        L.append(sub("Status and evidence", level=4, anchor=f"{profile}-{aid}-status"))
        L.append(scalar_list_html(v, [
            f"implementation_status: {d.get('implementation_status', 'unspecified')}",
            f"design gap reason: {imp.get('design_gap_reason', 'n/a')}",
            f"requirement gap reason: {d.get('requirement_gap_reason', 'n/a')}",
            f"evidence status: {d.get('evidence_status', 'unspecified')}",
        ], "implementation status"))
        L.append("</article>")

    recs = v.records(lambda d: d.get("artifact_type") == "design"
                     and d.get("design_level") != "architecture")
    if not recs:
        v.gap("absent-record-family", "detailed design",
              "The artifact index holds no design record with a detailed-design level in either "
              "profile.", "artifact index, design.design_level == detailed_design")
        L.append(f"<p>{v.gap_phrase('detailed design records')}</p>")
    for profile, aid, d in recs:
        L.append(f'<article class="card design-detailed" id="{v.anchor(profile, aid)}" '
                 f'data-artifact-type="design" data-profile="{esc(profile)}" '
                 f'data-revision="{esc(d.get("revision", ""))}">')
        v.rendered_artifact_ids.add((profile, aid))
        L += card_head(v, profile, aid, d, "Detailed design")
        design_summary(v, L, profile, aid, d)

        L.append(sub("Responsibilities", level=4, anchor=f"{profile}-{aid}-resp"))
        L += scalar_list_html(v, d.get("responsibilities"), "design responsibilities")

        L.append(sub("Decomposition", level=4, anchor=f"{profile}-{aid}-decomposition"))
        dec = d.get("decomposition") or []
        parents = sorted(
            qid for qid in v.ids_where(profile, lambda x: x.get("artifact_type") == "design")
            if any(isinstance(c, dict) and c.get("child_id") == aid
                   for c in (v.get(profile, qid).get("decomposition") or [])))
        if dec:
            rows = []
            for i, c in enumerate(dec):
                if isinstance(c, dict):
                    cid = c.get("child_id") or c.get("component") or c.get("name") or f"child-{i}"
                    rows.append([v.aref(profile, str(cid)) if v.anchor_exists(profile, str(cid))
                                 else f"<code>{esc(cid)}</code>",
                                 f"<code>{esc(c.get('relationship'))}</code>",
                                 esc(c.get("description") or c.get("rationale")
                                     or "not specified in corpus")])
                else:
                    rows.append([esc(c), "contains", "not specified in corpus"])
            L += table(["Child", "Relationship", "Corpus description"], rows)
        else:
            v.gap("absent-decomposition", f"{profile}/{aid}",
                  "The detailed design record declares no decomposition of its own. The static "
                  "structure shown below is therefore derived from the parent design that "
                  "declares this record as a child, from the record's own interfaces, and from its "
                  "implementation_mapping entries — not from a decomposition this record holds.",
                  f"{profile} artifact index: {aid} → decomposition")
            L.append(f"<p>{v.gap_phrase('decomposition of this record')}</p>")
        if parents:
            L.append(kv("Parent design(s) that declare this record as a child",
                        v.joined(v.aref(profile, q) for q in parents)))
        else:
            v.gap("absent-parent-decomposition", f"{profile}/{aid}",
                  "No design record in this profile declares this record as a decomposition child, "
                  "so the component's position in the architecture cannot be derived from the "
                  "corpus.",
                  f"{profile} artifact index: design.decomposition[].child_id")
            L.append(kv("Parent design(s)", v.gap_phrase("declaring this record as a child")))

        # ---- per-component static diagram
        ifs = d.get("interfaces") or []
        im = d.get("implementation_mapping") or []
        self_label = f"{short_id(aid)} {d.get('title') or aid}"
        if not (parents or dec or ifs or im):
            v.gap("absent-static-structure", f"{profile}/{aid}",
                  "The record holds no parent decomposition, no decomposition of its own, no "
                  "interfaces and no implementation_mapping, so no static structure can be derived "
                  f"for it.",
                  f"{profile} artifact index: {aid} → decomposition, interfaces, "
                  f"implementation_mapping")
            L.append(f"<p>{v.gap_phrase('static structure')}</p>")
        else:
            body = [f"  {mid(aid)}[{mlabel(self_label, 60)}]"]
            if parents:
                for q in parents:
                    qd = v.get(profile, q) or {}
                    body.append(f"  P_{mid(q)}[{mlabel(f'{short_id(q)} {qd.get("title") or q}', 56)}]")
                    body.append(f"  P_{mid(q)} -->|contains| {mid(aid)}")
            for i, c in enumerate(dec):
                if isinstance(c, dict):
                    cid = str(c.get("child_id") or c.get("component") or c.get("name") or f"c{i}")
                    cd = v.get(profile, cid) or {}
                    label = f"{short_id(cid)} {cd.get('title')}" if cd.get("title") else short_id(cid)
                    body.append(f"  C_{mid(cid)}[{mlabel(label, 52)}]")
                    body.append(f"  {mid(aid)} -->|{mv(c.get('relationship') or 'contains')}| "
                                f"C_{mid(cid)}")
                else:
                    body.append(f"  C{i}[{mlabel(c, 44)}]")
                    body.append(f"  {mid(aid)} -->|contains| C{i}")
            for i, itf in enumerate(ifs):
                if not isinstance(itf, dict):
                    continue
                iid = str(itf.get("interface_id") or f"interface-{i}")
                nsig = len(itf.get("signals") or [])
                idir = str(itf.get("direction") or "unspecified")
                body.append(f"  I_{mid(iid)}[{mlabel(f'{iid} ({idir}, {nsig} signal(s))', 56)}]")
                body.append(f"  {mid(aid)} -->|{mv(itf.get('direction') or 'interface')}| "
                            f"I_{mid(iid)}")
            for m in im:
                if not isinstance(m, dict):
                    continue
                sf = str(m.get("source_file") or "source")
                sym = m.get("symbol")
                leaf = f"{sf}::{sym}()" if sym else sf
                key = f"S_{mid(sf + str(sym))}"
                if key not in [x.split("]")[0] for x in body if x.strip().startswith(key)]:
                    body.append(f"  {key}[{mlabel(leaf, 60)}]")
                body.append(f"  {mid(aid)} -->|mapped to — {mv(m.get('status') or 'status')}| {key}")
            sources = (f"the parent design's decomposition; this record's own decomposition"
                       if dec else
                       "the parent design's decomposition (this record declares none of its own)")
            ifs_note = f"; this record's interfaces ({len(ifs)})" if ifs else ""
            maps_note = f"; this record's implementation_mapping ({len(im)} entries)" if im else ""
            L += diagram(
                v, f"design.static.{profile}.{short_id(aid)}", "flowchart TD",
                "Detailed design static viewpoint",
                f"Static structure of {aid}: the design(s) that declare it, the children it "
                f"declares, the interfaces it exposes and the source elements it is mapped to.",
                f"{profile} artifact index: design.decomposition[].child_id (parent and own), "
                f"{aid} → interfaces[], implementation_mapping[].source_file/symbol/status"
                + ("" if dec else "; this record's own decomposition is empty and is reported as a "
                                "gap in section 12"),
                ["flowchart TD"] + body)
            L.append(note(
                f"Node and edge provenance: the containing edge comes from {sources}; the interface "
                f"edges come from{ifs_note or ' (this record declares no interfaces)'}; the source "
                f"edges come from{maps_note or ' (this record declares no implementation mapping)'}.",
                "meta"))

        L.append(sub("Interfaces", level=4, anchor=f"{profile}-{aid}-interfaces"))
        L += interface_table(v, d)

        L.append(sub("Constraints", level=4, anchor=f"{profile}-{aid}-constraints"))
        L += scalar_list_html(v, d.get("constraints"), "constraints")

        L.append(sub("Budgets", level=4, anchor=f"{profile}-{aid}-budgets"))
        budgets = {k: d[k] for k in ("budgets", "electrical_budgets", "timing_budget",
                                     "fault_indications") if d.get(k)}
        if budgets:
            rows = []
            for k in sorted(budgets):
                val = budgets[k]
                if isinstance(val, dict):
                    rows.append([f"<code>{esc(k)}</code>",
                                 esc("; ".join(f"{kk} = {esc(vv)}" for kk, vv in sorted(val.items())))])
                else:
                    rows.append([f"<code>{esc(k)}</code>", esc(val)])
            L += table(["Budget field", "Corpus value"], rows)
        else:
            L.append(f"<p>{v.gap_phrase('budgets')}</p>")

        L.append(sub("Failure Response", level=4, anchor=f"{profile}-{aid}-failure-response"))
        fr = d.get("failure_response") or []
        if fr:
            L += table(["Failure mode", "Detection", "Reaction"], [
                [esc(f.get("failure_mode")), esc(f.get("detection")), esc(f.get("reaction"))]
                if isinstance(f, dict) else [esc(f), "not specified in corpus",
                                             "not specified in corpus"] for f in fr])
        else:
            L.append(f"<p>{v.gap_phrase('failure response')}</p>")

        L.append(sub("Static Diagram", level=4, anchor=f"{profile}-{aid}-static-diagram"))
        L.append(note(
            "The static diagram of this design is the decomposition diagram emitted above, derived "
            "from the record's own <code>decomposition</code> field. It is not repeated here.",
            "meta"))

        L.append(sub("Dynamic Diagram", level=4, anchor=f"{profile}-{aid}-dynamic-diagram"))
        bm = d.get("behavior_model")
        if isinstance(bm, dict) and bm.get("states"):
            states = [s for s in bm.get("states", []) if isinstance(s, str)]
            trans = [t for t in (bm.get("transitions") or []) if isinstance(t, dict)]
            body = [f"  [*] --> {mid(states[0])}"]
            for t in trans:
                f_, t_ = t.get("from"), t.get("to")
                if not f_ or not t_:
                    continue
                trig = t.get("trigger")
                suffix = f" : {mv(trig, 40)}" if trig else ""
                body.append(f"  {mid(f_)} --> {mid(t_)}{suffix}")
            for s in states:
                body.append(f"  {mid(s)}")
            L += diagram(
                v, f"design.dynamic.{profile}.{short_id(aid)}", "stateDiagram-v2",
                "Detailed design dynamic viewpoint",
                f"Behaviour model of {aid} as a state machine, containing exactly the states and "
                f"transitions the record declares ({len(states)} states, {len(trans)} transitions).",
                f"{profile} artifact index: {aid} → behavior_model.states[], "
                f"behavior_model.transitions[]",
                ["stateDiagram-v2"] + body)
        else:
            v.gap("absent-behaviour-model", f"{profile}/{aid}",
                  f"The detailed design record holds no behavior_model with states, so no dynamic "
                  f"design diagram can be derived for it.",
                  f"{profile} artifact index: {aid} → behavior_model")
            L.append(f"<p>{v.gap_phrase('behaviour model')}</p>")

        L.append(sub("Implementation Requirements", level=4, anchor=f"{profile}-{aid}-implreq"))
        cons, bud = d.get("constraints") or [], bool(d.get("budgets") or d.get("timing_budget")
                                                    or d.get("electrical_budgets"))
        if cons or bud:
            L.append(note(
                "Implementation requirements are the record's own constraint and budget fields, "
                "restated here as the obligations they place on the implementation. No additional "
                "requirement is introduced.", "meta"))
            L += ul([f"<code>{esc(c)}</code> (from this record's <code>constraints</code>)"
                     for c in cons])
            if bud:
                for k in ("budgets", "electrical_budgets", "timing_budget"):
                    if d.get(k):
                        L.append(kv(esc(k.replace("_", " ")), esc(d[k])))
        else:
            L.append(f"<p>{v.gap_phrase('implementation requirements beyond the mapping')}</p>")

        L.append(kv("Assumption references", v.asm_ref_html(d.get("assumption_refs"))))
        L.append(kv("Source references", v.src_ref_html(d.get("source_refs"))))
        L.append(kv("Standards mappings", standards_table(d, v)))
        L.append(kv("Record limitations", limitation_block(d, v)))
        L.append("</article>")
    return L


# ---------------------------------------------------------------- 7. implementation mapping

def sec_07(v):
    L = []
    L.append(note(
        "Implementation mapping: for every design record, the source file, symbol and status the "
        "record itself declares; and for every software requirement, the hyperlinked chain from the "
        "requirement through its design and its mapped source to the test measures that verify it. "
        "Where a design declares no mapping, that is stated as a gap rather than filled from the "
        "repository.", "callout"))

    L.append(sub("Implementation Mapping", anchor="implementation-mapping"))
    dsns = v.records(lambda d: d.get("artifact_type") == "design")
    for profile, aid, d in dsns:
        L.append(sub(f"{v.aref(profile, aid)} — {esc(d.get('title'))}", level=4,
                     anchor=f"{profile}-{aid}-mapping"))
        im = d.get("implementation_mapping") or []
        if im:
            L += table(["Source file", "Symbol", "Status", "Notes"], [
                [f"<code>{esc(m.get('source_file'))}</code>", f"<code>{esc(m.get('symbol'))}</code>",
                 f"<code>{esc(m.get('status'))}</code>",
                 esc(m.get("note") or m.get("rationale") or "not specified in corpus")]
                if isinstance(m, dict) else [esc(m), "not specified in corpus",
                                             "not specified in corpus", "not specified in corpus"]
                for m in im])
        else:
            v.gap("absent-implementation-mapping", f"{profile}/{aid}",
                  "The design record declares no implementation_mapping entry, so the corpus holds "
                  "no source file, symbol or status for this design.",
                  f"{profile} artifact index: {aid} → implementation_mapping")
            L.append(f"<p>{v.gap_phrase('implementation mapping')}</p>")

    L.append(sub("Requirement to Design to Source to Test Chains", anchor="chains"))
    swrs = v.records(lambda d: d.get("artifact_type") == "requirement"
                     and is_software_requirement(d))
    if not swrs:
        v.gap("absent-record-family", "requirement-to-code chains",
              "The artifact index holds no software requirement, so no requirement-to-code chain "
              "can be derived.", "artifact index, requirement, software domain")
    for profile, aid, d in swrs:
        L.append(sub(v.href(aid), level=4, anchor=f"chain-{profile}-{aid}"))
        designs = sorted({l["source_id"] for l in v.links_where(profile=profile, relation="implements",
                                                               tgt=aid)})
        steps = [f"<strong>1. Software requirement</strong>: {v.aref(profile, aid)}"]
        if not designs:
            v.gap("unlinked-design", f"{profile}/{aid}",
                  "No design record implements this software requirement through the link registry, "
                  "so the chain stops at the requirement.",
                  f"{profile} link registry, relation_type == implements, target_id == {aid}")
        for i, dsn in enumerate(designs, start=2):
            dd = v.get(profile, dsn) or {}
            srcs = sorted({m.get("source_file") for m in (dd.get("implementation_mapping") or [])
                           if isinstance(m, dict) and m.get("source_file")})
            syms = sorted({m.get("symbol") for m in (dd.get("implementation_mapping") or [])
                           if isinstance(m, dict) and m.get("symbol")})
            steps.append(
                f"<strong>{i}. Design</strong>: {v.aref(profile, dsn)} → source file(s): "
                + (", ".join(f"<code>{esc(s)}</code>" for s in srcs) or "none declared in corpus")
                + "; symbol(s): "
                + (", ".join(f"<code>{esc(s)}</code>" for s in syms) or "none declared in corpus"))
            if not srcs:
                v.gap("absent-implementation-mapping", f"{profile}/{dsn}",
                      f"The design that implements {aid} declares no implementation_mapping entry, "
                      f"so the chain reaches the design but no source code.",
                      f"{profile} artifact index: {dsn} → implementation_mapping")
        cov = v.coverage(profile, aid)
        n = len(designs) + 2
        if cov["tests"]:
            steps.append(f"<strong>{n}. Verifying test measure(s)</strong>: "
                         + ", ".join(v.aref(profile, t) for t in cov["tests"])
                         + f" (coverage status <code>{esc(cov['status'])}</code>)")
            exes = []
            for t in cov["tests"]:
                for e in v.ids_where(profile, lambda d: d.get("artifact_type") == "execution"):
                    if _measure_of(v, profile, e) == t:
                        exes.append(e)
            if exes:
                n += 1
                steps.append(f"<strong>{n}. Execution record(s)</strong>: "
                             + ", ".join(v.aref(profile, e) for e in sorted(exes)))
        else:
            v.gap("uncovered-requirement", f"{profile}/{aid}",
                  "No test measure verifies or validates this requirement, and no test measure names "
                  "it in referenced_requirements, so the chain ends with an explicit uncovered "
                  "status.", f"{profile} link registry and test_measure.referenced_requirements")
            steps.append(f"<strong>{n}. Verifying test measure(s)</strong>: "
                         f"<strong>UNCOVERED</strong> — no test measure in the corpus verifies or "
                         f"names this requirement (see the coverage matrix in section 11).")
        L.append("<ol class=\"chain\">" + "".join(f"<li>{s}</li>" for s in steps) + "</ol>")

    L.append(sub("Change Records", anchor="change-records"))
    changes = v.records(lambda d: d.get("artifact_type") == "change")
    if not changes:
        v.gap("absent-record-family", "change records",
              "The artifact index holds no change record, so no change-lifecycle evidence is "
              "available for the implementation mapping.",
              "artifact index, artifact_type == change")
        L.append(f"<p>{v.gap_phrase('change records')}</p>")
    for profile, aid, d in changes:
        L.append(card_open(v, profile, aid, d, "change"))
        L += card_head(v, profile, aid, d, "Change record")
        L.append(kv("Change type", f"<code>{esc(d.get('change_type'))}</code>"))
        L.append(kv("Change type note", esc(d.get("change_type_note"))))
        L.append(kv("Trigger", esc(d.get("trigger"))))
        L.append(kv("Implementation target", esc(d.get("implementation_target"))))
        L.append(kv("Implementation status", esc(d.get("implementation_status"))))
        L.append(kv("Implementation note", esc(d.get("implementation_note"))))
        L.append(kv("Decision", esc(d.get("decision"))))
        L.append(kv("Synthetic decision", esc(d.get("synthetic_decision"))))
        L.append(kv("Decision disposition scope", esc(d.get("decision_disposition_scope"))))
        L.append(kv("Change control", esc(d.get("change_control"))))
        L.append(kv("Post-change baseline", esc(d.get("post_change_baseline"))))
        L.append(kv("Record kind", esc(d.get("record_kind"))))
        L.append(kv("Record purpose", esc(d.get("record_purpose"))))
        L.append(kv("Relationship to scenario fixture", esc(d.get("relationship_to_scenario_fixture"))))
        L.append(kv("Corpus boundaries", esc(d.get("corpus_boundaries"))))
        L.append(kv("Cross-profile references avoided", esc(d.get("cross_profile_references_avoided"))))
        for key, label in (("impact_analysis", "Impact analysis"),
                           ("new_revisions", "New revisions"),
                           ("suspect_links", "Suspect links"),
                           ("suspect_link_rationale", "Suspect link rationale"),
                           ("suspect_link_registry_state", "Suspect link registry state"),
                           ("required_updates", "Required updates"),
                           ("reverification_criterion", "Reverification criterion"),
                           ("reverification_selection", "Reverification selection"),
                           ("evidence_invalidation", "Evidence invalidation"),
                           ("assumptions_invalidated", "Assumptions invalidated"),
                           ("assumptions_reconfirmed", "Assumptions reconfirmed"),
                           ("new_links_required", "New links required"),
                           ("parameter_registry_entries_affected",
                            "Parameter registry entries affected"),
                           ("variant_impact", "Variant impact"),
                           ("re_review_scope", "Re-review scope"),
                           ("hardware_source_anchors_re_reviewed",
                            "Hardware source anchors re-reviewed"),
                           ("software_source_anchors_re_reviewed",
                            "Software source anchors re-reviewed"),
                           ("interaction_with_other_changes", "Interaction with other changes"),
                           ("not_included_and_why", "Not included, and why")):
            if d.get(key):
                L.append(kv(label, esc(d[key])))
        L.append(kv("Assumption references", v.asm_ref_html(d.get("assumption_refs"))))
        L.append(kv("Source references", v.src_ref_html(d.get("source_refs"))))
        L.append(kv("Standards mappings", standards_table(d, v)))
        L.append(kv("Record limitations", limitation_block(d, v)))
        L.append("</article>")
    return L


# ---------------------------------------------------------------- 8. software integration

def sec_08(v):
    L = []
    L.append(note(
        "Software integration: which software components the corpus says are integrated, what "
        "integration evidence exists, and — stated explicitly — what integration evidence does not "
        "exist. The gaps in 8.3 are computed from the corpus, not asserted; a missing integration "
        "record is reported as missing.", "callout"))

    L.append(sub("Integrated Components", anchor="integrated-components"))
    rows = []
    for profile, aid, d in v.records(lambda d: d.get("artifact_type") == "design"):
        im = d.get("implementation_mapping") or []
        implemented = sorted({l["source_id"] for l in v.links_where(profile=profile, relation="verifies",
                                                                  tgt=aid)})
        rows.append([
            v.aref(profile, aid),
            f"<code>{esc(d.get('design_level'))}</code>",
            esc(str(len(im))),
            esc(", ".join(sorted({m.get("source_file") for m in im if isinstance(m, dict)})) or "—"),
            esc(", ".join(v.aref(profile, t) for t in implemented) or "—"),
        ])
    if rows:
        L += table(["Design", "Level", "Mapped source entries", "Source files", "Verified by"], rows,
                   css_class="wide")
    else:
        v.gap("absent-record-family", "integrated components",
              "The artifact index holds no design record, so no integrated component can be listed.",
              "artifact index, artifact_type == design")
        L.append(f"<p>{v.gap_phrase('integrated components')}</p>")
    L.append(note(
        "An integrated component is listed here only when a design record exists and declares an "
        "<code>implementation_mapping</code> entry. A design that exists without a mapping is shown "
        "with a mapped-entry count of zero and appears in the gaps below; it is not presented as "
        "integrated.", "meta"))

    L.append(sub("Integration Evidence", anchor="integration-evidence"))
    int_tms = v.records(lambda d: d.get("artifact_type") == "test_measure"
                        and d.get("test_type") == "integration")
    if not int_tms:
        v.gap("absent-verification-level", "integration test specification",
              "No test measure in the corpus declares test_type == integration, so the corpus holds "
              "no integration test specification.",
              "artifact index, test_measure.test_type == integration")
        L.append(f"<p>{v.gap_phrase('integration test specifications')}</p>")
    for profile, aid, d in int_tms:
        L += test_measure_block(v, profile, aid, d, level=4)
    L.append(sub("Integration executions", level=4, anchor="integration-executions"))
    exes = v.records(lambda d: d.get("artifact_type") == "execution"
                     and _measure_of(v, d.get("profile", ""), d.get("id")) in
                     {aid for _p, aid, _d in int_tms})
    if not exes:
        v.gap("absent-integration-evidence", "integration execution",
              "No execution record in the corpus executes an integration-typed test measure, so the "
              "corpus holds no integration run result.",
              "artifact index, execution.test_measure_id")
        L.append(f"<p>{v.gap_phrase('integration execution results')}</p>")
    for profile, aid, d in exes:
        L += execution_block(v, profile, aid, d, level=4)
    L.append(note(
        "Execution records are labelled with their own <code>execution_kind</code> and "
        "<code>outcome</code>. An <code>actual_host_run</code> is a run on a real host of the "
        "pinned sources; a <code>synthetic_fixture</code> is a fixture built for the fictional "
        "project; <code>none</code> with outcome <code>blocked</code> means no run was performed. "
        "None of the three is product verification credit, and every execution record carries "
        "<code>product_verification_credit: false</code>.", "callout"))

    L.append(sub("Integration Gaps", anchor="integration-gaps"))
    L += integration_gap_table(v)
    return L


def integration_gap_table(v):
    rows = []
    for profile, aid, d in v.records(lambda d: d.get("artifact_type") == "design"):
        im = d.get("implementation_mapping") or []
        if not im:
            rows.append([v.aref(profile, aid), "no implementation_mapping entry",
                         f"The design record declares no mapped source file or symbol.",
                         f"{profile} artifact index: {aid} → implementation_mapping"])
        statuses = sorted({str(m.get("status")) for m in im if isinstance(m, dict)})
        for st in statuses:
            if st.lower() in ("not_in_source", "proposed", "not_implemented"):
                rows.append([v.aref(profile, aid), f"mapping status <code>{esc(st)}</code>",
                             "The corpus itself records that this mapped element is not present in "
                             "the source tree.",
                             f"{profile} artifact index: {aid} → implementation_mapping[].status"])
    for profile in PROFILES:
        intm = v.ids_where(profile, lambda d: d.get("artifact_type") == "test_measure"
                           and d.get("test_type") == "integration")
        if not intm:
            rows.append(["—", f"no integration-typed test measure ({profile})",
                         "The corpus holds no integration test specification for this profile.",
                         "artifact index, test_measure.test_type == integration"])
    if not rows:
        return [f"<p>{v.gap_phrase('integration gaps')}</p>"]
    return table(["Subject", "Gap", "What the corpus does and does not hold",
                  "Corpus field consulted"], rows, css_class="gaps")


# ---------------------------------------------------------------- 9/10. verification

def test_measure_block(v, profile, aid, d, level=4):
    L = [card_open(v, profile, aid, d, "test-measure")]
    L.append(f"<h{level}>{v.aref(profile, aid)} — {esc(d.get('title') or aid)}</h{level}>")
    L.append(guard_html(guard_tuple(d)))
    L.append(kv("Test type", f"<code>{esc(d.get('test_type'))}</code>"))
    L.append(kv("Oracle basis", f"<code>{esc(d.get('oracle_basis'))}</code>"))
    if d.get("oracle_detail"):
        L.append(kv("Oracle detail", esc(d["oracle_detail"])))
    L.append(kv("Objective", esc(d.get("objective"))))
    L.append(kv("Referenced requirements",
                v.joined(v.ref_list(profile, d.get("referenced_requirements", [])))))
    L.append(kv("Referenced designs",
                v.joined(v.ref_list(profile, d.get("referenced_designs", [])))))
    if d.get("validates_safety_goals"):
        L.append(kv("Validates safety goals",
                    v.joined(v.ref_list(profile, d["validates_safety_goals"]))))
    if d.get("validates_stakeholder_needs"):
        L.append(kv("Validates stakeholder needs",
                    v.joined(v.ref_list(profile, d["validates_stakeholder_needs"]))))
    if d.get("validates_use_cases"):
        L.append(kv("Validates use cases",
                    v.joined(v.ref_list(profile, d["validates_use_cases"]))))
    L.append(sub("Preconditions", level=level + 1, anchor=f"{profile}-{aid}-pre"))
    L += scalar_list_html(v, d.get("preconditions"), "test preconditions")
    L.append(sub("Environment", level=level + 1, anchor=f"{profile}-{aid}-env"))
    env = d.get("environment") or {}
    if isinstance(env, dict) and env:
        tv = env.get("tool_versions") or {}
        rows = [[f"<code>{esc(k)}</code>", esc(env.get(k))]
                for k in ("hardware", "software", "configuration") if env.get(k)]
        if env.get("tools"):
            rows.append(["tools", esc(", ".join(env.get("tools")))])
        if tv:
            rows.append(["tool_versions", esc("; ".join(f"{k} {vv}" for k, vv in sorted(tv.items())))])
        L += table(["Environment field", "Corpus value"], rows)
    else:
        L.append(f"<p>{v.gap_phrase('test environment')}</p>")
    L.append(sub("Stimuli", level=level + 1, anchor=f"{profile}-{aid}-stimuli"))
    stim = d.get("stimuli") or []
    if stim:
        L += table(["Signal", "Value", "Timing"], [
            [esc(s.get("signal")), esc(s.get("value")), esc(s.get("timing"))]
            if isinstance(s, dict) else [esc(s), "—", "—"] for s in stim])
    else:
        L.append(f"<p>{v.gap_phrase('stimuli')}</p>")
    L.append(sub("Tolerances and timing", level=level + 1, anchor=f"{profile}-{aid}-tol"))
    bits = []
    if d.get("tolerances"):
        bits.append(("tolerances", d["tolerances"]))
    if d.get("timing"):
        bits.append(("timing", d["timing"]))
    if bits:
        L += table(["Field", "Corpus value"], [[f"<code>{esc(k)}</code>", esc(val)] for k, val in bits])
    else:
        L.append(f"<p>{v.gap_phrase('tolerances and timing')}</p>")
    if d.get("execution_state"):
        L.append(kv("Execution state", esc(d["execution_state"])))
    L.append(kv("Assumption references", v.asm_ref_html(d.get("assumption_refs"))))
    L.append(kv("Source references", v.src_ref_html(d.get("source_refs"))))
    L.append(kv("Standards mappings", standards_table(d, v)))
    L.append(kv("Record limitations", limitation_block(d, v)))
    L.append("</article>")
    return L


def execution_block(v, profile, aid, d, level=4):
    L = [card_open(v, profile, aid, d, "execution")]
    L.append(f"<h{level}>{v.aref(profile, aid)} — {esc(d.get('title') or aid)}</h{level}>")
    L.append(guard_html(guard_tuple(d)))
    ek = d.get("execution_kind")
    L.append(kv("Execution kind", f"<code>{esc(ek)}</code>"))
    L.append(kv("Meaning of this execution kind", esc(execution_kind_meaning(ek))))
    L.append(kv("Outcome", f"<strong>{esc(str(d.get('outcome')).upper())}</strong>"))
    if d.get("aggregate_outcome"):
        L.append(kv("Aggregate outcome", esc(d["aggregate_outcome"])))
    tmid = d.get("test_measure_id")
    L.append(kv("Test measure executed",
                v.href(tmid.split("..")[0].strip()) if isinstance(tmid, str) else "—"
                + (f" (corpus field records a range: {esc(tmid)})" if isinstance(tmid, str) else "")))
    L.append(kv("Test measure revision", esc(d.get("test_measure_revision"))))
    if d.get("regression_check"):
        L.append(kv("Regression check", esc(d["regression_check"])))
    L.append(sub("Environment", level=level + 1, anchor=f"{profile}-{aid}-env"))
    env = d.get("environment") or {}
    if isinstance(env, dict) and env:
        tv = env.get("tool_versions") or {}
        rows = [[f"<code>{esc(k)}</code>", esc(env.get(k))]
                for k in ("hardware", "software", "configuration", "platform", "os") if env.get(k)]
        if env.get("tools"):
            rows.append(["tools", esc(", ".join(env.get("tools")))])
        if tv:
            rows.append(["tool_versions", esc("; ".join(f"{k} {vv}" for k, vv in sorted(tv.items())))])
        if d.get("timestamps"):
            rows.append(["timestamps", esc(d["timestamps"])])
        L += table(["Environment field", "Corpus value"], rows)
    else:
        L.append(f"<p>{v.gap_phrase('execution environment')}</p>")
    if d.get("measured_results"):
        L.append(sub("Measured results", level=level + 1, anchor=f"{profile}-{aid}-measured"))
        mr = d["measured_results"]
        if isinstance(mr, list):
            L += table(["Result", "Value"], [
                [esc(r.get("signal") or r.get("name")), esc(r.get("value") or r.get("measured"))]
                if isinstance(r, dict) else ["—", esc(r)] for r in mr])
        else:
            L.append(kv("Measured results", esc(mr)))
    if d.get("assertions"):
        L.append(kv("Assertions", esc(d["assertions"])))
    if d.get("anomalies"):
        L.append(sub("Anomalies", level=level + 1, anchor=f"{profile}-{aid}-anomalies"))
        an = d["anomalies"]
        if isinstance(an, list):
            L += table(["Anomaly", "Description"], [
                [esc(a.get("id") or a.get("kind")), esc(a.get("description"))]
                if isinstance(a, dict) else ["—", esc(a)] for a in an])
        else:
            L.append(kv("Anomalies", esc(an)))
    if d.get("verbatim_unity_failures"):
        L.append(kv("Verbatim recorded failures", esc(d["verbatim_unity_failures"])))
    if d.get("blocked_reason"):
        L.append(kv("Blocked reason", esc(d["blocked_reason"])))
    if d.get("what_would_unblock_it"):
        L.append(kv("What would unblock it", esc(d["what_would_unblock_it"])))
    if d.get("unblocking_conditions"):
        L.append(kv("Unblocking conditions", esc(d["unblocking_conditions"])))
    if d.get("evidence_refs") or d.get("evidence_files"):
        L.append(kv("Evidence references", esc(", ".join(
            [str(x) for x in (d.get("evidence_refs") or [])]
            + [str(x) for x in (d.get("evidence_files") or [])]) or "—")))
    L.append(kv("Assumption references", v.asm_ref_html(d.get("assumption_refs"))))
    L.append(kv("Source references", v.src_ref_html(d.get("source_refs"))))
    L.append(kv("Standards mappings", standards_table(d, v)))
    L.append(kv("Record limitations", limitation_block(d, v)))
    L.append("</article>")
    return L


def execution_kind_meaning(kind):
    return {
        "actual_host_run": "A run performed on a real host against the pinned foxBMS sources. It is "
                           "a real measurement of the real code on the development machine, and it "
                           "is not a target-hardware or vehicle result.",
        "synthetic_fixture": "A fixture built for the fictional synthetic_reference project. It is "
                             "not a measurement of the real foxBMS product.",
        "none": "No run was performed. The record exists to state that, and the outcome is blocked.",
    }.get(str(kind), f"Execution kind `{kind}` is recorded on this record; its meaning is "
                     f"{GAP_PHRASE} in the corpus, so no gloss is invented here.")


def verification_section(v, sec_id, title, levels, intro, close=True):
    """Render one verification section: specification, cases, execution report.

    `levels` is a list of (level label, test_type tuple, execution-kind tuple or
    None). Measures are selected by their own declared test_type; the
    execution-kind tuple is a secondary selection for executions whose measure
    is absent, which is how a target-HIL run would be surfaced if the corpus
    ever held one. A level with no measure in the corpus is declared as a gap,
    naming the exact test_type values searched.
    """
    L = []
    L.append(note(intro, "callout"))
    measures = v.records(lambda d: d.get("artifact_type") == "test_measure")
    executions = v.records(lambda d: d.get("artifact_type") == "execution")
    vocabulary = sorted({str(m[2].get("test_type")) for m in measures})

    for label, test_types, exec_kinds in levels:
        anchor = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")
        L.append(sub(label, anchor=anchor))
        sel = [r for r in measures if r[2].get("test_type") in test_types]
        L.append(sub("Test Specification", level=4, anchor=f"{anchor}-spec"))
        if not sel:
            v.gap("absent-verification-level", f"{label} ({sec_id})",
                  f"No test measure in the corpus declares test_type in "
                  f"<code>{esc(', '.join(test_types))}</code>. The corpus test_type vocabulary is "
                  f"<code>{esc(', '.join(vocabulary))}</code>; the value(s) this level needs are "
                  f"absent from it, so no specification can be shown.",
                  "artifact index, test_measure.test_type")
            L.append(f"<p>{v.gap_phrase(f'test specification for the {label.lower()} level')}</p>")
        for profile, aid, d in sel:
            L += test_measure_block(v, profile, aid, d, level=5)
        L.append(sub("Test Cases", level=4, anchor=f"{anchor}-cases"))
        total, with_steps = 0, 0
        for profile, aid, d in sel:
            steps = d.get("steps") or []
            total += len(steps) if steps else 0
            if steps:
                with_steps += 1
            L.append(sub(f"Test cases of {v.aref(profile, aid)}", level=5,
                         anchor=f"{anchor}-cases-{profile}-{aid}"))
            if steps:
                L += table(["Step", "Action", "Expected result"], [
                    [esc(s.get("step")), esc(s.get("action")), esc(s.get("expected"))]
                    if isinstance(s, dict) else [esc(s), "not specified in corpus",
                                                 "not specified in corpus"] for s in steps])
                eo = d.get("expected_outcomes") or []
                if eo:
                    L += table(["Signal", "Expected value", "Tolerance", "Unit"], [
                        [esc(e.get("signal")), esc(e.get("expected_value")),
                         esc(e.get("tolerance")), esc(e.get("unit"))]
                        if isinstance(e, dict) else [esc(e), "—", "—", "—"] for e in eo])
            else:
                v.gap("absent-test-steps", f"{profile}/{aid}",
                      "The test measure records no steps, so it contributes no test case.",
                      f"{profile} artifact index: {aid} → steps")
                L.append(f"<p>{v.gap_phrase('test steps')}</p>")
        L.append(kv("Test cases in this level",
                    esc(f"{total} step-level case(s) across {with_steps} of {len(sel)} measure(s)")))
        L.append(sub("Execution Report", level=4, anchor=f"{anchor}-executions"))
        ex_ids = {aid for _p, aid, _d in sel}
        exsel = [r for r in executions if _measure_of(v, r[0], r[1]) in ex_ids]
        if not exsel and exec_kinds:
            exsel = [r for r in executions
                     if str(r[2].get("execution_kind")) in exec_kinds]
        if not exsel:
            v.gap("absent-execution-evidence", f"{label} ({sec_id})",
                  f"No execution record in the corpus executes a test measure classified into the "
                  f"{label} level, so the corpus holds no run result for this level.",
                  "artifact index, execution.test_measure_id")
            L.append(f"<p>{v.gap_phrase(f'execution report for the {label.lower()} level')}</p>")
        for profile, aid, d in exsel:
            L += execution_block(v, profile, aid, d, level=5)
        L.append(execution_kind_summary(v, sec_id, label, sel, exsel))
    return L


def execution_kind_summary(v, sec_id, label, measures, executions):
    rows = []
    by_kind = {}
    for profile, aid, d in executions:
        by_kind.setdefault(str(d.get("execution_kind")), []).append((profile, aid, d))
    for kind in sorted(by_kind):
        recs = sorted(by_kind[kind])
        outcomes = {}
        for _p, _a, d in recs:
            outcomes[str(d.get("outcome"))] = outcomes.get(str(d.get("outcome")), 0) + 1
        rows.append([
            f"<code>{esc(kind)}</code>",
            esc(execution_kind_meaning(kind)),
            esc(str(len(recs))),
            esc("; ".join(f"{k}: {n}" for k, n in sorted(outcomes.items()))),
        ])
    L = [sub("Execution-kind breakdown for this level", level=4,
             anchor=re.sub(r"[^a-z0-9]+", "-", (sec_id + "-" + label).lower()).strip("-") + "-kinds")]
    if not rows:
        L.append(f"<p>{v.gap_phrase('executions at this level')}</p>")
        return L
    L += table(["Execution kind", "What the corpus means by it", "Records", "Recorded outcomes"],
               rows, css_class="wide")
    return L


def sec_09(v):
    return verification_section(
        v, "sec-09-system-verification", dict(SECTIONS)["sec-09-system-verification"],
        [("System Testing", ("system",), None),
         ("Validation Testing", ("validation",), None),
         ("Qualification Testing", ("qualification",), None)],
        "System verification: the test specifications, test cases and execution reports whose test "
        "type the corpus places at system level. The placement rule is stated rather than "
        f"assumed: a measure is placed here when its own <code>test_type</code> is one of "
        f"{esc(', '.join(SYSTEM_TEST_TYPES))}. Every other test type appears in section 10. A level "
        f"the corpus does not hold is reported as <span class=\"phrase-ref\">{GAP_PHRASE}</span>.")


def sec_10(v):
    L = verification_section(
        v, "sec-10-software-verification", dict(SECTIONS)["sec-10-software-verification"],
        [("Unit Testing", ("unit",), None),
         ("Component Testing", ("component",), None),
         ("Integration Testing", ("integration",), None),
         ("HIL Testing", ("hil",), HIL_LIKE_EXECUTION_KINDS),
         ("Fault Injection and Robustness Testing", ("fault_injection", "robustness"), None)],
        "Software verification by level. A measure is placed by its own <code>test_type</code>; a "
        "measure whose type is <code>fault_injection</code> or <code>robustness</code> is grouped "
        "here as fault-injection and robustness testing, and its measures are selected by test type "
        "rather than by execution kind so the selection stays data-derived. "
        "<code>actual_host_run</code> and <code>synthetic_fixture</code> are distinguished in every "
        "execution block and in the per-level breakdown; neither is product verification credit.",
        close=False)
    L.append(sub("Static-Analysis Deviance Evidence", anchor="static-analysis-deviance"))
    devs = v.records(lambda d: d.get("artifact_type") == "deviation")
    if not devs:
        v.gap("absent-record-family", "static-analysis deviance",
              "The artifact index holds no deviation record, so the corpus holds no coding-guideline "
              "deviance evidence.", "artifact index, artifact_type == deviation")
        L.append(f"<p>{v.gap_phrase('static-analysis deviance records')}</p>")
    rows = []
    for profile, aid, d in devs:
        rows.append([v.aref(profile, aid), esc(d.get("rule_reference")),
                     f"<code>{esc(d.get('rule_category'))}</code>",
                     f"<code>{esc(d.get('suppression_form'))}</code>",
                     f"<code>{esc(d.get('affected_lines'))}</code>",
                     f"<code>{esc(d.get('affected_file'))}</code>",
                     esc(d.get("affected_symbol")),
                     f"<code>{esc(d.get('lifecycle_status'))}</code>"])
    if rows:
        L += table(["Record", "Rule reference", "Category", "Suppression form", "Affected lines",
                    "File", "Symbol", "Lifecycle status"], rows, css_class="wide")
    L.append(note(
        "A deviation record documents an observed, in-source, justified exception to a coding "
        "guideline in the pinned implementation. It is not a test, not a test result and not a "
        "coverage claim, and it is not evidence that any guideline was met. The per-record guard "
        "lines above are authoritative for its approval status.", "callout"))
    for profile, aid, d in devs:
        L.append(card_open(v, profile, aid, d, "deviation"))
        L.append(f"<h4>{v.aref(profile, aid)} — {esc(d.get('title') or aid)}</h4>")
        L.append(guard_html(guard_tuple(d)))
        for key, label in (("guideline_id", "Guideline"), ("rule_reference", "Rule reference"),
                           ("rule_category", "Rule category"),
                           ("suppression_form", "Suppression form"),
                           ("suppression_scope", "Suppression scope"),
                           ("deviation_type", "Deviation type"),
                           ("deviation_rationale", "Deviation rationale"),
                           ("reanalysis_justification", "Reanalysis justification"),
                           ("normative_verification", "Normative verification"),
                           ("review_disposition", "Review disposition"),
                           ("review_disposition_note", "Review disposition note"),
                           ("impact_notes", "Impact notes"),
                           ("project_process_evidence", "Project process evidence"),
                           ("design_traceability", "Design traceability"),
                           ("tool_reference", "Tool reference"),
                           ("corpus_scope", "Corpus scope"),
                           ("evidence_quote", "Evidence quote"),
                           ("affected_file", "Affected file"),
                           ("affected_lines", "Affected lines"),
                           ("affected_symbol", "Affected symbol"),
                           ("deviations", "Deviation list")):
            if d.get(key):
                L.append(kv(label, esc(d[key])))
        L.append(kv("Assumption references", v.asm_ref_html(d.get("assumption_refs"))))
        L.append(kv("Source references", v.src_ref_html(d.get("source_refs"))))
        L.append(kv("Standards mappings", standards_table(d, v)))
        L.append(kv("Record limitations", limitation_block(d, v)))
        L.append("</article>")
    return L


# ---------------------------------------------------------------- 11. traceability

def sec_11(v):
    L = []

    L.append(sub("Link Registry", anchor="link-registry"))
    L.append(note(
        f"Every link in both per-profile link registries: {len(v.links)} entries, one row each, "
        f"with the link's own rationale, provenance, review state and change-suspect status. The "
        f"row anchor is <code>lnk-&lt;profile&gt;-&lt;link id&gt;</code>, so any link cited "
        f"elsewhere in this document resolves here. The same identifier in the two profiles is two "
        f"different links by corpus design and is listed twice.", "callout"))
    rows = []
    for l in v.links:
        profile = l.get("_profile")
        rows.append([
            f'<a id="lnk-{esc(profile)}-{esc(l.get("link_id"))}" href="#lnk-{esc(profile)}-{esc(l.get("link_id"))}">'
            f"<code>{esc(l.get('link_id'))}</code></a>",
            f"<code>{esc(profile)}</code>",
            v.aref(profile, l.get("source_id")) if v.anchor_exists(profile, l.get("source_id"))
            else f"<code>{esc(l.get('source_id'))}</code>",
            f"<code>{esc(l.get('relation_type'))}</code>",
            v.aref(profile, l.get("target_id")) if v.anchor_exists(profile, l.get("target_id"))
            else f"<code>{esc(l.get('target_id'))}</code>",
            esc(l.get("rationale")),
            f"<code>{esc(l.get('provenance'))}</code>",
            f"<code>{esc(l.get('review_state'))}</code>",
            f"<code>{esc('true' if l.get('change_suspect_status') else 'false')}</code>",
            esc(f"rev {l.get('source_revision')} → rev {l.get('target_revision')}"),
        ])
    L += table(["Link", "Profile", "Source", "Relation", "Target", "Rationale", "Provenance",
                "Review state", "Change-suspect", "Revisions"], rows,
               css_class="links wide",
               caption=f"All {len(v.links)} registry links, sorted by profile then link id.")
    counts = {}
    for l in v.links:
        counts[(l.get("_profile"), l.get("relation_type"))] = \
            counts.get((l.get("_profile"), l.get("relation_type")), 0) + 1
    L += table(["Profile", "Relation type", "Links"], [
        [f"<code>{esc(p)}</code>", f"<code>{esc(r)}</code>", esc(str(n))]
        for (p, r), n in sorted(counts.items())], css_class="std")

    L.append(sub("Requirement Coverage Matrix", anchor="requirement-coverage-matrix"))
    L.append(note(
        "One row per requirement record in the artifact index, both profiles. Statuses are derived, "
        "not asserted: <code>COVERED-DIRECT</code> when a <code>verifies</code> or "
        "<code>validates</code> link points at the requirement; <code>COVERED-INDIRECT</code> when "
        "a requirement allocated to it is covered; <code>COVERED-EMBEDDED</code> when a test "
        "measure names it in <code>referenced_requirements</code>; <code>UNCOVERED</code> "
        "otherwise, which is a declared gap. The row anchor is "
        "<code>cov-&lt;profile&gt;-&lt;requirement id&gt;</code>.", "callout"))
    rows = []
    _row_cov_id = []
    for profile, aid in v.requirements():
        d = v.get(profile, aid)
        cov = v.coverage(profile, aid)
        _row_cov_id.append(f"{profile}-{aid}")
        rows.append([
            f"<a id=\"cov-{esc(profile)}-{esc(aid)}\" href=\"#cov-{esc(profile)}-{esc(aid)}\">"
            f"<code>{esc(aid)}</code></a>",
            f"<code>{esc(profile)}</code>",
            f"<code>{esc(requirement_class(aid))}</code>",
            f"<code>{esc(d.get('engineering_domain'))}</code>",
            f"<code>{esc(cov['status'])}</code>",
            ", ".join(v.aref(profile, t) for t in cov["direct"]) or "—",
            esc("; ".join(f"{k} ← {', '.join(t)}" for k, t in sorted(cov["indirect"].items()))) or "—",
            ", ".join(v.aref(profile, t) for t in cov["embedded"]) or "—",
            esc(", ".join(cov["tests"]) or "none — requirement is not covered by any test measure"),
        ])
    L += table(["Requirement", "Profile", "Class", "Domain", "Coverage status", "Direct measures",
                "Indirect (allocated child ← measure)", "Embedded in measure", "All measures"],
               rows, css_class="wide",
               row_id_fn=lambda i, _row: f"cov-row-{_row_cov_id[i]}",
               caption=f"All {len(v.requirements())} requirement records, sorted by profile then id.")
    uncovered = [f"{p}/{a}" for p, a in v.requirements() if v.coverage(p, a)["status"] == "UNCOVERED"]
    if uncovered:
        v.gap("uncovered-requirement", "coverage matrix",
              f"{len(uncovered)} requirement record(s) have no verifying or validating test measure "
              f"and are not named in any test measure's referenced_requirements: "
              f"{esc(', '.join(uncovered))}.",
              "link registry and test_measure.referenced_requirements")
        L.append(note(
            f"{len(uncovered)} requirement record(s) are marked UNCOVERED in the matrix above and "
            f"are listed as a named gap in section 12. An uncovered requirement is reported, not "
            f"papered over.", "warn"))

    L.append(sub("Review Coverage", anchor="review-coverage"))
    revs = v.records(lambda d: d.get("artifact_type") == "review")
    if not revs:
        v.gap("absent-record-family", "reviews",
              "The artifact index holds no review record, so the corpus holds no review evidence.",
              "artifact index, artifact_type == review")
        L.append(f"<p>{v.gap_phrase('review records')}</p>")
    for profile, aid, d in revs:
        L.append(card_open(v, profile, aid, d, "review"))
        L.append(f"<h4>{v.aref(profile, aid)} — {esc(d.get('title') or aid)}</h4>")
        L.append(guard_html(guard_tuple(d)))
        for key in ("review_type", "review_state", "reviewer", "reviewer_role", "method",
                    "scope", "decision", "verdict", "summary", "notes", "review_date",
                    "independence", "automation", "tool", "conclusion", "recommendation",
                    "records_reviewed", "criteria", "findings_summary", "lifecycle_status_note",
                    "limitations", "review_disposition", "review_disposition_note"):
            if d.get(key):
                L.append(kv(esc(key.replace("_", " ")), esc(d[key])))
        revlinks = [l for l in v.links_where(profile=profile) if l.get("relation_type") == "reviewed_by"
                    and (l.get("source_id") == aid or l.get("target_id") == aid)]
        L.append(kv("Records reviewed, via the link registry",
                    esc(str(len(revlinks)))))
        L.append(kv("Assumption references", v.asm_ref_html(d.get("assumption_refs"))))
        L.append(kv("Source references", v.src_ref_html(d.get("source_refs"))))
        L.append(kv("Standards mappings", standards_table(d, v)))
        L.append(kv("Record limitations", limitation_block(d, v)))
        L.append("</article>")

    L.append(sub("Findings", anchor="findings"))
    fnd = v.records(lambda d: d.get("artifact_type") == "finding")
    if not fnd:
        v.gap("absent-record-family", "findings",
              "The artifact index holds no finding record.", "artifact index, artifact_type == finding")
        L.append(f"<p>{v.gap_phrase('finding records')}</p>")
    rows = []
    for profile, aid, d in fnd:
        rows.append([
            v.aref(profile, aid),
            f"<code>{esc(d.get('severity'))}</code>",
            f"<code>{esc(d.get('status') or d.get('lifecycle_status'))}</code>",
            esc(d.get("title") or aid, 90),
            esc(d.get("description") or d.get("summary") or d.get("statement"), 200),
            esc(", ".join(v.aref(profile, r) for r in (d.get("affected_artifacts") or [])) or "—"),
        ])
    if rows:
        L += table(["Finding", "Severity", "Status", "Title", "Description", "Affected artifacts"],
                   rows, css_class="wide")
    for profile, aid, d in fnd:
        L.append(card_open(v, profile, aid, d, "finding"))
        L.append(f"<h4>{v.aref(profile, aid)} — {esc(d.get('title') or aid)}</h4>")
        L.append(guard_html(guard_tuple(d)))
        for key, val in sorted(d.items()):
            if key in ("id", "title", "profile", "origin", "human_approval_status",
                       "production_authorized", "product_verification_credit",
                       "automated_review_status", "revision_history", "created_at",
                       "updated_at", "revision", "schema_version", "artifact_type",
                       "engineering_domain", "scenario_id", "baseline_id",
                       "variant_applicability", "standards_mappings", "source_refs",
                       "assumption_refs", "lifecycle_status", "owner_role"):
                continue
            L.append(kv(esc(key.replace("_", " ")), esc(val, 600)))
        L.append(kv("Standards mappings", standards_table(d, v)))
        L.append("</article>")

    L.append(sub("Scenario Fixtures", anchor="scenario-fixtures"))
    scns = v.records(lambda d: d.get("artifact_type") == "scenario")
    if not scns:
        v.gap("absent-record-family", "scenario fixtures",
              "The artifact index holds no scenario record, so the corpus holds no negative-test "
              "fixture.", "artifact index, artifact_type == scenario")
        L.append(f"<p>{v.gap_phrase('scenario fixtures')}</p>")
    for profile, aid, d in scns:
        L.append(card_open(v, profile, aid, d, "scenario"))
        L.append(f"<h4>{v.aref(profile, aid)} — {esc(d.get('title') or aid)}</h4>")
        L.append(guard_html(guard_tuple(d)))
        for key, val in sorted(d.items()):
            if key in ("id", "title", "profile", "origin", "human_approval_status",
                       "production_authorized", "product_verification_credit",
                       "automated_review_status", "revision_history", "created_at",
                       "updated_at", "revision", "schema_version", "artifact_type",
                       "engineering_domain", "scenario_id", "baseline_id",
                       "variant_applicability", "standards_mappings", "source_refs",
                       "assumption_refs", "lifecycle_status", "owner_role"):
                continue
            L.append(kv(esc(key.replace("_", " ")), esc(val, 600)))
        L.append(kv("Standards mappings", standards_table(d, v)))
        L.append("</article>")
    return L


# ---------------------------------------------------------------- 12. gaps

def sec_12(v):
    L = []
    L.append(note(
        "Every place where the engineering process expects content the corpus does not hold is "
        "listed here as a named gap. The registry is built from the same calls the section "
        "renderers make, so it cannot drift from the body: a gap is registered at the moment the "
        "renderer discovers the absence, and the mandated wording "
        f"<span class=\"phrase-ref\">{GAP_PHRASE}</span> is what the body shows at that site. "
        "Nothing below is filled with a plausible substitute, and nothing is omitted silently.",
        "callout"))
    L.append(sub("Gap Registry", anchor="gap-registry"))
    by_kind = {}
    for g in v.gaps:
        by_kind.setdefault(g["kind"], []).append(g)
    L += table(["Gap kind", "Count"], [[f"<code>{esc(k)}</code>", esc(str(len(g)))]
                                  for k, g in sorted(by_kind.items())])
    rows = []
    for g in v.gaps:
        rows.append([
            f"<code>{esc(g['gap_id'])}</code>",
            f"<code>{esc(g['kind'])}</code>",
            esc(g["subject"]),
            esc(g["statement"]),
            f"<code>{esc(g['consulted'])}</code>",
        ])
    L += table(["Gap", "Kind", "Subject", "What the corpus does and does not hold",
                "Corpus field consulted"], rows, css_class="gaps wide",
               row_id_fn=lambda i, _row: v.gaps[i]["gap_id"],
               caption=f"{len(v.gaps)} declared gap(s), in the order the renderer discovered them.")
    return L


# ---------------------------------------------------------------- 13. diagram validation

def sec_13(v):
    L = []
    L.append(note(
        "<strong>No diagram in this document is described as validated by this file.</strong> The "
        "diagrams are emitted as Mermaid source and rendered by the reader's browser from a CDN. "
        "The syntax check is a separate post-generation step, run by the operator, whose result is "
        "reported on the console and deliberately not embedded here — embedding it would make the "
        "file depend on the outcome of an external tool and would break the byte-for-byte "
        "determinism the integrity check enforces. The table below therefore records, for every "
        "diagram, its identifier, its Mermaid diagram type, its viewpoint and the exact corpus "
        "fields it is derived from. It makes no syntax claim.", "warn"))
    L.append(sub("Diagram Inventory", anchor="diagram-inventory"))
    rows = []
    for d in v.diagrams:
        rows.append([
            f"<code>{esc(d['diagram_id'])}</code>",
            f"<code>{esc(d['mermaid_type'])}</code>",
            esc(d["viewpoint"]),
            esc(d["caption"]),
            esc(d["derived_from"]),
            esc(str(d["source_lines"])),
            '<span class="unvalidated">not checked by this file</span>',
        ])
    L += table(["Diagram identifier", "Mermaid type", "Viewpoint", "Caption",
                "Corpus records it is derived from", "Source lines",
                "Syntax validation performed at generation time"], rows, css_class="wide")
    L.append(sub("How validation is performed", anchor="how-validation-is-performed"))
    L.append(table(["Step", "Command or fact"], [
        ["Generate", "<code>python3 docs/artifacts/tools/render_e2e_html.py</code>"],
        ["List the diagrams", "every <code>&lt;pre class=\"mermaid\"&gt;</code> block in the "
                              "generated file, identified by the enclosing "
                              "<code>data-diagram-id</code> attribute"],
        ["Syntax-check them",
         "<code>python3 docs/artifacts/tools/render_e2e_html.py --validate-mermaid</code> — "
         "extracts each block, writes it to a temporary file and runs <code>mmdc</code> "
         "(mermaid-cli) against a locally installed Chrome, reporting one result per diagram"],
        ["When the tooling is absent",
         "the command reports that the diagrams were NOT checked and why. It never reports a "
         "diagram as validated on the basis of not having checked it"],
    ]))
    return L


# ---------------------------------------------------------------- 14. guard audit

def sec_14(v):
    L = []
    L.append(sub("Guard-Field Census", anchor="guard-field-census"))
    L.append(note(
        "The census below is computed at render time by walking every record in the artifact index "
        "and reading its own guard fields. It is a description of the corpus, not a statement about "
        "what this document would like the corpus to contain.", "callout"))
    recs = v.records(lambda _d: True)
    fields = ("profile", "origin", "human_approval_status", "production_authorized",
              "product_verification_credit", "lifecycle_status", "scenario_id", "baseline_id",
              "revision", "owner_role")
    rows = []
    for f in fields:
        counts = {}
        for _p, _a, d in recs:
            val = d.get(f, "(field absent)")
            counts[str(val)] = counts.get(str(val), 0) + 1
        rows.append([f"<code>{esc(f)}</code>",
                     esc(", ".join(f"{k} ({n})" for k, n in sorted(counts.items(), key=lambda kv: kv[0]))),
                     esc(str(len(counts)))])
    L += table(["Guard / governance field", "Distinct values across all records (value (count))",
                "Distinct values"], rows, css_class="wide")

    L.append(sub("Census by artifact type and profile", level=4, anchor="guard-census-by-type"))
    types = {}
    for p, _a, d in recs:
        types.setdefault((d.get("artifact_type", "(absent)"), p), 0)
        types[(d.get("artifact_type", "(absent)"), p)] += 1
    L += table(["Artifact type", "as_is", "synthetic_reference", "Total"],
               [[f"<code>{esc(t)}</code>", esc(str(types.get((t, 'as_is'), 0))),
                 esc(str(types.get((t, 'synthetic_reference'), 0))),
                 esc(str(types.get((t, 'as_is'), 0) + types.get((t, 'synthetic_reference'), 0)))]
                for t in sorted({t for t, _p in types})], css_class="std")

    L.append(sub("Declarations", anchor="declarations"))
    hs, asp = guard_census(v)
    L.append("<ul>")
    L.append(f"<li>Every record rendered in this document carries its own "
             f"<code>profile</code>, <code>origin</code>, <code>human_approval_status</code> and "
             f"<code>production_authorized</code> on a guard line directly beneath its title.</li>")
    L.append(f"<li>Across all {len(recs)} records in the artifact index the distinct "
             f"<code>human_approval_status</code> values are "
             f"<code>{esc(', '.join(hs))}</code> and the distinct "
             f"<code>production_authorized</code> values are <code>{esc(', '.join(asp))}</code>.</li>")
    L.append("<li>This document asserts no ISO 26262 conformity, no ASIL capability level, no "
             "Automotive SPICE assessment, and no human approval or sign-off. An automated review "
             "recorded on a record is an automated review and is not an organisational or human "
             "confirmation measure.</li>")
    L.append("<li>Every ASIL value in this document is a field read from a corpus record. For the "
             "<code>synthetic_reference</code> profile those values belong to a fictional project "
             "grounded in foxBMS; they are not a determination for the real foxBMS product.</li>")
    L.append("<li>No execution record in this document carries product verification credit; the "
             "<code>product_verification_credit</code> field is shown on every one of them.</li>")
    L.append("</ul>")
    return L


# ---------------------------------------------------------------- 15. appendix

def sec_15(v):
    L = []

    L.append(sub("Parameter Registry", anchor="parameter-registry"))
    if not v.params:
        v.gap("absent-registry", "parameter registry",
              "The shared parameter registry holds no parameter entry.",
              "shared/parameter-registry.json")
        L.append(f"<p>{v.gap_phrase('parameter registry entries')}</p>")
    else:
        rows = []
        for p in sorted(v.params, key=lambda p: str(p.get("id"))):
            rows.append([
                f"<code>{esc(p.get('id'))}</code>", f"<code>{esc(p.get('name'))}</code>",
                esc(f"{p.get('value')} {p.get('unit')}"),
                esc(p.get("tolerance")), esc(p.get("domain")),
                esc(p.get("thresholds")), esc(p.get("timing_budget")),
                esc(p.get("debounce")), esc(p.get("hysteresis")),
                esc(", ".join(p.get("assumptions", []) or []) or "—"),
                esc(", ".join(p.get("configuration_selection", []) or []) or "—"),
            ])
        L += table(["Parameter", "Name", "Value", "Tolerance", "Domain", "Thresholds",
                    "Timing budget", "Debounce", "Hysteresis", "Assumptions", "Configurations"],
                   rows, css_class="wide")

    L.append(sub("Assumption Registry", anchor="assumption-registry"))
    if not v.assumptions:
        v.gap("absent-registry", "assumption registry",
              "The shared assumption registry holds no assumption entry.",
              "shared/assumption-registry.json")
        L.append(f"<p>{v.gap_phrase('assumption registry entries')}</p>")
    else:
        rows = []
        for a in sorted(v.assumptions, key=lambda a: str(a.get("id"))):
            rows.append([
                f"<code>{esc(a.get('id'))}</code>", esc(a.get("statement")),
                esc(a.get("rationale")), esc(a.get("affected_scope")),
                f"<code>{esc(a.get('source'))}</code>",
                esc(a.get("validity_conditions")),
                esc(a.get("invalidation_consequence")),
                f"<code>{esc(a.get('review_status'))}</code>",
            ])
        L += table(["Assumption", "Statement", "Rationale", "Affected scope", "Source",
                    "Validity conditions", "Consequence if invalidated", "Review status"], rows,
                   css_class="wide")

    L.append(sub("Source Registry", anchor="source-registry"))
    if not v.source_anchors:
        v.gap("absent-registry", "source registry",
              "The source anchor registry holds no anchor.",
              "sources/source-registry.json")
        L.append(f"<p>{v.gap_phrase('source anchors')}</p>")
    else:
        rows = []
        for a in sorted(v.source_anchors, key=lambda a: str(a.get("anchor_id"))):
            loc = a.get("location") or {}
            rows.append([
                f"<code>{esc(a.get('anchor_id'))}</code>",
                f"<code>{esc(a.get('source_type'))}</code>",
                esc(source_anchor_str(a)),
                esc(loc.get("commit") or loc.get("repository") or "—"),
                esc(a.get("content_hash")),
                esc(a.get("retrieval_date")),
            ])
        L += table(["Anchor", "Source type", "Resolved location", "Repository / commit",
                    "Content hash", "Retrieval date"], rows, css_class="wide")

    L.append(sub("Management and Supporting Records", anchor="management-and-supporting-records"))
    support_types = ("project_plan", "measurement_plan", "process_record", "process_improvement",
                     "risk_register", "post_development_record")
    for atype in support_types:
        recs = v.records(lambda d, a=atype: d.get("artifact_type") == a)
        L.append(sub(atype.replace("_", " ").title(), level=4,
                     anchor=f"support-{atype.replace('_', '-')}"))
        if not recs:
            v.gap("absent-record-family", atype,
                  f"The artifact index holds no {esc(atype)} record in either profile.",
                  f"artifact index, artifact_type == {atype}")
            L.append(f"<p>{v.gap_phrase(atype.replace('_', ' '))}</p>")
            continue
        for profile, aid, d in recs:
            L.append(card_open(v, profile, aid, d, atype))
            L.append(f"<h5>{v.aref(profile, aid)} — {esc(d.get('title') or aid)}</h5>")
            L.append(guard_html(guard_tuple(d)))
            for key, val in sorted(d.items()):
                if key in ("id", "title", "profile", "origin", "human_approval_status",
                           "production_authorized", "product_verification_credit",
                           "automated_review_status", "revision_history", "created_at",
                           "updated_at", "revision", "schema_version", "artifact_type",
                           "engineering_domain", "scenario_id", "baseline_id",
                           "variant_applicability", "standards_mappings", "source_refs",
                           "assumption_refs", "lifecycle_status", "owner_role"):
                    continue
                L.append(kv(esc(key.replace("_", " ")), esc(val, 800)))
            L.append(kv("Standards mappings", standards_table(d, v)))
            L.append("</article>")

    L.append(sub("Corpus Census", anchor="corpus-census"))
    L.append(note(
        "The population every other count in this document is drawn from, as read from the "
        f"artifact index and both link registries at generation time.", "meta"))
    rows = []
    for atype in sorted({d.get("artifact_type", "(absent)") for _p, _a, d in v.records(lambda _d: True)}):
        a = sum(1 for _p, _aid, d in v.records(lambda _d: True)
                if d.get("artifact_type") == atype and _p == "as_is")
        s = sum(1 for _p, _aid, d in v.records(lambda _d: True)
                if d.get("artifact_type") == atype and _p == "synthetic_reference")
        u = sum(1 for _p, _aid, d in v.records(lambda _d: True)
                if d.get("artifact_type") == atype and _p not in PROFILES)
        rows.append([f"<code>{esc(atype)}</code>", esc(str(a)), esc(str(s)), esc(str(u)),
                     esc(str(a + s + u))])
    rows.append(["<strong>Total</strong>",
                 esc(str(sum(1 for p, _a, _d in v.records(lambda _d: True) if p == "as_is"))),
                 esc(str(sum(1 for p, _a, _d in v.records(lambda _d: True)
                             if p == "synthetic_reference"))),
                 esc(str(sum(1 for p, _a, _d in v.records(lambda _d: True) if p not in PROFILES))),
                 esc(str(len(v.index)))])
    L += table(["Artifact type", "as_is", "synthetic_reference", "other / unknown", "Total"], rows,
               css_class="std")
    L.append(table(["Registry", "Entries"], [
        ["Link registry (<code>as_is</code>)",
         esc(str(len([l for l in v.links if l.get("_profile") == "as_is"])))],
        ["Link registry (<code>synthetic_reference</code>)",
         esc(str(len([l for l in v.links if l.get("_profile") == "synthetic_reference"])))],
        ["Link registry total", esc(str(len(v.links)))],
        ["Parameter registry", esc(str(len(v.params)))],
        ["Assumption registry", esc(str(len(v.assumptions)))],
        ["Source anchor registry", esc(str(len(v.source_anchors)))],
    ]))
    L.append(note(
        "A record that exists in both profiles is counted once per profile. The same identifier in "
        "<code>as_is</code> and in <code>synthetic_reference</code> is two different records by "
        "corpus design and is never merged.", "meta"))

    L.append(sub("Regeneration and Integrity", anchor="regeneration-and-integrity"))
    L.append(table(["What the integrity check verifies", "How"], [
        ["The file exists and is non-empty", "stat and size"],
        ["Every required section anchor and heading is present",
         "each <code>sec-*</code> id and heading string from the generator's section registry"],
        ["Every required sub-heading is present inside its section",
         "each heading from the generator's sub-heading map, searched within that section's text"],
        ["Every record in the artifact index is anchored in the document",
         "each <code>(profile, id)</code> in the index must have an <code>art-&lt;profile&gt;-"
         "&lt;id&gt;</code> anchor; a missing one is named in the failure output"],
        ["Every requirement record appears",
         "each <code>cov-&lt;profile&gt;-&lt;id&gt;</code> coverage-matrix row must exist for every "
         "requirement record in the index"],
        ["Every link registry entry appears",
         "each <code>lnk-&lt;profile&gt;-&lt;link id&gt;</code> row must exist for every link"],
        ["Every gap is registered and every absent-model site carries the mandated wording",
         "the number of rendered <code>gap</code> registry rows must equal the number of gaps the "
         "renderers registered, and the number of <code>gap-phrase</code> spans in the file must "
         "equal the number of absent-model sites the renderers passed"],
        ["Every guard line matches the corpus",
         "each <code>guard</code> element's <code>data-guard</code> attribute is compared against "
         "the record's own four guard fields, and its visible text is checked to contain all four"],
        ["The run is deterministic",
         "the document is generated a second time into a temporary directory and byte-compared "
         "after normalising the single <code>data-generated-at</code> attribute"],
    ], css_class="wide"))
    return L


# ---------------------------------------------------------------- page assembly

CSS = """
:root {
  --bg: #ffffff; --fg: #16191d; --muted: #5b6470; --line: #d8dee6;
  --panel: #f6f8fa; --panel2: #eef2f6; --accent: #1f4e79; --accent2: #0b6e4f;
  --warn: #8a4b00; --warnbg: #fff6e5; --gap: #7a1f1f; --gapbg: #fdf1f1;
  --mono: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
  --sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #14171a; --fg: #e6e9ec; --muted: #9aa4b0; --line: #2c333b;
    --panel: #1b1f24; --panel2: #22272e; --accent: #7fb3e8; --accent2: #6fd3a8;
    --warn: #ffc078; --warnbg: #33280f; --gap: #ff9d9d; --gapbg: #331616;
  }
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body { margin: 0; background: var(--bg); color: var(--fg); font: 15px/1.55 var(--sans); }
a { color: var(--accent); text-decoration: none; border-bottom: 1px solid transparent; }
a:hover { border-bottom-color: var(--accent); }
code { font-family: var(--mono); font-size: .9em; background: var(--panel2);
       padding: 0 .25em; border-radius: 3px; }
pre { font-family: var(--mono); }
h1 { font-size: 1.7rem; margin: 0 0 .2rem; }
h2 { font-size: 1.3rem; border-bottom: 2px solid var(--line); padding-bottom: .3rem;
     margin-top: 2.2rem; }
h3 { font-size: 1.1rem; margin-top: 1.6rem; }
h4 { font-size: 1rem; margin: 1.4rem 0 .4rem; }
h5 { font-size: .95rem; margin: 1.1rem 0 .3rem; }
p { margin: .45rem 0; }
ul, ol { margin: .4rem 0 .6rem 1.2rem; padding: 0; }
li { margin: .2rem 0; }
.wrap { display: flex; align-items: flex-start; }
nav.toc { position: sticky; top: 0; align-self: flex-start; width: 24rem; max-width: 30vw;
          height: 100vh; overflow: auto; border-right: 1px solid var(--line);
          padding: 1rem .9rem 3rem; background: var(--panel); }
nav.toc h2 { font-size: .8rem; text-transform: uppercase; letter-spacing: .06em;
             color: var(--muted); border: 0; margin: 0 0 .5rem; }
nav.toc ol { list-style: none; margin: 0; padding: 0; }
nav.toc li { margin: .12rem 0; }
nav.toc a { display: block; padding: .18rem .3rem; border-radius: 4px; font-size: .86rem;
            color: var(--fg); border: 0; }
nav.toc a:hover { background: var(--panel2); }
nav.toc a.sub { padding-left: 1.1rem; font-size: .8rem; color: var(--muted); }
main { flex: 1 1 auto; min-width: 0; padding: 1.2rem 2rem 8rem; }
header.doc { border-bottom: 1px solid var(--line); padding-bottom: 1rem; margin-bottom: 1rem; }
table { border-collapse: collapse; width: 100%; margin: .7rem 0 1rem; font-size: .87rem;
        display: block; overflow-x: auto; }
th, td { border: 1px solid var(--line); padding: .34rem .5rem; text-align: left;
         vertical-align: top; }
th { background: var(--panel2); font-weight: 600; position: sticky; top: 0; }
table.links td:first-child, table.wide td { min-width: 6rem; }
table.gaps td { font-size: .84rem; }
p.tbl-cap { color: var(--muted); font-size: .84rem; margin: .2rem 0; }
p.kv { margin: .18rem 0; }
p.kv .k { display: inline-block; min-width: 15rem; color: var(--muted); font-size: .84rem; }
p.guard { font-size: .78rem; color: var(--muted); background: var(--panel);
          border-left: 3px solid var(--line); padding: .2rem .5rem; margin: .25rem 0 .5rem; }
p.callout { background: var(--panel); border: 1px solid var(--line); border-left: 4px solid var(--accent);
            padding: .6rem .8rem; margin: .8rem 0; border-radius: 4px; }
p.warn { background: var(--warnbg); border: 1px solid var(--warn); padding: .6rem .8rem;
         margin: .8rem 0; border-radius: 4px; }
p.meta { color: var(--muted); font-size: .84rem; }
span.gap-phrase { background: var(--gapbg); color: var(--gap); border: 1px solid var(--gap);
                  padding: 0 .3em; border-radius: 3px; font-size: .9em; white-space: nowrap; }
/* A quotation of the mandated wording in prose. Deliberately a different class
   from .gap-phrase, which marks an actual absent-model site, so the integrity
   check can count real sites without counting mentions of the phrase. */
span.phrase-ref { color: var(--gap); font-style: italic; }
article.card { border: 1px solid var(--line); border-radius: 6px; padding: .8rem 1rem;
               margin: 1rem 0; background: var(--panel); }
article.card > h4:first-child, article.card > h5:first-child { margin-top: 0; }
figure.diagram { border: 1px solid var(--line); border-radius: 6px; padding: .6rem .8rem;
                 margin: 1rem 0; background: var(--panel); }
figure.diagram figcaption { font-weight: 600; font-size: .9rem; margin-bottom: .4rem; }
figure.diagram figcaption .dg-id { font-family: var(--mono); font-size: .82rem;
                                   color: var(--accent2); }
pre.mermaid { background: var(--bg); border: 1px dashed var(--line); border-radius: 4px;
              padding: .7rem; overflow: auto; font-size: .8rem; line-height: 1.4;
              max-height: 34rem; white-space: pre; }
p.dg-src { font-size: .8rem; color: var(--muted); }
p.noscript { font-size: .85rem; color: var(--muted); }
span.unvalidated { color: var(--warn); font-weight: 600; }
details.sec { border: 1px solid var(--line); border-radius: 6px; margin: .6rem 0;
              background: var(--bg); }
details.sec > summary { cursor: pointer; padding: .5rem .8rem; font-weight: 600;
                        background: var(--panel2); border-radius: 6px; }
details.sec[open] > summary { border-radius: 6px 6px 0 0; border-bottom: 1px solid var(--line); }
details.sec > .secbody { padding: .2rem 1rem 1rem; }
ol.chain > li { margin: .3rem 0; }
.doctype-note { color: var(--muted); font-size: .84rem; }
#toc-toggle { display: none; }
@media (max-width: 60rem) {
  nav.toc { position: static; width: auto; max-width: none; height: auto;
            border-right: 0; border-bottom: 1px solid var(--line); }
  .wrap { display: block; }
  main { padding: 1rem; }
}
@media print {
  nav.toc { display: none; }
  details.sec > .secbody { display: block; }
  pre.mermaid { max-height: none; }
}
"""

SCRIPTS = """
<script>
// Copy the single run-varying field out of the document metadata so the
// generation stamp is visible in the page as well as in the file. This reads
// only local document state: nothing is fetched, and the bytes of this file
// are identical between two runs, because the value is never written into the
// file itself.
(function () {
  var meta = document.querySelector('meta[name="data-generated-at"]');
  var cell = document.getElementById('gen-stamp-view');
  if (meta && cell) { cell.textContent = meta.getAttribute('content') || ''; }
})();
</script>
<script type="module">
// Mermaid is loaded from a CDN at view time only. Nothing is fetched when this
// document is generated. If the CDN is unreachable, or scripting is off, the
// Mermaid blocks stay as readable diagram source and every table, card and
// link in the document is unaffected.
import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.esm.min.mjs';
mermaid.initialize({ startOnLoad: true, securityLevel: 'strict', theme: 'neutral' });
</script>
"""


def build_toc():
    out = ['<nav class="toc" aria-label="Table of contents">', "<h2>Contents</h2>", "<ol>"]
    for sec_id, heading in SECTIONS:
        out.append(f'<li><a href="#{sec_id}">{esc(heading)}</a>')
        subs = REQUIRED_SUBHEADINGS.get(sec_id, [])
        if subs:
            out.append("<ol>")
            for s in subs:
                a = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
                out.append(f'<li><a class="sub" href="#{a}">{esc(s)}</a></li>')
            out.append("</ol>")
        out.append("</li>")
    out.append("</ol>")
    out.append("<p class=\"doctype-note\">Diagrams render client-side from a CDN. With no network "
               "or no scripting they remain readable as Mermaid source; no other part of this "
               "document depends on them.</p>")
    out.append("</nav>")
    return out


def build(v, stamp):
    def flat(lines):
        # Section renderers return a flat list of HTML lines; the block helpers
        # (table, diagram, card) return lists of lines that a renderer may
        # append either way. Flatten once here so no renderer has to remember
        # which helper returns what.
        out = [x for chunk in lines for x in ([chunk] if isinstance(chunk, str) else chunk)]
        if not all(isinstance(x, str) for x in out):
            raise TypeError("section renderer produced a non-string line")
        return out

    # Each section is a collapsible <details> block. The wrapper carries the
    # section anchor, so every internal cross-reference resolves whether or not
    # the reader has the section open. build() owns the wrapper so no renderer
    # can open a section it forgets to close.
    section_bodies = {}
    for sec_id, _heading in SECTIONS:
        if sec_id == "sec-00-about":
            section_bodies[sec_id] = flat(sec_00(v, stamp))
        elif sec_id == "sec-09-system-verification":
            section_bodies[sec_id] = flat(sec_09(v))
        elif sec_id == "sec-10-software-verification":
            section_bodies[sec_id] = flat(sec_10(v))
        else:
            fn = globals()["sec_" + {
                "sec-01-stakeholder": "01",
                "sec-02-system-requirements": "02",
                "sec-03-system-architecture": "03",
                "sec-04-software-requirements": "04",
                "sec-05-software-architecture": "05",
                "sec-06-detailed-design": "06",
                "sec-07-implementation-mapping": "07",
                "sec-08-software-integration": "08",
                "sec-11-traceability": "11",
                "sec-12-gaps": "12",
                "sec-13-diagram-validation": "13",
                "sec-14-guard-audit": "14",
                "sec-15-appendix": "15",
            }[sec_id]]
            section_bodies[sec_id] = flat(fn(v))
    body = []
    for sec_id, heading in SECTIONS:
        body.append(f'<details class="sec" id="{sec_id}" open>')
        body.append(f"<summary>{esc(heading)}</summary>")
        body.append('<div class="secbody">')
        body.append(f'<h2 id="{sec_id}-h">{esc(heading)}</h2>')
        body += section_bodies[sec_id]
        body.append("</div>")
        body.append("</details>")

    out = []
    out.append("<!DOCTYPE html>")
    out.append('<html lang="en">')
    out.append("<head>")
    out.append('<meta charset="utf-8">')
    out.append('<meta name="viewport" content="width=device-width, initial-scale=1">')
    out.append(f'<meta name="data-generated-at" content="{esc(stamp)}">')
    out.append("<title>foxBMS 2 — End-to-End Engineering Document (derived from the lifecycle "
               "artifact corpus)</title>")
    out.append(f'<style>{CSS}</style>')
    out.append("</head>")
    out.append("<body>")
    out.append('<div class="wrap">')
    out += build_toc()
    out.append("<main>")
    out.append('<header class="doc">')
    out.append("<h1>foxBMS 2 — End-to-End Engineering Document</h1>")
    out.append('<p class="doctype-note">A derived, read-only work product generated from the '
               'foxBMS 2 lifecycle artifact corpus. It is not hand-authored, it asserts no '
               'standards conformity, no ASIL capability level, no process assessment and no human '
               'approval, and it introduces no fact that is not derivable from the corpus.</p>')
    out += table(["Field", "Value"], [
        ["Project", "foxBMS 2 — Battery Management System reference platform"],
        ["Document", "End-to-end engineering document (single-file HTML)"],
        ["Profiles covered",
         "<code>as_is</code> (source-grounded reconstruction) and "
         "<code>synthetic_reference</code> (fictional hypothetical project)"],
        ["Baseline recorded in the corpus records",
         esc(", ".join(sorted({str(d.get("baseline_id")) for _p, _a, d in
                               v.records(lambda _d: True) if d.get("baseline_id")})))],
        ["Records in the artifact index", esc(str(len(v.index)))],
        ["Links in both link registries", esc(str(len(v.links)))],
        ["Diagrams emitted", esc(str(len(v.diagrams)))],
        ["Declared gaps", esc(str(len(v.gaps)))],
        ["Generated by", "<code>docs/artifacts/tools/render_e2e_html.py</code>"],
        ["Generation stamp", '<span id="gen-stamp-view">(shown in the document metadata)</span>'],
    ])
    out.append("</header>")

    out += body

    out.append('<p class="doctype-note">End of document. Generated from the corpus; regenerate with '
               '<code>python3 docs/artifacts/tools/render_e2e_html.py</code> and verify with '
               '<code>--check</code>.</p>')
    out.append("</main>")
    out.append("</div>")
    out.append(SCRIPTS)
    out.append("</body>")
    out.append("</html>")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- integrity check

STAMP_RE = re.compile(r'(<meta name="data-generated-at" content=")[^"]*(">)')


def strip_stamp(text):
    """Normalise the single run-varying field so two runs can be byte-compared."""
    out, n = STAMP_RE.subn(r'\1<stamp>\2', text)
    return out, n


def section_spans(text):
    """Split the document into (section_id, body) so a sub-heading can be
    required inside its own section rather than anywhere in the file.

    The section anchor lives on the collapsible <details> wrapper, so the
    boundaries are the <details> elements, not <section> elements.
    """
    spans = {}
    for m in re.finditer(r'<(?:details|section)[^>]*\bid="(sec-[a-z0-9-]+)"', text):
        spans[m.group(1)] = m.end()
    order = sorted(spans.items(), key=lambda kv: kv[1])
    result = {}
    for i, (sid, start) in enumerate(order):
        end = order[i + 1][1] if i + 1 < len(order) else len(text)
        result[sid] = text[start:end]
    return result


def verify_html(v, path):
    """Integrity verification of a generated document. Returns (ok, failures)."""
    failures = []
    if not path.exists():
        return False, [f"MISSING document: {path}"]
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return False, [f"EMPTY document: {path}"]
    stripped, n_stamps = strip_stamp(text)
    if n_stamps != 1:
        failures.append(f"expected exactly one data-generated-at field, found {n_stamps}")

    # (a) required sections. The heading is matched as a whole heading element,
    # not as a substring, so renaming or appending to a required heading is a
    # failure rather than a near miss.
    spans = section_spans(text)
    for sec_id, heading in SECTIONS:
        if f'id="{sec_id}"' not in text:
            failures.append(f"MISSING section anchor: {sec_id}")
        exact = f'<h2 id="{sec_id}-h">{esc(heading)}</h2>'
        if exact not in text:
            failures.append(f"MISSING section heading for {sec_id}: expected exactly {exact!r}")
    # (b) required sub-headings, inside their own section, matched as whole
    # heading elements at whatever level the renderer chose
    for sec_id, heads in sorted(REQUIRED_SUBHEADINGS.items()):
        body = spans.get(sec_id)
        if body is None:
            failures.append(f"{sec_id}: section body not found, cannot check its sub-headings")
            continue
        for h in heads:
            pattern = r"<h[2-5][^>]*>" + re.escape(esc(h)) + r"</h[2-5]>"
            if not re.search(pattern, body):
                failures.append(f"{sec_id}: missing required sub-heading '{h}'")

    # (c) every record in the artifact index is anchored
    art_anchors = set(re.findall(r'id="(art-[a-z_]+-[A-Za-z0-9\-]+)"', text))
    unmapped = []
    for (profile, aid) in sorted(v.index):
        if owning_section(profile, aid, v.index[(profile, aid)][1], v) is None:
            unmapped.append(f"{profile}/{aid} (artifact_type "
                            f"{v.index[(profile, aid)][1].get('artifact_type')!r} has no owning "
                            f"section)")
        elif v.anchor(profile, aid) not in art_anchors:
            failures.append(f"owned artifact not present in document: {profile}/{aid} "
                            f"(expected anchor {v.anchor(profile, aid)})")
    for u in unmapped:
        failures.append(f"UNMAPPED artifact type: {u}")

    # (d) coverage matrix complete
    cov = set(re.findall(r'id="(cov-[a-z_]+-[A-Za-z0-9\-]+)"', text))
    for profile, aid in v.requirements():
        if f"cov-{profile}-{aid}" not in cov:
            failures.append(f"coverage matrix: missing row for {profile}/{aid} "
                            f"(expected anchor cov-{profile}-{aid})")

    # (e) every link appears in the matrix
    lnk = set(re.findall(r'id="(lnk-[a-z_]+-[A-Za-z0-9\-]+)"', text))
    for l in v.links:
        key = f"lnk-{l.get('_profile')}-{l.get('link_id')}"
        if key not in lnk:
            failures.append(f"traceability matrix: missing link row for {key}")

    # (f) gaps are registered and every absent-model site carries the wording
    gap_ids = set(re.findall(r'<tr id="(GAP-\d+)"', text))
    if not gap_ids and v.gaps:
        failures.append("gap registry: no gap rows rendered although gaps were registered")
    for g in v.gaps:
        if g["gap_id"] not in gap_ids:
            failures.append(f"gap registry: missing gap row {g['gap_id']} ({g['kind']}, "
                            f"{g['subject']})")
    n_phrase = len(re.findall(r'<span class="gap-phrase">', text))
    if n_phrase != v.gap_phrase_sites:
        failures.append(f"gap wording: {n_phrase} 'not specified in corpus' sites rendered but "
                        f"{v.gap_phrase_sites} absent-model sites were visited — a required "
                        f"wording was dropped or invented")
    for m in re.finditer(r'<span class="gap-phrase">(.*?)</span>', text):
        if m.group(1) != GAP_PHRASE:
            failures.append(f"gap wording: found non-canonical phrasing {m.group(1)!r} where "
                            f"{GAP_PHRASE!r} is required")

    # (g) guard lines match the corpus, field by field
    guard_failures = check_guards(v, text)
    failures += guard_failures

    return (not failures), failures


GUARD_RE = re.compile(r'<p class="guard" data-guard="([^"]*)">(.*?)</p>', re.S)


def parse_guard_blocks(text):
    """[(fields dict, visible text)] for every rendered guard line."""
    out = []
    for attr, body in GUARD_RE.findall(text):
        fields = {}
        for part in attr.split(";"):
            if "=" in part:
                k, val = part.split("=", 1)
                fields[k.strip()] = val.strip()
        out.append((fields, body))
    return out


def check_guards(v, text):
    """Every guard line must carry all four mandated fields, with the values the
    corpus record actually holds, in both the attribute and the visible text.
    The comparison is field-by-field against the record, not a count, so a guard
    line that silently dropped or altered a value fails."""
    failures = []
    blocks = parse_guard_blocks(text)
    if not blocks:
        return ["guard audit: no guard lines found in the document"]
    seen_keys = set()
    for fields, body in blocks:
        missing = [f for f in GUARD_ATTR_FIELDS if f not in fields]
        if missing:
            failures.append(f"guard line missing field(s) {missing}: {fields}")
            continue
        for f in GUARD_ATTR_FIELDS:
            if f"<code>{fields[f]}</code>" not in body:
                failures.append(f"guard line does not show {f}={fields[f]} in its visible text: "
                                f"{fields}")
        seen_keys.add(tuple(str(fields[f]) for f in GUARD_ATTR_FIELDS))
    for (profile, aid), (_path, d) in sorted(v.index.items()):
        g = guard_tuple(d)
        key = tuple(str(g[f]) for f in GUARD_ATTR_FIELDS)
        if key not in seen_keys:
            failures.append(
                f"guard audit: no rendered guard line carries the corpus guard values of "
                f"{profile}/{aid} (profile={g['profile']}, origin={g['origin']}, "
                f"human_approval_status={g['human_approval_status']}, "
                f"production_authorized={g['production_authorized']}, "
                f"product_verification_credit={g['product_verification_credit']})")
    return failures


def determinism(out_path, rebuilt_text):
    """Byte-compare the file on disk against an independent rebuild, after
    normalising the one run-varying field. The rebuild is produced with a fixed
    placeholder stamp, so a difference anywhere other than that field fails."""
    a, na = strip_stamp(out_path.read_text(encoding="utf-8"))
    b, nb = strip_stamp(rebuilt_text)
    ok = (a == b) and na == 1 and nb == 1
    if ok:
        print(f"Determinism: byte-identical across two runs "
              f"({len(a)} bytes; the only normalised field is data-generated-at)")
    else:
        print(f"Determinism: MISMATCH — file on disk {len(a)} bytes / {na} stamp field(s), "
              f"rebuild {len(b)} bytes / {nb} stamp field(s)")
        for i, (x, y) in enumerate(zip(a, b)):
            if x != y:
                print(f"  first difference at byte {i}:")
                print(f"    on disk: {a[max(0, i - 80):i + 80]!r}")
                print(f"    rebuild: {b[max(0, i - 80):i + 80]!r}")
                break
        if len(a) != len(b):
            print(f"  length differs by {abs(len(a) - len(b))} bytes")
    return ok


# ---------------------------------------------------------------- conformity scan

# Patterns that would constitute an affirmative conformity claim. Every pattern
# is scoped to an affirmative construction, and every raw hit is additionally
# classified as negated when a negation appears in the same sentence, so a
# corpus sentence such as "Not ISO 26262 compliant or ASIL certified" is
# reported as a negated mention rather than a claim.
CONFORMITY_PATTERNS = [
    (r"\bISO\s*26262[\s-]*(?:compliant|certified|conformant)\b", "ISO 26262 conformity claim"),
    (r"\bISO\s*26262\s+compliance\b", "ISO 26262 compliance claim"),
    (r"\bASIL[\s-]*(?:certified|certification|compliant)\b", "ASIL certification claim"),
    (r"\bASIL\s+capability\s+level\b", "ASIL capability level claim"),
    (r"\bASPICE[\s-]*(?:compliant|certified|conformant|capability\s+level)\b",
     "ASPICE conformity or capability claim"),
    (r"\bcapability\s+level\s+[1-6]\b", "process capability level claim"),
    (r"\bcompliant\s+with\s+ISO\b", "ISO conformity claim"),
    (r"\bconforms?\s+to\s+ISO\b", "ISO conformity claim"),
    (r"\bmeets?\s+ISO\s*26262\b", "ISO 26262 conformance claim"),
    (r"\bfunctional\s+safety\s+compliance\b", "functional safety compliance claim"),
    (r"\b(?:this|the)\s+(?:corpus|document|item|product|project|repository)\s+"
     r"(?:is|are|has|have)\s+(?:fully\s+)?(?:compliant|certified|conformant|approved)\b",
     "conformity claim about this corpus or product"),
    (r"\bapproved\s+for\s+(?:production|release|service|use)\b", "production approval claim"),
    (r"\bhuman\s+approval\s+(?:granted|obtained|completed|recorded|given)\b",
     "human approval claim"),
    (r"\bhuman[\s-]approved\b", "human approval claim"),
    (r"\bconformity\s+(?:achieved|granted|established|declared|confirmed|proven)\b",
     "conformity claim"),
    (r"\b(?:safety|quality|process)\s+certification\s+(?:achieved|granted|obtained|held)\b",
     "certification claim"),
]
NEGATION_RE = re.compile(
    r"\b(?:not|no|never|without|nor|cannot|can't|does\s+not|do\s+not|is\s+not|are\s+not|"
    r"was\s+not|were\s+not|neither|non|disclaims?|disclaimed|declines?|refuses?|"
    r"makes?\s+no|asserts?\s+no|claims?\s+no|states?\s+no)\b", re.I)


def sentence_around(text, start, end):
    left = max(0, text.rfind(".", 0, start), text.rfind(";", 0, start),
               text.rfind("\n", 0, start))
    right_candidates = [c for c in (text.find(".", end), text.find(";", end),
                                    text.find("\n", end)) if c != -1]
    right = min(right_candidates) if right_candidates else len(text)
    return text[max(0, left + 1):right + 1]


def scan_conformity(text):
    """Return (findings, mentions) where findings are unnegated claim matches."""
    findings, mentions = [], []
    for pattern, label in CONFORMITY_PATTERNS:
        for m in re.finditer(pattern, text, re.I):
            sentence = sentence_around(text, m.start(), m.end())
            negated = bool(NEGATION_RE.search(sentence))
            rec = {"pattern": pattern, "label": label, "match": m.group(0),
                   "context": " ".join(sentence.split())[:240], "negated": negated}
            mentions.append(rec)
            if not negated:
                findings.append(rec)
    return findings, mentions


def audit_guard(v, out_path):
    """Printable audit: guard-field coverage per rendered artifact, and the
    conformity scan with every mention and its verdict."""
    print("=" * 78)
    print("GUARD-FIELD AUDIT — every rendered artifact record")
    print("=" * 78)
    if not out_path.exists():
        print(f"MISSING document: {out_path}")
        return False
    text = out_path.read_text(encoding="utf-8")
    blocks = parse_guard_blocks(text)
    tally = {}
    for fields, body in blocks:
        for f in GUARD_ATTR_FIELDS:
            if f not in fields:
                print(f"  FAIL  guard line missing {f}: {fields}")
                return False
            if f"<code>{fields[f]}</code>" not in body:
                print(f"  FAIL  guard line text does not show {f}={fields[f]}: {fields}")
                return False
        key = tuple(str(fields[f]) for f in GUARD_ATTR_FIELDS)
        tally[key] = tally.get(key, 0) + 1
    print(f"  guard lines rendered: {len(blocks)}")
    print(f"  guard lines carrying all of {', '.join(GUARD_ATTR_FIELDS)}: "
          f"{sum(1 for f, _b in blocks if all(x in f for x in GUARD_ATTR_FIELDS))}")
    print("  distinct guard tuples (profile, origin, human_approval_status, "
          "production_authorized, product_verification_credit) -> count:")
    for key in sorted(tally, key=lambda k: tuple(str(x) for x in k)):
        print(f"    {key[0]:20s} {key[1]:18s} {key[2]:8s} "
              f"prod_auth={key[3]:5s} credit={key[4]:5s}  x{tally[key]}")
    print(f"  records in the artifact index: {len(v.index)}")
    missing = []
    for (profile, aid), (_p, d) in sorted(v.index.items()):
        g = guard_tuple(d)
        key = tuple(str(g[f]) for f in GUARD_ATTR_FIELDS)
        if key not in tally:
            missing.append(f"{profile}/{aid}")
    if missing:
        print(f"  FAIL  {len(missing)} record(s) have no matching guard line: "
              f"{', '.join(missing[:20])}")
    else:
        print("  OK    every record in the artifact index has a matching rendered guard line")

    print()
    print("=" * 78)
    print("CONFORMITY-CLAIM SCAN — affirmative claim patterns, negation-aware")
    print("=" * 78)
    print(f"  patterns checked: {len(CONFORMITY_PATTERNS)}")
    findings, mentions = scan_conformity(text)
    print(f"  raw matches: {len(mentions)}; negated mentions: "
          f"{sum(1 for m in mentions if m['negated'])}; "
          f"affirmative claims: {len(findings)}")
    for m in mentions:
        verdict = "NEGATED" if m["negated"] else "ASSERTED"
        print(f"    [{verdict}] {m['label']}: {m['match']!r}")
        print(f"             in: {m['context']}")
    if findings:
        print(f"  FAIL  {len(findings)} affirmative conformity claim(s) found:")
        for m in findings:
            print(f"    - {m['label']}: {m['match']!r} in {m['context']!r}")
    else:
        print("  OK    no affirmative conformity claim in the generated document")
    return (not findings) and (not missing)


# ---------------------------------------------------------------- mermaid validation

MERMAID_BLOCK_RE = re.compile(
    r'<figure class="diagram" data-diagram-id="([^"]*)"[^>]*>\s*<figcaption>.*?</figcaption>\s*'
    r'<pre class="mermaid"[^>]*>(.*?)</pre>', re.S)


def unescape_mermaid(raw):
    return (raw.replace("&lt;", "<").replace("&gt;", ">")
            .replace("&quot;", '"').replace("&#x27;", "'").replace("&amp;", "&"))


def validate_mermaid(out_path):
    """Syntax-check every embedded diagram with mermaid-cli against a local
    Chrome. Reports the real result per diagram and never claims a check that
    did not run."""
    if not out_path.exists():
        print(f"MISSING document: {out_path}")
        return False
    text = out_path.read_text(encoding="utf-8")
    blocks = MERMAID_BLOCK_RE.findall(text)
    print("=" * 78)
    print("MERMAID DIAGRAM AUDIT")
    print("=" * 78)
    print(f"  diagrams found in {out_path.name}: {len(blocks)}")
    if not blocks:
        print("  FAIL  no <pre class=\"mermaid\"> blocks found")
        return False
    mmdc = shutil.which("mmdc")
    if not mmdc:
        print("  NOT RUN  mermaid-cli (`mmdc`) is not on PATH; no diagram was syntax-checked")
        for did, _b in blocks:
            print(f"    {did}: not_checked_no_mermaid_cli")
        return False
    chrome = next((c for c in (
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    ) if os.path.exists(c)), None)
    if not chrome:
        print("  NOT RUN  mermaid-cli found but no supported Chrome/Chromium binary; "
              "no diagram was syntax-checked")
        for did, _b in blocks:
            print(f"    {did}: not_checked_no_chrome")
        return False
    tmp = tempfile.mkdtemp(prefix="fb2-html-mermaid-")
    pconf = os.path.join(tmp, "puppeteer.json")
    with open(pconf, "w", encoding="utf-8") as fh:
        json.dump({"executablePath": chrome, "args": ["--no-sandbox"]}, fh)
    results = []
    try:
        for n, (did, raw) in enumerate(blocks):
            mmd = os.path.join(tmp, f"d{n}.mmd")
            svg = os.path.join(tmp, f"d{n}.svg")
            with open(mmd, "w", encoding="utf-8") as fh:
                fh.write(unescape_mermaid(raw) + "\n")
            try:
                proc = subprocess.run([mmdc, "-i", mmd, "-o", svg, "-p", pconf],
                                      capture_output=True, text=True, timeout=180)
                err = (proc.stderr or "") + (proc.stdout or "")
                if proc.returncode == 0 and os.path.exists(svg) and os.path.getsize(svg) > 0:
                    results.append((did, "validated", f"{os.path.getsize(svg)} bytes of SVG"))
                else:
                    detail = [ln.strip() for ln in err.splitlines()
                              if "rror" in ln or "xpecting" in ln][:2]
                    results.append((did, "INVALID", " | ".join(detail)[:240]
                                    or "unknown error"))
            except subprocess.TimeoutExpired:
                results.append((did, "not_checked_timeout", "mermaid-cli exceeded 180 s"))
            except OSError as e:
                results.append((did, f"not_checked_error: {e}", "mermaid-cli could not be run"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    n_ok = sum(1 for _d, r, _n in results if r == "validated")
    for did, res, note in results:
        print(f"    {did:58s} {res:20s} {note}")
    print(f"  validator: mermaid-cli {mmdc} with Chrome; {n_ok}/{len(blocks)} diagrams parsed "
          f"and rendered to SVG")
    return n_ok == len(blocks)


# ---------------------------------------------------------------- main

def generate(out_path, stamp=None):
    stamp = stamp or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    v = CorpusView()
    if v.load_errors:
        print("CORPUS LOAD FAILED — the document cannot be generated honestly:", file=sys.stderr)
        for e in v.load_errors:
            print("  -", e, file=sys.stderr)
        return 1, None
    text = build(v, stamp)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")
    print(f"Generated {out_path}")
    print(f"  {len(text.encode('utf-8'))} bytes; {len(v.index)} records; {len(v.links)} links; "
          f"{len(v.diagrams)} diagrams; {len(v.gaps)} declared gaps; "
          f"{v.gap_phrase_sites} absent-model sites")
    return 0, v


def main():
    ap = argparse.ArgumentParser(
        description="Generate the single-file end-to-end HTML engineering document.")
    ap.add_argument("--out", default=str(OUT_DEFAULT),
                    help="output path (default: docs/artifacts/reports/"
                         "e2e-engineering-document.html)")
    ap.add_argument("--check", action="store_true",
                    help="verify the generated document's integrity and determinism; "
                         "exit nonzero on any failure")
    ap.add_argument("--audit-guard", action="store_true",
                    help="audit guard-field coverage and scan for conformity claims")
    ap.add_argument("--validate-mermaid", action="store_true",
                    help="syntax-check every embedded Mermaid diagram with mermaid-cli")
    ap.add_argument("--root", default=None, help="repository root (default: inferred)")
    args = ap.parse_args()
    out_path = Path(args.out)

    if args.validate_mermaid:
        return 0 if validate_mermaid(out_path) else 1

    if args.audit_guard:
        v = CorpusView(root=args.root)
        if v.load_errors:
            print("CORPUS LOAD FAILED:", file=sys.stderr)
            for e in v.load_errors:
                print("  -", e, file=sys.stderr)
            return 1
        return 0 if audit_guard(v, out_path) else 1

    if args.check:
        v = CorpusView(root=args.root)
        if v.load_errors:
            print("CORPUS LOAD FAILED:", file=sys.stderr)
            for e in v.load_errors:
                print("  -", e, file=sys.stderr)
            return 1
        # One rebuild serves both purposes: it populates the gap and
        # absent-model-site counters the integrity check compares the file
        # against, and it is the independent second render the determinism check
        # byte-compares the file with. Building once keeps the two checks
        # consistent by construction instead of by coincidence.
        rebuilt = build(v, "1970-01-01T00:00:00Z")
        ok, failures = verify_html(v, out_path)
        if failures:
            print("INTEGRITY CHECK FAILED:")
            for f in failures[:60]:
                print("  -", f)
            if len(failures) > 60:
                print(f"  ... and {len(failures) - 60} more")
            return 1
        print("INTEGRITY CHECK PASSED: all required sections and sub-headings present; every "
              f"record in the artifact index anchored ({len(v.index)}); coverage matrix complete "
              f"({len(v.requirements())} requirements); every registry link present "
              f"({len(v.links)}); {len(v.gaps)} gaps registered; {v.gap_phrase_sites} "
              f"absent-model sites carry the mandated wording; every guard line matches the corpus.")
        return 0 if determinism(out_path, rebuilt) else 1

    rc, _v = generate(out_path)
    return rc


if __name__ == "__main__":
    sys.exit(main())
