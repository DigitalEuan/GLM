import re
import os
from GLM11_runtime import GLMRuntimeV37, WordMath, geometricize_word, encode_semantic_octad
from GLM01_substrate import WordEntry, LEECH_ENGINE, BLA, _get_mog_category

class WordsAbsorber:
    def __init__(self, runtime: GLMRuntimeV37):
        self.rt = runtime
        self.stop_words = {"the", "and", "a", "of", "to", "in", "is", "it", "that", "as", "for", "was", "with"}

    def absorb_document(self, filepath: str):
        if not os.path.exists(filepath):
            print(f"❌ File not found: {filepath}")
            return

        print(f"📖 Ingesting document: {filepath}...")
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()

        # Extract unique words (alphabetic only, 3+ chars)
        raw_tokens = re.findall(r'\b[a-zA-Z]{3,}\b', text)
        unique_tokens = set(t.lower() for t in raw_tokens if t.lower() not in self.stop_words)
        
        new_count = 0
        for word in unique_tokens:
            if word not in self.rt.vocab_dict:
                # 1. Geometricize
                tag = geometricize_word(word)
                # 2. Map to 12-bit Intent -> 24-bit Octad
                wm = WordMath(tag["layer"], tag["arm"], tag["category"], 0, word)
                vec = encode_semantic_octad(wm)
                nrci = float(LEECH_ENGINE.calculate_nrci(vec))
                
                # 3. Inject into live runtime
                self.rt.vocab_dict[word] = WordEntry(
                    word=word, vector=vec, role=tag["category"].upper(), 
                    ubp_id=f"ABSORBED_{word.upper()}",
                    nrci=nrci, golay_codeword=vec, fold3=BLA.fold24_to3(vec),
                    mog_category=_get_mog_category(vec)
                )
                new_count += 1

        print(f"✅ Absorption Complete. Learned {new_count} new geometric anchors.")
        print(f"📊 Total Runtime Vocabulary: {len(self.rt.vocab_dict)} words.")

# --- EXAMPLE USAGE ---
if __name__ == "__main__":
    # Initialize the upgraded runtime
    rt = GLMRuntimeV37()
    absorber = WordsAbsorber(rt)
    
    # If you have a file named 'research_notes.txt', it would learn it here:
    # absorber.absorb_document('research_notes.txt')
    
    # For now, let's simulate a small "Document" string to prove it works
    sample_doc = "The holographic principle suggests that information entropy is proportional to the boundary area."
    with open('temp_context.txt', 'w') as f: f.write(sample_doc)
    
    absorber.absorb_document('temp_context.txt')