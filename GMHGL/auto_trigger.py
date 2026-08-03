"""
UBP Auto-Trigger v17.4 (Full Semantic + Numeric)
============================================
Now loads ubp_lang_kb_combined_v4.json + system KB
Semantic operators are detected and returned in context.
Author: E R A Craig & UBP Research Cortex + GLM Study Team
Date: 31 March 2026
"""

import json
import re
import os
from typing import List, Dict, Any

# --- 1. LOAD BOTH KNOWLEDGE BASES ---
kb_system_path = 'ubp_system_kb.json'
kb_lang_path   = 'ubp_lang_kb_combined_v4.json'

try:
    with open(kb_system_path, 'r', encoding='utf-8') as f:
        KB_SYSTEM = json.load(f)
    print(f"[Cortex] System KB loaded: {len(KB_SYSTEM)} entries")

    with open(kb_lang_path, 'r', encoding='utf-8') as f:
        KB_LANG = json.load(f)
    print(f"[Cortex] Language KB loaded: {len(KB_LANG)} semantic operators")

except Exception as e:
    print(f"[Cortex] CRITICAL LOAD ERROR: {e}")
    KB_SYSTEM = {}
    KB_LANG = {}

# --- 2. REVERSE MAPS (System + Language) ---
ID_TO_KEY = {}          # ubp_id → fingerprint (system)
PHRASE_TO_KEY = {}      # name → fingerprint (system)
OPERATOR_TO_KEY = {}    # OP_XXX → fingerprint (language)
OP_TRIGGER_WORDS = {}   # common words → operator fingerprint

for key, entry in KB_SYSTEM.items():
    uid = entry.get('ubp_id')
    if uid:
        ID_TO_KEY[uid] = key
    name = entry.get('lexicon', '').split(']')[0].strip('[]').split(':')[-1].strip()
    if name and name != "Unknown":
        PHRASE_TO_KEY[name.lower()] = key

for key, entry in KB_LANG.items():
    uid = entry.get('ubp_id')
    if uid and uid.startswith('OP_'):
        OPERATOR_TO_KEY[uid] = key
        # Simple trigger word extraction from lexicon
        lex_lower = entry.get('lexicon', '').lower()
        for word in ['why', 'how', 'what', 'which', 'and', 'or', 'not', 'xor', 'equal', 'greater', 'less', 
                     'before', 'after', 'during', 'know', 'believe', 'predict', 'infer', 'force', 'flow']:
            if word in lex_lower:
                OP_TRIGGER_WORDS[word] = key
                break

print(f"[Cortex] Maps ready — {len(OPERATOR_TO_KEY)} operators, {len(OP_TRIGGER_WORDS)} trigger words")

# ================================================================
# NUMERIC TRIGGER (Gray-code) — unchanged from previous version
# ================================================================
class MathStringParser:
    @staticmethod
    def parse(math_str: str) -> Dict[str, float]:
        if not math_str: return {}
        props = {}
        for pair in math_str.split('|'):
            if '=' in pair:
                k, v = pair.split('=', 1)
                k = k.strip()
                v = v.strip()
                try:
                    if '/' in v:
                        num, den = v.split('/')
                        props[k] = float(num) / float(den)
                    else:
                        props[k] = float(v)
                except:
                    pass
        return props

class MetricPreservingEncoder:
    def __init__(self):
        self.schema = {  # same as GLM Study Step 5
            'Z': {'scale':'linear','bits':7,'min':0,'max':120},
            'M': {'scale':'log','bits':8,'min':0.5,'max':310},
            'BP':{'scale':'log','bits':8,'min':0.05,'max':7000},
            'MP':{'scale':'log','bits':8,'min':0.05,'max':4000},
            'EN':{'scale':'linear','bits':6,'min':0,'max':4.5},
            'Ion':{'scale':'log','bits':8,'min':50,'max':30000},
            'Rho':{'scale':'log','bits':8,'min':5e-5,'max':30},
            'Rad':{'scale':'linear','bits':7,'min':20,'max':310},
            'Valence_e':{'scale':'linear','bits':4,'min':0,'max':8},
            'Phase_STP':{'scale':'linear','bits':2,'min':0,'max':3},
            'Oxidation':{'scale':'linear','bits':5,'min':-4,'max':8},
            'Crystal':{'scale':'linear','bits':4,'min':0,'max':10},
            'Dipole':{'scale':'linear','bits':8,'min':0,'max':10},
            'Density':{'scale':'log','bits':8,'min':5e-5,'max':30},
            'pKa1':{'scale':'linear','bits':8,'min':-2,'max':16},
        }

    def _gray_encode(self, value: int, bits: int) -> list[int]:
        binary = value ^ (value >> 1)
        return [(binary >> i) & 1 for i in range(bits-1, -1, -1)]

    def encode(self, props: Dict[str, float]) -> list[int]:
        vector = []
        for key, spec in self.schema.items():
            val = props.get(key)
            present = 1 if val is not None else 0
            vector.append(present)
            if present:
                v = max(spec['min'], min(spec['max'], val))
                if spec['scale'] == 'log':
                    v = (v - spec['min']) / (spec['max'] - spec['min'] + 1e-12)
                    v = int(v * (2**spec['bits'] - 1))
                else:
                    v = int((v - spec['min']) / (spec['max'] - spec['min']) * (2**spec['bits'] - 1))
                vector.extend(self._gray_encode(v, spec['bits']))
            else:
                vector.extend([0] * spec['bits'])
        return vector[:142]

