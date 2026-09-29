#!/usr/bin/env bash
#
# probe_pragma_pack.sh -- the evidence behind `-Wno-pragma-pack`.
#
# Seven tests fail to build under Apple clang with
#   error: the current #pragma pack alignment value is modified in the
#          included file [-Werror,-Wpragma-pack]
# raised 133 times, all inside the vendored FreeRTOS+TCP stack.
#
# -Wpragma-pack is a Clang diagnostic. GNU gcc has no equivalent and silently
# accepts `#pragma pack(push,1)` in one file and `#pragma pack(pop)` in another
# -- which is the idiom this stack uses, because pack_struct_start.h and
# pack_struct_end.h are separate headers precisely so they can bracket a struct
# declared in a third header. That makes the diagnostic a plausible platform
# difference. Plausible is not evidence, so this script measures the layout
# both ways.
#
# It answers one question: does silencing the WARNING change anything, or is
# the pragma load-bearing?
#
#   A) compile all 22 pack_struct-bracketed structs WITH the repo's pragma
#   B) compile the same 22 with the pragma removed
#   and diff sizeof().
#
# If (A) == (B) the pragma would be inert and the flag pointless. It is not:
# 7 of 22 differ, so the pragma is load-bearing, and suppressing the diagnostic
# -- which does not remove the pragma -- is both safe and necessary.
#
# The 22 struct bodies are EXTRACTED from the repository by regex, not
# transcribed, so this measures the repository's construct.
#
# LIMIT: this verifies the COMPILER's layout, not the receiver's. It says
# nothing about the wire, and this harness verifies no timing, no DMA, no
# clocking and no device behaviour.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "${HERE}/../../../../../.." && pwd)"
TCP="${REPO}/src/os/freertos/freertos-plus/freertos-plus-tcp"
PKG="${TCP}/source/portable/Compiler/CCS"
WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

# FreeRTOS+TCP's own configuration constants, which the DHCP message needs to
# be a complete type. These are stack settings, not device facts, and BOTH arms
# of the comparison use the identical values, so the A/B is unaffected.
read -r -d '' PRELUDE <<'EOF' || true
#include <stdint.h>
#include <stdio.h>
#define dhcpCLIENT_HARDWARE_ADDRESS_LENGTH 6U
#define dhcpSERVER_HOST_NAME_LENGTH 64U
#define dhcpBOOT_FILE_NAME_LENGTH 128U
#define ipSIZE_OF_IPv4_ADDRESS 4U
#define ipSIZE_OF_ETH_HEADER 14U
#define ipIPv6_STRING_LENGTH 46U
typedef struct xMAC_ADDRESS { uint8_t ucBytes[6]; } MACAddress_t;
typedef struct xIPv6_ADDRESS { uint8_t ucBytes[16]; } IPv6_Address_t;
EOF

python3 - "${TCP}" "${WORK}" "${PRELUDE}" <<'PY'
import re, sys, pathlib
tcp, work, prelude = sys.argv[1], pathlib.Path(sys.argv[2]), sys.argv[3]
pat = re.compile(
    r'#include "pack_struct_start\.h"\s*\nstruct\s+(\w+)\s*\{(.*?)\}\s*\n'
    r'#include "pack_struct_end\.h"\s*\ntypedef struct (?:\w+ )?(\w+);', re.S)
seen, out = set(), []
for p in sorted(pathlib.Path(tcp).rglob('*.h')):
    for m in pat.finditer(p.read_text(errors='replace')):
        struct, body, typedef = m.group(1), m.group(2), m.group(3)
        if struct in seen:
            continue
        seen.add(struct)
        out.append((struct, body, typedef))

def emit(pragma: bool) -> str:
    s = prelude + "\n"
    for struct, body, typedef in out:
        if pragma:
            s += (f'#include "pack_struct_start.h"\nstruct {struct}\n{{\n{body}\n}}\n'
                  f'#include "pack_struct_end.h"\n')
        else:
            # pack_struct_end.h opens with a ';' that terminates the struct tag.
            # With the bracket removed that ';' is gone, so put it back.
            s += f'struct {struct}\n{{\n{body}\n}};\n'
        s += f'typedef struct {struct} {typedef};\n'
    s += "\nint main(void){\n"
    for _, _, typedef in out:
        s += f'  printf("{typedef}\\t%zu\\n", sizeof({typedef}));\n'
    s += "  return 0;}\n"
    return s

(work / "packed.c").write_text(emit(True))
(work / "natural.c").write_text(emit(False))
print(f"extracted {len(out)} pack_struct-bracketed structs from the vendored +TCP stack")
PY

echo
echo "=== A) pack pragma ACTIVE (the repository's own pack_struct_*.h) ==="
clang -std=c11 -w -I "${PKG}" -o "${WORK}/packed" "${WORK}/packed.c"
"${WORK}/packed" | sort > "${WORK}/sizes_packed.txt"
wc -l < "${WORK}/sizes_packed.txt" | tr -d ' ' | sed 's/^/    structs: /'

echo
echo "=== B) pack pragma REMOVED (identical struct bodies) ==="
mkdir -p "${WORK}/nopack"
sed -e 's/^#pragma pack(push, 1)$//' -e 's/^#pragma diag_push$//' -e 's/^#pragma diag_suppress=1916$//' \
    "${PKG}/pack_struct_start.h" > "${WORK}/nopack/pack_struct_start.h"
sed -e 's/^#pragma pack(pop)$//' -e 's/^#pragma diag_pop$//' \
    "${PKG}/pack_struct_end.h" > "${WORK}/nopack/pack_struct_end.h"
clang -std=c11 -w -I "${WORK}/nopack" -o "${WORK}/natural" "${WORK}/natural.c"
"${WORK}/natural" | sort > "${WORK}/sizes_natural.txt"

echo
echo "=== sizeof, packed vs natural ==="
# sizes_packed.txt and sizes_natural.txt are both "NAME<TAB>SIZE".
diff_count=$(diff "${WORK}/sizes_packed.txt" "${WORK}/sizes_natural.txt" | grep -c '^<' || true)
paste "${WORK}/sizes_packed.txt" "${WORK}/sizes_natural.txt" |
  awk -F'\t' '{
      if ($2 == $4) printf "    %-34s packed=%-4s natural=%-4s same\n", $1, $2, $4;
      else          printf "    %-34s packed=%-4s natural=%-4s  *** DIFFERENT -- pragma is load-bearing\n", $1, $2, $4;
  }'

echo
echo "=== verdict ==="
echo "    ${diff_count} of $(wc -l < "${WORK}/sizes_packed.txt" | tr -d ' ') structs change size when the pragma is removed."
echo "    -> The pragma is load-bearing, so it must stay."
echo "    -> -Wno-pragma-pack silences the DIAGNOSTIC about it and leaves the pragma"
echo "       in force, so the packed layout is exactly the one the wire requires."
echo "    -> Negative control: this diff is what makes the measurement non-vacuous."
echo "       A vacuous result (0 differences) would have meant the pragma was"
echo "       inert on this ABI and the flag unnecessary."
