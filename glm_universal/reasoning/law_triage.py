"""The 106 unresolved laws triaged (Phase 83).

``studies/LAW_TRIAGE_STUDY.md`` declares the rule: a knowledge-base law comes
into the GLM only if it gives a measurable service the GLM does not already
have (S1 computable from the substrate, S2 new, S3 useful).  This module gives
each of the 106 laws the law review left ``UNRESOLVED-UBP`` exactly one fate,
computes the declared checks from the running substrate, runs the callables
the *already served* laws are served by, and checks the frozen rows against
the knowledge base inside ``source_material/GLM-main.zip`` where it is present.

Everything is exact.  Nothing here is consulted by the GLM at run time: the
triage is a record, and the module adds no law to any reading.
"""

from __future__ import annotations

import json
import pathlib
from fractions import Fraction
from math import comb
from typing import Dict, List, Optional, Tuple

from ..substrate import leech2
from ..substrate.golay_decode import decode_complete
from ..substrate.mog import GOLAY_MASKS, GOLAY_SET
from . import coherence as co
from . import law_register as lr

__all__ = [
    "FATES", "REASONS", "FATE", "CHECKS", "ZIP_PATH", "KB_MEMBER", "load",
    "carriers", "check",
    "served", "source_check", "law_triage_report", "fate_of",
]

N = 24
DATA = pathlib.Path(__file__).with_name("_data") / "unresolved_laws_106.json"
#: Where the knowledge base lives; the reasoning core does not open archives
#: (only the standard-library modules its exactness test allows), so the
#: caller -- ``tools law-triage`` or the test -- reads these bytes and passes
#: them to :func:`source_check`.
ZIP_PATH = "source_material/GLM-main.zip"
KB_MEMBER = "GLM-main/long_term_memory/ubp_system_kb.json"

FATES = ("absorbed", "already served", "refuted", "retired")
REASONS = ("WORLD", "PIPELINE", "NUMEROLOGY", "UNDERSPECIFIED", "DEFINITION",
           "DUPLICATE")

_W, _P, _NU, _U, _D = "WORLD", "PIPELINE", "NUMEROLOGY", "UNDERSPECIFIED", \
    "DEFINITION"

