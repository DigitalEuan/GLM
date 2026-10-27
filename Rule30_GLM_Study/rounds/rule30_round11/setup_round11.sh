#!/bin/sh
# Round 11 setup, run from the directory holding GLM.py (e.g. glm_repo/overlay), with the
# Rule 30 study folder (the one holding parser.py, session.py, ..., rule30_round9/10/11) at $STUDY.
#   STUDY=/path/to/study sh $STUDY/rule30_round11/setup_round11.sh
set -e
: "${STUDY:?set STUDY to the Rule 30 study folder}"
G=glm_universal
# your files (Rounds 8-9 and the Round 11 attachments)
cp "$STUDY"/parser.py "$STUDY"/session.py "$STUDY"/tct_engine.py      $G/runtime/
cp "$STUDY"/__init__.py "$STUDY"/lattice_geometry.py                 $G/runtime/reports/
cp "$STUDY"/semantic_plan.py "$STUDY"/stepwise.py                   $G/runtime/
cp "$STUDY"/speak.py                                                $G/engineering/
cp "$STUDY"/batch_machine.py "$STUDY"/llvq.py "$STUDY"/nearest_address.py \
   "$STUDY"/timed_question.py                                       $G/reasoning/
# stand-ins (only where your tree has no module; replace with your real files)
[ -f $G/reasoning/frozen_path.py ]      || cp "$STUDY"/rule30_round9/frozen_path_standin.py $G/reasoning/frozen_path.py
[ -f $G/evaluation/harness.py ]         || cp "$STUDY"/rule30_round11/standins/evaluation_harness_standin.py $G/evaluation/harness.py
[ -f $G/runtime/respell.py ]            || cp "$STUDY"/rule30_round11/standins/respell_standin.py $G/runtime/respell.py
[ -f $G/runtime/sinter.py ]             || cp "$STUDY"/rule30_round11/standins/sinter_standin.py $G/runtime/sinter.py
[ -f $G/reasoning/colour_induction.py ] || cp "$STUDY"/rule30_round11/standins/colour_induction_standin.py $G/reasoning/colour_induction.py
# the overlays, in order (each later round supersedes files of the earlier ones)
cp -r "$STUDY"/rule30_round9/glm_overlay/$G/.  $G/
cp -r "$STUDY"/rule30_round10/glm_overlay/$G/. $G/
cp -r "$STUDY"/rule30_round11/glm_overlay/$G/. $G/
# toolbox: the wheel fallback of tool induce (Round 10), then tool claim (Round 11)
patch -p1 -N < "$STUDY"/rule30_round10/toolbox_wheel_induction.patch || true
patch -p1 -N < "$STUDY"/rule30_round11/toolbox_claim.patch || true
mkdir -p rule30_round11 && cp "$STUDY"/rule30_round11/*.py "$STUDY"/rule30_round11/*.json rule30_round11/
PYTHONPATH=. python3 rule30_round11/test_round11.py
