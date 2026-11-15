#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <string>
#include <cmath>
#include <algorithm>
#include <gmp.h>
#include <queue>
#include <set>

#ifndef _countof
    #define _countof(a) (sizeof(a)/sizeof(*(a)))
#endif

// High-precision PI constant
mpf_t PI_CONSTANT;
bool PI_INITIALIZED = false;

void init_pi() {
    if (!PI_INITIALIZED) {
        mpf_init(PI_CONSTANT);
        // Compute PI using Machin's formula: π/4 = 4*arctan(1/5) - arctan(1/239)
        // Or use a high-precision string
        mpf_set_str(PI_CONSTANT, 
            "3.1415926535897932384626433832795028841971693993751058209749445923"
            "078164062862089986280348253421170679821480865132823066470938446095"
            "505822317253594081284811174502841027019385211055596446229489549303"
            "819644288109756659334461284756482337867831652712019091456485669234"
            "603486104543266482133936072602491412737245870066063155881748815209"
            "209628292540917153643678925903600113305305488204665213841469519415"
            "116094330572703657595919530921861173819326117931051185480744623799"
            "627495673518857527248912279381830119491298336733624406566430860213"
            "949463952247371907021798609437027705392171762931767523846748184676"
            "694051320005681271452635608277857713427577896091736371787214684409"
            "012249534301465495853710507922796892589235420199561121290219608640"
            "344181598136297747713099605187072113499999983729780499510597317328"
            "160963185950244594553469083026425223082533446850352619311881710100"
            "031378387528865875332083814206171776691473035982534904287554687311"
            "595628638823537875937519577818577805321712268066130019278766111959"
            "092164201989", 10);
        PI_INITIALIZED = true;
    }
}

// High-precision square structure
struct Square {
    int id;
    mpf_t x, y, theta;
    mpf_t c, s;  // cos and sin of theta

    Square() {
        mpf_inits(x, y, theta, c, s, NULL);
    }

    ~Square() {
        mpf_clears(x, y, theta, c, s, NULL);
    }

    Square(const Square& other) {
        mpf_inits(x, y, theta, c, s, NULL);

        mpf_set(x, other.x);
        mpf_set(y, other.y);
        mpf_set(theta, other.theta);
        mpf_set(c, other.c);
        mpf_set(s, other.s);
        id = other.id;
    }

    Square& operator=(const Square& other) {
        if (this != &other) {
            mpf_set(x, other.x);
            mpf_set(y, other.y);
            mpf_set(theta, other.theta);
            mpf_set(c, other.c);
            mpf_set(s, other.s);
            id = other.id;
        }
        return *this;
    }
};

// Compute high-precision sin and cos using Taylor series
void compute_sin_cos(mpf_t result_sin, mpf_t result_cos, const mpf_t angle, const mpf_t epsilon) {
    mpf_t x, term_sin, term_cos, x_squared;
    mpf_t temp1, temp2;

    mpf_inits(x, term_sin, term_cos, x_squared, temp1, temp2, NULL);

    // Reduce angle to [0, 2π)
    mpf_t two_pi;
    mpf_init(two_pi);
    mpf_set_d(two_pi, 2.0);
    mpf_mul(two_pi, two_pi, PI_CONSTANT);

    mpf_set(x, angle);
    // x = x mod 2π (simple reduction)
    while (mpf_cmp(x, two_pi) >= 0) {
        mpf_sub(x, x, two_pi);
    }
    while (mpf_cmp_d(x, 0) < 0) {
        mpf_add(x, x, two_pi);
    }

    mpf_mul(x_squared, x, x);

    // Compute cos using Taylor series: 1 - x²/2! + x⁴/4! - ...
    mpf_set_d(result_cos, 1.0);
    mpf_set_d(term_cos, 1.0);

    for (int n = 1; n <= 500; n++) {
        // term *= -x² / ((2n)(2n-1))
        mpf_neg(term_cos, term_cos);
        mpf_mul(term_cos, term_cos, x_squared);
        mpf_set_d(temp1, 2.0 * n);
        mpf_set_d(temp2, 2.0 * n - 1);
        mpf_mul(temp1, temp1, temp2);
        mpf_div(term_cos, term_cos, temp1);

        mpf_add(result_cos, result_cos, term_cos);

        // Check convergence
        mpf_abs(temp1, term_cos);
        if (mpf_cmp(temp1, epsilon) < 0) break;
    }

    // Compute sin using Taylor series: x - x³/3! + x⁵/5! - ...
    mpf_set(result_sin, x);
    mpf_set(term_sin, x);

    for (int n = 1; n <= 500; n++) {
        // term *= -x² / ((2n+1)(2n))
        mpf_neg(term_sin, term_sin);
        mpf_mul(term_sin, term_sin, x_squared);
        mpf_set_d(temp1, 2.0 * n + 1);
        mpf_set_d(temp2, 2.0 * n);
        mpf_mul(temp1, temp1, temp2);
        mpf_div(term_sin, term_sin, temp1);

        mpf_add(result_sin, result_sin, term_sin);

        // Check convergence
        mpf_abs(temp1, term_sin);
        if (mpf_cmp(temp1, epsilon) < 0) break;
    }

    mpf_clears(x, term_sin, term_cos, x_squared, temp1, temp2, two_pi, NULL);
}

// Calculate s (enclosing square size) from configuration
void calculate_s(mpf_t result, const std::vector<Square>& squares) {
    mpf_t extent, abs_c, abs_s, max_val, temp;
    mpf_t corner_x, corner_y, abs_corner;

    mpf_inits(extent, abs_c, abs_s, max_val, temp, corner_x, corner_y, abs_corner, NULL);

    mpf_set_d(result, 0.0);

    for (const auto& sq : squares) {
        // extent = (|cos| + |sin|) / 2
        mpf_abs(abs_c, sq.c);
        mpf_abs(abs_s, sq.s);
        mpf_add(extent, abs_c, abs_s);
        mpf_div_ui(extent, extent, 2);

        // max_val = max(|x| + extent, |y| + extent)
        mpf_abs(abs_corner, sq.x);
        mpf_add(corner_x, abs_corner, extent);

        mpf_abs(abs_corner, sq.y);
        mpf_add(corner_y, abs_corner, extent);

        mpf_set(max_val, corner_x);
        if (mpf_cmp(corner_y, max_val) > 0) {
            mpf_set(max_val, corner_y);
        }

        // s = max(s, 2 * max_val)
        mpf_mul_ui(temp, max_val, 2);
        if (mpf_cmp(temp, result) > 0) {
            mpf_set(result, temp);
        }
    }

    mpf_clears(extent, abs_c, abs_s, max_val, temp, corner_x, corner_y, abs_corner, NULL);
}

