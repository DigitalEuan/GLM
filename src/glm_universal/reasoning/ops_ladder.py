"""``glm_universal.reasoning.ops_ladder`` -- the operations ladder as a domain.

The owner's research note (``source_material/devops_ladder/DevOps-Ladder.txt``)
proposes a DevOps ladder of ten tiers -- the machine substrate at the bottom,
culture at the top -- as "a deterministic, layered dictionary/wheel for GLM",
in which "each tier rests on the one below it" and "higher tiers compose lower
ones".  This module is that ladder as a register the GLM can reason over:

* **the terms** -- the note's 97, tier by tier and in the note's order, each
  with a short identifier and its display name as the note writes it;
* **the compositions** -- for each term, the terms it is built from.  These
  are *declared* (the note names the tiers, not the edges), and the register
  enforces the note's rule as a refinement check: a term is built only from
  terms of a strictly lower tier or from terms listed earlier in its own tier,
  so the rank ``(tier, index)`` strictly decreases along every edge and the
  graph has no cycle (``RequestProject/GLM/OperationsLadder.lean``,
  ``layered_wf``);
* **the projection** onto the Geometric-Cybernetic ladder the note recommends
  as the primary wheel -- one GC term per DevOps term, declared;
* **the cross-overs** -- a term of this ladder beside an object the GLM
  already holds, each resolved against the tree.

Everything derived from these -- closures, grounds, relations, the carrier,
the projection census -- is computed, never stored.  Exact integers and
``Fraction`` throughout (D7).  ``studies/OPERATIONS_LADDER_STUDY.md`` is the
study.
"""

from __future__ import annotations

import re
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

# ===========================================================================
# 1.  THE TERMS AND THEIR DECLARED COMPOSITIONS
# ===========================================================================

#: The note's tier titles, tier 0 first.
TIER_TITLES: Tuple[str, ...] = (
    "Machine Substrate",
    "Shell & Control Plane",
    "Configuration & State",
    "Source & Artifact",
    "Automation & Task",
    "Continuous Integration & Delivery (CI/CD)",
    "Infrastructure & Runtime",
    "Observability & Feedback",
    "Reliability & Operations",
    "Culture & System Properties",
)

