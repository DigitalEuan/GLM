import json
import os

# ==========================================
# INGESTION CONFIGURATION V1.0
# ==========================================
# List the proposed JSON files you want to ingest here:
PROPOSED_FILES = [
    'proposed_chromatic_law.json',
    'proposed_resonance_law.json'
]

SOURCE_KB = 'ubp_system_kb.json'
OUTPUT_KB = 'ubp_system_kb_1.json'
# ==========================================

# MOG Mapping Logic
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

def run_safe_ingestion():
    print(f"--- UBP SAFE INGESTION ENGINE v2.0 ---")
    
    if not os.path.exists(SOURCE_KB):
        print(f"❌ Error: Source KB '{SOURCE_KB}' not found.")
        return

    # 1. Load the Source KB
    with open(SOURCE_KB, 'r', encoding='utf-8') as f:
        kb_data = json.load(f)

    fields = kb_data["_fields"]
    params = kb_data["_params"]
    entries = kb_data["entries"]
    
    added_count = 0
    skipped_count = 0

    # 2. Process Each Proposed File
    for prop_file in PROPOSED_FILES:
        if not os.path.exists(prop_file):
            print(f"⚠️ Warning: {prop_file} not found. Skipping.")
            continue
            
        with open(prop_file, 'r', encoding='utf-8') as f:
            proposed_data = json.load(f)

        print(f"\nProcessing {prop_file}...")

        # 3. Append Entries
        for fp, entry in proposed_data.items():
            uid = entry.get("ubp_id", "UNKNOWN")
            
            if fp in entries:
                print(f"  ⏭️ Skipped {uid}: Fingerprint already exists.")
                skipped_count += 1
                continue
                
            # Extract Math Properties for MOG Tensor
            props = {}
            m = entry.get("math", "")
            if m and m != "0":
                for p in m.split('|'):
                    if '=' in p:
                        k, v = p.split('=', 1)
                        props[k] = v
                        
                        # Dynamically update _params if a new key is introduced
                        cat = get_mog_cat(k)
                        if k not in params[cat]:
                            params[cat].append(k)
                            params[cat].sort()
                            print(f"  [+] Added new parameter '{k}' to MOG Category '{cat}'")

            # Build the MOG Tensor Array
            tensor = []
            for cat, cat_keys in params.items():
                cat_values = []
                has_data = False
                for k in cat_keys:
                    val = props.get(k)
                    if val is not None:
                        cat_values.append(val)
                        has_data = True
                    else:
                        cat_values.append(0) # Null token
                tensor.append(cat_values if has_data else 0)

            # Construct the strict Columnar Array
            atlas = entry.get("atlas", {})
            flat_entry = [
                uid,
                entry.get("lexicon", ""),
                entry.get("tags", []),
                atlas.get("vector", []),
                atlas.get("nrci", "0/1"),
                atlas.get("nrci_score", 0.0),
                atlas.get("tax", "0/1"),
                tensor
            ]
            
            # Append to KB
            entries[fp] = flat_entry
            added_count += 1
            print(f"  ✅ Ingested: {uid}")

    # 4. Save to the New Output File
    if added_count > 0:
        with open(OUTPUT_KB, 'w', encoding='utf-8') as f:
            # Use separators to keep it ultra-compact
            json.dump(kb_data, f, separators=(',', ':'))
        print(f"\n🎉 Successfully wrote {added_count} new entries to '{OUTPUT_KB}'.")
        print(f"   (Original '{SOURCE_KB}' was not modified).")
    else:
        print(f"\nℹ️ No new entries were added ({skipped_count} skipped). '{OUTPUT_KB}' was not created.")

if __name__ == "__main__":
    run_safe_ingestion()