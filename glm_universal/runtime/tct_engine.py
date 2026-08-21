"""``glm_universal.runtime.tct_engine`` -- Three Column Thinking.

A Three Column Thinking (TCT) trace states one solved query three times over:

**Column 1 -- Language.**
    The deterministic reasoning chain in plain English, one sentence per step.

**Column 2 -- Exact mathematics.**
    The same chain as exact statements over ``Q``, ``Z`` and ``F_2``: rational
    equations, 2-adic digit-stack parameters, Griess forms, Norton-Sakuma
    products.  Every rational appears as a canonical ``"n/d"`` string.

**Column 3 -- Executable script.**
    A self-contained Python script that recomputes the answer from the public
    :mod:`glm_universal` API and *asserts* it against the values column 2
    claims.  It is run in a fresh interpreter by :func:`verify_trace`.

Why the third column is more than a printout
--------------------------------------------
The three columns are generated from one :class:`~glm_universal.runtime.
session.Solution`, so they cannot drift apart by construction.  What they
*could* still share is a bug in the solver.  Column 3 does not repeat the
solver's steps: it re-enters the package at its public API, in a separate
process, with the claimed values embedded as literals, and fails with a
non-zero exit code if anything differs.  Verification is therefore two
independent comparisons of the same claim:

1. the script's own ``assert`` against its embedded copy of the claim, whose
   outcome is the process exit code; and
2. :func:`verify_trace` re-reading the JSON the script emits and comparing it,
   key by key, to :attr:`~glm_universal.runtime.session.Solution.expected` in
   the parent process.

A trace is reported as verified only when both agree.  This is a same-session
cross-check between two code paths -- it is not a claim that the underlying
mathematics has been independently reproduced from a second implementation.

Invariants
----------
Generated scripts are held to the same standard as the package: no ``float``
literal, no ``float()`` call, no ``import random``, standard library plus
``glm_universal`` only.  :func:`script_is_exact` checks this by AST, and the
test suite applies it to the script of every trace it builds.
"""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from .session import Solution, Step

__all__ = [
    "TCTError", "BEGIN_MARKER", "END_MARKER", "DEFAULT_TIMEOUT_SECONDS",
    "ScriptVerdict", "ThreeColumnTrace", "package_root", "render_script",
    "script_is_exact", "build_trace", "verify_trace", "trace_to_markdown",
]


class TCTError(ValueError):
    """Raised when a trace cannot be built or its script cannot be rendered."""


#: The script brackets its JSON payload with these so that anything else it
#: prints -- a warning, a progress line -- cannot be mistaken for the payload.
BEGIN_MARKER = "GLM_TCT_JSON_BEGIN"
END_MARKER = "GLM_TCT_JSON_END"

#: Subprocess wall-clock ceiling.  Generous, because a ``product`` script
#: builds the exhaustive 98,280-class type-2 table before it can multiply.
DEFAULT_TIMEOUT_SECONDS = 900


def package_root() -> Path:
    """The directory that must be on ``sys.path`` to import ``glm_universal``."""
    return Path(__file__).resolve().parent.parent.parent


# ===========================================================================
# 1.  SCRIPT TEMPLATES
# ===========================================================================

_HEADER = '''"""Column 3 of a Three Column Thinking trace -- generated, self-contained.

Query : {query!r}
Kind  : {kind}

Recomputes the answer from the public glm_universal API in a fresh
interpreter and asserts it against the exact values column 2 claims.  Exits 0
only if every claim matches; exits 1 with a diff otherwise.
"""

import json
import sys
from fractions import Fraction

sys.path.insert(0, {root!r})

from glm_universal import data_objects as do
from glm_universal.reasoning import analogy as an
from glm_universal.reasoning import metric as me
from glm_universal.reasoning import product as pr
from glm_universal.reasoning import verifier as ve
from glm_universal.substrate import leech2, mog
from glm_universal.runtime.session import spatial_objects


def q(x):
    """Canonical "n/d" rendering of an exact scalar -- no float is ever made."""
    f = Fraction(x)
    return "%d/%d" % (f.numerator, f.denominator)


EXPECTED = {expected}

'''

