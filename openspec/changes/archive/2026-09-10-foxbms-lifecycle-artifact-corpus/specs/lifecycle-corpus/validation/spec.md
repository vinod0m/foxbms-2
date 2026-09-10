## Purpose

Defines executable validation and maintenance tooling for the foxBMS 2 lifecycle artifact corpus with a documented CLI supporting inventory, validate, coverage, trace, impact, render, export, scenario-test, and check functions.

## ADDED Requirements

### Requirement: Corpus CLI tool
The corpus SHALL provide a documented CLI at `tools/corpus.py` (or equivalent) supporting: inventory, validate, coverage, trace, impact, render, export, scenario-test, check.

#### Scenario: CLI runs all validation functions
- **WHEN** `python3 tools/corpus.py check` is executed
- **THEN** all validation functions run and exit with nonzero on failure

### Requirement: Inventory function
The inventory function SHALL build/check source and feature inventories against the actual repository.

#### Scenario: Inventory matches actual repository
- **WHEN** inventory runs
- **THEN** it reports 612 source files, 20 features, 24 variants matching actual repository

### Requirement: Validate function
The validate function SHALL run schema validation, identity checks, link validation, provenance checks, and semantic consistency rules.

#### Scenario: Schema validation catches invalid artifacts
- **WHEN** an artifact violates its schema
- **THEN** validate reports the specific schema error with artifact ID and field

### Requirement: Coverage function
The coverage function SHALL compute process, feature, implementation, and evidence coverage with explicit numerators/denominators from inventories.

#### Scenario: Coverage reports separate dimensions
- **WHEN** coverage runs
- **THEN** it outputs scope_accounting, artifact_population, standards_mapping, source_grounding, traceability_integrity, semantic_consistency_checks, automated_review_coverage, verification_planning, actual_product_evidence, synthetic_fixture_coverage, negative_scenario_validation, export_reproducibility

### Requirement: Trace function
The trace function SHALL query forward/reverse/lateral paths for any artifact ID.

#### Scenario: Trace finds vertical chain
- **WHEN** `trace FB2-SAF-HAZ-000001` is executed
- **THEN** it returns the complete path to evidence

### Requirement: Impact function
The impact function SHALL calculate typed transitive impact from changed IDs/revisions.

#### Scenario: Impact analysis identifies all affected artifacts
- **WHEN** `impact FB2-PRM-000001` is executed
- **THEN** it lists all dependent artifacts, links, reviews, and evidence

### Requirement: Render function
The render function SHALL regenerate human-readable views (Markdown, CSV, diagrams) from canonical JSON data.

#### Scenario: Views match canonical data
- **WHEN** render runs
- **THEN** all views in `views/` are regenerated from `corpus/` with matching content

### Requirement: Export function
The export function SHALL produce portable JSONL nodes/edges, CSV inventory/trace matrices, Markdown work products, baseline/content manifests with documented import contract.

#### Scenario: Export includes import contract
- **WHEN** export runs
- **THEN** output includes schema_version, profile/scenario boundaries, provenance, link semantics, approval/evidence semantics

### Requirement: Scenario-test function
The scenario-test function SHALL apply isolated mutations and compare actual findings against expected findings from evaluator manifests.

#### Scenario: Mutation test detects expected finding
- **WHEN** `scenario-test SCN-MUT-001` runs
- **THEN** it reports finding FB2-FND-MUT-001 detected with correct severity

### Requirement: Check function (acceptance suite)
The check function SHALL run the complete offline corpus acceptance suite and fail with nonzero exit status on failed acceptance checks.

#### Scenario: Check enforces all gates
- **WHEN** `check` runs
- **THEN** it validates all 15 completion dimensions and exits nonzero if any gate fails

### Requirement: Unit/integration tests for validators
The corpus SHALL provide tests for validators covering: valid/invalid schemas, duplicate IDs, dangling links, incorrect types, invalid state changes, version mismatch, profile contamination, source drift, export consistency, numerical constraints.

#### Scenario: Mutation scenarios demonstrate defect detection
- **WHEN** validator tests run
- **THEN** each mutation scenario produces its expected detection

### Requirement: Offline determinism and reproducibility
The corpus SHALL ensure offline determinism, idempotent regeneration, clean import/export round-trip preservation, and incremental maintenance after changes.

#### Scenario: Unchanged baseline yields unchanged exports
- **WHEN** corpus is regenerated without changes
- **THEN** all exports have identical content hashes (excluding run metadata)

### Requirement: Graph reachability validation
The corpus SHALL validate graph reachability independently of rendering code where practical.

#### Scenario: All vertical chains resolve
- **WHEN** graph validation runs
- **THEN** all required vertical paths from hazard to evidence are traversable

## REMOVED Requirements

None - new capability.