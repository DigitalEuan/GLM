"""The economic register: quoted prices as exact rationals, with a magnitude.

Why an economic register
------------------------
The supplied study catalogue makes one universality claim in three parts:
chemical equilibria, musical harmony and **market price discovery** all map to
proximity in the Leech lattice.  :mod:`glm_universal.data_objects.harmonics`
supplied the musical third, and
:mod:`glm_universal.reasoning.harmony` measured it.  The economic third has
been recorded as *not implemented* in :mod:`glm_universal.reasoning.catalog`
for a plain reason: there was no register of prices to run it against, and a
claim nothing can be run against is not a finding.  This module supplies one.

What a price is here
--------------------
A record is one instrument in one observation window: an exact rational price
in a named quoting unit, the physical quantity the price is *per*, and the
provenance of the number.  Twenty-one records over seven instruments and three
consecutive quarterly windows -- so the register carries a time series, not a
snapshot, which is what lets co-movement be measured rather than assumed.

Nothing is stored as a float.  ``2070/1``, ``47/2``, ``377/5``, ``137/200``:
every price in ``_data/economics_register.csv`` is written as a fraction and
parsed with :class:`fractions.Fraction`, so the exact-rational contract the
rest of the package keeps is kept here too.

Magnitude without a logarithm
-----------------------------
A price vector needs a *scale-invariant magnitude descriptor*, and the obvious
one is ``floor(log_b x)``.  A logarithm is a transcendental function evaluated
in floating point, which this package does not do.  :func:`compute_exact_log_bucket`
computes the same integer by comparison alone: ``k`` is the unique integer with

.. math::  b^k \\le x < b^{k+1}

and for ``x = p/q`` in lowest terms that is decided by integer multiplication,
``q b^k \\le p < q b^{k+1}`` when ``k \\ge 0`` and the mirrored comparison when
``k < 0``.  No float is constructed and no precision is lost.  The existence
and uniqueness of that ``k``, its agreement with the integer comparisons, and
its monotonicity in ``x`` are proved in ``RequestProject/GLM/LogBucket.lean``.

The 24-coordinate layout
------------------------
Twelve market coordinates, the ten EXT10 exponents of the physical quantity
the price is quoted per, the index of that quantity, and one redundancy flag::

    0   numerator            p of the price in lowest terms
    1   denominator          q of the price in lowest terms
    2   log_bucket_base_2    the unique k with 2^k <= price < 2^(k+1)
    3   log_bucket_base_10   the unique k with 10^k <= price < 10^(k+1)
    4   quoting_multiplier   the price is per this many units
    5   is_dimensionless     1 for a currency pair, 0 otherwise
    6   precision_sig_figs   significant figures the source quotes
    7   sector_index         index into SECTORS
    8   instrument_index     index into instrument_identifiers()
    9   window_index         index into WINDOWS
    10  window_year
    11  window_quarter       1, 2 or 3
    12..21  ext10 exponents of the denominator quantity (all zero for a pair)
    22  quantity_index       index into denominator_quantities()
    23  price_is_integral    1 when q == 1  (redundant, and checked on decode)

Coordinate 23 is derived from coordinate 1, deliberately: a decoder that read
the wrong slice would disagree with itself, exactly as the redundant SI7 slice
does in :mod:`glm_universal.data_objects.physics`.

What is *not* claimed
---------------------
The prices are quarterly reference levels from public series, recorded to the
significant figures the source quotes; they are a register to compute against,
not a market feed.  Whether proximity in the Leech lattice says anything about
them is measured in :mod:`glm_universal.reasoning.economics` and is not
assumed here.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from .base import Codec, DataObject, Scalar, as_exact
from .physics import AXES_EXT10, quantity_by_name

__all__ = [
    "ECONOMICS_LAYOUT",
    "SECTORS",
    "WINDOWS",
    "DIMENSIONLESS",
    "PriceRecord",
    "PriceCodec",
    "compute_exact_log_bucket",
    "bucket_bounds_hold",
    "denominator_quantities",
    "economics_objects",
    "instrument_identifiers",
    "instrument_series",
    "load_price_register",
    "record_by_key",
    "register_summary",
]

_DATA = Path(__file__).resolve().parent / "_data" / "economics_register.csv"

#: The name the register uses for a price with no physical denominator: a
#: currency pair is a ratio of two currencies and is dimensionless.  It is not
#: a physics-register quantity and must not be looked up as one.
DIMENSIONLESS = "dimensionless"

#: Sectors, in a fixed order, so the index coordinate is stable.
SECTORS: Tuple[str, ...] = ("Agriculture", "Currency", "Energy",
                            "Precious Metals")

#: Observation windows, in chronological order.
WINDOWS: Tuple[str, ...] = ("2024-Q1", "2024-Q2", "2024-Q3")

#: Names of the 24 carrier coordinates, in order.
ECONOMICS_LAYOUT: Tuple[str, ...] = (
    "numerator",             # 0
    "denominator",           # 1
    "log_bucket_base_2",     # 2
    "log_bucket_base_10",    # 3
    "quoting_multiplier",    # 4
    "is_dimensionless",      # 5
    "precision_sig_figs",    # 6
    "sector_index",          # 7
    "instrument_index",      # 8
    "window_index",          # 9
    "window_year",           # 10
    "window_quarter",        # 11
) + tuple(f"ext10.{a}" for a in AXES_EXT10) + (   # 12..21
    "quantity_index",        # 22
    "price_is_integral",     # 23
)
assert len(ECONOMICS_LAYOUT) == 24


# ===========================================================================
# 1.  EXACT LOG-SCALE BUCKETING
# ===========================================================================

def compute_exact_log_bucket(price: Fraction, base: int = 2) -> int:
    """``floor(log_base(price))``, by integer comparison alone.

    The unique integer ``k`` with ``base**k <= price < base**(k+1)``.  For a
    price ``p/q`` in lowest terms the two comparisons are

    * ``k >= 0``:  ``q * base**k <= p``  and  ``p < q * base**(k+1)``;
    * ``k < 0``:   ``p * base**(-k) <= q`` fails and ``p * base**(-k-1) < q``,

    both decided by multiplying integers.  No logarithm is evaluated, no float
    is constructed, and nothing is rounded, so the answer is exact for a price
    of any magnitude.

    :raises ValueError: for a price that is not strictly positive -- a
        magnitude is not defined at or below zero, and returning a sentinel
        would make the exactness claim unfalsifiable -- or for a base below 2,
        where the bucket is not unique.
    """
    price = as_exact(price)
    if price <= 0:
        raise ValueError(
            "economics_register: magnitude tracking requires strictly "
            "positive prices")
    if not isinstance(base, int) or isinstance(base, bool) or base < 2:
        raise ValueError(
            "economics_register: the bucket base must be an integer above 1")

    p, q = price.numerator, price.denominator
    if price >= 1:
        k = 0
        power = base
        while p >= q * power:
            k += 1
            power *= base
        return k
    k = -1
    power = base
    while p * power < q:
        k -= 1
        power *= base
    return k


def bucket_bounds_hold(price: Fraction, base: int = 2) -> bool:
    """Whether ``base**k <= price < base**(k+1)`` for the computed ``k``.

    The defining property, checked on the rationals themselves rather than on
    the integer comparisons that produced ``k``.  It is the falsifier for
    :func:`compute_exact_log_bucket`: a bucket that failed it would be wrong
    no matter how it was derived.
    """
    price = as_exact(price)
    k = compute_exact_log_bucket(price, base)
    lower = Fraction(base) ** k
    upper = Fraction(base) ** (k + 1)
    return lower <= price < upper


# ===========================================================================
# 2.  THE RECORD
# ===========================================================================

@dataclass(frozen=True)
class PriceRecord:
    """One instrument's quoted price in one observation window."""

    identifier: str
    sector: str
    priced_quantity: str
    quoting_unit: str
    quoting_multiplier: int
    denominator_physical_quantity: str
    is_dimensionless_currency: bool
    price: Fraction
    observation_window: str
    precision_sig_figs: int
    retrieval_date: str
    reference_source: str

    def __post_init__(self) -> None:
        if self.price <= 0:
            raise ValueError(f"{self.key}: a quoted price must be positive")
        if self.sector not in SECTORS:
            raise ValueError(f"{self.key}: unknown sector {self.sector!r}")
        if self.observation_window not in WINDOWS:
            raise ValueError(
                f"{self.key}: unknown window {self.observation_window!r}")
        if self.quoting_multiplier < 1:
            raise ValueError(f"{self.key}: the quoting multiplier must be "
                             f"a positive integer")
        if self.is_dimensionless_currency:
            if self.denominator_physical_quantity != DIMENSIONLESS:
                raise ValueError(
                    f"{self.key}: a currency pair is dimensionless and cannot "
                    f"name a physical denominator")
        else:
            # raises KeyError if the physics register does not hold it, which
            # is the point: a denominator nothing measures is not admitted
            quantity_by_name(self.denominator_physical_quantity)

    @property
    def key(self) -> str:
        """The register key: identifier and window, which is unique."""
        return f"{self.identifier}@{self.observation_window}"

    @property
    def exponents(self) -> Tuple[Fraction, ...]:
        """The EXT10 exponents of the denominator quantity; zero for a pair."""
        if self.is_dimensionless_currency:
            return tuple(Fraction(0) for _ in AXES_EXT10)
        return quantity_by_name(self.denominator_physical_quantity).exps_ext10

    @property
    def window_year(self) -> int:
        return int(self.observation_window.split("-")[0])

    @property
    def window_quarter(self) -> int:
        return int(self.observation_window.split("-Q")[1])

    def log_bucket(self, base: int = 2) -> int:
        """The exact magnitude bucket of this price."""
        return compute_exact_log_bucket(self.price, base)


