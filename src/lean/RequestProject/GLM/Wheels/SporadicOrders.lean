module

public import Mathlib

/-!
# The Monster Wheel's group orders: the 26 sporadic simple groups

*Created 31 October 2026 (repository check; the intake of `source_material/ToDo/glm_wheels_bundle`,
directive D22).* The supplied Monster Wheel (`monster_wheel.py`, data `cfsg_seed.py`) adds to the
Integer Wheel the 26 sporadic simple groups, keyed by order and by the prime factorisation of the
order, and answers `find_by_order`. This file proves the finite facts that mechanism rests on:

* `order_M11` … `order_M` — each stored order equals its prime factorisation (26 facts; the
  exponents are the exponent vector the wheel stores over the primes `2 … 73`);
* `sporadicOrders_length` — there are 26 of them;
* `sporadicOrders_nodup`, `sporadicNames_nodup` — the 26 orders are distinct, and so are the names;
* `findByOrder_sound` — `findByOrder n = some g` only if `g` is a sporadic group of order `n`;
* `findByOrder_complete` — and, the orders being distinct, every sporadic group is found by its
  order: the answer to "which sporadic group has order `n`?" is unique.

That the Monster Wheel keeps every Integer Wheel entry is the `merge_keeps` theorem of
`Wheels/IntegerWheel.lean`, so the Integer Wheel's soundness carries over to it.
`tests/test_monster_wheel.py` reads `sporadicOrders` and the `order_…` statements below and compares
them with the Python data, so a drift between the two fails a test. Everything here is formal
(`norm_num`, `decide`; no `native_decide`).
-/

@[expose] public section

namespace GLM.SporadicOrders

/-- The 26 sporadic simple groups and their orders. -/
def sporadicOrders : List (String × ℕ) :=
  [("M11", 7920), ("M12", 95040), ("M22", 443520), ("M23", 10200960), ("M24", 244823040),
   ("J1", 175560), ("J2", 604800), ("J3", 50232960), ("J4", 86775571046077562880),
   ("Co1", 4157776806543360000), ("Co2", 42305421312000), ("Co3", 495766656000),
   ("HS", 44352000), ("McL", 898128000), ("He", 4030387200), ("Ru", 145926144000),
   ("Suz", 448345497600), ("ON", 460815505920), ("Fi22", 64561751654400),
   ("Fi23", 4089470473293004800), ("Fi24'", 1255205709190661721292800),
   ("HN", 273030912000000), ("Th", 90745943887872000), ("Ly", 51765179004000000),
   ("B", 4154781481226426191177580544000000),
   ("M", 808017424794512875886459904961710757005754368000000000)]

theorem sporadicOrders_length : sporadicOrders.length = 26 := rfl

/-! ## Each order is its factorisation -/

theorem order_M11 : (7920 : ℕ) = 2 ^ 4 * 3 ^ 2 * 5 * 11 := by norm_num
theorem order_M12 : (95040 : ℕ) = 2 ^ 6 * 3 ^ 3 * 5 * 11 := by norm_num
theorem order_M22 : (443520 : ℕ) = 2 ^ 7 * 3 ^ 2 * 5 * 7 * 11 := by norm_num
theorem order_M23 : (10200960 : ℕ) = 2 ^ 7 * 3 ^ 2 * 5 * 7 * 11 * 23 := by norm_num
theorem order_M24 : (244823040 : ℕ) = 2 ^ 10 * 3 ^ 3 * 5 * 7 * 11 * 23 := by norm_num
theorem order_J1 : (175560 : ℕ) = 2 ^ 3 * 3 * 5 * 7 * 11 * 19 := by norm_num
theorem order_J2 : (604800 : ℕ) = 2 ^ 7 * 3 ^ 3 * 5 ^ 2 * 7 := by norm_num
theorem order_J3 : (50232960 : ℕ) = 2 ^ 7 * 3 ^ 5 * 5 * 17 * 19 := by norm_num
theorem order_J4 : (86775571046077562880 : ℕ) =
    2 ^ 21 * 3 ^ 3 * 5 * 7 * 11 ^ 3 * 23 * 29 * 31 * 37 * 43 := by norm_num
theorem order_Co1 : (4157776806543360000 : ℕ) =
    2 ^ 21 * 3 ^ 9 * 5 ^ 4 * 7 ^ 2 * 11 * 13 * 23 := by norm_num
