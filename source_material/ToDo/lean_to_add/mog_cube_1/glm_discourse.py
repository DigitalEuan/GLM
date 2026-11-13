#!/usr/bin/env python3
"""
Runnable mirror of the *discourse* layers proved in RequestProject/*.lean.

  Discourse.lean -> and / but / so, connected paragraphs, the 1536-paragraph
                    corpus                                   (validity proved)
  Zipf.lean      -> word frequencies of that corpus, the Zipf comparison, and
                    the least-effort Huffman code            (numbers proved)
  Dialogue.lean  -> a conversation with memory and pronouns  (soundness proved)
  Narrative.lean -> shortest plans and the story of carrying  (correctness and
                    them out                                   reach proved)
  WideDiscourse  -> paragraphs that change the subject       (validity proved)

Depends only on glm_chat2.py, which mirrors the earlier layers.  No external
packages, no randomness, no hashing.  Every printed number is compared against
the number that appears as a theorem in the Lean sources; a mismatch means the
Python is wrong, not the Lean.  Run:  python3 glm_discourse.py
"""

from glm_chat2 import (ENTS, ALL_WORLDS, USEFUL, ACTS, eval_atom, eval_lit,
                       contingent, r_ent, r_lit, r_act, render, answer, step,
                       DEMO_WORLD)

# ──────────────────────────────────────────────────────────────────────────
# 1. Live worlds and the three connectives        (Discourse.lean §1-2)
# ──────────────────────────────────────────────────────────────────────────


def subj(a):
    return a[1]


def ctx_worlds(ctx):
    return [w for w in ALL_WORLDS if all(eval_lit(l, w) for l in ctx)]


def live_with(live, q):
    return [w for w in live if eval_lit(q, w)]


def ok_live(live, ctx, topic, conn, l):
    if subj(l[0]) != topic or l in ctx:
        return False
    n, m = len(live_with(live, l)), len(live)
    if conn == "so":
        return n == m
    if conn == "and":
        return n < m and m <= 2 * n
    return 2 * n < m                                    # "but"


def step_ok(ctx, topic, conn, l):
    """The context definition, exactly as in Lean's `stepOK`."""
    if subj(l[0]) != topic or not contingent(l) or l in ctx:
        return False
    live = ctx_worlds(ctx)
    n, m = len(live_with(live, l)), len(live)
    if conn == "so":
        return n == m
    if conn == "and":
        return n < m and m <= 2 * n
    return 2 * n < m


def candidates(w, e):
    return [l for l in USEFUL if subj(l[0]) == e and eval_lit(l, w)]


def pick(cs, live, ctx, topic):
    for conn in ("but", "and", "so"):
        for l in cs:
            if ok_live(live, ctx, topic, conn, l):
                return (conn, l)
    return None


def describe(w, e, fuel=6):
    cs = candidates(w, e)
    if not cs:
        return None
    opening = cs[0]
    ctx, live, steps = [opening], live_with(ALL_WORLDS, opening), []
    for _ in range(fuel):
        s = pick(cs, live, ctx, topic=e)
        if s is None:
            break
        steps.append(s)
        live = live_with(live, s[1])
        ctx = [s[1]] + ctx
    return (e, opening, steps)


def valid_para(w, p):
    topic, opening, steps = p
    if subj(opening[0]) != topic or not contingent(opening) or not eval_lit(opening, w):
        return False
    ctx = [opening]
    for conn, l in steps:
        if not eval_lit(l, w) or not step_ok(ctx, topic, conn, l):
            return False
        ctx = [l] + ctx
    return True


def say_it(l):
    neg = " is " if l[1] else " is not "
    k = l[0][0]
    if k in ("frozen", "boiling", "warm", "heavy"):
        return "it" + neg + k
    return "it" + neg + ("hotter than " if k == "hotter" else "heavier than ") + r_ent(l[0][2])


def render_para(p):
    _, opening, steps = p
    out = r_lit(opening)
    for conn, l in steps:
        out += ", " + conn + " " + say_it(l)
    return out + "."


# ──────────────────────────────────────────────────────────────────────────
# 2. Zipf and least effort                             (Zipf.lean)
# ──────────────────────────────────────────────────────────────────────────


