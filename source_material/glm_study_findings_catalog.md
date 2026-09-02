# Catalog of Empirical Findings and Subsystem Insights: GLM-3+ Research Suite

This catalog serves as the authoritative, mathematically rigorous, and empirical record of the findings, benchmarks, and architectural insights established across the various subsystem studies of the **Geometric Language Machine (GLM-3+)**. 

Each study is cataloged below with its core research question, mathematical formulation, exact empirical results, and system-development implications.

---

## 1. Iteration Drift and the Lattice Landscape
**Source:** *GLM_Iteration_Study.pdf*

### 1.1 Research Question
Does the Universal Binary Principle’s (UBP) absolute prohibition on floating-point arithmetic (no floats, exact arithmetic over $\mathbb{Q}$) actually matter in practice? What is the rate of numerical drift under repeated agent-tool-memory handoffs?

### 1.2 Mathematical Formulation
The study establishes a stress test using a parametric family of rational recurrences over odd primes $p > 2$ with an initial condition of $X_0 = 1/p$ and an inhomogeneous term of $-1/p$:

$$\text{Contractive Rule (Fixed Point } X^* = -1\text{): } X_{n+1} = \frac{p-1}{p} X_n - \frac{1}{p}$$
$$\text{Accumulative Rule (Unstable Point } X^* = 1\text{): } X_{n+1} = \frac{p+1}{p} X_n - \frac{1}{p}$$

Because $1/p$ has no finite binary expansion in base-2 for any odd prime, floating-point representations must introduce a rounding error of approximately $1.1 \times 10^{-16}/p$ at Step 0. The recurrence is iterated for 200 steps across three regimes:
1. **Exact Rational ($\mathbb{Q}$):** Using Python's arbitrary-precision `fractions.Fraction`.
2. **IEEE-754 Lossless:** Standard 64-bit float with lossless `repr()` round-trips.
3. **IEEE-754 Display-Truncated:** Simulating an AI tool loop by truncating the float to 6 or 4 significant decimal digits (display6 / display4) at each step before parsing back.

### 1.3 Key Empirical Findings
* **Contractive Path (Damped Jitter):** Under the contractive rule, the physical dynamics of the map damp per-step rounding errors. The absolute drift remains strictly bounded by the truncation ceiling of the regime across all 200 steps (lossless stays at $10^{-16}$ machine epsilon, display6 at $10^{-6}$, and display4 at $10^{-4}$).
* **Accumulative Path (Geometric Explosion):** Under the expansive rule, the starting rounding error is amplified by $\left(\frac{p+1}{p}\right)^n$ at each step.
  * For $p=3$, the true rational value at step 200 is $X_{200} \approx 7.5 \times 10^{10}$.
  * **Lossless Float64 Drift:** Reaches an absolute error of **$7.5 \times 10^{10}$** (relative error $\approx 1.0$), meaning the float has lost all semantic information and represents pure, compounded noise.
  * **Display6 Truncation Drift:** Explodes to an astronomical **$6.0 \times 10^{19}$** (eight orders of magnitude worse than the lossless regime).
  * **Display4 Truncation Drift:** Reaches **$2.2 \times 10^{22}$**.
* **Divergence Onset ($>10^{-9}$):** The first step where drift becomes meaningful ($>10^{-9}$) is strictly **Step 1 or 2** for both display6 and display4 regimes across all primes tested. Lossless floats reach this boundary at Step 46 for $p=3$, but never within 200 steps for $p \ge 17$.

| Prime ($p$) | Rule | Lossless Final Drift | Display6 Final Drift | Display4 Final Drift |
|---|---|---|---|---|
| **p = 3** | Contractive | $4.4 \times 10^{-16}$ | $1.0 \times 10^{-6}$ | $1.0 \times 10^{-4}$ |
| **p = 3** | Accumulative | $7.5 \times 10^{10}$ | $6.0 \times 10^{19}$ | $2.2 \times 10^{22}$ |
| **p = 5** | Contractive | $2.2 \times 10^{-16}$ | $2.0 \times 10^{-6}$ | $2.0 \times 10^{-4}$ |
| **p = 5** | Accumulative | $4.2 \times 10^{1}$ | $1.6 \times 10^{10}$ | $2.1 \times 10^{12}$ |
| **p = 23** | Contractive | $0.0$ (Exact) | $7.0 \times 10^{-7}$ | $9.6 \times 10^{-4}$ |
| **p = 23** | Accumulative | $2.9 \times 10^{-11}$ | $7.9 \times 10^{-2}$ | $1.5 \times 10^{0}$ |

