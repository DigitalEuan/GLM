#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  THE GEOMETRIC LANGUAGE MACHINE (GLM)
  A substrate-native codec and exact reasoner for dimensional knowledge, on
  the extended binary Golay code [24,12,8] and the Leech lattice
================================================================================

  Author   : E. R. A. Craig (DigitalEuan), Auckland, New Zealand
  Version  : 20.0 (consolidated edition)
  Status   : operational paper — this file is both the write-up and the
             executable verification of every claim it makes
  Licence  : open, for research, verification and educational use
  Companion: glm_reasoner.py  (the implementation you call)
  Run      : python3 glm_paper.py            (full verification, ~15 s,
                                             43 numbered claims)
             python3 glm_paper.py --quick    (skips the exhaustive sweeps)

--------------------------------------------------------------------------------
  ABSTRACT
--------------------------------------------------------------------------------

  The Geometric Language Machine encodes dimensional knowledge — physical
  quantities, the equations relating them, and the derivations that connect
  them — into a 24-bit discrete substrate built on the extended binary Golay
  code, and reasons about that knowledge exactly in the free abelian group
  (Z^7, +) of SI dimension exponents.

  The main design decision of this edition is which object is primary:

    0.  MEANING IS THE STATE; THE BITS ARE A VIEW.  A concept IS its exponent
        vector d in (Z^7, +).  The 24-bit word is derived from it, word(d) =
        encode(d), recomputed on demand, never stored as independent state,
        never settable and never composed.  Earlier versions of this work had
        it the other way round — a bit pattern as the object with an integer
        vector carried alongside as a companion — and Section 5 retires that
        arrangement, with Claims C42 and C43 checking the invariant.

    1.  A LOSSLESS CODEC.  The derivation is injective with a total inverse:
        the exponents of length, mass, time, current, temperature, amount of
        substance and luminous intensity are packed into a 24-bit word and
        projected through the 4x6 Miracle Octad Generator onto six GF(4)
        hexacode symbols plus six Z_4 fibre keys.  Every step is a bijection,
        so the round trip d -> bits -> shadow -> bits -> d has zero loss.  The
        Golay code then supplies a decoder ("snap"), a syndrome, a notion of
        lawfulness, and an honest account of where correction is ambiguous.

    2.  AN EXACT REASONER.  Composition of quantities is addition in (Z^7, +).
        Equation checking is integer equality; target synthesis is an integer
        linear system solved by Smith normal form; dimensionless-group
        analysis is the kernel of the same matrix.  Nothing is approximate and
        nothing is heuristic: the answers are decisions, not scores.

  The negative result that forces this order is the MOD-2 CEILING: any
  composition rule that is F_2-linear — XOR of bit patterns being the
  canonical case — can only compare exponents modulo 2, so it cannot
  distinguish E = m c^2 from E = m c^4, and indeed no such encoder is
  injective at all.  A bit pattern therefore cannot be the thing that carries
  meaning.  Section 5 states and proves this and measures it: over the
  90-quantity library shipped here, 101 of the 2,346 distinct dimension pairs
  are indistinguishable mod 2, while the exact group separates all of them.
  Those measurements live in an appendix; nothing on the decision path
  computes anything modulo 2.

  This edition also revisits earlier GLM results.  Two are corrected: the
  four-tier "ontological" encoder used up to v17 was many-to-one (so its
  reported zero-bit reconstruction described the feature bits, not the
  concept), and the "snap-based Griess product" is shown to collapse to
  v . w = snap(v) XOR snap(w), which is associative — not the commutative
  non-associative algebra it was described as.  One is kept and strengthened:
  the faithful 4096-dimensional Schrodinger representation of the
  extraspecial group 2^(1+24), where the commutator [x_i, y_i] = z is
  verified as an exact operator identity, in contrast to the 24-dimensional
  action, where it is checked here and shown to fail.

  Section 8.1 closes a gap every archive version left open: the Mathieu group
  M24 is constructed here rather than invoked.  An exact search over the code's
  column matroid produces automorphisms; a Schreier-Sims stabiliser chain gives
  a 5-transitive group of order 244,823,040; and an exhaustive enumeration of
  the automorphisms fixing five coordinates (there are 48) shows by
  orbit-stabiliser that this group is all of Aut(C).

  Sections 9 and 10 consolidate the rest of the development that followed
  those early versions - versors and quaternionic fibres, winding and
  holonomy, the conformal grading, the Leech line census, the 196,884 ledger
  and the semidirect product 2^(1+24):S_12 - keeping what is exactly
  computable and naming what is not.  Four further corrections come out of
  that pass: the archive's conformal weight is half the syndrome weight, its
  "Leech inner product" is the Hamming distance rescaled, its Monster
  conjugacy classes are a relabelling of the same syndrome, and the outer
  factor of its semidirect product is S_12 rather than Co_1.  Section 11 and
  DEVELOPMENT_CATALOG.md track every version of the system and where each of
  its ideas ended up.

--------------------------------------------------------------------------------
  0.  HOW TO READ AND RUN THIS
--------------------------------------------------------------------------------

  The GLM is a small stack of modules, each self-auditing:

      glm_substrate.py   Golay code, hexacode, MOG alignment, Leech metrics
      glm_codec.py       column bijection, 24-bit codec, dimension carrier
      glm_metrology.py   (Z^7,+), the quantity library, the parser, auditing
      glm_linalg.py      exact integer linear algebra (Smith normal form)
      glm_reasoner.py    THE COMPANION IMPLEMENTATION: concepts, audit,
                         target synthesis, Buckingham-Pi, geometry telemetry,
                         scene export, CLI
      glm_geometry.py    optional: versors, quaternionic fibres, winding,
                         holonomy, grading, vacua, colour (Section 9)
      glm_moonshine.py   optional: the Leech line census, the 196,884 ledger,
                         the Jordan layer (Section 10)
      glm_m24.py         optional: the automorphism search, Schreier-Sims
                         stabiliser chains, and Aut(C) = M24 (Section 8.1)
      glm_monster.py     optional: automorphism membership, 2^(1+24) and its
                         4096D action, 2^(1+24):S_12, the snap algebra
                         (Sections 8, 10.6)
      test_glm.py        the test-suite (unittest)

  Two companion documents sit beside them: README.md (the file map and how to
  run everything) and DEVELOPMENT_CATALOG.md (a version-by-version reading of
  the nineteen archived iterations and where each of their ideas ended up).

  Each module runs standalone (`python3 glm_codec.py` etc.) and prints its own
  audit.  This file runs all of them, checks the numbered claims of the paper
  one by one, and writes results/glm_results.json.

  Reading order for a newcomer: this docstring, then glm_reasoner.py, then
  whichever module the reasoner pulled you into.

--------------------------------------------------------------------------------
  1.  THE PROBLEM
--------------------------------------------------------------------------------

  A knowledge representation for physical reasoning has to do three things at
  once: hold structured concepts compactly, compose them, and refuse
  nonsense.  Bit-vector substrates are excellent at the first, natural at the
  second (XOR), and catastrophic at the third.

  The failure mode is precise.  Encode a quantity by a bit pattern and compose
  by XOR.  Then composition is addition in F_2, so the exponent of each base
  dimension is tracked modulo 2.  Since 2 and 4 are congruent mod 2, the
  encoder cannot separate c^2 from c^4, and a checker built on it accepts
  E = m c^4.  No amount of error correction repairs this: it is a property of
  the arithmetic, not of the code (Section 5, Proposition 1).

  The GLM's response is to choose which of the two is the object and which is
  the view, and to choose the only way round that can work:

      MEANING   lives in (Z^7, +)   — the concept itself; exact; composed;
                                     decides acceptance
      CARRIER   lives in F_2^24     — DERIVED from the meaning by an injective
                                     encoder; geometric; gives locality,
                                     repair, symmetry and colour

  The carrier is a function of the meaning, recomputed on demand, never stored
  as independent state and never composed.  The reverse arrangement — bits as
  the object, integers carried alongside as a companion — is not available:
  Proposition 1 of Section 5.3 shows that no XOR-composing encoder of (Z^7,+)
  is even injective, so a bit pattern cannot be the thing that means something.
  Section 5.2 states the architecture and Claims C42 and C43 check it.

--------------------------------------------------------------------------------
  2.  THE SUBSTRATE
--------------------------------------------------------------------------------

  2.1  The extended binary Golay code

    C is the [24, 12, 8] binary code generated by G = [I_12 | B] with the
    symmetric block B given in glm_substrate.py.  Established by execution in
    `GolayCode.census()`:

        |C| = 4096                      2^12 codewords
        d(C) = 8                        minimum weight of a nonzero codeword
        C = C^perp                      self-dual: G G^T = 0 (mod 2)
        every weight is 0 mod 4         doubly even
        W(z) = 1 + 759 z^8 + 2576 z^12 + 759 z^16 + z^24
        759 octads                      the blocks of the Steiner system S(5,8,24)
        packing radius t = 3            all patterns of weight <= 3 correctable
        covering radius rho = 4         every word is within distance 4 of C

    The coset-leader profile over the 4096 cosets is
        weight 0: 1,  1: 24,  2: 276,  3: 2024,  4: 1771     (total 4096)
    and each of the 1771 weight-4 cosets has exactly SIX minimum-weight
    leaders.  Correction at distance 4 is therefore a genuine six-way tie; the
    decoder here breaks it by a stated convention (lexicographically first
    leader) and reports the tie count rather than hiding it.

    This matters for the GLM's semantics: a concept whose carrier sits at
    distance 4 from the code has no canonical repair.  We label it "ambiguous"
    and say so, rather than pretending the substrate has an opinion.

  2.2  The hexacode and the MOG

    Arrange the 24 coordinates in a 4x6 grid.  Each column b in F_2^4 gets a
    GF(4) label, the sum of the labels (0, 1, w, w^2) of the rows it occupies.
    The label map is F_2-linear and surjective, and its kernel has order 4, so
    each of the four GF(4) symbols has exactly four columns above it.

    Under the bit alignment `MOG.ALIGNED_BITS` — which is specific to this
    generator matrix — the six labels of any Golay codeword form a word of the
    hexacode H6, the [6, 3, 4] code over GF(4) with 64 words.  This is checked
    exhaustively: 0 failures out of 4096 codewords (Claim C7).

    The GLM also uses a second, plain gridding (row r = coordinates 6r..6r+5)
    for the four "ontological tiers".  It is a relabelling, the codec is
    bijective under it too, but its labels are NOT hexacode words, and the
    paper never claims otherwise.  Conflating the two griddings was a latent
    error in earlier versions of this work.

  2.3  The Leech lattice

    In the x sqrt(8) integer representation, the minimal vectors of Lambda_24
    have norm^2 = 32 and fall into three shape classes, all enumerated and
    checked here (Claim C9):

        A   (+-4, +-4, 0^22)             1,104   glue: sum = 0 mod 8
        B   (+-2^8, 0^16) on octads     97,152   glue: sum = 0 mod 8
        C   (+-3, +-1^23) Golay-driven  98,304   glue: sum = 4 mod 8
        total                          196,560   = the kissing number

    Class B is where the Golay code enters (one octad per support), class C
    uses every codeword.  The GLM uses the lattice for its metric intuition
    and for the cost layer of Section 7; no reasoning decision depends on it.

