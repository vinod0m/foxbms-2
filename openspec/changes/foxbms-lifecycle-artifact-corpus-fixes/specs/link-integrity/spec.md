## Purpose

Defines fixes for link integrity: resolving dangling links, ensuring all link endpoints resolve to artifacts in the corpus, and maintaining profile-partitioned link registries.

## ADDED Requirements

### Requirement: Profile-aware link resolution
Link validation SHALL resolve endpoints within the same profile — `as_is` links resolve to `as_is` artifacts, `synthetic_reference` links to `synthetic_reference` artifacts.

#### Scenario: Cross-profile links do not validate
- **WHEN** a link in `synthetic_reference` registry references an `as_is` artifact
- **THEN** validation reports dangling endpoint (profiles must match)

### Requirement: Review artifact in corpus for link resolution
The review artifact `review-vertical-slice.json` SHALL exist in `docs/artifacts/corpus/as_is/reviews/records/` so that `as_is` links referencing it resolve correctly.

#### Scenario: Review artifact resolves in as_is profile
- **WHEN** `as_is` link registry references FB2-REV-000001
- **THEN** the artifact exists in `docs/artifacts/corpus/as_is/reviews/records/review-vertical-slice.json`

### Requirement: Synthetic reference links only reference synthetic artifacts
The `synthetic_reference` link registry SHALL only contain links where both source and target are `synthetic_reference` profile artifacts.

#### Scenario: Synthetic links validated against synthetic artifacts
- **WHEN** synthetic_reference link registry is validated
- **THEN** all source_id and target_id exist in synthetic_reference profile artifacts

## MODIFIED Requirements

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

### Requirement: Link metadata completeness
Every link SHALL include: link_id, source_id/revision, target_id/revision, relation_type, profile, scenario_id, baseline_id, variant_applicability, rationale, provenance, review_state, change_suspect_status.

#### Scenario: Link metadata validated
- **WHEN** link registry is validated
- **THEN** all links have all required metadata fields populated

## REMOVED Requirements

### Requirement: Links referencing missing review artifacts
- **Reason**: Review artifacts must exist in the corpus for link resolution
- **Migration**: Copy review-vertical-slice.json to corpus/as_is/reviews/records/ or remove links referencing it
