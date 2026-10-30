"""Three domains, described rather than coded.

Each of the three registers below was built by hand in an earlier round --
:mod:`glm_universal.data_objects.harmonics` (Phase 13),
:mod:`glm_universal.data_objects.economics_register` (Phase 17) and
:mod:`glm_universal.data_objects.comparison_classes` (Phase 16) -- each with
its own carrier method, its own codec and its own layer audit.  This module
writes down what each of them *is*, in the vocabulary of
:mod:`glm_universal.recipe.spec`, and nothing else: no carrier is built here,
no codec is written here, and no audit is run here.
:mod:`glm_universal.recipe.build` does all of that generically, and
:func:`glm_universal.recipe.build.regeneration` checks the result against the
hand-written register coordinate by coordinate.

What the descriptions measure
-----------------------------
A coordinate is either a **derivation** -- one of the shared primitives, which
serve a frequency ratio and a quoted price and a comparison bracket alike -- or
a **judgement** the domain has to state for itself.  The counts are the
interesting part, and they are reported rather than claimed:

* the comparison-class register needs **no judgement at all**: every one of its
  24 coordinates is a shared primitive over the bracket and the physics
  register;
* the economics register needs none either;
* the harmonic register needs **six**, and they are exactly the musical
  conventions -- twelve-tone equal temperament, Euler's weighting of a prime by
  ``p - 1``, what counts as a comma, and which ratios are read as harmonics or
  subharmonics of a power of two.

That is the shape the plan predicted: the *judgements* are what does not
generalise, and a description makes them countable instead of invisible.
"""

from __future__ import annotations

from contextlib import contextmanager
from fractions import Fraction
from typing import Any, Dict, Iterator, Mapping, Sequence, Tuple

from ..data_objects import comparison_classes as cc
from ..data_objects import economics_register as er
from ..data_objects import harmonics as hm
from ..data_objects import physics as ph
from .spec import (Coordinate, DomainSpec, Reading, affine_position,
                   comparison_sign, denominator, difference, distinct_primes,
                   exponent_weight, flag, held, indicator_between,
                   indicator_equals, judgement, largest_exponent, log_bucket,
                   maximum, midpoint, numerator, odd_part, p_adic_exponent,
                   prime_exponents, prime_limit, product, quotient, text_part,
                   vocabulary_index, borrowed)

__all__ = [
    "HARMONIC_DESCRIPTION", "ECONOMICS_DESCRIPTION", "COMPARISON_DESCRIPTION",
    "DESCRIPTIONS", "description_by_name", "described_domains",
]


# ===========================================================================
# 0.  SUBSTITUTING A REGENERATED REGISTER FOR THE SHIPPED ONE
# ===========================================================================

@contextmanager
def _patched(module: Any, attribute: str, value: Any,
             caches: Sequence[Any] = ()) -> Iterator[None]:
    """Put a regenerated register where the shipped modules read from."""
    original = getattr(module, attribute)
    for cache in caches:
        cache.cache_clear()
    setattr(module, attribute, value)
    try:
        yield
    finally:
        setattr(module, attribute, original)
        for cache in caches:
            cache.cache_clear()


# ===========================================================================
# 1.  THE HARMONIC REGISTER
# ===========================================================================

def _harmonic_facts() -> Tuple[Mapping[str, Any], ...]:
    """What the harmonic domain holds: a name, an exact ratio, a degree."""
    return tuple({"name": interval.name,
                  "ratio": interval.ratio,
                  "degree": interval.degree}
                 for interval in hm.interval_register())


def _tet_step(facts: Mapping[str, Any]) -> int:
    """The nearest 12-TET step, decided by integer comparison alone."""
    ratio = Fraction(facts["ratio"])
    power = ratio ** 24
    two = Fraction(2)
    k = 0
    while power >= two ** (2 * k + 1):
        k += 1
    while power < two ** (2 * k - 1):
        k -= 1
    return k


def _tet_error(facts: Mapping[str, Any]) -> Fraction:
    return (Fraction(facts["ratio"]) ** 12) / Fraction(2) ** _tet_step(facts)


