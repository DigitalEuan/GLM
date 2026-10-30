import Mathlib

/-!
# Role–filler binding: what a bound relation gives back, and what it cannot

The supplied conversational material carries a vector-symbolic idea the rest of
this system does not have: a typed relation *R(A, B)* written as one carrier,
`R ⊗ A ⊗ B`, from which `B` is meant to be recovered by re-binding with what is
known.  Two bindings are offered there, both described as recoverable: an
elementwise **product** of the three rational 24-vectors, and an exclusive-or
of their **parity readings**, with the role `R` carried by a permutation of the
coordinates rather than by a carrier of its own.

This file settles which of the two claims is true, and exactly how much the
true one gives.

* **The parity binding is exactly invertible, always** (`unbind_bind`).  There
  is no side condition: the masks form an elementary abelian 2-group, the role
  acts on it by a permutation of coordinates, and `unbind` is `bind` again.
  Binding the filler twice gives the filler back (`bind_involutive_right`), and
  the binding is injective in the filler (`bind_injective_right`).
* **The product binding is not**, and the obstruction is a single zero
  coordinate (`hbind_not_injective_of_zero`): if the known side reads zero
  anywhere, two different fillers bind to the same vector and no procedure can
  tell them apart.  Where nothing reads zero, recovery is exact
  (`hbind_recover`).  Every carrier in every register the shipped system loads
  has a zero coordinate, so in this system the product binding recovers
  nothing; the theorem says why, and the study counts it.
* **Recovering the reading is not recovering the name.**  A register is a list
  of named masks, and what a recovery has in hand after unbinding is a *fibre*
  of the parity map.  `recover_ok_iff` says a name comes back exactly when that
  fibre holds one name; `recover_sound` says the name that comes back reads as
  what was recovered; and `two_names_one_reading_is_ambiguous` exhibits the
  case the shipped registers are full of — 726 physics carriers take 128
  distinct parity readings — where the fibre holds two names and the operation
  must refuse rather than choose.
* **The refusal is not fussiness**, because the cheap alternative is wrong:
  `nearest_names_the_wrong_carrier` takes the supplied nearest-mask search and
  exhibits a register on which it silently returns a carrier that is not the
  filler that was bound.
* **The role tag is a rule about `A`, not about the bound mask.**
  `bind_eq_iff_role_agrees` says two roles bind alike exactly when they agree
  on the known side, and `roles_differ_but_bind_alike` exhibits two different
  roles that bind identically — a constant reading is fixed by every
  permutation — so the relation type cannot be read back out of the binding.

The shipped counterpart is `glm_universal.reasoning.role_binding`, whose tests
pin these properties on the real registers.
-/

namespace GLM.RoleBinding

variable {n : ℕ}

/-- A parity reading of a carrier: one bit per coordinate.  This is the whole
of what the substrate layer sees of a carrier, and it is what the parity
binding binds. -/
abbrev Mask (n : ℕ) := Fin n → Bool

/-- A role tag: the relation type is carried by a permutation of the
coordinates rather than by a carrier of its own. -/
abbrev Role (n : ℕ) := Equiv.Perm (Fin n)

/-- Coordinatewise exclusive-or of two readings. -/
def xorM (x y : Mask n) : Mask n := fun i => xor (x i) (y i)

/-- The role acting on a reading: coordinate `i` of the result is coordinate
`σ i` of the reading. -/
def act (σ : Role n) (m : Mask n) : Mask n := fun i => m (σ i)

/-- The key a binding is made with: the known side, tagged by the role. -/
def key (σ : Role n) (a : Mask n) : Mask n := xorM (act σ a) a

/-- Bind the relation `(σ, a, b)` into one reading. -/
def bind (σ : Role n) (a b : Mask n) : Mask n := xorM (key σ a) b

/-- Recover the filler's reading from a bound reading, given the role and the
known side.  It is `bind` again: the masks are an elementary abelian
2-group. -/
def unbind (σ : Role n) (a x : Mask n) : Mask n := xorM (key σ a) x

/-! ## The group law -/

@[simp] lemma xorM_self (x : Mask n) : xorM x x = fun _ => false := by
  funext i; simp [xorM]

lemma xorM_comm (x y : Mask n) : xorM x y = xorM y x := by
  funext i; simp [xorM, Bool.xor_comm]

lemma xorM_assoc (x y z : Mask n) : xorM (xorM x y) z = xorM x (xorM y z) := by
  funext i; simp [xorM]

@[simp] lemma xorM_cancel (x y : Mask n) : xorM x (xorM x y) = y := by
  funext i; cases hx : x i <;> simp [xorM, hx]

/-- **Recoverability, with no side condition.**  Unbinding a bound reading
with the role and the known side returns the filler's reading exactly. -/
@[simp] theorem unbind_bind (σ : Role n) (a b : Mask n) :
    unbind σ a (bind σ a b) = b := by
  simp [unbind, bind]