_FOOTER = '''

# -- compare, report, and set the exit code ---------------------------------

mismatches = []
for key in sorted(EXPECTED):
    if key not in observed:
        mismatches.append((key, EXPECTED[key], "<missing>"))
    elif observed[key] != EXPECTED[key]:
        mismatches.append((key, EXPECTED[key], observed[key]))
extra = sorted(set(observed) - set(EXPECTED))

print({begin!r})
print(json.dumps({{"observed": observed,
                  "mismatches": [list(m) for m in mismatches],
                  "extra_keys": extra}},
                 sort_keys=True, indent=2))
print({end!r})

if mismatches:
    for key, want, got in mismatches:
        sys.stderr.write("MISMATCH %s: column 2 says %s, recomputation says "
                         "%s\\n" % (key, want, got))
    sys.exit(1)
sys.exit(0)
'''


def _pool_snippet(domain: str) -> str:
    """Source that binds ``pool`` to a domain's carriers and ``by_name``."""
    loaders = {
        "physics": "do.physics_objects()",
        "chemistry": "do.element_objects()",
        "mathematics": "do.mathematics_objects()",
        "lexicon": "do.lexicon_objects()[0]",
        "spatial": "spatial_objects()",
    }
    if domain not in loaders:
        raise TCTError(f"render_script: no pool loader for domain {domain!r}")
    return (f"pool = {loaders[domain]}\n"
            f"by_name = {{o.name: o for o in pool}}\n")


def _body_verify(args: Mapping[str, object]) -> str:
    return f'''# -- recompute -------------------------------------------------------------

verdict = ve.verify_expression_pair({args["lhs"]!r}, {args["rhs"]!r},
                                    {args["semantics"]!r})

observed = {{
    "holds": str(verdict.holds),
    "lhs_dimension": str(verdict.lhs_dimension),
    "rhs_dimension": str(verdict.rhs_dimension),
    "lhs_rank": str(verdict.lhs_rank),
    "rhs_rank": str(verdict.rhs_rank),
    "failing_planes": str(list(verdict.failing_planes)),
    "blamed_facets": str(list(verdict.blamed_facets)),
}}
'''


def _body_analogy(args: Mapping[str, object]) -> str:
    return f'''# -- recompute -------------------------------------------------------------

{_pool_snippet(str(args["domain"]))}
result = an.solve_analogy_objects(by_name[{args["a"]!r}],
                                  by_name[{args["b"]!r}],
                                  by_name[{args["c"]!r}],
                                  pool, subspace={args["subspace"]!r})

observed = {{
    "answer": result.answer,
    "distance2": q(result.distance2),
    "exact_hit": str(result.exact_hit),
    "unique": str(result.unique),
    "tied": str(list(result.tied)),
}}
'''


def _body_describe(args: Mapping[str, object]) -> str:
    return f'''# -- recompute -------------------------------------------------------------

{_pool_snippet(str(args["domain"]))}
obj = by_name[{args["name"]!r}]
params = obj.parameters()
address = obj.monster_address()

observed = {{
    "name": obj.name,
    "domain": obj.domain,
    "depth": str(params.depth),
    "offset": str(params.offset),
    "plane0_mask": str(address["plane0_mask"]),
    "plane0_weight": str(address["plane0_weight"]),
    "is_golay_codeword": str(address["is_golay_codeword"]),
    "round_trip_ok": str(obj.round_trip_ok()),
    "griess_norm2": q(me.griess_norm2(obj.carrier)),
}}
'''


def _body_nearest(args: Mapping[str, object]) -> str:
    return f'''# -- recompute -------------------------------------------------------------

{_pool_snippet(str(args["domain"]))}
obj = by_name[{args["name"]!r}]
subspace = {args["subspace"]!r}
indices = None
if subspace is not None:
    indices = an.subspace_indices(obj.layout, an.SUBSPACES[subspace])

target = an.project_subspace(obj.carrier, indices)
candidates = [(o.name, an.project_subspace(o.carrier, indices)) for o in pool]
ranked = me.rank_by_distance(target, candidates, exclude=(obj.name,))
top = ranked[:{int(args["limit"])}]

observed = {{
    "reference": obj.name,
    "nearest": top[0][0],
    "nearest_distance2": q(top[0][1]),
    "top_names": str([n for n, _ in top]),
    "top_distances2": str([q(d) for _, d in top]),
}}
'''


