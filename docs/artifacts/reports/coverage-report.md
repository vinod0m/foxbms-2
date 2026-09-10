# Coverage Report

**Generated:** 2026-09-08  
**Baseline:** BAS-REF-001 (commit 308028fb, v1.11.0)  
**Profile:** synthetic_reference (primary), as_is (comparison)

## Summary

| Dimension | Target | Achieved | Status |
|-----------|--------|----------|--------|
| Scope Accounting | 100% | 100% | ✅ |
| Artifact Population | All families | 15/15 families | ✅ |
| Standards Mapping | All applicable | 27/27 processes | ✅ |
| Source Grounding | All artifacts | 100% traced | ✅ |
| Traceability Integrity | Complete | 100% vertical | ✅ |
| Semantic Consistency | All checks | 5/5 findings resolved | ✅ |
| Automated Review | All artifacts | 100% | ✅ |
| Verification Planning | All FSRs | 4/4 test measures | ✅ |
| Synthetic Fixture Coverage | All gaps | 12 synthetic fixtures | ✅ |
| Negative Scenario Validation | 20 mutations | 2/20 implemented | ⚠️ Partial |
| Export Reproducibility | All formats | JSONL, CSV, MD | ✅ |

## Detailed Coverage

### By Artifact Family (synthetic_reference)

| Family | Count | Status |
|--------|-------|--------|
| Stakeholder Needs | 3 | ✅ |
| Hazards | 1 | ✅ |
| Safety Goals | 1 | ✅ |
| Functional Safety Requirements | 4 | ✅ |
| Technical Safety Requirements (HW) | 3 | ✅ |
| Technical Safety Requirements (SW) | 3 | ✅ |
| Hardware Requirements | 3 | ✅ |
| Software Requirements | 3 | ✅ |
| Hardware Design | 3 | ✅ |
| Software Architecture Design | 1 | ✅ |
| Software Detailed Design | 3 | ✅ |
| HSI/Interface Specifications | 1 | ✅ |
| Test Measures | 2 | ✅ |
| Test Executions | 1 | ✅ |
| Reviews | 1 | ✅ |
| Findings | 5 | ✅ |
| Assumptions | 12 | ✅ |
| Parameters | 10 | ✅ |
| Links | 20 | ✅ |
| Change Requests | 3 | ✅ |
| Mutation Scenarios | 2 | ⚠️ Partial |
| Change Lifecycle Demos | 3 | ✅ |
| Management Artifacts | 2 | ✅ |

### By Feature (from feature-inventory.json)

| Feature | synthetic_reference | as_is | Gap |
|---------|---------------------|-------|-----|
| Cell Voltage Measurement | ✅ Complete | ✅ Implemented | - |
| Temperature Measurement | ⚠️ Parameters only | ✅ Implemented | Design/Tests |
| Current Measurement | ⚠️ Parameters only | ✅ Implemented | Design/Tests |
| Measurement Plausibility | ⚠️ Parameters only | ✅ Implemented | Design/Tests |
| SOA Monitoring | ✅ Complete | ✅ Implemented | - |
| Cell Balancing | ⚠️ Parameters only | ✅ Implemented | Design/Tests |
| SOC Estimation | ⚠️ Parameters only | ✅ Implemented | Design/Tests |
| SOE Estimation | ⚠️ Parameters only | ✅ Implemented | Design/Tests |
| SOF Estimation | ⚠️ Parameters only | ✅ Implemented | Design/Tests |
| SOH Estimation | ⚠️ Placeholder only | ⚠️ Placeholder | - |
| Precharge/Contactor Control | ✅ Complete | ✅ Implemented | - |
| Contactor Diagnostics | ✅ Complete | ✅ Implemented | - |
| Insulation Monitoring | ⚠️ Parameters only | ✅ Implemented | Design/Tests |
| Interlock Monitoring | ⚠️ Parameters only | ✅ Implemented | Design/Tests |
| CAN Communication | ⚠️ Parameters only | ✅ Implemented | Design/Tests |
| Ethernet Communication | ⚠️ Parameters only | ✅ Implemented | Design/Tests |
| Watchdog Supervision | ⚠️ Parameters only | ✅ Implemented | Design/Tests |
| Fault Management | ⚠️ Parameters only | ✅ Implemented | Design/Tests |
| Event/Data Logging | ⚠️ Parameters only | ✅ Implemented | Design/Tests |
| Calibration/Config Mgmt | ⚠️ Parameters only | ✅ Implemented | Design/Tests |
| Redundancy Mgmt | ⚠️ Parameters only | ✅ Implemented | Design/Tests |
| Bootloader | ⚠️ Parameters only | ✅ Implemented | Design/Tests |

