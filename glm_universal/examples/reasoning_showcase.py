#!/usr/bin/env python3
"""Can the GLM reason?  A runnable, self-verifying answer.

This script asks the live :class:`~glm_universal.runtime.session.GeometricSession`
a fixed list of questions and prints, for each one:

* the question exactly as typed,
* the kind the parser assigned it,
* the answer,
* the reasoning chain, twice over -- column 1 (language) and column 2
  (exact mathematics),
* the falsifiable claims the answer commits to, and
* the verdict of column 3: a script generated from the solution, run in a
  **fresh interpreter**, whose output is compared claim by claim against
  column 2.

Nothing here is narrated by hand.  Everything printed is read off the
solution objects, so the transcript cannot drift from what the system
actually does.  The final section is deliberately made of questions the
system *cannot* answer, printed with the same machinery, so that the
capability claim is bounded from both sides.

Run::

    PYTHONPATH=. python3 glm_universal/examples/reasoning_showcase.py

Options::

    --no-verify     skip column 3 (much faster; no subprocesses)
    --markdown      emit GitHub-flavoured Markdown instead of plain text
    --only SECTION  run one section only (substring match, case-insensitive)
    --timeout N     per-script wall-clock ceiling in seconds (default 180)
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from glm_universal.runtime import tct_engine as TE
from glm_universal.runtime.session import GeometricSession, Solution

RULE = "=" * 78
THIN = "-" * 78


# ===========================================================================
# 1.  THE PROBES
# ===========================================================================

@dataclass(frozen=True)
class Probe:
    """One question, with the reason it is worth asking."""

    query: str
    why: str
    #: ``True`` when the probe is expected to be refused rather than answered.
    expect_unsolved: bool = False


@dataclass(frozen=True)
class Section:
    title: str
    blurb: str
    probes: Tuple[Probe, ...]


SECTIONS: Tuple[Section, ...] = (
    Section(
        "1. Dimensional reasoning over SI7 / EXT10",
        "The register holds 726 named quantities as exact exponent vectors. "
        "A relation is checked by adding exponents, so a true law and a "
        "false one are separated by arithmetic, not by lookup.",
        (
            Probe("verify energy = mass * speed_of_light^2",
                  "the canonical mass-energy relation, now that the register "
                  "carries the speed of light"),
            Probe("verify energy = mass * speed_of_light",
                  "the same relation with the square dropped: must be "
                  "rejected, not repaired"),
            Probe("verify energy = mass * speed of light^2",
                  "the same question typed with spaces instead of "
                  "underscores"),
            Probe("verify pressure = force / area",
                  "division as well as multiplication"),
            Probe("check tensor force = mass * acceleration",
                  "the stricter semantics: tensor rank and parity must agree "
                  "too, not only the dimension"),
            Probe("verify impedance_of_free_space = resistance",
                  "a constant identified with the quantity it is a value of"),
            Probe("verify energy = entropy * temperature",
                  "a thermodynamic relation reached through a different "
                  "domain of the register"),
            Probe("verify energy = entropy * force",
                  "the same shape, falsified"),
        ),
    ),
    Section(
        "2. Constants and the TAX / NRCI coherence law",
        "Every carrier has a topological-plus-geometric cost TAX and a "
        "coherence NRCI = B / (B + TAX) with B = 10.  Both are exact "
        "rationals over the read quantum Y.",
        (
            Probe("what is speed of light",
                  "a constant looked up by its ordinary English name"),
            Probe("describe fine_structure_constant",
                  "a dimensionless constant: every exponent zero, so the "
                  "dimension facet of its carrier is empty"),
            Probe("coherence of planck_constant",
                  "the NRCI of a constant's carrier, with its regime band"),
            Probe("coherence of electron",
                  "the same law applied to a chemical element, i.e. across "
                  "registers"),
            Probe("angle energy torque",
                  "the exact squared cosine between two carriers that share "
                  "an SI7 dimension"),
        ),
    ),
    Section(
        "3. Retrieval, analogy and grouping",
        "Nearest-neighbour and analogy work on the carriers, so they answer "
        "with a ranked list and say when the answer is not unique.",
        (
            Probe("nearest 5 to planck_constant",
                  "ranked retrieval in the physics register"),
            Probe("force : energy :: pressure : ?",
                  "a four-term analogy solved by carrier arithmetic"),
            Probe("cluster energy, torque, pressure, power into 2",
                  "unsupervised grouping by exact distance"),
            Probe("mog grid of carbon",
                  "the substrate view: where a concept sits in the Miracle "
                  "Octad Generator, and how far it is from the Golay code"),
        ),
    ),
    Section(
        "4. Layered reasoning: where a truth stops holding",
        "The escalation walk is the information-loss study made "
        "operational.  Two concepts are compared at each layer of the "
        "dimension projection; the walk reports the first layer that tells "
        "them apart.",
        (
            Probe("project energy torque",
                  "two quantities that SI7 cannot separate: the walk has to "
                  "climb"),
            Probe("project energy speed_of_light",
                  "two quantities separated immediately"),
            Probe("task physics",
                  "the worked end-to-end task: the same pair, adjudicated "
                  "and attributed to facets"),
        ),
    ),
    Section(
        "5. Reasoning over the migrated state",
        "The concept store built by the literal data migration is queried "
        "the same way as the built-in registers, and its answers are "
        "cross-checked against the dimensional register.",
        (
            Probe("report state migration",
                  "what the migration actually produced, recomputed on "
                  "demand rather than quoted"),
            Probe("report concept store",
                  "the shape of the migrated relational graph"),
            Probe("task concepts",
                  "retrieval from the migrated graph, adjudicated by the "
                  "dimensional register: one claim upheld, one rejected"),
        ),
    ),
    Section(
        "6. Puzzle solving",
        "A task that is not about physics at all: infer a transformation "
        "rule from worked pairs and apply it.",
        (
            Probe("task grid",
                  "rule induction on ARC-style grids"),
            Probe("sakuma product",
                  "an exact computation in the Griess algebra"),
        ),
    ),
    Section(
        "7. The limits, stated as refusals",
        "These are the questions the system declines.  A refusal names the "
        "missing capability instead of guessing, and no refusal is silently "
        "converted into an answer.",
        (
            Probe("verify energy = mass * zzzz_nope",
                  "an unknown concept: refused, with spelling suggestions",
                  expect_unsolved=True),
            Probe("verify energy = 3 * mass * speed_of_light^2",
                  "a numeric factor that is not a power of ten: the register "
                  "tracks decimal scale exactly and refuses to absorb it",
                  expect_unsolved=True),
            Probe("how many joules is one electronvolt",
                  "numeric evaluation and unit conversion: not implemented, "
                  "and not faked",
                  expect_unsolved=True),
            Probe("why is the sky blue",
                  "open-ended natural language: outside every supported "
                  "query kind",
                  expect_unsolved=True),
        ),
    ),
)


# ===========================================================================
# 2.  RENDERING
# ===========================================================================

class Writer:
    """Plain-text or Markdown output, chosen once."""

    def __init__(self, markdown: bool, stream=sys.stdout) -> None:
        self.md = markdown
        self.out = stream

    def line(self, text: str = "") -> None:
        print(text, file=self.out)

    def title(self, text: str) -> None:
        if self.md:
            self.line(f"# {text}\n")
        else:
            self.line(RULE)
            self.line(text)
            self.line(RULE)

    def section(self, text: str, blurb: str) -> None:
        if self.md:
            self.line(f"\n## {text}\n")
            self.line(blurb + "\n")
        else:
            self.line("")
            self.line(RULE)
            self.line(text)
            self.line(RULE)
            self.line(blurb)

    def probe(self, probe: Probe) -> None:
        if self.md:
            self.line(f"\n### `{probe.query}`\n")
            self.line(f"*Why:* {probe.why}\n")
        else:
            self.line("")
            self.line(THIN)
            self.line(f"ASK  {probe.query}")
            self.line(f"WHY  {probe.why}")
            self.line(THIN)

    def block(self, heading: str, rows: Sequence[str]) -> None:
        if not rows:
            return
        if self.md:
            self.line(f"**{heading}**\n")
            self.line("```")
            for row in rows:
                self.line(row)
            self.line("```")
        else:
            self.line(f"  {heading}")
            for row in rows:
                self.line(f"    {row}")


def render(writer: Writer, probe: Probe, solution: Solution,
           verify: bool, timeout: int) -> bool:
    """Print one probe's full transcript.  Returns whether it behaved."""
    writer.probe(probe)
    writer.block("kind", [f"{solution.kind}  (solved={solution.ok})"])

    if not solution.ok:
        writer.block("refusal", [solution.answer])
        behaved = probe.expect_unsolved
        writer.block("expected to be refused",
                     ["yes" if probe.expect_unsolved else
                      "NO -- this is a regression"])
        return behaved

    writer.block("answer", [solution.answer])

    writer.block("column 1 -- language",
                 [f"{i + 1}. [{s.label}] {s.language}"
                  for i, s in enumerate(solution.steps)])
    writer.block("column 2 -- mathematics",
                 [f"{i + 1}. [{s.label}] {s.mathematics}"
                  for i, s in enumerate(solution.steps)])
    writer.block("falsifiable claims",
                 [f"{k} = {v}" for k, v in sorted(solution.expected.items())])

    if not verify:
        writer.block("column 3 -- script", ["(skipped: --no-verify)"])
        return not probe.expect_unsolved

    trace = TE.verify_trace(TE.build_trace(solution), timeout=timeout)
    verdict = trace.verdict
    exact, offenders = TE.script_is_exact(trace.script)
    rows = [
        f"executed        : {verdict.executed} (returncode "
        f"{verdict.returncode})",
        f"claims checked  : {len(verdict.observed)}",
        f"mismatches      : {len(verdict.mismatches)}",
        f"missing         : {len(verdict.missing_keys)}",
        f"float-free      : {exact}"
        + ("" if exact else f"  {offenders}"),
        f"VERIFIED        : {trace.verified}",
    ]
    if verdict.mismatches:
        rows.extend(f"  mismatch {k}: column 2 said {want}, "
                    f"the script said {got}"
                    for k, want, got in verdict.mismatches)
    if not verdict.executed and verdict.stderr_tail:
        rows.append(f"  stderr: {verdict.stderr_tail[-300:]}")
    writer.block("column 3 -- independent script", rows)
    return trace.verified and not probe.expect_unsolved


