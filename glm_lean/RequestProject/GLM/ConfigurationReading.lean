import Mathlib

/-!
# The configuration reading: the 28-vertex pair of lattice item 6 (Phase 122)

`studies/CONFIGURATION_READING_STUDY.md` reads a deep hole's ensemble through
the **configuration** of the vertices it reached rather than a sorted list of
their shares.  Each arrival vertex `v` gets a key `κ v` (the size of its
component of the affine diagram the arrival vertices form, and its degree
counted with multiplicity), and the profile is the pushforward of the arrival
shares along `κ`.  This file proves the three facts the study measures
against.

## 1.  The pushforward is non-expansive in L1

`push_shift_le`: for any key map, the L1 distance between the pushforwards of
two share vectors is at most their L1 distance vertex by vertex.  For one hole
under two seeds the vertices are the same lattice points, so the configuration
reading's seed shift is bounded by the vertex-matched shift
(`config_shift_le_matched`), exactly as Phase 121 bounded the sorted reading's.

## 2.  The two 28-vertex holes in the uniform limit

The vertices of a deep hole of type `E_6^4` form four copies of the affine
diagram `Ẽ_6`; those of `D_6^4`, four copies of `D̃_6`.  Both have seven nodes
per copy and so 28 vertices, which is why a sorted share list cannot tell them
apart once every share is near `1/28`.  Their degree sequences differ:
`Ẽ_6` has degree counts `3, 3, 1` (degrees 1, 2, 3), `D̃_6` has `4, 1, 2`
(`e6_degree_counts`, `d6_degree_counts`).  With uniform shares the two
configuration profiles are at L1 distance exactly `4/7`
(`e6_d6_uniform_distance`).  The same computation for the 27-vertex pair
`E_8^3` / `D_8^3` gives `4/9` (`e8_d8_uniform_distance`), the closest pair the
study predicts.

## 3.  A separation floor

`separation_floor`: two configuration profiles are at least their
uniform-limit distance apart, less each one's vertex-level departure from
uniform.  For the 28-vertex pair (`e6_d6_separation_floor`) that is
`4/7 - δ_E - δ_D`; so whenever the two ensembles' shares are, between them,
within `4/7` of uniform in L1, the reading separates the pair
(`e6_d6_separated`).  The sorted reading has floor `0` in the same limit.
-/

namespace GLM.ConfigurationReading

open Finset

/-! ## 1.  The pushforward is non-expansive in L1 -/

/-- The pushforward of a share vector `s` along a key map `κ`: the total share
of the vertices with key `b`. -/
def push {α β : Type*} [Fintype α] [DecidableEq β] (κ : α → β) (s : α → ℚ)
    (b : β) : ℚ :=
  ∑ a ∈ univ.filter (fun a => κ a = b), s a

/-- The L1 distance between two profiles on a finite key set. -/
def l1 {β : Type*} [Fintype β] (x y : β → ℚ) : ℚ := ∑ b, |x b - y b|

theorem l1_triangle {β : Type*} [Fintype β] (x y z : β → ℚ) :
    l1 x z ≤ l1 x y + l1 y z := by
  unfold l1
  rw [← Finset.sum_add_distrib]
  exact Finset.sum_le_sum fun b _ => abs_sub_le (x b) (y b) (z b)

theorem l1_comm {β : Type*} [Fintype β] (x y : β → ℚ) : l1 x y = l1 y x := by
  unfold l1
  exact Finset.sum_congr rfl fun b _ => abs_sub_comm _ _

