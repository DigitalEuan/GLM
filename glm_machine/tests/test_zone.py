import sys
import time
from GLM01_substrate import _build_vocabulary, build_default_crg
from GLM06_idea_zone import IdeaZone

# Force output to be immediate
def log(msg):
    print(msg, flush=True)

log("=== Testing Module 06: Idea Zone (Diagnostic Mode) ===")

log("Step 1: Loading Vocabulary (This may take 10-20 seconds)...")
start_time = time.time()
try:
    vocab_dict = _build_vocabulary()
    elapsed = time.time() - start_time
    log(f"✅ Vocabulary Loaded in {elapsed:.2f}s. Found {len(vocab_dict)} words.")
except Exception as e:
    log(f"❌ Failed to load vocabulary: {e}")
    sys.exit(1)

log("Step 2: Building CRG...")
crg = build_default_crg()
log(f"✅ CRG Built with {len(crg.edges)} edges.")

# Wrap the dict in a simple object so GLM06 can use it
class VocabWrapper:
    def __init__(self, d): self.words = d
vocab = VocabWrapper(vocab_dict)

log("Step 3: Initializing Idea Zone...")
zone = IdeaZone()
zone.set_context(crg, vocab)

# Seed with Entropy
target = "entropy"
if target in vocab.words:
    log(f"Step 4: Seeding with '{target}'...")
    h_entry = vocab.words[target]
    zone.update([(target, h_entry)], turn=1)
    log(f"✅ Seeded: {zone.status_line()}")
    
    log("Step 5: Running Autonomous Tick (Thinking)...")
    res = zone.tick()
    log(f"✅ Autonomous Discovery: {res['discovered']}")
    log(f"✅ Final State: {zone.status_line()}")
else:
    log(f"❌ Error: '{target}' not found in vocabulary. Check your Lang KB.")