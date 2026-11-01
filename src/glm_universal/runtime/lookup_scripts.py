"""``glm_universal.runtime.lookup_scripts`` -- column 3 for the four lookup
kinds (``sequence``, ``study``, ``tool``, ``corpus``).

*Created 31 October 2026 (repository check), beside the kinds themselves
(:mod:`glm_universal.runtime.reports.lookup`).  The bodies are registered in*
:data:`glm_universal.runtime.tct_engine.TEMPLATES` *and rendered between the
engine's header and footer like every other template: each binds*
``observed`` *and the footer compares it with column 2's* ``expected``.

What each script re-checks, and how independently:

``sequence``  an identification by a brute-force scan of every entry of a
              freshly built wheel -- exact matches first, then prefixes, the
              least id; else the earliest run after the first term, least id
              on a tie -- without calling ``speak`` or ``locate``; a next
              term by the same scan, every entry whose stored terms start
              with the claim, or hold it from their second term, collected
              and required to run past it and to agree on the term after it;
              a sporadic
              order by recomputing all 26 orders from their written prime
              factorisations and requiring exactly one to match.
``study``     the reply re-derived from the manifests on disk in the fresh
              interpreter, and every study it names checked to have a
              manifest ``studies/<ID>.yaml`` and a document
              ``studies/<ID>.md``.
``tool``      the tool run again in the fresh interpreter, its verdict and
              figures compared -- a reproduction, not a second derivation;
              each tool's correctness is pinned by its own tests.
``corpus``    the brute-force recheck of :mod:`glm_universal.knowledge.ask`
              (``recheck``), which recounts over the sentences without the
              model's index.

Exact: integers and strings only; no float, no randomness.

*Last altered 1 November 2026 (Phase 186: intake absorption -- the sequence
body re-checks the* ``next`` *reading: a brute-force scan of every entry of a
freshly built wheel, collecting each entry whose stored terms start with the
claim or hold it from their second stored term, requiring that each runs past
it and that all give one next term).*
"""
from __future__ import annotations

from typing import Callable, Dict, Mapping

__all__ = ["LOOKUP_TEMPLATES"]