#: ``(identifier, display name as the note writes it, composition)``, one
#: tuple of rows per tier, in the note's order.  A composition names only
#: terms of a strictly lower tier or earlier terms of the same tier.
TIERS: Tuple[Tuple[Tuple[str, str, Tuple[str, ...]], ...], ...] = (
    # ----- Tier 0 -- Machine Substrate: the primitives, built from nothing
    (
        ("process", "Process", ()),
        ("thread", "Thread", ()),
        ("file", "File / Directory", ()),
        ("stream", "Stream (stdin / stdout / stderr)", ()),
        ("env_var", "Environment Variable", ()),
        ("exit_code", "Exit Code / Return Code", ()),
        ("signal", "Signal", ()),
        ("permission", "Permission / Ownership", ()),
        ("device", "Device / Node", ()),
        ("resource", "Memory / Disk / Network Interface", ()),
    ),
    # ----- Tier 1 -- Shell & Control Plane
    (
        ("command", "Command", ("process", "stream", "exit_code")),
        ("argument", "Argument / Flag", ("command",)),
        ("variable", "Variable (SET / export)", ("env_var",)),
        ("assignment", "Assignment", ("variable",)),
        ("conditional", "Conditional (IF / ELSE / test / [ ])",
         ("exit_code", "variable")),
        ("loop", "Loop (FOR / WHILE)", ("conditional", "process")),
        ("jump", "Jump / Label (GOTO / CALL / function)", ("process",)),
        ("redirection", "Redirection (`>`, `>>`, `<`, `2>&1`)",
         ("stream", "file", "command")),
        ("pipe", "Pipe (`|`)", ("stream", "command")),
        ("substitution", "Substitution / Expansion", ("variable", "command")),
        ("exit_handling", "Exit / Errorlevel handling",
         ("exit_code", "conditional")),
        ("script", "Script / Batch file",
         ("command", "file", "conditional", "loop", "jump")),
        ("shebang", "Shebang / Interpreter", ("script", "process")),
    ),
    # ----- Tier 2 -- Configuration & State
    (
        ("config_file", "Config File / Manifest", ("file", "variable")),
        ("template", "Template", ("config_file", "substitution")),
        ("parameter", "Parameter / Key-Value", ("variable", "argument")),
        ("secret", "Secret / Credential", ("parameter", "permission")),
        ("environment", "Environment (dev / stage / prod)",
         ("env_var", "config_file", "parameter")),
        ("state", "State (desired vs actual)",
         ("file", "process", "config_file")),
        ("idempotence", "Idempotence", ("state", "script")),
        ("drift", "Drift", ("state",)),
        ("version", "Version / Tag / Hash", ("file", "state")),
    ),
    # ----- Tier 3 -- Source & Artifact
    (
        ("repository", "Source / Repository", ("file", "version")),
        ("commit", "Commit / Change", ("repository", "version", "state")),
        ("branch", "Branch", ("commit",)),
        ("build", "Build", ("script", "repository", "process")),
        ("compile", "Compile / Package", ("build", "file")),
        ("artifact", "Artifact / Binary / Image",
         ("compile", "file", "version")),
        ("dependency", "Dependency / Lockfile",
         ("artifact", "version", "config_file")),
        ("registry", "Registry / Repository (artifact store)",
         ("artifact", "repository", "permission")),
        ("provenance", "Provenance / SBOM",
         ("artifact", "commit", "dependency", "version")),
    ),
    # ----- Tier 4 -- Automation & Task
    (
        ("task", "Task / Job / Step", ("script", "command", "exit_code")),
        ("reusable_script", "Script (reusable)", ("script", "parameter")),
        ("workflow", "Workflow / Playbook",
         ("task", "conditional", "exit_handling")),
        ("trigger", "Trigger (manual / event / schedule)",
         ("signal", "workflow")),
        ("gate", "Gate / Checkpoint", ("exit_handling", "conditional", "task")),
        ("retry", "Retry / Timeout / Backoff",
         ("loop", "exit_code", "task", "signal")),
        ("parallelism", "Parallelism / Fan-out", ("process", "thread", "task")),
        ("orchestration", "Orchestration (of tasks)",
         ("workflow", "trigger", "parallelism", "gate")),
    ),
    # ----- Tier 5 -- Continuous Integration & Delivery (CI/CD)
    (
        ("pipeline", "Pipeline", ("workflow", "pipe", "gate", "trigger")),
        ("stage", "Stage / Phase", ("task", "gate", "pipeline")),
        ("ci", "Continuous Integration (CI)",
         ("pipeline", "commit", "build", "trigger")),
        ("continuous_delivery", "Continuous Delivery",
         ("ci", "artifact", "environment")),
        ("continuous_deployment", "Continuous Deployment",
         ("continuous_delivery", "trigger")),
        ("build_test_package_promote", "Build → Test → Package → Promote",
         ("stage", "build", "compile", "artifact")),
        ("quality_gate", "Quality Gate", ("gate", "stage", "exit_code")),
        ("artifact_promotion", "Artifact Promotion",
         ("artifact", "registry", "environment", "quality_gate")),
        ("rollback", "Rollback / Roll-forward",
         ("version", "state", "artifact_promotion")),
        ("progressive_delivery", "Canary / Blue-Green / Rolling",
         ("artifact_promotion", "environment", "rollback")),
    ),
    # ----- Tier 6 -- Infrastructure & Runtime
    (
        ("host", "Host / Node / Instance", ("device", "resource", "process")),
        ("container", "Container / Image",
         ("process", "permission", "artifact", "file")),
        ("volume", "Volume / Persistent Storage",
         ("file", "device", "container")),
        ("service", "Network / Service / Endpoint",
         ("resource", "process", "host")),
        ("orchestrator", "Orchestrator (scheduler, controller)",
         ("container", "host", "orchestration")),
        ("iac", "Infrastructure as Code (IaC)",
         ("config_file", "version", "state", "script")),
        ("provisioning", "Provisioning", ("iac", "host", "idempotence")),
        ("scaling", "Scaling (horizontal / vertical)",
         ("orchestrator", "service", "parallelism")),
        ("immutable_infra", "Immutable Infrastructure",
         ("container", "artifact", "version")),
        ("platform", "Platform / Self-service",
         ("orchestrator", "provisioning", "pipeline", "permission")),
    ),
    # ----- Tier 7 -- Observability & Feedback
    (
        ("metric", "Metric", ("resource", "process")),
        ("log", "Log", ("stream", "file")),
        ("trace", "Trace", ("log", "process", "thread")),
        ("event", "Event", ("signal", "log")),
        ("health_check", "Health Check / Probe",
         ("service", "exit_code", "metric")),
        ("alert", "Alert / Notification", ("metric", "event", "signal")),
        ("dashboard", "Dashboard", ("metric", "log", "trace")),
        ("slo", "SLI / SLO / Error Budget", ("metric", "health_check")),
        ("telemetry", "Telemetry", ("metric", "log", "trace", "event")),
        ("feedback_loop", "Feedback Loop",
         ("telemetry", "alert", "loop", "pipeline")),
    ),
    # ----- Tier 8 -- Reliability & Operations
    (
        ("deployment_strategy", "Deployment Strategy",
         ("progressive_delivery", "rollback", "environment")),
        ("incident", "Incident / Outage", ("alert", "slo", "service")),
        ("recovery", "Recovery / MTTR", ("incident", "rollback", "metric")),
        ("circuit_breaker", "Circuit Breaker / Bulkhead",
         ("service", "health_check", "retry")),
        ("chaos", "Chaos / Fault Injection",
         ("signal", "incident", "health_check")),
        ("capacity", "Capacity / Load", ("scaling", "metric", "resource")),
        ("on_call", "On-call / Escalation",
         ("alert", "incident", "permission")),
        ("runbook", "Runbook / Playbook (ops)",
         ("script", "incident", "workflow")),
        ("postmortem", "Post-mortem / Retrospective (blameless)",
         ("incident", "log", "trace", "recovery")),
    ),
    # ----- Tier 9 -- Culture & System Properties
    (
        ("shared_ownership", "Shared Ownership / “You build it, you run it”",
         ("on_call", "pipeline", "service")),
        ("collaboration", "Collaboration / Cross-functional",
         ("shared_ownership", "repository", "dashboard")),
        ("feedback_speed", "Feedback Speed", ("feedback_loop", "ci", "metric")),
        ("blamelessness", "Psychological Safety / Blamelessness",
         ("postmortem", "collaboration")),
        ("continuous_improvement", "Continuous Improvement",
         ("postmortem", "feedback_loop", "metric")),
        ("small_batch", "Lean / Small Batch",
         ("commit", "ci", "artifact_promotion")),
        ("measurement_driven", "Measurement-driven",
         ("metric", "slo", "dashboard")),
        ("platform_thinking", "Platform Thinking",
         ("platform", "reusable_script", "shared_ownership")),
        ("value_stream", "Flow / Value Stream",
         ("pipeline", "feedback_speed", "small_batch")),
    ),
)