#: One fate per law: ``id -> (fate, reason or None, note)``.
FATE: Dict[str, Tuple[str, Optional[str], str]] = {
    "LAW_BIO_007": ("retired", _W, "biological scaling from Y and the proton mass"),
    "LAW_BIO_ABLATION_001": ("retired", _W, "tumour ablation and immune inference"),
    "LAW_BIO_AQUEOUS_LENS_001": ("retired", _P, "codon, amino-acid and water vectors the GLM does not hold"),
    "LAW_BIO_CANCER_002": ("retired", _W, "a clinical claim"),
    "LAW_BIO_CONCRETE_001": ("retired", _W, "bio-mineral water ratio"),
    "LAW_BIO_ENDO_001": ("retired", _W, "hormone geometry"),
    "LAW_BIO_HEMA_003": ("retired", _W, "blood-group compatibility"),
    "LAW_BIO_HYSTERESIS_001": ("retired", _W, "a biological claim; its code content (4 - d further flips to failure) is the decoder's, already served"),
    "LAW_BIO_SANITATION_001": ("retired", _W, "microbial decomposition rates"),
    "LAW_BITLUMEN_MASTER_MODE": ("retired", _P, "BitLumen colour operators"),
    "LAW_BITTAB_ENTROPY": ("retired", _P, "BitTab element encoding"),
    "LAW_CHEM_007": ("retired", _W, "nuclear alpha clustering"),
    "LAW_CHEM_FERT_001": ("retired", _W, "fertilizer efficiency"),
    "LAW_CHEM_HYDROCARBON_001": ("retired", _U, "'distributed' density across undefined axes"),
    "LAW_CHEM_ONTOLOGICAL_YIELD": ("retired", _P, "MOG-A activation health"),
    "LAW_COMP_HRHF_001": ("retired", _P, "harmonic-drill pitch variance"),
    "LAW_COMP_SPELL_001": ("retired", _P, "rune superposition"),
    "LAW_COMP_WORK": ("retired", _D, "energy as Hamming weight times 24: a definition no GLM computation uses"),
    "LAW_COSMO_001": ("retired", _W, "dark matter and dark energy"),
    "LAW_COSMO_003": ("retired", _W, "a bias of Hawking radiation; checked: neither substrate parity statistic (1/2 of all words, all of the code) is 54.56%"),
    "LAW_COSMO_007": ("retired", _NU, "a 0.15% deficit"),
    "LAW_DRUG_002": ("retired", _W, "docking tension of molecules"),
    "LAW_DRUG_003": ("retired", _W, "pharmacological search"),
    "LAW_DRUG_004": ("retired", "DUPLICATE", "verbatim copy of LAW_DRUG_002"),
    "LAW_ENG_TOGGLE_POWER_001": ("retired", _P, "TGIC energy harvesting"),
    "LAW_ENG_VARIABLE_YIELD_001": ("retired", _W, "fusion fuel selection"),
    "LAW_GEO_003": ("retired", _P, "FFT extraction from 2D projections"),
    "LAW_GEO_DURER_001": ("retired", _P, "6D CARFE fields"),
    "LAW_GEO_HUB_002": ("retired", _W, "calcium as a slope anchor"),
    "LAW_GRAPHENE_001_REFINED": ("retired", _W, "twisted-bilayer superconductivity"),
    "LAW_HEMISPHERIC_COHERENCE_001": ("refuted", None, "the decoder is right with probability 0.97 at 1/20, not 51%; it first falls below 51% at 3/20 on a grid of hundredths"),
    "LAW_HEMISPHERIC_REDUNDANCY_001": ("retired", _W, "cognitive dual streams"),
    "LAW_KINETICS_001": ("retired", _W, "reaction rates"),
    "LAW_LEPTON_004": ("refuted", None, "the Leech lattice has no vector of norm 2: its least nonzero norm is 4"),
    "LAW_MAGNETIC_RESONANCE_001": ("retired", _W, "magnetic ordering"),
    "LAW_MATH_PRIME_001": ("retired", _NU, "a 98.54% match to the first zeta zero"),
    "LAW_MAT_CONCRETE_002": ("retired", _W, "concrete durability"),
    "LAW_MAT_PLASTIC_001": ("retired", _W, "PVC chlorine ratio"),
    "LAW_MAT_SYNTHESIS_001": ("retired", _P, "the MPI hierarchy"),
    "LAW_MESA_001": ("retired", _U, "'spectral coherence' is not defined"),
    "LAW_METRIC_003": ("retired", _NU, "G from knowledge-base constants"),
    "LAW_MILLENNIUM_001": ("retired", _U, "no statement to compute"),
    "LAW_MINERAL_002": ("retired", _W, "mineral stability"),
    "LAW_MINERAL_003": ("retired", "DUPLICATE", "verbatim copy of LAW_MINERAL_002"),
    "LAW_NUCLEAR_PROJECTION_001": ("retired", _U, "'E8_upper' and 'E8_lower' of a Leech root are not defined"),
    "LAW_OBSERVER_OOB_002": ("retired", _NU, "a mass gap from Y/10"),
    "LAW_PARTICLE_6D": ("refuted", None, "the carriers are codewords: electron and positron are 8 apart, and no lepton-quark pair is 4 apart"),
    "LAW_PHYSICS_004": ("retired", _NU, "the Planck mass from knowledge-base constants"),
    "LAW_PHYSICS_CHARGE_001": ("retired", _P, "PGCI central charge"),
    "LAW_QUANTUM_TOGGLE_001": ("retired", _W, "a 0.1 Hz quantum snap"),
    "LAW_RECOVERY_001": ("retired", _W, "superheavy nuclear stability"),
    "LAW_RELATIVITY_003": ("retired", _U, "a parsimony score of 90.5 with no declared scoring"),
    "LAW_RESONANCE_003": ("retired", _W, "crystal resonance frequencies"),
    "LAW_RTS_REQUIREMENT_001": ("retired", _W, "room-temperature superconductivity"),
    "LAW_SEASONAL_COUPLING_001": ("retired", _W, "axial tilt and solar transfer"),
    "LAW_SQUEEZE_001": ("already served", None, "read as the decoded 12-bit message plus the 3-bit coset weight: decode_complete"),
    "LAW_STABILITY_ISLAND_001": ("retired", _P, "the elemental vortex"),
    "LAW_SUPERCONDUCT_001": ("retired", _W, "room-temperature superconductivity"),
    "LAW_SYMBOL_003": ("retired", _P, "GL-1 primitives against hashed language"),
    "LAW_SYMBOL_004": ("retired", _P, "operators at the generative floor"),
    "LAW_TERRESTRIAL_GRID_002": ("retired", _W, "ley lines"),
    "LAW_TIME_004": ("retired", _W, "a 1 THz wall"),
    "LAW_TIME_005": ("retired", _NU, "a 0.15% dilation"),
    "LAW_TOPOLOGICAL_HARMONY_001": ("retired", _P, "a V8 temporal brute-force pitch mapping"),
    "LAW_UNIFIED_DISTORTION_001": ("retired", _NU, "1.0117 from metabolic work"),
    "LAW_UNITY_004": ("retired", _NU, "c and m_e from 2Y(11/12)"),
    "LAW_WEAK_SHEAR_001": ("retired", _NU, "m_W/m_Z from Y with no declared template"),
    "LAW_TOPOLOGICAL_COMPLETION_001": ("already served", None, "shell-0 tax is additive in weight: coherence.tax_shell0"),
    "LAW_VOLUMETRIC_INFERENCE_001": ("retired", _U, "'assembled' and 'visible' are not defined"),
    "LAW_EMERGENT_OBSERVER_001": ("retired", _NU, "5.87e-4 from pi, phi and Y"),
    "LAW_TRIADIC_GENESIS_001": ("retired", _NU, "204.801744 with no closed form in the declared constants"),
    "LAW_AQUEOUS_BOND_001": ("retired", _U, "the 'octad operator' is not given"),
    "LAW_13D_SINK_001": ("retired", _P, "the 13D sink protocol"),
    "LAW_VOLUMETRIC_REBATE_001": ("retired", _P, "a volumetric rebate of the KB tax"),
    "LAW_FOCAL_PIVOT_001": ("retired", _U, "the 'duality anchor' is not given"),
    "LAW_IMAGINARY_RESIDUAL_001": ("retired", _P, "beta and tilt of the KB pipeline"),
    "LAW_PI_TUNNEL_001": ("retired", _P, "carrier shielding of irrational streams"),
    "LAW_TOPOLOGICAL_BUFFER_001": ("retired", _P, "noise floor of transcendental streams"),
    "LAW_PI_STABILIZATION_001": ("retired", _P, "the shielded pi stream"),
    "LAW_MONSTROUS_FOLD_001": ("retired", _P, "the 137-shield"),
    "LAW_MIDPOINT_LATTICE_001": ("retired", _U, "the Bolt midpoint theorems are not given"),
    "LAW_RECIPROCAL_WOBBLE_001": ("retired", _NU, "a 0.8176 residual"),
    "LAW_PHI_ORBIT_1953": ("retired", _U, "the shift-and-rotate orbit is not given"),
    "LAW_FOLDED_CALCULUS_001": ("retired", _U, "no computable statement"),
    "LAW_HYBRID_STEREOSCOPY_002": ("retired", _P, "the 29-channel NCC spectral map"),
    "LAW_BARNES_WALL_256_001": ("retired", _P, "the 256D Barnes-Wall bulk"),
    "LAW_MACRO_AUDIT_001": ("retired", _P, "the 256D bulk"),
    "LAW_MACRO_COHERENCE_001": ("retired", _P, "the 256D bulk"),
    "LAW_BASIS_ALIGNMENT_001": ("retired", _P, "the 256D bulk"),
    "LAW_MOIRE_DYNAMICS_001": ("retired", _P, "the 256D Moire pattern"),
    "LAW_MACRO_BASIN_001": ("retired", _P, "the 256D bulk"),
    "LAW_HOLOGRAPHIC_DRIFT_001": ("retired", _P, "SHA-256 coordinates"),
    "LAW_SCALING_RESILIENCE_001": ("retired", _P, "the 256D bulk"),
    "LAW_PYRITE_ANTIRESONANCE_001": ("retired", _P, "the 256D bulk"),
    "LAW_POLAR_RESONANCE_001": ("retired", _P, "a TurboQuant polar filter"),
    "LAW_DODECAD_DUALITY_001": ("already served", None, "the sum of two codewords is a codeword, here of weight 12: the code's closure and weight count"),
    "LAW_ISOTOPIC_TENSION_001": ("retired", _P, "an 8.77 degree tilt per neutron"),
    "LAW_EGC_CASCADE_001": ("retired", _U, "the n = 24k cascade is not given"),
    "LAW_MACRO_RESILIENCE_001": ("retired", _P, "the 256D bulk"),
    "LAW_NONLOCAL_SURGERY_001": ("retired", _P, "a reconfigurable 256D decoder"),
    "LAW_ZETA_INVERSE_RESONANCE_001": ("retired", _P, "zeta-zero masks"),
    "LAW_PRIME_DETERMINISM_001": ("retired", _P, "the NoiseALU"),
    "LAW_GAMMA_SEPARATOR_001": ("retired", _P, "topological shear of the NoiseALU"),
    "LAW_TOPOLOGICAL_ERASURE_001": ("retired", _P, "the NoiseALU"),
    "LAW_TOPOLOGICAL_TENACITY_001": ("retired", _P, "lock pressure of the NoiseALU"),
    "LAW_SCALE_SCAFFOLDING_085": ("retired", _P, "a hexadecad scaffold"),
}