// Check if two squares overlap using SAT (from original refine_packing)
bool check_overlap(const Square& a, const Square& b, mpf_t epsilon, mpf_t min_overlap) {
    mpf_t ax1[2], ax2[2];  // Axes for a and b
    mpf_t corners_a[4][2], corners_b[4][2];  // 4 corners, each with x,y
    mpf_t half, temp, temp2;

    mpf_inits(half, temp, temp2, NULL);
    mpf_set_d(half, 0.5);

    for (int i = 0; i < 2; i++) {
        mpf_init(ax1[i]);
        mpf_init(ax2[i]);
    }
    for (int i = 0; i < 4; i++) {
        mpf_inits(corners_a[i][0], corners_a[i][1], corners_b[i][0], corners_b[i][1], NULL);
    }

    mpf_set_ui(min_overlap, 1000000);

    // Axes for SAT test
    mpf_set(ax1[0], a.c);
    mpf_set(ax1[1], a.s);
    mpf_neg(ax2[0], a.s);
    mpf_set(ax2[1], a.c);

    // Compute corners of square a
    int corner_idx = 0;
    for (int dx_sign = -1; dx_sign <= 1; dx_sign += 2) {
        for (int dy_sign = -1; dy_sign <= 1; dy_sign += 2) {
            mpf_t dx, dy, rx, ry;
            mpf_inits(dx, dy, rx, ry, NULL);

            mpf_set_d(dx, dx_sign * 0.5);
            mpf_set_d(dy, dy_sign * 0.5);

            // rx = dx * cos - dy * sin
            mpf_mul(temp, dx, a.c);
            mpf_mul(temp2, dy, a.s);
            mpf_sub(rx, temp, temp2);

            // ry = dx * sin + dy * cos
            mpf_mul(temp, dx, a.s);
            mpf_mul(temp2, dy, a.c);
            mpf_add(ry, temp, temp2);

            mpf_add(corners_a[corner_idx][0], a.x, rx);
            mpf_add(corners_a[corner_idx][1], a.y, ry);

            corner_idx++;
            mpf_clears(dx, dy, rx, ry, NULL);
        }
    }

    // Compute corners of square b
    corner_idx = 0;
    for (int dx_sign = -1; dx_sign <= 1; dx_sign += 2) {
        for (int dy_sign = -1; dy_sign <= 1; dy_sign += 2) {
            mpf_t dx, dy, rx, ry;
            mpf_inits(dx, dy, rx, ry, NULL);

            mpf_set_d(dx, dx_sign * 0.5);
            mpf_set_d(dy, dy_sign * 0.5);

            mpf_mul(temp, dx, b.c);
            mpf_mul(temp2, dy, b.s);
            mpf_sub(rx, temp, temp2);

            mpf_mul(temp, dx, b.s);
            mpf_mul(temp2, dy, b.c);
            mpf_add(ry, temp, temp2);

            mpf_add(corners_b[corner_idx][0], b.x, rx);
            mpf_add(corners_b[corner_idx][1], b.y, ry);

            corner_idx++;
            mpf_clears(dx, dy, rx, ry, NULL);
        }
    }

    // Test axes from square a
    for (int axis_idx = 0; axis_idx < 2; axis_idx++) {
        mpf_t* axis = (axis_idx == 0) ? ax1 : ax2;
        mpf_t min_a, max_a, min_b, max_b, proj;
        mpf_inits(min_a, max_a, min_b, max_b, proj, NULL);

        // Project corners of a onto axis
        for (int i = 0; i < 4; i++) {
            mpf_mul(temp, corners_a[i][0], axis[0]);
            mpf_mul(temp2, corners_a[i][1], axis[1]);
            mpf_add(proj, temp, temp2);

            if (i == 0 || mpf_cmp(proj, min_a) < 0) mpf_set(min_a, proj);
            if (i == 0 || mpf_cmp(proj, max_a) > 0) mpf_set(max_a, proj);
        }

        // Project corners of b onto axis
        for (int i = 0; i < 4; i++) {
            mpf_mul(temp, corners_b[i][0], axis[0]);
            mpf_mul(temp2, corners_b[i][1], axis[1]);
            mpf_add(proj, temp, temp2);

            if (i == 0 || mpf_cmp(proj, min_b) < 0) mpf_set(min_b, proj);
            if (i == 0 || mpf_cmp(proj, max_b) > 0) mpf_set(max_b, proj);
        }

        // Check for separation
        mpf_add(temp, min_a, epsilon);
        //gmp_printf("max_a = %.100Fe, max_a+E = %.100Fe, min_b = %.100Fe\n", max_a, temp, min_b);
        if (mpf_cmp(temp, max_b) > 0) {
            // Separated
            mpf_clears(min_a, max_a, min_b, max_b, proj, NULL);
            goto cleanup_and_return_false;
        }
        mpf_add(temp, min_b, epsilon);
        //gmp_printf("max_b = %.100Fe, max_b+E = %.100Fe, min_a = %.100Fe\n", max_b, temp, min_a);
        if (mpf_cmp(temp, max_a) > 0) {
            // Separated
            mpf_clears(min_a, max_a, min_b, max_b, proj, NULL);
            goto cleanup_and_return_false;
        }
        {
            mpf_t *min_max = mpf_cmp(max_a, max_b) < 0 ? &max_a : &max_b;
            mpf_t *max_min = mpf_cmp(min_a, min_b) > 0 ? &min_a : &min_b;
            mpf_sub(temp, *min_max, *max_min);
            if (mpf_cmp(min_overlap, temp) > 0)
                mpf_set(min_overlap, temp);
        }

        mpf_clears(min_a, max_a, min_b, max_b, proj, NULL);
    }

    // Test axes from square b
    mpf_t bx1[2], bx2[2];
    mpf_inits(bx1[0], bx1[1], bx2[0], bx2[1], NULL);
    mpf_set(bx1[0], b.c);
    mpf_set(bx1[1], b.s);
    mpf_neg(bx2[0], b.s);
    mpf_set(bx2[1], b.c);

    for (int axis_idx = 0; axis_idx < 2; axis_idx++) {
        mpf_t* axis = (axis_idx == 0) ? bx1 : bx2;
        mpf_t min_a, max_a, min_b, max_b, proj;
        mpf_inits(min_a, max_a, min_b, max_b, proj, NULL);

        for (int i = 0; i < 4; i++) {
            mpf_mul(temp, corners_a[i][0], axis[0]);
            mpf_mul(temp2, corners_a[i][1], axis[1]);
            mpf_add(proj, temp, temp2);

            if (i == 0 || mpf_cmp(proj, min_a) < 0) mpf_set(min_a, proj);
            if (i == 0 || mpf_cmp(proj, max_a) > 0) mpf_set(max_a, proj);
        }

        for (int i = 0; i < 4; i++) {
            mpf_mul(temp, corners_b[i][0], axis[0]);
            mpf_mul(temp2, corners_b[i][1], axis[1]);
            mpf_add(proj, temp, temp2);

            if (i == 0 || mpf_cmp(proj, min_b) < 0) mpf_set(min_b, proj);
            if (i == 0 || mpf_cmp(proj, max_b) > 0) mpf_set(max_b, proj);
        }

        mpf_add(temp, min_a, epsilon);
        if (mpf_cmp(temp, max_b) > 0) {
            mpf_clears(min_a, max_a, min_b, max_b, proj, bx1[0], bx1[1], bx2[0], bx2[1], NULL);
            goto cleanup_and_return_false;
        }
        mpf_add(temp, min_b, epsilon);
        if (mpf_cmp(temp, max_a) > 0) {
            mpf_clears(min_a, max_a, min_b, max_b, proj, bx1[0], bx1[1], bx2[0], bx2[1], NULL);
            goto cleanup_and_return_false;
        }
        {
            mpf_t *min_max = mpf_cmp(max_a, max_b) < 0 ? &max_a : &max_b;
            mpf_t *max_min = mpf_cmp(min_a, min_b) > 0 ? &min_a : &min_b;
            mpf_sub(temp, *min_max, *max_min);
            if (mpf_cmp(min_overlap, temp) > 0)
                mpf_set(min_overlap, temp);
        }

        mpf_clears(min_a, max_a, min_b, max_b, proj, NULL);
    }

    mpf_clears(bx1[0], bx1[1], bx2[0], bx2[1], NULL);

    // Overlapping
    mpf_clears(half, temp, temp2, NULL);
    for (int i = 0; i < 2; i++) {
        mpf_clear(ax1[i]);
        mpf_clear(ax2[i]);
    }
    for (int i = 0; i < 4; i++) {
        mpf_clears(corners_a[i][0], corners_a[i][1], corners_b[i][0], corners_b[i][1], NULL);
    }
    return true;

cleanup_and_return_false:
    mpf_clears(half, temp, temp2, NULL);
    for (int i = 0; i < 2; i++) {
        mpf_clear(ax1[i]);
        mpf_clear(ax2[i]);
    }
    for (int i = 0; i < 4; i++) {
        mpf_clears(corners_a[i][0], corners_a[i][1], corners_b[i][0], corners_b[i][1], NULL);
    }
    return false;
}