# ===========================================================================
# 2.  THE GEOMETRIC-CYBERNETIC LADDER AND THE DECLARED PROJECTION
# ===========================================================================

#: The note's recommended primary wheel, tier 0 first.  ``boundary`` appears
#: at tiers 4 and 7 in the note; the second is ``system boundary`` here.
GC_TIERS: Tuple[Tuple[str, ...], ...] = (
    ("point", "vector", "distance", "lattice", "codeword", "syndrome",
     "coset", "projection", "embedding", "invariant"),
    ("group", "ring", "field", "module", "homomorphism", "kernel", "image",
     "exact sequence", "composition", "inverse"),
    ("state", "transition", "operator", "path", "composition of operators",
     "fixed point", "orbit", "conjugation"),
    ("distinction", "entropy", "mutual information", "channel", "noise",
     "capacity", "encoding", "decoding", "fidelity", "loss"),
    ("observable", "measurement", "probe", "outcome", "consistency",
     "verification", "refusal", "boundary"),
    ("goal", "error", "feedback", "regulator", "stabilisation", "gain",
     "delay", "hierarchy of control", "requisite variety"),
    ("intention", "plan", "action", "consequence", "model", "prediction",
     "adaptation", "learning"),
    ("system", "system boundary", "environment", "coupling", "emergence",
     "self-organisation", "autonomy"),
)