def _euler_gradus(facts: Mapping[str, Any]) -> int:
    total = 1
    for prime, exponent in prime_exponents(Fraction(facts["ratio"])).items():
        total += abs(exponent) * (prime - 1)
    return total


def _is_power_of_two(value: int) -> bool:
    return value > 0 and value & (value - 1) == 0


def _harmonic_index(facts: Mapping[str, Any]) -> int:
    ratio = Fraction(facts["ratio"])
    return ratio.numerator if _is_power_of_two(ratio.denominator) else 0


def _subharmonic_index(facts: Mapping[str, Any]) -> int:
    ratio = Fraction(facts["ratio"])
    return ratio.denominator if _is_power_of_two(ratio.numerator) else 0


def _is_comma(facts: Mapping[str, Any]) -> int:
    ratio = Fraction(facts["ratio"])
    return 1 if (_tet_step(facts) == 0 and ratio != 1) else 0


_TET_ERROR = judgement(
    "(n/d)^12 / 2^step against twelve-tone equal temperament", _tet_error)

_HARMONIC_COORDINATES: Tuple[Coordinate, ...] = (
    Coordinate("numerator", numerator("ratio"), "the held ratio"),
    Coordinate("denominator", denominator("ratio"), "the held ratio"),
    Coordinate("exponent_2", p_adic_exponent("ratio", 2), "the held ratio"),
    Coordinate("exponent_3", p_adic_exponent("ratio", 3), "the held ratio"),
    Coordinate("exponent_5", p_adic_exponent("ratio", 5), "the held ratio"),
    Coordinate("exponent_7", p_adic_exponent("ratio", 7), "the held ratio"),
    Coordinate("prime_limit", prime_limit("ratio"), "the held ratio"),
    Coordinate("odd_limit",
               maximum(odd_part("ratio", "numerator"),
                       odd_part("ratio", "denominator")),
               "the held ratio"),
    Coordinate("product_complexity",
               product(numerator("ratio"), denominator("ratio")),
               "the held ratio -- Tenney height, unlogged"),
    Coordinate("euler_gradus",
               judgement("1 + sum e_p (p - 1): Euler's gradus suavitatis "
                         "weights a prime by p - 1", _euler_gradus),
               "a stated measure of consonance"),
    Coordinate("tet_step",
               judgement("the nearest step of twelve-tone equal temperament, "
                         "decided by comparing r^24 against powers of two",
                         _tet_step),
               "a stated tuning"),
    Coordinate("tet_error", _TET_ERROR, "a stated tuning"),
    Coordinate("tet_sharper", comparison_sign(_TET_ERROR, 1),
               "the tempering error"),
    Coordinate("superparticular",
               indicator_equals(
                   difference(numerator("ratio"), denominator("ratio")), 1),
               "the held ratio"),
    Coordinate("within_octave", indicator_between("ratio", 1, 2),
               "the held ratio"),
    Coordinate("distinct_primes", distinct_primes("ratio"),
               "the held ratio"),
    Coordinate("numerator_odd_part", odd_part("ratio", "numerator"),
               "the held ratio"),
    Coordinate("denominator_odd_part", odd_part("ratio", "denominator"),
               "the held ratio"),
    Coordinate("harmonic_index",
               judgement("n when d is a power of two: the ratio is read as a "
                         "harmonic of a fundamental", _harmonic_index),
               "a stated reading of the harmonic series"),
    Coordinate("subharmonic_index",
               judgement("d when n is a power of two: the ratio is read as a "
                         "subharmonic", _subharmonic_index),
               "a stated reading of the harmonic series"),
    Coordinate("exponent_weight", exponent_weight("ratio"),
               "the held ratio"),
    Coordinate("largest_exponent", largest_exponent("ratio"),
               "the held ratio"),
    Coordinate("diatonic_degree", held("degree"),
               "the held degree of the 5-limit major scale"),
    Coordinate("is_comma",
               judgement("within a tempered semitone of the unison, and not "
                         "the unison", _is_comma),
               "a stated reading of the tempering error"),
)


