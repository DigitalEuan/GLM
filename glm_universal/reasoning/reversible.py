"""``glm_universal.reasoning.reversible`` -- Part V of the unification blueprint.

The blueprint (`source_material/glm_unification_blueprint.md`, Part V) asks for three things
that the package did not have:

* a **read channel** comparison -- standard binary counting against the
  binary reflected Gray code (BRGC), measured by how much a step disturbs
  the carrier;
* **logically reversible gates** -- Toffoli (CCNOT) and Fredkin (CSWAP) run
  on the 24 coordinates, so that a semantic operation erases nothing and
  therefore dissipates nothing under Landauer's principle;
* **topological defect storage** -- information carried as *kinks* in a
  circular 24-coordinate string rather than as the values at fixed
  coordinates.

Everything here is exact: integers and :class:`~fractions.Fraction` only, no
float is ever constructed, nothing is sampled, no seed is used.  Every figure
this module reports is recomputed from the definitions by
:func:`reversible_report`, and the runtime reaches it as
``report reversible``.

What the blueprint claims, and what is actually true
----------------------------------------------------
The module is written so that each of the blueprint's Part V claims is a
computation with a verdict rather than a sentence.  Three of them are exactly
right, and three are not; the verdicts live in :func:`blueprint_claims` and
each one names the figure that settles it.

============================================  ==========================
blueprint claim                               verdict
============================================  ==========================
BRGC changes exactly one bit per step         confirmed
BRGC transition entropy is exactly zero       confirmed (as a point mass)
BRGC halves the cumulative symmetry TAX       refuted -- it does better
Toffoli and Fredkin are self-inverse          confirmed
syndrome weight is conserved by the gates     refuted -- it moves
a single bit flip changes the kink count      refuted -- it can leave it
by exactly +/-2                               unchanged
============================================  ==========================

The two refutations of "exactly" claims are not failures of the design; both
are cases where the true statement is sharper than the claimed one.  The gate
finding is a real correction: the gates conserve *information*, which is what
reversibility means, and they do not conserve *position in the Golay code*,
which is a different property that the blueprint conflates with it.

The formal counterpart is ``RequestProject/GLM/Reversible.lean``, which proves
the Gray-code, gate and kink statements as theorems over arbitrary widths
rather than checking them at width 24.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Mapping, Sequence, Tuple

__all__ = [
    "N",
    "TAX_SCALE",
    "gray",
    "gray_inverse",
    "bits_of",
    "int_of",
    "hamming",
    "counting_sequence",
    "transition_counts",
    "symmetry_tax",
    "flip_distribution",
    "distribution_variance",
    "channel_report",
    "BLOCKS_8x3",
    "BLOCKS_MOG",
    "toffoli",
    "fredkin",
    "apply_gate_blocks",
    "round_forward",
    "round_backward",
    "gate_period",
    "syndrome_weight",
    "reversibility_report",
    "kinks",
    "rotate",
    "kink_rotation_orbit",
    "flip_deltas",
    "soliton_report",
    "blueprint_claims",
    "reversible_report",
]


#: The substrate width: 24 coordinates.
N = 24

#: The blueprint prices a disturbance of Hamming size ``d`` at ``d^2 / 32``
#: -- the same TAX scale Stage 3 of the carrier engine uses, where ``32`` is
#: the squared minimal norm of the Leech lattice in the Construction-C
#: normalisation.
TAX_SCALE = 32


# ═════════════════════════════════════════════════════════════════════════
# 1.  BIT VECTORS, WITHOUT FLOATS AND WITHOUT XOR OUTSIDE F2
# ═════════════════════════════════════════════════════════════════════════

def bits_of(n: int, width: int) -> Tuple[int, ...]:
    """``n`` as ``width`` bits, most significant first."""
    if n < 0:
        raise ValueError(f"bits_of: negative value {n}")
    if n >= 1 << width:
        raise ValueError(f"bits_of: {n} does not fit in {width} bits")
    return tuple((n >> (width - 1 - i)) & 1 for i in range(width))


def int_of(bits: Sequence[int]) -> int:
    """The integer a most-significant-first bit vector spells."""
    value = 0
    for bit in bits:
        if bit not in (0, 1):
            raise ValueError(f"int_of: {bit!r} is not a bit")
        value = (value << 1) | bit
    return value


def hamming(a: Sequence[int], b: Sequence[int]) -> int:
    """The number of coordinates at which two equal-length vectors differ."""
    if len(a) != len(b):
        raise ValueError(f"hamming: length {len(a)} against {len(b)}")
    return sum(1 for x, y in zip(a, b) if x != y)


def gray(n: int) -> int:
    """The binary reflected Gray code of ``n``.

    Defined without appealing to a machine XOR: the ``i``-th Gray bit is the
    sum mod 2 of the ``i``-th and ``(i+1)``-th binary bits, which is addition
    in F2 and therefore inside the UBP's one exception to the XOR ban.
    """
    if n < 0:
        raise ValueError(f"gray: negative value {n}")
    out = 0
    prev = 0
    for shift in reversed(range(n.bit_length() + 1)):
        bit = (n >> shift) & 1
        out = (out << 1) | ((bit + prev) % 2)
        prev = bit
    return out


def gray_inverse(g: int) -> int:
    """The index whose Gray code is ``g``; inverse of :func:`gray`."""
    if g < 0:
        raise ValueError(f"gray_inverse: negative value {g}")
    out = 0
    run = 0
    for shift in reversed(range(g.bit_length() + 1)):
        run = (run + ((g >> shift) & 1)) % 2
        out = (out << 1) | run
    return out


# ═════════════════════════════════════════════════════════════════════════
# 2.  THE READ CHANNEL: BINARY COUNTING AGAINST BRGC
# ═════════════════════════════════════════════════════════════════════════

def counting_sequence(width: int, code: str = "binary",
                      cyclic: bool = True) -> Tuple[Tuple[int, ...], ...]:
    """Every state a ``width``-bit counter passes through, in order.

    ``code`` is ``"binary"`` for straight binary counting or ``"gray"`` for
    the binary reflected Gray code.  With ``cyclic`` the sequence returns to
    its starting state, so the last step is the wrap-around -- which is where
    binary counting is at its worst and BRGC is not.
    """
    if code not in ("binary", "gray"):
        raise ValueError(f"counting_sequence: unknown code {code!r}")
    span = 1 << width
    order = range(span) if code == "binary" else (gray(i) for i in range(span))
    states = [bits_of(value, width) for value in order]
    if cyclic:
        states.append(states[0])
    return tuple(states)


def transition_counts(states: Sequence[Sequence[int]]) -> Tuple[int, ...]:
    """The Hamming size of each step of a walk through bit vectors."""
    return tuple(hamming(states[i], states[i + 1])
                 for i in range(len(states) - 1))


def symmetry_tax(counts: Sequence[int]) -> Fraction:
    """The cumulative symmetry TAX of a walk: the sum of ``d^2 / 32``."""
    return sum((Fraction(d * d, TAX_SCALE) for d in counts), Fraction(0))


def flip_distribution(counts: Sequence[int]) -> Dict[int, Fraction]:
    """The exact rational distribution of a walk's step sizes."""
    total = len(counts)
    tally: Dict[int, int] = {}
    for d in counts:
        tally[d] = tally.get(d, 0) + 1
    return {d: Fraction(k, total) for d, k in sorted(tally.items())}


