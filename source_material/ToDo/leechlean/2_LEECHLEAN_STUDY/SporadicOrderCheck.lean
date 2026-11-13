module

public import Mathlib

/-!
# The 26 sporadic group orders, checked on their own

*Created 1 November 2026 (Phase 186: the intake of `source_material/ToDo/glm_wheels_bundle`,
directive D22; a standalone check, written for the absorption ahead of the owner's build).*

The Monster Wheel answers "which sporadic group has order `n`?" from a table of the 26 sporadic
simple groups. This file states the 26 orders afresh, from their standard prime factorisations, and
proves the two facts the answer rests on, independently of `Wheels/SporadicOrders.lean`:

* `order_M11` … `order_M` — each order equals its prime factorisation (26 facts, `norm_num`);
* `orders_nodup` — the 26 orders are distinct, so an order names at most one group;
* `names_nodup` — the 26 names are distinct.

`tests/test_monster_wheel.py` compares `orders` with the Python data of the wheel. Everything here
is formal (`norm_num`, `decide`; no `native_decide`).
-/

@[expose] public section

namespace GLM.IntakeChecks.SporadicOrderCheck

/-- The 26 sporadic simple groups with their orders (ATLAS names; `ON` is O'Nan, `Fi24'` the
derived Fischer group, `B` the Baby Monster and `M` the Monster). -/
def orders : List (String × ℕ) :=
  [("M11", 7920), ("M12", 95040), ("J1", 175560), ("M22", 443520), ("J2", 604800),
   ("M23", 10200960), ("HS", 44352000), ("J3", 50232960), ("M24", 244823040),
   ("McL", 898128000), ("He", 4030387200), ("Ru", 145926144000), ("Suz", 448345497600),
   ("ON", 460815505920), ("Co3", 495766656000), ("Co2", 42305421312000),
   ("Fi22", 64561751654400), ("HN", 273030912000000), ("Ly", 51765179004000000),
   ("Th", 90745943887872000), ("Fi23", 4089470473293004800), ("Co1", 4157776806543360000),
   ("J4", 86775571046077562880), ("Fi24'", 1255205709190661721292800),
   ("B", 4154781481226426191177580544000000),
   ("M", 808017424794512875886459904961710757005754368000000000)]

theorem orders_length : orders.length = 26 := by decide

theorem orders_nodup : (orders.map Prod.snd).Nodup := by decide

theorem names_nodup : (orders.map Prod.fst).Nodup := by decide

theorem order_M11 : (7920 : ℕ) = 2 ^ 4 * 3 ^ 2 * 5 * 11 := by norm_num
theorem order_M12 : (95040 : ℕ) = 2 ^ 6 * 3 ^ 3 * 5 * 11 := by norm_num
theorem order_J1 : (175560 : ℕ) = 2 ^ 3 * 3 * 5 * 7 * 11 * 19 := by norm_num
theorem order_M22 : (443520 : ℕ) = 2 ^ 7 * 3 ^ 2 * 5 * 7 * 11 := by norm_num
theorem order_J2 : (604800 : ℕ) = 2 ^ 7 * 3 ^ 3 * 5 ^ 2 * 7 := by norm_num
theorem order_M23 : (10200960 : ℕ) = 2 ^ 7 * 3 ^ 2 * 5 * 7 * 11 * 23 := by norm_num
theorem order_HS : (44352000 : ℕ) = 2 ^ 9 * 3 ^ 2 * 5 ^ 3 * 7 * 11 := by norm_num
theorem order_J3 : (50232960 : ℕ) = 2 ^ 7 * 3 ^ 5 * 5 * 17 * 19 := by norm_num
theorem order_M24 : (244823040 : ℕ) = 2 ^ 10 * 3 ^ 3 * 5 * 7 * 11 * 23 := by norm_num
theorem order_McL : (898128000 : ℕ) = 2 ^ 7 * 3 ^ 6 * 5 ^ 3 * 7 * 11 := by norm_num
theorem order_He : (4030387200 : ℕ) = 2 ^ 10 * 3 ^ 3 * 5 ^ 2 * 7 ^ 3 * 17 := by norm_num
theorem order_Ru : (145926144000 : ℕ) = 2 ^ 14 * 3 ^ 3 * 5 ^ 3 * 7 * 13 * 29 := by norm_num
theorem order_Suz : (448345497600 : ℕ) = 2 ^ 13 * 3 ^ 7 * 5 ^ 2 * 7 * 11 * 13 := by norm_num
theorem order_ON : (460815505920 : ℕ) = 2 ^ 9 * 3 ^ 4 * 5 * 7 ^ 3 * 11 * 19 * 31 := by norm_num
theorem order_Co3 : (495766656000 : ℕ) = 2 ^ 10 * 3 ^ 7 * 5 ^ 3 * 7 * 11 * 23 := by norm_num
theorem order_Co2 : (42305421312000 : ℕ) = 2 ^ 18 * 3 ^ 6 * 5 ^ 3 * 7 * 11 * 23 := by norm_num
theorem order_Fi22 : (64561751654400 : ℕ) = 2 ^ 17 * 3 ^ 9 * 5 ^ 2 * 7 * 11 * 13 := by norm_num
theorem order_HN : (273030912000000 : ℕ) = 2 ^ 14 * 3 ^ 6 * 5 ^ 6 * 7 * 11 * 19 := by norm_num
theorem order_Ly : (51765179004000000 : ℕ) = 2 ^ 8 * 3 ^ 7 * 5 ^ 6 * 7 * 11 * 31 * 37 * 67 := by
  norm_num
theorem order_Th : (90745943887872000 : ℕ) = 2 ^ 15 * 3 ^ 10 * 5 ^ 3 * 7 ^ 2 * 13 * 19 * 31 := by
  norm_num
theorem order_Fi23 :
    (4089470473293004800 : ℕ) = 2 ^ 18 * 3 ^ 13 * 5 ^ 2 * 7 * 11 * 13 * 17 * 23 := by norm_num
theorem order_Co1 :
    (4157776806543360000 : ℕ) = 2 ^ 21 * 3 ^ 9 * 5 ^ 4 * 7 ^ 2 * 11 * 13 * 23 := by norm_num
theorem order_J4 :
    (86775571046077562880 : ℕ) = 2 ^ 21 * 3 ^ 3 * 5 * 7 * 11 ^ 3 * 23 * 29 * 31 * 37 * 43 := by
  norm_num
theorem order_Fi24' : (1255205709190661721292800 : ℕ) =
    2 ^ 21 * 3 ^ 16 * 5 ^ 2 * 7 ^ 3 * 11 * 13 * 17 * 23 * 29 := by norm_num
theorem order_B : (4154781481226426191177580544000000 : ℕ) =
    2 ^ 41 * 3 ^ 13 * 5 ^ 6 * 7 ^ 2 * 11 * 13 * 17 * 19 * 23 * 31 * 47 := by norm_num
theorem order_M : (808017424794512875886459904961710757005754368000000000 : ℕ) =
    2 ^ 46 * 3 ^ 20 * 5 ^ 9 * 7 ^ 6 * 11 ^ 2 * 13 ^ 3 * 17 * 19 * 23 * 29 * 31 * 41 * 47 * 59 *
      71 := by norm_num

end GLM.IntakeChecks.SporadicOrderCheck
