"""``glm_universal.runtime`` -- the interactive geometric language runtime.

Three modules turn the substrate, the carriers and the reasoning kernel into
something a person can hold a conversation with:

``parser``
    Deterministic semantic query parsing.  A fixed grammar and a fixed keyword
    table map a natural-language or symbolic string onto a typed
    :class:`~.parser.Query` -- no language model, no embedding, no sampling.
    Every classification decision is recorded on the query so it can be read
    back.
``session``
    :class:`~.session.GeometricSession`: lazily loaded registers (660 physical
    quantities, 118 chemical elements, the mathematics carriers, the lexicon,
    and a spatial register built from the MOG's own trio, sextet and frame),
    the concept index over them, the active dimensional basis, the inference
    history, and one solver per query kind.  A solver returns a
    :class:`~.session.Solution`: the reasoning chain with each step stated in
    both language and exact algebra, plus a flat mapping of falsifiable exact
    claims.
``tct_engine``
    Three Column Thinking.  Columns 1 and 2 are read off the same steps, so
    they are aligned by construction; column 3 is a generated, self-contained
    script that re-enters the package's public API in a fresh interpreter and
    asserts the claims of column 2.  A trace counts as verified only when the
    script exits 0 *and* the parent process's own key-by-key comparison of the
    script's output against column 2 finds no difference.

Scope of the verification claim
-------------------------------
Column 3 is a **same-session cross-check between two code paths** -- the
solver's and the script's -- not an independent reproduction of the
mathematics.  Both call the same ``glm_universal`` functions, so a defect in
those functions would be invisible to it.  What it does catch is the solver
mis-transcribing, mis-rounding or mis-labelling a result, and any dependence
of an answer on interpreter state, import order or cached tables, since the
script shares none of those.

Invariants, inherited unchanged
-------------------------------
Exact arithmetic (``int`` / ``fractions.Fraction``), no randomness, standard
library only -- and the same holds for every script this package generates,
which :func:`~.tct_engine.script_is_exact` checks by AST.
"""

from __future__ import annotations

from . import parser, session, tct_engine
from .parser import (DOMAIN_PRIORITY, KINDS, VERBS, ConceptIndex, Query,
                     QueryError, QueryKind, levenshtein, normalise,
                     parse_query, split_analogy, split_equation, tokenise)
from .session import (DEFAULT_SUBSPACE, DOMAINS, GeometricSession,
                      InferenceRecord, Solution, SolverError, Step,
                      spatial_objects)
from .tct_engine import (BEGIN_MARKER, DEFAULT_TIMEOUT_SECONDS, END_MARKER,
                         ScriptVerdict, TCTError, ThreeColumnTrace,
                         build_trace, package_root, render_script,
                         script_is_exact, trace_to_markdown, verify_trace)

__all__ = [
    "parser", "session", "tct_engine",
    # parser
    "QueryError", "QueryKind", "KINDS", "VERBS", "DOMAIN_PRIORITY", "Query",
    "ConceptIndex", "normalise", "tokenise", "levenshtein", "split_analogy",
    "split_equation", "parse_query",
    # session
    "SolverError", "DOMAINS", "DEFAULT_SUBSPACE", "Step", "Solution",
    "InferenceRecord", "GeometricSession", "spatial_objects",
    # tct_engine
    "TCTError", "BEGIN_MARKER", "END_MARKER", "DEFAULT_TIMEOUT_SECONDS",
    "ScriptVerdict", "ThreeColumnTrace", "package_root", "render_script",
    "script_is_exact", "build_trace", "verify_trace", "trace_to_markdown",
]


def ask(text: str, domain: str = None, verify: bool = False):
    """One-shot convenience: parse, solve and trace a single query.

    Builds a throwaway :class:`~.session.GeometricSession`, so it pays the
    register load every call.  For more than one query, hold a session.

    Parameters
    ----------
    text
        The query.
    domain
        Optional domain hint.
    verify
        Whether to run column 3 in a subprocess before returning.

    Returns
    -------
    ThreeColumnTrace
    """
    sess = GeometricSession()
    solution = sess.ask(text, domain)
    trace = build_trace(solution)
    return verify_trace(trace) if verify else trace
