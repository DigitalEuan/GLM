"""Explore abstract ∆ concepts through the exact vocabulary.

The explorer does not invent methods.  Every method is one of the 41 contracts
in :mod:`cent_compiler.vocabulary`; its "exact path" is read from the contract
and the evaluator dispatch table, its simulation evidence is a small explicit
map onto :mod:`cent_compiler.simulator`, and its application evidence is a
short list of existing proposals/demos.  Wheel links are *text matches* only
(axioms, cases and quantities), never a claim that a wheel proves the method.

A query returns a tree of branches with ``pass`` / ``gap`` / ``stop`` / ``out``
statuses so the first missing stage is visible.  Unknown queries return
suggestions instead of a fabricated answer.
"""
from __future__ import annotations

import difflib
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

from . import vocabulary
from .evaluator import HANDLERS

WHEELS_DIR = Path(__file__).resolve().parent.parent / "wheels"

PRETTY: dict[str, str] = {
    "sum": "Sum",
    "neg": "Negate",
    "mult": "Multiply",
    "scale": "Scale",
    "accum": "Accumulate / integrate",
    "rate": "Rate / differentiate",
    "wrap": "Phase wrap",
    "spatial": "Spatial sample",
    "exp": "Exponential",
    "log": "Logarithm",
    "sat": "Saturation",
    "hysteresis": "Hysteresis",
    "delay": "Delay",
    "grad": "Gradient",
    "div_spatial": "Divergence",
    "curl": "Curl",
    "laplacian": "Laplacian",
    "boundary": "Boundary condition",
    "junction_0": "0-junction (common flow)",
    "junction_1": "1-junction (common effort)",
    "gyrator": "Gyrator",
    "transformer": "Transformer",
    "dissipate": "Dissipation",
    "store_pot": "Potential storage",
    "store_kin": "Kinetic storage",
    "transduce": "Transducer",
    "noise": "Noise",
    "quantize": "Quantize",
    "entropy": "Entropy production",
    "recip": "Reciprocal",
    "div": "Divide",
    "sqrt": "Square root",
    "eq": "Equilibrium solve",
    "translinear": "Translinear power law",
    "state_space": "State space",
    "pid": "PID control",
    "phase_locked_loop": "Phase-locked loop",
    "transmission_line": "Transmission line",
    "kalman_observer": "Kalman observer",
    "thermo_electric": "Thermoelectric transducer",
    "delta_sigma_modulator": "Delta-sigma modulator",
}

ALIASES: dict[str, tuple[str, ...]] = {
    "delta_sigma_modulator": (
        "delta sigma", "delta-sigma", "∆σ", "δσ", "sigma delta",
        "noise shaping", "noise-shaping", "oversampling", "bitstream",
    ),
    "phase_locked_loop": (
        "pll", "phase lock", "phase-locked", "phase locked", "vco",
        "phase detector", "frequency synthesis",
    ),
    "kalman_observer": ("kalman", "observer", "state estimation", "estimator"),
    "pid": ("pid", "proportional integral derivative", "control loop", "feedback control"),
    "state_space": ("state space", "state-space", "linear system", "matrix system"),
    "translinear": ("translinear", "log domain", "log-domain", "analog calculator"),
    "transmission_line": ("transmission line", "delay line", "telegrapher", "reflection"),
    "thermo_electric": ("thermoelectric", "thermo-electric", "seebeck", "peltier"),
    "sqrt": ("sqrt", "square root", "root extraction"),
    "accum": ("accumulate", "accumulator", "integration", "integrator"),
    "rate": ("differentiate", "differentiation", "derivative"),
    "wrap": ("phase wrap", "phase wrapping", "modulo", "mod 2pi", "mod 2π"),
    "exp": ("exponential", "decay", "growth"),
    "log": ("logarithm", "log compression", "compression"),
    "sat": ("saturation", "limiter", "tanh", "clip", "clipping"),
    "hysteresis": ("hysteresis", "schmitt", "latch", "memory"),
    "delay": ("delay", "echo", "queue"),
    "noise": ("noise", "stochastic", "dither"),
    "quantize": ("quantize", "quantization", "adc"),
    "entropy": ("entropy", "thermodynamic"),
    "grad": ("gradient",),
    "div_spatial": ("divergence",),
    "curl": ("curl", "vorticity"),
    "laplacian": ("laplacian",),
    "boundary": ("boundary condition", "dirichlet", "neumann", "robin"),
    "junction_0": ("0 junction", "common flow", "kirchhoff current"),
    "junction_1": ("1 junction", "common effort", "kirchhoff voltage"),
    "store_pot": ("capacitor", "capacitance", "spring", "potential storage"),
    "store_kin": ("inductor", "inductance", "inertia", "kinetic storage"),
    "dissipate": ("dissipation", "resistance", "friction", "damper"),
    "transduce": ("transducer", "transduction"),
    "gyrator": ("gyrator",),
    "transformer": ("transformer", "gear ratio"),
    "recip": ("reciprocal", "inverse"),
}

