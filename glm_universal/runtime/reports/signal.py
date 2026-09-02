"""``glm_universal.runtime.reports.signal``
-- the subjects that read a signal, exactly.

Reports about signals, noise and the arithmetic of a machine word.

The noise laboratory, the spectral signature of a constant, the prime
iteration drift, the container census behind the first companion study,
the exact IEEE-754 model, the reversible-computing part, the thermodynamic
carrier engine, and the values that are processes rather than carriers.

Every method here is a solver for one ``report <subject>`` query.  They are
mixed into :class:`glm_universal.runtime.session.GeometricSession`,
which is where ``self`` comes from: the loaded registers, the concept index
and the shared helpers.  Splitting them out of the session keeps each family
beside a docstring that says which sub-package computes it, and keeps the
dispatcher readable as a dispatcher.
"""
from __future__ import annotations

from ...reasoning import containers as con
from ...reasoning import drift as dft
from ...reasoning import engine as eng
from ...reasoning import exact_real as xr
from ...reasoning import mantissa as mn
from ...reasoning import noise_lab as nlb
from ...reasoning import reversible as rv
from ...reasoning import wobble as wbl

from ..payload import containers_payload, drift_payload, noise_payload
from ..parser import Query
from ..solution import Solution, Step, q


class SignalReports:
    """The subjects that read a signal, exactly.

    A mixin of :class:`~glm_universal.runtime.session.GeometricSession`;
    it holds no state of its own.
    """

    def _report_noise(self, query: Query) -> Solution:
        """Wires nlb.noise_report -- noise used as the computation.

        Five measurements, each bound to a theorem of
        ``RequestProject/GLM/Cascade.lean`` or
        ``RequestProject/GLM/Feedback.lean``: the loop tracking a signal
        rather than a constant, the condition under which its orbit closes,
        what a second cascaded loop buys, what dither costs, and what happens
        when several coordinates are modulated at once with the error fed
        back through a rational matrix.
        """
        report = nlb.noise_report()
        track = report["signal_tracking"]
        closing = report["orbit_closure"]["closing"]
        open_orbit = report["orbit_closure"]["not_closing"]
        cascade = report["cascade"]
        table = report["convergence_third"]
        half = report["convergence_half"]
        sweep = report["dither_sweep"]
        feedback = report["feedback"]
        tracking = feedback["tracking"]
        equivariant = feedback["equivariant"]
        asymmetric = feedback["not_equivariant"]
        dead = feedback["dead_zone"]
        widest = table[-1]

        steps = [
            Step("a loop that chases a signal",
                 f"The quantiser is driven by {track['signal']} -- two tones "
                 f"added together, so the input moves at every tick and beats "
                 f"with period {track['period']}.  The emitted bits still "
                 f"track the input's running mean: the accumulator stayed "
                 f"inside [0, 1) for the whole run, which is what bounds the "
                 f"error.",
                 f"mean input = {q(track['input_mean'])}, "
                 f"mean bits = {q(track['bit_mean'])}, "
                 f"error = {q(track['error'])} <= 1/{track['ticks']} "
                 f"({track['within_bound']})"),
            Step("when the wobble closes its orbit",
                 f"A periodic input whose sum over one period is a whole "
                 f"number empties the accumulator at the end of every period, "
                 f"so the trajectory is a closed cycle; when the period sum "
                 f"is not whole, it never closes.  Both cases are run, and "
                 f"the criterion is checked against what happened rather "
                 f"than assumed.",
                 f"{closing['signal']}: period sum {q(closing['period_sum'])}, "
                 f"orbit closed {closing['orbit_closed']}; "
                 f"{open_orbit['signal']}: period sum "
                 f"{q(open_orbit['period_sum'])}, orbit closed "
                 f"{open_orbit['orbit_closed']}"),
            Step("what a second loop buys",
                 f"Stage two modulates stage one's error and the outputs "
                 f"recombine, which leaves the error as a *second* difference "
                 f"of a bounded sequence.  That identity is checked at every "
                 f"one of the {cascade['ticks']} ticks, and the doubly "
                 f"accumulated error is checked to be exactly stage two's "
                 f"state -- bounded by 1 however long the loop runs.",
                 f"second difference holds {cascade['second_difference_holds']}"
                 f", double sum = {q(cascade['double_sum'])} "
                 f"(= state: {cascade['double_sum_equals_state']}), "
                 f"alphabet {list(cascade['alphabet'])}"),
            Step("the order it is worth",
                 f"Read through a triangular window, the cascade converges an "
                 f"order faster than a single loop.  On the target 1/3 the "
                 f"single loop's error is exactly {widest['window'] - 1} "
                 f"times the cascade's at the widest window measured; on 1/2 "
                 f"the cascade is exact and the single loop is not.",
                 f"M = {widest['window']}: cascade "
                 f"{q(widest['cascade_error'])} <= "
                 f"{q(widest['cascade_bound'])}, single loop "
                 f"{q(widest['single_loop_error'])}, ratio "
                 f"{widest['ratio_single_to_cascade']}; on 1/2 cascade "
                 f"{q(half[-1]['cascade_error'])} against single loop "
                 f"{q(half[-1]['single_loop_error'])}"),
            Step("what dither costs",
                 f"A rational target drives the loop into a cycle, and a "
                 f"cycle is a line in the spectrum.  Subtractive dither from "
                 f"an equidistributed sequence breaks it up: the Walsh peak "
                 f"falls monotonically as the dither is driven harder "
                 f"({sweep['monotone_in_amplitude']}), and what it costs -- "
                 f"the bias the dither's own mean leaves behind -- is "
                 f"computed rather than assumed to vanish.",
                 f"undithered peak "
                 f"{q(sweep['undithered_peak_fraction'])} of the window; "
                 f"lowest dithered peak "
                 f"{q(sweep['lowest_peak_fraction'])} over "
                 f"{sweep['amplitudes_tried']} amplitudes; bias at "
                 f"amplitude {q(report['dither']['amplitude'])} = "
                 f"{q(report['dither']['bias'])}"),
            Step("error feedback through a matrix, and the symmetry it keeps",
                 f"The same loop on {tracking['dim']} coordinates at once, "
                 f"with each tick's quantisation error returned through a "
                 f"rational matrix A.  At A = 1 every coordinate tracks its "
                 f"own input to 1/(2N), which is sharper than the scalar "
                 f"accumulator's 1/N; contracting the feedback to A = 1/2 "
                 f"does not merely slow it down, it kills the loop -- on the "
                 f"constant 1/4 the quantiser never fires and the error "
                 f"stays at {q(dead['contracting_error'])} for ever.  A "
                 f"permutation that leaves A invariant permutes the whole "
                 f"trajectory tick for tick, and one that does not is run "
                 f"beside it so the hypothesis is seen to be doing work.",
                 f"coordinate errors "
                 f"{[q(e) for e in tracking['coordinate_errors']]} <= "
                 f"{q(tracking['bound'])} "
                 f"({tracking['within_bound']}); dead zone fires "
                 f"{dead['identity_fires']} at A = 1 against "
                 f"{not dead['contracting_outputs_all_zero']} at A = 1/2; "
                 f"equivariance {equivariant['outputs_permute']} when A is "
                 f"invariant, {asymmetric['outputs_permute']} when it is "
                 f"not"),
        ]

        expected = {
            "signal_period": str(track["period"]),
            "signal_input_mean": q(track["input_mean"]),
            "signal_bit_mean": q(track["bit_mean"]),
            "signal_within_bound": str(track["within_bound"]),
            "state_stayed_in_range": str(track["state_stayed_in_range"]),
            "closing_period_sum": q(closing["period_sum"]),
            "closing_orbit_closed": str(closing["orbit_closed"]),
            "open_period_sum": q(open_orbit["period_sum"]),
            "open_orbit_closed": str(open_orbit["orbit_closed"]),
            "cascade_second_difference": str(
                cascade["second_difference_holds"]),
            "cascade_double_sum": q(cascade["double_sum"]),
            "cascade_double_sum_equals_state": str(
                cascade["double_sum_equals_state"]),
            "cascade_triangular_error": q(cascade["triangular_error"]),
            "cascade_triangular_bound": q(cascade["triangular_bound"]),
            "dither_monotone": str(sweep["monotone_in_amplitude"]),
            "dither_undithered_peak": q(sweep["undithered_peak_fraction"]),
            "dither_lowest_peak": q(sweep["lowest_peak_fraction"]),
            "feedback_bound": q(tracking["bound"]),
            "feedback_within_bound": str(tracking["within_bound"]),
            "feedback_errors_bounded": str(tracking["errors_bounded"]),
            "feedback_equivariant": str(equivariant["outputs_permute"]),
            "feedback_not_equivariant": str(asymmetric["outputs_permute"]),
            "feedback_dead_zone_silent": str(
                dead["contracting_outputs_all_zero"]),
            "feedback_dead_zone_error": q(dead["contracting_error"]),
            "feedback_identity_fires": str(dead["identity_fires"]),
        }
        for index, value in enumerate(tracking["coordinate_errors"]):
            expected[f"feedback_error_{index}"] = q(value)
        for row in table:
            expected[f"third_error_{row['window']}"] = q(row["cascade_error"])
            expected[f"third_single_{row['window']}"] = q(
                row["single_loop_error"])

        return Solution(
            query=query, kind="report",
            answer=f"report noise: the loop tracks a two-tone signal to "
                   f"{q(track['error'])} against the bound "
                   f"1/{track['ticks']}; a periodic input closes its orbit "
                   f"exactly when its period sum is whole "
                   f"({closing['orbit_closed']} against "
                   f"{open_orbit['orbit_closed']}); the cascade's error is a "
                   f"second difference at every tick "
                   f"({cascade['second_difference_holds']}) and its "
                   f"doubly accumulated error stays at "
                   f"{q(cascade['double_sum'])}; read through a triangular "
                   f"window it beats a single loop by a factor of "
                   f"{widest['ratio_single_to_cascade']} at M = "
                   f"{widest['window']}; and dither trades the idle tone "
                   f"{q(sweep['undithered_peak_fraction'])} down to "
                   f"{q(sweep['lowest_peak_fraction'])} for a bias of "
                   f"{q(report['dither']['bias'])}",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_noise", "args": {}},
            payload={"report": noise_payload(report)})

    def _report_signature(self, query: Query) -> Solution:
        """Wires wbl.wobble_report -- the spectral signature of a constant.

        The external studies run the modulator for ten thousand ticks against
        a constant and tabulate the emitted stream: entropy, run lengths,
        transitions, one-density.  Every one of those columns is a closed form
        of the target, proved in ``RequestProject/GLM/Sturmian.lean``, so the
        subject reports the measurement and the law side by side rather than
        the measurement alone.
        """
        report = wbl.wobble_report()
        table = report["signatures"]
        oscillator = report["oscillator"]
        lock = report["resonance"]
        sweep = report["resonance_sweep"]
        scan = report["resonance_q_scan"]
        runs_at_bound = sum(
            1 for row in table
            if row["longest_zero_run"] == row["longest_zero_run_bound"]
            or row["longest_one_run"] == row["longest_one_run_bound"])

        steps = [
            Step("the stream is a mechanical word",
                 f"The first-order modulator chasing a constant t emits "
                 f"bit n = floor((n+1)t) - floor(n t): an irrational rotation "
                 f"read through the unit interval, which is a Sturmian word "
                 f"when t is irrational.  Everything below follows from that "
                 f"one identity rather than from the run.",
                 f"{report['targets']} targets, {report['steps']} ticks each; "
                 f"every measured column matches its closed form: "
                 f"{report['all_laws_hold']}"),
            Step("entropy is a function of the target",
                 f"The ones in N ticks are exactly floor(N t), so the density "
                 f"is pinned by the target and the 'measured' Shannon entropy "
                 f"is the binary entropy of t.  It is not an experimental "
                 f"property of the stream: two constants with the same "
                 f"fractional part have the same entropy to the last bit.",
                 "; ".join(f"{row['name']} {row['entropy_rounded']}"
                           for row in table)),
            Step("run lengths sit on their bound",
                 f"No run of zeros can reach 1/t and no run of ones can reach "
                 f"1/(1-t), and the longest run in a long enough stream "
                 f"attains the bound.  The two extreme rows -- the "
                 f"fine-structure constant and exp(pi) - pi -- are the "
                 f"visible case: their streams are almost silent.",
                 "; ".join(f"{row['name']} "
                           f"{max(row['longest_zero_run'], row['longest_one_run'])}"
                           for row in table)
                 + f"; rows attaining a bound: {runs_at_bound} of "
                   f"{len(table)}"),
            Step("signal quality is the same number",
                 f"The oscillator study's SNR table is the binary entropy of "
                 f"the one-density and nothing else, so 'SNR is wobble "
                 f"entropy' is an identity rather than a correlation.",
                 "; ".join(f"{row['condition']} {row['entropy_rounded']}"
                           for row in oscillator)),
            Step("resonance, and how far the dip carries",
                 f"At gain one the loop locks: after the accumulator fills it "
                 f"emits nothing but ones and the entropy is exactly zero "
                 f"(GLM.Info.ds_resonance_lock).  Swept across the normalised "
                 f"response the entropy rises on both sides of resonance -- "
                 f"but it peaks at the half-power points and falls away "
                 f"again, so the dip identifies resonance only inside the "
                 f"band.  No quality factor reproduces the study's two "
                 f"off-resonance figures at once.",
                 f"locked after tick 0: "
                 f"{lock['all_ones_after_the_first']}, entropy "
                 f"{lock['resonant_entropy']}; sweep "
                 + ", ".join(row["entropy_rounded"] for row in sweep)
                 + f"; best q = {scan['best_q']} gives "
                   f"{scan['best_low_entropy']} and "
                   f"{scan['best_high_entropy']}, hits {len(scan['hits'])} of "
                   f"{scan['points']}"),
        ]

        expected = {
            "targets": str(report["targets"]),
            "steps": str(report["steps"]),
            "all_laws_hold": str(report["all_laws_hold"]),
            "max_entropy_density": q(report["max_entropy_density"]),
            "resonance_locked": str(lock["all_ones_after_the_first"]),
            "resonant_entropy": q(lock["resonant_entropy"]),
            "scan_hits": str(len(scan["hits"])),
            "scan_points": str(scan["points"]),
            "scan_best_q": q(scan["best_q"]),
            "scan_best_low": str(scan["best_low_entropy"]),
            "scan_best_high": str(scan["best_high_entropy"]),
        }
        for row in table:
            key = str(row["name"]).replace(" ", "_")
            expected[f"entropy_{key}"] = str(row["entropy_rounded"])
            expected[f"ones_{key}"] = str(row["ones"])
            expected[f"zero_run_{key}"] = str(row["longest_zero_run"])
            expected[f"one_run_{key}"] = str(row["longest_one_run"])
        for row in oscillator:
            key = str(row["condition"]).replace(" ", "_")
            expected[f"oscillator_{key}"] = str(row["entropy_rounded"])
        for row in sweep:
            expected[f"sweep_{q(row['ratio'])}"] = str(row["entropy_rounded"])

        return Solution(
            query=query, kind="report",
            answer=f"report signature: the modulator's stream over "
                   f"{report['steps']} ticks reproduces every tabulated "
                   f"column of the spectral study from the target alone "
                   f"({report['all_laws_hold']}) -- the ones are exactly "
                   f"floor(N t), the entropy is the binary entropy of the "
                   f"density, and the longest run sits on 1/min(t, 1-t); "
                   f"the oscillator's SNR table is the same function, and at "
                   f"lock the entropy is exactly "
                   f"{q(lock['resonant_entropy'])}, though the entropy dip "
                   f"is local to the resonance band and no quality factor "
                   f"gives both off-resonance figures",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_signature", "args": {}},
            payload={"report": noise_payload(report)})

    def _report_drift(self, query: Query) -> Solution:
        """Wires dft.drift_report -- iteration drift over the odd primes.

        The same recurrence is run three ways -- exactly, in binary64, and in
        binary64 truncated to a display precision -- and the gap between the
        exact orbit and the others is the drift.  Every figure is exact: the
        binary64 regime is modelled by the package's own IEEE-754 rounding,
        not by the host's floats.
        """
        report = dft.drift_report()
        table = report["table"]
        rows = {(row["prime"], row["rule"]): row for row in table}
        accumulative = [row for row in table if row["rule"] == "accumulative"]
        three = rows[(3, "accumulative")]

        steps = [
            Step("three regimes on one recurrence",
                 f"X_(n+1) = r X_n - 1/p is iterated {report['steps']} times "
                 f"from X_0 = 1/p, for each odd prime and each of the two "
                 f"rules.  The exact orbit is rational arithmetic; the "
                 f"lossless regime rounds both operations to binary64; the "
                 f"display regimes round the result again to six and to four "
                 f"significant decimal digits.",
                 f"{len(table)} rows over primes "
                 f"{', '.join(str(p) for p in report['primes'])}, rules "
                 f"{', '.join(dft.RULES)}"),
            Step("the contractive rule forgets its error",
                 f"When |r| < 1 the map is a contraction, so an error "
                 f"introduced at any step is damped by every step after it. "
                 f"The drift is bounded by the regime's own resolution and "
                 f"stays there however long the loop runs.",
                 f"every contractive row stays under its ceiling: "
                 f"{report['contractive_stays_under_its_ceiling']}"),
            Step("the accumulative rule amplifies it",
                 f"When |r| > 1 the same error is multiplied at every step, "
                 f"so the drift grows geometrically and the small primes -- "
                 f"whose ratio is largest -- end furthest from the truth.  "
                 f"The drift is not the value: at p = 3 the orbit itself has "
                 f"run away to {three['exact_final_sci']} while the drift is "
                 f"{three['lossless_drift_sci']}.",
                 "; ".join(f"p = {row['prime']}: "
                           f"{row['lossless_drift_sci']}, "
                           f"{row['display6_drift_sci']}, "
                           f"{row['display4_drift_sci']}"
                           for row in accumulative)),
            Step("when the drift becomes meaningful",
                 f"The first step at which the gap exceeds 1e-9.  Truncating "
                 f"the display never helps -- every display regime is at "
                 f"least as far out as the hardware one "
                 f"({report['truncation_never_helps']}) -- and the lossless "
                 f"regime survives to step "
                 f"{report['lossless_onset_at_three']} at p = 3 and never "
                 f"diverges at all within the run for the larger primes.",
                 f"display diverges by step two everywhere: "
                 f"{report['display_diverges_by_step_two']}; exceptions "
                 + ", ".join(f"p = {e['prime']} {e['rule']} "
                             f"({e['display6']}, {e['display4']})"
                             for e in report["display_onset_exceptions"])),
        ]

        expected = {
            "steps": str(report["steps"]),
            "rows": str(len(table)),
            "contractive_under_ceiling": str(
                report["contractive_stays_under_its_ceiling"]),
            "truncation_never_helps": str(report["truncation_never_helps"]),
            "display_diverges_by_step_two": str(
                report["display_diverges_by_step_two"]),
            "lossless_onset_at_three": str(report["lossless_onset_at_three"]),
            "onset_exceptions": str(len(report["display_onset_exceptions"])),
        }
        for row in table:
            key = f"{row['prime']}_{row['rule']}"
            expected[f"exact_{key}"] = str(row["exact_final_sci"])
            expected[f"lossless_{key}"] = str(row["lossless_drift_sci"])
            expected[f"display6_{key}"] = str(row["display6_drift_sci"])
            expected[f"display4_{key}"] = str(row["display4_drift_sci"])

        return Solution(
            query=query, kind="report",
            answer=f"report drift: over {report['steps']} steps the "
                   f"contractive rule holds every regime inside its own "
                   f"resolution "
                   f"({report['contractive_stays_under_its_ceiling']}) while "
                   f"the accumulative rule amplifies the first rounding into "
                   f"a drift of {three['lossless_drift_sci']} at p = 3 in "
                   f"plain binary64 and {three['display4_drift_sci']} at four "
                   f"displayed digits; truncation never helps "
                   f"({report['truncation_never_helps']}), and the lossless "
                   f"regime first exceeds 1e-9 at step "
                   f"{report['lossless_onset_at_three']}",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_drift", "args": {}},
            payload={"report": drift_payload(report)})

    def _report_containers(self, query: Query) -> Solution:
        """Wires con.containers_report -- the three containers of a constant.

        A constant enters the GLM as a generator, a stream and a point in 24
        coordinates.  This subject runs all three: how many exact steps the
        generator needs for a stated precision, what the modulator's stream
        looks like statistically, and whether the projection lies in the
        convex hull of the Leech minimal vectors -- with a certificate either
        way, checked against all 196,560 of them rather than a sample.
        """
        report = con.containers_report()
        scales = report["critical_scales"]
        convergence = report["convergence"]
        hull = report["hull"]

        def _steps(name: str) -> str:
            row = next(r for r in convergence if r["name"] == name)
            return ", ".join(
                "never" if row["steps_to"][t] is None       # type: ignore
                else str(row["steps_to"][t])                # type: ignore
                for t in con.PRECISION_THRESHOLDS)

        steps = [
            Step("the algorithmic container",
                 f"Each constant's generator is run in exact rational "
                 f"arithmetic and the bits of relative precision are decided "
                 f"by integer comparison against a "
                 f"{con.REFERENCE_BITS}-bit reference.  No logarithm is "
                 f"taken and no float is constructed: the answer is the "
                 f"first index at which an integer inequality holds.",
                 f"steps to {', '.join(str(t) for t in con.PRECISION_THRESHOLDS)} "
                 f"bits: sqrt(2) {_steps('sqrt(2)')}; pi {_steps('pi')}; "
                 f"e {_steps('e')}; Liouville {_steps('Liouville')}"),
            Step("the temporal container",
                 f"Every constant is chased by the delta-sigma modulator for "
                 f"{report['steps']} exact steps and the stream's statistics "
                 f"are printed beside the closed form each one is known to "
                 f"take.  The point of the column is that the laws hold: the "
                 f"stream's entropy, run length and autocorrelation are "
                 f"functions of the target, so the measurement tests the "
                 f"modulator and not the constant.",
                 f"laws hold for every constant: {report['laws_hold']}; the "
                 f"rigid baseline's stream has least period "
                 f"{report['rigid_period']}, not two"),
            Step("the geometric container",
                 f"The projection v_i = 4c/(i+1) is tested against the "
                 f"convex hull of the Leech minimal vectors.  Sampling can "
                 f"only ever prove that a point is inside, so both verdicts "
                 f"are certificates here: inside when the projection lies in "
                 f"the polytope whose extreme points are the shape-(+-4^2) "
                 f"minimal vectors, outside when an explicit direction "
                 f"separates it from all 196,560.",
                 f"{report['hull_decided']} of {len(hull)} constants "
                 f"decided; inside {', '.join(report['hull_inside']) or 'none'}; "
                 f"outside {', '.join(report['hull_outside']) or 'none'}; "
                 f"undetermined "
                 f"{', '.join(report['hull_undetermined']) or 'none'}"),
            Step("where the certificates change their answer",
                 f"Every target is a positive multiple c of one direction, "
                 f"so both tests reduce to a comparison on c and the census "
                 f"is two exact thresholds rather than eight separate "
                 f"questions.",
                 f"inside for c at most "
                 f"{wbl.round_str(scales['inside_at_most'], 4)}, outside for "
                 f"c above {wbl.round_str(scales['outside_above'], 4)}; the "
                 f"support of the projection direction is "
                 f"{scales['unit_support']}"),
        ]

        expected = {
            "constants": ",".join(report["constants"]),
            "laws_hold": str(report["laws_hold"]),
            "rigid_period": str(report["rigid_period"]),
            "hull_decided": str(report["hull_decided"]),
            "hull_inside": ",".join(report["hull_inside"]),
            "hull_outside": ",".join(report["hull_outside"]),
            "hull_undetermined": ",".join(report["hull_undetermined"]),
            "unit_support": str(scales["unit_support"]),
            "outside_above": wbl.round_str(scales["outside_above"], 6),
            "inside_at_most": wbl.round_str(scales["inside_at_most"], 6),
        }
        for row in convergence:
            expected[f"steps_{row['name']}"] = _steps(str(row["name"]))

        return Solution(
            query=query, kind="report",
            answer=(f"report containers: eight constants through three "
                    f"containers; {report['hull_decided']} of {len(hull)} "
                    f"hull verdicts settled by certificate"),
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_containers", "args": {}},
            payload={"report": containers_payload(report)})

    def _report_mantissa(self, query: Query) -> Solution:
        """Wires mn.mantissa_report -- where a float's precision goes.

        IEEE-754 binary64 is modelled exactly in integers, so the question
        the blueprint's section 5.1 asks can be answered rather than
        estimated: how much is lost when 1/p is first stored, and where the
        drift that follows actually comes from.
        """
        report = mn.mantissa_report()
        rounding = report["rounding"]
        drift = report["drift"]

        steps = [
            Step("the first rounding",
                 f"For each odd prime p, 1/p is rounded to the nearest "
                 f"binary64 value -- computed in exact integer arithmetic, "
                 f"not by asking the hardware -- and the result is compared "
                 f"bit for bit against the exact expansion.",
                 f"the least retained is "
                 f"{rounding['min_retained_bits']} bits; the significand "
                 f"differs from the exact expansion in at most "
                 f"{rounding['max_significand_hamming']} places; bits lost "
                 f"at step zero {rounding['bits_lost_at_step_zero']}"),
            Step("the period",
                 f"The blueprint's oscillation frequency is the "
                 f"multiplicative order of 2 modulo p, and the exact "
                 f"expansion repeats with exactly that period.",
                 f"periods "
                 f"{[row['period'] for row in rounding['rows']]}, every "
                 f"prime repeats {rounding['every_prime_repeats']}"),
            Step("where the loss really is",
                 f"A double is a dyadic rational, so under the doubling map "
                 f"its orbit runs out of bits and dies; the exact orbit of "
                 f"1/p never does. That difference, not the first rounding, "
                 f"is what separates the float from the substrate.",
                 f"every stored orbit collapses "
                 f"{drift['all_collapse']}, within the bit-count bound "
                 f"{drift['all_collapse_within_bound']}; no exact orbit "
                 f"terminates"),
            Step("the substrate projection",
                 f"Projecting the significand onto the 24 coordinates and "
                 f"following the orbit shows the drift. The antipodal "
                 f"reading the blueprint reports is a post-collapse "
                 f"artefact: before the stored orbit dies the distance never "
                 f"reaches 24.",
                 f"maximum distance before collapse "
                 f"{drift['max_distance_before_collapse']} of 24; antipodal "
                 f"before collapse "
                 f"{drift['any_antipodal_before_collapse']}"),
        ]

        expected = {
            "precision": str(report["precision"]),
            "primes": ",".join(str(p) for p in report["primes"]),
            "min_retained_bits": str(rounding["min_retained_bits"]),
            "bits_lost_at_step_zero": str(
                rounding["bits_lost_at_step_zero"]),
            "max_significand_hamming": str(
                rounding["max_significand_hamming"]),
            "every_prime_repeats": str(rounding["every_prime_repeats"]),
            "periods": ",".join(
                str(row["period"]) for row in rounding["rows"]),
            "all_collapse": str(drift["all_collapse"]),
            "all_collapse_within_bound": str(
                drift["all_collapse_within_bound"]),
            "max_distance_before_collapse": str(
                drift["max_distance_before_collapse"]),
            "any_antipodal_before_collapse": str(
                drift["any_antipodal_before_collapse"]),
            "claim_count": str(report["claim_count"]),
            "confirmed": str(report["confirmed"]),
            "refuted": str(report["refuted"]),
        }
        for row in drift["rows"]:
            prime = str(row["prime"])
            expected[f"collapse_step_{prime}"] = str(row["collapse_step"])
            expected[f"exact_terminates_{prime}"] = str(
                row["exact_orbit_terminates"])

        return Solution(
            query=query, kind="report",
            answer=f"report mantissa: storing 1/p in binary64 retains at "
                   f"least {rounding['min_retained_bits']} bits, so the "
                   f"blueprint's ten bits are not lost at the first "
                   f"operation; the period of the expansion is the order of "
                   f"2 mod p for every prime tested "
                   f"({rounding['every_prime_repeats']}); and the loss is "
                   f"structural -- every stored orbit collapses "
                   f"({drift['all_collapse']}) while no exact orbit does",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_mantissa", "args": {}},
            payload={"report": report})

    def _report_reversible(self, query: Query) -> Solution:
        """Wires rv.reversible_report -- Part V of the blueprint, measured.

        The Gray-code read channel, the Toffoli and Fredkin gates on the 24
        coordinates, and the kink invariant.  Three of the section's claims
        hold exactly and three do not; both are reported.
        """
        report = rv.reversible_report()
        channel = report["channel"]
        gates = report["gates"]
        solitons = report["solitons"]

        steps = [
            Step("the read channel",
                 f"A {channel['width']}-bit counter is walked through a full "
                 f"cycle twice: once in binary, once in the binary reflected "
                 f"Gray code.  The cost of a step is the number of "
                 f"coordinates that change, and the symmetry TAX is the "
                 f"total over the cycle.",
                 f"Gray flips {channel['gray']['flips']} bits with maximum "
                 f"step {channel['gray']['max_step']} and variance "
                 f"{channel['gray']['variance']}; binary flips "
                 f"{channel['binary']['flips']} with maximum step "
                 f"{channel['binary']['max_step']}"),
            Step("exactly half?",
                 f"The blueprint says Gray dissipates exactly half the "
                 f"binary TAX.  It does not: over a full cycle binary flips "
                 f"2^(w+1) - 2 bits and Gray flips 2^w, so twice the Gray "
                 f"cost exceeds the binary cost by exactly 2 at every "
                 f"width. Half is the limit, not the value.",
                 f"flip ratio {channel['flip_ratio']}, TAX ratio "
                 f"{channel['tax_ratio']}, halving exact "
                 f"{channel['halving_exact']}"),
            Step("reversibility",
                 f"Both gates are checked to be self-inverse and bijective "
                 f"on all eight inputs, then a carrier is run forward "
                 f"{gates['rounds']} rounds and backward "
                 f"{gates['rounds']} rounds over the eight coordinate "
                 f"triples.",
                 f"{gates['gate_applications']} gate applications, Hamming "
                 f"distance to the start {gates['hamming_to_start']}, exact "
                 f"return {gates['exact_return']}"),
            Step("what reversibility does not conserve",
                 f"The blueprint says the Golay syndrome weight stays at "
                 f"zero throughout.  Reversibility is a property of the map, "
                 f"not of the code: a bijection may leave the code and come "
                 f"back, and this one does.",
                 f"syndrome weight starts at {gates['syndrome_start']} and "
                 f"takes the values {gates['syndrome_values']}; conserved "
                 f"{gates['syndrome_conserved']}"),
            Step("the kink invariant",
                 f"A kink is a boundary where adjacent coordinates differ. "
                 f"The count is invariant under every rotation and always "
                 f"even. A single flip moves it by -2, 0 or +2 -- not by "
                 f"exactly +/-2, as the blueprint has it -- and the "
                 f"exhaustive census over all circular 8-bit words says how "
                 f"often each happens.",
                 f"{solitons['kinks']} kinks, rotation invariant "
                 f"{solitons['rotation_invariant']}, always even "
                 f"{solitons['kink_count_always_even']}; deltas over "
                 f"{solitons['exhaustive_words']} words "
                 f"{solitons['exhaustive_flip_deltas']}"),
        ]

        expected = {
            "width": str(channel["width"]),
            "steps": str(channel["steps"]),
            "gray_flips": str(channel["gray"]["flips"]),
            "gray_max_step": str(channel["gray"]["max_step"]),
            "gray_variance": q(channel["gray"]["variance"]),
            "binary_flips": str(channel["binary"]["flips"]),
            "gray_tax": q(channel["gray"]["tax"]),
            "binary_tax": q(channel["binary"]["tax"]),
            "halving_exact": str(channel["halving_exact"]),
            "gates_involutive": str(gates["gates_involutive"]),
            "gates_bijective": str(gates["gates_bijective"]),
            "gate_applications": str(gates["gate_applications"]),
            "hamming_to_start": str(gates["hamming_to_start"]),
            "exact_return": str(gates["exact_return"]),
            "syndrome_conserved": str(gates["syndrome_conserved"]),
            "kinks": str(solitons["kinks"]),
            "rotation_invariant": str(solitons["rotation_invariant"]),
            "kink_count_always_even": str(
                solitons["kink_count_always_even"]),
            "delta_always_two": str(solitons["delta_always_two"]),
            "claim_count": str(report["claim_count"]),
            "confirmed": str(report["confirmed"]),
            "refuted": str(report["refuted"]),
        }

        return Solution(
            query=query, kind="report",
            answer=f"report reversible: Gray flips "
                   f"{channel['gray']['flips']} bits against binary's "
                   f"{channel['binary']['flips']} over a full "
                   f"{channel['width']}-bit cycle, so the halving is exact "
                   f"{channel['halving_exact']}; "
                   f"{gates['gate_applications']} reversible gate "
                   f"applications return the carrier at Hamming distance "
                   f"{gates['hamming_to_start']}, with the syndrome weight "
                   f"conserved {gates['syndrome_conserved']}; the kink count "
                   f"is rotation invariant "
                   f"{solitons['rotation_invariant']} and a single flip "
                   f"always moves it by two "
                   f"{solitons['delta_always_two']}",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_reversible", "args": {}},
            payload={"report": report})

    def _report_engine(self, query: Query) -> Solution:
        """Wires eng.engine_report -- the blueprint's Part III, assembled.

        The engine family was the one part of the blueprint the package had
        no code for.  This subject runs the assembled machine and measures
        what each stage is worth, including the section's headline ratio,
        which turns out to name no measurement at all.
        """
        report = eng.engine_report()
        runs = report["runs"]
        fuel = report["multi_fuel"]
        leap = report["precision_leap"]
        strain = report["strain_readings"]

        steps = [
            Step("the accumulator and the drums",
                 f"The target is integrated exactly, one bit emitted per "
                 f"tick, and the escapement drums advance under it. The "
                 f"joint drum reading repeats only after the least common "
                 f"multiple of the moduli.",
                 f"error {runs['plain']['error']} after "
                 f"{report['ticks']} ticks; moduli "
                 f"{list(eng.ESCAPEMENT_MODULI)}, period "
                 f"{eng.escapement_period()}"),
            Step("two strains, not one",
                 f"The exact snap measures the distance to the Leech "
                 f"lattice; the certificate path measures the distance to "
                 f"the nearest Golay-aligned sign pattern. On the same "
                 f"carrier these are different numbers, so the fast path is "
                 f"a different reading rather than a cheaper version of the "
                 f"slow one.",
                 f"tight {strain['tight']['kind']} TAX "
                 f"{strain['tight']['tax']}; relaxed "
                 f"{strain['relaxed']['kind']} TAX "
                 f"{strain['relaxed']['tax']}; agree {strain['agree']}"),
            Step("radiator and trip-lever",
                 f"Strain above the capacity trips the escalation lever. "
                 f"The radiator bleeds the accumulated strain periodically, "
                 f"which lowers both the final strain and the number of "
                 f"trips.",
                 f"uncooled: strain "
                 f"{runs['plain']['accumulated_tax']}, "
                 f"{runs['plain']['escalations']} escalations; cooled: "
                 f"strain {runs['cooled']['accumulated_tax']}, "
                 f"{runs['cooled']['escalations']} escalations after "
                 f"{report['radiator_bleeds']} bleeds"),
            Step("turbocharger",
                 f"Once the strain is over capacity the turbocharger relaxes "
                 f"the snap, and over twice capacity it skips it. The "
                 f"saving is counted in integer operations under the cost "
                 f"model the module states.",
                 f"{report['turbo_snaps_avoided']} snaps skipped, "
                 f"{report['turbo_saves_operations']} operations saved"),
            Step("multi-fuel",
                 f"Heron's iteration and the continued-fraction convergents "
                 f"are burned in parallel on the same algebraic target and "
                 f"the better one is read at each tick. The comparison is "
                 f"exact: the residual is rational, so the root itself is "
                 f"never needed.",
                 f"Heron clears {fuel['depth']} bits at tick "
                 f"{fuel['heron_tick']}, the convergents at "
                 f"{fuel['convergent_tick']}, the switching strategy at "
                 f"{fuel['switched_tick']} -- a speed-up of "
                 f"{fuel['speedup_over_slower']} over the slower fuel"),
            Step("the headline",
                 f"A ratio of precisions means nothing until both terms are "
                 f"named. Three baselines are measured and all three are "
                 f"reported: against bitwise truncation the modulator loses, "
                 f"against a one-shot hold it wins, and against half its own "
                 f"budget it gains a little. None of them is 27/10.",
                 f"truncation {leap['against_truncation_range']}, half "
                 f"budget {leap['against_half_budget_range']}, claimed "
                 f"{leap['claimed_ratio']}, matched "
                 f"{leap['any_baseline_gives_the_claimed_ratio']}"),
        ]

        expected = {
            "ticks": str(report["ticks"]),
            "escapement_period": str(eng.escapement_period()),
            "plain_error": str(runs["plain"]["error"]),
            "plain_tax": str(runs["plain"]["accumulated_tax"]),
            "plain_escalations": str(runs["plain"]["escalations"]),
            "cooled_tax": str(runs["cooled"]["accumulated_tax"]),
            "cooled_escalations": str(runs["cooled"]["escalations"]),
            "radiator_bleeds": str(report["radiator_bleeds"]),
            "radiator_lowers_final_strain": str(
                report["radiator_lowers_final_strain"]),
            "turbo_snaps_avoided": str(report["turbo_snaps_avoided"]),
            "turbo_saves_operations": str(
                report["turbo_saves_operations"]),
            "strain_readings_agree": str(strain["agree"]),
            "tight_tax": str(strain["tight"]["tax"]),
            "relaxed_tax": str(strain["relaxed"]["tax"]),
            "heron_tick": str(fuel["heron_tick"]),
            "convergent_tick": str(fuel["convergent_tick"]),
            "switched_tick": str(fuel["switched_tick"]),
            "fuel_speedup": q(fuel["speedup_over_slower"]),
            "claimed_ratio": str(leap["claimed_ratio"]),
            "claimed_ratio_matched": str(
                leap["any_baseline_gives_the_claimed_ratio"]),
        }

        return Solution(
            query=query, kind="report",
            answer=f"report engine: the assembled engine runs 1/3 to error "
                   f"{runs['plain']['error']} in {report['ticks']} ticks, "
                   f"the radiator turns "
                   f"{runs['plain']['escalations']} escalations into "
                   f"{runs['cooled']['escalations']}, the turbocharger "
                   f"skips {report['turbo_snaps_avoided']} snaps for "
                   f"{report['turbo_saves_operations']} operations, the two "
                   f"fuels together clear the depth "
                   f"{fuel['speedup_over_slower']} times sooner than the "
                   f"slower one alone, and the claimed "
                   f"{leap['claimed_ratio']} precision leap is matched by "
                   f"none of the three stated baselines",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_engine", "args": {}},
            payload={"report": report})

    def _report_infinite_values(self, query: Query) -> Solution:
        """Wires xr.exact_real_report -- what the machine does with infinities.

        Three claims, each recomputed: irrational values are reached as
        processes; the dynamic carrier's one-dimensional bound is exact; and
        in twenty-four dimensions the reachable set is the convex hull of the
        code, with a certificate for a target outside it.
        """
        report = xr.exact_real_report()
        runs = ", ".join(f"N={steps} err={error}"
                         for steps, error, _ok in report["delta_sigma_runs"])

        steps = [
            Step("the wall",
                 "A carrier is a tuple of rationals and a digit stack is "
                 "finite, so the set of values either can hold is countable "
                 "while the reals are not.  No representation the machine "
                 "could adopt separates all real targets -- "
                 "GLM.Info.no_countable_layer_lossless.",
                 f"sqrt(2) to 2**-40 = {report['sqrt2_at_40']}; "
                 f"its square misses 2 by {report['sqrt2_squared_error']}"),
            Step("through it, by process",
                 "A real is held as a function from precision to rational. "
                 "Constants are produced to any precision asked for, and "
                 "each is checked against a relation it must satisfy.",
                 f"sqrt(2) = {report['sqrt2_decimal_20']}, "
                 f"pi = {report['pi_decimal_20']}, "
                 f"e = {report['e_decimal_20']}, "
                 f"phi = {report['phi_decimal_20']}"),
            Step("the tower's stand-ins",
                 "Each level of the dyadic tower holds a rational carrier "
                 "indistinguishable from the target at that resolution, and "
                 "each is exposed at a higher level: true up to a point, then "
                 "superseded.",
                 f"levels 0..{report['levels'] - 1}: "
                 f"{', '.join(report['stand_ins'])}; exposed at "
                 f"{report['stand_in_exposed_at']}"),
            Step("the dynamic carrier, in one dimension",
                 "The modulator's time average is within 1/N of the target "
                 "after N ticks, exactly as proved.  No random, no float.",
                 f"{runs}; law holds {report['delta_sigma_law_holds']}; "
                 f"deterministic {report['delta_sigma_deterministic']}"),
            Step("and in twenty-four",
                 "Every state the 24-D carrier emits is a codeword, so its "
                 "reachable set is the convex hull of the code.  The all-1/2 "
                 "vector is inside it and is held exactly; the ramp target "
                 "i/24 is outside it, and a separating functional verified "
                 "against all 4,096 codewords proves no quantiser can hold "
                 "it -- GLM.Info.not_tendsto_avg_of_separating.",
                 f"reachable deviation {report['golay_reachable_deviation']}; "
                 f"unreachable deviation {report['golay_average_deviation']} "
                 f"with accumulator {report['golay_max_accumulator']}; "
                 f"certificate {report['golay_unreachable_certified']} "
                 f"(gap {report['golay_certificate_gap']})"),
            Step("what is still not possible",
                 "Equality of two processes is undecidable, and the machine "
                 "reports 'not yet distinguished' rather than guessing. "
                 "Inequality is decidable.",
                 f"equality undecided {report['equality_undecided']}; "
                 f"inequality decided {report['inequality_decided']}"),
        ]

        expected = {
            "sqrt2_decimal_20": report["sqrt2_decimal_20"],
            "pi_decimal_20": report["pi_decimal_20"],
            "e_decimal_20": report["e_decimal_20"],
            "phi_decimal_20": report["phi_decimal_20"],
            "delta_sigma_law_holds": str(report["delta_sigma_law_holds"]),
            "delta_sigma_deterministic": str(
                report["delta_sigma_deterministic"]),
            "no_stand_in_is_the_target": str(
                report["no_stand_in_is_the_target"]),
            "golay_reachable_deviation": str(
                report["golay_reachable_deviation"]),
            "golay_within_one_over_n": str(report["golay_within_one_over_n"]),
            "golay_unreachable_certified": str(
                report["golay_unreachable_certified"]),
            "equality_undecided": str(report["equality_undecided"]),
            "inequality_decided": str(report["inequality_decided"]),
        }

        return Solution(
            query=query, kind="report",
            answer=f"report infinite values: sqrt(2) = "
                   f"{report['sqrt2_decimal_20']}, pi = "
                   f"{report['pi_decimal_20']}; the 1/N law holds "
                   f"{report['delta_sigma_law_holds']}; the 24-D carrier "
                   f"holds the all-1/2 target exactly and provably cannot "
                   f"hold the ramp target "
                   f"({report['golay_unreachable_certified']}); equality of "
                   f"processes stays undecidable "
                   f"({report['equality_undecided']})",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_infinite_values", "args": {}},
            payload={"report": {key: str(value)
                                for key, value in report.items()}})
