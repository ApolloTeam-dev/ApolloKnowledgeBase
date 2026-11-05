/*
  @PROJECT@ - @WHAT@

  Target: @TARGETS@
  Execution mode: os-friendly (OS calls where available)
*/

#include <stdio.h>
#include <dos/dos.h>
#include <exec/execbase.h>
#include <proto/exec.h>

extern struct ExecBase *SysBase;

/* ApolloKnowledgeBase os/best-practices/detect-68080-and-fpu-at-run-time.md */
static int has_68080(void) { return (SysBase->AttnFlags & (1 << 10)) != 0; }
static int has_fpu(void)   { return (SysBase->AttnFlags & AFF_68881) != 0; }

int main(void)
{
    if (!has_68080()) {
        printf("@PROJECT@ needs an Apollo 68080.\n");
        return RETURN_FAIL;
    }
    printf("@PROJECT@ runs on a 68080 %s.\n", has_fpu() ? "with its FPU" : "with the FPU switched off");

    /* The program starts here. */

    return RETURN_OK;
}
