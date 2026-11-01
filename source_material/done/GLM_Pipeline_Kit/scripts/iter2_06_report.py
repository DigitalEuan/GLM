#!/usr/bin/env python3
"""
Generate the Iteration 2 PDF report.

Builds on Iteration 1 by adding:
  - Phase 1: Golay-syndrome cost atlas (Golay as measuring device)
  - Phase 2: Delta-sigma wobble signatures + hull certificate
  - Phase 3: Leech native 24-D wobble (full 196,560 minimal vectors)
  - Phase 4: Per-step cost in multi-step traces (escalation triggers)
  - Summary: layered perspective (Golay -> Leech -> Barnes-Wall)
"""

import os, sys
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak,
    Table, TableStyle, KeepTogether
)

pdfmetrics.registerFont(TTFont('BodySerif',   '/usr/share/fonts/truetype/noto-serif-sc/NotoSerifSC-Regular.ttf'))
pdfmetrics.registerFont(TTFont('BodySerifB', '/usr/share/fonts/truetype/noto-serif-sc/NotoSerifSC-Bold.ttf'))
pdfmetrics.registerFont(TTFont('BodySans',    '/usr/share/fonts/truetype/noto-serif-sc/NotoSerifSC-Medium.ttf'))
pdfmetrics.registerFont(TTFont('Mono',        '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'))

# Palette (from palette.cascade, dark mode for an "iteration" feel)
PAGE_BG       = colors.HexColor('#f1f0ef')
SECTION_BG    = colors.HexColor('#f1f0ee')
CARD_BG       = colors.HexColor('#ebeae5')
TABLE_STRIPE  = colors.HexColor('#ecebe9')
HEADER_FILL   = colors.HexColor('#5a4e2a')
COVER_BLOCK   = colors.HexColor('#4a3e1a')
BORDER        = colors.HexColor('#c9c5bb')
ACCENT        = colors.HexColor('#8a6f1c')
ACCENT_2      = colors.HexColor('#4ea3bf')
TEXT_PRIMARY  = colors.HexColor('#191816')
TEXT_MUTED    = colors.HexColor('#8c8a83')
SEM_SUCCESS   = colors.HexColor('#49835c')
SEM_WARNING   = colors.HexColor('#a68544')
SEM_ERROR     = colors.HexColor('#93504a')
SEM_INFO      = colors.HexColor('#4e769d')

OUT_PDF = "/home/z/my-project/download/GLM_Iteration2_Exact_Reasoning.pdf"
PLOT_DIR = "/home/z/my-project/download/iter2_plots"


