"""``glm_universal.knowledge.answer`` -- the corpus readings.

What the counted corpus (:mod:`~glm_universal.knowledge.model`) can say, each
reading an exact count of the corpus with a witness sentence for its answer
(``studies/CORPUS_KNOWLEDGE_STUDY.md`` §1, ``studies/CORPUS_DEFINITIONS_STUDY.md``
§2.3):

``define``
    what the corpus says X is: the sentences that state X by a declared
    definitional pattern (:data:`PATTERNS`), each with its address, the rank
    of its source (:func:`source_of`) and its context support, ranked by the
    term's sentence-scale context words first (Phase 155's context ranking,
    which ``corpus define`` uses) and then by define's own order (source
    rank, pattern strength, corpus order);
``context``
    the words over-represented around X at sentence, paragraph or document
    scale;
``similar``
    the words used like X: the squared cosine of the positional feature sets
    (``model.positional_sets``);
``related``
    the words found with the same company as X: the squared cosine of the
    associated-context sets (``model.context_sets``);
``continue_text``
    the corpus's own most frequent continuation of a phrase, each token with
    its count and a witness sentence, stopping -- and naming why -- at a tie,
    at the end of a sentence, at an unseen context, at a repeated state or at
    :data:`MAX_CONTINUATION` tokens;
``spread``
    how far X reaches through the hierarchy (tokens, sentences, paragraphs,
    documents, folders);
``predict``
    the guarded next word: the unique strict maximum of the deciding row, and
    no word at a tie (``GLM.CorpusKnowledge.predict_eq_none_of_tie``).

Every reading returns a dict with ``ok`` and, when it declines, a
``refusal`` giving the reason (a term the corpus never mentions, a term it
mentions but never defines, a tie, a word with too little company).  Every
count is an ``int`` and every ratio a :class:`~fractions.Fraction`; nothing
samples.

The declared rules the documents leave open, fixed here:

* **Patterns** (strength 0 strongest).  The term must *open* the sentence --
  be its first tokens, or follow one determiner (*the*, *a*, *an*), or a list
  number -- and then:

  ====================  ========  ==============================================
  pattern               strength  shape
  ====================  ========  ==============================================
  ``gloss::``           0         ``X: gloss`` (also ``X — gloss``, and
                                  ``–`` or ``-`` before a space)
  ``copula:<verb>``     1         ``X is …`` (``is are means denotes``,
                                  ``refers to``, ``stands for``)
  ``copula:<verb>``     2         the same after a determiner: ``The X is …``
  ``gloss:,``           3         ``X, the …`` / ``X, a …`` / ``X, an …``
  ====================  ========  ==============================================

  The label rule (§3a): a gloss separator followed by a path, a file name or
  nothing is a label, not a definition; a comma is a gloss only before *the*,
  *a* or *an*; and a table row of more than two cells is never a gloss.
* **Sources** (rank 0 first): ``tier-0`` (a sentence of a tier-0 block),
  ``state document`` (written Markdown and text), ``Lean doc comment``,
  ``docstring`` (and comments), ``archive or supplied`` (anything under
  ``archive/`` or ``source_material/``), ``data file`` (JSON and CSV).  A
  sentence copied into several documents is kept at its best-ranked copy.
* **Context words**: the content words (``model.is_content``) other than the
  term's own that stand in at least :data:`MIN_SUPPORT` of the units
  mentioning the term and more often than independence predicts
  (``co·S > m·n(w)``), ranked by that count, then spelling; the first
  :data:`CONTEXT_WORDS`.  A candidate's **support** is how many of them it
  holds, both sides folded as in Phase 155 §2.1 (a final ``s`` dropped from a
  word of more than three letters).

*Created 31 October 2026 (repository check).*

*Reconstructed 31 October 2026 (repository check): the original was lost in
the October 2026 reorganisation (the 29 October placeholder refused every
reading); rebuilt from studies/CORPUS_KNOWLEDGE_STUDY.md (§§1, 3, 3a, 5, 7),
studies/CORPUS_DEFINITIONS_STUDY.md (§§2.1, 2.3, 7.2),
studies/CONFIDENCE_CURVE_STUDY.md §3 (the pattern strength, source and
context support every answer carries), MASTER_PLAN.md Phases 154-155, the
original answers stored in reasoning/_data/evidence_model_study.json (the
answer and witness shapes) and knowledge/model.py.  The pattern table, the
source names and the context rule above are declared here; where the
documents name them (``copula:is``, ``gloss::``, ``tier-0``, ``Lean doc
comment``, ``docstring``, ``archive or supplied``, ``data file``) the names
are the original's.*
"""

