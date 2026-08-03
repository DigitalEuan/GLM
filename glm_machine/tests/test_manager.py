from GLM01_substrate import _build_vocabulary, build_default_crg
from GLM07_idea_manager import IdeaManager

print("=== Testing Module 07: Idea Manager ===")
vocab_dict = _build_vocabulary()
class VocabWrapper:
    def __init__(self, d): self.words = d
vocab = VocabWrapper(vocab_dict)
crg = build_default_crg()

manager = IdeaManager(vocab=vocab, crg=crg)

# 1. Add Entropy to Zone 0
if "entropy" in vocab.words:
    print("Turn 1: Adding 'entropy'...")
    manager.update([("entropy", vocab.words["entropy"])], turn=1)
    print(f"  Active Zone: {manager.active_idx} | Total Zones: {len(manager.zones)}")

# 2. Add something far away (if your KB has it, otherwise use a dummy)
# Let's simulate a 'far' vector
from GLM01_substrate import WordEntry
far_word = "quantum"
if far_word in vocab.words:
    print(f"Turn 2: Adding '{far_word}'...")
    manager.update([(far_word, vocab.words[far_word])], turn=2)
    print(f"  Active Zone: {manager.active_idx} | Total Zones: {len(manager.zones)}")

print("✅ Manager Test Complete.")