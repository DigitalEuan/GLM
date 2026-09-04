"""``glm_universal.runtime.reports.reasoning``
-- the subjects the restored reasoning modules compute.

The archive's reasoning loop, measured on the smallest instance it used
itself (:mod:`glm_universal.reasoning.search_loop`), and the address book used
as a retrieval index, measured against its controls
(:mod:`glm_universal.reasoning.retrieval`).

Every method here is a solver for one ``report <subject>`` query.  They are
mixed into :class:`glm_universal.runtime.session.GeometricSession`,
which is where ``self`` comes from.  Splitting them out of the session keeps
each family beside a docstring that says which sub-package computes it, and
keeps the dispatcher readable as a dispatcher.
"""
from __future__ import annotations

from ...reasoning import controller as ctl
from ...reasoning import retrieval as rt
from ...reasoning import search_loop as sl

from ..payload import jsonable
from ..parser import Query
from ..solution import Solution, Step, q


class ReasoningReports:
    """The subjects the restored reasoning modules compute.

    A mixin of :class:`~glm_universal.runtime.session.GeometricSession`;
    it holds no state of its own.
    """

    # -- the archive's search loop, measured ------------------------------

    def _report_searchloop(self, query: Query) -> Solution:
        """Wires sl.search_loop_report -- the hard gate and what it leaves.

        The archive's ARC solvers all converge on one shape: propose
        candidates, keep exactly those that reproduce every training pair,
        rank what is left.  This subject measures what that shape leaves
        behind on the eight symmetries of the square acting on ``3 x 3``
        binary grids -- how many candidates one example can ever remove,
        how many distinct answers survive on a fresh question, and what a
        second example buys -- and exhibits the four-line refutation of
        the soft alternative.
        """
        report = sl.search_loop_report()
        stab = report["stabiliser_census"]
        amb = report["ambiguity_census"]
        second = report["second_example"]
        gate = report["soft_gate"]

        steps = [
            Step("the candidate set is a group",
                 f"The candidates are the eight symmetries of the square "
                 f"acting on the {report['grids']} binary "
                 f"3 x 3 grids.  They are checked, not assumed, to be "
                 f"distinct as permutations of the grids and closed under "
                 f"composition, so 'how much does one example tell you' is "
                 f"a question about a group action rather than about a "
                 f"particular solver.",
                 f"candidates {report['candidates']}, grids "
                 f"{report['grids']}, closed "
                 f"{report['group_is_closed']}, faithful "
                 f"{report['group_is_faithful']}"),
            Step("one example leaves a coset of a stabiliser",
                 f"Filtering on a single input/output pair leaves exactly "
                 f"the candidates agreeing with it, and that set is a coset "
                 f"of the stabiliser of the *input*: its size does not "
                 f"depend on the output observed, only on how symmetric the "
                 f"input grid happens to be.  So the survivor count is "
                 f"|Stab g|, and the census over all grids is the census of "
                 f"stabiliser orders.",
                 f"stabiliser census "
                 + ", ".join(f"|Stab| = {k}: {v} grids"
                             for k, v in sorted(stab.items()))
                 + f"; total {report['stabiliser_total']}, orbits "
                 f"{report['orbits']}, mean survivors "
                 f"{q(report['mean_survivors'])}"),
            Step("what is left undetermined is an orbit, not a count",
                 f"Survivors are not the measure that matters: two survivors "
                 f"that agree on the fresh question leave nothing "
                 f"undetermined.  The honest measure is the number of "
                 f"distinct predictions, an orbit of the question under the "
                 f"stabiliser of the example, and it is 1 exactly when every "
                 f"symmetry of the example is also a symmetry of the "
                 f"question.  Over all "
                 f"{report['pairs']} (example, question) pairs the answer is "
                 f"determined outright in a clear majority of cases and "
                 f"never in more than eight ways.",
                 f"ambiguity census "
                 + ", ".join(f"{k} prediction(s): {v} pairs"
                             for k, v in sorted(amb.items()))
                 + f"; mean {q(report['mean_ambiguity'])}, determined "
                 f"{q(report['determined_fraction'])}, every ambiguity "
                 f"divides 8 {report['every_ambiguity_divides_eight']}"),
            Step("a second example is monotone and cheap",
                 f"Adding an example can only remove candidates, never add "
                 f"one, so ambiguity is antitone in the evidence.  A second "
                 f"example pins the answer outright on "
                 f"{second['pinned_by_two']} of the "
                 f"{second['pairs']} pairs, against "
                 f"{second['pinned_by_one']} for one example -- most of the "
                 f"remaining ambiguity is bought out by one more "
                 f"observation.",
                 f"second-example census "
                 + ", ".join(f"{k}: {v}"
                             for k, v in sorted(second["census"].items()))
                 + f"; mean {q(second['mean'])}, Lean {second['lean']}"),
            Step("the soft gate is refuted in four lines",
                 f"The archive's own ledger records accepting a candidate on "
                 f"a high coherence score as catastrophic, and the reason "
                 f"fits in one witness: two candidates, one observation that "
                 f"already refutes the second, and a score that prefers it "
                 f"anyway.  The hard gate keeps the truth; the score picks "
                 f"the refuted candidate.  This is why the loop filters "
                 f"before it ranks.",
                 f"survivors {gate['survivors']}, truth {gate['truth']} "
                 f"survives {gate['truth_survives']}, score choice "
                 f"{gate['score_choice']} refuted "
                 f"{gate['score_choice_is_refuted']}; Lean {gate['lean']}"),
        ]

        expected = {
            "grids": str(report["grids"]),
            "candidates": str(report["candidates"]),
            "group_is_closed": str(report["group_is_closed"]),
            "group_is_faithful": str(report["group_is_faithful"]),
            "stabiliser_total": str(report["stabiliser_total"]),
            "orbits": str(report["orbits"]),
            "mean_survivors": q(report["mean_survivors"]),
            "pairs": str(report["pairs"]),
            "ambiguity_total": str(report["ambiguity_total"]),
            "mean_ambiguity": q(report["mean_ambiguity"]),
            "determined_fraction": q(report["determined_fraction"]),
            "every_ambiguity_divides_eight":
                str(report["every_ambiguity_divides_eight"]),
            "pinned_by_one": str(second["pinned_by_one"]),
            "pinned_by_two": str(second["pinned_by_two"]),
            "second_mean": q(second["mean"]),
            "score_choice_is_refuted": str(gate["score_choice_is_refuted"]),
            "truth_survives": str(gate["truth_survives"]),
            "lean_file": str(report["lean_file"]),
        }
        for order, count in sorted(stab.items()):
            expected[f"stabiliser_{order}"] = str(count)
        for width, count in sorted(amb.items()):
            expected[f"ambiguity_{width}"] = str(count)

        return Solution(
            query=query, kind="report",
            answer=f"report searchloop: the archive's loop -- filter on "
                   f"every example, then rank -- measured on the eight "
                   f"symmetries of the square over {report['grids']} binary "
                   f"3 x 3 grids.  One example leaves a coset of the "
                   f"stabiliser of the example's input, so its survivor "
                   f"count does not depend on the output observed at all: "
                   f"the census is "
                   + ", ".join(f"{k}:{v}" for k, v in sorted(stab.items()))
                   + f" over {report['orbits']} orbits, a mean of "
                   f"{q(report['mean_survivors'])} survivors.  Survivors "
                   f"overstate the difficulty -- what is actually "
                   f"undetermined is the orbit of the fresh question under "
                   f"that stabiliser, which is "
                   + ", ".join(f"{k}:{v}" for k, v in sorted(amb.items()))
                   + f" over {report['pairs']} pairs, mean "
                   f"{q(report['mean_ambiguity'])}, determined outright on "
                   f"{q(report['determined_fraction'])} of them and never "
                   f"more than eight ways.  A second example is monotone "
                   f"and raises the determined count from "
                   f"{second['pinned_by_one']} to "
                   f"{second['pinned_by_two']}.  The soft alternative is "
                   f"refuted by one witness in which the score prefers a "
                   f"candidate the single observation has already ruled "
                   f"out, which is why the gate is hard; the general "
                   f"statements are proved for an arbitrary candidate set "
                   f"in {report['lean_file']}",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_searchloop", "args": {}},
            payload={"report": jsonable({
                "grids": report["grids"],
                "orbits": report["orbits"],
                "mean_survivors": q(report["mean_survivors"]),
                "mean_ambiguity": q(report["mean_ambiguity"]),
                "determined_fraction": q(report["determined_fraction"]),
                "pinned_by_two": second["pinned_by_two"],
                "lean_file": report["lean_file"]})})

    # -- the address book, used as an index -------------------------------

    def _report_retrieval(self, query: Query) -> Solution:
        """Wires rt.retrieval_report -- does the address layer do work?

        The address book gave every Lean declaration a deterministic Leech
        address; this subject asks whether that address can *retrieve* the
        declarations relevant to a query, and scores it against the controls
        the house style requires -- a digest, a seeded reshuffle, a random
        ranking, chance, a name search, and the one that decides the matter,
        a plain lexical search over the statement text.
        """
        report = rt.retrieval_report()
        decl = report["declaration_queries"]
        goal = report["goal_queries"]
        hybrid = report["hybrid"]
        guarantee = report["guarantee"]
        verdict = report["verdict"]
        k = report["k"]
        rows = decl["schemes"]

        def rate(scheme: str, table=None) -> str:
            source = table if table is not None else rows
            return q(source[scheme][k]["hit_rate"])

        steps = [
            Step("the index, and what counts as a hit",
                 f"Every one of the {decl['corpus']} declarations of the Lean "
                 f"development carries a Leech address computed from twenty "
                 f"four structural counts.  A query is answered by the "
                 f"{k} nearest addresses.  A retrieved declaration counts as "
                 f"a hit when it is a *relative* of the query -- same source "
                 f"file, or joined by a citation -- and neither relation is "
                 f"anywhere in the feature map, so this is a prediction the "
                 f"scheme can fail.  {decl['queries']} queries, a mean of "
                 f"{q(decl['mean_relatives'])} relatives each.",
                 f"corpus {decl['corpus']}, queries {decl['queries']}, k {k}, "
                 f"mean relatives {q(decl['mean_relatives'])}"),
            Step("the address is a real index",
                 f"At k = {k} the address finds a relative for "
                 f"{rows['address'][k]['hits']} of {decl['queries']} queries "
                 f"against a closed-form chance of "
                 f"{q(report['chance_rounded'][k])} -- "
                 f"{q(report['times_chance_rounded'])} times chance -- and it "
                 f"beats "
                 f"the digest control, the seeded reshuffle, the random "
                 f"ranking and name-substring search.  The three null models "
                 f"sit at chance, which is what makes the comparison mean "
                 f"anything.",
                 f"address {rate('address')}, digest {rate('digest')}, "
                 f"shuffled {rate('shuffled')}, random {rate('random')}, "
                 f"name {rate('name')}, chance {q(decl['chance'][k])}"),
            Step("and a plain lexical search beats it",
                 f"The strong control is Jaccard overlap of identifier tokens "
                 f"between the query and each candidate statement -- what a "
                 f"text search does.  It finds a relative for "
                 f"{rows['text'][k]['hits']} of the same {decl['queries']} "
                 f"queries at {q(rows['text'][k]['precision'])} precision "
                 f"against the address's "
                 f"{q(rows['address'][k]['precision'])}.  Ranking the raw "
                 f"feature vectors with no lattice at all scores "
                 f"{rate('features')}, within a few points of the address: "
                 f"the separation belongs to the feature map, not to the "
                 f"quantiser, exactly as GLM.Retrieval.retrieve_congr says it "
                 f"must.  Giving the geometry the identifiers instead of the "
                 f"syntax -- a second address book built from initial-letter "
                 f"counts -- reaches {rate('lexical')}, better and still not "
                 f"enough.",
                 f"text {rate('text')}, lexical {rate('lexical')}, "
                 f"features {rate('features')}, address {rate('address')}"),
            Step("a bare goal is harder, and the order does not change",
                 f"A goal query is a statement with no name and no place in "
                 f"the development, so the two coordinates it cannot know are "
                 f"zero: none of the {goal['queries']} goal queries "
                 f"reproduces its own stored feature vector.  The address "
                 f"drops to {rate('address', goal['schemes'])} and the "
                 f"lexical address to {rate('lexical', goal['schemes'])}, "
                 f"while the text control is almost unmoved at "
                 f"{rate('text', goal['schemes'])} -- a goal is its "
                 f"identifiers.",
                 f"goal queries {goal['queries']}, reproduced "
                 f"{goal['features_reproduced']}, address "
                 f"{rate('address', goal['schemes'])}, text "
                 f"{rate('text', goal['schemes'])}"),
            Step("and it is not a free filter either",
                 f"Pruning to the nearest by address and then ranking by text "
                 f"costs accuracy at every shortlist size tried: "
                 + ", ".join(f"{row['shortlist']} -> {q(row['hit_rate'])}"
                             for row in hybrid["rows"])
                 + f", against {q(hybrid['text_alone']['hit_rate'])} with no "
                 f"shortlist at all.  The curve is monotone, so the ordering "
                 f"is positively correlated with relevance -- it just is not "
                 f"free.",
                 f"any shortlist beats text {hybrid['any_shortlist_beats_text']}"),
            Step("what the lattice does earn is exactness",
                 f"The completeness bound of {report['lean_file']} -- feature "
                 f"distance r implies address distance at most r + 2rho -- was "
                 f"checked on {guarantee['pairs_checked']} pairs with "
                 f"{guarantee['violations']} violations.  At feature radius "
                 f"{guarantee['feature_radius']} the guaranteed-complete "
                 f"shortlist is {q(guarantee['mean_shortlist'])} declarations, "
                 f"{q(guarantee['mean_shortlist_fraction'])} of the corpus, "
                 f"and it provably contains all "
                 f"{q(guarantee['mean_feature_close'])} feature-close ones.  "
                 f"An empty shortlist is a proof of absence, the ranking does "
                 f"not depend on the order the corpus was read in, and "
                 f"widening k only appends -- all four are theorems, not "
                 f"measurements.",
                 f"pairs {guarantee['pairs_checked']}, violations "
                 f"{guarantee['violations']}, shortlist "
                 f"{q(guarantee['mean_shortlist_fraction'])} of the corpus"),
        ]

        expected = {
            "corpus": str(decl["corpus"]),
            "queries": str(decl["queries"]),
            "goal_queries": str(goal["queries"]),
            "goal_features_reproduced": str(goal["features_reproduced"]),
            "k": str(k),
            "chance": q(decl["chance"][k]),
            "times_chance": q(report["times_chance"]),
            "times_chance_rounded": q(report["times_chance_rounded"]),
            "pairs_checked": str(guarantee["pairs_checked"]),
            "violations": str(guarantee["violations"]),
            "mean_shortlist": q(guarantee["mean_shortlist"]),
            "hybrid_beats_text": str(hybrid["any_shortlist_beats_text"]),
            "lean_file": str(report["lean_file"]),
        }
        for scheme in rt.SCHEMES:
            expected[f"{scheme}_hit_rate"] = q(rows[scheme][k]["hit_rate"])
        for key, value in verdict.items():
            expected[f"verdict_{key}"] = str(value)

        return Solution(
            query=query, kind="report",
            answer=f"report retrieval: the address book used as an index over "
                   f"{decl['corpus']} Lean declarations, scored on "
                   f"{decl['queries']} queries against every control.  The "
                   f"address finds a relative in its top {k} for "
                   f"{rows['address'][k]['hits']} of them -- "
                   f"{q(report['times_chance_rounded'])} times the "
                   f"closed-form chance of "
                   f"{q(report['chance_rounded'][k])} -- and beats the digest "
                   f"({rate('digest')}), the seeded reshuffle "
                   f"({rate('shuffled')}), a random ranking "
                   f"({rate('random')}) and name search ({rate('name')}).  It "
                   f"is beaten decisively by a plain lexical search over the "
                   f"statement text ({rate('text')}), ranking the raw feature "
                   f"vectors without any lattice scores {rate('features')}, "
                   f"and an address book built from the identifiers rather "
                   f"than the syntax reaches {rate('lexical')} -- so the "
                   f"separation is the feature map's and the ceiling is the "
                   f"projection into twenty four capped integers, not the "
                   f"decoder.  No address shortlist improves on the text "
                   f"control at any size.  What the lattice does earn is "
                   f"exactness: the completeness bound of "
                   f"{report['lean_file']} holds on "
                   f"{guarantee['pairs_checked']} pairs with "
                   f"{guarantee['violations']} violations, so a radius search "
                   f"prunes the corpus to "
                   f"{q(guarantee['mean_shortlist_fraction'])} of itself "
                   f"while provably keeping every feature-close declaration, "
                   f"and an empty shortlist is a proof of absence",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_retrieval", "args": {}},
            payload={"report": jsonable({
                "corpus": decl["corpus"],
                "queries": decl["queries"],
                "address": q(rows["address"][k]["hit_rate"]),
                "text": q(rows["text"][k]["hit_rate"]),
                "lexical": q(rows["lexical"][k]["hit_rate"]),
                "chance": q(decl["chance"][k]),
                "pairs_checked": guarantee["pairs_checked"],
                "violations": guarantee["violations"],
                "lean_file": report["lean_file"]})})

    # -- the loop: propose, check, refuse ---------------------------------

    def _report_controller(self, query: Query) -> Solution:
        """Wires ctl.controller_report -- can the substrate steer a loop?

        The controller derives a physical quantity from the ten EXT10
        generators one factor at a time: propose the twenty moves, check the
        state exactly, keep the best few, and refuse when the beam is spent.
        Six scorers run on the same tasks, one of them the Leech address, and
        every plan any of them returns is re-checked by the digit-stack
        verifier, which is a different instrument from the one that built it.
        """
        report = ctl.controller_report()
        rows = report["heuristics"]
        verdict = report["verdict"]
        reachable = report["reachable"]

        steps = [
            Step("the task, and why every step can be checked",
                 f"A state is the ten EXT10 exponents; a move multiplies or "
                 f"divides by one of the ten generators, each checked against "
                 f"the register to be the unit quantity of its axis rather "
                 f"than assumed to be.  The loop proposes the "
                 f"{report['generators']['moves']} moves, checks the state "
                 f"against the target exactly, keeps the best "
                 f"{report['width']} and goes round again, up to "
                 f"{report['depth']} rounds.  The finished plan is an "
                 f"expression, and it is handed to the digit-stack verifier -- "
                 f"a different instrument from the one that built it.",
                 f"generators {len(ctl.GENERATORS)} all unit vectors "
                 f"{report['generators']['all_unit_vectors']}, moves "
                 f"{report['generators']['moves']}, width {report['width']}, "
                 f"depth {report['depth']}"),
            Step("a refusal that carries a proof",
                 f"Every move adds one to a single exponent, so it cannot "
                 f"change the denominator of an exponent, the decimal scale, "
                 f"the tensor rank or the P/T/C grading.  A target differing "
                 f"in any of those is unreachable at any depth, and the "
                 f"controller says so without expanding a node: "
                 f"{report['register'] - report['reachable_in_register']} of "
                 f"the register's {report['register']} quantities are refused "
                 f"this way and "
                 f"{report['reachable_in_register']} are reachable.  The other "
                 f"refusal -- the beam ran out of depth -- is a statement "
                 f"about the search, and the loop never returns its closest "
                 f"state as if it were the answer.",
                 f"invariant refusals {report['unreachable']} of "
                 f"{report['targets']} tasks, reachable in register "
                 f"{report['reachable_in_register']}/{report['register']}"),
            Step("the exact scorer is the ceiling, and it is a theorem",
                 f"There is always a move that reduces the remaining distance "
                 f"by one, so a loop steered by the exact count never "
                 f"backtracks and its plan is minimal.  It solves "
                 f"{rows['exponent']['solved']} of {reachable}, all minimal, "
                 f"scoring {q(rows['exponent']['mean_proposals'])} proposals "
                 f"per task.",
                 f"exponent {rows['exponent']['solved']}/{reachable}, minimal "
                 f"{rows['exponent']['minimal']}, mean proposals "
                 f"{q(rows['exponent']['mean_proposals'])}"),
            Step("the substrate steers -- and no better than its own coordinates",
                 f"The Leech address at scale 9 solves "
                 f"{rows['address']['solved']} of {reachable} against "
                 f"{rows['none']['solved']} for no guidance and "
                 f"{rows['random']['solved']} for a scorer blind to the "
                 f"target, so the geometry really is guiding the search.  The "
                 f"same distance with the decoder removed -- the raw carrier -- "
                 f"solves {rows['carrier']['solved']}, so the lattice is "
                 f"carrying the structure faithfully and adding nothing to it.",
                 f"address {rows['address']['solved']}, carrier "
                 f"{rows['carrier']['solved']}, none {rows['none']['solved']}, "
                 f"random {rows['random']['solved']}, of {reachable}"),
            Step("and below the read-back scale it stops working entirely",
                 f"Decoded at the register's own resolution instead of scale "
                 f"9, the address scorer solves "
                 f"{rows['address_native']['solved']} -- exactly the "
                 f"no-guidance figure, proposal for proposal.  The covering "
                 f"radius is 4 and adjacent states are sqrt(2) apart, so the "
                 f"decoder conflates them; Address.lean requires a scale above "
                 f"twice the covering radius for the encoding to be lossless, "
                 f"and this is that bound measured rather than asserted.",
                 f"address at scale 1 {rows['address_native']['solved']}, "
                 f"proposals {q(rows['address_native']['mean_proposals'])}; "
                 f"none {rows['none']['solved']}, proposals "
                 f"{q(rows['none']['mean_proposals'])}"),
            Step("nothing is trusted because the loop produced it",
                 f"Every plan every scorer returned was re-verified end to end "
                 f"by the digit-stack verifier: "
                 f"{sum(r['verified'] for r in rows.values())} of "
                 f"{sum(r['solved'] for r in rows.values())} across the six "
                 f"scorers, with no exceptions.",
                 f"verified {sum(r['verified'] for r in rows.values())}/"
                 f"{sum(r['solved'] for r in rows.values())}, every answer "
                 f"verified {verdict['every_answer_is_verified']}"),
        ]

        expected = {
            "targets": str(report["targets"]),
            "reachable": str(report["reachable"]),
            "unreachable": str(report["unreachable"]),
            "register": str(report["register"]),
            "reachable_in_register": str(report["reachable_in_register"]),
            "width": str(report["width"]),
            "depth": str(report["depth"]),
            "moves": str(report["generators"]["moves"]),
            "generators_are_unit_vectors":
                str(report["generators"]["all_unit_vectors"]),
            "lean_file": str(report["lean_file"]),
        }
        for name in ctl.HEURISTIC_ORDER:
            expected[f"{name}_solved"] = str(rows[name]["solved"])
            expected[f"{name}_minimal"] = str(rows[name]["minimal"])
            expected[f"{name}_verified"] = str(rows[name]["verified"])
            expected[f"{name}_mean_proposals"] = q(rows[name]["mean_proposals"])
        for key, value in verdict.items():
            expected[f"verdict_{key}"] = str(value)

        return Solution(
            query=query, kind="report",
            answer=f"report controller: a propose-check-refuse loop that "
                   f"derives a physical quantity from the ten EXT10 "
                   f"generators one factor at a time, run on {reachable} "
                   f"reachable targets and {report['unreachable']} unreachable "
                   f"ones with six different scorers.  Every plan returned was "
                   f"re-verified by the digit-stack verifier, which did not "
                   f"build it.  The exact remaining-move count solves "
                   f"{rows['exponent']['solved']}/{reachable}, all minimal, "
                   f"because a descent move always exists.  The Leech address "
                   f"at scale 9 solves {rows['address']['solved']}/{reachable} "
                   f"against {rows['none']['solved']} for no guidance and "
                   f"{rows['random']['solved']} for a scorer blind to the "
                   f"target -- so the substrate can steer a loop -- but the "
                   f"same distance measured on the undecoded carrier solves "
                   f"{rows['carrier']['solved']}, so the lattice adds nothing "
                   f"to its own coordinates; and at the register's native "
                   f"resolution it solves {rows['address_native']['solved']}, "
                   f"identical to no guidance, which is Address.lean's "
                   f"read-back bound measured.  "
                   f"{report['register'] - report['reachable_in_register']} of "
                   f"the {report['register']} register quantities are refused "
                   f"outright by an invariant no move can change, with no "
                   f"search at all; the general statements are proved in "
                   f"{report['lean_file']}",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_controller", "args": {}},
            payload={"report": jsonable({
                "reachable": reachable,
                "unreachable": report["unreachable"],
                "exponent": rows["exponent"]["solved"],
                "address": rows["address"]["solved"],
                "carrier": rows["carrier"]["solved"],
                "none": rows["none"]["solved"],
                "random": rows["random"]["solved"],
                "lean_file": report["lean_file"]})})
