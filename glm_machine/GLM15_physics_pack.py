# ==============================================================================
# §15  PHYSICS VOCABULARY PACK (v3.8.0 NEW MODULE)
# ==============================================================================
# A deterministic vocabulary augmentation that fills the largest semantic gap
# in v3.7.x: ~80% of frontier-physics multi-word terms were absent from the
# lang_kb.  The pack contributes ~140 terms drawn from QFT/HEP, condensed
# matter, GR/holography, quantum information, hydrodynamics, and stochastic
# biology.
#
# Design rules (UBP-consistent, no floats, no mocks, stdlib only):
#   * Each new term is given a 24-bit vector derived deterministically from
#     (MOG-category signature) XOR (role nibble) XOR (domain seed) XOR
#     (string-hash low bits), constrained to weight in [6, 18].
#   * The vector is then snapped to the nearest Golay codeword to guarantee
#     lattice-membership.
#   * No randomness: every vector is a pure function of the term string.
#
# Adapted from core/glm_physics_vocab_pack.py to be self-contained
# (uses only GLM01_substrate primitives).
# ==============================================================================
from __future__ import annotations
import hashlib
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

from GLM01_substrate import (
    BLA, GOLAY_ENGINE, LEECH_ENGINE, MOG_CATEGORIES, WordEntry, _get_mog_category,
)

# ── 1. QUADRANT MAP ──────────────────────────────────────────────────────────

QUADRANTS = {
    0: "Matter",       # M_*    (indices 0..5)
    1: "Information",  # I_*    (indices 6..11)
    2: "Activation",   # A_*    (indices 12..17)
    3: "Potential",    # P_*    (indices 18..23)
}

