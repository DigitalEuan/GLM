import RequestProject.GLM.Rule30
import RequestProject.GLM.HypothesisEngine
import RequestProject.GLM.Escalation.LayerStack
import RequestProject.GLM.Escalation.MasterStep
import RequestProject.GLM.Escalation.GolayTies
import RequestProject.GLM.Escalation.Rule30Parity
import RequestProject.GLM.Escalation.Niemeier
import RequestProject.GLM.Escalation.LeechResidue

/-!
# The Rule 30 study package — single root

This file imports everything the Rule 30 study produced:

* `RequestProject/GLM/Rule30.lean` — the Rule 30 mathematics (guide: `Rule30/README.md`);
* `RequestProject/GLM/HypothesisEngine.lean` — the Hypothesis Engine contracts and benchmarks
  (guide: `HypothesisEngine/README.md`);
* the six modules of `RequestProject/GLM/Escalation/` — the escalation-boundaries checks
  (guide: `Escalation/README.md`).

It imports the six escalation modules directly rather than through
`RequestProject/GLM/Escalation.lean`, because the GLM repository already has its own module of
that name. This root does not collide with any GLM module, so it is the file to import after
merging the package into the GLM (see `MERGE_INTO_GLM.md` at the top of this project).

`lake build RequestProject.GLM.Rule30Study` builds and checks the whole package.
-/
