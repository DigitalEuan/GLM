#!/usr/bin/env bash
# Rebuild the GLM's Lean development from scratch and keep a log.
#
# Created 31 October 2026 (repository check, STATUS.md item 0).  The
# repository is uploaded without its .lake folder; this script makes a fresh
# one.  Run it from anywhere:
#
#     scripts/rebuild_lean.sh            # fetch the Mathlib cache, then build
#     scripts/rebuild_lean.sh --clean    # delete .lake first (a cold rebuild)
#
# It runs, in order, and writes everything to scripts/logs/lean_build_latest.log
# (also kept with a time stamp beside it):
#   1. the static check  (python3 -m glm_universal.lean_check) -- seconds;
#   2. the toolchain versions (elan, lake, lean);
#   3. lake exe cache get  -- downloads the pre-built Mathlib for the pinned commit;
#   4. lake build          -- builds RequestProject, including AxiomAuditAll.lean,
#                             whose #guard_axioms_development fails the build if any
#                             theorem rests on sorry or a non-standard axiom;
#   5. a sorry/admit scan of src/lean/RequestProject (comments ignored);
#   6. only if the build passed: the elaborator's citation graph re-taken
#      (tools citation-scope --reference --write), which the citation-scope
#      and proof-dependency tests read and which needs the compiled library;
#   7. only if steps 1, 4 and 5 all passed: the build record
#      scripts/logs/lean_build_evidence.json -- the SHA-256 of every Lean file
#      that was built and of the toolchain and Mathlib pins.  This record is
#      the evidence the intake's "Lean verified" gate needs
#      (python3 -m glm_universal.intake advance <item> lean_verified); a file
#      edited after the build no longer matches it.
#
# Last altered 31 October 2026 (step 5 ignores comments: a docstring saying
# "no `sorry`" is not a sorry; step 6 added -- the stored citation graph was
# taken over the tree before the reorganisation; step 7 added -- the build
# record that lets the intake promote an item past "Lean verified").
# Last altered 31 October 2026 also: the script exits 1 when any required step
# fails (the log's last lines name them) and 0 only when all pass, so a caller
# can rely on its exit status.
# The log ends with a summary line.  Send scripts/logs/lean_build_latest.log
# and scripts/logs/lean_build_evidence.json back with the next upload and the
# next round fixes whatever the log reports.
set -u
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
mkdir -p scripts/logs
STAMP="$(date +%Y%m%d_%H%M%S)"
LOG="scripts/logs/lean_build_${STAMP}.log"
STATIC=1; CACHE=1; BUILD=1; SORRY=1; CITE=skipped; RECORD=1
{
  echo "# GLM Lean rebuild, ${STAMP}, in ${ROOT}"
  if [ "${1:-}" = "--clean" ]; then
    echo "== removing .lake (cold rebuild)"
    rm -rf .lake
  fi
  echo "== 1. static check (glm_universal.lean_check)"
  PYTHONPATH=src python3 -m glm_universal.lean_check; STATIC=$?
  echo "== 2. toolchain"
  echo "lean-toolchain: $(cat lean-toolchain)"
  (elan --version; lake --version; lean --version) 2>&1
  echo "== 3. lake exe cache get"
  lake exe cache get 2>&1; CACHE=$?
  echo "== 4. lake build"
  START=$(date +%s)
  lake build 2>&1; BUILD=$?
  echo "lake build exit ${BUILD} after $(( $(date +%s) - START )) s"
  echo "== 5. sorry / admit scan (comments ignored)"
  PYTHONPATH=src python3 - <<'PY'; SORRY=$?
import re, sys
from glm_universal.constants import LEAN_SOURCE_DIR, LEAN_LIBRARY
from glm_universal.lean_check import _strip_comments
hits = []
for p in sorted((LEAN_SOURCE_DIR / LEAN_LIBRARY).rglob("*.lean")):
    code = _strip_comments(p.read_text(encoding="utf-8"))
    for i, line in enumerate(code.splitlines(), 1):
        if re.search(r"\b(sorry|admit)\b", line):
            hits.append(f"{p.relative_to(LEAN_SOURCE_DIR)}:{i}: {line.strip()}")
print("\n".join(hits) if hits else "none")
sys.exit(1 if hits else 0)
PY
  echo "== 6. citation reference (tools citation-scope --reference --write)"
  if [ "${BUILD}" = "0" ]; then
    PYTHONPATH=src python3 -m glm_universal.tools citation-scope --reference --write 2>&1; CITE=$?
  else
    echo "skipped: the build did not pass"
  fi
  echo "== 7. build record (scripts/logs/lean_build_evidence.json)"
  PYTHONPATH=src python3 -m glm_universal.lean_check --write-build-evidence \
    --static-exit "${STATIC}" --build-exit "${BUILD}" --sorry-exit "${SORRY}" --log "${LOG}"; RECORD=$?
  echo "== summary: static=${STATIC} cache=${CACHE} build=${BUILD} sorry=${SORRY} citation=${CITE} record=${RECORD} (0 = ok)"
  # The script's own exit status: 0 only when every required step passed
  # (the static check, the build, the sorry scan, the citation re-take when
  # it ran, and the build record).  The cache download is not required: a
  # build that compiles Mathlib itself is as good, only slower.
  FAILED=""
  [ "${STATIC}" = 0 ] || FAILED="${FAILED} static"
  [ "${BUILD}" = 0 ] || FAILED="${FAILED} build"
  [ "${SORRY}" = 0 ] || FAILED="${FAILED} sorry"
  [ "${CITE}" = 0 ] || [ "${CITE}" = skipped ] || FAILED="${FAILED} citation"
  [ "${RECORD}" = 0 ] || FAILED="${FAILED} record"
  if [ -z "${FAILED}" ]; then
    echo "== result: PASSED"
    exit 0
  fi
  echo "== result: FAILED:${FAILED}"
  exit 1
} 2>&1 | tee "${LOG}"
STATUS=${PIPESTATUS[0]}
cp "${LOG}" scripts/logs/lean_build_latest.log
echo "log: ${LOG} (copied to scripts/logs/lean_build_latest.log)"
exit "${STATUS}"
