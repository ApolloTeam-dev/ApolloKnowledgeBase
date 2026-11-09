/* add-mem-dbra: cycles per iteration of `add.l #1,counter` + dbra.
 *
 * Gunnar expects about 1 iteration per cycle (G, 2026-11-03, in
 * core/cpu-68080/caches-and-memory.md and execution-units.md); TuKo1982
 * saw a memory counter with read-modify-write serialise (M). An empty dbra
 * loop and a register loop are the baselines.
 *
 * Method (guides/benchmark-method.md): each loop is trained once, then the
 * loops are timed in rotating order, ROUNDS times, under Disable(). The
 * minimum and maximum per loop are reported in cycles per 1000 iterations. */
#include "../akbtest.h"

#define N      65536UL
#define ROUNDS 8

unsigned long loop_empty(unsigned long n);
unsigned long loop_reg(unsigned long n);
unsigned long loop_mem_abs(unsigned long n);
unsigned long loop_mem_an(unsigned long n);
extern volatile unsigned long counter;
unsigned long loop_mem_ptr(unsigned long n, volatile unsigned long *p);
extern volatile unsigned long near_0, near_64, near_128, near_256, near_1k,
    near_4k, near_16k;
static volatile unsigned long *const near[7] =
    { &near_0, &near_64, &near_128, &near_256, &near_1k, &near_4k, &near_16k };

static const char *name[4] = { "empty", "reg", "mem-abs", "mem-an" };
static unsigned long (*const fn[4])(unsigned long) =
    { loop_empty, loop_reg, loop_mem_abs, loop_mem_an };

int main(void)
{
    unsigned long lo[4], hi[4], c;
    unsigned long before, after;
    int r, i, k;
    char key[32];

    AKB_BEGIN("add-mem-dbra");
    akb_machine();
    /* The load address can change the result (guides/benchmark-method.md,
     * step 4): keep it with the numbers. */
    AKB_INFO("counter $%08lX loop_mem_abs $%08lX loop_mem_an $%08lX",
             (unsigned long)&counter, (unsigned long)loop_mem_abs,
             (unsigned long)loop_mem_an);
    for (i = 0; i < 4; i++) { lo[i] = ~0UL; hi[i] = 0; }

    counter = 0;
    Disable();
    for (i = 0; i < 4; i++)
        fn[i](N);                                   /* train */
    for (r = 0; r < ROUNDS; r++)
        for (k = 0; k < 4; k++) {
            i = (k + r) % 4;                        /* rotate the order */
            c = fn[i](N);
            if (c < lo[i]) lo[i] = c;
            if (c > hi[i]) hi[i] = c;
        }
    before = counter;
    loop_mem_abs(1000);
    loop_mem_an(1000);
    after = counter;
    Enable();

    AKB_CHECK("counter", before == 2 * N * (ROUNDS + 1),
              "counter %lu, want %lu", before, 2 * N * (ROUNDS + 1));
    AKB_CHECK("counter-short", after - before == 2000,
              "added %lu, want 2000", after - before);
    for (i = 0; i < 4; i++) {
        sprintf(key, "%s-min", name[i]);
        AKB_VALUE(key, lo[i] * 1000 / N, "cycles/1000-iterations");
        sprintf(key, "%s-max", name[i]);
        AKB_VALUE(key, hi[i] * 1000 / N, "cycles/1000-iterations");
    }

    /* The same loop with the counter at growing distances after the loop
     * code, in the code section. */
    AKB_INFO("loop_mem_ptr $%08lX", (unsigned long)loop_mem_ptr);
    for (i = 0; i < 7; i++) {
        unsigned long best = ~0UL;
        Disable();
        loop_mem_ptr(N, near[i]);                   /* train */
        for (r = 0; r < ROUNDS; r++) {
            c = loop_mem_ptr(N, near[i]);
            if (c < best) best = c;
        }
        Enable();
        sprintf(key, "near-%ld", (long)((unsigned long)near[i] - (unsigned long)loop_mem_ptr));
        AKB_VALUE(key, best * 1000 / N, "cycles/1000-iterations");
    }
    return AKB_END();
}
