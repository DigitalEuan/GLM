"""Flatten the declared wheel axioms into one typed, inspectable graph.

The graph is a projection of the data in ``wheels/*.json`` and the declared
junction table in ``wheels/index.json``.  It does not prove an analogy, derive
a new spoke, or merge quantities merely because they share a name.

Node kinds
----------
wheel
    One of the 39 built wheels.
axiom
    One declared equation, with its exact relation vector.
quantity
    A wheel-local quantity.  ``W1.power`` and ``W5.power`` are distinct nodes
    unless a declared junction connects them.
dimension
    An exact SI exponent vector shared by quantities.

Edge kinds
----------
contains
    wheel -> axiom
mentions
    axiom -> quantity, carrying the exact exponent
typed_as
    quantity -> dimension
junction
    quantity -> quantity, only from the declared junction table
non_identity
    quantity -> quantity, a declared barrier rather than an identity

A junction whose endpoint is not present in the declared wheel quantities is
reported in ``gaps`` and produces no edge.  The same rule applies to
non-identities.  This is intentional: the graph must not invent a quantity to
make the table look complete.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from fractions import Fraction
from functools import lru_cache
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .wheels import (
    JUNCTIONS,
    NON_IDENTITIES,
    WHEELS,
    relation_vector,
    render_monomial,
    wheel_quantities,
    wheel_spokes,
)

SCHEMA = "cent-axiom-graph/1"
DERIVATION_SCHEMA = "cent-derivation/1"
GROUNDING_SCHEMA = "cent-wheel-grounding/1"
SPOKE_REGRESSION_SCHEMA = "cent-spoke-regression/1"
DIRECT_JUNCTION_HOPS = 1
MAX_CANDIDATE_AXIOMS = 32
MAX_DERIVATION_AXIOMS = 6
MAX_DERIVATIONS = 8
AXES = ("L", "M", "T", "I", "H", "N", "J", "A")
WHEELS_DIR = Path(__file__).resolve().parent.parent / "wheels"

#: Exact algebraic shapes that can be grounded by a declared monomial axiom.
#: These are relation queries, not keyword maps: a candidate must still pass
#: ``derive_from`` over the flattened graph.  Transcendental and stateful
#: primitives have no monomial query and return an explicit gap here; their
#: separately declared physical bridges remain a different evidence class.
RELATION_QUERIES: dict[str, dict[str, str]] = {
    "sqrt": {
        "kind": "half-exponent",
        "detail": "a declared axiom contains a quantity with exponent 1/2 or -1/2",
    },
    "mult": {
        "kind": "product",
        "detail": "a single positive target is the product of at least two negative-exponent inputs",
    },
}


def _fraction_text(value: Any) -> str:
    item = Fraction(value)
    return f"{item.numerator}/{item.denominator}"


def _dimension_text(values: Iterable[Any]) -> str:
    parts = []
    for axis, value in zip(AXES, values):
        item = _fraction_text(value)
        if item != "0/1":
            parts.append(f"{axis}^{item}")
    return " ".join(parts) or "1"


def _dimension_id(values: Iterable[Any]) -> str:
    text = _dimension_text(values)
    return "dimension:" + text.replace(" ", "_")


@lru_cache(maxsize=1)
def _documents() -> dict[str, Mapping[str, Any]]:
    docs: dict[str, Mapping[str, Any]] = {}
    if not WHEELS_DIR.is_dir():
        return docs
    for path in sorted(WHEELS_DIR.glob("W*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, Mapping):
            docs[str(data.get("id", path.stem))] = data
    return docs


def _dimension_for(
    doc: Mapping[str, Any], quantity: str
) -> tuple[Any, ...] | None:
    item = (doc.get("dimensions") or {}).get(quantity)
    if not isinstance(item, Mapping):
        return None
    axes = tuple(item.get("axes") or ())
    exponents = item.get("exponents")
    if axes != AXES or not isinstance(exponents, list) or len(exponents) != len(AXES):
        return None
    try:
        return tuple(exponents)
    except (TypeError, ValueError):
        return None


@lru_cache(maxsize=1)
def build_axiom_graph() -> dict[str, Any]:
    """Return the flattened graph and its declared-coverage gaps."""
    docs = _documents()
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []
    node_by_id: dict[str, dict[str, Any]] = {}
    quantity_by_key: dict[tuple[str, str], str] = {}
    shared: dict[str, set[str]] = {}

    def add_node(node: dict[str, Any]) -> bool:
        existing = node_by_id.get(node["id"])
        if existing is not None:
            if existing != node:
                gaps.append(
                    {
                        "kind": "node-collision",
                        "id": node["id"],
                        "detail": "two declared nodes have the same id",
                    }
                )
            return False
        node_by_id[node["id"]] = node
        nodes.append(node)
        return True

    def add_edge(kind: str, source: str, target: str, data: Mapping[str, Any]) -> None:
        edges.append(
            {
                "kind": kind,
                "source": source,
                "target": target,
                "data": dict(data),
            }
        )

    def add_quantity(wheel_id: str, name: str, declared: bool) -> str:
        key = (wheel_id, name)
        existing = quantity_by_key.get(key)
        if existing is not None:
            return existing
        quantity_id = f"quantity:{wheel_id}:{name}"
        dim = _dimension_for(docs.get(wheel_id, {}), name)
        dim_id = _dimension_id(dim) if dim is not None else None
        add_node(
            {
                "id": quantity_id,
                "kind": "quantity",
                "label": f"{wheel_id}.{name}",
                "data": {
                    "wheel": wheel_id,
                    "name": name,
                    "declared_quantity": declared,
                    "dimension": dim_id,
                    "dimension_text": _dimension_text(dim) if dim is not None else None,
                    "source": f"wheels/{wheel_id}.json",
                },
            }
        )
        quantity_by_key[key] = quantity_id
        if dim is None:
            gaps.append(
                {
                    "kind": "missing-dimension",
                    "wheel": wheel_id,
                    "quantity": name,
                    "detail": (
                        f"{wheel_id}.{name} has no usable SI exponent vector; "
                        "it has no typed_as edge"
                    ),
                }
            )
        else:
            add_node(
                {
                    "id": dim_id,
                    "kind": "dimension",
                    "label": _dimension_text(dim),
                    "data": {
                        "axes": list(AXES),
                        "exponents": [_fraction_text(value) for value in dim],
                        "text": _dimension_text(dim),
                    },
                }
            )
            add_edge(
                "typed_as",
                quantity_id,
                dim_id,
                {"dimension_text": _dimension_text(dim)},
            )
        return quantity_id

    for wheel in WHEELS:
        doc = docs.get(wheel.id, {})
        wheel_id = f"wheel:{wheel.id}"
        add_node(
            {
                "id": wheel_id,
                "kind": "wheel",
                "label": f"{wheel.id} — {wheel.title}",
                "data": {
                    "wheel": wheel.id,
                    "title": wheel.title,
                    "source": f"wheels/{wheel.id}.json",
                },
            }
        )
        declared_quantities = [
            str(name)
            for name in (doc.get("quantities") or wheel_quantities(wheel))
        ]
        for name in dict.fromkeys(declared_quantities):
            add_quantity(wheel.id, name, True)
            shared.setdefault(name, set()).add(wheel.id)

        for index, equation in enumerate(wheel.axioms):
            axiom_id = f"axiom:{wheel.id}:{index:02d}"
            try:
                relation = relation_vector(equation)
            except (TypeError, ValueError) as exc:
                gaps.append(
                    {
                        "kind": "invalid-axiom",
                        "wheel": wheel.id,
                        "index": index,
                        "equation": equation,
                        "detail": str(exc),
                    }
                )
                continue
            named = {
                key: _fraction_text(value)
                for key, value in relation.items()
                if not str(key).startswith("#")
            }
            scalars = {
                str(key): _fraction_text(value)
                for key, value in relation.items()
                if str(key).startswith("#")
            }
            add_node(
                {
                    "id": axiom_id,
                    "kind": "axiom",
                    "label": equation,
                    "data": {
                        "wheel": wheel.id,
                        "index": index,
                        "equation": equation,
                        "relation": named,
                        "scalars": scalars,
                        "source": f"wheels/{wheel.id}.json",
                    },
                }
            )
            add_edge(
                "contains",
                wheel_id,
                axiom_id,
                {"wheel": wheel.id, "index": index, "equation": equation},
            )
            for name, exponent in named.items():
                quantity_id = add_quantity(wheel.id, name, name in declared_quantities)
                add_edge(
                    "mentions",
                    axiom_id,
                    quantity_id,
                    {"exponent": exponent, "quantity": name},
                )

    junction_edges = 0
    for junction in JUNCTIONS:
        source = quantity_by_key.get((junction.wheel_a, junction.name))
        target = quantity_by_key.get((junction.wheel_b, junction.name_b or junction.name))
        if source is None or target is None:
            missing = []
            if source is None:
                missing.append(f"{junction.wheel_a}.{junction.name}")
            if target is None:
                missing.append(f"{junction.wheel_b}.{junction.name_b or junction.name}")
            gaps.append(
                {
                    "kind": "junction-endpoint",
                    "wheel_a": junction.wheel_a,
                    "wheel_b": junction.wheel_b,
                    "name_a": junction.name,
                    "name_b": junction.name_b or junction.name,
                    "missing": missing,
                    "reason": junction.reason,
                    "detail": (
                        "declared junction has no quantity node for "
                        + ", ".join(missing)
                    ),
                }
            )
            continue
        add_edge(
            "junction",
            source,
            target,
            {
                "wheel_a": junction.wheel_a,
                "wheel_b": junction.wheel_b,
                "name_a": junction.name,
                "name_b": junction.name_b or junction.name,
                "reason": junction.reason,
                "source": "wheels/index.json",
            },
        )
        junction_edges += 1

    non_identity_edges = 0
    for item in NON_IDENTITIES:
        source = quantity_by_key.get((item.wheel_a, item.name))
        target = quantity_by_key.get((item.wheel_b, item.name))
        if source is None or target is None:
            missing = []
            if source is None:
                missing.append(f"{item.wheel_a}.{item.name}")
            if target is None:
                missing.append(f"{item.wheel_b}.{item.name}")
            gaps.append(
                {
                    "kind": "non-identity-endpoint",
                    "wheel_a": item.wheel_a,
                    "wheel_b": item.wheel_b,
                    "name": item.name,
                    "missing": missing,
                    "reason": item.reason,
                    "detail": (
                        "declared non-identity has no quantity node for "
                        + ", ".join(missing)
                    ),
                }
            )
            continue
        add_edge(
            "non_identity",
            source,
            target,
            {
                "wheel_a": item.wheel_a,
                "wheel_b": item.wheel_b,
                "name": item.name,
                "reason": item.reason,
                "source": "wheels/index.json",
            },
        )
        non_identity_edges += 1

    nodes.sort(key=lambda item: (item["kind"], item["id"]))
    edges.sort(key=lambda item: (item["kind"], item["source"], item["target"]))
    gaps.sort(key=lambda item: (item["kind"], str(item.get("wheel_a", "")), str(item.get("wheel", ""))))

    edge_counts: dict[str, int] = {}
    for edge in edges:
        edge_counts[edge["kind"]] = edge_counts.get(edge["kind"], 0) + 1
    shared_names = sorted(name for name, wheels in shared.items() if len(wheels) > 1)
    counts = {
        "wheels": len([node for node in nodes if node["kind"] == "wheel"]),
        "axioms": len([node for node in nodes if node["kind"] == "axiom"]),
        "quantities": len([node for node in nodes if node["kind"] == "quantity"]),
        "dimensions": len([node for node in nodes if node["kind"] == "dimension"]),
        "contains": edge_counts.get("contains", 0),
        "mentions": edge_counts.get("mentions", 0),
        "typed_as": edge_counts.get("typed_as", 0),
        "junction_edges": junction_edges,
        "junction_declared": len(JUNCTIONS),
        "non_identity_edges": non_identity_edges,
        "non_identity_declared": len(NON_IDENTITIES),
        "shared_names": len(shared_names),
    }
    return {
        "schema": SCHEMA,
        "status": "complete" if not gaps else "partial",
        "source": "wheels/*.json and wheels/index.json",
        "identity_policy": (
            "quantity nodes are wheel-local; only declared junction edges "
            "connect identities"
        ),
        "counts": counts,
        "shared_names": shared_names,
        "nodes": nodes,
        "edges": edges,
        "gaps": gaps,
        "claim": (
            "typed projection of declared wheel axioms; not an axiom proof, "
            "a spoke derivation, a physical route or a fabrication netlist"
        ),
    }


def render_text(graph: Mapping[str, Any]) -> str:
    counts = graph.get("counts", {})
    lines = [
        "GLOBAL AXIOM GRAPH",
        "=" * 72,
        f"schema: {graph.get('schema')}",
        f"status: {graph.get('status')}",
        (
            f"wheels: {counts.get('wheels')}  axioms: {counts.get('axioms')}  "
            f"quantities: {counts.get('quantities')}  "
            f"dimensions: {counts.get('dimensions')}"
        ),
        (
            f"edges: contains={counts.get('contains')}  "
            f"mentions={counts.get('mentions')}  "
            f"typed_as={counts.get('typed_as')}  "
            f"junctions={counts.get('junction_edges')}/"
            f"{counts.get('junction_declared')}  "
            f"non-identities={counts.get('non_identity_edges')}/"
            f"{counts.get('non_identity_declared')}"
        ),
        f"identity: {graph.get('identity_policy')}",
        f"shared names kept wheel-local: {counts.get('shared_names')}",
    ]
    gaps = graph.get("gaps") or []
    lines.append(f"gaps: {len(gaps)}")
    for gap in gaps:
        lines.append(f"  - {gap.get('kind')}: {gap.get('detail', '')}")
    return "\n".join(lines)


# ===========================================================================
# Derivation over the flattened graph
# ===========================================================================


class DerivationLookupError(ValueError):
    """A requested derivation quantity cannot be resolved unambiguously."""


def _quantity_nodes(graph: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {
        node["id"]: node
        for node in graph["nodes"]
        if node["kind"] == "quantity"
    }


def _resolve_quantity(
    graph: Mapping[str, Any], reference: str, role: str
) -> str:
    text = str(reference).strip()
    if not text:
        raise DerivationLookupError(f"{role} quantity is empty")
    nodes = _quantity_nodes(graph)
    if text in nodes:
        return text
    if text.startswith("quantity:"):
        qid = text
    elif "." in text:
        qid = "quantity:" + text.replace(".", ":", 1)
    else:
        matches = sorted(
            node["id"]
            for node in nodes.values()
            if node["data"].get("name") == text
        )
        if len(matches) == 1:
            return matches[0]
        if not matches:
            raise DerivationLookupError(
                f"unknown {role} quantity {text!r}; use a wheel-qualified name "
                "such as W1.power"
            )
        shown = ", ".join(matches[:8])
        raise DerivationLookupError(
            f"ambiguous {role} quantity {text!r}; qualify it with a wheel "
            f"({shown})"
        )
    if qid not in nodes:
        raise DerivationLookupError(
            f"unknown {role} quantity {text!r}; no declared quantity node exists"
        )
    return qid


def _identity_classes(
    graph: Mapping[str, Any]
) -> tuple[
    dict[str, str],
    dict[str, list[str]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    """Union declared junction identities and reject declared contradictions."""
    quantity_ids = sorted(_quantity_nodes(graph))
    parent = {qid: qid for qid in quantity_ids}

    def find(qid: str) -> str:
        root = qid
        while parent[root] != root:
            root = parent[root]
        while parent[qid] != qid:
            nxt = parent[qid]
            parent[qid] = root
            qid = nxt
        return root

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    resolved_junctions = []
    for edge in graph["edges"]:
        if edge["kind"] != "junction":
            continue
        source, target = edge["source"], edge["target"]
        if source in parent and target in parent:
            union(source, target)
            resolved_junctions.append(edge)

    conflicts = []
    for edge in graph["edges"]:
        if edge["kind"] != "non_identity":
            continue
        source, target = edge["source"], edge["target"]
        if source in parent and target in parent and find(source) == find(target):
            conflicts.append(edge)
    if conflicts:
        raise DerivationLookupError(
            "declared junction identities conflict with a declared non-identity"
        )

    members: dict[str, list[str]] = defaultdict(list)
    by_root: dict[str, str] = {}
    for qid in quantity_ids:
        root = find(qid)
        by_root[qid] = root
        members[root].append(qid)
    labels = {
        root: sorted(
            str(node["label"])
            for node in (
                _quantity_nodes(graph)[qid] for qid in roots
            )
        )
        for root, roots in members.items()
    }
    return by_root, labels, resolved_junctions, conflicts


def _neighbour_wheels(graph: Mapping[str, Any]) -> dict[str, set[str]]:
    neighbours: dict[str, set[str]] = defaultdict(set)
    for edge in graph["edges"]:
        if edge["kind"] != "junction":
            continue
        a = edge["data"].get("wheel_a")
        b = edge["data"].get("wheel_b")
        if a and b and a != b:
            neighbours[str(a)].add(str(b))
            neighbours[str(b)].add(str(a))
    return neighbours


def _solve_linear(
    rows: Sequence[Sequence[Fraction]], rhs: Sequence[Fraction], nvars: int
) -> list[Fraction] | None:
    """Solve an exact rectangular linear system; free variables become zero."""
    aug = [
        [Fraction(value) for value in row] + [Fraction(value)]
        for row, value in zip(rows, rhs)
    ]
    pivots: list[int] = []
    pivot_row = 0
    for column in range(nvars):
        found = next(
            (i for i in range(pivot_row, len(aug)) if aug[i][column]),
            None,
        )
        if found is None:
            continue
        aug[pivot_row], aug[found] = aug[found], aug[pivot_row]
        pivot = aug[pivot_row][column]
        aug[pivot_row] = [value / pivot for value in aug[pivot_row]]
        for i in range(len(aug)):
            if i != pivot_row and aug[i][column]:
                factor = aug[i][column]
                aug[i] = [
                    value - factor * base
                    for value, base in zip(aug[i], aug[pivot_row])
                ]
        pivots.append(column)
        pivot_row += 1
        if pivot_row == len(aug):
            break
    for row in aug:
        if all(value == 0 for value in row[:nvars]) and row[nvars] != 0:
            return None
    solution = [Fraction(0)] * nvars
    for i, column in enumerate(pivots):
        solution[column] = aug[i][nvars]
    return solution


def _fraction(value: Any) -> str:
    item = Fraction(value)
    return f"{item.numerator}/{item.denominator}"


def _derivation_base(
    graph: Mapping[str, Any],
    target_qid: str,
    input_qids: Sequence[str],
    candidate_wheels: Sequence[str],
    candidate_axioms: int,
    max_axioms: int,
) -> dict[str, Any]:
    labels = {
        node["id"]: node["label"]
        for node in graph["nodes"]
        if node["kind"] == "quantity"
    }
    return {
        "schema": DERIVATION_SCHEMA,
        "status": "gap",
        "strategy": "direct",
        "target": labels.get(target_qid, target_qid),
        "target_qid": target_qid,
        "inputs": [labels.get(qid, qid) for qid in input_qids],
        "input_qids": list(input_qids),
        "formula": None,
        "coefficient": None,
        "support": 0,
        "max_support": max_axioms,
        "candidate_wheels": list(candidate_wheels),
        "candidate_axioms": candidate_axioms,
        "used_axioms": [],
        "used_junctions": [],
        "input_exponents": [],
        "unused_inputs": [],
        "k": 1,
        "returned": 0,
        "alternatives": [],
        "proof_steps": [],
        "assumptions": [
            "declared wheel axioms only",
            "declared junction identities only",
            "exact relation-vector algebra, not a physical proof",
        ],
        "missing_bridges": [],
        "gaps": [],
        "scope": (
            "target and input wheels plus one declared-junction hop; "
            "sparse exact support within max_support"
        ),
        "identity_policy": (
            "junction identities are transitive; non-identities are barriers; "
            "missing endpoints are never invented"
        ),
        "claim": (
            "exact relation-vector derivation over declared wheel axioms; "
            "not a physical proof, a route or a fabricated device"
        ),
    }


def _gap(
    payload: dict[str, Any],
    reason: str,
) -> dict[str, Any]:
    payload["status"] = "gap"
    payload["gaps"] = [reason]
    return payload


def _solve_subset(
    graph: Mapping[str, Any],
    target_root: str,
    input_roots: Sequence[str],
    input_labels: Sequence[str],
    selected: Sequence[Mapping[str, Any]],
    class_of: Mapping[str, str],
    resolved_junctions: Sequence[Mapping[str, Any]],
    payload: dict[str, Any],
) -> dict[str, Any] | None:
    n = len(selected)
    input_index = {root: i for i, root in enumerate(input_roots)}
    relations = []
    scalars = []
    for node in selected:
        data = node["data"]
        relation: dict[str, Fraction] = defaultdict(Fraction)
        for name, exponent in data["relation"].items():
            qid = f"quantity:{data['wheel']}:{name}"
            root = class_of.get(qid)
            if root is None:
                return None
            relation[root] += Fraction(exponent)
        relations.append(
            {root: value for root, value in relation.items() if value}
        )
        scalars.append(
            {
                str(key): Fraction(value)
                for key, value in data.get("scalars", {}).items()
            }
        )

    classes = {target_root, *input_roots}
    for relation in relations:
        classes.update(relation)
    rows: list[list[Fraction]] = []
    rhs: list[Fraction] = []
    for root in sorted(classes):
        row = [Fraction(0)] * (n + len(input_roots))
        for i, relation in enumerate(relations):
            row[i] = relation.get(root, Fraction(0))
        if root == target_root:
            rhs.append(Fraction(1))
        elif root in input_index:
            row[n + input_index[root]] = Fraction(-1)
            rhs.append(Fraction(0))
        else:
            rhs.append(Fraction(0))
        rows.append(row)
    solution = _solve_linear(rows, rhs, n + len(input_roots))
    if solution is None:
        return None
    weights = solution[:n]
    if any(weight == 0 for weight in weights):
        return None

    combo: dict[str, Fraction] = defaultdict(Fraction)
    scalar_combo: dict[str, Fraction] = defaultdict(Fraction)
    for weight, relation, scalar in zip(weights, relations, scalars):
        for root, value in relation.items():
            combo[root] += weight * value
        for key, value in scalar.items():
            scalar_combo[key] += weight * value
    if combo.get(target_root, Fraction(0)) != 1:
        return None
    if any(
        combo.get(root, Fraction(0)) != 0
        for root in combo
        if root != target_root and root not in input_index
    ):
        return None

    powers = []
    input_exponents = []
    used_inputs = []
    unused_inputs = []
    for root, label in zip(input_roots, input_labels):
        exponent = -combo.get(root, Fraction(0))
        input_exponents.append({"quantity": label, "exponent": _fraction(exponent)})
        if exponent:
            powers.append((label, exponent))
            used_inputs.append(label)
        else:
            unused_inputs.append(label)
    if not powers:
        return None

    primes = {
        int(key[1:]): -value
        for key, value in scalar_combo.items()
        if key.startswith("#") and value
    }
    formula = render_monomial(primes, powers)
    coefficient = render_monomial(primes, [])

    # Report only the declared junction edges that connect an axiom's raw
    # quantity label to one of the requested target/input labels.  Merely
    # sharing a transitive class is not enough to claim an edge was used.
    requested = [str(payload.get("target_qid", ""))] + [
        str(qid) for qid in payload.get("input_qids", [])
    ]
    by_pair = {
        tuple(sorted((edge["source"], edge["target"]))): edge
        for edge in resolved_junctions
    }
    adjacency: dict[str, set[str]] = defaultdict(set)
    for source, target in by_pair:
        adjacency[source].add(target)
        adjacency[target].add(source)

    def junction_path(raw: str, root: str) -> list[tuple[str, str]]:
        wanted = {qid for qid in requested if class_of.get(qid) == root}
        if raw in wanted:
            return []
        queue = [(raw, [])]
        seen = {raw}
        while queue:
            current, path = queue.pop(0)
            for other in sorted(adjacency.get(current, ())):
                if other in seen:
                    continue
                if class_of.get(other) != root:
                    continue
                pair = (min(current, other), max(current, other))
                next_path = path + [pair]
                if other in wanted:
                    return next_path
                seen.add(other)
                queue.append((other, next_path))
        return []

    used_pairs: set[tuple[str, str]] = set()
    raw_qids = {
        f"quantity:{node['data']['wheel']}:{name}"
        for node in selected
        for name in node["data"]["relation"]
    }
    for raw in sorted(raw_qids):
        root = class_of.get(raw)
        if root not in {target_root, *input_roots}:
            continue
        used_pairs.update(junction_path(raw, root))
    used_junctions = [by_pair[pair] for pair in sorted(used_pairs)]
    payload.update(
        {
            "status": "derived",
            "formula": formula,
            "coefficient": coefficient,
            "support": n,
            "used_axioms": [
                {
                    "id": node["id"],
                    "wheel": node["data"]["wheel"],
                    "index": node["data"]["index"],
                    "equation": node["data"]["equation"],
                    "weight": _fraction(weight),
                }
                for node, weight in zip(selected, weights)
            ],
            "used_junctions": [
                {
                    "source": edge["source"],
                    "target": edge["target"],
                    "wheel_a": edge["data"].get("wheel_a"),
                    "wheel_b": edge["data"].get("wheel_b"),
                    "reason": edge["data"].get("reason"),
                }
                for edge in used_junctions
            ],
            "input_exponents": input_exponents,
            "used_inputs": used_inputs,
            "unused_inputs": unused_inputs,
            "gaps": [],
        }
    )
    return payload


def _proof_steps(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Turn the selected axioms and declared junctions into proof steps."""
    steps: list[dict[str, Any]] = []
    for item in payload.get("used_axioms") or []:
        steps.append(
            {
                "kind": "axiom",
                "id": item.get("id"),
                "wheel": item.get("wheel"),
                "equation": item.get("equation"),
                "weight": item.get("weight"),
            }
        )
    for item in payload.get("used_junctions") or []:
        steps.append(
            {
                "kind": "junction",
                "source": item.get("source"),
                "target": item.get("target"),
                "reason": item.get("reason"),
            }
        )
    return steps