def distribution_variance(distribution: Mapping[int, Fraction]) -> Fraction:
    """The exact variance of a rational distribution over the integers.

    A distribution has zero Shannon entropy exactly when it is a point mass,
    and a distribution over the integers is a point mass exactly when its
    variance is zero.  Reporting the variance is therefore the entropy claim
    stated without ever taking a logarithm -- which is what lets this module
    settle the blueprint's "entropy exactly 0.0000" without a float.
    """
    mean = sum((Fraction(d) * p for d, p in distribution.items()),
               Fraction(0))
    return sum(((Fraction(d) - mean) ** 2 * p
                for d, p in distribution.items()), Fraction(0))


def channel_report(width: int = 8) -> Dict[str, object]:
    """Binary counting against BRGC over one full ``width``-bit cycle.

    Both walks visit all ``2**width`` states and return to the start, so they
    are compared over the same work.  Every figure is exact.
    """
    if width < 1:
        raise ValueError(f"channel_report: width must be positive, got {width}")
    span = 1 << width
    out: Dict[str, object] = {"width": width, "states": span,
                              "steps": span}
    for code in ("binary", "gray"):
        counts = transition_counts(counting_sequence(width, code))
        dist = flip_distribution(counts)
        out[code] = {
            "flips": sum(counts),
            "max_step": max(counts),
            "tax": symmetry_tax(counts),
            "distribution": dist,
            "variance": distribution_variance(dist),
            "zero_entropy": distribution_variance(dist) == 0,
        }
    binary = out["binary"]  # type: ignore[index]
    gray_walk = out["gray"]  # type: ignore[index]
    out["flip_ratio"] = Fraction(gray_walk["flips"], binary["flips"])
    out["tax_ratio"] = Fraction(gray_walk["tax"]) / Fraction(binary["tax"])
    # The closed forms, stated so the test suite can check them rather than
    # re-measure them: over a full cycle binary counting flips 2**(w+1) - 2
    # bits and BRGC flips 2**w, so the ratio is 2**w / (2**(w+1) - 2) -- above
    # one half for every finite width, and one half only in the limit.
    out["closed_form_binary_flips"] = 2 * span - 2
    out["closed_form_gray_flips"] = span
    out["halving_exact"] = out["flip_ratio"] == Fraction(1, 2)
    out["gray_at_least_as_cheap"] = (gray_walk["tax"] <= binary["tax"]
                                     and gray_walk["flips"]
                                     <= binary["flips"])
    return out


