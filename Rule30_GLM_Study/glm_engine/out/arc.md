# ARC-style puzzles — GLM Hypothesis Engine v18

The solver answers only when every consistent program of least depth agrees. Synthetic families are generated from steps that the library contains, so they measure need routing, not discovery; the real ARC tasks are the honest test.

## Synthetic held-out families

60 test grids

| condition | outcome |
|---|---|
| base steps only (symmetries + colour map) | {'right': 6, 'refused': 54} |
| on demand: the wheel serves each puzzle's stated needs | {'right': 55, 'refused': 5} |
| all provisions | {'right': 56, 'refused': 4} |
| random provisions, same number as on demand #1 | {'right': 15, 'refused': 45} |
| random provisions, same number as on demand #2 | {'right': 18, 'refused': 42} |
| random provisions, same number as on demand #3 | {'right': 13, 'refused': 47} |
| random provisions, same number as on demand #4 | {'right': 18, 'refused': 42} |
| random provisions, same number as on demand #5 | {'right': 16, 'refused': 44} |

Needs stated by the base solver (from demonstrations only): {'primitive:select': 22, 'primitive:arrange': 12, 'primitive:fill': 12, 'primitive:move': 6, 'primitive:recolour': 6, 'primitive:count': 5}

Solved on demand: flip+recolour (flip_h+colour_map), flip+recolour (flip_h+colour_map), flip+recolour (flip_h+colour_map), flip+recolour (flip_h+colour_map), flip+recolour (flip_h+colour_map), flip+recolour (flip_h+colour_map), gravity (gravity_down), gravity (gravity_down), gravity (gravity_down), gravity (gravity_down), gravity (gravity_down), gravity (gravity_down), mirror-tile (tiling), mirror-tile (tiling), mirror-tile (tiling), mirror-tile (tiling), scale (scale), scale (scale), scale (scale), scale (scale), scale (scale), scale (scale), periodic (periodic_fill), periodic (periodic_fill), periodic (periodic_fill), periodic (periodic_fill), periodic (periodic_fill), periodic (periodic_fill), select-odd (select_block), select-odd (select_block), select-odd (select_block), select-odd (select_block), select-odd (select_block), select-odd (select_block), boolean (boolean_halves), boolean (boolean_halves), boolean (boolean_halves), boolean (boolean_halves), boolean (boolean_halves), boolean (boolean_halves), recolour-size (recolour_by_feature), recolour-size (recolour_by_feature), recolour-size (recolour_by_feature), recolour-size (recolour_by_feature), count (count_to_row), count (count_to_row), count (count_to_row), count (count_to_row), count (count_to_row), crop (crop_nonbg), crop (crop_largest+crop_nonbg), crop (crop_largest+crop_nonbg), crop (crop_largest+crop_nonbg), crop (crop_largest+crop_nonbg), crop (crop_largest+crop_nonbg)

Wrong answers: none

## Real ARC tasks

53 test grids

| condition | outcome |
|---|---|
| base steps only (symmetries + colour map) | {'refused': 53} |
| on demand: the wheel serves each puzzle's stated needs | {'refused': 44, 'right': 9} |
| all provisions | {'refused': 44, 'right': 9} |
| random provisions, same number as on demand #1 | {'refused': 52, 'right': 1} |
| random provisions, same number as on demand #2 | {'refused': 50, 'right': 3} |
| random provisions, same number as on demand #3 | {'refused': 52, 'right': 1} |

Needs stated by the base solver (from demonstrations only): {'primitive:fill': 19, 'primitive:recolour': 13, 'primitive:select': 11, 'primitive:unknown': 10, 'primitive:arrange': 5, 'primitive:move': 4, 'primitive:count': 1}

Solved on demand: 1e0a9b12#0 (gravity_down), 45737921#0 (swap_in_objects), 484b58aa#0 (periodic_fill), 662c240a#0 (select_block), 7953d61e#0 (tiling), ae58858e#0 (recolour_by_feature), b91ae062#0 (scale), bc4146bd#0 (tiling), d631b094#0 (count_to_row)

Wrong answers: none