def _body_product(args: Mapping[str, object]) -> str:
    return f'''# -- recompute -------------------------------------------------------------
#
# Note on the F_2 step: the third axis is the sum of the two classes in the
# module Lambda / 2 Lambda.  That module's addition IS the bitwise XOR of the
# coordinate vectors, so sakuma_third_axis is a linear map over F_2, not an
# opportunistic bit trick standing in for arithmetic.  Every rational below is
# a Fraction.

u = {int(args["u"])}
v = {int(args["v"])}
assert leech2.is_type2_class(u), "u is not a type-2 class"
assert leech2.is_type2_class(v), "v is not a type-2 class"
assert pr.is_two_a_pair(u, v), "u and v are not in the 2A position"

third = pr.sakuma_third_axis(u, v)
prod = pr.axis_product(u, v)
sub = pr.two_a_subalgebra(u, v)
coeffs = {{str(label): q(prod.coefficient(label)) for label in sorted(sub.labels)}}

observed = {{
    "u": str(u),
    "v": str(v),
    "third_axis": str(third),
    "position": pr.position_name(u, v),
    "coefficients": str(sorted(coeffs.items())),
    "griess_self": q(pr.griess_form(pr.axis(u), pr.axis(u))),
    "griess_pair": q(pr.griess_form(pr.axis(u), pr.axis(v))),
    "subalgebra_labels": str(sorted(sub.labels)),
}}
'''


def _body_cluster(args: Mapping[str, object]) -> str:
    names = list(args["names"])  # type: ignore[arg-type]
    return f'''# -- recompute -------------------------------------------------------------

{_pool_snippet(str(args["domain"]))}
names = {names!r}
objs = [by_name[n] for n in names]
tree = me.single_linkage([o.carrier for o in objs], [o.name for o in objs])
groups = me.cut_tree(tree, {int(args["k"])})

observed = {{
    "labels": str([o.name for o in objs]),
    "k": str({int(args["k"])}),
    "groups": str(groups),
    "merge_heights": str([q(m.height) for m in tree.merges]),
}}
'''


def _body_spatial(args: Mapping[str, object]) -> str:
    return f'''# -- recompute -------------------------------------------------------------

{_pool_snippet(str(args["domain"]))}
obj = by_name[{args["name"]!r}]
plane0 = obj.stack().planes[0]
grid = mog.frame(plane0)
cube = mog.cube_profile(plane0)
codeword, distance, count = an.nearest_golay_codeword(plane0)

observed = {{
    "name": obj.name,
    "plane0_mask": "0x%06x" % plane0,
    "plane0_weight": str(bin(plane0).count("1")),
    "frame_rows": str([[int(b) for b in row] for row in grid]),
    "brick_weights": str([c["weight"] for c in cube]),
    "nearest_codeword": "0x%06x" % codeword,
    "golay_distance": str(distance),
    "golay_multiplicity": str(count),
}}
'''


#: Template name -> body renderer.  A solver names its template in
#: ``Solution.script_spec["template"]``; there is no fallback, because a
#: silently generic script would verify nothing in particular.
TEMPLATES = {
    "verify": _body_verify,
    "analogy": _body_analogy,
    "describe": _body_describe,
    "nearest": _body_nearest,
    "product": _body_product,
    "cluster": _body_cluster,
    "spatial": _body_spatial,
}