// Get minimum separation vector using SAT
// Returns true if overlapping, and fills in depth and direction
bool get_separation_info(const Square& a, const Square& b, mpf_t epsilon, 
                         mpf_t& sep_depth, mpf_t& sep_dir_x, mpf_t& sep_dir_y) {
    mpf_t ax1[2], ax2[2];
    mpf_t corners_a[4][2], corners_b[4][2];
    mpf_t half, temp, temp2;

    mpf_inits(half, temp, temp2, NULL);
    mpf_set_d(half, 0.5);

    for (int i = 0; i < 2; i++) {
        mpf_init(ax1[i]);
        mpf_init(ax2[i]);
    }
    for (int i = 0; i < 4; i++) {
        mpf_inits(corners_a[i][0], corners_a[i][1], corners_b[i][0], corners_b[i][1], NULL);
    }

    // Axes for SAT test
    mpf_set(ax1[0], a.c);
    mpf_set(ax1[1], a.s);
    mpf_neg(ax2[0], a.s);
    mpf_set(ax2[1], a.c);

    // Compute corners of square a
    int corner_idx = 0;
    for (int dx_sign = -1; dx_sign <= 1; dx_sign += 2) {
        for (int dy_sign = -1; dy_sign <= 1; dy_sign += 2) {
            mpf_t dx, dy, rx, ry;
            mpf_inits(dx, dy, rx, ry, NULL);

            mpf_set_d(dx, dx_sign * 0.5);
            mpf_set_d(dy, dy_sign * 0.5);

            mpf_mul(temp, dx, a.c);
            mpf_mul(temp2, dy, a.s);
            mpf_sub(rx, temp, temp2);

            mpf_mul(temp, dx, a.s);
            mpf_mul(temp2, dy, a.c);
            mpf_add(ry, temp, temp2);

            mpf_add(corners_a[corner_idx][0], a.x, rx);
            mpf_add(corners_a[corner_idx][1], a.y, ry);

            corner_idx++;
            mpf_clears(dx, dy, rx, ry, NULL);
        }
    }

    // Compute corners of square b
    corner_idx = 0;
    for (int dx_sign = -1; dx_sign <= 1; dx_sign += 2) {
        for (int dy_sign = -1; dy_sign <= 1; dy_sign += 2) {
            mpf_t dx, dy, rx, ry;
            mpf_inits(dx, dy, rx, ry, NULL);

            mpf_set_d(dx, dx_sign * 0.5);
            mpf_set_d(dy, dy_sign * 0.5);

            mpf_mul(temp, dx, b.c);
            mpf_mul(temp2, dy, b.s);
            mpf_sub(rx, temp, temp2);

            mpf_mul(temp, dx, b.s);
            mpf_mul(temp2, dy, b.c);
            mpf_add(ry, temp, temp2);

            mpf_add(corners_b[corner_idx][0], b.x, rx);
            mpf_add(corners_b[corner_idx][1], b.y, ry);

            corner_idx++;
            mpf_clears(dx, dy, rx, ry, NULL);
        }
    }

    // Track minimum overlap and corresponding axis
    mpf_t min_overlap, min_axis_x, min_axis_y;
    mpf_inits(min_overlap, min_axis_x, min_axis_y, NULL);
    mpf_set_d(min_overlap, 1e100);  // Large value
    bool is_overlapping = true;

    // Test axes from square a
    for (int axis_idx = 0; axis_idx < 2; axis_idx++) {
        mpf_t* axis = (axis_idx == 0) ? ax1 : ax2;
        mpf_t min_a, max_a, min_b, max_b, proj, overlap;
        mpf_inits(min_a, max_a, min_b, max_b, proj, overlap, NULL);

        // Project corners of a onto axis
        for (int i = 0; i < 4; i++) {
            mpf_mul(temp, corners_a[i][0], axis[0]);
            mpf_mul(temp2, corners_a[i][1], axis[1]);
            mpf_add(proj, temp, temp2);

            if (i == 0 || mpf_cmp(proj, min_a) < 0) mpf_set(min_a, proj);
            if (i == 0 || mpf_cmp(proj, max_a) > 0) mpf_set(max_a, proj);
        }

        // Project corners of b onto axis
        for (int i = 0; i < 4; i++) {
            mpf_mul(temp, corners_b[i][0], axis[0]);
            mpf_mul(temp2, corners_b[i][1], axis[1]);
            mpf_add(proj, temp, temp2);

            if (i == 0 || mpf_cmp(proj, min_b) < 0) mpf_set(min_b, proj);
            if (i == 0 || mpf_cmp(proj, max_b) > 0) mpf_set(max_b, proj);
        }

        // Check for separation
        mpf_add(temp, max_a, epsilon);
        if (mpf_cmp(temp, min_b) < 0) {
            is_overlapping = false;
            mpf_clears(min_a, max_a, min_b, max_b, proj, overlap, NULL);
            break;
        }
        mpf_add(temp, max_b, epsilon);
        if (mpf_cmp(temp, min_a) < 0) {
            is_overlapping = false;
            mpf_clears(min_a, max_a, min_b, max_b, proj, overlap, NULL);
            break;
        }

        // Calculate overlap: min(max_a, max_b) - max(min_a, min_b)
        if (mpf_cmp(max_a, max_b) < 0) {
            mpf_set(temp, max_a);
        } else {
            mpf_set(temp, max_b);
        }
        if (mpf_cmp(min_a, min_b) > 0) {
            mpf_set(temp2, min_a);
        } else {
            mpf_set(temp2, min_b);
        }
        mpf_sub(overlap, temp, temp2);

        // Track minimum
        if (mpf_cmp(overlap, min_overlap) < 0) {
            mpf_set(min_overlap, overlap);
            mpf_set(min_axis_x, axis[0]);
            mpf_set(min_axis_y, axis[1]);
        }

        mpf_clears(min_a, max_a, min_b, max_b, proj, overlap, NULL);
    }

    if (!is_overlapping) {
        // Cleanup and return
        mpf_clears(half, temp, temp2, NULL);
        for (int i = 0; i < 2; i++) {
            mpf_clear(ax1[i]); mpf_clear(ax2[i]);
        }
        for (int i = 0; i < 4; i++) {
            mpf_clears(corners_a[i][0], corners_a[i][1], corners_b[i][0], corners_b[i][1], NULL);
        }
        mpf_clears(min_overlap, min_axis_x, min_axis_y, NULL);
        return false;
    }

    // Test axes from square b
    mpf_t bx1[2], bx2[2];
    mpf_inits(bx1[0], bx1[1], bx2[0], bx2[1], NULL);
    mpf_set(bx1[0], b.c);
    mpf_set(bx1[1], b.s);
    mpf_neg(bx2[0], b.s);
    mpf_set(bx2[1], b.c);

    for (int axis_idx = 0; axis_idx < 2; axis_idx++) {
        mpf_t* axis = (axis_idx == 0) ? bx1 : bx2;
        mpf_t min_a, max_a, min_b, max_b, proj, overlap;
        mpf_inits(min_a, max_a, min_b, max_b, proj, overlap, NULL);

        for (int i = 0; i < 4; i++) {
            mpf_mul(temp, corners_a[i][0], axis[0]);
            mpf_mul(temp2, corners_a[i][1], axis[1]);
            mpf_add(proj, temp, temp2);

            if (i == 0 || mpf_cmp(proj, min_a) < 0) mpf_set(min_a, proj);
            if (i == 0 || mpf_cmp(proj, max_a) > 0) mpf_set(max_a, proj);
        }

        for (int i = 0; i < 4; i++) {
            mpf_mul(temp, corners_b[i][0], axis[0]);
            mpf_mul(temp2, corners_b[i][1], axis[1]);
            mpf_add(proj, temp, temp2);

            if (i == 0 || mpf_cmp(proj, min_b) < 0) mpf_set(min_b, proj);
            if (i == 0 || mpf_cmp(proj, max_b) > 0) mpf_set(max_b, proj);
        }

        mpf_add(temp, max_a, epsilon);
        if (mpf_cmp(temp, min_b) < 0) {
            is_overlapping = false;
            mpf_clears(min_a, max_a, min_b, max_b, proj, overlap, NULL);
            break;
        }
        mpf_add(temp, max_b, epsilon);
        if (mpf_cmp(temp, min_a) < 0) {
            is_overlapping = false;
            mpf_clears(min_a, max_a, min_b, max_b, proj, overlap, NULL);
            break;
        }

        // Calculate overlap
        if (mpf_cmp(max_a, max_b) < 0) {
            mpf_set(temp, max_a);
        } else {
            mpf_set(temp, max_b);
        }
        if (mpf_cmp(min_a, min_b) > 0) {
            mpf_set(temp2, min_a);
        } else {
            mpf_set(temp2, min_b);
        }
        mpf_sub(overlap, temp, temp2);

        if (mpf_cmp(overlap, min_overlap) < 0) {
            mpf_set(min_overlap, overlap);
            mpf_set(min_axis_x, axis[0]);
            mpf_set(min_axis_y, axis[1]);
        }

        mpf_clears(min_a, max_a, min_b, max_b, proj, overlap, NULL);
    }

    mpf_clears(bx1[0], bx1[1], bx2[0], bx2[1], NULL);

    if (!is_overlapping) {
        mpf_clears(half, temp, temp2, NULL);
        for (int i = 0; i < 2; i++) {
            mpf_clear(ax1[i]); mpf_clear(ax2[i]);
        }
        for (int i = 0; i < 4; i++) {
            mpf_clears(corners_a[i][0], corners_a[i][1], corners_b[i][0], corners_b[i][1], NULL);
        }
        mpf_clears(min_overlap, min_axis_x, min_axis_y, NULL);
        return false;
    }

    // Set output values
    mpf_set(sep_depth, min_overlap);

    // Ensure axis points from a to b
    mpf_t vec_x, vec_y, dot;
    mpf_inits(vec_x, vec_y, dot, NULL);

    mpf_sub(vec_x, b.x, a.x);
    mpf_sub(vec_y, b.y, a.y);

    mpf_mul(temp, vec_x, min_axis_x);
    mpf_mul(temp2, vec_y, min_axis_y);
    mpf_add(dot, temp, temp2);

    if (mpf_cmp_d(dot, 0) < 0) {
        mpf_neg(min_axis_x, min_axis_x);
        mpf_neg(min_axis_y, min_axis_y);
    }

    mpf_set(sep_dir_x, min_axis_x);
    mpf_set(sep_dir_y, min_axis_y);

    mpf_clears(vec_x, vec_y, dot, half, temp, temp2, NULL);
    for (int i = 0; i < 2; i++) {
        mpf_clear(ax1[i]); mpf_clear(ax2[i]);
    }
    for (int i = 0; i < 4; i++) {
        mpf_clears(corners_a[i][0], corners_a[i][1], corners_b[i][0], corners_b[i][1], NULL);
    }
    mpf_clears(min_overlap, min_axis_x, min_axis_y, NULL);

    return true;
}

