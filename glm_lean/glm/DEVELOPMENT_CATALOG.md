# GLM development catalog

A version-by-version reading of the archive (`glm_paper.zip`, 22 files), and a
map from every idea in it to its place — or its absence — in the consolidated
system shipped in this directory.

The archive is not a linear series. Three strands run through it:

* **the paper strand** — `glm_paper.py`, `glm_paper_2`, `glm_paper_3`,
  `glm_paper_6`, `glm_paper_7`, `glm_paper_10`: the write-up;
* **the companion strand** — `glm_geometric_reasoner`, `glm_v17_companion`:
  the operational engine;
* **the research strand** — `glm_v8_honest`, `glm_v9`, `glm_versor_fibers`,
  `glm_v10` … `glm_v19`: one experiment per file, each preserving the previous
  one and adding a tier.

All twenty-one GLM files import a common substrate, `ubp_unified_v5 (2).py`
(4,174 lines: `GOLAY_ENGINE`, `LEECH_ENGINE`, exact arithmetic helpers, plus a
great deal of unrelated UBP machinery). The consolidated system replaces that
dependency with `glm_substrate.py`, which is self-contained, exact, and
audited.

---

## 1. Version notes

### `glm_paper.py` — the first paper (v1)
Establishes the shape everything later keeps: Golay `[24,12,8]` substrate, MOG
`4×6` grid, GF(4) column labels with `Z_4` fibre keys, "0-bit reconstruction
error", and the integer companion `(Z^7,+)` as the answer to characteristic-2
aliasing. Quotes "100% precision vs 89% over 6,793 equation pairs" and cites
Lean theorems by name.

### `glm_paper_2.py` — trimmed restatement
Same abstract, single author, tidier module layout. No new mathematics.

### `glm_paper_3.py` — v5.5 "hardened exact edition"
First real refinement: the 16-state column bijection is written out as a table;
syndrome weight `|σ(v)|` is separated from Hamming distance to the anchor;
telemetry becomes a structured `EvaluationRecord`; full 4096-coset syndrome
decoding.

### `glm_paper_6.py` — v7.0 "master unified executable"
The paper becomes an operational script for the first time: the write-up is the
module docstring and running the file verifies it. Introduces the four
"ontological tiers" (Reality / Information / Activation / Potential) as the
four MOG rows.

### `glm_paper_7.txt` — v7.1 "master integrated specification"
The version the user singled out as the format to keep: abstract, theoretical
foundation, numbered sections, then an executable verification run. Names the
companion (`glm_geometric_reasoner.py`) explicitly.

### `glm_geometric_reasoner.txt` — companion v1.0
The operational engine: 7D dimension parsing, exact composition in `(Z^7,+)`,
an inversion solver (`v = sqrt(E/m)`, `P = VI = I²R`), an adversarial equation
auditor, NRCI/TAX telemetry, and a 3D scene export to `scene_3d.json`.

### `glm_v8_honest.py` — the honesty pass
A rewrite in response to critique. Dimensional analysis is presented **first**
and as classical; the Golay layer is demoted to an optional representation;
the mod-2 ceiling is admitted to be self-inflicted; the "100% precision" claim
is withdrawn as a restatement of what dimensional analysis already gives. Two
headline theorems are stated formally and a threat model for error correction
is defined. The most valuable single file in the archive.

### `glm_v9.txt` — versor fibres, walks, syndrome-as-dynamics
Identifies the `Z_4` fibre index with the fourth roots of unity `⟨1, i, -1,
-i⟩`; a walk through concepts accumulates phase, and closed walks carry a
winding number (the `E = mc²` round trip is quoted as winding −2). Reads the
syndrome as a field residual and the snap as its resolution. Keeps v8's honest
framing.

### `glm_versor_fibers.py` — the versor engine, standalone
The v9 versor material extracted: fibre → versor map, phase accumulator,
`M_24` permutation generators on the `4×6` grid, and the `Co_0 = 2^12 : M_24`
reading (signs × permutations).

### `glm_v10.py` — quaternionic fibres and an `M_24` engine
Replaces the complex versors by the quaternion units `{1, i, j, k}`, so that
composition stops commuting; adds executable grid permutations with a
Golay-preservation test, and a quaternionic walk.

### `glm_v11.py` — Leech stabilisers, `H^6`
"Tier 2": freeze a Leech vector and take the residual symmetry — `Co_2`
(norm 4), `Co_3` (norm 6) — selected per concept from its syndrome; the six
fibres are laid out as a 6-dimensional quaternionic vector `H^6`.

### `glm_v12.py` — quaternionic matrices, holonomy, `L_0`
Three vectors: `6×6` quaternionic unitary matrices replacing heuristic row
swaps; path-dependent holonomy as the ordered product around a closed loop;
and a first Virasoro-style conformal weight `L_0`.

