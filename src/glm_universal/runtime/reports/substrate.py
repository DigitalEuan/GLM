"""``glm_universal.runtime.reports.substrate``
-- the subjects the substrate computes.

Reports read off :mod:`glm_universal.substrate`.

The Leech lattice's own arithmetic: the pair census and the theta series,
the Golay decoder and the coset it lands in, the superposition of tied
hypotheses, and the two constructions -- the lattice built from the code,
and the frame permutation that carries the legacy labelling onto the core.

Every method here is a solver for one ``report <subject>`` query.  They are
mixed into :class:`glm_universal.runtime.session.GeometricSession`,
which is where ``self`` comes from: the loaded registers, the concept index
and the shared helpers.  Splitting them out of the session keeps each family
beside a docstring that says which sub-package computes it, and keeps the
dispatcher readable as a dispatcher.
"""
from __future__ import annotations

from ...substrate import golay_decode as gdc
from ...substrate import leech2
from ...substrate import leech_construct as lcs
from ...substrate import superposition as sup

from ..parser import Query
from ..solution import Solution, Step


class SubstrateReports:
    """The subjects the substrate computes.

    A mixin of :class:`~glm_universal.runtime.session.GeometricSession`;
    it holds no state of its own.
    """

    def _report_leech_distribution(self, query: Query) -> Solution:
        """Wires leech2.pair_census — the 4-position Leech distribution."""
        census = leech2.pair_census()
        steps = [
            Step("pair_census",
                 f"The 196,560 minimal vectors of the Leech lattice, "
                 f"taken against any fixed one, fall into exactly four "
                 f"mutual positions.  This is the reason the Monster's 2A "
                 f"axes have only four positions: 1A (2 vectors), 2A "
                 f"(9,200), invariant-1 (94,208, not modelled), and 2B "
                 f"(93,150).",
                 f"pair_census = {dict(census)}"),
        ]
        expected = {f"position_{k}": str(v) for k, v in census.items()}
        return Solution(
            query=query, kind="report",
            answer=f"report leech distribution: {dict(census)}",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_leech", "args": {}},
            payload={"census": dict(census)})

    def _report_theta(self, query: Query) -> Solution:
        """Wires leech2.theta_series — the Leech theta series E_4^3 - 720*Delta."""
        order = 5
        coeffs = leech2.theta_series(order=order)
        steps = [
            Step("theta_series",
                 f"The theta series of the Leech lattice is "
                 f"E_4^3 - 720*Delta, computed exactly.  Coefficient n "
                 f"counts vectors of squared norm 8n.  The first few: "
                 f"1 (the zero vector), 0 (no norm-8 vectors), 196560 "
                 f"(the minimal vectors, norm 16 = 8*2), 16773120 "
                 f"(norm 24 = 8*3), ...",
                 f"theta = {coeffs}"),
        ]
        expected = {f"coeff_{i}": str(c) for i, c in enumerate(coeffs)}
        return Solution(
            query=query, kind="report",
            answer=f"report theta: {coeffs}",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_theta", "args": {}},
            payload={"coefficients": coeffs, "order": order})

    # ------------------------------------------------------------------
    # 3k-bis.  the five report subjects added in v0.8.0
    # ------------------------------------------------------------------
    # Each of these wires a substrate or reasoning module that had been
    # built but was not reachable from a query.  They follow the same
    # contract as the older report subjects: recompute, state the facts
    # as steps, and put only independently reproducible scalars into
    # ``expected``.
    # ------------------------------------------------------------------

    def _report_golay_decoding(self, query: Query) -> Solution:
        """Wires gdc.golay_decode_report -- complete decoding, no silent snap."""
        report = gdc.golay_decode_report()
        census = report["coset_census"]
        steiner = report["steiner"]
        weight5 = report["weight5"]
        rows = {row["weight"]: row for row in report["comparison"]["rows"]}
        flagged_at_4 = rows[4]["complete"]["flagged"]
        silent_at_4 = rows[4]["legacy_ties_broken_silently"]

        steps = [
            Step("coset table",
                 f"The 4,096 cosets of the Golay code were enumerated and "
                 f"each given its full set of minimum-weight leaders.  Below "
                 f"the packing radius {report['packing_radius']} the leader "
                 f"is unique; at the covering radius "
                 f"{report['covering_radius']} every coset has a sextet of "
                 f"six leaders, so no nearest codeword is singled out.",
                 f"cosets = {census['cosets']}, "
                 f"leaders = {census['total_leaders']}, "
                 f"by leader weight = {census['cosets_by_leader_weight']}"),
            Step("decode or detect",
                 f"The complete decoder returns every nearest codeword and a "
                 f"status.  On the {flagged_at_4} sampled weight-4 patterns "
                 f"it reports ambiguity; the retired snap decoder returned "
                 f"one of the six silently in all {silent_at_4} of them.",
                 f"weight 4: complete flagged {flagged_at_4}, "
                 f"legacy silent tie-breaks {silent_at_4}"),
            Step("why weight 5 is not a bug",
                 f"Every 5-subset of the 24 points lies in exactly one octad "
                 f"-- the Steiner system S(5,8,24), verified here on all "
                 f"{steiner['five_subsets_total']} of them.  A weight-5 "
                 f"error is therefore the complement inside that octad of a "
                 f"weight-3 error, so it sits at distance 3 from a codeword "
                 f"and is decoded confidently and wrongly by any "
                 f"nearest-codeword rule.  The remedy is a declared channel "
                 f"radius, not a better decoder.",
                 f"octads = {steiner['octads']}, "
                 f"multiplicities = {steiner['multiplicities']}, "
                 f"weight-5 coset weights = {weight5['coset_weights']}"),
        ]
        expected = {
            "cosets": str(census["cosets"]),
            "total_leaders": str(census["total_leaders"]),
            "unique_below_radius_4": str(census["unique_below_radius_4"]),
            "sextet_at_radius_4": str(census["sextet_at_radius_4"]),
            "packing_radius": str(report["packing_radius"]),
            "covering_radius": str(report["covering_radius"]),
            "codewords": str(report["codewords"]),
            "octads": str(steiner["octads"]),
            "is_steiner_5_8_24": str(steiner["is_steiner_5_8_24"]),
            "weight5_always_coset_weight_3":
                str(weight5["always_coset_weight_3"]),
            "weight5_always_miscorrected":
                str(weight5["always_miscorrected"]),
            "silent_tie_breaking_retired":
                str(report["silent_tie_breaking_retired"]),
        }
        return Solution(
            query=query, kind="report",
            answer=f"report golay decoding: {census['cosets']} cosets, "
                   f"{census['total_leaders']} leaders, unique below weight "
                   f"4 and a sextet of six at weight 4; S(5,8,24) verified "
                   f"on {steiner['five_subsets_total']} five-subsets, so "
                   f"weight-5 miscorrection is a theorem, not a bug",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_golay_decoding", "args": {}},
            payload={"report": report})

    def _report_superposition(self, query: Query) -> Solution:
        """Wires sup.superposition_report -- the tie carried, not broken."""
        report = sup.superposition_report()
        sextet = report["sextet"]
        bundling = report["bundling"]
        collapsed = report["collapse"]
        census = report["census"]
        chain = report["chain"]
        hull = report["hull"]

        steps = [
            Step("the tie is a sextet",
                 f"At the covering radius the nearest-codeword reading has "
                 f"exactly {report['tie_count']} answers.  Their error "
                 f"patterns are six disjoint tetrads covering all 24 "
                 f"coordinates -- a MOG sextet -- checked here on "
                 f"{sextet['tetrads_checked']} received words.",
                 f"leader counts = {sextet['leader_counts']}, "
                 f"disjoint = {sextet['pairwise_disjoint']}, "
                 f"covers 24 = {sextet['covers_all_24']}"),
            Step("bundling: the two rules do not agree",
                 f"Bundling the six candidates by F_2 symmetric difference "
                 f"gives the all-ones word for every received word, so it "
                 f"distinguishes {bundling['f2_bundle_distinguishes']} of the "
                 f"{bundling['words_checked']} words checked.  Bundling them "
                 f"by exact rational addition gives (1 + 4 v)/6 "
                 f"coordinatewise, which is invertible: it distinguishes all "
                 f"{bundling['rational_bundle_distinguishes']}, and the "
                 f"received word is recovered from the bundle.",
                 f"F_2 bundle = {bundling['f2_bundle_values']}, "
                 f"rational coordinates = "
                 f"{bundling['rational_bundle_coordinate_values']}, "
                 f"recovers input = "
                 f"{bundling['rational_bundle_recovers_input']}"),
            Step("collapse is a measurement, not a coin flip",
                 f"A downstream context filters the hypothesis space: a "
                 f"selective one collapses it to a single codeword, a "
                 f"permissive one leaves it standing, an incompatible one "
                 f"refutes the read.  No tie is broken by enumeration order.",
                 f"collapsed = {collapsed['collapsed']['status']}, "
                 f"superposed = {collapsed['superposed']['status']}, "
                 f"refuted = {collapsed['refuted']['status']}"),
            Step("how often the tie happens",
                 f"Counting the cosets rather than describing one: the "
                 f"{census['cosets']} cosets sit at distances "
                 f"{census['cosets_by_distance']} from the code, so "
                 f"{census['uniquely_read_cosets']} are read uniquely and "
                 f"{census['ambiguous_cosets']} are six-fold ties, and the "
                 f"mean distance to the code is exactly "
                 f"{census['mean_coset_weight']}.  That is strictly past the "
                 f"packing radius {census['packing_radius']} and strictly "
                 f"inside the covering radius {census['covering_radius']}: "
                 f"the average word already sits outside the radius within "
                 f"which the reading is unique, so ambiguity is the typical "
                 f"case for this code rather than a corner case.",
                 f"mean coset weight = {census['mean_coset_weight']}, "
                 f"ambiguous fraction = {census['ambiguous_fraction']}, "
                 f"agrees with Lean = "
                 f"{census['census_agrees_with_lean']} / "
                 f"{census['mean_agrees_with_lean']}"),
            Step("the dynamical half: no, it does not settle",
                 f"A carrier under repeated one-bit perturbation is a random "
                 f"walk on the {chain['states']} cosets.  Its unique "
                 f"stationary law is the uniform one, whose mean distance to "
                 f"the code is the census figure "
                 f"{chain['stationary_mean_distance']} -- but the walk has no "
                 f"limiting law at all: every parity-check column has odd "
                 f"parity, so after n ticks the law sits on one of the two "
                 f"parity classes and never on both.  Only the time average "
                 f"settles: after {chain['steps']} exact ticks the two-step "
                 f"average is "
                 f"{chain['two_step_average_mean_distance']}, within "
                 f"{chain['two_step_average_error']} of the stationary mean.  "
                 f"And if each perturbation is corrected, the carrier returns "
                 f"to the same codeword and stays at distance "
                 f"{chain['corrected_distance_after_correction']}: correction "
                 f"destroys the criticality rather than maintaining it.",
                 f"support by step = {chain['support_by_step']}, "
                 f"parity alternates = {chain['parity_alternates']}, "
                 f"two-step average error = "
                 f"{chain['two_step_average_error']}, "
                 f"corrected carrier returns = "
                 f"{chain['corrected_carrier_returns_to_code']}"),
            Step("widening the alphabet",
                 f"The functional 7 x_0 - sum_(j != 0) x_j is <= 0 on all "
                 f"{hull['codewords_checked']} codewords, hence on every "
                 f"non-negative multiple of one, while it is "
                 f"{hull['value_at_target']} at the target (1/2) e_0.  "
                 f"Scaling the emitted alphabet therefore changes nothing; "
                 f"admitting two minimal Leech vectors of shape (+-4^2, "
                 f"0^22) reaches the same target exactly, at every completed "
                 f"{hull['leech_cycle_length']}-tick cycle.",
                 f"max over scaled codewords = "
                 f"{hull['max_over_scaled_codewords']}, "
                 f"value at target = {hull['value_at_target']}, "
                 f"Leech cycle reaches target = "
                 f"{hull['leech_cycle_reaches_target']}"),
        ]
        expected = {
            "tie_count": str(report["tie_count"]),
            "pairwise_disjoint": str(sextet["pairwise_disjoint"]),
            "covers_all_24": str(sextet["covers_all_24"]),
            "f2_bundle_is_all_ones": str(bundling["f2_bundle_is_all_ones"]),
            "f2_bundle_distinguishes":
                str(bundling["f2_bundle_distinguishes"]),
            "rational_bundle_recovers_input":
                str(bundling["rational_bundle_recovers_input"]),
            "rational_bundle_distinguishes":
                str(bundling["rational_bundle_distinguishes"]),
            "collapse_status": str(collapsed["collapsed"]["status"]),
            "refuted_status": str(collapsed["refuted"]["status"]),
            "cosets": str(census["cosets"]),
            "cosets_by_distance": str(census["cosets_by_distance"]),
            "mean_coset_weight": str(census["mean_coset_weight"]),
            "uniquely_read_cosets": str(census["uniquely_read_cosets"]),
            "ambiguous_cosets": str(census["ambiguous_cosets"]),
            "ambiguous_fraction": str(census["ambiguous_fraction"]),
            "mean_exceeds_packing_radius":
                str(census["mean_exceeds_packing_radius"]),
            "mean_below_covering_radius":
                str(census["mean_below_covering_radius"]),
            "census_agrees_with_lean":
                str(census["census_agrees_with_lean"]),
            "mean_agrees_with_lean": str(census["mean_agrees_with_lean"]),
            "chain_states": str(chain["states"]),
            "columns_all_odd_parity": str(chain["columns_all_odd_parity"]),
            "uniform_is_stationary": str(chain["uniform_is_stationary"]),
            "parity_alternates": str(chain["parity_alternates"]),
            "law_never_uniform": str(chain["law_never_uniform"]),
            "settles_in_distribution": str(chain["settles_in_distribution"]),
            "two_step_average_mean_distance":
                str(chain["two_step_average_mean_distance"]),
            "two_step_average_error": str(chain["two_step_average_error"]),
            "corrected_carrier_returns_to_code":
                str(chain["corrected_carrier_returns_to_code"]),
            "corrected_distance_after_correction":
                str(chain["corrected_distance_after_correction"]),
            "codewords_checked": str(hull["codewords_checked"]),
            "max_over_scaled_codewords":
                str(hull["max_over_scaled_codewords"]),
            "value_at_target": str(hull["value_at_target"]),
            "leech_cycle_reaches_target":
                str(hull["leech_cycle_reaches_target"]),
        }
        return Solution(
            query=query, kind="report",
            answer=f"report superposition: the covering-radius tie has "
                   f"{report['tie_count']} candidates whose error patterns "
                   f"partition the 24 coordinates; XOR-bundling them is the "
                   f"constant all-ones word, rational bundling is the "
                   f"invertible (1 + 4 v)/6 and recovers the read; context "
                   f"collapses, holds or refutes; "
                   f"{census['ambiguous_cosets']} of the {census['cosets']} "
                   f"cosets are such ties and the mean distance to the code "
                   f"is {census['mean_coset_weight']}, past the packing "
                   f"radius, though the perturbation chain has no limiting "
                   f"law and settles only on average; and widening the "
                   f"emitted "
                   f"alphabet by scale reaches nothing new while widening it "
                   f"by support reaches (1/2) e_0 exactly",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_superposition", "args": {}},
            payload={"report": report})

    def _report_leech_construction(self, query: Query) -> Solution:
        """Wires lcs.leech_construction_report -- the A/B/C ladder."""
        report = lcs.leech_construction_report()
        kissing = report["kissing_by_level"]
        norms = report["minimal_norm_by_level"]
        shapes = report["levels"]["C"]["shapes"]
        necessity = report["necessity"]
        agreement = report["agreement_with_leech2"]

        steps = [
            Step("construction A",
                 f"Construction A lifts the Golay code mod 2 alone.  It is a "
                 f"lattice, but its minimum is {norms['A']} and only "
                 f"{kissing['A']} vectors attain it -- the coordinate "
                 f"vectors +-4 e_i.  That is the simplification this report "
                 f"removes.",
                 f"min norm^2 = {norms['A']}, kissing = {kissing['A']}"),
            Step("construction B and the mod-8 sum",
                 f"Requiring the coordinates mod 4 to form a Golay codeword "
                 f"and the coordinate sum to vanish mod 8 kills +-4 e_i and "
                 f"lifts the minimum to {norms['B']}, with {kissing['B']} "
                 f"minimal vectors.",
                 f"min norm^2 = {norms['B']}, kissing = {kissing['B']}"),
            Step("construction C",
                 f"Adjoining the odd coset -- all coordinates odd, again "
                 f"with the Golay and mod-8 conditions -- contributes "
                 f"{report['odd_coset_contribution']} further minimal "
                 f"vectors and restores the true kissing number "
                 f"{kissing['C']}.",
                 f"shapes = {shapes}, kissing = {kissing['C']}"),
            Step("each condition is necessary",
                 f"Dropping the mod-4 Golay condition admits (2, -2, 0^22) "
                 f"and the minimum falls to "
                 f"{necessity['drop_mod4_golay']['minimal_norm2']}; "
                 f"dropping the mod-8 sum readmits +-4 e_i and the minimum "
                 f"falls to {necessity['drop_mod8_sum']['minimal_norm2']}.",
                 f"drop mod-4 Golay: min norm^2 = "
                 f"{necessity['drop_mod4_golay']['minimal_norm2']}; "
                 f"drop mod-8 sum: min norm^2 = "
                 f"{necessity['drop_mod8_sum']['minimal_norm2']}, "
                 f"kissing = {necessity['drop_mod8_sum']['count_at_minimum']}"),
            Step("agreement with the substrate",
                 f"On {agreement['checked']} sampled vectors the ladder's "
                 f"membership test agrees with the package's own Leech "
                 f"predicate in every case, so the construction is the same "
                 f"lattice the rest of the system uses.",
                 f"checked = {agreement['checked']}, "
                 f"disagreements = {agreement['disagreements']}"),
        ]
        expected = {
            "kissing_A": str(kissing["A"]),
            "kissing_B": str(kissing["B"]),
            "kissing_C": str(kissing["C"]),
            "min_norm2_A": str(norms["A"]),
            "min_norm2_B": str(norms["B"]),
            "min_norm2_C": str(norms["C"]),
            "odd_coset_contribution": str(report["odd_coset_contribution"]),
            "construction_C_is_196560":
                str(report["construction_C_is_196560"]),
            "drop_mod4_golay_min_norm2":
                str(necessity["drop_mod4_golay"]["minimal_norm2"]),
            "drop_mod8_sum_min_norm2":
                str(necessity["drop_mod8_sum"]["minimal_norm2"]),
            "agrees_with_leech2": str(agreement["agrees"]),
        }
        return Solution(
            query=query, kind="report",
            answer=f"report leech construction: A gives {kissing['A']} "
                   f"minimal vectors, B gives {kissing['B']}, and C with the "
                   f"mod-8 sum condition gives {kissing['C']} at norm^2 "
                   f"{norms['C']}",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_leech_construction",
                         "args": {}},
            payload={"report": report})
