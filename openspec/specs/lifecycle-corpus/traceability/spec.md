# traceability Specification

## Purpose

Defines the canonical traceability graph with typed links supporting vertical, reverse, lateral, and lifecycle traversal across all engineering artifacts.

## Requirements

### Requirement: Canonical link registry
The corpus SHALL maintain a canonical link registry (`traceability/link-registry/`) partitioned by profile (`as_is`, `synthetic_reference`) with all 17 required relation types: refines, allocated_to, implements, verifies, validates, result_of, supports, mitigates, specified_by, consumes, produces, depends_on, constrained_by, reviewed_by, changes, supersedes.

#### Scenario: Links partitioned by profile
- **WHEN** links are queried
- **THEN** they are retrievable separately for `as_is` and `synthetic_reference` profiles

### Requirement: Vertical traceability chains
The corpus SHALL support complete vertical paths: Operational scenario → hazardous event → safety goal → functional safety requirement → technical/system safety requirement → system architecture → HW/SW requirements → HW/SW architecture → detailed design → implementation → verification measure → execution/evidence → review → safety argument.

#### Scenario: Vertical chain traversable end-to-end
- **WHEN** a vertical chain query is executed for cell voltage protection
- **THEN** all links from hazard to evidence are resolvable

### Requirement: Reverse traceability
The corpus SHALL support reverse queries from any artifact to its upstream sources (e.g., from implementation to requirements to hazards).

#### Scenario: Implementation traces back to safety goal
- **WHEN** reverse query from contactor driver code
- **THEN** path reaches safety goal via SWR, FSR, SG, hazard

### Requirement: Lateral traceability
The corpus SHALL explicitly represent lateral dependencies: same-level requirement constraints, HW/SW allocation vs responsibilities, HW pins vs HSI vs driver assumptions, producer/consumer data APIs, shared safety mechanisms, architecture vs design vs code vs test consistency.

#### Scenario: HW/SW interface consistency checked
- **WHEN** lateral consistency check runs
- **THEN** HSI signal definitions match between HW TSRs and SW SWRs

### Requirement: Lifecycle traceability
The corpus SHALL support change-impact-to-reverification paths: change request → affected artifacts → suspect links → affected reviews → affected evidence → reverification selection → clean post-change baseline.

#### Scenario: Change impact analysis identifies all affected artifacts
- **WHEN** a parameter change is analyzed (e.g., cell_voltage_max 4.2V → 4.15V)
- **THEN** all dependent artifacts, links, reviews, and evidence are identified

### Requirement: Link metadata completeness
Every link SHALL include: link_id, source_id/revision, target_id/revision, relation_type, profile, scenario_id, baseline_id, variant_applicability, rationale, provenance, review_state, change_suspect_status.

#### Scenario: Link metadata validated
- **WHEN** link registry is validated
- **THEN** all links have all required metadata fields populated

### Requirement: Typed root and leaf exceptions
The corpus SHALL allow stakeholder needs, source anchors, policies, and findings as root exceptions (no fabricated parent), and safety/product requirements as leaf exceptions with appropriate realization/verification disposition.

#### Scenario: Stakeholder need has no parent requirement
- **WHEN** a stakeholder need is created
- **THEN** it does not require a refines link to a parent

### Requirement: Query and matrix utilities
The corpus SHALL provide forward/reverse queries and matrices for adjacent engineering levels, HW/SW interfaces, requirements-to-tests, tests-to-results, findings-to-fixes, and change-impact-to-reverification.

#### Scenario: Traceability matrix generated
- **WHEN** matrix generation runs
- **THEN** CSV matrices are produced for all required traversal types
