#!/usr/bin/env python3
"""One number, carried through every layer of the pipeline.

This is the worked example for ``studies/GLM_Complete_Number_Theory_Evidence.md``:
a single exact target enters at the top and every stage below is a *projection*
of it at a stated resolution.  Nothing here is quoted -- each stage recomputes
itself, so the document's transcript is whatever this script prints today.

The stages, and the layer each one reads at::

    target        an exact Fraction                      (the thing itself)
      |
      v  delta-sigma modulator, integer accumulator
    wobble        a bitstream b_n = floor((n+1)t) - floor(nt)
      |
      v  take the first 24 bits
    word          a 24-bit carrier                        (Hamming layer)
      |
      v  multiply by the parity-check matrix
    syndrome      12 bits                                 (coset layer)
      |
      v  complete nearest-codeword decoding
    codeword      one of 4,096, or a tie                  (code layer)
      |
      v  the MOG's 4 x 6 frame
    cells         six columns of four                     (MOG layer)
      |
      v  doubling the codeword into the integral model
    Leech point   24 integers, norm 32 when minimal       (lattice layer)
      |
      v  TAX = HW.Y + ||v||^2 / 8
    coherence     TAX, NRCI, regime                       (cost layer)

Run it with::

    cd overlay
    PYTHONPATH=. python3 -m glm_universal.examples.number_pipeline

Everything is exact: integers and :class:`~fractions.Fraction` only, no float
is constructed anywhere in this file (D7).
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Sequence, Tuple

from ..reasoning import coherence as coh
from ..reasoning import wobble as wb
from ..substrate import golay_decode as gd
from ..substrate import leech2, mog

__all__ = [
    "wobble_stage", "word_stage", "code_stage", "mog_stage", "leech_stage",
    "coherence_stage", "arithmetic_stage", "resolution_stage",
    "pipeline", "render",
]

#: The default worked target.  1/7 is the smallest odd prime reciprocal whose
#: binary period (3) is shorter than p - 1, so it is not full-reptend and the
#: number-theoretic layer has something to say that the wobble alone does not.
DEFAULT_TARGET = Fraction(1, 7)

#: How many bits of wobble the 24-bit carrier holds.
WIDTH = 24


# ---------------------------------------------------------------------------
# stage 1 -- the wobble
# ---------------------------------------------------------------------------
def wobble_stage(target: Fraction, steps: int = WIDTH) -> Dict[str, object]:
    """The delta-sigma bitstream of ``target``, and the closed form it obeys.

    ``Sturmian.dsOnes_eq_floor`` says the number of ones in ``N`` ticks is
    exactly ``floor(N * t)``; ``law_holds`` is that theorem, checked.
    """
    bits = wb.stream_bits(target, steps)
    law = wb.ones_count_law(target, steps)
    return {
        "target": target,
        "steps": steps,
        "bits": bits,
        "ones": law["measured"],
        "predicted_ones": law["predicted"],
        "law_holds": law["law_holds"],
        "density": law["density"],
        "longest_zero_run": wb.longest_run(bits, 0),
        "zero_run_bound": wb.run_bound(target),
        "transitions": wb.transitions(bits),
        "lean": "Sturmian.dsBit_eq_floor_diff, Sturmian.dsOnes_eq_floor",
    }


# ---------------------------------------------------------------------------
# stage 2 -- the 24-bit word
# ---------------------------------------------------------------------------
def word_stage(bits: Sequence[int]) -> Dict[str, object]:
    """Pack the first 24 bits into the carrier the substrate runs on."""
    mask = sum(1 << k for k, v in enumerate(bits) if v)
    return {
        "mask": mask,
        "hex": f"0x{mask:06X}",
        "binary": format(mask, "024b"),
        "hamming_weight": mog.popcount(mask),
        "support": tuple(k for k, v in enumerate(bits) if v),
    }


# ---------------------------------------------------------------------------
# stage 3 -- the code layer
# ---------------------------------------------------------------------------
def code_stage(mask: int) -> Dict[str, object]:
    """Syndrome, coset weight, and the complete decoding of the word."""
    code = mog.GolayCode()
    decoding = gd.decode_complete(mask)
    return {
        "syndrome": code.syndrome_int(mask),
        "syndrome_bits": format(code.syndrome_int(mask), "012b"),
        "is_codeword": code.is_codeword(mask),
        "coset_weight": gd.coset_weight(mask),
        "coset_leaders": len(gd.coset_leaders(mask)),
        "candidates": decoding.candidates,
        "codeword": (decoding.corrected if decoding.corrected is not None
                     else decoding.candidates[0]),
        "distance": decoding.weight,
        "status": decoding.status,
        "unique": decoding.corrected is not None,
        "guaranteed_decodable": decoding.guaranteed,
        "lean": "GolayBoundary.snap_boundary_at_three, Golay.Sextet.ties_card_eq_six",
    }


# ---------------------------------------------------------------------------
# stage 4 -- the MOG layer
# ---------------------------------------------------------------------------
def mog_stage(mask: int) -> Dict[str, object]:
    """The same word read as the Miracle Octad Generator's 4 x 6 frame."""
    frame = mog.frame(mask)
    return {
        "frame": frame,
        "column_weights": tuple(sum(row[c] for row in frame) for c in range(6)),
        "row_weights": tuple(sum(row) for row in frame),
        "hexacode_shadow": mog.hexacode_shadow(mask),
    }


