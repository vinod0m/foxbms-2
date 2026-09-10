# reviews Specification

## Purpose

Defines the review organization and substantive review loop for the foxBMS 2 lifecycle artifact corpus, including domain reviews, cross-domain reviews, adversarial reviews, and AI review limitations tracking.

## Requirements

### Requirement: Review roles and responsibilities
The corpus SHALL define review responsibilities for: architect/integrator (scope, schemas, shared decisions, allocation, cross-domain integration, gates), system/safety/hardware/software authors (inspect evidence, author canonical records), verification author (measures, execution classification, trace coverage), traceability/data engineer (graph, schemas, exports, metrics), domain reviewers (correctness, safety/standards mapping, provenance, verification quality, cross-domain consistency), adversarial reviewer (challenge false completeness, unsupported source links, weak oracles, variant contamination, circular arguments, fake approvals, metric gaming).

#### Scenario: Each artifact has assigned author and reviewer
- **WHEN** review is scheduled
- **THEN** it has an authoritative owner and at least one independent reviewer

### Requirement: Required reviews per artifact
Every engineering artifact SHALL receive: source/provenance check, type-specific completeness check, local domain check, relevant cross-domain check, verification/traceability check. Safety-critical artifacts SHALL receive an additional separated challenge pass.

#### Scenario: Safety-critical artifact gets challenge pass
- **WHEN** a safety-critical artifact (FSR, TSR, SWR) is reviewed
- **THEN** it receives both domain review and adversarial challenge pass

### Requirement: Review record structure
Each review SHALL record: reviewed IDs with exact revisions and content digests, reviewer identity (role, session_id, model), checklist version, scope, findings (with severity, category, evidence), dispositions (with action, resolved_artifact_id), limitations.

#### Scenario: Review record includes AI model identity
- **WHEN** AI-assisted review is recorded
- **THEN** reviewer_identity includes model (e.g., nvidia/nemotron-3-ultra-550b-a55b) and session_id

### Requirement: Batch review rules
Batch reviews MAY cover multiple records only when all covered IDs/digests and findings are enumerated. Universal review from a sample is prohibited.

#### Scenario: Batch review enumerates all artifacts
- **WHEN** a batch review is created
- **THEN** reviewed_ids lists every artifact ID, revision, and digest

### Requirement: Adversarial review scope
Adversarial reviewer SHALL challenge: false completeness, unsupported source links, weak oracles, variant contamination, circular arguments, fake approvals, metric gaming.

#### Scenario: Adversarial review finds false completeness
- **WHEN** adversarial review runs on vertical slice
- **THEN** it checks if all required work products exist or are explicitly documented as gaps

### Requirement: Review limitations recorded
Every review SHALL explicitly record limitations of AI review: "AI reviews are automated reviews. Distinct agent sessions are not organizational independence or human confirmation measures. Real human approval remains pending."

#### Scenario: AI review limitation statement present
- **WHEN** any review record is created
- **THEN** it includes limitations field with AI review disclaimer

### Requirement: Review closure and dispositions
Findings SHALL have dispositions (accepted, rejected, deferred, partial, in_progress) with actions and resolved_artifact_id. Closure records SHALL track when all findings for a review are resolved.

#### Scenario: Finding disposition creates new artifact revision
- **WHEN** finding disposition=accepted with action
- **THEN** resolved_artifact_id points to the new revision created to fix the finding

### Requirement: Human approval tracking
All artifacts SHALL have human_approval_status (pending|approved|rejected|not_required) defaulting to pending. Synthetic decisions SHALL be labeled synthetic_decision with fictional role identities.

#### Scenario: No artifact has human approval without explicit record
- **WHEN** artifact is created
- **THEN** human_approval_status=pending unless explicitly set otherwise
