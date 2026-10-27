#!/bin/sh
# Round 28 setup, run from the directory holding GLM.py (glm_repo/overlay), with the Rule 30
# study folder at $STUDY:
#   STUDY=/path/to/study PKG=/path/to/RequestProject/GLM/Rule30 sh $STUDY/rule30_round28/setup_round28.sh
# (PKG is optional: it installs the full ledger carriers glm/r28_wheel.json from the Lean package.)
# It runs the Round 12 setup (which runs Round 11), adds the Round 13 and Round 16 overlays,
# then Round 28: local-rule induction, the Round 28 theorem wheel, the ledger carriers, and the
# toolbox hooks.  Ends with "round 28: all checks pass".
set -e
: "${STUDY:?set STUDY to the Rule 30 study folder}"
G=glm_universal
sh "$STUDY"/rule30_round12/setup_round12.sh
cp -r "$STUDY"/rule30_round13/glm_overlay/$G/. $G/
cp -r "$STUDY"/rule30_round16/glm_overlay/$G/. $G/
cp -r "$STUDY"/rule30_round28/glm_overlay/$G/. $G/
# the full evidence ledger as carriers, from the Lean package (optional; else a 3-row sample)
if [ -n "${PKG:-}" ] && [ -f "$PKG"/glm/r28_wheel.json ]; then
  cp "$PKG"/glm/r28_wheel.json $G/reasoning/_data/r28_wheel.json
fi
python3 "$STUDY"/rule30_round28/apply_round28.py
mkdir -p rule30_round28 && cp "$STUDY"/rule30_round28/*.py rule30_round28/
PYTHONPATH=. python3 rule30_round28/test_round28.py
