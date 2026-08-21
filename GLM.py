#!/usr/bin/env python3
"""``GLM.py`` -- the command-line entry point for the Geometric Language Machine.

A thin shell over :mod:`glm_universal.runtime`.  Everything substantive happens
there: parsing, the session, the Three Column Thinking trace, the script
verification.  This file owns argument parsing, presentation, and exit codes.

The shape of the surface
-------------------------
Two operating modes:

* **batch** -- one or more ``-q QUERY`` flags or a ``--query-file PATH`` file
  of newline-separated queries.  Each query is parsed, solved, traced, and
  printed.  Exit code 0 if every query solved; 1 if any did not or was
  malformed; 2 if the invocation itself was a usage error.
* **interactive** -- ``--interactive`` opens a REPL on ``source`` (stdin by
  default).  Meta-commands start with ``:`` and adjust the session state
  without restarting it.  Plain lines are queries.  EOF or ``:quit`` ends
  the session.

Three columns
-------------
A trace has three columns -- language, exact mathematics, and an executable
script -- plus the expected key/value claims that the script re-derives.  The
``-c`` flag selects which columns to print; default is ``1,2``.

Formats
-------
``text`` (the default) is human-readable.  ``json`` is the trace's own
``as_dict`` payload, with ``column1_language`` and ``column2_mathematics``
keys.  ``markdown`` renders the trace as a Markdown table.  ``--export-trace
PATH`` writes the trace to disk; the suffix ``.md``, ``.json`` or ``.py``
chooses what gets written.  Several traces under one ``--export-trace`` of
``.json`` suffix are written as a JSON list.

Verification
------------
``--verify-tct`` runs column 3 in a fresh interpreter and reports whether it
reproduced column 2.  ``--check-script-exactness`` AST-scans every generated
script and refuses to ship one that contains a float literal, a ``float()``
call, or an RNG import.

Invariants, inherited from :mod:`glm_universal`
-----------------------------------------------
Exact arithmetic (``int`` / ``fractions.Fraction``), no randomness, standard
library plus :mod:`glm_universal` only.  An AST scan in the test suite
asserts the same for this file.
"""

from __future__ import annotations

import argparse
import ast
import io
import json
import os
import sys
from pathlib import Path
from typing import (Any, Dict, Iterable, List, Optional, Sequence, TextIO,
                    Tuple)

# The package lives one directory below this script.  Insert the parent
# (the repo root) so a fresh interpreter finds ``glm_universal`` on its
# ``sys.path`` even when invoked from elsewhere.
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from glm_universal.runtime import (DOMAINS, GeometricSession, QueryError,
                                    SolverError, build_trace, package_root,
                                    script_is_exact, trace_to_markdown,
                                    verify_trace)
from glm_universal.runtime.tct_engine import TCTError, ThreeColumnTrace

__all__ = ["main", "build_parser"]


# ===========================================================================
# 1.  OUTPUT WRITER -- a thin buffer with column-aware line emission
# ===========================================================================

class Out:
    """A small wrapper that lets tests substitute a :class:`io.StringIO`."""

    def __init__(self, stream: Optional[TextIO] = None) -> None:
        self._stream = stream if stream is not None else sys.stdout

    def write(self, text: str) -> None:
        self._stream.write(text)

    def line(self, text: str = "") -> None:
        self._stream.write(text + "\n")

    def rule(self, char: str = "-", width: int = 72) -> None:
        self.line(char * width)


# ===========================================================================
# 2.  COLUMN RENDERING
# ===========================================================================

#: Human-readable names for the three columns, in order.
COLUMN_NAMES = ("Column 1 -- Language", "Column 2 -- Exact mathematics",
                "Column 3 -- executable script")


