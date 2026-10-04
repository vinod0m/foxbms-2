#!/usr/bin/env python3
"""Generate self-contained review packets for the foxBMS 2 ASPICE corpus.

WHAT THIS TOOL IS FOR
=====================

Two coverage dimensions of this corpus cannot move by authoring:

    human_approval            0/321
    actual_product_evidence   0/33

The first needs a named human who reads a record and signs it. The second needs
the product running on its own TMS570 hardware. Neither may be manufactured.

This tool makes the first one as cheap as it can honestly be made. It does NOT
perform it. It emits, per record, a packet containing everything a competent
reviewer needs in order to decide, and an EMPTY signature block for them to
fill in. The signature block is empty in every packet this tool writes and this
tool has no code path that fills one - see "THE ONE RULE" below.

A packet exists so that a reviewer SIGNS rather than RECONSTRUCTS. The failure
mode this is built against is a reviewer who opens a record, cannot tell what
has already been checked, and either redoes two hours of machine work or, worse,
approves a record whose unverifiable claim nobody flagged. So a packet states,
per record:

  * the identity, including that (profile, id) is the primary key;
  * the sha256 of the record's exact current bytes, so a signature provably
    refers to those bytes rather than a later revision;
  * the full record, verbatim, so no other file needs to be open;
  * the claims that could be false, derived from the record's own fields;
  * what is already machine-checked, and by which detector, so the reviewer
    does not redo it - with machine-verified / peer-reviewed-and-disputed /
    unexamined stated as three distinct states;
  * the record's own limitations and honesty fields, verbatim;
  * the specific judgement calls a machine cannot settle (2-4 per record);
  * a blank signature block.

THE ONE RULE
============

Nothing in this tool writes a value into `human_approval_status`, into any
approval field, into a signature, or into an execution verdict. The signature
block is emitted as a set of empty strings and a `decision` that is the empty
string. There is no default, no placeholder, no "suggested decision", and no
merge path that would let a tool-supplied value reach a signature.

Two structural consequences follow, and both are load-bearing:

  1. `packet.json` is deliberately NOT a corpus record. It carries no top-level
     `id`, `profile`, `artifact_type` or `source_refs`, because
     `docs/artifacts/reviews/` is one of the three roots `corpus.py`
     `iter_corpus_artifacts()` walks. A packet file shaped like a record would
     enter the artefact index and move coverage denominators - including
     `human_approval` and `source_grounding` - on nothing but the act of
     generating review material. `selftest` asserts this invisibility.

  2. Regeneration will not silently destroy a signature. If a packet on disk
     already carries a non-empty signature field, this tool refuses to
     overwrite it and says where to move the signed packet first. `--force`
     exists for the case where you have already archived it.

USAGE
=====

    python3 docs/artifacts/tools/make_review_packets.py            # write all
    python3 docs/artifacts/tools/make_review_packets.py --only FB2-SAF-FSR-000001
    python3 docs/artifacts/tools/make_review_packets.py --only-type finding
    python3 docs/artifacts/tools/make_review_packets.py --verify   # staleness
    python3 docs/artifacts/tools/make_review_packets.py --out /tmp/packets

`--verify` re-reads every packet on disk and reports, per packet: whether the
embedded record bytes still equal the file, whether the embedded digest still
matches, whether every path the packet names still exists, and whether the
signature block is still empty. It writes nothing and imports nothing from
`corpus.py`.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

PACKET_FORMAT = "foxbms2-review-packet/1.0.0"
GENERATOR = "docs/artifacts/tools/make_review_packets.py"

# The three roots corpus.py walks. Re-declared here rather than imported so the
# packets do not depend on corpus.py being importable, and so that a change to
# corpus.py's scan roots cannot silently change which records get packets.
RECORD_ROOTS = ("docs/artifacts/corpus",
                "docs/artifacts/reviews",
                "docs/artifacts/scenarios")
REGISTRY_PATH = "docs/artifacts/sources/source-registry.json"

SKIP_DIR_PARTS = {".work", "evaluator-only", "__pycache__", "packets", "signed"}

# Mirrors corpus.py ARTIFACT_TYPE_SCHEMAS / BASE_ONLY_TYPES. Kept local so this
# tool is independently re-derivable; `selftest` checks the two maps agree when
# corpus.py is importable, so a divergence is a failing test rather than a
# silently different packet.
TYPE_SCHEMAS = {
    "requirement": "requirement.schema.json",
    "design": "design.schema.json",
    "test_measure": "test_measure.schema.json",
    "execution": "execution.schema.json",
    "review": "review.schema.json",
    "scenario": "scenario.schema.json",
    "change": "change.schema.json",
    "implementation": "implementation.schema.json",
    "integration_plan": "integration_plan.schema.json",
    "qualification_test_plan": "qualification_test_plan.schema.json",
    "verification_summary": "verification_summary.schema.json",
    "unit_test_specification": "unit_test_specification.schema.json",
    "hardware_configuration_baseline": "hardware_configuration_baseline.schema.json",
    "hardware_verification_plan": "hardware_verification_plan.schema.json",
    "software_interface_specification": "software_interface_specification.schema.json",
    "verification_deficiency_register": "verification_deficiency_register.schema.json",
    "finding": "finding.schema.json",
    "deviation": "deviation.schema.json",
    "tara": "tara.schema.json",
    "item_definition": "item_definition.schema.json",
    "safety_concept": "safety_concept.schema.json",
    "stakeholder_need": "stakeholder_need.schema.json",
    "use_case": "use_case.schema.json",
    "project_plan": "project_plan.schema.json",
    "risk_register": "risk_register.schema.json",
    "measurement_plan": "measurement_plan.schema.json",
    "process_improvement": "process_improvement.schema.json",
    "process_record": "process_record.schema.json",
    "post_development_record": "post_development_record.schema.json",
    "controlled_vocabulary": "controlled_vocabulary.schema.json",
    "interpretation_guidelines": "interpretation_guidelines.schema.json",
}
BASE_ONLY_TYPES = {
    "hazard", "safety_goal", "safety_case", "safety_analysis",
    "parameter_registry", "assumption_registry", "link_registry",
}

# How many judgement calls a packet asks a reviewer to answer. The brief this
# tool implements asks for 2-4; the cap is 4 and the realised count is
# reported per packet and in the index, so a reader can see it is not drifting
# towards a checklist.
MAX_QUESTIONS = 4

# The signature fields, in the order they appear. All emitted empty.
SIGNATURE_FIELDS = (
    ("reviewer_name", "Reviewer name"),
    ("organisation", "Organisation"),
    ("role", "Role (must be independent of this record's author role)"),
    ("date", "Date (YYYY-MM-DD)"),
    ("decision", "Decision (`approve` / `approve-with-comments` / `reject`)"),
    ("comments", "Comments"),
    ("signature", "Signature"),
)

ARTEFACT_ID_RE = re.compile(r"^FB2-[A-Z]{2,3}-[A-Z]{2,3}-[0-9]{6}$")
ID_ANYWHERE_RE = re.compile(r"FB2-[A-Z]{2,3}-[A-Z]{2,3}-[0-9]{6}")
LINE_RANGE_RE = re.compile(r"^\s*(\d+)\s*(?:-\s*(\d+)\s*)?$")
PLACEHOLDER_HASHES = {"", "placeholder", "sha256:placeholder", "sha256:", "none", "null"}
PLAIN_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


# --------------------------------------------------------------------------
# small helpers


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def jload(p: Path):
    with p.open(encoding="utf-8") as f:
        return json.load(f)


def strip_sha(value) -> str:
    s = str(value or "").strip()
    return s[len("sha256:"):] if s.lower().startswith("sha256:") else s


def is_placeholder_hash(value) -> bool:
    return str(value or "").strip().lower() in PLACEHOLDER_HASHES


def fence_for(text: str) -> str:
    """A fence long enough that the text cannot close it early."""
    longest = 0
    for run in re.findall(r"`+", text):
        longest = max(longest, len(run))
    return "`" * max(3, longest + 1)


def md_cell(value) -> str:
    if value is None:
        return "-"
    s = str(value).replace("\r", " ").replace("\n", " ").replace("|", "\\|")
    s = s.replace("`", "'")
    return s if s.strip() else "-"


def md_blockquote(value) -> str:
    if value is None:
        return "_(absent)_"
    s = str(value).rstrip("\n")
    if not s.strip():
        return "_(empty)_"
    return "\n".join("> " + ln if ln.strip() else ">" for ln in s.split("\n"))


def shorten(text, n=240):
    s = " ".join(str(text or "").split())
    return s if len(s) <= n else s[: n - 1] + "\u2026"


def find_repo_root(start: Path) -> Path:
    p = start.resolve()
    for cand in [p] + list(p.parents):
        if (cand / "docs" / "artifacts" / "corpus").is_dir():
            return cand
    # fall back: docs/artifacts/tools -> repo root
    return p.parents[2] if len(p.parents) >= 2 else p


# --------------------------------------------------------------------------
# discovery


def discover_record_files(root: Path):
    """Every record-bearing JSON under the three roots corpus.py walks.

    A file is a record when it is a dict carrying `id`. Everything else is a
    registry container, which corpus.py also skips when it counts the record
    population, so the same rule is used here: the packets must cover the same
    321 records, not a different population.
    """
    out = []
    for rel_root in RECORD_ROOTS:
        base = root / rel_root
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*.json")):
            if SKIP_DIR_PARTS.intersection(p.parts):
                continue
            try:
                d = jload(p)
            except Exception:
                continue
            if not isinstance(d, dict) or not d.get("id"):
                continue
            out.append(p)
    return out


def load_links(root: Path):
    links = []
    trace = root / "docs" / "artifacts" / "traceability" / "link-registry"
    if trace.is_dir():
        for p in sorted(trace.rglob("links-*.json")):
            try:
                d = jload(p)
            except Exception:
                continue
            for l in (d.get("links") or []):
                if isinstance(l, dict) and l.get("link_id"):
                    links.append((p.relative_to(root).as_posix(), l))
    return links


def load_anchors(root: Path):
    p = root / REGISTRY_PATH
    if not p.exists():
        return {}, {}
    d = jload(p)
    by_id = {a.get("anchor_id"): a for a in (d.get("anchors") or []) if a.get("anchor_id")}
    return by_id, d


def load_assumptions_and_params(root: Path):
    """Ids that are real but are not artefacts: assumptions, parameters, links."""
    known = set()
    for rel in ("docs/artifacts/shared/assumption-registry.json",
                "docs/artifacts/corpus/synthetic_reference/shared/assumption-registry.json",
                "docs/artifacts/corpus/synthetic_reference/shared/parameter-registry.json"):
        p = root / rel
        if not p.exists():
            continue
        d = jload(p)
        for key, idkey in (("assumptions", "assumption_id"), ("parameters", "parameter_id")):
            for entry in (d.get(key) or []):
                if isinstance(entry, dict) and entry.get(idkey):
                    known.add(entry[idkey])
    return known


# --------------------------------------------------------------------------
# per-record live re-derivation


class Live:
    """Live facts about the tree, re-derived at generation time.

    Deliberately independent of corpus.py. A packet that says "machine-verified"
    on the strength of the same code it is asking a human to double-check would
    be circular; these checks are small enough to re-state, and corpus.py's own
    verdict is reported separately as a corroborating source rather than as the
    basis of the claim.
    """

    def __init__(self, root: Path):
        self.root = root
        self.index = {}          # (profile, id) -> (relpath, dict)
        self.id_index = {}       # id -> [ (profile, relpath) ]
        self.files = []
        for p in discover_record_files(root):
            d = jload(p)
            rel = p.relative_to(root).as_posix()
            prof = d.get("profile", "unknown")
            key = (prof, d["id"])
            if key not in self.index:
                self.index[key] = (rel, d)
                self.files.append((rel, p, d))
            self.id_index.setdefault(d["id"], []).append((prof, rel))
        self.links = load_links(root)
        self.link_ids = {l.get("link_id") for _rel, l in self.links}
        self.anchors, self.anchor_registry = load_anchors(root)
        self.known_ids = load_assumptions_and_params(root)
        self.review_records = []
        rdir = root / "docs" / "artifacts" / "reviews" / "records"
        if rdir.is_dir():
            for p in sorted(rdir.glob("*.json")):
                try:
                    self.review_records.append((p.relative_to(root).as_posix(), jload(p)))
                except Exception:
                    continue
        self.review_findings = []
        fdir = root / "docs/artifacts/reviews/findings"
        if fdir.is_dir():
            for p in sorted(fdir.glob("*.json")):
                try:
                    d = jload(p)
                except Exception:
                    continue
                if isinstance(d, dict) and d.get("artifact_id"):
                    self.review_findings.append((p.relative_to(root).as_posix(), d))
        self.registry_rel = REGISTRY_PATH
        self.registry_sha = None
        rp = root / REGISTRY_PATH
        if rp.exists():
            self.registry_sha = sha256_bytes(rp.read_bytes())
        self._schema_cache = {}
        self._validator_error = None

    # -- reference resolution ------------------------------------------------

    def resolves(self, ref: str, profile: str):
        """(resolves, note). Profile-scoped first, then profile-free ids."""
        if not ref:
            return False, "empty reference"
        if (profile, ref) in self.index:
            return True, "resolves to a record in this profile"
        if ref in self.anchors:
            return True, "resolves to a source anchor in " + REGISTRY_PATH
        if ref in self.known_ids:
            return True, "resolves to an assumption or parameter in a shared registry"
        holders = self.id_index.get(ref)
        if holders:
            profs = sorted({h[0] for h in holders})
            if profile in profs:
                return True, "resolves to a record in this profile"
            return False, (f"exists only in profile(s) {profs}; a record in profile "
                           f"{profile!r} may not reference it unqualified")
        if ref in self.link_ids:
            return True, "resolves to a link in the link registry"
        if ARTEFACT_ID_RE.match(ref):
            return False, "shaped like an artefact id but no such record exists in any profile"
        return False, "not an artefact id, anchor, link, assumption or parameter"

    # -- schema --------------------------------------------------------------

    def schema_for(self, atype: str):
        if atype in TYPE_SCHEMAS:
            return TYPE_SCHEMAS[atype]
        if atype in BASE_ONLY_TYPES:
            return "artifact-base.schema.json"
        return None

    def schema_check(self, atype: str, record: dict):
        """(ok, schema_name, first_error). None schema_name means 'no schema'."""
        name = self.schema_for(atype)
        if not name:
            return None, None, None
        sp = self.root / "docs" / "artifacts" / "schemas" / name
        if not sp.exists():
            return False, name, f"schema file {name} not found"
        key = ("v", name)
        if key not in self._schema_cache:
            try:
                from jsonschema import Draft202012Validator
                from referencing import Registry, Resource
            except Exception as e:      # pragma: no cover - env dependent
                self._schema_cache[key] = None
                self._validator_error = str(e)
                return None, name, f"jsonschema/referencing unavailable: {e}"
            schema = jload(sp)
            # Every entry must be a `Resource`, not a bare dict: `Registry` looks
            # the retrieved value up and calls `.contents` on it, so a raw dict
            # under any one of the keys raises AttributeError at validation time
            # rather than at registration time. Three keys per schema so that a
            # sibling's relative `$ref` resolves however it is written.
            resources = {}
            for other in sorted((self.root / "docs" / "artifacts" / "schemas").glob("*.schema.json")):
                try:
                    s = jload(other)
                except Exception:
                    continue
                res = Resource.from_contents(s)
                resources[other.name] = res
                resources[f"https://foxbms2.softwaredevlabs.org/schemas/{other.name}"] = res
                resources[f"file://{self.root / 'docs' / 'artifacts' / 'schemas' / other.name}"] = res
            registry = Registry().with_resources(list(resources.items()))
            self._schema_cache[key] = Draft202012Validator(schema, registry=registry)
        validator = self._schema_cache[key]
        if validator is None:
            return None, name, "validator unavailable"
        errors = sorted(validator.iter_errors(record), key=lambda e: list(e.path))
        if errors:
            e = errors[0]
            where = "/".join(str(x) for x in e.path) or "<root>"
            return False, name, f"{where}: {e.message}"
        return True, name, None

    # -- file / anchor facts -------------------------------------------------

    def file_sha(self, rel: str):
        p = self.root / rel
        if not p.exists():
            return None
        return sha256_bytes(p.read_bytes())

    def file_lines(self, rel: str):
        p = self.root / rel
        if not p.exists():
            return None
        try:
            return len(p.read_text(encoding="utf-8", errors="replace").splitlines())
        except Exception:
            return None

    def anchor_state(self, anchor_id: str):
        """Re-derive, per anchor, the three facts the provenance gate checks.

        The registry holds four kinds of anchor and they need different
        treatment, because they make different kinds of claim:

          location.path present          a file in this repository. Fully checkable.
          location.external_file        a file in a SEPARATE repository. The
                                        corpus cannot see it; the anchor says so
                                        itself and records content_hash as the
                                        literal 'unresolved'.
          location.url_or_path           a fetched URL. The hash pins the
                                        retrieval, not a stable artefact.
          location.file_or_executable   a test file. In this repository and
                                        checkable, though the key is not `path`,
                                        so the provenance gate does not bounds-check
                                        it. Re-derived here anyway, and the
                                        difference is reported rather than hidden.

        Collapsing all four into "unverifiable" would tell a reviewer less than
        the record already says, so each is reported in its own class.
        """
        a = self.anchors.get(anchor_id)
        if a is None:
            return {"anchor_id": anchor_id, "resolves": False, "anchor_class": "absent",
                    "note": "no such anchor in sources/source-registry.json"}
        loc = a.get("location") or {}
        rel = loc.get("path")
        out = {
            "anchor_id": anchor_id,
            "resolves": True,
            "path": rel,
            "line_range": loc.get("line_range"),
            "symbol": loc.get("symbol"),
            "content_hash": a.get("content_hash"),
            "source_type": a.get("source_type"),
            "repository": loc.get("repository"),
            "commit": loc.get("commit"),
            "retrieval_date": a.get("retrieval_date"),
            "has_correction": bool(a.get("correction")),
            "hash_note": a.get("hash_note"),
            "hash_status": a.get("hash_status"),
        }
        if rel:
            out["anchor_class"] = "repository_file"
        elif loc.get("external_file"):
            out["anchor_class"] = "external_repository_file"
            out["external_file"] = loc.get("external_file")
            out["external_repository"] = loc.get("external_repository")
        elif loc.get("url_or_path"):
            out["anchor_class"] = "fetched_url"
            out["url_or_path"] = loc.get("url_or_path")
            out["section_anchor"] = loc.get("section_anchor")
        elif loc.get("file_or_executable"):
            out["anchor_class"] = "repository_file_under_a_non_path_key"
            out["file_or_executable"] = loc.get("file_or_executable")
            rel = loc.get("file_or_executable")
            out["path"] = rel
        else:
            out["anchor_class"] = "unknown_shape"
        if not rel:
            out["verifiable"] = False
            out["note"] = {
                "external_repository_file":
                    "names a file in a separate repository, so nothing here can check it; "
                    "the anchor records content_hash as the literal "
                    f"{a.get('content_hash')!r} rather than claiming a digest",
                "fetched_url":
                    "names a fetched URL, not a file in this tree; its content_hash pins "
                    "one retrieval and cannot be re-checked here",
                "unknown_shape":
                    "this anchor's location names no file this tool can resolve",
            }.get(out["anchor_class"], "no repository file named")
            return out
        fp = self.root / rel
        if not fp.exists():
            out["verifiable"] = False
            out["file_exists"] = False
            out["note"] = f"anchor names {rel}, which does not exist in this repository"
            return out
        out["file_exists"] = True
        actual = self.file_sha(rel)
        recorded = a.get("content_hash")
        if is_placeholder_hash(recorded) or str(recorded).strip().lower() == "unresolved":
            out["hash_state"] = ("placeholder" if is_placeholder_hash(recorded)
                                 else "declined")
            out["hash_matches_now"] = None
        else:
            out["hash_matches_now"] = (strip_sha(recorded) == actual)
            out["hash_state"] = "match" if out["hash_matches_now"] else "mismatch"
            out["actual_sha256"] = actual
        lr = loc.get("line_range")
        if lr is not None:
            m = LINE_RANGE_RE.match(str(lr))
            n = self.file_lines(rel)
            if not m:
                out["line_range_state"] = "unparseable"
            else:
                start = int(m.group(1))
                end = int(m.group(2)) if m.group(2) else start
                out["line_range_state"] = ("in_bounds" if (start >= 1 and start <= end
                                                            and n is not None and end <= n)
                                           else "out_of_bounds")
                out["file_line_count"] = n
        sym = loc.get("symbol")
        if sym is not None:
            if PLAIN_IDENTIFIER_RE.match(str(sym)):
                text = (self.root / rel).read_text(encoding="utf-8", errors="replace")
                out["symbol_state"] = ("present" if re.search(
                    r"\b" + re.escape(str(sym)) + r"\b", text) else "absent")
            else:
                out["symbol_state"] = "prose_not_checkable"
        out["verifiable"] = True
        out["note"] = "checked against the file on disk at packet generation time"
        return out

    # -- reviews / findings --------------------------------------------------

    def reviews_covering(self, profile: str, aid: str):
        out = []
        for rel, d in self.review_records:
            if d.get("profile") != profile:
                continue
            for e in (d.get("reviewed_ids") or []):
                if isinstance(e, dict) and e.get("artifact_id") == aid:
                    out.append((rel, d, e))
        for rel, l in self.links:
            if l.get("relation_type") != "reviewed_by":
                continue
            if l.get("profile") != profile or l.get("target_id") != aid:
                continue
            rid = l.get("source_id")
            rd = next((x for _r, x in self.review_records if x.get("id") == rid), None)
            if rd is None:
                out.append((None, {"id": rid, "_link_only": True}, None))
            elif not any(r == rel for r, _dd, _e in out):
                out.append((rel, rd, None))
        return out

    def findings_about(self, aid: str):
        out = []
        for rel, f in self.review_findings:
            if f.get("artifact_id") == aid:
                out.append((rel, f))
        for rel, rd in self.review_records:
            for f in (rd.get("findings") or []):
                if isinstance(f, dict) and f.get("artifact_id") == aid:
                    out.append((rel, f))
        return out

    def links_touching(self, profile: str, aid: str):
        out = []
        for rel, l in self.links:
            if l.get("profile") != profile:
                continue
            if l.get("source_id") == aid or l.get("target_id") == aid:
                out.append((rel, l))
        return out


# --------------------------------------------------------------------------
# claims to verify


def _claim(cid, kind, statement, machine, judgement, evidence):
    return {"claim_id": cid, "claim_class": kind, "statement": statement,
            "machine_state": machine, "judgement_needed": judgement,
            "evidence_in_packet": evidence}


def collect_id_refs(record: dict, self_id: str):
    """Every id-shaped string the record states, with the field it sits in.

    Walked over the record's own values only. `revision_history[].description`
    is included: prose there names ids too, and a reviewer is entitled to know
    a revision note cites a record that no longer exists.
    """
    found = []

    def walk(node, path):
        if isinstance(node, dict):
            for k, v in node.items():
                if k == "revision_history":
                    walk(v, path + ".revision_history")
                else:
                    walk(v, path + "." + k)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]")
        elif isinstance(node, str):
            s = node.strip()
            if ARTEFACT_ID_RE.match(s) and s != self_id:
                found.append((path, s))

    walk(record, "")
    seen, out = set(), []
    for path, ref in found:
        if (path, ref) in seen:
            continue
        seen.add((path, ref))
        out.append((path, ref))
    return out


def claims_for(live: Live, profile: str, aid: str, atype: str, record: dict):
    claims = []
    n = [0]

    def nid(stem):
        n[0] += 1
        return f"C{n[0]:02d}-{stem}"

    # 1. source anchors -- every record, because source_refs is a base field.
    for a in (record.get("source_refs") or []):
        st = live.anchor_state(a)
        bits = [f"anchor class `{md_cell(st.get('anchor_class'))}`"]
        if st.get("path"):
            bits.append(f"path `{md_cell(st['path'])}`")
        if st.get("external_file"):
            bits.append(f"external_file `{md_cell(st['external_file'])}` "
                        f"(repository `{md_cell(st.get('external_repository'))}`, "
                        "not present in this tree)")
        if st.get("url_or_path"):
            bits.append(f"url_or_path `{md_cell(st['url_or_path'])}`")
        if st.get("line_range"):
            bits.append(f"line_range `{md_cell(st.get('line_range'))}`")
        bits.append(f"content_hash `{md_cell(strip_sha(st.get('content_hash')) or st.get('content_hash'))}`")
        if st.get("symbol"):
            bits.append(f"symbol `{md_cell(st.get('symbol'))}`")
        if not st.get("resolves"):
            machine = f"anchor does NOT resolve: {st.get('note')}"
        elif not st.get("verifiable"):
            machine = ("anchor resolves in the registry but claims nothing checkable in this "
                       f"repository: {st.get('note')}")
        else:
            checks = [f"file {'exists' if st.get('file_exists') else 'ABSENT'}"]
            checks.append(f"hash {st.get('hash_state') or 'not checked'}")
            checks.append(f"line_range {st.get('line_range_state') or 'not declared'}")
            checks.append(f"symbol {st.get('symbol_state') or 'not declared'}")
            machine = "; ".join(checks) + " (re-derived at packet generation time)"
        extra = ""
        if st.get("hash_note"):
            extra = (f" The registry's own note on this hash: \"{shorten(st['hash_note'], 400)}\"")
        claims.append(_claim(
            nid("anchor"), "source_anchor",
            f"This record cites anchor {a}, which records "
            + "; ".join(bits) + ".",
            machine + extra,
            "Whether that attribution is the right reading of the source. A digest proves the "
            "bytes have not changed; it does not prove this record uses them correctly, and "
            "for an anchor with no local file it proves nothing at all here.",
            "The anchor's own correction and hash_note blocks are in "
            + REGISTRY_PATH + " and the full record is in section 3."))

    # 2. id references the record states
    for path, ref in collect_id_refs(record, aid):
        ok, note = live.resolves(ref, profile)
        claims.append(_claim(
            nid("xref"), "traceability_edge",
            f"`{path}` names {ref}.",
            ("resolves" if ok else "DOES NOT RESOLVE") + f": {note}",
            "Whether {ref} is the record this field should point at. Resolution is not "
            "correctness: a field can resolve and still name the wrong record.".format(ref=ref),
            "The record verbatim in section 3. The link registry is separate from this "
            "field and may disagree, and that disagreement is itself part of what is being "
            "reviewed."))

    # 3. standards mappings
    for i, m in enumerate(record.get("standards_mappings") or []):
        if not isinstance(m, dict):
            continue
        claims.append(_claim(
            nid("std"), "standards_mapping",
            f"This record maps to {m.get('standard_id')} {m.get('reference')} with status "
            f"`{m.get('status')}` on the grounds: {md_cell(m.get('rationale'))}",
            "no machine check: clause selection is not verifiable from the repository",
            "Whether that clause is the right obligation for this work product and whether "
            "`{s}` is the right status.".format(s=m.get("status")),
            "The record verbatim in section 3."))

    # 4. evidence: logs and evidence_files
    for entry in (record.get("logs") or []):
        if not isinstance(entry, dict) or not entry.get("file"):
            continue
        rel = str(entry["file"])
        exists = (live.root / rel).exists()
        rec_h = entry.get("hash")
        state = "file ABSENT"
        if exists:
            actual = live.file_sha(rel)
            if is_placeholder_hash(rec_h):
                state = "file exists; recorded hash is a PLACEHOLDER, so identity unverified"
            elif strip_sha(rec_h) == actual:
                state = "file exists; hash matches the bytes on disk now"
            else:
                state = (f"file exists; hash MISMATCH (recorded {strip_sha(rec_h)[:16]}..., "
                         f"actual {str(actual)[:16]}...)")
        claims.append(_claim(
            nid("log"), "evidence_file",
            f"`logs[]` names {rel} as captured output, hash `{md_cell(rec_h)}`.",
            state,
            "Whether this log is the output of the run this record describes, and whether "
            "it shows what the record says it shows. The hash proves the file has not "
            "changed; it does not prove the file is about this run.",
            "The record verbatim in section 3."))
    for entry in (record.get("evidence_files") or []):
        if not isinstance(entry, str):
            continue
        if entry.startswith("<"):
            continue
        exists = (live.root / entry).exists()
        claims.append(_claim(
            nid("ev"), "evidence_file",
            f"`evidence_files[]` names {entry} as supporting evidence.",
            "file exists" if exists else "file ABSENT",
            "Whether that file supports the claim it is offered for.",
            "The record verbatim in section 3."))

    # 5. type-specific claims
    if atype == "execution":
        kind = record.get("execution_kind")
        outcome = record.get("outcome")
        agg = record.get("aggregate_outcome")
        hw = (record.get("environment") or {}).get("hardware")
        claims.append(_claim(
            nid("exec"), "execution_classification",
            f"This record declares execution_kind `{kind}`, outcome `{outcome}`, "
            f"aggregate_outcome `{agg}`, on hardware `{md_cell(hw)}`, for test measure "
            f"`{record.get('test_measure_id')}`.",
            ("`actual_target_hardware_run` is the only kind that counts as product-hardware "
             "evidence. `actual_host_run`/`actual_simulation_run` are real executions of the "
             "product's code on developer infrastructure. `none` means no run was performed. "
             f"This record's kind is `{kind}`."
             + ("" if kind != "actual_target_hardware_run"
                else " A target run is additionally required by the corpus rule "
                     "`execution_kind_classifier` to carry an existing log, input hashes, "
                     "output hashes, evidence_refs and an origin of source_observed; "
                     "those conditions are listed separately below.")),
            "Whether this outcome is a legitimate basis for the verification claim its test "
            "measure makes. A green run on a host is not evidence about the MCU, and only "
            "the domain owner can say whether the measure's acceptance criteria are met at all.",
            "The record verbatim in section 3. The test measure it names has its own packet."))
        tm = record.get("test_measure_id")
        for t in _expand_id_ranges(tm):
            ok, note = live.resolves(t, profile)
            claims.append(_claim(
                nid("tms"), "traceability_edge",
                f"`test_measure_id` names {t}.",
                ("resolves" if ok else "DOES NOT RESOLVE") + f": {note}",
                "Whether this execution is the execution of that measure.",
                "The record verbatim in section 3."))
        ts = record.get("timestamps") or {}
        claims.append(_claim(
            nid("time"), "execution_metadata",
            f"`timestamps` = {json.dumps(ts, sort_keys=True)}",
            ("start and end present" if ts.get("start") and ts.get("end")
             else "start or end ABSENT"),
            "Whether the recorded interval is the real duration of the run. Duration is not "
            "verifiable from a file's contents.",
            "The record verbatim in section 3."))
        if kind == "actual_target_hardware_run":
            claims.append(_claim(
                nid("tgt"), "product_evidence",
                "This record claims a run on the product's own hardware.",
                "origin=`{}`; logs={}; input_hashes={}; output_hashes={}; evidence_refs={}".format(
                    record.get("origin"), len(record.get("logs") or []),
                    len(record.get("input_hashes") or {}),
                    len(record.get("output_hashes") or {}),
                    len(record.get("evidence_refs") or [])),
                "Whether the hardware really was the product's own. This is the single "
                "judgement the corpus cannot make for itself and the one it must never "
                "guess: a host run recorded as a target run is the most damaging error "
                "this corpus could contain.",
                "The record verbatim in section 3."))

    if atype == "test_measure":
        crit = record.get("acceptance_criteria") or record.get("acceptance") or []
        claims.append(_claim(
            nid("oracle"), "verification_oracle",
            f"This measure declares {len(crit)} acceptance criterion/criteria and method "
            f"`{record.get('verification_method') or record.get('method') or 'not stated'}`.",
            "count only; whether a criterion is decidable is not machine-checkable",
            "Whether the criterion would actually FAIL if the property it names were "
            "violated. A criterion that cannot fail is the defect this corpus's own "
            "FB2-REV-FND-000042 is about.",
            "The record verbatim in section 3."))

    if atype == "review":
        for e in (record.get("reviewed_ids") or []):
            if not isinstance(e, dict):
                continue
            rid = e.get("artifact_id")
            holder = live.index.get((profile, rid))
            state = "reviewed id does not resolve"
            if holder:
                actual = live.file_sha(holder[0])
                if is_placeholder_hash(e.get("digest")):
                    state = ("digest is a PLACEHOLDER (permitted only with a note); "
                             "the reviewed bytes are not identified")
                elif strip_sha(e.get("digest")) == actual:
                    state = (f"resolves to {holder[0]}; recorded digest matches that file "
                             f"now, so this review provably examined those bytes")
                else:
                    state = (f"resolves to {holder[0]}; digest MISMATCH - the reviewed bytes "
                             f"have changed since the review")
            claims.append(_claim(
                nid("rev"), "review_coverage",
                f"This review states it reviewed {rid} at revision `{e.get('revision')}` "
                f"with digest `{md_cell(strip_sha(e.get('digest')))}`.",
                state,
                "Whether the conclusion this review reached about that record is correct. "
                "A matching digest proves the bytes; it does not prove the reading.",
                "The review's own findings and dispositions, listed under what is already checked."))
        ri = record.get("reviewer_identity") or {}
        claims.append(_claim(
            nid("rev-id"), "review_independence",
            f"reviewer_identity = {json.dumps({k: v for k, v in ri.items() if k != 'note'}, sort_keys=True)}",
            "declared in the record; independence is not machine-verifiable",
            "Whether this reviewer was independent enough for the claim being made. A single "
            "AI session reviewing its own output is not independence, and the record says so.",
            "The record verbatim in section 3, including the reviewer's own note."))

    if atype == "finding":
        disp = record.get("disposition")
        sev = record.get("severity")
        cat = record.get("category")
        rv = record.get("reverification") or {}
        rv_paths = [str(x) for x in (rv.get("method") or "").split() if "/" in x]
        rv_state = "no reverification block"
        if rv:
            exists = [p_ for p_ in rv_paths if (live.root / p_).exists()]
            rv_state = (f"reverification dated {rv.get('date')} by {rv.get('raised_by')}; "
                        f"method {rv.get('method')!r}; "
                        + (f"{len(exists)}/{len(rv_paths)} named method path(s) exist"
                           if rv_paths else "no path named in method"))
        names_fix = bool(re.search(r"FB2-[A-Z]{2,3}-[A-Z]{2,3}-[0-9]{6}",
                                   str(record.get("resolution") or "")))
        claims.append(_claim(
            nid("fnd"), "finding_classification",
            f"This finding is recorded as severity `{sev}`, category `{cat}`, disposition "
            f"`{disp}`. Its resolution text names a corpus id: {names_fix}.",
            f"reverification state: {rv_state}. Per "
            "docs/artifacts/governance/finding-disposition-vocabulary.md, `resolved` asserts "
            "the condition NO LONGER HOLDS and must name what fixed it; `accepted`, "
            "`deferred` and `in_progress` all assert the condition STILL HOLDS.",
            "Whether the defect class is right and whether the stated resolution was actually "
            "verified. A `resolved` finding whose condition still holds is worse than an "
            "`accepted` one, because it tells a reader the work is finished.",
            "The record verbatim in section 3, including the resolution and disposition_note prose."))

    if atype == "deviation":
        af = record.get("affected_file")
        sym = record.get("affected_symbol")
        lines = record.get("affected_lines")
        exists = bool(af) and (live.root / str(af)).exists()
        sym_state = "not checked"
        if sym and exists:
            text = (live.root / str(af)).read_text(encoding="utf-8", errors="replace")
            sym_state = ("present" if re.search(r"\b" + re.escape(str(sym)) + r"\b", text)
                         else "ABSENT")
        claims.append(_claim(
            nid("dev"), "source_observation",
            f"This deviation records an observation in {md_cell(af)} at symbol "
            f"`{md_cell(sym)}` lines {md_cell(lines)}.",
            f"file {'exists' if exists else 'ABSENT'}; symbol {sym_state}",
            "Whether what this deviation asserts about the source is a fair reading of it. "
            "A deviation is an observation, so a wrong observation is a wrong record.",
            "The record verbatim in section 3, including evidence_quote."))

    if atype in ("requirement", "design", "item_definition", "software_interface_specification"):
        alloc = record.get("safety_allocation") or {}
        scope = record.get("asil_allocation_scope") or {}
        if alloc:
            claims.append(_claim(
                nid("asil"), "classification",
                f"This record carries safety_allocation.asil = `{alloc.get('asil')}`"
                + (f" and a safety_goal_ref of `{alloc.get('safety_goal_ref')}`."
                   if alloc.get("safety_goal_ref") else " with no safety_goal_ref."),
                ("`asil_allocation_scope.classification_kind` = "
                 f"`{scope.get('classification_kind')}`; asserts a determination for the real "
                 f"product: {scope.get('is_a_determination_for_the_real_product')}"
                 if scope else
                 "NO `asil_allocation_scope` block, so the classification is presented "
                 "unqualified. On an `as_is` profile record that is a reconstruction "
                 "presented as a determination, and is exactly what an independent audit "
                 "already raised against this corpus."),
                "Whether presenting this classification this way is acceptable. On an as_is "
                "record a reader can take an ASIL value as a statement about the real product, "
                "and no machine can tell whether that misreading has happened.",
                "The record verbatim in section 3, including the whole asil_allocation_scope block."))

    if atype == "change":
        claims.append(_claim(
            nid("chg"), "change_decision",
            f"This change record states decision `{md_cell((record.get('decision') or {}).get('disposition'))}` "
            f"by `{md_cell((record.get('decision') or {}).get('made_by'))}`, with "
            f"{len(record.get('required_updates') or [])} required update(s) and "
            f"{len(record.get('reverification_selection') or [])} reverification selection(s).",
            "ids resolve (listed above); no machine check on the decision itself",
            "Whether the recorded decision reflects what a real change process would decide, "
            "and whether the required updates are the right ones.",
            "The record verbatim in section 3."))

    return claims


def _expand_id_ranges(value):
    out = []
    for part in re.split(r"[,\s]+", str(value or "")):
        part = part.strip()
        if not part:
            continue
        m = re.fullmatch(r"(.*-)(\d+)\.\.(\d+)", part)
        if m:
            for i in range(int(m.group(2)), int(m.group(3)) + 1):
                out.append(f"{m.group(1)}{i:06d}")
        elif ARTEFACT_ID_RE.match(part):
            out.append(part)
    return out


# --------------------------------------------------------------------------
# questions for the human reviewer

ROLE_DUTY = {
    "safety_engineer": "hazard analysis, safety goals, FSR/TSR allocation, safety analyses, the safety case",
    "system_engineer": "stakeholder needs, system requirements, architecture, HSI, validation",
    "hw_engineer": "hardware requirements, architecture, detailed design, hardware safety analysis",
    "sw_engineer": "software requirements, architecture, detailed design, implementation mapping, unit verification",
    "verification_engineer": "verification measures, execution classification, trace coverage, evidence handling",
    "quality_engineer": "verification and quality process records and their evidence",
    "cybersecurity_engineer": "cybersecurity requirements, attack surface, authentication and integrity verification",
    "traceability_engineer": "the link graph, schemas, exports, metrics and deterministic tooling",
    "data_quality_engineer": "the measurable quality claims this corpus makes about its own numbers",
    "project_manager": "project planning, schedule, resources, risk",
    "safety_manager": "safety management, safety culture, escalation",
    "verification_lead": "the verification strategy and the independence of verification",
    "configuration_manager": "configuration and change control",
    "change_manager": "change management",
    "integration_engineer": "integration planning and interfaces",
    "sys_engineer": "system engineering",
}


def questions_for(live: Live, profile: str, aid: str, atype: str, record: dict,
                  claims, anchor_states, review_state, limitation_text):
    """The judgement calls a machine cannot settle. Ranked, then capped.

    Every question below is derived from a field OF THIS RECORD. Nothing here is
    a generic checklist item: if the record does not carry the field, the
    question does not appear. The cap is MAX_QUESTIONS (4) because a reviewer
    handed a long list reads none of it; anything past the cap is returned
    separately rather than dropped.

    Returns (shown, suppressed).
    """
    qs = []

    def add(prio, group, question, why, answerable):
        qs.append({"priority": prio, "group": group, "question": question,
                   "why_this_needs_a_human": why,
                   "what_in_this_packet_bears_on_it": answerable})

    owner = record.get("owner_role")
    domain = record.get("engineering_domain")
    duty = ROLE_DUTY.get(owner, "the work this record belongs to")
    subject = record.get("statement") or record.get("title") or "this record's subject"
    add(1, "engineering validity",
        f"As the {owner} for this {domain} record, do you agree that \""
        f"{shorten(subject, 180)}\" is a correct and complete statement of {duty}?",
        "Correctness of engineering content is not derivable from the repository. The corpus "
        "can prove the record is well-formed and internally consistent; it cannot prove the "
        "engineering is right.",
        "The record verbatim in section 3.")

    origin = record.get("origin")
    if origin == "source_observed":
        add(20, "provenance honesty",
            f"This record is labelled origin=`source_observed`: it claims its content was read "
            f"out of the foxBMS 2 source rather than constructed. Reading the anchors listed "
            f"under claims, is that true - and is the record a faithful statement of what those "
            f"files actually say?",
            "A file's bytes and a record's reading of them can disagree, and only the reader "
            "who looked can say which is wrong.",
            "Claims section, source anchors; and the record's own provenance_note.")
    elif origin == "derived":
        add(20, "provenance honesty",
            "This record is labelled origin=`derived`, not observed. Is the derivation "
            "reproducible from what it names, or does it assert more than its sources carry?",
            "Derivation is a human act. The corpus can check that the named sources exist; it "
            "cannot check that the conclusion follows from them.",
            "Claims section; provenance_note; assumption_refs.")
    elif origin == "synthetic":
        add(20, "provenance honesty",
            "This record is a synthetic fixture of the hypothetical reference project this "
            "corpus also declares. Is anything in it readable as a claim about the real "
            "foxBMS 2 product?",
            "Contamination between the fictional project and the real one is the failure this "
            "corpus's whole as_is/synthetic split exists to prevent, and it is a reading "
            "failure, not a data error.",
            "The record's profile and corpus_boundaries block.")

    # type-specific, highest information value first
    if atype == "execution":
        kind = record.get("execution_kind")
        hw = (record.get("environment") or {}).get("hardware")
        if kind == "actual_target_hardware_run":
            add(5, "product evidence",
                "This record claims a run on the product's own hardware. Was it? Name the "
                "board, the firmware image and the person who ran it.",
                "This is the judgement the corpus is least able to make and most exposed to. "
                "A host run recorded as a target run is the single most damaging error this "
                "corpus could contain, and no digest or log proves hardware identity.",
                "section 3: environment.hardware, input/output hashes and the logs listed.")
        else:
            add(5, "execution classification",
                f"This is `{kind}`, on `{md_cell(hw)}`. Given that, does the outcome support "
                f"the verification claim its test measure ({record.get('test_measure_id')}) "
                f"makes?",
                "Whether a given kind of run is sufficient evidence for a given acceptance "
                "criterion is a domain judgement. A host run can be perfectly good evidence "
                "for driver logic and no evidence at all for register timing.",
                "section 3: the environment block. The test measure has its own packet.")
        if record.get("outcome") == "blocked" or kind == "none":
            add(15, "gap honesty",
                "This record records that no run happened. Is the stated blocker the real "
                "one, and is the gap still open today?",
                "Blockers move. A record that says 'blocked' for a reason that has since been "
                "removed understates the corpus's real gaps.",
                "notes and limitations in section 3.")
    elif atype == "test_measure":
        ncrit = len(record.get("acceptance_criteria") or record.get("acceptance") or [])
        add(5, "oracle strength",
            f"This measure declares {ncrit} acceptance criterion/criteria. For each, would the "
            f"criterion actually FAIL if the property it names were violated?",
            "A test that cannot fail is indistinguishable from a passing test. This corpus "
            "measured 53 such files in its own suite and recorded it as "
            "FB2-REV-FND-000042.",
            "acceptance_criteria in section 3.")
    elif atype == "finding":
        disp = record.get("disposition")
        add(5, "finding classification",
            f"This finding is `{disp}`. Under "
            "docs/artifacts/governance/finding-disposition-vocabulary.md, is that the right "
            "member for the condition as it stands now?",
            "The vocabulary is normative and the six members assert different facts about "
            "whether the defect is still live. Only someone who knows the current state can "
            "choose correctly.",
            "resolution and reverification blocks in section 3, plus docs/artifacts/governance/finding-disposition-vocabulary.md.")
        if disp in ("accepted", "deferred", "in_progress", "partial"):
            add(12, "ownership of the remainder",
                "For the part that is still open: is the named owner real, and is the named "
                "trigger for revisiting it real?",
                "A deferred finding with no live trigger is indistinguishable from an "
                "abandoned one.",
                "resolution text in the record.")
        if disp == "resolved":
            add(12, "closure",
                "Does the named fix actually close the condition, on the current tree?",
                "`resolved` is a claim about the world. Re-deriving it is work no digest does.",
                "resolution text; the named record id or rule.")
    elif atype == "review":
        add(5, "review conclusion",
            "This review reached conclusions about the records it covers. Are those "
            "conclusions correct?",
            "A review is an argument. Its digests prove it read the bytes; nothing proves it "
            "read them correctly.",
            "The findings and dispositions listed under what is already checked.")
        ri = record.get("reviewer_identity") or {}
        add(10, "independence",
            f"This review was performed by {md_cell(ri.get('model') or ri.get('role'))} in "
            f"session `{md_cell(ri.get('session_id'))}`. Is that independence sufficient for "
            "the weight this review's conclusions are being given?",
            "Independence is a governance judgement. A single automated session reviewing its "
            "own output is not organisational independence, and the corpus says so itself.",
            "reviewer_identity in section 3, including its note.")
    elif atype == "requirement":
        add(8, "requirement quality",
            "Are the acceptance criteria complete and decidable - could a verifier say with "
            "certainty whether this requirement is met?",
            "An undecidable requirement cannot be verified, and the corpus cannot tell an "
            "undecidable requirement from a merely terse one.",
            "acceptance_criteria and verification_approach in the record.")
    elif atype == "deviation":
        add(8, "observation accuracy",
            "Is what this deviation asserts about the named source a fair reading of that "
            "source?",
            "A deviation is an observation. A wrong observation is a wrong record, and the "
            "evidence_quote is the only thing standing behind it.",
            "affected_file/symbol/lines and evidence_quote in section 3.")
    elif atype in ("design", "item_definition", "software_interface_specification"):
        add(8, "design adequacy",
            "Does this design specify enough for an implementer to build it without inventing "
            "a decision?",
            "Design adequacy is judged by building it, or by reading it as an implementer "
            "would. No validator measures it.",
            "The record verbatim in section 3.")
    elif atype in ("change", "deviation_note"):
        pass

    # conditional: something the machine found and cannot resolve
    unverifiable = [s for s in anchor_states
                    if not s.get("verifiable", True) or s.get("symbol_state") == "prose_not_checkable"]
    if unverifiable:
        add(25, "unverifiable provenance",
            f"{len(unverifiable)} of this record's source anchors cannot be checked against "
            "this repository. Does the claim still hold, on evidence outside the corpus?",
            "The corpus declines to make a statement it cannot support. Whether the claim is "
            "nonetheless true is a human question.",
            "The anchors' entries in the claims section.")
    scope = record.get("asil_allocation_scope") or {}
    if scope:
        add(26, "classification presentation",
            "This record presents a reconstructed ASIL classification with an explicit scope "
            "block. Is presenting it this way acceptable, or should the value be removed?",
            "Keeping the value is a judgement about the reference project's internal "
            "consistency; presenting it on an as_is record is a judgement about what a reader "
            "will take from it. Neither is machine-decidable.",
            "asil_allocation_scope in section 3.")
    for e in (record.get("logs") or []):
        if isinstance(e, dict) and e.get("file") and not (live.root / str(e["file"])).exists():
            add(27, "evidence that is not there",
                f"`logs[]` names {e['file']}, which does not exist in this tree. Was the "
                "output ever captured, and if so where is it now?",
                "A citation to a file that is not there is a checkable claim that is false on "
                "a clean checkout. Only a person knows whether the file ever existed.",
                "The claims section, evidence_file entries.")
            break

    if not review_state["covered"]:
        add(30, "review coverage",
            "No other record in this corpus reviews this one. Is it in fact unreviewed, and "
            "does that matter for what you are signing?",
            "Approving an unreviewed record is close to meaningless: the packet gives you the "
            "record and the machine checks, not a second reader's reasoning. Say so in the "
            "comments if you accept that.",
            "What is already checked, below: the review coverage column for this record.")
    elif review_state["disputed"]:
        add(15, "existing disagreement",
            f"{len(review_state['disputed'])} finding(s) already dispute something about this "
            "record. Do you agree with the dispute, with the record, or with neither?",
            "A prior reviewer and this record already disagree. Resolving that is the point of "
            "a second reader.",
            "The disputed findings listed under what is already checked.")

    std = record.get("standards_mappings") or []
    if std:
        add(40, "standards mapping",
            "For each standards mapping: is the cited clause the right obligation for this "
            "work product, and is the status right?",
            "Clause selection is a reading of a standard, not a property of the repository.",
            "standards_mappings in section 3.")

    add(50, "lifecycle status",
        f"`lifecycle_status` is `{record.get('lifecycle_status')}`. Is that the right status "
        "for this revision?",
        "A status is a claim about how far the work has actually got, and no detector "
        "measures it.",
        "lifecycle_status and its note in section 3.")

    qs.sort(key=lambda q: q["priority"])
    # Cap the questions a reviewer is asked to answer. A reviewer handed a long
    # list reads none of it, and the point of a packet is that four questions
    # are answerable rather than fifty are skippable. Overflow is NOT discarded:
    # it is carried in packet.json under
    # `additional_questions_derived_not_shown`, so nothing this tool derived is
    # lost and nothing is silently dropped from the reviewer's view.
    return qs[:MAX_QUESTIONS], qs[MAX_QUESTIONS:]


# --------------------------------------------------------------------------
# rendering


def honesty_fields(record: dict):
    """The record's own honesty statements, verbatim. Not paraphrased."""
    keys = ("limitations", "provenance_note", "lifecycle_status_note",
            "disposition_note", "corpus_boundaries", "notes", "scope",
            "assumptions_disclosure", "honesty_statement")
    out = []
    for k in keys:
        if k in record and record[k] not in (None, "", [], {}):
            out.append((k, record[k]))
    ars = record.get("automated_review_status") or {}
    if ars:
        out.append(("automated_review_status", ars))
    return out


