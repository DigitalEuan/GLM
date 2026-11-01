"""``glm_universal.knowledge.thermo_friction`` -- the bimetallic governor (A)
and the thermoelectric prompt anchor (B).

Phase 159 (``studies/THERMO_FRICTION_STUDY.md``), over Phase 156's held-out
sample, hold-out model, continuation and directory evidence
(:mod:`glm_universal.knowledge.friction`), imported and not modified.  The
third experiment, the sintered respelling (C), lives in
:mod:`glm_universal.runtime.sinter`.

**A -- the governor** (§2.1).  At each step the deciding row's 32 tallest
continuations ``R₁ ≥ R₂ ≥ …`` are its candidates.  The row is **hot** when
``2·R₁ ≥ R₁ + … + R₅`` (the top candidate holds at least half of the five
tallest, or of those there are), **cold** otherwise; the heat level ``h`` is
the number of hot rows met so far, this one included.  A candidate ``c``
**repeats** when the bigram ``(b, c)``, ``b`` the last token of the history
(prompt and produced words, no padding), already occurs as two adjacent
tokens of the history's last 8 tokens.  The governor scores ``R(c)`` at a
cold row or for a candidate that does not repeat, and ``R(c) / (1 + h)``
(exact rationals) for a repeating candidate at a hot row; the unique maximum
answers, a tie refuses.  The static taboo (the control) scores every
repeating candidate ``R(c) / 2``, hot or cold; the contact governor applies
the governor's penalty to the contact score ``R(c)·(1 + A(c))``.

**B -- the anchor** (§2.2).  On the directory reader, the prompt words of a
sentence are its first 3 distinct content words, every later content word a
generated word; ``P(f)`` and ``G(f)`` are the scores the two sides give, the
frictionless score ``S = P + G``.  At a step the prompt leader ``p`` and the
generated leader ``g`` (first by name on a tie; each only where its score is
positive somewhere) give the gradient ``Γ = (P(p) − P(g)) + (G(g) − G(p))``
when both exist and differ (else 0); the step is **hot** when ``Γ > 0`` and
``4·Γ ≥ S(ℓ)``, ``ℓ`` the frictionless leader.  The anchor reader reads the
frictionless leader at a cold step and the largest ``2·P + G`` at a hot one;
the mismatched anchor reads the largest ``P' + P + G`` at the same hot steps,
``P'`` the score of another sentence's prompt words.

``RequestProject/GLM/ThermoFriction.lean`` (named by the study, §5) is to
prove that the governor rests when cold, keeps an unrepeated leader, that the
anchor is inactive when the two sides agree, and that sintering keeps the
solid reading.

Exact (D7): integer counts and :class:`fractions.Fraction` scores only.

*Reconstructed 31 October 2026 (repository check): the original was lost in
the October 2026 reorganisation; rebuilt from studies/THERMO_FRICTION_STUDY.md
§§1-2, 5 and 7, the CLI handler ``_thermo_friction`` in
glm_universal/tools.py and glm_universal/knowledge/friction.py.*
"""
from __future__ import annotations

from fractions import Fraction
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple

from . import friction as fr
from . import model as mdl

__all__ = [
    "RECENT", "HEAT_TOP", "PROMPT_WORDS", "is_hot", "repeats",
    "governor_scores", "governor_choice", "governor_chooser",
    "static_chooser", "contact_governor_chooser", "patch_chooser",
    "governed_continuation", "governed_positions",
    "split_scores", "anchor_steps", "anchor_readers",
]

#: The recent window of the history, in tokens.
RECENT = 8
#: The heat reads the top count against this many tallest counts.
HEAT_TOP = 5
#: The prompt side of the anchor: the first three distinct content words.
PROMPT_WORDS = 3


# ===========================================================================
# A.  THE BIMETALLIC GOVERNOR
# ===========================================================================

def is_hot(counts: Sequence[int]) -> bool:
    """``2·R₁ ≥ R₁ + … + R₅`` over the counts (most frequent first)."""
    top = list(counts[:HEAT_TOP])
    return bool(top) and 2 * top[0] >= sum(top)


def repeats(history: Sequence[str], candidate: str,
            recent: int = RECENT) -> bool:
    """Whether ``(last token, candidate)`` already occurs as two adjacent
    tokens of the history's last ``recent`` tokens."""
    if not history:
        return False
    window = list(history[-recent:])
    b = history[-1]
    return any(window[i] == b and window[i + 1] == candidate
               for i in range(len(window) - 1))


