#!/usr/bin/env node
/* gen_report.js — Leech 格与装箱网格研究报告 (docx)
 * Cover: R1 recipe + DS-1 palette (design-system.md)
 * 3 sections: cover (no page#) / front matter (Roman) / body (Arabic start=1)
 * Profile A formal: SimHei headings, SimSun body, pure black, 3-line tables
 * 5 embedded figures + TOC field + refresh hint + footer pgNum patch
 */
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  ImageRun, PageBreak, Header, Footer, PageNumber, NumberFormat,
  AlignmentType, HeadingLevel, WidthType, BorderStyle, ShadingType,
  SectionType, TableOfContents, TableLayoutType,
} = require("docx");
const fs = require("fs");

const OUT = "/home/z/my-project/download/Leech格与装箱网格研究报告.docx";
const FIG = "/home/z/my-project/download/fig/";

// ---------------- palette (DS-1 Deep Sea) ----------------
const P = {
  bg: "0B1C2C", titleColor: "FFFFFF", subtitleColor: "B0B8C0",
  metaColor: "90989F", footerColor: "687078", accent: "529286",
  table: { headerBg: "529286", headerText: "FFFFFF", accentLine: "529286",
           innerLine: "BECFCC", surface: "E8ECEB" },
};
const NB = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: NB, bottom: NB, left: NB, right: NB };
const allNoBorders = { ...noBorders, insideHorizontal: NB, insideVertical: NB };

// ---------------- cover helpers (from design-system.md) ----
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
    if (breakAt === -1) {
      breakAt = charsPerLine;
      const prevChar = remaining[breakAt - 1], nextChar = remaining[breakAt];
      if (prevChar && nextChar && !breakAfter.has(prevChar) && !breakAfter.has(nextChar)
          && /[\u4e00-\u9fff]/.test(prevChar) && /[\u4e00-\u9fff]/.test(nextChar)) breakAt -= 1;
    }
    lines.push(remaining.slice(0, breakAt).trim());
    remaining = remaining.slice(breakAt).trim();
  }
  if (remaining) lines.push(remaining);
  if (lines.length > 1 && lines[lines.length - 1].length <= 2) {
    const last = lines.pop();
    lines[lines.length - 1] += last;
  }
  return lines;
}

function calcTitleLayout(title, maxWidthTwips, preferredPt = 40, minPt = 24) {
  const charsPerLine = (pt) => Math.floor(maxWidthTwips / (pt * 20));
  let titlePt = preferredPt, lines;
  while (titlePt >= minPt) {
    const cpl = charsPerLine(titlePt);
    if (cpl < 2) { titlePt -= 2; continue; }
    lines = splitTitleLines(title, cpl);
    if (lines.length <= 3) break;
    titlePt -= 2;
  }
  if (!lines || lines.length > 3) {
    lines = splitTitleLines(title, charsPerLine(minPt));
    titlePt = minPt;
  }
  return { titlePt, titleLines: lines };
}

function calcCoverSpacing(params) {
  const { titleLineCount = 1, titlePt = 36, hasSubtitle = false,
          hasEnglishLabel = false, metaLineCount = 0,
          fixedHeight = 800, pageHeight = 16838,
          marginTop = 0, marginBottom = 0 } = params;
  const SAFETY = 1200;
  const usable = pageHeight - marginTop - marginBottom - SAFETY;
  const titleHeight = titleLineCount * (titlePt * 23 + 200);
  const subtitleHeight = hasSubtitle ? (12 * 23 + 600) : 0;
  const engHeight = hasEnglishLabel ? (9 * 23 + 600) : 0;
  const metaHeight = metaLineCount * (10 * 23 + 100);
  const implicit = 3 * 300;
  const content = titleHeight + subtitleHeight + engHeight + metaHeight + fixedHeight + implicit;
  const remaining = Math.max(usable - content, 400);
  const FOOTER_MIN = 800;
  const rawTop = Math.floor(remaining * 0.45);
  const rawBottom = Math.floor(remaining * 0.45);
  const bottomSpacing = Math.max(rawBottom, FOOTER_MIN);
  const topSpacing = Math.max(rawTop - Math.max(0, FOOTER_MIN - rawBottom), 400);
  const midSpacing = Math.max(remaining - topSpacing - bottomSpacing, 0);
  return { topSpacing, midSpacing, bottomSpacing };
}

