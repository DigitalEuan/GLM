import json
import os
from ubp_viz import save_scene_3d

# ==========================================
# CONFIGURATION
# ==========================================
# Enter the name of the file you want to see
TARGET_FILE = 'scene_3d_3D.json' 
# ==========================================

def load_and_render():
    print(f"--- VISUALIZATION LOADER ---")
    print(f"Target: {TARGET_FILE}")

    # 1. Check if file exists
    if not os.path.exists(TARGET_FILE):
        print(f"❌ Error: File '{TARGET_FILE}' not found in Workspace.")
        print("Please check the filename and try again.")
        return

    # 2. Read the data
    try:
        with open(TARGET_FILE, 'r') as f:
            scene_data = json.load(f)
        
        # 3. Send to Visualizer
        # This function writes the data to 'scene_3d.json', 
        # which triggers the React frontend to update the 3D view.
        save_scene_3d(scene_data)
        
        print(f"✅ Data loaded successfully.")
        print(f"   Points: {len(scene_data.get('points', []))}")
        print(f"   Lines:  {len(scene_data.get('lines', []))}")
        print("Check the 'Visual' tab to see the result.")

    except json.JSONDecodeError:
        print(f"❌ Error: '{TARGET_FILE}' is not valid JSON.")
    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    load_and_render()