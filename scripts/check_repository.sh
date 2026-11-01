#!/usr/bin/env bash
# Check the whole GLM repository (Python side) and keep a log.
#
# Created 31 October 2026 (repository check, STATUS.md item 0).  The companion
# of scripts/rebuild_lean.sh: that one builds the Lean development, this one
# runs every Python gate the documents name.  Run it from anywhere:
#
#     scripts/check_repository.sh           # every gate
#     scripts/check_repository.sh --quick   # skip the test suite and the evaluation
#
# Gates, cheapest first (directive D16):
#   1. the Lean tree, statically   python3 -m glm_universal.lean_check
#   2. the directives               python3 -m glm_universal.tools report directives (via GLM.py)
#   3. the date stamps (D17)        python3 -m glm_universal.tools dates
#   4. the intake ledger (D22)      python3 -m glm_universal.intake check
#   5. the corpus contract          python3 -m glm_universal.corpus --check
#   6. a smoke query                python3 src/GLM.py -q "address of golay"
#   7. the test suite               python3 -m pytest src/glm_universal/tests -q
#   8. the end-to-end evaluation    python3 -m glm_universal.evaluation --jobs 8
# Everything goes to scripts/logs/repository_check_latest.log (and a
# time-stamped copy).  The log ends with one line giving each gate's exit
# status (0 = passed) and a result line; the script itself exits 1 when any
# gate failed and 0 only when every gate it ran passed.  Send the log back
# with the next upload.
#
# Run scripts/rebuild_lean.sh first.  Six tests (one in test_citation_scope.py,
# five in test_proof_dependency.py) read the elaborator's citation graph, and
# only a passing Lean build re-takes it; until rebuild_lean.sh has passed they
# fail, and the pytest gate with them.
#
# Last altered 31 October 2026: the exit status carries the gates' result.
# Last altered 1 November 2026: the run order (rebuild_lean.sh first) stated
# here and printed before the test suite.
set -u
cd "$(dirname "$0")/.."
export PYTHONPATH=src
mkdir -p scripts/logs
STAMP="$(date +%Y%m%d_%H%M%S)"
LOG="scripts/logs/repository_check_${STAMP}.log"
QUICK=0
[ "${1:-}" = "--quick" ] && QUICK=1
{
  echo "# GLM repository check, ${STAMP}, in $(pwd)"
  python3 --version
  python3 -c "import yaml; print('PyYAML', yaml.__version__)" 2>&1
  SUMMARY=""
  FAILED=""
  run() {  # run <name> <command...>
    local name="$1"; shift
    echo
    echo "== ${name}: $*"
    local start=$(date +%s)
    "$@" 2>&1
    local rc=$?
    echo "-- ${name} exit ${rc} after $(( $(date +%s) - start )) s"
    SUMMARY="${SUMMARY} ${name}=${rc}"
    [ "${rc}" = 0 ] || FAILED="${FAILED} ${name}"
  }
  run lean_check  python3 -m glm_universal.lean_check
  run directives  python3 src/GLM.py -q "report directives"
  run dates       python3 -m glm_universal.tools dates
  run intake      python3 -m glm_universal.intake check
  run corpus      python3 -m glm_universal.corpus --check
  run smoke       python3 src/GLM.py -q "address of golay"
  if [ "${QUICK}" = 0 ]; then
    echo
    echo "note: six tests read the elaborator's citation graph and fail until scripts/rebuild_lean.sh has passed"
    run pytest      python3 -m pytest src/glm_universal/tests -q
    run evaluation  python3 -m glm_universal.evaluation --jobs 8
  fi
  echo
  echo "== summary:${SUMMARY} (0 = passed)"
  if [ -z "${FAILED}" ]; then
    echo "== result: PASSED"
    exit 0
  fi
  echo "== result: FAILED:${FAILED}"
  exit 1
} 2>&1 | tee "${LOG}"
STATUS=${PIPESTATUS[0]}
cp "${LOG}" scripts/logs/repository_check_latest.log
echo "log: ${LOG} (copied to scripts/logs/repository_check_latest.log)"
exit "${STATUS}"