def render_script(solution: Solution, root: Optional[str] = None) -> str:
    """Render column 3 for a solution.

    Parameters
    ----------
    solution
        A solved query.  Its ``script_spec`` names the template and supplies
        the arguments; its ``expected`` mapping is embedded as the assertion
        target.
    root
        Directory to prepend to ``sys.path`` inside the script.  Defaults to
        :func:`package_root`, which is what makes the script runnable from any
        working directory.

    Raises
    ------
    TCTError
        If the solution is unsolved, names no template, or names one that does
        not exist.
    """
    if not solution.ok:
        raise TCTError(
            f"render_script: refusing to render a script for an unsolved "
            f"query ({solution.error})")
    spec = dict(solution.script_spec)
    template = spec.get("template")
    if template is None:
        raise TCTError("render_script: solution names no script template")
    if template not in TEMPLATES:
        raise TCTError(f"render_script: unknown template {template!r}; known "
                       f"templates are {sorted(TEMPLATES)}")
    args = dict(spec.get("args", {}))  # type: ignore[arg-type]

    header = _HEADER.format(
        query=solution.query.raw, kind=solution.kind,
        root=str(root or package_root()),
        expected=json.dumps(dict(solution.expected), indent=4,
                            sort_keys=True))
    body = TEMPLATES[template](args)
    footer = _FOOTER.format(begin=BEGIN_MARKER, end=END_MARKER)
    return header + body + footer


def script_is_exact(source: str) -> Tuple[bool, Tuple[str, ...]]:
    """Whether a generated script obeys the package's exactness rules.

    Checks by AST, not by text search, so a ``float`` inside a string literal
    or a comment is correctly ignored while a real one is caught.

    Returns
    -------
    (ok, offenders)
        ``offenders`` names each violation as ``"line N: what"``.
    """
    offenders: List[str] = []
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return False, (f"line {exc.lineno}: syntax error: {exc.msg}",)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            offenders.append(f"line {node.lineno}: float literal")
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "float"):
            offenders.append(f"line {node.lineno}: float() call")
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] == "random":
                    offenders.append(f"line {node.lineno}: imports random")
        if isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] == "random":
                offenders.append(f"line {node.lineno}: imports random")
    return not offenders, tuple(offenders)


# ===========================================================================
# 2.  THE TRACE
# ===========================================================================

@dataclass(frozen=True)
class ScriptVerdict:
    """The outcome of running column 3 in a fresh interpreter.

    Attributes
    ----------
    executed
        Whether the subprocess ran at all.  ``False`` means it timed out or
        the interpreter could not be started -- distinct from running and
        failing.
    returncode
        The process exit code.  ``0`` means the script's own assertions
        passed.
    observed
        The JSON payload the script emitted, key by key.  Empty if the script
        died before printing it.
    matches_column2
        Whether the parent process's own comparison of ``observed`` against
        the solution's ``expected`` found no difference.  This is computed
        here, independently of the script's exit code.
    mismatches
        ``(key, expected, observed)`` for each disagreement.
    missing_keys
        Claims in column 2 that the script did not report at all.
    stderr_tail
        The last part of standard error, for diagnosis.
    duration_note
        How the run was bounded, recorded rather than timed, so that a trace
        is byte-identical between runs.
    """

    executed: bool
    returncode: Optional[int]
    observed: Mapping[str, str] = field(default_factory=dict)
    matches_column2: bool = False
    mismatches: Tuple[Tuple[str, str, str], ...] = ()
    missing_keys: Tuple[str, ...] = ()
    stderr_tail: str = ""
    duration_note: str = ""

    @property
    def verified(self) -> bool:
        """Both checks agree: exit code 0 *and* a key-by-key match.

        Either alone is insufficient.  A zero exit with no payload would mean
        the script never got to its assertions; a payload match with a
        non-zero exit would mean the script found something the parent's
        comparison does not model.
        """
        return (self.executed and self.returncode == 0
                and self.matches_column2 and bool(self.observed))

    def as_dict(self) -> Dict[str, object]:
        """A JSON-serialisable view."""
        return {
            "executed": self.executed,
            "returncode": self.returncode,
            "verified": self.verified,
            "matches_column2": self.matches_column2,
            "observed": dict(self.observed),
            "mismatches": [list(m) for m in self.mismatches],
            "missing_keys": list(self.missing_keys),
            "stderr_tail": self.stderr_tail,
            "duration_note": self.duration_note,
        }


