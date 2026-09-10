## 1. Governance and Setup

- [x] 1.1 Create governance directory structure and corpus-policy.json with profiles, provenance rules, evidence classification, approval semantics, boundary enforcement
- [x] 1.2 Create standards-lock.json locking ISO 26262:2018 (Parts 1-12) and ASPICE PAM 4.1 (VDA QMC English 2026-08-24) with publisher, edition, retrieval date, authorization basis, review status
- [x] 1.3 Create scope-and-applicability.json with item definition, boundaries, hazards, safety scope, stakeholder needs, operational situations, modes, environmental assumptions, external systems, applicability decisions for ISO Part 11/12 and MLE processes
- [x] 1.4 Create coverage-plan.json mapping all 27 ASPICE processes (SYS.1-5, SWE.1-6, HWE.1-4, VAL.1, ACQ.4, SPL.2, SUP.1,8-11, MAN.3,5,6, PIM.3, REU.2, MLE.1-4) and 12 ISO parts to artifact families with dispositions
- [x] 1.5 Create role-and-review-policy.json defining 11 roles, responsibilities, authority, independence, required reviews per artifact, AI review limitations, human approval tracking
- [x] 1.6 Create corpus-policy.json with profiles (as_is, synthetic_reference), provenance rules (source_observed, derived, synthetic), evidence classification (execution_kind, outcome), approval semantics (human_approval_status, synthetic_decision, production_authorized=false), change management rules
- [x] 1.7 Verify all governance artifacts validate against their JSON schemas
- [x] 1.8 Create _control/ directory with execution-plan.md, progress.json, decisions.jsonl, work-queue.json, resume.md

## 2. JSON Schemas

- [x] 2.1 Create artifact-base.schema.json with common fields: id, revision, schema_version, artifact_type, engineering_domain, profile, scenario_id, baseline_id, variant_applicability, title, owner_role, origin, source_refs, assumption_refs, standards_mappings, lifecycle_status, automated_review_status, human_approval_status, production_authorized, product_verification_credit, timestamps, revision_history
- [x] 2.2 Create requirement.schema.json extending base with statement, rationale, classification, acceptance_criteria, verification_approach, safety_allocation, assumptions, conditions_modes, feasibility_dependencies
- [x] 2.3 Create design.schema.json with design_level, responsibilities, decomposition, interfaces, behavior_model, constraints, budgets, failure_response, decisions, implementation_mapping
- [x] 2.3 Create test_measure.schema.json with test_type, objective, referenced_requirements, referenced_designs, preconditions, environment, stimuli, steps, expected_outcomes, tolerances, timing, oracle_basis, cleanup, regression_selection
- [x] 2.4 Create execution.schema.json with test_measure_id, test_measure_revision, execution_kind (none|actual_host_run|actual_simulation_run|synthetic_fixture), outcome, environment, input_hashes, output_hashes, logs, timestamps, anomalies, evidence_refs
- [x] 2.5 Create review.schema.json with review_type, reviewed_ids (with revision, digest), reviewer_identity, checklist_version, scope, findings, dispositions, limitations
- [x] 2.6 Create assumption.schema.json with statement, rationale, affected_scope, source, validity_conditions, invalidation_consequence, review_status
- [x] 2.7 Create parameter.schema.json with name, value, unit, tolerance, domain, sign_convention, timing_budget, thresholds, hysteresis, debounce, calibration, configuration_selection, assumptions
- [x] 2.8 Create link.schema.json with all 17 relation types, required metadata (rationale, provenance, review_state, change_suspect_status)
- [x] 2.9 Create source_anchor.schema.json supporting code, hardware, documentation, test source types with durable location and content hashes
- [x] 2.9 Create change.schema.json with change_type, trigger, impact_analysis, decision, new_revisions, suspect_links, required_updates, reverification_selection, post_change_baseline
- [x] 2.10 Create finding.schema.json with severity, category, evidence, disposition, impact, root_cause, resolution
- [x] 2.11 Create scenario.schema.json with scenario_type (mutation|change_lifecycle), baseline_ref, patch, affected_ids, trigger, expected_detector, expected_finding, impact_paths, expected_remediation, oracle_manifest_ref
- [x] 2.12 Verify all schemas validate against JSON Schema draft-07 meta-schema
- [x] 2.13 Test schema validation with sample artifacts

## 3. Source Registry

