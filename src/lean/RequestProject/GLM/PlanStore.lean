import Mathlib

/-!
# A resolved follow-up, kept against a digest of what it depended on

Resolving *describe it* after a fourteen-row tie costs fourteen licensing
trials and then refuses.  The supplied conversational material keeps resolved
plans in a content-addressed store and replays them; it keeps only the
**successful** ones, so the expensive case — the refusal — is the one case it
pays for again every time.

This file states what a store of plans may and may not do.  A `Plan` is what
was asked and where: the turns of the conversation before it, and the
follow-up itself.  An `Outcome` is what resolving it decided — an antecedent,
or a refusal with its reason, the two treated alike.  A store is a list of
`(key, outcome)` pairs, and the whole of the argument is in two properties of
the key.

* **What is recorded is what comes back** (`lookup_record`), refusals included
  (`refusal_survives_replay`).  A store that forgets refusals is not a cheaper
  conversation, it is a different one.
* **A store may save work and may never change an answer.**  `Sound` says
  every entry of a store is something the resolver really decided;
  `replay_agrees_with_run` says that with a key that separates plans, a hit is
  exactly what resolving again would have said — so the store is a memo and
  not a second opinion.  `replay_preserves_refusal` is the case the round was
  taken for.
* **The key has to cover the whole conversation.**
  `coarse_key_answers_the_wrong_question` exhibits the failure the shipped
  measurement then counts: keyed by the follow-up text alone, a store that is
  sound — every entry really was decided by the resolver — still answers one
  conversation's *describe it* with another conversation's antecedent.  Eight
  of the fifteen declared follow-ups come back wrong that way.
* **And the exact key does separate them** (`exactKey_injective`): the key is
  the content, which is what a digest checked against the stored content
  amounts to, so a collision can cost a miss and cannot cost an answer.

The shipped counterpart is `glm_universal.runtime.plan_store`, wired into
`glm_universal.runtime.conversation` as an optional store.
-/

namespace GLM.PlanStore

/-- What was asked, and in what conversation: the turns before it, in order,
and the follow-up itself.  This is everything resolving a follow-up depends
on. -/
structure Plan where
  /-- The turns already asked, oldest first. -/
  before : List String
  /-- The follow-up. -/
  text : String
deriving DecidableEq, Repr

/-- What resolving a follow-up decided. -/
inductive Outcome where
  /-- It bound, to this antecedent. -/
  | bound (name : String)
  /-- It refused, for this reason. -/
  | refused (reason : String)
deriving DecidableEq, Repr

/-- Whether an outcome is a refusal. -/
def Outcome.isRefusal : Outcome → Bool
  | .refused _ => true
  | .bound _ => false

variable {K : Type} [DecidableEq K]

/-- A store: what has been recorded, newest first. -/
abbrev Store (K : Type) := List (K × Outcome)

/-- What the store holds under a key. -/
def lookup (s : Store K) (k : K) : Option Outcome :=
  (s.find? (fun p => decide (p.1 = k))).map Prod.snd

/-- Record an outcome under a key. -/
def record (s : Store K) (k : K) (o : Outcome) : Store K := (k, o) :: s

/-! ## What is recorded is what comes back -/

@[simp] theorem lookup_record (s : Store K) (k : K) (o : Outcome) :
    lookup (record s k o) k = some o := by
  simp [lookup, record]

/-- **A refusal is kept as an answer is.**  Recording a refusal and replaying
it gives back the same refusal, with its reason. -/
theorem refusal_survives_replay (s : Store K) (k : K) (reason : String) :
    lookup (record s k (.refused reason)) k = some (.refused reason) :=
  lookup_record s k _

/-- Recording under one key leaves every other key alone. -/
theorem lookup_record_of_ne (s : Store K) {j k : K} (h : j ≠ k)
    (o : Outcome) : lookup (record s k o) j = lookup s j := by
  simp [lookup, record, Ne.symm h]

/-! ## A store may save work and may never change an answer -/

/-- A store is **sound** for a resolver and a key when every entry it holds is
something the resolver really decided, about a plan with that key. -/
def Sound (key : Plan → K) (run : Plan → Outcome) (s : Store K) : Prop :=
  ∀ k o, lookup s k = some o → ∃ p, key p = k ∧ run p = o

