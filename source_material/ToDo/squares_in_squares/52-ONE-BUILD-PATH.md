# Run 89 — one build path, and a count that cannot go stale

Two small debts from run 88, both about the same thing: a number or a code path that
says something it no longer does.

## 1. The Pocket is the strip at m = 1

Run 88 put `p_strip(k, m)` on `strip_field(k, m)` and left `p_pocket(k)` on run 84's
sentence builder, noting the agreement as a control rather than sharing the path. The
pocket *is* `S(k, 1)` — it declares N = 4k² + 1 and the side `2k + ½√2` — so the two
builders were two spellings of one object.

```python
def p_pocket(k):
    if k < 1:
        raise Refusal("degenerate_cell", f"k = {k}")
    return _assemble_field(f"Pocket({k})", strip_field(k, 1), family="Pocket",
                           params={"k": k})
```

One assembly, two claims: the family stays `Pocket` (that is the object being claimed)
while the cells, words, side and void all come from the strip field. `Q_mixed_strip` is
still used where it belongs — control 12's cage recovery and control 19's cross-check
against the run-84 sentence — so the old builder is still the *witness*, not the source.

Control 19 now carries the equality directly, for k = 1, 2, 3: same state, same words,
same L, same N = 4k² + 1, with the families distinct. The wheel's Pocket rows are
unchanged (`k = 1`: 5 squares, `L = 2 + ½√2`; `k = 2`: 17, `4 + ½√2`; `k = 3`: 37,
`6 + ½√2`), all four witnesses, all certified — 31/31 spatial stands.

## 2. The control count is derived

`selftest` carried `checks = 0`, incremented nowhere, and printed a hardcoded
`selftest: OK (17 controls)` — which run 88 had already broken (it printed 0, then a
literal 19). The counter is gone; each control now announces itself through one helper:

```python
    announced = []
    def say(msg):
        announced.append(msg)
        print(msg)
    ...
    print(f"selftest: OK ({len(announced)} controls)")
```

so the count *is* the number of controls that ran. A control cannot be added without
being counted, and a control cannot be removed while its number stays behind.

The `--selftest` branch of `main` used to `return selftest()`, i.e. the exit status was
the control count; now it runs the controls and returns 0, so a passing selftest exits 0
and a failing one raises, as with every other selftest in the project.

## 3. Verification

| check | result |
|---|---|
| `glm_wheels --selftest` | **19 controls** (counted, not typed), exit 0 |
| `glm_wheels` spin | spatial **31/31**, sequences 6/7, lattice 24/28 |
| `glm_wheels --audit` | **177 functions, 0 offenders** |
| `grammar_induction --selftest` | 3/3 |
| `qsqrt2 --selftest` | 11/11 |
| `field_triage --selftest` | 4/4 |
| `record_guard.py` | OK |

## 4. What did not change

No row of the table, `submission.csv`, the root whiteboard, any cell's N/L/void/gain, or
any witness verdict. This run rewired two code paths and a counter; it discovered
nothing, and it does not claim to. Doc 51's note that "Pocket is still `S(k,1)` from run
84's builder" was true of run 88 and is superseded here.

Entries `52-ONE-BUILD-PATH.md`; records `31`–`52`.