from __future__ import annotations

import re
from fractions import Fraction
from typing import Any, Dict, FrozenSet, Iterable, List, Mapping, Optional, Sequence, Tuple

from . import model as mdl
from . import reader as rd

__all__ = [
    "define", "context", "similar", "related", "continue_text", "spread",
    "predict", "tokens_of", "find_run", "mention_ids", "source_of",
    "match_pattern", "fold", "content_set", "support", "sqcos",
    "PATTERNS", "SOURCES", "CONTEXT_WORDS", "NEIGHBOURS", "MAX_CONTINUATION",
    "MIN_SUPPORT", "SCALES", "STRONG_STRENGTH", "STRONG_SUPPORT",
]

#: The context words a term is ranked by (Phase 155 §2.3: "the term's 12
#: sentence-scale context words").
CONTEXT_WORDS = 12

#: A context word must stand in at least this many of the term's units
#: (the model's ``MIN_PAIR``).
MIN_SUPPORT = mdl.MIN_PAIR

#: The neighbours ``similar`` and ``related`` return.
NEIGHBOURS = 10

#: The longest continuation ``continue_text`` gives.
MAX_CONTINUATION = 24

#: The scales of ``context``.
SCALES: Tuple[str, ...] = ("sentence", "paragraph", "document")

#: The answer text of ``define`` is cut to this many characters.
ANSWER_CHARS = 240

#: The quality grade of a definition (CONFIDENCE_CURVE_STUDY.md §3): strong
#: when the pattern strength is at most 2 and the context support at least 2.
STRONG_STRENGTH = 2
STRONG_SUPPORT = 2

DETERMINERS: FrozenSet[str] = frozenset({"the", "a", "an"})

#: The copulas of the ``copula:<verb>`` pattern, as token runs.
COPULAS: Tuple[Tuple[str, ...], ...] = (
    ("is",), ("are",), ("means",), ("denotes",), ("refers", "to"),
    ("stands", "for"),
)

#: The declared patterns and their strengths (0 strongest).
PATTERNS: Tuple[Tuple[str, int, str], ...] = (
    ("gloss::", 0, "X: gloss (or X — gloss), the term opening the sentence"),
    ("copula:<verb>", 1, "X is …, the term opening the sentence"),
    ("copula:<verb>", 2, "The X is …, one determiner before the term"),
    ("gloss:,", 3, "X, the/a/an …"),
)

#: The sources, in rank order.
SOURCES: Tuple[str, ...] = (
    "tier-0", "state document", "Lean doc comment", "docstring",
    "archive or supplied", "data file",
)

_ARCHIVE_TOPS: FrozenSet[str] = frozenset({"archive", "source_material"})
_PROSE = (".md", ".markdown", ".txt")
_FILE_NAME = re.compile(r"^[\w.-]*\w\.[A-Za-z][A-Za-z0-9]{0,5}$")
_EMPHASIS = "*_`\"')]"


# ---------------------------------------------------------------------------
#  Small exact helpers
# ---------------------------------------------------------------------------

def _knowledge(knowledge: Optional[mdl.Knowledge]) -> mdl.Knowledge:
    return mdl.load() if knowledge is None else knowledge


def tokens_of(text: str) -> Tuple[str, ...]:
    """The tokens of ``text`` by the reader's own rule."""
    return rd._tokenise(text)


