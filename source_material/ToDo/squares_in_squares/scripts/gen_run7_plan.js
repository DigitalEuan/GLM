/* gen_run7_plan.js — Run 7 Strategic Plan (English, report/plan scene).
   Cover: recipe R4 (Top Color Block) + palette GO-1, per design-system.md
   routing (docType plan -> R4/GO-1). Title 20 chars (<=20, no override).
   Fonts: Profile A English — Times New Roman body/headings, pure black body.
   Sections: 1 cover (margin 0, no page number) / 2 front matter (TOC, Roman) /
   3 body (Arabic from 1). Tables: Horizontal-Only with GO-1 table tokens. */
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  ImageRun, PageBreak, Header, Footer, PageNumber, NumberFormat,
  AlignmentType, HeadingLevel, WidthType, BorderStyle, ShadingType,
  TableLayoutType, SectionType, TableOfContents,
} = require("docx");
const fs = require("fs");

/* ---------------- palette (GO-1, from design-system.md) ---------------- */
const PAL = {
  bg: "1A2330", primary: "1A2330", accent: "D4875A",
  cover: { titleColor: "FFFFFF", subtitleColor: "B0B8C0", metaColor: "90989F", footerColor: "687078" },
  table: { headerBg: "D4875A", headerText: "FFFFFF", innerLine: "DDD0C8", surface: "F8F0EB" },
};
const HEADING_COLOR = "1A2330";
const BODY = "000000";
const SECONDARY = "606060";

const NB = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: NB, bottom: NB, left: NB, right: NB };
const allNoBorders = { top: NB, bottom: NB, left: NB, right: NB, insideHorizontal: NB, insideVertical: NB };
const emptyPara = () => new Paragraph({ children: [] });

/* ---------------- title layout (from design-system.md; width factor
   adapted for Latin text: CJK chars are ~pt*20 twips wide, Latin mixed-case
   averages ~pt*11 — the CJK factor would split this English title badly) */
function splitTitleLines(title, charsPerLine) {
  if (title.length <= charsPerLine) return [title];
  const breakAfter = new Set([..."，。、；：！？", ..."的与和及之在于为", ..."-_—–·/", ..." \t"]);
  const lines = [];
  let remaining = title;
  while (remaining.length > charsPerLine) {
    let breakAt = -1;
    for (let i = charsPerLine; i >= Math.floor(charsPerLine * 0.6); i--) {
      if (i < remaining.length && breakAfter.has(remaining[i - 1])) { breakAt = i; break; }
    }
    if (breakAt === -1) {
      const limit = Math.min(remaining.length, Math.ceil(charsPerLine * 1.3));
      for (let i = charsPerLine + 1; i < limit; i++) {
        if (breakAfter.has(remaining[i - 1])) { breakAt = i; break; }
      }
    }
    if (breakAt === -1) breakAt = charsPerLine;
    lines.push(remaining.slice(0, breakAt).trim());
    remaining = remaining.slice(breakAt).trim();
  }
  if (remaining) lines.push(remaining);
  if (lines.length > 1 && lines[lines.length - 1].length <= 2) {
    const last = lines.pop();
    lines[lines.length - 1] += " " + last;
  }
  return lines;
}
function calcTitleLayout(title, maxWidthTwips, preferredPt = 40, minPt = 24) {
  const charWidth = (pt) => pt * 11;               // Latin factor (see header note)
  const charsPerLine = (pt) => Math.floor(maxWidthTwips / charWidth(pt));
  let titlePt = preferredPt, lines;
  while (titlePt >= minPt) {
    const cpl = charsPerLine(titlePt);
    if (cpl < 2) { titlePt -= 2; continue; }
    lines = splitTitleLines(title, cpl);
    if (lines.length <= 3) break;
    titlePt -= 2;
  }
  if (!lines || lines.length > 3) { lines = splitTitleLines(title, charsPerLine(minPt)); titlePt = minPt; }
  return { titlePt, titleLines: lines };
}

