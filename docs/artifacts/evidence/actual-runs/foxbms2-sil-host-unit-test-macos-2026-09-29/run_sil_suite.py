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
import hashlib
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
DIAG_RE = re.compile(
    r"^(?P<file>[^\n:]+\.(?:c|h|m)):(?P<line>\d+):(?P<col>\d+): "
    r"(?P<sev>fatal error|error|warning|note): (?P<msg>.*)$",
    re.MULTILINE,
)
FLAG_RE = re.compile(r"\[((?:-W[a-z0-9-]+)(?:\s*,\s*-W[a-z0-9-]+)*)\]")

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


def _flags(msg: str) -> str:
    """The diagnostic group(s) clang attributed this message to.

    Clang writes the group either bare (`[-Warray-bounds]`) or, when -Werror
    promoted it, prefixed with it (`[-Werror,-Warray-bounds]`). `-Werror` is
    the promotion, not the defect, so it is dropped and the remaining groups
    are kept in order.
    """
    m = FLAG_RE.search(msg)
    if not m:
        return ""
    return ",".join(g for g in (x.strip() for x in m.group(1).split(",")) if g != "-Werror")


def _code(d: dict) -> str:
    """A stable identity for one diagnostic.

    Line and column numbers are deliberately NOT part of the code: they vary
    with unrelated edits, and a class must survive an unrelated line shifting
    above it. Identifiers in quotes and integer literals are folded, so the
    same defect reached from two places collapses to one code.
    """
    msg = d.get("msg", "")
    flag = d.get("flag") or _flags(msg)
    msg = FLAG_RE.sub("", msg)
    msg = re.sub(r"'[^']*'", "'X'", msg)
    msg = re.sub(r"\b0[xX][0-9a-fA-F]+\b", "N", msg)
    msg = re.sub(r"\b\d+\b", "N", msg)
    return f"{d['sev']}|{flag}|{msg}".strip()


def collect_codes(output: str, records: list[dict] | None = None) -> list[dict]:
    """Every distinct diagnostic, keyed by stable code, order-independent.

    `records` is the structured per-translation-unit log written by
    tools/sil_cc.py. When present it is the authoritative source: it is
    collected with SIL_DIAG_COLLECT=1, which makes the wrapper return 0 on a
    failed compile so that Ceedling compiles EVERY remaining translation unit
    instead of aborting at the first one. That is what makes this set
    independent of Ceedling's unstable per-test file order.
    """
    found: dict[str, dict] = {}

    def add(d: dict) -> None:
        if d["sev"] not in ("error", "fatal error"):
            return
        d = {**d, "flag": d.get("flag") or _flags(d.get("msg", ""))}
        c = _code(d)
        if c not in found:
            found[c] = {**d, "code": c, "count": 1, "sites": [f"{d['file']}:{d['line']}"]}
        else:
            found[c]["count"] += 1
            site = f"{d['file']}:{d['line']}"
            if site not in found[c]["sites"] and len(found[c]["sites"]) < 6:
                found[c]["sites"].append(site)

    for rec in records or []:
        if rec.get("rc") == 0:
            continue
        for d in rec.get("diagnostics", []):
            add(d)

    if not records:
        for m in DIAG_RE.finditer(output):
            add(
                {
                    "file": m.group("file"),
                    "line": int(m.group("line")),
                    "col": int(m.group("col")),
                    "sev": m.group("sev"),
                    "msg": m.group("msg").rstrip(),
                }
            )

    return sorted(found.values(), key=lambda d: d["code"])


def _has(codes: list[dict], *needles: str) -> bool:
    return any(any(n in c["code"] for n in needles) for c in codes)


def _in_mocks(codes: list[dict]) -> bool:
    return any("/mocks/" in c["file"] or c["file"].startswith("mocks/") for c in codes)


