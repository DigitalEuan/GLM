This project was edited by [Aristotle](https://aristotle.harmonic.fun).

To cite Aristotle:
- Tag @Aristotle-Harmonic on GitHub PRs/issues
- Add as co-author to commits:
```
Co-authored-by: Aristotle (Harmonic) <aristotle-harmonic@harmonic.fun>
```

# 24D Golay/Leech lattice shortcut — verified method and audit

## Start here

| File | What it is |
|---|---|
| `LATTICE_SHORTCUT_METHOD.md` | **The explainer**: the working method, stage by stage, with its guarantees and limits |
| `lattice_shortcut.py` | **The operational system**: self-contained implementation (`--explain`, `--walk`, `--range`, `--primes`, `--stats`, `--tgic`, `--selftest`) |
| `LATTICE_SHORTCUT_REPORT.md` | Verification report on the original write-up and data (revision 2) |
| `audit_ubp_directory.py` | Audit run against the author's own modules; writes `lattice_shortcut_audit.json`, `lattice_shortcut_audit.log` and the regenerated `lattice_shortcut_directory_corrected.json` |
| `RequestProject/*.lean` | Machine-checked proofs (Lean 4 + Mathlib, no `sorry`) |

## Observer/read quantum study ("I am Y…")

| File | What it is |
|---|---|
| `Y_STUDY_CLEAN_RESTATEMENT.md` | **The clean version of the study itself**: same structure and vocabulary, every sentence labelled definition / stipulation / theorem / open and written so that it is defensible as stated |
| `Y_OBSERVER_STUDY_REPORT.md` | **The audit**: the study stage by stage — each claim made precise, labelled definition / stipulation / theorem / corrected, with the machine-checked name beside it, three corrections and four strengthening results |
| `observer_y.py` | Exact-rational audit (`--selftest`, `--constants`, `--stages`, `--tables`, `--regimes`, `--vector`, `--json`) |
| `RequestProject/ObserverY.lean` | The machine-checked statements: the vacuum, the activation quantum, `TAX = HW·Q`, the loop-as-syndrome, the regime bands, the MOG-aware tax, the calibrated budget |

```bash
python3 observer_y.py --selftest
python3 observer_y.py --stages --tables --regimes
```

## Lightspeed study

| File | What it is |
|---|---|
| `SUBSTRATE_LIGHTSPEED_REPORT.md` | **The explainer**: exact definitions of the substrate speed-of-light calibration, what it does and does not establish, and a corrected version of the note |
| `substrate_lightspeed.py` | Exact-rational audit (`--selftest`, `--report`, `--chain`, `--index`, `--constants`, `--json`) |
| `RequestProject/Lightspeed.lean`, `RequestProject/SubstrateConstants.lean` | The machine-checked statements |
| `lightspeed_audit.json` | Machine-readable dump |

```bash
python3 substrate_lightspeed.py --selftest
python3 substrate_lightspeed.py --report
```

```bash
python3 lattice_shortcut.py --selftest                  # verify every guarantee
python3 lattice_shortcut.py --explain 1000003 1000033   # narrate one transition
python3 audit_ubp_directory.py                          # audit the published directory
lake build                                              # check the proofs
```

## Original material (unmodified apart from a prepended audit note)

`lattice_shortcode_directory.md`, `lattice_shortcut_directory_standalone.json`,
`generate_shortcut_directory_standalone.py`, `ubp_unified_v5.py`,
`value_geometry.py`, `ubp_tgic_engine.py`, `tgic_v3.py`,
`substrate_speed_of_light.md`, `LIGHTSPEED_STUDY_SYNTHESIS.md`,
`I am Y but I don’t know what or where I am, I feel in the dark with what I haven’t.txt`.

---

This project was edited by [Aristotle](https://aristotle.harmonic.fun).

To cite Aristotle:
- Tag @Aristotle-Harmonic on GitHub PRs/issues
- Add as co-author to commits:
```
Co-authored-by: Aristotle (Harmonic) <aristotle-harmonic@harmonic.fun>
```