function buildCoverR1(config) {
  const padL = 1200, padR = 800;
  const availableWidth = 11906 - padL - padR - 300;
  const { titlePt, titleLines } = calcTitleLayout(config.title, availableWidth, 40, 24);
  const titleSize = titlePt * 2;
  const spacing = calcCoverSpacing({
    titleLineCount: titleLines.length, titlePt,
    hasSubtitle: !!config.subtitle, hasEnglishLabel: !!config.englishLabel,
    metaLineCount: (config.metaLines || []).length, fixedHeight: 400,
  });
  const accentLeft = { style: BorderStyle.SINGLE, size: 8, color: P.accent, space: 12 };
  const children = [];
  children.push(new Paragraph({ spacing: { before: spacing.topSpacing } }));
  if (config.englishLabel) {
    children.push(new Paragraph({
      indent: { left: padL, right: padR }, spacing: { after: 500 },
      border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: P.accent, space: 8 } },
      children: [new TextRun({ text: config.englishLabel.split("").join("  "),
        size: 18, color: P.accent, font: { ascii: "Calibri", eastAsia: "SimHei" },
        characterSpacing: 40 })],
    }));
  }
  for (let i = 0; i < titleLines.length; i++) {
    children.push(new Paragraph({
      indent: { left: padL },
      spacing: { after: i < titleLines.length - 1 ? 100 : 300,
                 line: Math.ceil(titlePt * 23), lineRule: "atLeast" },
      children: [new TextRun({ text: titleLines[i], size: titleSize, bold: true,
        color: P.titleColor, font: { eastAsia: "SimHei", ascii: "Arial" } })],
    }));
  }
  if (config.subtitle) {
    children.push(new Paragraph({
      indent: { left: padL }, spacing: { after: 800 },
      children: [new TextRun({ text: config.subtitle, size: 24, color: P.subtitleColor,
        font: { eastAsia: "Microsoft YaHei", ascii: "Arial" } })],
    }));
  }
  for (const line of (config.metaLines || [])) {
    children.push(new Paragraph({
      indent: { left: padL + 200 }, spacing: { after: 80 },
      border: { left: accentLeft },
      children: [new TextRun({ text: line, size: 24, color: P.metaColor,
        font: { eastAsia: "Microsoft YaHei", ascii: "Arial" } })],
    }));
  }
  children.push(new Paragraph({ spacing: { before: spacing.bottomSpacing } }));
  children.push(new Paragraph({
    indent: { left: padL, right: padR },
    border: { top: { style: BorderStyle.SINGLE, size: 2, color: P.accent, space: 8 } },
    spacing: { before: 200 },
    children: [
      new TextRun({ text: config.footerLeft || "", size: 16, color: P.footerColor, font: { ascii: "Arial" } }),
      new TextRun({ text: "                                        " }),
      new TextRun({ text: config.footerRight || "", size: 16, color: P.footerColor, font: { ascii: "Arial" } }),
    ],
  }));
  return [new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    layout: TableLayoutType.FIXED,
    borders: allNoBorders,
    rows: [new TableRow({
      height: { value: 16838, rule: "exact" },
      children: [new TableCell({
        shading: { type: ShadingType.CLEAR, fill: P.bg }, borders: noBorders,
        children,
      })],
    })],
  })];
}

