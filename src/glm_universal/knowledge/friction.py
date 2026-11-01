"""``glm_universal.knowledge.friction`` -- the hold-out model and the readers.

Phase 156 (``studies/FRICTION_STUDY.md`` §§2.2-2.4) reads the owner's analogy
of friction in the counted corpus model:

* **the held-out sample** (:func:`sample`) -- qualifying corpus sentences (not
  a heading, not inside a tier-0 block, at least 8 tokens of which at least 6
  are alphabetic and at least 4 are content words, a token sequence occurring
  exactly once in the corpus), every ``k``-th of the ``Q`` in corpus order,
  ``k = max(1, Q // 1000)``, cut at 1000;
* **the hold-out** (:func:`hold_out_model`) -- the counts of every sampled
  sentence (n-gram rows, window pairs, unigrams, tokens) subtracted from the
  corpus model; the predictors read only the subtracted model;
* **the patch predictor** (:func:`patch_predict`) -- the deciding row (the
  two-token row of the last two tokens if non-empty, else the one-token row)
  and its unique most frequent continuation, a tie refusing;
* **the contact predictor** (:func:`contact_predict`) -- the row's 32 tallest
  continuations (:func:`tallest`, ties at the cut by spelling), each scored
  ``R(c)·(1 + A(c))`` with ``A(c)`` the distinct content words ``p != c`` of
  the prefix with window count ``n(p,c) >= 2`` associated with ``c``; the
  tie-break (§2.4: contact only where the patch's row ties at the maximum)
  and the loaded score ``R(c)·(L + A(c))``, ``L = 8``;
* **the continuation** (:func:`continuation`) -- a 3-token prompt continued
  greedily for at most 12 tokens, stopping at the sentence end, a refusal or
  a recurring two-token state, and its overlap with the truth
  (:func:`overlap`);
* **the folder evidence** (:class:`FolderEvidence`) and **the readers** of
  §2.3 -- the leader after each token (:func:`leaders`), the frictionless
  reader and the sticking reader with a margin (moves to the leader only when
  ``S(leader) > (1 + margin)·S(held)``, i.e. ``4·S(leader) > 5·S(held)`` at a
  quarter), with the switch, return and final-reading counts
  (:func:`reading_stats`).

``RequestProject/GLM/Friction.lean`` proves that a keep-or-move reader never
switches more often than the leader (``held_switches_le``), that the held
reading stays within the margin (``held_within_margin``), and the contact
lemmas (``contact_keeps_large_lead``, ``contact_empty_prompt``).

Exact throughout (D7): every count is an ``int`` and every comparison of
scores is in integers or :class:`fractions.Fraction`; nothing samples.

*Reconstructed 31 October 2026 (repository check): the original was lost in
the October 2026 reorganisation; rebuilt from studies/FRICTION_STUDY.md
§§2.2-2.4 and §7, studies/FRICTION_TWO_STUDY.md §§2.3-2.4,
studies/THERMO_FRICTION_STUDY.md §§2.1-2.2 (the interface its experiments
import), RequestProject/GLM/Friction.lean (the sticking rule) and the
knowledge model (knowledge/model.py, knowledge/reader.py).  Two readings the
documents leave open are declared here: a predicted sentence end is
``</s>`` or a sentence-final ``.``/``!``/``?`` (the corpus splits sentences
there, so the token always ends its sentence) and is not part of the
continuation's text; and the token that would re-enter a two-token state the
continuation has already met is not emitted (the stop ``cycle``).*
"""
from __future__ import annotations

import zipfile
from collections import Counter
from dataclasses import dataclass, field
from fractions import Fraction
from typing import (Any, Callable, Dict, FrozenSet, Iterable, List, Mapping,
                    Optional, Sequence, Set, Tuple)

from . import model as mdl
from . import reader as rd

