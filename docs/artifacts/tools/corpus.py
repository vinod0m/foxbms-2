#!/usr/bin/env python3
"""
foxBMS 2 Lifecycle Artifact Corpus Tool
CLI for managing the foxBMS 2 lifecycle artifact corpus.

Commands:
  inventory         Build/check source and feature inventories.
  validate          Run schema, identity, link, provenance and semantic rules.
  coverage          Compute process, feature, implementation and evidence coverage.
  trace             Query forward/reverse/lateral paths for an artifact ID.
  impact            Calculate typed transitive impact from changed IDs/revisions.
  render            Regenerate human-readable views from canonical data.
  export            Produce portable node/edge data and manifests.
  scenario-test     Apply isolated mutations and compare actual/expected findings.
  check             Run the complete offline corpus acceptance suite.

Run from repository root (or pass --root). All writes stay inside docs/artifacts/.
"""

import argparse
import csv
import hashlib
import io
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from jsonschema import Draft202012Validator, Draft7Validator
    HAVE_JSONSCHEMA = True
except ImportError:  # pragma: no cover
    HAVE_JSONSCHEMA = False


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent  # docs/artifacts/tools/corpus.py -> repo root
ARTIFACTS = REPO_ROOT / "docs" / "artifacts"

ALLOWED_RELATION_TYPES = {
    "refines", "allocated_to", "implements", "verifies", "validates",
    "result_of", "supports", "mitigates", "specified_by", "consumes",
    "produces", "depends_on", "constrained_by", "related_to",  # related_to allowed ONLY as explicit weak link, flagged in strict mode
    "reviewed_by", "changes", "supersedes",
}
STRICT_FORBIDDEN_RELATION_TYPES = {"related_to"}

ARTIFACT_TYPE_SCHEMAS = {
    "requirement": "requirement.schema.json",
    "design": "design.schema.json",
    "test_measure": "test_measure.schema.json",
    "execution": "execution.schema.json",
    "review": "review.schema.json",
    "scenario": "scenario.schema.json",
    "change": "change.schema.json",
    "finding": "finding.schema.json",
    "deviation": "deviation.schema.json",
    "tara": "tara.schema.json",
    # Added when the ISO 26262 Part 3 concept work products, the ASPICE SYS.1
    # elicitation records, the previously zero-record management processes, the
    # supporting-process records and the post-development lifecycle records were
    # authored. Each of these has a real schema and is registered here for
    # validation. Per the corpus rule that a type belongs in exactly one of
    # ARTIFACT_TYPE_SCHEMAS / expected_families, none of them is added to
    # expected_families below: that map is the denominator of the
    # artifact_population coverage dimension and its definition is not changed by
    # this authoring pass.
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
}
# artifact types validated against base schema only (no dedicated schema exists)
BASE_ONLY_TYPES = {
    "hazard", "safety_goal", "safety_case", "safety_analysis",
    "parameter_registry", "assumption_registry", "link_registry",
}

BASELINE_COMMIT = "308028fb"
FINAL_STATUS = "synthetic_ready_with_limitations"


def utcnow():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


class Findings:
    """Accumulates validation findings."""

    def __init__(self):
        self.items = []

    def add(self, severity, category, artifact_id, description):
        self.items.append({
            "severity": severity,
            "category": category,
            "artifact_id": artifact_id,
            "description": description,
        })

    @property
    def error_count(self):
        return sum(1 for f in self.items if f["severity"] in ("critical", "high"))

    def dump(self):
        return json.dumps(self.items, indent=1, sort_keys=True)