_CAT_TO_QSUB: Dict[str, Tuple[int, int]] = {}
for _idx, _name in enumerate(MOG_CATEGORIES):
    _CAT_TO_QSUB[_name] = (_idx // 6, _idx % 6)


# ── 2. DETERMINISTIC VECTOR DERIVATION ───────────────────────────────────────

def _string_hash_bits(s: str, n_bits: int) -> List[int]:
    """SHA-256 truncated to n_bits, returned as bit list (MSB first)."""
    h = hashlib.sha256(s.lower().encode("utf-8")).digest()
    bits: List[int] = []
    for byte in h:
        for k in range(7, -1, -1):
            bits.append((byte >> k) & 1)
            if len(bits) == n_bits:
                return bits
    return bits


def _category_signature(category: str) -> List[int]:
    """24-bit signature whose dominant quadrant matches the given MOG category."""
    if category not in _CAT_TO_QSUB:
        category = "I_Topology"
    q, sub = _CAT_TO_QSUB[category]
    vec = [0] * 24
    base = q * 6
    on_positions = [(sub * 2) % 6, (sub * 2 + 1) % 6,
                    (sub * 2 + 2) % 6, (sub * 2 + 3) % 6]
    for p in on_positions:
        vec[base + p] = 1
    return vec


def derive_term_vector(term: str, mog_category: str, role: str,
                       domain_seed: int = 0) -> List[int]:
    """Deterministic 24-bit vector for a physics term.

    Vector = category_signature XOR role_nibble XOR domain_seed XOR string_hash
    constrained to weight in [6, 18], then snapped to the nearest Golay
    codeword to guarantee lattice membership.
    """
    cat = _category_signature(mog_category)
    role_id = {"NOUN": 0, "VERB": 1, "ADJECTIVE": 2,
               "OPERATOR": 3, "PROPERTY": 4}.get(role, 4)
    # role smear: 4-bit role id at positions 20..23
    role_smear = [0] * 24
    for k in range(4):
        role_smear[20 + k] = (role_id >> (3 - k)) & 1
    # domain seed: 4-bit value at positions 16..19
    dom_smear = [0] * 24
    for k in range(4):
        dom_smear[16 + k] = (domain_seed >> (3 - k)) & 1
    # string hash: 8 low bits at positions 8..15
    h_bits = _string_hash_bits(term, 8)
    h_smear = [0] * 24
    for k, b in enumerate(h_bits):
        h_smear[8 + k] = b
    vec = [cat[i] ^ role_smear[i] ^ dom_smear[i] ^ h_smear[i] for i in range(24)]

    # Constrain weight to a healthy Leech-typical range
    w = sum(vec)
    if w < 6:
        for i in range(24):
            if vec[i] == 0:
                vec[i] = 1
                w += 1
                if w >= 6:
                    break
    if w > 18:
        for i in range(24):
            if vec[i] == 1:
                vec[i] = 0
                w -= 1
                if w <= 18:
                    break

    # Snap to nearest Golay codeword
    snapped, _ = GOLAY_ENGINE.snap_to_codeword(vec)
    return list(snapped)


# ── 3. CRITPT-DOMAIN PHYSICS LEXICON ─────────────────────────────────────────
# Each entry: (term, role, mog_category, domain_seed, definition)
# Domain seeds:
#   0 = QFT / HEP           4 = quantum information
#   1 = condensed matter    5 = hydrodynamics
#   2 = GR / holography     6 = stochastic / bio
#   3 = optics / cavity     7 = mathematical structure

PHYSICS_LEXICON: List[Tuple[str, str, str, int, str]] = [
    # ── core physics nouns that were astonishingly missing ────────────────────
    ("state",              "NOUN", "I_Topology",  7, "A vector in a Hilbert space describing a quantum system."),
    ("field",              "NOUN", "A_Energy",    0, "A function assigning a value to every point of spacetime."),
    ("energy",             "NOUN", "A_Energy",    0, "Conserved quantity associated with time-translation symmetry."),
    ("hamiltonian",        "NOUN", "A_Energy",    0, "Operator generating time evolution of a quantum system."),
    ("lagrangian",         "NOUN", "A_Energy",    0, "Functional whose stationary points give the equations of motion."),
    ("action",             "NOUN", "A_Energy",    0, "Time-integral of the Lagrangian."),
    ("operator",           "NOUN", "I_Symmetry",  7, "Linear map acting on a Hilbert space."),
    ("number",             "NOUN", "M_Count",     7, "A scalar quantity counting elements of a set."),
    ("constant",           "NOUN", "P_Limit",     7, "A quantity whose value does not change under the symmetry considered."),
    ("coupling",           "NOUN", "A_Force",     0, "Strength parameter of an interaction term in a Lagrangian."),
    ("interaction",        "NOUN", "A_Force",     0, "Term in the Hamiltonian connecting two or more degrees of freedom."),
    ("phase",              "NOUN", "P_Phase",     1, "Complex argument or thermodynamic regime of a system."),
    ("symmetry",           "NOUN", "I_Symmetry",  7, "Transformation leaving the action invariant."),
    ("group",              "NOUN", "I_Symmetry",  7, "Algebraic structure of symmetry transformations."),
    ("loop",               "NOUN", "I_Topology",  0, "Closed propagator line in a Feynman diagram."),
    ("vertex",             "NOUN", "I_Connectivity", 0, "Interaction node in a Feynman diagram."),
    ("propagator",         "NOUN", "A_Flux",      0, "Two-point Green's function of a quantum field."),
    ("renormalization",    "NOUN", "P_Tax",       0, "Procedure absorbing UV divergences into redefined couplings."),
    ("regularization",     "NOUN", "P_Limit",     0, "Method for assigning meaning to divergent integrals."),
    ("divergence",         "NOUN", "P_Limit",     0, "Behavior of an integral that grows without bound."),
    ("dimension",          "NOUN", "I_Dimension", 7, "Number of independent directions or scaling exponent."),
    ("scaling",            "NOUN", "P_Ratio",     7, "How a quantity transforms under a rescaling of length."),
    ("regulator",          "NOUN", "P_Limit",     0, "Auxiliary parameter introduced to tame divergences."),
    ("anomaly",            "NOUN", "I_Symmetry",  2, "Quantum violation of a classical symmetry."),
    ("conformal",          "ADJECTIVE", "I_Symmetry", 2, "Invariant under angle-preserving rescalings."),
    ("partition",          "NOUN", "M_Charge",    7, "Sum over states weighted by Boltzmann factors."),
    ("function",           "NOUN", "I_Symmetry",  7, "Map from one set to another."),
    ("functional",         "NOUN", "I_Symmetry",  7, "Map from a function space to numbers."),
    ("derivative",         "NOUN", "A_Velocity",  7, "Rate of change of a function with respect to a variable."),
    ("integral",           "NOUN", "A_Flux",      7, "Antiderivative or sum over a continuum."),
    ("tensor",             "NOUN", "I_Dimension", 7, "Multilinear geometric object transforming under coordinate changes."),
    ("metric",             "NOUN", "I_Dimension", 2, "Bilinear form measuring distances on a manifold."),
    ("manifold",           "NOUN", "I_Topology",  2, "Topological space locally homeomorphic to Euclidean space."),
    ("geodesic",           "NOUN", "A_Flux",      2, "Locally length-minimizing curve on a manifold."),
    ("curvature",          "NOUN", "I_Dimension", 2, "Local measure of departure from flatness."),
    ("connection",         "NOUN", "I_Connectivity", 2, "Differential-geometric object specifying parallel transport."),
    ("torsion",            "NOUN", "I_Symmetry",  2, "Antisymmetric part of an affine connection."),
    ("tetrad",             "NOUN", "I_Connectivity", 2, "Orthonormal frame field on a Lorentzian manifold."),

    # ── QFT specifics ─────────────────────────────────────────────────────────
    ("beta",               "NOUN", "P_Ratio",     0, "Beta function: RG flow of a coupling with energy scale."),
    ("weyl",               "ADJECTIVE", "I_Symmetry", 2, "Pertaining to local rescaling symmetry of the metric."),
    ("parton",             "NOUN", "I_Topology",  0, "Pointlike constituent of a hadron."),
    ("quark",              "NOUN", "I_Topology",  0, "Spin-1/2 colored elementary fermion."),
    ("gluon",              "NOUN", "I_Connectivity", 0, "Gauge boson of QCD mediating the strong interaction."),
    ("hadron",             "NOUN", "I_Topology",  0, "Composite particle bound by the strong force."),
    ("pion",               "NOUN", "I_Topology",  0, "Lightest meson; pseudoscalar bound state of u, d quarks."),
    ("meson",              "NOUN", "I_Topology",  0, "Quark-antiquark bound state."),
    ("baryon",             "NOUN", "I_Topology",  0, "Three-quark bound state."),
    ("fermion",            "NOUN", "I_Topology",  1, "Particle with half-integer spin obeying Fermi-Dirac statistics."),
    ("boson",              "NOUN", "I_Topology",  1, "Particle with integer spin obeying Bose-Einstein statistics."),
    ("majorana",           "ADJECTIVE", "I_Symmetry", 1, "A fermion equal to its own antiparticle."),
    ("dirac",              "ADJECTIVE", "I_Symmetry", 0, "Pertaining to spin-1/2 fields satisfying the Dirac equation."),
    ("feynman",            "ADJECTIVE", "I_Connectivity", 0, "Pertaining to perturbative path-integral diagrams."),
    ("diagram",            "NOUN", "I_Connectivity", 0, "Graphical representation of a perturbative contribution."),
    ("casimir",            "NOUN", "P_Limit",     0, "Quadratic invariant of a Lie algebra; or the zero-point energy effect."),
    ("dimensional regularization", "NOUN", "P_Limit", 0, "Continuation of integrals to d = 4 - 2*epsilon dimensions to regulate divergences."),
    ("sail diagram",       "NOUN", "I_Connectivity", 0, "One-loop diagram contributing to LaMET matching with a 'sail' topology."),
    ("lamet",              "NOUN", "I_Topology",  0, "Large-Momentum Effective Theory for parton distributions."),
    ("matching kernel",    "NOUN", "I_Connectivity", 0, "Perturbative coefficient linking quasi- and light-cone distributions."),
    ("dglap",              "NOUN", "A_Flux",      0, "Evolution equation governing scale dependence of parton distributions."),
    ("photopion",          "NOUN", "I_Connectivity", 0, "Photon-pion production process; central to astrophysical cascades."),
    ("synchrotron",        "NOUN", "A_Energy",    0, "Radiation emitted by relativistic charged particles in magnetic fields."),
    ("alpha",              "NOUN", "P_Ratio",     7, "Fine-structure constant or first Greek letter."),
    ("beta function",      "NOUN", "P_Ratio",     0, "RG-flow equation d(g)/d(ln mu) encoding scale dependence of a coupling."),
    ("weyl anomaly",       "NOUN", "I_Symmetry",  2, "Quantum violation of Weyl invariance encoded in the trace of T_munu."),
    ("partition function", "NOUN", "M_Charge",    7, "Generating functional of correlation functions."),
    ("path integral",      "NOUN", "A_Flux",      7, "Sum over all field histories weighted by exp(iS/hbar)."),

    # ── condensed matter ──────────────────────────────────────────────────────
    ("hubbard",            "ADJECTIVE", "A_Force", 1, "Pertaining to on-site repulsion in lattice fermion models."),
    ("hatsugai-kohmoto",   "ADJECTIVE", "A_Force", 1, "HK model: exactly-solvable variant of Hubbard with all-to-all interaction."),
    ("parafermion",        "NOUN", "I_Topology",  1, "Z_N generalization of Majorana zero modes."),
    ("anyon",              "NOUN", "I_Topology",  1, "2D excitation with fractional exchange statistics."),
    ("braiding",           "NOUN", "I_Connectivity", 1, "Topological operation of exchanging anyons along worldlines."),
    ("fusion",             "NOUN", "I_Connectivity", 1, "Combining two anyons to give a definite anyon type."),
    ("verlinde",           "ADJECTIVE", "I_Symmetry", 1, "Pertaining to Verlinde lines and their fusion algebra."),
    ("verlinde line",      "NOUN", "I_Symmetry",  1, "Topological line operator in a 2D CFT."),
    ("moore-read",         "ADJECTIVE", "I_Topology", 1, "Non-Abelian fractional quantum Hall state at nu=1/2."),
    ("filling",            "NOUN", "M_Count",     1, "Average occupation of a lattice site or Landau level."),
    ("tunneling",          "NOUN", "A_Flux",      1, "Quantum hopping of a particle between sites."),
    ("hopping",            "NOUN", "A_Flux",      1, "Nearest-neighbor kinetic term in a tight-binding model."),
    ("mott",               "ADJECTIVE", "P_Phase", 1, "Insulating phase driven by strong interactions at half-filling."),
    ("berry",              "ADJECTIVE", "I_Symmetry", 1, "Pertaining to Berry phase / Berry curvature / Berry connection."),
    ("chern",              "ADJECTIVE", "I_Topology", 1, "Pertaining to Chern number / Chern class."),
    ("chern number",       "NOUN", "I_Topology",  1, "Integer topological invariant of a band Bloch bundle."),
    ("wannier",            "NOUN", "I_Topology",  1, "Maximally localized orbital basis derived from Bloch states."),
    ("brillouin",          "NOUN", "I_Topology",  1, "First Brillouin zone: primitive cell of reciprocal lattice."),
    ("quantum metric",     "NOUN", "I_Dimension", 1, "Real symmetric part of the quantum geometric tensor on a band."),
    ("fermi surface",      "NOUN", "I_Topology",  1, "Locus of zero-energy single-particle excitations."),
    ("fermi liquid",       "NOUN", "P_Phase",     1, "Phase of weakly interacting fermions with long-lived quasiparticles."),
    ("quasiparticle",      "NOUN", "I_Topology",  1, "Long-lived excitation of an interacting system."),
    ("spin squeezing",     "NOUN", "I_Symmetry",  4, "Redistribution of quantum uncertainty among collective spin components."),
    ("wineland parameter", "NOUN", "P_Ratio",     4, "Spin-squeezing parameter quantifying metrological gain."),
    ("dephasing",          "NOUN", "P_Tax",       4, "Loss of off-diagonal coherence without population change."),
    ("dissipation",        "NOUN", "P_Tax",       4, "Energy loss to environmental degrees of freedom."),
    ("lindblad",           "ADJECTIVE", "P_Tax",  4, "Pertaining to trace-preserving completely-positive Markovian dynamics."),
    ("dissipator",         "NOUN", "P_Tax",       4, "Non-Hamiltonian generator of an open-system master equation."),
    ("kraus",              "ADJECTIVE", "P_Tax",  4, "Pertaining to operator-sum representation of quantum channels."),
    ("kraus operator",     "NOUN", "P_Tax",       4, "Operator in the sum representation of a quantum channel."),
    ("squeezed state",     "NOUN", "P_Phase",     4, "Gaussian state with sub-shot-noise variance in one quadrature."),
    ("coherent state",     "NOUN", "P_Coherence", 4, "Eigenstate of the photon annihilation operator; minimum-uncertainty state."),
    ("holevo",             "ADJECTIVE", "I_Complexity", 4, "Upper bound on accessible classical information from a quantum ensemble."),
    ("holevo information", "NOUN", "I_Complexity", 4, "Mutual information bound for classical-quantum ensembles."),
    ("matrix product",     "NOUN", "I_Connectivity", 4, "Compact representation of 1D quantum states as tensor networks."),
    ("bond dimension",     "NOUN", "I_Dimension", 4, "Auxiliary index size controlling MPS entanglement capacity."),
    ("qubit",              "NOUN", "I_Topology",  4, "Two-level quantum system."),
    ("pauli",              "ADJECTIVE", "I_Symmetry", 4, "Pertaining to the Pauli sigma matrices generating SU(2)."),

    # ── GR / holography ───────────────────────────────────────────────────────
    ("holographic",        "ADJECTIVE", "I_Topology", 2, "Realising a lower-dim QFT as a higher-dim gravitational dual."),
    ("ads",                "NOUN", "I_Topology",  2, "Anti-de Sitter spacetime: maximally symmetric negative curvature."),
    ("bcft",               "NOUN", "I_Topology",  2, "Boundary conformal field theory."),
    ("brane",              "NOUN", "I_Topology",  2, "Extended object on which open strings or EOW boundaries can end."),
    ("einstein-hilbert",   "ADJECTIVE", "A_Energy", 2, "Standard gravitational action integral of sqrt(-g)*R."),
    ("palatini",           "ADJECTIVE", "A_Energy", 2, "First-order formulation treating metric and connection independently."),
    ("chern-simons",       "ADJECTIVE", "I_Topology", 2, "Topological gauge action defined via the CS 3-form."),
    ("efolds",             "NOUN", "P_Ratio",     2, "Logarithmic measure of inflationary expansion."),
    ("scale factor",       "NOUN", "P_Ratio",     2, "Cosmological function controlling spatial dilation."),
    ("qft",                "NOUN", "I_Topology",  0, "Quantum field theory: framework combining QM and special relativity."),

    # ── optics / cavity ───────────────────────────────────────────────────────
    ("cavity",             "NOUN", "I_Topology",  3, "Bounded electromagnetic region supporting discrete modes."),
    ("optical",            "ADJECTIVE", "A_Flux", 3, "Pertaining to visible-frequency electromagnetic phenomena."),
    ("tweezer",            "NOUN", "A_Force",     3, "Tightly focused laser beam trapping a particle by gradient force."),
    ("polarizability",     "NOUN", "I_Density",   3, "Linear response of dipole moment to applied electric field."),
    ("rayleigh range",     "NOUN", "I_Dimension", 3, "Axial distance over which a Gaussian beam waist doubles in area."),
    ("opa",                "NOUN", "A_Flux",      3, "Optical parametric amplifier producing squeezed/entangled light."),
    ("squeezed",           "ADJECTIVE", "P_Phase", 4, "Having sub-vacuum quadrature noise."),
    ("photocurrent",       "NOUN", "A_Flux",      3, "Detector current produced by an incident optical field."),
    ("oam",                "NOUN", "A_Spin",      3, "Orbital angular momentum of a structured optical field."),
    ("helicity",           "NOUN", "A_Spin",      3, "Projection of spin along the direction of motion."),
    ("harmonic",           "NOUN", "A_Resonance", 3, "Integer-multiple frequency component."),

    # ── hydrodynamics ─────────────────────────────────────────────────────────
    ("rayleigh",           "ADJECTIVE", "P_Ratio", 5, "Pertaining to Lord Rayleigh; in hydrodynamics the Ra number."),
    ("rayleigh number",    "NOUN", "P_Ratio",     5, "Dimensionless ratio controlling onset of convection."),
    ("prandtl",            "NOUN", "P_Ratio",     5, "Ratio of momentum diffusivity to thermal diffusivity."),
    ("convection",         "NOUN", "A_Flux",      5, "Heat transport by bulk fluid motion."),
    ("benard",             "ADJECTIVE", "A_Resonance", 5, "Of the Rayleigh-Benard convective instability."),
    ("darcy",              "NOUN", "P_Ratio",     5, "Empirical law for slow flow in porous media."),
    ("eigenfunction",      "NOUN", "I_Symmetry",  7, "Function on which a linear operator acts as a scalar multiple."),
    ("eigenvalue",         "NOUN", "P_Limit",     7, "Scalar associated with an eigenfunction by a linear operator."),
    ("wavenumber",         "NOUN", "I_Dimension", 5, "Spatial frequency 2*pi/lambda of a wave."),
    ("instability",        "NOUN", "P_Tax",       5, "Tendency of a state to grow perturbations exponentially."),

    # ── stochastic / bio ──────────────────────────────────────────────────────
    ("growth rate",        "NOUN", "P_Ratio",     6, "Exponential rate of size or population increase."),
    ("gamma distribution", "NOUN", "P_Probability", 6, "Continuous distribution parameterised by shape and rate."),
    ("waiting time",       "NOUN", "M_Time",      6, "Random duration between two events of a stochastic process."),
    ("autocatalytic",      "ADJECTIVE", "A_Force", 6, "Of a reaction in which a product catalyzes its own production."),
    ("homeostasis",        "NOUN", "P_Coherence", 6, "Stable maintenance of internal state under perturbation."),
    ("variance",           "NOUN", "P_Probability", 6, "Second central moment of a probability distribution."),
    ("dispersion",         "NOUN", "P_Probability", 6, "Spread of a distribution; or k-omega relation of a wave."),

    # ── mathematical structure ────────────────────────────────────────────────
    ("hilbert",            "ADJECTIVE", "I_Topology", 7, "Of complete inner-product spaces."),
    ("hilbert space",      "NOUN", "I_Topology",  7, "Complete complex inner-product space."),
    ("projector",          "NOUN", "I_Symmetry",  7, "Idempotent Hermitian operator with eigenvalues 0 and 1."),
    ("commutator",         "NOUN", "I_Connectivity", 7, "[A,B] = AB - BA, measuring non-commutativity."),
    ("anticommutator",     "NOUN", "I_Connectivity", 7, "{A,B} = AB + BA, central to fermionic algebra."),
    ("expectation value",  "NOUN", "P_Probability", 7, "Mean of an observable in a quantum state."),
    ("ground state",       "NOUN", "P_Phase",     7, "Lowest-energy eigenstate of a Hamiltonian."),
    ("excited state",      "NOUN", "P_Phase",     7, "Eigenstate of higher energy than the ground state."),
    ("density matrix",     "NOUN", "P_Probability", 7, "Positive trace-1 operator describing a mixed quantum state."),
    ("trace",              "NOUN", "M_Count",     7, "Sum of diagonal elements of a matrix."),
    ("lattice",            "NOUN", "I_Topology",  7, "Discrete subgroup of Euclidean space; or a periodic crystal."),
    ("crystal",            "NOUN", "I_Topology",  1, "Periodic arrangement of atoms with long-range order."),

    # ── core verbs the existing engine sorely lacked ──────────────────────────
    ("commute",            "VERB", "I_Symmetry",  7, "To satisfy [A,B] = 0."),
    ("derive",             "VERB", "A_Flux",      7, "To obtain a result from prior premises."),
    ("scale",              "VERB", "P_Ratio",     7, "To change under a rescaling of length or energy."),
    ("converge",           "VERB", "P_Limit",     7, "To approach a limit."),
    ("diverge",            "VERB", "P_Limit",     7, "To grow without bound."),
    ("interact",           "VERB", "A_Force",     0, "To couple to another degree of freedom."),
    ("propagate",          "VERB", "A_Flux",      0, "To travel through space-time."),
    ("oscillate",          "VERB", "A_Resonance", 0, "To vary periodically in time."),
    ("squeeze",            "VERB", "P_Phase",     4, "To reduce uncertainty in one variable at the cost of its conjugate."),
    ("dissipate",          "VERB", "P_Tax",       4, "To lose energy or coherence to an environment."),
    ("evolve",             "VERB", "A_Flux",      7, "To change in time according to a dynamical law."),
    ("renormalize",        "VERB", "P_Tax",       0, "To absorb divergences into redefined parameters."),
    ("regularize",         "VERB", "P_Limit",     0, "To assign finite meaning to a divergent expression."),
    ("braid",              "VERB", "I_Connectivity", 1, "To interchange worldlines of anyons or zero-modes."),

    # ── vector / linear algebra ops (for vector-physics queries) ──────────────
    ("dot product",        "NOUN", "I_Connectivity", 7, "Scalar product of two vectors: a.b = sum(a_i * b_i)."),
    ("cross product",      "NOUN", "I_Connectivity", 7, "Vector product of two 3D vectors."),
    ("magnitude",          "NOUN", "M_Count",     7, "Euclidean length (L2 norm) of a vector."),
    ("vector",             "NOUN", "I_Dimension", 7, "Element of a vector space with magnitude and direction."),
    ("norm",               "NOUN", "P_Limit",     7, "Function assigning a length to a vector."),

    # ── adjectives ────────────────────────────────────────────────────────────
    ("quantum",            "ADJECTIVE", "I_Symmetry", 7, "Pertaining to the quantization of physical observables."),
    ("classical",          "ADJECTIVE", "I_Symmetry", 7, "Non-quantum; obeying deterministic equations of motion."),
    ("topological",        "ADJECTIVE", "I_Topology", 1, "Invariant under continuous deformation."),
    ("perturbative",       "ADJECTIVE", "P_Limit",  0, "Expanded as a power series in a small coupling."),
    ("nonperturbative",    "ADJECTIVE", "P_Limit",  0, "Containing contributions invisible to any finite-order expansion."),
    ("critical",           "ADJECTIVE", "P_Phase", 1, "At a continuous phase transition."),
    ("relativistic",       "ADJECTIVE", "A_Velocity", 2, "Lorentz-invariant; involving speeds near c."),
    ("massless",           "ADJECTIVE", "M_Mass",  0, "Having zero rest mass."),
    ("massive",            "ADJECTIVE", "M_Mass",  0, "Having nonzero rest mass."),
    ("isotropic",          "ADJECTIVE", "I_Symmetry", 7, "Invariant under rotations."),
    ("anisotropic",        "ADJECTIVE", "I_Symmetry", 7, "Not isotropic."),
    ("free",               "ADJECTIVE", "A_Energy", 0, "Non-interacting (in field theory) or unconstrained (in mechanics)."),
    ("strong",             "ADJECTIVE", "A_Force", 0, "Pertaining to the strong nuclear interaction or to a large coupling regime."),
    ("weak",               "ADJECTIVE", "A_Force", 0, "Pertaining to the weak nuclear interaction or to a small coupling regime."),
    ("on-shell",           "ADJECTIVE", "P_Limit", 0, "Satisfying the classical equations of motion."),
    ("off-shell",          "ADJECTIVE", "P_Limit", 0, "Not satisfying the classical equations of motion."),
    ("infrared",           "ADJECTIVE", "P_Limit", 0, "Pertaining to low-energy (long-wavelength) phenomena."),
    ("ultraviolet",        "ADJECTIVE", "P_Limit", 0, "Pertaining to high-energy (short-wavelength) phenomena."),

    # ── operators ─────────────────────────────────────────────────────────────
    ("commute_with",       "OPERATOR", "I_Symmetry", 7, "Binary relation: [A,B] = 0."),
    ("scales_as",          "OPERATOR", "P_Ratio",  7, "Binary relation: f(lambda*x) = lambda^n * f(x)."),
    ("dual_to",            "OPERATOR", "I_Symmetry", 7, "Binary relation indicating an equivalence under a duality map."),
    ("gradient_of",        "OPERATOR", "A_Velocity", 7, "Unary operator: nabla dot."),
    ("integral_of",        "OPERATOR", "A_Flux",   7, "Unary operator: integral of."),
    ("expectation_of",     "OPERATOR", "P_Probability", 7, "Unary operator: <.>"),
]


# ── 4. PACK ASSEMBLY ─────────────────────────────────────────────────────────

@dataclass
class PackEntry:
    term: str
    vector: List[int]
    role: str
    mog_category: str
    definition: str
    ubp_id: str


def build_pack() -> List[PackEntry]:
    """Build the physics pack.  All entries are accepted (the deterministic
    derivation already constrains the weight to a Leech-typical range and
    snaps to a Golay codeword)."""
    out: List[PackEntry] = []
    seen = set()
    for term, role, cat, dom, defn in PHYSICS_LEXICON:
        key = term.lower()
        if key in seen:
            continue
        seen.add(key)
        vec = derive_term_vector(term, cat, role, dom)
        ubp_id = "PVE_" + hashlib.sha256(key.encode()).hexdigest()[:24]
        out.append(PackEntry(term=key, vector=vec, role=role, mog_category=cat,
                             definition=defn, ubp_id=ubp_id))
    return out


def inject_physics_pack(words: dict) -> dict:
    """Inject physics pack entries into a live vocabulary dict.

    Skips any term already present (KB-derived entries take precedence).
    Returns a report dict for diagnostics.
    """
    report = {"injected": 0, "skipped": 0, "definitions_added": 0}
    pack = build_pack()
    for entry in pack:
        if entry.term in words:
            # If existing entry has no description but we have one, fill it in
            existing = words[entry.term]
            if not getattr(existing, 'definition', None) and entry.definition:
                # WordEntry doesn't have a definition field by default, but we
                # can attach it dynamically for the response composer.
                try:
                    existing.definition = entry.definition
                    report["definitions_added"] += 1
                except Exception:
                    pass
            report["skipped"] += 1
            continue
        words[entry.term] = WordEntry(
            word=entry.term, vector=entry.vector, role=entry.role,
            ubp_id=entry.ubp_id, nrci=float(LEECH_ENGINE.calculate_nrci(entry.vector)),
            golay_codeword=entry.vector,
            fold3=BLA.fold24_to3(entry.vector),
            mog_category=entry.mog_category,
        )
        # Attach the definition as a dynamic attribute so the response composer
        # can surface it without requiring KB lookup.
        words[entry.term].definition = entry.definition  # type: ignore[attr-defined]
        report["injected"] += 1
    return report


def get_pack_summary() -> Dict[str, int]:
    by_role: Dict[str, int] = {}
    by_domain: Dict[int, int] = {}
    for term, role, cat, dom, _ in PHYSICS_LEXICON:
        by_role[role] = by_role.get(role, 0) + 1
        by_domain[dom] = by_domain.get(dom, 0) + 1
    return {"total": len(PHYSICS_LEXICON),
            "by_role": by_role,
            "by_domain": by_domain}


# ── 5. ISOLATION TEST ────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=== Testing Module 15: Physics Vocabulary Pack (v3.8.0) ===")
    s = get_pack_summary()
    print(f"Total terms: {s['total']}")
    print(f"By role: {s['by_role']}")
    print(f"By domain: {s['by_domain']}")
    print()
    pack = build_pack()
    print(f"Built {len(pack)} pack entries.")
    # Verify deterministic: same term -> same vector
    v1 = derive_term_vector("weyl anomaly", "I_Symmetry", "NOUN", 2)
    v2 = derive_term_vector("weyl anomaly", "I_Symmetry", "NOUN", 2)
    print(f"  Determinism check: {v1 == v2}")
    # Check weight is in [6, 18]
    w = sum(v1)
    print(f"  'weyl anomaly' vector weight: {w} (must be in [6, 18])")
    # Show a few entries
    for e in pack[:3]:
        print(f"  {e.term:30s} role={e.role:10s} cat={e.mog_category:12s} def='{e.definition[:50]}...'")
