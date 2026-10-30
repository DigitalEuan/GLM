/* Round 39 — fast pattern-level scan of a Rule 30 left-diagonal regime.
 *
 * Same algorithm as regime_scan.py (which reads the exact starting patterns from the automaton
 * and checks F against it); this C version only iterates F, so it can run billions of diagonals.
 *
 *   usage: ./regime_scan Q A B D_start max_steps
 *     Q          regime period (1..64, a power of two)
 *     A, B       eventual patterns (hex, bit t = phase t mod Q) of diagonals D_start, D_start+1
 *     D_start    index of the diagonal carrying pattern A
 *     max_steps  number of further diagonals to compute
 *
 * Output: the first white diagonal (pattern 0) with the parity of the diagonal outside it, or a
 * return to the start state (left side periodic in D for ever), or "none".
 * Integers and bit operations only.
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

static inline uint64_t F(uint64_t A, uint64_t B, int Q) {
    int phi = __builtin_ctzll(B);
    uint64_t x = 1 ^ ((A >> phi) & 1);
    int ph = (phi + 1) % Q;
    uint64_t C = 0;
    for (int i = 0; i < Q; i++) {
        C |= x << ph;
        x = ((A >> ph) & 1) ^ (((B >> ph) & 1) | x);
        ph = (ph + 1 == Q) ? 0 : ph + 1;
    }
    return C;
}

int main(int argc, char **argv) {
    if (argc < 6) { fprintf(stderr, "usage: Q A B D_start max_steps\n"); return 2; }
    int Q = atoi(argv[1]);
    uint64_t A = strtoull(argv[2], 0, 16), B = strtoull(argv[3], 0, 16);
    unsigned long long D = strtoull(argv[4], 0, 10) + 1, steps = strtoull(argv[5], 0, 10);
    uint64_t a0 = A, b0 = B, a = A, b = B;
    for (unsigned long long k = 1; k <= steps; k++) {
        uint64_t c = F(a, b, Q);
        a = b; b = c; D++;
        if (b == 0) {
            printf("WHITE %llu outer_parity %d outer_pattern %llx after %llu steps\n", D,
                   __builtin_popcountll(a) & 1, (unsigned long long)a, k);
            return 0;
        }
        if (a == a0 && b == b0) {
            printf("RETURN after %llu steps (left side periodic in D)\n", k);
            return 0;
        }
        if ((k & ((1ULL << 32) - 1)) == 0) { fprintf(stderr, "... %llu\n", k); fflush(stderr); }
    }
    printf("NONE up to D = %llu\n", D);
    return 0;
}