def _harmonic_rebuild(keyed: Mapping[str, Any],
                      labels: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "name": labels.get("name", "interval"),
        "ratio": Fraction(int(keyed["numerator"]), int(keyed["denominator"])),
        "degree": int(keyed["diatonic_degree"]),
    }


def _harmonic_native(facts: Mapping[str, Any]) -> hm.Interval:
    return hm.Interval(name=str(facts["name"]), ratio=Fraction(facts["ratio"]),
                       degree=int(facts["degree"]))


def _install_intervals(intervals: Sequence[hm.Interval]):
    from ..reasoning import harmony as hy
    return _patched(hm, "interval_register", lambda: tuple(intervals),
                    caches=(hy.harmony_report,))


def _harmonic_figures() -> Tuple[Tuple[str, Any], ...]:
    from ..reasoning import harmony as hy
    return (
        ("register summary", hm.register_summary),
        ("temperament table", hy.temperament_table),
        ("consonance orderings", hy.consonance_orderings),
    )


def _harmonic_figures_exhaustive() -> Tuple[Tuple[str, Any], ...]:
    from ..reasoning import harmony as hy
    return (("harmony report", hy.harmony_report),)


HARMONIC_DESCRIPTION = DomainSpec(
    name="harmonics",
    gloss="an interval as an exact frequency ratio",
    facts=_harmonic_facts,
    coordinates=_HARMONIC_COORDINATES,
    keys=("numerator", "denominator", "diatonic_degree"),
    rebuild=_harmonic_rebuild,
    labels=("name",),
    readings=(
        Reading("ratio", ("numerator", "denominator"),
                "the interval itself, and nothing about it"),
        Reading("arithmetic",
                ("numerator", "denominator", "exponent_2", "exponent_3",
                 "exponent_5", "exponent_7", "prime_limit", "odd_limit",
                 "product_complexity", "distinct_primes",
                 "numerator_odd_part", "denominator_odd_part",
                 "exponent_weight", "largest_exponent"),
                "what arithmetic alone says about the ratio"),
        Reading("full", tuple(c.name for c in _HARMONIC_COORDINATES),
                "the whole description, tuning and reading included"),
    ),
    refuses=("cents", "beat_rate", "timbre"),
    native=_harmonic_native,
    natives=lambda: tuple(hm.interval_register()),
    shipped=lambda: tuple(interval.carrier()
                          for interval in hm.interval_register()),
    figures=_harmonic_figures(),
    figures_exhaustive=_harmonic_figures_exhaustive(),
    install=_install_intervals,
)


# ===========================================================================
# 2.  THE ECONOMIC REGISTER
# ===========================================================================

def _economics_facts() -> Tuple[Mapping[str, Any], ...]:
    return tuple({
        "name": record.key,
        "identifier": record.identifier,
        "sector": record.sector,
        "priced_quantity": record.priced_quantity,
        "quoting_unit": record.quoting_unit,
        "quoting_multiplier": record.quoting_multiplier,
        "denominator_physical_quantity": record.denominator_physical_quantity,
        "is_dimensionless_currency": record.is_dimensionless_currency,
        "price": record.price,
        "observation_window": record.observation_window,
        "precision_sig_figs": record.precision_sig_figs,
        "retrieval_date": record.retrieval_date,
        "reference_source": record.reference_source,
    } for record in er.load_price_register())


def _ext10_of_quantity(name: str, axis: int) -> Fraction:
    """One EXT10 exponent of a named quantity, read from the physics register.

    ``dimensionless`` is the register's sentinel for a currency pair, which
    names no physical denominator at all and therefore carries no exponent.
    """
    if name == er.DIMENSIONLESS:
        return Fraction(0)
    return ph.quantity_by_name(name).exps_ext10[axis]


def _ext10_coordinates(key: str, source: str) -> Tuple[Coordinate, ...]:
    return tuple(
        Coordinate(
            f"ext10.{axis}",
            borrowed(key,
                     (lambda index: lambda name: _ext10_of_quantity(
                         name, index))(i),
                     f"physics register: EXT10 axis {axis} of {key}"),
            source)
        for i, axis in enumerate(ph.AXES_EXT10))