--------------------------------------------------------------------------------
  3.  THE CODEC
--------------------------------------------------------------------------------

  3.1  The column bijection

    A 4-bit column carries (label, fibre): its GF(4) label, and its rank among
    the four columns sharing that label.  Since |F_2^4| = 16 = |GF(4) x Z_4|
    and the fibres have size exactly 4, the map

        b  <->  (label(b), fibre(b))

    is a bijection, verified over all 16 states (Claim C10).  Applying it to
    the six columns gives the 24-bit codec

        F_2^24  <->  GF(4)^6 x Z_4^6,

    "six hexacode symbols plus six fibre keys", with zero reconstruction
    error.  Bijectivity of the 24-bit map follows from the column map acting
    independently on the six columns; the round trip is also measured
    directly on 20,000 pseudo-random words in both griddings (Claim C11).

  3.2  The dimension carrier  (a correction to earlier versions)

    Up to v17 the GLM encoded a dimension vector into 24 bits by four
    six-bit "tiers": Reality (which exponents are nonzero), Information (their
    parities), Activation (which exceed 1 in absolute value), Potential (which
    are negative).  That map is many-to-one — d = (2,1,-2,0,0,0,0) and
    (4,1,-4,0,0,0,0) share all four tiers — and the published code also
    skipped the amount-of-substance exponent through an indexing slip
    (`range(5)` plus index 6).  Its reported "0-bit reconstruction error" was
    therefore a statement about the feature bits, not about the concept: the
    bits came back, the physics did not.

    This edition replaces it with a bijection.  Exponents are restricted to
    the box [-4, 4]^7 — which covers the SI quantities in the library,
    including T^4 in capacitance and Theta^-4 in the Stefan-Boltzmann
    constant — zigzag coded (0, 1, -1, 2, -2, ... -> 0..8) and packed as a
    base-9 integer:

        9^7 = 4,782,969  <  16,777,216 = 2^24.

    Consequences:
      * the chain d -> carrier -> MOG shadow -> carrier -> d is exact
        (Claim C12: all 90 library quantities, 0 bits lost);
      * the dimensionless vector maps to the all-zero word, which is the zero
        codeword: "dimensionless is the vacuum" is now a fact about the
        encoding rather than a slogan;
      * the four tiers survive as an interpretive VIEW (`ontological_profile`),
        which is how they were actually used.

    Honest note: the packing is arithmetic, not code-theoretic.  It makes the
    codec lossless; it does not make the bit pattern physically meaningful.
    Where the bits do acquire meaning is the lawfulness census below, and it
    is a statement about the encoding, not about nature.

  3.3  Lawfulness

    Sweeping all 4,782,969 representable dimension vectors and testing which
    carriers are Golay codewords gives 1,168 lawful vectors (Claim C13),
    distributed by carrier weight as
        weight 0: 1,  weight 8: 390,  weight 12: 696,  weight 16: 81,
    which is the Golay weight enumerator restricted to the carrier's image.
    The dimensionless vector is the unique weight-0 case.  Of the named
    quantities in the library, exactly the dimensionless ones are lawful; all
    others sit at snap distance 1 to 4 from the code.

--------------------------------------------------------------------------------
  4.  SNAP: SYNDROME, REPAIR, AMBIGUITY
--------------------------------------------------------------------------------

  For v in F_2^24 the syndrome is sigma(v) = H v (mod 2), a 12-bit vector, and
  snap(v) = v XOR L(sigma(v)) where L is the coset-leader table.  The decoder
  reports four numbers, all exact:

      syndrome        which coset the word is in (0 iff v is a codeword)
      syndrome weight the weight of the 12-bit syndrome (0..12)
      distance        how far snap moved the word (= leader weight, 0..4)
      tie count       how many codewords were equally near (1, or 6 at d = 4)

  Distance, not syndrome weight, is the geometric quantity: earlier write-ups
  sometimes used "|sigma| <= 4" as though the syndrome weight were bounded by
  the covering radius.  It is not — the syndrome is a 12-bit object and its
  weight regularly exceeds 4 — while the coset-leader weight is bounded by 4,
  and that is the covering-radius statement (Claim C5, C6).

  Interpretation, stated as interpretation: a nonzero syndrome is the
  "history" a concept carries relative to the code; snapping resolves it.
  Nothing in the reasoner uses this reading, and no acceptance decision
  depends on the substrate.

--------------------------------------------------------------------------------
  5.  MEANING IS PRIMARY; THE CARRIER IS DERIVED
--------------------------------------------------------------------------------

  5.1  The group

    A quantity's dimension is a vector in Z^7 over the SI base dimensions
    (L, M, T, I, Theta, N, J).  Composition is a homomorphism:

        dim(A B)   = dim(A) + dim(B)
        dim(A / B) = dim(A) - dim(B)
        dim(A^n)   = n dim(A)

    An equation is dimensionally admissible exactly when the two sides have
    equal vectors.  This is classical dimensional analysis (Buckingham, 1914).

    That vector is the concept.  It is the whole state of the system: what is
    stored, what is composed, what is compared, and what every verdict is
    computed from.  Nothing else in the GLM is state.

  5.2  The derivation

    The 24-bit carrier word is a FUNCTION of the meaning,

        word : [-4,4]^7 -> F_2^24,      word(d) = encode(d)      (Section 3.2)

    injective, with a total inverse on its image: decode(word(d)) = d.  It is
    recomputed from the meaning on demand and cached, never stored as
    independent state and never settable; `Concept` in `glm_reasoner.py` is a
    frozen record whose only field of substance is `dim`, and `carrier`,
    `shadow`, `snap`, `lawful`, `tax` and `nrci` are read-only views derived
    from it.  A concept therefore cannot hold bits that disagree with its
    meaning, because it is never handed bits at all.  Claim C42 checks the
    invariant on every concept in the library, on the whole image of the
    encoder, and on meanings outside the representable box, where the honest
    answer is that there are no bits rather than a truncated word.

    The dependence runs one way and only one way:

        meaning  --encode-->  bits  --decode-->  meaning.

    Consequences that the rest of the system relies on:

      (a) two concepts with the same meaning have the same bits, and distinct
          meanings have distinct bits (injectivity, Claim C42);

      (b) composition never touches the carrier.  A product of quantities is
          computed as d1 + d2 in Z^7 and its word is derived afterwards.  It
          has to be done that way: the derived word map is *not* additive, and
          Claim C43 exhibits the failure on the library rather than asserting
          it — for the great majority of pairs, word(d1 + d2) is not word(d1)
          XOR word(d2), nor any other F_2-linear combination, and Section 5.3
          says why no encoder can do better;

      (c) the carrier is read, never written.  Snap telemetry, the MOG shadow,
          colour, the fibre geometry of Section 9 and the M24 orbit of
          Section 8.1 are all views of the derived word.  None of them feeds
          back into a meaning, and no verdict consults them (invariant I7).

    Earlier versions of this work had the arrow the other way round: a bit
    pattern was the object, and an integer exponent vector was carried
    alongside it as a companion to repair what the bits could not express.
    That is the design this section retires.  A companion is a second source
    of truth; here there is one source of truth and one derived view of it.

  5.3  Proposition 1 (why the arrow points this way)

    Let e : Z^7 -> F_2^n be any map used as an encoder, and suppose
    composition is realised by XOR, i.e. e(d1 + d2) = e(d1) XOR e(d2).  Then e
    is a homomorphism of abelian groups into an elementary abelian 2-group, so
    2 Z^7 lies in its kernel: e(d) = e(d + 2u) for every u in Z^7.  Hence any
    checker built from e accepts d1 = d2 whenever d1 = d2 (mod 2).

    Corollary 1 (no primary bit pattern).  No such e is injective: 2u is a
    nonzero element of its kernel for every u != 0.  A bit pattern composed by
    XOR cannot be the object that carries meaning, however wide the word and
    however good the error correction, because it identifies concepts that
    differ.  That is the theorem behind Section 5.2: meaning must be primary
    and the bits derived, since the reverse arrow does not exist.

    Corollary 2 (the named traps).  E = m c^2 and E = m c^4 are
    indistinguishable under any such encoder, since (2,1,-2) and (4,1,-4)
    differ by 2(1,0,-1).  The same holds for F = m a^3, for illuminance vs.
    flux times area, and for the Stefan-Boltzmann law with Theta^2 in place of
    Theta^4.  Claim C14 checks the corollary directly.

    Both corollaries are about the rejected design, not about the GLM: the
    system as shipped does not compose bits at all, and no decision anywhere
    in it is taken modulo 2.  The measurements in 5.4 exist so that the reason
    for the architecture stays reproducible; they are quarantined in an
    appendix (`glm_metrology.py` Section 6, and the reasoner's
    `mod2_ceiling_batch`) and nothing on the decision path can reach them.

  5.4  Measurement rather than assertion

    Earlier versions quoted "100% precision vs 89% for the mod-2 substrate"
    over 6,793 equation pairs, without a reproducible definition of the
    denominator.  Here is a definition and its measurement (Claim C15).  Take
    the 69 distinct dimension vectors of the shipped library and all 2,346
    unordered pairs of them.  Each pair is an equation that is dimensionally
    false.  A mod-2 checker accepts 101 of them (4.3%); the exact group
    accepts none.  On the 26 curated equations of the demonstration suite
    (physics and adversarial traps mixed), the GLM accepts every true one and
    rejects every false one, four of which a mod-2 checker would have
    accepted.

    Two further measurements give the ceiling a denominator that does not
    depend on which quantities happen to be in the library.

      (a) The perturbation family (Claim C23).  For each of the 90 quantities
          q, each of the 7 exponent slots i and each sign, form the false
          equation q = q * (base_i)^(+-2).  That is 90 * 7 * 2 = 1,260
          equations, every one of them dimensionally false.  A mod-2 checker
          accepts 1,260 of 1,260 (100%, as Proposition 1 forces); the exact
          group accepts 0.  96 of the 1,260 are traps a user could actually
          write, in that the perturbed dimension is itself a named library
          quantity (E = m c^4 is of this kind).

      (b) The whole exponent box (Claim C24).  Over B = [-2,2]^7, which holds
          78,125 vectors and 3,051,718,750 unordered pairs, exactly
          31,335,196 pairs (1.03%) share a mod-2 shadow and are therefore
          confusable by any F_2-linear checker; (Z^7,+) confuses none.  The
          count is obtained in closed form from the per-coordinate parity
          counts, not by enumeration.

  5.5  A machine-checked companion

    Proposition 1 and its corollaries are proved, not just argued, in
    `RequestProject/GLM.lean` (Lean 4 with Mathlib), which contains:

      GLM.xor_blind                      f (d + 2u) = f d for any additive f
                                         into a group of exponent 2
      GLM.no_injective_additive_into_char_two,
      GLM.f2_carrier_cannot_be_primary   Corollary 1: no XOR-composing encoder
                                         of (Z^7,+) is injective, in particular
                                         none into F_2^24 -- so the bits cannot
                                         be the primary object
      GLM.mc4_eq, GLM.mc4_ne             m c^4 differs from energy by 2(1,0,-1)
                                         yet is not equal to it in Z^7
      GLM.mc4_indistinguishable_under_xor  Corollary 2: every XOR encoder
                                         accepts E = m c^4
      GLM.xor_universal_kernel           two dimensions are confusable by some
                                         XOR encoder iff they agree mod 2 --
                                         the ceiling is exactly a mod-2 effect
      GLM.carrier_card, carrier_fits_24_bits, carrier_embeds
                                         9^7 = 4,782,969 < 2^24, with the
                                         embedding exhibited
      GLM.zigzag_lt_nine, zigzag_injOn   the carrier's digit map is injective
                                         on [-4,4] and lands in {0..8}, which
                                         is what makes the derived word a
                                         faithful view of the meaning
      GLM.colLabel_table, colLabel_xor, fibre_card, fibres_partition
                                         the column label map is F_2-linear
                                         and exactly 4-to-1 on the 16 states
      GLM.winding_integral,              Proposition 2 of section 9.3: on a
      GLM.winding_integral_liftStep      closed walk the lifted Z_4 steps sum
                                         to a multiple of 4, for an arbitrary
                                         lift and for the concrete {-1,0,1,2}
                                         lift used by glm_geometry.py
      GLM.shift_sign_comm,               the Schrodinger relations of section
      GLM.shift_sign_anticomm,           8.2: X_b Y_a = (-1)^<a,b> Y_a X_b,
      GLM.shift_sign_comm_off_diag       anticommuting exactly on the diagonal
                                         (the extraspecial commutator)
      GLM.mathieu_order_arithmetic       the orbit-stabiliser arithmetic of
                                         section 8.1: 24 x 23 x 22 x 21 x 20 x
                                         48 = 759 x 322,560 = 244,823,040
      GLM.dimension_ledger               the arithmetic of section 10

    These are the statements that are theorems; the rest of the paper's
    claims are finite verifications and are checked by running this file.

    What this does NOT say: dimensional homogeneity is necessary, not
    sufficient, for physical truth.  E = m c^2 and E = 1000 m c^2 are equally
    acceptable here, as are energy and torque, which share a dimension vector.
    The library reports such collisions explicitly (12 groups of them) rather
    than pretending to break them.