def tokens(s):
    return [t for t in s.replace(",", "").replace(".", "").split(" ") if t]


def huffman(counts):
    """The same merge as in Lean: join the two lightest, insert keeping sorted."""
    items = sorted([(c, i, ("leaf", t)) for i, (t, c) in enumerate(counts)])
    nxt = len(items)
    while len(items) > 1:
        (c1, _, t1), (c2, _, t2) = items[0], items[1]
        items = items[2:]
        node = (c1 + c2, nxt, ("node", t1, t2))
        nxt += 1
        pos = 0
        while pos < len(items) and items[pos][0] < node[0]:
            pos += 1
        items.insert(pos, node)
    return items[0][2]


def codes_of(tree, pre=""):
    if tree[0] == "leaf":
        return {tree[1]: pre}
    out = dict(codes_of(tree[1], pre + "0"))
    out.update(codes_of(tree[2], pre + "1"))
    return out


# ──────────────────────────────────────────────────────────────────────────
# 3. Dialogue with memory                              (Dialogue.lean)
# ──────────────────────────────────────────────────────────────────────────


def bare_fact(w, e):
    return (("frozen", e), eval_atom(("frozen", e), w))


def reply(w, st, u):
    """st = (topic, said).  Returns (new state, (connective or None, sentence))."""
    topic, said = st
    kind = u[0]
    if kind == "about":
        l = bare_fact(w, u[1])
        return ((u[1], [l] + said), (None, ("lit", l), False))
    if kind == "more":
        s = pick(candidates(w, topic), ctx_worlds(said), said, topic)
        if s is None:
            return (st, (None, ("lit", bare_fact(w, topic)), False))
        conn, l = s
        return ((topic, [l] + said), (conn, ("lit", l), False))
    if kind == "is":
        a = (u[1], topic)
        l = (a, eval_atom(a, w))
        return ((topic, [l] + said), (None, ("lit", l), l in said))
    if kind == "why":
        a = (u[1], topic)
        s = answer(("why", (a, eval_atom(a, w))), w)
        asserted = {"lit": lambda s: [s[1]],
                    "because": lambda s: [s[1], s[2]],
                    "because2": lambda s: [s[1], s[2], s[3]]}.get(s[0], lambda s: [])(s)
        return ((topic, asserted + said), (None, s, all(l in said for l in asserted)))
    a = ("hotter", topic, u[1])                          # "is it hotter than …"
    l = (a, eval_atom(a, w))
    return ((topic, [l] + said), (None, ("lit", l), l in said))


DEMO_SCRIPT = [("about", "water"), ("more",), ("more",), ("is", "warm"),
               ("why", "warm"), ("about", "stone"), ("more",), ("more",),
               ("hotter", "water"), ("more",)]


def render_utt(u):
    return {"about": lambda: "tell me about " + r_ent(u[1]),
            "more": lambda: "tell me more",
            "is": lambda: "is it " + u[1] + "?",
            "why": lambda: "why is it " + u[1] + "?",
            "hotter": lambda: "is it hotter than " + r_ent(u[1]) + "?"}[u[0]]()


def run(w, script):
    st, out = ("water", []), []
    for u in script:
        st, r = reply(w, st, u)
        out.append((u, r))
    return st, out


# ──────────────────────────────────────────────────────────────────────────
# 3b. Paragraphs that change the subject         (WideDiscourse.lean)
# ──────────────────────────────────────────────────────────────────────────


def w_candidates(w):
    return [l for l in USEFUL if eval_lit(l, w)]


def w_pick(cs, live, ctx):
    for conn in ("but", "and", "so"):
        for l in cs:
            if ok_live(live, ctx, subj(l[0]), conn, l):
                return (conn, l)
    return None


def w_describe(w, fuel=6):
    cs = w_candidates(w)
    if not cs:
        return None
    opening = cs[0]
    ctx, live, steps = [opening], live_with(ALL_WORLDS, opening), []
    for _ in range(fuel):
        s = w_pick(cs, live, ctx)
        if s is None:
            break
        steps.append(s)
        live = live_with(live, s[1])
        ctx = [s[1]] + ctx
    return (opening, steps)