encoder = MetricPreservingEncoder()

def numeric_trigger(text: str) -> List[Dict]:
    math_str = ""  # reuse the heuristic from before
    text_l = text.lower()
    m = re.search(r'mass.*?(\d+\.?\d*)|molecular weight.*?(\d+\.?\d*)|(\d+\.?\d*)\s*g/mol', text_l)
    if m: math_str += f"M={float(next(x for x in m.groups() if x))}|"
    bp = re.search(r'boil.*?(\d+\.?\d*)|bp.*?(\d+\.?\d*)', text_l)
    if bp: math_str += f"BP={float(next(x for x in bp.groups() if x))}|"
    mp = re.search(r'melt.*?(\d+\.?\d*)|mp.*?(\d+\.?\d*)', text_l)
    if mp: math_str += f"MP={float(next(x for x in mp.groups() if x))}|"
    if 'liquid' in text_l or 'solvent' in text_l: math_str += "Phase_STP=2|"

    if not math_str: return []
    props = MathStringParser.parse(math_str)
    query_vec = encoder.encode(props)

    memories = []
    for key, entry in KB_SYSTEM.items():
        gray = entry.get('atlas', {}).get('gray_vector')
        if gray and len(gray) == 142:
            dist = sum(x != y for x, y in zip(query_vec, gray))
            if dist <= 14:
                memories.append({
                    "data": entry,
                    "match": "NUMERIC",
                    "boost": 3.5 - (dist / 142),
                    "numeric_dist": dist,
                    "math_str": math_str
                })
    return sorted(memories, key=lambda x: x['boost'], reverse=True)[:12]

# --- 3. MAIN REFLEXIVE RECALL (now fully semantic) ---
def reflexive_recall(text: str):
    memories = {}
    input_lower = text.lower()

    # 1. NUMERIC TRIGGER (highest priority)
    for m in numeric_trigger(text):
        key = next((k for k, v in KB_SYSTEM.items() if v is m['data']), None)
        if key:
            memories[key] = m

    # 2. OPERATOR TRIGGER (semantic understanding)
    for word, op_key in OP_TRIGGER_WORDS.items():
        if word in input_lower and op_key not in memories:
            if op_key in KB_LANG:
                memories[op_key] = {
                    "data": KB_LANG[op_key],
                    "match": "OPERATOR",
                    "boost": 3.0
                }

    # 3. PHRASE + ID (system KB)
    for phrase, key in PHRASE_TO_KEY.items():
        if phrase in input_lower and key not in memories:
            memories[key] = {"data": KB_SYSTEM[key], "match": "PHRASE", "boost": 2.2}

    ids = re.findall(r'\b[A-Z]+_[A-Z0-9_]+_\d+\b', text)
    for uid in ids:
        key = ID_TO_KEY.get(uid)
        if key and key not in memories:
            memories[key] = {"data": KB_SYSTEM[key], "match": "ID", "boost": 1.8}

    # 4. KEYWORD FALLBACK
    if len(memories) < 10:
        words = re.findall(r'\b\w{4,}\b', input_lower)
        for word in words:
            for key, entry in KB_SYSTEM.items():
                if word in entry.get('lexicon', '').lower() and key not in memories:
                    memories[key] = {"data": entry, "match": "KEYWORD", "boost": 1.0}
            for key, entry in KB_LANG.items():
                if word in entry.get('lexicon', '').lower() and key not in memories:
                    memories[key] = {"data": entry, "match": "KEYWORD_OP", "boost": 1.2}

    # Format context for AI
    final_context = []
    sorted_mem = sorted(memories.values(), key=lambda x: x.get('boost', 1.0), reverse=True)
    for m in sorted_mem[:15]:
        entry = m['data']
        atlas = entry.get('atlas', {})
        ctx = {
            "ubp_id": entry.get('ubp_id'),
            "name": entry.get('lexicon', '').split(']')[0].strip('[]').split(':')[-1].strip(),
            "math": entry.get('math'),
            "hierarchy": atlas.get('hierarchy'),
            "nrci": str(entry.get('atlas', {}).get('nrci_score', 'N/A')),
            "match_type": m.get('match'),
            "numeric_dist": m.get('numeric_dist')
        }
        final_context.append(ctx)

    return final_context

if __name__ == "__main__":
    test = "why does water dissolve sodium chloride"
    print(json.dumps(reflexive_recall(test), indent=2))