/* ---------------- cover: recipe R4 (copied from design-system.md) ------- */
function buildCoverR4(config) {
  const P = config.palette;
  const padL = 1200, padR = 800;
  const availableWidth = 11906 - padL - padR;
  const { titlePt, titleLines } = calcTitleLayout(config.title, availableWidth, 40, 26);
  const titleSize = titlePt * 2;
  const titleBlockHeight = titleLines.length * (titlePt * 23 + 200);
  const englishLabelH = config.englishLabel ? (9 * 23 + 500) : 0;
  const subtitleH = config.subtitle ? (12 * 23 + 200) : 0;
  const upperContentH = englishLabelH + titleBlockHeight + subtitleH;
  const UPPER_MIN = 7500;
  const UPPER_H = Math.max(UPPER_MIN, upperContentH + 1500 + 800);
  const DIVIDER_H = 60;
  const contentEstimate = englishLabelH + titleBlockHeight + subtitleH;
  const spacerIntrinsic = 280;
  const topSpacing = Math.max(UPPER_H - contentEstimate - spacerIntrinsic - 800, 400);

  const upperBlock = new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    layout: TableLayoutType.FIXED,
    borders: allNoBorders,
    rows: [new TableRow({
      height: { value: UPPER_H, rule: "exact" },
      children: [new TableCell({
        shading: { type: ShadingType.CLEAR, fill: P.bg }, borders: noBorders,
        verticalAlign: "top",
        margins: { left: padL, right: padR },
        children: [
          new Paragraph({ spacing: { before: topSpacing } }),
          config.englishLabel ? new Paragraph({
            spacing: { after: 500 },
            children: [new TextRun({ text: config.englishLabel.split("").join(" "),
              size: 18, color: P.accent, font: { ascii: "Calibri" }, characterSpacing: 60 })],
          }) : null,
          ...titleLines.map((line, i) => new Paragraph({
            spacing: { after: i < titleLines.length - 1 ? 100 : 200, line: Math.ceil(titlePt * 23), lineRule: "atLeast" },
            children: [new TextRun({ text: line, size: titleSize, bold: true,
              color: P.cover.titleColor, font: { eastAsia: "SimHei", ascii: "Arial" } })],
          })),
          config.subtitle ? new Paragraph({
            spacing: { after: 100 },
            children: [new TextRun({ text: config.subtitle, size: 24, color: P.cover.subtitleColor,
              font: { eastAsia: "Microsoft YaHei", ascii: "Arial" } })],
          }) : null,
        ].filter(Boolean),
      })],
    })],
  });

  const divider = new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: allNoBorders,
    rows: [new TableRow({
      height: { value: DIVIDER_H, rule: "exact" },
      children: [new TableCell({ borders: noBorders,
        shading: { type: ShadingType.CLEAR, fill: P.accent }, children: [emptyPara()] })],
    })],
  });

  const lowerContent = [
    new Paragraph({ spacing: { before: 800 } }),
    ...(config.metaLines || []).map(line => new Paragraph({
      indent: { left: padL }, spacing: { after: 100 },
      children: [new TextRun({ text: line, size: 28, color: P.cover.metaColor,
        font: { eastAsia: "Microsoft YaHei", ascii: "Arial" } })],
    })),
    new Paragraph({ spacing: { before: 2000 } }),
    new Paragraph({
      indent: { left: padL },
      children: [
        new TextRun({ text: config.footerLeft || "", size: 22, color: "909090" }),
        new TextRun({ text: "          " }),
        new TextRun({ text: config.footerRight || "", size: 22, color: "909090" }),
      ],
    }),
  ];

  return [new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    layout: TableLayoutType.FIXED,
    borders: allNoBorders,
    rows: [new TableRow({
      height: { value: 16838, rule: "exact" },
      children: [new TableCell({
        shading: { type: ShadingType.CLEAR, fill: "FFFFFF" }, borders: noBorders,
        verticalAlign: "top",
        children: [upperBlock, divider, ...lowerContent],
      })],
    })],
  })];
}

/* ---------------- body helpers (Profile A English) ---------------- */
const FONT = { ascii: "Times New Roman", eastAsia: "SimSun" };
const HFONT = { ascii: "Times New Roman", eastAsia: "SimHei" };

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 360, after: 160, line: 312 },
    children: [new TextRun({ text, bold: true, size: 32, color: HEADING_COLOR, font: HFONT })],
  });
}
function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 240, after: 120, line: 312 },
    children: [new TextRun({ text, bold: true, size: 28, color: HEADING_COLOR, font: HFONT })],
  });
}
function p(text, opts = {}) {
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    spacing: { line: 312, after: opts.after ?? 120 },
    children: [new TextRun({ text, size: 24, color: BODY, font: FONT })],
  });
}
function pRuns(runs, opts = {}) {
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    spacing: { line: 312, after: opts.after ?? 120 },
    children: runs.map(r => new TextRun({ size: 24, color: BODY, font: FONT, ...r })),
  });
}
function caption(text) {
  return new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { before: 80, after: 200, line: 312 },
    children: [new TextRun({ text, size: 21, color: SECONDARY, font: FONT })],
  });
}
function tableTitle(text) {
  return new Paragraph({
    keepNext: true, spacing: { before: 200, after: 100, line: 312 },
    children: [new TextRun({ text, bold: true, size: 21, color: HEADING_COLOR, font: FONT })],
  });
}
function makeTable(headers, rows, widths) {
  const T = PAL.table;
  const cell = (text, { header = false, i = 0 } = {}) => new TableCell({
    children: [new Paragraph({
      spacing: { line: 276 },
      children: [new TextRun({ text: String(text), bold: header, size: 20,
        color: header ? T.headerText : BODY, font: FONT })],
    })],
    shading: header ? { type: ShadingType.CLEAR, fill: T.headerBg }
      : (i % 2 === 1 ? { type: ShadingType.CLEAR, fill: T.surface } : undefined),
    margins: { top: 60, bottom: 60, left: 120, right: 120 },
    width: { size: 0, type: WidthType.PERCENTAGE },   // set below per column
  });
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: {
      top: { style: BorderStyle.SINGLE, size: 2, color: T.headerBg },
      bottom: { style: BorderStyle.SINGLE, size: 2, color: T.headerBg },
      left: NB, right: NB,
      insideHorizontal: { style: BorderStyle.SINGLE, size: 1, color: T.innerLine },
      insideVertical: NB,
    },
    rows: [
      new TableRow({
        tableHeader: true, cantSplit: true,
        children: headers.map((t, j) => {
          const c = cell(t, { header: true });
          c.options.width = { size: widths[j], type: WidthType.PERCENTAGE };
          return c;
        }),
      }),
      ...rows.map((r, i) => new TableRow({
        cantSplit: true,
        children: r.map((t, j) => {
          const c = cell(t, { i });
          c.options.width = { size: widths[j], type: WidthType.PERCENTAGE };
          return c;
        }),
      })),
    ],
  });
}
function readPngSize(buf) {
  return { width: buf.readUInt32BE(16), height: buf.readUInt32BE(20) };
}
function figure(path, cap, displayWidth) {
  const buf = fs.readFileSync(path);
  const { width, height } = readPngSize(buf);
  const w = displayWidth, h = Math.round(displayWidth * height / width);
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 160 },
      children: [new ImageRun({ data: buf, transformation: { width: w, height: h }, type: "png" })],
    }),
    caption(cap),
  ];
}