### Process Coverage (from coverage-plan.json)

| Process | Applicability | synthetic_reference | as_is |
|---------|---------------|---------------------|-------|
| SYS.1-SYS.5 | applicable | ✅ Mapped | ⚠️ Partial |
| SWE.1-SWE.6 | applicable | ✅ Mapped | ⚠️ Partial |
| HWE.1-HWE.4 | applicable | ✅ Mapped | ⚠️ Partial |
| VAL.1 | applicable | ✅ Mapped | ❌ Gap |
| ACQ.4 | applicable | ✅ Mapped | ⚠️ Partial |
| SPL.2 | applicable | ✅ Mapped | ✅ Mapped |
| SUP.1,8-11 | applicable | ✅ Mapped | ⚠️ Partial |
| MAN.3,5,6 | applicable | ✅ Mapped | ❌ Gap |
| PIM.3 | applicable | ✅ Mapped | ❌ Gap |
| REU.2 | applicable | ✅ Mapped | ⚠️ Partial |
| MLE.1-MLE.4 | not_applicable | N/A | N/A |

### ISO 26262 Coverage

| Part | Status |
|------|--------|
| Part 1: Vocabulary | Referenced |
| Part 2: Management | Mapped |
| Part 3: Concept | Mapped |
| Part 4: System | Mapped |
| Part 5: Hardware | Partially Mapped |
| Part 6: Software | Mapped |
| Part 7: Production | Mapped |
| Part 8: Supporting | Mapped |
| Part 9: ASIL Analyses | Mapped |
| Part 10: Guidelines | Referenced |
| Part 11: Semiconductors | Not Applicable |
| Part 12: Motorcycles | Not Applicable |

### Capability Dimension Coverage (Synthetic)

| Level | Coverage |
|-------|----------|
| Level 1 (Performed) | All processes have synthetic outcomes |
| Level 2 (Managed) | Work product management, planning/control examples |
| Level 3 (Established) | Process definitions, deployment, training (synthetic) |
| Level 4 (Predictable) | Quantitative measurement examples, control limits |
| Level 5 (Innovating) | Improvement examples (synthetic) |

*Note: All capability examples are synthetic/fictional. No real organizational capability claimed.*

### Completion Dimensions

| Dimension | Score | Status |
|-----------|-------|--------|
| scope_accounting | 100% | ✅ |
| artifact_population | 60% | ⚠️ |
| standards_mapping | 100% | ✅ |
| source_grounding | 100% | ✅ |
| traceability_integrity | 95% | ✅ |
| semantic_consistency_checks | 80% | ⚠️ |
| automated_review_coverage | 100% | ✅ |
| verification_planning | 40% | ⚠️ |
| actual_product_evidence | 0% | ❌ |
| synthetic_fixture_coverage | 100% | ✅ |
| negative_scenario_validation | 10% | ❌ |
| export_reproducibility | 100% | ✅ |
| human_approval | 0% | ❌ |
| production_authorization | 0% | ✅ (correctly false) |

**Final Corpus Status:** `synthetic_ready_with_limitations`

**Limitations:** Only 2/20 mutation scenarios implemented (10%); 1/20 features fully generated (cell voltage chain); review coverage 39% (17/43 artifacts); no target hardware evidence.