def find_run(tokens: Sequence[str], run: Sequence[str], start: int = 0) -> int:
    """The index of the first contiguous occurrence of ``run`` at or after
    ``start``, or ``-1``."""
    n = len(run)
    if n == 0:
        return -1
    first = run[0]
    last = len(tokens) - n
    i = start
    while i <= last:
        if tokens[i] == first and tuple(tokens[i:i + n]) == tuple(run):
            return i
        i += 1
    return -1


def runs(tokens: Sequence[str], run: Sequence[str]) -> List[int]:
    """Every index at which ``run`` occurs contiguously in ``tokens``."""
    out: List[int] = []
    i = find_run(tokens, run)
    while i >= 0:
        out.append(i)
        i = find_run(tokens, run, i + 1)
    return out


def fold(word: str) -> str:
    """Phase 155 §2.1: a final ``s`` dropped from a word of more than three letters."""
    return word[:-1] if len(word) > 3 and word.endswith("s") else word


def content_set(tokens: Iterable[str], exclude: Iterable[str] = ()) -> FrozenSet[str]:
    """The folded content words of ``tokens``, without the folded ``exclude``."""
    drop = {fold(t) for t in exclude}
    return frozenset(f for f in (fold(t) for t in tokens if mdl.is_content(t))
                     if f not in drop)


def support(tokens: Sequence[str], context_words: Iterable[str],
            term_tokens: Sequence[str]) -> int:
    """How many of the context words the sentence holds (both sides folded)."""
    words = content_set(tokens, term_tokens)
    wanted = content_set(context_words, term_tokens)
    return len(words & wanted)


def sqcos(a: FrozenSet[str], b: FrozenSet[str]) -> Fraction:
    """The squared cosine of two finite sets, ``|a∩b|² / (|a|·|b|)``, exactly
    (``GLM.CorpusKnowledge.sqcos``: in ``[0, 1]``, ``1`` exactly at equality)."""
    if not a or not b:
        return Fraction(0)
    k = len(a & b)
    return Fraction(k * k, len(a) * len(b))


def one_line(text: str) -> str:
    return " ".join(str(text).split())


def _cut(text: str, limit: int = ANSWER_CHARS) -> str:
    text = one_line(text)
    return text if len(text) <= limit else text[:limit]


# ---------------------------------------------------------------------------
#  Where a sentence stands, and whether it defines
# ---------------------------------------------------------------------------

def source_of(sentence: rd.Sentence) -> Tuple[int, str]:
    """The rank and name of a sentence's source (rank 0 first)."""
    path = sentence.document or sentence.address.split("#", 1)[0]
    top = rd.top_folder(path)
    lower = path.lower()
    if top in _ARCHIVE_TOPS or ".zip/" in lower:
        rank = 4
    elif sentence.tier0:
        rank = 0
    elif lower.endswith(_PROSE):
        rank = 1
    elif lower.endswith(".lean"):
        rank = 2
    elif lower.endswith(".py"):
        rank = 3
    else:
        rank = 5
    return rank, SOURCES[rank]


def _opening(tokens: Sequence[str], i: int) -> Optional[int]:
    """``0`` when the run at ``i`` opens the sentence, ``1`` when one
    determiner stands before it, ``None`` otherwise (a leading list number is
    passed over)."""
    lead = 1 if tokens and tokens[0].isdigit() and i >= 1 else 0
    if i == lead or i == 0:
        return 0
    if i == lead + 1 and tokens[lead] in DETERMINERS:
        return 1
    return None


def _term_regex(term_tokens: Sequence[str]) -> "re.Pattern[str]":
    body = r"\W+".join(re.escape(t) for t in term_tokens)
    return re.compile(r"(?<!\w)" + body + r"(?!\w|'\w)", re.IGNORECASE)


def _is_label(gloss: str) -> bool:
    """The label rule: nothing, a path or a file name after the separator."""
    if not tokens_of(gloss):
        return True
    first = gloss.split()[0].strip(_EMPHASIS + "([<")
    if "/" in first or first.startswith(("[", "<")):
        return True
    return bool(_FILE_NAME.match(first.rstrip(".,;:")))


