#!/usr/bin/env python3
"""patch_footers.py -- post-process the report docx per toc.md rules:
1. Footer PAGE fields get explicit format switches (Roman front matter,
   arabic body) because WPS ignores pgNumType fmt.
2. Remove empty <w:pgNumType/> from any section.
3. Verify each section's pgNumType survives with start/fmt attributes.
"""
import re
import shutil
import sys
import zipfile

ROOT = __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__)))

SRC = ROOT + "/download/Leech格与装箱网格研究报告.docx"
TMP = SRC + ".tmp"

zin = zipfile.ZipFile(SRC)
names = zin.namelist()
doc_xml = zin.read("word/document.xml").decode("utf-8")

# ---- 1. split sections: footer rIds per section ----
# sectPr blocks appear in document order: cover (in last paragraph? no --
# docx-js puts sectPr of each section as properties; order = cover, roman, body)
sects = re.findall(r"<w:sectPr[^>]*>.*?</w:sectPr>", doc_xml, re.S)
print(f"sections found: {len(sects)}")
for i, s in enumerate(sects):
    fmt = re.search(r'<w:pgNumType[^/]*/>', s)
    ftr = re.findall(r'<w:footerReference[^>]*r:id="(rId\d+)"', s)
    print(f"  sect{i}: pgNumType={fmt.group(0) if fmt else None} footers={ftr}")

# map footer rId -> format by section order (sect0=cover: none, sect1=ROMAN, sect2=arabic)
rels = zin.read("word/_rels/document.xml.rels").decode("utf-8")
rid_to_file = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="(footer\d+\.xml)"', rels))
print("footer rels:", rid_to_file)

patch = {}
if len(sects) >= 3:
    for rid in re.findall(r'<w:footerReference[^>]*r:id="(rId\d+)"', sects[1]):
        if rid in rid_to_file:
            patch["word/" + rid_to_file[rid]] = "ROMAN"
    for rid in re.findall(r'<w:footerReference[^>]*r:id="(rId\d+)"', sects[2]):
        if rid in rid_to_file:
            patch["word/" + rid_to_file[rid]] = "arabic"
print("patch plan:", patch)

# ---- 2. remove empty pgNumType (cover) ----
n_empty = len(re.findall(r"<w:pgNumType/>", doc_xml))
doc_xml = doc_xml.replace("<w:pgNumType/>", "")
print(f"removed {n_empty} empty pgNumType")

out = {}
for n in names:
    data = zin.read(n)
    if n == "word/document.xml":
        data = doc_xml.encode("utf-8")
    elif n in patch:
        x = data.decode("utf-8")
        fmt = patch[n]
        x2, cnt = re.subn(
            r"(<w:instrText[^>]*>)\s*PAGE\s*(</w:instrText>)",
            rf"\1 PAGE \\* {fmt} \\* MERGEFORMAT \2", x)
        print(f"{n}: patched {cnt} PAGE fields -> {fmt}")
        data = x2.encode("utf-8")
    out[n] = data
zin.close()

zout = zipfile.ZipFile(TMP, "w", zipfile.ZIP_DEFLATED)
for n in names:
    zout.writestr(n, out[n])
zout.close()
shutil.move(TMP, SRC)
print("OK ->", SRC)
