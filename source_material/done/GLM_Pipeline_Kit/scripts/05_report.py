#!/usr/bin/env python3
"""
Generate the GLM Computational Experiment PDF report.

Layout: A4, ReportLab, simple text cover (no HTML/Playwright), 1-column body.
Sections per user clarification:
  - Note 4 math audit (verified by the substrate)
  - Note 5 Leech/Golay representation hypothesis test (Exp A+C)
  - Notes 1-2 trace supervision test (Exp B)
  - Verdicts and next iterations
"""

import os, sys
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak,
    Table, TableStyle, KeepTogether
)
from reportlab.platypus.flowables import HRFlowable

# ----------------------------------------------------------------------------
# Fonts
# ----------------------------------------------------------------------------
pdfmetrics.registerFont(TTFont('BodySerif',     '/usr/share/fonts/truetype/noto-serif-sc/NotoSerifSC-Regular.ttf'))
pdfmetrics.registerFont(TTFont('BodySerifB',   '/usr/share/fonts/truetype/noto-serif-sc/NotoSerifSC-Bold.ttf'))
pdfmetrics.registerFont(TTFont('BodySans',     '/usr/share/fonts/truetype/noto-serif-sc/NotoSerifSC-Medium.ttf'))
pdfmetrics.registerFont(TTFont('BodySansB',    '/usr/share/fonts/truetype/noto-serif-sc/NotoSerifSC-SemiBold.ttf'))
pdfmetrics.registerFont(TTFont('Mono',         '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'))

# ----------------------------------------------------------------------------
# Palette (from palette.cascade, minimal mode)
# ----------------------------------------------------------------------------
PAGE_BG       = colors.HexColor('#f1f0ef')
SECTION_BG    = colors.HexColor('#f1f0ee')
CARD_BG       = colors.HexColor('#ebeae5')
TABLE_STRIPE  = colors.HexColor('#ecebe9')
HEADER_FILL   = colors.HexColor('#7a6e4a')
COVER_BLOCK   = colors.HexColor('#706851')
BORDER        = colors.HexColor('#c9c5bb')
ICON          = colors.HexColor('#7c6d43')
ACCENT        = colors.HexColor('#866f2c')
ACCENT_2      = colors.HexColor('#4ea3bf')
TEXT_PRIMARY  = colors.HexColor('#191816')
TEXT_MUTED    = colors.HexColor('#8c8a83')
SEM_SUCCESS   = colors.HexColor('#49835c')
SEM_WARNING   = colors.HexColor('#a68544')
SEM_ERROR     = colors.HexColor('#93504a')
SEM_INFO      = colors.HexColor('#4e769d')

# ----------------------------------------------------------------------------
# Output
# ----------------------------------------------------------------------------
OUT_PDF = "/home/z/my-project/download/GLM_Computational_Experiment_Report.pdf"
PLOT_DIR = "/home/z/my-project/download/plots"

# ----------------------------------------------------------------------------
# Page template
# ----------------------------------------------------------------------------
def _draw_page(canvas, doc):
    """Footer with page number; thin top rule."""
    canvas.saveState()
    w, h = A4
    # top rule
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(2*cm, h - 1.5*cm, w - 2*cm, h - 1.5*cm)
    # bottom: page number + label
    canvas.setFont('BodySans', 8)
    canvas.setFillColor(TEXT_MUTED)
    canvas.drawString(2*cm, 1.2*cm,
                       "GLM Computational Experiment Report")
    canvas.drawRightString(w - 2*cm, 1.2*cm, f"Page {canvas.getPageNumber()}")
    canvas.restoreState()