# ===========================================================================
# 3.  THE REGISTER
# ===========================================================================

def _parse_bool(text: str, where: str) -> bool:
    lowered = text.strip().lower()
    if lowered in ("true", "1"):
        return True
    if lowered in ("false", "0"):
        return False
    raise ValueError(f"{where}: {text!r} is not a boolean")


@lru_cache(maxsize=1)
def load_price_register() -> Tuple[PriceRecord, ...]:
    """The register, parsed once from the frozen CSV.

    Every field is validated on the way in: the sector and window must be
    known, the price must be a positive fraction, and a non-currency record
    must name a quantity the physics register actually holds.  A record that
    fails any of those does not load, so the register cannot quietly acquire a
    denominator nothing measures.
    """
    rows: List[PriceRecord] = []
    with _DATA.open(encoding="utf-8", newline="") as handle:
        for line, raw in enumerate(csv.DictReader(handle), start=2):
            where = f"economics_register.csv line {line}"
            rows.append(PriceRecord(
                identifier=raw["identifier"].strip(),
                sector=raw["sector"].strip(),
                priced_quantity=raw["priced_quantity"].strip(),
                quoting_unit=raw["quoting_unit"].strip(),
                quoting_multiplier=int(raw["quoting_multiplier"]),
                denominator_physical_quantity=(
                    raw["denominator_physical_quantity"].strip()),
                is_dimensionless_currency=_parse_bool(
                    raw["is_dimensionless_currency"], where),
                price=Fraction(raw["numeric_price_fraction"].strip()),
                observation_window=raw["observation_window"].strip(),
                precision_sig_figs=int(raw["precision_sig_figs"]),
                retrieval_date=raw["retrieval_date"].strip(),
                reference_source=raw["reference_source"].strip(),
            ))
    keys = [r.key for r in rows]
    if len(set(keys)) != len(keys):
        raise AssertionError("economics_register: duplicate identifier/window")
    return tuple(rows)


