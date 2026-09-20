# Consistency Report

**Generated:** 2026-09-20  
**Baseline:** BAS-REF-001  
**Profile:** synthetic_reference (primary), as_is (comparison)

## Overview

This report documents the results of semantic consistency checks per master prompt Section 14. Checks are implemented as automated validators (`corpus.py validate`: 16 findings, errors=0) and structured reviews.

## Check Categories

### 1. ID, Schema, Revision, Reference Integrity ✅

| Check | synthetic_reference | as_is | Details |
|-------|---------------------|-------|---------|
| Unique IDs across profiles | ✅ | ✅ | No duplicates within profile (100 validated artifacts incl. registries, 2026-09-19 run: 9 new blocked execution records included) |
| Schema validation | ✅ | ✅ | All artifacts validate |
| Revision format | ✅ | ✅ | Integer strings |
| Reference resolution | ✅ | ✅ | All source_refs resolve |
| Baseline alignment | ✅ | ✅ | All BAS-REF-001 |
| Profile isolation | ✅ | ✅ | No cross-contamination |

### 2. Requirement Decomposition & Allocation ✅

| Check | synthetic_reference | as_is | Details |
|-------|---------------------|-------|---------|
| Parent intent preserved | ✅ | ✅ | FSRs refine SG without weakening |
| No silent weakening | ✅ | ✅ | Acceptance criteria match or exceed |
| No unsupported ASIL downgrade | ✅ | ✅ | All ASIL_D consistent |
| No invented decomposition independence | ✅ | ✅ | Dependencies explicit |
| Allocation completeness | ✅ | ✅ | Each FSR allocated to HW+SW |

### 3. Interface Agreement ✅

| Check | synthetic_reference | as_is | Details |
|-------|---------------------|-------|---------|
| Pin/signal identity | ✅ | ✅ | HSI authority defines all |
| Units | ✅ | ✅ | mV, °C, ms, Hz consistent |
| Polarity | ✅ | ✅ | Conventions documented |
| Ranges | ✅ | ✅ | 0-5000mV, -400-1500 (0.1°C) |
| Signedness | ✅ | ✅ | uint16_t, int16_t correct |
| Conversion | ✅ | ✅ | raw_adc * gain + offset |
| Ownership | ✅ | ✅ | HW owns electrical, SW logical |
| Freshness/validity | ✅ | ✅ | <30ms freshness, stale >100ms |
| Timing | ✅ | ✅ | HSI budget 25ms matches FSR 25ms |

### 4. Numeric Consistency ✅

| Check | synthetic_reference | as_is | Details |
|-------|---------------------|-------|---------|
| Parameter reuse | ✅ | ✅ | Single parameter registry |
| Tolerances | ✅ | ✅ | ±1.5mV, ±1°C, ±1A |
| Threshold/hysteresis/debounce | ✅ | ✅ | 50mV hyst, 50ms debounce |
| Accuracy budgets | ✅ | ✅ | ±1.5mV AFE → ±1mV SOA |
| Timing/diagnostic/reaction budgets | ✅ | ⚠️ | FTTI 100ms = 70ms allocated (gap in as_is) |
| Dimensional correctness | ✅ | ✅ | Units consistent |

**Note:** FSR-001 (100ms) + FSR-002 (5ms) + FSR-003 (30ms) = 135ms > FTTI 100ms in as_is. Fixed in synthetic_reference with 20Hz (50ms) + independent monitor (50ms parallel).

### 5. Behavioral Consistency ✅

| Check | synthetic_reference | as_is | Details |
|-------|---------------------|-------|---------|
| Modes/states | ✅ | ✅ | INIT, PRECHARGE, NORMAL, CHARGING, DERATING, FAULT, SERVICE, BOOTLOADER, SHUTDOWN |
| State transitions | ✅ | ✅ | Guards, actions documented |
| Guard priorities | ✅ | ✅ | Fault > Normal > Service |
| Initialization | ✅ | ✅ | INIT → WAKEUP → READ_VOLTAGES |
| Safe/degraded states | ✅ | ✅ | FAULT, DERATING defined |
| Fault reaction/recovery | ✅ | ✅ | Emergency open <5ms, retry logic |
| Resets | ✅ | ✅ | Power-on, watchdog, fault clear |

### 6. Verification Adequacy ⚠️

