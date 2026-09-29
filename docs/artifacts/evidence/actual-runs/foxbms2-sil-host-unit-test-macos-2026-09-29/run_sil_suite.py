#!/usr/bin/env python3
"""Run the foxBMS 2 host unit tests against the SIL harness and record real evidence.

Every test gets its own Ceedling invocation, so every verdict is individually
attributable and every raw log is kept. Nothing is inferred: the pass/fail
counts are parsed from Ceedling's own OVERALL TEST SUMMARY and cross-checked
against the process exit code, exactly as the pre-SIL sweep did.

Build failures are additionally classified, because "does not build" is not one
thing:

  build:no_hl_surface
        the test reaches a TI HAL symbol the interface headers do not declare
  build:excluded_by_paths
        excluded by the shipped Ceedling :paths: config (upstream's choice)
  build:strict_diagnostic
        fails only under an Apple-clang-only diagnostic promoted by -Werror
  build:missing_module
        the test's module under test is not reachable at all
  build:other
        anything else; the compiler's first message is recorded verbatim

Usage:
    run_sil_suite.py                      # the tests the pre-SIL run could not build
    run_sil_suite.py --all                # every test, for the regression delta
    run_sil_suite.py --only test_can.c    # substring filter
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent.parent
ENV_ROOT = HERE.parent
REPO = pathlib.Path(__file__).resolve().parents[6]
LOGS = HERE / "logs"
SURFACE = LOGS / "hl-surface.json"

SUMMARY_RE = re.compile(
    r"TESTED:\s*(\d+)\s*\n\s*PASSED:\s*(\d+)\s*\n\s*FAILED:\s*(\d+)\s*\n\s*IGNORED:\s*(\d+)",
    re.MULTILINE,
)
CEEDLING_EXC_RE = re.compile(r"EXCEPTION: (.*)", re.MULTILINE)
ERROR_RE = re.compile(r"^(?:\.{0,2}/)?[^\n:]*:\d+:\d+: (?:fatal )?error: (.+)$", re.MULTILINE)

# Symbols the interface headers declare. A build failure that mentions one of
# these is a genuine gap in sil/iface/, not a compiler-diagnostic artefact.
HL_WITNESS = re.compile(
    r"\b(?:HL_[A-Za-z0-9_]+|spiBASE_t|canBASE_t|hetBASE_t|sciBASE_t|i2cBASE_t|gioBASE_t|"
    r"adcBASE_t|crcBASE_t|ecapBASE_t|etpwmBASE_t|rtiBASE_t|dccBASE_t|eqepBASE_t|linBASE_t|"
    r"spiREG\d|canREG\d|hetREG\d|sciREG\d|i2cREG\d|adcREG\d|crcREG\d|rtiREG\d|ecapREG\d|etpwmREG\d|"
    r"spiRAMREG|dmaRAMREG|systemREG\d)\b"
)


def slug(test: str) -> str:
    return test.replace("/", "__").removesuffix(".c")


def tool_versions() -> dict[str, str]:
    env = dict(os.environ)
    env["GEM_HOME"] = str(ENV_ROOT / ".work-gems")
    env["GEM_PATH"] = env["GEM_HOME"]
    env["PATH"] = f"{ENV_ROOT}/bin:{env['GEM_HOME']}/bin:{env['PATH']}"

    def run(cmd: list[str]) -> str:
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=180, check=False)
            return (out.stdout + out.stderr).strip()
        except (OSError, subprocess.SubprocessError) as exc:
            return f"<error: {exc}>"

    gcc = run(["gcc", "--version"]).splitlines()
    return {
        "uname": run(["uname", "-a"]).splitlines()[0],
        "ruby": run(["ruby", "--version"]),
        "gcc": gcc[0] if gcc else "",
        "clang": (run(["clang", "--version"]).splitlines() or [""])[0],
        "ceedling": run(["ceedling", "version"]),
        "cmock": run(["python3", "-c", "print('see ceedling gemspec')"]),
    }


def classify(output: str, test: str) -> str:
    # The shipped :paths: config and :files: :test: list exclude these tests
    # deliberately. Ceedling reports an excluded test as "Found no file ... in
    # search paths", not as a compile error, so it must be recognised first.
    if re.search(r"Found no file `test_", output):
        return "build:excluded_by_shipped_paths"
    errors = ERROR_RE.findall(output)
    if not errors:
        return "build:other"
    joined = " | ".join(errors)
    # A generated mock that fails to parse at a function body: CMock's #if
    # accounting loses sync with FreeRTOS's #if blocks in queue.h / event_groups.h
    # and the tail of the generated file is swallowed. Pre-existing, unrelated to
    # the SIL headers, and platform-independent.
    if "expected identifier or '('" in joined and "/mocks/" in output:
        return "build:ceedling_cmock_config_quirk"
    if HL_WITNESS.search(joined):
        return "build:no_hl_surface"
    if any(
        k in joined
        for k in (
            "-Wenum-conversion",
            "-Warray-bounds",
            "-Wparentheses-equality",
            "-Wimplicit-int",
            "-Wswitch",
            "-Wsign-compare",
            "-Wdeclaration-after-statement",
            "-Wmissing-field-initializers",
        )
    ):
        return "build:strict_diagnostic"
    return "build:other"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--only", default=None)
    ap.add_argument("--out", default="results-sil.json")
    ap.add_argument("--relax", action="store_true")
    ap.add_argument("--log-subdir", default=None)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    surface = json.loads(SURFACE.read_text(encoding="utf-8"))
    rows = surface["closure"]["rows"]
    # Default scope: the tests the pre-SIL analysis could not build because of
    # HALCoGen, i.e. every test with a non-empty HL header set.
    if not args.all:
        rows = [r for r in rows if r["hcg_all"]]
    if args.only:
        rows = [r for r in rows if args.only in r["test"]]
    if args.limit:
        rows = rows[: args.limit]

    log_subdir = args.log_subdir or ("relaxed" if args.relax else "strict")
    test_logs = LOGS / f"per-test-{log_subdir}"
    test_logs.mkdir(parents=True, exist_ok=True)

    env = dict(os.environ)
    env["GEM_HOME"] = str(ENV_ROOT / ".work-gems")
    env["GEM_PATH"] = env["GEM_HOME"]
    env["PATH"] = f"{ENV_ROOT}/bin:{env['GEM_HOME']}/bin:{env['PATH']}"
    if args.relax:
        env["RELAX_CLANG_DIAGNOSTICS"] = "1"

    results = []
    provisioned = set()
    for index, row in enumerate(rows, start=1):
        test = row["test"]
        variant = "bootloader" if "/bootloader/" in test else "app"
        unit_dir = "bootloader_host_unit_test" if variant == "bootloader" else "app_host_unit_test"
        cwd = HERE / "build" / unit_dir
        if variant not in provisioned:
            subprocess.run([str(HERE / "provision.sh"), variant], check=True, capture_output=True, text=True)
            provisioned.add(variant)
        started = time.time()
        stamp = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        proc = subprocess.run(
            [str(HERE / "run.sh"), f"test:{test}"],
            cwd=cwd,
            env={**env, "VARIANT": variant},
            capture_output=True,
            text=True,
            check=False,
            timeout=1800,
        )
        output = proc.stdout + proc.stderr
        (test_logs / f"{slug(test)}.log").write_text(output, encoding="utf-8")
        summary = SUMMARY_RE.search(output)
        rec = {
            "test": test,
            "variant": row["variant"],
            "ceedling_target": f"test:{test}",
            "working_directory": str(cwd),
            "halcogen_headers_required": row["hcg_all"],
            "halcogen_via_test_closure": row["hcg_via_test_closure"],
            "halcogen_via_module_under_test": row["hcg_via_module_under_test"],
            "start_time": stamp,
            "duration_s": round(time.time() - started, 2),
            "exit_code": proc.returncode,
            "outcome": None,
            "tested": int(summary.group(1)) if summary else None,
            "passed": int(summary.group(2)) if summary else None,
            "failed": int(summary.group(3)) if summary else None,
            "ignored": int(summary.group(4)) if summary else None,
            "first_error": None,
            "log": f"logs/per-test-{log_subdir}/{slug(test)}.log",
        }
        if summary and proc.returncode == 0 and int(summary.group(3)) == 0:
            rec["outcome"] = "pass"
        elif summary:
            rec["outcome"] = "fail"
            rec["first_error"] = _first_failure(output)
        else:
            rec["outcome"] = "build_failure"
            rec["build_failure_class"] = classify(output, test)
            errs = ERROR_RE.findall(output)
            exc = CEEDLING_EXC_RE.search(output)
            rec["first_error"] = (
                (errs[0] if errs else (exc.group(1) if exc else output[-400:]))[:400]
            )
            rec["first_error_lines"] = [e[:200] for e in errs[:6]]
        for scratch in ("test/out", "test/dependencies", "test/preprocess", "mocks"):
            shutil.rmtree(cwd / scratch, ignore_errors=True)
        results.append(rec)
        state = (rec["outcome"] + ":" + rec.get("build_failure_class", "")).upper()
        counts = (
            f"tested={rec['tested']} pass={rec['passed']} fail={rec['failed']}"
            if rec["tested"] is not None
            else "no test summary (build failure)"
        )
        print(f"[{index:>3}/{len(rows)}] {state:<34} {counts:<34} {test}", flush=True)

    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "harness": "SIL host unit tests (CMock mocks of host-declared HL_*.h interface headers)",
        "host": tool_versions(),
        "selection": "all" if args.all else "halcogen_blocked_only",
        "relaxed_clang_diagnostics": bool(args.relax),
        "total": len(results),
        "passed_tests": sum(1 for r in results if r["outcome"] == "pass"),
        "failed_tests": sum(1 for r in results if r["outcome"] == "fail"),
        "build_failures": sum(1 for r in results if r["outcome"] == "build_failure"),
        "build_failure_classes": _tally(results),
        "total_assertions_tested": sum(r["tested"] or 0 for r in results),
        "total_assertions_passed": sum(r["passed"] or 0 for r in results),
        "total_assertions_failed": sum(r["failed"] or 0 for r in results),
        "results": results,
    }
    (LOGS / args.out).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print()
    print(json.dumps({k: v for k, v in payload.items() if k != "results"}, indent=2))
    return 0


def _tally(results: list[dict]) -> dict[str, int]:
    out: dict[str, int] = {}
    for r in results:
        if r["outcome"] == "build_failure":
            k = r.get("build_failure_class", "build:other")
            out[k] = out.get(k, 0) + 1
    return dict(sorted(out.items()))


def _first_failure(output: str) -> str | None:
    for line in output.splitlines():
        if ":FAIL:" in line:
            return line.strip()[:500]
    for line in output.splitlines():
        if "FAIL" in line:
            return line.strip()[:500]
    return None


if __name__ == "__main__":
    sys.exit(main())