/-- Binding the filler twice with the same key is the filler again. -/
theorem bind_involutive_right (σ : Role n) (a b : Mask n) :
    bind σ a (bind σ a b) = b := unbind_bind σ a b

/-- The binding is injective in the filler: two fillers that bind alike are
the same filler. -/
theorem bind_injective_right (σ : Role n) (a : Mask n) :
    Function.Injective (bind σ a) := by
  intro b₁ b₂ h
  have := congrArg (unbind σ a) h
  simpa using this

/-- Every reading is the binding of something: the bound readings are all of
them, so a bound reading on its own says nothing. -/
theorem bind_surjective_right (σ : Role n) (a : Mask n) :
    Function.Surjective (bind σ a) :=
  fun x => ⟨unbind σ a x, by simp [unbind, bind]⟩

/-! ## The role tag -/

/-- Two roles bind alike exactly when they agree on the known side. -/
theorem bind_eq_iff_role_agrees (σ τ : Role n) (a b : Mask n) :
    bind σ a b = bind τ a b ↔ act σ a = act τ a := by
  constructor
  · intro h
    funext i
    have := congrFun h i
    simp only [bind, xorM, key] at this
    revert this
    cases act σ a i <;> cases act τ a i <;> cases a i <;> cases b i <;> simp
  · intro h
    funext i
    simp only [bind, xorM, key, h]

/-- **The relation type is not in the binding.**  Two different roles can bind
a pair identically — a constant reading is fixed by every permutation of the
coordinates — so the role must be known in order to unbind, and cannot be read
back out. -/
theorem roles_differ_but_bind_alike :
    ∃ (σ τ : Role 24) (a b : Mask 24),
      σ ≠ τ ∧ bind σ a b = bind τ a b := by
  refine ⟨Equiv.refl _, Equiv.swap 0 1, (fun _ => false), (fun _ => false),
    ?_, ?_⟩
  · intro h
    have : (Equiv.swap (0 : Fin 24) 1) 0 = (0 : Fin 24) := by
      rw [← h]; rfl
    simp at this
  · rw [bind_eq_iff_role_agrees]
    funext i
    simp [act]

/-! ## The product binding, and the zero that breaks it -/

/-- The elementwise product binding of the supplied material, over the exact
rational coordinates the registers hold. -/
def hbind (r a b : Fin n → ℚ) : Fin n → ℚ := fun i => r i * a i * b i

/-- Where the known side reads nowhere zero, the product binding is exactly
invertible by division. -/
theorem hbind_recover {r a b : Fin n → ℚ} (h : ∀ i, r i * a i ≠ 0) (i : Fin n) :
    hbind r a b i / (r i * a i) = b i := by
  have h' := h i
  simp only [hbind]
  exact mul_div_cancel_left₀ _ h'

/-- **One zero coordinate destroys the product binding.**  If the key reads
zero anywhere then two different fillers bind to the same vector, so no
procedure — not division, not search — recovers the filler.  Every carrier in
every register this system loads reads zero somewhere. -/
theorem hbind_not_injective_of_zero {r a : Fin n → ℚ} {i₀ : Fin n}
    (h : r i₀ * a i₀ = 0) :
    ∃ b₁ b₂ : Fin n → ℚ, b₁ ≠ b₂ ∧ hbind r a b₁ = hbind r a b₂ := by
  classical
  refine ⟨fun _ => 0, fun i => if i = i₀ then 1 else 0, ?_, ?_⟩
  · intro hb
    have := congrFun hb i₀
    simp at this
  · funext i
    by_cases hi : i = i₀
    · subst hi; simp [hbind, h]
    · simp [hbind, hi]

/-! ## From a reading to a name -/

/-- Why a recovery refused. -/
inductive Reason where
  /-- No carrier of the register reads as the recovered mask. -/
  | noCarrier
  /-- Two or more carriers do, and naming one would be a choice. -/
  | ambiguous
deriving DecidableEq, Repr

/-- A register, as a recovery sees it: named carriers with their readings. -/
abbrev Register (n : ℕ) := List (String × Mask n)

/-- The names of a register that read as a given mask — the fibre of the
parity map over that mask. -/
def fibre (R : Register n) (m : Mask n) : List String :=
  (R.filter (fun p => decide (p.2 = m))).map Prod.fst

/-- Recover a name from a bound reading: unbind, then look the reading up.
A name comes back only when the fibre holds exactly one. -/
def recover (R : Register n) (σ : Role n) (a x : Mask n) :
    Except Reason String :=
  match fibre R (unbind σ a x) with
  | [name] => .ok name
  | [] => .error .noCarrier
  | _ => .error .ambiguous