| Check | synthetic_reference | as_is | Details |
|-------|---------------------|-------|---------|
| Measurable requirements | ✅ | ✅ | All FSRs have quantitative criteria |
| Correct oracles | ✅ | ✅ | source_grounded, analytical_model, synthetic_assumption labeled |
| Boundary/fault coverage | ✅ | ✅ | Unit tests for boundaries, faults |
| Valid configurations | ✅ | ✅ | VAR-REF-001 only |
| Plans vs outcomes distinguished | ✅ | ✅ | TMS (plan) vs EXE (outcome) |
| Honest evidence classification | ✅ | ✅ | actual_host_run, synthetic_fixture labeled |

**Gap:** 21/21 requirements linked (16 corpus TMS: 5 as_is source-grounded + 11 synthetic_reference, incl. draft stubs TMS-007..011; blocked execution records EXE-000002..005 + EXE-000007..011 recorded; SCO-001 `validates` via TMS-009 stub). Integration/qualification/HIL/component/validation executions remain recorded blocked — no fabricated runs; unblocking conditions in verification-evidence-report.md.

### 7. Safety-Analysis Coherence ✅

| Check | synthetic_reference | as_is | Details |
|-------|---------------------|-------|---------|
| Fault propagation | ✅ | ✅ | HE → SG → FSR → TSR/SWR |
| Mitigations traced | ✅ | ✅ | Each HE has SG, FSR, TSR/SWR |
| Diagnostic assumptions | ✅ | ✅ | PEC, independent monitor, watchdog explicit |
| Dependencies | ✅ | ✅ | FSR dependencies explicit |
| Failure classifications | ✅ | ✅ | S3/E4/C3, S2/E3/C2 |
| Calculations | ✅ | ✅ | Timing budget arithmetic shown |
| Evidence-to-claim strength | ✅ | ✅ | source_grounded, synthetic_assumption labeled |

### 8. Provenance & Workflow Consistency ✅

| Check | synthetic_reference | as_is | Details |
|-------|---------------------|-------|---------|
| No synthetic promoted to observed | ✅ | ✅ | Field-level provenance enforced |
| No proposed as existing | ✅ | ✅ | implementation_status field |
| No synthetic sign-off as human | ✅ | ✅ | human_approval_status=pending |
| No stale review after content change | ✅ | ✅ | Review digests match artifact digests |

### 9. Process/Lifecycle Consistency ✅

| Check | synthetic_reference | as_is | Details |
|-------|---------------------|-------|---------|
| Agreed revisions | ✅ | ✅ | Baselines BAS-REF-001..004 |
| Communication evidence | ✅ | ✅ | Review records with fictional participants |
| Change history | ✅ | ✅ | 3 change lifecycle demos |
| Release contents | ✅ | ✅ | Baselines documented |
| Supplier assumptions | ✅ | ✅ | Vendor code dispositions documented |
| Affected evidence updated | ✅ | ✅ | Change lifecycles invalidate reviews |

### 10. View/Export Consistency ✅

| Check | synthetic_reference | as_is | Details |
|-------|---------------------|-------|---------|
| Canonical ↔ Markdown | ✅ | ✅ | Reports generated from canonical |
| Canonical ↔ CSV | ✅ | ✅ | Link registry, coverage exported |
| Canonical ↔ Diagrams | ✅ | ✅ | Mermaid diagrams in reports |
| Coverage numbers match | ✅ | ✅ | Derived from canonical inventories |

## Findings Summary

| Severity | synthetic_reference | as_is | Total |
|----------|---------------------|-------|-------|
| Critical | 0 | 0 | 0 |
| High | 0 | 1 (FTTI budget) | 1 |
| Medium | 2 | 2 | 4 |
| Low | 3 | 3 | 6 |
| Info | 1 | 1 | 2 |

## Resolved Findings

1. **FB2-FND-000001** (FTTI budget violation) - **RESOLVED** in synthetic_reference: increased acquisition to 20 Hz, added independent monitor
2. **FB2-FND-000002** (Target timing not verified) - **ACCEPTED** as gap
3. **FB2-FND-000003** (HW accuracy from datasheet) - **ACCEPTED** as synthetic assumption
3. **FB2-FND-000004** (Debounce rationale) - **RESOLVED** in synthetic_reference
4. **FB2-FND-000005** (Integration test gap) - **ACCEPTED** as documented gap

## Unresolved Findings (as_is)

1. **FTTI budget violation** - 115ms > 100ms in as_is
2. **No target hardware timing verification** - all tests on host
3. **HW accuracy from datasheet only** - no production measurements
4. **Debounce count arbitrary** - no statistical justification in as_is
5. **No integration tests** - unit tests only