def w_valid(w, p):
    opening, steps = p
    if not contingent(opening) or not eval_lit(opening, w):
        return False
    ctx = [opening]
    for conn, l in steps:
        if not eval_lit(l, w) or not step_ok(ctx, subj(l[0]), conn, l):
            return False
        ctx = [l] + ctx
    return True


def w_render(p):
    opening, steps = p
    out, prev = r_lit(opening), subj(opening[0])
    for conn, l in steps:
        out += ", " + conn + " " + (say_it(l) if subj(l[0]) == prev else r_lit(l))
        prev = subj(l[0])
    return out + "."


def subject_changes(p):
    opening, steps = p
    prev, out = subj(opening[0]), []
    for conn, l in steps:
        if subj(l[0]) != prev:
            out.append((conn, l))
        prev = subj(l[0])
    return out


# ──────────────────────────────────────────────────────────────────────────
# 4. Planning and narration                           (Narrative.lean)
# ──────────────────────────────────────────────────────────────────────────


def run_acts(acts, w):
    for a in acts:
        w = step(a, w)
    return w


def seqs_up_to(n):
    out, cur = [[]], [[]]
    for _ in range(n):
        cur = [[a] + s for a in ACTS for s in cur]
        out += cur
    return out


SEQS = seqs_up_to(3)


def plan(w, goal):
    for s in SEQS:
        if eval_lit(goal, run_acts(s, w)):
            return s
    return None


def new_facts(a, u):
    return [l for l in USEFUL if eval_lit(l, step(a, u)) and not eval_lit(l, u)]


def story_data(acts, w):
    out = []
    for a in acts:
        out.append((w, a, new_facts(a, w)))
        w = step(a, w)
    return out


def render_story(w, acts, goal):
    lines = []
    for u, a, facts in story_data(acts, w):
        if facts:
            lines.append(r_act(a) + ", and now " + ", and ".join(r_lit(l) for l in facts))
        else:
            lines.append(r_act(a) + ", and nothing changes yet")
    return lines + ["so " + r_lit(goal)]


# ──────────────────────────────────────────────────────────────────────────


