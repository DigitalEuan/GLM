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
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Mapping, Optional, Tuple

__all__ = ["Surface", "Tool", "ToolResult", "SURFACES", "TOOLS",
           "tool_named", "run_tool", "reads_tool", "catalogue_text"]


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
    Surface("engineering", "a question one of the eight engineering frames "
            "reads (derive, across wheels, wheel, check, Smith, analogy, "
            "resonance, delta-sigma)", "GLM.py --ask TEXT, or --eng -q TEXT",
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
             "RequestProject/GLM/StepwiseFrames.lean"),
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
                      f"catalogued without enumeration ({shells}); kissing "
                      f"number {r['kissing_number']}",
                      {"kissing_number": r["kissing_number"],
                       "shells": r["n_shells_catalogued"]})


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
    from ..reasoning import native_parity as npar
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
    from ..reasoning import native_words as nwd
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
)


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