#: Conceptual ingredients documented for composites.  These are *not* how the
#: evaluator implements the handler (each composite has a direct handler); they
#: are the decomposition the framework documentation uses.
COMPONENTS: dict[str, tuple[str, ...]] = {
    "recip": ("eq", "mult"),
    "div": ("mult", "recip"),
    "sqrt": ("eq", "mult"),
    "eq": ("mult", "sum"),
    "translinear": ("log", "mult", "exp"),
    "state_space": ("accum", "mult", "sum"),
    "pid": ("sum", "scale", "accum", "rate"),
    "phase_locked_loop": ("accum", "wrap", "sum", "scale"),
    "transmission_line": ("delay", "scale", "sum"),
    "kalman_observer": ("mult", "sum", "div"),
    "thermo_electric": ("mult", "scale", "sum"),
    "delta_sigma_modulator": ("accum", "quantize", "delay"),
}

SIMULATIONS: dict[str, dict[str, str]] = {
    "delta_sigma_modulator": {
        "function": "simulate_delta_sigma_integrator",
        "test": "test_delta_sigma_integration",
        "detail": (
            "float showcase plus the exact typed route simulation in "
            "assembly.delta_sigma_route() and the declared device binding in "
            "device.bind_delta_sigma()"
        ),
    },
    "accum": {
        "function": "simulate_delta_sigma_integrator",
        "test": "test_delta_sigma_integration",
        "detail": "delta-sigma running sum as an integrator; float tolerance",
    },
    "sqrt": {
        "function": "simulate_opamp_sqrt",
        "test": "test_opamp_sqrt",
        "detail": (
            "op-amp feedback convergence to √x (float) plus the exact log-domain "
            "route in assembly.log_domain_sqrt_route(), the exact finite-gain "
            "op-amp feedback route in assembly.opamp_multiplier_sqrt_route(), "
            "and the declared log-domain and feedback device bindings in "
            "device.bind_log_domain_sqrt() and device.bind_feedback_sqrt()"
        ),
    },
    "phase_locked_loop": {
        "function": "simulate_pll",
        "test": "test_pll_wrap",
        "detail": "type-2 PLL phase tracking; float simulation",
    },
    "wrap": {
        "function": "simulate_pll",
        "test": "test_pll_wrap",
        "detail": "PLL phase tracking exercises wrap; float simulation",
    },
}

APPLICATIONS: dict[str, dict[str, str]] = {
    "phase_locked_loop": {
        "title": "Optical PLL (W9/W19)",
        "path": "applications/proposal_05_optical_pll_w9_w19.md",
        "kind": "proposal",
    },
    "translinear": {
        "title": "Translinear diode calculator",
        "path": "applications/proposal_08_translinear_diode_calculator_w24_exp.md",
        "kind": "proposal",
    },
    "log": {
        "title": "Log-compression signal processor",
        "path": "applications/proposal_09_logcompression_signal_processor_log.md",
        "kind": "proposal",
    },
    "sqrt": {
        "title": "Log-domain square-root compute route",
        "path": "docs/LOG_DOMAIN_SQRT.md",
        "kind": "demo",
    },
    "sat": {
        "title": "Saturation-limited amplifier",
        "path": "applications/proposal_10_saturationlimited_amplifier_sat.md",
        "kind": "proposal",
    },
    "hysteresis": {
        "title": "Magnetic memory cell (MTJ)",
        "path": "applications/proposal_22_magnetic_memory_cell_hysteresis_mtj.md",
        "kind": "proposal",
    },
    "delta_sigma_modulator": {
        "title": "Delta-sigma flagship demonstration",
        "path": "docs/DELTA_SIGMA_DEMO.md",
        "kind": "demo",
    },
}

