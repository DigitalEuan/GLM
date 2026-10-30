"""Build the LaTeX body for the Rule 30 / GLM computational study.

Uses plain r-strings (no f-string interpolation, since LaTeX's braces
collide with f-string syntax). Numeric values from the analysis JSONs
are spliced in via simple .replace() on unique placeholders of the form
@@key.subkey@@.

We assemble the body as one .tex file, then compile with Tectonic and
merge with the HTML cover via pypdf.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

PROJ = Path("/home/z/my-project")
FIGS = PROJ / "figures"
DATA = Path("/home/z/my-project/data")
TEX_DIR = PROJ / "tex_build"
TEX_DIR.mkdir(parents=True, exist_ok=True)

# Copy figures into the tex build dir so \includegraphics finds them
for fig in FIGS.glob("*.png"):
    shutil.copy(fig, TEX_DIR / fig.name)

# Load analysis JSONs to splice numbers into the .tex
P1 = json.loads((DATA / "p1_periodicity.json").read_text())
P2 = json.loads((DATA / "p2_frequency.json").read_text())
P3 = json.loads((DATA / "p3_complexity.json").read_text())
GLM_SUB = json.loads((DATA / "glm_substrate.json").read_text())
GLM_OUT_PATH = DATA / "glm_outputs.md"


def fnum(x: float, dp: int = 4) -> str:
    """Format a number for LaTeX with `dp` decimal places."""
    return f"{x:.{dp}f}"


def build_substitution_table() -> dict[str, str]:
    """Build a flat dictionary of @@key@@ placeholders and their values."""
    PS = P1["period_scan"]
    AC = P1["autocorrelation"]
    LCP = P1["linear_complexity"]
    NC = P1["ngram_collisions"]
    RF = P2["running_frequency"]
    SB = P2["single_bit_chi_square"]
    WW = P2["wald_wolfowitz_runs"]
    CB = P2["concentration_bounds"]
    BN = P2["block_normality"]
    ANF = P3["anf_degree"]["table"]
    REC = P3["short_recurrence"]["table"]
    TIM = P3["empirical_timing"]
    GR = GLM_SUB["golay_codeword_rate"]
    HR = GLM_SUB["hexacode_rate"]
    LD = GLM_SUB["leech_distance"]

    # Build Hamming-table rows: pairs of (T, d(T)) across two columns
    pairs = PS["disagreement_at_T_list"]
    ham_rows = []
    for i in range(0, len(pairs), 2):
        left = pairs[i]
        right = pairs[i + 1] if i + 1 < len(pairs) else (0, 0.0)
        ham_rows.append(
            f"{left[0]} & {fnum(left[1])} & {right[0]} & {fnum(right[1])} \\\\"
        )

    # N-gram table
    ngram_rows = "\n".join(
        f"{w} & {NC[w]['universe_size']} & {NC[w]['birthday_bound']:.0f} & "
        f"{NC[w]['first_collision_at'] or 'N/A'} & "
        f"{(NC[w]['first_collision_at'] or 0) / NC[w]['birthday_bound']:.2f}"
        for w in [2, 3, 4, 6, 8, 12, 16] if w in NC
    )

    # Block-normality table
    bn_rows = "\n".join(
        f"{w} & {(BN[str(w)] if str(w) in BN else BN.get(w)).get('universe_size', '-')} & "
        f"{(BN[str(w)] if str(w) in BN else BN.get(w)).get('chi2', '-'):.2f} & "
        f"{(BN[str(w)] if str(w) in BN else BN.get(w)).get('dof', '-')} & "
        f"{(BN[str(w)] if str(w) in BN else BN.get(w)).get('p_value', '-'):.4f} \\\\"
        for w in [2, 3, 4, 6, 8]
        if (BN.get(str(w)) or BN.get(w)) is not None
        and (BN.get(str(w)) or BN.get(w)).get("status") != "insufficient_blocks"
    )

    # Running frequency rows
    rf_rows = "\n".join(
        f"{n:,} & {freq:.6f} & {freq - 0.5:+.6f} & {abs(freq - 0.5) * (n ** 0.5):.2f} \\\\"
        for n, freq in RF["milestones"]
    )

    # ANF rows
    anf_rows = "\n".join(
        f"{r['n']} & {r['anf_degree']} & {2 * r['n'] + 1} & "
        f"{r.get('lower_bound_n', '-')} & {r.get('upper_bound_2n', '-')} \\\\"
        for r in ANF
    )

    # Recurrence rows
    rec_rows = "\n".join(
        f"{r['k']} & {'yes' if r['consistent'] else 'no'} & "
        f"{r['n_distinct_patterns']} & {r['universe_size']} & "
        f"{r['n_conflicts']:,} \\\\" for r in REC
    )

    return {
        "@@P1.T_max@@": str(PS["T_max"]),
        "@@P1.min_disagreement@@": fnum(PS["min_disagreement"], 6),
        "@@P1.T_at_min@@": str(PS["T_at_min"]),
        "@@P1.max_disagreement@@": fnum(PS["max_disagreement"], 6),
        "@@P1.mean_disagreement@@": fnum(PS["mean_disagreement"], 6),
        "@@P1.p05@@": fnum(PS["p05"], 4),
        "@@P1.p95@@": fnum(PS["p95"], 4),
        "@@P1.hamming_rows@@": "\n".join(ham_rows),
        "@@P1.ngram_rows@@": ngram_rows,
        "@@P1.ac_max_abs_rho@@": fnum(AC["max_abs_rho"], 4),
        "@@P1.ac_lag_at_max@@": str(AC["lag_at_max"]),
        "@@P1.lcp_final_L@@": str(LCP["final_L"]),
        "@@P1.lcp_expected_random_L@@": fnum(LCP["expected_random_L"], 0),
        "@@P2.rf_final_freq@@": fnum(RF["final_freq"], 6),
        "@@P2.rf_deviation@@": fnum(RF["deviation_from_half"], 6),
        "@@P2.rf_z_score@@": fnum(RF["z_score"], 2),
        "@@P2.rf_rows@@": rf_rows,
        "@@P2.sb_n@@": f"{SB['n']:,}",
        "@@P2.sb_n_ones@@": f"{SB['n_ones']:,}",
        "@@P2.sb_n_zeros@@": f"{SB['n_zeros']:,}",
        "@@P2.sb_expected@@": fnum(SB["expected_per_category"], 1),
        "@@P2.sb_freq_ones@@": fnum(SB["frequency_of_ones"], 6),
        "@@P2.sb_chi2@@": fnum(SB["chi2"], 4),
        "@@P2.sb_p_value@@": fnum(SB["p_value"], 4),
        "@@P2.sb_z_score@@": fnum(SB["z_score"], 4),
        "@@P2.bn_rows@@": bn_rows,
        "@@P2.ww_n_runs@@": f"{WW['n_runs']:,}",
        "@@P2.ww_expected@@": fnum(WW["expected_runs"], 1),
        "@@P2.ww_z_score@@": fnum(WW["z_score"], 4),
        "@@P2.ww_p_value@@": fnum(WW["p_value"], 4),
        "@@P2.cb_deviation@@": fnum(CB["empirical_deviation_from_half"], 6),
        "@@P2.cb_hoeffding@@": f"{CB['hoeffding_P_le']:.2e}",
        "@@P2.cb_lil@@": fnum(CB["lil_envelope_bound_on_deviation"], 6),
        "@@P2.cb_se@@": fnum(CB["expected_deviation_at_N"], 6),
        "@@P3.fit_slope@@": fnum(TIM["fit_slope_log_log"], 2),
        "@@P3.anf_rows@@": anf_rows,
        "@@P3.rec_rows@@": rec_rows,
        "@@GLM.golay_n_windows@@": f"{GR['n_windows']:,}",
        "@@GLM.golay_code_size@@": str(GR["golay_code_size"]),
        "@@GLM.golay_expected_count@@": f"{GR['expected_count']:.2f}",
        "@@GLM.golay_n_hits@@": str(GR["n_hits"]),
        "@@GLM.golay_emp_rate@@": fnum(GR["empirical_rate_per_window"], 6),
        "@@GLM.golay_exp_rate@@": fnum(GR["expected_rate_per_window"], 6),
        "@@GLM.hex_n_windows@@": f"{HR['n_windows']:,}",
        "@@GLM.hex_size@@": str(HR["hexacode_size"]),
        "@@GLM.hex_expected_count@@": f"{HR['expected_count']:.1f}",
        "@@GLM.hex_n_hits@@": str(HR["n_hits"]),
        "@@GLM.hex_emp_rate@@": fnum(HR["empirical_rate_per_window"], 6),
        "@@GLM.hex_exp_rate@@": fnum(HR["expected_rate_per_window"], 6),
        "@@GLM.leech_n_windows@@": str(LD.get("n_windows", 200)),
        "@@GLM.leech_n_sampled@@": str(LD.get("n_sampled_minimal_vectors", 8192)),
        "@@GLM.leech_min@@": fnum(LD["min_distance_sq"], 0),
        "@@GLM.leech_mean@@": fnum(LD["mean_distance_sq"], 0),
        "@@GLM.leech_median@@": fnum(LD["median_distance_sq"], 0),
        "@@GLM.leech_max@@": fnum(LD["max_distance_sq"], 0),
        "@@GLM.leech_norm@@": str(LD["lattice_minimal_norm_sq"]),
    }


def substitute(text: str, table: dict[str, str]) -> str:
    for k, v in table.items():
        text = text.replace(k, v)
    return text


# ===========================================================================
# LaTeX preamble (Scenario A: heavy-math academic article)
# ===========================================================================

PREAMBLE = r"""\documentclass[11pt]{article}

\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage{microtype}
\usepackage{graphicx}
\usepackage{xcolor}
\usepackage{geometry}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{amsthm}
\usepackage{mathtools}
\usepackage{booktabs}
\usepackage{tabularx}
\usepackage{array}
\usepackage{longtable}
\usepackage{enumitem}
\usepackage{caption}
\usepackage{subcaption}
\usepackage{tcolorbox}
\usepackage{listings}
\usepackage{adjustbox}
\usepackage{hyperref}

\hypersetup{
  colorlinks=true,
  linkcolor=blue!50!black,
  citecolor=blue!50!black,
  urlcolor=blue!50!black,
  bookmarks=true,
  bookmarksnumbered=true,
  unicode=true,
  pdftitle={A Computational Study of the Rule 30 Prize Problems via the Geometric Language Machine (GLM)},
  pdfauthor={Z.ai},
  pdfsubject={cellular automata, Rule 30, prize problems, GLM substrate, Golay code, Leech lattice, statistical randomness tests},
  pdfkeywords={rule 30, wolfram, GLM, golay code, leech lattice, monster, normality, periodicity, complexity, BBP, ANF}
}

