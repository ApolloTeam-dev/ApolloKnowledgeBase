/* fpu-m68881: float code built with -m68080 -m68881 uses the FPU and gives
 * correct results; built with -m68080 alone it falls back to soft-float
 * (toolchain/pitfalls/float-settings-mismatch.md). The two variants are
 * separate programs, each linked with its own settings. libnix keeps the
 * soft-float routines (__mulsf3 and friends) in libm, so soft links -lm.
 *
 * v4:variant fpu  -O2 -m68080 -m68881 -ffast-math -fomit-frame-pointer
 * v4:variant soft -O2 -m68080 -ffast-math -fomit-frame-pointer -lm
 */
#include "../akbtest.h"

#define N 4096

static float a[N], b[N];
volatile float sink;

/* Sum of a[i] * b[i]; every product and partial sum is exact in float. */
static float dot(void)
{
    float s = 0.0f;
    int i;
    for (i = 0; i < N; i++)
        s += a[i] * b[i];
    return s;
}

int main(void)
{
    unsigned long t0, t1, best = ~0UL;
    float s = 0.0f;
    int i, r;

    AKB_BEGIN("fpu-m68881");
    akb_machine();
#ifdef __HAVE_68881__
    AKB_INFO("build: __HAVE_68881__ defined (FPU code)");
#else
    AKB_INFO("build: __HAVE_68881__ not defined (soft-float)");
#endif
    for (i = 0; i < N; i++) {
        a[i] = (float)(i & 63);
        b[i] = 0.5f;
    }
    sink = dot();                                   /* train */
    for (r = 0; r < 5; r++) {
        Disable();
        t0 = akb_ccc();
        s = dot();
        t1 = akb_ccc();
        Enable();
        sink = s;
        if (t1 - t0 < best) best = t1 - t0;
    }
    /* sum over i of (i & 63) * 0.5 = 64 blocks * 2016 * 0.5 = 64512 */
    AKB_CHECK("dot-result", s == 64512.0f, "got %ld, want 64512", (long)s);
    AKB_VALUE("dot-cycles-per-element-x100", best * 100 / N, "cycles");
    return AKB_END();
}
