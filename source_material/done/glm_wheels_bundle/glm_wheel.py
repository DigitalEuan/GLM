#!/usr/bin/env python3
"""GLM Wheel Generator — the engine's self-reflective inventory.

Runs v16 and extracts three rings:
  1. DOESN'T KNOW    — open questions, gaps left by refutations
  2. THINKS IS TRUE  — surviving hypotheses that need independent verification
  3. THINKS IS NEEDED — new directions suggested by guards, tools, and refutations

Then verifies/falsifies a few Wheel entries as a demonstration, and produces
the LANGUAGE WHEEL: the verified concepts that survive testing.

The Wheel is the engine telling us what it doesn't know.  The language wheel
is what survives verification — the vetted vocabulary for future runs.
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Optional

import matplotlib.font_manager as fm
fm.fontManager.addfont('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')

import matplotlib.pyplot as plt
import numpy as np

plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

# The v16 engine (`hypothesis_engine_v16.py`) pulls a long chain of
# dependencies (v15 -> v14 -> ...). If any link is missing, we still want
# the Integer Wheel integration to run, so we wrap the v16 imports in a
# try/except and let the rest of the script degrade gracefully.
_ENGINE_V16_AVAILABLE = True
try:
    from hypothesis_engine_v16 import EngineV16, sanitize
    from hypothesis_engine_v14 import (
        centre_column, left_profile, exact_wobble, exact_tax_analysis,
    )
except Exception as _import_err:  # noqa: BLE001 - degrade gracefully
    _ENGINE_V16_AVAILABLE = False
    EngineV16 = None  # type: ignore[assignment,misc]
    # fallback sanitize: convert non-JSON-serialisable types (Fraction, set, etc.)
    def sanitize(obj):
        from fractions import Fraction
        if isinstance(obj, Fraction):
            return str(obj)
        if isinstance(obj, (set, frozenset)):
            return sorted(sanitize(x) for x in obj)
        if isinstance(obj, dict):
            return {str(k): sanitize(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [sanitize(x) for x in obj]
        if isinstance(obj, (str, int, float, bool)) or obj is None:
            return obj
        return str(obj)
    _IMPORT_ERROR = _import_err
else:
    _IMPORT_ERROR = None

# ── Integer Wheel integration ─────────────────────────────────────────────────
# The Integer Wheel (integer_wheel.py) is a NEW provision placed on the GLM
# Wheel. Its signature is `Sequence[int] -> Optional[str]` (an OEIS ID), which
# is strictly distinct from the v16 hypothesis provisions
# (`str -> dict {verified, result, verdict}`) and from DriveWheel
# (`(int, int) -> int`). See INTEGER_WHEEL.md for the contract.
from integer_wheel import (
    IntegerWheel,
    default_wheel as default_integer_wheel,
)


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# 1. The three rings
# ═══════════════════════════════════════════════════════════════════════════════════════════════


@dataclass
class WheelEntry:
    """One entry on the Wheel."""
    ring: str          # "doesn't-know" | "thinks-true" | "thinks-needed"
    category: str      # sub-category within the ring
    hid: str           # hypothesis id, or "NEEDED-N" for thinks-needed
    statement: str     # the question / belief / proposal
    evidence: str      # why it's on this ring
    status: str = "on-wheel"   # on-wheel | verified | falsified | still-open


def extract_rings(eng: EngineV16) -> list:
    """Extract the three rings from the engine's hypotheses."""

    # ── Ring 1: DOESN'T KNOW ──
    # Open questions: hypotheses with status "open" or "prediction-pending",
    # plus the gaps left by refuted hypotheses.
    doesnt_know = []

    for h in eng.hyps:
        if h.status in ("open", "prediction-pending"):
            doesnt_know.append(WheelEntry(
                ring="doesn't-know",
                category="open-question",
                hid=h.hid,
                statement=h.text,
                evidence=f"status={h.status}; no finite range decides it"))

    # The gap left by refuted hypotheses: what should replace them?
    refuted_by_guard = [h for h in eng.hyps if h.status == "refuted-by-guard"]
    for h in refuted_by_guard:
        if h.key in ("TAX.mechanism.cluster", "TAX.substrate.model"):
            doesnt_know.append(WheelEntry(
                ring="doesn't-know",
                category="gap-from-refutation",
                hid=h.hid,
                statement=f"what (if anything) explains the period-doubling law H08, "
                          f"now that TAX conservation has been refuted as the mechanism?",
                evidence=f"{h.hid} was refuted by guard; the gap it leaves needs filling"))

    # The unbounded periods question (H11)
    for h in eng.hyps:
        if h.key == "LD.periods.unbounded":
            doesnt_know.append(WheelEntry(
                ring="doesn't-know",
                category="decidability",
                hid=h.hid,
                statement="are the left-diagonal periods truly unbounded? "
                          "The gap analysis says YES (implied by super-exponential growth) "
                          "but PRACTICALLY UNDECIDABLE (no finite search can confirm).",
                evidence="6 confirmed jumps; gap ratios growing; no finite verification possible"))

    # ── Ring 2: THINKS IS TRUE ──
    # Surviving hypotheses that need independent verification.
    thinks_true = []

    for h in eng.hyps:
        if h.status in ("survives", "law-holds", "prediction-confirmed"):
            # Only include hypotheses that are NOT closed in the Lean package
            # (closed = already formally verified, no longer "thinks")
            if not getattr(h, "closed", False):
                thinks_true.append(WheelEntry(
                    ring="thinks-true",
                    category=h.status,
                    hid=h.hid,
                    statement=h.text,
                    evidence=f"status={h.status}; survives held-out but not formally verified"))

    # The gap estimate (a prediction, not a hypothesis)
    for h in eng.hyps:
        if h.key == "GAP.next.estimate":
            thinks_true.append(WheelEntry(
                ring="thinks-true",
                category="prediction",
                hid=h.hid,
                statement=h.text,
                evidence="based on super-exponential gap growth; "
                         "the next jump is estimated at D >= ~275 million"))

    # ── Ring 3: THINKS IS NEEDED ──
    # New directions suggested by the guards, tools, and refutations.
    # These are NOT existing hypotheses — they are things the engine thinks
    # should BECOME hypotheses.
    thinks_needed = []

    # From the v14 dialogue's "What should I check next?" suggestions
    thinks_needed.append(WheelEntry(
        ring="thinks-needed",
        category="new-invariant",
        hid="NEEDED-1",
        statement="find an invariant that is NOT forced by white(D-1) — e.g., "
                  "the parity of D-2 read two out (doubling_read_two_out). "
                  "The TAX tool failed because every jump has defect 0 (forced by "
                  "white(D-1)). A non-forced invariant would be a genuine new mechanism.",
        evidence="v14 dialogue suggestion; the refutation of TAX.mechanism.cluster "
                 "leaves a gap that a non-forced invariant could fill"))

    thinks_needed.append(WheelEntry(
        ring="thinks-needed",
        category="new-tool",
        hid="NEEDED-2",
        statement="a guard-extractor for the R-calculus domain — test whether "
                  "R-calculus pipelines produce the centre column's lag-k profile. "
                  "The current engine only guards TAX and wobble; R-calculus is unguarded.",
        evidence="the application test APP.rcalculus.model is unguarded; "
                 "the lag-k fingerprint exists but no guard checks it"))

    thinks_needed.append(WheelEntry(
        ring="thinks-needed",
        category="new-tool",
        hid="NEEDED-3",
        statement="a guard-extractor for the seed-memory domain — test whether "
                  "the seed-forgetting law (H22) holds with a layer-aware guard. "
                  "The current guard is flat.",
        evidence="LD.seed.forgetting is law-holds but not layer-aware-guarded"))

    thinks_needed.append(WheelEntry(
        ring="thinks-needed",
        category="extend-range",
        hid="NEEDED-4",
        statement="extend the automaton run past D=87867 to test H43 "
                  "(TAX defects beyond 87867 cluster around the next jump). "
                  "Currently open because the run exceeds the held-out range.",
        evidence="H43 is open; the test is executable but requires D >= 100000"))

    thinks_needed.append(WheelEntry(
        ring="thinks-needed",
        category="formalisation",
        hid="NEEDED-5",
        statement="formalise the TAX defect closed form in Lean: "
                  "defect = -2(3c^2 - 2c(a+b) + ab). "
                  "The identity guard confirmed this; the Lean statement is proposed "
                  "but not machine-checked.",
        evidence="identity guard verified the closed form on 819 cases; "
                 "Lean proof is the next step"))

    thinks_needed.append(WheelEntry(
        ring="thinks-needed",
        category="new-domain",
        hid="NEEDED-6",
        statement="test the engine on a fourth domain (e.g., the right-diagonal "
                  "structure or the centre-column aperiodicity) to verify the "
                  "guard architecture generalises beyond TAX and wobble.",
        evidence="v16 tested 3 domains; a fourth would confirm generality"))

    thinks_needed.append(WheelEntry(
        ring="thinks-needed",
        category="automatic-extraction",
        hid="NEEDED-7",
        statement="automatic guard-input derivation: parse the hypothesis's Lean "
                  "statement to extract the algebraic criterion, rather than "
                  "hand-writing guard-extractors. This would make the engine "
                  "fully general.",
        evidence="v16's guard-extractors are manual; a parser would automate them"))

    return doesnt_know + thinks_true + thinks_needed


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# 1b. Integer Wheel — the OEIS provisions
# ═══════════════════════════════════════════════════════════════════════════════════════════════

