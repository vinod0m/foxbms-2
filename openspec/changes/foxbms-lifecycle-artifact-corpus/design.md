## Context

See proposal.md for motivation. The foxBMS 2 repository (commit 308028fb, v1.11.0) contains a production-grade BMS development platform but lacks a comprehensive, traceable engineering corpus spanning the full ISO 26262 / Automotive SPICE lifecycle. This design creates that corpus under `docs/artifacts/` with two profiles: `as_is` (faithful reconstruction) and `synthetic_reference` (hypothetical automotive BMS project).

Constraints: All writes restricted to `docs/artifacts/`; `.work/` for temporary files; no modifications to existing foxBMS source/hardware/config/tests; ISO 26262:2018 and ASPICE PAM 4.1 baselines locked; no normative text reproduction per rights policy.

## Goals / Non-Goals

**Goals:**
- Create canonical JSON schemas for all artifact types with field-level provenance
- Build traceability graph with 17 typed link relations supporting vertical/reverse/lateral/lifecycle traversal
- Generate two profiles: `as_is` (observed) and `synthetic_reference` (hypothetical complete project)
- Create 20+ mutation scenarios and 3 change-lifecycle demonstrations for corpus validation
- Implement executable validation tooling (inventory, validate, coverage, trace, impact, render, export, scenario-test, check)
- Produce 10 final reports with 15 completion dimensions
- All artifacts conform to JSON schemas with schema_version, provenance, standards mappings

**Non-Goals:**
- No modifications to existing foxBMS source code, hardware files, configuration, or tests
- No ISO 26262 or ASPICE certification claims - this is a synthetic development corpus
- No reproduction of normative standard text - only metadata and methodology mappings
- No actual hardware testing or tool qualification
- No production authorization or product verification credit

## Decisions

### 1. Two-profile architecture (`as_is` + `synthetic_reference`)
**Decision:** Maintain two explicitly separated profiles sharing a controlled source registry.
**Rationale:** Per master prompt Section 5. The `as_is` profile faithfully reconstructs observed foxBMS behavior; `synthetic_reference` creates a complete hypothetical automotive BMS project. This separation prevents synthetic content from being mistaken for observed evidence.
**Alternatives considered:** Single profile with mixed provenance - rejected because it would obscure the distinction between observed and synthetic content.

### 2. Canonical JSON records as authoritative data
**Decision:** Use versioned JSON records as the single source of truth, validated by JSON Schema (draft-07). Generate Markdown, CSV, graph exports from canonical data.
**Rationale:** Per master prompt Section 6. Prevents drift between multiple document copies. Enables deterministic validation and regeneration.
**Alternatives considered:** Markdown-first with embedded metadata - rejected because schema validation and automated checks are harder.

### 3. ID scheme: `FB2-<DOMAIN>-<TYPE>-<NNNNNN>`
**Decision:** Use stable, globally unique, readable IDs with explicit profile/scenario namespace rules.
**Rationale:** Per master prompt Section 6. Enables cross-profile traceability while maintaining isolation. Never renumber established IDs.
**Alternatives considered:** UUIDs - rejected as not human-readable; simple sequential numbers - rejected as not globally unique across profiles.

### 4. Link semantics with 17 relation types
**Decision:** Define precise domain/range for 17 link types (refines, allocated_to, implements, verifies, validates, result_of, supports, mitigates, specified_by, consumes, produces, depends_on, constrained_by, reviewed_by, changes, supersedes).
**Rationale:** Per master prompt Section 13. Generic `related_to` does not satisfy engineering coverage obligations. Links need metadata: rationale, provenance, review_state, change_suspect_status.
**Alternatives considered:** Simplified link types - rejected as insufficient for engineering traceability.

### 5. Parameter registry as single source of truth
**Decision:** Define one coherent parameter registry (`shared/parameter-registry.json`) with units, tolerances, timing budgets, thresholds, hysteresis, debounce, calibration, variant applicability.
**Rationale:** Per master prompt Section 5.133. Prevents scattered conflicting hard-coded values across requirements, design, tests, diagrams.
**Alternatives considered:** Parameters embedded in each artifact - rejected as source of inconsistency.

### 6. Assumption registry with validity tracking
**Decision:** Explicit assumption registry (`shared/assumption-registry.json`) with validity conditions, invalidation consequences, review status.
**Rationale:** Per master prompt Section 5.131. Every important claim needs provenance. Unknowns must remain visible.
**Alternatives considered:** Assumptions embedded in requirements - rejected as they become hidden and untraceable.

