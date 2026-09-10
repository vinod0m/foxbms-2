# schemas Specification

## Purpose

Defines JSON schemas for all artifact types in the foxBMS 2 lifecycle artifact corpus, validated by published JSON Schemas (draft-07).

## Requirements

### Requirement: Base artifact schema
The corpus SHALL provide a base schema (`artifact-base.schema.json`) defining common fields: id, revision, schema_version, artifact_type, engineering_domain, profile, scenario_id, baseline_id, variant_applicability, title, owner_role, origin, source_refs, assumption_refs, standards_mappings, lifecycle_status, automated_review_status, human_approval_status, production_authorized, product_verification_credit, created_at, updated_at, revision_history.

#### Scenario: All artifacts validate against base schema
- **WHEN** any artifact is created or validated
- **THEN** it passes validation against `artifact-base.schema.json`

### Requirement: Requirement artifact schema
The corpus SHALL provide a requirement schema (`requirement.schema.json`) extending base with statement, rationale, classification, acceptance_criteria, verification_approach, safety_allocation, assumptions, conditions_modes, feasibility_dependencies.

#### Scenario: Safety requirements include ASIL allocation
- **WHEN** a safety requirement is validated
- **THEN** it includes safety_allocation with ASIL level and safety_goal_ref

### Requirement: Design artifact schema
The corpus SHALL provide a design schema (`design.schema.json`) with design_level, responsibilities, decomposition, interfaces, behavior_model, constraints, budgets, failure_response, decisions, implementation_mapping.

#### Scenario: Software designs include state machine behavior
- **WHEN** a software design is validated
- **THEN** it includes behavior_model with states and transitions

### Requirement: Test measure schema
The corpus SHALL provide a test measure schema (`test_measure.schema.json`) with test_type, objective, referenced_requirements, referenced_designs, preconditions, environment, stimuli, steps, expected_outcomes, tolerances, timing, oracle_basis, cleanup, regression_selection.

#### Scenario: Test measures reference oracle basis
- **WHEN** a test measure is validated
- **THEN** it specifies oracle_basis as source_grounded, analytical_model, synthetic_assumption, or measured_reference

### Requirement: Execution artifact schema
The corpus SHALL provide an execution schema (`execution.schema.json`) with test_measure_id, test_measure_revision, execution_kind (none|actual_host_run|actual_simulation_run|synthetic_fixture), outcome, environment, input_hashes, output_hashes, logs, timestamps, anomalies, evidence_refs.

#### Scenario: Execution kind orthogonal to outcome
- **WHEN** an execution record is created
- **THEN** execution_kind and outcome are independently specified

### Requirement: Review artifact schema
The corpus SHALL provide a review schema (`review.schema.json`) with review_type, reviewed_ids (with revision and digest), reviewer_identity, checklist_version, scope, findings, dispositions, limitations.

#### Scenario: Review records include all reviewed artifact digests
- **WHEN** a review is created
- **THEN** reviewed_ids contains artifact_id, revision, and content digest for each artifact

### Requirement: Link artifact schema
The corpus SHALL provide a link schema (`link.schema.json`) with all 17 relation types (refines, allocated_to, implements, verifies, validates, result_of, supports, mitigates, specified_by, consumes, produces, depends_on, constrained_by, reviewed_by, changes, supersedes) and required metadata fields.

#### Scenario: All links include change suspect status
- **WHEN** a link is created
- **THEN** it includes change_suspect_status boolean field

### Requirement: Source anchor schema
The corpus SHALL provide a source anchor schema (`source_anchor.schema.json`) supporting code, hardware, documentation, and test source types with durable location information and content hashes.

#### Scenario: Code anchors include working file hash
- **WHEN** a code source anchor is created for a changed local file
- **THEN** it includes working_file_hash in addition to commit hash

### Requirement: Change artifact schema
The corpus SHALL provide a change schema (`change.schema.json`) with change_type, trigger, impact_analysis, decision, new_revisions, suspect_links, required_updates, reverification_selection, post_change_baseline.

#### Scenario: Change lifecycle tracks suspect links
- **WHEN** a change is recorded
- **THEN** suspect_links array identifies all link IDs marked as suspect due to the change

### Requirement: Finding artifact schema
The corpus SHALL provide a finding schema (`finding.schema.json`) with severity, category, evidence, disposition, impact, root_cause, resolution.

#### Scenario: Findings include disposition tracking
- **WHEN** a finding is resolved
- **THEN** it includes disposition, action, and resolved_artifact_id

### Requirement: Scenario artifact schema
The corpus SHALL provide a scenario schema (`scenario.schema.json`) with scenario_type (mutation|change_lifecycle), baseline_ref, patch, affected_ids, trigger, expected_detector, expected_finding, impact_paths, expected_remediation.

#### Scenario: Mutation scenarios include oracle manifest reference
- **WHEN** a mutation scenario is created
- **THEN** it references an evaluator-only manifest with expected labels