__all__ = [
    "SAMPLE_SIZE", "MIN_TOKENS", "MIN_ALPHA", "MIN_CONTENT", "TOUCH", "LOAD",
    "PROMPT", "MAX_TOKENS", "STOPS", "END_TOKENS",
    "qualifies", "is_heading", "qualifying", "sample", "HeldOut",
    "hold_out_model", "deciding_row", "tallest", "touches", "contact_score",
    "patch_predict", "contact_predict", "tiebreak_predict", "loaded_predict",
    "continuation", "overlap", "predict_positions", "content_words",
    "FolderEvidence", "leaders", "frictionless_reader", "sticking_reader",
    "keep_or_move", "reading_stats", "margin_reader",
]

#: §2.2's sample: at most this many held-out sentences.
SAMPLE_SIZE = 1000
#: A qualifying sentence has at least this many tokens ...
MIN_TOKENS = 8
#: ... of which at least this many are alphabetic ...
MIN_ALPHA = 6
#: ... and at least this many are content words (``model.is_content``).
MIN_CONTENT = 4
#: The contact predictor's candidates: the row's tallest continuations.
TOUCH = 32
#: The load of the loaded contact score ``R·(L + A)`` (§2.4).
LOAD = 8
#: The continuation's prompt (tokens) and its length limit (tokens).
PROMPT = 3
MAX_TOKENS = 12
#: The four declared stops of a continuation.
STOPS: Tuple[str, ...] = ("end", "refusal", "cycle", "limit")
#: A predicted token that ends the sentence.
END_TOKENS: FrozenSet[str] = frozenset({mdl.EOS, ".", "!", "?"})


# ===========================================================================
# 1.  THE HELD-OUT SAMPLE
# ===========================================================================

def content_words(tokens: Iterable[str]) -> List[str]:
    """The distinct content words of ``tokens``, in reading order."""
    seen: Set[str] = set()
    out: List[str] = []
    for t in tokens:
        if mdl.is_content(t) and t not in seen:
            seen.add(t)
            out.append(t)
    return out


def qualifies(tokens: Sequence[str]) -> bool:
    """§2.2's size rule: at least 8 tokens, 6 alphabetic, 4 content words."""
    if len(tokens) < MIN_TOKENS:
        return False
    if sum(1 for t in tokens if t.isalpha()) < MIN_ALPHA:
        return False
    return sum(1 for t in tokens if mdl.is_content(t)) >= MIN_CONTENT


_HEADINGS: Dict[str, FrozenSet[str]] = {}