// Parse input file
bool load_packing(const char* filename, std::vector<Square>& squares, int precision, mpf_t epsilon) {
    std::ifstream file(filename);
    if (!file.is_open()) {
        std::cerr << "Error: Could not open file " << filename << std::endl;
        return false;
    }

    std::string line;
    while (std::getline(file, line)) {
        // Skip empty lines and comments
        if (line.empty() || line[0] == '#') continue;

        // Parse format: "Square N: x=..., y=..., deg=..."
        if (line.find("Square") == 0) {
            Square sq;

            // Extract ID
            size_t colon_pos = line.find(':');
            std::string id_str = line.substr(7, colon_pos - 7);
            sq.id = std::stoi(id_str);

            // Extract x
            size_t x_pos = line.find("x=") + 2;
            size_t x_end = line.find(',', x_pos);
            std::string x_str = line.substr(x_pos, x_end - x_pos);
            mpf_set_str(sq.x, x_str.c_str(), 10);

            // Extract y
            size_t y_pos = line.find("y=") + 2;
            size_t y_end = line.find(',', y_pos);
            std::string y_str = line.substr(y_pos, y_end - y_pos);
            mpf_set_str(sq.y, y_str.c_str(), 10);

            // Extract theta (in degrees)
            size_t deg_pos = line.find("deg=") + 4;
            std::string deg_str = line.substr(deg_pos);
            mpf_t deg_val, deg_to_rad;
            mpf_init(deg_val);
            mpf_init(deg_to_rad);
            mpf_set_str(deg_val, deg_str.c_str(), 10);

            // Convert to radians: rad = deg * PI / 180
            mpf_mul(deg_to_rad, deg_val, PI_CONSTANT);
            mpf_div_ui(sq.theta, deg_to_rad, 180);

            mpf_clear(deg_val);
            mpf_clear(deg_to_rad);

            // Compute sin and cos
            compute_sin_cos(sq.s, sq.c, sq.theta, epsilon);

            squares.push_back(sq);
        }
    }

    file.close();
    return !squares.empty();
}

// Save packing
void save_packing(const char* filename, const std::vector<Square>& squares, const mpf_t s, int precision) {
    std::ofstream file(filename);
    if (!file.is_open()) {
        std::cerr << "Error: Could not create output file " << filename << std::endl;
        return;
    }

    // Print final s value
    char* s_str = nullptr;
    gmp_asprintf(&s_str, "%.*Ff", precision, s);
    file << "Final s: " << s_str << "\n\n";
    free(s_str);

    mpf_t rad_to_deg, deg_val;
    mpf_init(rad_to_deg);
    mpf_init(deg_val);
    mpf_set_d(rad_to_deg, 180.0);
    mpf_div(rad_to_deg, rad_to_deg, PI_CONSTANT);

    for (const auto& sq : squares) {
        char* x_str = nullptr;
        char* y_str = nullptr;
        char* deg_str = nullptr;

        gmp_asprintf(&x_str, "%.*Ff", precision, sq.x);
        gmp_asprintf(&y_str, "%.*Ff", precision, sq.y);

        mpf_mul(deg_val, sq.theta, rad_to_deg);
        gmp_asprintf(&deg_str, "%.*Ff", precision, deg_val);

        file << "Square " << sq.id << ": x=" << x_str << ", y=" << y_str << ", deg=" << deg_str << std::endl;

        free(x_str);
        free(y_str);
        free(deg_str);
    }

    mpf_clear(rad_to_deg);
    mpf_clear(deg_val);

    file.close();
}

// Shift packing by moving an 'I' strip from one edge to the opposite edge
void shift_packing(std::vector<Square>& squares, char direction) {
    /**
     * Move an 'I' strip from the specified edge to the opposite edge.
     * 
     * Algorithm:
     * 1. Bounding box is constant at ±s/2 from origin
     * 2. Shift all squares by 1 in the specified direction
     * 3. Wrap squares that went outside ±s/2 to the opposite side by ±s
     * 
     * N: Shift up, wrap squares where y > s/2 by subtracting s
     * S: Shift down, wrap squares where y < -s/2 by adding s
     * E: Shift right, wrap squares where x > s/2 by subtracting s
     * W: Shift left, wrap squares where x < -s/2 by adding s
     */

    mpf_t half_s, s_wrap, one;
    mpf_inits(half_s, s_wrap, one, NULL);

    calculate_s(s_wrap, squares);
    mpf_div_2exp(half_s, s_wrap, 1);

    mpf_t Square::*coord_ptr = (direction == 'N' || direction == 'S') ? &Square::y : &Square::x;
    int shift_dir = (direction == 'N' || direction == 'E') ? 1 : -1;

    mpf_set_si(one, shift_dir);

    if (shift_dir < 0) {
        mpf_neg(half_s, half_s);
        mpf_neg(s_wrap, s_wrap);
    }

    int wrapped_count = 0;

    for (auto& sq : squares) {
        mpf_t& coord = sq.*coord_ptr;

        // Shift by 1
        mpf_add(coord, coord, one);
        // Wrap squares that go outside bounds
        if (mpf_cmp(coord, half_s) * shift_dir > 0) {
            mpf_sub(coord, coord, s_wrap);
            wrapped_count++;
        }
    }

    std::cout << "Shifted 1 square " << direction << " and wrapped " << wrapped_count << " squares from " << direction << " edge to "
              << "ENWS"[shift_dir+1 + (coord_ptr==&Square::y ? 1 : 0)] << " edge" << std::endl;

    mpf_clears(half_s, s_wrap, one, NULL);
}

