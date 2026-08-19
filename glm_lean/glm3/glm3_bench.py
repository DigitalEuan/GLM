#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  GLM-3 BENCHMARK  —  measured pass rates, not showcase examples
================================================================================

  Part of:  The Geometric Language Machine, third generation (GLM-3).
  Layer  :  Tier 3b — evaluation of the whole stack.
  Deps   :  glm3_reasoner (hence all of GLM-3 and GLM-2).

  ------------------------------------------------------------------------
  Why this module exists
  ------------------------------------------------------------------------

  Up to now the evidence that the system reasons correctly was E = m c^2
  against E = m c^4: one true equation, one false one, and a handful of
  library pairs.  An anecdote is not an evaluation.  This module replaces it
  with four measurements, each with an unambiguous right answer, each
  reported as a pass rate over a stated denominator.

    A.  THE EXHAUSTIVE PAIRWISE SWEEP.  All C(660, 2) = 217,470 pairs from
        the register, comparing the verdict reached ENTIRELY INSIDE the
        Monster (facet words of Lambda/2Lambda classes) with the verdict of
        the GLM-2 meaning algebra.  The claim being measured is that the
        Monster layer is not an approximation of the meaning layer but a
        faithful rewriting of it, so the two must agree on every pair.

    B.  A CORPUS OF PHYSICAL LAWS.  Fifty-odd named laws — Newton, Coulomb,
        gravitation, Ohm, the ideal gas law, Planck, Stefan-Boltzmann,
        Bernoulli, drag, Lorentz, Poynting, Larmor, de Broglie, Compton,
        Rydberg, Josephson, Hall, Arrhenius, Beer-Lambert, Fick, Fourier,
        Darcy, Bragg, Boltzmann entropy, Friedmann, and individual
        Navier-Stokes and Maxwell terms — each of which must come out
        ADMISSIBLE.  They are written in the register's own vocabulary, so
        they test the codec, the parser, the tensor rank and parity
        bookkeeping and the Monster verdict at once.

    C.  DELIBERATELY CORRUPTED MUTANTS OF EVERY LAW.  Four mutation
        operators — shift one exponent, swap two quantities, change the
        tensor rank, change the decimal scale — applied to every law in the
        corpus.  Each mutant that genuinely changes the meaning must come out
        REJECTED, which turns "no false positives" into a measured rate; and
        because the Monster verdict NAMES the facet that failed, the report
        cross-tabulates mutation operator against the facet that caught it.
        A mutation that leaves the meaning intact (an exponent shift on a
        dimensionless factor, say) is counted separately as vacuous rather
        than being scored either way.

    D.  DIMENSIONLESS NUMBERS.  Reynolds, Mach, Prandtl, Nusselt, Froude,
        Weber, Peclet, Strouhal, Knudsen, Biot, Rossby, Ekman, Schmidt,
        Lewis, Grashof, Rayleigh, Bond, Capillary and a dozen more, each
        written out as its defining ratio and required to come out with EVERY
        exponent zero, scale zero and rank zero.  This is the widest fully
        automatic test in the project, and it stresses the codec's rational
        exponents in a way pairwise comparison does not: Froude needs a
        square root, Grashof a cube and a square, Ohnesorge a half power of a
        product of three quantities.

        One systematic exception is reported rather than hidden.  GLM-2
        promotes the plane angle to a dimension, which is what keeps torque
        and energy apart.  The Coriolis-based groups (Rossby, Ekman) are then
        NOT dimensionless as usually written, because the Coriolis parameter
        is measured in radians per second: the naive ratio carries A^-1.  The
        corpus contains both readings — the textbook one, marked as expected
        to carry a radian, and the angle-corrected one, which is
        dimensionless — and the report states which is which.

      python3 glm3_bench.py             # the whole benchmark
      python3 glm3_bench.py --quick     # skips the exhaustive sweep
      python3 glm3_bench.py laws        # one section only
      python3 glm3_bench.py mutants
      python3 glm3_bench.py numbers
      python3 glm3_bench.py sweep
