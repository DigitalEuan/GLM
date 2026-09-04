# Positioning — what is being claimed, and what is not

*Read this before starting a round. It is short on purpose, and every other
document in the repository is written on the assumption that it has been read.*

---

## 1. The claim

**We are not claiming that the lattice generates the universe.** The claim is
narrower, and it is testable: there is an *exact* substrate — the Golay code,
the Leech lattice, and the arithmetic on them, integer and `Fraction` exact
throughout (directive D7) — and reality maps onto it with unusual fidelity.

"Unusual fidelity" is a measurement, not an adjective. Wherever this repository
asserts it, there is a control beside it — a digest, a reshuffle, a chance
baseline — and the assertion stands only by the margin over that control. Where
the margin is not there, the study says so; nine of the retrieved results are
negative results, kept because a refuted claim is a result.

## 2. What the GLM is

The **Geometric Language Machine (GLM)** is the experimental implementation of
that mapping. It exists to answer four questions, and each one is a question
about what the machine can be made to do rather than about what the substrate
is:

1. Can language, mathematics and program text be mapped onto the Leech lattice,
   using the Golay code and the other systems developed here?
2. Can the GLM *reason* with the information that mapping gives it?
3. Can it be generative — work with what it holds, rather than only recall it?
4. Can it solve problems and produce results that are real, accurate and
   checkable?

Every one of those is answerable by running something.
[`CAPABILITY_ASSESSMENT.md`](CAPABILITY_ASSESSMENT.md) is where the current
answers live, and each is a probe that either holds or breaks.

## 3. Layers, and why an absence is not a refutation

Some of what the substrate holds is hidden by the layer it is read at. Every
carrier here is a **projection at a stated resolution** — the 24-bit word, the
syndrome, the MOG cell, the Leech point, the shell — so a correspondence that
is invisible at one layer can be exact one layer up.

The working consequence: **check a claim from several layers and resolutions
before calling it absent.** An absence at one resolution is a statement about
that resolution, not about the substrate.

Two studies measure exactly what each step down discards, so that this is a
measurement rather than an excuse:

* [`studies/COMBINER_STUDY.md`](studies/COMBINER_STUDY.md) — what XOR loses
  (uniformly `2²⁴`-to-one, which is the pigeonhole bound for *any* combiner of
  that output width), and what a wider output buys back.
* [`studies/INFORMATION_LOSS_STUDY.md`](studies/INFORMATION_LOSS_STUDY.md) —
  what each layer of the stack cannot see, listed pair by pair rather than
  asserted.

## 4. What follows from this in practice

* A result is stated at the layer it was measured at, and the layer is named.
* A negative result is recorded, not discarded; it is the cheapest thing this
  project produces and the most easily lost.
* No claim of correspondence is made without the control it was measured
  against.
* The substrate stays exact: integers and `Fraction`, no floats (D7).