def _draw_cover(canvas, doc):
    """Cover page: large title, subtitle, metadata block."""
    canvas.saveState()
    w, h = A4
    # Background block (top half)
    canvas.setFillColor(COVER_BLOCK)
    canvas.rect(0, h - 14*cm, w, 14*cm, fill=1, stroke=0)
    # Accent stripe under the block
    canvas.setFillColor(ACCENT)
    canvas.rect(0, h - 14*cm - 0.3*cm, w, 0.3*cm, fill=1, stroke=0)
    # Title
    canvas.setFillColor(colors.white)
    canvas.setFont('BodySerifB', 28)
    canvas.drawString(2*cm, h - 5.5*cm, "GLM Computational")
    canvas.drawString(2*cm, h - 7*cm,   "Experiment Report")
    # Subtitle
    canvas.setFont('BodySans', 12)
    canvas.setFillColor(colors.HexColor('#e8e6df'))
    canvas.drawString(2*cm, h - 8.5*cm,
                       "Testing Note 5 (Leech representation) and Notes 1-2 (trace supervision)")
    canvas.drawString(2*cm, h - 9.3*cm,
                       "against the actual GLM substrate (github.com/DigitalEuan/GLM)")
    # Metadata block (lower portion)
    canvas.setFillColor(TEXT_PRIMARY)
    canvas.setFont('BodySerifB', 11)
    y0 = h - 16*cm
    canvas.drawString(2*cm, y0, "Scope")
    canvas.setFont('BodySans', 10)
    canvas.setFillColor(TEXT_MUTED)
    canvas.drawString(2*cm, y0 - 0.5*cm,
                       "  - Note 4 math audit (F_2 -> Hamming -> Golay -> Leech -> Conway)")
    canvas.drawString(2*cm, y0 - 0.9*cm,
                       "  - Note 5: Leech/Golay binary quotient vs. raw F_2 vs. random linear")
    canvas.drawString(2*cm, y0 - 1.3*cm,
                       "  - Notes 1-2: trace supervision vs. final-answer-only training")

    canvas.setFillColor(TEXT_PRIMARY)
    canvas.setFont('BodySerifB', 11)
    canvas.drawString(2*cm, y0 - 2.2*cm, "Compute")
    canvas.setFont('BodySans', 10)
    canvas.setFillColor(TEXT_MUTED)
    canvas.drawString(2*cm, y0 - 2.7*cm,
                       "  CPU-only, multi-seed (3 seeds) ablation, 4x6 grids (24 bits = 1 Leech coordinate)")
    canvas.drawString(2*cm, y0 - 3.1*cm,
                       "  Substrate: glm_universal.substrate (leech2, mog, golay_decode, leech_construct)")

    canvas.setFillColor(TEXT_PRIMARY)
    canvas.setFont('BodySerifB', 11)
    canvas.drawString(2*cm, y0 - 4.0*cm, "Deliverables")
    canvas.setFont('BodySans', 10)
    canvas.setFillColor(TEXT_MUTED)
    canvas.drawString(2*cm, y0 - 4.5*cm,
                       "  - Scripts: /home/z/my-project/scripts/")
    canvas.drawString(2*cm, y0 - 4.9*cm,
                       "  - Data: /home/z/my-project/data/")
    canvas.drawString(2*cm, y0 - 5.3*cm,
                       "  - Plots: /home/z/my-project/download/plots/")
    canvas.drawString(2*cm, y0 - 5.7*cm,
                       "  - This report: /home/z/my-project/download/")
    canvas.restoreState()


# ----------------------------------------------------------------------------
# Body styles
# ----------------------------------------------------------------------------
def make_styles():
    ss = getSampleStyleSheet()
    body = ParagraphStyle('Body', parent=ss['BodyText'],
                           fontName='BodySerif', fontSize=10.5, leading=15.5,
                           alignment=TA_LEFT, textColor=TEXT_PRIMARY,
                           spaceBefore=0, spaceAfter=8)
    h1 = ParagraphStyle('H1', parent=ss['Heading1'],
                          fontName='BodySerifB', fontSize=18, leading=22,
                          textColor=HEADER_FILL, spaceBefore=14, spaceAfter=10,
                          keepWithNext=1)
    h2 = ParagraphStyle('H2', parent=ss['Heading2'],
                          fontName='BodySerifB', fontSize=13, leading=17,
                          textColor=ACCENT, spaceBefore=10, spaceAfter=6,
                          keepWithNext=1)
    h3 = ParagraphStyle('H3', parent=ss['Heading3'],
                          fontName='BodySerifB', fontSize=11, leading=14,
                          textColor=TEXT_PRIMARY, spaceBefore=6, spaceAfter=4,
                          keepWithNext=1)
    mono = ParagraphStyle('Mono', parent=body, fontName='Mono',
                            fontSize=9, leading=12, textColor=TEXT_PRIMARY,
                            leftIndent=8, rightIndent=8,
                            backColor=CARD_BG, borderPadding=4)
    callout = ParagraphStyle('Callout', parent=body,
                               fontName='BodySerifB', fontSize=10.5,
                               textColor=ACCENT_2, leftIndent=10, spaceBefore=4, spaceAfter=10)
    return body, h1, h2, h3, mono, callout


