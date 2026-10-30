"""``glm_universal.knowledge.model`` -- what the corpus "teaches", as counts.

An LLM is trained by adjusting floating-point weights under a random
initialisation and a random batch order, so the same corpus never gives the
same model twice and no weight can be traced to the text that set it.  This
module is the opposite end of that design space, and the whole of its
"training" is **counting**:

``unigram``
    how often each token occurs;
``ctx1`` / ``ctx2``
    for each one-token (resp. two-token) left context, how often each token
    follows it inside a sentence -- the n-gram tables, with the sentence
    boundaries ``<s>`` and ``</s>`` as tokens;
``df`` / ``folders``
    in how many documents, and in how many top-level folders, each token
    occurs -- the document and folder scales of the hierarchy;
``window``
    for each pair of content words, how often they stand within
    :data:`WINDOW` tokens of each other inside one sentence -- the word's
    natural-language surroundings.

Every entry is an ``int``.  Counting is additive over documents -- the model
of two disjoint collections is the sum of their models -- so a model
"learns as the corpus collects": adding a document is adding its counts, and
the result is *equal* to retraining from nothing (``GLM.CorpusKnowledge``,
``train_append``).  The order documents arrive in cannot change the model
(``train_perm``).  Those two facts are what make an incremental model
trustworthy, and both are tested on the real corpus by :func:`additivity_check`.

Two declared rules shape the counts and are the same for every document:

* a document that repeats a sentence verbatim says it once (the distinct
  sentences of a document are counted, in first-occurrence order);
* the stop-word list :data:`STOPWORDS` decides which tokens are *content*
  words for the ``window`` table; the n-gram tables keep every token.
"""

from __future__ import annotations

import hashlib
import os
import pickle
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, FrozenSet, Iterable, List, Optional, Sequence, Tuple

from . import reader as rd

#: The co-occurrence window, in tokens, either side, inside one sentence.
WINDOW = 4

BOS = "<s>"
EOS = "</s>"

#: Function words: never a content word of the ``window`` table.  A fixed,
#: declared list -- English closed-class words and nothing else.
STOPWORDS: FrozenSet[str] = frozenset("""
a an the and or but nor if then else when while of in on at to for from by with
without into onto over under above below between among through during before
after since until as than so such that this these those there here it its it's
is are was were be been being am do does did done doing have has had having
can could may might must shall should will would not no yes i we you he she they
them us our your his her their my me him what which who whom whose where why how
all any both each every few more most other some only own same too very just also
s t up down out off again further once about against because per via
""".split())


def is_content(token: str) -> bool:
    return token not in STOPWORDS and len(token) > 1


Transform = Callable[[Tuple[str, ...]], Tuple[str, ...]]


def sorted_tokens(toks: Tuple[str, ...]) -> Tuple[str, ...]:
    """The order-destroying control: a sentence's tokens in sorted order.

    It keeps every count of the bag -- the same tokens, the same frequencies,
    the same sentences, documents and folders -- and destroys exactly the
    order of the words, so a measurement that survives it was not carried by
    word order.
    """
    return tuple(sorted(toks))