### 1.4 Code-Lattice Pairings & The A $\to$ B $\to$ C Ladder
The study maps the broader mathematical landscape of error-correcting codes systematically lifted to continuous Euclidean sphere packings:

| Dimension ($d$) | Code | Lattice | Kissing Number | Method / Conditions |
|---|---|---|---|---|
| **4** | Parity $[4,3,2]$ | $D_4$ | 24 | Construction A |
| **8** | Ext. Hamming $[8,4,4]$ | $E_8$ (Gosset) | 240 | Construction A (Even unimodular) |
| **12** | Ternary Golay $[12,6,6]$ | $K_{12}$ (Coxeter-Todd) | 756 | Construction A over $\mathbb{F}_3$ |
| **16** | Reed-Muller $RM(1,4)$ | $BW_{16}$ (Barnes-Wall) | 4,320 | Construction A |
| **24** | **Ext. Binary Golay $[24,12,8]$** | **$\Lambda_{24}$ (Leech)** | **196,560** | **Construction A $\to$ B $\to$ C** |
| **32** | Extremal QR $[32,16,8]$ | $Q_{32}$ (Quebbemann) | 146,880 | Construction A |
| **48** | Extremal Type II $[48,24,12]$ | $P_{48n}$ | $\sim 5.2 \times 10^{9}$ | - |

The Leech lattice $\Lambda_{24}$ is reached from the Golay support via a progressive ladder of congruence conditions, with every condition proven strictly necessary to prevent short vectors from slipping below the minimal norm:
1. **Construction A:** mod-2 Golay support $\implies$ minimal norm$^2$ 16, kissing number **48**.
2. **Construction B:** + mod-4 even parity ($\sum x_i \equiv 0 \pmod 4$) $\implies$ minimal norm$^2$ 32, kissing number **98,256**.
3. **Construction C:** + mod-8 coordinate-sum ($\sum x_i \equiv 4m \pmod 8$) and adjoin the odd glue coset $(-3, 1^{23})$ $\implies$ minimal norm$^2$ 32, kissing number **196,560**.

---

## 2. The Generators and Containers of Real Processes
**Source:** *GLM_Generators_Containers.pdf*

### 2.1 Research Question
How can the GLM reason over irrational or transcendental numbers without using floats? What are the mathematical, temporal, and geometric "containers" that uniquely define a number?

