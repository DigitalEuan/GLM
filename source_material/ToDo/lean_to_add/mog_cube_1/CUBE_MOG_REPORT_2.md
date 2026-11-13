# Cube / MOG semantics, stage 2: past the precision wall, and into sentences

This continues `CUBE_MOG_REPORT.md`.  It reports on the four scripts you sent —
`test_5_three_ideas.py`, `test_6_precision_wall.py`, `test_7_chat.py`,
`test_8_three_cube.py` — what of them worked, what of them was wrong, and what
had to be built instead.

Everything claimed below is proved in Lean and compiles with no `sorry` and no
extra axioms (`lake build` is clean over the whole project).  Where a number
appears — 356, 1758, 0, 39, 32/16/0, 8 — it is the statement of a theorem, not
the output of a script.  A dependency-free Python mirror, `glm_chat2.py`,
recomputes every one of those numbers so you can poke at the system directly;
it prints the Lean value next to its own.

---

## 1. The precision wall is gone  (`RequestProject/IntegerCube.lean`)

Your Idea 1 — keep the integer exponents, compose by addition, not XOR — is
right, and it is stronger than the script had it: the integers do not need to
sit *beside* the cube, they fit *inside* it.

**The encoding.** Each face keeps all four of its cells and holds one exponent
as a four-cell two's-complement number, so a face carries an integer in
`[-8, 7]` rather than a parity bit.

**The composition.** `addCol` is a ripple-carry adder wired across the four
cells of a face; `addG` runs it on all six faces. Multiplying two quantities is
adding their cubes (`encG_add`), and it is reversible (`subG_addG`) — you can
divide the second factor out again.

**Why this is not XOR, exactly.** XOR *is* the same circuit with the carry wire
cut: they agree precisely on the inputs that generate no carry
(`xor_is_add_without_carry`). The carry is the information XOR throws away —
`gxorCol c c` is always zero, `addCol c c` doubles.

**The measurement.** Re-running the stage-1 experiment (12 measurable words plus
all 144 two-word products = 156 phrases):

| | true sentences | accepted | false positives | precision |
|---|---|---|---|---|
| parity cube (stage 1) | 356 | 1758 | 1402 | 0.20 |
| integer cube (now) | 356 | 356 | **0** | **1.00** |

`integer_accepts_eq_equations` proves the accepted set is *the same list* as the
true set, not merely the same size. `E = mc⁴`, which the parity cube accepted,
is now rejected; the true equations are still accepted.

**What it costs, honestly.** An integer record is essentially never a lawful
codeword: **none** of the 156 phrases lands in the code
(`phrase_codeword_count = 0`), so the "free to hold" property of the parity
encoding is gone. What survives is the repair bound: any record returns to the
code for at most `4·Q` (`encG_tax_le_four`).

**Where it still fails.** The window wraps: exponents differing by 16 collide
(`wrap_blindness_witness`), and no encoding into 24 cells can be faithful on all
of ℤ⁶ (`no_faithful_encoding`). The blind spot moved from "differs by 2" —
inside the vocabulary — to "differs by 16", far outside it.

---

## 2. The three-cube rules, checked  (`RequestProject/ThreeCube.lean`)

Your `test_8` proposal was three 8-vertex cubes with Rules A, B, C. Checked
exactly:

* **Rule A is `RM(1,3)`, not `RM(2,3)`.** "All six face parities even" picks out
  exactly the 16 affine functions of `(x,y,z)` (`ruleA_iff_affine`,
  `ruleA_card = 16`). `RM(2,3)` — the even-weight code named in the script — has
  128 words (`rm2_card`). The label was off by one order.
* **Rule B rejects nothing.** Under Rule A every face parity is already `0`, so
  the cross-cube parity condition follows automatically (`ruleB_of_ruleA`).
* **The Rule-A three-cube code is `[24, 12, 4]`.** Right size — `2^12` words,
  the same as Golay (`ruleAB_card`) — but a weight-4 word passes Rules A and B
  (`ruleA_weight_four_witness`), so it corrects **one** cell error, not three.
* **Rule C does bite, and breaks linearity.** It rejects that weight-4 word
  (`ruleC_is_a_real_filter`), but two words of weights 8 and 12 that pass it have
  a sum of weight 4 that does not (`ruleAC_not_linear`) — the filtered set is not
  a code you can compose inside.
* **No relabelling rescues it.** For *any* bijection of the 24 cells, the
  transported Rule-A code still carries a weight-4 word, while every nonzero
  Golay codeword has weight ≥ 8 (`ruleA_code_is_not_golay`).

**What does work — keep the three cubes, change the glue.** With `a, b` in the
Rule-A cube code and `x` a relabelled copy of it (vertex permutation
`σ = [0,1,2,4,3,6,7,5]`), set