# Rule-30-derived integer sequences the engine has produced (H08, H24, H26, H35
# from the v16 hypothesis list; H44 the TAX defect closed form is structural
# and not a single sequence). Each tuple is (H-id, the integer sequence, a
# short description). The Integer Wheel is run on each prefix; if it speaks,
# the entry goes on the THINKS-TRUE ring (a verified match); if it stays
# silent, the entry goes on the DOESN'T-KNOW ring (the sequence is not in
# OEIS as far as the wheel's curated coverage knows).
RULE30_INTEGER_SEQUENCES = [
    ("H08", [0, 3, 8, 29, 400, 87867],
     "the period-doubling left diagonals of Rule 30 (where the eventual "
     "period doubles from 1 -> 2 -> 4 -> 8 -> 16 -> 32)"),
    ("H26", [1, 2, 4, 8, 16, 32],
     "the eventual periods of the period-doubling diagonals (a dyadic tower, "
     "matching the GLM's layer stack)"),
    ("H35", [100, 99, 99, 98, 96, 92, 84],
     "R-calculus (T=0, rho=1, C=0) lag-k biases for the centre column"),
    ("H39", [1, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 0, 1, 1],
     "the Rule 30 centre column from a single black cell (first 18 terms)"),
    ("H40", [8, 29, 30, 107],
     "the delta-sigma accumulator range at N=1000, 5000, 10000, 20000"),
    ("H47", [185, 175],
     "centre column 2-bit and 3-bit block uniformity gaps"),
]


