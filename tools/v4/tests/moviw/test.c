/* moviw: MOVIW.L sign-extends its word to a long, to a register and to
 * memory, and sets N and Z (core/cpu-68080/prm/integer/moviw.md).
 * Open question it answers: does MOVIW.L run on the current core? */
#include "../akbtest.h"

unsigned long moviw_reg(void);
void moviw_mem(unsigned long *p);
unsigned long moviw_ccr(void);

int main(void)
{
    unsigned long m = 0x55555555, f;
    int pass;

    AKB_BEGIN("moviw");
    akb_machine();
    for (pass = 0; pass < 5; pass++) {          /* cold and trained passes */
        unsigned long r = moviw_reg();
        AKB_CHECK("register", r == 0xFFFF8123, "got $%08lX, want $FFFF8123", r);
        m = 0x55555555;
        moviw_mem(&m);
        AKB_CHECK("memory", m == 0xFFFF8123, "got $%08lX, want $FFFF8123", m);
        f = moviw_ccr();
        /* CCR bits: N = 8, Z = 4, V = 2, C = 1; X (16) is unchanged. */
        AKB_CHECK("flags-negative", ((f >> 16) & 0xF) == 0x8,
                  "NZVC %lX, want 8", (f >> 16) & 0xF);
        AKB_CHECK("flags-zero", (f & 0xF) == 0x4, "NZVC %lX, want 4", f & 0xF);
    }
    return AKB_END();
}
