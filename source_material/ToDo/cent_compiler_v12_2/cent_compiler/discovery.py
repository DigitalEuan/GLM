"""Problem-to-method discovery for the physical compiler.

This is the first *front-end* layer above the existing £ → ¢ → ∆ pipeline.
It answers a different question from ``cent compile``:

    compile:  "given this relation, lower it to ¢ and enumerate ∆"
    discover: "given this problem, which exact contracts and declared physical
               routes could realise it?"

The engine deliberately does **not** invent physics.  A candidate can only come
from one of these declared sources:

* an exact contract in :mod:`cent_compiler.vocabulary`;
* an expansion in :mod:`cent_compiler.substrate_library`;
* a substrate row in :mod:`cent_compiler.pattern_matcher`;
* a documented application/simulation in :mod:`cent_compiler.concepts`;
* a wheel whose text mentions the primitive or one of its material terms.

Wheel links are candidates for grounding, not proofs.  Coverage and evidence
are reported separately so a user can see where the physical route stops.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, replace
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Mapping

from . import assembly, axiom_graph, concepts, design, device, envelope, mechanisms, packing, vocabulary, wheel_mapping
from .evaluator import HANDLERS
from .isomorphism_gate import DECLARED_ANALOGIES
from .pattern_matcher import DELTA_SUBSTRATE
from .spice_emitter import SPICE_TEMPLATE_PATTERNS
from .substrate_library import EXPANSIONS, expansions_for

ROOT = Path(__file__).resolve().parent.parent
WHEELS_DIR = ROOT / "wheels"
SCHEMA = "cent-discovery/1"

#: Which exact contracts can serve which abstract capability.  This is a
#: curated capability index, not a list of answers: each entry points back to a
#: contract or a documented demonstration.
CAPABILITIES: dict[str, tuple[str, ...]] = {
    "sqrt": (
        "compute:root",
        "compute:irrational",
        "approximate:irrational",
    ),
    "translinear": (
        "compute:root",
        "compute:power",
        "compute:transcendental",
    ),
    "eq": (
        "compute:root",
        "solve:equilibrium",
        "compute:implicit",
    ),
    "div": ("compute:ratio",),
    "recip": ("compute:inverse",),
    "exp": ("compute:transcendental", "compute:growth"),
    "log": ("compute:transcendental", "compress:dynamic_range"),
    "delta_sigma_modulator": (
        "carry:irrational",
        "represent:irrational",
        "approximate:irrational",
        "convert:analog_digital",
    ),
    "phase_locked_loop": ("track:phase", "synthesize:frequency"),
    "state_space": ("solve:linear_system", "simulate:state"),
}

#: The remaining reviewed records cover every vocabulary contract.  Tags are
#: deliberately contract-shaped rather than route claims: they say what the
#: exact operation can do, not that a physical implementation has been built.
CAPABILITIES.update({
    "sum": ("compute:sum", "compose:exact"),
    "neg": ("compute:negate", "compose:exact"),
    "mult": ("compute:product", "compose:exact"),
    "scale": ("compute:scale", "compose:exact"),
    "accum": ("accumulate:state", "integrate:state"),
    "rate": ("differentiate:signal",),
    "wrap": ("wrap:phase",),
    "spatial": ("sample:field",),
    "sat": ("limit:signal", "clip:signal"),
    "hysteresis": ("latch:signal", "detect:threshold"),
    "delay": ("delay:signal",),
    "grad": ("compute:gradient",),
    "div_spatial": ("compute:divergence",),
    "curl": ("compute:curl",),
    "laplacian": ("compute:laplacian",),
    "boundary": ("constrain:field",),
    "junction_0": ("constrain:effort", "conserve:power"),
    "junction_1": ("constrain:flow", "conserve:power"),
    "gyrator": ("convert:effort_flow", "conserve:power"),
    "transformer": ("convert:effort", "conserve:power"),
    "dissipate": ("dissipate:energy",),
    "store_pot": ("store:potential_energy",),
    "store_kin": ("store:kinetic_energy",),
    "transduce": ("convert:domain",),
    "noise": ("generate:noise",),
    "quantize": ("quantize:level",),
    "entropy": ("compute:entropy",),
    "pid": ("control:feedback",),
    "transmission_line": ("propagate:signal", "model:reflection"),
    "kalman_observer": ("estimate:state",),
    "thermo_electric": ("convert:thermal_electrical",),
})

CAPABILITY_BASIS: dict[str, str] = {
    "sqrt": "exact interval square-root handler; wheel spokes use ^(1/2)",
    "translinear": "exact product-of-powers contract; can compute fractional roots",
    "eq": "equilibrium contract; physical realisations relax an implicit equation",
    "div": "exact ratio contract",
    "recip": "exact reciprocal contract",
    "exp": "certified enclosure contract",
    "log": "certified enclosure contract",
    "delta_sigma_modulator": "composed bitstream loop; carry_irrational demo and exact tick test",
    "phase_locked_loop": "stateful phase-tracking contract",
    "state_space": "state-space contract for coupled linear systems",
}

#: Provenance for every reviewed capability tag.  Each basis names the exact
#: contract semantics or declared evidence; it is not a fabricated route claim.
CAPABILITY_BASIS.update({
    "sum": "exact n-ary rational/interval addition; stateless",
    "neg": "exact signed negation; unit complement is a separate density operation",
    "mult": "exact n-ary rational/interval product; stateless",
    "scale": "exact rational factor applied to one numeric value",
    "accum": "stateful running sum y_t = x_t + y_{t-1}",
    "rate": "signed first difference divided by a positive dt",
    "wrap": "exact representative in [0, period); no metric implied",
    "spatial": "explicit field sampling at an axis/index; no metric implied",
    "sat": "idempotent clamp between explicit ordered rational bounds",
    "hysteresis": "two-threshold latched bit with retention inside the deadband",
    "delay": "per-node ring-buffer delay of at least one tick",
    "grad": "discrete field gradient; tested curl(grad) identity",
    "div_spatial": "discrete vector-field divergence",
    "curl": "discrete exterior derivative returning a two-form",
    "laplacian": "discrete field Laplacian over declared axes",
    "boundary": "Dirichlet/Neumann/Robin field constraint on every face",
    "junction_0": "common-flow junction resolving effort by power conservation",
    "junction_1": "common-effort junction resolving flow by power conservation",
    "gyrator": "anti-reciprocal effort/flow conversion with power conservation",
    "transformer": "effort/flow ratio conversion with power conservation",
    "dissipate": "linear dissipator with nonnegative entropy rate",
    "store_pot": "stateful potential storage; stores charge",
    "store_kin": "stateful kinetic storage; stores flux",
    "transduce": "declared-efficiency port-domain conversion",
    "noise": "deterministic two-point +-a distribution; not a physical entropy source",
    "quantize": "nearest-multiple quantizer with ties away from zero",
    "entropy": "entropy production P/T; rejects active ports",
    "pid": "stateful proportional/integral/derivative control update",
    "transmission_line": "lossless delay-line model with declared load reflection",
    "kalman_observer": "scalar exact-rational Kalman state/covariance update",
    "thermo_electric": "Peltier heat plus Joule heat with declared thermoelectric parameters",
})

#: Short, explicit aliases used only to recognise a primitive name in a
#: problem statement.  Problem semantics do not depend on these strings.
EXPLICIT_ALIASES: dict[str, tuple[str, ...]] = {
    "sqrt": ("sqrt", "square root", "root extraction"),
    "translinear": ("translinear", "log domain", "log-domain"),
    "eq": ("equilibrium", "implicit equation"),
    "mult": ("multiply", "multiplication", "product", "times", "multiplier"),
    "div": ("divide", "division", "quotient", "ratio", "divider"),
    "recip": ("reciprocal",),
    "exp": ("exponentiate", "exponentiation", "exponential", "exp", "antilog", "antilogarithm"),
    "log": ("logarithm", "logarithmic", "log", "ln", "log compression"),
    "sum": ("sum", "add", "addition", "summing", "adder"),
    "neg": ("negate", "negation"),
    "delta_sigma_modulator": (
        "delta sigma", "delta-sigma", "sigma delta", "sigma-delta",
        "noise shaping", "noise-shaping", "bitstream",
    ),
    "phase_locked_loop": ("phase-locked loop", "phase locked loop", "pll"),
    "state_space": ("state space", "state-space"),
}

# Every canonical primitive is reachable by its contract name, display name and
# the reviewed concept aliases, without changing the existing key precedence.
for _op in vocabulary.ALL_PRIMITIVES:
    aliases = EXPLICIT_ALIASES.get(_op, ())
    if _op not in aliases:
        EXPLICIT_ALIASES[_op] = (
            _op,
            concepts.PRETTY.get(_op, _op),
            *aliases,
            *concepts.ALIASES.get(_op, ()),
        )

EXAMPLE_QUERIES = (
    "compute an irrational value with an analog method",
    "carry an irrational value as a physical signal",
    "compute a square root in a mechanical domain",
    "solve an equilibrium equation physically",
    "compute a power law with a translinear circuit",
    "compute a square root, then carry the result as a bitstream",
    "how do I multiply two signals",
    "compute a ratio",
    "exponentiate a signal",
    "take the logarithm of a signal",
    "sum two signals",
    "find an optimal 2D square packing for n squares",
    "compute a minimum-area bounding box for points",
)

_ENVELOPE_TERMS = (
    "bounding box", "bounding-box", "orientation envelope",
    "minimum area rectangle", "minimum-area rectangle", "liquid crystal",
    "liquid-crystal", "envelope",
)


def _is_envelope_query(normalized: str) -> bool:
    return any(term in normalized for term in _ENVELOPE_TERMS)

_STOP = {
    "about", "above", "after", "again", "against", "analog", "analogue",
    "and", "are", "around", "because", "before", "between", "both", "can",
    "compute", "computing", "could", "derive", "different", "does", "each",
    "for", "from", "given", "have", "how", "into", "method", "methods",
    "need", "other", "physical", "possible", "problem", "produce", "rather",
    "same", "should", "signal", "some", "such", "than", "that", "the", "their",
    "them", "then", "there", "these", "they", "this", "through", "using",
    "value", "want", "what", "when", "where", "which", "while", "with",
    "would", "your", "voltage", "current", "resistance", "power",
}

_DOMAIN_CLASS = {
    "electrical": "electrical",
    "mechanical": "mechanical",
    "rotational": "mechanical",
    "fluidic": "fluidic",
    "fluid": "fluidic",
    "thermal": "thermal",
    "optical": "optical",
    "digital": "mixed-signal",
    "mixed": "mixed-signal",
    "mixed-signal": "mixed-signal",
    "bio-chemical": "chemical",
    "chemical": "chemical",
    "spintronics": "quantum",
    "quantum": "quantum",
    "abstract": "abstract",
}

_DOMAIN_LABEL = {
    "electrical": "electrical",
    "mechanical": "mechanical",
    "fluidic": "fluidic",
    "thermal": "thermal",
    "optical": "optical",
    "mixed-signal": "digital / mixed-signal",
    "chemical": "chemical",
    "quantum": "quantum",
    "abstract": "abstract",
}


@dataclass(frozen=True)
class GoalStep:
    """One ordered clause of a problem statement."""

    index: int
    raw: str
    normalized: str
    behavior: str
    object: str
    goals: tuple[str, ...]
    constraints: tuple[str, ...]
    matched: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "raw": self.raw,
            "normalized": self.normalized,
            "behavior": self.behavior,
            "object": self.object,
            "goals": list(self.goals),
            "constraints": list(self.constraints),
            "matched": self.matched,
        }


@dataclass(frozen=True)
class ProblemSpec:
    """The structured interpretation of a user problem statement."""

    raw: str
    normalized: str
    behavior: str
    object: str
    goals: tuple[str, ...]
    constraints: tuple[str, ...]
    domain: str | None
    assumptions: tuple[str, ...]
    matched: bool
    steps: tuple[GoalStep, ...] = ()

    @property
    def multi_step(self) -> bool:
        return len(self.steps) > 1

    def as_dict(self) -> dict[str, Any]:
        return {
            "raw": self.raw,
            "normalized": self.normalized,
            "behavior": self.behavior,
            "object": self.object,
            "goals": list(self.goals),
            "constraints": list(self.constraints),
            "domain": self.domain,
            "assumptions": list(self.assumptions),
            "matched": self.matched,
            "multi_step": self.multi_step,
            "steps": [step.as_dict() for step in self.steps],
        }


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(text).lower()).strip()


def _tokens(text: str) -> set[str]:
    return {
        token for token in re.findall(r"[a-z0-9]+", str(text).lower())
        if len(token) >= 4 and token not in _STOP
    }


def _has_phrase(text: str, phrase: str) -> bool:
    return f" {phrase} " in f" {text} "


_STEP_BREAK = re.compile(
    r"\s*(?:;|->|→|,?\s*(?:and\s+)?then\s+|,?\s*after\s+that\s+|,?\s*followed\s+by\s+)\s*",
    re.IGNORECASE,
)


def _split_steps(text: str) -> list[str]:
    """Split an ordered goal on explicit sequencing words or punctuation."""
    raw = str(text or "").strip()
    parts = [part.strip(" ,.;") for part in _STEP_BREAK.split(raw)]
    return [part for part in parts if part] or [raw]


def _ordered_unique(items: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(items))


def _explicit_primitive(q: str) -> str | None:
    for op, aliases in EXPLICIT_ALIASES.items():
        for alias in aliases:
            alias = _norm(alias)
            if alias and _has_phrase(q, alias):
                return op
    return None


def parse_problem(text: str, domain: str | None = None) -> ProblemSpec:
    """Turn a terse problem statement into explicit goals and assumptions.

    The parser is deliberately modest.  It recognises a small vocabulary of
    behaviours and objects; an unrecognised problem returns ``matched=False``
    so the caller can ask for clarification instead of guessing.
    """
    raw = str(text or "").strip()
    q = _norm(raw)
    pieces = _split_steps(raw)
    if len(pieces) > 1:
        children = [parse_problem(piece, domain=domain) for piece in pieces]
        steps = tuple(
            GoalStep(
                index=index,
                raw=child.raw,
                normalized=child.normalized,
                behavior=child.behavior,
                object=child.object,
                goals=child.goals,
                constraints=child.constraints,
                matched=child.matched,
            )
            for index, child in enumerate(children, 1)
        )
        unmatched = [str(step.index) for step in steps if not step.matched]
        goals = _ordered_unique(goal for step in steps for goal in step.goals)
        constraints = _ordered_unique(
            item for step in steps for item in step.constraints
        )
        assumptions = list(_ordered_unique(
            note for child in children for note in child.assumptions
        ))
        assumptions.append(
            f"Parsed as {len(steps)} ordered goal steps; candidates are matched "
            "independently and no declared handoff executes one step's output "
            "on the next."
        )
        if unmatched:
            assumptions.append(
                "Unrecognised step(s): " + ", ".join(unmatched)
                + "; no whole-pipeline match is claimed."
            )
        return ProblemSpec(
            raw=raw,
            normalized=q,
            behavior="multi-step",
            object="multi-step",
            goals=goals,
            constraints=constraints,
            domain=(domain or None),
            assumptions=tuple(assumptions),
            matched=not unmatched,
            steps=steps,
        )
    if not q:
        return ProblemSpec(
            raw, q, "unspecified", "unspecified", (), (), domain, (), False,
            steps=(GoalStep(1, raw, q, "unspecified", "unspecified", (), (), False),),
        )

    tokens = set(q.split())
    constraints: list[str] = []
    if tokens & {"analog", "analogue", "continuous", "physical", "hardware"}:
        constraints.append("analog/physical")
    if tokens & {"exact", "certified", "rigorous"}:
        constraints.append("exact/certified")
    if tokens & {"digital", "bitstream", "discrete"}:
        constraints.append("digital")

    if tokens & {"carry", "carrying", "represent", "representing", "store",
                 "storing", "encode", "encoding", "transmit", "transmitting"}:
        behavior = "carry"
    elif tokens & {"solve", "solving", "equilibrium", "find"}:
        behavior = "solve"
    else:
        behavior = "compute"

    explicit = _explicit_primitive(q)
    if tokens & {"packing", "pack"}:
        object_name = "packing"
        goals = (
            "optimize:packing",
            "minimize:overlap",
            "relax:penetration",
            "constrain:container",
        )
    elif explicit:
        object_name = explicit
        goals = (f"primitive:{explicit}",) + CAPABILITIES.get(explicit, ())
    elif "irrational" in tokens or "irrational number" in q:
        object_name = "irrational"
        if behavior == "carry":
            goals = ("carry:irrational",)
        else:
            # A computed irrational still has to be represented by a physical
            # carrier.  Keep compute and carry separate, but expose both so a
            # user can compare a root extractor with a bitstream carrier.
            goals = ("compute:irrational", "compute:root", "carry:irrational")
    elif "root" in tokens or "sqrt" in tokens:
        object_name = "root"
        goals = ("compute:root",)
    elif tokens & {"equilibrium", "implicit"}:
        object_name = "equilibrium"
        goals = ("solve:equilibrium",)
    elif tokens & {"power", "exponent", "power-law"}:
        object_name = "power"
        goals = ("compute:power",)
    elif tokens & {"phase", "oscillation", "oscillator"}:
        object_name = "phase"
        goals = ("track:phase",)
    else:
        object_name = "unspecified"
        goals = ()

    matched = bool(goals)
    assumptions: list[str] = []
    if object_name == "irrational" and behavior != "carry":
        assumptions.append(
            "Interpreted as computing a specified irrational relation (for "
            "example sqrt(x)) or carrying a known irrational value.  Computing "
            "an arbitrary irrational without a defining relation is not a "
            "well-posed compilation target."
        )
    if object_name == "packing":
        assumptions.append(
            "Packing is parsed as a fixed-container overlap-relaxation problem, "
            "not as a proof of global optimality. The W36/W37 pressure-settling "
            "analogy is a declared candidate; the optimality gap stays explicit."
        )
    if "analog/physical" in constraints:
        assumptions.append(
            "Analog includes mixed-signal methods when the output is an analog "
            "quantity; a digital bitstream is labelled digital/mixed-signal."
        )
    if matched:
        assumptions.append(
            "Candidates come only from exact contracts and declared substrate "
            "tables; a wheel match is text-level evidence, not a derivation."
        )

    return ProblemSpec(
        raw=raw,
        normalized=q,
        behavior=behavior,
        object=object_name,
        goals=tuple(goals),
        constraints=tuple(constraints),
        domain=(domain or None),
        assumptions=tuple(assumptions),
        matched=matched,
        steps=(GoalStep(1, raw, q, behavior, object_name, tuple(goals), tuple(constraints), matched),),
    )


def _domain_class(domain: str) -> str:
    return _DOMAIN_CLASS.get(str(domain).lower(), str(domain).lower() or "unknown")


def _domain_label(domain: str) -> str:
    cls = _domain_class(domain)
    return _DOMAIN_LABEL.get(cls, cls)


def _title(text: str) -> str:
    return " ".join(part.capitalize() for part in str(text).replace("_", "-").split("-") if part)


def _ingredient_status(op: str) -> dict[str, Any]:
    expansions = len(expansions_for(op))
    substrates = sum(1 for row in DELTA_SUBSTRATE if row.primitive == op)
    return {
        "primitive": op,
        "expansions": expansions,
        "substrates": substrates,
        "physical": expansions + substrates,
        "exact": op in HANDLERS,
    }


def _ingredients(op: str) -> tuple[str, ...]:
    return tuple(concepts.COMPONENTS.get(op, ()))


def _contract_evidence(op: str) -> tuple[bool, bool, bool, bool, list[str]]:
    """Return exact/simulated/application-declared/application-available."""
    exact = op in HANDLERS
    simulation = op in concepts.SIMULATIONS
    application = concepts.APPLICATIONS.get(op)
    declared = application is not None
    available = False
    if application:
        path = ROOT / str(application.get("path", ""))
        available = path.is_file()
    gaps: list[str] = []
    if declared and not available:
        gaps.append(
            f"application evidence points to a missing file: {application.get('path')}"
        )
    return exact, simulation, declared, available, gaps


def _evidence(
    *,
    exact: bool,
    simulation: bool,
    application_declared: bool,
    application_available: bool,
    route: str,
    route_model: Mapping[str, Any] | None = None,
    route_simulation: Mapping[str, Any] | None = None,
    device_binding: Mapping[str, Any] | None = None,
    notes: Iterable[str] = (),
) -> list[dict[str, str]]:
    evidence = [
        {
            "kind": "exact contract",
            "status": "pass" if exact else "gap",
            "detail": "evaluator handler present" if exact else "no evaluator handler",
        },
        {
            "kind": "dynamic simulation",
            "status": "pass" if simulation else "gap",
            "detail": (
                "primitive-level simulation mapped"
                if simulation else "no dedicated simulation mapped"
            ),
        },
    ]
    if application_declared:
        evidence.append(
            {
                "kind": "application / demo",
                "status": "pass" if application_available else "gap",
                "detail": (
                    "application note/demo exists"
                    if application_available
                    else "declared path is missing"
                ),
            }
        )
    if route_model is not None:
        evidence.append(
            {
                "kind": "route model",
                "status": "pass",
                "detail": "typed exact route graph with declared component contracts",
            }
        )
        if route_simulation is not None:
            evidence.append(
                {
                    "kind": "route simulation",
                    "status": "pass" if route_simulation.get("passed") else "gap",
                    "detail": (
                        "exact route simulation passed; result checked against its declared bracket"
                        if route_simulation.get("passed")
                        else "exact route simulation did not meet its tolerance"
                    ),
                }
            )
    elif route != "contract":
        evidence.append(
            {
                "kind": "route model",
                "status": "gap",
                "detail": "declared material route; no parameterised port graph or netlist yet",
            }
        )
    if device_binding is not None:
        evidence.append(
            {
                "kind": "device binding",
                "status": "pass" if device_binding.get("passed") else "gap",
                "detail": (
                    "declared reference design passes its exact device-law checks; no netlist"
                    if device_binding.get("passed")
                    else "declared reference design misses a device-law check"
                ),
            }
        )
    for note in notes:
        evidence.append({"kind": "note", "status": "info", "detail": note})
    return evidence


def _design_route(op: str, route_model: Mapping[str, Any] | None) -> str | None:
    """Map an exact route model to the solver's declared design-space key."""
    if op == "delta_sigma_modulator":
        return "delta-sigma"
    kind = str((route_model or {}).get("kind") or "")
    if kind == "certified-enclosure":
        return "sqrt-log"
    if kind == "certified-algebraic-feedback":
        return "sqrt-feedback"
    return None