// ---------------- body helpers ----------------
const BLACK = "000000";
function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1, keepNext: true,
    spacing: { before: 360, after: 160, line: 312 },
    children: [new TextRun({ text, bold: true, size: 32, color: BLACK,
      font: { ascii: "Times New Roman", eastAsia: "SimHei" } })],
  });
}
function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2, keepNext: true,
    spacing: { before: 240, after: 120, line: 312 },
    children: [new TextRun({ text, bold: true, size: 28, color: BLACK,
      font: { ascii: "Times New Roman", eastAsia: "SimHei" } })],
  });
}
function para(text, opts = {}) {
  const runs = Array.isArray(text) ? text : [new TextRun({ text, size: 24, color: BLACK,
    font: { ascii: "Times New Roman", eastAsia: "SimSun" } })];
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    indent: { firstLine: opts.noIndent ? 0 : 480 },
    spacing: { line: 312, after: opts.after ?? 80 },
    keepNext: opts.keepNext || false,
    children: runs,
  });
}
function run(text, o = {}) {
  return new TextRun({ text, size: o.size || 24, bold: o.bold || false,
    italics: o.italics || false, color: o.color || BLACK,
    font: { ascii: o.ascii || "Times New Roman", eastAsia: o.east || "SimSun" } });
}
function caption(text) {
  return new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { before: 60, after: 200, line: 312 },
    children: [new TextRun({ text, italics: true, size: 21, color: "404040",
      font: { ascii: "Times New Roman", eastAsia: "SimSun" } })],
  });
}
function pngDims(buf) {
  // PNG IHDR: width at bytes 16-19, height 20-23 (big-endian). Zero deps.
  return { width: buf.readUInt32BE(16), height: buf.readUInt32BE(20) };
}
function figure(path, width, capText) {
  const buf = fs.readFileSync(path);
  const dims = pngDims(buf);
  const h = Math.round(width * dims.height / dims.width);
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 160 },
      children: [new ImageRun({ data: buf, transformation: { width, height: h }, type: "png" })],
    }),
    caption(capText),
  ];
}
// 3-line table (Profile A)
function threeLine(header, rows, widths) {
  const mk = (text, bold, isHeader) => new TableCell({
    children: [new Paragraph({
      spacing: { line: 312 },
      children: [new TextRun({ text: String(text), bold, size: 21, color: BLACK,
        font: { ascii: "Times New Roman", eastAsia: bold ? "SimHei" : "SimSun" } })],
    })],
    borders: isHeader ? { ...noBorders, bottom: { style: BorderStyle.SINGLE, size: 2, color: BLACK } }
      : noBorders,
    margins: { top: 60, bottom: 60, left: 120, right: 120 },
    width: undefined,
  });
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: {
      top: { style: BorderStyle.SINGLE, size: 4, color: BLACK },
      bottom: { style: BorderStyle.SINGLE, size: 4, color: BLACK },
      left: NB, right: NB, insideHorizontal: NB, insideVertical: NB,
    },
    rows: [
      new TableRow({ tableHeader: true, cantSplit: true,
        children: header.map(t => mk(t, true, true)) }),
      ...rows.map(r => new TableRow({ cantSplit: true, children: r.map(t => mk(t, false, false)) })),
    ],
  });
}
function tableTitle(text) {
  return new Paragraph({
    keepNext: true, spacing: { before: 200, after: 80 },
    children: [new TextRun({ text, bold: true, size: 21, color: BLACK,
      font: { ascii: "Times New Roman", eastAsia: "SimHei" } })],
  });
}

// ---------------- data (all verified numbers) ----------------
const LM = JSON.parse(fs.readFileSync("/home/z/my-project/download/leech_map.json", "utf8"));
const CORE = JSON.parse(fs.readFileSync("/home/z/my-project/download/leech_core.json", "utf8"));
const OCT = JSON.parse(fs.readFileSync("/home/z/my-project/download/octad_moves.json", "utf8"));
const M = LM.metrics;

// ---------------- assemble body ----------------
const body = [];