#: One GC term per DevOps term, declared with the register (hypothesis H of
#: the study is measured over it, never tuned to it).
PROJECTION: Dict[str, str] = {
    # tier 0
    "process": "path", "thread": "path", "file": "point",
    "stream": "channel", "env_var": "state", "exit_code": "outcome",
    "signal": "transition", "permission": "boundary", "device": "embedding",
    "resource": "capacity",
    # tier 1
    "command": "operator", "argument": "vector", "variable": "state",
    "assignment": "transition", "conditional": "distinction",
    "loop": "orbit", "jump": "transition", "redirection": "projection",
    "pipe": "composition", "substitution": "homomorphism",
    "exit_handling": "verification", "script": "composition of operators",
    "shebang": "decoding",
    # tier 2
    "config_file": "encoding", "template": "coset", "parameter": "vector",
    "secret": "boundary", "environment": "environment", "state": "state",
    "idempotence": "fixed point", "drift": "error", "version": "codeword",
    # tier 3
    "repository": "path", "commit": "transition", "branch": "path",
    "build": "operator", "compile": "encoding", "artifact": "image",
    "dependency": "coupling", "registry": "module", "provenance": "path",
    # tier 4
    "task": "action", "reusable_script": "operator", "workflow": "plan",
    "trigger": "transition", "gate": "verification", "retry": "feedback",
    "parallelism": "coupling", "orchestration": "regulator",
    # tier 5
    "pipeline": "composition of operators", "stage": "operator",
    "ci": "consistency", "continuous_delivery": "channel",
    "continuous_deployment": "action", "build_test_package_promote": "path",
    "quality_gate": "refusal", "artifact_promotion": "transition",
    "rollback": "inverse", "progressive_delivery": "probe",
    # tier 6
    "host": "point", "container": "boundary", "volume": "state",
    "service": "operator", "orchestrator": "regulator", "iac": "encoding",
    "provisioning": "action", "scaling": "gain", "immutable_infra": "invariant",
    "platform": "system",
    # tier 7
    "metric": "observable", "log": "measurement", "trace": "path",
    "event": "outcome", "health_check": "probe", "alert": "error",
    "dashboard": "observable", "slo": "goal", "telemetry": "channel",
    "feedback_loop": "feedback",
    # tier 8
    "deployment_strategy": "plan", "incident": "error",
    "recovery": "stabilisation", "circuit_breaker": "regulator",
    "chaos": "noise", "capacity": "capacity", "on_call": "hierarchy of control",
    "runbook": "plan", "postmortem": "learning",
    # tier 9
    "shared_ownership": "coupling", "collaboration": "coupling",
    "feedback_speed": "delay", "blamelessness": "self-organisation",
    "continuous_improvement": "adaptation", "small_batch": "delay",
    "measurement_driven": "measurement", "platform_thinking": "system",
    "value_stream": "path",
}


# ===========================================================================
# 3.  THE CROSS-OVERS -- A TERM BESIDE SOMETHING THE GLM ALREADY HOLDS
# ===========================================================================

