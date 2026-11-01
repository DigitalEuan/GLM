# GLM Conversation v2 — Porting & Usage Guide

## What this is

`glm_conversation_v2.py` is the next iteration of the GLM conversational
module. It runs against the **real `glm_universal` substrate** (no stub)
and implements:

- All 5 immediate bug fixes from the research feedback
- 4 architectural additions (episodic memory, typed relations,
  executable reasoning plan, trace-derived explanations with
  provenance spans)
- Strict back-compatibility with v1's public API

The demo output is in `v2_demo_output.txt`.

---

## Installation

Drop `glm_conversation_v2.py` into your GLM repository root, alongside
the existing `glm_conversation.py`. Both can coexist — v2 does not
modify v1.

```python
from glm_conversation_v2 import GLMConversation
glm = GLMConversation()
```

No new dependencies. Standard library + `glm_universal` only.

---

## The 5 bug fixes

### #1 — Intent ordering (fixed)

v1 checked `"does"` under `verify` BEFORE checking `"how does"` under
`explain`. So `"how does light bend"` was classified as `verify`.

v2 checks multi-word explain patterns (`"how does"`, `"why does"`,
`"how can"`, `"what causes"`, etc.) FIRST. Bare `"does"` only triggers
`verify` when paired with `"="` or a verify verb (`"verify"`,
`"is it true that"`, `"holds"`, etc.).

Verified:
```
✓ 'how does light bend near a massive object'  -> explain
✓ 'why does gravity affect light'              -> explain
✓ 'what causes gravitational lensing'           -> explain
✓ 'verify energy = mass * speed_of_light^2'    -> verify
✓ 'is it true that force = mass * acceleration'-> verify
✓ 'does energy equal mass times c squared'     -> explore   (not verify!)
```

### #2 — Float-free NRCI display (fixed)

v1 called `float(nrci_val)` for display, violating the "no float on any
path that feeds a result" invariant — even though the float was only
for display, the invariant was stated as absolute.

v2 introduces `_fmt_frac(x, places)`, a pure-integer-arithmetic
formatter that converts a `Fraction` to a decimal string using
`(2 * num * scale + 1) // (2 * den)` (round-half-up). No `float()`
is constructed anywhere on any path.

Verified:
```
_fmt_frac(Fraction(3, 4), 4)                         = "0.7500"
_fmt_frac(Fraction(1, 3), 6)                         = "0.333333"
_fmt_frac(Fraction(-5, 8), 4)                        = "-0.6250"
_fmt_frac(Fraction(25500000000000000000,
                   47168713655770732267), 4)         = "0.5406"
```

### #3 — Analogy verification (fixed)

v1's `_verify_candidate("analogy")` returned `True` for any resolved
carrier. A valid carrier is not evidence that it is the correct
analogue.

v2 introduces `_verify_analogy(session, a, b, c, d)` which checks the
**transported relation** by component-wise dimensional-ratio equality
on the EXT10 exponents:

```
Δ(a→b) == Δ(c→d)   ⟺   dim(b)/dim(a) == dim(d)/dim(c)
```

This is the exact condition for a multiplicative analogy. Verified:

```
✓ force:energy::pressure:adhesion_energy  holds=True
  (Δ(force→energy) = Δ(pressure→adhesion_energy) = (1, 0, 1, 0, 0, 0, 0, 0, 0, 0))

✓ force:energy::pressure:wavelength  holds=False
  (axes differ: ['L', 'M', 'T'])

✓ force:energy::pressure:spring_constant  holds=True
  (same Δ transport)
```

Additionally, v2 surfaces ties honestly. When
`physics_analogy('force','energy','pressure')` returns 7 tied
candidates (all with d²=0), v2 reports `status="ambiguous"` in the
plan rather than silently picking the alphabetically-first one.

### #4 — Rich context summary (fixed)

v1's `summary()` retained only names and domains — the conversation's
structure was lost.

v2's `MemoryGraph.summary()` preserves:
- Turn boundaries (each Memory is a discrete episode)
- Speaker (`user` / `glm`)
- Raw text
- Concepts (resolved register names)
- Intent (describe / compare / verify / analogy / explain / explore)
- Confidence
- Provenance (`user_input` / `glm_derived` / `register_lookup`)
- Relations asserted that turn
- All typed relations in the graph (with turn, provenance, confidence)

