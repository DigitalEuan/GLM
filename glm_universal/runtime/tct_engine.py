"""``glm_universal.runtime.tct_engine`` -- Three Column Thinking.

A Three Column Thinking (TCT) trace states one solved query three times over:

**Column 1 -- Language.**
    The deterministic reasoning chain in plain English, one sentence per step.

**Column 2 -- Exact mathematics.**
    The same chain as exact statements over ``Q``, ``Z`` and ``F_2``: rational
    equations, 2-adic digit-stack parameters, Griess forms, Norton-Sakuma
    products.  Every rational appears as a canonical ``"n/d"`` string.

**Column 3 -- Executable script.**
    A self-contained Python script that recomputes the answer from the public
    :mod:`glm_universal` API and *asserts* it against the values column 2
    claims.  It is run in a fresh interpreter by :func:`verify_trace`.

Why the third column is more than a printout
--------------------------------------------
The three columns are generated from one :class:`~glm_universal.runtime.
session.Solution`, so they cannot drift apart by construction.  What they
*could* still share is a bug in the solver.  Column 3 does not repeat the
solver's steps: it re-enters the package at its public API, in a separate
process, with the claimed values embedded as literals, and fails with a
non-zero exit code if anything differs.  Verification is therefore two
independent comparisons of the same claim:

1. the script's own ``assert`` against its embedded copy of the claim, whose
   outcome is the process exit code; and
2. :func:`verify_trace` re-reading the JSON the script emits and comparing it,
   key by key, to :attr:`~glm_universal.runtime.session.Solution.expected` in
   the parent process.

A trace is reported as verified only when both agree.  This is a same-session
cross-check between two code paths -- it is not a claim that the underlying
mathematics has been independently reproduced from a second implementation.

Invariants
----------
Generated scripts are held to the same standard as the package: no ``float``
literal, no ``float()`` call, no ``import random``, standard library plus
``glm_universal`` only.  :func:`script_is_exact` checks this by AST, and the
test suite applies it to the script of every trace it builds.
"""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from .session import Solution, Step

__all__ = [
    "TCTError", "BEGIN_MARKER", "END_MARKER", "DEFAULT_TIMEOUT_SECONDS",
    "ScriptVerdict", "ThreeColumnTrace", "package_root", "render_script",
    "script_is_exact", "build_trace", "verify_trace", "trace_to_markdown",
]


class TCTError(ValueError):
    """Raised when a trace cannot be built or its script cannot be rendered."""


#: The script brackets its JSON payload with these so that anything else it
#: prints -- a warning, a progress line -- cannot be mistaken for the payload.
BEGIN_MARKER = "GLM_TCT_JSON_BEGIN"
END_MARKER = "GLM_TCT_JSON_END"

#: Subprocess wall-clock ceiling.  Generous, because a ``product`` script
#: builds the exhaustive 98,280-class type-2 table before it can multiply.
DEFAULT_TIMEOUT_SECONDS = 900


def package_root() -> Path:
    """The directory that must be on ``sys.path`` to import ``glm_universal``."""
    return Path(__file__).resolve().parent.parent.parent


# ===========================================================================
# 1.  SCRIPT TEMPLATES
# ===========================================================================

_HEADER = '''"""Column 3 of a Three Column Thinking trace -- generated, self-contained.

Query : {query!r}
Kind  : {kind}

Recomputes the answer from the public glm_universal API in a fresh
interpreter and asserts it against the exact values column 2 claims.  Exits 0
only if every claim matches; exits 1 with a diff otherwise.
"""

import json
import sys
from fractions import Fraction

sys.path.insert(0, {root!r})

from glm_universal import data_objects as do
from glm_universal.reasoning import analogy as an
from glm_universal.reasoning import coherence as co
from glm_universal.reasoning import dimension_layers as dl
from glm_universal.reasoning import metric as me
from glm_universal.reasoning import product as pr
from glm_universal.reasoning import verifier as ve
from glm_universal.substrate import leech2, mog
from glm_universal.runtime.session import spatial_objects


def q(x):
    """Canonical "n/d" rendering of an exact scalar -- no float is ever made."""
    f = Fraction(x)
    return "%d/%d" % (f.numerator, f.denominator)


EXPECTED = {expected}

'''

_FOOTER = '''

# -- compare, report, and set the exit code ---------------------------------

mismatches = []
for key in sorted(EXPECTED):
    if key not in observed:
        mismatches.append((key, EXPECTED[key], "<missing>"))
    elif observed[key] != EXPECTED[key]:
        mismatches.append((key, EXPECTED[key], observed[key]))
extra = sorted(set(observed) - set(EXPECTED))

print({begin!r})
print(json.dumps({{"observed": observed,
                  "mismatches": [list(m) for m in mismatches],
                  "extra_keys": extra}},
                 sort_keys=True, indent=2))
print({end!r})

if mismatches:
    for key, want, got in mismatches:
        sys.stderr.write("MISMATCH %s: column 2 says %s, recomputation says "
                         "%s\\n" % (key, want, got))
    sys.exit(1)
sys.exit(0)
'''


def _pool_snippet(domain: str) -> str:
    """Source that binds ``pool`` to a domain's carriers and ``by_name``."""
    loaders = {
        "physics": "do.physics_objects()",
        "chemistry": "do.element_objects()",
        "molecules": "do.molecule_objects()",
        "mathematics": "do.mathematics_objects()",
        "lexicon": "do.semantic_lexicon_objects()[0]",
        "spatial": "spatial_objects()",
        "harmonics": "do.harmonic_objects()",
        "economics": "do.economics_objects()",
    }
    if domain not in loaders:
        raise TCTError(f"render_script: no pool loader for domain {domain!r}")
    return (f"pool = {loaders[domain]}\n"
            f"by_name = {{o.name: o for o in pool}}\n")


def _carrier_expr(name: object, formula: object) -> str:
    """Source for one operand's carrier: a look-up, or the formula parser.

    A solver that accepts an operand no register enumerates records the
    formula it built the carrier from; the generated script must build it the
    same way rather than looking up a name that is not there.
    """
    if formula is None:
        return f"by_name[{str(name)!r}]"
    return f"do.object_from_formula({str(formula)!r})"


def _two_operand_snippet(args: Mapping[str, object]) -> str:
    """Source binding ``obj_a`` and ``obj_b`` for a two-carrier template.

    The two operands may sit in different domains, so each is looked up in
    its own pool -- or, when the solver built it from a chemical formula
    rather than finding it in a register, rebuilt from that formula.
    """
    lines = ["# Two pools may be needed -- the operands may differ in "
             "domain."]
    for suffix in ("a", "b"):
        formula = args.get(f"formula_{suffix}")
        if formula is None:
            lines.append(
                f"pool_{suffix} = {_POOL_TABLE}"
                f"[{str(args[f'domain_{suffix}'])!r}]")
            lines.append(
                f"obj_{suffix} = next(o for o in pool_{suffix} "
                f"if o.name == {str(args[f'name_{suffix}'])!r})")
        else:
            lines.append(
                f"obj_{suffix} = do.object_from_formula({str(formula)!r})")
    return "\n".join(lines) + "\n"


#: The domain -> carrier-pool table the two-operand templates index into.
_POOL_TABLE = (
    '{"physics": do.physics_objects(), '
    '"chemistry": do.element_objects(), '
    '"molecules": do.molecule_objects(), '
    '"mathematics": do.mathematics_objects(), '
    '"lexicon": do.semantic_lexicon_objects()[0], '
    '"spatial": spatial_objects(), '
    '"harmonics": do.harmonic_objects(), '
    '"economics": do.economics_objects()}')


def _body_verify(args: Mapping[str, object]) -> str:
    return f'''# -- recompute -------------------------------------------------------------

verdict = ve.verify_expression_pair({args["lhs"]!r}, {args["rhs"]!r},
                                    {args["semantics"]!r})

observed = {{
    "holds": str(verdict.holds),
    "lhs_dimension": str(verdict.lhs_dimension),
    "rhs_dimension": str(verdict.rhs_dimension),
    "lhs_rank": str(verdict.lhs_rank),
    "rhs_rank": str(verdict.rhs_rank),
    "failing_planes": str(list(verdict.failing_planes)),
    "blamed_facets": str(list(verdict.blamed_facets)),
}}
'''


def _body_analogy(args: Mapping[str, object]) -> str:
    return f'''# -- recompute -------------------------------------------------------------

{_pool_snippet(str(args["domain"]))}
result = an.solve_analogy_objects(by_name[{args["a"]!r}],
                                  by_name[{args["b"]!r}],
                                  by_name[{args["c"]!r}],
                                  pool, subspace={args["subspace"]!r})

observed = {{
    "answer": result.answer,
    "distance2": q(result.distance2),
    "exact_hit": str(result.exact_hit),
    "unique": str(result.unique),
    "tied": str(list(result.tied)),
}}
'''


def _body_analogy_model(args: Mapping[str, object]) -> str:
    return f'''# -- recompute -------------------------------------------------------------

from glm_universal.reasoning import analogy_models as am

{_pool_snippet(str(args["domain"]))}
model = am.explain_analogy({args["domain"]!r}, {args["a"]!r}, {args["b"]!r},
                           {args["c"]!r}, pool)

observed = {{
    "model": model.model,
    "answer": str(model.answer),
    "candidates": str(list(model.candidates)),
    "unique": str(model.unique),
}}
'''


def _body_report_analogies(args: Mapping[str, object]) -> str:
    return '''# -- recompute -------------------------------------------------------------

from glm_universal.reasoning import analogy_models as am

report = am.analogy_models_report()
table = report["periodic_table"]

observed = {
    "cases_total": str(report["cases_total"]),
    "cases_as_expected": str(report["cases_as_expected"]),
    "models": str(list(report["models"])),
    "periods_agree_with_register":
        str(table["periods_agree_with_register"]),
    "noble_gases": str(list(table["noble_gases"])),
}
for row in report["cases"]:
    observed["case_%s" % row["question"]] = "%s:%s" % (row["model"],
                                                       row["answer"])
'''


def _body_describe(args: Mapping[str, object]) -> str:
    return f'''# -- recompute -------------------------------------------------------------

{_pool_snippet(str(args["domain"]))}
obj = by_name[{args["name"]!r}]
params = obj.parameters()
address = obj.monster_address()
# v0.5.3: wires analogy.nearest_lattice_point into the describe payload.
lattice = an.nearest_lattice_point(list(obj.carrier))

observed = {{
    "name": obj.name,
    "domain": obj.domain,
    "depth": str(params.depth),
    "offset": str(params.offset),
    "plane0_mask": str(address["plane0_mask"]),
    "plane0_weight": str(address["plane0_weight"]),
    "is_golay_codeword": str(address["is_golay_codeword"]),
    "round_trip_ok": str(obj.round_trip_ok()),
    "griess_norm2": q(me.griess_norm2(obj.carrier)),
    "lattice_distance2": q(lattice.distance2),
    "lattice_norm2": q(lattice.norm2),
    "lattice_is_2a_axis": str(lattice.is_2a_axis),
}}
'''


def _body_describe_arithmetic(args: Mapping[str, object]) -> str:
    """Re-evaluate arithmetic over register names (v1.3.0)."""
    expression = str(args["expression"])
    return f'''# -- recompute -------------------------------------------------------------

from glm_universal.reasoning import term_arithmetic as tar

_result = tar.evaluate({expression!r})

observed = {{
    "source": _result.source,
    "normalised": _result.normalised,
    "ext10": _result.ext10,
    "si7": _result.si7,
    "scale": str(_result.sense.scale),
    "rank": str(_result.sense.rank),
    "name_count": str(len(_result.names)),
    "names": str(list(_result.names[:tar.NAMES_SHOWN])),
}}
'''


def _body_project(args: Mapping[str, object]) -> str:
    """Template for the v0.5.3 'project A B' query kind.

    Recomputes the layered projection from the substrate up to the
    universal layer, reporting each layer's view of the two carriers and
    the distance it measured.  Wires ``reasoning/dimension_layers.escalate``.
    """
    return f'''# -- recompute -------------------------------------------------------------

{_two_operand_snippet(args)}
# Walk every dimension-projection layer.
result = dl.escalate(obj_a.carrier, obj_b.carrier, start=0)
all_views = result["all_views"]
final_layer = result["layer"]

observed = {{
    "operand_a": obj_a.name,
    "operand_b": obj_b.name,
    "layers_walked": str(len(all_views)),
    "final_layer": final_layer.name,
    "final_distance": q(Fraction(result["distance"])),
}}
'''


def _body_trilinear(args: Mapping[str, object]) -> str:
    """Template for the v0.5.3 'trilinear A B C' query kind.

    Projects each carrier onto its nearest 2A axis (via the Leech
    lattice's type-2 class) and computes the invariant trilinear form
    ``T(A, B, C) = <A.B, C>`` of the Griess algebra.  Wires
    ``reasoning/product.griess_trilinear``.
    """
    return f'''# -- recompute -------------------------------------------------------------

pool = {{
    "physics": do.physics_objects(),
    "chemistry": do.element_objects(),
    "mathematics": do.mathematics_objects(),
    "lexicon": do.semantic_lexicon_objects()[0],
    "spatial": spatial_objects(),
    "harmonics": do.harmonic_objects(),
    "economics": do.economics_objects(),
}}[{args["domain_a"]!r}]
by_name = {{o.name: o for o in pool}}
obj_a = by_name[{args["name_a"]!r}]
obj_b = by_name[{args["name_b"]!r}]
obj_c = by_name[{args["name_c"]!r}]

# Project each carrier onto its nearest 2A axis via the Leech lattice.
lat_a = an.nearest_lattice_point(list(obj_a.carrier))
lat_b = an.nearest_lattice_point(list(obj_b.carrier))
lat_c = an.nearest_lattice_point(list(obj_c.carrier))
cls_a = leech2.class_of(list(lat_a.point))
cls_b = leech2.class_of(list(lat_b.point))
cls_c = leech2.class_of(list(lat_c.point))
ax_a = pr.axis(cls_a)
ax_b = pr.axis(cls_b)
ax_c = pr.axis(cls_c)

# The invariant trilinear form T(A, B, C) = <A.B, C>.
T = pr.griess_trilinear(ax_a, ax_b, ax_c)
# Pairwise bilinear forms: squared norms of the pairwise products.
prod_ab = pr.axis_product(cls_a, cls_b)
prod_ac = pr.axis_product(cls_a, cls_c)
prod_bc = pr.axis_product(cls_b, cls_c)
Tab = pr.griess_form(prod_ab, prod_ab)
Tac = pr.griess_form(prod_ac, prod_ac)
Tbc = pr.griess_form(prod_bc, prod_bc)

observed = {{
    "operand_a": obj_a.name,
    "operand_b": obj_b.name,
    "operand_c": obj_c.name,
    "axis_a": str(cls_a),
    "axis_b": str(cls_b),
    "axis_c": str(cls_c),
    "trilinear": q(T),
    "pairwise_AB": q(Tab),
    "pairwise_AC": q(Tac),
    "pairwise_BC": q(Tbc),
}}
'''