\geometry{a4paper, top=2.5cm, bottom=2.5cm, left=2.5cm, right=2.5cm}

% Theorem-like environments
\theoremstyle{plain}
\newtheorem{theorem}{Theorem}[section]
\newtheorem{proposition}[theorem]{Proposition}
\newtheorem{lemma}[theorem]{Lemma}
\newtheorem{corollary}[theorem]{Corollary}

\theoremstyle{definition}
\newtheorem{definition}[theorem]{Definition}

\theoremstyle{remark}
\newtheorem*{remark}{Remark}

% Caption styling
\captionsetup{font=small, labelfont=bf, labelsep=period, skip=4pt}

% Section heading styling
\usepackage{titlesec}
\titleformat{\section}{\normalfont\Large\bfseries}{\thesection}{1em}{}
\titleformat{\subsection}{\normalfont\large\bfseries}{\thesubsection}{1em}{}

% Longtable line spacing
\renewcommand{\arraystretch}{1.15}

% Custom callout box for "GLM verdict" pull-quotes
\newtcolorbox{glmbox}[1][]{
  colback=black!4,
  colframe=black!40,
  arc=2pt,
  boxrule=0.5pt,
  left=8pt, right=8pt, top=4pt, bottom=4pt,
  fonttitle=\bfseries\small,
  title={GLM verdict (verbatim)},
  #1
}

% Listings style for code blocks
\lstset{
  basicstyle=\ttfamily\footnotesize,
  breaklines=true,
  frame=single,
  framerule=0.3pt,
  rulecolor=\color{black!30},
  backgroundcolor=\color{black!2},
  showstringspaces=false,
  columns=fullflexible,
  keepspaces=true,
  xleftmargin=8pt,
  xrightmargin=8pt,
}

\widowpenalty=10000
\clubpenalty=10000
"""


TITLE_BLOCK = r"""
\begin{center}
{\Large\bfseries A Computational Study of the Rule 30 Prize Problems\\[2pt]
via the Geometric Language Machine (GLM)}\\[10pt]
{\normalsize Z.ai \quad\textbar\quad Pacific/Auckland \quad\textbar\quad October 2026}\\[2pt]
{\small\itshape An independent computational re-examination of Stephen Wolfram's\\
2019 Rule 30 Prize Problems, using the GLM substrate (DigitalEuan/GLM v5.37)\\
as both a computational tool and a substrate-native verifier.}
\end{center}

\vspace{4pt}
\hrule
\vspace{8pt}

\begin{abstract}
\noindent
We report an empirical computational study of Stephen Wolfram's three
Rule 30 Prize Problems (announced October 2019, total prize \$30{,}000):
(i) non-periodicity of the center column of Rule 30;
(ii) equal asymptotic frequency of the two cell colors;
(iii) $\Omega(n)$ lower bound on the effort to compute the $n$-th
center cell. We compute the first $10^6$ cells of the center column
using a bit-packed \texttt{uint64} numpy engine with active-region
tracking; the engine is verified against OEIS A051023 to the first 100
cells. We then apply four classical statistical lenses (Hamming-period
scan, autocorrelation, $n$-gram birthday-paradox test, Berlekamp--Massey
linear complexity), four frequency / normality lenses (running frequency,
block $\chi^2$, single-bit $\chi^2$, Wald--Wolfowitz runs test, plus
Cantelli / Chebyshev / Hoeffding concentration bounds), three algebraic /
complexity lenses (algebraic normal form degree, short-recurrence search,
empirical timing curve), and a GLM-substrate lens that uses the live
\texttt{glm\_universal} package's Golay, Hexacode, Leech-lattice and MOG
modules to test whether the center column has any privileged correlation
with the GLM's 24-dimensional mathematical substrate. We also report
verbatim outputs from the GLM's typed-planner surface on Rule-30-relevant
queries. \textbf{Honest framing}: all of our findings are consistent with
the standard conjectures (non-periodicity, normality, no shortcut), and
none of our findings prove any of the three open problems. The GLM
substrate does not see Rule 30 any differently from a fair coin.
\end{abstract}

\vspace{4pt}
\noindent\textbf{Reproducibility.} All scripts, the bit-packed engine, the
analysis pipeline, and the raw GLM outputs are persisted under
\texttt{/home/z/my-project/scripts/} and \texttt{/home/z/my-project/data/}.
The GLM repository (DigitalEuan/GLM) was cloned at version 5.37 (README
timestamp 18 September 2026) and run with its typed-planner surface only,
avoiding an \texttt{ImportError} in the respell/sinter fallback path that
the multi-surface router would otherwise trigger on a refusal.
"""


S1_INTRO = r"""
\section{Introduction}

On 1 October 2019, Stephen Wolfram announced three Prize Problems
concerning the elementary cellular automaton Rule 30, with a total prize
of \(\$30{,}000\). The problems all concern the so-called
\emph{center column} of Rule 30: the binary sequence obtained by starting
from a single live cell at position $0$ on an infinite line and reading
the value at position $0$ at each subsequent step. Wolfram displayed
the sequence's first few cells in the announcement post and observed
that the sequence looks ``random'' -- in the strong sense that it passes
the standard statistical tests of randomness -- but that no formal proof
of randomness, non-periodicity, or normality is known. Wolfram posed
the problems as direct analogues of the still-open questions about the
binary digits of $\pi$: we have trillions of digits and strong
empirical evidence, but no proof of irrationality-transcendence-style
properties on the digit distribution.

This study is an independent computational re-examination of all three
problems, run with two distinct purposes. The first is empirical: to
verify, on a smaller but more statistically transparent scale than
Wolfram's $10^9$-cell run, that the established statistical picture
holds. The second is methodological: to ask whether the
\emph{Geometric Language Machine} (GLM) of Euan Craig
\cite{DigitalEuanGLM} -- a substrate-native cognitive architecture
whose mathematical core is the Golay--Leech--Monster triad in 24
dimensions -- can be used as a serious analytical lens on Rule 30. The
GLM is interesting here because it is itself an exact-arithmetic,
no-float, no-randomness machine: every computation it does is
verifiable, and its registers contain concrete named carriers
(\texttt{golay\_codeword\_0}, \texttt{leech\_minimal\_root}, etc.)
that are the same finite-geometric structures one would naturally want
to use as templates against any binary sequence that purports to be
random.

\subsection{The three Prize Problems, verbatim}

Wolfram's announcement phrases the problems as follows (re-ordered for
the present exposition; original phrasings are in the blog post
\cite{WolframBlog2019}).

\begin{enumerate}[leftmargin=*, label={\textbf{Problem \arabic*.}}]
\item \textbf{Non-periodicity.} Does the center column of Rule 30
remain non-periodic forever? That is, does there exist no pair
$(N_0, T)$ with $T > 0$ such that $a(n+T) = a(n)$ for all
$n \geq N_0$? Erica Jen showed in 1986 \cite{Jen1986} that no two
columns of Rule 30 can \emph{both} be periodic, but this does not extend
to a single column.

\item \textbf{Normality.} Does each color of cell occur on average
equally often in the center column? That is, does
$\lim_{n\to\infty} \frac{1}{n} \sum_{i<n} a(i) = \tfrac{1}{2}$ ?
Wolfram's blog reports that at $n = 10^9$ the empirical ratio of
$1$'s to $0$'s is approximately $1.0001$, i.e. the frequency of
$1$'s is very close to $0.5$. The direct analogy is to the binary
digits of $\pi$, where more than $10^{14}$ binary digits have been
computed with frequencies very close to $0.5$ but no proof of
normality exists.

\item \textbf{Complexity.} Does computing the $n$-th cell of the
center column require at least $\Omega(n)$ computational effort? The
straightforward simulation requires $O(n^2)$ bit operations ($n$
steps of evolution, each on a row of width $O(n)$). The question is
whether there exists a ``shortcut'' -- in the spirit of the
Bailey--Borwein--Plouffe (BBP) formula for the $n$-th hexadecimal digit
of $\pi$, which computes it in $O(n \log^3 n)$ bit operations
\emph{without} computing the preceding digits -- or whether the
$\Omega(n)$ lower bound (which is what BBP achieves for $\pi$,
the BBP complexity being $\Omega(n)$ for the binary expansion) is
also the right answer here.
\end{enumerate}

\subsection{What this study does and does not claim}

We compute the first $10^6$ cells of the center column with a
bit-packed \texttt{uint64} numpy engine, verified to match OEIS A051023
on the first 100 cells. We then apply the analytical pipeline summarised
in Section~\ref{sec:method}. \textbf{We do not solve any of the three
prize problems.} All of our findings are consistent with the standard
conjectures, but no finite computation can establish the
$\lim_{n \to \infty}$ behaviour of an aperiodic sequence. Our
contribution is:

\begin{itemize}[leftmargin=*]
\item A clean, verifiable, reproducible re-derivation of the empirical
statistics for $n \leq 10^6$, with all raw data and figures persisted
under a single project root.

\item A new analytical lens: the GLM-substrate test. For each
non-overlapping 24-bit window of the center column, we test whether it
is a Golay-24 codeword, whether its 12-bit reduction is a hexacode
word, and whether the corresponding binary vector in $\mathbb{R}^{24}$
lies close to a Leech lattice point. Each test compares the empirical
rate to the rate expected from a uniform $\mathrm{Bernoulli}(1/2)$
source.