### `glm_v13.py` — Griess algebra, Monster classes, moonshine
"Tier 4": a truncated Griess element `(α, v)` with a product whose
non-associative correction term is built from the snap; a lift of each
concept's stabiliser to a Monster conjugacy class keyed on syndrome and TAX;
McKay–Thompson coefficient tables; the 2A involution and its idempotent.

### `glm_v14.py` — `2^(1+24)`, 1A concepts, `Λ²`
Implements the extraspecial group abstractly (12 anticommuting pairs plus a
central `z`) and acts with it on 24 coordinates; brute-force search of
`[-3,3]^7` for syndrome-zero "1A" concepts (221 found); extends the Griess
element by the 276-dimensional `Λ²(R^24)` piece.

### `glm_v15.py` — the faithful 4096D action, 299D, vacuum renormalisation
The single biggest correction in the research strand: the 24-dimensional
action **cannot** satisfy `[x_i, y_i] = z`, so the extraspecial group is moved
to its faithful `2^12 = 4096`-dimensional Schrödinger representation. Adds the
299-dimensional traceless symmetric space `S²₀(R^24)`, and renormalises `L_0`
so that the "1A vacuum" sits at zero.

### `glm_v16.py` — optimisation and a 4096D equation checker
POPCOUNT tables for the 4096D action, an optional NumPy path verified against
the pure-Python one, the `98,304 = 24 × 4096` tensor product `R^24 ⊗ V_4096`,
and an equation checker that compares concepts as 4096D states.

### `glm_paper_10.py` + `glm_v17_companion.py` — paper and companion, together
The archive's high-water mark for presentation: a full academic paper with the
five-tier pipeline, and a companion implementing it end to end
(`Z^7 → F_2^24 → MOG → H^6 → Co_0 → L_0 → Griess(600D) → 2^(1+24) → 𝕄`). The
companion states the "no XOR composition" rule explicitly.

### `glm_v18.py` — lines, coupled tensor, OPE, colour
The 98,280 lines of minimal vectors (`552 + 48,576 + 49,152`), a fully coupled
`R^24 ⊗ V_4096`, an OPE-derived `L_0`, and — the most immediately usable idea
in the late archive — the observation that a hex colour `#RRGGBB` *is* a 24-bit
Golay word, with the snap as a chromatic correction.

### `glm_v19.py` — semidirect product, vertex operators, colour discovery
The last version. Adds the semidirect product of the extraspecial group with
permutations of the twelve pairs; formal vertex operators `Y(v,z)` with an OPE;
a search for syndrome-free "chromatic ground state" colours; a candid note that
the type-3 minimal vectors need the holy construction, which is not derived.

---

## 2. Overall development catalog

Where each idea ended up. "Shipped" means it is in this directory, exact, and
verified by a numbered claim of `glm_paper.py` or by `test_glm.py`.

