# governance Specification

## Purpose

Establishes corpus governance including policy, standards locking, scope/applicability, coverage planning, and role/review policies for the foxBMS 2 lifecycle artifact corpus.

## Requirements

### Requirement: Corpus policy enforcement
The corpus SHALL enforce a policy that defines two profiles (`as_is` and `synthetic_reference`), provenance rules, evidence classification, approval semantics, and boundary enforcement.

#### Scenario: Policy loaded and validated
- **WHEN** corpus tooling initializes
- **THEN** policy is loaded from `governance/corpus-policy.json` and validated against its schema

### Requirement: Standards baseline locking
The corpus SHALL lock ISO 26262:2018 (Parts 1-12) and Automotive SPICE PAM 4.1 (VDA QMC English 2026-08-24) as the authoritative standards baselines with publisher, edition, retrieval date, and authorization basis recorded.

#### Scenario: Standards lock file created
- **WHEN** corpus initialization runs
- **THEN** `governance/standards-lock.json` is created with both standards locked and review status set

### Requirement: Scope and applicability definition
The corpus SHALL define the item definition, boundaries, functions, operational situations, modes, environmental assumptions, external systems, stakeholder needs, and safety scope for the hypothetical BMS item.

#### Scenario: Scope document defines ASIL assignments
- **WHEN** scope is reviewed
- **THEN** hazardous events have severity/exposure/controllability reasoning with illustrative ASIL assignments

### Requirement: Coverage planning with process inventory
The corpus SHALL create a coverage plan mapping all 27 applicable ASPICE processes (SYS.1-5, SWE.1-6, HWE.1-4, VAL.1, ACQ.4, SPL.2, SUP.1,8-11, MAN.3,5,6, PIM.3, REU.2, MLE.1-4) and 12 ISO parts to expected artifact families with disposition status.

#### Scenario: Process inventory covers all required processes
- **WHEN** coverage plan is validated
- **THEN** all 27 ASPICE processes and 12 ISO parts have explicit dispositions (mapped, partially_mapped, not_applicable, gap)

### Requirement: Role and review policy
The corpus SHALL define 11 roles (architect, safety_engineer, system_engineer, hw_engineer, sw_engineer, verification_engineer, traceability_engineer, reviewer_domain, reviewer_adversarial, project_manager, safety_manager) with responsibilities, authority, independence, and required reviews per artifact.

#### Scenario: Safety-critical artifacts require challenge pass
- **WHEN** a safety-critical artifact is reviewed
- **THEN** it receives an additional separated challenge pass by the adversarial reviewer