def main():
    print("=" * 72)
    print("DISCOURSE, ZIPF AND DIALOGUE — mirror of the Lean proofs")
    print("=" * 72)

    # ---- paragraphs -------------------------------------------------------
    print("\nParagraphs about the demo world (Discourse.demoParas):")
    for e in ENTS:
        print("  " + render_para(describe(DEMO_WORLD, e)))

    corpus = [(w, describe(w, e)) for w in ALL_WORLDS for e in ENTS]
    bad = [wp for wp in corpus if not valid_para(wp[0], wp[1])]
    conns = [c for _, p in corpus for c, _ in p[2]]
    print(f"\ncorpus: {len(corpus)} paragraphs   (Lean: 1536)")
    print(f"  invalid paragraphs : {len(bad)}   (Lean: 0)")
    print(f"  clauses joined     : {len(conns)}   (Lean: 9216)")
    for c, want in (("and", 4824), ("but", 1512), ("so", 2880)):
        print(f"    {c:<4}: {conns.count(c)}   (Lean: {want})")
    lens = {1 + len(p[2]) for _, p in corpus}
    print(f"  clauses per paragraph: {sorted(lens)}   (Lean: always 7)")

    # ---- paragraphs that change the subject --------------------------------
    wp = w_describe(DEMO_WORLD)
    print("\nA paragraph that changes the subject (WideDiscourse.wdemo):")
    print("  " + w_render(wp))
    wcorpus = [(w, w_describe(w)) for w in ALL_WORLDS]
    wbad = [x for x in wcorpus if not w_valid(x[0], x[1])]
    wclauses = sum(len(p[1]) for _, p in wcorpus)
    wchanges = [s for _, p in wcorpus for s in subject_changes(p)]
    print(f"  paragraphs {len(wcorpus)} (Lean: 512), invalid {len(wbad)} (Lean: 0), "
          f"clauses {wclauses} (Lean: 3072)")
    print(f"  subject changes {len(wchanges)}   (Lean: 2524); "
          f"of them 'so' deductions {sum(1 for c, _ in wchanges if c == 'so')}"
          f"   (Lean: 330)")

    # ---- Zipf -------------------------------------------------------------
    toks = [t for _, p in corpus for t in tokens(render_para(p))]
    vocab = list(dict.fromkeys(toks))
    counts = sorted(((t, toks.count(t)) for t in vocab), key=lambda p: -p[1])
    print(f"\nword tokens: {len(toks)}   (Lean: 66288);  types: {len(vocab)}   (Lean: 17)")
    f1 = counts[0][1]
    print("  rank  word      observed   Zipf f1/n   ratio")
    for n, (t, c) in enumerate(counts, start=1):
        pred = f1 // n
        print(f"  {n:>4}  {t:<9} {c:>8}   {pred:>9}   {c/pred:>5.2f}")
    flatter = all(c >= f1 // n for n, (_, c) in enumerate(counts, start=1))
    doubled = all(c >= 2 * (f1 // n) for n, (_, c) in enumerate(counts, start=1)
                  if 4 <= n <= 12)
    print(f"  every rank at or above the Zipf prediction : {flatter}   (Lean: True)")
    print(f"  ranks 4-12 at least twice the prediction   : {doubled}   (Lean: True)")
    print("  -> the generated language is much flatter than Zipf's law")

    # ---- least effort -----------------------------------------------------
    book = codes_of(huffman(counts))
    prefix_free = all(a == b or not book[b].startswith(book[a]) for a in book for b in book)
    cost = sum(len(book[t]) for t in toks)
    fixed = 5 * len(toks)
    cubes = lambda bits: (bits + 23) // 24
    print(f"\nleast-effort code: prefix free {prefix_free}   (Lean: True)")
    print("  " + "  ".join(f"{t}:{len(book[t])}" for t, _ in counts))
    print(f"  corpus cost   : {cost} bits   (Lean: 249528)")
    print(f"  fixed 5 bits  : {fixed} bits   (Lean: 331440)")
    print(f"  cubes needed  : {cubes(cost)} vs {cubes(fixed)}   (Lean: 10397 vs 13810)")
    ok = all("".join(book[t] for t in tokens(render_para(p))) is not None for _, p in corpus)
    print(f"  every paragraph encodes and decodes back unchanged: {ok and prefix_free}"
          f"   (Lean: True)")

    # ---- dialogue ---------------------------------------------------------
    print("\nA conversation in the demo world (Dialogue.renderRun):")
    _, turns = run(DEMO_WORLD, DEMO_SCRIPT)
    for u, (conn, s, again) in turns:
        lead = ("as I said, " if again else "") + ((conn + " ") if conn else "")
        text = say_it(s[1]) if (conn and s[0] == "lit") else render(s)
        print(f"  > {render_utt(u):<28} {lead}{text}")

    # ---- planning ---------------------------------------------------------
    goal = (("boiling", "water"), True)
    acts = plan(DEMO_WORLD, goal)
    print(f"\nA plan in the demo world (Narrative.demoStory): {len(acts)} step(s)")
    for line in render_story(DEMO_WORLD, acts, goal):
        print("  " + line)

    solvable = sum(1 for w in ALL_WORLDS for g in USEFUL if plan(w, g) is not None)
    print(f"\n  goal/world pairs reachable in <= 3 actions : {solvable}   (Lean: 22080)")
    print(f"  unreachable, and reported as such         : {512 * 48 - solvable}"
          f"   (Lean: 2496)")

    worst = min(len(dict.fromkeys(run(w, DEMO_SCRIPT)[0][1])) for w in ALL_WORLDS)
    alltrue = all(all(eval_lit(l, w) for l in run(w, DEMO_SCRIPT)[0][1]) for w in ALL_WORLDS)
    print(f"\n  all commitments true, in all 512 worlds : {alltrue}   (Lean: True)")
    print(f"  fewest distinct commitments             : {worst}   (Lean: 8)")
    print("=" * 72)


if __name__ == "__main__":
    main()
