"""``glm_universal.knowledge.glossary`` -- the paper's glossary, held out.

Phase 155, ``studies/CORPUS_DEFINITIONS_STUDY.md`` §2.1 and §2.3:

* **the glossary** (:data:`GLOSSARY`) -- the list items ``**Term:** gloss``
  of Appendix E of ``studies/GLM_ACADEMIC_PAPER.md``; the term is the text
  before the colon, the gloss the text after it, a term with a slash asked as
  written (27 entries when the measurement was taken);
* **the hold-out** (:func:`hold_out`) -- every sentence of the corpus, in any
  document, whose token sequence contains a gloss's tokens as a contiguous
  run is removed before ``define`` is asked; nothing else is
  (``GLM.CorpusDefinitions.heldout_clean`` / ``heldout_keeps``).  ``define``
  reads only the sentences and their postings, so the hold-out is applied to
  those;
* **the grade** (:func:`grade`) -- the content words an answer shares with
  the gloss (``model.is_content``, a final ``s`` dropped from a word of more
  than three letters, the term's own words left out); an answer **agrees**
  when the grade is at least :data:`AGREE`;
* **the controls** -- the term's **first mention** (:func:`first_mention`: the
  first sentence of the held-out corpus, in corpus order, holding the term
  and not a heading), and the **mismatched gloss** (:func:`mismatched_gloss`:
  each answer graded against the next term's gloss, the last against the
  first);
* **the context ranking** (:func:`context_ranking`) -- ``define``'s
  candidates ordered by how many of the term's twelve sentence-scale context
  words they hold, then by define's own order; what ``corpus define`` uses.

:func:`grade_definitions` grades ``define`` under either ranking against the
held-out glossary and gives the figures of G1-G4 (G1'-G4').

*Created 31 October 2026 (repository check).*

*Reconstructed 31 October 2026 (repository check): the original was lost in
the October 2026 reorganisation (the 29 October placeholder returned empty
values); rebuilt from studies/CORPUS_DEFINITIONS_STUDY.md §§2.1, 2.3, 5 and
7, MASTER_PLAN.md Phase 155, studies/CONFIDENCE_CURVE_STUDY.md §3 and
Appendix E of studies/GLM_ACADEMIC_PAPER.md.*
"""
from __future__ import annotations

import dataclasses
import re
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, FrozenSet, List, Optional, Sequence, Tuple

from .. import constants
from . import answer as ans
from . import model as mdl
from . import reader as rd

__all__ = ["PAPER", "GLOSSARY", "AGREE", "TOP", "parse_glossary", "glossary",
           "gloss_runs", "held_out_ids", "hold_out", "grade", "agrees",
           "first_mention", "mismatched_gloss", "context_ranking",
           "is_heading", "grade_definitions", "leaks"]

#: The paper whose Appendix E is the glossary.
PAPER: Path = constants.STUDIES_DIR / "GLM_ACADEMIC_PAPER.md"

#: An answer agrees with the gloss when it shares this many content words.
AGREE = 2

#: G3: an agreeing answer among the first ``TOP``.
TOP = 3

_APPENDIX = re.compile(r"^##\s+Appendix\s+E\b", re.IGNORECASE)
_ENTRY = re.compile(r"^\s*[-*]\s+\*\*(?P<term>[^*]+?):\*\*\s*(?P<gloss>.+?)\s*$")


def parse_glossary(text: str) -> Tuple[Tuple[str, str], ...]:
    """The ``(term, gloss)`` entries of Appendix E in ``text``, in order."""
    out: List[Tuple[str, str]] = []
    inside = False
    for line in text.splitlines():
        if _APPENDIX.match(line):
            inside = True
            continue
        if inside and re.match(r"^#{1,2}\s", line):
            break
        if inside:
            m = _ENTRY.match(line)
            if m:
                out.append((m.group("term").strip(), m.group("gloss").strip()))
    return tuple(out)


def glossary(path: Optional[Path] = None) -> Tuple[Tuple[str, str], ...]:
    """The glossary read from the paper (empty when the paper is absent)."""
    path = PAPER if path is None else Path(path)
    try:
        return parse_glossary(path.read_text(encoding="utf-8"))
    except OSError:
        return ()


#: The held-out glossary, read once at import.
GLOSSARY: Tuple[Tuple[str, str], ...] = glossary()


