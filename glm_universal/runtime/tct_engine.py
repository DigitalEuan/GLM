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
    }
    if domain not in loaders:
        raise TCTError(f"render_script: no pool loader for domain {domain!r}")
    return (f"pool = {loaders[domain]}\n"
            f"by_name = {{o.name: o for o in pool}}\n")


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
    domain_a = args["domain_a"]
    domain_b = args["domain_b"]
    name_a = args["name_a"]
    name_b = args["name_b"]
    return f'''# -- recompute -------------------------------------------------------------

# Two pools may be needed -- if the operands come from different domains.
pool_a = {{
    "physics": do.physics_objects(),
    "chemistry": do.element_objects(),
    "mathematics": do.mathematics_objects(),
    "lexicon": do.semantic_lexicon_objects()[0],
    "spatial": spatial_objects(),
}}[{domain_a!r}]
pool_b = {{
    "physics": do.physics_objects(),
    "chemistry": do.element_objects(),
    "mathematics": do.mathematics_objects(),
    "lexicon": do.semantic_lexicon_objects()[0],
    "spatial": spatial_objects(),
}}[{domain_b!r}]
obj_a = next(o for o in pool_a if o.name == {name_a!r})
obj_b = next(o for o in pool_b if o.name == {name_b!r})

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
obj = by_name[{args["name"]!r}]
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
    domain_a = args["domain_a"]
    domain_b = args["domain_b"]
    name_a = args["name_a"]
    name_b = args["name_b"]
    return f'''# -- recompute -------------------------------------------------------------

pool_a = {{
    "physics": do.physics_objects(),
    "chemistry": do.element_objects(),
    "mathematics": do.mathematics_objects(),
    "lexicon": do.semantic_lexicon_objects()[0],
    "spatial": spatial_objects(),
}}[{domain_a!r}]
pool_b = {{
    "physics": do.physics_objects(),
    "chemistry": do.element_objects(),
    "mathematics": do.mathematics_objects(),
    "lexicon": do.semantic_lexicon_objects()[0],
    "spatial": spatial_objects(),
}}[{domain_b!r}]
obj_a = next(o for o in pool_a if o.name == {name_a!r})
obj_b = next(o for o in pool_b if o.name == {name_b!r})

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
    return f'''# -- recompute -------------------------------------------------------------

{_pool_snippet(str(args["domain"]))}
obj = by_name[{args["name"]!r}]
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
    linkage = str(args.get("linkage", "single"))
    build = "complete_linkage" if linkage == "complete" else "single_linkage"
    return f'''# -- recompute -------------------------------------------------------------

{_pool_snippet(str(args["domain"]))}
names = {names!r}
objs = [by_name[n] for n in names]
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
obj = by_name[{args["name"]!r}]
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
