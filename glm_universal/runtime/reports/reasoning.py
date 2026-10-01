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

from ...reasoning import anonymous as anon
from ...reasoning import controller as ctl
from ...reasoning import generative as gen
from ...reasoning import retrieval as rt
from ...reasoning import search_loop as sl
from ...reasoning import stack as sk
from ...reasoning import vision_stack as vs

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

    # -- the multi-part stack, and who carries whom -----------------------

    def _report_relay(self, query: Query) -> Solution:
        """Wires sk.relay_report -- does the stack beat its best faculty?

        The retrieval subject records the negative result that the address
        layer loses to a plain lexical search when it answers alone.  This
        subject asks the question that result does not settle: gated on the
        text layer's own confidence, do the two geometric address books carry
        the queries the text layer cannot read, and does the stack then beat
        the text control?  The controls are a relay to the digest addresses
        and a seeded permutation, and a relay to the name search, so a gain
        from padding a list is separated from a gain from the substrate.  The
        second register is the ARC grids, where the same relay runs over a
        generator, a visual filter and a cross-domain check.
        """
        report = sk.relay_report()
        vision = vs.vision_report()
        sets = report["sets"]
        verdict = report["verdict"]
        k = 5
        carried = sum(len(sets[name]["carried"]) for name in sets)
        lost = sum(len(sets[name]["lost"]) for name in sets)

        def pair(name: str) -> str:
            entry = sets[name]
            return (f"{entry['leader']['hits'][k]} -> "
                    f"{entry['relay']['hits'][k]} of {entry['queries']}")

        def standing(name: str) -> str:
            #  Read off the measurement rather than asserted: the goal set
            #  fell level with the text control when the corpus moved in
            #  Phase 59, and the sentence has to say so when it happens.
            entry = sets[name]
            before, after = entry["leader"]["hits"][k], entry["relay"]["hits"][k]
            return ("ahead" if after > before
                    else "level" if after == before else "behind")

        every = verdict["relay_beats_text_on_every_set"]

        steps = [
            Step("the gate, and what it is for",
                 f"A faculty reports how much evidence it has for *this* "
                 f"query: for the lexical search that is the overlap its best "
                 f"candidate achieves.  Below a gate of {report['gate']} the "
                 f"leader is judged to have abstained and the stack relays to "
                 f"the two address books, taking "
                 f"{', '.join(f'{quota} from {name}' for name, quota in report['quotas'])}.  "
                 f"The gate fires on "
                 f"{sum(sets[name]['fired'] for name in sets)} of "
                 f"{sum(sets[name]['queries'] for name in sets)} queries, so "
                 f"the stack leaves the leader alone almost everywhere "
                 f"-- which is GLM.Relay.relay_confident.",
                 f"gate {report['gate']}, quotas "
                 f"{', '.join(f'{name}:{quota}' for name, quota in report['quotas'])}"),
            Step("the relay beats the control that beat the geometry"
                 if every else
                 "the relay against the control that beat the geometry",
                 f"At k = {k}, against the text control, the relay reads: "
                 f"the tuning stride {pair('tuning')} ({standing('tuning')}), "
                 f"a disjoint held-out stride {pair('holdout')} "
                 f"({standing('holdout')}) and the goal queries "
                 f"{pair('goal')} ({standing('goal')}).  It carries "
                 f"{carried} queries the text control misses and loses "
                 f"{lost}.",
                 f"tuning {pair('tuning')}, holdout {pair('holdout')}, "
                 f"goal {pair('goal')}, carried {carried}, lost {lost}"),
            Step("and the gain is the geometry's",
                 f"The same relay to the digest addresses and a seeded "
                 f"permutation carries "
                 f"{sum(len(report['controls']['digest_random'][name]['carried']) for name in sets)} "
                 f"queries; to the name search, "
                 f"{sum(len(report['controls']['name'][name]['carried']) for name in sets)}.  "
                 f"The mechanism is not padding a list.",
                 f"geometry {carried}, digest+reshuffle "
                 f"{sum(len(report['controls']['digest_random'][name]['carried']) for name in sets)}, "
                 f"name "
                 f"{sum(len(report['controls']['name'][name]['carried']) for name in sets)}"),
            Step("the same stack over grids",
                 f"On the {vision['puzzles']} ARC training puzzles the same "
                 f"relay runs over a generator, a visual filter and a "
                 f"cross-domain check: the cheap look removes "
                 f"{q(vision['filter_saving'])} of "
                 f"{vision['proposed']} proposals before the verification "
                 f"gate sees them, the leading faculty solves "
                 f"{vision['leader_solves']} alone and the relay solves "
                 f"{vision['relay_solves']}.",
                 f"puzzles {vision['puzzles']}, filter "
                 f"{q(vision['filter_saving'])}, leader "
                 f"{vision['leader_solves']}, relay {vision['relay_solves']}"),
        ]

        expected = {
            "gate": q(report["gate"]),
            "corpus": str(report["corpus"]),
            "carried": str(carried),
            "lost": str(lost),
            "vision_puzzles": str(vision["puzzles"]),
            "vision_leader_solves": str(vision["leader_solves"]),
            "vision_relay_solves": str(vision["relay_solves"]),
            "vision_filter_saving": q(vision["filter_saving"]),
            "lean_file": str(report["lean_file"]),
        }
        for name in sets:
            expected[f"{name}_queries"] = str(sets[name]["queries"])
            expected[f"{name}_fired"] = str(sets[name]["fired"])
            expected[f"{name}_leader_hits"] = str(sets[name]["leader"]["hits"][k])
            expected[f"{name}_relay_hits"] = str(sets[name]["relay"]["hits"][k])
        for key, value in verdict.items():
            expected[f"verdict_{key}"] = str(value)

        return Solution(
            query=query, kind="report",
            answer=f"report relay: the machine's faculties arranged as a "
                   f"stack rather than scored one at a time.  Gated on the "
                   f"text layer's own confidence -- below {report['gate']} it "
                   f"is judged to have no evidence for the query -- the two "
                   f"geometric address books carry it, and at k = {k} "
                   f"against the text control the stack reads: the tuning "
                   f"stride {pair('tuning')} ({standing('tuning')}), a "
                   f"disjoint held-out stride {pair('holdout')} "
                   f"({standing('holdout')}) and bare goal queries "
                   f"{pair('goal')} ({standing('goal')}), carrying {carried} "
                   f"queries it misses and losing {lost}.  The same relay to a digest and a "
                   f"reshuffle carries "
                   f"{sum(len(report['controls']['digest_random'][name]['carried']) for name in sets)}, "
                   f"so the gain is the substrate's rather than the list "
                   f"padding's, and the gate fires on only "
                   f"{sum(sets[name]['fired'] for name in sets)} of "
                   f"{sum(sets[name]['queries'] for name in sets)} queries.  "
                   f"In the grid register the same mechanism runs over "
                   f"{vision['puzzles']} ARC puzzles with a generator, a "
                   f"visual filter and a cross-domain check: the filter "
                   f"removes {q(vision['filter_saving'])} of the proposals "
                   f"before the verification gate sees them, and the relay "
                   f"solves {vision['relay_solves']} "
                   f"against the leading faculty's {vision['leader_solves']}",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_relay", "args": {}},
            payload={"report": jsonable({
                "gate": q(report["gate"]),
                "carried": carried,
                "lost": lost,
                "tuning": sets["tuning"]["relay"]["hits"][k],
                "holdout": sets["holdout"]["relay"]["hits"][k],
                "goal": sets["goal"]["relay"]["hits"][k],
                "vision_relay_solves": vision["relay_solves"],
                "lean_file": report["lean_file"]})})

    # -- the loop: propose, check, refuse ---------------------------------

    def _report_anonymous(self, query: Query) -> Solution:
        """Wires anon.anonymous_report -- who reads a query with no names.

        The relay subject shows the geometry carrying a *residue*: a handful
        of queries the text layer cannot read.  This subject asks whether
        there is a register where the carry set is a whole class, and answers
        yes: rename every identifier of a query outside a declared vocabulary
        and the text search and the identifier address book both fall to
        chance, while the structural address keeps most of what it had,
        because renaming cannot move a count of the syntax.
        """
        report = anon.anonymous_report()
        plain = report["plain"]
        after = report["anonymous"]
        relay_after = report["relay_anonymous"]
        verdict = report["verdict"]
        queries = report["queries"]
        k = report["k"]

        def hits(table, faculty: str) -> int:
            return table[faculty]["hits"][k]

        def move(faculty: str) -> str:
            return (f"{hits(plain, faculty)} -> {hits(after, faculty)} "
                    f"of {queries}")

        chance_hits = report["chance_at_5"] * queries
        steps = [
            Step("the register, stated before it is measured",
                 f"A query is *anonymous* when its identifiers are not the "
                 f"corpus's: a goal from another formalisation, a generated "
                 f"goal with no names yet, a statement autoformalised in the "
                 f"vocabulary of its source.  Every identifier outside a "
                 f"declared vocabulary of "
                 f"{len(report['kept_vocabulary'])} words -- Lean's own "
                 f"syntax and the type names the feature map counts -- is "
                 f"replaced by a positional placeholder, and the "
                 f"placeholders are checked to be fresh against the corpus "
                 f"rather than assumed to be.",
                 f"queries {queries}, kept vocabulary "
                 f"{len(report['kept_vocabulary'])}, placeholders fresh "
                 f"{verdict['placeholders_are_fresh']}"),
            Step("what the renaming does to each faculty",
                 f"At k = {k} the text search falls {move('text')} and the "
                 f"identifier address book falls {move('lexical')}, both to "
                 f"the {chance_hits.numerator // chance_hits.denominator} "
                 f"hits chance alone would give; the structural address "
                 f"holds {move('address')}, which is more than twice what "
                 f"any other faculty manages in this register.",
                 f"text {move('text')}, lexical {move('lexical')}, address "
                 f"{move('address')}, digest {move('digest')}, random "
                 f"{move('random')}"),
            Step("why, checked coordinate by coordinate",
                 f"A renaming cannot move a count of the syntax, which is "
                 f"GLM.Anonymous.features_anonymise.  Measured on the "
                 f"shipped feature map rather than on the idealisation: "
                 f"{report['invariant_queries']} of {queries} queries keep "
                 f"every syntax coordinate, and every coordinate that moves "
                 f"on the remaining "
                 f"{queries - report['invariant_queries']} is one of the six "
                 f"that count type words, which the shipped map reads inside "
                 f"identifiers too.",
                 f"invariant {report['invariant_queries']} of {queries}, "
                 f"moved outside the type vocabulary "
                 f"{len(report['queries_moved_outside_the_type_vocabulary'])}"),
            Step("and the stack hands the register over on its own",
                 f"The gate is the one the relay already carries, not "
                 f"re-tuned: it fires on {relay_after['fired']} of "
                 f"{queries} anonymous queries against "
                 f"{report['relay_plain']['fired']} of the same queries read "
                 f"plainly, and the relay lifts the text leader "
                 f"{relay_after['leader']['hits'][k]} -> "
                 f"{relay_after['relay']['hits'][k]}.  With confidence zero "
                 f"that hand-over is a theorem, "
                 f"GLM.Anonymous.relay_hands_over, not a measurement.",
                 f"fired {relay_after['fired']} of {queries}, leader "
                 f"{relay_after['leader']['hits'][k]}, relay "
                 f"{relay_after['relay']['hits'][k]}"),
        ]

        expected = {
            "queries": str(queries),
            "corpus": str(report["corpus"]),
            "chance_at_5": q(report["chance_at_5"]),
            "invariant_queries": str(report["invariant_queries"]),
            "fired": str(relay_after["fired"]),
            "relay_hits": str(relay_after["relay"]["hits"][k]),
            "leader_hits": str(relay_after["leader"]["hits"][k]),
            "lean_file": str(report["lean_file"]),
        }
        for faculty in anon.SCORED:
            expected[f"plain_{faculty}_hits"] = str(hits(plain, faculty))
            expected[f"anonymous_{faculty}_hits"] = str(hits(after, faculty))
        for key, value in verdict.items():
            expected[f"verdict_{key}"] = str(value)

        return Solution(
            query=query, kind="report",
            answer=f"report anonymous: the register where the geometric "
                   f"address is the only faculty left reading.  Rename every "
                   f"identifier of a query outside a declared vocabulary and "
                   f"at k = {k} over {queries} queries the text search falls "
                   f"{move('text')} and the identifier address book "
                   f"{move('lexical')}, both to the "
                   f"{chance_hits.numerator // chance_hits.denominator} hits "
                   f"chance gives, while the structural address holds "
                   f"{move('address')} -- more than twice any other faculty "
                   f"here.  A renaming cannot move a count of the syntax "
                   f"({report['invariant_queries']} of {queries} queries "
                   f"keep every syntax coordinate, and the rest move only "
                   f"the six that count type words), so the stack's existing "
                   f"gate fires on {relay_after['fired']} of {queries} and "
                   f"lifts the leader "
                   f"{relay_after['leader']['hits'][k]} -> "
                   f"{relay_after['relay']['hits'][k]}.  The carry set is a "
                   f"class, not a residue",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_anonymous", "args": {}},
            payload={"report": jsonable({
                "queries": queries,
                "text": hits(after, "text"),
                "lexical": hits(after, "lexical"),
                "address": hits(after, "address"),
                "fired": relay_after["fired"],
                "invariant_queries": report["invariant_queries"],
                "lean_file": report["lean_file"]})})

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

    # -- generate, don't store: the zero-storage substrate, measured ------

    def _report_generated(self, query: Query) -> Solution:
        """Wires gen.zero_storage_report -- what can be generated, and is it right?

        The zero-storage proposal is that the substrate should stop holding
        tables and start regenerating them: the lattice from an arithmetic
        sieve at the moment of the snap, a real number from a process, a
        register from a running loop.  This subject measures the proposal
        against the package's own exact instruments -- the sieve against all
        196,560 minimal vectors, the snap against an exact coset decoder, the
        closed-form constants against certified processes -- and then asks
        the same question of the overlay's own stored files.
        """
        report = gen.zero_storage_report(4)
        sieve = report["sieve"]
        fix = report["fix"]
        snap = report["snap"]
        near = report["snap_near"]
        storage = report["storage"]
        repo = report["repo"]
        reals = report["exact_real"]
        sextet = report["sextet"]
        verdict = report["verdict"]
        by_bits = {row["constant"]: row for row in reals["rows"]}

        steps = [
            Step("generating the lattice is the right idea",
                 f"Membership of Lambda is three congruences on 24 integers, "
                 f"so the {sieve['minimal_vectors']} minimal vectors never "
                 f"have to be held: a stored shell costs "
                 f"{storage['rows'][2]['stored_bytes']} bytes and the "
                 f"generator that decides membership costs "
                 f"{storage['rows'][2]['generator_bytes']} -- the Golay code, "
                 f"itself regenerated from 12 rows and "
                 f"checked identical to the stored code.  Over the whole "
                 f"table the ratio is {q(storage['ratio'])} to one, and every "
                 f"regenerated object was compared with the stored one before "
                 f"the row was emitted: {storage['all_verified']}.",
                 f"stored {storage['stored_bytes']} bytes, generator "
                 f"{storage['generator_bytes']}, ratio {q(storage['ratio'])}, "
                 f"all verified {storage['all_verified']}"),
            Step("but the proposed sieve is not the lattice",
                 f"The sieve keeps a vector when all 24 coordinates agree "
                 f"mod 4.  That is sound -- {sieve['unsound']} of the vectors "
                 f"it keeps are outside Lambda -- and it is not the Golay "
                 f"condition of Construction C, which asks that the "
                 f"coordinates which *disagree* form a codeword.  Run against "
                 f"the kissing shell it keeps {sieve['kept']} of "
                 f"{sieve['minimal_vectors']}: every "
                 f"(4^2, 0^22) vector, 48 of the 98,304 odd ones, and none at "
                 f"all of the 97,152 octad vectors.  Lean: v3Sieve_sound and "
                 f"v3Sieve_iff in RequestProject/GLM/ZeroStorage.lean, with "
                 f"octadVec the rejected minimal vector.",
                 f"kept {sieve['kept']}/{sieve['minimal_vectors']}, recall "
                 f"{q(sieve['recall'])}, unsound {sieve['unsound']}"),
            Step("the repair is one line, and it is exact",
                 f"Replacing 'all coordinates agree mod 4' by 'the "
                 f"disagreeing coordinates form a Golay codeword' restores "
                 f"the defining congruences at the same cost.  The repaired "
                 f"sieve was compared with the package's own membership test "
                 f"on {fix['checked']} vectors -- the whole shell plus probe "
                 f"vectors in general position, {fix['probe_vectors_outside_lattice']} "
                 f"of which are outside the lattice -- and agreed every time: "
                 f"{fix['exact']}.",
                 f"checked {fix['checked']}, agree {fix['agree']}, exact "
                 f"{fix['exact']}"),
            Step("and the generated snap does not snap",
                 f"The proposed snap rounds, probes one coordinate at a time, "
                 f"and falls back to 'round every coordinate to the nearest "
                 f"even integer'.  On {snap['probes']} targets in general "
                 f"position it returned a point outside the lattice "
                 f"{snap['v3_outside_lattice']} times, at squared distance up "
                 f"to {q(snap['worst_excess_dist2'])} beyond the true nearest "
                 f"point; on {near['probes']} targets half a step from a "
                 f"genuine minimal vector, {near['v3_outside_lattice']}.  The "
                 f"exact coset decoder beside it answered inside the lattice "
                 f"every time ({snap['exact_all_in_lattice']}) and within the "
                 f"covering radius squared of {snap['covering_radius2']} "
                 f"({snap['exact_within_covering_radius']}), which is the "
                 f"check that it really is the nearest point.  Lean: "
                 f"fallbackVec_not_isLeech.",
                 f"v3 outside {snap['v3_outside_lattice']}/{snap['probes']} "
                 f"general, {near['v3_outside_lattice']}/{near['probes']} "
                 f"near; exact in lattice {snap['exact_all_in_lattice']}"),
            Step("a generated number is only as good as its cost bound",
                 f"Machin's pi and the Taylor e are exactly what they claim.  "
                 f"The Babylonian sqrt is not: its own docstring promises "
                 f"about 2^k bits after k steps and ten steps deliver "
                 f"{by_bits['sqrt2 (Babylonian, 10 steps)']['bits_correct']}, "
                 f"while the denominator of the iterate doubles in length "
                 f"every step ({reals['babylonian_doubles']}), so the "
                 f"module's own default of {reals['default_iterations']} "
                 f"iterations is unrunnable.  The alternating ln2 at "
                 f"precision 64 yields "
                 f"{by_bits['ln2 (alternating, precision=64)']['bits_correct']} "
                 f"bits, and the Euler-Mascheroni generator -- which rounds "
                 f"log n to a bit length -- yields "
                 f"{by_bits['gamma (H_n - ln2*bit_length, precision=8)']['bits_correct']}.  "
                 f"{reals['claims_met']} of {reals['claims_made']} stated "
                 f"accuracy claims hold.  A process is a number only when the "
                 f"error is a function of the work, which is what "
                 f"ExactReal.at(k) is for.",
                 f"claims met {reals['claims_met']}/{reals['claims_made']}, "
                 f"babylonian denominator doubles "
                 f"{reals['babylonian_doubles']}"),
            Step("the deep-hole 'portal' is a real invariant with a constant label",
                 f"At each of the {sextet['weight4_words_checked']} weight-4 "
                 f"words checked there are exactly six codewords at distance "
                 f"4 and none closer ({sextet['sextet_confirmed']}), and "
                 f"their pairwise distances are all 8 "
                 f"({sextet['pairwise_distance_8']}): the sextet is genuine.  "
                 f"What it is not is a Niemeier identification -- the "
                 f"detector's output takes "
                 f"{sextet['distinct_detector_outputs']} distinct value over "
                 f"those words, and a constant separates nothing.  The "
                 f"instrument that does read a hole's diagram is "
                 f"reasoning/deep_holes.py.",
                 f"sextets {sextet['sextet_confirmed']}/"
                 f"{sextet['weight4_words_checked']}, distinct outputs "
                 f"{sextet['distinct_detector_outputs']}"),
            Step("and the same question, asked of this package",
                 f"Of the {repo['total_bytes']} bytes the overlay keeps on "
                 f"disk, {repo['generated_bytes']} are caches of things it "
                 f"can recompute -- the address books from the Lean tree, the "
                 f"type-2 table from the lattice -- each stored beside the "
                 f"digest of the inputs it came from, and only "
                 f"{repo['primary_bytes']} are primary data it was given.  "
                 f"The generate-don't-store principle is already how this "
                 f"system holds {q(repo['generated_fraction'])} of its bytes; "
                 f"what the audit adds is that a generator has to be checked "
                 f"against what it replaces.",
                 f"generated {repo['generated_bytes']} bytes, primary "
                 f"{repo['primary_bytes']}, fraction "
                 f"{q(repo['generated_fraction'])}"),
        ]

        expected = {
            "minimal_vectors": str(sieve["minimal_vectors"]),
            "sieve_kept": str(sieve["kept"]),
            "sieve_unsound": str(sieve["unsound"]),
            "sieve_recall": q(sieve["recall"]),
            "fix_checked": str(fix["checked"]),
            "fix_agree": str(fix["agree"]),
            "fix_exact": str(fix["exact"]),
            "snap_probes": str(snap["probes"]),
            "snap_outside": str(snap["v3_outside_lattice"]),
            "snap_near_outside": str(near["v3_outside_lattice"]),
            "exact_all_in_lattice": str(snap["exact_all_in_lattice"]),
            "exact_within_covering_radius":
                str(snap["exact_within_covering_radius"]),
            "storage_stored_bytes": str(storage["stored_bytes"]),
            "storage_generator_bytes": str(storage["generator_bytes"]),
            "storage_ratio": q(storage["ratio"]),
            "storage_all_verified": str(storage["all_verified"]),
            "repo_generated_bytes": str(repo["generated_bytes"]),
            "repo_primary_bytes": str(repo["primary_bytes"]),
            "repo_generated_fraction": q(repo["generated_fraction"]),
            "claims_met": str(reals["claims_met"]),
            "claims_made": str(reals["claims_made"]),
            "babylonian_doubles": str(reals["babylonian_doubles"]),
            "sextet_confirmed": str(sextet["sextet_confirmed"]),
            "sextet_distinct_outputs":
                str(sextet["distinct_detector_outputs"]),
        }
        for key, value in verdict.items():
            expected[f"verdict_{key}"] = str(value)

        return Solution(
            query=query, kind="report",
            answer=f"report generated: how much of the substrate can be "
                   f"generated instead of stored, and whether the generated "
                   f"copy is the same object.  Generating is right in "
                   f"principle -- the stored tables audited here cost "
                   f"{storage['stored_bytes']} bytes against "
                   f"{storage['generator_bytes']} for their generators, a "
                   f"ratio of {q(storage['ratio'])} to one, every regenerated "
                   f"object checked identical -- and "
                   f"{q(repo['generated_fraction'])} of the overlay's own "
                   f"stored bytes are already caches with a digest.  But the "
                   f"proposed on-the-fly Leech sieve is sound and badly "
                   f"incomplete: it keeps {sieve['kept']} of the "
                   f"{sieve['minimal_vectors']} minimal vectors, because "
                   f"'all coordinates agree mod 4' is not the Golay condition "
                   f"of Construction C; the repaired sieve agrees with the "
                   f"package's membership test on all {fix['checked']} "
                   f"vectors tested.  The snap built on it returned a "
                   f"non-lattice point on {snap['v3_outside_lattice']} of "
                   f"{snap['probes']} targets in general position, where an "
                   f"exact coset decoder is always inside and within the "
                   f"covering radius.  Of the script's closed-form constants "
                   f"{reals['claims_met']} of {reals['claims_made']} accuracy "
                   f"claims hold.  The general statements are proved in "
                   f"RequestProject/GLM/ZeroStorage.lean",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_generated", "args": {}},
            payload={"report": jsonable({
                "minimal_vectors": sieve["minimal_vectors"],
                "sieve_kept": sieve["kept"],
                "sieve_unsound": sieve["unsound"],
                "fix_exact": fix["exact"],
                "snap_outside": snap["v3_outside_lattice"],
                "storage_ratio": storage["ratio"],
                "repo_generated_fraction": repo["generated_fraction"],
                "lean_file": "RequestProject/GLM/ZeroStorage.lean"})})