- [x] 3.1 Create source-registry.json with 40+ durable anchors: code (repo, commit, path, symbol, line_range, content_hash, working_file_hash), hardware (board_revision, file, sheet_page, reference_designator, net_connector_pin, file_hash), documentation (url_or_path, version, section_anchor, retrieval_date, content_hash), test (file_or_executable, version, configuration, assertion_report)
- [x] 3.2 Create permitted-extracts/ directory structure for rights-sensitive content with authorization metadata
- [x] 3.3 Verify all source_refs in artifacts resolve to registry entries

## 4. Canonical Data Model - Shared Artifacts

- [x] 4.1 Create shared/parameter-registry.json with 10 parameters: cell_voltage_max/min, ftti_ms, afe_acquisition_period_ms, contactor_mechanical_time_ms, independent_monitor_latency_ms, soa_debounce_count, pack_current_max_charge/discharge, cell_temperature_max - each with value, unit, tolerance, thresholds, hysteresis, debounce, calibration, configuration_selection, assumptions
- [x] 4.2 Create shared/assumption-registry.json with 12 assumptions: ASM-001 to ASM-012 (chemistry, thermal, charger, SPI latency, noise, contactor timing, SBC independence, independent monitor, sensor accuracy, FreeRTOS scheduling, FRAM endurance) with validity_conditions, invalidation_consequence, review_status
- [x] 4.3 Verify parameter registry references assumption registry via assumptions array
- [x] 4.4 Verify all parameters have configuration_selection including VAR-REF-001

## 5. Traceability Infrastructure

- [x] 5.1 Create traceability/link-registry/as_is/ and traceability/link-registry/synthetic_reference/ directories
- [x] 5.2 Create traceability/rules/ with link type definitions, domain/range rules, metadata requirements
- [x] 5.4 Create traceability/queries/ with forward/reverse/lateral query utilities
- [x] 5.5 Create link registry files with all 17 relation types, required metadata (rationale, provenance, review_state, change_suspect_status)

## 6. as_is Profile Artifacts

- [x] 6.1 Create corpus/as_is/safety/hazard-analysis-cell-voltage.json with malfunctioning_behavior, hazardous_events (HE-01 ASIL_D, HE-02 ASIL_B), safe_states, degraded_states, origin=derived
- [x] 6.2 Create corpus/as_is/safety/safety-goal-cell-voltage.json with statement, FTTI=100ms, safe_state, degraded_state, asil=ASIL_D, origin=derived
- [x] 6.3 Create corpus/as_is/safety/fsr-cell-voltage.json (acquisition 10Hz, PEC validation), fsr-soa-monitoring.json (limit check 10ms), fsr-contactor-response.json (50ms opening), origin=source_observed
- [x] 6.4 Create corpus/as_is/hardware/tsr-afe-cell-voltage.json (±1.5mV accuracy), tsr-afe-communication.json (isoSPI BER<1e-9), tsr-contactor-driver.json (30ms mechanical), origin=source_observed
- [x] 6.5 Create corpus/as_is/software/swr-afe-driver.json (20Hz acquisition, 5ms publish), swr-soa-monitoring.json (10ms check), swr-contactor-control.json (5ms fault response), origin=source_observed
- [x] 6.6 Create corpus/as_is/software/design-afe-driver.json (state machine, DMA, PEC), design-soa.json (debounce state machine), design-contactor.json (state machine, feedback monitoring), origin=source_observed
- [x] 6.7 Create corpus/as_is/verification/test-soa-voltage-limits.json (unit, source_grounded), test-contactor-statemachine.json (unit, source_grounded), execution-soa-voltage.json (actual_host_run, pass)
- [x] 6.8 Create corpus/as_is/verification/ with evidence gaps documented (no system qualification tests, no HW FMEDA, no calibration procedures)
- [x] 6.9 Create reviews/records/review-vertical-slice.json with 17 reviewed artifacts, 5 findings (FTTI budget, target timing, HW accuracy, debounce justification, integration test gap)

## 7. synthetic_reference Profile - Safety

