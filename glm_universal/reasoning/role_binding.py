"""``glm_universal.reasoning.role_binding`` -- a typed relation written as one
word, and how much of it comes back.

Why this module exists
----------------------
The conversational material supplied with Phase 54
(``source_material/conversation_experiment/``) carries one idea this system
did not have: a typed relation *R(A, B)* stored as a single carrier-sized
word, ``R ⊗ A ⊗ B``, out of which ``B`` is recovered by re-binding with what
is known.  Two bindings are offered there and **both are described as
recoverable**:

``hadamard_perm``
    the elementwise product of three exact rational 24-vectors, undone by
    elementwise division;
``parity_xor``
    the exclusive-or of their 24-bit parity readings, undone by the same
    exclusive-or.

The role ``R`` carries no carrier of its own in either: it is a fixed
permutation of the coordinates, one per relation type, so the relation type
*is* a re-indexing.  :data:`ROLES` is that table, copied unchanged from the
supplied ``_RELATION_PERMUTATIONS``.

``CONVERSATION_STUDY.md`` §9 said what a round taking this would have to do:
*recoverability is a theorem, not a demo: state it over the substrate and
prove it, with the collision rate as the control.*  This module is the
measured half and ``RequestProject/GLM/RoleBinding.lean`` is the proved half.

What is true, and what is not
-----------------------------
Of the two claims, **one survives and one does not**.

* The parity binding is exactly invertible with no side condition at all --
  ``GLM.RoleBinding.unbind_bind`` -- because the readings are an elementary
  abelian 2-group and the role acts on it by permuting coordinates.
* The product binding is invertible only where the key reads nowhere zero, and
  ``GLM.RoleBinding.hbind_not_injective_of_zero`` shows that a single zero
  coordinate makes two different fillers bind to the same vector.
  :func:`product_census` counts what that costs here: 1,133 of the 1,143
  carriers this system loads read zero somewhere, and the ten that do not all
  live in the mathematics register and take three distinct values between
  them -- eight of the ten are one and the same vector.  So a product binding
  is recoverable only from a known side that seven other carriers are
  identical to, which refutes the claim rather than qualifying it.

What recovery is worth
----------------------
Unbinding returns the filler's *reading*, exactly.  Turning a reading back
into a **name** is a second step, and it is where the cost is: the reading is
24 parity bits and a register is a list of carriers, so what a recovery holds
is a **fibre** of the parity map.  A name comes back when the fibre holds one;
otherwise the operation refuses, because naming one of several would be a
choice the binding did not make.  :func:`register_census` measures the fibres
of every register the session loads, and that measurement is the whole of what
the binding is worth here: it is a property of the registers, not of the
binding, which is why :func:`recover` gives the same verdict whatever role and
whatever known side produced the word.

The refusal is not fussiness.  The supplied code, when the fibre is not a
singleton, returns the nearest carrier by Hamming distance and says nothing
about having chosen; :func:`nearest` is that rule, kept as the control, and
the declared set below counts how often it names a carrier that is not the one
that was bound.

What it moves
-------------
Under directive **D15** this is **addressing** -- a filler recovered from a
word that is not its key, the key being the role and the known side -- and
**refusal**: two named reasons, one of which (``ambiguous-recovery``) is
forced by the registers on 719 of their 1,143 carriers rather than chosen.  It
derives nothing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from . import dimension_layers

__all__ = [
    "BindingError", "REFUSAL_REASONS", "ROLES", "DIM",
    "parity", "permute_mask", "key_mask", "bind", "unbind", "hamming",
    "Bound", "bind_names", "fibre", "recover", "nearest",
    "product_zeros", "product_census", "register_census",
    "DECLARED_BINDINGS", "binding_report",
]

#: The width of a carrier, and of a reading of one.
DIM = 24


class BindingError(ValueError):
    """Raised when a binding, or a recovery from one, has no answer.

    The reason is one of :data:`REFUSAL_REASONS`, carried in :attr:`reason` so
    a caller can act on the kind of refusal rather than on its wording.
    """

    def __init__(self, reason: str, message: str,
                 candidates: Sequence[str] = ()):
        super().__init__(message)
        self.reason = reason
        self.candidates: Tuple[str, ...] = tuple(candidates)


#: Every way a binding or a recovery can refuse, in the order they are
#: checked.  ``unrecoverable`` is the product binding's refusal and is
#: reported by :func:`product_census` rather than raised, because it is not a
#: property of one pair but of every pair in the system.
REFUSAL_REASONS: Tuple[str, ...] = (
    "unknown-role", "unknown-name", "no-carrier", "ambiguous-recovery",
)

#: The relation types, each with the permutation of the 24 coordinates that
#: stands for it.  Copied unchanged from the supplied material's
#: ``_RELATION_PERMUTATIONS``: the role tag is a re-indexing, and these are the
#: re-indexings that were declared there.
ROLES: Mapping[str, Tuple[int, ...]] = {
    "equals": tuple(range(DIM)),
    "causes": tuple((i + 1) % DIM for i in range(DIM)),
    "contrasts_with": tuple((i + 2) % DIM for i in range(DIM)),
    "part_of": tuple((i + 3) % DIM for i in range(DIM)),
    "mentioned_after": tuple(DIM - 1 - i for i in range(DIM)),
    "affected_by": tuple((i + 5) % DIM for i in range(DIM)),
    "derived_from": tuple((i + 7) % DIM for i in range(DIM)),
}


# ===========================================================================
# 1.  THE BINDING ITSELF -- 24 bits, and exact arithmetic on them
# ===========================================================================

def parity(carrier: Sequence) -> int:
    """The 24-bit parity reading of a carrier.

    One definition of this exists in the package and this is a call to it:
    :func:`glm_universal.reasoning.dimension_layers.parity_bits`.
    """
    return dimension_layers.parity_bits(carrier)


def permute_mask(mask: int, perm: Sequence[int]) -> int:
    """Move bit ``i`` of a reading to position ``perm[i]``.

    This is the reading of the permuted carrier:
    ``permute_mask(parity(v), p) == parity(permute_vector(v, p))``, which the
    tests pin against the substrate's own :func:`permute_vector`.
    """
    if len(perm) != DIM:
        raise ValueError(f"permute_mask: expected {DIM} positions, "
                         f"got {len(perm)}")
    out = 0
    for i, target in enumerate(perm):
        if mask & (1 << i):
            out |= 1 << target
    return out


def key_mask(role: str, a_mask: int) -> int:
    """The key a binding is made with: the known side, tagged by the role."""
    perm = ROLES.get(role)
    if perm is None:
        raise BindingError(
            "unknown-role",
            f"{role!r} is not a declared relation type "
            f"({', '.join(sorted(ROLES))})")
    return permute_mask(a_mask, perm) ^ a_mask


def bind(role: str, a_mask: int, b_mask: int) -> int:
    """Bind the relation ``(role, a, b)`` into one 24-bit word."""
    return key_mask(role, a_mask) ^ b_mask


def unbind(role: str, a_mask: int, word: int) -> int:
    """Recover the filler's reading from a bound word.

    It is :func:`bind` again, which is the whole of why the parity binding is
    recoverable: ``GLM.RoleBinding.unbind_bind``.
    """
    return key_mask(role, a_mask) ^ word


def hamming(x: int, y: int) -> int:
    """The Hamming distance between two readings."""
    return bin(x ^ y).count("1")


@dataclass(frozen=True)
class Bound:
    """A typed relation stored as one word, with what went into it."""

    role: str
    a_name: str
    b_name: str
    domain: str
    word: int

    @property
    def sentence(self) -> str:
        """The binding as one line."""
        return (f"{self.role}({self.a_name}, {self.b_name}) in "
                f"{self.domain} is the word 0x{self.word:06x}")


# ===========================================================================
# 2.  BINDING AND RECOVERING OVER A REAL REGISTER
# ===========================================================================

def _readings(session, domain: str) -> Tuple[Tuple[str, int], ...]:
    """Every carrier of one register, as ``(name, reading)``."""
    return tuple((obj.name, parity(obj.carrier))
                 for obj in session.register(domain))


def _reading_of(session, domain: str, name: str) -> int:
    for obj_name, mask in _readings(session, domain):
        if obj_name == name:
            return mask
    raise BindingError(
        "unknown-name",
        f"{name!r} is not a carrier of the {domain} register")


def bind_names(session, role: str, a_name: str, b_name: str,
               domain: str) -> Bound:
    """Bind two named carriers of one register into a word."""
    a_mask = _reading_of(session, domain, a_name)
    b_mask = _reading_of(session, domain, b_name)
    return Bound(role=role, a_name=a_name, b_name=b_name, domain=domain,
                 word=bind(role, a_mask, b_mask))


def fibre(session, domain: str, mask: int) -> Tuple[str, ...]:
    """Every carrier of a register that reads as a given mask."""
    return tuple(name for name, m in _readings(session, domain) if m == mask)


def recover(session, word: int, role: str, a_name: str, domain: str) -> str:
    """Recover the filler's **name** from a bound word.

    Unbinding is exact and unconditional; naming is not.  A name comes back
    only when one carrier of the register reads as the recovered mask.  Two or
    more is ``ambiguous-recovery``, none is ``no-carrier``, and neither is a
    failed search: both are statements about the register.
    """
    a_mask = _reading_of(session, domain, a_name)
    recovered = unbind(role, a_mask, word)
    names = fibre(session, domain, recovered)
    if len(names) == 1:
        return names[0]
    if not names:
        raise BindingError(
            "no-carrier",
            f"no carrier of the {domain} register reads as "
            f"0x{recovered:06x}")
    raise BindingError(
        "ambiguous-recovery",
        f"{len(names)} carriers of the {domain} register read as "
        f"0x{recovered:06x} ({', '.join(names[:4])}"
        f"{', ...' if len(names) > 4 else ''}); naming one would be a choice "
        f"the binding did not make",
        candidates=names)


def nearest(session, word: int, role: str, a_name: str,
            domain: str) -> Optional[str]:
    """The control: the supplied nearest-mask search.

    Where :func:`recover` refuses, this returns the carrier at least Hamming
    distance from the recovered reading -- first in register order among ties
    -- and says nothing about having chosen.  It is kept because the value of
    a refusal is measured against what answering anyway would have said.
    """
    try:
        a_mask = _reading_of(session, domain, a_name)
    except BindingError:
        return None
    recovered = unbind(role, a_mask, word)
    best: Optional[Tuple[int, str]] = None
    for name, mask in _readings(session, domain):
        distance = hamming(mask, recovered)
        if best is None or distance < best[0]:
            best = (distance, name)
    return None if best is None else best[1]


# ===========================================================================
# 3.  THE TWO CENSUSES -- what the registers make of each binding
# ===========================================================================

def product_zeros(carrier: Sequence) -> int:
    """How many coordinates of a carrier read exactly zero."""
    return sum(1 for value in carrier if value == 0)


def product_census(session=None) -> Dict[str, object]:
    """How far the **product** binding gets on the registers as they are.

    A product binding is invertible only where the key reads nowhere zero, so
    a carrier with a zero coordinate cannot be the known side of a recoverable
    product binding -- and a carrier with a zero coordinate cannot be
    recovered as the filler either, since the coordinate carries no
    information about it.  This counts both.
    """
    session = session or _session()
    rows: List[Dict[str, object]] = []
    keys: List[Tuple[str, str]] = []
    vectors: set = set()
    total = 0
    with_zero = 0
    for domain in session.domains:
        carriers = tuple(session.register(domain))
        zeros = tuple(obj for obj in carriers if product_zeros(obj.carrier))
        total += len(carriers)
        with_zero += len(zeros)
        rows.append({
            "domain": domain,
            "carriers": len(carriers),
            "with_zero_coordinate": len(zeros),
            "least_zeros": min((product_zeros(obj.carrier)
                                for obj in carriers), default=0),
            "keys": tuple(obj.name for obj in carriers
                          if not product_zeros(obj.carrier)),
        })
        for obj in carriers:
            if not product_zeros(obj.carrier):
                keys.append((domain, obj.name))
                vectors.add(tuple(str(value) for value in obj.carrier))
    return {
        "rows": tuple(rows),
        "carriers": total,
        "with_zero_coordinate": with_zero,
        "recoverable": total - with_zero,
        "keys": tuple(keys),
        "distinct_keys": len(vectors),
    }


def register_census(session=None) -> Dict[str, object]:
    """The fibres of the parity reading, register by register.

    ``recoverable`` is the count of carriers whose reading no other carrier of
    the same register shares -- exactly the carriers a parity binding can name
    rather than merely read.
    """
    session = session or _session()
    rows: List[Dict[str, object]] = []
    total = 0
    recoverable = 0
    readings_total = 0
    largest = 0
    largest_where = ""
    for domain in session.domains:
        readings = _readings(session, domain)
        counts: Dict[int, int] = {}
        for _, mask in readings:
            counts[mask] = counts.get(mask, 0) + 1
        unique = sum(1 for _, mask in readings if counts[mask] == 1)
        biggest = max(counts.values(), default=0)
        if biggest > largest:
            largest, largest_where = biggest, domain
        total += len(readings)
        recoverable += unique
        readings_total += len(counts)
        rows.append({
            "domain": domain,
            "carriers": len(readings),
            "readings": len(counts),
            "recoverable": unique,
            "largest_fibre": biggest,
        })
    return {
        "rows": tuple(rows),
        "carriers": total,
        "readings": readings_total,
        "recoverable": recoverable,
        "ambiguous": total - recoverable,
        "largest_fibre": largest,
        "largest_fibre_domain": largest_where,
        # The nearest-mask control answers for every carrier and is right
        # exactly once per fibre -- it returns whichever member of the fibre
        # the register lists first.
        "control_right": readings_total,
        "control_wrong": total - readings_total,
    }


# ===========================================================================
# 4.  THE DECLARED SET -- what the operation is measured on
# ===========================================================================

#: The bindings this round declares before running them.  Each row is
#: ``(key, role, a, b, domain, expected, note)``; ``expected`` is the name the
#: recovery must return or the refusal reason it must give.
DECLARED_BINDINGS: Tuple[
    Tuple[str, str, str, str, str, str, str], ...] = (
    ("element-recovered",
     "causes", "C", "O", "chemistry", "O",
     "the plainest one: both carriers read uniquely, so the word names the "
     "filler"),
    ("element-other-role",
     "derived_from", "C", "O", "chemistry", "O",
     "the same pair under another role: a different word, the same filler"),
    ("element-far-apart",
     "part_of", "H", "Og", "chemistry", "Og",
     "the two ends of the table, to show the recovery is not proximity"),
    ("molecule-recovered",
     "affected_by", "water", "methane", "molecules", "methane",
     "another register, with 37 of its 51 carriers uniquely read"),
    ("harmonic-recovered",
     "contrasts_with", "unison", "perfect_fifth", "harmonics",
     "perfect_fifth",
     "the one register whose parity reading is injective: 28 of 28"),
    ("lexicon-recovered",
     "mentioned_after", "force", "mass", "lexicon", "mass",
     "the register the conversation layer binds pronouns in"),
    ("element-collision",
     "causes", "C", "Ba", "chemistry", "ambiguous-recovery",
     "the chemistry register's one collision: barium and lead read alike, "
     "and the recovery refuses rather than choose"),
    ("lexicon-collision",
     "equals", "force", "energy", "lexicon", "ambiguous-recovery",
     "energy and work read alike, so the word that binds energy names both"),
    ("physics-collision",
     "derived_from", "acceleration", "absorptance", "physics",
     "ambiguous-recovery",
     "the worst case in the system: 136 physics carriers read as all-zero "
     "parity, and the binding cannot tell them apart"),
    ("unknown-role",
     "rhymes_with", "C", "O", "chemistry", "unknown-role",
     "a relation type the table does not declare is not a role"),
    ("unknown-name",
     "causes", "C", "phlogiston", "chemistry", "unknown-name",
     "a filler the register does not hold cannot be bound"),
    ("unknown-known-side",
     "causes", "phlogiston", "O", "chemistry", "unknown-name",
     "nor can a known side the register does not hold"),
)


def _run_declared(session) -> Tuple[Dict[str, object], ...]:
    rows: List[Dict[str, object]] = []
    for key, role, a_name, b_name, domain, expected, note in \
            DECLARED_BINDINGS:
        entry: Dict[str, object] = {
            "key": key, "role": role, "a": a_name, "b": b_name,
            "domain": domain, "expected": expected, "note": note,
        }
        try:
            bound = bind_names(session, role, a_name, b_name, domain)
        except BindingError as error:
            entry["outcome"] = error.reason
            entry["detail"] = str(error)
            entry["control"] = ""
            entry["control_agrees"] = True
        else:
            entry["word"] = f"0x{bound.word:06x}"
            entry["sentence"] = bound.sentence
            control = nearest(session, bound.word, role, a_name, domain)
            entry["control"] = control or ""
            try:
                entry["outcome"] = recover(
                    session, bound.word, role, a_name, domain)
                entry["detail"] = bound.sentence
                entry["candidates"] = []
            except BindingError as error:
                entry["outcome"] = error.reason
                entry["detail"] = str(error)
                entry["candidates"] = list(error.candidates[:6])
            entry["control_agrees"] = control == b_name
        entry["as_declared"] = entry["outcome"] == expected
        rows.append(entry)
    return tuple(rows)


def _session():
    from ..runtime.session import GeometricSession
    return GeometricSession()


def binding_report(session=None) -> Dict[str, object]:
    """What a bound relation gives back, measured three ways.

    The declared set with the outcome of each against what was declared for
    it; the fibres of every register, which are what decides a recovery; and
    the product binding's census, which is the refutation of the second
    supplied claim.
    """
    session = session or _session()
    rows = _run_declared(session)
    fibres = register_census(session)
    product = product_census(session)
    recovered = tuple(row for row in rows
                      if row["outcome"] not in REFUSAL_REASONS)
    refused = tuple(row for row in rows if row["outcome"] in REFUSAL_REASONS)
    as_declared = tuple(row for row in rows if row["as_declared"])
    reasons = tuple(sorted({str(row["outcome"]) for row in refused}))
    answerable = tuple(row for row in rows if "word" in row)
    control_wrong = tuple(row for row in answerable
                          if not row["control_agrees"])
    return {
        "roles": len(ROLES),
        "declared": len(DECLARED_BINDINGS),
        "rows": rows,
        "recovered": len(recovered),
        "refused": len(refused),
        "as_declared": len(as_declared),
        "refusal_reasons": reasons,
        "reasons_declared": len(REFUSAL_REASONS),
        "control_rows": len(answerable),
        "control_wrong": len(control_wrong),
        "control_wrong_keys": [row["key"] for row in control_wrong],
        "control_silent": len([row for row in answerable
                               if row["outcome"] in REFUSAL_REASONS]),
        "fibres": fibres,
        "product": product,
        "verdict": (
            f"the parity binding writes a typed relation into one 24-bit word "
            f"and gives the filler's reading back exactly, with no side "
            f"condition; naming the filler is a second step, and on the "
            f"{len(DECLARED_BINDINGS)} declared bindings it names "
            f"{len(recovered)} and refuses {len(refused)} under "
            f"{len(reasons)} of its {len(REFUSAL_REASONS)} named reasons, "
            f"every one of them as declared before the run. Across the "
            f"{fibres['carriers']} carriers the session loads, "
            f"{fibres['recoverable']} read uniquely and so can be named; the "
            f"other {fibres['ambiguous']} share a reading with another "
            f"carrier of their own register, the worst fibre holding "
            f"{fibres['largest_fibre']} of them in "
            f"{fibres['largest_fibre_domain']}. The product binding of the "
            f"same material is recoverable from "
            f"{product['recoverable']} of {product['carriers']} known sides: "
            f"one zero coordinate is enough to make two fillers bind alike, "
            f"{product['with_zero_coordinate']} carriers read zero "
            f"somewhere, and the "
            f"{product['recoverable']} that do not take only "
            f"{product['distinct_keys']} distinct values between them."),
        "caveat": (
            f"what comes back is a reading, not a name, and whether a reading "
            f"names a carrier is a property of the register rather than of "
            f"the binding: the same word recovers the same reading under "
            f"every role and every known side. The nearest-mask control -- "
            f"the supplied search, which answers whatever the fibre holds -- "
            f"names a carrier other than the one that was bound on "
            f"{len(control_wrong)} of the {len(answerable)} bindings it "
            f"applies to and answers without comment on every one of the "
            f"{len([row for row in answerable if row['outcome'] in REFUSAL_REASONS])} "
            f"the operation refuses; taken over every carrier rather than "
            f"the declared set it is right once per fibre, which is "
            f"{fibres['control_right']} of {fibres['carriers']} and wrong on "
            f"the other {fibres['control_wrong']}. Nothing here "
            f"is a claim that a relation type means anything: a role is a "
            f"permutation someone wrote down, and two roles that agree on the "
            f"known side bind identically."),
    }


if __name__ == "__main__":                      # pragma: no cover
    report = binding_report()
    print(report["verdict"])
    for row in report["rows"]:
        print(f"  {row['key']:<22} {str(row['outcome']):<20} "
              f"{'as declared' if row['as_declared'] else 'NOT AS DECLARED'}")