/* ---------------- content ------------------------------------------------ */
const body = [];

body.push(h1("1. Executive Summary"));
body.push(p("This plan takes stock of the squares-in-squares packing project at leaderboard position 1184 (platform score 23.193864 against a leading score of 22.0544214515, a gap of 1.139443) and commits to a phased program for the next runs. The verified local submission scores 23.173640, covers all 1000 puzzles, improves 407 of them over the standard grid, and matches the published survey catalogue everywhere, so every further point must come from open problems. The 593 grid-tied puzzles split into 31 perfect squares and 60 Nagamochi-class puzzles that are provably optimal, and 69 low-residue and 433 mid-band puzzles that are genuinely open."));
body.push(p("This run researched the untried GLM method the project flagged: the Lorentzian lift of LorentzianLift.lean. Its Lean-verified boundary theorem explains every negative result of the previous runs in one sentence: no rule invariant under reflections can break a tie, and all local physical dynamics are such rules. The compiled prototype then found and fixed two real defects in the shared search substrate, and for the first time drove open targets to residual overlaps of 1.5e-4 to 7.7e-4 at grid minus 0.002, roughly one hundred times closer to feasibility than the previous wall at 0.06. It does not close yet, and this plan says exactly what is missing."));
body.push(p("The quantified value ladder is the core planning fact. Marginal pushes at grid minus 0.002 across all 593 open puzzles are worth only 0.053314 in total, which does not move the ranking. The mid-band alone at grid minus 0.1 is worth 1.848594, taking the score to 21.325046 and past the current leader on its own. The program is therefore re-aimed: stop buying epsilon, start constructing mid-band motifs at real depth. Phase 0 re-uploads the current verified file for a free 0.020224; Phase 1 closes the residual frontier and cascades; Phase 2 builds the 45-degree family at 0.02-class and then 0.1-class depth in the mid-band; Phase 3 certifies and consolidates."));

body.push(h1("2. Where We Stand: What We Have Done"));
body.push(h2("2.1 The submission and its verification discipline"));
body.push(p("The competition asks for one packing of n equal unit squares into the smallest possible square container, for every n from 1 to 1000, and scores the sum of L/sqrt(n) minus 1 over all puzzles. Every state in the submission was produced by a constructive pipeline (record SVGs parsed exactly, Göbel strips, chain constructions, removal closures) and passes packlib verification: SAT separation on the four edge-normal axes with worst penetration below 1e-9 and strict container containment. Nothing enters the table by the word of a search engine; the verifier is the only authority. The current file covers 1000 of 1000 puzzles, improves 407 over the grid baseline, and scores 23.173640 locally against the grid ceiling of 28.937670."));
body.push(p("Against the published survey catalogue the submission has zero holes: for every n up to 1000 the survey-known value is at or above our table value. This was re-checked programmatically this run, not assumed. The consequence is double-edged: we are at the published state of the art everywhere, and any further find anywhere is a genuine advance over the literature, not a catch-up."));
body.push(tableTitle("Table 1: Current position (all values computed this run)"));
body.push(makeTable(
  ["Measure", "Value"],
  [
    ["Platform score / rank", "23.193864 / 1184"],
    ["Leading score", "22.0544214515"],
    ["Gap to leader", "1.139443"],
    ["Local verified score (current submission.csv)", "23.173640"],
    ["Platform minus local (re-upload gain)", "0.020224"],
    ["Grid ceiling / improvement", "28.937670 / 5.764030"],
    ["Puzzles beating grid", "407 of 1000"],
    ["Open (grid-tied) puzzles", "593 = 31 SQ + 60 NAG + 69 LOW + 433 MID"],
  ],
  [46, 54]));
