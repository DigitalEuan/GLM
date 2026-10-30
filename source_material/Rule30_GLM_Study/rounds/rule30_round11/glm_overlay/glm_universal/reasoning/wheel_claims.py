"""``glm_universal.reasoning.wheel_claims`` -- checking claims about the wheels (Round 11).

Round 11 of the Rule 30 study, track D (the reasoning benchmark).  ``tool claim <text>`` reads a
claim about Rule 30 / the 256 wheels in one of the declared **claim frames** below, decides it,
and answers with a four-part trace:

    VERDICT              ACCEPT, REJECT or OPEN (with its evidence class)
    MISSING HYPOTHESIS   for REJECT: what the claim silently assumes; for OPEN: what is missing
    WITNESS / REFERENCE  a counterexample computed here, or the Lean theorem that settles it
    NEXT TEST            what to compute or prove next

Two kinds of frame, declared and not mixed:

* **Computed frames** -- the verdict is computed from the exact register, then matched to the
  Lean theorem that covers every parameter where one exists:
  ``column C distinguishes wheel R from wheel S`` (both columns from the impulse; a first
  differing time is a witness; for ``S = mirror R`` at ``C = 0`` the columns are equal for ever by
  ``ecaColumn_mirror``), ``the wobble at column C equals the wobble at column -C``,
  ``right diagonal D is balanced``, ``rows 0..T determine wheel 30``.
* **Settled frames** -- claims whose verdict is a proved theorem or a proved non-implication in
  the Lean package; the frame carries the theorem and the missing hypothesis.  These are
  retrieval with a reason, not computation, and the answer says so.

Anything outside the frames is refused, with the list of frames.  Exact integers only.
"""
from __future__ import annotations

import re
from fractions import Fraction
from typing import Callable, Dict, List, Optional, Tuple

from ..data_objects import automata as ca
from ..data_objects import automata_round11 as r11

__all__ = ["check_claim", "claim_text", "FRAMES", "CLAIM_STEPS"]

#: Steps computed for a column comparison.
CLAIM_STEPS = 256


def _col(word: str) -> Optional[int]:
    w = word.strip().lower()
    if w in ("centre", "center", "the centre", "the center", "0", "centre column",
             "center column"):
        return 0
    try:
        return int(w.replace("column", "").strip())
    except ValueError:
        return None


def _trace(verdict: str, evidence: str, missing: str, witness: str, nxt: str,
           kind: str) -> Dict[str, str]:
    return {"verdict": verdict, "evidence": evidence, "missing": missing, "witness": witness,
            "next": nxt, "kind": kind}


# ---------------------------------------------------------------------------
# computed frames
# ---------------------------------------------------------------------------

def _distinguish(m) -> Dict[str, str]:
    c = _col(m.group("c"))
    r, s = int(m.group("r")), int(m.group("s"))
    if c is None or not (0 <= r < 256 and 0 <= s < 256):
        raise ValueError("column or wheel out of range")
    a = ca.evolve_impulse_column(r, CLAIM_STEPS, c)
    b = ca.evolve_impulse_column(s, CLAIM_STEPS, c)
    diff = next((t for t in range(CLAIM_STEPS) if a[t] != b[t]), None)
    if diff is not None:
        return _trace(
            "ACCEPT", "EMP (finite witness computed here)",
            "none",
            f"column {c} of wheel {r} and of wheel {s} from the impulse first differ at t = "
            f"{diff}: {a[diff]} vs {b[diff]}",
            "none: a finite witness settles a claim of distinguishability", "computed")
    if r == s:
        return _trace("REJECT", "FORMAL (trivial)", "the two wheels are the same wheel",
                      "identical rules give identical columns", "name two different wheels",
                      "computed")
    if c == 0 and s == ca.mirror_number(r):
        return _trace(
            "REJECT", "FORMAL",
            "the centre column of the impulse run is invariant under the mirror (wheel r -> its "
            "mirror image, cell j -> -j), and the impulse is mirror-symmetric",
            f"column 0 of wheels {r} and {s} agree at every t < {CLAIM_STEPS} (computed) and for "
            f"every t (Lean: GLM.Rule30.ecaColumn_mirror, seed_mirror; for 30/86: "
            f"ecaColumn_eightySix_centre, centre_column_class)",
            "move the observer off-centre: column 1 separates them (Lean: "
            "column_one_separates_mirror, column_one_identifies; 8 values suffice)", "computed")
    if c != 0 and s == ca.mirror_number(r):
        return _trace(
            "OPEN", "EMP", "no theorem on file for this pair and column",
            f"columns agree for t < {CLAIM_STEPS}; by the mirror, column {c} of {s} is column "
            f"{-c} of {r} (ecaColumn_mirror)",
            f"compare column {c} and column {-c} of wheel {r} further", "computed")
    return _trace(
        "OPEN", "EMP", "the columns agree on every value computed; no theorem on file",
        f"columns agree for t < {CLAIM_STEPS}",
        "compute further, or prove equality of the two columns", "computed")


