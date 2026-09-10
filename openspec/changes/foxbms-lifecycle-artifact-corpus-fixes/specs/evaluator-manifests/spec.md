## Purpose

Defines evaluator-only oracle manifests for all mutation and change lifecycle scenarios, keeping expected labels/oracles outside the normal ingestible engineering dataset to avoid answer leakage.

## ADDED Requirements

### Requirement: Evaluator manifest structure
Each evaluator manifest SHALL be a JSON file in `scenarios/evaluator-only/<scenario-id>/oracle-manifest.json` containing expected findings with finding_id, severity, category, description, and affected artifact IDs.

#### Scenario: Mutation manifest matches expected finding
- **WHEN** SCN-MUT-001 evaluator manifest is queried
- **THEN** it contains expected finding FB2-FND-MUT-000001 with severity high, category traceability, description "FSR FB2-SAF-FSR-000001 has no parent safety goal (missing refines link)"

### Requirement: Mutation evaluator manifests (20)
The corpus SHALL create evaluator manifests for all 20 mutation scenarios in `scenarios/evaluator-only/SCN-MUT-XXX/`.

#### Scenario: Mutation manifest not in normal corpus
- **WHEN** mutation scenario is validated
- **THEN** expected findings are in `scenarios/evaluator-only/` not in normal corpus

### Requirement: Change lifecycle evaluator manifests (3)
The corpus SHALL create evaluator manifests for all 3 change lifecycle demonstrations in `scenarios/evaluator-only/SCN-CHG-XXX/`.

#### Scenario: Change lifecycle manifest not in normal corpus
- **WHEN** change lifecycle scenario is validated
- **THEN** expected findings are in `scenarios/evaluator-only/` not in normal corpus

### Requirement: Manifest schema compliance
Each evaluator manifest SHALL validate against a schema defining required fields: finding_id, severity, category, description, affected_ids, expected_detector.

#### Scenario: Manifest validates against schema
- **WHEN** evaluator manifest is validated
- **THEN** it passes schema validation with all required fields present

## REMOVED Requirements

None - new capability for this fix change.

## MODIFIED Requirements

### Requirement: Isolated mutation scenarios (minimum 20)
The corpus SHALL create 20 isolated mutation scenarios, each derived reproducibly from a pinned clean baseline with documented patch, affected IDs, trigger, expected detector/rule, expected finding, impact paths, and expected remediation.

#### Scenario: Mutation detector finds missing parent link
- **WHEN** SCN-MUT-001 (missing refines link FSR→SG) is applied
- **THEN** traceability checker detects "FSR has no parent safety goal" finding with severity high

### Requirement: Change lifecycle demonstrations (minimum 3)
The corpus SHALL create 3 complete change-lifecycle demonstrations: safety-related threshold/timing change, HSI/hardware interface change, software behavioral defect/change.

#### Scenario: Voltage threshold change demonstrates full lifecycle
- **WHEN** SCN-CHG-001 (cell_voltage_max 4.2V→4.15V) is executed
- **THEN** it shows baseline, trigger, impact analysis (6 artifacts, 2 links, 1 review, 1 evidence), decision, 6 new revisions, 1 suspect link, 8 updates, 3 reverification tests, clean post-change baseline

### Requirement: Evaluator-only oracle separation
The corpus SHALL keep expected labels/oracles outside the normal ingestible engineering dataset, with a separate evaluator manifest to avoid answer leakage.

#### Scenario: Oracle manifest not in normal corpus
- **WHEN** mutation scenario is validated
- **THEN** expected findings are in `scenarios/evaluator-only/` not in normal corpus
