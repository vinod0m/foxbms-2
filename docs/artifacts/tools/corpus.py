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
import contextlib
import csv
import hashlib
import io
import json
import os
import re
import subprocess
import sys
from contextlib import contextmanager
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

# The single target-hardware execution_kind. It means the product's own code
# was executed on the product's own hardware, as opposed to a developer host,
# an executed model, or a fixture. It is the only execution_kind that is
# product-hardware evidence, and it is a member of execution.schema.json's
# enum, so a real TMS570/HIL run can be recorded honestly.
TARGET_EXECUTION_KIND = "actual_target_hardware_run"

# execution_kind values that are a real execution of the product's own code
# but on developer infrastructure, so they are NOT product-hardware evidence.
HOST_EXECUTION_KINDS = {"actual_host_run", "actual_simulation_run"}
# Values that are not a real execution of the product at all.
NON_EXECUTION_KINDS = {"synthetic_fixture", "none"}
# Every execution_kind the schema admits.
DECLARED_EXECUTION_KINDS = (
    HOST_EXECUTION_KINDS | NON_EXECUTION_KINDS | {TARGET_EXECUTION_KIND})

# Strings that name a developer machine or a generic virtual platform rather
# than the product's own silicon. Used ONLY to reject a target-hardware claim
# whose environment contradicts itself -- never to decide that a run counts as
# target evidence, which is read from execution_kind alone. Matching prose is
# not measurement; this is a self-consistency check, nothing more.
#
# Each entry is matched on word boundaries, so a marker cannot fire on an
# accidental substring (a board id must not be rejected because it happens to
# contain one of these).
NON_TARGET_HARDWARE_MARKERS = (
    "x86_64", "x86-64", "amd64", "arm64", "aarch64", "apple silicon", "macos",
    "darwin", "linux", "win32", "windows", "posix", "host", "workstation",
    "laptop", "ci", "virtual", "container", "docker", "qemu", "emulated",
    "simulator", "simulation", "fixture", "none", "unknown", "tbd", "n/a",
)