--------------------------------------------------------------------------------
  6.  REASONING
--------------------------------------------------------------------------------

  6.1  Equation audit

    `GeometricReasoner.audit(lhs, rhs)` parses both sides with a small
    recursive-descent parser (products, quotients, integer powers,
    parentheses, numeric prefactors treated as dimensionless), compares the
    exponent vectors exactly, and additionally reports what a mod-2 substrate
    would have concluded — so the ceiling is visible in every audit rather
    than being an anecdote about E = m c^4.

  6.2  Target synthesis

    Given inputs q_1..q_k and a target t, we solve

        A x = dim(t),     A = [dim(q_1) ... dim(q_k)]  (7 x k over Z)

    exactly.  The Smith normal form U A V = D gives a particular integer
    solution when one exists, plus an integer basis of ker A; the reasoner
    then searches small combinations of the kernel basis for the simplest
    representative (least total |exponent|).  If no integer solution exists we
    solve over Q and report fractional powers: speed from (energy, mass) is
    returned as speed = energy^(1/2) / mass^(1/2), i.e. v = sqrt(E/m), and it
    is labelled as rational rather than integer.  If the target is outside the
    span, the reasoner says so instead of guessing — temperature cannot be
    built from energy and mass.

    This replaces the earlier hand-written pattern list (try A*B, then A/B,
    then B/A, then A*B^2), which could only find the shapes it had been told
    about.

  6.3  Buckingham-Pi

    ker A is exactly the set of dimensionless groups of the inputs, so the
    same machinery does Pi analysis: `pi_groups` returns an integer basis, and
    checks the Pi theorem count n - rank(A) as an assertion about its own
    output (Claim C17).  For (force, density, speed, length) it returns the
    drag-coefficient group; for (speed, length, kinematic viscosity) it
    returns the reciprocal Reynolds number.

--------------------------------------------------------------------------------
  7.  THE COST LAYER  (stipulative, separable)
--------------------------------------------------------------------------------

  Two quantities travel with every carrier word, inherited from the UBP
  working notes that this line of work grew out of:

      Y      = 1 / (pi + 2/pi)          ~ 0.2646754
      TAX(v) = HW(v) * Y + ||v||^2 / 8
      NRCI(v) = 10 / (10 + TAX(v))

  They are computed as exact rationals (pi from a truncated continued
  fraction, so the value is reproducible to the digit).  They are a MODELLING
  CHOICE, not a theorem, and no decision in the codec, the decoder or the
  reasoner reads them.  Deleting Section 7 would not change a single verdict
  in Sections 3 to 6.  They are kept because they give a cheap, monotone
  "weight of a concept" for ranking and display, and because continuity with
  the earlier versions is useful.

--------------------------------------------------------------------------------
  8.  UPPER TIERS  (optional)
--------------------------------------------------------------------------------

  8.1  Code automorphisms: M24, constructed

    Every archive version from v10 on names M24 and none of them builds it;
    what they build is a membership test.  We keep the test -- does a
    permutation map all 4096 codewords into C?  Under it the message/parity
    half-swap is an automorphism of this systematic code and the naive
    coordinate transposition is not (Claim C18) -- and then we build the
    group, in `glm_m24.py`.

    The search rests on one observation.  Fix a basis b_1..b_12 of C and let
    col(j) in F_2^12 be the column (b_i[j])_i.  A set S of coordinates carries
    a linear dependency of columns exactly when S is the support of a
    codeword, because C is self-dual; so a coordinate permutation preserves C
    if and only if it preserves every dependency among the columns.  That test
    is incremental: reduce the domain column and the candidate image column
    through the same echelon, and a partial map either forces the next image
    or is already impossible.  Twelve 12-bit words replace 4096 membership
    tests, and the whole search runs in under a second.

    Four automorphisms found this way generate a group G.  Its stabiliser
    chain (Schreier-Sims, exact) has base 0,1,2,3,4,5,6 with orbit lengths
    24, 23, 22, 21, 20, 16, 3 -- so G is 5-transitive -- and

        |G| = 24 x 23 x 22 x 21 x 20 x 48 = 244,823,040.

    G is also transitive on the 759 octads, the 2576 dodecads and the 1771
    sextets, so orbit-stabiliser reads the orders of the three classical
    maximal subgroups straight off the measured orbits: the octad stabiliser
    2^4:A_8 of order 322,560, the dodecad stabiliser M_12 of order 95,040, and
    the sextet stabiliser 2^6:3.S_6 of order 138,240 (Claims C37 and C41).
    M_12, the other Mathieu group the archive kept mentioning, is thus also
    accounted for -- as an order forced by an orbit, not as a construction.

    That G is the *whole* automorphism group is then a second computation, not
    a citation: the search enumerates exhaustively every automorphism fixing
    the five coordinates 0,1,2,3,4, and finds exactly 48, all of them already
    in G.  Since the G-orbit of an ordered 5-tuple is already every ordered
    5-tuple, orbit-stabiliser gives |Aut(C)| = 24 x 23 x 22 x 21 x 20 x 48 =
    |G|, hence Aut(C) = G = M24 (Claim C38).  Nothing about M24 is assumed;
    the order that agrees with the literature comes out of the chain.

    Claim C39 checks the chain as software: membership testing by sifting
    agrees with the exhaustive codeword test on generated elements and on
    non-members, and the transversals reconstruct group elements exactly.

    What the group means for the reasoner is Claim C40, and it is a negative
    as much as a positive.  M24 permutes carrier words while preserving
    everything the substrate *decides*: weight, lawfulness, and the snap
    distance (the minimum weight of the coset).  It does not preserve the
    syndrome, which is read off a fixed systematic basis and therefore travels
    with the coordinates.  Because the group is 5-transitive it is transitive
    on the words of any weight up to five, so a concept of carrier weight 3 --
    energy, for instance -- has as its orbit all 2,024 words of weight 3: the
    substrate has no preferred coordinates, only preferred *distances*.  The
    companion exposes this as `reasoner.symmetry_orbit(name)`.

  8.2  The extraspecial group 2^(1+24)

    In Heisenberg coordinates (a, b, eps) with a, b in F_2^12, the group of
    order 2^25 acts on a 4096-dimensional space by signed permutations:

        rho(a, b, eps) |k> = (-1)^(<a,k> + eps) |k XOR b>.

    All defining relations hold as exact operator identities, including the
    extraspecial commutator [x_i, y_i] = z (Claim C19).  For contrast we also
    build the 24-dimensional "sign flip and axis swap" action used in earlier
    versions and check the same relation: it fails, because those matrices
    commute.  That is the concrete content of "the 24D action is not
    faithful".

  8.3  The snap algebra  (a corrected result)

    Earlier versions defined
        B(v,w) = snap(v XOR w) XOR snap(v) XOR snap(w) XOR snap(0)
        v . w  = snap(v XOR w) XOR B(v,w)
    and described the result as a commutative NON-associative algebra, "the
    Griess product", unifying the bottom and top of the sporadic hierarchy.

    Writing snap(v) = v XOR L(sigma(v)) and substituting gives

        B(v,w) = L(sigma(v) XOR sigma(w)) XOR L(sigma(v)) XOR L(sigma(w)),
        v . w  = snap(v) XOR snap(w).

    So (i) B depends only on the two syndromes and always has zero syndrome
    (it is a codeword); (ii) the product is XOR of two codewords, hence
    commutative AND associative, with v . v = 0; and (iii) all triple defects
    vanish: B(B(v,w), u) = 0.  Claim C20 checks all four statements.

    The construction is real and mildly interesting — it is the retraction of
    F_2^24 onto (C, XOR) induced by the decoder — but it is not a Griess-like
    algebra, and the Monster does not enter.  We record the correction rather
    than quietly dropping the claim.

--------------------------------------------------------------------------------
  9.  THE FIBRE GEOMETRY  (versions 9-12, made exact)
