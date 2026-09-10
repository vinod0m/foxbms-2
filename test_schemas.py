import json
import os
from jsonschema import Draft202012Validator

# Load base schema
with open('docs/artifacts/schemas/artifact-base.schema.json') as f:
    base = json.load(f)

# Load requirement schema
with open('docs/artifacts/schemas/requirement.schema.json') as f:
    req_schema = json.load(f)

# Create a merged schema for testing (allOf with base)
# Since allOf with additionalProperties:false on base doesn't work directly,
# we'll test with the extended schema directly (which includes base fields)
# The schema files are self-contained with allOf including base fields

# Load requirement schema (it includes allOf with base)
with open('docs/artifacts/schemas/requirement.schema.json') as f:
    schema = json.load(f)

# Test valid requirement
test_req = {
    'id': 'FB2-SYS-REQ-000001',
    'revision': '1',
    'schema_version': '1.0.0',
    'artifact_type': 'requirement',
    'engineering_domain': 'system',
    'profile': 'synthetic_reference',
    'scenario_id': 'SCN-BASELINE',
    'baseline_id': 'BAS-REF-001',
    'variant_applicability': ['VAR-REF-001'],
    'title': 'Cell Voltage Monitoring',
    'owner_role': 'safety_engineer',
    'origin': 'synthetic',
    'source_refs': ['FB2-SRC-COD-000001'],
    'assumption_refs': ['FB2-ASM-001'],
    'standards_mappings': [{'standard_id': 'ISO_26262_2018', 'reference': 'Part 6, Clause 7', 'status': 'mapped'}],
    'lifecycle_status': 'baselined',
    'automated_review_status': {'schema_valid': True, 'links_valid': True, 'provenance_consistent': True, 'consistency_checks': True, 'last_run': '2026-09-08T00:00:00Z'},
    'human_approval_status': 'pending',
    'production_authorized': False,
    'product_verification_credit': False,
    'created_at': '2026-09-08T00:00:00Z',
    'updated_at': '2026-09-08T00:00:00Z',
    'revision_history': [{'revision': '1', 'date': '2026-09-08T00:00:00Z', 'author': 'safety_engineer', 'description': 'Initial creation'}],
    'statement': 'The BMS shall acquire all cell voltages at a minimum rate of 20 Hz with PEC/CRC validation.',
    'rationale': 'Required for SOA monitoring to detect overvoltage/undervoltage within FTTI',
    'classification': 'safety',
    'acceptance_criteria': [{'criterion': 'All cell voltages acquired', 'measure': 'Cell count match', 'threshold': '100%', 'unit': '%'}, {'criterion': 'Acquisition rate', 'measure': 'Period', 'threshold': '50', 'unit': 'ms'}],
    'verification_approach': 'test',
    'safety_allocation': {'asil': 'ASIL_D', 'safety_goal_ref': 'FB2-SAF-SGO-000001', 'mitigation': 'PEC/CRC, database integrity, independent HW monitor, plausibility'},
    'assumptions': ['FB2-ASM-001', 'FB2-ASM-004'],
    'conditions_modes': ['NORMAL', 'CHARGING', 'PRECHARGE', 'DERATING'],
    'feasibility_dependencies': ['FB2-SAF-FSR-000001', 'FB2-SAF-FSR-000002', 'FB2-SAF-FSR-000003']
}

# Load the requirement schema
with open('docs/artifacts/schemas/requirement.schema.json') as f:
    req_schema = json.load(f)

# Create validator
validator = Draft202012Validator(schema)

# Test 1: Valid requirement
try:
    validator.validate(test_req)
    print('✓ Valid requirement instance passes validation')
except Exception as e:
    print(f'✗ Valid instance failed: {e}')

# Test 2: Invalid requirement (missing required field)
test_invalid = dict(test_req)
del test_invalid['statement']

try:
    validator.validate(test_invalid)
    print('✗ Invalid instance passed validation (should have failed)')
except Exception as e:
    print(f'✓ Invalid instance correctly rejected: {type(e).__name__}')

# Test 3: Invalid enum value
test_invalid2 = dict(test_req)
test_invalid2['classification'] = 'invalid_type'

try:
    validator.validate(test_invalid2)
    print('✗ Invalid enum passed validation (should have failed)')
except Exception as e:
    print(f'✓ Invalid enum correctly rejected: {type(e).__name__}')

# Test 4: Invalid pattern on id
test_invalid3 = dict(test_req)
test_invalid3['id'] = 'INVALID-ID'

try:
    validator.validate(test_invalid3)
    print('✗ Invalid ID pattern passed validation (should have failed)')
except Exception as e:
    print(f'✓ Invalid ID pattern correctly rejected: {type(e).__name__}')

# Test 5: acceptance_criteria minItems
test_invalid4 = dict(test_req)
test_invalid4['acceptance_criteria'] = []

try:
    validator.validate(test_invalid4)
    print('✗ Empty acceptance_criteria passed validation (should have failed)')
except Exception as e:
    print(f'✓ Empty acceptance_criteria correctly rejected: {type(e).__name__}')

print("\nAll schema validation tests completed!")