def _table_row(text: str) -> bool:
    """A table row of more than two cells (never ranked as a glossary entry)."""
    for line in text.splitlines():
        cells = line.strip().strip("|").split("|")
        if line.count("|") >= 2 and len(cells) > 2:
            return True
    return False


def match_pattern(sentence: rd.Sentence, term_tokens: Sequence[str]
                  ) -> Optional[Tuple[str, int]]:
    """The strongest declared pattern by which ``sentence`` defines the term,
    as ``(pattern, strength)``, or ``None``."""
    toks = sentence.tokens
    n = len(term_tokens)
    i = find_run(toks, term_tokens)
    if i < 0:
        return None
    opening = _opening(toks, i)
    if opening is None:
        return None
    best: Optional[Tuple[str, int]] = None
    j = i + n
    # the copula after the term
    for cop in COPULAS:
        if tuple(toks[j:j + len(cop)]) == cop:
            best = ("copula:" + " ".join(cop), 1 + opening)
            break
    # the gloss, read on the text right after the term
    m = _term_regex(term_tokens).search(sentence.text or "")
    if m is not None:
        rest = (sentence.text or "")[m.end():]
        stripped = rest.lstrip(_EMPHASIS + " \t")
        # an en dash or a hyphen separates only before a space (``0–1`` and
        # ``golay-like`` are not glosses); a colon or an em dash always
        g = re.match(r"(:|—|–(?=\s)|-(?=\s))\s*(.*)$", stripped, re.S)
        if g is not None and not _table_row(sentence.text or ""):
            gloss = g.group(2).lstrip(_EMPHASIS + " \t")
            if not _is_label(gloss):
                cand = ("gloss:" + (":" if g.group(1) == ":" else g.group(1)), 0)
                if best is None or cand[1] < best[1]:
                    best = cand
        elif re.match(r",\s*(the|a|an)\b", stripped, re.IGNORECASE):
            cand = ("gloss:,", 3)
            if best is None or cand[1] < best[1]:
                best = cand
    return best


# ---------------------------------------------------------------------------
#  Mentions and the context words
# ---------------------------------------------------------------------------

def mention_ids(term_tokens: Sequence[str], knowledge: mdl.Knowledge) -> List[int]:
    """The ids of the sentences holding the term as a contiguous run, in
    corpus order (read through the postings)."""
    if not term_tokens:
        return []
    lists = [knowledge.sentence_ids(t) for t in set(term_tokens)]
    if any(not ids for ids in lists):
        return []
    lists.sort(key=len)
    common = set(lists[0])
    for ids in lists[1:]:
        common.intersection_update(ids)
    sentences = knowledge.sentences
    return sorted(sid for sid in common
                  if find_run(sentences[sid].tokens, term_tokens) >= 0)


def _unit(sentence: rd.Sentence, scale: str):
    if scale == "sentence":
        return sentence.address
    document = sentence.document or sentence.address.split("#", 1)[0]
    if scale == "paragraph":
        return (document, sentence.paragraph)
    return document


def _units_total(knowledge: mdl.Knowledge, scale: str) -> int:
    if scale == "sentence":
        return len(knowledge.sentences)
    return len({_unit(s, scale) for s in knowledge.sentences})


