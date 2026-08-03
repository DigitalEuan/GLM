"""Quick diagnostic: check min_operator_residual values per pair."""
import sys, json, statistics
sys.path.insert(0, '/home/z/my-project/scripts')
import ubp_kb_loader as kb
import stacked_mog_grids as smg
from e1_e2_e3_kb_sweep import KNOWN_PAIRS

scene = smg.StackedMOGScene(cell_w=4.0, cell_h=4.0, z_offset=6.0)
print('=== sq4_z6_MULT_only: min_operator_residual per pair ===')
print(f'{"Pair":<10} {"BE":>5} {"dH":>6} {"min_resid":>12} {"n_ops":>6} {"AND":>4} {"HWa":>4} {"HWb":>4}')

residuals = []
dh_vals = []
for sym_a, sym_b, be, dh, _ in KNOWN_PAIRS:
    ea = kb.get_element(sym_a)
    eb = kb.get_element(sym_b)
    if ea is None or eb is None: continue
    m = scene.compute_pair_metrics(ea.vector24, eb.vector24)
    and_count = sum(1 for i in range(24) if ea.vector24[i]==1 and eb.vector24[i]==1)
    dh_str = f'{dh:>6.0f}' if dh else '     0'
    hwa = sum(ea.vector24)
    hwb = sum(eb.vector24)
    print(f'{sym_a+"+"+sym_b:<10} {be:>5} {dh_str} {m["min_operator_residual"]:>12.8f} '
          f'{m["n_operator_pairs"]:>6} {and_count:>4} {hwa:>4} {hwb:>4}')
    if dh is not None and dh != 0:
        residuals.append(m["min_operator_residual"])
        dh_vals.append(dh)

print(f'\nCorrelation min_operator_residual vs dH: r = {statistics.correlation(residuals, dh_vals):+.4f}')
print(f'\nResidual value distribution:')
from collections import Counter
rc = Counter(round(r, 6) for r in residuals)
for val, cnt in sorted(rc.items()):
    print(f'  {val:.6f}: {cnt} pairs')