/-- The empty store is sound for anything. -/
theorem sound_nil (key : Plan → K) (run : Plan → Outcome) :
    Sound key run ([] : Store K) := by
  intro k o h
  simp [lookup] at h

/-- Recording what the resolver decided keeps a store sound. -/
theorem sound_record {key : Plan → K} {run : Plan → Outcome} {s : Store K}
    (hs : Sound key run s) (p : Plan) :
    Sound key run (record s (key p) (run p)) := by
  intro k o h
  by_cases hk : k = key p
  · subst hk
    rw [lookup_record] at h
    exact ⟨p, rfl, by simpa using h⟩
  · rw [lookup_record_of_ne s hk] at h
    exact hs k o h

/-- **The store is a memo, not a second opinion.**  With a key that separates
plans, a hit on a sound store is exactly what resolving again would have
said. -/
theorem replay_agrees_with_run {key : Plan → K} {run : Plan → Outcome}
    {s : Store K} (hkey : Function.Injective key) (hs : Sound key run s)
    {p : Plan} {o : Outcome} (h : lookup s (key p) = some o) :
    o = run p := by
  obtain ⟨q, hq, ho⟩ := hs (key p) o h
  rw [hkey hq] at ho
  exact ho.symm

/-- **The case the round was taken for.**  Where resolving refuses, a sound
store under a separating key hands back that refusal and nothing else. -/
theorem replay_preserves_refusal {key : Plan → K} {run : Plan → Outcome}
    {s : Store K} (hkey : Function.Injective key) (hs : Sound key run s)
    {p : Plan} {reason : String} (hrun : run p = .refused reason)
    {o : Outcome} (h : lookup s (key p) = some o) :
    o = .refused reason := by
  rw [replay_agrees_with_run hkey hs h, hrun]

/-! ## The key has to cover the whole conversation -/

/-- The key the store ships with: the plan itself.  A digest that is checked
against the stored plan's own content before it is used is this key, which is
why a collision can cost a miss and cannot cost an answer. -/
def exactKey (p : Plan) : Plan := p

/-- The control: the follow-up text alone. -/
def coarseKey (p : Plan) : String := p.text

theorem exactKey_injective : Function.Injective exactKey := fun _ _ h => h

/-- **The coarse key answers the wrong question.**  Two conversations end with
the same words and resolve differently; a store keyed by those words alone is
*sound* — its one entry really was decided by the resolver — and still hands
the first conversation the second one's antecedent. -/
theorem coarse_key_answers_the_wrong_question :
    ∃ (run : Plan → Outcome) (p q : Plan) (s : Store String),
      p ≠ q ∧ coarseKey p = coarseKey q ∧ Sound coarseKey run s ∧
      lookup s (coarseKey p) = some (run q) ∧ run p ≠ run q := by
  classical
  refine ⟨fun r => if r.before = ["describe carbon"] then .bound "C"
            else .bound "Og",
    ⟨["describe carbon"], "describe it"⟩,
    ⟨["largest atomic_weight_u in element"], "describe it"⟩,
    [("describe it", .bound "Og")], ?_, rfl, ?_, ?_, ?_⟩
  · intro h
    rw [Plan.mk.injEq] at h
    simp at h
  · intro k o h
    refine ⟨⟨["largest atomic_weight_u in element"], "describe it"⟩, ?_, ?_⟩
    · simp [lookup] at h
      simp [coarseKey, h.1.symm]
    · simp [lookup] at h
      simp [h.2.symm]
  · simp [lookup, coarseKey]
  · simp

/-- **And the exact key does not.**  Under the key the store ships with, the
same two conversations are two keys, so each gets its own answer back. -/
theorem exact_key_separates_the_two_conversations
    (run : Plan → Outcome)
    (p q : Plan) (h : p ≠ q) :
    lookup (record ([] : Store Plan) (exactKey q) (run q)) (exactKey p)
      = none := by
  simpa [lookup, record, exactKey] using Ne.symm h

end GLM.PlanStore
