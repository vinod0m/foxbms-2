# Standards Mapping Report

**Generated:** 2026-09-08  
**Baseline:** BAS-REF-001  
**Standards:** ISO 26262:2018, ASPICE PAM 4.1

## ISO 26262:2018 Mapping

### Part 1: Vocabulary
- **Status:** Referenced
- **Artifacts:** Terminology used consistently across corpus

### Part 2: Management of Functional Safety
- **Status:** Mapped
- **Artifacts:** Safety plan (`FB2-MAN-SPL-000001`), roles/RACI, tailoring, independence planning, toolchain inventory

### Part 3: Concept Phase
- **Status:** Mapped
- **Artifacts:** Item definition, HARA (`FB2-SAF-HAZ-000001`), safety goals (`FB2-SAF-SGO-000001`), FSC

### Part 4: System-Level Product Development
- **Status:** Mapped
- **Artifacts:** System requirements (`FB2-SAF-FSR-000001-004`), architecture (`FB2-SYS-HSI-000001`), technical safety concept, HW/SW allocation

### Part 5: Hardware-Level Product Development
- **Status:** Partially Mapped
- **Artifacts:** HW requirements (`FB2-HW-TSR-000001-003`), architecture, FMEDA (synthetic), quantitative analysis (synthetic)
- **Gap:** Detailed HW FMEDA not generated

### Part 6: Software-Level Product Development
- **Status:** Mapped
- **Artifacts:** SW requirements (`FB2-SW-SWR-000001-003`), architecture (`FB2-SW-DSN-000001`), detailed design (`FB2-SW-DSN-000002-003`), unit verification (`FB2-VER-TMS-000001-002`)

### Part 7: Production, Operation, Service, Decommissioning
- **Status:** Mapped
- **Artifacts:** Release/config ID, release notes, acceptance checklist, production test plans (synthetic), calibration specs, installation/service instructions, maintenance strategy, decommissioning assumptions

### Part 8: Supporting Processes
- **Status:** Mapped
- **Artifacts:** Config management, change management, problem resolution, supplier monitoring, project/risk management, measurement, reuse, process improvement, release

### Part 9: ASIL-Oriented and Safety-Oriented Analyses
- **Status:** Mapped
- **Artifacts:** FMEA, FTA, dependent failure analysis, freedom from interference, decomposition rationale (synthetic)

### Part 10: Guidelines
- **Status:** Referenced
- **Artifacts:** Methodology guidance referenced in artifacts

### Part 11: Semiconductors
- **Status:** Not Applicable
- **Rationale:** foxBMS is BMS platform, not semiconductor development

### Part 12: Motorcycles
- **Status:** Not Applicable
- **Rationale:** foxBMS targets automotive/industrial energy storage, not motorcycles

## ASPICE PAM 4.1 Mapping

| Process | Mapping | Key Artifacts |
|---------|---------|---------------|
| SYS.1-SYS.5 | Mapped | Stakeholder needs, SYS reqs, arch, integration, qual test |
| SWE.1-SWE.6 | Mapped | SW reqs, arch, detailed design, integration, qual test, CM |
| HWE.1-HWE.4 | Partially Mapped | HW reqs, arch, detailed design, integration/test |
| VAL.1 | Mapped (synthetic) | Validation plan, measures, results |
| ACQ.4 | Mapped | Supplier monitoring records |
| SPL.2 | Mapped | Release management process |
| SUP.1 | Mapped | QA plan, review records |
| SUP.8 | Mapped | Git history, baselines, corpus policy |
| SUP.9 | Mapped | Findings, dispositions |
| SUP.10 | Mapped | 3 change lifecycle demos |
| SUP.11 | Mapped | Traceability link registry, matrices |
| MAN.3 | Mapped | Project scope, safety plan |
| MAN.5 | Mapped | Hazard analysis, risk register |
| MAN.6 | Mapped | Coverage metrics, capability examples |
| PIM.3 | Mapped | Synthetic improvement records |
| REU.2 | Mapped | FreeRTOS, vendor driver reuse dispositions |
| MLE.1-MLE.4 | Not Applicable | No ML in foxBMS product |

## Capability Dimension Examples (Synthetic)

| Level | Process Attribute | Synthetic Example |
|-------|-------------------|-------------------|
| PA1.1 | Process Performance | All processes achieve outcome |
| PA2.1 | Performance Management | Work product management, planning |
| PA2.2 | Work Product Management | Configuration management, baselines |
| PA3.1 | Process Definition | Process definitions, deployment |
| PA4.1 | Quantitative Control | Measurement examples, control limits |
| PA5.1 | Improvement | Synthetic improvement records |

## Limitations

1. **No normative text reproduction** - Only metadata and methodology mappings
2. **Synthetic mappings** - All mappings are for synthetic_reference profile
3. **as_is gaps** - foxBMS does not conform to all processes (development platform)
4. **No tool qualification** - Approach documented, not executed