body.push(h1("一、执行摘要"));
body.push(para("本报告回答两个问题：其一，Leech 格（Leech lattice）及其载体 Golay 码这个系统是否存在可陈述的逻辑；其二，这套逻辑是否有助于求解装箱网格（在最小正方形中放入 n 个单位正方形）。全部结论以可复现的机器验证为准：Golay 码与 Leech 格的构造、不变量、层叠塔与投影定律共 28 项断言全部通过穷举验证；八元组演算层共 14 项断言全部通过验证。"));
body.push(para([
  run("对 1000 个已解网格的映射给出定量回答：87% 的容器值可精确识别数域；"),
  run("逻辑层级越高（数域次数越大），对网格解的构建力越强", { bold: true }),
  run("——层级与改进量的 Spearman 秩相关为 +0.79，与浪费率的秩相关为 +0.51。二次数域 Q(√2) 层级以 262 个网格贡献了 4.04 的总分改进（占全部 5.76 改进的 70%），是全部层级中构建力最强的一层。"),
]));

body.push(h1("二、背景与研究问题"));
body.push(h2("2.1 两个系统的原始形态"));
body.push(para("第一个系统是组合格论中的 Leech 格 Λ24：24 维欧氏空间中 kissing number（最小向量数）达到 196560 的唯一偶Unimodular 格，其载体是扩展二元 Golay 码 G24——一个 [24,12,8] 纠错码。第二个系统是装箱网格：对每个 n，求边长 L(n) 最小的正方形，使其容纳 n 个互不重叠的单位正方形（每个正方形可以任意旋转）。前一阶段工作已将 n=1..1000 全部求解并落盘（table.json），本报告在其之上建立两层结构。"));
body.push(h2("2.2 研究问题的精确表述"));
body.push(para("问题一（逻辑）：Golay/Leech 系统中哪些事实是有限、可穷举、可验证的，它们是否构成一个封闭的规则系（如同一个公理系统），而不是一堆孤立数字。问题二（帮助）：把每个已解网格按其容器值所属数域映射到层叠格塔（laminated tower）Λ1→Λ24 的对应层级后，层级是否解释解的来源、是否预测解的质量。两个问题都用同一判据回答：不接受任何未经验证的陈述。"));

body.push(h1("三、方法与数据来源"));
body.push(para("全部计算为整数精确计算（位掩码、Python 大整数），不做任何浮点近似；验证脚本与输出 JSON 随附交付。三个模块的分工如下：leech_core.py 构造 Golay 码（x^23+1 在 GF(2) 上的 QR 因子搜索）与 Leech 格（三条件成员判定），并穷举验证 196560 个最小向量；octad_moves.py 验证八元组演算（Steiner 阶梯、相交演算、距离-8 图、覆盖半径）；leech_map.py 把 1000 个已解网格按数域精确分级（沿用本仓库 level_audit.py 已审计的识别标准：容差 2e-8，分母整除 24，无平方因子 ≤23），并计算解释覆盖率、构建力与秩相关。"));
body.push(para([
  run("数域识别的金标准是 54 份伽罗瓦证书（galois_certificates.json）——证书仅在认证值与该网格容器值一致（<1e-6）时才被采用，共 9 份被值匹配采纳；"),
  run("识别不出精确形式的数据一律记为层级 0（未定），绝不强行归类", { bold: true }),
  run("。本数据中层级 0 共 130 例，在所有统计中单独列出。"),
]));

