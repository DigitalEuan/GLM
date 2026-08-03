from GLM08_idea_meta_graph import IdeaMetaGraph, CrystallisedIdea

print("=== Testing Module 08: Meta-Graph ===")

# 1. Initialize (should create or load the file)
meta = IdeaMetaGraph("test_meta.json")

# 2. Create a mock crystallized idea
class MockZone:
    def __init__(self):
        self.centroid = [1] * 24
        self.topic_nouns = ["entropy", "chaos"]
        self.thesis = "Entropy leads to chaos."
        self.crg_backbone = []
        self.peak_coherence = 0.85
        self.turns = 5

mock_zone = MockZone()
new_idea = meta.record(mock_zone)
print(f"✅ Recorded: {new_idea.idea_id}")

# 3. Test Matching (Warm-Start)
# Simulate user typing "entropy"
match = meta.match([[1]*24], ["entropy"])
if match:
    print(f"✅ Warm-Start Match Found: {match.idea_id} ('{match.thesis}')")
else:
    print("❌ Match Failed.")

print(f"✅ Stats: {meta.stats()}")