def _body_coherence(args: Mapping[str, object]) -> str:
    """Template for the v0.5.3 'coherence <concept>' query kind.

    Recomputes the five-shell NRCI breakdown.  Wires
    ``reasoning/coherence.nrci_breakdown``.
    """
    return f'''# -- recompute -------------------------------------------------------------

{_pool_snippet(str(args["domain"]))}
obj = {_carrier_expr(args["name"], args.get("formula"))}
carrier = list(obj.carrier)

breakdown = co.nrci_breakdown(carrier)
regime = breakdown.get("regime") or co.coherence_regime(breakdown["nrci"])
nrci_value = Fraction(breakdown["nrci"])
nrci_str = q(nrci_value)

def _render(v):
    if isinstance(v, Fraction):
        return q(v)
    return str(v)

observed = {{
    "name": obj.name,
    "domain": obj.domain,
    "nrci": nrci_str,
    "regime": regime,
    "shell0_golay": _render(breakdown["shell0_golay"]),
    "shell1_sign_parity": _render(breakdown["shell1_sign_parity"]),
}}
'''


# ===========================================================================
# v0.5.4 templates: report and angle query kinds
# ===========================================================================

def _body_report_relations(args: Mapping[str, object]) -> str:
    """Recompute the verifier's 222+71 relation audit (v0.5.4)."""
    return '''# -- recompute -------------------------------------------------------------

report = ve.verifier_report()
scalar_scalar = report["scalar_relations_under_scalar_semantics"]
scalar_full = report["scalar_relations_under_full_semantics"]
tensor_full = report["tensor_relations_under_full_semantics"]

observed = {
    "scalar_scalar_checked": str(scalar_scalar["checked"]),
    "scalar_scalar_held": str(scalar_scalar["held"]),
    "scalar_full_checked": str(scalar_full["checked"]),
    "scalar_full_held": str(scalar_full["held"]),
    "scalar_full_failed": str(scalar_full["failed"]),
    "tensor_full_checked": str(tensor_full["checked"]),
    "tensor_full_held": str(tensor_full["held"]),
}
'''


def _body_report_leech(args: Mapping[str, object]) -> str:
    """Recompute the Leech lattice pair census (v0.5.4)."""
    return '''# -- recompute -------------------------------------------------------------

census = leech2.pair_census()

observed = {
    "position_4": str(census[4]),
    "position_2": str(census[2]),
    "position_1": str(census[1]),
    "position_0": str(census[0]),
}
'''


def _body_report_information_loss(args: Mapping[str, object]) -> str:
    """Recompute the layer-boundary information-loss study (v0.7.0)."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal.reasoning import information_loss as il

report = il.information_loss_report()
raw = report["non_cumulative"]

observed = {"carrier_count": str(report["carrier_count"])}
for _layer in report["layers"]:
    _name = _layer["name"]
    observed["resolution_" + _name] = str(_layer["resolution"])
    observed["loss_" + _name] = str(_layer["loss_count"])
    observed["addition_descends_" + _name] = str(_layer["addition_descends"])
for _edge in report["boundaries"]:
    _key = _edge["lower"] + "_to_" + _edge["higher"]
    observed["lost_count_" + _key] = str(_edge["lost_count"])
    observed["refines_" + _key] = str(_edge["refines"])
observed["refinement_chain_intact"] = str(report["refinement_chain_intact"])
observed["non_cumulative_refines_substrate"] = str(raw["refines_substrate"])
observed["non_cumulative_violations"] = str(raw["violation_count"])
observed["cumulative_refines_substrate"] = str(
    raw["cumulative_refines_substrate"])
'''


def _body_report_noise(args) -> str:
    """Recompute the noise laboratory in a fresh interpreter (v1.5.0)."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal.reasoning import noise_lab as nlb


def _q(value):
    from fractions import Fraction
    f = Fraction(value)
    return str(f.numerator) + "/" + str(f.denominator)


report = nlb.noise_report()
track = report["signal_tracking"]
closing = report["orbit_closure"]["closing"]
open_orbit = report["orbit_closure"]["not_closing"]
cascade = report["cascade"]
sweep = report["dither_sweep"]
feedback = report["feedback"]
tracking = feedback["tracking"]
equivariant = feedback["equivariant"]
asymmetric = feedback["not_equivariant"]
dead = feedback["dead_zone"]

observed = {
    "signal_period": str(track["period"]),
    "signal_input_mean": _q(track["input_mean"]),
    "signal_bit_mean": _q(track["bit_mean"]),
    "signal_within_bound": str(track["within_bound"]),
    "state_stayed_in_range": str(track["state_stayed_in_range"]),
    "closing_period_sum": _q(closing["period_sum"]),
    "closing_orbit_closed": str(closing["orbit_closed"]),
    "open_period_sum": _q(open_orbit["period_sum"]),
    "open_orbit_closed": str(open_orbit["orbit_closed"]),
    "cascade_second_difference": str(cascade["second_difference_holds"]),
    "cascade_double_sum": _q(cascade["double_sum"]),
    "cascade_double_sum_equals_state": str(
        cascade["double_sum_equals_state"]),
    "cascade_triangular_error": _q(cascade["triangular_error"]),
    "cascade_triangular_bound": _q(cascade["triangular_bound"]),
    "dither_monotone": str(sweep["monotone_in_amplitude"]),
    "dither_undithered_peak": _q(sweep["undithered_peak_fraction"]),
    "dither_lowest_peak": _q(sweep["lowest_peak_fraction"]),
    "feedback_bound": _q(tracking["bound"]),
    "feedback_within_bound": str(tracking["within_bound"]),
    "feedback_errors_bounded": str(tracking["errors_bounded"]),
    "feedback_equivariant": str(equivariant["outputs_permute"]),
    "feedback_not_equivariant": str(asymmetric["outputs_permute"]),
    "feedback_dead_zone_silent": str(dead["contracting_outputs_all_zero"]),
    "feedback_dead_zone_error": _q(dead["contracting_error"]),
    "feedback_identity_fires": str(dead["identity_fires"]),
}
for _index, _value in enumerate(tracking["coordinate_errors"]):
    observed["feedback_error_" + str(_index)] = _q(_value)
for _row in report["convergence_third"]:
    observed["third_error_" + str(_row["window"])] = _q(_row["cascade_error"])
    observed["third_single_" + str(_row["window"])] = _q(
        _row["single_loop_error"])
'''


def _body_report_lattices(args) -> str:
    """Recompute the 24 -> 32 -> 48 lattice ladder in a fresh interpreter."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal.reasoning import higher_lattices as hlt


def _q(value):
    from fractions import Fraction
    f = Fraction(value)
    return str(f.numerator) + "/" + str(f.denominator)


report = hlt.higher_lattices_report()
ladder = report["ladder"]
rows = ladder["rows"]
leech = [r for r in rows if r["dimension"] == 24][0]
bw = [r for r in rows if r["dimension"] == 32][0]
top = [r for r in rows if r["dimension"] == 48][0]
d32 = report["dimension_32"]
codes = d32["codes"]
det = d32["determinant"]
kissing = d32["kissing"]
address = d32["address"]
trip = d32["round_trip"]
d48 = report["dimension_48"]

observed = {
    "all_extremal": str(ladder["all_extremal"]),
    "density_24": _q(leech["centre_density"]),
    "density_32": _q(bw["centre_density"]),
    "density_48": _q(top["centre_density"]),
    "minimum_32": str(bw["minimum"]),
    "minimum_48": str(top["minimum"]),
    "outer_minimum_weight": str(codes["outer"]["minimum_weight"]),
    "inner_minimum_weight": str(codes["inner"]["minimum_weight"]),
    "dual_pair": str(address["dual_pair"]),
    "even_32": str(det["even"]),
    "gram_is_2_to_64": str(det["gram_determinant_is_2_to_64"]),
    "kissing_32": str(kissing["total"]),
    "address_total_index": str(address["total_index"]),
    "round_trip": str(trip["all_round_trip"]),
    "levels_usable": str(trip["all_levels_usable"]),
    "binary_route_minimum": str(d48["binary_route_stops_at"]),
    "ternary_self_dual": str(d48["ternary_code"]["self_dual"]),
    "ternary_minimum_weight": str(d48["ternary_code"]["minimum_weight"]),
    "even_sublattice_minimum": _q(d48["even_sublattice_minimum"]),
    "full_weight_total": str(d48["full_weight_census"]["total"]),
    "full_weight_even": str(
        d48["full_weight_census"]["even_number_of_twos"]),
    "full_weight_odd": str(d48["full_weight_census"]["odd_number_of_twos"]),
    "N1_minimum": _q(d48["N1_minimum"]),
    "N2_minimum": _q(d48["N2_minimum"]),
    "N2_extremal": str(d48["extremal"]),
}
for _shape, _count in kissing["counts"].items():
    observed["kissing_" + _shape] = str(_count)
'''


def _body_report_lean(args) -> str:
    """Recompute the Lean address study in a fresh interpreter."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal.reasoning import lean_address as lad


def _q(value):
    from fractions import Fraction
    f = Fraction(value)
    return str(f.numerator) + "/" + str(f.denominator)


report = lad.lean_address_report()
corpus = report["corpus"]
cache = report["cache"]
guarantee = report["guarantee"]
trip = report["round_trip"]
sep = report["separation"]
feature = sep["feature"]
control = sep["hash_control"]
null = sep["shuffled"]
inj = feature["injectivity"]

observed = {
    "declarations": str(corpus["declarations"]),
    "files": str(corpus["files"]),
    "cache_verdict": str(cache["verdict"]),
    "scale": str(report["features"]["scale"]),
    "covering_radius": str(guarantee["covering_radius"]),
    "moved": str(guarantee["moved_by_the_decoder"]),
    "worst_residual": str(guarantee["worst_observed_residual"]),
    "read_back_exact": str(trip["exact"]),
    "coordinate_errors": str(trip["coordinate_errors"]),
    "distinct_addresses": str(inj["distinct_addresses"]),
    "distinct_features": str(inj["distinct_feature_vectors"]),
    "collision_classes": str(inj["collision_classes"]),
    "largest_class": str(inj["largest_class_size"]),
    "feature_same_file": str(feature["neighbours"]["same_file_nearest"]),
    "control_same_file": str(control["neighbours"]["same_file_nearest"]),
    "shuffled_same_file": str(null["neighbours"]["same_file_nearest"]),
    "same_file_chance": _q(feature["neighbours"]["same_file_chance"]),
    "feature_linked": str(feature["neighbours"]["linked_nearest"]),
    "linked_chance": _q(feature["neighbours"]["linked_chance"]),
    "feature_beats_control": str(sep["verdict"]["feature_beats_hash_control"]),
    "hash_is_chance_like": str(sep["verdict"]["hash_is_chance_like"]),
}
'''


def _body_report_directives(args) -> str:
    """Recompute the directives table in a fresh interpreter."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal.reasoning import directives as drc

report = drc.directives_report()
rows = report["rows"]

observed = {
    "count": str(report["count"]),
    "instrumented": str(report["instrumented"]),
    "defects": str(len(report["defects"])),
    "sound": str(report["sound"]),
    "words": str(report["words"]),
    "keys": ",".join(_r["key"] for _r in rows),
}
'''


def _body_report_pipeline(args) -> str:
    """Recompute the pipeline board in a fresh interpreter."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal.reasoning import pipeline as ppl

report = ppl.pipeline_report()

observed = {
    "rows": str(report["count"]),
    "complete": str(report["complete"]),
    "incomplete": ",".join(report["incomplete"]) or "none",
    "total_tests": str(report["total_tests"]),
    "stages": ",".join(report["stages"]),
}
for _row in report["rows"]:
    observed["stage_" + _row["key"]] = str(_row["stages_reached"])
'''


def _body_report_shells(args) -> str:
    """Recompute the shell delta-sigma study in a fresh interpreter."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal.reasoning import shell_sigma as shs


def _q(value):
    from fractions import Fraction
    f = Fraction(value)
    return str(f.numerator) + "/" + str(f.denominator)


report = shs.shell_sigma_report()
shell = report["shell"]
ball = report["inner_ball"]
inside = report["inside"]
run = inside["run"]
outside = report["outside"]
lattice = report["lattice"]
gibbs = report["gibbs"]
uniform = gibbs["rows"][0]
cold = gibbs["rows"][-1]

observed = {
    "shell_size": str(shell["size"]),
    "shell_norm2": str(shell["norm2"]),
    "inner_ball_radius2": _q(ball["radius_squared"]),
    "inside_ticks": str(run["ticks"]),
    "inside_error2": _q(run["error_norm2"]),
    "inside_half_error2": _q(inside["half_run_error_norm2"]),
    "inside_error_fell": str(inside["error_fell"]),
    "inside_max_state2": _q(run["max_state_norm2"]),
    "inside_margin_held": str(inside["margin_hypothesis_held"]),
    "inside_on_shell": str(run["all_on_shell"]),
    "outside_support": _q(outside["support_in_direction"]),
    "outside_target": _q(outside["target_in_direction"]),
    "outside_separated": str(outside["separated"]),
    "outside_gap": _q(outside["gap"]),
    "outside_final_state2": _q(outside["run"]["final_state_norm2"]),
    "lattice_max_state2": _q(lattice["max_state_norm2"]),
    "lattice_within_covering": str(lattice["within_covering_radius"]),
    "lattice_error2": _q(lattice["error_norm2"]),
    "lattice_bound2": _q(lattice["error_bound_norm2"]),
    "lattice_within_bound": str(lattice["within_bound"]),
    "gibbs_candidates": str(gibbs["candidate_count"]),
    "gibbs_energies": ",".join(str(_e) for _e in gibbs["energies"]),
    "gibbs_uniform_error": _q(uniform["max_frequency_error"]),
    "gibbs_cold_weight": _q(cold["weights"][0]),
    "gibbs_cold_error": _q(cold["max_frequency_error"]),
    "gibbs_bound": _q(cold["bound"]),
    "gibbs_within_bound": str(cold["within_bound"]),
}
'''


def _body_report_llvq(args) -> str:
    """Recompute the LLVQ class table and its agreement, fresh."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal.reasoning import llvq_table as llt

report = llt.llvq_table_report()
shape = report["characterisation"]
cost = report["cost"]
agree = report["agreement"]
corpus = llt.corpus_report(limit=150)

