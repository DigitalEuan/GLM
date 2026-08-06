# 'light/' README — Speed of Light Calibration and EM scale calibration

**Version:** 1.3.0  (6 August 2026) 
**Author:** Euan R. A. Craig (DigitalEuan), Auckland, New Zealand   
**Parent:** `../README.md`  

## UPDATE THIS README - if changes are made in this folder or systems in sub-folders need rewiring within the repository and effect this README file's structure

- UBP-to-real-world scale alignment through the speed of light. 

---

## Role in the System

```
light/ (this folder)
  ├──┬ 'aristotle_01' - provides Lattice shortcut method
  │  ├ 'lattice_shortcut.py' - the operational system: self-contained implementation
  │  └ `LATTICE_SHORTCUT_METHOD.md` the working method, stage by stage
  │
  ├──┬ 'EM_calibration_1' - The UBP-to-realworld scale is: S(λ, HW) = λ / [HW × (Y + 1/8)]d
  │  ├ 'reports/ubp_scale_final_v9_report.md' - explainer
  │  ├ 'scripts/ubp_scale_final_v9` the working method, stage by stage
  │  └ `ubp_layered_arch_v11_report.md' Bit-Ops - native UBP bit-level operations and metrics
  │
  ├── 'reports' = development reports
  │
  ├── 'scripts' = development python scripts
  │
  ├── 'source_documents' = original research
  │
  └── 'worklogs' = original research workload


20 phases of rigorous, independent audit of the UBP framework's claims about
the speed of light and physical constants. The study evolved from falsification
testing to calibration analysis, ultimately establishing a partially calibrated
UBP-to-Reality scale:

- Charge: 1 vertex step = e/12 C (exact)
- Velocity: v/c = 0.339 (exact, from γ = MONAD/13)
- Mass: m_e = Y² × WOBBLE × 24⁴ × 29⁴ × h × Δν_Cs / c² (0.007% - 0.009% error results vary currently)
The mass residual is the most important open problem.

---

## Contents

### /reports — All original audit reports (20 phases)
- `UBP_c_Falsification_Study.pdf` — Phase 1-3 (original PDF report with charts)
- `Phase4_Structural_Claims_Audit.md` through `Phase20_Calibration_Audit.md`

### /scripts — All original Python analysis scripts
- `phase1_falsification.py` through `phase20_calibration.py`
- `ubp_constants.py` — UBP substrate constants
- `aggregate_results.py` — Chart generation
- `generate_pdf_report.py` — PDF report generator

### /source_documents — Original documents provided by the user
- All .txt files (driving instructions, review documents, etc.)
- `ubp_script_20260730192545.py` — Original UBP c-formula script
- `ubp_study_2026-07-30.json` — Full UBP study export (91 files)

### /worklogs — Multi-agent original work log
- `worklog.md` — Complete record of all 20 phases