body.push(h1("四、Golay 码与 Leech 格的机器验证"));
body.push(h2("4.1 Golay 码：4096 词、759 八元组"));
body.push(para("扩展二元 Golay 码 G24 通过 x^23+1 的 QR 因子构造（程序搜索而非查表），全部 4096 个码字由 12 个移位生成元张成。机器验证确认：权重分布恰为 {0:1, 8:759, 12:2576, 16:759, 24:1}；所有权重均为 4 的倍数（双重偶），配合维度 12 = 24/2，得自对偶。759 个权重 8 的码字称为八元组（octad），是后续全部演算的对象。"));
body.push(h2("4.2 Leech 格：196560 个最小向量"));
body.push(para("Leech 格以整系数形式 L_raw = √8·Λ24 定义，成员须同时满足三个条件：24 个坐标同奇偶；坐标和 ≡ 4·a₀ (mod 8)；每个剩余类 {i: aᵢ ≡ r (mod 4)} 都是 Golay 码字。程序对全部 4096 码字逐一检验成员资格，确认最小向量恰为三族之和：1104（形如 (±4,±4,0²²)）+ 97152（八元组上 (±2⁸,0¹⁶)，负号偶数个）+ 98304（形如 (∓3,±1²³)），合计 196560，两两不重，每条范数平方（缩放后）均为 4。行列式经分层陪集计数 |L_raw/8Z²⁴| = 2^36 得 det Λ24 = 1。"));
body.push(tableTitle("表1  Leech 格核心不变量（leech_core.py，28/28 全部通过）"));
body.push(threeLine(
  ["不变量", "值", "验证方式"],
  [
    ["Golay 码字数", "4096（[24,12,8]，自对偶）", "移位生成元张成，穷举"],
    ["权重分布", "0:1, 8:759, 12:2576, 16:759, 24:1", "穷举计数"],
    ["最小向量数 kissing", "196560 = 1104+97152+98304", "三族枚举，互不相交"],
    ["行列式 det", "1（|L_raw/8Z^24| = 2^36）", "分层陪集计数"],
    ["最小范数", "4（缩放后）", "逐向量计算"],
  ]
));
body.push(para("层叠格塔的接触数（kissing number，最小向量数）在维度 1、2、3、4、8 分别为 2、6、12、24、240，均由程序穷举得出；Λ16 的 7320 为文献引用值（Conway & Sloane, SPLAG），在图中以灰色方块标注，未冒充已验证。", { after: 120 }));

body.push(h1("五、八元组演算：系统的逻辑层"));
body.push(h2("5.1 完全性：Steiner 阶梯"));
body.push(para("对每个 k=1..5，任取 k 个坐标，程序穷举确认含它的八元组个数恰为 λₖ：253、77、21、5、1。k=5 时唯一性成立——五个已定坐标完全决定八元组，一条局部信息封闭出全局对象，这正是\u201c填格规则\u201d的代数形态。"));
body.push(h2("5.2 封闭性：相交演算"));
body.push(para("任意两个八元组的交集只可能是 0、2 或 4 点，每个八元组分别有 30、448、280 个这样的伙伴（758 = 30+448+280）。三个数值构成封闭的二元演算表：以八元组为对象、以相交为运算，759 个对象在规则下封闭，没有例外情形。"));
body.push(h2("5.3 连通性与纠错：覆盖半径 4"));
body.push(para("以码字为顶点、Hamming 距离 8 为边，4096 个码字构成 759-正则图，连通且直径为 3。解码层面：权重 ≤4 的字覆盖全部 4096 个陪集代表（覆盖半径恰为 4，因权重 ≤3 只覆盖 2325 个），任意 24 位输入都在距某码字 4 次翻转之内——基底对任意输入可\u201c求解\u201d。20 个随机字的解码演示全部落在距离 2–4。"));
body.push(...figure(FIG + "f4_octads.png", 540,
  "图4  八元组演算：(a) 相交演算 0/2/4 点（每八元组 30/448/280）；(b) Steiner 阶梯 253/77/21/5/1（对数轴）"));

body.push(h1("六、投影定律：缺陷恰为八元组"));
body.push(para("把 Leech 格投影到任意 d 个坐标（d≤8）上：投影格与 2Z^d + Z(1..1)（棋盘格加一条对角线）之间的指标，经穷举验证为：d=2..7 的全部 C(24,d) 个坐标子集指标一律为 1（零缺陷）；d=8 时 735471 个子集中恰有 759 个指标为 2，且这 759 个子集恰是全部八元组。d=2、3 用 (Z/4)^d 上的 BFS 全验证，d=4..8 用限制码规模 |C_S| 的公式验证并抽 50 例暴力复核，指标一律吻合。"));
body.push(para([
  run("结论可以一句话陈述："),
  run("Leech 格的一切坐标投影都是同一个格（棋盘+对角线），唯一的缺陷轨迹恰好是八元组的集合", { bold: true }),
  run("。缺陷不是散布的，而是有精确位置的——这是第六章映射解释力的几何来源。"),
]));
body.push(...figure(FIG + "f5_projection.png", 540,
  "图5  投影定律：指标=1（蓝）覆盖一切 ≤7 维投影；指标=2（红）恰为 759 个八元组（对数轴）"));