@lru_cache(maxsize=1)
def instrument_identifiers() -> Tuple[str, ...]:
    """Every instrument in the register, in first-appearance order."""
    seen: List[str] = []
    for record in load_price_register():
        if record.identifier not in seen:
            seen.append(record.identifier)
    return tuple(seen)


@lru_cache(maxsize=1)
def denominator_quantities() -> Tuple[str, ...]:
    """The distinct denominator quantities, sorted, with ``dimensionless``."""
    return tuple(sorted({r.denominator_physical_quantity
                         for r in load_price_register()}))


def instrument_series(identifier: str) -> Tuple[PriceRecord, ...]:
    """One instrument's records, in chronological window order."""
    series = tuple(sorted((r for r in load_price_register()
                           if r.identifier == identifier),
                          key=lambda r: WINDOWS.index(r.observation_window)))
    if not series:
        raise KeyError(f"economics_register: no instrument {identifier!r}")
    return series


@lru_cache(maxsize=1)
def _by_key() -> Dict[str, PriceRecord]:
    return {r.key: r for r in load_price_register()}


def record_by_key(key: str) -> PriceRecord:
    """Look a record up by ``identifier@window``."""
    try:
        return _by_key()[key]
    except KeyError:
        raise KeyError(f"economics_register: no record {key!r}") from None


