# 'aristotle_01/' LIGHT README — Speed of Light Calibration Study

**Version:** 1.0.0  (5 August 2026) 
**Author:** Euan R. A. Craig (DigitalEuan), Auckland, New Zealand   
**Parent:** `light/README.md`  

## UPDATE THIS README - if changes are made in this folder or systems in sub-folders need rewiring within the repository and effect this README file's structure

- UBP-to-real-world scale alignment through the speed of light. 

---

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
`substrate_speed_of_light.md`, `LIGHTSPEED_STUDY_SYNTHESIS.md`.

---

This project was edited by [Aristotle](https://aristotle.harmonic.fun).

To cite Aristotle:
- Tag @Aristotle-Harmonic on GitHub PRs/issues
- Add as co-author to commits:
```
Co-authored-by: Aristotle (Harmonic) <aristotle-harmonic@harmonic.fun>
```
