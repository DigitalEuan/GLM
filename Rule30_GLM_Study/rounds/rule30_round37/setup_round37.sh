#!/bin/sh
# Round 37 setup, run from the directory holding GLM.py (glm_repo/overlay), with the Rule 30
# study folder at $STUDY:
#   STUDY=/path/to/study sh $STUDY/rule30_round37/setup_round37.sh
# It runs the Round 34 setup (which runs Rounds 11-16, 28-30, 33 and 34), then installs the
# Round 37 overlay (hub index, theorem wheel to Round 37 with the hub rule, hub-first tool next,
# tool requirements, their data) and its toolbox hooks.  Ends with "round 37: all checks pass".
set -e
: "${STUDY:?set STUDY to the Rule 30 study folder}"
G=glm_universal
sh "$STUDY"/rule30_round34/setup_round34.sh
cp -r "$STUDY"/rule30_round37/glm_overlay/$G/. $G/
python3 "$STUDY"/rule30_round37/apply_round37.py
mkdir -p rule30_round37 && cp "$STUDY"/rule30_round37/*.py "$STUDY"/rule30_round37/*.json rule30_round37/
PYTHONPATH=. python3 rule30_round37/test_round37.py
