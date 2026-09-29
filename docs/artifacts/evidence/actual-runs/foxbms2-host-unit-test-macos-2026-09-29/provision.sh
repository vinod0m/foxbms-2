#!/usr/bin/env bash
#
# Provision the isolated foxBMS 2 host unit-test Ceedling workspace on macOS.
#
# This script reproduces, inside docs/artifacts/.work/verification-env/, what
# `fox.py ceedling` would do inside build/<variant>_host_unit_test/ -- except that
# it is done without touching the live checkout, because
# cli/cmd_embedded_ut/embedded_ut_impl.py raises SystemExit at import time on
# any platform that is neither "linux" nor "win32" (see embedded_ut_impl.py:88).
#
# Nothing under src/ tests/ conf/ tools/ cli/ gui/ hardware/ or the repo-root
# wscript/fox.py/fox.sh is read-write touched. The repository's src/, tests/
# and conf/ trees are reached through symlinks; Ceedling writes only into the
# build/ directory below this workspace.
#
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "${HERE}/../../../.." && pwd)"
VARIANT="${1:-app}"

case "${VARIANT}" in
  app)        UNIT_DIR="app_host_unit_test" ;;
  bootloader) UNIT_DIR="bootloader_host_unit_test" ;;
  *) echo "usage: $0 [app|bootloader]" >&2; exit 2 ;;
esac

BUILD="${HERE}/build/${UNIT_DIR}"

echo "== repo   : ${REPO}"
echo "== variant: ${VARIANT}"
echo "== build  : ${BUILD}"

mkdir -p "${BUILD}/include" "${BUILD}/source"

# The shipped Ceedling project file for POSIX hosts. foxBMS ships it as
# conf/unit/<variant>_project_<platform>.yml and copies it to project.yml.
# :build_root: . means every path inside it is relative to this directory, so
# the ../../src, ../../tests and ../../conf references are satisfied by the
# symlinks below.
for tree in src tests conf; do
  ln -sfn "${REPO}/${tree}" "${HERE}/${tree}"
done
cp -f "${REPO}/conf/unit/${VARIANT}_project_posix.yml" "${BUILD}/project.yml"

# HALCoGen inputs. HALCoGen itself is proprietary TI software and is not
# available; _run_halcogen() in the fox CLI tolerates its absence and logs
# "Assuming HALCoGen sources are available...". We therefore reproduce the two
# things its output is actually needed for (see tools/waf-tools/f_hcg.py:150-157
# and cli/cmd_embedded_ut/embedded_ut_impl.py:247-275):
#
#   1. conf/hcg/<variant>.hcg and .dil are copied verbatim.
#   2. include/config_cpu_clock_hz.h is synthesised. That header is the ONLY
#      artefact the host build needs from HALCoGen: every other generated file
#      is on the conf/hcg/<variant>-remove.yml removal list, and the FreeRTOS
#      sources HALCoGen would emit are already shipped in src/os/freertos/.
#      The clock value is read from the committed conf/hcg/<variant>.dil
#      (DRIVER.OS.VAR.OS_CPUCLOCKHZ.VALUE) rather than guessed.
cp -f "${REPO}/conf/hcg/${VARIANT}.hcg" "${BUILD}/${VARIANT}.hcg"
cp -f "${REPO}/conf/hcg/${VARIANT}.dil" "${BUILD}/${VARIANT}.dil"

python3 "${HERE}/make_halcogen_stubs.py" "${BUILD}/${VARIANT}.dil" "${BUILD}"

echo "== ceedling project file is byte-identical to conf/unit/${VARIANT}_project_posix.yml"
cmp -s "${REPO}/conf/unit/${VARIANT}_project_posix.yml" "${BUILD}/project.yml" \
  && echo "   cmp: OK (unmodified)" || { echo "   cmp: MISMATCH" >&2; exit 1; }
echo "== workspace ready"
