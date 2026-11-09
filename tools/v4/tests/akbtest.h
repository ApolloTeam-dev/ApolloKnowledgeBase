/* akbtest.h: output helpers for AKB tests on a V4 (tools/v4/v4test.py).
 *
 * A test prints its results as text lines, which v4test.py reads back over
 * ApolloExplorer's ash:
 *
 *   AKB-TEST <name>            first line
 *   PASS <check>               a check that passed
 *   FAIL <check> <detail>      a check that failed
 *   VALUE <key> <number> <unit>  a measured value
 *   INFO <text>                anything else worth keeping
 *   AKB-DONE                   last line; missing = crash or hang
 *
 * os-friendly only: these helpers use printf. Keep timed code under
 * Disable(), and print after Enable().
 */
#ifndef AKBTEST_H
#define AKBTEST_H

#include <stdio.h>
#include <exec/execbase.h>
#include <proto/exec.h>

static int akb_failed;

#define AKB_BEGIN(name)  printf("AKB-TEST %s\n", name)
#define AKB_PASS(check)  printf("PASS %s\n", check)
#define AKB_FAIL(check, ...) \
    (akb_failed = 1, printf("FAIL %s ", check), printf(__VA_ARGS__), printf("\n"))
#define AKB_CHECK(check, cond, ...) \
    ((cond) ? (void)AKB_PASS(check) : (void)AKB_FAIL(check, __VA_ARGS__))
#define AKB_VALUE(key, num, unit)  printf("VALUE %s %lu %s\n", key, (unsigned long)(num), unit)
#define AKB_INFO(...)    (printf("INFO "), printf(__VA_ARGS__), printf("\n"))
#define AKB_END()        (printf("AKB-DONE\n"), akb_failed ? 5 : 0)

/* Clock cycle counter: movec ccc,d0 ($4E7A $0809), readable in user mode
 * on Core 12830-12841 (core/cpu-68080/performance-counters.md). */
static inline unsigned long akb_ccc(void)
{
    register unsigned long r __asm__("d0");
    __asm__ volatile (".short 0x4e7a,0x0809" : "=d" (r));
    return r;
}

/* Board ID (high byte) and CPU clock multiplier (low byte) at $DFF3FC
 * (core/saga-registers/system.md). */
static inline unsigned short akb_board_reg(void)
{
    return *(volatile unsigned short *)0xDFF3FC;
}

/* Print the machine the test ran on. */
static void akb_machine(void)
{
    unsigned short b = akb_board_reg();
    AKB_INFO("board-id $%02X clock-multiplier %u attnflags $%04X",
             b >> 8, b & 0xFF, SysBase->AttnFlags);
}

#endif