- [x] 7.1 Create corpus/synthetic_reference/safety/hazard-analysis-cell-voltage.json with HE-01 (S3/E4/C3=ASIL_D), HE-02 (S2/E3/C2=ASIL_B), safe_states, degraded_states, assumptions, origin=synthetic
- [x] 7.2 Create corpus/synthetic_reference/safety/safety-goal-cell-voltage.json with FTTI=100ms, timing budget allocation (AFE 25ms, SOA 5ms, contactor 30ms, independent monitor 50ms parallel, margin 20ms), origin=synthetic
- [x] 7.3 Create corpus/synthetic_reference/safety/fsr-cell-voltage.json (20Hz, 25ms publish), fsr-soa-monitoring.json (5ms check, debounce=2 justified statistically), fsr-contactor-response.json (30ms opening, 5ms feedback), fsr-independent-monitor.json (50ms ASIL_B parallel), origin=synthetic
- [x] 7.4 Create corpus/synthetic_reference/safety/ with safety analyses: FMEA, FTA, dependent failure analysis, freedom-from-interference linked to elements, assumptions, mechanisms, requirements, verification measures
- [x] 7.5 Create corpus/synthetic_reference/safety/safety-case-skeleton.json with claims, arguments, evidence/gap links, assumptions, defeaters, unresolved concerns, release_recommendation (production_authorized=false)

## 8. synthetic_reference Profile - System

- [x] 8.1 Create corpus/synthetic_reference/system/hsi-cell-voltage.json with SPI signals (CLK/MOSI/MISO/CS timing), database signals (cell_voltage[mV], cell_temperature[0.1°C], freshness<30ms), electrical budgets, timing budget (25ms total), fault indications, variant applicability table

## 9. synthetic_reference Profile - Hardware

- [x] 9.1 Create corpus/synthetic_reference/hardware/tsr-afe-cell-voltage.json (±1.5mV including calibration), tsr-afe-communication.json (isoSPI BER<1e-9, 5ms failure detection), tsr-contactor-driver.json (30ms mechanical, 5ms feedback), tsr-independent-monitor.json (50ms ASIL_B), origin=synthetic

## 10. synthetic_reference Profile - Software

- [x] 10.1 Create corpus/synthetic_reference/software/swr-afe-driver.json (25ms publish), swr-soa-monitoring.json (5ms check, debounce=2), swr-contactor-control.json (5ms fault response), origin=synthetic
- [x] 10.2 Create corpus/synthetic_reference/software/design-afe-driver.json (DMA, PEC, state machine), design-soa.json (debounce state machine, statistical justification), design-contactor.json (emergency open <5ms), origin=synthetic

## 11. synthetic_reference Profile - Management & Shared

- [x] 11.1 Create corpus/synthetic_reference/management/project-scope.json with scope, rationale, acceptance criteria
- [x] 11.2 Create corpus/synthetic_reference/management/safety-plan.json with safety activities, independence, tool confidence, confirmation measures
- [x] 11.3 Verify shared/parameter-registry.json and shared/assumption-registry.json referenced by all profile artifacts

## 12. Traceability Links (synthetic_reference)

- [x] 12.1 Create traceability/link-registry/synthetic_reference/links-cell-voltage.json with 20+ links: refines (SG→hazard, FSR→SG), allocated_to (FSR→TSR/SWR), implements (DSN→SWR), verifies (TMS→FSR/SWR), mitigates (SG→hazard), specified_by (HSI), result_of (EXE→TMS), reviewed_by (REV→artifacts)
- [x] 12.2 Verify all link metadata complete: rationale, provenance, review_state, change_suspect_status

## 13. Mutation Scenarios (minimum 20, start with 2)

- [x] 13.1 Create scenarios/mutations/mutation-001-missing-parent-link.json (delete refines link FSR→SG, expected finding: high severity traceability gap)
- [x] 13.2 Create scenarios/mutations/mutation-002-invalid-link-type.json (change verifies to related_to, expected finding: high severity invalid relation_type)
- [x] 13.3 Create evaluator-only manifests for each mutation in scenarios/evaluator-only/
- [x] 13.4 Implement remaining 18 mutation scenarios (stale revision, unit mismatch, HW/SW pin polarity, timing budget, threshold contradiction, missing fault reaction, ASIL downgrade, false diagnostic coverage, invalid config, fabricated evidence, unjustified N/A, dangling evidence, duplicate ID, source anchor drift, unsafe workflow promotion, incomplete change propagation, circular refinement, missing verification link)

## 14. Change Lifecycle Demonstrations (3 required)