@dataclass(frozen=True)
class ThreeColumnTrace:
    """One query, stated three times over, plus the verification verdict."""

    query: str
    kind: str
    answer: str
    language: Tuple[str, ...]
    mathematics: Tuple[str, ...]
    script: str
    expected: Mapping[str, str] = field(default_factory=dict)
    labels: Tuple[str, ...] = ()
    verdict: Optional[ScriptVerdict] = None

    @property
    def synchronized(self) -> bool:
        """Whether the three columns describe the same number of steps.

        Columns 1 and 2 are emitted from the same
        :class:`~glm_universal.runtime.session.Step` objects, so this is a
        structural invariant rather than a discovery -- it is asserted here so
        that a future refactor that breaks the pairing fails loudly.
        """
        return (len(self.language) == len(self.mathematics) == len(self.labels)
                and len(self.language) > 0 and bool(self.script))

    @property
    def verified(self) -> bool:
        """Whether column 3 ran and agreed with column 2."""
        return self.verdict is not None and self.verdict.verified

    def with_verdict(self, verdict: ScriptVerdict) -> "ThreeColumnTrace":
        """A copy carrying ``verdict``; the trace itself stays immutable."""
        return ThreeColumnTrace(
            query=self.query, kind=self.kind, answer=self.answer,
            language=self.language, mathematics=self.mathematics,
            script=self.script, expected=self.expected, labels=self.labels,
            verdict=verdict)

    def as_dict(self, include_script: bool = True) -> Dict[str, object]:
        """A JSON-serialisable view."""
        out: Dict[str, object] = {
            "query": self.query,
            "kind": self.kind,
            "answer": self.answer,
            "labels": list(self.labels),
            "column1_language": list(self.language),
            "column2_mathematics": list(self.mathematics),
            "expected": dict(self.expected),
            "synchronized": self.synchronized,
            "verified": self.verified,
            "verdict": self.verdict.as_dict() if self.verdict else None,
        }
        if include_script:
            out["column3_script"] = self.script
        return out


def build_trace(solution: Solution,
                root: Optional[str] = None) -> ThreeColumnTrace:
    """Assemble the three columns from one solution.

    Columns 1 and 2 are read off the solution's steps in order, so they are
    aligned by construction: entry *i* of each column is the same
    :class:`~glm_universal.runtime.session.Step`.
    """
    steps: Sequence[Step] = solution.steps
    if not steps:
        raise TCTError("build_trace: the solution carries no steps")
    return ThreeColumnTrace(
        query=solution.query.raw,
        kind=solution.kind,
        answer=solution.answer,
        language=tuple(s.language for s in steps),
        mathematics=tuple(s.mathematics for s in steps),
        script=render_script(solution, root=root),
        expected=dict(solution.expected),
        labels=tuple(s.label for s in steps),
    )