@dataclass
class Model:
    """The counts.  Every value is an ``int``."""

    documents: int = 0
    sentences: int = 0
    tokens: int = 0
    unigram: Counter = field(default_factory=Counter)
    ctx1: Dict[str, Counter] = field(default_factory=dict)
    ctx2: Dict[Tuple[str, str], Counter] = field(default_factory=dict)
    df: Counter = field(default_factory=Counter)
    folders: Dict[str, set] = field(default_factory=dict)
    window: Counter = field(default_factory=Counter)
    window_pairs: int = 0

    # -- counting ---------------------------------------------------------

    def add_sentence(self, toks: Tuple[str, ...], with_window: bool = True) -> None:
        self.sentences += 1
        self.tokens += len(toks)
        self.unigram.update(toks)
        padded = (BOS, BOS) + toks + (EOS,)
        for i in range(2, len(padded)):
            a, b, c = padded[i - 2], padded[i - 1], padded[i]
            self.ctx1.setdefault(b, Counter())[c] += 1
            self.ctx2.setdefault((a, b), Counter())[c] += 1
        if with_window:
            content = [(i, t) for i, t in enumerate(toks) if is_content(t)]
            for j in range(len(content)):
                pj, tj = content[j]
                for k in range(j + 1, len(content)):
                    pk, tk = content[k]
                    if pk - pj > WINDOW:
                        break
                    if tj == tk:
                        continue
                    key = (tj, tk) if tj < tk else (tk, tj)
                    self.window[key] += 1
                    self.window_pairs += 1

    def add_document(self, document: rd.Document,
                     transform: Optional[Transform] = None,
                     with_window: bool = True) -> None:
        self.documents += 1
        seen = set()
        present = set()
        for sentence in document.sentences:
            toks = sentence.tokens
            if toks in seen:
                continue
            seen.add(toks)
            if transform is not None:
                toks = transform(toks)
            present.update(toks)
            self.add_sentence(toks, with_window)
        self.df.update(present)
        top = rd.top_folder(document.path)
        for t in present:
            self.folders.setdefault(t, set()).add(top)

    # -- the additive structure ----------------------------------------

    def signature(self) -> str:
        """A SHA-256 of every count, in sorted order: equal iff the counts are."""
        h = hashlib.sha256()
        h.update(f"{self.documents},{self.sentences},{self.tokens},"
                 f"{self.window_pairs}".encode())
        for key in sorted(self.unigram):
            h.update(f"u{key}={self.unigram[key]};".encode())
        for b in sorted(self.ctx1):
            row = self.ctx1[b]
            for c in sorted(row):
                h.update(f"1{b}|{c}={row[c]};".encode())
        for ab in sorted(self.ctx2):
            row = self.ctx2[ab]
            for c in sorted(row):
                h.update(f"2{ab[0]} {ab[1]}|{c}={row[c]};".encode())
        for key in sorted(self.df):
            h.update(f"d{key}={self.df[key]};".encode())
        for key in sorted(self.window):
            h.update(f"w{key[0]} {key[1]}={self.window[key]};".encode())
        return h.hexdigest()

    def merge(self, other: "Model") -> "Model":
        """The sum of two models (the counts of the union of their corpora).

        Folder sets are unioned rather than summed: a folder is a set the
        token was seen in, not a count.
        """
        out = Model(documents=self.documents + other.documents,
                    sentences=self.sentences + other.sentences,
                    tokens=self.tokens + other.tokens,
                    unigram=self.unigram + other.unigram,
                    df=self.df + other.df,
                    window=self.window + other.window,
                    window_pairs=self.window_pairs + other.window_pairs)
        for src in (self.ctx1, other.ctx1):
            for k, row in src.items():
                out.ctx1.setdefault(k, Counter()).update(row)
        for src in (self.ctx2, other.ctx2):
            for k, row in src.items():
                out.ctx2.setdefault(k, Counter()).update(row)
        for src in (self.folders, other.folders):
            for k, tops in src.items():
                out.folders.setdefault(k, set()).update(tops)
        return out


def train(documents: Iterable[rd.Document], transform: Optional[Transform] = None,
          with_window: bool = True) -> Model:
    """Count ``documents``.  Deterministic: the same documents, the same model."""
    model = Model()
    for document in documents:
        model.add_document(document, transform, with_window)
    return model


# ---------------------------------------------------------------------------
#  The association rule, and the associated-context sets
# ---------------------------------------------------------------------------

def associated(model: Model, a: str, b: str) -> bool:
    """Do ``a`` and ``b`` stand together more often than their counts predict?

    Exactly ``n(a,b) * T**2 > n(a) * n(b) * P`` -- the lift of the pair
    against independence, compared in integers (``T`` the tokens, ``P`` the
    window pairs).  No logarithm and no float: the comparison is what the
    pointwise mutual information is positive *means*.
    """
    key = (a, b) if a < b else (b, a)
    n_ab = model.window.get(key, 0)
    return n_ab * model.tokens * model.tokens > \
        model.unigram[a] * model.unigram[b] * model.window_pairs


#: A context counts towards a word's associated set only with this support.
MIN_PAIR = 2

#: Words rarer than this get no associated set (too little to read from).
MIN_WORD = 10