def register_summary() -> Dict[str, object]:
    """What the register holds, counted rather than described."""
    records = load_price_register()
    buckets = sorted({r.log_bucket(2) for r in records})
    return {
        "records": len(records),
        "instruments": len(instrument_identifiers()),
        "sectors": len(sorted({r.sector for r in records})),
        "windows": len(WINDOWS),
        "currency_pairs": sum(1 for r in records
                              if r.is_dimensionless_currency),
        "denominator_quantities": denominator_quantities(),
        "base_2_buckets": tuple(buckets),
        "base_2_bucket_span": buckets[-1] - buckets[0],
        "integral_prices": sum(1 for r in records
                               if r.price.denominator == 1),
        "all_bounds_hold": all(bucket_bounds_hold(r.price, b)
                               for r in records for b in (2, 10)),
    }


# ===========================================================================
# 4.  THE CODEC
# ===========================================================================

class PriceCodec(Codec):
    """Embed a :class:`PriceRecord` in ``Q^24`` and read it back exactly."""

    domain = "economics"
    layout = ECONOMICS_LAYOUT

    def encode(self, source: PriceRecord) -> DataObject:
        """The 24-coordinate carrier of a quoted price."""
        carrier: List[Scalar] = [
            source.price.numerator,
            source.price.denominator,
            source.log_bucket(2),
            source.log_bucket(10),
            source.quoting_multiplier,
            1 if source.is_dimensionless_currency else 0,
            source.precision_sig_figs,
            SECTORS.index(source.sector),
            instrument_identifiers().index(source.identifier),
            WINDOWS.index(source.observation_window),
            source.window_year,
            source.window_quarter,
        ]
        carrier.extend(source.exponents)
        carrier.append(denominator_quantities().index(
            source.denominator_physical_quantity))
        carrier.append(1 if source.price.denominator == 1 else 0)
        return DataObject(
            name=source.key, domain=self.domain, carrier=carrier,
            attributes={
                "identifier": source.identifier,
                "priced_quantity": source.priced_quantity,
                "quoting_unit": source.quoting_unit,
                "retrieval_date": source.retrieval_date,
                "reference_source": source.reference_source,
                "price": str(source.price),
            },
            layout=ECONOMICS_LAYOUT,
            provenance={
                "source": "_data/economics_register.csv",
                "magnitude": "exact integer bucketing, no logarithm",
            },
        )

    def decode(self, obj: DataObject) -> PriceRecord:
        """Recover the record.  Raises if the redundant slices disagree."""
        c = obj.carrier
        price = Fraction(int(c[0]), int(c[1]))
        if int(c[23]) != (1 if price.denominator == 1 else 0):
            raise ValueError(
                f"economics.decode: carrier is internally inconsistent for "
                f"{obj.name!r} -- the integrality flag does not match the "
                f"denominator")
        if int(c[2]) != compute_exact_log_bucket(price, 2):
            raise ValueError(
                f"economics.decode: carrier is internally inconsistent for "
                f"{obj.name!r} -- the base-2 magnitude bucket does not match "
                f"the price")
        attrs = obj.attributes
        dimensionless = int(c[5]) == 1
        quantity = denominator_quantities()[int(c[22])]
        return PriceRecord(
            identifier=attrs["identifier"],
            sector=SECTORS[int(c[7])],
            priced_quantity=attrs["priced_quantity"],
            quoting_unit=attrs["quoting_unit"],
            quoting_multiplier=int(c[4]),
            denominator_physical_quantity=quantity,
            is_dimensionless_currency=dimensionless,
            price=price,
            observation_window=WINDOWS[int(c[9])],
            precision_sig_figs=int(c[6]),
            retrieval_date=attrs["retrieval_date"],
            reference_source=attrs["reference_source"],
        )


def economics_objects() -> Tuple[DataObject, ...]:
    """Every record of the register as an encoded :class:`DataObject`."""
    codec = PriceCodec()
    return tuple(codec.encode(r) for r in load_price_register())