def governor_scores(base: Sequence[Tuple[str, Any]], history: Sequence[str],
                    hot: bool, heat: int, static: bool = False
                    ) -> List[Tuple[Fraction, str]]:
    """The penalised scores over ``(candidate, base score)``: at a hot row a
    repeating candidate scores ``base / (1 + heat)`` (``static``: every
    repeating candidate ``base / 2``, hot or cold); every other score is the
    base score."""
    out = []
    for c, s in base:
        s = Fraction(s)
        if repeats(history, c):
            if static:
                s = s / 2
            elif hot:
                s = s / (1 + heat)
        out.append((s, c))
    return out


def governor_choice(model: fr.HeldOut, history: Sequence[str],
                    state: Dict[str, Any], static: bool = False,
                    contact: bool = False) -> Optional[str]:
    """One step of the governor (or the static taboo, or the contact
    governor) over the deciding row's 32 tallest; ``state`` carries the heat
    level and the row tally (``hot``, ``cold``, ``cold_disagree`` against the
    patch, ``hot_repeating``, ``moved``)."""
    cands = fr.tallest(model, history)
    if not cands:
        return None
    hot = is_hot([r for _c, r in cands])
    if hot:
        state["heat"] = state.get("heat", 0) + 1
    heat = state.get("heat", 0)
    if contact:
        ws = fr.content_words(history)
        base = [(c, fr.contact_score(r, len(fr.touches(model, c, ws))))
                for c, r in cands]
    else:
        base = list(cands)
    choice = fr._unique_max(governor_scores(base, history, hot, heat, static))
    plain = fr._unique_max([(Fraction(s), c) for c, s in base])
    state["hot" if hot else "cold"] = state.get("hot" if hot else "cold", 0) + 1
    if not hot and choice != plain:
        state["cold_disagree"] = state.get("cold_disagree", 0) + 1
    if any(repeats(history, c) for c, _s in base):
        key = "hot_repeating" if hot else "cold_repeating"
        state[key] = state.get(key, 0) + 1
    if choice != plain:
        state["moved"] = state.get("moved", 0) + 1
    return choice


def _chooser(static: bool = False, contact: bool = False):
    def choose(model: fr.HeldOut, history: List[str],
               state: Dict[str, Any]) -> Optional[str]:
        return governor_choice(model, history, state, static, contact)
    choose._chooser = True  # type: ignore[attr-defined]
    return choose


def governor_chooser():
    """The governor as a continuation chooser (state: the heat level)."""
    return _chooser()


def static_chooser():
    """The static taboo (the control)."""
    return _chooser(static=True)


def contact_governor_chooser():
    """The governor's penalty over the contact score (reported beside)."""
    return _chooser(contact=True)


def patch_chooser():
    """The patch predictor as a chooser (the comparison's base)."""
    def choose(model, history, state):
        return fr.patch_predict(model, history)
    choose._chooser = True  # type: ignore[attr-defined]
    return choose


def governed_continuation(model: fr.HeldOut, prompt: Sequence[str],
                          chooser=None) -> Dict[str, Any]:
    """Phase 156's continuation under a governor chooser (default: the
    governor); the state's tallies say how many rows were hot and cold."""
    return fr.continuation(chooser or governor_chooser(), model, prompt)


def governed_positions(model: fr.HeldOut, sentence: Sequence[str],
                       chooser=None) -> Dict[str, Any]:
    """Every position of a held-out sentence under a governor chooser, the
    history being the sentence's own tokens (one heat level over the
    sentence)."""
    return fr.predict_positions(chooser or governor_chooser(), model, sentence)


# ===========================================================================
# B.  THE THERMOELECTRIC PROMPT ANCHOR
# ===========================================================================

def _leader_of(scores: Mapping[str, Any]) -> Optional[str]:
    """The largest positive score, the first by name on a tie."""
    return fr._leader(scores)


def split_scores(evidence: fr.FolderEvidence, sentence: Any,
                 prompt_words: int = PROMPT_WORDS
                 ) -> Tuple[List[Tuple[Dict[str, int], Dict[str, int]]], List[str]]:
    """``(P, G)`` after every token (from the first with a positive ``S``),
    and the prompt words: a content word read for the first time adds its
    height to every directory holding it, to ``P`` if it is among the first
    ``prompt_words`` distinct content words, to ``G`` otherwise."""
    P: Dict[str, int] = {}
    G: Dict[str, int] = {}
    seen: Set[str] = set()
    prompt: List[str] = []
    steps: List[Tuple[Dict[str, int], Dict[str, int]]] = []
    for tok in sentence.tokens:
        if mdl.is_content(tok) and tok not in seen:
            seen.add(tok)
            side = P if len(prompt) < prompt_words else G
            if side is P:
                prompt.append(tok)
            h, holding = evidence.height(tok, sentence)
            if h:
                for f in holding:
                    side[f] = side.get(f, 0) + h
        if any(v > 0 for v in P.values()) or any(v > 0 for v in G.values()):
            steps.append((dict(P), dict(G)))
    return steps, prompt