/-- **The pushforward is non-expansive in L1.**  Grouping vertices by key can
only cancel differences, never create them. -/
theorem push_shift_le {α β : Type*} [Fintype α] [Fintype β] [DecidableEq β]
    (κ : α → β) (s t : α → ℚ) :
    l1 (push κ s) (push κ t) ≤ ∑ a, |s a - t a| := by
  unfold l1 push
  calc ∑ b, |∑ a ∈ univ.filter (fun a => κ a = b), s a
            - ∑ a ∈ univ.filter (fun a => κ a = b), t a|
      = ∑ b, |∑ a ∈ univ.filter (fun a => κ a = b), (s a - t a)| := by
        simp only [Finset.sum_sub_distrib]
    _ ≤ ∑ b, ∑ a ∈ univ.filter (fun a => κ a = b), |s a - t a| :=
        Finset.sum_le_sum fun b _ => Finset.abs_sum_le_sum_abs _ _
    _ = ∑ a, |s a - t a| := Finset.sum_fiberwise univ κ _

/-- **The configuration reading's seed shift is bounded by the vertex-matched
shift.**  `s` and `t` are one hole's arrival shares under two seeds, indexed
by the same vertices (zero where a seed did not arrive); `κ` is any key map,
in particular the diagram key of the study. -/
theorem config_shift_le_matched {α β : Type*} [Fintype α] [Fintype β]
    [DecidableEq β] (κ : α → β) (s t : α → ℚ) :
    l1 (push κ s) (push κ t) ≤ ∑ a, |s a - t a| :=
  push_shift_le κ s t

/-! ## 2.  The affine diagrams and their uniform-limit profiles -/

/-- The edges of `Ẽ_6`: a centre (node 0) with three arms of length two
(nodes 1–2, 3–4, 5–6). -/
def e6Edges : List (Fin 7 × Fin 7) := [(0, 1), (1, 2), (0, 3), (3, 4), (0, 5), (5, 6)]

/-- The edges of `D̃_6`: a path 0 – 1 – 2 with two leaves on each end
(nodes 3, 4 on node 0; nodes 5, 6 on node 2). -/
def d6Edges : List (Fin 7 × Fin 7) := [(0, 1), (1, 2), (0, 3), (0, 4), (2, 5), (2, 6)]

/-- The edges of `Ẽ_8`: a branch node 0 with arms of lengths 1, 2 and 5. -/
def e8Edges : List (Fin 9 × Fin 9) :=
  [(0, 1), (0, 2), (2, 3), (0, 4), (4, 5), (5, 6), (6, 7), (7, 8)]

