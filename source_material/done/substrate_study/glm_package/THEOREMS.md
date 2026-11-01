# Index of machine-checked results

Every name below is a theorem in `../RequestProject/GLM/` (Lean 4 + Mathlib, namespace `GLM`),
proved with no `sorry`. Finite facts about explicit codes use `native_decide`, so those proofs
also trust Lean's compiler. The statements here are informal summaries. The Lean docstrings give
the exact hypotheses.

Notation: "a design" means any set of 4096 words in \(\mathbb F_2^{24}\), linear or not, with any
decoder. "Weight-\(w\) corruption" means \(w\) bit flips.

## 1. Universal limits (any code, any length): `Bounds.lean`

| Result | Lean |
|---|---|
| Hamming spheres and balls have \(\binom{n}{i}\) and \(V(n,t)\) points | `card_sphere`, `card_ball` |
| BSC bound: success probability of every code and decoder is \(\le\) `qpBound` | `successProb_le_qpBound` |
| Quasi-perfect decoders attain the bound with equality (design criterion) | `successProb_eq_qpBound_of_quasiPerfect` |
| Correcting all weight \(\le t\) forces \(\lvert C\rvert\,V(n,t)\le2^n\) | `card_mul_ballVol_le_of_corrects` |
| At most \(\lvert C\rvert\,V(n,t)\) words are decoded within distance \(t\) | `card_near_le` |
| Next-shell ceiling | `card_corrected_next_shell_le` |
| Side information with \(K\) values: \(\lvert C\rvert\,V(n,r)\le 2^nK\) | `card_mul_ballVol_le_side_info` |

## 2. The Golay substrate: `Golay.lean`, `GolayOptimal.lean`, `Steiner.lean`, `GolaySymmetry.lean`

| Result | Lean |
|---|---|
| 4096 codewords; weight enumerator \(1+759z^8+2576z^{12}+759z^{16}+z^{24}\); minimum weight 8 | `card_golayCode`, `golay_weight_enumerator`, `golay_min_weight` |
| Self-orthogonal generator; code = kernel of the syndrome | `golayRow_dot_golayRow`, `mem_golayCode_iff` |
| Coset-leader census \(1,24,276,2024,1771\); covering radius 4 | `golayLeader_wt_count`, `golay_dist_le_four` |
| Exact success probability \(w_0+24w_1+276w_2+2024w_3+1771w_4\) | `golay_successProb` |
| **Optimal among all designs, for every \(p\le1/2\)** | `golay_optimal` |
| Corrects every weight \(\le3\) corruption; completes any 7 erasures | `golay_corrects_weight_le3`, `golay_erasure_unique` |
| No design corrects all weight-4 corruptions | `no_substrate_corrects_all_weight4` |
| One-sixth ceiling for weight-4 events; Golay attains it | `weight4_resolvable_le`, `golay_weight4_resolved` |
| Negative-space floor \(4096\cdot1771\) for every design | `negative_space_floor` |
| Rate limits at length 24: \(\le1295\) words for 4-bit correction, \(\le7216\) for 3-bit | `card_le_of_corrects_weight4`, `card_le_of_corrects_weight3` |
| Octads form the Steiner system \(S(5,8,24)\) | `steiner_5_8_24` |
| Puncturing gives the perfect \([23,12,7]\) code | `golay23_perfect` |
| The cyclic shift of `DesignSpec_v1.pdf` §4 maps \(G_{24}\) onto itself | `golayRho_image` |

## 3. The negative space and the mirror: `Mirror.lean`, `CheapMirror.lean`, `GolayPartialMirror.lean`

| Result | Lean |
|---|---|
| Every weight-4 coset holds exactly six disjoint weight-4 words covering all 24 positions (a sextet) | `card_golaySextet`, `golaySextet_disjoint`, `golaySextet_cover` |
| After a weight-4 corruption exactly 6 codewords lie within distance 4 | `golay_candidates_card` |
| After a weight-4 corruption no codeword lies within distance 3 (never silent) | `golay_no_silent_weight4` |
| Parities along codewords are syndrome functions: no branch information | `dot_golayEncode`, `codeword_parity_constant_on_coset` |
| Any design needs \(\ge4\) mirror labels | `side_info_floor_universal` |
| Golay needs exactly 6 labels | `golay_side_info_needs_six`, `golay_side_info_six_suffice` |
| Minimum distance 8 forces \(\ge6\) labels | `side_info_needs_six_of_dist8` |
| Trade-off: correcting all weight \(\le3\) means silent weight-4 errors or \(\ge6\) labels | `silent_or_six_labels` |
| \(\le5\) labels force ambiguity after some corruption of weight \(\le3\) | `cheap_mirror_forces_early_ambiguity`, `six_labels_of_unambiguous_le3` |
| Partial mirrors on Golay: \(K\) labels resolve exactly a fraction \(K/6\) of weight-4 events, and no more | `golay_partial_mirror_upper`, `golay_partial_mirror_achieves` |

## 4. The five-label substrate: `Mirror5.lean`, `MirrorConsult.lean`, `GolayExtWitness.lean`, `GolayExtMirror.lean`

| Result | Lean |
|---|---|
| `mirror5Code` has 4096 words and needs exactly 5 mirror labels | `card_mirror5Code`, `mirror5_five_labels_suffice`, `mirror5_needs_five` |
| Its minimum distance is 5; every single flip is ambiguous | `mirror5_min_dist`, `mirror5_single_flip_ambiguous` |
| Its list-size histogram over the 4096 syndromes | `mirror5_list_histogram` |
| Exact consultation probabilities: Golay \(10626p^4(1-p)^{20}\), and the five-label code's polynomial | `golay_consultProb`, `mirror5_consultProb` |
| The five-label code consults more often for every \(0<p\le1/2\); more than 2000× at \(p=1/100\) | `golay_consult_lt_mirror5`, `mirror5_consult_at_one_percent` |
| All 4096 one-bit extensions of \([23,12,7]\) have distance \(\ge7\) and need \(\ge6\) labels | `ext23Encode_wt_ge`, `ext23_needs_six` |