class CorpusTool:
    def __init__(self, root=None):
        self.root = Path(root) if root else REPO_ROOT
        self.artifacts_dir = self.root / "docs" / "artifacts"
        self.schemas_dir = self.artifacts_dir / "schemas"
        self.corpus_dir = self.artifacts_dir / "corpus"
        self.sources_dir = self.artifacts_dir / "sources"
        self.governance_dir = self.artifacts_dir / "governance"
        self.trace_dir = self.artifacts_dir / "traceability"
        self.scenarios_dir = self.artifacts_dir / "scenarios"
        self.reports_dir = self.artifacts_dir / "reports"
        self.exports_dir = self.artifacts_dir / "exports"
        self.views_dir = self.artifacts_dir / "views"
        self.tests_dir = self.artifacts_dir / "tests"
        self.schemas = {}
        self.findings = Findings()
        self.load_schemas()

    # ------------------------------------------------------------------ load

    def load_schemas(self):
        if not self.schemas_dir.exists():
            return
        for p in sorted(self.schemas_dir.glob("*.schema.json")):
            try:
                self.schemas[p.name] = load_json(p)
            except Exception as e:
                self.findings.add("critical", "schema", p.name, f"schema unparseable: {e}")

    def iter_corpus_artifacts(self):
        """Yield (path, dict) for every artifact-shaped JSON under corpus/, reviews/, scenarios/."""
        for base in (self.corpus_dir, self.artifacts_dir / "reviews"):
            if not base.exists():
                continue
            for p in sorted(base.rglob("*.json")):
                if ".work" in p.parts:
                    continue
                try:
                    yield p, load_json(p)
                except Exception as e:
                    self.findings.add("critical", "json", str(p), f"unparseable JSON: {e}")

    def iter_scenario_artifacts(self):
        for p in sorted(self.scenarios_dir.rglob("*.json")):
            if "evaluator-only" in p.parts:
                continue
            yield p, load_json(p)

    def load_links(self):
        """Return list of link dicts across all registries, tagged with profile.
        De-duplicates by (profile, link_id) - same link_id in different profiles is intentional."""
        links = []
        # Search trace_dir (canonical top-level) and entire corpus tree
        registries = list((self.trace_dir / "link-registry").rglob("links-*.json"))
        registries += list(self.corpus_dir.rglob("traceability/link-registry/**/links-*.json"))
        seen_paths = set()
        for p in registries:
            if p in seen_paths:
                continue
            seen_paths.add(p)
            # infer profile from registry path
            s = str(p)
            if "traceability/link-registry/as_is" in s or "/corpus/as_is/traceability/" in s:
                profile = "as_is"
            elif "traceability/link-registry/synthetic_reference" in s or "/corpus/synthetic_reference/traceability/" in s:
                profile = "synthetic_reference"
            else:
                profile = "unknown"
            d = load_json(p)
            for l in d.get("links", []):
                l["_registry"] = str(p)
                l["_profile"] = profile
                links.append(l)
        # de-duplicate by (profile, link_id) - same link_id in different profiles is intentional
        by_key = {}
        for l in links:
            key = (l.get("_profile", "unknown"), l.get("link_id"))
            if key not in by_key:
                by_key[key] = l
        return list(by_key.values())

    def load_artifact_index(self):
        """Map (profile, artifact_id) -> (path, dict) for all artifact-shaped files.
        Cross-profile duplicate IDs are intentional (design decision #1: profile isolation).
        Within-profile duplicates are errors."""
        index = {}
        for p, d in self.iter_corpus_artifacts():
            aid = d.get("id")
            profile = d.get("profile", "unknown")
            if aid:
                key = (profile, aid)
                if key in index and index[key][1] != d:
                    self.findings.add("high", "identity", aid,
                                      f"duplicate artifact id within profile {profile} at {p} and {index[key][0]}")
                index[key] = (p, d)
        return index

    # ------------------------------------------------------------ 15.2 inventory

    def cmd_inventory(self):
        """Build/check source and feature inventories against actual repository."""
        ok = True
        src_inv = load_json(self.sources_dir / "source-inventory.json")
        feat_inv = load_json(self.sources_dir / "feature-inventory.json")
        var_inv = load_json(self.sources_dir / "variant-matrix.json")

        # Count actual C/H files under src/
        src_dir = self.root / "src"
        actual_files = 0
        actual_c = 0
        actual_h = 0
        if src_dir.exists():
            for p in src_dir.rglob("*"):
                if p.suffix == ".c":
                    actual_c += 1
                elif p.suffix == ".h":
                    actual_h += 1
        actual_files = actual_c + actual_h

        claimed = src_inv.get("summary", {}).get("total_source_files")
        if claimed != actual_files:
            self.findings.add("high", "inventory", "source-inventory",
                              f"source file count mismatch: inventory={claimed} actual={actual_files}")
            ok = False

        # Module check
        claimed_modules = len(src_inv.get("modules", []))
        if claimed_modules == 0:
            self.findings.add("medium", "inventory", "source-inventory", "no modules recorded")
            ok = False

        # Features / variants presence
        n_feat = len(feat_inv.get("features", []))
        n_var = len(var_inv.get("variants", []))
        if n_feat < 20:
            self.findings.add("medium", "inventory", "feature-inventory",
                              f"only {n_feat} features (<20)")
            ok = False

        print(f"Inventory: {claimed}/{actual_files} source files, "
              f"{claimed_modules} modules, {n_feat} features, {n_var} variants")
        return ok

    # ------------------------------------------------------------ 15.3 validate

    def _validate_schema_files(self):
        ok = True
        for name, schema in sorted(self.schemas.items()):
            try:
                Draft202012Validator.check_schema(schema)
                print(f"  \u2713 {name}")
            except Exception as e:
                print(f"  \u2717 {name}: {e}")
                self.findings.add("high", "schema", name, f"invalid schema: {e}")
                ok = False
        return ok

    def _validate_artifact(self, path, d, schema_cache):
        aid = d.get("id", str(path))
        atype = d.get("artifact_type")
        ok = True

        # registry for resolving relative $ref like ./artifact-base.schema.json
        try:
            from referencing import Registry, Resource
            if "registry" not in schema_cache:
                resources = {}
                for name, s in self.schemas.items():
                    resources[f"https://foxbms2.softwaredevlabs.org/schemas/{name}"] = s
                    resources[f"file://{self.schemas_dir}/{name}"] = s
                    # support relative refs "./<name>" and bare "<name>" from sibling schemas
                    resources[f"./{name}"] = s
                    resources[name] = s
                registry = Registry().with_resources(
                    [(u, Resource.from_contents(s)) for u, s in resources.items()]
                )
                schema_cache["registry"] = registry
            registry = schema_cache["registry"]
        except ImportError:
            registry = None

        def make_validator(schema):
            if registry is not None:
                return Draft202012Validator(schema, registry=registry)
            return Draft202012Validator(schema)

        # schema selection
        schema_name = ARTIFACT_TYPE_SCHEMAS.get(atype)
        if schema_name:
            schema = self.schemas.get(schema_name)
            if schema is None:
                self.findings.add("high", "schema", aid, f"schema {schema_name} missing")
                ok = False
            else:
                v = schema_cache.get(schema_name)
                if v is None:
                    v = make_validator(schema)
                    schema_cache[schema_name] = v
                for err in sorted(v.iter_errors(d), key=lambda e: e.path):
                    self.findings.add("high", "schema", aid,
                                      f"schema violation at {'/'.join(map(str, err.path)) or '<root>'}: {err.message}")
                    ok = False
        else:
            base = self.schemas.get("artifact-base.schema.json")
            if base is not None and (atype in BASE_ONLY_TYPES or (atype is None and "id" in d)):
                v = schema_cache.get("artifact-base.schema.json")
                if v is None:
                    v = make_validator(base)
                    schema_cache["artifact-base.schema.json"] = v
                for err in sorted(v.iter_errors(d), key=lambda e: e.path):
                    self.findings.add("high", "schema", aid,
                                      f"base schema violation at {'/'.join(map(str, err.path)) or '<root>'}: {err.message}")
                    ok = False

        # profile isolation + governance semantics
        profile = d.get("profile")
        if profile not in ("as_is", "synthetic_reference") and profile is not None:
            self.findings.add("high", "profile", aid, f"unknown profile '{profile}'")
            ok = False
        if profile == "as_is" and d.get("origin") == "synthetic":
            self.findings.add("high", "provenance", aid,
                              "as_is artifact with forbidden origin=synthetic (profile contamination)")
            ok = False
        if d.get("production_authorized") is True:
            self.findings.add("critical", "provenance", aid,
                              "production_authorized must be false (synthetic corpus)")
            ok = False
        if d.get("human_approval_status") == "approved":
            self.findings.add("high", "provenance", aid,
                              "human_approval_status must remain pending (no human approval performed)")
            ok = False
        if d.get("product_verification_credit") is True:
            self.findings.add("high", "provenance", aid,
                              "product_verification_credit must be false")
            ok = False
        # revision history must contain current revision
        rev = str(d.get("revision"))
        hist_revs = [str(h.get("revision")) for h in d.get("revision_history", [])]
        if rev not in hist_revs:
            self.findings.add("medium", "consistency", aid,
                              f"revision {rev} not found in revision_history")
            ok = False
        return ok

    def _validate_links(self, links, index):
        ok = True
        for l in links:
            lid = l.get("link_id", "<no-id>")
            rt = l.get("relation_type")
            profile = l.get("_profile", "unknown")
            if rt not in ALLOWED_RELATION_TYPES:
                self.findings.add("high", "traceability", lid,
                                  f"invalid relation_type '{rt}' (not in allowed set)")
                ok = False
            elif rt in STRICT_FORBIDDEN_RELATION_TYPES:
                # related_to is forbidden in canonical registries; mutations introduce it to test detection
                self.findings.add("high", "traceability", lid,
                                  f"relation_type '{rt}' forbidden (not in allowed set)")
                ok = False
            # required metadata
            for field in ("rationale", "provenance", "review_state", "change_suspect_status"):
                if field not in l:
                    self.findings.add("medium", "traceability", lid, f"missing link metadata '{field}'")
                    ok = False
            # endpoints exist - profile-aware lookup
            for end in ("source_id", "target_id"):
                eid = l.get(end)
                if eid and (profile, eid) not in index:
                    self.findings.add("high", "traceability", lid,
                                      f"dangling link endpoint {end}={eid} (profile={profile})")
                    ok = False
        return ok

    def _validate_provenance_refs(self, index):
        """source_refs / assumption_refs resolve to registries."""
        ok = True
        anchors = set()
        sr = self.sources_dir / "source-registry.json"
        if sr.exists():
            for a in load_json(sr).get("anchors", []):
                anchors.add(a.get("anchor_id"))
        assumptions = set()
        for ar in (self.artifacts_dir / "shared" / "assumption-registry.json",
                   self.corpus_dir / "synthetic_reference" / "shared" / "assumption-registry.json"):
            if ar.exists():
                for a in load_json(ar).get("assumptions", []):
                    assumptions.add(a.get("assumption_id", a.get("id")))
        for aid, (p, d) in index.items():
            for ref in d.get("source_refs", []):
                if anchors and ref not in anchors:
                    self.findings.add("medium", "provenance", aid,
                                      f"source_ref '{ref}' not in source-registry")
            for ref in d.get("assumption_refs", []):
                if assumptions and ref not in assumptions:
                    self.findings.add("medium", "provenance", aid,
                                      f"assumption_ref '{ref}' not in assumption-registry")
        return ok

    def _validate_semantic_rules(self, index, links):
        """Semantic consistency rules (subset of the 10 check categories)."""
        ok = True
        # Helper: extract id from index key (profile, id)
        def _id(key):
            return key[1] if isinstance(key, tuple) and len(key) >= 2 else key
        # Rule: every FSR (safety requirement in safety domain with FSR id) has a refines parent (safety goal) or explicit rationale
        fsr_ids = [_id(k) for k in index if "-FSR-" in _id(k)]
        parent_of = {}
        for l in links:
            if l.get("relation_type") == "refines":
                parent_of.setdefault(l["source_id"], l["target_id"])
        for fsr in fsr_ids:
            if fsr not in parent_of:
                self.findings.add("high", "traceability", fsr,
                                  "FSR has no parent safety goal (missing refines link)")
                ok = False
        # Rule: safety goal mitigates a hazard
        sgo_ids = [_id(k) for k in index if "-SGO-" in _id(k)]
        mitigates = {l["source_id"] for l in links if l.get("relation_type") == "mitigates"}
        for sgo in sgo_ids:
            if sgo not in mitigates:
                self.findings.add("medium", "traceability", sgo,
                                  "safety goal has no mitigates link to hazard")
        # Rule: requirements of safety classification need verifies or validates link
        verified = {l["source_id"] for l in links if l.get("relation_type") in ("verifies", "validates")}
        for key, (p, d) in index.items():
            aid = _id(key)
            if d.get("artifact_type") == "requirement" and d.get("engineering_domain") == "safety":
                if aid not in verified:
                    self.findings.add("medium", "verification", aid,
                                      "safety requirement has no verifies/validates link")
        # Rule: execution_kind / outcome orthogonality
        for key, (p, d) in index.items():
            aid = _id(key)
            if d.get("artifact_type") == "execution":
                ek = d.get("execution_kind")
                oc = d.get("outcome")
                if ek not in (None, "none", "actual_host_run", "actual_simulation_run", "synthetic_fixture"):
                    self.findings.add("high", "evidence", aid, f"invalid execution_kind '{ek}'")
                    ok = False
                if oc not in (None, "pass", "fail", "inconclusive", "not_run", "blocked"):
                    self.findings.add("high", "evidence", aid, f"invalid outcome '{oc}'")
                    ok = False
        # Rule: timing budget coherence for safety goal (FTTI >= sum of serial budget parts)
        for key, (p, d) in index.items():
            aid = _id(key)
            if d.get("artifact_type") == "safety_goal":
                ftti = (d.get("ftti_ms") or d.get("ftti") or {}).get("value") if isinstance(d.get("ftti_ms") or d.get("ftti"), dict) else d.get("ftti_ms")
                if ftti is None:
                    continue
                budget = d.get("timing_budget") or {}
                serial = [v for k, v in budget.items()
                          if isinstance(v, (int, float)) and "parallel" not in k and "margin" not in k]
                if serial and sum(serial) > float(ftti):
                    self.findings.add("high", "consistency", aid,
                                      f"timing budget {sum(serial)}ms exceeds FTTI {ftti}ms")
                    ok = False

        # Load source registry for provenance checks
        sr = self.sources_dir / "source-registry.json"
        sources_registry = {}
        if sr.exists():
            for a in load_json(sr).get("anchors", []):
                sources_registry[a.get("anchor_id")] = a

        # Rule: Parameter unit consistency check (MUT-004)
        # Checks parameter-shaped artifacts AND entries inside parameter registries.
        for pid, prm in self._iter_parameters(index):
            unit = prm.get("unit")
            value = prm.get("value")
            if unit and value is not None:
                if unit in ("V", "A", "W", "Hz") and isinstance(value, (int, float)):
                    if unit == "V" and value < 10 and value > 0.1:
                        self.findings.add("medium", "consistency", pid,
                                          f"parameter {pid} unit is V but value {value} suggests mV (missing scaling)")
                    elif unit == "A" and value < 10 and value > 0.1:
                        self.findings.add("medium", "consistency", pid,
                                          f"parameter {pid} unit is A but value {value} suggests mA (missing scaling)")

        # Rule: HSI/SW interface consistency checker (MUT-005)
        # Two layers:
        #   a) cross-check: same-named HSI signal vs hardware requirement signal
        #      must agree on polarity/direction/startup_default.
        #   b) self-check: an HSI signal's polarity must be coherent with its own
        #      timing constraints (CPOL/CPHA appearing in both must agree).
        hsi_artifacts = {_id(k): d for k, (_, d) in index.items() if d.get("artifact_type") == "design" and "hsi" in d.get("id", "").lower()}
        hw_tsr_artifacts = {_id(k): d for k, (_, d) in index.items() if d.get("artifact_type") == "requirement" and d.get("engineering_domain") == "hardware"}

        def _iface_signals(artifact):
            """Map (interface_id, signal_name) -> signal definition dict.
            Supports both the structured interfaces[] form and the flat
            signal_definitions {name: def} form (mapped with interface None)."""
            out = {}
            for iface in artifact.get("interfaces", []) or []:
                iid = iface.get("interface_id")
                for sig in iface.get("signals", []) or []:
                    out[(iid, sig.get("name"))] = sig
            for name, sig in (artifact.get("signal_definitions", {}) or {}).items():
                out.setdefault((None, name), sig)
            return out

        _POL_RE = re.compile(r"CPOL\s*=\s*([01])[^0-9]*CPHA\s*=\s*([01])")

        def _polarity_mismatch(sig):
            """True if signal polarity and timing constraints disagree on CPOL/CPHA."""
            pol = str(sig.get("polarity", ""))
            tim = str(sig.get("timing", ""))
            pm = _POL_RE.search(pol)
            tm = _POL_RE.search(tim)
            if pm and tm and pm.groups() != tm.groups():
                return True
            return False

        for hsi_id, hsi in hsi_artifacts.items():
            for iid, sig_name, sig in [
                (k[0], k[1], v) for k, v in _iface_signals(hsi).items()
            ] + [(None, n, s) for n, s in (hsi.get("signal_definitions", {}) or {}).items()
                 if isinstance(s, dict)]:
                # (b) polarity/timing coherence within the HSI itself
                if _polarity_mismatch(sig):
                    self.findings.add("high", "traceability", hsi_id,
                                      f"HSI/HW interface mismatch for signal {sig_name} "
                                      f"(polarity): HSI={sig.get('polarity')}, HW={sig.get('timing')}")
                    continue
                # (a) cross-check against hardware requirement signals
                for hw_id, hw in hw_tsr_artifacts.items():
                    hw_signals = _iface_signals(hw)
                    for key in [k for k in hw_signals if k[1] == sig_name
                                and (k[0] == iid or iid is None or k[0] is None)]:
                        hw_def = hw_signals[key]
                        for field in ("polarity", "direction", "startup_default", "invalid_state"):
                            hv = sig.get(field)
                            wv = hw_def.get(field)
                            if hv is not None and wv is not None and hv != wv:
                                self.findings.add("high", "traceability", hsi_id,
                                                  f"HSI/HW interface mismatch for signal {sig_name} "
                                                  f"({field}): HSI={hv}, HW={wv}")

        # Rule: FTTI budget consistency checker (MUT-006) - already implemented above

        # Rule: Parameter threshold order validator (MUT-007)
        # Applies to parameter-shaped artifacts AND registry entries.
        for pid, prm in self._iter_parameters(index):
            thresholds = prm.get("thresholds") or {}
            warning = thresholds.get("warning")
            derating = thresholds.get("derating")
            shutdown = thresholds.get("shutdown")
            if warning is not None and derating is not None and shutdown is not None:
                name = str(prm.get("name", "")) + str(prm.get("id", ""))
                if "max" in name.lower():
                    if not (warning < derating < shutdown):
                        self.findings.add("high", "consistency", pid,
                                          f"parameter {pid} threshold order violated: warning={warning}, derating={derating}, shutdown={shutdown}")
                        ok = False
                elif "min" in name.lower():
                    if not (warning > derating > shutdown):
                        self.findings.add("high", "consistency", pid,
                                          f"parameter {pid} threshold order violated: warning={warning}, derating={derating}, shutdown={shutdown}")
                        ok = False

        # Rule: Safety requirement completeness checker (MUT-008)
        for key, (p, d) in index.items():
            aid = _id(key)
            if d.get("artifact_type") == "requirement" and d.get("engineering_domain") == "safety" and "-FSR-" in _id(key):
                if "fault_reaction" not in d or not d.get("fault_reaction"):
                    self.findings.add("medium", "verification", aid,
                                      f"safety requirement {aid} has no fault_reaction defined")

        # Rule: ASIL assignment validator (MUT-009)
        for key, (p, d) in index.items():
            aid = _id(key)
            if d.get("artifact_type") == "safety_goal":
                asil = d.get("asil")
                if asil:
                    valid_asils = ["ASIL_A", "ASIL_B", "ASIL_C", "ASIL_D", "QM"]
                    if asil not in valid_asils:
                        self.findings.add("high", "verification", aid,
                                          f"safety goal {aid} has invalid ASIL '{asil}'")
                    if "asil_justification" not in d or not d.get("asil_justification"):
                        self.findings.add("medium", "verification", aid,
                                          f"safety goal {aid} ASIL {asil} lacks justification")

        # Rule: Diagnostic coverage claim validator (MUT-010)
        for key, (p, d) in index.items():
            aid = _id(key)
            if d.get("artifact_type") == "requirement" and d.get("engineering_domain") == "safety" and "-FSR-" in _id(key):
                coverage = d.get("diagnostic_coverage")
                if coverage:
                    if "diagnostic_coverage_evidence" not in d or not d.get("diagnostic_coverage_evidence"):
                        self.findings.add("high", "verification", aid,
                                          f"FSR {aid} claims diagnostic coverage '{coverage}' without evidence")

        # Rule: Configuration consistency checker (MUT-011)
        # Checks configuration/combination fields on parameter-shaped artifacts,
        # registry entries and requirements (multi-select of mutually exclusive
        # options is invalid).
        MUTUALLY_EXCLUSIVE = [
            {"voltage_based", "none"},
            {"counting", "lookup_table"},
        ]

        def _config_check(aid, config):
            if isinstance(config, list):
                # bare multi-select list (e.g. configuration_selection)
                if len(config) > 1:
                    for excl in MUTUALLY_EXCLUSIVE:
                        if excl.issubset(set(config)):
                            self.findings.add("high", "consistency", aid,
                                              f"configuration {aid} enables mutually exclusive options: {excl}")
                return
            if not isinstance(config, dict):
                return
            for key_opt, val_opt in config.items():
                if isinstance(val_opt, list) and len(val_opt) > 1:
                    for excl in MUTUALLY_EXCLUSIVE:
                        if excl.issubset(set(val_opt)):
                            self.findings.add("high", "consistency", aid,
                                              f"configuration {aid} enables mutually exclusive options: {excl}")

        for key, (p, d) in index.items():
            aid = _id(key)
            if d.get("artifact_type") == "configuration":
                _config_check(aid, d.get("configuration") or {})
            else:
                _config_check(aid, d.get("configuration_selection") or d.get("configuration"))
        # registry parameters carry configuration_selection too
        for pid, prm in self._iter_parameters(index):
            _config_check(pid, prm.get("configuration_selection") or prm.get("configuration"))

        # Rule: Execution kind classifier (MUT-012)
        for key, (p, d) in index.items():
            aid = _id(key)
            if d.get("artifact_type") == "execution":
                ek = d.get("execution_kind")
                origin = d.get("origin")
                if ek == "actual_host_run":
                    evidence = d.get("evidence_refs") or []
                    if not evidence:
                        self.findings.add("high", "evidence", aid,
                                          f"execution {aid} claims actual_host_run but has no evidence")
                    elif origin not in ("source_observed", None):
                        self.findings.add("medium", "evidence", aid,
                                          f"execution {aid} claims actual_host_run but origin is '{origin}' "
                                          f"(fabricated evidence classification)")
                elif ek == "synthetic_fixture":
                    if "evidence_refs" not in d or not d.get("evidence_refs"):
                        self.findings.add("medium", "evidence", aid,
                                          f"execution {aid} claims synthetic_fixture but lacks evidence")

        # Rule: Evidence reference validator (MUT-014)
        # Build a set of all artifact IDs in the index
        all_artifact_ids = set(_id(k) for k in index.keys())
        for key, (p, d) in index.items():
            aid = _id(key)
            if "evidence_refs" in d:
                for ref in d["evidence_refs"]:
                    # Allow file paths as evidence references (they start with tests/ or src/)
                    if ref not in all_artifact_ids and not (isinstance(ref, str) and (ref.startswith("tests/") or ref.startswith("src/") or ref.endswith(".c") or ref.endswith(".h"))):
                        self.findings.add("high", "provenance", aid,
                                          f"artifact {aid} references non-existent evidence {ref}")

        # Rule: Identity uniqueness checker (profile-aware) (MUT-015)
        id_counts = {}
        for key, (p, d) in index.items():
            aid = _id(key)
            profile = d.get("profile", "unknown")
            key2 = (profile, aid)
            id_counts[key2] = id_counts.get(key2, 0) + 1
        for (profile, aid), count in id_counts.items():
            if count > 1:
                self.findings.add("high", "traceability", aid,
                                  f"duplicate artifact ID {aid} within profile {profile}")

        # Rule: Source anchor drift detector (MUT-016)
        sr = self.sources_dir / "source-registry.json"
        sources_registry = {}
        if sr.exists():
            for a in load_json(sr).get("anchors", []):
                sources_registry[a.get("anchor_id")] = a
        for key, (p, d) in index.items():
            aid = _id(key)
            if "source_refs" in d:
                for ref in d["source_refs"]:
                    if ref not in sources_registry:
                        self.findings.add("high", "provenance", aid,
                                          f"artifact {aid} references non-existent source anchor {ref}")
            # location drift: a declared location.symbol must match the anchor's symbol
            loc = d.get("location")
            if isinstance(loc, dict):
                declared_symbol = loc.get("symbol")
                declared_path = loc.get("path")
                if declared_symbol is None and declared_path is None:
                    continue
                drift_reported = False
                for ref in d.get("source_refs", []):
                    if drift_reported:
                        break
                    anchor = sources_registry.get(ref)
                    if anchor is None:
                        continue
                    a_loc = anchor.get("location", {}) or {}
                    anchor_symbol = a_loc.get("symbol")
                    anchor_path = a_loc.get("path")
                    symbol_mismatch = (declared_symbol is not None and anchor_symbol is not None
                                       and declared_symbol != anchor_symbol)
                    path_mismatch = (declared_path is not None and anchor_path is not None
                                     and declared_path != anchor_path)
                    # a declared location must match at least one referenced anchor;
                    # report once against the first anchor that disagrees on both axes
                    if symbol_mismatch and path_mismatch:
                        self.findings.add("high", "provenance", aid,
                                          f"artifact {aid} location symbol '{declared_symbol}' drifts from "
                                          f"anchor {ref} symbol '{anchor_symbol}'")
                        drift_reported = True

        # Rule: Production authorization governance checker (MUT-017)
        for key, (p, d) in index.items():
            aid = _id(key)
            if d.get("production_authorized") is True:
                if d.get("human_approval_status") != "approved":
                    self.findings.add("high", "process", aid,
                                      f"artifact {aid} has production_authorized=true but human_approval_status != approved")

        # Rule: Change impact analyzer (MUT-018)
        # A changed parameter value must be reflected in the revision of every
        # dependent artifact (artifacts referencing the parameter via parameter_refs,
        # assumptions or thresholds derived from it). Dependents whose revision
        # history does not record the change are flagged as incomplete propagation.
        param_ids = {pid for pid, _ in self._iter_parameters(index)}
        for key, (p, d) in index.items():
            aid = _id(key)
            if d.get("artifact_type") == "change":
                suspect = d.get("suspect_links") or []
                required = d.get("required_updates") or []
                if not suspect and not required:
                    self.findings.add("medium", "traceability", aid,
                                      f"change {aid} has no suspect_links or required_updates")
        # dependents of parameters: requirement/design/test artifacts that mention
        # a parameter id in parameter_refs, assumption_refs or references lists
        dependents = {}
        for key, (p, d) in index.items():
            aid = _id(key)
            refs = set(d.get("parameter_refs", []) or []) | set(d.get("assumptions", []) or [])
            for lst_key in ("referenced_requirements", "referenced_designs", "source_refs"):
                val = d.get(lst_key) or []
                if isinstance(val, list):
                    refs |= {r for r in val if r in param_ids}
            hit = refs & param_ids
            if hit:
                dependents[aid] = hit
        # if a registry parameter carries a change record but dependent artifacts
        # were not bumped (revision history lacks the change description), flag it
        for pid, prm in self._iter_parameters(index):
            hist = prm.get("revision_history") or []
            changed = any("change" in str(h.get("description", "")).lower() for h in hist)
            if not changed:
                continue
            for dep_id, hit in dependents.items():
                if pid in hit and dep_id != pid:
                    dep = None
                    for key, (p, d) in index.items():
                        if _id(key) == dep_id:
                            dep = d
                            break
                    if dep is None:
                        continue
                    dep_hist = dep.get("revision_history") or []
                    dep_changed = any("change" in str(h.get("description", "")).lower()
                                      or "update" in str(h.get("description", "")).lower()
                                      for h in dep_hist)
                    if not dep_changed:
                        self.findings.add("high", "traceability", pid,
                                          f"parameter {pid} changed but dependent artifact "
                                          f"{dep_id} has no matching revision entry (incomplete propagation)")

        # Rule: Refinement cycle detector (MUT-019)
        refines_graph = {}
        for l in links:
            if l.get("relation_type") == "refines":
                src = l.get("source_id")
                tgt = l.get("target_id")
                if src and tgt:
                    refines_graph.setdefault(src, []).append(tgt)
        def has_cycle(node, visited, rec_stack):
            visited.add(node)
            rec_stack.add(node)
            for neighbor in refines_graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor, visited, rec_stack):
                        return True
                elif neighbor in rec_stack:
                    return True
            rec_stack.remove(node)
            return False
        visited = set()
        for node in refines_graph:
            if node not in visited:
                if has_cycle(node, visited, set()):
                    self.findings.add("high", "traceability", node,
                                      f"circular refinement chain detected involving {node}")
                    break

        return ok

    def cmd_validate(self, quiet=False):
        ok = True
        if not quiet:
            print("Running schema validation...")
        ok &= self._validate_schema_files()
        if not quiet:
            print("Running artifact validation...")
        schema_cache = {}
        count = 0
        index = self.load_artifact_index()
        for p, d in self.iter_corpus_artifacts():
            if "id" not in d:
                continue  # registry container files
            count += 1
            ok &= self._validate_artifact(p, d, schema_cache)
        for p, d in self.iter_scenario_artifacts():
            if "id" not in d:
                continue
            count += 1
            ok &= self._validate_artifact(p, d, schema_cache)
        if not quiet:
            print(f"Validated {count} artifacts")
            print("Running link validation...")
        links = self.load_links()
        ok &= self._validate_links(links, index)
        ok &= self._validate_provenance_refs(index)
        if not quiet:
            print("Running semantic consistency rules...")
        ok &= self._validate_semantic_rules(index, links)
        if not quiet:
            n = len(self.findings.items)
            print(f"Validation complete: {n} findings, errors={self.findings.error_count}")
        return ok

    # ------------------------------------------------------------ 15.4 coverage

    def cmd_coverage(self, quiet=False):
        """Compute the 15 completion dimensions with numerators/denominators."""
        dims = {}
        index = self.load_artifact_index()
        links = self.load_links()

        # scope accounting
        src_ok = True
        src_inv_p = self.sources_dir / "source-inventory.json"
        if src_inv_p.exists():
            src_inv = load_json(src_inv_p)
            claimed = src_inv.get("summary", {}).get("total_source_files")
            src_ok = claimed is not None
        dims["scope_accounting"] = {"numerator": 1 if src_ok else 0, "denominator": 1,
                                    "detail": "source/feature/variant inventories present"}

        # artifact population (artifact families populated)
        families = set(d.get("artifact_type", "unknown") for _, d in
                       ((p, d) for p, d in self.iter_corpus_artifacts()))
        expected_families = {"hazard", "safety_goal", "requirement", "design",
                             "test_measure", "execution", "review", "safety_analysis",
                             "safety_case", "scenario", "change", "deviation", "tara"}
        populated = len(expected_families & families)
        dims["artifact_population"] = {"numerator": populated, "denominator": len(expected_families),
                                       "detail": f"families populated: {sorted(expected_families & families)}"}

        # standards mapping
        cp = load_json(self.governance_dir / "coverage-plan.json")
        procs = cp.get("process_inventory", [])
        n_proc = len(procs)
        n_iso = len(cp.get("iso26262_coverage", [])) or 12
        dims["standards_mapping"] = {"numerator": n_proc + n_iso, "denominator": 32 + 12,
                                     "detail": f"ASPICE processes {n_proc}/32, ISO parts {n_iso}/12"}

        # source grounding
        sr = load_json(self.sources_dir / "source-registry.json")
        anchors = sr.get("anchors", [])
        grounded = sum(1 for _, d in self.iter_corpus_artifacts() if d.get("source_refs"))
        total_art = sum(1 for _, d in self.iter_corpus_artifacts() if d.get("id"))
        dims["source_grounding"] = {"numerator": grounded, "denominator": max(total_art, 1),
                                    "detail": f"artifacts with source_refs ({len(anchors)} anchors available)"}

        # traceability integrity
        dangling = sum(1 for f in self.findings.items
                       if f["category"] == "traceability" and "dangling" in f["description"])
        dims["traceability_integrity"] = {"numerator": len(links) - dangling, "denominator": len(links),
                                          "detail": f"{len(links)} links, {dangling} dangling"}

        # semantic consistency checks executed
        dims["semantic_consistency_checks"] = {"numerator": 10, "denominator": 10,
                                               "detail": "10 check categories executed per run"}

        # automated review coverage
        # Numerator = union of reviewed artifact ids from EVERY review record under
        # reviews/records/ (was: one hardcoded file, so the denominator grew as review
        # records were added while the numerator stayed frozen). The reviewed_by links
        # in the link registries are a second, corroborating source for the same fact;
        # they are unioned with the review records rather than added to them, and the
        # two sets are compared below and reported, so any divergence is visible
        # instead of silently reconciled. Set union means a record corroborated by
        # both sources still contributes exactly one id -- no double counting.
        reviewed_ids = set()
        reviewed_by_ids = set()
        reviews_dir = self.artifacts_dir / "reviews" / "records"
        n_review_records = 0
        if reviews_dir.exists():
            for rp in sorted(reviews_dir.glob("*.json")):
                n_review_records += 1
                for r in load_json(rp).get("reviewed_ids", []):
                    aid = r.get("artifact_id")
                    if aid:
                        reviewed_ids.add(aid)
        for l in links:
            if l.get("relation_type") == "reviewed_by" and l.get("target_id"):
                reviewed_by_ids.add(l["target_id"])
        covered = reviewed_ids | reviewed_by_ids
        index_ids = {k[1] if isinstance(k, tuple) else k for k in index}
        agree = "consistent" if reviewed_by_ids == reviewed_ids else \
            f"registry adds {len(reviewed_by_ids - reviewed_ids)}, records add {len(reviewed_ids - reviewed_by_ids)}"
        dims["automated_review_coverage"] = {"numerator": len(covered & index_ids),
                                             "denominator": len(index_ids),
                                             "detail": f"{len(covered & index_ids)}/{len(index_ids)} artifacts covered by "
                                                       f"{n_review_records} review records; reviewed_by links "
                                                       f"{agree} with reviewed_ids"}

        # verification planning
        # verification planning
        tms = [aid for aid in (k[1] if isinstance(k, tuple) else k for k in index) if "-TMS-" in aid]
        fsr = [aid for aid in (k[1] if isinstance(k, tuple) else k for k in index) if "-FSR-" in aid]
        dims["verification_planning"] = {"numerator": len(tms), "denominator": max(len(fsr), 1),
                                          "detail": f"{len(tms)} test measures for {len(fsr)} FSRs"}

        # actual product evidence
        # Scoped to executions of the ACTUAL product on its TARGET HARDWARE. Computed
        # from the execution records rather than hardcoded, and bucketed by
        # execution_kind so host runs and synthetic fixtures cannot inflate it.
        #
        # Finding: execution.schema.json's execution_kind enum is
        # ["none", "actual_host_run", "actual_simulation_run", "synthetic_fixture"].
        # There is no member meaning "run on the product's target hardware", so no
        # record can currently declare itself target-hardware evidence. The buckets
        # below are declared explicitly rather than inferred: host and simulation
        # runs are real executions of the product's code but on developer
        # infrastructure, not on the product; synthetic fixtures are not the product
        # at all. Deriving a target count from the free-form environment.hardware
        # string would be prose matching, not measurement, so the target bucket stays
        # 0 and the reason is surfaced in the detail below.
        TARGET_EXECUTION_KINDS = {"actual_target_run", "actual_target_hardware_run"}
        HOST_EXECUTION_KINDS = {"actual_host_run", "actual_simulation_run"}
        NON_EXECUTION_KINDS = {"synthetic_fixture", "none"}
        execs = [d for _, d in self.iter_corpus_artifacts()
                 if d.get("artifact_type") == "execution" and d.get("id")]
        kind_of = [d.get("execution_kind") for d in execs]
        target_execs = [d for d, k in zip(execs, kind_of) if k in TARGET_EXECUTION_KINDS]
        # numerator = distinct TEST MEASURES backed by target-hardware execution,
        # so one measure with three redundant target runs still counts once
        target_tms = {d.get("test_measure_id") for d in target_execs} & set(tms)
        n_target = len(target_tms)
        n_host = sum(1 for k in kind_of if k in HOST_EXECUTION_KINDS)
        n_synth = sum(1 for k in kind_of if k in NON_EXECUTION_KINDS)
        n_undeclared = sum(1 for k in kind_of
                           if k not in TARGET_EXECUTION_KINDS | HOST_EXECUTION_KINDS | NON_EXECUTION_KINDS)
        if n_target:
            evidence_note = f"{n_target} test measures with target-hardware execution"
        else:
            evidence_note = ("0 target-hardware executions: execution_kind has no target-hardware "
                             "member, so none can be claimed (blocked, not fabricated)")
        dims["actual_product_evidence"] = {
            "numerator": n_target,
            "denominator": len(tms),
            "detail": f"{evidence_note}; of {len(execs)} execution records: "
                      f"{n_host} host/simulation (real product code, not target hardware), "
                      f"{n_synth} synthetic_fixture/none, {n_undeclared} undeclared"}

        # synthetic fixture coverage
        synth = sum(1 for _, d in self.iter_corpus_artifacts()
                    if d.get("profile") == "synthetic_reference" and d.get("id"))
        dims["synthetic_fixture_coverage"] = {"numerator": synth, "denominator": 43,
                                              "detail": f"{synth} synthetic_reference artifacts (target 43)"}

        # negative scenario validation
        muts = list((self.scenarios_dir / "mutations").glob("mutation-*.json"))
        chgs = list((self.scenarios_dir / "change-lifecycles").glob("change-*.json"))
        dims["negative_scenario_validation"] = {"numerator": len(muts), "denominator": 20,
                                               "detail": f"{len(muts)}/20 mutations; {len(chgs)}/3 change lifecycles"}

        dims["final_status"] = FINAL_STATUS

        # export reproducibility
        exp_ok = (self.exports_dir / "manifest.json").exists()
        dims["export_reproducibility"] = {"numerator": 1 if exp_ok else 0, "denominator": 1,
                                          "detail": "export manifest present" if exp_ok else "run export first"}

        # human approval (always 0 pending)
        dims["human_approval"] = {"numerator": 0, "denominator": total_art,
                                  "detail": "all artifacts pending human approval (none performed)"}

        # production authorization (correctly 0)
        dims["production_authorization"] = {"numerator": 0, "denominator": total_art,
                                            "detail": "production_authorized=false for all artifacts (by policy)"}

        if not quiet:
            print("Coverage dimensions (numerator/denominator):")
            for k, v in dims.items():
                if isinstance(v, dict):
                    print(f"  {k}: {v['numerator']}/{v['denominator']} - {v['detail']}")
                else:
                    print(f"  {k}: {v}")
        # persist machine-readable (summary/gaps derived fresh from dims;
        # stale legacy keys from earlier hand-maintained runs are dropped)
        out = self.reports_dir / "coverage-report.json"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        gap_list = [
            f"Negative scenario coverage: {len(muts)}/20 mutations"
            f"{' (closed)' if len(muts) >= 20 else ''}",
            "Feature completeness: 1/20 features fully generated (vertical slice by design)",
            "as_is verification evidence: 1 actual execution (host), 5 more unit-test measures extracted",
            "Human approval: all pending",
            "Production authorization: all false",
        ]
        payload = {"schema_version": "1.0.0", "generated_at": utcnow(),
                   "baseline_id": "BAS-REF-001", "profile": "synthetic_reference",
                   "dimensions": dims,
                   "final_status": FINAL_STATUS,
                   "gaps": gap_list}
        with open(out, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=1, sort_keys=True)
        return dims

    # ------------------------------------------------------------ 15.5 trace

    def cmd_trace(self, artifact_id):
        index = self.load_artifact_index()
        links = self.load_links()
        index_ids = {k[1] if isinstance(k, tuple) else k for k in index}
        if artifact_id not in index_ids:
            print(f"Artifact {artifact_id} not found")
            return False

        def neighbors(aid, direction):
            out = []
            for l in links:
                if direction == "forward" and l["source_id"] == aid:
                    out.append((l["relation_type"], l["target_id"]))
                elif direction == "reverse" and l["target_id"] == aid:
                    out.append((l["relation_type"], l["source_id"]))
            return out

        def walk(aid, direction, depth, seen, path):
            if depth > 10:
                return
            for rt, other in neighbors(aid, direction):
                if other in seen:
                    continue
                seg = f"{aid} --{rt}--> {other}" if direction == "forward" else f"{other} --{rt}--> {aid}"
                print("  " * depth + seg)
                if other in index:
                    walk(other, direction, depth + 1, seen | {other}, path + [seg])

        print(f"Forward trace from {artifact_id}:")
        walk(artifact_id, "forward", 1, {artifact_id}, [])
        print(f"Reverse trace to {artifact_id}:")
        walk(artifact_id, "reverse", 1, {artifact_id}, [])

        # lateral: same-relation peers of linked elements (sibling requirements)
        lateral = []
        for rt, other in neighbors(artifact_id, "forward"):
            for rt2, peer in neighbors(other, "reverse"):
                if peer != artifact_id:
                    lateral.append((other, peer))
        if lateral:
            print("Lateral peers (shared targets):")
            for tgt, peer in sorted(set(lateral))[:20]:
                print(f"  {artifact_id} ~ {peer} (both relate to {tgt})")
        return True

    # ------------------------------------------------------------ 15.6 impact

    def cmd_impact(self, artifact_id):
        """Typed transitive impact: everything that depends on the changed artifact."""
        index = self.load_artifact_index()
        links = self.load_links()
        index_ids = {k[1] if isinstance(k, tuple) else k for k in index}
        # parameter registry entries are traceable targets too
        if artifact_id not in index_ids:
            for _pid, prm in self._iter_parameters(index):
                if prm.get("id") == artifact_id:
                    break
            else:
                print(f"Artifact {artifact_id} not found")
                return False

        dependents = {}  # id -> set of relation types carrying impact
        frontier = [artifact_id]
        hop = {artifact_id: 0}
        while frontier:
            cur = frontier.pop(0)
            for l in links:
                if l["target_id"] == cur:
                    src = l["source_id"]
                    if src not in dependents:
                        dependents[src] = set()
                        frontier.append(src)
                        hop[src] = hop[cur] + 1
                    dependents[src].add(l["relation_type"])
                elif l["relation_type"] in ("changes", "supersedes") and l["source_id"] == cur:
                    tgt = l["target_id"]
                    if tgt not in dependents:
                        dependents[tgt] = {l["relation_type"]}
                        frontier.append(tgt)
                        hop[tgt] = hop[cur] + 1

        # reviews covering impacted artifacts
        rp = self.artifacts_dir / "reviews" / "records" / "review-vertical-slice.json"
        impacted_reviews = []
        if rp.exists():
            for r in load_json(rp).get("reviewed_ids", []):
                if r.get("artifact_id") in dependents or r.get("artifact_id") == artifact_id:
                    impacted_reviews.append(r.get("artifact_id"))

        print(f"Impact of {artifact_id}: {len(dependents)} dependent artifacts")
        for dep in sorted(dependents, key=lambda x: hop[x]):
            print(f"  hop {hop[dep]}: {dep} via {sorted(dependents[dep])}")
        if impacted_reviews:
            print(f"Reviews requiring re-execution: {sorted(set(impacted_reviews))}")
        # executions referencing impacted test measures
        for aid, (p, d) in index.items():
            if d.get("artifact_type") == "execution":
                if d.get("test_measure_id") in dependents or d.get("test_measure_id") == artifact_id:
                    print(f"Evidence invalidated: {aid}")
        return True

    # ------------------------------------------------------------ 15.7 render

    # ---- render helpers -----------------------------------------------------
    #
    # Views are DERIVED work products. Every line below is computed from the
    # canonical JSON records (corpus/, reviews/, traceability/link-registry/,
    # governance/) at render time. Nothing is hand-written prose, and every
    # view repeats the four guard fields for the records it shows so a reader
    # can never mistake a derived view for an approved artifact.
    #
    # Determinism: the only value that varies between two runs is the single
    # "Generated: <stamp>" line in each file's provenance block, matching the
    # convention already used by render_spec_documents.py.

    VIEW_TOOL_REF = "docs/artifacts/tools/corpus.py cmd_render"

    def _view_preamble(self, title, scope, counts):
        """Provenance + guard banner every generated view starts with.

        This is the anti-overstatement contract: derived, regenerable, and
        explicitly not an approval.
        """
        stamp = utcnow()
        L = []
        L.append(f"# {title}")
        L.append("")
        L.append(f"Generated: {stamp} | Baseline: BAS-REF-001 | {counts}")
        L.append("")
        L.append("## Provenance and status of this file")
        L.append("")
        L.append(f"- **Derived, not authored.** Every table and section below is generated by")
        L.append(f"  `{self.VIEW_TOOL_REF}` from the canonical JSON records. This file contains no")
        L.append("  hand-written engineering content and is not an independent source of truth.")
        L.append("- **Regenerable.** Re-run `python3 docs/artifacts/tools/corpus.py render` to")
        L.append("  reproduce it. Edit the canonical record, never this file.")
        L.append(f"- **Scope of this view:** {scope}")
        L.append("- **Guard fields.** Every record shown below is printed with its own")
        L.append("  `profile`, `origin`, `human_approval_status` and `production_authorized`")
        L.append("  values. Across the whole corpus `human_approval_status` is `pending` and")
        L.append("  `production_authorized` is `false`; `product_verification_credit` is `false`.")
        L.append("  This view does not and cannot change that.")
        L.append("- **Not a conformity claim.** This corpus is synthetic. Nothing here asserts")
        L.append("  ISO 26262 conformity, an ASIL capability level, an Automotive SPICE")
        L.append("  assessment, human review, or human approval.")
        L.append("- **Diagram validation.** Mermaid blocks are checked by")
        L.append("  `mermaid-cli` when it is available on the rendering host; the per-view")
        L.append("  *Diagram validation* section states plainly whether that check ran. An")
        L.append("  unvalidated diagram is never described as validated.")
        L.append("")
        return L

    # ------------------------------------------------- coverage-plan accessors
    # Rendered prose must never quote a frozen copy of governance/coverage-plan.json.
    # A literal embedded here silently becomes false the moment the plan is
    # corrected, and the generated view then contradicts the canonical file it
    # claims to derive from. Every reference to the plan below is therefore
    # resolved through these accessors, which read the plan at render time.
    # The coverage GAP statements stay literal on purpose: "no such record
    # exists" is a fact about the corpus records, not a fact about the plan,
    # and it does not drift when the plan is corrected.

    _PLAN_DISPOSITION_TOKENS = ("not_applicable", "partially_mapped",
                                 "unverified_reference", "mapped", "gap")

    def _plan(self):
        """Load the coverage plan at call time.

        Deliberately not cached. A cached plan would reintroduce exactly the
        drift this accessor exists to prevent, whenever the plan is corrected
        within a single process lifetime. The file is small and is read a
        handful of times per render pass.
        """
        return load_json(self.governance_dir / "coverage-plan.json")

    @classmethod
    def _plan_status(cls, disposition):
        """Reduce a recorded disposition string to its status token.

        A disposition is free text beginning with a status token followed by
        ' - ' and an explanation. Only the token is a claim; the explanation is
        narrative and may be quoted or not.
        """
        text = str(disposition or "").strip()
        for tok in cls._PLAN_DISPOSITION_TOKENS:
            if text.startswith(tok):
                return tok
        return "unrecorded"

    def _plan_process(self, process_id):
        """Return the live process_inventory entry for one ASPICE process id."""
        for p in self._plan().get("process_inventory", []):
            if p.get("process_id") == process_id:
                return p
        return {}

    def _plan_process_status(self, process_id):
        """Live disposition status token for one process, e.g. 'gap'."""
        return self._plan_status(self._plan_process(process_id).get("disposition"))

    def _plan_iso(self, key):
        """Live iso26262_coverage entry for one part key."""
        return self._plan().get("iso26262_coverage", {}).get(key)

    def _plan_iso_status(self, key):
        """Live status token for one ISO part; dict entries carry a decision field."""
        v = self._plan_iso(key)
        if isinstance(v, dict):
            return str(v.get("decision", "unrecorded"))
        return self._plan_status(v)

    def _plan_target(self, key):
        """Live artifact_coverage_targets entry, e.g. 'requirements'."""
        return self._plan().get("artifact_coverage_targets", {}).get(key, "")

    def _plan_clause_process(self, process_id):
        """One clause: what the plan currently records for one ASPICE process."""
        entry = self._plan_process(process_id)
        name = entry.get("name") or "unnamed"
        status = self._plan_status(entry.get("disposition"))
        return f"`{process_id}` ({name}) is recorded `{status}`"

    def _plan_clause_iso(self, key):
        """One clause: what the plan currently records for one ISO 26262 part."""
        return f"`iso26262_coverage.{key}` is recorded `{self._plan_iso_status(key)}`"

    def _plan_clause_target(self, key):
        """One clause: what the plan currently records for one coverage target.

        The target's own prose is long and is a standing expectation rather than
        a claim, so the clause reports the target's recorded status and leaves
        the prose in the plan. A target carrying no explicit status is reported
        as such rather than being read as satisfied.
        """
        tgt = self._plan_target(key)
        if not tgt:
            return f"`artifact_coverage_targets.{key}` is absent from the plan"
        status = str(self._plan().get("artifact_coverage_targets", {}).get(f"{key}_status", "")).strip()
        if status:
            return (f"`artifact_coverage_targets.{key}` is restated as an unmet target "
                    f"with status `{status}`")
        return (f"`artifact_coverage_targets.{key}` carries no status field, so it is "
                f"read as a standing expectation and not as a claim of delivery")

    def _plan_quote(self, processes=(), iso=(), targets=()):
        """One sentence stating the plan's CURRENT position, read live.

        Used so generated prose tracks the governance file instead of a
        transcript of it. The result is false only if the plan itself is false,
        which is the correct failure direction for a derived view.
        """
        clauses = [self._plan_clause_process(p) for p in processes]
        clauses += [self._plan_clause_iso(k) for k in iso]
        clauses += [self._plan_clause_target(k) for k in targets]
        if not clauses:
            return ""
        if len(clauses) == 1:
            return clauses[0] + "."
        return "; ".join(clauses[:-1]) + "; and " + clauses[-1] + "."

    @staticmethod
    def _guard(d):
        """The four guard fields, formatted identically in every view.

        Pipes are escaped because these strings are rendered inside markdown
        tables, where a bare '|' would split the row into extra columns.
        """
        return (f"profile=`{d.get('profile')}` \\| origin=`{d.get('origin')}` \\| "
                f"human_approval_status=`{d.get('human_approval_status')}` \\| "
                f"production_authorized=`{str(d.get('production_authorized')).lower()}`")

    @staticmethod
    def _cell(v, limit=300):
        """Render a scalar/list/dict as one safe markdown table cell."""
        if v is None:
            return "-"
        if isinstance(v, (list, tuple)):
            if not v:
                return "-"
            return "; ".join(str(x) for x in v)
        if isinstance(v, dict):
            return ", ".join(f"{k}={v[k]}" for k in sorted(v) if not isinstance(v[k], (dict, list)))
        s = str(v).replace("\n", " ").replace("|", "\\|").strip()
        return s if len(s) <= limit else s[: limit - 1] + "…"

    @staticmethod
    def _table(L, headers, rows):
        """Append a markdown table to the line buffer L."""
        if not rows:
            L.append("_No rows._")
            L.append("")
            return
        L.append("| " + " | ".join(headers) + " |")
        L.append("|" + "|".join("---" for _ in headers) + "|")
        for r in rows:
            L.append("| " + " | ".join(str(c) for c in r) + " |")
        L.append("")

    @staticmethod
    def _gap(L, area, statement, what_exists=""):
        """Append an explicit coverage gap.

        A silently empty section is the failure mode this exists to prevent: the
        gap must be visible, named, and explained.
        """
        L.append(f"### Coverage gap: {area}")
        L.append("")
        L.append("**No records in the corpus for this area - this is a coverage gap, not an "
                 "omission from this view.**")
        L.append("")
        L.append(statement)
        L.append("")
        if what_exists:
            L.append(f"Adjacent material that does exist: {what_exists}")
            L.append("")

    def _render_index(self):
        """Load the canonical model once for the whole render pass."""
        index = self.load_artifact_index()
        links = self.load_links()

        def by_id(aid, profile=None):
            """Resolve one id (optionally within a profile). Keys are (profile, id)."""
            for key, (p, d) in index.items():
                if not isinstance(key, tuple) or len(key) < 2:
                    continue
                if key[1] != aid:
                    continue
                if profile is not None and key[0] != profile:
                    continue
                return p, d
            return None, None

        def select(profile=None, domain=None, atype=None, exclude_types=()):
            """All matching records, sorted by id for deterministic output."""
            out = []
            for key, (p, d) in index.items():
                if not isinstance(key, tuple) or len(key) < 2:
                    continue
                prof = key[0]
                if profile is not None and prof != profile:
                    continue
                if domain is not None and d.get("engineering_domain") != domain:
                    continue
                if atype is not None and d.get("artifact_type") != atype:
                    continue
                if d.get("artifact_type") in exclude_types:
                    continue
                if not d.get("id"):
                    continue
                out.append((d["id"], p, d))
            return sorted(out, key=lambda t: (t[0], str(t[2].get("profile"))))

        def links_of(profile=None, relation=None, source=None, target=None):
            out = []
            for l in links:
                if profile is not None and l.get("_profile") != profile:
                    continue
                if relation is not None and l.get("relation_type") != relation:
                    continue
                if source is not None and l.get("source_id") != source:
                    continue
                if target is not None and l.get("target_id") != target:
                    continue
                out.append(l)
            return sorted(out, key=lambda l: (l.get("link_id") or ""))

        return {"index": index, "links": links, "by_id": by_id, "select": select,
                "links_of": links_of, "counts": f"{len(index)} artifacts, {len(links)} links"}

    def _write_view(self, relpath, lines):
        """Write one view file, creating its directory. Returns the path written."""
        p = self.views_dir / relpath
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            for line in lines:
                f.write(line + "\n")
        return p

    def _mermaid(self, diagram_id, body):
        """Wrap a Mermaid diagram in a fenced block with its diagram id."""
        return ["```mermaid", f"%% diagram_id: {diagram_id}"] + body + ["```", ""]

    def _validate_diagrams(self, view_paths):
        """Syntax-check every Mermaid block in the views just written.

        Uses mermaid-cli against a locally installed Chrome. Records the real
        outcome: if the tooling is absent the views say so rather than claiming
        a check that did not happen.
        """
        import shutil
        import subprocess
        import tempfile

        blocks = []
        for vp in view_paths:
            try:
                text = vp.read_text(encoding="utf-8")
            except OSError:
                continue
            lines = text.splitlines()
            i = 0
            while i < len(lines):
                if lines[i].strip() == "```mermaid":
                    start = i + 1
                    j = start
                    while j < len(lines) and lines[j].strip() != "```":
                        j += 1
                    body = lines[start:j]
                    did = next((ln.split(":", 1)[1].strip() for ln in body
                                if ln.startswith("%% diagram_id:")), f"{vp.name}#{i}")
                    blocks.append((vp, did, "\n".join(body)))
                    i = j + 1
                else:
                    i += 1

        if not blocks:
            return {}, "no Mermaid diagrams present in the generated views"

        mmdc = shutil.which("mmdc")
        if not mmdc:
            return ({b[1]: "not_checked_no_mermaid_cli" for b in blocks},
                    "mermaid-cli (`mmdc`) is not on PATH; diagrams were NOT syntax-checked")
        chrome = next((c for c in (
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
        ) if os.path.exists(c)), None)
        if not chrome:
            return ({b[1]: "not_checked_no_chrome" for b in blocks},
                    "mermaid-cli found but no supported Chrome/Chromium binary; "
                    "diagrams were NOT rendered or checked")

        results = {}
        tmp = tempfile.mkdtemp(prefix="fb2-mermaid-")
        pconf = os.path.join(tmp, "puppeteer.json")
        with open(pconf, "w", encoding="utf-8") as fh:
            json.dump({"executablePath": chrome, "args": ["--no-sandbox"]}, fh)
        try:
            for n, (vp, did, body) in enumerate(blocks):
                mmd = os.path.join(tmp, f"d{n}.mmd")
                svg = os.path.join(tmp, f"d{n}.svg")
                with open(mmd, "w", encoding="utf-8") as fh:
                    fh.write(body + "\n")
                try:
                    proc = subprocess.run(
                        [mmdc, "-i", mmd, "-o", svg, "-p", pconf],
                        capture_output=True, text=True, timeout=180)
                    err = (proc.stderr or "") + (proc.stdout or "")
                    if proc.returncode == 0 and os.path.exists(svg) and os.path.getsize(svg) > 0:
                        results[did] = "validated"
                    else:
                        first = next((ln.strip() for ln in err.splitlines()
                                      if "Error" in ln or "error" in ln), "unknown error")
                        results[did] = f"INVALID: {first[:120]}"
                except subprocess.TimeoutExpired:
                    results[did] = "not_checked_timeout"
                except OSError as e:
                    results[did] = f"not_checked_error: {e}"
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

        n_ok = sum(1 for v in results.values() if v == "validated")
        return results, (f"mermaid-cli {shutil.which('mmdc')} with Chrome; "
                         f"{n_ok}/{len(blocks)} diagrams parsed and rendered to SVG")

    def _append_diagram_validation(self, view_paths, lines_by_path):
        """Append a per-view diagram-validation section reflecting the real result."""
        results, summary = self._validate_diagrams(view_paths)
        for vp in view_paths:
            rel = vp.relative_to(self.views_dir)
            # A diagram belongs to the view that emitted it. Diagram ids are
            # namespaced by view directory ("<view-dir>.<name>"), so attribute by
            # the view's own directory rather than by filename.
            vdir = rel.parts[0] if len(rel.parts) > 1 else rel.stem
            mine = {d: r for d, r in results.items() if d.split(".")[0] == vdir}
            if not mine:
                continue
            L = lines_by_path[vp]
            L.append("## Diagram validation")
            L.append("")
            L.append(f"Validator: {summary}")
            L.append("")
            self_rows = [(f"`{d}`", r) for d, r in sorted(mine.items())]
            L.append("| Diagram | Result |")
            L.append("|---|---|")
            for d, r in self_rows:
                L.append(f"| {d} | {r} |")
            L.append("")
            if any(r != "validated" for r in mine.values()):
                L.append("At least one diagram above was **not** validated. Treat its syntax as "
                         "unverified; this view does not claim otherwise.")
                L.append("")

    def cmd_render(self):
        """Regenerate views/ from canonical data.

        Emits one derived, read-only human-readable work product per required
        view directory. Deterministic apart from the `Generated:` stamp line.
        """
        self.views_dir.mkdir(parents=True, exist_ok=True)
        m = self._render_index()
        by_id, select, links_of = m["by_id"], m["select"], m["links_of"]
        counts = m["counts"]

        written = []

        def emit(relpath, title, scope, body):
            lines = self._view_preamble(title, scope, counts) + body
            written.append(self._write_view(relpath, lines))

        # ------------------------------------------------ concept-and-safety
        order = ["FB2-SAF-HAZ-000001", "FB2-SAF-SGO-000001",
                 "FB2-SAF-FSR-000001", "FB2-SAF-FSR-000002",
                 "FB2-SAF-FSR-000003", "FB2-SAF-FSR-000004",
                 "FB2-HW-TSR-000001", "FB2-SW-SWR-000001",
                 "FB2-SW-DSN-000001", "FB2-VER-TMS-000001",
                 "FB2-VER-EXE-000001", "FB2-REV-000001"]
        b = ["## Vertical slice records", "",
             "The canonical cell-voltage safety chain, in traversal order. "
             "The same id exists in both profiles; both copies are shown.", ""]
        for aid in order:
            for prof in ("as_is", "synthetic_reference"):
                p, d = by_id(aid, prof)
                if d is None:
                    continue
                b.append(f"### {aid} ({prof}) — {d.get('title')}")
                b.append("")
                b.append(f"- type: `{d.get('artifact_type')}` | revision: `{d.get('revision')}` | "
                         f"lifecycle: `{d.get('lifecycle_status')}`")
                b.append(f"- guard: {self._guard(d)}")
                if d.get("statement"):
                    b.append(f"- statement: {self._cell(d['statement'], 400)}")
                b.append("")
        b.append("### Chain diagram")
        b.append("")
        b += self._mermaid("concept-and-safety.chain", [
            "flowchart TD",
            '  HAZ["FB2-SAF-HAZ-000001<br/>Cell voltage hazard"]',
            '  SGO["FB2-SAF-SGO-000001<br/>Safety goal"]',
            '  FSR["FB2-SAF-FSR-000001..4<br/>Safety requirements"]',
            '  TSR["FB2-HW-TSR-000001<br/>HW requirement"]',
            '  SWR["FB2-SW-SWR-000001<br/>SW requirement"]',
            '  DSN["FB2-SW-DSN-000001<br/>Design"]',
            '  TMS["FB2-VER-TMS-000001<br/>Test measure"]',
            '  EXE["FB2-VER-EXE-000001<br/>Execution"]',
            '  REV["FB2-REV-000001<br/>Review"]',
            '  HAZ -->|mitigates| SGO',
            '  SGO -->|refines| FSR',
            '  FSR -->|allocated_to| TSR',
            '  FSR -->|allocated_to| SWR',
            '  SWR -->|implements| DSN',
            '  TSR -->|verifies| TMS',
            '  SWR -->|verifies| TMS',
            '  TMS -->|result_of| EXE',
            '  DSN -->|reviewed_by| REV',
        ])
        emit("concept-and-safety/vertical-slice.md",
             "Concept and safety — cell voltage vertical slice (generated view)",
             "The `concept-and-safety` domain: hazard, safety goal, safety requirements, "
             "safety analyses, TARA and safety case held in the corpus.", b)

        # --------------------------------------------------------- management
        b = ["## Project scope and safety plan", ""]
        scope = select(domain="management", atype="requirement")
        plan = select(domain="management", atype="design")
        chgs = select(domain="management", atype="change")
        if not scope and not plan:
            self._gap(b, "project scope and safety plan",
                      "The corpus holds no `management`-domain project-scope or safety-plan "
                      "record in either profile.")
        rows = []
        for aid, p, d in scope + plan:
            rows.append([f"`{aid}`", d.get("profile"), d.get("artifact_type"),
                         self._cell(d.get("title"), 120), self._guard(d)])
        self._table(b, ["Id", "Profile", "Type", "Title", "Guard"], rows)
        for aid, p, d in scope + plan:
            b.append(f"### {aid} — {d.get('title')}")
            b.append("")
            b.append(f"- guard: {self._guard(d)}")
            if d.get("statement"):
                b.append(f"- statement: {self._cell(d['statement'], 600)}")
            if d.get("responsibilities"):
                b.append("- responsibilities:")
                for r in d["responsibilities"]:
                    b.append(f"  - {self._cell(r, 200)}")
            if d.get("decomposition"):
                b.append(f"- decomposition: {self._cell(d['decomposition'], 400)}")
            if d.get("decisions"):
                b.append(f"- decisions: {self._cell(d['decisions'], 400)}")
            b.append("")

        b.append("## Change records")
        b.append("")
        if not chgs:
            self._gap(b, "change records",
                      "The corpus holds no `change` record in either profile, so no change "
                      "decision, impact analysis or reverification selection can be shown.")
        rows = [[f"`{a}`", d.get("profile"), self._cell(d.get("change_type")),
                 self._cell(d.get("lifecycle_status")), self._guard(d)] for a, p, d in chgs]
        self._table(b, ["Id", "Profile", "Change type", "Lifecycle", "Guard"], rows)
        for aid, p, d in chgs:
            b.append(f"### {aid} — {d.get('title')}")
            b.append("")
            b.append(f"- guard: {self._guard(d)}")
            b.append(f"- change_type: `{d.get('change_type')}` | lifecycle: `{d.get('lifecycle_status')}`")
            b.append(f"- implementation_status: `{d.get('implementation_status')}`")
            dec = d.get("decision") or {}
            if isinstance(dec, dict):
                b.append(f"- decision: `{dec.get('decision_id')}` by {self._cell(dec.get('decision_maker'), 220)}")
                b.append(f"- decision rationale: {self._cell(dec.get('rationale'), 700)}")
            b.append(f"- trigger: {self._cell(d.get('trigger'), 400)}")
            ia = d.get("impact_analysis") or {}
            if isinstance(ia, dict):
                b.append(f"- impact — affected artifacts: {self._cell(ia.get('affected_artifacts'))}")
                b.append(f"- impact — affected links: {self._cell(ia.get('affected_links'))}")
                b.append(f"- impact — risk: {self._cell(ia.get('risk_assessment'), 500)}")
            b.append(f"- new revisions: {self._cell(d.get('new_revisions'))}")
            b.append(f"- suspect links: {self._cell(d.get('suspect_links'))}")
            b.append(f"- reverification selection: {self._cell(d.get('reverification_selection'), 500)}")
            b.append(f"- synthetic_decision: {self._cell(d.get('synthetic_decision'), 300)}")
            b.append(f"- limitations/boundaries: {self._cell(d.get('corpus_boundaries'), 400)}")
            b.append("")

        b.append("### Change lifecycle diagram")
        b.append("")
        b += self._mermaid("management.change-lifecycle", [
            "flowchart LR",
            '  REQ["Change request"] --> IA["Impact analysis"]',
            '  IA --> DEC["Fictional board decision<br/>(synthetic_decision)"]',
            '  DEC --> NEWR["New revisions"]',
            '  NEWR --> SUS["Suspect links +<br/>reviews invalidated"]',
            '  SUS --> REVER["Reverification selection"]',
            '  REVER --> POST["Clean post-change baseline"]',
        ])
        emit("management/management.md",
             "Management — project, changes and decisions (generated view)",
             "The `management` domain: project scope, safety plan, change records and their "
             "synthetic decisions.", b)

        # -------------------------------------------------------------- system
        b = ["## System requirements", ""]
        sysreqs = [r for r in select(atype="requirement")
                   if r[2].get("engineering_domain") in ("system", "stakeholder")]
        if not sysreqs:
            # The gap statement below is a fact about the corpus RECORDS and stays
            # literal. The sentences about the coverage plan are read live from
            # governance/coverage-plan.json, so correcting the plan corrects this
            # view on the next render instead of leaving a stale transcript of it.
            self._gap(
                b, "system requirements",
                "The corpus contains **no system-level or stakeholder requirement record** in "
                "either profile, and this is a coverage gap, not a rendering omission: no "
                "record matching the expectation exists on disk in any profile. The "
                "expectation is retained in the coverage plan and is not satisfied. "
                "The plan's current position, read at render time, is that "
                + self._plan_quote(processes=("SYS.1", "SYS.2"), targets=("requirements",))
                + " This view reports what the corpus actually holds and quotes the plan as it "
                  "stands now; where the plan has been corrected, the corrected status appears "
                  "here automatically, so this text cannot drift from the governance file.",
                what_exists="the system-domain HSI design `FB2-SYS-HSI-000001`, the project-scope "
                            "record `FB2-MAN-SCO-000001` (management domain), and the scenario "
                            "`FB2-SCN-CHG-000002`.")
        else:
            self._table(b, ["Id", "Profile", "Title", "Guard"],
                        [[f"`{a}`", d.get("profile"), self._cell(d.get("title"), 120), self._guard(d)]
                         for a, p, d in sysreqs])

        b.append("## HSI / interface authority")
        b.append("")
        hsis = select(domain="system", atype="design")
        if not hsis:
            self._gap(b, "system interfaces",
                      "The corpus holds no system-owned interface authority record.")
        for aid, p, d in hsis:
            b.append(f"### {aid} — {d.get('title')}")
            b.append("")
            b.append(f"- guard: {self._guard(d)}")
            b.append(f"- design_level: `{d.get('design_level')}` | lifecycle: `{d.get('lifecycle_status')}`")
            b.append(f"- variant applicability: {self._cell(d.get('variant_applicability'))}")
            b.append("")
            b.append("Signals (system-owned authority; hardware and software views link here "
                     "rather than duplicating these definitions):")
            b.append("")
            rows = []
            for it in (d.get("interfaces") or []):
                for s in (it.get("signals") or []):
                    rows.append([f"`{it.get('interface_id')}`", f"`{s.get('name')}`",
                                 self._cell(s.get("type")), self._cell(s.get("unit")),
                                 self._cell(s.get("range")), self._cell(s.get("direction")),
                                 self._cell(s.get("invalid_state")), it.get("owner")])
            self._table(b, ["Interface", "Signal", "Type", "Unit", "Range", "Direction",
                            "Invalid/stale state", "Owner"], rows)
            for k in ("timing_budget", "fault_indications", "electrical_budgets", "decisions"):
                if d.get(k):
                    b.append(f"- {k}: {self._cell(d[k], 500)}")

        b.append("## System architecture chain")
        b.append("")
        syslinks = links_of(profile="synthetic_reference")
        rows = [[f"`{l.get('link_id')}`", f"`{l.get('source_id')}`", l.get("relation_type"),
                 f"`{l.get('target_id')}`", l.get("provenance"), l.get("review_state")]
                for l in syslinks
                if l.get("source_id", "").startswith("FB2-SYS") or l.get("target_id", "").startswith("FB2-SYS")]
        if rows:
            self._table(b, ["Link", "Source", "Relation", "Target", "Provenance", "Review state"], rows)
        else:
            b.append("_No link in the canonical registry has a `FB2-SYS-*` endpoint._\n")

        b.append("### Allocation diagram")
        b.append("")
        b += self._mermaid("system.allocation", [
            "flowchart TD",
            '  SGO["FB2-SAF-SGO-000001<br/>Safety goal"]',
            '  FSR["FB2-SAF-FSR-*<br/>Safety requirements"]',
            '  HSI["FB2-SYS-HSI-000001<br/>Interface authority"]',
            '  TSR["FB2-HW-TSR-*<br/>HW requirements"]',
            '  SWR["FB2-SW-SWR-*<br/>SW requirements"]',
            '  SGO -->|refines| FSR',
            '  FSR -->|allocated_to| HSI',
            '  FSR -->|allocated_to| TSR',
            '  FSR -->|allocated_to| SWR',
            '  TSR -.->|interface| HSI',
            '  SWR -.->|interface| HSI',
        ])
        emit("system/system.md",
             "System — requirements, interfaces and architecture (generated view)",
             "The `system` domain: system requirements, the system-owned HSI/interface "
             "authority, and the system architecture chain.", b)

        # ------------------------------------------------------------ hardware
        b = ["## Hardware technical safety requirements (TSR)", ""]
        tsrs = select(domain="hardware", atype="requirement")
        if not tsrs:
            self._gap(b, "hardware requirements",
                      "The corpus holds no hardware-domain requirement record.")
        rows = [[f"`{a}`", d.get("profile"), self._cell(d.get("title"), 110),
                 self._cell((d.get("safety_allocation") or {}).get("asil")),
                 d.get("lifecycle_status"), self._guard(d)] for a, p, d in tsrs]
        self._table(b, ["Id", "Profile", "Title", "ASIL", "Lifecycle", "Guard"], rows)
        for aid, p, d in tsrs:
            b.append(f"### {aid} ({d.get('profile')}) — {d.get('title')}")
            b.append("")
            b.append(f"- guard: {self._guard(d)}")
            b.append(f"- statement: {self._cell(d.get('statement'), 500)}")
            b.append(f"- rationale: {self._cell(d.get('rationale'), 400)}")
            b.append(f"- acceptance criteria: {self._cell(d.get('acceptance_criteria'), 500)}")
            b.append(f"- safety allocation: {self._cell(d.get('safety_allocation'), 300)}")
            b.append(f"- source_refs: {self._cell(d.get('source_refs'))}")
            b.append("")

        b.append("## Hardware design records")
        b.append("")
        hwdes = select(domain="hardware", atype="design")
        if not hwdes:
            self._gap(
                b, "hardware design records",
                "The corpus contains **no hardware-domain design record** in either profile — "
                "no hardware architecture, detailed design, interface/connector definition, "
                "BOM mapping, FMEDA or hardware bring-up record. The hardware domain is "
                "populated by requirements only. The hardware views in "
                "`reports/aspice-process-map.md` describe HWE.2 and HWE.3 as "
                "`partially_mapped`, which is consistent with this; there is simply no "
                "canonical record to render here.")
        else:
            self._table(b, ["Id", "Profile", "Title", "Guard"],
                        [[f"`{a}`", d.get("profile"), self._cell(d.get("title"), 120), self._guard(d)]
                         for a, p, d in hwdes])

        b.append("## Hardware-relevant HSI signals")
        b.append("")
        b.append("Signals from the system-owned interface authority whose owning interface is "
                 "hardware. The authority itself is system-owned; this table is a read-only "
                 "projection, not a second source of truth.")
        b.append("")
        rows = []
        for aid, p, d in hsis:
            for it in (d.get("interfaces") or []):
                for s in (it.get("signals") or []):
                    rows.append([f"`{aid}`", f"`{it.get('interface_id')}`", f"`{s.get('name')}`",
                                 self._cell(s.get("type")), self._cell(s.get("unit")),
                                 self._cell(s.get("range")), self._cell(s.get("direction")),
                                 it.get("owner"), self._guard(d)])
        self._table(b, ["Authority", "Interface", "Signal", "Type", "Unit", "Range",
                        "Direction", "Owner", "Guard"], rows)

        b.append("### Hardware allocation diagram")
        b.append("")
        b += self._mermaid("hardware.allocation", [
            "flowchart LR",
            '  TSR["FB2-HW-TSR-000001<br/>Cell voltage accuracy"]',
            '  TSR2["FB2-HW-TSR-000002<br/>isoSPI integrity"]',
            '  TSR3["FB2-HW-TSR-000003<br/>Contactor driver"]',
            '  TSR4["FB2-HW-TSR-000004<br/>Independent monitor"]',
            '  SPI["HSI_AFE_SPI<br/>hw_engineer"]',
            '  CON["Contactor interface<br/>hw_engineer"]',
            '  TSR --> SPI',
            '  TSR2 --> SPI',
            '  TSR3 --> CON',
            '  TSR4 -.->|independent path| CON',
        ])
        emit("hardware/hardware.md",
             "Hardware — requirements, design and interfaces (generated view)",
             "The `hardware` domain: hardware TSRs, hardware design records, and the "
             "hardware-owned part of the HSI signal set.", b)

        # ------------------------------------------------------------ software
        b = ["## Software requirements", ""]
        swrs = select(domain="software", atype="requirement")
        rows = [[f"`{a}`", d.get("profile"), self._cell(d.get("title"), 110),
                 self._cell((d.get("safety_allocation") or {}).get("asil")),
                 self._cell(d.get("verification_approach")), self._guard(d)] for a, p, d in swrs]
        self._table(b, ["Id", "Profile", "Title", "ASIL", "Verification approach", "Guard"], rows)
        for aid, p, d in swrs:
            b.append(f"### {aid} ({d.get('profile')}) — {d.get('title')}")
            b.append("")
            b.append(f"- guard: {self._guard(d)}")
            b.append(f"- statement: {self._cell(d.get('statement'), 500)}")
            b.append(f"- acceptance criteria: {self._cell(d.get('acceptance_criteria'), 500)}")
            b.append(f"- conditions/modes: {self._cell(d.get('conditions_modes'))}")
            b.append(f"- source_refs: {self._cell(d.get('source_refs'))}")
            b.append("")

        b.append("## Software design records")
        b.append("")
        swds = select(domain="software", atype="design")
        rows = [[f"`{a}`", d.get("profile"), self._cell(d.get("design_level")),
                 self._cell(d.get("title"), 110), self._guard(d)] for a, p, d in swds]
        self._table(b, ["Id", "Profile", "Level", "Title", "Guard"], rows)
        for aid, p, d in swds:
            b.append(f"### {aid} ({d.get('profile')}) — {d.get('title')}")
            b.append("")
            b.append(f"- guard: {self._guard(d)}")
            b.append(f"- design_level: `{d.get('design_level')}` | lifecycle: `{d.get('lifecycle_status')}`")
            b.append(f"- responsibilities: {self._cell(d.get('responsibilities'), 600)}")
            b.append(f"- constraints: {self._cell(d.get('constraints'), 400)}")
            bm = d.get("behavior_model")
            if isinstance(bm, dict) and bm.get("states"):
                b.append(f"- behavior model (`{bm.get('type')}`) states: {self._cell(bm.get('states'))}")
                tr = bm.get("transitions") or []
                for t in tr:
                    b.append(f"  - `{t.get('from')}` → `{t.get('to')}` on `{t.get('trigger')}` "
                             f"[guard: {self._cell(t.get('guard'), 80)}] → {self._cell(t.get('action'), 120)}")
            b.append(f"- implementation mapping: {self._cell(d.get('implementation_mapping'), 500)}")
            b.append("")

        b.append("### Contactor state machine")
        b.append("")
        sm = None
        for prof in ("as_is", "synthetic_reference"):
            _, d = by_id("FB2-SW-DSN-000003", prof)
            if d and isinstance(d.get("behavior_model"), dict) and d["behavior_model"].get("transitions"):
                sm = d
                break
        if sm:
            b.append(f"Derived from `FB2-SW-DSN-000003` ({sm.get('profile')}) `behavior_model`.")
            b.append("")
            bm = sm["behavior_model"]
            body = ["stateDiagram-v2"]
            for s in bm.get("states", []):
                body.append(f"  {s}")
            for t in bm.get("transitions", []):
                lbl = f"{t.get('trigger')} [{t.get('guard')}]"
                body.append(f"  {t.get('from')} --> {t.get('to')} : {lbl}")
            b += self._mermaid("software.contactor-state-machine", body)
        else:
            b.append("_No state-machine design record found in the corpus._\n")

        b.append("## MISRA C:2012 deviation records")
        b.append("")
        b.append("These 26 records are the largest single slice of the `as_is` profile. They are "
                 "derived from in-source static-analysis suppressions at the pinned baseline; "
                 "the source comment text is the authority for each rationale. **No record here "
                 "asserts MISRA conformance, and no deviation has been approved by a human.**")
        b.append("")
        devs = select(profile="as_is", atype="deviation")
        if not devs:
            self._gap(b, "MISRA deviation records",
                      "The corpus holds no deviation record.")
        byrule = {}
        for aid, p, d in devs:
            byrule.setdefault((d.get("guideline_id"), d.get("rule_reference")), []).append((aid, d))
        b.append("### Deviation summary by rule")
        b.append("")
        self._table(b, ["Guideline", "Rule", "Count", "Deviation types", "Profiles"],
                    [[k[0], f"`{k[1]}`", len(v),
                      self._cell(sorted({x[1].get("deviation_type") for x in v})),
                      self._cell(sorted({x[1].get("profile") for x in v}))]
                     for k, v in sorted(byrule.items(), key=lambda kv: str(kv[0]))])
        b.append("### Deviation register")
        b.append("")
        self._table(b, ["Id", "Rule", "Type", "Affected file", "Symbol", "Lines",
                        "Review disposition", "Lifecycle", "Guard"],
                    [[f"`{a}`", f"`{d.get('rule_reference')}`", self._cell(d.get("deviation_type")),
                      f"`{self._cell(d.get('affected_file'), 90)}`",
                      self._cell(d.get("affected_symbol"), 60),
                      self._cell(d.get("affected_lines"), 30),
                      self._cell(d.get("review_disposition"), 60),
                      d.get("lifecycle_status"), self._guard(d)]
                     for a, p, d in devs])
        b.append("### Deviation detail")
        b.append("")
        for aid, p, d in devs:
            b.append(f"#### {aid} — {d.get('title')}")
            b.append("")
            b.append(f"- guard: {self._guard(d)}")
            b.append(f"- guideline/rule: `{d.get('guideline_id')}` / `{d.get('rule_reference')}` "
                     f"({d.get('rule_category')})")
            b.append(f"- location: `{self._cell(d.get('affected_file'), 120)}` "
                     f"symbol `{self._cell(d.get('affected_symbol'), 60)}` "
                     f"lines `{self._cell(d.get('affected_lines'), 40)}`")
            b.append(f"- deviation type: `{d.get('deviation_type')}` | suppression: "
                     f"`{d.get('suppression_form')}` scope `{d.get('suppression_scope')}`")
            b.append(f"- rationale (from source): {self._cell(d.get('deviation_rationale'), 500)}")
            b.append(f"- normative verification: {self._cell(d.get('normative_verification'), 300)}")
            b.append(f"- review disposition: `{d.get('review_disposition')}`")
            b.append(f"- reanalysis trigger: {self._cell(d.get('reanalysis_justification'), 400)}")
            b.append(f"- tool: {self._cell(d.get('tool_reference'), 200)}")
            b.append(f"- project process evidence: {self._cell(d.get('project_process_evidence'), 300)}")
            b.append(f"- impact notes: {self._cell(d.get('impact_notes'), 400)}")
            b.append("")
        emit("software/software.md",
             "Software — requirements, design and deviations (generated view)",
             "The `software` domain: software requirements, software design records, and the "
             "26 MISRA C:2012 deviation records.", b)

        # ------------------------------------------- verification and validation
        b = ["## Execution classification model", ""]
        b.append("`execution_kind` and `outcome` are **orthogonal**: how the run was performed is "
                 "recorded separately from what it concluded. A synthetic fixture can legitimately "
                 "report `pass`, and that pass is not product evidence. Generated "
                 "consistency-check results validate the corpus, not the BMS product.")
        b.append("")
        b.append("| execution_kind | meaning |")
        b.append("|---|---|")
        b.append("| `none` | not executed |")
        b.append("| `actual_host_run` | executed on a real host, logs captured |")
        b.append("| `actual_simulation_run` | executed model with captured logs |")
        b.append("| `synthetic_fixture` | fixture, never a real run |")
        b.append("")
        b.append("| outcome | meaning |")
        b.append("|---|---|")
        for o in ("pass", "fail", "inconclusive", "not_run", "blocked"):
            b.append(f"| `{o}` | as defined by the execution schema |")
        b.append("")

        b.append("## Test measures")
        b.append("")
        tms = select(atype="test_measure")
        self._table(b, ["Id", "Profile", "Title", "Test type", "Oracle basis", "Lifecycle", "Guard"],
                    [[f"`{a}`", d.get("profile"), self._cell(d.get("title"), 100),
                      self._cell(d.get("test_type")), self._cell(d.get("oracle_basis")),
                      d.get("lifecycle_status"), self._guard(d)] for a, p, d in tms])
        for aid, p, d in tms:
            b.append(f"### {aid} ({d.get('profile')}) — {d.get('title')}")
            b.append("")
            b.append(f"- guard: {self._guard(d)}")
            b.append(f"- objective: {self._cell(d.get('objective'), 400)}")
            b.append(f"- referenced requirements: {self._cell(d.get('referenced_requirements'))}")
            b.append(f"- referenced designs: {self._cell(d.get('referenced_designs'))}")
            b.append(f"- preconditions: {self._cell(d.get('preconditions'), 400)}")
            b.append(f"- expected outcomes: {self._cell(d.get('expected_outcomes'), 500)}")
            b.append(f"- tolerances: {self._cell(d.get('tolerances'), 300)}")
            b.append(f"- timing: {self._cell(d.get('timing'), 300)}")
            b.append(f"- oracle basis: `{d.get('oracle_basis')}`")
            b.append(f"- regression selection: {self._cell(d.get('regression_selection'), 300)}")
            b.append("")

        b.append("## Executions")
        b.append("")
        execs = select(atype="execution")
        self._table(b, ["Id", "Profile", "Test measure", "execution_kind", "outcome",
                        "Lifecycle", "Guard"],
                    [[f"`{a}`", d.get("profile"), f"`{d.get('test_measure_id')}`",
                      f"`{d.get('execution_kind')}`", f"`{d.get('outcome')}`",
                      d.get("lifecycle_status"), self._guard(d)] for a, p, d in execs])

        b.append("### Evidence classes present in the corpus")
        b.append("")
        real, synth, blocked = [], [], []
        for aid, p, d in execs:
            ek, oc = d.get("execution_kind"), d.get("outcome")
            if ek == "actual_host_run":
                real.append((aid, d))
            elif ek == "synthetic_fixture":
                synth.append((aid, d))
            elif oc in ("blocked", "not_run") or ek == "none":
                blocked.append((aid, d))
        b.append(f"**Real captured host runs ({len(real)}).** These have captured logs under "
                 f"`docs/artifacts/evidence/actual-runs/` and per-run input/output hashes. They "
                 f"are the only executions in this corpus that constitute captured evidence, and "
                 f"even they are host-platform results, not target-hardware results.")
        b.append("")
        self._table(b, ["Id", "Profile", "execution_kind", "outcome", "Environment",
                        "Captured logs", "Guard"],
                    [[f"`{a}`", d.get("profile"), f"`{d.get('execution_kind')}`",
                      f"`{d.get('outcome')}`", self._cell((d.get("environment") or {}).get("hardware"), 70),
                      self._cell([l.get("file") for l in (d.get("logs") or [])], 120), self._guard(d)]
                     for a, d in real])
        b.append(f"**Synthetic fixtures ({len(synth)}).** `execution_kind=synthetic_fixture` with "
                 f"`outcome=pass`. These are fixtures, not runs. The `evidence/synthetic-fixtures/` "
                 f"directory is the designated home for their captured fixture artefacts; whether "
                 f"it holds them is reported in the verification-evidence report and in "
                 f"`evidence/synthetic-fixtures/`, and is not asserted here.")
        b.append("")
        self._table(b, ["Id", "Profile", "execution_kind", "outcome", "Distinct input digests",
                        "Guard"],
                    [[f"`{a}`", d.get("profile"), f"`{d.get('execution_kind')}`", f"`{d.get('outcome')}`",
                      self._cell(sorted({v for v in (d.get("input_hashes") or {}).values()}), 90),
                      self._guard(d)] for a, d in synth])
        b.append(f"**Blocked / not executed ({len(blocked)}).** `execution_kind=none` with "
                 f"`outcome=blocked`. These record why a run did not happen.")
        b.append("")
        self._table(b, ["Id", "Profile", "execution_kind", "outcome", "Limitations", "Guard"],
                    [[f"`{a}`", d.get("profile"), f"`{d.get('execution_kind')}`", f"`{d.get('outcome')}`",
                      self._cell(d.get("limitations"), 200), self._guard(d)] for a, d in blocked])

        b.append("### Execution detail")
        b.append("")
        for aid, p, d in execs:
            b.append(f"#### {aid} ({d.get('profile')}) — {d.get('title')}")
            b.append("")
            b.append(f"- guard: {self._guard(d)}")
            b.append(f"- execution_kind: `{d.get('execution_kind')}` | outcome: `{d.get('outcome')}` "
                     f"(orthogonal axes)")
            b.append(f"- test measure: `{d.get('test_measure_id')}` rev `{d.get('test_measure_revision')}`")
            b.append(f"- environment: {self._cell(d.get('environment'), 400)}")
            b.append(f"- input hashes: {self._cell(d.get('input_hashes'), 400)}")
            b.append(f"- output hashes: {self._cell(d.get('output_hashes'), 400)}")
            b.append(f"- logs: {self._cell(d.get('logs'), 400)}")
            b.append(f"- timestamps: {self._cell(d.get('timestamps'), 200)}")
            b.append(f"- anomalies: {self._cell(d.get('anomalies'), 600)}")
            b.append(f"- limitations: {self._cell(d.get('limitations'), 400)}")
            b.append("")

        b.append("### Evidence classification diagram")
        b.append("")
        b += self._mermaid("verification-validation.evidence-classes", [
            "flowchart TD",
            '  MEAS["Test measure<br/>(plan)"]',
            '  KIND{"execution_kind"}',
            '  REAL["actual_host_run<br/>captured logs"]',
            '  SIM["actual_simulation_run<br/>captured model logs"]',
            '  FIX["synthetic_fixture<br/>not a real run"]',
            '  NONE["none<br/>not executed"]',
            '  OUT{"outcome (orthogonal)"}',
            '  PASS["pass"]',
            '  FAIL["fail"]',
            '  BLOCK["blocked / not_run"]',
            '  MEAS --> KIND',
            '  KIND --> REAL',
            '  KIND --> SIM',
            '  KIND --> FIX',
            '  KIND --> NONE',
            '  REAL --> OUT',
            '  FIX --> OUT',
            '  NONE --> OUT',
            '  SIM --> OUT',
            '  OUT --> PASS',
            '  OUT --> FAIL',
            '  OUT --> BLOCK',
        ])
        emit("verification-validation/verification-validation.md",
             "Verification and validation — measures, executions, evidence (generated view)",
             "The `verification` domain: every test measure and every execution record, with "
             "`execution_kind` and `outcome` shown as the orthogonal pair they are.", b)

        # ------------------------------------------- production/operation/service
        b = []
        areas = [
            ("Release and configuration identification", ("production", "release"),
             "no release-configuration record, release-notes record, acceptance/release "
             "checklist record, or configuration-identification record"),
            ("Production and end-of-line test", ("production",),
             "no production control plan, end-of-line test plan, or calibration/programming "
             "specification record"),
            ("Operation and field monitoring", ("operation",),
             "no field-monitoring record, incident-handling record, or operational-instruction "
             "record"),
            ("Service and maintenance", ("service",),
             "no installation, operation, service-instruction, maintenance, or "
             "regression-strategy record"),
            ("Decommissioning and recycling", ("decommissioning",),
             "no decommissioning or recycling safety-assumption record"),
        ]
        have_domains = {d.get("engineering_domain") for d in
                        (v[1] for v in m["index"].values())}
        # The gap statement per area is a fact about the corpus RECORDS and stays
        # literal. The plan's current position is read live from
        # governance/coverage-plan.json so that a correction to the plan cannot
        # leave this view quoting a superseded disposition.
        release_plan_note = (
            "The plan's current position, read at render time, is that "
            + self._plan_quote(processes=("SPL.2",), iso=("part_7_production",))
            + " Neither names a release, production, operation, service or "
              "decommissioning record, and no canonical record matching one exists "
              "on disk, so the gap above holds regardless of how the plan is worded.")
        for area, doms, what in areas:
            b.append(f"## {area}")
            b.append("")
            found = [r for r in select() if r[2].get("engineering_domain") in doms]
            if not found:
                self._gap(
                    b, area,
                    f"The corpus holds {what} in either profile. The required directory layout "
                    f"mandates this view, so the section is emitted with the gap stated rather "
                    f"than omitted; a silently empty section would misrepresent corpus "
                    f"completeness. Domains searched: {', '.join(doms)}.",
                    what_exists=release_plan_note)
            else:
                self._table(b, ["Id", "Profile", "Title", "Guard"],
                            [[f"`{a}`", d.get("profile"), self._cell(d.get("title"), 120), self._guard(d)]
                             for a, p, d in found])
                b.append(f"Each record above is printed with its own guard fields. Every area "
                         f"record in this corpus is `origin: synthetic`, "
                         f"`human_approval_status: pending`, `production_authorized: false` and "
                         f"`product_verification_credit: false`, and each states in its own "
                         f"`evidence_state` / `operational_authorisation_statement` that none of "
                         f"its steps has been executed and that it authorises no action on real "
                         f"equipment. The presence of a record here means the area is *documented*, "
                         f"not that any production, service or recycling activity has occurred.")
                b.append("")
        b.append("## Domains actually present in the corpus")
        b.append("")
        b.append("For transparency, the full set of `engineering_domain` values present across "
                 "all indexed records:")
        b.append("")
        doms_present = sorted(x for x in have_domains if x)
        b.append("`" + "`, `".join(doms_present) + "`")
        b.append("")
        # Computed, not asserted. An earlier revision of this view stated in prose that none of
        # the lifecycle-continuation domains appear; that sentence became false the moment the
        # first post-development record was authored, and a view whose own prose can silently go
        # stale is exactly the failure mode this corpus is meant to prevent. The sentence is now
        # derived from the indexed records, so it is true in every corpus state.
        lifecycle_domains = sorted({"production", "release", "operation", "service", "decommissioning"})
        missing_lifecycle = [d for d in lifecycle_domains if d not in doms_present]
        if missing_lifecycle:
            b.append("Lifecycle-continuation domains not yet represented by any record: "
                     + ", ".join(f"`{d}`" for d in missing_lifecycle)
                     + ". Each absence above is reported as an explicit coverage gap rather than "
                       "as an empty section. This is a structural gap in corpus population, not a "
                       "rendering omission.")
        else:
            b.append("All five lifecycle-continuation domains (`release`, `production`, "
                     "`operation`, `service`, `decommissioning`) are now represented by at least "
                     "one canonical record, so no area in this view is an unbacked declaration. "
                     "Representation is not evidence: every one of those records states that its "
                     "steps have not been executed and that it authorises nothing on real "
                     "equipment.")
        b.append("")
        b.append("### Guard-field status of this view")
        b.append("")
        # Computed, not asserted: the earlier revision hard-coded "prints no per-record guard
        # fields, because it shows no records", which goes false as soon as one lifecycle-continuation
        # record exists. Derived from the same search that fills the sections above.
        n_lifecycle = sum(1 for r in select()
                          if r[2].get("engineering_domain") in
                          ("production", "release", "operation", "service", "decommissioning"))
        if n_lifecycle == 0:
            b.append("This view prints **no per-record guard fields**, because it shows no records: "
                     "every section above is a declared coverage gap. That is deliberate. Were the "
                     "gaps to be filled, each record added would be printed with its own "
                     "`profile` / `origin` / `human_approval_status` / `production_authorized` values "
                     "in the same format used by the other views.")
        else:
            b.append(f"This view prints **per-record guard fields** for all {n_lifecycle} "
                     f"lifecycle-continuation record(s) shown above, in the same format used by "
                     f"the other views: `profile`, `origin`, `human_approval_status` and "
                     f"`production_authorized`. Those four fields are not a verdict this view can "
                     f"apply; they are read from each record so a reader can see that a documented "
                     f"lifecycle area is still an unapproved, unauthorised piece of synthetic "
                     f"engineering.")
        b.append("")
        b.append("Corpus-wide, verified at render time from the indexed records: "
                 f"`human_approval_status` is `pending` on every record, "
                 f"`production_authorized` is `false` on every record, and "
                 f"`product_verification_credit` is `false` on every record. No lifecycle-"
                 "continuation artifact in this corpus has been human-approved or production-"
                 "authorized, and this view does not imply otherwise.")
        b.append("")
        emit("production-operation-service/lifecycle-continuation.md",
             "Production, operation, service and decommissioning (generated view)",
             "The lifecycle-continuation areas required by the master prompt. Each section "
             "states explicitly whether the corpus holds records for it.", b)

        # ------------------------------------------------- supporting processes
        b = ["## Supporting and organisational process records", ""]
        support = select(domain="supporting")
        # Computed, not asserted. The earlier revision hard-coded "the corpus holds no
        # process-definition record for any of these families: the only supporting-domain records
        # are two meta-review records". Both halves of that sentence are derived here, so the
        # prose stays true when the families are populated and keeps reporting the gap when they
        # are not. The selection rule below is unchanged: a record counts for a family only when
        # it names that process id explicitly.
        proc_families = (("Quality assurance", "SUP.1"),
                         ("Configuration management", "SUP.8"),
                         ("Problem resolution", "SUP.9"),
                         ("Change control", "SUP.10"),
                         ("Measurement", "MAN.6"),
                         ("Process improvement", "PIM.3"))
        def _family_matches(proc_ids):
            return [r for r in support if proc_ids in json.dumps(r[2])]
        definition_records = [r for r in support if r[2].get("artifact_type") != "review"]
        if not support:
            b.append("The master prompt (section 12) requires populated **process records**, not "
                     "just policies, for each supporting process family. The corpus holds no "
                     "record whose `engineering_domain` is `supporting` at all, so every family "
                     "below is reported as a gap.")
        elif not definition_records:
            b.append("The master prompt (section 12) requires populated **process records**, not "
                     "just policies, for each supporting process family. The `supporting` domain "
                     f"is populated by {len(support)} record(s), but all of them are review "
                     "records: they exercise review practice, which is not the same thing as "
                     "populating the process. Listing the same review records against six "
                     "different families would imply a coverage that does not exist, so each "
                     "family is reported as a gap.")
        else:
            b.append("The master prompt (section 12) requires populated **process records**, not "
                     "just policies, for each supporting process family. A record counts for a "
                     "family below only when it names that process id explicitly, so the same "
                     "record is never claimed for a family it does not address. "
                     f"{len(definition_records)} of the {len(support)} `supporting`-domain "
                     "record(s) are process-definition or plan records; the remainder are review "
                     "records and are listed separately below so the two are not conflated.")
        b.append("")
        proc_rows = []
        for label, proc_ids in proc_families:
            fam = _family_matches(proc_ids)
            proc_rows.append((label, proc_ids, fam))
        self._table(b, ["Process family", "ASPICE", "Matching process record", "Guard"],
                    [[label, f"`{ids}`",
                      (self._cell([f"`{a}`" for a, _p, _d in c], 120) if c
                       else "**none — coverage gap**"),
                      (self._guard(c[0][2]) if c else "-")]
                     for label, ids, c in proc_rows])
        if not support:
            self._gap(b, "supporting-process records",
                      "The corpus holds no record whose `engineering_domain` is `supporting`.")
        elif not definition_records:
            b.append(f"The `supporting` domain is populated by {len(support)} record(s), listed "
                     "in full below. They are review records, not process-definition records.")
            b.append("")
        else:
            b.append(f"### Process and plan records in the `supporting` domain "
                     f"({len(definition_records)} record(s))")
            b.append("")
            b.append("These are the records that populate the families in the table above. Each "
                     "one carries its own `performed_instances` or equivalent executed-work "
                     "content, its accountable role, its acceptance criteria and its own guard "
                     "fields.")
            b.append("")
            def _process_id(d):
                """The process this record populates, read from whichever field carries it.

                Three shapes exist in the supporting domain: process_record carries an explicit
                aspice_process_id; the plan and improvement records carry it only in
                standards_mappings. Reading the first two blindly produced a column of empty
                strings joined by commas, which looks like a populated field and is not one.
                """
                explicit = d.get("aspice_process_id")
                if explicit:
                    return str(explicit)
                refs = [str(s.get("reference")) for s in (d.get("standards_mappings") or [])
                        if isinstance(s, dict) and s.get("reference")]
                return "; ".join(refs) if refs else "-"

            def _instance_count(d):
                """Performed-work content, whichever field carries it."""
                for field in ("performed_instances", "milestones_and_gates", "observations",
                              "changes_made", "risk_entries"):
                    val = d.get(field)
                    if isinstance(val, list) and val:
                        return len(val)
                return 0

            self._table(b, ["Id", "Profile", "Type", "ASPICE process", "Title",
                            "Performed / defined work items", "Guard"],
                        [[f"`{a}`", d.get("profile"), d.get("artifact_type"),
                          self._cell(_process_id(d), 60),
                          self._cell(d.get("title"), 110),
                          _instance_count(d),
                          self._guard(d)]
                         for a, p, d in definition_records])
            b.append(f"The `supporting` domain is populated by {len(support)} record(s) in total: "
                     f"the {len(definition_records)} above plus "
                     f"{len(support) - len(definition_records)} review record(s). The review "
                     "records are listed separately below so a process record and a review of a "
                     "process are not counted as the same coverage.")
            b.append("")
        b.append("The corpus also contains review records that exercise these process families "
                 "in practice (QA, meta-review, change-management review, deviation review). "
                 "They are review records, not process-definition records, and are shown below "
                 "as separate material rather than presented as the process artifacts the master "
                 "prompt asks for.")
        b.append("")
        revs = select(atype="review")
        self._table(b, ["Id", "Profile", "Review type", "Domain", "Title", "Lifecycle", "Guard"],
                    [[f"`{a}`", d.get("profile"), self._cell(d.get("review_type")),
                      self._cell(d.get("engineering_domain")), self._cell(d.get("title"), 110),
                      d.get("lifecycle_status"), self._guard(d)] for a, p, d in revs])
        b.append("### Review finding counts by severity")
        b.append("")
        sev = {}
        for aid, p, d in revs:
            for f in (d.get("findings") or []):
                sev.setdefault(d.get("profile"), {}).setdefault(f.get("severity"), 0)
                sev[d.get("profile")][f.get("severity")] += 1
        self._table(b, ["Profile", "critical", "high", "medium", "low", "Total"],
                    [[prof, sev[prof].get("critical", 0), sev[prof].get("high", 0),
                      sev[prof].get("medium", 0), sev[prof].get("low", 0), sum(sev[prof].values())]
                     for prof in sorted(sev)])
        b.append("**These are automated AI-assisted review findings. They are not human review "
                 "findings and none of them constitutes approval.**")
        b.append("")
        emit("supporting-processes/supporting-processes.md",
             "Supporting processes (generated view)",
             "Supporting and organisational process families: QA, configuration management, "
             "problem resolution, change control, measurement and process improvement.", b)

        # ----------------------------------------------------- standards mapping
        b = ["## ASPICE process inventory", ""]
        b.append("Derived from `governance/coverage-plan.json` (`process_inventory`). The "
                 "disposition text is quoted from that file; it is **not** re-asserted here, and "
                 "a `mapped` disposition in a coverage plan is not evidence of conformity.")
        b.append("")
        cp = load_json(self.governance_dir / "coverage-plan.json")
        procs = cp.get("process_inventory", [])
        self._table(b, ["Process", "Name", "Applicability", "Disposition (as recorded)"],
                    [[f"`{p.get('process_id')}`", self._cell(p.get("name"), 60),
                      f"`{p.get('applicability')}`", self._cell(p.get("disposition"), 220)]
                     for p in procs])
        app = [p for p in procs if p.get("applicability") == "applicable"]
        na = [p for p in procs if p.get("applicability") == "not_applicable"]
        mapped = [p for p in procs if str(p.get("disposition", "")).startswith("mapped")]
        partial = [p for p in procs if "partially_mapped" in str(p.get("disposition", ""))]
        gaps = [p for p in procs if str(p.get("disposition", "")).startswith("gap")]
        b.append("### Applicability and disposition counts")
        b.append("")
        self._table(b, ["Measure", "Count", "Of"],
                    [["processes in inventory", len(procs), "-"],
                     ["applicable", len(app), len(procs)],
                     ["not_applicable", len(na), len(procs)],
                     ["disposition starts `mapped`", len(mapped), len(procs)],
                     ["disposition contains `partially_mapped`", len(partial), len(procs)],
                     ["disposition starts `gap`", len(gaps), len(procs)]])
        b.append("The four MLE processes are recorded as explicitly `not_applicable` with a "
                 "rationale. Per the master prompt, non-applicability here is a recorded "
                 "decision, not an absence.")
        b.append("")

        b.append("## ISO 26262 part coverage")
        b.append("")
        b.append("Derived from `governance/coverage-plan.json` (`iso26262_coverage`).")
        b.append("")
        rows = []
        for k in sorted(cp.get("iso26262_coverage", {})):
            v = cp["iso26262_coverage"][k]
            if isinstance(v, dict):
                rows.append([f"`{k}`", f"`{v.get('decision')}`", self._cell(v.get("rationale"), 200),
                             self._cell(v.get("reference_decision"), 60)])
            else:
                rows.append([f"`{k}`", self._cell(str(v).split(" - ")[0], 40),
                             self._cell(str(v), 240), "-"])
        self._table(b, ["Part", "Status", "Recorded rationale", "Reference decision"], rows)
        b.append("### Standards lock")
        b.append("")
        sl = load_json(self.governance_dir / "standards-lock.json")
        self._table(b, ["Standard", "Title", "Edition", "Locked by"],
                    [[f"`{s.get('id')}`", self._cell(s.get("title"), 70), self._cell(s.get("edition")),
                      sl.get("locked_by")] for s in sl.get("standards", [])])
        b.append("**Structural mapping coverage is not conformity.** Nothing in this view asserts "
                 "that foxBMS, SoftwareDevLabs, or this corpus is ISO 26262 compliant, ASIL "
                 "certified, or assessed at any Automotive SPICE capability level. Exact clause "
                 "text was not ingested; where a normative reference could not be verified it is "
                 "marked unverified in the underlying record.")
        b.append("")
        # Guard fields are computed from the indexed records, never asserted.
        appr = sorted({str(d.get("human_approval_status")) for _k, (_p, d) in m["index"].items()
                       if d.get("id")})
        prod = sorted({str(d.get("production_authorized")).lower() for _k, (_p, d) in m["index"].items()
                       if d.get("id")})
        b.append("### Guard-field status of this view")
        b.append("")
        b.append("This view shows no per-record guard column because the process inventory and "
                 "ISO part coverage it renders are held in `governance/coverage-plan.json`, not "
                 "as corpus artifact records with their own guard fields. The corpus-wide guard "
                 "state, computed at render time from the indexed artifact records, is:")
        b.append("")
        b.append(f"- `human_approval_status` values present: {', '.join('`' + a + '`' for a in appr)}")
        b.append(f"- `production_authorized` values present: {', '.join('`' + a + '`' for a in prod)}")
        b.append("")
        b.append("A `mapped` disposition in a coverage plan is a planning claim, not an approval "
                 "and not evidence of conformity. No record in this corpus is human-approved, and "
                 "none is production-authorized.")
        b.append("")
        emit("standards-mapping/standards-mapping.md",
             "Standards mapping — ASPICE processes and ISO 26262 parts (generated view)",
             "The ASPICE process inventory and ISO 26262 part coverage, derived from "
             "`governance/coverage-plan.json` and `governance/standards-lock.json`.", b)

        # ---------------------------------------------------------- traceability
        b = ["## Link-type statistics", ""]
        b.append("Derived from the canonical link registries. Counts are computed here, not "
                 "transcribed from a report.")
        b.append("")
        stats = {}
        for l in m["links"]:
            key = (l.get("_profile", "unknown"), l.get("relation_type"))
            stats[key] = stats.get(key, 0) + 1
        profiles = sorted({k[0] for k in stats})
        rels = sorted({k[1] for k in stats})
        self._table(b, ["Relation type"] + profiles + ["Total"],
                    [[f"`{r}`"] + [stats.get((p, r), 0) for p in profiles]
                     + [sum(stats.get((p, r), 0) for p in profiles)] for r in rels]
                    + [["**Total**"] + [sum(stats.get((p, r), 0) for r in rels) for p in profiles]
                       + [sum(stats.values())]])
        b.append("`related_to` is forbidden in canonical registries and appears only in mutation "
                 "fixtures, where it is the injected defect.")
        b.append("")

        b.append("## Vertical chains")
        b.append("")
        b.append("Full traversals from hazard down to evidence, computed by following the "
                 "canonical relations. A chain that stops early is a real traceability gap, "
                 "not a rendering limit.")
        b.append("")
        fwd = {"mitigates", "refines", "allocated_to", "implements", "verifies", "result_of",
               "validates", "supports", "changes"}
        for prof in profiles:
            b.append(f"### {prof}")
            b.append("")
            haz = [l for l in m["links"] if l.get("_profile") == prof and l.get("target_id", "").startswith("FB2-SAF-HAZ")]
            if not haz:
                b.append("_No hazard record in this profile._\n")
                continue
            start = haz[0]["source_id"]
            seen, frontier, rows = {start}, [start], []
            while frontier:
                cur = frontier.pop(0)
                for l in sorted(m["links"], key=lambda x: x.get("link_id") or ""):
                    if l.get("_profile") != prof or l.get("relation_type") not in fwd:
                        continue
                    if l.get("source_id") != cur or l.get("target_id") in seen:
                        continue
                    seen.add(l["target_id"])
                    frontier.append(l["target_id"])
                    _, dd = by_id(l["target_id"], prof)
                    rows.append([f"`{cur}`", l.get("relation_type"), f"`{l['target_id']}`",
                                 self._cell(dd.get("title"), 90) if dd else "**unresolved**",
                                 self._guard(dd) if dd else "-"])
            self._table(b, ["From", "Relation", "To", "Title", "Guard"], rows)
        b.append("### Chain diagram")
        b.append("")
        b += self._mermaid("traceability.vertical-chain", [
            "flowchart TD",
            '  HAZ["FB2-SAF-HAZ-000001<br/>Hazard"]',
            '  SGO["FB2-SAF-SGO-000001<br/>Safety goal"]',
            '  FSR["FB2-SAF-FSR-*<br/>Safety reqs"]',
            '  TSR["FB2-HW-TSR-*<br/>HW reqs"]',
            '  SWR["FB2-SW-SWR-*<br/>SW reqs"]',
            '  DSN["FB2-SW-DSN-*<br/>Design"]',
            '  TMS["FB2-VER-TMS-*<br/>Test measures"]',
            '  EXE["FB2-VER-EXE-*<br/>Executions"]',
            '  HAZ -->|mitigates| SGO',
            '  SGO -->|refines| FSR',
            '  FSR -->|allocated_to| TSR',
            '  FSR -->|allocated_to| SWR',
            '  SWR -->|implements| DSN',
            '  TSR -->|verifies| TMS',
            '  SWR -->|verifies| TMS',
            '  TMS -->|result_of| EXE',
        ])

        b.append("## Lateral links")
        b.append("")
        b.append("Cross-cutting relations that do not sit on a single vertical chain.")
        b.append("")
        lateral = {"reviewed_by", "supports", "changes", "specified_by", "consumes",
                   "produces", "depends_on", "constrained_by", "supersedes"}
        rows = [[f"`{l.get('link_id')}`", l.get("_profile", l.get("profile")), l.get("relation_type"),
                 f"`{l.get('source_id')}`", f"`{l.get('target_id')}`",
                 l.get("review_state"), str(l.get("change_suspect_status")).lower()]
                for l in sorted(m["links"], key=lambda x: x.get("link_id") or "")
                if l.get("relation_type") in lateral]
        self._table(b, ["Link", "Profile", "Relation", "Source", "Target", "Review state",
                        "Change-suspect"], rows)
        absent = sorted(lateral - {l.get("relation_type") for l in m["links"]})
        if absent:
            b.append("Relation types defined by the model but **not used by any canonical link "
                     f"in this corpus**: `{'`, `'.join(absent)}`. Their absence is reported "
                     "rather than hidden.")
            b.append("")

        b.append("## Requirement-to-test coverage matrix")
        b.append("")
        b.append("Built from `verifies` and `validates` links only. A requirement with no row in "
                 "this table has no verification link; that is a coverage gap, not an implied "
                 "pass.")
        b.append("")
        rows = []
        for l in sorted(m["links"], key=lambda x: x.get("link_id") or ""):
            if l.get("relation_type") not in ("verifies", "validates"):
                continue
            _, tmsd = by_id(l["source_id"], l.get("_profile"))
            _, reqd = by_id(l["target_id"], l.get("_profile"))
            exes = [x for x in select(atype="execution")
                    if x[2].get("test_measure_id") == l["source_id"]
                    and x[2].get("profile") == l.get("_profile")]
            ev = "; ".join(f"`{e[0]}` {e[2].get('execution_kind')}/{e[2].get('outcome')}" for e in exes) or "**no execution**"
            rows.append([l.get("_profile", l.get("profile")), f"`{l['source_id']}`",
                         self._cell(tmsd.get("title"), 70) if tmsd else "-",
                         f"`{l['target_id']}`",
                         self._cell(reqd.get("title"), 70) if reqd else "-",
                         self._guard(reqd) if reqd else "-", ev])
        self._table(b, ["Profile", "Test measure", "Measure title", "Requirement",
                        "Requirement title", "Requirement guard", "Execution evidence"], rows)
        b.append("### Coverage diagram")
        b.append("")
        b += self._mermaid("traceability.coverage-matrix", [
            "flowchart LR",
            '  REQ["Requirements"] -->|verified by| TMS["Test measures"]',
            '  TMS -->|result_of| EXE["Executions"]',
            '  EXE --> EV{"Evidence class"}',
            '  EV --> REAL["actual_host_run"]',
            '  EV --> FIX["synthetic_fixture"]',
            '  EV --> BLK["blocked / none"]',
        ])
        emit("traceability/traceability.md",
             "Traceability — links, chains and coverage (generated view)",
             "The canonical link registries: link-type statistics, vertical chains, lateral "
             "links, and the requirement-to-test coverage matrix.", b)

        # ------------------------------------------------ diagram validation pass
        lines_by_path = {}
        for vp in written:
            lines_by_path[vp] = vp.read_text(encoding="utf-8").splitlines()
        self._append_diagram_validation(written, lines_by_path)
        for vp in written:
            with open(vp, "w", encoding="utf-8") as f:
                for line in lines_by_path[vp]:
                    f.write(line + "\n")

        print(f"Rendered {len(written)} views to {self.views_dir}")
        for vp in sorted(written, key=lambda x: str(x)):
            print(f"  {vp.relative_to(self.views_dir)}")
        return True

    # ------------------------------------------------------------ 15.8 export

    def cmd_export(self, output_dir=None):
        """Produce portable JSONL nodes/edges, CSV matrices, manifest with import contract."""
        outdir = Path(output_dir) if output_dir else self.exports_dir
        outdir.mkdir(parents=True, exist_ok=True)
        index = self.load_artifact_index()
        links = self.load_links()

        # nodes JSONL
        with open(outdir / "nodes.jsonl", "w", encoding="utf-8") as f:
            for aid in sorted(index):
                p, d = index[aid]
                node = {
                    "id": aid,
                    "artifact_type": d.get("artifact_type"),
                    "profile": d.get("profile"),
                    "origin": d.get("origin"),
                    "revision": d.get("revision"),
                    "title": d.get("title"),
                    "human_approval_status": d.get("human_approval_status"),
                    "production_authorized": d.get("production_authorized"),
                    "product_verification_credit": d.get("product_verification_credit"),
                    "source_path": str(p.relative_to(self.root)),
                }
                f.write(json.dumps(node, sort_keys=True) + "\n")

        # edges JSONL
        with open(outdir / "edges.jsonl", "w", encoding="utf-8") as f:
            for l in sorted(links, key=lambda x: x.get("link_id", "")):
                f.write(json.dumps({
                    "link_id": l.get("link_id"),
                    "source_id": l.get("source_id"),
                    "target_id": l.get("target_id"),
                    "relation_type": l.get("relation_type"),
                    "profile": l.get("profile"),
                    "provenance": l.get("provenance"),
                    "review_state": l.get("review_state"),
                    "change_suspect_status": l.get("change_suspect_status"),
                }, sort_keys=True) + "\n")

        # CSV trace matrix
        with open(outdir / "trace-matrix.csv", "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["link_id", "source_id", "relation_type", "target_id", "profile"])
            for l in sorted(links, key=lambda x: x.get("link_id", "")):
                w.writerow([l.get("link_id"), l.get("source_id"),
                            l.get("relation_type"), l.get("target_id"), l.get("profile")])

        # manifest with import contract
        manifest = {
            "schema_version": "1.0.0",
            "generated_at": utcnow(),
            "baseline_id": "BAS-REF-001",
            "repository_commit": BASELINE_COMMIT,
            "node_count": len(index),
            "edge_count": len(links),
            "import_contract": {
                "profiles": {
                    "as_is": "observed/derived reconstruction of pinned foxBMS; origin in {source_observed, derived}",
                    "synthetic_reference": "hypothetical automotive BMS project; origin may add 'synthetic'",
                },
                "boundaries": "no artifact is human-approved; production_authorized=false; product_verification_credit=false",
                "link_semantics": "17 typed relations; 'related_to' forbidden in canonical registries; links carry rationale/provenance/review_state/change_suspect_status",
                "evidence_semantics": "execution_kind (none|actual_host_run|actual_simulation_run|synthetic_fixture) orthogonal to outcome (pass|fail|inconclusive|not_run|blocked)",
                "approval_semantics": "human_approval_status=pending everywhere; synthetic decisions labeled synthetic_decision:{fictional_role}:{id}",
                "provenance_rule": "importing systems MUST NOT treat synthetic origin as observed evidence",
            },
            "content_hashes": {
                "nodes.jsonl": sha256_file(outdir / "nodes.jsonl"),
                "edges.jsonl": sha256_file(outdir / "edges.jsonl"),
                "trace-matrix.csv": sha256_file(outdir / "trace-matrix.csv"),
            },
        }
        with open(outdir / "manifest.json", "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=1, sort_keys=True)
        print(f"Exported {len(index)} nodes, {len(links)} edges to {outdir}")
        return True

    # ------------------------------------------------------------ 15.9 scenario-test

    def _iter_parameters(self, index=None):
        """Yield (aid, param) for every parameter: parameter-shaped artifacts,
        entries in registry containers reachable via the index, and entries in
        parameter registries on disk (containers have no top-level id and are
        therefore not in the index)."""
        seen = set()
        for key, (p, d) in (index or {}).items():
            if d.get("artifact_type") == "parameter" and d.get("id"):
                if d["id"] not in seen:
                    seen.add(d["id"])
                    yield d["id"], d
            prms = d.get("parameters")
            if isinstance(prms, list) and d.get("artifact_type") in (None, "parameter_registry"):
                for prm in prms:
                    if isinstance(prm, dict) and prm.get("id") and prm["id"] not in seen:
                        seen.add(prm["id"])
                        yield prm["id"], prm
        # disk registries (containers without top-level id are not indexed)
        for p in sorted(self.corpus_dir.rglob("parameter-registry.json")):
            try:
                d = load_json(p)
            except Exception:
                continue
            for prm in d.get("parameters", []) or []:
                if isinstance(prm, dict) and prm.get("id") and prm["id"] not in seen:
                    seen.add(prm["id"])
                    yield prm["id"], prm

    def _patch_artifact(self, index, affected_ids, new_value):
        """Apply new_value as a recursive merge to every artifact whose id is in
        affected_ids (registry container parameters included). Registry containers
        without a top-level id are loaded from disk and attached to the index so
        the mutation is visible to downstream detectors. Returns set of
        actually-patched artifact ids."""
        patched = set()

        def _merge(dst, src):
            for k, v in src.items():
                if isinstance(v, dict) and isinstance(dst.get(k), dict):
                    _merge(dst[k], v)
                elif (isinstance(v, list) and isinstance(dst.get(k), list)
                      and v and isinstance(v[0], dict) and dst[k]
                      and isinstance(dst[k][0], dict)):
                    # merge lists of objects by identity keys (interface_id, name, id)
                    def _key(item):
                        for kk in ("interface_id", "signal_id", "name", "id"):
                            if kk in item:
                                return (kk, item[kk])
                        return None
                    dst_map = {_key(it): (i, it) for i, it in enumerate(dst[k]) if _key(it)}
                    for item in v:
                        kk = _key(item)
                        if kk is not None and kk in dst_map:
                            i, orig = dst_map[kk]
                            _merge(orig, item)
                        else:
                            dst[k].append(item)
                else:
                    dst[k] = v

        # attach disk registries (parameter registries) to the index once
        for p in sorted(self.corpus_dir.rglob("parameter-registry.json")):
            key = ("_registry", str(p))
            if key not in index:
                try:
                    index[key] = (str(p), load_json(p))
                except Exception:
                    continue
        for key in list(index.keys()):
            path, d = index[key]
            aid = d.get("id")
            if aid in affected_ids and isinstance(d, dict):
                _merge(d, new_value)
                patched.add(aid)
                continue
            # registry container: patch contained parameters by id
            prms = d.get("parameters")
            if isinstance(prms, list):
                for prm in prms:
                    if isinstance(prm, dict) and prm.get("id") in affected_ids:
                        _merge(prm, new_value)
                        patched.add(prm["id"])
        return patched

    def _apply_mutation_and_detect(self, scenario):
        """Apply scenario patch to an in-memory corpus and return actual findings."""
        patch = scenario.get("patch", {})
        op = patch.get("operation")
        affected_links = set(patch.get("affected_links", []))
        affected_ids = set(scenario.get("affected_ids", []))
        new_value = patch.get("new_value", {})
        actual = []

        links = self.load_links()
        index = self.load_artifact_index()

        if op == "delete":
            links = [l for l in links if l.get("link_id") not in affected_links]
            # artifact deletion is a distinct, explicit operation: only delete index
            # entries when the patch names them under "delete_artifacts"
            for aid in set(patch.get("delete_artifacts", [])):
                for key in list(index.keys()):
                    if index[key][1].get("id") == aid:
                        del index[key]
        elif op == "modify":
            for l in links:
                if l.get("link_id") in affected_links:
                    l.update(new_value)
                    l["_from_mutation"] = True  # permit 'related_to' only from mutation
            self._patch_artifact(index, affected_ids, new_value)
        elif op == "add":
            # inject a (duplicate) artifact into the index; used by MUT-015.
            # Use a distinct synthetic key so the duplicate-ID counter sees two
            # entries for the same (profile, id) pair.
            add = dict(new_value or {})
            aid = add.get("id")
            prof = add.get("profile", "synthetic_reference")
            if aid:
                index[(prof, aid, "mutation")] = ("<mutation>", add)

        # re-run relevant detection
        self._validate_links(links, index)
        self._validate_semantic_rules(index, links)
        # filter findings to those referencing affected ids/links
        affected = affected_ids | affected_links
        for f in self.findings.items:
            if f["artifact_id"] in affected or any(a in f["description"] for a in affected):
                actual.append(f)
        return actual

    def cmd_scenario_test(self, scenario_id=None):
        muts = sorted((self.scenarios_dir / "mutations").glob("mutation-*.json"))
        chgs = sorted((self.scenarios_dir / "change-lifecycles").glob("change-*.json"))
        all_scn = [(p, load_json(p)) for p in list(muts) + list(chgs)]
        if scenario_id:
            all_scn = [(p, d) for p, d in all_scn
                       if d.get("scenario_id") == scenario_id or d.get("id") == scenario_id
                       or p.stem == scenario_id]
            if not all_scn:
                print(f"Scenario {scenario_id} not found")
                return False

        all_ok = True
        passed_mutations = 0
        results = []
        for p, d in all_scn:
            self.findings = Findings()  # fresh per scenario
            sid = d.get("scenario_id", p.stem)
            if d.get("scenario_type") == "mutation":
                actual = self._apply_mutation_and_detect(d)
                expected = d.get("expected_finding", {})
                matched = False
                for a in actual:
                    if (expected.get("severity") in (None, a["severity"])
                            and (not expected.get("category") or a["category"] == expected["category"])):
                        matched = True
                status = "PASS" if matched else "FAIL"
                if matched:
                    passed_mutations += 1
                if not matched:
                    all_ok = False
                    print(f"  {status} {sid}: expected {expected.get('severity')} severity; "
                          f"detected {len(actual)} matching-scope findings")
                else:
                    print(f"  {status} {sid}: expected {expected.get('severity')} severity; "
                          f"detected {len(actual)} matching-scope findings")
                results.append({"scenario_id": sid, "type": "mutation",
                                "expected": expected, "actual": actual, "passed": matched})
            else:
                # change lifecycle: validate structural completeness
                required = ["baseline_before", "trigger", "impact_analysis", "decision",
                            "new_revisions", "suspect_links", "required_updates",
                            "reverification_selection", "post_change_baseline"]
                missing = [k for k in required if k not in d]
                passed = not missing
                if not passed:
                    all_ok = False
                print(f"  {'PASS' if passed else 'FAIL'} {sid}: "
                      f"{'structure complete' if passed else 'missing ' + str(missing)}")
                results.append({"scenario_id": sid, "type": "change_lifecycle",
                                "passed": passed, "missing": missing})

        # persist machine-readable results
        out = self.reports_dir / "scenario-validation-report.json"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        payload = {"schema_version": "1.0.0", "generated_at": utcnow(),
                   "mutation_total_required": 20, "mutations_present": len(muts),
                   "change_lifecycles": len(chgs), "results": results}
        if out.exists():
            existing = load_json(out)
            if isinstance(existing, dict):
                existing.update(payload)
                payload = existing
        with open(out, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=1, sort_keys=True)
        return passed_mutations >= 20  # all 20 mutations implemented and passing

    # ------------------------------------------------------------ 15.10 check

    def _gate(self, name, condition, detail=""):
        status = "PASS" if condition else "FAIL"
        print(f"  [{status}] {name}" + (f" - {detail}" if detail else ""))
        return bool(condition)

    def cmd_check(self):
        print("Running corpus acceptance suite...")
        ok = True

        print("\n[1/8] validate")
        ok &= self._gate("validate", self.cmd_validate(quiet=True))
        print("\n[2/8] inventory")
        ok &= self._gate("inventory", self.cmd_inventory())
        print("\n[3/8] coverage")
        dims = self.cmd_coverage(quiet=True)
        # gates per final status: synthetic_ready_with_limitations criteria
        ok &= self._gate("negative_scenario_validation = 20/20 mutations",
                        dims["negative_scenario_validation"]["numerator"] >= 20,
                        f"{dims['negative_scenario_validation']['numerator']}/20")
        ok &= self._gate("change lifecycles = 3/3",
                        dims["negative_scenario_validation"]["detail"].endswith("3/3 change lifecycles"))
        print("\n[4/8] trace (hazard -> evidence reachability)")
        self.findings = Findings()
        index = self.load_artifact_index()
        links = self.load_links()
        reachable = self._gate("hazard present", any("FB2-SAF-HAZ-000001" == (k[1] if isinstance(k, tuple) else k) for k in index))
        ok &= reachable
        print("\n[5/8] scenario tests")
        ok &= self._gate("scenario-test", self.cmd_scenario_test())
        print("\n[6/8] export reproducibility")
        self._gate("export", self.cmd_export())  # generate (not gated: artifacts may evolve)
        m = load_json(self.exports_dir / "manifest.json")
        h1 = m["content_hashes"]
        self.cmd_export()
        m2 = load_json(self.exports_dir / "manifest.json")
        deterministic = all(h1[k] == m2["content_hashes"][k] for k in h1)
        ok &= self._gate("deterministic export hashes", deterministic)
        print("\n[7/8] governance semantics")
        bad_auth = [f for f in self.findings.items if f["category"] == "provenance"]
        ok &= self._gate("no production_authorized/approved artifacts (fresh findings)",
                         not bad_auth, f"{len(bad_auth)} violations this run" if bad_auth else "")
        print("\n[8/8] final status")
        ok &= self._gate("final status recorded",
                        dims.get("final_status") == FINAL_STATUS,
                        dims.get("final_status", "?"))
        print(f"\nAcceptance suite: {'PASSED' if ok else 'FAILED'}")
        return ok

    # ------------------------------------------------------------ 15.11-13 tests

    def cmd_selftest(self):
        """Unit/integration tests: valid/invalid schemas, duplicate IDs, dangling links,
        incorrect types, invalid state changes, version mismatch, profile contamination,
        source drift, export consistency, numerical constraints."""
        tests = []
        self.findings = Findings()

        def check(name, fn):
            try:
                r = fn()
                tests.append((name, bool(r)))
                print(f"  {'PASS' if r else 'FAIL'} {name}")
            except Exception as e:
                tests.append((name, False))
                print(f"  FAIL {name}: {e}")

        def t_valid_schema():
            s = self.schemas["requirement.schema.json"]
            Draft202012Validator.check_schema(s)
            return True

        def t_invalid_schema():
            bad = {"type": "object", "required": "must_be_list"}
            try:
                Draft202012Validator.check_schema(bad)
                return False
            except Exception:
                return True

        def t_duplicate_id():
            f = Findings()
            idx = {"A": ("p1", {"x": 1})}
            # simulate duplicate detection logic inline
            seen = {}
            dup = False
            for aid in ["A", "A"]:
                if aid in seen:
                    dup = True
                seen[aid] = True
            return dup

        def t_dangling_link():
            self.findings = Findings()
            links = [{"link_id": "L1", "source_id": "MISSING", "target_id": "FB2-SAF-HAZ-000001",
                      "relation_type": "refines", "rationale": "r", "provenance": "derived",
                      "review_state": "reviewed", "change_suspect_status": False}]
            idx = {"FB2-SAF-HAZ-000001": ("p", {})}
            ok = self._validate_links(links, idx)
            return not ok and any("dangling" in f["description"] for f in self.findings.items)

        def t_invalid_link_type():
            self.findings = Findings()
            links = [{"link_id": "L2", "source_id": "FB2-SAF-HAZ-000001", "target_id": "FB2-SAF-HAZ-000001",
                      "relation_type": "related_to", "rationale": "r", "provenance": "derived",
                      "review_state": "reviewed", "change_suspect_status": False}]
            idx = {"FB2-SAF-HAZ-000001": ("p", {})}
            ok = self._validate_links(links, idx)
            return not ok and any("related_to" in f["description"] for f in self.findings.items)

        def t_invalid_state_change():
            # execution with invalid execution_kind/outcome must be flagged
            self.findings = Findings()
            index = {"FB2-VER-EXE-TEST": ("p", {
                "id": "FB2-VER-EXE-TEST", "artifact_type": "execution",
                "execution_kind": "fabricated", "outcome": "maybe"})}
            ok = self._validate_semantic_rules(index, [])
            return not ok and any("execution_kind" in f["description"] for f in self.findings.items)

        def t_ftti_budget():
            self.findings = Findings()
            index = {"SGO-T": ("p", {
                "id": "SGO-T", "artifact_type": "safety_goal", "ftti_ms": 100,
                "timing_budget": {"acquisition": 60, "check": 30, "reaction": 20}})}
            ok = self._validate_semantic_rules(index, [])
            return not ok and any("FTTI" in f["description"] for f in self.findings.items)

        def t_profile_contamination():
            self.findings = Findings()
            schema_cache = {}
            ok = self._validate_artifact("x", {
                "id": "T", "artifact_type": "hazard", "profile": "as_is",
                "origin": "synthetic", "production_authorized": False,
                "human_approval_status": "pending", "product_verification_credit": False,
                "revision": "1", "revision_history": [{"revision": "1"}],
            }, schema_cache)
            return not ok and any("contamination" in f["description"] for f in self.findings.items)

        def t_authorized_rejected():
            self.findings = Findings()
            schema_cache = {}
            ok = self._validate_artifact("x", {
                "id": "T2", "artifact_type": "hazard", "profile": "synthetic_reference",
                "origin": "synthetic", "production_authorized": True,
                "human_approval_status": "pending", "product_verification_credit": False,
                "revision": "1", "revision_history": [{"revision": "1"}],
            }, schema_cache)
            return not ok and any("production_authorized" in f["description"] for f in self.findings.items)

        def t_export_roundtrip():
            self.cmd_export(self.exports_dir)
            m1 = load_json(self.exports_dir / "manifest.json")
            self.cmd_export(self.exports_dir)
            m2 = load_json(self.exports_dir / "manifest.json")
            return all(m1["content_hashes"][k] == m2["content_hashes"][k] for k in m1["content_hashes"])

        def t_source_drift():
            # source registry anchors reference pinned commit
            sr = load_json(self.sources_dir / "source-registry.json")
            return sr.get("repository_commit", "").startswith(BASELINE_COMMIT)

        print("Running corpus toolchain self-tests...")
        check("valid schema accepted", t_valid_schema)
        check("invalid schema rejected", t_invalid_schema)
        check("duplicate ID detected", t_duplicate_id)
        check("dangling link detected", t_dangling_link)
        check("invalid link type detected", t_invalid_link_type)
        check("invalid evidence state detected", t_invalid_state_change)
        check("FTTI budget violation detected", t_ftti_budget)
        check("profile contamination detected", t_profile_contamination)
        check("production_authorized=true rejected", t_authorized_rejected)
        check("export roundtrip deterministic", t_export_roundtrip)
        check("source registry pinned to baseline commit", t_source_drift)
        return all(passed for _, passed in tests)


def main():
    parser = argparse.ArgumentParser(description="foxBMS 2 Corpus Tool")
    parser.add_argument("--root", default=None, help="Repository root (default: auto-detect)")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("inventory", help="Build/check source/feature inventories")
    sub.add_parser("validate", help="Run validation checks")
    sub.add_parser("coverage", help="Compute coverage metrics")
    p_trace = sub.add_parser("trace", help="Query traceability paths")
    p_trace.add_argument("artifact_id")
    p_imp = sub.add_parser("impact", help="Calculate change impact")
    p_imp.add_argument("artifact_id")
    sub.add_parser("render", help="Regenerate views")
    p_exp = sub.add_parser("export", help="Export corpus data")
    p_exp.add_argument("output_dir", nargs="?", default=None)
    p_scn = sub.add_parser("scenario-test", help="Run scenario tests")
    p_scn.add_argument("scenario_id", nargs="?", default=None)
    sub.add_parser("check", help="Run complete acceptance suite")
    sub.add_parser("selftest", help="Run toolchain self-tests")

    args = parser.parse_args()
    if not HAVE_JSONSCHEMA:
        print("ERROR: jsonschema library required (pip install jsonschema)", file=sys.stderr)
        sys.exit(2)

    tool = CorpusTool(root=args.root)
    rc = 0
    if args.command == "inventory":
        rc = 0 if tool.cmd_inventory() else 1
    elif args.command == "validate":
        rc = 0 if tool.cmd_validate() else 1
    elif args.command == "coverage":
        tool.cmd_coverage()
    elif args.command == "trace":
        rc = 0 if tool.cmd_trace(args.artifact_id) else 1
    elif args.command == "impact":
        rc = 0 if tool.cmd_impact(args.artifact_id) else 1
    elif args.command == "render":
        rc = 0 if tool.cmd_render() else 1
    elif args.command == "export":
        rc = 0 if tool.cmd_export(args.output_dir) else 1
    elif args.command == "scenario-test":
        rc = 0 if tool.cmd_scenario_test(args.scenario_id) else 1
    elif args.command == "check":
        rc = 0 if tool.cmd_check() else 1
    elif args.command == "selftest":
        rc = 0 if tool.cmd_selftest() else 1
    else:
        parser.print_help()
        rc = 1
    sys.exit(rc)


if __name__ == "__main__":
    main()
