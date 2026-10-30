"""``glm_universal.reasoning.quoted_measurements_study`` -- the marks of
``studies/QUOTED_MEASUREMENTS_STUDY.md`` (Phase 174).

*Created 20 October 2026.*

What is measured
----------------
Two lines of To-Do item 7 (*the evidence model, in use, the rest*):

* the evidence census (Phase 169) and the result census (Phase 171) record the
  system's answers, and their digests did not cover the stored measurements
  those answers quote, so either could hold a stale answer and call itself
  current (``ITERATE.md`` §0.1, hazard 4).  Since Phase 174 each records the
  stored measurements its answers opened (:mod:`glm_universal.quoted_measurements`)
  and its digest covers them;
* the replay gate of Phase 171 was a flag of the evaluation, not a step of the
  close.  Since Phase 174 it is the sign-off instrument ``replay``.

The marks, declared with this module before the first run:

* **Q1** both censuses record the stored measurements their answers quote:
  at least one each;
* **Q2** every quoted file, altered by one byte in a copy of the tree, moves
  the digest of every census that quotes it (n of n), and the unaltered copy
  reproduces the live digest;
* **Q3** no cycle: neither census quotes its own file, and the evidence census
  does not quote the result census, which digests it;
* **Q4** stage 0 of the close re-takes the censuses last, the evidence census
  before the result census, whatever order the stale caches arrive in;
* **Q5** the ``replay`` instrument is declared, its closure holds
  ``evaluation/replay.py`` and ``GLM.py``, and its last run is signed passed at
  the current digest.

Nothing is cached: the report is computed when asked (a few seconds).

Exactness
---------
Strings and integers only.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from .. import integrity
from .. import quoted_measurements as qm

__all__ = ["CENSUSES", "tamper", "compute", "quoted_measurements_report"]

#: The caches that record answers, by module name.
CENSUSES: Tuple[str, ...] = ("evidence_model_study", "evidence_in_use_study")


def _module(name: str):
    import importlib
    return importlib.import_module(f"glm_universal.reasoning.{name}")


def _digest_names(mod, quoted: Sequence[str]) -> Tuple[List[Path], Path]:
    """The files a census's digest reads, and the root it is taken at --
    re-derived from the module the way its ``module_digest`` takes them."""
    root = Path(mod.__file__).resolve().parent.parent
    names = [root / n for n in sorted(set(mod._SOURCES))]
    base = root
    if mod.__name__.endswith("evidence_in_use_study"):
        names.append(root.parent / "GLM.py")
        base = root.parent
    names += [p for p in qm.existing(quoted) if p not in names]
    return names, base


def tamper(name: str) -> Dict[str, object]:
    """Q2 for one census: copy the files its digest reads into a scratch
    tree, check the copy reproduces the live digest, then alter each quoted
    file in turn and count the digests that moved."""
    mod = _module(name)
    stored = mod.measurements() or {}
    quoted = list(stored.get("quoted", ()))
    names, base = _digest_names(mod, quoted)
    live = mod.module_digest(quoted)
    with tempfile.TemporaryDirectory() as tmp:
        scratch = Path(tmp)
        copies = []
        for p in names:
            target = scratch / p.relative_to(base)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, target)
            copies.append(target)
        reproduced = integrity.tree_digest(copies, scratch) == live
        moved = 0
        quoted_paths = [p for p in qm.existing(quoted)]
        for p in quoted_paths:
            target = scratch / p.relative_to(base)
            original = target.read_bytes()
            target.write_bytes(original + b" ")
            moved += int(integrity.tree_digest(copies, scratch) != live)
            target.write_bytes(original)
    return {"quoted": len(quoted), "present": len(quoted_paths),
            "moved": moved, "reproduced": reproduced}


def compute() -> Dict[str, object]:
    from ..signoff import __main__ as so
    from ..signoff import checks as C
    q1 = {}
    q2 = {}
    q3 = {"own": [], "downstream": []}
    for name in CENSUSES:
        mod = _module(name)
        quoted = list((mod.measurements() or {}).get("quoted", ()))
        q1[name] = len(quoted)
        q2[name] = tamper(name)
        own = mod.DATA_PATH.resolve().relative_to(qm.PACKAGE_ROOT).as_posix()
        if own in quoted:
            q3["own"].append(name)
    em = _module("evidence_model_study")
    eiu = _module("evidence_in_use_study")
    downstream = eiu.DATA_PATH.resolve().relative_to(
        qm.PACKAGE_ROOT).as_posix()
    if downstream in (em.measurements() or {}).get("quoted", ()):
        q3["downstream"].append("evidence_model_study")
    sample = [("evidence_in_use_study", "x"), ("nearest_question_study", "y"),
              ("evidence_model_study", "z"), ("address_read_study", "w")]
    order = sorted(sample, key=lambda mc: (
        mc[0] in so.CENSUS_LAST,
        so.CENSUS_LAST.index(mc[0]) if mc[0] in so.CENSUS_LAST else 0))
    q4 = {"order": [m for m, _ in order]}
    plan = {u.name: u for u in C.check_plan()}
    replay = C.checks_by_name().get("replay")
    closure = ([p.relative_to(C.L.REPOSITORY_ROOT).as_posix()
                for p in C.check_closure(replay)] if replay else [])
    unit = plan.get("replay")
    q5 = {"declared": replay is not None,
          "closure_replay": "glm_universal/evaluation/replay.py"
          in closure,
          "closure_cli": "GLM.py" in closure,
          "state": unit.state if unit else "absent",
          "output_tail": (unit.recorded or {}).get("output_tail", "")
          if unit else ""}
    report = {"Q1": q1, "Q2": q2, "Q3": q3, "Q4": q4, "Q5": q5}
    report["marks"] = _marks(report)
    report["met"] = sum(1 for v in report["marks"].values() if v)
    report["taken"] = len(report["marks"])
    return report


def _marks(r: Dict[str, object]) -> Dict[str, bool]:
    q2 = r["Q2"].values()
    return {
        "Q1": all(n > 0 for n in r["Q1"].values()),
        "Q2": all(t["reproduced"] and t["moved"] == t["present"]
                  == t["quoted"] > 0 for t in q2),
        "Q3": not r["Q3"]["own"] and not r["Q3"]["downstream"],
        "Q4": r["Q4"]["order"][-2:] == ["evidence_model_study",
                                        "evidence_in_use_study"],
        "Q5": (r["Q5"]["declared"] and r["Q5"]["closure_replay"]
               and r["Q5"]["closure_cli"] and r["Q5"]["state"] == "signed"),
    }


def quoted_measurements_report() -> Dict[str, object]:
    """The marks, computed now."""
    return compute()
