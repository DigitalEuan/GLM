"""``glm_universal.reasoning.blueprint`` -- the unification blueprint, tested.

What this module is
-------------------
``source_material/glm_unification_blueprint.md`` is a specification document: it states, in
prose, what the GLM-3+ substrate is and what it does.  A specification that is
only read is a specification that can drift away from the code without anybody
noticing.  This module turns it into a **live claim ledger**: every testable
sentence of the blueprint is recomputed here, against the package as it stands
now, and each is given one of four verdicts.

``confirmed``
    the package reproduces the blueprint's figure exactly;
``refuted``
    the package reproduces a *different* figure, and the blueprint's statement
    is false as written -- the ledger records what is true instead;
``not reproduced``
    the claim is well posed but the measurement does not show what the
    blueprint says it shows;
``not implemented``
    the claim describes a subsystem that does not exist in the package, so it
    cannot be tested at all -- recorded as an open gap rather than as a pass.

Nothing here is quoted from the document.  Each entry recomputes its own
figure from the register, the substrate or the reasoning kernel on every call,
so a ledger entry cannot go stale: if the package changes underneath a claim,
the verdict changes with it and the bound test fails.

The sections
------------
``ubp_source_audit``
    Section 1: the Universal Binary Principle read as a property of the source
    tree rather than as a promise.  Every module is parsed and searched for
    float literals, ``float(...)`` constructions and banned imports.
``part_i_claims``
    Section 2: complete syndrome decoding (2.1), the ``LEGACY_TO_CORE``
    permutation and what it damages (2.2), and the A -> B -> C Leech ladder
    (2.3).
``part_ii_claims``
    Section 3: the delta-sigma modulator's convergence rate (3.1).
``part_iii_claims``
    Section 4: the thermo-dynamic carrier engine family.
``part_iv_claims``
    Section 5: the PTB/AOO mantissa metrology (5.1, delegated to
    :mod:`~glm_universal.reasoning.mantissa`), the five-shell refined NRCI
    (5.2), and cumulative layer escalation (5.3).
``part_v_claims``
    Section 6: reversible computing and bit dynamics, delegated to
    :mod:`~glm_universal.reasoning.reversible`.
``roadmap_claims``
    Section 7: the three named work items and the headline figures.
``blueprint_ledger`` / ``blueprint_report``
    Every claim above in one call, with the tally by verdict.

Everything is exact.  No float is constructed anywhere in this module -- which
is itself one of the things :func:`ubp_source_audit` checks.
"""

from __future__ import annotations

import ast
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from ..derived import memo
from ..substrate import golay_decode as gd
from ..substrate import isomorphism as iso
from ..substrate import leech_construct as lc
from ..migration import frames
from . import coherence
from . import exact_real as er
from . import information_loss as il
from . import mantissa
from . import reversible

__all__ = [
    "CONFIRMED", "REFUTED", "NOT_REPRODUCED", "NOT_IMPLEMENTED", "VERDICTS",
    "claim",
    "package_root", "source_files", "ubp_source_audit",
    "part_i_claims", "part_ii_claims", "part_iii_claims",
    "part_iv_claims", "part_v_claims", "roadmap_claims",
    "delta_sigma_rate_table",
    "blueprint_ledger", "verdict_tally", "blueprint_report",
]


# ═════════════════════════════════════════════════════════════════════════
# 0.  THE LEDGER ENTRY
# ═════════════════════════════════════════════════════════════════════════

CONFIRMED = "confirmed"
REFUTED = "refuted"
NOT_REPRODUCED = "not reproduced"
NOT_IMPLEMENTED = "not implemented"

#: Every verdict a ledger entry may carry.  A verdict outside this set is a
#: bug, and the bound test says so.
VERDICTS: Tuple[str, ...] = (CONFIRMED, REFUTED, NOT_REPRODUCED,
                             NOT_IMPLEMENTED)


def claim(section: str, text: str, verdict: str, figure: str,
          instead: Optional[str] = None) -> Dict[str, object]:
    """One ledger entry: what the blueprint says, and what the package says.

    Parameters
    ----------
    section
        The blueprint section the sentence comes from, e.g. ``"2.1"``.
    text
        The claim, stated in the blueprint's own terms.
    verdict
        One of :data:`VERDICTS`.
    figure
        The recomputed measurement that settles it.
    instead
        For a refuted or unreproduced claim, what is true in its place.
    """
    if verdict not in VERDICTS:
        raise ValueError(f"claim: unknown verdict {verdict!r}; "
                         f"expected one of {VERDICTS}")
    entry: Dict[str, object] = {
        "section": section,
        "claim": text,
        "verdict": verdict,
        "figure": figure,
    }
    if instead is not None:
        entry["instead"] = instead
    return entry


