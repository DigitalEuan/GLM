"""
UBP MOG MAPPER v2.1 (Ultra-Compact)
===================================
- Replaces 'null' with '0' (1-byte token).
- Preserves ALL fields (Tags, NRCI, Tax, etc.) in a fixed-index list.
- Generates a 'ubp_system_kb.json' for maximum environment efficiency.
- FIXED: Handles both list and dict input structures to prevent AttributeError.
"""

import json
import os
import importlib
import ubp_kb_architect
importlib.reload(ubp_kb_architect)
from ubp_kb_architect import KBArchitect, MOG_CATEGORIES

MAPPING = {
    "M": "M_Mass", "Mass": "M_Mass", "Z": "M_Count", "BP": "M_Thermal", 
    "MP": "M_Thermal", "Rho": "I_Density", "Density": "I_Density",
    "Formula": "I_Connectivity", "Energy": "A_Energy", "c": "A_Velocity"
}

def get_mog_cat(key):
    if key in MAPPING: return MAPPING[key]
    k = key.lower()
    if "time" in k or "period" in k: return "M_Time"
    if "charge" in k or "ion" in k: return "M_Charge"
    if "force" in k or "gravity" in k: return "A_Force"
    return "I_Complexity"

def run_ultra_migration():
    with open('ubp_system_kb.json', 'r') as f: raw_data = json.load(f)
    
    # Normalize input to a list of dictionaries
    if isinstance(raw_data, dict):
        if "entries" in raw_data:
            print("File is already in ultra-compact format.")
            return
        entries_list = list(raw_data.values())
    else:
        entries_list = raw_data
    
    # 1. Build Global Sub-Schema
    param_map = {cat: set() for cat in MOG_CATEGORIES}
    for entry in entries_list:
        m = entry.get("math", "")
        if m and m != "0":
            for p in m.split('|'):
                if '=' in p: param_map[get_mog_cat(p.split('=')[0])].add(p.split('=')[0])
    
    MASTER_PARAMS = {cat: sorted(list(keys)) for cat, keys in param_map.items()}
    
    # 2. Remint and Flatten
    arch = KBArchitect()
    new_kb = {
        "_fields": ["ubp_id", "lexicon", "tags", "vector", "nrci_str", "nrci_val", "tax_str", "mog_tensor"],
        "_params": MASTER_PARAMS,
        "_null_token": 0,
        "entries": {}
    }
    
    for entry in entries_list:
        uid = entry.get("ubp_id", "UNKNOWN")
        props = {}
        m = entry.get("math", "")
        if m and m != "0":
            for p in m.split('|'):
                if '=' in p:
                    k, v = p.split('=', 1)
                    props[k] = v
        
        # Build MOG Tensor with Tokenized Nulls
        tensor = []
        for cat in MOG_CATEGORIES:
            cat_keys = MASTER_PARAMS[cat]
            cat_values = []
            has_data = False
            for k in cat_keys:
                val = props.get(k)
                if val is not None:
                    cat_values.append(val)
                    has_data = True
                else:
                    cat_values.append(0)
            
            tensor.append(cat_values if has_data else 0)
        
        # Generate Metrics
        fp, vec, n_str, n_val, tax_str = arch.create_raw_metrics(uid, props)
        
        # The Final Flattened List
        flat_entry = [
            uid,
            entry.get("lexicon", ""),
            entry.get("tags", []),
            vec,
            n_str,
            n_val,
            tax_str,
            tensor
        ]
        new_kb["entries"][fp] = flat_entry

    # Save with maximum minification
    with open('ubp_system_kb_1.json', 'w') as f:
        json.dump(new_kb, f, separators=(',', ':'))
    
    print(f"✅ Ultra-Compact Migration Complete.")
    print(f"   Original Size: {os.path.getsize('ubp_system_kb.json') / 1024:.2f} KB")
    print(f"   New Size:      {os.path.getsize('ubp_system_kb_1.json') / 1024:.2f} KB")

if __name__ == "__main__":
    run_ultra_migration()