observed = {
    "codewords": str(shape["codewords"]),
    "classes": str(shape["classes"]),
    "class_size": str(report["class_size"]),
    "table_entries": str(report["table_entries"]),
    "hexacode_words": str(report["hexacode_words"]),
    "accounts_for_the_code": str(shape["accounts_for_the_code"]),
    "shadow_failures": str(shape["shadow_failures"]),
    "rebuild_failures": str(shape["rebuild_failures"]),
    "reference_words_per_call": str(cost["reference_words_per_call"]),
    "reference_additions_per_call": str(cost["reference_additions_per_call"]),
    "agreement_checked": str(agree["checked"]),
    "agreement_mismatches": str(agree["mismatches"]),
    "corpus_declarations": str(corpus["declarations"]),
    "corpus_unchanged": str(corpus["addresses_unchanged"]),
    "corpus_all_unchanged": str(corpus["all_unchanged"]),
}
'''


def _body_measure(args) -> str:
    """Re-read one measure word against one comparison class, fresh."""
    word = str(args.get("word", ""))
    klass = str(args.get("klass", ""))
    return f'''# -- recompute -------------------------------------------------------------

from fractions import Fraction

from glm_universal.data_objects import comparison_classes as cc
from glm_universal.reasoning import measure_view as mvw


def _q(_x):
    _f = Fraction(_x)
    return str(_f.numerator) + "/" + str(_f.denominator)


_word = {word!r}
_klass = {klass!r}
reading = mvw.read(_word, _klass)
entry = mvw.word_by_name(_word)
others = [mvw.read(_word, _c.name)
          for _c in cc.classes_for_quantity(reading.quantity)
          if _c.name != _klass]

observed = {{
    "word": _word,
    "comparison_class": _klass,
    "quantity": reading.quantity,
    "unit": reading.unit,
    "dimension": reading.dimension,
    "position": _q(reading.position),
    "magnitude": _q(reading.magnitude),
    "low": _q(reading.low),
    "high": _q(reading.high),
    "above_on": ",".join(mvw.above_on(_word)),
    "status": entry.status,
    "other_classes": ",".join(
        _o.comparison_class + ":" + _q(_o.magnitude) for _o in others),
}}

# The magnitude is recomputed from the bracket rather than trusted.
_klass_obj = cc.class_by_name(_klass)
assert reading.magnitude == (
    _klass_obj.low + reading.position * (_klass_obj.high - _klass_obj.low))
'''


def _body_measure_magnitude(args) -> str:
    """Re-place one magnitude in one comparison class, fresh."""
    magnitude = str(args.get("magnitude", "0"))
    klass = str(args.get("klass", ""))
    return f'''# -- recompute -------------------------------------------------------------

from fractions import Fraction

from glm_universal.reasoning import measure_view as mvw


def _q(_x):
    _f = Fraction(_x)
    return str(_f.numerator) + "/" + str(_f.denominator)


_magnitude = Fraction({magnitude!r})
_klass = {klass!r}
verdict = mvw.classify(_magnitude, _klass)

observed = {{
    "magnitude": _q(_magnitude),
    "comparison_class": _klass,
    "quantity": str(verdict["quantity"]),
    "unit": str(verdict["unit"]),
    "position": _q(verdict["position"]),
    "inside_bracket": str(verdict["inside_bracket"]),
    "word": str(verdict["word"]),
    "word_position": _q(verdict["word_position"]),
    "above": ",".join(verdict["above"]),
}}
'''


def _body_measure_word(args) -> str:
    """Re-read one word against every class of its quantity, fresh."""
    word = str(args.get("word", ""))
    return f'''# -- recompute -------------------------------------------------------------

from fractions import Fraction

from glm_universal.data_objects import comparison_classes as cc
from glm_universal.reasoning import measure_view as mvw


def _q(_x):
    _f = Fraction(_x)
    return str(_f.numerator) + "/" + str(_f.denominator)


_word = {word!r}
entry = mvw.word_by_name(_word)
readings = [mvw.read(_word, _c.name)
            for _c in cc.classes_for_quantity(entry.quantity)]
_low = min(readings, key=lambda _r: _r.magnitude)
_high = max(readings, key=lambda _r: _r.magnitude)

observed = {{
    "word": _word,
    "quantity": str(entry.quantity),
    "position": _q(entry.position),
    "classes": ",".join(_r.comparison_class for _r in readings),
    "magnitudes": ",".join(_q(_r.magnitude) for _r in readings),
    "lowest": _low.comparison_class,
    "highest": _high.comparison_class,
    "ratio": _q(_high.magnitude / _low.magnitude),
}}
'''


def _body_comparative(args) -> str:
    """Re-decide one comparative between two measured uses, fresh."""
    form = str(args.get("form", ""))
    equative = bool(args.get("equative", False))
    left_word = str(args.get("left_word", ""))
    left_class = str(args.get("left_class", ""))
    right_word = str(args.get("right_word", ""))
    right_class = str(args.get("right_class", ""))
    return f'''# -- recompute -------------------------------------------------------------

from fractions import Fraction

from glm_universal.reasoning import measure_view as mvw


def _q(_x):
    _f = Fraction(_x)
    return str(_f.numerator) + "/" + str(_f.denominator)


verdict = mvw.answer_comparative(
    {form!r}, {left_word!r}, {left_class!r}, {right_word!r}, {right_class!r},
    equative={equative!r})
comparison = verdict["comparison"]
audit = mvw.comparative_audit()

observed = {{
    "form": {form!r},
    "stem": str(verdict["stem"]),
    "equative": str({equative!r}),
    "direction": str(verdict["direction"]),
    "quantity": str(verdict["quantity"]),
    "unit": str(verdict["unit"]),
    "left_magnitude": _q(comparison.left.magnitude),
    "right_magnitude": _q(comparison.right.magnitude),
    "difference": _q(verdict["difference"]),
    "order": str(verdict["order"]),
    "word_order": str(verdict["word_order"]),
    "holds": str(verdict["holds"]),
    "same_class_disagree": str(audit["same_class"]["disagree"]),
    "cross_class_disagree": str(audit["cross_class"]["disagree"]),
    "cross_class_pairs": str(audit["cross_class"]["pairs"]),
}}

# The two magnitudes are recomputed from their brackets rather than trusted,
# and the verdict is re-derived from them rather than read back.
for _reading in (comparison.left, comparison.right):
    assert _reading.magnitude == (
        _reading.low + _reading.position * (_reading.high - _reading.low))
_order = ((comparison.left.magnitude > comparison.right.magnitude)
          - (comparison.left.magnitude < comparison.right.magnitude))
assert _order == verdict["order"]
assert verdict["holds"] == (
    _order == 0 if verdict["direction"] == "equal"
    else _order > 0 if verdict["direction"] == "greater" else _order < 0)
'''


def _body_report_measure(args) -> str:
    """Recompute the whole relative-measure study, fresh."""
    return '''# -- recompute -------------------------------------------------------------

from fractions import Fraction

from glm_universal.reasoning import denotation_view as dvw
from glm_universal.reasoning import measure_view as mvw


def _q(_x):
    _f = Fraction(_x)
    return str(_f.numerator) + "/" + str(_f.denominator)


report = mvw.measure_report()
denot = dvw.denotation_report()
denot_register = denot["register"]
denot_coverage = denot["coverage"]
denot_pass = denot["second_pass"]
denot_closure = denot["closure"]
register = report["register"]
widening = report["widening"]
views = {_v["name"]: _v for _v in widening["views"]}
boundary = widening["boundary"]
replacement = widening["non_cumulative"]
witness = report["replacement_witness"]
witness_replacement = witness["replacement"]
repair = report["relation_repair"]
sweep = report["basis_sweep"]
transport = report["transport"]
agreement = report["lexicon_agreement"]
examples = report["examples"]

observed = {
    "classes": str(register["classes"]),
    "quantities": ",".join(register["quantities"]),
    "scale_words": str(register["scale_words"]),
    "lexicon_agreement": str(agreement["agrees"]),
    "shared_words": str(agreement["shared_count"]),
    "scaled_words": str(report["scaled"]),
    "unscaled_words": str(report["unscaled"]),
    "uses": str(widening["uses"]),
    "static_resolution": str(views["static"]["resolution"]),
    "measure_resolution": str(views["measure"]["resolution"]),
    "measure_only_resolution": str(views["measure_only"]["resolution"]),
    "gained": str(boundary["gained"]),
    "violations": str(boundary["violations"]),
    "refines": str(boundary["refines"]),
    "replacement_refines": str(replacement["refines"]),
    "replacement_violations": str(replacement["violations"]),
    "witness_uses": str(witness["uses"]),
    "witness_replacement_violations": str(witness_replacement["violations"]),
    "witness_widening_violations": str(witness["widening"]["violations"]),
    "aliases": ",".join(_k + "=" + _v for _k, _v
                        in register["aliases"].items()),
    "aliases_sound": str(register["aliases_sound"]),
    "static_agreement": str(widening["static_agreement"]["agrees"]),
    "related_to": str(repair["related_to"]),
    "converted": str(repair["converted"]),
    "residue": str(repair["residue"]),
    "same_dimension_as": str(repair["by_predicate"].get(
        "same_dimension_as", 0)),
    "differs_by": str(repair["by_predicate"].get("differs_by", 0)),
    "residue_by_kind": ",".join(
        _k + ":" + str(_v) for _k, _v
        in sorted(repair["residue_by_kind"].items())),
    "residue_by_pos": ",".join(
        _k + ":" + str(_v) for _k, _v
        in sorted(repair["residue_by_pos"].items())),
    "denotations": str(denot_register["entries"]),
    "denotation_verdicts": ",".join(
        _k + ":" + str(_v) for _k, _v
        in denot_register["by_verdict"].items()),
    "denotation_sound": str(denot_register["audit"]["sound"]),
    "denotation_needed": str(denot_coverage["needed"]),
    "denotation_complete": str(denot_coverage["complete"]),
    "denotation_converted": str(denot_pass["converted"]),
    "denotation_decided": str(denot_pass["decided"]),
    "denotation_declined": str(denot_pass["declined"]),
    "denotation_closed": str(denot_closure["decided"]),
    "basis_size": str(sweep["basis_size"]),
    "basis_dimensions": str(sweep["basis_dimensions"]),
    "basis_sound": str(sweep["basis_sound"]),
    "basis_candidates": str(sweep["candidates"]),
    "basis_inert": str(sweep["inert"]),
    "basis_ambiguates": str(sweep["ambiguates"]),
    "basis_converts": str(sweep["converts"]),
    "basis_converting_dimensions": ",".join(
        str(_c["dimension"]) for _c in sweep["converting_classes"]),
    "basis_trimmed_converted": str(sweep["trimmed_counts"]["converted"]),
    "transport_cases": str(transport["cases"]),
    "transport_answered": str(transport["answered"]),
    "transport_control_answered": str(transport["control_answered"]),
    "hot_in_tea": _q(examples[0]["magnitude"]),
    "hot_in_stellar_surface": _q(examples[1]["magnitude"]),
    "refusal_reasons": ",".join(str(_r["reason"]) for _r in report["refusals"]),
}
'''


def _body_report_escalation(args) -> str:
    """Recompute the register-scale layer audit, fresh."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal.reasoning import escalation as esc


report = esc.escalation_report()
layers = {_l["name"]: _l for _l in report["layers"]}
boundaries = report["boundaries"]
ceiling = report["ceiling"]
agreement = report["key_agreement"]
raw = report["non_cumulative"]

observed = {
    "carriers": str(report["carrier_count"]),
    "registers": ",".join(report["registers"]),
    "substrate_resolution": str(layers["substrate"]["resolution"]),
    "integer_resolution": str(layers["integer"]["resolution"]),
    "rational_resolution": str(layers["rational"]["resolution"]),
    "griess_resolution": str(layers["griess"]["resolution"]),
    "universal_resolution": str(layers["universal"]["resolution"]),
    "integer_raw_resolution": str(raw["resolution"]),
    "gained_substrate_integer": str(boundaries[0]["gained"]),
    "gained_integer_rational": str(boundaries[1]["gained"]),
    "gained_rational_griess": str(boundaries[2]["gained"]),
    "gained_griess_universal": str(boundaries[3]["gained"]),
    "chain_intact": str(report["refinement_chain_intact"]),
    "distinct_carriers": str(ceiling["distinct_carriers"]),
    "unreachable": str(ceiling["unreachable"]),
    "collision_classes": str(ceiling["collision_classes"]),
    "cross_register_collisions": str(ceiling["cross_register"]),
    "largest_collision": str(ceiling["largest_class_size"]),
    "unreachable_by_register": ",".join(
        str(_r["register"]) + ":" + str(_r["unreachable"])
        for _r in report["by_register"]),
    "addition_descends": ",".join(
        _l["name"] for _l in report["layers"] if _l["addition_descends"]),
    "key_agreement": str(agreement["agrees"]),
    "key_pairs_checked": str(agreement["pairs_checked"]),
    "raw_refines_substrate": str(raw["refines_substrate"]),
    "raw_violations": str(raw["violations"]),
}
'''


def _body_report_names(args) -> str:
    """Recompute the name coordinate and the ceiling it lifts, fresh."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal.reasoning import name_coordinate as nco


report = nco.name_report()
before = report["before"]
exact = report["exact"]
prime = report["sweeps"]["prime_mod"]
low = report["sweeps"]["low_bits"]
controls = {_r["coordinate"]: _r for _r in report["controls"]}
sufficient = report["sufficient_bits"]

observed = {
    "entries": str(report["entries"]),
    "distinct_carriers": str(before["distinct_carriers"]),
    "unreachable_before": str(before["unreachable"]),
    "collision_classes": str(before["collision_classes"]),
    "largest_class": str(before["largest_class_size"]),
    "code_injective": str(report["code_injective_on_corpus"]),
    "distinct_names": str(report["distinct_names"]),
    "exact_distinct": str(exact["distinct"]),
    "exact_unreachable": str(exact["unreachable"]),
    "exact_recovered": str(exact["recovered"]),
    "substrate_resolution": str(report["substrate_resolution"]),
    "substrate_resolution_named": str(report["substrate_resolution_named"]),
    "prime_mod_sweep": ",".join(
        str(_r["bits"]) + ":" + str(_r["unreachable"]) for _r in prime),
    "low_bits_sweep": ",".join(
        str(_r["bits"]) + ":" + str(_r["unreachable"]) for _r in low),
    "sufficient_bits_prime_mod": str(sufficient["prime_mod"]),
    "sufficient_bits_low_bits": str(sufficient["low_bits"]),
    "low_bits_floor": str(min(_r["unreachable"] for _r in low)),
    "forced_bits": str(report["forced_bits"]),
    "control_recovered": ",".join(
        _k + ":" + str(report["control_recovered"][_k])
        for _k in nco.CONTROLS),
    "rows_checked": str(len(prime) + len(low) + len(controls) + 1),
    "violations": str(
        sum(_r["violations"] for _r in prime)
        + sum(_r["violations"] for _r in low)
        + sum(_r["violations"] for _r in controls.values())
        + exact["violations"]),
}
'''


def _body_derive(args) -> str:
    """Re-derive one coordinate of one object from its description, fresh."""
    coordinate = str(args.get("coordinate", ""))
    target = str(args.get("object", ""))
    domain = str(args.get("domain", ""))
    return f'''# -- recompute -------------------------------------------------------------

from fractions import Fraction

from glm_universal import recipe as rcp
from glm_universal.recipe import build as rbuild


def _q(_x):
    _f = Fraction(_x)
    return str(_f.numerator) + "/" + str(_f.denominator)


_coordinate = {coordinate!r}
_object = {target!r}
_domain = {domain!r}

_spec = rcp.description_by_name(_domain)
_answer = rcp.ask(_coordinate, _object, _domain)
assert _answer["answered"], _answer
_value = _answer["value"]

observed = {{
    "domain": str(_answer["domain"]),
    "coordinate": _coordinate,
    "object": _object,
    "value": (_q(_value) if isinstance(_value, Fraction) else str(_value)),
    "kind": str(_answer["kind"]),
    "rule": str(_answer["rule"]),
    "index": str(_spec.layout.index(_coordinate)),
}}

# The value is recomputed straight off the description's own rule, and the
# whole carrier is regenerated so the coordinate cannot disagree with it.
_facts = [_f for _f in _spec.facts() if str(_f["name"]) == _object][0]
assert _spec.coordinate(_coordinate).of(_facts) == _value
assert rbuild.carrier(_spec, _facts)[_spec.layout.index(_coordinate)] == _value

# And a coordinate the description does not derive is refused, not guessed.
for _absent in _spec.refuses:
    assert not rbuild.answer(_spec, _absent, _object)["answered"]
'''


def _body_report_language(args) -> str:
    """Recompute the question descriptions and the parser comparison."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal import language as lang

