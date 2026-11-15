# Attachment import record

Imported from `message-5aa7bad8-e578-45df-b4bf-c32a731798db.zip` on 2026-11-08.

The attachment contained 36 Python files, 25 Markdown files, one CSV,
three DOCX files, three PDFs, and six PNG figures. It contained **no JSON
files**. Existing files were preserved; only artifacts absent from the live
repository were added.

## Destinations

- Six Run 35/36 scripts were added under `scripts/`: `deliver36.py`,
  `docs36.py`, `fetch_candidates.py`, `import_candidates.py`,
  `portable_paths36.py`, and `probe_wedges36.py`.
- Four missing run notes were added under `notes/`: `run26_NOTES.md`,
  `run32_NOTES.md`, `run35_NOTES.md`, and `run36_NOTES.md`.
- Five missing legacy research documents were added at repository root:
  `00-OVERVIEW.md`, `01-LAYERS.md`, `02-EXACT-VERIFICATION.md`,
  `04-RUN-LOG.md`, and `MANIFEST.md`.
- Reports and figures were added under `workspace/docs/attachments/`.
- The attachment CSV was added as
  `workspace/submission/submission.run36.csv`; the existing canonical
  `workspace/submission/submission.csv` was not overwritten.

## Deliberately preserved

- The attachment's `root_audit.py` differs from the existing
  `scripts/root_audit.py`, so it was not overwritten.
- Existing same-named scripts and notes were not duplicated or replaced.
- No JSON files were available in the attachment to import.
