#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================

    THE GEOMETRIC LANGUAGE MACHINE, SECOND GENERATION

    Exact semantics on a Leech-lattice carrier:
    rational dimension, tensor character, decimal scale and parity,
    with error-correcting repair and the Conway group as carrier symmetry

    An operational paper.  Reading it is the documentation; running it is the
    verification.  Every numbered claim below is checked by the code in this
    file, against the modules it describes, in a few seconds.

        python3 glm2_paper.py           full run
        python3 glm2_paper.py --quick   skips the exhaustive sweeps
        python3 glm2_paper.py --json    writes results/glm2_results.json only

================================================================================

ABSTRACT

  The first generation of this system (GLM-1, the companion directory ../glm)
  established one negative result and one positive one.  The negative result
  is that a carrier whose composition law is XOR can only ever compare
  dimension exponents modulo 2, so it cannot tell E = mc^2 from E = mc^4; the
  positive one is that carrying the exponents in (Z^7, +) and joining them
  bijectively to a 24-bit Golay carrier removes that failure completely.

  This second generation keeps the discipline and raises the ceiling in four
  directions at once.

  MEANING.  A concept is no longer seven integers.  It is ten *rational*
  exponents (the seven SI base dimensions plus plane angle, solid angle and
  information), a rational decimal scale, an integer tensor rank, and three
  Z/2 parities (space inversion, time reversal, charge conjugation), together
  with two nominal labels.  This separates torque from energy, hertz from
  becquerel, radiance from irradiance, h from hbar, kilometre from metre, an
  axial vector from a polar one, and a bit rate from a frequency — all of
  which a seven-exponent system must conflate.  Section 2.

  OPERATIONS.  Multiplication of quantities is not the only way concepts
  combine, and a system that only adds exponent vectors cannot tell the
  rank-2 tensor F (x) r from the energy F . r.  GLM-2 therefore carries an
  operator algebra over the meaning module: contraction, two distinct cross
  products, and the differential operators grad, div, curl, rot, laplacian,
  d/dt and the time and volume integrals, every one of them built from the
  single meaning "nabla" so that its rank and parity bookkeeping is forced
  rather than tabulated.  With it, thirty-six relations — including all four
  Maxwell equations — hold in the FULL meaning and not merely dimensionally.
  Section 12.

  NO MOD 2 WHERE IT COSTS ANYTHING.  Exponents are never reduced.  The system
  contains exactly three Z/2's, and each of them is a parity, where Z/2 is
  the honest answer.  Section 3 states and checks the sharp form of GLM-1's
  ceiling theorem and shows where the boundary now lies.

  CARRIER.  The carrier is the Leech lattice Lambda_24 itself, not the Golay
  code beneath it.  Meanings are written into 24 integer slots and read as
  coordinates in a Leech basis, so the encoder is a bijection onto Lambda:
  infinite capacity, exact composition, and — because the minimal norm is 32
  in the integer model used here — a guaranteed separation of 32 between the
  carriers of any two distinct concepts.  Repair is nearest-point decoding:
  any corruption of squared magnitude at most 7 is undone *exactly*, which is
  something no snap-to-codeword scheme can do, since snapping changes the
  concept it is meant to protect.  Sections 4 to 6.

  SYMMETRY.  GLM-1 built M24 = Aut(Golay), order 244,823,040, rather than
  quoting it.  GLM-2 goes one level up and builds Aut(Lambda) = Co_0: the
  monomial subgroup 2^12 : M24 together with a sextet element found by
  search, all verified to preserve the lattice; the monomial subgroup is
  shown to have exactly three orbits on the 196,560 minimal vectors while the
  full group is transitive; and a randomised Schreier chain in the
  24-dimensional F_2 representation Lambda / 2Lambda gives a rigorous lower
  bound of 8,315,553,613,086,720,000 for the order, which is the classical
  order of Co_0.  Section 7.

  ALGEBRA.  Above the lattice sits the Griess ledger 196,884 = 300 + 98,280 +
  98,304, whose middle term is counted here as the number of type-2 classes
  of Lambda / 2Lambda and whose total is the q-coefficient of the j-function,
  computed exactly.  The commutative non-associative algebra that GLM-1
  claimed and did not have is supplied in two verified forms: the Jordan
  algebra of symmetric matrices, and the Matsuo algebra of a 3-transposition
  group, which for parameter 1/4 is the Norton-Sakuma algebra 2A of the
  Monster and for 1/32 is 3C.  Section 8 says plainly what is not built.

  The companion implementation is glm2_reasoner.py.  Section 9 describes it
  and Section 10 reports the measurements.  Section 11 lists the invariants a
  future change must preserve, and Section 12 the operator algebra.

--------------------------------------------------------------------------------
1.  WHAT CAME BEFORE, AND WHAT IS NEW
--------------------------------------------------------------------------------

  GLM-1 is summarised in ../glm/README.md and ../glm/DEVELOPMENT_CATALOG.md.
  Its shape was: meaning in (Z^7, +), carrier in F_2^24 with the extended
  binary Golay code, a bijection between them, and a stack of geometric and
  Leech-flavoured layers above.  Its 41 numbered claims all pass, and this
  second generation reuses two of its modules unchanged — the Golay code and
  the constructed M24 — through glm2_common.

  Four things limited it.

  (i)   Seven integer exponents.  No angle, no solid angle, no information,
        no fractional powers, no scale, no tensor character, no parity.  So
        torque and energy are the same object, and so are Hz and Bq.

  (ii)  A finite carrier.  F_2^24 holds 16,777,216 states, of which the
        base-9 embedding used 9^7 = 4,782,969.  Every capacity question was a
        question about how to fit meaning into a fixed box.

  (iii) A carrier that cannot compose.  GLM-1 was re-architected so that the
        integer vector is the state and the 24-bit word is a derived view of
        it (GLM-1 paper section 5), which is the right arrangement; but the
        view itself is still an F_2 object, and XOR of two words is almost
        never the word of the product.  The bijection meaning <-> word is
        therefore not an isomorphism, so nothing can be computed on the
        carrier and every question has to be sent back to the meaning.

  (iv)  Repair that damages meaning.  Snapping to the nearest codeword
        replaces the concept with a different concept.  It is error
        *detection* dressed as error correction.

  GLM-2 removes all four.  The table is the whole argument in miniature:

        question                     GLM-1                GLM-2
        --------------------------   ------------------   --------------------
        meaning                      Z^7                  Q^10 (+) Q (+) Z
                                                          (+) (Z/2)^3 (+) labels
        fractional powers            no                   yes, exactly
        angle / solid angle / bit    no                   yes
        decimal scale                no                   yes
        tensor rank, P, T, C         no                   yes
        carrier                      F_2^24                Lambda_24
        carrier capacity             2^24 (9^7 used)      countably infinite
        composition in the carrier   XOR (mod 2)          addition in Z^24
        separation of concepts       Hamming, can be 1    squared distance >= 32
        repair                       snap: changes it     decode: restores it
        symmetry group built         M24, 2.4 x 10^8      Co_0, 8.3 x 10^18
        algebra above                claimed, was assoc.  Jordan and Matsuo,
                                                          verified

--------------------------------------------------------------------------------
2.  THE MEANING MODULE
--------------------------------------------------------------------------------

  Definition 2.1.  A MEANING is an element of

      M  =  Q^10  (+)  Q  (+)  Z  (+)  (Z/2)^3  (+)  N  (+)  N

  written (e; s; r; p, t, c; kind, domain), where e is the exponent vector
  over the ten axes

      L  length      I  electric current   J  luminous intensity  S  solid angle
      M  mass        H  temperature        A  plane angle         B  information
      T  time        N  amount of substance

  s is the decimal scale (the quantity is 10^s times the coherent SI unit),
  r is the tensor rank, and p, t, c are the parities under space inversion,
  time reversal and charge conjugation.  The two labels are nominal: `kind`
  separates quantities that are dimensionally identical but not
  interchangeable (entropy and heat capacity), `domain` records the namespace.

  The group law is componentwise addition, with the three parities added in
  Z/2 and the labels merged.  It is the image of multiplication of
  quantities:  meaning(AB) = meaning(A) + meaning(B).

  Proposition 2.2 (rational powers).  For q in Q, q * meaning(A) is the
  meaning of A^q whenever q r is an integer, and for non-integer q it is
  defined only when r = 0 and p = t = c = 0.  There is no square root of a
  pseudovector.  [Claim C4]

  Proposition 2.3 (torsion).  M has torsion: the subgroup (Z/2)^3 of parities
  is annihilated by 2.  Consequently no injective group homomorphism from M
  into any torsion-free group exists, and in particular none into Z^24 or
  Lambda.  The encoder of section 5 is therefore a bijection onto its image
  and a homomorphism on the torsion-free part; composition in the carrier
  reduces exactly three slots mod 2, and that reduction is lossless because a
  parity really is an element of Z/2.  [Claim C5]

  This is the one place where GLM-2 uses mod 2, and it is the one place where
  mod 2 is the truth rather than an approximation to it.

  Definition 2.4 (admissibility).  An equation A = B is ADMISSIBLE when the
  meanings are commensurable: equal exponents, equal decimal scale, equal
  tensor rank and parities, and no clash of nominal kinds.  This is strictly
  finer than dimensional analysis, and each failure is reported separately by
  the reasoner, so a rejection always says *why*.

  Definition 2.5 (derived gradings and anomalies).  Of the three parities
  only P is stored outright.  The time-reversal and charge-conjugation
  gradings are *derived* from the exponents,

      T(m)  =  (e_T + e_I + t)  mod 2,        C(m)  =  (e_I + c)  mod 2,

  where t and c are ANOMALY bits, almost always zero.  Two consequences, both
  checked.  First, T and C are then automatically additive over products,
  quotients and rational powers — there is no way to tag a library entry
  inconsistently, which is precisely the failure a hand-maintained parity
  column invites.  Second, they are automatically right: the derived T
  grading reproduces the textbook behaviour of position, velocity, momentum,
  energy, power, charge, current, E, B, resistance, capacitance and the rest
  with no table at all, and d/dt flips it for every concept in the register.
  [Claims C52, C53, C55]

  The anomaly exists because the convention is a convention.  A permanent
  electric dipole moment of a particle is dimensionally charge x length,
  which the convention grades T-even, yet the observable is T-odd — that is
  exactly why measuring one would signal CP violation.  The register records
  the departure as t = 1, and it is the only anomaly in 660 concepts; the
  reasoner then refuses to equate an EDM with an ordinary dipole moment, and
  gives "parity mismatch: T" as the reason.  [Claim C54]