--------------------------------------------------------------------------------

  Sections 9 and 10 consolidate the second half of the GLM's development, the
  line that ran from v9 to v19.  Everything in them is optional: no verdict of
  Sections 3 to 6 depends on a single line of it.  What it adds is geometry on
  top of the carrier, and - just as importantly - an exact account of which of
  the earlier geometric claims survive.  The code is glm_geometry.py; the
  version-by-version account is DEVELOPMENT_CATALOG.md.

  9.1  The fibre key is a quarter turn

    The column codec of Section 3.1 splits a MOG column into a GF(4) label and
    a fibre key in Z_4.  Reading the key as a fourth root of unity gives a
    Z_4-valued invariant of a word,

        u(w) = (sum of the six fibre keys) mod 4,

    computed by integer arithmetic; nothing is ever rotated numerically.  This
    is v9's "versor", stripped of the claim that it says anything about the
    Leech lattice.

  9.2  Quaternions buy exactly one thing

    v10 replaced the fourth roots of unity by the quaternion units 1, i, j, k.
    The map Z_4 -> {1,i,j,k} is a bijection of SETS and is not a group
    homomorphism (Z_4 is cyclic of order 4; the units generate Q8, of order
    8), and Claim C25 records both halves of that.  What the change does buy
    is non-commutativity: the ordered product of a word's six fibre
    quaternions depends on the column order, for part of the library and not
    all of it (Claim C26 counts which).  The H^6 layout of v11 is this list of
    six unit quaternions.

  9.3  Walks and winding  (Proposition 2)

    Let u be the invariant of 9.1.  For a step from w to w' put s = u(w') -
    u(w) in Z_4 and lift it to the representative s~ in {-1, 0, 1, 2}.  Along
    any CLOSED walk the sum of the lifted steps is divisible by 4, so

        winding = (sum of lifted steps) / 4

    is an integer.  Proof: s~ = s in Z_4, so the sum of the lifts is congruent
    mod 4 to the telescoping sum of the true steps, which is u(w_n) - u(w_0) =
    0.  Claim C27 checks the consequence over a generated family of closed
    walks, including the E = m c^2 round trip that v9 reported.  The winding
    is an invariant of the lift, not of the endpoints: two routes between the
    same concepts generally wind differently, which is what makes it worth
    computing at all.  Proposition 2 is also proved in general (for any lift
    of Z_4 to Z, and for the concrete lift used here) in the Lean companion,
    as GLM.winding_integral and GLM.winding_integral_liftStep.

  9.4  Holonomy

    v12 asked for a path-dependent holonomy; here it is the ordered product of
    the loop's fibre quaternions.  It is genuinely path-dependent (reversing a
    loop generally changes it) and it telescopes exactly against the reversed
    product of inverses (Claim C28).  It is a Q8-valued invariant of the
    ordered loop, and no more: no connection, curvature or parallel transport
    is claimed.

  9.5  What L0 was  (a correction)

    Versions 15 to 19 carried a "renormalised Virasoro weight"

        L0 = (||H^6 vector||^2 - 6)/2 + sigma/2,

    described as a conformal grading renormalised so that a "1A vacuum" sits
    at zero.  But the H^6 vector is six UNIT quaternions, so its squared norm
    is 6 for every concept whatsoever, and the first term is identically zero.
    The quantity actually computed was

        L0 = sigma / 2,

    half the Golay syndrome weight.  Claim C29 verifies the identity over the
    whole library.  The observable is kept and reported by the reasoner; the
    Virasoro name is dropped, because nothing in it came from a vertex
    algebra.

  9.6  Vacua

    v14 searched [-3,3]^7 for "1A concepts" - dimension vectors whose carrier
    is a codeword - and found 221 with its (many-to-one) encoder.  With the
    bijective carrier the question has an exact answer: 1,168 over the whole
    representable box (Claim C13), of which 22 lie in [-2,2]^7 (Claim C30),
    each verified to be a codeword that decodes back to its exponents.  The
    dimensionless vector is the zero codeword.

  9.7  Colour

    A hex colour #RRGGBB is 24 bits, so it is a word of F_2^24; v18 noticed
    this and v19 searched for "chromatic ground states", the syndrome-free
    colours.  No search is needed.  The syndrome-free words are exactly the
    codewords, so there are exactly 4,096 such colours out of 16,777,216 - one
    colour in every 4,096 - and they can be listed in full; black and white are
    among them (Claim C31).  Snapping a colour is a chromatic correction, and
    the reasoner reports the per-channel shift.  This is the most usable idea
    of the late archive: it turns the substrate into something a person can
    see.

--------------------------------------------------------------------------------
  10.  THE LEECH LEDGER  (versions 13-19, what counts and what does not)
--------------------------------------------------------------------------------

  The late archive climbed a "sporadic complexity map" towards the Monster.
  Some of that ascent is exactly checkable arithmetic and is shipped here, in
  glm_moonshine.py; the rest was reached for, and this section says so.

  10.1  The lines

    Lambda_24 has 196,560 minimal vectors, in three shape classes (Section
    2.3).  Enumerating all of them and checking that the set is closed under
    v -> -v, that no vector is its own negative, and that all are distinct,
    turns "98,280 lines" from an assertion into a count, with the split
    552 / 48,576 / 49,152 (Claim C32).  v18's "orbit line tracker" asserted
    this; here it is counted.

  10.2  98,304 = 24 x 4096

    The class C minimal vectors are indexed by a coordinate (24 choices) and a
    codeword (4,096 choices).  The indexing is verified to be injective, with
    every image of norm^2 32 and glue residue 4 mod 8 (Claim C32).  So the
    tensor-product dimension that v16 and v18 introduced is a count of
    something, not an analogy.

  10.3  The ledger, and the head of J

    Two independent computations of the same number:

        1 + 299 + 98,280 + 98,304 = 196,884

    where 299 = 24.25/2 - 1 is the dimension of the traceless symmetric forms,
    98,280 is the line count of 10.1 and 98,304 the index count of 10.2; and

        196,884 = 324 + 196,560

    where 324 is the q^2 coefficient of prod (1 - q^n)^-24, computed here as an
    exact integer power series, and 196,560 is the census.  The second is the
    weight-2 graded dimension of the Leech lattice vertex algebra, i.e. the
    q^1 coefficient of J(q) = q^-1 + 24 + 196884 q + ...  (Claim C33).

    That is the whole of what this system says about moonshine.  It is
    bookkeeping that happens to be checkable, not a construction of the Griess
    algebra and still less of its automorphism group.  The expansion is
    carried to q^1 and stops there, because the next coefficient needs the
    norm-6 shell, which this system does not enumerate; asking for it raises
    rather than guesses.

  10.4  A layer that really is non-associative  (replacing 8.3)

    Section 8.3 shows the archive's snap-based "Griess product" is
    associative.  What can be exhibited exactly, in 300 dimensions, is the
    scalar-plus-traceless-symmetric layer with

        (a, S) . (b, T) = (ab + tr(ST)/24,
                           aT + bS + (ST + TS)/2 - tr(ST)/24 . I).

    Under (a, S) <-> aI + S this is the Jordan algebra of symmetric 24 x 24
    matrices: commutative, unital, NOT associative, and satisfying the Jordan
    identity - all four checked in exact rational arithmetic (Claim C34).  It
    is the layer of the right shape that a small machine can carry honestly.
    The other two layers of 10.3 are counted, not constructed.

    The 4096-dimensional equation checker of v16 is not kept.  Comparing
    concepts as 4096-dimensional states is strictly weaker than integer
    equality in Z^7 and far slower; the 4096-dimensional space earns its place
    here as a faithful representation (8.2, 10.6), not as a decision
    procedure.

  10.5  What the archive's "inner product" was  (a correction)

    Versions 18 and 19 fused concepts using an "inner product" defined as
    (matching bits) - (mismatching bits) between two 24-bit words, read as a
    Leech lattice pairing.  For 24-bit words that quantity is identically
    24 - 2 d(u,v): it is the Hamming distance, rescaled (Claim C35).  The
    vertex operators built on it therefore carried no VOA content and are not
    kept.

  10.6  The semidirect product  (a correction of naming)

    v19 built "2^(1+24) semidirect Co_1" with the outer factor acting by
    permutations of the twelve Heisenberg pairs.  The construction is sound,
    but permuting twelve pairs gives S_12, of order 479,001,600, not Co_1, of
    order about 4.16 x 10^18.  Shipped under its own name, 2^(1+24) : S_12 is
    verified exactly: pair permutations act by automorphisms fixing the
    centre, the product is associative, unital and has inverses, conjugation
    moves the generators (x_i -> x_{s(i)}), the group is non-commutative, and
    the map to signed permutations of the 4096 basis vectors is a homomorphism
    checked on the whole space (Claim C36).  Co_1 is not implemented, and
    saying so is part of the result.

--------------------------------------------------------------------------------
  11.  WHAT NINETEEN VERSIONS LEFT BEHIND
--------------------------------------------------------------------------------

  The GLM was developed as a sequence of experiments: a paper strand (v1 to
  v7, then paper 10), a companion strand (the geometric reasoner, then v17)
  and a research strand (v8 to v19), each version preserving the last and
  adding a tier.  DEVELOPMENT_CATALOG.md notes every version and tabulates
  where each of its 36 ideas ended up.  In summary:

    kept and strengthened   the Golay/MOG/hexacode substrate; the integer
                            companion and the mod-2 ceiling (now a theorem);
                            the reasoner's solver and Pi analysis; the
                            faithful 4096-dimensional action; the line count;
                            the colour view;

    corrected               the four-tier encoder (many-to-one, Section 3.2);
                            the 6,793-pair precision figure (unreproducible,
                            Section 5.4); the snap-based Griess product
                            (associative, Section 8.3); L0 (= sigma/2, 9.5);
                            the "Leech inner product" (= Hamming distance,
                            10.5); Co_1 (= S_12, 10.6);

    dropped, with reason    the Co_2/Co_3 stabiliser selection and the
                            concept-to-conjugacy-class map, both of which were
                            relabellings of the syndrome weight; the
                            McKay-Thompson tables, which no code in the
                            archive generated and which disagree between
                            versions; the vertex operators of 10.5; the
                            4096-dimensional equation checker of 10.4.

  The pattern is worth stating because it is the method: each ascent was
  attempted, the part that could be computed exactly was kept, and the part
  that could not was named as such rather than carried forward as decoration.

--------------------------------------------------------------------------------
  12.  WHAT IS CLASSICAL, WHAT IS NEW, WHAT IS STIPULATED
--------------------------------------------------------------------------------

  Classical, used as-is:
    the Golay code and its parameters; the Steiner system S(5,8,24); the
    hexacode and the MOG; the Leech lattice minimal-vector classification;
    dimensional analysis and the Buckingham Pi theorem; the Smith normal form;
    the Schrodinger (Heisenberg-group) representation of an extraspecial
    2-group.

  New here, in the sense of being this system's own construction:
    the pairing of an exact (Z^7,+) semantics with a bijective 24-bit Golay
    carrier; the base-9 dimension carrier and its lawfulness census (1,168
    lawful vectors, the dimensionless vector as the zero codeword); the
    column-fibre presentation of the codec as "hexacode symbol plus fibre
    key"; the matroid-based automorphism search of Section 8.1, which produces
    Aut(C) = M24 from this code with nothing about M24 assumed; the reasoner
    built on exact integer solving with honest integer/rational/impossible
    verdicts; and the corrections in Sections 3.2 and 8.3.

  Stipulated (a modelling choice, not a result):
    the cost layer Y, TAX, NRCI of Section 7; the reading of the syndrome as
    "history"; the names of the four ontological tiers.

  Deliberately NOT claimed:
    that dimensional admissibility is physical truth; that the carrier bits
    have intrinsic physical meaning; that the Monster group, its Griess
    algebra or a vertex operator algebra is constructed anywhere in this
    system.  Section 10 counts 196,884 in two ways, and that is arithmetic
    about known objects, not a construction of them; Section 10.6 ships S_12
    and says plainly that Co_1 is absent.  Earlier drafts reached further; the
    versions of those reaches that survive contact with a verifier are in
    Sections 8 to 10, and they are smaller.