body.push(h1("七、1000 个网格的 Leech 映射"));
body.push(h2("7.1 分级与覆盖"));
body.push(para("按容器值所属数域的次数把 1000 个网格分为四级：有理（Q，→Λ1–Λ4 窗口）、二次（Q(√m)，→Λ8 窗口）、双二次/四次（→Λ16 窗口）、八次以上（→Λ24 窗口）。870 个（87%）获得精确数域；130 个未定级（数值最优，无精确形式声称），它们在统计中单独成行，从未被并入任何层级。"));
body.push(...figure(FIG + "f2_fields.png", 520, "图2  数域分布：Q 占 596，Q(√2) 247，Q(√7) 15，未定 130（87% 精确覆盖）"));
body.push(h2("7.2 构建力：层级解释了多少分"));
body.push(para([
  run("计分语义与提交管线一致（score_submission.py：总分 = Σ L_n/√n − 1；纯网格天花板 = Σ ⌈√n⌉/√n − 1 = 28.94）。总改进 5.76 中，"),
  run("二次层级（Λ8 窗口）贡献 4.04，占 70%", { bold: true }),
  run("，全部来自 262 个网格；其中 Q(√2)（Göbel 型 45° 倾斜族）247 例、Q(√7)（目录精确族）15 例。双二次层级 12 例贡献 0.15；有理层级 596 例仅贡献 0.12（网格解几乎贴天花板）；未定级 130 例合计 1.45，是最值得继续攻坚的池子。"),
]));
body.push(tableTitle("表2  分层统计（leech_map.json，全部机器算得）"));
body.push(threeLine(
  ["层级（数域窗口）", "网格数", "改进量合计", "平均浪费率", "主要数域"],
  [
    ["0 未定（纯数值）", "130", "1.45", "0.077", "——"],
    ["1 有理 Q → Λ1–Λ4", "596", "0.12", "0.035", "Q"],
    ["2 二次 → Λ8", "262", "4.04", "0.060", "Q(√2)×247, Q(√7)×15"],
    ["3 双二次 → Λ16", "12", "0.15", "0.073", "Q(√2,√5)×9, Q(√2,√3)×2, Q(√3,√5)×1"],
  ]
));
body.push(...figure(FIG + "f1_map.png", 540,
  "图1  全景映射：每格按 (n, L/√n) 落点、按 Leech 层级着色；下界 1 为虚线"));
body.push(h2("7.3 预测力：层级与解质量"));
body.push(para("Spearman 秩相关：层级 vs 浪费率 w = L²/n − 1 为 +0.51（正：层级越高，浪费越大——高级解恰恰出现在难网格上）；层级 vs 改进量为 +0.79（强正：高级构造几乎必然带来超出网格的改进）。两个相关合起来的含义：高数域层级不是装饰，它准确标记了\u201c哪些网格被非平凡构造解出\u201d以及\u201c解在其中获得了多少增益\u201d。"));
body.push(...figure(FIG + "f3_tower.png", 540,
  "图3  (a) 层叠格塔接触数（2/6/12/24/240/7320/196560，对数轴；灰方块=引用值）；(b) 1000 个网格在塔上的落位"));

body.push(h1("八、结论与建议"));
body.push(para([
  run("对问题一（逻辑）：存在，且已验证。"),
  run("Golay/Leech 基底的逻辑由四层封闭事实组成——Steiner 完全阶梯（λ=253/77/21/5/1）、相交演算（30/448/280）、距离-8 图（759-正则、连通、直径 3）、覆盖半径 4——外加一条精确的几何缺陷定律：坐标投影零缺陷，唯一缺陷恰为 759 个八元组。", {}),
  run("这不是数字的堆砌，而是一个可运算的规则系。"),
]));
body.push(para([
  run("对问题二（帮助）：有，且可量化。"),
  run("87% 精确覆盖；层级对改进量的秩相关 +0.79；单一层级（Q(√2)，Λ8 窗口）解释 70% 的总改进。"),
  run("建议把后续攻坚集中在 130 个未定级网格上（它们合计还有 1.45 的改进池），并把识别标准沿 22.5° 嵌套四次域 Q(√(2+√2)) 扩展证书——现有证书已含该域，但尚未有网格落入该层。"),
]));
body.push(para("边界说明：本报告不声称 Leech 格与装箱问题存在同构；映射的语义是\u201c容器值的数域层级 ↔ 层叠塔层级\u201d这一经验对应，其解释力以本文的统计量为准。Λ16 的 7320 为文献引用值；130 个未定级网格是纯数值最优，不附带任何精确形式声称。", { after: 0 }));

