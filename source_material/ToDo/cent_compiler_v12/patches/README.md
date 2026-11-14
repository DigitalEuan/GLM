# Applied patches

The three patches supplied on 14 November 2026 are kept here rather than in `cent_compiler/`.

| patch | state |
| --- | --- |
| `d10_unblock.patch` | **applied** 14 November 2026 — the newest and the superset: D8 origination (`cent_compiler/origination.py`), D9 origination at scale (`cent_compiler/origination_scale.py`, `wheels/W42.json`), `tests/test_origination.py`, `examples/origination/`, and the directive, README, scope and test updates that go with them. Gate after applying: 27 of 27 suites, 1061 of 1061 checks |
| `d9_origination.patch` | superseded — every change it carries is in `d10_unblock.patch`, which applies to the same base |
| `d8_origination.patch` | superseded — same |

Each patch is a `git diff` of the whole delivery against the tree as it stood: 314 of 343 entries are only a mode change (644 to 755) on files the patch does not otherwise touch, and the paths are `source_material/cent_compiler_v12/` from before the folder moved under `ToDo/`. To apply one, strip the mode-only sections and re-root the paths:

```bash
cd source_material/ToDo
sed -e 's|a/source_material/cent_compiler_v12/|a/cent_compiler_v12/|' \
    -e 's|b/source_material/cent_compiler_v12/|b/cent_compiler_v12/|' \
    cent_compiler_v12/patches/d10_unblock.patch > /tmp/d10_local.patch
# drop sections with no hunk (mode-only), then apply
patch -p1 --batch --forward --no-backup-if-mismatch < /tmp/d10_clean.patch
```