body.push(p("Table 1 states the reconciliation item plainly. The platform holds a file 0.020224 worse than the current verified submission, so re-uploading the 24.8 MB submission.csv is an immediate, risk-free gain. No search run can buy that much for less work.", { after: 200 }));

body.push(h2("2.2 The residue census of the 593 grid-tied puzzles"));
body.push(p("With n written as k squared plus residue r, the audit this run assigns every grid-tied puzzle to an exact class. The 31 perfect squares (r = 0) are optimal by area. The 60 Nagamochi-class puzzles (r = 2k minus 1 and 2k) are proven optimal, so attacking them is futile by theorem. The 69 low-residue puzzles occupy r from k plus 1 to 18: this refutes the earlier belief that the cascade had solved everything up to r = 18, because the constructive cascade reach is exactly r up to k. The 433 mid-band puzzles occupy r from 19 to 2k minus 2 and concentrate in the largest blocks, from n = 140 up to n = 1000."));
body.push(...figure("/home/z/my-project/download/fig/f6_residue.png",
  "Figure 1: The 593 grid-tied puzzles by block k and residue class (audited, not assumed).", 540));
body.push(p("Two structural facts follow from the census, and both matter for planning. First, the low-residue band is not empty and not provably closed: its 69 members are open problems, but the survey catalogue already matches them, so any find there beats the published literature. Second, all of the room lives in the mid-band: 433 puzzles whose distance from the grid is at most 0.65 in container units, most of them in blocks k at or above 26 where a 0.1-class construction is worth more than 0.003 per puzzle.", { after: 200 }));

body.push(h1("3. What We Lack: The Honest Deficit Ledger"));
body.push(h2("3.1 The motif barrier, now explained by a verified theorem"));
body.push(p("Five engine families have now failed on the open band in the same way: pressure settling, simulated annealing with rotation moves, the delta-sigma controller with Sturmian classification, and last run the four compiled cent isomorphisms (flywheel, optical PLL, piezo, Griffith), 236 of 240 planned runs, zero finds. Every one of them is a local dynamics: it moves squares by rules derived from the current geometry. The GLM repository supplied the explanation this run, and it is a verified theorem, not a conjecture. LorentzianLift.lean proves that a tie is a mirror, that the reflection in that mirror fixes the tied point and swaps the tied candidates, and that therefore no rule invariant under reflections can break a tie. Every function of the local geometry is such a rule. A jammed wall is a multi-way tie, so every local engine is provably blind exactly where it jams."));
body.push(p("The same file prescribes the cure, and the study verdict quantifies it: ties are broken by information from outside the geometry. A second reading, a context, breaks a tie exactly when it is not itself equidistant, and summing Lorentzian scores over further readings resolved ties with zero wrong answers in the GLM measurements. This is the ingredient none of our engines had: global, discrete assignment decisions with context, not local continuous dynamics."));
body.push(h2("3.2 Two substrate defects found and fixed this run"));
body.push(p("Honesty requires correcting the record of the previous run. The shared vectorized substrate sat_margins, used by all four Run 6 engines, had its orientation matrices transposed relative to the documented index convention since it was written. For pairs of squares at equal angles the error was invisible, which is why earlier campaigns on near-axis configurations looked sane; for mixed-angle pairs, exactly the situations a tilted motif creates, the substrate was blind. The authority verifier packlib saw the overlaps the engines could not, so Run 6 outcomes stand as measured, but the claim that the engines had optimized the true penalty and still jammed is retracted: they descended a corrupted objective. The defect was fixed this run and the substrate now agrees with packlib on every pair, including the hand-checked worst cases."));
body.push(p("A second defect was found in the new lift engine itself: the bisector-reflection move mutated the caller state in place while the composed engine assumed call-by-value, so reported objectives did not match the returned states. This was found by instrumenting the engine chain stage by stage and was fixed by making the move pure. Both fixes are permanent assets of the pipeline, independent of any single campaign."));
body.push(h2("3.3 The quantified value ladder"));
body.push(p("The planning arithmetic was computed this run, not estimated. Moving all 593 open puzzles from grid to grid minus 0.002 is worth 0.053314 in total. At grid minus 0.02 it is worth 0.533142 and the score becomes 22.640498, still above the leader. The mid-band alone at grid minus 0.1 is worth 1.848594 and the score becomes 21.325046, past the leading score on its own. Matching the leader by a uniform push needs grid minus 0.0616 on the mid-band alone; the low-residue route would need grid minus 0.1394, which is beyond the survey-known values for most of that band and is treated as closed."));
body.push(tableTitle("Table 2: Score scenarios for the open band (computed from the audit)"));
body.push(makeTable(
  ["Push depth", "LOW delta", "MID delta", "All delta", "Score after", "Beats leader 22.0544"],
  [
    ["grid - 0.002", "-0.016342", "-0.036972", "-0.053314", "23.120326", "No"],
    ["grid - 0.02", "-0.163423", "-0.369719", "-0.533142", "22.640498", "No"],
    ["grid - 0.1", "-0.817115", "-1.848594", "-2.665710", "20.507930", "Yes"],
    ["MID alone at 0.1", "-", "-1.848594", "-", "21.325046", "Yes"],
  ],
  [17, 15, 15, 15, 19, 19]));