def _parse_columns(spec: str) -> Tuple[int, ...]:
    """Parse ``-c 1,2`` into a tuple of column indices, validated.

    Returns a sorted tuple of indices in ``{1, 2, 3}``.  Raises
    :class:`ValueError` on anything else, which the caller turns into exit
    code 2 (usage error).
    """
    if not spec:
        return (1, 2)
    parts = spec.split(",")
    out: List[int] = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if not p.isdigit():
            raise ValueError(f"bad column {p!r}: not an integer")
        n = int(p)
        if n not in (1, 2, 3):
            raise ValueError(f"bad column {n}: must be 1, 2, or 3")
        out.append(n)
    if not out:
        return (1, 2)
    return tuple(sorted(set(out)))


def _render_text(out: Out, trace: ThreeColumnTrace,
                 columns: Sequence[int]) -> None:
    """Default text rendering: a header per included column."""
    out.line(f"QUERY   {trace.query}")
    out.line(f"KIND    {trace.kind}")
    out.line(f"ANSWER  {trace.answer}")
    for n in columns:
        out.line("")
        out.line(COLUMN_NAMES[n - 1])
        if n == 1:
            for i, line in enumerate(trace.language, 1):
                out.line(f"  {i}. {line}")
        elif n == 2:
            for i, line in enumerate(trace.mathematics, 1):
                out.line(f"  {i}. {line}")
        else:
            out.line(trace.script)
    if trace.verdict is not None:
        out.line("")
        _render_verdict(out, trace)


def _render_verdict(out: Out, trace: ThreeColumnTrace) -> None:
    v = trace.verdict
    flag = "True" if v.verified else "False"
    out.line(f"VERIFIED          {flag}")
    if not v.executed:
        out.line(f"NOT EXECUTED      {v.stderr_tail}")
    elif v.returncode != 0:
        out.line(f"EXIT CODE         {v.returncode}")
    if v.mismatches:
        out.line(f"MISMATCHES        {len(v.mismatches)}")
        for key, exp, got in v.mismatches:
            out.line(f"  {key}: expected={exp!r} observed={got!r}")
    if v.missing_keys:
        out.line(f"MISSING KEYS      {list(v.missing_keys)}")


def _render_markdown(out: Out, trace: ThreeColumnTrace,
                     columns: Sequence[int]) -> None:
    """Render the trace as a Markdown table -- one row per step."""
    out.line("# Three Column Thinking")
    out.line("")
    out.line(f"**Query.** `{trace.query}`  ")
    out.line(f"**Kind.** `{trace.kind}`  ")
    out.line(f"**Answer.** `{trace.answer}`  ")
    out.line("")
    header = "| # | Step |"
    sep = "|---|---|"
    if 2 in columns and 3 not in columns:
        header = "| # | Step | Mathematics |"
        sep = "|---|---|---|"
    elif 2 in columns and 3 in columns:
        header = "| # | Step | Mathematics | Script |"
        sep = "|---|---|---|---|"
    elif 1 in columns and 3 in columns and 2 not in columns:
        header = "| # | Step | Script |"
        sep = "|---|---|---|"
    elif 3 in columns and 1 not in columns and 2 not in columns:
        header = "| # | Script |"
        sep = "|---|---|"
    else:
        header = "| # | Step |"
        sep = "|---|---|"
    out.line(header)
    out.line(sep)
    for i in range(max(len(trace.language), len(trace.mathematics), 1)):
        cells = [str(i + 1)]
        if 1 in columns:
            cells.append(_cell_escape(trace.language[i] if i <
                                      len(trace.language) else ""))
        if 2 in columns and ("Mathematics" in header):
            cells.append(_cell_escape(trace.mathematics[i] if i <
                                      len(trace.mathematics) else ""))
        if 3 in columns and ("Script" in header):
            # The script is one big block; show it once on row 1.
            snippet = trace.script if i == 0 else ""
            cells.append(_cell_escape(snippet))
        out.line("| " + " | ".join(cells) + " |")
    if trace.verdict is not None:
        out.line("")
        out.line(f"**Verified.** `{trace.verified}`")