def _wobble_mirror(m) -> Dict[str, str]:
    c = _col(m.group("c"))
    if c is None:
        raise ValueError("column")
    if c == 0:
        return _trace("ACCEPT", "FORMAL", "none",
                      "the gap D_0(N) - D_-0(N) is 0 for every N (Lean: chiralGap_centre)",
                      "none", "computed")
    N = 10000
    a = ca.evolve_impulse_column(30, N, c)
    b = ca.evolve_impulse_column(30, N, -c)
    first = next((n for n in range(N + 1) if ca.wobble(a, n) != ca.wobble(b, n)), None)
    ev = "FORMAL" if 1 <= abs(c) <= 5 else "EMP"
    ref = (" (Lean: GLM.Rule30.chiralGap_first)" if ev == "FORMAL" else " (computed here)")
    return _trace(
        "REJECT", ev,
        "a column and its mirror column agree only at the centre: the mirror maps column c of "
        "wheel 30 to column -c of wheel 86, not of wheel 30",
        f"D_{c}(N) != D_{-c}(N) first at N = {first}: {ca.wobble(a, first)} vs "
        f"{ca.wobble(b, first)}{ref}; the gap is wheel 30 minus wheel 86 at column {c} "
        f"(chiralGap_eq_thirty_sub_eightySix)",
        "measure the size of the gap: to N = 10^6 it stays within a random-walk range "
        "(r30_chiral_gap_c_N, EMP)", "computed")


def _diag_balanced(m) -> Dict[str, str]:
    D = int(m.group("d"))
    if not 0 <= D < 40:
        raise ValueError("diagonals 0..39 are held")
    rec = r11.diagonal_record(D)
    P, k, anti = rec["period"], rec["ones"], rec["anti"]
    if anti:
        ev = "FORMAL" if D == 7 else "EMP (anti-periodicity computed) + FORMAL (its consequence)"
        return _trace(
            "ACCEPT", ev, "none",
            f"diagonal {D} is anti-periodic with half-period {P // 2}: |D(N)| <= {P // 2} for "
            f"every N and frequency 1/2 (Lean: wobble_antiPeriodic_bound, "
            f"antiPeriodic_hasFrequencyHalf" + (", rdiag_seven_bounded)" if D == 7 else ")"),
            "none", "computed")
    if 2 * k == P:
        return _trace(
            "ACCEPT", "EMP (period and count computed; a periodic sequence balanced over a "
            "period has frequency 1/2)", "none",
            f"diagonal {D}: least period {P}, {k} black per period (balanced, not anti-periodic)",
            "none", "computed")
    return _trace(
        "REJECT", "FORMAL" if D == 5 else "EMP",
        "a right diagonal is periodic, but periodicity does not force balance; only "
        "anti-periodic diagonals are forced to be balanced",
        f"diagonal {D}: least period {P}, {k} black per period, frequency {Fraction(k, P)}"
        + (" (Lean: rdiag_five_not_half)" if D == 5 else ""),
        "ask which diagonals are anti-periodic (r30_rdiag_D); infinitely many are "
        "(infinitely_many_balanced_rdiag)", "computed")


def _rows_determine(m) -> Dict[str, str]:
    T = int(m.group("t"))
    from . import wheel_induction as wi
    rows = ca.impulse_rows(30, T)
    surv = [r for r in range(256) if ca.local_rule(r, 0, 0, 0) == 0
            and ca.impulse_rows(r, T) == rows]
    if surv == [30]:
        return _trace("ACCEPT", "FORMAL" if T >= 4 else "EMP", "none",
                      f"only wheel 30 reproduces rows 0..{T} of the impulse run among the 128 "
                      f"wheels with f(000)=0 (Lean: rows_identify_thirty for T >= 4)",
                      "none", "computed")
    return _trace(
        "REJECT", "FORMAL" if T == 3 else "EMP",
        f"rows 0..{T} never show every neighbourhood wheel 30's table needs",
        f"{len(surv)} wheels reproduce rows 0..{T}: {surv[:8]}{'...' if len(surv) > 8 else ''}"
        + (" (Lean: rows_three_do_not_identify: wheel 62)" if T == 3 else ""),
        f"show row {T + 1}: rows 0..4 determine wheel 30 (rows_identify_thirty)", "computed")


