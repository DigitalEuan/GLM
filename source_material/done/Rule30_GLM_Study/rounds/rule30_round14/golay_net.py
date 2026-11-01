"""Round 14: the GLM's Golay / Leech 'lattice shortcut' network, rebuilt from its published data.

Generator rows G = [I12 | B] are the twelve 24-bit masks of the GLM's `Shortcut/Golay.lean`.
Decoding is complete minimum-distance decoding by syndrome; the coset leader of a syndrome is
the minimum-weight word with that syndrome, ties broken by the smallest integer value
(the rule used in the Lean file ShortcutNetworkData.lean).  `glm_leaders()` reads the GLM's own
packed leader table, so the two tie-breaks can be compared.
"""
import numpy as np, os, re, zipfile

ROWS = [16769025, 4681730, 10727428, 13750280, 6877200, 11825184,
        14299200, 15536256, 7770368, 3887616, 1946624, 9361408]

def cw(m):
    c = 0
    for j in range(12):
        if (m >> j) & 1:
            c ^= ROWS[j]
    return c

CODE = np.array([cw(m) for m in range(4096)], dtype=np.int64)
POP8 = np.array([bin(i).count("1") for i in range(256)], dtype=np.int64)

def pop(x):
    x = np.asarray(x, dtype=np.int64)
    return POP8[x & 255] + POP8[(x >> 8) & 255] + POP8[(x >> 16) & 255]

def syn(v):
    v = np.asarray(v, dtype=np.int64)
    return (v ^ CODE[v & 4095]) >> 12

def min_leaders():
    v = np.arange(1 << 24, dtype=np.int64)
    s = syn(v); w = pop(v)
    key = (w << 24) | v                     # weight first, then value
    best = np.full(4096, 1 << 62, dtype=np.int64)
    np.minimum.at(best, s, key)
    return best & ((1 << 24) - 1), best >> 24

def glm_leaders(zip_path=os.path.join(os.path.dirname(__file__), "..", "glm_repo.zip")):
    with zipfile.ZipFile(zip_path) as z:
        name = [n for n in z.namelist() if n.endswith("glm_lean/RequestProject/GLM/Shortcut/Decoder.lean")][0]
        txt = z.read(name).decode()
    hexs = re.search(r"def leaderNat : ℕ :=\s*0x([0-9a-fA-F]+)", txt).group(1)
    big = int(hexs, 16)
    return np.array([(big >> (24 * s)) & ((1 << 24) - 1) for s in range(4096)], dtype=np.int64)

_LEAD = None
def leaders():
    global _LEAD
    if _LEAD is None:
        cache = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leaders_min.npy")
        if os.path.exists(cache):
            _LEAD = np.load(cache)
        else:
            _LEAD, _ = min_leaders(); np.save(cache, _LEAD)
    return _LEAD

def decode(v, lead=None):
    lead = leaders() if lead is None else lead
    v = np.asarray(v, dtype=np.int64)
    return v ^ lead[syn(v)]