# ---------------------------------------------------------------------------
# stage 5 -- the lattice layer
# ---------------------------------------------------------------------------
def _doubled(mask: int) -> Tuple[int, ...]:
    return tuple(2 if (mask >> k) & 1 else 0 for k in range(WIDTH))


def leech_stage(mask: int, codeword: int) -> Dict[str, object]:
    """Both the received word and its correction, doubled into the lattice.

    ``2c`` for a Golay codeword ``c`` is a lattice point, and it is a minimal
    vector -- norm 32 -- exactly when ``c`` is an octad
    (``Shortcut.Leech.golay_step_minimal_iff``).  The received word is *not* a
    codeword in general, and doubling it is then not a lattice point at all:
    that is the step this layer refuses, and the reason the code layer runs
    first.
    """
    received, corrected = _doubled(mask), _doubled(codeword)
    weight = mog.popcount(codeword)
    return {
        "received_point": received,
        "received_norm_squared": sum(v * v for v in received),
        "received_in_leech": leech2.in_leech(list(received)),
        "point": corrected,
        "norm_squared": sum(v * v for v in corrected),
        "in_leech": leech2.in_leech(list(corrected)),
        "codeword_weight": weight,
        "is_minimal": sum(v * v for v in corrected) == 32,
        "shape": "octad (2^8 0^16)" if weight == 8 else f"weight {weight}",
        "lean": "Shortcut.Leech.golay_step_minimal_iff, Shortcut.Leech.leech_min_norm",
    }


# ---------------------------------------------------------------------------
# stage 6 -- the cost layer
# ---------------------------------------------------------------------------
def coherence_stage(point: Sequence[int]) -> Dict[str, object]:
    """TAX, NRCI and the regime of the carrier, at the binary layer.

    ``TAX(v) = HW(v) . Y + ||v||^2 / 8`` with ``Y`` carried as the exact
    15-digit rational of ``reasoning/coherence.py``; the regime bands are
    ``Constants.regime_onBit_iff`` and its three companions.
    """
    weight = sum(1 for v in point if v)
    norm2 = sum(v * v for v in point)
    tax = weight * coh.Y + Fraction(norm2, 8)
    nrci = coh.B / (coh.B + tax)
    if tax <= Fraction(5, 2):
        regime = "onBit"
    elif tax <= Fraction(10):
        regime = "coherent"
    elif tax <= Fraction(70, 3):
        regime = "transitional"
    else:
        regime = "subcoherent"
    return {
        "hamming_weight": weight,
        "norm_squared": norm2,
        "tax": tax,
        "tax_decimal": coh.decimal_str(tax, 6),
        "nrci": nrci,
        "nrci_decimal": coh.decimal_str(nrci, 6),
        "regime": regime,
        "lean": "Constants.tax_nonneg, Constants.nrci_eq_one_iff, Constants.regime_onBit_iff",
    }


# ---------------------------------------------------------------------------
# stage 7 -- back up to arithmetic
# ---------------------------------------------------------------------------
def _multiplicative_order_of_two(modulus: int) -> int:
    order, value = 1, 2 % modulus
    while value != 1:
        value = value * 2 % modulus
        order += 1
    return order


def arithmetic_stage(target: Fraction) -> Dict[str, object]:
    """What the *number* layer knows that no carrier below it can see.

    For ``t = 1/p`` with ``p`` odd, the orbit of the doubling map is periodic
    with period ``ord_p(2)`` and never reaches zero
    (``Mantissa.oddOrbit_periodic``, ``Mantissa.oddOrbit_ne_zero``), while for a
    dyadic target it dies in ``k`` steps (``Mantissa.dyadicOrbit_collapses``).
    """
    denominator = target.denominator
    odd_part, twos = denominator, 0
    while odd_part % 2 == 0:
        odd_part //= 2
        twos += 1
    if odd_part == 1:
        return {
            "class": "dyadic",
            "steps_to_zero": twos,
            "binary_period": None,
            "full_reptend": False,
            "lean": "Mantissa.dyadicOrbit_collapses",
        }
    order = _multiplicative_order_of_two(odd_part)
    return {
        "class": "odd-denominator",
        "steps_to_zero": None,
        "binary_period": order,
        "full_reptend": order == odd_part - 1,
        "odd_part": odd_part,
        "lean": "Mantissa.oddOrbit_periodic, Mantissa.exists_period",
    }


