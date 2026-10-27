"""Write r11_reasoning_suite.json: claims about Rule 30 for `tool claim`, with the expected
verdict and a keyword the missing hypothesis must contain (REJECT items).

`split`: "frame" items use the declared frame wording; "heldout" items rephrase a claim in a
way the frames were not written against; "refuse" items are outside every frame (the expected
behaviour is a refusal, not a guess).  Written by hand, Round 11.
"""
import json

ITEMS = [
    # id, split, claim, verdict, keyword (missing hypothesis / witness must mention it), reference
    ("D1", "frame", "The center column observer can distinguish wheel 30 from wheel 86.",
     "REJECT", "mirror", "centre_column_class"),
    ("D2", "frame", "column 1 distinguishes wheel 30 from wheel 86", "ACCEPT", "differ",
     "column_one_separates_mirror"),
    ("D3", "frame", "column 0 distinguishes wheel 30 from wheel 62", "ACCEPT", "differ",
     "(computed witness)"),
    ("D4", "frame", "the wobble at column 0 equals the wobble at column 0", "ACCEPT", "",
     "chiralGap_centre"),
    ("D5", "frame", "the wobble at column 2 equals the wobble at column -2", "REJECT", "mirror",
     "chiralGap_first"),
    ("D6", "frame", "right diagonal 5 is balanced", "REJECT", "anti-periodic",
     "rdiag_five_not_half"),
    ("D7", "frame", "right diagonal 7 is balanced", "ACCEPT", "", "rdiag_seven_bounded"),
    ("D8", "frame", "right diagonal 8 is balanced", "ACCEPT", "", "(computed)"),
    ("D9", "frame", "rows 0..3 determine wheel 30", "REJECT", "neighbourhood",
     "rows_three_do_not_identify"),
    ("D10", "frame", "rows 0..4 determine wheel 30", "ACCEPT", "", "rows_identify_thirty"),
    ("D11", "frame", "For almost every initial row the centre column has frequency 1/2, hence "
     "the seed's centre column has frequency 1/2", "REJECT", "measure 0",
     "bernoulliRow_seed_null"),
    ("D12", "frame", "for almost every row the centre column is not eventually periodic",
     "ACCEPT", "", "ae_column_not_eventuallyPeriodic"),
    ("D13", "frame", "the wobble arrow tells left from right", "REJECT", "mirror",
     "observerArrow_mirror"),
    ("D14", "frame", "the wobble arrow is reversed by swapping the colours", "ACCEPT", "",
     "observerArrow_complement"),
    ("D15", "frame", "the right-edge zero boundary forces frequency 1/2", "REJECT", "left half",
     "exists_row_with_biased_column"),
    ("D16", "frame", "every right diagonal is balanced", "REJECT", "periodicity",
     "rdiag_five_not_half"),
    ("D17", "frame", "infinitely many right diagonals are balanced", "ACCEPT", "",
     "infinitely_many_balanced_rdiag"),
    ("D18", "frame", "the centre column is eventually constant", "REJECT", "adjacent",
     "centerCol_not_eventually_constant"),
    ("D19", "frame", "two different columns are both eventually periodic", "REJECT",
     "two distinct columns", "seed_at_most_one_periodic_column"),
    ("D20", "frame", "whiteDiagonalCount n is odd for all n >= 2", "ACCEPT", "",
     "whiteDiagonalCount_odd"),
    ("D21", "frame", "the ANF degree is 2n-1, so the centre bit is hard to compute", "REJECT",
     "all rows", "map_properties_cannot_decide_periodicity"),
    ("D22", "frame", "Problem 1 is proved", "OPEN", "seed-specific", "OPEN"),
    ("D23", "frame", "the centre column has frequency 1/2", "OPEN", "seed-specific", "OPEN"),
    # held out: rephrasings
    ("H1", "heldout", "the observer at the centre can tell apart wheel 30 and wheel 86", "REJECT",
     "mirror", "centre_column_class"),
    ("H2", "heldout", "the centre column of rule 30 and rule 86 differ somewhere", "REJECT",
     "mirror", "centre_column_class"),
    ("H3", "heldout", "the wobble arrow records chirality", "REJECT", "mirror",
     "observerArrow_mirror"),
    ("H4", "heldout", "pinning the right half white gives balance", "REJECT", "left half",
     "exists_row_with_biased_column"),
    ("H5", "heldout", "diagonal number 5 behind the right edge has frequency one half", "REJECT",
     "anti-periodic", "rdiag_five_not_half"),
    # outside every frame: a refusal is expected
    ("R1", "refuse", "the centre column is normal in base 2", "REFUSE", "", ""),
    ("R2", "refuse", "rule 110 is Turing complete", "REFUSE", "", ""),
]

suite = {"format": "tool claim <claim> -> VERDICT / MISSING HYPOTHESIS / WITNESS-REFERENCE / "
                   "NEXT TEST",
         "scoring": "1 point if the verdict matches (REFUSE = the tool refused); for REJECT "
                    "items the missing hypothesis or witness must also contain the keyword",
         "items": [dict(id=i, split=sp, claim=c, verdict=v, keyword=k, reference=r)
                   for i, sp, c, v, k, r in ITEMS]}
json.dump(suite, open("r11_reasoning_suite.json", "w"), indent=1)
print(len(ITEMS), "items")