def context(term: str, knowledge: Optional[mdl.Knowledge] = None,
            scale: str = "sentence", k: int = CONTEXT_WORDS) -> Dict[str, Any]:
    """The words over-represented around ``term`` at ``scale``.

    For the units (sentences, paragraphs or documents) that mention the term:
    ``co(w)`` the units holding content word ``w`` too, ``n(w)`` all units
    holding ``w``, ``S`` all units, ``m`` the term's units.  A word is a
    context word when ``co(w) >= MIN_SUPPORT`` and ``co(w)·S > m·n(w)``;
    the first ``k`` by ``co(w)``, then spelling.
    """
    knowledge = _knowledge(knowledge)
    if scale not in SCALES:
        return {"ok": False, "reading": "context", "term": term,
                "refusal": f"the scale must be one of {', '.join(SCALES)}"}
    term_tokens = tokens_of(term)
    if not term_tokens:
        return {"ok": False, "reading": "context", "term": term,
                "refusal": "there is no word to read the context of"}
    ids = mention_ids(term_tokens, knowledge)
    if not ids:
        return {"ok": False, "reading": "context", "term": term,
                "refusal": f"no sentence of the corpus mentions {term!r}"}
    sentences = knowledge.sentences
    own = set(term_tokens)
    if scale == "sentence":
        unit_words = [frozenset(t for t in sentences[sid].tokens
                                if mdl.is_content(t) and t not in own) for sid in ids]
    else:
        keys = {_unit(sentences[sid], scale) for sid in ids}
        grouped: Dict[Any, set] = {key: set() for key in keys}
        # every sentence of a mentioning unit contributes its words
        for s in sentences:
            key = _unit(s, scale)
            if key in grouped:
                grouped[key].update(t for t in s.tokens
                                    if mdl.is_content(t) and t not in own)
        unit_words = [frozenset(v) for v in grouped.values()]
    m = len(unit_words)
    co: Dict[str, int] = {}
    for words in unit_words:
        for w in words:
            co[w] = co.get(w, 0) + 1
    total = _units_total(knowledge, scale)
    rows = []
    for w, c in co.items():
        if c < MIN_SUPPORT:
            continue
        posting = knowledge.sentence_ids(w)
        if scale == "sentence":
            n = len(posting)
        else:
            n = len({_unit(sentences[sid], scale) for sid in posting})
        if c * total > m * n:
            rows.append((w, c, n))
    rows.sort(key=lambda r: (-r[1], r[0]))
    rows = rows[:k]
    return {"ok": True, "reading": "context", "term": term, "scale": scale,
            "units": total, "mentions": m,
            "words": [w for w, _, _ in rows],
            "rows": [{"word": w, "with_term": c, "units": n} for w, c, n in rows],
            "witness": sentences[ids[0]].address}


# ---------------------------------------------------------------------------
#  define
# ---------------------------------------------------------------------------

def _candidates(term_tokens: Sequence[str], ids: Sequence[int],
                knowledge: mdl.Knowledge) -> List[Dict[str, Any]]:
    """Every defining sentence, at its best-ranked copy, in define's own order."""
    best: Dict[Tuple[str, ...], Dict[str, Any]] = {}
    for sid in ids:
        s = knowledge.sentences[sid]
        hit = match_pattern(s, term_tokens)
        if hit is None:
            continue
        rank, label = source_of(s)
        row = {"sid": sid, "address": s.address, "text": one_line(s.text),
               "rank": rank, "source": label, "pattern": hit[0],
               "strength": hit[1], "order": (rank, hit[1], sid)}
        old = best.get(s.tokens)
        if old is None or row["order"] < old["order"]:
            best[s.tokens] = row
    out = sorted(best.values(), key=lambda r: r["order"])
    return out


def grade_of(strength: int, support_count: int) -> str:
    """The quality grade (CONFIDENCE_CURVE_STUDY.md §3)."""
    return ("strong" if strength <= STRONG_STRENGTH
            and support_count >= STRONG_SUPPORT else "weak")


