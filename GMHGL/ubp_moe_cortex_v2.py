import json
import math
import random
import re
import os
from fractions import Fraction
from ubp_semantic_engine import UBPSemanticEngine
from ubp_unified_v5 import BinaryLinearAlgebra, GOLAY_ENGINE, LEECH_ENGINE

class UBPMoECortexV2:
    STOP_WORDS = {'is', 'the', 'a', 'an', 'of', 'to', 'and', 'in', 'with', 'for', 'on'}

    def __init__(self):
        print("[Cortex] Initializing MoE v2.0 (Functional Bypass)...")
        self.semantic_engine = UBPSemanticEngine()
        self.semantic_engine.load('ubp_system_kb.json', 'ubp_lang_kb_combined_v4.json')
        
        # Hydrate N-Gram Manifold with BOTH English and UBP Logic
        self.vocab, self.manifold, self.char_to_idx = self._train_linguist()
        self.order = 5

    def _train_linguist(self):
        docs = []
        # 1. Load English Definitions
        if os.path.exists('ubp_lexicon_v2_defs.json'):
            with open('ubp_lexicon_v2_defs.json', 'r') as f:
                lex = json.load(f)
                for v in lex['c'].values(): docs.append(v[0].lower())
        
        # 2. Load UBP Scientific Descriptions (Crucial for "Scientific Grammar")
        for entry in self.semantic_engine.all_kb.values():
            docs.append(entry['lexicon'].lower())
        
        text = "  ".join(docs)
        text = re.sub(r'[^a-z0-9 :_-]', '', text)
        vocab = sorted(list(set(text)))
        c2i = {c: i for i, c in enumerate(vocab)}
        
        manifold = {}
        print(f"Training Linguist on {len(text)} characters...")
        for _ in range(2000000):
            idx = random.randint(0, len(text) - 6)
            ctx, tar = text[idx:idx+5], text[idx+5]
            if ctx not in manifold: manifold[ctx] = [0.01] * len(vocab)
            manifold[ctx][c2i[tar]] += 1.0
        return vocab, manifold, c2i

    def _get_vector(self, word):
        res = self.semantic_engine.query(word, top_k=1)
        if res and res[0].resonance_score > 0.5:
            uid = res[0].ubp_id
            return self.semantic_engine.all_kb[uid]['vector'], uid
        return None, None

    def research(self, objective_str, max_words=12):
        print(f"\n{'═'*80}\n[MOE RESEARCH] OBJECTIVE: {objective_str.upper()}\n{'═'*80}")
        
        goal_vec, goal_id = self._get_vector(objective_str)
        if not goal_vec: return "Objective not found."
        
        current_sentence = objective_str + " is "
        used_words = {objective_str, "is"}
        
        for _ in range(max_words):
            # 1. LINGUIST: Propose 20 candidates
            candidates = self._propose_candidates(current_sentence, count=20)
            
            best_word = None
            max_score = -1.0
            
            # 2. PHYSICIST & AUDITOR: Evaluate
            for word in candidates:
                word_clean = word.strip().lower()
                if word_clean in used_words or len(word_clean) < 2: continue
                
                # BYPASS: Glue words get a base score
                if word_clean in self.STOP_WORDS:
                    score = 0.5 
                else:
                    # CONTENT WORD: Geometric Audit
                    word_vec, word_id = self._get_vector(word_clean)
                    if not word_vec: 
                        score = 0.1 # Penalize unknown content words
                    else:
                        # Calculate XOR Bridge Stability to the Objective
                        bridge = [(a ^ b) for a, b in zip(goal_vec, word_vec)]
                        decoded, _, _ = GOLAY_ENGINE.decode(bridge)
                        stable_bridge = GOLAY_ENGINE.encode(decoded)
                        tax = LEECH_ENGINE.calculate_symmetry_tax(stable_bridge)
                        nrci = float(Fraction(10, 1) / (Fraction(10, 1) + tax))
                        score = nrci * 1.5 # Reward geometric stability
                
                if score > max_score:
                    max_score = score
                    best_word = word_clean
            
            if not best_word: break
            
            current_sentence += best_word + " "
            used_words.add(best_word)
            print(f"  [Expert Consensus] Added '{best_word}' (Score: {max_score:.4f})")
            
            if current_sentence.endswith(". "): break
            
        print(f"\n[FINAL FINDING] {current_sentence}")
        return current_sentence

    def _propose_candidates(self, sentence, count=20):
        words = []
        for _ in range(count):
            temp_sentence = sentence
            current_word = ""
            for _ in range(15):
                ctx = temp_sentence[-self.order:]
                if ctx not in self.manifold: break
                # Use higher temp (0.5) for candidate generation
                weights = [math.pow(w, 1/0.5) for w in self.manifold[ctx]]
                char = self.vocab[random.choices(range(len(self.vocab)), weights=weights)[0]]
                if char == " ": break
                current_word += char
                temp_sentence += char
            if current_word: words.append(current_word)
        return list(set(words))

# --- EXECUTION ---
moe = UBPMoECortexV2()
moe.research("hydrogen")
moe.research("stability")