### 2.2 Phase 1: Algorithmic Step Cost (The Algorithmic Container)
The study measures the exact number of generator steps required in exact rational arithmetic to reach 10, 30, and 50 bits of precision:
* **Algebraic Irrationals (Babylonian/Heron's Method):** Converge *quadratically* (correct bits double at each step).
  * $\sqrt{2}, \sqrt{3}$: Reach 50 bits of precision in exactly **5 steps** (100 bits in 8 steps).
  * $\sqrt{5}$ through $\sqrt{13}$: Reach 50 bits in **6 steps** (100 bits in 9 steps).
  * $\sqrt{15}$ through $\sqrt{23}$: Reach 50 bits in **7 steps** (100 bits in 10 steps).
* **Transcendental Constants (Geometric Convergence):** Each term adds a fixed number of bits.
  * $\pi$ (via Machin's arctangent series formula): Reaches 50 bits in **9 steps** (converges at a rate of $1/25$ per term, yielding $\approx 2.32$ bits/step).
  * $e$ (via exponential Taylor series): Reaches 50 bits in **17 steps** (error bounded by $2/(k+1)!$).
* **Exotic and Algorithmically Random Constants:**
  * **Liouville's Constant:** Reaches 50 bits in just **3 steps** because its sparse factorial expansion ($10^{-n!}$) makes it exact rapidly.
  * **Champernowne's Number and Chaitin $\Omega$ LCG Surrogate:** Reveal exactly 1 bit per step, behaving *linearly*. They fail to reach 50 bits within 30 generator steps.

### 2.3 Phase 2: Spectral Wobble Analysis (The Temporal Container)
Running each target through a 10,000-step first-order Delta-Sigma modulator converts the continuous target into a deterministic stream of discrete snaps (0s and 1s), revealing their unique "vibrational signatures":

| Constant | Fractional Target | Wobble Shannon Entropy | Autocorrelation Lag 1 [AC(1)] | AC(100) | Mean Run Length | Max Run Length |
|---|---|---|---|---|---|---|
| **$\Omega$ Surrogate** | $0.567143$ | **$0.980$** | $-0.671$ | $-0.163$ | $1.20$ | $2$ |
| **$\sqrt{2}-1$** | $0.414214$ | **$0.979$** | $-0.657$ | $-0.657$ | $1.21$ | $2$ |
| **$\phi-1$** | $0.618034$ | **$0.959$** | $-0.528$ | $+0.214$ | $1.31$ | $2$ |
| **$1/3$ Baseline** | $0.333333$ | $0.918$ | $-0.333$ | $-0.333$ | $1.50$ | $2$ |
| **$e-2$** | $0.718282$ | $0.858$ | $-0.127$ | $+0.313$ | $1.77$ | $3$ |
| **$\pi-3$** | $0.141593$ | $0.588$ | $+0.434$ | $+0.434$ | $3.53$ | $7$ |
| **Liouville** | $0.110001$ | **$0.500$** | $+0.560$ | $+1.000$ | $4.55$ | - |
| **$\alpha$ (Fine-Structure)** | $0.007297$ | **$0.062$** | $-0.007$ | $-0.007$ | $68.49$ | **$137$** |
| **$e^\pi - \pi$** | $0.999100$ | **$0.011$** | $-0.001$ | $-0.001$ | $500.00$ | **$1110$** |

* **Sturmian Quasiperiodicity:** The algebraic irrationals ($\sqrt{2}, \phi$) produce highly structured Sturmian word sequences. They show a strong negative AC at lag 1, indicating rapid alternation (0101...), which decays quasiperiodically over larger lags.
* **Transcendental Run-Lengths:** $\pi$ and $e$ have smaller fractional parts, yielding positive AC across lags (self-similar, non-quasiperiodic structure) and longer run lengths.
* **Extreme Signatures:** The uncomputable Chaitin $\Omega$ surrogate has near-maximal entropy, while the sparse Liouville's constant collapses to the minimum entropy.

### 2.4 Phase 3: The 24-D Leech Hull Census (The Geometric Container)
By projecting each constant into a 24-dimensional target vector and testing its containment against 150 Leech minimal vectors, the study identifies a sharp, physical boundary:

* **Leech minimal vectors** have a fixed norm of $\sqrt{32} \approx 5.66$.
* **Inside the Hull:** Only **Liouville's constant** sits inside the hull (Target Norm **$0.56$**, Margin **$-5.38$**) because of its near-zero magnitude.
* **Outside the Hull (Hull Certificates):** Algebraic and transcendental constants scale far beyond the packing boundary ($\sqrt{2}$ norm 7.16, margin $+4.17$; $\pi$ norm 15.92, margin $+12.92$; $e$ norm 13.77, margin $+10.77$). The system generates an exact separating linear functional (hull certificate)—a mathematical proof that no quantizer rule can ever converge to these targets on the substrate.

---

## 3. The 53-Bit Mantissa Question
**Source:** *GLM_53bit_Mantissa_Answer.pdf*

### 3.1 Research Question
Can the GLM track the bit-allocation and precision loss inside the standard 53-bit IEEE-754 significand (52 explicit fraction bits + 1 implicit hidden bit) during the Prime Iteration Test?

### 3.2 Key Empirical Findings
* **Immediate 10-Bit Collapse:** Across all odd primes $p \in \{3, 5, 7, 11, 13, 17, 23\}$ and both rules (contractive and accumulative), **exactly 10 bits of significand precision are lost by step 0 or step 1—the very first operation**. Because $1/p$ has an infinite repeating binary expansion, the double-precision float must round the trailing bits instantly.
* **Runaway Degeneracy:** By Step 100, the accumulative rule has lost **24 to 32 bits** of its 52-bit mantissa.
* **The GLM's Superior Eyesight:** While the float is blind, the GLM (operating with exact rational fractions) sees **100 bits of the binary expansion** (48 more than IEEE-754) and knows the exact **binary period** of $1/p$ (the multiplicative order of 2 modulo $p$):

| Prime ($p$) | Multiplicative Order [Binary Period of $1/p$] | Leech Substrate Hamming Distance (Exact vs. Float) | Substrate Representation Class |
|---|---|---|---|
| **p = 3** | **2** | **0** | **Substrate-Faithful** (Lands on exact same Leech point) |
| **p = 5** | **4** | **24** | **Substrate-Inverted** (Lands on antipodal point; every coordinate disagrees) |
| **p = 7** | **3** | **0** | **Substrate-Faithful** (Lands on exact same Leech point) |
| **p = 11** | **10** | **10** | Intermediate Drift |
| **p = 13** | **12** | **16** | Intermediate Drift |
| **p = 17** | **8** | **12** | Intermediate Drift |
| **p = 23** | **11** | **10** | Intermediate Drift |

This proves that floating-point "hallucinations" in iterative AI systems are not statistical quirks, but deterministic consequences of hardware truncation.

---

## 4. The Physical-Mechanical Engine Series
**Sources:** *GLM_TDCE_Engine_Study.pdf, GLM_Advanced_Engine_Family.pdf, GLM_Optimal_Engine.pdf*

### 4.1 Research Question
Does translating the GLM's exact rational computations into physical-mechanical analogues (springs, dashpots, escapements, radiators, and gearboxes) yield measurably better results than a naive direct-encoding approach?

### 4.2 The Thermo-Dynamic Carrier Engine (TDCE)
The first prototype routes target values through a 4-stage mechanical pipeline: Delta-Sigma accumulator, modular escapements (mod 2/4/8/144/256), Leech lattice snap, and dyadic escalation.
* **Successes:** The TDCE achieves full 60-bit precision on exotic constants (Champernowne, $\Omega$ surrogate) where the naive baseline stalls at **21–22 bits** ($2.7\times$ improvement) and dissipates lower "TAX" strain on irrationals ($0.1\times - 0.5\times$ of naive).
* **Failures:** The TDCE is **$\sim 22\times$ more expensive** in integer arithmetic operations, produces lower-entropy wobble streams, and triggers escalation events on stress tests. 

### 4.3 Subsystem Optimizations
To resolve the TDCE's massive computational overhead, three advanced stages were engineered:
1. **Radiator (Cooling):** Periodically dissipates accumulated TAX strain every $N$ steps. This prevents premature dyadic escalation, successfully reducing the TAX on a $\pi$ run by **15,000$\times$**.
2. **Multi-Fuel (Parallel Generators):** Runs two mathematical generators in parallel (e.g., Newton's method + continued fractions) and dynamically takes the one with lower error at each step, utilizing cached trajectories.
3. **Turbocharger (Adaptive Snap):** Dynamically adjusts the Leech lattice snapping strategy based on current strain:
   * *Tight Snap* ($|e| < 1$): Evaluates the local space.
   * *Relaxed Snap* ($1 \le |e| < 4$): Evaluates a coarser grid.
   * *Skip Snap* ($|e| \ge 4$): Bypasses search, preserving CPU cycles when strain is high.

### 4.4 The Optimal Engine
The culmination of the engine series integrates all six stages under a runtime **Gearbox Classifier** that identifies the incoming target's class (Rational, Algebraic, Transcendental, or Exotic) and shifts configurations dynamically. 
* **The Finding:** Achieves **100% Three Column Thinking (TCT) verification**—all 15 complex workloads (including $\pi+e$ and $\sqrt{2}\times\phi$) pass independent re-derivation in a fresh subprocess, with 10 of 15 workloads reaching full 60-bit precision.

---

## 5. Substrate-Native Bit Dynamics and Reversible Computing
**Source:** *GLM_Bit_Reversibility_Study.md*

### 5.1 Protocol I: Transition Entropy & Cliff Analysis
This protocol tests the hypothesis that positional binary counting introduces massive multi-bit "transition cliffs" (e.g., $011 \to 100$) that trigger unstable local noise (high transition entropy). It compares standard binary against Binary Reflected Gray Code (BRGC) over 10,000 steps:

| Metric | Standard Binary | BRGC (Gray) | Ratio / Difference |
|---|---|---|---|
| **Mean transitions per step** | $1.9946$ bits | $1.0000$ bit | **$1.99\times$ reduction** |
| **Max transition cliff** | **$11$ bits** | **$1$ bit** | **$11\times$ reduction** |
| **Transition Shannon Entropy** | $1.9939$ bits/symbol | $0.0000$ bits/symbol | Complete noise collapse |
| **Cumulative Symmetry TAX** | $7,791.56$ units | $3,896.75$ units | **Exactly 2:1 TAX conservation** |

Standard binary counting is noisy and traumatic, producing broadband noise and high-amplitude spikes. BRGC smooths out all transition cliffs, guaranteeing exactly 1 bit flip per step, zero transition entropy, and halving the geometric Symmetry TAX.

### 5.2 Protocol II: Reversible Gates & Landauer's Limit
To prevent silent information erasure—which under Landauer's Principle dissipates a minimum of $kT \ln 2$ of heat (expressed as Symmetry TAX strain)—this protocol partitions the MOG grid into eight vertical 3-bit sub-registers and tests logically reversible, self-inverse gates:
* **CCNOT (Toffoli):** $[c_1, c_2, c_3] \to [c_1, c_2, c_3 \oplus (c_1 \land c_2)]$
* **CSWAP (Fredkin):** Swap $c_2, c_3$ if $c_1 = 1$.
* **The 100-Operation Test:** Running 100 rounds of forward gates (800 total gate operations) and 100 rounds of backward gates on a random 24-bit MOG carrier returns a final Hamming distance of **exactly 0** (byte-identical starting state).
* **The Finding:** Reversible gates perfectly conserve the **Symmetry TAX** and **Refined NRCI** ($0.699965$ throughout), with zero syndrome accumulation. Standard lossy `AND` operations fail reversibility in 6 of 8 test cases, permanently destroying data.

### 5.3 Protocol III: Topological Defect Storage
This protocol tests whether bits can be stored as topological defects (solitons or phase kinks) propagating along 1D cyclic lattice strings rather than static coordinates, achieving immunity to coordinate-level noise.
* **Definition of a Kink:** A boundary where adjacent coordinates differ ($v_i \ne v_{i+1}$, with cyclic wrap-around).
* **The Finding:** Across 20 random vectors, the kink count is **perfectly conserved (20/20 PASS)** under 9 cyclic rotations (shifts of 1, 3, 5, 7, 11, 13, 17, 19, and 23 coordinates). Cyclic rotation merely shifts the spatial position of the kinks, not their count.
* **Soliton Injection:** A single coordinate bit flip is proven to alter the global kink count by **exactly $\pm 2$**, establishing a quantized, noise-immune unit of information.

### 5.4 Protocol IV: Persistent Homology of Perturbations
This protocol tests whether the birth/death of topological features (loops, voids, cavities) around lattice perturbations can classify carriers without reading their raw coordinates.
* **The Finding:** Mapping birth/death times (directly representing active coordinate Hamming weights) on persistence diagrams clusters 100 random carriers (50 physics, 50 chemistry) into their correct semantic domains with **100% classification accuracy**.

---

## 6. High-Fidelity Domain Applications
**Source:** *GLM Domain Applications: A Landscape Study*

To evaluate whether the Delta-Sigma modulator operating on the Leech lattice is "dynamics-native" and universally applicable, the substrate was tested across five distinct real-world domains:

### 6.1 Domain 2: The Electrical Oscillator (Resonance & SNR)
The electrical study maps physical resonance and Signal-to-Noise Ratio (SNR) directly to the wobble entropy of the Delta-Sigma stream:

* **Resonance IS Zero Wobble Entropy:** At exact resonance ($\omega/\omega_0 = 1.0$), the system achieves lock-in (gain exactly 1.0), and the modulator outputs a continuous stream of 1s—**collapsing the wobble entropy to exactly 0.0000**. Off-resonance frequencies produce high entropy (0.985 at ratio 0.9; 0.996 at ratio 1.1), creating a sharp V-shaped entropy dip that acts as the physical signature of resonance.
* **SNR IS Wobble Entropy:** For binary signals, the signal quality is proven to be a mathematical identity of wobble entropy:

| Condition / Signal Quality | Wobble Shannon Entropy | Modulator 1-Bit Density |
|---|---|---|
| **Pure Signal** | **$0.000$** | $1.000$ |
| **SNR = 40 dB** | $0.011$ | $0.999$ |
| **SNR = 20 dB** | $0.081$ | $0.990$ |
| **SNR = 10 dB** | $0.469$ | $0.900$ |
| **SNR = 0 dB** | **$1.000$** | $0.500$ |

### 6.2 The Unified Synthesis of Homeostasis
The landscape study proves that **the mathematics of homeostasis is universal**:
* **Chemical Equilibria:** Reactant concentrations and weak/strong acid dissociations map to Leech lattice points, where chemical stability is represented by lattice proximity.
* **Musical Harmony:** Musical intervals and chord structures map onto Leech coordinates, where harmonic consonance is represented by proximity to core lattice axes.
* **Economic Markets:** Price discovery and supply/demand wiggles are modeled as Delta-Sigma feedback loops, with high wobble entropy acting as a direct measure of market efficiency.
