"""``glm_universal.runtime.reports.address``
-- the address family: ``nearest``, ``hole`` and ``locate``.

*Created 31 October 2026 (repository check): the four solvers and two helpers
below were moved here verbatim from* ``runtime/session.py`` *, which had grown
back to 4579 lines against the 4500-line budget that*
``test_runtime.TestTheReportSolversStaySplitOut`` *keeps ("a solver family
that grew here belongs in runtime/reports/").  Only the relative imports
changed (``..reasoning`` became ``...reasoning`` and ``. import
nearest_question`` became ``.. import nearest_question``); no line of logic,
wording or payload moved.*

These are not ``report <subject>`` solvers -- they answer query kinds of their
own, and ``_solve`` in the session still dispatches to them by kind -- but
they are one family that read one set of sub-packages, which is what this
directory groups by:

* ``_solve_nearest_address`` -- ``nearest to C moved 8 by 1/2``: the ranking
  against the address table, certified by the guarded read (Phase 148), with
  the question at a tie (Phase 150, :mod:`..nearest_question`);
* ``_solve_hole`` -- the deep-hole reading (:mod:`...reasoning.hole_reading`);
* ``_solve_locate`` with ``_locate_junction`` and ``_locate_question`` --
  the timed read of a place and the coordinate junction, ending with the
  declared question when more than one member is live.

The methods are mixed into
:class:`glm_universal.runtime.session.GeometricSession`, which is where
``self`` comes from: the loaded registers, the concept index and the shared
helpers.  The mixin holds no state of its own.

*Last altered 31 October 2026 (repository check): usage commands rewritten to start from the repository root (``PYTHONPATH=src``).*
"""
from __future__ import annotations

from fractions import Fraction

from ..parser import Query
from ..solution import Solution, SolverError, Step, q


