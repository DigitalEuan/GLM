"""The surface language, driven off descriptions.

:mod:`glm_universal.recipe` made a *domain* declarative: a description yields
the carriers, the readings, the widening audit, the query surface and the
refusal boundary, with no code of its own.  This sub-package does the same
for the *question*.  A question shape -- an opening, named slots, the words
that separate them, and the boundaries it refuses at -- is an object, and one
generic matcher serves every described shape.

``glm_universal.language.question``
    :class:`~glm_universal.language.question.QuestionSpec` and the pieces a
    shape is written in, with the decisions about English marked as
    judgements so they are counted rather than hidden.
``glm_universal.language.descriptions``
    Seven of the runtime's query kinds written down: ``derive``,
    ``measure``, ``task`` and the list form of ``compare`` as slot shapes;
    ``verify``, ``analogy`` and the relational form of ``compare`` as infix
    shapes; and ``comparative`` as a nested shape -- with the reason the
    remaining kinds are none of the three.
``glm_universal.language.infix``
    The second shape family and its matcher: an operator that cuts a string,
    for questions whose operands are notations rather than runs of words,
    with the modifiers and trailing options a shape may hold beside them.
``glm_universal.language.nested``
    The third family: an operator whose operands are not text but *matches*
    of another described shape, tightened where nesting requires it.
``glm_universal.language.build``
    The generic matcher, the generated corpora, and the measurement: the
    described shapes against the deleted branches, question by question,
    with the one declared widening audited rather than hidden.
``glm_universal.language.legacy``
    The seven hand-written branches as they were on the day they were
    deleted from the parser, kept so that the measurement still has
    something to measure against.  Nothing in the runtime imports it.
``glm_universal.language.report``
    The measured result, and :func:`~glm_universal.language.report.ask`, a
    query surface that reads a question with no hand-written phrase in the
    path.

``RequestProject/GLM/Question.lean`` proves the part of the matching that is
not a measurement: that matching a written question returns the slots it was
written from, that a shape whose opening is absent refuses, that a match
never leaves a required slot empty, that two shapes with different openings
cannot both match -- which is what makes the order the shapes are tried in
irrelevant -- and, for the preamble, that skipping a described leading
remainder changes nothing about what is then matched while an undescribed
one is still refused.
"""

from __future__ import annotations

from .question import (Phrasing, Preamble, PreamblePiece, QuestionSpec,
                       Refusal, ROLES, Slot, describe_specs, phrasing,
                       preamble_piece, slot, tokenise)
from .infix import (InfixDecline, InfixMatch, InfixOutcome, InfixSpec,
                    Modifier, TrailingOption, describe_infix, match_infix,
                    parse_infix)
from .nested import (DegreeOperator, NestedDecline, NestedMatch,
                     NestedOutcome, NestedSide, NestedSpec, match_nested)
from .descriptions import (ANALOGY_QUESTION, COMPARATIVE_QUESTION,
                           COMPARE_LIST_QUESTION, COMPARE_QUESTION,
                           COURTESY_PREAMBLE, DERIVE_QUESTION,
                           DESCRIBED_KINDS, INFIX_KINDS, INFIX_QUESTIONS,
                           MEASURE_QUESTION, NESTED_KINDS, NESTED_QUESTIONS,
                           QUESTIONS, STANDARD_PREAMBLE,
                           TASK_QUESTION, VERIFY_QUESTION, described_kinds,
                           infix_by_kind, nested_by_kind, question_by_kind)
from .build import (ARTICLES, Decline, Match, Outcome, agreement, corpus,
                    coverage, decorations, describe, infix_agreement,
                    infix_corpus, match, narrowing, nested_agreement,
                    nested_corpus, openings_disjoint, options_of, parse,
                    refusal_audit, render, round_trip, undescribed_parts,
                    widening)
from .legacy import legacy_parse, legacy_parse_shaped
from .report import (ask, described_share, infix_surface, language_report,
                     nested_surface)

__all__ = [
    "Phrasing", "Preamble", "PreamblePiece", "QuestionSpec", "Refusal",
    "ROLES", "Slot", "describe_specs", "phrasing", "preamble_piece",
    "slot", "tokenise",
    "InfixDecline", "InfixMatch", "InfixOutcome", "InfixSpec",
    "Modifier", "TrailingOption",
    "describe_infix", "match_infix", "parse_infix",
    "DegreeOperator", "NestedDecline", "NestedMatch", "NestedOutcome",
    "NestedSide", "NestedSpec", "match_nested",
    "ANALOGY_QUESTION", "COMPARATIVE_QUESTION", "COMPARE_LIST_QUESTION",
    "COMPARE_QUESTION", "COURTESY_PREAMBLE",
    "DERIVE_QUESTION", "DESCRIBED_KINDS", "INFIX_KINDS", "INFIX_QUESTIONS",
    "MEASURE_QUESTION", "NESTED_KINDS", "NESTED_QUESTIONS",
    "QUESTIONS", "STANDARD_PREAMBLE", "TASK_QUESTION",
    "VERIFY_QUESTION", "described_kinds", "infix_by_kind",
    "nested_by_kind", "question_by_kind",
    "ARTICLES", "Decline", "Match", "Outcome", "agreement", "corpus",
    "coverage", "decorations", "describe", "infix_agreement",
    "infix_corpus", "match", "narrowing", "nested_agreement",
    "nested_corpus", "openings_disjoint", "options_of", "parse",
    "refusal_audit", "render", "round_trip", "undescribed_parts",
    "widening",
    "legacy_parse", "legacy_parse_shaped",
    "ask", "described_share", "infix_surface", "language_report",
    "nested_surface",
]
