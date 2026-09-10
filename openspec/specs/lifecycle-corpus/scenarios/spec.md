# scenarios Specification

## Purpose

Defines 20+ isolated mutation scenarios and 3 complete change-lifecycle demonstrations for corpus validation, with expected findings kept separate in evaluator-only manifests.

## Requirements

### Requirement: Isolated mutation scenarios (minimum 20)
The corpus SHALL create at least 20 isolated mutation scenarios, each derived reproducibly from a pinned clean baseline with documented patch, affected IDs, trigger, expected detector/rule, expected finding, impact paths, and expected remediation.

#### Scenario: Mutation detector finds missing parent link
- **WHEN** SCN-MUT-001 (missing refines link FSR→SG) is applied
- **THEN** traceability checker detects "FSR has no parent safety goal" finding with severity high

### Requirement: Mutation scenario categories covered
The corpus SHALL cover mutations for: missing parent/verification links, invalid link types, stale revisions/reviews, unit/scaling mismatch, HW/SW pin or polarity mismatch, incompatible timing budgets, contradictory thresholds, missing fault reaction, unsupported ASIL downgrade, false diagnostic coverage, invalid configuration combinations, fabricated evidence classification, unjustified non-applicability, dangling evidence, duplicate identity, source-anchor drift, unsafe workflow state promotion, incomplete change propagation.

#### Scenario: Invalid link type detected
- **WHEN** SCN-MUT-002 (link type changed to 'related_to') is applied
- **THEN** link validator detects "invalid relation_type 'related_to'" finding with severity high

### Requirement: Multi-defect interactions
The corpus SHALL include controlled multi-defect interaction scenarios after isolated cases, plus legitimate exceptions and clean controls so a checker cannot pass by flagging everything.

#### Scenario: Multi-defect scenario combines timing and threshold errors
- **WHEN** a multi-defect scenario with timing budget violation and threshold contradiction is applied
- **THEN** both expected findings are detected independently

### Requirement: Evaluator-only oracle separation
The corpus SHALL keep expected labels/oracles outside the normal ingestible engineering dataset, with a separate evaluator manifest to avoid answer leakage.

#### Scenario: Oracle manifest not in normal corpus
- **WHEN** mutation scenario is validated
- **THEN** expected findings are in `scenarios/evaluator-only/` not in normal corpus

### Requirement: Change lifecycle demonstrations (minimum 3)
The corpus SHALL create 3 complete change-lifecycle demonstrations: safety-related threshold/timing change, HSI/hardware interface change, software behavioral defect/change.

#### Scenario: Voltage threshold change demonstrates full lifecycle
- **WHEN** SCN-CHG-001 (cell_voltage_max 4.2V→4.15V) is executed
- **THEN** it shows baseline, trigger, impact analysis (6 artifacts, 2 links, 1 review, 1 evidence), decision, 6 new revisions, 1 suspect link, 8 updates, 3 reverification tests, clean post-change baseline

### Requirement: HSI interface change lifecycle
The corpus SHALL demonstrate an AFE communication interface change (LTC6811 isoSPI → ADI ADES1830 SPI/DMA) with cross-domain impact on HW, SW, HSI, verification, and independent monitor.

#### Scenario: AFE interface change affects independent monitor
- **WHEN** SCN-CHG-002 is executed
- **THEN** impact analysis includes independent monitor redesign requirement

### Requirement: Software behavioral defect lifecycle
The corpus SHALL demonstrate a SOA debounce logic defect (counter not reset on recovery) with state machine correction, new test case, and reverification.

#### Scenario: Debounce defect fix includes new transient test
- **WHEN** SCN-CHG-003 is executed
- **THEN** reverification includes new test: 3 transients of 4300mV for 50ms each → no fault

### Requirement: Change invalidates dependent reviews/evidence
The corpus SHALL ensure changes invalidate dependent review/evidence where appropriate, with merge/conflict handling and superseded artifacts recorded.

#### Scenario: Change marks suspect links and stale reviews
- **WHEN** any change lifecycle is executed
- **THEN** suspect_links array identifies affected links, affected_reviews lists stale reviews