body.push(p("The lesson is uncomfortable but clarifying. Epsilon-chasing at 0.002 is close to worthless, 0.02-class work is worth half a point at best, and the leader is playing 0.1-class constructions. The mid-band is the only real estate with enough value, and the project directive stands: the 45-degree family is the motif line, no angle search.", { after: 200 }));

body.push(h1("4. The Lorentzian Lift Program"));
body.push(h2("4.1 The mechanism, as verified in Lean"));
body.push(p("The lift maps a planar configuration point x to the light cone of a space with one extra time-like dimension, L(x) = (x, (1 - |x| squared)/2, (1 + |x| squared)/2). Two properties do the work. First, the lift linearizes squared distance: the inner product of a lifted point with the root of a candidate site equals 1 minus half the squared distance, so nearest-site decisions become linear scores. Second, ties are mirrors, and reflections cannot break them; only context can. The escalation ladder of DeepHoleEscalation.lean adds the third piece: escalate the reading along a declared ladder until the separation ratio drops below one, then the nearest-site rule is provably correct."));
body.push(h2("4.2 Prototype results and the current frontier"));
body.push(p("The prototype compiled the lift into packing moves: linear site scoring over a declared site lattice, certified ties with context lookahead that tries both branches under a brief global relaxation, bisector-reflection long jumps that implement the mirror swap, and a terminal pure-relaxation polish. On the sanity container, 13 squares at side 4.2, it reaches an exact zero-objective verified find, so the engine is functional. On the open targets at grid minus 0.002 the residuals fall to between 1.5e-4 and 7.7e-4 penetration, where the previous engines froze at 0.06: a factor of about one hundred. The polish stage still improves the roomy mid-band targets by roughly a quarter, but does not close to feasible."));
body.push(p("What is missing is therefore precise and small: an exact closure of 1e-4-class residuals, deeper joint context over the certified ties, and site lattices that encode real 45-degree motifs rather than the union of a grid and a diamond lattice. None of these is a new search paradigm; they are completions of the one that finally moves."));
body.push(h2("4.3 Relation to the 45-degree directive"));
body.push(p("The project directive fixes the motif line: 45 degrees is the angle, and no angle search is to be spent. The lift engine already respects this in its site lattice, and Phase 2 extends it to depth: 45-degree strip templates and 45-degree lattice packings for the mid-band, parameterized analytically like the Göbel family, refined by the lift assignment with context, and verified by packlib as always. The published records at other angles are noted once, honestly: this plan does not chase them, per directive.", { after: 200 }));

body.push(h1("5. The Road Ahead: Phased Plan"));
body.push(h2("5.1 Phase 0 - Reconcile the platform (immediate)"));
body.push(p("Re-upload the current verified submission.csv. The platform file is 0.020224 worse than the local verified state, so this phase is pure bookkeeping with zero search cost. Success criterion: the platform reports 23.173640 or better. If the platform still disagrees, the divergence becomes a standing investigation item with the scoring formula, since the local scorer recomputes every L from the states with packlib."));
body.push(h2("5.2 Phase 1 - Close the residual frontier"));
body.push(p("Attack the 20 probe targets of this run at grid minus 0.002 with the completed lift engine: exact rational polishing of the 1e-4 residuals, joint context over certified ties, and deeper escalation rounds. Every find is packlib-verified, applied through the cascade closure, and scored. The expected yield is honest and modest: 0.01 to 0.053 depending on how many of the 593 convert, and each low-residue base unlocked propagates downstream by the constructively verified leverage rule, m squares at container L yielding m plus 2 floor L plus 1 squares at L plus 1."));
body.push(h2("5.3 Phase 2 - The mid-band prize"));
body.push(p("This is the main line. Build 45-degree family templates for the mid-band at two depths. First 0.02-class across the 433, worth 0.369719, taking the score to about 22.80. Then 0.1-class, worth 1.848594 on its own, past the current leader. The method is the one this run validated in miniature: analytic 45-degree motifs parameterized by block k and residue r, lift assignment with context tie-breaking, terminal exact polish, packlib verification. The mid-band census gives the target list per block, largest blocks first, because value per puzzle grows with k."));
body.push(h2("5.4 Phase 3 - Certification and consolidation"));
body.push(p("Every accepted state is re-verified, the survey cross-check is re-run to confirm no regression, and the residue audit is regenerated so the next planning run starts from audited numbers rather than memory. The Galois certificates and the exact-arithmetic chain are kept in step with the table so the repository remains a single reproducible artifact."));
body.push(h2("5.5 Milestones and success criteria"));
body.push(tableTitle("Table 3: Milestones for the next runs"));
body.push(makeTable(
  ["Phase", "Scope", "Success criterion", "Expected score effect"],
  [
    ["0. Re-upload", "submission.csv", "platform 23.173640 or better", "+0.020224"],
    ["1. Frontier", "20 targets at grid-0.002", "packlib-verified finds, cascade applied", "+0.01 to +0.053"],
    ["2a. Mid 0.02", "433 MID, 45-degree templates", "verified, survey cross-check clean", "to about 22.80"],
    ["2b. Mid 0.1", "433 MID, deeper 45-degree", "verified, beats leader on paper", "to about 21.33"],
    ["3. Consolidate", "full table + audit", "zero regressions, audit regenerated", "protects gains"],
  ],
  [16, 27, 32, 25]));