# ═════════════════════════════════════════════════════════════════════════
# 3.  REVERSIBLE GATES ON THE 24 COORDINATES
# ═════════════════════════════════════════════════════════════════════════

#: The blueprint's partition: eight blocks of three coordinates.  It is a
#: partition of the 24 coordinates, but it is *not* the MOG's own column
#: structure -- the MOG frame is 4 rows by 6 columns, so its columns hold
#: four coordinates each, not three.  Both partitions are offered, and
#: :func:`reversibility_report` runs the gates on both.
BLOCKS_8x3: Tuple[Tuple[int, int, int], ...] = tuple(
    (3 * b, 3 * b + 1, 3 * b + 2) for b in range(8))

#: The MOG's six columns, four coordinates each, in the substrate's own
#: coordinate order.  A three-bit gate acts on the first three of each.
BLOCKS_MOG: Tuple[Tuple[int, ...], ...] = tuple(
    tuple(4 * c + r for r in range(4)) for c in range(6))


def toffoli(triple: Sequence[int]) -> Tuple[int, int, int]:
    """CCNOT: ``[c1, c2, c3] -> [c1, c2, c3 + c1*c2 mod 2]``."""
    if len(triple) != 3:
        raise ValueError(f"toffoli: expected 3 bits, got {len(triple)}")
    c1, c2, c3 = (int(b) for b in triple)
    for b in (c1, c2, c3):
        if b not in (0, 1):
            raise ValueError(f"toffoli: {b!r} is not a bit")
    return (c1, c2, (c3 + c1 * c2) % 2)