#: ``(term, kind, file, name, what the cross-over says)``.  ``kind`` is
#: ``python`` (a top-level function or class of the file) or ``lean`` (a
#: theorem or definition of the file).  Each is resolved by reading the file,
#: never by importing it.
CROSSOVERS: Tuple[Tuple[str, str, str, str, str], ...] = (
    ("version", "python", "glm_universal/signoff/rules.py", "file_digest",
     "a version hash is what the sign-off signs every unit against: a digest "
     "addresses integrity, never meaning (D3, D4)"),
    ("version", "python", "glm_universal/substrate/golay_decode.py",
     "decode_or_detect",
     "a checksum that can also repair: the Golay decoder corrects up to three "
     "flipped bits of a 24-bit word and detects four"),
    ("drift", "python", "glm_universal/reasoning/drift.py", "drift_report",
     "drift between desired and actual is the drift between an exact orbit "
     "and its rounded run, measured step by step"),
    ("idempotence", "python", "glm_universal/reasoning/drift.py", "fixed_point",
     "an idempotent apply is a map whose image is its fixed-point set; the "
     "drift module's fixed point is the state a reconciliation converges to"),
    ("rollback", "python", "glm_universal/reasoning/reversible.py",
     "round_backward",
     "a rollback is an inverse: the reversible gate rounds run backward to "
     "the exact starting carrier"),
    ("feedback_loop", "python", "glm_universal/engineering/delta_sigma.py",
     "first_order_bits",
     "a delta-sigma modulator is a feedback loop whose error is fed back "
     "every step; the engineering surface already answers what it does"),
    ("retry", "lean", "RequestProject/GLM/ProbeBudget.lean", "miss_bound",
     "a retry budget is a probe budget: k(1-p)^B <= delta once B is at least "
     "(k/c) log(k/delta)"),
    ("slo", "lean", "RequestProject/GLM/ProbeBudget.lean",
     "budget_serves_every_type",
     "an error budget fixed in advance: 1056 starts keep the miss chance at "
     "most 1/1000 for every deep-hole type"),
    ("pipeline", "lean", "RequestProject/GLM/ConnectedMachine.lean",
     "route_cons_none",
     "the connected router is a pipeline of surfaces: a stage put in front "
     "changes the verdict only for text it reads"),
    ("quality_gate", "python", "glm_universal/signoff/ledger.py", "plan",
     "the repository's own quality gate: the close re-runs every stale unit "
     "and signs only what passed"),
    ("on_call", "python", "glm_universal/runtime/escalation_loop.py",
     "ladder_for",
     "escalation as a declared ladder: a re-reading is declared and costed "
     "before it is taken (D13)"),
    ("dashboard", "python", "glm_universal/figures.py", "package_figures",
     "every figure a document shows is generated by the code that reports "
     "it (D6)"),
    ("health_check", "python", "glm_universal/capabilities/harness.py",
     "holds",
     "the capability probes: each one holds or breaks, and a surprise is a "
     "failed health check"),
    ("platform", "python", "glm_universal/runtime/toolbox.py", "run_tool",
     "self-service: every reasoning module reachable as `tool <name>`"),
)


# ===========================================================================
# 4.  THE REGISTER, READ
# ===========================================================================

#: The repository root (``glm_universal/reasoning`` is three down).
_ROOT = Path(__file__).resolve().parents[3]
#: The supplied note, the control the register is checked against (O2).
NOTE = "source_material/devops_ladder/DevOps-Ladder.txt"


@lru_cache(maxsize=None)
def _table() -> Dict[str, Tuple[int, int, str, Tuple[str, ...]]]:
    out: Dict[str, Tuple[int, int, str, Tuple[str, ...]]] = {}
    for tier, rows in enumerate(TIERS):
        for index, (ident, display, parts) in enumerate(rows):
            out[ident] = (tier, index, display, parts)
    return out


def term_ids() -> Tuple[str, ...]:
    """Every term, tier 0 first and in the note's order."""
    return tuple(ident for rows in TIERS for ident, _, _ in rows)


def tier_of(term: str) -> int:
    return _table()[term][0]


def index_of(term: str) -> int:
    return _table()[term][1]


def display(term: str) -> str:
    return _table()[term][2]


def parts_of(term: str) -> Tuple[str, ...]:
    return _table()[term][3]


def rank(term: str) -> Tuple[int, int]:
    """``(tier, index)``: strictly decreases along every composition edge
    (``GLM.OperationsLadder.layered_wf`` with the lexicographic order)."""
    t = _table()[term]
    return (t[0], t[1])


def layering_violations() -> List[Tuple[str, str]]:
    """Edges ``term -> part`` along which the rank does not decrease, and
    parts that are not terms.  Empty for a layered register."""
    bad: List[Tuple[str, str]] = []
    table = _table()
    for term in term_ids():
        for part in parts_of(term):
            if part not in table or not rank(part) < rank(term):
                bad.append((term, part))
    return bad


@lru_cache(maxsize=None)
def closure(term: str) -> frozenset:
    """``term`` and everything it is built from, transitively."""
    out: Set[str] = {term}
    for part in parts_of(term):
        out |= closure(part)
    return frozenset(out)


def ground(term: str) -> frozenset:
    """The tier-0 primitives a term rests on."""
    return frozenset(t for t in closure(term) if tier_of(t) == 0)


