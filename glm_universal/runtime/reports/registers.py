"""``glm_universal.runtime.reports.registers``
-- the subjects the registers and their audits compute.

Reports about what the registers hold.

The physical relation audit, the unit strings, the molecule register, the
sparsity of the element register and the three widenings that invent no
measurement, the harmonic register's temperament arithmetic, the price
register's discovery run, and analogy by named relation.

Every method here is a solver for one ``report <subject>`` query.  They are
mixed into :class:`glm_universal.runtime.session.GeometricSession`,
which is where ``self`` comes from: the loaded registers, the concept index
and the shared helpers.  Splitting them out of the session keeps each family
beside a docstring that says which sub-package computes it, and keeps the
dispatcher readable as a dispatcher.
"""
from __future__ import annotations

from ... import data_objects as do
from ...reasoning import analogy_models as am
from ...reasoning import economics as ecn
from ...reasoning import element_coverage as eco
from ...reasoning import harmony as hy
from ...reasoning import units as un
from ...reasoning import verifier as ve

from ..payload import noise_payload
from ..parser import Query
from ..solution import Solution, Step, q


class RegisterReports:
    """The subjects the registers and their audits compute.

    A mixin of :class:`~glm_universal.runtime.session.GeometricSession`;
    it holds no state of its own.
    """

    def _report_relations(self, query: Query) -> Solution:
        """Wires ve.verifier_report — the 222+71 relation audit."""
        report = ve.verifier_report()
        # The report has three tables: scalar relations under scalar
        # semantics (all hold), scalar relations under full semantics
        # (some fail on rank/parity), and tensor relations under full
        # semantics (all hold).
        scalar_scalar = report["scalar_relations_under_scalar_semantics"]
        scalar_full = report["scalar_relations_under_full_semantics"]
        tensor_full = report["tensor_relations_under_full_semantics"]
        steps = [
            Step("verifier_report",
                 f"The verifier audited three tables: {scalar_scalar['checked']} "
                 f"scalar relations under scalar semantics ({scalar_scalar['held']} "
                 f"hold), {scalar_full['checked']} scalar relations under full "
                 f"tensor semantics ({scalar_full['held']} hold, "
                 f"{scalar_full['failed']} fail on rank/parity), and "
                 f"{tensor_full['checked']} tensor relations ({tensor_full['held']} "
                 f"hold).  The {scalar_full['failed']} that hold scalarly but fail "
                 f"under full semantics are statements a units table gets right "
                 f"but a tensor analysis gets wrong -- e.g. 'acceleration = speed "
                 f"/ time' fails because the left side is rank-1 and the right "
                 f"side a scalar.",
                 f"scalar/scalar: {scalar_scalar['held']}/{scalar_scalar['checked']}, "
                 f"scalar/full: {scalar_full['held']}/{scalar_full['checked']} "
                 f"({scalar_full['failed']} fail), "
                 f"tensor/full: {tensor_full['held']}/{tensor_full['checked']}"),
        ]
        expected = {
            "scalar_scalar_checked": str(scalar_scalar["checked"]),
            "scalar_scalar_held": str(scalar_scalar["held"]),
            "scalar_full_checked": str(scalar_full["checked"]),
            "scalar_full_held": str(scalar_full["held"]),
            "scalar_full_failed": str(scalar_full["failed"]),
            "tensor_full_checked": str(tensor_full["checked"]),
            "tensor_full_held": str(tensor_full["held"]),
        }
        return Solution(
            query=query, kind="report",
            answer=f"report relations: scalar/scalar "
                   f"{scalar_scalar['held']}/{scalar_scalar['checked']}, "
                   f"scalar/full {scalar_full['held']}/{scalar_full['checked']}, "
                   f"tensor/full {tensor_full['held']}/{tensor_full['checked']}",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_relations", "args": {}},
            payload={"report": report})

    def _report_units(self, query: Query) -> Solution:
        """Wires units.units_report -- the unit strings, read as dimensions.

        Every quantity states what it is twice, once as a unit string and
        once as EXT10 exponents.  This parses the first and checks it
        against the second, and measures what the SI reading of the
        steradian would cost.
        """
        report = un.units_report()
        audit = report["audit"]
        case = report["steradian"]

        steps = [
            Step("ten units stored, the rest derived",
                 report["method"],
                 f"base units = {report['base_unit_count']}, derived "
                 f"definitions = {report['derived_unit_count']}, decimal "
                 f"prefixes = {report['prefix_count']}"),
            Step("every unit string in the register is parsed and checked",
                 f"Each of the {audit['quantities']} quantities carries a "
                 f"unit string and a vector of EXT10 exponents, written "
                 f"independently.  The string is parsed and the two are "
                 f"compared, so a typo in either is a failure rather than a "
                 f"silent disagreement.",
                 f"readable = {audit['readable']}/{audit['quantities']}, "
                 f"agreeing = {audit['agreed']}, mismatched = "
                 f"{audit['mismatched_count']}, unreadable = "
                 f"{audit['unreadable_count']}"),
            Step("the steradian is a dimension here, not a ratio",
                 case["statement"],
                 f"with the steradian carried, mismatches = "
                 f"{case['with_steradian']['mismatched']}; dropped, "
                 f"mismatches = {case['without_steradian']['mismatched']}"),
            Step("what a dimensionless steradian would conflate",
                 f"Dropping it breaks "
                 f"{case['broken_count']} quantities, of which "
                 f"{case['photometric_count']} are written with the lumen or "
                 f"the lux: "
                 f"{', '.join(case['photometric_quantities'])}.  The lumen "
                 f"would read as the candela, so luminous flux would become "
                 f"luminous intensity; the lux would read as the candela per "
                 f"square metre, so illuminance would become luminance.",
                 f"broken = {case['broken_count']}, photometric = "
                 f"{case['photometric_count']}, quantities carrying a solid "
                 f"angle = {case['solid_angle_count']}"),
        ]
        expected = {
            "quantities": str(audit["quantities"]),
            "every_unit_readable": str(audit["every_unit_readable"]),
            "every_unit_agrees": str(audit["every_unit_agrees"]),
            "mismatched_count": str(audit["mismatched_count"]),
            "broken_by_dropping_the_steradian": str(case["broken_count"]),
            "photometric_count": str(case["photometric_count"]),
        }
        return Solution(
            query=query, kind="report",
            answer=f"report units: all {audit['quantities']} unit strings in "
                   f"the physics register parse, and all "
                   f"{audit['agreed']} agree with the EXT10 exponents "
                   f"declared beside them, with "
                   f"{audit['mismatched_count']} mismatches; the parser "
                   f"carries the steradian as a dimension, and reading it "
                   f"the SI way -- as dimensionless -- would break "
                   f"{case['broken_count']} quantities, "
                   f"{case['photometric_count']} of them written with the "
                   f"lumen or the lux",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_units", "args": {}},
            payload={"report": report})

    def _report_molecules(self, query: Query) -> Solution:
        """Wires molecules.molecules_report -- the multi-carrier register.

        A molecule is held twice: as the faithful bundle of its element
        carriers with multiplicities, and as one composite carrier that is
        a *summary* of the bundle.  The report says which of the two is
        lossless and checks the claim rather than asserting it.
        """
        report = do.molecules_report()
        collisions = report["collisions"]
        missing = report["missing_by_field"]
        heaviest_name, heaviest_mass = report["largest_by_mass"]

        steps = [
            Step("the register stores no measurement",
                 f"{report['molecules']} molecules and ions are held as a "
                 f"name and a formula each.  Every one of the "
                 f"{report['derived_fields']} derived coordinates -- molar "
                 f"mass, electron count, electronegativity spread, degree "
                 f"of unsaturation and the rest -- is recomputed from the "
                 f"element register when the carrier is built, so this "
                 f"register cannot disagree with that one.",
                 f"molecules = {report['molecules']}, derived fields = "
                 f"{report['derived_fields']}, coordinates = "
                 f"{report['coordinates']}"),
            Step("the bundle is faithful, the composite is a summary",
                 f"The bundle ((symbol, count, carrier), ...) has the "
                 f"formula read straight back off it, which is checked for "
                 f"every molecule.  The composite carrier folds the "
                 f"composition into 24 coordinates and is therefore a "
                 f"summary; it is checked for collisions rather than "
                 f"assumed injective.",
                 f"bundle_is_faithful = "
                 f"{collisions['bundle_is_faithful']}, distinct composites "
                 f"= {collisions['distinct_composites']} of "
                 f"{collisions['molecules']}, composite collisions = "
                 f"{collisions['composite_collision_count']}"),
            Step("a gap in the element register stays a gap",
                 f"A coordinate the element register cannot support is left "
                 f"at 0 with its bit set in the missingness mask, never "
                 f"imputed.  On this register the only such coordinate is "
                 f"the degree of unsaturation, which is undefined for a "
                 f"formula containing sulfur, phosphorus or a metal -- so "
                 f"it is absent rather than wrong.",
                 f"missing_by_field = {dict(missing)}"),
            Step("what the register reaches",
                 f"{report['distinct_elements_used']} distinct elements "
                 f"appear across the register; the heaviest molecule is "
                 f"{heaviest_name} at {q(heaviest_mass)} u and the largest "
                 f"by atom count is {report['largest_by_atom_count'][0]} "
                 f"with {report['largest_by_atom_count'][1]} atoms.  "
                 f"{len(report['charged'])} of the entries are ions.",
                 f"elements used = {report['distinct_elements_used']}, "
                 f"ions = {len(report['charged'])}"),
        ]
        expected = {
            "molecules": str(report["molecules"]),
            "coordinates": str(report["coordinates"]),
            "derived_fields": str(report["derived_fields"]),
            "distinct_elements_used": str(report["distinct_elements_used"]),
            "bundle_is_faithful": str(collisions["bundle_is_faithful"]),
            "distinct_composites": str(collisions["distinct_composites"]),
            "composite_collision_count":
                str(collisions["composite_collision_count"]),
            "bundle_collision_count":
                str(collisions["bundle_collision_count"]),
            "missing_by_field": str(dict(missing)),
            "largest_by_mass": f"{heaviest_name}={q(heaviest_mass)}",
        }
        return Solution(
            query=query, kind="report",
            answer=f"report molecules: {report['molecules']} molecules and "
                   f"ions over {report['distinct_elements_used']} elements, "
                   f"each held twice -- as the faithful bundle of its "
                   f"element carriers, from which the formula is read back "
                   f"exactly for every entry, and as one composite carrier "
                   f"of {report['coordinates']} coordinates that is a "
                   f"summary and collides "
                   f"{collisions['composite_collision_count']} times on "
                   f"this register; no measurement is stored and no missing "
                   f"value is imputed",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_molecules", "args": {}},
            payload={"report": report})

    def _report_chemistry_coverage(self, query: Query) -> Solution:
        """Wires element_coverage.element_coverage_report.

        The element register is sparse.  The three honest repairs -- derive,
        estimate with the error measured, cross-check without merging -- are
        run and each is labelled with what it is.
        """
        report = eco.element_coverage_report()
        coverage = report["coverage"]
        derived = report["derived"]
        estimates = report["estimates"]
        model = estimates["model"]
        cross = report["cross_check"]

        steps = [
            Step("how sparse it actually is",
                 f"Across {coverage['elements']} elements and the measured "
                 f"fields there are {coverage['total_cells']} cells, of "
                 f"which {coverage['filled_cells']} are filled.  Three "
                 f"fields are complete "
                 f"({', '.join(coverage['complete_fields'])}); the sparsest "
                 f"is {coverage['sparsest']}.",
                 f"filled = {coverage['filled_cells']}/"
                 f"{coverage['total_cells']}, sparsest = "
                 f"{coverage['sparsest']}"),
            Step("derive: exact, and as reliable as its inputs",
                 f"{derived['attribute_count']} attributes are exact "
                 f"functions of fields already present -- molar volume, "
                 f"liquid range, Mulliken electronegativity, valence-shell "
                 f"load -- and together they add {derived['new_cells']} "
                 f"filled cells without a new measurement.",
                 f"derived attributes = {derived['attribute_count']}, new "
                 f"cells = {derived['new_cells']}"),
            Step("estimate: a line, fitted exactly, with its residuals",
                 f"The covalent radius is known for "
                 f"{estimates['measured_count']} elements.  A rational "
                 f"least-squares line against the atomic radius, fitted on "
                 f"exactly those {model['fitted_on']}, extends it to "
                 f"{estimates['estimate_count']} more -- coverage "
                 f"{estimates['coverage_before']} to "
                 f"{estimates['coverage_after']}.  The mean absolute "
                 f"residual is {q(model['mean_absolute_residual_pm'])} pm "
                 f"and the worst is {model['worst_element']} at "
                 f"{q(model['max_absolute_residual_pm'])} pm.  Every "
                 f"extended value is labelled 'estimated', and "
                 f"{len(estimates['still_absent'])} elements still have no "
                 f"atomic radius to estimate from and stay absent.",
                 f"fitted_on = {model['fitted_on']}, estimates = "
                 f"{estimates['estimate_count']}, mean |residual| = "
                 f"{q(model['mean_absolute_residual_pm'])} pm"),
            Step("cross-check: compare, do not merge",
                 cross["statement"],
                 f"compared = {cross['compared']}, agreeing within 20 "
                 f"kJ/mol = {cross['agree_within_20_count']}, largest "
                 f"difference = {cross['largest_difference']['element']} at "
                 f"{q(cross['largest_difference']['difference'])} kJ/mol"),
            Step("what it leaves alone",
                 report["limits"],
                 f"values written back into the element register = 0"),
        ]
        expected = {
            "elements": str(coverage["elements"]),
            "total_cells": str(coverage["total_cells"]),
            "filled_cells": str(coverage["filled_cells"]),
            "sparsest": str(coverage["sparsest"]),
            "derived_attribute_count": str(derived["attribute_count"]),
            "derived_new_cells": str(derived["new_cells"]),
            "fitted_on": str(model["fitted_on"]),
            "slope": q(model["slope"]),
            "intercept_pm": q(model["intercept_pm"]),
            "mean_absolute_residual_pm":
                q(model["mean_absolute_residual_pm"]),
            "estimate_count": str(estimates["estimate_count"]),
            "measured_count": str(estimates["measured_count"]),
            "coverage_before": str(estimates["coverage_before"]),
            "coverage_after": str(estimates["coverage_after"]),
            "cross_check_compared": str(cross["compared"]),
            "cross_check_agree_within_20":
                str(cross["agree_within_20_count"]),
            "largest_difference_element":
                str(cross["largest_difference"]["element"]),
        }
        return Solution(
            query=query, kind="report",
            answer=f"report chemistry coverage: "
                   f"{coverage['filled_cells']} of "
                   f"{coverage['total_cells']} measured cells are filled and "
                   f"the sparsest field is {coverage['sparsest']}; coverage "
                   f"is widened three ways that each keep their label -- "
                   f"{derived['attribute_count']} exactly derived "
                   f"attributes adding {derived['new_cells']} cells, a "
                   f"rational fit that carries the covalent radius from "
                   f"{estimates['coverage_before']} to "
                   f"{estimates['coverage_after']} of the elements with a "
                   f"mean residual of "
                   f"{q(model['mean_absolute_residual_pm'])} pm, and a "
                   f"cross-check against the diatomic register that reports "
                   f"the disagreement instead of merging the two "
                   f"quantities; nothing is written back into the register",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_chemistry_coverage", "args": {}},
            payload={"report": report})

    def _report_harmony(self, query: Query) -> Solution:
        """Wires hy.harmony_report -- the musical third of a claim, tested.

        The supplied study catalogue asserts that chemical equilibria, musical
        harmony and market price discovery all map to proximity in the Leech
        lattice.  The catalogue's verdict column recorded that as *not
        implemented*, because there was no musical register to run it against.
        There is one now, and the answer is not the one the sentence wants:
        proximity does order the intervals, but so does the same distance
        taken *before* the lattice decoder is applied, and the decoder
        reorders no pair.  What the measurement finds is the prime-exponent
        vector, which is what Tenney height already is.  The subject reports
        the statistic, the control beside it, and the verdict that follows.
        """
        report = hy.harmony_report()
        register = report["register"]
        temperament = report["temperament"]
        closure = report["closure"]
        consonance = report["consonance"]
        lattice = report["lattice"]
        control = lattice["control"]
        verdict = report["verdict"]
        because = verdict["because"]

        steps = [
            Step("a register that needs no measurement",
                 f"An interval is a ratio of two integers, so a musical "
                 f"register is arithmetic rather than data: nothing is "
                 f"measured, nothing is calibrated, and no float exists.  "
                 f"All {register['count']} intervals carry 24 coordinates "
                 f"derived from the pair (n, d) alone, which is why the "
                 f"codec reads the ratio back from two of them and cannot "
                 f"disagree with the other twenty-two.",
                 f"{register['count']} intervals ({register['just']} just, "
                 f"{register['septimal']} septimal, {register['commas']} "
                 f"commas), prime limits {list(register['prime_limits'])}"),
            Step("equal temperament misses everything but the octave",
                 f"The nearest equal step is decided by comparing r^24 "
                 f"against powers of two -- integers, not logarithms -- and "
                 f"the error is the exact rational (n/d)^12 / 2^k.  It is 1 "
                 f"for the unison and the octave and for nothing else, and "
                 f"RequestProject/GLM/Harmony.lean proves that no ratio "
                 f"carrying an odd prime can ever be a step of any equal "
                 f"division of the octave, for any number of divisions.",
                 f"tempered exactly: "
                 f"{', '.join(temperament['tempered_exactly'])}; the fifth "
                 f"is off by {q(temperament['fifth_error'])}, the third by "
                 f"{q(temperament['third_error'])}; worst missed "
                 f"{temperament['worst_missed']}, best missed "
                 f"{temperament['best_missed']}"),
            Step("the circle of fifths is not a circle",
                 f"Stacking fifths never returns to an octave: (3/2)^n is "
                 f"3^n over 2^n in lowest terms, and 3^n is odd.  Searched "
                 f"to n = {closure['bound']} here, and closed for every n in "
                 f"Lean.  Twelve fifths overshoot seven octaves by the "
                 f"Pythagorean comma; four fifths overshoot the just major "
                 f"third by the syntonic comma.  Both are exact.",
                 f"closures found {list(closure['closures'])}; twelve "
                 f"fifths over seven octaves "
                 f"{q(closure['twelve_fifths_over_seven_octaves'])}; four "
                 f"fifths over the third "
                 f"{q(closure['four_fifths_over_major_third'])}"),
            Step("two measures of consonance, and how far they agree",
                 f"Tenney height (n * d, before anyone takes a logarithm) "
                 f"against Euler's gradus suavitatis.  Kendall's tau between "
                 f"them is exact and rational.  They agree at the simple end "
                 f"and part company further out, which is why the lattice "
                 f"test below is run against both rather than against a "
                 f"favourite.",
                 f"tau {q(consonance['tau'])}; simplest by Tenney "
                 f"{list(consonance['simplest_by_tenney'])}; simplest by "
                 f"gradus {list(consonance['simplest_by_gradus'])}"),
            Step("the claim, and the control that decides it",
                 f"Each interval is sent to its nearest Leech point through "
                 f"its prime exponents -- deliberately not through its "
                 f"carrier, which holds consonance outright and would make "
                 f"the claim true by construction.  At scale "
                 f"{lattice['best_scale']} the lattice separates all "
                 f"{lattice['interval_count']} intervals and distance from "
                 f"the unison orders them at tau "
                 f"{q(lattice['best_tau_tenney'])}.  The control is that "
                 f"same distance measured before the decoder runs, and it "
                 f"scores {q(control['tau_tenney'])}.",
                 f"best scale {lattice['best_scale']}, distinct points "
                 f"{lattice['best_distinct']}, tau against Tenney "
                 f"{q(lattice['best_tau_tenney'])} versus control "
                 f"{q(control['tau_tenney'])}; pairs the decoder reorders "
                 f"{lattice['best_reordered_pairs']}"),
            Step("what is recorded",
                 f"A finding that survives its control is a finding; one "
                 f"that does not is a change of coordinates.  "
                 f"{because[0].upper()}{because[1:]}.",
                 f"verdict {verdict['verdict']} (separated "
                 f"{verdict['separated']}, ordered {verdict['ordered']}, "
                 f"beats control {verdict['beats_control']})"),
        ]

        expected = {
            "intervals": str(register["count"]),
            "just": str(register["just"]),
            "septimal": str(register["septimal"]),
            "commas": str(register["commas"]),
            "tempered_exactly": ",".join(temperament["tempered_exactly"]),
            "fifth_error": q(temperament["fifth_error"]),
            "third_error": q(temperament["third_error"]),
            "closures": ",".join(str(n) for n in closure["closures"]),
            "pythagorean_comma":
                q(closure["twelve_fifths_over_seven_octaves"]),
            "syntonic_comma": q(closure["four_fifths_over_major_third"]),
            "consonance_tau": q(consonance["tau"]),
            "best_scale": str(lattice["best_scale"]),
            "best_distinct": str(lattice["best_distinct"]),
            "best_tau_tenney": q(lattice["best_tau_tenney"]),
            "best_tau_gradus": q(lattice["best_tau_gradus"]),
            "control_tau_tenney": q(control["tau_tenney"]),
            "reordered_pairs": str(lattice["best_reordered_pairs"]),
            "beats_control": str(lattice["beats_control"]),
            "verdict": verdict["verdict"],
        }

        return Solution(
            query=query, kind="report",
            answer=f"report harmony: {register['count']} intervals held as "
                   f"exact ratios; equal temperament is exact for "
                   f"{' and '.join(temperament['tempered_exactly'])} and for "
                   f"nothing else, missing the fifth by "
                   f"{q(temperament['fifth_error'])}; no stack of fifths is "
                   f"a stack of octaves up to n = {closure['bound']}, and by "
                   f"Harmony.lean none ever is; Tenney height and Euler's "
                   f"gradus agree at tau {q(consonance['tau'])}; the Leech "
                   f"lattice separates all {lattice['interval_count']} "
                   f"intervals at scale {lattice['best_scale']} and orders "
                   f"them at tau {q(lattice['best_tau_tenney'])} -- but the "
                   f"undecoded control scores {q(control['tau_tenney'])} and "
                   f"the decoder reorders {lattice['best_reordered_pairs']} "
                   f"pairs, so the catalogue's claim is recorded as "
                   f"{verdict['verdict']}",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_harmony", "args": {}},
            payload={"report": noise_payload(report)})

    def _report_economics(self, query: Query) -> Solution:
        """Wires ecn.economics_report -- the economic third of that claim.

        The same catalogue sentence has a third part, market price discovery,
        and it was recorded as *not implemented* because there was no
        register of prices to run it against.  There is one now: 21 quoted
        prices as exact rationals over seven instruments and three
        consecutive quarters, with every magnitude computed by integer
        comparison rather than by a logarithm.  The answer is again not the
        one the sentence wants.  Proximity does track the market -- every
        record's nearest neighbour is another quarter of the same instrument
        -- but the undecoded control does exactly as well, so what the
        measurement finds is the price vector and not the geometry of the
        Leech lattice.
        """
        report = ecn.economics_report()
        register = report["register"]
        lattice = report["lattice"]
        control = lattice["control"]
        best = lattice["best_comovement"]
        control_co = control["comovement"]
        verdict = report["verdict"]
        because = verdict["because"]
        magnitudes = report["magnitudes"]

        steps = [
            Step("a price register with no float in it",
                 f"Every price is stored as a fraction and parsed with "
                 f"Fraction, so the register keeps the same exact-rational "
                 f"contract as the rest of the package.  It is a time "
                 f"series rather than a snapshot -- {register['windows']} "
                 f"consecutive quarters of each instrument -- which is what "
                 f"lets co-movement be measured rather than assumed.",
                 f"{register['records']} records, "
                 f"{register['instruments']} instruments, "
                 f"{register['sectors']} sectors, "
                 f"{register['windows']} windows, "
                 f"{register['currency_pairs']} currency pairs"),
            Step("a magnitude without a logarithm",
                 f"floor(log_b x) is computed by integer multiplication: k "
                 f"is the unique integer with b^k <= x < b^(k+1), decided by "
                 f"comparing q*b^k against p.  Existence, uniqueness, "
                 f"agreement with those integer comparisons and monotonicity "
                 f"are proved in RequestProject/GLM/LogBucket.lean.  The "
                 f"mantissa x / b^k is kept beside the bucket, which is what "
                 f"separates two quarters of one instrument that share a "
                 f"bucket.",
                 f"base-2 buckets {list(register['base_2_buckets'])}, span "
                 f"{register['base_2_bucket_span']}; bounds hold for all "
                 f"{len(magnitudes)} rows: {register['all_bounds_hold']}"),
            Step("where the lattice stops conflating prices",
                 f"Each record becomes a 24-vector of buckets, mantissas, "
                 f"EXT10 exponents and a currency flag, scaled and decoded "
                 f"to the nearest Leech point.  At scale 1 the decoder sees "
                 f"only {lattice['rows'][0]['distinct_points']} distinct "
                 f"points among {lattice['record_count']} records; the "
                 f"sweep separates them all only at scale "
                 f"{lattice['best_scale']}, because the closest pair has to "
                 f"be pushed past the covering radius first.",
                 f"fully separated at {list(lattice['fully_separated'])}; "
                 f"best scale {lattice['best_scale']}, distinct "
                 f"{lattice['best_distinct']} of {lattice['record_count']}"),
            Step("co-movement, and the chance rate it has to beat",
                 f"Two of the twenty other records are another quarter of "
                 f"the same instrument, so {q(ecn.CHANCE_SAME_INSTRUMENT)} "
                 f"is what a nearest neighbour scores by luck.  Distance "
                 f"from the origin also orders the records by magnitude, at "
                 f"an exact Kendall tau against the base-2 bucket.",
                 f"co-movement {best['hits']}/{best['of']} = "
                 f"{q(best['rate'])} against chance "
                 f"{q(ecn.CHANCE_SAME_INSTRUMENT)}; tau against magnitude "
                 f"{q(lattice['best_tau_magnitude'])}"),
            Step("the control, and what it leaves of the claim",
                 f"The same distances taken before the decoder runs.  "
                 f"Scaling every coordinate by one positive factor cannot "
                 f"reorder distances, so the control is one set of numbers "
                 f"for the whole sweep.  "
                 f"{because[0].upper()}{because[1:]}.",
                 f"control co-movement {control_co['hits']}/"
                 f"{control_co['of']}, control tau "
                 f"{q(control['tau_magnitude'])}; beats control "
                 f"{lattice['beats_control']}; verdict "
                 f"{verdict['verdict']}"),
        ]

        expected = {
            "records": str(register["records"]),
            "instruments": str(register["instruments"]),
            "windows": str(register["windows"]),
            "currency_pairs": str(register["currency_pairs"]),
            "all_bounds_hold": str(register["all_bounds_hold"]),
            "base_2_bucket_span": str(register["base_2_bucket_span"]),
            "best_scale": str(lattice["best_scale"]),
            "best_distinct": str(lattice["best_distinct"]),
            "fully_separated": ",".join(str(s)
                                        for s in lattice["fully_separated"]),
            "best_tau_magnitude": q(lattice["best_tau_magnitude"]),
            "comovement": q(best["rate"]),
            "chance_rate": q(ecn.CHANCE_SAME_INSTRUMENT),
            "control_comovement": q(control_co["rate"]),
            "control_tau_magnitude": q(control["tau_magnitude"]),
            "beats_control": str(lattice["beats_control"]),
            "verdict": verdict["verdict"],
        }

        return Solution(
            query=query, kind="report",
            answer=f"report economics: {register['records']} quoted prices "
                   f"as exact rationals over {register['instruments']} "
                   f"instruments and {register['windows']} quarters, every "
                   f"magnitude bucket decided by integer comparison rather "
                   f"than by a logarithm; the Leech lattice first separates "
                   f"all {lattice['record_count']} of them at scale "
                   f"{lattice['best_scale']}, orders them by magnitude at "
                   f"tau {q(lattice['best_tau_magnitude'])}, and every "
                   f"record's nearest neighbour is another quarter of the "
                   f"same instrument ({best['hits']}/{best['of']} against a "
                   f"chance rate of {q(ecn.CHANCE_SAME_INSTRUMENT)}) -- but "
                   f"the undecoded control scores "
                   f"{control_co['hits']}/{control_co['of']} with no lattice "
                   f"at all, so the catalogue's economic claim is recorded "
                   f"as {verdict['verdict']}",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_economics", "args": {}},
            payload={"report": noise_payload(report)})

    def _report_analogies(self, query: Query) -> Solution:
        """Wires analogy_models.analogy_models_report -- analogy by relation.

        Every case is re-solved here and now through the model layer, and
        each row says which model recognised the relation, what it answered,
        and whether that is what the mathematics of the case requires.  A
        refusal is a row like any other: the periodic step that lands on
        group 3 of period 6 has no single element to name.
        """
        report = am.analogy_models_report()
        table = report["periodic_table"]
        lines = "; ".join(
            f"{row['question']} -> "
            f"{row['answer'] or 'refused'} [{row['model']}]"
            for row in report["cases"])
        steps = [
            Step("the models",
                 "An analogy is transported as a *named relation* wherever "
                 "the register states one, and as a displacement of the "
                 "coordinates only when it does not.",
                 f"models = {list(report['models'])}"),
            Step("the table's own coordinates",
                 f"The chemistry model needs a period and a group, and the "
                 f"register stores a group-block *category*, not a group.  "
                 f"Both are derived from the period boundaries and checked "
                 f"against the {table['elements']} stored periods.",
                 f"elements = {table['elements']}, "
                 f"periods_agree_with_register = "
                 f"{table['periods_agree_with_register']}, "
                 f"noble gases = {table['noble_gases']}"),
            Step("what is not transportable",
                 "A relation that records *that* two concepts are linked "
                 "without saying how determines no answer, so it is excluded "
                 "by name rather than followed to a guess.",
                 f"vague relations = {list(report['vague_relations'])}"),
            Step("the cases",
                 f"{report['cases_total']} analogies re-solved through the "
                 f"layer; {report['cases_as_expected']} came out as the "
                 f"mathematics of the case requires.",
                 lines),
        ]
        expected = {
            "cases_total": str(report["cases_total"]),
            "cases_as_expected": str(report["cases_as_expected"]),
            "models": str(list(report["models"])),
            "periods_agree_with_register":
                str(table["periods_agree_with_register"]),
            "noble_gases": str(list(table["noble_gases"])),
        }
        for row in report["cases"]:
            expected[f"case_{row['question']}"] = (
                f"{row['model']}:{row['answer']}")
        return Solution(
            query=query, kind="report",
            answer=(f"report analogies: {len(report['models'])} relation "
                    f"models, {report['cases_total']} cases, "
                    f"{report['cases_as_expected']} as expected"),
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_analogies", "args": {}},
            payload={"report": report})