def _extract_payload(stdout: str) -> Optional[Dict[str, object]]:
    """Pull the JSON payload from between the markers, or ``None``."""
    start = stdout.find(BEGIN_MARKER)
    end = stdout.find(END_MARKER)
    if start < 0 or end < 0 or end < start:
        return None
    blob = stdout[start + len(BEGIN_MARKER):end].strip()
    try:
        parsed = json.loads(blob)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def verify_trace(trace: ThreeColumnTrace, workdir: Optional[Path] = None,
                 timeout: int = DEFAULT_TIMEOUT_SECONDS) -> ThreeColumnTrace:
    """Run column 3 in a fresh interpreter and cross-check its output.

    The script is written into ``workdir`` (a temporary directory if none is
    given) and run with :data:`sys.executable`, so it uses the same
    interpreter and the same installed package as the caller but shares no
    interpreter state with it -- no cached register, no imported module, no
    already-computed table.

    Parameters
    ----------
    trace
        The trace whose script to run.
    workdir
        Where to write the script.  Supplying one keeps the script on disk for
        inspection after the run.
    timeout
        Wall-clock ceiling in seconds.

    Returns
    -------
    ThreeColumnTrace
        A copy of ``trace`` carrying a :class:`ScriptVerdict`.  A failed run
        is reported, never raised: a script that disagrees with column 2 is a
        result about the trace, not an error in the harness.
    """
    import tempfile

    temp: Optional[tempfile.TemporaryDirectory] = None
    if workdir is None:
        temp = tempfile.TemporaryDirectory(prefix="glm_tct_")
        target = Path(temp.name)
    else:
        target = Path(workdir)
        target.mkdir(parents=True, exist_ok=True)

    try:
        path = target / "tct_column3.py"
        path.write_text(trace.script, encoding="utf-8")

        env = dict(os.environ)
        env["PYTHONPATH"] = str(package_root()) + os.pathsep + env.get(
            "PYTHONPATH", "")
        env["PYTHONHASHSEED"] = "0"
        try:
            proc = subprocess.run(
                [sys.executable, str(path)], capture_output=True, text=True,
                timeout=timeout, env=env, cwd=str(package_root()), check=False)
        except subprocess.TimeoutExpired:
            return trace.with_verdict(ScriptVerdict(
                executed=False, returncode=None,
                stderr_tail=f"timed out after {timeout} s",
                duration_note=f"bounded at {timeout} s"))
        except OSError as exc:
            return trace.with_verdict(ScriptVerdict(
                executed=False, returncode=None,
                stderr_tail=f"could not start interpreter: {exc}",
                duration_note=f"bounded at {timeout} s"))

        payload = _extract_payload(proc.stdout)
        observed: Dict[str, str] = {}
        if payload is not None and isinstance(payload.get("observed"), dict):
            observed = {str(k): str(v)
                        for k, v in payload["observed"].items()}

        mismatches: List[Tuple[str, str, str]] = []
        missing: List[str] = []
        for key in sorted(trace.expected):
            if key not in observed:
                missing.append(key)
            elif observed[key] != trace.expected[key]:
                mismatches.append((key, trace.expected[key], observed[key]))

        return trace.with_verdict(ScriptVerdict(
            executed=True,
            returncode=proc.returncode,
            observed=observed,
            matches_column2=not mismatches and not missing and bool(observed),
            mismatches=tuple(mismatches),
            missing_keys=tuple(missing),
            stderr_tail=proc.stderr[-2000:],
            duration_note=f"bounded at {timeout} s"))
    finally:
        if temp is not None:
            temp.cleanup()


# ===========================================================================
# 3.  PRESENTATION
# ===========================================================================

def trace_to_markdown(trace: ThreeColumnTrace,
                      include_script: bool = True) -> str:
    """Render a trace as Markdown: the three columns, then the verdict."""
    lines: List[str] = [
        f"# Three Column Thinking -- {trace.kind}",
        "",
        f"**Query.** `{trace.query}`",
        "",
        f"**Answer.** {trace.answer}",
        "",
        "| # | Step | Column 1 -- Language | Column 2 -- Exact mathematics |",
        "|---|------|----------------------|-------------------------------|",
    ]
    for i, (label, lang, math) in enumerate(
            zip(trace.labels, trace.language, trace.mathematics), start=1):
        lines.append(f"| {i} | `{label}` | {_cell(lang)} | {_cell(math)} |")

    lines += ["", "## Claims checked by column 3", "",
              "| Claim | Exact value |", "|-------|-------------|"]
    for key in sorted(trace.expected):
        lines.append(f"| `{key}` | `{trace.expected[key]}` |")

    if trace.verdict is not None:
        v = trace.verdict
        lines += [
            "", "## Column 3 verdict", "",
            f"- executed: **{v.executed}**",
            f"- exit code: **{v.returncode}**",
            f"- parent-process key-by-key match: **{v.matches_column2}**",
            f"- verified (both checks agree): **{v.verified}**",
        ]
        if v.mismatches:
            lines.append("- mismatches:")
            for key, want, got in v.mismatches:
                lines.append(f"  - `{key}`: column 2 `{want}`, "
                             f"recomputation `{got}`")
        if v.missing_keys:
            lines.append(f"- claims the script did not report: "
                         f"{list(v.missing_keys)}")
        if v.stderr_tail.strip():
            lines += ["", "```text", v.stderr_tail.strip()[-1200:], "```"]

    if include_script:
        lines += ["", "## Column 3 -- executable script", "",
                  "```python", trace.script.rstrip(), "```"]
    return "\n".join(lines) + "\n"


def _cell(text: str) -> str:
    """Fold a multi-line step into one Markdown table cell."""
    return text.replace("|", r"\|").replace("\n", "<br>")
