"""Reference: from notation to meaning, or an explicit refusal.

What resolution is, and what it is not
--------------------------------------
:func:`resolve` maps a **term** -- a word, a numeral, a Roman numeral, an
arithmetic expression, a chemical formula, a register name, an operator sign
-- to the :class:`~.meaning.Meaning` it *denotes*, or to a refusal carrying
the reason.  It is a lookup of reference, not a similarity model.  Nothing is
guessed, nothing is embedded, nothing is hashed, and a term with no
determinate referent gets no carrier at all.

That refusal is the design.  The state this package inherited had grown to
4,282 concepts by minting a SHA-256 carrier for any string that crossed the
pipeline -- ``"abb"``, ``"ado"``, ``"ah"``.  A carrier derived from letters
cannot answer a question about the subject, so the graph built over those
carriers answered questions about letters.  Here a term is admitted only when
the repository can state exactly what it refers to.

The nine resolvers, in the order they are tried
-----------------------------------------------
======================  ====================================================
resolver                admits
======================  ====================================================
``arithmetic``          ``"2"``, ``"-7/2"``, ``"1.25"``, ``"2+2"``,
                        ``"(3*4)/2"``, ``"2^10"`` -- a full exact-rational
                        expression grammar over numerals *and* number words
``roman``               ``"XIV"``, ``"MCMXCIV"`` (strict, uppercase)
``number_word``         ``"zero"``..``"nineteen"``, the tens, ``"hundred"``,
                        ``"thousand"``, ``"million"``, their compounds
                        (``"twenty one"``, ``"three hundred and four"``),
                        and the exact fractional words ``"half"``,
                        ``"third"``, ``"quarter"``, plus ``"dozen"``,
                        ``"score"``, ``"pair"``, ``"gross"``
``si_constant``         the seven defining constants of the SI, whose values
                        are exact *by definition* since 2019
``element``             the 118 element names and the 118 symbols
``formula``             ``"H2O"``, ``"CO2"``, ``"Ca(OH)2"`` -- a formula
                        parser over the 118 symbols
``compound_name``       the named species whose formula is determinate
                        (``"water"``, ``"salt"``, ``"methane"``, ...)
``physics``             the 726 register quantity names, their symbols, and
                        the register's own alias table (``"heat"`` ->
                        ``energy``, ``"distance"`` -> ``length``)
``operation``           ``"+"``, ``"plus"``, ``"add"``, ``"sum"``, ``"*"``,
                        ``"times"``, ``"product"``, ... the eight operations
======================  ====================================================

Determinism and ambiguity
-------------------------
Every resolver is a pure function of frozen repository data.  Where two
resolvers would answer differently for the same term the term is **ambiguous**
and :func:`resolve` says so instead of silently preferring one: see
:func:`ambiguity_report`, which lists every such term in the union of the
registers.  Ordering the resolvers is therefore not a tie-break mechanism --
it is only a speed choice, and the report is what makes that checkable.

A term's *sense* (which resolver answered, and with what witness) travels
beside the meaning, so a resolution can always be audited back to the
register row that justified it.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from ..data_objects.elements import load_element_register
from ..data_objects.physics import load_physics_register
from .meaning import Meaning, zero_exponents

__all__ = [
    "Resolution", "resolve", "resolve_many", "is_grounded", "meaning_of",
    "SI_DEFINING_CONSTANTS", "COMPOUND_NAMES", "NUMBER_WORDS",
    "OPERATION_WORDS", "ambiguity_report", "coverage_report",
    "reference_terms", "senses_of",
]

_RELATIONS = (Path(__file__).resolve().parent.parent / "reasoning" / "_data"
              / "physics_relations.json")


# ===========================================================================
# 1.  RESOLUTIONS
# ===========================================================================

@dataclass(frozen=True)
class Resolution:
    """The outcome of resolving one term.

    ``meaning`` is ``None`` exactly when the term has no determinate referent
    in the repository's registers; ``reason`` then says why, in words a reader
    can act on.  ``sense`` names the resolver that answered and ``witness``
    records the register row, so nothing here is unauditable.
    """

    term: str
    meaning: Optional[Meaning]
    sense: str
    witness: str
    reason: str = ""

    @property
    def grounded(self) -> bool:
        """Whether the term denotes something determinate."""
        return self.meaning is not None

    def as_dict(self) -> Dict[str, object]:
        """A JSON-serialisable view."""
        return {
            "term": self.term,
            "grounded": self.grounded,
            "sense": self.sense,
            "witness": self.witness,
            "reason": self.reason,
            "meaning": self.meaning.as_dict() if self.meaning else None,
        }


def _refused(term: str, reason: str) -> Resolution:
    return Resolution(term=term, meaning=None, sense="none", witness="",
                      reason=reason)


# ===========================================================================
# 2.  NUMBERS: numerals, number words, Roman numerals, arithmetic
# ===========================================================================

#: Number words with a determinate exact value.
NUMBER_WORDS: Dict[str, Fraction] = {
    "zero": Fraction(0), "nought": Fraction(0), "nil": Fraction(0),
    "one": Fraction(1), "two": Fraction(2), "three": Fraction(3),
    "four": Fraction(4), "five": Fraction(5), "six": Fraction(6),
    "seven": Fraction(7), "eight": Fraction(8), "nine": Fraction(9),
    "ten": Fraction(10), "eleven": Fraction(11), "twelve": Fraction(12),
    "thirteen": Fraction(13), "fourteen": Fraction(14),
    "fifteen": Fraction(15), "sixteen": Fraction(16),
    "seventeen": Fraction(17), "eighteen": Fraction(18),
    "nineteen": Fraction(19), "twenty": Fraction(20),
    "thirty": Fraction(30), "forty": Fraction(40), "fifty": Fraction(50),
    "sixty": Fraction(60), "seventy": Fraction(70), "eighty": Fraction(80),
    "ninety": Fraction(90),
    # exact fractional and collective words
    "half": Fraction(1, 2), "third": Fraction(1, 3),
    "quarter": Fraction(1, 4), "fourth": Fraction(1, 4),
    "eighth": Fraction(1, 8), "tenth": Fraction(1, 10),
    "pair": Fraction(2), "couple": Fraction(2), "dozen": Fraction(12),
    "score": Fraction(20), "gross": Fraction(144),
}

_MULTIPLIERS: Dict[str, Fraction] = {
    "hundred": Fraction(100), "thousand": Fraction(1000),
    "million": Fraction(10 ** 6), "billion": Fraction(10 ** 9),
    "trillion": Fraction(10 ** 12),
}

_ROMAN_VALUES = (("M", 1000), ("CM", 900), ("D", 500), ("CD", 400),
                 ("C", 100), ("XC", 90), ("L", 50), ("XL", 40),
                 ("X", 10), ("IX", 9), ("V", 5), ("IV", 4), ("I", 1))

_NUMERAL_RE = re.compile(r"^[+-]?(\d+(\.\d+)?|\d*\.\d+)(/\d+)?$")


def _numeral_value(text: str) -> Optional[Fraction]:
    """The exact rational a numeral string denotes, or ``None``."""
    if not _NUMERAL_RE.match(text):
        return None
    try:
        return Fraction(text)
    except (ValueError, ZeroDivisionError):
        return None


def _roman_value(text: str) -> Optional[int]:
    """The integer a strict uppercase Roman numeral denotes, or ``None``."""
    if not text or not re.fullmatch(r"[MDCLXVI]+", text):
        return None
    total, i = 0, 0
    for symbol, value in _ROMAN_VALUES:
        while text.startswith(symbol, i):
            total += value
            i += len(symbol)
    if i != len(text):
        return None
    # Canonicity: the value must render back to the same string.
    rendered, rest = [], total
    for symbol, value in _ROMAN_VALUES:
        while rest >= value:
            rendered.append(symbol)
            rest -= value
    return total if "".join(rendered) == text else None


def _number_word_value(text: str) -> Optional[Fraction]:
    """The exact value of an English cardinal phrase, or ``None``.

    Handles the standard grammar: units, teens, tens with an optional unit,
    and the multipliers hundred / thousand / million / billion / trillion,
    with an optional ``and``.  ``"three hundred and four"`` is ``304``;
    ``"three four"`` is refused, because juxtaposition is not a numeral.
    """
    tokens = [t for t in re.split(r"[\s\-]+", text.strip()) if t and t != "and"]
    if not tokens:
        return None
    total = Fraction(0)
    current = Fraction(0)
    saw_value = False
    used_multiplier: List[Fraction] = []
    pending_unit = False
    for token in tokens:
        if token in _MULTIPLIERS:
            multiplier = _MULTIPLIERS[token]
            if not saw_value:
                current = Fraction(1)
                saw_value = True
            if multiplier >= 1000:
                total += current * multiplier
                current = Fraction(0)
            else:
                current *= multiplier
            if used_multiplier and multiplier >= used_multiplier[-1] >= 1000:
                return None            # "thousand million" is not canonical
            used_multiplier.append(multiplier)
            pending_unit = False
            continue
        if token not in NUMBER_WORDS:
            return None
        value = NUMBER_WORDS[token]
        if pending_unit:
            return None                # two bare units in a row
        if value >= 20 and value % 10 == 0 and value <= 90:
            current += value
        else:
            current += value
            pending_unit = True
        saw_value = True
    if not saw_value:
        return None
    return total + current


_EXPR_TOKEN = re.compile(r"\s*(\d+\.\d+|\d+|[A-Za-z]+|[()+\-*/^])")


def _tokenise_expression(text: str) -> Optional[List[str]]:
    tokens: List[str] = []
    pos = 0
    while pos < len(text):
        match = _EXPR_TOKEN.match(text, pos)
        if not match:
            if text[pos].isspace():
                pos += 1
                continue
            return None
        tokens.append(match.group(1))
        pos = match.end()
    return tokens or None


def _expression_value(text: str) -> Optional[Fraction]:
    """The exact rational an arithmetic expression denotes, or ``None``.

    Grammar: ``expr := term (('+'|'-') term)*``,
    ``term := factor (('*'|'/') factor)*``,
    ``factor := ('-')? atom ('^' factor)?``,
    ``atom := numeral | number-word-phrase | '(' expr ')'``.
    Exponents must be integers, so the value stays rational and exact.
    """
    tokens = _tokenise_expression(text)
    if tokens is None:
        return None
    pos = 0

    def peek() -> Optional[str]:
        return tokens[pos] if pos < len(tokens) else None

    def parse_expr() -> Optional[Fraction]:
        nonlocal pos
        value = parse_term()
        if value is None:
            return None
        while peek() in ("+", "-"):
            op = tokens[pos]
            pos += 1
            rhs = parse_term()
            if rhs is None:
                return None
            value = value + rhs if op == "+" else value - rhs
        return value

    def parse_term() -> Optional[Fraction]:
        nonlocal pos
        value = parse_factor()
        if value is None:
            return None
        while peek() in ("*", "/"):
            op = tokens[pos]
            pos += 1
            rhs = parse_factor()
            if rhs is None:
                return None
            if op == "/":
                if rhs == 0:
                    return None
                value = value / rhs
            else:
                value = value * rhs
        return value

    def parse_factor() -> Optional[Fraction]:
        nonlocal pos
        if peek() == "-":
            pos += 1
            inner = parse_factor()
            return None if inner is None else -inner
        base = parse_atom()
        if base is None:
            return None
        if peek() == "^":
            pos += 1
            exponent = parse_factor()
            if exponent is None or exponent.denominator != 1:
                return None
            if base == 0 and exponent < 0:
                return None
            return base ** int(exponent)
        return base

    def parse_atom() -> Optional[Fraction]:
        nonlocal pos
        token = peek()
        if token is None:
            return None
        if token == "(":
            pos += 1
            inner = parse_expr()
            if inner is None or peek() != ")":
                return None
            pos += 1
            return inner
        if re.fullmatch(r"\d+\.\d+|\d+", token):
            pos += 1
            return Fraction(token)
        if re.fullmatch(r"[A-Za-z]+", token):
            words: List[str] = []
            while (peek() is not None
                   and re.fullmatch(r"[A-Za-z]+", peek() or "")):
                words.append(tokens[pos])
                pos += 1
            return _number_word_value(" ".join(words))
        return None

    value = parse_expr()
    return value if value is not None and pos == len(tokens) else None


# ===========================================================================
# 3.  THE SI DEFINING CONSTANTS
# ===========================================================================

#: The seven constants that *define* the SI since the 2019 revision.  Their
#: values are exact by definition, not measured, which is what makes them
#: admissible as ``quantity`` meanings: the magnitude is a fact about the
#: unit system, stated to the last digit.
SI_DEFINING_CONSTANTS: Dict[str, Tuple[Tuple[int, ...], Fraction, str]] = {
    "speed_of_light": ((1, 0, -1, 0, 0, 0, 0, 0, 0, 0),
                       Fraction(299792458), "m/s, exact by SI definition"),
    "planck_constant": ((2, 1, -1, 0, 0, 0, 0, 0, 0, 0),
                        Fraction(662607015, 10 ** 42),
                        "J s, exact by SI definition"),
    "elementary_charge": ((0, 0, 1, 1, 0, 0, 0, 0, 0, 0),
                          Fraction(1602176634, 10 ** 28),
                          "C, exact by SI definition"),
    "boltzmann_constant": ((2, 1, -2, 0, -1, 0, 0, 0, 0, 0),
                           Fraction(1380649, 10 ** 29),
                           "J/K, exact by SI definition"),
    "avogadro_constant": ((0, 0, 0, 0, 0, -1, 0, 0, 0, 0),
                          Fraction(602214076 * 10 ** 15),
                          "1/mol, exact by SI definition"),
    "caesium_hyperfine_frequency": ((0, 0, -1, 0, 0, 0, 0, 0, 0, 0),
                                    Fraction(9192631770),
                                    "Hz, exact by SI definition"),
    "luminous_efficacy_540thz": ((-2, -1, 3, 0, 0, 0, 1, 0, 1, 0),
                                 Fraction(683),
                                 "lm/W, exact by SI definition"),
}

#: Case-**sensitive** aliases.  ``"c"`` is the speed of light and ``"C"`` is
#: carbon; conflating the two would be precisely the spelling-over-meaning
#: mistake this package exists to remove.
_CONSTANT_ALIASES: Dict[str, str] = {
    "c": "speed_of_light", "light_speed": "speed_of_light",
    "speed of light": "speed_of_light",
    "h": "planck_constant", "planck": "planck_constant",
    "e_charge": "elementary_charge",
    "k_B": "boltzmann_constant", "boltzmann": "boltzmann_constant",
    "N_A": "avogadro_constant", "avogadro": "avogadro_constant",
    "delta_nu_Cs": "caesium_hyperfine_frequency",
    "K_cd": "luminous_efficacy_540thz",
}


# ===========================================================================
# 4.  CHEMISTRY: elements, formulae, named species
# ===========================================================================

#: Named chemical species whose formula is determinate.  Each entry is the
#: formula in the notation the parser accepts; the meaning is the parsed
#: multiset, so ``"water"`` and ``"H2O"`` land on the same carrier.
COMPOUND_NAMES: Dict[str, str] = {
    "water": "H2O", "dihydrogen_monoxide": "H2O", "heavy_water": "H2O",
    "ice": "H2O", "steam": "H2O",
    "carbon_dioxide": "CO2", "carbon_monoxide": "CO",
    "methane": "CH4", "ammonia": "NH3", "ozone": "O3",
    "salt": "NaCl", "table_salt": "NaCl", "halite": "NaCl",
    "quartz": "SiO2", "silica": "SiO2",
    "rust": "Fe2O3", "hematite": "Fe2O3",
    "lime": "CaO", "quicklime": "CaO", "slaked_lime": "Ca(OH)2",
    "baking_soda": "NaHCO3", "washing_soda": "Na2CO3",
    "sulfuric_acid": "H2SO4", "sulphuric_acid": "H2SO4",
    "nitric_acid": "HNO3", "hydrochloric_acid": "HCl",
    "glucose": "C6H12O6", "ethanol": "C2H6O", "benzene": "C6H6",
    "hydrogen_peroxide": "H2O2", "nitrous_oxide": "N2O",
    "laughing_gas": "N2O", "sulfur_dioxide": "SO2",
    "calcium_carbonate": "CaCO3", "chalk": "CaCO3", "limestone": "CaCO3",
    "pyrite": "FeS2", "galena": "PbS", "magnetite": "Fe3O4",
    "hydrogen_gas": "H2", "oxygen_gas": "O2", "nitrogen_gas": "N2",
}

_FORMULA_TOKEN = re.compile(r"([A-Z][a-z]?|\(|\)|\d+)")


@lru_cache(maxsize=1)
def _symbol_to_z() -> Dict[str, int]:
    return {el.symbol: el.z for el in load_element_register()}


@lru_cache(maxsize=1)
def _name_to_z() -> Dict[str, int]:
    return {el.name.lower(): el.z for el in load_element_register()}


def _parse_formula(text: str) -> Optional[Tuple[Tuple[int, int], ...]]:
    """The multiset of ``(Z, count)`` a chemical formula denotes."""
    if not text or not re.fullmatch(r"[A-Za-z0-9()]+", text):
        return None
    if not text[0].isupper() and text[0] != "(":
        return None
    tokens = _FORMULA_TOKEN.findall(text)
    if "".join(tokens) != text:
        return None
    symbols = _symbol_to_z()
    stack: List[Dict[int, int]] = [{}]
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token == "(":
            stack.append({})
            i += 1
            continue
        if token == ")":
            if len(stack) == 1:
                return None
            group = stack.pop()
            i += 1
            count = 1
            if i < len(tokens) and tokens[i].isdigit():
                count = int(tokens[i])
                i += 1
            if count <= 0:
                return None
            for z, n in group.items():
                stack[-1][z] = stack[-1].get(z, 0) + n * count
            continue
        if token.isdigit():
            return None                # a count with nothing to count
        if token not in symbols:
            return None
        z = symbols[token]
        i += 1
        count = 1
        if i < len(tokens) and tokens[i].isdigit():
            count = int(tokens[i])
            i += 1
        if count <= 0:
            return None
        stack[-1][z] = stack[-1].get(z, 0) + count
        continue
    if len(stack) != 1 or not stack[0]:
        return None
    return tuple(sorted(stack[0].items()))


# ===========================================================================
# 5.  PHYSICS: register names, symbols, aliases
# ===========================================================================

@lru_cache(maxsize=1)
def _physics_names() -> Dict[str, Tuple[Tuple[Fraction, ...], str]]:
    """``name -> (EXT10 exponents, witness)`` over register names and aliases.

    Register names are lowercase with underscores, so this index is matched
    case-insensitively.
    """
    index: Dict[str, Tuple[Tuple[Fraction, ...], str]] = {}
    by_name: Dict[str, Tuple[Fraction, ...]] = {}
    for quantity in load_physics_register():
        by_name[quantity.name] = quantity.exps_ext10
        index[quantity.name] = (quantity.exps_ext10,
                                f"physics register: {quantity.name}")
    raw = json.loads(_RELATIONS.read_text(encoding="utf-8"))
    for alias, target in raw.get("aliases", {}).items():
        if target in by_name and alias not in index:
            index[alias] = (by_name[target],
                            f"physics register alias: {alias} -> {target}")
    return index


@lru_cache(maxsize=1)
def _physics_symbols() -> Dict[str, Tuple[Tuple[Fraction, ...], str]]:
    """``symbol -> (EXT10 exponents, witness)``, matched case-sensitively.

    A symbol is admitted only when it names exactly one quantity: an
    overloaded symbol is not a determinate reference.  Case matters -- ``B``
    is a magnetic flux density and ``Ba`` is barium -- so this index is never
    consulted with a case-folded key.
    """
    seen: Dict[str, int] = {}
    for quantity in load_physics_register():
        seen[quantity.symbol] = seen.get(quantity.symbol, 0) + 1
    index: Dict[str, Tuple[Tuple[Fraction, ...], str]] = {}
    for quantity in load_physics_register():
        if seen.get(quantity.symbol) == 1:
            index[quantity.symbol] = (
                quantity.exps_ext10,
                f"physics register symbol: {quantity.symbol} "
                f"= {quantity.name}")
    return index


# ===========================================================================
# 6.  OPERATIONS
# ===========================================================================

#: Operator notations, in every script the runtime accepts.
OPERATION_WORDS: Dict[str, str] = {
    "+": "add", "plus": "add", "add": "add", "sum": "add",
    "addition": "add", "and_then_add": "add",
    "-": "subtract", "minus": "subtract", "subtract": "subtract",
    "difference": "subtract", "less": "subtract",
    "*": "multiply", "x": "multiply", "times": "multiply",
    "multiply": "multiply", "product": "multiply", "\u00d7": "multiply",
    "/": "divide", "divide": "divide", "quotient": "divide",
    "per": "divide", "\u00f7": "divide", "over": "divide",
    "negate": "negate", "negative": "negate", "opposite": "negate",
    "reciprocal": "reciprocal", "inverse": "reciprocal",
    "^": "power", "power": "power", "exponent": "power",
    "raised_to": "power",
    "identity": "identity", "same": "identity", "itself": "identity",
}


# ===========================================================================
# 7.  RESOLUTION
# ===========================================================================

def _normalise(term: str) -> str:
    return " ".join(term.strip().split())


def _resolve_numeral(term: str) -> Optional[Resolution]:
    value = _numeral_value(term)
    if value is None:
        return None
    return Resolution(term, Meaning.number(value), "numeral",
                      f"numeral {term}")


def _resolve_arithmetic(term: str) -> Optional[Resolution]:
    value = _expression_value(term)
    if value is None:
        return None
    return Resolution(term, Meaning.number(value), "arithmetic",
                      f"expression evaluates to {value}")


def _resolve_roman(term: str) -> Optional[Resolution]:
    value = _roman_value(term)
    if value is None:
        return None
    return Resolution(term, Meaning.number(Fraction(value)), "roman",
                      f"roman numeral {term} = {value}")


def _resolve_number_word(term: str) -> Optional[Resolution]:
    value = _number_word_value(term.lower().replace("_", " "))
    if value is None:
        return None
    return Resolution(term, Meaning.number(value), "number_word",
                      f"cardinal phrase {term!r} = {value}")


def _resolve_si_constant(term: str) -> Optional[Resolution]:
    if term in _CONSTANT_ALIASES:
        key = _CONSTANT_ALIASES[term]
    else:
        key = term.lower().replace(" ", "_").replace("-", "_")
        key = _CONSTANT_ALIASES.get(key, key) if len(key) > 2 else key
    if key not in SI_DEFINING_CONSTANTS:
        return None
    exponents, magnitude, note = SI_DEFINING_CONSTANTS[key]
    return Resolution(term, Meaning.quantity(exponents, magnitude),
                      "si_constant", f"{key}: {note}")


def _resolve_element(term: str) -> Optional[Resolution]:
    symbols = _symbol_to_z()
    if term in symbols:
        return Resolution(term, Meaning.element(symbols[term]), "element",
                          f"element symbol {term} = Z {symbols[term]}")
    names = _name_to_z()
    key = term.lower()
    if key in names:
        return Resolution(term, Meaning.element(names[key]), "element",
                          f"element name {key} = Z {names[key]}")
    return None


def _resolve_formula(term: str) -> Optional[Resolution]:
    parts = _parse_formula(term)
    if parts is None:
        return None
    if len(parts) == 1 and parts[0][1] == 1:
        return Resolution(term, Meaning.element(parts[0][0]), "element",
                          f"formula {term} is one atom of Z {parts[0][0]}")
    try:
        meaning = Meaning.compound(parts)
    except ValueError as exc:
        return _refused(term, str(exc))
    return Resolution(term, meaning, "formula", f"formula {term}")


def _resolve_compound_name(term: str) -> Optional[Resolution]:
    key = term.lower().replace(" ", "_").replace("-", "_")
    formula = COMPOUND_NAMES.get(key)
    if formula is None:
        return None
    parts = _parse_formula(formula)
    if parts is None:                                # pragma: no cover
        return _refused(term, f"named species {key} has an unparsable "
                              f"formula {formula!r}")
    meaning = (Meaning.element(parts[0][0])
               if len(parts) == 1 and parts[0][1] == 1
               else Meaning.compound(parts))
    return Resolution(term, meaning, "compound_name",
                      f"named species {key} = {formula}")


def _resolve_physics(term: str) -> Optional[Resolution]:
    symbols = _physics_symbols()
    if term in symbols:
        exponents, witness = symbols[term]
        return Resolution(term, Meaning.dimension(exponents), "physics",
                          witness)
    names = _physics_names()
    key = term.lower().replace(" ", "_").replace("-", "_")
    if key in names:
        exponents, witness = names[key]
        return Resolution(term, Meaning.dimension(exponents), "physics",
                          witness)
    return None


def _resolve_operation(term: str) -> Optional[Resolution]:
    key = term.lower().replace(" ", "_").replace("-", "_")
    name = OPERATION_WORDS.get(key)
    if name is None:
        return None
    return Resolution(term, Meaning.op(name), "operation",
                      f"operator notation {term!r} = {name}")


#: The resolvers, in the order :func:`resolve` tries them.
_RESOLVERS = (
    ("numeral", _resolve_numeral),
    ("roman", _resolve_roman),
    ("number_word", _resolve_number_word),
    ("arithmetic", _resolve_arithmetic),
    ("si_constant", _resolve_si_constant),
    ("element", _resolve_element),
    ("formula", _resolve_formula),
    ("compound_name", _resolve_compound_name),
    ("physics", _resolve_physics),
    ("operation", _resolve_operation),
)


def senses_of(term: str) -> Tuple[Resolution, ...]:
    """Every resolver's answer for a term, in resolver order.

    More than one grounded answer with *different* meanings means the term is
    ambiguous; :func:`resolve` refuses it and says so.
    """
    term = _normalise(term)
    out: List[Resolution] = []
    for _, resolver in _RESOLVERS:
        answer = resolver(term)
        if answer is not None and answer.grounded:
            out.append(answer)
    return tuple(out)


def resolve(term: str) -> Resolution:
    """The meaning a term denotes, or a refusal with its reason.

    Deterministic: a pure function of the frozen registers and the term.
    """
    original = term
    term = _normalise(term)
    if not term:
        return _refused(original, "the empty term denotes nothing")
    answers = senses_of(term)
    if not answers:
        return _refused(
            original,
            "no determinate referent: the term is not a numeral, a number "
            "word, a Roman numeral, an arithmetic expression, an SI defining "
            "constant, an element, a chemical formula or named species, a "
            "register quantity or an operator")
    distinct = {answer.meaning for answer in answers}
    if len(distinct) == 1:
        return answers[0]
    finest = _finest(distinct)
    if finest is not None:
        for answer in answers:
            if answer.meaning == finest:
                coarser = ", ".join(sorted(m.describe() for m in distinct
                                           if m != finest))
                return Resolution(
                    answer.term, answer.meaning, answer.sense, answer.witness,
                    reason=(f"read at the finer layer; {coarser} is its "
                            f"projection, not a rival referent"))
    senses = ", ".join(f"{a.sense}={a.meaning.describe()}"  # type: ignore
                       for a in answers)
    return _refused(original,
                    f"ambiguous: {len(distinct)} determinate referents "
                    f"({senses}) -- the term is not by itself a reference")


def _projects_to(fine: Meaning, coarse: Meaning) -> bool:
    """Whether ``coarse`` is a strictly coarser reading of ``fine``.

    The one case that arises: a ``quantity`` is a ``dimension`` together with
    a magnitude, so the dimension is what the lower layer sees of it.  Two
    readings related this way are not two referents -- they are one referent
    at two resolutions, and the resolver keeps the finer one rather than
    refusing the term.
    """
    return (fine.kind == "quantity" and coarse.kind == "dimension"
            and fine.exponents == coarse.exponents)


def _finest(meanings: Iterable[Meaning]) -> Optional[Meaning]:
    """The unique meaning every other one is a projection of, if there is one."""
    candidates = list(meanings)
    winners = [m for m in candidates
               if all(other == m or _projects_to(m, other)
                      for other in candidates)]
    return winners[0] if len(winners) == 1 else None


def resolve_many(terms: Iterable[str]) -> Tuple[Resolution, ...]:
    """:func:`resolve` over an iterable, in the order given."""
    return tuple(resolve(term) for term in terms)


def is_grounded(term: str) -> bool:
    """Whether a term denotes something determinate."""
    return resolve(term).grounded


def meaning_of(term: str) -> Meaning:
    """The meaning of a term, raising :class:`KeyError` if it has none."""
    answer = resolve(term)
    if answer.meaning is None:
        raise KeyError(f"reference: {term!r} has no determinate referent "
                       f"({answer.reason})")
    return answer.meaning


# ===========================================================================
# 8.  THE REFERENCE VOCABULARY, AND ITS AUDIT
# ===========================================================================

@lru_cache(maxsize=1)
def reference_terms() -> Tuple[str, ...]:
    """Every term the registers name explicitly, sorted.

    The unbounded resolvers -- numerals, Roman numerals, arithmetic, formulae
    -- accept infinitely many terms and are not enumerated here; this is the
    finite, register-backed vocabulary.
    """
    terms = set(_physics_names()) | set(_physics_symbols())
    terms |= set(NUMBER_WORDS) | set(_MULTIPLIERS)
    terms |= set(SI_DEFINING_CONSTANTS) | set(_CONSTANT_ALIASES)
    terms |= set(COMPOUND_NAMES)
    terms |= set(_symbol_to_z()) | set(_name_to_z())
    terms |= set(OPERATION_WORDS)
    return tuple(sorted(terms))


@lru_cache(maxsize=1)
def ambiguity_report() -> Dict[str, object]:
    """Every named term that two resolvers answer differently.

    An ambiguous term is refused rather than resolved by resolver order, so
    this report is the complete list of what resolver order is *not* deciding.
    """
    ambiguous: List[Dict[str, object]] = []
    for term in reference_terms():
        answers = senses_of(term)
        distinct = {answer.meaning for answer in answers}
        if len(distinct) > 1:
            ambiguous.append({
                "term": term,
                "senses": [{"sense": a.sense,
                            "meaning": a.meaning.describe(),  # type: ignore
                            "witness": a.witness} for a in answers],
            })
    return {
        "named_terms": len(reference_terms()),
        "ambiguous_terms": len(ambiguous),
        "ambiguous": ambiguous,
    }


def coverage_report(terms: Sequence[str]) -> Dict[str, object]:
    """How many of a list of terms denote something determinate.

    The counts are by sense, and the refusals are counted rather than hidden,
    so a caller can see exactly what a corpus is made of.
    """
    by_sense: Dict[str, int] = {}
    refused: List[str] = []
    grounded: List[str] = []
    for term in terms:
        answer = resolve(term)
        if answer.grounded:
            grounded.append(term)
            by_sense[answer.sense] = by_sense.get(answer.sense, 0) + 1
        else:
            refused.append(term)
    return {
        "terms": len(terms),
        "grounded": len(grounded),
        "refused": len(refused),
        "by_sense": dict(sorted(by_sense.items())),
        "grounded_terms": tuple(sorted(set(grounded))),
        "refused_sample": tuple(sorted(set(refused))[:40]),
    }