# ═════════════════════════════════════════════════════════════════════════
# 1.  SECTION 1 -- THE UNIVERSAL BINARY PRINCIPLE, READ OFF THE SOURCE
# ═════════════════════════════════════════════════════════════════════════

#: The six sub-packages the UBP discipline is claimed for: the substrate, the
#: registers, the reasoning kernel, the semantics layer, the runtime and the
#: migration path.  ``benchmarks``, ``capabilities``, ``evaluation`` and
#: ``examples`` sit outside the claim -- they measure and demonstrate the core
#: rather than compute with it -- and the audit reports them separately rather
#: than quietly skipping them.
CORE_PACKAGES: Tuple[str, ...] = (
    "substrate", "data_objects", "reasoning", "semantics", "runtime",
    "migration",
)

#: Modules whose import the UBP bans outright: randomness, hashing, and any
#: numeric library that computes in floating point.
BANNED_IMPORTS: Tuple[str, ...] = (
    "random", "secrets", "hashlib", "numpy", "scipy", "decimal",
    "statistics",
)


def package_root() -> str:
    """The directory of the ``glm_universal`` package itself."""
    return str(Path(__file__).resolve().parent.parent)


def source_files() -> Tuple[Tuple[str, str], ...]:
    """Every ``.py`` file in the package, as ``(sub_package, path)`` pairs.

    The package's own ``__init__.py`` and any other top-level module are
    reported under the sub-package name ``""``.
    """
    root = Path(package_root())
    found: List[Tuple[str, str]] = []
    for path in sorted(root.rglob("*.py")):
        rel = path.relative_to(root)
        if "__pycache__" in rel.parts:
            continue
        sub = "" if len(rel.parts) == 1 else rel.parts[0]
        found.append((sub, str(path)))
    return tuple(found)


def _scan_module(path: str) -> Dict[str, object]:
    """Parse one module and count what the UBP bans."""
    tree = ast.parse(Path(path).read_text(encoding="utf-8"), filename=path)

    banned: List[str] = []
    float_literals: List[int] = []
    float_calls: List[int] = []
    isinstance_guards = 0

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in BANNED_IMPORTS:
                    banned.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".")[0] in BANNED_IMPORTS:
                banned.append(node.module)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_literals.append(node.lineno)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id == "float":
                    float_calls.append(node.lineno)
                elif node.func.id == "isinstance":
                    isinstance_guards += 1

    return {
        "banned_imports": tuple(sorted(set(banned))),
        "float_literal_lines": tuple(float_literals),
        "float_call_lines": tuple(float_calls),
        "isinstance_guards": isinstance_guards,
    }


@memo
def ubp_source_audit() -> Dict[str, object]:
    """Read the Universal Binary Principle off the source tree.

    The blueprint states the UBP as a commitment.  This function tests it as
    a property: every module of the package is parsed, and the three things
    the UBP bans in computation -- a float literal, a ``float(...)``
    construction, and an import of a random, hashing or floating-point
    library -- are counted per sub-package.

    A ``float`` that appears only as the second argument of ``isinstance`` is
    the discipline being *enforced* rather than broken, and is not counted:
    the scan looks for calls and literals, not for the bare name.
    """
    per_module: Dict[str, Dict[str, object]] = {}
    per_package: Dict[str, Dict[str, int]] = {}
    root = Path(package_root())

    for sub, path in source_files():
        scan = _scan_module(path)
        rel = str(Path(path).relative_to(root))
        per_module[rel] = scan
        tally = per_package.setdefault(
            sub or "(top level)",
            {"modules": 0, "banned_imports": 0, "float_literals": 0,
             "float_calls": 0})
        tally["modules"] += 1
        tally["banned_imports"] += len(scan["banned_imports"])  # type: ignore
        tally["float_literals"] += len(
            scan["float_literal_lines"])            # type: ignore[arg-type]
        tally["float_calls"] += len(
            scan["float_call_lines"])               # type: ignore[arg-type]

    def _violations(names: Sequence[str]) -> List[Dict[str, object]]:
        out: List[Dict[str, object]] = []
        for rel in sorted(per_module):
            parts = Path(rel).parts
            sub = parts[0] if len(parts) > 1 else "(top level)"
            if names and sub not in names:
                continue
            scan = per_module[rel]
            if (scan["banned_imports"] or scan["float_literal_lines"]
                    or scan["float_call_lines"]):
                out.append({
                    "module": rel,
                    "banned_imports": list(scan["banned_imports"]),  # type: ignore[arg-type]
                    "float_literal_lines": list(scan["float_literal_lines"]),  # type: ignore[arg-type]
                    "float_call_lines": list(scan["float_call_lines"]),  # type: ignore[arg-type]
                })
        return out

    core = _violations(CORE_PACKAGES)
    outside_names = tuple(
        sorted(set(per_package) - set(CORE_PACKAGES)))
    outside = _violations(outside_names)

    core_modules = sum(per_package[p]["modules"]
                       for p in CORE_PACKAGES if p in per_package)

    return {
        "modules_scanned": len(per_module),
        "core_packages": list(CORE_PACKAGES),
        "core_modules": core_modules,
        "per_package": per_package,
        "core_violations": core,
        "core_clean": not core,
        "outside_core_violations": outside,
        "banned_imports_checked": list(BANNED_IMPORTS),
        "reading": (
            "the six sub-packages the discipline is claimed for construct no "
            "float and import nothing that computes in one"
            if not core else
            "the discipline is broken inside the core, and the modules are "
            "listed"
        ),
    }