report = lang.language_report()
described = report["surface"]
agreed = report["agreement"]
trips = report["round_trip"]
refusals = report["refusals"]
disjoint = report["disjoint"]
narrowing = report["narrowing"]
infix = report["infix"]
infix_agreed = report["infix_agreement"]
parts = report["undescribed_parts"]
verdict = report["verdict"]

observed = {
    "kinds": ",".join(described["kinds"]),
    "judgements": str(described["judgements"]),
    "phrasings": str(described["phrasings"]),
    "slots": str(described["slots"]),
    "preamble_forms": str(described["preamble_forms"]),
    "corpus": str(agreed["corpus"]),
    "agreed": str(agreed["agreed"]),
    "disagreed": str(len(agreed["disagreed"])),
    "outside": str(agreed["outside"]),
    "false_positives": str(len(agreed["false_positives"])),
    "round_trips": str(trips["checked"]),
    "openings": str(disjoint["openings"]),
    "openings_disjoint": str(disjoint["disjoint"]),
    "witnesses": str(len(refusals["witnesses"])),
    "narrowing_witnesses": str(len(narrowing["witnesses"])),
    "narrowing_misread": str(narrowing["misread_by_the_parser"]),
    "infix_kinds": ",".join(infix["kinds"]),
    "infix_judgements": str(infix["judgements"]),
    "infix_corpus": str(infix_agreed["corpus"]),
    "infix_agreed": str(infix_agreed["agreed"]),
    "infix_disagreed": str(len(infix_agreed["disagreed"])),
    "undescribed_parts": str(len(parts)),
    "kinds_read_off": str(verdict["kinds_read_off"]),
    "kinds_covered": str(verdict["kinds_covered"]),
    "shape_families": str(verdict["shape_families"]),
    "verdict": str(verdict["verdict"]),
}

# The comparison has two halves, and neither is against a stored
# expectation.  First: the shipped parser now *reads* the descriptions for
# these kinds, so the standing claim is against the branches it used to
# have -- kept frozen in `language.legacy` -- and every question of the
# generated corpus is put to the frozen branch and to the live parser.
from glm_universal.runtime.parser import parse_query

for _kind, _question, _fills in lang.corpus():
    _mine = lang.parse(_question)
    _live = parse_query(_question)
    _old = lang.legacy_parse(_question)
    assert _mine.matched, (_question, _mine.boundary)
    assert _mine.kind == _live.kind == _kind, (_question, _mine.kind)
    assert _old is not None and _old[0] == _kind, (_question, _old)
    for _key, _value in lang.options_of(_mine).items():
        assert _live.options.get(_key) == _value, (_question, _key)
        assert str(_old[1].get(_key, "")) == _value, (_question, _key)

# Second: the branches really are gone from the parser, and nothing the
# runtime loads reaches the frozen copy.
import inspect
import glm_universal.runtime.parser as _parser

_src = inspect.getsource(_parser)
for _kind in lang.DESCRIBED_KINDS:
    assert 'kind == "' + _kind + '"' not in _src, _kind
assert "language.legacy" not in _src and "import legacy" not in _src

# And the second family, which has not replaced anything yet: its matcher
# against the parser branch it describes, over its own generated corpus.
for _kind, _question, _operands in lang.infix_corpus():
    _got = lang.parse_infix(_question, lang.INFIX_QUESTIONS)
    _live = parse_query(_question)
    assert getattr(_got, "matched", False), (_question, _kind)
    assert _got.kind == _live.kind == _kind, (_question, _got.kind)
'''


def _body_report_recipe(args) -> str:
    """Recompute the descriptions, the generic path and the regeneration."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal import recipe as rcp

report = rcp.recipe_report()
shared = report["shared"]
verdict = report["verdict"]

observed = {
    "domains": ",".join(shared["domains"]),
    "coordinates": str(shared["coordinates"]),
    "derivations": str(shared["derivations"]),
    "judgements": str(shared["judgements"]),
    "primitives_used": str(len(shared["primitives_used"])),
    "carriers_compared": str(verdict["carriers_compared"]),
    "carriers_identical": str(verdict["carriers_identical"]),
    "domains_regenerated": str(verdict["domains_regenerated"]),
    "chains_intact": str(verdict["chains_intact"]),
    "all_lossless": str(verdict["all_lossless"]),
    "figures_unchanged": str(verdict["figures_unchanged"]),
    "verdict": str(verdict["verdict"]),
}

for _entry in report["domains"]:
    observed[_entry["domain"] + "_judgements"] = str(_entry["judgement_count"])
    observed[_entry["domain"] + "_carriers"] = str(_entry["carriers_identical"])
'''


def _body_report_harmony(args) -> str:
    """Recompute the harmonic register and the harmony verdict, fresh."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal.reasoning import harmony as hy


def _q(value):
    from fractions import Fraction
    f = Fraction(value)
    return str(f.numerator) + "/" + str(f.denominator)


report = hy.harmony_report()
register = report["register"]
temperament = report["temperament"]
closure = report["closure"]
consonance = report["consonance"]
lattice = report["lattice"]
control = lattice["control"]
verdict = report["verdict"]

observed = {
    "intervals": str(register["count"]),
    "just": str(register["just"]),
    "septimal": str(register["septimal"]),
    "commas": str(register["commas"]),
    "tempered_exactly": ",".join(temperament["tempered_exactly"]),
    "fifth_error": _q(temperament["fifth_error"]),
    "third_error": _q(temperament["third_error"]),
    "closures": ",".join(str(_n) for _n in closure["closures"]),
    "pythagorean_comma": _q(closure["twelve_fifths_over_seven_octaves"]),
    "syntonic_comma": _q(closure["four_fifths_over_major_third"]),
    "consonance_tau": _q(consonance["tau"]),
    "best_scale": str(lattice["best_scale"]),
    "best_distinct": str(lattice["best_distinct"]),
    "best_tau_tenney": _q(lattice["best_tau_tenney"]),
    "best_tau_gradus": _q(lattice["best_tau_gradus"]),
    "control_tau_tenney": _q(control["tau_tenney"]),
    "reordered_pairs": str(lattice["best_reordered_pairs"]),
    "beats_control": str(lattice["beats_control"]),
    "verdict": verdict["verdict"],
}
'''


def _body_report_economics(args) -> str:
    """Recompute the economic register and its verdict, fresh."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal.reasoning import economics as ecn


def _q(value):
    from fractions import Fraction
    f = Fraction(value)
    return str(f.numerator) + "/" + str(f.denominator)


report = ecn.economics_report()
register = report["register"]
lattice = report["lattice"]
control = lattice["control"]
best = lattice["best_comovement"]
control_co = control["comovement"]
verdict = report["verdict"]

observed = {
    "records": str(register["records"]),
    "instruments": str(register["instruments"]),
    "windows": str(register["windows"]),
    "currency_pairs": str(register["currency_pairs"]),
    "all_bounds_hold": str(register["all_bounds_hold"]),
    "base_2_bucket_span": str(register["base_2_bucket_span"]),
    "best_scale": str(lattice["best_scale"]),
    "best_distinct": str(lattice["best_distinct"]),
    "fully_separated": ",".join(str(_s)
                                for _s in lattice["fully_separated"]),
    "best_tau_magnitude": _q(lattice["best_tau_magnitude"]),
    "comovement": _q(best["rate"]),
    "chance_rate": _q(ecn.CHANCE_SAME_INSTRUMENT),
    "control_comovement": _q(control_co["rate"]),
    "control_tau_magnitude": _q(control["tau_magnitude"]),
    "beats_control": str(lattice["beats_control"]),
    "verdict": verdict["verdict"],
}
'''


def _body_real(args: Mapping[str, object]) -> str:
    """Recompute a real value as a process, in a fresh interpreter (v1.2.0)."""
    notation = str(args.get("notation", "sqrt(2)"))
    places = int(args.get("places", 20))          # type: ignore[arg-type]
    levels = int(args.get("levels", 6))           # type: ignore[arg-type]
    ticks = int(args.get("ticks", 512))           # type: ignore[arg-type]
    return f'''# -- recompute -------------------------------------------------------------

from fractions import Fraction

from glm_universal.reasoning import exact_real as xr

_value = xr.parse_real({notation!r})
_stand_ins = xr.surrogate_sequence(_value, {levels})
_exposed = []
for _level in range({levels} - 1):
    _found = None
    for _higher in range(_level, _level + 12):
        if xr.surrogate(_value, _higher) != xr.rational_surrogate(
                _stand_ins[_level], _higher):
            _found = _higher
            break
    _exposed.append(str(_level) + "->" + (str(_found) if _found is not None
                                          else "never"))