body.push(p("Each phase gates the next: Phase 1 must produce at least one verified find at grid minus 0.002 before Phase 2 template work is trusted, and Phase 2a must hold at zero regressions before 2b deepens. The plan is falsifiable at every gate, which is the point.", { after: 200 }));

body.push(h1("6. Risks and Honest Counter-Evidence"));
body.push(p("The strongest risk is that the residual closure fails the way five engine families failed before. The counter-evidence is part of the record now: the lift engine is the first to move the open targets at all, the residuals it leaves are two orders of magnitude smaller, and the missing pieces are completions, not a new paradigm. The Lean theorem that killed the local engines also protects this plan from repeating the mistake, because the lift program is exactly the prescribed alternative: discrete assignment with context."));
body.push(p("The second risk is arithmetic: 0.1-class constructions in the mid-band may simply not exist for some blocks, since the mid-band is open in the literature too. The scenario table already prices partial success: even a third of the mid-band at 0.1-class is worth about 0.6. The third risk is directive scope: the 45-degree-only line forgoes the record angles of the published catalogue; the plan accepts this per directive and notes it once. The fourth risk is platform drift, which Phase 0 resolves or escalates. Financial and schedule risk is minimal: the pipeline is scripted, deterministic by seed, and every run this session reproduced from its saved scripts.", { after: 200 }));

body.push(h1("7. Reproducibility"));
body.push(p("Every number in this plan was computed this run from the saved artifacts: the residue census from residue_audit.json, the scenario table from run7_gain_tables.json, the engine frontier from lorentz_results.json, and the substrate fix verified by debug_lorentz.py against packlib. The scripts are residue_audit.py, cent_engines.py with the corrected substrate, lorentz_lift.py, gain_tables.py, fig6_residue.py, and the two diagnostics. The generator of this document is gen_run7_plan.js, and the post-processing chain is the docx skill pipeline. A fresh sandbox reproduces the tables from these files without any manual step."));

body.push(h1("8. Execution Addendum: the push, measured"));
body.push(h2("8.1 Phase 1 outcome: the closure law"));
body.push(p("The push executed Phase 1 as planned: the lift engine plus an exact linear-programming closure (scipy HiGHS) over the near-states, with binding-axis repair and angle-flip ladders. The outcome is a computed negative with two measured laws. First, on every probe target without exception, the min-violation LP returned exactly s* = (k - L)/(k - 1): the engine always lands a rigid grid, the binding system demands every gap at least 1, and the shortfall (k - L) is distributed evenly over the k - 1 gaps. The LP closure is a finisher, not a finder: it closes exactly and only when the structure is already right. Second, a mixed-angle contact (a 45-degree square against an axis-aligned one) costs 1 + sqrt(2)/2 = 1.2071 on every SAT axis, twenty percent more than a same-angle contact at 1.0. Compression therefore cannot come from interlocking mixed angles; it can only come from same-angle 45-degree strips, the Göbel mechanism. Repair search performed zero flips in all runs: every alternative binding was strictly worse. Angle flips did not help on the small band."));
body.push(h2("8.2 Phase 2a and 2b outcomes"));
body.push(p("The sweep then covered the low-residue band completely: 69 of 69 puzzles at both depths, two seeds each, zero finds. For the mid-band the sweep ran largest-first and covered the top of the band (n = 1000 down through the largest blocks) within the session budget; the law held on every attempt, including n = 1000 and n = 999. Phase 2b ran eight representative mid-band targets across k = 17 to 30 at depths 0.1 and 0.2: the engine landed rigid grids everywhere, with s* equal to the law exactly, one case jammed worse than a rigid grid, and no finds. The honest verdict of the push: search-based closure cannot produce 0.1-class packings in the open band; the compression ingredient must be constructed analytically, not found by dynamics."));
body.push(h2("8.3 The area recalibration"));
body.push(p("Executing the plan surfaced a correction to its own value ladder. Table 2 assumed L = k - 0.1 for all 433 mid-band puzzles, but the container must satisfy the area bound L at least sqrt(n), and for the 34 mid-band puzzles closest to a perfect square the container k - 0.1 has area below n: they can never reach grid minus 0.1 at any level of skill, their best conceivable value is sqrt(n), and their total headroom is at most 0.056 below the grid. Table 4 gives the recalibrated ceilings; the 0.1-class ceiling moves from the naive 20.508 to the honest 20.541, still past the leader. The low-residue band has no area cap at 0.1: its obstruction is purely constructive."));
body.push(tableTitle("Table 4: Area-recalibrated scenario ceilings (open band at max(k - eps, sqrt(n)))"));
body.push(makeTable(
  ["Depth class", "LOW contribution", "MID contribution", "Score ceiling", "Beats leader 22.0544"],
  [
    ["grid - 0.002", "+3.083492", "+5.795667", "23.120326", "No"],
    ["grid - 0.02", "+2.936411", "+5.462920", "22.640498", "No"],
    ["grid - 0.1", "+2.282719", "+4.017193", "20.541079", "Yes"],
  ],
  [18, 21, 21, 19, 21]));