WHEEL_TERMS: dict[str, tuple[str, ...]] = {
    "sqrt": ("sqrt", "^(1/2)", "√"),
    "exp": ("exp(", "e^"),
    "log": ("log(",),
    "sat": ("tanh(", "saturat", "clip"),
    "hysteresis": ("hysteresis", "latch"),
    "wrap": ("mod ", "modulo", "phase"),
    "delay": ("delay",),
    "grad": ("gradient",),
    "div_spatial": ("divergence",),
    "curl": ("curl", "vorticity"),
    "laplacian": ("laplacian",),
    "boundary": ("boundary",),
    "quantize": ("quantiz",),
    "noise": ("noise",),
    "entropy": ("entropy",),
    "gyrator": ("gyrator",),
    "transformer": ("transformer",),
    "transduce": ("transduc",),
    "junction_0": ("junction", "kirchhoff", "kcl"),
    "junction_1": ("junction", "kirchhoff", "kvl"),
    "store_pot": ("capacitor", "capacitance", "spring", "storage"),
    "store_kin": ("inductor", "inductance", "inertia"),
    "dissipate": ("resistance", "dissipat", "friction"),
    "thermo_electric": ("seebeck", "peltier", "thermoelectric"),
    "phase_locked_loop": ("phase", "oscillator"),
    "delta_sigma_modulator": ("delta-sigma", "sigma-delta", "∆σ"),
    "state_space": ("state space", "state-space"),
    "pid": ("pid", "control"),
    "kalman_observer": ("kalman",),
    "transmission_line": ("transmission line", "delay line", "telegrapher"),
}

STATUS_LABEL = {
    vocabulary.IMPLEMENTED_VERIFIED: "verified by exact checks",
    vocabulary.IMPLEMENTED_TESTED: "implemented and exercised",
    vocabulary.IMPLEMENTED_PROOF_PENDING: "implemented; theorem pending",
    vocabulary.SPECIFIED_PENDING: "contract only",
    vocabulary.UNSUPPORTED: "unsupported",
}

GROUPS = (
    ("composite", "Composite methods"),
    ("classical", "Classical"),
    ("continuum", "Continuum"),
    ("conservative", "Conservative network"),
    ("stochastic_topological", "Stochastic / topological"),
)


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(text).lower()).strip()


def _search_text(op: str) -> str:
    contract = vocabulary.CONTRACTS[op]
    parts: Iterable[str] = (
        op,
        PRETTY.get(op, op),
        contract.tier,
        contract.kind,
        contract.inputs,
        contract.output,
        contract.notes,
        *ALIASES.get(op, ()),
    )
    return _norm(" ".join(parts))


def _handler(op: str) -> bool:
    return op in HANDLERS


def _exact(op: str) -> bool:
    return _handler(op) and vocabulary.CONTRACTS[op].status != vocabulary.UNSUPPORTED


def _tier(op: str) -> str:
    return vocabulary.CONTRACTS[op].tier


def _method(op: str) -> dict[str, Any]:
    contract = vocabulary.CONTRACTS[op]
    return {
        "id": op,
        "name": PRETTY.get(op, op),
        "tier": contract.tier,
        "kind": contract.kind,
        "signature": f"{contract.inputs} → {contract.output}",
        "summary": contract.notes or contract.domain,
        "domain": contract.domain,
        "status": contract.status,
        "status_label": STATUS_LABEL.get(contract.status, contract.status),
        "state": contract.state,
        "exact": _exact(op),
        "simulated": op in SIMULATIONS,
        "applied": op in APPLICATIONS,
    }


@lru_cache(maxsize=1)
def _wheels() -> tuple[dict[str, Any], dict[str, Any]]:
    index_path = WHEELS_DIR / "index.json"
    if not index_path.is_file():
        return {}, {}
    index = json.loads(index_path.read_text(encoding="utf-8"))
    docs: dict[str, Any] = {}
    for wid, meta in index.get("wheels", {}).items():
        path = WHEELS_DIR / str(meta.get("file", f"{wid}.json"))
        if path.is_file():
            docs[wid] = json.loads(path.read_text(encoding="utf-8"))
    return index, docs