// ---------------- TOC/front matter ----------------
const front = [
  new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { before: 480, after: 360 },
    children: [new TextRun({ text: "目  录", bold: true, size: 32,
      font: { eastAsia: "SimHei", ascii: "Times New Roman" } })],
  }),
  new TableOfContents("Table of Contents", { hyperlink: true, headingStyleRange: "1-2" }),
  new Paragraph({
    spacing: { before: 200 },
    children: [new TextRun({
      text: "注：本目录由域代码生成。编辑后如页码变化，请右键目录并选择\u201c更新域\u201d以刷新页码。",
      italics: true, size: 18, color: "888888",
      font: { ascii: "Times New Roman", eastAsia: "SimSun" } })],
  }),
  // no trailing PageBreak: body is a separate NEXT_PAGE section (a PageBreak
  // here would produce a double break -> blank page)
];

// ---------------- footers ----------------
const romanFooter = new Footer({ children: [new Paragraph({
  alignment: AlignmentType.CENTER,
  children: [new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "808080" })],
})] });
const arabicFooter = new Footer({ children: [new Paragraph({
  alignment: AlignmentType.CENTER,
  children: [new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "808080" })],
})] });
const bodyHeader = new Header({ children: [new Paragraph({
  alignment: AlignmentType.CENTER,
  children: [new TextRun({ text: "Leech 格与装箱网格研究报告", size: 18, color: "888888",
    font: { ascii: "Times New Roman", eastAsia: "SimSun" } })],
})] });

// ---------------- document ----------------
const doc = new Document({
  styles: { default: { document: {
    run: { font: { ascii: "Times New Roman", eastAsia: "SimSun" }, size: 24, color: BLACK },
    paragraph: { spacing: { line: 312 } },
  } } },
  sections: [
    { properties: { page: { size: { width: 11906, height: 16838 },
        margin: { top: 0, bottom: 0, left: 0, right: 0 } } },
      children: buildCoverR1({
        title: "Leech 格与装箱网格研究报告",
        englishLabel: "LEECH LATTICE & SQUARE PACKING",
        subtitle: "Golay 码逻辑层的机器验证与 1000 个已解网格的数域映射",
        metaLines: [
          "报告类型：数理研究报告（分析型）",
          "验证基线：28/28 + 14/14 全部通过（整数精确计算）",
          "数据来源：table.json（1000 解）· 54 份伽罗瓦证书（9 份值匹配采纳）",
          "完成日期：2026 年 11 月 3 日",
        ],
        footerLeft: "Exact verification pipeline",
        footerRight: "2026-11-03",
      }) },
    { properties: { type: SectionType.NEXT_PAGE,
        page: { size: { width: 11906, height: 16838 },
          margin: { top: 1440, bottom: 1440, left: 1701, right: 1417 },
          pageNumbers: { start: 1, formatType: NumberFormat.UPPER_ROMAN } } },
      footers: { default: romanFooter },
      children: front },
    { properties: { type: SectionType.NEXT_PAGE,
        page: { size: { width: 11906, height: 16838 },
          margin: { top: 1440, bottom: 1440, left: 1701, right: 1417 },
          pageNumbers: { start: 1, formatType: NumberFormat.DECIMAL } } },
      headers: { default: bodyHeader },
      footers: { default: arabicFooter },
      children: body },
  ],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(OUT, buf);
  console.log("wrote", OUT, buf.length, "bytes");
});
