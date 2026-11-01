"""``glm_universal.knowledge.ask`` -- the ``corpus`` query kind.

The request grammar of the ``corpus`` kind (``GLM.py -q "corpus define golay
code"``, ``tools corpus-ask what is a syndrome``) and the brute-force recheck
column 3 runs (``runtime/lookup_scripts.py``, template ``corpus``).

:func:`ask` reads one request into one of the readings of
:mod:`~glm_universal.knowledge.answer` -- or the word address of
:mod:`~glm_universal.knowledge.word_address` -- and returns::

    {"ok": bool, "reading": str, "answer": str (one line),
     "refusal": str (when not ok), "expected": {str: str}, "witness": ...}

``expected`` holds the figures the answer rests on (the witness addresses,
the counts, the context words, the coordinates and the Leech point).
:func:`recheck` recomputes exactly those keys in a fresh interpreter **by
brute force over the corpus sentences** -- every mention found by scanning
every sentence, every count recounted from the documents under the model's
own rule (a document's repeated sentence counted once), no postings and no
cached index -- and column 3 compares the two key by key.

The grammar (a leading ``corpus`` is optional; case and a final ``?`` are
ignored):

=========================================================  ============
request                                                    reading
=========================================================  ============
``define X`` · ``definition of X`` · ``what is X``         ``define``
``context of X [at sentence|paragraph|document scale]``    ``context``
``words like X`` · ``similar to X``                        ``similar``
``related to X`` · ``words related to X``                  ``related``
``continue X``                                             ``continue``
``spread of X``                                            ``spread``
``predict X`` · ``next after X``                           ``predict``
``address of X``                                           ``address``
=========================================================  ============

A request the grammar does not read, a term no sentence mentions, a term the
corpus mentions but never defines, a tie, a phrase given to ``address of``
and a word with too little company are refused with the reason.

*Created 31 October 2026 (repository check).*

*Reconstructed 31 October 2026 (repository check): the original was lost in
the October 2026 reorganisation (the 29 October placeholder refused every
request); rebuilt from studies/CORPUS_KNOWLEDGE_STUDY.md (§§1, 5, 6),
studies/CORPUS_DEFINITIONS_STUDY.md (§§1, 7.2-7.3: ``corpus define`` uses
the context ranking and its column 3 recomputes the context words and the
ranking by brute force; ``corpus address of X`` with column 3 recounting the
coordinates from the sentences), MASTER_PLAN.md Phases 154-155, the five
evaluation cases (``corpus-define``, ``corpus-continue``,
``corpus-unmentioned``, ``corpus-address``, ``corpus-address-phrase``), the
original answers stored in reasoning/_data/evidence_model_study.json (the
answer shapes are theirs), the runtime's ``_solve_corpus`` and
``_body_corpus``, and the ``corpus-ask`` handler of tools.py.*
"""

from __future__ import annotations

import re
from collections import Counter
from fractions import Fraction
from typing import Any, Dict, List, Optional, Sequence, Tuple

from . import answer as ans
from . import model as mdl
from . import reader as rd

__all__ = ["CorpusRefusal", "ask", "recheck", "answer_request", "parse",
           "READINGS"]

#: The readings the grammar names.
READINGS: Tuple[str, ...] = ("define", "context", "similar", "related",
                             "continue", "spread", "predict", "address")


class CorpusRefusal(Exception):
    """Raised by :func:`answer_request` when the request cannot be answered.

    The CLI handler in :mod:`glm_universal.tools` catches this and prints
    ``refused: <message>``, exiting 1.
    """


# ---------------------------------------------------------------------------
#  The grammar
# ---------------------------------------------------------------------------

_RULES: Tuple[Tuple[str, "re.Pattern[str]"], ...] = tuple(
    (reading, re.compile(pattern)) for reading, pattern in (
        ("address", r"^(?:the\s+)?(?:lattice\s+)?address\s+(?:of\s+)?(?P<x>.+)$"),
        ("context", r"^context\s+(?:of\s+)?(?P<x>.+?)"
                    r"(?:\s+at\s+(?:the\s+)?(?P<scale>sentence|paragraph|document)\s+scale)?$"),
        ("similar", r"^(?:words\s+(?:used\s+)?like|used\s+like|similar\s+to|like)\s+(?P<x>.+)$"),
        ("related", r"^(?:words\s+related\s+to|related\s+to|related|company\s+of)\s+(?P<x>.+)$"),
        ("continue", r"^(?:continue|continuation\s+of)\s+(?P<x>.+)$"),
        ("spread", r"^(?:spread|reach)\s+(?:of\s+)?(?P<x>.+)$"),
        ("predict", r"^(?:predict|next\s+(?:word\s+)?after)\s+(?P<x>.+)$"),
        ("define", r"^(?:define:?|definition\s+of)\s+(?P<x>.+)$"),
        ("define", r"^(?:what\s+is|what\s+are|what's)\s+(?:(?:the|a|an)\s+)?(?P<x>.+)$"),
    ))