body.push(p("Contributions are per-class sums of L/sqrt(n) - 1, positive because open puzzles sit above their area bounds; the ceilings replace the corresponding open-band part of the current score. All values are computed by area_recal.py from the audit and the live table and saved to run8_area_recal.json.", { after: 200 }));
body.push(h2("8.4 The leader implication and the re-scoped Phase 2"));
body.push(p("The recalibration yields the sharpest planning fact of the session. Solving for the uniform depth that matches the leader exactly, area-respecting, gives d* = 0.041986: the leading score is precisely equivalent to every open puzzle sitting at grid minus 0.042. Catching the leader therefore needs a uniform 0.045-class construction over the open band; beating it soundly needs about 0.06. The absolute area floor for the whole board is 14.241167, so the room exists, but it is reachable only through constructions near the area bound, which are the hardest open problems in the field. Phase 2 is re-scoped accordingly: away from search and toward analytic construction families. The Göbel mechanism generalizes to the mid-band (same-angle 45-degree diamond cores plus axis staircases, parameterized by block k and residue, swept like the (a, b) family in gobel_squares.py), each candidate verified exactly by packlib, with the LP closure retained as the finisher it has proven to be."));
body.push(h2("8.5 Session ledger"));
body.push(p("No finds were applied in this session: the submission is unchanged and the local score stands at 23.173640. The measured assets are durable: the corrected substrate, the LP closure ladder, the closure law, the mixed-contact cost, the area recalibration, and the leader threshold. The immediate free action remains Phase 0: re-upload the current verified submission.csv, worth 0.020224 against the file the platform holds. The next run should execute the re-scoped Phase 2: mid-band construction families at 0.05-class and deeper, largest blocks first, with the honest gates of this plan.", { after: 200 }));

body.push(h1("9. Run 9 Addendum: the construction program, executed"));
body.push(h2("9.1 The generalized family and its exact validity envelope"));
body.push(p("The re-scoped Phase 2 was executed as an analytic construction sweep, not a search. The instrument is the full four-parameter Göbel central-square family G(a1, a2, b, c): a b-by-c diamond of 45-degree squares centered in the container, corner staircases of depth a1 on the x+y pair of corners and depth a2 on the x-y pair, container s = max(a1 + 1 + b*sqrt(2)/2, a2 + 1 + c*sqrt(2)/2, sqrt(2)*(b+c)/2), with the adjacency bound a1 + a2 at most s. The shipped enumeration had covered only the square subfamily a1 = a2 and b = c; the general family had never been swept. Every candidate that would beat the current table was generated, opened to a 2e-9 contact gap by packlib.finalize, rounded to 12 decimals, and applied only if packlib verified it. Of 326 pre-filtered candidates, 68 were applied and zero failed verification: the contact-identity derivation is exact, so the family needs no repair step."));
body.push(h2("9.2 The finds and the propagation"));
body.push(p("The 68 direct finds split into 17 mid-band and 51 low-band improvements. The 17 mid-band finds are all beyond the published catalogue: the survey holds grid for every one of the 433 mid-band puzzles, so each find is a new state of the art, including four of the ten strategic roomy targets (n = 695, 803, 862, 922) at depths 0.05 to 0.10. The chains then propagated the bases: cascade3 applied 81 chain improvements with zero verification failures, and the removal closure added 44 more in its first round, reaching a fixpoint at a second pass. The rebuilt submission round-trips clean: 500500 rows, zero issues, score 22.897558, 445 puzzles beating grid, survey cross-check still at zero holes, and the residue audit was regenerated from the new table."));
body.push(tableTitle("Table 5: Run 9 measured outcomes"));
body.push(makeTable(
  ["Quantity", "Before run 9", "After run 9", "Source"],
  [
    ["Score (local, verified)", "23.173640", "22.897558", "final_assembly + score_submission"],
    ["Gap to leader 22.0544", "1.119219", "0.843137", "computed"],
    ["Puzzles beating grid", "407", "445", "residue audit"],
    ["MID band below grid", "8", "46", "run9_outcomes.json"],
    ["Leader uniform depth d*", "0.041986", "0.026677", "run9_gain_tables.json"],
    ["MID 0.1-class ceiling", "20.541", "20.405", "run9_gain_tables.json"],
  ],
  [26, 24, 24, 26]));