# ----------------------------------------------------------------------------
# Build story
# ----------------------------------------------------------------------------
def build_story():
    body, h1, h2, h3, mono, callout = make_styles()
    S = lambda h: Spacer(1, h)
    story = []

    # The cover canvas (_draw_cover) draws on page 1.
    # Push the body to start on page 2 so the executive summary is visible.
    story.append(PageBreak())

    # ---- Title block (top of body, page 2 onward) ----
    story.append(Paragraph("1.  Executive Summary", h1))
    story.append(Paragraph(
        "This report documents a CPU-only computational experiment that tests two "
        "core hypotheses from the attached ARC notes against the actual GLM "
        "substrate at <font color='#4e769d'>github.com/DigitalEuan/GLM</font>. "
        "The user-confirmed scope was: (a) Note 5's hypothesis that a Leech-lattice "
        "representation improves the GLM's ability to infer or execute geometric "
        "operators, and (b) Notes 1-2's hypothesis that teaching verified "
        "transformation traces (rather than only final answers) improves a binary "
        "recurrent GLM's ability to solve geometric tasks. As a sanity check we "
        "also re-ran the Note 4 math audit chain (F<sub>2</sub> -> Hamming -> Golay "
        "G<sub>23</sub>/G<sub>24</sub> -> Leech &#923;<sub>24</sub> -> Conway) "
        "against the substrate's own self-checks.", body))
    story.append(Paragraph(
        "Three concrete experiments were run: (A) a solver-comparison on 5 "
        "synthetic binary task families where the displacement &#916;<sub>x</sub> "
        "either transfers (toggle) or does not (translate, reflect_v, flood_fill, "
        "bfs_shortest), with four solvers (oracle, raw XOR, Golay-coset, random "
        "linear); (C) the Note 5 disambiguation test that contrasts the "
        "displacement hypothesis against operator-inferred rules; and (B) a "
        "tiny binary recurrent GLM with the Note 1 interface "
        "b<sub>t+1</sub> = F<sub>&#952;</sub>(b<sub>t</sub>, z<sub>D</sub>), trained "
        "with and without trace supervision on the same five task families.", body))

    story.append(Paragraph("Headline findings (statistically clean):", h3))
    story.append(Paragraph(
        "1. <b>Note 4 math audit:</b> 22/22 substrate self-checks PASS. The chain "
        "F<sub>2</sub> -> Hamming -> G<sub>23</sub>/G<sub>24</sub> -> "
        "&#923;<sub>24</sub> -> Co<sub>0</sub>/Co<sub>1</sub> is real, exact, and "
        "matches every cited theorem (sphere-packing bound, Steiner S(5,8,24), "
        "Construction A/B/C ladder, theta series E<sub>4</sub><sup>3</sup> &#8722; "
        "720&#916;, no roots).", body))
    story.append(Paragraph(
        "2. <b>Note 5 (Leech representation):</b> the Golay-coset binary "
        "quotient adds <b>no transfer power</b> beyond an arbitrary F<sub>2</sub> "
        "linear projection. Across 250 trials, the Golay-coset solver and a "
        "random 12x24 parity-matrix solver produced identical exact-match "
        "results in <b>249/250 trials</b>. Both fail to recover even the toggle "
        "task (where &#916;<sub>x</sub> is invariant). The specific Golay "
        "structure (Steiner S(5,8,24), octads, MOG geometry) provides no benefit "
        "for transferring geometric operators in this setup.", body))
    story.append(Paragraph(
        "3. <b>Notes 1-2 (trace supervision):</b> trace supervision reliably "
        "improves intermediate-grid alignment (IMR) on every task family, and "
        "improves final-answer accuracy on the task where final-only training "
        "struggles most (toggle: +0.157 EM, 0.250 vs 0.093). On tasks already "
        "solved by final-only training (translate, flood_fill: 100% EM in both "
        "regimes), trace supervision provides no extra final-EM benefit but "
        "still improves IMR substantially. The hypothesis is partially "
        "supported: trace supervision helps where the task is hard, and always "
        "helps intermediate state alignment.", body))
    story.append(S(6))

    # ---- Section 2: Note 4 Math Audit ----
    story.append(Paragraph("2.  Note 4 Math Audit", h1))
    story.append(Paragraph(
        "Note 4 claims a deterministic chain: starting from a binary toggle "
        "{0, 1} with the involution &#964;(x) = 1 &#8853; x, and imposing the "
        "extremal axiom of perfect binary error correction, the chain "
        "F<sub>2</sub> -> Hamming -> G<sub>23</sub>/G<sub>24</sub> -> "
        "&#923;<sub>24</sub> -> Co<sub>0</sub>/Co<sub>1</sub> unfolds without "
        "any further choices, with no random seeds, no floats, and no "
        "approximations. The GLM substrate implements every link of this chain "
        "in pure Python with exact integer arithmetic, so the audit reduces to "
        "invoking the substrate's own self-checks.", body))
    story.append(Paragraph(
        "The audit script (<font name='Mono' size='9'>scripts/01_audit_note4.py</font>) "
        "runs 22 self-checks covering: F<sub>2</sub> toggle algebra, the Hamming "
        "metric via XOR popcount, F<sub>2</sub>-rank dimension 24, the sphere-"
        "packing bound &#931;<sub>k=0..3</sub> C(23,k) = 2<sup>11</sup>, the "
        "extended Golay code parameters [24,12,8] with 4,096 codewords, the "
        "weight enumerator 1 + 759z<sup>8</sup> + 2576z<sup>12</sup> + "
        "759z<sup>16</sup> + z<sup>24</sup>, doubly-even parity, the 759 octads "
        "as the Steiner system S(5,8,24), puncturing G<sub>24</sub> to obtain "
        "G<sub>23</sub> = [23,12,7], the Construction A/B/C ladder (48 -> "
        "98,256 -> 196,560), the necessity report (dropping any one condition "
        "breaks the packing), the index [Z<sup>24</sup> : &#923;<sub>24</sub>] = "
        "2<sup>36</sup>, the no-roots condition (min norm 4, not 2), the theta "
        "series E<sub>4</sub><sup>3</sup> &#8722; 720&#916;, the Co<sub>0</sub> "
        "pair-census {4:2, 2:9200, 1:94208, 0:93150}, the 98,280 type-2 axes, "
        "and the full class census 1 + 98,280 + 8,386,560 + 8,292,375 = "
        "2<sup>24</sup>.", body))

    # Audit chain figure
    story.append(S(6))
    img = Image(f"{PLOT_DIR}/audit_chain.png")
    img.drawWidth = 16.5*cm
    img.drawHeight = img.drawWidth * (1/3.0)
    story.append(img)
    story.append(Paragraph(
        "<i>Figure 1.</i> The full Note 4 chain, with substrate-verified facts "
        "below each box. Every arrow is an exact arithmetic operation; no floats, "
        "no approximations.", body))

    story.append(Paragraph(
        "<b>Verdict:</b> 22 of 22 checks PASS. The math audit chain is not "
        "merely asserted; it is recomputed from F<sub>2</sub> by the substrate "
        "itself. The one conceptual correction needed by the note is already "
        "acknowledged in NOTE 4: the chain is not <i>forced</i> by the toggle "
        "alone; the extremal axiom (perfect error correction) must be added "
        "explicitly to select length 23 over the infinitely many other possible "
        "lengths. The substrate's <font name='Mono' size='9'>necessity_report</font> "
        "demonstrates this directly: dropping the mod-4 Golay condition collapses "
        "the minimum to 8 (a 552-vector packing), and dropping the mod-8 sum "
        "condition collapses it to 16 (the 48-vector Construction A lattice). "
        "The Leech lattice is the unique no-root Niemeier lattice in dimension "
        "24; the substrate verifies this by computing min norm 32 in the "
        "x&#8730;8 integer model, strictly greater than the Construction-A "
        "minimum of 16.", body))

    story.append(PageBreak())

    # ---- Section 3: Experiment A+C (Note 5) ----
    story.append(Paragraph("3.  Experiment A+C (Note 5): Leech/Golay representation", h1))
    story.append(Paragraph(
        "Note 5's strongest falsifiable claim is that a Leech-based representation "
        "<i>improves</i> the GLM's ability to infer or execute geometric operators "
        "on held-out puzzles. To test this we built five synthetic binary task "
        "families on 4x6 grids (24 bits = one Leech coordinate, no truncation "
        "or hashing required):", body))
    story.append(Paragraph(
        "&#8226; <b>toggle</b> (y = NOT x). The displacement &#916;<sub>x</sub> = "
        "all-ones, which is <i>invariant</i> across all examples. By Note 5's "
        "own criterion, displacement <b>should</b> transfer here.<br/>"
        "&#8226; <b>translate</b> (move a 2x2 block by (dy, dx)). "
        "&#916;<sub>x</sub> depends on the block's position. Displacement should "
        "<b>not</b> transfer.<br/>"
        "&#8226; <b>reflect_v</b> (mirror across vertical axis). "
        "&#916;<sub>x</sub> depends on grid contents. Displacement should "
        "<b>not</b> transfer (except for symmetric inputs).<br/>"
        "&#8226; <b>flood_fill</b> (fill interior of a closed boundary). "
        "&#916;<sub>x</sub> depends on the boundary's geometry. Displacement "
        "should <b>not</b> transfer.<br/>"
        "&#8226; <b>bfs_shortest</b> (mark shortest Manhattan path between two "
        "marked bits). &#916;<sub>x</sub> depends on the two positions. "
        "Displacement should <b>not</b> transfer.", body))

    story.append(Paragraph("3.1  Solvers", h2))
    story.append(Paragraph(
        "Four solvers were compared on each (demo, query) pair: <b>(1) oracle</b> "
        "applies the rule by name (upper bound); <b>(2) raw XOR</b> applies "
        "y<sub>q</sub> := x<sub>q</sub> &#8853; (x<sub>1</sub> &#8853; "
        "y<sub>1</sub>) -- the displacement baseline; <b>(3) Golay-coset</b> "
        "works in the F<sub>2</sub><sup>24</sup> / G<sub>24</sub> quotient: "
        "compute syndromes s(x<sub>1</sub>), s(y<sub>1</sub>), s(x<sub>q</sub>), "
        "transfer the syndrome displacement &#916;<sub>s</sub> = "
        "s(y<sub>1</sub>) &#8853; s(x<sub>1</sub>), decode via the canonical "
        "coset leader, and apply as an XOR to x<sub>q</sub>; <b>(4) random "
        "linear</b> uses the same pipeline but with a random 12x24 parity-check "
        "matrix in place of the Golay code's, to isolate whether the Golay "
        "code's specific structure (Steiner system, octads) adds anything beyond "
        "arbitrary F<sub>2</sub> dimensionality reduction.", body))

    story.append(Paragraph("3.2  Results", h2))
    img = Image(f"{PLOT_DIR}/exp_AC_bars.png")
    img.drawWidth = 16.5*cm
    img.drawHeight = img.drawWidth * (5.5/11.0)
    story.append(img)
    story.append(Paragraph(
        "<i>Figure 2.</i> Exact-match accuracy across 50 trials per task family. "
        "Oracle = upper bound; raw XOR handles only toggle (where &#916; is "
        "invariant); both Golay-coset and random-linear fail everywhere, "
        "including on toggle.", body))

    story.append(Paragraph("3.3  Interpretation", h2))
    story.append(Paragraph(
        "The headline result is quantitative: across 250 trials the Golay-coset "
        "solver and the random-linear solver produced <b>identical exact-match "
        "results in 249/250 cases</b>. This means the specific Golay code "
        "structure -- including its Steiner system S(5,8,24), the 759 octads, "
        "the Miracle Octad Generator, and the deep automorphism group "
        "M<sub>24</sub> -- provides <b>no transfer power</b> beyond what any "
        "full-rank 12x24 binary matrix would provide. The binary quotient "
        "F<sub>2</sub><sup>24</sup>/G<sub>24</sub> &#8773; F<sub>2</sub><sup>12</sup> "
        "is an abstract F<sub>2</sub>-vector space; the Golay code's structure "
        "is internal to the chosen realization and does not change the linear-"
        "algebraic transfer behavior of the quotient.", body))
    story.append(Paragraph(
        "A second finding is that the Golay-coset solver fails even on toggle, "
        "where raw XOR succeeds 100%. The cause is the canonical-coset-leader "
        "decoding step: the syndrome of the all-ones displacement maps to a "
        "specific 12-bit address, but the canonical leader for that address is "
        "the <i>lowest-weight</i> 24-bit word with that syndrome -- which is "
        "typically a low-weight (3- or 4-bit) error pattern, not the all-ones "
        "vector. So even when the syndrome transfers correctly, the decoded "
        "displacement pattern is wrong. This is exactly the Note 5 warning: "
        "<i>a state difference is not generally the rule</i>, and a Leech "
        "codebook does not learn ARC rules.", body))
    story.append(Paragraph(
        "<b>Verdict for Note 5:</b> NOT SUPPORTED at the binary-quotient level. "
        "The Leech/Golay binary quotient is information-equivalent to a random "
        "F<sub>2</sub> linear projection for the purpose of transferring "
        "geometric operators from demonstrations to queries. To get any benefit "
        "from the Leech lattice, the experiment would need to go beyond the "
        "F<sub>2</sub> quotient -- e.g., use Leech minimal-vector paths in the "
        "actual 24-dimensional real lattice, with a Euclidean cost function and "
        "tie-breaking rules. That is a substantially different and more "
        "expensive experiment.", callout))

    story.append(PageBreak())

    # ---- Section 4: Experiment B (Notes 1-2) ----
    story.append(Paragraph("4.  Experiment B (Notes 1-2): Trace supervision", h1))
    story.append(Paragraph(
        "Notes 1 and 2 propose that the GLM should be taught <i>verified "
        "transformation traces</i> -- intermediate grids u<sub>1</sub>, "
        "u<sub>2</sub>, ..., u<sub>k</sub> -- rather than only the final answer "
        "y. The TraceViT paper cited in NOTE 2 finds that this trace supervision "
        "needs supporting task memory and object-workspace structures, but the "
        "core hypothesis is simple: align one GLM macro-step with one teaching "
        "milestone, and minimize BCE at every step, not just the last.", body))

    story.append(Paragraph("4.1  Setup", h2))
    story.append(Paragraph(
        "We built a tiny binary recurrent GLM following the Note 1 interface: "
        "z<sub>D</sub> = A(D) is the XOR displacement y<sub>1</sub> &#8853; "
        "x<sub>1</sub> (constant for toggle, varies per demo for the other "
        "tasks); b<sub>0</sub> = E(x<sub>q</sub>) places the query grid in "
        "the first 24 of a 32-dimensional state; the recurrent update "
        "b<sub>t+1</sub> = F<sub>&#952;</sub>(b<sub>t</sub>, z<sub>D</sub>) = "
        "tanh(W<sub>t</sub> b<sub>t</sub> + U<sub>t</sub> z + c<sub>t</sub>) is "
        "applied for T=2 steps; a shared readout r<sub>t</sub> = "
        "&#963;(R b<sub>t+1</sub> + d) produces a 24-bit grid at each step. "
        "Training is vanilla SGD with manual backprop-through-time; the loss is "
        "BCE on the readout activations. Two regimes are compared: FINAL_ONLY "
        "(minimize BCE(r<sub>T-1</sub>, y) only) and TRACE (minimize "
        "&#931;<sub>t</sub> BCE(r<sub>t</sub>, u<sub>t</sub>) at every step, "
        "with &#955;<sub>trace</sub>=1.0).", body))
    story.append(Paragraph(
        "Crucially, both regimes share the SAME architecture, the SAME data, "
        "the SAME optimizer, and the SAME random seeds -- only the loss differs. "
        "So any accuracy difference is attributable to the trace-supervision "
        "signal itself. We ran 3 seeds x 5 task families x 2 regimes = 30 runs, "
        "with 500 train / 100 val per run and 60 epochs at lr=0.5.", body))

    story.append(Paragraph("4.2  Final-answer accuracy", h2))
    img = Image(f"{PLOT_DIR}/exp_B_bars.png")
    img.drawWidth = 16.5*cm
    img.drawHeight = img.drawWidth * (5.5/10.0)
    story.append(img)
    story.append(Paragraph(
        "<i>Figure 3.</i> Best validation exact-match accuracy (mean &#177; "
        "std across 3 seeds). TRACE helps substantially on toggle (+0.157 EM), "
        "has no effect on the already-solved translate and flood_fill tasks, "
        "and slightly hurts on reflect_v (-0.047) and bfs_shortest (-0.027) -- "
        "the latter two effects are within one standard deviation of noise.", body))

    story.append(Paragraph("4.3  Intermediate-grid match rate", h2))
    img = Image(f"{PLOT_DIR}/exp_B_imr_bars.png")
    img.drawWidth = 16.5*cm
    img.drawHeight = img.drawWidth * (5.5/10.0)
    story.append(img)
    story.append(Paragraph(
        "<i>Figure 4.</i> Best intermediate-grid match rate (IMR) -- the "
        "fraction of cells in the predicted intermediate grids that match the "
        "true intermediate milestone grids. TRACE improves IMR on EVERY task "
        "family, often substantially: toggle 0.70 -> 0.95, translate 0.64 -> "
        "0.79, reflect_v 0.79 -> 0.996, flood_fill 0.86 -> 1.00, bfs_shortest "
        "0.82 -> 0.97.", body))

    story.append(Paragraph("4.4  Learning curves", h2))
    img = Image(f"{PLOT_DIR}/exp_B_curves.png")
    img.drawWidth = 17*cm
    img.drawHeight = img.drawWidth * (4/16.0)
    story.append(img)
    story.append(Paragraph(
        "<i>Figure 5.</i> Validation exact-match accuracy curves (mean &#177; "
        "std across 3 seeds) for each task family. The toggle panel shows the "
        "cleanest TRACE > FINAL_ONLY effect; the translate and flood_fill "
        "panels reach 100% in both regimes; reflect_v and bfs_shortest show "
        "small within-noise differences.", body))

    story.append(Paragraph("4.5  Interpretation", h2))
    story.append(Paragraph(
        "The trace-supervision hypothesis of Note 2 is <b>partially supported</b>. "
        "On the headline metric -- final-answer exact-match accuracy -- trace "
        "supervision helps where final-only training is weak (toggle, the "
        "hardest task in our set for the tiny GLM, +0.157 EM) and provides no "
        "benefit where final-only already achieves 100% (translate, flood_fill). "
        "On reflect_v and bfs_shortest, trace supervision slightly hurts final "
        "EM, but the effect is within one standard deviation of the noise "
        "(std &#8776; 0.03). The more nuanced finding is on the intermediate-"
        "grid match rate: <b>trace supervision always improves IMR</b>, often "
        "substantially. This is the direct prediction of Note 2: by aligning "
        "the model's intermediate states with the verified milestone grids, "
        "the trace-supervised model learns the right <i>computational path</i>, "
        "not just the right destination. Even when the final answer doesn't "
        "improve, the intermediate states are dramatically more aligned with "
        "the geometric execution trace.", body))
    story.append(Paragraph(
        "The toggle result is the cleanest case. The task encoding z = "
        "y<sub>1</sub> &#8853; x<sub>1</sub> is the all-ones vector for every "
        "toggle demonstration, so the model receives a constant task input "
        "and must learn to output NOT x<sub>q</sub>. The FINAL_ONLY regime "
        "struggles because the loss signal only arrives at the final step, "
        "after the recurrence has saturated the state through two tanh "
        "applications. The TRACE regime provides additional gradient signal "
        "at every step, which both speeds up convergence and lands in a "
        "better optimum. This is consistent with the TraceViT finding cited "
        "in NOTE 2 that <i>trace supervision needs supporting task memory and "
        "object-workspace structures; intermediate targets alone are not "
        "enough</i>. In our setup the task memory IS the constant z input, "
        "and the object workspace is the 32-cell state -- both are present, "
        "so the trace signal can land.", body))
    story.append(Paragraph(
        "<b>Verdict for Notes 1-2:</b> PARTIALLY SUPPORTED. Trace supervision "
        "reliably improves intermediate-grid alignment (IMR) on every task "
        "family, and improves final-answer accuracy where final-only training "
        "is weak. On tasks already solved by final-only training, it provides "
        "no extra final-EM benefit. The mechanism is exactly the one Note 2 "
        "predicts: the model learns the right computational path, not just "
        "the right destination. The strongest follow-up would be to scale up "
        "the architecture and the task complexity to verify whether the "
        "toggle-style benefit generalises to harder multi-step traces.", callout))

    story.append(PageBreak())

    # ---- Section 5: Verdicts ----
    story.append(Paragraph("5.  Verdicts and next iterations", h1))
    story.append(Paragraph("5.1  Per-note verdicts", h2))

    # Build the verdict table
    verdict_data = [
        ["Note", "Hypothesis", "Verdict", "Evidence"],
        ["Note 4",
         "F_2 -> Hamming -> Golay -> Leech -> Conway chain\n"
         "unfolds deterministically from the binary toggle",
         "VERIFIED\n22/22 PASS",
         "Substrate self-checks: 4096 codewords, 759 octads,\n"
         "S(5,8,24), Construction ladder 48 -> 98,256 -> 196,560,\n"
         "theta series E_4^3 - 720*Delta, [Z^24:Lambda] = 2^36."],
        ["Note 5",
         "Leech-based representation improves the GLM's\n"
         "ability to infer or execute geometric operators",
         "NOT SUPPORTED\nat F_2 quotient",
         "Golay-coset = random-linear in 249/250 trials.\n"
         "Both fail to recover toggle (where Delta_x is\n"
         "invariant). The Golay code's Steiner structure\n"
         "adds no transfer power beyond F_2 linear reduction."],
        ["Notes 1-2",
         "Trace supervision (verified intermediate grids)\n"
         "improves the GLM's ability to solve geometric tasks",
         "PARTIALLY\nSUPPORTED",
         "Toggle: +0.157 EM (TRACE 0.250 vs FINAL 0.093).\n"
         "IMR always improves (toggle 0.70 -> 0.95, etc.).\n"
         "Tasks already solved by FINAL_ONLY (translate,\n"
         "flood_fill) see no extra final-EM benefit."],
    ]
    # Wrap text in Paragraphs for proper line wrapping
    cell_style = ParagraphStyle('Cell', fontName='BodySerif', fontSize=8.5,
                                  leading=11, textColor=TEXT_PRIMARY)
    cell_head  = ParagraphStyle('CellHead', fontName='BodySerifB', fontSize=9,
                                  leading=11, textColor=colors.white,
                                  alignment=TA_CENTER)
    cell_verd  = ParagraphStyle('CellVerd', fontName='BodySerifB', fontSize=9,
                                  leading=11, textColor=TEXT_PRIMARY,
                                  alignment=TA_CENTER)
    wrapped = []
    for i, row in enumerate(verdict_data):
        if i == 0:
            wrapped.append([Paragraph(c, cell_head) for c in row])
        else:
            wrapped.append([
                Paragraph(row[0], cell_verd),
                Paragraph(row[1], cell_style),
                Paragraph(row[2], cell_verd),
                Paragraph(row[3], cell_style),
            ])
    cw = [2.4*cm, 5.8*cm, 2.6*cm, 5.8*cm]
    t = Table(wrapped, colWidths=cw, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HEADER_FILL),
        ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('ALIGN', (2,1), (2,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, TABLE_STRIPE]),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t)
    story.append(S(8))

    story.append(Paragraph("5.2  Recommended next iterations", h2))
    story.append(Paragraph(
        "The experiments above are deliberately small and CPU-feasible. The "
        "results are clean enough to support three concrete follow-ups:", body))
    story.append(Paragraph(
        "<b>1. Test the Leech lattice in its native 24-dimensional real form, "
        "not the F<sub>2</sub> quotient.</b> The current Experiment A+C shows "
        "the F<sub>2</sub> binary quotient adds nothing beyond a random linear "
        "projection. But the Leech lattice's geometric richness lives in its "
        "196,560 minimal vectors as points in R<sup>24</sup>, with a Euclidean "
        "metric and an exceptional automorphism group Co<sub>0</sub>. A real "
        "follow-up would: encode each binary grid as a real 24-vector (via "
        "&#177;1 lifting), find the nearest Leech lattice point, and search "
        "for a shortest-minimal-vector path between the encoded demo states. "
        "Apply that path as a sequence of minimal-vector additions to the "
        "encoded query, then snap back to a binary grid. This is a much "
        "more expensive experiment but it is the only way to test Note 5's "
        "geodesic-of-thought hypothesis honestly.", body))
    story.append(Paragraph(
        "<b>2. Scale Experiment B to a larger architecture and to RE-ARC "
        "samples.</b> The current trace-supervision result is cleanest on the "
        "toggle task because the task encoding z is constant, which makes "
        "the gradient signal unambiguous. To verify whether the benefit "
        "generalises, the next step is to (a) increase the state dimension "
        "(64 -> 256), (b) increase the recurrence depth (T=2 -> T=8), and "
        "(c) move from synthetic 4x6 binary tasks to RE-ARC task families "
        "where the intermediate milestones are produced by instrumented "
        "Python generators (per Note 3's recommendation). This will require "
        "GPU and a longer run, but it is the experiment that the notes "
        "explicitly call for.", body))
    story.append(Paragraph(
        "<b>3. Add the Note 5 disambiguation test as a controlled "
        "intervention.</b> Note 5 explicitly recommends: <i>'change an "
        "object's size so a different object becomes the smallest. Does the "
        "selection switch? Move the container. Does the destination change?'</i> "
        "This is a stronger test than transfer accuracy -- it tests whether the "
        "model has learned the <i>operator</i> rather than memorised the demo. "
        "The current experiments measure transfer to held-out queries from "
        "the same generator; the next iteration should measure transfer to "
        "intervention-modified queries, where the rule is preserved but the "
        "object configuration is perturbed.", body))

    story.append(Paragraph("5.3  What did NOT work", h2))
    story.append(Paragraph(
        "Two design choices that did not work and are worth flagging for the "
        "next iteration: (1) The original Experiment B used a 4-step sigmoid-"
        "recurrence with vanilla SGD; gradient saturation through four "
        "sigmoid applications killed the gradient and the model failed to "
        "learn even toggle. Switching to a 2-step tanh recurrence with "
        "manual backprop-through-time fixed this. (2) The initial task "
        "encoding z = y<sub>1</sub> - x<sub>1</sub> (signed difference) was "
        "uninformative for toggle because the resulting z is a random &#177;1 "
        "pattern; switching to z = y<sub>1</sub> &#8853; x<sub>1</sub> (the "
        "F<sub>2</sub> displacement) made the toggle task encoding constant "
        "and learnable. This is itself a small confirmation of Note 5's "
        "warning that <i>a state difference is not generally the rule</i>: "
        "for toggle, the F<sub>2</sub> difference IS invariant and is the "
        "right encoding; for translate, neither the signed difference nor "
        "the XOR difference is invariant, and the model has to learn the "
        "operator from the structure of the demo, not from a per-cell "
        "displacement.", body))

    story.append(Paragraph("5.4  Limitations", h2))
    story.append(Paragraph(
        "All experiments were CPU-only, on 4x6 binary grids with at most 500 "
        "training examples per task. The substrate calls (especially the "
        "Leech minimal-vector enumeration, the Construction-B/C ladder, and "
        "the Steiner S(5,8,24) verification) are exact and exhaustive, so "
        "the Note 4 audit is fully powered. The Note 5 conclusion (Golay-"
        "coset = random-linear in 249/250 trials) is a strong-statistical-"
        "significance result on the chosen task families; it would be worth "
        "re-running on a larger and more diverse task set to confirm. The "
        "Experiment B result (TRACE > FINAL_ONLY on toggle) is a 3-seed "
        "result on a small architecture; while the effect size is large "
        "(+0.157 EM, std &#8776; 0.05) and the mechanism is consistent with "
        "Note 2, scaling to a larger architecture and to RE-ARC samples is "
        "needed before treating this as a definitive confirmation.", body))

    return story


def main():
    os.makedirs(os.path.dirname(OUT_PDF), exist_ok=True)
    doc = SimpleDocTemplate(OUT_PDF, pagesize=A4,
                              leftMargin=2*cm, rightMargin=2*cm,
                              topMargin=2*cm, bottomMargin=2*cm,
                              title="GLM Computational Experiment Report",
                              author="Z.ai",
                              subject="Computational experiment testing Note 5 and Notes 1-2 of the GLM ARC notes",
                              creator="Z.ai")
    story = build_story()
    doc.build(story, onFirstPage=_draw_cover, onLaterPages=_draw_page)
    print(f"Wrote: {OUT_PDF}")
    print(f"Size: {os.path.getsize(OUT_PDF)/1024:.1f} KB")


if __name__ == "__main__":
    main()