def review_state_for(live: Live, profile: str, aid: str):
    """Who has already read this record, and what did they conclude.

    Keyed by REVIEW ID, not by source. The corpus carries coverage in two
    places - a review record's `reviewed_ids` list and a `reviewed_by` link in
    the registry - and the two can name the same review twice, or disagree.
    Keying by id and merging means a reviewer sees one row per review with both
    routes named, instead of one row per route. Where the two disagree (a link
    exists for a review that does not enumerate this record) that is reported as
    its own row rather than hidden, because the disagreement is itself a fact
    about the corpus that a reviewer signing this record may want to know.
    """
    by_review = {}
    order = []

    for rel, d in live.review_records:
        if d.get("profile") != profile:
            continue
        for e in (d.get("reviewed_ids") or []):
            if isinstance(e, dict) and e.get("artifact_id") == aid:
                rid = d.get("id")
                if rid not in by_review:
                    order.append(rid)
                    by_review[rid] = {"review_id": rid, "review_path": rel,
                                       "routes": [], "reviewed_revision": e.get("revision"),
                                       "digest": e.get("digest")}
                by_review[rid]["routes"].append(
                    "reviewed_ids entry in " + rel)
    link_only = []
    for rel, l in live.links:
        if l.get("relation_type") != "reviewed_by":
            continue
        if l.get("profile") != profile or l.get("target_id") != aid:
            continue
        rid = l.get("source_id")
        if rid in by_review:
            by_review[rid]["routes"].append(f"reviewed_by link {l.get('link_id')} in {rel}")
        else:
            link_only.append((rid, rel, l))
            if rid not in order:
                order.append(rid)

    holder = live.index.get((profile, aid))
    actual = live.file_sha(holder[0]) if holder else None
    digest_ok = digest_bad = digest_placeholder = 0
    per_review = []
    for rid in order:
        info = by_review.get(rid)
        if info is None:
            continue
        rec = next((x for _r, x in live.review_records if x.get("id") == rid), None)
        recorded = info.get("digest")
        if is_placeholder_hash(recorded):
            state = "PLACEHOLDER digest (permitted only with a note); the reviewed bytes are not identified"
            digest_placeholder += 1
        elif holder and strip_sha(recorded) == actual:
            state = "digest matches this record on disk NOW, so the review provably read these bytes"
            digest_ok += 1
        elif holder:
            state = ("digest MISMATCH - the record has changed since this review, so the "
                     "review did not read the bytes now on disk")
            digest_bad += 1
        else:
            state = "reviewed id does not resolve to any record in this profile"
        per_review.append({
            "review_id": rid,
            "review_path": info.get("review_path"),
            "routes": info.get("routes"),
            "review_type": (rec or {}).get("review_type"),
            "reviewer_role": ((rec or {}).get("reviewer_identity") or {}).get("role"),
            "reviewer_model": ((rec or {}).get("reviewer_identity") or {}).get("model"),
            "checklist_version": (rec or {}).get("checklist_version"),
            "reviewed_revision": info.get("reviewed_revision"),
            "digest_state": state,
        })
    for rid, rel, l in link_only:
        per_review.append({
            "review_id": rid,
            "review_path": None,
            "routes": [f"reviewed_by link {l.get('link_id')} in {rel} ONLY - the review record "
                       f"{rid} was not found, or does not enumerate this record in its "
                       f"reviewed_ids. The link registry and the review records disagree "
                       f"about who reviewed this."],
            "review_type": None, "reviewer_role": None, "reviewer_model": None,
            "checklist_version": None, "reviewed_revision": None,
            "digest_state": "no digest carried on the link",
        })
    findings = live.findings_about(aid)
    disputed = [{"finding_id": f.get("finding_id"), "severity": f.get("severity"),
                 "category": f.get("category"),
                 "description": shorten(f.get("description"), 400),
                 "raised_in": f.get("id"), "source_path": rel}
                for rel, f in findings if f.get("finding_id")]
    return {
        "covered": bool(per_review),
        "reviews": per_review,
        "findings_about": disputed,
        "disputed": disputed,
        "digest_ok": digest_ok,
        "digest_mismatch": digest_bad,
        "digest_placeholder": digest_placeholder,
    }