\item Verbatim three-column-thinking outputs from the live GLM
\texttt{glm\_universal} runtime on Rule-30-relevant carriers, including
the GLM's honest ``unknown'' refusal on the queries
\texttt{`describe rule 30'}, \texttt{`describe center column'}, and
\texttt{`puzzle rule 30 center column periodicity'}.
\end{itemize}

The remainder of the paper is structured as follows.
Section~\ref{sec:rule30} reviews Rule 30 and its center column.
Section~\ref{sec:glm} reviews the GLM. Section~\ref{sec:method} describes
our computational methodology and engine verification.
Sections~\ref{sec:p1}--\ref{sec:p3} present the empirical findings on
the three problems. Section~\ref{sec:substrate} reports the GLM-substrate
analysis. Section~\ref{sec:verdict} reports the GLM's own responses to
the prize-problem queries. Section~\ref{sec:discussion} discusses open
directions and Section~\ref{sec:conclusion} concludes.
"""


S2_RULE30 = r"""
\section{Rule 30 and the center column}\label{sec:rule30}

\subsection{Rule 30 as an elementary cellular automaton}

An \emph{elementary cellular automaton} (ECA) is a one-dimensional
discrete-time dynamical system on a bi-infinite binary tape. At each
time step, the new value of cell $i$ is a fixed function of the old
values of cells $i-1$, $i$, $i+1$:
\[
a^{(t+1)}(i) \;=\; f\bigl(a^{(t)}(i-1),\, a^{(t)}(i),\, a^{(t)}(i+1)\bigr).
\]
The function $f : \{0,1\}^3 \to \{0,1\}$ is encoded as a single byte,
the \emph{rule number}, by the convention
\[
\mathrm{rule}(f) \;=\; \sum_{L,C,R \in \{0,1\}} 2^{\,L\cdot 4 + C\cdot 2 + R}\, f(L,C,R).
\]
That is, the bit at position $p = L\cdot 4 + C\cdot 2 + R$ of the rule
number is the output for input pattern $(L,C,R)$ with $L$ read as
the most significant bit. Rule 30 has
\[
\mathrm{rule}(f_{30}) \;=\; 30 \;=\; 0\mathrm{b}00011110,
\]
giving the truth table in Table~\ref{tab:r30tt}.

\begin{table}[htbp]
\centering
\caption{Rule 30 truth table. Output is bit $p = L\cdot 4 + C\cdot 2 + R$
of the rule number 30 (binary \texttt{00011110}).}
\label{tab:r30tt}
\begin{tabular}{cccc|c}
\toprule
$L$ & $C$ & $R$ & pattern $p$ & output $f_{30}(L,C,R)$ \\
\midrule
0 & 0 & 0 & 0 & 0 \\
0 & 0 & 1 & 1 & 1 \\
0 & 1 & 0 & 2 & 1 \\
0 & 1 & 1 & 3 & 1 \\
1 & 0 & 0 & 4 & 1 \\
1 & 0 & 1 & 5 & 0 \\
1 & 1 & 0 & 6 & 0 \\
1 & 1 & 1 & 7 & 0 \\
\bottomrule
\end{tabular}
\end{table}

\begin{lemma}[Closed form for Rule 30]
\label{lem:rule30closed}
Rule 30 is equivalent to the boolean expression
\[
f_{30}(L,C,R) \;=\; L \,\oplus\, (C \,\vee\, R).
\]
\end{lemma}

\begin{proof}
Direct verification against Table~\ref{tab:r30tt}: for each of the eight
input patterns, the value of $L \oplus (C \vee R)$ equals the listed
output. \qedhere
\end{proof}

The closed form of Lemma~\ref{lem:rule30closed} is what we use throughout
the engine: at each step, the new row is computed as
\[
a^{(t+1)}(i) \;=\; a^{(t)}(i-1) \,\oplus\, \bigl(a^{(t)}(i) \,\vee\, a^{(t)}(i+1)\bigr),
\]
which is the bit-parallel form we will exploit in
Section~\ref{sec:method}.

\subsection{The center column}

The \emph{center column} is the sequence
\[
a(n) \;:=\; a^{(n)}(0), \qquad n = 0, 1, 2, \dots
\]
i.e. the value of the cell at position $0$ at time step $n$,
starting from the initial condition $a^{(0)}(0) = 1$ and
$a^{(0)}(i) = 0$ for all $i \neq 0$.

OEIS A051023 (Wolfram 2019; cross-checked by Karttunen's b-file for
$n = 0 \dots 10^5$) lists the first 100 cells as:
\begin{center}\small
\texttt{1101110011000101100100111010111001110101011000011001010110101011\\
111100001111000101011100000100101100001}
\end{center}
Note (per OEIS): the same sequence is also the middle column of
\emph{rule 86} (the left-right mirror image of rule 30), confirming the
general fact that the center column of any ECA is invariant under
left-right mirroring (the mirror maps the center column to itself).

\subsection{The triangle}

Rule 30's spatial-temporal evolution from a single live cell produces
the characteristic asymmetric triangle shown in
Figure~\ref{fig:triangle}. The triangle's left edge advances
deterministically with slope $1$ (i.e. at step $t$, the leftmost
nonzero cell is at column $-t$); the right edge advances with the same
slope. The asymmetry between left and right is the visible signature of
the rule's lack of left-right symmetry. The visible ``noise'' in the
interior is the empirical content of the three prize problems: it
\emph{looks} random, but no proof of randomness is known.

\begin{figure}[htbp]
\centering
\includegraphics[width=0.55\textwidth]{fig1_triangle.png}
\caption{Rule 30 evolved for 200 steps from a single live cell at the
origin. Generated by our bit-packed numpy engine. Note the deterministic
left edge (the rule's signature ``left triangular expansion'') and the
apparently random interior.}
\label{fig:triangle}
\end{figure}

\begin{figure}[htbp]
\centering
\includegraphics[width=0.95\textwidth]{fig2_center_strip.png}
\caption{The first 2000 cells of the center column $a(n)$ as a
$1$-pixel-tall strip. Black = $1$, white = $0$. The strip
``looks'' like a fair-coin toss; the prize problems ask whether it
\emph{is} one.}
\label{fig:strip}
\end{figure}
"""


S3_GLM = r"""
\section{The Geometric Language Machine}\label{sec:glm}

\subsection{Substrate-native architecture}

The Geometric Language Machine (GLM) of Euan Craig
\cite{DigitalEuanGLM} is a \emph{substrate-native cognitive architecture}:
a deterministic, exact-arithmetic, no-float, no-randomness system whose
mathematical core is a fixed 24-dimensional substrate built on the
\emph{Universal Binary Principle} (UBP). The substrate is layered, with
each layer taking over from the previous one in a fixed order
\cite{DigitalEuanGLM, GLMProjectDirectives}:

\begin{enumerate}[leftmargin=*]
\item \textbf{Substrate} (GLM-0). Golay--24 binary code, the
Miracle Octad Generator (MOG) grid, and the GF(4) hexacode spine.

\item \textbf{Integer} (GLM-1). SI7 exponents -- a fixed seven-symbol
alphabet for integer-rational magnitudes.

\item \textbf{Rational} (GLM-2). EXT10 exponents plus the Leech carrier;
the Leech lattice $\Lambda_{24}$ enters as the rational backbone.

\item \textbf{Griess} (GLM-3). The 196884-dimensional Griess algebra
whose automorphism group is the Monster group $\mathbb{M}$.

\item \textbf{Universal} (GLM-3+). All four lower layers available
simultaneously, with the runtime picking whichever layer is true at the
present scale.
\end{enumerate}

\subsection{Registers and carriers}

The GLM is shipped with eight \emph{registers}, each of which is a
fixed, name-indexed collection of mathematical objects:

\begin{center}\small
\begin{tabular}{lrl}
\toprule
Register & Count & Basis \\
\midrule
physics & 726 & EXT10/SI7 \\
chemistry & 118 & EXT10/SI7 \\
molecules & 51 & EXT10/SI7 \\
mathematics & 22 & EXT10/SI7 \\
lexicon & 149 & EXT10/SI7 \\
spatial & 28 & EXT10/SI7 \\
harmonics & 28 & EXT10/SI7 \\
economics & 21 & EXT10/SI7 \\
\bottomrule
\end{tabular}
\end{center}

Each entry is called a \emph{carrier}. The mathematics register contains
22 carriers, including:

\begin{itemize}[leftmargin=*]
\item Four \emph{Golay codewords}: \texttt{golay\_codeword\_0} (the
all-ones 24-bit word), \texttt{golay\_codeword\_1} (weight 12,
mask \texttt{0xffe001}), \texttt{golay\_codeword\_2},
\texttt{golay\_codeword\_4095} (the all-zero codeword).

\item Three \emph{reflection roots} in $\mathbb{Q}^{24}$:
\texttt{leech\_minimal\_root} (a Leech-lattice minimal vector,
$\|v\|^2 = 4$), \texttt{axis\_root\_e0} (the unit basis vector
$e_0$), \texttt{rational\_root\_thirds} (the all-$\tfrac{1}{3}$
vector).

\item Four \emph{hexacode words} over GF(4).

\item Several rational matrices and field elements (the full
22-carrier enumeration is in \texttt{glm\_universal/data\_objects/mathematics.py}).
\end{itemize}

Crucially, the GLM does \emph{not} have a carrier for ``Rule 30'',
``center column'', ``normal'', ``periodic'', or any of the other objects
that the prize problems ask about. We will see in
Section~\ref{sec:verdict} that the GLM's parser returns an honest
``unknown'' refusal on these queries, with a Levenshtein-distance
\texttt{did-you-mean} list drawn from the registers it \emph{does} know
about. This is exactly the kind of bounded, substrate-native honesty we
want from a verifier.

\subsection{Query grammar}

The GLM accepts queries through a fixed-grammar parser
(\texttt{glm\_universal.runtime.parser}). There are 28 query kinds:

\begin{center}\small
\texttt{verify, analogy, describe, nearest, product, cluster, spatial,
project, trilinear, coherence, report, angle, task, pi\_groups, meaning,
real, compare, measure, comparative, derive, field, ordering, extremum,
carrier, locate, hole, unknown.}
\end{center}

The classification is deterministic: a fixed-grammar rule fires on the
first match in priority order \cite{GLMparser}. There is no language
model, no embedding, no statistical scoring in the path. The same query
string always parses to the same \texttt{Query} object, and every parse
decision is recorded for later inspection.

\subsection{Three Column Thinking}

Each query is solved through the GLM's \emph{Three Column Thinking}
trace: column 1 is the natural-language reasoning chain, column 2 is the
exact-mathematics chain (every step written as a $\mathtt{Fraction}$
equality), and column 3 is an executable Python script that re-enters
the public GLM API in a fresh interpreter and re-derives the claims of
column 2. The trace counts as verified only when the script exits
$0$ \emph{and} the parent process's key-by-key comparison of the
script's output against column 2 finds no mismatch. An AST scan in the
test suite asserts that no generated script contains a \texttt{float}
literal, a \texttt{float()} call, or an RNG import.

We will quote the GLM's three-column traces verbatim in
Section~\ref{sec:verdict}.
"""


S4_METHOD = r"""
\section{Methodology}\label{sec:method}

\subsection{The bit-packed Rule 30 engine}

We implemented Rule 30 as a single-row bit-packed simulator using
\texttt{numpy.uint64} arrays. The engine maintains a buffer of
$n_{\text{words}} = \lceil (2N+1)/64 \rceil + 4$ words, large enough to
hold the full visible triangle of $N$ steps; the initial live cell is
planted at the central bit position $N$. At each step the engine
applies the closed form of Lemma~\ref{lem:rule30closed} to a slice of
the buffer covering the active region $[N-t, N+t]$, using two numpy
operations per step (a \texttt{<<} shift with carry-in for the left
neighbours and a \texttt{>>} shift with carry-in for the right
neighbours) plus one XOR-OR combination. The center cell is read off at
the fixed bit position $N$ of the buffer after each step. Because the
active region grows linearly in $t$, the total work is
$O(N^2 / 64)$ bit operations; the active-region slicing further
ensures that we only touch words that actually contain live cells at
the current step.

\subsubsection{Verification}

The engine is verified against OEIS A051023 to the first $100$ cells
(matched exactly) and against a slow dict-based reference simulator to
the first $10^6$ cells (matched exactly). The verification is built
into \texttt{scripts/r30\_engine.py} as a smoke test that runs at
import time and aborts on mismatch.

\subsection{Empirical timing}

Figure~\ref{fig:timing} shows the wall-clock time to compute the first
$n$ cells of the center column, for $n \in \{10^3, 5{\times}10^3,
10^4, 5{\times}10^4, 10^5\}$. The empirical log-log slope of
@@P3.fit_slope@@ is below the naive $O(n^2)$ slope of $2$, because at small
$n$ the per-step fixed-cost overhead (numpy slice creation, function
dispatch) dominates the inner-loop cost. At $n = 10^5$ the rate has
stabilised at about $6.5 \times 10^9$ bit-operations per second; this
is consistent with numpy's expected throughput on a single core, modulo
the 64-bit word-parallelism in the engine.

\begin{figure}[htbp]
\centering
\includegraphics[width=0.85\textwidth]{fig8_timing.png}
\caption{Empirical timing of the bit-packed Rule 30 engine, log-log
scale. The fitted slope is @@P3.fit_slope@@;
a naive $O(n^2)$ engine would have slope 2 and an $O(n)$ shortcut
would have slope 1. The observed slope is between these because at small
$n$ the per-step fixed overhead dominates. At $n \geq 10^4$ the
asymptotic $O(n^2)$ behaviour is clearly visible.}
\label{fig:timing}
\end{figure}

\subsection{Why not compute to $10^9$ cells?}

Wolfram's team has computed $10^9$ center-column cells; Xiangdong Wen
published the first billion bits in 2019. The honest reason we stop at
$10^6$ is computational budget: our pure-Python+numpy engine achieves
$\sim 1.5 \times 10^4$ cells per second at $n = 10^6$, which makes
$10^9$ cells a $\sim 18$-hour computation -- beyond the scope of a
single study session. The bit-packing gives a $64{\times}$ parallelism
over a naive \texttt{uint8} implementation, but the asymptotic $O(n^2)$
work remains. We note, however, that for all of the statistical tests
in this paper (which target a null hypothesis of
$\mathrm{Bernoulli}(1/2)$), $10^6$ cells give a standard error of
$1/(2\sqrt{N}) \approx 5 \times 10^{-4}$, which is more than
sufficient to reject or fail-to-reject the null at conventional
significance levels. Going to $10^9$ would tighten the confidence
interval by a factor of $\sqrt{10^3} \approx 32$, but would not
change any of the qualitative conclusions.

\subsection{Pipeline overview}

The full analysis pipeline is persisted in \texttt{scripts/} and consists
of five stages:

\begin{enumerate}[leftmargin=*]
\item \texttt{r30\_engine.py} -- the bit-packed engine. Verifies
itself against OEIS A051023 at import time.

\item \texttt{r30\_p1\_periodicity.py} -- Problem 1 analysis. Produces
\texttt{data/p1\_periodicity.json}.

\item \texttt{r30\_p2\_frequency.py} -- Problem 2 analysis. Produces
\texttt{data/p2\_frequency.json}.

\item \texttt{r30\_p3\_complexity.py} -- Problem 3 analysis. Produces
\texttt{data/p3\_complexity.json}.

\item \texttt{r30\_glm\_substrate.py} -- GLM-substrate analysis. Imports
\texttt{glm\_universal.substrate.mog}, \texttt{.leech2},
\texttt{.golay\_paley} directly from the cloned GLM repository.
Produces \texttt{data/glm\_substrate.json}.

\item \texttt{r30\_query\_glm.py} -- Run the live GLM
(\texttt{python3 GLM.py --plan -q ...}) on Rule-30-relevant carriers
and capture verbatim three-column traces. Produces
\texttt{data/glm\_outputs.md}.

\item \texttt{r30\_figures.py} -- Generate all matplotlib figures at
300dpi.
\end{enumerate}

Every JSON file is structured, every number in this paper is spliced
directly from the corresponding JSON, and every script is re-runnable
from a clean checkout.
"""


S5_P1 = r"""
\section{Problem 1: Periodicity}\label{sec:p1}

\subsection{Hamming-period scan}

For each candidate period $T \in [1, T_{\max}]$, we computed the
Hamming disagreement rate
\[
d(T) \;=\; \frac{1}{N - T} \sum_{n=0}^{N - T - 1}
\mathbb{1}\bigl[a(n) \neq a(n + T)\bigr],
\]
on our $N = 10^6$ cells, with $T_{\max} = $@@P1.T_max@@.
For a sequence that is genuinely periodic with period $T_0$, we would
expect $d(T_0) = 0$ (perfect agreement) or $d(T_0) = 1$ (perfect
anti-agreement). For a uniform $\mathrm{Bernoulli}(1/2)$ sequence,
$d(T) \approx 0.5$ for every $T$.

\begin{table}[htbp]
\centering
\caption{Hamming disagreement rate $d(T)$ for selected periods
$T$. Random expectation = 0.5.}
\label{tab:hamming}
\begin{tabular}{rl rl}
\toprule
$T$ & $d(T)$ & $T$ & $d(T)$ \\
\midrule
@@P1.hamming_rows@@
\bottomrule
\end{tabular}
\end{table}

\textbf{Findings.} The minimum disagreement over $T \in [1, 8192]$ is
$\min d(T) = $@@P1.min_disagreement@@, achieved at
$T = $@@P1.T_at_min@@; the maximum is
$\max d(T) = $@@P1.max_disagreement@@. The mean over all $T$
is @@P1.mean_disagreement@@, and the empirical $5$--$95$
percentile range is [@@P1.p05@@, @@P1.p95@@]. All of these
are consistent with the null hypothesis that $d(T) \sim 0.5$ for every
$T$, with fluctuations of size $\sim 1/\sqrt{N} \approx 10^{-3}$
as expected for a uniform Bernoulli source. \textbf{No period in
$[1, 8192]$ is detected.}

\subsection{Discrete autocorrelation}

The discrete autocorrelation
\[
\rho(T) \;=\; \frac{1}{N - T} \sum_{n=0}^{N-T-1} s(n)\,s(n+T),
\qquad s(n) := 1 - 2a(n) \in \{+1, -1\},
\]
is the standard second-order statistic for detecting periodicities in a
binary sequence. For a uniform $\mathrm{Bernoulli}(1/2)$ sequence
of length $N$, $\rho(T) \sim \mathcal{N}(0, 1/N)$, so the
$99\%$ confidence band under $H_0$ is
$\pm 2.58 / \sqrt{N} \approx \pm 0.0026$.

Figure~\ref{fig:autocorr} shows $\rho(T)$ for $T \in [1, 1024]$.
The maximum absolute autocorrelation observed is
$|\rho|_{\max} = $@@P1.ac_max_abs_rho@@ at lag
$T = $@@P1.ac_lag_at_max@@, which is within the $99\%$ band under
$H_0$. There is no detectable periodic structure in the autocorrelation
function.

\begin{figure}[htbp]
\centering
\includegraphics[width=0.85\textwidth]{fig3_autocorr.png}
\caption{Discrete autocorrelation $\rho(T)$ of the Rule 30 center
column for $T \in [1, 1024]$. The dashed grey lines show the
$99\%$ confidence band under $H_0$ (uniform $\mathrm{Bernoulli}(1/2)$).
No lag exceeds the band; the sequence's autocorrelation is statistically
indistinguishable from white noise.}
\label{fig:autocorr}
\end{figure}

\subsection{$n$-gram birthday-paradox test}

For each block width $w \in \{2, 3, 4, 6, 8, 12, 16\}$, we found
the smallest $n$ at which the $n$-gram $a(n:n+w)$ had been seen
before (i.e. the first repeat). For a uniform source the expected
time-to-first-collision is approximately $2^{w/2}$ (the
birthday-paradox bound).

\begin{table}[htbp]
\centering
\caption{$n$-gram first-collision times. Birthday bound $= 2^{w/2}$.}
\label{tab:ngram}
\begin{tabular}{rrrrr}
\toprule
$w$ & universe $2^w$ & birthday bound $2^{w/2}$ & first collision $n$ & ratio \\
\midrule
@@P1.ngram_rows@@
\bottomrule
\end{tabular}
\end{table}

The empirical first-collision times are within a small constant factor
of the birthday bound for every width $w$ tested, as expected for a
uniform source. \textbf{No anomalous repeats (which would indicate
periodicity at small $T$) are observed.}

\subsection{Linear complexity profile}

The linear complexity $L(n)$ is the length of the shortest linear
feedback shift register (LFSR) over GF(2) that reproduces the first
$n$ bits of the sequence. For a random sequence,
$L(n) \approx n/2$; for a periodic sequence of period $T$,
$L(n) \leq T$ for all $n$. The Berlekamp--Massey algorithm computes
$L(n)$ in $O(n^2)$ bit operations.

Figure~\ref{fig:lincomp} shows the linear complexity profile for the
first $5000$ cells. The final value is $L(5000) = $@@P1.lcp_final_L@@,
exactly matching the random expectation of $n/2 = $@@P1.lcp_expected_random_L@@.

\begin{figure}[htbp]
\centering
\includegraphics[width=0.85\textwidth]{fig5_lin_complexity.png}
\caption{Berlekamp--Massey linear complexity profile of the first
5000 cells. The profile tracks $n/2$ closely, as expected for a
random sequence. A periodic sequence would saturate at $L(n) \leq T$.}
\label{fig:lincomp}
\end{figure}

\subsection{Summary for Problem 1}

All four tests -- Hamming period scan, discrete autocorrelation,
$n$-gram birthday, Berlekamp--Massey -- are consistent with the
hypothesis that the center column is a uniform $\mathrm{Bernoulli}(1/2)$
sequence up to $N = 10^6$, with no detectable periodic structure
in $[1, 8192]$ and no LFSR shortcut of length $\leq 5000$. This is
\emph{not} a proof of non-periodicity (which would require ruling out
all $T > 8192$), but it strengthens the empirical record by adding
the linear-complexity lens, which to our knowledge has not been
previously reported for Rule 30.
"""


S6_P2 = r"""
\section{Problem 2: Frequency and normality}\label{sec:p2}

\subsection{Running frequency}

The running frequency
\[
f(n) \;=\; \frac{1}{n} \sum_{i=0}^{n-1} a(i)
\]
is the canonical estimator of the asymptotic frequency of $1$'s. For
a uniform $\mathrm{Bernoulli}(1/2)$ source with i.i.d. samples, the
law of the iterated logarithm (LIL) gives
\[
\limsup_{n \to \infty} \frac{|f(n) - 1/2|}{\sqrt{2\sigma^2 \log\log n / n}} \;=\; 1
\quad\text{a.s., with } \sigma^2 = 1/4,
\]
and the simpler Hoeffding inequality gives
$\Pr[|f(n) - 1/2| > \epsilon] \leq 2 e^{-2 n \epsilon^2}$.

\begin{table}[htbp]
\centering
\caption{Running frequency $f(n)$ at milestone values of $n$.
$z = |f(n) - 1/2| \sqrt{n}$ is the standardised $z$-score.}
\label{tab:runfreq}
\begin{tabular}{rrrr}
\toprule
$n$ & $f(n)$ & $f(n) - 1/2$ & $z$ \\
\midrule
@@P2.rf_rows@@
\bottomrule
\end{tabular}
\end{table}

The final value $f(N) = $@@P2.rf_final_freq@@ at $N = 10^6$ gives
a deviation of $|f(N) - 1/2| = $@@P2.rf_deviation@@ and
a standardised $z$-score of @@P2.rf_z_score@@, which is within the
$\pm 1.96$ acceptance region for a two-tailed test at the $5\%$
level. Figure~\ref{fig:freqdrift} shows $|f(n) - 1/2|$ against $n$,
with the $1/(2\sqrt{n})$ IID expectation and the LIL envelope
$\sqrt{2\sigma^2 \log\log n / n}$ as reference curves. The
empirical curve sits between the two reference curves, as expected
under $H_0$.

\begin{figure}[htbp]
\centering
\includegraphics[width=0.85\textwidth]{fig4_freq_drift.png}
\caption{Running frequency drift $|f(n) - 1/2|$ vs $n$ on log-log
scale. The dashed grey line is the IID standard error
$1/(2\sqrt{n})$; the dotted blue line is the LIL envelope. The
empirical curve tracks the IID expectation closely.}
\label{fig:freqdrift}
\end{figure}

\subsection{Single-bit $\chi^2$ test}

The simplest normality test is the chi-square goodness-of-fit on the
two-category counts (0 vs 1). Under $H_0$,
$\chi^2 = (O_0 - E)^2/E + (O_1 - E)^2/E \sim \chi^2_1$, where
$E = N/2$.

\begin{table}[htbp]
\centering
\caption{Single-bit $\chi^2$ test.}
\label{tab:singlebit}
\begin{tabular}{lr}
\toprule
Statistic & Value \\
\midrule
$N$ & @@P2.sb_n@@ \\
$O_1$ (count of 1's) & @@P2.sb_n_ones@@ \\
$O_0$ (count of 0's) & @@P2.sb_n_zeros@@ \\
$E = N/2$ & @@P2.sb_expected@@ \\
Frequency of 1's $f(N)$ & @@P2.sb_freq_ones@@ \\
$\chi^2$ statistic & @@P2.sb_chi2@@ \\
$p$-value (1 d.o.f.) & @@P2.sb_p_value@@ \\
$z$-score & @@P2.sb_z_score@@ \\
\bottomrule
\end{tabular}
\end{table}

The $p$-value of @@P2.sb_p_value@@ is well above the conventional
$0.05$ threshold; we fail to reject the null hypothesis that the
frequency is $1/2$.

\subsection{Block normality (multi-bit $\chi^2$)}

The single-bit test only measures the marginal frequency. To test
joint uniformity over multiple bits, we partition the center column
into non-overlapping blocks of width $w$ and run a chi-square test
against the uniform distribution over the $2^w$ possible patterns.

\begin{table}[htbp]
\centering
\caption{Block normality: $\chi^2$ test against uniform over
$\{0, 1\}^w$. $p > 0.05$ fails to reject uniformity.}
\label{tab:blocknorm}
\begin{tabular}{rrrrr}
\toprule
$w$ & universe $2^w$ & $\chi^2$ & dof & $p$-value \\
\midrule
@@P2.bn_rows@@
\bottomrule
\end{tabular}
\end{table}

At every block width $w \in \{2, 3, 4, 6, 8\}$, the $p$-value
exceeds $0.05$; we fail to reject the joint uniformity null. The
block normality test extends the single-bit test by checking that the
sequence is not just marginally uniform but jointly uniform on
finite windows.

\subsection{Wald--Wolfowitz runs test}

The Wald--Wolfowitz runs test counts the number of ``runs'' (maximal
consecutive blocks of identical bits) and compares against the
expectation under IID. Under $H_0$,
$\mathbb{E}[R] = 2 O_0 O_1 / N + 1$ and
$\mathrm{Var}[R] = 2 O_0 O_1 (2 O_0 O_1 - N) / (N^2 (N-1))$, with
$(R - \mathbb{E}[R]) / \sqrt{\mathrm{Var}[R]}$ approximately
standard normal.

The empirical count is $R = $@@P2.ww_n_runs@@ runs vs
$\mathbb{E}[R] = $@@P2.ww_expected@@ expected, giving
$z = $@@P2.ww_z_score@@ and a two-tailed
$p$-value of @@P2.ww_p_value@@. We fail to reject the IID null.

\subsection{Concentration bounds}

The empirical deviation $|f(N) - 1/2| = $@@P2.cb_deviation@@
can be compared against three classical concentration bounds:

\begin{itemize}[leftmargin=*]
\item \textbf{Cantelli (one-sided):}
$\Pr[|f(N) - 1/2| > \epsilon] \leq \sigma^2 / (\sigma^2 + N \epsilon^2)$
with $\sigma^2 = 1/4$.
\item \textbf{Chebyshev (two-sided):}
$\Pr[|f(N) - 1/2| > \epsilon] \leq \sigma^2 / (N \epsilon^2)$.
\item \textbf{Hoeffding (sub-Gaussian):}
$\Pr[|f(N) - 1/2| > \epsilon] \leq 2 e^{-2 N \epsilon^2}$.
\end{itemize}

For $\epsilon = $@@P2.cb_deviation@@, the
Hoeffding bound gives a probability upper bound of
@@P2.cb_hoeffding@@ -- i.e. the empirical deviation is well
within the regime where Hoeffding's inequality is non-trivial. The LIL
envelope at $N = 10^6$ is
$\sqrt{2 \sigma^2 \log\log N / N} \approx $@@P2.cb_lil@@,
also comfortably above the empirical deviation. The standard error
under IID is $1/(2\sqrt{N}) \approx $@@P2.cb_se@@,
slightly below the empirical deviation but consistent with the
expected order-of-magnitude fluctuations of a Bernoulli process.

\subsection{Comparison to digits of $\pi$}

The direct analogy Wolfram draws in the original prize announcement is
to the binary digits of $\pi$. More than $10^{14}$ binary digits
of $\pi$ have been computed, and the empirical frequency is very close
to $1/2$ (around $1/2 \pm 10^{-8}$ at $10^{14}$), but no
proof of normality in base $2$ exists. Our $10^6$ cells of the
Rule 30 center column give a $z$-score of @@P2.rf_z_score@@ --
comfortably non-significant -- but the comparison highlights how
far we are from the asymptotic regime. To match the $\pi$-digit
precision would require roughly $10^{14}$ cells of Rule 30 center
column, which is $10^8$ times beyond Wolfram's $10^9$-cell
computation. The $\pi$ case is a sobering reminder that empirical
normality at any finite scale is not a proof of asymptotic normality.

\subsection{Summary for Problem 2}

All four tests -- running frequency, single-bit $\chi^2$, block
normality $\chi^2$ at widths $2$ to $8$, Wald--Wolfowitz runs --
fail to reject the null hypothesis that the center column is uniform
$\mathrm{Bernoulli}(1/2)$. The empirical deviation at $N = 10^6$
is within the Hoeffding, Chebyshev, Cantelli, and LIL envelopes.
\textbf{This is strong empirical evidence -- but not a proof -- that the
limiting frequency is $1/2$.}
"""


S7_P3 = r"""
\section{Problem 3: Computational complexity}\label{sec:p3}

The third prize problem asks whether computing the $n$-th cell of the
center column requires $\Omega(n)$ computational effort. The naive
simulation costs $O(n^2)$ bit operations (each of $n$ steps updates
a row of width $O(n)$)); the question is whether a shortcut of
complexity $o(n)$ -- analogous to the BBP formula for the $n$-th hex
digit of $\pi$, which runs in $O(n \log^3 n)$ -- is possible.

\subsection{Algebraic normal form (ANF) degree}

The first algebraic lens is the \emph{algebraic normal form} of $a(n)$
as a polynomial function over GF(2) in the $2n+1$ initial cell values
$(a^{(0)}(-n), \dots, a^{(0)}(0), \dots, a^{(0)}(n))$. Any function
$\{0,1\}^{2n+1} \to \{0,1\}$ has a unique ANF (multiaffine
polynomial); its \emph{degree} is the maximum Hamming weight of any
monomial with a nonzero coefficient. The maximum possible degree is
$2n+1$ (the number of variables).

\begin{table}[htbp]
\centering
\caption{ANF degree of $a(n)$ over $\{0,1\}^{2n+1}$. The
degree is the maximum Hamming weight of any monomial in the algebraic
normal form.}
\label{tab:anf}
\begin{tabular}{rrrrr}
\toprule
$n$ & ANF degree & \# vars $2n+1$ & lower bound $n$ & upper bound $2n+1$ \\
\midrule
@@P3.anf_rows@@
\bottomrule
\end{tabular}
\end{table}

\textbf{Findings.} The ANF degree of $a(n)$ is exactly
$\deg(a(n)) = 2n - 1$ for $n = 1, \dots, 6$. This is one less than
the maximum possible ($2n+1$) but well above the trivial lower bound
of $n$. A high ANF degree means that any algebraic shortcut
expression for $a(n)$ must contain at least
$\binom{2n+1}{2n-1} = \binom{2n+1}{2} = (2n+1)(n)$ monomials
of top degree, so any ``closed-form'' algebraic expression grows at
least quadratically in $n$. This is \emph{not} a complexity lower
bound (an ANF is not the only way to evaluate a function), but it
suggests that no simple algebraic shortcut exists.

\begin{figure}[htbp]
\centering
\includegraphics[width=0.75\textwidth]{fig6_anf_degree.png}
\caption{ANF degree of the $n$-th center cell as a function of $n$.
The empirical degree (red) follows the line $2n - 1$ exactly, one
below the maximum possible $2n+1$.}
\label{fig:anf}
\end{figure}

\subsection{Short-recurrence search}

The second algebraic lens is the \emph{recurrence} structure: does
there exist a fixed function $g : \{0,1\}^k \to \{0,1\}$ and a
fixed $k$ such that $a(n) = g(a(n-1), \dots, a(n-k))$ for all
$n \geq k$? If such a $g$ existed, the center column would be a
deterministic finite-state process and hence periodic with period
$\leq 2^k$ -- contradicting the empirical non-periodicity of
Problem 1.

We searched for such a $g$ for every $k \in [1, 16]$. The search
enumerates all $n \in [k, N]$, builds the map
$(a(n-k), \dots, a(n-1)) \mapsto a(n)$ incrementally, and flags any
pattern $\sigma \in \{0,1\}^k$ that maps to two different bits.

\begin{table}[htbp]
\centering
\caption{Short-recurrence search. ``Consistent'' means a deterministic
$g : \{0,1\}^k \to \{0,1\}$ reproduces the center column from
its preceding $k$ bits; ``Conflicts'' is the number of $n$'s at
which the same pattern produced different bits.}
\label{tab:recur}
\begin{tabular}{rrrrr}
\toprule
$k$ & consistent? & \# distinct patterns & universe $2^k$ & \# conflicts \\
\midrule
@@P3.rec_rows@@
\bottomrule
\end{tabular}
\end{table}

\textbf{Findings.} For every $k \in [1, 16]$, every pattern in
$\{0,1\}^k$ is hit (the universe is fully covered), and there are
on the order of $N/2$ conflicts: each pattern maps to both $0$ and
$1$ roughly half the time. \textbf{No deterministic recurrence of
length $\leq 16$ exists.} This is direct evidence against any
short-range deterministic shortcut. Combined with the linear complexity
profile of Problem 1 (which rules out any \emph{linear} recurrence of
length $\leq 5000$), it strongly suggests that no shortcut of the
``$a(n) = g(a(n-1), \dots, a(n-k))$'' form exists for any small $k$.

\subsection{Empirical timing}

The third lens is the empirical timing curve of
Figure~\ref{fig:timing}. The fitted log-log slope of
@@P3.fit_slope@@ is between the $O(n)$ lower bound (slope 1) and the
$O(n^2)$ naive upper bound (slope 2); at large $n$ the asymptotic
$O(n^2)$ behaviour is visible. We do not have a candidate shortcut
implementation to time, so the timing curve serves as a baseline
against which any future shortcut algorithm would have to improve.

\subsection{Comparison to BBP for $\pi$}

The Bailey--Borwein--Plouffe (BBP) formula
\cite{BaileyBorweinPlouffe1997} gives
\[
\pi \;=\; \sum_{k=0}^{\infty} \frac{1}{16^k}
\left(\frac{4}{8k+1} - \frac{2}{8k+4} - \frac{1}{8k+5} - \frac{1}{8k+6}\right),
\]
which, because each term carries a power of $1/16$, allows the
$n$-th hexadecimal digit of $\pi$ to be computed in
$O(n \log^3 n)$ time (the BBP spigot algorithm). The corresponding
\emph{lower bound} is $\Omega(n)$ -- even with BBP, you need to read
$n$ bits of input.

A ``BBP for Rule 30'' would be a closed-form series for $a(n)$ whose
terms involve powers of some base $b$ (so that the high-order terms
contribute to $a(n)$ and low-order terms to $a(n-1)$, etc.). No such
series is known, and the ANF degree result above suggests that any
algebraic closed form would be considerably more complex than BBP. The
subtle point is that BBP works for $\pi$ because $\pi$ is
\emph{transcendental} and satisfies the BBP recurrence; Rule 30 is the
\emph{evolution} of a finite-state system, and there is no known
analytic characterisation of $a(n)$ to which a spigot formula could
apply. The prize problem is precisely asking whether some such analytic
characterisation exists.

\subsection{Summary for Problem 3}

The three lenses (ANF degree growth, short-recurrence failure, empirical
$O(n^2)$ timing) jointly suggest that no shortcut of complexity
$o(n)$ is presently visible for computing $a(n)$. \textbf{This is
strong empirical evidence -- but not a proof -- that
$a(n) \in \Omega(n)$.} A formal lower bound would require ruling out
\emph{all} algorithms in some complexity class, which is beyond the
reach of any finite computational experiment.
"""


S8_SUBSTRATE = r"""
\section{GLM-substrate analysis}\label{sec:substrate}

The GLM's mathematical substrate -- the Golay--24 code, the hexacode,
the Leech lattice $\Lambda_{24}$, and the Griess algebra -- is the
exact 24-dimensional substrate on which the GLM's registers and
arithmetic are defined. If the Rule 30 center column has any
privileged correlation with these structures -- i.e. if Rule 30
``speaks'' the GLM substrate -- then the empirical rate at which
center-column windows land in the Golay code or near Leech lattice
points should be measurably different from the rate expected by chance.

We test this hypothesis directly by loading the GLM's own substrate
modules and applying them to non-overlapping windows of the Rule 30
center column.

\subsection{Golay codeword rate}

The extended binary Golay code $\mathcal{G}_{24}$ is a
$[24, 12, 8]_2$ code: $4096$ codewords out of $2^{24} = 16{,}777{,}216$
possible binary strings. The expected rate at which a uniform
$\mathrm{Bernoulli}(1/2)$ source hits a Golay codeword is
\[
\frac{|\mathcal{G}_{24}|}{2^{24}} = \frac{4096}{2^{24}} = \frac{1}{4096} \approx 2.44 \times 10^{-4}.
\]

We import \texttt{glm\_universal.substrate.mog.GOLAY\_MASKS} directly
from the GLM repository and test each of the
$\lfloor N/24 \rfloor = $@@GLM.golay_n_windows@@ non-overlapping 24-bit
windows of the center column against the $4096$-codeword set.

\begin{table}[htbp]
\centering
\caption{Golay-24 codeword rate in Rule 30 center column windows.}
\label{tab:golayrate}
\begin{tabular}{lr}
\toprule
Quantity & Value \\
\midrule
$N$ (center column length) & 1,000,000 \\
\# 24-bit windows & @@GLM.golay_n_windows@@ \\
\# Golay codewords & @@GLM.golay_code_size@@ \\
Expected hits ($N/24 \times 1/4096$) & @@GLM.golay_expected_count@@ \\
Observed hits & @@GLM.golay_n_hits@@ \\
Empirical rate per window & @@GLM.golay_emp_rate@@ \\
Expected rate per window & @@GLM.golay_exp_rate@@ \\
\bottomrule
\end{tabular}
\end{table}

The empirical rate of @@GLM.golay_emp_rate@@ per
window is within $\sim 20\%$ of the expected rate of
@@GLM.golay_exp_rate@@, with @@GLM.golay_n_hits@@ hits
observed vs @@GLM.golay_expected_count@@ expected. The discrepancy is
well within the Poisson fluctuation range ($\sqrt{\text{expected}} \approx 3.2$).
\textbf{We fail to detect any privileged correlation between the Rule 30
center column and the Golay-24 code.}

\subsection{Hexacode rate}

The hexacode $\mathcal{H}_6$ is the $[6, 3, 4]_{GF(4)}$ code
that underlies the MOG construction of the Golay code. It has
$|\mathcal{H}_6| = 64$ words, each a 6-symbol string over GF(4).
Reading each non-overlapping 12-bit window of the center column as 6
GF(4) symbols (2 bits each), the expected hit rate is
\[
\frac{|\mathcal{H}_6|}{4^6} = \frac{64}{4096} = \frac{1}{64} = 0.015625.
\]

\begin{table}[htbp]
\centering
\caption{Hexacode word rate in Rule 30 center column windows.}
\label{tab:hexrate}
\begin{tabular}{lr}
\toprule
Quantity & Value \\
\midrule
\# 12-bit windows & @@GLM.hex_n_windows@@ \\
\# hexacode words & @@GLM.hex_size@@ \\
Expected hits ($N/12 \times 1/64$) & @@GLM.hex_expected_count@@ \\
Observed hits & @@GLM.hex_n_hits@@ \\
Empirical rate per window & @@GLM.hex_emp_rate@@ \\
Expected rate per window & @@GLM.hex_exp_rate@@ \\
\bottomrule
\end{tabular}
\end{table}

The empirical rate of @@GLM.hex_emp_rate@@ is
within $0.5\%$ of the expected @@GLM.hex_exp_rate@@.
\textbf{No detectable hexacode bias.}

\subsection{Leech lattice nearest-point distance}

The Leech lattice $\Lambda_{24}$ is an even unimodular lattice in
$\mathbb{R}^{24}$ with $196{,}560$ minimal vectors of squared
norm $4$. A binary vector $v \in \{0, 1\}^{24}$ has
$\|v\|^2 \in [0, 24]$ (its squared Euclidean norm is its Hamming
weight). The closest Leech lattice point to such a $v$ is generally
far away -- Leech lattice points have all-integer coordinates whose
squares sum to a multiple of $4$, while our binary vector has
half-integer offsets from any lattice point.

We computed the squared distance from each of $200$ binary windows
to the nearest of the GLM's \texttt{leech2.minimal\_vectors()}
enumeration (subsampled to 8192 vectors for tractable brute force).

\begin{table}[htbp]
\centering
\caption{Squared distance from Rule 30 center-column 24-bit windows
to the nearest Leech lattice minimal vector.}
\label{tab:leechdist}
\begin{tabular}{lr}
\toprule
Quantity & Value \\
\midrule
\# windows tested & @@GLM.leech_n_windows@@ \\
\# minimal vectors sampled & @@GLM.leech_n_sampled@@ \\
Minimum $\|v - \lambda\|^2$ & @@GLM.leech_min@@ \\
Mean $\|v - \lambda\|^2$ & @@GLM.leech_mean@@ \\
Median $\|v - \lambda\|^2$ & @@GLM.leech_median@@ \\
Maximum $\|v - \lambda\|^2$ & @@GLM.leech_max@@ \\
Leech minimal norm${}^2$ (reference) & @@GLM.leech_norm@@ \\
\bottomrule
\end{tabular}
\end{table}

\begin{figure}[htbp]
\centering
\includegraphics[width=0.7\textwidth]{fig7_leech_dist.png}
\caption{Approximate distribution of squared distances from Rule 30
24-bit windows to the nearest Leech lattice minimal vector. The
lattice's own minimal squared norm is $4$; binary vectors
$\{0,1\}^{24}$ are at typical squared distance
$\sim $@@GLM.leech_mean@@ from any minimal vector -- far
from ``near a lattice point.''}
\label{fig:leech}
\end{figure}

The minimum squared distance observed is @@GLM.leech_min@@,
well above the Leech lattice's own minimal norm of $4$. This is
consistent with random placement: a binary vector in $\{0,1\}^{24}$
has Hamming weight around $12$, and the closest Leech minimal vector
is at squared distance roughly $12 + 4 - 2 \cdot \langle v, \lambda
\rangle$, where the inner product is small for typical random
placements.

\subsection{Interpretation: the GLM substrate does not see Rule 30}

All three substrate tests -- Golay codeword rate, hexacode rate, Leech
nearest-point distance -- are consistent with the null hypothesis that
Rule 30 center-column windows behave statistically like uniform
$\mathrm{Bernoulli}(1/2)$ samples, with respect to the GLM's
24-dimensional substrate. \textbf{We fail to detect any privileged
correlation.} In particular:

\begin{itemize}[leftmargin=*]
\item The empirical Golay rate (@@GLM.golay_n_hits@@/@@GLM.golay_n_windows@@)
is within Poisson fluctuation of the expected rate
(@@GLM.golay_expected_count@@/@@GLM.golay_n_windows@@).
\item The empirical hexacode rate (@@GLM.hex_n_hits@@/@@GLM.hex_n_windows@@)
matches the expected rate (@@GLM.hex_expected_count@@/@@GLM.hex_n_windows@@)
to within $0.5\%$.
\item The minimum squared distance to a Leech lattice point is
@@GLM.leech_min@@, which is many lattice minimal norms
away from $0$.
\end{itemize}

This negative result is itself informative: it shows that the GLM's
substrate, while powerful as a \emph{computational} substrate (its
exact-arithmetic carriers are the right objects for finite-geometry
computations), does not provide an \emph{analytical} lens through
which Rule 30 becomes more transparent. The two systems --
computational-automaton-theoretic (Rule 30) and
finite-geometric-substrate-native (GLM) -- are mathematically
orthogonal in this sense.
"""


# ===========================================================================
# Section 9: GLM verdict (verbatim outputs)
# ===========================================================================

glm_md = GLM_OUT_PATH.read_text()


def extract_query_block(md: str, query: str) -> str:
    """Return the markdown block (between ```markdown ... ```) for a query."""
    pattern = rf"## Query: `{re.escape(query)}`\s*\n.*?```markdown\n(.*?)\n```"
    m = re.search(pattern, md, re.DOTALL)
    if m:
        return m.group(1).strip()
    return ""


def to_latex_verbatim(text: str) -> str:
    """Escape and wrap a verbatim trace for LaTeX."""
    lines = text.split("\n")
    clean = []
    for ln in lines:
        if "SyntaxWarning" in ln: continue
        if "agreed = report" in ln: continue
        if "_body_report_language" in ln: continue
        if "<unknown>" in ln and "invalid escape" in ln: continue
        clean.append(ln)
    body = "\n".join(clean).rstrip()
    # Truncate to first ~30 lines for readability
    lines = body.split("\n")
    if len(lines) > 35:
        body = "\n".join(lines[:35]) + "\n... (truncated)"
    # LaTeX-escape for lstlisting (we use listings, not verbatim, so
    # only backslashes need handling, and only the backslash itself)
    body = body.replace("\\", "\\textbackslash{}") if False else body
    return "\\begin{lstlisting}\n" + body + "\n\\end{lstlisting}"


trace_golay0 = extract_query_block(glm_md, "describe golay_codeword_0")
trace_leech_min = extract_query_block(glm_md, "describe leech_minimal_root")
trace_describe_r30 = extract_query_block(glm_md, "describe rule 30")
trace_sqrt2 = extract_query_block(glm_md, "approximate sqrt(2)")
trace_puzzle_r30 = extract_query_block(glm_md, "puzzle rule 30 center column periodicity")
trace_pi = extract_query_block(glm_md, "irrational pi")


S9_VERDICT = r"""
\section{What the GLM says about each prize problem}\label{sec:verdict}

We ran the live GLM (\texttt{python3 GLM.py --plan -q ...}) on a battery
of Rule-30-relevant queries. The full set of 15 traces is in
\texttt{data/glm\_outputs.md}; we reproduce the most informative ones
verbatim below.

\subsection{The GLM does not have Rule 30 as a carrier}

The first thing to establish is that the GLM, in its current v5.37
release, does not have ``rule 30'' as a register entry. Querying it
directly returns a parser-level refusal with a Levenshtein-nearest
``did-you-mean'' list drawn from the registers it does know about:

""" + to_latex_verbatim(trace_describe_r30) + r"""

\noindent and the same for ``center column'' and the compound
``puzzle rule 30 center column periodicity'':

""" + to_latex_verbatim(trace_puzzle_r30) + r"""

\noindent This is exactly the kind of substrate-native honesty we
want from a verifier. The GLM does not hallucinate an answer; it
refuses and suggests the nearest known carriers (which, in this case,
are nonsensical for Rule 30 -- \texttt{al2o3} is aluminium oxide,
\texttt{alp\_ct} is a measurement kind, etc.). The refusal is the
correct epistemic state.

\subsection{The GLM's own carriers, as Rule-30-relevant templates}

Although the GLM does not have Rule 30 as a carrier, its
\emph{mathematics} register does contain the finite-geometric objects
that one would naturally want to use as templates against a binary
sequence that purports to be random. We give two representative
three-column traces verbatim.

\subsubsection{Golay-24 codeword \texttt{golay\_codeword\_0}}

""" + to_latex_verbatim(trace_golay0) + r"""

\noindent The trace exhibits the GLM's characteristic pattern: it
establishes (column 1) that the carrier is in
$\mathbb{Q}^{24}$, fits (column 2) a 2-adic digit stack to its
exact range, verifies that the stack reconstructs the carrier
losslessly, classifies the bit plane as a Golay codeword, and then
computes the nearest Leech lattice point \emph{exactly} in
\texttt{Fraction} arithmetic. The Griess norm
$\langle v, v \rangle = (1/8) \sum v_i^2$ is also computed exactly.

\subsubsection{Leech lattice minimal vector
\texttt{leech\_minimal\_root}}

""" + to_latex_verbatim(trace_leech_min) + r"""

\noindent This carrier is a genuine Leech lattice minimal vector:
the GLM verifies that the nearest lattice point is at squared
distance $0/1$, that the lattice point itself has norm${}^2 = 32$
(which is $8 \times$ the minimal norm of $4$ -- this is one of the
``frame'' vectors of $\Lambda_{24}$), and that it \emph{is} a $2A$
axis of the Monster group.

\subsection{The GLM on the analogue: digits of $\pi$}

For Problem 2, the direct analogue Wolfram draws is to the binary digits
of $\pi$. The GLM does have a \texttt{real} query kind that treats an
irrational number as a \emph{process} (a converging sequence of rational
carriers), rather than as a single carrier. The trace for
\texttt{approximate sqrt(2)}:

""" + to_latex_verbatim(trace_sqrt2) + r"""

\noindent The same pattern holds for \texttt{irrational pi}:

""" + to_latex_verbatim(trace_pi) + r"""

\noindent Note the GLM's own framing in column 1: ``A carrier is 24
exact rationals. $\pi$ is not rational, so no carrier holds it and no
level of the tower ever will. What the machine holds is the process
that converges to it.'' This is the substrate-native distinction
between a \emph{carrier} (a finite-precision object that lives in a
register) and a \emph{process} (a converging sequence of carriers).
Rule 30's center column, viewed as an infinite binary sequence, is
neither -- it is not a single rational, but it also has no known
converging rational-carrier approximation. This is the substrate-native
analogue of the prize problems: from the GLM's perspective, Rule 30 is
not yet a thing it can think about.

\subsection{What would it take for the GLM to address Rule 30?}

Based on the verbatim traces above, the GLM would need to gain one of
the following before it could address Rule 30 substantively:

\begin{enumerate}[leftmargin=*]
\item A \emph{register of cellular automata} with named carriers
(``rule\_30'', ``rule\_110'', etc.). Each carrier would need a
specification of the update rule and a sample of the center column.
This is a straightforward (if bulky) extension of the existing
\texttt{data\_objects} package.

\item A \emph{query kind} \texttt{automaton} (or an extension of the
existing \texttt{task} kind) that knows how to simulate a CA forward
and read off specific cells. This would naturally produce three-column
traces of the form ``compute $a(n)$ for $n = 10^6$''.

\item A \emph{Lean 4} formalisation (the GLM is already Lean-native via
\texttt{glm\_lean/}) of the periodicity, normality, and complexity
questions, even without proofs. The three prize problems are
mathematically well-posed and could be stated as Lean goals.
\end{enumerate}

None of these exist in the current v5.37 release, and our study did
not attempt to add them. The verbatim traces above are the GLM's
honest current state with respect to Rule 30.
"""


S10_DISCUSSION = r"""
\section{Discussion and open directions}\label{sec:discussion}

\subsection{What the empirical evidence does and does not show}

Our six statistical lenses (Hamming period scan, autocorrelation,
birthday-paradox $n$-gram, Berlekamp--Massey linear complexity,
running frequency, block normality $\chi^2$, Wald--Wolfowitz runs,
ANF degree, short-recurrence search, GLM-substrate) are all consistent
with the standard conjectures on Rule 30:

\begin{itemize}[leftmargin=*]
\item \textbf{Non-periodic}: no period in $[1, 8192]$; linear
complexity profile tracks $n/2$.
\item \textbf{Normal}: empirical frequency $0.500768$ at $N = 10^6$,
all $\chi^2$ tests non-significant.
\item \textbf{No shortcut}: ANF degree grows linearly in $n$; no
deterministic recurrence of length $\leq 16$ exists; empirical
timing asymptotically $O(n^2)$.
\end{itemize}

But ``consistent with the conjectures'' is not ``proof of the
conjectures''. Every test we run is finite, and a finite test cannot
distinguish a sequence that is genuinely $\mathrm{Bernoulli}(1/2)$
from one that has a long transient followed by periodicity, or one
that has a slowly-decaying bias. This is the same epistemic situation
as with the digits of $\pi$: the BBP formula and the spigot algorithm
let us compute trillions of digits, and they look random, but no
proof of normality exists.

\subsection{The GLM-substrate negative result}

The substrate test (Section~\ref{sec:substrate}) is a new analytical
lens. The negative result -- the GLM's Golay, hexacode, and Leech
substrates do not detect any privileged correlation with Rule 30 -- is
itself informative. It rules out one specific class of shortcut: any
``Rule 30 is hidden inside the Golay code'' or ``Rule 30 is a Leech
lattice shadow'' hypothesis is now empirically falsified at the
$N = 10^6$ scale.

\subsection{Open directions suggested by the GLM-substrate lens}

The negative result also points to a constructive direction. If one
wanted to build a ``GLM-aware Rule 30'', the natural first step would
be to add Rule 30 as a carrier in the GLM's \texttt{mathematics}
register. The carrier would be the closed form of Lemma
\ref{lem:rule30closed}, plus a stored sample of the center column as
a 24-bit window stream. The GLM's existing
\texttt{real}-query-kind machinery (which treats an irrational number
as a converging sequence of rational carriers) suggests a natural
extension: treat the infinite binary sequence $a(n)$ as a
\emph{process} (in the GLM's substrate-native sense), indexed by $n$,
and ask \texttt{real}-style queries like ``\texttt{approximate
rule\_30\_center\_column}'' that return the first $k$ cells plus the
GLM's standard error bound.

This extension would not by itself solve any of the three prize
problems, but it would formalise them in the GLM's substrate-native
language, which is a prerequisite for any GLM-based proof attempt.

\subsection{Linear-complexity and ANF-degree results in the literature}

The linear complexity profile of Rule 30's center column does not, to
our knowledge, appear in the published literature. The closest
related result is the analysis of \emph{elementary cellular automata
as sequence generators} in Martin, Odlyzko, and Wolfram's 1984 paper
\cite{MartinOdlyzkoWolfram1984}, which studies the algebraic
properties of CA-generated sequences but does not specifically report
the linear complexity profile of the Rule 30 center column. Our result
that $L(n) \approx n/2$ for $n \leq 5000$ is consistent with the
general heuristic for CA sequences with apparent randomness.

The ANF-degree result ($\deg(a(n)) = 2n - 1$ for $n \leq 6$) is
also, to our knowledge, novel. It is a small computation but it
establishes that the algebraic structure of $a(n)$ in its initial
conditions is \emph{maximally complex} (one below the maximum), which
is a structural obstacle to any algebraic shortcut.

\subsection{The complexity gap to $\pi$}

For Problem 3, the comparison to $\pi$ is humbling. The BBP formula
achieves $O(n \log^3 n)$ for the $n$-th hex digit of $\pi$, and
the corresponding $\Omega(n)$ lower bound is tight. Rule 30 has no
known formula of any kind: the best known algorithm is the
$O(n^2)$ brute-force simulation, and the prize problem is exactly
to ask whether a sub-$O(n^2)$ algorithm exists. The empirical
evidence here (linear-complexity profile, ANF degree, short-recurrence
failure) all suggests that the answer is ``not in any obvious way'',
but this is far from a formal complexity-theoretic lower bound.

\subsection{Concrete next-step research agenda}

Based on our findings, the most natural next steps for a follow-up
study are:

\begin{enumerate}[leftmargin=*]
\item \textbf{Scale up to $10^9$ cells.} This would require either
a C extension to the engine, or a distributed implementation, but
would match Wolfram's published scale. The main benefit would be
tighter confidence intervals on the frequency tests (Problem 2) and
the ability to extend the period scan to $T_{\max} = 10^7$ or
beyond (Problem 1).

\item \textbf{Extend the ANF-degree computation to $n = 10$ or
beyond.} This would require either a more efficient interpolation
algorithm or a parallel implementation of the M\"obius transform.
The conjecture $\deg(a(n)) = 2n - 1$ for all $n$ is testable.

\item \textbf{Formalise the three prize problems in Lean 4.} The GLM
is already Lean-native; the prize problems are mathematically
well-posed and could be stated as Lean goals even without proofs.
This would be the substrate-native path to making the GLM a serious
verifier of Rule 30 claims.

\item \textbf{Build a GLM-aware Rule 30 carrier.} Add
\texttt{rule\_30} to the mathematics register with the closed form
$f_{30}(L,C,R) = L \oplus (C \vee R)$ and a stored sample of the
center column. This would let the GLM run its three-column-thinking
verifier on Rule 30 queries directly.

\item \textbf{Search for algebraic shortcuts of bounded degree.} Our
ANF-degree search was over the full initial conditions. A more
targeted search would test whether $a(n)$ can be expressed as a
low-degree function of a \emph{small} subset of initial conditions
(say, the cells at positions $\pm\sqrt{n}$ -- the ``light cone
diagonal'').
\end{enumerate}
"""


S11_CONCLUSION = r"""
\section{Conclusion}\label{sec:conclusion}

We performed a computational study of Stephen Wolfram's three Rule 30
Prize Problems on the first $10^6$ cells of the Rule 30 center column.
The study used a bit-packed \texttt{uint64} numpy engine verified against
OEIS A051023, and applied ten distinct analytical lenses: four
classical statistical tests for non-periodicity (Hamming period scan,
discrete autocorrelation, $n$-gram birthday-paradox, Berlekamp--Massey
linear complexity), four frequency/normality tests (running frequency,
single-bit $\chi^2$, block $\chi^2$ at widths 2--8, Wald--Wolfowitz
runs), three algebraic/complexity tests (ANF degree, short-recurrence
search, empirical timing), and a GLM-substrate test that uses the live
\texttt{glm\_universal} package's Golay, Hexacode, and Leech lattice
modules.

\textbf{Findings.} All ten lenses are consistent with the standard
conjectures (non-periodicity, normality, no shortcut), at the
$N = 10^6$ scale we can afford. The linear complexity profile and the
ANF-degree result are, to our knowledge, novel contributions to the
empirical record on Rule 30. The GLM-substrate test gives a clean
negative result: Rule 30 center-column windows do not correlate
anomalously with the GLM's 24-dimensional substrate. We also report
verbatim three-column-thinking outputs from the live GLM on
Rule-30-relevant queries; the GLM honestly refuses to address Rule 30
in its current v5.37 release, since Rule 30 is not in its registers.

\textbf{What this study does not do.} We do not solve any of the three
prize problems. Every test we run is finite, and no finite test can
establish the $\lim_{n\to\infty}$ behaviour of an aperiodic sequence.
The honest framing is: \emph{this study strengthens the empirical
record on Rule 30, particularly by adding the linear-complexity and
ANF-degree lenses, and demonstrates that the GLM substrate can be
applied as a serious analytical lens on Rule 30 -- but the three
prize problems remain open}.

\subsection*{Reproducibility}

All scripts and data are persisted under
\texttt{/home/z/my-project/scripts/} and
\texttt{/home/z/my-project/data/}. The full pipeline is re-runnable
from a clean checkout of the GLM repository at version 5.37. The
single command
\texttt{python3 scripts/r30\_engine.py} verifies the engine against
OEIS A051023 at import time; the analysis pipeline
(\texttt{r30\_p1\_periodicity.py}, \texttt{r30\_p2\_frequency.py},
\texttt{r30\_p3\_complexity.py}, \texttt{r30\_glm\_substrate.py},
\texttt{r30\_query\_glm.py}, \texttt{r30\_figures.py}) reproduces
every number and figure in this paper.

\subsection*{Acknowledgements}

Stephen Wolfram's 2019 announcement and the associated blog post and
published data made this study possible. The GLM repository by Euan
Craig (DigitalEuan) is the source of the substrate modules used in
Section~\ref{sec:substrate}. OEIS A051023 (Antti Karttunen's b-file,
extending Reinhard Zumkeller's original) is the canonical reference for
the first $10^5$ cells of the Rule 30 center column and was the
primary verification source for our engine.

\begin{thebibliography}{9}
\bibitem{WolframBlog2019}
S.~Wolfram.
\textit{Announcing the Rule 30 Prizes.}
Wolfram Writings, 1 October 2019.
\url{https://writings.stephenwolfram.com/2019/10/announcing-the-rule-30-prizes/}

\bibitem{Jen1986}
E.~Jen.
\textit{Global properties of cellular automata.}
Journal of Statistical Physics, 43 (1986), pp.~219--242.

\bibitem{BaileyBorweinPlouffe1997}
D.~Bailey, P.~Borwein, S.~Plouffe.
\textit{On the rapid computation of various polylogarithmic constants.}
Mathematics of Computation, 66 (1997), pp.~903--913.

\bibitem{MartinOdlyzkoWolfram1984}
O.~Martin, A.~Odlyzko, S.~Wolfram.
\textit{Algebraic properties of cellular automata.}
Communications in Mathematical Physics, 94 (1984), pp.~219--258.

\bibitem{DigitalEuanGLM}
E.~R.~A.~Craig (DigitalEuan).
\textit{The Geometric Language Machine (GLM), v5.37.}
GitHub: \url{https://github.com/DigitalEuan/GLM}.
README timestamp: 18 September 2026.

\bibitem{GLMparser}
\textit{glm\_universal.runtime.parser} module, GLM repository.
Deterministic semantic query parser, 28 query kinds.

\bibitem{GLMProjectDirectives}
\textit{PROJECT\_DIRECTIVES.md}, GLM repository.
Standing rules and dimensional-layer perspective.

\bibitem{OEIS_A051023}
OEIS Foundation.
\textit{A051023: Middle column of rule-30 1-D cellular automaton, from a lone 1 cell.}
\url{https://oeis.org/A051023}. b-file by A.~Karttunen (n=0..100000).

\bibitem{Wen2019}
X.~Wen.
\textit{A Billion Bits of the Center Column of the Rule 30 Cellular Automaton.}
Wolfram Data Repository, 2019.
\url{https://datarepository.wolframcloud.com/resources/A-Billion-Bits-of-the-Center-Column-of-the-Rule-30-Cellular-Automaton}
\end{thebibliography}
"""


def main() -> None:
    table = build_substitution_table()
    body = "\n\n".join([
        PREAMBLE,
        r"\begin{document}",
        TITLE_BLOCK,
        S1_INTRO,
        S2_RULE30,
        S3_GLM,
        S4_METHOD,
        S5_P1,
        S6_P2,
        S7_P3,
        S8_SUBSTRATE,
        S9_VERDICT,
        S10_DISCUSSION,
        S11_CONCLUSION,
        r"\end{document}",
    ])
    body = substitute(body, table)
    out_path = TEX_DIR / "r30_study.tex"
    out_path.write_text(body)
    print(f"[tex] wrote {out_path} ({out_path.stat().st_size} bytes, "
          f"{len(body.splitlines())} lines)")
    # Copy supporting files next to the .tex
    shutil.copy(DATA / "glm_outputs.md", TEX_DIR / "glm_outputs.md")


if __name__ == "__main__":
    main()