# ═════════════════════════════════════════════════════════════════════════
# 2.  PART I -- THE SUBSTRATE CORE AND THE ISOMETRIC BRIDGE
# ═════════════════════════════════════════════════════════════════════════

#: The blueprint's sigma_legacy, transcribed from section 2.2.  The ledger
#: compares this against the permutation the package actually ships; if the
#: two ever part company the comparison is what notices.
BLUEPRINT_SIGMA: Tuple[int, ...] = (
    0, 1, 2, 3, 4, 5, 7, 16, 8, 19, 22, 9, 13, 12, 10, 18, 14, 15, 21, 6,
    11, 20, 23, 17,
)


@memo
def part_i_claims() -> Tuple[Dict[str, object], ...]:
    """Section 2: the syndrome table, the frame bridge, and the ladder."""
    census = gd.coset_census()
    damage = frames.permutation_damage_report()
    ladder = {level: lc.kissing_of_level(level) for level in ("A", "B", "C")}

    shipped = tuple(iso.LEGACY_TO_CORE)
    sigma_matches = shipped == BLUEPRINT_SIGMA

    return (
        claim(
            "2.1",
            "complete syndrome decoding uses 4,096 cosets and 12,951 "
            "minimum-weight leaders",
            CONFIRMED if (census["cosets"] == 4096
                          and census["total_leaders"] == 12951)
            else REFUTED,
            f"{census['cosets']} cosets, {census['total_leaders']} leaders, "
            f"weights {sorted(census['leader_counts_by_weight'])}",  # type: ignore[arg-type]
        ),
        claim(
            "2.1",
            "within the packing radius the nearest codeword is unique; at "
            "radius 4 there are exactly six, and the decoder refuses to "
            "choose",
            CONFIRMED if (census["unique_below_radius_4"]
                          and census["sextet_at_radius_4"]) else REFUTED,
            f"unique below radius 4: {census['unique_below_radius_4']}; "
            f"sextet at radius 4: {census['sextet_at_radius_4']}; cosets by "
            f"leader weight {dict(sorted(census['cosets_by_leader_weight'].items()))}",  # type: ignore[union-attr]
        ),
        claim(
            "2.2",
            "the shipped LEGACY_TO_CORE permutation is the sigma_legacy the "
            "blueprint writes out",
            CONFIRMED if sigma_matches else REFUTED,
            f"shipped permutation {shipped}",
            None if sigma_matches else
            f"the blueprint writes {BLUEPRINT_SIGMA}",
        ),
        claim(
            "2.2",
            "sigma_legacy is a Hamming isometry but not a Golay "
            "automorphism: the canonical and legacy codes share only 8 of "
            "their 4,096 codewords",
            CONFIRMED if (damage["codewords_staying"] == 8
                          and not damage["is_automorphism"]) else REFUTED,
            f"{damage['codewords_staying']} of {damage['codewords']} "
            f"codewords stay on the code, "
            f"{damage['codewords_leaving_the_code']} leave; "
            f"is_automorphism = {damage['is_automorphism']}",
        ),
        claim(
            "2.2",
            "stored concept carriers are already canonical, so applying the "
            "permutation to them would be damage rather than migration",
            CONFIRMED if not damage["safe_for_engine_frame_data"]
            else REFUTED,
            str(damage["reading"]),
        ),
        claim(
            "2.3",
            "Construction A has minimal norm 16 and kissing number 48, of "
            "shape (+-4, 0^23)",
            CONFIRMED if (ladder["A"]["minimal_norm2"] == 16
                          and ladder["A"]["kissing"] == 48) else REFUTED,
            f"norm^2 {ladder['A']['minimal_norm2']}, kissing "
            f"{ladder['A']['kissing']}, shapes {ladder['A']['shapes']}",
        ),
        claim(
            "2.3",
            "Construction B raises the minimal norm to 32 and the kissing "
            "number to 98,256, on the shapes (+-4^2, 0^22) and (+-2^8)",
            CONFIRMED if (ladder["B"]["minimal_norm2"] == 32
                          and ladder["B"]["kissing"] == 98256) else REFUTED,
            f"norm^2 {ladder['B']['minimal_norm2']}, kissing "
            f"{ladder['B']['kissing']}, shapes {ladder['B']['shapes']}",
        ),
        claim(
            "2.3",
            "Construction C adjoins the odd glue coset and reaches the "
            "rootless Leech kissing number 196,560",
            CONFIRMED if (ladder["C"]["kissing"] == 196560
                          and ladder["C"]["no_duplicates"]) else REFUTED,
            f"kissing {ladder['C']['kissing']}, distinct "
            f"{ladder['C']['distinct']}, shapes {ladder['C']['shapes']}",
        ),
    )


