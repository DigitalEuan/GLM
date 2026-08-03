# Data sources

## PubChem periodic table snapshot

- File: `raw/pubchem_periodic_table.csv`
- Provider: PubChem, National Center for Biotechnology Information (NCBI)
- Page: <https://pubchem.ncbi.nlm.nih.gov/periodic-table/>
- API endpoint: <https://pubchem.ncbi.nlm.nih.gov/rest/pug/periodictable/CSV>
- Accessed: 2026-08-02
- SHA-256: `efcadb3dd180bd06fc0fa069a81082e86553ba2b8b5d679b7827bb8c03afd3ce`
- Rows: 118, one for each atomic number 1–118

The snapshot is retained unchanged. `processed/elements.csv` is generated from it by `golay_mog_experiments.py`, adding deterministic period and group fields. Empty source fields remain empty.

## NIST CCCBDB experimental atomization-energy snapshot

- Files: `raw/nist_cccbdb/species_selection.html` and `raw/nist_cccbdb/atomization_energy_selected.html`
- Provider: NIST Computational Chemistry Comparison and Benchmark Database (CCCBDB), SRD 101
- Entry page: <https://cccbdb.nist.gov/ea1x.asp>
- Accessed: 2026-08-03
- Species-selection SHA-256: `b35cd4f17acd1838cdc37ec58c35afe23fd796c097cd4c23d6bdeb58d7459ace`
- Atomization-result SHA-256: `6b71837bea3d18a1d45c309cde46a85a837342054c414a757061546a6e18b9e1`

The retained result page reports experimental 0 K and 298 K atomization energies in kJ mol⁻¹ and a source uncertainty column. `processed/diatomic_dissociation_0k.csv` selects neutral diatomic rows with a displayed 0 K value. For these species, 0 K atomization to ground-state atoms is used as the gas-phase dissociation endpoint D0. Missing uncertainty remains explicit. The snapshot contains 52 retained species over 19 elements and is a selected pilot corpus, not a complete mirror of CCCBDB.