@lru_cache(maxsize=64)
def wheel_matches(op: str) -> tuple[dict[str, Any], ...]:
    """Wheel text mentioning this concept (not a proof of support)."""
    terms = WHEEL_TERMS.get(op)
    if not terms:
        return ()
    _, docs = _wheels()
    found: list[dict[str, Any]] = []
    for wid, data in docs.items():
        hits: list[str] = []
        for axiom in data.get("axioms", []):
            if any(term in axiom.lower() for term in terms):
                hits.append(axiom)
        for case in data.get("cases", []):
            equation = case.get("equation", "")
            if any(term in equation.lower() for term in terms):
                hits.append(equation)
        for quantity in data.get("quantities", []):
            if any(term in str(quantity).lower() for term in terms):
                hits.append(str(quantity))
        if hits:
            found.append({
                "wheel": wid,
                "title": data.get("title", wid),
                "matches": hits[:4],
            })
    return tuple(found[:6])


def _node(label: str, status: str, detail: str, **extra: Any) -> dict[str, Any]:
    node = {"label": label, "status": status, "detail": detail}
    node.update(extra)
    return node


def _verification_node(op: str) -> dict[str, Any]:
    contract = vocabulary.CONTRACTS[op]
    status = contract.status
    if status in (vocabulary.IMPLEMENTED_VERIFIED, vocabulary.IMPLEMENTED_TESTED):
        node_status = "pass"
    elif status == vocabulary.UNSUPPORTED:
        node_status = "gap"
    else:
        node_status = "info"
    detail = STATUS_LABEL.get(status, status)
    if contract.theorem:
        detail += f" · {contract.theorem}"
    return _node("Verification", node_status, detail)


def _exact_branch(op: str) -> dict[str, Any]:
    contract = vocabulary.CONTRACTS[op]
    children = [
        _node(
            "Contract",
            "pass",
            f"{contract.kind} · {contract.tier} · {contract.inputs} → {contract.output}",
        ),
        _node(
            "Exact handler",
            "pass" if _handler(op) else "gap",
            f"evaluator.HANDLERS[{op!r}]" if _handler(op) else "no evaluator handler",
        ),
        _verification_node(op),
    ]
    ok = _handler(op) and contract.status != vocabulary.UNSUPPORTED
    return {
        "key": "exact",
        "label": "Exact path",
        "status": "pass" if ok else "gap",
        "detail": "contract → evaluator → verification",
        "children": children,
    }


def _physical_branch(op: str) -> dict[str, Any]:
    simulation = SIMULATIONS.get(op)
    application = APPLICATIONS.get(op)

    sim_node = (
        _node(
            "Dynamic simulation",
            "pass",
            f"{simulation['function']} · {simulation['test']} · {simulation['detail']}",
        )
        if simulation
        else _node(
            "Dynamic simulation",
            "gap",
            "no dedicated simulator entry; exact tick execution is not a physical simulation",
        )
    )
    app_node = (
        _node(
            "Application / demonstration",
            "pass",
            f"{application['kind']} · {application['title']} · {application['path']}",
        )
        if application
        else _node(
            "Application / demonstration",
            "gap",
            "no application note or demo mapped to this contract",
        )
    )
    fab_node = _node(
        "Fabrication",
        "out",
        "not attempted in this repository; no fabricated device is claimed",
    )

    if simulation and application:
        status, detail = "pass", "runs through simulation and application; fabrication is out of scope"
    elif simulation:
        status, detail = "stop", "stops after simulation: no application note or demo mapped"
    elif application:
        status, detail = "stop", "stops at dynamic simulation: no dedicated simulator entry"
    else:
        status, detail = "stop", "stops at dynamic simulation: no dedicated simulator entry"

    return {
        "key": "physical",
        "label": "Physical path",
        "status": status,
        "detail": detail,
        "children": [sim_node, app_node, fab_node],
    }


def _ingredients_branch(op: str) -> dict[str, Any] | None:
    parts = COMPONENTS.get(op)
    if not parts:
        return None
    children = []
    for part in parts:
        method = _method(part)
        children.append(
            _node(
                method["name"],
                "pass" if method["exact"] else "gap",
                f"{method['kind']} · {method['tier']} · {method['signature']}",
                method=part,
            )
        )
    return {
        "key": "ingredients",
        "label": "Conceptual ingredients",
        "status": "info",
        "detail": "documented decomposition; the evaluator uses a direct handler",
        "children": children,
    }