--------------------------------------------------------------------------------
  13.  DEVELOPING THIS FURTHER
--------------------------------------------------------------------------------

  The invariants a change must preserve (all enforced by test_glm.py):

    I0  the meaning is the state and the carrier is a derived view of it:
        `derive_substrate` is the only producer of a carrier, `Concept` is
        frozen with `dim` as its only semantic field, every substrate
        attribute is a read-only property, and no bit pattern is ever an
        input.  Nothing composes on the carrier, and no verdict reduces an
        exponent modulo 2 (Section 5);
    I1  the column codec is a bijection on all 16 states;
    I2  the 24-bit codec round trip loses 0 bits in both griddings;
    I3  the dimension carrier is injective on [-4,4]^7 and inverts exactly;
    I4  snap always lands on a codeword, at distance <= 4, and reports its
        ties truthfully;
    I5  the reasoner's verdict is integer equality in Z^7 — never a score,
        never a threshold;
    I6  every claim in this docstring has a verifier in `CLAIMS` below;
    I7  the optional layers of Sections 8 to 10 stay optional: glm_substrate,
        glm_codec, glm_metrology and glm_linalg must not import them, and no
        verdict of `audit`, `solve` or `pi_groups` may consult them.  The
        reasoner may DISPLAY their telemetry and does; it never decides with
        it.

  Natural next steps, in rough order of value:

    D1  more quantities and unit-name aliases; the library is a dictionary and
        adding to it costs one line each.  A dimension is not a unit: adding
        unit prefixes and numeric conversion is a separate (useful) layer.
    D2  numeric evaluation alongside dimensional checking, so that
        E = 1000 m c^2 can be rejected as well as E = m c^4.
    D3  a relation store: named laws with their derivations, so target
        synthesis can return the actual law (P = U I) rather than only the
        dimensionally admissible product.
    D4  richer geometry: the current scene export places concepts at their
        (L, M, T) exponents.  Using the Leech metric on carriers, or the MOG
        shadow, would make the picture substrate-native.
    D5  formal verification.  Section 5.5 lists what is already proved in
        `RequestProject/GLM.lean` (the mod-2 ceiling, the carrier capacity and
        the column-label fibration).  Still open: the Golay parameters, the
        covering radius and the Leech shell counts, so that Section 2 rests on
        proof rather than on exhaustive computation.
    D6  a fibre-aware search: which dimension vectors share a hexacode shadow,
        and does that equivalence mean anything for physics?  This is the most
        interesting open question the codec raises, and it is currently
        unanswered.

--------------------------------------------------------------------------------
  14.  REFERENCES
--------------------------------------------------------------------------------

  [1] Conway, J. H.; Sloane, N. J. A.  Sphere Packings, Lattices and Groups.
      3rd ed., Springer, 1999.  (Golay code, MOG, hexacode, Leech lattice,
      minimal-vector classes.)
  [2] MacWilliams, F. J.; Sloane, N. J. A.  The Theory of Error-Correcting
      Codes.  North-Holland, 1977.  (Weight enumerator, covering radius.)
  [3] Buckingham, E.  On physically similar systems.  Physical Review 4
      (1914), 345-376.  (The Pi theorem.)
  [4] Bureau International des Poids et Mesures.  The International System of
      Units (SI), 9th ed., 2019.  (The seven base quantities.)
  [5] Cohn, H.; Kumar, A.  Optimality and uniqueness of the Leech lattice
      among lattices.  Annals of Mathematics 170 (2009), 1003-1050.
  [6] Griess, R. L.  The Friendly Giant.  Inventiones Mathematicae 69 (1982),
      1-102.  (Cited to delimit what Sections 8.3 and 10.4 do NOT do.)
  [7] Conway, J. H.; Norton, S. P.  Monstrous moonshine.  Bulletin of the
      London Mathematical Society 11 (1979), 308-339.  (The J-function head
      of Section 10.3; no coefficient table is taken from it.)
  [8] Frenkel, I.; Lepowsky, J.; Meurman, A.  Vertex Operator Algebras and
      the Monster.  Academic Press, 1988.  (Cited to delimit Section 10.5.)

================================================================================
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Callable, Dict, List, Tuple

from glm_codec import (CARRIER_CAPACITY, ColumnCodec, DimCarrier, MOGCodec,
                       lawful_dimension_census)
from glm_geometry import (chromatic_ground_states, colour_report,
                          conformal_grading_report,
                          fibre_noncommutativity_report, holonomy_report,
                          quaternion_group_report, vacuum_census,
                          winding_report, word_of_colour)
from glm_linalg import _self_check as linalg_self_check
from glm_metrology import (QUANTITIES, Dimension, audit_equation,
                           dimensional_collisions, mod2_box_census,
                           mod2_collapse_report, mod2_perturbation_sweep,
                           mod2_would_accept, parse_expression)
from glm_m24 import (BASE_POINTS, M24_GENERATORS, StabChain, code_automorphisms,
                     compose, inverse, m24_report, preserves_code,
                     schreier_sims, subgroup_census)
from glm_monster import (column_symmetry_report, extraspecial_relation_report,
                         normaliser_report, snap_algebra_report)
from glm_moonshine import (class_c_indexing_report, dimension_ledger,
                           hamming_inner_product_report,
                           jordan_algebra_report, leech_voa_head, line_census)
from glm_reasoner import DEMO_EQUATIONS, DEMO_QUERIES, REASONER, Concept
from glm_substrate import (GOLAY, HEXACODE, LEECH, MOG, BitOps, Y,
                           substrate_audit)

PAPER_TITLE = "The Geometric Language Machine (GLM)"
PAPER_VERSION = "20.0 (consolidated edition)"
PAPER_AUTHOR = "E. R. A. Craig (DigitalEuan), Auckland, New Zealand"


# ══════════════════════════════════════════════════════════════════════════════
#  THE CLAIMS  —  one verifier per numbered claim in the paper above
# ══════════════════════════════════════════════════════════════════════════════
#
#  A claim is a triple (id, statement, verifier).  The verifier returns
#  (passed, evidence).  `run_paper` executes all of them and prints a table;
#  the paper is "operational" precisely in the sense that no statement above
#  is unaccompanied by one of these.

Verifier = Callable[[], Tuple[bool, object]]


def _c1_codeword_count() -> Tuple[bool, object]:
    n = len(GOLAY.all_codewords())
    return n == 4096, {"codewords": n}


def _c2_min_distance() -> Tuple[bool, object]:
    d = GOLAY.min_distance()
    return d == 8, {"min_distance": d}


def _c3_weight_enumerator() -> Tuple[bool, object]:
    w = GOLAY.weight_enumerator()
    expected = {0: 1, 8: 759, 12: 2576, 16: 759, 24: 1}
    return w == expected, {"weight_enumerator": w}


def _c4_self_dual_doubly_even() -> Tuple[bool, object]:
    sd, de = GOLAY.is_self_dual(), GOLAY.is_doubly_even()
    return sd and de, {"self_dual": sd, "doubly_even": de}


def _c5_covering_radius() -> Tuple[bool, object]:
    census = GOLAY.census()
    profile = census["leader_weight_profile"]
    ok = (census["cosets"] == 4096 and census["covering_radius"] == 4
          and profile == {0: 1, 1: 24, 2: 276, 3: 2024, 4: 1771})
    return ok, {"cosets": census["cosets"], "leader_weight_profile": profile}


def _c6_ambiguity_at_four() -> Tuple[bool, object]:
    """Every weight-4 coset has exactly six minimum-weight leaders, and a
    directly computed example confirms six equally near codewords."""
    profile = GOLAY.census()["tie_profile"]
    ok = profile.get("weight4:6-way") == 1771 and \
        all(k.endswith("1-way") for k in profile if not k.startswith("weight4"))
    # independent confirmation by brute force on one ambiguous word
    leaders = GOLAY.leader_table()
    target = next(s for s, mask in leaders.items() if bin(mask).count("1") == 4)
    word = BitOps.from_int(leaders[target], 24)
    nearest = GOLAY.nearest_codewords(word)
    ok = ok and len(nearest) == 6
    return ok, {"tie_profile": profile, "brute_force_ties": len(nearest)}


def _c7_mog_alignment() -> Tuple[bool, object]:
    res = MOG.verify_hexacode_shadow()
    fibres = MOG.label_fibre_sizes()
    ok = res["failures"] == 0 and fibres == {0: 4, 1: 4, 2: 4, 3: 4}
    return ok, {"hexacode_shadow_failures": res["failures"], "label_fibres": fibres}


def _c8_hexacode() -> Tuple[bool, object]:
    c = HEXACODE.census()
    return c["size"] == 64 and c["min_distance"] == 4, c


def _c9_leech_census() -> Tuple[bool, object]:
    c = LEECH.census(verify_every_vector=True)
    ok = (c["total"] == 196560 and c["norm_failures"] == 0
          and c["class_A"] == 1104 and c["class_B"] == 97152
          and c["class_C"] == 98304
          and c["glue_residues_mod8"] == {"A": [0], "B": [0], "C": [4]})
    return ok, c


def _c10_column_bijection() -> Tuple[bool, object]:
    res = ColumnCodec.verify_bijection()
    return bool(res["bijective"]), res


def _c11_codec_round_trip() -> Tuple[bool, object]:
    errors = {"aligned": 0, "tier": 0}
    state = 0x5DEECE66
    for _ in range(20000):
        state = (state * 1103515245 + 12345) & 0xFFFFFF
        v = BitOps.from_int(state, 24)
        errors["aligned"] += MOGCodec.round_trip_error(v, aligned=True)
        errors["tier"] += MOGCodec.round_trip_error(v, aligned=False)
    # plus every Golay codeword, exhaustively
    codeword_errors = sum(MOGCodec.round_trip_error(cw, aligned=True)
                          for cw in GOLAY.all_codewords())
    ok = errors["aligned"] == 0 and errors["tier"] == 0 and codeword_errors == 0
    return ok, {"random_words": 20000, **errors, "codeword_errors": codeword_errors}


def _c12_carrier_lossless() -> Tuple[bool, object]:
    integrity = REASONER.codec_integrity()
    ok = bool(integrity["lossless"]) and integrity["concepts_tested"] == len(QUANTITIES)
    return ok, integrity