Verified output:
```
turns:    4
episodes: 4
relations: 6
Last episode:
  turn 4, intent=verify, text='verify energy = mass * speed_of_light^2'
  concepts: ['energy', 'mass']
  relations asserted this turn:
    [('energy', 'mentioned_after', 'mass'),
     ('energy', 'derived_from', 'mass')]
All typed relations in graph:
  [2] energy mentioned_after torque     [glm_derived,   high]
  [3] force mentioned_after mass        [glm_derived,   high]
  [3] mass mentioned_after acceleration [glm_derived,   high]
  [3] force derived_from mass           [user_asserted, medium]
  [4] energy mentioned_after mass       [glm_derived,   high]
  [4] energy derived_from mass          [user_asserted, medium]
```

### #5 — Honest fallback (fixed)

v1's `reason()` returned the first unverified candidate as `answer`
while setting `verified=False`. The caller could not distinguish a
verified answer from a guess.

v2 returns `answer=None` when no candidate passes verification, and
surfaces the best unverified candidate as `hypothesis` with
`confidence="low"` and an explicit rationale:

> "none verified — hypothesis: alfven_speed (unverified, do not
> present as fact)"

Verified:
```
Query: derive speed_of_light from mass
answer:     None
hypothesis: alfven_speed  (explicitly labelled, unverified)
verified:   False
confidence: low — none verified — hypothesis: alfven_speed
             (unverified, do not present as fact)
plan failed_step: plan:2
```

---

## The 4 architectural additions

### A — Episodic memory store (MAGMA / GAAMA inspired)

Each turn is stored as a `Memory` dataclass:

```python
@dataclass(frozen=True)
class Memory:
    turn: int
    speaker: str              # "user" | "glm"
    text: str                 # raw input text
    concepts: Tuple[str, ...]
    carriers: Tuple[Tuple[Any, ...], ...]   # exact 24-vectors
    relations: Tuple[Relation, ...]
    intent: str
    confidence: str           # high/medium/low/identical
    provenance: str           # user_input | glm_derived | register_lookup
```

The weighted centroid is kept as ONE retrieval feature among several
(`MemoryGraph.centroid()`). Graph expansion and intent matching are
the others.

### B — Typed relation graph

Relations are stored separately from geometric similarity:

```python
@dataclass(frozen=True)
class Relation:
    a: str
    relation_type: str       # causes | contrasts_with | part_of |
                             # equals | mentioned_after |
                             # affected_by | derived_from
    b: str
    provenance: str          # user_asserted | glm_derived | inferred
    turn: int
    confidence: str          # high/medium/low
```

`MemoryGraph.expand_relations(concept, max_depth=2)` walks the graph
from a concept, returning typed relations rather than blended vectors.

### C — Executable reasoning plan

`reason()` now emits a typed `ReasoningPlan`:

```python
@dataclass(frozen=True)
class PlanStep:
    op: str               # resolve | derive | verify | retrieve |
                          # explain | refuse
    target: str
    status: str          # pending | ok | failed | skipped | ambiguous
    result: str
    failure_reason: str  # empty iff status == "ok"
    derivation_node: str  # "plan:0", "plan:1", ... (for Span back-pointers)

@dataclass(frozen=True)
class ReasoningPlan:
    intent: str
    steps: Tuple[PlanStep, ...]
    final_answer: Optional[str]
    final_verified: bool
    failed_step: Optional[str]
    hypothesis: Optional[str]
```

Failed steps are exposed, not hidden. Example trace for
`force : energy :: pressure : ?`:

```
✓ [resolve ] ok        | force, energy, pressure
? [derive  ] ambiguous | force:energy::pressure:?     (7 tied candidates)
✓ [verify  ] ok        | analogy force:energy::pressure:adhesion_energy
✓ [verify  ] ok        | analogy force:energy::pressure:spring_constant
  ... (7 candidates, all verified)
✓ [explain ] ok        | adhesion_energy
```