def _missing_bridges(
    target_root: str,
    input_roots: Sequence[str],
    class_labels: Mapping[str, Sequence[str]],
) -> list[dict[str, Any]]:
    """Report which requested components have no declared bridge."""
    return [
        {
            "target_component": target_root,
            "input_component": root,
            "target_labels": list(class_labels.get(target_root, [])),
            "input_labels": list(class_labels.get(root, [])),
            "detail": (
                "no declared junction identity connects these components "
                "inside the selected scope"
            ),
        }
        for root in input_roots
        if root != target_root
    ]


def _substitution_search(
    graph: Mapping[str, Any],
    target_qid: str,
    input_qids: Sequence[str],
    target_root: str,
    input_roots: Sequence[str],
    class_of: Mapping[str, str],
    class_labels: Mapping[str, Sequence[str]],
    resolved_junctions: Sequence[Mapping[str, Any]],
    payload: dict[str, Any],
    *,
    max_axioms: int,
    candidate_wheels: Sequence[str],
) -> dict[str, Any] | None:
    """Find a bounded backward-substitution proof over declared axioms.

    Each step picks one declared equation, solves it for one quantity class
    whose dependencies are already inputs or earlier substitutions, and records
    the exact exponent and scalar transformation.  The selected axioms are
    then checked by the same exact linear solver used by the direct path; a
    path that does not reproduce an exact combination is discarded.  Junction
    identities are used only through ``class_of``; no quantity or edge is
    invented.
    """
    allowed = set(candidate_wheels)
    nodes = [
        node
        for node in graph["nodes"]
        if node["kind"] == "axiom" and node["data"]["wheel"] in allowed
    ]
    if not nodes:
        return None
    records: dict[str, tuple[Mapping[str, Any], dict[str, Fraction]]] = {}
    by_root: dict[str, list[str]] = defaultdict(list)
    node_by_id = {node["id"]: node for node in nodes}
    for node in nodes:
        data = node["data"]
        relation: dict[str, Fraction] = defaultdict(Fraction)
        for name, exponent in data["relation"].items():
            qid = f"quantity:{data['wheel']}:{name}"
            root = class_of.get(qid)
            if root is not None:
                relation[root] += Fraction(exponent)
        relation = {root: value for root, value in relation.items() if value}
        records[node["id"]] = (node, relation)
        for root in relation:
            by_root[root].append(node["id"])
    for root in by_root:
        by_root[root].sort(
            key=lambda node_id: (
                len(records[node_id][1]),
                node_id,
            )
        )

    input_set = set(input_roots)

    def label(root: str) -> str:
        labels = class_labels.get(root) or (root,)
        return str(labels[0])

    def step_for(
        node: Mapping[str, Any], relation: Mapping[str, Fraction], root: str
    ) -> dict[str, Any]:
        data = node["data"]
        target_exponent = relation[root]
        powers: list[tuple[str, Fraction]] = []
        from_items: list[dict[str, str]] = []
        for other in sorted(relation):
            if other == root:
                continue
            exponent = -relation[other] / target_exponent
            item_label = label(other)
            powers.append((item_label, exponent))
            from_items.append(
                {"quantity": item_label, "exponent": _fraction(exponent)}
            )
        primes = {
            int(key[1:]): Fraction(value) / target_exponent
            for key, value in data.get("scalars", {}).items()
            if key.startswith("#")
        }
        return {
            "kind": "substitution",
            "axiom": node["id"],
            "wheel": data["wheel"],
            "equation": data["equation"],
            "derives": label(root),
            "target_exponent": _fraction(target_exponent),
            "from": from_items,
            "formula": render_monomial(primes, powers),
            "coefficient": render_monomial(primes, []),
        }

    def prove(
        root: str,
        budget: int,
        visiting: frozenset[str],
        used: frozenset[str],
    ) -> tuple[frozenset[str], list[dict[str, Any]]] | None:
        if root in input_set:
            return used, []
        if budget <= 0 or root in visiting:
            return None
        for node_id in by_root.get(root, ()):
            if node_id in used:
                continue
            node, relation = records[node_id]
            others = [other for other in relation if other != root]
            if not others:
                continue
            new_used = set(used)
            new_used.add(node_id)
            if len(new_used) > budget:
                continue
            steps: list[dict[str, Any]] = []
            new_visiting = visiting | {root}
            ok = True
            for other in sorted(
                others,
                key=lambda item: (
                    0 if item in input_set else len(by_root.get(item, ())),
                    item,
                ),
            ):
                result = prove(
                    other,
                    budget - 1,
                    new_visiting,
                    frozenset(new_used),
                )
                if result is None:
                    ok = False
                    break
                sub_used, sub_steps = result
                new_used.update(sub_used)
                if len(new_used) > budget:
                    ok = False
                    break
                steps.extend(sub_steps)
            if not ok:
                continue
            steps.append(step_for(node, relation, root))
            return frozenset(new_used), steps
        return None

    found = prove(target_root, max_axioms, frozenset(), frozenset())
    if found is None:
        return None
    selected_ids, steps = found
    ordered_ids = list(dict.fromkeys(step["axiom"] for step in steps))
    selected = [node_by_id[node_id] for node_id in ordered_ids]
    solved = _solve_subset(
        graph,
        target_root,
        input_roots,
        [str(payload["inputs"][index]) for index in range(len(input_roots))],
        selected,
        class_of,
        resolved_junctions,
        payload.copy(),
    )
    if solved is None:
        return None
    used_ids = {item["id"] for item in solved.get("used_axioms") or []}
    if used_ids != selected_ids:
        return None
    weights = {
        item["id"]: item.get("weight")
        for item in solved.get("used_axioms") or []
    }
    for step in steps:
        step["weight"] = weights.get(step["axiom"])
    junction_steps = [
        {
            "kind": "junction",
            "source": item.get("source"),
            "target": item.get("target"),
            "reason": item.get("reason"),
        }
        for item in solved.get("used_junctions") or []
    ]
    solved.update(
        {
            "candidate_axioms": len(nodes),
            "candidate_wheels": sorted(allowed),
            "scope": (
                f"bounded backward substitution across {len(nodes)} declared "
                f"axiom(s) in {', '.join(sorted(allowed))}; at most "
                f"{max_axioms} substitution(s); declared junction identities only"
            ),
            "strategy": "substitution",
            "proof_steps": steps + junction_steps,
            "proof_depth": len(steps),
            "intermediate_quantities": [step["derives"] for step in steps[:-1]],
            "returned": 1,
            "alternatives": [],
            "k": 1,
            "assumptions": list(payload.get("assumptions") or [])
            + [
                "each substitution solves one declared quantity from already-derived quantities",
                "the selected substitution axioms are rechecked by exact relation-vector algebra",
            ],
            "gaps": [],
            "missing_bridges": [],
        }
    )
    return solved