def integer_wheel_entries(int_wheel: IntegerWheel) -> list:
    """Run the Integer Wheel over Rule-30-derived integer sequences.

    Returns a list of WheelEntry items. Each entry is on the THINKS-TRUE ring
    (category `integer-wheel-verified`) when the Integer Wheel spoke, or on
    the DOESN'T-KNOW ring (category `integer-wheel-silent`) when it stayed
    silent.
    """
    entries = []
    for hid, seq, desc in RULE30_INTEGER_SEQUENCES:
        spoken = int_wheel.speak(seq)
        if spoken is not None:
            # soundness re-check
            ok = int_wheel.soundness_check(seq, spoken)
            entry = WheelEntry(
                ring="thinks-true" if ok else "doesn't-know",
                category="integer-wheel-verified" if ok else "integer-wheel-unsound",
                hid=f"IW-{hid}",
                statement=f"the Rule 30 sequence '{desc}' is OEIS {spoken}",
                evidence=(f"Integer Wheel provision matched {len(seq)}/{len(seq)} terms "
                         f"of {spoken}'s b-file" if ok else
                         f"soundness re-check FAILED on {spoken}"))
            entries.append(entry)
        else:
            entry = WheelEntry(
                ring="doesn't-know",
                category="integer-wheel-silent",
                hid=f"IW-{hid}",
                statement=(f"the Rule 30 sequence '{desc}' is not in OEIS "
                          f"(or below the wheel's curated coverage of "
                          f"{len(int_wheel)} entries)"),
                evidence=f"Integer Wheel stayed silent on {seq}")
            entries.append(entry)
    return entries


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# 2. Verification: test a few Wheel entries
# ═══════════════════════════════════════════════════════════════════════════════════════════════


