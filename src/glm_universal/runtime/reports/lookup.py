"""``glm_universal.runtime.reports.lookup``
-- the four lookup kinds: ``tool``, ``corpus``, ``study`` and ``sequence``.

*Created 31 October 2026 (repository check).  The parser's* ``KINDS`` *did
not list* ``corpus`` *(Phase 154) or* ``tool`` *(the evaluation's kind since
Phase 164) although the evaluation set covers both; the* ``corpus``
*solver of Phase 154 was lost with the reorganisation and is rebuilt here
against* :mod:`glm_universal.knowledge.ask`; *and the owner asked for a*
``study`` *kind (answered from the study manifests by*
:func:`glm_universal.corpus.study_index.answer_study_query`*) and a*
``sequence`` *kind (answered from the Integer and Monster Wheels by*
:func:`glm_universal.wheels.sequence_query.resolve_query`*).*

*Last altered 31 October 2026 (repository check): the Integer and Monster
wheels are installed provisionally -- the owner's decision, until the Lean
build confirms* ``Wheels/IntegerWheel.lean`` *and*
``Wheels/SporadicOrders.lean`` *-- so while they are in the register of*
:data:`glm_universal.wheels.PROVISIONAL_REGISTER` *a sequence answer ends
with that note, in square brackets, and its steps say so.*

*Last altered 1 November 2026 (Phase 186: intake absorption -- the sequence
kind's ``next`` reading, *what comes next in 1, 1, 2, 5, 14, 42*: its steps,
column 2 and payload in* ``_solve_sequence`` *(answered only when every entry
that starts with the claim agrees on the next term, and every entry holding
the claim from its second stored term agrees too; a disagreement is refused
as* ``JUNCTION``*), and its column 3 in*
:mod:`glm_universal.runtime.lookup_scripts`*.  The same day, after the
wheels bundle was absorbed ahead of its Lean build by the owner's decision,
the provisional step says which of the two states the register records.)*

What a lookup kind claims is decided in one place,
:mod:`glm_universal.runtime.lookup_kinds` (parser rule 0).  Each solver here
reads the data its kind names, says what it read, and returns a
:class:`~glm_universal.runtime.solution.Solution` whose column 3 re-checks
the reading in a fresh interpreter (:mod:`glm_universal.runtime.
lookup_scripts`):

* ``sequence`` -- an identification is re-derived by a brute-force scan of
  every wheel entry (exact matches first, then prefixes, least id; else the
  earliest run after the first term), a next term by a brute-force scan of
  every entry that starts with the claim or holds it from its second stored
  term (all must agree), and a sporadic order by recomputing every one of
  the 26 orders from its prime factorisation;
* ``study`` -- the reply is re-derived from the manifests on disk, and every
  study it names is checked to have a manifest (``studies/<ID>.yaml``) and a
  document (``studies/<ID>.md``);
* ``tool`` -- the tool is run again in the fresh interpreter and its verdict
  and figures compared: a reproduction, since each tool's own correctness is
  pinned by its tests (``tests/test_tool_verdicts.py`` and the rest);
* ``corpus`` -- the readings are recounted by the brute-force recheck of
  :mod:`glm_universal.knowledge.ask`.

A lookup that finds nothing refuses with the reason (``unsolved: ...``),
never a guess.  The methods are mixed into
:class:`glm_universal.runtime.session.GeometricSession`; the mixin holds no
state of its own.
"""
from __future__ import annotations

import re
from typing import Dict, List, Mapping, Tuple

from ..parser import Query
from ..solution import Solution, SolverError, Step


def _one_line(text: str) -> str:
    """A multi-line reply as one answer line, its lines joined by ``; ``."""
    return "; ".join(line.strip() for line in str(text).splitlines()
                     if line.strip())


def named_studies(reply: str, ids) -> Tuple[str, ...]:
    """The study ids ``reply`` names, in order of first mention: every
    upper-case token that is the id of a manifest."""
    known = set(ids)
    out: List[str] = []
    for token in re.findall(r"(?<![A-Za-z0-9_])[A-Z][A-Z0-9_]*[A-Z0-9]"
                            r"(?![A-Za-z0-9_])", str(reply)):
        if token in known and token not in out:
            out.append(token)
    return tuple(out)