/-- The edges of `D̃_8`: a path 0 – 1 – 2 – 3 – 4 with two leaves on each end. -/
def d8Edges : List (Fin 9 × Fin 9) :=
  [(0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (0, 6), (4, 7), (4, 8)]

/-- The degree of node `i` in a diagram given by its (simple) edge list. -/
def degree {n : ℕ} (edges : List (Fin n × Fin n)) (i : Fin n) : ℕ :=
  (edges.filter (fun e => e.1 = i ∨ e.2 = i)).length

/-- Each diagram is a tree on its nodes: one fewer edge than nodes, so the
number of edges (and the total share-weighted degree) cannot tell them
apart. -/
theorem diagrams_are_trees :
    e6Edges.length = 6 ∧ d6Edges.length = 6 ∧ e8Edges.length = 8 ∧
    d8Edges.length = 8 := by decide

/-- `Ẽ_6`: three nodes of degree 1, three of degree 2, one of degree 3. -/
theorem e6_degree_counts :
    (univ.filter (fun i => degree e6Edges i = 1)).card = 3 ∧
    (univ.filter (fun i => degree e6Edges i = 2)).card = 3 ∧
    (univ.filter (fun i => degree e6Edges i = 3)).card = 1 := by decide

/-- `D̃_6`: four nodes of degree 1, one of degree 2, two of degree 3. -/
theorem d6_degree_counts :
    (univ.filter (fun i => degree d6Edges i = 1)).card = 4 ∧
    (univ.filter (fun i => degree d6Edges i = 2)).card = 1 ∧
    (univ.filter (fun i => degree d6Edges i = 3)).card = 2 := by decide

/-- The diagram key of a hole made of `c` copies of one affine diagram on `n`
nodes, restricted to its degree part (every component has the same size, so
the size part of the key is constant).  Degrees in these diagrams are at most
3, so `Fin 4` holds every key. -/
def degKey {c n : ℕ} (edges : List (Fin n × Fin n)) (v : Fin c × Fin n) : Fin 4 :=
  ⟨min (degree edges v.2) 3, by omega⟩

/-- The uniform share on `c · n` vertices. -/
def uniform (c n : ℕ) : Fin c × Fin n → ℚ := fun _ => 1 / (c * n : ℚ)

/-- **The 28-vertex pair in the uniform limit.**  With every one of the 28
vertices at share `1/28`, the configuration profiles of `E_6^4` and `D_6^4`
are `4/7` apart in L1. -/
theorem e6_d6_uniform_distance :
    l1 (push (degKey (c := 4) e6Edges) (uniform 4 7))
       (push (degKey (c := 4) d6Edges) (uniform 4 7)) = 4 / 7 := by
  unfold l1 push uniform degKey
  decide +kernel

/-- **The 27-vertex pair `E_8^3` / `D_8^3` in the uniform limit**: `4/9`. -/
theorem e8_d8_uniform_distance :
    l1 (push (degKey (c := 3) e8Edges) (uniform 3 9))
       (push (degKey (c := 3) d8Edges) (uniform 3 9)) = 4 / 9 := by
  unfold l1 push uniform degKey
  decide +kernel

/-! ## 3.  A separation floor -/

/-- **The separation floor.**  Two holes on the same vertex index type with key
maps `κ₁`, `κ₂` and shares `s₁`, `s₂`: their configuration profiles are at
least the distance between the profiles of the reference shares `u₁`, `u₂`,
less each hole's vertex-level departure from its reference share. -/
theorem separation_floor {α β : Type*} [Fintype α] [Fintype β] [DecidableEq β]
    (κ₁ κ₂ : α → β) (s₁ s₂ u₁ u₂ : α → ℚ) :
    l1 (push κ₁ u₁) (push κ₂ u₂) - ∑ a, |s₁ a - u₁ a| - ∑ a, |s₂ a - u₂ a|
      ≤ l1 (push κ₁ s₁) (push κ₂ s₂) := by
  have h1 := push_shift_le κ₁ s₁ u₁
  have h2 := push_shift_le κ₂ s₂ u₂
  have t1 := l1_triangle (push κ₁ u₁) (push κ₁ s₁) (push κ₂ u₂)
  have t2 := l1_triangle (push κ₁ s₁) (push κ₂ s₂) (push κ₂ u₂)
  rw [l1_comm (push κ₁ u₁) (push κ₁ s₁)] at t1
  linarith

/-- **The floor for the 28-vertex pair**: whatever the two ensembles' shares,
the configuration reading puts `E_6^4` and `D_6^4` at least
`4/7 - δ_E - δ_D` apart, where `δ` is each one's L1 departure from uniform. -/
theorem e6_d6_separation_floor (sE sD : Fin 4 × Fin 7 → ℚ) :
    4 / 7 - ∑ a, |sE a - uniform 4 7 a| - ∑ a, |sD a - uniform 4 7 a|
      ≤ l1 (push (degKey e6Edges) sE) (push (degKey d6Edges) sD) := by
  have := separation_floor (degKey (c := 4) e6Edges) (degKey (c := 4) d6Edges)
    sE sD (uniform 4 7) (uniform 4 7)
  rwa [e6_d6_uniform_distance] at this

/-- **The pair is separated** whenever the two share vectors are, between
them, within `4/7` of uniform: the configuration profiles then differ.  The
sorted share reading has no such floor — two uniform share lists of equal
length coincide. -/
theorem e6_d6_separated (sE sD : Fin 4 × Fin 7 → ℚ)
    (h : ∑ a, |sE a - uniform 4 7 a| + ∑ a, |sD a - uniform 4 7 a| < 4 / 7) :
    0 < l1 (push (degKey e6Edges) sE) (push (degKey d6Edges) sD) := by
  have := e6_d6_separation_floor sE sD
  linarith

end GLM.ConfigurationReading
