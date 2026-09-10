#!/usr/bin/env python3
"""
Regenerate source-registry.json from graphify AST extraction.
Updates line ranges for code anchors from actual AST; preserves non-code anchors.
"""
import json
import subprocess
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(__file__).resolve().parent.parent
GRAPH_FILE = REPO_ROOT / "graphify-out" / "graph.json"
OUTPUT_FILE = REPO_ROOT / "docs" / "artifacts" / "sources" / "source-registry.json"


def load_graph():
    with open(GRAPH_FILE) as f:
        return json.load(f)


def get_file_hash(filepath):
    import hashlib
    try:
        content = Path(filepath).read_bytes()
        return "sha256:" + hashlib.sha256(content).hexdigest()
    except:
        return "sha256:placeholder"


def extract_function_info(graph):
    """Extract function info from graph: filepath -> list of (symbol, line_start, line_end, is_header)."""
    file_functions = defaultdict(list)

    for node in graph.get("nodes", []):
        sf = node.get("source_file", "")
        label = node.get("label", "")
        loc = node.get("source_location", "")

        if not (sf.startswith("src/") or sf.startswith("conf/")):
            continue
        if not (sf.endswith(".c") or sf.endswith(".h")):
            continue

        line_start = 1
        line_end = 1
        if loc.startswith("L"):
            parts = loc[1:].split("-")
            line_start = int(parts[0])
            line_end = int(parts[-1]) if len(parts) > 1 else line_start

        symbol = label
        if label.endswith("()"):
            symbol = label[:-2]

        if symbol == sf.split("/")[-1]:
            continue

        file_functions[sf].append({
            "symbol": symbol,
            "line_start": line_start,
            "line_end": line_end,
            "is_header": sf.endswith(".h")
        })
    return file_functions


def get_file_hash(filepath):
    import hashlib
    try:
        content = Path(filepath).read_bytes()
        return "sha256:" + hashlib.sha256(content).hexdigest()
    except:
        return "sha256:placeholder"


def main():
    print("Loading graphify AST...")
    graph = load_graph()

    print("Extracting all functions from AST...")
    file_functions = extract_function_info(graph)
    print(f"  Found functions in {len(file_functions)} files")

    # Build AST lookup: (filepath, symbol) -> function info
    ast_lookup = {}
    for filepath, funcs in file_functions.items():
        for fn in file_functions[filepath]:
            ast_lookup[(filepath, fn["symbol"])] = fn

    # Get original registry from git
    result = subprocess.run(
        ["git", "show", "8ad60c8d:docs/artifacts/sources/source-registry.json"],
        capture_output=True, text=True, cwd=REPO_ROOT
    )
    original_registry = json.loads(result.stdout)

    # Process each anchor
    updated_anchors = []
    for anchor in original_registry.get("anchors", []):
        aid = anchor["anchor_id"]
        old_loc = anchor["location"]
        source_type = anchor.get("source_type", "code")

        if source_type == "code":
            # Code anchor - update line range from AST
            filepath = old_loc["path"]
            symbol = old_loc["symbol"]

            # Try to find in AST
            fn = None
            key = (filepath, symbol)
            if key in ast_lookup:
                fn = ast_lookup[key]
            else:
                # Try variations: .h -> .c, .c -> .h
                for ext in [".c", ".h"]:
                    alt_path = filepath.replace(".h", ext).replace(".c", ext)
                    key2 = (alt_path, symbol)
                    if key2 in ast_lookup:
                        fn = ast_lookup[key2]
                        filepath = alt_path
                        break

            if fn:
                line_start = fn["line_start"]
                line_end = fn["line_end"]
            else:
                # Fallback to original line range
                old_range = old_loc["line_range"]
                if "-" in str(old_range):
                    line_start, line_end = map(int, str(old_range).split("-"))
                else:
                    line_start = line_end = 1

            # Compute working file hash
            working_hash = "sha256:placeholder"
            if (REPO_ROOT / filepath).exists():
                working_hash = get_file_hash(REPO_ROOT / filepath)

            # Build updated anchor
            updated_anchor = {
                "anchor_id": anchor["anchor_id"],
                "source_type": "code",
                "location": {
                    "repository": "foxbms-2",
                    "commit": "308028fb",
                    "path": filepath,
                    "symbol": symbol,
                    "line_range": f"{line_start}-{line_end}",
                    "working_file_hash": "sha256:placeholder"
                },
                "content_hash": "sha256:placeholder",
                "retrieval_date": "2026-09-10T00:00:00Z"
            }
            updated_anchors.append(updated_anchor)

        else:
            # Non-code anchor (hardware, documentation, test) - preserve as-is
            updated_anchors.append(anchor)

    # Write output
    new_registry = {
        "schema_version": "1.0.0",
        "created_at": "2026-09-10T00:00:00Z",
        "updated_at": "2026-09-10T00:00:00Z",
        "repository_commit": "308028fb",
        "anchors": updated_anchors
    }

    OUTPUT_FILE = REPO_ROOT / "docs" / "artifacts" / "sources" / "source-registry.json"
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(new_registry, f, indent=2)
        f.write("\n")

    print(f"Written to {OUTPUT_FILE}")
    print(f"Total anchors: {len(updated_anchors)}")

    # Verify corpus refs resolve
    corpus_refs = set()
    for f in Path("docs/artifacts/corpus").rglob("*.json"):
        try:
            d = json.load(open(f))
            if d.get("source_refs"):
                for r in d["source_refs"]:
                    corpus_refs.add(r)
        except:
            pass

    anchor_ids = {a["anchor_id"] for a in updated_anchors}
    missing = corpus_refs - anchor_ids
    if missing:
        print(f"  WARNING: {len(missing)} corpus refs not in registry: {missing}")
    else:
        print(f"  OK: All {len(corpus_refs)} corpus source_refs resolve")


if __name__ == "__main__":
    import json
    import subprocess
    from pathlib import Path
    from collections import defaultdict
    main()
