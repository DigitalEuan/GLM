"""``glm_universal.knowledge.study`` -- the measurement of Phase 154.

``studies/CORPUS_KNOWLEDGE_STUDY.md``: the corpus counted rather than trained,
measured against the marks declared before the measurement (§3: K1-K9) and
the two amended marks (§3a: K3', K8'):

* **K1-K4** -- next-token prediction on the *novel* sentences of the held-out
  fifth of the documents (document ``i`` of the sorted corpus is held out
  when ``i mod 5 = 4``; a held-out sentence is novel when its token sequence
  occurs nowhere in the training documents): the counted model (two-token
  context, backing off to one, then to the most frequent token) against the
  most frequent token (K1) and against the **order control** -- the same
  training documents with every sentence's tokens sorted (K2); the declared
  guard (a two-token context seen at least twice with a unique maximum, K3)
  and the majority guard (seen at least three times, the winner more than
  half, K3'); the accuracy as the training documents grow by quarters (K4);
* **K5** -- additivity and order-freedom on the real corpus;
* **K6, K7** -- ``similar`` on the twelve number words, and singular/plural
  pairs under ``similar`` and ``related``;
* **K8, K9, K8'** -- ``define`` on the frequency term list, the backwards
  spellings, and the corpus's own bold terms.

:func:`compute` takes the whole measurement from the corpus as it now is
(several minutes: about ten models are counted).  Nothing here writes: the
stored measurement (``_data/corpus_knowledge.json``) is written only by
``tools corpus-knowledge --write``, and :func:`corpus_knowledge_report`
reports it absent or stale when it is.

Two readings the study leaves open are declared here: the unguarded
prediction breaks a tie at the maximum by spelling (it must answer every
position; the readings themselves refuse a tie), and the held-out sentences
of a document are its distinct sentences (the model's own rule).

*Created 31 October 2026 (repository check).*

*Reconstructed 31 October 2026 (repository check): the original was lost in
the October 2026 reorganisation (the 29 October placeholder returned every
mark false); rebuilt from studies/CORPUS_KNOWLEDGE_STUDY.md §§3, 3a and 7,
MASTER_PLAN.md Phase 154, the report shape read by tools.py
``_corpus_knowledge`` and the names knowledge/word_address.py imports
(``NUMBER_WORDS``, ``plural_pairs``).  ``NUMBER_WORDS`` is the study's twelve
number words *one* ... *twelve* (K6, W2: 12 words, 120 neighbours); the
placeholder had listed 32.*
"""
from __future__ import annotations

import json
import re
from collections import Counter
from fractions import Fraction
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .. import integrity
from . import model as mdl
from . import reader as rd

__all__ = [
    "NUMBER_WORDS", "plural_pairs", "heldout_split", "novel_sentences",
    "prediction_stats", "frequency_terms", "bold_terms", "backwards",
    "define_rate", "number_word_share", "plural_rates", "additivity",
    "DATA_PATH", "_SOURCES", "compute", "measure", "write_measurements",
    "measurements", "state", "current", "module_digest",
    "corpus_knowledge_report",
]

_HERE = Path(__file__).resolve().parent
DATA_PATH = _HERE / "_data" / "corpus_knowledge.json"

#: Files whose digest ``module_digest`` covers.
_SOURCES: Tuple[str, ...] = (
    "knowledge/study.py",
    "knowledge/model.py",
    "knowledge/reader.py",
    "knowledge/answer.py",
)

_cache: Optional[Dict[str, object]] = None

#: The twelve number words of K6 (and W2/W2' of Phase 155).
NUMBER_WORDS: Tuple[str, ...] = (
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "ten", "eleven", "twelve",
)

#: Held-out rule: document ``i`` of the sorted corpus when ``i % FOLDS == HELD``.
FOLDS = 5
HELD = 4

#: The term lists of K8 and K8'.
FREQUENT_WORDS = 40
FREQUENT_PAIRS = 40
BOLD_TERMS = 60
MIN_TERM_LETTERS = 4


# ---------------------------------------------------------------------------
#  The split and the positions
# ---------------------------------------------------------------------------

def heldout_split(documents: Sequence[rd.Document]
                  ) -> Tuple[List[rd.Document], List[rd.Document]]:
    """``(training, held_out)``: the document at index ``i`` of the sorted list
    is held out when ``i mod 5 = 4``."""
    ordered = sorted(documents, key=lambda d: d.path)
    train = [d for i, d in enumerate(ordered) if i % FOLDS != HELD]
    held = [d for i, d in enumerate(ordered) if i % FOLDS == HELD]
    return train, held