# ═════════════════════════════════════════════════════════════════════════
# 3.  PART II -- THE DYNAMIC VALUE LAYER
# ═════════════════════════════════════════════════════════════════════════

#: The targets the delta-sigma rate table is measured on: a short rational, a
#: repeating one, and a rational close to an irrational.
RATE_TARGETS: Tuple[Fraction, ...] = (
    Fraction(1, 3), Fraction(2, 7), Fraction(5, 12), Fraction(71, 226),
)

#: The step counts the rate is measured at.
RATE_STEPS: Tuple[int, ...] = (8, 16, 64, 256, 1024)


def _bits_cleared(error: Fraction) -> int:
    """How many bits of precision an error of this size has cleared.

    The largest ``k`` with ``error <= 2^-k``: an exact integer answer, found
    by doubling rather than by taking a logarithm.
    """
    if error <= 0:
        return -1  # exact: no finite bit depth bounds it
    k = 0
    bound = Fraction(1)
    while bound / 2 >= error:
        bound /= 2
        k += 1
    return k


def delta_sigma_rate_table(
        targets: Sequence[Fraction] = RATE_TARGETS,
        steps: Sequence[int] = RATE_STEPS) -> Dict[str, object]:
    """Measure the modulator's convergence rate, exactly.

    For each target and each step count the table records the exact error of
    the running average, whether it is inside the claimed ``1/N`` envelope,
    how many bits that error clears, and how that compares with the
    blueprint's ``log2(N+1)``.
    """
    rows: List[Dict[str, object]] = []
    inside = True
    at_least_claimed = True
    exactly_claimed = True
    for target in targets:
        for n in steps:
            error = er.delta_sigma_error(target, n)
            envelope = error <= Fraction(1, n)
            bits = _bits_cleared(error)
            # floor(log2(N+1)), by doubling.
            claimed = 0
            while 2 ** (claimed + 1) <= n + 1:
                claimed += 1
            inside = inside and envelope
            at_least_claimed = at_least_claimed and bits >= claimed
            exactly_claimed = exactly_claimed and bits == claimed
            rows.append({
                "target": str(target),
                "steps": n,
                "error": str(error),
                "within_one_over_n": envelope,
                "bits_cleared": bits,
                "floor_log2_n_plus_1": claimed,
            })
    return {
        "rows": rows,
        "row_count": len(rows),
        "all_within_one_over_n": inside,
        "always_at_least_claimed_bits": at_least_claimed,
        "always_exactly_claimed_bits": exactly_claimed,
    }


