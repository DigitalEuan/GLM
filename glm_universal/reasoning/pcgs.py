"""``glm_universal.reasoning.pcgs`` -- the proof-carrying generative substrate.

What this module is
-------------------
``source_material/pcgs_wider_landscape_v4.txt`` and
``source_material/pcgs_glm_integration.py`` push "generate, don't store" past the
one pair the substrate already generates -- the Golay code and the Leech lattice
of :mod:`glm_universal.substrate.mog` and
:mod:`glm_universal.reasoning.generative` -- and onto a wider list of systems,
under a stronger contract than procedural generation.  A *proof-carrying
generative substrate* answers a query with three things rather than one:

    compact description -> (answer, correctness evidence, resource evidence)

The two scripts cannot be run as they stand: they import a ``pcgs`` package from
an absolute path outside the repository, and set ``GLM_ROOT`` to a directory that
does not exist here.  This module is the part of them that survives that
transplant -- rewritten against the package's own substrate, standard library
only, exact ``int`` and ``Fraction`` throughout (D7), no RNG -- and it is wired
to the Lean development so that the load-bearing claims are *proved* rather than
sampled.

The six admission criteria of the concept document are applied to each system by
:func:`admission_table`; every row states which of the three kinds of evidence
it actually has.

What is here, and what backs it
-------------------------------
=============================  =====================================  ==================================
system                          this module                            proved in ``GLM.PCGS``
=============================  =====================================  ==================================
cost algebra (AICA)             :class:`Cost`                          ``Cost.plus_comm``, ``Cost.plus_assoc``, ``Cost.algebraicTotal_plus``, ``Cost.algebraicTotal_scale``
information axis                :func:`bits_for`                       ``bitsFor_spec``, ``bitsFor_min``, ``bitsFor_two_pow``
Reed-Muller ``RM(1,m)``         :class:`ReedMullerCode`                ``rmWeight_of_ne_zero``, ``rmWeight_of_zero``, ``rm_min_distance``
number-theoretic transform      :class:`NumberTheoreticTransform`      ``ntt_intt`` (for :meth:`~NumberTheoreticTransform.forward_direct`)
physical cost layer             :class:`PhysicalCostLayer`             ``bitsErased_reversible``, ``landauerEnergy_mono``, ``landauerEnergy_le_of_le_log_two``, ``ln2Fast_le_log_two``, ``ln2Lower_100_le_log_two``
caching decision                :func:`breakeven_queries`              ``breakeven_iff``, ``breakevenQueries_spec``
sparse operator                 :class:`SparseStencilOperator`         (tested, not proved)
transducer                      :class:`FiniteStateTransducer`         (tested, not proved)
=============================  =====================================  ==================================

The transform is the case where the distinction matters most.  ``GLM.PCGS.ntt_intt``
proves the round trip for the *definition* -- the sum ``Σ_j a_j w^{ij}`` -- while
the script ships the iterative radix-2 algorithm.  :meth:`NumberTheoreticTransform.forward`
is that algorithm and :meth:`NumberTheoreticTransform.forward_direct` is the
definition; :func:`transform_report` checks that they agree on every input it is
given, so the theorem is carried across by a *tested* transcription and the
report says so rather than claiming the algorithm is proved.

Three corrections to the source scripts
---------------------------------------
1. ``InformationComplexity.of_vector`` fell back to ``math.log2`` -- a float --
   for ``n > 65536``.  :func:`bits_for_vector` is exact at every size: it is
   ``bits_for(q ** n)`` computed by integer bit length, and for large ``n`` it
   uses the integer identity rather than a float estimate.
2. ``thermodynamic_efficiency`` returned ``Fraction(0)`` both when the ratio is
   genuinely zero and when it is undefined (no operations at all).
   :meth:`PhysicalCostLayer.thermodynamic_efficiency` returns ``None`` for the
   undefined case, and the caller has to say what it wants done.
3. The comment that an efficiency above 1 "would violate the second law" is not
   what the model says: the CMOS figure is a per-*operation* engineering
   constant, not a bound, so a ratio above 1 means the two axes were measured
   against incomparable units -- :func:`physical_report` reports it that way.

One improvement
---------------
The script's lower bound for ``ln 2`` is the alternating harmonic sum, which at a
hundred terms is still wrong in the third decimal place (0.68817 against
0.69315) -- and being *a* lower bound is a separate fact for each length.
:meth:`PhysicalCostLayer.ln2_lower_fast` uses ``ln 2 = sum 1/(k 2^k)`` instead:
every term is positive, so every partial sum is a lower bound at once
(``GLM.PCGS.ln2Fast_le_log_two``, proved for all lengths), and at 64 terms the
residual is below ``10 ** -21``.  That is the constant
:meth:`PhysicalCostLayer.landauer_per_bit` now uses.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from fractions import Fraction
from typing import Callable, Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

from ..substrate.mog import GOLAY, GOLAY_MASKS

__all__ = [
    "Cost",
    "bits_for",
    "bits_for_vector",
    "GeneratedLinearCode",
    "ReedMullerCode",
    "NumberTheoreticTransform",
    "InstrumentedField",
    "SparseStencilOperator",
    "FiniteStateTransducer",
    "PhysicalCostLayer",
    "breakeven_queries",
    "breakeven_holds",
    "code_report",
    "transform_report",
    "operator_report",
    "transducer_report",
    "physical_report",
    "golay_cross_check",
    "admission_table",
    "pcgs_report",
]


# ---------------------------------------------------------------------------
# 1. The cost algebra (AICA): algebraic operations and information bits
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Cost:
    """An exact resource ledger: operation counts, and the information content.

    The two axes replace "CPU cycles" and "RAM bytes", which are platform- and
    representation-dependent.  Sequential composition is :meth:`plus` and
    ``k``-fold repetition is :meth:`scale`; ``GLM.PCGS.Cost`` proves that the two
    make a commutative monoid with an additive :meth:`algebraic_total`, which is
    what lets a report be assembled in any order.
    """

    mul: int = 0
    add: int = 0
    sub: int = 0
    xor: int = 0
    modinv: int = 0
    cmp: int = 0
    info_bits: int = 0

    def plus(self, other: "Cost") -> "Cost":
        return Cost(
            self.mul + other.mul,
            self.add + other.add,
            self.sub + other.sub,
            self.xor + other.xor,
            self.modinv + other.modinv,
            self.cmp + other.cmp,
            self.info_bits + other.info_bits,
        )

    __add__ = plus

    def scale(self, k: int) -> "Cost":
        if k < 0:
            raise ValueError("repetition count must be non-negative")
        return Cost(
            self.mul * k,
            self.add * k,
            self.sub * k,
            self.xor * k,
            self.modinv * k,
            self.cmp * k,
            self.info_bits * k,
        )

    def algebraic_total(self) -> int:
        """Every primitive operation counted once; a modular inverse is one."""

        return self.mul + self.add + self.sub + self.xor + self.modinv + self.cmp

    def with_info(self, bits: int) -> "Cost":
        return replace(self, info_bits=bits)

    def as_dict(self) -> Dict[str, int]:
        return {
            "mul": self.mul,
            "add": self.add,
            "sub": self.sub,
            "xor": self.xor,
            "modinv": self.modinv,
            "cmp": self.cmp,
            "info_bits": self.info_bits,
            "algebraic_total": self.algebraic_total(),
        }


ZERO_COST = Cost()


def bits_for(cardinality: int) -> int:
    """``ceil(log2(cardinality))``: bits to name one element of a set.

    Exact for every size -- no float anywhere.  ``GLM.PCGS.bitsFor_spec`` proves
    ``n <= 2 ** bits_for(n)`` and ``GLM.PCGS.bitsFor_min`` proves that nothing
    smaller will do, so this is the description bound rather than an estimate.
    """

    if cardinality < 0:
        raise ValueError("cardinality must be non-negative")
    if cardinality <= 1:
        return 0
    return (cardinality - 1).bit_length()


def bits_for_vector(alphabet: int, length: int) -> int:
    """Bits to describe a ``length``-symbol word over an ``alphabet``-symbol set.

    The source script fell back to ``math.log2`` above 65,536 symbols.  This is
    exact at every size: for a power-of-two alphabet the answer is
    ``length * log2(alphabet)`` on the nose, and otherwise it is the bit length
    of ``alphabet ** length - 1``, computed in integers.
    """

    if alphabet <= 1 or length <= 0:
        return 0
    if alphabet & (alphabet - 1) == 0:  # exact power of two
        return length * (alphabet.bit_length() - 1)
    return bits_for(alphabet**length)


# ---------------------------------------------------------------------------
# 2. Generated linear codes: Reed-Muller, and the cross-check against Golay
# ---------------------------------------------------------------------------


def _popcount(x: int) -> int:
    return bin(x).count("1")


class GeneratedLinearCode:
    """A binary linear code held as its generator rows, never as a codeword table.

    The description is ``k`` rows of ``n`` bits.  The extensional object is
    ``2 ** k`` codewords; it is produced only when a census is asked for, and
    the ledger of that census is reported beside it.
    """

    def __init__(self, rows: Sequence[int], length: int, name: str) -> None:
        self.rows: Tuple[int, ...] = tuple(rows)
        self.n = length
        self.k = len(self.rows)
        self.name = name

    # -- generation ---------------------------------------------------------

    def encode(self, message: int) -> int:
        """The codeword of a ``k``-bit message: XOR of the selected rows."""

        if not 0 <= message < (1 << self.k):
            raise ValueError("message out of range")
        word = 0
        for i, row in enumerate(self.rows):
            if (message >> i) & 1:
                word ^= row
        return word

    def encode_with_cost(self, message: int) -> Tuple[int, Cost]:
        word = 0
        xors = 0
        for i, row in enumerate(self.rows):
            if (message >> i) & 1:
                word ^= row
                xors += 1
        return word, Cost(xor=xors, info_bits=self.n)

    def codewords(self) -> Iterator[int]:
        for message in range(1 << self.k):
            yield self.encode(message)

    # -- queries that avoid the full object ---------------------------------

    def weight_enumerator(self) -> Dict[int, int]:
        counts: Dict[int, int] = {}
        for word in self.codewords():
            w = _popcount(word)
            counts[w] = counts.get(w, 0) + 1
        return dict(sorted(counts.items()))

    def minimum_distance(self) -> int:
        best = self.n
        for message in range(1, 1 << self.k):
            best = min(best, _popcount(self.encode(message)))
        return best

    def certificate(self, word: int) -> Optional[Tuple[int, ...]]:
        """A membership certificate: the message that generates ``word``.

        Returned as the bits of the message, so a checker can re-encode it and
        compare -- ``k`` XORs -- rather than trusting the search that found it.
        """

        for message in range(1 << self.k):
            if self.encode(message) == word:
                return tuple((message >> i) & 1 for i in range(self.k))
        return None

    def verify_certificate(self, word: int, certificate: Sequence[int]) -> bool:
        message = 0
        for i, bit in enumerate(certificate):
            if bit:
                message |= 1 << i
        return self.encode(message) == word

    # -- description vs extension -------------------------------------------

    def description_bits(self) -> int:
        return self.k * self.n

    def extension_bits(self) -> int:
        return (1 << self.k) * self.n


class ReedMullerCode(GeneratedLinearCode):
    """``RM(1, m) = [2^m, m+1, 2^(m-1)]`` generated from its evaluation basis.

    The compact description is the single integer ``m``: the rows are the
    evaluations of ``1, x_1, ..., x_m`` on ``F_2^m``.  ``GLM.PCGS.rmWeight_of_ne_zero``
    proves that every codeword with a nonzero linear part has weight exactly
    ``2 ** (m-1)``, and ``GLM.PCGS.rm_min_distance`` reads the minimum distance
    off that -- so :meth:`predicted_weight_enumerator` is a *theorem*, and
    :meth:`weight_enumerator` (which enumerates) is the check on the code this
    module actually built.
    """

    def __init__(self, m: int) -> None:
        if m < 1:
            raise ValueError("m must be at least 1")
        self.m = m
        n = 1 << m
        rows = [(1 << n) - 1]
        for i in range(m):
            row = 0
            for point in range(n):
                if (point >> i) & 1:
                    row |= 1 << point
            rows.append(row)
        super().__init__(rows, n, f"RM(1,{m}) [{n},{m + 1},{1 << (m - 1)}]")

    def predicted_weight_enumerator(self) -> Dict[int, int]:
        """What ``GLM.PCGS`` proves the weight distribution must be.

        One zero word, one all-ones word, and ``2 ** (m+1) - 2`` words of weight
        ``2 ** (m-1)``.
        """

        n = self.n
        half = n >> 1
        counts = {0: 1, n: 1}
        counts[half] = counts.get(half, 0) + (1 << (self.m + 1)) - 2
        return dict(sorted(counts.items()))

    def is_self_dual(self) -> bool:
        """``RM(1,m)`` is self-dual only at ``m = 3`` (the extended Hamming code).

        The source script says "iff ``m`` is odd", which is false for ``m = 5``:
        self-duality needs ``k = n/2``, i.e. ``m + 1 = 2 ** (m-1)``, and that
        holds only at ``m = 3``.  Decided here rather than asserted: the check is
        ``k == n/2`` together with every pair of rows being orthogonal.
        """

        if self.k * 2 != self.n:
            return False
        return all(
            _popcount(self.rows[i] & self.rows[j]) % 2 == 0
            for i in range(self.k)
            for j in range(self.k)
        )


def golay_cross_check() -> Dict[str, object]:
    """Does the generative account agree with the substrate's own Golay code?

    The substrate holds ``[24,12,8]`` in systematic form; this regenerates it
    from the same twelve rows through :class:`GeneratedLinearCode` and compares
    the two codeword sets and weight enumerators.  This is the cross-validation
    that ``pcgs_glm_integration.py`` performs against an external package.
    """

    rows = GOLAY.basis_masks if hasattr(GOLAY, "basis_masks") else GOLAY._basis_masks
    generated = GeneratedLinearCode(rows, 24, "Golay [24,12,8] (regenerated)")
    regenerated = frozenset(generated.codewords())
    stored = frozenset(GOLAY_MASKS)
    enumerator = generated.weight_enumerator()
    return {
        "regenerated_count": len(regenerated),
        "stored_count": len(stored),
        "sets_agree": regenerated == stored,
        "weight_enumerator": enumerator,
        "weight_enumerator_expected": {0: 1, 8: 759, 12: 2576, 16: 759, 24: 1},
        "minimum_distance": min(w for w in enumerator if w > 0),
        "description_bits": generated.description_bits(),
        "extension_bits": generated.extension_bits(),
    }


def code_report() -> Dict[str, object]:
    """Reed-Muller generated at three sizes, against what the theorem predicts."""

    rows: List[Dict[str, object]] = []
    for m in (2, 3, 4):
        code = ReedMullerCode(m)
        enumerator = code.weight_enumerator()
        rows.append(
            {
                "m": m,
                "name": code.name,
                "n": code.n,
                "k": code.k,
                "weight_enumerator": enumerator,
                "predicted": code.predicted_weight_enumerator(),
                "matches_theorem": enumerator == code.predicted_weight_enumerator(),
                "minimum_distance": code.minimum_distance(),
                "predicted_minimum_distance": 1 << (m - 1),
                "self_dual": code.is_self_dual(),
                "description_bits": code.description_bits(),
                "extension_bits": code.extension_bits(),
            }
        )
    return {"reed_muller": rows, "golay_cross_check": golay_cross_check()}


# ---------------------------------------------------------------------------
# 3. The transform, generated from a primitive root
# ---------------------------------------------------------------------------


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n == p:
            return True
        if n % p == 0:
            return False
    d, r = n - 1, 0
    while d % 2 == 0:
        d //= 2
        r += 1
    for a in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(r - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


def _prime_factors(n: int) -> List[int]:
    factors: List[int] = []
    d = 2
    while d * d <= n:
        if n % d == 0:
            factors.append(d)
            while n % d == 0:
                n //= d
        d += 1
    if n > 1:
        factors.append(n)
    return factors


def is_primitive_root(g: int, p: int) -> bool:
    order = p - 1
    return all(pow(g, order // q, p) != 1 for q in _prime_factors(order))


def smallest_primitive_root(p: int) -> int:
    for g in range(2, p):
        if is_primitive_root(g, p):
            return g
    raise ValueError("no primitive root found")


class InstrumentedField:
    """``Z/pZ`` arithmetic that counts every primitive operation it performs."""

    def __init__(self, prime: int) -> None:
        if prime < 2:
            raise ValueError("modulus must be at least 2")
        self.p = prime
        self.mul_count = 0
        self.add_count = 0
        self.sub_count = 0
        self.modinv_count = 0

    def mul(self, a: int, b: int) -> int:
        self.mul_count += 1
        return a * b % self.p

    def add(self, a: int, b: int) -> int:
        self.add_count += 1
        return (a + b) % self.p

    def sub(self, a: int, b: int) -> int:
        self.sub_count += 1
        return (a - b) % self.p

    def modinv(self, a: int) -> int:
        self.modinv_count += 1
        return pow(a, self.p - 2, self.p)

    def measured(self) -> Cost:
        return Cost(
            mul=self.mul_count,
            add=self.add_count,
            sub=self.sub_count,
            modinv=self.modinv_count,
        )

    def reset(self) -> None:
        self.mul_count = self.add_count = self.sub_count = self.modinv_count = 0


class NumberTheoreticTransform:
    """The NTT of length ``n`` over ``Z/pZ``, generated from ``(p, g)``.

    The compact description is two integers.  Everything else -- the ``n``-th
    root of unity, the twiddle factors, the transform matrix -- is generated:
    ``w = g ** ((p-1)/n) mod p``, ``w_k = w ** k mod p`` on demand.

    :meth:`forward_direct` is the *definition* ``A_i = Σ_j a_j w^{ij}``, which is
    what ``GLM.PCGS.ntt_intt`` proves invertible.  :meth:`forward` is the
    iterative radix-2 algorithm the script ships.  They are checked against each
    other by :func:`transform_report`.
    """

    def __init__(self, prime: int, length: int, root: Optional[int] = None) -> None:
        if not is_prime(prime):
            raise ValueError(f"{prime} is not prime")
        if length <= 0 or length & (length - 1):
            raise ValueError("length must be a power of two")
        if (prime - 1) % length:
            raise ValueError("length must divide p - 1")
        self.p = prime
        self.n = length
        self.g = smallest_primitive_root(prime) if root is None else root
        if not is_primitive_root(self.g, prime):
            raise ValueError(f"{self.g} is not a primitive root mod {prime}")
        self.w = pow(self.g, (prime - 1) // length, prime)

    # -- generated twiddles --------------------------------------------------

    def twiddle(self, k: int) -> int:
        """``w ** k``, generated in ``O(log k)`` multiplications, never stored."""

        return pow(self.w, k % self.n, self.p)

    def root_order(self) -> int:
        order = 1
        value = self.w
        while value != 1:
            value = value * self.w % self.p
            order += 1
        return order

    # -- the definition, which is what is proved -----------------------------

    def forward_direct(self, a: Sequence[int]) -> List[int]:
        if len(a) != self.n:
            raise ValueError("wrong length")
        return [
            sum(a[j] * pow(self.w, i * j, self.p) for j in range(self.n)) % self.p
            for i in range(self.n)
        ]

    def inverse_direct(self, spectrum: Sequence[int]) -> List[int]:
        if len(spectrum) != self.n:
            raise ValueError("wrong length")
        w_inv = pow(self.w, self.p - 2, self.p)
        n_inv = pow(self.n, self.p - 2, self.p)
        return [
            n_inv
            * sum(spectrum[i] * pow(w_inv, k * i, self.p) for i in range(self.n))
            % self.p
            for k in range(self.n)
        ]

    # -- the algorithm, which is what runs -----------------------------------

    @staticmethod
    def _bit_reverse(k: int, bits: int) -> int:
        r = 0
        for _ in range(bits):
            r = (r << 1) | (k & 1)
            k >>= 1
        return r

    def forward(self, a: Sequence[int], field: Optional[InstrumentedField] = None) -> List[int]:
        """Iterative radix-2 Cooley-Tukey, optionally through a counting field."""

        if len(a) != self.n:
            raise ValueError("wrong length")
        f = field if field is not None else InstrumentedField(self.p)
        n, p = self.n, self.p
        bits = n.bit_length() - 1
        A = [a[self._bit_reverse(i, bits)] % p for i in range(n)]
        m = 2
        while m <= n:
            wm = pow(self.w, n // m, p)
            half = m // 2
            for i in range(0, n, m):
                wj = 1
                for j in range(half):
                    u = A[i + j]
                    v = f.mul(A[i + j + half], wj)
                    A[i + j] = f.add(u, v)
                    A[i + j + half] = f.sub(u, v)
                    wj = f.mul(wj, wm)
            m <<= 1
        return A

    def inverse(self, spectrum: Sequence[int], field: Optional[InstrumentedField] = None) -> List[int]:
        f = field if field is not None else InstrumentedField(self.p)
        n_inv = f.modinv(self.n)
        inverse_root = NumberTheoreticTransform(self.p, self.n, self.g)
        inverse_root.w = f.modinv(self.w)
        out = inverse_root.forward(spectrum, f)
        return [f.mul(x, n_inv) for x in out]

    def convolve(self, a: Sequence[int], b: Sequence[int]) -> List[int]:
        """Cyclic convolution through the transform pair."""

        A = self.forward(a)
        B = self.forward(b)
        C = [x * y % self.p for x, y in zip(A, B)]
        return self.inverse(C)

    def convolve_schoolbook(self, a: Sequence[int], b: Sequence[int]) -> List[int]:
        n, p = self.n, self.p
        return [
            sum(a[j] * b[(k - j) % n] for j in range(n)) % p for k in range(n)
        ]

    # -- declared cost, to be compared with the measured one -----------------

    def declared_forward_cost(self) -> Cost:
        stages = self.n.bit_length() - 1
        butterflies = (self.n // 2) * stages
        return Cost(
            mul=2 * butterflies,
            add=butterflies,
            sub=butterflies,
            info_bits=bits_for_vector(self.p, self.n),
        )

    def declared_inverse_cost(self) -> Cost:
        return self.declared_forward_cost().plus(Cost(mul=self.n, modinv=2))

    def description_bits(self) -> int:
        """Two integers: the prime and the primitive root."""

        return bits_for(self.p + 1) + bits_for(self.g + 1)

    def table_bits(self) -> int:
        """What a stored twiddle table would cost."""

        return self.n * bits_for(self.p)


def transform_report(prime: int = 17, length: int = 4) -> Dict[str, object]:
    """Generate the transform, check the round trip, and price it exactly.

    The inputs are a documented integer recurrence, never random: ``x_{i+1} =
    (5 x_i + 3) mod p`` from ``x_0 = 1``.
    """

    ntt = NumberTheoreticTransform(prime, length)
    vectors: List[List[int]] = []
    x = 1
    for _ in range(4):
        vector = []
        for _ in range(length):
            vector.append(x % prime)
            x = (5 * x + 3) % prime
        vectors.append(vector)

    roundtrips = []
    agreements = []
    convolutions = []
    for vector in vectors:
        spectrum = ntt.forward(vector)
        agreements.append(spectrum == ntt.forward_direct(vector))
        roundtrips.append(ntt.inverse(spectrum) == [v % prime for v in vector])
        roundtrips.append(ntt.inverse_direct(ntt.forward_direct(vector)) == [v % prime for v in vector])
    for a, b in zip(vectors, vectors[1:]):
        convolutions.append(ntt.convolve(a, b) == ntt.convolve_schoolbook(a, b))

    field = InstrumentedField(prime)
    ntt.forward(vectors[0], field)
    measured_forward = field.measured()
    field_inv = InstrumentedField(prime)
    ntt.inverse(ntt.forward(vectors[0]), field_inv)
    measured_inverse = field_inv.measured()

    declared_forward = ntt.declared_forward_cost()
    declared_inverse = ntt.declared_inverse_cost()
    return {
        "prime": prime,
        "length": length,
        "primitive_root": ntt.g,
        "root_of_unity": ntt.w,
        "root_order": ntt.root_order(),
        "algorithm_matches_definition": all(agreements),
        "roundtrip": all(roundtrips),
        "convolution_matches_schoolbook": all(convolutions),
        "measured_forward": measured_forward.as_dict(),
        "declared_forward": declared_forward.as_dict(),
        "forward_cost_agrees": measured_forward.as_dict()["algebraic_total"]
        == declared_forward.as_dict()["algebraic_total"],
        "measured_inverse": measured_inverse.as_dict(),
        "declared_inverse": declared_inverse.as_dict(),
        "inverse_cost_agrees": measured_inverse.as_dict()["algebraic_total"]
        == declared_inverse.as_dict()["algebraic_total"],
        "description_bits": ntt.description_bits(),
        "table_bits": ntt.table_bits(),
    }


# ---------------------------------------------------------------------------
# 4. Sparse operators and transducers: the two systems that stay tested
# ---------------------------------------------------------------------------


class SparseStencilOperator:
    """A banded operator held as its stencil, applied without a matrix."""

    def __init__(self, stencil: Sequence[int], n: int, name: str = "stencil") -> None:
        if n <= 0:
            raise ValueError("dimension must be positive")
        if not len(stencil) % 2:
            raise ValueError("stencil must have odd length so it has a centre")
        self.stencil = tuple(stencil)
        self.n = n
        self.name = name
        self.half = len(self.stencil) // 2

    def apply(self, x: Sequence[Fraction]) -> List[Fraction]:
        if len(x) != self.n:
            raise ValueError("wrong length")
        out = [Fraction(0)] * self.n
        for i in range(self.n):
            total = Fraction(0)
            for j, coefficient in enumerate(self.stencil):
                col = i + j - self.half
                if 0 <= col < self.n:
                    total += Fraction(coefficient) * x[col]
            out[i] = total
        return out

    def apply_with_cost(self, x: Sequence[Fraction]) -> Tuple[List[Fraction], Cost]:
        muls = 0
        adds = 0
        out = [Fraction(0)] * self.n
        for i in range(self.n):
            total = Fraction(0)
            for j, coefficient in enumerate(self.stencil):
                col = i + j - self.half
                if 0 <= col < self.n:
                    total += Fraction(coefficient) * x[col]
                    muls += 1
                    adds += 1
            out[i] = total
        return out, Cost(mul=muls, add=adds)

    def dense_matrix(self) -> List[List[Fraction]]:
        """The extensional object, produced only to check the operator against."""

        matrix = [[Fraction(0)] * self.n for _ in range(self.n)]
        for i in range(self.n):
            for j, coefficient in enumerate(self.stencil):
                col = i + j - self.half
                if 0 <= col < self.n:
                    matrix[i][col] = Fraction(coefficient)
        return matrix

    def dense_apply(self, x: Sequence[Fraction]) -> List[Fraction]:
        matrix = self.dense_matrix()
        return [sum((matrix[i][j] * x[j] for j in range(self.n)), Fraction(0)) for i in range(self.n)]

    def description_entries(self) -> int:
        return len(self.stencil) + 1

    def matrix_entries(self) -> int:
        return self.n * self.n


class FiniteStateTransducer:
    """A stream processor held as its transition function.

    The extensional object -- an output for every input sequence -- is infinite,
    so this is the clearest case of the concept: there is nothing to store.
    """

    def __init__(
        self,
        name: str,
        initial_state: Tuple,
        transition: Callable[[Tuple, object], Tuple],
        output: Callable[[Tuple], object],
    ) -> None:
        self.name = name
        self.initial_state = initial_state
        self.transition = transition
        self.output = output

    def run(self, inputs: Iterable) -> List:
        state = self.initial_state
        outputs = []
        for symbol in inputs:
            state = self.transition(state, symbol)
            outputs.append(self.output(state))
        return outputs

    def final_state(self, inputs: Iterable) -> Tuple:
        state = self.initial_state
        for symbol in inputs:
            state = self.transition(state, symbol)
        return state


def running_mean_transducer() -> FiniteStateTransducer:
    """The exact rational running mean: state ``(sum, count)``, output ``sum/count``."""

    return FiniteStateTransducer(
        "running mean",
        (Fraction(0), 0),
        lambda state, symbol: (state[0] + Fraction(symbol), state[1] + 1),
        lambda state: state[0] / state[1] if state[1] else Fraction(0),
    )


def operator_report(n: int = 8) -> Dict[str, object]:
    """The Laplacian stencil applied without its matrix, and checked against it."""

    operator = SparseStencilOperator((-1, 2, -1), n, "1-D Laplacian")
    x = [Fraction(i * i, 3) for i in range(1, n + 1)]
    stencil_result, cost = operator.apply_with_cost(x)
    dense_result = operator.dense_apply(x)
    return {
        "name": operator.name,
        "dimension": n,
        "agrees_with_matrix": stencil_result == dense_result,
        "description_entries": operator.description_entries(),
        "matrix_entries": operator.matrix_entries(),
        "cost": cost.as_dict(),
    }


def transducer_report(length: int = 12) -> Dict[str, object]:
    """The running mean run as a stream, against the mean recomputed from scratch."""

    transducer = running_mean_transducer()
    stream = [((5 * i + 3) % 17) for i in range(1, length + 1)]
    outputs = transducer.run(stream)
    expected = [
        Fraction(sum(stream[: i + 1]), i + 1) for i in range(len(stream))
    ]
    return {
        "name": transducer.name,
        "length": length,
        "agrees_with_recomputation": outputs == expected,
        "final_value": str(outputs[-1]),
        "state_size": 2,
        "extensional_object": "infinite (one output per input sequence)",
    }


# ---------------------------------------------------------------------------
# 5. The physical cost layer
# ---------------------------------------------------------------------------


class PhysicalCostLayer:
    """Landauer's floor and the CMOS switching cost, in exact Fractions.

    ``GLM.PCGS`` proves the three claims that make the layer safe to quote:
    a step that loses no information erases nothing
    (``bitsErased_reversible``), the energy is monotone in the bits erased
    (``landauerEnergy_mono``), and replacing ``ln 2`` by a rational lower bound
    keeps the reported figure a lower bound (``landauerEnergy_le_of_le_log_two``)
    -- with ``ln2Lower_100_le_log_two`` checking the constant used here.
    """

    BOLTZMANN_K = Fraction(1380649, 10**29)  # J/K, exact by the 2019 SI definition
    ROOM_TEMP_T = Fraction(300)  # K
    CMOS_VOLTAGE_V = Fraction(7, 10)  # V, a stated choice
    CMOS_CAPACITANCE_C = Fraction(1, 10**15)  # F, a stated choice

    @staticmethod
    def ln2_lower(terms: int = 100) -> Fraction:
        """An even partial sum of the alternating harmonic series: below ``ln 2``."""

        if terms <= 0 or terms % 2:
            raise ValueError("terms must be positive and even")
        return sum(
            (Fraction(1 if k % 2 else -1, k) for k in range(1, terms + 1)),
            Fraction(0),
        )

    @staticmethod
    def ln2_lower_fast(terms: int = 64) -> Fraction:
        """A far tighter lower bound: the partial sums of ``ln 2 = sum 1/(k 2^k)``.

        Every term is positive, so every partial sum is below ``ln 2`` --
        ``GLM.PCGS.ln2Fast_le_log_two`` proves that for *all* lengths at once,
        where the alternating constant of the source script has to be checked one
        length at a time.  At 64 terms the residual is below 10**-21,
        against 5 * 10**-3 for the alternating sum at a hundred terms.
        """

        if terms <= 0:
            raise ValueError("terms must be positive")
        return sum(
            (Fraction(1, k * 2**k) for k in range(1, terms + 1)),
            Fraction(0),
        )

    @staticmethod
    def ln2_fast_tail_bound(terms: int = 64) -> Fraction:
        """How far below ``ln 2`` the fast bound can be: ``2^-n / (n+1)``."""

        if terms <= 0:
            raise ValueError("terms must be positive")
        return Fraction(1, (terms + 1) * 2**terms)

    @staticmethod
    def ln2_upper(terms: int = 101) -> Fraction:
        """An odd partial sum: above ``ln 2``.  The pair brackets the constant."""

        if terms <= 0 or terms % 2 == 0:
            raise ValueError("terms must be positive and odd")
        return sum(
            (Fraction(1 if k % 2 else -1, k) for k in range(1, terms + 1)),
            Fraction(0),
        )

    @classmethod
    def landauer_per_bit(cls) -> Fraction:
        """``k_B T ln 2`` from below, using the fast bound rather than the slow one."""

        return cls.BOLTZMANN_K * cls.ROOM_TEMP_T * cls.ln2_lower_fast(64)

    @classmethod
    def landauer_energy(cls, bits_erased: int) -> Fraction:
        if bits_erased <= 0:
            return Fraction(0)
        return cls.landauer_per_bit() * bits_erased

    @classmethod
    def cmos_per_op(cls) -> Fraction:
        return cls.CMOS_CAPACITANCE_C * cls.CMOS_VOLTAGE_V**2 / 2

    @classmethod
    def cmos_energy(cls, operations: int) -> Fraction:
        if operations <= 0:
            return Fraction(0)
        return cls.cmos_per_op() * operations

    @staticmethod
    def bits_erased(input_bits: int, output_bits: int) -> int:
        return max(0, input_bits - output_bits)

    @staticmethod
    def is_reversible(input_bits: int, output_bits: int) -> bool:
        return output_bits >= input_bits

    @classmethod
    def thermodynamic_efficiency(
        cls, bits_erased: int, operations: int
    ) -> Optional[Fraction]:
        """``E_landauer / E_cmos``, or ``None`` when there are no operations.

        The source script returned ``Fraction(0)`` for the undefined case as well
        as for the genuinely-zero one; here the two are distinguished.
        """

        cmos = cls.cmos_energy(operations)
        if cmos == 0:
            return None
        return cls.landauer_energy(bits_erased) / cmos


def physical_report(cost: Optional[Cost] = None) -> Dict[str, object]:
    """Price one measured ledger thermodynamically and electrically."""

    if cost is None:
        transform = NumberTheoreticTransform(17, 4)
        cost = transform.declared_forward_cost()
    layer = PhysicalCostLayer
    operations = cost.algebraic_total()
    erased = cost.info_bits
    efficiency = layer.thermodynamic_efficiency(erased, operations)
    return {
        "ln2_lower": str(layer.ln2_lower(100)),
        "ln2_bracket_width": str(layer.ln2_upper(101) - layer.ln2_lower(100)),
        "ln2_lower_fast": str(layer.ln2_lower_fast(64)),
        "ln2_fast_tail_bound": str(layer.ln2_fast_tail_bound(64)),
        "landauer_per_bit_J": str(layer.landauer_per_bit()),
        "cmos_per_op_J": str(layer.cmos_per_op()),
        "operations": operations,
        "bits": erased,
        "landauer_J": str(layer.landauer_energy(erased)),
        "cmos_J": str(layer.cmos_energy(operations)),
        "efficiency": None if efficiency is None else str(efficiency),
        "efficiency_undefined_without_operations": layer.thermodynamic_efficiency(8, 0)
        is None,
        "reversible_step_costs_nothing": layer.landauer_energy(
            layer.bits_erased(3, 3)
        )
        == 0,
        "note": (
            "the ratio compares a physical floor with an engineering constant; a "
            "value above 1 means the two axes were measured against incomparable "
            "units, not that the second law was broken"
        ),
    }


# ---------------------------------------------------------------------------
# 6. Caching is a decision
# ---------------------------------------------------------------------------


def breakeven_queries(store: int, generate: int, lookup: int) -> int:
    """Queries after which materialising is cheaper: ``ceil(store / (gen - look))``.

    ``GLM.PCGS.breakevenQueries_spec`` proves that this is exactly the threshold.
    """

    if generate <= lookup:
        raise ValueError("generation must be dearer than lookup for a break-even")
    d = generate - lookup
    return (store + d - 1) // d


def breakeven_holds(store: int, generate: int, lookup: int, queries: int) -> bool:
    """Is the stored table already paying for itself at this query count?"""

    return store + lookup * queries <= generate * queries


def caching_table() -> List[Dict[str, object]]:
    """The break-even point of each generated object in this module."""

    rows: List[Dict[str, object]] = []
    rm = ReedMullerCode(4)
    rows.append(
        {
            "object": rm.name,
            "store_bits": rm.extension_bits(),
            "generate_bits_per_query": rm.k,
            "lookup_bits_per_query": 1,
            "breakeven_queries": breakeven_queries(rm.extension_bits(), rm.k, 1),
        }
    )
    ntt = NumberTheoreticTransform(17, 4)
    rows.append(
        {
            "object": f"NTT twiddles mod {ntt.p}",
            "store_bits": ntt.table_bits(),
            "generate_bits_per_query": bits_for(ntt.n),
            "lookup_bits_per_query": 1,
            "breakeven_queries": breakeven_queries(
                ntt.table_bits(), bits_for(ntt.n), 1
            ),
        }
    )
    rows.append(
        {
            "object": "Golay [24,12,8] codeword table",
            "store_bits": 4096 * 24,
            "generate_bits_per_query": 12,
            "lookup_bits_per_query": 1,
            "breakeven_queries": breakeven_queries(4096 * 24, 12, 1),
        }
    )
    return rows


# ---------------------------------------------------------------------------
# 7. Admission, and the whole report
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Admission:
    """One system against the six admission criteria of the concept document."""

    system: str
    compact_description: str
    direct_query: str
    semantic_specification: str
    evidence: str
    evidence_kind: str  # "proved" | "tested" | "checked transcription"
    resource_report: str
    caching: str

    def admitted(self) -> bool:
        return all(
            bool(field)
            for field in (
                self.compact_description,
                self.direct_query,
                self.semantic_specification,
                self.evidence,
                self.resource_report,
                self.caching,
            )
        )


def admission_table() -> List[Admission]:
    """Every system in this module, with the kind of evidence it actually has."""

    return [
        Admission(
            system="Reed-Muller RM(1,m)",
            compact_description="one integer m; the rows are the evaluation basis",
            direct_query="weight of a codeword, and the minimum distance, without a codeword table",
            semantic_specification="the affine functionals on F_2^m",
            evidence="GLM.PCGS.rmWeight_of_ne_zero, rmWeight_of_zero, rm_min_distance",
            evidence_kind="proved",
            resource_report="k XORs per encode; description k*n bits against 2^k*n extensional",
            caching="a table wins only past the break-even query count in caching_table()",
        ),
        Admission(
            system="Golay [24,12,8] (cross-check)",
            compact_description="twelve generator rows, 36 bytes",
            direct_query="membership by twelve parity checks (GLM.ZeroStorageV5)",
            semantic_specification="the self-dual [24,12,8] code",
            evidence="GLM.ZeroStorageV5.syndromeZero_iff_isGolay, and the census here",
            evidence_kind="proved",
            resource_report="12 AND-popcount-parity operations against 36 bytes",
            caching="the 4096-word table breaks even after the count in caching_table()",
        ),
        Admission(
            system="Number-theoretic transform",
            compact_description="two integers (p, g); twiddles are powers of a generated root",
            direct_query="w_k in O(log k) multiplications; convolution without a matrix",
            semantic_specification="A_i = sum_j a_j w^{ij} over Z/pZ",
            evidence="GLM.PCGS.ntt_intt for the definition; the radix-2 algorithm is a checked transcription of it",
            evidence_kind="checked transcription",
            resource_report="measured against declared: (n/2)log n butterflies, 2 mul + 1 add + 1 sub each",
            caching="a twiddle table is n*ceil(log2 p) bits against two integers",
        ),
        Admission(
            system="Sparse stencil operator",
            compact_description="the stencil and the dimension",
            direct_query="matrix-vector product without the matrix",
            semantic_specification="the banded Toeplitz operator of that stencil",
            evidence="agreement with the dense matrix on exact rational inputs",
            evidence_kind="tested",
            resource_report="|stencil| multiply-adds per row; description |stencil|+1 against n^2",
            caching="materialising is never worth it while the stencil is shorter than a row",
        ),
        Admission(
            system="Finite-state transducer",
            compact_description="the transition and output functions",
            direct_query="the output stream for one input stream",
            semantic_specification="the exact running mean of the prefix",
            evidence="agreement with recomputation from scratch at every prefix",
            evidence_kind="tested",
            resource_report="one state pair carried; the extensional object is infinite",
            caching="there is nothing to cache: the extension does not exist",
        ),
        Admission(
            system="Cost algebra and physical layer",
            compact_description="seven counters, four physical constants",
            direct_query="the energy floor of a measured ledger",
            semantic_specification="Landauer's kT ln 2 per bit erased; half C V squared per gate transition",
            evidence="GLM.PCGS.Cost.*, bitsErased_reversible, landauerEnergy_mono, landauerEnergy_le_of_le_log_two, ln2Lower_100_le_log_two",
            evidence_kind="proved",
            resource_report="the ledger is the report",
            caching="not applicable: nothing is generated twice",
        ),
    ]


def pcgs_report() -> Dict[str, object]:
    """Everything in this module, run: the figures the study quotes."""

    admissions = admission_table()
    return {
        "codes": code_report(),
        "transform": transform_report(),
        "operator": operator_report(),
        "transducer": transducer_report(),
        "physical": physical_report(),
        "caching": caching_table(),
        "admission": [
            {
                "system": row.system,
                "evidence_kind": row.evidence_kind,
                "admitted": row.admitted(),
            }
            for row in admissions
        ],
        "admitted_count": sum(1 for row in admissions if row.admitted()),
        "system_count": len(admissions),
        "proved_count": sum(1 for row in admissions if row.evidence_kind == "proved"),
    }
