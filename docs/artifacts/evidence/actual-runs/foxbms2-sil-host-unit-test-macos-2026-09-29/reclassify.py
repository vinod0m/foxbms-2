#!/usr/bin/env python3
"""Re-classify an existing results file under the current classifier.

WHY
---
The classifier used to key on `first_error` -- the first compiler message --
which is not stable, because Ceedling compiles a test's translation units in an
unstable order and aborts at the first failure. See
sil/logs/evidence-classifier-flip-detail.txt: test_os_freertos.c landed in
build:ceedling_cmock_config_quirk in the recorded run and in build:other in a
re-measurement, purely because of compile order.

The classifier now keys on the SET of distinct diagnostic codes. An existing
results file therefore reports a class the current tool would never produce, and
leaving it alone would make the recorded evidence disagree with what the tool
now says. This re-derives the class for every record.

HONEST LIMIT
------------
This reads the per-test logs that were recorded with the OLD harness, which did
not compile every translation unit -- Ceedling stopped at the first failure. The
re-derived code set is therefore whatever that run happened to surface, and
inherits its order-dependence. That is unavoidable when re-classifying
evidence that was gathered without the collection wrapper, and it is stated
here rather than hidden: `reclassified_from_incomplete_diagnostic_set` is set to
true on every record this tool touches, so a consumer can tell the difference
between a set that was complete by construction and one that was salvaged.

For a trustworthy set, re-run the sweep: sil/tools/sil_cc.py makes the set a
union over all translation units regardless of order.

Usage:
    reclassify.py RESULTS.json --logs <dir> [--out OUT.json]
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from run_sil_suite import collect_codes, classify, slug, _hash_codes  # noqa: E402

# The pre-refactor class names, kept only to report what changed.
OLD_NAMES = {
    "build:excluded_by_shipped_paths": "excluded:upstream_config",
    "build:ceedling_cmock_config_quirk": "build:cmock_freertos_macro_erasure",
    "build:no_hl_surface": "build:undeclared_identifier",
    "build:strict_diagnostic": "build:clang_only_diagnostic",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--logs", required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    src = pathlib.Path(args.results)
    logs = pathlib.Path(args.logs)
    data = json.loads(src.read_text(encoding="utf-8"))

    changed = 0
    for rec in data["results"]:
        if rec["outcome"] != "build_failure":
            continue
        was = rec.get("build_failure_class")
        log = logs / f"{slug(rec['test'])}.log"
        if not log.exists():
            rec["reclassify_status"] = "no log found; class left unchanged"
            continue
        output = log.read_text(encoding="utf-8", errors="replace")
        codes = collect_codes(output, None)
        now = classify(codes, output)
        rec["build_failure_class_previous"] = was
        if was != now:
            changed += 1
        rec["build_failure_class"] = now
        rec["error_code_set"] = [c["code"] for c in codes]
        rec["error_code_set_hash"] = _hash_codes(codes)
        rec["diagnostic_codes"] = [
            {
                "code": c["code"],
                "severity": c["sev"],
                "flag": c.get("flag", ""),
                "count": c["count"],
                "sites": c["sites"],
            }
            for c in codes
        ]
        rec["reclassified_from_incomplete_diagnostic_set"] = True

    data["build_failure_classes"] = _tally(data["results"])
    data["classifier"] = {
        "rule": "build failure is classified on the SET of distinct, "
                "order-independent diagnostic codes (severity | -W flag | "
                "normalised message), never on a single message",
        "reclassified_at": "see generated_at",
        "reclassified_from": str(src),
        "reclassified_log_dir": str(logs),
        "caveat": "the per-test logs in reclassified_log_dir were recorded by "
                  "the previous harness, which stopped at the first failing "
                  "translation unit, so the code set salvaged from them is "
                  "whatever that run surfaced and is order-dependent. Every "
                  "record carries "
                  "reclassified_from_incomplete_diagnostic_set=true. Re-run the "
                  "sweep for a set that is complete by construction.",
        "old_class_names": OLD_NAMES,
    }
    data["reclassified_build_failures_changed"] = changed

    out = pathlib.Path(args.out) if args.out else src
    out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"reclassified {sum(1 for r in data['results'] if r['outcome'] == 'build_failure')} "
          f"build failures; {changed} changed class -> {out}")
    print(json.dumps(data["build_failure_classes"], indent=2))
    return 0


def _tally(results: list[dict]) -> dict[str, int]:
    out: dict[str, int] = {}
    for r in results:
        if r["outcome"] == "build_failure":
            k = r.get("build_failure_class", "build:other")
            out[k] = out.get(k, 0) + 1
    return dict(sorted(out.items()))


if __name__ == "__main__":
    sys.exit(main())
