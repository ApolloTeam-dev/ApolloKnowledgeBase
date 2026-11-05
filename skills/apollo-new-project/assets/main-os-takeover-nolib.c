/*
  @PROJECT@ - @WHAT@

  Target: @TARGETS@
  Execution mode: os-takeover (multitasking off, direct 68080 and SAGA access,
  multitasking and the Workbench screen restored on exit). Without ApolloLib.
*/

#include <dos/dos.h>
#include <exec/execbase.h>
#include <proto/exec.h>

extern struct ExecBase *SysBase;

/* ApolloKnowledgeBase os/best-practices/detect-68080-and-fpu-at-run-time.md */
static int has_68080(void) { return (SysBase->AttnFlags & (1 << 10)) != 0; }

int main(void)
{
    if (!has_68080())
        return RETURN_FAIL;

    /* 1. Allocate memory (AllocMem) and load files (Open/Read/Close) here,
          while the OS still runs. */

    Forbid();                       /* multitasking off; interrupts still run */

    /* 2. Take over the display and run the program here. ApolloKnowledgeBase
          os/os-takeover.md does not document the display takeover yet. */

    /* 3. Restore the display here. */
    Permit();                       /* one Permit for every Forbid, on every exit path */

    /* 4. Free memory (FreeMem) and close files. */
    return RETURN_OK;
}
