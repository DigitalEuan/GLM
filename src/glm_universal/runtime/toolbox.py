"""``glm_universal.runtime.toolbox`` -- every working part, named and reachable.

What this module is
-------------------
Until Phase 66 the GLM's surfaces were reached by flag -- ``-q`` for the
planner and the grammar, ``--eng`` for engineering, ``--python`` for the
Python dialect and, through it, the carried fork -- and eight tested
reasoning modules were reached by nothing at all (the wiring audit,
``studies/scripts/wiring_audit.py``).  This module is the catalogue the
router of :mod:`glm_universal.runtime.router` reads: each **surface** says
what text it reads and how, and each **tool** is one of the eight, reached by
``tool <name>`` and answering from its own module, with the Lean
specification and the study it answers to.

A tool never quotes a number: every figure in its answer is recomputed by the
module it names, when it is asked.  The two tools whose full studies are
census-sized (``tie break`` and ``stability``, both over the 3,838-name Lean
address book) answer for **one** named declaration, which is the question a
caller can actually ask of them; their censuses stay in their studies.

``studies/CONNECTED_MACHINE_STUDY.md`` is the study; the decision for each of
the eight is *reachable*, recorded there with the reason.

Last altered 20 October 2026 (Phase 167: `adversarial_dialogue_study` declared in the wiring census; Phase 169: `evidence_model_study`; Phase 170: the engineering surface's ten frames; Phase 171: `evidence_in_use_study`; Phase 172: `resumed_dialogue_study`; Phase 173: `stacked_dialogue_study`; Phase 174: `quoted_measurements_study`). Last altered 21 October 2026 (Phase 175: `tool induce`, the owner's pipeline kit as a reachable tool; `pipeline_kit_study` declared in the wiring census).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Mapping, Optional, Tuple

__all__ = ["Surface", "Tool", "ToolResult", "SURFACES", "TOOLS",
           "tool_named", "run_tool", "reads_tool", "catalogue_text",
           "TOOL_PHRASES", "phrase_tool", "MEASUREMENT_ONLY",
           "wiring_census"]


@dataclass(frozen=True)
class Surface:
    """A way into the machine: what it reads, and how a caller reaches it."""

    name: str
    reads: str
    reached_by: str
    faculty: str
    lean: Tuple[str, ...]
    study: str


@dataclass(frozen=True)
class ToolResult:
    """What a tool gave: an answer or a refusal, with its figures."""

    ok: bool
    text: str
    figures: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class Tool:
    """One reasoning module, made reachable by ``tool <name> [argument]``."""

    name: str
    module: str
    summary: str
    faculty: str
    lean: Tuple[str, ...]
    study: str
    run: Callable[[str], ToolResult]
    takes: str = ""


#: The surfaces, in the order the router tries them.
SURFACES: Tuple[Surface, ...] = (
    Surface("toolbox", "text that starts with `tool`, or is `tools`",
            "GLM.py --ask 'tool <name>'", "address",
            ("RequestProject/GLM/ConnectedMachine.lean",),
            "studies/CONNECTED_MACHINE_STUDY.md"),
    Surface("reverse", "text that starts with a reverse-TCT operation "
            "(`say:`, `equivalent:`, `paraphrase:`, `negate:`, `solve for x:`, "
            "`entails:`, `bounds of x:`, `entails over the integers:`, "
            "`bounds over the integers of x:`, and `relay:` before any of "
            "them, which hands the values to the planner)", "GLM.py --ask 'say: "
            "SOURCE', or --reverse TEXT", "derive, refusal",
            ("RequestProject/GLM/ReverseTCT.lean",
             "RequestProject/GLM/ReverseTCTTwo.lean",
             "RequestProject/GLM/ReverseTCTThree.lean"),
            "studies/REVERSE_TCT_STUDY.md"),
    Surface("python", "a Python program whose every loaded name is bound",
            "GLM.py --ask SOURCE, or --python SOURCE", "derive",
            ("RequestProject/GLM/PythonSpeech.lean",
             "RequestProject/GLM/CarriedFork.lean"),
            "studies/PYTHON_SPEECH_STUDY.md"),
    Surface("frames", "a question one of the declared question frames reads "
            "(Phase 89: agree channel at a floor, declared error weight, rate "
            "grid, Routh cubic, reflection/VSWR, aliasing, convolution, "
            "Wiener taps, entropies, Huffman, Kalman rank, Golay deep holes, "
            "...); each answer gated by its column-3 script under python3 -I",
            "GLM.py --ask TEXT, or -q TEXT", "derive, refusal",
            ("RequestProject/GLM/QuestionSetB.lean",
             "RequestProject/GLM/ConnectedMachine.lean"),
            "studies/QUESTION_SET_B_STUDY.md"),
    Surface("engineering", "a question one of the ten engineering frames "
            "reads (in a declared context, across domains, across wheels, "
            "derive, wheel, check, Smith, analogy, resonance, delta-sigma)", "GLM.py --ask TEXT, or --eng -q TEXT",
            "derive", ("RequestProject/GLM/EngineeringWheels.lean",
                       "RequestProject/GLM/ConnectedMachine.lean"),
            "studies/ENGINEERING_LANGUAGE_STUDY.md"),
    Surface("planner", "everything else: the typed planner, then the "
            "grammar, then -- only on a refusal -- the stepwise planner, "
            "which reads the text as a chain of planner steps",
            "GLM.py --ask TEXT, -q TEXT, or --steps TEXT",
            "derive, address, refusal",
            ("RequestProject/GLM/SemanticPlan.lean",
             "RequestProject/GLM/StepwisePlanner.lean",
             "RequestProject/GLM/StepwiseFrames.lean",
             "RequestProject/GLM/StepwiseWiden.lean",
             "RequestProject/GLM/HoleBounds.lean",
             "RequestProject/GLM/DeclaredFrames.lean"),
            "studies/SEMANTIC_PLAN_STUDY.md"),
)


# ===========================================================================
# THE EIGHT TOOLS
# ===========================================================================

def _moonshine(arg: str) -> ToolResult:
    from ..reasoning import moonshine as m
    r = m.moonshine_report()
    dims = r["graded_dimensions"]
    return ToolResult(True, "moonshine: the graded dimensions of V-natural "
                      f"are {', '.join(str(d) for d in dims)} (the "
                      "coefficients of j - 744); dim V_2 = "
                      f"{r['v2_dimension']} = 196560 + 324, the Griess "
                      "algebra over the Leech minimal vectors",
                      {"graded_dimensions": list(dims),
                       "v2_dimension": r["v2_dimension"]})


def _llvq(arg: str) -> ToolResult:
    from ..reasoning import llvq as l
    r = l.llvq_report()
    shells = "; ".join(f"norm {s['norm2']}: {s['count']}"
                       for s in r["shells"])
    return ToolResult(True, f"llvq: {r['n_shells_catalogued']} Leech shells "
                      f"counted from the Golay census ({shells}); kissing "
                      f"number {r['kissing_number']}",
                      {"kissing_number": r["kissing_number"],
                       "shells": r["n_shells_catalogued"],
                       "shell_counts": {str(s["norm2"]): s["count"]
                                        for s in r["shells"]}})


def _pcgs(arg: str) -> ToolResult:
    from ..reasoning import pcgs as p
    r = p.pcgs_report()
    return ToolResult(True, f"pcgs: {r['admitted_count']} of "
                      f"{r['system_count']} generative systems admitted "
                      f"with correctness and resource evidence, "
                      f"{r['proved_count']} of them by proof",
                      {"admitted": r["admitted_count"],
                       "systems": r["system_count"],
                       "proved": r["proved_count"]})


def _salvage(arg: str) -> ToolResult:
    from ..reasoning import salvage as s
    r = s.salvage_report()
    files = ", ".join(f.split("/")[-1] for f, _, _ in s.RETRIEVED)
    return ToolResult(True, f"salvage: {r['retrieved_files']} archive "
                      f"results recomputed from the substrate, one per Lean "
                      f"file: {files}; e.g. the Golay weight enumerator "
                      f"{r['golay']['weight_enumerator']}",
                      {"retrieved": r["retrieved_files"]})


def _salvage_second(arg: str) -> ToolResult:
    from ..reasoning import salvage_second as s
    r = s.second_pass_report()
    files = ", ".join(f.replace("RequestProject/GLM/", "")
                      for f, _, _ in s.RETRIEVED_SECOND)
    return ToolResult(True, f"salvage second: {r['retrieved_files']} more "
                      f"archive results recomputed: {files}; the cube "
                      f"surface is the MOG grid ({r['cube']['faces']} faces "
                      f"of {r['cube']['cells_per_face']} cells)",
                      {"retrieved": r["retrieved_files"]})


def _deep_dive(arg: str) -> ToolResult:
    from ..reasoning import deep_dive as d
    r = d.deep_dive_report()
    b = r["balance"]
    return ToolResult(True, f"deep dive: {b['observed_balanced']} of the 759 "
                      f"octads are balanced, against "
                      f"{b['chance_census'][0]} of all "
                      f"{b['eight_subsets']} eight-subsets by chance "
                      f"(expected {b['expected_balanced_by_chance']} per 759)",
                      {"observed_balanced": b["observed_balanced"],
                       "chance_balanced": b["chance_census"][0]})


def _declaration(arg: str) -> Tuple[Optional[str], Optional[ToolResult]]:
    from ..reasoning import lean_address as la
    name = arg.strip()
    if not name:
        return None, ToolResult(False, "refused: name a Lean declaration, "
                                "e.g. GLM.Address.Quantiser")
    if name not in la.feature_table():
        return None, ToolResult(False, f"refused: {name} is not a "
                                "declaration of the Lean address book")
    return name, None


def _tie_break(arg: str) -> ToolResult:
    from ..reasoning import lean_address as la
    from ..reasoning import tie_break as tb
    name, refusal = _declaration(arg)
    if refusal is not None:
        return refusal
    vector = tb._scaled(la.feature_table()[name])
    rec = tb.tie_record(vector)
    return ToolResult(True, f"tie break: the address of {name} has a tie "
                      f"class of {rec['size']} equally near Leech points at "
                      f"squared distance {rec['distance2']}, counted in "
                      f"closed form; the stated rule takes the least",
                      {"size": rec["size"],
                       "distance2": str(rec["distance2"])})


def _stability(arg: str) -> ToolResult:
    from ..reasoning import stability as st
    name, refusal = _declaration(arg)
    if refusal is not None:
        return refusal
    r = st.stability_radius(name)
    return ToolResult(True, f"stability: the address of {name} holds under "
                      f"any perturbation of squared size below "
                      f"{r['crossing']} (stability radius squared "
                      f"{r['radius2']}, residual squared {r['residual2']}); "
                      f"certified by the exact criterion: {r['certified']}",
                      {"radius2": str(r["radius2"]),
                       "crossing": str(r["crossing"]),
                       "certified": bool(r["certified"])})


def _native_parity(arg: str) -> ToolResult:
    from ..reasoning import native_ledger as npar
    r = npar.tool_summary()
    counts = r["counts"]
    return ToolResult(True, "native parity: the ledger holds "
                      + ", ".join(f"{n} {klass}" for klass, n in counts.items())
                      + f"; the refinements taken are {', '.join(r['targets'])}; "
                      f"the read-back of {r['readback_exact']} of "
                      f"{r['readback_checked']} Leech addresses is exact",
                      {"counts": dict(counts),
                       "readback_exact": r["readback_exact"],
                       "readback_checked": r["readback_checked"]})


def _native_words(arg: str) -> ToolResult:
    from ..reasoning import golay_words as nwd
    r = nwd.tool_summary(arg)
    rows = r["tokens"]
    if not rows:
        return ToolResult(False, "native words: give a fragment of text to "
                          "read its tokens as Golay words", {"tokens": []})
    said = "; ".join(f"{row['token']} -> "
                     + ", ".join(f"{part} {word}" for part, word
                                 in zip(row["parts"], row["letter_words"]))
                     for row in rows)
    return ToolResult(True, "native words: each part's letter word, as a "
                      "24-bit Golay-space word in hexadecimal: " + said,
                      {"tokens": rows})


def _law_register(arg: str) -> ToolResult:
    from ..reasoning import law_register as lr
    r = lr.tool_summary(arg)
    if "law" in r:
        law = r["law"]
        if not law["known"]:
            # Phase 136: a law the register does not retain may be one of the
            # 106 the law triage gave a fate to; until then that fate was a
            # record no question reached.
            from ..reasoning import law_triage as lt
            if law["id"] in lt.FATE:
                fate = lt.fate_of(law["id"])
                return ToolResult(True, f"law register: {law['id']} is not "
                                  "one of the 65 retained laws; the law "
                                  f"triage gave it the fate {fate['fate']} "
                                  f"({fate['reason']}): {fate['note']}",
                                  {"law": law, "triage": fate})
            return ToolResult(False, f"law register: {law['id']} is not one of "
                              "the 65 retained laws nor of the 106 triaged "
                              "ones", {"law": law})
        return ToolResult(True, f"law register: {law['id']} ({law['class']}) is "
                          f"{law['verdict']}: {law['reason']}", {"law": law})
    exact = ", ".join(f"{n} {k}" for k, n in r["exact_census"].items())
    numeric = ", ".join(f"{n} {k}" for k, n in r["numeric_census"].items())
    return ToolResult(True, "law register: the 16 exact rows are " + exact
                      + "; the 49 numeric rows are " + numeric
                      + f"; of {r['formulas_tested']} external formulas "
                      f"{r['formulas_admitted']} pass the look-elsewhere test "
                      f"({', '.join(r['admitted'])})",
                      {k: v for k, v in r.items()})


def _ladder(arg: str) -> ToolResult:
    """The operations ladder (Phase 125): one term, the relation between two,
    or the census."""
    from ..reasoning import ops_ladder as ol
    text = arg.strip()
    if not text:
        note = ol.note_check()
        h = ol.projection_census()
        return ToolResult(True, f"ladder: {note['terms']} terms in 10 tiers, "
                          f"every one grounded in the 10 machine primitives, "
                          f"{len(note['layering_violations'])} layering "
                          f"violations; {len(ol.CROSSOVERS)} cross-overs to "
                          f"what the GLM already holds; the projection onto "
                          f"the Geometric-Cybernetic ladder is monotone on "
                          f"{h['monotone']} of {h['edges']} composition edges",
                          {"terms": note["terms"], "monotone": h["monotone"],
                           "edges": h["edges"]})
    import re as _re
    m = _re.match(r"^(?:relation\s+(?:between\s+)?)?(.+?)\s+and\s+(.+)$",
                  text, _re.IGNORECASE)
    if m:
        a, b = ol.resolve(m.group(1)), ol.resolve(m.group(2))
        if a is None or b is None:
            missing = m.group(1) if a is None else m.group(2)
            return ToolResult(False, f"refused: {missing!r} is not a term of "
                              "the operations ladder", {})
        return ToolResult(True, "ladder: " + ol.relation_sentence(a, b),
                          {"relation": ol.relation(a, b)["kind"]})
    term = ol.resolve(text)
    if term is None:
        return ToolResult(False, f"refused: {text!r} is not a term of the "
                          "operations ladder", {})
    return ToolResult(True, "ladder: " + ol.term_sentence(term),
                      {"term": term, "tier": ol.tier_of(term)})


def _machine(arg: str) -> ToolResult:
    """GLM-BAT (Phase 125): ``QUESTION :: PROGRAM [:: file PATH=a // b]
    [:: env NAME=value]``; program lines are separated by newlines or
    ``;;``, and may be written as English sentences."""
    from ..reasoning import batch_speech as bs
    parts = [p.strip() for p in arg.split("::")]
    if len(parts) < 2 or not parts[0] or not parts[1]:
        return ToolResult(False, "refused: give QUESTION :: PROGRAM, e.g. "
                          "tool machine what does it print? :: ECHO hello", {})
    env: Dict[str, str] = {}
    files: Dict[str, List[str]] = {}
    for extra in parts[2:]:
        kind, _, rest = extra.partition(" ")
        name, _, value = rest.partition("=")
        if kind.lower() == "env" and name:
            env[name.strip()] = value.strip()
        elif kind.lower() == "file" and name:
            files[name.strip()] = [v.strip() for v in value.split("//")]
        else:
            return ToolResult(False, f"refused: {extra!r} is neither "
                              "'env NAME=value' nor 'file PATH=a // b'", {})
    a = bs.answer(parts[0], parts[1], env, files)
    tail = (" [column 3 verified]" if a.verified else "")
    return ToolResult(a.answered, "machine: " + a.body() + tail,
                      {"refusal": a.refusal, "faculty": a.faculty,
                       "sentences": a.column1, "program": a.column2,
                       "claim": a.claim})


# ===========================================================================
# THE TOOLS OF PHASE 136 -- operations measured in a study, never reached
# ===========================================================================

#: The longest expansion a stream tool emits, and the precision it stops at.
STREAM_MAX_TERMS = 40
STREAM_MAX_BITS = 4096


def _terms_option(text: str, default: int = 10) -> Tuple[str, int]:
    """Split an optional ``terms N`` (or ``N terms``) off a stream request."""
    import re as _re
    m = _re.search(r"\s*(?:\bterms\s+(\d+)|\b(\d+)\s+terms)\s*$", text,
                   _re.IGNORECASE)
    if not m:
        return text.strip(), default
    return text[:m.start()].strip(), int(m.group(1) or m.group(2))


def _exact_fraction(text: str):
    from fractions import Fraction
    try:
        return Fraction(text.replace(" ", ""))
    except (ValueError, ZeroDivisionError):
        return None


def _continued_fraction(arg: str) -> ToolResult:
    """Certified continued-fraction terms of a written real (Phase 136)."""
    from ..reasoning import exact_real as xr
    from ..reasoning import substrate_cognition as sc
    text, count = _terms_option(arg)
    if not text:
        return ToolResult(False, "refused: give a real, e.g. tool continued "
                          "fraction sqrt(2) terms 8", {})
    if not 1 <= count <= STREAM_MAX_TERMS:
        return ToolResult(False, f"refused: ask for 1 to {STREAM_MAX_TERMS} "
                          "terms", {})
    q = _exact_fraction(text)
    if q is not None:
        terms = xr.continued_fraction(q, count)
        return ToolResult(True, f"continued fraction: {text} is the rational "
                          f"{q}, whose expansion is exact: "
                          f"[{', '.join(map(str, terms))}]"
                          + (" (it ends there)" if len(terms) < count else ""),
                          {"terms": list(terms), "exact": True,
                           "complete": True})
    try:
        x = xr.parse_real(text)
    except ValueError as error:
        return ToolResult(False, f"refused: {error}", {})
    terms, bits, complete = sc.cf_certified(x, count,
                                            max_bits=STREAM_MAX_BITS)
    said = ", ".join(map(str, terms))
    if complete:
        return ToolResult(True, f"continued fraction: the first {count} "
                          f"terms of {text} are [{said}], each certified by "
                          f"both ends of an interval of width 2^-{bits - 1} "
                          "around it (GLM.CertifiedStreams.cfPrefix_certified)",
                          {"terms": list(terms), "bits": bits,
                           "complete": True, "exact": False})
    return ToolResult(len(terms) > 0, f"continued fraction: only "
                      f"{len(terms)} of the {count} terms of {text} are "
                      f"certified at 2^-{bits}: [{said}]; the rest are "
                      "refused, since a value whose expansion ends (a "
                      "rational written as an expression) certifies no term "
                      "past its last one at any precision",
                      {"terms": list(terms), "bits": bits,
                       "complete": False, "exact": False})


def _mobius(arg: str) -> ToolResult:
    """``a b c d of X``: the continued fraction of ``(a X + b)/(c X + d)``,
    streamed from the certified terms of ``X`` by Gosper's rule (Phase 136)."""
    import re as _re
    from fractions import Fraction
    from ..reasoning import exact_real as xr
    from ..reasoning import substrate_cognition as sc
    text, count = _terms_option(arg)
    m = _re.match(r"^\s*(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+of\s+(.+)$",
                  text, _re.IGNORECASE)
    if not m:
        return ToolResult(False, "refused: give 'a b c d of X', e.g. tool "
                          "mobius 1 1 1 0 of sqrt(2), for (a X + b)/(c X + d)",
                          {})
    a, b, c, d = (int(m.group(i)) for i in range(1, 5))
    expr = m.group(5).strip()
    if not 1 <= count <= STREAM_MAX_TERMS:
        return ToolResult(False, f"refused: ask for 1 to {STREAM_MAX_TERMS} "
                          "terms", {})
    if a * d - b * c == 0:
        return ToolResult(False, f"refused: ({a} X + {b})/({c} X + {d}) is "
                          "constant or undefined (ad - bc = 0), not a "
                          "homographic transform", {})
    q = _exact_fraction(expr)
    if q is not None:
        if c * q + d == 0:
            return ToolResult(False, f"refused: the denominator {c} X + {d} "
                              f"vanishes at X = {q}", {})
        y = (a * q + b) / (c * q + d)
        terms = xr.continued_fraction(Fraction(y), count)
        return ToolResult(True, f"mobius: X = {q} is rational, so "
                          f"({a} X + {b})/({c} X + {d}) = {y} exactly: "
                          f"[{', '.join(map(str, terms))}]",
                          {"terms": list(terms), "exact": True})
    try:
        x = xr.parse_real(expr)
    except ValueError as error:
        return ToolResult(False, f"refused: {error}", {})
    want = count + 8
    out: List[int] = []
    used = 0
    while True:
        inputs, bits, complete = sc.cf_certified(x, want,
                                                 max_bits=STREAM_MAX_BITS)
        out = list(sc.mobius_stream(a, b, c, d, inputs))[:count]
        used = len(inputs)
        if len(out) >= count or not complete or want >= 8 * STREAM_MAX_TERMS:
            break
        want *= 2
    if not out:
        return ToolResult(False, f"refused: no term of ({a} X + {b})/({c} X + "
                          f"{d}) at X = {expr} is decided by the {used} "
                          "certified terms of X", {"inputs": used})
    check = ""
    figures: Dict[str, object] = {"terms": list(out), "inputs": used}
    try:
        direct = xr.parse_real(f"({a}*({expr})+{b})/({c}*({expr})+{d})")
        dterms, _, _ = sc.cf_certified(direct, len(out),
                                       max_bits=STREAM_MAX_BITS)
        agree = tuple(dterms) == tuple(out[:len(dterms)]) and \
            len(dterms) == len(out)
        figures["direct_agrees"] = agree
        check = ("; the direct expansion of the composed real agrees"
                 if agree else "; the direct expansion of the composed real "
                 f"gave [{', '.join(map(str, dterms))}] -- they disagree")
    except (ValueError, ZeroDivisionError):
        figures["direct_agrees"] = None
    short = (f" (only {len(out)} of {count} decided)" if len(out) < count
             else "")
    return ToolResult(True, f"mobius: ({a} X + {b})/({c} X + {d}) at X = "
                      f"{expr} is [{', '.join(map(str, out))}]{short}, "
                      f"streamed from {used} certified terms of X; each term "
                      "is emitted only when every tail gives it "
                      "(GLM.CertifiedStreams.gosper_emit_sound)" + check,
                      figures)


def _bind(arg: str) -> ToolResult:
    """``ROLE A B in DOMAIN``: a typed relation as one 24-bit word, and the
    filler read back from it (Phase 136; ``reasoning/role_binding.py``)."""
    import re as _re
    from ..reasoning import role_binding as rb
    m = _re.match(r"^\s*(\S+)\s+(\S+)\s+(\S+)\s+in\s+(\S+)\s*$", arg)
    if not m:
        return ToolResult(False, "refused: give 'ROLE A B in DOMAIN', e.g. "
                          "tool bind causes C O in chemistry; the roles are "
                          + ", ".join(sorted(rb.ROLES)), {})
    role, a, b, domain = m.groups()
    session = rb._session()
    try:
        bound = rb.bind_names(session, role, a, b, domain)
    except rb.BindingError as error:
        return ToolResult(False, f"refused ({error.reason}): {error}",
                          {"reason": error.reason})
    except (KeyError, ValueError) as error:
        return ToolResult(False, f"refused: {error}", {})
    try:
        back = rb.recover(session, bound.word, role, a, domain)
    except rb.BindingError as error:
        return ToolResult(False, f"bind: {bound.sentence}; reading the filler "
                          f"back is refused ({error.reason}): {error}",
                          {"word": bound.word, "reason": error.reason,
                           "candidates": list(error.candidates)})
    return ToolResult(True, f"bind: {bound.sentence}; unbinding with "
                      f"{role} and {a} reads the filler back as {back} "
                      "(GLM.RoleBinding.unbind_bind), the only carrier of "
                      f"the {domain} register with that reading",
                      {"word": bound.word, "recovered": back})


def _parse_word(text: str) -> Optional[int]:
    t = text.strip().lower().replace("_", "")
    try:
        if t.startswith("0x") or t.startswith("#"):
            value = int(t.lstrip("#")[2:] if t.startswith("0x") else t[1:], 16)
        elif t.startswith("0b"):
            value = int(t[2:], 2)
        else:
            value = int(t)
    except ValueError:
        return None
    return value if 0 <= value < (1 << 24) else None


def _gates(arg: str) -> ToolResult:
    """``SOURCE to TARGET``: the least number of Toffoli/Fredkin moves on the
    eight 3-bit blocks of a 24-bit word, or the block that cannot be reached
    (Phase 136; ``reasoning/substrate_cognition.py``, X5)."""
    import re as _re
    from ..reasoning import substrate_cognition as sc
    m = _re.match(r"^\s*(\S+)\s+to\s+(\S+)\s*$", arg, _re.IGNORECASE)
    if not m:
        return ToolResult(False, "refused: give 'SOURCE to TARGET', two "
                          "24-bit words, e.g. tool gates 0x000007 to 0x000003",
                          {})
    source, target = _parse_word(m.group(1)), _parse_word(m.group(2))
    if source is None or target is None:
        bad = m.group(1) if source is None else m.group(2)
        return ToolResult(False, f"refused: {bad!r} is not a 24-bit word", {})
    moves = sc.reachability_certificate(source, target)
    if moves is None:
        dist = sc.gate_orbit_distances()
        block = next(bk for bk in range(8)
                     if ((source >> 3 * bk) & 7, (target >> 3 * bk) & 7)
                     not in dist)
        s3, t3 = (source >> 3 * block) & 7, (target >> 3 * block) & 7
        if not s3 & 1:
            why = ("its control bit is clear, and both gates fix a block whose "
                   "control bit is clear (GLM.SubstrateCognition."
                   "gates_fix_of_control_clear)")
        elif not t3 & 1:
            why = ("no word of the two gates changes a block's control bit "
                   "(GLM.SubstrateCognition.applyWord_control)")
        else:
            why = ("the target is outside the source's orbit under the two "
                   "gates, found by breadth-first search over the eight "
                   "3-bit values")
        return ToolResult(False, f"gates: 0x{target:06x} is not reachable "
                          f"from 0x{source:06x}: block {block} must go from "
                          f"{s3:03b} to {t3:03b} (bits read low to high as "
                          f"a + 2b + 4c), and {why}",
                          {"reachable": False, "block": block})
    return ToolResult(True, f"gates: 0x{source:06x} reaches 0x{target:06x} in "
                      f"exactly {moves} Toffoli/Fredkin move{'' if moves == 1 else 's'}, "
                      "the sum of "
                      "the least distances of its eight blocks, each found "
                      "by breadth-first search over the eight 3-bit values",
                      {"reachable": True, "moves": moves})


def _tag_length(arg: str) -> ToolResult:
    """``D``: how many tag bits a tie-resolving tag with octad weight ``D``
    needs, from the proved floors (Phase 136; ``reasoning/shortest_tag.py``)."""
    from ..reasoning import shortest_tag as stg
    text = arg.strip().lower()
    for prefix in ("for distance ", "distance ", "d=", "d "):
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
    try:
        d = int(text)
    except ValueError:
        return ToolResult(False, "refused: give the octad tag weight D the tag "
                          "must reach (D = 2s + 1 corrects s flipped tag "
                          "bits), e.g. tool tag length 5", {})
    if d < 1:
        return ToolResult(False, "refused: D must be at least 1 -- a tag of "
                          "octad weight 0 resolves no tie", {})
    general = d + 6
    built = stg.FLOOR_BUILT.get(d)
    flips = (d - 1) // 2
    tail = (f"; built as parities of the seven-bit tag it needs {built} bits "
            "(GLM.Golay24.built_tag_floor), and the GLM's tag of that "
            "length meets it" if built is not None and d > 1 else
            "; the seven-bit sender tag meets it (GLM.Golay24.tag7_shortest)"
            if d == 1 else "; no floor for tags built on seven bits is proved "
            "at this weight")
    return ToolResult(True, f"tag length: a tag giving every octad tag weight "
                      f"at least {d} (absorbing {flips} flipped tag bit"
                      f"{'' if flips == 1 else 's'}) has at least {general} "
                      f"bits (GLM.Golay24.tag_length_floor){tail}",
                      {"general_floor": general, "built_floor": built})


# ===========================================================================
# THE TOOLS OF PHASE 137 -- a fraction, not a term list
# ===========================================================================

def _parse_real_or_fraction(expr: str):
    """An exact real for ``expr``: a rational written plainly is held exactly
    (so the tools can say it ends), anything else through ``parse_real``."""
    from ..reasoning import exact_real as xr
    q = _exact_fraction(expr)
    if q is not None:
        x = xr.from_fraction(q)
        return x
    return xr.parse_real(expr)


def _convergent(arg: str) -> ToolResult:
    """``K of X``: the ``K``-th convergent of the continued fraction of ``X``
    (Phase 137; ``reasoning/rational_approx.py``)."""
    import re as _re
    from ..reasoning import exact_real as xr
    from ..reasoning import rational_approx as ra
    from ..reasoning import substrate_cognition as sc
    m = _re.match(r"^\s*(\d+)\s+of\s+(.+)$", arg, _re.IGNORECASE)
    if not m:
        return ToolResult(False, "refused: give 'K of X', e.g. tool "
                          "convergent 4 of pi (the first convergent is the "
                          "integer part)", {})
    k, expr = int(m.group(1)), m.group(2).strip()
    if not 1 <= k <= STREAM_MAX_TERMS:
        return ToolResult(False, f"refused: ask for convergent 1 to "
                          f"{STREAM_MAX_TERMS}", {})
    q = _exact_fraction(expr)
    if q is not None:
        terms = xr.continued_fraction(q, k)
        if len(terms) < k:
            return ToolResult(False, f"refused: {q} is rational and its "
                              f"expansion [{', '.join(map(str, terms))}] has "
                              f"only {len(terms)} terms, so it has no "
                              f"convergent {k}", {"terms": list(terms)})
        exact = True
    else:
        try:
            x = xr.parse_real(expr)
        except ValueError as error:
            return ToolResult(False, f"refused: {error}", {})
        terms, bits, complete = sc.cf_certified(x, k,
                                                max_bits=STREAM_MAX_BITS)
        if not complete:
            return ToolResult(False, f"refused: only {len(terms)} terms of "
                              f"{expr} are certified at 2^-{bits}, and "
                              f"convergent {k} needs {k}",
                              {"terms": list(terms)})
        exact = False
    value = ra.convergent(terms, k)
    return ToolResult(True, f"convergent: convergent {k} of {expr} is "
                      f"{value}, from the "
                      f"{'exact' if exact else 'certified'} terms "
                      f"[{', '.join(map(str, terms[:k]))}] by p_k = a_k "
                      "p_(k-1) + p_(k-2), q_k likewise; it is the value of "
                      "that finite expansion, in lowest terms "
                      "(GLM.ToolValues.cfValue_eq_conv, "
                      "GLM.ToolValues.conv_det)",
                      {"value": str(value), "k": k,
                       "terms": list(terms[:k]), "exact": exact})


def _best_approximation(arg: str) -> ToolResult:
    """``X denominator N``: the fraction nearest ``X`` with denominator at
    most ``N`` (Phase 137; ``reasoning/rational_approx.py``)."""
    import re as _re
    from ..reasoning import rational_approx as ra
    m = _re.match(r"^\s*(.+?)\s+(?:denominator|den|q)\s*(?:<=|at most)?\s*"
                  r"(\d+)\s*$", arg, _re.IGNORECASE)
    if not m:
        return ToolResult(False, "refused: give 'X denominator N', e.g. tool "
                          "best approximation pi denominator 1000", {})
    expr, bound = m.group(1).strip(), int(m.group(2))
    try:
        x = _parse_real_or_fraction(expr)
    except ValueError as error:
        return ToolResult(False, f"refused: {error}", {})
    got = ra.best_approximation(x, bound)
    if not got["ok"]:
        return ToolResult(False, f"refused: {got['reason']}",
                          {"candidates": [str(c) for c in
                                          got.get("candidates", [])]})
    value = got["value"]
    figures: Dict[str, object] = {
        "value": str(value), "bound": bound,
        "candidates": [str(c) for c in got["candidates"]],
        "terms_used": got["terms_used"]}
    if got["exact_input"] and len(got["candidates"]) == 1:
        return ToolResult(True, f"best approximation: {expr} is itself the "
                          f"fraction {value}, whose denominator is at most "
                          f"{bound}", dict(figures, certificate=None))
    cert = got["certificate"]
    figures["certificate"] = {"det": cert["det"],
                              "denominator_sum": cert["denominator_sum"]}
    cands = " and ".join(str(c) for c in got["candidates"])
    return ToolResult(True,
                      f"best approximation: the fraction nearest {expr} with "
                      f"denominator at most {bound} is {value}; the "
                      f"candidates were {cands} (the last convergent within "
                      "the bound and the semiconvergent below the next), "
                      "told apart by the side of their midpoint the value "
                      "lies on (GLM.ToolValues.closer_iff_midpoint); they are "
                      f"Farey neighbours (b c - a d = {cert['det']}), their "
                      f"denominators add up to {cert['denominator_sum']}, past "
                      f"{bound}, and the value lies between them, so no "
                      f"fraction with denominator at most {bound} is nearer "
                      "(GLM.NearestFraction.farey_certificate; that the two "
                      "candidates always pass is the classical theorem "
                      "GLM.NearestFraction.nearest_fraction_candidates)",
                      figures)


# ===========================================================================
# THE WIRING CENSUS -- every reasoning module reached, or declared not to be
# ===========================================================================

#: The reasoning modules no query reaches, each with the reason it is not a
#: tool.  ``wiring_census`` fails a module that is neither reached from the
#: runtime nor named here, so a new study module cannot be left behind
#: silently (Phase 136).
MEASUREMENT_ONLY: Mapping[str, str] = {
    "affine_output": "the GLM-BAT battery of Phase 132; its rule lives in "
                     "batch_machine, reached through `tool machine`",
    "constant_bound": "the GLM-BAT battery of Phase 131; its rule lives in "
                      "batch_machine, reached through `tool machine`",
    "counter_lasso": "the GLM-BAT battery of Phase 130; its rule lives in "
                     "batch_machine, reached through `tool machine`",
    "inert_counter": "the GLM-BAT battery of Phase 126; its rule lives in "
                     "batch_machine, reached through `tool machine`",
    "operations": "the operations-round battery; the ladder and GLM-BAT it "
                  "measures are `tool ladder` and `tool machine`",
    "quadratic_lasso": "the GLM-BAT battery of Phase 142; its rule lives in "
                       "batch_machine, reached through `tool machine`",
    "address_read_study": "the address-read battery of Phase 143; the read "
                          "itself is the `locate` query kind",
    "coordinate_junction_study": "the register-junction battery of Phase "
                                 "144; the junction read itself is the "
                                 "`locate` query kind",
    "answering_question": "the measurement of Phase 146; the question it "
                          "measures is put by the `locate` query kind and "
                          "read back by the conversation's `reply` shape",
    "probe_budget": "the measurement of Phase 124; the rule it measured is "
                    "in the answering path through hole_reading (Phase 147: "
                    "`report deep holes` and the `hole` query kind)",
    "budget_reading_study": "the measurement of Phase 147; the rule itself is "
                            "the `hole` query kind and `report deep holes`",
    "nearest_address_study": "the measurement of Phase 148; the read itself "
                             "is the `nearest` query kind on a point no "
                             "register holds",
    "budget_guard_frozen": "the frozen path and ladder audit of Phases "
                           "147-148, asked over the whole evaluation",
    "hole_reports_l5_study": "the measurement of Phase 149; the readings "
                             "themselves are the L5 clauses of `report hole "
                             "classifier`, `ladder` and `failures`",
    "nearest_question_study": "the measurement of Phase 150; the question "
                              "it measures is put by the `nearest` query "
                              "kind at a tied head and read back by its "
                              "`given` replies",
    "ties_ladder_frozen": "the frozen path of Phases 150-151, asked over the "
                          "whole evaluation",
    "planner_ladder_study": "the measurement of Phase 151; the program it "
                            "measures is said and run by the stepwise "
                            "planner's gate",
    "l5_first_budget": "the measurement of Phase 152: L5 re-profiled at 240 "
                       "starts, which no answer reads",
    "carried_read_study": "the measurement of Phase 153; the reads it "
                          "measures are made by the stepwise gate, the "
                          "typed planner's gate and the `field` query kind",
    "adversarial_dialogue_study": "the measurement of Phase 167; the replies "
                                  "it measures are read by the conversation "
                                  "at the `nearest` query kind's tied heads",
    "resumed_dialogue_study": "the measurement of Phase 172; the replies "
                              "it measures are read by the conversation at "
                              "the `nearest` and `locate` ties",
    "stacked_dialogue_study": "the measurement of Phase 173; the replies "
                              "it measures are read by the conversation at "
                              "the `nearest` and `locate` ties, several "
                              "open at once",
    "pipeline_kit_study": "the measurement of Phase 175; the solver it "
                          "measures is `tool induce`",
    "quoted_measurements_study": "the marks of Phase 174, computed when "
                                 "asked: whether the answer censuses are "
                                 "guarded by the stored measurements their "
                                 "answers quote, and the replay instrument",
    "evidence_model_study": "the measurement of Phase 169: a census of what "
                            "every evaluation answer rests on, read through "
                            "`runtime.evidence`, not a question about one",
    "evidence_in_use_study": "the measurement of Phase 171: the command "
                             "line's `--result` reading and the "
                             "evaluation's replay gate, not a question",
    "pi_machine_study": "the measurement of Phase 166; the enclosure of pi "
                        "it measures is summed by the batch machine the "
                        "stepwise planner's gate runs",
    "stray_blind": "a census over the 23 deep holes, not a question about one",
    "citation_scope": "a measurement of the Lean corpus readings",
    "document_tree": "the retrieval line, parked at the owner's direction "
                     "(Phase 106)",
    "corpus_resample": "the declared resampling of two corpus measurements",
    "native_parity": "the measuring half of `tool native parity`, whose "
                     "operation lives in native_ledger",
    "native_words": "the measuring half of `tool native words`, whose "
                    "operation lives in golay_words",
    "now_receipt": "an audit of a supplied study's claims; its capture "
                   "takes a 24-coordinate composition no question supplies",
    "now_float_control": "the float control of the now-receipt audit (D11)",
    "operation_escalation": "measures the answering path's operations under "
                            "one refusal contract",
    "second_reading": "measures guards on those operations; the adopted one "
                      "is already in the answering path",
    "frame_operator_study": "the Archive 25 frame-operator measurement; it "
                            "is read by the study instrument, not a query",
    "frame_operators": "the Archive 25 frame-operator implementation; it is "
                       "called by the frame study instrument",
    "frame_plane": "the Archive 25 frame-plane implementation; it is called "
                   "by the frame study instrument",
    "frame_plane_study": "the Archive 25 frame-plane measurement; it is read "
                         "by the study instrument, not a query",
    "generate_not_store": "directive D19's document-backed measurement; it is "
                          "not a direct query surface",
    "improper_frame_study": "the Archive 25 improper-frame measurement; it is "
                            "read by the study instrument, not a query",
    "improper_units_study": "the Archive 25 improper-units measurement; it is "
                            "read by the study instrument, not a query",
    "kappa_anchor": "the Archive 25 calibration measurement; it is reached "
                    "through the frame study instrument",
    "leech_shells": "the Archive 25 Leech-shell measurement; it is read by "
                    "the formal study instrument",
    "lorentzian_evidence": "the Archive 25 Lorentzian evidence implementation; "
                          "it is called by its study instrument",
    "lorentzian_evidence_study": "the Archive 25 Lorentzian evidence "
                                 "measurement; it is not a direct query",
    "lorentzian_lift": "the Archive 25 Lorentzian-lift implementation; it is "
                      "called by its study instrument",
    "lorentzian_lift_study": "the Archive 25 Lorentzian-lift measurement; it "
                             "is not a direct query",
    "lorentzian_majority": "the Archive 25 majority implementation; it is "
                           "called by its study instrument",
    "lorentzian_majority_study": "the Archive 25 majority measurement; it is "
                                 "not a direct query",
    "pipeline_ask_study": "the Archive 25 separating-question measurement; it "
                          "is read by the study instrument",
    "pipeline_kit_crosscheck": "the Archive 25 Pipeline Kit cross-check; it is "
                               "not a direct query",
    "reversibility": "directive D18's document-backed measurement; it is not a "
                     "direct query surface",
    "tool_machine": "the retained tool-machine study implementation; it is "
                    "measured through the batch machine",
    "wobble_registry": "directive D17's document-backed measurement; it is not "
                       "a direct query surface",
    "typed_plans": "measures the typed planner on held-out questions",
}


def wiring_census() -> Dict[str, object]:
    """Which reasoning modules a query can reach (Phase 136).

    The import graph of the package is read from source; the closure is taken
    from every module of ``glm_universal.runtime`` -- the answering path,
    including this toolbox -- and every reasoning module outside it must be
    declared in :data:`MEASUREMENT_ONLY`.
    """
    import ast
    from pathlib import Path
    package = Path(__file__).resolve().parents[1]
    modules: Dict[str, Path] = {}
    for path in sorted(package.rglob("*.py")):
        rel = path.relative_to(package)
        if any(part in ("__pycache__", "_derived", "_data", "tests")
               for part in rel.parts):
            continue
        name = "glm_universal." + ".".join(rel.with_suffix("").parts)
        if name.endswith(".__init__"):
            name = name[: -len(".__init__")]
        modules[name] = path
    graph: Dict[str, set] = {}
    for name, path in modules.items():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        pkg = name if path.name == "__init__.py" else name.rsplit(".", 1)[0]
        targets = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                targets.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    base = pkg
                    for _ in range(node.level - 1):
                        base = base.rsplit(".", 1)[0]
                    target = base + ("." + node.module if node.module else "")
                else:
                    target = node.module or ""
                targets.add(target)
                targets.update(target + "." + alias.name
                               for alias in node.names)
        graph[name] = targets
    seen: set = set()
    stack = [n for n in modules if n.startswith("glm_universal.runtime")]
    while stack:
        name = stack.pop()
        if name in seen:
            continue
        seen.add(name)
        stack.extend(t for t in graph.get(name, ()) if t in modules
                     and t not in seen)
    reasoning = sorted(n.split(".")[-1] for n in modules
                       if n.startswith("glm_universal.reasoning.")
                       and n.count(".") == 2)
    unreached = [m for m in reasoning
                 if "glm_universal.reasoning." + m not in seen]
    return {
        "reasoning": len(reasoning),
        "reached": len(reasoning) - len(unreached),
        "declared": sorted(m for m in unreached if m in MEASUREMENT_ONLY),
        "undeclared": sorted(m for m in unreached
                             if m not in MEASUREMENT_ONLY),
        "stale_declarations": sorted(m for m in MEASUREMENT_ONLY
                                     if m not in unreached),
    }


def _induce(arg: str) -> ToolResult:
    """``IN -> OUT ; IN -> OUT ? QUERY``: the rule the demonstrations
    determine, applied to the query, or the refusal that says why not
    (Phase 175; ``reasoning/pipeline_kit.py``)."""
    from ..reasoning import pipeline_kit as pk
    ok, text, figures = pk.induce_text(arg)
    return ToolResult(ok, text, figures)


def _wiring(arg: str) -> ToolResult:
    """The wiring census: what a query can reach, and what it cannot and why."""
    c = wiring_census()
    name = arg.strip()
    if name:
        key = name.replace(" ", "_").removesuffix(".py")
        if key in MEASUREMENT_ONLY:
            return ToolResult(True, f"wiring: reasoning/{key}.py is reached by "
                              f"no query: {MEASUREMENT_ONLY[key]}",
                              {"module": key, "reached": False})
        modules = {t.module.split(".")[-1]: t.name for t in TOOLS}
        if key in modules:
            return ToolResult(True, f"wiring: reasoning/{key}.py answers "
                              f"`tool {modules[key]}`",
                              {"module": key, "reached": True})
        return ToolResult(False, f"wiring: {name!r} is not a reasoning module "
                          "declared unreached or named by a tool", {})
    ok = not c["undeclared"] and not c["stale_declarations"]
    return ToolResult(ok, f"wiring: {c['reached']} of {c['reasoning']} "
                      "reasoning modules are reached from the answering "
                      f"path; the other {len(c['declared'])} are declared "
                      "measurement-only, each with its reason"
                      + ("" if ok else f"; undeclared: {c['undeclared']}, "
                         f"stale declarations: {c['stale_declarations']}"),
                      dict(c))


TOOLS: Tuple[Tool, ...] = (
    Tool("moonshine", "reasoning.moonshine", "graded dimensions of the "
         "moonshine module and the Leech bridge", "address",
         ("RequestProject/GLM/Foundations.lean",),
         "studies/CONSTRUCTION_LADDER_STUDY.md", _moonshine),
    Tool("llvq", "reasoning.llvq", "Leech shells classified without a "
         "codebook", "address", ("RequestProject/GLM/Foundations.lean",
                                 "RequestProject/GLM/LLVQTable.lean"),
         "studies/LLVQ_TABLE_STUDY.md", _llvq),
    Tool("pcgs", "reasoning.pcgs", "proof-carrying generative systems and "
         "their admission", "derive", ("RequestProject/GLM/PCGS.lean",),
         "studies/PCGS_STUDY.md", _pcgs),
    Tool("salvage", "reasoning.salvage", "the first eleven archive results, "
         "recomputed", "derive", ("RequestProject/GLM/Lightspeed.lean",
                                  "RequestProject/GLM/GolayWeightEnum.lean"),
         "studies/SOURCE_SALVAGE_AUDIT.md", _salvage),
    Tool("salvage second", "reasoning.salvage_second", "eight more archive "
         "results, recomputed", "derive",
         ("RequestProject/GLM/Cube/Surface.lean",
          "RequestProject/GLM/GrayJump.lean"),
         "studies/SOURCE_SALVAGE_SECOND_PASS.md", _salvage_second),
    Tool("deep dive", "reasoning.deep_dive", "balanced octads against "
         "chance, and relaxation descent", "derive",
         ("RequestProject/GLM/TriadChance.lean",
          "RequestProject/GLM/Relaxation.lean"),
         "studies/ARCHIVE_DEEP_DIVE_STUDY.md", _deep_dive),
    Tool("tie break", "reasoning.tie_break", "the tie class of one Lean "
         "declaration's address", "address",
         ("RequestProject/GLM/TieBreak.lean",), "studies/TIE_BREAK_STUDY.md",
         _tie_break, takes="a Lean declaration name"),
    Tool("stability", "reasoning.stability", "how far one Lean "
         "declaration's address may move", "refusal",
         ("RequestProject/GLM/Stability.lean",), "studies/TIE_BREAK_STUDY.md",
         _stability, takes="a Lean declaration name"),
    Tool("native parity", "reasoning.native_parity", "where a standard method "
         "ties or narrowly beats a native one, and the native refinement",
         "address", ("RequestProject/GLM/NativeParity.lean",),
         "studies/NATIVE_PARITY_STUDY.md", _native_parity),
    Tool("native words", "reasoning.native_words", "a text's tokens read as "
         "Golay words: the parts' letter words the native word ranking uses",
         "address", ("RequestProject/GLM/NativeWords.lean",),
         "studies/NATIVE_WORDS_STUDY.md", _native_words,
         takes="a fragment of text"),
    Tool("law register", "reasoning.law_register", "the 65 retained UBP laws "
         "re-graded: structural laws with their Lean theorems, numeric laws "
         "through the look-elsewhere test", "refusal",
         ("RequestProject/GLM/LawRegister.lean",),
         "studies/LAW_REGISTER_STUDY.md", _law_register,
         takes="a law id, or nothing for the census"),
    Tool("ladder", "reasoning.ops_ladder", "the operations ladder: 97 terms "
         "each built from lower ones, the relation between two computed from "
         "their closures, the projection onto the Geometric-Cybernetic ladder "
         "and the cross-overs", "derive",
         ("RequestProject/GLM/OperationsLadder.lean",),
         "studies/OPERATIONS_LADDER_STUDY.md", _ladder,
         takes="a term, 'A and B', or nothing for the census"),
    Tool("machine", "reasoning.batch_speech", "GLM-BAT, an old-style batch "
         "machine learnt as a language: a question about a program, answered "
         "from a run with a certificate, or refused by name", "derive",
         ("RequestProject/GLM/OperationsLadder.lean",),
         "studies/OPERATIONS_LADDER_STUDY.md", _machine,
         takes="QUESTION :: PROGRAM"),
    Tool("continued fraction", "reasoning.substrate_cognition", "certified "
         "continued-fraction terms of a written real: a term is emitted only "
         "when both ends of an interval around the value agree on it",
         "derive", ("RequestProject/GLM/CertifiedStreams.lean",),
         "studies/CONNECTED_MACHINE_TWO_STUDY.md", _continued_fraction,
         takes="a real such as sqrt(2), pi or (1+sqrt(5))/2 [terms N]"),
    Tool("mobius", "reasoning.substrate_cognition", "the continued fraction "
         "of (a X + b)/(c X + d), streamed from the terms of X by Gosper's "
         "rule and checked against the direct expansion", "derive",
         ("RequestProject/GLM/CertifiedStreams.lean",),
         "studies/CONNECTED_MACHINE_TWO_STUDY.md", _mobius,
         takes="a b c d of X [terms N]"),
    Tool("bind", "reasoning.role_binding", "a typed relation bound into one "
         "24-bit word, and the filler read back from it or refused by name",
         "address, refusal", ("RequestProject/GLM/RoleBinding.lean",),
         "studies/CONVERSATION_STUDY.md", _bind,
         takes="ROLE A B in DOMAIN"),
    Tool("gates", "reasoning.substrate_cognition", "the least number of "
         "reversible Toffoli/Fredkin moves between two 24-bit words, or the "
         "block that makes the target unreachable", "derive, refusal",
         ("RequestProject/GLM/SubstrateCognition.lean",),
         "studies/SUBSTRATE_NATIVE_COGNITION_STUDY.md", _gates,
         takes="SOURCE to TARGET"),
    Tool("tag length", "reasoning.shortest_tag", "how many bits a sender tag "
         "needs to give every octad a given tag weight, from the proved floors",
         "derive", ("RequestProject/GLM/ShortestTag.lean",),
         "studies/SHORTEST_TAG_STUDY.md", _tag_length,
         takes="the octad tag weight D"),
    Tool("convergent", "reasoning.rational_approx", "the K-th convergent of "
         "the continued fraction of a written real, as a fraction in lowest "
         "terms", "derive", ("RequestProject/GLM/ToolValues.lean",
                             "RequestProject/GLM/CertifiedStreams.lean"),
         "studies/TOOL_VALUES_STUDY.md", _convergent, takes="K of X"),
    Tool("best approximation", "reasoning.rational_approx", "the fraction "
         "nearest a written real among those with denominator at most N, "
         "for any N, each answer carrying a Farey certificate", "derive",
         ("RequestProject/GLM/ToolValues.lean",
          "RequestProject/GLM/NearestFraction.lean"),
         "studies/TOOL_VERDICTS_STUDY.md", _best_approximation,
         takes="X denominator N"),
    Tool("induce", "reasoning.pipeline_kit", "a rule induced from "
         "demonstration pairs of 0/1 grids or bit strings and applied to a "
         "query: every operator hypothesis that fits all the pairs is kept, "
         "and the query is answered only when they all agree (the owner's "
         "pipeline kit)", "derive, refusal",
         ("RequestProject/GLM/PipelineInduction.lean",
          "RequestProject/GLM/PipelineKit/Permutation.lean"),
         "studies/PIPELINE_KIT_STUDY.md", _induce,
         takes="IN -> OUT ; IN -> OUT ? QUERY"),
    Tool("wiring", "runtime.toolbox", "which reasoning modules a query can "
         "reach, and the declared reason for each one it cannot", "address",
         ("RequestProject/GLM/ConnectedMachine.lean",),
         "studies/CONNECTED_MACHINE_TWO_STUDY.md", _wiring,
         takes="a module name, or nothing for the census"),
)


#: English openings a tool answers when every surface has refused (Phase 136).
#: Each is ``(pattern, template)``: a full-match pattern over the question
#: with its courtesy and trailing punctuation stripped, and the ``tool ...``
#: text it stands for, with ``{1}``, ``{2}``, ... the pattern's groups.
#: The router consults these only after the planner, the grammar and the
#: stepwise planner have all refused, and keeps the tool's verdict only if it
#: answers -- so no answer the machine gave before is changed
#: (``GLM.ConnectedMachine.route_cons_none``), and a refusal stays the
#: refusal it was unless a tool can do better.
TOOL_PHRASES: Tuple[Tuple[str, str], ...] = (
    (r"(?:what is |what's |give me |give |compute )?(?:the )?first (\d+) "
     r"terms of the continued fraction (?:expansion )?of (.+)",
     "tool continued fraction {2} terms {1}"),
    (r"(?:what is |what's |give me |give |compute )?(?:the )?continued "
     r"fraction (?:expansion )?of (.+)", "tool continued fraction {1}"),
    (r"expand (.+?) (?:as|into) a continued fraction",
     "tool continued fraction {1}"),
    (r"how many (?:tag )?bits does a (?:sender )?tag need for (?:an )?"
     r"(?:octad )?(?:tag )?(?:weight|distance) (?:of )?(\d+)",
     "tool tag length {1}"),
    (r"how many tag bits (?:are needed|does it take|are required) for "
     r"(?:an )?(?:octad )?(?:tag )?(?:weight|distance) (?:of )?(\d+)",
     "tool tag length {1}"),
    (r"(?:what is )?the shortest tag for (?:octad )?(?:tag )?"
     r"(?:weight|distance) (\d+)", "tool tag length {1}"),
    (r"can (\S+) reach (\S+)(?: by (?:reversible )?(?:gates|gate moves))?",
     "tool gates {1} to {2}"),
    (r"how many (?:reversible )?gate moves (?:take|from) (\S+) to (\S+)",
     "tool gates {1} to {2}"),
    (r"bind (\S+ \S+ \S+ in \S+)", "tool bind {1}"),
    (r"(?:what (?:is|was) the fate of|what became of|what happened to) "
     r"(law_\w+)", "tool law register {1}"),
    (r"(?:induce|infer|find) the rule (?:from|of|in) (.+\?.+)",
     "tool induce {1}"),
    (r"which reasoning modules (?:can a query reach|are reached|are wired)",
     "tool wiring"),
)


def phrase_tool(text: str) -> Optional[str]:
    """The ``tool ...`` text an English opening stands for, or ``None``."""
    import re as _re
    t = text.strip().rstrip("?.! ").strip()
    for courtesy in ("please ", "could you ", "can you tell me "):
        if t.lower().startswith(courtesy):
            t = t[len(courtesy):]
    for pattern, template in TOOL_PHRASES:
        m = _re.fullmatch(pattern, t, _re.IGNORECASE)
        if m:
            out = template
            for i, g in enumerate(m.groups(), 1):
                out = out.replace("{" + str(i) + "}", g.strip())
            return out
    return None


def tool_named(name: str) -> Optional[Tool]:
    for t in TOOLS:
        if t.name == name:
            return t
    return None


def reads_tool(text: str) -> bool:
    """Whether the toolbox reads ``text``."""
    t = text.strip().lower()
    return t == "tools" or t.startswith("tool ") or t == "tool"


def catalogue_text() -> str:
    lines = ["surfaces, in the order the router tries them:"]
    for i, s in enumerate(SURFACES, 1):
        lines.append(f"  {i}. {s.name}: reads {s.reads}; {s.reached_by}")
    lines.append("tools (tool <name> [argument]):")
    for t in TOOLS:
        arg = f" <{t.takes}>" if t.takes else ""
        lines.append(f"  tool {t.name}{arg}: {t.summary} "
                     f"[{', '.join(x.split('/')[-1] for x in t.lean)}; "
                     f"{t.study.split('/')[-1]}]")
    return "\n".join(lines)


def run_tool(text: str) -> ToolResult:
    """Run ``tool <name> [argument]``; ``tools`` lists the catalogue."""
    t = text.strip()
    if t.lower() in ("tools", "tool"):
        return ToolResult(True, catalogue_text(),
                          {"surfaces": len(SURFACES), "tools": len(TOOLS)})
    rest = t[len("tool"):].strip()
    low = rest.lower()
    for tool in sorted(TOOLS, key=lambda x: -len(x.name)):
        if low == tool.name or low.startswith(tool.name + " "):
            return tool.run(rest[len(tool.name):].strip())
    return ToolResult(False, f"refused: no tool named {rest!r}; the tools "
                      f"are {', '.join(x.name for x in TOOLS)}")
