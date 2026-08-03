# ==============================================================================
# §14  MULTI-TOKEN LEXER + LATEX SCRUB (v3.8.0 NEW MODULE)
# ==============================================================================
# Fills the second-largest semantic gap in v3.7.x: the original engine
# tokenised every query at whitespace, destroying multi-word physics concepts
# such as 'Weyl anomaly', 'Hatsugai-Kohmoto model', or 'spin squeezing
# parameter'.  It also choked on LaTeX like $\alpha + \beta$.
#
# This module performs three jobs, in order:
#   1. LaTeX scrub          - strips $...$ blocks and LaTeX-command tokens,
#                              then converts a dictionary of Greek-letter
#                              commands to plain-text names so they can still
#                              match the vocabulary.
#   2. Multi-word detect    - greedy longest-match against the live vocabulary
#                              (handles 'weyl anomaly', 'beta function', etc.)
#   3. Standard tokenise    - whitespace + stop-word filter for the remainder,
#                              with light lemmatisation (plurals, -ed, -ing)
#                              and fuzzy matching for typos.
#
# The lexer is PURE (no I/O, no random state) and stdlib only.
# Adapted from core/glm_multi_token_lexer.py to be self-contained.
# ==============================================================================
from __future__ import annotations
import re
import difflib
from typing import List, Set, Tuple, Dict, Optional, Iterable

# ── 1. LATEX SCRUB ────────────────────────────────────────────────────────────

_GREEK_MAP: Dict[str, str] = {
    r"\\alpha": "alpha", r"\\beta": "beta", r"\\gamma": "gamma",
    r"\\delta": "delta", r"\\epsilon": "epsilon", r"\\varepsilon": "epsilon",
    r"\\zeta": "zeta", r"\\eta": "eta", r"\\theta": "theta",
    r"\\vartheta": "theta", r"\\iota": "iota", r"\\kappa": "kappa",
    r"\\lambda": "lambda", r"\\mu": "mu", r"\\nu": "nu", r"\\xi": "xi",
    r"\\pi": "pi", r"\\varpi": "pi", r"\\rho": "rho", r"\\varrho": "rho",
    r"\\sigma": "sigma", r"\\varsigma": "sigma", r"\\tau": "tau",
    r"\\upsilon": "upsilon", r"\\phi": "phi", r"\\varphi": "phi",
    r"\\chi": "chi", r"\\psi": "psi", r"\\omega": "omega",
    r"\\Gamma": "gamma", r"\\Delta": "delta", r"\\Theta": "theta",
    r"\\Lambda": "lambda", r"\\Xi": "xi", r"\\Pi": "pi",
    r"\\Sigma": "sigma", r"\\Phi": "phi", r"\\Psi": "psi",
    r"\\Omega": "omega",
}

_OP_MAP: Dict[str, str] = {
    r"\\partial": "derivative", r"\\nabla": "gradient",
    r"\\int": "integral", r"\\sum": "sum", r"\\prod": "product",
    r"\\langle": "expectation", r"\\rangle": "expectation",
    r"\\bar": "conjugate", r"\\dagger": "adjoint",
    r"\\hat": "operator", r"\\tilde": "modified",
    r"\\overline": "conjugate", r"\\cdot": "times",
    r"\\times": "times", r"\\div": "divide",
    r"\\pm": "plusminus", r"\\mp": "minusplus",
    r"\\leq": "leq", r"\\geq": "geq", r"\\neq": "neq",
    r"\\approx": "approx", r"\\equiv": "equiv",
    r"\\to": "to", r"\\rightarrow": "to", r"\\Rightarrow": "implies",
    r"\\infty": "infinity", r"\\partial": "derivative",
}


def _extract_nested_content(text: str, start_idx: int) -> Tuple[str, int]:
    """Extract content between matching braces starting at start_idx."""
    if start_idx >= len(text) or text[start_idx] != '{':
        return "", start_idx
    stack = 0
    content = []
    for i in range(start_idx, len(text)):
        c = text[i]
        if c == '{':
            stack += 1
            if stack > 1:
                content.append(c)
        elif c == '}':
            stack -= 1
            if stack == 0:
                return "".join(content), i + 1
            content.append(c)
        else:
            content.append(c)
    return "".join(content), len(text)