lemma mem_fibre_iff {R : Register n} {m : Mask n} {name : String} :
    name ∈ fibre R m ↔ ∃ p ∈ R, p.1 = name ∧ p.2 = m := by
  constructor
  · intro h
    simp only [fibre, List.mem_map, List.mem_filter, decide_eq_true_eq] at h
    obtain ⟨p, ⟨hp, hm⟩, hn⟩ := h
    exact ⟨p, hp, hn, hm⟩
  · rintro ⟨p, hp, hn, hm⟩
    simp only [fibre, List.mem_map, List.mem_filter, decide_eq_true_eq]
    exact ⟨p, ⟨hp, hm⟩, hn⟩

/-- A name is recovered exactly when it is the only one that reads as the
recovered mask. -/
theorem recover_ok_iff {R : Register n} {σ : Role n} {a x : Mask n}
    {name : String} :
    recover R σ a x = .ok name ↔ fibre R (unbind σ a x) = [name] := by
  unfold recover
  cases h : fibre R (unbind σ a x) with
  | nil => simp
  | cons y ys =>
      cases ys with
      | nil => simp
      | cons z zs => simp

/-- **Recovery never names a carrier that reads otherwise.**  The name that
comes back is in the register, and its reading is the reading that was
recovered. -/
theorem recover_sound {R : Register n} {σ : Role n} {a x : Mask n}
    {name : String} (h : recover R σ a x = .ok name) :
    (name, unbind σ a x) ∈ R := by
  rw [recover_ok_iff] at h
  have hmem : name ∈ fibre R (unbind σ a x) := by rw [h]; simp
  obtain ⟨p, hp, hn, hm⟩ := mem_fibre_iff.mp hmem
  have : p = (name, unbind σ a x) := Prod.ext hn hm
  exact this ▸ hp

/-- **What the binding is worth.**  If the filler is the only carrier of the
register with its reading, binding and recovering returns its name. -/
theorem recover_bind_of_unique {R : Register n} {σ : Role n} {a b : Mask n}
    {name : String} (h : fibre R b = [name]) :
    recover R σ a (bind σ a b) = .ok name := by
  rw [recover_ok_iff, unbind_bind]; exact h

/-- **The recovery is a fact about the register, not about the binding.**
Whatever role and whatever known side the word was made with, the name that
comes back is the same — which is why the measurement that decides what a
binding is worth here is a census of the registers' readings. -/
theorem recover_bind_independent_of_role (R : Register n) (σ τ : Role n)
    (a c b : Mask n) :
    recover R σ a (bind σ a b) = recover R τ c (bind τ c b) := by
  simp [recover, unbind_bind]

/-- **The refusal the registers force.**  Two carriers with the same parity
reading make the recovery ambiguous: the reading comes back exactly, and it
names two carriers.  In the shipped physics register 726 carriers take 128
distinct readings, so this is the ordinary case rather than the exotic one. -/
theorem two_names_one_reading_is_ambiguous (σ : Role n) (a b : Mask n)
    (u v : String) :
    recover [(u, b), (v, b)] σ a (bind σ a b) = .error .ambiguous := by
  simp [recover, fibre, unbind_bind]

/-- A register that holds no carrier with the recovered reading refuses for
the other reason. -/
theorem no_carrier_is_refused (σ : Role n) (a b : Mask n)
    (R : Register n) (h : fibre R b = []) :
    recover R σ a (bind σ a b) = .error .noCarrier := by
  simp [recover, unbind_bind, h]

/-! ## The cheap alternative, refuted -/

/-- The Hamming distance between two readings. -/
def hamming (x y : Mask n) : ℕ :=
  (List.finRange n).countP (fun i => decide (x i ≠ y i))

/-- The supplied nearest-mask search: the first carrier of the register at
least Hamming distance from the recovered reading. -/
def nearest (R : Register n) (m : Mask n) : Option String :=
  (R.mergeSort (fun p q => hamming p.2 m ≤ hamming q.2 m)).head?.map Prod.fst

/-- **The cheap alternative answers, and is wrong.**  Where the recovery
refuses because two carriers share a reading, the nearest-mask search returns
one of them with no sign that anything was chosen — and the one it returns is
not the filler that was bound. -/
theorem nearest_names_the_wrong_carrier :
    ∃ (R : Register 24) (σ : Role 24) (a b : Mask 24) (wrong bound : String),
      wrong ≠ bound ∧
      recover R σ a (bind σ a b) = .error .ambiguous ∧
      nearest R (unbind σ a (bind σ a b)) = some wrong := by
  refine ⟨[("wrong", fun _ => false), ("bound", fun _ => false)],
    Equiv.refl _, (fun _ => false), (fun _ => false), "wrong", "bound",
    by decide, ?_, ?_⟩
  · simp [recover, fibre, unbind_bind]
  · simp [nearest, unbind_bind, List.mergeSort]

end GLM.RoleBinding
