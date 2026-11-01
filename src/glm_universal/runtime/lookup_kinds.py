"""``glm_universal.runtime.lookup_kinds`` -- which text the four lookup kinds
claim: ``tool``, ``corpus``, ``study`` and ``sequence``.

*Created 31 October 2026 (repository check).  The parser's* :data:`KINDS`
*did not list* ``corpus`` *(Phase 154) or* ``tool`` *(the evaluation's
kind for* ``tool-leech-norm-12`` *since Phase 164), although the evaluation
set covers both and* ``test_evaluation`` *requires the two lists to agree;
and the owner asked (31 October 2026) for the* ``study`` *kind -- ENTRY.md
already says the GLM answers it from the study manifests -- and for a*
``sequence`` *kind over the absorbed Integer and Monster Wheels.  This module
holds the one rule for what each of them reads; the parser
(:func:`glm_universal.runtime.parser.parse_query`, rule 0) and the router
(:func:`glm_universal.runtime.router.reader_of`) both ask it, so the two can
never disagree about a text.*

Each kind is a *lookup*: its answer is read off data the repository holds --
the toolbox, the corpus, the study manifests (``studies/*.yaml``), the
wheels -- and its column 3 re-checks the reading in a fresh interpreter.  A
lookup kind claims a text only by a narrow, declared form, because it is
consulted before every other rule:

``tool``      text the toolbox reads (``tool <name> ...`` or ``tools``):
              :func:`reads_tool` (the toolbox's rule, held here);
``corpus``    text that opens with the word ``corpus`` (start-only, as in
              Phase 154; the request after it is passed whole, as Phase 155
              says -- a leading *address* is not stripped as a weak opener);
``study``     text that opens with ``study`` or ``studies``, uses the word
              ``studies`` anywhere, or names a study id (an upper-case token
              ending ``_STUDY``, e.g. ``FOLD_MACHINE_STUDY``) -- answered by
              :func:`glm_universal.corpus.study_index.answer_study_query`;
``sequence``  a sequence or sporadic-order question as
              :func:`glm_universal.wheels.sequence_query.resolve_query`
              decides it (code 0 or 1; code 2, *not mine*, is left alone, so
              *what is the order of operations* falls through).

A text that opens with the word ``report`` is never claimed by ``study`` or
``sequence``: the report kind owns its subjects, and some of their aliases use
the word *studies* (``report external studies``, ``report companion
studies``).

*Last altered 31 October 2026 (repository check): the tool rule held here
rather than imported from the toolbox (the session's import closure); the*
``report`` *exclusion
added, after the full test run found* ``report external studies`` *and*
``report companion studies`` *claimed as* ``study`` *(test_catalog,
test_companion); the report kind answers them again.*

``tests/test_lookup_kinds.py`` runs every question of the evaluation set and
every declared text of the router's census through :func:`claimed_kind` and
requires that none is claimed: adding these kinds moves no existing answer.

Exact and deterministic: regular expressions over the text and, for the
sequence kind, one wheel built once per process (no network).
"""
from __future__ import annotations

import re
from functools import lru_cache
from typing import Optional, Tuple

__all__ = ["LOOKUP_KINDS", "claimed_kind", "reads_tool", "reads_corpus",
           "reads_study", "reads_sequence", "sequence_wheel", "STUDY_ID"]

#: The four kinds, in the order :func:`claimed_kind` tries them.
LOOKUP_KINDS: Tuple[str, ...] = ("tool", "corpus", "study", "sequence")

#: A study id as the manifests write it: upper case, ending ``_STUDY``.
STUDY_ID = re.compile(r"(?<![A-Za-z0-9_])[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*_STUDY"
                      r"(?![A-Za-z0-9_])")

_OPENS_STUDY = re.compile(r"^(?:study|studies)(?:\s|$)", re.I)
_SAYS_STUDIES = re.compile(r"\bstudies\b", re.I)
_OPENS_CORPUS = re.compile(r"^corpus(?:\s|$)", re.I)
_OPENS_REPORT = re.compile(r"^report(?:\s|$)", re.I)


def _plain(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def reads_tool(text: str) -> bool:
    """Whether the toolbox reads ``text``: ``tools``, ``tool`` or text that
    opens ``tool `` (case-insensitive).

    The rule lives here and :func:`glm_universal.runtime.toolbox.reads_tool`
    is this function (31 October 2026, repository check): asking the toolbox
    module put it -- and through it the Lean address book's walk of the
    whole development -- into the import closure of every session, which
    ``tests/test_signoff.py`` (*building a session does not take the whole
    development*) forbids.
    """
    t = (text or "").strip().lower()
    return t == "tools" or t.startswith("tool ") or t == "tool"


def reads_corpus(text: str) -> bool:
    """Whether ``text`` opens with the word ``corpus``."""
    return bool(_OPENS_CORPUS.match(_plain(text)))


def reads_study(text: str) -> bool:
    """Whether ``text`` is a question about the studies (see the module
    docstring for the three forms)."""
    t = _plain(text)
    if not t or _OPENS_REPORT.match(t):
        return False
    return bool(_OPENS_STUDY.match(t) or _SAYS_STUDIES.search(t)
                or STUDY_ID.search(t))


@lru_cache(maxsize=1)
def sequence_wheel():
    """The absorbed Monster Wheel, built once per process (the audited
    Integer Wheel's entries, the 26 sporadic groups, their exponent vectors
    and the sorted orders); never touches the network."""
    from ..wheels.monster_wheel import default_monster_wheel
    return default_monster_wheel()


def reads_sequence(text: str) -> bool:
    """Whether ``text`` is a sequence or sporadic-order question: what
    :func:`~glm_universal.wheels.sequence_query.resolve_query` does not
    call *not mine* (code 2)."""
    t = _plain(text)
    if not t or _OPENS_REPORT.match(t):
        return False
    from ..wheels import sequence_query as sq
    return sq.resolve_query(t, wheel=sequence_wheel()).code != sq.NOT_MINE


def claimed_kind(text: str) -> Optional[str]:
    """The lookup kind that claims ``text``, or ``None``.  Tried in the
    order of :data:`LOOKUP_KINDS`; the first that reads the text claims
    it."""
    if not text or not text.strip():
        return None
    if reads_tool(text):
        return "tool"
    if reads_corpus(text):
        return "corpus"
    if reads_study(text):
        return "study"
    if reads_sequence(text):
        return "sequence"
    return None