_ECONOMICS_COORDINATES: Tuple[Coordinate, ...] = (
    Coordinate("numerator", numerator("price"), "the quoted price"),
    Coordinate("denominator", denominator("price"), "the quoted price"),
    Coordinate("log_bucket_base_2", log_bucket("price", 2),
               "the quoted price"),
    Coordinate("log_bucket_base_10", log_bucket("price", 10),
               "the quoted price"),
    Coordinate("quoting_multiplier", held("quoting_multiplier"),
               "the quoting convention"),
    Coordinate("is_dimensionless", flag("is_dimensionless_currency"),
               "the quoting convention"),
    Coordinate("precision_sig_figs", held("precision_sig_figs"),
               "the quote's stated precision"),
    Coordinate("sector_index", vocabulary_index("sector", lambda: er.SECTORS,
                                                "sector in SECTORS"),
               "the register's sector vocabulary"),
    Coordinate("instrument_index",
               vocabulary_index("identifier", er.instrument_identifiers,
                                "identifier in instrument_identifiers()"),
               "the register's instruments, in first-appearance order"),
    Coordinate("window_index",
               vocabulary_index("observation_window", lambda: er.WINDOWS,
                                "observation_window in WINDOWS"),
               "the register's observation windows"),
    Coordinate("window_year", text_part("observation_window", "-", 0),
               "the observation window"),
    Coordinate("window_quarter", text_part("observation_window", "-Q", 1),
               "the observation window"),
) + _ext10_coordinates("denominator_physical_quantity",
                       "the physics register, through the denominator "
                       "quantity") + (
    Coordinate("quantity_index",
               vocabulary_index("denominator_physical_quantity",
                                er.denominator_quantities,
                                "denominator_physical_quantity in "
                                "denominator_quantities()"),
               "the register's denominator quantities"),
    Coordinate("price_is_integral",
               indicator_equals(denominator("price"), 1),
               "the quoted price"),
)


def _economics_rebuild(keyed: Mapping[str, Any],
                       labels: Mapping[str, Any]) -> Dict[str, Any]:
    quantity = er.denominator_quantities()[int(keyed["quantity_index"])]
    return {
        "name": labels.get("name", ""),
        "identifier": er.instrument_identifiers()[
            int(keyed["instrument_index"])],
        "sector": er.SECTORS[int(keyed["sector_index"])],
        "priced_quantity": labels.get("priced_quantity", ""),
        "quoting_unit": labels.get("quoting_unit", ""),
        "quoting_multiplier": int(keyed["quoting_multiplier"]),
        "denominator_physical_quantity": quantity,
        "is_dimensionless_currency": bool(int(keyed["is_dimensionless"])),
        "price": Fraction(int(keyed["numerator"]), int(keyed["denominator"])),
        "observation_window": er.WINDOWS[int(keyed["window_index"])],
        "precision_sig_figs": int(keyed["precision_sig_figs"]),
        "retrieval_date": labels.get("retrieval_date", ""),
        "reference_source": labels.get("reference_source", ""),
    }


def _economics_native(facts: Mapping[str, Any]) -> er.PriceRecord:
    return er.PriceRecord(
        identifier=str(facts["identifier"]),
        sector=str(facts["sector"]),
        priced_quantity=str(facts["priced_quantity"]),
        quoting_unit=str(facts["quoting_unit"]),
        quoting_multiplier=int(facts["quoting_multiplier"]),
        denominator_physical_quantity=str(
            facts["denominator_physical_quantity"]),
        is_dimensionless_currency=bool(facts["is_dimensionless_currency"]),
        price=Fraction(facts["price"]),
        observation_window=str(facts["observation_window"]),
        precision_sig_figs=int(facts["precision_sig_figs"]),
        retrieval_date=str(facts["retrieval_date"]),
        reference_source=str(facts["reference_source"]))


def _install_prices(records: Sequence[er.PriceRecord]):
    return _patched(er, "load_price_register", lambda: tuple(records),
                    caches=(er.instrument_identifiers,
                            er.denominator_quantities))