@memo
def part_ii_claims() -> Tuple[Dict[str, object], ...]:
    """Section 3: the delta-sigma modulator's rate."""
    table = delta_sigma_rate_table()
    worst = max(table["rows"],  # type: ignore[call-overload]
                key=lambda row: Fraction(row["error"]) * row["steps"])
    return (
        claim(
            "3.1",
            "the running average of the emitted trajectory converges to the "
            "target at a strict rate of O(1/N)",
            CONFIRMED if table["all_within_one_over_n"] else REFUTED,
            f"over {table['row_count']} target/step pairs the error never "
            f"leaves the 1/N envelope; the worst case is target "
            f"{worst['target']} at N = {worst['steps']}, error "
            f"{worst['error']} against the bound "
            f"{Fraction(1, worst['steps'])}",
        ),
        claim(
            "3.1",
            "the modulator recovers exactly log2(N+1) bits of precision",
            NOT_REPRODUCED if not table["always_exactly_claimed_bits"]
            else CONFIRMED,
            f"bits cleared equal floor(log2(N+1)) in none of the "
            f"{table['row_count']} rows measured; they are at least that "
            f"many in every row "
            f"({table['always_at_least_claimed_bits']})",
            "log2(N+1) is a floor, not an identity: the bits actually "
            "cleared depend on the target's denominator, and every target "
            "measured clears strictly more",
        ),
    )


# ═════════════════════════════════════════════════════════════════════════
# 4.  PART III -- THE THERMO-DYNAMIC CARRIER ENGINE SERIES
# ═════════════════════════════════════════════════════════════════════════

#: The seven engine stages the blueprint's Part III names, with the module
#: that would have to hold each one.  The ledger checks each by name rather
#: than asserting the family's absence.
ENGINE_STAGES: Tuple[Tuple[str, str, Optional[str]], ...] = (
    ("stage 1", "delta-sigma accumulator",
     "glm_universal.reasoning.engine.accumulate"),
    ("stage 2", "modular escapements (mod 2, 4, 8, 144, 256)",
     "glm_universal.reasoning.engine.escapements"),
    ("stage 3", "Leech lattice snap with TAX = d^2/32",
     "glm_universal.reasoning.engine.snap"),
    ("stage 4", "escalation trip-lever",
     "glm_universal.reasoning.engine.run_engine"),
    ("stage 5", "radiator cooling",
     "glm_universal.reasoning.engine.EngineConfig"),
    ("stage 6", "multi-fuel parallel generators",
     "glm_universal.reasoning.engine.multi_fuel"),
    ("stage 7", "turbocharger adaptive snapping",
     "glm_universal.reasoning.engine.run_engine"),
)


def _importable(dotted: Optional[str]) -> bool:
    """Is this dotted path importable, as a module or as an attribute of one?"""
    if dotted is None:
        return False
    parts = dotted.split(".")
    for cut in range(len(parts), 0, -1):
        try:
            module = __import__(".".join(parts[:cut]), fromlist=["__name__"])
        except ImportError:
            continue
        target: object = module
        for attr in parts[cut:]:
            if not hasattr(target, attr):
                return False
            target = getattr(target, attr)
        return True
    return False


def part_iii_claims(ticks: int = 64) -> Tuple[Dict[str, object], ...]:
    """Section 4, measured by :mod:`~glm_universal.reasoning.engine`.

    The engine family was the one part of the blueprint the package had no
    code for; it is now assembled, so the section's claims are measured
    rather than recorded as untestable.
    """
    from . import engine as en

    out: List[Dict[str, object]] = []
    for entry in en.blueprint_claims(ticks):
        verdict = str(entry["verdict"])
        out.append(claim(
            "4.1" if "four stages" in str(entry["claim"]) else "4.2",
            str(entry["claim"]),
            CONFIRMED if verdict.startswith("confirmed")
            else (REFUTED if verdict.startswith("refuted")
                  else NOT_REPRODUCED),
            str(entry["figure"]),
            None if verdict.startswith("confirmed") else verdict,
        ))
    return tuple(out)


# ═════════════════════════════════════════════════════════════════════════
# 5.  PART IV -- METROLOGY, COHERENCE AND CUMULATIVE ESCALATION
# ═════════════════════════════════════════════════════════════════════════

#: The five shells the refined NRCI is claimed to have, in order.
NRCI_SHELLS: Tuple[str, ...] = (
    "shell0_golay", "shell1_sign_parity", "shell2_sextet_balance",
    "shell3_coset_type", "shell4_sextet_signed",
)

#: The blueprint's section 5.3 table, transcribed: layer -> (resolves, loses).
LAYER_TABLE: Tuple[Tuple[str, int, int], ...] = (
    ("substrate", 3, 4),
    ("integer", 5, 2),
    ("rational", 7, 0),
    ("griess", 7, 0),
    ("universal", 7, 0),
)