def _cell_escape(text: str) -> str:
    """Escape pipe characters so a Markdown table cell does not break."""
    if text is None:
        return ""
    return str(text).replace("\n", " ").replace("|", r"\|")


def _render_json(trace: ThreeColumnTrace) -> str:
    """The trace as a JSON string, with script included when present."""
    return json.dumps(trace.as_dict(include_script=True), indent=2,
                      sort_keys=False)


# ===========================================================================
# 3.  EXPORT
# ===========================================================================

def _write_export(target: Path, trace: ThreeColumnTrace,
                  traces: List[ThreeColumnTrace]) -> None:
    """Write a trace to disk according to the suffix of ``target``.

    ``.md``  -- the markdown rendering.
    ``.json``-- the JSON ``as_dict`` payload, or a list if ``traces`` has more.
    ``.py``  -- the column 3 script source.
    """
    suffix = target.suffix.lower()
    target.parent.mkdir(parents=True, exist_ok=True)
    if suffix == ".md":
        target.write_text(trace_to_markdown(trace), encoding="utf-8")
    elif suffix == ".json":
        if len(traces) > 1:
            payload = [t.as_dict(include_script=True) for t in traces]
        else:
            payload = trace.as_dict(include_script=True)
        target.write_text(json.dumps(payload, indent=2, sort_keys=False),
                          encoding="utf-8")
    elif suffix == ".py":
        target.write_text(trace.script, encoding="utf-8")
    else:
        # Unknown suffix -- default to text, but write something rather than
        # silently dropping the request.
        target.write_text(trace_to_markdown(trace), encoding="utf-8")


# ===========================================================================
# 4.  BATCH MODE
# ===========================================================================

def _solve_one(session: GeometricSession, query: str,
               domain: Optional[str]) -> Optional[ThreeColumnTrace]:
    """Solve one query and return its trace, or ``None`` if it could not be."""
    try:
        solution = session.ask(query, domain=domain)
    except QueryError as exc:
        # Malformed queries are reported, not raised.
        sys.stderr.write(f"malformed: {exc}\n")
        return None
    if not solution.ok:
        return None
    try:
        return build_trace(solution)
    except TCTError as exc:
        sys.stderr.write(f"trace error: {exc}\n")
        return None


def _print_solution_summary(out: Out, idx: int,
                            trace: Optional[ThreeColumnTrace]) -> None:
    if trace is None:
        out.line(f"[{idx}] UNSOLVED")
    else:
        out.line(f"[{idx}] ok  {trace.kind}")


def _batch_query(out: Out, session: GeometricSession, query: str,
                 domain: Optional[str], columns: Sequence[int],
                 fmt: str, verify: bool,
                 exactness_check: bool) -> Tuple[int, Optional[ThreeColumnTrace]]:
    """Run one batch query; print to ``out``; return ``(exit_code, trace)``."""
    try:
        solution = session.ask(query, domain=domain)
    except QueryError as exc:
        out.line(f"QUERY   {query}")
        out.line(f"malformed: {exc}")
        return 1, None

    trace: Optional[ThreeColumnTrace] = None
    if solution.ok:
        try:
            trace = build_trace(solution)
        except TCTError as exc:
            out.line(f"QUERY   {query}")
            out.line(f"trace error: {exc}")
            return 1, None
    else:
        out.line(f"QUERY   {query}")
        out.line(f"UNSOLVED        {solution.error or ''}")
        return 1, None

    if verify:
        trace = verify_trace(trace)

    if fmt == "json":
        out.write(_render_json(trace))
        out.line()
    elif fmt == "markdown":
        _render_markdown(out, trace, columns)
    else:
        _render_text(out, trace, columns)
        if solution.kind == "verify":
            semantics = solution.payload.get("verdict", {}).get(
                "semantics", "scalar")
            holds = solution.payload.get("verdict", {}).get("holds", True)
            if holds:
                out.line(f"holds under {semantics} semantics")
            else:
                out.line(f"fails under {semantics} semantics")

    if exactness_check:
        ok, offenders = script_is_exact(trace.script)
        if ok:
            out.line("script exact: construct no float, no RNG, stdlib only")
        else:
            out.line("script exact: FAILED")
            for o in offenders:
                out.line(f"  {o}")

    return 0, trace


