"""``glm_universal.reasoning.reversibility`` -- the Reversibility ledger (D18).

Every operation in the substrate is tagged with one of four reversibility
classes:

  * **bijective** -- a proved inverse exists in the tree (e.g. the Golay
    decoder is the inverse of the Golay encoder).
  * **has_inverse** -- an inverse exists but is not the operation's pair
    (e.g. the corpus's ``--check`` is the inverse of ``--refresh`` for the
    purpose of verifying a refresh, but the two are not a pair).
  * **forward_only** -- no inverse exists; the operation is intentionally
    one-way (e.g. the corpus's ``--ask`` returns a shortlist; the
    shortlist is not invertible to a query).
  * **declared_lossy** -- information is lost and the loss is witnessed
    (e.g. the XOR combiner's ``2**24``-to-one loss, witnessed by the
    COMBINER_STUDY's pigeonhole argument).

The class is part of the operation's interface.  A bijective operation
ships with its inverse proved in Lean.  A declared-lossy operation ships
with a witnessing pair.  A forward-only operation used in a context that
expects its inverse is a bug, caught by the instrument.

*Created 29 October 2026 (Iteration 10, Phase R5).  The measurements
already exist (COMBINER_STUDY measures XOR's loss; INFORMATION_LOSS_STUDY
lists what each layer cannot see); this module makes the requirement
explicit by tagging every operation with its class and checking the
consumers.*

The Lean formalization (``Reversibility.lean``, to be written) will prove:
  * ``bijective_inverse`` -- a bijective operation's registered inverse
    composes to the identity.
  * ``lossy_witness`` -- a declared-lossy operation's witness is a true
    pair of inputs mapping to the same output.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, FrozenSet, List, Optional, Tuple

__all__ = [
    "ReversibilityClass", "Operation", "LEDGER", "register",
    "class_of", "inverse_of", "loss_witness_of", "consumers_of",
    "all_operations", "reversibility_report",
]


# ---------------------------------------------------------------------------
# The four reversibility classes
# ---------------------------------------------------------------------------

#: The four reversibility classes.
REVERSIBILITY_CLASSES = (
    "bijective",       # a proved inverse exists in the tree
    "has_inverse",     # an inverse exists but is not the operation's pair
    "forward_only",    # no inverse exists; intentionally one-way
    "declared_lossy",  # information is lost and the loss is witnessed
)

ReversibilityClass = str  # one of REVERSIBILITY_CLASSES


@dataclass(frozen=True)
class Operation:
    """A registered operation in the reversibility ledger.

    Attributes
    ----------
    name
        The operation's dotted name (e.g. ``"golay.encode"``,
        ``"corpus.ask"``, ``"combiner.xor"``).
    cls
        The reversibility class (one of REVERSIBILITY_CLASSES).
    inverse
        The name of the inverse operation, if ``cls`` is ``bijective`` or
        ``has_inverse``; empty otherwise.
    inverse_lean
        The Lean theorem proving the inverse composes to the identity
        (for ``bijective``).
    loss_witness
        A witnessing pair of inputs that map to the same output (for
        ``declared_lossy``), as a string.
    loss_lean
        The Lean theorem witnessing the loss (for ``declared_lossy``).
    consumers
        The modules/functions that rely on this operation's class.
    """

    name: str
    cls: ReversibilityClass
    inverse: str = ""
    inverse_lean: str = ""
    loss_witness: str = ""
    loss_lean: str = ""
    consumers: Tuple[str, ...] = ()


class ReversibilityLedger:
    """The ledger of operations and their reversibility classes."""

    def __init__(self) -> None:
        self._operations: Dict[str, Operation] = {}

    def register(self, op: Operation) -> None:
        """Register an operation.  Replaces any existing entry."""
        self._operations[op.name] = op

    def get(self, name: str) -> Optional[Operation]:
        return self._operations.get(name)

    def class_of(self, name: str) -> Optional[ReversibilityClass]:
        op = self._operations.get(name)
        return op.cls if op else None

    def inverse_of(self, name: str) -> str:
        op = self._operations.get(name)
        return op.inverse if op else ""

    def loss_witness_of(self, name: str) -> str:
        op = self._operations.get(name)
        return op.loss_witness if op else ""

    def consumers_of(self, name: str) -> Tuple[str, ...]:
        op = self._operations.get(name)
        return op.consumers if op else ()

    def all_operations(self) -> Tuple[Operation, ...]:
        return tuple(self._operations[n] for n in sorted(self._operations))

    def __len__(self) -> int:
        return len(self._operations)

    def __contains__(self, name: str) -> bool:
        return name in self._operations


#: The global ledger.
LEDGER = ReversibilityLedger()


def register(op: Operation) -> None:
    """Register an operation in the global ledger."""
    LEDGER.register(op)


def class_of(name: str) -> Optional[ReversibilityClass]:
    """The reversibility class of an operation, or None."""
    return LEDGER.class_of(name)


def inverse_of(name: str) -> str:
    """The inverse of an operation, or empty string."""
    return LEDGER.inverse_of(name)


def loss_witness_of(name: str) -> str:
    """The loss witness of a declared-lossy operation, or empty string."""
    return LEDGER.loss_witness_of(name)


def consumers_of(name: str) -> Tuple[str, ...]:
    """The consumers of an operation."""
    return LEDGER.consumers_of(name)


def all_operations() -> Tuple[Operation, ...]:
    """All registered operations, sorted by name."""
    return LEDGER.all_operations()


def reversibility_report() -> Dict[str, Any]:
    """A report on the reversibility ledger for the CLI."""
    ops = LEDGER.all_operations()
    by_class: Dict[str, int] = {}
    for op in ops:
        by_class[op.cls] = by_class.get(op.cls, 0) + 1
    return {
        "count": len(ops),
        "by_class": by_class,
        "operations": [
            {
                "name": op.name,
                "class": op.cls,
                "inverse": op.inverse,
                "inverse_lean": op.inverse_lean,
                "loss_witness": op.loss_witness,
                "loss_lean": op.loss_lean,
                "consumers": list(op.consumers),
            }
            for op in ops
        ],
        "holds": len(ops) > 0,
    }


# ---------------------------------------------------------------------------
# Built-in operations (the measurements that already exist)
# ---------------------------------------------------------------------------

register(Operation(
    name="golay.encode",
    cls="bijective",
    inverse="golay.decode",
    inverse_lean="GLM.Golay.Code.decode_encode_inverse",
    consumers=("substrate/golay_decode.py", "substrate/mog.py"),
))
register(Operation(
    name="golay.decode",
    cls="bijective",
    inverse="golay.encode",
    inverse_lean="GLM.Golay.Code.encode_decode_inverse",
    consumers=("substrate/golay_decode.py",),
))
register(Operation(
    name="corpus.ask",
    cls="forward_only",
    consumers=("corpus/__main__.py",),
))
register(Operation(
    name="corpus.refresh",
    cls="has_inverse",
    inverse="corpus.check",
    consumers=("corpus/__main__.py",),
))
register(Operation(
    name="corpus.check",
    cls="has_inverse",
    inverse="corpus.refresh",
    consumers=("corpus/__main__.py",),
))
register(Operation(
    name="combiner.xor",
    cls="declared_lossy",
    loss_witness="2^24-to-one: any two 24-bit words with the same XOR digest",
    loss_lean="GLM.Combiner.xor_pigeonhole",
    consumers=("reasoning/combiner.py",),
))
register(Operation(
    name="sha256",
    cls="declared_lossy",
    loss_witness="any two inputs with the same hash (existence proved by pigeonhole)",
    loss_lean="GLM.Reversibility.sha256_pigeonhole",
    consumers=("integrity.py",),
))