_GRAMMAR_HELP = ("define X, context of X [at sentence|paragraph|document "
                 "scale], words like X, related to X, continue X, spread of X, "
                 "predict X, or address of X")


def parse(request: str) -> Optional[Dict[str, str]]:
    """``{"reading", "subject", "scale"}`` for a request, or ``None``."""
    text = " ".join(str(request).split()).strip().lower()
    if text.startswith("corpus ") or text == "corpus":
        text = text[len("corpus"):].strip()
    text = text.rstrip("?").strip()
    if not text:
        return None
    for reading, rule in _RULES:
        m = rule.match(text)
        if m is not None:
            subject = m.group("x").strip().strip("'\"`").strip()
            if not subject:
                return None
            scale = (m.groupdict().get("scale") or "sentence")
            return {"reading": reading, "subject": subject, "scale": scale}
    return None


# ---------------------------------------------------------------------------
#  ask: the reading, its answer and its expected figures
# ---------------------------------------------------------------------------

def _refused(reading: str, reason: str) -> Dict[str, Any]:
    return {"ok": False, "reading": reading, "answer": "", "refusal": reason,
            "expected": {}, "witness": ()}


def _join(items: Sequence[Any], sep: str = ",") -> str:
    return sep.join(str(x) for x in items)


def ask(request: str, knowledge: Optional[mdl.Knowledge] = None) -> Dict[str, Any]:
    """Read one ``corpus`` request and answer it from the counted corpus."""
    parsed = parse(request)
    if parsed is None:
        return _refused("unrecognised", f"the corpus request is not one the "
                                        f"grammar reads; ask {_GRAMMAR_HELP}")
    reading, subject, scale = parsed["reading"], parsed["subject"], parsed["scale"]
    knowledge = mdl.load() if knowledge is None else knowledge
    handler = {
        "define": _ask_define, "context": _ask_context, "similar": _ask_company,
        "related": _ask_company, "continue": _ask_continue, "spread": _ask_spread,
        "predict": _ask_predict, "address": _ask_address,
    }[reading]
    out = handler(reading, subject, scale, knowledge)
    if out.get("ok") and not out.get("expected"):  # pragma: no cover - a contract
        raise AssertionError(f"corpus {reading}: an answer without expected figures")
    return out


def _ask_define(reading, subject, scale, knowledge) -> Dict[str, Any]:
    got = ans.define(subject, knowledge, ranking="context")
    if not got.get("ok"):
        return _refused(reading, got["refusal"])
    rows = got["answers"]
    head = rows[0]
    text = f"The corpus says: {head['text']} [{head['address']}]"
    if len(rows) > 1:
        text += " Also: " + " ".join(
            f"({r['source']}, {r['pattern']}) {ans._cut(r['text'])} [{r['address']}]"
            for r in rows[1:3])
    expected = {
        "reading": "define", "term": " ".join(ans.tokens_of(subject)),
        "mentions": str(got["mentions"]), "documents": str(got["documents"]),
        "context": _join(got["context"]), "head": head["address"],
        "pattern": head["pattern"], "strength": str(head["strength"]),
        "support": str(head["support"]),
        "ranking": _join(got["candidates"], " | "),
    }
    return {"ok": True, "reading": reading, "answer": ans.one_line(text),
            "expected": expected, "witness": tuple(got["candidates"]),
            "quality": {"grade": got["strength"], "pattern": head["pattern"],
                        "strength": head["strength"], "source": head["source"],
                        "support": head["support"]}}


