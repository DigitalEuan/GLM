#!/bin/bash
# Auto-resume wrapper: the cloud runner can restart mid-run, so each relaunch
# picks the training grid back up from its per-cell checkpoint
# (workspace/push/train_proven_all.jsonl) and only re-does unfinished cells.
cd "$(dirname "$0")/.." || exit 1
LOG="$HOME/glm/squares_lang41_loop.log"
for _ in $(seq 1 40); do
  if grep -q 'full-proven refit' "$LOG" 2>/dev/null; then
    echo "done: refit recorded" >> "$LOG"
    exit 0
  fi
  python3 scripts/cram_language.py --fit-proven-all --workers 8 --steps 8000 --write >> "$LOG" 2>&1
  echo "--- relaunch $(date -u +%H:%M:%S) ckpt $(wc -l < workspace/push/train_proven_all.jsonl) ---" >> "$LOG"
  sleep 2
done
echo "gave up after 40 relaunches" >> "$LOG"
exit 1
