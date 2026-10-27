import RequestProject.GLM.Rule30.Injector

/-!
# Round 18 data: exact numbers of surviving injector pairs

`injectorPairs_card_odd` (in `Injector.lean`) proves that the number of surviving pairs for
`M_{n+1}` is odd for every `n ≥ 1`.  The exact counts below show that more than one pair
survives, so the oddness comes from cancellation in pairs, not from a single term.
-/

namespace GLM.Rule30

/-- **The surviving pairs are not unique: the oddness is a parity lock.** Exact counts for
`n = 1, 2, 3, 4` (machine-checked computation): `3, 3, 5, 3` surviving pairs. -/
theorem injectorPairs_card_small :
    (injectorPairs 1).card = 3 ∧ (injectorPairs 2).card = 3 ∧ (injectorPairs 3).card = 5 ∧
      (injectorPairs 4).card = 3 := by
  native_decide

end GLM.Rule30