def derive_from(
    target: str,
    inputs: Sequence[str],
    *,
    allowed_wheels: Sequence[str] | None = None,
    max_axioms: int = 4,
    junction_hops: int = DIRECT_JUNCTION_HOPS,
    k: int = 1,
    strategy: str = "auto",
) -> dict[str, Any]:
    """Derive a wheel quantity from any number of inputs over the global graph.

    The graph contributes the exact axiom relation vectors and only the
    declared junction identities.  ``strategy="direct"`` keeps the original
    target/input plus one-junction-hop linear enumeration.  ``strategy="auto"``
    tries that direct path first, then a bounded backward-substitution search
    over the requested wheel scope.  ``strategy="substitution"`` forces the
    substitution path and records each exact substitution step.  Exact support
    is bounded by ``max_axioms``; a missing or ambiguous quantity raises
    ``DerivationLookupError``, while a well-formed request with no derivation
    returns ``status: gap``.

    The legacy ``wheels.derive_from`` remains the one-wheel, two-input helper
    used to generate the 366-spoke regression corpus.  This is the graph-level
    generalization and does not alter that corpus.
    """
    if isinstance(inputs, str):
        inputs = [inputs]
    input_refs = [str(item) for item in inputs]
    if not input_refs:
        raise DerivationLookupError("at least one input quantity is required")
    if not 1 <= max_axioms <= MAX_DERIVATION_AXIOMS:
        raise ValueError(
            f"max_axioms must be between 1 and {MAX_DERIVATION_AXIOMS}"
        )
    if not 0 <= junction_hops <= 2:
        raise ValueError("junction_hops must be between 0 and 2")
    if not 1 <= k <= MAX_DERIVATIONS:
        raise ValueError(f"k must be between 1 and {MAX_DERIVATIONS}")
    if strategy not in {"auto", "direct", "substitution"}:
        raise ValueError("strategy must be 'auto', 'direct' or 'substitution'")

    graph = build_axiom_graph()
    target_qid = _resolve_quantity(graph, target, "target")
    input_qids = [_resolve_quantity(graph, ref, "input") for ref in input_refs]
    class_of, class_labels, resolved_junctions, _ = _identity_classes(graph)
    target_root = class_of[target_qid]
    input_roots = [class_of[qid] for qid in input_qids]
    if target_root in input_roots:
        raise DerivationLookupError(
            "the target and an input are the same declared quantity"
        )
    if len(set(input_roots)) != len(input_roots):
        raise DerivationLookupError(
            "two inputs are the same declared quantity"
        )

    input_labels = [str(_quantity_nodes(graph)[qid]["label"]) for qid in input_qids]
    target_label = str(_quantity_nodes(graph)[target_qid]["label"])
    target_wheel = str(_quantity_nodes(graph)[target_qid]["data"]["wheel"])
    input_wheels = {
        str(_quantity_nodes(graph)[qid]["data"]["wheel"]) for qid in input_qids
    }
    if allowed_wheels:
        candidate_wheels = sorted({str(w).upper() for w in allowed_wheels})
        unknown = [
            w for w in candidate_wheels
            if w not in {wheel.id for wheel in WHEELS}
        ]
        if unknown:
            raise DerivationLookupError(
                "unknown wheel in --wheel: " + ", ".join(unknown)
            )
        if target_wheel not in candidate_wheels or not input_wheels <= set(candidate_wheels):
            raise DerivationLookupError(
                "target and input wheels must all be included in --wheel"
            )
    else:
        active = {target_wheel, *input_wheels}
        neighbours = _neighbour_wheels(graph)
        frontier = set(active)
        for _ in range(junction_hops):
            added = {
                other for wheel in frontier for other in neighbours.get(wheel, set())
            }
            active.update(added)
            frontier = added
        candidate_wheels = sorted(active)

    candidate_nodes = sorted(
        (
            node
            for node in graph["nodes"]
            if node["kind"] == "axiom"
            and node["data"]["wheel"] in candidate_wheels
        ),
        key=lambda node: (node["data"]["wheel"], node["data"]["index"]),
    )
    payload = _derivation_base(
        graph,
        target_qid,
        input_qids,
        candidate_wheels,
        len(candidate_nodes),
        max_axioms,
    )
    payload["target"] = target_label
    payload["inputs"] = input_labels

    if strategy == "substitution":
        scope_wheels = (
            candidate_wheels
            if allowed_wheels
            else sorted({node["data"]["wheel"] for node in graph["nodes"] if node["kind"] == "axiom"})
        )
        found = _substitution_search(
            graph,
            target_qid,
            input_qids,
            target_root,
            input_roots,
            class_of,
            class_labels,
            resolved_junctions,
            payload,
            max_axioms=max_axioms,
            candidate_wheels=scope_wheels,
        )
        if found is not None:
            return found
        return _gap(
            payload,
            (
                f"no exact substitution path of at most {max_axioms} axiom(s) "
                f"in {', '.join(scope_wheels)} derives {target_label} from "
                f"{', '.join(input_labels)}"
            ),
        )

    if not candidate_nodes:
        return _gap(payload, "no declared axioms in the candidate wheel scope")
    if len(candidate_nodes) > MAX_CANDIDATE_AXIOMS:
        if strategy == "auto":
            scope_wheels = sorted(
                {node["data"]["wheel"] for node in graph["nodes"] if node["kind"] == "axiom"}
            )
            found = _substitution_search(
                graph,
                target_qid,
                input_qids,
                target_root,
                input_roots,
                class_of,
                class_labels,
                resolved_junctions,
                payload,
                max_axioms=max_axioms,
                candidate_wheels=scope_wheels,
            )
            if found is not None:
                return found
        return _gap(
            payload,
            (
                f"candidate scope has {len(candidate_nodes)} axioms, above the "
                f"bound of {MAX_CANDIDATE_AXIOMS}; narrow it with --wheel"
            ),
        )

    candidates = []
    for node in candidate_nodes:
        data = node["data"]
        roots = set()
        for name in data["relation"]:
            qid = f"quantity:{data['wheel']}:{name}"
            root = class_of.get(qid)
            if root is not None:
                roots.add(root)
        candidates.append({"node": node, "roots": roots, "relation": data["relation"]})

    parent = {root: root for root in set(class_of.values())}

    def find(root: str) -> str:
        while parent[root] != root:
            parent[root] = parent[parent[root]]
            root = parent[root]
        return root

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    for item in candidates:
        roots = list(item["roots"])
        for other in roots[1:]:
            union(roots[0], other)
    target_component = find(target_root)
    if any(find(root) != target_component for root in input_roots):
        payload = _gap(
            payload,
            "target and inputs are in disjoint declared-axiom components in this scope",
        )
        payload["missing_bridges"] = _missing_bridges(
            target_component, input_roots, class_labels
        )
        return payload

    relevant = [item for item in candidates if find(next(iter(item["roots"]))) == target_component]
    nodes = [item["node"] for item in relevant]
    solutions: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for size in range(1, min(max_axioms, len(nodes)) + 1):
        for subset in combinations(nodes, size):
            solved = _solve_subset(
                graph,
                target_root,
                input_roots,
                input_labels,
                subset,
                class_of,
                resolved_junctions,
                payload.copy(),
            )
            if solved is None:
                continue
            key = (
                solved.get("formula"),
                tuple(item["id"] for item in solved.get("used_axioms") or []),
                tuple(
                    (item.get("source"), item.get("target"))
                    for item in solved.get("used_junctions") or []
                ),
            )
            if key in seen:
                continue
            seen.add(key)
            solved["candidate_axioms"] = len(nodes)
            solved["k"] = k
            solved["returned"] = len(solutions) + 1
            solved["proof_steps"] = _proof_steps(solved)
            solutions.append(solved)
            if len(solutions) >= k:
                break
        if len(solutions) >= k:
            break

    if not solutions:
        if strategy == "auto":
            scope_wheels = (
                candidate_wheels
                if allowed_wheels
                else sorted(
                    {node["data"]["wheel"] for node in graph["nodes"] if node["kind"] == "axiom"}
                )
            )
            found = _substitution_search(
                graph,
                target_qid,
                input_qids,
                target_root,
                input_roots,
                class_of,
                class_labels,
                resolved_junctions,
                payload,
                max_axioms=max_axioms,
                candidate_wheels=scope_wheels,
            )
            if found is not None:
                return found
        return _gap(
            payload,
            (
                f"no exact relation-vector combination of at most {max_axioms} "
                f"declared axioms in {', '.join(candidate_wheels)} derives "
                f"{target_label} from {', '.join(input_labels)}"
            ),
        )

    best = solutions[0]
    best["returned"] = len(solutions)
    best["alternatives"] = solutions[1:]
    return best


