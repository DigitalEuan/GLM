"""Fix Unicode super/subscripts in generate_pdf_report.py by replacing them
with ReportLab <super>/<sub> tags per the Character Safety Rule."""
import re

PATH = "/home/z/my-project/scripts/generate_pdf_report.py"
with open(PATH) as f:
    content = f.read()

# Order matters: replace multi-char sequences before single chars
replacements = [
    # Superscripts (negative)
    ("⁻¹⁵", "<super>-15</super>"),
    ("⁻⁵",  "<super>-5</super>"),
    ("⁻⁴",  "<super>-4</super>"),
    ("⁻³",  "<super>-3</super>"),
    ("⁻²",  "<super>-2</super>"),
    ("⁻¹",  "<super>-1</super>"),
    # Positive superscripts (check 2-digit before 1-digit)
    ("¹⁰",  "<super>10</super>"),
    ("²⁴",  "<super>24</super>"),
    ("²³",  "<super>23</super>"),
    ("¹⁸",  "<super>18</super>"),
    ("¹²",  "<super>12</super>"),
    ("¹¹",  "<super>11</super>"),
    ("¹⁶",  "<super>16</super>"),
    ("²⁵",  "<super>25</super>"),
    ("¹⁹",  "<super>19</super>"),
    ("²⁰",  "<super>20</super>"),
    ("¹⁵",  "<super>15</super>"),
    ("²²",  "<super>22</super>"),
    ("²⁸",  "<super>28</super>"),
    # Single-digit superscripts
    ("²",  "<super>2</super>"),
    ("³",  "<super>3</super>"),
    ("⁴",  "<super>4</super>"),
    ("⁵",  "<super>5</super>"),
    ("⁶",  "<super>6</super>"),
    ("⁷",  "<super>7</super>"),
    ("⁸",  "<super>8</super>"),
    ("⁹",  "<super>9</super>"),
    ("¹",  "<super>1</super>"),
    ("⁰",  "<super>0</super>"),
    # Subscripts (check 2-digit before 1-digit)
    ("₂₄", "<sub>24</sub>"),
    ("₁₀", "<sub>10</sub>"),
    ("₂₃", "<sub>23</sub>"),
    ("₂₀", "<sub>20</sub>"),
    ("₁₆", "<sub>16</sub>"),
    ("₂₂", "<sub>22</sub>"),
    # Single subscripts
    ("₀", "<sub>0</sub>"),
    ("₁", "<sub>1</sub>"),
    ("₂", "<sub>2</sub>"),
    ("₃", "<sub>3</sub>"),
    ("₄", "<sub>4</sub>"),
    ("₅", "<sub>5</sub>"),
    ("₆", "<sub>6</sub>"),
    ("₇", "<sub>7</sub>"),
    ("₈", "<sub>8</sub>"),
    ("₉", "<sub>9</sub>"),
]

orig = content
for old, new in replacements:
    content = content.replace(old, new)

# Count changes
n_changed = sum(1 for o, _ in replacements if orig.count(o) > 0)
print(f"Applied {len(replacements)} replacement rules")

# Verify no Unicode super/subscripts remain
import unicodedata
remaining = set()
for c in content:
    cat = unicodedata.category(c)
    if cat == 'No' or (0x2070 <= ord(c) <= 0x209F):  # Number, other OR super/subscript block
        remaining.add(c)
if remaining:
    print(f"WARNING: remaining super/subscript characters: {remaining}")
else:
    print("OK: no Unicode super/subscripts remain")

with open(PATH, "w") as f:
    f.write(content)
print(f"Saved: {PATH}")
