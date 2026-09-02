"""``glm_universal.runtime.reports.ledgers``
-- the subjects that recompute a document as a claim ledger.

Reports that turn a document, or a probe set, into live verdicts.

The unification blueprint, the study findings catalogue and the two
companion preprints, each recomputed claim by claim; the capability probes
and what they say stops; and the benchmark suites.

Every method here is a solver for one ``report <subject>`` query.  They are
mixed into :class:`glm_universal.runtime.session.GeometricSession`,
which is where ``self`` comes from: the loaded registers, the concept index
and the shared helpers.  Splitting them out of the session keeps each family
beside a docstring that says which sub-package computes it, and keeps the
dispatcher readable as a dispatcher.
"""
from __future__ import annotations

from ...reasoning import blueprint as bp
from ...reasoning import catalog as cat
from ...reasoning import companion as cpn

from ..parser import Query
from ..solution import Solution, Step


class LedgerReports:
    """The subjects that recompute a document as a claim ledger.

    A mixin of :class:`~glm_universal.runtime.session.GeometricSession`;
    it holds no state of its own.
    """

    def _report_blueprint(self, query: Query) -> Solution:
        """Wires bp.blueprint_report -- the unification blueprint, tested.

        The blueprint is a specification document.  This subject turns it
        into a ledger: every testable sentence is recomputed against the
        package as it stands and given a verdict, so a claim that drifts away
        from the code is a changed verdict rather than a sentence nobody
        rechecked.
        """
        report = bp.blueprint_report()
        tally = report["tally"]
        audit = report["source_audit"]
        rate = report["delta_sigma_rate"]
        claims = report["claims"]

        def _by(verdict: str) -> str:
            named = [f"{c['section']}" for c in claims
                     if c["verdict"] == verdict]
            return ", ".join(named) or "none"

        steps = [
            Step("what is being tested",
                 f"Each sentence of the blueprint that names a figure, a "
                 f"count or a behaviour is restated here as a claim and "
                 f"recomputed from the package.  Nothing is quoted: the "
                 f"figure beside a claim is produced by the call that "
                 f"settles it.",
                 f"{report['claim_count']} claims across sections "
                 f"{', '.join(sorted(report['sections']))}"),
            Step("the discipline, read off the source",
                 f"Section 1 states the Universal Binary Principle as a "
                 f"commitment.  It is tested as a property instead: every "
                 f"module is parsed, and float literals, float "
                 f"constructions and imports of random, hashing or "
                 f"floating-point libraries are counted.  A float named "
                 f"only inside an isinstance guard is the discipline being "
                 f"enforced, and is not counted against it.",
                 f"{audit['modules_scanned']} modules scanned, "
                 f"{audit['core_modules']} in the six sub-packages the "
                 f"claim covers; core clean {audit['core_clean']}; "
                 f"{len(audit['outside_core_violations'])} modules outside "
                 f"the core do construct floats"),
            Step("the value layer's rate",
                 f"The modulator's claimed O(1/N) convergence is measured "
                 f"rather than asserted: for each target and step count the "
                 f"exact error of the running average is compared against "
                 f"the 1/N envelope, and the bits it clears against the "
                 f"blueprint's log2(N+1).",
                 f"{rate['row_count']} rows, all inside the envelope: "
                 f"{rate['all_within_one_over_n']}; bits cleared are at "
                 f"least log2(N+1) in every row: "
                 f"{rate['always_at_least_claimed_bits']}"),
            Step("the verdicts",
                 f"A claim is confirmed when the package reproduces its "
                 f"figure exactly, refuted when the package reproduces a "
                 f"different one, not reproduced when the measurement it "
                 f"names does not show what it says, and not implemented "
                 f"when it describes a subsystem the package does not have. "
                 f"The last is an open gap, recorded rather than passed "
                 f"over.",
                 f"confirmed {tally[bp.CONFIRMED]} "
                 f"(sections {_by(bp.CONFIRMED)}); "
                 f"refuted {tally[bp.REFUTED]} "
                 f"(sections {_by(bp.REFUTED)}); "
                 f"not reproduced {tally[bp.NOT_REPRODUCED]} "
                 f"(sections {_by(bp.NOT_REPRODUCED)}); "
                 f"not implemented {tally[bp.NOT_IMPLEMENTED]} "
                 f"(sections {_by(bp.NOT_IMPLEMENTED)})"),
        ]

        expected = {
            "claim_count": str(report["claim_count"]),
            "confirmed": str(tally[bp.CONFIRMED]),
            "refuted": str(tally[bp.REFUTED]),
            "not_reproduced": str(tally[bp.NOT_REPRODUCED]),
            "not_implemented": str(tally[bp.NOT_IMPLEMENTED]),
            "sections": ",".join(sorted(report["sections"])),
            "core_modules": str(audit["core_modules"]),
            "core_clean": str(audit["core_clean"]),
            "outside_core_violations": str(
                len(audit["outside_core_violations"])),
            "rate_rows": str(rate["row_count"]),
            "all_within_one_over_n": str(rate["all_within_one_over_n"]),
        }
        for index, entry in enumerate(claims):
            expected[f"verdict_{index}"] = str(entry["verdict"])
            expected[f"section_{index}"] = str(entry["section"])

        return Solution(
            query=query, kind="report",
            answer=f"report blueprint: {report['reading']}",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_blueprint", "args": {}},
            payload={"report": report})

    def _report_catalog(self, query: Query) -> Solution:
        """Wires cat.catalog_report -- the external study findings, tested.

        A catalogue of findings from studies run outside this package is a
        document.  This subject turns it into a ledger: every sentence of it
        that names a figure, a count or a behaviour is recomputed here and
        given a verdict, so a finding that the package cannot reproduce is a
        recorded disagreement rather than an unexamined claim.
        """
        report = cat.catalog_report()
        tally = report["tally"]
        claims = report["claims"]

        def _by(verdict: str) -> str:
            named = sorted({str(c["section"]) for c in claims
                            if c["verdict"] == verdict})
            return ", ".join(named) or "none"

        steps = [
            Step("what is being tested",
                 f"Each finding of the catalogue that names a figure, a "
                 f"count or a behaviour is restated as a claim and "
                 f"recomputed from the package.  Nothing is quoted: the "
                 f"figure beside a claim is produced by the call that "
                 f"settles it, in exact arithmetic.",
                 f"{report['claim_count']} claims across sections "
                 f"{', '.join(report['section_labels'])}"),
            Step("where the studies are reproduced",
                 f"A claim is confirmed when the package reproduces its "
                 f"figure exactly.  The drift ladder, the code-to-lattice "
                 f"chain up to the Leech lattice, the generator step costs, "
                 f"the spectral columns, the reversibility protocols and the "
                 f"oscillator's SNR identity are all in this class.",
                 f"confirmed {tally[cat.CONFIRMED]} "
                 f"(sections {_by(cat.CONFIRMED)})"),
            Step("where they are not",
                 f"Refuted means the package reproduces a different figure, "
                 f"and says which.  Not reproduced means the measurement the "
                 f"claim names does not show what the claim says it shows -- "
                 f"typically because the study's own column is a function of "
                 f"its input rather than a measurement of its run.",
                 f"refuted {tally[cat.REFUTED]} "
                 f"(sections {_by(cat.REFUTED)}); "
                 f"not reproduced {tally[cat.NOT_REPRODUCED]} "
                 f"(sections {_by(cat.NOT_REPRODUCED)})"),
            Step("the open gaps",
                 f"Not implemented is a subsystem the package does not have. "
                 f"It is recorded as an open gap rather than passed over, "
                 f"and it is the honest reading of what would have to be "
                 f"built for the finding to be testable here at all.",
                 f"not implemented {tally[cat.NOT_IMPLEMENTED]} "
                 f"(sections {_by(cat.NOT_IMPLEMENTED)})"),
        ]

        expected = {
            "claim_count": str(report["claim_count"]),
            "sections": str(report["sections"]),
            "section_labels": ",".join(report["section_labels"]),
            "confirmed": str(tally[cat.CONFIRMED]),
            "refuted": str(tally[cat.REFUTED]),
            "not_reproduced": str(tally[cat.NOT_REPRODUCED]),
            "not_implemented": str(tally[cat.NOT_IMPLEMENTED]),
        }
        for index, entry in enumerate(claims):
            expected[f"verdict_{index}"] = str(entry["verdict"])
            expected[f"section_{index}"] = str(entry["section"])

        return Solution(
            query=query, kind="report",
            answer=f"report catalog: {report['reading']}",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_catalog", "args": {}},
            payload={"report": report})

    def _report_companion(self, query: Query) -> Solution:
        """Wires cpn.companion_report -- the two companion studies, tested.

        The study catalogue this package already audits is a summary of these
        two preprints, and a summary drops the definitions.  This subject
        reads the preprints' own tables and tests them row by row against the
        definitions the preprints give, so a figure that turns on an
        unstated parameter is recorded as such rather than guessed at.
        """
        report = cpn.companion_report()
        tally = report["tally"]
        claims = report["claims"]

        def _by(verdict: str) -> str:
            named = sorted({str(c["section"]) for c in claims
                            if c["verdict"] == verdict})
            return ", ".join(named) or "none"

        steps = [
            Step("what is being tested",
                 f"The two companion studies state the definitions their "
                 f"summary omits: the projection the hull census uses, the "
                 f"indexing the convergence table counts in, and the "
                 f"alphabet the autocorrelation column is computed on.  Each "
                 f"testable sentence is restated as a claim and recomputed "
                 f"from the package.",
                 f"{report['claim_count']} claims across sections "
                 f"{', '.join(report['sections'])}; "
                 + "; ".join(f"{count} from {cpn.STUDIES[prefix]}"
                             for prefix, count
                             in report["claims_by_study"].items())),
            Step("what the definitions settle",
                 f"Several verdicts turn on a definition rather than on a "
                 f"measurement.  With the stated projection the whole "
                 f"target-norm column reproduces; with the uncentred "
                 f"product on the +/-1 alphabet the whole autocorrelation "
                 f"column does; and with steps counted from x_0 five of the "
                 f"eight convergence rows do.",
                 f"confirmed {tally[cpn.CONFIRMED]} "
                 f"(sections {_by(cpn.CONFIRMED)})"),
            Step("where the studies are wrong",
                 f"Refuted means the package reproduces a different figure "
                 f"and records what is true instead.  The largest group is "
                 f"the hull census: a sample of witnesses can establish that "
                 f"a point is inside a hull and can never establish that it "
                 f"is outside, so the study's outside verdicts are "
                 f"unestablished by its own method -- and two of them are "
                 f"wrong.",
                 f"refuted {tally[cpn.REFUTED]} "
                 f"(sections {_by(cpn.REFUTED)})"),
            Step("what cannot be settled",
                 f"Not reproduced means a parameter the figure depends on is "
                 f"never stated -- the congruential generator's seed, or the "
                 f"definition of the margin column.  Not implemented means a "
                 f"structure the package does not have, and is an open gap "
                 f"rather than a pass.",
                 f"not reproduced {tally[cpn.NOT_REPRODUCED]} "
                 f"(sections {_by(cpn.NOT_REPRODUCED)}); "
                 f"not implemented {tally[cpn.NOT_IMPLEMENTED]} "
                 f"(sections {_by(cpn.NOT_IMPLEMENTED)})"),
        ]

        expected = {
            "claim_count": str(report["claim_count"]),
            "sections": ",".join(report["sections"]),
            "confirmed": str(tally[cpn.CONFIRMED]),
            "refuted": str(tally[cpn.REFUTED]),
            "not_reproduced": str(tally[cpn.NOT_REPRODUCED]),
            "not_implemented": str(tally[cpn.NOT_IMPLEMENTED]),
            "claims_by_study": ",".join(
                f"{prefix}:{count}"
                for prefix, count in report["claims_by_study"].items()),
        }
        for index, entry in enumerate(claims):
            expected[f"verdict_{index}"] = str(entry["verdict"])
            expected[f"section_{index}"] = str(entry["section"])

        return Solution(
            query=query, kind="report",
            answer=f"report companion: {report['reading']}",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_companion", "args": {}},
            payload={"report": report})

    def _report_capabilities(self, query: Query) -> Solution:
        """Wires capabilities.capability_report -- what works and what stops.

        Each probe states a capability in a user's words and comes back either
        holding, with how far it was pushed, or breaking, with the place it
        stops.  A probe whose verdict differs from what was expected is
        surfaced as a surprise rather than buried.
        """
        from ... import capabilities as cap
        report = cap.capability_report()
        areas = ", ".join(
            f"{area} {counts['holds']}/{counts['holds'] + counts['breaks']}"
            for area, counts in report["by_area"].items())
        boundary_lines = "; ".join(
            f"{b['name']}" for b in report["boundaries"])

        steps = [
            Step("what was asked",
                 f"{report['probes']} capability probes, each a question a "
                 f"user might ask of the machine, put to the real code.  A "
                 f"probe that breaks is a located boundary, not a failure.",
                 f"holds {report['holds']}, breaks {report['breaks']}, "
                 f"errors {report['errors']}"),
            Step("by area",
                 "Where the machine is solid and where it is thin.",
                 areas),
            Step("where it breaks",
                 "Each of these carries the exact place the capability "
                 "stops.  Several are theorems and will not move: the Golay "
                 "repair radius, the undecidability of equality between "
                 "processes, the convex hull that bounds the 24-D carrier.",
                 boundary_lines),
            Step("surprises",
                 "A probe whose verdict differs from the expectation "
                 "declared before it ran: a regression, or a capability "
                 "newly won.",
                 str(report["surprises"]) if report["surprises"] else "none"),
        ]

        expected = {
            "probes": str(report["probes"]),
            "holds": str(report["holds"]),
            "breaks": str(report["breaks"]),
            "errors": str(report["errors"]),
            "surprises": str(report["surprises"]),
        }
        for result in report["results"]:
            expected[f"verdict_{result['name']}"] = str(result["verdict"])

        return Solution(
            query=query, kind="report",
            answer=f"report capabilities: {report['probes']} probes, "
                   f"{report['holds']} hold, {report['breaks']} break, "
                   f"{report['errors']} errored; surprises "
                   f"{report['surprises'] or 'none'}",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_capabilities", "args": {}},
            payload={"report": report})

    def _report_benchmarks(self, query: Query) -> Solution:
        """Wires benchmarks.benchmark_report -- the scored task suites.

        Imported here rather than at module scope: the suites drive queries
        through this very session class, so a top-level import would be
        circular.
        """
        from ... import benchmarks as bm

        report = bm.benchmark_report()
        suites = report["suites"]
        nulls = report["null_results"]

        tiers = ", ".join(f"{s['name']} {s['tier']['tier']}" for s in suites)
        scores = ", ".join(
            f"{s['name']} {s['passed']}/{s['total']} vs {s['baseline']}"
            for s in suites)

        steps = [
            Step("declared before the run",
                 f"Each of the {report['suite_count']} suites fixes its "
                 f"population, its ground truth, what counts as a pass, what "
                 f"a baseline would score and what a null result would look "
                 f"like, before it is run.  A score is reported only "
                 f"together with that declaration.",
                 f"tiers: {tiers}"),
            Step("scores",
                 f"{report['passed_count']} of {report['task_count']} tasks "
                 f"pass, each against the baseline its own suite declared.  "
                 f"The ratios are exact rationals; no score is a float.",
                 f"{scores}\noverall = {report['overall_score']}"),
            Step("null and negative results",
                 f"A suite that only reported its wins would be a broken "
                 f"suite.  {len(report['findings'])} findings are reported "
                 f"beside the scores, including every failing task and every "
                 f"known failure mode measured rather than asserted.",
                 "; ".join(f"[{f['suite']}/{f['key']}] {f['statement']}"
                           for f in report["findings"])),
            Step("reproducibility",
                 f"The run id is a hash of the results themselves, so the "
                 f"same code produces the same id and a changed number is "
                 f"visible as a changed id.  No suite samples without a "
                 f"recorded seed.",
                 f"run_id = {report['run_id']}"),
        ]

        expected = {
            "suite_count": str(report["suite_count"]),
            "task_count": str(report["task_count"]),
            "passed_count": str(report["passed_count"]),
            "overall_score": str(report["overall_score"]),
            "run_id": str(report["run_id"]),
            "null_result_count": str(len(nulls)),
        }
        for suite in suites:
            name = suite["name"]
            expected[f"score_{name}"] = str(suite["score"])
            expected[f"baseline_{name}"] = str(suite["baseline"])
            expected[f"verdict_{name}"] = str(suite["verdict"])

        return Solution(
            query=query, kind="report",
            answer=f"report benchmarks: {report['passed_count']}/"
                   f"{report['task_count']} tasks "
                   f"({report['overall_score']}) across "
                   f"{report['suite_count']} suites; {scores}; "
                   + (f"null or below-baseline: {', '.join(nulls)}"
                      if nulls else "every suite beat its baseline"),
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_benchmarks", "args": {}},
            payload={"report": report})