_at = _value.at(64)
_fractional = _at - (_at.numerator // _at.denominator)
_average = xr.delta_sigma_average(_fractional, {ticks})
_error = abs(_average - _fractional)

observed = {{
    "notation": {notation!r},
    "places": str({places}),
    "decimal": _value.decimal({places}),
    "rational": str(_value.exact is not None),
    "stand_ins": str([str(_s) for _s in _stand_ins]),
    "exposed": str(_exposed),
    "delta_sigma_ticks": str({ticks}),
    "delta_sigma_average": str(_average),
    "delta_sigma_within_bound": str(_error <= Fraction(1, {ticks})),
}}
'''


def _body_compare(args: Mapping[str, object]) -> str:
    """Re-decide the order of two written real values (v1.2.0)."""
    left = str(args.get("left", "sqrt(2)"))
    right = str(args.get("right", "7/5"))
    relation = str(args.get("relation", "compare"))
    ladder = list(args.get("ladder", [8, 16, 32, 64, 128, 256]))  # type: ignore[arg-type]
    return f'''# -- recompute -------------------------------------------------------------

from glm_universal.reasoning import exact_real as xr

_left = xr.parse_real({left!r})
_right = xr.parse_real({right!r})
_ladder = {ladder!r}

_order, _settled = 0, None
for _precision in _ladder:
    _order = xr.compare(_left, _right, _precision)
    if _order != 0:
        _settled = _precision
        break

_relation = {relation!r}
if _order == 0:
    _verdict = "undecided"
elif _relation == "greater":
    _verdict = str(_order > 0)
elif _relation == "less":
    _verdict = str(_order < 0)
elif _relation == "equal":
    _verdict = "False"
else:
    _verdict = "{{}} {{}} {{}}".format(
        {left!r}, ">" if _order > 0 else "<", {right!r})

observed = {{
    "left": {left!r},
    "right": {right!r},
    "relation": _relation,
    "order": str(_order),
    "settled_at": str(_settled),
    "verdict": _verdict,
    "left_decimal": _left.decimal(20),
    "right_decimal": _right.decimal(20),
}}
'''


def _body_report_infinite_values(args: Mapping[str, object]) -> str:
    """Recompute the infinite-values report from the public API (v1.2.0)."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal.reasoning import exact_real as xr

report = xr.exact_real_report()

observed = {
    "sqrt2_decimal_20": report["sqrt2_decimal_20"],
    "pi_decimal_20": report["pi_decimal_20"],
    "e_decimal_20": report["e_decimal_20"],
    "phi_decimal_20": report["phi_decimal_20"],
    "delta_sigma_law_holds": str(report["delta_sigma_law_holds"]),
    "delta_sigma_deterministic": str(report["delta_sigma_deterministic"]),
    "no_stand_in_is_the_target": str(report["no_stand_in_is_the_target"]),
    "golay_reachable_deviation": str(report["golay_reachable_deviation"]),
    "golay_within_one_over_n": str(report["golay_within_one_over_n"]),
    "golay_unreachable_certified": str(report["golay_unreachable_certified"]),
    "equality_undecided": str(report["equality_undecided"]),
    "inequality_decided": str(report["inequality_decided"]),
}
'''


def _body_report_capabilities(args: Mapping[str, object]) -> str:
    """Re-run every capability probe in a fresh interpreter (v1.2.0)."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal import capabilities as cap

report = cap.capability_report()

observed = {
    "probes": str(report["probes"]),
    "holds": str(report["holds"]),
    "breaks": str(report["breaks"]),
    "errors": str(report["errors"]),
    "surprises": str(report["surprises"]),
}
for _result in report["results"]:
    observed["verdict_" + _result["name"]] = str(_result["verdict"])
'''


def _body_meaning(args: Mapping[str, object]) -> str:
    """Re-resolve notations and re-derive their relations (v1.1.0)."""
    terms = [str(t) for t in args.get("terms", ())]      # type: ignore[arg-type]
    return f'''# -- recompute -------------------------------------------------------------

from fractions import Fraction

from glm_universal.semantics import meaning as sme
from glm_universal.semantics import reference as sre
from glm_universal.semantics import relations as srl

_terms = {terms!r}
_answers = [sre.resolve(_term) for _term in _terms]

observed = {{"terms": str(list(_terms))}}
for _a in _answers:
    observed["grounded_" + _a.term] = str(_a.grounded)
    if _a.meaning is not None:
        observed["meaning_" + _a.term] = _a.meaning.describe()
        observed["carrier_" + _a.term] = str(
            [str(Fraction(_c).numerator) + "/" + str(Fraction(_c).denominator)
             for _c in sme.encode(_a.meaning)])

_grounded = [_a for _a in _answers if _a.meaning is not None]
if _grounded:
    observed["all_round_trips_hold"] = str(all(
        sme.decode(sme.encode(_a.meaning)) == _a.meaning for _a in _grounded))

if len(_grounded) == 2:
    _first, _second = _grounded[0].meaning, _grounded[1].meaning
    _claims = srl.derive(_first, _second) + srl.derive(_second, _first)
    observed["same_meaning"] = str(_first == _second)
    observed["relations"] = str(sorted({{_c.relation for _c in _claims}}))
    observed["relation_count"] = str(len(_claims))
    observed["all_claims_reverify"] = str(
        all(srl.verify(_c) for _c in _claims))
'''


def _body_report_semantics(args: Mapping[str, object]) -> str:
    """Re-run the whole semantic audit of the inherited graph (v1.1.0)."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal.semantics import audit as sau

report = sau.audit_report()
concepts = report["concept_grounding"]
edges = report["edge_grounding"]
carriers = report["carrier_information"]
variants = report["notational_variants"]
plan = report["purge_plan"]
replacement = report["replacement"]
classes = edges["classes"]

observed = {
    "legacy_concepts": str(concepts["concepts"]),
    "legacy_concepts_grounded": str(concepts["grounded"]),
    "legacy_edges": str(edges["edges"]),
    "edges_proximity_artefact": str(classes.get("proximity_artefact", 0)),
    "edges_endpoint_ungrounded": str(classes.get("endpoint_ungrounded", 0)),
    "edges_derivable": str(classes.get("derivable", 0)),
    "edges_retained": str(plan["retained"]),
    "edges_dumped": str(plan["dumped"]),
    "mean_hamming_related": str(carriers["mean_hamming_related"]),
    "mean_hamming_unrelated": str(carriers["mean_hamming_unrelated"]),
    "synonym_pairs": str(variants["synonym_pairs"]),
    "mean_legacy_hamming_between_synonyms": str(
        variants["mean_legacy_hamming_between_synonyms"]),
    "grounded_meanings": str(replacement["meanings"]),
    "grounded_notations": str(replacement["notations"]),
    "grounded_binary_edges": str(replacement["binary_edges"]),
    "grounded_ternary_edges": str(replacement["ternary_edges"]),
    "all_edges_reverified": str(replacement["all_edges_reverified"]),
}
'''


def _body_report_fusion(args: Mapping[str, object]) -> str:
    """Recompute the Ising fusion structure of the 2A algebra (v0.9.0)."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal.reasoning import product as pr

report = pr.fusion_report()

observed = {
    "pairs_checked": str(report["pairs_checked"]),
    "axes_checked": str(report["axes_checked"]),
    "all_eigenspaces_span": str(report["all_eigenspaces_span"]),
    "all_dimensions_as_predicted": str(report["all_dimensions_as_predicted"]),
    "all_adjoint_traces_five_quarters": str(
        report["all_adjoint_traces_five_quarters"]),
    "tau_always_identity": str(report["tau_always_identity"]),
    "sigma_always_swaps": str(report["sigma_always_swaps"]),
    "all_automorphisms": str(report["all_automorphisms"]),
    "all_isometries": str(report["all_isometries"]),
    "all_involutions": str(report["all_involutions"]),
}
'''


def _body_report_benchmarks(args: Mapping[str, object]) -> str:
    """Re-run every benchmark suite in a fresh interpreter (v1.0.0)."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal import benchmarks as bm

report = bm.benchmark_report()

observed = {
    "suite_count": str(report["suite_count"]),
    "task_count": str(report["task_count"]),
    "passed_count": str(report["passed_count"]),
    "overall_score": str(report["overall_score"]),
    "run_id": str(report["run_id"]),
    "null_result_count": str(len(report["null_results"])),
}
for _suite in report["suites"]:
    _name = _suite["name"]
    observed["score_" + _name] = str(_suite["score"])
    observed["baseline_" + _name] = str(_suite["baseline"])
    observed["verdict_" + _name] = str(_suite["verdict"])
'''


def _body_report_golay_decoding(args: Mapping[str, object]) -> str:
    """Recompute the complete Golay decoder's census (v0.8.0)."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal.substrate import golay_decode as gdc

report = gdc.golay_decode_report()
census = report["coset_census"]
steiner = report["steiner"]
weight5 = report["weight5"]

observed = {
    "cosets": str(census["cosets"]),
    "total_leaders": str(census["total_leaders"]),
    "unique_below_radius_4": str(census["unique_below_radius_4"]),
    "sextet_at_radius_4": str(census["sextet_at_radius_4"]),
    "packing_radius": str(report["packing_radius"]),
    "covering_radius": str(report["covering_radius"]),
    "codewords": str(report["codewords"]),
    "octads": str(steiner["octads"]),
    "is_steiner_5_8_24": str(steiner["is_steiner_5_8_24"]),
    "weight5_always_coset_weight_3": str(weight5["always_coset_weight_3"]),
    "weight5_always_miscorrected": str(weight5["always_miscorrected"]),
    "silent_tie_breaking_retired": str(report["silent_tie_breaking_retired"]),
}
'''


def _body_report_transform_decoder(args: Mapping[str, object]) -> str:
    """Recompute the transform-driven decoder and its certificate (v1.4.0)."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal.reasoning import fwht_decode as fdc

report = fdc.fwht_decode_report()
counts = report["operation_counts"]
rates = report["certificate_rates"]
agree = report["agreement"]
ties = report["tie_sets"]

observed = {
    "direct_adds": str(counts["direct_adds"]),
    "fwht_ops": str(counts["fwht_ops"]),
    "equal_because_n_equals_2k": str(counts["equal_because_n_equals_2k"]),
    "column_identity_failures": str(agree["column_identity_failures"]),
    "support_sums_failures": str(agree["support_sums_failures"]),
    "lattice_point_failures": str(agree["lattice_point_failures"]),
    "all_agree": str(agree["all_agree"]),
    "tie_set_failures": str(ties["failures"]),
    "sextet_case_is_sixfold": str(ties["sextet_case_is_sixfold"]),
    "flat_profile_always_certifies":
        str(rates["flat_profile_always_certifies"]),
    "certified_but_wrong": str(rates["certified_but_wrong"]),
    "overall_certified_fraction": str(rates["overall_certified_fraction"]),
}
'''


def _body_report_units(args: Mapping[str, object]) -> str:
    """Recompute the unit-string audit and the steradian case (v1.5.0)."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal.reasoning import units as un

report = un.units_report()
audit = report["audit"]
case = report["steradian"]

observed = {
    "quantities": str(audit["quantities"]),
    "every_unit_readable": str(audit["every_unit_readable"]),
    "every_unit_agrees": str(audit["every_unit_agrees"]),
    "mismatched_count": str(audit["mismatched_count"]),
    "broken_by_dropping_the_steradian": str(case["broken_count"]),
    "photometric_count": str(case["photometric_count"]),
}
'''


def _body_report_deep_holes(args: Mapping[str, object]) -> str:
    """Recompute the deep-hole census reached by walking (v1.5.0)."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal.reasoning import deep_holes as dhl

report = dhl.deep_holes_report(walks=3)
census = report["census"]

observed = {
    "catalogue_size": str(report["catalogue_size"]),
    "covering_radius2": str(report["covering_radius2"]),
    "walks_run": str(census["walks_run"]),
    "every_named_type_certified":
        str(census["every_named_type_certified"]),
    "census_complete": str(census["census_complete"]),
}
'''


def _body_report_molecules(args: Mapping[str, object]) -> str:
    """Recompute the molecules register from name and formula alone (v1.4.0)."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal.data_objects import molecules as mol

report = mol.molecules_report()
collisions = report["collisions"]
heaviest_name, heaviest_mass = report["largest_by_mass"]

observed = {
    "molecules": str(report["molecules"]),
    "coordinates": str(report["coordinates"]),
    "derived_fields": str(report["derived_fields"]),
    "distinct_elements_used": str(report["distinct_elements_used"]),
    "bundle_is_faithful": str(collisions["bundle_is_faithful"]),
    "distinct_composites": str(collisions["distinct_composites"]),
    "composite_collision_count":
        str(collisions["composite_collision_count"]),
    "bundle_collision_count": str(collisions["bundle_collision_count"]),
    "missing_by_field": str(dict(report["missing_by_field"])),
    "largest_by_mass": heaviest_name + "=" + q(heaviest_mass),
}
'''


def _body_report_chemistry_coverage(args: Mapping[str, object]) -> str:
    """Recompute the three honest widenings of the element register (v1.4.0)."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal.reasoning import element_coverage as eco

report = eco.element_coverage_report()
coverage = report["coverage"]
derived = report["derived"]
estimates = report["estimates"]
model = estimates["model"]
cross = report["cross_check"]

observed = {
    "elements": str(coverage["elements"]),
    "total_cells": str(coverage["total_cells"]),
    "filled_cells": str(coverage["filled_cells"]),
    "sparsest": str(coverage["sparsest"]),
    "derived_attribute_count": str(derived["attribute_count"]),
    "derived_new_cells": str(derived["new_cells"]),
    "fitted_on": str(model["fitted_on"]),
    "slope": q(model["slope"]),
    "intercept_pm": q(model["intercept_pm"]),
    "mean_absolute_residual_pm": q(model["mean_absolute_residual_pm"]),
    "estimate_count": str(estimates["estimate_count"]),
    "measured_count": str(estimates["measured_count"]),
    "coverage_before": str(estimates["coverage_before"]),
    "coverage_after": str(estimates["coverage_after"]),
    "cross_check_compared": str(cross["compared"]),
    "cross_check_agree_within_20": str(cross["agree_within_20_count"]),
    "largest_difference_element":
        str(cross["largest_difference"]["element"]),
}
'''


def _body_report_blueprint(args: Mapping[str, object]) -> str:
    """Recompute the unification-blueprint claim ledger (v5.2.0)."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal.reasoning import blueprint as bp

report = bp.blueprint_report()
tally = report["tally"]
audit = report["source_audit"]
rate = report["delta_sigma_rate"]

observed = {
    "claim_count": str(report["claim_count"]),
    "confirmed": str(tally[bp.CONFIRMED]),
    "refuted": str(tally[bp.REFUTED]),
    "not_reproduced": str(tally[bp.NOT_REPRODUCED]),
    "not_implemented": str(tally[bp.NOT_IMPLEMENTED]),
    "sections": ",".join(sorted(report["sections"])),
    "core_modules": str(audit["core_modules"]),
    "core_clean": str(audit["core_clean"]),
    "outside_core_violations": str(len(audit["outside_core_violations"])),
    "rate_rows": str(rate["row_count"]),
    "all_within_one_over_n": str(rate["all_within_one_over_n"]),
}
for _index, _entry in enumerate(report["claims"]):
    observed["verdict_" + str(_index)] = str(_entry["verdict"])
    observed["section_" + str(_index)] = str(_entry["section"])
'''


def _body_report_signature(args: Mapping[str, object]) -> str:
    """Recompute the spectral signature table (v5.3.0)."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal.reasoning import wobble as wbl

report = wbl.wobble_report()
table = report["signatures"]
lock = report["resonance"]
scan = report["resonance_q_scan"]

observed = {
    "targets": str(report["targets"]),
    "steps": str(report["steps"]),
    "all_laws_hold": str(report["all_laws_hold"]),
    "max_entropy_density": q(report["max_entropy_density"]),
    "resonance_locked": str(lock["all_ones_after_the_first"]),
    "resonant_entropy": q(lock["resonant_entropy"]),
    "scan_hits": str(len(scan["hits"])),
    "scan_points": str(scan["points"]),
    "scan_best_q": q(scan["best_q"]),
    "scan_best_low": str(scan["best_low_entropy"]),
    "scan_best_high": str(scan["best_high_entropy"]),
}
for _row in table:
    _key = str(_row["name"]).replace(" ", "_")
    observed["entropy_" + _key] = str(_row["entropy_rounded"])
    observed["ones_" + _key] = str(_row["ones"])
    observed["zero_run_" + _key] = str(_row["longest_zero_run"])
    observed["one_run_" + _key] = str(_row["longest_one_run"])
for _row in report["oscillator"]:
    _key = str(_row["condition"]).replace(" ", "_")
    observed["oscillator_" + _key] = str(_row["entropy_rounded"])
for _row in report["resonance_sweep"]:
    observed["sweep_" + q(_row["ratio"])] = str(_row["entropy_rounded"])
'''


def _body_report_drift(args: Mapping[str, object]) -> str:
    """Recompute the prime-iteration drift table (v5.3.0)."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal.reasoning import drift as dft

report = dft.drift_report()

observed = {
    "steps": str(report["steps"]),
    "rows": str(len(report["table"])),
    "contractive_under_ceiling": str(
        report["contractive_stays_under_its_ceiling"]),
    "truncation_never_helps": str(report["truncation_never_helps"]),
    "display_diverges_by_step_two": str(
        report["display_diverges_by_step_two"]),
    "lossless_onset_at_three": str(report["lossless_onset_at_three"]),
    "onset_exceptions": str(len(report["display_onset_exceptions"])),
}
for _row in report["table"]:
    _key = str(_row["prime"]) + "_" + str(_row["rule"])
    observed["exact_" + _key] = str(_row["exact_final_sci"])
    observed["lossless_" + _key] = str(_row["lossless_drift_sci"])
    observed["display6_" + _key] = str(_row["display6_drift_sci"])
    observed["display4_" + _key] = str(_row["display4_drift_sci"])
'''


def _body_report_catalog(args: Mapping[str, object]) -> str:
    """Recompute the external-study claim ledger (v5.3.0)."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal.reasoning import catalog as cat

report = cat.catalog_report()
tally = report["tally"]

observed = {
    "claim_count": str(report["claim_count"]),
    "sections": str(report["sections"]),
    "section_labels": ",".join(report["section_labels"]),
    "confirmed": str(tally[cat.CONFIRMED]),
    "refuted": str(tally[cat.REFUTED]),
    "not_reproduced": str(tally[cat.NOT_REPRODUCED]),
    "not_implemented": str(tally[cat.NOT_IMPLEMENTED]),
}
for _index, _entry in enumerate(report["claims"]):
    observed["verdict_" + str(_index)] = str(_entry["verdict"])
    observed["section_" + str(_index)] = str(_entry["section"])
'''


def _body_report_containers(args: Mapping[str, object]) -> str:
    """Recompute the three containers of the eight constants (v5.5.0)."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal.reasoning import containers as con
from glm_universal.reasoning import wobble as wbl

report = con.containers_report()
scales = report["critical_scales"]


def _steps(name):
    row = next(r for r in report["convergence"] if r["name"] == name)
    return ", ".join(
        "never" if row["steps_to"][t] is None else str(row["steps_to"][t])
        for t in con.PRECISION_THRESHOLDS)


observed = {
    "constants": ",".join(report["constants"]),
    "laws_hold": str(report["laws_hold"]),
    "rigid_period": str(report["rigid_period"]),
    "hull_decided": str(report["hull_decided"]),
    "hull_inside": ",".join(report["hull_inside"]),
    "hull_outside": ",".join(report["hull_outside"]),
    "hull_undetermined": ",".join(report["hull_undetermined"]),
    "unit_support": str(scales["unit_support"]),
    "outside_above": wbl.round_str(scales["outside_above"], 6),
    "inside_at_most": wbl.round_str(scales["inside_at_most"], 6),
}
for _row in report["convergence"]:
    observed["steps_" + str(_row["name"])] = _steps(str(_row["name"]))
'''


def _body_report_companion(args: Mapping[str, object]) -> str:
    """Recompute the companion-studies claim ledger (v5.5.0)."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal.reasoning import companion as cpn

report = cpn.companion_report()
tally = report["tally"]

observed = {
    "claim_count": str(report["claim_count"]),
    "sections": ",".join(report["sections"]),
    "confirmed": str(tally[cpn.CONFIRMED]),
    "refuted": str(tally[cpn.REFUTED]),
    "not_reproduced": str(tally[cpn.NOT_REPRODUCED]),
    "not_implemented": str(tally[cpn.NOT_IMPLEMENTED]),
    "claims_by_study": ",".join(
        str(_prefix) + ":" + str(_count)
        for _prefix, _count in report["claims_by_study"].items()),
}
for _index, _entry in enumerate(report["claims"]):
    observed["verdict_" + str(_index)] = str(_entry["verdict"])
    observed["section_" + str(_index)] = str(_entry["section"])
'''


def _body_report_reversible(args: Mapping[str, object]) -> str:
    """Recompute the reversible bit-dynamics audit (v5.2.0)."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal.reasoning import reversible as rv

report = rv.reversible_report()
channel = report["channel"]
gates = report["gates"]
solitons = report["solitons"]

observed = {
    "width": str(channel["width"]),
    "steps": str(channel["steps"]),
    "gray_flips": str(channel["gray"]["flips"]),
    "gray_max_step": str(channel["gray"]["max_step"]),
    "gray_variance": q(channel["gray"]["variance"]),
    "binary_flips": str(channel["binary"]["flips"]),
    "gray_tax": q(channel["gray"]["tax"]),
    "binary_tax": q(channel["binary"]["tax"]),
    "halving_exact": str(channel["halving_exact"]),
    "gates_involutive": str(gates["gates_involutive"]),
    "gates_bijective": str(gates["gates_bijective"]),
    "gate_applications": str(gates["gate_applications"]),
    "hamming_to_start": str(gates["hamming_to_start"]),
    "exact_return": str(gates["exact_return"]),
    "syndrome_conserved": str(gates["syndrome_conserved"]),
    "kinks": str(solitons["kinks"]),
    "rotation_invariant": str(solitons["rotation_invariant"]),
    "kink_count_always_even": str(solitons["kink_count_always_even"]),
    "delta_always_two": str(solitons["delta_always_two"]),
    "claim_count": str(report["claim_count"]),
    "confirmed": str(report["confirmed"]),
    "refuted": str(report["refuted"]),
}
'''


def _body_report_mantissa(args: Mapping[str, object]) -> str:
    """Recompute the PTB/AOO mantissa metrology (v5.2.0)."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal.reasoning import mantissa as mn

report = mn.mantissa_report()
rounding = report["rounding"]
drift = report["drift"]

observed = {
    "precision": str(report["precision"]),
    "primes": ",".join(str(p) for p in report["primes"]),
    "min_retained_bits": str(rounding["min_retained_bits"]),
    "bits_lost_at_step_zero": str(rounding["bits_lost_at_step_zero"]),
    "max_significand_hamming": str(rounding["max_significand_hamming"]),
    "every_prime_repeats": str(rounding["every_prime_repeats"]),
    "periods": ",".join(str(row["period"]) for row in rounding["rows"]),
    "all_collapse": str(drift["all_collapse"]),
    "all_collapse_within_bound": str(drift["all_collapse_within_bound"]),
    "max_distance_before_collapse":
        str(drift["max_distance_before_collapse"]),
    "any_antipodal_before_collapse":
        str(drift["any_antipodal_before_collapse"]),
    "claim_count": str(report["claim_count"]),
    "confirmed": str(report["confirmed"]),
    "refuted": str(report["refuted"]),
}
for _row in drift["rows"]:
    _p = str(_row["prime"])
    observed["collapse_step_" + _p] = str(_row["collapse_step"])
    observed["exact_terminates_" + _p] = str(_row["exact_orbit_terminates"])
'''


def _body_report_engine(args: Mapping[str, object]) -> str:
    """Recompute the thermo-dynamic carrier engine (v5.2.0)."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal.reasoning import engine as eng

report = eng.engine_report()
runs = report["runs"]
fuel = report["multi_fuel"]
leap = report["precision_leap"]
strain = report["strain_readings"]

observed = {
    "ticks": str(report["ticks"]),
    "escapement_period": str(eng.escapement_period()),
    "plain_error": str(runs["plain"]["error"]),
    "plain_tax": str(runs["plain"]["accumulated_tax"]),
    "plain_escalations": str(runs["plain"]["escalations"]),
    "cooled_tax": str(runs["cooled"]["accumulated_tax"]),
    "cooled_escalations": str(runs["cooled"]["escalations"]),
    "radiator_bleeds": str(report["radiator_bleeds"]),
    "radiator_lowers_final_strain": str(
        report["radiator_lowers_final_strain"]),
    "turbo_snaps_avoided": str(report["turbo_snaps_avoided"]),
    "turbo_saves_operations": str(report["turbo_saves_operations"]),
    "strain_readings_agree": str(strain["agree"]),
    "tight_tax": str(strain["tight"]["tax"]),
    "relaxed_tax": str(strain["relaxed"]["tax"]),
    "heron_tick": str(fuel["heron_tick"]),
    "convergent_tick": str(fuel["convergent_tick"]),
    "switched_tick": str(fuel["switched_tick"]),
    "fuel_speedup": q(fuel["speedup_over_slower"]),
    "claimed_ratio": str(leap["claimed_ratio"]),
    "claimed_ratio_matched": str(
        leap["any_baseline_gives_the_claimed_ratio"]),
}
'''


def _body_report_superposition(args: Mapping[str, object]) -> str:
    """Recompute the parallel-hypothesis study (v1.3.0)."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal.substrate import superposition as sup

report = sup.superposition_report()
sextet = report["sextet"]
bundling = report["bundling"]
collapse = report["collapse"]
census = report["census"]
chain = report["chain"]
hull = report["hull"]

observed = {
    "tie_count": str(report["tie_count"]),
    "pairwise_disjoint": str(sextet["pairwise_disjoint"]),
    "covers_all_24": str(sextet["covers_all_24"]),
    "f2_bundle_is_all_ones": str(bundling["f2_bundle_is_all_ones"]),
    "f2_bundle_distinguishes": str(bundling["f2_bundle_distinguishes"]),
    "rational_bundle_recovers_input":
        str(bundling["rational_bundle_recovers_input"]),
    "rational_bundle_distinguishes":
        str(bundling["rational_bundle_distinguishes"]),
    "collapse_status": str(collapse["collapsed"]["status"]),
    "refuted_status": str(collapse["refuted"]["status"]),
    "cosets": str(census["cosets"]),
    "cosets_by_distance": str(census["cosets_by_distance"]),
    "mean_coset_weight": str(census["mean_coset_weight"]),
    "uniquely_read_cosets": str(census["uniquely_read_cosets"]),
    "ambiguous_cosets": str(census["ambiguous_cosets"]),
    "ambiguous_fraction": str(census["ambiguous_fraction"]),
    "mean_exceeds_packing_radius":
        str(census["mean_exceeds_packing_radius"]),
    "mean_below_covering_radius": str(census["mean_below_covering_radius"]),
    "census_agrees_with_lean": str(census["census_agrees_with_lean"]),
    "mean_agrees_with_lean": str(census["mean_agrees_with_lean"]),
    "chain_states": str(chain["states"]),
    "columns_all_odd_parity": str(chain["columns_all_odd_parity"]),
    "uniform_is_stationary": str(chain["uniform_is_stationary"]),
    "parity_alternates": str(chain["parity_alternates"]),
    "law_never_uniform": str(chain["law_never_uniform"]),
    "settles_in_distribution": str(chain["settles_in_distribution"]),
    "two_step_average_mean_distance":
        str(chain["two_step_average_mean_distance"]),
    "two_step_average_error": str(chain["two_step_average_error"]),
    "corrected_carrier_returns_to_code":
        str(chain["corrected_carrier_returns_to_code"]),
    "corrected_distance_after_correction":
        str(chain["corrected_distance_after_correction"]),
    "codewords_checked": str(hull["codewords_checked"]),
    "max_over_scaled_codewords": str(hull["max_over_scaled_codewords"]),
    "value_at_target": str(hull["value_at_target"]),
    "leech_cycle_reaches_target": str(hull["leech_cycle_reaches_target"]),
}
'''


def _body_report_leech_construction(args: Mapping[str, object]) -> str:
    """Recompute the Construction A/B/C ladder (v0.8.0)."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal.substrate import leech_construct as lcs

report = lcs.leech_construction_report()
kissing = report["kissing_by_level"]
norms = report["minimal_norm_by_level"]
necessity = report["necessity"]
agreement = report["agreement_with_leech2"]

observed = {
    "kissing_A": str(kissing["A"]),
    "kissing_B": str(kissing["B"]),
    "kissing_C": str(kissing["C"]),
    "min_norm2_A": str(norms["A"]),
    "min_norm2_B": str(norms["B"]),
    "min_norm2_C": str(norms["C"]),
    "odd_coset_contribution": str(report["odd_coset_contribution"]),
    "construction_C_is_196560": str(report["construction_C_is_196560"]),
    "drop_mod4_golay_min_norm2":
        str(necessity["drop_mod4_golay"]["minimal_norm2"]),
    "drop_mod8_sum_min_norm2":
        str(necessity["drop_mod8_sum"]["minimal_norm2"]),
    "agrees_with_leech2": str(agreement["agrees"]),
}
'''


def _body_report_facets(args: Mapping[str, object]) -> str:
    """Recompute the six-facet decomposition (v0.8.0)."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal.reasoning import facets as fa

report = fa.facets_report()
partition = report["partition"]
linearity = report["linearity"]
pythagoras = report["pythagoras"]
index = report["index_by_facet"]

observed = {
    "facets": str(partition["facets"]),
    "total": str(partition["total"]),
    "is_partition": str(partition["is_partition"]),
    "strictly_linear": str(linearity["strictly_linear"]),
    "pythagoras_additive": str(pythagoras["additive"]),
    "autonomous_facets": str(list(report["autonomous_facets"])),
}
for _name in report["order"]:
    observed["size_" + _name] = str(partition["sizes"][_name])
    observed["index_" + _name] = str(index[_name])
'''


def _body_report_monster_stack(args: Mapping[str, object]) -> str:
    """Recompute the ten-plane Monster address stack (v0.8.0)."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal.reasoning import monster_stack as msk

report = msk.monster_stack_report()
census = report["position_census"]
repaired = report["position_census_pair_repaired"]
loss = report["shortcut_loss"]
assoc = report["associativity"]

observed = {
    "depth": str(report["depth"]),
    "planes": str(census["planes"]),
    "defined_strict": str(census["defined"]),
    "defined_pair_repaired": str(repaired["defined"]),
    "sakuma_term_count": str(loss["sakuma_term_count"]),
    "terms_discarded_by_xor": str(loss["terms_discarded_by_xor"]),
    "xor_is_the_third_axis_label": str(loss["xor_is_the_third_axis_label"]),
    "sakuma_norm2": str(loss["sakuma_norm2"]),
    "shortcut_norm2": str(loss["shortcut_norm2"]),
    "associative": str(assoc["associative"]),
    "xor_associative": str(assoc["xor_associative"]),
    "commutative": str(assoc["commutative"]),
    "associativity_difference_norm2": str(assoc["difference_norm2"]),
}
'''


def _body_report_multiresolution(args: Mapping[str, object]) -> str:
    """Recompute the multi-resolution addressing report (v0.8.0)."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal.reasoning import multires as mrs

report = mrs.multires_report()
fib = report["fibration"]
columns = report["columns"]
rows = report["scale_invariance"]["rows"]
collision = report["census_collision"]
indices = sorted({_col["index"] for _col in columns})

observed = {
    "fibre_columns": str(fib["columns"]),
    "fibre_bijective": str(fib["bijective"]),
    "fibre_round_trip": str(fib["round_trip"]),
    "fibre_kernel": str(list(fib["kernel"])),
    "fibre_kernel_is_cyclic_of_order_4":
        str(fib["kernel_is_cyclic_of_order_4"]),
    "column_indices": str(indices),
    "signature_invariant_everywhere":
        str(all(_row["signature_invariant"] for _row in rows)),
    "address_invariant_anywhere":
        str(any(_row["address_invariant"] for _row in rows)),
    "census_collision_found": str(collision["found"]),
    "census_collision_carriers_equal": str(collision["carriers_equal"]),
}
'''


def _body_report_migration(args: Mapping[str, object]) -> str:
    """Recompute the legacy-to-core migration report (v0.8.0)."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal.substrate import isomorphism as iso

report = iso.migration_report()
codes = report["codes"]
isometry = codes["isometry"]
automorphism = codes["automorphism"]
decoder = report["decoder"]
dataset = report["dataset"]

observed = {
    "is_permutation": str(report["is_permutation"]),
    "fixed_points": str(list(report["fixed_points"])),
    "shared_codewords": str(codes["shared_codewords"]),
    "legacy_is_distinct": str(codes["legacy_is_distinct"]),
    "weight_distributions_agree": str(codes["weight_distributions_agree"]),
    "minimum_distance": str(codes["minimum_distance"]),
    "is_automorphism": str(automorphism["is_automorphism"]),
    "weight_preserving": str(isometry["weight_preserving"]),
    "distance_preserving": str(isometry["distance_preserving"]),
    "snap_silent_ties_total": str(decoder["snap_silent_ties_total"]),
    "routed_flagged_total": str(decoder["routed_flagged_total"]),
    "every_silent_tie_is_now_flagged":
        str(decoder["every_silent_tie_is_now_flagged"]),
    "guaranteed_below_packing_radius":
        str(decoder["guaranteed_below_packing_radius"]),
    "dataset_round_trip": str(dataset["round_trip"]),
    "dataset_weights_preserved": str(dataset["weights_preserved"]),
    "dataset_referentially_intact": str(dataset["referentially_intact"]),
}
'''


def _body_report_state_migration(args: Mapping[str, object]) -> str:
    """Recompute the literal migration of the stored GLM state (v0.9.0)."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal.migration import state as stm

report = stm.state_migration_report()
checks = report["checks"]
frame = report["frame"]
verification = report["verification"]
hexcolours = report["hexcolours"]
addresses = frame["addresses"] or {}

observed = {
    "frames_coincide": str(frame["frames_coincide"]),
    "shared_codewords": str(frame["shared_codewords"]),
    "permutation_damage": str(frame["permutation_damage"]),
    "bit_reversal_required": str(addresses.get("bit_reversal_required")),
    "concepts_imported": str(checks["concepts_imported"]),
    "concepts_minted": str(checks["concepts_minted"]),
    "edges_migrated": str(checks["edges_migrated"]),
    "edges_dropped": str(checks["edges_dropped"]),
    "referentially_intact": str(checks["referentially_intact"]),
    "roles_agree": str(checks["roles_agree"]),
    "carriers_that_are_codewords":
        str(checks["carriers_that_are_codewords"]),
    "decode_ambiguous": str(checks["decode_ambiguous"]),
    "decode_guaranteed": str(checks["decode_guaranteed"]),
    "worst_nrci_gap": str(list(checks["worst_nrci_gap"])),
    "fields_recomputed_and_agreeing":
        str(verification["fields_recomputed_and_agreeing"]),
    "floats_in_payload": str(verification["floats_in_payload"]),
    "hexcolour_concepts": str(hexcolours["concepts"]),
    "hexcolour_distinct": str(hexcolours["distinct"]),
    "hexcolour_round_trip_failures": str(hexcolours["round_trip_failures"]),
    "hexcolour_recomputed_disagreements":
        str(hexcolours["recomputed_disagreements"]),
    "hexcolour_migration_mismatches":
        str(hexcolours["migration_mismatches"]),
    "legacy_hexcolours": str(hexcolours["legacy_addresses"]),
    "legacy_hexcolour_codewords": str(hexcolours["legacy_codewords"]),
    "legacy_hexcolour_round_trip_failures":
        str(hexcolours["legacy_round_trip_failures"]),
    "hexcolours_faithful": str(hexcolours["faithful"]),
}
'''


def _body_report_concept_store(args: Mapping[str, object]) -> str:
    """Recompute the facts about the migrated concept store (v0.9.0)."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal.migration import store as sto

report = sto.store_report()

observed = {
    "concepts": str(report["concepts"]),
    "edges": str(report["edges"]),
    "labels": str(report["labels"]),
    "asserted_edges": str(report["asserted_edges"]),
    "auto_proposed_edges": str(report["auto_proposed_edges"]),
    "isolated_concepts": str(report["isolated_concepts"]),
    "minted_concepts": str(report["minted_concepts"]),
    "max_degree": str(report["max_degree"]),
    "max_degree_concept": str(report["max_degree_concept"]),
    "samples_checked": str(report["samples_checked"]),
    "samples_where_graph_and_substrate_agree":
        str(report["samples_where_graph_and_substrate_agree"]),
}
'''


def _body_task_concepts(args: Mapping[str, object]) -> str:
    """Recompute the migrated-CRG reasoning task (v0.9.0)."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal.reasoning import tasks as tk

result = tk.concept_task()
checks = result["checks"]

observed = {
    "source": str(result["source"]),
    "target": str(result["target"]),
    "asserted_steps": str(len(result["asserted_path"])),
    "path_found": str(checks["path_found"]),
    "asserted_path_found": str(checks["asserted_path_found"]),
    "paths_differ": str(checks["paths_differ"]),
    "both_crosslinked": str(checks["both_crosslinked"]),
    "law_holds": str(checks["law_holds"]),
    "control_fails": str(checks["control_fails"]),
    "discriminating": str(checks["discriminating"]),
    "substrate_contributes": str(checks["substrate_contributes"]),
}
'''


def _body_task_grid(args: Mapping[str, object]) -> str:
    """Recompute the ARC-style grid task (v0.8.0)."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal.reasoning import tasks as tk

result = tk.grid_task()
stages = {_s["resolution"]: _s for _s in result["stages"]}
checks = result["checks"]

observed = {
    "task": str(result["task"]),
    "solved": str(result["solved"]),
    "rule": str(result["rule"]),
    "prediction": str(result["prediction"]),
    "training_reproduced": str(checks["training_reproduced"]),
    "address_changed": str(checks["address_changed"]),
    "signature_preserved": str(checks["signature_preserved"]),
    "survivors_signature": str(list(stages["signature"]["survivors"])),
    "survivors_plane0": str(list(stages["address_plane0"]["survivors"])),
    "survivors_full": str(list(stages["address_full"]["survivors"])),
}
'''


def _body_task_physics(args: Mapping[str, object]) -> str:
    """Recompute the energy-versus-torque task (v0.8.0)."""
    return '''# -- recompute -------------------------------------------------------------

from glm_universal.reasoning import tasks as tk

result = tk.physics_task()
si7 = result["si7"]
ext10 = result["ext10"]
escalation = result["escalation"]
facet_part = result["facets"]
address = result["address"]

observed = {
    "left": str(result["left"]),
    "right": str(result["right"]),
    "si7_equal": str(si7["equal"]),
    "ext10_equal": str(ext10["equal"]),
    "si7_left": str(si7["left"]),
    "ext10_right": str(ext10["right"]),
    "first_separating_layer": str(escalation["first_separating_layer"]),
    "carrying_the_difference":
        str(list(facet_part["carrying_the_difference"])),
    "first_differing_plane": str(address["first_differing_plane"]),
    "difference_weight": str(address["difference_weight"]),
    "decode_status": str(address["golay"]["status"]),
    "decode_guaranteed": str(address["golay"]["guaranteed"]),
}
'''


def _body_report_theta(args: Mapping[str, object]) -> str:
    """Recompute the Leech theta series (v0.5.4)."""
    return '''# -- recompute -------------------------------------------------------------

coeffs = leech2.theta_series(order=5)

# Every coefficient the series returns, not a hand-written prefix of them:
# `order=5` yields six coefficients, and listing five of them left the last
# one unchecked.
observed = {"coeff_%d" % i: str(c) for i, c in enumerate(coeffs)}
'''


def _body_report_subalgebra(args: Mapping[str, object]) -> str:
    """Recompute the 2A subalgebra closure report (v0.5.4)."""
    return '''# -- recompute -------------------------------------------------------------

report = pr.two_a_closure_report()

observed = {k: str(v) for k, v in report.items()}
'''


def _body_angle(args: Mapping[str, object]) -> str:
    """Recompute the signed cosine squared (v0.5.4)."""
    return f'''# -- recompute -------------------------------------------------------------

{_two_operand_snippet(args)}
sc2 = me.signed_cosine_squared(obj_a.carrier, obj_b.carrier)
sign = "+" if sc2 >= 0 else "-"
abs_sc2 = abs(sc2)
if abs_sc2 == 0:
    regime = "orthogonal"
elif abs_sc2 == 1:
    regime = "parallel" if sc2 > 0 else "anti-parallel"
elif abs_sc2 >= Fraction(1, 2):
    regime = "acute" if sc2 > 0 else "obtuse"
else:
    regime = "near-orthogonal"

observed = {{
    "operand_a": obj_a.name,
    "operand_b": obj_b.name,
    "signed_cosine_squared": q(sc2),
    "regime": regime,
}}
'''


def _body_pi_groups(args: Mapping[str, object]) -> str:
    """Recompute the Buckingham-Pi groups of a quantity set (v1.0.0)."""
    names = list(args["names"])            # type: ignore[arg-type]
    return f'''# -- recompute -------------------------------------------------------------

from glm_universal.reasoning import valorani as va

names = {names!r}
report = va.buckingham_pi_groups(names)
groups = [[Fraction(c) for c in vec] for vec in report["pi_groups"]]
rank = len(names) - len(groups)

residues = []
for _vec in groups:
    _total = [Fraction(0)] * 10
    for _weight, _name in zip(_vec, names):
        _exps = do.physics.quantity_by_name(_name).exps_ext10
        for _axis in range(10):
            _total[_axis] += _weight * _exps[_axis]
    residues.append(_total)
all_dimensionless = all(all(x == 0 for x in row) for row in residues)

observed = {{
    "quantities": str(names),
    "n_quantities": str(len(names)),
    "rank": str(rank),
    "n_pi_groups": str(len(groups)),
    "pi_groups": str([[q(c) for c in vec] for vec in groups]),
    "all_dimensionless": str(all_dimensionless),
}}
'''


def _body_nearest(args: Mapping[str, object]) -> str:
    reference = _carrier_expr(args["name"], args.get("formula"))
    return f'''# -- recompute -------------------------------------------------------------

{_pool_snippet(str(args["domain"]))}
obj = {reference}
subspace = {args["subspace"]!r}
indices = None
if subspace is not None:
    indices = an.subspace_indices(obj.layout, an.SUBSPACES[subspace])

target = an.project_subspace(obj.carrier, indices)
candidates = [(o.name, an.project_subspace(o.carrier, indices)) for o in pool]
ranked = me.rank_by_distance(target, candidates, exclude=(obj.name,))
top = ranked[:{int(args["limit"])}]

observed = {{
    "reference": obj.name,
    "nearest": top[0][0],
    "nearest_distance2": q(top[0][1]),
    "top_names": str([n for n, _ in top]),
    "top_distances2": str([q(d) for _, d in top]),
}}
'''


def _body_product(args: Mapping[str, object]) -> str:
    return f'''# -- recompute -------------------------------------------------------------
#
# Note on the F_2 step: the third axis is the sum of the two classes in the
# module Lambda / 2 Lambda.  That module's addition IS the bitwise XOR of the
# coordinate vectors, so sakuma_third_axis is a linear map over F_2, not an
# opportunistic bit trick standing in for arithmetic.  Every rational below is
# a Fraction.

u = {int(args["u"])}
v = {int(args["v"])}
assert leech2.is_type2_class(u), "u is not a type-2 class"
assert leech2.is_type2_class(v), "v is not a type-2 class"
assert pr.is_two_a_pair(u, v), "u and v are not in the 2A position"

third = pr.sakuma_third_axis(u, v)
prod = pr.axis_product(u, v)
sub = pr.two_a_subalgebra(u, v)
coeffs = {{str(label): q(prod.coefficient(label)) for label in sorted(sub.labels)}}

observed = {{
    "u": str(u),
    "v": str(v),
    "third_axis": str(third),
    "position": pr.position_name(u, v),
    "coefficients": str(sorted(coeffs.items())),
    "griess_self": q(pr.griess_form(pr.axis(u), pr.axis(u))),
    "griess_pair": q(pr.griess_form(pr.axis(u), pr.axis(v))),
    "subalgebra_labels": str(sorted(sub.labels)),
}}
'''


def _body_cluster(args: Mapping[str, object]) -> str:
    names = list(args["names"])  # type: ignore[arg-type]
    formulas = list(args.get("formulas")   # type: ignore[arg-type]
                    or [None] * len(names))
    linkage = str(args.get("linkage", "single"))
    build = "complete_linkage" if linkage == "complete" else "single_linkage"
    return f'''# -- recompute -------------------------------------------------------------

{_pool_snippet(str(args["domain"]))}
names = {names!r}
formulas = {formulas!r}
objs = [by_name[n] if f is None else do.object_from_formula(f)
        for n, f in zip(names, formulas)]
tree = me.{build}([o.carrier for o in objs], [o.name for o in objs])
groups = me.cut_tree(tree, {int(args["k"])})

observed = {{
    "labels": str([o.name for o in objs]),
    "k": str({int(args["k"])}),
    "linkage": tree.linkage,
    "groups": str(groups),
    "merge_heights": str([q(m.height) for m in tree.merges]),
}}
'''


def _body_spatial(args: Mapping[str, object]) -> str:
    return f'''# -- recompute -------------------------------------------------------------

{_pool_snippet(str(args["domain"]))}
obj = {_carrier_expr(args["name"], args.get("formula"))}
plane0 = obj.stack().planes[0]
grid = mog.frame(plane0)
cube = mog.cube_profile(plane0)
codeword, distance, count = an.nearest_golay_codeword(plane0)

observed = {{
    "name": obj.name,
    "plane0_mask": "0x%06x" % plane0,
    "plane0_weight": str(bin(plane0).count("1")),
    "frame_rows": str([[int(b) for b in row] for row in grid]),
    "brick_weights": str([c["weight"] for c in cube]),
    "nearest_codeword": "0x%06x" % codeword,
    "golay_distance": str(distance),
    "golay_multiplicity": str(count),
}}
'''


#: Template name -> body renderer.  A solver names its template in
#: ``Solution.script_spec["template"]``; there is no fallback, because a
#: silently generic script would verify nothing in particular.
TEMPLATES = {
    "verify": _body_verify,
    "analogy": _body_analogy,
    # v1.4.0: an analogy transported as a named relation, and the report
    # that re-solves every case through the model layer.
    "analogy_model": _body_analogy_model,
    "report_analogies": _body_report_analogies,
    "describe": _body_describe,
    # v1.3.0: a description whose subject is arithmetic over register names.
    "describe_arithmetic": _body_describe_arithmetic,
    "nearest": _body_nearest,
    "product": _body_product,
    "cluster": _body_cluster,
    "spatial": _body_spatial,
    # Three new templates added in v0.5.3, wiring previously-unused
    # reasoning mechanisms into the runtime.
    "project": _body_project,        # uses dimension_layers.escalate
    "trilinear": _body_trilinear,    # uses product.griess_trilinear
    "coherence": _body_coherence,   # uses coherence.nrci_breakdown
    # Two more templates added in v0.5.4 for the report and angle
    # query kinds.
    "report_relations": _body_report_relations,
    "report_leech": _body_report_leech,
    # v0.7.0: the information-loss-at-boundaries study.
    "report_information_loss": _body_report_information_loss,
    # v1.5.0: noise used as the computation -- cascaded loops, interacting
    # tones, and the dither sweep.
    "report_noise": _body_report_noise,
    # v1.6.0: the lattice ladder past 24 dimensions, and delta-sigma with a
    # shell alphabet plus the Gibbs-style rule.
    "report_lattices": _body_report_lattices,
    "report_shells": _body_report_shells,
    # The LLVQ class table on the quantiser's hot path.
    "report_llvq": _body_report_llvq,
    "report_harmony": _body_report_harmony,
    # v1.11.0: the recipe made into an object -- the domain descriptions,
    # the one generic path, and the regeneration test.
    "derive": _body_derive,
    "report_recipe": _body_report_recipe,
    # v1.12.0: the surface language driven off the same kind of
    # description -- the question shape made an object.
    "report_language": _body_report_language,
    # v1.8.0: the economic third of the same universality claim.
    "report_economics": _body_report_economics,
    # v1.8.0: the layer audit run on every register carrier.
    "report_escalation": _body_report_escalation,
    # A coordinate for the name, and what it buys against four controls.
    "report_names": _body_report_names,
    # v1.9.0: a measure word read against a comparison class, and the
    # relative-measure study behind it.
    "measure": _body_measure,
    # v1.9.0: the comparative between two uses of a measure word.
    "comparative": _body_comparative,
    "measure_magnitude": _body_measure_magnitude,
    "measure_word": _body_measure_word,
    "report_measure": _body_report_measure,
    # v1.6.0: Leech addresses for Lean declarations, the standing
    # directives and their instruments, and the study pipeline board.
    "report_lean": _body_report_lean,
    "report_directives": _body_report_directives,
    "report_pipeline": _body_report_pipeline,
    "report_theta": _body_report_theta,
    "report_subalgebra": _body_report_subalgebra,
    "angle": _body_angle,
    # v0.8.0: the five newly reachable report subjects and the two
    # worked end-to-end tasks.
    "report_golay_decoding": _body_report_golay_decoding,
    "report_superposition": _body_report_superposition,
    "report_leech_construction": _body_report_leech_construction,
    "report_facets": _body_report_facets,
    "report_monster_stack": _body_report_monster_stack,
    "report_multiresolution": _body_report_multiresolution,
    "report_migration": _body_report_migration,
    "report_state_migration": _body_report_state_migration,
    "report_concept_store": _body_report_concept_store,
    # v0.9.0: the Griess-algebra fusion layer.
    "report_fusion": _body_report_fusion,
    # v1.0.0: the benchmark suites and the Buckingham-Pi query kind.
    "report_benchmarks": _body_report_benchmarks,
    "pi_groups": _body_pi_groups,
    # v1.1.0: the meaning space -- reference resolution, derived relations,
    # and the audit of the inherited concept graph against both.
    "meaning": _body_meaning,
    # v1.2.0: values that are not carriers, and the capability probes.
    "real": _body_real,
    "compare": _body_compare,
    "report_infinite_values": _body_report_infinite_values,
    "report_capabilities": _body_report_capabilities,
    "report_semantics": _body_report_semantics,
    # v1.4.0: the transform-driven decoder and its O(1) certificate.
    "report_transform_decoder": _body_report_transform_decoder,
    "report_deep_holes": _body_report_deep_holes,
    "report_units": _body_report_units,
    # v1.4.0: the molecules register and the chemistry-coverage widening.
    "report_molecules": _body_report_molecules,
    "report_chemistry_coverage": _body_report_chemistry_coverage,
    # v5.2.0: the unification blueprint tested claim by claim, and the two
    # studies it rests on.
    "report_blueprint": _body_report_blueprint,
    "report_signature": _body_report_signature,
    "report_drift": _body_report_drift,
    "report_catalog": _body_report_catalog,
    # v5.5.0: the two companion preprints, and the instrument behind them.
    "report_containers": _body_report_containers,
    "report_companion": _body_report_companion,
    "report_reversible": _body_report_reversible,
    "report_mantissa": _body_report_mantissa,
    "report_engine": _body_report_engine,
    "task_grid": _body_task_grid,
    "task_physics": _body_task_physics,
    "task_concepts": _body_task_concepts,
}


def render_script(solution: Solution, root: Optional[str] = None) -> str:
    """Render column 3 for a solution.

    Parameters
    ----------
    solution
        A solved query.  Its ``script_spec`` names the template and supplies
        the arguments; its ``expected`` mapping is embedded as the assertion
        target.
    root
        Directory to prepend to ``sys.path`` inside the script.  Defaults to
        :func:`package_root`, which is what makes the script runnable from any
        working directory.

    Raises
    ------
    TCTError
        If the solution is unsolved, names no template, or names one that does
        not exist.
    """
    if not solution.ok:
        raise TCTError(
            f"render_script: refusing to render a script for an unsolved "
            f"query ({solution.error})")
    spec = dict(solution.script_spec)
    template = spec.get("template")
    if template is None:
        raise TCTError("render_script: solution names no script template")
    if template not in TEMPLATES:
        raise TCTError(f"render_script: unknown template {template!r}; known "
                       f"templates are {sorted(TEMPLATES)}")
    args = dict(spec.get("args", {}))  # type: ignore[arg-type]

    header = _HEADER.format(
        query=solution.query.raw, kind=solution.kind,
        root=str(root or package_root()),
        expected=json.dumps(dict(solution.expected), indent=4,
                            sort_keys=True))
    body = TEMPLATES[template](args)
    footer = _FOOTER.format(begin=BEGIN_MARKER, end=END_MARKER)
    return header + body + footer


def script_is_exact(source: str) -> Tuple[bool, Tuple[str, ...]]:
    """Whether a generated script obeys the package's exactness rules.

    Checks by AST, not by text search, so a ``float`` inside a string literal
    or a comment is correctly ignored while a real one is caught.

    Returns
    -------
    (ok, offenders)
        ``offenders`` names each violation as ``"line N: what"``.
    """
    offenders: List[str] = []
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return False, (f"line {exc.lineno}: syntax error: {exc.msg}",)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            offenders.append(f"line {node.lineno}: float literal")
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "float"):
            offenders.append(f"line {node.lineno}: float() call")
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] == "random":
                    offenders.append(f"line {node.lineno}: imports random")
        if isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] == "random":
                offenders.append(f"line {node.lineno}: imports random")
    return not offenders, tuple(offenders)


# ===========================================================================
# 2.  THE TRACE
# ===========================================================================

@dataclass(frozen=True)
class ScriptVerdict:
    """The outcome of running column 3 in a fresh interpreter.

    Attributes
    ----------
    executed
        Whether the subprocess ran at all.  ``False`` means it timed out or
        the interpreter could not be started -- distinct from running and
        failing.
    returncode
        The process exit code.  ``0`` means the script's own assertions
        passed.
    observed
        The JSON payload the script emitted, key by key.  Empty if the script
        died before printing it.
    matches_column2
        Whether the parent process's own comparison of ``observed`` against
        the solution's ``expected`` found no difference.  This is computed
        here, independently of the script's exit code.
    mismatches
        ``(key, expected, observed)`` for each disagreement.
    missing_keys
        Claims in column 2 that the script did not report at all.
    stderr_tail
        The last part of standard error, for diagnosis.
    duration_note
        How the run was bounded, recorded rather than timed, so that a trace
        is byte-identical between runs.
    """

    executed: bool
    returncode: Optional[int]
    observed: Mapping[str, str] = field(default_factory=dict)
    matches_column2: bool = False
    mismatches: Tuple[Tuple[str, str, str], ...] = ()
    missing_keys: Tuple[str, ...] = ()
    stderr_tail: str = ""
    duration_note: str = ""

    @property
    def verified(self) -> bool:
        """Both checks agree: exit code 0 *and* a key-by-key match.

        Either alone is insufficient.  A zero exit with no payload would mean
        the script never got to its assertions; a payload match with a
        non-zero exit would mean the script found something the parent's
        comparison does not model.
        """
        return (self.executed and self.returncode == 0
                and self.matches_column2 and bool(self.observed))

    def as_dict(self) -> Dict[str, object]:
        """A JSON-serialisable view."""
        return {
            "executed": self.executed,
            "returncode": self.returncode,
            "verified": self.verified,
            "matches_column2": self.matches_column2,
            "observed": dict(self.observed),
            "mismatches": [list(m) for m in self.mismatches],
            "missing_keys": list(self.missing_keys),
            "stderr_tail": self.stderr_tail,
            "duration_note": self.duration_note,
        }


@dataclass(frozen=True)
class ThreeColumnTrace:
    """One query, stated three times over, plus the verification verdict."""

    query: str
    kind: str
    answer: str
    language: Tuple[str, ...]
    mathematics: Tuple[str, ...]
    script: str
    expected: Mapping[str, str] = field(default_factory=dict)
    labels: Tuple[str, ...] = ()
    verdict: Optional[ScriptVerdict] = None

    @property
    def synchronized(self) -> bool:
        """Whether the three columns describe the same number of steps.

        Columns 1 and 2 are emitted from the same
        :class:`~glm_universal.runtime.session.Step` objects, so this is a
        structural invariant rather than a discovery -- it is asserted here so
        that a future refactor that breaks the pairing fails loudly.
        """
        return (len(self.language) == len(self.mathematics) == len(self.labels)
                and len(self.language) > 0 and bool(self.script))

    @property
    def verified(self) -> bool:
        """Whether column 3 ran and agreed with column 2."""
        return self.verdict is not None and self.verdict.verified

    def with_verdict(self, verdict: ScriptVerdict) -> "ThreeColumnTrace":
        """A copy carrying ``verdict``; the trace itself stays immutable."""
        return ThreeColumnTrace(
            query=self.query, kind=self.kind, answer=self.answer,
            language=self.language, mathematics=self.mathematics,
            script=self.script, expected=self.expected, labels=self.labels,
            verdict=verdict)

    def as_dict(self, include_script: bool = True) -> Dict[str, object]:
        """A JSON-serialisable view."""
        out: Dict[str, object] = {
            "query": self.query,
            "kind": self.kind,
            "answer": self.answer,
            "labels": list(self.labels),
            "column1_language": list(self.language),
            "column2_mathematics": list(self.mathematics),
            "expected": dict(self.expected),
            "synchronized": self.synchronized,
            "verified": self.verified,
            "verdict": self.verdict.as_dict() if self.verdict else None,
        }
        if include_script:
            out["column3_script"] = self.script
        return out


def build_trace(solution: Solution,
                root: Optional[str] = None) -> ThreeColumnTrace:
    """Assemble the three columns from one solution.

    Columns 1 and 2 are read off the solution's steps in order, so they are
    aligned by construction: entry *i* of each column is the same
    :class:`~glm_universal.runtime.session.Step`.
    """
    steps: Sequence[Step] = solution.steps
    if not steps:
        raise TCTError("build_trace: the solution carries no steps")
    return ThreeColumnTrace(
        query=solution.query.raw,
        kind=solution.kind,
        answer=solution.answer,
        language=tuple(s.language for s in steps),
        mathematics=tuple(s.mathematics for s in steps),
        script=render_script(solution, root=root),
        expected=dict(solution.expected),
        labels=tuple(s.label for s in steps),
    )


def _extract_payload(stdout: str) -> Optional[Dict[str, object]]:
    """Pull the JSON payload from between the markers, or ``None``."""
    start = stdout.find(BEGIN_MARKER)
    end = stdout.find(END_MARKER)
    if start < 0 or end < 0 or end < start:
        return None
    blob = stdout[start + len(BEGIN_MARKER):end].strip()
    try:
        parsed = json.loads(blob)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def verify_trace(trace: ThreeColumnTrace, workdir: Optional[Path] = None,
                 timeout: int = DEFAULT_TIMEOUT_SECONDS) -> ThreeColumnTrace:
    """Run column 3 in a fresh interpreter and cross-check its output.

    The script is written into ``workdir`` (a temporary directory if none is
    given) and run with :data:`sys.executable`, so it uses the same
    interpreter and the same installed package as the caller but shares no
    interpreter state with it -- no cached register, no imported module, no
    already-computed table.

    Parameters
    ----------
    trace
        The trace whose script to run.
    workdir
        Where to write the script.  Supplying one keeps the script on disk for
        inspection after the run.
    timeout
        Wall-clock ceiling in seconds.

    Returns
    -------
    ThreeColumnTrace
        A copy of ``trace`` carrying a :class:`ScriptVerdict`.  A failed run
        is reported, never raised: a script that disagrees with column 2 is a
        result about the trace, not an error in the harness.
    """
    import tempfile

    temp: Optional[tempfile.TemporaryDirectory] = None
    if workdir is None:
        temp = tempfile.TemporaryDirectory(prefix="glm_tct_")
        target = Path(temp.name)
    else:
        target = Path(workdir)
        target.mkdir(parents=True, exist_ok=True)

    try:
        path = target / "tct_column3.py"
        path.write_text(trace.script, encoding="utf-8")

        env = dict(os.environ)
        env["PYTHONPATH"] = str(package_root()) + os.pathsep + env.get(
            "PYTHONPATH", "")
        env["PYTHONHASHSEED"] = "0"
        try:
            proc = subprocess.run(
                [sys.executable, str(path)], capture_output=True, text=True,
                timeout=timeout, env=env, cwd=str(package_root()), check=False)
        except subprocess.TimeoutExpired:
            return trace.with_verdict(ScriptVerdict(
                executed=False, returncode=None,
                stderr_tail=f"timed out after {timeout} s",
                duration_note=f"bounded at {timeout} s"))
        except OSError as exc:
            return trace.with_verdict(ScriptVerdict(
                executed=False, returncode=None,
                stderr_tail=f"could not start interpreter: {exc}",
                duration_note=f"bounded at {timeout} s"))

        payload = _extract_payload(proc.stdout)
        observed: Dict[str, str] = {}
        if payload is not None and isinstance(payload.get("observed"), dict):
            observed = {str(k): str(v)
                        for k, v in payload["observed"].items()}

        mismatches: List[Tuple[str, str, str]] = []
        missing: List[str] = []
        for key in sorted(trace.expected):
            if key not in observed:
                missing.append(key)
            elif observed[key] != trace.expected[key]:
                mismatches.append((key, trace.expected[key], observed[key]))

        return trace.with_verdict(ScriptVerdict(
            executed=True,
            returncode=proc.returncode,
            observed=observed,
            matches_column2=not mismatches and not missing and bool(observed),
            mismatches=tuple(mismatches),
            missing_keys=tuple(missing),
            stderr_tail=proc.stderr[-2000:],
            duration_note=f"bounded at {timeout} s"))
    finally:
        if temp is not None:
            temp.cleanup()


# ===========================================================================
# 3.  PRESENTATION
# ===========================================================================

def trace_to_markdown(trace: ThreeColumnTrace,
                      include_script: bool = True) -> str:
    """Render a trace as Markdown: the three columns, then the verdict."""
    lines: List[str] = [
        f"# Three Column Thinking -- {trace.kind}",
        "",
        f"**Query.** `{trace.query}`",
        "",
        f"**Answer.** {trace.answer}",
        "",
        "| # | Step | Column 1 -- Language | Column 2 -- Exact mathematics |",
        "|---|------|----------------------|-------------------------------|",
    ]
    for i, (label, lang, math) in enumerate(
            zip(trace.labels, trace.language, trace.mathematics), start=1):
        lines.append(f"| {i} | `{label}` | {_cell(lang)} | {_cell(math)} |")

    lines += ["", "## Claims checked by column 3", "",
              "| Claim | Exact value |", "|-------|-------------|"]
    for key in sorted(trace.expected):
        lines.append(f"| `{key}` | `{trace.expected[key]}` |")

    if trace.verdict is not None:
        v = trace.verdict
        lines += [
            "", "## Column 3 verdict", "",
            f"- executed: **{v.executed}**",
            f"- exit code: **{v.returncode}**",
            f"- parent-process key-by-key match: **{v.matches_column2}**",
            f"- verified (both checks agree): **{v.verified}**",
        ]
        if v.mismatches:
            lines.append("- mismatches:")
            for key, want, got in v.mismatches:
                lines.append(f"  - `{key}`: column 2 `{want}`, "
                             f"recomputation `{got}`")
        if v.missing_keys:
            lines.append(f"- claims the script did not report: "
                         f"{list(v.missing_keys)}")
        if v.stderr_tail.strip():
            lines += ["", "```text", v.stderr_tail.strip()[-1200:], "```"]

    if include_script:
        lines += ["", "## Column 3 -- executable script", "",
                  "```python", trace.script.rstrip(), "```"]
    return "\n".join(lines) + "\n"


def _cell(text: str) -> str:
    """Fold a multi-line step into one Markdown table cell."""
    return text.replace("|", r"\|").replace("\n", "<br>")
