"""``glm_universal.engineering.context_frames`` -- contextual domain frames:
the question says which energy, which oscillator, and which body drives the
wave.

Phase 170 (``studies/CONTEXT_FRAMES_STUDY.md`` §1).  A question may end
*across domains where* followed by one or more declared context phrases
(joined by *and* or a comma).  Six contexts are declared (:data:`CONTEXTS`),
each with its phrasing and its reason:

=========================  =====================================  ==========================
context                    phrasing                               what it does
=========================  =====================================  ==========================
energy-delivered           the energy is delivered over a time    pins ``energy`` to W15
energy-stored-capacitor    the energy is stored in a capacitor    pins ``energy`` to W3
energy-stored-inductor     the energy is stored in an inductor    pins ``energy`` to W14
oscillator-spring          the oscillator is a mass on a spring   pins ``angular_frequency`` to W13
oscillator-lc              the oscillator is an lc circuit        pins ``angular_frequency`` to W14
rotating-drive             a rotating body drives the wave        joins ``angle`` across W9/W13
=========================  =====================================  ==========================

A **pin** keeps only the copies of the named quantity whose junction class
holds the named wheel; a **join** adds one junction to the union for this
question only.  The fifteen-wheel union is never modified, and a question
without a ``where`` clause is answered by
:func:`glm_universal.engineering.domains.derive_domains` as before.  The rule
that decides is the domains frame's: every remaining copy is tried, and the
answer is given only when every derivation found agrees.

The declared refusals (§1): a phrase that is not declared is refused, never
guessed; a pin on a quantity the question does not ask about is refused; two
pins that say different things about one quantity are refused; a frame in
which no derivation remains is refused.

*Reconstructed 31 October 2026 (repository check): the original was lost in
the October 2026 reorganisation; rebuilt from studies/CONTEXT_FRAMES_STUDY.md
(§§1, 4, 7), MASTER_PLAN.md Phase 170 and the domains frame of
engineering/domains.py (``derive_domains``'s ``pins`` and ``junctions``
parameters), which it reads and does not modify.*
"""
from __future__ import annotations

import dataclasses
import re
from dataclasses import dataclass
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from ..wheels import ALIASES
from . import domains as dmn

__all__ = ["Context", "CONTEXTS", "PHRASES", "ContextRefusal", "read_where",
           "frame_of", "derive_in_context"]


@dataclass(frozen=True)
class Context:
    """One declared context: its phrasings, the pin or the join it makes,
    and why."""

    key: str
    phrases: Tuple[str, ...]
    reason: str
    pin: Optional[Tuple[str, str]] = None          # (quantity, wheel)
    join: Optional[Tuple[Tuple[str, str], Tuple[str, ...]]] = None

    def says(self) -> str:
        if self.pin is not None:
            return f"{self.pin[0]} pinned to {self.pin[1]}"
        (a, b), names = self.join
        return f"{', '.join(names)} joined across {a}/{b} for this question"


#: The six declared contexts (§1), keyed by name.
CONTEXTS: Dict[str, Context] = {c.key: c for c in (
    Context("energy-delivered", ("the energy is delivered over a time",),
            "the energy meant is the energy delivered over a time (W15), "
            "not a stored energy", pin=("energy", "W15")),
    Context("energy-stored-capacitor", ("the energy is stored in a capacitor",),
            "the energy meant is the capacitor's stored energy (W3)",
            pin=("energy", "W3")),
    Context("energy-stored-inductor", ("the energy is stored in an inductor",),
            "the energy meant is the inductor's stored energy (W14)",
            pin=("energy", "W14")),
    Context("oscillator-spring", ("the oscillator is a mass on a spring",),
            "the oscillator meant is the mass-spring oscillator (W13)",
            pin=("angular_frequency", "W13")),
    Context("oscillator-lc", ("the oscillator is an lc circuit",),
            "the oscillator meant is the LC circuit (W14)",
            pin=("angular_frequency", "W14")),
    Context("rotating-drive", ("a rotating body drives the wave",),
            "the wave's source is a rotating body, so the oscillator's turn is "
            "the wave's turn for this question",
            join=(("W9", "W13"), ("angle",))),
)}