def fredkin(triple: Sequence[int]) -> Tuple[int, int, int]:
    """CSWAP: swap the last two bits when the first is set."""
    if len(triple) != 3:
        raise ValueError(f"fredkin: expected 3 bits, got {len(triple)}")
    c1, c2, c3 = (int(b) for b in triple)
    for b in (c1, c2, c3):
        if b not in (0, 1):
            raise ValueError(f"fredkin: {b!r} is not a bit")
    return (c1, c3, c2) if c1 == 1 else (c1, c2, c3)


def apply_gate_blocks(vector: Sequence[int], gate, blocks) -> Tuple[int, ...]:
    """Apply a three-bit ``gate`` to the first three indices of each block."""
    out = list(vector)
    for block in blocks:
        idx = tuple(block[:3])
        got = gate(tuple(out[i] for i in idx))
        for i, bit in zip(idx, got):
            out[i] = bit
    return tuple(out)


def round_forward(vector: Sequence[int],
                  blocks=BLOCKS_8x3) -> Tuple[int, ...]:
    """One forward round: Toffoli then Fredkin on every block."""
    return apply_gate_blocks(apply_gate_blocks(vector, toffoli, blocks),
                             fredkin, blocks)


def round_backward(vector: Sequence[int],
                   blocks=BLOCKS_8x3) -> Tuple[int, ...]:
    """The inverse round: Fredkin then Toffoli, each being its own inverse."""
    return apply_gate_blocks(apply_gate_blocks(vector, fredkin, blocks),
                             toffoli, blocks)


def gate_period(blocks=BLOCKS_8x3) -> int:
    """The order of :func:`round_forward` as a permutation of one block.

    Worth knowing, and not what "self-inverse" would suggest: each gate is an
    involution, but their *composition* is not, so undoing a run of rounds
    means running the inverse round, not running the same round again.
    """
    del blocks
    period = 1
    for start in range(8):
        state = bits_of(start, 3)
        seen = state
        k = 0
        while True:
            seen = round_forward(seen, ((0, 1, 2),))
            k += 1
            if seen == state:
                break
        period = period * k // _gcd(period, k)
    return period


def _gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a


def syndrome_weight(vector: Sequence[int]) -> int:
    """The Golay syndrome weight of a 24-bit vector, from the substrate."""
    from ..reasoning import coherence as co
    return co._golay_syndrome_weight(tuple(vector))


#: A deterministic 24-bit carrier to run the gates on.  No seed and no
#: randomness: it is the binary expansion of a fixed integer, chosen so that
#: it is *not* a Golay codeword (its syndrome weight is positive), because a
#: codeword would make the conservation question vacuous.
DEMO_CARRIER: Tuple[int, ...] = bits_of(0b101100111000110101001110, 24)


def reversibility_report(rounds: int = 100,
                         blocks=BLOCKS_8x3) -> Dict[str, object]:
    """Run a carrier forward through ``rounds`` rounds and back again.

    Reports the three things the blueprint asserts -- byte-identical return,
    gate self-inverseness, and conservation -- and separates the two that
    hold from the one that does not.
    """
    if rounds < 1:
        raise ValueError(f"reversibility_report: rounds must be positive")
    start = DEMO_CARRIER
    state = start
    syndromes = [syndrome_weight(state)]
    weights = [sum(state)]
    for _ in range(rounds):
        state = round_forward(state, blocks)
        syndromes.append(syndrome_weight(state))
        weights.append(sum(state))
    midpoint = state
    for _ in range(rounds):
        state = round_backward(state, blocks)
    gate_applications = 2 * rounds * len(blocks)

    involutive = all(
        toffoli(toffoli(bits_of(v, 3))) == bits_of(v, 3)
        and fredkin(fredkin(bits_of(v, 3))) == bits_of(v, 3)
        for v in range(8))
    bijective = (len({toffoli(bits_of(v, 3)) for v in range(8)}) == 8
                 and len({fredkin(bits_of(v, 3)) for v in range(8)}) == 8)

    return {
        "rounds": rounds,
        "blocks": len(blocks),
        "gate_applications": gate_applications,
        "start": start,
        "midpoint": midpoint,
        "returned": state,
        "hamming_to_start": hamming(state, start),
        "exact_return": state == start,
        "gates_involutive": involutive,
        "gates_bijective": bijective,
        "round_period": gate_period(blocks),
        "syndrome_start": syndromes[0],
        "syndrome_values": sorted(set(syndromes)),
        "syndrome_conserved": len(set(syndromes)) == 1,
        "hamming_weight_values": sorted(set(weights)),
        "hamming_weight_conserved": len(set(weights)) == 1,
    }


