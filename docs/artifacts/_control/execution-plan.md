# foxBMS 2 Lifecycle Artifact Corpus — Execution Plan

**Repository:** `/Users/vinod/Downloads/SoftwareDevLabs/foxbms-2`  
**Commit:** `308028fb` (v1.11.0, 2026-04-20)  
**Branch:** `master`  
**Started:** 2026-09-08  
**Runtime:** OpenCode with GPT-6 Astra (actual model: nvidia/nemotron-3-ultra-550b-a55b)

## Stage 1: Preflight (Current)
- [ ] Verify repository/output boundaries
- [ ] Record initial git state and tool capabilities
- [ ] Create control directory structure
- [ ] Create `.gitignore` for `docs/artifacts/.work/`
- [ ] Record runtime/tool capabilities

## Stage 2: Discovery
- [ ] Inventory source code (modules, interfaces, configuration)
- [ ] Inventory hardware (boards, interfaces, design resources)
- [ ] Inventory documentation (structure, modules, tests)
- [ ] Inventory tests (unit, integration, frameworks)
- [ ] Pin standards: ISO 26262:2018, ASPICE PAM 4.1
- [ ] Create process/applicability inventory (SYS.1-5, SWE.1-6, HWE.1-4, VAL.1, ACQ.4, SPL.2, SUP.1,8-11, MAN.3,5,6, PIM.3, REU.2, MLE.1-4)
- [ ] Create `source-inventory.json`, `feature-inventory.json`, `variant-matrix.json`, `coverage-plan.json`

## Stage 3: Model
- [ ] Create `standards-lock.json`
- [ ] Create `corpus-policy.json` (profiles, provenance, approval semantics)
- [ ] Define JSON schemas in `schemas/`
- [ ] Create `source-registry.json` with durable anchors
- [ ] Define hypothetical item, parameters, ID scheme, link semantics
- [ ] Create `scope-and-applicability.json`

## Stage 4: Vertical Slice
- [ ] Select one safety-critical function chain (e.g., cell voltage monitoring -> SOA -> contactor control)
- [ ] Generate as_is and synthetic_reference artifacts for: stakeholder need -> hazard -> safety goal -> FSR -> TSR -> system arch -> HW req -> SW req -> design -> implementation -> verification -> execution -> review -> safety argument
- [ ] Create one mutation scenario and one change lifecycle demo
- [ ] Validate schemas, links, provenance, consistency
- [ ] Repair weaknesses before scaling

## Stage 5: Full Generation
- [ ] Expand to all discovered features and domains
- [ ] Generate all lifecycle work-product families
- [ ] Use bounded batches with explicit completion states
- [ ] Update work queue and progress at each batch

## Stage 6: Integration
- [ ] Reconcile HSI/interface authority
- [ ] Reconcile shared parameters and assumptions
- [ ] Reconcile safety analyses (FMEA, FTA, dependent failures)
- [ ] Reconcile verification measures and coverage
- [ ] Reconcile standards mappings

## Stage 7: Review and Repair
- [ ] Domain reviews (system/safety, hardware, software, verification)
- [ ] Cross-domain consistency checks
- [ ] Adversarial review (false completeness, weak oracles, variant contamination)
- [ ] Repair authoritative records, regenerate dependents, regression test

## Stage 8: Scenario/Maintenance Validation
- [ ] Execute 20+ mutation scenarios
- [ ] Complete 3 change lifecycle demonstrations
- [ ] Round-trip/export/reproducibility tests
- [ ] Corpus toolchain self-tests

## Stage 9: Final Assessment
- [ ] Run all completion gates
- [ ] Produce final reports (coverage, standards-mapping, traceability, consistency, review-summary, gaps, verification-evidence, scenario-validation, reproducibility, final-acceptance)
- [ ] 5 cross-domain walkthroughs
- [ ] Verify source unchanged
- [ ] Report final corpus status