@lru_cache(maxsize=None)
def path_counts(term: str) -> Tuple[int, ...]:
    """Distinct composition paths from ``term`` to each tier-0 primitive."""
    prims = [ident for ident, _, _ in TIERS[0]]
    if tier_of(term) == 0:
        return tuple(1 if p == term else 0 for p in prims)
    total = [0] * len(prims)
    for part in parts_of(term):
        for k, v in enumerate(path_counts(part)):
            total[k] += v
    return tuple(total)


@lru_cache(maxsize=None)
def depth(term: str) -> int:
    """The longest composition chain from ``term`` down to tier 0."""
    return 1 + max((depth(p) for p in parts_of(term)), default=-1)


def chain(top: str, bottom: str) -> Optional[Tuple[str, ...]]:
    """One shortest composition chain ``top ⊃ … ⊃ bottom`` (breadth first,
    parts in declared order), or ``None``."""
    if bottom not in closure(top):
        return None
    frontier: List[Tuple[str, ...]] = [(top,)]
    seen = {top}
    while frontier:
        nxt: List[Tuple[str, ...]] = []
        for path in frontier:
            if path[-1] == bottom:
                return path
            for part in parts_of(path[-1]):
                if part not in seen:
                    seen.add(part)
                    nxt.append(path + (part,))
        frontier = nxt
    return None  # pragma: no cover -- closure says it exists


# ===========================================================================
# 5.  RELATIONS, COMPUTED
# ===========================================================================

def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


@lru_cache(maxsize=None)
def _lookup() -> Dict[str, str]:
    out: Dict[str, str] = {}
    for ident in term_ids():
        out[_norm(ident)] = ident
        disp = display(ident)
        out[_norm(disp)] = ident
        for piece in re.split(r"\s*/\s*|\(|\)|,", disp):
            p = _norm(piece)
            if p and p not in out:
                out[p] = ident
    return out


def resolve(text: str) -> Optional[str]:
    """A term from its identifier, its display name, or one of the names the
    display joins with a slash (``exit code``, ``errorlevel handling``…)."""
    n = _norm(text)
    table = _lookup()
    if n in table:
        return table[n]
    if n.endswith("s") and n[:-1] in table:
        return table[n[:-1]]
    return None


def relation(a: str, b: str) -> Dict[str, object]:
    """How two terms stand to each other, read from their closures."""
    ca, cb = closure(a), closure(b)
    ga, gb = ground(a), ground(b)
    union = ga | gb
    overlap = Fraction(len(ga & gb), len(union)) if union else Fraction(0)
    out: Dict[str, object] = {
        "a": a, "b": b, "tier_a": tier_of(a), "tier_b": tier_of(b),
        "ground_overlap": overlap,
        "shared_ground": sorted(ga & gb, key=rank),
        "projection": (PROJECTION[a], PROJECTION[b]),
    }
    if a == b:
        out["kind"] = "same"
        return out
    if a in cb:
        out["kind"] = "part_of"
        out["chain"] = chain(b, a)
        return out
    if b in ca:
        out["kind"] = "contains"
        out["chain"] = chain(a, b)
        return out
    shared = ca & cb
    maximal = [t for t in shared
               if not any(t in closure(u) and u != t for u in shared)]
    composers = [t for t in term_ids() if a in closure(t) and b in closure(t)]
    least: List[str] = []
    if composers:
        low = min(tier_of(t) for t in composers)
        least = sorted((t for t in composers if tier_of(t) == low), key=rank)
    out["kind"] = "related" if shared else "unrelated"
    out["shared_parts"] = sorted(maximal, key=rank)
    out["least_common_composers"] = least
    return out


def relation_sentence(a: str, b: str) -> str:
    r = relation(a, b)
    da, db = display(a), display(b)
    proj = (f"; on the Geometric-Cybernetic ladder they project to "
            f"{r['projection'][0]} and {r['projection'][1]}")
    ov = r["ground_overlap"]
    tail = (f"; their grounds share {len(r['shared_ground'])} primitive(s) "
            f"(overlap {ov})")
    if r["kind"] == "same":
        return f"{da} is the same term" + proj
    if r["kind"] in ("part_of", "contains"):
        path = " ⊃ ".join(display(t) for t in r["chain"])
        lead = (f"{da} is a part of {db}" if r["kind"] == "part_of"
                else f"{db} is a part of {da}")
        return f"{lead}, by the chain {path}" + tail + proj
    shared = ", ".join(display(t) for t in r["shared_parts"]) or "nothing"
    least = ", ".join(display(t) for t in r["least_common_composers"]) \
        or "no term"
    return (f"neither is a part of the other; both are built from {shared}; "
            f"the least terms built from both are {least}" + tail + proj)