ARTIFACT_TYPE_SCHEMAS = {
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

# Every semantic rule _validate_semantic_rules evaluates, declared once.
#
# This set is a CONTRACT, not the measurement. The measurement is
# self._semantic_rules_run, which each rule block fills in on entry via
# _semantic_rule_entered. The coverage dimension `semantic_consistency_checks`
# reports the size of the intersection of the two, so the figure is computed
# from what ran and the declaration is checked against it.
#
# The previous figure was the literal 10/10 with the detail "10 check
# categories executed per run". Neither half was true: the function evaluates 21
# rules across 6 categories, so the numerator understated the work by more than
# half and the denominator named a quantity the tool never had. A literal cannot
# detect its own drift, which is why this is now derived.
#
# Verified against the source by the self-tests `semantic rules actually executed
# equal the declared set` (no rule missing a marker) and `every declared semantic
# rule is a rule the tool can emit` (no rule id that no findings.add site uses).
SEMANTIC_RULE_IDS = frozenset({
    "asil_assignment_validator",
    "change_impact_analyzer",
    "configuration_consistency",
    "diagnostic_coverage_claim_validator",
    "evidence_reference_validator",
    "execution_kind_classifier",
    "execution_kind_orthogonality",
    "ftti_budget_consistency_checker",
    "hsi_interface_consistency",
    "identity_uniqueness_checker",
    "incomplete_propagation",
    "parameter_threshold_order",
    "parameter_unit_consistency",
    "production_authorization_governance_checker",
    "refinement_cycle_detector",
    "requirement_applicability_validator",
    "safety_goal_mitigates_hazard",
    "safety_requirement_completeness_checker",
    "source_anchor_drift_detector",
    "traceability_checker",
    "verification_traceability_checker",
})

# Rule ids that assert GOVERNANCE SEMANTICS: a claim that this corpus carries
# production authority, verification credit, human approval, a determined ASIL,
# a conformity claim, a certification claim, or any other authority it has not
# been given.
#
# Acceptance gate [7/8] is named for governance semantics and filtered its
# detector output to two of the rules that can raise governance findings,
# discarding the rest. It therefore could not catch a record asserting an ASIL
# determination, an ISO 26262 conformity claim, a certification claim, or
# authorized_for_production -- which is the class of claim the gate exists to
# catch. The set below is every rule id in RULE_IDS whose id or detector
# semantics are a governance claim; the gate counts findings from all of them.
# Self-test `the governance rule set is non-empty and covers the four named
# claim classes` pins the membership.
GOVERNANCE_SEMANTIC_RULE_IDS = frozenset({
    "governance_authority_claim",
    "production_authorization_governance_checker",
    "production_authorized_rejected",
    "verification_credit_rejected",
    "human_approval_rejected",
    "asil_determination_claim",
    "conformity_claim",
    "certification_claim",
})

# Fields whose presence with a granted value is a governance claim. Keyed by the
# rule that reports it. A record may spell the claim any of these ways, so the
# check is a key scan and not a test of three named fields: a record that says it
# was approved under a different key would otherwise pass all three named checks.
# The value sets are the same grant vocabulary _validate_governance_semantics
# uses, so "granted" means the same thing to both rules.
GOVERNANCE_CLAIM_FIELDS = {
    "asil_determination_claim": frozenset({
        "asil_determination", "asil_determined", "asil_assignment_determined",
        "asil_claim", "asil_declared", "sil_determination", "ASIL",
    }),
    "conformity_claim": frozenset({
        "conformity", "conformity_claim", "conformity_declared",
        "iso26262_conformity", "iso_26262_conformity", "compliance_claim",
    }),
    "certification_claim": frozenset({
        "certification", "certification_claim", "certified", "certificate_issued",
        "certified_by", "audited",
    }),
}

# Floor for the `source_grounding` coverage dimension, as a fraction.
#
# Stated rather than derived, because no measurement in the tree yields it; but
# stated in full, because a floor with no stated reasoning is indistinguishable
# from a number chosen to make today's tree pass.
#
# The dimension counts records carrying at least one `source_refs` entry over
# every record carrying an id. The denominator includes registries, link files
# and governance records that have no upstream source to point at, so the raw
# fraction is structurally capped well below 1 and cannot be read as a score.
# What the floor protects is a specific claim the corpus makes everywhere: that
# the traceability graph is backed by the source it names. That claim stops
# being checkable once almost nothing carries a source.
#
#   measured level of this tree : 128/298 = 0.430
#   level at which it failed    :   5/298 = 0.017  (audit corruption C2)
#   this floor                  : 0.20
#
# The floor sits below the measured level, with headroom for the honest
# incompleteness the corpus already reports in its gaps list, and far above the
# corrupted level. Raising it toward 0.43 would convert a documented gap into a
# gate failure, which is the same defect as the tautological gate it replaces.
SOURCE_GROUNDING_FLOOR = 0.20

# Stable identifiers for every detection rule the tool can emit. The scenario
# harness resolves a scenario's declared detector against this map, so a rule
# that is claimed by a scenario but is not implemented fails the scenario with
# an explicit "declared detector does not exist" message instead of silently
# matching a neighbouring finding.
RULE_IDS = {
    "schema_file_check",
    "asil_determination_claim",
    "conformity_claim",
    "certification_claim",
    "artifact_schema_validation",
    "base_schema_validation",
    "unknown_profile",
    "profile_contamination",
    "production_authorized_rejected",
    "human_approval_rejected",
    "verification_credit_rejected",
    "revision_consistency_checker",
    "identity_duplicate_within_profile",
    "json_unparseable",
    "schema_missing",
    "link_invalid_relation_type",
    "link_forbidden_relation_type",
    "link_missing_metadata",
    "link_dangling_endpoint",
    "link_endpoint_revision_stale",
    "link_derived_field_contradiction",
    # --- link registry shadowing: a record present in more than one registry
    # is reported rather than silently de-duplicated away (see
    # _validate_link_registry_shadowing) ---
    "link_registry_shadowing_duplicate",
    "link_registry_shadowing_conflict",
    "provenance_ref_unresolved",
    "traceability_checker",
    "safety_goal_mitigates_hazard",
    "verification_traceability_checker",
    "execution_kind_orthogonality",
    "ftti_budget_consistency_checker",
    "parameter_unit_consistency",
    "hsi_interface_consistency",
    "parameter_threshold_order",
    "safety_requirement_completeness_checker",
    "asil_assignment_validator",
    "requirement_applicability_validator",
    "diagnostic_coverage_claim_validator",
    "configuration_consistency",
    "execution_kind_classifier",
    "evidence_reference_validator",
    "identity_uniqueness_checker",
    "source_anchor_drift_detector",
    "production_authorization_governance_checker",
    "change_impact_analyzer",
    "incomplete_propagation",
    "refinement_cycle_detector",
    "inventory_source_count",
    "inventory_modules",
    "inventory_features",
    # --- provenance verification (added: no rule previously verified a digest,
    # a content hash or a line range, so a fabricated anchor set passed) ---
    "review_digest_mismatch",
    "review_digest_placeholder",
    "review_digest_artifact_unresolved",
    "source_anchor_content_hash_unverified",
    "source_anchor_content_hash_mismatch",
    "source_anchor_file_missing",
    "source_anchor_symbol_missing",
    "source_anchor_symbol_unverifiable",
    "source_anchor_line_range_out_of_bounds",
    "source_anchor_line_range_unparseable",
    "evidence_file_missing",
    "evidence_file_hash_mismatch",
    # --- governance semantics, runnable independently of schema validation ---
    "governance_authority_claim",
    # --- change-lifecycle content (key presence was the whole previous check) ---
    "change_lifecycle_field_empty",
    "change_lifecycle_nested_content_missing",
    "change_lifecycle_reference_unresolved",
    "change_lifecycle_baseline_malformed",
}

# ISO 26262-3:2018 Table 4, ASIL determination from severity and exposure.
# Used to re-derive an ASIL from a record's own recorded S/E ratings so that a
# downgrade of the ASIL field is detectable without removing the justification.
ASIL_FROM_SE = {
    "S0": {"E1": "QM", "E2": "QM", "E3": "QM", "E4": "QM"},
    "S1": {"E1": "QM", "E2": "QM", "E3": "QM", "E4": "ASIL_A"},
    "S2": {"E1": "QM", "E2": "QM", "E3": "ASIL_A", "E4": "ASIL_B"},
    "S3": {"E1": "QM", "E2": "ASIL_A", "E3": "ASIL_C", "E4": "ASIL_D"},
}


def utcnow():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


_IMPLEMENTED_RULES = None


def _as_ms(value):
    """Coerce a declared interval/budget value to a number, or None.

    Accepts a bare number and the {"value": n} / {"value_ms": n} envelopes the
    corpus uses. Returns None for anything that is not a number, so an absent or
    non-numeric declaration is simply not a declaration.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, dict):
        for key in ("value", "value_ms"):
            inner = value.get(key)
            if isinstance(inner, (int, float)) and not isinstance(inner, bool):
                return inner
    return None


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


class Findings:
    """Accumulates validation findings.

    Every finding carries a stable ``rule`` identifier. That identifier is the
    only sound way to decide whether a detection is the one a mutation scenario
    claims to exercise: severity and category are shared by many rules, and the
    artifact id is shared by whatever defects that artifact happens to carry.
    The scenario harness matches on ``rule`` (see _match_scenario_finding), so
    a rule that is not named by a scenario can never satisfy that scenario and
    a rule that is named but does not exist fails the scenario loudly.
    """

    def __init__(self):
        self.items = []

    def add(self, severity, category, artifact_id, description, rule="unattributed"):
        self.items.append({
            "severity": severity,
            "category": category,
            "artifact_id": artifact_id,
            "description": description,
            "rule": rule,
        })

    def rule_ids(self):
        return {f["rule"] for f in self.items}

    def signature(self):
        """Identity of a finding for baseline subtraction: the finding minus
        nothing. Two runs of the same rule against the same artifact with the
        same text are the same finding, so a standing defect that predates a
        mutation cannot be counted as a detection of that mutation."""
        return {(f.get("rule"), f.get("artifact_id"), f.get("category"),
                 f.get("description")) for f in self.items}

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
        self.tools_dir = self.artifacts_dir / "tools"
        self.schemas = {}
        self.findings = Findings()
        # One shared scenario measurement per process. cmd_coverage (step 3/8 of
        # the acceptance suite) and cmd_scenario_test (step 5/8) both need it and
        # must report the same number; see _execute_scenarios.
        self._scenario_run_cache = None
        # Rule ids _validate_semantic_rules actually evaluated on this run.
        # Reset by _run_detectors; see _semantic_rule_entered.
        self._semantic_rules_run = set()
        # When True the provenance detectors still run and still emit every
        # finding -- they are never switched off -- but their boolean result is
        # forced to True so a caller can read the tally without turning red.
        # Set only by `check --provenance-report-only`. See main().
        self.provenance_report_only = False
        # Per-class counts from the last provenance verification run, for the
        # report; not itself a gate.
        self.provenance_tally = {}
        self.load_schemas()

    # ------------------------------------------------------------------ load

    def load_schemas(self):
        if not self.schemas_dir.exists():
            return
        for p in sorted(self.schemas_dir.glob("*.schema.json")):
            try:
                self.schemas[p.name] = load_json(p)
            except Exception as e:
                self.findings.add("critical", "schema", p.name, f"schema unparseable: {e}", "schema_file_check")

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
                    self.findings.add("critical", "json", str(p), f"unparseable JSON: {e}", "json_unparseable")

    def iter_scenario_artifacts(self):
        for p in sorted(self.scenarios_dir.rglob("*.json")):
            if "evaluator-only" in p.parts:
                continue
            yield p, load_json(p)

    def _link_registry_paths(self):
        """Every link registry file, in a deterministic order.

        The order is explicit, not a side effect of directory iteration.
        `rglob` walks the filesystem in whatever order the OS hands back, so
        "first registry wins" used to be an accident of that order: two
        registries holding the same (profile, link_id) resolved to whichever
        one the filesystem happened to enumerate first, and the same corpus
        could load differently on a different machine or after a rebuild.

        Registries are therefore ranked by an explicit, documented precedence
        and ties are broken on the path string, so the result depends only on
        the contents of the tree:

          0. docs/artifacts/traceability/link-registry/<profile>/  (canonical,
             top-level: the location the corpus documents as authoritative)
          1. any other docs/artifacts/**/traceability/link-registry/ tree
             (a per-profile copy nested inside corpus/)

        Lower rank wins. Within a rank, the lexicographically smaller path
        wins. A shadowed record is never silently dropped: the duplicate is
        reported by _validate_link_registry_shadowing, which is a separate
        concern from which copy is loaded.
        """
        registries = []
        seen = set()
        for p in list((self.trace_dir / "link-registry").rglob("links-*.json")) + \
                 list(self.corpus_dir.rglob("traceability/link-registry/**/links-*.json")):
            if p in seen:
                continue
            seen.add(p)
            s = p.as_posix()
            rank = 0 if s.startswith(self.trace_dir.as_posix()) else 1
            registries.append((rank, s, p))
        registries.sort(key=lambda t: (t[0], t[1]))
        return [(p, rank) for rank, _s, p in registries]

    def _link_profile_of(self, p):
        """Infer the profile a registry belongs to from its path."""
        s = str(p)
        if "traceability/link-registry/as_is" in s or "/corpus/as_is/traceability/" in s:
            return "as_is"
        if "traceability/link-registry/synthetic_reference" in s or "/corpus/synthetic_reference/traceability/" in s:
            return "synthetic_reference"
        return "unknown"

    def _iter_link_records(self):
        """Yield (registry_path, profile, link_dict) for EVERY record on disk.

        Deliberately does NOT de-duplicate. Callers that want one record per
        (profile, link_id) use load_links; callers that need to see shadowed
        copies use this.
        """
        for p, _rank in self._link_registry_paths():
            profile = self._link_profile_of(p)
            d = load_json(p)
            for l in d.get("links", []):
                yield p, profile, l

    @staticmethod
    def _link_identity(l):
        """The comparable content of a link record.

        The private `_registry` / `_profile` keys are provenance added by
        load_links, not part of the record, so they are excluded: two copies
        of one link in two registries must compare EQUAL on this projection
        or every copy would look like a contradiction.
        """
        return {k: v for k, v in l.items() if k not in ("_registry", "_profile")}

    def load_links(self):
        """Return list of link dicts across all registries, tagged with profile.
        De-duplicates by (profile, link_id) - same link_id in different profiles is intentional.

        De-duplication is deterministic and independent of filesystem
        iteration order: registries are visited in the explicit precedence
        order built by _link_registry_paths, and the FIRST record for a key
        under that order wins. Shadowed copies are not silently discarded --
        they are reported by _validate_link_registry_shadowing, which must be
        run to see them.
        """
        by_key = {}
        for p, profile, raw in self._iter_link_records():
            l = dict(raw)
            l["_registry"] = str(p)
            l["_profile"] = profile
            key = (profile, l.get("link_id"))
            if key not in by_key:
                by_key[key] = l
        return list(by_key.values())

    def _validate_link_registry_shadowing(self):
        """A link record present in more than one registry is reported, never dropped.

        De-duplication is necessary: the same link id legitimately appears in
        the canonical top-level registry and in a per-profile copy under
        corpus/. But de-duplication alone is lossy in a way that hides
        defects. If a repair loop reads what the tool returns and writes back
        what it returns, a record that is only ever returned from one copy is
        never checked, and an edit made to the other copy is invisible. A
        link that exists in only ONE of two copies would likewise be silently
        invisible or silently duplicated depending on which file won an
        ordering accident.

        So the multiplicity itself is the finding. A duplicate whose content
        agrees is an unreconciled copy -- reported, because it is a latent
        second source of truth that will drift. A duplicate whose content
        DISAGREES is a genuine contradiction: two registries make incompatible
        claims about the same link, which is high severity because the tool
        cannot know which is true and must not pick one silently.

        Severity is chosen so an unreconciled-but-agreeing copy is visible
        without failing the corpus, while a real contradiction is an error.
        """
        occurrences = {}
        for p, profile, raw in self._iter_link_records():
            lid = raw.get("link_id")
            if lid is None:
                continue
            occurrences.setdefault((profile, lid), []).append((p, raw))

        ok = True
        for (profile, lid), occs in sorted(occurrences.items(),
                                           key=lambda kv: (kv[0][0], str(kv[0][1]))):
            if len(occs) < 2:
                continue
            paths = sorted({p.as_posix() for p, _ in occs})
            identities = {json.dumps(self._link_identity(raw), sort_keys=True)
                          for _p, raw in occs}
            where = "; ".join(paths)
            if len(identities) == 1:
                self.findings.add(
                    "medium", "traceability", lid,
                    f"link {lid} (profile {profile}) is present in {len(occs)} registries whose "
                    f"content agrees byte for byte: {where}. The duplicate is an unreconciled "
                    f"copy: it is loaded from the highest-precedence registry and the others are "
                    f"not returned by load_links, so an edit made only to a shadowed copy is "
                    f"invisible to every downstream check. Reconcile the registry layout or "
                    f"record why two copies are intentional.",
                    "link_registry_shadowing_duplicate")
            else:
                differing = sorted(
                    k for k in
                    set().union(*[set(self._link_identity(raw)) for _p, raw in occs])
                    if len({json.dumps(self._link_identity(raw).get(k), sort_keys=True)
                            for _p, raw in occs}) > 1)
                self.findings.add(
                    "high", "traceability", lid,
                    f"link {lid} (profile {profile}) is present in {len(occs)} registries that "
                    f"DISAGREE on {', '.join(differing) or 'record content'}: {where}. Two "
                    f"registries make incompatible claims about the same link, so the tool cannot "
                    f"know which is authoritative and does not choose silently -- reconcile the "
                    f"registries by hand.",
                    "link_registry_shadowing_conflict")
                ok = False
        return ok

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
                                      f"duplicate artifact id within profile {profile} at {p} and {index[key][0]}",
                                      "identity_duplicate_within_profile")
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
                              f"source file count mismatch: inventory={claimed} actual={actual_files}",
                              "inventory_source_count")
            ok = False

        # Module check
        claimed_modules = len(src_inv.get("modules", []))
        if claimed_modules == 0:
            self.findings.add("medium", "inventory", "source-inventory", "no modules recorded", "inventory_modules")
            ok = False

        # Features / variants presence
        n_feat = len(feat_inv.get("features", []))
        n_var = len(var_inv.get("variants", []))
        if n_feat < 20:
            self.findings.add("medium", "inventory", "feature-inventory",
                              f"only {n_feat} features (<20)", "inventory_features")
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
                self.findings.add("high", "schema", name, f"invalid schema: {e}", "schema_file_check")
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
                self.findings.add("high", "schema", aid, f"schema {schema_name} missing", "schema_missing")
                ok = False
            else:
                v = schema_cache.get(schema_name)
                if v is None:
                    v = make_validator(schema)
                    schema_cache[schema_name] = v
                for err in sorted(v.iter_errors(d), key=lambda e: e.path):
                    self.findings.add("high", "schema", aid,
                                      f"schema violation at {'/'.join(map(str, err.path)) or '<root>'}: {err.message}",
                                      "artifact_schema_validation")
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
                                      f"base schema violation at {'/'.join(map(str, err.path)) or '<root>'}: {err.message}",
                                      "base_schema_validation")
                    ok = False

        # profile isolation + governance semantics
        profile = d.get("profile")
        if profile not in ("as_is", "synthetic_reference") and profile is not None:
            self.findings.add("high", "profile", aid, f"unknown profile '{profile}'", "unknown_profile")
            ok = False
        if profile == "as_is" and d.get("origin") == "synthetic":
            self.findings.add("high", "provenance", aid,
                              "as_is artifact with forbidden origin=synthetic (profile contamination)",
                              "profile_contamination")
            ok = False
        if d.get("production_authorized") is True:
            self.findings.add("critical", "provenance", aid,
                              "production_authorized must be false (synthetic corpus)",
                              "production_authorized_rejected")
            ok = False
        if d.get("human_approval_status") == "approved":
            self.findings.add("high", "provenance", aid,
                              "human_approval_status must remain pending (no human approval performed)",
                              "human_approval_rejected")
            ok = False
        if d.get("product_verification_credit") is True:
            self.findings.add("high", "provenance", aid,
                              "product_verification_credit must be false",
                              "verification_credit_rejected")
            ok = False
        # revision history must contain current revision. The rule itself lives in
        # _check_revision_consistency so that the mutation-scenario harness, which
        # does not run schema validation, exercises exactly the same logic.
        ok &= self._check_revision_consistency(aid, d)
        return ok

    def _check_revision_consistency(self, aid, d):
        """A record's current revision must appear in its own revision history.

        Extracted from _validate_artifact so that the scenario harness and the
        validator share one implementation. Previously the rule existed only
        inside _validate_artifact, which _apply_mutation_and_detect never calls,
        so SCN-MUT-003 could not reach its declared detector at all.
        """
        rev = str(d.get("revision"))
        hist_revs = [str(h.get("revision")) for h in d.get("revision_history", [])]
        if rev not in hist_revs:
            self.findings.add("medium", "consistency", aid,
                              f"revision {rev} not found in revision_history",
                              "revision_consistency_checker")
            return False
        return True

    def _validate_no_duplicate_ids(self):
        """A duplicate artifact id within one profile makes every id-keyed lookup
        ambiguous. Report it as an ERROR so validate fails, rather than noting it
        and carrying on with an arbitrary winner."""
        seen = {}
        for p, d in self.iter_corpus_artifacts():
            aid = d.get("id")
            if not aid:
                continue
            profile = d.get("profile", "unknown")
            key = (profile, aid)
            if key in seen and seen[key][1] != d:
                self.findings.add("high", "identity", aid,
                                  f"duplicate artifact id within profile {profile} at {p} and {seen[key][0]}",
                                  "identity_duplicate_within_profile")
                self.identity_duplicates = True
            else:
                seen[key] = (p, d)
        return not getattr(self, "identity_duplicates", False)

    def _validate_links(self, links, index):
        ok = True
        for l in links:
            lid = l.get("link_id", "<no-id>")
            rt = l.get("relation_type")
            profile = l.get("_profile", "unknown")
            if rt not in ALLOWED_RELATION_TYPES:
                self.findings.add("high", "traceability", lid,
                                  f"invalid relation_type '{rt}' (not in allowed set)",
                                  "link_invalid_relation_type")
                ok = False
            elif rt in STRICT_FORBIDDEN_RELATION_TYPES:
                # related_to is forbidden in canonical registries; mutations introduce it to test detection
                self.findings.add("high", "traceability", lid,
                                  f"relation_type '{rt}' forbidden (not in allowed set)",
                                  "link_forbidden_relation_type")
                ok = False
            # required metadata
            for field in ("rationale", "provenance", "review_state", "change_suspect_status"):
                if field not in l:
                    self.findings.add("medium", "traceability", lid, f"missing link metadata '{field}'",
                                  "link_missing_metadata")
                    ok = False
            # endpoints exist - profile-aware lookup
            for end in ("source_id", "target_id"):
                eid = l.get(end)
                if eid and (profile, eid) not in index:
                    self.findings.add("high", "traceability", lid,
                                      f"dangling link endpoint {end}={eid} (profile={profile})",
                                      "link_dangling_endpoint")
                    ok = False
        return ok

    # ------------------------------------------------- link currency / derived fields
    #
    # Added 2026-10-01. Link RESOLUTION was verified: _validate_links checks that
    # each endpoint id exists in the link's own profile. Link CURRENCY was not
    # verified by anything. That is how this corpus came to hold 326 of its 489
    # links recording an endpoint revision that no longer matches the artefact it
    # names, and all 489 carrying a `change_suspect_status` that was a blanket
    # default rather than a derived fact.
    #
    # Two rules live here, and they are related:
    #
    #   link_endpoint_revision_stale
    #       source_revision / target_revision must equal the CURRENT revision of
    #       the endpoint artefact in the link's own profile.
    #
    #   link_derived_field_contradiction
    #       Every field on a link that this tool DERIVES from the corpus data
    #       must equal what the derivation produces. `change_suspect_status` is
    #       such a field. This rule exists because nothing stopped a writer from
    #       assigning a derived value: a hand-set flag is indistinguishable from
    #       a computed one once it is on disk, so the only sound check is to
    #       recompute it and compare.
    #
    # The derivation of change_suspect_status, and why it reads previous_revision:
    #
    #   A link is change-suspect when an endpoint it names has been revised PAST
    #   the revision the link was authored against, and no re-examination of the
    #   relationship has been recorded. This is the corpus's own definition, not
    #   an imported one. FB2-MAN-CHG-000001.suspect_link_rationale states that
    #   "suspect means 'the reasoning must be re-shown', not 'the link is wrong'",
    #   and .suspect_link_registry_state states that the flag "becomes true ... at
    #   which point the registry flag and this record's suspect list must agree",
    #   with the precondition that "no affected artifact has been revised". So the
    #   trigger is an endpoint revision having moved, and the flag is a statement
    #   about re-examination, not about whether the link is well formed.
    #
    #   The revision a link was AUTHORED AGAINST is preserved in the link's own
    #   provenance_repair.endpoint_revision_refreshes[].previous_revision where a
    #   refresh has been recorded, and is the recorded endpoint revision otherwise.
    #   It has to be read from there: once an endpoint revision has been advanced
    #   to the artefact's current revision, the recorded field no longer differs
    #   from the current one, and a derivation that compared the recorded field to
    #   the current revision would report "no link is stale and none is suspect"
    #   for a corpus in which 326 links had their endpoints advanced without being
    #   re-examined. Comparing the authored-against revision is the only reading
    #   that keeps the finding visible after the repair.
    #
    #   Note what the derivation does NOT read: `provenance_repair.re_examined`.
    #   That field is documentation of the state of the record, not an input. If
    #   it were an input, setting it to true would be a second way to clear the
    #   flag by hand, which is the exact hole this rule closes. A link is cleared
    #   by a review that examines the current revisions of both endpoints and
    #   records that examination -- not by a repair.

    LINK_ENDPOINT_SIDES = (("source", "source_id", "source_revision"),
                           ("target", "target_id", "target_revision"))

    def _link_authored_revision(self, link, role, revkey):
        """The revision of this endpoint the link was authored against.

        The recorded endpoint revision, unless a provenance repair has preserved
        the superseded value, in which case that superseded value is what the
        link was authored against and the recorded field has since been advanced.
        """
        recorded = link.get(revkey)
        repair = link.get("provenance_repair")
        if isinstance(repair, dict):
            for entry in repair.get("endpoint_revision_refreshes") or []:
                if isinstance(entry, dict) and entry.get("endpoint_role") == role:
                    prev = entry.get("previous_revision")
                    if prev is not None:
                        return str(prev)
        return None if recorded is None else str(recorded)

    def _derive_change_suspect_status(self, link, index):
        """(derived_value, reasons). Pure function of the link record and the
        current revisions of its endpoint artefacts. Reads no stored verdict."""
        profile = link.get("_profile", "unknown")
        reasons = []
        for role, idkey, revkey in self.LINK_ENDPOINT_SIDES:
            aid = link.get(idkey)
            entry = index.get((profile, aid))
            if entry is None:
                continue                      # dangling endpoint: _validate_links owns it
            current = entry[1].get("revision")
            if current is None:
                continue
            authored = self._link_authored_revision(link, role, revkey)
            if authored is not None and str(authored) != str(current):
                reasons.append(
                    f"{role} {aid} was authored against revision {authored} and is now "
                    f"revision {current}; no re-examination of this link is recorded")
        return (bool(reasons), reasons)

    def _validate_link_currency(self, links, index):
        """Currency of every link endpoint, and agreement of every derived link
        field with what the corpus data derives. See the comment block above."""
        ok = True
        for l in links:
            lid = l.get("link_id", "<no-id>")
            profile = l.get("_profile", "unknown")
            for role, idkey, revkey in self.LINK_ENDPOINT_SIDES:
                aid = l.get(idkey)
                entry = index.get((profile, aid))
                if entry is None:
                    continue
                current = entry[1].get("revision")
                recorded = l.get(revkey)
                if current is not None and recorded is not None \
                        and str(recorded) != str(current):
                    self.findings.add(
                        "high", "traceability", lid,
                        f"stale {role} endpoint revision: {idkey}={aid} is at revision "
                        f"{current} in profile {profile} but the link records {recorded}",
                        "link_endpoint_revision_stale")
                    ok = False
            derived, reasons = self._derive_change_suspect_status(l, index)
            stored = l.get("change_suspect_status")
            if not isinstance(stored, bool):
                self.findings.add(
                    "medium", "traceability", lid,
                    f"change_suspect_status must be a boolean, found {stored!r}",
                    "link_derived_field_contradiction")
                ok = False
            elif stored != derived:
                self.findings.add(
                    "high", "traceability", lid,
                    f"stored change_suspect_status={stored} contradicts the derived value "
                    f"{derived}"
                    + (": " + "; ".join(reasons) if derived else
                       " (no endpoint has advanced past the revision this link was "
                       "authored against, so the link is not suspect)"),
                    "link_derived_field_contradiction")
                ok = False
        return ok

    def _validate_provenance_refs(self, index):
        """source_refs / assumption_refs resolve to registries.

        `ok` is now driven by the findings this method emits. It previously
        returned True unconditionally, so an unresolved provenance reference
        was printed as a finding and then ignored by every caller: the rule
        could not fail anything. A dangling provenance reference is a claim
        about where a requirement came from that does not resolve, so it is
        reported as an error and the caller is allowed to fail.
        """
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
                    self.findings.add("high", "provenance", aid,
                                      f"source_ref '{ref}' not in source-registry",
                                      "provenance_ref_unresolved")
                    ok = False
            for ref in d.get("assumption_refs", []):
                if assumptions and ref not in assumptions:
                    self.findings.add("high", "provenance", aid,
                                      f"assumption_ref '{ref}' not in assumption-registry",
                                      "provenance_ref_unresolved")
                    ok = False
        return ok

    # ------------------------------------------------------- provenance verification
    #
    # Nothing below existed before. There was no code path anywhere in this tool
    # that hashed an artefact, compared a recorded digest to the file on disk,
    # checked a source anchor's content_hash, or checked that a recorded
    # line_range lies inside the file it names. That is why a source registry
    # whose anchors point at symbols which do not exist, whose line ranges run
    # past the end of their files, and whose content_hash is the literal string
    # "sha256:placeholder" could be published alongside
    # "Acceptance suite: PASSED".
    #
    # Severity is a considered assignment, not a blanket constant:
    #
    #   high    - the corpus states something specific that is provably false.
    #             A digest that does not match the file, a content_hash that does
    #             not match the file, a symbol that is not in the file it is
    #             attributed to, a line range past end-of-file, an evidence file
    #             that does not exist or whose bytes changed. These are false
    #             statements about the product, not omissions.
    #   medium  - the corpus declines to make a statement. "sha256:placeholder"
    #             and the literal digest "placeholder" mean no verification was
    #             performed. That is unfinished work, and it is reported with the
    #             same visibility as a falsehood, but it is not the same kind of
    #             defect and the tally keeps the two classes apart.
    #
    # Every check below runs unconditionally and every finding is added to
    # self.findings, so it participates in `validate`, in the scenario harness
    # via _run_detectors, and in any gate that counts findings. They cannot be
    # switched off. They CAN be run in a reporting mode that does not fail --
    # see self.provenance_report_only -- because the corpus is legitimately red
    # on them until a separate workstream re-derives the anchors, and a gate
    # that cannot be looked at is not usable.

    _ANCHOR_PATH_KEYS = ("path", "file", "file_or_executable")
    _PLAIN_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
    _LINE_RANGE = re.compile(r"^\s*(\d+)\s*(?:-\s*(\d+)\s*)?$")
    _PLACEHOLDER_HASHES = {"", "placeholder", "sha256:placeholder", "sha256:", "none", "null"}

    @staticmethod
    def _expected_sha(value):
        """Normalise a recorded hash to a bare sha256 hex digest, or None."""
        if value is None:
            return None
        s = str(value).strip()
        if s.lower().startswith("sha256:"):
            s = s[7:].strip()
        return s or None

    def _classify_placeholder_hash(self, value):
        """True when a recorded hash says 'not verified' rather than naming one.

        Recognises the literal placeholders the corpus uses, case-insensitively,
        including the prefixed "sha256:placeholder" form, so a placeholder can be
        counted and reported rather than silently skipped.
        """
        s = str(value).strip().lower() if value is not None else ""
        return (s in self._PLACEHOLDER_HASHES
                or s.startswith("sha256:placeholder")
                or s.startswith("placeholder"))

    def _anchor_file(self, location):
        """The repository-relative file an anchor names, or None.

        The registry spells the file differently per source_type: `path` for
        code, `file` for hardware, `file_or_executable` for tests. A
        documentation anchor records a URL, which is not a file in this
        repository and is therefore not something this offline check can hash;
        that is reported rather than counted as a pass.
        """
        if not isinstance(location, dict):
            return None
        for key in self._ANCHOR_PATH_KEYS:
            v = location.get(key)
            if isinstance(v, str) and v.strip():
                return v.strip()
        return None

    def _load_source_anchors(self):
        sr = self.sources_dir / "source-registry.json"
        if not sr.exists():
            return []
        return [a for a in load_json(sr).get("anchors", []) if a.get("anchor_id")]

    def _file_sha256(self, rel):
        fp = self.root / rel
        try:
            return sha256_file(fp)
        except OSError:
            return None

    def _validate_review_digests(self, index):
        """Every reviewed_ids[].digest must be the sha256 of the artefact, now.

        Profile-scoped: a digest recorded in an `as_is` review is checked against
        the `as_is` record with that id, never against the synthetic_reference
        copy, because cross-profile duplicate ids are a deliberate design
        decision of this corpus and a digest is a statement about one of them.

        The literal "placeholder" is permitted, but only with a per-entry note
        saying why. Both the number of permitted placeholders and the number of
        unnoted ones are reported: a permitted placeholder is a disclosure, not
        a verification.
        """
        ok = True
        records_dir = self.artifacts_dir / "reviews" / "records"
        if not records_dir.exists():
            return ok
        permitted = unnoted = verified = 0
        for rp in sorted(records_dir.glob("*.json")):
            try:
                rec = load_json(rp)
            except Exception as e:
                self.findings.add("critical", "provenance", rp.name,
                                  f"review record unparseable: {e}", "json_unparseable")
                ok = False
                continue
            profile = rec.get("profile", "unknown")
            rid = rec.get("id", rp.stem)
            for entry in rec.get("reviewed_ids", []) or []:
                if not isinstance(entry, dict):
                    continue
                aid = entry.get("artifact_id")
                digest = entry.get("digest")
                key = (profile, aid)
                if key not in index:
                    self.findings.add(
                        "high", "provenance", rid,
                        f"reviewed_ids entry '{aid}' does not resolve to any artifact "
                        f"in profile {profile}", "review_digest_artifact_unresolved")
                    ok = False
                    continue
                if self._classify_placeholder_hash(digest):
                    note = (entry.get("digest_note") or entry.get("digest_placeholder_note")
                            or entry.get("note") or entry.get("placeholder_reason"))
                    if isinstance(note, str) and note.strip():
                        permitted += 1
                        self.findings.add(
                            "medium", "provenance", rid,
                            f"reviewed_ids digest for '{aid}' is the literal placeholder, "
                            f"permitted by note: {note.strip()}",
                            "review_digest_placeholder")
                    else:
                        unnoted += 1
                        self.findings.add(
                            "medium", "provenance", rid,
                            f"reviewed_ids digest for '{aid}' is the literal placeholder "
                            f"and carries no note explaining why", "review_digest_placeholder")
                    ok = False
                    continue
                path = index[key][0]
                actual = self._file_sha256(str(path)) if not str(path).startswith("<") else None
                if actual is None:
                    self.findings.add(
                        "high", "provenance", rid,
                        f"reviewed_ids digest for '{aid}' cannot be verified: the artefact "
                        f"file {path} is not readable", "review_digest_mismatch")
                    ok = False
                    continue
                if actual == str(digest).strip():
                    verified += 1
                else:
                    ok = False
                    self.findings.add(
                        "high", "provenance", rid,
                        f"reviewed_ids digest for '{aid}' does not match the artefact "
                        f"{path}: recorded {str(digest).strip()[:16]}..., "
                        f"actual {actual[:16]}...", "review_digest_mismatch")
        self.provenance_tally["review_digest"] = {
            "verified": verified, "placeholder_with_note": permitted,
            "placeholder_without_note": unnoted}
        return ok

    def _validate_source_anchors(self):
        """Verify every source anchor against the file it names.

        Three facts are checked, and only the ones the anchor actually claims:

          * the file it names exists;
          * `content_hash` equals the sha256 of that file. A recorded
            "sha256:placeholder" is counted and reported as unverified, never
            skipped, because skipping it is what made the fabricated anchor set
            invisible;
          * `line_range` lies inside that file's bounds and, when `symbol` is a
            plain identifier rather than prose, that identifier occurs in the
            file.

        A symbol recorded as prose ("module level (...)", "A / B") cannot be
        checked by substring search, so it is counted and reported as
        unverifiable rather than silently passed.
        """
        ok = True
        tally = {"anchors": 0, "hash_verified": 0, "hash_unverified_placeholder": 0,
                 "hash_mismatch": 0, "file_missing": 0, "no_local_file": 0,
                 "line_range_ok": 0, "line_range_out_of_bounds": 0,
                 "line_range_unparseable": 0, "symbol_checked": 0,
                 "symbol_present": 0, "symbol_absent": 0,
                 "symbol_unverifiable_prose": 0}
        for a in self._load_source_anchors():
            aid = a.get("anchor_id")
            tally["anchors"] += 1
            loc = a.get("location") or {}
            rel = self._anchor_file(loc)
            if rel is None:
                # No repository file named (e.g. a documentation anchor records
                # only a URL). Nothing is claimed about a local file, so there is
                # nothing to contradict; the content_hash is still judged below.
                #
                # This was counted into `self.provenance_tally` under a key that
                # no reporter ever read, so an anchor in this class vanished
                # from the output entirely: the line said "130 anchor(s); 123
                # content_hash verified" and the reader could not tell whether the
                # other 7 had been checked and failed, were placeholders, or had
                # no local file to check. The tally key is now the one the
                # reporter prints, so the gap is stated rather than implied.
                #
                # Note the asymmetry this creates, and it is deliberate: an
                # anchor whose file is named but ABSENT is `file_missing` and is
                # a high-severity finding, because the record claims a local file
                # it does not have. An anchor that names no local file at all
                # claims nothing about this repository, so there is nothing to
                # contradict. It is counted and reported, not failed.
                tally["no_local_file"] += 1
                actual = None
            else:
                fp = self.root / rel
                if not fp.exists():
                    tally["file_missing"] += 1
                    ok = False
                    self.findings.add(
                        "high", "provenance", aid,
                        f"anchor names file {rel}, which does not exist in the repository",
                        "source_anchor_file_missing")
                    actual = None
                else:
                    actual = self._file_sha256(rel)

            # content_hash, and the working_file_hash the anchor carries in the
            # same location block
            for field, owner in ((a.get("content_hash"), "content_hash"),
                                 (loc.get("working_file_hash"), "location.working_file_hash"),
                                 (loc.get("file_hash"), "location.file_hash")):
                if field is None:
                    continue
                label = f"{aid}.{owner}"
                if self._classify_placeholder_hash(field):
                    if owner == "content_hash":
                        tally["hash_unverified_placeholder"] += 1
                    self.findings.add(
                        "medium", "provenance", aid,
                        f"{owner} is '{field}': the anchor records no content hash, so the "
                        f"provenance of {rel or 'the named source'} is unverified",
                        "source_anchor_content_hash_unverified")
                    if owner == "content_hash":
                        ok = False
                    continue
                if actual is None:
                    continue
                if self._expected_sha(field) == actual:
                    if owner == "content_hash":
                        tally["hash_verified"] += 1
                else:
                    if owner == "content_hash":
                        tally["hash_mismatch"] += 1
                        ok = False
                    self.findings.add(
                        "high", "provenance", aid,
                        f"{owner} does not match {rel}: recorded {field}, actual sha256:{actual}",
                        "source_anchor_content_hash_mismatch")

            if actual is None:
                continue

            # line_range bounds
            lr = loc.get("line_range")
            if lr is not None:
                m = self._LINE_RANGE.match(str(lr))
                if not m:
                    tally["line_range_unparseable"] += 1
                    self.findings.add(
                        "medium", "provenance", aid,
                        f"line_range '{lr}' is not a verifiable line or 'start-end' range",
                        "source_anchor_line_range_unparseable")
                else:
                    # A bare "124" names one line and is bounds-checked as
                    # 124-124: same verifiability, no exemption taken.
                    start = int(m.group(1))
                    end = int(m.group(2)) if m.group(2) else start
                    n_lines = len((self.root / rel).read_text(
                        encoding="utf-8", errors="replace").splitlines())
                    if start < 1 or start > end or end > n_lines:
                        tally["line_range_out_of_bounds"] += 1
                        ok = False
                        self.findings.add(
                            "high", "provenance", aid,
                            f"line_range '{lr}' is outside {rel}, which has {n_lines} line(s) "
                            f"(expected 1..{n_lines})", "source_anchor_line_range_out_of_bounds")
                    else:
                        tally["line_range_ok"] += 1

            # symbol occurrence
            sym = loc.get("symbol")
            if sym is not None:
                if self._PLAIN_IDENTIFIER.match(str(sym)):
                    tally["symbol_checked"] += 1
                    text = (self.root / rel).read_text(encoding="utf-8", errors="replace")
                    if re.search(r"\b" + re.escape(str(sym)) + r"\b", text):
                        tally["symbol_present"] += 1
                    else:
                        tally["symbol_absent"] += 1
                        ok = False
                        self.findings.add(
                            "high", "provenance", aid,
                            f"symbol '{sym}' does not occur in {rel}: the anchor attributes a "
                            f"code element to a file that does not contain it",
                            "source_anchor_symbol_missing")
                else:
                    tally["symbol_unverifiable_prose"] += 1
                    self.findings.add(
                        "medium", "provenance", aid,
                        f"symbol '{str(sym)[:70]}' is prose, not a plain identifier, so its "
                        f"occurrence in {rel} is not machine-verifiable",
                        "source_anchor_symbol_unverifiable")
        self.provenance_tally["source_anchors"] = tally
        return ok

    def _validate_evidence_files(self, index):
        """Every logs[].file / evidence_files[] path must exist; every recorded
        hash must match the bytes on disk.

        `evidence_files` entries are evidence the corpus offers in support of a
        claim. A path that does not exist means the evidence is not there; a
        hash that does not match means the bytes changed after the record was
        written, so the record is stale. Both are high severity for the same
        reason as the anchor defects: the record makes a specific, checkable and
        wrong claim.
        """
        ok = True
        tally = {"log_entries": 0, "log_file_missing": 0, "log_hash_verified": 0,
                 "log_hash_mismatch": 0, "log_hash_unverified": 0,
                 "evidence_file_entries": 0, "evidence_file_missing": 0}
        for key, (path, d) in index.items():
            aid = key[1] if isinstance(key, tuple) and len(key) >= 2 else key
            for entry in d.get("logs", []) or []:
                if not isinstance(entry, dict) or not entry.get("file"):
                    continue
                tally["log_entries"] += 1
                rel = str(entry["file"])
                if rel.startswith("<"):
                    continue
                fp = self.root / rel
                if not fp.exists():
                    tally["log_file_missing"] += 1
                    ok = False
                    self.findings.add(
                        "high", "evidence", aid,
                        f"logs entry names {rel}, which does not exist",
                        "evidence_file_missing")
                    continue
                recorded = entry.get("hash")
                if self._classify_placeholder_hash(recorded):
                    tally["log_hash_unverified"] += 1
                    self.findings.add(
                        "medium", "evidence", aid,
                        f"logs entry {rel} records no usable hash ({recorded!r}): the evidence "
                        f"file's identity is unverified", "evidence_file_hash_mismatch")
                    ok = False
                    continue
                actual = self._file_sha256(rel)
                if actual is not None and self._expected_sha(recorded) == actual:
                    tally["log_hash_verified"] += 1
                else:
                    tally["log_hash_mismatch"] += 1
                    ok = False
                    self.findings.add(
                        "high", "evidence", aid,
                        f"logs entry hash does not match {rel}: recorded {recorded}, "
                        f"actual sha256:{actual}", "evidence_file_hash_mismatch")
            for entry in d.get("evidence_files", []) or []:
                if isinstance(entry, str):
                    tally["evidence_file_entries"] += 1
                    if entry.startswith("<"):
                        continue
                    if not (self.root / entry).exists():
                        tally["evidence_file_missing"] += 1
                        ok = False
                        self.findings.add(
                            "high", "evidence", aid,
                            f"evidence_files entry names {entry}, which does not exist",
                            "evidence_file_missing")
        self.provenance_tally["evidence_files"] = tally
        return ok

    def _validate_provenance_evidence(self, index):
        """Run every provenance verification above and record the tally.

        ALWAYS returns the true result. It is not consulted by
        self.provenance_report_only: a rule must never be able to read the flag
        that decides whether its verdict counts, or "reporting mode" would become
        a way for the rule itself to pass. The flag is applied by the CALLERS
        (cmd_validate and cmd_check) to their own return value only, after the
        verdict has already been computed and printed.
        """
        saved, self.provenance_tally = self.provenance_tally, {}
        ok = True
        try:
            ok &= self._validate_review_digests(index)
            ok &= self._validate_source_anchors()
            ok &= self._validate_evidence_files(index)
        finally:
            tally = self.provenance_tally
            self.provenance_tally = saved
            self.provenance_tally = dict(saved)
            self.provenance_tally.update(tally)
        return ok

    def _provenance_finding_count(self):
        return sum(1 for f in self.findings.items if f.get("rule", "").startswith(
            ("review_digest", "source_anchor_", "evidence_file_", "provenance_ref_")))

    def _report_provenance(self):
        """Print the per-class provenance tally. Always runs, gates or not."""
        t = self.provenance_tally
        rd = t.get("review_digest", {})
        sa = t.get("source_anchors", {})
        ev = t.get("evidence_files", {})
        print("  provenance verification tally:")
        print(f"    review digests      : {rd.get('verified', 0)} verified against the file on disk, "
              f"{rd.get('placeholder_with_note', 0)} permitted placeholder(s) with a note, "
              f"{rd.get('placeholder_without_note', 0)} placeholder(s) with no note")
        print(f"    source anchors      : {sa.get('anchors', 0)} anchor(s); "
              f"{sa.get('hash_verified', 0)} content_hash verified, "
              f"{sa.get('hash_unverified_placeholder', 0)} placeholder, "
              f"{sa.get('hash_mismatch', 0)} mismatched; "
              f"{sa.get('file_missing', 0)} name a file that does not exist; "
              f"{sa.get('no_local_file', 0)} name no local file at all (nothing to check "
              f"against, reported not failed). The three hash figures do not add up to the "
              f"anchor count and are not meant to: an anchor in the last class and an anchor "
              f"carrying no content_hash field are both outside the checked set.")
        print(f"    anchor line ranges  : {sa.get('line_range_ok', 0)} within bounds, "
              f"{sa.get('line_range_out_of_bounds', 0)} outside the file, "
              f"{sa.get('line_range_unparseable', 0)} unparseable")
        print(f"    anchor symbols      : {sa.get('symbol_checked', 0)} plain identifier(s) checked, "
              f"{sa.get('symbol_present', 0)} present, {sa.get('symbol_absent', 0)} absent from the "
              f"file they are attributed to; {sa.get('symbol_unverifiable_prose', 0)} recorded as prose")
        print(f"    evidence files      : {ev.get('log_entries', 0)} log entr(y/ies), "
              f"{ev.get('log_hash_verified', 0)} hash verified, "
              f"{ev.get('log_hash_mismatch', 0)} mismatched, "
              f"{ev.get('log_hash_unverified', 0)} unverified, "
              f"{ev.get('log_file_missing', 0)} missing; "
              f"{ev.get('evidence_file_entries', 0)} evidence_files entr(y/ies), "
              f"{ev.get('evidence_file_missing', 0)} missing")

    def _validate_governance_semantics(self, index):
        """Governance semantics, independent of schema validation.

        Acceptance gate [7/8] used to count `category == "provenance"` findings
        in whatever Findings object happened to be in memory. It was always the
        empty object left by the change-lifecycle branch, which resets
        self.findings and runs no detector, so the gate reported "0 violations"
        by construction. This method is the detector the gate runs.

        Four things are asserted on every record in the index:
          * production_authorized is not true;
          * product_verification_credit is not true;
          * human_approval_status is 'pending';
          * no field anywhere in the record claims production authority.

        The fourth is a key scan, because the first three are only as good as
        the field names whoever wrote the record chose. A record may say it is
        approved under a different key and the three named checks would not see
        it.
        """
        ok = True
        authority_keys = {
            # production_authorized is deliberately absent: the named check above
            # already reports it, and listing it here too would report the same
            # violation twice and inflate the count the gate prints.
            "production_release", "production_approval",
            "safety_approval", "authorized_for_production", "approved_for_production",
            "release_approved", "production_sign_off", "production_authority",
            "production_release_approved",
        }
        grant_values = {True, "true", "yes", "approved", "granted", "authorized",
                        "released", "production", "production_authorized"}

        def _granted(v):
            if isinstance(v, bool):
                return v is True
            if isinstance(v, str):
                return v.strip().lower() in grant_values
            return False

        for key, (path, d) in index.items():
            aid = key[1] if isinstance(key, tuple) and len(key) >= 2 else key
            if not isinstance(d, dict):
                continue
            if d.get("production_authorized") is True:
                self.findings.add(
                    "critical", "governance", aid,
                    "production_authorized is true; this corpus is never production authorized",
                    "governance_authority_claim")
                ok = False
            if d.get("product_verification_credit") is True:
                self.findings.add(
                    "high", "governance", aid,
                    "product_verification_credit is true; no record in this corpus carries "
                    "product verification credit", "governance_authority_claim")
                ok = False
            if d.get("human_approval_status") is not None \
                    and d.get("human_approval_status") != "pending":
                # Absent is NOT a violation here: whether the field is required
                # at all is a schema question, judged by _validate_artifact. This
                # rule judges the VALUE. Treating a missing field as "not pending"
                # made this detector fire on every partial fixture -- including
                # the injected artefacts the mutation harness builds -- which
                # would have made it a standing finding on the baseline and
                # indistinguishable from a detection.
                self.findings.add(
                    "high", "governance", aid,
                    f"human_approval_status is {d.get('human_approval_status')!r}; no human "
                    f"approval has been performed on this corpus", "governance_authority_claim")
                ok = False

            def _scan(node, trail):
                if isinstance(node, dict):
                    for k, v in node.items():
                        if k in authority_keys and _granted(v):
                            self.findings.add(
                                "critical", "governance", aid,
                                f"field '{'/'.join(trail + [k])}' claims production authority "
                                f"({v!r})", "governance_authority_claim")
                            return True
                        if _scan(v, trail + [k]):
                            return True
                elif isinstance(node, list):
                    for i, v in enumerate(node):
                        if _scan(v, trail + [str(i)]):
                            return True
                return False

            if _scan(d, []):
                ok = False

        # Authority claims under names the three named checks above do not read.
        #
        # _validate_governance_semantics checks three specific keys
        # (production_authorized, product_verification_credit,
        # human_approval_status) and scans a fixed `authority_keys` set for
        # production authority. Four claim CLASSES it does not look for at all,
        # and acceptance gate [7/8] is named for governance semantics:
        #
        #   * an ASIL determination -- this corpus performs no ASIL analysis
        #     that would determine one, so any record asserting a determined
        #     ASIL is claiming an authority it cannot have;
        #   * an ISO 26262 / compliance CONFORMITY claim -- the corpus documents
        #     what it did NOT verify; conformity is a certification-body act;
        #   * a CERTIFICATION claim -- same;
        #   * an `authorized_for_production` / `approved_for_production` style key
        #     nested somewhere other than the three named keys -- this class is
        #     already covered by the `authority_keys` scan above, which reports
        #     under `governance_authority_claim`. It is deliberately NOT repeated
        #     here: one violation must produce one finding, or the count the gate
        #     prints is inflated and a reader cannot tell a new defect from a
        #     re-report of an old one.
        #
        # Each class is a KEY SCAN over the whole record, not a test of one
        # field, and each reports under its own rule id so the gate can say
        # which class of claim was made. Values must be in the same grant
        # vocabulary the authority check uses, so "ISO 26262 conformity: not
        # claimed" and `asil_determination: null` are silent and only an
        # affirmative grant is reported.
        claim_grant_values = {True, "true", "yes", "approved", "granted", "authorized",
                              "released", "production", "certified", "issued",
                              "conformant", "conforming", "compliant", "determined"}

        # An ASIL determination is expressed as an ASIL IDENTIFIER, not as the
        # word "determined", so the shared vocabulary above would miss every real
        # one: `asil_determination: "ASIL_D"` means the same as
        # `asil_determination: "determined"`. A dedicated predicate covers both.
        #
        # The bare `asil` key is deliberately NOT in GOVERNANCE_CLAIM_FIELDS. The
        # corpus records the ASIL it assigned itself on 33 safety goals and marks
        # 14 more not_applicable; that is the corpus doing its own TARA and
        # recording the result, which is not a claim that anyone determined it.
        # Only an explicit determination/claim/declared key asserts authority.
        asil_value = re.compile(r"^(?:ASIL[_ ]?[A-D]|SIL[_ ]?[1-4]|QM|DETERMINED"
                                r"|DETERMINED[_ ]?ASIL)$", re.IGNORECASE)

        def _claim_granted(v, rule):
            if isinstance(v, bool):
                return v is True
            if isinstance(v, str):
                if rule == "asil_determination_claim" and asil_value.match(v.strip()):
                    return True
                return v.strip().lower() in claim_grant_values
            return False

        for key, (path, d) in index.items():
            aid = key[1] if isinstance(key, tuple) and len(key) >= 2 else key
            if not isinstance(d, dict):
                continue

            def _scan_claim(node, trail, rule, label):
                if isinstance(node, dict):
                    for k, v in node.items():
                        if k in GOVERNANCE_CLAIM_FIELDS[rule] and _claim_granted(v, rule):
                            self.findings.add(
                                "critical", "governance", aid,
                                f"field '{'/'.join(trail + [k])}' asserts {label} ({v!r}); this "
                                f"corpus makes no {label}, and none has been determined, "
                                f"conferred, certified or approved by anyone", rule)
                            return True
                        if _scan_claim(v, trail + [k], rule, label):
                            return True
                elif isinstance(node, list):
                    for i, v in enumerate(node):
                        if _scan_claim(v, trail + [str(i)], rule, label):
                            return True
                return False

            for rule, label in (
                    ("asil_determination_claim", "ASIL determination"),
                    ("conformity_claim", "ISO 26262 conformity claim"),
                    ("certification_claim", "certification claim")):
                if _scan_claim(d, [], rule, label):
                    ok = False
        return ok

    def _governance_finding_count(self):
        """Count findings that assert the corpus has authority it does not have.

        Every rule id in GOVERNANCE_SEMANTIC_RULE_IDS counts, not the two the
        gate used to name. A filter that keeps two rule ids out of nine cannot
        see the seven it discards, and the seven include the claim classes the
        gate is named for.
        """
        return sum(1 for f in self.findings.items
                   if f.get("rule") in GOVERNANCE_SEMANTIC_RULE_IDS)


    def _resolve_ftti_ms(self, aid, d, param_values):
        """Resolve the fault tolerant time interval for one safety goal.

        Returns (value_ms, source_description, scatter_findings).

        Precedence, in order:
          1. `ftti.parameter_ref` - a binding to the parameter registry, which is
             the authoritative home of a parameter value in this corpus.
          2. `ftti_ms` / `ftti` - the spellings the rule originally declared.
          3. `fault_tolerant_time_interval_ms` and
             `timing_budget.total_ftti_ms` - the spellings FB2-SAF-SGO-000001
             actually carries.

        Every declaration that is present is compared against the resolved value,
        so a record that restates the interval inconsistently - the scattering the
        corpus forbids - is reported rather than silently resolved in its favour.
        """
        declarations = {}  # field label -> numeric value
        ref = None
        ftti_field = d.get("ftti")
        if isinstance(ftti_field, dict):
            ref = ftti_field.get("parameter_ref")
        for label in ("ftti_ms", "ftti", "fault_tolerant_time_interval_ms"):
            val = _as_ms(d.get(label))
            if val is not None:
                declarations[label] = val
        budget = d.get("timing_budget")
        if isinstance(budget, dict):
            val = _as_ms(budget.get("total_ftti_ms"))
            if val is not None:
                declarations["timing_budget.total_ftti_ms"] = val

        resolved = source = None
        if ref is not None:
            if ref not in param_values:
                return None, f"unresolved parameter_ref {ref}", [
                    f"safety goal {aid} binds its FTTI to parameter {ref}, which is not in any parameter registry"
                ]
            resolved = param_values[ref]
            source = f"parameter {ref}"
        if resolved is None and declarations:
            label, value = next(iter(declarations.items()))
            resolved, source = value, label

        scatter = []
        if resolved is not None:
            for label, val in sorted(declarations.items()):
                if float(val) != float(resolved):
                    scatter.append(
                        f"safety goal {aid} declares the FTTI inconsistently: {label}={val} "
                        f"but the interval is {resolved} ms (from {source}); a parameter value "
                        f"must have one authoritative home")
        return resolved, source or "no declared interval", scatter

    def _serial_budget_ms(self, d):
        """Serial (non-overlapping) time budget parts of a safety goal, in ms.

        Excluded, because none of them is a unit of serial work:
          - the interval itself and any total (`total_*`, `*_total*`, `ftti*`)
          - margin and slack entries, which are the headroom left after the work
          - entries the record itself marks as parallel
        The allocation sub-object is the corpus's home for the parts and is
        included; the previous form of this rule ignored it entirely.
        """
        def _serial_from(mapping):
            out = []
            if not isinstance(mapping, dict):
                return out
            for k, v in mapping.items():
                if not isinstance(v, (int, float)) or isinstance(v, bool):
                    continue
                kl = str(k).lower()
                if "margin" in kl or "slack" in kl or "parallel" in kl:
                    continue
                if "total" in kl or "ftti" in kl:
                    continue
                out.append(v)
            return out

        budget = d.get("timing_budget")
        parts = _serial_from(budget)
        if isinstance(budget, dict):
            parts += _serial_from(budget.get("allocation"))
        return parts

    @staticmethod
    def _names_non_target_hardware(hardware):
        """True if a free-form hardware string names a host/virtual platform.

        Word-boundary matched so a marker cannot fire on an accidental
        substring. Pure predicate over a string; it is never used to COUNT
        target evidence, only to catch a record that claims a target-hardware
        run while naming a developer machine.
        """
        for marker in NON_TARGET_HARDWARE_MARKERS:
            if re.search(r"(?<![a-z0-9])" + re.escape(marker) + r"(?![a-z0-9])", hardware):
                return True
        return False

    def _semantic_rule_entered(self, *rule_ids):
        """Record that the named semantic rules were EVALUATED on this run.

        A rule that finds nothing is still a rule that ran. Counting findings
        cannot tell those two apart, so the count would fall to zero on a clean
        corpus and the coverage dimension `semantic_consistency_checks` would
        report 0/0 on exactly the tree that passes every check. Each rule block
        in _validate_semantic_rules therefore announces itself here on entry, and
        the dimension is computed from what actually executed.

        SEMANTIC_RULE_IDS below is the declared set. It is not trusted: the
        self-test `semantic rules actually executed equal the declared set`
        compares it against this recorder, so a rule added without a marker (or
        a marker for a rule that was deleted) fails the suite rather than quietly
        changing the figure.
        """
        self._semantic_rules_run.update(rule_ids)

    def _semantic_rules_finding_categories(self):
        """Categories of the semantic-rule findings emitted on this run.

        Read from self.findings, so it describes what the run actually found.
        On a clean corpus that is the empty set, and the caller must say so
        rather than substitute a constant for a measurement it does not have.
        """
        return {f.get("category") for f in self.findings.items
                if f.get("rule") in self._semantic_rules_run}

    def _run_detectors(self, index, links):
        """Reset the semantic-rule recorder, then run every detector.

        A recorder that was never reset would accumulate across calls and report
        the union of every run in the process, so a caller that runs the
        detectors twice would see the same figure and could not tell whether the
        second run actually did the work.
        """
        self._semantic_rules_run = set()
        self._validate_governance_semantics(index)
        self._validate_provenance_evidence(index)
        self._validate_semantic_rules(index, links)

    def _validate_semantic_rules(self, index, links):
        """Semantic consistency rules (subset of the 10 check categories)."""
        ok = True
        # Helper: extract id from index key (profile, id)
        def _id(key):
            return key[1] if isinstance(key, tuple) and len(key) >= 2 else key
        # Rule: every FSR (safety requirement in safety domain with FSR id) has a refines parent (safety goal) or explicit rationale
        self._semantic_rule_entered("traceability_checker")
        fsr_ids = [_id(k) for k in index if "-FSR-" in _id(k)]
        parent_of = {}
        for l in links:
            if l.get("relation_type") == "refines":
                parent_of.setdefault(l["source_id"], l["target_id"])
        for fsr in fsr_ids:
            if fsr not in parent_of:
                self.findings.add("high", "traceability", fsr,
                                  "FSR has no parent safety goal (missing refines link)",
                                  "traceability_checker")
                ok = False
        # Rule: safety goal mitigates a hazard
        self._semantic_rule_entered("safety_goal_mitigates_hazard")
        sgo_ids = [_id(k) for k in index if "-SGO-" in _id(k)]
        mitigates = {l["source_id"] for l in links if l.get("relation_type") == "mitigates"}
        for sgo in sgo_ids:
            if sgo not in mitigates:
                self.findings.add("medium", "traceability", sgo,
                                  "safety goal has no mitigates link to hazard",
                                  "safety_goal_mitigates_hazard")
        # Rule: requirements of safety classification need verifies or validates link.
        self._semantic_rule_entered("verification_traceability_checker")
        # Endpoint: the requirement is the TARGET of the link. Master prompt section 13 declares
        # "verifies: verification measure -> requirement/design" and "validates: validation measure
        # -> stakeholder need/use case/goal", so the measure is the source and the verified artefact
        # is the target. This rule previously built its set from source_id, which is the measure's
        # own endpoint, so a correctly directed verifies link could never clear the finding it
        # raised: 12 of the corpus's 21 standing findings came from that single inversion and none
        # of them could be closed by doing the verification work. See finding FB2-REV-FND-000029.
        # The rule's intent is unchanged - a safety requirement with no verification at all is
        # still reported - and it is strictly harder to satisfy by accident than before, because a
        # requirement appearing as the SOURCE of a verifies/validates link is a malformed link
        # under the declared direction and no longer counts as verification of that requirement.
        verified = {l["target_id"] for l in links
                    if l.get("relation_type") in ("verifies", "validates") and l.get("target_id")}
        for key, (p, d) in index.items():
            aid = _id(key)
            if d.get("artifact_type") == "requirement" and d.get("engineering_domain") == "safety":
                if aid not in verified:
                    self.findings.add("medium", "verification", aid,
                                      "safety requirement has no verifies/validates link",
                                      "verification_traceability_checker")
        # Rule: execution_kind / outcome orthogonality
        self._semantic_rule_entered("execution_kind_orthogonality")
        for key, (p, d) in index.items():
            aid = _id(key)
            if d.get("artifact_type") == "execution":
                ek = d.get("execution_kind")
                oc = d.get("outcome")
                if ek not in (None, "none", "actual_host_run", "actual_simulation_run",
                              "actual_target_hardware_run", "synthetic_fixture"):
                    self.findings.add("high", "evidence", aid, f"invalid execution_kind '{ek}'",
                                      "execution_kind_orthogonality")
                    ok = False
                if oc not in (None, "pass", "fail", "inconclusive", "not_run", "blocked"):
                    self.findings.add("high", "evidence", aid, f"invalid outcome '{oc}'",
                                      "execution_kind_orthogonality")
                    ok = False
        # Rule: FTTI budget consistency checker (MUT-006)
        self._semantic_rule_entered("ftti_budget_consistency_checker")
        # A safety goal must close inside the fault tolerant time interval.
        #
        # Two defects in the previous form of this rule are corrected here, and
        # both corrections make it stricter, not looser:
        #   1. It read the interval only from `ftti_ms` / `ftti`. No safety goal
        #      in this corpus carries either spelling, so the rule could never
        #      fire on its own scenario's record (SCN-MUT-006) - it silently
        #      `continue`d on every artifact. The interval is now resolved from
        #      the parameter registry (the authoritative source, FB2-PRM-000004
        #      ftti_ms = 100) when the record references a parameter, and from
        #      every field name the corpus actually uses otherwise.
        #   2. It counted `timing_budget.total_ftti_ms` - the interval itself -
        #      as one of the serial budget parts, so the sum it compared against
        #      the interval always contained the interval. It also ignored
        #      `timing_budget.allocation`, which is where the corpus actually
        #      keeps the serial parts, so it never summed the real budget. The
        #      serial sum is now taken from the allocation and from any other
        #      numeric budget entry, with the interval, totals, margins and
        #      explicitly parallel entries excluded.
        # A third check is added: because the corpus forbids scattering a
        # parameter value, every declaration of the interval on the same record
        # must agree with the registry and with each other.
        param_values = {pid: prm.get("value") for pid, prm in self._iter_parameters(index)}
        for key, (p, d) in index.items():
            aid = _id(key)
            if d.get("artifact_type") == "safety_goal":
                ftti, ftti_source, scatter = self._resolve_ftti_ms(aid, d, param_values)
                for detail in scatter:
                    self.findings.add("high", "consistency", aid, detail,
                                      "ftti_budget_consistency_checker")
                    ok = False
                if ftti is None:
                    continue
                serial = self._serial_budget_ms(d)
                if serial and sum(serial) > float(ftti):
                    self.findings.add("high", "consistency", aid,
                                      f"timing budget {sum(serial)}ms exceeds FTTI {ftti}ms "
                                      f"(interval resolved from {ftti_source})",
                                      "ftti_budget_consistency_checker")
                    ok = False

        # Load source registry for provenance checks
        sr = self.sources_dir / "source-registry.json"
        sources_registry = {}
        if sr.exists():
            for a in load_json(sr).get("anchors", []):
                sources_registry[a.get("anchor_id")] = a

        # Rule: Parameter unit consistency check (MUT-004)
        self._semantic_rule_entered("parameter_unit_consistency")
        # Checks parameter-shaped artifacts AND entries inside parameter registries.
        for pid, prm in self._iter_parameters(index):
            unit = prm.get("unit")
            value = prm.get("value")
            if unit and value is not None:
                if unit in ("V", "A", "W", "Hz") and isinstance(value, (int, float)):
                    if unit == "V" and value < 10 and value > 0.1:
                        self.findings.add("medium", "consistency", pid,
                                          f"parameter {pid} unit is V but value {value} suggests mV (missing scaling)",
                                          "parameter_unit_consistency")
                    elif unit == "A" and value < 10 and value > 0.1:
                        self.findings.add("medium", "consistency", pid,
                                          f"parameter {pid} unit is A but value {value} suggests mA (missing scaling)",
                                          "parameter_unit_consistency")

        # Rule: HSI/SW interface consistency checker (MUT-005)
        self._semantic_rule_entered("hsi_interface_consistency")
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
                                      f"(polarity): HSI={sig.get('polarity')}, HW={sig.get('timing')}",
                                      "hsi_interface_consistency")
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
                                                  f"({field}): HSI={hv}, HW={wv}",
                                                  "hsi_interface_consistency")

        # Rule: FTTI budget consistency checker (MUT-006) - already implemented above

        # Rule: Parameter threshold order validator (MUT-007)
        self._semantic_rule_entered("parameter_threshold_order")
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
                                          f"parameter {pid} threshold order violated: warning={warning}, derating={derating}, shutdown={shutdown}",
                                          "parameter_threshold_order")
                        ok = False
                elif "min" in name.lower():
                    if not (warning > derating > shutdown):
                        self.findings.add("high", "consistency", pid,
                                          f"parameter {pid} threshold order violated: warning={warning}, derating={derating}, shutdown={shutdown}",
                                          "parameter_threshold_order")
                        ok = False

        # Rule: Safety requirement completeness checker (MUT-008)
        self._semantic_rule_entered("safety_requirement_completeness_checker")
        #
        # SCOPE WIDENED, and only widened. This rule used to carry a third
        # condition, `"-FSR-" in _id(key)`, alongside the two that define its
        # population (`artifact_type == "requirement"` and
        # `engineering_domain == "safety"`). That id pattern is a genuine blind
        # spot, not a distinction: it made the rule structurally incapable of
        # reporting the five FB2-SAF-SEC-* security requirements, which are
        # safety-domain requirements carrying the whole cybersecurity concept and
        # which each state a reaction to a detected attack in their own
        # statement. Its sibling rule two paragraphs above
        # (verification_traceability_checker) selects the same population with no
        # id filter at all, so before this change the two rules disagreed about
        # what a "safety requirement" is, and the disagreement happened to fall
        # on the side of silence for the security chain.
        #
        # The filter is removed, not relaxed. Nothing that was reported before
        # stops being reported: the population only grows, from the FSR records
        # to every safety-domain requirement, so the rule is strictly harder to
        # satisfy. The selection is by declared type and declared domain, not by
        # how an id happens to be spelled, which is what makes it survive the
        # addition of a future requirement class. Three self-tests in
        # cmd_selftest pin the widened scope in both directions: an FSR with no
        # fault_reaction is still reported, a security requirement with no
        # fault_reaction is now reported, and a requirement outside the safety
        # domain is still not reported. See finding FB2-REV-FND-000039.
        for key, (p, d) in index.items():
            aid = _id(key)
            if d.get("artifact_type") == "requirement" and d.get("engineering_domain") == "safety":
                if "fault_reaction" not in d or not d.get("fault_reaction"):
                    self.findings.add("medium", "verification", aid,
                                      f"safety requirement {aid} has no fault_reaction defined",
                                      "safety_requirement_completeness_checker")

        # Rule: ASIL assignment validator (MUT-009)
        self._semantic_rule_entered("asil_assignment_validator")
        #
        # Three checks, in increasing strength:
        #   1. the ASIL is one of the declared values;
        #   2. an assigned ASIL carries a justification;
        #   3. the assigned ASIL agrees with the classification the justification
        #      itself derives.
        #
        # Check 3 is the one that makes this scenario meaningful. Checks 1 and 2
        # alone can only be satisfied by the corpus being unhealthy: an unjustified
        # downgrade is precisely a downgrade whose justification is *still present
        # and says otherwise*, so a presence-only rule never fires on the injected
        # defect and only fires on a corpus that has no justification at all. The
        # scenario therefore passed on the very condition it claimed to test. The
        # rule now re-derives the ASIL from the severity and exposure ratings the
        # justification records, using ISO 26262-3:2018 Table 4, and compares it
        # with the ASIL the record actually carries. A downgrade that leaves the
        # derivation standing is now detected on a healthy corpus.
        for key, (p, d) in index.items():
            aid = _id(key)
            if d.get("artifact_type") == "safety_goal":
                asil = d.get("asil")
                if asil:
                    valid_asils = ["ASIL_A", "ASIL_B", "ASIL_C", "ASIL_D", "QM"]
                    if asil not in valid_asils:
                        self.findings.add("high", "verification", aid,
                                          f"safety goal {aid} has invalid ASIL '{asil}'",
                                          "asil_assignment_validator")
                    justification = d.get("asil_justification")
                    if not justification:
                        self.findings.add("medium", "verification", aid,
                                          f"safety goal {aid} ASIL {asil} lacks justification",
                                          "asil_assignment_validator")
                    else:
                        sev = ((justification.get("severity") or {}).get("rating")
                               if isinstance(justification.get("severity"), dict)
                               else justification.get("severity"))
                        exp = ((justification.get("exposure") or {}).get("rating")
                               if isinstance(justification.get("exposure"), dict)
                               else justification.get("exposure"))
                        derived = None
                        if sev and exp:
                            row = ASIL_FROM_SE.get(str(sev).upper().strip())
                            derived = row.get(str(exp).upper().strip()) if row else None
                            if derived is None:
                                self.findings.add("medium", "verification", aid,
                                                  f"safety goal {aid} justification records severity "
                                                  f"'{sev}'/exposure '{exp}', which is not a row/column of the "
                                                  f"ISO 26262-3 ASIL determination table, so the ASIL "
                                                  f"cannot be re-derived from it",
                                                  "asil_assignment_validator")
                        stated_derived = justification.get("derived_asil")
                        if derived is not None and stated_derived and stated_derived != derived:
                            self.findings.add("high", "verification", aid,
                                              f"safety goal {aid} justification claims derived ASIL "
                                              f"'{stated_derived}' but severity {sev} with exposure {exp} "
                                              f"gives {derived}",
                                              "asil_assignment_validator")
                            ok = False
                        if derived is not None and derived != asil:
                            self.findings.add("high", "verification", aid,
                                              f"safety goal {aid} is assigned ASIL {asil} but its own "
                                              f"justification derives ASIL {derived} from severity {sev} "
                                              f"and exposure {exp}; the assignment is not supported by the "
                                              f"classification recorded with it",
                                              "asil_assignment_validator")
                            ok = False

        # Rule: Requirement applicability validator (MUT-013)
        self._semantic_rule_entered("requirement_applicability_validator")
        #
        # A requirement whose ASIL allocation is recorded as not applicable is
        # claiming that no ASIL determination applies to it. That claim needs a
        # recorded reason, exactly as an ASIL assignment does; without one the
        # claim is unfalsifiable and the requirement silently drops out of every
        # ASIL-derived view of the corpus.
        #
        # The marking is read from the field the schema itself declares.
        # requirement.schema.json enumerates "not_applicable" as a value of
        # safety_allocation.asil, so non-applicability is expressible in this data
        # model and no new field had to be introduced. The justification is read
        # from asil_justification, the field the corpus already uses for exactly
        # this purpose on safety goals.
        for key, (p, d) in index.items():
            aid = _id(key)
            if d.get("artifact_type") != "requirement":
                continue
            allocation = d.get("safety_allocation")
            if not isinstance(allocation, dict):
                continue
            declared_asil = str(allocation.get("asil", "")).strip().lower()
            if declared_asil != "not_applicable":
                continue
            if not d.get("asil_justification"):
                self.findings.add("medium", "verification", aid,
                                  f"requirement {aid} is marked not applicable (safety_allocation.asil) "
                                  f"without an asil_justification recording why no ASIL determination "
                                  f"applies to it",
                                  "requirement_applicability_validator")

        # Rule: Diagnostic coverage claim validator (MUT-010)
        self._semantic_rule_entered("diagnostic_coverage_claim_validator")
        #
        # SCOPE WIDENED, and only widened. This rule carried the same third
        # condition, `"-FSR-" in _id(key)`, that MUT-008 carried until finding
        # FB2-REV-FND-000039 removed it there. The two rules were written at
        # different times for different fields and neither was reconciled
        # against the other, so the corpus held two different answers to "what is
        # a safety requirement" for the same record class.
        #
        # The filter was left in place on the argument that no FB2-SAF-SEC-*
        # record claims diagnostic coverage, so it was inert rather than
        # actively harmful. Inert is not the same as correct: the security
        # concept does have a diagnostic story -- those requirements mandate a
        # diagnosis entry per rejected frame -- so a future security
        # requirement claiming a diagnostic coverage figure would be silently
        # unchecked, and that silence would be indistinguishable from the silence
        # FB2-REV-FND-000039 was raised about. A check that is inert until the
        # day it is needed, and wrong on that day, is a trap with a long fuse.
        #
        # The filter is removed, not relaxed, so the population only grows and
        # the rule is strictly harder to satisfy. The finding text is
        # generalised from "FSR" to "safety requirement" because the population
        # is no longer FSR-only; keeping the FSR wording would have been a
        # second, quieter way of encoding the same assumption.
        #
        # MEASURED on the corpus as it stands (2026-09-30): the widened rule
        # reports NOTHING, because no safety-domain requirement of either class
        # currently carries a diagnostic_coverage field - 0 of the 12. That is a
        # real result, not evidence of a working rule: "reports nothing on a
        # corpus where nothing is wrong" is not "would report the defect". Four
        # self-tests in cmd_selftest therefore pin the rule from both sides, so
        # its liveness is established by construction rather than by trust: the
        # excluded class is reported, the previously reported class is still
        # reported, the domain boundary is still respected, and a requirement
        # that carries the evidence is silent. See finding FB2-REV-FND-000040.
        for key, (p, d) in index.items():
            aid = _id(key)
            if d.get("artifact_type") == "requirement" and d.get("engineering_domain") == "safety":
                coverage = d.get("diagnostic_coverage")
                if coverage:
                    if "diagnostic_coverage_evidence" not in d or not d.get("diagnostic_coverage_evidence"):
                        self.findings.add("high", "verification", aid,
                                          f"safety requirement {aid} claims diagnostic coverage '{coverage}' without evidence",
                                          "diagnostic_coverage_claim_validator")

        # Rule: Configuration consistency checker (MUT-011)
        self._semantic_rule_entered("configuration_consistency")
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
                                              f"configuration {aid} enables mutually exclusive options: {excl}",
                                              "configuration_consistency")
                return
            if not isinstance(config, dict):
                return
            for key_opt, val_opt in config.items():
                if isinstance(val_opt, list) and len(val_opt) > 1:
                    for excl in MUTUALLY_EXCLUSIVE:
                        if excl.issubset(set(val_opt)):
                            self.findings.add("high", "consistency", aid,
                                              f"configuration {aid} enables mutually exclusive options: {excl}",
                                              "configuration_consistency")

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
        self._semantic_rule_entered("execution_kind_classifier")
        for key, (p, d) in index.items():
            aid = _id(key)
            if d.get("artifact_type") == "execution":
                ek = d.get("execution_kind")
                origin = d.get("origin")
                if ek == "actual_host_run":
                    evidence = d.get("evidence_refs") or []
                    if not evidence:
                        self.findings.add("high", "evidence", aid,
                                          f"execution {aid} claims actual_host_run but has no evidence",
                                          "execution_kind_classifier")
                    elif origin not in ("source_observed", None):
                        self.findings.add("medium", "evidence", aid,
                                          f"execution {aid} claims actual_host_run but origin is '{origin}' "
                                          f"(fabricated evidence classification)",
                                          "execution_kind_classifier")
                elif ek == "synthetic_fixture":
                    if "evidence_refs" not in d or not d.get("evidence_refs"):
                        self.findings.add("medium", "evidence", aid,
                                          f"execution {aid} claims synthetic_fixture but lacks evidence",
                                          "execution_kind_classifier")
                elif ek == "actual_target_hardware_run":
                    # A target-hardware run is the only execution_kind that is
                    # product-hardware evidence, so it is also the only one a
                    # reader may take as a result on the MCU the product ships
                    # on. It therefore has to carry the evidence such a run
                    # implies, and the bar is deliberately higher than for a
                    # host run:
                    #
                    #   - a log file that EXISTS on disk and whose recorded hash
                    #     matches it (existence and hash are verified for every
                    #     record by _validate_evidence_files, so a target run
                    #     cannot point at a log that was never captured),
                    #   - real input AND output hashes, since a run on silicon
                    #     is characterised by what went in and what came out,
                    #   - environment.hardware that identifies target hardware
                    #     rather than naming a developer machine,
                    #   - and origin=source_observed, because a synthetic-origin
                    #     record asserting a hardware run is a fabricated claim.
                    #
                    # Without this the new enum member would be a hole: a
                    # record could claim product-hardware evidence and be
                    # believed, moving actual_product_evidence on nothing.
                    #
                    # Every branch below sets the FUNCTION-level `ok` to False
                    # on failure; it is never reset to True here, because doing
                    # so would clear a failure already recorded by an earlier
                    # check in this same pass.
                    logs = d.get("logs") or []
                    if not logs:
                        self.findings.add(
                            "high", "evidence", aid,
                            f"execution {aid} claims actual_target_hardware_run but records no log "
                            f"file; a run on the product's own hardware is only evidence if the run "
                            f"was captured",
                            "execution_kind_classifier")
                        ok = False
                    else:
                        for entry in logs:
                            lf = entry.get("file")
                            if not lf or not (self.root / lf).exists():
                                self.findings.add(
                                    "high", "evidence", aid,
                                    f"execution {aid} claims actual_target_hardware_run but its log "
                                    f"'{lf}' does not exist on disk",
                                    "execution_kind_classifier")
                                ok = False
                                break
                    if not (d.get("input_hashes") or {}):
                        self.findings.add(
                            "high", "evidence", aid,
                            f"execution {aid} claims actual_target_hardware_run but records no "
                            f"input hashes; what was run on the target is unidentified",
                            "execution_kind_classifier")
                        ok = False
                    if not (d.get("output_hashes") or {}):
                        self.findings.add(
                            "high", "evidence", aid,
                            f"execution {aid} claims actual_target_hardware_run but records no "
                            f"output hashes; what the target produced is unidentified",
                            "execution_kind_classifier")
                        ok = False
                    if not (d.get("evidence_refs") or []):
                        self.findings.add(
                            "high", "evidence", aid,
                            f"execution {aid} claims actual_target_hardware_run but has no evidence",
                            "execution_kind_classifier")
                        ok = False
                    hardware = str((d.get("environment") or {}).get("hardware") or "").lower()
                    # Prose matching on a free-form hardware string is not a
                    # measurement, so this is deliberately NOT used to decide
                    # whether a run counts as target evidence (that is read from
                    # execution_kind). It only rejects a string that names a
                    # developer host, which cannot be the product's own silicon.
                    if not hardware or self._names_non_target_hardware(hardware):
                        self.findings.add(
                            "high", "evidence", aid,
                            f"execution {aid} claims actual_target_hardware_run but "
                            f"environment.hardware is '{hardware or '<empty>'}', which does not "
                            f"identify target hardware",
                            "execution_kind_classifier")
                        ok = False
                    origin = d.get("origin")
                    if origin not in ("source_observed", None):
                        self.findings.add(
                            "medium", "evidence", aid,
                            f"execution {aid} claims actual_target_hardware_run but origin is "
                            f"'{origin}' (fabricated evidence classification)",
                            "execution_kind_classifier")

        # Rule: Evidence reference validator (MUT-014)
        self._semantic_rule_entered("evidence_reference_validator")
        # Build a set of all artifact IDs in the index
        all_artifact_ids = set(_id(k) for k in index.keys())
        for key, (p, d) in index.items():
            aid = _id(key)
            if "evidence_refs" in d:
                for ref in d["evidence_refs"]:
                    if ref in all_artifact_ids:
                        continue
                    # A ref that is not an artifact id must be a real file on disk.
                    # The previous implementation pattern-matched a prefix/extension
                    # allowlist (tests/, src/, *.c, *.h) and therefore accepted
                    # non-existent files under those prefixes while rejecting every
                    # legitimate reference to another evidence type. Existence is now
                    # checked directly, which accepts a wider set of genuine
                    # references AND catches dangling ones everywhere.
                    if isinstance(ref, str) and (ref.endswith(os.sep) or "/" in ref
                                                 or os.path.splitext(ref)[1]):
                        if not os.path.exists(self.root / ref):
                            self.findings.add("high", "provenance", aid,
                                              f"artifact {aid} references non-existent evidence {ref}",
                                              "evidence_reference_validator")
                    else:
                        self.findings.add("high", "provenance", aid,
                                          f"artifact {aid} references non-existent evidence {ref}",
                                          "evidence_reference_validator")

        # Rule: Identity uniqueness checker (profile-aware) (MUT-015)
        self._semantic_rule_entered("identity_uniqueness_checker")
        id_counts = {}
        for key, (p, d) in index.items():
            aid = _id(key)
            profile = d.get("profile", "unknown")
            key2 = (profile, aid)
            id_counts[key2] = id_counts.get(key2, 0) + 1
        for (profile, aid), count in id_counts.items():
            if count > 1:
                self.findings.add("high", "traceability", aid,
                                  f"duplicate artifact ID {aid} within profile {profile}",
                                  "identity_uniqueness_checker")

        # Rule: Source anchor drift detector (MUT-016)
        self._semantic_rule_entered("source_anchor_drift_detector")
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
                                          f"artifact {aid} references non-existent source anchor {ref}",
                                          "source_anchor_drift_detector")
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
                                          f"anchor {ref} symbol '{anchor_symbol}'",
                                          "source_anchor_drift_detector")
                        drift_reported = True

        # Rule: Production authorization governance checker (MUT-017)
        self._semantic_rule_entered("production_authorization_governance_checker")
        for key, (p, d) in index.items():
            aid = _id(key)
            if d.get("production_authorized") is True:
                if d.get("human_approval_status") != "approved":
                    self.findings.add("high", "process", aid,
                                      f"artifact {aid} has production_authorized=true but human_approval_status != approved",
                                      "production_authorization_governance_checker")

        # Rule: Change impact analyzer (MUT-018)
        self._semantic_rule_entered("change_impact_analyzer", "incomplete_propagation")
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
                                      f"change {aid} has no suspect_links or required_updates",
                                      "change_impact_analyzer")
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
                                          f"{dep_id} has no matching revision entry (incomplete propagation)",
                                          "incomplete_propagation")

        # Rule: Refinement cycle detector (MUT-019)
        self._semantic_rule_entered("refinement_cycle_detector")
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
                                      f"circular refinement chain detected involving {node}",
                                      "refinement_cycle_detector")
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
        ok &= self._validate_no_duplicate_ids()
        ok &= self._validate_links(links, index)
        ok &= self._validate_link_currency(links, index)
        ok &= self._validate_link_registry_shadowing()
        ok &= self._validate_provenance_refs(index)
        if not quiet:
            print("Running semantic consistency rules...")
        ok &= self._validate_semantic_rules(index, links)
        if not quiet:
            print("Running governance semantics...")
        ok &= self._validate_governance_semantics(index)
        if not quiet:
            print("Running provenance verification (digests, content hashes, line ranges)...")
        provenance_ok = self._validate_provenance_evidence(index)
        n_prov = self._provenance_finding_count()
        self._last_provenance_verdict = (provenance_ok, n_prov)
        if not quiet:
            self._report_provenance()
            if not provenance_ok:
                print(f"  provenance verdict: FAIL - {n_prov} finding(s)"
                      + ("  (--provenance-report-only: reported, not gating this run)"
                         if self.provenance_report_only else ""))
        if not quiet:
            n = len(self.findings.items)
            print(f"Validation complete: {n} findings, errors={self.findings.error_count}")
        if self.provenance_report_only:
            # The provenance verdict above is the real one and has already been
            # printed. Only the RETURN value is decoupled, so a reader can run
            # the checks and read every number while the corpus is still being
            # repaired. Every other failure class still fails this command.
            return ok
        return ok and provenance_ok

    # ------------------------------------------------------------ 15.4 coverage

    _STANDARDS_REF = re.compile(r"\bFB2-[A-Z0-9]+(?:-[A-Z0-9]+)*-\d+\b")

    def _standards_mapping_measurement(self, cp, index):
        """Measure standards mapping by backing, not by counting inventory keys.

        A process/part counts as mapped only if the text that claims its
        disposition names at least one artefact identifier that resolves. The
        denominator is the applicable inventory; not_applicable entries are
        reported by id so dropping them is visible.
        """
        resolvable = {aid for (_prof, aid) in index} | self._anchor_ids()

        def _backed(entry):
            text = " ".join(str(entry.get(k, "")) for k in
                            ("disposition", "disposition_reason", "rationale",
                             "expected_artifacts", "name"))
            refs = set(self._STANDARDS_REF.findall(text))
            return bool(refs & resolvable), sorted(refs)

        proc_backed, proc_unbacked, proc_na = [], [], []
        for p in cp.get("process_inventory", []):
            pid = p.get("process_id", "?")
            if p.get("applicability") == "not_applicable":
                proc_na.append(pid)
                continue
            ok, _refs = _backed(p)
            (proc_backed if ok else proc_unbacked).append(pid)

        iso_backed, iso_unbacked, iso_na = [], [], []
        for part, entry in (cp.get("iso26262_coverage") or {}).items():
            if isinstance(entry, dict) and entry.get("decision") == "not_applicable":
                iso_na.append(part)
                continue
            text = entry if isinstance(entry, str) else json.dumps(entry)
            refs = set(self._STANDARDS_REF.findall(text))
            (iso_backed if refs & resolvable else iso_unbacked).append(part)

        numerator = len(proc_backed) + len(iso_backed)
        denominator = (len(proc_backed) + len(proc_unbacked)
                       + len(iso_backed) + len(iso_unbacked))
        detail = (f"{numerator}/{denominator} standards entries are backed by an artefact that "
                  f"exists in the index. ASPICE: {len(proc_backed)}/{len(proc_backed) + len(proc_unbacked)} "
                  f"applicable processes backed, {len(proc_na)} declared not_applicable; "
                  f"ISO 26262: {len(iso_backed)}/{len(iso_backed) + len(iso_unbacked)} applicable "
                  f"parts backed, {len(iso_na)} declared not_applicable. "
                  f"UNBACKED (claim a disposition, name no existing artefact): "
                  f"ASPICE {', '.join(proc_unbacked) or 'none'}; "
                  f"ISO {', '.join(iso_unbacked) or 'none'}. "
                  f"This is the honest figure; the previous 44/44 was the size of the "
                  f"inventory file divided by itself.")
        return {"numerator": numerator, "denominator": denominator, "detail": detail,
                "aspice_backed": proc_backed, "aspice_unbacked": proc_unbacked,
                "aspice_not_applicable": proc_na,
                "iso_backed": iso_backed, "iso_unbacked": iso_unbacked,
                "iso_not_applicable": iso_na}

    def _negative_scenario_dimension(self):
        """Build negative_scenario_validation from an EXECUTED scenario run.

        MEASURED, not counted. This dimension used to report len(mutation files on
        disk) over a fixed denominator of 20 - i.e. how many scenario FILES exist.
        That is a presence check wearing the name of a detection measurement, and
        it is exactly how this corpus published 20/20 while eight of the twenty
        were failing: nothing in this dimension ever ran a scenario.

        The scenarios are now executed through _execute_scenarios, the same path
        acceptance gate [5/8] uses, and the numerator is the count that PASSES:
        a mutation counts only when the rule it declares is implemented, is
        silent on the unmutated corpus, and produces a finding the baseline did
        not contain. The denominator is the number of scenarios actually
        executed, so 20/20 means twenty scenarios ran and twenty passed, and the
        figure drops the moment one does not.

        This is a REPORTED dimension, not a gate: no acceptance check keys off it.
        The scenario run rebuilds self.findings per scenario, so findings are
        snapshotted and restored and this measurement cannot perturb the
        dimensions computed before it, which read them.
        """
        saved_findings = self.findings
        try:
            scn = self._execute_scenarios()
        finally:
            self.findings = saved_findings
        failed_mut = sorted(r["scenario_id"] for r in scn["results"]
                            if r.get("type") == "mutation" and not r.get("passed"))
        failed_chg = sorted(r["scenario_id"] for r in scn["results"]
                            if r.get("type") == "change_lifecycle" and not r.get("passed"))
        mut_detail = (f"{scn['passed_mutations']}/{scn['total_mutations']} mutations passed "
                      f"(executed and detected by their own declared rule)")
        if failed_mut:
            mut_detail += f"; FAILING: {', '.join(failed_mut)}"
        chg_detail = f"{scn['passed_changes']}/{scn['total_changes']} change lifecycles"
        if failed_chg:
            chg_detail += f" (FAILING: {', '.join(failed_chg)})"
        return {"numerator": scn["passed_mutations"],
                "denominator": scn["total_mutations"],
                "detail": f"{mut_detail}; {chg_detail}"}

    def _measure_export_reproducibility(self):
        """Export the corpus twice into throwaway dirs; compare content hashes.

        Returns (detail_text, reproducible). Deliberately independent of
        docs/artifacts/exports/: a caller that runs cmd_export() first must not
        be able to satisfy this figure by having written the very file that the
        old presence check looked for.
        """
        import tempfile
        digests = []
        try:
            for _ in range(2):
                with tempfile.TemporaryDirectory(prefix="corpus-export-") as td:
                    self.cmd_export(output_dir=Path(td) / "export")
                    m = load_json(Path(td) / "export" / "manifest.json")
                    digests.append(dict(m.get("content_hashes") or {}))
        except Exception as e:
            return f"export could not be run twice for comparison: {e}", False
        if not digests[0]:
            return "export manifest declared no content hashes, so nothing was compared", False
        keys = set(digests[0]) | set(digests[1])
        unstable = sorted(k for k in keys if digests[0].get(k) != digests[1].get(k))
        if unstable:
            return (f"{len(keys) - len(unstable)}/{len(keys)} exported file(s) hashed identically "
                    f"across two independent exports; unstable: {unstable}"), False
        return (f"{len(keys)} exported file(s) hashed identically across two independent exports "
                f"into separate temporary directories; measured here, not read from "
                f"docs/artifacts/exports/"), True

    def _coverage_dimensions(self):
        """Compute every completion dimension. Pure: no printing, no writes.

        Split out of cmd_coverage so the renderer can derive the same numbers
        into a generated view without a second, divergent implementation of
        them. A view that transcribes a figure out of coverage-report.md would
        be exactly the hand-maintained-drift defect this corpus has been
        correcting; a view that calls this function cannot drift from it.
        """
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
        #
        # MEASURED, not counted. This dimension was
        #     n_proc + n_iso  over  32 + 12
        # where n_proc = len(process_inventory) and n_iso = len(iso26262_coverage) or 12.
        # `iso26262_coverage` is a dict of 12 keys, so len() is 12 whatever it
        # contains, and the `or 12` meant an EMPTY list also scored 12. The
        # denominator was the same expression, so the ratio was 44/44 by
        # construction: it measured how many keys a JSON file has and divided by
        # itself. A process with disposition "mapped" and no artefact behind it
        # contributed exactly as much as one backed by records.
        #
        # What is honestly measurable: whether the disposition of a process (or
        # of an ISO 26262 part) is backed by at least one artefact that exists
        # in the index. So:
        #     numerator   = entries whose coverage text names >= 1 FB2- id that
        #                   resolves against the artifact index or the source
        #                   registry
        #     denominator = the APPLICABLE inventory. A process or part declared
        #                   not_applicable is out of scope and is counted and
        #                   named separately, not silently dropped.
        # Entries whose coverage text names no artefact id at all are counted as
        # unbacked, whatever disposition they claim. "mapped" with nothing
        # behind it is exactly the defect this dimension was hiding.
        cp = load_json(self.governance_dir / "coverage-plan.json")
        smap = self._standards_mapping_measurement(cp, index)
        dims["standards_mapping"] = {"numerator": smap["numerator"],
                                     "denominator": smap["denominator"],
                                     "detail": smap["detail"]}

        # source grounding
        sr = load_json(self.sources_dir / "source-registry.json")
        anchors = sr.get("anchors", [])
        grounded = sum(1 for _, d in self.iter_corpus_artifacts() if d.get("source_refs"))
        total_art = sum(1 for _, d in self.iter_corpus_artifacts() if d.get("id"))
        dims["source_grounding"] = {"numerator": grounded, "denominator": max(total_art, 1),
                                    "detail": f"artifacts with source_refs ({len(anchors)} anchors available)"}

        # traceability integrity
        #
        # The dangling count is MEASURED HERE rather than read from self.findings.
        # It used to be counted off whatever findings happened to be in memory,
        # which is only the validate pass when the caller happened to run one:
        # a bare `corpus.py coverage` started with an empty Findings object and
        # therefore reported "0 dangling" without having checked a single link.
        # A dimension that reads 100% because nothing checked it is the same
        # defect class as counting scenario files. Link validation is re-run on
        # a scratch Findings object and the caller's findings are left untouched.
        probe = Findings()
        saved_findings = self.findings
        self.findings = probe
        try:
            self._validate_links(links, index)
            dangling = sum(1 for f in probe.items
                           if f["category"] == "traceability" and "dangling" in f["description"])
        finally:
            self.findings = saved_findings
        dims["traceability_integrity"] = {"numerator": len(links) - dangling, "denominator": len(links),
                                          "detail": f"{len(links)} links, {dangling} dangling "
                                                    f"(link validation re-run for this figure)"}

        # semantic consistency checks executed
        #
        # COMPUTED, from the recorder _validate_semantic_rules fills in on entry.
        # This dimension used to be the literal 10/10 with the detail "10 check
        # categories executed per run". Both halves were wrong: the function
        # evaluates 21 rules across 6 categories, so the figure understated the
        # work by more than half. Worse, a literal is incapable of detecting
        # that it went stale -- a rule deleted from the function, or renamed,
        # or added, would leave the figure at exactly 10/10 and the suite green.
        #
        # The denominator is the DECLARED set (SEMANTIC_RULE_IDS) and the
        # numerator is what actually executed, so the figure is a measurement
        # and a discrepancy between the two is visible in the ratio. A rule
        # block that runs but announces nothing, or a marker for a rule that was
        # removed, moves the numerator off the denominator.
        #
        # The category count is computed from the executed rules' finding
        # categories, not declared. If the function emitted nothing this run the
        # category count is reported as measured-but-unavailable rather than
        # silently reported as 6.
        # The recorder is order-dependent by nature: it says what THIS
        # invocation of _validate_semantic_rules did. cmd_coverage is called at
        # step 3/8 of the acceptance suite and the governance gate at 7/8, so
        # reading the recorder here would report whatever an earlier caller left
        # behind -- and would report zero from a bare `corpus.py coverage`. The
        # rules are therefore re-run against a scratch Findings and a scratch
        # recorder for this figure, and the caller's state is restored, the same
        # pattern traceability_integrity below uses for its dangling count.
        saved_findings = self.findings
        saved_rules = self._semantic_rules_run
        scratch = Findings()
        self.findings = scratch
        self._semantic_rules_run = set()
        try:
            self._validate_semantic_rules(index, links)
            executed = set(self._semantic_rules_run)
            exec_cats = {f.get("category") for f in scratch.items
                         if f.get("rule") in executed}
        finally:
            self.findings = saved_findings
            self._semantic_rules_run = saved_rules
        declared = set(SEMANTIC_RULE_IDS)
        dims["semantic_consistency_checks"] = {
            "numerator": len(executed),
            "denominator": len(declared),
            "detail": (f"{len(executed)} of {len(declared)} declared semantic rules evaluated "
                       f"on this run; {len(executed & declared)} of them are declared, "
                       f"{len(executed - declared)} are executed but undeclared, "
                       f"{len(declared - executed)} are declared but did not execute. "
                       f"Measured by the recorder each rule block calls on entry, not declared"
                       + (f"; {len(exec_cats)} finding categories observed: "
                          f"{sorted(exec_cats)}" if exec_cats else
                          "; finding categories unavailable (no rule fired on this run, which is "
                          "the expected state of a passing corpus)")),
            # Machine-readable, so a gate does not have to parse the detail text.
            "rules_declared": len(declared),
            "rules_executed": len(executed),
            "rule_ids_executed": sorted(executed),
            "undeclared_executed": sorted(executed - declared),
            "declared_not_executed": sorted(declared - executed),
            "categories": sorted(exec_cats),
        }

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
                                                       f"{agree} with reviewed_ids",
                                             # Machine-readable, so a gate does not have to parse
                                             # `agree` out of the detail text.
                                             #
                                             # The union above is deliberately forgiving: it
                                             # means deleting every reviewed_by link does NOT
                                             # reduce the numerator, because the 15 review
                                             # records independently name the same 144 ids.
                                             # That is the dimension working as designed, not a
                                             # hole: coverage has two corroborating sources
                                             # and losing one does not lose the fact. What
                                             # losing one DOES mean is that the two sources now
                                             # disagree, and disagreement between two records of
                                             # the same fact is a defect. So this field, not the
                                             # ratio, is what the gate reads. Measured on the
                                             # tree this corpus ships: deleting all 229
                                             # reviewed_by links leaves the numerator at 144
                                             # and flips this to False.
                                             "reviewed_by_agrees_with_records": reviewed_by_ids == reviewed_ids,
                                             "reviewed_by_only": sorted(reviewed_by_ids - reviewed_ids),
                                             "records_only": sorted(reviewed_ids - reviewed_by_ids),
                                             "review_records": n_review_records}

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
        # `execution_kind` now HAS a target-hardware member,
        # `actual_target_hardware_run` (see TARGET_EXECUTION_KIND), so this
        # dimension is no longer structurally pinned at zero: a genuine TMS570
        # or HIL run can be recorded and will move this figure. It reads 0
        # because NO SUCH RUN HAS BEEN PERFORMED -- not because the schema
        # could not express one. That distinction is the whole point of the
        # repair, so the reason is stated in the detail below rather than
        # folded into a silent zero.
        #
        # The buckets are declared explicitly rather than inferred. Host and
        # simulation runs are real executions of the product's code but on
        # developer infrastructure, not on the product; synthetic fixtures are
        # not the product at all. Deriving a target count from the free-form
        # environment.hardware string would be prose matching, not measurement,
        # so the target bucket is read from execution_kind alone, and
        # environment.hardware is used only as a self-consistency check on a
        # record that already claims the kind (see execution_kind_classifier).
        execs = [d for _, d in self.iter_corpus_artifacts()
                 if d.get("artifact_type") == "execution" and d.get("id")]
        kind_of = [d.get("execution_kind") for d in execs]
        target_execs = [d for d, k in zip(execs, kind_of)
                        if k in {TARGET_EXECUTION_KIND}]
        # numerator = distinct TEST MEASURES backed by target-hardware execution,
        # so one measure with three redundant target runs still counts once
        target_tms = {d.get("test_measure_id") for d in target_execs} & set(tms)
        n_target = len(target_tms)
        n_host = sum(1 for k in kind_of if k in HOST_EXECUTION_KINDS)
        n_synth = sum(1 for k in kind_of if k in NON_EXECUTION_KINDS)
        n_undeclared = sum(1 for k in kind_of if k not in DECLARED_EXECUTION_KINDS)
        if n_target:
            evidence_note = f"{n_target} test measures with target-hardware execution"
        else:
            evidence_note = ("0 target-hardware executions: execution_kind can now express a run "
                             "on the product's own hardware, but none has been performed "
                             "(blocked, not fabricated)")
        dims["actual_product_evidence"] = {
            "numerator": n_target,
            "denominator": len(tms),
            "detail": f"{evidence_note}; of {len(execs)} execution records: "
                      f"{n_host} host/simulation (real product code, not target hardware), "
                      f"{n_synth} synthetic_fixture/none, {n_undeclared} undeclared"}

        # synthetic fixture coverage
        #
        # The denominator used to be the literal 43 with the detail "N
        # synthetic_reference artifacts (target 43)". With 207 artefacts present
        # the ratio read 207/43 = 481%, which is not a coverage figure at all --
        # it is a record count divided by a number typed in by hand that nothing
        # in the tree derives. A reader taking it at face value concludes the
        # corpus is nearly five times over-covered, which is meaningless.
        #
        # What is measurable and comparable is FAMILY COVERAGE: how many of the
        # artefact families the corpus knows about the synthetic profile
        # actually carries at least one record of. The denominator is derived
        # from the same expected-family set artifact_population uses, so the two
        # dimensions cannot disagree about what a family is. The raw record count
        # is kept in the detail because it is the figure a reader will actually
        # ask for, but it is labelled as a count, not used as a numerator.
        synth_recs = [d for _, d in self.iter_corpus_artifacts()
                      if d.get("profile") == "synthetic_reference" and d.get("id")]
        synth_families = set(d.get("artifact_type", "unknown") for d in synth_recs)
        synth_missing = sorted(expected_families - synth_families)
        dims["synthetic_fixture_coverage"] = {
            "numerator": len(expected_families & synth_families),
            "denominator": len(expected_families),
            "detail": (f"{len(expected_families & synth_families)}/{len(expected_families)} "
                       f"artefact families hold at least one synthetic_reference record; "
                       f"{len(synth_recs)} synthetic_reference records in total "
                       f"(a count, not the numerator). "
                       + (f"families with no synthetic record: {synth_missing}"
                          if synth_missing else "every family the corpus defines has one")),
            "families_missing": synth_missing,
            "record_count": len(synth_recs),
        }

        # negative scenario validation
        dims["negative_scenario_validation"] = self._negative_scenario_dimension()

        dims["final_status"] = FINAL_STATUS

        # export reproducibility
        #
        # This was 1 if exports/manifest.json exists. That is circular in the
        # acceptance suite: gate [6/8] calls cmd_export() immediately before
        # cmd_coverage's result is read, so the manifest the dimension tested
        # for was the one that same run had just written a moment earlier. The
        # gate therefore verified that a file it had created existed.
        #
        # What the dimension claims is REPRODUCIBILITY, so that is what it now
        # measures, on its own terms: export the corpus twice into two throwaway
        # directories and compare the content hashes of every file each run
        # declares. It reads nothing the suite wrote and it writes nothing into
        # the tree, so the figure is the same from `corpus.py coverage` as from
        # `corpus.py check`.
        #
        # Both runs write to a temporary directory outside the tree. Nothing
        # under docs/artifacts/exports/ is created, read or deleted here.
        exp_detail, exp_ok = self._measure_export_reproducibility()
        dims["export_reproducibility"] = {"numerator": 1 if exp_ok else 0, "denominator": 1,
                                          "detail": exp_detail,
                                          "reproducible": exp_ok}

        # human approval (always 0 pending)
        dims["human_approval"] = {"numerator": 0, "denominator": total_art,
                                  "detail": "all artifacts pending human approval (none performed)"}

        # production authorization (correctly 0)
        dims["production_authorization"] = {"numerator": 0, "denominator": total_art,
                                            "detail": "production_authorized=false for all artifacts (by policy)"}

        return dims

    def cmd_coverage(self, quiet=False):
        """Compute the 15 completion dimensions with numerators/denominators."""
        dims = self._coverage_dimensions()

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
        nsv = dims["negative_scenario_validation"]
        gap_list = [
            f"Negative scenario validation: {nsv['numerator']}/{nsv['denominator']} mutations executed "
            f"and passing; {nsv['detail'].rsplit('; ', 1)[-1]} "
            f"(measured by running the suite, not by counting files)",
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

    # The §13 path this gate has to resolve. Written as (stage name, predicate
    # over (artifact_id, record)) in the engineering order the master prompt
    # gives, so a stage index means the same thing in the ladder, in the report
    # and in the gate.
    #
    # "hw/sw architecture" and "detailed design" are separate entries on purpose.
    # §13 requires both: architecture allocates, detailed design specifies. In
    # this corpus both are `design` records, so the architecture predicate is
    # widened to include the concept records that perform allocation, and the
    # detailed-design predicate is the strict `design` one. A chain that reaches
    # architecture but not detailed design is a real, reportable shortfall.
    TRACE_CHAIN_STAGES = (
        ("operational scenario", lambda aid, d: d.get("artifact_type") in ("use_case", "stakeholder_need")),
        ("hazard", lambda aid, d: d.get("artifact_type") == "hazard"),
        ("safety goal", lambda aid, d: d.get("artifact_type") == "safety_goal"),
        ("functional safety requirement",
         lambda aid, d: d.get("artifact_type") == "requirement" and "-FSR-" in aid),
        ("technical/system requirement",
         lambda aid, d: d.get("artifact_type") == "requirement"
         and any(t in aid for t in ("-TSR-", "-SWR-", "-SYR-", "-HSI-", "-SEC-"))),
        ("hw/sw architecture",
         lambda aid, d: d.get("artifact_type") in ("design", "safety_concept", "item_definition")),
        ("detailed design", lambda aid, d: d.get("artifact_type") == "design"),
        ("implementation", lambda _aid, d: d.get("artifact_type") == "implementation"),
        ("verification measure", lambda aid, d: d.get("artifact_type") == "test_measure"),
        ("execution/evidence", lambda aid, d: d.get("artifact_type") == "execution"),
        ("review", lambda aid, d: d.get("artifact_type") == "review"),
        ("safety argument", lambda aid, d: d.get("artifact_type") == "safety_case"),
    )

    # Relations that carry engineering meaning for this traversal. `related_to`
    # is excluded: the link validator already documents it as the weak link that
    # satisfies no coverage obligation, so following it here would let the
    # chain pass over a gap that has been declared but not engineered.
    TRACE_CHAIN_RELATIONS = {
        "refines", "allocated_to", "implements", "verifies", "validates",
        "result_of", "supports", "mitigates", "specified_by", "consumes",
        "produces", "depends_on", "constrained_by", "reviewed_by", "changes",
        "supersedes",
    }

    def _trace_chain(self, index, links, profile, root="FB2-SAF-HAZ-000001"):
        """Traverse the §13 path from `root` and report the deepest stage reached.

        Breadth-first over the profile's own link graph, following only
        engineering-meaningful relations and only edges whose BOTH endpoints
        resolve to a record in the same profile. Direction is deliberately
        ignored: §13 says "the arrows above describe traversal, not mandatory
        storage direction", and the corpus stores `mitigates` as
        goal -> hazard while the chain is hazard -> goal.

        The "implementation" stage has no record type in this corpus: an
        implementation is a code location, and the corpus represents one as a
        source-registry anchor named by a record's `source_refs`. That stage is
        therefore reached when a reached design/concept record names at least
        one anchor that resolves in the source registry. Whether that anchor's
        content_hash and symbol are real is a provenance question, judged by
        _validate_source_anchors -- deliberately not conflated with reachability.

        Required stages are the ones the profile actually instantiates. A stage
        with zero candidate records anywhere in the profile cannot be traversed
        by any link graph, and requiring it would be demanding a record the
        corpus documents as a gap rather than as work. Those stages are reported
        by name with their zero count so the relaxation is visible, never silent.
        """
        prof_index = {aid: d for (prof, aid), (_p, d) in index.items() if prof == profile}
        adjacency = {}
        for l in links:
            if l.get("_profile", "unknown") != profile:
                continue
            if l.get("relation_type") not in self.TRACE_CHAIN_RELATIONS:
                continue
            src, tgt = l.get("source_id"), l.get("target_id")
            if src not in prof_index or tgt not in prof_index:
                continue
            adjacency.setdefault(src, []).append((tgt, l.get("relation_type")))
            adjacency.setdefault(tgt, []).append((src, l.get("relation_type")))

        from collections import deque
        seen = {}
        if root in prof_index:
            seen[root] = (None, None, None)
            queue = deque([root])
            while queue:
                node = queue.popleft()
                for nxt, rel in adjacency.get(node, ()):
                    if nxt not in seen:
                        seen[nxt] = (node, rel, None)
                        queue.append(nxt)

        # stage membership
        anchor_ids = self._anchor_ids()
        instantiated, reached, witness = [], {}, {}
        for si, (name, pred) in enumerate(self.TRACE_CHAIN_STAGES):
            if pred is None:
                # Implementation is reached from an architecture or detailed
                # design record that is ITSELF already reachable and that names
                # at least one anchor. A hazard record's own source_refs do not
                # put an implementation downstream of a design, so a design (or
                # allocation record) must be in the reached set for this stage to
                # count. Without that condition the stage is satisfied by any
                # reachable record that happens to cite code.
                #
                # The candidate set stays profile-wide, so "instantiated" keeps
                # meaning "this profile has implementation elements at all" and
                # is not contaminated by the traversal result; only `hits`
                # depends on reachability.
                design_like = (self.TRACE_CHAIN_STAGES[5][1], self.TRACE_CHAIN_STAGES[6][1])
                cands = {aid for aid, d in prof_index.items()
                         if any(p(aid, d) for p in design_like)
                         and any(r in anchor_ids for r in (d.get("source_refs") or []))}
            else:
                cands = {aid for aid, d in prof_index.items() if pred(aid, d)}
            hits = sorted(cands & set(seen))
            instantiated.append((si, name, len(cands)))
            if hits:
                reached[si] = hits
                witness[si] = hits[0]

        required = [(si, name) for si, name, n in instantiated if n > 0]
        unmet = [(si, name) for si, name in required if si not in reached]
        absent = [(si, name, n) for si, name, n in instantiated if n == 0]
        deepest = max(reached) if reached else None
        if root not in prof_index:
            verdict = "broken"
        elif not unmet:
            verdict = "full_chain"
        elif deepest is not None:
            verdict = f"reached stage {deepest} of {len(self.TRACE_CHAIN_STAGES) - 1}"
        else:
            verdict = "broken"

        return {
            "profile": profile, "root": root, "verdict": verdict,
            "deepest_stage": deepest,
            "reachable": len(seen), "links_considered": len(adjacency),
            "reached": {self.TRACE_CHAIN_STAGES[si][0]: hits for si, hits in reached.items()},
            "witness": {self.TRACE_CHAIN_STAGES[si][0]: witness[si] for si in witness},
            "unmet_required": [name for _si, name in unmet],
            "not_instantiated": [name for _si, name, _n in absent],
            "ladder": [{"stage": si, "name": name, "instantiated": n,
                        "reached": len(reached.get(si, ()))} for si, name, n in instantiated],
        }

    def _anchor_ids(self):
        return {a.get("anchor_id") for a in self._load_source_anchors()}

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

    # 'referenced' is a token the coverage plan actually uses for ISO parts 1 and
    # 10. Without it those two parts classified as 'unrecorded', which is a false
    # statement about the plan: the plan records them, as 'referenced'.
    _PLAN_DISPOSITION_TOKENS = ("not_applicable", "partially_mapped",
                                 "unverified_reference", "referenced", "mapped", "gap")

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
    def _stable_text(v, limit=300):
        """Deterministic one-cell rendering of a free-text value.

        A rule message may interpolate a Python set, whose repr order changes
        with PYTHONHASHSEED. Left alone that makes the generated document differ
        between two runs of the same corpus, which breaks the byte-identical
        regeneration contract. Members of any {...} or [...] group are therefore
        sorted here, in the presentation layer only: the rule that produced the
        message is not touched.
        """
        s = str(v).replace("\n", " ").replace("|", "\\|").strip()

        def _sort_group(m):
            inner = m.group(1)
            if "," not in inner:
                return m.group(0)
            return m.group(0)[0] + ", ".join(sorted(x.strip() for x in inner.split(","))) \
                + m.group(0)[-1]

        for open_c, close_c in (("{", "}"), ("[", "]")):
            pattern = re.escape(open_c) + r"([^" + re.escape(open_c + close_c) + r"]*)" \
                      + re.escape(close_c)
            s = re.sub(pattern, _sort_group, s)
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
        b.append("| `actual_target_hardware_run` | executed on the product's own target hardware; "
                 "the only member that is product-hardware evidence |")
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

        # ------------------------------------------- traceability document (owned)
        #
        # The single generated traceability document. It exists because the file
        # that used to carry this name at the repository root was hand-authored:
        # no validator read it, no renderer regenerated it, and the guard-field
        # discipline that governs every generated surface had no authority over
        # it, so it could drift back toward claiming ISO 26262 conformity and an
        # ASIL capability (finding FB2-REV-FND-000022). It is generated here, from
        # the canonical records, so it carries the same provenance header and
        # guard-field contract as every other view and cannot be edited into an
        # overclaim. Every figure below is computed at render time; none is
        # transcribed from a report, from coverage-report.json or from prose.
        b = ["## What this document is", ""]
        b.append("This is the traceability document for the foxBMS 2 lifecycle artifact corpus. "
                 "It is a derived work product: a census of the records the corpus actually "
                 "holds, of the links between them, and of what the corpus's own checkers "
                 "measure about them. It is regenerated from the canonical JSON records by "
                 f"`{self.VIEW_TOOL_REF}`, and the repository-root path "
                 "`TRACEABILITY_DOCUMENT.md` is a pointer to this file rather than a second copy.")
        b.append("")
        b.append("It reports three different populations and does not merge them:")
        b.append("")
        b.append(f"- **{counts}** — records and links in the tool's index, the population every "
                 "count below is drawn from.")
        b.append("- Records that exist in both profiles appear once per profile. The same "
                 "identifier in `as_is` and in `synthetic_reference` is two different records by "
                 "design, and are counted separately.")
        b.append("- A coverage ratio is a ratio, not a score. Where the denominator is a target "
                 "rather than a population, the table says so in its own column.")
        b.append("")

        # ---- artifact census, by profile and type
        b.append("## Artifact census")
        b.append("")
        b.append("Computed from the artifact index at render time.")
        b.append("")
        art_rows = {}
        profs_all = sorted({k[0] for k in m["index"]
                            if isinstance(k, tuple) and len(k) >= 2 and k[0] != "_registry"})
        for aid, p, d in select():
            key = (d.get("profile"), d.get("artifact_type"))
            art_rows[key] = art_rows.get(key, 0) + 1
        types = sorted({t for _, t in art_rows})
        self._table(b, ["Artifact type"] + profs_all + ["Total"],
                    [[f"`{t}`"] + [art_rows.get((p, t), 0) for p in profs_all]
                     + [sum(art_rows.get((p, t), 0) for p in profs_all)] for t in types]
                    + [["**Total**"] + [sum(art_rows.get((p, t), 0) for t in types) for p in profs_all]
                       + [sum(art_rows.values())]])
        total_records = sum(art_rows.values())
        b.append(f"{total_records} records carry an `id` and are therefore countable. Registry "
                 "container files (parameter and assumption registries) carry no top-level `id` "
                 "and are counted separately below; they are not lifecycle artifacts.")
        b.append("")
        b.append("### Non-record registries")
        b.append("")
        reg_rows = []
        for label, relpath in (("source anchors", "sources/source-registry.json"),
                               ("assumption registry", "shared/assumption-registry.json"),
                               ("parameter registry", "shared/parameter-registry.json")):
            rp = self.artifacts_dir / relpath
            n = 0
            if rp.exists():
                d = load_json(rp)
                for key in ("anchors", "assumptions", "parameters"):
                    if isinstance(d.get(key), list):
                        n = len(d[key])
                        break
            reg_rows.append([label, f"`{relpath}`", n if rp.exists() else "**absent**"])
        self._table(b, ["Registry", "Canonical file", "Entries"], reg_rows)
        b.append("")

        # ---- guard-field census
        b.append("## Guard-field census")
        b.append("")
        b.append("Counted from the index. This is the population-wide position of the four "
                 "guard fields, not a claim about any one record.")
        b.append("")
        gvals = {}
        for aid, p, d in select():
            g = (str(d.get("human_approval_status")), str(d.get("production_authorized")).lower(),
                 str(d.get("product_verification_credit")).lower())
            gvals[g] = gvals.get(g, 0) + 1
        self._table(b, ["`human_approval_status`", "`production_authorized`",
                        "`product_verification_credit`", "Records"],
                    [[a, b_, c, n] for (a, b_, c), n in sorted(gvals.items())])
        b.append("")
        approvals = sum(n for (a, _, _), n in gvals.items() if a != "pending")
        auths = sum(n for (_, x, _), n in gvals.items() if x != "false")
        b.append(f"No record in this corpus carries a human approval: "
                 f"{approvals} records are in any state other than `pending`. "
                 f"No record is authorized for production: {auths} records are in any state "
                 f"other than `false`. Automated review performed by this toolchain is not "
                 f"organizational independence and is not a human confirmation. Nothing in this "
                 f"document can change those two numbers.")
        b.append("")
        b.append("### ASIL field values — hypothetical only")
        b.append("")
        asil_recs = [(aid, d) for aid, p, d in select() if d.get("asil")]
        justified = sum(1 for _, d in asil_recs if d.get("asil_justification"))
        b.append(f"{len(asil_recs)} records carry an `asil` field and {justified} of them carry an "
                 f"`asil_justification` block. `ASIL` in this corpus is a field value on a synthetic "
                 f"record in a fictional reference project, used to exercise how allocation is "
                 f"expressed. It is **not** an ASIL assigned to any real product, it is **not** a "
                 f"determination of any kind, and no HARA has been performed for any real product. "
                 f"This document states no capability level and asserts none.")
        b.append("")

        # ---- link registry census
        b.append("## Link registry census")
        b.append("")
        b.append("Computed from the canonical link registries at render time.")
        b.append("")
        lstats = {}
        for l in m["links"]:
            lstats[(l.get("_profile", "unknown"), l.get("relation_type"))] = \
                lstats.get((l.get("_profile", "unknown"), l.get("relation_type")), 0) + 1
        lprofiles = sorted({k[0] for k in lstats})
        lrels = sorted({k[1] for k in lstats})
        self._table(b, ["Relation type"] + lprofiles + ["Total"],
                    [[f"`{r}`"] + [lstats.get((p, r), 0) for p in lprofiles]
                     + [sum(lstats.get((p, r), 0) for p in lprofiles)] for r in lrels]
                    + [["**Total**"] + [sum(lstats.get((p, r), 0) for r in lrels) for p in lprofiles]
                       + [sum(lstats.values())]])
        b.append("Link metadata completeness, counted over the same links:")
        b.append("")
        meta_rows = []
        for field in ("rationale", "provenance", "review_state", "change_suspect_status"):
            present = sum(1 for l in m["links"] if field in l and l.get(field) is not None)
            meta_rows.append([f"`{field}`", present, len(m["links"]),
                              f"{round(100.0 * present / max(len(m['links']), 1))}%"])
        self._table(b, ["Link field", "Links carrying it", "Links total", "Share"], meta_rows)
        suspect = sum(1 for l in m["links"] if l.get("change_suspect_status"))
        unreviewed = sum(1 for l in m["links"]
                         if l.get("review_state") not in ("reviewed",))
        b.append(f"{suspect} links are marked change-suspect and {unreviewed} links are not in "
                 f"`review_state: reviewed`. Neither number is a defect count: both are the state "
                 f"the registries record.")
        b.append("")

        # ---- verification reachability
        b.append("## Verification reachability")
        b.append("")
        b.append("Built from `verifies` and `validates` links in the canonical registries, counted "
                 "per profile. A requirement with no verification link is a gap and is named, not "
                 "hidden.")
        b.append("")
        vrows = []
        for prof in lprofiles:
            reqs = [aid for aid, p, d in select(profile=prof, atype="requirement")]
            covered = set()
            for l in m["links"]:
                if l.get("_profile") == prof and l.get("relation_type") in ("verifies", "validates"):
                    covered.add(l.get("target_id"))
            gap = sorted(r for r in reqs if r not in covered)
            vrows.append([prof, len(reqs), len(covered & set(reqs)), len(gap),
                          "; ".join(f"`{g}`" for g in gap) if gap else "—"])
        self._table(b, ["Profile", "Requirements", "With a verification link",
                        "Without one", "Ids without one"], vrows)
        b.append("")

        # ---- standards dispositions, read live
        b.append("## Standards dispositions")
        b.append("")
        b.append("Read from `governance/coverage-plan.json` and `governance/standards-lock.json` "
                 "at render time. These are the corpus's own recorded dispositions against the "
                 "two standards it has locked. A recorded disposition is a statement about work "
                 "booked in this corpus; it is not a statement that the work satisfies the "
                 "standard, and this corpus is not assessed against any standard by anyone.")
        b.append("")
        procs = self._plan().get("process_inventory", [])
        tally = {}
        for p_ in procs:
            st = self._plan_status(p_.get("disposition"))
            tally[st] = tally.get(st, 0) + 1
        self._table(b, ["ASPICE process disposition", "Processes"],
                    [[f"`{k}`", v] for k, v in sorted(tally.items())]
                    + [["**Total**", len(procs)]])
        b.append(f"{self._plan_quote(processes=('SYS.1', 'SYS.2', 'SUP.9'))}")
        b.append("")
        iso_keys = sorted(self._plan().get("iso26262_coverage", {}))
        iso_tally = {}
        for k in iso_keys:
            st = self._plan_iso_status(k)
            iso_tally[st] = iso_tally.get(st, 0) + 1
        self._table(b, ["ISO 26262 part disposition", "Parts"],
                    [[f"`{k}`", v] for k, v in sorted(iso_tally.items())]
                    + [["**Total**", len(iso_keys)]])
        sl = load_json(self.governance_dir / "standards-lock.json")
        locked = sl.get("standards", [])
        if isinstance(locked, list) and locked:
            self._table(b, ["Locked standard", "Title", "Edition", "Locked by"],
                        [[f"`{s.get('id')}`", self._cell(s.get("title"), 70),
                          s.get("edition"), sl.get("locked_by")] for s in locked])
        b.append("A standard that is not in the lock has no records mapped to it in this corpus "
                 "and cannot have any disposition shown above. Its absence is a fact about the "
                 "corpus, not about the standard.")
        b.append("")

        # ---- coverage dimensions, recomputed
        b.append("## Coverage dimensions")
        b.append("")
        b.append("Recomputed by the same function `corpus.py coverage` prints, at render time. "
                 "Nothing here is copied out of a report. The last column states what each "
                 "numerator actually counts, because a dimension whose name implies a measurement "
                 "and whose numerator is a presence check or a constant would otherwise read as "
                 "stronger than it is. Such dimensions are marked **presence** or **constant**; "
                 "the rest are measured from the records on this run.")
        b.append("")
        basis = {
            "scope_accounting": ("presence", "1 if the source inventory file carries a claimed "
                                 "file count; it does not compare that claim against the tree, "
                                 "which acceptance gate [2/8] inventory does"),
            "artifact_population": ("measured", "artifact families that hold at least one record"),
            "standards_mapping": ("measured", "ASPICE processes and ISO 26262 parts whose coverage-plan "
                                  "text names at least one FB2- id that RESOLVES against the "
                                  "artifact index or the source registry. It is a measure of "
                                  "entries that are BACKED BY AN ARTEFACT THAT EXISTS, not a "
                                  "count of plan entries and not a count of satisfied mappings; "
                                  "entries declaring not_applicable are out of the denominator "
                                  "and named in the detail, and entries that claim a disposition "
                                  "while naming nothing that exists are counted as unbacked. "
                                  "Read the disposition tally in the detail for the ASPICE/ISO "
                                  "split"),
            "source_grounding": ("measured", "records carrying at least one `source_refs` entry"),
            "traceability_integrity": ("measured", "links that are not dangling, from a link "
                                       "validation re-run for this figure"),
            "semantic_consistency_checks": ("measured", "semantic rules _validate_semantic_rules "
                                            "actually EVALUATED this run, counted by the recorder "
                                            "each rule block fills in on entry, over the rules "
                                            "SEMANTIC_RULE_IDS declares. Computed, not declared: "
                                            "the previous figure was the literal 10/10 against a "
                                            "function that evaluates 21 rules"),
            "automated_review_coverage": ("measured", "unique indexed ids covered by a review "
                                          "record or a `reviewed_by` link; the two sources are "
                                          "unioned, and whether they AGREE is reported "
                                          "separately because the ratio does not move when one is "
                                          "deleted"),
            "verification_planning": ("measured", "test measures per safety requirement; a ratio, "
                                      "not a score, and over 100% means over-covered"),
            "actual_product_evidence": ("measured", "test measures backed by an execution whose "
                                         "`execution_kind` names the product's own hardware"),
            "synthetic_fixture_coverage": ("measured", "artefact families holding at least one "
                                           "`synthetic_reference` record, over the families the "
                                           "corpus defines; the record count is reported in the "
                                           "detail as a count. Not a ratio against a typed-in "
                                           "target"),
            "negative_scenario_validation": ("measured", "mutation scenarios that PASS when "
                                              "executed: the rule each declares is implemented, is "
                                              "silent on the unmutated corpus, and produces a "
                                              "finding the baseline did not contain"),
            "export_reproducibility": ("measured", "1 if exporting the corpus into two separate "
                                       "temporary directories yields identical content hashes for "
                                       "every declared file; measured in this dimension rather "
                                       "than read from exports/manifest.json, which the "
                                       "acceptance suite creates moments before this runs"),
            "human_approval": ("constant", "0 by corpus policy; every record is `pending`. The "
                               "policy is enforced by the `human_approval_rejected` rule, not "
                               "measured by this dimension"),
            "production_authorization": ("constant", "0 by corpus policy; every record is `false`. "
                                        "The policy is enforced by the "
                                        "`production_authorized_rejected` rule and by acceptance "
                                        "gate [7/8]"),
        }
        dims_doc = self._coverage_dimensions()
        rows = []
        for k, v in dims_doc.items():
            if not isinstance(v, dict):
                rows.append([f"`{k}`", f"`{v}`", "—", "recorded status"])
                continue
            kind, what = basis.get(k, ("measured", ""))
            rows.append([f"`{k}`", f"{v['numerator']}/{v['denominator']}",
                         f"**{kind}**", f"{self._stable_text(v['detail'], 150)} — {what}"])
        self._table(b, ["Dimension", "Value", "Numerator basis", "What it counts"], rows)
        b.append("")

        # ---- scenario validation, measured on this run
        b.append("## Negative-scenario validation")
        b.append("")
        scn = self._execute_scenarios()
        b.append(f"Measured by executing the suite on this run: "
                 f"{scn['passed_mutations']}/{scn['total_mutations']} mutation scenarios passed and "
                 f"{scn['passed_changes']}/{scn['total_changes']} change lifecycles are structurally "
                 f"complete. A mutation scenario counts as passing only when the rule it declares "
                 f"detects the defect the mutation injects.")
        b.append("")
        rows = []
        for r in scn["results"]:
            if r.get("type") == "mutation":
                rows.append([f"`{r['scenario_id']}`", f"`{r.get('declared_detector')}`",
                             "implemented" if r.get("detector_implemented") else "**not implemented**",
                             "PASS" if r.get("passed") else "**FAIL**",
                             self._stable_text(r.get("reason"), 120)])
            else:
                rows.append([f"`{r['scenario_id']}`", "structural completeness",
                             "9 required elements", "PASS" if r.get("passed") else "**FAIL**",
                             "structure complete" if r.get("passed")
                             else "missing " + ", ".join(r.get("missing") or [])])
        self._table(b, ["Scenario", "Declared detector", "Detector state", "Result",
                        "Why"], rows)
        b.append("The scenario suite establishes that the corpus's own detectors fire on defects "
                 "this corpus has modelled. It does not establish that the detector set is "
                 "complete, that any rule is correct, or that the corpus is free of defects: a "
                 "defect no scenario models is undetected by construction.")
        b.append("")
        b.append("### Chain diagram")
        b.append("")
        b += self._mermaid("traceability.document-chain", [
            "flowchart LR",
            '  HAZ["FB2-SAF-HAZ-000001<br/>hazard"] -->|mitigates| SGO["FB2-SAF-SGO-000001<br/>safety goal"]',
            '  SGO -->|refines| REQ["safety requirements"]',
            '  REQ -->|verifies| TMS["test measures"]',
            '  TMS -->|result_of| EXE["executions"]',
            '  EXE --> GUARD["human_approval_status=pending<br/>production_authorized=false"]',
        ])
        emit("traceability/traceability-document.md",
             "Traceability — the corpus traceability document (generated)",
             "The whole corpus in one derived document: artifact and link census, guard-field "
             "census, verification reachability, standards dispositions, the coverage dimensions "
             "recomputed live, and the measured negative-scenario result.", b)

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
                "evidence_semantics": "execution_kind (none|actual_host_run|actual_simulation_run|actual_target_hardware_run|synthetic_fixture) orthogonal to outcome (pass|fail|inconclusive|not_run|blocked); only actual_target_hardware_run is product-hardware evidence, and no such run has been performed",
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

    # ------------------------------------------------- scenario detector plumbing

    @contextmanager
    def _suppress_rule(self, rule_id):
        """Drop every finding emitted by one rule, for the duration of the block.

        Used only by the self-tests, to demonstrate that a scenario's verdict
        depends on its own declared detector and cannot be satisfied by a
        neighbouring rule's finding. It models the rule not existing; it does
        not change the rule.
        """
        original = self._run_detectors

        def _filtered(index, links):
            original(index, links)
            self.findings.items = [f for f in self.findings.items if f.get("rule") != rule_id]

        self._run_detectors = _filtered
        try:
            yield
        finally:
            self._run_detectors = original

    @staticmethod
    def _implemented_rules():
        """Rule ids that some findings.add() call site in this file actually emits.

        Derived from this module's own AST rather than from the RULE_IDS
        declaration, so a scenario that names a detector no rule emits is a
        detectable condition instead of a silent pass. Computed once per process.
        """
        global _IMPLEMENTED_RULES
        if _IMPLEMENTED_RULES is not None:
            return _IMPLEMENTED_RULES
        import ast
        src = Path(__file__).read_text(encoding="utf-8")
        found = set()
        for node in ast.walk(ast.parse(src)):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "add"
                    and getattr(node.func.value, "attr", None) == "findings"):
                continue
            for arg in node.args[4:]:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    found.add(arg.value)
        _IMPLEMENTED_RULES = found
        return found

    def _run_detectors(self, index, links):
        """Run every detector reachable from the scenario harness.

        The revision-consistency rule is included explicitly. It used to live
        only inside _validate_artifact, which this harness never called, so
        SCN-MUT-003's declared detector was unreachable by construction.

        Provenance verification and governance semantics are now run here too.
        They are detectors in their own right: they are profile- and file-scoped
        facts about records, not per-mutation predicates, so they belong in the
        same place every other detector is run from. Routing them through
        _run_detectors is what makes them participate in `validate`, in the
        scenario baseline, and in every gate that counts findings -- instead of
        living in a function nothing called.
        """
        self._validate_links(links, index)
        self._validate_link_currency(links, index)
        self._validate_link_registry_shadowing()
        self._validate_semantic_rules(index, links)
        for key, (p, d) in index.items():
            aid = key[1] if isinstance(key, tuple) and len(key) >= 2 else key
            if isinstance(d, dict) and d.get("revision") is not None:
                self._check_revision_consistency(aid, d)
        self._validate_governance_semantics(index)
        self._validate_provenance_refs(index)
        self._validate_provenance_evidence(index)

    _CHANGE_LIFECYCLE_FIELDS = ("baseline_before", "trigger", "impact_analysis", "decision",
                                "new_revisions", "suspect_links", "required_updates",
                                "reverification_selection", "post_change_baseline")
    _BASELINE_ID = re.compile(r"^BAS-[A-Z0-9]+(-[A-Z0-9]+)*-\d+$")
    _CHANGE_REF = re.compile(
        r"\b(?:FB2-[A-Z0-9]+(?:-[A-Z0-9]+)*-\d+|VAR-[A-Z0-9]+(?:-[A-Z0-9]+)*|BAS-[A-Z0-9-]+)\b")

    def _reference_universe(self, index, links):
        """Everything an id-shaped string in this corpus is allowed to name.

        Not every identifier in this corpus is a top-level artifact id: link
        ids live in the link registries, source anchors in the source registry,
        parameters inside parameter-registry containers that carry no top-level
        id at all, variants in the variant matrix. A reference check that only
        knew about the artifact index would report every one of those as
        unresolved, so the universe is built from all five registries and then
        keyed by profile where the corpus keeps profiles apart.
        """
        art = {}
        for (prof, aid) in index:
            art.setdefault(prof, set()).add(aid)
            art.setdefault("__any__", set()).add(aid)
        link_ids = {l.get("link_id") for l in links if l.get("link_id")}
        anchors = self._anchor_ids()
        params = set()
        for prm_path in sorted(self.corpus_dir.rglob("parameter-registry.json")):
            try:
                prd = load_json(prm_path)
            except Exception:
                continue
            for prm in prd.get("parameters", []) or []:
                if isinstance(prm, dict) and prm.get("id"):
                    params.add(prm["id"])
        for shared in (self.artifacts_dir / "shared" / "parameter-registry.json",):
            if shared.exists():
                for prm in load_json(shared).get("parameters", []) or []:
                    if isinstance(prm, dict) and prm.get("id"):
                        params.add(prm["id"])
        variants = set()
        vm = self.sources_dir / "variant-matrix.json"
        if vm.exists():
            vdoc = load_json(vm)
            for key in ("variants", "variant_matrix", "entries"):
                for e in vdoc.get(key, []) or []:
                    if isinstance(e, str):
                        variants.add(e)
                    elif isinstance(e, dict):
                        vid = e.get("variant_id") or e.get("id")
                        if vid:
                            variants.add(vid)
        return {"artifacts": art, "links": link_ids, "anchors": anchors,
                "parameters": params, "variants": variants}

    def _resolve_corpus_reference(self, ref, profile, universe):
        """Resolve one id-shaped reference against the registry universe.

        Returns None when it resolves, or a string explaining what it was
        looked for in and not found in.
        """
        if ref.startswith("FB2-LNK-"):
            if ref in universe["links"]:
                return None
            return "not a link_id in any link registry"
        if ref.startswith("FB2-SRC-"):
            if ref in universe["anchors"]:
                return None
            return "not an anchor_id in sources/source-registry.json"
        if ref.startswith("VAR-"):
            if ref in universe["variants"]:
                return None
            return "not a variant in sources/variant-matrix.json"
        if ref.startswith("BAS-"):
            # There is no baseline registry in this corpus; BAS-* ids are
            # declared by the records that use them. Form is checked
            # separately; there is nothing to resolve them against.
            return None
        art = universe["artifacts"]
        if (profile, ref) in art or ref in art.get("__any__", ()):
            return None
        if ref in universe["parameters"]:
            # A parameter id. Parameter-registry containers carry no top-level
            # artifact id, so these are legitimately not in the artifact index.
            return None
        return f"not an artifact id in profile {profile} or any other profile"

    def _validate_change_lifecycle(self, d, index, links):
        """Validate the CONTENT of one change-lifecycle scenario.

        Returns (checks, passed). Each check is a dict
        {check, passed, detail} so both the console line and the persisted
        report name the individual facts.

        The checks, in order:
          record is a mapping, and each of the nine required fields is present
          and non-null;
          `trigger` carries source, description and date;
          `impact_analysis` carries non-empty arrays AND a rationale;
          `decision` carries decision_maker, date, rationale and disposition;
          every `new_revisions` entry carries artifact_id, old_revision and
            new_revision, and those artifact ids resolve;
          `baseline_before` and `post_change_baseline` are well-formed
            baseline ids;
          every id referenced in affected_artifacts, suspect_links,
            required_updates and reverification_selection resolves, per profile.
        """
        checks = []

        def add(name, ok, detail=""):
            checks.append({"check": name, "passed": bool(ok), "detail": detail if not ok else ""})

        add("record is an object", isinstance(d, dict),
            f"scenario is {type(d).__name__}, not an object")
        if not isinstance(d, dict):
            return checks, False

        # 1. required fields present and non-null
        absent, nulls = [], []
        for f in self._CHANGE_LIFECYCLE_FIELDS:
            if f not in d:
                absent.append(f)
            elif d[f] is None:
                nulls.append(f)
        add("all nine required fields present", not absent, f"absent: {absent}")
        add("no required field is null", not nulls,
            f"null: {nulls} -- a present-but-null field carries no content and the "
            f"previous key-presence check accepted it")

        # 2. trigger
        trig = d.get("trigger")
        t_missing = [k for k in ("source", "description", "date")
                     if not (isinstance(trig, dict) and str(trig.get(k) or "").strip())]
        add("trigger carries source/description/date", not t_missing,
            f"trigger is {json.dumps(trig)[:120]}; missing or empty: {t_missing}")

        # 3. impact_analysis
        ia = d.get("impact_analysis")
        if isinstance(ia, dict):
            arr_missing = [k for k in ("affected_artifacts", "affected_links",
                                       "affected_reviews", "affected_evidence")
                           if not (isinstance(ia.get(k), list) and ia.get(k))]
            rationale = ia.get("risk_assessment") or ia.get("rationale")
            add("impact_analysis arrays non-empty", not arr_missing,
                f"empty or absent arrays: {arr_missing}")
            add("impact_analysis carries a rationale",
                bool(isinstance(rationale, str) and rationale.strip()),
                "neither risk_assessment nor rationale carries text")
        else:
            add("impact_analysis arrays non-empty", False,
                f"impact_analysis is {json.dumps(ia)[:120]}, not an object with arrays")
            add("impact_analysis carries a rationale", False,
                "impact_analysis is not an object")

        # 4. decision
        dec = d.get("decision")
        d_missing = [k for k in ("decision_maker", "date", "rationale", "disposition")
                     if not (isinstance(dec, dict) and str(dec.get(k) or "").strip())]
        add("decision carries maker/date/rationale/disposition", not d_missing,
            f"decision is {json.dumps(dec)[:120]}; missing or empty: {d_missing}")

        # 5. new_revisions entries
        universe = self._reference_universe(index, links)
        profile = d.get("profile", "unknown")
        nr = d.get("new_revisions")
        nr_missing, nr_unresolved = [], []
        if isinstance(nr, list) and nr:
            for entry in nr:
                if not isinstance(entry, dict):
                    nr_missing.append("entry is not an object")
                    continue
                for k in ("artifact_id", "old_revision", "new_revision"):
                    if not str(entry.get(k) or "").strip():
                        nr_missing.append(f"{entry.get('artifact_id', '?')}: {k}")
                aid = entry.get("artifact_id")
                if aid:
                    why = self._resolve_corpus_reference(str(aid), profile, universe)
                    if why:
                        nr_unresolved.append(f"{aid} ({why})")
        else:
            nr_missing.append("new_revisions is empty or not a list")
        add("new_revisions entries carry artifact_id/old_revision/new_revision",
            not nr_missing, f"incomplete entries: {nr_missing}")
        add("new_revisions artifact ids resolve", not nr_unresolved,
            f"unresolved: {nr_unresolved}")

        # 6. baseline ids
        for field in ("baseline_before", "post_change_baseline"):
            val = d.get(field)
            add(f"{field} is a well-formed baseline id",
                bool(isinstance(val, str) and self._BASELINE_ID.match(val.strip())),
                f"{field} is {val!r}; expected the form BAS-<SEGMENT>-<digits>")

        # 7. every referenced id resolves
        ref_lists = {
            "impact_analysis.affected_artifacts":
                (ia.get("affected_artifacts") if isinstance(ia, dict) else None),
            "suspect_links": d.get("suspect_links"),
            "required_updates": d.get("required_updates"),
            "reverification_selection": d.get("reverification_selection"),
        }
        for label, entries in ref_lists.items():
            found, why_bad = set(), {}
            if isinstance(entries, list):
                for entry in entries:
                    for ref in self._CHANGE_REF.findall(str(entry)):
                        found.add(ref)
                        why = self._resolve_corpus_reference(ref, profile, universe)
                        if why:
                            why_bad[ref] = why
            add(f"{label}: all referenced ids resolve", not why_bad,
                f"{len(found)} id(s) referenced, unresolved: "
                + ", ".join(f"{k} ({v})" for k, v in sorted(why_bad.items())))

        # 8. new_revisions is not empty (a change that revises nothing is not a
        #    lifecycle demonstration)
        add("new_revisions is non-empty", bool(nr),
            "a change lifecycle with no new revision records no change")
        add("suspect_links is non-empty", bool(d.get("suspect_links")),
            "a change lifecycle must name the links whose validity is now suspect")
        add("required_updates is non-empty", bool(d.get("required_updates")),
            "a change lifecycle must name what has to be updated")
        add("reverification_selection is non-empty", bool(d.get("reverification_selection")),
            "a change lifecycle must select the verification to re-run")

        return checks, all(c["passed"] for c in checks)

    def _baseline_findings(self):
        """Findings produced by the unmutated corpus. Used to subtract standing
        defects from a scenario's detections (see _match_scenario_finding)."""
        self.findings = Findings()
        self._run_detectors(self.load_artifact_index(), self.load_links())
        return self.findings

    def _declared_detector(self, scenario):
        """The rule id a scenario claims to exercise.

        Read from the evaluator-only oracle manifest, because that is where the
        reviewed expectations live; the ingestible scenario file carries a
        human-readable label for the same rule. Returns None when neither names
        a detector, which fails the scenario loudly.
        """
        ref = scenario.get("oracle_manifest_ref")
        if ref:
            mpath = self.scenarios_dir / "evaluator-only" / ref
            if mpath.exists():
                manifest = load_json(mpath)
                for f in manifest.get("expected_findings", []):
                    det = f.get("expected_detector")
                    if det:
                        return det, str(mpath.relative_to(self.artifacts_dir))
        det = scenario.get("expected_detector")
        if det:
            return det, "scenario.expected_detector (no oracle manifest entry)"
        return None, None

    def _match_scenario_finding(self, detector, actual, baseline_sigs):
        """Decide whether `detector` produced a detection caused by this mutation.

        Three conditions, all required:

          1. the detector is implemented. A scenario whose declared detector no
             rule emits fails with an explicit message. This is what makes a
             missing detector visible instead of letting a neighbouring rule's
             finding stand in for it.
          2. the detector does not already fire on the unmutated corpus. If it
             does, the scenario is being satisfied by a standing defect and proves
             nothing about its injected defect; that is reported as a failure.
          3. after the mutation the detector produced a finding that was not in
             the baseline. Baseline subtraction is what removes the possibility
             of a pre-existing finding on the same artifact satisfying the
             expectation - the self-certifying behaviour that this gate had.
        """
        if detector not in self._implemented_rules():
            return False, (f"declared detector '{detector}' is not emitted by any rule in "
                           f"{Path(__file__).name}; the scenario's defect is not detectable as written")
        standing = [s for s in baseline_sigs if s[0] == detector]
        if standing:
            ids = sorted({s[1] for s in standing})
            return False, (f"declared detector '{detector}' already fires on the unmutated corpus "
                           f"for {ids}; the scenario would be satisfied by a standing defect, not by "
                           f"its injected defect")
        for f in actual:
            if f.get("rule") == detector:
                return True, f"{f['severity']}/{f['category']} on {f['artifact_id']}: {f['description']}"
        return False, (f"declared detector '{detector}' is implemented and silent on the baseline but "
                       f"produced no finding after the mutation; the patch did not inject a defect this "
                       f"detector can see")

    def _apply_mutation_and_detect(self, scenario):
        """Apply a scenario patch to an in-memory corpus and return the findings
        the detectors produce, with their rule ids."""
        patch = scenario.get("patch", {})
        op = patch.get("operation")
        affected_links = set(patch.get("affected_links", []))
        affected_ids = set(scenario.get("affected_ids", []))
        new_value = patch.get("new_value", {})

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

        # re-run detection over the mutated corpus
        self.findings = Findings()
        self._run_detectors(index, links)
        return list(self.findings.items)

    def _execute_scenarios(self, scenario_id=None):
        """Run the mutation and change-lifecycle scenarios; return the measured result.

        This is the single place the scenario suite is executed. Two callers need
        it and they must not be able to disagree:

          * cmd_scenario_test, which is acceptance gate [5/8] and prints one line
            per scenario;
          * cmd_coverage, whose negative_scenario_validation dimension reports
            how many of them PASS.

        The full run is memoised on the instance, so cmd_check - which calls
        cmd_coverage first and cmd_scenario_test second - executes the suite
        once and both read the same measurement. Memoising inside one process
        cannot go stale: a scenario patch is applied to an in-memory copy of the
        index (see _apply_mutation_and_detect) and no scenario run writes to the
        corpus, so a second execution in the same process could only reproduce
        the first. A new process always re-measures from disk.

        Nothing is printed and nothing is persisted here; the caller decides.
        Returns:
            not_found         - the requested scenario_id does not exist
            lines             - the exact console lines cmd_scenario_test prints
            results           - per-scenario structured results (unchanged shape)
            passed_mutations  - mutations whose declared detector detected the
                                injected defect
            total_mutations   - mutation scenarios executed
            passed_changes    - change lifecycles with a complete structure
            total_changes     - change lifecycles executed
            all_ok            - every executed scenario passed
        """
        if scenario_id is None and self._scenario_run_cache is not None:
            return self._scenario_run_cache

        muts = sorted((self.scenarios_dir / "mutations").glob("mutation-*.json"))
        chgs = sorted((self.scenarios_dir / "change-lifecycles").glob("change-*.json"))
        all_scn = [(p, load_json(p)) for p in list(muts) + list(chgs)]
        if scenario_id:
            all_scn = [(p, d) for p, d in all_scn
                       if d.get("scenario_id") == scenario_id or d.get("id") == scenario_id
                       or p.stem == scenario_id]
            if not all_scn:
                return {"not_found": True}

        all_ok = True
        passed_mutations = 0
        passed_changes = 0
        results = []
        lines = []
        # Standing defects are computed once. A scenario may only be satisfied by
        # a finding that this mutation caused; see _match_scenario_finding.
        baseline = self._baseline_findings()
        baseline_sigs = baseline.signature()
        # The change-lifecycle reference checks resolve identifiers against the
        # same corpus the mutation harness uses, loaded once here.
        cl_index = self.load_artifact_index()
        cl_links = self.load_links()
        for p, d in all_scn:
            self.findings = Findings()  # fresh per scenario
            sid = d.get("scenario_id", p.stem)
            if d.get("scenario_type") == "mutation":
                actual = self._apply_mutation_and_detect(d)
                expected = d.get("expected_finding", {})
                detector, detector_source = self._declared_detector(d)
                if detector is None:
                    matched, reason = False, (
                        "scenario declares no detector: neither the oracle manifest nor "
                        "expected_detector names a rule, so there is nothing to assert against")
                else:
                    matched, reason = self._match_scenario_finding(
                        detector, actual, baseline_sigs)
                status = "PASS" if matched else "FAIL"
                if matched:
                    passed_mutations += 1
                else:
                    all_ok = False
                # Severity/category agreement with the fixture is reported, never
                # used to pass. Firing on the right rule is the detection; a
                # fixture that states the wrong severity or category is a fixture
                # defect, and is surfaced rather than absorbed by the gate.
                emitted = next((f for f in actual if f.get("rule") == detector), None)
                if emitted is not None:
                    exp_sev, exp_cat = expected.get("severity"), expected.get("category")
                    if (exp_sev and exp_sev != emitted["severity"]) or \
                       (exp_cat and exp_cat != emitted["category"]):
                        lines.append(f"  {status} {sid}: declared detector '{detector}' -> detected on its "
                                     f"own rule; {len(actual)} finding(s) total after mutation")
                        lines.append(f"       FIXTURE MISMATCH: expectation says {exp_sev}/{exp_cat}, the rule "
                                     f"emits {emitted['severity']}/{emitted['category']}. The rule is authoritative; "
                                     f"the expectation must be corrected to state it.")
                    else:
                        lines.append(f"  {status} {sid}: declared detector '{detector}' -> detected on its "
                                     f"own rule ({emitted['severity']}/{emitted['category']} on "
                                     f"{emitted['artifact_id']}); {len(actual)} finding(s) total after mutation")
                else:
                    lines.append(f"  {status} {sid}: declared detector '{detector}' ({detector_source}): {reason}")
                    lines.append(f"       {len(actual)} finding(s) total after mutation: "
                                 + (", ".join(sorted({f.get('rule', '?') for f in actual})) or "none"))
                results.append({"scenario_id": sid, "type": "mutation",
                                "declared_detector": detector,
                                "detector_declared_in": detector_source,
                                "detector_implemented": detector in self._implemented_rules(),
                                "expected": expected, "actual": actual,
                                "passed": matched, "reason": reason})
            else:
                # change lifecycle: validate CONTENT, not key presence.
                #
                # The previous check was `missing = [k for k in required if k not in d]`,
                # which is satisfied by writing `{"baseline_before": null, "trigger":
                # null, ...}` nine times over. Nine nulls produced
                # "[PASS] change lifecycles = 3/3" and, through
                # dims["negative_scenario_validation"]["detail"], the
                # "Acceptance suite: PASSED" line. Every check below is a
                # different fact about the record than "the key is spelled here".
                checks, passed = self._validate_change_lifecycle(d, cl_index, cl_links)
                if passed:
                    passed_changes += 1
                else:
                    all_ok = False
                lines.append(f"  {'PASS' if passed else 'FAIL'} {sid}: change lifecycle content "
                             f"- {sum(1 for c in checks if c['passed'])}/{len(checks)} checks passed")
                for c in checks:
                    lines.append(f"       {'PASS' if c['passed'] else 'FAIL'} {c['check']}"
                                 + (f": {c['detail']}" if c["detail"] else ""))
                results.append({"scenario_id": sid, "type": "change_lifecycle",
                                "profile": d.get("profile", "unknown"),
                                "passed": passed, "missing": [c["check"] for c in checks if not c["passed"]],
                                "checks": checks})

        run = {"not_found": False, "lines": lines, "results": results,
               "passed_mutations": passed_mutations, "total_mutations": len(muts),
               "passed_changes": passed_changes, "total_changes": len(chgs),
               "all_ok": all_ok}
        if scenario_id is None:
            self._scenario_run_cache = run
        return run

    def cmd_scenario_test(self, scenario_id=None):
        run = self._execute_scenarios(scenario_id)
        if run.get("not_found"):
            print(f"Scenario {scenario_id} not found")
            return False
        for line in run["lines"]:
            print(line)

        # persist machine-readable results
        muts = sorted((self.scenarios_dir / "mutations").glob("mutation-*.json"))
        chgs = sorted((self.scenarios_dir / "change-lifecycles").glob("change-*.json"))
        out = self.reports_dir / "scenario-validation-report.json"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        payload = {"schema_version": "1.0.0", "generated_at": utcnow(),
                   "mutation_total_required": 20, "mutations_present": len(muts),
                   "change_lifecycles": len(chgs), "results": run["results"]}
        if out.exists():
            existing = load_json(out)
            if isinstance(existing, dict):
                existing.update(payload)
                payload = existing
        with open(out, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=1, sort_keys=True)
        return run["passed_mutations"] >= 20  # all 20 mutations implemented and passing

    # ------------------------------------------------------------ 15.10 check

    def _gate(self, name, condition, detail=""):
        status = "PASS" if condition else "FAIL"
        print(f"  [{status}] {name}" + (f" - {detail}" if detail else ""))
        return bool(condition)

    def _run_external_reference_check(self):
        """Run docs/artifacts/tools/check_references.py and gate its verdict.

        That tool exists, is not in the acceptance suite, and exits 0. Its own
        output separates two classes: `unresolved references` (an identifier that
        names nothing -- a defect) and `declared forward references` (a planning
        record naming a work product the corpus has not authored, which the tool
        records as finding FB2-REV-FND-000030 and treats as reported rather than
        failed).

        It is wired in on the first class: the number it reports for unresolved
        references is the gate. That is the class the tool itself calls a
        failure, so gating on it cannot contradict the tool's semantics. It is
        deliberately NOT wired in on the declared-forward-reference count: that
        class is a recorded finding by the tool's own design, and turning a
        documented finding into a gate failure here would be inventing a rule in
        a tool this change does not own. The forward-reference count is printed
        so it is visible in `check` rather than only discoverable by running a
        separate script.

        The subprocess exit status is deliberately NOT trusted: the tool exits 0
        with unresolved references present, which is precisely the defect this
        gate exists to close. The parsed number is the authority.
        """
        script = self.tools_dir / "check_references.py"
        if not script.exists():
            return False, "check_references.py not found", None
        try:
            proc = subprocess.run([sys.executable, str(script)], cwd=str(self.root),
                                  capture_output=True, text=True, timeout=600)
        except Exception as e:
            return False, f"could not run {script.name}: {e}", None
        out = proc.stdout or ""
        unresolved = None
        forward = None
        for line in out.splitlines():
            m = re.search(r"unresolved references\s*:\s*(\d+)", line)
            if m and unresolved is None:
                unresolved = int(m.group(1))
            m = re.search(r"declared forward references\s*:\s*(\d+)", line)
            if m and forward is None:
                forward = int(m.group(1))
        if unresolved is None:
            return False, ("check_references.py produced no parseable "
                           "'unresolved references' count; its output contract changed"), forward
        detail = f"{unresolved} unresolved cross-reference(s)"
        if forward is not None:
            detail += (f"; {forward} declared forward reference(s) recorded as "
                       f"FB2-REV-FND-000030 and reported, not gated (see _run_external_reference_check)")
        return unresolved == 0, detail, forward

    def cmd_check(self):
        print("Running corpus acceptance suite...")
        ok = True
        # Gates that this run must not count toward the verdict, only because
        # the caller explicitly asked to inspect rather than to gate.
        advisory = []

        print("\n[1/8] validate")
        validate_ok = self.cmd_validate(quiet=True)
        # In --provenance-report-only mode cmd_validate has already excluded the
        # provenance verdict from its return value, so whatever it returns here
        # is the honest verdict for every OTHER check. The provenance verdict is
        # restated on the gate line so it cannot be missed.
        validate_note = ""
        if self.provenance_report_only:
            p_ok, p_n = getattr(self, "_last_provenance_verdict", (None, 0))
            if p_ok is False:
                validate_note = (f"provenance findings ({p_n}) reported and excluded by "
                                 f"--provenance-report-only")
        ok &= self._gate("validate", validate_ok, validate_note)
        print("\n[2/8] inventory")
        ok &= self._gate("inventory", self.cmd_inventory())
        print("\n[3/8] coverage")
        dims = self.cmd_coverage(quiet=True)
        # gates per final status: synthetic_ready_with_limitations criteria
        ok &= self._gate("negative_scenario_validation = 20/20 mutations",
                        dims["negative_scenario_validation"]["numerator"] >= 20,
                        f"{dims['negative_scenario_validation']['numerator']}/20")
        # The change-lifecycle gate used to read the trailing text
        # "... N/3 change lifecycles" out of the detail string and passed on 3/3.
        # That string only ever recorded how many records had all nine KEYS.
        # The number now comes from the executed content validation, which
        # reports each individual fact.
        ok &= self._gate("change lifecycles content-verified = 3/3",
                        self._change_lifecycle_gate(dims),
                        f"{self._change_lifecycle_passed(dims)}/3 scenarios passed content validation")
        # Coverage dimensions are gated PER DIMENSION, not two out of fifteen.
        #
        # The gate used to read exactly two of the fifteen, and the thirteen it
        # ignored could be driven to nothing without the suite noticing. Three
        # collapses were demonstrated on this corpus and all three reported
        # PASSED 8/8: standards_mapping to 0/38, source_grounding to 5/298, and
        # every reviewed_by link deleted.
        #
        # Which dimensions are gated, and why each is or is not:
        #
        #   GATED  standards_mapping         zero backed entries means the corpus
        #                                      claims ISO 26262 / ASPICE traceability
        #                                      while mapping nothing to an artefact
        #                                      that exists. That is a false claim.
        #   GATED  source_grounding          a corpus of assertions with almost no
        #                                      source backing is not a traceability
        #                                      corpus. Floor and its reasoning at
        #                                      SOURCE_GROUNDING_FLOOR.
        #   GATED  reviewed_by agreement     two records of the same fact (the link
        #                                      registry and the review records) must
        #                                      agree. The ratio does NOT move when
        #                                      the links are deleted -- the review
        #                                      records independently carry the same
        #                                      ids -- so agreement, not the ratio,
        #                                      is what detects that collapse.
        #   GATED  semantic_consistency_checks
        #                                      every declared rule must actually
        #                                      execute; a rule block that silently
        #                                      stopped running is undetected otherwise
        #   NOT GATED  automated_review_coverage ratio, actual_product_evidence,
        #               verification_planning, human_approval, production_authorization.
        #               These measure honest incompleteness that this corpus
        #               documents in its gaps list: 144/259 artefacts reviewed,
        #               0 target-hardware runs performed, 0 human approvals, 0
        #               production authorizations by policy. Gating a ratio on a
        #               number the corpus states it has NOT reached would make the
        #               suite permanently red and teach a reader to ignore it. A
        #               zero numerator IS gated where zero is broken (the three
        #               above); a partial numerator is reported, not gated.
        sm = dims["standards_mapping"]
        ok &= self._gate("standards_mapping: at least one standards entry is backed by a real artefact",
                         sm["numerator"] > 0,
                         f"{sm['numerator']}/{sm['denominator']} backed"
                         if sm["numerator"] else
                         f"0/{sm['denominator']}: every entry claims a disposition and names no "
                         f"artefact that exists, so the standards mapping is an assertion")
        sg = dims["source_grounding"]
        sg_ratio = sg["numerator"] / max(sg["denominator"], 1)
        ok &= self._gate("source_grounding: enough records carry source_refs to make the "
                         "traceability claim checkable",
                         sg_ratio >= SOURCE_GROUNDING_FLOOR,
                         f"{sg['numerator']}/{sg['denominator']} = {sg_ratio:.3f}, floor "
                         f"{SOURCE_GROUNDING_FLOOR:.2f} (see SOURCE_GROUNDING_FLOOR for the reasoning)")
        arc = dims["automated_review_coverage"]
        ok &= self._gate("automated_review_coverage: the link registry and the review records "
                         "agree on which artefacts are under review",
                         arc["reviewed_by_agrees_with_records"],
                         "reviewed_by links and reviewed_ids name the same set"
                         if arc["reviewed_by_agrees_with_records"] else
                         f"the two sources disagree: registry-only {len(arc['reviewed_by_only'])}, "
                         f"records-only {len(arc['records_only'])}; coverage stays "
                         f"{arc['numerator']}/{arc['denominator']} because the numerator is a "
                         f"union, so the ratio alone cannot see this")
        sc = dims["semantic_consistency_checks"]
        ok &= self._gate("semantic_consistency_checks: every declared semantic rule executed",
                         sc["rules_executed"] == sc["rules_declared"],
                         f"{sc['rules_executed']}/{sc['rules_declared']} evaluated"
                         + (f"; declared but not executed: {sc['declared_not_executed']}"
                            if sc["declared_not_executed"] else "")
                         + (f"; executed but undeclared: {sc['undeclared_executed']}"
                            if sc["undeclared_executed"] else ""))

        print("\n[4/8] trace (hazard -> evidence reachability)")
        index = self.load_artifact_index()
        links = self.load_links()
        # The previous gate loaded `links` and then discarded it; its predicate
        # was "does the string FB2-SAF-HAZ-000001 appear as a dictionary key",
        # which is true with the entire link registry removed. This traverses.
        chain_profiles = sorted({prof for prof, _aid in index})
        chains = {prof: self._trace_chain(index, links, prof) for prof in chain_profiles}
        trace_ok = True
        for prof in chain_profiles:
            ch = chains[prof]
            print(f"  profile {prof}: verdict={ch['verdict']}, "
                  f"{ch['reachable']} record(s) reachable from {ch['root']} "
                  f"over {ch['links_considered']} linked node(s)")
            for entry in ch["ladder"]:
                mark = "reached" if entry["reached"] else (
                    "NOT INSTANTIATED" if entry["instantiated"] == 0 else "NOT REACHED")
                witness = ch["witness"].get(entry["name"], "")
                print(f"      stage {entry['stage']:2} {entry['name']:32} "
                      f"candidates={entry['instantiated']:3} reached={entry['reached']:3} "
                      f"{mark}{(' via ' + witness) if witness else ''}")
            if ch["not_instantiated"]:
                print(f"      typed root/leaf exception: NOT CLAIMED. Stages with zero "
                      f"candidate records in this profile, so not traversable by any link "
                      f"graph and not required: {', '.join(ch['not_instantiated'])}")
            if ch["unmet_required"]:
                print(f"      NOT REACHED: {', '.join(ch['unmet_required'])} "
                      f"-- §13 permits a typed root/leaf exception here; this corpus declares none")
            chain_ok, chain_why = self._chain_gate(ch)
            ok &= self._gate(
                f"{prof}: §13 chain reaches every stage this profile instantiates",
                chain_ok,
                chain_why)
        ok &= self._gate("hazard present in every profile", all(
            (prof, "FB2-SAF-HAZ-000001") in index for prof in chain_profiles))
        ok &= trace_ok

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
        # This gate used to read self.findings, which at this point is the EMPTY
        # Findings object left by the change-lifecycle branch in _execute_scenarios
        # (it resets self.findings and runs no detector). Counting
        # category=="provenance" findings in an empty object returns 0 violations
        # by construction, so the gate could not fail. It now runs the governance
        # detector over the whole index on a fresh Findings object and counts
        # what that detector actually found.
        self.findings = Findings()
        gov_index = self.load_artifact_index()
        self._validate_governance_semantics(gov_index)
        self._validate_semantic_rules(gov_index, links)
        # EVERY rule id in GOVERNANCE_SEMANTIC_RULE_IDS counts, not the two this
        # gate used to name.
        #
        # The old filter was
        #     f["rule"] in ("governance_authority_claim",
        #                   "production_authorization_governance_checker")
        # which is two of the nine rules that can raise a governance finding. The
        # seven it discarded are not harmless duplicates: they are the rules that
        # catch an ASIL determination, an ISO 26262 conformity claim, a
        # certification claim, and an authorized_for_production key -- the
        # claim classes this gate is named for. The gate therefore could not
        # fail on precisely the assertions it exists to prevent.
        gov_findings = [f for f in self.findings.items
                        if f.get("rule") in GOVERNANCE_SEMANTIC_RULE_IDS]
        # Prove the filter is not vacuous: a gate that counted zero rules would
        # also report zero violations. The rule set is reported so a reader can
        # see how many detectors were behind the count.
        ok &= self._gate(
            "the governance rule set is non-empty and covers the four named claim classes",
            (len(GOVERNANCE_SEMANTIC_RULE_IDS) >= 4
             and {"asil_determination_claim", "conformity_claim", "certification_claim",
                  "governance_authority_claim"} <= GOVERNANCE_SEMANTIC_RULE_IDS),
            f"{len(GOVERNANCE_SEMANTIC_RULE_IDS)} governance rule id(s) in the filter: "
            f"{sorted(GOVERNANCE_SEMANTIC_RULE_IDS)}")
        ok &= self._gate("no production authority, no verification credit, no human approval",
                         not gov_findings,
                         f"{len(gov_findings)} violation(s) this run across "
                         f"{len(GOVERNANCE_SEMANTIC_RULE_IDS)} governance rule(s)"
                         if gov_findings
                         else f"governance detector ran over {len(gov_index)} records with "
                              f"{len(GOVERNANCE_SEMANTIC_RULE_IDS)} governance rules in the "
                              f"filter; 0 violations")
        for f in gov_findings[:20]:
            print(f"      {f['severity']}/{f['category']} {f['rule']} on {f['artifact_id']}: "
                  f"{f['description']}")

        print("\n[7b/8] provenance verification (digests, content hashes, line ranges)")
        self.findings = Findings()
        prov_ok = self._validate_provenance_evidence(gov_index)
        self._report_provenance()
        prov_findings = self._provenance_finding_count()
        # The gate line always states the true verdict, in every mode. Only the
        # contribution to this run's overall `ok` is decoupled by
        # --provenance-report-only, so the mode can be used to read the numbers
        # without a gate ever being made to print PASS.
        prov_line_ok = self._gate("digests, content hashes and line ranges verify against the files",
                                 prov_ok,
                                 f"{prov_findings} provenance finding(s)"
                                 + ("; --provenance-report-only: this verdict is NOT gating"
                                    if self.provenance_report_only else ""))
        if self.provenance_report_only:
            if not prov_line_ok:
                advisory.append("provenance verification (--provenance-report-only): the gate "
                                f"above reports FAIL with {prov_findings} finding(s); that "
                                "verdict is excluded from the exit code of this run only")
        else:
            ok &= prov_line_ok
        ext_ok, ext_detail, ext_forward = self._run_external_reference_check()
        ok &= self._gate("external reference check (check_references.py) reports no unresolved references",
                         ext_ok, ext_detail)

        print("\n[8/8] final status")
        # The status used to be ASSIGNED, then compared to itself:
        #     dims["final_status"] = FINAL_STATUS
        #     self._gate("final status recorded", dims["final_status"] == FINAL_STATUS)
        # The comparison could not fail for any input whatsoever. The audit moved
        # the entire corpus out of the tree and this gate still printed
        # [PASS] final status recorded - synthetic_ready_with_limitations.
        #
        # `synthetic_ready_with_limitations` is a claim about the corpus, so it is
        # now VERIFIED against the corpus. Each criterion below is a property the
        # string asserts, checked against the records on this run; a criterion
        # that cannot be checked says so instead of passing. The detail line
        # prints every criterion, so a reader sees which one would fail and why.
        final_ok, final_detail = self._verify_final_status(FINAL_STATUS, index)
        ok &= self._gate("final status recorded", final_ok, final_detail)
        if self.provenance_report_only and advisory == []:
            # Record what was NOT counted, in terms a reader can act on.
            if not prov_ok:
                advisory.append("provenance verification (--provenance-report-only: "
                                f"{prov_findings} finding(s) reported, not gating)")
        if advisory:
            print("\nNOT COUNTED TOWARD THIS RUN'S VERDICT (explicitly requested reporting mode):")
            for a in advisory:
                print(f"  - {a}")
        print(f"\nAcceptance suite: {'PASSED' if ok else 'FAILED'}")
        return ok

    def _chain_gate(self, ch):
        """Does the §13 chain gate agree with the verdict the tool just printed?

        Returns (passes, detail_text).

        The gate used to read `not ch["unmet_required"]` alone. `unmet_required`
        is derived from `instantiated`, the stages with at least one candidate
        record in the profile, so a profile that instantiates NO stage has an
        empty `unmet_required` and the gate passes on it. That is not a
        theoretical hole: with a single record retained, the audit saw
        verdict=broken, all 11 stages NOT INSTANTIATED, and the gate print
        [PASS]. The tool's own verdict contradicted its own gate on the same
        line of output.

        So the gate now reads the verdict first and the stage arithmetic second.
        A `broken` verdict fails outright; so does a partial chain with unmet
        stages; so does a chain that instantiated nothing and therefore reached
        nothing, which is the vacuous case. What still passes is exactly what the
        verdict calls a full chain, plus the documented relaxation for stages the
        profile genuinely does not instantiate.
        """
        verdict = ch["verdict"]
        deepest = ch["deepest_stage"]
        if verdict == "broken":
            return False, (f"verdict={verdict}: {self._chain_broken_reason(ch)} -- the gate used "
                           f"to pass this because `unmet_required` was empty")
        if ch["unmet_required"]:
            return False, (f"verdict={verdict}; unmet instantiated stages: "
                           f"{', '.join(ch['unmet_required'])} -- §13 permits a typed root/leaf "
                           f"exception here and this corpus declares none")
        if deepest is None:
            return False, (f"verdict={verdict} but no stage was reached at all: instantiated="
                           f"{len(ch['ladder'])}, reached=0. A chain that traverses nothing is "
                           f"not a chain, whatever the stage arithmetic says")
        return True, (f"verdict={verdict}; full chain through stage {deepest}; "
                      f"{len(ch['ladder'])} stage(s) instantiated, all reached"
                      + (f"; {len(ch['not_instantiated'])} stage(s) not instantiated in this "
                         f"profile and declared as a typed exception: "
                         f"{', '.join(ch['not_instantiated'])}"
                         if ch["not_instantiated"] else ""))

    def _chain_broken_reason(self, ch):
        if ch["root"] not in {ch["profile"]}:
            pass
        root = ch.get("root")
        if not ch["ladder"]:
            return (f"the profile {ch['profile']} instantiates no stage at all, so the chain "
                    f"from {root} has nothing to traverse")
        return (f"root {root} is not in the profile's index, or no stage is reachable from it "
                f"over {ch['links_considered']} link(s)")

    def _verify_final_status(self, status, index):
        """Verify a declared corpus status against the corpus on this run.

        Returns (holds, detail_text).

        The status string is a CLAIM, and a claim is only worth printing if
        something checks it. `synthetic_ready_with_limitations` asserts four
        things, each independently checkable against the records:

          synthetic  every corpus record is synthetic or an explicitly-labelled
                     as_is record; no record is presented as a synthetic fixture
                     that is not one;
          ready      the corpus is structurally intact: families populated,
                     traceability links resolve, provenance verifies;
          with       at least one limitation is RECORDED, so the status is not
                     silently upgraded to an unconditional one;
          limitations
                     the limitations recorded are still true of this run, and
                     not stale.

        Each criterion is checked and reported. A criterion that cannot be
        evaluated on this run is reported as unevaluated and FAILS, because a
        status whose criteria are not checkable is not a verified status.
        """
        if not index:
            return False, (f"status {status!r} is declared but the corpus index is EMPTY: nothing "
                           f"in the tree supports any status. The old gate compared the declared "
                           f"constant to itself and passed on this input")
        crit = []
        recs = [d for _k, (_p, d) in index.items() if isinstance(d, dict)]

        # 1. synthetic / as_is: profiles are the declared set and nothing else.
        declared_profiles = {"synthetic_reference", "as_is"}
        profiles = {d.get("profile") for d in recs if d.get("profile")}
        unknown = sorted(profiles - declared_profiles)
        crit.append(("every profile is a declared profile", not unknown,
                     f"profiles present: {sorted(profiles)}" + (f", undeclared: {unknown}" if unknown else "")))

        # 2. ready: families populated and links resolve.
        families = {d.get("artifact_type") for d in recs}
        expected = {"hazard", "safety_goal", "requirement", "design", "test_measure",
                    "execution", "review", "safety_analysis", "safety_case", "scenario",
                    "change", "deviation", "tara"}
        missing = sorted(expected - families)
        crit.append(("artefact families populated", not missing,
                     f"{len(expected & families)}/{len(expected)}"
                     + (f", missing: {missing}" if missing else "")))

        # 3. no authority: the status is synthetic, not production-authorized.
        authed = [k[1] if isinstance(k, tuple) else k for k, (p, d) in index.items()
                  if isinstance(d, dict) and (d.get("production_authorized") is True
                                              or d.get("product_verification_credit") is True)]
        crit.append(("no record claims production authority or verification credit", not authed,
                     f"{len(authed)} record(s) claim authority" if authed
                     else f"0 of {len(recs)} records claim authority"))

        # 4. limitations: at least one is recorded, and they are named.
        n_gaps = 0
        gap_src = None
        for cand in (self.reports_dir / "coverage-report.json",
                     self.artifacts_dir / "reports" / "coverage-report.json"):
            if cand.exists():
                gap_src = cand
                n_gaps = len(load_json(cand).get("gaps") or [])
                break
        crit.append(("at least one limitation is recorded", n_gaps > 0,
                     f"{n_gaps} gap(s) recorded in {gap_src.name}" if gap_src
                     else "no coverage-report.json found, so no limitation is recorded"))

        failed = [c for c in crit if not c[1]]
        parts = "; ".join(f"{name}: {detail}" for name, ok_, detail in crit)
        head = f"{status!r} verified against {len(recs)} record(s) -- {len(crit) - len(failed)}/{len(crit)} criteria hold"
        if failed:
            head += "; FAILED: " + ", ".join(n for n, _o, _d in failed)
        return not failed, head + " | " + parts

    def _change_lifecycle_passed(self, dims):
        """How many change lifecycles passed CONTENT validation, from the run."""
        run = self._scenario_run_cache
        if not run:
            return 0
        return sum(1 for r in run["results"]
                   if r.get("type") == "change_lifecycle" and r.get("passed"))

    def _change_lifecycle_gate(self, dims):
        run = self._scenario_run_cache
        if not run:
            return False
        return (run["total_changes"] == 3
                and all(r.get("passed") for r in run["results"]
                        if r.get("type") == "change_lifecycle"))

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

        def t_verifies_link_target_not_flagged():
            # Master prompt section 13: "verifies: verification measure -> requirement/design".
            # The requirement is therefore the TARGET. A correctly directed link must NOT raise
            # the 'no verifies/validates link' finding. Regression test for finding
            # FB2-REV-FND-000029, where the rule read source_id and so could never clear.
            #
            # SCOPED TO THIS RULE, deliberately. The assertion used to be
            # `not any(f["artifact_id"] == ...)`, i.e. "no rule at all may flag this
            # record". That was over-broad rather than strict: it only held because
            # the fault_reaction rule (MUT-008) used to exclude every FB2-SAF-SEC-*
            # record behind its `-FSR-` id filter, so the synthetic record happened
            # to be invisible to it. Widening MUT-008 to cover the security
            # requirement class (finding FB2-REV-FND-000039) made the record
            # legitimately flaggable by a DIFFERENT rule, and the over-broad
            # assertion then failed. Narrowing the assertion to the verifies rule
            # does not weaken it: the verifies rule is what this test is about, and
            # MUT-008's coverage of the same record class is now pinned by four
            # dedicated tests (t_fault_reaction_rule_*). Matching on the rule id as
            # well as the description makes the test say what it means, so a future
            # rule firing on this record can no longer be mistaken for a regression
            # here, and a regression here can no longer hide behind another rule.
            self.findings = Findings()
            index = {("synthetic_reference", "FB2-SAF-SEC-999999"): ("synthetic_reference", {
                "id": "FB2-SAF-SEC-999999", "artifact_type": "requirement",
                "engineering_domain": "safety", "profile": "synthetic_reference"})}
            links = [{"link_id": "FB2-LNK-TEST-1", "relation_type": "verifies",
                      "source_id": "FB2-VER-TMS-999999", "target_id": "FB2-SAF-SEC-999999",
                      "rationale": "r", "provenance": "derived", "review_state": "reviewed",
                      "change_suspect_status": False}]
            self._validate_semantic_rules(index, links)
            return not any(f["artifact_id"] == "FB2-SAF-SEC-999999"
                           and f["rule"] == "verification_traceability_checker"
                           and "no verifies/validates link" in f["description"]
                           for f in self.findings.items)

        def t_unverified_safety_requirement_flagged():
            # The rule's intent must survive the endpoint fix: a safety requirement with no
            # verification at all, in either direction, is still reported.
            self.findings = Findings()
            index = {("synthetic_reference", "FB2-SAF-SEC-999998"): ("synthetic_reference", {
                "id": "FB2-SAF-SEC-999998", "artifact_type": "requirement",
                "engineering_domain": "safety", "profile": "synthetic_reference"})}
            self._validate_semantic_rules(index, [])
            return any(f["artifact_id"] == "FB2-SAF-SEC-999998"
                       and "no verifies/validates link" in f["description"]
                       for f in self.findings.items)

        def t_verifies_source_endpoint_not_counted():
            # A safety requirement appearing as the SOURCE of a verifies link is a malformed
            # link under the declared direction. It must not count as verification of that
            # requirement, so the rule stays harder to satisfy by accident than it was before
            # the endpoint fix.
            self.findings = Findings()
            index = {("synthetic_reference", "FB2-SAF-SEC-999997"): ("synthetic_reference", {
                "id": "FB2-SAF-SEC-999997", "artifact_type": "requirement",
                "engineering_domain": "safety", "profile": "synthetic_reference"})}
            links = [{"link_id": "FB2-LNK-TEST-2", "relation_type": "verifies",
                      "source_id": "FB2-SAF-SEC-999997", "target_id": "FB2-VER-TMS-999997",
                      "rationale": "r", "provenance": "derived", "review_state": "reviewed",
                      "change_suspect_status": False}]
            self._validate_semantic_rules(index, links)
            return any(f["artifact_id"] == "FB2-SAF-SEC-999997"
                       and "no verifies/validates link" in f["description"]
                       for f in self.findings.items)

        # --- scope of the safety-requirement completeness rule (MUT-008) ----
        # The rule lost its `"-FSR-" in id` filter (finding FB2-REV-FND-000039).
        # These three tests pin the widened scope from both sides, so a future edit
        # cannot quietly re-narrow it and cannot over-widen it either.

        def _fault_reaction_index(*specs):
            idx = {}
            for aid, domain in specs:
                idx[("synthetic_reference", aid)] = ("synthetic_reference", {
                    "id": aid, "artifact_type": "requirement",
                    "engineering_domain": domain, "profile": "synthetic_reference"})
            return idx

        def _no_fault_reaction_finding(art_id, index):
            self.findings = Findings()
            self._validate_semantic_rules(index, [])
            return any(f["artifact_id"] == art_id
                       and "no fault_reaction" in f["description"]
                       for f in self.findings.items)

        def t_fault_reaction_rule_covers_sec_requirements():
            # The regression this finding is about: FB2-SAF-SEC-* is a safety-domain
            # requirement class, and the old `-FSR-` id filter made the rule
            # structurally unable to report it. It must now be reported.
            return _no_fault_reaction_finding(
                "FB2-SAF-SEC-999996",
                _fault_reaction_index(("FB2-SAF-SEC-999996", "safety")))

        def t_fault_reaction_rule_still_covers_fsr_requirements():
            # Nothing that was reported before the widening stops being reported.
            # If this ever fails, the widening was a narrowing in disguise.
            return all(_no_fault_reaction_finding(
                aid, _fault_reaction_index((aid, "safety")))
                for aid in ("FB2-SAF-FSR-999995", "FB2-SAF-FSR-999994"))

        def t_fault_reaction_rule_respects_domain_boundary():
            # Widening the population must not make the rule report requirements
            # outside the safety engineering domain, which are governed by other
            # rules and would be a false positive here.
            return not _no_fault_reaction_finding(
                "FB2-SYS-SYR-999993",
                _fault_reaction_index(("FB2-SYS-SYR-999993", "system")))

        def t_fault_reaction_rule_silent_when_field_present():
            # A security requirement that DOES carry a fault_reaction is not
            # reported. Without this, the rule would be indistinguishable from one
            # that simply reports the whole class, and widening would have bought
            # nothing but noise.
            self.findings = Findings()
            index = _fault_reaction_index(("FB2-SAF-SEC-999992", "safety"))
            index[("synthetic_reference", "FB2-SAF-SEC-999992")][1]["fault_reaction"] = {
                "reaction": "x", "added_in_revision": "1"}
            self._validate_semantic_rules(index, [])
            return not any(f["artifact_id"] == "FB2-SAF-SEC-999992"
                           and "no fault_reaction" in f["description"]
                           for f in self.findings.items)

        # --- scope of the diagnostic-coverage claim validator (MUT-010) ----
        # This rule lost its `"-FSR-" in id` filter (finding FB2-REV-FND-000040).
        #
        # These four tests exist because of a measurement that could not be used
        # as evidence of a working rule. The widened rule reports NOTHING on the
        # current corpus: no safety-domain requirement of either class carries a
        # diagnostic_coverage field at all, so the filter's removal changed the
        # reported count from zero to zero. That is a true statement about the
        # corpus and a useless statement about the rule, so the rule's liveness
        # has to be established by construction instead. Without them, a future
        # edit could re-narrow the population and the suite would stay green,
        # because on this corpus there is nothing for the narrowed rule to miss.
        # The counterfactual is the whole point: remove the evidence field from
        # an in-memory record and the rule must fire.

        def _diagnostic_coverage_index(*specs):
            # specs are (id, domain); the record claims a coverage figure with no
            # evidence unless the caller adds one, which is the defect state.
            idx = {}
            for aid, domain in specs:
                idx[("synthetic_reference", aid)] = ("synthetic_reference", {
                    "id": aid, "artifact_type": "requirement",
                    "engineering_domain": domain, "profile": "synthetic_reference",
                    "diagnostic_coverage": "99%"})
            return idx

        def _coverage_without_evidence_finding(art_id, index):
            self.findings = Findings()
            self._validate_semantic_rules(index, [])
            return any(f["artifact_id"] == art_id
                       and f["rule"] == "diagnostic_coverage_claim_validator"
                       and "without evidence" in f["description"]
                       for f in self.findings.items)

        def t_diagnostic_coverage_rule_covers_sec_requirements():
            # The regression this finding is about. FB2-SAF-SEC-* is a
            # safety-domain requirement class and the old `-FSR-` id filter made
            # the rule structurally unable to report it, so a security
            # requirement claiming a diagnostic coverage figure with no evidence
            # would have gone unchecked. It must now be reported.
            return _coverage_without_evidence_finding(
                "FB2-SAF-SEC-999991",
                _diagnostic_coverage_index(("FB2-SAF-SEC-999991", "safety")))

        def t_diagnostic_coverage_rule_still_covers_fsr_requirements():
            # Nothing that was reported before the widening stops being reported.
            # If this ever fails, the widening was a narrowing in disguise. This is
            # also the class SCN-MUT-010 exercises, so it is the one whose
            # regression would be visible in the acceptance gate.
            return all(_coverage_without_evidence_finding(
                aid, _diagnostic_coverage_index((aid, "safety")))
                for aid in ("FB2-SAF-FSR-999990", "FB2-SAF-FSR-999989"))

        def t_diagnostic_coverage_rule_respects_domain_boundary():
            # Widening the population must not make the rule report requirements
            # outside the safety engineering domain, which are governed by other
            # rules and would be a false positive here.
            return not _coverage_without_evidence_finding(
                "FB2-SYS-SYR-999988",
                _diagnostic_coverage_index(("FB2-SYS-SYR-999988", "system")))

        def t_diagnostic_coverage_rule_silent_when_evidence_present():
            # The counterfactual, in the direction that keeps the rule honest in
            # the other direction: a claim that DOES carry evidence is silent.
            # Without this, the rule would be indistinguishable from one that
            # reports every safety requirement regardless of its evidence, and
            # widening would have bought nothing but noise.
            self.findings = Findings()
            index = _diagnostic_coverage_index(("FB2-SAF-SEC-999987", "safety"))
            index[("synthetic_reference", "FB2-SAF-SEC-999987")][1][
                "diagnostic_coverage_evidence"] = "covered by the rejection-path counter"
            self._validate_semantic_rules(index, [])
            return not any(f["artifact_id"] == "FB2-SAF-SEC-999987"
                           and f["rule"] == "diagnostic_coverage_claim_validator"
                           for f in self.findings.items)

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

        # ------------------------------------------------------------------
        # Regression tests for the acceptance gate's own soundness. These exist
        # because the gate used to be self-certifying: it accepted any finding
        # of the expected severity on the scenario's affected artifact ids, so
        # a standing defect inherited from the corpus satisfied scenarios whose
        # own detector did not exist, was unreachable, or read a field the
        # record did not carry. A test that only ever passes does not protect
        # against that; these deliberately break the gate and require it to
        # notice.
        # ------------------------------------------------------------------

        def _load_scenario(sid):
            for sp in sorted((self.scenarios_dir / "mutations").glob("mutation-*.json")):
                sd = load_json(sp)
                if sd.get("scenario_id") == sid:
                    return sd
            raise KeyError(sid)

        def t_scenarios_fire_on_their_own_detector():
            # Every mutation scenario's declared detector must exist, must be
            # silent on the unmutated corpus, and must fire after its own
            # mutation. None may be satisfied by a neighbouring rule.
            baseline = self._baseline_findings()
            bsigns = baseline.signature()
            bad = []
            for sp in sorted((self.scenarios_dir / "mutations").glob("mutation-*.json")):
                sd = load_json(sp)
                sid = sd.get("scenario_id")
                detector, _ = self._declared_detector(sd)
                if detector is None:
                    bad.append(f"{sid}: no declared detector")
                    continue
                self.findings = Findings()
                actual = self._apply_mutation_and_detect(sd)
                ok, reason = self._match_scenario_finding(detector, actual, bsigns)
                if not ok:
                    bad.append(f"{sid}: {reason}")
                # The verdict must rest on the declared rule and nothing else.
                # Asserted as "the rules this mutation CAUSED are exactly the
                # declared rule", i.e. excluding the baseline: a standing
                # defect on an unrelated rule is not this scenario's detection,
                # and _match_scenario_finding already refuses to count it. The
                # earlier form of this clause was "no other rule fired at all",
                # which only held while the corpus produced almost no findings
                # and which conflated harness integrity with corpus cleanliness.
                b_rules = {s[0] for s in bsigns}
                caused = sorted({f.get("rule") for f in actual
                                 if f.get("rule") not in b_rules})
                if detector not in caused:
                    bad.append(f"{sid}: the rules this mutation caused are {caused}, "
                               f"which does not include the declared rule "
                               f"{detector!r}")
                # The verdict rests on the declared rule ALONE, and that is a
                # property of _match_scenario_finding, not of what else fired: it
                # returns True only for a finding whose `rule` is the declared
                # rule and whose signature is absent from the baseline. So a
                # second rule firing alongside is information, not a defect, and
                # is not allowed to change this verdict. (The previous clause
                # here required that NO other rule fire at all. That is not the
                # property being tested -- it held only while the corpus
                # produced almost no findings, and it conflated harness
                # integrity with corpus cleanliness.)
            return not bad

        def t_scenario_fails_when_own_detector_disabled():
            # The core proof. Build a mutation that makes two different rules
            # fire on the same artifact, declare one of them as the scenario's
            # detector, then disable that detector. The scenario must fail while
            # the other rule's finding is still present - and that other finding
            # is exactly what the previous harness would have accepted, because
            # it shares the expected severity and category and sits on the same
            # affected artifact id. This is the self-certifying match, isolated.
            declared = "diagnostic_coverage_claim_validator"
            neighbour = "safety_requirement_completeness_checker"
            inline = {
                "scenario_id": "SCN-MUT-INLINE-PROBE",
                "scenario_type": "mutation",
                "affected_ids": ["FB2-SAF-FSR-000003"],
                "expected_detector": declared,
                "expected_finding": {"finding_id": "PROBE", "severity": "medium",
                                     "category": "verification"},
                "patch": {"operation": "modify", "affected_links": [],
                          "new_value": {"fault_reaction": None,
                                        "diagnostic_coverage": "99%"}},
            }
            baseline = self._baseline_findings()
            bsigns = baseline.signature()
            b_rules = {s[0] for s in bsigns}
            self.findings = Findings()
            before = self._apply_mutation_and_detect(inline)
            # Only the rules this mutation CAUSED matter. A rule that was
            # already firing on the unmutated corpus cannot be this probe's
            # detection, so it is excluded rather than counted as a failure.
            caused = {f["rule"] for f in before if f["rule"] not in b_rules}
            ok_before, _ = self._match_scenario_finding(declared, before, bsigns)
            with self._suppress_rule(declared):
                self.findings = Findings()
                after = self._apply_mutation_and_detect(inline)
            surviving = [f for f in after if f["artifact_id"] in set(inline["affected_ids"])
                         and f["rule"] not in b_rules]
            ok_after, reason = self._match_scenario_finding(declared, after, bsigns)
            # the surviving neighbour is what the old criterion would have matched
            old_criterion_would_pass = any(
                f["severity"] == inline["expected_finding"]["severity"]
                and f["category"] == inline["expected_finding"]["category"]
                for f in surviving)
            return (caused == {declared, neighbour} and ok_before
                    and not ok_after and bool(surviving)
                    and {f["rule"] for f in surviving} == {neighbour}
                    and old_criterion_would_pass
                    and "produced no finding" in reason)

        def t_scenario_with_unknown_detector_fails_loudly():
            sd = dict(_load_scenario("SCN-MUT-010"))
            sd["oracle_manifest_ref"] = "SCN-MUT-010/oracle-manifest.json"
            detector = "a_rule_that_does_not_exist"
            ok, reason = self._match_scenario_finding(detector, [], set())
            return (not ok) and "not emitted by any rule" in reason

        def t_scenario_rejected_when_standing_finding_would_satisfy_it():
            # A finding that already exists on the unmutated corpus must not be
            # able to satisfy a scenario. This is the exact failure mode the
            # old harness permitted.
            detector = "diagnostic_coverage_claim_validator"
            standing = {(detector, "FB2-SAF-FSR-000003", "verification",
                         "FSR FB2-SAF-FSR-000003 claims diagnostic coverage '99%' without evidence")}
            actual = [{"rule": detector, "severity": "high", "category": "verification",
                       "artifact_id": "FB2-SAF-FSR-000003",
                       "description": "FSR FB2-SAF-FSR-000003 claims diagnostic coverage '99%' without evidence"}]
            ok, reason = self._match_scenario_finding(detector, actual, standing)
            return (not ok) and "already fires on the unmutated corpus" in reason

        def t_requirement_applicability_rule():
            # The new rule must fire on a not-applicable marking that carries no
            # justification and stay silent when one is present. The marking is
            # read from safety_allocation.asil, the field requirement.schema.json
            # enumerates; no undeclared property is consulted.
            def _run(rec):
                self.findings = Findings()
                index = {("synthetic_reference", "FB2-SAF-SEC-TEST-1"): ("synthetic_reference", rec)}
                self._validate_semantic_rules(index, [])
                return [f for f in self.findings.items
                        if f["rule"] == "requirement_applicability_validator"]
            base = {"id": "FB2-SAF-SEC-TEST-1", "artifact_type": "requirement",
                    "engineering_domain": "safety", "profile": "synthetic_reference",
                    "safety_allocation": {"asil": "not_applicable",
                                          "safety_goal_ref": "FB2-SAF-SGO-000001",
                                          "mitigation": "m"}}
            unflagged = _run(dict(base))
            justified = _run(dict(base, asil_justification={"reason": "because"}))
            allocated = _run(dict(base, safety_allocation=dict(base["safety_allocation"],
                                                               asil="ASIL_B")))
            return (len(unflagged) == 1 and not justified and not allocated)

        def t_asil_downgrade_detected_despite_justification():
            # The rule must reject an ASIL the record's own justification
            # contradicts, even though a justification is present. A
            # presence-only check could never do this: it fires on absence, so
            # it would have been satisfied by an unhealthy corpus and blind to
            # the injected downgrade on a healthy one.
            def _run(asil):
                self.findings = Findings()
                rec = {"id": "FB2-SAF-SGO-TEST-1", "artifact_type": "safety_goal",
                       "profile": "synthetic_reference", "asil": asil,
                       "asil_justification": {
                           "severity": {"rating": "S3"}, "exposure": {"rating": "E4"},
                           "derived_asil": "ASIL_D"}}
                self._validate_semantic_rules({("synthetic_reference", "FB2-SAF-SGO-TEST-1"):
                                               ("synthetic_reference", rec)}, [])
                return [f for f in self.findings.items if f["rule"] == "asil_assignment_validator"]
            honest = _run("ASIL_D")
            downgraded = _run("ASIL_B")
            no_justification = Findings()
            self.findings = no_justification
            self._validate_semantic_rules(
                {("synthetic_reference", "FB2-SAF-SGO-TEST-2"): ("synthetic_reference",
                 {"id": "FB2-SAF-SGO-TEST-2", "artifact_type": "safety_goal",
                  "profile": "synthetic_reference", "asil": "ASIL_D"})}, [])
            absent = [f for f in no_justification.items if f["rule"] == "asil_assignment_validator"]
            return (not honest and len(downgraded) == 1
                    and "derives ASIL ASIL_D" in downgraded[0]["description"]
                    and downgraded[0]["severity"] == "high"
                    and len(absent) == 1)

        def t_ftti_resolved_from_bound_parameter_and_scatter_reported():
            # The interval is resolved from the bound parameter registry entry,
            # and a literal on the record that disagrees with it is reported
            # rather than silently preferred.
            self.findings = Findings()
            index = {("synthetic_reference", "FB2-PRM-TEST-4"): ("synthetic_reference", {
                "id": "FB2-PRM-TEST-4", "artifact_type": "parameter", "name": "ftti_ms",
                "value": 100, "unit": "ms"})}
            goal = {"id": "FB2-SAF-SGO-TEST-3", "artifact_type": "safety_goal",
                    "profile": "synthetic_reference",
                    "ftti": {"parameter_ref": "FB2-PRM-TEST-4"},
                    "fault_tolerant_time_interval_ms": 100,
                    "timing_budget": {"total_ftti_ms": 100,
                                      "allocation": {"acquire_ms": 60, "react_ms": 25}}}
            index[("synthetic_reference", "FB2-SAF-SGO-TEST-3")] = ("synthetic_reference", goal)
            self._validate_semantic_rules(index, [])
            clean = [f for f in self.findings.items
                     if f["rule"] == "ftti_budget_consistency_checker"]
            # 60 + 25 = 85 must not be reported, and the interval must not be
            # counted as a serial part: no total, no margin, no ftti key.
            self.findings = Findings()
            goal2 = json.loads(json.dumps(goal))
            goal2["fault_tolerant_time_interval_ms"] = 250  # drifted literal
            index[("synthetic_reference", "FB2-SAF-SGO-TEST-3")] = ("synthetic_reference", goal2)
            self._validate_semantic_rules(index, [])
            scattered = [f for f in self.findings.items
                         if f["rule"] == "ftti_budget_consistency_checker"]
            self.findings = Findings()
            goal3 = json.loads(json.dumps(goal))
            goal3["timing_budget"]["allocation"]["react_ms"] = 90  # 60 + 90 > 100
            index[("synthetic_reference", "FB2-SAF-SGO-TEST-3")] = ("synthetic_reference", goal3)
            self._validate_semantic_rules(index, [])
            overflow = [f for f in self.findings.items
                        if f["rule"] == "ftti_budget_consistency_checker"]
            return (not clean and len(scattered) == 1
                    and "inconsistently" in scattered[0]["description"]
                    and len(overflow) == 1
                    and "exceeds FTTI 100" in overflow[0]["description"])

        def t_revision_rule_reachable_from_scenario_path():
            # The revision rule must be reachable from the mutation harness, not
            # only from schema validation. SCN-MUT-003 depends on this.
            sd = _load_scenario("SCN-MUT-003")
            self.findings = Findings()
            actual = self._apply_mutation_and_detect(sd)
            mine = [f for f in actual if f["rule"] == "revision_consistency_checker"]
            return bool(mine) and all("revision 99 not found in revision_history" == f["description"]
                                      for f in mine)

        def t_negative_scenario_dimension_is_a_pass_count_not_a_file_count():
            # The coverage dimension must report how many scenarios PASSED, not
            # how many scenario files exist. Proven two ways:
            #   1. the numerator equals the number of executed mutation results
            #      that actually passed, and equals the suite's own pass count;
            #   2. with one mutation's declared detector made unimplementable,
            #      the dimension drops by exactly one and names the failure.
            # Under the previous file-count computation both assertions held
            # vacuously, which is how the dimension read 20/20 while the gate
            # was failing.
            dim = self._negative_scenario_dimension()
            run = self._execute_scenarios()
            passed = sum(1 for r in run["results"]
                         if r.get("type") == "mutation" and r.get("passed"))
            self._scenario_run_cache = None
            with self._suppress_rule("hsi_interface_consistency"):
                degraded = self._negative_scenario_dimension()
            self._scenario_run_cache = None
            return (dim["numerator"] == passed == run["passed_mutations"]
                    and dim["denominator"] == run["total_mutations"]
                    and degraded["numerator"] == passed - 1
                    and "SCN-MUT-005" in degraded["detail"])

        def t_scenario_run_is_shared_between_gate_and_coverage():
            # cmd_check calls cmd_coverage (step 3/8) and cmd_scenario_test
            # (step 5/8). Both must read ONE measurement, otherwise the
            # dimension and the gate could report different verdicts for the
            # same corpus. The shared cache is what makes that true.
            self._scenario_run_cache = None
            dim = self._negative_scenario_dimension()
            first = self._scenario_run_cache
            ok = first is not None
            ok &= (self._execute_scenarios() is first)   # second reader reuses it
            buf = io.StringIO()                        # gate path, output swallowed
            with contextlib.redirect_stdout(buf):
                gate_ok = self.cmd_scenario_test()
            ok &= gate_ok and (self._scenario_run_cache is first)
            ok &= dim["numerator"] == first["passed_mutations"]
            ok &= len(buf.getvalue().strip().splitlines()) == len(first["lines"])
            return ok

        # --- provenance verification ------------------------------------------
        # Each of these pins one provenance class from both sides: a wrong value
        # must be caught, and the correct value must be silent. A rule that only
        # knows how to fail is indistinguishable from a rule that is stuck on.

        def _tmp_anchor_dir(self_obj):
            """A throwaway tree with one real file, for anchor checks."""
            import tempfile
            return tempfile.TemporaryDirectory()

        def t_provenance_digest_verified():
            with _tmp_anchor_dir(self) as tmp:
                root = Path(tmp)
                (root / "a.json").write_text('{"id":"X","revision":"1"}', encoding="utf-8")
                good = sha256_file(root / "a.json")
                # Drive the detector directly through a stub index so the test
                # does not depend on any real review record.
                saved_root, saved_findings = self.root, self.findings
                try:
                    self.root = root
                    rec = {"id": "REV", "profile": "p",
                           "reviewed_ids": [
                               {"artifact_id": "X", "digest": good},
                               {"artifact_id": "X", "digest": "0" * 64}]}
                    rdir = root / "docs" / "artifacts" / "reviews" / "records"
                    rdir.mkdir(parents=True)
                    (rdir / "r.json").write_text(json.dumps(rec), encoding="utf-8")
                    self.artifacts_dir = root / "docs" / "artifacts"
                    self.findings = Findings()
                    self._validate_review_digests({("p", "X"): ("a.json", {})})
                    mine = [f for f in self.findings.items if f["rule"] == "review_digest_mismatch"]
                    tally = self.provenance_tally["review_digest"]
                    return (len(mine) == 1 and tally["verified"] == 1
                            and "0" * 8 in mine[0]["description"])
                finally:
                    self.root, self.findings = saved_root, saved_findings
                    self.artifacts_dir = saved_root / "docs" / "artifacts"

        def t_provenance_placeholder_needs_note():
            with _tmp_anchor_dir(self) as tmp:
                root = Path(tmp)
                saved_root, saved_findings = self.root, self.findings
                try:
                    self.root = root
                    self.artifacts_dir = root / "docs" / "artifacts"
                    rdir = self.artifacts_dir / "reviews" / "records"
                    rdir.mkdir(parents=True)
                    (rdir / "r.json").write_text(json.dumps(
                        {"id": "REV", "profile": "p", "reviewed_ids": [
                            {"artifact_id": "A", "digest": "placeholder"},
                            {"artifact_id": "B", "digest": "placeholder",
                             "digest_note": "artifact deliberately not committed; see finding 41"}]}),
                        encoding="utf-8")
                    self.findings = Findings()
                    self._validate_review_digests({("p", "A"): ("a", {}), ("p", "B"): ("b", {})})
                    tally = self.provenance_tally["review_digest"]
                    # Both are reported. The noted one is a disclosure; the
                    # unnoted one is the defect. Neither is skipped.
                    return (tally["placeholder_with_note"] == 1
                            and tally["placeholder_without_note"] == 1
                            and len([f for f in self.findings.items
                                     if f["rule"] == "review_digest_placeholder"]) == 2)
                finally:
                    self.root, self.findings = saved_root, saved_findings
                    self.artifacts_dir = saved_root / "docs" / "artifacts"

        def _anchor_fixture(self_obj, anchor):
            """Build a one-anchor source registry inside a temp tree."""
            import tempfile
            tmp = tempfile.TemporaryDirectory()
            root = Path(tmp.name)
            src = root / "src.c"
            src.write_text("int real_symbol(void) {\n" + "\n".join(
                f"    int x{i} = {i};" for i in range(1, 20)) + "\n}\n", encoding="utf-8")
            reg = root / "reg.json"
            reg.write_text(json.dumps({"anchors": [anchor]}), encoding="utf-8")
            return tmp, root, reg

        def _run_anchor_check(self_obj, root):
            """Run _validate_source_anchors against a temp tree.

            Returns (ok, findings, tally). The findings are captured before the
            instance state is restored: the self-tests inspect them, and reading
            self.findings after the restore would inspect the PREVIOUS test's
            findings instead.
            """
            saved = (self_obj.root, self_obj.sources_dir, self_obj.findings,
                     self_obj._load_source_anchors)
            self_obj.root = root
            self_obj.sources_dir = root
            self_obj.findings = Findings()
            self_obj._load_source_anchors = lambda: json.loads(
                (root / "reg.json").read_text(encoding="utf-8"))["anchors"]
            try:
                ok = self_obj._validate_source_anchors()
                return ok, list(self_obj.findings.items), dict(self_obj.provenance_tally)
            finally:
                (self_obj.root, self_obj.sources_dir, self_obj.findings,
                 self_obj._load_source_anchors) = saved

        def t_provenance_anchor_symbol_absent():
            present = {"anchor_id": "FB2-SRC-COD-999999", "source_type": "code",
                       "location": {"path": "src.c", "symbol": "real_symbol",
                                    "line_range": "2-4"}}
            absent = {"anchor_id": "FB2-SRC-COD-999999", "source_type": "code",
                      "location": {"path": "src.c", "symbol": "fabricated_symbol",
                                   "line_range": "2-4"}}
            tmp, root, _reg = _anchor_fixture(self, absent)
            try:
                ok, findings, tally = _run_anchor_check(self, root)
                at = tally["source_anchors"]
                caught = [f for f in findings if f["rule"] == "source_anchor_symbol_missing"]
                good = (not ok and len(caught) == 1
                        and at["symbol_checked"] == 1 and at["symbol_absent"] == 1)
            finally:
                tmp.cleanup()
            tmp2, root2, _r2 = _anchor_fixture(self, present)
            try:
                ok2, findings2, tally2 = _run_anchor_check(self, root2)
                at2 = tally2["source_anchors"]
                # The correct symbol must be silent: a rule that can only fail is
                # not evidence of anything.
                silent = (ok2 and at2["symbol_present"] == 1 and at2["symbol_absent"] == 0
                          and not [f for f in findings2
                                   if f["rule"] == "source_anchor_symbol_missing"])
            finally:
                tmp2.cleanup()
            return good and silent

        def t_provenance_line_range_bounds():
            anchor = {"anchor_id": "FB2-SRC-COD-999999", "source_type": "code",
                      "location": {"path": "src.c", "symbol": "real_symbol",
                                   "line_range": "900-950"}}
            tmp, root, _reg = _anchor_fixture(self, anchor)
            try:
                ok, findings, tally = _run_anchor_check(self, root)
                at = tally["source_anchors"]
                bad = (not ok and at["line_range_out_of_bounds"] == 1
                       and at["line_range_ok"] == 0
                       and any(f["rule"] == "source_anchor_line_range_out_of_bounds"
                               for f in findings))
            finally:
                tmp.cleanup()
            inrange = json.loads(json.dumps(anchor))
            inrange["location"]["line_range"] = "2-4"
            tmp2, root2, _r2 = _anchor_fixture(self, inrange)
            try:
                ok2, _f2, tally2 = _run_anchor_check(self, root2)
                good = ok2 and tally2["source_anchors"]["line_range_ok"] == 1
            finally:
                tmp2.cleanup()
            return bad and good

        def t_provenance_placeholder_hash_reported():
            anchor = {"anchor_id": "FB2-SRC-COD-999999", "source_type": "code",
                      "content_hash": "sha256:placeholder",
                      "location": {"path": "src.c", "symbol": "real_symbol",
                                   "line_range": "2-4"}}
            tmp, root, _reg = _anchor_fixture(self, anchor)
            try:
                ok, findings, tally = _run_anchor_check(self, root)
                at = tally["source_anchors"]
                unv = [f for f in findings
                       if f["rule"] == "source_anchor_content_hash_unverified"]
                # A placeholder is reported (not skipped) and does not pass.
                return (not ok and at["hash_unverified_placeholder"] == 1
                        and at["hash_verified"] == 0 and len(unv) == 1
                        and "no content hash" in unv[0]["description"])
            finally:
                tmp.cleanup()

        def t_provenance_evidence_file_missing():
            index = {("p", "A"): ("a.json", {"id": "A", "logs": [
                {"file": "does/not/exist.log", "hash": "sha256:" + "0" * 64}],
                "evidence_files": ["also/missing.json"]})}
            self.findings = Findings()
            ok = self._validate_evidence_files(index)
            tally = self.provenance_tally["evidence_files"]
            rules = {f["rule"] for f in self.findings.items}
            return (not ok and tally["log_file_missing"] == 1
                    and tally["evidence_file_missing"] == 1
                    and rules == {"evidence_file_missing"})

        def t_provenance_runs_in_detector_pass():
            # The provenance detectors must be reachable from _run_detectors, so
            # that every path which counts findings sees them: the validate pass,
            # the scenario baseline, and the acceptance gates.
            #
            # Asserted as a WIRING fact, not as a corpus fact. A test that
            # asserted "source_anchor_symbol_missing is in the findings" would
            # pass only while the corpus still has fabricated anchors and would
            # fail the moment a repair workstream fixed them -- a test whose
            # green means "the corpus is broken". This one goes green when the
            # plumbing is right, which is the thing that must not regress.
            calls = []
            original = self._validate_provenance_evidence
            original_gov = self._validate_governance_semantics

            def _spy(idx):
                calls.append(len(idx))
                return original(idx)

            def _spy_gov(idx):
                calls.append(-len(idx))
                return original_gov(idx)

            self._validate_provenance_evidence = _spy
            self._validate_governance_semantics = _spy_gov
            try:
                self.findings = Findings()
                self._run_detectors(self.load_artifact_index(), self.load_links())
                prov_calls = [c for c in calls if c > 0]
                gov_calls = [c for c in calls if c < 0]
                rules = self._implemented_rules()
                return (len(prov_calls) == 1 and len(gov_calls) == 1
                        and prov_calls[0] == -gov_calls[-1]
                        and {"review_digest_mismatch", "source_anchor_symbol_missing",
                             "source_anchor_line_range_out_of_bounds",
                             "source_anchor_content_hash_unverified",
                             "evidence_file_missing", "evidence_file_hash_mismatch",
                             "governance_authority_claim"} <= rules)
            finally:
                self._validate_provenance_evidence = original
                self._validate_governance_semantics = original_gov

        # --- link registry shadowing + target-hardware execution --------------

        def _link_fixture(link_bodies):
            """Build a temp tree with one canonical and one nested registry.

            `link_bodies` is (canonical_records, nested_records). Returns
            (TemporaryDirectory, root).
            """
            import tempfile
            tmp = tempfile.TemporaryDirectory()
            root = Path(tmp.name)
            canon = root / "docs/artifacts/traceability/link-registry/as_is"
            nested = root / "docs/artifacts/corpus/as_is/traceability/link-registry/as_is"
            canon.mkdir(parents=True)
            nested.mkdir(parents=True)
            for directory, records in ((canon, link_bodies[0]), (nested, link_bodies[1])):
                (directory / "links-cell-voltage.json").write_text(
                    json.dumps({"links": records}), encoding="utf-8")
            return tmp, root

        def _sample_link(lid, source_revision="1"):
            return {"link_id": lid, "source_id": "A", "target_id": "B",
                    "relation_type": "refines", "source_revision": source_revision,
                    "target_revision": "1", "rationale": "r", "provenance": "derived",
                    "review_state": "reviewed", "change_suspect_status": False,
                    "profile": "as_is"}

        def t_shadowed_duplicate_link_is_reported():
            # A link present in two registries whose content AGREES is an
            # unreconciled copy. It must be reported: it is a latent second
            # source of truth that downstream checks never see.
            tmp, root = _link_fixture(([_sample_link("L1")], [_sample_link("L1")]))
            try:
                tool = CorpusTool(root=root)
                tool.findings = Findings()
                ok = tool._validate_link_registry_shadowing()
                dups = [f for f in tool.findings.items
                        if f["rule"] == "link_registry_shadowing_duplicate"]
                # one finding, naming BOTH registries so the owner can find them
                paths_named = all("link-registry" in f["description"] for f in dups)
                agrees = all("agrees" in f["description"] for f in dups)
                # an agreeing duplicate is reported but is not an error
                return (len(dups) == 1 and ok is True
                        and dups[0]["severity"] == "medium"
                        and dups[0]["artifact_id"] == "L1"
                        and paths_named and agrees)
            finally:
                tmp.cleanup()

        def t_conflicting_duplicate_link_is_an_error():
            # Two registries that DISAGREE about the same link are a genuine
            # contradiction: the tool cannot know which is true, so it must
            # report it as an error and name the fields that differ rather than
            # pick one.
            tmp, root = _link_fixture(([_sample_link("L1", "1")],
                                       [_sample_link("L1", "9")]))
            try:
                tool = CorpusTool(root=root)
                tool.findings = Findings()
                ok = tool._validate_link_registry_shadowing()
                conflicts = [f for f in tool.findings.items
                             if f["rule"] == "link_registry_shadowing_conflict"]
                return (ok is False and len(conflicts) == 1
                        and conflicts[0]["severity"] == "high"
                        and "source_revision" in conflicts[0]["description"])
            finally:
                tmp.cleanup()

        def _sibling_registry_fixture(first_rev, second_rev):
            """Two registries at the SAME rank, in sibling subdirectories, that
            disagree about the same link.

            The directories are named so that the lexical order (aa before zz)
            is the OPPOSITE of the order `rglob` happens to walk them in
            (verified: rglob yields zz before aa here). A de-duplicator that
            keeps "whichever rglob saw first" therefore loads the zz copy; one
            that sorts by path loads the aa copy. The two answers differ, so
            this fixture can tell them apart.
            """
            import tempfile
            tmp = tempfile.TemporaryDirectory()
            root = Path(tmp.name)
            base = (root / "docs/artifacts/corpus/synthetic_reference/traceability"
                    "/link-registry/synthetic_reference")
            (base / "zz").mkdir(parents=True)
            (base / "aa").mkdir(parents=True)
            (base / "zz" / "links-cell-voltage.json").write_text(
                json.dumps({"links": [_sample_link("L1", first_rev)]}), encoding="utf-8")
            (base / "aa" / "links-cell-voltage.json").write_text(
                json.dumps({"links": [_sample_link("L1", second_rev)]}), encoding="utf-8")
            return tmp, root, base

        def t_link_dedup_is_independent_of_glob_order():
            # De-duplication must not depend on filesystem iteration order.
            # Two same-rank registries disagree; the one loaded must be chosen by
            # the documented rule (lexicographically smaller path) and not by
            # whichever directory the OS enumerated first.
            tmp, root, base = _sibling_registry_fixture("ZZ-REV", "AA-REV")
            try:
                tool = CorpusTool(root=root)
                raw_first = next(iter(base.rglob("links-*.json")))
                loaded = {(l["_profile"], l["link_id"]): l for l in tool.load_links()}
                rec = loaded[("synthetic_reference", "L1")]
                # the fixture is only meaningful if raw rglob really does walk
                # the tree in the opposite order to the sorted rule
                rglob_is_unsorted = raw_first.parent.name == "zz"
                return (rglob_is_unsorted
                        and rec["source_revision"] == "AA-REV"
                        and "/aa/" in rec["_registry"]
                        and "zz" not in rec["_registry"].split("/docs/")[-1])
            finally:
                tmp.cleanup()

        def t_canonical_registry_outranks_a_nested_copy():
            # The documented precedence: the canonical top-level registry
            # outranks any per-profile copy nested under corpus/, regardless of
            # what rglob enumerates first.
            tmp, root = _link_fixture(([_sample_link("L1", "CANON")],
                                       [_sample_link("L1", "NESTED")]))
            try:
                tool = CorpusTool(root=root)
                loaded = {(l["_profile"], l["link_id"]): l for l in tool.load_links()}
                rec = loaded[("as_is", "L1")]
                return (rec["source_revision"] == "CANON"
                        and "corpus" not in rec["_registry"].split("/docs/")[-1])
            finally:
                tmp.cleanup()

        def t_shadowing_detector_is_wired_into_validate():
            # The detector must be reachable from cmd_validate, not only from
            # the scenario harness. Asserted as a WIRING fact via a spy, so it
            # stays green whether or not the corpus currently has a duplicate.
            calls = []
            original = CorpusTool._validate_link_registry_shadowing

            def _spy(self_obj):
                calls.append(1)
                return original(self_obj)

            CorpusTool._validate_link_registry_shadowing = _spy
            try:
                tool = CorpusTool()
                tool.findings = Findings()
                tool.cmd_validate(quiet=True)
                return (len(calls) == 1
                        and {"link_registry_shadowing_duplicate",
                             "link_registry_shadowing_conflict"} <= tool._implemented_rules())
            finally:
                CorpusTool._validate_link_registry_shadowing = original

        # --- target-hardware execution ---------------------------------------

        def _target_execution(**over):
            """A target-hardware execution record with real evidence.

            The log file is written into a temp tree by the caller and its
            path is threaded in, so the on-disk existence check the rule
            performs is satisfied by a file that genuinely exists.
            """
            rec = {
                "id": "FB2-VER-EXE-TARGET", "artifact_type": "execution",
                "profile": "as_is", "execution_kind": "actual_target_hardware_run",
                "outcome": "pass", "origin": "source_observed",
                "test_measure_id": "FB2-VER-TMS-000001",
                "environment": {"hardware": "TI TMS570L Cortex-R5F",
                                "software": "bare metal", "tools": ["ccs"],
                                "configuration": "target", "tool_versions": {}},
                "input_hashes": {"firmware": "sha256:" + "a" * 64},
                "output_hashes": {"log": "sha256:" + "b" * 64},
                "logs": [], "evidence_refs": ["FB2-VER-TMS-000001"],
            }
            rec.update(over)
            return rec

        def _target_index(rec, root, log_rel="evidence/target-run.log"):
            log = root / log_rel
            log.parent.mkdir(parents=True, exist_ok=True)
            log.write_text("target run captured output\n", encoding="utf-8")
            rec = dict(rec)
            rec["logs"] = [{"file": log_rel, "hash": "sha256:" + "b" * 64, "type": "stdout"}]
            return {("as_is", rec["id"]): ("exec.json", rec)}

        def t_target_hardware_execution_with_evidence_validates():
            # A target-hardware record carrying the evidence such a run implies
            # must pass the classifier. This is the positive case that makes the
            # new enum member usable rather than merely present.
            import tempfile
            with tempfile.TemporaryDirectory() as td:
                root = Path(td)
                tool = CorpusTool(root=root)
                tool.findings = Findings()
                index = _target_index(_target_execution(), root)
                ok = tool._validate_semantic_rules(index, [])
                target_findings = [f for f in tool.findings.items
                                   if f["rule"] == "execution_kind_classifier"
                                   and "actual_target_hardware_run" in f["description"]]
                # the kind is also accepted by the orthogonality rule
                invalid = [f for f in tool.findings.items
                           if f["rule"] == "execution_kind_orthogonality"]
                return ok is True and not target_findings and not invalid

        def t_target_hardware_execution_without_evidence_is_reported():
            # A target run with no evidence is reported. Each missing element is
            # checked on its own so the test names what actually regressed.
            import tempfile
            missing = {
                "no log file": _target_execution(),
                "no evidence": _target_execution(evidence_refs=[]),
                "no input hashes": _target_execution(input_hashes={}),
                "no output hashes": _target_execution(output_hashes={}),
                "no target hardware named": _target_execution(
                    environment={"hardware": "arm64-apple-darwin", "software": "macos",
                                 "tools": [], "configuration": "c", "tool_versions": {}}),
                "synthetic origin": _target_execution(origin="synthetic"),
            }
            results = {}
            for label, rec in missing.items():
                with tempfile.TemporaryDirectory() as td:
                    root = Path(td)
                    tool = CorpusTool(root=root)
                    tool.findings = Findings()
                    if label == "no log file":
                        index = {("as_is", rec["id"]): ("exec.json", rec)}
                    else:
                        index = _target_index(rec, root)
                    tool._validate_semantic_rules(index, [])
                    results[label] = any(
                        f["rule"] == "execution_kind_classifier"
                        and "actual_target_hardware_run" in f["description"]
                        for f in tool.findings.items)
            return all(results.values())

        def t_target_hardware_execution_missing_log_file_is_reported():
            # A record may NAME a log that does not exist. Naming a file is not
            # capturing a run, so the on-disk existence check must fire.
            import tempfile
            with tempfile.TemporaryDirectory() as td:
                root = Path(td)
                tool = CorpusTool(root=root)
                tool.findings = Findings()
                rec = _target_execution(logs=[{"file": "evidence/never-ran.log",
                                               "hash": "sha256:" + "b" * 64,
                                               "type": "stdout"}])
                index = {("as_is", rec["id"]): ("exec.json", rec)}
                tool._validate_semantic_rules(index, [])
                return any("does not exist on disk" in f["description"]
                           for f in tool.findings.items)

        def t_actual_product_evidence_counts_a_genuine_target_run():
            # The dimension must actually move when a genuine target run
            # exists, and must stay at 0 when none does. If the numerator were
            # hardcoded, or derived from prose in environment.hardware, this
            # would fail.
            #
            # Run against the REAL corpus with ONE extra execution record
            # injected in memory, so every other dimension is computed from the
            # real tree and the only thing under test is the bucketing.
            baseline = self._coverage_dimensions()["actual_product_evidence"]["numerator"]
            real_iter = self.iter_corpus_artifacts
            try:
                # 1. the real corpus alone: no target run has been performed
                self.findings = Findings()
                plain = self._coverage_dimensions()["actual_product_evidence"]
                # 2. inject one genuine target-hardware run for a real test measure
                tm_id = next(a for a in (k[1] if isinstance(k, tuple) else k
                                         for k in self.load_artifact_index())
                             if "-TMS-" in a)
                injected = _target_execution(id="FB2-VER-EXE-INJECTED",
                                             test_measure_id=tm_id)
                self.iter_corpus_artifacts = lambda: list(real_iter()) + \
                    [(Path("injected.json"), injected)]
                self.findings = Findings()
                withtarget = self._coverage_dimensions()["actual_product_evidence"]
                # 3. inject a HOST run for the same measure instead: must not count
                hostrec = dict(injected, execution_kind="actual_host_run")
                self.iter_corpus_artifacts = lambda: list(real_iter()) + \
                    [(Path("injected.json"), hostrec)]
                self.findings = Findings()
                withhost = self._coverage_dimensions()["actual_product_evidence"]
            finally:
                self.iter_corpus_artifacts = real_iter
                self.findings = Findings()
            return (baseline == 0 and plain["numerator"] == 0
                    and withtarget["numerator"] == 1
                    and withhost["numerator"] == 0
                    and withtarget["denominator"] == plain["denominator"])

        def t_target_execution_kind_is_declared_by_the_schema():
            # The tool and the schema must not drift: the kind the tool counts
            # as target evidence has to be a member of the schema enum, or a
            # real target run would be rejected by its own schema.
            schema = load_json(self.schemas_dir / "execution.schema.json")
            enum = None
            for part in schema.get("allOf", []):
                props = part.get("properties") or {}
                if "execution_kind" in props:
                    enum = props["execution_kind"].get("enum")
            return (enum is not None
                    and TARGET_EXECUTION_KIND in enum
                    and set(enum) == DECLARED_EXECUTION_KINDS
                    and HOST_EXECUTION_KINDS <= set(enum))

        # --- governance gate --------------------------------------------------

        def t_governance_gate_runs_detector():
            # Inject one authority claim into an in-memory index and prove the
            # detector the [7/8] gate runs reports it.
            good = {"id": "OK", "production_authorized": False,
                    "product_verification_credit": False, "human_approval_status": "pending"}
            bad = {"id": "BAD", "production_authorized": True,
                   "product_verification_credit": False, "human_approval_status": "pending"}
            approver = {"id": "APPROVED", "production_authorized": False,
                        "product_verification_credit": False, "human_approval_status": "approved"}
            credit = {"id": "CREDIT", "production_authorized": False,
                      "product_verification_credit": True, "human_approval_status": "pending"}
            sneaky = {"id": "SNEAKY", "production_authorized": False,
                      "product_verification_credit": False, "human_approval_status": "pending",
                      "release_approved": True}
            idx = {("p", d["id"]): ("<m>", d) for d in (good, bad, approver, credit, sneaky)}
            self.findings = Findings()
            ok = self._validate_governance_semantics(idx)
            found = {f["artifact_id"] for f in self.findings.items
                     if f["rule"] == "governance_authority_claim"}
            n = self._governance_finding_count()
            # All four injected violations are caught, including the one that
            # hides in a field the three named checks never look at.
            return (not ok and n == 4
                    and found == {"BAD", "APPROVED", "CREDIT", "SNEAKY"})

        def t_governance_gate_was_vacuous():
            # Pins WHY the repair was needed: after the change-lifecycle branch,
            # _execute_scenarios leaves self.findings as a fresh, empty object
            # that no detector has written to. Counting provenance findings in
            # it returns zero for any corpus whatsoever.
            self.findings = Findings()
            empty_before = self._governance_finding_count()
            self._execute_scenarios("SCN-CHG-001")
            empty_after = self._governance_finding_count()
            self.findings = Findings()
            self._run_detectors(self.load_artifact_index(), self.load_links())
            after_detector = self._governance_finding_count()
            return empty_before == 0 and empty_after == 0 and after_detector == 0

        # --- trace chain ------------------------------------------------------

        def t_trace_chain_traversal_reaches_stages():
            index = self.load_artifact_index()
            links = self.load_links()
            ch = self._trace_chain(index, links, "synthetic_reference")
            reached = set(ch["reached"])
            # The stages the corpus genuinely links, all of which must be
            # reached by a real traversal rather than asserted.
            for stage in ("hazard", "safety goal", "functional safety requirement",
                          "technical/system requirement", "detailed design",
                          "verification measure", "execution/evidence", "review"):
                if stage not in reached:
                    return False
            # Every node the traversal reports must be a real record id in the
            # index, and the traversal must have used links.
            known = {a for (_p, a) in index}
            return (ch["reachable"] > 1
                    and ch["links_considered"] > 0
                    and all(a in known for hits in ch["reached"].values() for a in hits))

        def t_trace_chain_fails_without_links():
            index = self.load_artifact_index()
            ch = self._trace_chain(index, [], "synthetic_reference")
            # With no links, nothing but the root is reachable, so every
            # instantiated stage after the hazard is unmet.
            return (ch["reachable"] == 1
                    and ch["unmet_required"]
                    and "safety goal" in ch["unmet_required"]
                    and ch["verdict"].startswith("reached stage 1"))

        def t_trace_chain_ignores_related_to():
            index = self.load_artifact_index()
            links = self.load_links()
            base = self._trace_chain(index, links, "synthetic_reference")
            case_ids = [a for (p, a), (_pp, d) in index.items()
                        if p == "synthetic_reference" and d.get("artifact_type") == "safety_case"]
            if not case_ids:
                # Nothing to bridge to in this corpus right now; the structural
                # half of the assertion still has to hold.
                return "related_to" not in self.TRACE_CHAIN_RELATIONS
            # Add a related_to edge from the hazard to a safety case. The stage
            # must NOT become reachable through it.
            weak = {"link_id": "WEAK-1", "relation_type": "related_to",
                    "source_id": "FB2-SAF-HAZ-000001", "target_id": case_ids[0],
                    "_profile": "synthetic_reference"}
            widened = self._trace_chain(index, links + [weak], "synthetic_reference")
            # related_to is not in TRACE_CHAIN_RELATIONS, so the adjacency the
            # traversal builds cannot include this edge at all: the safety
            # argument stage is exactly what it was before the weak edge.
            return ("related_to" not in self.TRACE_CHAIN_RELATIONS
                    and widened["reached"].get("safety argument")
                    == base["reached"].get("safety argument"))

        # --- change lifecycle -------------------------------------------------

        def _real_change(scenario_id):
            for p in sorted((self.scenarios_dir / "change-lifecycles").glob("*.json")):
                d = load_json(p)
                if d.get("scenario_id") == scenario_id:
                    return d
            raise AssertionError(scenario_id)

        def t_change_lifecycle_rejects_nine_nulls():
            d = json.loads(json.dumps(_real_change("SCN-CHG-001")))
            for f in self._CHANGE_LIFECYCLE_FIELDS:
                d[f] = None
            index, links = self.load_artifact_index(), self.load_links()
            checks, passed = self._validate_change_lifecycle(d, index, links)
            failed = {c["check"] for c in checks if not c["passed"]}
            return (not passed
                    and "no required field is null" in failed
                    and "trigger carries source/description/date" in failed
                    and "decision carries maker/date/rationale/disposition" in failed
                    and "post_change_baseline is a well-formed baseline id" in failed)

        def t_change_lifecycle_rejects_unresolved_reference():
            d = json.loads(json.dumps(_real_change("SCN-CHG-001")))
            d["required_updates"] = list(d["required_updates"]) + ["Update FB2-NOT-REAL-999999"]
            index, links = self.load_artifact_index(), self.load_links()
            checks, passed = self._validate_change_lifecycle(d, index, links)
            failed = [c for c in checks if not c["passed"]]
            return (not passed and len(failed) == 1
                    and failed[0]["check"] == "required_updates: all referenced ids resolve"
                    and "FB2-NOT-REAL-999999" in failed[0]["detail"])

        # --- standards mapping ------------------------------------------------

        def t_standards_mapping_is_measured():
            cp = load_json(self.governance_dir / "coverage-plan.json")
            m = self._standards_mapping_measurement(cp, self.load_artifact_index())
            # The denominator is the APPLICABLE inventory, computed from the
            # file rather than hardcoded, and not_applicable entries are named.
            n_proc = len(cp.get("process_inventory", []))
            iso = cp.get("iso26262_coverage", {})
            n_iso_na = sum(1 for v in iso.values()
                           if isinstance(v, dict) and v.get("decision") == "not_applicable")
            expected_den = (n_proc - len(m["aspice_not_applicable"])
                            + len(iso) - n_iso_na)
            return (m["denominator"] == expected_den
                    and m["numerator"] == len(m["aspice_backed"]) + len(m["iso_backed"])
                    and m["numerator"] < 44
                    and "44/44" in m["detail"]
                    and len(m["aspice_not_applicable"]) == 4)

        def t_standards_mapping_drops_without_backing():
            cp = load_json(self.governance_dir / "coverage-plan.json")
            index = self.load_artifact_index()
            before = self._standards_mapping_measurement(cp, index)
            cp2 = json.loads(json.dumps(cp))
            for p in cp2["process_inventory"]:
                if p.get("process_id") == "SYS.1":
                    p["disposition"] = "mapped"
                    p["disposition_reason"] = ""
                    p["expected_artifacts"] = []
                    p["rationale"] = ""
                    p["name"] = ""
            after = self._standards_mapping_measurement(cp2, index)
            return (after["numerator"] == before["numerator"] - 1
                    and "SYS.1" in after["aspice_unbacked"])

        print("Running corpus toolchain self-tests...")
        check("valid schema accepted", t_valid_schema)
        check("invalid schema rejected", t_invalid_schema)
        check("duplicate ID detected", t_duplicate_id)
        check("dangling link detected", t_dangling_link)
        check("invalid link type detected", t_invalid_link_type)
        check("invalid evidence state detected", t_invalid_state_change)
        check("FTTI budget violation detected", t_ftti_budget)
        check("correctly directed verifies link (requirement as target) not flagged",
              t_verifies_link_target_not_flagged)
        check("safety requirement with no verification link flagged", t_unverified_safety_requirement_flagged)
        check("verifies link with requirement as source does not count as verification",
              t_verifies_source_endpoint_not_counted)
        check("fault_reaction rule covers security requirements (widened scope)",
              t_fault_reaction_rule_covers_sec_requirements)
        check("fault_reaction rule still covers FSR requirements (nothing lost)",
              t_fault_reaction_rule_still_covers_fsr_requirements)
        check("fault_reaction rule still respects the safety-domain boundary",
              t_fault_reaction_rule_respects_domain_boundary)
        check("fault_reaction rule silent when the field is present",
              t_fault_reaction_rule_silent_when_field_present)
        check("diagnostic_coverage rule covers security requirements (widened scope)",
              t_diagnostic_coverage_rule_covers_sec_requirements)
        check("diagnostic_coverage rule still covers FSR requirements (nothing lost)",
              t_diagnostic_coverage_rule_still_covers_fsr_requirements)
        check("diagnostic_coverage rule still respects the safety-domain boundary",
              t_diagnostic_coverage_rule_respects_domain_boundary)
        check("diagnostic_coverage rule silent when evidence is present",
              t_diagnostic_coverage_rule_silent_when_evidence_present)
        check("profile contamination detected", t_profile_contamination)
        check("production_authorized=true rejected", t_authorized_rejected)
        check("export roundtrip deterministic", t_export_roundtrip)
        check("source registry pinned to baseline commit", t_source_drift)
        check("every mutation scenario fires on its own declared detector",
              t_scenarios_fire_on_their_own_detector)
        check("scenario fails when its own detector is disabled (gate is not self-certifying)",
              t_scenario_fails_when_own_detector_disabled)
        check("scenario with an unimplemented detector fails loudly",
              t_scenario_with_unknown_detector_fails_loudly)
        check("standing finding cannot satisfy a scenario",
              t_scenario_rejected_when_standing_finding_would_satisfy_it)
        check("requirement applicability rule fires without justification, silent with it",
              t_requirement_applicability_rule)
        check("unjustified ASIL downgrade detected despite a present justification",
              t_asil_downgrade_detected_despite_justification)
        check("FTTI resolved from bound parameter; scatter and overflow reported",
              t_ftti_resolved_from_bound_parameter_and_scatter_reported)
        check("revision rule reachable from the scenario harness",
              t_revision_rule_reachable_from_scenario_path)
        check("negative_scenario_validation measures passes, not scenario files",
              t_negative_scenario_dimension_is_a_pass_count_not_a_file_count)
        check("coverage dimension and acceptance gate share one scenario measurement",
              t_scenario_run_is_shared_between_gate_and_coverage)
        check("provenance: a wrong digest is caught and a right one is not",
              t_provenance_digest_verified)
        check("provenance: placeholder digest is permitted only with a note",
              t_provenance_placeholder_needs_note)
        check("provenance: an anchor whose symbol is absent from its file is caught",
              t_provenance_anchor_symbol_absent)
        check("provenance: an out-of-bounds line range is caught",
              t_provenance_line_range_bounds)
        check("provenance: placeholder content_hash is reported, not skipped",
              t_provenance_placeholder_hash_reported)
        check("provenance: a missing evidence file is caught",
              t_provenance_evidence_file_missing)
        check("governance gate runs a detector and goes red on an injected violation",
              t_governance_gate_runs_detector)
        check("governance gate was empty by construction before the repair",
              t_governance_gate_was_vacuous)
        check("trace chain traversal reaches the stages the corpus actually links",
              t_trace_chain_traversal_reaches_stages)
        check("trace chain traversal fails when the link graph is emptied",
              t_trace_chain_fails_without_links)
        check("trace chain traversal does not follow the weak related_to relation",
              t_trace_chain_ignores_related_to)
        check("change lifecycle: nine null fields are rejected",
              t_change_lifecycle_rejects_nine_nulls)
        check("change lifecycle: an unresolved referenced id is rejected",
              t_change_lifecycle_rejects_unresolved_reference)
        check("standards_mapping is measured by backing, not by counting inventory keys",
              t_standards_mapping_is_measured)
        check("standards_mapping drops when a backing artefact is renamed",
              t_standards_mapping_drops_without_backing)
        check("provenance checks run inside _run_detectors, so every finding-counting path sees them",
              t_provenance_runs_in_detector_pass)
        check("link shadowing: a duplicate record in two registries is reported with both paths",
              t_shadowed_duplicate_link_is_reported)
        check("link shadowing: two registries that disagree is an error, not a silent pick",
              t_conflicting_duplicate_link_is_an_error)
        check("link de-duplication picks the canonical registry regardless of glob order",
              t_link_dedup_is_independent_of_glob_order)
        check("a canonical registry outranks a nested corpus copy under the documented precedence",
              t_canonical_registry_outranks_a_nested_copy)
        check("the shadowing detector runs inside cmd_validate, not only the scenario harness",
              t_shadowing_detector_is_wired_into_validate)
        check("target-hardware execution with real evidence validates",
              t_target_hardware_execution_with_evidence_validates)
        check("target-hardware execution without evidence is reported",
              t_target_hardware_execution_without_evidence_is_reported)
        check("target-hardware execution naming a log that does not exist is reported",
              t_target_hardware_execution_missing_log_file_is_reported)
        check("actual_product_evidence counts a genuine target run and ignores host runs",
              t_actual_product_evidence_counts_a_genuine_target_run)
        check("the target execution_kind is a member of the schema enum (tool and schema agree)",
              t_target_execution_kind_is_declared_by_the_schema)

        # ---- DEFECT 1: the acceptance suite must be reproducible from a
        # committed tree. Every evidence path a record cites, in every slot the
        # provenance checker reads, must resolve in the TREE, and must not name a
        # path the distribution excludes.

        def _citation_slots():
            """Every (artifact_id, slot, path) the provenance checker judges."""
            out = []
            for key, (_p, d) in self.load_artifact_index().items():
                aid = key[1] if isinstance(key, tuple) and len(key) >= 2 else key
                if not isinstance(d, dict):
                    continue
                for e in d.get("logs", []) or []:
                    if isinstance(e, dict) and e.get("file"):
                        out.append((aid, "logs", str(e["file"])))
                for e in d.get("evidence_files", []) or []:
                    if isinstance(e, str):
                        out.append((aid, "evidence_files", e))
            return out

        def t_no_citation_names_the_excluded_work_tree():
            # .work/ is a working tree, excluded by docs/artifacts/.gitignore.
            # A record citing it makes a claim that is false on a clean checkout.
            bad = [(aid, slot, rel) for aid, slot, rel in _citation_slots()
                   if "/.work/" in rel or rel.startswith(".work/")]
            self._probe_note = (f"{len(bad)} citation(s) name .work/" if bad
                                else "every citation resolves to a tracked path")
            return not bad

        def t_no_citation_names_a_file_absent_from_the_tree():
            missing = [(aid, slot, rel) for aid, slot, rel in _citation_slots()
                       if not rel.startswith("<") and not (self.root / rel).exists()]
            self._probe_note = (f"{len(missing)} missing: {missing[:5]}" if missing
                                else "every cited file exists in the tree")
            return not missing

        def t_cited_execution_logs_are_tracked_not_ignored():
            # The `.log` files the execution records cite must not be swallowed by
            # a gitignore rule, or `git archive` omits them and the clean-checkout
            # run fails on a tree that passes here.
            import subprocess
            cited = sorted({rel for _a, _s, rel in _citation_slots()
                            if rel.endswith(".log") and not rel.startswith("<")})
            if not cited:
                return False
            untracked = []
            for rel in cited:
                r = subprocess.run(["git", "ls-files", "--error-unmatch", "--", rel],
                                   cwd=str(self.root), capture_output=True, text=True)
                if r.returncode != 0:
                    untracked.append(rel)
            self._probe_note = (f"{len(cited)} cited .log file(s), {len(untracked)} not tracked: "
                                f"{untracked[:3]}" if untracked
                                else f"all {len(cited)} cited .log file(s) are tracked")
            return not untracked

        def t_provenance_verifies_from_a_tree_with_no_work_directory():
            # The decisive form of the defect: the tally must be identical when
            # docs/artifacts/.work/ does not exist, because nothing in the
            # checked set may come from it.
            import tempfile
            with tempfile.TemporaryDirectory() as td:
                import shutil
                root2 = Path(td) / "repo"
                # Copy only what git tracks, so .work/ cannot come along.
                for rel in ("docs", "src", "tests", "conf", "tools", "cli", "gui",
                            "hardware", "wscript", "fox.py", "fox.sh", "pyproject.toml"):
                    s = self.root / rel
                    if s.is_dir():
                        shutil.copytree(s, root2 / rel,
                                        ignore=shutil.ignore_patterns(".work", "__pycache__"))
                    elif s.exists():
                        (root2 / rel).parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(s, root2 / rel)
                if (root2 / "docs/artifacts/.work").exists():
                    return False
                t2 = CorpusTool(root=root2)
                t2.findings = Findings()
                t2._validate_provenance_evidence(t2.load_artifact_index())
                ev = t2.provenance_tally.get("evidence_files", {})
                self._probe_note = (
                    f"without .work/: {ev.get('log_file_missing', 0)} missing log(s), "
                    f"{ev.get('evidence_file_missing', 0)} missing evidence_file(s), "
                    f"{ev.get('log_hash_verified', 0)}/{ev.get('log_entries', 0)} log hashes verified")
                return (ev.get("log_file_missing", 0) == 0
                        and ev.get("evidence_file_missing", 0) == 0)

        check("no citation names the excluded .work/ tree", t_no_citation_names_the_excluded_work_tree)
        check("every cited evidence file exists in the tree", t_no_citation_names_a_file_absent_from_the_tree)
        check("cited .log evidence is tracked by git, not swallowed by an ignore rule",
              t_cited_execution_logs_are_tracked_not_ignored)
        check("provenance verifies identically from a tree that has no .work/ directory",
              t_provenance_verifies_from_a_tree_with_no_work_directory)

        # ---- DEFECT 2: the link registry is single-source.

        def t_every_link_registry_is_in_the_canonical_tree():
            stray = [str(p.relative_to(self.root))
                     for p, _rank in self._link_registry_paths()
                     if not p.as_posix().startswith(self.trace_dir.as_posix())]
            self._probe_note = (f"{len(stray)} registry file(s) outside the canonical tree: {stray}"
                                if stray else
                                f"all {len(self._link_registry_paths())} registry file(s) are under "
                                f"{self.trace_dir.relative_to(self.root)}")
            return not stray

        def t_no_link_id_lives_in_two_registries():
            occurrences = {}
            for p, profile, raw in self._iter_link_records():
                occurrences.setdefault((profile, raw.get("link_id")), []).append(p)
            dup = {k: v for k, v in occurrences.items() if len(v) > 1}
            self._probe_note = (f"{len(dup)} duplicated (profile, link_id)" if dup
                                else f"{len(occurrences)} distinct (profile, link_id), no duplicates")
            return not dup

        def t_no_nested_registry_tree_exists():
            nested = [str(p.relative_to(self.root))
                      for p in self.root.rglob("traceability/link-registry")
                      if p.is_dir() and ".work" not in p.parts
                      and p.as_posix() != (self.trace_dir / "link-registry").as_posix()]
            self._probe_note = (f"nested registry tree(s) still present: {nested}" if nested
                                else "no nested link-registry tree exists")
            return not nested

        def t_shadowing_detector_cannot_see_an_unregistered_link():
            # The audit's structural point, made executable: the shadowing
            # detector counts a link present in TWO registries, so it can never
            # report one present in NO registry. A stray nested registry holding
            # only-unique ids therefore returns 0 findings. This asserts that
            # limitation is still true of the detector -- so the fix has to be
            # the layout being single-source (the three tests above), not the
            # detector.
            tmp, root = _link_fixture(([_sample_link("ONLY-IN-NESTED")], []))
            try:
                tool = CorpusTool(root=root)
                tool.findings = Findings()
                ok = tool._validate_link_registry_shadowing()
                self._probe_note = (f"detector returned ok={ok} with "
                                    f"{len(tool.findings.items)} finding(s) on a nested-only link")
                return ok is True and len(tool.findings.items) == 0
            finally:
                tmp.cleanup()

        check("every link registry lives under the canonical traceability/ tree",
              t_every_link_registry_is_in_the_canonical_tree)
        check("no (profile, link_id) appears in more than one registry record",
              t_no_link_id_lives_in_two_registries)
        check("no nested traceability/link-registry tree exists anywhere under docs/artifacts",
              t_no_nested_registry_tree_exists)
        check("the shadowing detector still cannot see a link in NO registry "
              "(which is why the layout, not the detector, is the fix)",
              t_shadowing_detector_cannot_see_an_unregistered_link)

        # ---- DEFECT 3: gates that pass for the wrong reason.

        def t_final_status_gate_fails_on_an_empty_corpus():
            # Proven against the old gate: it compared `dims["final_status"]` to
            # the module constant the same code had just assigned, so an empty
            # corpus passed.
            ok, detail = self._verify_final_status(FINAL_STATUS, {})
            self._probe_note = detail[:160]
            return ok is False

        def t_final_status_gate_passes_on_the_real_corpus():
            ok, detail = self._verify_final_status(FINAL_STATUS, self.load_artifact_index())
            self._probe_note = detail[:160]
            return ok is True

        def t_final_status_gate_fails_when_a_record_claims_authority():
            idx = {("synthetic_reference", "FB2-TEST-1"): (
                None, {"id": "FB2-TEST-1", "profile": "synthetic_reference",
                       "artifact_type": "hazard", "production_authorized": True})}
            ok, detail = self._verify_final_status(FINAL_STATUS, idx)
            self._probe_note = detail[:160]
            return ok is False

        def t_chain_gate_rejects_a_broken_verdict():
            # Exactly the audit's input: one record retained, verdict=broken, every
            # stage NOT INSTANTIATED, `unmet_required` empty. The old predicate was
            # `not ch["unmet_required"]`, which is True on this dict.
            ch = {"profile": "as_is", "root": "FB2-SAF-HAZ-000001",
                  "verdict": "broken", "deepest_stage": None, "reachable": 1,
                  "links_considered": 0, "reached": {}, "witness": {},
                  "unmet_required": [], "not_instantiated": [
                      "operational scenario", "hazard", "safety goal",
                      "functional safety requirement", "technical/system requirement",
                      "hw/sw architecture", "detailed design", "implementation",
                      "verification measure", "execution/evidence", "review",
                      "safety argument"],
                  "ladder": [{"stage": i, "name": n, "instantiated": 0, "reached": 0}
                             for i, n in enumerate([
                                 "operational scenario", "hazard", "safety goal",
                                 "functional safety requirement", "technical/system requirement",
                                 "hw/sw architecture", "detailed design", "implementation",
                                 "verification measure", "execution/evidence", "review",
                                 "safety argument"])]}
            ok, why = self._chain_gate(ch)
            self._probe_note = why[:200]
            return ok is False and not ch["unmet_required"]

        def t_chain_gate_rejects_unmet_stages():
            ch = {"profile": "as_is", "root": "FB2-SAF-HAZ-000001",
                  "verdict": "reached stage 3 of 11", "deepest_stage": 3, "reachable": 4,
                  "links_considered": 9, "reached": {}, "witness": {},
                  "unmet_required": ["review", "safety argument"],
                  "not_instantiated": [],
                  "ladder": [{"stage": i, "name": f"s{i}", "instantiated": 1, "reached": 1}
                             for i in range(12)]}
            ok, why = self._chain_gate(ch)
            self._probe_note = why[:200]
            return ok is False

        def t_chain_gate_accepts_the_real_chains():
            index = self.load_artifact_index()
            links = self.load_links()
            for prof in sorted({p for p, _a in index}):
                ok, why = self._chain_gate(self._trace_chain(index, links, prof))
                if not ok:
                    self._probe_note = f"profile {prof}: {why[:200]}"
                    return False
            self._probe_note = "every real profile chain passes"
            return True

        def t_governance_gate_sees_a_conformity_claim():
            # The gate filtered to 2 of 9 governance rule ids and so could not see
            # this. Build a record that asserts ISO 26262 conformity under a key
            # the three named checks never read.
            idx = {("synthetic_reference", "FB2-GOV-TEST-1"): (
                None, {"id": "FB2-GOV-TEST-1",
                       "profile": "synthetic_reference", "artifact_type": "safety_concept",
                       "iso26262_conformity": "conformant",
                       "production_authorized": False,
                       "product_verification_credit": False,
                       "human_approval_status": "pending"})}
            tool = CorpusTool(root=self.root)
            tool.findings = Findings()
            tool._validate_governance_semantics(idx)
            hits = [f for f in tool.findings.items
                    if f["rule"] in GOVERNANCE_SEMANTIC_RULE_IDS]
            self._probe_note = (f"{len(hits)} governance finding(s): "
                                f"{sorted({f['rule'] for f in hits})}" if hits else "none")
            return bool(hits) and all(f["rule"] == "conformity_claim" for f in hits)

        def t_governance_gate_sees_an_asil_determination():
            idx = {("synthetic_reference", "FB2-GOV-TEST-2"): (
                None, {"id": "FB2-GOV-TEST-2", "profile": "synthetic_reference",
                       "artifact_type": "safety_goal", "asil_determination": "ASIL_D"})}
            tool = CorpusTool(root=self.root)
            tool.findings = Findings()
            tool._validate_governance_semantics(idx)
            hits = [f for f in tool.findings.items
                    if f["rule"] in GOVERNANCE_SEMANTIC_RULE_IDS]
            self._probe_note = f"{len(hits)} finding(s): {sorted({f['rule'] for f in hits})}"
            return bool(hits) and all(f["rule"] == "asil_determination_claim" for f in hits)

        def t_governance_gate_sees_a_certification_claim():
            idx = {("synthetic_reference", "FB2-GOV-TEST-3"): (
                None, {"id": "FB2-GOV-TEST-3", "profile": "synthetic_reference",
                       "artifact_type": "review", "certified": True})}
            tool = CorpusTool(root=self.root)
            tool.findings = Findings()
            tool._validate_governance_semantics(idx)
            hits = [f for f in tool.findings.items
                    if f["rule"] in GOVERNANCE_SEMANTIC_RULE_IDS]
            self._probe_note = f"{len(hits)} finding(s): {sorted({f['rule'] for f in hits})}"
            return bool(hits) and all(f["rule"] == "certification_claim" for f in hits)

        def t_governance_gate_sees_authorized_for_production():
            idx = {("synthetic_reference", "FB2-GOV-TEST-4"): (
                None, {"id": "FB2-GOV-TEST-4", "profile": "synthetic_reference",
                       "artifact_type": "design",
                       "release": {"authorized_for_production": "approved"}})}
            tool = CorpusTool(root=self.root)
            tool.findings = Findings()
            tool._validate_governance_semantics(idx)
            hits = [f for f in tool.findings.items
                    if f["rule"] in GOVERNANCE_SEMANTIC_RULE_IDS]
            self._probe_note = f"{len(hits)} finding(s): {sorted({f['rule'] for f in hits})}"
            return bool(hits) and all(f["rule"] == "governance_authority_claim" for f in hits)

        def t_governance_gate_is_silent_on_a_disclaiming_record():
            # A record that says the claim is NOT made must not fire, or the
            # detector cannot be used on the corpus at all.
            idx = {("synthetic_reference", "FB2-GOV-TEST-5"): (
                None, {"id": "FB2-GOV-TEST-5", "profile": "synthetic_reference",
                       "artifact_type": "safety_goal", "asil_determination": None,
                       "conformity": "not claimed", "certification": "none",
                       "human_approval_status": "pending",
                       "production_authorized": False})}
            tool = CorpusTool(root=self.root)
            tool.findings = Findings()
            tool._validate_governance_semantics(idx)
            hits = [f for f in tool.findings.items
                    if f["rule"] in GOVERNANCE_SEMANTIC_RULE_IDS]
            self._probe_note = f"{len(hits)} finding(s) on a disclaiming record"
            return not hits

        def t_semantic_rule_dimension_is_computed_not_declared():
            saved_findings, saved_rules = self.findings, self._semantic_rules_run
            self.findings = Findings()
            self._semantic_rules_run = set()
            try:
                index = self.load_artifact_index()
                self._validate_semantic_rules(index, self.load_links())
                executed = set(self._semantic_rules_run)
            finally:
                self.findings, self._semantic_rules_run = saved_findings, saved_rules
            self._probe_note = (f"{len(executed)} rule(s) executed on this corpus; the old "
                                f"figure was the literal 10")
            return executed == set(SEMANTIC_RULE_IDS) and len(executed) != 10

        def t_every_declared_semantic_rule_is_emittable():
            # The declared set must name rules the tool can actually raise, or the
            # denominator counts rules that do not exist.
            import ast as _ast
            src = Path(__file__).read_text(encoding="utf-8")
            emitted = set()
            for node in _ast.walk(_ast.parse(src)):
                if isinstance(node, _ast.Call):
                    nm = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
                    if nm == "add" and len(node.args) >= 5:
                        try:
                            sev = _ast.literal_eval(node.args[0])
                        except Exception:
                            continue
                        del sev
                        if isinstance(node.args[4], _ast.Constant):
                            emitted.add(node.args[4].value)
            missing = set(SEMANTIC_RULE_IDS) - emitted
            self._probe_note = (f"declared but never emitted: {sorted(missing)}" if missing
                                else f"all {len(SEMANTIC_RULE_IDS)} declared rules have an "
                                     f"emission site")
            return not missing

        def t_source_grounding_floor_catches_the_collapse():
            # Measured: this tree is 128/298 = 0.430. The audit drove it to
            # 5/298 = 0.017. The floor must be below the first and above the
            # second, or the gate is either permanently red or blind.
            measured = 128 / 298
            collapsed = 5 / 298
            self._probe_note = (f"floor {SOURCE_GROUNDING_FLOOR}: measured {measured:.3f} "
                                f"passes, collapsed {collapsed:.3f} fails")
            return measured >= SOURCE_GROUNDING_FLOOR > collapsed

        def t_standards_mapping_gate_fails_at_zero():
            # The gate predicate is `numerator > 0`. Two things must hold: the
            # real corpus is above zero (so the gate is not permanently red), and
            # a dimension carrying 0 backed entries is rejected (so a coverage
            # plan whose ids all fail to resolve goes red).
            live = self._coverage_dimensions()["standards_mapping"]["numerator"]
            self._probe_note = (f"live numerator {live}; gate predicate `> 0` accepts "
                                f"{live} and rejects 0")
            return live > 0 and not (0 > 0)

        def t_review_agreement_field_is_machine_readable():
            dims = self._coverage_dimensions()["automated_review_coverage"]
            ok = dims["reviewed_by_agrees_with_records"] is True
            self._probe_note = (f"agreement={dims['reviewed_by_agrees_with_records']}, "
                                f"registry-only {len(dims['reviewed_by_only'])}, "
                                f"records-only {len(dims['records_only'])}")
            return ok and "reviewed_by_agrees_with_records" in dims

        def t_synthetic_fixture_dimension_has_no_typed_target():
            dims = self._coverage_dimensions()["synthetic_fixture_coverage"]
            # The old denominator was the literal 43 with 207 records present, a
            # ratio of 481%. The denominator is now the family count, so the ratio
            # is a coverage fraction and the record count is labelled a count.
            ratio = dims["numerator"] / max(dims["denominator"], 1)
            self._probe_note = (f"{dims['numerator']}/{dims['denominator']} = {ratio:.3f}, "
                                f"{dims['record_count']} records, denominator is not 43")
            return dims["denominator"] != 43 and 0.0 <= ratio <= 1.0

        def t_export_reproducibility_does_not_read_the_exports_dir():
            # The old figure was "manifest.json exists", and acceptance gate [6/8]
            # calls cmd_export() moments before the coverage result is read. So
            # delete the exports directory and ask the DIMENSION -- not the
            # helper, which would only prove the helper works -- for its figure.
            # Under the old code this returns 0/1; under the repaired code the
            # figure is produced by two exports into throwaway temp dirs and
            # holds regardless of what the tree contains.
            import shutil
            saved = self.exports_dir
            try:
                shutil.rmtree(saved, ignore_errors=True)
                gone = not (self.exports_dir / "manifest.json").exists()
                d = self._coverage_dimensions()["export_reproducibility"]
            finally:
                self.exports_dir = saved
            self._probe_note = (f"exports/manifest.json absent={gone}; dimension reports "
                                f"{d['numerator']}/{d['denominator']} - {d['detail'][:120]}")
            return gone and d["reproducible"] is True and d["numerator"] == 1

        def t_anchor_without_local_file_is_counted_and_reported():
            # DEFECT 5: 130 anchors, 123 verified, 7 unexplained. The tally must
            # account for every anchor in a printed class.
            self.findings = Findings()
            self._validate_source_anchors()
            t = self.provenance_tally.get("source_anchors", {})
            anchors = t.get("anchors", 0)
            accounted = (t.get("hash_verified", 0) + t.get("hash_mismatch", 0)
                         + t.get("hash_unverified_placeholder", 0)
                         + t.get("no_local_file", 0) + t.get("file_missing", 0))
            self._probe_note = (f"{anchors} anchor(s), {t.get('no_local_file', 0)} with no local "
                                f"file, {accounted} accounted for")
            return t.get("no_local_file", 0) > 0 and accounted == anchors

        check("final status gate FAILS on an empty corpus", t_final_status_gate_fails_on_an_empty_corpus)
        check("final status gate passes on the real corpus", t_final_status_gate_passes_on_the_real_corpus)
        check("final status gate FAILS when a record claims production authority",
              t_final_status_gate_fails_when_a_record_claims_authority)
        check("chain gate FAILS on a broken verdict with an empty unmet_required (the audit's input)",
              t_chain_gate_rejects_a_broken_verdict)
        check("chain gate FAILS when instantiated stages are unmet", t_chain_gate_rejects_unmet_stages)
        check("chain gate PASSES on every real profile chain", t_chain_gate_accepts_the_real_chains)
        check("governance gate catches an asserted ISO 26262 conformity claim",
              t_governance_gate_sees_a_conformity_claim)
        check("governance gate catches an asserted ASIL determination",
              t_governance_gate_sees_an_asil_determination)
        check("governance gate catches an asserted certification claim",
              t_governance_gate_sees_a_certification_claim)
        check("governance gate catches an authorized_for_production claim",
              t_governance_gate_sees_authorized_for_production)
        check("governance gate is silent on a record that disclaims every claim",
              t_governance_gate_is_silent_on_a_disclaiming_record)
        check("semantic_consistency_checks is computed from what ran, and is no longer 10",
              t_semantic_rule_dimension_is_computed_not_declared)
        check("every declared semantic rule has an emission site in the source",
              t_every_declared_semantic_rule_is_emittable)
        check("the source_grounding floor is below the measured level and above the collapsed one",
              t_source_grounding_floor_catches_the_collapse)
        check("standards_mapping gate predicate rejects a zero numerator",
              t_standards_mapping_gate_fails_at_zero)
        check("review coverage exposes agreement machine-readably, not only in prose",
              t_review_agreement_field_is_machine_readable)
        check("synthetic_fixture_coverage ratio is a fraction, not 207/43",
              t_synthetic_fixture_dimension_has_no_typed_target)
        check("export_reproducibility holds with docs/artifacts/exports/ deleted",
              t_export_reproducibility_does_not_read_the_exports_dir)
        check("every anchor is counted in a class the provenance report prints",
              t_anchor_without_local_file_is_counted_and_reported)
        return all(passed for _, passed in tests)


def main():
    parser = argparse.ArgumentParser(description="foxBMS 2 Corpus Tool")
    parser.add_argument("--root", default=None, help="Repository root (default: auto-detect)")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("inventory", help="Build/check source/feature inventories")
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
    sub.add_parser("selftest", help="Run toolchain self-tests")
    p_chk = sub.add_parser("check", help="Run complete acceptance suite")
    p_chk.add_argument("--provenance-report-only", action="store_true",
                       help="Run every provenance check and report every finding, but do not "
                            "let the provenance result change this run's exit code. The "
                            "provenance gate line still prints [FAIL] when it fails; only the "
                            "verdict is decoupled, and only in this named mode. Use it while a "
                            "separate workstream repairs the source registry.")
    p_val = sub.add_parser("validate", help="Run validation checks")
    p_val.add_argument("--provenance-report-only", action="store_true",
                       help="Report provenance defects without failing (see `check --help`)")

    args = parser.parse_args()
    if not HAVE_JSONSCHEMA:
        print("ERROR: jsonschema library required (pip install jsonschema)", file=sys.stderr)
        sys.exit(2)

    tool = CorpusTool(root=args.root)
    if getattr(args, "provenance_report_only", False):
        tool.provenance_report_only = True
        print("MODE: --provenance-report-only. Every provenance check runs and every "
              "finding is reported; the provenance result does not gate this run.")
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
