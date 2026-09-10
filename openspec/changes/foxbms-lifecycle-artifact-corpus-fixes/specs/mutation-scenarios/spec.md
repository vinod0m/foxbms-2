## Purpose

Defines 20 isolated mutation scenarios for corpus validation, each derived from a pinned clean baseline with documented patch, affected IDs, trigger, expected detector, expected finding, impact paths, and expected remediation.

## ADDED Requirements

### Requirement: Isolated mutation scenarios (20 minimum)
The corpus SHALL create 20 isolated mutation scenarios, each derived reproducibly from a pinned clean baseline with documented patch, affected IDs, trigger, expected detector/rule, expected finding, impact paths, and expected remediation.

#### Scenario: Mutation detector finds missing parent link
- **WHEN** SCN-MUT-001 (missing refines link FSR→SG) is applied
- **THEN** traceability checker detects "FSR has no parent safety goal" finding with severity high

### Requirement: Mutation scenario categories covered (18 additional)
The corpus SHALL cover mutations for: stale revisions/reviews, unit/scaling mismatch, HW/SW pin or polarity mismatch, incompatible timing budgets, contradictory thresholds, missing fault reaction, unsupported ASIL downgrade, false diagnostic coverage, invalid configuration combinations, fabricated evidence classification, unjustified non-applicability, dangling evidence, duplicate identity, source-anchor drift, unsafe workflow state promotion, incomplete change propagation, circular refinement, missing verification link.

#### Scenario: Invalid link type detected
- **WHEN** SCN-MUT-002 (link type changed to 'related_to') is applied
- **THEN** link validator detects "invalid relation_type 'related_to'" finding with severity high

### Requirement: Stale revision/review mutation
The corpus SHALL create a mutation where an artifact's revision is stale (referenced revision doesn't match current).

#### Scenario: Stale revision detected
- **WHEN** SCN-MUT-003 (stale revision) is applied
- **THEN** validator detects "artifact revision mismatch" finding with severity high

### Requirement: Unit/scaling mismatch mutation
The corpus SHALL create a mutation where a parameter's unit or scaling factor is changed inconsistently.

#### Scenario: Unit mismatch detected
- **WHEN** SCN-MUT-004 (unit mismatch) is applied
- **THEN** validator detects "parameter unit inconsistency" finding with severity high

### Requirement: HW/SW pin or polarity mismatch mutation
The corpus SHALL create a mutation where HSI pin assignment or polarity conflicts with hardware design.

#### Scenario: Pin/polarity mismatch detected
- **WHEN** SCN-MUT-005 (pin/polarity mismatch) is applied
- **THEN** lateral consistency check detects "HSI pin/polarity mismatch" finding with severity high

### Requirement: Incompatible timing budgets mutation
The corpus SHALL create a mutation where timing budget sums exceed FTTI.

#### Scenario: Timing budget violation detected
- **WHEN** SCN-MUT-006 (timing budget overflow) is applied
- **THEN** semantic rule detects "timing budget exceeds FTTI" finding with severity high

### Requirement: Contradictory thresholds mutation
The corpus SHALL create a mutation where safety thresholds contradict (e.g., warning > derating > shutdown violated).

#### Scenario: Threshold contradiction detected
- **WHEN** SCN-MUT-007 (threshold contradiction) is applied
- **THEN** semantic rule detects "threshold order violation" finding with severity high

### Requirement: Missing fault reaction mutation
The corpus SHALL create a mutation where a safety requirement lacks a fault reaction mechanism.

#### Scenario: Missing fault reaction detected
- **WHEN** SCN-MUT-008 (missing fault reaction) is applied
- **THEN** semantic rule detects "safety requirement missing fault reaction" finding with severity high

### Requirement: Unsupported ASIL downgrade mutation
The corpus SHALL create a mutation where an ASIL is downgraded without justification.

#### Scenario: ASIL downgrade detected
- **WHEN** SCN-MUT-009 (ASIL downgrade) is applied
- **THEN** semantic rule detects "unsupported ASIL downgrade" finding with severity high

### Requirement: False diagnostic coverage mutation
The corpus SHALL create a mutation where diagnostic coverage claims are false/unsupported.