def gloss_runs(entries: Sequence[Tuple[str, str]] = GLOSSARY) -> List[Tuple[str, ...]]:
    """The token run of every gloss (empty runs dropped)."""
    return [r for r in (ans.tokens_of(g) for _, g in entries) if r]


def held_out_ids(knowledge: mdl.Knowledge,
                 entries: Sequence[Tuple[str, str]] = GLOSSARY) -> List[int]:
    """The ids of the sentences holding some gloss as a contiguous run."""
    removed = set()
    sentences = knowledge.sentences
    for run in gloss_runs(entries):
        lists = [knowledge.sentence_ids(t) for t in set(run)]
        if any(not ids for ids in lists):
            continue
        lists.sort(key=len)
        common = set(lists[0])
        for ids in lists[1:]:
            common.intersection_update(ids)
        removed.update(sid for sid in common
                       if ans.find_run(sentences[sid].tokens, run) >= 0)
    return sorted(removed)


def hold_out(knowledge: mdl.Knowledge,
             entries: Sequence[Tuple[str, str]] = GLOSSARY) -> mdl.Knowledge:
    """A copy of ``knowledge`` whose sentences and postings lack every sentence
    holding a gloss; the documents and the counted model are unchanged
    (``define`` reads neither)."""
    removed = set(held_out_ids(knowledge, entries))
    kept = tuple(s for i, s in enumerate(knowledge.sentences) if i not in removed)
    postings: Dict[str, List[int]] = {}
    for sid, s in enumerate(kept):
        for t in set(s.tokens):
            postings.setdefault(t, []).append(sid)
    held = dataclasses.replace(knowledge, sentences=kept,
                               postings={t: tuple(v) for t, v in postings.items()})
    return held


def grade(answer_tokens: Sequence[str], gloss_tokens: Sequence[str],
          term_tokens: Sequence[str]) -> int:
    """The content words the answer shares with the gloss (both folded, the
    term's words left out).  Symmetric and bounded by either side
    (``grade_comm``, ``grade_le_left``)."""
    return len(ans.content_set(answer_tokens, term_tokens)
               & ans.content_set(gloss_tokens, term_tokens))


def agrees(answer_tokens: Sequence[str], gloss_tokens: Sequence[str],
           term_tokens: Sequence[str]) -> bool:
    return grade(answer_tokens, gloss_tokens, term_tokens) >= AGREE


# ---------------------------------------------------------------------------
#  The controls
# ---------------------------------------------------------------------------

_HEADINGS: Dict[str, FrozenSet[str]] = {}
_HEADING_LINE = re.compile(r"^\s{0,3}#{1,6}\s+(.*\S)\s*$")


def _heading_texts(path: str, root: Optional[Path] = None) -> FrozenSet[str]:
    if path not in _HEADINGS:
        found: set = set()
        if path.lower().endswith((".md", ".markdown")):
            base = rd.REPOSITORY_ROOT if root is None else Path(root)
            try:
                text = (base / path).read_text(encoding="utf-8", errors="replace")
            except OSError:
                text = ""
            for line in text.splitlines():
                m = _HEADING_LINE.match(line)
                if m:
                    heading = " ".join(m.group(1).split())
                    found.add(heading)
                    # the reader splits a heading at its sentence ends too
                    found.update(" ".join(p.split())
                                 for p in rd._split_sentences(heading))
        _HEADINGS[path] = frozenset(found)
    return _HEADINGS[path]


def is_heading(sentence: rd.Sentence) -> bool:
    """A sentence that is a Markdown heading line of its document (or one of
    the sentences the reader cut a heading into)."""
    heads = _heading_texts(sentence.document)
    if not heads:
        return False
    return " ".join(sentence.text.split()) in heads


def first_mention(term: str, knowledge: mdl.Knowledge) -> Optional[Dict[str, Any]]:
    """The first sentence, in corpus order, that holds ``term`` and is not a
    heading -- the uninformed control (no rule about definitions, no chance)."""
    run = ans.tokens_of(term)
    for sid in ans.mention_ids(run, knowledge):
        s = knowledge.sentences[sid]
        if not is_heading(s):
            return {"address": s.address, "text": ans.one_line(s.text),
                    "tokens": s.tokens}
    return None


def mismatched_gloss(term: str, entries: Sequence[Tuple[str, str]] = GLOSSARY
                     ) -> Tuple[str, str]:
    """The next entry after ``term`` in glossary order (the last's is the
    first's): the gloss each answer is graded against for the mismatched
    control."""
    terms = [t for t, _ in entries]
    if term not in terms or not entries:
        return ("", "")
    nxt = entries[(terms.index(term) + 1) % len(entries)]
    return nxt


