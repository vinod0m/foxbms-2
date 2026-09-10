# reports Specification

## Purpose

Defines the required final reports for the foxBMS 2 lifecycle artifact corpus with machine-readable data and cross-domain walkthroughs.

## Requirements

### Requirement: Coverage report
The corpus SHALL produce `reports/coverage-report.md` and machine-readable data with scope accounting, artifact population, standards mapping, source grounding, traceability integrity, semantic consistency, automated review coverage, verification planning, actual product evidence, synthetic fixture coverage, negative scenario validation, export reproducibility.

#### Scenario: Coverage report has separate completion dimensions
- **WHEN** coverage report is generated
- **THEN** it includes all 15 completion dimensions with numerators/denominators

### Requirement: Standards mapping report
The corpus SHALL produce `reports/standards-mapping-report.md` with ISO 26262 part mapping, ASPICE process mapping, capability dimension examples, and gap analysis.

#### Scenario: Standards mapping shows all process dispositions
- **WHEN** standards mapping report is generated
- **THEN** all 27 ASPICE processes and 12 ISO parts have explicit dispositions

### Requirement: Traceability report
The corpus SHALL produce `reports/traceability-report.md` with vertical chains, reverse queries, lateral consistency, change impact, and lateral HW/SW interface consistency.

#### Scenario: Traceability report includes 5 cross-domain walkthroughs
- **WHEN** traceability report is generated
- **THEN** it includes walkthroughs for voltage protection, temperature protection, current limits, precharge/contactor, communication/watchdog

### Requirement: Consistency report
The corpus SHALL produce `reports/consistency-report.md` with results of all 10 semantic consistency check categories and findings summary.

#### Scenario: Consistency report documents resolved findings
- **WHEN** consistency report is generated
- **THEN** it shows FTTI budget violation resolved in synthetic_reference via independent monitor

### Requirement: Review summary report
The corpus SHALL produce `reports/review-summary.md` with review coverage, findings by severity/category, dispositions, and limitations.

#### Scenario: Review summary shows AI review limitations
- **WHEN** review summary is generated
- **THEN** it includes "AI reviews are automated reviews..." disclaimer

### Requirement: Source vs synthetic gap report
The corpus SHALL produce `reports/source-vs-synthetic-gap-report.md` documenting gaps between as_is and synthetic_reference profiles by category.

#### Scenario: Gap report quantifies missing artifacts
- **WHEN** gap report is generated
- **THEN** it shows 1/20 features fully generated, 18 features parameters-only

### Requirement: Verification evidence report
The corpus SHALL produce `reports/verification-evidence-report.md` with execution kinds, outcomes, oracle basis analysis, and coverage by requirement.

#### Scenario: Evidence report separates execution kinds
- **WHEN** verification evidence report is generated
- **THEN** it distinguishes actual_host_run, synthetic_fixture, blocked, not_run

### Requirement: Scenario validation report
The corpus SHALL produce `reports/scenario-validation-report.md` with mutation scenario results, change lifecycle demonstrations, evaluator manifest status.

#### Scenario: Scenario report shows 2/20 mutations implemented
- **WHEN** scenario validation report is generated
- **THEN** it reports mutation completion 10% and change lifecycle 100%

### Requirement: Reproducibility report
The corpus SHALL produce `reports/reproducibility-report.md` with round-trip tests, determinism, tool versions, export consistency.

#### Scenario: Reproducibility report validates round-trip
- **WHEN** reproducibility report is generated
- **THEN** it shows Export->Import->Export produces identical content

### Requirement: Final acceptance report
The corpus SHALL produce `reports/final-acceptance-report.md` with gate results, dimension scores, artifact counts, walkthroughs, limitations, and final corpus status.

#### Scenario: Final report determines corpus status
- **WHEN** final acceptance report is generated
- **THEN** it outputs `synthetic_ready_with_limitations` with precise criteria

### Requirement: Machine-readable data for all reports
Each report SHALL have corresponding machine-readable JSON data in the same directory.

#### Scenario: Report JSON matches Markdown
- **WHEN** reports are validated
- **THEN** JSON data matches Markdown content

### Requirement: README with corpus documentation
The corpus SHALL produce `README.md` explaining the two profiles, source/standards baseline, directory structure, warning labels, how to explore/query/import, how to run checks, how to regenerate/export, how to resume, and how changes invalidate links/reviews/evidence.

#### Scenario: README contains all required sections
- **WHEN** README is reviewed
- **THEN** it includes all 10 required documentation sections
