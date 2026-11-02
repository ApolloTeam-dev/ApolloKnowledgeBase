/* Toolchain smoke test: C compiler and NDK 3.2 headers. */
#include <exec/types.h>

ULONG smoke_c(ULONG a, ULONG b)
{
    return a * b + 3;
}