# ===========================================================================
# 6.  THE CARRIER
# ===========================================================================

LAYOUT: Tuple[str, ...] = tuple(
    [f"paths_to_{ident}" for ident, _, _ in TIERS[0]] + ["tier"]
    + [f"closure_tier_{k}" for k in range(10)]
    + ["index", "parts", "depth"])


def carrier(term: str) -> Tuple[int, ...]:
    counts = [0] * 10
    for t in closure(term):
        counts[tier_of(t)] += 1
    return (path_counts(term) + (tier_of(term),) + tuple(counts)
            + (index_of(term), len(parts_of(term)), depth(term)))


def _codec():
    from ..data_objects.base import Codec, DataObject

    class OperationsCodec(Codec):
        """A term as its 24 counts, and back: (tier, index) names the term,
        and the other 22 coordinates must recompute."""

        domain = "operations"
        layout = LAYOUT

        def encode(self, source: str) -> DataObject:
            return DataObject(name=source, domain=self.domain,
                              carrier=carrier(source),
                              attributes={"display": display(source),
                                          "tier": tier_of(source)},
                              layout=self.layout,
                              provenance={"source": NOTE})

        def decode(self, obj: DataObject) -> str:
            tier, index = int(obj.carrier[10]), int(obj.carrier[21])
            if not (0 <= tier < len(TIERS) and 0 <= index < len(TIERS[tier])):
                raise ValueError("no term at that (tier, index)")
            term = TIERS[tier][index][0]
            if tuple(int(x) for x in obj.carrier) != carrier(term):
                raise ValueError(f"carrier does not recompute for {term}")
            return term

    return OperationsCodec()


def operations_objects() -> Tuple[object, ...]:
    """Every term as a checked :class:`~glm_universal.data_objects.base.
    DataObject` (both round trips asserted)."""
    codec = _codec()
    return tuple(codec.check(t) for t in term_ids())


def carrier_census() -> Dict[str, object]:
    objs = operations_objects()
    carriers = [o.carrier for o in objs]
    by_ground: Dict[Tuple[int, ...], List[str]] = {}
    by_set: Dict[frozenset, List[str]] = {}
    for t in term_ids():
        by_ground.setdefault(path_counts(t), []).append(t)
        by_set.setdefault(ground(t), []).append(t)
    return {"terms": len(objs), "round_trips": len(objs),
            "distinct": len(set(carriers)),
            "distinct_path_vectors": len(by_ground),
            "distinct_ground_sets": len(by_set),
            "largest_ground_set_class": max(len(v) for v in by_set.values())}


def nearest_terms(prims: Sequence[str], tier: Optional[int] = None,
                  limit: int = 3) -> List[Tuple[str, Fraction]]:
    """Address a term from a description: the terms whose ground is nearest
    (Jaccard distance, exact) to the given primitives, optionally at one
    tier."""
    want = frozenset(prims)
    rows = []
    for t in term_ids():
        if tier is not None and tier_of(t) != tier:
            continue
        g = ground(t)
        u = g | want
        d = Fraction(len(g.symmetric_difference(want)), len(u)) if u else Fraction(0)
        rows.append((d, rank(t), t))
    rows.sort()
    return [(t, d) for d, _, t in rows[:limit]]


# ===========================================================================
# 7.  THE NOTE, THE PROJECTION AND THE CROSS-OVERS, CHECKED
# ===========================================================================

def note_terms() -> List[List[str]]:
    """The bullet terms of the note's ten DevOps tiers, read from the
    supplied file (the control of mark O2)."""
    text = (_ROOT / NOTE).read_text(encoding="utf-8-sig")
    text = text.split("**How to use this", 1)[0]
    tiers: List[List[str]] = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("### Tier"):
            tiers.append([])
        elif line.startswith("- ") and tiers:
            tiers[-1].append(line[2:].strip())
    return tiers


