"""``glm_universal.corpus.study_index`` -- the studies, as something the GLM
can reason over.

Every study has a manifest (``studies/*.yaml``, schema
``glm-study-manifest/v1``) derived from its prose and the tree by
:mod:`glm_universal.corpus.study_manifest`.  This module loads all of them
(through the one loader the study ledger also uses,
:func:`study_manifest.load_manifests`) and answers structured questions over
them, with nothing stored beside them:

* which studies bear on a term (ranked by where the term occurs: id, title,
  question, verdict, deciding figure, section headings, cited files);
* which studies cite a code module, a Lean file or a test;
* a study's predecessors and successors (and their transitive closure), the
  other studies it links to, its follow-ups and its marks met or missed;
* the studies whose Lean file is missing or held back from the build;
* the open studies (status ``open``, or a follow-up still ``open``);
* studies by phase, by directive, by faculty.

:func:`answer_study_query` reads a question in words ("which studies bear on
the Golay code", "study LORENTZIAN_MAJORITY_STUDY", "what does
FOLD_MACHINE_STUDY depend on") and returns ``(exit_code, reply)``: ``0`` when
it answered, ``1`` when nothing in the manifests answers it (an unknown
study, or no study bears on the term -- said in words, never guessed), ``2``
when the question is empty.

Command line::

    PYTHONPATH=src python3 -m glm_universal.corpus.study_index "golay"
    PYTHONPATH=src python3 -m glm_universal.corpus.study_index \\
        "what does FOLD_MACHINE_STUDY depend on"
    PYTHONPATH=src python3 -m glm_universal.corpus.study_index --json "golay"

*Created 31 October 2026 (repository check of the YAML study system).*
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, \
    Set, Tuple

from . import study_manifest as sm

__all__ = [
    "StudyIndex",
    "Hit",
    "study_index",
    "answer_study_query",
    "main",
]

#: Words a term search ignores.
_STOP = frozenset("""
a an the of on in to for and or by with from at as is are was were be been
which what who whom whose how why when where that this these those it its
study studies document documents bear bears bearing on about concern concerns
concerning mention mentions cite cites use uses used any all some do does did
me tell show find list give glm say says
""".split())

#: Field weights for the term search: a term in the title or the id is the
#: study's subject; in a cited file name, a strong pointer; in the verdict or
#: a heading, what it found or covers; in the deciding figure, a mention.
_WEIGHTS: Tuple[Tuple[str, int], ...] = (
    ("id", 5), ("title", 5), ("question", 3), ("files", 3),
    ("verdict", 2), ("headings", 2), ("figure", 1),
)

_WORD = re.compile(r"[a-z0-9][a-z0-9'-]*")


def _words(text: str) -> List[str]:
    return [w.strip("'-") for w in _WORD.findall(text.lower()) if w.strip("'-")]


def _matches(query_word: str, token: str) -> bool:
    if token == query_word:
        return True
    if len(query_word) >= 4 and len(token) >= 4:
        shorter, longer = sorted((query_word, token), key=len)
        return longer.startswith(shorter) and len(longer) - len(shorter) <= 3
    return False


@dataclass(frozen=True)
class Hit:
    """One study found by a term search."""

    sid: str
    score: int
    fields: Tuple[str, ...]
    matched: int = 0      # how many of the term's content words it holds
    of: int = 0           # how many content words the term has


class StudyIndex:
    """All study manifests, and the questions they answer."""

    def __init__(self, manifests: Optional[Mapping[str, Mapping[str, Any]]]
                 = None) -> None:
        self.manifests: Dict[str, Mapping[str, Any]] = dict(
            manifests if manifests is not None else sm.load_manifests())
        self._tokens: Dict[str, Dict[str, Set[str]]] = {}
        self._succ: Dict[str, List[str]] = {sid: [] for sid in self.manifests}
        for sid, data in self.manifests.items():
            for pred in data.get("predecessors") or []:
                if pred in self._succ:
                    self._succ[pred].append(sid)
        for sid in self._succ:
            self._succ[sid].sort()

    # ---------------------------------------------------------- lookup
    @property
    def ids(self) -> List[str]:
        return sorted(self.manifests)

    def get(self, sid: str) -> Optional[Mapping[str, Any]]:
        return self.manifests.get(sid)

    def resolve(self, text: str) -> Optional[str]:
        """The study id a phrase names, or ``None``: ``FOLD_MACHINE_STUDY``,
        ``fold machine``, ``the fold machine study``, ``FOLD_MACHINE_STUDY.md``."""
        raw = text.strip().strip("`'\"?.!").strip()
        raw = re.sub(r"^(?:studies/)", "", raw)
        raw = re.sub(r"\.(?:md|yaml)$", "", raw)
        if raw in self.manifests:
            return raw
        words = [w for w in re.split(r"[\s_\-]+", raw) if w]
        while words and words[0].lower() in ("the", "a", "an"):
            words = words[1:]
        candidates = []
        if words:
            joined = "_".join(words).upper()
            candidates = [joined, joined + "_STUDY"]
            if joined.endswith("_STUDY"):
                candidates.append(joined)
        upper = {sid.upper(): sid for sid in self.manifests}
        for candidate in candidates:
            if candidate in upper:
                return upper[candidate]
        return None

    # ---------------------------------------------------------- search
    def _fields(self, sid: str) -> Dict[str, Set[str]]:
        cached = self._tokens.get(sid)
        if cached is not None:
            return cached
        data = self.manifests[sid]
        refs = data.get("file_refs") or {}
        files: List[str] = []
        for kind in ("code", "test", "lean", "lean_missing"):
            for ref in refs.get(kind) or []:
                files.append(re.sub(r"[/_.]", " ", str(ref)))
                files.append(re.sub(r"(?<=[a-z])(?=[A-Z])", " ", str(ref)))
        out = {
            "id": set(_words(sid.replace("_", " "))),
            "title": set(_words(str(data.get("title", "")))),
            "question": set(_words(str(data.get("question", "")))),
            "verdict": set(_words(str(data.get("verdict", "")))),
            "figure": set(_words(str(data.get("deciding_figure", "")))),
            "headings": set(_words(" ".join(
                str(s.get("heading", "")) for s in data.get("sections") or []
                if isinstance(s, Mapping)))),
            "files": set(_words(" ".join(files))),
        }
        self._tokens[sid] = out
        return out

    def bearing_on(self, term: str, limit: Optional[int] = None) -> List[Hit]:
        """The studies that bear on a term, best first.

        Every content word of the term must occur in the study's manifest
        (a word matches the same word or one differing by a short suffix,
        ``code``/``codes``); when no study holds them all, the studies holding
        the most of them are returned.  Ties are broken by id.
        """
        query = [w for w in _words(term) if w not in _STOP]
        if not query:
            return []
        scored: List[Tuple[int, int, str, Tuple[str, ...]]] = []
        for sid in self.ids:
            fields = self._fields(sid)
            matched = 0
            score = 0
            where: List[str] = []
            for word in query:
                best = 0
                best_field = ""
                for name, weight in _WEIGHTS:
                    if any(_matches(word, tok) for tok in fields[name]):
                        if weight > best:
                            best, best_field = weight, name
                if best:
                    matched += 1
                    score += best
                    if best_field not in where:
                        where.append(best_field)
            if matched:
                scored.append((matched, score, sid, tuple(where)))
        if not scored:
            return []
        top = max(m for m, _s, _i, _w in scored)
        hits = [Hit(sid, score, where, m, len(query))
                for m, score, sid, where in scored if m == top]
        hits.sort(key=lambda h: (-h.score, h.sid))
        return hits[:limit] if limit else hits

    # ---------------------------------------------------------- files
    @staticmethod
    def _norm_file(name: str) -> str:
        text = name.strip().strip("`")
        for prefix in ("src/glm_universal/", "glm_universal/", "src/lean/",
                       "RequestProject/GLM/", "awaiting_recovery/"):
            if text.startswith(prefix):
                text = text[len(prefix):]
        if text.startswith("glm_universal."):
            text = text[len("glm_universal."):].replace(".", "/")
        return text

    def by_code(self, name: str) -> List[str]:
        """Studies citing a code module (``reasoning/leech_shells.py``,
        ``leech_shells``, ``glm_universal.reasoning.leech_shells``)."""
        key = self._norm_file(name)
        key_py = key if key.endswith(".py") else key + ".py"
        out = []
        for sid in self.ids:
            refs = self.manifests[sid].get("file_refs") or {}
            for ref in (refs.get("code") or []) + (refs.get("missing") or []):
                if ref == key_py or ref.endswith("/" + key_py):
                    out.append(sid)
                    break
        return out

    def by_lean(self, name: str) -> List[str]:
        """Studies citing a Lean file, present, held or missing
        (``LeechShells``, ``LeechShells.lean``, ``Rule30/Basic``)."""
        key = self._norm_file(name)
        if key.endswith(".lean"):
            key = key[:-len(".lean")]
        key = key.replace("RequestProject.GLM.", "").replace(".", "/")
        out = []
        for sid in self.ids:
            refs = self.manifests[sid].get("file_refs") or {}
            for ref in (refs.get("lean") or []) + (refs.get("lean_missing") or []):
                if ref == key or ref.rsplit("/", 1)[-1] == key:
                    out.append(sid)
                    break
        return out

    def by_test(self, name: str) -> List[str]:
        """Studies citing a test file (``test_leech_shells.py``)."""
        key = self._norm_file(name).rsplit("/", 1)[-1]
        if not key.endswith(".py"):
            key += ".py"
        out = []
        for sid in self.ids:
            refs = self.manifests[sid].get("file_refs") or {}
            tests = list(refs.get("test") or []) + [
                m.rsplit("/", 1)[-1] for m in refs.get("missing") or []
                if m.startswith("tests/")]
            if key in tests:
                out.append(sid)
        return out

    # ---------------------------------------------------------- graph
    def predecessors(self, sid: str) -> List[str]:
        return sorted(self.manifests.get(sid, {}).get("predecessors") or [])

    def successors(self, sid: str) -> List[str]:
        return list(self._succ.get(sid, []))

    def related(self, sid: str) -> List[str]:
        return sorted(self.manifests.get(sid, {}).get("related") or [])

    def _closure(self, sid: str, step) -> List[str]:
        seen: Set[str] = set()
        stack = list(step(sid))
        while stack:
            current = stack.pop()
            if current in seen or current == sid:
                continue
            seen.add(current)
            stack.extend(step(current))
        return sorted(seen)

    def ancestors(self, sid: str) -> List[str]:
        return self._closure(sid, self.predecessors)

    def descendants(self, sid: str) -> List[str]:
        return self._closure(sid, self.successors)

    # ---------------------------------------------------------- facts
    def marks(self, sid: str) -> Dict[str, List[str]]:
        marks = self.manifests.get(sid, {}).get("marks") or {}
        return {k: list(marks.get(k) or []) for k in
                ("declared", "met", "missed", "amended")}

    def follow_ups(self, sid: str) -> List[Mapping[str, Any]]:
        return list(self.manifests.get(sid, {}).get("follow_ups") or [])

    def lean_gaps(self) -> List[Tuple[str, str, str]]:
        """``(study, lean file, "missing"|"held")`` for every study whose
        cited Lean file is missing from the repository or held back."""
        out: List[Tuple[str, str, str]] = []
        for sid in self.ids:
            refs = self.manifests[sid].get("file_refs") or {}
            for ref in refs.get("lean_missing") or []:
                out.append((sid, ref, "missing"))
            for ref in refs.get("lean_held") or []:
                out.append((sid, ref, "held"))
        return out

    def open_studies(self) -> List[Tuple[str, str]]:
        """``(study, why)`` for each study still open: status ``open``, or a
        follow-up recorded as ``open``."""
        out: List[Tuple[str, str]] = []
        for sid in self.ids:
            data = self.manifests[sid]
            if data.get("status") == "open":
                out.append((sid, "status open"))
                continue
            pending = [f for f in data.get("follow_ups") or []
                       if isinstance(f, Mapping) and f.get("status") == "open"]
            if pending:
                out.append((sid, f"{len(pending)} open follow-up(s)"))
        return out

    def by_phase(self, phase: int) -> List[str]:
        return [sid for sid in self.ids
                if self.manifests[sid].get("phase") == phase]

    def by_directive(self, directive: str) -> List[str]:
        key = directive.upper()
        return [sid for sid in self.ids
                if key in (self.manifests[sid].get("directives") or [])]

    def by_faculty(self, faculty: str) -> List[str]:
        return [sid for sid in self.ids
                if self.manifests[sid].get("faculty") == faculty]

    def by_status(self, status: str) -> List[str]:
        return [sid for sid in self.ids
                if self.manifests[sid].get("status") == status]

    # ---------------------------------------------------------- render
    def label(self, sid: str) -> str:
        data = self.manifests.get(sid, {})
        phase = data.get("phase") or 0
        title = str(data.get("title", ""))
        return (f"{sid} (Phase {phase})" if phase else sid) + (
            f" — {title}" if title else "")

    def card(self, sid: str) -> str:
        """Everything the manifest says about one study, in words."""
        data = self.manifests[sid]
        refs = data.get("file_refs") or {}
        marks = self.marks(sid)
        lines = [self.label(sid)]
        facts = [f"phase {data.get('phase') or 'unknown'}",
                 f"status {data.get('status', 'unknown')}",
                 f"faculty {data.get('faculty', 'unknown')}"]
        if data.get("last_altered"):
            facts.append(f"last altered {data['last_altered']}")
        lines.append("; ".join(facts))
        for label, key in (("Question", "question"), ("Verdict", "verdict"),
                           ("Deciding figure", "deciding_figure"),
                           ("Recomputed by", "recomputed_by")):
            if data.get(key):
                lines.append(f"{label}: {data[key]}")
        if marks["declared"] or marks["amended"]:
            text = (f"Marks: {len(marks['declared'])} declared"
                    f" ({', '.join(marks['declared'])})")
            text += f"; met {len(marks['met'])}"
            if marks["missed"]:
                text += f"; missed {', '.join(marks['missed'])}"
            if marks["amended"]:
                text += f"; amended {', '.join(marks['amended'])}"
            lines.append(text)
        for label, items in (("Builds on", self.predecessors(sid)),
                             ("Built on by", self.successors(sid)),
                             ("Also links to", self.related(sid))):
            if items:
                lines.append(f"{label}: {', '.join(items)}")
        for label, key in (("Code", "code"), ("Tests", "test"),
                           ("Lean", "lean"), ("Lean held", "lean_held"),
                           ("Lean missing", "lean_missing"),
                           ("Cited but missing", "missing")):
            items = refs.get(key) or []
            if items:
                lines.append(f"{label}: {', '.join(items)}")
        if data.get("directives"):
            lines.append(f"Directives: {', '.join(data['directives'])}")
        for follow in self.follow_ups(sid):
            if isinstance(follow, Mapping) and follow.get("question"):
                lines.append(f"Follow-up ({follow.get('status', 'open')}): "
                             f"{follow['question']}")
        lines.append(f"Prose: studies/{refs.get('prose', sid + '.md')}")
        return "\n".join(lines)


def study_index() -> StudyIndex:
    """A fresh index over the manifests as they are now (the loader caches
    parsed files on their modification times, so this is cheap)."""
    return StudyIndex(sm.load_manifests())


# ===========================================================================
# Questions in words
# ===========================================================================

_PRED_PATTERNS = (
    re.compile(r"\bwhat (?:does|did) (?P<s>.+?) (?:depend|build|rest|draw|rely) on\b"),
    re.compile(r"\b(?:predecessors?|ancestors?|prerequisites?) (?:of|for) (?P<s>.+)"),
    re.compile(r"\bwhat (?:comes|came) before (?P<s>.+)"),
    re.compile(r"\bwhat (?:does|did) (?P<s>.+?) (?:need|follow|build upon)\b"),
)
_SUCC_PATTERNS = (
    re.compile(r"\b(?:what|which studies?) (?:depends?|builds?|rests?|relies?) "
               r"on (?P<s>.+)"),
    re.compile(r"\b(?:successors?|descendants?) (?:of|to) (?P<s>.+)"),
    re.compile(r"\bwhat (?:comes|came) after (?P<s>.+)"),
    re.compile(r"\b(?:what|which studies?) (?:follows?|followed) (?P<s>.+)"),
)
_MARK_PATTERNS = (
    re.compile(r"\bmarks? (?:of|for|in) (?P<s>.+)"),
    re.compile(r"\bwhich marks? (?:did|does) (?P<s>.+?) (?:miss|meet|make)\b"),
    re.compile(r"\b(?:what|which) (?:did|does) (?P<s>.+?) (?:miss|meet)\b"),
)
_FOLLOW_PATTERNS = (
    re.compile(r"\bfollow[- ]?ups? (?:of|for|from|to) (?P<s>.+)"),
    re.compile(r"\bwhat (?:did|does) (?P<s>.+?) leave(?: open)?\b"),
)
_CARD_PATTERNS = (
    re.compile(r"^(?:study|show|card|describe|summari[sz]e|tell me about|"
               r"what is|what was|what did) (?P<s>.+?)(?: say| find| conclude)?$"),
)
_BEARING_PATTERNS = (
    re.compile(r"\b(?:which|what) (?:studies )?(?:bear|bears|bearing) on (?P<t>.+)"),
    re.compile(r"\b(?:which|what) studies (?:are about|concern|mention|cite|use|"
               r"touch|cover|discuss|involve) (?P<t>.+)"),
    re.compile(r"\bstudies (?:on|about|of|for|concerning|citing|using) (?P<t>.+)"),
)


def _clean_subject(text: str) -> str:
    return text.strip().strip("?.!").strip()


def _list_reply(head: str, sids: Sequence[str], idx: StudyIndex,
                empty: str) -> Tuple[int, str]:
    if not sids:
        return 1, empty
    lines = [f"{head} ({len(sids)}):"]
    lines.extend(f"  {idx.label(sid)}" for sid in sids)
    return 0, "\n".join(lines)


def _unknown(subject: str) -> Tuple[int, str]:
    return 1, (f"no study is named {subject!r}: the study manifests hold no "
               f"such id (try a term search: \"which studies bear on ...\")")


def _file_query(text: str, idx: StudyIndex) -> Optional[Tuple[int, str]]:
    lean = re.search(r"([A-Za-z0-9_/.]+\.lean)\b", text) or re.search(
        r"\blean (?:file|module) `?([A-Za-z0-9_/.]+)`?", text, re.I)
    if lean:
        name = lean.group(1)
        sids = idx.by_lean(name)
        return _list_reply(f"studies citing the Lean file {name}", sids, idx,
                           f"no study manifest cites the Lean file {name}")
    test = re.search(r"\b(test_[A-Za-z0-9_]+(?:\.py)?)\b", text)
    if test:
        name = test.group(1)
        sids = idx.by_test(name)
        return _list_reply(f"studies citing the test {name}", sids, idx,
                           f"no study manifest cites the test {name}")
    code = re.search(r"((?:[A-Za-z0-9_]+/)*[A-Za-z0-9_]+\.py)\b", text) or \
        re.search(r"\b(glm_universal(?:\.[A-Za-z0-9_]+)+)", text) or \
        re.search(r"\b(?:module|code) `?([A-Za-z0-9_/.]+)`?", text, re.I)
    if code:
        name = code.group(1)
        sids = idx.by_code(name)
        return _list_reply(f"studies citing the module {name}", sids, idx,
                           f"no study manifest cites the module {name}")
    return None


def _bearing_reply(term: str, idx: StudyIndex) -> Tuple[int, str]:
    #  A term that is itself a file name is answered from the file references.
    if re.fullmatch(r"[A-Za-z0-9_/.]+\.(?:py|lean)", term.strip("` ")):
        found = _file_query(term, idx)
        if found is not None:
            return found
    hits = idx.bearing_on(term)
    words = [w for w in _words(term) if w not in _STOP]
    if not hits:
        return 1, (f"no study manifest bears on {term!r}: none of "
                   f"{', '.join(words) or 'its words'} occurs in any study's "
                   f"id, title, question, verdict, figure, headings or cited "
                   f"files")
    shown = hits[:15]
    partial = hits[0].matched < hits[0].of
    if partial:
        lines = [f"no study manifest holds all of {', '.join(words)}; "
                 f"{len(hits)} hold {hits[0].matched} of {hits[0].of} "
                 f"(ranked by where the words occur):"]
    else:
        lines = [f"{len(hits)} stud{'y bears' if len(hits) == 1 else 'ies bear'}"
                 f" on {term!r} (ranked by where the words occur):"]
    for hit in shown:
        lines.append(f"  {idx.label(hit.sid)}  [{', '.join(hit.fields)}]")
    if len(hits) > len(shown):
        lines.append(f"  ... and {len(hits) - len(shown)} more")
    #  Fewer than half the words found is not an answer, only a lead.
    code = 1 if partial and hits[0].matched * 2 < hits[0].of else 0
    return code, "\n".join(lines)


def answer_study_query(text: str, index: Optional[StudyIndex] = None
                       ) -> Tuple[int, str]:
    """Answer a question about the studies from their manifests.

    Returns ``(exit_code, reply)``: ``0`` answered, ``1`` nothing in the
    manifests answers it (said in the reply), ``2`` an empty question.
    """
    question = (text or "").strip()
    if not question:
        return 2, ("ask about the studies: \"which studies bear on the Golay "
                   "code\", \"study LEECH_SHELLS_STUDY\", \"what does "
                   "FOLD_MACHINE_STUDY depend on\", \"which studies have a "
                   "missing Lean file\", \"open studies\"")
    idx = index if index is not None else study_index()
    lowered = re.sub(r"\s+", " ", question.lower()).strip().rstrip("?.!")
    # A bare study id (or a phrase that is exactly one).
    direct = idx.resolve(question)
    if direct is not None:
        return 0, idx.card(direct)
    # The Lean gaps.
    if re.search(r"(missing|held|lost|absent|awaiting).{0,40}\blean\b|"
                 r"\blean\b.{0,40}(missing|held|lost|absent|awaiting)", lowered):
        gaps = idx.lean_gaps()
        if "held" in lowered and "missing" not in lowered:
            gaps = [g for g in gaps if g[2] == "held"]
        elif ("missing" in lowered or "lost" in lowered) and "held" not in lowered:
            gaps = [g for g in gaps if g[2] == "missing"]
        if not gaps:
            return 1, "no study cites a Lean file that is missing or held"
        lines = [f"{len(gaps)} citation(s) of a Lean file missing or held:"]
        for sid, ref, state in gaps:
            lines.append(f"  {sid}: {ref}.lean ({state})")
        return 0, "\n".join(lines)
    # Open studies.
    if re.search(r"\bopen (?:studies|study|questions?|follow[- ]?ups?)\b|"
                 r"\bstudies (?:still |that are )?open\b|\bwhich studies are open",
                 lowered):
        rows = idx.open_studies()
        if not rows:
            return 0, ("no study is open: every manifest's status is closed or "
                       "negative, and no follow-up is recorded as open")
        lines = [f"{len(rows)} open:"]
        lines.extend(f"  {idx.label(sid)} ({why})" for sid, why in rows)
        return 0, "\n".join(lines)
    # Graph questions.
    for patterns, kind in ((_PRED_PATTERNS, "pred"), (_SUCC_PATTERNS, "succ"),
                           (_MARK_PATTERNS, "marks"),
                           (_FOLLOW_PATTERNS, "follow")):
        for pattern in patterns:
            match = pattern.search(lowered)
            if not match:
                continue
            start, end = match.span("s")
            subject = _clean_subject(question[start:end])
            sid = idx.resolve(subject)
            if sid is None:
                continue
            if kind == "pred":
                preds = idx.predecessors(sid)
                anc = idx.ancestors(sid)
                lines = [f"{sid} builds on {len(preds)} stud"
                         f"{'y' if len(preds) == 1 else 'ies'} (the studies it "
                         f"links to that come from an earlier phase):"]
                lines.extend(f"  {idx.label(p)}" for p in preds)
                if len(anc) > len(preds):
                    lines.append(f"and, through them, {len(anc)} in all.")
                related = idx.related(sid)
                if related:
                    lines.append(f"It also links to: {', '.join(related)}")
                if not preds:
                    lines[0] = (f"{sid} builds on no earlier study"
                                + (" (its phase is unknown, so its links are "
                                   "not ordered)"
                                   if not idx.get(sid).get("phase") else ""))
                return 0, "\n".join(lines)
            if kind == "succ":
                succ = idx.successors(sid)
                desc = idx.descendants(sid)
                if not succ:
                    return 0, f"no later study builds on {sid}"
                lines = [f"{len(succ)} later stud"
                         f"{'y builds' if len(succ) == 1 else 'ies build'} on "
                         f"{sid}:"]
                lines.extend(f"  {idx.label(s)}" for s in succ)
                if len(desc) > len(succ):
                    lines.append(f"and, through them, {len(desc)} in all.")
                return 0, "\n".join(lines)
            if kind == "marks":
                marks = idx.marks(sid)
                if not marks["declared"] and not marks["amended"]:
                    return 1, (f"{sid} tabulates no marks the manifest could "
                               f"read; its deciding figure says: "
                               f"{idx.get(sid).get('deciding_figure', '')}")
                lines = [f"{sid}: {len(marks['declared'])} marks declared "
                         f"({', '.join(marks['declared'])})",
                         f"  met: {', '.join(marks['met']) or 'none read'}",
                         f"  missed: {', '.join(marks['missed']) or 'none'}"]
                if marks["amended"]:
                    lines.append(f"  amended: {', '.join(marks['amended'])}")
                unread = [m for m in marks["declared"]
                          if m not in marks["met"] and m not in marks["missed"]]
                if unread:
                    lines.append(f"  outcome not read from the prose: "
                                 f"{', '.join(unread)}")
                lines.append(f"  deciding figure: "
                             f"{idx.get(sid).get('deciding_figure', '')}")
                return 0, "\n".join(lines)
            follows = idx.follow_ups(sid)
            if not follows:
                return 1, (f"{sid}'s manifest records no follow-ups (the prose "
                           f"may list what it left; see "
                           f"studies/{sid}.md)")
            lines = [f"{sid}: {len(follows)} follow-up(s):"]
            for follow in follows:
                if isinstance(follow, Mapping):
                    lines.append(f"  [{follow.get('status', 'open')}] "
                                 f"{follow.get('question', '')}")
            return 0, "\n".join(lines)
    # Phase and directive lists.
    phase = re.fullmatch(r"(?:which )?(?:studies (?:of|in|from) )?phase (\d+)", lowered)
    if phase:
        number = int(phase.group(1))
        return _list_reply(f"studies of Phase {number}", idx.by_phase(number),
                           idx, f"no study manifest records Phase {number}")
    directive = re.search(r"\bdirective (d\d{1,2})\b|\b(d\d{1,2})\b.*\bdirective",
                          lowered)
    if directive:
        name = (directive.group(1) or directive.group(2)).upper()
        return _list_reply(f"studies citing directive {name}",
                           idx.by_directive(name), idx,
                           f"no study manifest cites directive {name}")
    # "study X" / "what is X".
    for pattern in _CARD_PATTERNS:
        match = pattern.search(lowered)
        if match:
            start, end = match.span("s")
            subject = _clean_subject(question[start:end])
            sid = idx.resolve(subject)
            if sid is not None:
                return 0, idx.card(sid)
            if lowered.startswith("study "):
                return _unknown(subject)
    # File references.
    found = _file_query(question, idx)
    if found is not None:
        return found
    # "which studies bear on T".
    for pattern in _BEARING_PATTERNS:
        match = pattern.search(lowered)
        if match:
            start, end = match.span("t")
            return _bearing_reply(_clean_subject(question[start:end]), idx)
    return _bearing_reply(question, idx)


# ===========================================================================
# Command line
# ===========================================================================

def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python3 -m glm_universal.corpus.study_index",
        description="Answer a question about the studies from their YAML "
                    "manifests.")
    parser.add_argument("question", nargs="*",
                        help="a term, a study id, or a question in words")
    parser.add_argument("--json", action="store_true",
                        help="print the manifest(s) the answer names as JSON")
    args = parser.parse_args(argv)
    text = " ".join(args.question)
    idx = study_index()
    if args.json:
        sid = idx.resolve(text)
        if sid is not None:
            print(json.dumps(idx.get(sid), indent=1, sort_keys=True,
                             ensure_ascii=False))
            return 0
        hits = idx.bearing_on(text)
        print(json.dumps([{"id": h.sid, "score": h.score,
                           "fields": list(h.fields)} for h in hits],
                         indent=1))
        return 0 if hits else 1
    code, reply = answer_study_query(text, idx)
    print(reply)
    return code


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
