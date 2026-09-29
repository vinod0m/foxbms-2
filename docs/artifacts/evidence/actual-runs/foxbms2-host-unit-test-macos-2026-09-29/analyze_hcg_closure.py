#!/usr/bin/env python3
"""Static analysis: which host unit tests need HALCoGen-generated TI headers?

For every test_*.c under tests/unit/ this walks the quoted-#include closure
(starting from the test file, using the include directories the shipped
Ceedling project file declares) and reports the set of HALCoGen-generated
headers reached, i.e. every header matching the TI 'HL_*.h' / 'HL_reg_*.h'
naming that HALCoGen emits and that is NOT present in the repository.

Output is a JSON summary plus a per-test table, used to choose which tests the
macOS workspace can realistically run and to document the rest as blocked.
"""

import json
import pathlib
import re
import sys
from collections import defaultdict

REPO = pathlib.Path(__file__).resolve().parents[4]

INCLUDE_DIRS = [
    "src/os/freertos/freertos/include",
    "src/os/freertos/freertos/portable/ccs/arm_cortex-r5",
    "src/app/main/include",
    "src/app/application/config",
    "src/app/engine/config",
    "src/app/engine/database",
    "src/app/driver/mcu",
    "src/app/task/os",
    "tests/unit/app/application/config",
    "tests/unit/support",
]

INCLUDE_RE = re.compile(r'^\s*#\s*include\s+"([^"]+)"', re.MULTILINE)
SYS_INCLUDE_RE = re.compile(r"^\s*#\s*include\s+<", re.MULTILINE)

# index every header in the repository once
header_index: dict[str, list[pathlib.Path]] = defaultdict(list)
for pat in ("src/**/*.h", "tests/**/*.h"):
    for path in REPO.glob(pat):
        header_index[path.name].append(path)


def resolve(name: str, origin: pathlib.Path) -> pathlib.Path | None:
    """Resolve a quoted include the way the compiler would."""
    sibling = origin.parent / name
    if sibling.is_file():
        return sibling
    for d in INCLUDE_DIRS:
        candidate = REPO / d / name
        if candidate.is_file():
            return candidate
    matches = header_index.get(pathlib.Path(name).name)
    if matches:
        return matches[0]
    return None


def closure(test: pathlib.Path) -> tuple[set[str], set[str]]:
    """Return (all headers reached, HALCoGen-only headers reached)."""
    seen: set[pathlib.Path] = set()
    hcg: set[str] = set()
    stack = [test]
    while stack:
        current = stack.pop()
        if current in seen or not current.is_file():
            continue
        seen.add(current)
        try:
            text = current.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for name in INCLUDE_RE.findall(text):
            # CMock generates Mock<name>.h *from* the real <name>.h, so the
            # real header is what has to be parseable. Follow it.
            if name.startswith("Mock") and len(name) > len("Mock"):
                name = name[len("Mock") :]
            if name == "unity.h" or name.startswith("unity_"):
                continue
            resolved = resolve(name, current)
            if resolved is None:
                if re.fullmatch(r"HL_[A-Za-z0-9_]+\.h", name):
                    hcg.add(name)
                continue
            if re.fullmatch(r"HL_[A-Za-z0-9_]+\.h", resolved.name):
                hcg.add(name)
            stack.append(resolved)
    return {p.name for p in seen}, hcg


def main() -> int:
    tests = sorted((REPO / "tests/unit").rglob("test_*.c"))
    rows = []
    for test in tests:
        _, hcg = closure(test)
        rows.append(
            {
                "test": str(test.relative_to(REPO)),
                "variant": "bootloader" if "/bootloader/" in f"/{test}" else "app",
                "hcg_headers": sorted(hcg),
                "hcg_count": len(hcg),
            }
        )
    payload = {
        "total_tests": len(rows),
        "tests_with_no_halcogen_dependency": sum(
            1 for r in rows if r["hcg_count"] == 0
        ),
        "distinct_halcogen_headers": sorted(
            {h for r in rows for h in r["hcg_headers"]}
        ),
        "tests": rows,
    }
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