// Snap nearly-orthogonal squares to grid positions
void snap_squares_to_grid(std::vector<Square>& squares, double position_threshold, double angle_threshold_deg, const mpf_t epsilon) {
    /**
     * Snap nearly-orthogonal squares to their appropriate grid positions.
     * 
     * There are 4 possible grids (one anchored at each corner of the bounding square).
     * We determine which grid each square belongs to by following chains of neighboring
     * squares back to a corner.
     * 
     * Algorithm:
     * 1. Find bounding box and identify the 4 corners
     * 2. Build adjacency graph of touching/neighboring squares
     * 3. For each corner, do BFS to find all squares connected to that corner
     * 4. For nearly-orthogonal squares, snap to the grid of their connected corner
     */

    std::cout << "\n=== Grid Snapping ===" << std::endl;
    std::cout << "Position threshold: " << position_threshold << " units" << std::endl;
    std::cout << "Angle threshold: " << angle_threshold_deg << "°" << std::endl;

    if (squares.empty()) {
        std::cout << "No squares to snap." << std::endl;
        return;
    }

    // Step 1: Find bounding box
    mpf_t min_x, max_x, min_y, max_y;
    mpf_inits(min_x, max_x, min_y, max_y, NULL);

    mpf_set(min_x, squares[0].x);
    mpf_set(max_x, squares[0].x);
    mpf_set(min_y, squares[0].y);
    mpf_set(max_y, squares[0].y);

    for (const auto& sq : squares) {
        if (mpf_cmp(sq.x, min_x) < 0) mpf_set(min_x, sq.x);
        if (mpf_cmp(sq.x, max_x) > 0) mpf_set(max_x, sq.x);
        if (mpf_cmp(sq.y, min_y) < 0) mpf_set(min_y, sq.y);
        if (mpf_cmp(sq.y, max_y) > 0) mpf_set(max_y, sq.y);
    }

    double bounds[4] = {
        mpf_get_d(min_x), mpf_get_d(max_x),
        mpf_get_d(min_y), mpf_get_d(max_y)
    };

    std::cout << "Bounding box: [" << bounds[0] << ", " << bounds[1] << "] x [" 
              << bounds[2] << ", " << bounds[3] << "]" << std::endl;

    mpf_clears(min_x, max_x, min_y, max_y, NULL);

    // Four corners
    struct Corner {
        double x, y;
        const char* name;
    };

    Corner corners[] = {
        {bounds[0], bounds[2], "bottom-left"},
        {bounds[1], bounds[2], "bottom-right"},
        {bounds[0], bounds[3], "top-left"},/*
        {bounds[1], bounds[3], "top-right"},*/
    };

    // Step 2: Build adjacency graph
    // Two squares are neighbors if they're touching or very close (within ~1 unit)
    std::vector<std::vector<size_t>> neighbors(squares.size());
    const double neighbor_dist_threshold = 1.05; // Just over 1.0 for touching squares

    for (size_t i = 0; i < squares.size(); i++) {
        double x1 = mpf_get_d(squares[i].x);
        double y1 = mpf_get_d(squares[i].y);

        for (size_t j = i + 1; j < squares.size(); j++) {
            double x2 = mpf_get_d(squares[j].x);
            double y2 = mpf_get_d(squares[j].y);

            double dx = x2 - x1;
            double dy = y2 - y1;
            double dist = std::sqrt(dx*dx + dy*dy);

            if (dist <= neighbor_dist_threshold) {
                neighbors[i].push_back(j);
                neighbors[j].push_back(i);
            }
        }
    }

    std::cout << "Built adjacency graph" << std::endl;

    // Step 3: For each corner, find which squares connect to it via BFS
    std::vector<int> square_corner(squares.size(), -1); // Which corner each square connects to

    for (int corner_idx = 0; corner_idx < _countof(corners); corner_idx++) {
        // Find squares very close to this corner
        std::vector<size_t> corner_squares;
        const double corner_proximity = 1.0; // Squares within 1 unit of corner

        for (size_t i = 0; i < squares.size(); i++) {
            double x = mpf_get_d(squares[i].x);
            double y = mpf_get_d(squares[i].y);
            double dx = x - corners[corner_idx].x;
            double dy = y - corners[corner_idx].y;
            double dist = std::sqrt(dx*dx + dy*dy);

            if (dist <= corner_proximity) {
                corner_squares.push_back(i);
            }
        }

        if (corner_squares.empty()) continue;

        // BFS from corner squares to mark all connected squares
        std::vector<bool> visited(squares.size(), false);
        std::vector<size_t> queue = corner_squares;

        for (size_t sq : corner_squares) {
            visited[sq] = true;
            if (square_corner[sq] == -1) {
                square_corner[sq] = corner_idx;
            }
        }

        size_t queue_pos = 0;
        while (queue_pos < queue.size()) {
            size_t current = queue[queue_pos++];

            for (size_t neighbor : neighbors[current]) {
                if (!visited[neighbor]) {
                    visited[neighbor] = true;
                    queue.push_back(neighbor);
                    if (square_corner[neighbor] == -1) {
                        square_corner[neighbor] = corner_idx;
                    }
                }
            }
        }

        std::cout << "Corner " << corners[corner_idx].name << ": found " 
                  << queue.size() << " connected squares" << std::endl;
    }

    // Step 4: Snap nearly-orthogonal squares to their corner's grid
    int snapped_count = 0;
    int candidates = 0;

    for (size_t i = 0; i < squares.size(); i++) {
        // Check if nearly orthogonal
        mpf_t deg_val;
        mpf_init(deg_val);
        mpf_mul_ui(deg_val, squares[i].theta, 180);
        mpf_div(deg_val, deg_val, PI_CONSTANT);
        double angle_deg = mpf_get_d(deg_val);
        mpf_clear(deg_val);

        // Normalize to [0, 90)
        while (angle_deg < 0) angle_deg += 90;
        while (angle_deg >= 90) angle_deg -= 90;

        double dev_0 = std::abs(angle_deg);
        double dev_90 = std::abs(angle_deg - 90.0);
        double min_dev = std::min(dev_0, dev_90);

        if (min_dev > angle_threshold_deg) continue;

        candidates++;

        // Get corner this square belongs to
        int corner_idx = square_corner[i];
        if (corner_idx == -1) {
            // Not connected to any corner, skip
            continue;
        }

        // Grid is anchored at this corner
        double grid_x0 = corners[corner_idx].x;
        double grid_y0 = corners[corner_idx].y;

        double x = mpf_get_d(squares[i].x);
        double y = mpf_get_d(squares[i].y);

        // Find nearest grid point
        double offset_x = x - grid_x0;
        double offset_y = y - grid_y0;
        double snap_x = grid_x0 + std::round(offset_x);
        double snap_y = grid_y0 + std::round(offset_y);

        // Check if within position threshold
        double dx = x - snap_x;
        double dy = y - snap_y;
        double pos_error = std::sqrt(dx*dx + dy*dy);

        if (pos_error <= position_threshold) {
            // Snap position
            mpf_set_d(squares[i].x, snap_x);
            mpf_set_d(squares[i].y, snap_y);

            // Snap angle
            bool target_90 = (dev_90 < dev_0);
            if (target_90) {
                mpf_div_ui(squares[i].theta, PI_CONSTANT, 2);
            } else {
                mpf_set_d(squares[i].theta, 0.0);
            }

            compute_sin_cos(squares[i].s, squares[i].c, squares[i].theta, epsilon);
            snapped_count++;
        }
    }

    std::cout << "Candidates: " << candidates << ", Snapped: " << snapped_count << std::endl;
    std::cout << "======================\n" << std::endl;
}