def define(term: str, knowledge: Optional[mdl.Knowledge] = None,
           ranking: str = "context") -> Dict[str, Any]:
    """What the corpus says ``term`` is.

    ``ranking="context"`` (the default, and what ``corpus define`` uses since
    Phase 155) orders the defining sentences by their context support, then by
    define's own order; ``ranking="pattern"`` by define's own order alone
    (source rank, pattern strength, corpus order).

    Returns ``answer`` (the first sentence, cut to 240 characters, one line),
    ``text`` (in full), ``address``, ``candidates`` (the first three
    addresses), ``answers`` (every defining sentence with its source, pattern,
    strength, support and grade), ``witness`` (the address and the
    ``pattern=``/``strength=``/``source=``/``support=`` description),
    ``strength`` (the grade, ``strong`` or ``weak``), ``mentions`` and
    ``documents``, and the ``context`` words; or ``ok=False`` with the reason.
    """
    knowledge = _knowledge(knowledge)
    term_tokens = tokens_of(term)
    base = {"reading": "define", "term": term, "ranking": ranking}
    if not term_tokens:
        return dict(base, ok=False, answer="", mentions=0, documents=0,
                    refusal="there is no word to define")
    ids = mention_ids(term_tokens, knowledge)
    documents = len({knowledge.sentences[sid].document for sid in ids})
    if not ids:
        return dict(base, ok=False, answer="", mentions=0, documents=0,
                    refusal=f"no sentence of the corpus mentions {term!r}")
    found = _candidates(term_tokens, ids, knowledge)
    if not found:
        return dict(base, ok=False, answer="", mentions=len(ids), documents=documents,
                    refusal=(f"the corpus mentions {term!r} in {len(ids)} sentences "
                             f"of {documents} documents but no sentence defines it "
                             f"by a declared pattern"))
    ctx = context(term, knowledge, "sentence")
    words = list(ctx.get("words", ())) if ctx.get("ok") else []
    for row in found:
        row["support"] = support(knowledge.sentences[row["sid"]].tokens, words,
                                 term_tokens)
        row["grade"] = grade_of(row["strength"], row["support"])
    if ranking == "context":
        found.sort(key=lambda r: (-r["support"], r["order"]))
    head = found[0]
    witness = [head["address"], f"pattern={head['pattern']}",
               f"strength={head['strength']}", f"source={head['source']}",
               f"support={head['support']}"]
    answers = [{k: v for k, v in r.items() if k not in ("order",)} for r in found]
    return dict(base, ok=True, answer=_cut(head["text"]), text=head["text"],
                address=head["address"],
                candidates=[r["address"] for r in found[:3]],
                answers=answers, witness=witness, strength=head["grade"],
                pattern=head["pattern"], source=head["source"],
                support=head["support"], mentions=len(ids), documents=documents,
                context=words)


# ---------------------------------------------------------------------------
#  similar and related
# ---------------------------------------------------------------------------

_INVERTED: Dict[Tuple[int, str], Dict[str, List[str]]] = {}


def _inverted(knowledge: mdl.Knowledge, which: str) -> Dict[str, List[str]]:
    key = (id(knowledge), which)
    got = _INVERTED.get(key)
    if got is None:
        sets = knowledge.positions if which == "positions" else knowledge.contexts
        got = {}
        for w, feats in sets.items():
            for f in feats:
                got.setdefault(f, []).append(w)
        _INVERTED.clear()
        _INVERTED[key] = got
    return got


def _neighbours(word: str, knowledge: mdl.Knowledge, which: str, k: int
                ) -> List[Tuple[str, Fraction]]:
    sets = knowledge.positions if which == "positions" else knowledge.contexts
    mine = sets[word]
    shared: Dict[str, int] = {}
    for f in mine:
        for w in _inverted(knowledge, which).get(f, ()):
            if w != word:
                shared[w] = shared.get(w, 0) + 1
    counts = knowledge.model.unigram
    scored = [(Fraction(c * c, len(mine) * len(sets[w])), w) for w, c in shared.items()]
    scored.sort(key=lambda r: (-r[0], -counts[r[1]], r[1]))
    return [(w, s) for s, w in scored[:k]]


def _company(word: str, knowledge: Optional[mdl.Knowledge], which: str,
             reading: str, k: int) -> Dict[str, Any]:
    knowledge = _knowledge(knowledge)
    toks = tokens_of(word)
    if len(toks) != 1:
        return {"ok": False, "reading": reading, "word": word,
                "refusal": f"{reading} reads one word, and {word!r} is "
                           f"{len(toks)} tokens"}
    w = toks[0]
    sets = knowledge.positions if which == "positions" else knowledge.contexts
    if w not in sets:
        seen = knowledge.model.unigram.get(w, 0)
        return {"ok": False, "reading": reading, "word": w,
                "refusal": (f"the corpus never uses {w!r}" if not seen else
                            f"{w!r} occurs {seen} times, too little company to "
                            f"compare")}
    near = _neighbours(w, knowledge, which, k)
    return {"ok": True, "reading": reading, "word": w, "features": len(sets[w]),
            "neighbours": [x for x, _ in near],
            "scores": [s for _, s in near]}