def render_markdown(live: Live, rel: str, raw_text: str, digest: str,
                    record: dict, claims, questions, suppressed, anchor_states,
                    review_state, link_touching, machine, limitation_text,
                    packet_rel_md: str):
    profile = record.get("profile", "unknown")
    aid = record["id"]
    atype = record.get("artifact_type")
    fence = fence_for(raw_text)

    L = []
    A = L.append
    A(f"# Review packet - {profile} / {aid}")
    A("")
    A(f"**This packet is unsigned and contains no decision.** It was generated by "
      f"`{GENERATOR}` and it fills nothing in for you. Read section 8, answer it, "
      f"then sign section 9.")
    A("")
    A("---")
    A("")

    # 1 identity
    A("## 1. Identity")
    A("")
    A("| field | value |")
    A("| --- | --- |")
    A(f"| record id | `{aid}` |")
    A(f"| profile | `{profile}` |")
    A(f"| artifact type | `{atype}` |")
    A(f"| revision | `{md_cell(record.get('revision'))}` |")
    A(f"| lifecycle_status | `{md_cell(record.get('lifecycle_status'))}` |")
    A(f"| origin | `{md_cell(record.get('origin'))}` |")
    A(f"| owner_role | `{md_cell(record.get('owner_role'))}` |")
    A(f"| engineering_domain | `{md_cell(record.get('engineering_domain'))}` |")
    A(f"| human_approval_status | `{md_cell(record.get('human_approval_status'))}` |")
    A(f"| production_authorized | `{md_cell(record.get('production_authorized'))}` |")
    A(f"| product_verification_credit | `{md_cell(record.get('product_verification_credit'))}` |")
    A(f"| file (exact) | `{rel}` |")
    A(f"| size on disk | {len(raw_text.encode('utf-8'))} bytes |")
    A("")
    A("**`(profile, id)` is the primary key.** Under amendment ID-RULE-004-A1 an "
      "artefact identifier is unique *within its profile*, and two records of different "
      "profiles may legitimately carry the same identifier string. So this record is "
      "uniquely named by the pair `(" + profile + ", " + aid + ")`, never by `" + aid +
      "` alone. If you are comparing this packet against a reference that gives only the "
      "id, it is ambiguous until the profile is also given.")
    A("")

    # 2 integrity
    A("## 2. Integrity digest")
    A("")
    A("| field | value |")
    A("| --- | --- |")
    A(f"| sha256 of this record's exact current bytes | `{digest}` |")
    A(f"| bytes hashed | {len(raw_text.encode('utf-8'))} |")
    A(f"| embedded in section 3 verbatim | yes - the block is the file's bytes, not a re-serialisation |")
    if live.registry_sha:
        applies = bool(record.get("source_refs"))
        A(f"| sha256 of `{REGISTRY_PATH}` (the anchor registry the provenance gate reads) "
          f"| `{live.registry_sha}` |")
        A(f"| applies to this record | "
          + ("yes - this record cites source anchors" if applies
             else "no - this record cites no source anchors, so the registry digest is "
                  "recorded for completeness only")
          + " |")
    A("")
    A("The signature in section 9 refers to the bytes hashed above. If the record changes, "
      "the digest changes, and a signature against the old digest no longer covers what is "
      "on disk. Run `make_review_packets.py --verify` to detect that.")
    A("")
    A("**What the corpus provenance gate actually does with anchors**, so you do not "
      "over-read the registry digest: it verifies each anchor against the file that anchor "
      "names - existence, `content_hash` against the file's sha256, `line_range` inside the "
      "file's bounds, and `symbol` occurring in the file - and it stores no registry-level "
      "digest of its own. The digest above is the digest of the registry file the gate "
      "reads, given here so that a signature also pins which anchor set was in force.")
    A("")

    # 3 record verbatim
    A("## 3. The record, verbatim")
    A("")
    A("The block below is the file's exact bytes. You need no other file open to review "
      "this record.")
    A("")
    A(f"{fence}json")
    A(raw_text.rstrip("\n"))
    A(fence)
    A("")

    # 4 claims
    A("## 4. Claims to verify")
    A("")
    A(f"{len(claims)} claim(s) derived from this record's own fields. These are the "
      "assertions in this record that could be false. Each row states what a machine "
      "settled and what it did not.")
    A("")
    for c in claims:
        A(f"### {c['claim_id']} - {c['claim_class']}")
        A("")
        A(f"**Assertion.** {c['statement']}")
        A("")
        A(f"- *Machine state:* {c['machine_state']}")
        A(f"- *Still needs a human:* {c['judgement_needed']}")
        A(f"- *Where to look:* {c['evidence_in_packet']}")
        A("")
    if not claims:
        A("_This record carries no source anchor, no id reference, no standards mapping, no "
          "evidence file and no type-specific claim field. Its content is prose and its "
          "correctness is entirely a human question._")
        A("")

    # 5 already checked
    A("## 5. What is ALREADY checked, and by what")
    A("")
    A("Do not redo this. Three states are distinguished and they are not "
      "interchangeable.")
    A("")
    A("### 5.1 Machine-verified, re-derived at packet generation time")
    A("")
    A("| check | detector / method | result |")
    A("| --- | --- | --- |")
    for k, method, result in machine:
        A(f"| {md_cell(k)} | {md_cell(method)} | {md_cell(result)} |")
    A("")
    A("These are re-derived by this tool, independently of `corpus.py`. `corpus.py check` "
      "runs the same classes of check as part of the acceptance suite; its verdict is a "
      "separate, corroborating source, not the basis of the rows above.")
    A("")
    A("### 5.2 Reviewed by a peer, and what it concluded")
    A("")
    if review_state["covered"]:
        A(f"{len(review_state['reviews'])} review record(s) cover this record. Where a review "
          "is named by both a `reviewed_ids` entry and a `reviewed_by` link, it is one row.")
        A("")
        A("| review | type | reviewer role | reviewer model | reviewed revision | digest state | how it is recorded |")
        A("| --- | --- | --- | --- | --- | --- | --- |")
        for r in review_state["reviews"]:
            A("| `{id}` | {t} | {role} | {model} | {rev} | {d} | {routes} |".format(
                id=md_cell(r.get("review_id")), t=md_cell(r.get("review_type")),
                role=md_cell(r.get("reviewer_role")), model=md_cell(r.get("reviewer_model")),
                rev=md_cell(r.get("reviewed_revision")), d=md_cell(r.get("digest_state")),
                routes=md_cell("; ".join(r.get("routes") or []))))
        A("")
        if review_state["findings_about"]:
            A(f"**{len(review_state['findings_about'])} finding(s) in the corpus reference "
              "this record.** These are peer-review output, not machine output.")
            A("")
            A("| finding | severity | category | description |")
            A("| --- | --- | --- | --- |")
            for f in review_state["findings_about"]:
                A("| `{i}` | {s} | {c} | {d} |".format(
                    i=md_cell(f.get("finding_id")), s=md_cell(f.get("severity")),
                    c=md_cell(f.get("category")), d=md_cell(f.get("description"))))
            A("")
        else:
            A("No finding in the corpus references this record.")
            A("")
    else:
        A("**UNEXAMINED by any other record in this corpus.** No review record lists this "
          "record in its `reviewed_ids`, and no `reviewed_by` link targets it. That is a "
          "fact about the corpus, not about the record's quality - and it is the reason "
          "your signature carries more weight on this packet than on a covered one.")
        A("")
    A("### 5.3 Traceability edges touching this record")
    A("")
    if link_touching:
        A(f"{len(link_touching)} link(s) in the registry have this record as an endpoint.")
        A("")
        A("| link | from -> to | relation | review_state | rationale (short) |")
        A("| --- | --- | --- | --- | --- |")
        for rel_l, l in link_touching[:60]:
            A("| `{i}` | {a} -> {b} | {r} | {s} | {x} |".format(
                i=md_cell(l.get("link_id")), a=md_cell(l.get("source_id")),
                b=md_cell(l.get("target_id")), r=md_cell(l.get("relation_type")),
                s=md_cell(l.get("review_state")), x=md_cell(shorten(l.get("rationale"), 130))))
        if len(link_touching) > 60:
            A(f"| ... | | | | {len(link_touching) - 60} more in "
              "`docs/artifacts/traceability/link-registry/` |")
        A("")
    else:
        A("No link in the registry has this record as an endpoint. For a record of type "
          f"`{atype}` that is unusual and is itself part of what is being reviewed.")
        A("")
    A("### 5.4 The three states, stated explicitly")
    A("")
    A("- **machine-verified:** the rows in 5.1. A detector settled them. You do not need "
      "to re-derive them; you are entitled to disbelieve them.")
    A("- **reviewed by a peer and disputed:** the findings in 5.2 that carry a severity. "
      "Someone already disagreed with this record. Read them before deciding.")
    A("- **unexamined:** everything else - every judgement in section 4 whose machine "
      "state is descriptive rather than decisive, and every claim in section 6. Nobody has "
      "looked at it but a machine.")
    A("")

    # 6 limitations
    A("## 6. Known limitations, in the record's own words")
    A("")
    A("Reproduced verbatim. Where the record limits itself, that limit is part of the "
      "claim, not commentary on it.")
    A("")
    if limitation_text:
        for k, v in limitation_text:
            A(f"### `{k}`")
            A("")
            A(md_blockquote(v) if not isinstance(v, (dict, list)) else
              ("```json\n" + json.dumps(v, indent=1, sort_keys=True) + "\n```"))
            A("")
    else:
        A("_This record declares no `limitations`, no `provenance_note` and no honesty "
          "note. For a record of this type that is itself a finding: a record that cannot "
          "be wrong needs to say so._")
        A("")

    # 7 questions
    A("## 7. The questions only you can answer")
    A("")
    A(f"{len(questions)} question(s). Each one is derived from a field of this record; "
      "none is a generic checklist item. There is no list of fifty to work through - if a "
      "question is not here, the machine settled it or the record does not raise it.")
    A("")
    for i, q in enumerate(questions, 1):
        A(f"**Q{i}. {q['question']}**")
        A("")
        A(f"- *Why a machine cannot answer this:* {q['why_this_needs_a_human']}")
        A(f"- *What in this packet bears on it:* {q['what_in_this_packet_bears_on_it']}")
        A("- *Your answer:*")
        A("")
    if suppressed:
        A(f"_{len(suppressed)} further question(s) were derived from this record and are "
          f"NOT shown above, because a reviewer handed a long list reads none of it. They "
          f"are recorded in `packet.json` beside this file under "
          f"`additional_questions_derived_not_shown` - nothing was discarded. Ask for them "
          f"if the four above do not cover what you need to decide._")
        A("")

    # 8 what signing does
    A("## 8. What your signature changes, and exactly what to write")
    A("")
    A(f"Filling in section 9 is the only thing that changes `human_approval_status` on this "
      f"record. It is currently `{record.get('human_approval_status', 'pending')}`. No automated "
      f"process may fill it, and none can.")
    A("")
    A("### 8.1 The rule that will read your signature")
    A("")
    A("As of **2026-10-04** this is an EVIDENCE requirement, not a prohibition. The corpus used "
      "to run a rule that failed validation on any record whose "
      "`human_approval_status` was `approved`, however well evidenced - a ban, which cannot tell "
      "a fabricated approval from a real one because it never looks at one. That ban was replaced "
      "(amendment `APPROVAL-RULE-A1`, recorded at "
      "`docs/artifacts/governance/role-and-review-policy.json#/approval_evidence_contract`). "
      "**Recording the first real approval no longer turns `corpus.py check` red.** What it does "
      "instead is make the tool check six things, and fail if any one is missing.")
    A("")
    A("**A properly formed approval must carry, on the record itself, all six of these:**")
    A("")
    A("| # | element | what the validator actually checks |")
    A("| --- | --- | --- |")
    A("| 1 | the grant value | `human_approval_status` is `\"approved\"` (or `\"rejected\"` - "
      "both are recorded human decisions and both need a person behind them). A value on its own "
      "is necessary and **not sufficient**. |")
    A(f"| 2 | `approved_by` | a named individual, not a role and not a team. Rejected if it is a "
      f"single token, if it equals a declared `role_id` or role name, if any token is a declared "
      f"`role_id`, or if any token is in the team vocabulary (team, group, board, committee, "
      f"panel, crew, squad, staff, department, automation, system, tool, agent, ...). |")
    A(f"| 3 | `role` + `independence` | `role` must be a `role_id` declared in "
      f"`role-and-review-policy.json#/roles`. `independence` must be an object carrying "
      f"`owner_role` (**must equal this record's own `owner_role`, which is "
      f"`{record.get('owner_role')!r}`**), `satisfied: true`, an `evidence` string of at least 24 "
      f"characters that is not a placeholder, and a `policy_ref` naming "
      f"`role-and-review-policy.json`. Then independence is ENFORCED, not just asserted: your role "
      f"must differ from `{record.get('owner_role')}` **and** from the author of the last "
      f"`revision_history` entry that changed this record's content. |")
    A("| 4 | `date` | ISO-8601, `YYYY-MM-DD` optionally followed by `THH:MM[:SS]` and `Z` or an "
      "offset. Checked by grammar AND by parse. |")
    A("| 5 | `review_packet` | an object carrying `path`, `sha256` and "
      "`record_sha256_at_signing`. See 8.2 - this is the part reviewers get wrong. |")
    A("| 6 | `revision_history` | an entry whose `author` is your approving role, whose `revision` "
      "is at least this record's current revision, and whose `description` both records the "
      "approval **and cites the signed packet by digest or by name**. |")
    A("")
    A("### 8.2 The packet digest, which is the part that is easy to get wrong")
    A("")
    A("Three digests are involved and they are not interchangeable:")
    A("")
    A(f"- `record_sha256_at_signing` is printed in section 4 of this packet and in this packet's "
      f"`packet.json` under `integrity.record_sha256`. It is "
      f"`{digest}`-class: the digest of THIS RECORD's bytes as they stand now. You can copy it "
      f"straight out of section 4.")
    A("- `sha256` is the digest of **this packet file's own bytes**, which the packet cannot "
      "print about itself. Do not type it by hand. Either run "
      "`shasum -a 256 <packet.json>` or, much better, let the generator print the whole block:")
    A("")
    A("```")
    A(f"python3 docs/artifacts/tools/make_review_packets.py --transcribe {aid}"
      + (f" --profile {profile}" if aid in ("",) else ""))
    A("```")
    A("")
    A("  That command writes nothing and fills no decision. It resolves both digests against the "
      "files on disk and prints the exact `approval_evidence` block and the exact "
      "`revision_history` entry to append, with your name, role, organisation and date left for "
      "you to supply.")
    A("")
    A("What the validator does with them, so you can check your work:")
    A("")
    A("1. `path` must be a `.json` packet twin under `docs/artifacts/reviews/packets/` or under "
      "the signed-packet archive `docs/artifacts/reviews/signed/`, and it must exist on disk. "
      "Anything else is rejected.")
    A("2. `sha256` must equal that file's bytes **as they stand on disk now**. If the packet has "
      "been regenerated since you signed, the digest no longer matches and the approval is "
      "rejected - which is correct, because the record state you reviewed has changed.")
    A("3. `record_sha256_at_signing` must equal **the packet's own** `integrity.record_sha256`. "
      "This is the binding that matters: citing a packet that exists, is the right shape and is "
      "byte-stable proves nothing unless its recorded record digest is the one you attested to. A "
      "digest belonging to a different record, a different revision, or a packet that was never "
      "on disk all fail here.")
    A("4. The cited packet must name THIS record in `target.record_id` **and** "
      "`target.profile` (the pair is the key under ID-RULE-004-A1), and its `integrity."
      "record_path` must be this record's own file.")
    A("")
    A("### 8.3 What happens to the numbers, read from the code")
    A("")
    A("1. **The coverage dimension `human_approval` now moves.** It used to be a literal "
      "`{\"numerator\": 0}` with the detail string \"all artifacts pending human approval (none "
      "performed)\" - a constant that measured nothing and would have read 0/321 after three "
      "hundred signatures. Since 2026-10-04 it is COMPUTED from the records, by the same "
      "predicate the validator enforces, so it reads 0/321 today and will read 1/321 the moment "
      "one properly evidenced approval is recorded. `production_authorization` is the same, with "
      "a STRICTLY higher bar: the approving role must be one the corpus grants production "
      "authority to (`architect` or `safety_manager`), and the record's family must be one human "
      "approval is required for (`safety_case`, `post_development_record`, `change`).")
    A("2. **Recording a properly formed approval keeps `corpus.py check` green.** The finding "
      "you would get for a bare `approved` names every unmet element, so if you get one, read it "
      "rather than guessing: it tells you which of the six is missing.")
    A("3. **Two controls the signature does not touch.** `automated_review_status` describes "
      "machine checks, not your judgement - leave it alone. And the recursive key scan for "
      "authority claims (`production_release`, `authorized_for_production` and eight siblings, "
      "plus the ASIL/conformity/certification claim classes) is unchanged: nesting a production "
      "claim inside the new `approval_evidence` block is still caught.")
    A("")
    A("### 8.4 How to record it, in order")
    A("")
    A("1. Fill section 9 and archive the signed packet **outside** "
      "`docs/artifacts/reviews/packets/` - into `docs/artifacts/reviews/signed/` - because "
      "regenerating a packet overwrites it, and the generator refuses to overwrite a packet that "
      "already carries a signature rather than destroy it. Cite the archived copy in "
      "`review_packet.path`; both locations resolve.")
    A(f"2. Run `--transcribe {aid}` and paste the block it prints.")
    A("3. Add the `revision_history` entry it prints. Record the approval against the record's "
      "CURRENT revision; bumping the revision number makes every link that pins this record's "
      "revision stale and invalidates the sha256 every review record stores for it.")
    A("4. Run `python3 docs/artifacts/tools/corpus.py validate` and read the result. Zero "
      "approval findings means the approval is properly evidenced.")
    A("")
    A("**Still not yours to do:** writing the approval value into the record. The gate now "
      "*accepts* a legitimately evidenced approval, which is what makes the guard meaningful, but "
      "*producing* one needs a person. No tool in this repository may do it, and the self-test "
      "`no record in the corpus carries an approval of any kind` fails the suite if one ever "
      "appears.")
    A("")
    A("`docs/artifacts/governance/closing-list.md` states what is still outstanding and who owns "
      "it. Read it before recording anything.")
    A("")

    # 9 signature
    A("## 9. Signature")
    A("")
    A("**This block is deliberately empty.** No field below has a default, no decision is "
      "suggested, and no automated process may fill any of it. If you find a value already "
      "present in this block, this packet is not the one the generator wrote and you should "
      "stop and say so.")
    A("")
    A("| field | value |")
    A("| --- | --- |")
    for key, label in SIGNATURE_FIELDS:
        A(f"| {label} | |")
    A("")
    A(f"_Date in ISO 8601. Decision is exactly one of: approve, approve-with-comments, "
      f"reject. Your role must be independent of this record's `owner_role` "
      f"(`{record.get('owner_role')}`) and of the author of the content you are reviewing; see "
      f"`docs/artifacts/governance/role-and-review-policy.json` for the independence requirement "
      f"per role. Section 8 says exactly which fields the validator reads and what it checks "
      f"against each._")
    A("")
    A("---")
    A("")
    A(f"Packet `{packet_rel_md}` | format `{PACKET_FORMAT}` | machine-readable twin: "
      "`packet.json` beside this file | index: `docs/artifacts/reviews/packets/INDEX.md`")
    A("")
    return "\n".join(L) + "\n"