def _c13_lawful_census() -> Tuple[bool, object]:
    census = lawful_dimension_census()
    ok = (census["searched"] == CARRIER_CAPACITY and census["lawful"] == 1168
          and census["by_carrier_weight"] == {0: 1, 8: 390, 12: 696, 16: 81}
          and census["examples"][0]["dims"] == [0] * 7)
    return ok, {k: v for k, v in census.items() if k != "examples"}


def _c14_mod2_corollary() -> Tuple[bool, object]:
    """The named traps: accepted mod 2, rejected exactly."""
    traps = [
        ("energy", "mass*speed^4"),
        ("force", "mass*acceleration^3"),
        ("illuminance", "luminous_flux*area"),
        ("stefan_boltzmann", "irradiance/temperature^2"),
        ("action", "energy*time^3"),
    ]
    detail = []
    ok = True
    for lhs, rhs in traps:
        rec = audit_equation(lhs, rhs)
        would = mod2_would_accept(rec.lhs_dim, rec.rhs_dim)
        ok = ok and would and not rec.accepted
        detail.append({"equation": f"{lhs} = {rhs}",
                       "exact_accepts": rec.accepted,
                       "mod2_accepts": would})
    return ok, detail


def _c15_mod2_measurement() -> Tuple[bool, object]:
    report = mod2_collapse_report()
    batch = REASONER.mod2_ceiling_batch(DEMO_EQUATIONS)
    ok = (report["pairs_indistinguishable_mod2"] > 0
          and report["exact_false_positive_rate"] == 0.0
          and batch["mod2_false_positives_prevented"] >= 4)
    return ok, {"library": report,
                "curated_equations": {k: v for k, v in batch.items()
                                      if k != "records"}}


def _c16_target_synthesis() -> Tuple[bool, object]:
    """Known answers the solver must reproduce, including the honest failures."""
    expected = {
        ("energy", ("mass", "speed")): ("integer", "energy = mass * speed^2"),
        ("power", ("voltage", "current")): ("integer", "power = voltage * current"),
        ("power", ("current", "resistance")):
            ("integer", "power = current^2 * resistance"),
        ("speed", ("energy", "mass")):
            ("fractional", "speed = energy^1/2 / mass^1/2"),
        ("illuminance", ("luminous_flux", "area")):
            ("integer", "illuminance = luminous_flux / area"),
        ("temperature", ("energy", "mass")): ("impossible", ""),
    }
    detail, ok = [], True
    for (target, inputs), (status, formula) in expected.items():
        sol = REASONER.solve(target, list(inputs))
        got = sol.formula() if sol.found else ""
        good = sol.status == status and (not formula or got == formula)
        ok = ok and good
        detail.append({"target": target, "inputs": list(inputs),
                       "status": sol.status, "formula": got, "ok": good})
    return ok, detail


def _c17_pi_theorem() -> Tuple[bool, object]:
    cases = (("force", "density", "speed", "length"),
             ("speed", "length", "kinematic_viscosity"),
             ("energy", "mass", "speed", "time"),
             ("pressure", "density", "speed"),
             ("voltage", "current", "resistance"))
    detail, ok = [], True
    for inputs in cases:
        res = REASONER.pi_groups(list(inputs))
        good = (res["status"] == "ok" and res["pi_theorem_holds"]
                and all(g["verified_dimensionless"] for g in res["groups"]))
        ok = ok and good
        detail.append({"inputs": list(inputs), "rank": res["rank"],
                       "groups": [g["expression"] for g in res["groups"]],
                       "ok": good})
    return ok, detail


def _c18_automorphism_test() -> Tuple[bool, object]:
    report = column_symmetry_report()
    ok = report["identity"] and report["swap_halves"] and \
        not report["transpose_1_2"]
    return ok, report


def _c19_extraspecial() -> Tuple[bool, object]:
    report = extraspecial_relation_report()
    ok = bool(report["all_relations_hold"]) and \
        not report["24d_action_realises_commutator"]
    return ok, report


def _c20_snap_algebra() -> Tuple[bool, object]:
    report = snap_algebra_report()
    ok = (report["commutative"] and report["associative"]
          and report["defect_is_always_a_codeword"]
          and report["defect_depends_only_on_syndromes"]
          and report["product_equals_snap_xor_snap"]
          and report["squares_are_zero"]
          and report["triple_defect_nonzero_count"] == 0
          and not report["earlier_non_associativity_claim_holds"])
    return ok, report


def _c21_exact_arithmetic() -> Tuple[bool, object]:
    """No decision anywhere depends on a float: the cost layer is rational and
    the linear algebra is integer/rational."""
    passed, total = linalg_self_check(200)
    tax = LEECH.tax(BitOps.from_int(0b1011, 24))
    ok = passed == total and tax.denominator > 1 and float(Y) < 1
    return ok, {"linalg_random_systems": f"{passed}/{total}",
                "example_tax_is_exact_fraction": str(tax)}


def _c22_parser() -> Tuple[bool, object]:
    cases = {
        "mass*speed^2": Dimension((2, 1, -2, 0, 0, 0, 0)),
        "energy/(area*time)": Dimension((0, 1, -3, 0, 0, 0, 0)),
        "1/time": Dimension((0, 0, -1, 0, 0, 0, 0)),
        "force*length^2/mass^2": Dimension((3, -1, -2, 0, 0, 0, 0)),
        "(luminous_flux/area)*time": Dimension((-2, 0, 1, 0, 0, 0, 1)),
    }
    detail, ok = [], True
    for text, want in cases.items():
        got = parse_expression(text)
        good = got == want
        ok = ok and good
        detail.append({"expression": text, "parsed": str(got), "ok": good})
    return ok, detail


def _int_box(bound: int) -> List[Tuple[int, ...]]:
    """All exponent vectors in [-bound, bound]^7 (used by Claim C24)."""
    vectors: List[Tuple[int, ...]] = [()]
    for _ in range(7):
        vectors = [v + (e,) for v in vectors
                   for e in range(-bound, bound + 1)]
    return vectors


def _c23_mod2_perturbation() -> Tuple[bool, object]:
    """
    Proposition 1 on a family with a reproducible denominator: shifting one
    exponent of a named quantity by +-2 always fools an XOR substrate and
    never fools (Z^7, +).
    """
    sweep = mod2_perturbation_sweep()
    ok = (sweep["false_equations"] == 2 * 7 * len(QUANTITIES)
          and sweep["mod2_accepted"] == sweep["false_equations"]
          and sweep["mod2_false_positive_rate"] == 1.0
          and sweep["exact_accepted"] == 0
          and sweep["named_traps"] > 0)
    return ok, sweep


def _c24_mod2_box_census() -> Tuple[bool, object]:
    """
    The same ceiling counted in closed form over the whole exponent box
    [-2,2]^7, checked against a direct count over a small box where direct
    counting is affordable.
    """
    census = mod2_box_census(2)
    small = mod2_box_census(1)
    vectors = [tuple(e) for e in _int_box(1)]
    brute = 0
    for i in range(len(vectors)):
        for j in range(i + 1, len(vectors)):
            if (tuple(v % 2 for v in vectors[i])
                    == tuple(v % 2 for v in vectors[j])):
                brute += 1
    ok = (census["box_size"] == 5 ** 7
          and census["unordered_pairs"] == 5 ** 7 * (5 ** 7 - 1) // 2
          and census["pairs_confused_mod2"] == 31335196
          and census["pairs_confused_exactly"] == 0
          and small["pairs_confused_mod2"] == brute)
    return ok, {"box_2": census, "box_1_closed_form": small,
                "box_1_brute_force": brute}


def _c25_versor_layer() -> Tuple[bool, object]:
    """Section 9.1-9.2: the fibre keys as quarter turns and as quaternions."""
    report = quaternion_group_report()
    ok = (report["order"] == 8 and report["closed"] and report["associative"]
          and report["relations_all_hold"]
          and report["fibre_map_bijective"]
          and not report["fibre_map_is_homomorphism"])
    return ok, report


def _c26_fibre_noncommutativity() -> Tuple[bool, object]:
    """The only structural gain of the quaternionic reading, counted."""
    report = fibre_noncommutativity_report()
    ok = (report["tested"] == len(QUANTITIES)
          and report["order_sensitive"] > 0
          and report["order_sensitive"] + report["order_insensitive"]
          == report["tested"])
    return ok, report


def _c27_winding() -> Tuple[bool, object]:
    """Section 9.3: closed walks have integer winding numbers."""
    report = winding_report()
    ok = (report["closed_walks"] > 0 and report["all_windings_integral"]
          and report["emc2_roundtrip"]["closed"]          # type: ignore[index]
          and report["emc2_roundtrip"]["winding"] is not None)  # type: ignore[index]
    return ok, {k: v for k, v in report.items() if k != "detail"}


def _c28_holonomy() -> Tuple[bool, object]:
    """Section 9.4: the loop product is path-dependent and telescopes."""
    report = holonomy_report()
    ok = (report["path_dependent_loops"] > 0
          and report["telescoping_identity_holds"])
    return ok, report


def _c29_conformal_grading() -> Tuple[bool, object]:
    """Section 9.5: the archive's L0 is half the syndrome weight, exactly."""
    report = conformal_grading_report()
    ok = (report["tested"] == len(QUANTITIES)
          and report["h6_norm_sq_always_six"]
          and report["archive_L0_equals_half_syndrome"])
    return ok, report


def _c30_vacua() -> Tuple[bool, object]:
    """Section 9.6: the syndrome-free dimension vectors of a small box."""
    census = vacuum_census(bound=2)
    lawful_named = set(census["named_lawful"])          # type: ignore[arg-type]
    ok = (census["searched"] == 5 ** 7
          and census["lawful"] == 22
          and lawful_named <= set(REASONER.lawful_concepts()))
    # each reported vector really is a codeword and decodes back
    for dims in census["examples"]:                     # type: ignore[union-attr]
        word = DimCarrier.encode(dims)
        ok = ok and GOLAY.is_codeword(word) and DimCarrier.decode(word) == dims
    return ok, census


def _c31_colour() -> Tuple[bool, object]:
    """Section 9.7: the chromatic ground states are exactly the code."""
    report = colour_report()
    grounds = chromatic_ground_states()
    ok = (report["ground_states"] == 4096
          and report["ground_state_fraction_one_in"] == 4096
          and report["round_trip_lossless"]
          and all(report["black_and_white_are_ground_states"].values())  # type: ignore[union-attr]
          and len(set(grounds)) == 4096
          and all(GOLAY.is_codeword(word_of_colour(c)) for c in grounds[:64]))
    return ok, report