================================================================================
"""

from __future__ import annotations

import itertools
import re
import sys
from fractions import Fraction as F
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from glm3_common import banner, fmt_int
from glm3_reasoner import REASONER

from glm2_parse import parse

__all__ = [
    "LAWS", "DIMENSIONLESS", "MUTATORS",
    "pairwise_sweep", "law_report", "mutant_report", "dimensionless_report",
    "benchmark", "summarise", "main",
]


# ══════════════════════════════════════════════════════════════════════════════
#  §B.  THE CORPUS OF PHYSICAL LAWS
# ══════════════════════════════════════════════════════════════════════════════
#
#  (name, left-hand side, right-hand side).  Both sides are read by the GLM-2
#  parser, so a side may be a concept, a product of concepts with rational
#  exponents, or one of the differential/tensor operations grad, div, curl,
#  ddt, dot, cross, moment.
#
#  Vector laws are written with a vector factor on the right, because the
#  register distinguishes rank and parity: `force = spring_constant * length`
#  is REJECTED (a rank-1 P-odd quantity is not a rank-0 P-even one) while
#  `force = spring_constant * position` is admissible.  That is not pedantry
#  imposed by the benchmark; it is the register refusing to equate a vector
#  with its magnitude, and the corpus is written to respect it.

LAWS: List[Tuple[str, str, str]] = [
    # ── mechanics ─────────────────────────────────────────────────────────
    ("newton_second", "force", "mass*acceleration"),
    ("newton_second_momentum", "force", "momentum/time"),
    ("hooke", "force", "spring_constant*position"),
    ("stokes_drag", "force", "dynamic_viscosity*length*velocity"),
    ("centripetal", "acceleration", "speed^2*position/area"),
    ("kinetic_energy", "kinetic_energy", "mass*speed^2"),
    ("work", "energy", "dot(force, position)"),
    ("gravitational_potential_energy", "energy",
     "mass*dot(gravitational_field, position)"),
    ("torque_definition", "torque", "moment(position, force)"),
    ("angular_momentum_definition", "angular_momentum",
     "moment_of_inertia*angular_velocity"),
    ("impulse_definition", "impulse", "force*time"),
    ("power_definition", "power", "dot(force, velocity)"),
    ("gravitation", "force",
     "gravitational_constant*mass^2*position/(area*length)"),
    ("mass_energy", "energy", "mass*speed^2"),
    ("heisenberg", "planck_constant", "dot(momentum, position)"),
    # ── fluids ────────────────────────────────────────────────────────────
    ("bernoulli_dynamic", "pressure", "density*speed^2"),
    ("bernoulli_static", "pressure", "density*dot(gravitational_field, position)"),
    ("drag_equation", "drag_force",
     "drag_coefficient*density*speed^2*area*position/length"),
    ("hagen_poiseuille", "volumetric_flow",
     "pressure*area^2/(dynamic_viscosity*length)"),
    ("navier_stokes_inertia", "density*speed/time", "pressure/length"),
    ("navier_stokes_viscous", "dynamic_viscosity*speed/area", "pressure/length"),
    ("continuity", "ddt(density)", "div(mass_current_density)"),
    ("mass_flow_definition", "mass_flow", "density*speed*area"),
    # ── electromagnetism ──────────────────────────────────────────────────
    ("coulomb", "force", "charge^2*position/(permittivity*area*length)"),
    ("ohm", "voltage", "current*resistance"),
    ("ohm_microscopic", "current_density", "conductivity*electric_field"),
    ("joule_heating", "power", "current^2*resistance"),
    ("capacitor_energy", "energy", "capacitance*voltage^2"),
    ("inductor_energy", "energy", "inductance*current^2"),
    ("faraday_induction", "voltage", "magnetic_flux/time"),
    ("lorentz_electric", "force", "charge*electric_field"),
    ("lorentz_magnetic", "force", "charge*cross(velocity, magnetic_flux_density)"),
    ("poynting", "poynting_vector", "cross(electric_field, magnetic_field_h)"),
    ("larmor", "power",
     "charge^2*dot(acceleration, acceleration)/(permittivity*speed^3)"),
    ("maxwell_faraday", "curl(electric_field)", "ddt(magnetic_flux_density)"),
    ("maxwell_ampere", "curl(magnetic_field_h)", "current_density"),
    ("maxwell_ampere_displacement", "curl(magnetic_field_h)",
     "ddt(electric_displacement)"),
    ("maxwell_gauss", "div(electric_displacement)", "charge_density"),
    ("vector_potential", "magnetic_flux_density", "curl(magnetic_vector_potential)"),
    ("electrostatic_potential", "electric_field", "grad(voltage)"),
    ("hall", "hall_coefficient", "1/(charge*number_density)"),
    ("josephson", "frequency", "josephson_constant*voltage"),
    # ── quantum, atomic, relativistic ─────────────────────────────────────
    ("planck_relation", "energy", "planck_constant*frequency"),
    ("de_broglie", "de_broglie_wavelength", "planck_constant/(mass*speed)"),
    ("compton", "compton_wavelength", "planck_constant/(mass*speed)"),
    ("rydberg", "wavenumber", "rydberg_energy/(planck_constant*speed)"),
    ("bragg", "wavelength", "length"),
    ("photoelectric", "energy", "work_function"),
    ("schwarzschild", "schwarzschild_radius",
     "gravitational_constant*mass/speed^2"),
    ("friedmann", "hubble_parameter^2", "gravitational_constant*density"),
    # ── thermodynamics, transport, chemistry ──────────────────────────────
    ("ideal_gas", "pressure", "amount*gas_constant*temperature/volume"),
    ("boltzmann_kinetic", "energy", "boltzmann_constant*temperature"),
    ("boltzmann_entropy", "entropy", "boltzmann_constant"),
    ("stefan_boltzmann", "heat_flux", "stefan_boltzmann*temperature^4"),
    ("wien", "wavelength*temperature", "planck_constant*speed/boltzmann_constant"),
    ("fourier_conduction", "heat_flux", "thermal_conductivity*temperature/length"),
    ("fick", "diffusion_flux", "diffusion_coefficient*grad(concentration)"),
    ("darcy", "darcy_flux",
     "intrinsic_permeability*pressure/(dynamic_viscosity*length)"),
    ("einstein_diffusion", "diffusion_coefficient",
     "boltzmann_constant*temperature/(dynamic_viscosity*length)"),
    ("arrhenius", "rate_constant_first", "frequency"),
    ("arrhenius_exponent", "1", "molar_energy/(gas_constant*temperature)"),
    ("beer_lambert", "1", "molar_absorptivity*concentration*length"),
    ("nernst", "voltage", "gas_constant*temperature/faraday_constant"),
    ("doppler", "frequency", "speed/wavelength"),
]


# ══════════════════════════════════════════════════════════════════════════════
#  §D.  DIMENSIONLESS GROUPS
# ══════════════════════════════════════════════════════════════════════════════
#
#  (name, defining expression, expected residual).  The expected residual is
#  the empty string for a genuinely dimensionless group, and otherwise the
#  dimension the angle-aware register says the textbook ratio actually
#  carries.  Nothing here is exempted from the test: a group with a nonempty
#  expected residual must carry exactly that residual and no other.

DIMENSIONLESS: List[Tuple[str, str, str]] = [
    ("reynolds", "density*speed*length/dynamic_viscosity", ""),
    ("mach", "speed/sound_speed", ""),
    ("prandtl", "kinematic_viscosity/thermal_diffusivity", ""),
    ("nusselt", "heat_transfer_coefficient*length/thermal_conductivity", ""),
    ("froude", "speed/(surface_gravity*length)^(1/2)", ""),
    ("weber", "density*speed^2*length/surface_tension", ""),
    ("peclet", "speed*length/thermal_diffusivity", ""),
    ("strouhal", "frequency*length/speed", ""),
    ("knudsen", "mean_free_path/length", ""),
    ("biot", "heat_transfer_coefficient*length/thermal_conductivity", ""),
    ("rossby_textbook", "speed/(coriolis_parameter*length)", "A^-1"),
    ("rossby_angle_corrected", "speed*angle/(coriolis_parameter*length)", ""),
    ("ekman_textbook", "kinematic_viscosity/(coriolis_parameter*area)", "A^-1"),
    ("ekman_angle_corrected", "kinematic_viscosity*angle/(coriolis_parameter*area)",
     ""),
    ("schmidt", "kinematic_viscosity/diffusion_coefficient", ""),
    ("lewis", "thermal_diffusivity/diffusion_coefficient", ""),
    ("grashof",
     "surface_gravity*thermal_expansion*temperature*length^3"
     "/kinematic_viscosity^2", ""),
    ("rayleigh",
     "surface_gravity*thermal_expansion*temperature*length^3"
     "/(kinematic_viscosity*thermal_diffusivity)", ""),
    ("bond", "density*surface_gravity*area/surface_tension", ""),
    ("capillary", "dynamic_viscosity*speed/surface_tension", ""),
    ("euler", "pressure/(density*speed^2)", ""),
    ("stokes", "time_constant*speed/length", ""),
    ("damkohler", "rate_constant_first*time", ""),
    ("fourier_group", "thermal_diffusivity*time/area", ""),
    ("atwood", "density/density", ""),
    ("ohnesorge",
     "dynamic_viscosity/(density*surface_tension*length)^(1/2)", ""),
    ("laplace", "density*surface_tension*length/dynamic_viscosity^2", ""),
    ("eckert", "speed^2/(specific_heat_capacity*temperature)", ""),
    ("brinkman", "dynamic_viscosity*speed^2/(thermal_conductivity*temperature)",
     ""),
    ("galilei",
     "surface_gravity*length^3/kinematic_viscosity^2", ""),
    ("archimedes",
     "surface_gravity*length^3*density^2/dynamic_viscosity^2", ""),
    ("stanton",
     "heat_transfer_coefficient/(density*speed*specific_heat_capacity)", ""),
    ("sherwood", "mass_transfer_coefficient*length/diffusion_coefficient", ""),
    ("courant", "speed*time/length", ""),
    ("fine_structure_group",
     "elementary_charge^2/(permittivity*planck_constant*speed)", ""),
    ("magnetic_reynolds", "speed*length/magnetic_diffusivity", ""),
    ("lundquist", "alfven_speed*length/magnetic_diffusivity", ""),
    ("hartmann",
     "dot(magnetic_flux_density, magnetic_flux_density)^(1/2)*length"
     "*(conductivity/dynamic_viscosity)^(1/2)", ""),
    ("plasma_beta_group", "pressure/magnetic_pressure", ""),
    ("weissenberg", "time_constant*strain_rate", ""),
]


# ══════════════════════════════════════════════════════════════════════════════
#  §C.  MUTATION OPERATORS
# ══════════════════════════════════════════════════════════════════════════════

_NAME_RE = re.compile(r"[A-Za-z_][A-Za-z_0-9]*")
_FUNCTIONS = {"dot", "cross", "moment", "grad", "div", "curl", "rot",
              "laplacian", "ddt", "integral_dt", "integral_dV"}


def _quantity_spans(text: str) -> List[Tuple[int, int]]:
    """The spans of the quantity names in an expression (not the functions)."""
    out = []
    for m in _NAME_RE.finditer(text):
        if m.group(0) in _FUNCTIONS:
            continue
        j = m.end()
        while j < len(text) and text[j] == " ":
            j += 1
        if j < len(text) and text[j] == "(":
            continue
        out.append((m.start(), m.end()))
    return out


def _meaning_or_none(text: str):
    try:
        return parse(text)
    except Exception:
        return None


def _pick(text: str, candidates: Sequence[str]) -> Optional[str]:
    """
    The first candidate that genuinely changes the meaning; failing that, the
    first candidate the parser refuses (a corruption caught one level lower);
    failing that, None, meaning the operator has nothing to say here.
    """
    base = _meaning_or_none(text)
    refused = None
    for cand in candidates:
        m = _meaning_or_none(cand)
        if m is None:
            refused = refused or cand
            continue
        if base is None or not m.commensurable(base):
            return cand
    return refused


def mutate_exponent(text: str, which: int = 0) -> Optional[str]:
    """
    Raise one factor to one power higher: `speed^2` becomes `speed^3`.  The
    factor is the first one for which this changes the meaning, so that
    bumping the exponent of a dimensionless coefficient does not count as a
    corruption.
    """
    out = []
    for s, e in _quantity_spans(text):
        rest = text[e:]
        m = re.match(r"\^\(?(-?\d+)\)?", rest)
        if m:
            new = int(m.group(1)) + 1
            out.append(f"{text[:s]}{text[s:e]}^({new}){rest[m.end():]}")
        else:
            out.append(f"{text[:e]}^2{text[e:]}")
    return _pick(text, out)


def mutate_swap(text: str, which: int = 0) -> Optional[str]:
    """
    Exchange two of the quantities in the expression — the first exchange
    that changes the meaning, since swapping two factors of a plain product
    changes nothing at all.
    """
    spans = _quantity_spans(text)
    out = []
    for i in range(len(spans)):
        for j in range(i + 1, len(spans)):
            (s1, e1), (s2, e2) = spans[i], spans[j]
            a, b = text[s1:e1], text[s2:e2]
            if a == b:
                continue
            out.append(text[:s1] + b + text[e1:s2] + a + text[e2:])
    return _pick(text, out)


def mutate_rank(text: str, which: int = 0) -> Optional[str]:
    """
    Multiply by a dimensionless RANK-ONE factor.  Nothing about the ten
    exponents or the decimal scale changes; only the tensor facet does.
    """
    return f"({text})*position/length"


def mutate_scale(text: str, which: int = 0) -> Optional[str]:
    """Multiply by 10^3: only the decimal scale changes."""
    return f"({text})*1000"


MUTATORS: Dict[str, Callable[[str, int], Optional[str]]] = {
    "exponent": mutate_exponent,
    "swap": mutate_swap,
    "rank": mutate_rank,
    "scale": mutate_scale,
}


# ══════════════════════════════════════════════════════════════════════════════
#  §A.  THE EXHAUSTIVE PAIRWISE SWEEP
# ══════════════════════════════════════════════════════════════════════════════

def pairwise_sweep(limit: Optional[int] = None, cross_check: int = 2000,
                   reasoner=None) -> Dict[str, object]:
    """
    Every pair of concepts in the register, Monster verdict against GLM
    verdict.

    The Monster verdict is the facet-word computation of
    `MonsterReasoner.monster_check`, evaluated here in its unrolled form so
    that a quarter of a million pairs is a second's work rather than an
    hour's: the facet words are computed once per concept and cached, and a
    pair is then four tuple comparisons.  That the unrolled form is the same
    computation is not assumed — `cross_check` pairs are run through
    `monster_check` itself and the verdicts compared.
    """
    r = reasoner or REASONER
    names = r.list_concepts()
    if limit:
        names = names[:limit]
    facets = ("dimension", "scale", "tensor", "kind")
    words: Dict[str, Tuple[Tuple[int, ...], ...]] = {}
    meanings = {}
    unencodable = []
    for n in names:
        try:
            words[n] = tuple(tuple(r.facet_word(n, f)) for f in facets)
            meanings[n] = r.meaning(n)
        except Exception:
            unencodable.append(n)
    zero = tuple(r.zero_word)
    usable = [n for n in names if n in words]

    pairs = 0
    agree = 0
    admissible = 0
    disagreements: List[Tuple[str, str]] = []
    for a, b in itertools.combinations(usable, 2):
        wa, wb = words[a], words[b]
        kind_ok = wa[3] == wb[3] or wa[3] == zero or wb[3] == zero
        monster = (wa[0] == wb[0] and wa[1] == wb[1] and wa[2] == wb[2]
                   and kind_ok)
        glm = meanings[a].commensurable(meanings[b])
        pairs += 1
        if monster:
            admissible += 1
        if monster == glm:
            agree += 1
        elif len(disagreements) < 8:
            disagreements.append((a, b))

    checked = 0
    unrolled_ok = True
    for a, b in itertools.islice(itertools.combinations(usable, 2),
                                 0, cross_check):
        rep = r.monster_check(a, b)
        wa, wb = words[a], words[b]
        kind_ok = wa[3] == wb[3] or wa[3] == zero or wb[3] == zero
        monster = (wa[0] == wb[0] and wa[1] == wb[1] and wa[2] == wb[2]
                   and kind_ok)
        checked += 1
        if (rep["verdict"] == "ADMISSIBLE") != monster or not rep[
                "agrees_with_glm"]:
            unrolled_ok = False
            break
    return {
        "concepts": len(usable),
        "unencodable": unencodable,
        "pairs": pairs,
        "agreements": agree,
        "disagreements": pairs - agree,
        "examples": disagreements,
        "admissible_pairs": admissible,
        "rejected_pairs": pairs - admissible,
        "cross_checked_against_monster_check": checked,
        "unrolled_form_agrees": unrolled_ok,
        "pass_rate": F(agree, pairs) if pairs else F(0),
    }


# ══════════════════════════════════════════════════════════════════════════════
#  §B / §C.  LAWS AND MUTANTS
# ══════════════════════════════════════════════════════════════════════════════

def _verdicts(lhs: str, rhs: str, reasoner=None) -> Dict[str, object]:
    """The GLM verdict and the in-Monster verdict for one equation."""
    r = reasoner or REASONER
    audit = r.audit(lhs, rhs)
    monster = r.monster_check(lhs, rhs)
    return {
        "glm_admissible": bool(audit.admissible),
        "monster_admissible": monster["verdict"] == "ADMISSIBLE",
        "failing_facets": list(monster["failing_facets"]),
        "reasons": audit.reasons(),
        "agree": bool(audit.admissible) == (monster["verdict"] == "ADMISSIBLE"),
        "plane0_agrees": bool(monster["plane0_agrees"]),
    }


def law_report(laws: Optional[Sequence[Tuple[str, str, str]]] = None,
               reasoner=None) -> Dict[str, object]:
    """Every law in the corpus must come out admissible, both ways."""
    laws = list(laws if laws is not None else LAWS)
    rows = []
    passed = 0
    agreed = 0
    errors = []
    for name, lhs, rhs in laws:
        try:
            v = _verdicts(lhs, rhs, reasoner)
        except Exception as exc:  # a parse failure is a failure
            errors.append((name, str(exc)))
            rows.append({"law": name, "lhs": lhs, "rhs": rhs,
                         "error": str(exc), "pass": False})
            continue
        ok = v["glm_admissible"] and v["monster_admissible"]
        passed += 1 if ok else 0
        agreed += 1 if v["agree"] else 0
        rows.append({"law": name, "lhs": lhs, "rhs": rhs, "pass": ok,
                     "reasons": v["reasons"],
                     "failing_facets": v["failing_facets"]})
    return {
        "laws": len(laws),
        "admissible": passed,
        "failures": [r["law"] for r in rows if not r["pass"]],
        "monster_agrees_with_glm": agreed,
        "errors": errors,
        "rows": rows,
        "pass_rate": F(passed, len(laws)) if laws else F(0),
    }


def mutant_report(laws: Optional[Sequence[Tuple[str, str, str]]] = None,
                  reasoner=None) -> Dict[str, object]:
    """
    Every law, corrupted four ways.  A mutant that genuinely changes the
    meaning must be REJECTED; a mutation that happens to leave the meaning
    unchanged is counted as vacuous and scored neither way.

    The report also cross-tabulates the mutation operator against the facet
    the Monster names as the one that failed, which is what the facet
    decomposition is for: `exponent` should be caught by the dimension facet,
    `rank` by the tensor facet, `scale` by the scale facet, and `swap` by
    whichever facet the swapped pair moved.
    """
    laws = list(laws if laws is not None else LAWS)
    r = reasoner or REASONER
    rows = []
    total = 0
    vacuous = 0
    rejected = 0
    false_negative = []
    disagreements = []
    by_operator: Dict[str, Dict[str, int]] = {k: {} for k in MUTATORS}
    for name, lhs, rhs in laws:
        for op, fn in MUTATORS.items():
            try:
                mutant = fn(rhs, 0)
            except Exception:
                mutant = None
            if mutant is None:
                continue
            try:
                v = _verdicts(lhs, mutant, r)
            except Exception:
                # a corruption the parser refuses is a rejection too, but it
                # is not a verdict of the system, so it is recorded apart
                rows.append({"law": name, "operator": op, "rhs": mutant,
                             "unparseable": True})
                continue
            total += 1
            if v["glm_admissible"]:
                vacuous += 1
                rows.append({"law": name, "operator": op, "rhs": mutant,
                             "vacuous": True})
                continue
            if v["monster_admissible"]:
                false_negative.append((name, op, mutant))
            else:
                rejected += 1
            if not v["agree"]:
                disagreements.append((name, op, mutant))
            caught = ",".join(v["failing_facets"]) or "none"
            by_operator[op][caught] = by_operator[op].get(caught, 0) + 1
            rows.append({"law": name, "operator": op, "rhs": mutant,
                         "rejected": not v["monster_admissible"],
                         "facets": v["failing_facets"],
                         "plane0_would_have_agreed": v["plane0_agrees"]})
    genuine = total - vacuous
    plane0_blind = sum(1 for row in rows
                       if row.get("plane0_would_have_agreed")
                       and row.get("rejected"))
    refused = [r for r in rows if r.get("unparseable")]
    detected = rejected + len(refused)
    denominator = genuine + len(refused)
    return {
        "mutants": total + len(refused),
        "vacuous": vacuous,
        "genuine_corruptions": denominator,
        "rejected_by_verdict": rejected,
        "refused_by_the_parser": len(refused),
        "rejected": detected,
        "false_negatives": false_negative,
        "false_negative_rate": (F(len(false_negative), denominator)
                                if denominator else F(0)),
        "monster_glm_disagreements": disagreements,
        "unparseable": refused,
        "facet_attribution": by_operator,
        "caught_by_the_stack_but_not_by_plane_0": plane0_blind,
        "rows": rows,
        "pass_rate": F(detected, denominator) if denominator else F(0),
    }


# ══════════════════════════════════════════════════════════════════════════════
#  §D.  DIMENSIONLESS GROUPS
# ══════════════════════════════════════════════════════════════════════════════

_AXIS_NAMES = ("L", "M", "T", "I", "K", "N", "J", "A", "S", "B")


def _residual(meaning) -> str:
    """The dimension of a meaning, written out, or "" if it has none."""
    parts = []
    for axis, e in zip(_AXIS_NAMES, meaning.exps):
        if e:
            parts.append(f"{axis}^{e}")
    return " ".join(parts)


def dimensionless_report(groups: Optional[Sequence[Tuple[str, str, str]]] = None
                         ) -> Dict[str, object]:
    """
    Each group must reduce to exactly the residual the corpus predicts —
    nothing at all for a genuine dimensionless number, and the stated radian
    power for the two Coriolis groups written in the textbook way.
    """
    groups = list(groups if groups is not None else DIMENSIONLESS)
    rows = []
    passed = 0
    truly_dimensionless = 0
    for name, expr, expected in groups:
        try:
            m = parse(expr)
        except Exception as exc:
            rows.append({"group": name, "expression": expr,
                         "error": str(exc), "pass": False})
            continue
        residual = _residual(m)
        ok = (residual == expected and m.scale == 0 and m.rank == 0)
        passed += 1 if ok else 0
        if ok and not expected:
            truly_dimensionless += 1
        rows.append({"group": name, "expression": expr, "residual": residual,
                     "expected": expected, "scale": m.scale, "rank": m.rank,
                     "pass": ok})
    return {
        "groups": len(groups),
        "as_expected": passed,
        "dimensionless": truly_dimensionless,
        "carrying_a_radian": [r["group"] for r in rows
                              if r.get("expected")],
        "failures": [r["group"] for r in rows if not r.get("pass")],
        "rows": rows,
        "pass_rate": F(passed, len(groups)) if groups else F(0),
    }


# ══════════════════════════════════════════════════════════════════════════════
#  THE WHOLE BENCHMARK
# ══════════════════════════════════════════════════════════════════════════════

def benchmark(quick: bool = False, reasoner=None) -> Dict[str, object]:
    """All four sections, as one report."""
    out: Dict[str, object] = {}
    out["laws"] = law_report(reasoner=reasoner)
    out["mutants"] = mutant_report(reasoner=reasoner)
    out["dimensionless"] = dimensionless_report()
    if not quick:
        out["pairwise"] = pairwise_sweep(reasoner=reasoner)
    else:
        out["pairwise"] = pairwise_sweep(limit=120, cross_check=200,
                                         reasoner=reasoner)
        out["pairwise"]["partial"] = True
    out["all_pass"] = (
        out["laws"]["pass_rate"] == 1
        and out["mutants"]["pass_rate"] == 1
        and out["dimensionless"]["pass_rate"] == 1
        and out["pairwise"]["pass_rate"] == 1
        and out["pairwise"]["unrolled_form_agrees"])
    return out


def _rate(x: F) -> str:
    return f"{float(x) * 100:.2f}%"


def summarise(report: Dict[str, object]) -> List[str]:
    """The benchmark as a table of pass rates."""
    lines = []
    law = report["laws"]
    mut = report["mutants"]
    dim = report["dimensionless"]
    pw = report["pairwise"]
    lines.append(f"  {'section':38s} {'pass':>10s}  {'of':>10s}   rate")
    lines.append(f"  {'-' * 38} {'-' * 10}  {'-' * 10}   {'-' * 7}")
    lines.append(f"  {'A. pairwise sweep (Monster vs GLM)':38s} "
                 f"{fmt_int(pw['agreements']):>10s}  "
                 f"{fmt_int(pw['pairs']):>10s}   {_rate(pw['pass_rate'])}")
    lines.append(f"  {'B. physical laws admissible':38s} "
                 f"{law['admissible']:>10d}  {law['laws']:>10d}   "
                 f"{_rate(law['pass_rate'])}")
    lines.append(f"  {'C. corrupted mutants rejected':38s} "
                 f"{mut['rejected']:>10d}  "
                 f"{mut['genuine_corruptions']:>10d}   "
                 f"{_rate(mut['pass_rate'])}")
    lines.append(f"  {'D. dimensionless groups as expected':38s} "
                 f"{dim['as_expected']:>10d}  {dim['groups']:>10d}   "
                 f"{_rate(dim['pass_rate'])}")
    return lines


def main(argv: Optional[Sequence[str]] = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    quick = "--quick" in argv
    argv = [a for a in argv if not a.startswith("--")]
    section = argv[0] if argv else None

    print(banner("GLM-3  BENCHMARK"))
    if section in (None, "laws"):
        rep = law_report()
        print(f"\nB.  PHYSICAL LAWS: {rep['admissible']}/{rep['laws']} "
              f"admissible, Monster agrees on "
              f"{rep['monster_agrees_with_glm']}/{rep['laws']}")
        for row in rep["rows"]:
            if not row["pass"]:
                print(f"    FAIL {row['law']}: {row.get('reasons')}"
                      f"{row.get('error', '')}")
    if section in (None, "mutants"):
        rep = mutant_report()
        print(f"\nC.  MUTANTS: {rep['rejected']}/{rep['genuine_corruptions']} "
              f"genuine corruptions caught "
              f"({rep['rejected_by_verdict']} by the verdict, "
              f"{rep['refused_by_the_parser']} refused by the parser; "
              f"{rep['vacuous']} vacuous mutations scored neither way)")
        for op, table in rep["facet_attribution"].items():
            got = ", ".join(f"{k}: {v}" for k, v in sorted(table.items()))
            print(f"    {op:9s} caught by  {got}")
        if rep["false_negatives"]:
            print(f"    FALSE NEGATIVES: {rep['false_negatives'][:5]}")
    if section in (None, "numbers"):
        rep = dimensionless_report()
        print(f"\nD.  DIMENSIONLESS GROUPS: {rep['as_expected']}/"
              f"{rep['groups']} as expected, {rep['dimensionless']} of them "
              f"exactly dimensionless")
        for row in rep["rows"]:
            if not row.get("pass"):
                print(f"    FAIL {row['group']}: residual "
                      f"{row.get('residual')} (expected "
                      f"{row.get('expected')!r}), scale {row.get('scale')}, "
                      f"rank {row.get('rank')}")
        if rep["carrying_a_radian"]:
            print(f"    carrying a radian by design: "
                  f"{', '.join(rep['carrying_a_radian'])}")
    if section in (None, "sweep"):
        rep = pairwise_sweep(limit=120 if quick else None,
                             cross_check=200 if quick else 2000)
        print(f"\nA.  PAIRWISE SWEEP: {fmt_int(rep['agreements'])}/"
              f"{fmt_int(rep['pairs'])} pairs agree "
              f"({fmt_int(rep['admissible_pairs'])} admissible, "
              f"{fmt_int(rep['rejected_pairs'])} rejected); the unrolled form "
              f"was cross-checked against monster_check on "
              f"{rep['cross_checked_against_monster_check']} pairs: "
              f"{rep['unrolled_form_agrees']}")
        if rep["disagreements"]:
            print(f"    DISAGREEMENTS: {rep['examples']}")

    if section is None:
        report = benchmark(quick=quick)
        print("\n" + "\n".join(summarise(report)))
        print(f"\n  {'ALL SECTIONS PASS' if report['all_pass'] else 'FAILURES'}")
        return 0 if report["all_pass"] else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
