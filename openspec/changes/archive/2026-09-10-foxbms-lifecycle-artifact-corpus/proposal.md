## Why

The foxBMS 2 repository contains a production-grade BMS development platform, but lacks a comprehensive, traceable engineering corpus that spans the full ISO 26262 / Automotive SPICE lifecycle. This corpus is needed to support change-impact analysis, review workflows, consistency checking, and import into future SoftwareDevLabs adapters without depending on a particular ALM database.

## What Changes

- Create a complete, structured engineering dataset under `docs/artifacts/` covering concept, system, hardware, software, integration, verification, validation, release, production, operation, service, change, and decommissioning phases
- Establish two explicitly separated profiles: `as_is` (faithful reconstruction of pinned foxBMS sources) and `synthetic_reference` (complete hypothetical automotive BMS project grounded in foxBMS)
- Define canonical JSON schemas for all artifact types with field-level provenance tracking
- Build a traceability graph with 17 typed link relations supporting vertical, reverse, lateral, and lifecycle traversal
- Generate 20+ mutation scenarios and 3 change-lifecycle demonstrations for corpus validation
- Implement machine checks for semantic consistency (10 check categories) and structured review loops
- Produce final acceptance reports with 15 separate completion dimensions

## Capabilities

### New Capabilities

- `lifecycle-corpus/governance`: Corpus policy, standards locking, scope/applicability, coverage planning, role/review policies
- `lifecycle-corpus/schemas`: JSON schemas for artifacts, typed payloads, links, source anchors, parameters, assumptions, baselines, reviews, findings, test measures, executions, changes, applicability decisions, scenario expectations
- `lifecycle-corpus/source-registry`: Durable source anchors for code, hardware, documentation, tests with content hashes
- `lifecycle-corpus/traceability`: Canonical typed links partitioned by profile, link rules, query utilities
- `lifecycle-corpus/as-is-profile`: Faithful reconstruction artifacts for safety, system, hardware, software, verification domains
- `lifecycle-corpus/synthetic-reference-profile`: Hypothetical engineering records for safety, system, hardware, software, verification, management domains
- `lifecycle-corpus/parameter-registry`: Coherent parameter registry with units, tolerances, timing budgets, thresholds, calibration
- `lifecycle-corpus/assumption-registry`: Explicit assumptions with validity conditions and invalidation consequences
- `lifecycle-corpus/scenarios`: 20+ isolated mutation scenarios and 3 change-lifecycle demonstrations
- `lifecycle-corpus/reviews`: Review records, findings, closure with AI/human approval tracking
- `lifecycle-corpus/validation`: Executable validation tooling (inventory, validate, coverage, trace, impact, render, export, scenario-test, check)
- `lifecycle-corpus/reports`: Final reports for coverage, standards mapping, traceability, consistency, review summary, gaps, verification evidence, scenario validation, reproducibility, final acceptance

### Modified Capabilities

None - this is a new corpus creation effort.

## Impact

- New directory structure under `docs/artifacts/` with governance, schemas, sources, corpus (as_is, synthetic_reference, shared), traceability, views, evidence, reviews, scenarios, exports, tools, tests, reports
- All artifacts conform to defined JSON schemas with schema_version, provenance, standards mappings
- No modifications to existing foxBMS source code, hardware files, configuration, or tests
- No implementation fixes, board changes, commits, pushes, branch switching, reset/clean, or submodule updates
- All writes restricted to `docs/artifacts/` boundary with `.work/` for temporary workspaces