def _draw_page(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setStrokeColor(BORDER); canvas.setLineWidth(0.5)
    canvas.line(2*cm, h - 1.5*cm, w - 2*cm, h - 1.5*cm)
    canvas.setFont('BodySerif', 8); canvas.setFillColor(TEXT_MUTED)
    canvas.drawString(2*cm, 1.2*cm, "GLM Iteration 2 — Exact Reasoning via the Layered Perspective")
    canvas.drawRightString(w - 2*cm, 1.2*cm, f"Page {canvas.getPageNumber()}")
    canvas.restoreState()


def _draw_cover(canvas, doc):
    canvas.saveState()
    w, h = A4
    # Top color block
    canvas.setFillColor(COVER_BLOCK)
    canvas.rect(0, h - 14*cm, w, 14*cm, fill=1, stroke=0)
    canvas.setFillColor(ACCENT)
    canvas.rect(0, h - 14*cm - 0.3*cm, w, 0.3*cm, fill=1, stroke=0)
    # Title
    canvas.setFillColor(colors.white)
    canvas.setFont('BodySerifB', 28)
    canvas.drawString(2*cm, h - 5.5*cm, "GLM Iteration 2")
    canvas.drawString(2*cm, h - 7*cm,   "Exact Reasoning via the")
    canvas.drawString(2*cm, h - 8.5*cm, "Layered Perspective")
    canvas.setFont('BodySans', 12)
    canvas.setFillColor(colors.HexColor('#e8e6df'))
    canvas.drawString(2*cm, h - 9.6*cm,
                       "What does it take to get this substrate to reason exactly?")
    canvas.drawString(2*cm, h - 10.4*cm,
                       "Golay as measuring device, wobble path shapes, escalation triggers.")
    # Metadata
    canvas.setFillColor(TEXT_PRIMARY); canvas.setFont('BodySerifB', 11)
    y0 = h - 16*cm
    canvas.drawString(2*cm, y0, "Phases")
    canvas.setFont('BodySerif', 10); canvas.setFillColor(TEXT_MUTED)
    canvas.drawString(2*cm, y0 - 0.5*cm, "  P1 Golay-syndrome cost atlas (Golay as measuring device)")
    canvas.drawString(2*cm, y0 - 0.9*cm, "  P2 Delta-sigma wobble + hull certificate")
    canvas.drawString(2*cm, y0 - 1.3*cm, "  P3 Leech native 24-D wobble (full 196,560 minimal vectors)")
    canvas.drawString(2*cm, y0 - 1.7*cm, "  P4 Per-step cost analysis (escalation triggers in multi-step traces)")
    canvas.setFillColor(TEXT_PRIMARY); canvas.setFont('BodySerifB', 11)
    canvas.drawString(2*cm, y0 - 2.6*cm, "Headline finding")
    canvas.setFont('BodySerif', 10); canvas.setFillColor(TEXT_MUTED)
    canvas.drawString(2*cm, y0 - 3.1*cm,
                       "  Every binary task target lies OUTSIDE the convex hull of the 4,096 Golay")
    canvas.drawString(2*cm, y0 - 3.5*cm,
                       "  codewords (Phase 2). Translate's mask_block and erase_old steps sit at")
    canvas.drawString(2*cm, y0 - 3.9*cm,
                       "  deep holes (coset wt = 4) in 100% of trials (Phase 4) — the substrate")
    canvas.drawString(2*cm, y0 - 4.3*cm,
                       "  mathematically cannot decide which octad to credit. This is the layered")
    canvas.drawString(2*cm, y0 - 4.7*cm,
                       "  perspective in action: failure indicates the required mechanism for")
    canvas.drawString(2*cm, y0 - 5.1*cm,
                       "  progression up the ladder (Golay -> Leech -> Barnes-Wall).")
    canvas.restoreState()


def make_styles():
    ss = getSampleStyleSheet()
    body = ParagraphStyle('Body', parent=ss['BodyText'],
                           fontName='BodySerif', fontSize=10.5, leading=15.5,
                           alignment=TA_LEFT, textColor=TEXT_PRIMARY, spaceAfter=8)
    h1 = ParagraphStyle('H1', parent=ss['Heading1'], fontName='BodySerifB',
                          fontSize=18, leading=22, textColor=HEADER_FILL,
                          spaceBefore=14, spaceAfter=10, keepWithNext=1)
    h2 = ParagraphStyle('H2', parent=ss['Heading2'], fontName='BodySerifB',
                          fontSize=13, leading=17, textColor=ACCENT,
                          spaceBefore=10, spaceAfter=6, keepWithNext=1)
    h3 = ParagraphStyle('H3', parent=ss['Heading3'], fontName='BodySerifB',
                          fontSize=11, leading=14, textColor=TEXT_PRIMARY,
                          spaceBefore=6, spaceAfter=4, keepWithNext=1)
    callout = ParagraphStyle('Callout', parent=body, fontName='BodySerifB',
                              fontSize=10.5, textColor=ACCENT_2,
                              leftIndent=10, spaceBefore=4, spaceAfter=10)
    return body, h1, h2, h3, callout


def build_story():
    body, h1, h2, h3, callout = make_styles()
    S = lambda h: Spacer(1, h)
    story = []
    story.append(PageBreak())  # body starts on page 2 (cover on page 1)

    # ====== Section 1: Executive Summary ======
    story.append(Paragraph("1.  Executive Summary", h1))
    story.append(Paragraph(
        "Iteration 1 established that the F<sub>2</sub> binary quotient of the "
        "Golay code adds <b>no transfer power</b> beyond an arbitrary linear "
        "projection (249/250 identical trials). Iteration 2 asks the deeper "
        "question the user posed: <i>what does it take to get this substrate "
        "to reason exactly?</i> The user's clarifications mapped directly onto "
        "the GLM academic paper's existing machinery — the delta-sigma "
        "modulator (the 'wobble'), the hull certificate, and the layered "
        "perspective where each layer's failure indicates the required "
        "mechanism for progression up the ladder.", body))
    story.append(Paragraph(
        "We ran four phases against the actual GLM substrate. Phase 1 measures "
        "the Golay syndrome and TAX cost of every binary transition (Golay as a "
        "measuring device, per clarification a). Phase 2 runs the substrate's "
        "<font name='Mono' size='9'>exact_real.golay_delta_sigma</font> wobble on each "
        "task target and uses the <font name='Mono' size='9'>hull_certificate</font> "
        "to test reachability. Phase 3 implements a Leech native 24-D wobble "
        "using the full 196,560 minimal vectors. Phase 4 measures per-step "
        "cost in multi-step transformation traces to identify escalation "
        "triggers.", body))

    story.append(Paragraph("Headline findings:", h3))
    story.append(Paragraph(
        "1. <b>Phase 1 (Golay as measuring device):</b> each task family has a "
        "characteristic syndrome signature. Toggle has coset wt = 0 (the "
        "displacement IS a codeword) but codeword wt = 24 (TAX = 9.35, the "
        "highest). Translate has coset wt = 4 in 100% of trials — every "
        "transition is at a deep hole, the substrate cannot decide which octad "
        "to credit. Reflect_v is 79% at deep holes; flood_fill and "
        "bfs_shortest are well-defined (0% ambiguous).", body))
    story.append(Paragraph(
        "2. <b>Phase 2 (Golay wobble + hull certificate):</b> ALL 5 task family "
        "query grids lie <b>OUTSIDE the convex hull of the 4,096 Golay "
        "codewords</b> (100% hull-separation rate). The substrate "
        "mathematically cannot reach any of them via the Golay delta-sigma. "
        "The accumulator grows linearly at the predicted rate of ~1 per tick. "
        "Meanwhile, the constants (√2, π, e, 1/3, φ) all lie INSIDE the hull "
        "and the wobble tracks them with bounded accumulator and within-1/N "
        "deviation.", body))
    story.append(Paragraph(
        "3. <b>Phase 3 (Leech native 24-D wobble):</b> against the full 196,560 "
        "minimal vectors in R<sup>24</sup>, the constants √2 − 1 and φ − 1 "
        "CONVERGE (acc_max bounded at 5.67 and 26.19 respectively, deviation "
        "drops to 0.0063 for √2). But the binary task targets (encoded as ±4 "
        "per coordinate) all DIVERGE — the targets are outside the Leech shell "
        "hull too. This is the layered perspective: the Leech shell escalates "
        "the constants that the Golay alphabet handled, but binary grids need "
        "a further lift (the 32-D Barnes-Wall lattice, or proper Leech lattice "
        "points, not just the minimal-vector shell).", body))
    story.append(Paragraph(
        "4. <b>Phase 4 (per-step cost analysis):</b> the per-step breakdown "
        "shows WHERE the substrate fails. For translate, 2 of the 4 steps "
        "(mask_block and erase_old) sit at deep holes in 100% of trials — "
        "these are explicit escalation triggers. For toggle, the bitwise_not "
        "step is a CODEWORD operation (executable exactly at high TAX). For "
        "flood_fill and bfs_shortest, every step is well-defined.", body))
    story.append(S(6))

    # ====== Section 2: Phase 1 — Golay as Measuring Device ======
    story.append(Paragraph("2.  Phase 1 — Golay as measuring device", h1))
    story.append(Paragraph(
        "Per the user's clarification (a): <i>the Golay code isn't just for "
        "error correction, when we don't want to change data we use it as a "
        "measuring device to see the cost and inner working of any given data "
        "transaction.</i> For each transition x → y on a 4×6 binary grid (24 "
        "bits), we measure three quantities:", body))
    story.append(Paragraph(
        "&#8226; <b>Δ weight</b>: the Hamming weight of x &#8853; y — the number of cells "
        "that change. This is a content-blind count.<br/>"
        "&#8226; <b>coset weight</b>: the syndrome of x &#8853; y in F<sub>2</sub><sup>24</sup> / "
        "G<sub>24</sub>, in {0, 1, 2, 3, 4}. This is the F<sub>2</sub> cost of the "
        "transition. coset wt = 0 means the displacement IS a codeword (the F<sub>2</sub> "
        "quotient sees it as a no-op). coset wt = 4 means a deep hole (sextet "
        "ambiguity — the substrate cannot decide which octad to credit).<br/>"
        "&#8226; <b>TAX</b>: w × (Y + 1/8) where Y = 1/(π + 2/π) ≈ 0.2647 and w is the "
        "Hamming weight of the nearest codeword to the displacement. The minimum "
        "non-zero TAX is at octads (w = 8), giving 8Y + 1 = 3.1174.", body))

    img = Image(f"{PLOT_DIR}/cost_atlas_bars.png")
    img.drawWidth = 16.5*cm
    img.drawHeight = img.drawWidth * (4.5/13.0)
    story.append(img)
    story.append(Paragraph(
        "<i>Figure 1.</i> Per-task cost atlas. Left: mean Δ weight (bits changed) vs "
        "mean coset weight (F<sub>2</sub> cost). Right: TAX (codeword energy) and "
        "ambiguous-rate (fraction of transitions at deep holes). Toggle has the "
        "highest TAX (codeword wt 24); translate is 100% ambiguous; flood_fill "
        "and bfs_shortest are well-defined.", body))

    img = Image(f"{PLOT_DIR}/coset_weight_heatmap.png")
    img.drawWidth = 13*cm
    img.drawHeight = img.drawWidth * (4.5/8.0)
    story.append(img)
    story.append(Paragraph(
        "<i>Figure 2.</i> Coset weight distribution per task (row-normalised). Toggle "
        "is 100% at coset wt 0 (the all-ones codeword displacement). Translate is "
        "100% at coset wt 4 (deep hole). Reflect_v is 79% at wt 4 + 19% at wt 2. "
        "Flood_fill spans wts 1-3. BFS_shortest spans wts 0-4.", body))

    story.append(Paragraph(
        "<b>Interpretation.</b> The cost atlas reveals three distinct substrate-"
        "level failure modes. (1) <b>Toggle is information-free at the F<sub>2</sub> "
        "quotient</b>: its displacement IS a codeword, so the F<sub>2</sub> quotient "
        "sees the operation as a no-op (this is exactly why Iteration 1's "
        "Golay-coset solver failed on toggle). But the codeword weight is 24, "
        "the highest possible, so the operation carries high TAX — the substrate "
        "would have to lift to the codeword-weight layer to see the operation. "
        "(2) <b>Translate is fundamentally ambiguous</b>: every transition sits at "
        "a deep hole, where 6 codewords are equidistant. The substrate cannot "
        "decide which octad to credit; this is a forced escalation trigger. "
        "(3) <b>Flood_fill and BFS_shortest are well-defined</b>: the substrate "
        "handles them via syndrome decoding with no ambiguity.", body))

    story.append(PageBreak())

    # ====== Section 3: Phase 2 — Wobble signatures + hull certificate ======
    story.append(Paragraph("3.  Phase 2 — Delta-sigma wobble + hull certificate", h1))
    story.append(Paragraph(
        "Per the user's clarification (b): <i>looking simply at the difference "
        "between any two data changes is not enough, we also need to look at "
        "the path it takes, not just the start/end points or nodes - what is "
        "the exact shape of this 'decision'.</i> The GLM academic paper (§5.2-5.3) "
        "introduces the delta-sigma modulator — a deterministic error-feedback "
        "loop where an accumulator integrates (target − emitted), the quantiser "
        "(Golay snap) forces the value back to the nearest codeword, and the "
        "running mean of emitted codewords converges to the target at rate 1/N. "
        "The trajectory of codewords visited IS the path shape of the decision.", body))

    story.append(Paragraph("3.1  Constants baseline", h2))
    story.append(Paragraph(
        "We first ran the wobble on six known constants (each placed in all 24 "
        "coordinates) as a reference. The GLM paper reports these have distinct "
        "vibrational signatures (§5.4). The substrate confirms: √2−1 visits 2 "
        "codewords with share 0.585 (a quasiperiodic alternation); π−3 visits 2 "
        "codewords with share 0.858 (a more lopsided alternation); 1/3 has share "
        "0.667; e−2 has share 0.718; φ−1 has share 0.618 (the golden ratio "
        "in the orbit itself).", body))

    img = Image(f"{PLOT_DIR}/wobble_signatures.png")
    img.drawWidth = 16*cm
    img.drawHeight = img.drawWidth * (5/13.0)
    story.append(img)
    story.append(Paragraph(
        "<i>Figure 3.</i> Wobble signatures on constants (left) and task targets "
        "(right). Constants visit ~2 codewords with bounded accumulator (sublinear "
        "growth, the wobble tracks them). Task targets visit 1 codeword with "
        "linearly-growing accumulator — the wobble is stuck.", body))

    story.append(Paragraph("3.2  Hull certificate", h2))
    story.append(Paragraph(
        "The substrate's <font name='Mono' size='9'>hull_certificate</font> runs the "
        "wobble with the minimum-norm rule, takes the accumulator's drift "
        "direction as a candidate separating functional c, and verifies exactly "
        "against all 4,096 codewords: if &#10216;c, target&#10217; exceeds "
        "&#10216;c, w&#10217; for every codeword w, the target is provably "
        "outside the convex hull and unreachable by ANY quantiser rule. This is "
        "an exact mathematical certificate, not a measurement.", body))

    img = Image(f"{PLOT_DIR}/hull_separation.png")
    img.drawWidth = 16*cm
    img.drawHeight = img.drawWidth * (4.5/11.0)
    story.append(img)
    story.append(Paragraph(
        "<i>Figure 4.</i> Hull-separation rate. Green bars (constants) are inside "
        "the hull (reachable); red bars (task targets) are 100% outside. Every "
        "binary task target is provably unreachable by the Golay delta-sigma — "
        "the substrate must escalate.", body))

    story.append(Paragraph(
        "<b>Verdict for Phase 2:</b> the binary task targets lie provably outside "
        "the Golay hull. The substrate CANNOT reach them with the 4,096-codeword "
        "alphabet. The accumulator grows linearly at exactly the rate the GLM "
        "paper's §8.4 'wall' theorem predicts. This is the layered perspective's "
        "first failure: the Golay layer cannot reason about binary "
        "transformations on grids; escalation to the Leech layer is required.", callout))

    story.append(PageBreak())

    # ====== Section 4: Phase 3 — Leech native 24-D wobble ======
    story.append(Paragraph("4.  Phase 3 — Leech native 24-D wobble", h1))
    story.append(Paragraph(
        "Per the user's clarification (d): <i>the Leech in its native 24-D is "
        "the natural progression, according to GLM findings there is a layered "
        "perspective to almost all things where failure indicated the required "
        "mechanism for progression up the ladder.</i> Phase 2 showed that "
        "every binary task target lies outside the Golay hull. Phase 3 tests "
        "whether the Leech lattice's 196,560 minimal vectors — points in "
        "R<sup>24</sup>, not in F<sub>2</sub><sup>24</sup> — can reach them.", body))

    story.append(Paragraph(
        "We implemented the matched-rule delta-sigma (the GLM paper's Rule 2, "
        "§8.4): at each tick, emit the minimal vector v that maximises "
        "&#10216;v, accumulator + target&#10217; (the support function). Update "
        "the accumulator by subtracting v. The running mean of emitted vectors "
        "converges to the target iff the target is in the convex hull of the "
        "alphabet (a paper theorem, §8.4).", body))

    img = Image(f"{PLOT_DIR}/leech_vs_golay_wobble.png")
    img.drawWidth = 16*cm
    img.drawHeight = img.drawWidth * (5/11.0)
    story.append(img)
    story.append(Paragraph(
        "<i>Figure 5.</i> Golay vs Leech wobble on constants baseline. √2−1 and "
        "φ−1 CONVERGE on the Leech shell (acc_max bounded at 5.67 and 26.19). "
        "Constants with target values close to ±4 (the alphabet's per-coordinate "
        "maximum) still diverge.", body))

    story.append(Paragraph(
        "<b>Result for binary task targets:</b> all 5 task families diverge on the "
        "Leech shell alphabet (acc_max around 600-680 over 200 ticks). The "
        "bipolar ±4 encoding of binary grids places the target outside the "
        "Leech minimal-vector hull — the target has all 24 coordinates nonzero "
        "(norm² = 24 × 16 = 384, far exceeding the alphabet's 32), so no convex "
        "combination of alphabet vectors (each with at most 8 nonzero "
        "coordinates) can produce it.", body))

    story.append(Paragraph(
        "<b>Verdict for Phase 3:</b> the Leech shell alphabet (196,560 minimal "
        "vectors) escalates the constants that the Golay alphabet handled "
        "(√2 and φ converge here), but the binary task targets require a "
        "further lift. The next layers per the GLM paper are: (a) the full Leech "
        "lattice (all integer points, not just minimal vectors — but the "
        "Construction-C sieve requires substantial implementation); (b) the "
        "32-dimensional Barnes-Wall lattice Λ<sub>32</sub>, which has three "
        "nested resolutions (4Z<sup>32</sup> ⊂ 2·RM(3,5) ⊂ RM(1,5)) and can "
        "represent multi-resolution structures natively; (c) the 48-dimensional "
        "ternary lattice Λ<sub>48</sub>, which is 16,834× denser per unit cell "
        "but abandons the binary picture entirely.", callout))

    story.append(PageBreak())

    # ====== Section 5: Phase 4 — Per-step cost (escalation triggers) ======
    story.append(Paragraph("5.  Phase 4 — Per-step cost in multi-step traces", h1))
    story.append(Paragraph(
        "Per the user's clarification (c): <i>intermediate steps are part of "
        "(b) here - we need to take every operation step-by-step and explicitly "
        "measure, map and investigate each step - this is the information the "
        "GLM is to learn from.</i> For each task with a multi-step trace, we "
        "measure the per-step coset weight, codeword weight, and TAX. The "
        "spikes in this curve are the 'decision points' the GLM must learn.", body))

    img = Image(f"{PLOT_DIR}/per_step_costs.png")
    img.drawWidth = 17*cm
    img.drawHeight = img.drawWidth * (8/15.0)
    story.append(img)
    story.append(Paragraph(
        "<i>Figure 6.</i> Per-step cost across the 5 task families. Red shaded "
        "zones mark steps where coset wt ≈ 4 (deep hole — escalation trigger). "
        "Toggle's bitwise_not step is a codeword operation (cw wt 24, TAX 9.35). "
        "Translate's mask_block and erase_old steps are 100% at deep holes. "
        "Flood_fill and BFS_shortest are well-defined throughout.", body))

    # Per-step summary table
    story.append(Paragraph("5.1  Per-task breakdown", h2))
    cell_style = ParagraphStyle('Cell', fontName='BodySerif', fontSize=8.5,
                                  leading=11, textColor=TEXT_PRIMARY)
    cell_head  = ParagraphStyle('CellHead', fontName='BodySerifB', fontSize=9,
                                  leading=11, textColor=colors.white, alignment=TA_CENTER)
    rows = [
        ["Task", "Step", "Δ wt", "coset wt", "TAX", "ambig %", "cw wt"],
        ["toggle", "init",           "0.0", "0.0", "0.0",   "0%",   "0"],
        ["toggle", "bitwise_not",     "24.0", "0.0", "9.352", "0%",   "24"],
        ["translate", "init",         "0.0", "0.0", "0.0",   "0%",   "0"],
        ["translate", "mask_block",   "6.0", "4.0", "3.117", "100%", "8"],
        ["translate", "erase_old",    "10.0", "4.0", "3.117", "100%", "8"],
        ["translate", "paint_new",    "2.0", "2.0", "0.0",   "0%",   "0"],
        ["reflect_v", "flip_horizontal", "8.68", "3.48", "2.837", "78%", "7.3"],
        ["flood_fill", "fill_interior",  "2.14", "2.14", "0.0", "0%", "0"],
        ["bfs_shortest", "step_vertical",   "0.87", "0.87", "0.0", "0%", "0"],
        ["bfs_shortest", "step_horizontal", "0.53", "0.53", "0.0", "0%", "0"],
    ]
    wrapped = []
    for i, row in enumerate(rows):
        if i == 0:
            wrapped.append([Paragraph(c, cell_head) for c in row])
        else:
            wrapped.append([Paragraph(c, cell_style) for c in row])
    cw = [2.0*cm, 2.6*cm, 1.5*cm, 2.0*cm, 1.8*cm, 2.0*cm, 1.5*cm]
    t = Table(wrapped, colWidths=cw, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HEADER_FILL),
        ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, TABLE_STRIPE]),
        # Highlight escalation-trigger rows (translate mask_block and erase_old)
        ('BACKGROUND', (0,4), (-1,5), colors.HexColor('#ffe5e5')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t)
    story.append(Paragraph(
        "<i>Table 1.</i> Per-step cost. Rows 4-5 (translate's mask_block and "
        "erase_old) are highlighted as escalation triggers — both sit at deep "
        "holes in 100% of trials.", body))

    story.append(Paragraph("5.2  Interpretation: the layered perspective in action", h2))
    story.append(Paragraph(
        "The per-step breakdown reveals the precise location where the substrate "
        "fails. For translate, two of the four intermediate steps (mask_block "
        "and erase_old) are at deep holes — the substrate cannot execute them "
        "deterministically because 6 octads are equidistant from the "
        "displacement. To make progress, the substrate MUST escalate to a "
        "higher lattice (Leech Λ<sub>24</sub> or Barnes-Wall Λ<sub>32</sub>) "
        "where the 6-way ambiguity can be resolved.", body))
    story.append(Paragraph(
        "For toggle, the entire operation is a codeword move (the all-ones "
        "codeword), executable exactly at high TAX. The substrate does not "
        "need to escalate — it just needs to lift from the F<sub>2</sub> "
        "quotient to the codeword-weight layer.", body))
    story.append(Paragraph(
        "For flood_fill and bfs_shortest, every step is well-defined (coset "
        "weight ≤ 3, 0% ambiguous). The substrate handles these directly via "
        "syndrome decoding — no escalation needed. This is a useful prior: "
        "these task families should be solvable by the binary recurrent GLM "
        "(Iteration 1's Experiment B) at high accuracy, which is exactly what "
        "we observed (100% and 89% EM respectively).", body))

    story.append(PageBreak())

    # ====== Section 6: The layered perspective ======
    story.append(Paragraph("6.  The layered perspective: escalation ladder", h1))
    story.append(Paragraph(
        "Synthesising across all four phases, the layered perspective the GLM "
        "academic paper predicts is now concretely demonstrated. Each layer's "
        "failure mode indicates the required mechanism for progression up the "
        "ladder:", body))

    img = Image(f"{PLOT_DIR}/escalation_ladder.png")
    img.drawWidth = 17*cm
    img.drawHeight = img.drawWidth * (6/12.0)
    story.append(img)
    story.append(Paragraph(
        "<i>Figure 7.</i> The escalation ladder from F<sub>2</sub><sup>24</sup>/G<sub>24</sub> "
        "to the ternary Λ<sub>48</sub> lattice. Red annotations mark where "
        "each layer fails (Phases 1, 2, 3 results) and what the next layer "
        "must provide.", body))

    story.append(Paragraph("6.1  What we now know", h2))
    story.append(Paragraph(
        "<b>1.</b> The binary alphabet {0,1}<sup>24</sup> is NOT a subset of the "
        "Golay code's convex hull. Most binary vectors lie outside that hull, "
        "and the substrate proves this via an exact separating functional "
        "(Phase 2). This is the F<sub>2</sub> quotient's fundamental limitation "
        "for representing binary state — it explains why Iteration 1's "
        "Golay-coset solver produced 0% accuracy on toggle (the substrate "
        "literally cannot reach the target).", body))
    story.append(Paragraph(
        "<b>2.</b> The Leech shell alphabet (196,560 minimal vectors in "
        "R<sup>24</sup>) escalates the constants that the Golay alphabet "
        "handled (Phase 3). √2 − 1 and φ − 1 converge on the Leech shell with "
        "bounded accumulator and within-1/N deviation. But binary grid targets "
        "(encoded as ±4 per coordinate) lie outside the Leech shell hull too — "
        "the per-coordinate magnitudes are too large for the alphabet's "
        "structure.", body))
    story.append(Paragraph(
        "<b>3.</b> The per-step cost atlas (Phase 4) gives a precise map of "
        "WHERE each task family fails. Translate fails specifically at the "
        "mask_block and erase_old steps (deep holes, 100% ambiguous). Toggle "
        "doesn't fail at the binary level — it succeeds as a codeword "
        "operation. Flood_fill and bfs_shortest succeed throughout. This map "
        "tells the GLM exactly which steps need escalation and which can be "
        "handled at the binary layer.", body))

    story.append(Paragraph("6.2  What it takes to reason exactly", h2))
    story.append(Paragraph(
        "Answering the user's headline question: <b>to reason exactly on binary "
        "transformations, the substrate must (i) lift from the F<sub>2</sub> "
        "quotient to the codeword-weight layer for codeword operations "
        "(toggle's TAX = 9.35 is visible there); (ii) escalate to the Leech "
        "lattice for binary targets outside the Golay hull; (iii) further lift "
        "to the Barnes-Wall Λ<sub>32</sub> or ternary Λ<sub>48</sub> for "
        "targets outside the Leech shell hull.</b> Each layer has a specific "
        "failure mode (coset wt 0, coset wt 4, hull separation, target "
        "magnitude) that indicates exactly which lift is required.", body))
    story.append(Paragraph(
        "<b>For the specific binary tasks in this experiment:</b> flood_fill "
        "and bfs_shortest can be reasoned about at the binary layer (Phase 4 "
        "shows 0% ambiguity throughout); toggle requires the codeword-weight "
        "layer (TAX = 9.35, codeword wt 24); translate and reflect_v require "
        "the Leech layer or higher (deep holes in 100% and 79% of steps "
        "respectively).", callout))

    story.append(Paragraph("6.3  What this enables for the GLM", h2))
    story.append(Paragraph(
        "The per-step cost map (Phase 4) is exactly the information the GLM "
        "needs to learn from. A trainable GLM recurrent update F<sub>θ</sub> "
        "can use the per-step syndrome and TAX as supervisory signals — when "
        "the substrate encounters a deep hole (coset wt 4), it should learn to "
        "switch to a higher-lattice quantiser. This is the natural extension "
        "of Iteration 1's Experiment B (trace supervision): instead of only "
        "supervising the intermediate grids, we also supervise the <i>cost</i> "
        "at each step — the syndrome, the TAX, and the hull certificate. The "
        "GLM learns not just 'what is the right answer' but 'what is the right "
        "lattice layer for this step'.", body))

    story.append(PageBreak())

    # ====== Section 7: Verdicts and next iterations ======
    story.append(Paragraph("7.  Verdicts and next iterations", h1))

    # Verdict table
    cell_style = ParagraphStyle('Cell', fontName='BodySerif', fontSize=8.5,
                                  leading=11, textColor=TEXT_PRIMARY)
    cell_head  = ParagraphStyle('CellHead', fontName='BodySerifB', fontSize=9,
                                  leading=11, textColor=colors.white, alignment=TA_CENTER)
    cell_verd  = ParagraphStyle('CellVerd', fontName='BodySerifB', fontSize=9,
                                  leading=11, textColor=TEXT_PRIMARY, alignment=TA_CENTER)
    verdict_rows = [
        ["Phase", "Hypothesis", "Verdict", "Evidence"],
        ["Phase 1",
         "Golay syndrome measures the cost of every binary transition",
         "CONFIRMED",
         "Each task family has a characteristic signature. Toggle: codeword op (TAX 9.35). Translate: 100% deep holes. Flood_fill, BFS: well-defined."],
        ["Phase 2",
         "Wobble path shape + hull certificate distinguish reachable from unreachable targets",
         "CONFIRMED",
         "Constants converge (acc bounded, dev ≤ 1/N). Task targets all 100% hull-separate. Substrate proves unreachability exactly."],
        ["Phase 3",
         "Leech native 24-D wobble escalates constants the Golay alphabet handled",
         "PARTIALLY CONFIRMED",
         "√2−1 and φ−1 converge on Leech shell (acc bounded at 5.67, 26.19). Binary task targets still diverge — outside Leech shell hull."],
        ["Phase 4",
         "Per-step cost reveals escalation triggers (where the substrate cannot decide)",
         "CONFIRMED",
         "Translate: mask_block + erase_old at deep holes in 100% of trials. Toggle: bitwise_not is codeword op (TAX 9.35). Flood_fill, BFS: 0% ambiguous."],
    ]
    wrapped = []
    for i, row in enumerate(verdict_rows):
        if i == 0:
            wrapped.append([Paragraph(c, cell_head) for c in row])
        else:
            wrapped.append([
                Paragraph(row[0], cell_verd),
                Paragraph(row[1], cell_style),
                Paragraph(row[2], cell_verd),
                Paragraph(row[3], cell_style),
            ])
    cw = [1.8*cm, 4.5*cm, 2.5*cm, 7.6*cm]
    t = Table(wrapped, colWidths=cw, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HEADER_FILL),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('ALIGN', (2,1), (2,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, TABLE_STRIPE]),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t)
    story.append(S(8))

    story.append(Paragraph("7.1  Recommended next iterations", h2))
    story.append(Paragraph(
        "Three concrete follow-ups, in priority order:", body))
    story.append(Paragraph(
        "<b>1. Implement the full Leech lattice snap (Construction C).</b> The "
        "Phase 3 result used the 196,560 minimal vectors as the alphabet — "
        "but the Leech lattice itself contains all integer combinations of "
        "those vectors, not just the minimal ones. The Construction-C sieve "
        "(mod-2 parity → mod-4 Golay → mod-8 sum + odd coset) is the standard "
        "snap-to-nearest-Leech-point algorithm. Implementing it would let "
        "binary grid targets be encoded as proper Leech lattice points, "
        "which the wobble can then track. This is the most direct test of "
        "whether the Leech layer can reach what the Golay layer cannot.", body))
    story.append(Paragraph(
        "<b>2. Train a GLM recurrent update with per-step cost supervision.</b> "
        "Extend Iteration 1's Experiment B by adding a cost-head to the "
        "model: at each step, the model predicts not just the next grid but "
        "also the syndrome, TAX, and hull-membership of the transition. The "
        "loss combines grid-BCE + cost-MSE. The hypothesis: a model that "
        "learns to predict the per-step cost will learn to <i>choose</i> "
        "the right lattice layer for each step, escalating when needed. This "
        "is the operational form of 'the GLM is taught the path shape, not "
        "just the endpoints'.", body))
    story.append(Paragraph(
        "<b>3. Lift to the 32-D Barnes-Wall lattice Λ<sub>32</sub>.</b> The GLM "
        "academic paper (§8.2) describes Λ<sub>32</sub>'s three nested "
        "resolutions (4Z<sup>32</sup> ⊂ 2·RM(3,5) ⊂ RM(1,5)) as providing "
        "'three usable resolutions where Λ<sub>24</sub> provides one — a "
        "coarse address that is usable on its own and refinable later.' The "
        "binary task targets in our experiment may require this multi-"
        "resolution structure to be reachable. This is a substantially larger "
        "implementation effort (the substrate has <font name='Mono' size='9'>"
        "lattice32.py</font> with the construction, but no wobble against it).", body))

    story.append(Paragraph("7.2  What did NOT work", h2))
    story.append(Paragraph(
        "Two design choices that did not work and are worth flagging for the "
        "next iteration: (1) The first Phase 3 attempt used only the 1,104 "
        "sparse-shell minimal vectors (shape (±4², 0²²)) as the alphabet. "
        "This alphabet was too small — even constants like √2 failed to "
        "converge. Switching to the full 196,560 minimal vectors fixed the "
        "constants (√2 and φ now converge) but the binary task targets still "
        "fail because the ±4 encoding puts them outside the alphabet's per-"
        "coordinate range. (2) The bipolar ±4 encoding of binary grids was "
        "naive — each coordinate becomes ±4, but the Leech minimal vectors "
        "have at most 8 nonzero coordinates, so a target with all 24 nonzero "
        "is structurally outside the alphabet's hull. The right encoding is "
        "to map each binary grid to its nearest Leech lattice point via "
        "Construction C (which preserves the 24-bit information at the Leech "
        "level).", body))

    story.append(Paragraph("7.3  Limitations", h2))
    story.append(Paragraph(
        "All experiments were CPU-only on 4×6 binary grids. The Phase 2 "
        "hull-certificate result (100% separation for binary task targets) "
        "is exact and exhaustive — it's a mathematical certificate, not a "
        "measurement, so it cannot be disputed by sampling more. The Phase 3 "
        "Leech shell wobble used 200 ticks per target; longer runs would give "
        "tighter convergence bounds but would not change the qualitative "
        "result (constants converge, binary targets diverge). The Phase 4 "
        "per-step cost atlas is on 50 samples per task family — enough for "
        "the means and ambiguity rates to be statistically meaningful but "
        "not for fine-grained per-step distribution analysis. The next "
        "iteration's full-Leech-snap implementation (recommendation 1 above) "
        "is the highest-leverage follow-up: it would either confirm or refute "
        "the layered-progression hypothesis directly.", body))

    return story


def main():
    os.makedirs(os.path.dirname(OUT_PDF), exist_ok=True)
    doc = SimpleDocTemplate(OUT_PDF, pagesize=A4,
                              leftMargin=2*cm, rightMargin=2*cm,
                              topMargin=2*cm, bottomMargin=2*cm,
                              title="GLM Iteration 2 — Exact Reasoning via the Layered Perspective",
                              author="Z.ai",
                              subject="What does it take to get this substrate to reason exactly?",
                              creator="Z.ai")
    story = build_story()
    doc.build(story, onFirstPage=_draw_cover, onLaterPages=_draw_page)
    print(f"Wrote: {OUT_PDF}")
    print(f"Size: {os.path.getsize(OUT_PDF)/1024:.1f} KB")


if __name__ == "__main__":
    main()
