#!/usr/bin/env python3
"""Verify every `excluded:upstream_config` test against the shipped Ceedling config.

The classification asserts that a test did not fail; it was never in scope. That
is a strong claim about someone's deliberate decision, so it is checked against
the shipped config rather than assumed:

  * for each variant, load conf/unit/<variant>_project_posix.yml;
  * collect the NEGATIVE `:paths:` entries and the negative `:files: :test:`
    entries -- the two ways the project can exclude a test;
  * match each excluded test against them.

The check is reported three ways, because the three outcomes are different and
only two of them are "correctly excluded":

  EXCLUDED_UPSTREAM   matched a negative :paths: or :files: entry. Upstream's
                      own deliberate exclusion. Not a SIL gap, not a failure.
  NOT_A_TEST          the file is not a test at all: it lives in the
                      `:support:` tree and contains no test function. It is
                      swept in only because the harness enumerates candidates
                      with a filename glob (`test_*.c`).
  REAL_FAILURE        matched nothing. The harness is wrong and the test is a
                      genuine failure. This is the case that must be zero.

Usage:
    verify_exclusions.py RESULTS.json [--repo REPO] [--json OUT.json]
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[6]

# A test file must define at least one Unity test function to be a test.
TEST_FN = re.compile(r"^\s*void\s+(test\w+)\s*\(\s*(?:void)?\s*\)\s*\{", re.M)


def neg_entries(text: str) -> list[tuple[str, str, int]]:
    """Every `- -<path>` exclusion, with its line number and its section.

    Both exclusion mechanisms have the same YAML shape, so they cannot be told
    apart textually; the line number and a section probe are used instead, and
    the section is reported so a reader can see which mechanism applied.
    """
    out: list[tuple[str, str, int]] = []
    section = "?"
    for n, line in enumerate(text.splitlines(), start=1):
        m = re.match(r"^(\s*)(:[\w]+):\s*$", line)
        if m:
            section = m.group(2)
            continue
        m = re.match(r"\s*-\s*-\s*(\S+)\s*$", line)
        if m:
            out.append((section, m.group(1), n))
    return out


def to_repo_rel(g: str) -> str:
    """`./../../tests/unit/app/main` -> `tests/unit/app/main`"""
    parts = [p for p in pathlib.PurePosixPath(g).parts if p not in (".", "/")]
    # drop leading ".." segments
    while parts and parts[0] == "..":
        parts.pop(0)
    try:
        i = parts.index("tests")
        parts = parts[i:]
    except ValueError:
        pass
    return "/".join(parts)


def covers(glob_rel: str, test_rel: str) -> bool:
    """Does this negative glob cover this test path?

    Handles the two forms the shipped config actually uses:
      an exact file       tests/unit/app/main/test_fstartup.c
      a directory prefix tests/unit/app/driver/afe/adi/common/ades183x/**
    """
    if glob_rel.endswith("/**"):
        prefix = glob_rel[:-3]
        return test_rel == prefix or test_rel.startswith(prefix + "/")
    return glob_rel == test_rel


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--repo", default=str(REPO))
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    repo = pathlib.Path(args.repo)
    configs = {
        "app": (repo / "conf/unit/app_project_posix.yml").read_text(encoding="utf-8"),
        "bootloader": (repo / "conf/unit/bootloader_project_posix.yml").read_text(
            encoding="utf-8"
        ),
    }
    negs = {k: neg_entries(v) for k, v in configs.items()}

    data = json.loads(pathlib.Path(args.results).read_text(encoding="utf-8"))
    rows = []
    for rec in data["results"]:
        if rec.get("build_failure_class") != "excluded:upstream_config":
            continue
        variant = rec["variant"]
        rel = rec["test"]

        # Only exclusions from the variant this test belongs to. The app config
        # does not describe the bootloader tree, so borrowing its entries would
        # be exactly the kind of unfounded match this tool exists to catch.
        matched: tuple[str, str, int] | None = None
        for section, glob, line in negs.get(variant, []):
            if covers(to_repo_rel(glob), rel):
                matched = (section, glob, line)
                break

        if matched is not None:
            section, glob, line = matched
            verdict = "EXCLUDED_UPSTREAM"
            mech = (
                ":files: :test: (file-level)"
                if section == ":test:" and not glob.endswith("/**")
                else ":paths: (search-path level)"
                if section == ":paths:"
                else f"{section} (search-path level)"
            )
            evidence = (
                f"conf/unit/{variant}_project_posix.yml:{line} excludes it: "
                f"`- -{glob}` via {mech}"
            )
        else:
            src = repo / rel
            has_test_fn = bool(
                src.exists()
                and TEST_FN.search(src.read_text(encoding="utf-8", errors="replace"))
            )
            in_support = "/support/" in rel
            if not has_test_fn and in_support:
                verdict = "NOT_A_TEST"
                evidence = (
                    f"{rel} matched no negative entry in "
                    f"conf/unit/{variant}_project_posix.yml, and it is not a "
                    f"test: it lives in the :support: tree, declares no Unity "
                    f"test function, and conf/unit removes tests/unit/support "
                    f"from :paths: :test: while adding it as :support:. It is "
                    f"enumerated only because the harness globs test_*.c."
                )
            else:
                verdict = "REAL_FAILURE"
                evidence = (
                    f"{rel} matched no negative entry in "
                    f"conf/unit/{variant}_project_posix.yml and does define test "
                    f"functions. It is a genuine failure, not an exclusion."
                )
        rows.append(
            {
                "test": rel,
                "variant": variant,
                "verdict": verdict,
                "evidence": evidence,
            }
        )

    tally: dict[str, int] = {}
    for r in rows:
        tally[r["verdict"]] = tally.get(r["verdict"], 0) + 1

    print(f"verified {len(rows)} tests classified excluded:upstream_config")
    for k in sorted(tally):
        print(f"  {tally[k]:>4}  {k}")
    print()
    for r in sorted(rows, key=lambda x: (x["verdict"], x["test"])):
        print(f"[{r['verdict']:<19}] {r['test']}")
        print(f"    {r['evidence']}")

    payload = {
        "results_file": str(args.results),
        "total_classified_excluded": len(rows),
        "tally": tally,
        "negative_entries_found": {
            k: [{"section": s, "glob": g, "line": n} for s, g, n in v]
            for k, v in negs.items()
        },
        "rows": rows,
    }
    if args.json:
        pathlib.Path(args.json).write_text(
            json.dumps(payload, indent=2) + "\n", encoding="utf-8"
        )
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