def scrub_latex(text: str) -> str:
    """Strip LaTeX dollar-math delimiters, expand Greek/operator commands,
    drop the rest.  Pure deterministic, stdlib only.

    v3.8.0 fix: Expand Greek letters and operators BEFORE stripping $...$
    wrappers, so that '$\\alpha + \\beta$' yields 'alpha beta' rather than
    being silently removed.
    """
    if not text:
        return text
    # 1. Replace block math environments
    text = re.sub(r"\\begin\{[^}]+\}.*?\\end\{[^}]+\}", " ", text, flags=re.DOTALL)

    # 2. Expand Greek letters and operators FIRST (while they're still
    # inside the $...$ wrappers, so we don't lose them when we strip the $).
    for cmd in sorted(_GREEK_MAP, key=len, reverse=True):
        text = re.sub(cmd + r"(?![a-zA-Z])", " " + _GREEK_MAP[cmd] + " ", text)
    for cmd in sorted(_OP_MAP, key=len, reverse=True):
        text = re.sub(cmd + r"(?![a-zA-Z])", " " + _OP_MAP[cmd] + " ", text)

    # 3. Now strip $$...$$ and $...$ delimiters (keeping the expanded content).
    text = re.sub(r"\$\$", " ", text)
    text = re.sub(r"\$", " ", text)

    # 4. Handle nested font-style commands recursively
    style_commands = [
        r"\\mathrm", r"\\mathcal", r"\\mathbf", r"\\text", r"\\bm", r"\\dot",
        r"\\bar", r"\\tilde", r"\\hat", r"\\vec", r"\\acute", r"\\grave",
        r"\\check", r"\\breve", r"\\underline", r"\\frac", r"\\sqrt"
    ]
    cmd_pattern = "|".join(style_commands)

    def process_recursive(s: str) -> str:
        match = re.search(cmd_pattern, s)
        if not match:
            return s
        start = match.start()
        end_cmd = match.end()
        # Special case for \frac which has two braced arguments
        if s[start:end_cmd] == r"\frac":
            content1, next_idx = _extract_nested_content(s, end_cmd)
            content2, final_idx = _extract_nested_content(s, next_idx)
            return (s[:start] + " " + process_recursive(content1) + " / "
                    + process_recursive(content2) + " "
                    + process_recursive(s[final_idx:]))
        content, final_idx = _extract_nested_content(s, end_cmd)
        if content or final_idx > end_cmd:
            return (s[:start] + " " + process_recursive(content) + " "
                    + process_recursive(s[final_idx:]))
        return s[:start] + " " + process_recursive(s[end_cmd:])

    text = process_recursive(text)

    # 5. Clean up remaining LaTeX syntax
    text = re.sub(r"\\[a-zA-Z]+\*?", " ", text)
    text = re.sub(r"[_^]\{([^{}]*)\}", r" \1 ", text)
    text = re.sub(r"[_^]([a-zA-Z0-9])", r" \1 ", text)
    text = re.sub(r"[{}]", " ", text)
    return text


# ── 2. STOP WORDS (function-word filter) ─────────────────────────────────────

STOP_WORDS: Set[str] = {
    "what", "the", "on", "of", "in", "with", "to", "for", "have", "has", "had",
    "will", "shall", "should", "would", "may", "might", "must", "can", "could",
    "about", "does", "why", "how", "a", "an", "this", "that", "those", "these",
    "it", "be", "are", "is", "was", "were", "been", "being", "we", "you", "i",
    "they", "by", "as", "if", "so", "do", "at", "from", "into", "when", "where",
    "which", "then", "there", "here", "their", "its", "any", "each", "such",
    "more", "most", "much", "very", "well", "also", "only", "even", "thus",
    "hence", "suppose", "let", "given", "consider", "assume", "find", "show",
    "describe", "explain", "derive", "calculate", "determine", "both",
    "between", "all", "your", "answer", "please", "note", "take", "give",
    "tell", "me", "every", "positive", "integers", "integer", "natural",
    "number", "numbers", "real", "reals", "ways", "way", "many", "how",
    "compute", "evaluate", "prove", "proof", "verify", "demonstrate",
}


# ── 3. LEMMATISATION ─────────────────────────────────────────────────────────

_IRREGULAR_LEMMAS: Dict[str, str] = {
    "led": "lead", "leads": "lead", "leading": "lead",
    "brought": "bring", "bringing": "bring",
    "frozen": "freeze", "freezing": "freeze",
    "shown": "show", "showed": "show", "showing": "show",
    "gave": "give", "given": "give", "giving": "give",
    "took": "take", "taken": "take", "taking": "take",
    "found": "find", "finding": "find",
    "thought": "think", "thinking": "think",
    "known": "know", "knew": "know", "knowing": "know",
    "spent": "spend", "spending": "spend",
    "built": "build", "building": "build",
    "seen": "see", "saw": "see", "seeing": "see",
    "kept": "keep", "keeping": "keep",
    "atoms": "atom", "electrons": "electron", "protons": "proton",
    "neutrons": "neutron", "photons": "photon", "quarks": "quark",
    "gluons": "gluon", "bosons": "boson", "fermions": "fermion",
    "matrices": "matrix", "vectors": "vector", "states": "state",
    "operators": "operator", "hamiltonians": "hamiltonian",
}


# ── 4. MULTI-TOKEN LEXER ─────────────────────────────────────────────────────

