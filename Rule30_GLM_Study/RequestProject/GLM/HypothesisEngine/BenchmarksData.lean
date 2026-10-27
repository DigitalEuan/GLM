import RequestProject.GLM.HypothesisEngine.Benchmarks

/-!
# Round 39: hypothesis-engine benchmarks — finite certificates and bit-blasted laws

Companion of `Benchmarks.lean`.  These checks use `native_decide` or `bv_decide`, so they trust
Lean's compiler as well as the kernel (`CERT` in the package's evidence labels; the two midpoint
laws hold for **every** 16-bit input, established by bit-blasting).
-/

namespace GLM.HypothesisEngine

/-- The engine's survivor "every `n` reaches 1", certified on its range: every `1 ≤ n < 10000`
reaches `1` within `300` steps (`CERT`; the statement for all `n` is the open Collatz problem). -/
theorem collatz_reaches_one_below : ∀ n ∈ Finset.Ico 1 10000, reachesOne n 300 = true := by
  native_decide

/-- The statement survives on the engine's range (`CERT`, `n < 1000`). -/
theorem gcd_trap_survives : ∀ n ∈ Finset.range 1000, Nat.gcd (n ^ 17 + 9) ((n + 1) ^ 17 + 9) = 1 := by
  native_decide

/-- **The mined law (every input)**: with `lo ≤ hi`, the buggy midpoint falls below `lo` exactly
when `lo + hi` overflows 16 bits. -/
theorem midpoint_bug_iff_overflow (lo hi : BitVec 16) (h : lo ≤ hi) :
    midBuggy lo hi < lo ↔ 65536#17 ≤ lo.zeroExtend 17 + hi.zeroExtend 17 := by
  unfold midBuggy
  bv_decide

/-- **The fix (every input)**: the repaired midpoint lies in `[lo, hi]`. -/
theorem midpoint_fixed_correct (lo hi : BitVec 16) (h : lo ≤ hi) :
    lo ≤ midFixed lo hi ∧ midFixed lo hi ≤ hi := by
  unfold midFixed
  bv_decide

end GLM.HypothesisEngine