def _economics_figures() -> Tuple[Tuple[str, Any], ...]:
    from ..reasoning import economics as ecn
    return (
        ("register summary", er.register_summary),
        ("magnitude table", ecn.magnitude_table),
    )


ECONOMICS_DESCRIPTION = DomainSpec(
    name="economics",
    gloss="a quoted price as an exact rational, in a stated window",
    facts=_economics_facts,
    coordinates=_ECONOMICS_COORDINATES,
    keys=("numerator", "denominator", "quoting_multiplier",
          "is_dimensionless", "precision_sig_figs", "sector_index",
          "instrument_index", "window_index", "quantity_index"),
    rebuild=_economics_rebuild,
    labels=("name", "priced_quantity", "quoting_unit", "retrieval_date",
            "reference_source"),
    readings=(
        Reading("price", ("numerator", "denominator"),
                "the number quoted, and nothing about what it prices"),
        Reading("magnitude",
                ("numerator", "denominator", "log_bucket_base_2",
                 "log_bucket_base_10", "quoting_multiplier",
                 "precision_sig_figs", "price_is_integral"),
                "the price and its exact magnitude bucket"),
        Reading("full", tuple(c.name for c in _ECONOMICS_COORDINATES),
                "the whole description, instrument and dimension included"),
    ),
    refuses=("volatility", "bid_ask_spread", "market_capitalisation"),
    native=_economics_native,
    natives=lambda: tuple(er.load_price_register()),
    shipped=lambda: tuple(er.PriceCodec().encode(record).carrier
                          for record in er.load_price_register()),
    figures=_economics_figures(),
    install=_install_prices,
)


# ===========================================================================
# 3.  THE COMPARISON-CLASS REGISTER
# ===========================================================================

def _comparison_facts() -> Tuple[Mapping[str, Any], ...]:
    return tuple({"name": entry.name,
                  "quantity": entry.quantity,
                  "low": entry.low,
                  "high": entry.high,
                  "typical": entry.typical,
                  "gloss": entry.gloss}
                 for entry in cc.comparison_classes())


def _physics_names() -> Tuple[str, ...]:
    return tuple(q.name for q in ph.load_physics_register())


def _nonzero_exponents(name: str) -> int:
    return sum(1 for e in ph.quantity_by_name(name).exps_ext10 if e != 0)


def _si7_lossy(name: str) -> int:
    return 1 if ph.si7_projection_lossy(ph.quantity_by_name(name)) else 0


def _scale_words(name: str) -> int:
    scale = cc.MEASURE_SCALES.get(name)
    return len(scale.words) if scale is not None else 0


_COMPARISON_COORDINATES: Tuple[Coordinate, ...] = tuple(
    Coordinate(f"ext10.{axis}",
               borrowed("quantity",
                        (lambda index: lambda name: ph.quantity_by_name(
                            name).exps_ext10[index])(i),
                        f"physics register: EXT10 axis {axis} of quantity"),
               "the physics register, through the class's quantity")
    for i, axis in enumerate(ph.AXES_EXT10)) + (
    Coordinate("low", held("low"), "the bracket, in SI base units"),
    Coordinate("high", held("high"), "the bracket, in SI base units"),
    Coordinate("typical", held("typical"),
               "the typical magnitude of a member"),
    Coordinate("span", difference("high", "low"), "the bracket"),
    Coordinate("midpoint", midpoint("low", "high"), "the bracket"),
    Coordinate("typical_position",
               affine_position("typical", "low", "high"),
               "the typical magnitude, on the bracket's own scale"),
    Coordinate("span_ratio", quotient("high", "low"), "the bracket"),
    Coordinate("decimal_scale", log_bucket("typical", 10),
               "the typical magnitude"),
    Coordinate("quantity_index",
               vocabulary_index("quantity", _physics_names,
                                "quantity in the physics register"),
               "the physics register"),
    Coordinate("domain_index",
               borrowed("quantity",
                        lambda name: ph.quantity_by_name(name).domain_index,
                        "physics register: domain_index of quantity"),
               "the physics register"),
    Coordinate("nonzero_exponents",
               borrowed("quantity", _nonzero_exponents,
                        "physics register: nonzero EXT10 axes of quantity"),
               "the physics register"),
    Coordinate("si7_lossy",
               borrowed("quantity", _si7_lossy,
                        "physics register: EXT10 -> SI7 discards an exponent"),
               "the physics register"),
    Coordinate("scale_words",
               borrowed("quantity", _scale_words,
                        "measure scales: how many degree words the quantity "
                        "has"),
               "the measure-scale register"),
    Coordinate("spans_decades",
               log_bucket(quotient("high", "low"), 10), "the bracket"),
)


