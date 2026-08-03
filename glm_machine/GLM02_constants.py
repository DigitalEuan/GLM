# ══════════════════════════════════════════════════════════════════════════════
# §02  CONSTANTS & TUNABLES (v3.7.6 Hardened)
# ══════════════════════════════════════════════════════════════════════════════
import re

# ── 1. IDEA ZONE DYNAMICS ──────────────────────────────────────────────
IDEA_RADIUS        = 8      # Hamming distance within which a token "fits" the idea
REINFORCE_RES      = 1.0    # Resonance for a reinforcing token
DRIFT_RES          = 0.35   # Resonance for a drifting (off-topic) token
GET_IT_THRESHOLD   = 0.70   # Coherence at which the idea crystallises
MIN_EVIDENCE       = 3      # Need at least this many evidence tokens to crystallise
MIN_BACKBONE       = 1      # Need at least this many CRG edges to crystallise
MAX_EVIDENCE       = 16     # Rolling window — forget oldest evidence beyond this
MIN_TOPIC_NOUNS    = 2      # Need >= 2 topic nouns to form a relational idea

# ── 2. DECAY & MATURATION (v3.5) ───────────────────────────────────────
DECAY_LAMBDA       = 0.18   # Per turn; halflife ≈ 3.8 turns
PRUNE_FLOOR        = 0.08   # Evidence below this resonance is forgotten
TICK_AGE           = 0.35   # One tick ages evidence by 0.35 of a turn
INFERRED_RES       = 0.45   # Resonance for tick-discovered evidence
ADJACENT_RES       = 0.20   # Resonance for lattice-adjacent (no CRG) discoveries
TICK_SEARCH_RADIUS = 10     # Hamming radius for tick noun discovery
MAX_INFERRED       = 4      # Cap inferred evidence per tick cycle
REFINE_DELTA       = 0.05   # Coherence gain needed to re-announce a refined thesis

# ── 3. MULTI-ZONE & EXPANSION (v3.6+) ──────────────────────────────────
ZONE_SPAWN_THRESHOLD = 6    # Hamming distance threshold for spawning new zones
MAX_ZONES            = 3
AUTO_EXPAND_RADIUS   = 4    # Hamming distance for proposing new edges
AUTO_EXPAND_CONF     = 0.40 # Confidence for auto-proposed edges
LATTICE_LINK_RADIUS  = 4    # <--- ADDED: Threshold for aggressive lattice linking

# ── 4. LINGUISTIC FILTERS (Defect D1/D2 Fixes) ─────────────────────────
# v3.9.0: Extended with common verbs/fillers that the master resource
# injects as vocab entries (tell, about, discuss, etc.) — they pollute
# topic_nouns if not filtered.
FUNCTION_WORDS = frozenset({
    "what","how","why","when","who","where","which","whether",
    "is","are","was","were","be","been","being","do","does","did","done",
    "the","a","an","of","to","in","on","for","with","by","as","at","from",
    "and","or","but","not","no","yes","so","if","then","than","also","just",
    "explain","define","describe","compare","measure","tell","show","give",
    "between","relationship","connection","link","relates","relate","related",
    "about","more","like","kind","sort","type","example","mean","meaning",
    "can","could","would","should","may","might","will","shall",
    "i","you","he","she","we","they","it","that","this","those","these",
    "me","my","your","our","their","his","her","its",
    "hello","hi","hey","thanks","thank","please","ok","okay",
    # v3.9.0 additions — common verbs/fillers from the master resource
    "discuss","consider","suppose","assume","state","say","said",
    "use","used","using","uses","make","made","making","makes",
    "get","got","getting","gets","let","lets","letting",
    "know","known","knows","knowing","think","thinks","thinking",
    "see","sees","seeing","seen","saw","look","looks","looking",
    "come","comes","coming","came","go","goes","going","went",
    "find","finds","finding","found","want","wants","wanting","wanted",
    "put","puts","putting","set","sets","setting","take","takes","taking","took",
    "ask","asks","asking","asked","try","tries","trying","tried",
    "work","works","working","worked","play","plays","playing","played",
    "feel","feels","feeling","felt",
    "become","becomes","becoming","became","seem","seems","seemed",
    "turn","turns","turning","turned","leave","leaves","leaving","left",
    "call","calls","called","calling","keep","keeps","keeping","kept",
    "begin","begins","beginning","began","start","starts","starting","started",
    "stop","stops","stopping","stopped","end","ends","ending","ended",
    "live","lives","living","lived","die","dies","dying","died",
    "eat","eats","eating","ate","drink","drinks","drinking","drank",
    "sleep","sleeps","sleeping","slept","wake","wakes","waking","woke",
    "walk","walks","walking","walked","run","runs","running","ran",
    "stand","stands","standing","stood","sit","sits","sitting","sat",
    "read","reads","reading","write","writes","writing","wrote",
    "speak","speaks","speaking","spoke","talk","talks","talking","talked",
    "hear","hears","hearing","heard","listen","listens","listening","listened",
    "watch","watches","watching","watched","study","studies","studying","studied",
    "learn","learns","learning","learned","teach","teaches","teaching","taught",
})

PRONOUNS = frozenset({
    "they","it","that","this","those","these","he","she","we","i","you",
    "them","him","her","us","me","one",
})

# Clean verb whitelist (alpha-only lemmas)
_CLEAN_VERBS = [
    "generates","measures","commutes","scales","depends","transforms",
    "predicts","regularizes","captures","binds","links","relates",
    "forms","produces","encodes","defines","describes","constitutes",
    "reflects","exhibits","implies","determines","constrains",
]

_OP_SYNTAX_RE = re.compile(r"[()\s<>]")

# ── 5. EXPORT CONTROL ──────────────────────────────────────────────────
__all__ = [
    'IDEA_RADIUS', 'REINFORCE_RES', 'DRIFT_RES', 'GET_IT_THRESHOLD',
    'MIN_EVIDENCE', 'MIN_BACKBONE', 'MAX_EVIDENCE', 'MIN_TOPIC_NOUNS',
    'DECAY_LAMBDA', 'PRUNE_FLOOR', 'TICK_AGE', 'INFERRED_RES',
    'ADJACENT_RES', 'TICK_SEARCH_RADIUS', 'MAX_INFERRED', 'REFINE_DELTA',
    'ZONE_SPAWN_THRESHOLD', 'MAX_ZONES', 'AUTO_EXPAND_RADIUS', 'AUTO_EXPAND_CONF',
    'LATTICE_LINK_RADIUS', 'FUNCTION_WORDS', 'PRONOUNS', '_CLEAN_VERBS', '_OP_SYNTAX_RE'
]

if __name__ == "__main__":
    print("=== Testing Module 02: Constants ===")
    print(f"✅ Loaded {len(__all__)} constants.")
    print(f"  Example: IDEA_RADIUS is {IDEA_RADIUS}")