# ===========================================================================
# 5.  INTERACTIVE MODE
# ===========================================================================

class _InteractiveState:
    """Mutable state for an interactive session."""

    def __init__(self, session: GeometricSession, out: Out,
                 columns: Sequence[int], verify: bool,
                 exactness_check: bool) -> None:
        self.session = session
        self.out = out
        self.columns = tuple(columns)
        self.verify = verify
        self.exactness_check = exactness_check
        self.last_trace: Optional[ThreeColumnTrace] = None
        self.exit_code = 0


def _print_banner(out: Out) -> None:
    out.rule("=")
    out.line("GLM -- Geometric Language Machine (interactive)")
    out.line("Type a query, or :help for meta-commands.  :quit to exit.")
    out.rule("=")


def _meta_help(out: Out) -> None:
    out.line("Meta-commands:")
    out.line("  :help              this list")
    out.line("  :domains           list loaded and available domains")
    out.line("  :basis NAME        set the dimensional basis (EXT10 or SI7)")
    out.line("  :columns N[,N...]  which columns to show (1=lang,2=math,3=script)")
    out.line("  :verify on|off    run column 3 after each query")
    out.line("  :snapshot          print the session state as JSON")
    out.line("  :history           list queries asked so far")
    out.line("  :export PATH      write the last trace to PATH (.md/.json/.py)")
    out.line("  :quit              exit")


def _meta_domains(out: Out, session: GeometricSession) -> None:
    loaded = session.loaded_domains()
    out.line("domains:")
    for d in DOMAINS:
        mark = "*" if d in loaded else " "
        try:
            size = len(session.register(d)) if d in loaded else None
        except SolverError:
            size = None
        out.line(f"  {mark} {d:<14}  ({size if size is not None else 'lazy'})")


def _meta_columns(state: _InteractiveState, args: str) -> None:
    args = args.strip()
    if not args:
        state.out.line(f"columns: {','.join(str(c) for c in state.columns)}")
        return
    try:
        cols = _parse_columns(args)
    except ValueError as exc:
        state.out.line(f"bad columns: {exc}")
        return
    state.columns = cols
    state.out.line(f"columns set to {','.join(str(c) for c in cols)}")


def _meta_basis(state: _InteractiveState, name: str) -> None:
    name = name.strip()
    if not name:
        state.out.line(f"basis: {state.session.basis}")
        return
    try:
        state.session.set_basis(name)
    except ValueError as exc:
        state.out.line(f"bad basis: {exc}")
        return
    state.out.line(f"basis set to {state.session.basis}")


def _meta_verify(state: _InteractiveState, args: str) -> None:
    arg = args.strip().lower()
    if arg in ("on", "true", "1", "yes"):
        state.verify = True
        state.out.line("verify on")
    elif arg in ("off", "false", "0", "no"):
        state.verify = False
        state.out.line("verify off")
    else:
        state.out.line(f"verify: {'on' if state.verify else 'off'}")


def _meta_snapshot(state: _InteractiveState) -> None:
    snap = state.session.snapshot()
    state.out.write(json.dumps(snap, indent=2, sort_keys=False))
    state.out.line()


def _meta_history(state: _InteractiveState) -> None:
    history = state.session.history
    if not history:
        state.out.line("no queries yet")
        return
    for r in history:
        flag = "ok" if r.ok else "FAIL"
        state.out.line(f"  [{r.index}] {flag:<4} {r.kind:<10} {r.raw_query}")