# ---------------------------------------------------------------------------
# settled frames: (pattern, verdict, evidence, missing, reference, next)
# ---------------------------------------------------------------------------

_SETTLED: Tuple[Tuple[str, str, str, str, str, str], ...] = (
    (r"(?:for )?almost every (?:initial )?row.*(?:hence|so|therefore|thus).*seed.*",
     "REJECT", "FORMAL",
     "the seed is a single row of fair-coin measure 0; 'almost every row' says nothing about it",
     "Lean: bernoulliRow_seed_null, measure_theory_boundary, exists_row_with_biased_column",
     "a seed-specific argument (SeedFSTypical is one sufficient one)"),
    (r"(?:for )?almost every (?:initial )?row.*(?:frequency 1/2|balanced|not eventually periodic|"
     r"aperiodic).*", "ACCEPT", "FORMAL", "none",
     "Lean: ae_column_frequency_half, ae_column_not_eventuallyPeriodic, ae_problems_one_and_two",
     "none"),
    (r".*(?:wobble )?arrow.*(?:tells?|distinguish\w*|records?|shows?).*(?:left.*right|"
     r"orientation|mirror|chirality).*", "REJECT", "FORMAL",
     "the arrow -sign D(N) is unchanged by the mirror, for every N, wheel, row and column",
     "Lean: observerArrow_mirror, observerArrow_eightySix",
     "read an off-centre column instead (column_one_identifies)"),
    (r".*(?:wobble )?arrow.*(?:reverse\w*|flip\w*|negat\w*).*colou?r.*", "ACCEPT", "FORMAL",
     "none", "Lean: observerArrow_complement, observerArrow_oneThirtyFive", "none"),
    (r".*(?:right[- ]edge|right boundary|right half).*(?:white|zero|pinned).*(?:forces?|implies|"
     r"gives?).*(?:frequency 1/2|balance\w*|o\(n\)|d\(n\) ?= ?o\(n\)).*", "REJECT", "FORMAL",
     "the right-white boundary alone does not force balance: the left half matters",
     "Lean: exists_row_with_biased_column (a right-white row whose centre column has frequency "
     "1/3), column_inverse_exists, seed_unique_preimage",
     "use the seed's left edge as well (both edges white): no theorem on file"),
    (r".*every right diagonal.*(?:balanced|frequency 1/2).*", "REJECT", "FORMAL",
     "periodicity of a diagonal does not force balance",
     "Lean: rdiag_five_not_half (diagonal 5 has frequency 3/8)",
     "ask for infinitely many instead (infinitely_many_balanced_rdiag)"),
    (r".*infinitely many right diagonals.*(?:balanced|frequency 1/2|bounded wobble).*",
     "ACCEPT", "FORMAL", "none",
     "Lean: infinitely_many_balanced_rdiag, exists_antiPeriodic_rdiag", "none"),
    (r".*(?:centre|center) column.*eventually constant.*", "REJECT", "FORMAL",
     "a constant tail would make two adjacent columns eventually periodic",
     "Lean: centerCol_not_eventually_constant, column_not_eventually_constant",
     "period 2 and higher are OPEN"),
    (r".*two (?:different |distinct )?columns.*(?:both )?eventually periodic.*", "REJECT",
     "FORMAL", "two distinct columns can never both be eventually periodic",
     "Lean: not_both_columns_periodic, seed_at_most_one_periodic_column",
     "Problem 1 asks that the centre is not the (at most one) exception"),
    (r".*whitediagonalcount.*odd.*|.*anf degree.*2n ?- ?1.*(?:every|all) n.*", "ACCEPT",
     "FORMAL", "none",
     "Lean: whiteDiagonalCount_odd, topMonomialConjecture_holds, center_anfDegree_eq (Round 8)",
     "none"),
    (r".*anf degree.*(?:hence|so|therefore|implies).*(?:hard|aperiodic|not periodic|"
     r"complex).*", "REJECT", "FORMAL",
     "degree is a property of the map on all rows, not of its value on the seed; the all-white "
     "row has the same map and a periodic column",
     "Lean: map_properties_cannot_decide_periodicity, wholeCone_compatible_with_periodicity",
     "a seed-specific argument"),
    (r".*(?:problem|question) ?1.*(?:proved|solved|settled|true).*|.*(?:centre|center) column.*"
     r"(?:is )?not eventually periodic.*", "OPEN", "OPEN",
     "a seed-specific reason why the centre is not the one possibly periodic column",
     "proved: period 1 excluded (centerCol_not_eventually_constant), at most one periodic column "
     "(seed_at_most_one_periodic_column), equivalences problem1_iff_fsObservers_fail",
     "exclude period 2 for the centre column"),
    (r".*(?:problem|question) ?2.*(?:proved|solved|settled|true).*|.*(?:centre|center) column.*"
     r"frequency.*1/2.*", "OPEN", "OPEN",
     "a seed-specific genericity statement (e.g. SeedFSTypical)",
     "proved: P2 <=> D(N) = o(N) (problem2_iff_wobble); holds for almost every row; no finite "
     "certificate decides it (no_finite_certificate_problem2)",
     "a bound D(N) = o(N) for the seed"),
    (r".*(?:problem|question) ?3.*(?:proved|solved|settled|true).*", "OPEN", "OPEN",
     "a lower bound for a uniform machine model",
     "proved: whole-cone dependence (wholeConeDependence_holds), circuits need >= t gates "
     "(circuit_size_ge); Problem3 stated for Turing machines", "none on file"),
)


