"""``glm_universal.runtime.reports.development``
-- the subjects that read the development itself.

Reports whose subject is this repository.

The Leech address of every Lean declaration, the standing directives paired
with the instrument that would fail if one were broken, and the stage each
piece of work has reached, computed from the tree.

Every method here is a solver for one ``report <subject>`` query.  They are
mixed into :class:`glm_universal.runtime.session.GeometricSession`,
which is where ``self`` comes from: the loaded registers, the concept index
and the shared helpers.  Splitting them out of the session keeps each family
beside a docstring that says which sub-package computes it, and keeps the
dispatcher readable as a dispatcher.
"""
from __future__ import annotations

from ...reasoning import directives as drc
from ...reasoning import lean_address as lad
from ...reasoning import pipeline as ppl

from ..parser import Query
from ..solution import Solution, Step, q


class DevelopmentReports:
    """The subjects that read the development itself.

    A mixin of :class:`~glm_universal.runtime.session.GeometricSession`;
    it holds no state of its own.
    """

    def _report_lean(self, query: Query) -> Solution:
        """Wires lad.lean_address_report -- Leech addresses for Lean results.

        Every declaration of the formal development is reduced to twenty four
        structural counts and sent to its nearest Leech point, so a machine-
        checked result sits in the same space, and answers to the same metric,
        as a physical carrier.  The subject reports what that buys and what it
        does not: the encoding is lossless, the conflation it does cause is
        the feature map's and not the quantiser's, and a control addressed by
        the SHA-256 of its name scores at chance on the same statistic.
        """
        report = lad.lean_address_report()
        if not report.get("available"):
            return Solution(
                query=query, kind="report",
                answer="report lean: no address book has been written; run "
                       "`python -m glm_universal.tools lean-address "
                       "--write` from the directory holding glm_universal/",
                steps=(), expected={"available": "False"},
                script_spec=None, payload={})
        corpus = report["corpus"]
        cache = report["cache"]
        guarantee = report["guarantee"]
        trip = report["round_trip"]
        sep = report["separation"]
        feature = sep["feature"]
        control = sep["hash_control"]
        null = sep["shuffled"]
        inj = feature["injectivity"]
        spoken = report["spoken"][0] if report["spoken"] else None

        steps = [
            Step("the corpus, and the digest it is addressed against",
                 f"The address book is computed once -- one exact "
                 f"nearest-point decode per declaration -- and stored beside "
                 f"the SHA-256 digest of the Lean tree it was computed from. "
                 f"Every read recomputes that digest, so a single changed "
                 f"byte makes the book report itself stale instead of "
                 f"answering from a cache that no longer describes the "
                 f"sources.",
                 f"{corpus['declarations']} declarations in "
                 f"{corpus['files']} files, "
                 + ", ".join(f"{k} {v}" for k, v in corpus["by_kind"].items())
                 + f"; cache {cache['verdict']}"),
            Step("what is encoded: real information, not a digest",
                 f"A declaration becomes 24 integer counts -- quantifiers, "
                 f"connectives, equalities, order relations, carrier types, "
                 f"statement size, how many results it cites and how many "
                 f"cite it, namespace depth, kind.  Not its name, not its "
                 f"file: so 'declarations from one file land near each "
                 f"other' is a prediction this can fail, not an assumption "
                 f"built in.",
                 f"{len(lad.FEATURE_NAMES)} coordinates capped at "
                 f"{lad.CAP}, scale {report['features']['scale']}"),
            Step("the encoding is lossless, and provably so",
                 f"The covering radius of the lattice in this integer model "
                 f"is {guarantee['covering_radius']}, so quantising moves no "
                 f"coordinate by more than that; a scale above twice the "
                 f"radius therefore keeps every coordinate inside half a "
                 f"step and the feature vector is recovered exactly.  Scale "
                 f"9 rather than 8 because 8Z^24 lies inside the lattice, so "
                 f"at scale 8 the decoder would return its input and the "
                 f"address would be a relabelled cube "
                 f"(RequestProject/GLM/Address.lean: eightZ_mem_leech, "
                 f"readback_unique).",
                 f"moved by the decoder {guarantee['moved_by_the_decoder']}/"
                 f"{guarantee['declarations']}, worst residual "
                 f"{guarantee['worst_observed_residual']} against half-step "
                 f"{q(guarantee['half_step'])}, read back exactly "
                 f"{trip['exact']}/{trip['checked']}, coordinate errors "
                 f"{trip['coordinate_errors']}/{trip['coordinates_checked']}"),
            Step("what the address conflates is the feature map's doing",
                 f"Distinct addresses number exactly as many as distinct "
                 f"feature vectors, so the quantiser adds no conflation of "
                 f"its own: every collision is two declarations the features "
                 f"genuinely cannot tell apart, which is the boundary of "
                 f"this layer in the sense of Layers.lean.",
                 f"{inj['distinct_addresses']} distinct addresses for "
                 f"{inj['declarations']} declarations, "
                 f"{inj['collision_classes']} classes, largest "
                 f"{inj['largest_class_size']}, quantisation adds none "
                 f"{inj['quantisation_adds_no_conflation']}"),
            Step("does the address mean anything?  measured, against controls",
                 f"For each declaration, take its nearest neighbour by "
                 f"address and ask whether that neighbour comes from the "
                 f"same file, and whether the two cite one another.  The "
                 f"structural scheme is scored against a SHA-256-of-the-name "
                 f"control, which is deterministic and knows nothing, and "
                 f"against a seeded reshuffle of the same addresses, which "
                 f"has the same geometry and no pairing.",
                 f"same file: feature "
                 f"{feature['neighbours']['same_file_nearest']}/"
                 f"{feature['neighbours']['declarations']}, hash control "
                 f"{control['neighbours']['same_file_nearest']}, shuffled "
                 f"{null['neighbours']['same_file_nearest']}, chance "
                 f"{q(feature['neighbours']['same_file_chance'])}; cited "
                 f"either way: {feature['neighbours']['linked_nearest']} "
                 f"against chance "
                 f"{q(feature['neighbours']['linked_chance'])}"),
        ]
        if spoken is not None:
            steps.append(Step(
                "speaking one back",
                f"The address is read back into the sentence it came from -- "
                f"which is what 'the machine speaks Lean' amounts to: not the "
                f"proof, but the shape of the statement and its place in the "
                f"development.",
                f"{spoken['name']}: {spoken['sentence']}; nearest "
                + ", ".join(n["name"] for n in spoken["neighbours"])))

        expected = {
            "declarations": str(corpus["declarations"]),
            "files": str(corpus["files"]),
            "cache_verdict": str(cache["verdict"]),
            "scale": str(report["features"]["scale"]),
            "covering_radius": str(guarantee["covering_radius"]),
            "moved": str(guarantee["moved_by_the_decoder"]),
            "worst_residual": str(guarantee["worst_observed_residual"]),
            "read_back_exact": str(trip["exact"]),
            "coordinate_errors": str(trip["coordinate_errors"]),
            "distinct_addresses": str(inj["distinct_addresses"]),
            "distinct_features": str(inj["distinct_feature_vectors"]),
            "collision_classes": str(inj["collision_classes"]),
            "largest_class": str(inj["largest_class_size"]),
            "feature_same_file": str(feature["neighbours"]["same_file_nearest"]),
            "control_same_file": str(control["neighbours"]["same_file_nearest"]),
            "shuffled_same_file": str(null["neighbours"]["same_file_nearest"]),
            "same_file_chance": q(feature["neighbours"]["same_file_chance"]),
            "feature_linked": str(feature["neighbours"]["linked_nearest"]),
            "linked_chance": q(feature["neighbours"]["linked_chance"]),
            "feature_beats_control":
                str(sep["verdict"]["feature_beats_hash_control"]),
            "hash_is_chance_like": str(sep["verdict"]["hash_is_chance_like"]),
        }

        return Solution(
            query=query, kind="report",
            answer=f"report lean: {corpus['declarations']} declarations of "
                   f"the Lean development carry a deterministic Leech "
                   f"address, read back exactly "
                   f"{trip['exact']}/{trip['checked']} times with "
                   f"{trip['coordinate_errors']} coordinate errors; "
                   f"{inj['distinct_addresses']} addresses are distinct and "
                   f"the quantiser adds no conflation of its own; the "
                   f"nearest declaration by address shares a file "
                   f"{feature['neighbours']['same_file_nearest']} times "
                   f"against {control['neighbours']['same_file_nearest']} "
                   f"for a SHA-256 control and a chance rate of "
                   f"{q(feature['neighbours']['same_file_chance'])}",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_lean", "args": {}},
            payload={"cache": dict(cache)})

    def _report_directives(self, query: Query) -> Solution:
        """Wires drc.directives_report -- the standing rules and their instruments.

        ``PROJECT_DIRECTIVES.md`` states how work on this repository is done.
        A rule nobody can check is a wish, so every directive names an
        instrument, and this subject reports whether each instrument is
        actually present.
        """
        report = drc.directives_report()
        rows = report["rows"]
        steps = [
            Step("the rules, as the document states them",
                 f"Parsed out of {report['document']} rather than "
                 f"paraphrased: the summary table gives the one-line rule and "
                 f"the instrument, the long-form section gives the reason.",
                 "; ".join(f"{r['key']} {r['rule'][:48]}" for r in rows)),
            Step("every rule names something that could fail",
                 f"An instrument is a module, a report subject, a test file "
                 f"or a document.  Each is resolved against the tree, so a "
                 f"directive whose instrument was removed is reported as a "
                 f"defect instead of standing as prose.",
                 f"{report['instrumented']}/{report['count']} fully "
                 f"instrumented, defects {len(report['defects'])}"),
        ]
        for row in rows:
            steps.append(Step(
                f"{row['key']} -- {row['heading'] or row['rule'][:40]}",
                row["rule"],
                f"instrument {row['instrument']}; resolved "
                f"{row['state']['resolved']}/{row['state']['named']}; "
                f"{row['body_words']} words of reasoning"))

        expected = {
            "count": str(report["count"]),
            "instrumented": str(report["instrumented"]),
            "defects": str(len(report["defects"])),
            "sound": str(report["sound"]),
            "words": str(report["words"]),
            "keys": ",".join(r["key"] for r in rows),
        }
        return Solution(
            query=query, kind="report",
            answer=f"report directives: {report['count']} standing rules, "
                   f"{report['instrumented']} of them with every named "
                   f"instrument present in the tree, "
                   f"{len(report['defects'])} defects",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_directives", "args": {}},
            payload={"defects": list(report["defects"])})

    def _report_pipeline(self, query: Query) -> Solution:
        """Wires ppl.pipeline_report -- study to test to implemented.

        The six stages of directive D5, computed from the tree for every
        study: the document, the modules, the report subject, the tests that
        import it, the Lean counterpart, and the column-3 template.
        """
        report = ppl.pipeline_report()
        rows = report["rows"]
        steps = [
            Step("the six stages, and why they are computed",
                 f"A study that stops at 'written' states things nothing "
                 f"checks; a module that stops at 'implemented' is code "
                 f"nothing can reach.  Only the association between a "
                 f"document, its modules and its Lean files is declared -- "
                 f"every stage is read off the tree at call time, so a row "
                 f"cannot claim a stage it has not reached.",
                 " -> ".join(report["stages"])),
            Step("the board",
                 f"Each row's first missing stage is the next thing to do.",
                 "; ".join(
                     f"{r['key']} {r['stages_reached']}/6"
                     + (f" (next {r['first_missing']})" if r["first_missing"]
                        else "")
                     for r in rows)),
            Step("where the work is blocked",
                 f"Grouped by stage, so a systematic gap shows up as a "
                 f"column rather than as a scatter of rows.",
                 "; ".join(f"{stage}: {', '.join(keys)}"
                           for stage, keys in report["blocked_at"].items())
                 or "nothing blocked"),
            Step("how deep the testing goes",
                 f"Test methods are counted from the sources of the files "
                 f"that import each row's modules -- counted, not run, so "
                 f"the board is cheap enough to consult every time.",
                 f"{report['total_tests']} test methods across the rows"),
        ]
        expected = {
            "rows": str(report["count"]),
            "complete": str(report["complete"]),
            "incomplete": ",".join(report["incomplete"]) or "none",
            "total_tests": str(report["total_tests"]),
            "stages": ",".join(report["stages"]),
        }
        for row in rows:
            expected[f"stage_{row['key']}"] = str(row["stages_reached"])
        return Solution(
            query=query, kind="report",
            answer=f"report pipeline: {report['complete']} of "
                   f"{report['count']} rows have passed all six stages"
                   + (f"; incomplete: {', '.join(report['incomplete'])}"
                      if report["incomplete"] else ""),
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_pipeline", "args": {}},
            payload={"blocked_at": {k: list(v) for k, v
                                    in report["blocked_at"].items()}})
