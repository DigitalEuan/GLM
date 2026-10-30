#!/bin/sh
# Round 29 setup, run from the directory holding GLM.py (glm_repo/overlay), with the Rule 30
# study folder at $STUDY:
#   STUDY=/path/to/study PKG=/path/to/RequestProject/GLM/Rule30 sh $STUDY/rule30_round29/setup_round29.sh
# It runs the Round 28 setup (which runs Rounds 11-16), then installs the Round 29 planner and
# its toolbox hooks.  Ends with "round 29: all checks pass".
set -e
: "${STUDY:?set STUDY to the Rule 30 study folder}"
G=glm_universal
sh "$STUDY"/rule30_round28/setup_round28.sh
cp -r "$STUDY"/rule30_round29/glm_$G/. $G/
python3 "$STUDY"/rule30_round29/apply_round29.py
mkdir -p rule30_round29 && cp "$STUDY"/rule30_round29/*.py rule30_round29/
PYTHONPATH=. python3 rule30_round29/test_round29.py