def render_json(live: Live, rel: str, raw_bytes: bytes, digest: str, record: dict,
                claims, questions, suppressed, anchor_states, review_state,
                link_touching, machine, packet_rel_json: str, fence: str):
    """The machine-readable twin.

    SHAPE IS DELIBERATE. This object carries no top-level `id`, `profile`,
    `artifact_type` or `source_refs`. `docs/artifacts/reviews/` is one of the
    three roots `corpus.py iter_corpus_artifacts()` walks, and a packet shaped
    like a record would enter the artefact index - moving `human_approval`'s
    denominator, `source_grounding`'s numerator and `actual_product_evidence`'s
    record set on nothing but the act of generating review material. Everything
    record-shaped lives under `target`, which no corpus reader looks at.
    """
    return {
        "packet_format": PACKET_FORMAT,
        "is_a_corpus_record": False,
        "shape_note": (
            "Deliberately not shaped like a corpus record: no top-level id, profile, "
            "artifact_type or source_refs, so that generating packets cannot change any "
            "coverage number. See the module docstring of make_review_packets.py."),
        "generated_by": GENERATOR,
        "signature_policy": (
            "The signature block below is empty by construction. This tool has no code "
            "path that writes a decision, an approval, a signature or an execution "
            "verdict. Filling it is a human action. As of 2026-10-04 (amendment "
            "APPROVAL-RULE-A1) the corpus ACCEPTS a properly evidenced approval rather "
            "than banning the value outright, so this rule now has to carry the evidence "
            "contract in full: see signature_block._contract."),
        "packet_path": packet_rel_json,
        "integrity": {
            "record_path": rel,
            "record_sha256": digest,
            "record_bytes": len(raw_bytes),
            "verbatim_block_fence": fence,
            "verbatim_block_sha256": sha256_bytes(
                raw_text_of(raw_bytes).rstrip("\n").encode("utf-8")),
            "verbatim_block_is_record_bytes": True,
            "verbatim_block_note": (
                "The block in section 3 is the file's decoded text with any single "
                "trailing newline removed, which is what the markdown fences require. "
                "`record_sha256` above is over the raw file bytes and is the digest a "
                "signature refers to; this one is over the text as embedded, so a "
                "verifier can compare either."),
            "anchor_registry_path": REGISTRY_PATH if live.registry_sha else None,
            "anchor_registry_sha256": live.registry_sha,
            "anchor_registry_applies": bool(record.get("source_refs")),
            "anchor_registry_note": (
                "The corpus provenance gate verifies each anchor against the file that "
                "anchor names and stores no registry-level digest of its own. This digest "
                "is recorded so a signature also pins which anchor set was in force."),
        },
        "target": {
            "record_id": record["id"],
            "profile": record.get("profile", "unknown"),
            "artifact_type": record.get("artifact_type"),
            "revision": record.get("revision"),
            "lifecycle_status": record.get("lifecycle_status"),
            "origin": record.get("origin"),
            "owner_role": record.get("owner_role"),
            "engineering_domain": record.get("engineering_domain"),
            "human_approval_status": record.get("human_approval_status"),
            "production_authorized": record.get("production_authorized"),
            "product_verification_credit": record.get("product_verification_credit"),
            "primary_key": [record.get("profile", "unknown"), record["id"]],
            "primary_key_rule": (
                "ID-RULE-004-A1: an artefact identifier is unique within its profile; two "
                "records of different profiles may carry the same identifier string."),
        },
        "record_verbatim": json.loads(raw_bytes.decode("utf-8")),
        "claims_to_verify": claims,
        "already_checked": {
            "machine_verified": [{"check": k, "method": method, "result": result}
                                 for k, method, result in machine],
            "method_note": (
                "Re-derived by make_review_packets.py, independently of corpus.py. "
                "corpus.py check runs the same classes of check; its verdict corroborates, "
                "it is not the basis of these rows."),
            "peer_review": review_state,
            "links_touching_record": [
                {"link_id": l.get("link_id"), "source_id": l.get("source_id"),
                 "target_id": l.get("target_id"), "relation_type": l.get("relation_type"),
                 "review_state": l.get("review_state"), "registry_path": rel_l,
                 "rationale": l.get("rationale")}
                for rel_l, l in link_touching],
            "state_legend": {
                "machine-verified": "settled by a detector; see machine_verified above",
                "reviewed_by_a_peer_and_disputed":
                    "a finding in the corpus references this record; see "
                    "peer_review.findings_about",
                "unexamined":
                    "everything else, including every judgement in claims_to_verify whose "
                    "machine_state is descriptive rather than decisive",
            },
        },
        "known_limitations_verbatim": [
            {"field": k, "value": v} for k, v in honesty_fields(record)],
        "questions_for_human": questions,
        "questions_shown_count": len(questions),
        "questions_cap": MAX_QUESTIONS,
        "additional_questions_derived_not_shown": {
            "count": len(suppressed),
            "why": (
                "This record raised more judgement calls than a packet shows, so a "
                "reviewer is not handed a list long enough to skip. These are derived "
                "from the record's own fields and are recorded here rather than "
                "discarded, so nothing this tool found is lost. A reviewer who wants "
                "them should ask for them; the point of the cap is that the four "
                "highest-value questions are the ones that get answered."),
            "questions": suppressed,
        },
        "signature_block": {
            "filled": False,
            "reviewer_name": "",
            "organisation": "",
            "role": "",
            "date": "",
            "decision": "",
            "comments": "",
            "signature": "",
            "_rule": (
                "Empty by construction. No automated process may fill this. Filling it in is the "
                "only thing that changes human_approval_status on the record. As of 2026-10-04 "
                "(amendment APPROVAL-RULE-A1) the corpus rule human_approval_rejected is an "
                "EVIDENCE requirement, not a prohibition: a properly evidenced approval is "
                "ACCEPTED and keeps `corpus.py check` green, while a bare grant value is still "
                "rejected. What the validator reads is contract.approval_evidence_block below; "
                "it fails if any of its six elements is missing, and the finding names which."),
            "_contract": {
                "rule_id": "human_approval_rejected",
                "severity": "high",
                "record_field": "human_approval_status",
                "grant_is": "any value other than \"pending\" or absent",
                "evidence_record_field": "approval_evidence",
                "evidence_key": "human_approval",
                "policy_ref": (
                    "docs/artifacts/governance/role-and-review-policy.json"
                    "#/approval_evidence_contract"),
                "required_elements": [
                    "1. human_approval_status carries the grant value",
                    "2. approved_by - a named individual, not a role and not a team",
                    "3. role - a role_id declared in role-and-review-policy.json#/roles - plus "
                    "independence{owner_role, satisfied, evidence, policy_ref}; the approving role "
                    "must differ from owner_role AND from the author of the last content revision",
                    "4. date - ISO-8601, checked by grammar and by parse",
                    "5. review_packet{path, sha256, record_sha256_at_signing}; path must resolve "
                    "to a packet.json on disk under docs/artifacts/reviews/packets/ or "
                    "docs/artifacts/reviews/signed/; sha256 must equal that file's bytes now; "
                    "record_sha256_at_signing must equal this packet's integrity.record_sha256; "
                    "target.record_id and target.profile must both name this record",
                    "6. a revision_history entry whose author is the approving role and whose "
                    "description records the approval and cites the signed packet",
                ],
                "digest_note": (
                    "The digests below are already filled in. Copy them; do not type them. Run "
                    "`make_review_packets.py --transcribe " + str(record["id"]) + "` to have "
                    "them printed as a pasteable block."),
            },
            "_record_sha256_at_signing": digest,
            "_packet_sha256": None,
            "_packet_sha256_note": (
                "The digest of this packet.json's own bytes. It is deliberately left null rather "
                "than filled, because a file cannot contain its own digest. Compute it with "
                "`shasum -a 256`, or use `--transcribe`, which resolves it."),
            "_recording": (
                "Transcribe a completed signature into the record as human_approval_status plus "
                "an approval_evidence.human_approval block plus a revision_history entry naming "
                "the reviewer and citing this packet, and archive the signed packet under "
                "docs/artifacts/reviews/signed/."),
        },
        "outcome_record": {
            "_note": ("Fields a human or a later process may fill AFTER a signature exists. "
                      "Empty here; present so the outcome can be captured without editing "
                      "the generator."),
            "packet_sha256_at_signing": "",
            "signed_by": "",
            "signed_on": "",
            "decision_recorded_in_record": "",
            "recorded_revision": "",
        },
    }