void save_svg(const char* filename, const std::vector<Square>& squares, const mpf_t final_s) {
    std::ofstream file(filename);
    if (!file.is_open()) {
        std::cerr << "Error: Could not open SVG file " << filename << std::endl;
        return;
    }

    // Convert s to double for display calculations
    double s = mpf_get_d(final_s);
    double display_size = 800.0;
    double scale = display_size / (s * 1.2);
    double offset = display_size / 2.0;

    // Calculate required height for text section
    double text_x = 820.0;
    double text_y_start = 30.0;
    double line_height = 20.0;

    int text_lines = 1;  // "Result for N=..."
    text_lines++;  // "s = ..."
    text_lines++;  // "Coordinates & Angles:" header
    text_lines += squares.size();  // One line per square

    double total_text_height = text_y_start + (text_lines * line_height) + 20.0;
    double svg_height = std::max(display_size, total_text_height);

    file << "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1200\" height=\"" << svg_height << "\" style=\"background-color: white;\">\n";

    // Draw enclosing square
    double cont_px = s * scale;
    file << "<rect x=\"" << (offset - cont_px/2.0) << "\" y=\"" << (offset - cont_px/2.0) 
         << "\" width=\"" << cont_px << "\" height=\"" << cont_px 
         << "\" fill=\"none\" stroke=\"red\" stroke-width=\"0.1\" />\n";

    // Draw squares
    for (const auto& sq : squares) {
        double x = mpf_get_d(sq.x);
        double y = mpf_get_d(sq.y);
        double theta = mpf_get_d(sq.theta);

        double cx = offset + x * scale;
        double cy = offset - y * scale;  // SVG y-axis is inverted
        double size_px = 1.0 * scale;
        double angle_deg = -theta * 180.0 / M_PI;  // Negative for SVG rotation

        file << "<rect x=\"" << (cx - size_px/2.0) << "\" y=\"" << (cy - size_px/2.0) 
             << "\" width=\"" << size_px << "\" height=\"" << size_px 
             << "\" fill=\"rgba(0,100,255,0.5)\" stroke=\"black\" stroke-width=\"0.1\" "
             << "transform=\"rotate(" << angle_deg << " " << cx << " " << cy << ")\" />\n";

        file << "<text x=\"" << cx << "\" y=\"" << cy 
             << "\" font-family=\"Arial\" font-size=\"10\" text-anchor=\"middle\" fill=\"black\">" 
             << sq.id << "</text>\n";
    }

    // Add text information
    double text_y = text_y_start;
    file << "<text x=\"" << text_x << "\" y=\"" << text_y 
         << "\" font-family=\"Courier New\" font-size=\"16\" font-weight=\"bold\">Result for N=" 
         << squares.size() << "</text>\n";
    text_y += 30.0;

    // Print s value with 10 decimal places
    char* s_str = nullptr;
    gmp_asprintf(&s_str, "%.10Ff", final_s);
    file << "<text x=\"" << text_x << "\" y=\"" << text_y 
         << "\" font-family=\"Courier New\" font-size=\"14\">s = " << s_str << "</text>\n";
    free(s_str);
    text_y += 30.0;

    file << "<text x=\"" << text_x << "\" y=\"" << text_y 
         << "\" font-family=\"Courier New\" font-size=\"12\" font-weight=\"bold\">Coordinates &amp; Angles:</text>\n";
    text_y += line_height;

    // Print coordinates for each square (10 decimal places)
    for (const auto& sq : squares) {
        mpf_t deg_val;
        mpf_init(deg_val);

        // Convert radians to degrees
        mpf_mul_ui(deg_val, sq.theta, 180);
        mpf_div(deg_val, deg_val, PI_CONSTANT);

        char* x_str = nullptr;
        char* y_str = nullptr;
        char* deg_str = nullptr;

        gmp_asprintf(&x_str, "%.10Ff", sq.x);
        gmp_asprintf(&y_str, "%.10Ff", sq.y);
        gmp_asprintf(&deg_str, "%.10Ff", deg_val);

        file << "<text x=\"" << text_x << "\" y=\"" << text_y 
             << "\" font-family=\"Courier New\" font-size=\"12\">"
             << "Square " << sq.id << ": x=" << x_str << ", y=" << y_str << ", deg=" << deg_str 
             << "</text>\n";

        text_y += line_height;

        free(x_str);
        free(y_str);
        free(deg_str);

        mpf_clear(deg_val);
    }

    file << "</svg>\n";
}

void save_svg_raw(const char* filename, const std::vector<Square>& squares, const mpf_t s_value, int precision) {
    /**
     * Save SVG in "raw" format matching David Ellsworth's website style.
     * This format uses entity definitions and simple transforms with exact numbers.
     */
    std::ofstream file(filename);
    if (!file) {
        std::cerr << "Error: Could not open " << filename << " for writing" << std::endl;
        return;
    }

    // Get s as string with full precision
    char* s_str;
    gmp_asprintf(&s_str, "%.*Ff", precision, s_value);
    std::string s_full(s_str);
    free(s_str);

    // Calculate s/2
    mpf_t half_s;
    mpf_init(half_s);
    mpf_div_ui(half_s, s_value, 2);
    char* hs_str;
    gmp_asprintf(&hs_str, "%.*Ff", precision, half_s);
    std::string hs_full(hs_str);
    free(hs_str);
    mpf_clear(half_s);

    // Write SVG header
    file << "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n";
    file << "<!--\n";
    file << "    Square packing for n=" << squares.size() << "\n";
    file << "-->\n";
    file << "<!DOCTYPE svg PUBLIC \"-//W3C//DTD SVG 1.1//EN\" \"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd\" [\n";
    file << "    <!ENTITY  s \"" << s_full << "\">\n";
    file << "    <!ENTITY hs \"" << hs_full << "\">\n";
    file << "]>\n";
    file << "<svg xmlns=\"http://www.w3.org/2000/svg\" xmlns:xlink=\"http://www.w3.org/1999/xlink\" width=\"100%\" height=\"100%\" viewBox=\"-&hs; -&hs; &s; &s;\" style=\"fill:#B2B2B2; stroke:black; stroke-width:0.002\" id=\"svg\">\n";
    file << "    <script xlink:href=\"svgDisp.js\"/>\n";
    file << "    <defs>\n";
    file << "        <rect width=\"&s;\" height=\"&s;\" id=\"outer\" x=\"-&hs;\" y=\"-&hs;\"/>\n";
    file << "        <rect width=\"1\"   height=\"1\"   id=\"one\"/>\n";
    file << "    </defs>\n";
    file << "    <use xlink:href=\"#outer\" style=\"fill:white; stroke:none\"/>\n";
    file << "    <g transform=\"scale(1 -1)\">\n";

    // Calculate width for formatting based on s
    // Get integer part of s to determine how many digits we need
    mpf_t s_floor;
    mpf_init(s_floor);
    mpf_floor(s_floor, s_value);
    double s_int = mpf_get_d(s_floor);
    mpf_clear(s_floor);

    int s_digits = (int)floor(log10(fabs(s_int))) + 1;

    int coord_width = s_digits + precision + 2;  // sign + digits + decimal point + precision
    int angle_width = precision + 3;  // angles can be up to 90, so +3 for digits + decimal point

    // Write each square as a <use> element with transform
    for (const auto& sq : squares) {
        // Get x, y coordinates
        char* x_str;
        gmp_asprintf(&x_str, "%*.*Ff", coord_width, precision, sq.x);

        char* y_str;
        gmp_asprintf(&y_str, "%*.*Ff", coord_width, precision, sq.y);

        // Convert theta to degrees
        mpf_t deg_val;
        mpf_init(deg_val);
        mpf_mul_ui(deg_val, sq.theta, 180);
        mpf_div(deg_val, deg_val, PI_CONSTANT);

        char* deg_str;
        gmp_asprintf(&deg_str, "%*.*Ff", angle_width, precision, deg_val);
        mpf_clear(deg_val);

        file << "        <use xlink:href=\"#one\" transform=\"translate(" 
             << x_str << " " << y_str << ") rotate(" << deg_str << ") translate(-.5 -.5)\"/>\n";

        free(x_str);
        free(y_str);
        free(deg_str);
    }

    file << "    </g>\n";
    file << "    <use xlink:href=\"#outer\" style=\"fill:none\"/>\n";
    file << "</svg>\n";
}