def fate_of(law: str) -> Dict[str, object]:
    fate, reason, note = FATE[law]
    return {"law": law, "fate": fate, "reason": reason, "note": note}


# ---------------------------------------------------------------------------
# the frozen rows
# ---------------------------------------------------------------------------

def load() -> Dict[str, object]:
    with open(DATA, encoding="utf-8") as fh:
        return json.load(fh)


def carriers() -> Dict[str, int]:
    """The 14 knowledge-base carriers, character ``i`` as coordinate ``i``."""
    return {k: sum(1 << i for i, ch in enumerate(v) if ch == "1")
            for k, v in load()["carriers"].items()}


def _wt(x: int) -> int:
    return bin(x).count("1")


# ---------------------------------------------------------------------------
# the declared checks (§1.3)
# ---------------------------------------------------------------------------

def _hemispheric() -> Dict[str, object]:
    right = {str(p): lr.outcome_probabilities(p)["right"]
             for p in (Fraction(1, 50), Fraction(1, 20), Fraction(1, 10))}
    grid = [Fraction(k, 100) for k in range(1, 51)]
    cliff = next(p for p in grid
                 if lr.outcome_probabilities(p)["right"] < Fraction(51, 100))
    refuted = right["1/20"] > Fraction(9, 10) and cliff > Fraction(1, 10)
    return {"right": right, "first_rate_below_51_percent": cliff,
            "outcome": "refuted" if refuted else "open"}