def _design_metadata(
    op: str, route_model: Mapping[str, Any] | None
) -> dict[str, Any] | None:
    """Expose the declared solver space alongside a discoverable method."""
    route = _design_route(op, route_model)
    if route is None:
        return None
    space = design.DESIGN_SPACES[route]
    return {
        "route": route,
        "name": space.name,
        "input_domain": space.input_domain,
        "default_input": str(space.default_input),
        "default_accuracy": str(device.DEFAULT_ERROR_LIMIT),
        "options": [
            {"name": option.name, "cost": str(option.cost)}
            for option in space.options
        ],
    }


def _base_method(
    op: str,
    hit: str,
    *,
    name: str,
    route: str,
    domain: str,
    carrier: str,
    components: tuple[str, ...],
    description: str,
    tags: tuple[str, ...],
    sources: tuple[str, ...],
    delta_sigma: bool = False,
    ingredient_status: tuple[dict[str, Any], ...] = (),
    extra_gaps: Iterable[str] = (),
    route_model: Mapping[str, Any] | None = None,
    route_simulation: Mapping[str, Any] | None = None,
    device_binding: Mapping[str, Any] | None = None,
    material_contract: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    contract = vocabulary.CONTRACTS[op]
    exact, simulation, app_declared, app_available, app_gaps = _contract_evidence(op)
    gaps = list(extra_gaps) + app_gaps
    if not simulation:
        gaps.append("no dynamic simulation mapped to this primitive")
    if not app_declared:
        gaps.append("no application note or demonstration mapped to this primitive")
    if route_model is not None:
        if device_binding is None:
            gaps.append("no declared device binding for this route")
        gaps.append("no full physical netlist for this route")
    elif route != "contract":
        gaps.append("no route-level simulation or parameterised component model")
    else:
        gaps.append("no full physical netlist for this contract")
    for item in ingredient_status:
        if item["physical"] == 0:
            gaps.append(
                f"no physical substrate declared for ingredient ¢_{item['primitive']}"
            )

    covered = sum(1 for item in ingredient_status if item["physical"] > 0)
    if ingredient_status:
        coverage = f"{covered}/{len(ingredient_status)} ingredients have declared physical material"
    else:
        coverage = "single primitive; no ingredient decomposition required"

    return {
        "id": f"{route}:{op}:{name.lower().replace(' ', '-')}",
        "name": name,
        "primitive": op,
        "pretty": concepts.PRETTY.get(op, op),
        "goal": hit,
        "role": "carry" if hit.startswith(("carry:", "represent:", "convert:")) else
                "solve" if hit.startswith(("solve:", "track:")) else "compute",
        "tags": list(tags),
        "route": route,
        "sources": list(sources),
        "domain": domain,
        "domain_class": _domain_class(domain),
        "domain_label": _domain_label(domain),
        "carrier": carrier,
        "components": list(components),
        "description": description,
        "contract_status": contract.status,
        "contract_status_label": concepts.STATUS_LABEL.get(contract.status, contract.status),
        "capability_basis": CAPABILITY_BASIS.get(op, ""),
        "contract_exact": exact,
        "simulation": simulation,
        "application_declared": app_declared,
        "application_available": app_available,
        "delta_sigma": bool(delta_sigma),
        "ingredient_status": list(ingredient_status),
        "coverage": coverage,
        "route_model": route_model,
        "route_simulation": route_simulation,
        "device_binding": device_binding,
        "material_contract": material_contract,
        "design": _design_metadata(op, route_model),
        "gaps": sorted(dict.fromkeys(gaps)),
        "wheel_material": [],
        "wheel_mappings": [],
        "wheel_grounding": {},
        "declared_analogies": [],
        "evidence": _evidence(
            exact=exact,
            simulation=simulation,
            application_declared=app_declared,
            application_available=app_available,
            route=route,
            route_model=route_model,
            route_simulation=route_simulation,
            device_binding=device_binding,
            notes=(),
        ),
        "score": 0,
        "score_reasons": [],
        "step_indexes": [],
    }


def _route_method(op: str, hit: str, expansion: Any) -> dict[str, Any]:
    return _base_method(
        op,
        hit,
        name=f"{concepts.PRETTY.get(op, op)} — {_title(expansion.name)}",
        route="expansion",
        domain=expansion.substrate_domain,
        carrier=expansion.carrier_type,
        components=(expansion.substrate_component,),
        description=expansion.description,
        tags=CAPABILITIES.get(op, ()),
        sources=("EXPANSIONS",),
        delta_sigma=expansion.is_delta_sigma,
        ingredient_status=tuple(_ingredient_status(part) for part in _ingredients(op)),
        material_contract=expansion.contract.as_dict(),
    )


@lru_cache(maxsize=1)
def _feedback_sqrt_payload() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Build the op-amp feedback sqrt route once for discovery."""
    route = assembly.opamp_multiplier_sqrt_route()
    return (
        route.as_dict(),
        route.simulate(Fraction(2)).as_dict(),
        device.bind_feedback_sqrt().as_dict(),
    )


@lru_cache(maxsize=1)
def _sqrt_route_payload() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Build the certified log-domain sqrt route once for discovery."""
    route = assembly.log_domain_sqrt_route()
    return (
        route.as_dict(),
        route.simulate(Fraction(2)).as_dict(),
        device.bind_log_domain_sqrt().as_dict(),
    )


def _substrate_method(op: str, hit: str, substrate: Any) -> dict[str, Any]:
    route_model = None
    route_simulation = None
    device_binding = None
    component = substrate.component.lower()
    if op == "sqrt" and "diode" in component:
        route_model, route_simulation, device_binding = _sqrt_route_payload()
    elif op == "sqrt" and ("op-amp" in component or "multiplier" in component):
        route_model, route_simulation, device_binding = _feedback_sqrt_payload()
    return _base_method(
        op,
        hit,
        name=f"{concepts.PRETTY.get(op, op)} — {substrate.component}",
        route="substrate",
        domain=substrate.domain,
        carrier=substrate.carrier_type,
        components=(substrate.component,),
        description=f"{substrate.law}. {substrate.notes}".strip(),
        tags=CAPABILITIES.get(op, ()),
        sources=("DELTA_SUBSTRATE",),
        ingredient_status=tuple(_ingredient_status(part) for part in _ingredients(op)),
        material_contract=substrate.contract.as_dict(),
        extra_gaps=(),
        route_model=route_model,
        route_simulation=route_simulation,
        device_binding=device_binding,
    )


def _packing_wheel_scan() -> dict[str, Any]:
    """Scan every declared wheel for packing-adjacent material.

    W36 and W37 are selected because together they declare the objective and
    relaxation laws.  Other wheels stay adjacent candidates; a text hit is not
    promoted to a method.
    """
    terms = (
        "penetration", "packing", "overlap", "energy", "stress",
        "viscosity", "relaxation", "pressure", "force",
    )
    selected = {"W36": "objective", "W37": "relaxation"}
    candidates: list[dict[str, Any]] = []
    docs = _wheel_docs()
    for wid, data in docs.items():
        haystack = _wheel_haystack(data)
        hits = [term for term in terms if term in haystack]
        if not hits:
            continue
        role = "selected" if wid in selected else "adjacent"
        if role == "adjacent" and len(hits) < 2:
            continue
        candidates.append({
            "wheel": wid,
            "title": str(data.get("title", wid)),
            "role": role,
            "matches": hits[:5],
            "reason": (
                "selected for the W36/W37 objective-relaxation pair"
                if role == "selected"
                else "adjacent physical material; does not declare both the squared penetration objective and the relaxation law"
            ),
        })
    candidates.sort(key=lambda item: (0 if item["role"] == "selected" else 1, item["wheel"]))
    return {
        "wheels_scanned": len(docs),
        "selected": ["W36", "W37"],
        "candidates": candidates[:10],
        "rule": (
            "all wheel documents were scanned; only W36 supplies the squared "
            "penetration/wall energy and only W37 supplies the Maxwell "
            "relaxation law. Adjacent candidates are not promoted to methods."
        ),
    }


def _envelope_method(hit: str) -> dict[str, Any]:
    """Declared exact finite-direction envelope method."""
    probe = envelope.orientation_envelope(
        [(0, 1), (1, 0), (0, -1), (-1, 0)]
    )
    route_model = {
        "id": "orientation-envelope",
        "kind": "exact-algorithm",
        "method": envelope.METHOD,
        "primitive_chain": ["spatial"],
        "scope": "finite declared rational direction set",
        "optimality": "minimum over declared directions only",
        "gaps": [
            "finite declared direction set; not every real orientation",
            "no global optimality claim",
        ],
    }
    method = _base_method(
        "spatial",
        hit,
        name="Orientation Envelope — finite-direction minimax",
        route="exact-algorithm",
        domain="computational geometry",
        carrier="rational point set",
        components=(
            "exact point projections",
            "direction/normal bounds",
            "minimum-area selection",
            "exact corner reconstruction",
        ),
        description=(
            "Projects exact rational points onto a declared finite set of "
            "rational directions and their normals, computes the exact "
            "enclosing area and returns the minimum-area envelope. The "
            "physical or liquid-crystal interpretation is optional."
        ),
        tags=("compute:envelope", "minimize:area", "bound:points"),
        sources=("envelope.py", "docs/ORIENTATION_ENVELOPE.md"),
        route_model=route_model,
        route_simulation=probe,
    )
    method.update({
        "id": "exact-algorithm:bounding_box:orientation-envelope",
        "primitive": "bounding_box",
        "pretty": "Bounding-box envelope",
        "role": "compute",
        "route": "exact-algorithm",
        "contract_status": "exact computational method",
        "contract_status_label": "exact algorithm; finite direction set",
        "capability_basis": (
            "exact rational projections; minimum over the declared direction set"
        ),
        "contract_exact": True,
        "simulation": False,
        "application_declared": True,
        "application_available": (ROOT / "docs" / "ORIENTATION_ENVELOPE.md").is_file(),
        "coverage": (
            f"{probe['summary']['directions']} declared directions; "
            "exact area and corners; no global-orientation claim"
        ),
        "gaps": [
            "the minimum is over the finite declared direction set, not every real orientation",
            "projected extents are not unit-normalized; the returned area is exact",
            "no physical, liquid-crystal, optical or fabrication behavior is simulated",
            "the method is a computational construction, not a measured-device result",
        ],
        "wheel_material": [],
        "wheel_mappings": [],
        "wheel_grounding": {
            "status": "not-applicable",
            "basis": [],
            "candidates": [],
            "declared_bridges": [],
            "text_only": [],
            "gaps": [],
            "claim": "computational geometry method; no wheel grounding is claimed",
        },
        "declared_analogies": [],
        "evidence": [
            {
                "kind": "exact computational method",
                "status": "pass",
                "detail": "exact rational projections, area and corners",
            },
            {
                "kind": "exact probe",
                "status": "pass" if probe.get("passed") else "gap",
                "detail": f"diamond probe area {probe['summary']['best_area']}",
            },
            {
                "kind": "global optimum",
                "status": "gap",
                "detail": "finite declared direction set only",
            },
        ],
    })
    return method


def _packing_method(hit: str) -> dict[str, Any]:
    """Declared packing analogy from the W36/W37 settling pair.

    This is intentionally not a vocabulary contract: packing is an
    optimisation problem, not a primitive operation.  The exact probe checks
    the declared geometry and the W36/W37 laws; it does not claim a global
    optimum.
    """
    initial = (
        packing.Square("a", Fraction(1, 2), Fraction(1, 2)),
        packing.Square("b", Fraction(3, 4), Fraction(1, 2)),
    )
    probe = packing.settle(
        2,
        side=3,
        initial=initial,
        iterations=8,
        dt=Fraction(1, 4),
        viscosity=1,
        modulus=4,
    )
    route_model = {
        "id": "packing-pressure-settling",
        "kind": "declared-analogy",
        "source_wheels": ["W36", "W37"],
        "primitive_chain": list(packing.PRIMITIVE_CHAIN),
        "objective": packing.OBJECTIVE,
        "scope": packing.INSTANCE_SCOPE,
        "optimality": "not claimed",
        "gaps": [
            "no global optimality certificate or exhaustive configuration search",
            "axis-aligned unit squares in a fixed container only",
        ],
    }
    method = _base_method(
        "sum",
        hit,
        name="Pressure Settling Engine — W36/W37 relaxation",
        route="declared-analogy",
        domain="mechanical",
        carrier="position / penetration",
        components=(
            "squared penetration energy (W36)",
            "Maxwell relaxation (W37)",
            "container wall constraint (W36)",
            "contact projection",
        ),
        description=(
            "W36 turns pair penetration and container violation into squared "
            "energy; W37 supplies the viscous relaxation time. The declared "
            "probe projects overlaps apart in a fixed container. It is a "
            "feasibility heuristic, not a proof of optimal packing."
        ),
        tags=("optimize:packing", "minimize:overlap", "relax:penetration"),
        sources=("W36", "W37", "packing.py"),
        ingredient_status=tuple(
            _ingredient_status(part) for part in packing.PRIMITIVE_CHAIN
        ),
        route_model=route_model,
        route_simulation=probe,
    )
    method.update({
        "id": "declared-analogy:packing:pressure-settling",
        "primitive": "packing",
        "pretty": "2D square packing",
        "role": "compute",
        "route": "declared-analogy",
        "contract_status": "declared computational analogy",
        "contract_status_label": "declared analogy; optimality not proved",
        "capability_basis": (
            "W36 squared penetration/wall energy plus W37 Maxwell relaxation; "
            "the exact probe is a declared feasibility check"
        ),
        "contract_exact": False,
        "simulation": False,
        "application_declared": True,
        "application_available": (ROOT / "docs" / "PACKING_PRESSURE_SETTLING.md").is_file(),
        "coverage": "7 declared primitives map to W36/W37; no optimality proof",
        "gaps": [
            "no global optimality certificate or exhaustive configuration search",
            "axis-aligned unit squares in a fixed container only; no rotation or arbitrary sizes",
            "no physical device, fabrication netlist or measured run",
            "the relaxation projection is a declared numerical scheme, not a hardware simulation",
        ],
        "wheel_material": [
            {
                "wheel": "W36",
                "title": "Numerical SAT Substrate — quadratic energy laws",
                "matches": [
                    "pair_energy = pair_penetration^2",
                    "wall_energy = container_violation^2",
                ],
                "scope": "declared equation",
            },
            {
                "wheel": "W37",
                "title": "Viscoelastic Settling — Maxwell creep and dissipation",
                "matches": [
                    "relaxation_time = viscosity / modulus",
                    "strain_rate = stress / viscosity",
                    "dissipated_power = stress * strain_rate",
                ],
                "scope": "declared equation",
            },
        ],
        "wheel_grounding": {
            "status": "declared-analogy",
            "basis": ["W36", "W37"],
            "candidates": [],
            "declared_bridges": [],
            "text_only": [],
            "gaps": [],
            "claim": (
                "W36/W37 are source laws for a declared analogy; they do not "
                "prove an optimal packing or a physical implementation"
            ),
        },
        "wheel_scan": _packing_wheel_scan(),
        "declared_analogies": [{
            "name": "W36 penetration → W37 viscoelastic stress",
            "wheel_pair": ["W36", "W37"],
            "convention": "penetration as stress",
            "equations": [
                "pair_energy = pair_penetration^2",
                "relaxation_time = viscosity / modulus",
            ],
        }],
        "evidence": [
            {
                "kind": "declared wheel analogy",
                "status": "pass",
                "detail": "W36 penetration energy joined to W37 Maxwell relaxation",
            },
            {
                "kind": "exact application probe",
                "status": "pass" if probe.get("passed") else "gap",
                "detail": (
                    "axis-aligned fixed-container probe reached zero overlap/wall violation"
                    if probe.get("passed")
                    else "probe did not reach zero overlap/wall violation"
                ),
            },
            {
                "kind": "global optimality",
                "status": "gap",
                "detail": "no exhaustive search or lower-bound certificate",
            },
            {
                "kind": "physical device",
                "status": "gap",
                "detail": "no device binding or fabrication netlist",
            },
        ],
    })
    return method


def _contract_method(op: str, hit: str) -> dict[str, Any]:
    contract = vocabulary.CONTRACTS[op]
    ingredients = tuple(_ingredient_status(part) for part in _ingredients(op))
    domain = "mixed-signal" if op == "delta_sigma_modulator" else "abstract"
    carrier = "bitstream / temporal" if op == "delta_sigma_modulator" else "temporal"
    route_model = None
    route_simulation = None
    device_binding = None
    if op == "delta_sigma_modulator":
        route = assembly.delta_sigma_route()
        route_model = route.as_dict()
        route_simulation = route.simulate(Fraction(1, 2), samples=12).as_dict()
        device_binding = device.bind_delta_sigma().as_dict()
    elif op == "sqrt":
        route_model, route_simulation, device_binding = _sqrt_route_payload()
    return _base_method(
        op,
        hit,
        name=f"{concepts.PRETTY.get(op, op)} — contract level",
        route="contract",
        domain=domain,
        carrier=carrier,
        components=tuple(part["primitive"] for part in ingredients) or ("contract",),
        description=contract.notes or contract.domain,
        tags=CAPABILITIES.get(op, ()),
        sources=("vocabulary",),
        delta_sigma=op == "delta_sigma_modulator",
        ingredient_status=ingredients,
        route_model=route_model,
        route_simulation=route_simulation,
        device_binding=device_binding,
    )


def _similar(a: Mapping[str, Any], b: Mapping[str, Any]) -> bool:
    if a["primitive"] != b["primitive"]:
        return False
    if a["domain_class"] != b["domain_class"]:
        return False
    left = _tokens(" ".join([a["name"], a["description"], *a["components"]]))
    right = _tokens(" ".join([b["name"], b["description"], *b["components"]]))
    if not left or not right:
        return False
    return len(left & right) / len(left | right) >= 0.35


def _merge_routes(methods: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge an expansion and a substrate for the same material route.

    The two tables overlap (for example, an op-amp sqrt appears in both), but
    they describe the same candidate.  Merging keeps the source provenance.
    """
    merged: list[dict[str, Any]] = []
    for method in methods:
        match = None
        for existing in merged:
            if _similar(existing, method):
                match = existing
                break
        if match is None:
            merged.append(method)
            continue
        match["route"] = "expansion+substrate"
        match["sources"] = sorted(set(match["sources"]) | set(method["sources"]))
        match["components"] = list(dict.fromkeys(match["components"] + method["components"]))
        if method["description"] not in match["description"]:
            match["description"] = match["description"].rstrip(".") + ". " + method["description"]
        match["gaps"] = sorted(set(match["gaps"]) | set(method["gaps"]))
        match["delta_sigma"] = match["delta_sigma"] or method["delta_sigma"]
        # The expansion may be encountered before the substrate row that owns
        # the typed route.  Do not lose that evidence during the merge.
        if match.get("route_model") is None and method.get("route_model") is not None:
            match["route_model"] = method["route_model"]
            match["route_simulation"] = method.get("route_simulation")
            match["device_binding"] = method.get("device_binding")
            match["gaps"] = [
                gap for gap in match["gaps"]
                if gap != "no route-level simulation or parameterised component model"
            ]
            if method.get("device_binding") is not None:
                match["gaps"] = [
                    gap for gap in match["gaps"]
                    if gap != "no declared device binding for this route"
                ]
            if "no full physical netlist for this route" not in match["gaps"]:
                match["gaps"].append("no full physical netlist for this route")
    return merged


@lru_cache(maxsize=1)
def _wheel_docs() -> dict[str, dict[str, Any]]:
    if not WHEELS_DIR.is_dir():
        return {}
    docs: dict[str, dict[str, Any]] = {}
    for path in sorted(WHEELS_DIR.glob("W*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        docs[str(data.get("id", path.stem))] = data
    return docs


def _wheel_haystack(data: Mapping[str, Any]) -> str:
    parts: list[str] = [
        str(data.get("title", "")),
        *[str(item) for item in data.get("axioms", ())],
        *[str(item.get("equation", "")) for item in data.get("cases", ())],
        *[str(item) for item in data.get("quantities", ())],
    ]
    return " ".join(parts).lower()


def _wheel_material(op: str, method: Mapping[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Find wheel text that could ground a candidate.

    First use the primitive-level term map from ``concepts``.  Then look for
    component/material words.  Everything returned is explicitly a candidate.
    """
    found: list[dict[str, Any]] = []
    seen: set[str] = set()

    for item in concepts.wheel_matches(op):
        wid = str(item["wheel"])
        seen.add(wid)
        found.append({
            "wheel": wid,
            "title": item["title"],
            "matches": list(item["matches"]),
            "scope": "primitive text",
        })

    terms = _tokens(" ".join([
        method.get("name", ""),
        method.get("description", ""),
        *method.get("components", ()),
    ]))
    if terms:
        for wid, data in _wheel_docs().items():
            if wid in seen:
                continue
            haystack = _wheel_haystack(data)
            hits = sorted(term for term in terms if term in haystack)
            if len(hits) < 2 and not (len(terms) <= 4 and len(hits) == 1):
                continue
            found.append({
                "wheel": wid,
                "title": str(data.get("title", wid)),
                "matches": hits[:4],
                "scope": "component/material text",
            })
            seen.add(wid)
            if len(found) >= 4:
                break

    analogies: list[dict[str, Any]] = []
    for item in found:
        wid = item["wheel"]
        for analogy in DECLARED_ANALOGIES:
            if wid not in analogy.wheel_pair:
                continue
            entry = {
                "name": analogy.name,
                "wheel_pair": list(analogy.wheel_pair),
                "convention": analogy.convention,
                "equations": list(analogy.transducer_equations),
            }
            if entry["name"] not in {x["name"] for x in analogies}:
                analogies.append(entry)
    return found[:4], analogies


def _wheel_grounding(
    op: str,
    material: list[dict[str, Any]],
    mappings: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build graph/declared grounding and keep text matches separate."""
    grounding = dict(axiom_graph.ground_primitive(op))
    declared = [item for item in mappings if item.get("status") == "declared"]
    graph_wheels = {item["wheel"] for item in grounding.get("candidates") or []}
    declared_wheels = {item["wheel"] for item in declared}
    text_only = [
        item for item in material
        if item["wheel"] not in graph_wheels
        and item["wheel"] not in declared_wheels
    ]
    graph_status = str(grounding.get("status") or "gap")
    basis = []
    if graph_status == "derived":
        basis.append("graph-proof")
    if declared:
        basis.append("declared-bridge")
    if text_only:
        basis.append("text-only")
    graph_gaps = list(grounding.get("gaps") or [])
    grounding.update(
        {
            "graph_status": graph_status,
            "declared_bridges": declared,
            "text_only": text_only,
            "status": "grounded" if graph_status == "derived" or declared else "gap",
            "basis": basis,
            "graph_gaps": graph_gaps,
            "gaps": [] if graph_status == "derived" or declared else graph_gaps,
            "claim": (
                "graph-derived monomial relations and declared bridges are "
                "separate evidence; text-only matches are not grounding"
            ),
        }
    )
    return grounding


def _score(method: dict[str, Any], problem: ProblemSpec) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    if method["goal"] == (problem.goals[0] if problem.goals else ""):
        score += 40
        reasons.append("matches primary goal +40")
    else:
        score += 18
        reasons.append("matches secondary goal +18")
    if method["route"] == "contract":
        score += 22
        reasons.append("contract-level evidence +22")
    if method["contract_exact"]:
        score += 12
        reasons.append("exact handler +12")
    if method["simulation"]:
        score += 14
        reasons.append("simulation evidence +14")
    if method["application_available"]:
        score += 8
        reasons.append("available application/demo +8")
    grounding = method.get("wheel_grounding") or {}
    if grounding.get("status") == "grounded":
        count = len(grounding.get("candidates") or []) + len(
            grounding.get("declared_bridges") or []
        )
        bonus = min(8, 2 * count)
        score += bonus
        reasons.append(f"graph/declared wheel grounding +{bonus}")
    elif method["wheel_material"]:
        reasons.append("text-only wheel candidates +0")
    if "analog/physical" in problem.constraints:
        if method["domain_class"] in {"electrical", "mechanical", "fluidic", "thermal", "optical", "mixed-signal"}:
            score += 5
            reasons.append("eligible for analog/physical constraint +5")
        else:
            score -= 8
            reasons.append("outside analog/physical constraint -8")
    score -= len(method["gaps"])
    reasons.append(f"open gaps -{len(method['gaps'])}")
    return score, reasons


def _domain_matches(wanted: str | None, method: Mapping[str, Any]) -> bool:
    if not wanted:
        return True
    wanted = _norm(wanted)
    if wanted in {"analog", "analogue", "physical"}:
        return method["domain_class"] != "digital"
    if wanted == "digital":
        return method["domain_class"] in {"digital", "mixed-signal"}
    return method["domain_class"] == _domain_class(wanted) or method["domain"] == wanted


def _suggestions(query: str, limit: int = 5) -> list[dict[str, str]]:
    q = _norm(query)
    ranked: list[tuple[int, str]] = []
    for op in vocabulary.ALL_PRIMITIVES:
        terms = [op, concepts.PRETTY.get(op, op), *EXPLICIT_ALIASES.get(op, ())]
        score = sum(10 for term in terms if q and _norm(term) in q)
        if q and q in _norm(" ".join(terms)):
            score += 5
        if score:
            ranked.append((score, op))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    if not ranked:
        ranked = [(0, op) for op in vocabulary.ALL_PRIMITIVES]
    return [
        {"id": op, "name": concepts.PRETTY.get(op, op), "tier": vocabulary.tier_of(op)}
        for _, op in ranked[:limit]
    ]


MATRIX_SCHEMA = "cent-operation-matrix/1"
MATRIX_OPERATIONS = (
    "sum", "difference", "neg", "mult", "div", "exp", "log", "sqrt", "sat",
    "packing", "bounding_box", "delta_sigma_modulator",
)
MATRIX_EVIDENCE_CLASSES = (
    "exact-route",
    "exact-algorithm",
    "structural-template",
    "declared-bridge",
    "declared-analogy",
    "inherited-wheel-candidate",
    "gap",
)
MATRIX_MECHANISM_LINKS: dict[tuple[str, str], str] = {
    ("exact-route", "sum-kcl"): "kcl-conservation",
    ("exact-route", "sum-fluid"): "fluid-continuity",
    ("exact-route", "sum-opamp"): "opamp-summing",
    ("exact-route", "sqrt-log-domain"): "log-domain-sqrt",
    ("exact-route", "delta-sigma-first-order"): "delta-sigma-error-feedback",
    ("declared-bridge", "W24"): "log-domain-sqrt",
}
if not set(MATRIX_MECHANISM_LINKS.values()) <= set(mechanisms.MECHANISM_BY_ID):
    raise RuntimeError("operation matrix links an unknown mechanism id")

_MATRIX_ROLE_LABELS = {
    "compute": "Compute methods",
    "carry": "Carry methods",
    "grounding": "Grounding evidence",
}


def _matrix_route_context(route: Any) -> tuple[str, str]:
    """Return only domains/carriers declared by the route's components."""
    domains = sorted({component.contract.domain for component in route.components})
    carriers = sorted({component.contract.carrier for component in route.components})
    return ", ".join(domains) or "not declared", ", ".join(carriers) or "not declared"


def _matrix_route_rows() -> list[dict[str, Any]]:
    """Exact rows come from the actual route constructors, not a table."""
    routes = (
        ("sum", "compute", assembly.kcl_sum_route(operation="sum"), "assembly.kcl_sum_route"),
        ("sum", "compute", assembly.fluid_sum_route(), "assembly.fluid_sum_route"),
        ("sum", "compute", assembly.opamp_sum_route(operation="sum"), "assembly.opamp_sum_route"),
        (
            "difference", "compute",
            assembly.kcl_sum_route(operation="difference"),
            "assembly.kcl_sum_route",
        ),
        (
            "difference", "compute",
            assembly.fluid_sum_route(operation="difference"),
            "assembly.fluid_sum_route",
        ),
        (
            "difference", "compute",
            assembly.opamp_sum_route(operation="difference"),
            "assembly.opamp_sum_route",
        ),
        ("sqrt", "compute", assembly.log_domain_sqrt_route(), "assembly.log_domain_sqrt_route"),
        (
            "sqrt", "compute", assembly.opamp_multiplier_sqrt_route(),
            "assembly.opamp_multiplier_sqrt_route",
        ),
        ("delta_sigma_modulator", "carry", assembly.delta_sigma_route(), "assembly.delta_sigma_route"),
    )
    rows = []
    for operation, role, route, source in routes:
        domain, carrier = _matrix_route_context(route)
        gaps = list(getattr(route, "gaps", ()) or ())
        rows.append({
            "operation": operation,
            "method": route.name,
            "role": role,
            "evidence": "exact-route",
            "domain": domain,
            "carrier": carrier,
            "source": source,
            "route": route.id,
            "first_gap": gaps[0] if gaps else "no route-level gap declared",
        })
    return rows


def _matrix_template_rows(operation: str) -> list[dict[str, Any]]:
    """Expose structural templates separately from assembled routes."""
    rows = []
    for pattern in SPICE_TEMPLATE_PATTERNS:
        if operation not in pattern.required:
            continue
        rows.append({
            "operation": operation,
            "method": f"{pattern.description} ({pattern.name})",
            "role": "compute",
            "evidence": "structural-template",
            "domain": "not declared in template",
            "carrier": "not declared in template",
            "source": "spice_emitter.SPICE_TEMPLATE_PATTERNS",
            "route": pattern.name,
            "first_gap": "structural netlist template only; no exact assembled route or fabrication netlist",
        })
    return rows


def _matrix_discovery_rows(operation: str) -> list[dict[str, Any]]:
    """Carry exact, bridge and text-only evidence from discovery separately."""
    payload = discover(operation, limit=100)
    rows = []
    for method in payload.get("methods", ()):
        route_model = method.get("route_model")
        if route_model:
            route_gaps = list(route_model.get("gaps") or method.get("gaps") or ())
            rows.append({
                "operation": operation,
                "method": method["name"],
                "role": method["role"],
                "evidence": (
                    "declared-analogy"
                    if route_model.get("kind") == "declared-analogy"
                    else "exact-algorithm"
                    if route_model.get("kind") == "exact-algorithm"
                    else "exact-route"
                ),
                "domain": method["domain"],
                "carrier": method["carrier"],
                "source": "discovery",
                "route": route_model.get("id") or method["id"],
                "first_gap": route_gaps[0] if route_gaps else "no route-level gap declared",
            })
        declared = [
            item for item in method.get("wheel_mappings", ())
            if item.get("status") == "declared"
        ]
        if declared:
            for bridge in declared:
                bridge_gaps = list(bridge.get("gaps") or ())
                rows.append({
                    "operation": operation,
                    "method": f"{bridge.get('wheel')} {bridge.get('name', 'declared bridge')}",
                    "role": "grounding",
                    "evidence": "declared-bridge",
                    "domain": method["domain"],
                    "carrier": method["carrier"],
                    "source": "wheel_mapping",
                    "route": bridge.get("wheel") or "bridge",
                    "first_gap": (
                        bridge_gaps[0] if bridge_gaps
                        else "declared dimensional bridge only; no assembled route or netlist"
                    ),
                })
            continue
        if route_model:
            continue
        text_only = (method.get("wheel_grounding") or {}).get("text_only") or []
        for item in text_only[:2]:
            rows.append({
                "operation": operation,
                "method": f"{item.get('wheel')} text candidate",
                "role": "grounding",
                "evidence": "inherited-wheel-candidate",
                "domain": method["domain"],
                "carrier": method["carrier"],
                "source": "discovery.wheel_material",
                "route": item.get("wheel") or "wheel",
                "first_gap": "text-only wheel match; no graph proof, declared bridge or assembled route",
            })
    return rows


def _matrix_dedupe(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, str, str]] = set()
    unique = []
    for row in rows:
        key = (row["operation"], row["evidence"], row["route"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return unique


def operation_method_matrix(*, operation: str | None = None) -> dict[str, Any]:
    """Return the declared operation × method matrix.

    Rows are sourced only from route constructors, the structural template
    table and discovery's exact/bridge/text evidence.  A missing row is a gap;
    it is never filled with a guessed device or method.
    """
    if operation is not None and operation not in MATRIX_OPERATIONS:
        raise ValueError(
            f"unknown matrix operation: {operation}; "
            f"choose from {', '.join(MATRIX_OPERATIONS)}"
        )
    operations = (operation,) if operation is not None else MATRIX_OPERATIONS
    route_rows = _matrix_route_rows()
    rows: list[dict[str, Any]] = []
    for op in operations:
        rows.extend(row for row in route_rows if row["operation"] == op)
        rows.extend(_matrix_template_rows(op))
        if op != "difference":
            rows.extend(_matrix_discovery_rows(op))
        if not any(row["operation"] == op for row in rows):
            rows.append({
                "operation": op,
                "method": "no declared method",
                "role": "carry" if op == "delta_sigma_modulator" else "compute",
                "evidence": "gap",
                "domain": "not declared",
                "carrier": "not declared",
                "source": "none",
                "route": "gap",
                "first_gap": (
                    "no exact route, structural template, declared bridge or "
                    "inherited wheel candidate"
                ),
            })
    rows = _matrix_dedupe(rows)
    for row in rows:
        row["mechanism"] = MATRIX_MECHANISM_LINKS.get(
            (row["evidence"], row["route"])
        )
    role_order = {"compute": 0, "carry": 1, "grounding": 2}
    evidence_order = {name: index for index, name in enumerate(MATRIX_EVIDENCE_CLASSES)}
    rows.sort(key=lambda row: (
        role_order[row["role"]], row["operation"], evidence_order[row["evidence"]], row["method"],
    ))
    groups = []
    for role in ("compute", "carry", "grounding"):
        items = [row for row in rows if row["role"] == role]
        if items:
            groups.append({
                "role": role,
                "label": _MATRIX_ROLE_LABELS[role],
                "count": len(items),
                "rows": items,
            })
    evidence_counts = {
        evidence: sum(1 for row in rows if row["evidence"] == evidence)
        for evidence in MATRIX_EVIDENCE_CLASSES
    }
    return {
        "ok": True,
        "schema": MATRIX_SCHEMA,
        "scope": "declared evidence only; no fabrication or measured-device row",
        "operations": list(operations),
        "evidence_classes": list(MATRIX_EVIDENCE_CLASSES),
        "rows": rows,
        "groups": groups,
        "summary": {
            "operations": len(operations),
            "rows": len(rows),
            "exact_routes": evidence_counts["exact-route"],
            "exact_algorithms": evidence_counts["exact-algorithm"],
            "structural_templates": evidence_counts["structural-template"],
            "declared_bridges": evidence_counts["declared-bridge"],
            "declared_analogies": evidence_counts["declared-analogy"],
            "inherited_candidates": evidence_counts["inherited-wheel-candidate"],
            "gaps": evidence_counts["gap"],
            "mechanism_links": sum(1 for row in rows if row.get("mechanism")),
            "linked_mechanisms": sorted({
                row["mechanism"] for row in rows if row.get("mechanism")
            }),
            "compute_rows": sum(1 for row in rows if row["role"] == "compute"),
            "carry_rows": sum(1 for row in rows if row["role"] == "carry"),
            "grounding_rows": sum(1 for row in rows if row["role"] == "grounding"),
        },
        "gaps": [
            "Rows are declared evidence, not a fabricated or measured method catalogue.",
            "Carry rows are kept separate from compute and are not operation algorithms.",
            "Declared bridges are dimensional grounding; inherited wheel candidates are text-only.",
            "Mechanism ids are attached only to explicitly mapped route/bridge rows; "
            "templates, text candidates and gaps stay unlinked.",
        ],
        "headline": (
            f"{len(rows)} declared row(s) across {len(operations)} operation(s); "
            f"{evidence_counts['exact-route']} exact route(s), "
            f"{evidence_counts['exact-algorithm']} exact algorithm(s), "
            f"{evidence_counts['structural-template']} structural template(s), "
            f"{evidence_counts['declared-bridge']} declared bridge(s), "
            f"{evidence_counts['declared-analogy']} declared analogy row(s), "
            f"{evidence_counts['inherited-wheel-candidate']} inherited candidate(s), "
            f"{evidence_counts['gap']} gap row(s), "
            f"{sum(1 for row in rows if row.get('mechanism'))} mechanism link(s)."
        ),
    }


def render_matrix(payload: Mapping[str, Any]) -> str:
    """Render the operation matrix with compute and carry sections separate."""
    lines = ["=" * 78, "OPERATION × METHOD MATRIX", "=" * 78]
    lines.append(str(payload.get("headline", "")))
    lines.append(str(payload.get("scope", "")))
    for group in payload.get("groups", ()):
        lines.append("")
        lines.append(f"{group['label']} ({group['count']})")
        lines.append("-" * 78)
        for row in group.get("rows", ()):
            lines.append(
                f"{row['operation']:<24} [{row['evidence']}] {row['method']}"
            )
            lines.append(
                f"  domain={row['domain']} · carrier={row['carrier']} · "
                f"route={row['route']} · source={row['source']}"
            )
            if row.get("mechanism"):
                lines.append(f"  mechanism: {row['mechanism']}")
            lines.append(f"  first gap: {row['first_gap']}")
    if payload.get("gaps"):
        lines.append("")
        lines.append("System gaps")
        for gap in payload["gaps"]:
            lines.append("  - " + str(gap))
    return "\n".join(lines)


def discover(text: str, *, domain: str | None = None, limit: int = 20) -> dict[str, Any]:
    """Return ranked candidate methods for a problem statement.

    The return value is JSON-serialisable and is the public interface used by
    both the CLI and the browser API.
    """
    problem = parse_problem(text, domain=domain)
    envelope_query = _is_envelope_query(problem.normalized)
    if envelope_query and not problem.matched:
        goal = GoalStep(
            1, problem.raw, problem.normalized, "compute", "bounding_box",
            ("compute:envelope", "minimize:area", "bound:points"),
            problem.constraints, True,
        )
        problem = replace(
            problem,
            behavior="compute",
            object="bounding_box",
            goals=goal.goals,
            matched=True,
            steps=(goal,),
        )
    if not problem.matched:
        return {
            "ok": True,
            "schema": SCHEMA,
            "matched": False,
            "query": problem.raw,
            "problem": problem.as_dict(),
            "multi_step": problem.multi_step,
            "steps": [step.as_dict() for step in problem.steps],
            "headline": "No recognised compilation goal; nothing was invented.",
            "pipeline": [
                {
                    "stage": "interpret",
                    "label": "Interpret problem",
                    "status": "gap",
                    "detail": "no recognised behaviour/object pair",
                },
                {
                    "stage": "seed",
                    "label": "Seed exact contracts",
                    "status": "stop",
                    "detail": "not attempted without a goal",
                },
            ],
            "methods": [],
            "groups": [],
            "gaps": ["Name a behaviour and object, for example: compute a square root."],
            "notes": [],
            "suggestions": _suggestions(problem.raw),
            "examples": list(EXAMPLE_QUERIES),
        }

    requested_primitive = (
        problem.object if problem.object in vocabulary.ALL_PRIMITIVES else None
    )
    raw_methods: list[dict[str, Any]] = []
    for op, tags in CAPABILITIES.items():
        if requested_primitive is not None and op != requested_primitive:
            continue
        hits = [tag for tag in tags if tag in problem.goals]
        if not hits:
            continue
        hit = hits[0]
        expansions = expansions_for(op)
        substrates = [row for row in DELTA_SUBSTRATE if row.primitive == op]
        if expansions or substrates:
            for expansion in expansions:
                raw_methods.append(_route_method(op, hit, expansion))
            for substrate in substrates:
                raw_methods.append(_substrate_method(op, hit, substrate))
        else:
            raw_methods.append(_contract_method(op, hit))

    methods = _merge_routes(raw_methods)
    if "optimize:packing" in problem.goals and not any(
        method["primitive"] == "packing" for method in methods
    ):
        methods.append(_packing_method(problem.goals[0]))
    if envelope_query and not any(
        method["primitive"] == "bounding_box" for method in methods
    ):
        methods.append(_envelope_method("compute:envelope"))
    for method in methods:
        method["design"] = _design_metadata(
            method["primitive"], method.get("route_model")
        )
        if method["primitive"] not in {"packing", "bounding_box"}:
            method["evidence"] = _evidence(
                exact=method["contract_exact"],
                simulation=method["simulation"],
                application_declared=method["application_declared"],
                application_available=method["application_available"],
                route=method["route"],
                route_model=method.get("route_model"),
                route_simulation=method.get("route_simulation"),
                device_binding=method.get("device_binding"),
                notes=(),
            )

            wheels, analogies = _wheel_material(method["primitive"], method)
            method["wheel_material"] = wheels
            wheel_docs = _wheel_docs()
            method["wheel_mappings"] = [
                wheel_mapping.mapping_for_match(
                    method, item["wheel"], wheel_docs.get(item["wheel"], {})
                )
                for item in wheels
            ]
            method["wheel_grounding"] = _wheel_grounding(
                method["primitive"], wheels, method["wheel_mappings"]
            )
            method["declared_analogies"] = analogies
        method["score"], method["score_reasons"] = _score(method, problem)

    if domain:
        methods = [method for method in methods if _domain_matches(domain, method)]
    methods.sort(
        key=lambda method: (
            -int(method["score"]),
            0 if method["route"] == "contract" else 1,
            method["domain_class"],
            method["id"],
        )
    )
    methods = methods[: max(1, min(int(limit), 100))]
    for method in methods:
        method["step_indexes"] = [
            step.index for step in problem.steps
            if method["goal"] in step.goals
        ]
    step_payload = []
    for step in problem.steps:
        ids = [
            method["id"] for method in methods
            if step.index in method.get("step_indexes", ())
        ]
        step_payload.append({
            **step.as_dict(),
            "method_count": len(ids),
            "methods": ids,
            "status": "pass" if ids else "gap",
        })

    domains = sorted({method["domain_label"] for method in methods})
    evidence_count = sum(1 for method in methods if method["simulation"] or method["application_available"])
    grounded_count = sum(
        1 for method in methods
        if (method.get("wheel_grounding") or {}).get("status") == "grounded"
    )
    text_only_count = sum(
        1 for method in methods
        if (method.get("wheel_grounding") or {}).get("text_only")
    )
    typed_bridge_count = sum(
        1
        for method in methods
        for item in method.get("wheel_mappings", ())
        if item.get("status") == "declared"
    )
    bridge_phrase = (
        f"{typed_bridge_count} declared typed wheel bridge"
        f"{'' if typed_bridge_count == 1 else 's'}"
    )
    groups = []
    for role, label in (("compute", "Compute"), ("carry", "Carry / represent"), ("solve", "Solve / track")):
        items = [method for method in methods if method["role"] == role]
        if items:
            groups.append({
                "role": role,
                "label": label,
                "count": len(items),
                "methods": items,
            })

    seeded = sorted({method["primitive"] for method in methods})
    routed = [method for method in methods if method["route"] != "contract"]
    route_runs = [
        method["route_simulation"] for method in methods
        if method.get("route_simulation") is not None
    ]
    analogy_runs = [
        method for method in methods
        if method.get("route") == "declared-analogy"
    ]
    exact_route_runs = [
        method for method in methods
        if method.get("route_simulation") is not None
        and method.get("route") != "declared-analogy"
    ]
    passed_runs = sum(1 for run in route_runs if run.get("passed"))
    device_bindings = [
        method["device_binding"] for method in methods
        if method.get("device_binding") is not None
    ]
    passed_bindings = sum(
        1 for binding in device_bindings if binding.get("passed")
    )
    pipeline = [
        {
            "stage": "interpret",
            "label": "Interpret problem",
            "status": "pass",
            "detail": f"{problem.behavior} / {problem.object} · {', '.join(problem.goals)}",
        },
        {
            "stage": "seed",
            "label": "Seed exact contracts",
            "status": "pass" if seeded else "gap",
            "detail": ", ".join(seeded) if seeded else "no contract matched the goal",
        },
        {
            "stage": "expand",
            "label": "Expand declared materials",
            "status": "pass" if routed or route_runs else "gap",
            "detail": (
                f"{len(routed)} material route(s) from EXPANSIONS/DELTA_SUBSTRATE"
                if routed
                else f"{len(route_runs)} contract-level exact route model(s); no material expansion row"
                if route_runs
                else "no material route or exact assembly"
            ),
        },
        {
            "stage": "ground",
            "label": "Ground in wheel material",
            "status": "pass" if grounded_count else "gap",
            "detail": (
                f"{grounded_count} method(s) have graph/declared wheel grounding; "
                f"{text_only_count} also have text-only candidates; {bridge_phrase}"
                if grounded_count
                else (
                    f"no graph/declared wheel grounding; {text_only_count} method(s) "
                    "have text-only candidates only"
                )
            ),
        },
        {
            "stage": "rank",
            "label": "Rank and expose gaps",
            "status": "pass",
            "detail": f"{len(methods)} candidate(s), {evidence_count} with simulation/demo evidence",
        },
        {
            "stage": "simulate",
            "label": "Route-level simulation",
            "status": "pass" if passed_runs else "gap",
            "detail": (
                f"{passed_runs}/{len(route_runs)} declared route model(s) passed; "
                f"{len(exact_route_runs)} exact typed route(s) and "
                f"{len(analogy_runs)} declared analogy probe(s); "
                "device-level nonidealities are not simulated"
                if route_runs
                else "primitive-level simulations exist; selected material routes have no exact route model"
            ),
        },
        {
            "stage": "bind",
            "label": "Bind device quantities",
            "status": "pass" if device_bindings and passed_bindings == len(device_bindings) else "gap",
            "detail": (
                f"{passed_bindings}/{len(device_bindings)} declared reference binding(s) pass; "
                "no fabrication netlist"
                if device_bindings
                else "no declared device binding for the selected route(s)"
            ),
        },
        {
            "stage": "netlist",
            "label": "Emit physical design",
            "status": "gap",
            "detail": (
                f"{len(route_runs)} exact route graph(s) and {len(device_bindings)} device binding(s); no fabrication netlist or geometry"
                if route_runs
                else "no parameterised port graph or netlist for a discovered method yet"
            ),
        },
    ]
    if problem.multi_step:
        pipeline.append({
            "stage": "compose",
            "label": "Compose ordered goal steps",
            "status": "gap",
            "detail": (
                f"{len(problem.steps)} ordered step(s) parsed and matched "
                "independently; no declared handoff or typed composition is executed"
            ),
        })

    global_gaps = [
        "Declared routes are candidates; no method has a generated fabrication netlist yet.",
        "Wheel matches are text-level grounding candidates; declared bridges record port/quantity dimensions and a law, but are not axiom proofs or netlists.",
        "Exact route models have declared reference device bindings where present; generated netlists, geometry and measured-device evidence remain missing.",
    ]
    if problem.multi_step:
        global_gaps.insert(
            0,
            f"Multi-step goal parsed into {len(problem.steps)} ordered steps; "
            "no declared handoff maps one step's output to the next step's input, "
            "so the sequence is not composed or executed as one pipeline.",
        )
    if any(method["primitive"] == "delta_sigma_modulator" for method in methods):
        ds_gap = next(
            (gap for method in methods if method["primitive"] == "delta_sigma_modulator"
             for gap in method["gaps"] if "quantize" in gap),
            None,
        )
        if ds_gap:
            global_gaps.insert(0, f"Delta-sigma physical gap: {ds_gap}.")

    step_phrase = (
        f"{len(problem.steps)} ordered goal step(s) parsed; "
        if problem.multi_step else ""
    )
    headline = step_phrase + (
        f"{len(methods)} candidate method(s) across {len(domains)} domain label(s); "
        f"{evidence_count} have simulation or demo evidence; "
        f"{grounded_count} have graph/declared wheel grounding; "
        f"{text_only_count} have text-only candidates; "
        f"{bridge_phrase}; "                f"{len(route_runs)} have a declared route model "
                f"({len(exact_route_runs)} exact, {len(analogy_runs)} declared analogy); "
                f"{len(device_bindings)} have a declared device binding; "
        "none is a complete physical compiler output."
    )
    notes = list(problem.assumptions)
    if not methods:
        notes.append("The domain filter removed all candidates; remove it to compare domains.")

    return {
        "ok": True,
        "schema": SCHEMA,
        "matched": True,
        "query": problem.raw,
        "problem": problem.as_dict(),
        "multi_step": problem.multi_step,
        "steps": step_payload,
        "headline": headline,
        "domains": domains,
        "pipeline": pipeline,
        "methods": methods,
        "groups": groups,
        "gaps": global_gaps,
        "notes": notes,
        "suggestions": [],
        "examples": list(EXAMPLE_QUERIES),
    }


def render_text(payload: Mapping[str, Any]) -> str:
    """Render discovery results for the terminal."""
    lines = ["=" * 78, "PHYSICAL METHOD DISCOVERY", "=" * 78]
    lines.append(f"Problem: {payload.get('query', '')}")
    problem = payload.get("problem", {})
    if payload.get("matched"):
        if payload.get("multi_step"):
            lines.append(
                f"Interpreted as: {len(payload.get('steps', ()))} ordered goal steps"
            )
        else:
            lines.append(
                "Interpreted as: "
                f"{problem.get('behavior')} / {problem.get('object')} / "
                f"{', '.join(problem.get('goals', ())) or '(none)'}"
            )
        if problem.get("constraints"):
            lines.append("Constraints: " + ", ".join(problem["constraints"]))
    if payload.get("multi_step"):
        lines.append("")
        lines.append("Goal steps")
        for step in payload.get("steps", ()):
            lines.append(
                f"  {step.get('index')}. {step.get('behavior')} / {step.get('object')} · "
                f"{', '.join(step.get('goals', ())) or '(none)'}"
            )
            if "method_count" in step:
                lines.append(
                    f"     {step['method_count']} returned candidate(s), status {step.get('status')}"
                )
    lines.append("")
    lines.append(str(payload.get("headline", "")))
    if payload.get("pipeline"):
        lines.append("")
        lines.append("Pipeline")
        for stage in payload["pipeline"]:
            lines.append(f"  [{stage['status']:<5}] {stage['label']}: {stage['detail']}")
    lines.append("")

    for group in payload.get("groups", ()):
        lines.append(f"{group['label']} ({group['count']})")
        lines.append("-" * 78)
        for index, method in enumerate(group["methods"], 1):
            lines.append(
                f"{index:>2}. {method['name']}  [{method['domain_label']}, {method['carrier']}]"
            )
            lines.append(f"    route: {method['route']} · contract: {method['contract_status']}")
            if method.get("components"):
                lines.append("    material: " + ", ".join(method["components"]))
            if method.get("wheel_material"):
                wheels = ", ".join(
                    f"{item['wheel']} ({item['scope']})" for item in method["wheel_material"]
                )
                lines.append("    wheel text candidates: " + wheels)
            grounding = method.get("wheel_grounding") or {}
            for candidate in grounding.get("candidates") or []:
                lines.append(
                    f"    wheel graph proof: {candidate['wheel']} {candidate['axiom_id']} "
                    f"→ {candidate['formula']}"
                )
            if grounding.get("text_only"):
                lines.append(
                    "    wheel grounding gap: text-only candidates are not scored: "
                    + ", ".join(item["wheel"] for item in grounding["text_only"])
                )
            declared_mappings = [
                item for item in method.get("wheel_mappings", ())
                if item.get("status") == "declared"
            ]
            if declared_mappings:
                for mapping in declared_mappings:
                    ports = ", ".join(
                        f"{port['method_port']}→{port['device_symbol']}→{port['wheel_quantity']}"
                        for port in mapping.get("ports", ())
                        if port.get("status") == "pass"
                    )
                    lines.append(
                        f"    wheel bridge: {mapping['wheel']} declared "
                        f"[{ports}]; residual=0"
                    )
            gap_mappings = len(method.get("wheel_material", ())) - len(declared_mappings)
            if gap_mappings:
                lines.append(
                    f"    wheel bridges: {gap_mappings} candidate(s) without a declared typed bridge"
                )
            evidence = [
                f"{item['kind']}={item['status']}" for item in method.get("evidence", ())
                if item["kind"] in {
                    "dynamic simulation", "application / demo", "route model",
                    "route simulation", "device binding"
                }
            ]
            if evidence:
                lines.append("    evidence: " + ", ".join(evidence))
            scan = method.get("wheel_scan") or {}
            if scan:
                selected = ", ".join(scan.get("selected") or ())
                adjacent = ", ".join(
                    item["wheel"] for item in scan.get("candidates", ())
                    if item.get("role") == "adjacent"
                )
                lines.append(
                    f"    cross-domain scan: {scan.get('wheels_scanned')} wheels; "
                    f"selected {selected}; adjacent {adjacent or '(none)'}"
                )
            lines.append("    coverage: " + method["coverage"])
            for gap in method["gaps"][:3]:
                lines.append("    gap: " + gap)
        lines.append("")

    if payload.get("suggestions"):
        lines.append("Not matched. Nearby contracts: " + ", ".join(
            item["name"] for item in payload["suggestions"]
        ))
        lines.append("")
    if payload.get("gaps"):
        lines.append("System gaps")
        for gap in payload["gaps"]:
            lines.append("  - " + gap)
    if payload.get("notes"):
        lines.append("")
        lines.append("Assumptions / notes")
        for note in payload["notes"]:
            lines.append("  - " + note)
    lines.append("")
    lines.append("Examples: " + " | ".join(payload.get("examples", ())))
    return "\n".join(lines)


__all__ = [
    "CAPABILITIES", "CAPABILITY_BASIS", "EXAMPLE_QUERIES", "GoalStep",
    "MATRIX_EVIDENCE_CLASSES", "MATRIX_OPERATIONS", "MATRIX_SCHEMA",
    "ProblemSpec", "SCHEMA", "discover", "operation_method_matrix",
    "parse_problem", "render_matrix", "render_text",
]
