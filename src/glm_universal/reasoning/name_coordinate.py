"""``glm_universal.reasoning.name_coordinate`` -- a coordinate for the name.

What this module is
-------------------
:mod:`~glm_universal.reasoning.escalation` ran the layer stack on every named
object of every shipped register and found a **resolution ceiling**: 1,040
entries occupy 757 distinct carriers, so 283 of them share a carrier with
another entry and *no* layer can tell those apart -- a layer's view is a
function of the carrier, and the carrier is the same.  104 collision classes,
every one of them inside a single register, the largest being 78 dimensionless
physics quantities.

The finding was stated there as a diagnosis: *what is missing is a coordinate
for the name, not a finer layer*.  This module supplies the coordinate and
measures what it buys, which is a different question from whether it can be
supplied.  Three things come out of it, and the second is the point:

1. **An exact, injective name coordinate lifts the ceiling completely** --
   1,040 of 1,040, from any layer at all, the 24-bit substrate included.  That
   is not a discovery: ``GLM.Info.namedResolution_of_injective`` says it is
   forced.  It is worth having as a number only because it fixes what the
   coordinate *is*: an **address**, in the sense of directive D3, and not a
   measurement.  Nothing about a quantity's meaning is being added.
2. **A bounded coordinate is where the measurement lives.**  Reduce the name
   to ``b`` bits and the ceiling comes back gradually, and only inside the
   carrier collision classes -- two entries with different carriers are
   already separated, so a name collision between them costs nothing.  The
   sweep below reports, for each width, how many entries remain unreachable.
   ``GLM.Info.card_le_of_codeInjOn`` is the floor under it: a class of 78
   entries sharing a carrier cannot be separated by fewer than 78 codes, so
   at least ⌈log₂ 78⌉ = 7 bits are necessary whatever the reduction does.
3. **The control decides whether it is the name that is doing the work.**
   A coordinate is not informative merely by existing.  The register label is
   also a coordinate computed from the entry, and it recovers **none** of the
   283, because every collision class lies inside one register.  The first
   letter and the name's length are coordinates too, and they recover part.
   Reporting those beside the name coordinate is what keeps the claim from
   being "one more coordinate helps".

Exactness
---------
Every coordinate here is an integer computed from the entry's own name by
integer arithmetic -- no float, no hash library, nothing stored beside the
entry.  ``name_code`` is ``int.from_bytes`` of the UTF-8 bytes behind a
leading ``0x01``, which is injective because the leading byte fixes the
length band; the bounded codes are that integer reduced, either by taking its
low bits or modulo the largest prime below the bound.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from ..derived import memo
from . import escalation as esc

__all__ = [
    "BIT_WIDTHS", "SCHEMES", "CONTROLS",
    "name_code", "low_bits_code", "prime_mod_code", "largest_prime_below",
    "coordinate_function", "named_ceiling", "bit_sweep", "control_row",
    "name_report",
]


#: The widths the sweep reports, in bits.  ``0`` is the constant coordinate --
#: one code for every name -- and is in the list so that the sweep contains
#: its own null model.
BIT_WIDTHS: Tuple[int, ...] = (0, 4, 7, 8, 10, 12, 14, 16, 20, 24)

#: The two reductions of the exact name code to ``b`` bits.
SCHEMES: Tuple[str, ...] = ("low_bits", "prime_mod")

#: The coordinates that are *not* the name, measured beside it.  Each is
#: computed from the entry and nothing else, exactly as the rule requires; the
#: question the report asks is how much of the ceiling each one lifts.
CONTROLS: Tuple[str, ...] = ("constant", "register", "initial", "length")


# ===========================================================================
# 1.  THE CODES
# ===========================================================================

def name_code(name: str) -> int:
    """The exact integer a name is, and an injective function of it.

    The UTF-8 bytes of the name behind a leading ``0x01``, read as a
    big-endian integer.  The leading byte puts a name of ``L`` bytes in
    ``[256**L, 2*256**L)``, so names of different lengths land in disjoint
    bands and names of the same length differ in some byte: the map is
    injective, which :func:`name_report` re-checks on the shipped corpus
    rather than assuming.
    """
    return int.from_bytes(b"\x01" + name.encode("utf-8"), "big")


def largest_prime_below(bound: int) -> int:
    """The largest prime strictly below ``bound``, by trial division.

    Deterministic and exact.  ``bound`` here is always a power of two no
    larger than 2**24, so the search is short.
    """
    if bound < 3:
        raise ValueError("largest_prime_below: no prime below 2")
    candidate = bound - 1
    while candidate >= 2:
        if _is_prime(candidate):
            return candidate
        candidate -= 1
    raise ValueError("largest_prime_below: no prime found")   # pragma: no cover


def _is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    factor = 3
    while factor * factor <= n:
        if n % factor == 0:
            return False
        factor += 2
    return True


def low_bits_code(name: str, bits: int) -> int:
    """The bottom ``bits`` bits of the name code: the tail of the name.

    The cheapest possible reduction, and a deliberately unmixed one -- two
    names with the same last few characters agree in it.  It is in the sweep
    so that the *choice* of reduction is measured rather than assumed
    irrelevant.
    """
    if bits < 0:
        raise ValueError("low_bits_code: bits must be non-negative")
    if bits == 0:
        return 0
    return name_code(name) % (1 << bits)


def prime_mod_code(name: str, bits: int) -> int:
    """The name code modulo the largest prime below ``2**bits``.

    Still integer arithmetic and still a function of the name alone, but it
    mixes the whole name rather than its tail.
    """
    if bits < 0:
        raise ValueError("prime_mod_code: bits must be non-negative")
    if bits < 2:
        return 0
    return name_code(name) % largest_prime_below(1 << bits)


def coordinate_function(kind: str, bits: int = 0
                        ) -> Callable[[esc.RegisterCarrier], object]:
    """One coordinate, as a function of a whole register entry.

    ``kind`` is a scheme name, a control name, or ``\"exact\"`` for the
    injective code.  Every one of them reads the entry and nothing else.
    """
    if kind == "exact":
        return lambda entry: name_code(entry.name)
    if kind == "low_bits":
        return lambda entry: low_bits_code(entry.name, bits)
    if kind == "prime_mod":
        return lambda entry: prime_mod_code(entry.name, bits)
    if kind == "constant":
        return lambda entry: 0
    if kind == "register":
        return lambda entry: entry.register
    if kind == "initial":
        return lambda entry: entry.name[:1]
    if kind == "length":
        return lambda entry: len(entry.name)
    raise KeyError(f"name_coordinate: no coordinate called {kind!r}")


# ===========================================================================
# 2.  WHAT A COORDINATE BUYS
# ===========================================================================

@dataclass(frozen=True)
class CeilingRow:
    """What one coordinate does to the ceiling, measured."""

    coordinate: str
    bits: Optional[int]
    codes_used: int
    entries: int
    distinct: int
    unreachable: int
    collision_classes: int
    largest_class: int
    recovered: int
    violations: int

    def as_dict(self) -> Dict[str, object]:
        return {
            "coordinate": self.coordinate,
            "bits": self.bits,
            "codes_used": self.codes_used,
            "entries": self.entries,
            "distinct": self.distinct,
            "unreachable": self.unreachable,
            "collision_classes": self.collision_classes,
            "largest_class": self.largest_class,
            "recovered": self.recovered,
            "violations": self.violations,
        }


def named_ceiling(entries: Sequence[esc.RegisterCarrier],
                  coordinate: Callable[[esc.RegisterCarrier], object],
                  label: str = "", bits: Optional[int] = None) -> CeilingRow:
    """Re-run the ceiling measurement with one coordinate added beside the carrier.

    The reading is the pair ``(carrier, code)``, so it is a *widening* of the
    carrier reading in exactly the sense the layer work uses: it can split a
    class and it can never merge two.  That half needs no check -- the carrier
    is literally part of the key, and ``GLM.Info.namedLayer_refines_entryLayer``
    is the argument.  Counting merges here would be counting zero by
    construction, which is worth nothing.

    What *is* worth checking, and is checked, is the other half of the
    admission rule: the coordinate must be computable **from the entry**, and
    not stored beside it or read off the surrounding traversal.  Every
    coordinate is therefore evaluated twice, the second time with the entries
    visited in the opposite order, and ``violations`` counts the entries whose
    two values disagree.  A coordinate that consults anything but its argument
    -- a counter, a cursor, a clock -- shows up there.
    """
    plain: Dict[Tuple[Fraction, ...], List[int]] = {}
    named: Dict[Tuple[object, object], List[int]] = {}
    codes = set()
    first: List[object] = []
    for i, entry in enumerate(entries):
        code = coordinate(entry)
        first.append(code)
        codes.add(code)
        plain.setdefault(entry.carrier, []).append(i)
        named.setdefault((entry.carrier, code), []).append(i)
    plain_unreachable = len(entries) - len(plain)
    collisions = [g for g in named.values() if len(g) > 1]
    violations = 0
    for i in reversed(range(len(entries))):
        if coordinate(entries[i]) != first[i]:
            violations += 1
    return CeilingRow(
        coordinate=label or "coordinate",
        bits=bits,
        codes_used=len(codes),
        entries=len(entries),
        distinct=len(named),
        unreachable=len(entries) - len(named),
        collision_classes=len(collisions),
        largest_class=max((len(g) for g in collisions), default=0),
        recovered=plain_unreachable - (len(entries) - len(named)),
        violations=violations,
    )


def bit_sweep(entries: Sequence[esc.RegisterCarrier],
              scheme: str,
              widths: Sequence[int] = BIT_WIDTHS) -> List[Dict[str, object]]:
    """The ceiling as a function of how many bits of the name are kept."""
    out: List[Dict[str, object]] = []
    for bits in widths:
        row = named_ceiling(entries, coordinate_function(scheme, bits),
                            label=scheme, bits=bits)
        out.append(row.as_dict())
    return out


def control_row(entries: Sequence[esc.RegisterCarrier],
                kind: str) -> Dict[str, object]:
    """One control coordinate, measured the same way as the name."""
    return named_ceiling(entries, coordinate_function(kind),
                         label=kind, bits=None).as_dict()


def _first_sufficient(rows: Sequence[Dict[str, object]]) -> Optional[int]:
    """The narrowest width in a sweep that leaves nothing unreachable."""
    for row in rows:
        if row["unreachable"] == 0:
            return int(row["bits"])          # type: ignore[arg-type]
    return None


def _minimum_bits_forced(largest_class: int) -> int:
    """⌈log₂ n⌉ -- the width the pigeonhole theorem forces, by integer search."""
    bits = 0
    while (1 << bits) < largest_class:
        bits += 1
    return bits


# ===========================================================================
# 3.  THE REPORT
# ===========================================================================

@memo
def name_report() -> Dict[str, object]:
    """The whole study, recomputed.  Nothing here is quoted from a document."""
    entries = esc.register_carriers()
    plain = esc.resolution_ceiling(entries)
    exact = named_ceiling(entries, coordinate_function("exact"),
                          label="exact", bits=None)

    names = [e.name for e in entries]
    codes = [name_code(n) for n in names]
    injective_on_corpus = len(set(codes)) == len(set(names))

    substrate = esc.keyed_resolution("substrate", [e.carrier for e in entries])
    substrate_named = len({(esc.class_key("substrate", e.carrier),
                            name_code(e.name)) for e in entries})

    sweeps = {scheme: bit_sweep(entries, scheme) for scheme in SCHEMES}
    controls = [control_row(entries, kind) for kind in CONTROLS]

    largest = int(plain["largest_class_size"])
    return {
        "entries": len(entries),
        "registers": esc.register_sizes(entries),
        "before": {
            "distinct_carriers": plain["distinct_carriers"],
            "unreachable": plain["unreachable"],
            "collision_classes": plain["collision_classes"],
            "within_register": plain["within_register"],
            "cross_register": plain["cross_register"],
            "largest_class_size": largest,
            "largest_class_register": plain["largest_class_register"],
        },
        "exact": exact.as_dict(),
        "code_injective_on_corpus": injective_on_corpus,
        "distinct_names": len(set(names)),
        "substrate_resolution": substrate,
        "substrate_resolution_named": substrate_named,
        "sweeps": sweeps,
        "sufficient_bits": {scheme: _first_sufficient(sweeps[scheme])
                            for scheme in SCHEMES},
        "forced_bits": _minimum_bits_forced(largest),
        "controls": controls,
        "control_recovered": {row["coordinate"]: row["recovered"]
                              for row in controls},
    }