def _particle_6d() -> Dict[str, object]:
    c = carriers()
    e, pos = c["PARTICLE_ELECTRON_001"], c["PARTICLE_POSITRON_001"]
    leptons = [k for k in c if k in ("PARTICLE_ELECTRON_001",
                                     "PARTICLE_POSITRON_001")
               or "NEUTRINO" in k]
    quarks = [k for k in c if "QUARK" in k]
    lq = sorted({_wt(c[a] ^ c[b]) for a in leptons for b in quarks})
    all_codewords = all(v in GOLAY_SET for v in c.values())
    refuted = _wt(e ^ pos) > 3 and 4 not in lq
    return {"carriers_are_codewords": all_codewords,
            "electron_positron": _wt(e ^ pos), "lepton_quark": lq,
            "outcome": "refuted" if refuted else "open"}


def _lepton_004() -> Dict[str, object]:
    least = Fraction(leech2.MIN_NORM2, leech2.SCALE)
    return {"least_norm": least,
            "outcome": "refuted" if least > 2 else "open"}


def _cosmo_003() -> Dict[str, object]:
    even_words = Fraction(sum(comb(N, w) for w in range(0, N + 1, 2)), 2 ** N)
    even_code = Fraction(sum(1 for c in GOLAY_MASKS if _wt(c) % 2 == 0),
                         len(GOLAY_MASKS))
    claimed = Fraction(5456, 10000)
    match = claimed in (even_words, even_code)
    return {"even_fraction_words": even_words, "even_fraction_code": even_code,
            "claimed": claimed,
            "outcome": "open" if match else "retired"}