# ═════════════════════════════════════════════════════════════════════════
# 4.  TOPOLOGICAL DEFECTS: KINKS ON A CIRCULAR STRING
# ═════════════════════════════════════════════════════════════════════════

def kinks(vector: Sequence[int]) -> int:
    """The number of adjacent pairs that differ, counted around the circle."""
    n = len(vector)
    if n == 0:
        return 0
    return sum(1 for i in range(n) if vector[i] != vector[(i + 1) % n])


def rotate(vector: Sequence[int], k: int) -> Tuple[int, ...]:
    """``vector`` rotated left by ``k`` places."""
    n = len(vector)
    if n == 0:
        return tuple(vector)
    k %= n
    return tuple(vector[k:]) + tuple(vector[:k])


def kink_rotation_orbit(vector: Sequence[int]) -> Tuple[int, ...]:
    """The kink count of every rotation of ``vector``."""
    return tuple(kinks(rotate(vector, k)) for k in range(len(vector)))


def flip_deltas(vector: Sequence[int]) -> Dict[int, int]:
    """How the kink count moves when each single coordinate is flipped.

    The keys are the changes that occur and the values are how many of the
    coordinates produce them.
    """
    base = kinks(vector)
    tally: Dict[int, int] = {}
    for i in range(len(vector)):
        flipped = list(vector)
        flipped[i] = 1 - flipped[i]
        delta = kinks(flipped) - base
        tally[delta] = tally.get(delta, 0) + 1
    return dict(sorted(tally.items()))


def soliton_report(vector: Sequence[int] = DEMO_CARRIER) -> Dict[str, object]:
    """The kink invariant, measured rather than asserted.

    The rotation claim is checked on the given carrier; the flip claim is
    checked *exhaustively* over all 2**8 circular strings of length 8, which
    is what turns "changes by exactly +/-2" from a plausible sentence into a
    refuted one.
    """
    orbit = kink_rotation_orbit(vector)
    exhaustive: Dict[int, int] = {}
    for value in range(1 << 8):
        word = bits_of(value, 8)
        for delta, count in flip_deltas(word).items():
            exhaustive[delta] = exhaustive.get(delta, 0) + count
    parities = {kinks(bits_of(v, 8)) % 2 for v in range(1 << 8)}
    return {
        "length": len(vector),
        "kinks": kinks(vector),
        "rotation_orbit": orbit,
        "rotation_invariant": len(set(orbit)) == 1,
        "flip_deltas": flip_deltas(vector),
        "exhaustive_flip_deltas": dict(sorted(exhaustive.items())),
        "exhaustive_words": 1 << 8,
        "delta_always_two": set(exhaustive) == {-2, 2},
        "delta_in_minus_two_zero_two": set(exhaustive) <= {-2, 0, 2},
        "zero_delta_share": Fraction(exhaustive.get(0, 0),
                                     sum(exhaustive.values())),
        "kink_parities": sorted(parities),
        "kink_count_always_even": parities == {0},
    }


# ═════════════════════════════════════════════════════════════════════════
# 5.  THE BLUEPRINT'S PART V CLAIMS, EACH WITH A VERDICT
# ═════════════════════════════════════════════════════════════════════════

