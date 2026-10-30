"""``glm_universal.reasoning.theorem_wheel`` -- the Rule 30 theorem wheel and the discussion
pipeline (Rule 30 study, Round 12).

What a theorem wheel is here
----------------------------
A *formula wheel* (``engineering/wheels.py``) is a declared set of monomial axioms over named
quantities, and a formula *follows* when its relation vector lies in their span; the
coefficients are the certificate.  A **theorem wheel** is the same idea one level up:

* the *quantities* are named **statements** about Rule 30 (``P1`` = Problem 1, ``SeedAPBalanced``,
  ``RightDiagonalsPeriodic``, ...), each with its status for the seed: ``FORMAL`` (a Lean theorem),
  ``CERT`` (a machine-checked finite computation) or ``OPEN``;
* the *axioms* are the **spokes**: implications and equivalences that are Lean theorems of the
  package ``RequestProject/GLM/Rule30`` (namespace ``GLM.Rule30``), each carrying its theorem
  name and its **axiom footprint**, the Lean axioms it rests on (the hub of the wheel: every spoke
  rests on ``propext``, ``Classical.choice``, ``Quot.sound``; the finite certificates add
  ``Lean.ofReduceBool``, ``Lean.trustCompiler``, the trust in the compiled evaluator);
* a statement **follows** from given statements when forward chaining over the spokes reaches it;
  the chain of theorem names is the certificate;
* the **negative controls** are proved *non*-implications (a Lean counterexample: the premise
  holds for some sequence or row and the conclusion fails).  They play the part that dimensional
  consistency plays for formula wheels: a route that a negative control blocks is not offered.

The discussion pipeline
-----------------------
``tool discuss <question>`` reads a question about the dynamics of Rule 30 in this language and
answers in five stages, broad to narrow:

1. **BROAD** -- which target the question is about, and how many spokes and lenses reach it;
2. **LENSES** -- every lens (way of reading the column) with its relation to the target:
   ``=`` restatement (equivalent), ``<=`` sufficient, ``part`` a proved partial result, ``x`` a
   blocked route (negative control);
3. **NARROW** -- restatements are dropped (proving one is the same task), blocked routes are
   dropped, and the remaining sufficient open statements are ordered weakest first (``A`` is
   weaker than ``B`` when the wheel derives ``B => A``); the *arrow* of the run points from the
   strong end to the weak end, towards the target;
4. **EVIDENCE** -- the finite readings on file for the narrowed statements (``CERT`` / ``EMP``);
5. **LIMITS** -- the gap: whether any chain reaches the target from the ``FORMAL`` facts about the
   seed (none does), the nearest proved facts, and what the wheel cannot do.

Everything is retrieval and chaining over declared spokes; the module never invents a spoke, and
a question outside its targets is refused with the list of targets.  Exact; no floats.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Set, Tuple

__all__ = ["Statement", "Spoke", "NonImplication", "STATEMENTS", "SPOKES", "NON_IMPLICATIONS",
           "AXIOM_FOOTPRINT", "closure", "derives", "derivation", "sufficient_open",
           "weakest_first", "equivalents", "gap", "chains", "strictness", "discuss",
           "discuss_text", "theorem_text", "TARGET_WORDS"]

LEAN = "RequestProject/GLM/Rule30"

# ---------------------------------------------------------------------------------------------
# 1.  STATEMENTS (the quantities of the wheel)
# ---------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Statement:
    name: str
    text: str
    status: str            # FORMAL | CERT | OPEN  (for the seed's centre column unless stated)
    lens: str
    partial_of: Tuple[str, ...] = ()     # targets this proved fact is a partial result towards


S = Statement
STATEMENTS: Dict[str, Statement] = {s.name: s for s in (
    # the three prize questions
    S("P1", "the centre column is not eventually periodic (Problem 1)", "OPEN", "target"),
    S("P2", "black cells have frequency 1/2 in the centre column (Problem 2)", "OPEN", "target"),
    S("P3", "computing a(n) needs time growing with n on a uniform machine (Problem 3)", "OPEN",
      "target"),
    # restatements
    S("SublinearWobble", "the wobble is sub-linear: D(N)/N -> 0", "OPEN", "continuous wobble"),
    S("TotalEchoSmall", "the total echo is o(N^2) (radar identity D(N)^2 = N + 2 * echo)", "OPEN",
      "echo (radar)"),
    S("FSObserversFail", "every finite-state observer errs infinitely often", "OPEN",
      "finite-state observer"),
    S("LagMismatchAll", "for every lag p >= 1 there are arbitrarily late mismatches "
      "a(t+p) != a(t)", "OPEN", "echo (radar)"),
    S("StrobesNonconstant", "for every stride p >= 1 some phase of the strobe a(p t + r) keeps "
      "changing colour", "OPEN", "strobe (clock)"),
    # sufficient hypotheses
    S("SeedFSTypical", "every finite-state observer is right with frequency exactly 1/2",
      "OPEN", "finite-state observer"),
    S("SeedAPBalanced", "every arithmetic progression a(p t + r) has frequency 1/2", "OPEN",
      "strobe (clock)"),
    S("SqrtWobble", "|D(N)| <= C sqrt(N) eventually, for some C", "OPEN", "continuous wobble"),
    S("NoResonance", "no lag p >= 1 has a full echo resonance echo(N, p)/N -> 1", "OPEN",
      "echo (radar)"),
    S("OtherColumnPeriodic", "some column c != 0 of the seed pattern is eventually periodic",
      "OPEN", "off-centre observer"),
    # proved facts about the seed (partial results)
    S("Stride1Nonconstant", "the centre column is not eventually constant (stride 1, period 1)",
      "FORMAL", "strobe (clock)", ("P1",)),
    S("AtMostOnePeriodicColumn", "at most one column of the seed pattern is eventually periodic",
      "FORMAL", "off-centre observer", ("P1",)),
    S("OffCentrePair", "for c != 0, columns 0 and c are not both eventually periodic", "FORMAL",
      "off-centre observer", ("P1",)),
    S("RightDiagonalsPeriodic", "every right diagonal is periodic (power-of-two periods)",
      "FORMAL", "read angle (diagonals)", ("P1", "P2")),
    S("LeftDiagonalsPeriodic", "every left diagonal is eventually periodic (power-of-two "
      "periods)", "FORMAL", "read angle (diagonals)", ("P1",)),
    S("InfManyBalancedRdiag", "infinitely many right diagonals have bounded wobble and "
      "frequency exactly 1/2", "FORMAL", "read angle (diagonals)", ("P2",)),
    S("DegreeFormula", "the ANF degree of a(n)(c) is exactly 2n - 1", "FORMAL",
      "algebraic (ANF)", ("P3",)),
    S("WholeCone", "the n-step map depends on all 2n + 1 cells of the light cone", "FORMAL",
      "algebraic (ANF)", ("P3",)),
    S("AlmostEveryRowTypical", "for almost every initial row every column is finite-state "
      "typical", "FORMAL", "measure", ("P1", "P2")),
    S("Wobble1e6", "D(10^6) = 1536 and D(N)^2/N <= 175561/24979 for N <= 10^6", "CERT",
      "continuous wobble", ("P2",)),
    S("StrobeTable1e6", "the phase wobbles for strides 2..6 to 10^6 (largest D_{3,1} = 1583)",
      "CERT", "strobe (clock)", ("P1", "P2")),
    S("ArrowNoFlip1e6", "D(195112) = 0 and D(N) > 0 for 195112 < N <= 10^6", "CERT", "arrow",
      ("P2",)),
)}

# ---------------------------------------------------------------------------------------------
# 2.  SPOKES (proved implications) and NEGATIVE CONTROLS (proved non-implications)
# ---------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Spoke:
    premises: Tuple[str, ...]
    conclusion: str
    lean: str
    file: str
    iff: bool = False


SPOKES: Tuple[Spoke, ...] = (
    Spoke(("SeedFSTypical",), "P1", "problems_one_and_two_of_seed_fsTypical", "FiniteState.lean"),
    Spoke(("SeedFSTypical",), "P2", "problems_one_and_two_of_seed_fsTypical", "FiniteState.lean"),
    Spoke(("SeedFSTypical",), "SeedAPBalanced", "apBalanced_of_fsTypical", "WobbleLenses.lean"),
    Spoke(("SeedAPBalanced",), "P1", "not_eventuallyPeriodic_of_apBalanced", "WobbleLenses.lean"),
    Spoke(("SeedAPBalanced",), "P2", "hasFrequencyHalf_of_apBalanced", "WobbleLenses.lean"),
    Spoke(("SqrtWobble",), "P2", "problem2_of_sqrt_bound", "Prizes.lean"),
    Spoke(("P2",), "SublinearWobble", "problem2_iff_wobble", "Prizes.lean", iff=True),
    Spoke(("P2",), "TotalEchoSmall", "problem2_iff_totalEcho", "Spectral.lean", iff=True),
    Spoke(("P1",), "FSObserversFail", "problem1_iff_fsObservers_fail", "FiniteState.lean",
          iff=True),
    Spoke(("P1",), "LagMismatchAll", "problem1_iff_lag_mismatch", "Spectral.lean", iff=True),
    Spoke(("P1",), "StrobesNonconstant", "problem1_iff_strobes", "WobbleLenses.lean", iff=True),
    Spoke(("NoResonance",), "P1", "problem1_of_no_resonance", "Spectral.lean"),
    Spoke(("OtherColumnPeriodic",), "P1", "problem1_of_other_periodic_column",
          "OnePeriodicColumn.lean"),
)


@dataclass(frozen=True)
class NonImplication:
    premise: str
    conclusion: str
    lean: str
    why: str


NON_IMPLICATIONS: Tuple[NonImplication, ...] = (
    NonImplication("SeedAPBalanced", "SeedFSTypical", "exists_apBalanced_not_fsTypical",
                   "a doubled typical sequence is AP-balanced, yet the observer 'repeat the last "
                   "bit at odd times' is right 3/4 of the time"),
    NonImplication("DegreeFormula", "P1", "map_properties_cannot_decide_periodicity",
                   "every property of the n-step maps holds for the all-white row too, whose "
                   "centre column is periodic"),
    NonImplication("RightEdgeWhite", "P2", "exists_row_with_biased_column",
                   "a right-white row whose centre column has frequency 1/3"),
    NonImplication("RightDiagonalsPeriodic", "AllRdiagBalanced", "rdiag_five_not_half",
                   "right diagonal 5 has frequency 3/8"),
    NonImplication("FinitePrefix", "P1", "no_finite_certificate_problem1",
                   "every finite prefix extends to an eventually periodic sequence"),
    NonImplication("FinitePrefix", "P2", "no_finite_certificate_problem2",
                   "every finite prefix extends to a sequence with frequency != 1/2"),
    NonImplication("ArrowPersistent", "NotP2", "exists_balanced_persistent_arrow",
                   "1,1,0,1,0,... has frequency 1/2 and D(N) > 0 for every N >= 1"),
    NonImplication("AnySequence", "SqrtWobble", "not_forall_sqrt_bound",
                   "a sqrt bound is a property of particular sequences, not of all of them"),
    NonImplication("RightEdgeWhite", "P1", "exists_row_with_periodic_column",
                   "a right-white row whose centre column is periodic"),
)

#: Lean axiom footprint of each spoke / fact / control (``#print axioms``, Round 12;
#: ``RequestProject/GLM/Rule30/scripts/theorem_wheel_axioms.lean``).
_STD = ("propext", "Classical.choice", "Quot.sound")
_CMP = ("propext", "Classical.choice", "Lean.ofReduceBool", "Lean.trustCompiler", "Quot.sound")
AXIOM_FOOTPRINT: Dict[str, Tuple[str, ...]] = {n: _STD for n in (
    "problems_one_and_two_of_seed_fsTypical", "apBalanced_of_fsTypical",
    "not_eventuallyPeriodic_of_apBalanced", "hasFrequencyHalf_of_apBalanced",
    "problem2_of_sqrt_bound", "problem2_iff_wobble", "problem2_iff_totalEcho",
    "problem1_iff_fsObservers_fail", "problem1_iff_lag_mismatch", "problem1_iff_strobes",
    "problem1_of_no_resonance", "problem1_of_other_periodic_column",
    "centerCol_not_eventually_constant", "seed_at_most_one_periodic_column",
    "offCentre_pair_problem1", "rdiag_periodic", "ldiag_eventually_periodic",
    "infinitely_many_balanced_rdiag", "topMonomialConjecture_holds", "wholeConeDependence_holds",
    "ae_fsTypical", "exists_apBalanced_not_fsTypical", "exists_row_with_biased_column",
    "rdiag_five_not_half", "no_finite_certificate_problem1", "no_finite_certificate_problem2",
    "exists_balanced_persistent_arrow", "not_forall_sqrt_bound", "exists_row_with_periodic_column",
    "column_one_separates_mirror")}
AXIOM_FOOTPRINT.update({n: _CMP for n in ("wobble_1e6", "wobble_sq_ratio_cert",
                                           "arrow_last_flip_1e6", "strobe_wobble_table",
                                           "sqrt_bound_fails_below")})
AXIOM_FOOTPRINT["map_properties_cannot_decide_periodicity"] = ("propext",)

#: The Lean theorem behind each proved fact.
FACT_LEAN: Dict[str, str] = {
    "Stride1Nonconstant": "centerCol_not_eventually_constant",
    "AtMostOnePeriodicColumn": "seed_at_most_one_periodic_column",
    "OffCentrePair": "offCentre_pair_problem1",
    "RightDiagonalsPeriodic": "rdiag_periodic",
    "LeftDiagonalsPeriodic": "ldiag_eventually_periodic",
    "InfManyBalancedRdiag": "infinitely_many_balanced_rdiag",
    "DegreeFormula": "topMonomialConjecture_holds",
    "WholeCone": "wholeConeDependence_holds",
    "AlmostEveryRowTypical": "ae_fsTypical",
    "Wobble1e6": "wobble_1e6, wobble_sq_ratio_cert",
    "StrobeTable1e6": "strobe_wobble_table",
    "ArrowNoFlip1e6": "arrow_last_flip_1e6",
}

#: Finite readings on file (EMP = exact computation outside Lean; CERT = Lean certificate).
EVIDENCE: Dict[str, Tuple[str, ...]] = {
    "SeedAPBalanced": (
        "CERT strobe_wobble_table: 20 phase wobbles for p = 2..6 to 10^6; largest D_{3,1} = 1583 "
        "(z = 2.7 for a fair coin)",
        "EMP r12_lens_survey: 135 phases p <= 16 to 10^7, max |z| = 2.68 (control coin 2.60); "
        "D_{3,1} falls back to z = 1.8 at 10^7: a fluctuation, not a drift"),
    "SeedFSTypical": (
        "EMP r12_lens_survey: block counts k = 4, 8, 12 to 10^7 give chi2/dof 0.92, 0.89, 0.98; "
        "1023 Walsh window characters max |z| = 3.48 (control 2.94)",),
    "SqrtWobble": (
        "CERT wobble_sq_ratio_cert: D(N)^2/N <= 7.03 for N <= 10^6; sqrt_bound_fails_below: no "
        "C with C^2 < 7.03 works", "EMP: D(10^7) = 4440 (z = 1.40)"),
    "NoResonance": ("EMP r12_lens_survey: echo at lags 1..64 to 10^7, max |z| = 2.58",),
    "P2": ("CERT wobble_1e6: D(10^6) = 1536", "CERT arrow_last_flip_1e6: the arrow does not "
           "flip on (195112, 10^6]; arcsine law: about 9% for a fair coin, so not a signal"),
}

TARGET_WORDS: Tuple[Tuple[str, str], ...] = (
    (r"problem ?1|question ?1|periodic|period|repeat|cycle", "P1"),
    (r"problem ?2|question ?2|frequen|balance|half|equally|normal|wobble|bias", "P2"),
    (r"problem ?3|question ?3|complexit|comput|cost|shortcut|predict|time", "P3"),
)

# ---------------------------------------------------------------------------------------------
# 3.  CHAINING
# ---------------------------------------------------------------------------------------------


def _edges() -> List[Tuple[Tuple[str, ...], str, str]]:
    out = []
    for s in SPOKES:
        out.append((s.premises, s.conclusion, s.lean))
        if s.iff:
            out.append(((s.conclusion,), s.premises[0], s.lean))
    return out


def closure(givens: Sequence[str]) -> Dict[str, Tuple[str, ...]]:
    """Every statement that follows from ``givens``, with its certificate (theorem chain)."""
    known: Dict[str, Tuple[str, ...]] = {g: () for g in givens}
    changed = True
    while changed:
        changed = False
        for prem, concl, lean in _edges():
            if concl not in known and all(p in known for p in prem):
                cert: Tuple[str, ...] = ()
                for p in prem:
                    cert += known[p]
                known[concl] = cert + (lean,)
                changed = True
    return known


def derives(a: str, b: str) -> bool:
    return b in closure([a])


def derivation(a: str, b: str) -> Optional[Tuple[str, ...]]:
    return closure([a]).get(b)


def equivalents(target: str) -> List[str]:
    return sorted(n for n in STATEMENTS if n != target and derives(n, target)
                  and derives(target, n))


def sufficient_open(target: str) -> List[str]:
    """Open statements that derive ``target`` and are not equivalent to it."""
    return sorted(n for n, s in STATEMENTS.items()
                  if n != target and s.status == "OPEN" and s.lens != "target"
                  and derives(n, target) and not derives(target, n))


def weakest_first(names: Sequence[str]) -> List[Tuple[str, List[str]]]:
    """Order sufficient statements: each with the list of others that it is implied by
    (stronger ones).  The weakest come first."""
    rows = []
    for n in names:
        stronger = [m for m in names if m != n and derives(m, n) and not derives(n, m)]
        rows.append((n, stronger))
    rows.sort(key=lambda r: (-len(r[1]), r[0]))
    return rows


def gap(target: str) -> Dict[str, object]:
    facts = [n for n, s in STATEMENTS.items() if s.status in ("FORMAL", "CERT")]
    reached = closure(facts)
    nearest = [n for n in facts if target in STATEMENTS[n].partial_of]
    return {"closed": target in reached, "facts": facts, "nearest": nearest}


def _blocked(target: str) -> List[NonImplication]:
    """Negative controls that block a route to ``target`` (or to a restatement of it)."""
    rel = {target} | set(equivalents(target)) | {"Not" + target}
    if target == "P2":
        rel |= {"SqrtWobble", "AllRdiagBalanced"}
    return [ni for ni in NON_IMPLICATIONS if ni.conclusion in rel]


def chains(names: Sequence[str], target: str) -> List[List[str]]:
    """Maximal derivation chains among the sufficient statements, each ending at ``target``:
    ``A -> B`` appears only when the wheel derives ``A => B``."""
    succ = {n: [m for m in names if m != n and derives(n, m) and not derives(m, n)]
            for n in names}
    starts = [n for n in names if not any(n in succ[m] for m in names)]
    out: List[List[str]] = []

    def walk(path: List[str]) -> None:
        nxt = [m for m in succ[path[-1]] if m not in path]
        if not nxt:
            out.append(path + [target])
        for m in nxt:
            walk(path + [m])
    for s0 in starts:
        walk([s0])
    return out


def strictness(a: str, b: str) -> Optional[NonImplication]:
    """A negative control showing ``a =/=> b`` (so ``a`` is strictly weaker than ``b``)."""
    for ni in NON_IMPLICATIONS:
        if ni.premise == a and ni.conclusion == b:
            return ni
    return None

# ---------------------------------------------------------------------------------------------
# 4.  THE DISCUSSION PIPELINE
# ---------------------------------------------------------------------------------------------


def _target_of(question: str) -> Optional[str]:
    q = question.lower()
    for pat, t in TARGET_WORDS:
        if re.search(pat, q):
            return t
    return None


def discuss(question: str) -> Optional[Dict[str, object]]:
    target = _target_of(question)
    if target is None:
        return None
    eq = equivalents(target)
    suff = sufficient_open(target)
    order = weakest_first(suff)
    g = gap(target)
    lenses: Dict[str, List[str]] = {}
    for n in eq:
        lenses.setdefault(STATEMENTS[n].lens, []).append(f"=  {n}: {STATEMENTS[n].text} "
                                                         f"[{derivation(target, n)[-1]}]")
    for n in suff:
        lenses.setdefault(STATEMENTS[n].lens, []).append(
            f"<= {n}: {STATEMENTS[n].text} [{' ; '.join(derivation(n, target))}]")
    for n in g["nearest"]:
        lenses.setdefault(STATEMENTS[n].lens, []).append(
            f"part {n}: {STATEMENTS[n].text} [{STATEMENTS[n].status}: {FACT_LEAN[n]}]")
    blocked = _blocked(target)
    for ni in blocked:
        lens = STATEMENTS[ni.premise].lens if ni.premise in STATEMENTS else "boundary / prefix"
        lenses.setdefault(lens, []).append(f"x  {ni.premise} does not give {ni.conclusion}: "
                                           f"{ni.why} [{ni.lean}]")
    return {"target": target, "equivalents": eq, "sufficient": suff, "order": order,
            "gap": g, "lenses": lenses, "blocked": blocked}


def _fmt_order(order: List[Tuple[str, List[str]]]) -> List[str]:
    lines = []
    for n, stronger in order:
        tail = f" (weaker than {', '.join(stronger)})" if stronger else ""
        lines.append(f"  {n}{tail}: {STATEMENTS[n].text}")
    return lines


def discuss_text(question: str) -> Tuple[bool, str, Dict[str, object]]:
    if not question.strip():
        return False, "refused: ask a question about Problem 1, 2 or 3 of Rule 30", {
            "status": "empty"}
    d = discuss(question)
    if d is None:
        return False, ("refused: the question names none of the wheel's targets; targets: "
                       "Problem 1 (periodic, period, repeat), Problem 2 (frequency, balance, "
                       "wobble, bias), Problem 3 (complexity, cost, predict)"), {
            "status": "unread"}
    t = d["target"]
    out: List[str] = []
    n_spokes = sum(len(v) for v in d["lenses"].values())
    out.append(f"STAGE 1 BROAD     target {t}: {STATEMENTS[t].text} [OPEN]; {n_spokes} readings "
               f"through {len(d['lenses'])} lenses")
    out.append("STAGE 2 LENSES    (= restatement, <= sufficient, part = proved partial result, "
               "x = blocked by a negative control)")
    for lens in sorted(d["lenses"]):
        out.append(f"  [{lens}]")
        for line in d["lenses"][lens]:
            out.append(f"    {line}")
    out.append("STAGE 3 NARROW    restatements dropped (proving one is the same task); blocked "
               "routes dropped")
    if d["order"]:
        out.append("  sufficient open hypotheses, weakest first:")
        out.extend(_fmt_order(d["order"]))
        for n, stronger in d["order"]:
            for m in stronger:
                ni = strictness(n, m)
                if ni is not None:
                    out.append(f"  strictly weaker: {n} =/=> {m} [{ni.lean}: {ni.why}]")
        for ch in chains([n for n, _ in d["order"]], t):
            label = "ARROW " if len(ch) > 2 else "route "
            out.append(f"  {label} {' -> '.join(ch)}")
        out.append("  (each -> is a proved implication; the arrow runs from the strong end "
                   "towards the target)")
    else:
        out.append("  no sufficient open hypothesis on the wheel: only restatements and partial "
                   "results")
    out.append("STAGE 4 EVIDENCE")
    ev = False
    for n in [x for x, _ in d["order"]] + [t]:
        for e in EVIDENCE.get(n, ()):
            out.append(f"  {n}: {e}")
            ev = True
    if not ev:
        out.append("  none on file")
    g = d["gap"]
    out.append("STAGE 5 LIMITS")
    out.append(f"  gap: the {len(g['facts'])} proved facts about the seed "
               f"{'DO' if g['closed'] else 'do NOT'} reach {t} through the spokes")
    if g["nearest"]:
        out.append(f"  nearest proved facts: {', '.join(g['nearest'])}")
    out.append("  the wheel chains declared spokes only; it cannot invent a spoke, and finite "
               "evidence cannot close an infinite claim (no_finite_certificate_problem1/2)")
    if d["order"]:
        w = d["order"][0][0]
        out.append(f"NEXT    prove {w} for the seed, or a new spoke from a proved seed fact into "
                   f"{w}")
    return True, "\n".join(out), {"status": "discussed", "target": t,
                                  "weakest": d["order"][0][0] if d["order"] else None}


def theorem_text(arg: str) -> Tuple[bool, str, Dict[str, object]]:
    """``tool theorem``: the wheel (no argument), ``derive A => B``, ``axioms``, ``lenses``."""
    a = arg.strip()
    low = a.lower()
    if low in ("", "wheel", "overview"):
        nf = sum(1 for s in STATEMENTS.values() if s.status in ("FORMAL", "CERT"))
        no = sum(1 for s in STATEMENTS.values() if s.status == "OPEN")
        lines = [f"THEOREM WHEEL  {len(STATEMENTS)} statements ({nf} proved facts, {no} open), "
                 f"{len(SPOKES)} spokes, {len(NON_IMPLICATIONS)} negative controls"]
        for s in SPOKES:
            arrow = "<=>" if s.iff else "=>"
            lines.append(f"  {' & '.join(s.premises)} {arrow} {s.conclusion}   "
                         f"[{s.lean}, {s.file}]")
        for ni in NON_IMPLICATIONS:
            lines.append(f"  {ni.premise} =/=> {ni.conclusion}   [{ni.lean}]")
        return True, "\n".join(lines), {"status": "wheel"}
    if low == "axioms":
        groups: Dict[Tuple[str, ...], List[str]] = {}
        for k, v in AXIOM_FOOTPRINT.items():
            groups.setdefault(v, []).append(k)
        lines = ["AXIOM HUB  (Lean #print axioms for every spoke, fact and control)"]
        for v, ks in sorted(groups.items(), key=lambda kv: -len(kv[1])):
            lines.append(f"  {{{', '.join(v)}}}: {len(ks)} theorems")
            lines.append(f"    {', '.join(sorted(ks))}")
        lines.append("  no spoke rests on any axiom outside the standard three plus, for finite "
                     "certificates only, the compiled-evaluator trust")
        return True, "\n".join(lines), {"status": "axioms"}
    if low == "lenses":
        by: Dict[str, List[str]] = {}
        for s in STATEMENTS.values():
            by.setdefault(s.lens, []).append(f"{s.name} [{s.status}]")
        lines = ["LENSES"] + [f"  {k}: {', '.join(v)}" for k, v in sorted(by.items())]
        return True, "\n".join(lines), {"status": "lenses"}
    m = re.fullmatch(r"derive\s+(\w+)\s*=>\s*(\w+)", a)
    if m:
        x, y = m.group(1), m.group(2)
        for n in (x, y):
            if n not in STATEMENTS:
                return False, f"refused: {n} is not a statement of the wheel", {
                    "status": "unknown"}
        cert = derivation(x, y)
        for ni in NON_IMPLICATIONS:
            if ni.premise == x and ni.conclusion == y:
                return True, (f"{x} =/=> {y}  [negative control: {ni.lean}; {ni.why}]"), {
                    "status": "refuted"}
        if cert is None:
            return True, (f"{x} => {y}: NOT DERIVABLE from the declared spokes (this is not a "
                          f"proof that it fails)"), {"status": "underived"}
        return True, f"{x} => {y}: DERIVED  certificate: {' ; '.join(cert) or 'trivial'}", {
            "status": "derived", "certificate": list(cert)}
    return False, ("refused: tool theorem [wheel | axioms | lenses | derive A => B]"), {
        "status": "unread"}
