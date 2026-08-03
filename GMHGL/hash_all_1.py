"""
UBP HASH INDEXER v3.0 (Universal Merged Edition)
================================================
Generates a unified 'ubp_hash_memory_kb.json' index from all 
active Knowledge Base files (System + Language).

Author: E R A Craig, New Zealand  and the UBP Research Cortex v4.2.7
Date: 07 April 2026
"""

import json
import os

def run_indexing():
    # 1. Configuration: Define all KB files to be indexed
    kb_files = [
        'ubp_system_kb.json',
        'ubp_lang_kb_combined_v4.json'
    ]
    output_file = 'ubp_hash_memory_kb_1.json'
    
    hash_memory = {}
    total_processed = 0
    collisions_resolved = 0

    print("--- UBP UNIVERSAL INDEXING START ---")

    for f_path in kb_files:
        if not os.path.exists(f_path):
            print(f"⚠️  Skipping: {f_path} (File not found)")
            continue

        print(f"🔍 Processing: {f_path}...")
        
        try:
            with open(f_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"❌ Error reading {f_path}: {e}")
            continue

        # 2. Detect Format and Extract Entries
        entries_to_index = {}
        idx_id = None

        if isinstance(data, dict) and "_fields" in data:
            # v9.9 Ultra-Compact Columnar Format
            fields = data["_fields"]
            if "ubp_id" in fields:
                idx_id = fields.index("ubp_id")
                entries_to_index = data["entries"]
                print(f"   Format: v9.9 Columnar detected ({len(entries_to_index)} entries)")
        elif isinstance(data, dict):
            # Legacy Dictionary Format
            entries_to_index = data
            print(f"   Format: Legacy Dictionary detected ({len(entries_to_index)} entries)")
        else:
            print(f"   Format: Unknown/Unsupported for {f_path}")
            continue

        # 3. Build the Index
        for full_hash, entry in entries_to_index.items():
            # Extract the UBP ID based on format
            if isinstance(entry, list) and idx_id is not None:
                uid = entry[idx_id]
            elif isinstance(entry, dict):
                uid = entry.get("ubp_id", "UNK")
            else:
                continue

            # Generate short key (8 chars)
            short_key = full_hash[:8]
            
            # 4. Collision Resolution Logic
            # If prefix exists but points to a DIFFERENT ID, we have a collision
            if short_key in hash_memory and hash_memory[short_key]["ubp_id"] != uid:
                collisions_resolved += 1
                # Extend prefix to 12 chars to ensure uniqueness
                short_key = full_hash[:12]
                
            hash_memory[short_key] = {
                "ubp_id": uid,
                "full_hash": full_hash
            }
            total_processed += 1

    # 5. Save the Unified Index
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(hash_memory, f, indent=2)
        
        print("\n" + "="*40)
        print(f"✅ INDEXING COMPLETE")
        print(f"   Total Entries Processed: {total_processed}")
        print(f"   Unique Index Keys:       {len(hash_memory)}")
        print(f"   Collisions Resolved:     {collisions_resolved}")
        print(f"   Saved to:                {output_file}")
        print("="*40)
    except Exception as e:
        print(f"❌ Failed to save index: {e}")

if __name__ == "__main__":
    run_indexing()
