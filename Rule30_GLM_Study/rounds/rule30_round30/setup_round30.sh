#!/bin/sh
# Round 30 setup, run from the directory holding GLM.py (glm_repo/overlay), with the Rule 30
# study folder at $STUDY:
#   STUDY=/path/to/study PKG=/path/to/RequestProject/GLM/Rule30 sh $STUDY/rule30_round30/setup_round30.sh
# It runs the Round 29 setup (which runs Rounds 11-16 and 28), then installs the Round 30
# pipeline (glm_pipeline, statement_planner, pipeline_tool, the certified frontier data) and its
# toolbox hooks.  Ends with "round 30: all checks pass".
set -e
: "${STUDY:?set STUDY to the Rule 30 study folder}"
G=glm_universal
sh "$STUDY"/rule30_round29/setup_round29.sh
cp -r "$STUDY"/rule30_round30/glm_overlay/$G/. $G/
python3 "$STUDY"/rule30_round30/apply_round30.py
mkdir -p rule30_round30 && cp "$STUDY"/rule30_round30/*.py rule30_round30/
PYTHONPATH=. python3 rule30_round30/test_round30.py