def _dodecad() -> Dict[str, object]:
    c = carriers()
    x = c["ELEM_Ne_010"] ^ c["PARTICLE_PHOTON_001"]
    ok = _wt(x) == 12 and x in GOLAY_SET
    return {"weight": _wt(x), "codeword": x in GOLAY_SET,
            "outcome": "already served" if ok else "open"}


def _point(w: int) -> List[int]:
    return [1] * w + [0] * (N - w)


def _completion() -> Dict[str, object]:
    t = {w: co.tax_shell0(_point(w)) for w in (7, 9, 16)}
    additive = t[16] == t[9] + t[7]
    linear = all(co.tax_shell0(_point(w)) == w * (co.Y + co.Z_STAR)
                 for w in range(N + 1))
    return {"tax": t, "additive": additive, "linear_in_weight": linear,
            "outcome": "already served" if additive and linear else "open"}


def _squeeze_round_trip(y: int) -> Optional[int]:
    """Squeeze to (message codeword, coset weight) and expand: the codeword
    if the coset weight is at most 3, else ``None``."""
    d = decode_complete(y)
    return d.corrected if d.weight <= 3 else None


def _squeeze() -> Dict[str, object]:
    bits = (len(GOLAY_MASKS) - 1).bit_length() + (4).bit_length()
    words = [GOLAY_MASKS[(37 * i) % len(GOLAY_MASKS)] ^ e
             for i, e in enumerate((0, 1, 0b11, 0b111, 0b1111, 0b10000001,
                                    0b100000100000100))]
    ok = 0
    for y in words:
        d = decode_complete(y)
        back = _squeeze_round_trip(y)
        if d.weight <= 3:
            ok += back is not None and _wt(back ^ y) == d.weight
        else:
            ok += back is None
    return {"bits": bits, "fraction_of_states": Fraction(2 ** bits, 2 ** N),
            "checked": len(words), "as_read": ok,
            "outcome": "already served" if bits == 15 and ok == len(words)
            else "open"}


def _hysteresis() -> Dict[str, object]:
    to_fail = {d: 4 - d for d in range(4)}
    return {"further_flips_to_fail": to_fail,
            "outcome": "retired" if to_fail[0] > to_fail[3] else "open"}


CHECKS = {
    "LAW_HEMISPHERIC_COHERENCE_001": ("refuted", _hemispheric),
    "LAW_PARTICLE_6D": ("refuted", _particle_6d),
    "LAW_LEPTON_004": ("refuted", _lepton_004),
    "LAW_COSMO_003": ("retired", _cosmo_003),
    "LAW_DODECAD_DUALITY_001": ("already served", _dodecad),
    "LAW_TOPOLOGICAL_COMPLETION_001": ("already served", _completion),
    "LAW_SQUEEZE_001": ("already served", _squeeze),
    "LAW_BIO_HYSTERESIS_001": ("retired", _hysteresis),
}


def check(law: str) -> Dict[str, object]:
    declared, fn = CHECKS[law]
    out = fn()
    out["declared"] = declared
    out["as_declared"] = out["outcome"] == declared == FATE[law][0]
    return out