class MultiTokenLexer:
    """Multi-word-aware tokenizer for physics + math queries.

    Greedy longest-match against the live vocabulary, with LaTeX scrubbing,
    lemmatisation, and fuzzy matching for typos.  Pure deterministic.
    """

    def __init__(self, vocabulary_words: Iterable[str],
                 stop_words: Optional[Set[str]] = None,
                 min_len: int = 2):
        self.stop_words = set(stop_words) if stop_words is not None else set(STOP_WORDS)
        self.min_len = min_len
        self.multi_word: List[List[str]] = []
        self.single_word: Set[str] = set()
        for w in vocabulary_words:
            w = w.lower().strip()
            if not w:
                continue
            parts = re.split(r"[\s\-]+", w)
            if len(parts) > 1:
                self.multi_word.append(parts)
            else:
                self.single_word.add(parts[0])
        # Sort multi-word phrases by length descending for greedy match
        self.multi_word.sort(key=len, reverse=True)
        # Index single-word set for fast lemmatisation lookups
        self._single_list = sorted(self.single_word)

    def _lemmatize(self, word: str) -> str:
        if word in _IRREGULAR_LEMMAS:
            return _IRREGULAR_LEMMAS[word]
        if word in self.single_word:
            return word
        # Plurals
        if word.endswith("ies") and word[:-3] + "y" in self.single_word:
            return word[:-3] + "y"
        if word.endswith("es") and word[:-2] in self.single_word:
            return word[:-2]
        if word.endswith("s") and word[:-1] in self.single_word:
            return word[:-1]
        # Past tense
        if word.endswith("ed") and word[:-2] in self.single_word:
            return word[:-2]
        if word.endswith("ed") and word[:-1] in self.single_word:
            return word[:-1]
        # Gerund
        if word.endswith("ing") and word[:-3] in self.single_word:
            return word[:-3]
        if word.endswith("ing") and word[:-3] + "e" in self.single_word:
            return word[:-3] + "e"
        return word

    def _is_metadata(self, token: str) -> bool:
        """Identify non-semantic metadata tokens (challenge IDs, file exts)."""
        if re.match(r"^challenge_?\d+$", token) or token == "challenge":
            return True
        if re.match(r"^\d+[a-z]?$", token):
            return True
        if token in ("pdf", "json", "py", "txt", "md", "tex"):
            return True
        if token in ("main", "problem", "id", "description"):
            return True
        return False

    def _fuzzy_match(self, token: str) -> Optional[str]:
        """Find the closest vocabulary match for a potentially misspelled word.
        Only fires for tokens longer than 3 chars to avoid false positives."""
        if len(token) <= 3:
            return None
        matches = difflib.get_close_matches(token, self._single_list, n=1, cutoff=0.85)
        return matches[0] if matches else None

    def tokenise(self, text: str) -> List[str]:
        """Return a deterministic list of meaning-bearing tokens / phrases."""
        text = scrub_latex(text)
        text = text.lower()
        text = text.replace("_", " ")
        # Keep alphanumerics, internal hyphens, whitespace.
        text = re.sub(r"[^a-z0-9\-\s]", " ", text)
        raw = []
        for w in re.split(r"\s+", text):
            if not w:
                continue
            # Strip leading/trailing hyphens but keep internal ones
            # (so 'hatsugai-kohmoto' survives but '-function' becomes 'function').
            w = w.strip("-")
            if w and not self._is_metadata(w):
                raw.append(w)

        out: List[str] = []
        i = 0
        while i < len(raw):
            matched = False
            # Try longest multi-word phrase first
            for phrase in self.multi_word:
                k = len(phrase)
                if i + k > len(raw):
                    continue
                if raw[i:i + k] == phrase:
                    out.append(" ".join(phrase))
                    i += k
                    matched = True
                    break
            if matched:
                continue

            w = raw[i]
            if w in self.single_word:
                out.append(w)
            elif w not in self.stop_words and len(w) >= self.min_len:
                lemma = self._lemmatize(w)
                if lemma in self.single_word:
                    out.append(lemma)
                else:
                    fuzzy = self._fuzzy_match(lemma)
                    if fuzzy:
                        out.append(fuzzy)
                    else:
                        out.append(w)
            i += 1
        return out

    # Convenience overload
    def tokenize(self, text: str) -> List[str]:
        return self.tokenise(text)


def build_lexer_from_vocab(vocab) -> MultiTokenLexer:
    """Create a lexer whose phrase table matches the live vocabulary keys.

    `vocab` may be either:
      * a dict-like {word: WordEntry}
      * an object with a `.words` attribute that is such a dict
    """
    if hasattr(vocab, 'words'):
        words = vocab.words.keys()
    else:
        words = vocab.keys()
    return MultiTokenLexer(words)


# ── 5. ISOLATION TEST ────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=== Testing Module 14: Multi-Token Lexer (v3.8.0) ===")
    vocab_words = {
        "weyl anomaly", "beta function", "rayleigh number",
        "spin squeezing", "hatsugai-kohmoto", "majorana",
        "parton", "quantum", "metric", "hamiltonian", "time",
        "operator", "anomaly",
    }
    lx = MultiTokenLexer(vocab_words)
    tests = [
        r"What is the weyl anomaly?",
        r"Tell me about the beta function in QFT.",
        r"What does $\alpha + \beta$ mean?",
        r"What is the $\beta$-function for a Hatsugai-Kohmoto Majorana with spin squeezing?",
        r"Compute the dot product of <3, -1, 4> and <2, 5, -3>.",
        r"Discuss the Hamiltonian's relationship to time.",
    ]
    for q in tests:
        toks = lx.tokenise(q)
        print(f"  {q}")
        print(f"    -> {toks}")