def _ask_context(reading, subject, scale, knowledge) -> Dict[str, Any]:
    got = ans.context(subject, knowledge, scale)
    if not got.get("ok"):
        return _refused(reading, got["refusal"])
    if not got["words"]:
        return _refused(reading, f"no word stands around {subject!r} more often "
                                 f"than its own frequency predicts")
    shown = ", ".join(f"{r['word']} ({r['with_term']})" for r in got["rows"])
    text = (f"The words over-represented around {subject!r} at {scale} scale "
            f"({got['mentions']} of {got['units']} {scale}s mention it): {shown}. "
            f"First mention: {got['witness']}")
    expected = {"reading": "context", "term": " ".join(ans.tokens_of(subject)),
                "scale": scale, "mentions": str(got["mentions"]),
                "words": _join(got["words"])}
    return {"ok": True, "reading": reading, "answer": text, "expected": expected,
            "witness": (got["witness"],)}


def _ask_company(reading, subject, scale, knowledge) -> Dict[str, Any]:
    fn = ans.similar if reading == "similar" else ans.related
    got = fn(subject, knowledge)
    if not got.get("ok"):
        return _refused(reading, got["refusal"])
    what = ("used like" if reading == "similar" else "found with the same company as")
    rule = ("the squared cosine of their positional company" if reading == "similar"
            else "the squared cosine of their associated contexts")
    text = (f"The words {what} {got['word']!r} ({rule}, {got['features']} features): "
            + ", ".join(got["neighbours"]) + ".")
    expected = {"reading": reading, "word": got["word"],
                "neighbours": _join(got["neighbours"])}
    return {"ok": True, "reading": reading, "answer": text, "expected": expected,
            "witness": (f"features={got['features']}",)}


def _ask_continue(reading, subject, scale, knowledge) -> Dict[str, Any]:
    got = ans.continue_text(subject, knowledge)
    if not got.get("ok"):
        return _refused(reading, got["refusal"])
    expected = {"reading": "continue", "prefix": got["prefix"],
                "continuation": got["text"], "stop": got["stop"],
                "counts": _join(f"{s['count']}/{s['total']}" for s in got["steps"]),
                "witnesses": _join(got["witness"], " | ")}
    return {"ok": True, "reading": reading, "answer": got["answer"],
            "expected": expected, "witness": tuple(got["witness"])}


def _ask_spread(reading, subject, scale, knowledge) -> Dict[str, Any]:
    got = ans.spread(subject, knowledge)
    if not got.get("ok"):
        return _refused(reading, got["refusal"])
    sources = ", ".join(f"{k} {v}" for k, v in got["by_source"].items())
    text = (f"{got['term']!r} stands {got['occurrences']} times in "
            f"{got['sentences']} sentences, {got['paragraphs']} paragraphs and "
            f"{got['documents']} documents, across {len(got['folders'])} top-level "
            f"folders ({', '.join(got['folders'])}); by source: {sources}. "
            f"First: {got['witness']}")
    expected = {"reading": "spread", "term": got["term"],
                "occurrences": str(got["occurrences"]),
                "sentences": str(got["sentences"]),
                "paragraphs": str(got["paragraphs"]),
                "documents": str(got["documents"]),
                "folders": _join(got["folders"])}
    return {"ok": True, "reading": reading, "answer": text, "expected": expected,
            "witness": (got["witness"],)}


def _ask_predict(reading, subject, scale, knowledge) -> Dict[str, Any]:
    got = ans.predict(subject, knowledge)
    if not got.get("ok"):
        return _refused(reading, got["refusal"])
    text = (f"After {got['context']!r} the corpus's unique most frequent next "
            f"word is {got['word']!r} ({got['count']} of {got['total']}).")
    expected = {"reading": "predict", "context": got["context"],
                "word": got["word"], "count": str(got["count"]),
                "total": str(got["total"])}
    return {"ok": True, "reading": reading, "answer": text, "expected": expected,
            "witness": (f"context={got['context']}",)}


def _ask_address(reading, subject, scale, knowledge) -> Dict[str, Any]:
    from . import word_address as wa
    toks = ans.tokens_of(subject)
    if len(toks) != 1:
        return _refused(reading, f"a lattice address is for one word, and "
                                 f"{subject!r} is {len(toks)} tokens")
    got = wa.locate(toks[0], knowledge, scheme="positional")
    if not got.get("ok"):
        return _refused(reading, got["refusal"])
    company = ", ".join(f"'{name}' {value}" for name, value in got["coordinates"].items()
                        if value)
    near = ", ".join(f"{w} ({d})" for w, d in got["neighbours"])
    point = tuple(got["address"])
    text = (f"{got['word']!r} sits at the Leech point {point} (read back exactly: "
            f"{got['readback']}), from its positional company {company}. Its nearest "
            f"words on the lattice (squared distance): {near}.")
    vector = tuple(got["coordinates"].values())
    book = wa.address_book(knowledge, "positional")
    expected = {"reading": "address", "word": got["word"],
                "anchors": _join(book["anchors"]),
                "coordinates": _join(vector), "address": _join(point),
                "readback": str(got["readback"])}
    return {"ok": True, "reading": reading, "answer": text, "expected": expected,
            "witness": (f"coordinates={_join(vector)}",)}