def _comparison_rebuild(keyed: Mapping[str, Any],
                        labels: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "name": labels.get("name", "class"),
        "quantity": _physics_names()[int(keyed["quantity_index"])],
        "low": Fraction(keyed["low"]),
        "high": Fraction(keyed["high"]),
        "typical": Fraction(keyed["typical"]),
        "gloss": labels.get("gloss", ""),
    }


def _comparison_native(facts: Mapping[str, Any]) -> cc.ComparisonClass:
    return cc.ComparisonClass(name=str(facts["name"]),
                              quantity=str(facts["quantity"]),
                              low=Fraction(facts["low"]),
                              high=Fraction(facts["high"]),
                              typical=Fraction(facts["typical"]),
                              gloss=str(facts["gloss"]))


def _install_classes(classes: Sequence[cc.ComparisonClass]):
    return _patched(cc, "COMPARISON_CLASSES", tuple(classes))


def _comparison_figures() -> Tuple[Tuple[str, Any], ...]:
    from ..reasoning import measure_view as mvw
    return (
        ("register summary", cc.register_summary),
        ("lexicon agreement", cc.lexicon_agreement),
        ("transport audit", mvw.transport_audit),
        ("comparative audit", mvw.comparative_audit),
    )


def _comparison_figures_exhaustive() -> Tuple[Tuple[str, Any], ...]:
    from ..reasoning import measure_view as mvw
    return (("widening audit", mvw.widening_audit),)


COMPARISON_DESCRIPTION = DomainSpec(
    name="comparison",
    gloss="a comparison class as an exact bracket on one held quantity",
    facts=_comparison_facts,
    coordinates=_COMPARISON_COORDINATES,
    keys=("low", "high", "typical", "quantity_index"),
    rebuild=_comparison_rebuild,
    labels=("name", "gloss"),
    readings=(
        Reading("bracket", ("low", "high"),
                "the bracket, and nothing about what it brackets"),
        Reading("measured",
                ("low", "high", "typical", "span", "midpoint",
                 "typical_position", "span_ratio", "decimal_scale",
                 "spans_decades"),
                "the bracket and everything the bracket alone decides"),
        Reading("full", tuple(c.name for c in _COMPARISON_COORDINATES),
                "the whole description, dimension included"),
    ),
    refuses=("colour", "loudness", "prototypicality"),
    native=_comparison_native,
    natives=lambda: tuple(cc.comparison_classes()),
    shipped=lambda: tuple(entry.carrier()
                          for entry in cc.comparison_classes()),
    figures=_comparison_figures(),
    figures_exhaustive=_comparison_figures_exhaustive(),
    install=_install_classes,
)


# ===========================================================================
# 4.  THE CATALOGUE OF DESCRIPTIONS
# ===========================================================================

#: Every domain described here, in the order the phases built them.
DESCRIPTIONS: Tuple[DomainSpec, ...] = (
    COMPARISON_DESCRIPTION,
    HARMONIC_DESCRIPTION,
    ECONOMICS_DESCRIPTION,
)


def described_domains() -> Tuple[str, ...]:
    """The names of the domains that have a description."""
    return tuple(spec.name for spec in DESCRIPTIONS)


def description_by_name(name: str) -> DomainSpec:
    """One description, by domain name."""
    for spec in DESCRIPTIONS:
        if spec.name == name:
            return spec
    raise KeyError(f"recipe: no description of a domain called {name!r}")