def raw_text_of(raw_bytes: bytes) -> str:
    return raw_bytes.decode("utf-8")


def output_paths(out_dir: Path, profile: str, aid: str):
    return (out_dir / profile / f"{aid}.md", out_dir / profile / f"{aid}.json")


def packet_signature_filled(md_path: Path):
    """Read the generated signature table out of a packet on disk.

    Returns (filled, {field: value}). Used so regeneration cannot destroy a
    signature, and so --verify can report signed packets.
    """
    if not md_path.exists():
        return False, {}
    text = md_path.read_text(encoding="utf-8")
    marker = "## 9. Signature"
    if marker not in text:
        return False, {}
    tail = text.split(marker, 1)[1]
    vals = {}
    for key, label in SIGNATURE_FIELDS:
        # Anchored on both pipes, not split on them. `str.split("|", 2)` on the
        # row "| Reviewer name | |" yields ' |' as the last field, whose strip()
        # is '|' - which is not empty, so every packet read as already signed.
        pat = re.compile(r"^\|\s*" + re.escape(label) + r"\s*\|(.*)\|\s*$")
        for line in tail.splitlines():
            m = pat.match(line)
            if m:
                vals[key] = m.group(1).strip()
                break
    filled = any(v for v in vals.values())
    return filled, vals