def _grounding_targets(
    relation: Mapping[str, Fraction], kind: str
) -> list[str]:
    """Return exact target names for one declared relation shape."""
    positives = [name for name, value in relation.items() if value > 0]
    negatives = [name for name, value in relation.items() if value < 0]
    if kind == "half-exponent":
        if not any(abs(value) == Fraction(1, 2) for value in relation.values()):
            return []
        return positives
    if kind == "product":
        if len(positives) != 1 or len(negatives) < 2:
            return []
        return positives
    return []


@lru_cache(maxsize=64)
def ground_primitive(primitive: str, limit: int = 8) -> dict[str, Any]:
    """Ground a primitive in declared axiom relations, not text hits.

    A candidate is accepted only when its exact relation has the requested
    algebraic shape and ``derive_from`` re-derives the target from the other
    quantities using exactly that one declared axiom.  This proves a monomial
    relation; it does not prove a physical analogy, a nonlinear bridge or a
    route applicability claim.  Primitives without a declared relation query
    return a gap rather than falling back to keyword text.
    """
    if not 1 <= limit <= 32:
        raise ValueError("limit must be between 1 and 32")
    query = RELATION_QUERIES.get(primitive)
    payload: dict[str, Any] = {
        "schema": GROUNDING_SCHEMA,
        "primitive": primitive,
        "status": "gap",
        "basis": "graph-proof",
        "query": dict(query or {}),
        "candidates": [],
        "gaps": [],
        "claim": (
            "exact declared monomial relation and derivation; not a physical "
            "bridge, route proof or fabricated device"
        ),
    }
    if query is None:
        payload["gaps"] = [
            f"no declared monomial relation query for primitive {primitive!r}; "
            "text matches are not promoted to graph grounding"
        ]
        return payload

    graph = build_axiom_graph()
    quantity_nodes = _quantity_nodes(graph)
    wheel_titles = {
        str(node["id"]).removeprefix("wheel:"): str(node.get("label", node["id"]))
        for node in graph["nodes"]
        if node["kind"] == "wheel"
    }
    candidates: list[dict[str, Any]] = []
    for node in sorted(
        (node for node in graph["nodes"] if node["kind"] == "axiom"),
        key=lambda item: (item["data"]["wheel"], item["data"]["index"]),
    ):
        data = node["data"]
        relation = {
            name: Fraction(value) for name, value in data["relation"].items()
        }
        for target in _grounding_targets(relation, query["kind"]):
            inputs = [name for name in relation if name != target]
            if not inputs:
                continue
            target_qid = f"quantity:{data['wheel']}:{target}"
            input_qids = [f"quantity:{data['wheel']}:{name}" for name in inputs]
            target_ref = f"{data['wheel']}.{target}"
            input_refs = [f"{data['wheel']}.{name}" for name in inputs]
            try:
                proof = derive_from(
                    target_ref,
                    input_refs,
                    allowed_wheels=[data["wheel"]],
                    max_axioms=1,
                    strategy="direct",
                )
            except (DerivationLookupError, ValueError):
                continue
            if (
                proof.get("status") != "derived"
                or proof.get("support") != 1
                or [item.get("id") for item in proof.get("used_axioms") or []]
                != [node["id"]]
            ):
                continue
            candidates.append(
                {
                    "wheel": data["wheel"],
                    "title": wheel_titles.get(data["wheel"], data["wheel"]),
                    "axiom_id": node["id"],
                    "equation": data["equation"],
                    "target": str(quantity_nodes[target_qid]["label"]),
                    "inputs": [
                        str(quantity_nodes[ref]["label"]) for ref in input_qids
                    ],
                    "relation": {
                        name: _fraction(value) for name, value in relation.items()
                    },
                    "formula": proof.get("formula"),
                    "coefficient": proof.get("coefficient"),
                    "input_exponents": proof.get("input_exponents"),
                    "proof_steps": proof.get("proof_steps"),
                    "status": "derived",
                    "basis": "graph-proof",
                }
            )
            break
    payload["candidates"] = candidates[:limit]
    if candidates:
        payload["status"] = "derived"
        payload["gaps"] = []
    else:
        payload["gaps"] = [
            f"no declared axiom matches the {query['kind']} relation query for "
            f"primitive {primitive!r}"
        ]
    return payload