def _c32_leech_lines() -> Tuple[bool, object]:
    """Section 10.1-10.2: 98,280 lines, and 98,304 = 24 x 4096."""
    lines = line_census()
    index = class_c_indexing_report()
    ok = (lines["vectors"] == 196560 and lines["all_distinct"]
          and lines["negation_closed"]
          and lines["class_preserved_under_negation"]
          and lines["self_negative_vectors"] == 0
          and lines["matches_expected"]
          and index["injective"] and index["equals_24_times_4096"]
          and index["norm_failures"] == 0 and index["glue_failures"] == 0)
    return ok, {"lines": lines, "class_C_indexing": index}


def _c33_dimension_ledger() -> Tuple[bool, object]:
    """Section 10.3: 196,884 computed twice, from independent definitions."""
    ledger = dimension_ledger()
    head = leech_voa_head()
    ok = (ledger["ledger_balances"] and ledger["standard_rep_matches"]
          and ledger["traceless_sym_dim"] == 299
          and ledger["lines"] == 98280 and ledger["tensor"] == 98304
          and head["weight_two_dim"] == 196884
          and head["weight_two_split"] == {"oscillator": 324,
                                           "lattice": 196560}
          and head["matches_griess_dim"])
    return ok, {"ledger": ledger, "J_head": head}


def _c34_jordan_layer() -> Tuple[bool, object]:
    """Section 10.4: a genuinely non-associative commutative layer."""
    report = jordan_algebra_report()
    ok = (report["dimension"] == 300 and report["commutative"]
          and report["unital"] and report["closed_in_layer"]
          and not report["associative"] and report["jordan_identity"])
    return ok, report


def _c35_archive_inner_product() -> Tuple[bool, object]:
    """Section 10.5: the archive's 'Leech inner product' is Hamming distance."""
    report = hamming_inner_product_report(2048)
    ok = bool(report["holds"]) and report["counterexamples"] == 0
    return ok, report


def _c36_semidirect() -> Tuple[bool, object]:
    """Section 10.6: 2^(1+24) : S_12, exactly, in 4096 dimensions."""
    report = normaliser_report()
    ok = (report["pair_perms_are_automorphisms"] and report["centre_fixed"]
          and report["associative"] and report["unital"] and report["inverses"]
          and report["conjugation_moves_generators"]
          and report["non_commuting_pairs"] > 0
          and report["action_is_homomorphism_on_4096"])
    return ok, report


def _c37_m24_group() -> Tuple[bool, object]:
    """Section 8.1: the group generated is 5-transitive of order |M24|."""
    report = m24_report(quick=True)
    ok = (bool(report["generators_preserve_code"])
          and report["order"] == report["order_expected"]
          and bool(report["five_transitive"])
          and report["point_stabiliser_chain_order"] == 48
          and bool(report["octad_transitive"])
          and report["octad_stabiliser_order"] == 322560)
    return ok, report


def _c38_m24_is_full_aut() -> Tuple[bool, object]:
    """Section 8.1: Aut(C) = M24, by exhaustive stabiliser enumeration."""
    report = m24_report(quick=False)
    ok = (report["exhaustive_stabiliser"] == 48
          and bool(report["stabiliser_all_in_group"])
          and report["aut_order_from_orbit_stabiliser"] == 244823040
          and bool(report["is_full_automorphism_group"]))
    return ok, report


def _c39_stabiliser_chain_is_sound() -> Tuple[bool, object]:
    """Section 8.1: sifting through the chain agrees with the exhaustive
    codeword test, on members and on non-members alike."""
    chain: StabChain = schreier_sims(list(M24_GENERATORS), 24,
                                     base_hint=BASE_POINTS)
    members = []
    g = M24_GENERATORS[0]
    for h in M24_GENERATORS:
        g = compose(g, h)
        members.append(g)
        members.append(inverse(g))
    member_ok = all(chain.contains(p) and preserves_code(p) for p in members)
    # non-members: a transposition and a 3-cycle, neither an automorphism
    non = []
    p = list(range(24))
    p[0], p[1] = p[1], p[0]
    non.append(tuple(p))
    q = list(range(24))
    q[0], q[1], q[2] = q[1], q[2], q[0]
    non.append(tuple(q))
    non_ok = all((not chain.contains(p)) and (not preserves_code(p)) for p in non)
    stab = code_automorphisms({b: b for b in BASE_POINTS}, limit=8)
    stab_ok = all(chain.contains(p) and preserves_code(p) for p in stab)
    ok = member_ok and non_ok and stab_ok and chain.order() == 244823040
    return ok, {"members_tested": len(members), "members_agree": member_ok,
                "non_members_tested": len(non), "non_members_agree": non_ok,
                "stabiliser_samples": len(stab), "stabiliser_agree": stab_ok,
                "order": chain.order()}


def _c40_m24_on_concepts() -> Tuple[bool, object]:
    """Section 8.1: the group acts on carrier words preserving weight,
    lawfulness and snap distance, and is transitive on words of weight <= 5."""
    rows = []
    ok = True
    for name in ("energy", "force", "pressure", "speed", "entropy"):
        report = REASONER.symmetry_orbit(name)
        if report is None:
            continue
        rows.append(report)
        ok = ok and bool(report["decisions_preserved"])
        if report["weight"] <= 5:
            ok = ok and bool(report["orbit_is_every_word_of_this_weight"])
    return ok and bool(rows), {"concepts": rows}


def _c41_subgroup_census() -> Tuple[bool, object]:
    """Section 8.1: orbits of octads, dodecads and sextets give the orders of
    the three classical maximal subgroups."""
    census = subgroup_census()
    ok = (census["group_order"] == 244823040
          and census["octad_orbit"] == 759
          and census["octad_stabiliser_order"] == 322560
          and census["dodecad_orbit"] == 2576
          and census["dodecad_stabiliser_order"] == 95040
          and census["sextet_orbit"] == 1771
          and census["sextet_stabiliser_order"] == 138240
          and bool(census["matches_expected"]))
    return ok, census


def _c42_carrier_is_derived() -> Tuple[bool, object]:
    """
    Section 5.2: the bit pattern is a derived quantity.

    Three checks.  (i) Every concept in the library shows exactly the word its
    meaning encodes to, and decoding that word returns the meaning.  (ii) The
    derivation is injective on the whole representable box, which is what
    makes the word a faithful view rather than a lossy one: the encoder's
    image has exactly 9^7 words (Claim C11 counts them) and re-deriving a word
    from the meaning it decodes to is the identity on that image.  (iii) A
    concept whose meaning leaves the box has no bits at all, and says so,
    rather than being truncated into a word that would mean something else.
    """
    ok = True
    for c in REASONER.concepts.values():
        ok = ok and c.carrier_is_derived() and c.round_trip_ok()
    # the derived view depends on nothing but the meaning
    same_meaning = (Concept("a", Dimension((2, 1, -2, 0, 0, 0, 0))).carrier
                    == Concept("b", Dimension((2, 1, -2, 0, 0, 0, 0))).carrier)
    # and it follows the meaning when the meaning changes
    base = REASONER.concept("energy")
    assert base is not None
    moved = base.with_meaning(Dimension((4, 1, -4, 0, 0, 0, 0)))
    follows = (moved.carrier != base.carrier and moved.carrier_is_derived())
    # injective, and the identity on the image, sampled across the box
    sampled = 0
    injective = True
    seen: Dict[Tuple[int, ...], Tuple[int, ...]] = {}
    for n in range(0, CARRIER_CAPACITY, 4013):
        dims = DimCarrier.from_int(n)
        assert dims is not None
        word = tuple(DimCarrier.encode(dims))
        injective = injective and seen.setdefault(word, tuple(dims)) == tuple(dims)
        injective = injective and DimCarrier.decode(list(word)) == dims
        sampled += 1
    outside = Concept("outside the box", Dimension((9, 0, 0, 0, 0, 0, 0)))
    honest = (outside.carrier is None and not outside.representable
              and outside.carrier_is_derived())
    # the derived views are read-only: the bits cannot be set behind the
    # meaning's back
    try:
        outside.carrier = [0] * 24        # type: ignore[misc]
        settable = True
    except AttributeError:
        settable = False
    ok = ok and same_meaning and follows and injective and honest and not settable
    return ok, {
        "concepts_checked": len(REASONER.concepts),
        "words_sampled_across_the_box": sampled,
        "derivation_injective_on_sample": injective,
        "same_meaning_same_bits": same_meaning,
        "bits_follow_a_changed_meaning": follows,
        "unrepresentable_meaning_has_no_bits": honest,
        "carrier_is_settable": settable,
    }


def _c43_carrier_cannot_compose() -> Tuple[bool, object]:
    """
    Section 5.2(b) and Proposition 1: composition cannot live on the carrier.

    For every ordered pair of library concepts whose product stays inside the
    representable box, compare the word the GLM derives for the product,
    encode(d1 + d2), with the word an F_2 carrier would have produced,
    word(d1) XOR word(d2).  They almost never agree, so the derived word map
    is not additive and the carrier cannot be the object that composes.  The
    agreements that do occur are exactly the carries-free cases of the base-9
    packing and are counted rather than hidden.

    The second half of the claim is Corollary 1 of Proposition 1, checked
    concretely: any F_2-linear encoder identifies d with d + 2u, so it is not
    injective, and the pairs it confuses are exhibited from the library.
    """
    dims = sorted({q[0].exps for q in QUANTITIES.values()})
    pairs = agree = tested = 0
    for a in dims:
        for b in dims:
            s = tuple(x + y for x, y in zip(a, b))
            if not DimCarrier.in_range(s):
                continue
            pairs += 1
            wa = DimCarrier.encode(list(a))
            wb = DimCarrier.encode(list(b))
            ws = DimCarrier.encode(list(s))
            xor = [x ^ y for x, y in zip(wa, wb)]
            tested += 1
            if xor == ws:
                agree += 1
    # Corollary 1: an F_2 encoder is not injective -- exhibit the collisions
    collisions = []
    for d in dims[:40]:
        shifted = tuple(x + 2 if i == 0 else x for i, x in enumerate(d))
        if mod2_would_accept(Dimension(d), Dimension(shifted)):
            collisions.append({"meaning": str(Dimension(d)),
                               "confused_with": str(Dimension(shifted))})
    ok = (tested > 0 and agree < tested and len(collisions) == len(dims[:40]))
    return ok, {
        "in-box ordered pairs": pairs,
        "pairs where XOR of the words is the word of the product": agree,
        "pairs where it is not": tested - agree,
        "F_2 collisions exhibited (d vs d + 2u)": len(collisions),
        "examples": collisions[:4],
    }