def _wheel_branch(op: str) -> dict[str, Any]:
    matches = wheel_matches(op)
    if matches:
        return {
            "key": "wheels",
            "label": "Wheel substrate",
            "status": "pass",
            "detail": f"{len(matches)} wheel(s) mention this concept in axioms, cases or quantities",
            "children": [
                _node(
                    f"{item['wheel']} — {item['title']}",
                    "info",
                    " · ".join(item["matches"]),
                    wheel=item["wheel"],
                )
                for item in matches
            ],
        }
    if op in WHEEL_TERMS:
        return {
            "key": "wheels",
            "label": "Wheel substrate",
            "status": "gap",
            "detail": "no direct keyword match in the built wheel files",
            "children": [],
        }
    return {
        "key": "wheels",
        "label": "Wheel substrate",
        "status": "info",
        "detail": "not a wheel-spoke concept; generic arithmetic appears across the wheel substrate",
        "children": [],
    }


def _score(query: str, op: str) -> int:
    q = _norm(query)
    if not q:
        return 0
    names = {_norm(op), _norm(PRETTY.get(op, op)), *(_norm(a) for a in ALIASES.get(op, ()))}
    if q in names:
        return 100
    text = _search_text(op)
    if q in text:
        return 80
    tokens = q.split()
    return sum(18 for token in tokens if token in text)


def _suggestions(query: str, limit: int = 5) -> list[dict[str, str]]:
    ranked = sorted(
        ((_score(query, op), op) for op in vocabulary.ALL_PRIMITIVES),
        key=lambda item: (-item[0], item[1]),
    )
    positive = [op for score, op in ranked if score > 0][:limit]
    if not positive:
        names = [_norm(op) for op in vocabulary.ALL_PRIMITIVES]
        close = difflib.get_close_matches(_norm(query), names, n=limit, cutoff=0.45)
        positive = close
    return [
        {"id": op, "name": PRETTY.get(op, op), "tier": _tier(op)}
        for op in positive
    ]


def explore(query: str) -> dict[str, Any]:
    """Return the concept tree for ``query``, or suggestions when unmatched."""
    q = str(query or "").strip()
    if not q:
        return {
            "ok": True,
            "matched": False,
            "query": q,
            "suggestions": [],
            "catalogue": catalogue(),
        }

    ranked = sorted(
        ((_score(q, op), op) for op in vocabulary.ALL_PRIMITIVES),
        key=lambda item: (-item[0], 0 if _tier(item[1]) == "composite" else 1, item[1]),
    )
    best_score, best_op = ranked[0]
    if best_score <= 0:
        return {
            "ok": True,
            "matched": False,
            "query": q,
            "suggestions": _suggestions(q),
            "catalogue": None,
        }

    method = _method(best_op)
    exact = _exact_branch(best_op)
    physical = _physical_branch(best_op)
    branches = [exact, physical]
    ingredients = _ingredients_branch(best_op)
    if ingredients:
        branches.append(ingredients)
    branches.append(_wheel_branch(best_op))

    exact_children = exact["children"]
    counts = {
        "exact": sum(1 for child in exact_children if child["status"] == "pass"),
        "exact_total": len(exact_children),
        "physical": sum(1 for child in physical["children"] if child["status"] == "pass"),
        "physical_total": 2,
    }
    if physical["status"] == "pass":
        headline = "exact path complete; simulation and application/demonstration evidence present"
    elif physical["status"] == "stop":
        headline = physical["detail"]
    else:
        headline = "exact path complete; physical path has gaps"

    return {
        "ok": True,
        "matched": True,
        "query": q,
        "method": method,
        "headline": headline,
        "counts": counts,
        "branches": branches,
        "suggestions": _suggestions(q, limit=3) if best_score < 80 else [],
    }


def catalogue() -> dict[str, Any]:
    """All 41 contracts grouped by tier, with the evidence flags the UI shows."""
    groups = []
    for tier, label in GROUPS:
        items = [_method(op) for op in vocabulary.ALL_PRIMITIVES if _tier(op) == tier]
        items.sort(key=lambda item: item["name"].lower())
        groups.append({"tier": tier, "label": label, "methods": items})
    return {
        "ok": True,
        "total": len(vocabulary.ALL_PRIMITIVES),
        "atomic": len(vocabulary.ATOMIC_PRIMITIVES),
        "composite": len(vocabulary.COMPOSITE_PRIMITIVES),
        "groups": groups,
        "note": (
            "Every node is an exact contract. E = exact handler, S = mapped dynamic "
            "simulation, A = mapped application/demo. A missing S or A is a gap, not "
            "a claim that the method is impossible."
        ),
    }