#### Scenario: False diagnostic coverage detected
- **WHEN** SCN-MUT-010 (false diagnostic coverage) is applied
- **THEN** semantic rule detects "unsupported diagnostic coverage claim" finding with severity high

### Requirement: Invalid configuration combination mutation
The corpus SHALL create a mutation where parameter configuration is invalid (mutually exclusive options enabled).

#### Scenario: Invalid config combination detected
- **WHEN** SCN-MUT-011 (invalid config) is applied
- **THEN** semantic rule detects "invalid configuration combination" finding with severity high

### Requirement: Fabricated evidence classification mutation
The corpus SHALL create a mutation where synthetic evidence is misclassified as actual product evidence.

#### Scenario: Fabricated evidence detected
- **WHEN** SCN-MUT-011 (fabricated evidence) is applied
- **THEN** semantic rule detects "execution_kind mismatch: synthetic_fixture labeled as actual_host_run" finding with severity high

### Requirement: Unjustified non-applicability mutation
The corpus SHALL create a mutation where a requirement is marked non-applicable without justification.

#### Scenario: Unjustified N/A detected
- **WHEN** SCN-MUT-012 (unjustified N/A) is applied
- **THEN** semantic rule detects "requirement marked non-applicable without justification" finding with severity medium

### Requirement: Dangling evidence mutation
The corpus SHALL create a mutation where evidence references non-existent artifacts.

#### Scenario: Dangling evidence detected
- **WHEN** SCN-MUT-012 (dangling evidence) is applied
- **THEN** link validator detects "dangling evidence reference" finding with severity high

### Requirement: Duplicate identity mutation
The corpus SHALL create a mutation where two artifacts share the same ID within the same profile.

#### Scenario: Duplicate ID detected
- **WHEN** SCN-MUT-013 (duplicate ID) is applied
- **THEN** identity checker detects "duplicate artifact ID within profile" finding with severity high

### Requirement: Source anchor drift mutation
The corpus SHALL create a mutation where a source anchor's symbol or line range drifts from actual code.

#### Scenario: Source anchor drift detected
- **WHEN** SCN-MUT-013 (source anchor drift) is applied
- **THEN** provenance checker detects "source anchor symbol/line mismatch" finding with severity high

### Requirement: Unsafe workflow promotion mutation
The corpus SHALL create a mutation where an artifact with `production_authorized=false` is promoted to approved without human review.

#### Scenario: Unsafe promotion detected
- **WHEN** SCN-MUT-014 (unsafe promotion) is applied
- **THEN** governance check detects "production_authorized=true without human_approval_status=approved" finding with severity high

### Requirement: Incomplete change propagation mutation
The corpus SHALL create a mutation where a change fails to propagate to all dependent artifacts.

#### Scenario: Incomplete propagation detected
- **WHEN** SCN-MUT-014 (incomplete propagation) is applied
- **THEN** impact analysis detects "change impact missing dependent artifacts" finding with severity high

### Requirement: Circular refinement mutation
The corpus SHALL create a mutation where a refinement chain forms a cycle.

#### Scenario: Circular refinement detected
- **WHEN** SCN-MUT-015 (circular refinement) is applied
- **THEN** traceability checker detects "circular refinement chain" finding with severity high

### Requirement: Missing verification link mutation
The corpus SHALL create a mutation where a safety requirement lacks verifies/validates links.

#### Scenario: Missing verification link detected
- **WHEN** SCN-MUT-015 (missing verification) is applied
- **THEN** semantic rule detects "safety requirement has no verifies/validates link" finding with severity medium

### Requirement: Multi-defect interactions
The corpus SHALL include controlled multi-defect interaction scenarios after isolated cases, plus legitimate exceptions and clean controls so a checker cannot pass by flagging everything.

#### Scenario: Multi-defect scenario combines timing and threshold errors
- **WHEN** SCN-MUT-016 (multi-defect timing+threshold) is applied
- **THEN** both expected findings are detected independently

### Requirement: Evaluator-only oracle separation
The corpus SHALL keep expected labels/oracles outside the normal ingestible engineering dataset, with a separate evaluator manifest to avoid answer leakage.

#### Scenario: Oracle manifest not in normal corpus
- **WHEN** mutation scenario is validated
- **THEN** expected findings are in `scenarios/evaluator-only/` not in normal corpus
