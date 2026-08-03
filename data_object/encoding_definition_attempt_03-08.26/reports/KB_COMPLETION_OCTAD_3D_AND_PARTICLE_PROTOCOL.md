# KB completion, Golay-octad regions, 3D view, and particle protocol

## Scope

This round answers the five requested points without rewriting the source `ubp_system_kb.json` or claiming unavailable measurement metadata. It adds a usable typed companion table, exact MOG regions, one fully declared visualization, and a freeze-ready particle protocol. The existing standardized wide table remains unchanged.

## 1. Positional decoding and Golay Octad zones

The monitoring rule is retained exactly:

> A tensor category is positionally decoded only when every observed element tensor length equals the category's declared parameter count.

This is a schema rule, not a statistical guess. A short or long vector cannot safely inherit labels because all labels after an insertion/deletion may shift. The Octad structure does not repair those labels.

It can, however, define exact regions in data that genuinely have 24 MOG coordinates. Under the project's fixed 4×6 convention, each adjacent pair of columns is a weight-eight Golay codeword:

| Region | MOG columns | Cyclic coordinates |
|---|---|---|
| Octad zone 1 | 0–1 | 0, 4, 1, 17, 3, 21, 2, 23 |
| Octad zone 2 | 2–3 | 6, 19, 15, 5, 20, 8, 14, 12 |
| Octad zone 3 | 4–5 | 16, 11, 9, 13, 10, 22, 7, 18 |

The three verified octads are disjoint and partition all 24 coordinates. They are now published in `results/ubp_mog_octad_zones.json`. They may be used as coarse monitoring regions—such as per-zone occupancy, TAX, or error counts—provided the source datum has an explicit 24-coordinate mapping. They must not be imposed on 45-entry or 742-entry KB categories merely to make them fit.

## 2. Making the five KB channels operational

`data/processed/ubp_kb_elements_typed_long.csv` is the new typed companion to `ubp_kb_elements_standardized.csv`. It contains 590 records: five channels for each of 118 elements. Every record has:

- `value_exact`: the unchanged rational string from the KB extraction;
- `unit`;
- `condition`;
- `uncertainty`;
- `source`;
- `status`.

The table is complete as a **schema** because no metadata slot is blank. It does not fabricate metrological completeness:

- atomic number is an exact dimensionless count and is independently checked against the element identifier;
- atomic mass is labelled `u`, and melting/boiling points `K`, as inferred conventions rather than declarations made by the KB;
- density's unit is deliberately unresolved. The values span gas-like and condensed-phase conventions, so assigning one global density unit would be unsafe;
- temperature, pressure, phase/allotrope conditions, uncertainties, methods, and upstream per-value citations remain `not_reported` where unavailable;
- status distinguishes exact ontology-derived identity from inferred-unit/unresolved-source records.

This is the safe table to use now for element studies. Models may filter by status. They should not treat `not_reported` as zero, and they should not mix density with other physical channels until its per-value unit and conditions are resolved. The KB's global numeric null token remains a source limitation; the companion uses text statuses and would use an empty/null value for genuine missingness.

A truly metrologically complete revision still requires authoritative per-value sources. The retained PubChem snapshot can be a comparison source, but it is not silently substituted: many values differ from the KB, and the compact table itself does not provide per-value uncertainty and conditions.

## 3. Recommended schema revision

The recommendation remains useful even though the companion table is immediately usable. A future native KB record should use named objects rather than positional arrays:

```json
{
  "atomic_mass": {
    "value_exact": "126/125",
    "unit": "u",
    "condition": null,
    "uncertainty": null,
    "source": {"dataset": "...", "record": "..."},
    "status": "measured"
  }
}
```

Allowed statuses should include at least `measured`, `calculated`, `imputed`, `ontology_derived`, and `missing`. Missing values should be JSON `null`; numerical zero must remain available as a real value. `condition` should be structured (temperature, pressure, phase, isotope, allotrope, method) rather than an unparsed note when those data become available.

## 4. A declared 24D→3D visualization

`results/leech_24d_to_3d_projection.json` publishes a concrete matrix for the 24 fixed Leech-address vectors. Its entries are

`P[r,c] = S[r,c] / sqrt(24)`,

where the complete 3×24 sign matrix `S` is included in the file. The three sign rows are mutually orthogonal, so `P Pᵀ = I₃` and the rank is three. There is no inverse on 24-space. Reconstruction is only the orthogonal projection `x_hat = Pᵀ P x`, and the kernel has dimension 21.

The distortion audit on the 24 established address vectors finds:

- 276 pairwise distances audited;
- mean relative distance error: about **0.6531**;
- maximum relative distance error: **1.0**;
- distance-vector cosine similarity: about **0.9438**;
- directed nearest-neighbor recall: about **0.0888**;
- 15 projected-point collisions.

This is a useful negative result: the view is compact and exactly specified, but it loses too much local geometry for it to serve as a general computational replacement for 24D. It is suitable as a visual baseline. Exact distance, neighborhood, TAX, and symmetry calculations should remain in 24D.

Physical dimensions such as mass, temperature, vibration rate, and colour are typed observations—not automatically axes of this matrix. A task-specific visualizer may encode them as marker size, colour, animation frequency, or separate panels, but it must state scales, units, clipping, and missing-data handling. Those display channels do not increase the rank or recover discarded Leech coordinates.

## 5. Particle-level gate and the lightspeed synthesis

`results/prospective_particle_protocol.json` freezes a candidate grammar, coefficient bounds, dimensional rule, split rule, metrics, and three matched baselines. Its status is deliberately `protocol_only_not_a_prospective_result`.

The existing particle targets have already been inspected and used during formula development. They cannot become a locked test set retroactively. The protocol therefore requires measurements published after the freeze, or another target manifest sealed before any fitting. It restricts the first gate to dimensionless ratios; a dimensionful formula must explicitly name its independently supplied unit-bearing anchor.

The lightspeed synthesis is incorporated conservatively:

- SI-defined values such as `c`, `h`, `e`, `k_B`, and cesium frequency may be anchors but are not independent predicted measurements in the current SI;
- the electron-mass residual is an in-sample residual, not evidence of a QED correction until a correction rule predicts unseen data;
- the reported muon-ratio null-model result is prior evidence that can motivate a replication, not a new prospective result;
- training geometric mean, dimensional-analysis-only prediction, and a parameter-count-matched random-symbol grammar are mandatory baselines.

The protocol's coefficient rule and tie-breaking are explicit enough to implement without consulting test targets. Before execution it still needs a timestamped training table, a locked target manifest, and a version/hash. Only one final evaluation should be made after unblinding.

## Recommended use from here

1. Use the typed long table for all new element analyses; retain exact strings until a declared conversion step.
2. Exclude or stratify channels whose status is unresolved; density is the immediate priority for source repair.
3. Use the three Octad zones only for explicit 24-coordinate records and retain the strict category-length guardrail.
4. Use the published 3D map only for viewing; calculate scientific geometry in 24D and report projection controls.
5. Version and hash the particle protocol before collecting its locked targets.
6. Expand the interaction endpoint before another element-model search; the existing 52 diatomics are too sparse for broad geometric selection.

## Reproduction

```bash
python3 ubp_kb_geometry_protocol.py
python3 -m unittest discover -s tests -v
lake build RequestProject.GolayMOG
```