def _meta_export(state: _InteractiveState, target: str) -> None:
    target = target.strip()
    if not target:
        state.out.line("usage: :export PATH")
        return
    if state.last_trace is None:
        state.out.line("nothing to export yet")
        return
    _write_export(Path(target), state.last_trace, [state.last_trace])
    state.out.line(f"wrote {target}")


def _handle_meta(state: _InteractiveState, line: str) -> bool:
    """Handle one ``:command`` line.  Return True to continue, False to exit."""
    line = line[1:]  # strip the colon
    parts = line.split(None, 1)
    if not parts:
        state.out.line("unknown meta-command: (empty)")
        return True
    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""
    if cmd in ("quit", "q", "exit"):
        return False
    if cmd in ("help", "h", "?"):
        _meta_help(state.out)
    elif cmd == "domains":
        _meta_domains(state.out, state.session)
    elif cmd == "basis":
        _meta_basis(state, args)
    elif cmd == "columns":
        _meta_columns(state, args)
    elif cmd == "verify":
        _meta_verify(state, args)
    elif cmd == "snapshot":
        _meta_snapshot(state)
    elif cmd == "history":
        _meta_history(state)
    elif cmd == "export":
        _meta_export(state, args)
    else:
        state.out.line(f"unknown meta-command: :{cmd}")
    return True


def _interactive(out: Out, source: TextIO, session: GeometricSession,
                 columns: Sequence[int], verify: bool,
                 exactness_check: bool, banner: bool) -> int:
    state = _InteractiveState(session, out, columns, verify, exactness_check)
    if banner:
        _print_banner(out)
    idx = 0
    while True:
        line = source.readline()
        if line == "":
            # EOF
            break
        line = line.rstrip("\n")
        if not line.strip():
            continue
        if line.lstrip().startswith("#"):
            continue
        if line.startswith(":"):
            if not _handle_meta(state, line):
                break
            continue
        idx += 1
        out.line(f"QUERY   {line}")
        code, trace = _batch_query(out, session, line, None, state.columns,
                                   "text", state.verify, state.exactness_check)
        if trace is not None:
            state.last_trace = trace
        _print_solution_summary(out, idx - 1, trace)
        if code != 0:
            state.exit_code = 1
    return state.exit_code


# ===========================================================================
# 6.  ARGUMENT PARSING
# ===========================================================================