// Iterative nudging approach to eliminate overlaps
// Uses a cascading strategy with 3 methods
void eliminate_overlaps_by_nudging(std::vector<Square>& squares, mpf_t epsilon, int max_iterations = /*500*/5000) {
    std::cout << "Eliminating overlaps using iterative nudging..." << std::endl;

    mpf_t sep_depth, sep_dir_x, sep_dir_y;
    mpf_t displacement_x, displacement_y;
    mpf_t nudge_factor, temp, min_overlap;

    mpf_inits(sep_depth, sep_dir_x, sep_dir_y, displacement_x, displacement_y, nudge_factor, temp, min_overlap, NULL);

    // ============================================================
    // METHOD 1: Simple simultaneous processing (original approach)
    // ============================================================
    std::cout << "Method 1: Simple simultaneous nudging..." << std::endl;

    mpf_set_d(nudge_factor, 1.01);  // 1% extra
    int iteration = 0;
    int total_overlaps = 0;
    bool method1_success = false;

    while (iteration < /*max_iterations*/0) {
        // Find all overlapping pairs
        std::vector<std::pair<int, int>> overlapping_pairs;

        for (size_t i = 0; i < squares.size(); i++) {
            for (size_t j = i + 1; j < squares.size(); j++) {
                if (check_overlap(squares[i], squares[j], epsilon, min_overlap)) {
                    overlapping_pairs.push_back(std::make_pair(i, j));
                }
            }
        }

        int current_overlaps = overlapping_pairs.size();

        if (current_overlaps == 0) {
            std::cout << "  Success! No overlaps remaining after " << iteration << " iterations" << std::endl;
            method1_success = true;
            break;
        }

        if (iteration == 0) {
            total_overlaps = current_overlaps;
            std::cout << "  Initial overlaps found: " << total_overlaps << std::endl;
        }

        if (iteration % 100 == 0) {
            std::cout << "  Iteration " << iteration << ": " << current_overlaps << " overlaps" << std::endl;
        }

        // Process all overlapping pairs simultaneously
        for (const auto& pair : overlapping_pairs) {
            int i = pair.first;
            int j = pair.second;

            // Get separation vector
            if (get_separation_info(squares[i], squares[j], epsilon, 
                                     sep_depth, sep_dir_x, sep_dir_y)) {

                // Move both squares apart, splitting the movement
                mpf_mul(displacement_x, sep_dir_x, sep_depth);
                mpf_mul(displacement_x, displacement_x, nudge_factor);
                mpf_div_ui(displacement_x, displacement_x, 2);  // Half each

                mpf_mul(displacement_y, sep_dir_y, sep_depth);
                mpf_mul(displacement_y, displacement_y, nudge_factor);
                mpf_div_ui(displacement_y, displacement_y, 2);

                mpf_add(squares[j].x, squares[j].x, displacement_x);
                mpf_add(squares[j].y, squares[j].y, displacement_y);

                // Square i moves in negative direction
                mpf_sub(squares[i].x, squares[i].x, displacement_x);
                mpf_sub(squares[i].y, squares[i].y, displacement_y);
            }
        }

        iteration++;
    }

    if (!method1_success) {
        std::cout << "  Method 1 failed after " << iteration << " iterations" << std::endl;
        std::cout << "Method 2: Adaptive batch nudging..." << std::endl;

        // ============================================================
        // METHOD 2: Adaptive batch processing with stall detection
        // ============================================================

        mpf_set_d(nudge_factor, 1.0025);  // Start conservative
        iteration = 0;
        int prev_overlaps = -1;
        int stall_count = 0;
        bool method2_success = false;

        while (iteration < max_iterations) {
            // Find all overlapping pairs
            std::vector<std::pair<int, int>> overlapping_pairs;

            for (size_t i = 0; i < squares.size(); i++) {
                for (size_t j = i + 1; j < squares.size(); j++) {
                    if (check_overlap(squares[i], squares[j], epsilon, min_overlap)) {
                        overlapping_pairs.push_back(std::make_pair(i, j));
                    }
                }
            }

            int current_overlaps = overlapping_pairs.size();

            if (current_overlaps == 0) {
                std::cout << "  Success! No overlaps remaining after " << iteration << " iterations" << std::endl;
                method2_success = true;
                break;
            }

            if (iteration % 100 == 0) {
                std::cout << "  Iteration " << iteration << ": " << current_overlaps << " overlaps";
                if (mpf_cmp_d(nudge_factor, 1.0025) > 0) {
                    std::cout << " (nudge factor: " << mpf_get_d(nudge_factor) << ")";
                }
                std::cout << std::endl;
            }

            // Check if we're stuck in oscillation
            if (current_overlaps == prev_overlaps) {
                stall_count++;
                if (stall_count >= 50) {
                    mpf_t increase;
                    mpf_init(increase);
                    mpf_set_d(increase, 1.0025);
                    mpf_mul(nudge_factor, nudge_factor, increase);
                    mpf_clear(increase);
                    if (iteration % 100 == 0 || stall_count == 50) {
                        std::cout << "  [Stalled, increasing nudge factor to " << mpf_get_d(nudge_factor) << "]" << std::endl;
                    }
                }
                if (stall_count >= 500 && stall_count % 100 == 0) {
                    std::cout << "  [Very stuck - trying aggressive mode]" << std::endl;
                }
            } else if (current_overlaps < prev_overlaps) {
                stall_count = 0;
                if (mpf_cmp_d(nudge_factor, 1.0025) > 0) {
                    mpf_set_d(nudge_factor, 1.0025);
                }
            }/* else {
                stall_count += 5;
                mpf_t increase;
                mpf_init(increase);
                mpf_set_d(increase, 1.01);
                mpf_mul(nudge_factor, nudge_factor, increase);
                mpf_clear(increase);
            }*/

            prev_overlaps = current_overlaps;
            bool use_aggressive = (stall_count >= 500);

            // Process overlaps in batches
            std::vector<bool> square_used(squares.size(), false);

            for (const auto& pair : overlapping_pairs) {
                int i = pair.first;
                int j = pair.second;

                if (!use_aggressive && (square_used[i] || square_used[j])) {
                    continue;
                }

                if (get_separation_info(squares[i], squares[j], epsilon, 
                                         sep_depth, sep_dir_x, sep_dir_y)) {

                    mpf_mul(displacement_x, sep_dir_x, sep_depth);
                    mpf_mul(displacement_x, displacement_x, nudge_factor);
                    mpf_div_ui(displacement_x, displacement_x, 2);

                    mpf_mul(displacement_y, sep_dir_y, sep_depth);
                    mpf_mul(displacement_y, displacement_y, nudge_factor);
                    mpf_div_ui(displacement_y, displacement_y, 2);

                    mpf_add(squares[j].x, squares[j].x, displacement_x);
                    mpf_add(squares[j].y, squares[j].y, displacement_y);

                    mpf_sub(squares[i].x, squares[i].x, displacement_x);
                    mpf_sub(squares[i].y, squares[i].y, displacement_y);

                    square_used[i] = true;
                    square_used[j] = true;
                }
            }

            iteration++;
        }

        if (!method2_success) {
            std::cout << "  Method 2 failed after " << iteration << " iterations" << std::endl;
            std::cout << "Method 3: Uniform scaling fallback..." << std::endl;

            // ============================================================
            // METHOD 3: Uniform scaling with binary search (last resort)
            // ============================================================

            mpf_t low, high, mid, test_s;
            mpf_inits(low, high, mid, test_s, NULL);

            mpf_set_d(low, 1.0);
            mpf_set_d(high, 1.1);

            for (int bs_iter = 0; bs_iter < 200; bs_iter++) {
                mpf_add(mid, low, high);
                mpf_div_ui(mid, mid, 2);

                std::vector<Square> test_squares = squares;

                for (auto& sq : test_squares) {
                    mpf_mul(sq.x, sq.x, mid);
                    mpf_mul(sq.y, sq.y, mid);
                }

                bool has_overlaps = false;
                for (size_t i = 0; i < test_squares.size() && !has_overlaps; i++) {
                    for (size_t j = i + 1; j < test_squares.size(); j++) {
                        if (check_overlap(test_squares[i], test_squares[j], epsilon, min_overlap)) {
                            has_overlaps = true;
                            break;
                        }
                    }
                }

                if (has_overlaps) {
                    mpf_set(low, mid);
                } else {
                    mpf_set(high, mid);
                }

                mpf_sub(temp, high, low);
                if (mpf_cmp(temp, epsilon) < 0) {
                    break;
                }
            }

            for (auto& sq : squares) {
                mpf_mul(sq.x, sq.x, high);
                mpf_mul(sq.y, sq.y, high);
            }

            char* factor_str = nullptr;
            gmp_asprintf(&factor_str, "%.50Ff", high);
            std::cout << "  Applied uniform expansion factor: " << factor_str << std::endl;
            free(factor_str);

            mpf_clears(low, high, mid, test_s, NULL);
        }
    }

    mpf_clears(sep_depth, sep_dir_x, sep_dir_y, displacement_x, displacement_y, nudge_factor, temp, min_overlap, NULL);
}