def _body_sequence(args: Mapping[str, object]) -> str:
    request = str(args.get("request", ""))
    reading = str(args.get("reading", "sequence"))
    return f'''# -- recompute -------------------------------------------------------------

import re as _re

from glm_universal.wheels import sequence_query as _sq
from glm_universal.wheels.cfsg_seed import CFSG_GROUPS as _GROUPS
from glm_universal.wheels.monster_wheel import default_monster_wheel

_request = {request!r}
_reading = {reading!r}
_wheel = default_monster_wheel()
observed = {{}}

if _reading == "sequence":
    _claim = tuple(_sq.sequence_terms(_request))
    _n = len(_claim)
    _exact = sorted(_e.oeis_id for _e in _wheel.entries()
                    if tuple(_e.terms) == _claim)
    _prefix = sorted(_e.oeis_id for _e in _wheel.entries()
                     if len(_e.terms) > _n and tuple(_e.terms[:_n]) == _claim)
    if _exact or _prefix:
        _id, _pos = (_exact or _prefix)[0], 0
    else:
        _runs = []
        for _e in _wheel.entries():
            _t = tuple(_e.terms)
            for _k in range(1, len(_t) - _n + 1):
                if _t[_k:_k + _n] == _claim:
                    _runs.append((_k, _e.oeis_id))
                    break
        assert _runs, "no entry holds the claim as a run"
        _pos, _id = min(_runs)
    _t = tuple(_wheel.get(_id).terms)
    assert _t[_pos:_pos + _n] == _claim
    observed = {{"id": _id, "position": str(_pos),
                 "claim": ", ".join(str(_x) for _x in _claim)}}
elif _reading == "next":
    _claim = tuple(_sq.sequence_terms(_request))
    _n = len(_claim)
    assert _n >= 3, "a next term needs at least three terms"
    _after = {{}}
    _shifted = {{}}
    _stops = []
    for _e in _wheel.entries():
        _t = tuple(_e.terms)
        for _p, _into in ((0, _after), (1, _shifted)):
            if len(_t) >= _p + _n and _t[_p:_p + _n] == _claim:
                if len(_t) > _p + _n:
                    _into[_e.oeis_id] = _t[_p + _n]
                else:
                    _stops.append(_e.oeis_id)
    assert _after, "no entry starts with the claim and runs past it"
    assert not _stops, "entries stop at the claim: " + ",".join(sorted(_stops))
    _values = sorted(set(_after.values()) | set(_shifted.values()))
    assert len(_values) == 1, "the entries disagree on the next term"
    observed = {{"ids": ",".join(sorted(_after)), "next": str(_values[0]),
                 "claim": ", ".join(str(_x) for _x in _claim)}}
else:
    def _from_factorisation(_text):
        _value = 1
        for _part in _re.split(r"\\s*[\\u00b7*\\u00d7]\\s*", _text.strip()):
            _base, _, _exp = _part.partition("^")
            _value *= int(_base) ** (int(_exp) if _exp else 1)
        return _value

    _orders = {{}}
    for _g in _GROUPS:
        _gid, _order, _fact = _g[0], int(_g[2]), str(_g[3])
        assert _from_factorisation(_fact) == _order, _gid
        _orders[_gid] = _order
    assert len(set(_orders.values())) == len(_orders) == 26
    if _reading == "order":
        _m = _sq._ORDER_VALUE.search(_request)
        _target = _sq.parse_order(_m.group("expr"))
        _hits = sorted(_gid for _gid, _o in _orders.items() if _o == _target)
        assert len(_hits) == 1, _hits
        observed = {{"group": _hits[0], "order": str(_target)}}
    else:
        _phrase = _request[_sq._ORDER_OF.search(_request).end():]
        _gid, _unknown = _sq.group_named(
            _phrase, bool(_sq._SPORADIC.search(_request)))
        assert _gid in _orders, (_gid, _unknown)
        observed = {{"group": _gid, "order": str(_orders[_gid])}}
'''


def _body_study(args: Mapping[str, object]) -> str:
    request = str(args.get("request", ""))
    return f'''# -- recompute -------------------------------------------------------------

import re as _re

from glm_universal.constants import STUDIES_DIR as _STUDIES
from glm_universal.corpus import study_index as _si

_index = _si.study_index()
_code, _reply = _si.answer_study_query({request!r}, _index)
_known = set(_index.ids)
_named = []
for _token in _re.findall(r"(?<![A-Za-z0-9_])[A-Z][A-Z0-9_]*[A-Z0-9]"
                          r"(?![A-Za-z0-9_])", _reply):
    if _token in _known and _token not in _named:
        _named.append(_token)
for _sid in _named:
    assert (_STUDIES / (_sid + ".yaml")).is_file(), _sid + ": no manifest"
    assert (_STUDIES / (_sid + ".md")).is_file(), _sid + ": no document"

observed = {{"code": str(_code), "named": ",".join(_named),
             "lines": str(len(_reply.splitlines()))}}
'''


def _body_tool(args: Mapping[str, object]) -> str:
    request = str(args.get("request", ""))
    return f'''# -- recompute -------------------------------------------------------------

from glm_universal.runtime import toolbox as _tb

_got = _tb.run_tool({request!r})
observed = {{"ok": str(_got.ok)}}
for _key, _value in sorted(dict(_got.figures).items()):
    observed["figure:" + str(_key)] = str(_value)
'''


def _body_corpus(args: Mapping[str, object]) -> str:
    request = str(args.get("request", ""))
    return f'''# -- recompute -------------------------------------------------------------

from glm_universal.knowledge import ask as _ka

observed = {{str(_k): str(_v)
             for _k, _v in dict(_ka.recheck({request!r})).items()}}
'''


#: The four bodies, by template name.
LOOKUP_TEMPLATES: Dict[str, Callable[[Mapping[str, object]], str]] = {
    "sequence": _body_sequence,
    "study": _body_study,
    "tool": _body_tool,
    "corpus": _body_corpus,
}
