"""``glm_universal.knowledge.friction_two`` -- worn contact and the noise-set
reader.

Phase 157's friction half (``studies/FRICTION_TWO_STUDY.md``), over Phase
156's held-out sample, hold-out model and readers
(:mod:`glm_universal.knowledge.friction`), which it imports and does not
modify:

* **worn contact** (§2.3) -- each content word in the touch set (prompt or
  produced) has a budget of 2: ``A(c)`` counts only words with budget left,
  and after a word ``c`` is chosen every word that counted in its ``A(c)``
  loses one.  Reported for the full contact score ``R(c)·(1 + A(c))`` (the
  marks) and for the loaded score ``R(c)·(8 + A(c))`` beside it
  (:func:`worn_contact_predict`, :func:`worn_continuation`);
* **the noise-set reader** (§2.4) -- it holds its reading and moves to the
  leader at a step only when ``8·S(leader) > (8 + r)·S(held)``, ``r`` the
  number of times the frictionless leader has changed so far in the sentence
  (:func:`noise_set_reader`; the curve reads 4 and 16 in place of 8).

``RequestProject/GLM/FrictionTwo.lean`` proves that the noise-set reader is a
keep-or-move reader, so it never switches more often than the leader for any
noise rule (``noise_switches_le``), and that wear bounds the pull
(``worn_touches_le``: at most ``b·|P|`` touches over a continuation).

Exact (D7): integer scores and integer comparisons only.

*Reconstructed 31 October 2026 (repository check): the original was lost in
the October 2026 reorganisation; rebuilt from studies/FRICTION_TWO_STUDY.md
§§2.3-2.4 and §§7.4-7.5, RequestProject/GLM/FrictionTwo.lean (``noisy``,
``used``) and glm_universal/knowledge/friction.py.*
"""
from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from . import friction as fr

__all__ = [
    "BUDGET", "NOISE_SCALE", "NOISE_CURVE", "worn_contact_predict",
    "worn_continuation", "noise_reader", "noise_set_reader",
]

#: Every touch-set word's budget (§2.3).
BUDGET = 2
#: The noise-set reader's scale for the marks, and the curve beside it.
NOISE_SCALE = 8
NOISE_CURVE: Tuple[int, ...] = (16, 8, 4)


def worn_contact_predict(model: fr.HeldOut, prefix: Sequence[str],
                         budget: int = BUDGET, used: Optional[Dict[str, int]] = None,
                         load: int = 1) -> Tuple[Optional[str], List[str]]:
    """The worn-contact choice at one step: over the deciding row's 32
    tallest, the unique maximum of ``R(c)·(load + A(c))`` where ``A(c)``
    counts only the prefix's content words that have budget left (``used``
    holds how often each has counted).  Returns the choice (``None`` on a
    tie) and the words that counted in its ``A`` -- the caller spends them."""
    used = {} if used is None else used
    cands = fr.tallest(model, prefix)
    if not cands:
        return None, []
    live = [w for w in fr.content_words(prefix) if used.get(w, 0) < budget]
    scored = []
    touched: Dict[str, List[str]] = {}
    for c, r in cands:
        t = fr.touches(model, c, live)
        touched[c] = t
        scored.append((fr.contact_score(r, len(t), load), c))
    choice = fr._unique_max(scored)
    return choice, (touched[choice] if choice is not None else [])


def _worn_chooser(budget: int, load: int):
    def choose(model: fr.HeldOut, history: List[str],
               state: Dict[str, Any]) -> Optional[str]:
        used = state.setdefault("used", {})
        choice, spent = worn_contact_predict(model, history, budget, used, load)
        if choice is not None:
            for w in spent:
                used[w] = used.get(w, 0) + 1
            state["touches"] = state.get("touches", 0) + len(spent)
        return choice
    choose._chooser = True  # type: ignore[attr-defined]
    return choose


def worn_continuation(model: fr.HeldOut, prompt: Sequence[str],
                      max_tokens: int = fr.MAX_TOKENS, budget: int = BUDGET,
                      load: int = 1) -> Dict[str, Any]:
    """Phase 156's continuation under worn contact: the same prompt, limit
    and stops; ``state["touches"]`` is the number of touches spent (at most
    ``budget`` times the touch set, ``worn_touches_le``)."""
    return fr.continuation(_worn_chooser(budget, load), model, prompt,
                           max_tokens)


def noise_reader(steps: Sequence[Tuple[Mapping[str, int], str]],
                 scale: int = NOISE_SCALE) -> List[str]:
    """The noise-set reader over given steps (FrictionTwo.lean's ``noisy``):
    it starts at the leader and moves to the leader at step ``t`` only when
    ``scale·S(leader) > (scale + r(t))·S(held)``, ``r(t)`` the number of
    changes of the leader up to and including step ``t``."""
    leaders = [lead for _s, lead in steps]
    changes = [0] * len(leaders)
    for t in range(1, len(leaders)):
        changes[t] = changes[t - 1] + (leaders[t] != leaders[t - 1])
    return fr.keep_or_move(steps, lambda t, held, lead:
                           scale * lead > (scale + changes[t]) * held)


def noise_set_reader(evidence: fr.FolderEvidence, sentence: Any,
                     base: int = NOISE_SCALE) -> List[str]:
    """The noise-set sticking reader of §2.4 over a sentence."""
    return noise_reader(fr.leaders(evidence, sentence)["steps"], base)