```
cube₀ = a + x      cube₁ = b + x      cube₂ = a + b + x
```

This is linear (`turyn_add`), has `2^12` codewords (`turynCode_card`), minimum
weight **8** (`turyn_min_weight`), and weight enumerator `1, 759, 2576, 759, 1`
(`turyn_weight_enumerator`) — cell for cell the Golay enumerator already proved
for the MOG in stage 1. (That the two are literally the same code up to
relabelling is the classical uniqueness theorem for the binary Golay code; that
step is *not* formalised here. What is formalised is that the parameters and the
weight enumerator agree.)

So the "three columns" picture is sound; the glue has to be Turyn's, not a
parity rule between corresponding faces.

---

## 3. Sentences that make logical sense  (`RequestProject/Semantics.lean`)

This is the part your brief actually asks for: words that connect and grow
sentences, not just dimensional bookkeeping.

**The world.** Three tangible things — water, stone, lamp — each with a
temperature on `-10, 0, 20, 100 °C` and a mass on `1, 10 kg`. That is 512
worlds, and the enumeration is proved complete (`mem_allWorlds`), so every
"in every world" below really means all of them.

**The words.** Measured properties (`frozen`, `boiling`, `warm`, `heavy`) and
relations (`hotter`, `heavier`), each a threshold or comparison on readings —
nothing stipulated; negation; the deterministic actions `heat`, `cool`, `load`;
and the connectives `and`, `if … then …`, `because`, `after we …`.

**The logic is law-like, not local.** This is the design decision that makes the
sentences mean something:

* `if A then B` is true only when A implies B in **all 512 worlds**;
* `A because B` is true only when B holds here, A holds here, and B implies A in
  **all 512 worlds** (`because_is_explanatory`) — a reason, not a coincidence;
* `A because B and C` additionally requires that neither B nor C would have
  sufficed alone (`because2_is_minimal_explanation`) — the reason is minimal.

**What is guaranteed about what it says.** `speak w` is the set of sentences the
system is willing to utter in world `w`:

* everything it says is true in `w` (`speak_sound`);
* it never says a thing and its denial (`speak_consistent`), and the whole set is
  jointly satisfiable (`speak_satisfiable`);
* every property it reports is contingent — false in some world — so each report
  carries information (`speak_lits_contingent`);
* every law it states has a satisfiable antecedent, so none is true for want of a
  case (`speak_laws_nonvacuous`), and no law is stated twice in contrapositive
  disguise (`speakLaws_no_contrapositive_duplicate`);
* the sentences chain: modus ponens is sound on them (`modus_ponens_sound`) and
  laws compose (`law_trans`);
* a prediction is checked against the world the action actually produces, and it
  is a prediction of a *change* (`after_sound`).

For the demo world the counts are theorems (`demo_counts`): 24 measured reports,
39 laws, 30 explanations, 14 useful predictions — 107 sentences.

---

## 4. The chat  (`RequestProject/Chat.lean`)

Five question forms — "is X …?", "why is X …?", "if we heat X, is it …?",
"which is hotter, X or Y?", "tell me about X" — and one total, deterministic
`answer` function. Same question, same world, same answer; no search, no
sampling.

* **It cannot lie**: for *every* question and *every* one of the 512 worlds, the
  sentence it replies with is true in that world (`answer_true`).
* A yes/no question always gets a yes or a no, with the polarity the measurement
  supports, so a false premise in the question is contradicted rather than
  accepted (`answer_isIt_decisive`).
* When it gives a reason, the reason is a ground in every world
  (`answer_why_explains`).
* The reply is about what was asked (`answer_mentions_subject`).
* Distinct sentences get distinct English (`render_injective_on_demo`) — the
  surface form never blurs two meanings.

**How deep the explanations go, counted** (`why_reason_counts`): of the 48
"why" questions askable in the demo world, **32** are answered by a single
literal, **16** need a minimal pair, **0** are left unexplained. Where it has no
ground at all it states the bare fact; that branch exists in `answer` and simply
is not reached by this vocabulary.

A transcript, printed by the build and reproduced by `glm_chat2.py`:

```
> tell me about the water
  the water is frozen, and the water is not boiling, and the water is not warm,
  and the water is not heavy
> is the water warm?
  the water is not warm
> why is the water not warm?
  the water is not warm because the water is frozen
> why is the water frozen?
  the water is frozen because the water is not boiling and the water is not warm
> why is the lamp boiling?
  the lamp is boiling because the stone is not frozen and the lamp is hotter than the stone
> if we heat the lamp, is the lamp boiling?
  after we heat the lamp, the lamp is boiling
> why is the stone heavier than the water?
  the stone is heavier than the water because the water is not heavy and the stone is heavy
> why is the water heavy?
  the water is not heavy
```

The last line is the system refusing a false premise; the third and fourth are
it giving grounds that hold in every world, not just this one.