def distinct_sentences(documents: Iterable[rd.Document]) -> List[Tuple[str, ...]]:
    """Every document's distinct token sequences, in order (the model's rule)."""
    out: List[Tuple[str, ...]] = []
    for d in documents:
        seen = set()
        for s in d.sentences:
            if s.tokens not in seen:
                seen.add(s.tokens)
                out.append(s.tokens)
    return out


def novel_sentences(train: Iterable[rd.Document], held: Iterable[rd.Document]
                    ) -> Tuple[List[Tuple[str, ...]], int]:
    """The held-out sentences said nowhere in the training documents, and the
    number of held-out sentences."""
    known = {s.tokens for d in train for s in d.sentences}
    held_sentences = distinct_sentences(held)
    return [t for t in held_sentences if t not in known], len(held_sentences)


class _Rows:
    """The backed-off model's decision at each context, cached."""

    def __init__(self, model: mdl.Model):
        self.model = model
        self._two: Dict[Tuple[str, str], Tuple[int, int, int, str]] = {}
        self._one: Dict[str, Tuple[int, int, int, str]] = {}
        uni = model.unigram
        self.most_frequent = min(uni, key=lambda w: (-uni[w], w)) if uni else ""

    @staticmethod
    def _summary(row: Mapping[str, int]) -> Tuple[int, int, int, str]:
        """``(total, top, ties at top, winner)`` -- the winner the
        spelling-first of the maxima."""
        total = sum(row.values())
        top = max(row.values())
        tied = [c for c, n in row.items() if n == top]
        return total, top, len(tied), min(tied)

    def two(self, a: str, b: str) -> Optional[Tuple[int, int, int, str]]:
        key = (a, b)
        if key not in self._two:
            row = self.model.ctx2.get(key)
            self._two[key] = self._summary(row) if row else None
        return self._two[key]

    def one(self, b: str) -> Optional[Tuple[int, int, int, str]]:
        if b not in self._one:
            row = self.model.ctx1.get(b)
            self._one[b] = self._summary(row) if row else None
        return self._one[b]


def prediction_stats(model: mdl.Model, sentences: Iterable[Tuple[str, ...]],
                     baseline: Optional[str] = None) -> Dict[str, int]:
    """Score every token (and the end marker) of ``sentences``.

    ``right``: the backed-off model; ``baseline_right``: always the most
    frequent token of the training counts; ``guarded_*``: the declared guard
    (two-token context seen at least twice, unique maximum); ``majority_*``:
    the majority guard (seen at least three times, the winner more than half).
    """
    rows = _Rows(model)
    base = rows.most_frequent if baseline is None else baseline
    out = {"positions": 0, "right": 0, "baseline_right": 0,
           "guarded_answered": 0, "guarded_right": 0,
           "majority_answered": 0, "majority_right": 0}
    for toks in sentences:
        padded = (mdl.BOS, mdl.BOS) + tuple(toks) + (mdl.EOS,)
        for i in range(2, len(padded)):
            truth = padded[i]
            out["positions"] += 1
            out["baseline_right"] += truth == base
            two = rows.two(padded[i - 2], padded[i - 1])
            if two is not None:
                guess = two[3]
                total, top, ties, winner = two
                if total >= 2 and ties == 1:
                    out["guarded_answered"] += 1
                    out["guarded_right"] += truth == winner
                if total >= 3 and ties == 1 and 2 * top > total:
                    out["majority_answered"] += 1
                    out["majority_right"] += truth == winner
            else:
                one = rows.one(padded[i - 1])
                guess = one[3] if one is not None else base
            out["right"] += truth == guess
    return out


def _ratio(a: int, b: int) -> Fraction:
    return Fraction(a, b) if b else Fraction(0)


# ---------------------------------------------------------------------------
#  K5: additivity
# ---------------------------------------------------------------------------

def additivity(train: Sequence[rd.Document]) -> Dict[str, Any]:
    """The model of the training documents against the sum of the models of
    its two halves, and against the model of the documents reversed."""
    whole = mdl.train(train)
    half = len(train) // 2
    summed = mdl.train(train[:half]).merge(mdl.train(train[half:]))
    reverse = mdl.train(list(reversed(train)))
    sig = whole.signature()
    return {"documents": len(train), "signature": sig,
            "sum_of_halves_equal": summed.signature() == sig,
            "reverse_order_equal": reverse.signature() == sig}