def _source_text(path: str) -> Optional[str]:
    """The text of a corpus file (a zip member read from its archive)."""
    root = rd.REPOSITORY_ROOT
    if ".zip/" in path:
        archive, member = path.split(".zip/", 1)
        try:
            data = (root / (archive + ".zip")).read_bytes()
            import io
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                return zf.read(member).decode("utf-8", errors="replace")
        except (OSError, KeyError, zipfile.BadZipFile, RuntimeError):
            return None
    try:
        return (root / path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _heading_lines(path: str) -> FrozenSet[str]:
    """The heading texts of a Markdown document (outside fenced code)."""
    if path in _HEADINGS:
        return _HEADINGS[path]
    text = _source_text(path) or ""
    found: Set[str] = set()
    in_fence = False
    for line in text.split("\n"):
        if rd._FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = rd._HEADING.match(line)
        if m:
            found.add(m.group(2).strip())
    _HEADINGS[path] = frozenset(found)
    return _HEADINGS[path]


def is_heading(sentence: rd.Sentence,
               paragraphs: Mapping[Tuple[str, int], rd.Paragraph]) -> bool:
    """Whether a sentence is (part of) a Markdown heading.

    The reader keeps a heading as the first line of its paragraph; a sentence
    is a heading when its document is Markdown, its paragraph's first line is
    one of the document's heading lines, and the sentence starts on that line.
    """
    doc = sentence.document or sentence.address.split("#", 1)[0]
    if not doc.lower().endswith((".md", ".markdown")):
        return False
    para = paragraphs.get((doc, sentence.paragraph))
    if para is None:
        return False
    first = para.text.split("\n", 1)[0].strip()
    if not first or first not in _heading_lines(doc):
        return False
    head = sentence.text.split("\n", 1)[0].strip()
    return bool(head) and head in first


def qualifying(knowledge: mdl.Knowledge) -> List[int]:
    """The ids (into ``knowledge.sentences``) of every qualifying sentence,
    in corpus order (§2.2)."""
    counts = Counter(s.tokens for s in knowledge.sentences)
    paragraphs = {(d.path, p.index): p for d in knowledge.documents
                  for p in d.paragraphs}
    out: List[int] = []
    for sid, s in enumerate(knowledge.sentences):
        if s.tier0 or counts[s.tokens] != 1 or not qualifies(s.tokens):
            continue
        if is_heading(s, paragraphs):
            continue
        out.append(sid)
    return out


def sample(knowledge: Optional[mdl.Knowledge] = None,
           size: int = SAMPLE_SIZE) -> Tuple[rd.Sentence, ...]:
    """The held-out sample: every ``k``-th qualifying sentence from the first,
    ``k = max(1, Q // size)``, cut at ``size``."""
    knowledge = mdl.load() if knowledge is None else knowledge
    ids = qualifying(knowledge)
    k = max(1, len(ids) // size)
    return tuple(knowledge.sentences[i] for i in ids[::k][:size])


# ===========================================================================
# 2.  THE HOLD-OUT MODEL
# ===========================================================================

class HeldOut:
    """The corpus model with the counts of the held-out sentences subtracted.

    A view, not a copy: the deltas of the held-out sentences are kept beside
    the (unchanged) model and subtracted on reading, so every count is the
    count of the corpus without them.  Because each held-out sentence occurs
    once in the corpus, nothing of it survives the subtraction.
    """

    def __init__(self, model: mdl.Model, sentences: Iterable[Sequence[str]]):
        self.model = model
        self.d_uni: Counter = Counter()
        self.d1: Dict[str, Counter] = {}
        self.d2: Dict[Tuple[str, str], Counter] = {}
        self.d_win: Counter = Counter()
        self.d_tokens = 0
        self.d_pairs = 0
        self.d_sentences = 0
        for toks in sentences:
            self._subtract(tuple(toks))
        self._tallest: Dict[Tuple[str, ...], Tuple[Tuple[str, int], ...]] = {}
        self._tied: Dict[Tuple[str, ...], Tuple[str, ...]] = {}

    def _subtract(self, toks: Tuple[str, ...]) -> None:
        self.d_sentences += 1
        self.d_tokens += len(toks)
        self.d_uni.update(toks)
        padded = (mdl.BOS, mdl.BOS) + toks + (mdl.EOS,)
        for i in range(2, len(padded)):
            a, b, c = padded[i - 2], padded[i - 1], padded[i]
            self.d1.setdefault(b, Counter())[c] += 1
            self.d2.setdefault((a, b), Counter())[c] += 1
        content = [(i, t) for i, t in enumerate(toks) if mdl.is_content(t)]
        for j in range(len(content)):
            pj, tj = content[j]
            for k in range(j + 1, len(content)):
                pk, tk = content[k]
                if pk - pj > mdl.WINDOW:
                    break
                if tj == tk:
                    continue
                key = (tj, tk) if tj < tk else (tk, tj)
                self.d_win[key] += 1
                self.d_pairs += 1

    # -- the subtracted counts --------------------------------------------

    @property
    def tokens(self) -> int:
        return self.model.tokens - self.d_tokens

    @property
    def window_pairs(self) -> int:
        return self.model.window_pairs - self.d_pairs

    def unigram(self, token: str) -> int:
        return self.model.unigram.get(token, 0) - self.d_uni.get(token, 0)

    def window(self, a: str, b: str) -> int:
        key = (a, b) if a < b else (b, a)
        return self.model.window.get(key, 0) - self.d_win.get(key, 0)

    def associated(self, a: str, b: str) -> bool:
        """``model.associated`` on the subtracted counts."""
        t = self.tokens
        return (self.window(a, b) * t * t
                > self.unigram(a) * self.unigram(b) * self.window_pairs)

    def row(self, context: Tuple[str, ...]) -> Dict[str, int]:
        """The one-token (``(b,)``) or two-token (``(a, b)``) row, subtracted;
        entries with a count of zero are dropped."""
        if len(context) == 1:
            base = self.model.ctx1.get(context[0])
            delta = self.d1.get(context[0])
        else:
            base = self.model.ctx2.get((context[0], context[1]))
            delta = self.d2.get((context[0], context[1]))
        if not base:
            return {}
        if not delta:
            return dict(base)
        out = {}
        for c, n in base.items():
            m = n - delta.get(c, 0)
            if m > 0:
                out[c] = m
        return out

    def _sorted(self, key: Tuple[str, ...]) -> None:
        row = self.row(key)
        if not row:
            self._tallest[key] = ()
            self._tied[key] = ()
            return
        ordered = sorted(row.items(), key=lambda kv: (-kv[1], kv[0]))
        top = ordered[0][1]
        self._tallest[key] = tuple(ordered[:TOUCH])
        self._tied[key] = tuple(c for c, n in ordered if n == top)

    def tallest(self, key: Tuple[str, ...], k: int = TOUCH
                ) -> Tuple[Tuple[str, int], ...]:
        if key not in self._tallest:
            self._sorted(key)
        return self._tallest[key][:k]

    def tied_at_top(self, key: Tuple[str, ...]) -> Tuple[str, ...]:
        if key not in self._tied:
            self._sorted(key)
        return self._tied[key]


def hold_out_model(knowledge: Optional[mdl.Knowledge] = None,
                   held: Optional[Sequence[rd.Sentence]] = None) -> HeldOut:
    """The model trained on ``knowledge`` minus the ``held`` sentences
    (default: :func:`sample`)."""
    knowledge = mdl.load() if knowledge is None else knowledge
    held = sample(knowledge) if held is None else held
    return HeldOut(knowledge.model, (s.tokens for s in held))


# ===========================================================================
# 3.  THE PREDICTORS
# ===========================================================================

def deciding_row(model: HeldOut, prefix: Sequence[str]
                 ) -> Optional[Tuple[str, ...]]:
    """The key of the deciding row: the two-token row of the last two tokens
    if non-empty, else the one-token row; ``None`` when both are empty."""
    if len(prefix) >= 2:
        key2 = (prefix[-2], prefix[-1])
        if model.tallest(key2, 1):
            return key2
    if prefix:
        key1 = (prefix[-1],)
        if model.tallest(key1, 1):
            return key1
    return None


def tallest(model: HeldOut, prefix: Sequence[str], k: int = TOUCH
            ) -> List[Tuple[str, int]]:
    """The ``k`` tallest continuations of the deciding row, with their counts
    ``R(c)`` (most frequent first, ties by spelling)."""
    key = deciding_row(model, prefix)
    return [] if key is None else list(model.tallest(key, k))


def touches(model: HeldOut, candidate: str, words: Iterable[str]) -> List[str]:
    """The words ``p != candidate`` with window count ``n(p, c) >= 2`` that
    are associated with ``candidate`` -- the asperities that touch it."""
    out = []
    for p in words:
        if p == candidate:
            continue
        if model.window(p, candidate) >= mdl.MIN_PAIR and \
                model.associated(p, candidate):
            out.append(p)
    return out


def contact_score(r: int, a: int, load: int = 1) -> int:
    """``R(c)·(load + A(c))`` -- Friction.lean's ``contact`` at ``load = 1``."""
    return r * (load + a)


def _unique_max(scored: Sequence[Tuple[Any, str]]) -> Optional[str]:
    if not scored:
        return None
    best = max(s for s, _ in scored)
    top = [c for s, c in scored if s == best]
    return top[0] if len(top) == 1 else None


def patch_predict(model: HeldOut, prefix: Sequence[str]) -> Optional[str]:
    """The patch predictor: the deciding row's unique most frequent
    continuation, ``None`` (a refusal) on a tie or an empty row."""
    top = tallest(model, prefix, 2)
    if not top:
        return None
    if len(top) > 1 and top[1][1] == top[0][1]:
        return None
    return top[0][0]


def _prefix_words(prefix: Sequence[str],
                  words: Optional[Iterable[str]]) -> List[str]:
    return content_words(prefix) if words is None else content_words(words)


def contact_predict(model: HeldOut, prefix: Sequence[str],
                    words: Optional[Iterable[str]] = None,
                    load: int = 1) -> Optional[str]:
    """The contact predictor: over the row's 32 tallest, the unique maximum of
    ``R(c)·(load + A(c))``; ``words`` replaces the prefix's content words (the
    mismatched control passes another sentence's)."""
    cands = tallest(model, prefix)
    if not cands:
        return None
    ws = _prefix_words(prefix, words)
    return _unique_max([(contact_score(r, len(touches(model, c, ws)), load), c)
                        for c, r in cands])


def loaded_predict(model: HeldOut, prefix: Sequence[str],
                   words: Optional[Iterable[str]] = None,
                   load: int = LOAD) -> Optional[str]:
    """Loaded contact (§2.4): ``R(c)·(L + A(c))`` with ``L = 8``."""
    return contact_predict(model, prefix, words, load)


def tiebreak_predict(model: HeldOut, prefix: Sequence[str],
                     words: Optional[Iterable[str]] = None) -> Optional[str]:
    """Contact as a tie-break (§2.4): the patch's answer wherever it is
    decided; where the deciding row ties at the maximum, the tied candidates
    ordered by ``A(c)`` and a unique maximum answers."""
    key = deciding_row(model, prefix)
    if key is None:
        return None
    tied = model.tied_at_top(key)
    if len(tied) == 1:
        return tied[0]
    ws = _prefix_words(prefix, words)
    return _unique_max([(len(touches(model, c, ws)), c) for c in tied])


# ===========================================================================
# 4.  THE CONTINUATION AND THE POSITIONS
# ===========================================================================

#: A step chooser of a continuation: ``(model, history, state) -> token or
#: None``; ``state`` is a dict the chooser may keep its own memory in.
Chooser = Callable[[HeldOut, List[str], Dict[str, Any]], Optional[str]]


def _as_chooser(predictor: Any) -> Chooser:
    if getattr(predictor, "_chooser", False):
        return predictor
    return lambda model, history, state: predictor(model, history)


def continuation(predictor: Any, model: HeldOut, prompt: Sequence[str],
                 max_tokens: int = MAX_TOKENS) -> Dict[str, Any]:
    """Continue ``prompt`` greedily under ``predictor`` for at most
    ``max_tokens`` tokens.

    Stops: ``end`` (a sentence end is predicted), ``refusal`` (no unique
    answer), ``cycle`` (the next token would re-enter a two-token state the
    continuation has met -- that token is not emitted) and ``limit``.  A
    predictor is called as ``predictor(model, history)`` (the contact
    predictors read the history's content words: the prompt's and the
    continuation's own); a chooser marked ``_chooser`` is called with a state
    dict as well.
    """
    choose = _as_chooser(predictor)
    history = list(prompt)
    produced: List[str] = []
    seen = {tuple(history[-2:])}
    state: Dict[str, Any] = {}
    stop = "limit"
    while len(produced) < max_tokens:
        token = choose(model, history, state)
        if token is None:
            stop = "refusal"
            break
        if token in END_TOKENS:
            stop = "end"
            break
        nxt = (history[-1], token) if history else (token,)
        if nxt in seen:
            stop = "cycle"
            break
        seen.add(nxt)
        history.append(token)
        produced.append(token)
    return {"tokens": produced, "text": " ".join(produced), "stop": stop,
            "state": state}


def overlap(produced: Sequence[str], truth: Sequence[str]) -> int:
    """The size of the multiset intersection of ``produced`` and ``truth``."""
    return sum((Counter(produced) & Counter(truth)).values())


def predict_positions(predictor: Any, model: HeldOut,
                      sentence: Sequence[str],
                      words_for: Optional[Callable[[int], Iterable[str]]] = None
                      ) -> Dict[str, Any]:
    """Predict every token ``j`` from 2 to ``len - 1`` from tokens
    ``0..j-1``: the positions, how many were answered, how many correctly,
    and the per-position verdicts (``None`` refused, else right or wrong).

    ``words_for(j)`` supplies the prompt words of a contact predictor (the
    mismatched control); a chooser marked ``_chooser`` keeps one state over
    the sentence's positions."""
    toks = list(sentence)
    choose = _as_chooser(predictor)
    state: Dict[str, Any] = {}
    verdicts: List[Optional[bool]] = []
    for j in range(2, len(toks)):
        prefix = toks[:j]
        if words_for is not None:
            got = predictor(model, prefix, words_for(j))
        else:
            got = choose(model, prefix, state)
        verdicts.append(None if got is None else got == toks[j])
    return {"positions": len(verdicts),
            "answered": sum(1 for v in verdicts if v is not None),
            "correct": sum(1 for v in verdicts if v),
            "verdicts": verdicts}


# ===========================================================================
# 5.  THE FOLDER EVIDENCE AND THE READERS
# ===========================================================================

def _top_of(s: rd.Sentence) -> str:
    return rd.top_folder(s.document or s.address.split("#", 1)[0])


def _directory_of(s: rd.Sentence) -> str:
    return s.folder


class FolderEvidence:
    """The folder evidence of §2.3 at one scale.

    ``scale="top"``: a sentence's folder is the top folder of its document
    (``reader.top_folder``); ``scale="directory"``: its directory
    (``Sentence.folder``, §2.4's directory reader).  ``n(p, f)`` is the
    number of corpus sentences of ``f`` containing ``p``; read for a held-out
    sentence it is less one in the sentence's own folder (the sentence itself
    not counted).
    """

    def __init__(self, knowledge: Optional[mdl.Knowledge] = None,
                 scale: str = "top") -> None:
        if scale not in ("top", "directory"):
            raise ValueError("scale must be 'top' or 'directory'")
        self.knowledge = mdl.load() if knowledge is None else knowledge
        self.scale = scale
        of = _top_of if scale == "top" else _directory_of
        self.folder_of: Tuple[str, ...] = tuple(of(s) for s in
                                                self.knowledge.sentences)
        self.folders: Tuple[str, ...] = tuple(sorted(set(self.folder_of)))
        self._counts: Dict[str, Counter] = {}

    @property
    def size(self) -> int:
        """``F``, the number of folders."""
        return len(self.folders)

    def folder(self, sentence: rd.Sentence) -> str:
        return _top_of(sentence) if self.scale == "top" else \
            _directory_of(sentence)

    def counts(self, word: str) -> Counter:
        """``n(word, f)`` for every folder (corpus sentences, all counted)."""
        got = self._counts.get(word)
        if got is None:
            got = Counter(self.folder_of[i]
                          for i in self.knowledge.sentence_ids(word))
            self._counts[word] = got
        return got

    def held_counts(self, word: str, sentence: rd.Sentence) -> Dict[str, int]:
        """``n(word, f)`` with the held-out sentence not counted."""
        n = dict(self.counts(word))
        if word in sentence.tokens:
            own = self.folder(sentence)
            if n.get(own, 0) > 0:
                n[own] -= 1
                if n[own] == 0:
                    del n[own]
        return n

    def height(self, word: str, sentence: rd.Sentence) -> Tuple[int, Tuple[str, ...]]:
        """The word's height ``F − |{f : n(p,f) > 0}|`` and the folders that
        hold it, the sentence itself not counted."""
        held = self.held_counts(word, sentence)
        holding = tuple(sorted(f for f, n in held.items() if n > 0))
        return self.size - len(holding), holding


def _leader(scores: Mapping[str, int]) -> Optional[str]:
    """The highest-scoring folder, ties by folder name; ``None`` when no
    score is positive."""
    best = None
    for f in sorted(scores):
        s = scores[f]
        if s > 0 and (best is None or s > scores[best]):
            best = f
    return best


def leaders(evidence: FolderEvidence, sentence: rd.Sentence) -> Dict[str, Any]:
    """The word-by-word reading of ``sentence``: after each token, the score
    of every folder (the summed height of the distinct content words read so
    far that it holds) and the leader; the reading starts at the first token
    with a positive score.  ``steps`` lists ``(scores, leader)`` from there."""
    scores: Dict[str, int] = {}
    seen: Set[str] = set()
    steps: List[Tuple[Dict[str, int], str]] = []
    for tok in sentence.tokens:
        if mdl.is_content(tok) and tok not in seen:
            seen.add(tok)
            h, holding = evidence.height(tok, sentence)
            if h:
                for f in holding:
                    scores[f] = scores.get(f, 0) + h
        lead = _leader(scores)
        if lead is not None:
            steps.append((dict(scores), lead))
    return {"truth": evidence.folder(sentence), "steps": steps,
            "leaders": [lead for _s, lead in steps]}


def keep_or_move(steps: Sequence[Tuple[Mapping[str, int], str]],
                 moves: Callable[[int, int, int], bool]) -> List[str]:
    """A keep-or-move reader: it starts at the first leader and at each later
    step moves to the leader exactly when ``moves(t, S(held), S(leader))``."""
    out: List[str] = []
    for t, (scores, lead) in enumerate(steps):
        if not out:
            out.append(lead)
            continue
        held = out[-1]
        if held != lead and moves(t, scores.get(held, 0), scores[lead]):
            out.append(lead)
        else:
            out.append(held)
    return out


def frictionless_reader(evidence: FolderEvidence, sentence: rd.Sentence
                        ) -> List[str]:
    """The frictionless reader: the leader at every step."""
    return list(leaders(evidence, sentence)["leaders"])


def margin_reader(steps: Sequence[Tuple[Mapping[str, int], str]],
                  margin: Fraction = Fraction(1, 4)) -> List[str]:
    """The sticking reader over given steps: it moves to the leader only when
    ``S(leader) > (1 + margin)·S(held)`` -- with ``margin = 1/q``,
    Friction.lean's ``(q+1)·S(held) < q·S(leader)``."""
    m = Fraction(margin)
    return keep_or_move(steps, lambda t, held, lead:
                        lead * m.denominator > (m.denominator + m.numerator) * held)


def sticking_reader(evidence: FolderEvidence, sentence: rd.Sentence,
                    margin: Fraction = Fraction(1, 4)) -> List[str]:
    """The sticking reader (§2.3): holds its reading until the leader beats
    it by ``margin`` (a quarter for the marks)."""
    return margin_reader(leaders(evidence, sentence)["steps"], margin)


def reading_stats(readings: Sequence[str], truth: str) -> Dict[str, int]:
    """Switches (changes between consecutive steps), returns (switches back
    to a folder held before in the same sentence), switches into the truth,
    and whether the final reading is the sentence's own folder."""
    switches = returns = into_truth = 0
    held: Set[str] = set()
    for i, r in enumerate(readings):
        if i and r != readings[i - 1]:
            switches += 1
            if r in held:
                returns += 1
            if r == truth:
                into_truth += 1
        held.add(r)
    final = int(bool(readings) and readings[-1] == truth)
    return {"switches": switches, "returns": returns,
            "into_truth": into_truth, "final_correct": final}