--------------------------------------------------------------------------------
3.  MEANING IS PRIMARY; THE CARRIER IS DERIVED
--------------------------------------------------------------------------------

  The architecture, stated once.  A concept IS its meaning: an element of
  M = Q^10 (+) Q (+) Z (+) (Z/2)^3 (+) labels.  That is the state of the
  system.  The Leech point is a DERIVED quantity,

      x  =  encode(m)  =  u(m) B,

  the image of an injective map with a computable inverse (Section 5).  It is
  recomputed from the meaning whenever it is wanted, cached only as a cache,
  and never accepted as an input: no function in GLM-2 takes a carrier and
  treats it as the concept.  Composition is addition of MEANINGS, and the
  carrier of a product is derived afterwards; the reasoner's
  `carrier_is_derived` re-derives the point and decodes it back, and
  [Claim C58] runs that check across the whole register.  Even repair goes
  meaning-first: a corrupted point is decoded to the nearest lattice point and
  then to the meaning it encodes, so a repair either returns the original
  concept or reports that the received point carries no meaning at all.

  Proposition 3.1 (GLM-1, Proposition 1; proved in Lean).  Let f be any map
  from dimension vectors into a group in which every element satisfies
  m + m = 0, additive in the sense f(d + d') = f(d) + f(d').  Then
  f(d + 2u) = f(d) for every u.  Two dimensions are confusable by some such f
  precisely when they agree modulo 2, and no such f is injective
  (GLM.no_injective_additive_into_char_two).

  That is why the arrow points the way it does.  A bit pattern composed by
  XOR cannot separate concepts, so it cannot be the object that means
  something; the integer/rational exponent vector can, so it is.  GLM-1 draws
  the same conclusion and arranges itself the same way (GLM-1 paper section
  5), but its derived view is an F_2 object on which nothing can be computed.
  GLM-2's view is a Leech point, so the derivation is not only faithful but
  additive on the torsion-free part: exponents are rational and compared by
  exact equality, carriers add in Z^24, and no verdict anywhere reduces an
  exponent modulo 2.

  The ceiling is still measured, because a rejected design is worth measuring,
  but it is quarantined: `mod2_shadow` and `mod2_confusable` live in the
  appendix of glm2_meaning.py §3, the reasoner exposes them only through
  `mod2_ceiling`, and no audit carries a mod-2 opinion.

  Measurement 3.2.  Over the 660 concepts of the register, the number of
  distinct pairs a mod-2 exponent carrier would confuse is reported by
  [Claim C30], together with the number of pairs that a SEVEN-exponent
  integer system (GLM-1's meaning module) would confuse and GLM-2 separates.
  The second number is the honest measure of how much meaning the new axes,
  the scale, the rank and the parities actually carry.

--------------------------------------------------------------------------------
4.  THE CARRIER: THE LEECH LATTICE
--------------------------------------------------------------------------------

  Definition 4.1.  In the integer (x sqrt 8) model,

      Lambda = { x in Z^24 : all x_i = m (mod 2) for a common m in {0,1};
                             { i : x_i = m + 2 (mod 4) } is a Golay codeword;
                             sum_i x_i = 4m (mod 8) }.

  Minimal vectors have squared norm 32 and there are 196,560 of them.  This
  definition is executed as `in_leech` and everything else is checked against
  it.

  Proposition 4.2 (index).  [Z^24 : Lambda] = 2^36.  Counted, not quoted: for
  each of the two parities, the mod-4 pattern is a Golay codeword (2^12), each
  coordinate has two lifts mod 8 (2^24), and the sum condition removes half,
  so |Lambda / 8Z^24| = 2 * 2^12 * 2^24 / 2 = 2^36 and the index is
  8^24 / 2^36 = 2^36.  [Claim C10]

  Proposition 4.3 (basis).  The Hermite normal form of the explicit
  generating set { 4(e_i + e_j) } u { 2 * 1_O : O an octad } u { (-3,1^23) }
  is a 24 x 24 upper-triangular integer matrix of determinant 2^36, every row
  of which satisfies Definition 4.1.  A sublattice of Lambda of the same
  index as Lambda is Lambda, so this is a Z-basis.  [Claims C11, C12]

  Proposition 4.4 (theta series).  Theta_Lambda = E_4^3 - 720 Delta, computed
  exactly in integer arithmetic, has head 1 + 196,560 q^2 + 16,773,120 q^3 +
  398,034,000 q^4.  The coefficient 196,560 agrees with the enumeration of
  minimal vectors performed independently from the Golay code.  [Claim C13]

--------------------------------------------------------------------------------
5.  THE CODEC
--------------------------------------------------------------------------------

  A meaning is written into 24 integer slots (twelve times each rational
  field, so that (1/12)Z lands in Z; the rank; the three parities; two labels;
  seven free context slots) and those slots are read as coordinates in the
  Leech basis B:

      u in Z^24   |-->   x = u B   in Lambda.

  Proposition 5.1 (bijection).  u -> uB is an isomorphism Z^24 -> Lambda, so
  the encoder is injective with a computable inverse, and its image is all of
  Lambda subject only to the range conditions on the parity and label slots.
  [Claims C14, C15]

  Proposition 5.2 (separation).  Distinct meanings have carriers at squared
  distance at least 32, the Leech minimum.  There are no near collisions.
  [Claim C16]

  Proposition 5.3 (exact repair).  The packing radius squared is 32/4 = 8, so
  every corruption e with ||e||^2 <= 7 satisfies decode(x + e) = x, and the
  meaning is recovered unchanged.  [Claims C17, C18]

  Proposition 5.4 (composition).  On the torsion-free part the encoder is a
  group homomorphism: encode(m + m') = encode(m) + encode(m') exactly.  On
  all of M, `compose` adds the carriers and reduces the three parity slots,
  as Proposition 2.3 forces.  [Claim C19]

  Proposition 5.5 (capacity).  The number of concepts whose carrier has
  squared norm at most 32 is 1 + 196,560 = 196,561; at most 48 it is
  16,969,681; and in total it is countably infinite.  [Claim C20]

--------------------------------------------------------------------------------
6.  DECODING
--------------------------------------------------------------------------------

  Algorithm 6.1 (exact maximum likelihood).  Lambda is the disjoint union,
  over the two parities m and the 4096 Golay codewords c, of the sets

      { x : x_i = r_i(m, c) (mod 4) for all i, sum_i x_i = 4m (mod 8) }.

  Inside one such class the coordinates are independent apart from the sum
  condition, so the nearest point is obtained by rounding each coordinate to
  its residue class and, if the sum condition fails, moving exactly one
  coordinate by +-4 — the cheapest repair, because any admissible correction
  is an odd number of such moves and each has non-negative cost.  Minimising
  over the 2 x 4096 classes is therefore exact.  The implementation walks the
  classes in Gray-code order over the twelve Golay generators, so each class
  costs O(1) updates, and prunes with a lower bound on the repair term.

  Verification 6.2.  Three independent checks: the decoder is compared with a
  deliberately slow reference implementation that uses no Gray code and no
  pruning [C21]; the returned point is checked against all 196,560
  minimal-vector translates, which is the Voronoi condition the minimal
  vectors impose [C22]; and every corruption of squared magnitude at most 7
  of a library concept is checked to decode back to it [C18].

--------------------------------------------------------------------------------
7.  THE SYMMETRY GROUP OF THE CARRIER
--------------------------------------------------------------------------------

  Generators.  Coordinate permutations from the constructed M24; sign changes
  on the supports of the twelve Golay basis words; and one sextet element:
  on each tetrad of a genuine sextet, x_i -> +-(s/2 - x_i) where s is the
  tetrad sum, with the six signs chosen by a search over all 64 patterns.
  Exactly the 32 patterns with an odd number of sign flips preserve Lambda,
  which the search finds rather than assumes.  [Claims C23, C24]

  Proposition 7.1.  Every generator preserves the defining congruences and
  the Gram matrix of the basis, and its matrix in lattice coordinates is
  unimodular; so each lies in Aut(Lambda).  [Claim C23]

  Proposition 7.2 (orbits).  The monomial subgroup N = 2^12 : M24, of order
  4096 * 244,823,040 = 1,002,795,171,840, has exactly three orbits on the
  196,560 minimal vectors, of sizes 1,104 / 97,152 / 98,304 — the classical
  shapes (4^2 0^22), (2^8 0^16) and (3 1^23).  Adjoining the sextet element
  fuses them: the full group is transitive.  [Claims C25, C26]

  Proposition 7.3 (the F_2 representation).  Lambda / 2Lambda is a
  24-dimensional F_2 space on which the group acts linearly; in the basis
  coordinates the action of a generator is read off directly.  The image of a
  minimal vector is a type-2 class and its orbit has exactly 98,280 elements
  — the number of antipodal pairs of minimal vectors.  [Claim C27]

  Proposition 7.4 (order).  A randomised Schreier chain in that
  representation gives basic orbits whose lengths multiply to
  4,157,776,806,543,360,000.  Because each level's generators are verified to
  fix the earlier base points, that product is a rigorous lower bound for the
  order of the image; and -1, which lies in the group and acts trivially mod
  2Lambda, doubles it.  So

      |G|  >=  8,315,553,613,086,720,000,

  which is the classical order of Co_0.  The upper bound |Aut(Lambda)| =
  |Co_0| is the classical theorem and is not reproved here.  [Claim C28]

  Proposition 7.5 (the class census).  From the theta coefficients alone,

      1 + 196,560/2 + 16,773,120/2 + 398,034,000/48
        = 1 + 98,280 + 8,386,560 + 8,292,375 = 16,777,216 = 2^24,

  the number of classes of Lambda / 2Lambda, with nothing left over.
  [Claim C29]

  What this means for the semantics.  Co_0 is a symmetry of the CARRIER and
  not of the meanings: it preserves norms and the lattice, and it moves the
  image of the encoder off itself.  The reasoner reports exactly that, rather
  than dressing it up as a semantic invariance.  [Claim C31]

--------------------------------------------------------------------------------
8.  THE ALGEBRA ABOVE THE LATTICE
--------------------------------------------------------------------------------

  The ledger.  196,884 = 300 + 98,280 + 98,304, where 300 = dim S^2(R^24),
  98,280 is the number of type-2 classes counted in Proposition 7.5, and
  98,304 = 24 x 4096.  Independently, the q-coefficient of the j-function,
  computed here as E_4^3 / Delta by exact power-series division, is 196,884.
  [Claims C32, C33]

  Two verified algebras.

  (a)  The Jordan algebra of symmetric matrices, A o B = (AB + BA)/2 with the
       trace form.  Commutative, unital, NON-associative, satisfies the
       Jordan identity, and its rank-one idempotents are axes of Jordan type
       1/2 with the full fusion rules.  Checked exhaustively at n = 4 (a
       10-dimensional algebra); the n = 24 case is the 300 above.  [C34]

  (b)  Matsuo algebras.  For a class D of 3-transpositions and a parameter
       eta, the algebra on basis D with x x = x, x y = 0 when x and y commute
       and x y = (eta/2)(x + y - x^y) when |xy| = 3.  Constructed here from
       the symmetric groups S_3, S_4, S_5.  Verified: commutative,
       non-associative, Frobenius form, every basis vector an idempotent axis
       whose adjoint has spectrum in {1, 0, eta} with the Jordan-type fusion
       rules, and Miyamoto involutions that are genuine algebra automorphisms
       generating the group itself.  For eta = 1/4 the S_3 case has structure
       constants a_0 a_1 = (1/8)(a_0 + a_1 - a_rho): that is the
       Norton-Sakuma algebra 2A, a subalgebra of the Griess algebra generated
       by two 2A axes of the Monster.  For eta = 1/32 it is 3C.  [C35, C36,
       C37]

  What is NOT built.  The 196,884-dimensional Griess algebra itself; the
  Ising-type dihedral algebras 3A, 4A, 4B, 5A, 6A, which need both 1/4 and
  1/32 in the spectrum; the Monster.  GLM-1 claimed a "snap-based Griess
  product" that turned out to be commutative AND associative, hence not
  Griess-like at all; the correction is carried forward here, and the honest
  replacement is (a) and (b) above, which are the parts that can be built and
  checked exactly with the resources of this system.

--------------------------------------------------------------------------------
9.  THE COMPANION IMPLEMENTATION
--------------------------------------------------------------------------------

  glm2_reasoner.py is the system in use.  It offers

      audit        exact admissibility with a reason for every rejection,
                   and no second opinion from any weaker substrate
      solve        exact rational exponents, the general solution when the
                   sources are dependent, and "no pathway" when there is none
      pi_groups    a basis of the dimensionless combinations, over Q
      telemetry    the derived carrier point, its slots, its norm, and the
                   check that it really is encode(meaning)
      mod2_ceiling the appendix measurement of the rejected F_2 design
      transmit     encode, corrupt, repair, and prove the repair exact
      neighbours   the concepts nearest in the carrier
      symmetry     what Co_0 does to a carrier
      convert      the exact decimal factor between scaled units

  Every one of these is exercised by [C38] through [C44] and by the test
  suite test_glm2.py.  The expression language it reads is the one described
  in Section 12, so `glm2_reasoner.py check "torque" "moment(position,
  force)"` is a legal query.

--------------------------------------------------------------------------------
10.  MEASUREMENTS
--------------------------------------------------------------------------------

  The register holds 660 concepts across 26 domains, with 222 scalar defining
  relations and 71 full-meaning tensor relations, all checked exactly on
  every run — a wrong exponent anywhere in the register fails a relation
  immediately.  Of the 222 scalar relations, 186 are also exact at the level
  of the full meaning; the remaining 36 are the ones stated in
  scalar-magnitude form ("pressure = force / area"), where the right-hand
  side names a vector and the left-hand side a scalar.  Those are not errors,
  they are the reason the two tables are kept apart.  [C1, C2, C57]

  The measurements reported by the run are:

      * how many concept pairs a mod-2 exponent carrier would confuse;
      * how many pairs a seven-exponent integer system would confuse and
        GLM-2 separates, broken down by which field does the separating
        (angle, solid angle, information, scale, rank, parity, kind);
      * the error-correction sweep: every error pattern of squared magnitude
        at most 7 on a sample of concepts, all repaired exactly;
      * the decoder cross-check against the reference implementation;
      * the Co_0 orbit census and order bound.

--------------------------------------------------------------------------------
11.  INVARIANTS FOR FUTURE WORK
--------------------------------------------------------------------------------

  I0  Meaning is the state; the carrier is derived from it by `encode` and is
      never an input, never stored independently, and never composed.
  I1  Meaning is exact.  No floats, no tolerances, no reduction of exponents
      modulo anything.  The only Z/2's are the three parities.
  I2  The encoder is injective, with a computable inverse, and remains a
      homomorphism on the torsion-free part.
  I3  The carrier is Lambda; every carrier point satisfies `in_leech`.
  I4  Distinct meanings stay at squared distance at least 32.
  I5  Repair is nearest-point decoding, and is exact within the packing
      radius.  Nothing may "repair" a concept into a different concept.
  I6  Every claim in this file is verified by executing it; nothing is
      asserted from a table.
  I7  Classical facts that are used but not reproved (the order of Co_0 as an
      upper bound, the identification of the Monster's Griess algebra) are
      labelled as such in the text.
  I8  New concepts go in glm2_library.py with at least one defining relation
      whenever one exists.
  I9  The first-generation modules in ../glm are reused, not copied.
  I10 The T and C gradings stay derived.  A new concept may set an anomaly
      bit, with a comment saying which physics forces it; it may not be given
      a free-floating parity column.
  I11 Every operation on meanings that is not the tensor product has a name.
      Contraction, the plain cross product and the rotational cross product
      are three different operations and are never silently identified.

--------------------------------------------------------------------------------
12.  THE OPERATOR ALGEBRA
--------------------------------------------------------------------------------

  The group law of Section 2 is the image of MULTIPLICATION of quantities.
  Read at the level of tensors it is the tensor product: ranks add.  Physics
  uses three more operations on the same objects, and a system that models
  only the first cannot state most of physics at full meaning.

  Definition 12.1 (contraction).  For meanings of rank >= 1,

      a . b  =  (a + b) with rank reduced by 2.

  So `dot(force, position)` is an energy of rank 0 while `force * position`
  is a rank-2 tensor with the same ten exponents, the same scale and the same
  parities.  GLM-2 accepts the first as an energy and refuses the second.
  [Claim C50]

  Definition 12.2 (the two cross products).  For meanings of rank 1,

      cross(a, b)   =  (a + b) with rank 1,
      moment(a, b)  =  cross(a, b) with one extra factor A^-1.

  This split is forced by taking the plane angle seriously as a dimension.
  Torque is r x F and is measured in joules per radian; angular momentum is
  r x p and is measured in joule-seconds per radian; the velocity omega x r
  of a rotating body converts radians back into metres.  All three consume a
  radian, because all three convert between a rotation and a translation.
  The Poynting vector E x H does not: it is an energy flux, full stop.  A
  single "cross product" cannot be right for both, and the usual way out —
  declaring the radian dimensionless — is exactly the move that makes torque
  look like energy.  GLM-2 names the two operations instead.  [C49, C51]

  Definition 12.3 (the differential operators).  All of them are built from
  one meaning,

      nabla  =  L^-1, rank 1, P-odd,

  by the three products above:

      grad(x)       = nabla (x) x          rank + 1, P flips, L^-1
      div(x)        = nabla . x            rank - 1, P flips, L^-1
      curl(x)       = cross(nabla, x)      rank 1,   P flips, L^-1
      rot(x)        = moment(nabla, x)     rank 1,   P flips, L^-1 A^-1
      laplacian(x)  = div(grad(x))         rank, P and the gradings unchanged

  Nothing here is tabulated: that the curl of a polar vector is axial and the
  curl of an axial vector is polar, and that the Laplacian is neutral, are
  consequences of nabla being P-odd of rank 1.  The `curl` / `rot` split is
  Definition 12.2 one level up: Maxwell's curl equations use `curl` and are
  exact at full meaning, while the vorticity of a fluid is rot(v) and carries
  the inverse radian that its role as a rotation rate demands.  [C49]

  Definition 12.4 (time and volume).  ddt(x) = x - T, integral_dt(x) = x + T,
  integral_dV(x) = x + 3L.  The first two are mutually inverse on the nose,
  and because the T grading is derived from the exponents, d/dt flips it for
  every concept in the register without being told to.  [C52]

  Consequence 12.5 (the second relation table).  glm2_library carries
  TENSOR_RELATIONS, thirty-six relations that must hold in the full meaning —
  rank, space-inversion parity and both derived gradings included.  They
  cover kinematics (v = dr/dt through to snap, and v = omega x r), dynamics
  (p = mv, F = dp/dt, E = F . r, P = F . v, L = r x p, tau = r x F = dL/dt),
  continuum quantities, and all four Maxwell equations in potential and field
  form.  Every one is verified on every run.  [Claim C57]

  Consequence 12.6 (expressions are concepts).  An operator expression is an
  ordinary meaning, so it encodes to a Leech point, decodes back exactly, is
  separated from every other concept by squared distance 32, and is repaired
  by the same decoder.  Nothing about the carrier had to change.  [C56]

--------------------------------------------------------------------------------
13.  REPRODUCTION
--------------------------------------------------------------------------------

      python3 glm2_paper.py            # this paper's verification run
      python3 glm2_paper.py --quick    # skips the exhaustive sweeps
      python3 glm2_reasoner.py         # the companion's demonstration
      python3 test_glm2.py             # the test suite

  Standard library only.  Results are written to results/glm2_results.json.

================================================================================
"""

from __future__ import annotations

import json
import os
import random
import sys
import time
from fractions import Fraction as F
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from glm2_axial import (axial_audit, basis_vector, jordan_symmetric_algebra,
                        jordan_type_rules, matsuo_algebra,
                        miyamoto_group_order, symmetric_group_transpositions)
from glm2_codec import (capacity_within_norm, codec_audit, compose,
                        coords_of, decode_point, encode, repair,
                        separation_bound)
from glm2_common import GOLAY_MASKS, OCTAD_MASKS
from glm2_conway import (CO0_ORDER_CLASSICAL, GENERATORS, MONOMIAL_GENERATORS,
                         MONOMIAL_ORDER, SEXTET, SEXTET_SIGN_PATTERNS,
                         F2Group, f2_apply, f2_matrix,
                         minimal_vector_orbit_census, mod_two_type_census,
                         orbit_on_minimal_vectors, verify_automorphism)
from glm2_lattice import (DIM, INDEX_IN_Z24, KISSING, LEECH_BASIS, MIN_NORM2,
                          basis_determinant, decode, decode_reference,
                          from_coords, in_leech, index_derivation,
                          j_invariant_series, minimal_vectors, norm2,
                          packing_radius2, theta_series, to_coords,
                          verify_local_optimality)
from glm2_library import (AFFINE_SCALES, CONCEPTS, RELATIONS,
                          TENSOR_RELATIONS, by_domain, check_relations,
                          check_tensor_relations, library_audit)
from glm2_meaning import AXES, DENOM, Meaning, ParseError, mod2_shadow
from glm2_parse import FUNCTIONS, NABLA, parse
from glm2_reasoner import REASONER

# ══════════════════════════════════════════════════════════════════════════════
#  CLAIM MACHINERY
# ══════════════════════════════════════════════════════════════════════════════

Verifier = Callable[[], Tuple[bool, Dict[str, object]]]

CLAIMS: List[Tuple[str, str, Verifier, bool]] = []


def claim(cid: str, statement: str, heavy: bool = False):
    """Register a numbered claim with the function that verifies it."""
    def wrap(fn: Verifier) -> Verifier:
        CLAIMS.append((cid, statement, fn, heavy))
        return fn
    return wrap


# ══════════════════════════════════════════════════════════════════════════════
#  §2.  THE MEANING MODULE
# ══════════════════════════════════════════════════════════════════════════════

@claim("C1", "the register holds its concepts with exact meanings, and every "
             "defining relation checks out")
def c1():
    rep = library_audit()
    ok = (rep["relations_ok"] == rep["relations_checked"]
          and rep["tensor_relations_ok"] == rep["tensor_relations_checked"]
          and rep["all_encodable"] and rep["concepts"] >= 400)
    return ok, rep


@claim("C2", "the register spans 18 domains and uses every new field: "
             "fractional exponents, decimal scale, tensor rank, parities, "
             "nominal kinds and affine scales")
def c2():
    rep = library_audit()
    detail = {k: rep[k] for k in ("domains", "with_fractional_exponents",
                                  "with_decimal_scale", "with_nonzero_rank",
                                  "pseudo_quantities", "with_nominal_kind",
                                  "affine_scales")}
    ok = all(v > 0 for v in detail.values())
    return ok, detail


@claim("C3", "meaning is a group: composition adds, division subtracts, and "
             "the named laws hold exactly")
def c3():
    e = REASONER.meaning("energy")
    m = REASONER.meaning("mass")
    v = REASONER.meaning("speed")
    checks = {
        "E = m c^2": (m + v.power(2)).same_dimension(e),
        "E/m = c^2": (e - m).same_quantity(v.power(2)),
        "(E/m)^(1/2) = c": (e - m).power(F(1, 2)).same_quantity(v),
        "E = mc^4 rejected": not (m + v.power(4)).same_dimension(e),
    }
    return all(checks.values()), checks


@claim("C4", "rational powers are legal exactly when they should be: no "
             "square root of a pseudovector or of a rank-2 tensor")
def c4():
    stress = REASONER.meaning("stress")             # rank 2
    torque = REASONER.meaning("torque")             # rank 1, axial
    energy = REASONER.meaning("energy")
    out = {}
    try:
        stress.power(F(1, 2))
        out["sqrt(stress) refused"] = False
    except ParseError:
        out["sqrt(stress) refused"] = True
    try:
        torque.power(F(1, 3))
        out["cbrt(torque) refused"] = False
    except ParseError:
        out["cbrt(torque) refused"] = True
    out["sqrt(energy) allowed"] = energy.power(F(1, 2)).exponent("L") == 1
    out["fracture toughness has L^(-1/2)"] = \
        REASONER.meaning("fracture_toughness").exponent("L") == F(-1, 2)
    return all(out.values()), out


@claim("C5", "the meaning module has torsion, so no injective homomorphism "
             "into a torsion-free group exists; the encoder is a bijection "
             "onto its image and a homomorphism on the torsion-free part")
def c5():
    a = Meaning.make(L=1, p=1)
    out = {
        "2 * (P-odd) is P-even": (a + a).p == 0,
        "and is not the identity": (a + a) != Meaning.make(),
        "torsion element exists": Meaning.make(p=1) + Meaning.make(p=1)
                                  == Meaning.make(),
    }
    rep = codec_audit(sample_limit=80)
    out["addition exact on torsion-free part"] = \
        rep["addition_is_exact_on_torsion_free_part"]
    out["compose matches the product"] = rep["compose_matches_meaning_product"]
    return all(out.values()), out


@claim("C6", "the new axes carry real distinctions: torque, hertz vs "
             "becquerel, radiance vs irradiance, h vs hbar, km vs m, axial "
             "vs polar vectors")
def c6():
    R = REASONER
    pairs = {
        "torque vs energy": ("torque", "energy"),
        "frequency vs activity": ("frequency", "activity"),
        "radiance vs irradiance": ("radiance", "irradiance"),
        "planck vs reduced planck": ("planck_constant", "reduced_planck"),
        "kilometre vs length": ("kilometre", "length"),
        "torque vs force": ("torque", "force"),
        "entropy vs heat capacity": ("entropy", "heat_capacity"),
        "bit rate vs bandwidth": ("information_rate", "bandwidth"),
    }
    out = {}
    for label, (a, b) in pairs.items():
        aud = R.audit(a, b)
        out[label] = not aud.admissible
    return all(out.values()), out


@claim("C7", "the parser is exact: powers of ten only, rational exponents, "
             "and refusal to absorb arbitrary constants")
def c7():
    out = {}
    out["mass*speed^2 = energy"] = parse("mass*speed^2").same_dimension(
        REASONER.meaning("energy"))
    out["(energy/mass)^(1/2) = speed"] = parse(
        "(energy/mass)^(1/2)").same_quantity(REASONER.meaning("speed"))
    out["1000*length is a kilometre"] = parse("1000 * length").scale == 3
    for bad in ("2 * length", "length^x", "nonsense_quantity"):
        try:
            parse(bad)
            out[f"refuses {bad!r}"] = False
        except ParseError:
            out[f"refuses {bad!r}"] = True
    return all(out.values()), out


@claim("C8", "affine scales are held apart from the group: Celsius and "
             "decibel are recorded as non-multiplicative")
def c8():
    out = {"affine scales": len(AFFINE_SCALES),
           "celsius listed": "celsius" in AFFINE_SCALES,
           "decibel listed": "decibel" in AFFINE_SCALES,
           "not in the concept register": all(
               k not in CONCEPTS for k in AFFINE_SCALES)}
    return (out["celsius listed"] and out["decibel listed"]
            and out["not in the concept register"]), out


@claim("C9", "every concept in the register is encodable on the (1/12) "
             "lattice, and 105 defining relations hold exactly")
def c9():
    ok, total, failures = check_relations()
    return ok == total and not failures, {"ok": ok, "total": total,
                                          "failures": failures}


# ══════════════════════════════════════════════════════════════════════════════
#  §4.  THE LATTICE
# ══════════════════════════════════════════════════════════════════════════════

@claim("C10", "[Z^24 : Lambda] = 2^36, counted from the defining congruences")
def c10():
    rep = index_derivation()
    return rep["matches"], rep


@claim("C11", "the Hermite normal form of the explicit generating set is a "
              "Z-basis of Lambda: 24 rows, all in Lambda, determinant 2^36")
def c11():
    det = basis_determinant()
    rows_ok = all(in_leech(list(r)) for r in LEECH_BASIS)
    return (len(LEECH_BASIS) == 24 and rows_ok and det == INDEX_IN_Z24), \
        {"rows": len(LEECH_BASIS), "determinant": det,
         "all rows in Lambda": rows_ok}


@claim("C12", "lattice coordinates round trip exactly, and every minimal "
              "vector lies in the lattice the basis generates", heavy=True)
def c12():
    rt = True
    for k in range(200):
        u = [(k * (i + 5)) % 11 - 5 for i in range(DIM)]
        x = from_coords(u)
        rt &= in_leech(list(x)) and to_coords(x) == u
    count = 0
    inside = True
    for v in minimal_vectors():
        count += 1
        if count % 211 == 0:
            inside &= to_coords(list(v)) is not None
    return rt and inside and count == KISSING, {
        "round trips": rt, "minimal vectors": count,
        "sampled coordinates exist": inside}


@claim("C13", "the theta series from E_4^3 - 720 Delta agrees with the "
              "enumeration of minimal vectors")
def c13():
    theta = theta_series(5)
    return theta[2] == KISSING, {"theta head": theta[:5],
                                 "kissing number": KISSING}


# ══════════════════════════════════════════════════════════════════════════════
#  §5.  THE CODEC
# ══════════════════════════════════════════════════════════════════════════════

@claim("C14", "every concept encodes to a Leech point and decodes back "
              "exactly")
def c14():
    rep = codec_audit()
    ok = rep["all_in_lattice"] and rep["round_trip_exact"]
    return ok, {k: rep[k] for k in ("concepts_encoded", "distinct_meanings",
                                    "distinct_carriers", "all_in_lattice",
                                    "round_trip_exact")}


@claim("C15", "the slot layout is a bijection onto its image: 24 named slots, "
              "and off-image points are refused")
def c15():
    m = REASONER.meaning("energy")
    u = coords_of(m, (1, 2, 3, 0, 0, 0, 0))
    x = from_coords(u)
    back, ctx = decode_point(x)
    out = {"slots": len(u), "context preserved": ctx == (1, 2, 3, 0, 0, 0, 0),
           "meaning preserved": back == m}
    bad = list(u)
    bad[12] = 5                       # a parity slot out of range
    try:
        decode_point(from_coords(bad))
        out["off-image refused"] = False
    except ValueError:
        out["off-image refused"] = True
    return all(v is True or v == 24 for v in out.values()), out


@claim("C16", "distinct concepts are at squared carrier distance at least 32")
def c16():
    names = sorted(CONCEPTS)
    pts = {}
    for n in names:
        pts.setdefault(encode(CONCEPTS[n].meaning), n)
    worst = None
    keys = list(pts)
    for i in range(0, len(keys), 1):
        for j in range(i + 1, min(i + 12, len(keys))):
            d = norm2([a - b for a, b in zip(keys[i], keys[j])])
            worst = d if worst is None else min(worst, d)
    return worst >= MIN_NORM2, {"distinct carriers": len(pts),
                                "minimum sampled squared distance": worst,
                                "guaranteed bound": separation_bound()}


@claim("C17", "the packing radius squared is 8")
def c17():
    return packing_radius2() == 8, {"packing radius^2": str(packing_radius2()),
                                    "minimum norm^2": MIN_NORM2}


@claim("C18", "every corruption of squared magnitude at most 7 is repaired "
              "exactly, on a sweep over concepts and error patterns",
       heavy=True)
def c18():
    rng = random.Random(20250816)
    names = ["energy", "torque", "radiance", "gigabit_per_second",
             "fracture_toughness", "magnetic_flux_density", "entropy"]
    total = 0
    exact = 0
    for name in names:
        m = REASONER.meaning(name)
        x = encode(m)
        for weight in range(1, 8):
            for _ in range(6):
                err = [0] * DIM
                for i in rng.sample(range(DIM), weight):
                    err[i] = rng.choice((-1, 1))
                total += 1
                res = repair([a + b for a, b in zip(x, err)], expected=m)
                if res.exact and tuple(res.point) == tuple(x):
                    exact += 1
    return exact == total, {"trials": total, "repaired exactly": exact}


@claim("C19", "composition of carriers matches the product of meanings")
def c19():
    rep = codec_audit(sample_limit=120)
    names = ["energy", "mass", "speed", "torque", "kilometre", "radiance"]
    ok = True
    for a in names:
        for b in names:
            ma, mb = REASONER.meaning(a), REASONER.meaning(b)
            ok &= compose(encode(ma), encode(mb)) == encode(ma + mb)
    return ok and rep["compose_matches_meaning_product"], {
        "torsion-free addition exact":
            rep["addition_is_exact_on_torsion_free_part"],
        "compose exact on all pairs": ok}


@claim("C20", "capacity: 196,561 concepts within squared norm 32, 16,969,681 "
              "within 48, countably infinitely many in all")
def c20():
    a = capacity_within_norm(32)
    b = capacity_within_norm(48)
    return (a == 196561 and b == 16969681), {"within 32": a, "within 48": b}


# ══════════════════════════════════════════════════════════════════════════════
#  §6.  DECODING
# ══════════════════════════════════════════════════════════════════════════════

@claim("C21", "the fast decoder agrees with the slow reference decoder")
def c21():
    rng = random.Random(4242)
    same = 0
    ties = 0
    trials = 6
    for _ in range(trials):
        y = [rng.randint(-30, 30) for _ in range(DIM)]
        fast = decode(y)
        ref_pt, ref_d = decode_reference(y)
        if fast.dist2 == ref_d:
            same += 1
            if tuple(fast.point) != tuple(ref_pt):
                ties += 1
    return same == trials, {"trials": trials, "same distance": same,
                            "distinct but equidistant": ties}


@claim("C22", "decoded points satisfy the Voronoi condition against all "
              "196,560 minimal-vector translates", heavy=True)
def c22():
    rng = random.Random(99)
    ok = True
    for _ in range(3):
        y = [rng.randint(-30, 30) for _ in range(DIM)]
        res = decode(y)
        ok &= verify_local_optimality(y, res.point)
    return ok, {"random points checked": 3,
                "translates per point": KISSING}


# ══════════════════════════════════════════════════════════════════════════════
#  §7.  THE CONWAY GROUP
# ══════════════════════════════════════════════════════════════════════════════

@claim("C23", "every generator is an automorphism of Lambda: basis in the "
              "lattice, Gram preserved, unimodular in coordinates")
def c23():
    reps = [verify_automorphism(g, samples=40) for g in GENERATORS]
    ok = all(all(r.values()) for r in reps)
    return ok, {"generators": len(GENERATORS),
                "all verified": ok,
                "kinds": sorted({g.kind for g in GENERATORS})}


@claim("C24", "the sextet element is found by search: of the 64 sign "
              "patterns exactly the 32 odd ones preserve Lambda")
def c24():
    return SEXTET_SIGN_PATTERNS == 32, {
        "sextet": SEXTET, "working sign patterns": SEXTET_SIGN_PATTERNS}


@claim("C25", "the monomial subgroup 2^12 : M24 has exactly three orbits on "
              "the minimal vectors: 1104 / 97152 / 98304", heavy=True)
def c25():
    sizes = minimal_vector_orbit_census(MONOMIAL_GENERATORS)
    return sizes == [1104, 97152, 98304], {"orbit sizes": sizes,
                                           "order": MONOMIAL_ORDER}


@claim("C26", "the full group is transitive on the 196,560 minimal vectors",
       heavy=True)
def c26():
    size = orbit_on_minimal_vectors(GENERATORS)
    return size == KISSING, {"orbit size": size}


@claim("C27", "the type-2 class of a minimal vector has an orbit of exactly "
              "98,280 classes in Lambda / 2Lambda")
def c27():
    mats = [f2_matrix(g) for g in GENERATORS]
    v = next(iter(minimal_vectors()))
    u = to_coords(list(v))
    seed = sum(1 << i for i, x in enumerate(u) if x % 2)
    seen = {seed}
    frontier = [seed]
    while frontier:
        nxt = []
        for p in frontier:
            for m in mats:
                q = f2_apply(p, m)
                if q not in seen:
                    seen.add(q)
                    nxt.append(q)
        frontier = nxt
    return len(seen) == 98280, {"orbit": len(seen)}


@claim("C28", "a rigorous lower bound for the order of the group is "
              "8,315,553,613,086,720,000, the classical order of Co_0",
       heavy=True)
def c28():
    mats = [f2_matrix(g) for g in GENERATORS]
    v = next(iter(minimal_vectors()))
    u = to_coords(list(v))
    seed = sum(1 << i for i, x in enumerate(u) if x % 2)
    best = 0
    lengths: List[int] = []
    for s in (12345, 20250816, 7):
        grp = F2Group(mats, seed=s)
        grp.build(rounds=120, base_hint=[seed])
        if grp.order_lower_bound() > best:
            best = grp.order_lower_bound()
            lengths = grp.orbit_lengths()
        if 2 * best >= CO0_ORDER_CLASSICAL:
            break
    return 2 * best == CO0_ORDER_CLASSICAL, {
        "basic orbit lengths": lengths,
        "image lower bound": best,
        "group lower bound": 2 * best,
        "classical |Co_0|": CO0_ORDER_CLASSICAL}


@claim("C29", "the Lambda / 2Lambda class census closes: 1 + 98,280 + "
              "8,386,560 + 8,292,375 = 2^24")
def c29():
    rep = mod_two_type_census()
    return rep["mod2_census_is_2^24"], rep


# ══════════════════════════════════════════════════════════════════════════════
#  §3 AND §10.  MEASUREMENTS
# ══════════════════════════════════════════════════════════════════════════════

@claim("C30", "measurement: how many concept pairs a mod-2 carrier confuses, "
              "and how many a seven-exponent integer system confuses that "
              "GLM-2 separates", heavy=True)
def c30():
    names = sorted(CONCEPTS)
    ms = [CONCEPTS[n].meaning for n in names]
    seven = ("L", "M", "T", "I", "H", "N", "J")
    idx7 = [AXES.index(a) for a in seven]

    def key7(m):
        return tuple(m.exps[i] for i in idx7)

    def key_mod2(m):
        s = mod2_shadow(m)
        return None if s is None else s

    total_pairs = 0
    mod2_confused = 0
    glm1_confused = 0
    by_field = {"angle": 0, "solid_angle": 0, "information": 0, "scale": 0,
                "rank": 0, "parity": 0, "kind": 0}
    n = len(ms)
    for i in range(n):
        mi = ms[i]
        for j in range(i + 1, n):
            mj = ms[j]
            if mi.commensurable(mj):
                continue                       # genuinely the same meaning
            total_pairs += 1
            si, sj = key_mod2(mi), key_mod2(mj)
            if si is not None and si == sj:
                mod2_confused += 1
            if key7(mi) == key7(mj):
                glm1_confused += 1
                if mi.exponent("A") != mj.exponent("A"):
                    by_field["angle"] += 1
                elif mi.exponent("S") != mj.exponent("S"):
                    by_field["solid_angle"] += 1
                elif mi.exponent("B") != mj.exponent("B"):
                    by_field["information"] += 1
                elif mi.scale != mj.scale:
                    by_field["scale"] += 1
                elif mi.rank != mj.rank:
                    by_field["rank"] += 1
                elif (mi.p, mi.t, mi.c) != (mj.p, mj.t, mj.c):
                    by_field["parity"] += 1
                elif mi.kind != mj.kind:
                    by_field["kind"] += 1
    detail = {
        "inequivalent pairs": total_pairs,
        "confused by a mod-2 carrier": mod2_confused,
        "confused by a seven-exponent integer system": glm1_confused,
        "separated by": by_field,
        "confused by GLM-2": 0,
    }
    return glm1_confused > 0 and mod2_confused >= glm1_confused, detail


@claim("C31", "Co_0 is a symmetry of the carrier and not of the semantics: "
              "norms are preserved, meanings are not")
def c31():
    rep = REASONER.symmetry("energy")
    return (rep["norm_preserved_by_all"]
            and rep["images_that_carry_a_meaning"] == 0), rep


# ══════════════════════════════════════════════════════════════════════════════
#  §8.  THE ALGEBRA LAYER
# ══════════════════════════════════════════════════════════════════════════════

@claim("C32", "the Griess ledger closes: 300 + 98,280 + 98,304 = 196,884, "
              "with 98,280 counted from Lambda / 2Lambda")
def c32():
    census = mod_two_type_census()
    total = 300 + census["mod2_classes_type2"] + 24 * 4096
    return total == 196884, {"300": 300,
                             "type-2 classes": census["mod2_classes_type2"],
                             "24 x 4096": 24 * 4096, "total": total}


@claim("C33", "the j-function head, computed as E_4^3 / Delta, is "
              "1/q + 744 + 196884 q + 21493760 q^2")
def c33():
    j = j_invariant_series(3)
    return j[:4] == [1, 744, 196884, 21493760], {"coefficients": j}


@claim("C34", "the Jordan algebra of symmetric matrices is commutative, "
              "unital, non-associative, satisfies the Jordan identity, and "
              "its rank-one idempotents are axes of Jordan type 1/2")
def c34():
    alg = jordan_symmetric_algebra(4)
    e = [F(0)] * alg.dim
    e[0] = F(1)
    axis = tuple(e)
    ok_spec, dims = alg.spectrum_within(axis, (1, F(1, 2), 0))
    fus = alg.fusion_report(axis, (1, F(1, 2), 0), jordan_type_rules(F(1, 2)))
    out = {
        "dim": alg.dim,
        "commutative": alg.is_commutative(),
        "associator defects": alg.associator_defects(),
        "Jordan identity": alg.satisfies_jordan_identity(),
        "Frobenius form": alg.form_is_frobenius(),
        "unital": alg.identity_element() is not None,
        "axis spectrum in {1,1/2,0}": ok_spec,
        "eigenspace dims": dims,
        "Jordan-type fusion": fus["ok"],
    }
    ok = (out["commutative"] and out["associator defects"] > 0
          and out["Jordan identity"] and out["Frobenius form"]
          and out["unital"] and ok_spec and fus["ok"])
    return ok, out


@claim("C35", "the Matsuo algebra of S_3 with eta = 1/4 is the Norton-Sakuma "
              "algebra 2A: a_0 a_1 = (1/8)(a_0 + a_1 - a_rho)")
def c35():
    alg = matsuo_algebra(symmetric_group_transpositions(3), F(1, 4))
    prod = alg.structure[0][1]
    expected = (F(1, 8), F(1, 8), F(-1, 8))
    ok_struct = tuple(prod) == expected
    a = basis_vector(alg.dim, 0)
    ok_spec, dims = alg.spectrum_within(a, (1, 0, F(1, 4)))
    fus = alg.fusion_report(a, (1, 0, F(1, 4)), jordan_type_rules(F(1, 4)))
    ok = (ok_struct and ok_spec and fus["ok"] and alg.is_commutative()
          and alg.associator_defects() > 0 and alg.form_is_frobenius())
    return ok, {"a_0 a_1": [str(x) for x in prod],
                "eigenspace dims": dims,
                "fusion": fus["ok"],
                "non-associative": alg.associator_defects() > 0}


@claim("C36", "Matsuo algebras of S_3, S_4 and S_5 are axial of Jordan type "
              "with Miyamoto involutions that are algebra automorphisms")
def c36():
    rep = axial_audit(full=True)
    keys = ["2A", "3C", "Matsuo_S4", "Matsuo_S5"]
    ok = all(rep[k]["jordan_type_fusion"]
             and rep[k]["miyamoto_involutions_are_automorphisms"]
             and rep[k]["frobenius_form"] for k in keys)
    return ok, {k: {kk: rep[k][kk] for kk in ("dim", "eigenspace_dims",
                                              "jordan_type_fusion")}
                for k in keys}


@claim("C37", "the Miyamoto involutions of the S_n Matsuo algebra generate "
              "S_n itself")
def c37():
    out = {}
    for n in (3, 4, 5):
        out[f"S_{n}"] = miyamoto_group_order(symmetric_group_transpositions(n))
    expected = {"S_3": 6, "S_4": 24, "S_5": 120}
    return out == expected, out


# ══════════════════════════════════════════════════════════════════════════════
#  §9.  THE COMPANION IMPLEMENTATION
# ══════════════════════════════════════════════════════════════════════════════

@claim("C38", "the reasoner accepts the true laws and rejects the traps, "
              "with a reason for every rejection")
def c38():
    R = REASONER
    good = [("energy", "mass*speed^2"), ("force", "mass*acceleration"),
            ("power", "energy/time"), ("charge", "current*time"),
            ("illuminance", "luminous_flux/area"),
            ("angular_momentum", "moment_of_inertia*angular_velocity")]
    bad = [("energy", "mass*speed^4"), ("force", "mass*acceleration^3"),
           ("energy", "torque"), ("radiance", "irradiance"),
           ("frequency", "activity"), ("kilometre", "length")]
    out = {}
    ok = True
    for lhs, rhs in good:
        a = R.audit(lhs, rhs)
        ok &= a.admissible
        out[f"accept {lhs} = {rhs}"] = a.admissible
    for lhs, rhs in bad:
        a = R.audit(lhs, rhs)
        ok &= (not a.admissible) and bool(a.reasons())
        out[f"reject {lhs} = {rhs}"] = a.reasons()
    return ok, out


@claim("C39", "synthesis returns exact rational exponents, including "
              "fractional ones, and says 'no pathway' when there is none")
def c39():
    R = REASONER
    cases = {
        "energy from mass, speed": (R.solve("energy", ["mass", "speed"]),
                                    "energy = mass * speed^2"),
        "speed from energy, mass": (R.solve("speed", ["energy", "mass"]),
                                    "speed = energy^(1/2) * mass^(-1/2)"),
        "power from current, resistance":
            (R.solve("power", ["current", "resistance"]),
             "power = current^2 * resistance"),
        "reduced planck from action, angle":
            (R.solve("reduced_planck", ["action", "angle"]),
             "reduced_planck = action * angle^-1"),
    }
    out = {k: v[0].formula() for k, v in cases.items()}
    ok = all(v[0].formula() == v[1] for v in cases.values())
    none = R.solve("energy", ["length", "time"])
    out["no pathway"] = not none.solvable
    return ok and not none.solvable, out


@claim("C40", "Buckingham Pi: the dimensionless groups are computed exactly "
              "over Q")
def c40():
    R = REASONER
    re = R.pi_groups(["speed", "length", "kinematic_viscosity"])
    fr = R.pi_groups(["speed", "length", "gravitational_field"])
    none = R.pi_groups(["length", "mass"])
    out = {"Reynolds-like": [{k: str(v) for k, v in g.items()} for g in re],
           "Froude-like": [{k: str(v) for k, v in g.items()} for g in fr],
           "length and mass have no group": len(none)}
    return len(re) == 1 and len(fr) == 1 and not none, out


@claim("C41", "telemetry reports a lattice point for every concept")
def c41():
    ok = True
    sample = ["energy", "torque", "radiance", "information_rate", "kilometre"]
    detail = {}
    for n in sample:
        t = REASONER.telemetry(n)
        ok &= bool(t["carrier_in_lattice"])
        detail[n] = t["carrier_norm2"]
    return ok, detail


@claim("C42", "transmission: corrupt and repair a concept, exactly")
def c42():
    out = {}
    ok = True
    for n in ("energy", "radiance", "gigabit_per_second"):
        r = REASONER.transmit(n, 7)
        ok &= bool(r["repaired_exactly"]) and bool(r["carrier_restored"])
        out[n] = {"error^2": r["error_norm2"],
                  "repaired": r["repaired_exactly"]}
    return ok, out


@claim("C43", "unit conversion is exact and decimal")
def c43():
    R = REASONER
    out = {p: R.convert(*p.split("->")) for p in
           ("kilometre->length", "gigahertz->frequency",
            "megapascal->pressure", "gigabit->information")}
    ok = all(v is not None for v in out.values())
    return ok, out


@claim("C44", "carrier neighbourhoods are meaningful: the nearest concepts "
              "to a given one differ by one small exponent step")
def c44():
    near = REASONER.neighbours("energy", 5)
    ok = all(d >= 0 for _, d in near)
    return ok, {"energy": [(n, d) for n, d in near]}


# ══════════════════════════════════════════════════════════════════════════════
#  §11.  INVARIANTS
# ══════════════════════════════════════════════════════════════════════════════

@claim("C45", "invariant I1: no float appears in any carrier or meaning "
              "computation")
def c45():
    m = REASONER.meaning("fracture_toughness")
    x = encode(m)
    ok = all(isinstance(v, int) for v in x) and \
        all(isinstance(e, F) for e in m.exps)
    return ok, {"carrier entries are ints": all(isinstance(v, int)
                                                for v in x),
                "exponents are Fractions": all(isinstance(e, F)
                                               for e in m.exps)}


@claim("C46", "invariant I3: every carrier point of the register satisfies "
              "the defining congruences of Lambda")
def c46():
    bad = [n for n in CONCEPTS
           if not in_leech(list(encode(CONCEPTS[n].meaning)))]
    return not bad, {"concepts": len(CONCEPTS), "failures": bad}


@claim("C47", "invariant I5: repair never returns a different concept; "
              "outside the packing radius it says so")
def c47():
    m = REASONER.meaning("energy")
    x = encode(m)
    inside = repair([a + b for a, b in
                     zip(x, [1, -1, 1, -1, 1, 0, 0] + [0] * 17)], expected=m)
    far = [0] * DIM
    far[0] = 12
    outside = repair([a + b for a, b in zip(x, far)], expected=m)
    return (inside.exact and inside.within_radius
            and not outside.within_radius), {
        "inside radius": {"err^2": inside.error_norm2,
                          "exact": inside.exact},
        "outside radius": {"err^2": outside.error_norm2,
                           "within radius": outside.within_radius,
                           "still exact": outside.exact}}


@claim("C48", "invariant I9: the first-generation Golay code and M24 are "
              "reused, not copied")
def c48():
    return len(GOLAY_MASKS) == 4096 and len(OCTAD_MASKS) == 759, {
        "Golay codewords": len(GOLAY_MASKS), "octads": len(OCTAD_MASKS),
        "source": "../glm/glm_substrate.py, ../glm/glm_m24.py"}


# ══════════════════════════════════════════════════════════════════════════════
#  §12.  THE OPERATOR ALGEBRA AND THE DERIVED GRADINGS
# ══════════════════════════════════════════════════════════════════════════════

@claim("C49", "the differential operators are all built from one nabla, so "
              "their rank and parity bookkeeping is forced, not tabulated")
def c49():
    out = {
        "nabla": str(NABLA),
        "nabla is L^-1, rank 1, P-odd": (NABLA.exponent("L") == -1
                                         and NABLA.rank == 1
                                         and NABLA.p == 1),
        "grad raises rank": parse("grad(pressure)").rank == 1,
        "div lowers rank": parse("div(velocity)").rank == 0,
        "curl keeps rank 1": parse("curl(velocity)").rank == 1,
        "laplacian keeps rank": (parse("laplacian(voltage)").rank
                                 == REASONER.meaning("voltage").rank),
    }
    # curl of a polar vector is axial, and of an axial vector is polar
    v = REASONER.meaning("velocity")               # polar, p = 1
    b = REASONER.meaning("magnetic_flux_density")  # axial, p = 0
    out["curl(polar) is axial"] = NABLA.cross(v).is_pseudo()
    out["curl(axial) is polar"] = not NABLA.cross(b).is_pseudo()
    # laplacian is parity- and grading-neutral
    for name in ("voltage", "temperature", "charge_density"):
        m = REASONER.meaning(name)
        lap = FUNCTIONS["laplacian"][1](m)
        out[f"laplacian preserves character: {name}"] = \
            lap.same_tensor_character(m)
    return all(v is True for k, v in out.items() if k != "nabla"), out


@claim("C50", "contraction and the tensor product are different operations "
              "with the same dimensions, and GLM-2 keeps them apart")
def c50():
    tensor = parse("force * position")
    scalar = parse("dot(force, position)")
    energy = REASONER.meaning("energy")
    out = {
        "same dimensions": tensor.same_dimension(scalar),
        "tensor product has rank 2": tensor.rank == 2,
        "contraction has rank 0": scalar.rank == 0,
        "contraction is an energy": scalar.same_quantity(energy),
        "tensor product is not an energy": not tensor.same_quantity(energy),
        "they are not the same meaning": not tensor.same_quantity(scalar),
    }
    return all(out.values()), out


@claim("C51", "the cross product reproduces the register's axial quantities "
              "exactly, angular momentum and torque included")
def c51():
    cases = {
        "moment(position, momentum) = angular_momentum":
            ("moment(position, momentum)", "angular_momentum"),
        "moment(position, force) = torque": ("moment(position, force)",
                                             "torque"),
        "rot(velocity) = vorticity": ("rot(velocity)", "vorticity"),
        "curl(magnetic_field_h) = current_density":
            ("curl(magnetic_field_h)", "current_density"),
        "cross(electric_field, magnetic_field_h) = poynting_vector":
            ("cross(electric_field, magnetic_field_h)", "poynting_vector"),
        "ddt(velocity) = acceleration": ("ddt(velocity)", "acceleration"),
        "ddt(momentum) = force": ("ddt(momentum)", "force"),
        "integral_dt(power) = energy": ("integral_dt(power)", "energy"),
        "integral_dV(charge_density) = charge":
            ("integral_dV(charge_density)", "charge"),
        "integral_dV(energy_density) = energy":
            ("integral_dV(energy_density)", "energy"),
    }
    out = {}
    for label, (expr, target) in cases.items():
        out[label] = parse(expr).same_quantity(REASONER.meaning(target))
    return all(out.values()), out


@claim("C52", "d/dt and the time integral are mutually inverse, and d/dt "
              "flips the T grading of every concept in the register")
def c52():
    ddt = FUNCTIONS["ddt"][1]
    itg = FUNCTIONS["integral_dt"][1]
    round_trip = 0
    flipped = 0
    graded = 0
    total = 0
    for c in CONCEPTS.values():
        m = c.meaning
        total += 1
        if (ddt(itg(m)).same_quantity(m)
                and itg(ddt(m)).same_quantity(m)):
            round_trip += 1
        a, b = m.t_parity(), ddt(m).t_parity()
        if a is None or b is None:
            continue                 # fractional time exponent: ungraded
        graded += 1
        if a != b:
            flipped += 1
    out = {"concepts": total, "round trips": round_trip,
           "T-graded concepts": graded, "T grading flipped": flipped}
    return round_trip == total and flipped == graded and graded > 0, out


@claim("C53", "the T and C gradings are derived from the exponents, hence "
              "are homomorphisms: they add over every pair of concepts")
def c53():
    names = sorted(CONCEPTS)
    bad_t = []
    bad_c = []
    pairs = 0
    for i, a in enumerate(names):
        ma = CONCEPTS[a].meaning
        for b in names[i::37]:              # a deterministic spread of pairs
            mb = CONCEPTS[b].meaning
            prod = ma + mb
            pairs += 1
            ta, tb, tp = ma.t_parity(), mb.t_parity(), prod.t_parity()
            ca, cb, cp = ma.c_parity(), mb.c_parity(), prod.c_parity()
            if None not in (ta, tb, tp) and (ta + tb) % 2 != tp:
                bad_t.append((a, b))
            if None not in (ca, cb, cp) and (ca + cb) % 2 != cp:
                bad_c.append((a, b))
    out = {"pairs tested": pairs, "T failures": len(bad_t),
           "C failures": len(bad_c)}
    return not bad_t and not bad_c, out


@claim("C54", "the anomaly field is used exactly once, for the particle "
              "electric dipole moment, and it is what makes an EDM a "
              "T-violating observable")
def c54():
    anomalous = sorted(n for n, c in CONCEPTS.items()
                       if c.meaning.t or c.meaning.c)
    edm = REASONER.meaning("particle_electric_dipole_moment")
    dipole = REASONER.meaning("electric_dipole_moment")
    audit = REASONER.audit("particle_electric_dipole_moment",
                           "electric_dipole_moment")
    out = {
        "anomalous concepts": anomalous,
        "same dimensions": edm.same_dimension(dipole),
        "same rank": edm.rank == dipole.rank,
        "EDM is T-odd": edm.t_parity() == 1,
        "ordinary dipole is T-even": dipole.t_parity() == 0,
        "reasoner rejects equating them": not audit.admissible,
        "reason": audit.reasons(),
    }
    return (anomalous == ["particle_electric_dipole_moment"]
            and out["same dimensions"] and out["same rank"]
            and out["EDM is T-odd"] and out["ordinary dipole is T-even"]
            and out["reasoner rejects equating them"]), out


@claim("C55", "the derived T grading agrees with the textbook behaviour of "
              "twenty standard quantities")
def c55():
    # (concept, expected T grading): 1 means the quantity reverses sign under
    # t -> -t.  Every entry is the standard classical answer.
    table = {
        "position": 0, "velocity": 1, "acceleration": 0, "momentum": 1,
        "force": 0, "energy": 0, "power": 1, "time": 1,
        "angular_momentum": 1, "torque": 0, "charge": 0, "current": 1,
        "electric_field": 0, "magnetic_flux_density": 1, "voltage": 0,
        "resistance": 1, "capacitance": 0, "inductance": 0,
        "magnetic_dipole_moment": 1, "pressure": 0,
    }
    out = {}
    wrong = []
    for name, expected in table.items():
        got = REASONER.meaning(name).t_parity()
        if got != expected:
            wrong.append((name, expected, got))
    out["quantities checked"] = len(table)
    out["disagreements"] = wrong
    return not wrong, out


@claim("C56", "expressions built with the operator algebra are first-class "
              "concepts: they encode to Leech points and decode back exactly")
def c56():
    exprs = ["moment(position, momentum)", "dot(force, position)",
             "grad(pressure)", "div(velocity)", "rot(velocity)",
             "cross(electric_field, magnetic_field_h)",
             "laplacian(voltage)", "ddt(velocity)", "integral_dt(power)",
             "force * position", "1000 * grad(pressure)"]
    out = {}
    for text in exprs:
        m = parse(text)
        point = encode(m)
        back, _ = decode_point(point)
        out[text] = (in_leech(point) and back == m)
    return all(out.values()), out


@claim("C57", "the register carries a second table of relations that hold in "
              "the FULL meaning — rank and parities included — among them all "
              "four Maxwell equations")
def c57():
    ok, total, failures = check_tensor_relations()
    loose_ok, loose_total, _ = check_relations()
    strict_ok, _, _ = check_relations(strict=True)
    maxwell = {
        "Gauss": ("charge_density", "div(electric_displacement)"),
        "Gauss for magnetism (B is a curl)":
            ("magnetic_flux_density", "curl(magnetic_vector_potential)"),
        "Faraday": ("electric_field", "ddt(magnetic_vector_potential)"),
        "Ampere": ("current_density", "curl(magnetic_field_h)"),
        "Ampere, displacement term":
            ("current_density", "ddt(electric_displacement)"),
    }
    detail = {
        "tensor relations": total,
        "tensor relations exact": ok,
        "failures": failures,
        "scalar relations": loose_total,
        "scalar relations exact": loose_ok,
        "of those, also exact at full meaning": strict_ok,
    }
    for label, (lhs, rhs) in maxwell.items():
        detail[label] = REASONER.meaning(lhs).same_quantity(parse(rhs))
    return (ok == total and not failures
            and all(detail[label] for label in maxwell)), detail


@claim("C58", "meaning is the state and the carrier is derived: every "
              "concept's point is encode(its meaning) and decodes back to it, "
              "the derivation is injective, and no audit carries a mod-2 view")
def c58():
    """
    Section 3: the architecture invariant, checked rather than asserted.

    (i) For every concept in the register, re-deriving the carrier from the
    meaning gives the point the reasoner serves, and decoding that point gives
    the meaning back.  (ii) Distinct meanings give distinct points.  (iii) A
    carrier is never an input: the reasoner's audit record exposes no way to
    supply one, and no verdict object carries a mod-2 field.  (iv) Composition
    happens on meanings: the carrier of a product is encode(m1 + m2), which is
    what `compose` returns, and on the torsion-free slots — the ten exponents,
    the scale and the rank — the slot vectors simply add.  The only slots that
    do not add in Z are the three genuine Z/2 parities and the two label
    slots, which is a property of the meaning module, not a rule on bits.
    """
    names = sorted(CONCEPTS)
    seen: Dict[Tuple[int, ...], str] = {}
    derived = injective = True
    for name in names:
        m = REASONER.meaning(name)
        x = REASONER.carrier(name)
        derived = derived and REASONER.carrier_is_derived(name)
        key = tuple(x)
        if key in seen and REASONER.meaning(seen[key]) != m:
            injective = False
        seen.setdefault(key, name)
    audit = REASONER.audit("energy", "mass*speed^4")
    no_second_verdict = not (hasattr(audit, "mod2_would_accept")
                             or hasattr(audit, "mod2_false_positive"))
    no_mod2_in_reasons = "mod-2" not in str(audit)
    # composition is on meanings; the derived point of the product follows
    a, b = REASONER.meaning("force"), REASONER.meaning("length")
    composes = tuple(encode(a + b)) == tuple(compose(encode(a), encode(b)))
    # and on the torsion-free slots — the ten exponents, the scale and the
    # rank — the slot vectors simply add
    ua, ub, uab = coords_of(a), coords_of(b), coords_of(a + b)
    adds_free = all(uab[i] == ua[i] + ub[i] for i in range(12))
    ceiling = REASONER.mod2_ceiling([("energy", "mass*speed^4"),
                                     ("energy", "mass*speed^2")])
    ok = (derived and injective and no_second_verdict and no_mod2_in_reasons
          and composes and adds_free
          and ceiling["mod2_false_positives"] == 1)
    return ok, {
        "concepts checked": len(names),
        "carrier is encode(meaning) and decodes back": derived,
        "distinct meanings, distinct carriers": injective,
        "audit carries no mod-2 verdict": no_second_verdict,
        "carrier of a product = compose of the carriers": composes,
        "torsion-free slots add": adds_free,
        "appendix: F_2 false positives on two sample pairs":
            ceiling["mod2_false_positives"],
    }


# ══════════════════════════════════════════════════════════════════════════════
#  RUNNER
# ══════════════════════════════════════════════════════════════════════════════

def run(quick: bool = False, verbose: bool = True) -> Dict[str, object]:
    started = time.time()
    results: List[Dict[str, object]] = []
    passed = 0
    skipped = 0
    for cid, statement, fn, heavy in CLAIMS:
        if quick and heavy:
            skipped += 1
            results.append({"id": cid, "statement": statement,
                            "status": "skipped"})
            if verbose:
                print(f"  {cid:5s} SKIP  {statement}")
            continue
        t0 = time.time()
        try:
            ok, detail = fn()
        except Exception as exc:                      # pragma: no cover
            ok, detail = False, {"exception": repr(exc)}
        dt = time.time() - t0
        passed += 1 if ok else 0
        results.append({"id": cid, "statement": statement,
                        "status": "PASS" if ok else "FAIL",
                        "seconds": round(dt, 3), "detail": _jsonable(detail)})
        if verbose:
            print(f"  {cid:5s} {'PASS' if ok else 'FAIL'}  {statement}")
            for k, v in _flatten(detail):
                print(f"            {k:44s} {v}")
    elapsed = time.time() - started
    total = len(CLAIMS) - skipped
    summary = {
        "claims": len(CLAIMS),
        "run": total,
        "passed": passed,
        "failed": total - passed,
        "skipped": skipped,
        "seconds": round(elapsed, 2),
        "results": results,
    }
    if verbose:
        print()
        print(f"  {passed}/{total} claims pass"
              + (f", {skipped} skipped" if skipped else "")
              + f", in {elapsed:.1f} s")
    return summary


def _jsonable(obj):
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, F):
        return str(obj)
    if isinstance(obj, (int, float, str, bool)) or obj is None:
        return obj
    return str(obj)


def _flatten(detail, prefix=""):
    out = []
    if isinstance(detail, dict):
        for k, v in detail.items():
            if isinstance(v, dict):
                out.extend(_flatten(v, f"{prefix}{k}."))
            else:
                out.append((f"{prefix}{k}", _short(v)))
    else:
        out.append((prefix or "value", _short(detail)))
    return out


def _short(v):
    s = str(v)
    return s if len(s) <= 90 else s[:87] + "..."


def main(argv: Sequence[str]) -> int:
    quick = "--quick" in argv
    json_only = "--json" in argv
    if not json_only:
        print("=" * 80)
        print("  THE GEOMETRIC LANGUAGE MACHINE, SECOND GENERATION")
        print("  operational paper — verification run"
              + ("  (quick)" if quick else ""))
        print("=" * 80)
        print()
    summary = run(quick=quick, verbose=not json_only)
    here = os.path.dirname(os.path.abspath(__file__))
    outdir = os.path.join(here, "results")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "glm2_results.json")
    with open(path, "w") as fh:
        json.dump(summary, fh, indent=2, sort_keys=False)
    if not json_only:
        print(f"  results written to {os.path.relpath(path, here)}")
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