class AddressReports:
    """The address family -- ``nearest``, ``hole`` and ``locate``.

    A mixin of :class:`~glm_universal.runtime.session.GeometricSession`;
    it holds no state of its own.
    """

    def _solve_nearest_address(self, query: Query) -> Solution:
        """``nearest to C moved 8 by 1/2`` -- a point no register holds,
        ranked against the 142 carriers of the address table and read by
        the guarded read (Phase 148, ``studies/NEAREST_ADDRESS_STUDY.md``).

        The ranking is the scan the ``nearest`` kind has always made; the
        guarded read certifies its head and the gap after it
        (``GLM.NearestAddress.ranking_head_eq_read``,
        ``ranking_tail_outside``, ``ranking_head_origin``).  When the read
        refuses, the head is still the strict nearest carrier whenever there
        is one (``ranking_head_of_strict``), and the answer says that no
        margin is certified.
        """
        from ...reasoning import address_read as adr
        from ...reasoning import address_table as adt
        from ...reasoning import nearest_address as na
        from .. import nearest_question as nq
        request = str(query.options["address_request"])
        limit = query.options.get("limit")
        rows = adt.carriers()
        # Phase 150: the place is what precedes 'given'; the replies follow
        place, given = nq.split(request)
        try:
            out = na.nearest_read(place, limit, rows)
        except adr.AddressError as error:
            raise SolverError(f"nearest ({error.reason}): {error}") from None

        _q = q

        label = out["label"]
        ranked = out["ranked"]
        names = [adr.carrier_label(rows, i) for i, _d in ranked]
        listing = ", ".join(f"{adr.carrier_label(rows, i)} (|q-c|^2 = "
                            f"{_q(d)})" for i, d in ranked)
        head = adr.carrier_label(rows, out["head"])
        tied = [adr.carrier_label(rows, i) for i in out["head_tied"]]
        steps = [
            Step("the pool and the point",
                 f"{label!s} names a point no register holds, so it is ranked "
                 f"against the {out['pool']} carriers of the address table "
                 f"(the declared sample of the construction ladder) in all 24 "
                 f"coordinates.",
                 f"pool = {out['pool']} carriers; point = {label}"),
            Step("the ranking",
                 f"Score every carrier by its exact squared distance to the "
                 f"point and sort; ties break by register:name, so the order "
                 f"is a function of the data alone "
                 f"(GLM.NearestAddress.Ranking).",
                 "\n".join(f"|q - {adr.carrier_label(rows, i)}|^2 = {_q(d)}"
                           for i, d in ranked)),
        ]
        if out["certified"]:
            members = [adr.carrier_label(rows, i) for i in out["members"]]
            if len(members) > 1:
                what = (f"the junction {{{', '.join(members)}}} (carriers at "
                        f"one exact coordinate vector, which no read can "
                        f"separate, GLM.CoordinateJunction.no_read_separates)")
            else:
                what = members[0]
            steps.append(Step(
                "the guarded read certifies the head",
                f"The guarded read of the same point answers {what} at rung "
                f"{out['rung']}; on the sound stored table its answer is the "
                f"head of every ranking (GLM.NearestAddress."
                f"ranking_head_eq_read), the head lies inside the margin and "
                f"every later carrier outside it "
                f"(GLM.NearestAddress.ranking_tail_outside).",
                f"rung {out['rung']}; margin >= {_q(out['margin'])}; gap "
                f"certified = {out['gap_certified']}"))
            answer = (f"nearest to {label} among the {out['pool']} carriers "
                      f"of the address table: {listing}; the guarded read "
                      f"certifies the head at rung {out['rung']}")
            if out["margin"] > 0:
                answer += (f": no other carrier lies within "
                           f"{adr.margin_text(out['margin'])} of the point "
                           f"(GLM.NearestAddress.ranking_tail_outside)")
            if out["delta2"] is not None and out["origin_certified"] \
                    and out["origin"] is not None and len(members) > 1:
                answer += (f"; the stated move is inside the margin, so the "
                           f"carrier the point came from is a member of the "
                           f"junction (GLM.CoordinateJunction.jread_origin)")
            elif out["delta2"] is not None and out["origin_certified"] \
                    and out["origin"] is not None:
                origin = adr.carrier_label(rows, out["origin"])
                answer += (f"; the stated move is inside the margin, so the "
                           f"head is the carrier the point came from, "
                           f"{origin} (GLM.NearestAddress.ranking_head_origin)")
        else:
            unguarded = ""
            if out["unguarded"] is not None:
                i, rung = out["unguarded"]
                unguarded = (f"; the unguarded ladder would have named "
                             f"{adr.carrier_label(rows, i)} at rung {rung}")
            steps.append(Step(
                "the guarded read refuses",
                f"No rung certifies a carrier for the point: at every rung "
                f"the cell is empty, shared, or its placement guard fails "
                f"(GLM.AddressRead.read_none_iff){unguarded}. The ranking "
                f"still stands -- its head is the strict nearest carrier "
                f"whenever there is one (GLM.NearestAddress."
                f"ranking_head_of_strict) -- but no margin around it is "
                f"certified.",
                "read refused; ranking by full scan alone"))
            if len(tied) > 1:
                head_text = (f"the first {len(tied)} are at one distance "
                             f"({', '.join(tied)})")
            else:
                head_text = f"the head, {head}, is the strict nearest by scan"
            answer = (f"nearest to {label} among the {out['pool']} carriers "
                      f"of the address table: {listing}; the guarded read "
                      f"refuses (no rung certifies the point), so {head_text} "
                      f"but no margin is certified")
        if out["origin"] is not None and out["origin"] not in \
                out["head_tied"]:
            answer += (f" (the point is nearer to {head} than to "
                       f"{adr.carrier_label(rows, out['origin'])}, the "
                       f"carrier it was made from)")
        expected = {"head": head, "top_names": str(names),
                    "top_distances2": str([_q(d) for _i, d in ranked]),
                    "certified": str(out["certified"])}
        if out["certified"]:
            expected["margin"] = _q(out["margin"])
        # Phase 150: a head of two or more carriers ends with the question
        answer, tie_payload = nq.question_turn(
            nq.head_labels(out, rows), place, given, answer, expected, steps)
        return Solution(
            query=query, kind="nearest", answer=answer, steps=tuple(steps),
            expected=expected,
            script_spec={"template": "nearest_address",
                         "args": {"request": place,
                                  "given": [list(g) for g in given],
                                  "limit": out["limit"]}},
            payload={"ranked": [[n, _q(d)] for n, (_i, d) in
                                zip(names, ranked)],
                     "pool_size": out["pool"], "address": True,
                     "certified": out["certified"], "rung": out["rung"],
                     "margin": out["margin"], "label": label,
                     "members": [adr.carrier_label(rows, i)
                                 for i in out["members"]],
                     "gap_certified": out["gap_certified"],
                     "tie": tie_payload})

    def _solve_hole(self, query: Query) -> Solution:
        """``hole walk 3`` -- a carrier classified by the deep hole it sits
        in, read under the budget rule (Phase 147,
        ``studies/BUDGET_READING_STUDY.md``).

        At the covering radius the reading stops on the completeness
        certificate or after 1056 starts (``GLM.ProbeBudget``), never after
        a run of barren starts; ``GLM.BudgetReading.budget_agrees`` says that
        wherever the old patience reading was certified this gives the same
        vertex set and type, and ``budget_refuses_only_without_cert`` that
        it refuses only if no start inside the budget carries the
        certificate.  Below the covering radius there is no type to give.
        """
        from ...reasoning import hole_reading as hr
        request = str(query.options.get("request", "")).strip()
        try:
            out = hr.answer(request)
        except hr.HoleError as error:
            raise SolverError(f"hole ({error.reason}): {error}") from None
        label = out["label"]
        status = out["status"]
        if status == "stalled":
            raise SolverError(
                f"hole (shallow): {label} stalled below the covering radius "
                f"(squared radius {out.get('radius2')} against 2), so it "
                f"reached no deep hole and has no Niemeier type")
        steps = [
            Step("the point",
                 (f"{label}: walk from a lattice point to a vertex of the "
                  f"Voronoi diagram and climb its 1-skeleton until no edge "
                  f"raises the radius." if out["walk"] is not None else
                  f"{label}: {out['construction']}."),
                 f"centre = {[str(x) for x in out['centre']]}"),
            Step("start 0 decides the depth",
                 "The first start is the undithered modulator, whose emitted "
                 "point is the exact nearest lattice point, so whether the "
                 "carrier is at the covering radius is decided before any "
                 "other start.",
                 f"squared distance to the lattice = {out['distance2']} "
                 f"(covering radius 2)"),
        ]
        if status in ("lattice-point", "shallow"):
            what = ("a lattice point: distance 0" if status == "lattice-point"
                    else f"below the covering radius: squared distance "
                         f"{out['distance2']}")
            raise SolverError(
                f"hole ({status}): {label} is {what}, so it sits in no deep "
                f"hole and has no Niemeier type however long it is read")
        steps.append(Step(
            "the reading, under the budget rule",
            f"Modulator starts are run until the vertices in hand carry the "
            f"completeness certificate (the marked-barycentre identity), with "
            f"no barren stop and a budget of {out['budget']} starts "
            f"(GLM.ProbeBudget.budget_serves_every_type); the closure step "
            f"then completes the vertex set.",
            f"starts run = {out['starts']} of {out['budget']}; vertices = "
            f"{out['vertex_count']}; budget reached = "
            f"{out['budget_reached']}"))
        if status != "certified":
            raise SolverError(
                f"hole (uncertified): {label} is at the covering radius, but "
                f"no start inside the budget of {out['budget']} closed the "
                f"certificate ({out['vertex_count']} vertices in hand), so "
                f"no type is named (GLM.BudgetReading."
                f"budget_refuses_only_without_cert)")
        steps.append(Step(
            "the certificate",
            f"Every component's marked barycentre is the centre, all "
            f"components share Coxeter number {out['coxeter']}, and the "
            f"total rank is 24: no further vertex can be added, so the "
            f"diagram {out['type']} is the hole's.",
            f"type = {out['type']}; Coxeter number = {out['coxeter']}"))
        answer = (f"{label} sits in a deep hole of type {out['type']} "
                  f"(Coxeter number {out['coxeter']}), from "
                  f"{out['vertex_count']} vertices certified complete by the "
                  f"marked-barycentre identity after {out['starts']} of "
                  f"{out['budget']} starts, read under the budget rule with "
                  f"no barren stop (GLM.BudgetReading.budget_agrees)")
        expected = {"type": str(out["type"]),
                    "vertex_count": str(out["vertex_count"]),
                    "certified": "True"}
        return Solution(
            query=query, kind="hole", answer=answer, steps=tuple(steps),
            expected=expected,
            script_spec={"template": "hole", "args": {"request": request}},
            payload={"type": out["type"], "label": label,
                     "starts": out["starts"], "budget": out["budget"],
                     "vertex_count": out["vertex_count"],
                     "walk": out["walk"], "rule": out["rule"]})

    def _solve_locate(self, query: Query) -> Solution:
        """``locate C moved 8 by 1/2`` -- a point read by its address.

        The point (a carrier, a carrier moved by Phase 127's declared move,
        or 24 exact coordinates) is quantised at each rung of the ladder
        Phase 129 measured, in the middle-out order, and answered at the
        first rung whose cell holds one carrier and whose placement guard
        ``|q - c_i| + |q - p| < rho_p`` holds, with ``rho_p`` read from the
        stored table (:mod:`..reasoning.address_table`) only while the
        digests it is kept beside hold.

        What an answer is worth is proved in
        ``RequestProject/GLM/AddressRead.lean``: it is the strictly nearest
        carrier (``read_strict_nearest``), the one a full scan finds
        (``read_agrees_with_scan``), the same in every visiting order
        (``read_order_independent``), and the only carrier within the
        reported margin (``read_unique_in_ball``, ``margin_lower``); when the
        request bounds the move, ``read_origin`` says whether the answer is
        the carrier the point came from.
        """
        from ...reasoning import address_read as adr
        from ...reasoning import address_table as adt
        from ...reasoning import coordinate_junction as cj
        from ...reasoning import timed_question as tq
        request = str(query.options.get("request", "")).strip()
        rows = adt.carriers()
        try:
            # Phase 146: 'locate albedo given word:absorbed is no' -- the place,
            # then the replies a conversation gave to the questions asked
            place, given = tq.split_given(request)
        except tq.GivenError as error:
            raise SolverError(f"locate ({error.reason}): {error}") from None
        try:
            table = adr.load_table(rows=rows)
            parts = adr.parse_request(place, rows)
        except adr.AddressError as error:
            raise SolverError(f"locate ({error.reason}): {error}") from None
        jtable, jstate = cj.load(rows=rows)
        read = cj.read_point(parts["point"], table, jtable, rows,
                             delta2=parts["delta2"])
        visited = []
        for row in read.rows:
            if row["cell"] == "empty":
                visited.append(f"{row['rung']}: empty cell")
            elif row["cell"] == "shared":
                visited.append(f"{row['rung']}: cell shared by "
                               f"{len(row['members'])} carriers")
            elif row["cell"] == "junction":
                verdict = "holds" if row["guard"] else "fails"
                visited.append(
                    f"{row['rung']}: one junction, "
                    f"{len(row['members'])} carriers at the coordinates of "
                    f"{adr.carrier_label(rows, row['carrier'])}; guard "
                    f"|q-c|^2 = {row['a2']}, |q-p|^2 = {row['b2']}, "
                    f"rho^2 = {row['rho2']}: {verdict}")
            else:
                verdict = "holds" if row["guard"] else "fails"
                visited.append(
                    f"{row['rung']}: one carrier, "
                    f"{adr.carrier_label(rows, row['carrier'])}; guard "
                    f"|q-c|^2 = {row['a2']}, |q-p|^2 = {row['b2']}, "
                    f"rho^2 = {row['rho2']}: {verdict}")
        steps = [
            Step("the table holds",
                 f"The stored address table covers the {len(rows)} carriers "
                 f"of the declared sample on the {len(adr.LADDER)} rungs "
                 f"{' '.join(adr.LADDER)}; it is used only because its "
                 f"source, carrier and content digests all hold against what "
                 f"is live, so every stored radius is the one computed from "
                 f"these carriers.",
                 f"{len(rows)} carriers; order {' '.join(adr.ORDER)}"),
            Step("the point, read rung by rung",
                 f"The point ({parts['label']}) is quantised at each rung in "
                 f"the middle-out order. A rung answers only when its cell "
                 f"holds exactly one carrier and the placement guard "
                 f"|q - c| + |q - p| < rho holds, decided exactly "
                 f"(GLM.CellGuard.sqrt_add_lt_sqrt_iff); two distances per "
                 f"rung, no scan of the carriers.",
                 "\n".join(visited)),
        ]
        if jtable is None:
            steps.append(Step(
                "the junction table does not hold",
                f"The junction table (carriers that share exact coordinates, "
                f"GLM.CoordinateJunction) is {jstate['verdict']} "
                f"({', '.join(jstate['failed'])}), so cells whose carriers "
                f"share coordinates are read as shared cells, as Phase 143 "
                f"reads them; re-take it with `PYTHONPATH=src python3 -m "
                f"glm_universal.tools junction-table --write`.",
                f"junction table {jstate['verdict']}"))
        if read.status != "answered":
            unguarded = ""
            if read.unguarded is not None:
                i, rung = read.unguarded
                unguarded = (f"; the unguarded ladder would have named "
                             f"{adr.carrier_label(rows, i)} at rung {rung}, "
                             f"uncertified")
            raise SolverError(
                f"locate (no-certified-rung): no rung certifies a carrier for "
                f"{parts['label']} -- at every rung the cell is empty, shared, "
                f"or its placement guard fails, so the read refuses "
                f"(GLM.AddressRead.read_none_iff){unguarded}")
        margin = read.margin

        def _q(value: Fraction) -> str:
            return f"{value.numerator}/{value.denominator}"

        if len(read.members) > 1:
            return self._locate_junction(query, request, parts, read, rows,
                                         steps, adr, cj, place, given)
        name = adr.carrier_label(rows, read.carrier)
        if given:
            raise SolverError(
                f"locate (no-tie): {parts['label']} reads as the single "
                f"carrier {name} at rung {read.rung}, so there is no tie for "
                f"the {len(given)} given repl"
                f"{'y' if len(given) == 1 else 'ies'} to resolve; ask "
                f"`locate {place}` alone")
        answer = (f"{parts['label']} reads as {name} at rung {read.rung}: "
                  f"certified the strictly nearest of the {len(rows)} "
                  f"carriers (GLM.AddressRead.read_strict_nearest)")
        if margin > 0:
            answer += (f", and no other carrier lies within "
                       f"{adr.margin_text(margin)} of the point "
                       f"(GLM.AddressRead.read_unique_in_ball)")
        expected = {"carrier": name, "margin": _q(margin)}
        if parts["delta2"] is not None:
            if read.origin_certified and parts["delta2"] == 0:
                answer += (f"; the point is a carrier itself, and the only "
                           f"carrier at distance 0 is {name} "
                           f"(GLM.AddressRead.read_origin)")
                expected["origin"] = name
                expected["delta2"] = _q(parts["delta2"])
            elif read.origin_certified:
                origin = (name if parts["origin"] is None
                          else adr.carrier_label(rows, parts["origin"]))
                answer += (f"; a move of at most sqrt({parts['delta2']}) is "
                           f"inside the margin, so if the point is a carrier "
                           f"moved that far, the carrier is {name} "
                           f"(GLM.AddressRead.read_origin)")
                expected["origin"] = origin
                expected["delta2"] = _q(parts["delta2"])
            else:
                answer += ("; the stated move is not inside the margin, so "
                           "the answer is certified nearest but not "
                           "certified to be the carrier the point came from")
        if parts["origin"] is not None and parts["origin"] != read.carrier:
            answer += (f" (the moved point is strictly nearer to {name} than "
                       f"to {adr.carrier_label(rows, parts['origin'])}, the "
                       f"carrier it was made from)")
        steps.append(Step(
            "one rung certifies, and it is the answer",
            f"At rung {read.rung} the cell holds only {name} and the guard "
            f"holds. Every other carrier is then at least rho - |q - p| from "
            f"the point while {name} is nearer than that, so {name} is the "
            f"strictly nearest carrier and the only one inside that margin; "
            f"the margin is reported as an exact lower bound "
            f"(GLM.AddressRead.margin_lower).",
            f"rung {read.rung}; cell {list(read.cell)}; |q-c|^2 = {read.a2}; "
            f"|q-p|^2 = {read.b2}; rho^2 = {read.rho2}; margin >= "
            f"{margin}"))
        return Solution(
            query=query, kind="locate", answer=answer, steps=tuple(steps),
            expected=expected,
            script_spec={"template": "locate", "args": {"request": request}},
            payload={"carrier": name, "index": read.carrier,
                     "rung": read.rung, "cell": read.cell, "a2": read.a2,
                     "b2": read.b2, "rho2": read.rho2, "margin": margin,
                     "origin_certified": read.origin_certified,
                     "label": parts["label"]})

    def _locate_junction(self, query: Query, request: str, parts, read,
                         rows, steps, adr, cj, place: str = "",
                         given=()) -> Solution:
        """A `locate` answer that is a junction: several carriers at one
        exact coordinate vector (Phase 144,
        ``studies/COORDINATE_JUNCTION_STUDY.md``).

        No function of the coordinates names each member
        (``GLM.CoordinateJunction.no_read_separates``), so the read answers
        the junction: strictly nearer the point than every carrier off its
        coordinates (``jread_junction_nearest``), exactly the set a full scan
        finds at the least distance (``jread_scan``), with a margin inside
        which nothing else lies (``jread_unique_in_ball``), and containing
        the carrier the point came from when a stated move is inside that
        margin (``jread_origin``).  Whether the members are one object is the
        junction's declaration (:data:`coordinate_junction.DECLARATIONS`);
        an undeclared junction is read as distinct, Phase 66's default.
        """
        labels = tuple(adr.carrier_label(rows, i) for i in read.members)
        joined = ", ".join(labels)
        margin = read.margin
        dec = cj.declaration_for(labels)

        def _q(value: Fraction) -> str:
            return f"{value.numerator}/{value.denominator}"

        answer = (f"{parts['label']} reads as the junction {{{joined}}} at "
                  f"rung {read.rung}: these {len(labels)} carriers have the "
                  f"same coordinates, so no read can separate them "
                  f"(GLM.CoordinateJunction.no_read_separates); the point is "
                  f"certified strictly nearer to their coordinates than to "
                  f"any other of the {len(rows)} carriers "
                  f"(GLM.CoordinateJunction.jread_junction_nearest)")
        if margin > 0:
            answer += (f", and nothing else lies within "
                       f"{adr.margin_text(margin)} of the point "
                       f"(GLM.CoordinateJunction.jread_unique_in_ball)")
        answer += "; " + cj.describe(labels)
        expected = {"junction": "|".join(labels), "margin": _q(margin)}
        if parts["delta2"] is not None:
            origin = (None if parts["origin"] is None
                      else adr.carrier_label(rows, parts["origin"]))
            if read.origin_certified:
                expected["delta2"] = _q(parts["delta2"])
                if (origin is not None and origin in labels
                        and parts["delta2"] == 0):
                    expected["origin"] = origin
                    answer += (f"; the point is {origin} itself, a member of "
                               f"the junction: the only carriers at distance "
                               f"0 are the junction's "
                               f"(GLM.CoordinateJunction.jread_origin)")
                elif origin is not None and origin in labels:
                    expected["origin"] = origin
                    answer += (f"; the request names {origin}, and the "
                               f"stated move of at most "
                               f"sqrt({parts['delta2']}) is inside the "
                               f"margin, so the carrier the point came from "
                               f"is in the junction "
                               f"(GLM.CoordinateJunction.jread_origin)")
                else:
                    expected["origin"] = "|".join(labels)
                    answer += (f"; a move of at most "
                               f"sqrt({parts['delta2']}) is inside the "
                               f"margin, so if the point is a carrier moved "
                               f"that far, it is one of the junction's "
                               f"members (GLM.CoordinateJunction.jread_origin)")
            else:
                answer += ("; the stated move is not inside the margin, so "
                           "the junction is certified nearest but not "
                           "certified to hold the carrier the point came "
                           "from")
            if origin is not None and origin not in labels:
                answer += (f" (the moved point is strictly nearer to this "
                           f"junction than to {origin}, the carrier it was "
                           f"made from)")
        steps.append(Step(
            "one rung certifies a junction, and it is the answer",
            f"At rung {read.rung} the cell holds only the {len(labels)} "
            f"carriers of one junction ({joined}), and the guard holds "
            f"against the junction radius: the distance from the cell centre "
            f"to the nearest carrier whose coordinates differ. Every such "
            f"carrier is then at least rho - |q - p| from the point while "
            f"the junction is nearer than that (GLM.CoordinateJunction."
            f"entry_junction_in_ball); the junction table is used only while "
            f"its source, carrier, declaration, address-table and content "
            f"digests hold.",
            f"rung {read.rung}; cell {list(read.cell)}; |q-c|^2 = {read.a2}; "
            f"|q-p|^2 = {read.b2}; rho^2 = {read.rho2}; margin >= "
            f"{margin}; declaration "
            f"{'none (read as distinct)' if dec is None else dec.kind}"))
        answer, tie_payload = self._locate_question(
            labels, place or parts["label"], list(given), answer, expected,
            steps)
        return Solution(
            query=query, kind="locate", answer=answer, steps=tuple(steps),
            expected=expected,
            script_spec={"template": "locate", "args": {"request": request}},
            payload={"carrier": "|".join(labels), "junction": labels,
                     "tie": tie_payload,
                     "index": read.carrier, "members": read.members,
                     "rung": read.rung, "cell": read.cell, "a2": read.a2,
                     "b2": read.b2, "rho2": read.rho2, "margin": margin,
                     "origin_certified": read.origin_certified,
                     "declaration": None if dec is None else dec.kind,
                     "label": parts["label"]})

    def _locate_question(self, labels, place: str, given, answer: str,
                         expected, steps):
        """Phase 146 (``studies/ANSWERING_QUESTION_STUDY.md``): the question
        in the answering path.

        A junction is held open as a tie over its members (Phase 145,
        :mod:`..reasoning.timed_question`).  The replies given in the request
        are applied in order (``GLM.AnsweringQuestion.after_reply``), and the
        answer ends with the question that comes next: while the tie is open
        the minimax question of the declared vocabulary, which splits the
        live set (``GLM.TimedQuestion.splits_iff``), so every reply removes
        a member and a dialogue over ``n`` members ends within ``n - 1``
        replies (``GLM.AnsweringQuestion.dialogue_length_lt``); once one
        member is left, the confirming question
        (``GLM.AnsweringQuestion.confirm_catches``).  Replies that leave no
        member are refused as a contradiction, never resolved
        (``GLM.TimedQuestion.contradicted_not_truthful``).
        """
        from ...reasoning import timed_question as tq
        tie = tq.junction_tie(labels)
        try:
            tq.apply_given(tie, given)
        except tq.GivenError as error:
            raise SolverError(f"locate ({error.reason}): {error}") from None
        replies = "; ".join(f"{s.question} {s.answer}" for s in tie.ledger)
        live = [tie.label(c) for c in tie.live]
        if tie.status == "contradicted":
            raise SolverError(
                f"locate (contradicted): {place} reads as the junction "
                f"{{{', '.join(labels)}}}, and the replies given ({replies}) "
                f"leave no member: some reply is false of the carrier meant, "
                f"or the carrier meant is not in the junction "
                f"(GLM.TimedQuestion.contradicted_not_truthful); the GLM "
                f"reports the contradiction rather than choose")
        q = tq.pending_question(tie)
        record = None if q is None else tq.question_record(tie, q)
        if given:
            answer += (f"; the replies given ({replies}) leave "
                       f"{len(live)} of the {len(labels)} members: "
                       f"{', '.join(live)} (GLM.AnsweringQuestion."
                       f"after_reply)")
            expected["live"] = "|".join(live)
        if tie.status == "resolved":
            confirmed = any(s.mode == "confirmed" for s in tie.ledger)
            answer += (f"; if the replies are true of the carrier meant, it "
                       f"is {live[0]} (GLM.TimedQuestion.resolved_eq_truth)")
            if confirmed:
                answer += ", and the confirming reply agrees"
        if record is not None:
            how = (f"`locate {tq.join_given(place, list(given) + [(record['key'], '<reply>')])}`")
            if record["kind"] == "confirm":
                answer += (f"; to confirm, the GLM asks: "
                           f"{tq.describe_question(record)} -- a false "
                           f"resolution is caught here "
                           f"(GLM.AnsweringQuestion.confirm_catches); reply "
                           f"as the next turn, or ask {how}")
            else:
                answer += (f"; to separate them, the GLM asks: "
                           f"{tq.describe_question(record)} -- reply as the "
                           f"next turn, or ask {how}")
                expected["asks"] = record["key"] + " -> " + " / ".join(
                    "|".join(o["keeps"]) for o in record["options"])
        steps.append(Step(
            "the question that comes next",
            "The junction is held open as a tie over its members. The "
            "replies given are applied in order, each keeping the members "
            "that give it (GLM.AnsweringQuestion.after_reply). While more "
            "than one member is live, the answer ends with the declared "
            "question whose worst reply leaves the fewest members; it splits "
            "the live set, so any reply removes at least one "
            "(GLM.AnsweringQuestion.reply_removes). With one member left it "
            "ends with the confirming question.",
            f"replies {len(given)}; live {len(live)} of {len(labels)} "
            f"({', '.join(live)}); status {tie.status}; next "
            f"{'none' if record is None else record['key']}"))
        payload = {"status": tie.status, "live": tuple(live),
                   "given": tuple(f"{k} is {v}" for k, v in given),
                   "place": place, "question": record,
                   "steps": tuple(dict(s.__dict__) for s in tie.ledger)}
        return answer, payload