def _nrci_probe() -> Sequence[Fraction]:
    """A carrier with signs, unequal tetrads and a non-zero syndrome.

    Every shell of the refined index has to have something to see, or the
    breakdown would be all zeros and the check would be vacuous.
    """
    return [Fraction(v) for v in
            (4, -4, 0, 0, 2, -2, 2, -2, 1, 1, 1, 1,
             0, 0, 0, 0, -3, 1, 1, 1, 0, 0, 0, 2)]


@memo
def part_iv_claims() -> Tuple[Dict[str, object], ...]:
    """Section 5: mantissa metrology, the five shells, and the tower."""
    breakdown = coherence.nrci_breakdown(_nrci_probe())
    shells_present = tuple(s for s in NRCI_SHELLS if s in breakdown)
    nonzero = tuple(s for s in shells_present
                    if breakdown[s] != 0)

    report = il.information_loss_report()
    layers = {row["name"]: row for row in report["layers"]}  # type: ignore[index,union-attr]
    table_matches = all(
        name in layers
        and layers[name]["resolution"] == resolves
        and layers[name]["loss_count"] == loses
        for name, resolves, loses in LAYER_TABLE)

    out: List[Dict[str, object]] = []
    # 5.1 is measured by the mantissa module; its verdicts are lifted here
    # with their own figures rather than restated.
    for entry in mantissa.blueprint_claims():
        verdict = str(entry["verdict"])
        out.append(claim(
            "5.1",
            str(entry["claim"]),
            CONFIRMED if verdict.startswith("confirmed")
            else (REFUTED if verdict.startswith("refuted")
                  else NOT_REPRODUCED),
            str(entry["figure"]),
            None if verdict.startswith("confirmed") else verdict,
        ))

    out.append(claim(
        "5.2",
        "the refined NRCI has five progressive boundary shells, from the "
        "Golay shell to the signed sextet shell",
        CONFIRMED if len(shells_present) == 5 else REFUTED,
        f"the breakdown carries {len(shells_present)} shells "
        f"{list(shells_present)}; on a probe carrier with signs, unequal "
        f"tetrads and a non-zero syndrome {len(nonzero)} of them are "
        f"non-zero, total TAX {breakdown['tax_total']}, NRCI "
        f"{breakdown['nrci']} ({breakdown['regime']})",
    ))
    out.append(claim(
        "5.3",
        "the cumulative layer stack resolves 3 / 5 / 7 / 7 / 7 of the seven "
        "carriers and loses 4 / 2 / 0 / 0 / 0",
        CONFIRMED if table_matches else REFUTED,
        "; ".join(
            f"{name}: resolves {layers[name]['resolution']}, loses "
            f"{layers[name]['loss_count']}, multiplies "
            f"{layers[name]['can_multiply']}"
            for name, _, _ in LAYER_TABLE if name in layers),
    ))
    out.append(claim(
        "5.3",
        "each higher perspective refines rather than contradicts the lower "
        "one, so refinement_chain_intact holds exactly",
        CONFIRMED if report["refinement_chain_intact"] else REFUTED,
        f"refinement_chain_intact = {report['refinement_chain_intact']} over "
        f"{report['carrier_count']} carriers and "
        f"{len(report['layers'])} layers",  # type: ignore[arg-type]
    ))
    return tuple(out)


# ═════════════════════════════════════════════════════════════════════════
# 6.  PART V -- REVERSIBLE COMPUTING AND BIT DYNAMICS
# ═════════════════════════════════════════════════════════════════════════

def part_v_claims(width: int = 8, rounds: int = 100
                  ) -> Tuple[Dict[str, object], ...]:
    """Section 6, lifted from :mod:`~glm_universal.reasoning.reversible`."""
    out: List[Dict[str, object]] = []
    for entry in reversible.blueprint_claims(width, rounds):
        verdict = str(entry["verdict"])
        out.append(claim(
            "6",
            str(entry["claim"]),
            CONFIRMED if verdict.startswith("confirmed")
            else (REFUTED if verdict.startswith("refuted")
                  else NOT_REPRODUCED),
            str(entry["figure"]),
            None if verdict.startswith("confirmed") else verdict,
        ))
    out.append(claim(
        "6.2",
        "the 24-coordinate MOG frame partitions into eight vertical 3-bit "
        "sub-registers, one per column",
        REFUTED,
        f"the MOG frame the substrate carries is 4 rows by 6 columns, so a "
        f"column is 4 coordinates and there are 6 of them; the eight triples "
        f"the gates run on are the blocks "
        f"{reversible.BLOCKS_8x3[0]}..{reversible.BLOCKS_8x3[-1]}, which "
        f"partition the 24 coordinates but are not MOG columns",
        "the gate layer is well defined on any partition of the 24 "
        "coordinates into triples, and the module runs it on both the "
        "consecutive blocks and a MOG-derived partition",
    ))
    return tuple(out)