---

## 5. The sentence on the cube  (`RequestProject/SentenceCode.lean`)

A clause is stored as a three-cube Turyn codeword: subject (which thing, and the
polarity), predicate (which of the six measured properties), object (the second
thing, or none) — four bits each, one affine cube each, glued by Turyn's rule.

* This is your Idea 3 made exact: **the third cube is computed, not stored**
  (`third_cube_is_computed`), and the glue reads straight back off the record as
  the cellwise sum of the three cubes (`glue_recoverable`) — a determined value,
  no search.
* **No two meanings collide**: the 60 clauses of the vocabulary get 60 distinct
  records (`clauseCode_injective`) — this was the failure mode of the earlier
  word-encoding runs (23/30 unique, `force = action = spin` colliding).
* **Any two clauses differ in at least 8 of the 24 cells**
  (`clause_min_distance`), so a clause damaged in up to **3 cells** still reads
  back uniquely (`clause_unique_decoding`).

---

## 6. Where the two layers meet  (`RequestProject/Grounding.lean`)

Each atom is unpacked into the comparisons it actually performs — "the water is
warm" is `0 °C < temp(water)` together with `temp(water) < 100 °C` — and this
unpacking is proved to match the truth conditions (`compsOf_correct`).

* **The cube is a type checker for the language.** In every comparison the
  language performs, both sides carry the same dimension
  (`atoms_are_well_typed`), so the cube accepts it at zero tax
  (`well_typed_tax_zero`); a category error — a temperature against a mass — is
  rejected and costs at least `8·Q` (`category_error_is_rejected`). The cube
  rules out "the water is hotter than the stone's mass" knowing nothing about
  water or stones.
* **But dimensions cannot decide truth**: an atom's dimensional record is the
  same in every world while its truth is not (`dimension_cannot_decide_truth`),
  and truth values do not determine dimensions either
  (`truth_cannot_supply_types`). The layers are complementary: the cube types
  and protects the sentence, the measurement makes it true or false.

---

## 7. What was not achieved

Stated plainly, in the same spirit as §8 of the first report.

1. **The 24 cells cannot be a dimension record and a clause record at once.**
   `IntegerCube.encG` and `SentenceCode.clauseCode` are two different uses of the
   same surface. A working system needs one cube per role and a discipline for
   addressing them; nothing here provides that.
2. **The vocabulary is small and closed.** Three things, six predicates, three
   actions, 512 worlds. The proofs quantify over all of it, which is exactly why
   it has to be small. Nothing here says how the same guarantees would survive a
   vocabulary of thousands — the "all worlds" checks are the bottleneck, and a
   larger world model needs a proof method that is not enumeration.
3. **No abstract nouns yet.** Every word still bottoms out in a threshold on a
   reading. "Mother" is no closer than it was; what has changed is that the
   *connectives* (`if`, `because`, `and`, `after`) are now honest, so a future
   abstract word only has to supply truth conditions, not a whole logic.
4. **The integer window is finite.** Exponents differing by 16 still collide, and
   provably some collision is unavoidable on 24 cells.
5. **Turyn ≡ Golay is cited, not proved.** The three-cube code is proved to be a
   linear `[24,12,8]` code with the Golay weight enumerator; that this makes it
   *the* Golay code relies on the classical uniqueness theorem, which is not
   formalised here.
6. **"Because" is entailment, not causation.** `A because B` means B forces A in
   every world. That is a good notion of ground, and it is what makes the
   explanations sound — but it does not distinguish a cause from a definitional
   consequence. "The water is not warm because the water is frozen" and "the
   water is frozen because it is not boiling and not warm" are both accepted, and
   only the first reads as a cause.
7. **Predictions are one step deep.** `after we heat the water` looks one action
   ahead. Chains of actions, and planning ("what should we do to make the water
   warm?"), are not built.

---

## 8. What I would do next

* **Give each role its own cube.** Three cubes per clause (subject / predicate /
  object) is already the natural reading of your three-column picture; the Turyn
  glue then protects the whole clause at distance 8. Extending to a *chain* of
  clauses is where `because` and `if` would become codeword-level operations
  rather than sentence-level ones.
* **Add a direction of time to `because`.** Keeping entailment as the soundness
  condition but preferring a reason that mentions an *earlier* action would
  separate causes from definitional consequences without weakening the proofs.
* **Multi-step planning.** `after` composes: proving "there is a sequence of at
  most `n` actions after which A" is decidable in this world model and would give
  the system genuinely useful sentences ("heat the water twice and it will be
  warm").
* **Grow the vocabulary by one hard word at a time**, each with a threshold or a
  comparison behind it, and re-run the counts — the honest measure of progress
  here is the explanation ratio (currently 32 single / 16 pair / 0 unexplained),
  not the size of the lexicon.