def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser.

    Kept on a function so tests can inspect the help without invoking the
    program.
    """
    p = argparse.ArgumentParser(
        prog="GLM",
        description="Geometric Language Machine -- substrate-native reasoning CLI",
        add_help=True,
    )
    p.add_argument("-q", "--query", action="append", default=[],
                   metavar="QUERY",
                   help="one query to solve (repeatable for several)")
    p.add_argument("--query-file", metavar="PATH",
                   help="read queries from a file, one per line")
    p.add_argument("-c", "--columns", default="1,2", metavar="N[,N...]",
                   help="which columns to show: 1=language, 2=math, 3=script")
    p.add_argument("-f", "--format", default="text",
                   choices=("text", "json", "markdown"),
                   help="output format (default: text)")
    p.add_argument("-d", "--domain", default=None,
                   help="restrict concept resolution to one domain")
    p.add_argument("--export-trace", metavar="PATH", default=None,
                   help="write the trace to PATH (.md, .json, or .py)")
    p.add_argument("--verify-tct", action="store_true",
                   help="run column 3 in a fresh interpreter and verify")
    p.add_argument("--check-script-exactness", action="store_true",
                   help="AST-scan every generated script for floats/RNG/imports")
    p.add_argument("--list-domains", action="store_true",
                   help="list the available registers and exit")
    p.add_argument("--interactive", action="store_true",
                   help="enter the interactive REPL (read from --input)")
    p.add_argument("--no-banner", action="store_true",
                   help="suppress the interactive banner")
    p.add_argument("--input", metavar="PATH", default=None,
                   help="read interactive input from PATH instead of stdin")
    return p


def _load_query_file(path: Path) -> List[str]:
    """Read queries from a file, ignoring blanks and ``#`` comments."""
    text = path.read_text(encoding="utf-8")
    out: List[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        out.append(line)
    return out


# ===========================================================================
# 7.  DISPATCH
# ===========================================================================

def main(argv: Optional[Sequence[str]] = None,
        out: Optional[TextIO] = None,
        source: Optional[TextIO] = None) -> int:
    """Run the CLI.

    Parameters
    ----------
    argv
        Argument vector, excluding ``argv[0]``.  Defaults to ``sys.argv[1:]``.
    out
        Where to write output.  Tests pass a :class:`io.StringIO`; the
        default is :data:`sys.stdout`.
    source
        Where to read interactive input from.  Tests pass a
        :class:`io.StringIO`; the default is :data:`sys.stdin`.

    Returns
    -------
    int
        Exit code: 0 on success, 1 if any query failed, 2 on usage error.
    """
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    out_stream = Out(out)
    source_stream = source if source is not None else sys.stdin

    # ----- list-domains: short-circuit before anything else -----
    if args.list_domains:
        return _cmd_list_domains(out_stream)

    # ----- column validation: usage errors are exit 2 -----
    try:
        columns = _parse_columns(args.columns)
    except ValueError as exc:
        out_stream.line(f"usage error: {exc}")
        return 2

    # ----- collect queries -----
    queries: List[str] = list(args.query)
    if args.query_file is not None:
        path = Path(args.query_file)
        if not path.exists():
            out_stream.line(f"usage error: query file not found: {path}")
            return 2
        queries.extend(_load_query_file(path))

    # ----- interactive mode -----
    if args.interactive:
        # In interactive mode, queries passed on the command line are
        # pre-run, then the REPL takes over.
        session = GeometricSession()
        if banner_suppressed(args):
            pass
        return _interactive(out_stream, source_stream, session, columns,
                            args.verify_tct, args.check_script_exactness,
                            banner=not args.no_banner)

    # ----- batch mode -----
    if not queries and not args.interactive:
        # No query and not interactive: print help, exit 2.
        parser.print_help(out_stream._stream)
        return 2

    session = GeometricSession()
    traces: List[ThreeColumnTrace] = []
    worst = 0
    for q in queries:
        code, trace = _batch_query(
            out_stream, session, q, args.domain, columns, args.format,
            args.verify_tct, args.check_script_exactness)
        if trace is not None:
            traces.append(trace)
        worst = max(worst, code)

    if args.export_trace is not None:
        if not traces:
            out_stream.line("nothing to export: no solved queries")
            return worst
        target = Path(args.export_trace)
        # For .json exports of multiple traces, write the list.
        if target.suffix.lower() == ".json" and len(traces) > 1:
            target.write_text(
                json.dumps([t.as_dict(include_script=True) for t in traces],
                           indent=2, sort_keys=False),
                encoding="utf-8")
        else:
            _write_export(target, traces[-1], traces)

    return worst


def banner_suppressed(args: argparse.Namespace) -> bool:
    return bool(args.no_banner)


def _cmd_list_domains(out: Out) -> int:
    """Print every domain with its register size."""
    out.line("domains:")
    out.line(f"  {'name':<14}  {'count':>6}    basis")
    out.line(f"  {'----':<14}  {'-----':>6}    -----")
    sess = GeometricSession()
    for d in DOMAINS:
        try:
            size = len(sess.register(d))
        except SolverError:
            size = 0
        out.line(f"  {d:<14}  {size:>6}    EXT10/SI7")
    return 0


# ===========================================================================
# 8.  ENTRY POINT
# ===========================================================================

def _entry() -> None:
    sys.exit(main())


if __name__ == "__main__":
    _entry()