def _strip_wheel_prefixes(text: str) -> str:
    return re.sub(r"\bW\d+\.", "", str(text))


def regress_legacy_spokes() -> dict[str, Any]:
    """Re-derive the legacy 366 two-input spoke corpus over the graph.

    The legacy helper permits an extra input whose coefficient is zero.  Such
    a spoke is a formula on a subset of its declared inputs, and the graph
    correctly refuses the disconnected extra input.  This regression asks
    the graph for the inputs the formula actually uses, compares the exact
    formula, and reports those redundant legacy entries explicitly.
    """
    total = derived = formula_matches = 0
    extra_by_wheel: dict[str, int] = defaultdict(int)
    extra_examples: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []
    mismatches: list[dict[str, Any]] = []
    wheel_reports: list[dict[str, Any]] = []

    for wheel in WHEELS:
        wheel_total = 0
        wheel_derived = 0
        for target in wheel_quantities(wheel):
            for spoke in wheel_spokes(wheel, target):
                total += 1
                wheel_total += 1
                used_inputs = [
                    name for name, exponent in spoke.exponents if exponent
                ]
                unused_inputs = [
                    name for name in spoke.inputs if name not in used_inputs
                ]
                if unused_inputs:
                    extra_by_wheel[wheel.id] += 1
                    if len(extra_examples) < 5:
                        extra_examples.append(
                            {
                                "wheel": wheel.id,
                                "formula": spoke.text(),
                                "declared_inputs": list(spoke.inputs),
                                "used_inputs": used_inputs,
                                "unused_inputs": unused_inputs,
                            }
                        )
                try:
                    payload = derive_from(
                        f"{wheel.id}.{spoke.target}",
                        [f"{wheel.id}.{name}" for name in used_inputs],
                        allowed_wheels=[wheel.id],
                        max_axioms=MAX_DERIVATION_AXIOMS,
                    )
                except (DerivationLookupError, ValueError) as exc:
                    gaps.append(
                        {
                            "wheel": wheel.id,
                            "formula": spoke.text(),
                            "used_inputs": used_inputs,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    )
                    continue
                if payload.get("status") != "derived":
                    gaps.append(
                        {
                            "wheel": wheel.id,
                            "formula": spoke.text(),
                            "used_inputs": used_inputs,
                            "reason": payload.get("gaps"),
                        }
                    )
                    continue
                derived += 1
                wheel_derived += 1
                graph_formula = _strip_wheel_prefixes(payload.get("formula") or "")
                legacy_formula = _strip_wheel_prefixes(spoke.formula)
                if graph_formula == legacy_formula:
                    formula_matches += 1
                else:
                    mismatches.append(
                        {
                            "wheel": wheel.id,
                            "formula": spoke.text(),
                            "graph_formula": payload.get("formula"),
                            "legacy_formula": spoke.formula,
                        }
                    )
        wheel_reports.append(
            {
                "wheel": wheel.id,
                "spokes": wheel_total,
                "derived": wheel_derived,
            }
        )

    status = "ok" if total == derived == formula_matches and not gaps and not mismatches else "gap"
    return {
        "schema": SPOKE_REGRESSION_SCHEMA,
        "status": status,
        "total_spokes": total,
        "derived": derived,
        "formula_matches": formula_matches,
        "extra_input_spokes": sum(extra_by_wheel.values()),
        "extra_by_wheel": dict(sorted(extra_by_wheel.items())),
        "extra_examples": extra_examples,
        "wheel_reports": wheel_reports,
        "gaps": gaps,
        "mismatches": mismatches,
        "claim": (
            "formula-level regression over the legacy 366-spoke corpus; "
            "spokes with a redundant unused input are reported, and the graph "
            "is asked only for the inputs the formula uses"
        ),
    }


def render_derivation(payload: Mapping[str, Any]) -> str:
    lines = [
        "GRAPH DERIVATION",
        "=" * 72,
        f"schema: {payload.get('schema')}",
        f"status: {payload.get('status')}",
        f"target: {payload.get('target')}",
        f"inputs: {', '.join(payload.get('inputs') or [])}",
        f"scope: {payload.get('scope')}",
    ]
    if payload.get("status") == "derived":
        lines.append(f"formula: {payload.get('target')} = {payload.get('formula')}")
        lines.append(f"coefficient: {payload.get('coefficient')}")
        lines.append(
            "support: {} axiom(s), {} candidate(s) in {}".format(
                payload.get("support"),
                payload.get("candidate_axioms"),
                ", ".join(payload.get("candidate_wheels") or []),
            )
        )
        lines.append(f"paths returned: {payload.get('returned', 1)}")
        for index, alternative in enumerate(payload.get("alternatives") or [], 2):
            lines.append(
                f"  path {index}: {alternative.get('target')} = "
                f"{alternative.get('formula')}"
            )
        for step in payload.get("proof_steps") or []:
            if step.get("kind") == "substitution":
                lines.append(
                    f"  substitute {step.get('axiom')}: derive {step.get('derives')} "
                    f"from {', '.join(item.get('quantity', '') for item in step.get('from') or [])}"
                )
        for axiom in payload.get("used_axioms") or []:
            lines.append(
                f"  axiom {axiom['id']} (weight {axiom['weight']}): {axiom['equation']}"
            )
        for junction in payload.get("used_junctions") or []:
            lines.append(
                "  junction {} <-> {}: {}".format(
                    junction.get("source"),
                    junction.get("target"),
                    junction.get("reason"),
                )
            )
        unused = payload.get("unused_inputs") or []
        if unused:
            lines.append("unused inputs: " + ", ".join(unused))
    else:
        lines.append(f"inputs: {', '.join(payload.get('inputs') or [])}")
        for gap in payload.get("gaps") or []:
            lines.append(f"gap: {gap}")
        for bridge in payload.get("missing_bridges") or []:
            lines.append(
                "missing bridge: {} -> {} ({})".format(
                    bridge.get("input_component"),
                    bridge.get("target_component"),
                    bridge.get("detail"),
                )
            )
    return "\n".join(lines)


__all__ = [
    "DERIVATION_SCHEMA",
    "DerivationLookupError",
    "GROUNDING_SCHEMA",
    "RELATION_QUERIES",
    "SCHEMA",
    "build_axiom_graph",
    "derive_from",
    "ground_primitive",
    "regress_legacy_spokes",
    "render_derivation",
    "render_text",
]