def _figure_text(value: object) -> str:
    """A tool figure as text, exactly (``str`` of an int, a Fraction, a
    tuple of them)."""
    return str(value)


class LookupReports:
    """The four lookup kinds -- ``tool``, ``corpus``, ``study``,
    ``sequence``.

    A mixin of :class:`~glm_universal.runtime.session.GeometricSession`;
    it holds no state of its own.
    """

    # ------------------------------------------------------------------
    # sequence -- the Integer and Monster Wheels
    # ------------------------------------------------------------------

    def _solve_sequence(self, query: Query) -> Solution:
        """``what sequence is 1, 1, 2, 3, 5, 8``, ``what comes next in 1, 1,
        2, 5, 14, 42``, ``which sporadic group has order 7920``, ``what is
        the order of the Monster group``.

        Read by :func:`glm_universal.wheels.sequence_query.resolve_query`
        over the Monster Wheel (``studies/INTEGER_WHEEL_STUDY.md``
        section 2): ``speak`` for a claim the stored terms start with, then
        ``locate`` for a run inside them, ``find_by_order`` for an order.  A
        next-term question (the ``next`` reading, Phase 186) is answered only
        when every entry whose stored terms start with the claim and run past
        it gives the same next term, and every entry holding the claim from
        its second stored term (the offset-0/1 convention) gives it too;
        entries that disagree are refused as a junction (``JUNCTION``, naming
        each id and its next term), and a claim no entry starts with as
        ``NOT_ON_THE_WHEEL`` -- ``locate`` is never used for a next term.  A question nothing on the wheel answers
        is refused with the reason (``NOT_ON_THE_WHEEL``); nothing is
        guessed.  While the wheels are installed provisionally
        (:func:`glm_universal.wheels.provisional_status`) the answer ends
        with the provisional note.
        """
        from ...wheels import provisional_status
        from ...wheels import sequence_query as sq
        from ..lookup_kinds import sequence_wheel
        request = str(query.options.get("request", "")).strip()
        wheel = sequence_wheel()
        read = sq.resolve_query(request, wheel=wheel)
        if read.code == sq.NOT_MINE:
            raise SolverError(f"sequence (NOT_A_SEQUENCE_QUESTION): "
                              f"{request!r} is not a sequence or "
                              f"sporadic-order question")
        if read.code != sq.ANSWERED and read.kind == "next" and read.competing:
            raise SolverError(f"sequence (JUNCTION): {read.reply}")
        if read.code != sq.ANSWERED:
            raise SolverError(f"sequence (NOT_ON_THE_WHEEL): {read.reply}")
        found = read.ids[0]
        steps = [Step(
            "the wheel",
            "The question is read against the Monster Wheel: the "
            "audited Integer Wheel's OEIS entries, the 26 sporadic groups, "
            "their prime-exponent vectors and the sorted sporadic orders; it "
            "is built from the repository and never touches the network.",
            f"entries = {len(wheel)}")]
        if read.kind == "sequence":
            claim = ", ".join(str(t) for t in read.claim)
            how = ("speak: the least id among the entries whose stored "
                   "terms equal the claim, else among those that start with "
                   "it (Wheels/IntegerWheel.lean)" if read.position == 0
                   else "locate: no stored terms start with the claim, so "
                        "the entry in whose stored terms it occurs earliest "
                        "after the first term, least id on a tie")
            steps.append(Step("the claim", f"The integers of the question "
                              f"are the claim; it is read by {how}.",
                              f"claim = ({claim}); id = {found}; position = "
                              f"{read.position}"))
            expected = {"id": found, "position": str(read.position),
                        "claim": claim}
        elif read.kind == "next":
            claim = ", ".join(str(t) for t in read.claim)
            ids = ",".join(read.ids)
            shifted = ",".join(read.offset_ids) or "none"
            steps.append(Step(
                "the claim",
                "The integers of the question are the claim. Its next term is "
                "read from every entry whose stored terms start with the claim "
                "and run past it, and said only because all of them give the "
                "same next term, and so does every entry holding the claim from "
                "its second stored term (the same claim under the other "
                "indexing convention); entries that disagree, or one whose "
                "stored terms stop at the claim, would be a junction and "
                "refused. A run inside an entry is never the source of a next "
                "term: where it starts is unknown.",
                f"claim = ({claim}); entries starting with it = {ids}; "
                f"entries holding it from their second term = {shifted}; "
                f"next term = {read.next_term}"))
            expected = {"ids": ids, "next": str(read.next_term), "claim": claim}
        else:
            steps.append(Step(
                "the order",
                "A sporadic order is read by findByOrder "
                "(Wheels/SporadicOrders.lean: sound, and complete over the "
                "26); the 26 orders are distinct, so the group is unique."
                if read.kind == "order" else
                "The group named after 'order of' is read narrowly "
                "(an id as written, or a name the reading declares), and "
                "its stored order is said with its factorisation.",
                f"group = {found}; order = {read.order}"))
            expected = {"group": found, "order": str(read.order)}
        answer = read.reply
        note = provisional_status("wheels/sequence_query")
        if note:
            ahead = note.startswith("absorbed ahead of the build")
            steps.append(Step(
                "provisional",
                ("The Integer and Monster wheels are absorbed ahead of their "
                 "Lean build by the owner's decision: tested and measured "
                 "(studies/INTEGER_WHEEL_STUDY.md, "
                 "studies/INTAKE_CAPABILITY_STUDY.md), their Lean files "
                 "written and two standalone checks (IntakeChecks/NextTerm, "
                 "IntakeChecks/SporadicOrderCheck) built on their own; the "
                 "owner's build that confirms them is still to come, and the "
                 "answer says so."
                 if ahead else
                 "The Integer and Monster wheels are installed provisionally: "
                 "tested and measured (studies/INTEGER_WHEEL_STUDY.md), their "
                 "Lean files written, the build that confirms those files "
                 "still to come; the answer says so."),
                note))
            answer = f"{answer} [{note}]"
        payload = {"reading": read.kind, "ids": tuple(read.ids),
                   "order": read.order, "position": read.position,
                   "claim": tuple(read.claim), "faculty": "table"}
        if read.kind == "next":
            payload["next_term"] = read.next_term
        return Solution(
            query=query, kind="sequence", answer=answer,
            steps=tuple(steps), expected=expected,
            script_spec={"template": "sequence",
                         "args": {"request": request, "reading": read.kind}},
            payload=payload)

    # ------------------------------------------------------------------
    # study -- the study manifests
    # ------------------------------------------------------------------

    def _solve_study(self, query: Query) -> Solution:
        """``study colour induction``, ``which studies bear on the Golay
        code``, ``what does FOLD_MACHINE_STUDY depend on``, ``which studies
        have a missing Lean file``, ``open studies``.

        Answered from the study manifests (``studies/*.yaml``, schema
        ``glm-study-manifest/v1``) by
        :func:`glm_universal.corpus.study_index.answer_study_query`; nothing
        is stored beside them.  When nothing in the manifests answers, the
        question is refused with the reason (``NOTHING_IN_THE_MANIFESTS``).
        """
        from ...corpus import study_index as si
        request = str(query.options.get("request", "")).strip()
        index = si.study_index()
        code, reply = si.answer_study_query(request, index)
        if code == 2:
            raise SolverError(f"study (EMPTY): {_one_line(reply)}")
        if code != 0:
            raise SolverError(f"study (NOTHING_IN_THE_MANIFESTS): "
                              f"{_one_line(reply)}")
        named = named_studies(reply, index.ids)
        lines = len(str(reply).splitlines())
        steps = (
            Step("the manifests",
                 "Every study has a manifest derived from its prose and the "
                 "tree; the index loads all of them through the loader the "
                 "study ledger uses, and answers from them alone.",
                 f"manifests = {len(index.ids)}"),
            Step("the reading",
                 "The question is read as one of the index's forms -- a "
                 "study's card, a term the studies bear on, a study's "
                 "predecessors or successors, its marks or follow-ups, the "
                 "Lean gaps, the open studies, a phase or directive list, or "
                 "the studies citing a file.",
                 f"named = {', '.join(named) or 'none'}; lines = {lines}"),
        )
        return Solution(
            query=query, kind="study", answer=_one_line(reply), steps=steps,
            expected={"code": "0", "named": ",".join(named),
                      "lines": str(lines)},
            script_spec={"template": "study", "args": {"request": request}},
            payload={"reply": reply, "named": named,
                     "manifests": len(index.ids), "faculty": "table"})

    # ------------------------------------------------------------------
    # tool -- the toolbox, through the grammar
    # ------------------------------------------------------------------

    def _solve_tool(self, query: Query) -> Solution:
        """``tool <name> [argument]`` (and ``tools``) asked through the
        session rather than the router: the toolbox runs it exactly as the
        router's ``toolbox`` surface does
        (:func:`glm_universal.runtime.toolbox.run_tool`), and a tool's
        refusal is the solver's refusal."""
        from .. import toolbox as tb
        request = str(query.options.get("request", "")).strip()
        got = tb.run_tool(request)
        if not got.ok:
            text = got.text
            if text.startswith("refused: "):
                text = text[len("refused: "):]
            raise SolverError(f"tool: {_one_line(text)}")
        figures: Dict[str, str] = {f"figure:{key}": _figure_text(value)
                                   for key, value in sorted(
                                       dict(got.figures).items())}
        expected = {"ok": "True"}
        expected.update(figures)
        steps = (Step("the toolbox",
                      "The request names a tool of the toolbox; the tool "
                      "runs on the argument and returns its answer with "
                      "the figures it computed.",
                      f"{request}; figures = {len(figures)}"),)
        return Solution(
            query=query, kind="tool", answer=got.text, steps=steps,
            expected=expected,
            script_spec={"template": "tool", "args": {"request": request}},
            payload={"figures": dict(got.figures), "faculty": "address"})

    # ------------------------------------------------------------------
    # corpus -- what the corpus says (Phases 154-155)
    # ------------------------------------------------------------------

    def _solve_corpus(self, query: Query) -> Solution:
        """``corpus define golay code``, ``corpus continue a digest
        addresses``, ``corpus address of seven`` (Phases 154-155,
        ``studies/CORPUS_KNOWLEDGE_STUDY.md`` and
        ``studies/CORPUS_DEFINITIONS_STUDY.md``).

        The request grammar and the readings are
        :mod:`glm_universal.knowledge.ask`'s; column 3 recounts the answer by
        its brute-force recheck.  A term no sentence mentions, a tie, a
        phrase given to ``address of`` and a word with too little company are
        refused with the reason.
        """
        from ...knowledge import ask as ka
        request = str(query.options.get("request", "")).strip()
        reader = getattr(ka, "ask", None)
        if reader is not None:
            got: Mapping[str, object] = reader(request)
        else:
            refusal = getattr(ka, "CorpusRefusal", Exception)
            try:
                got = dict(ka.answer_request(request))
            except refusal as exc:
                raise SolverError(f"corpus: {exc}") from None
            got.setdefault("ok", True)
        if not got.get("ok"):
            reading = str(got.get("reading", "") or "corpus")
            raise SolverError(f"corpus ({reading}): "
                              f"{got.get('refusal', 'refused')}")
        expected = {str(k): str(v)
                    for k, v in dict(got.get("expected", {}) or {}).items()}
        witness = got.get("witness", ())
        steps = (Step("the reading",
                      f"The request is read as the corpus's "
                      f"{got.get('reading', '')!s} reading over the counted "
                      f"sentences of the repository; nothing is trained and "
                      f"nothing is sampled.",
                      f"witness = {witness}"),)
        return Solution(
            query=query, kind="corpus", answer=_one_line(got.get("answer", "")),
            steps=steps, expected=expected,
            script_spec={"template": "corpus", "args": {"request": request}},
            payload={"reading": got.get("reading", ""), "witness": witness,
                     "faculty": "table"})
