/*
 * Hot loops for lplab: quadgram scoring and periodic-key hill climbing over Z/29.
 *
 * Decryption model (matches lplab.ciphers.decrypt_stream):
 *   x_i = (c_i - sign * key[slot_i]) mod 29 ; p_i = (a * x_i + b) mod 29
 *   slot_i = -1 for interrupter positions (p_i = c_i, key does not advance).
 * Compiled at first use by lplab.kernels with: cc -O3 -fPIC -shared.
 */
#include <stdint.h>
#include <string.h>
#include <stdlib.h>

#define NR 29

static inline int mod29(int v) { v %= NR; return v < 0 ? v + NR : v; }

double lp_quad_score(const uint8_t *t, int64_t n, const float *quad) {
    if (n < 4) return -1e30;
    double s = 0.0;
    for (int64_t i = 0; i + 3 < n; i++) {
        int64_t q = (((int64_t)t[i] * NR + t[i + 1]) * NR + t[i + 2]) * NR + t[i + 3];
        s += quad[q];
    }
    return s / (double)(n - 3);
}

static inline uint64_t xorshift64(uint64_t *state) {
    uint64_t x = *state;
    x ^= x << 13; x ^= x >> 7; x ^= x << 17;
    *state = x;
    return x;
}

static void decrypt_into(const uint8_t *ct, const int32_t *slot, int64_t n, const uint8_t *key,
                         int sign, int a, int b, uint8_t *out) {
    for (int64_t i = 0; i < n; i++) {
        if (slot[i] < 0) { out[i] = ct[i]; continue; }
        int x = mod29((int)ct[i] - sign * (int)key[slot[i]]);
        out[i] = (uint8_t)mod29(a * x + b);
    }
}

/* Re-decrypt only the positions that use key slot k (value v). */
static void set_slot(const uint8_t *ct, const int32_t *slot, int64_t n, int k, int v, int sign,
                     int a, int b, uint8_t *pt) {
    for (int64_t i = 0; i < n; i++)
        if (slot[i] == k) pt[i] = (uint8_t)mod29(a * mod29((int)ct[i] - sign * v) + b);
}

/*
 * Coordinate-ascent hill climb with random restarts. For each key slot, try all 29 values and
 * keep the best; repeat until a sweep makes no improvement (max `sweeps`). Returns the best
 * mean quadgram score and writes the key to best_key[period].
 */
double lp_climb_periodic(const uint8_t *ct, int64_t n, const uint8_t *skip, int period,
                         int sign, int a, int b, const float *quad, int restarts, int sweeps,
                         uint64_t seed, uint8_t *best_key) {
    if (period <= 0 || n < 4) return -1e30;
    int32_t *slot = (int32_t *)malloc(sizeof(int32_t) * (size_t)n);
    uint8_t *pt = (uint8_t *)malloc((size_t)n);
    uint8_t *key = (uint8_t *)malloc((size_t)period);
    if (!slot || !pt || !key) { free(slot); free(pt); free(key); return -1e30; }
    int64_t live = 0;
    for (int64_t i = 0; i < n; i++) slot[i] = skip[i] ? -1 : (int32_t)(live++ % period);

    uint64_t state = seed ? seed : 0x9E3779B97F4A7C15ULL;
    double best = -1e30;
    for (int r = 0; r < restarts; r++) {
        for (int k = 0; k < period; k++) key[k] = (uint8_t)(xorshift64(&state) % NR);
        decrypt_into(ct, slot, n, key, sign, a, b, pt);
        double cur = lp_quad_score(pt, n, quad);
        for (int sw = 0; sw < sweeps; sw++) {
            int improved = 0;
            for (int k = 0; k < period; k++) {
                uint8_t keep = key[k];
                for (int v = 0; v < NR; v++) {
                    if (v == keep) continue;
                    set_slot(ct, slot, n, k, v, sign, a, b, pt);
                    double s = lp_quad_score(pt, n, quad);
                    if (s > cur) { cur = s; keep = (uint8_t)v; improved = 1; }
                }
                key[k] = keep;
                set_slot(ct, slot, n, k, keep, sign, a, b, pt);
            }
            if (!improved) break;
        }
        if (cur > best) { best = cur; memcpy(best_key, key, (size_t)period); }
    }
    free(slot); free(pt); free(key);
    return best;
}
