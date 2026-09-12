# The GLM Reverse-Call Planner
## A Problem-Driven Architecture for the Geometric Language Machine

---

## What this is

The GLM has 67 reasoning modules. Its runtime dispatches to 1–3 of them per query, selected by a fixed 20-entry kind table decided *before* the problem is inspected. This is "a lot of tools that could be used but not a system that has the ability to use what it needs when needed."

The reverse-call planner replaces the kind-table with a **problem-driven** architecture:

```
string → PROBLEM (goal, operands, domain, constraints)
       → PLANNER inspects the problem, SELECTS tools
       → tools run in cost order, each checked
       → results composed into a multi-step Solution
       → if all tools refuse, names every tool tried and why
```

## Why we're building it

1. **The controller proves the shape works.** `reasoning/controller.py` already has a propose/check/refuse loop with a pluggable heuristic registry, beam search, two refusal modes (invariant = proof, exhausted = budget), and independent re-verification. It was locked behind a report subject. We exposed it as `derive_plan` and it worked — the system discovered `energy = length × length × mass ÷ time ÷ time` by searching, then verified it.

2. **The generalised planner proves composition works.** We built a 6-tool registry and a planner that selects tools based on the problem, not the kind. It composed `controller + verifier` for derivations, `reference` for meaning, `escalation` for layer comparison, `exact_real` for irrationals, `nearest_neighbor` for proximity — all from one entry point. 9 of 10 tests passed.

3. **The remaining work is mechanical.** Registering each of the 67 modules as a Tool, adding the cross-register bridge, adding pipeline composition, and adding budget-aware search — these extend a working pattern, not invent a new one.

## What changed from the proof of concept

| Proof of concept (v1) | Full planner (v2) |
|---|---|
| 6 tools registered | All 67 reasoning modules registered |
| First success wins | Budget-aware search: try all applicable tools |
| No sub-goal composition | Pipeline composition: derive → verify → escalate |
| No cross-register bridge | Escalation consults reference resolver |
| Manual tool implementation per tool | Declarative `@tool` decorator with `applies_to`/`run`/`verify` |

## How it works

### The Problem

```python
@dataclass(frozen=True)
class Problem:
    raw: str                          # original query text
    operands: Tuple[str, ...]         # parsed operands
    goal: str                         # "derive", "verify", "compare", etc.
    domain: Optional[str] = None      # "physics", "chemistry", etc.
    constraints: Dict[str, str] = {} # k=5, places=20, etc.
```

The Problem carries everything a tool needs. The `goal` is a **hint** for the planner, not a dispatcher — the planner may override it if a tool with a different goal applies.

### The Tool

```python
@dataclass(frozen=True)
class Tool:
    name: str
    applies_to: Callable[[Problem, Session], bool]   # cheap precondition
    run: Callable[[Problem, Session], ToolResult]    # the computation
    postcondition: str                               # what it establishes
    cost: int = 1                                    # lower = tried first
    can_verify: Optional[Callable] = None            # independent checker
```

Each of the 67 reasoning modules gets a `Tool` entry. The `applies_to` function is a cheap check (does this tool handle this kind of problem?). The `run` function wraps the module's existing API.

### The Planner

```python
class Planner:
    def plan(self, problem, session) -> Solution:
        1. Find all applicable tools (sorted by cost)
        2. Try each tool (cheapest first)
        3. Check each result with the tool's verifier
        4. If a tool produces sub-goals, feed them back
        5. Compose results into a multi-step Solution
        6. If all tools refuse, name every tool tried and why
```

The planner is an instance of `SearchLoop.lean`'s specification: propose (run tool), check (verifier), refine (sub-goals) or refuse.

### The cross-register bridge

When a tool needs a register name that's actually a semantics-layer alias (e.g. `c` → `speed_of_light`), the bridge consults `reference.resolve()` first, then uses the resolved meaning's underlying register name.

### Pipeline composition

The planner can compose multiple tools into one Solution:
```
derive energy → [controller builds plan]
             → [verifier checks plan]  
             → [escalation finds which layer separates energy from torque]
             → 3-tool pipeline, one Solution, 3 verified steps
```

### Budget-aware search

The planner tries all applicable tools until the budget is exhausted, not just the first success. If multiple tools can answer, the cheapest verified result wins. If all tools refuse, the planner names every tool tried and why.

## The UBP discipline

- **No floats.** All tool results are exact rationals.
- **No random.** The planner is deterministic.
- **No SHA-256.** Tool selection is by `applies_to`, not by hashing.
- **The process IS the number.** The controller's propose/check/refuse loop IS the reasoning.