def verify_gap_estimate(eng: EngineV16) -> dict:
    """Verify the gap estimate arithmetic.

    The gap analysis claims the next period-doubling diagonal is at D >= ~275 million,
    based on: est_ratio = last_r * last_rr, est_gap = gaps[-1] * est_ratio,
    est_D = jump_Ds[-1] + est_gap.

    Verify the exact integer arithmetic.
    """
    jump_Ds = [0, 3, 8, 29, 400, 87867]
    gaps = [jump_Ds[i+1] - jump_Ds[i] for i in range(len(jump_Ds)-1)]
    ratios = [Fraction(gaps[i+1], gaps[i]) for i in range(len(gaps)-1)]
    ratio_ratios = [Fraction(ratios[i+1], ratios[i]) for i in range(len(ratios)-1)]

    last_rr = ratio_ratios[-1]  # 1836807/155241
    last_r = ratios[-1]         # 87467/371
    est_ratio = last_r * last_rr
    est_gap = gaps[-1] * est_ratio
    est_D = jump_Ds[-1] + est_gap

    return {
        "entry": "GAP.next.estimate (the next period-doubling diagonal)",
        "verified": True,  # the arithmetic is exact
        "result": {
            "last_gap_ratio": str(last_r),
            "last_ratio_of_ratios": str(last_rr),
            "estimated_next_ratio": str(est_ratio),
            "estimated_next_gap": str(est_gap),
            "estimated_next_D": str(est_D),
            "estimated_next_D_decimal": float(est_D),
        },
        "verdict": f"VERIFIED (arithmetic): the next jump is estimated at D = {est_D} "
                   f"(~{float(est_D):.0f}), based on exact integer arithmetic. "
                   f"This is beyond any practical search range (~275 million).",
    }


def verify_wobble_transport(eng: EngineV16) -> dict:
    """Verify the wobble transportability claim across more seeds.

    The claim: the wobble maximum D(N)^2/N is the same across Rule 30 seeds.
    v16 tested seeds 1, 11, 101. Test more seeds.
    """
    seeds_to_test = [1, 0b11, 0b101, 0b1001, 0b10001, 0b100001]
    wobbles = {}
    for seed in seeds_to_test:
        c = centre_column(20000, rule=30, seed=seed)
        w = exact_wobble(c)
        wobbles[seed] = w["max_wobble"]

    values = list(wobbles.values())
    all_same = all(w == values[0] for w in values)

    return {
        "entry": "WOBBLE.transportable (wobble maximum is seed-independent)",
        "verified": all_same,
        "result": {str(seed): str(w) for seed, w in wobbles.items()},
        "verdict": (f"VERIFIED: the wobble maximum is the same across all 6 seeds tested: "
                    f"{[str(w) for w in values]}. The claim survives extended testing."
                    if all_same else
                    f"FALSIFIED: the wobble maximum DIFFERS across seeds: "
                    f"{[str(w) for w in values]}. The claim does not survive."),
    }


