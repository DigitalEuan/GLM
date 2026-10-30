#!/bin/sh
# Round 12 setup, run from the directory holding GLM.py (e.g. glm_repo/overlay), with the Rule 30
# study folder (the one holding parser.py, session.py, ..., rule30_round9..12) at $STUDY.
#   STUDY=/path/to/study sh $STUDY/rule30_round12/setup_round12.sh
# It runs the Round 11 setup first (which ends "round 11: all checks pass"), then adds Round 12.
set -e
: "${STUDY:?set STUDY to the Rule 30 study folder}"
G=glm_universal
sh "$STUDY"/rule30_round11/setup_round11.sh
# the Round 12 overlay (supersedes data_objects/automata.py of Round 11 by one hook line)
cp -r "$STUDY"/rule30_round12/glm_$G/. $G/
# toolbox: tool theorem and tool discuss, with their English openings
patch -p1 -N < "$STUDY"/rule30_round12/toolbox_round12.patch || true
mkdir -p rule30_round12 && cp "$STUDY"/rule30_round12/*.py rule30_round12/
PYTHONPATH=. python3 rule30_round12/test_round12.py