# --- the decision table -----------------------------------------------------
#
# Every rule is a predicate over the WHOLE set of codes, and the rules are
# evaluated in this fixed order, so the class is a pure function of the set.
# The set itself is order-independent (see collect_codes). Nothing here reads
# "the first error", which is what made the old classifier flip run to run.
#
# `real_defect` outranks everything. A diagnostic that denotes a genuine
# out-of-bounds access, a genuine wrong initializer or a genuine undeclared
# callee is reported as a defect even if a clang-only flag would otherwise have
# filed it under a platform-difference class. A class that exists to explain
# away a red build must never be able to swallow one.
def classify(codes: list[dict], output: str) -> str:
    # Not a build failure at all: upstream's own :paths:/:files: exclusions.
    if re.search(r"Found no file `test_", output):
        return "excluded:upstream_config"

    # Every translation unit compiled; the LINK is what failed. Distinct from
    # every compile class below and worth its own bucket, because a link
    # failure usually means a harness gap (a missing model object) rather than
    # a diagnostic about any construct.
    if not codes:
        return "build:link_failure"

    # --- Genuine defects. Never a platform difference. -----------------------
    # A genuine out-of-bounds array access. Verified by hand, per site, against
    # the declaration: real, and must never be filed under a clang-difference
    # class.
    if _has(codes, "past the end of the array"):
        return "build:real_defect_out_of_bounds_array_index"

    # abs()/labs() on a type the function cannot represent. src/app/driver/
    # rtc/rtc.c:272 calls abs() on a time_t difference. Benign on the 32-bit
    # target, truncating on a 64-bit host. Fixing it is a product change.
    if _has(codes, "absolute value function"):
        return "build:real_defect_absolute_value_truncation"

    # A genuine wrong-arity function-like macro invocation.
    if _has(codes, "arguments provided to function-like macro invocation"):
        return "build:real_defect_macro_arity"

    # A genuine struct initializer with more elements than the type has fields.
    if _has(codes, "excess elements in struct initializer"):
        return "build:real_defect_excess_initializers"

    # A missing declaration of a function. C99 removed implicit declarations;
    # this is an error, not a style diagnostic, on both compilers.
    if _has(codes, "implicit declaration of function", "call to undeclared function"):
        return "build:real_defect_implicit_function_declaration"

    # Implicit int: a type specifier is missing. Invalid in C99 and later on
    # both compilers. Not a platform difference.
    if _has(codes, "type specifier missing"):
        return "build:real_defect_implicit_int"

    # Enabled by -Wall in BOTH compilers, so not a platform difference:
    #   -Wunused-but-set-variable   a test sets a variable and never reads it
    #   -Wmissing-field-initializers a partial initialiser of a large struct
    #   -Wparentheses-equality IS clang-only and is handled further down.
    if _has(codes, "set but not used"):
        return "build:strict_diagnostic_both_compilers"
    if _has(codes, "-Wmissing-field-initializers"):
        return "build:strict_diagnostic_both_compilers"

    # A comparison of an ARRAY against NULL, which is always true.
    # src/app/driver/afe/maxim/common/mxm_17841b.c:707. Behaviour is
    # unchanged, but a tautological guard in product source is a finding, not
    # something to mute. gcc's -Waddress is in -Wall and plausibly covers it,
    # so a clang/gcc difference is NOT established.
    if _has(codes, "not equal to a null pointer is always true"):
        return "build:product_tautological_guard"

    # An identifier used that nothing declares. Where the missing name is a
    # device fact the harness must not invent, the test is reported as not
    # brought up rather than given an invented value.
    if _has(codes, "use of undeclared identifier", "unknown type name"):
        return "build:undeclared_identifier"

    # A conflicting or duplicated declaration of a name the SIL interface
    # headers own. A gap or an error in sil/iface/, not a diagnostic about
    # repository code.
    if _has(codes, "conflicting types for", "duplicate member",
            "too few arguments to function call", "too many arguments to function call",
            "expected a field designator", "invalid parameter name",
            "expected member name or", "expected identifier"):
        return "build:sil_interface_header_mismatch"

    # CMock's generated mock does not parse: the generated file's function
    # definitions are erased by FreeRTOS's own EMPTY function-like macros.
    # The needle stops before the quoted "'('" because _code folds quoted runs
    # to 'X', so the code reads "expected identifier or 'X'".
    if _has(codes, "expected identifier or") and _in_mocks(codes):
        return "build:cmock_freertos_macro_erasure"

    # A TI HAL register macro or an object-format-specific construct.
    # Deliberately not reconstructed: a register offset or base address is a
    # fact about the silicon, and an ELF section name has no Mach-O spelling.
    if _has(codes, "EMAC_MACCONTROL", "EMAC_RXCONTROL", "EMAC_TXCONTROL",
            "EMAC_SOFTRESET", "HWREG", "EMAC_MDIO_") or re.search(
            r"\bEMAC_[A-Z0-9_]*(CONTROL|RESET|OFFSET|MACADDR)\b", output
    ):
        return "build:not_brought_up_register_map"
    if _has(codes, "attribute is not valid for this target",
            "mach-o section specifier"):
        return "build:not_buildable_on_macos_object_format"

    # A diagnostic only Apple clang emits by default; GNU gcc has no
    # equivalent under the shipped -std=c11 -Wextra -Wall -pedantic -Werror.
    # Every flag in this list is justified individually in
    # sil/RELAXED-DIAGNOSTICS.md with the evidence that the construct is
    # correct. Adding to this list without that file being updated is a defect.
    if _has(codes, "-Wenum-conversion", "-Wparentheses-equality",
            "-Wmacro-redefined", "-Wunknown-warning-option",
            "-Wtautological-pointer-compare", "-Wliteral-conversion",
            "-Wnon-literal-null-conversion", "-Wpragma-pack",
            "-Wabsolute-value",
            "attribute only applies to", "attribute ignored when parsing type",
            "expected ')'", "expected expression",
            "initializing '"):
        return "build:clang_only_diagnostic"

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

    # Diagnostics-collecting compiler wrapper. See tools/sil_cc.py: it makes the
    # recorded diagnostic set independent of Ceedling's unstable per-test
    # translation-unit order, which is what made the old `first_error`-keyed
    # classifier flip between runs.
    diag_dir = LOGS / "diag-records"
    diag_dir.mkdir(parents=True, exist_ok=True)
    env["SIL_DIAG_COLLECT"] = "1"
    env["SIL_DIAG_DIR"] = str(diag_dir)
    env["SIL_CC_WRAPPER"] = str(HERE / "tools" / "sil_cc.py")

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

        rec_file = diag_dir / f"{slug(test)}.jsonl"
        rec_file.unlink(missing_ok=True)

        proc = subprocess.run(
            [str(HERE / "run.sh"), f"test:{test}"],
            cwd=cwd,
            env={**env, "VARIANT": variant, "SIL_DIAG_SLUG": slug(test)},
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

        records = []
        if rec_file.exists():
            records = [
                json.loads(line)
                for line in rec_file.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        failed_units = [r for r in records if r.get("rc") not in (0, None)]
        codes = collect_codes(output, records)

        # A failed translation unit is a build failure even if some other
        # translation unit happened to produce a summary: the binary is not
        # trustworthy, so it is never allowed to yield a pass or a fail verdict.
        if summary and not failed_units and proc.returncode == 0 and int(summary.group(3)) == 0:
            rec["outcome"] = "pass"
        elif summary and not failed_units:
            rec["outcome"] = "fail"
            rec["first_error"] = _first_failure(output)
        else:
            rec["outcome"] = "build_failure"
            rec["build_failure_class"] = classify(codes, output)
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
            rec["failed_translation_units"] = sorted(
                {r["src"] for r in failed_units if r.get("src")}
            )
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
        "classifier": {
            "rule": "build failure is classified on the SET of distinct, "
                    "order-independent diagnostic codes (severity | -W flag | "
                    "normalised message), not on any single message",
            "determinism": "the set is collected with SIL_DIAG_COLLECT=1 via "
                           "tools/sil_cc.py, which returns 0 on a failed compile "
                           "so Ceedling compiles every remaining translation "
                           "unit instead of aborting at the first. The set is "
                           "therefore a union over all units and does not depend "
                           "on Ceedling's unstable per-test file order.",
            "replaced": "the previous classifier keyed on `first_error`, i.e. "
                        "on whichever message arrived first, and flipped between "
                        "build:other and build:ceedling_cmock_config_quirk for "
                        "test_os_freertos.c (22/24 vs 2/24 over 24 clean runs)",
        },
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


def _hash_codes(codes: list[dict]) -> str:
    joined = "\n".join(c["code"] for c in codes)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:16] if codes else ""


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