def context_sets(model: Model) -> Dict[str, FrozenSet[str]]:
    """For every content word seen :data:`MIN_WORD` times, its associated contexts."""
    sets: Dict[str, set] = {}
    t2 = model.tokens * model.tokens
    pairs = model.window_pairs
    uni = model.unigram
    for (a, b), n in model.window.items():
        if n < MIN_PAIR:
            continue
        if uni[a] < MIN_WORD or uni[b] < MIN_WORD:
            continue
        if n * t2 > uni[a] * uni[b] * pairs:
            sets.setdefault(a, set()).add(b)
            sets.setdefault(b, set()).add(a)
    return {w: frozenset(s) for w, s in sets.items()}


def positional_sets(model: Model) -> Dict[str, FrozenSet[str]]:
    """For every word seen :data:`MIN_WORD` times, its associated neighbours.

    The features are the token directly before (``"<u"``) and directly after
    (``">v"``) the word, stop words and sentence boundaries included, kept
    when the bigram is seen :data:`MIN_PAIR` times and more often than
    independence predicts: ``n(u,w) * T > n(u) * n(w)``.  Two words with
    many such features in common are *used alike* -- they fill the same slot
    of the same phrases -- which is a different relation from standing near
    each other, and the one :func:`glm_universal.knowledge.answer.similar`
    reads.
    """
    uni = Counter(model.unigram)
    uni[BOS] = model.sentences
    uni[EOS] = model.sentences
    total = model.tokens
    sets: Dict[str, set] = {}
    for b, row in model.ctx1.items():
        if uni[b] < MIN_WORD:
            continue
        for c, n in row.items():
            if n < MIN_PAIR or uni[c] < MIN_WORD:
                continue
            if n * total > uni[b] * uni[c]:
                if c != EOS:
                    sets.setdefault(c, set()).add("<" + b)
                if b != BOS:
                    sets.setdefault(b, set()).add(">" + c)
    return {w: frozenset(f) for w, f in sets.items()}


# ---------------------------------------------------------------------------
#  The cache: the corpus read once per file digest, the model once per corpus
# ---------------------------------------------------------------------------

#: Where the cache lives.  Beside this module by default; the environment
#: variable ``GLM_KNOWLEDGE_CACHE`` moves it (outside the working tree, say,
#: or onto a faster disk).  Either way it is *derived* and never version
#: controlled: the whole directory is listed in the repository's
#: ``.gitignore``, because the counted model is about 135 MB and is rewritten
#: whenever any corpus file moves -- tracked, each rewritten copy made a push
#: too large for the git server (22 October 2026).  A clone therefore starts
#: without it, and :func:`load` counts the corpus once (about a minute).
CACHE_ENVIRONMENT = "GLM_KNOWLEDGE_CACHE"
DEFAULT_CACHE_DIRECTORY = Path(__file__).resolve().parent / "_knowledge_cache"


def cache_directory(environ=os.environ) -> Path:
    """The cache directory an environment names (the default when it names none)."""
    named = environ.get(CACHE_ENVIRONMENT)
    return Path(named).expanduser().resolve() if named else DEFAULT_CACHE_DIRECTORY


CACHE_DIRECTORY = cache_directory()
CACHE_FILE = "knowledge.pickle"
CACHE_SCHEMA = 4


def _file_digests() -> Dict[str, str]:
    return {path: hashlib.sha256(data).hexdigest() for path, data in rd.iter_sources()}


def corpus_digest(digests: Dict[str, str]) -> str:
    h = hashlib.sha256(f"schema={CACHE_SCHEMA};".encode())
    for path in sorted(digests):
        h.update(f"{path}={digests[path]};".encode())
    return h.hexdigest()


@dataclass
class Knowledge:
    """The corpus and its model, loaded together."""

    digest: str
    documents: Tuple[rd.Document, ...]
    model: Model
    contexts: Dict[str, FrozenSet[str]]
    positions: Dict[str, FrozenSet[str]]
    postings: Dict[str, Tuple[int, ...]]   # token -> sentence ids
    sentences: Tuple[rd.Sentence, ...]
    reread: int = 0                         # documents re-read on this load

    def sentence_ids(self, token: str) -> Tuple[int, ...]:
        return self.postings.get(token, ())