def answer_request(text: str) -> Dict[str, Any]:
    """Parse ``text`` and answer it; raises :class:`CorpusRefusal` on refusal.

    Returns the dict of :func:`ask` (with at least ``"answer"``).
    """
    got = ask(text)
    if not got.get("ok"):
        raise CorpusRefusal(got.get("refusal") or "refused")
    return got


# ---------------------------------------------------------------------------
#  recheck: the same figures, by brute force over the sentences
# ---------------------------------------------------------------------------

def _counted(knowledge: mdl.Knowledge) -> List[Tuple[str, ...]]:
    """Every sentence the model counts: per document, its distinct token
    sequences in first-occurrence order (``Model.add_document``'s rule)."""
    out: List[Tuple[str, ...]] = []
    for document in knowledge.documents:
        seen = set()
        for s in document.sentences:
            if s.tokens in seen:
                continue
            seen.add(s.tokens)
            out.append(s.tokens)
    return out


def _all_sentences(knowledge: mdl.Knowledge) -> List[rd.Sentence]:
    """Every sentence as read, in corpus order, straight from the documents."""
    return [s for document in knowledge.documents for s in document.sentences]


def _scan_mentions(sentences: Sequence[rd.Sentence], run: Sequence[str]) -> List[int]:
    first = run[0]
    return [i for i, s in enumerate(sentences)
            if first in s.tokens and ans.find_run(s.tokens, run) >= 0]


def _brute_context(sentences: Sequence[rd.Sentence], run: Sequence[str],
                   mentions: Sequence[int], scale: str) -> List[str]:
    own = set(run)

    def unit(s: rd.Sentence):
        if scale == "sentence":
            return s.address
        if scale == "paragraph":
            return (s.document, s.paragraph)
        return s.document

    mention_units = {unit(sentences[i]) for i in mentions}
    words_of: Dict[Any, set] = {}
    holders: Dict[str, set] = {}
    all_units = set()
    for s in sentences:
        u = unit(s)
        all_units.add(u)
        content = {t for t in s.tokens if mdl.is_content(t) and t not in own}
        if u in mention_units:
            words_of.setdefault(u, set()).update(content)
        for t in content:
            holders.setdefault(t, set()).add(u)
    co: Counter = Counter()
    for words in words_of.values():
        co.update(words)
    m, total = len(words_of), len(all_units)
    rows = [(w, c) for w, c in co.items()
            if c >= ans.MIN_SUPPORT and c * total > m * len(holders[w])]
    rows.sort(key=lambda r: (-r[1], r[0]))
    return [w for w, _ in rows[:ans.CONTEXT_WORDS]]


def _recheck_define(subject: str, knowledge: mdl.Knowledge) -> Dict[str, str]:
    run = ans.tokens_of(subject)
    sentences = _all_sentences(knowledge)
    mentions = _scan_mentions(sentences, run)
    documents = len({sentences[i].document for i in mentions})
    best: Dict[Tuple[str, ...], Tuple[Tuple[int, int, int], int, str]] = {}
    for i in mentions:
        hit = ans.match_pattern(sentences[i], run)
        if hit is None:
            continue
        order = (ans.source_of(sentences[i])[0], hit[1], i)
        key = sentences[i].tokens
        if key not in best or order < best[key][0]:
            best[key] = (order, i, hit[0])
    words = _brute_context(sentences, run, mentions, "sentence")
    wanted = {ans.fold(w) for w in words} - {ans.fold(t) for t in run}
    drop = {ans.fold(t) for t in run}
    rows = []
    for order, i, pattern in best.values():
        have = {ans.fold(t) for t in sentences[i].tokens if mdl.is_content(t)} - drop
        rows.append((-len(have & wanted), order, i, pattern))
    rows.sort()
    if not rows:
        return {"reading": "define", "term": " ".join(run), "ok": "False",
                "mentions": str(len(mentions)), "documents": str(documents)}
    head = rows[0]
    return {"reading": "define", "term": " ".join(run),
            "mentions": str(len(mentions)), "documents": str(documents),
            "context": _join(words), "head": sentences[head[2]].address,
            "pattern": head[3], "strength": str(head[1][1]),
            "support": str(-head[0]),
            "ranking": _join([sentences[r[2]].address for r in rows[:3]], " | ")}


