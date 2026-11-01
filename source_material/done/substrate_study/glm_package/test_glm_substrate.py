"""Self-test of ``glm_substrate.py`` against the facts proved in ``RequestProject/GLM/``.

Run with ``python3 test_glm_substrate.py`` (or ``pytest``). Standard library only; a few
seconds. This is testing, not proof: it checks that the Python reference implementation
agrees with the Lean definitions and theorems named in each test.
"""

import itertools
import math
import random

import glm_substrate as g

WT4 = [v for v in g._low_weight_masks() if g.weight(v) == 4]
LE3 = [v for v in g._low_weight_masks() if g.weight(v) <= 3]
SAMPLE_CODEWORDS = [0, g.CODE[1], g.CODE[777], g.CODE[2048], g.CODE[4095]]


def test_code_parameters():
    # card_golayCode, golay_weight_enumerator, golay_min_weight
    assert len(set(g.CODE)) == 4096
    counts = {}
    for c in g.CODE:
        counts[g.weight(c)] = counts.get(g.weight(c), 0) + 1
    assert counts == {0: 1, 8: 759, 12: 2576, 16: 759, 24: 1}
    # mem_golayCode_iff: the code is the kernel of the syndrome
    assert all(g.syndrome(c) == 0 for c in g.CODE)
    assert len({g.syndrome(v) for v in g._low_weight_masks()}) == 4096


def test_leader_census():
    # golayLeader_wt_count: 1, 24, 276, 2024, 1771; covering radius 4
    counts = [0] * 5
    for v in g.LEADER:
        counts[g.weight(v)] += 1
    assert counts == [1, 24, 276, 2024, 1771]


def test_sextets():
    # card_golaySextet, golaySextet_disjoint, golaySextet_cover
    triggered = [s for s in range(4096) if g.is_triggered_syndrome(s)]
    assert len(triggered) == 1771
    for s in triggered:
        tet = g.sextet(s)
        assert len(tet) == 6 and all(g.weight(t) == 4 for t in tet)
        acc = 0
        for t in tet:
            assert acc & t == 0
            acc |= t
        assert acc == (1 << 24) - 1


def test_low_weight_corrected_and_trigger_off():
    # golay_corrects_weight_le3, golayTrigger_off_le3
    for c in SAMPLE_CODEWORDS:
        for e in LE3:
            dec, trig = g.hard_decode(c ^ e)
            assert dec == c and not trig
            assert g.resolve_with_label(c ^ e, g.mirror_label(e)) == (c,)


def test_weight4_trigger_and_mirror():
    # golayTrigger_on_4, golay_no_silent_weight4, golay_triggered_candidates(_dist),
    # golay_side_info_six_suffice, golay_triggered_list_mirror
    for c in SAMPLE_CODEWORDS:
        for e in WT4:
            y = c ^ e
            dec, trig = g.hard_decode(y)
            assert trig
            cand = g.candidates(y)
            assert len(cand) == 6 and c in cand
            assert all(g.weight(a ^ b) == 8 for a, b in itertools.combinations(cand, 2))
            assert g.resolve_with_label(y, g.mirror_label(e)) == (c,)
            for k in range(1, 7):
                lst = g.resolve_with_label(y, g.list_label(e, k), k)
                assert c in lst and len(lst) <= math.ceil(6 / k)


def test_trigger_depends_only_on_error():
    # golayTrigger_error_only: the label is computed from the error alone
    e = WT4[1234]
    lists = [g.resolve_with_label(c ^ e, g.mirror_label(e)) for c in g.CODE[:64]]
    assert lists == [(c,) for c in g.CODE[:64]]


def test_batching():
    # golay_batch_labels_suffice / _lower: 6^m joint labels
    assert [g.batch_bits(m) for m in (1, 2, 3, 4, 5)] == [3, 6, 8, 11, 13]
    rng = random.Random(1)
    for m in range(1, 8):
        labs = [rng.randrange(6) for _ in range(m)]
        v = g.batch_labels(labs)
        assert 0 <= v < 6 ** m and g.unbatch_labels(v, m) == labs


def test_tag():
    # golayTag_octad (every octad has a nonzero tag) => golay_tag_upper
    assert all(g.tag(c) != 0 for c in g.CODE if g.weight(c) == 8)
    for c in SAMPLE_CODEWORDS[:3]:
        for e in LE3 + WT4[::7]:
            assert g.resolve_with_tag(c ^ e, g.tag(c)) == c


def test_soft_certificate():
    # soft_beats_hard_example: 7 hard flips, certified with no label
    r = [-0.01] * 7 + [1.0] * 17
    assert g.weight(g.hard_decision(r)) == 7
    assert g.certified(r, 0)
    best = min(g.CODE, key=lambda w: g.sq_dist(r, w))
    assert best == 0
    # soft_certificate_sharp: the midpoint of two codewords at distance 8 is at exactly 8
    octad = next(c for c in g.CODE if g.weight(c) == 8)
    mid = [(a + b) / 2 for a, b in zip(g.bpsk(0), g.bpsk(octad))]
    assert abs(g.sq_dist(mid, 0) - 8.0) < 1e-12 and not g.certified(mid, 0)


def test_least_reliable_tetrad_is_nearest_candidate():
    # sqDist_flip_tetrad
    rng = random.Random(7)
    done = 0
    while done < 300:
        c = rng.choice(g.CODE)
        r = [x + rng.gauss(0, 0.8) for x in g.bpsk(c)]
        y = g.hard_decision(r)
        if not g.hard_decode(y)[1]:
            continue
        cand = g.candidates(y)
        assert g.least_reliable_tetrad(r) == min(cand, key=lambda w: g.sq_dist(r, w))
        done += 1


def test_receiver_smoke():
    rng = random.Random(3)
    sigma = 0.6
    statuses = {}
    for _ in range(300):
        c = rng.choice(g.CODE)
        r = [x + rng.gauss(0, sigma) for x in g.bpsk(c)]
        dec, status = g.receive_soft(r, sigma=sigma)
        statuses[status] = statuses.get(status, 0) + 1
        if status == "certified":
            assert dec == min(g.CODE, key=lambda w: g.sq_dist(r, w))
    assert set(statuses) <= {"clean", "certified", "gated", "ask"}


def test_matches_lean_tables():
    # Checksums of the Lean definitions `leaderTable` and the encoder masks (`golayRowMask`),
    # obtained by evaluating them in Lean (`#eval`). Equal checksums mean this module decodes
    # with the same coset leaders, in the same syndrome indexing, as `golayDecode`.
    mod = 1000000007
    assert sum((i + 1) * v for i, v in enumerate(g.LEADER)) % mod == 539488205
    assert sum((i + 1) * c for i, c in enumerate(g.CODE)) % mod == 35560637


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print("ok ", t.__name__)
    print(f"all {len(tests)} tests passed")