def note_check() -> Dict[str, object]:
    tiers = note_terms()
    mine = [[display(i) for i, _, _ in rows] for rows in TIERS]
    mismatches = []
    for k, (theirs, ours) in enumerate(zip(tiers, mine)):
        if theirs != ours:
            mismatches.append(k)
    used = set(p for t in term_ids() if tier_of(t) > 0 for p in parts_of(t))
    idle = [i for i, _, _ in TIERS[0] if not any(
        i in closure(t) for t in term_ids() if tier_of(t) > 0)]
    return {"tiers_in_note": len(tiers), "terms_in_note":
            sum(len(t) for t in tiers), "terms": len(term_ids()),
            "mismatched_tiers": mismatches,
            "layering_violations": layering_violations(),
            "ungrounded": [t for t in term_ids() if not ground(t)],
            "idle_primitives": idle, "direct_parts_used": len(used)}


def gc_tier(term: str) -> int:
    for k, row in enumerate(GC_TIERS):
        if term in row:
            return k
    raise KeyError(term)


def projection_census() -> Dict[str, object]:
    """Hypothesis H: along a composition edge ``a ⊃ b`` the GC tier of
    ``proj(a)`` is at least that of ``proj(b)``."""
    edges = [(t, p) for t in term_ids() for p in parts_of(t)]
    monotone = [(a, b) for a, b in edges
                if gc_tier(PROJECTION[a]) >= gc_tier(PROJECTION[b])]
    inverted = [(a, b) for a, b in edges if (a, b) not in set(monotone)]
    by_tier = []
    for k, rows in enumerate(TIERS):
        tiers = [gc_tier(PROJECTION[i]) for i, _, _ in rows]
        by_tier.append(Fraction(sum(tiers), len(tiers)))
    return {"edges": len(edges), "monotone": len(monotone),
            "share": Fraction(len(monotone), len(edges)),
            "threshold": Fraction(3, 4),
            "holds": Fraction(len(monotone), len(edges)) >= Fraction(3, 4),
            "inverted": inverted, "mean_gc_tier_by_tier": by_tier,
            "gc_terms_used": len(set(PROJECTION.values())),
            "every_term_projected": set(PROJECTION) == set(term_ids()),
            "every_target_known": all(any(v in row for row in GC_TIERS)
                                      for v in PROJECTION.values())}


def _defined_names(kind: str, path: Path) -> Set[str]:
    text = path.read_text(encoding="utf-8")
    if kind == "python":
        return set(re.findall(r"^(?:def|class)\s+([A-Za-z_][A-Za-z0-9_]*)",
                              text, re.MULTILINE))
    return set(re.findall(
        r"^\s*(?:@\[[^\]]*\]\s*)?(?:private\s+|protected\s+)?(?:noncomputable\s+)?"
        r"(?:theorem|lemma|def|abbrev|structure|inductive)\s+([^\s(:{\[]+)",
        text, re.MULTILINE))


def crossover_census() -> List[Dict[str, object]]:
    """Each declared cross-over, resolved by reading its file."""
    rows = []
    for term, kind, rel, name, says in CROSSOVERS:
        path = (_ROOT / "src" / rel if kind == "python"
                else _ROOT / "src" / "lean" / rel)
        ok = path.exists() and name in _defined_names(kind, path)
        rows.append({"term": term, "kind": kind, "file": rel, "name": name,
                     "resolves": ok, "says": says})
    return rows


def term_sentence(term: str) -> str:
    """What the register says about one term."""
    parts = ", ".join(display(p) for p in parts_of(term)) or "nothing (a primitive)"
    grd = ", ".join(display(p) for p in sorted(ground(term), key=rank))
    xs = [r for r in crossover_census() if r["term"] == term]
    cross = "".join(f"; cross-over: {r['says']} ({r['file']}, {r['name']})"
                    for r in xs)
    return (f"{display(term)} (tier {tier_of(term)}, "
            f"{TIER_TITLES[tier_of(term)]}) is built from {parts}; it grounds "
            f"in {grd}; its depth is {depth(term)}; it projects to "
            f"{PROJECTION[term]} (Geometric-Cybernetic tier "
            f"{gc_tier(PROJECTION[term])})" + cross)
