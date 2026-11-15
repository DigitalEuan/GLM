#!/usr/bin/env python3
"""patch_run7_docx.py — WPS compatibility patches per docx skill toc.md:
1. Map each section's footerReference to its footer file via document.xml.rels.
2. Patch instrText PAGE: front-matter (Roman) section -> PAGE \\* ROMAN,
   body (Arabic) -> PAGE \\* arabic  (never "\\* decimal").
3. Remove empty <w:pgNumType/> from document.xml (docx-js emits these).
4. TOC integrity: drop a duplicated first entry (a paragraph inside the
   field result whose text matches the next entry but carries no page
   number/PAGEREF).
5. Compact TOC1/2/3 styles (single line spacing, small after) so a
   26-entry TOC fits one page."""
import re
import shutil
import sys
import zipfile

PATH = "/home/z/my-project/download/Run7_Strategic_Plan.docx"
TMP = PATH + ".tmp"


def fix_toc_duplicate(docxml):
    """No-op: the first TOC entry's field begin/separate runs live in the
    first placeholder paragraph; removing it breaks the field. The
    duplicated first line in the render is the placeholder artifact of
    add_toc_placeholders.py and disappears when Word updates the field."""
    return docxml, 0


def compact_toc_styles(stylesxml):
    for sid in ("TOC1", "TOC2", "TOC3"):
        m = re.search(r'(<w:style [^>]*w:styleId="' + sid + r'"[^>]*>)(.*?)(</w:style>)',
                      stylesxml, flags=re.S)
        if not m:
            continue
        body = m.group(2)
        body2 = re.sub(r"<w:spacing\b[^/]*/>", "", body)
        if "<w:pPr>" in body2:
            body2 = body2.replace(
                "<w:pPr>",
                "<w:pPr><w:spacing w:after=\"0\" w:line=\"200\" w:lineRule=\"atLeast\"/>",
                1)
        else:
            body2 = ("<w:pPr><w:spacing w:after=\"0\" w:line=\"200\" "
                     "w:lineRule=\"atLeast\"/></w:pPr>") + body2
        # 10pt entries so a 31-entry TOC + note fit one page
        if "<w:rPr>" in body2:
            body2 = body2.replace("<w:rPr>", "<w:rPr><w:sz w:val=\"20\"/><w:szCs w:val=\"20\"/>", 1)
        else:
            body2 = "<w:rPr><w:sz w:val=\"20\"/><w:szCs w:val=\"20\"/></w:rPr>" + body2
        stylesxml = stylesxml[:m.start(2)] + body2 + stylesxml[m.end(2):]
    return stylesxml


def main():
    zin = zipfile.ZipFile(PATH)
    names = zin.namelist()
    docxml = zin.read("word/document.xml").decode("utf-8")
    rels = zin.read("word/_rels/document.xml.rels").decode("utf-8")
    stylesxml = zin.read("word/styles.xml").decode("utf-8")

    # rId -> footer target
    rid2target = dict(re.findall(r'<Relationship[^>]*Id="([^"]+)"[^>]*Target="(footer\d+\.xml)"', rels))
    for m in re.finditer(r'<Relationship\b[^>]*>', rels):
        tag = m.group(0)
        rid = re.search(r'Id="([^"]+)"', tag)
        tgt = re.search(r'Target="(footer\d+\.xml)"', tag)
        if rid and tgt:
            rid2target[rid.group(1)] = tgt.group(1)

    sects = re.findall(r"<w:sectPr\b.*?</w:sectPr>", docxml, flags=re.S)
    plan = {}
    for s in sects:
        fmt = None
        m = re.search(r'<w:pgNumType[^>]*w:fmt="([^"]+)"', s)
        if m:
            fmt = m.group(1)
        for fm in re.finditer(r'<w:footerReference[^>]*r:id="([^"]+)"', s):
            f = rid2target.get(fm.group(1))
            if f:
                if fmt == "upperRoman":
                    plan["word/" + f] = "ROMAN"
                else:
                    plan["word/" + f] = "arabic"
    print("footer plan:", plan)

    # remove empty pgNumType (cover section)
    n0 = docxml.count("<w:pgNumType/>")
    docxml = docxml.replace("<w:pgNumType/>", "")
    print("removed empty pgNumType:", n0)

    # TOC duplicate entry
    docxml, removed = fix_toc_duplicate(docxml)
    print("removed duplicate TOC entry:", removed)

    # compact TOC styles
    stylesxml = compact_toc_styles(stylesxml)
    print("compacted TOC1/2/3 styles")

    zout = zipfile.ZipFile(TMP, "w", zipfile.ZIP_DEFLATED)
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename == "word/document.xml":
            data = docxml.encode("utf-8")
        elif item.filename == "word/styles.xml":
            data = stylesxml.encode("utf-8")
        elif item.filename in plan:
            xml = data.decode("utf-8")
            fmt = plan[item.filename]
            xml, k = re.subn(
                r"(<w:instrText[^>]*>)\s*PAGE\s*(</w:instrText>)",
                r"\1 PAGE \\* " + fmt + r" \\* MERGEFORMAT \2", xml)
            print(f"patched {item.filename}: {k} PAGE field(s) -> {fmt}")
            data = xml.encode("utf-8")
        zout.writestr(item, data)
    zout.close()
    zin.close()
    shutil.move(TMP, PATH)
    print("patched", PATH)


if __name__ == "__main__":
    sys.exit(main())