# ===========================================================================
# 3.  DRIVER
# ===========================================================================

def run(markdown: bool = False, verify: bool = True, only: Optional[str] = None,
        timeout: int = 180, stream=sys.stdout) -> int:
    """Run the showcase.  Returns the number of probes that misbehaved."""
    writer = Writer(markdown, stream)
    writer.title("GLM reasoning showcase")
    writer.line("")
    writer.line("Every line below is read off a live session; none of it is "
                "written by hand.")

    session = GeometricSession()
    failures: List[str] = []
    total = 0

    for section in SECTIONS:
        if only and only.lower() not in section.title.lower():
            continue
        writer.section(section.title, section.blurb)
        for probe in section.probes:
            total += 1
            solution = session.ask(probe.query)
            if not render(writer, probe, solution, verify, timeout):
                failures.append(probe.query)

    writer.section("Summary", "")
    writer.block("counts", [
        f"probes run     : {total}",
        f"as expected    : {total - len(failures)}",
        f"unexpected     : {len(failures)}",
    ])
    if failures:
        writer.block("unexpected", failures)
    return len(failures)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-verify", action="store_true",
                        help="skip column 3")
    parser.add_argument("--markdown", action="store_true",
                        help="emit Markdown")
    parser.add_argument("--only", default=None,
                        help="run only sections whose title contains this")
    parser.add_argument("--timeout", type=int, default=180,
                        help="per-script wall-clock ceiling in seconds")
    args = parser.parse_args(argv)
    return run(markdown=args.markdown, verify=not args.no_verify,
               only=args.only, timeout=args.timeout)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