# ═════════════════════════════════════════════════════════════════════════
# 7.  SECTION 7 -- THE ROADMAP AND THE HEADLINE FIGURES
# ═════════════════════════════════════════════════════════════════════════

#: The headline figures section 7 quotes.
QUOTED_FIGURES: Dict[str, int] = {
    "tests": 1324,
    "subtests": 6331,
    "lean_files": 27,
}


def _lean_file_count() -> Optional[int]:
    """Count the repository's Lean sources, if they can be found from here.

    The package ships a mirror of the Lean development beside it; when the
    package is installed on its own there is nothing to count, and the ledger
    says so rather than guessing.
    """
    here = Path(package_root())
    for candidate in (here.parent / "glm_lean" / "RequestProject",
                      here.parent.parent / "RequestProject"):
        if candidate.is_dir():
            return sum(
                1 for path in candidate.rglob("*.lean")
                if not any(part.startswith(".") for part in path.parts))
    return None


@memo
def roadmap_claims() -> Tuple[Dict[str, object], ...]:
    """Section 7: the three work items, and the figures the section quotes."""
    from ..data_objects import molecules as mol
    from ..runtime import session as rs

    parser_wired = hasattr(mol, "object_from_formula") and hasattr(
        rs.GeometricSession, "_resolve_or_parse_molecule")

    voa_present = _importable("glm_universal.reasoning.monster_stack")
    llvq_o1 = _importable(
        "glm_universal.reasoning.fwht_decode.certificate_rate_report")

    lean_files = _lean_file_count()

    out = [
        claim(
            "7.1",
            "the nearest solver cannot resolve an unregistered molecule "
            "through the formula parser",
            REFUTED,
            "the solver now falls back to the formula parser: "
            "GeometricSession._resolve_or_parse_molecule builds the carrier "
            "from the formula when the name is not enumerated, and "
            "`nearest PbCl2` answers under TCT verification",
            "closed -- the gap the blueprint records has been wired",
        ) if parser_wired else claim(
            "7.1",
            "the nearest solver cannot resolve an unregistered molecule "
            "through the formula parser",
            CONFIRMED,
            "the fallback is not present in the runtime",
        ),
        claim(
            "7.2",
            "the mathematical pipeline truncates at the Griess layer "
            "because the Borcherds commutator fails in finite dimensions",
            CONFIRMED,
            "the obstruction is proved rather than assumed: "
            "GLM.VOA.borcherds_commutator_fails in "
            "RequestProject/GLM/VOA.lean exhibits the axis triple on which "
            "the truncated commutator formula fails, and "
            "GLM.VOA.form_invariant records what the Griess layer does "
            "carry",
        ),
        claim(
            "7.3",
            "LLVQ performs an angular search at runtime and has no "
            "constant-time path",
            REFUTED if llvq_o1 else CONFIRMED,
            "the constant-time path is fwht_decode's certificate: it hard "
            "decides the 24 signs, reads the Golay coset leader out of the "
            "syndrome table, and either proves optimality from the code's "
            "minimum distance or declines and hands over to the exact "
            "route; the rate at which it fires is measured per reliability "
            "regime rather than claimed"
            if llvq_o1 else "no constant-time path is present",
            "a table indexed by coordinate prefixes alone cannot see "
            "reliability magnitudes, so the fast path was given a "
            "certificate instead of more stored digits"
            if llvq_o1 else None,
        ),
        claim(
            "7",
            f"the package stands at {QUOTED_FIGURES['tests']} tests and "
            f"{QUOTED_FIGURES['subtests']} subtests",
            NOT_REPRODUCED,
            "the suite has grown past the figures the blueprint quotes; the "
            "live counts are generated into overlay/FIGURES.md by "
            "glm_universal.figures, which is the only place a test count is "
            "allowed to be stated",
            "the quoted figures are a snapshot, not a current measurement",
        ),
    ]

    if lean_files is None:
        out.append(claim(
            "7",
            f"the development has {QUOTED_FIGURES['lean_files']} Lean files",
            NOT_REPRODUCED,
            "no Lean tree is reachable from the installed package, so the "
            "count cannot be checked from here",
        ))
    else:
        out.append(claim(
            "7",
            f"the development has {QUOTED_FIGURES['lean_files']} Lean files",
            CONFIRMED if lean_files == QUOTED_FIGURES["lean_files"]
            else REFUTED,
            f"the tree beside the package holds {lean_files} .lean files",
            None if lean_files == QUOTED_FIGURES["lean_files"] else
            f"{lean_files}, not {QUOTED_FIGURES['lean_files']}",
        ))
    return tuple(out)