def _recheck_context(subject: str, scale: str, knowledge: mdl.Knowledge) -> Dict[str, str]:
    run = ans.tokens_of(subject)
    sentences = _all_sentences(knowledge)
    mentions = _scan_mentions(sentences, run)
    if scale == "sentence":
        m = len(mentions)
    elif scale == "paragraph":
        m = len({(sentences[i].document, sentences[i].paragraph) for i in mentions})
    else:
        m = len({sentences[i].document for i in mentions})
    return {"reading": "context", "term": " ".join(run), "scale": scale,
            "mentions": str(m),
            "words": _join(_brute_context(sentences, run, mentions, scale))}


def _followers(counted: Sequence[Tuple[str, ...]], key: Sequence[str]) -> Counter:
    """What follows ``key`` (one or two tokens) in the padded counted sentences."""
    row: Counter = Counter()
    last = key[-1]
    k = len(key)
    for toks in counted:
        if last not in toks:
            continue
        padded = (mdl.BOS, mdl.BOS) + toks + (mdl.EOS,)
        for i in range(2, len(padded)):
            if tuple(padded[i - k:i]) == tuple(key):
                row[padded[i]] += 1
    return row


def _brute_row(counted, history) -> Tuple[Tuple[str, ...], Counter]:
    if len(history) >= 2:
        key = (history[-2], history[-1])
        row = _followers(counted, key)
        if row:
            return key, row
    key = (history[-1],)
    return key, _followers(counted, key)


def _brute_witness(sentences: Sequence[rd.Sentence], key: Sequence[str],
                   token: str) -> str:
    wanted = tuple(key) + (token,)
    for s in sentences:
        if token not in s.tokens:
            continue
        padded = (mdl.BOS, mdl.BOS) + s.tokens + (mdl.EOS,)
        if ans.find_run(padded, wanted) >= 0:
            return s.address
    return ""


def _recheck_continue(subject: str, knowledge: mdl.Knowledge) -> Dict[str, str]:
    counted = _counted(knowledge)
    sentences = _all_sentences(knowledge)
    toks = list(ans.tokens_of(subject))
    history = list(toks)
    produced: List[str] = []
    counts: List[str] = []
    witnesses: List[str] = []
    states = {tuple(history[-2:])}
    stop = "limit"
    while len(produced) < ans.MAX_CONTINUATION:
        key, row = _brute_row(counted, history)
        if not row:
            stop = "unseen"
            break
        top = max(row.values())
        winners = sorted(c for c, n in row.items() if n == top)
        if len(winners) > 1:
            stop = "tie"
            break
        token = winners[0]
        if token == mdl.EOS:
            stop = "end"
            break
        if (history[-1], token) in states:
            stop = "cycle"
            break
        states.add((history[-1], token))
        counts.append(f"{top}/{sum(row.values())}")
        witnesses.append(_brute_witness(sentences, key, token))
        produced.append(token)
        history.append(token)
    return {"reading": "continue", "prefix": " ".join(toks),
            "continuation": " ".join(produced), "stop": stop,
            "counts": _join(counts), "witnesses": _join(witnesses, " | ")}


def _recheck_predict(subject: str, knowledge: mdl.Knowledge) -> Dict[str, str]:
    counted = _counted(knowledge)
    key, row = _brute_row(counted, list(ans.tokens_of(subject)))
    top = max(row.values()) if row else 0
    winners = sorted(c for c, n in row.items() if n == top)
    return {"reading": "predict", "context": " ".join(key),
            "word": winners[0] if len(winners) == 1 else "",
            "count": str(top), "total": str(sum(row.values()))}