def similar(word: str, knowledge: Optional[mdl.Knowledge] = None,
            k: int = NEIGHBOURS) -> Dict[str, Any]:
    """The ``k`` words used most like ``word``: squared cosine of the positional
    feature sets, ties by larger corpus count, then spelling."""
    return _company(word, knowledge, "positions", "similar", k)


def related(word: str, knowledge: Optional[mdl.Knowledge] = None,
            k: int = NEIGHBOURS) -> Dict[str, Any]:
    """The ``k`` words found most with the same company as ``word``: squared
    cosine of the associated-context sets, ties as :func:`similar`."""
    return _company(word, knowledge, "contexts", "related", k)


# ---------------------------------------------------------------------------
#  predict and continue_text
# ---------------------------------------------------------------------------

def deciding_row(model: mdl.Model, history: Sequence[str]
                 ) -> Tuple[int, Tuple[str, ...], Mapping[str, int]]:
    """The two-token row of the last two tokens if non-empty, else the
    one-token row of the last token; ``(level, context, row)``, level 0 and an
    empty row when neither was ever seen."""
    if len(history) >= 2:
        key2 = (history[-2], history[-1])
        row = model.ctx2.get(key2)
        if row:
            return 2, key2, row
    if history:
        row = model.ctx1.get(history[-1])
        if row:
            return 1, (history[-1],), row
    return 0, tuple(history[-2:]), {}


def top_of(row: Mapping[str, int]) -> Tuple[int, Tuple[str, ...]]:
    """The largest count of a row and every continuation holding it, sorted."""
    if not row:
        return 0, ()
    top = max(row.values())
    return top, tuple(sorted(c for c, n in row.items() if n == top))


def predict(prefix: str, knowledge: Optional[mdl.Knowledge] = None) -> Dict[str, Any]:
    """The guarded next word after ``prefix``: the unique strict maximum of the
    deciding row, and no word at a tie."""
    knowledge = _knowledge(knowledge)
    toks = tokens_of(prefix)
    if not toks:
        return {"ok": False, "reading": "predict", "refusal": "there is no text to go on from"}
    level, key, row = deciding_row(knowledge.model, toks)
    if not row:
        return {"ok": False, "reading": "predict", "context": " ".join(key),
                "refusal": f"the corpus never continues {' '.join(toks[-2:])!r}"}
    top, winners = top_of(row)
    total = sum(row.values())
    if len(winners) > 1:
        return {"ok": False, "reading": "predict", "context": " ".join(key),
                "tie": list(winners), "count": top, "total": total,
                "refusal": (f"a tie: {', '.join(winners)} each follow "
                            f"{' '.join(key)!r} {top} times")}
    word = winners[0]
    return {"ok": True, "reading": "predict", "context": " ".join(key),
            "level": level, "word": word, "count": top, "total": total}


def trigram_witness(knowledge: mdl.Knowledge, key: Sequence[str], token: str
                    ) -> str:
    """The first sentence, in corpus order, in which ``token`` follows ``key``."""
    wanted = tuple(key) + (token,)
    real = [t for t in wanted if t not in (mdl.BOS, mdl.EOS)]
    lists = [knowledge.sentence_ids(t) for t in set(real)]
    if not lists or any(not ids for ids in lists):
        return ""
    lists.sort(key=len)
    common = set(lists[0])
    for ids in lists[1:]:
        common.intersection_update(ids)
    for sid in sorted(common):
        padded = (mdl.BOS, mdl.BOS) + knowledge.sentences[sid].tokens + (mdl.EOS,)
        if find_run(padded, wanted) >= 0:
            return knowledge.sentences[sid].address
    return ""