#: phrase -> context key.
PHRASES: Dict[str, str] = {p: c.key for c in CONTEXTS.values() for p in c.phrases}


class ContextRefusal(ValueError):
    """A ``where`` clause the frame declines, with the reason."""


def _norm(phrase: str) -> str:
    return re.sub(r"\s+", " ", phrase.strip().lower().rstrip("?.!; "))


def read_where(where: str) -> List[Context]:
    """The declared contexts a ``where`` clause names (phrases joined by
    *and* or a comma); :class:`ContextRefusal` on a phrase not declared."""
    parts = [p for p in re.split(r"\s*,\s*(?:and\s+)?|\s+and\s+", _norm(where))
             if p.strip()]
    if not parts:
        raise ContextRefusal("the where clause names no context")
    out: List[Context] = []
    for p in parts:
        key = PHRASES.get(_norm(p))
        if key is None:
            raise ContextRefusal(
                f"the context '{p}' is not declared (declared: "
                + "; ".join(sorted(PHRASES)) + ")")
        if CONTEXTS[key] not in out:
            out.append(CONTEXTS[key])
    return out


def frame_of(contexts: Sequence[Context], target: str, inputs: Sequence[str],
             junctions: Optional[Mapping[Tuple[str, str], Sequence[str]]] = None
             ) -> Tuple[Dict[str, str], Dict[Tuple[str, str], Tuple[str, ...]]]:
    """``(pins, junction table)`` of a frame for the asked names: the pins
    the contexts make and the union's table with the contexts' joins added.
    :class:`ContextRefusal` when a pin names a quantity not asked, or two
    pins disagree about one quantity."""
    asked = {ALIASES.get(n, n) for n in (target, *inputs)}
    pins: Dict[str, str] = {}
    for c in contexts:
        if c.pin is None:
            continue
        name, wheel = c.pin
        if name not in asked:
            raise ContextRefusal(
                f"the context '{c.phrases[0]}' is about {name}, which the "
                f"question does not ask about")
        if name in pins and pins[name] != wheel:
            other = next(o for o in contexts if o.pin == (name, pins[name]))
            raise ContextRefusal(
                f"the contexts '{other.phrases[0]}' and '{c.phrases[0]}' say "
                f"different things about {name}")
        pins[name] = wheel
    table = dict(dmn.union_junctions() if junctions is None else junctions)
    table = {k: tuple(v) for k, v in table.items()}
    for c in contexts:
        if c.join is None:
            continue
        pair, names = c.join
        table[pair] = tuple(dict.fromkeys(table.get(pair, ()) + tuple(names)))
    return pins, table


def _refused(target: str, inputs: Sequence[str], reason: str) -> dmn.DomainAnswer:
    return dmn.DomainAnswer(False, target=ALIASES.get(target, target),
                            inputs=tuple(ALIASES.get(y, y) for y in inputs),
                            formula=None, wheels=(), junctions=(),
                            reason=reason)


def derive_in_context(target: str, inputs: Sequence[str], where: str,
                      junctions: Optional[Mapping[Tuple[str, str], Sequence[str]]] = None
                      ) -> dmn.DomainAnswer:
    """Answer *derive target from inputs across domains where <context>*
    in the frame the context declares (``junctions``: the union's table to
    start from, default the shipped one), or refuse with the reason."""
    try:
        contexts = read_where(where)
        pins, table = frame_of(contexts, target, inputs, junctions)
    except ContextRefusal as exc:
        return _refused(target, inputs, str(exc))
    said = "; ".join(f"in the frame '{c.phrases[0]}' ({c.says()})"
                     for c in contexts)
    ans = dmn.derive_domains(target, inputs, table, pins=pins or None)
    if not ans.answered and pins and not ans.found \
            and not ans.reason.startswith("no declared wheel names") \
            and not ans.reason.startswith("a name is asked twice"):
        ans = dataclasses.replace(
            ans, naive=None,
            reason=f"no derivation remains in this frame: no union of the "
                   f"declared wheels derives {ans.target} from "
                   f"{' and '.join(ans.inputs)} with "
                   + ", ".join(f"{n} pinned to {w}" for n, w in pins.items()))
    return dataclasses.replace(ans, aliases=ans.aliases + (said,))