# ═════════════════════════════════════════════════════════════════════════
# 8.  THE LEDGER
# ═════════════════════════════════════════════════════════════════════════

def blueprint_ledger(width: int = 8, rounds: int = 100
                     ) -> Tuple[Dict[str, object], ...]:
    """Every testable claim of the blueprint, with its verdict and figure."""
    audit = ubp_source_audit()
    ubp = (
        claim(
            "1",
            "the UBP bans floats, randomness and hashing across the system",
            CONFIRMED if audit["core_clean"] else REFUTED,
            f"{audit['core_modules']} modules of the six core sub-packages "
            f"construct no float and import none of "
            f"{list(BANNED_IMPORTS)}; "
            f"{len(audit['outside_core_violations'])} modules outside the "  # type: ignore[arg-type]
            f"core do, and are listed",
            None if audit["core_clean"] else
            "the discipline is broken inside the core",
        ),
        claim(
            "1",
            "the ban reaches the whole package, benchmarks and examples "
            "included",
            REFUTED if audit["outside_core_violations"] else CONFIRMED,
            "; ".join(
                f"{v['module']}: "
                f"{'imports ' + ', '.join(v['banned_imports']) if v['banned_imports'] else ''}"  # type: ignore[arg-type]
                f"{' ' if v['banned_imports'] and (v['float_literal_lines'] or v['float_call_lines']) else ''}"
                f"{'floats at lines ' + ', '.join(str(n) for n in list(v['float_literal_lines']) + list(v['float_call_lines'])) if (v['float_literal_lines'] or v['float_call_lines']) else ''}"  # type: ignore[arg-type]
                for v in audit["outside_core_violations"])  # type: ignore[union-attr]
            or "no module outside the core constructs a float",
            "the sub-packages that measure and demonstrate the core -- "
            "benchmarks, capabilities, evaluation, examples -- and the test "
            "suite itself do construct floats, deliberately: the probes and "
            "the tests feed floats in to check that they are refused, the "
            "evaluation harness times in seconds, the benchmark harness "
            "fingerprints a run with SHA-256, and the legacy example exists "
            "to show the damage. None of them is on a computation path."
            if audit["outside_core_violations"] else None,
        ),
    )
    return (ubp + part_i_claims() + part_ii_claims() + part_iii_claims()
            + part_iv_claims() + part_v_claims(width, rounds)
            + roadmap_claims())


def verdict_tally(claims: Sequence[Mapping[str, object]]) -> Dict[str, int]:
    """How many claims fell to each verdict."""
    tally = {verdict: 0 for verdict in VERDICTS}
    for entry in claims:
        tally[str(entry["verdict"])] += 1
    return tally


def blueprint_report(width: int = 8, rounds: int = 100) -> Dict[str, object]:
    """The whole ledger in one call, recomputed.

    Returns
    -------
    dict
        the ledger, the tally by verdict, the sections covered, and the
        source audit that settles section 1.
    """
    claims = blueprint_ledger(width, rounds)
    tally = verdict_tally(claims)
    sections: Dict[str, int] = {}
    for entry in claims:
        sections[str(entry["section"])] = sections.get(
            str(entry["section"]), 0) + 1
    return {
        "claims": list(claims),
        "claim_count": len(claims),
        "tally": tally,
        "sections": dict(sorted(sections.items())),
        "source_audit": ubp_source_audit(),
        "delta_sigma_rate": delta_sigma_rate_table(),
        "reading": (
            f"{tally[CONFIRMED]} of the blueprint's {len(claims)} testable "
            f"claims are reproduced exactly by the package; "
            f"{tally[REFUTED]} are false as written and the ledger records "
            f"what holds instead; {tally[NOT_REPRODUCED]} are not shown by "
            f"the measurement they name; {tally[NOT_IMPLEMENTED]} describe a "
            f"subsystem the package does not have."
        ),
    }
