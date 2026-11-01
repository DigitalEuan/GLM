# The GLM substrate study: record and integration package

**Question.** Is the Golay–Leech substrate of the Geometric Language Machine
([DigitalEuan/GLM](https://github.com/DigitalEuan/GLM)) optimal? Can a better one be
designed? Where are the limits, and why do they sit where they do?

**Short answer.** For the regime the GLM uses (24-bit symbols carrying 12 bits, corrupted by
bit flips), the extended Golay code \(G_{24}\) is **provably optimal**. Its "negative space" is
**forced by the parameters**: every design has at least as much of it. Golay makes that
negative space as shallow and as well structured as possible. No designed substrate beats it on
any measured axis without losing on another. The design freedom that is left lies in **how the
negative space is resolved**. This package records a protocol for that, called the *triggered
sextet mirror with soft resolution*. Its guarantees are proved, and a reference implementation
is included.

This document is self-contained. It is the record of the study and the specification to carry
into the GLM. The detailed phase reports are kept in `../reports/` as history (§11).

---

## 0. What is in this package

| File | What it is |
|---|---|
| `README.md` | this document: findings, boundaries, the recommended protocol, open problems |
| `THEOREMS.md` | index of every machine-checked result, by topic, with its Lean name and file |
| `glm_substrate.py` | reference implementation of the recommended protocol (Python standard library only) |
| `test_glm_substrate.py` | self-test of the implementation against the proved facts (`python3 test_glm_substrate.py`, a few seconds) |

The proofs live in `../RequestProject/GLM/*.lean` (Lean 4 + Mathlib, 21 files, no `sorry`).

### Evidence levels used below

* **[Lean]**: a theorem proved in Lean 4 / Mathlib in this project. Finite facts about
  explicit codes (the 4096 Golay codewords, the 4096 syndromes) are checked with
  `native_decide`, so those proofs also trust Lean's compiler. No other axioms are used
  beyond the standard three (`propext`, `Classical.choice`, `Quot.sound`).
* **[Exp]**: a computation (search, Monte Carlo, floating-point LP/SDP) in `../experiments/`.
  It is evidence, not proof. A search that finds nothing does not show that nothing exists.
* **[Lit]**: a published result that is quoted, not re-proved here.
* **[Impl]**: a property of the Python reference implementation, checked by its test suite
  and not formally verified.

---

## 1. The setting

* **Substrate.** A set \(C\) of \(4096 = 2^{12}\) words in \(\mathbb F_2^{24}\) together with a
  decoder. Each GLM symbol carries 12 bits in 24.
* **Noise.** Independent bit flips with probability \(p \le 1/2\) (the binary symmetric channel).
  In the soft-decision setting, \(\pm1\) signalling with Gaussian noise.
* **Negative space.** The received words that cannot be decoded within distance 3 of any
  codeword: "the information that falls off the Golay network".
* **Mirror.** A clarification layer. When a received word is ambiguous, it supplies a label
  with \(K\) possible values that lets the receiver choose. Two kinds are distinguished:
  * *corruption-aware labels*, which may depend on the error (for example reveals, or a
    party that observes the channel);
  * *sender tags*, computed by the sender from the codeword alone, without knowing the error.

---

## 2. Findings at a glance

| Question | Answer | Evidence |
|---|---|---|
| Is Golay optimal for correct decoding? | **Yes.** No 4096-word length-24 substrate, linear or not, with any decoder, decodes correctly more often, for every \(p\le1/2\) | [Lean] `golay_optimal` |
| How much negative space must a design have? | At least \(4096\cdot1771\) of the \(2^{24}\) received words (43.24 %), for **every** design | [Lean] `negative_space_floor` |
| Can any design correct all 4-bit corruptions? | **No.** At most one sixth of them, if all 3-bit ones are corrected. Golay attains exactly one sixth | [Lean] `no_substrate_corrects_all_weight4`, `weight4_resolvable_le`, `golay_weight4_resolved` |
| What does Golay's negative space look like? | 1771 cosets, each a **sextet**: six disjoint 4-sets tiling the 24 positions. Every 4-bit corruption leaves exactly 6 candidates, pairwise 8 apart, and is **never** silently miscorrected | [Lean] `card_golaySextet`, `golaySextet_cover`, `golay_candidates_card`, `golay_no_silent_weight4`, `golay_triggered_candidates_dist` |
| Can the negative space correct errors by itself, as a second lattice? | **No.** Every function of the received word is the same on all six branches. It is an *interface for new information*, not a corrector | [Lean] `codeword_parity_constant_on_coset`, `golay_side_info_needs_six` |
| Mirror cost for Golay? | **Exactly 6 labels** (3 bits) with corruption-aware labels | [Lean] `golay_side_info_needs_six`, `golay_side_info_six_suffice` |
| Mirror cost for any design? | At least 4 labels. 5 is achievable (`mirror5Code`). Whether 4 is achievable is **open** | [Lean] `side_info_floor_universal`, `mirror5_five_labels_suffice` |
| Is a cheaper mirror worth it? | **No.** Any design with \(\le5\) labels is already ambiguous after some corruption of \(\le3\) bits. For `mirror5Code`, after *every* single flip. It consults its mirror more than 2000 times as often as Golay at \(p=1/100\) | [Lean] `cheap_mirror_forces_early_ambiguity`, `mirror5_single_flip_ambiguous`, `mirror5_consult_at_one_percent` |
| Sender-tag cost? | Golay: between 86 and 128 labels; an explicit linear **7-bit** tag works. Any design: at least 8 labels | [Lean] `golay_tag_lower`, `golay_tag_upper`, `tag_needs_eight_labels` |
| Can the mirror be switched on only when needed? | **Yes, exactly and for free.** The trigger is read from the syndrome. It never fires after \(\le3\) flips and always fires after 4 | [Lean] `golayTrigger_off_le3`, `golayTrigger_on_4`, `golayTrigger_iff_ambiguous` |
| Can the negative space be resolved with no label at all? | **Yes, with soft information.** The nearest candidate is the least reliable 4-set. A proved certificate (radius 8) and a proved posterior gate say when the free answer is safe. In simulation the gate removed 59–99 % of label requests at 3–6 dB | [Lean] `soft_certificate`, `sqDist_flip_tetrad`, `posterior_gate_silent_error_le`; [Exp] for the percentages |
| Euclidean (Leech) layer? | The Leech lattice on the Golay carrier: minimal norm 4 and **exactly 196,560** minimal vectors (proved by classification, with no appeal to uniqueness theorems) | [Lean] `leech_min_norm`, `leech_kissing_number` |
| HPSKL (quantum phase-space codebook)? | Scientific in its v0 form, but **no advantage**. A 5-qubit state reads a GLM symbol with probability at most \(1/128\). Product-state baselines beat the Leech codebook at the brief's sizes. The useful part is the classical \(\pm1\) embedding used by soft resolution | [Lean] `five_qubit_glm_symbol`, `leech_codebook_large_overlap`, `contact_iff` |

---

## 3. Why Golay is optimal: the volume picture

Think of \(\mathbb F_2^{24}\) as \(2^{24}\) cells and the 4096 codewords as owners. A received
word at distance \(i\) from its owner has probability weight \(w_i = p^i(1-p)^{24-i}\), and
\(w_0 > w_1 > \dots\) when \(p<1/2\). The best conceivable design gives each owner its nearest
cells first. Each owner can hold at most \(\binom{24}{i}\) cells at distance \(i\):

\[
1 + 24 + 276 + 2024 = 2325 \text{ cells at distance} \le 3, \qquad
\frac{2^{24}}{4096} - 2325 = 1771 \text{ cells left over, at distance} \ge 4.
\]

`successProb_le_qpBound` [Lean] turns this into a bound for every code, every length and every
decoder. Golay's decoding regions are *exactly* this greedy filling: full radius-3 balls plus
1771 cells at distance exactly 4. So it meets the bound with equality
(`successProb_eq_qpBound_of_quasiPerfect`, `golay_optimal`).

Consequences:

1. **The negative space belongs to the parameters (24, 12), not to Golay.** Every design has at
   least 43.24 % of the space at distance \(\ge4\). Golay puts all of it at distance exactly 4,
   none deeper.
2. **The "6" in six-way ambiguity is a volume ratio:** \(\binom{24}{4} = 10626 = 6\cdot1771\).
   That is why at most one sixth of the 4-bit corruptions can be resolved
   (`weight4_resolvable_le`).
3. **Ambiguity is the price of rate.** Unique 4-bit correction needs at most 1295 codewords
   (about 10.3 bits per symbol). Correcting all 3-bit corruptions allows at most 7216
   (`card_le_of_corrects_weight4`, `card_le_of_corrects_weight3`).
4. **Golay is not the only optimal code, but it is the best-behaved one found.** Every
   quasi-perfect code ties on success probability. Among the 4096 one-bit extensions of the
   perfect \([23,12,7]\) code, all of which tie, \(G_{24}\) is the only one with no silent
   4-bit miscorrections. The others have 2695 to 8855 [Exp]. A design that corrects all 3-bit
   corruptions and needs fewer than 6 mirror labels **must** miscorrect some 4-bit corruption
   silently (`silent_or_six_labels` [Lean]).

---

## 4. The negative space as its own layer

The study set out to test this idea: a second "mirror" substrate on the negative space, which
picks up the ambiguous information that falls off the Golay network. What the theorems say:

* **Structure.** The negative space is a union of 1771 cosets. Each carries a sextet: six
  disjoint tetrads (4-sets) that tile the 24 coordinates. When a received word is in the
  negative space, its candidates are that word plus each tetrad: six codewords, pairwise
  exactly 8 apart (`golay_triggered_candidates`, `golay_triggered_candidates_dist`). Every
  triggered word is a "deep hole", at distance 4 from a regular hexad of codewords.
* **It carries information about the noise, not the message.** The syndrome identifies which
  of the 1771 sextets the corruption came from, about 10.8 bits about the error. The received
  word narrows the message from 4096 to 6. Whether the trigger fires, and which sextet it names,
  depend only on the error (`golayTrigger_error_only`).
* **It cannot correct errors on its own.** Anything the receiver computes from the received
  word takes the same value on all six branches. Even parities along codewords reduce to the
  syndrome (`dot_golayEncode`, `codeword_parity_constant_on_coset`). Resolution therefore has to
  come from *new* information. That information can be a label, a sender tag, or soft
  reliabilities.
* **Redesigning the negative space does not help.** Searches that reshaped it (linear tabu
  search, and non-linear annealing over all \(2^{24}\) received words) made six-way ambiguity
  rarer only by creating lists of 7–11 candidates elsewhere [Exp]. The volume that has to go
  somewhere does go somewhere.
* **Euclidean counterpart.** In the Leech picture, the corresponding objects are the deep holes
  of \(\Lambda_{24}\) [Lit: Conway–Sloane, *SPLAG* ch. 23]. That is a correspondence between
  structures, not a decoding mechanism.

So the paired "Golay + negative-space layer" architecture is right. The negative-space layer
should be built as a **resolver of flagged, structured ambiguity**, and the rest of this
document specifies one.

---

## 5. Designed alternatives that were tried

| Design | Result | Verdict |
|---|---|---|
| The 4095 other one-bit extensions of \([23,12,7]\) | tie on success; all miscorrect silently (2695–8855 of 10626 4-bit patterns) [Exp]; all need 6 mirror labels [Lean `ext23_needs_six`] | worse |
| Linear \([24,12]\) codes by tabu search (13 runs) | worst list stays 6; six-way lists become rare, but minimum distance falls to 3–5 [Exp] | worse |
| Arbitrary 4096-word codes by annealing (4 runs, exact over \(2^{24}\) words) | worst list rises to 10–11 [Exp] | worse |
| `mirror5Code` (\(2\times2\) block-circulant, found by exhaustive search) | mirror needs exactly 5 labels [Lean]; minimum distance 5; every single flip is ambiguous [Lean] | cheaper worst case, much worse in use |
| Codes with a cheaper sender tag | floor of 8 labels for any design [Lean]; no construction found | open, not promising |
| Soft decoding of the same codes (AWGN Monte Carlo) | Golay best of the four codes tested; soft ML about 2 dB better than hard decoding [Exp] | **largest gain found: keep Golay, use soft information** |
| HPSKL v0 (Leech-derived quantum codebook) | dimension caps discrimination (GLM symbol in 5 qubits: \(\le1/128\)) [Lean]; product-state baselines win at \(M = 16, 64, 256\) [Lean + Lit]; noise adds no contact structure of its own [Lean] | no advantage; classical \(\pm1\) embedding kept |

---

## 6. Where the boundaries are

| Boundary | Why | Status |
|---|---|---|
| No 4096-word code corrects every 4-bit corruption | \(4096\cdot V(24,4) > 2^{24}\) | [Lean] |
| At most 1/6 of 4-bit corruptions resolvable once all 3-bit ones are | \(10626 = 6\cdot1771\) | [Lean] |
| Negative space \(\ge 4096\cdot1771\) words | volume | [Lean] |
| Mirror below 4 labels | average list \(12951/4096 > 3\) | impossible [Lean] |
| Mirror at 5 labels | `mirror5Code` | possible [Lean], but ambiguous below 4 flips for every such design [Lean] |
| Mirror at 4 labels | pair- and triple-level LP/SDP relaxations are feasible [Exp] | **open** |
| Mirror at 5 labels with minimum distance \(\ge6\) | impossible at distance \(\ge8\) [Lean] and for the whole Golay-extension family [Lean] | **open in general** |
| Golay sender tag | Plotkin bound on distance-12 classes | 86 to 128 labels [Lean] |
| Any sender tag | Delsarte bound \(A(24,9)\le551\), with an integer certificate | \(\ge 8\) labels [Lean] |
| Free soft resolution, worst case | midpoint of two codewords at distance 8 | radius 8, sharp [Lean] |
| Quantum carrier (5 qubits) | \(\sum_i P(\text{correct}\mid i) \le \dim = 32\) | \(\le 1/128\) per GLM symbol [Lean] |
| Outside the theorem | soft information, longer blocks, other rates, skewed priors, bursty noise, byte symbols | Golay's optimality theorem does not apply. Longer codes (LDPC, polar, concatenated) win asymptotically; Golay's value is exactness, small size and the sextet interface |

---

## 7. The recommended protocol: triggered sextet mirror with soft resolution

### 7.1 Receiver

For each received 24-bit symbol (soft vector \(r\in\mathbb R^{24}\) if available, otherwise the
hard word \(y\)):

1. **Decode** \(y\) (the hard decision of \(r\)) with the Golay syndrome decoder.
2. **Trigger off** (coset leader of weight \(\le3\)): accept. This is never wrong for \(\le3\)
   flips (`golay_corrects_weight_le3`, `golayTrigger_off_le3`).
3. **Trigger on**: the receiver knows the sextet and the six candidates.
   1. If soft values exist, take the **least reliable tetrad**: flip the 4-set with the smallest
      \(\sum_{j\in t}|r_j|\). This is the nearest candidate (`sqDist_flip_tetrad`).
   2. Accept it for free if \(\lVert r - \pm1(\hat c)\rVert^2 < 8\). The answer is then
      certainly the nearest codeword (`soft_certificate`).
   3. Otherwise accept it for free if its posterior is \(\ge 1-\varepsilon\), given a noise
      estimate \(\sigma\). Silent errors are then at most a fraction \(\varepsilon\) of the
      accepted answers (`posterior_gate_silent_error_le`).
   4. Otherwise **ask for a label**:
      * a corruption-aware label: 6 values (3 bits) for full resolution, or \(K\) values for a
        list of at most \(\lceil6/K\rceil\) that always contains the truth
        (`golay_triggered_list_mirror`; optimal by `golay_triggered_list_lower`);
      * batched over \(m\) events: exactly \(6^m\) joint values, approaching
        \(\log_2 6\approx2.585\) bits per event (5 events in 13 bits;
        `golay_batch_labels_suffice`, `golay_batch_labels_lower`);
      * from the sender, who does not know the error: the 7-bit tag `golayTag`
        (`golay_on_demand`). No 4096-word design could do this with fewer than 8 values.
4. Pass any remaining short lists (for example the 2-candidate lists of a 2-bit label) to the
   next GLM layer as erasure-like information.

### 7.2 Cost of clarification per ambiguous event

| Option | Bits | Result | Proved |
|---|---|---|---|
| soft certificate or posterior gate | 0 | single answer (gate: error \(\le\varepsilon\) of accepted cases) | [Lean] guarantees; [Exp] acceptance rate |
| corruption-aware label, 6 values | 3 | single answer, never wrong for \(\le4\) flips | [Lean] |
| corruption-aware label, 4 values | 2 | list of \(\le2\) containing the truth | [Lean] |
| corruption-aware label, 2 values | 1 | list of \(\le3\) containing the truth | [Lean] |
| batched labels | \(\to 2.585\) | single answer | [Lean] |
| sender tag | 7 | single answer, never wrong for \(\le4\) flips | [Lean] |

The probability that a symbol needs the mirror at all is \(10626\,p^4(1-p)^{20}\) for Golay
(`golay_consultProb` [Lean]). In the AWGN simulation [Exp], the posterior gate with
\(\varepsilon=10^{-2}\) cut label requests by 59 % at 3 dB, 82 % at 4 dB, 95 % at 5 dB and 99 % at
6 dB, with no measurable change in symbol error.

### 7.3 What the GLM front end must supply

* Hard bits only: the protocol works as specified, with label costs as in §7.2.
* Per-position reliabilities (\(|r_j|\) or flip probabilities \(p_j\)): enables free ranking of
  the six candidates (`posLik_le_iff` covers the per-position flip-probability form).
* A noise estimate \(\sigma\): enables the posterior gate. Without it, the certificate
  (radius 8) is still a valid but conservative gate.
* If the front end can afford it, full soft maximum-likelihood decoding over the 4096 codewords
  (or a Leech-lattice decoder) gives the largest measured improvement [Exp].

### 7.4 Reference implementation

`glm_substrate.py` implements every step above:

| Step | Function |
|---|---|
| encode / syndrome / decode + trigger | `encode`, `syndrome`, `hard_decode` |
| sextet and candidates | `sextet`, `candidates` |
| corruption-aware labels and lists | `mirror_label`, `list_label`, `resolve_with_label` |
| batching | `batch_labels`, `unbatch_labels`, `batch_bits` |
| sender tag | `tag`, `resolve_with_tag` |
| soft resolution | `least_reliable_tetrad`, `certified`, `posterior` |
| complete receiver | `receive_soft` (returns `clean`, `certified`, `gated` or `ask`) |

It uses the same generator (\(g(x)=x^{11}+x^9+x^7+x^6+x^5+x+1\) with an overall parity bit),
the same coset-leader order and the same tag masks as the Lean files, so the proved
statements are about the very objects it computes. Checksums of the coset-leader table and
of the codeword list agree with the same checksums evaluated on the Lean definitions. The implementation itself is **[Impl]**:
`test_glm_substrate.py` checks it against the proved facts. For example, it exhaustively checks
the weight enumerator, the leader census \(1, 24, 276, 2024, 1771\), all 1771 sextets, every
corruption of weight \(\le4\) on sample codewords, the octad condition behind the tag, and the
soft certificate example. Bit-ordering conventions are in the module docstring. Remap them if
the GLM orders coordinates differently.

---

## 8. Open problems (precisely stated)

1. **Four-label mirror.** Is there a set of 4096 words in \(\mathbb F_2^{24}\) such that every
   Hamming ball of radius 4 contains at most 4 of them? (Equivalently for linear codes: every
   coset has at most 4 words of weight \(\le4\).) Known: 5 is achievable, 3 is impossible.
   Relaxations using pairs and triples of codewords cannot decide it [Exp], so a proof would
   need four-point constraints or a large structured search.
2. **Five labels at distance \(\ge6\).** The same with "at most 5", and minimum distance
   \(\ge6\). Known: impossible at distance \(\ge8\), and impossible for all 4096 Golay
   extensions. All searches stop at 6 [Exp].
3. **Exact sender-tag cost for Golay**, somewhere in 86–128 labels. Also: can any design get
   below 86? The proved floor is 8.

None of these affects the recommendation. Even a 4-label design would have to be ambiguous
below 4 flips (`cheap_mirror_forces_early_ambiguity`). Batching on Golay already gets to
2.585 bits per event, and soft resolution removes most label traffic.

---

## 9. Corrections to the source material

| Where | Was | Corrected |
|---|---|---|
| `DesignSpec_v1.pdf` §4 | \(\lvert M_{24}\rvert = 311{,}351{,}040\) | \(244{,}823{,}040 = 2^{10}\cdot3^3\cdot5\cdot7\cdot11\cdot23\). Drop-in text in `../reports/DesignSpec_v1-section4-corrected.md`. Claim (i), that the cyclic shift preserves \(G_{24}\), is proved (`golayRho_image`) |
| `Void-Complex_Protocol_v1.1.md` line 91, `census23/Void-Complex_Protocol_v1.2.md` line 95 | same figure | fixed in place (logged in `../reports/REORGANISATION-LOG.md`) |
| `DesignSpec_v1.pdf`, "no [FORMAL] claim is made" | — | O1–O4 and the \(S(5,8,24)\) claim are now formal (see `THEOREMS.md`) |
| `DesignSpec_v1.pdf` O4, "3 bits, optimal" | — | correct for corruption-aware labels only. A sender tag needs at least 86 labels for Golay (7 bits suffice) |
| `golay_leech_certify.py`, 196,560 by appeal to uniqueness | — | now proved directly by classification (`mem_leechMinimal_iff`, `leech_kissing`) |

---

## 10. Verifying

```
lake build                                  # all Lean files; a few minutes (native_decide checks)
cd glm_package && python3 test_glm_substrate.py
```

No Lean file contains `sorry`. The Lean files add no axioms. As noted in §0, `native_decide`
proofs also trust Lean's compiler.

Published results quoted, not formalised: the kissing-number bound in 24 dimensions
(Levenshtein; Odlyzko–Sloane), optimality of the Leech packing (Cohn–Kumar–Miller–Radchenko–
Viazovska), mutually unbiased bases in prime-power dimension (Wootters–Fields), the
spherical 11-design property of the Leech minimal vectors, the Bures-fidelity formula, the
classification of perfect codes (Tietäväinen; van Lint), and the order of \(M_{24}\).

---

## 11. Where the history lives

| Path | Content |
|---|---|
| `../reports/01`–`05` | the five phase reports (optimality; design attempts; five-label mirror; trigger; HPSKL and soft resolution). Superseded by this document where they differ |
| `../reports/SOURCE-MATERIAL-AUDIT.md` | audit of the uploaded Designed-Dimensions material |
| `../reports/REORGANISATION-LOG.md` | every file move and edit made to the source material |
| `../experiments/` | the exploratory scripts and logs behind every [Exp] figure (index in `../experiments/README.md`) |
| `../source_material/` | the original Designed-Dimensions material, as uploaded (with the two one-line fixes above) |
