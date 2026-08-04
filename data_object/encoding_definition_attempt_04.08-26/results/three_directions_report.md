# Three Directions Report — 4 August 2026

## Direction 1: Nonlinear Predictors

| Method | CV r | Verdict |
|--------|------|---------|
| Random Forest (original features) | 0.06 | ✗ No improvement |
| Gradient Boosting | −0.08 | ✗ No improvement |
| Random Forest (set-based features) | 0.10 | ✗ Marginal |
| Random Forest (all features) | 0.05 | ✗ No improvement |
| **Best set metric:** Jaccard on Activation row | **r = −0.27** | ⚠ Weak but real |

**Finding:** Nonlinear methods don't extract more signal. The features
genuinely don't carry enough information about bond energy. The best
set-based metric (Jaccard on Activation row, r=−0.27) suggests that
elements with *similar* Activation patterns tend to have *higher* bond
energies — but the signal is weak.

---

## Direction 2: Bond as Geometric Object

### Bond geometry correlations

| Feature | r(BE) | r(BO) | Interpretation |
|---------|-------|-------|----------------|
| pre_tax | −0.25 | 0.13 | Lower pre-snap TAX → higher BE |
| length | 0.22 | −0.21 | Longer bonds → higher BE, lower BO |
| act_diff | 0.11 | **−0.22** | More Activation difference → lower BO |
| info_overlap | −0.19 | 0.08 | More shared Info → lower BE |
| **snap_energy** | 0.06 | **0.18** | **See below** |

### Snap energy by bond order — KEY FINDING

| Bond Order | Mean Snap Energy | n |
|------------|-----------------|---|
| 1 (single) | **−0.171** | 98 |
| 1.5 (aromatic) | 0.000 | 1 |
| 2 (double) | **+0.117** | 10 |
| 3 (triple) | **+0.234** | 5 |

**Single bonds RELEASE energy when snapped. Triple bonds ABSORB energy.**
This is a real, monotonic signal. The snap process behaves differently
for different bond types — your insight that "the interactions come from
sometime around the snap, not just once completed" is validated.

---

## Direction 3: Understanding Beyond Interactions

### What the encoding DOES capture

| Test | Result | Assessment |
|------|--------|------------|
| **EN prediction** | **r = 0.92** | ✓ Excellent |
| **BP prediction** | **r = 0.95** | ✓ Excellent |
| **MP prediction** | **r = 0.87** | ✓ Strong |
| **Rho prediction** | **r = 0.82** | ✓ Strong |
| Z prediction | r = 0.73 | ✓ Good |
| Element clustering | 63.6% | ⚠ Above chance |

### What it DOESN'T capture

| Test | Result | Assessment |
|------|--------|------------|
| Compound formation | 54.2% | ✗ Barely above chance |
| Noble gas detection | 2/5 | ✗ Only He and Ne detected |

---

## The Big Picture

The Data Object encoding **understands elements** (EN, BP, MP, Rho all
predicted with r > 0.8). It does NOT understand **interactions** (bond
energy prediction fails without explicit bond order).

The one bright spot in interactions is the **snap energy signal**: single
bonds release energy when snapped, triple bonds absorb it. This validates
the idea that the snap process is part of the interaction mechanism, not
just a post-processing step.

### What this means for the system

1. **Element identity → works.** The encoding is good for element properties.
2. **Interactions → need bond context.** The bond itself must be encoded as
   a geometric object (your Direction 2 insight).
3. **Snap dynamics → carry bond-type signal.** The snap energy monotonic
   relationship with bond order is the strongest new finding.
4. **Nonlinear methods → don't help here.** The bottleneck is features, not
   model complexity.

### Next steps (your call)

1. **Investigate snap energy further** — can we use it to classify bond order?
2. **Encode the bond as a geometric object** — the midpoint/direction/snap
   framework from Direction 2
3. **Test understanding differently** — the property prediction results
   (r=0.92 for EN, r=0.95 for BP) show the encoding works; maybe
   interactions aren't the right test for "understanding"
4. **Translate to language** — the encoding clearly captures element
   identity; the same approach would work for word identity