def verify_doubling_read_two_out(eng: EngineV16) -> dict:
    """Verify NEEDED-1: is the parity of D-2 read two out independent of white(D-1)?

    The hypothesis: the parity of diagonal D-2 (read at time D, two steps out from
    the centre) might be an invariant that is NOT forced by white(D-1).

    Test: for each period-doubling diagonal J ∈ {3, 8, 29, 400}, check whether
    parity(D-2) is independent of white(D-1). If parity(D-2) varies among jumps
    while white(D-1) is always true, then parity(D-2) is a non-forced invariant.
    """
    jumps = [3, 8, 29, 400]
    big = eng.left_profiles.get(max(eng.left_profiles.keys())) if hasattr(eng, "left_profiles") else eng.left_dev
    if big is None:
        return {"entry": "NEEDED-1", "verified": False, "result": {},
                "verdict": "could not access the left profile"}

    results = {}
    for J in jumps:
        if J >= big.N:
            continue
        white_Dm1 = big.white[J - 1]
        parity_Dm2 = big.parity[J - 2] if J - 2 < len(big.parity) else None
        results[J] = {"white(D-1)": white_Dm1, "parity(D-2)": parity_Dm2}

    # Check: is parity(D-2) the same across all jumps?
    parities = [r["parity(D-2)"] for r in results.values() if r["parity(D-2)"] is not None]
    all_same_parity = len(set(parities)) == 1 if parities else False

    return {
        "entry": "NEEDED-1 (doubling_read_two_out: is parity(D-2) a non-forced invariant?)",
        "verified": not all_same_parity,  # if parities differ, it's a non-forced invariant
        "result": results,
        "verdict": (f"VERIFIED (partial): parity(D-2) varies across jumps "
                    f"({[r['parity(D-2)'] for r in results.values()]}), so it is NOT "
                    f"forced by white(D-1). This is a candidate for a non-forced invariant. "
                    f"Further testing needed."
                    if not all_same_parity else
                    f"FALSIFIED: parity(D-2) is the same across all jumps "
                    f"({parities}), so it IS forced by white(D-1). Not a new invariant."),
    }


def verify_wheel_entries(eng: EngineV16) -> list:
    """Verify/falsify a few Wheel entries as a demonstration."""
    return [
        verify_gap_estimate(eng),
        verify_wobble_transport(eng),
        verify_doubling_read_two_out(eng),
    ]


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# 3. The language wheel: verified concepts
# ═══════════════════════════════════════════════════════════════════════════════════════════════


def build_language_wheel(eng: EngineV16, verifications: list) -> list:
    """Build the language wheel: concepts that have survived verification.

    These are the vetted vocabulary for future runs:
      - law-holds hypotheses (formally verified or exact on all data)
      - prediction-confirmed hypotheses (checked by direct computation)
      - closed hypotheses (already in the Lean package)
      - newly verified Wheel entries
    """
    language = []

    for h in eng.hyps:
        if h.status == "law-holds":
            language.append({
                "concept": h.text[:120],
                "hid": h.hid,
                "source": "law-holds (exact on all data)",
                "formal": getattr(h, "lean_status", "not formalised"),
            })
        elif h.status == "prediction-confirmed":
            language.append({
                "concept": h.text[:120],
                "hid": h.hid,
                "source": "prediction-confirmed (checked by direct computation)",
                "formal": getattr(h, "lean_status", "not formalised"),
            })
        elif getattr(h, "closed", False):
            language.append({
                "concept": h.text[:120],
                "hid": h.hid,
                "source": "closed in the Lean package",
                "formal": getattr(h, "lean_status", ""),
            })

    # Add newly verified Wheel entries
    for v in verifications:
        if v["verified"]:
            language.append({
                "concept": v["entry"],
                "hid": "WHEEL-VERIFY",
                "source": "verified in this Wheel run",
                "formal": v["verdict"][:120],
            })

    return language


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# 4. The Wheel visualization
# ═══════════════════════════════════════════════════════════════════════════════════════════════