theorem order_Co2 : (42305421312000 : ℕ) = 2 ^ 18 * 3 ^ 6 * 5 ^ 3 * 7 * 11 * 23 := by norm_num
theorem order_Co3 : (495766656000 : ℕ) = 2 ^ 10 * 3 ^ 7 * 5 ^ 3 * 7 * 11 * 23 := by norm_num
theorem order_HS : (44352000 : ℕ) = 2 ^ 9 * 3 ^ 2 * 5 ^ 3 * 7 * 11 := by norm_num
theorem order_McL : (898128000 : ℕ) = 2 ^ 7 * 3 ^ 6 * 5 ^ 3 * 7 * 11 := by norm_num
theorem order_He : (4030387200 : ℕ) = 2 ^ 10 * 3 ^ 3 * 5 ^ 2 * 7 ^ 3 * 17 := by norm_num
theorem order_Ru : (145926144000 : ℕ) = 2 ^ 14 * 3 ^ 3 * 5 ^ 3 * 7 * 13 * 29 := by norm_num
theorem order_Suz : (448345497600 : ℕ) = 2 ^ 13 * 3 ^ 7 * 5 ^ 2 * 7 * 11 * 13 := by norm_num
theorem order_ON : (460815505920 : ℕ) = 2 ^ 9 * 3 ^ 4 * 5 * 7 ^ 3 * 11 * 19 * 31 := by norm_num
theorem order_Fi22 : (64561751654400 : ℕ) = 2 ^ 17 * 3 ^ 9 * 5 ^ 2 * 7 * 11 * 13 := by norm_num
theorem order_Fi23 : (4089470473293004800 : ℕ) =
    2 ^ 18 * 3 ^ 13 * 5 ^ 2 * 7 * 11 * 13 * 17 * 23 := by norm_num
theorem order_Fi24' : (1255205709190661721292800 : ℕ) =
    2 ^ 21 * 3 ^ 16 * 5 ^ 2 * 7 ^ 3 * 11 * 13 * 17 * 23 * 29 := by norm_num
theorem order_HN : (273030912000000 : ℕ) = 2 ^ 14 * 3 ^ 6 * 5 ^ 6 * 7 * 11 * 19 := by norm_num
theorem order_Th : (90745943887872000 : ℕ) =
    2 ^ 15 * 3 ^ 10 * 5 ^ 3 * 7 ^ 2 * 13 * 19 * 31 := by norm_num
theorem order_Ly : (51765179004000000 : ℕ) =
    2 ^ 8 * 3 ^ 7 * 5 ^ 6 * 7 * 11 * 31 * 37 * 67 := by norm_num
theorem order_B : (4154781481226426191177580544000000 : ℕ) =
    2 ^ 41 * 3 ^ 13 * 5 ^ 6 * 7 ^ 2 * 11 * 13 * 17 * 19 * 23 * 31 * 47 := by norm_num
theorem order_M : (808017424794512875886459904961710757005754368000000000 : ℕ) =
    2 ^ 46 * 3 ^ 20 * 5 ^ 9 * 7 ^ 6 * 11 ^ 2 * 13 ^ 3 * 17 * 19 * 23 * 29 * 31 * 41 * 47 * 59 * 71 := by
  norm_num

/-! ## Distinct orders, and a unique answer to `find_by_order` -/

theorem sporadicOrders_nodup : (sporadicOrders.map Prod.snd).Nodup := by decide

theorem sporadicNames_nodup : (sporadicOrders.map Prod.fst).Nodup := by decide

/-- `find_by_order`: the name of the sporadic group of order `n`, if there is one. -/
def findByOrder (n : ℕ) : Option String :=
  (sporadicOrders.find? (fun g => g.2 = n)).map Prod.fst

theorem findByOrder_sound {n : ℕ} {g : String} (h : findByOrder n = some g) :
    (g, n) ∈ sporadicOrders := by
  unfold findByOrder at h
  obtain ⟨p, hp, rfl⟩ := Option.map_eq_some_iff.1 h
  have hmem := List.mem_of_find?_eq_some hp
  have hn : p.2 = n := by simpa using List.find?_some hp
  obtain ⟨a, b⟩ := p
  simp only at hn
  subst hn
  exact hmem

theorem findByOrder_complete {n : ℕ} {g : String} (h : (g, n) ∈ sporadicOrders) :
    findByOrder n = some g := by
  have key : ∀ p ∈ sporadicOrders, ∀ q ∈ sporadicOrders, p.2 = q.2 → p = q := by decide
  unfold findByOrder
  cases hf : sporadicOrders.find? (fun g => g.2 = n) with
  | none =>
    have := List.find?_eq_none.1 hf (g, n) h
    simp at this
  | some p =>
    have hmem := List.mem_of_find?_eq_some hf
    have hn : p.2 = n := by simpa using List.find?_some hf
    have := key p hmem (g, n) h hn
    simp [this]

end GLM.SporadicOrders
