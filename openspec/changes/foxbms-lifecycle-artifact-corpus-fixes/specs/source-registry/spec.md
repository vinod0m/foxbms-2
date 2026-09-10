## Purpose

Defines the regeneration of the source registry (`docs/artifacts/sources/source-registry.json`) from actual AST extraction, ensuring all anchors match real code symbols and line ranges.

## ADDED Requirements

### Requirement: AST-derived source anchors
The corpus SHALL regenerate `docs/artifacts/sources/source-registry.json` using graphify AST extraction, with every anchor's symbol, line range, and path matching actual code.

#### Scenario: All anchors match actual symbols
- **WHEN** source registry is validated against graphify extraction
- **THEN** every anchor's `location.symbol` matches an actual function/symbol in the source file at the specified line range

### Requirement: Header vs implementation distinction
The source registry SHALL distinguish between header file declarations and implementation file definitions.

#### Scenario: Header functions mapped to .h files
- **WHEN** a function is declared in a header (.h)
- **THEN** the anchor's `location.path` points to the .h file and `location.symbol` is the declared name

### Requirement: Symbol coverage completeness
The regenerated registry SHALL include anchors for all public symbols referenced in corpus artifacts' `source_refs`.

#### Scenario: All corpus source_refs resolve
- **WHEN** corpus artifacts are validated
- **THEN** every `source_refs` entry in all artifacts resolves to an anchor in the regenerated registry

### Requirement: Working file hash for local changes
Code anchors SHALL include `working_file_hash` for files that differ from the baseline commit.

#### Scenario: Modified local files have working hash
- **WHEN** a source file differs from baseline commit 308028fb
- **THEN** its anchor includes `working_file_hash` with SHA256 of current file content

## REMOVED Requirements

None - this replaces the existing fabricated registry.

## MODIFIED Requirements

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
