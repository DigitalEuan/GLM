ENCODING STRATEGY MAP
=====================

PRINCIPLE: Meaning IS the vector from a reference point.
           The concept IS the relation to its origin.
           The GLM speaks by computing vector operations.

THE 24-BIT DATA OBJECT (4×6 MOG grid):
  Reality row (6 bits)    = domain ID (which domain this concept belongs to)
  Info row (6 bits)       = the specific value within the domain
  Activation row (6 bits) = secondary properties (magnitude, energy, etc.)
  Potential row (6 bits)  = context (phase, scale, parity, etc.)

DOMAIN ENCODERS:
  Domain 0: Direction
    Reference: center (0,0,0)
    Vector: 3D (x, y, z) with sign
    Concepts: left(-1,0,0), right(+1,0,0), up(0,+1,0), down(0,-1,0),
              forward(0,0,+1), back(0,0,-1), center(0,0,0)
    Operations: addition (composition), cosine (same/opposite/orthogonal)
    Key test: left + right = center (opposites cancel)

  Domain 1: Temperature
    Reference: freezing (0°C)
    Vector: 1D scalar (temperature in °C)
    Concepts: freezing(0), cold(10), cool(20), tepid(30), warm(40), hot(60), boiling(100)
    Operations: subtraction (difference), addition (sum)
    Key test: hot - cold = warm (the difference IS the midpoint)

  Domain 2: Color
    Reference: red (700nm, longest visible wavelength)
    Vector: 1D scalar (offset from red in nm)
    Concepts: red(0), orange(80), yellow(120), green(170), blue(230), indigo(260), violet(320)
    Operations: subtraction (wavelength difference)
    Key test: red - violet = -320nm (the full visible spectrum)

  Domain 3: Size
    Reference: tiny (magnitude 1)
    Vector: 1D scalar (offset from tiny)
    Concepts: tiny(0), small(3), medium(9), big(14), large(19), huge(39), giant(62)
    Operations: subtraction (size difference), scaling (multiplication)
    Key test: 2 × small = medium (scaling works)

  Domain 4: Number
    Reference: zero
    Vector: 1D scalar (the number itself)
    Concepts: 0, 1, 2, 3, 5, 7, 10, 20, 50
    Operations: addition, subtraction, scaling (multiplication)
    Key test: 2 + 3 = 5 (arithmetic works)

  Domain 5: Force
    Reference: zero_force
    Vector: 1D scalar (force magnitude)
    Concepts: zero_force(0), weak(10), gentle(20), moderate(30), strong(45), powerful(55), massive(63)
    Operations: addition (combined forces), subtraction (force difference)
    Key test: massive - weak = 53 (the force range)

VECTOR OPERATIONS (how the GLM speaks):
  Addition (c1 + c2):     Composition — what do you get when you combine them?
  Subtraction (c1 - c2):  Difference — what is the gap between them?
  Cosine similarity:      Relation type — same(1.0), opposite(-1.0), orthogonal(0.0)
  Scaling (n × c):        Multiplication — what is n times this concept?

CROSS-DOMAIN RULE:
  Cross-domain operations produce orthogonal results (cosine ≈ 0).
  This IS meaningful: the GLM says "these concepts don't directly relate."
  Example: left vs hot → cosine ≈ 0 (a direction is not a temperature)

THE SNAP:
  Each concept's 24-bit encoding has a syndrome (σ).
  The snap corrects to the nearest Golay codeword.
  The syndrome weight (tax) measures how "raw" the concept is.
  Low tax = close to lawful. High tax = needs interpretation.

GROWTH STRATEGY:
  1. Add more domains (speed, time, energy, angle, area, volume)
  2. Each domain: define reference, vector, concepts, key operations
  3. Test: do the vector operations produce semantically correct results?
  4. Cross-domain: let the cosine tell us which domains interact
  5. The body state stores concepts + their relations (computed vectors)
  6. The system grows by adding concepts, not by adding systems