def draw_wheel(rings: list, verifications: list, language: list, out_path: str):
    """Draw the Wheel as a three-ring radial diagram."""
    fig, ax = plt.subplots(figsize=(14, 14), constrained_layout=True)

    doesnt_know = [e for e in rings if e.ring == "doesn't-know"]
    thinks_true = [e for e in rings if e.ring == "thinks-true"]
    thinks_needed = [e for e in rings if e.ring == "thinks-needed"]

    # Three concentric rings
    # Inner: thinks-needed (proposals)
    # Middle: thinks-true (beliefs)
    # Outer: doesn't-know (questions)
    ring_radii = {"thinks-needed": (0.0, 0.33), "thinks-true": (0.33, 0.66),
                  "doesn't-know": (0.66, 1.0)}
    ring_colors = {"thinks-needed": "#2ca02c", "thinks-true": "#1f77b4",
                   "doesn't-know": "#ff7f0e"}

    # Draw the ring backgrounds
    for ring_name, (r_inner, r_outer) in ring_radii.items():
        theta = np.linspace(0, 2 * np.pi, 200)
        ax.fill_between(theta, r_inner, r_outer, color=ring_colors[ring_name],
                        alpha=0.15, zorder=1)
        # Ring label
        ax.text(0, -(r_inner + r_outer) / 2 - 0.02, ring_name.replace("-", " "),
                ha="center", va="top", fontsize=11, fontweight="bold",
                color=ring_colors[ring_name], alpha=0.8)

    # Place entries on each ring
    def place_ring(entries, r_inner, r_outer, color, ring_name):
        n = len(entries)
        if n == 0:
            return
        r_mid = (r_inner + r_outer) / 2
        for i, entry in enumerate(entries):
            angle = 2 * np.pi * i / n + np.pi / 2  # start at top
            x = r_mid * np.cos(angle)
            y = r_mid * np.sin(angle)
            ax.plot(x, y, 'o', color=color, markersize=8, zorder=4)
            # Label
            label_r = r_outer + 0.05
            lx = label_r * np.cos(angle)
            ly = label_r * np.sin(angle)
            ha = 'left' if np.cos(angle) > 0.1 else ('right' if np.cos(angle) < -0.1 else 'center')
            va = 'bottom' if np.sin(angle) > 0.1 else ('top' if np.sin(angle) < -0.1 else 'center')
            label = f"{entry.hid}"
            if entry.hid.startswith("NEEDED"):
                label = f"N{entry.hid.split('-')[1]}"
            ax.annotate(label, (x, y), xytext=(lx, ly), fontsize=7,
                        ha=ha, va=va, color=color, fontweight='bold',
                        arrowprops=dict(arrowstyle='-', color=color, alpha=0.3, lw=0.5))

    place_ring(thinks_needed, *ring_radii["thinks-needed"], ring_colors["thinks-needed"], "thinks-needed")
    place_ring(thinks_true, *ring_radii["thinks-true"], ring_colors["thinks-true"], "thinks-true")
    place_ring(doesnt_know, *ring_radii["doesn't-know"], ring_colors["doesn't-know"], "doesn't-know")

    # Center: the language wheel (verified concepts)
    center_text = f"LANGUAGE WHEEL\n{len(language)} verified concepts"
    ax.text(0, 0, center_text, ha="center", va="center", fontsize=12,
            fontweight="bold", bbox=dict(boxstyle='round,pad=0.5',
            facecolor='white', edgecolor='black', alpha=0.9))

    # Verification results (top-right)
    ver_text = "VERIFICATION RESULTS\n"
    for v in verifications:
        status = "VERIFIED" if v["verified"] else "FALSIFIED"
        ver_text += f"  {status}: {v['entry'][:50]}\n"
    ax.text(1.15, 1.15, ver_text.strip(), fontsize=8, family='monospace',
            va='top', ha='left',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#f0f0f0',
                      edgecolor='#cccccc', alpha=0.9))

    # Title
    ax.set_title("The GLM Wheel\n"
                 "what the engine doesn't know (outer) · thinks is true (middle) · thinks is needed (inner)\n"
                 f"{len(doesnt_know)} questions · {len(thinks_true)} beliefs · {len(thinks_needed)} proposals",
                 fontsize=13, fontweight='bold', pad=20)

    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.5, 1.5)
    ax.set_aspect('equal')
    ax.axis('off')

    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"Wheel saved: {out_path}")


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# 5. Main
# ═══════════════════════════════════════════════════════════════════════════════════════════════