def _postings(sentences: Sequence[rd.Sentence]) -> Dict[str, Tuple[int, ...]]:
    acc: Dict[str, List[int]] = {}
    for sid, s in enumerate(sentences):
        for t in set(s.tokens):
            acc.setdefault(t, []).append(sid)
    return {t: tuple(ids) for t, ids in acc.items()}


def _read_documents_incremental(previous: Dict[str, rd.Document]
                                ) -> Tuple[Tuple[rd.Document, ...], int, Dict[str, str]]:
    out: List[rd.Document] = []
    digests: Dict[str, str] = {}
    reread = 0
    for path, data in rd.iter_sources():
        digest = hashlib.sha256(data).hexdigest()
        digests[path] = digest
        old = previous.get(path)
        if old is not None and old.digest == digest:
            document: Optional[rd.Document] = old
        else:
            reread += 1
            document = rd.read_bytes(path, data)
        if document is not None and document.sentences:
            out.append(document)
    return tuple(out), reread, digests


_LOADED: Dict[str, Knowledge] = {}


def load(rebuild: bool = False) -> Knowledge:
    """The corpus knowledge, current with the files on disk.

    Re-reads only the files whose digest moved since the cached reading
    (the corpus *collects*: a new study is one file read and counted), then
    re-counts.  The cache lives in ``_knowledge_cache/`` beside this module
    and is never read by the corpus walk itself.
    """
    if not rebuild and "current" in _LOADED:
        return _LOADED["current"]
    CACHE_DIRECTORY.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIRECTORY / CACHE_FILE
    if not path.exists() and not rebuild:
        _announce_cold_start(path)
    previous: Dict[str, rd.Document] = {}
    cached: Optional[Knowledge] = None
    if path.exists() and not rebuild:
        try:
            with path.open("rb") as handle:
                cached = pickle.load(handle)
        except Exception:  # pragma: no cover - a corrupt cache is rebuilt
            cached = None
    if cached is not None:
        digest = corpus_digest(_file_digests())
        if cached.digest == digest:
            cached.reread = 0
            _LOADED["current"] = cached
            return cached
        previous = {d.path: d for d in cached.documents}
    documents, reread, digests = _read_documents_incremental(previous)
    digest = corpus_digest(digests)
    knowledge = build(documents, digest)
    knowledge.reread = reread
    # Written beside the target and renamed into place, so a reader in
    # another process never sees half a cache.
    partial = path.with_name(f"{path.name}.{os.getpid()}.partial")
    with partial.open("wb") as handle:
        pickle.dump(knowledge, handle, protocol=pickle.HIGHEST_PROTOCOL)
    os.replace(partial, path)
    _LOADED["current"] = knowledge
    return knowledge


def _announce_cold_start(path: Path) -> None:
    """Say once, on a terminal, why the first reading takes a minute.

    A fresh clone has no cache (it is not version controlled), so the first
    call reads and counts every corpus file.  The notice goes to standard
    error and only when that is a terminal, so no piped output, test capture
    or CLI answer ever changes because a cache was absent.
    """
    if sys.stderr is not None and sys.stderr.isatty():
        print(f"glm: no knowledge cache at {path}; reading and counting the "
              f"corpus once (about a minute) -- later readings load the cache",
              file=sys.stderr, flush=True)


def cache_state() -> Dict[str, object]:
    """Whether the on-disk cache is present, and how large.

    Reading the cache's digest needs the cache loaded; this reports what a
    caller can know cheaply (presence and size) and leaves currency to
    :func:`load`, which re-reads only the files that moved.
    """
    path = CACHE_DIRECTORY / CACHE_FILE
    present = path.exists()
    size = path.stat().st_size if present else 0
    return {"path": str(path), "present": present, "bytes": size,
            "directory": str(CACHE_DIRECTORY),
            "relocated": CACHE_DIRECTORY != DEFAULT_CACHE_DIRECTORY,
            "verdict": (f"present ({size // 1_000_000} MB)" if present
                        else "absent -- the next reading counts the corpus once")}


def build(documents: Tuple[rd.Document, ...], digest: str = "") -> Knowledge:
    model = train(documents)
    sentences = tuple(s for d in documents for s in d.sentences)
    return Knowledge(digest=digest, documents=documents, model=model,
                     contexts=context_sets(model),
                     positions=positional_sets(model), postings=_postings(sentences),
                     sentences=sentences)