CLAIMS: Tuple[Tuple[str, str, Verifier], ...] = (
    ("C1", "the Golay code has 4096 codewords", _c1_codeword_count),
    ("C2", "its minimum distance is 8", _c2_min_distance),
    ("C3", "W(z) = 1 + 759z^8 + 2576z^12 + 759z^16 + z^24", _c3_weight_enumerator),
    ("C4", "the code is self-dual and doubly even", _c4_self_dual_doubly_even),
    ("C5", "covering radius 4; leader profile 1/24/276/2024/1771", _c5_covering_radius),
    ("C6", "every weight-4 coset has exactly 6 minimal leaders", _c6_ambiguity_at_four),
    ("C7", "the MOG alignment sends all 4096 codewords to hexacode words",
     _c7_mog_alignment),
    ("C8", "the hexacode is [6,3,4] with 64 words", _c8_hexacode),
    ("C9", "196,560 Leech minimal vectors in classes 1104/97152/98304",
     _c9_leech_census),
    ("C10", "the column map F_2^4 <-> GF(4) x Z_4 is a bijection",
     _c10_column_bijection),
    ("C11", "the 24-bit codec round trip loses 0 bits", _c11_codec_round_trip),
    ("C12", "all library concepts survive Z^7 -> bits -> shadow -> Z^7",
     _c12_carrier_lossless),
    ("C13", "1168 of 4,782,969 dimension vectors are lawful", _c13_lawful_census),
    ("C14", "the mod-2 traps are accepted mod 2 and rejected exactly",
     _c14_mod2_corollary),
    ("C15", "the mod-2 ceiling measured over the library and the suite",
     _c15_mod2_measurement),
    ("C16", "target synthesis reproduces known answers, integer and rational",
     _c16_target_synthesis),
    ("C17", "Buckingham-Pi groups are correct and the Pi count holds",
     _c17_pi_theorem),
    ("C18", "code-automorphism membership is decided exhaustively",
     _c18_automorphism_test),
    ("C19", "2^(1+24) relations hold in 4096D and fail in 24D", _c19_extraspecial),
    ("C20", "the snap product is associative (earlier claim corrected)",
     _c20_snap_algebra),
    ("C21", "all arithmetic on the decision path is exact", _c21_exact_arithmetic),
    ("C22", "the expression parser agrees with hand-computed dimensions",
     _c22_parser),
    ("C23", "every +-2 exponent perturbation fools mod 2 and never fools Z^7",
     _c23_mod2_perturbation),
    ("C24", "1.03% of pairs in [-2,2]^7 collapse mod 2; closed form = brute force",
     _c24_mod2_box_census),
    ("C25", "the fibre quaternions satisfy the Q8 relations; the fibre map is "
     "a bijection, not a homomorphism", _c25_versor_layer),
    ("C26", "the ordered fibre product is order-sensitive for part of the "
     "library", _c26_fibre_noncommutativity),
    ("C27", "every closed walk has an integer winding number", _c27_winding),
    ("C28", "holonomy is path-dependent and telescopes exactly", _c28_holonomy),
    ("C29", "the v15-v19 conformal weight is exactly half the syndrome weight",
     _c29_conformal_grading),
    ("C30", "22 syndrome-free dimension vectors in [-2,2]^7, each a codeword",
     _c30_vacua),
    ("C31", "the chromatic ground states are exactly the 4096 codewords",
     _c31_colour),
    ("C32", "196,560 minimal vectors give 98,280 lines; 98,304 = 24 x 4096",
     _c32_leech_lines),
    ("C33", "1 + 299 + 98,280 + 98,304 = 196,884 = 324 + 196,560",
     _c33_dimension_ledger),
    ("C34", "the 300-dimensional Jordan layer is commutative, unital and "
     "non-associative", _c34_jordan_layer),
    ("C35", "the archive's 'Leech inner product' is 24 - 2 x Hamming distance",
     _c35_archive_inner_product),
    ("C36", "2^(1+24) : S_12 acts faithfully and homomorphically on 4096D",
     _c36_semidirect),
    ("C37", "the automorphisms found generate a 5-transitive group of order "
     "244,823,040, transitive on the 759 octads", _c37_m24_group),
    ("C38", "that group is all of Aut(C): the stabiliser of five points has "
     "exactly 48 elements, so Aut(C) = M24", _c38_m24_is_full_aut),
    ("C39", "the stabiliser chain decides membership exactly, agreeing with "
     "the exhaustive codeword test", _c39_stabiliser_chain_is_sound),
    ("C40", "M24 preserves every substrate decision about a carrier word and "
     "is transitive on the words of low weight", _c40_m24_on_concepts),
    ("C41", "orbits on octads, dodecads and sextets give the maximal subgroup "
     "orders 322,560, 95,040 (= |M12|) and 138,240", _c41_subgroup_census),
    ("C42", "the bit pattern is derived: every concept's word is encode(its "
     "meaning), decodes back to it, and cannot be set", _c42_carrier_is_derived),
    ("C43", "composition cannot live on the carrier: the derived word map is "
     "not additive, and no F_2 encoder is injective", _c43_carrier_cannot_compose),
)


# ══════════════════════════════════════════════════════════════════════════════
#  OPERATIONAL RUN
# ══════════════════════════════════════════════════════════════════════════════

def _banner() -> None:
    line = "=" * 78
    print(line)
    print(f"  {PAPER_TITLE}")
    print("  A substrate-native codec and exact reasoner for dimensional knowledge")
    print(line)
    print(f"  author  : {PAPER_AUTHOR}")
    print(f"  version : {PAPER_VERSION}")
    print("  companion implementation : glm_reasoner.py")
    print(line)


def run_paper(quick: bool = False, out_dir: str = "results") -> Dict[str, object]:
    """Verify every claim, run the demonstration, and write the results file."""
    start = time.time()
    _banner()

    print("\nSECTION 2-3.  SUBSTRATE AND CODEC")
    print("-" * 78)
    audit = substrate_audit(full_leech=not quick)
    g = audit["golay"]
    print(f"  Golay      : {g['codewords']} codewords, d = {g['min_distance']}, "
          f"self-dual {g['self_dual']}, {g['octads']} octads")
    print(f"  cosets     : {g['cosets']}, covering radius {g['covering_radius']}, "
          f"leader profile {g['leader_weight_profile']}")
    print(f"  hexacode   : {audit['hexacode']}")
    print(f"  MOG        : {audit['mog_alignment']['failures']} shadow failures "
          f"over 4096 codewords; label fibres {audit['mog_label_fibres']}")
    if not quick:
        lch = audit["leech"]
        print(f"  Leech      : {lch['total']} minimal vectors "
              f"(A {lch['class_A']}, B {lch['class_B']}, C {lch['class_C']}), "
              f"{lch['norm_failures']} norm failures")
    print(f"  carrier    : {CARRIER_CAPACITY} dimension vectors in 2^24 words")

    print("\nSECTION 5.  THE MOD-2 CEILING, MEASURED")
    print("-" * 78)
    collapse = mod2_collapse_report()
    print(f"  distinct dimensions in the library : {collapse['distinct_dimensions']}")
    print(f"  distinct mod-2 shadows             : {collapse['distinct_mod2_shadows']}")
    print(f"  pairs confused by an XOR substrate : "
          f"{collapse['pairs_indistinguishable_mod2']} of "
          f"{collapse['unordered_pairs']} "
          f"({100 * collapse['mod2_false_positive_rate']:.1f}%)")
    print("  pairs confused by (Z^7,+)          : 0 (0.0%)")
    collisions = dimensional_collisions()
    print(f"  genuine dimensional collisions     : {len(collisions)} groups "
          f"(reported, not resolved)")

    print("\nSECTION 6.  THE REASONER (see glm_reasoner.py for the API)")
    print("-" * 78)
    batch = REASONER.audit_many(DEMO_EQUATIONS)
    print(f"  curated equations audited          : {batch['total']}")
    print(f"    accepted (dimensionally true)    : {batch['accepted']}")
    print(f"    rejected                         : {batch['rejected']}")
    print(f"    (appendix) accepted by an F_2    : "
          f"{REASONER.mod2_ceiling_batch(DEMO_EQUATIONS)['mod2_false_positives_prevented']}")
    solved = {"integer": 0, "fractional": 0, "impossible": 0}
    for target, inputs in DEMO_QUERIES:
        solved[REASONER.solve(target, list(inputs)).status] += 1
    print(f"  synthesis queries                  : {len(DEMO_QUERIES)} "
          f"({solved['integer']} integer, {solved['fractional']} rational, "
          f"{solved['impossible']} no pathway)")

    print("\nSECTIONS 9-10.  THE OPTIONAL LAYERS (never on the decision path)")
    print("-" * 78)
    grading = conformal_grading_report()
    walks = winding_report()
    colours = colour_report()
    print(f"  H^6 norm^2 is 6 for all {grading['tested']} concepts, so the "
          f"v15-v19 L0 is sigma/2 : {grading['archive_L0_equals_half_syndrome']}")
    print(f"  closed walks with integral winding : "
          f"{walks['closed_walks']}/{walks['closed_walks']} "
          f"(windings observed {walks['windings']})")
    print(f"  chromatic ground states            : {colours['ground_states']} "
          f"(one colour in {colours['ground_state_fraction_one_in']})")
    if not quick:
        ledger = dimension_ledger()
        print(f"  Griess ledger                      : 1 + "
              f"{ledger['traceless_sym_dim']} + {ledger['lines']} + "
              f"{ledger['tensor']} = {ledger['total']}")

    print("\nCLAIM VERIFICATION")
    print("-" * 78)
    results: List[Dict[str, object]] = []
    passed = 0
    for cid, statement, verifier in CLAIMS:
        if quick and cid in ("C9", "C13", "C32", "C33"):
            print(f"  {cid:<5} SKIP  {statement}")
            results.append({"id": cid, "statement": statement,
                            "passed": None, "evidence": "skipped (--quick)"})
            continue
        ok, evidence = verifier()
        passed += 1 if ok else 0
        print(f"  {cid:<5} {'PASS' if ok else 'FAIL'}  {statement}")
        results.append({"id": cid, "statement": statement,
                        "passed": ok, "evidence": evidence})
    checked = sum(1 for r in results if r["passed"] is not None)
    print("-" * 78)
    print(f"  {passed}/{checked} claims verified"
          + ("  (some skipped in quick mode)" if quick else ""))

    elapsed = time.time() - start
    payload: Dict[str, object] = {
        "title": PAPER_TITLE,
        "author": PAPER_AUTHOR,
        "version": PAPER_VERSION,
        "companion": "glm_reasoner.py",
        "quick_mode": quick,
        "elapsed_seconds": round(elapsed, 2),
        "substrate": audit,
        "mod2_ceiling": collapse,
        "dimensional_collisions": collisions,
        "equation_audit": {k: v for k, v in batch.items() if k != "records"},
        "equation_records": batch["records"],
        "synthesis": solved,
        "claims": results,
        "claims_passed": passed,
        "claims_checked": checked,
    }
    path = Path(out_dir)
    path.mkdir(parents=True, exist_ok=True)
    target = path / "glm_results.json"
    with open(target, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, default=str)
    print(f"\n  results written to {target}")
    print(f"  total run time {elapsed:.1f} s")
    print("=" * 78)
    return payload


def main(argv: List[str]) -> int:
    quick = "--quick" in argv
    payload = run_paper(quick=quick)
    return 0 if payload["claims_passed"] == payload["claims_checked"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