| # | idea | first seen | status here | where |
|---|---|---|---|---|
| 1 | Golay `[24,12,8]` substrate, weight enumerator, covering radius | v1 | shipped, verified exhaustively | `glm_substrate.py`, C1–C6 |
| 2 | MOG `4×6` grid, GF(4) labels, hexacode shadow | v1 | shipped, alignment verified on all 4096 codewords | `glm_substrate.py`, C7–C8 |
| 3 | `16 = 4 × 4` column bijection | v1 (table in v5.5) | shipped, exhaustive | `glm_codec.py`, C10 |
| 4 | "0-bit reconstruction error" of the four-tier encoder | v1 | **corrected**: that encoder is many-to-one and dropped the amount-of-substance exponent; replaced by a bijective base-9 carrier | paper §3.2, C11–C12 |
| 5 | integer companion `(Z^7,+)`, exact equation checking | v1 | shipped and **promoted**: it is no longer a companion to the bit pattern but the state itself, with the carrier derived from it | `glm_metrology.py`, C14–C15, C42–C43 |
| 6 | "100% vs 89% over 6,793 pairs" | v1 | **withdrawn as unreproducible** (no generator in the archive), replaced by three regenerable measurements | paper §5.4, C15, C23, C24 |
| 7 | mod-2 ceiling as a theorem | v8 | **proved**, machine-checked | `../RequestProject/GLM.lean` |
| 8 | syndrome vs. anchor distance separated | v5.5 | shipped | `SnapMeta` in `glm_substrate.py` |
| 9 | four ontological tiers | v7.0 | kept as an interpretive view only | `ontological_profile` |
| 10 | inversion solver, Buckingham-Pi, scene export | companion v1 | shipped and generalised (Smith normal form, rational fallback) | `glm_reasoner.py`, C16–C17 |
| 11 | TAX / NRCI cost layer | UBP | shipped, exact, and quarantined as stipulative | paper §7 |
| 12 | honest framing (classical / novel / stipulated) | v8 | shipped as a section of the paper | paper §9 |
| 13 | `Z_4` fibre = quarter turn (versor) | v9 | shipped, exact in `Z_4` | `glm_geometry.py` §1, C25 |
| 14 | quaternionic fibres `{1,i,j,k}`, `H^6` | v10, v11 | shipped with exact integer quaternions; the map is a bijection of sets, **not** a homomorphism, and this is now stated | `glm_geometry.py` §2, C25–C26 |
| 15 | walks and winding numbers | v9 | shipped, with the integrality proved and verified over a generated family | `glm_geometry.py` §3, C27 |
| 16 | holonomy around a loop | v12 | shipped, exact, path dependence measured | `glm_geometry.py` §4, C28 |
| 17 | `M_24` permutation engine | v10 | **completed**: the membership test is kept, and the group itself is now built — a matroid-based automorphism search plus a Schreier–Sims chain give a 5-transitive group of order 244,823,040, and an exhaustive enumeration of the 48 automorphisms fixing five coordinates proves by orbit–stabiliser that it is all of `Aut(C) = M_24` | `glm_m24.py`, `glm_monster.py` §1, C18, C37–C40 |
| 18 | `Co_2` / `Co_3` stabiliser selection | v11 | **dropped**: the selection was a relabelling of the syndrome, with no stabiliser computed | catalog note only |
| 19 | conformal weight `L_0`, "1A vacuum" renormalisation | v12, v15 | **corrected**: the `H^6` norm is 6 for *every* concept, so the archive's `L_0` is exactly `σ/2`; the observable is kept, the name dropped | `glm_geometry.py` §5, C29 |
| 20 | 1A concept search over `[-3,3]^7` | v14 | shipped and completed: the lawful census is exact over the whole representable box | `glm_geometry.py` §6, C13, C30 |
| 21 | Griess product built from the snap | v13 | **corrected**: substituting `snap(v) = v ⊕ L(σ(v))` collapses it to `v·w = snap(v) ⊕ snap(w)`, which is associative; all triple defects vanish | paper §8.3, C20 |
| 22 | Griess layer that *is* commutative and non-associative | — | **new**: the 300-dimensional Jordan algebra `R ⊕ S²₀(R^24)`, verified in exact rational arithmetic | `glm_moonshine.py` §5, C34 |
| 23 | extraspecial `2^(1+24)` acting on 24 coordinates | v14 | **corrected** (already in v15): impossible; the 24D action is checked here and fails | `glm_monster.py` §2, C19 |
| 24 | faithful 4096D Schrödinger representation | v15, v16 | shipped, exact signed permutations, every relation checked on the whole space | `glm_monster.py` §2, C19 |
| 25 | POPCOUNT / NumPy optimisation | v16 | not needed: the exact integer path runs the full audit in seconds, and a second implementation is a second thing to be wrong | — |
| 26 | 4096D equation checker | v16 | **dropped as a decision procedure**: it is strictly weaker than integer equality in `Z^7` and much slower; the 4096D layer is kept for group theory only | paper §10.4 |
| 27 | 98,280 lines of minimal vectors | v18 | shipped and *counted*, not asserted: all 196,560 vectors enumerated, closure under negation verified, split `552 / 48,576 / 49,152` | `glm_moonshine.py` §1, C32 |
| 28 | `98,304 = 24 × 4096` tensor index | v16, v18 | shipped as a verified bijection onto the shape-C minimal vectors | `glm_moonshine.py` §2, C32 |
| 29 | `196,884 = 1 + 299 + 98,280 + 98,304` | v13–v19 (implicit) | shipped: every summand computed from its own definition | `glm_moonshine.py` §3, C33 |
| 30 | moonshine numerology | v13 | shipped in the one form that can be computed here: `196,884 = 324 + 196,560` from an exact `q`-expansion of `∏(1-q^n)^{-24}` and the census | `glm_moonshine.py` §4, C33 |
| 31 | McKay–Thompson tables for 1A, 2A, 2B, 3A … | v13 | **dropped**: unsourced, ungenerated, and inconsistent between versions; only the computed 1A head coefficient ships | catalog + `glm_moonshine.py` header |
| 32 | concept → Monster conjugacy class | v13 | **dropped**: a renaming of syndrome weight with no group-theoretic content | catalog note only |
| 33 | vertex operators `Y(v,z)`, OPE-derived `L_0` | v18, v19 | **dropped**: the modes were hand-chosen and the "Leech inner product" is `24 − 2·d_Hamming`, verified as such | `glm_moonshine.py` `hamming_inner_product_report`, C35 |
| 34 | `2^(1+24) ⋊ Co_1` | v19 | shipped under its true name `2^(1+24) : S_12`: the implemented outer factor permutes the twelve pairs, which is `S_12`, not `Co_1` | `glm_monster.py` §4, C36 |
| 35 | hex colour `#RRGGBB` ↔ `F_2^24`, chromatic ground states | v18, v19 | shipped and *completed*: no search is needed, the ground states are exactly the 4096 codewords, one colour in 4096 | `glm_geometry.py` §7, C31 |
| 36 | 3D scene export | companion v1 | shipped | `glm_reasoner.py`, `scene_3d.json` |