# --------------------------------------------------------------------------
# build


def build(root: Path, out_dir: Path, only=None, only_type=None, force=False,
          quiet=False):
    live = Live(root)
    records = []
    # `--only` takes an id, or `profile:id` when the id exists in more than one
    # profile. Under ID-RULE-004-A1 the primary key is the PAIR, so a bare id
    # that exists in both profiles names two records and both are generated: a
    # reviewer asking for FB2-HW-TSR-000001 does not get half the answer.
    want_profile = None
    want_id = only
    if only and ":" in only:
        want_profile, want_id = only.split(":", 1)
    for rel, path, record in live.files:
        if only and record["id"] != want_id:
            continue
        if only and want_profile and record.get("profile") != want_profile:
            continue
        if only_type and record.get("artifact_type") != only_type:
            continue
        records.append((rel, path, record))
    records.sort(key=lambda t: (t[2].get("profile", ""), t[2]["id"]))

    if not quiet:
        print(f"review packet generator: {len(records)} record(s) selected "
              f"of {len(live.files)} in the corpus")

    written = skipped_signed = 0
    index_rows = []
    for rel, path, record in records:
        profile = record.get("profile", "unknown")
        aid = record["id"]
        atype = record.get("artifact_type")
        raw_bytes = path.read_bytes()
        raw_text = raw_text_of(raw_bytes)
        digest = sha256_bytes(raw_bytes)

        md_path, json_path = output_paths(out_dir, profile, aid)
        md_rel = md_path.relative_to(root).as_posix() if out_dir.is_relative_to(root) \
            else md_path.as_posix()
        json_rel = json_path.relative_to(root).as_posix() if out_dir.is_relative_to(root) \
            else json_path.as_posix()

        anchor_states = [live.anchor_state(a) for a in (record.get("source_refs") or [])]
        claims = claims_for(live, profile, aid, atype, record)
        review_state = review_state_for(live, profile, aid)
        link_touching = live.links_touching(profile, aid)

        schema_ok, schema_name, schema_err = live.schema_check(atype, record)
        machine = []
        if schema_name:
            machine.append(("schema validity",
                            f"jsonschema Draft 2020-12 against {schema_name}",
                            "valid against its schema" if schema_ok
                            else f"INVALID: {schema_err}"))
        machine.append(("primary key uniqueness",
                        "within-profile (profile, id) index built by this tool",
                        "unique in profile" if sum(
                            1 for k in live.index if k == (profile, aid)) == 1
                        else "DUPLICATE"))
        machine.append(("authority fields",
                        "direct read of the record",
                        "human_approval_status=pending, production_authorized=false, "
                        "product_verification_credit=false"
                        if (record.get("human_approval_status") == "pending"
                            and record.get("production_authorized") is False
                            and record.get("product_verification_credit") is False)
                        else "READ THESE - they are not the expected policy values"))
        if anchor_states:
            ok = sum(1 for s in anchor_states if s.get("verifiable")
                     and s.get("hash_matches_now") is not False
                     and s.get("symbol_state") != "absent"
                     and s.get("line_range_state") != "out_of_bounds")
            machine.append((f"source anchors ({len(anchor_states)})",
                            "per-anchor existence / content_hash / line_range / symbol, "
                            "re-derived against the files on disk",
                            f"{ok}/{len(anchor_states)} fully checked with no contradiction"
                            if ok == len(anchor_states)
                            else f"{ok}/{len(anchor_states)} fully checked; see claims"))
        else:
            machine.append(("source anchors", "not applicable",
                            "this record cites no source_refs, so it asserts nothing about "
                            "source bytes"))
        nlog = 0
        nlog_ok = 0
        for e in (record.get("logs") or []):
            if isinstance(e, dict) and e.get("file"):
                nlog += 1
                if (root / str(e["file"])).exists() and not is_placeholder_hash(e.get("hash")) \
                        and strip_sha(e.get("hash")) == live.file_sha(str(e["file"])):
                    nlog_ok += 1
        if nlog:
            machine.append((f"evidence logs ({nlog})",
                            "file existence and recorded hash against the bytes on disk",
                            f"{nlog_ok}/{nlog} exist with a matching hash"))
        nrev = len(review_state["reviews"])
        if nrev:
            machine.append((f"peer review coverage ({nrev} review record(s))",
                            "reviewed_ids entries and reviewed_by links",
                            f"{review_state['digest_ok']} digest(s) match the record now, "
                            f"{review_state['digest_mismatch']} mismatch, "
                            f"{review_state['digest_placeholder']} placeholder"))
        else:
            machine.append(("peer review coverage", "reviewed_ids and reviewed_by lookup",
                            "UNEXAMINED: no review record in this corpus covers it"))

        limitation_text = honesty_fields(record)
        questions, suppressed = questions_for(live, profile, aid, atype, record,
                                             claims, anchor_states, review_state,
                                             limitation_text)
        fence = fence_for(raw_text)
        md = render_markdown(live, rel, raw_text, digest, record, claims, questions,
                             suppressed, anchor_states, review_state, link_touching,
                             machine, limitation_text, md_rel)
        js = render_json(live, rel, raw_bytes, digest, record, claims, questions,
                         suppressed, anchor_states, review_state, link_touching,
                         machine, json_rel, fence)

        already_filled, _ = packet_signature_filled(md_path)
        if already_filled and not force:
            skipped_signed += 1
            if not quiet:
                print(f"  SKIP {profile}/{aid}: a packet with a filled signature block "
                      f"already exists at {md_rel}; move it out of the packets tree first "
                      f"(regenerating would destroy the signature)")
            index_rows.append((profile, aid, atype, record.get("lifecycle_status"),
                               len(claims), len(questions), md_rel, "SKIPPED-SIGNED"))
            continue

        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(md, encoding="utf-8")
        json_path.write_text(json.dumps(js, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        written += 1
        index_rows.append((profile, aid, atype, record.get("lifecycle_status"),
                           len(claims), len(questions), md_rel, "written"))

    if not only and not only_type:
        write_index(root, out_dir, live, index_rows)

    if not quiet:
        print(f"  written: {written} packet(s) under {out_dir}")
        if skipped_signed:
            print(f"  skipped because a signature is already present: {skipped_signed} "
                  f"(not overwritten; see the message above)")
        nq = [r[5] for r in index_rows]
        if nq:
            print(f"  questions per packet: min {min(nq)}, max {max(nq)}, "
                  f"mean {sum(nq) / len(nq):.1f}")
    return written, skipped_signed, index_rows


def write_index(root: Path, out_dir: Path, live: Live, rows):
    by_profile = {}
    by_type = {}
    covered = 0
    for profile, aid, atype, life, nclaims, nqs, md_rel, status in rows:
        by_profile[profile] = by_profile.get(profile, 0) + 1
        by_type[atype] = by_type.get(atype, 0) + 1
    for profile, aid, *_rest in rows:
        if live.reviews_covering(profile, aid):
            covered += 1

    L = []
    A = L.append
    A("# Review packets - index")
    A("")
    A(f"Generated by `{GENERATOR}`. {len(rows)} packet(s).")
    A("")
    A("**Every packet in this tree is unsigned and contains no decision.** Each one ends "
      "in an empty signature block. No automated process fills it. If you find a filled "
      "block in a file here, that file was not produced by the generator.")
    A("")
    A("A packet exists so a reviewer signs rather than reconstructs. Read "
      "`docs/artifacts/governance/closing-list.md` for who should sign what, in what "
      "order, and what they return.")
    A("")
    A("## How to use one")
    A("")
    A("1. Open the packet for your record. It embeds the record verbatim, so you need no "
      "other file open.")
    A("2. Section 5 tells you what is already machine-checked and what a peer already "
      "concluded. Do not redo section 5.")
    A("3. Section 7 has the questions only you can answer. For most records that is 2-4 "
      "questions, not a checklist.")
    A("4. Section 9 is empty. Answer section 7, then fill section 9 in your own copy.")
    A("5. Return the signed packet. Do not write the decision into the generator's tree - "
      "regeneration overwrites it, and the generator refuses to overwrite a signed packet "
      "rather than lose your signature.")
    A("")
    A("## What a packet is checked against")
    A("")
    A("- the record's own sha256, so a signature provably refers to the bytes hashed, not "
      "to a later revision;")
    A("- the corpus provenance gate's anchor classes: file existence, `content_hash`, "
      "`line_range` bounds, `symbol` occurrence, and evidence-log existence and hash;")
    A("- the `reviewed_ids` / `reviewed_by` coverage, with each review's digest state "
      "reported;")
    A("- every path the packet names, which `--verify` re-checks.")
    A("")
    A("## Staleness")
    A("")
    A("```")
    A(f"python3 {GENERATOR} --verify")
    A("```")
    A("")
    A("re-reads every packet and reports whether its embedded record bytes and digest "
      "still match the file on disk. `corpus.py check` runs the same verification as a "
      "non-fatal line, so a stale packet cannot go unnoticed for long. A stale packet is "
      "not an error in the corpus; it is a packet that no longer describes the record, and "
      "regenerating it is the fix.")
    A("")
    A("## Coverage of this index")
    A("")
    A("| profile | packets |")
    A("| --- | --- |")
    for k in sorted(by_profile):
        A(f"| `{k}` | {by_profile[k]} |")
    A("")
    A("| artifact type | packets |")
    A("| --- | --- |")
    for k in sorted(by_type, key=lambda x: (str(x))):
        A(f"| `{k}` | {by_type[k]} |")
    A("")
    A(f"Covered by at least one other review record: {covered}/{len(rows)}. "
      "The remainder are unexamined by any other record in the corpus - see section 5.2 of "
      "each packet.")
    A("")
    A("## Packets")
    A("")
    A("| profile | id | type | lifecycle | claims | questions | packet | state |")
    A("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for profile, aid, atype, life, nclaims, nqs, md_rel, status in sorted(rows):
        href = md_rel.split("packets/", 1)[-1] if "packets/" in md_rel else md_rel
        A(f"| `{profile}` | `{aid}` | `{md_cell(atype)}` | `{md_cell(life)}` | {nclaims} | "
          f"{nqs} | [{aid}]({href}) | {status} |")
    A("")
    (out_dir / "INDEX.md").write_text("\n".join(L) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------
# transcribe
#
# The evidence contract amendment (APPROVAL-RULE-A1) requires an approval to
# cite two digests, one of which is the digest of the packet file's own bytes.
# A packet cannot print its own digest, so a reviewer working only from the
# packet has to run `shasum` and copy 64 hex characters correctly. That is a
# guaranteed first-attempt failure, and a reviewer who fails it will conclude
# the requirement is unreasonable rather than that they mistyped.
#
# So this command exists: it resolves both digests against the files on disk and
# prints the exact block to paste, with every field a human must supply left
# blank. It writes NOTHING. It fills no decision, no name, no date. Its only
# non-trivial outputs are the two digests and the paths, which are facts about
# files rather than judgements about records.
#
# A reviewer can therefore transcribe a correct approval first time, which is
# the only way the requirement is fair.

TRANSCRIBE_FIELDS = ("approved_by", "organisation", "role", "date", "decision")


def transcribe(root: Path, out_dir: Path, only: str, profile: str = None):
    """Print the pasteable approval_evidence block for one record. Writes nothing.

    Returns 0 on success, 1 if the record or its packet cannot be found, 2 if
    the packet is stale (generated against an older state of the record), which
    would make the digest chain unsatisfiable and is therefore reported rather
    than printed.
    """
    live = Live(root)
    matches = [(rel, path, rec) for rel, path, rec in live.files
               if rec["id"] == only and (not profile or rec.get("profile") == profile)]
    if not matches:
        print(f"no record with id {only}"
              + (f" in profile {profile}" if profile else "")
              + f"; run with --only-list to see what exists")
        return 1
    if len(matches) > 1:
        print(f"{only} exists in {len(matches)} profiles "
              f"({', '.join(sorted(m.get('profile', 'unknown') for _r, _p, m in matches))}). "
              f"Under ID-RULE-004-A1 the pair (profile, id) is the key, so pass --profile.")
        return 1
    rel, path, rec = matches[0]
    jp = out_dir / rec.get("profile", "unknown") / f"{rec['id']}.json"
    if not jp.is_file():
        print(f"no packet for {rec['id']} at {jp}. Run this tool with no arguments first.")
        return 1
    packet = jload(jp)
    integ = packet.get("integrity") or {}
    recorded = integ.get("record_sha256")
    actual = sha256_bytes(path.read_bytes())
    if actual != recorded:
        print(f"STALE: the packet on disk was generated against an older state of this record.\n"
              f"  record on disk : {actual}\n"
              f"  packet records : {recorded}\n"
              f"Regenerate the packet before transcribing, or your approval will be rejected at "
              f"element 5.")
        return 2
    pkt_sha = sha256_bytes(jp.read_bytes())
    pkt_rel = jp.relative_to(root).as_posix() if jp.is_relative_to(root) else jp.as_posix()
    owner = rec.get("owner_role")
    rev = str(rec.get("revision"))

    block = {
        "approved_by": "<YOUR FULL NAME - a person, not a role, not a team>",
        "organisation": "<your organisation>",
        "role": "<your role_id, declared in role-and-review-policy.json#/roles; must "
                "differ from owner_role and from the author of the content>",
        "date": "<YYYY-MM-DD>",
        "decision": "<approve | approve-with-comments | reject>",
        "independence": {
            "owner_role": owner,
            "satisfied": True,
            "evidence": "<how you are independent of owner_role: different role, different "
                        "reporting line, separate session. At least 24 characters.>",
            "policy_ref": "docs/artifacts/governance/role-and-review-policy.json#/roles/"
                          "<your role_id>",
        },
        "review_packet": {
            "path": pkt_rel,
            "sha256": pkt_sha,
            "record_sha256_at_signing": recorded,
        },
    }
    hist = {
        "revision": rev,
        "date": "<YYYY-MM-DDTHH:MM:SSZ>",
        "author": "<your role_id, the same value as above>",
        "description": (f"Recorded human approval of revision {rev} by <YOUR FULL NAME> "
                        f"(<your role_id>) against review packet {pkt_sha}."),
    }
    print(f"# transcribe target: {rec.get('profile', 'unknown')} / {rec['id']}")
    print(f"# record file      : {rel}")
    print(f"# owner_role       : {owner}   (your role must differ from this)")
    print(f"# record revision  : {rev}   (record the approval against this revision; do not")
    print(f"#                      bump it, or links pinning this revision go stale)")
    print(f"# packet file      : {pkt_rel}")
    print(f"# packet sha256    : {pkt_sha}")
    print(f"# record sha256    : {recorded}  (== integrity.record_sha256 in packet.json)")
    print("#")
    print("# Replace every <...> placeholder. Leave the two digests exactly as printed.")
    print("# Then merge into the record as:")
    print("#   \"human_approval_status\": \"approved\",")
    print(f"#   \"approval_evidence\": {{\"human_approval\": {json.dumps(block, indent=2)}}}")
    print("# and append to revision_history:")
    print(json.dumps(hist, indent=2))
    print("#")
    print("# This command wrote nothing. It is not an approval and records nothing.")
    return 0


# --------------------------------------------------------------------------
# verify


def verify(root: Path, out_dir: Path, quiet=False):
    problems = []
    checked = 0
    signed = []
    stale = []
    missing_ref = []
    for profile_dir in sorted(p for p in out_dir.iterdir() if p.is_dir()):
        for md_path in sorted(profile_dir.glob("*.md")):
            jp = md_path.with_suffix(".json")
            if not jp.exists():
                problems.append((md_path.as_posix(), "packet.json is missing"))
                continue
            checked += 1
            meta = jload(jp)
            integ = meta.get("integrity") or {}
            target = meta.get("target") or {}
            rel = integ.get("record_path")
            recorded = integ.get("record_sha256")
            src = root / rel if rel else None
            if src is None or not src.exists():
                problems.append((md_path.as_posix(), f"record path does not exist: {rel}"))
                continue
            actual = sha256_bytes(src.read_bytes())
            if actual != recorded:
                stale.append((target.get("record_id"), rel, recorded, actual))
                continue
            # The embedded block must equal the file's text EXACTLY. The generator
            # writes `raw_text.rstrip("\n")` between the fences, so the comparison
            # normalises the same single trailing newline on both sides; anything
            # else is a difference in the record's content and is reported.
            fence = str(integ.get("verbatim_block_fence") or "```")
            text = md_path.read_text(encoding="utf-8")
            start_tok = fence + "json"
            if start_tok in text:
                body = text.split(start_tok, 1)[1]
                if body.startswith("\n"):
                    body = body[1:]
                # `find`, not `rfind`: this packet contains a second fenced block
                # later (section 6 renders dict-typed honesty fields as json), so
                # searching backwards for the last fence returns that block's
                # opening fence and swallows sections 4 to 6 into the record. The
                # fence is chosen to be longer than any backtick run inside the
                # record, so the FIRST fence after the opening is this block's own.
                end = body.find("\n" + fence)
                embedded = body[:end] if end != -1 else body
                expected = src.read_text(encoding="utf-8").rstrip("\n")
                if embedded != expected:
                    problems.append((
                        md_path.as_posix(),
                        "embedded record text does not equal the file bytes "
                        f"(embedded {len(embedded)} chars, file {len(expected)} chars)"))
            else:
                problems.append((md_path.as_posix(), "verbatim block not found in the packet"))
            filled, vals = packet_signature_filled(md_path)
            if filled:
                signed.append((target.get("record_id"),
                               {k: v for k, v in vals.items() if v}))
            sb = meta.get("signature_block") or {}
            nonempty = {k: v for k, v in sb.items()
                        if k in dict(SIGNATURE_FIELDS) and v}
            if nonempty:
                problems.append((jp.as_posix(),
                                 f"packet.json signature_block is not empty: {sorted(nonempty)}"))
            if sb.get("filled") is not False:
                problems.append((jp.as_posix(), "packet.json signature_block.filled is not False"))
            # every repo-relative path the packet names must exist
            for relref in _paths_named(meta):
                if relref.startswith("<") or relref.startswith("http"):
                    continue
                if not (root / relref).exists():
                    missing_ref.append((target.get("record_id"), relref))

    if not quiet:
        print(f"packet verify: {checked} packet(s) under {out_dir}")
        intact = checked - len(stale)
        print(f"  digest matches the record on disk            : {intact}/{checked}")
        print(f"  embedded bytes match the record on disk      : "
              f"{intact - len([p for p in problems if 'embedded record text' in p[1]])}/{checked}")
        print(f"  stale (record changed since the packet)     : {len(stale)}")
        for aid, rel, rec, act in stale:
            print(f"      STALE {aid}  {rel}")
            print(f"           packet digest {rec[:16]}...  file digest {act[:16]}...")
        print(f"  signature block non-empty                   : {len(signed)} "
              f"(expected 0 in a freshly generated tree)")
        for aid, vals in signed:
            print(f"      SIGNED {aid}: fields {sorted(vals)}")
        print(f"  referenced paths that no longer exist      : {len(missing_ref)}")
        for aid, relref in missing_ref[:20]:
            print(f"      MISSING {aid}  {relref}")
        print(f"  structural problems                         : {len(problems)}")
        for p, why in problems[:20]:
            print(f"      {p}: {why}")
        ok = not stale and not problems and not missing_ref
        print(f"packet verify: {'OK' if ok else 'PROBLEMS FOUND'}")
    return {"checked": checked, "stale": stale, "signed": signed,
            "missing_ref": missing_ref, "problems": problems,
            "ok": not stale and not problems and not missing_ref}


def _paths_named(meta):
    """Every repository-relative path a packet.json names."""
    out = set()
    integ = meta.get("integrity") or {}
    for k in ("record_path", "anchor_registry_path"):
        v = integ.get(k)
        if isinstance(v, str):
            out.add(v)
    for e in (meta.get("already_checked") or {}).get("links_touching_record") or []:
        v = e.get("registry_path")
        if isinstance(v, str):
            out.add(v)
    for c in meta.get("claims_to_verify") or []:
        for m in re.finditer(r"`([A-Za-z0-9_./-]+\.(?:json|md|log|c|h|py|sh|yml|yaml|dil|txt|csv))`",
                             str(c.get("machine_state", ""))):
            out.add(m.group(1))
    return sorted(out)


# --------------------------------------------------------------------------
# main


def main(argv=None):
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(
        description="Generate or verify foxBMS 2 corpus review packets. "
                    "Writes no approval, verdict, signature or evidence value.")
    ap.add_argument("--root", default=None)
    ap.add_argument("--out", default=None,
                    help="output directory (default docs/artifacts/reviews/packets)")
    ap.add_argument("--only", default=None, help="a single record id")
    ap.add_argument("--only-type", default=None,
                    help="a single artifact_type, e.g. finding")
    ap.add_argument("--verify", action="store_true",
                    help="re-check every packet on disk against the record; writes nothing")
    ap.add_argument("--transcribe", default=None, metavar="ID",
                    help="print the pasteable approval_evidence block and revision_history "
                         "entry for one record, with both digests resolved against the files "
                         "on disk. Writes nothing and fills no decision.")
    ap.add_argument("--profile", default=None,
                    help="disambiguate --transcribe when the id exists in both profiles")
    ap.add_argument("--force", action="store_true",
                    help="overwrite a packet that already carries a signature "
                         "(archive the signed packet first)")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve() if args.root else find_repo_root(here)
    out_dir = Path(args.out).resolve() if args.out else root / "docs/artifacts/reviews/packets"

    if args.transcribe:
        return transcribe(root, out_dir, args.transcribe, profile=args.profile)

    if args.verify:
        if not out_dir.is_dir():
            print(f"packet verify: {out_dir} does not exist; nothing to verify")
            return 0
        r = verify(root, out_dir, quiet=args.quiet)
        return 0 if r["ok"] else 1

    if not out_dir.parent.exists():
        print(f"refusing to create {out_dir}: parent {out_dir.parent} does not exist")
        return 2
    out_dir.mkdir(parents=True, exist_ok=True)
    written, skipped, _rows = build(root, out_dir, only=args.only,
                                    only_type=args.only_type, force=args.force,
                                    quiet=args.quiet)
    return 0


if __name__ == "__main__":
    sys.exit(main())