def blueprint_claims(width: int = 8, rounds: int = 100) -> Tuple[
        Dict[str, object], ...]:
    """Each Part V claim, the figure that settles it, and the verdict."""
    channel = channel_report(width)
    gray_walk = channel["gray"]      # type: ignore[index]
    binary = channel["binary"]       # type: ignore[index]
    gates = reversibility_report(rounds)
    solitons = soliton_report()

    return (
        {
            "claim": "BRGC changes exactly one bit per step",
            "verdict": "confirmed",
            "holds": gray_walk["max_step"] == 1,
            "figure": f"max step = {gray_walk['max_step']} bit over "
                      f"{channel['steps']} steps",
        },
        {
            "claim": "BRGC transition entropy is exactly zero",
            "verdict": "confirmed",
            "holds": bool(gray_walk["zero_entropy"]),
            "figure": f"step-size variance = {gray_walk['variance']}, so the "
                      f"distribution is a point mass and its entropy is 0",
        },
        {
            "claim": "BRGC dissipates exactly half the cumulative symmetry "
                     "TAX of binary counting",
            "verdict": "refuted -- it dissipates less than half",
            "holds": not channel["halving_exact"],
            "figure": f"TAX {gray_walk['tax']} against {binary['tax']}, "
                      f"ratio {channel['tax_ratio']}; in bit flips "
                      f"{gray_walk['flips']} against {binary['flips']}, "
                      f"ratio {channel['flip_ratio']} -- one half only in "
                      f"the limit",
        },
        {
            "claim": "Toffoli and Fredkin are self-inverse and bijective",
            "verdict": "confirmed",
            "holds": bool(gates["gates_involutive"]
                          and gates["gates_bijective"]),
            "figure": "checked on all 8 inputs of each gate",
        },
        {
            "claim": f"{rounds} forward rounds then {rounds} backward rounds "
                     f"return the carrier byte-identically",
            "verdict": "confirmed",
            "holds": bool(gates["exact_return"]),
            "figure": f"{gates['gate_applications']} gate applications, "
                      f"Hamming distance to start "
                      f"{gates['hamming_to_start']}",
        },
        {
            "claim": "the Golay syndrome weight is conserved throughout the "
                     "gate cycle",
            "verdict": "refuted -- reversibility does not fix the syndrome",
            "holds": not gates["syndrome_conserved"],
            "figure": f"syndrome weight takes the values "
                      f"{gates['syndrome_values']} during the run, starting "
                      f"at {gates['syndrome_start']}",
        },
        {
            "claim": "the kink count is invariant under rotation",
            "verdict": "confirmed",
            "holds": bool(solitons["rotation_invariant"]),
            "figure": f"all {solitons['length']} rotations give "
                      f"{solitons['kinks']} kinks",
        },
        {
            "claim": "a single bit flip changes the kink count by exactly "
                     "+/-2",
            "verdict": "refuted -- the change is in {-2, 0, +2}",
            "holds": (not solitons["delta_always_two"]
                      and bool(solitons["delta_in_minus_two_zero_two"])),
            "figure": f"over all {solitons['exhaustive_words']} circular "
                      f"8-bit words the deltas are "
                      f"{solitons['exhaustive_flip_deltas']}; a flip leaves "
                      f"the count unchanged in "
                      f"{solitons['zero_delta_share']} of cases",
        },
    )


def reversible_report(width: int = 8, rounds: int = 100) -> Dict[str, object]:
    """Everything Part V asks for, recomputed in one call."""
    claims = blueprint_claims(width, rounds)
    return {
        "channel": channel_report(width),
        "gates": reversibility_report(rounds),
        "solitons": soliton_report(),
        "claims": claims,
        "claim_count": len(claims),
        "claims_holding": sum(1 for c in claims if c["holds"]),
        "confirmed": sum(1 for c in claims
                         if str(c["verdict"]).startswith("confirmed")),
        "refuted": sum(1 for c in claims
                       if str(c["verdict"]).startswith("refuted")),
    }