### Summary of the corrections

Five statements from the archive do not survive contact with an exact
implementation, and each is now stated as a correction rather than quietly
removed:

1. the four-tier encoder is many-to-one (#4);
2. "100% vs 89% on 6,793 pairs" has no reproducible population (#6);
3. the snap-based Griess product is associative (#21);
4. the archive's `L_0` is `σ/2`, and its "Leech inner product" is Hamming
   distance in disguise (#19, #33);
5. the outer factor of the v19 semidirect product is `S_12`, not `Co_1` (#34).

Three archive claims turned out to be exactly right and are now stronger than
they were: the mod-2 ceiling (now a machine-checked theorem), the necessity of
the 4096-dimensional action (now verified on the whole space), and the line
count `98,280` (now enumerated rather than asserted).

### One gap closed

Every version from v10 on speaks of `M_24` and none of them constructs it; what
they construct is a predicate that tests a single permutation.  `glm_m24.py`
closes that gap.  A permutation preserves the Golay code exactly when it
preserves the linear dependencies among the columns of a generator matrix — the
supports of codewords, the code being self-dual — so the search can decide a
partial map incrementally and, most of the time, force the next image outright.
Four automorphisms found this way generate a group; its stabiliser chain is
5-transitive with order 244,823,040; and the exhaustive list of automorphisms
fixing five coordinates has exactly 48 entries, so orbit–stabiliser closes the
argument: the group is `Aut(C) = M_24`.  Nothing about `M_24` is assumed
anywhere — the order that matches the literature is an output.  Orbits of the
classical objects then give the orders of the three maximal subgroups for free:
759 octads (stabiliser `2^4 : A_8`, 322,560), 2576 dodecads (stabiliser `M_12`,
95,040) and 1771 sextets (stabiliser `2^6 : 3.S_6`, 138,240).  The subgroup
tower the archive gestured at is therefore accounted for as far as orders go,
by measurement rather than assertion.

### The architecture change: meaning first, bits derived

Every archived version carries two objects side by side — a 24-bit carrier
word and an integer exponent vector — and treats the integer vector as the
add-on that repairs the carrier's mistakes.  Read in order, the versions are
the story of that add-on quietly taking over: it starts as a "companion",
becomes the thing every verdict is actually taken from, and by the last
version the bit pattern decides nothing at all.

This directory finishes the move rather than describing it.  The integer
vector is the state, and the bit pattern is a derived view of it:

* `derive_substrate(dim)` is a pure function from a `Dimension` to a frozen
  `_Substrate` record (word, shadow, snap, lawfulness, cost).  It is the only
  place a carrier is ever produced.
* `Concept` is a frozen dataclass whose fields are `name`, `dim`, `symbol`
  and `unit` — nothing else.  `carrier`, `shadow`, `snap`, `snapped_carrier`,
  `lawful`, `tax` and `nrci` are read-only properties backed by one cached
  call to `derive_substrate`.  Assigning to any of them raises.
* Changing a concept's meaning is `with_meaning(new_dim)`, which returns a new
  concept; the bits follow automatically, because there is nowhere else for
  them to come from.  `carrier_is_derived()` re-derives and checks.
* Nothing composes on the carrier.  XOR of two words is almost never the word
  of the product (claim C43), and paper §5.3 says why it never could be: an
  additive map into a group of exponent 2 cannot be injective on `Z^7`
  (`GLM.no_injective_additive_into_char_two`, machine-checked).

The mod-2 material is kept, because a rejected design is worth measuring, but
it is quarantined: `mod2_shadow`, `mod2_would_accept`, `mod2_collapse_report`,
`mod2_perturbation_sweep` and `mod2_box_census` live in §6 of
`glm_metrology.py`, headed *APPENDIX — THE REJECTED F_2 CARRIER*, and reach the
reasoner only through `mod2_ceiling_batch`.  No audit record, no verdict and no
telemetry field carries a mod-2 opinion, and `Dimension` has no `mod2()`
method.  The same discipline is applied to GLM-2 in `../glm2`.