# ---------------------------------------------------------------------------
# stage 8 -- the resolution the word is read at
# ---------------------------------------------------------------------------
def resolution_stage(target: Fraction, width: int = WIDTH,
                     search: int = 400) -> Dict[str, object]:
    """A second target with the *same* 24-bit word, separated one layer up.

    This is the positioning note made concrete: the 24-bit carrier is a
    projection at a stated resolution, and two different numbers can share it.
    Widening the window separates them, so the collision is a property of the
    reading and not of the substrate.
    """
    mine = wb.stream_bits(target, width)
    for denominator in range(2, search):
        for numerator in range(1, denominator):
            other = Fraction(numerator, denominator)
            if other == target:
                continue
            if wb.stream_bits(other, width) != mine:
                continue
            wider = width
            while (wb.stream_bits(target, wider)
                   == wb.stream_bits(other, wider)) and wider < 8 * width:
                wider += 1
            return {
                "collision": other,
                "shared_width": width,
                "separated_at": wider,
                "separated": (wb.stream_bits(target, wider)
                              != wb.stream_bits(other, wider)),
            }
    return {"collision": None, "shared_width": width}


# ---------------------------------------------------------------------------
# the whole walk
# ---------------------------------------------------------------------------
def pipeline(target: Fraction = DEFAULT_TARGET) -> Dict[str, object]:
    """Every stage above, for one target."""
    wobble = wobble_stage(target)
    word = word_stage(wobble["bits"])           # type: ignore[arg-type]
    code = code_stage(word["mask"])             # type: ignore[arg-type]
    cells = mog_stage(word["mask"])             # type: ignore[arg-type]
    lattice = leech_stage(word["mask"], code["codeword"])   # type: ignore[arg-type]
    cost = coherence_stage(
        tuple(1 if (word["mask"] >> k) & 1 else 0            # type: ignore[operator]
              for k in range(WIDTH)))
    return {
        "target": target,
        "wobble": wobble,
        "word": word,
        "code": code,
        "mog": cells,
        "leech": lattice,
        "coherence": cost,
        "arithmetic": arithmetic_stage(target),
        "resolution": resolution_stage(target),
    }


def render(target: Fraction = DEFAULT_TARGET) -> str:
    """The transcript the study document quotes."""
    r = pipeline(target)
    w, word, code = r["wobble"], r["word"], r["code"]      # type: ignore[index]
    cells, lat = r["mog"], r["leech"]                      # type: ignore[index]
    cost, arith = r["coherence"], r["arithmetic"]          # type: ignore[index]
    res = r["resolution"]                                  # type: ignore[index]
    lines: List[str] = []
    add = lines.append
    add(f"target                t = {target}   (exact Fraction, no float)")
    add("")
    add(f"1  wobble             {''.join(str(b) for b in w['bits'])}")
    add(f"   ones in {w['steps']} ticks   {w['ones']}   "
        f"= floor({w['steps']}t) = {w['predicted_ones']}   "
        f"law holds: {w['law_holds']}")
    add(f"   longest 0-run      {w['longest_zero_run']}   "
        f"(bound 1/t = {w['zero_run_bound']})")
    add("")
    add(f"2  word               {word['hex']}  = {word['binary']}")
    add(f"   Hamming weight     {word['hamming_weight']}   "
        f"support {word['support']}")
    add("")
    add(f"3  syndrome           {code['syndrome_bits']}  "
        f"({code['syndrome']})")
    add(f"   coset weight       {code['coset_weight']}   "
        f"leaders {code['coset_leaders']}   "
        f"unique reading: {code['unique']}")
    add(f"   nearest codeword   0x{code['codeword']:06X}   "
        f"at distance {code['distance']}")
    add("")
    add("4  MOG frame          " + "  ".join(
        "".join(str(v) for v in row) for row in cells["frame"]))
    add(f"   column weights     {cells['column_weights']}")
    add(f"   hexacode shadow    {cells['hexacode_shadow']}")
    add("")
    add(f"5  2 x received       norm^2 = {lat['received_norm_squared']}   "
        f"in Leech: {lat['received_in_leech']}")
    add(f"   2 x codeword       norm^2 = {lat['norm_squared']}   "
        f"in Leech: {lat['in_leech']}   minimal: {lat['is_minimal']}   "
        f"shape: {lat['shape']}")
    add("")
    add(f"6  TAX of the word    {cost['tax_decimal']}   "
        f"NRCI {cost['nrci_decimal']}   regime {cost['regime']}")
    add("")
    add(f"7  arithmetic layer   class {arith['class']}   "
        f"binary period {arith['binary_period']}   "
        f"full reptend: {arith['full_reptend']}")
    add("")
    if res["collision"] is not None:
        add(f"8  resolution         {res['collision']} shares the "
            f"{res['shared_width']}-bit word, and separates at "
            f"{res['separated_at']} ticks")
    else:
        add(f"8  resolution         no other target below the search bound "
            f"shares the {res['shared_width']}-bit word")
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover
    print(render())