### 7. Evidence classification orthogonal to outcome
**Decision:** Use execution_kind (none|actual_host_run|actual_simulation_run|synthetic_fixture) orthogonal to outcome (pass|fail|inconclusive|not_run|blocked).
**Rationale:** Per master prompt Section 11.240. Planning is not execution. Fabricated numbers = synthetic_fixture.
**Alternatives considered:** Combined status field - rejected as it conflates execution type with result.

### 8. Mutation scenarios and change lifecycles as corpus validation
**Decision:** Create 20+ isolated mutation scenarios and 3 change-lifecycle demos with evaluator-only oracle manifests.
**Rationale:** Per master prompt Section 16. Corpus-design minimum for validation. Keeps expected labels separate to avoid answer leakage.
**Alternatives considered:** Fewer scenarios - rejected as insufficient for validation coverage.

### 9. Validation tooling as Python CLI
**Decision:** Implement corpus tooling as `python3 docs/artifacts/tools/corpus.py` with inventory, validate, coverage, trace, impact, render, export, scenario-test, check commands.
**Rationale:** Per master prompt Section 18. Python available in repo, good JSON Schema libraries, cross-platform.
**Alternatives considered:** Shell scripts - rejected for complex validation logic; Node.js - rejected as not in repo toolchain.

### 10. 15 separate completion dimensions
**Decision:** Report scope_accounting, artifact_population, standards_mapping, source_grounding, traceability_integrity, semantic_consistency_checks, automated_review_coverage, verification_planning, actual_product_evidence, synthetic_fixture_coverage, negative_scenario_validation, export_reproducibility, human_approval, production_authorization separately.
**Rationale:** Per master prompt Section 19. Structural mapping coverage is not conformity. Actual product evidence may be incomplete even when synthetic corpus is complete.
**Alternatives considered:** Single composite score - rejected as it hides gaps.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Scope creep: corpus generation never completes | Fixed 15-dimension gates; `synthetic_ready_with_limitations` status documents genuine gaps |
| Synthetic content mistaken for observed evidence | Two-profile architecture with field-level provenance; all synthetic content labeled |
| Normative standard text reproduction | Rights policy prohibits reproduction; only metadata/methodology mappings |
| Mutation scenarios incomplete (target 20, may deliver fewer) | `synthetic_ready_with_limitations` status documents gap; negative_scenario_validation dimension tracks it |
| Human approval pending for all artifacts | Explicit `human_approval_status: pending` on all artifacts; `production_authorized: false` |
| Target hardware unavailable for verification | `execution_kind: blocked` for HW tests; `synthetic_fixture` for timing analysis |
| Rights-sensitive standard text | Policy: no normative text reproduction; only permitted metadata/methodology mappings |
| Mutation scenarios target 20, may deliver fewer | Documented in negative_scenario_validation dimension; clean controls prevent false positives |
| Evaluator manifests not in normal corpus | Stored in `scenarios/evaluator-only/`; separate from ingestible dataset |

## Migration Plan

Not applicable - this creates new corpus artifacts under `docs/artifacts/` without modifying existing foxBMS code. The corpus is additive only.

**Rollback:** Delete `docs/artifacts/` directory (except preserved master prompt in `_control/`).

## Open Questions

1. **Exact ASPICE PAM 4.1 process attribute coverage** - The master prompt requires capability examples through highest level. Need to determine which process attributes (PA1.1-PA6.2) get synthetic examples for each of the 27 processes. *Deferrable: can be added during full generation phase.*

2. **Exact FMEDA methodology for HW quantitative analysis** - Master prompt requires "reproducible arithmetic, units, classifications, sensitivity" but warns "never represent invented supplier reliability data as qualified evidence." Need to select illustrative methodology (e.g., IEC 62380, SN 29500) and label calculations as illustrative. *Deferrable: can be decided during hardware domain generation.*

3. **Exact FreeRTOS task set for synthetic_reference** - Need to define the task set, priorities, periods, stack sizes, and WCET bounds for the hypothetical BMS. *Deferrable: can be derived from foxBMS task config during software domain generation.*

4. **Evaluator manifest format for mutation scenarios** - Need to define JSON structure for oracle manifests kept in `scenarios/evaluator-only/`. *Deferrable: can be defined when first mutation scenario is implemented.*