def prompt_scores(evidence: fr.FolderEvidence, words: Sequence[str],
                  sentence: Any) -> Dict[str, int]:
    """``P'``: the scores another sentence's prompt words give, read with the
    held-out sentence not counted."""
    out: Dict[str, int] = {}
    for w in words:
        h, holding = evidence.height(w, sentence)
        if h:
            for f in holding:
                out[f] = out.get(f, 0) + h
    return out


def _add(*maps: Mapping[str, int], weights: Sequence[int] = ()) -> Dict[str, int]:
    weights = list(weights) or [1] * len(maps)
    out: Dict[str, int] = {}
    for w, m in zip(weights, maps):
        for f, v in m.items():
            out[f] = out.get(f, 0) + w * v
    return out


def anchor_steps(evidence: fr.FolderEvidence, sentence: Any,
                 others: Mapping[str, Sequence[str]] = ()
                 ) -> Dict[str, Any]:
    """The anchor's reading of a sentence: per step the frictionless scores
    and leader, the gradient, whether the step is hot, the anchor's reading
    and each mismatched anchor's (``others`` maps a control's name to the
    prompt words it reads ``P'`` from)."""
    split, prompt = split_scores(evidence, sentence)
    extra = {name: prompt_scores(evidence, words, sentence)
             for name, words in dict(others).items()}
    steps = []
    for P, G in split:
        S = _add(P, G)
        lead = _leader_of(S)
        p, g = _leader_of(P), _leader_of(G)
        gamma = 0
        if p is not None and g is not None and p != g:
            gamma = (P.get(p, 0) - P.get(g, 0)) + (G.get(g, 0) - G.get(p, 0))
        hot = gamma > 0 and 4 * gamma >= S.get(lead, 0)
        anchor = _leader_of(_add(P, G, weights=(2, 1))) if hot else lead
        controls = {name: (_leader_of(_add(Px, P, G)) if hot else lead)
                    for name, Px in extra.items()}
        steps.append({"scores": S, "leader": lead, "prompt_leader": p,
                      "generated_leader": g, "gamma": gamma, "hot": hot,
                      "anchor": anchor, "controls": controls,
                      "agree": p is not None and p == g})
    return {"truth": evidence.folder(sentence), "prompt": prompt,
            "steps": steps}


def anchor_readers(evidence: fr.FolderEvidence, sentence: Any,
                   others: Mapping[str, Sequence[str]] = ()
                   ) -> Dict[str, Any]:
    """Every reader of §2.2's comparison over one sentence: the frictionless
    reader, the fixed quarter (Phase 156), the noise-set ``r/8`` (Phase 157),
    the anchor and each mismatched anchor; with the hot and cold step counts
    and the B5 check (a cold step reading other than the leader, an agreeing
    step that is hot)."""
    from . import friction_two as f2
    got = anchor_steps(evidence, sentence, others)
    st = got["steps"]
    plain = [(s["scores"], s["leader"]) for s in st]
    readings = {
        "frictionless": [s["leader"] for s in st],
        "stick 1/4": fr.margin_reader(plain, Fraction(1, 4)),
        "noise r/8": f2.noise_reader(plain, f2.NOISE_SCALE),
        "anchor": [s["anchor"] for s in st],
    }
    for name in dict(others):
        readings[name] = [s["controls"][name] for s in st]
    return {
        "truth": got["truth"], "readings": readings,
        "hot_steps": sum(1 for s in st if s["hot"]),
        "steps": len(st),
        "cold_off_leader": sum(1 for s in st if not s["hot"]
                               and s["anchor"] != s["leader"]),
        "agree_hot": sum(1 for s in st if s["agree"] and s["hot"]),
        "last_hot": bool(st) and st[-1]["hot"],
        "last": ({"prompt": st[-1]["prompt_leader"],
                  "generated": st[-1]["generated_leader"],
                  "leader": st[-1]["leader"]} if st else None),
    }