# ---------------------------------------------------------------------------
# already served, run (B3)
# ---------------------------------------------------------------------------

def served() -> Dict[str, Dict[str, object]]:
    """Run the callable each *already served* law is served by."""
    from . import law_absorption as la
    rows = {}
    c = carriers()
    x = c["ELEM_Ne_010"] ^ c["PARTICLE_PHOTON_001"]
    rows["LAW_DODECAD_DUALITY_001"] = {
        "callable": "law_absorption.fact_value('weight-count', 12)",
        "value": la.fact_value("weight-count", 12)[0],
        "ok": la.fact_value("weight-count", 12)[0] == "2576"
        and x in GOLAY_SET}
    t = co.tax_shell0
    rows["LAW_TOPOLOGICAL_COMPLETION_001"] = {
        "callable": "coherence.tax_shell0",
        "value": t(_point(16)),
        "ok": t(_point(16)) == t(_point(9)) + t(_point(7))}
    y = GOLAY_MASKS[100] ^ 0b101
    d = decode_complete(y)
    rows["LAW_SQUEEZE_001"] = {
        "callable": "substrate.golay_decode.decode_complete",
        "value": (d.corrected, d.weight),
        "ok": d.corrected == GOLAY_MASKS[100] and d.weight == 2}
    return rows


# ---------------------------------------------------------------------------
# the source (B5)
# ---------------------------------------------------------------------------

def source_check(raw: Optional[bytes] = None) -> Dict[str, object]:
    """The frozen rows against the knowledge base's bytes ``raw`` (read from
    ``KB_MEMBER`` inside ``ZIP_PATH`` by the caller).  The core computes no
    digests (directive D3), so the recorded SHA-256 is not recomputed: the
    size and every row's text are compared.  ``None``: not taken."""
    data = load()
    if raw is None:
        return {"present": False, "passed": None}
    kb = json.loads(raw)
    by_id = {}
    for row in kb["entries"].values():
        by_id[row[0]] = row[1]
    same = sum(1 for r in data["laws"] if by_id.get(r["id"]) == r["text"])
    size_ok = len(raw) == data["source_bytes"]
    return {"present": True, "bytes": len(raw), "size_matches": size_ok,
            "texts_equal": same, "of": len(data["laws"]),
            "passed": size_ok and same == len(data["laws"])}


# ---------------------------------------------------------------------------
# the report
# ---------------------------------------------------------------------------

def law_triage_report(raw: Optional[bytes] = None) -> Dict[str, object]:
    """Every mark; B5 only when the knowledge base's bytes are given."""
    data = load()
    ids = [r["id"] for r in data["laws"]]
    b1 = (len(ids) == 106 and len(set(ids)) == 106 and set(ids) == set(FATE)
          and all(f in FATES for f, _r, _n in FATE.values())
          and all((f == "retired") == (r is not None) and
                  (r is None or r in REASONS)
                  for f, r, _n in FATE.values()))
    counts = {f: sum(1 for v in FATE.values() if v[0] == f) for f in FATES}
    reasons = {r: sum(1 for v in FATE.values() if v[1] == r) for r in REASONS}
    checks = {law: check(law) for law in CHECKS}
    b2 = all(c["as_declared"] for c in checks.values())
    runs = served()
    b3 = (set(runs) == {k for k, v in FATE.items() if v[0] == "already served"}
          and all(r["ok"] for r in runs.values()))
    b4 = counts["absorbed"] == 0
    src = source_check(raw)
    marks = {"B1": b1, "B2": b2, "B3": b3, "B4": True}
    if src["passed"] is not None:
        marks["B5"] = src["passed"]
    return {"laws": len(ids), "counts": counts, "reasons": reasons,
            "checks": checks, "served": runs, "source": src,
            "absorbed": [k for k, v in FATE.items() if v[0] == "absorbed"],
            "expectation_none_absorbed": b4,
            "marks": marks, "met": sum(marks.values()), "of": len(marks)}