def _recheck_company(reading: str, subject: str, knowledge: mdl.Knowledge
                     ) -> Dict[str, str]:
    """The ranking recomputed against every word's set, with no index."""
    w = ans.tokens_of(subject)[0]
    sets = knowledge.positions if reading == "similar" else knowledge.contexts
    mine = sets.get(w, frozenset())
    counts = knowledge.model.unigram
    scored = []
    for other, feats in sets.items():
        if other == w:
            continue
        shared = len(mine & feats)
        if shared:
            scored.append((Fraction(shared * shared, len(mine) * len(feats)), other))
    scored.sort(key=lambda r: (-r[0], -counts[r[1]], r[1]))
    return {"reading": reading, "word": w,
            "neighbours": _join([o for _, o in scored[:ans.NEIGHBOURS]])}


def _recheck_spread(subject: str, knowledge: mdl.Knowledge) -> Dict[str, str]:
    run = ans.tokens_of(subject)
    sentences = _all_sentences(knowledge)
    mentions = _scan_mentions(sentences, run)
    occurrences = sum(len(ans.runs(sentences[i].tokens, run)) for i in mentions)
    documents = {sentences[i].document for i in mentions}
    return {"reading": "spread", "term": " ".join(run),
            "occurrences": str(occurrences), "sentences": str(len(mentions)),
            "paragraphs": str(len({(sentences[i].document, sentences[i].paragraph)
                                   for i in mentions})),
            "documents": str(len(documents)),
            "folders": _join(sorted({rd.top_folder(d) for d in documents}))}


def _recheck_address(subject: str, knowledge: mdl.Knowledge) -> Dict[str, str]:
    """The positional coordinates recounted from the sentences, then the point
    and its read-back (the decoder is the declarations' own)."""
    from ..reasoning import lean_address as la
    from . import word_address as wa
    word = ans.tokens_of(subject)[0]
    counted = _counted(knowledge)
    unigram: Counter = Counter()
    total = 0
    for toks in counted:
        unigram.update(toks)
        total += len(toks)
    anchors = sorted(unigram, key=lambda t: (-unigram[t], t))[:wa.POSITIONAL_ANCHORS]
    before: Counter = Counter()   # anchor a directly before the word
    after: Counter = Counter()    # anchor a directly after the word
    for toks in counted:
        if word not in toks:
            continue
        for i, t in enumerate(toks):
            if t != word:
                continue
            if i > 0:
                before[toks[i - 1]] += 1
            if i + 1 < len(toks):
                after[toks[i + 1]] += 1

    def coord(n: int, a: str) -> int:
        if n < mdl.MIN_PAIR:
            return 0
        lift = Fraction(n * total, unigram[a] * unigram[word])
        return max(1, min(wa.CAP, wa.CENTRE + wa.floor_log2(lift)))

    vector = tuple(coord(before[a], a) for a in anchors) + \
        tuple(coord(after[a], a) for a in anchors)
    point = la.quantise(vector)
    readback = tuple(la.describe_address(point)["recovered"]) == vector
    return {"reading": "address", "word": word, "anchors": _join(anchors),
            "coordinates": _join(vector), "address": _join(point),
            "readback": str(readback)}


def recheck(request: str) -> Dict[str, str]:
    """The figures of :func:`ask`'s ``expected``, recomputed by brute force.

    Loads the documents (``model.load``), then reads only their sentences:
    no postings, no address book and no cached ranking.  Returns the same
    keys as ``expected`` for an answered request (column 3 compares only
    those).  An unparsed request, a phrase asked for an address and a term
    no sentence defines give ``{"reading": ..., "ok": "False", ...}``; for
    the other readings a refused request gives whatever the brute force
    finds (an empty continuation, a tied row, no neighbours).
    """
    parsed = parse(request)
    if parsed is None:
        return {"reading": "unrecognised", "ok": "False"}
    reading, subject, scale = parsed["reading"], parsed["subject"], parsed["scale"]
    if not ans.tokens_of(subject):
        return {"reading": reading, "ok": "False"}
    knowledge = mdl.load()
    if reading == "define":
        return _recheck_define(subject, knowledge)
    if reading == "context":
        return _recheck_context(subject, scale, knowledge)
    if reading in ("similar", "related"):
        return _recheck_company(reading, subject, knowledge)
    if reading == "continue":
        return _recheck_continue(subject, knowledge)
    if reading == "spread":
        return _recheck_spread(subject, knowledge)
    if reading == "predict":
        return _recheck_predict(subject, knowledge)
    if len(ans.tokens_of(subject)) != 1:
        return {"reading": "address", "ok": "False"}
    return _recheck_address(subject, knowledge)