## 5. The trigger and on-demand clarification: `TriggeredMirror.lean`, `Tag.lean`, `Delsarte.lean`

| Result | Lean |
|---|---|
| The trigger fires on exactly \(4096\cdot1771\) words, the words at distance \(\ge4\) from the code | `card_golayTrigger`, `golayTrigger_iff_far` |
| Never fires after \(\le3\) flips; always fires after 4; for weight \(\le4\) it fires iff the list is ambiguous | `golayTrigger_off_le3`, `golayTrigger_on_4`, `golayTrigger_iff_ambiguous` |
| Firing and the sextet depend only on the error | `golayTrigger_error_only` |
| Triggered candidates: received word plus the six tetrads, pairwise at distance 8 | `golay_triggered_candidates`, `golay_triggered_candidates_dist` |
| \(K\) labels on demand give lists of \(\le\lceil6/K\rceil\) containing the truth; optimal | `golay_triggered_list_mirror`, `golay_triggered_list_lower` |
| \(m\) events need exactly \(6^m\) joint labels; 5 events in 13 bits | `golay_batch_labels_lower`, `golay_batch_labels_suffice`, `six_pow_five_le_two_pow_thirteen` |
| Per-position flip probabilities rank the six candidates (least reliable tetrad) | `posLik_shift`, `posLik_le_iff` |
| Triggered Golay uses fewer expected label bits than the five-label code for \(0<p\le1/4\) | `golay_triggered_bits_lt_mirror5` |
| Sender tag corrects radius \(r\) iff it separates codewords at distance \(\le2r\) | `tagCorrects_iff` |
| At most 48 words of length 24 pairwise at distance \(\ge12\) | `card_le_48_of_dist_ge_12` |
| Golay sender tag needs \(\ge86\) labels; an explicit linear 7-bit tag works; on-demand protocol | `golay_tag_lower`, `golay_tag_upper`, `golay_on_demand` |
| Delsarte inequalities; \(A(24,9)\le551\); any design's sender tag needs \(\ge8\) labels | `delsarte_nonneg`, `card_le_551_of_dist_ge_9`, `tag_needs_eight_labels` |

## 6. Soft resolution: `SoftResolve.lean`

| Result | Lean |
|---|---|
| \(\lVert\pm1(c)-\pm1(c')\rVert^2 = 4\,d(c,c')\); distinct Golay codewords are \(\ge32\) apart | `sqDist_phase`, `golay_phase_sqDist_ge` |
| Certificate: \(\lVert r-\pm1(c)\rVert^2<8\) implies \(c\) is the unique nearest codeword | `soft_certificate` |
| The radius 8 is sharp | `soft_certificate_sharp` |
| Noise energy \(<8\) causes at most 7 hard flips; a 7-flip example resolved for free | `soft_noise_flips_le_seven`, `soft_beats_hard_example` |
| Flipping a tetrad changes the squared distance by \(4\sum_{j\in t}\lvert r_j\rvert\) | `sqDist_flip_tetrad` |
| Posterior gate: accepting only at posterior \(\ge1-\varepsilon\) gives \(P(\text{accepted and wrong})\le\varepsilon P(\text{accepted})\) | `posterior_gate_silent_error_le` |

## 7. The Leech layer: `Leech.lean`, `LeechKissing.lean`

| Result | Lean |
|---|---|
| Leech vectors (Golay construction) form an additive subgroup of \(\mathbb Z^{24}\); nonzero norm \(\ge32\) (minimal norm 4 after rescaling) | `leechLattice`, `leech_min_norm` |
| Norm-32 vectors are exactly the three standard shapes | `mem_leechMinimal_iff` |
| Their counts are 1104, 97152, 98304; total **196,560** | `card_parA_image`, `card_parB_image`, `card_parC_image`, `leech_kissing`, `leech_kissing_number` |

## 8. HPSKL: `HPSKLLeech.lean`, `QuantumDiscrimination.lean`, `HPSKLVerdict.lean`

| Result | Lean |
|---|---|
| Leech norms are \(\equiv0 \bmod 16\), inner products divisible by 8 | `leech_normSq_mod16`, `leech_inner_dvd8` |
| Minimal-vector inner products lie in \(\{\pm32,\pm16,\pm8,0\}\); state overlaps in \(\{0,1/4,1/2\}\) | `leech_min_inner_cases`, `leech_codebook_fidelity` |
| More than 24 HPSKL states force an overlap \(\ge1/4\) | `leech_codebook_large_overlap` |
| GLM phase states: overlaps in \(\{\pm1,\pm1/3,0\}\); a codeword and its complement give the same ray | `golay_phase_inner_cases`, `phase_add_one` |
| Any POVM: summed success \(\le\operatorname{Tr}P\); after depolarizing noise \(\le(1-p)\operatorname{Tr}P+p\); tight frames attain it | `success_sum_le`, `success_sum_le_depolarized`, `tight_frame_success` |
| Depolarizing noise rescales differences; the contact graph is unchanged up to threshold | `depolarize_sub`, `contact_iff` |
| A GLM symbol in one 5-qubit state: average success \(\le1/128\) | `five_qubit_success_le`, `five_qubit_glm_symbol` |
| Real 24-dimensional restriction: \(\le24-23p\); the GLM phase codebook is a tight frame and optimal | `real24_success_le`, `golay_phase_frame`, `glm_phase_codebook_optimal` |
