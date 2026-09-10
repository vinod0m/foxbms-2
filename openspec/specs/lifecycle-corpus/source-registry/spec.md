# source-registry Specification

## Purpose

Establishes a durable source registry with anchors for code, hardware, documentation, and tests that provide traceability from artifacts back to their source evidence.

## Requirements

### Requirement: Code source anchors
The corpus SHALL create code source anchors with repository identity, commit SHA, relative path, symbol name, line range, content hash, and working file hash for changed local files.

#### Scenario: Code anchor resolves to exact symbol
- **WHEN** a code source anchor is queried
- **THEN** it identifies the exact function/method/variable in the source file at the specified line range

### Requirement: Hardware source anchors
The corpus SHALL create hardware source anchors with board/revision, file, sheet/page, reference designator, net/connector/pin, and file hash.

#### Scenario: Hardware anchor traces to schematic symbol
- **WHEN** a hardware source anchor is queried
- **THEN** it identifies the exact component or net on the specified schematic sheet

### Requirement: Documentation source anchors
The corpus SHALL create documentation anchors with exact URL or local path, version, section/anchor, retrieval date, and content hash.

#### Scenario: Documentation anchor retrieves exact section
- **WHEN** a documentation anchor is used
- **THEN** it points to the exact section in the official foxBMS documentation

### Requirement: Test source anchors
The corpus SHALL create test anchors with file/executable identity, version, configuration, and the precise assertion/report supporting the claim.

#### Scenario: Test anchor links to specific assertion
- **WHEN** a test source anchor is used
- **THEN** it identifies the exact test case and assertion in the test file

### Requirement: Source registry manifest
The corpus SHALL maintain a source registry (`sources/source-registry.json`) cataloging all anchors with unique IDs, enabling resolution from any artifact's source_refs field.

#### Scenario: All artifact source_refs resolve to registry entries
- **WHEN** validation runs
- **THEN** every source_refs entry in all artifacts resolves to an entry in source-registry.json

### Requirement: Permitted extracts directory
The corpus SHALL maintain a `sources/permitted-extracts/` directory for rights-sensitive content where normative text extraction is authorized, with metadata tracking authorization basis.

#### Scenario: Extracts carry authorization metadata
- **WHEN** a permitted extract is stored
- **THEN** it includes authorization_basis and rights_policy metadata