int main(int argc, char* argv[]) {
    if (argc < 3) {
        std::cerr << "Usage: " << argv[0] << " <input.txt> <precision_digits> [output.txt] [options]" << std::endl;
        std::cerr << "Example: " << argv[0] << " squares.txt 100 squares_refined.txt" << std::endl;
        std::cerr << "         " << argv[0] << " squares.txt 100 squares_refined.txt --snap-grid 0.1 0.1" << std::endl;
        std::cerr << "         " << argv[0] << " squares.txt 100 squares_refined.txt --shift S" << std::endl;
        std::cerr << "         " << argv[0] << " squares.txt 100 squares_refined.txt --no-fix" << std::endl;
        std::cerr << "         " << argv[0] << " squares.txt 100 --check" << std::endl;
        std::cerr << std::endl;
        std::cerr << "Options:" << std::endl;
        std::cerr << "  --snap-grid <pos_thresh> <angle_thresh>" << std::endl;
        std::cerr << "                           Snap nearly-orthogonal squares to grid positions" << std::endl;
        std::cerr << "                           pos_thresh: max position deviation from grid (e.g., 0.1)" << std::endl;
        std::cerr << "                           angle_thresh: max angle deviation in degrees (e.g., 0.1)" << std::endl;
        std::cerr << "  --shift <direction>      Move 'I' strip from edge to opposite edge" << std::endl;
        std::cerr << "                           direction: N, S, E, or W" << std::endl;
        std::cerr << "  --no-fix                 Do not repair overlaps" << std::endl;
        std::cerr << "  --check                  Do not output any files; only check for overlaps" << std::endl;
        return 1;
    }

    const char* input_file = argv[1];
    int precision = std::atoi(argv[2]);
    const char* output_file = (argc >= 4 && argv[3][0] != '-') ? argv[3] : "squares_refined.txt";

    // Parse optional arguments
    bool snap_to_grid = false;
    double snap_position_threshold = 0.1; // units
    double snap_angle_threshold = 0.1;    // degrees

    bool do_shift = false;
    char shift_direction = '\0';  // N, S, E, or W

    bool no_fix = false, check_only = false;

    // Start searching from after the mandatory and optional positional args
    int start_idx = (argc >= 4 && argv[3][0] != '-') ? 4 : 3;

    for (int i = start_idx; i < argc; i++) {
        if (std::string(argv[i]) == "--snap-grid") {
            snap_to_grid = true;
            if (i + 2 < argc) {
                snap_position_threshold = std::atof(argv[i + 1]);
                snap_angle_threshold = std::atof(argv[i + 2]);
                i += 2; // Skip next two arguments
            } else {
                std::cerr << "Error: --snap-grid requires two arguments: <position_threshold> <angle_threshold>" << std::endl;
                std::cerr << "Found " << (argc - i - 1) << " argument(s) after --snap-grid" << std::endl;
                return 1;
            }
        } else if (std::string(argv[i]) == "--shift") {
            do_shift = true;
            if (i + 1 < argc) {
                std::string dir = argv[i + 1];
                if (dir == "N" || dir == "S" || dir == "E" || dir == "W") {
                    shift_direction = dir[0];
                    i++; // Skip next argument
                } else {
                    std::cerr << "Error: --shift direction must be N, S, E, or W" << std::endl;
                    return 1;
                }
            } else {
                std::cerr << "Error: --shift requires a direction argument (N, S, E, or W)" << std::endl;
                return 1;
            }
        } else if (std::string(argv[i]) == "--no-fix") {
            no_fix = true;
        } else if (std::string(argv[i]) == "--check") {
            check_only = true;
            no_fix = true;
        }
    }

    if (snap_to_grid) {
        std::cout << "Grid snapping enabled:" << std::endl;
        std::cout << "  Position threshold: " << snap_position_threshold << std::endl;
        std::cout << "  Angle threshold: " << snap_angle_threshold << std::endl;
    }

    if (do_shift) {
        std::cout << "Shift enabled: moving 'I' strip from " << shift_direction << " edge" << std::endl;
    }

    if (precision < 10) {
        std::cerr << "Error: Precision (as specified in number of decimal digits) must be at least 10" << std::endl;
        return 1;
    }

    // Set GMP precision: bits = digits * log2(10) + 50
    mp_bitcnt_t precision_bits = (mp_bitcnt_t)(precision * 3.3219280948873623478703194294893901758648313930246 + 50);
    mpf_set_default_prec(precision_bits);

    // Initialize PI constant
    init_pi();

    std::cout << (check_only ? "Checking" : "Refining") << " packing: " << input_file << std::endl;
    std::cout << "Using precision: " << precision << " decimal digits" << std::endl;

    // Set epsilon based on precision (10^-precision)
    mpf_t epsilon;
    mpf_init(epsilon);
    mpf_set_ui(epsilon, 1);
    for (int i = 0; i < precision; i++)
        mpf_div_ui(epsilon, epsilon, 10);

    // Load packing
    std::vector<Square> squares;
    if (!load_packing(input_file, squares, precision, epsilon)) {
        std::cerr << "Failed to load packing" << std::endl;
        return 1;
    }

    std::cout << "Loaded " << squares.size() << " squares" << std::endl;

    // Apply shift if requested (do this before other processing)
    if (do_shift) {
        shift_packing(squares, shift_direction);
    }

    // Apply grid snapping if requested (before checking overlaps)
    if (snap_to_grid) {
        snap_squares_to_grid(squares, snap_position_threshold, snap_angle_threshold, epsilon);
    }

    // Calculate initial s
    mpf_t current_s, min_overlap;
    mpf_inits(current_s, min_overlap, NULL);
    calculate_s(current_s, squares);

    char* initial_s_str = nullptr;
    gmp_asprintf(&initial_s_str, "%.*Ff", precision, current_s);
    std::cout << (no_fix ? "s: " : "Initial s: ") << initial_s_str << std::endl;
    free(initial_s_str);

    // Check for initial overlaps
    int overlap_count = 0;
    for (size_t i = 0; i < squares.size(); i++) {
        for (size_t j = i + 1; j < squares.size(); j++) {
            if (check_overlap(squares[i], squares[j], epsilon, min_overlap)) {
                overlap_count++;
                gmp_printf("Overlap: Squares %zd, %zd (depth = %.15Fe)\n", i+1, j+1, min_overlap);
            }
        }
    }

    std::cout << (no_fix ? "Overlap count: " : "Initial overlap count: ") << overlap_count << std::endl;

    if (!check_only) {
        if (!no_fix && overlap_count > 0) {
            // Use iterative nudging to eliminate overlaps
            eliminate_overlaps_by_nudging(squares, epsilon);
        }

        if (!no_fix) {
            // Calculate final s
            calculate_s(current_s, squares);

            char* final_s_str = nullptr;
            gmp_asprintf(&final_s_str, "%.*Ff", precision, current_s);
            std::cout << "Final s after overlap elimination: " << final_s_str << std::endl;
            free(final_s_str);

            // Verify no overlaps remain
            overlap_count = 0;
            for (size_t i = 0; i < squares.size(); i++) {
                for (size_t j = i + 1; j < squares.size(); j++) {
                    if (check_overlap(squares[i], squares[j], epsilon, min_overlap)) {
                        overlap_count++;
                    }
                }
            }

            std::cout << "Final overlap count: " << overlap_count << std::endl;
        }

        // Save result
        std::cout << "Saving refined packing to " << output_file << "..." << std::endl;
        save_packing(output_file, squares, current_s, precision);

        // Save SVG
        std::string svg_filename = std::string(output_file);
        size_t dot_pos = svg_filename.find_last_of('.');
        if (dot_pos != std::string::npos) {
            svg_filename = svg_filename.substr(0, dot_pos) + ".svg";
        } else {
            svg_filename += ".svg";
        }
        std::cout << "Saving SVG to " << svg_filename << "..." << std::endl;
        save_svg(svg_filename.c_str(), squares, current_s);

        // Save raw SVG (website format)
        std::string svg_raw_filename = std::string(output_file);
        if (dot_pos != std::string::npos) {
            svg_raw_filename = svg_raw_filename.substr(0, dot_pos) + "_raw.svg";
        } else {
            svg_raw_filename += "_raw.svg";
        }
        std::cout << "Saving raw SVG to " << svg_raw_filename << "..." << std::endl;
        save_svg_raw(svg_raw_filename.c_str(), squares, current_s, precision);

        std::cout << "Done!" << std::endl;
    }    

    mpf_clears(current_s, epsilon, min_overlap, NULL);

    return 0;
}