def continue_text(prefix: str, knowledge: Optional[mdl.Knowledge] = None,
                  max_tokens: int = MAX_CONTINUATION) -> Dict[str, Any]:
    """The corpus's own most frequent continuation of ``prefix``.

    At each step the deciding row (:func:`deciding_row`) gives its unique
    most frequent continuation, with its count over the row's total and the
    first sentence that carries it.  It stops at a tie (naming it), at the end
    of a sentence, at a context the corpus never continues, before re-entering
    a two-token state it has met, or at ``max_tokens``.
    """
    knowledge = _knowledge(knowledge)
    model = knowledge.model
    toks = list(tokens_of(prefix))
    if not toks:
        return {"ok": False, "reading": "continue", "refusal": "there is no text to continue"}
    history = list(toks)
    produced: List[str] = []
    steps: List[Dict[str, Any]] = []
    states = {tuple(history[-2:])}
    stop, why = "limit", f"the limit of {max_tokens} tokens"
    while len(produced) < max_tokens:
        level, key, row = deciding_row(model, history)
        if not row:
            stop, why = "unseen", f"the corpus never continues {' '.join(history[-2:])!r}"
            break
        top, winners = top_of(row)
        if len(winners) > 1:
            stop, why = "tie", (f"a tie between {', '.join(winners)} "
                                f"({top} each after {' '.join(key)!r})")
            break
        token = winners[0]
        if token == mdl.EOS:
            stop, why = "end", "end of sentence"
            break
        state = (history[-1], token)
        if state in states:
            stop, why = "cycle", f"the continuation would repeat {' '.join(state)!r}"
            break
        states.add(state)
        steps.append({"token": token, "count": top, "total": sum(row.values()),
                      "level": level, "context": " ".join(key),
                      "witness": trigram_witness(knowledge, key, token)})
        produced.append(token)
        history.append(token)
    base = {"reading": "continue", "prefix": " ".join(toks), "stop": stop,
            "stopped": why}
    if not produced:
        return dict(base, ok=False, refusal=f"the corpus gives no continuation of "
                                            f"{' '.join(toks)!r}: {why}")
    text = " ".join(produced)
    shown = "; ".join(f"{s['token']} ({s['count']}/{s['total']}, {s['witness']})"
                      for s in steps[:5])
    answer = (f"{' '.join(toks)} \u2026 {text} (the corpus's own most frequent "
              f"continuation; stopped: {why}). Witnesses: {shown}")
    return dict(base, ok=True, answer=answer, text=text, tokens=produced,
                steps=steps, witness=[s["witness"] for s in steps])


# ---------------------------------------------------------------------------
#  spread
# ---------------------------------------------------------------------------

def spread(word: str, knowledge: Optional[mdl.Knowledge] = None) -> Dict[str, Any]:
    """How far ``word`` (or a phrase) reaches through the hierarchy: its
    occurrences, sentences, paragraphs, documents and top-level folders, and
    the sources it stands in."""
    knowledge = _knowledge(knowledge)
    toks = tokens_of(word)
    if not toks:
        return {"ok": False, "reading": "spread", "refusal": "there is no word to read"}
    ids = mention_ids(toks, knowledge)
    if not ids:
        return {"ok": False, "reading": "spread", "term": word,
                "refusal": f"no sentence of the corpus mentions {word!r}"}
    sentences = knowledge.sentences
    occurrences = sum(len(runs(sentences[sid].tokens, toks)) for sid in ids)
    paragraphs = {(sentences[sid].document, sentences[sid].paragraph) for sid in ids}
    documents = {sentences[sid].document for sid in ids}
    folders = {rd.top_folder(d) for d in documents}
    by_source: Dict[str, int] = {}
    for sid in ids:
        label = source_of(sentences[sid])[1]
        by_source[label] = by_source.get(label, 0) + 1
    return {"ok": True, "reading": "spread", "term": " ".join(toks),
            "occurrences": occurrences, "sentences": len(ids),
            "paragraphs": len(paragraphs), "documents": len(documents),
            "folders": sorted(folders),
            "by_source": {k: by_source[k] for k in SOURCES if k in by_source},
            "witness": sentences[ids[0]].address}