# ---------------------------------------------------------------------------
#  K6, K7: word use
# ---------------------------------------------------------------------------

def number_word_share(knowledge: mdl.Knowledge) -> Dict[str, Any]:
    """K6: the share of the ten ``similar`` neighbours of each number word that
    are number words."""
    from . import answer as ans
    words = set(NUMBER_WORDS)
    rows, hits, asked = [], 0, 0
    for w in NUMBER_WORDS:
        got = ans.similar(w, knowledge)
        if not got.get("ok"):
            rows.append({"word": w, "refusal": got.get("refusal", "")})
            continue
        h = sum(1 for x in got["neighbours"] if x in words)
        hits += h
        asked += 1
        rows.append({"word": w, "neighbours": got["neighbours"], "number_words": h})
    total = ans.NEIGHBOURS * len(NUMBER_WORDS)
    vocabulary = len(knowledge.positions)
    return {"rows": rows, "hits": hits, "neighbours": total,
            "mean_share": _ratio(hits, total),
            # the chance of a random neighbour being one of the other 11
            "chance": _ratio(len(NUMBER_WORDS) - 1, max(vocabulary - 1, 1))}


def plural_pairs(knowledge: Any) -> List[Tuple[str, str]]:
    """The singular/plural pairs of K7 (and W3): every alphabetic content word
    ``w`` of at least three letters, not ending in ``s``, such that ``w`` and
    ``w + "s"`` both have a positional and an associated-context set -- both
    read and compared.  Sorted by spelling."""
    contexts = getattr(knowledge, "contexts", {}) or {}
    positions = getattr(knowledge, "positions", {}) or {}
    out = []
    for w in sorted(contexts):
        if not (w.isalpha() and len(w) >= 3 and not w.endswith("s")
                and mdl.is_content(w)):
            continue
        p = w + "s"
        if p in contexts and w in positions and p in positions:
            out.append((w, p))
    return out


def plural_rates(knowledge: mdl.Knowledge, pairs: Optional[Sequence[Tuple[str, str]]] = None
                 ) -> Dict[str, Any]:
    """K7: the plural among the ten neighbours of the singular, under
    ``similar`` and under ``related``."""
    from . import answer as ans
    pairs = plural_pairs(knowledge) if pairs is None else list(pairs)
    sim = rel = 0
    examples: List[Dict[str, str]] = []
    for w, p in pairs:
        s_hit = p in ans.similar(w, knowledge).get("neighbours", ())
        r_hit = p in ans.related(w, knowledge).get("neighbours", ())
        sim += s_hit
        rel += r_hit
        if (s_hit or r_hit) and len(examples) < 12:
            examples.append({"word": w, "plural": p})
    n = len(pairs)
    return {"pairs": n, "similar_hits": sim, "related_hits": rel,
            "similar_rate": _ratio(sim, n), "related_rate": _ratio(rel, n),
            "similar_chance": _ratio(ans.NEIGHBOURS, len(knowledge.positions)),
            "related_chance": _ratio(ans.NEIGHBOURS, len(knowledge.contexts)),
            "examples": examples}


# ---------------------------------------------------------------------------
#  K8, K9, K8': define
# ---------------------------------------------------------------------------

def frequency_terms(knowledge: mdl.Knowledge) -> List[str]:
    """K8's term list: the 40 alphabetic content words of at least four letters
    with the largest document frequency, and the 40 pairs of adjacent
    alphabetic content words with the largest sentence count (ties by
    spelling)."""
    df = knowledge.model.df
    words = [w for w in df if mdl.is_content(w) and len(w) >= MIN_TERM_LETTERS
             and w.isalpha()]
    words.sort(key=lambda w: (-df[w], w))
    pairs: Counter = Counter()
    for s in knowledge.sentences:
        toks = s.tokens
        found = {(a, b) for a, b in zip(toks, toks[1:])
                 if a != b and a.isalpha() and b.isalpha()
                 and mdl.is_content(a) and mdl.is_content(b)}
        pairs.update(found)
    ranked = sorted(pairs, key=lambda ab: (-pairs[ab], ab))
    return words[:FREQUENT_WORDS] + [f"{a} {b}" for a, b in ranked[:FREQUENT_PAIRS]]


_BOLD = re.compile(r"\*\*([^*\n]{1,80}?)\*\*")