### D — Trace-derived explanations with provenance spans

Every `Step` now carries `spans` — a tuple of `Span(text, provenance,
derivation_node)` objects. Each sentence in the language column points
to one or more derivation nodes.

Four provenance tags:

| Tag | Meaning |
|---|---|
| `registered_axiom` | Loaded directly from the register |
| `retrieved_fact` | Asserted by user or retrieved from memory |
| `derived_expression` | Computed by a PlanStep |
| `explanatory_gloss` | Prose — NOT a verified claim |

The light/gravity chain no longer prints `δθ = 4GM/(rc²)` as if
verified when it is only documentation. It is now tagged as
`explanatory_gloss` with an explicit derivation_node `gloss:deflection_formula`.

Example — the E=mc² step:

```
Step 17: Einstein's E = mc². A photon has energy E = hf, so effective
         mass m = E/c² = hf/c². Gravity affects light because photons
         carry energy, even though they are massless.

  Spans:
    [derived_expression] node=plan:E_mc2
      text: "Einstein's E = mc². "
    [explanatory_gloss] node=gloss:photon_effective_mass
      text: "A photon has energy E = hf, so effective mass m = E/c² = hf/c². "
    [explanatory_gloss] node=gloss:gravity_affects_light
      text: "Gravity affects light because photons carry energy, even though
             they are massless."
```

The verification column now reads:

> `dim(gravitational_constant × mass) = L³T⁻² (verified). dim(length × c²)
> = L³T⁻² (verified). Ratio is dimensionless (verified). Formula
> δθ = 4GM/(rc²): external — not derived from register.`

---

## Public API

### Back-compatible (v1 signatures preserved)

```python
glm.talk(input_text: str) -> Answer
glm.explain(question: str) -> Explanation
glm.reason(question: str) -> ReasonResult
glm.attend(concept: str, subspace: str = "full",
           domain: str = "physics", top_k: int = 10
           ) -> Tuple[Tuple[str, Fraction], ...]
glm.ask(query: str) -> Tuple[Optional[Any], Confidence]
```

### New in v2 (additive)

```python
glm.memory_graph() -> MemoryGraph
glm.trace(query: str) -> ReasoningPlan
glm.recall(concepts: Sequence[str], intent: str = "explore",
           top_k: int = 5) -> List[Tuple[Memory, Fraction]]
```

### Returned objects — old vs new attributes

| Object | v1 attributes | v2 additions |
|---|---|---|
| `Answer` | text, kind, confidence, context, suggestions | `trace: Optional[ReasoningPlan]`, `memory_refs: Tuple[int, ...]` |
| `Explanation` | question, steps, summary, carriers_used | (unchanged — `Step.spans` is the addition) |
| `Step` | language, mathematics, verification, carriers | `spans: Tuple[Span, ...]` |
| `ReasonResult` | answer, method, confidence, steps, verified | `hypothesis: Optional[str]`, `plan: Optional[ReasoningPlan]` |
| `Confidence` | score, first_separation, rationale | (unchanged) |

Old attribute access still works. v1 callers see no breakage.

---

## Combined-score retrieval

`MemoryGraph.recall()` implements:

$$
S(m, q) = \alpha \cdot S_{\text{geometry}}(m, q)
        + \beta  \cdot S_{\text{graph}}(m, q)
        + \gamma \cdot S_{\text{recency}}(m, q)
        + \delta \cdot S_{\text{intent}}(m, q)
$$

Defaults: $\alpha = 1/2, \beta = 1/4, \gamma = 1/8, \delta = 1/8$.

All four components are exact `Fraction` in $[0, 1]$. The result is a
**set of memories**, not a blended vector.

Verified: for query `[energy, mass]` with `intent='verify'`, recall
surfaces turn 4 (`verify energy = mass * speed_of_light^2`) with score
17/20, beating turn 2 (`Compare energy and torque`) at 193/400 —
even though both contain "energy", because intent matching matters.

---

## File layout

```
/
├── glm_conversation_v2.py    # the module (2456 lines)
├── v2_demo_output.txt          # demo output (evidence)
└── PORTING.md                  # this file
```

---