body.push(p("The leader threshold moved the most: matching the leader now needs only a uniform 0.027-class construction over the open band, down from 0.042, and this run already delivered 0.05-class on 46 of 441 mid-band puzzles. The platform gain including the Phase 0 headroom is 0.296306: re-uploading the current submission.csv is now worth 0.020224 plus the run 9 gain of 0.276082.", { after: 120 }));
body.push(h2("9.3 Wave 2, measured and closed as a negative"));
body.push(p("Two second-wave generalizations were evaluated and closed honestly. Mixed-wedge serration rows (45-degree rows replacing the innermost staircase rows) are a wash: the row's areal density of about 0.707 in the hypotenuse band exactly cancels the lost staircase depth, per-wedge net about minus one square at a1 = 15. Asymmetric pair splits beyond the balanced optimum are split-invariant at maximum count: verified across the full split range at s = 31, every split lands at n of about 930, because the iso-n curve is a consequence of the symmetric exchange between the contact and bbox constraints. Side-band squares in unbalanced regimes are degenerate at the balanced optimum, where all three container constraints are tight within slack 1. The family's honest frontier is therefore the balanced four-parameter envelope itself, which the sweep covered completely for n up to 1000."));
body.push(h2("9.4 What remains open"));
body.push(p("After propagation the open band is 69 low-band and 395 mid-band puzzles, of which the mid-band holds the prize. The refreshed value ladder prices the next step: uniform 0.02-class over the open band reaches 22.392, and 0.1-class reaches 20.405, both computed area-respecting in run9_gain_tables.json. The constructions this run found are all at the 0.03 to 0.10 depth class; the 34 area-capped mid-band puzzles can never exceed their sqrt(n) bound, so the ceiling math already accounts for them. The next program line is a constructive 0.05-class family over the remaining mid-band: the same swept-envelope discipline, parameterized by block k and residue r, largest blocks first, with the LP closure retained as the finisher and packlib as the only acceptance gate.", { after: 200 }));

/* ---------------- assemble ---------------------------------------------- */
const pgSize = { width: 11906, height: 16838 };
const pgMargin = { top: 1440, bottom: 1440, left: 1701, right: 1417 };
const pageFooter = () => new Footer({
  children: [new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "808080", font: FONT })],
  })],
});
const pageHeader = new Header({
  children: [new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "Run 7 Strategic Plan - GLM Packing Project", size: 18, color: "808080", font: FONT })],
  })],
});

const doc = new Document({
  styles: {
    default: {
      document: {
        run: { font: FONT, size: 24, color: BODY },
        paragraph: { spacing: { line: 312 } },
      },
      heading1: { run: { font: HFONT, size: 32, bold: true, color: HEADING_COLOR }, paragraph: { spacing: { before: 360, after: 160, line: 312 } } },
      heading2: { run: { font: HFONT, size: 28, bold: true, color: HEADING_COLOR }, paragraph: { spacing: { before: 240, after: 120, line: 312 } } },
    },
  },
  sections: [
    { /* Section 1: cover */
      properties: { page: { size: pgSize, margin: { top: 0, bottom: 0, left: 0, right: 0 } } },
      children: buildCoverR4({
        title: "Run 7 Strategic Plan",
        subtitle: "Squares in Squares: closing the gap to the leader",
        englishLabel: "SQUARES IN SQUARES",
        metaLines: [
          "Competition: Squares in Squares, n = 1 to 1000",
          "Position: 1184 of the leaderboard, score 23.193864",
          "Leader: 22.0544214515 - gap 1.139443",
          "Program: Lorentzian lift and the 45-degree motif line",
          "Date: 4 November 2026",
        ],
        footerLeft: "GLM Packing Project",
        footerRight: "Run 7 - 2026-11-04",
        palette: PAL,
      }),
    },
    { /* Section 2: front matter (TOC) - Roman numerals */
      properties: {
        type: SectionType.NEXT_PAGE,
        page: { size: pgSize, margin: pgMargin, pageNumbers: { start: 1, formatType: NumberFormat.UPPER_ROMAN } },
      },
      footers: { default: pageFooter() },
      children: [
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { before: 240, after: 200 },
          children: [new TextRun({ text: "Table of Contents", bold: true, size: 32, color: HEADING_COLOR, font: HFONT })],
        }),
        new TableOfContents("Table of Contents", { hyperlink: true, headingStyleRange: "1-2" }),
        new Paragraph({
          spacing: { before: 100 },
          children: [new TextRun({
            text: "Note: this Table of Contents is generated via field codes. To refresh page numbers after editing, right-click it and select Update Field.",
            italics: true, size: 16, color: "888888", font: FONT,
          })],
        }),
      ],
    },
    { /* Section 3: body - Arabic from 1 */
      properties: {
        type: SectionType.NEXT_PAGE,
        page: { size: pgSize, margin: pgMargin, pageNumbers: { start: 1, formatType: NumberFormat.DECIMAL } },
      },
      headers: { default: pageHeader },
      footers: { default: pageFooter() },
      children: body,
    },
  ],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync("/home/z/my-project/download/Run7_Strategic_Plan.docx", buf);
  console.log("written Run7_Strategic_Plan.docx", buf.length, "bytes");
});