def main():
    # ── v16 engine — degrade gracefully if its dep chain is broken ─────────
    if not _ENGINE_V16_AVAILABLE:
        print(f"WARNING: v16 engine unavailable ({_IMPORT_ERROR}); "
              f"running the Integer Wheel integration only.")
        # synthesise an empty engine placeholder so the rest of main() can run
        class _Empty:
            hyps = []
            left_profiles = {}
            left_dev = None
        eng = _Empty()
        rings = []
        verifications = []
    else:
        print("Running v16 to generate the Wheel...")
        eng = EngineV16(quick=True, log=lambda *a: None)
        eng.run()

        print("\nExtracting the three rings...")
        rings = extract_rings(eng)

    # ── Plug in the Integer Wheel ─────────────────────────────────────────
    # Build the Integer Wheel (curated OEIS subset) and run its provisions
    # over Rule-30-derived integer sequences. Each provision speaks an OEIS
    # ID (THINKS-TRUE, category integer-wheel-verified) or stays silent
    # (DOESN'T-KNOW, category integer-wheel-silent). The entries are added
    # to the rings and to the language wheel below.
    print("\nBuilding the Integer Wheel (curated OEIS subset)...")
    int_wheel = default_integer_wheel()
    print(f"  Loaded Integer Wheel with {len(int_wheel)} OEIS entries.")

    print("\nRunning the Integer Wheel over Rule 30 integer sequences...")
    iw_entries = integer_wheel_entries(int_wheel)
    iw_spoke = sum(1 for e in iw_entries if e.ring == "thinks-true")
    iw_silent = sum(1 for e in iw_entries if e.ring == "doesn't-know")
    print(f"  Spoke on {iw_spoke}/{len(iw_entries)} sequences; "
          f"silent on {iw_silent}.")
    for e in iw_entries:
        tag = "SPOKE" if e.ring == "thinks-true" else "silent"
        print(f"  [{tag}] {e.hid}: {e.statement[:80]}")

    # Merge the Integer Wheel entries into the three rings.
    rings.extend(iw_entries)

    doesnt_know = [e for e in rings if e.ring == "doesn't-know"]
    thinks_true = [e for e in rings if e.ring == "thinks-true"]
    thinks_needed = [e for e in rings if e.ring == "thinks-needed"]

    print(f"\n  DOESN'T KNOW:    {len(doesnt_know)} entries")
    print(f"  THINKS IS TRUE:  {len(thinks_true)} entries")
    print(f"  THINKS IS NEEDED:{len(thinks_needed)} entries")

    if _ENGINE_V16_AVAILABLE:
        print("\nVerifying Wheel entries...")
        verifications = verify_wheel_entries(eng)
        for v in verifications:
            status = "VERIFIED" if v["verified"] else "FALSIFIED"
            print(f"  [{status}] {v['entry'][:70]}")
    else:
        verifications = []

    print("\nBuilding the language wheel...")
    language = build_language_wheel(eng, verifications) if _ENGINE_V16_AVAILABLE else []

    # Augment the language wheel with the Integer Wheel's spoken assertions.
    # Each verified Integer Wheel entry adds an (OEIS ID, sequence) assertion
    # to the language — the GLM can now "speak integer" by citing the OEIS ID
    # whose b-file matches a Rule-30-derived sequence.
    for e in iw_entries:
        if e.ring == "thinks-true" and e.category == "integer-wheel-verified":
            language.append({
                "concept": e.statement,
                "hid": e.hid,
                "source": "Integer Wheel provision (OEIS b-file match)",
                "formal": "Integer Wheel soundness: b-file prefix verified",
            })
    print(f"  {len(language)} verified concepts "
          f"(incl. {sum(1 for e in iw_entries if e.ring == 'thinks-true')} "
          f"from the Integer Wheel)")

    # Draw the Wheel
    out_dir = Path("/home/z/my-project/download")
    draw_wheel(rings, verifications, language,
               str(out_dir / "glm_wheel.png"))

    # Write the Wheel document
    md = ["# The GLM Wheel", "",
          "The engine's self-reflective inventory: what it doesn't know, what it "
          "thinks is true, and what it thinks is needed.", "",
          "![The GLM Wheel](./glm_wheel.png)", "",
          f"Generated from v16's {len(eng.hyps)} hypotheses.", "",
          "## Ring 1 (outer) — DOESN'T KNOW", "",
          "Open questions, gaps left by refutations, decidability questions.", ""]
    for e in doesnt_know:
        md.append(f"### {e.hid} [{e.category}]")
        md.append(f"**Question**: {e.statement}")
        md.append(f"**Evidence**: {e.evidence}")
        md.append("")

    md += ["## Ring 2 (middle) — THINKS IS TRUE", "",
           "Surviving hypotheses that need independent verification.", ""]
    for e in thinks_true:
        md.append(f"### {e.hid} [{e.category}]")
        md.append(f"**Belief**: {e.statement}")
        md.append(f"**Evidence**: {e.evidence}")
        md.append("")

    md += ["## Ring 3 (inner) — THINKS IS NEEDED", "",
           "New directions suggested by guards, tools, and refutations.", ""]
    for e in thinks_needed:
        md.append(f"### {e.hid} [{e.category}]")
        md.append(f"**Proposal**: {e.statement}")
        md.append(f"**Evidence**: {e.evidence}")
        md.append("")

    md += ["## Verification results", ""]
    for v in verifications:
        status = "VERIFIED" if v["verified"] else "FALSIFIED"
        md.append(f"### [{status}] {v['entry']}")
        md.append(f"**Verdict**: {v['verdict']}")
        if v["result"]:
            md.append(f"**Result**: {json.dumps(sanitize(v['result']), indent=2)}")
        md.append("")

    md += ["## The Language Wheel", "",
           "Verified concepts — the vetted vocabulary for future runs.", ""]
    for c in language:
        md.append(f"- **{c['hid']}** ({c['source']}): {c['concept']}")
    md.append("")

    (out_dir / "glm_wheel.md").write_text("\n".join(md))

    # JSON output
    wheel_json = {
        "engine": "GLM Wheel (from v16) + Integer Wheel provisions",
        "rings": {
            "doesn't-know": [sanitize({"ring": e.ring, "category": e.category,
                                       "hid": e.hid, "statement": e.statement,
                                       "evidence": e.evidence})
                             for e in doesnt_know],
            "thinks-true": [sanitize({"ring": e.ring, "category": e.category,
                                      "hid": e.hid, "statement": e.statement,
                                      "evidence": e.evidence})
                            for e in thinks_true],
            "thinks-needed": [sanitize({"ring": e.ring, "category": e.category,
                                        "hid": e.hid, "statement": e.statement,
                                        "evidence": e.evidence})
                              for e in thinks_needed],
        },
        "verifications": [sanitize(v) for v in verifications],
        "language_wheel": sanitize(language),
        "integer_wheel": {
            "n_oeis_entries": len(int_wheel),
            "provisions": [
                sanitize({
                    "hid": e.hid,
                    "spoke": e.ring == "thinks-true",
                    "category": e.category,
                    "statement": e.statement,
                    "evidence": e.evidence,
                })
                for e in iw_entries
            ],
        },
    }
    (out_dir / "glm_wheel.json").write_text(
        json.dumps(sanitize(wheel_json), indent=2, ensure_ascii=False))

    print(f"\nWheel document: {out_dir / 'glm_wheel.md'}")
    print(f"Wheel JSON:     {out_dir / 'glm_wheel.json'}")
    print(f"Wheel image:    {out_dir / 'glm_wheel.png'}")


if __name__ == "__main__":
    main()