#: Declared computed frames: (pattern, checker).
FRAMES: Tuple[Tuple[str, Callable], ...] = (
    (r"(?:the )?(?:observer at )?(?:column )?(?P<c>centre|center|-?\d+)(?: column)?(?: observer)?"
     r" (?:can )?(?:distinguish(?:es)?|tells? apart|separates?|can tell) wheel (?P<r>\d+) "
     r"(?:from|and) wheel (?P<s>\d+)", _distinguish),
    (r"(?:the )?(?:centre|center) column observer can distinguish wheel (?P<r>\d+) from wheel "
     r"(?P<s>\d+)(?P<c>)", None),
    (r"(?:the )?wobble at column (?P<c>-?\d+) equals the wobble at column -?\d+", _wobble_mirror),
    (r"(?:the )?right diagonal (?P<d>\d+) (?:is balanced|has frequency 1/2)", _diag_balanced),
    (r"rows 0 ?(?:\.\.|to|-) ?(?P<t>\d+) (?:of the impulse run )?(?:determine|identify) wheel 30",
     _rows_determine),
)


def check_claim(text: str) -> Optional[Dict[str, str]]:
    t = text.strip().rstrip(".?! ").strip()
    t = re.sub(r"\s+", " ", t)
    low = t.lower()
    for pattern, fn in FRAMES:
        mm = re.fullmatch(pattern, low)
        if mm:
            if fn is None:
                # the centre-observer phrasing of the distinguish frame
                class _M:
                    def __init__(self, g):
                        self.g = g

                    def group(self, k):
                        return self.g[k]
                return _distinguish(_M({"c": "0", "r": mm.group("r"), "s": mm.group("s")}))
            return fn(mm)
    for pattern, verdict, ev, missing, ref, nxt in _SETTLED:
        if re.fullmatch(pattern, low):
            return _trace(verdict, ev, missing, ref, nxt, "settled")
    return None


def claim_text(arg: str) -> Tuple[bool, str, Dict[str, object]]:
    """``tool claim <claim>``: the four-part trace, or a refusal naming the frames."""
    if not arg.strip():
        return (False, "refused: give a claim, e.g. 'tool claim the centre column observer can "
                "distinguish wheel 30 from wheel 86'", {"status": "empty"})
    try:
        tr = check_claim(arg)
    except ValueError as e:
        return False, f"refused: the claim is in a frame but out of range ({e})", {
            "status": "out_of_range"}
    if tr is None:
        frames = ("column C distinguishes wheel R from wheel S; the wobble at column C equals "
                  "the wobble at column -C; right diagonal D is balanced; rows 0..T determine "
                  "wheel 30; and the settled frames (almost every row ..., the arrow ..., right "
                  "edge ..., every/infinitely many right diagonals ..., eventually constant, two "
                  "columns periodic, whiteDiagonalCount / ANF degree, problem 1/2/3)")
        return False, f"refused: the claim is in no declared frame; frames: {frames}", {
            "status": "unread"}
    if tr["kind"] == "computed":
        how = "computed from the register, matched to the Lean theorem"
    elif tr["verdict"] == "OPEN":
        how = "a settled frame: the statement is open; the frame carries what is proved around it"
    else:
        how = "a settled frame: the verdict is a Lean theorem carried by the frame"
    text = (f"VERDICT  {tr['verdict']} [{tr['evidence']}]\n"
            f"MISSING HYPOTHESIS  {tr['missing']}\n"
            f"WITNESS / REFERENCE  {tr['witness']}\n"
            f"NEXT TEST  {tr['next'] or 'none'}\n"
            f"({how})")
    return True, text, dict(tr, status=tr["verdict"].lower())