- [x] 14.1 Create scenarios/change-lifecycles/change-001-voltage-threshold.json (4.2V→4.15V): baseline, trigger, impact (6 artifacts, 2 links, 1 review, 1 evidence), decision, 6 new revisions, 1 suspect link, 8 updates, 3 reverification tests, post-change baseline BAS-REF-002
- [x] 14.2 Create scenarios/change-lifecycles/change-002-hsi-interface.json (LTC6811→ADI ADES1830): baseline, trigger, impact (9 artifacts, 5 links, 1 review, 1 evidence), decision, 6 new revisions, 5 suspect links, 11 updates, 5 reverification tests, post-change baseline BAS-REF-003
- [x] 14.3 Create scenarios/change-lifecycles/change-003-software-defect.json (SOA debounce counter not reset): baseline, trigger, impact (4 artifacts, 3 links, 1 review, 1 evidence), decision, 4 new revisions, 3 suspect links, 5 updates, 2 reverification tests (including new transient test), post-change baseline BAS-REF-004
- [x] 14.4 Create evaluator-only manifests for each change lifecycle in scenarios/evaluator-only/

## 15. Validation Tooling

- [x] 15.1 Create tools/corpus.py with CLI commands: inventory, validate, coverage, trace, impact, render, export, scenario-test, check
- [x] 15.2 Implement inventory command: builds source/feature inventories from repository
- [x] 15.3 Implement validate command: schema validation, identity checks, link validation, provenance checks, semantic consistency rules
- [x] 15.4 Implement coverage command: computes process, feature, implementation, evidence coverage with numerators/denominators
- [x] 15.5 Implement trace command: forward/reverse/lateral queries for artifact IDs
- [x] 15.6 Implement impact command: typed transitive impact from changed IDs/revisions
- [x] 15.7 Implement render command: regenerates views (Markdown, CSV, diagrams) from canonical JSON
- [x] 15.8 Implement export command: JSONL nodes/edges, CSV inventory/matrices, Markdown reports, manifests with import contract
- [x] 15.9 Implement scenario-test command: applies mutations, compares findings to evaluator manifests
- [x] 15.10 Implement check command: runs complete acceptance suite, exits nonzero on failure
- [x] 15.11 Create unit/integration tests for validators: valid/invalid schemas, duplicate IDs, dangling links, incorrect types, invalid state changes, version mismatch, profile contamination, source drift, export consistency, numerical constraints
- [x] 15.12 Verify mutation scenarios produce expected detections (not hardcoded)
- [x] 15.13 Test offline determinism, idempotent regeneration, round-trip preservation, incremental maintenance

## 16. Reports Generation

- [x] 16.1 Create reports/coverage-report.md with 15 completion dimensions, numerators/denominators, by-family/feature/process/capability breakdowns
- [x] 16.2 Create reports/standards-mapping-report.md with ISO 26262 part mapping, ASPICE process mapping, capability dimensions, gaps
- [x] 16.3 Create reports/traceability-report.md with vertical chains, reverse/lateral queries, change impact, 5 cross-domain walkthroughs (voltage protection, temperature protection, current limits, precharge/contactor, communication/watchdog)
- [x] 16.4 Create reports/consistency-report.md with 10 check categories, findings summary, FTTI resolution
- [x] 16.5 Create reports/review-summary.md with coverage, findings by severity/category, dispositions, AI review limitations
- [x] 16.5 Create reports/source-vs-synthetic-gap-report.md with gap analysis by category (1/20 features complete, 18 parameters-only)
- [x] 16.6 Create reports/verification-evidence-report.md with execution kinds, outcomes, oracle basis, coverage by requirement
- [x] 16.7 Create reports/scenario-validation-report.md with mutation results (2/20), change lifecycle demos (3/3), evaluator manifest status
- [x] 16.8 Create reports/reproducibility-report.md with round-trip tests, determinism, tool versions, export consistency
- [x] 16.9 Create reports/final-acceptance-report.md with gate results, dimension scores, artifact counts, 5 walkthroughs, limitations, final status `synthetic_ready_with_limitations`
- [x] 16.10 Create README.md with 10 sections: two profiles, baselines, directory structure, warning labels, exploration guide, check commands, regeneration guide, resume guide, change invalidation rules
- [x] 16.11 Verify all reports have corresponding machine-readable JSON data

## 17. Final Validation and Completion

- [x] 17.1 Run `python3 tools/corpus.py check` - all acceptance gates pass
- [x] 17.2 Verify final corpus status is `synthetic_ready_with_limitations` with precise criteria
- [x] 17.3 Verify all 15 completion dimensions reported with numerators/denominators
- [x] 17.4 Verify all artifacts have human_approval_status=pending, production_authorized=false, product_verification_credit=false
- [x] 17.5 Create branch foxbms-2-synthetic-data and commit all docs/artifacts/ changes
- [x] 17.6 Push branch to remote