def context_ranking(term: str, knowledge: Optional[mdl.Knowledge] = None
                    ) -> Dict[str, Any]:
    """``define`` with the context ranking (Phase 155 §2.3): of the sentences
    that define ``term`` by a declared pattern, those holding most of the
    term's sentence-scale context words first."""
    return ans.define(term, knowledge, ranking="context")


# ---------------------------------------------------------------------------
#  The grading
# ---------------------------------------------------------------------------

def leaks(texts: Sequence[Sequence[str]],
          entries: Sequence[Tuple[str, str]] = GLOSSARY) -> int:
    """How many of the token sequences hold a gloss as a contiguous run (the
    hold-out guarantees none)."""
    runs = gloss_runs(entries)
    return sum(1 for toks in texts if any(ans.find_run(toks, r) >= 0 for r in runs))


def grade_definitions(held: mdl.Knowledge, ranking: str = "context",
                      entries: Sequence[Tuple[str, str]] = GLOSSARY
                      ) -> Dict[str, Any]:
    """``define`` (under ``ranking``) graded against the held-out glossary.

    ``held`` must already be held out (:func:`hold_out`).  Per term: the
    first answer's grade against its own gloss and against the mismatched
    gloss, whether one of the first three agrees, and the first-mention
    control's grade.  A refused term scores 0 and records its mentions.
    """
    rows: List[Dict[str, Any]] = []
    total = control_total = mismatched_total = 0
    wins = losses = agree = agree_top = control_agree = 0
    texts: List[Tuple[str, ...]] = []
    for term, gloss in entries:
        run = ans.tokens_of(term)
        gloss_toks = ans.tokens_of(gloss)
        _, other = mismatched_gloss(term, entries)
        other_toks = ans.tokens_of(other)
        got = ans.define(term, held, ranking=ranking)
        control = first_mention(term, held)
        c_grade = grade(control["tokens"], gloss_toks, run) if control else 0
        row: Dict[str, Any] = {"term": term, "control": control["address"] if control else "",
                               "control_grade": c_grade}
        if control:
            texts.append(tuple(control["tokens"]))
        if got.get("ok"):
            answers = got["answers"]
            first = held.sentences[answers[0]["sid"]].tokens
            texts.extend(held.sentences[a["sid"]].tokens for a in answers[:TOP])
            g = grade(first, gloss_toks, run)
            mg = grade(first, other_toks, run)
            top_agree = any(agrees(held.sentences[a["sid"]].tokens, gloss_toks, run)
                            for a in answers[:TOP])
            row.update({"answered": True, "address": answers[0]["address"],
                        "grade": g, "mismatched_grade": mg, "agrees": g >= AGREE,
                        "top_agrees": top_agree,
                        "quality": {"pattern": answers[0]["pattern"],
                                    "strength": answers[0]["strength"],
                                    "source": answers[0]["source"],
                                    "support": answers[0]["support"],
                                    "grade": answers[0]["grade"]}})
        else:
            g = mg = 0
            top_agree = False
            row.update({"answered": False, "grade": 0, "mismatched_grade": 0,
                        "agrees": False, "top_agrees": False,
                        "refusal": got.get("refusal", ""),
                        "mentions": got.get("mentions", 0)})
        total += g
        mismatched_total += mg
        control_total += c_grade
        wins += g > c_grade
        losses += g < c_grade
        agree += g >= AGREE
        agree_top += top_agree
        control_agree += c_grade >= AGREE
        rows.append(row)
    return {"ranking": ranking, "terms": len(entries), "rows": rows,
            "answered": sum(1 for r in rows if r["answered"]),
            "total_grade": total, "control_total": control_total,
            "mismatched_total": mismatched_total, "wins": wins, "losses": losses,
            "agree": agree, "agree_top": agree_top, "control_agree": control_agree,
            "leaks": leaks(texts, entries)}


def marks(graded: Dict[str, Any]) -> Dict[str, bool]:
    """G1-G4 (or G1'-G4') of a grading."""
    return {
        "G1": graded["total_grade"] > graded["control_total"]
              and graded["wins"] > graded["losses"],
        "G2": graded["agree"] >= 14,
        "G3": graded["agree_top"] >= 18,
        "G4": graded["total_grade"] >= 2 * graded["mismatched_total"],
    }