def bold_terms(knowledge: mdl.Knowledge, root: Optional[Path] = None,
               limit: int = BOLD_TERMS) -> List[str]:
    """K8''s term list: the phrases of one to three alphabetic words set in
    bold most often across the written Markdown documents (outside the
    archive and the supplied material), ties by spelling."""
    root = rd.REPOSITORY_ROOT if root is None else Path(root)
    counts: Counter = Counter()
    for d in knowledge.documents:
        path = d.path
        if not path.lower().endswith((".md", ".markdown")):
            continue
        if rd.top_folder(path) in ("archive", "source_material") or ".zip/" in path:
            continue
        try:
            text = (root / path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in _BOLD.finditer(text):
            phrase = m.group(1).strip().strip(".:;,!?").strip().lower()
            if re.fullmatch(r"[a-z]+(?: [a-z]+){0,2}", phrase):
                counts[phrase] += 1
    ranked = sorted(counts, key=lambda p: (-counts[p], p))
    return ranked[:limit]


def backwards(term: str) -> str:
    """K9: the term spelled backwards (``golay`` -> ``yalog``)."""
    return term[::-1]


def define_rate(knowledge: mdl.Knowledge, terms: Sequence[str]) -> Dict[str, Any]:
    """``define`` on ``terms``: how many are answered, and how many of their
    backwards spellings are refused."""
    from . import answer as ans
    answered, refused, rows = 0, 0, []
    for term in terms:
        got = ans.define(term, knowledge)
        back = ans.define(backwards(term), knowledge)
        answered += bool(got.get("ok"))
        refused += not back.get("ok")
        rows.append({"term": term, "answered": bool(got.get("ok")),
                     "address": got.get("address", ""),
                     "pattern": got.get("pattern", ""),
                     "backwards": backwards(term),
                     "backwards_refused": not back.get("ok")})
    return {"terms": len(terms), "answered": answered, "nonsense_refused": refused,
            "rows": rows}


# ---------------------------------------------------------------------------
#  The measurement
# ---------------------------------------------------------------------------

def compute(knowledge: Optional[mdl.Knowledge] = None) -> Dict[str, object]:
    """Take the Phase 154 measurement from the corpus as it now is."""
    knowledge = mdl.load() if knowledge is None else knowledge
    docs = list(knowledge.documents)
    train, held = heldout_split(docs)
    novel, held_count = novel_sentences(train, held)
    model = mdl.train(train)
    control = mdl.train(train, transform=mdl.sorted_tokens)
    m = prediction_stats(model, novel)
    c = prediction_stats(control, novel, baseline=_Rows(model).most_frequent)
    positions = m["positions"]
    accuracy = _ratio(m["right"], positions)
    baseline = _ratio(m["baseline_right"], positions)
    guarded_precision = _ratio(m["guarded_right"], m["guarded_answered"])
    guarded_coverage = _ratio(m["guarded_answered"], positions)
    majority_precision = _ratio(m["majority_right"], m["majority_answered"])
    majority_coverage = _ratio(m["majority_answered"], positions)
    curve = []
    for q in (1, 2, 3, 4):
        part = train[:len(train) * q // 4]
        s = prediction_stats(mdl.train(part, with_window=False), novel)
        curve.append({"quarter": q, "documents": len(part), "right": s["right"],
                      "accuracy": _ratio(s["right"], s["positions"])})
    add = additivity(train)
    numbers = number_word_share(knowledge)
    plural = plural_rates(knowledge)
    define = define_rate(knowledge, frequency_terms(knowledge))
    define_bold = define_rate(knowledge, bold_terms(knowledge))
    whole = knowledge.model
    marks = {
        "K1": accuracy >= 2 * baseline,
        "K2": accuracy - _ratio(c["right"], c["positions"]) >= Fraction(1, 10),
        "K3": guarded_precision >= Fraction(3, 2) * accuracy
              and guarded_coverage >= Fraction(1, 5),
        "K4": curve[-1]["accuracy"] >= curve[0]["accuracy"],
        "K5": add["sum_of_halves_equal"] and add["reverse_order_equal"],
        "K6": 2 * numbers["hits"] >= numbers["neighbours"],
        "K7": any(rate >= Fraction(1, 5) and rate >= 10 * chance
                  for rate, chance in ((plural["similar_rate"], plural["similar_chance"]),
                                       (plural["related_rate"], plural["related_chance"]))),
        "K8": 5 * define["answered"] >= 4 * define["terms"],
        "K9": define["nonsense_refused"] == define["terms"],
    }
    amended = {
        "K3'": majority_precision >= Fraction(3, 2) * accuracy
               and majority_coverage >= Fraction(1, 5),
        "K8'": 5 * define_bold["answered"] >= 4 * define_bold["terms"]
               and define_bold["nonsense_refused"] == define_bold["terms"],
    }
    return {
        "corpus": {"documents": len(docs), "sentences": whole.sentences,
                   "tokens": whole.tokens, "vocabulary": len(whole.unigram),
                   "digest": knowledge.digest},
        "prediction": {
            "training_documents": len(train), "held_documents": len(held),
            "held_sentences": held_count, "novel_sentences": len(novel),
            "positions": positions,
            "model": {"right": m["right"], "accuracy": accuracy,
                      "baseline_right": m["baseline_right"],
                      "baseline_accuracy": baseline,
                      "baseline_token": _Rows(model).most_frequent,
                      "guarded_answered": m["guarded_answered"],
                      "guarded_right": m["guarded_right"],
                      "guarded_precision": guarded_precision,
                      "guarded_coverage": guarded_coverage,
                      "majority_answered": m["majority_answered"],
                      "majority_right": m["majority_right"],
                      "majority_precision": majority_precision,
                      "majority_coverage": majority_coverage},
            "control": {"right": c["right"],
                        "accuracy": _ratio(c["right"], c["positions"])},
            "curve": curve,
        },
        "additivity": add,
        "number_words": numbers,
        "plural": plural,
        "define": define,
        "define_bold": define_bold,
        "marks": marks,
        "met": sum(1 for v in marks.values() if v),
        "taken": len(marks),
        "amended": amended,
        "amended_met": sum(1 for v in amended.values() if v),
    }


# ---------------------------------------------------------------------------
#  The stored measurement (written only by ``tools corpus-knowledge --write``)
# ---------------------------------------------------------------------------

def _plain(x: Any) -> Any:
    """Recursive serializer: Fraction -> str, dict/list -> plain."""
    if isinstance(x, Fraction):
        return str(x)
    if isinstance(x, dict):
        return {k: _plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_plain(v) for v in x]
    return x


def module_digest() -> str:
    """The digest of every file in :data:`_SOURCES`."""
    root = _HERE.parent  # glm_universal/
    paths = [root / n for n in sorted(set(_SOURCES))]
    return integrity.tree_digest(paths, root)


def measure() -> Dict[str, object]:
    """``compute()`` plus the ``source_digest``."""
    r = compute()
    r["source_digest"] = module_digest()
    return r


def write_measurements(path: Optional[Path] = None) -> Path:
    """Write ``measure()`` as JSON to :data:`DATA_PATH` (or ``path``)."""
    out = path if path is not None else DATA_PATH
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(_plain(measure()), indent=1, sort_keys=True,
                      ensure_ascii=False) + "\n"
    out.write_text(text, encoding="utf-8")
    global _cache
    _cache = None
    return out


def measurements(refresh: bool = False) -> Optional[Dict[str, object]]:
    """Read the stored measurement from :data:`DATA_PATH`, or ``None``."""
    global _cache
    if _cache is not None and not refresh:
        return _cache
    if not DATA_PATH.exists():
        return None
    try:
        _cache = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        _cache = None
    return _cache


def state() -> Dict[str, object]:
    """``{"present", "fresh", "verdict", "live_digest", "stored_digest"}``."""
    stored = measurements()
    live = module_digest()
    if stored is None:
        return {"present": False, "fresh": False, "verdict": "absent",
                "live_digest": live, "stored_digest": None}
    stored_digest = stored.get("source_digest")
    return {"present": True, "fresh": stored_digest == live,
            "verdict": "current" if stored_digest == live else "stale",
            "live_digest": live, "stored_digest": stored_digest}


def current() -> Optional[Dict[str, object]]:
    """``measurements()`` if fresh, else ``None``."""
    if state()["fresh"]:
        return measurements()
    return None


def corpus_knowledge_report() -> Dict[str, object]:
    """If fresh: the stored measurement with ``available=True``.  Else: why
    not (absent or stale) and the command that re-takes it; the live
    figures are :func:`compute`'s."""
    stored = current()
    if stored is not None:
        out = dict(stored)
        out["available"] = True
        return out
    verdict = state()["verdict"]
    return {
        "available": False,
        "verdict": verdict,
        "reason": (f"the stored measurement is {verdict}; re-take it with "
                   f"python3 -m glm_universal.tools corpus-knowledge --write"),
    }
