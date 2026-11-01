# GLM Conversation — Complete Module Documentation

## What This Is

**One file** (`glm_conversation.py`). Drop it into the GLM repository root. Import it:

```python
from glm_conversation import GLMConversation
glm = GLMConversation()
```

It gives the GLM five capabilities, unified into one class, all in exact arithmetic.

## The Five Capabilities

### 1. `talk()` — Multi-turn Dialogue

```python
glm.talk("What is energy?")
glm.talk("How does it relate to force?")
glm.talk("What have we been talking about?")
```

- Maintains conversation context with exact rational recency decay (9/10 per turn)
- Context centroid identifies "what the conversation is about"
- Nearest carriers to centroid across registers
- Follow-up suggestions when queries are unclear

### 2. `explain()` — Three Column Thinking Explanations

```python
exp = glm.explain("how does light bend near a massive object")
for step in exp.steps:
    print(step.language)       # Column 1: physical meaning
    print(step.mathematics)    # Column 2: exact dimensional analysis
    print(step.verification)   # Column 3: what the GLM checked
```

For "how does light bend near a massive object", the GLM produces 20 steps including:

- **Step 15:** Light propagates at speed c (L T⁻¹). `verify speed_of_light = length / time: holds`
- **Step 16:** Gravitational field has dimension L T⁻². `verify gravitational_field = force / mass: holds`
- **Step 17:** E = mc² means photons have effective mass m = hf/c². `verify energy = mass × c²: holds`
- **Step 18:** Curvature has dimension L⁻¹. Einstein field equation: G_μν = (8πG/c⁴) T_μν
- **Step 19:** Deflection δθ = 4GM/(rc²). `dim(GM) = L³T⁻² = dim(rc²). Dimensions match.`
- **Step 20:** SI7(c) = (1,0,-1,0,0,0,0), SI7(g) = (1,0,-2,0,0,0,0). They differ in time exponent.

Each step is verified by the GLM's own machinery — dimensional consistency, coherence, Golay decoding, layer escalation.

### 3. `reason()` — Propose, Check, Refine

```python
result = glm.reason("force : energy :: pressure : ?")
print(result.answer)     # "adhesion_energy"
print(result.verified)   # True
```

Generates candidates through:
- **Analogy transport** — uses the GLM's 5 named relation models
- **Nearest-neighbour** — exact Griess distances in Q²⁴
- **Dimensional derivation** — from the 10 EXT10 generators

Verifies each through intent-appropriate strategies:
- Analogies → register membership + coherence
- Exploration → coherence + lattice proximity
- Verification → dimensional equality

### 4. `attend()` — Subspace Attention

```python
for name, d2 in glm.attend("energy", subspace="dimension", top_k=5):
    print(f"{name}: d² = {d2}")
```

Subspaces act like attention heads:
- `"dimension"` — EXT10 + SI7 exponents (what the quantity *is*)
- `"scale"` — magnitude only
- `"full"` — all 24 coordinates (everything)

### 5. `ask()` — Native Query with Confidence

```python
answer, confidence = glm.ask("verify energy = mass * speed_of_light^2")
print(answer.holds)           # True
print(confidence.score)       # "high"
print(confidence.rationale)   # "separate at substrate — clearly distinct"
```

Confidence scored from layer separation:
- **high** — concepts separate at substrate (clearly distinct carriers)
- **medium** — concepts separate at integer (same dimensional family)
- **low** — concepts only separate at Griess/universal (very similar)
- **identical** — concepts are the same at all layers

## Architecture

```
GLMConversation
├── _Context          — conversation state with rational recency decay
├── _extract()        — finds register concepts in natural language
├── _classify()       — intent classification (describe/compare/verify/...)
├── _confidence()     — layer-based confidence scoring
├── talk()            — conversational interface
├── explain()         — Three Column Thinking explanation builder
│   ├── _identify_physics()  — physics-aware concept mapping
│   ├── _build_explanation() — multi-step chain construction
│   ├── _chain_light_gravity() — light/gravity specific chain
│   ├── _chain_light()       — light-specific chain
│   └── _chain_gravity()     — gravity-specific chain
├── reason()          — propose-check-refine loop
│   ├── analogy transport (via GLM's 5 relation models)
│   ├── nearest-neighbour (exact Griess distances)
│   └── dimensional derivation (10 EXT10 generators)
├── attend()          — subspace attention
└── ask()             — native query + confidence
```

## What Makes This Different From an LLM

| | LLM | GLM Conversation |
|---|---|---|
| **Generation** | Statistical patterns from training data | Mathematical structure from registers |
| **Verification** | Implicit (training loss) | Explicit (dimensional analysis, NRCI, Golay decoding) |
| **Refusal** | Hallucinates | Refuses with proof |
| **Explanation** | Plausible text | Verified carriers + exact math |
| **Confidence** | Softmax probability | Layer separation depth |
| **Arithmetic** | Float approximation | Exact rational (Fraction) |

## Invariants

- Exact arithmetic (`int` / `Fraction` / `F₂`) on all computation paths
- No float constructed on any path that feeds a result
- No randomness anywhere
- Standard library + `glm_universal` only
- Single file, no additional dependencies

## Tested Operations

| Operation | Status | Example |
|-----------|--------|---------|
| Multi-turn dialogue | ✅ | 4-turn physics conversation |
| Concept explanation | ✅ | 20-step light/gravity explanation |
| Analogy reasoning | ✅ | `force:energy::pressure:?` → adhesion_energy |
| Nearest-neighbour | ✅ | energy → kinetic_energy (d²=0) |
| Subspace attention | ✅ | dimension subspace finds energy family |
| Confidence scoring | ✅ | E=mc² → "high" (substrate separation) |
| Multi-word concepts | ✅ | "speed of light" → speed_of_light |
| Context tracking | ✅ | Centroid identifies conversation topic |
| Layer comparison | ✅ | energy vs torque with facet attribution |
