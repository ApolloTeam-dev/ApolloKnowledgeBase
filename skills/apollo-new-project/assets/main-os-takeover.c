/*
  @PROJECT@ - @WHAT@

  Target: @TARGETS@
  Execution mode: os-takeover (multitasking off, direct 68080 and SAGA access,
  multitasking and the Workbench screen restored on exit)
*/

#include <dos/dos.h>
#include <exec/execbase.h>
#include <proto/exec.h>
#include "ApolloCrossDev_Lib.h"

extern struct ExecBase *SysBase;

/* ApolloKnowledgeBase os/best-practices/detect-68080-and-fpu-at-run-time.md */
static int has_68080(void) { return (SysBase->AttnFlags & (1 << 10)) != 0; }

int main(void)
{
    ApolloMouseState mouse = {0};

    if (!has_68080())
        return RETURN_FAIL;

    /* 1. Allocate memory (AllocMem) and load files (Open/Read/Close) here,
          while the OS still runs. */

    /* 2. Take over: Workbench closed and task priority 20 (ApolloTakeOver),
          then multitasking off (ApolloForbid). */
    ApolloTakeOver();
    ApolloForbid();

    /* 3. Take over the display here. ApolloKnowledgeBase os/os-takeover.md
          does not document this yet. */

    for (;;) {
        ApolloWaitVBL();
        ApolloMouse(&mouse);
        if (mouse.Button_Left)
            break;

        /* One frame of the program. */
    }

    /* 4. Restore the display here, then undo the takeover in reverse order. */
    ApolloPermit();
    ApolloRelease();

    /* 5. Free memory (FreeMem) and close files. */
    return RETURN_OK;
}
