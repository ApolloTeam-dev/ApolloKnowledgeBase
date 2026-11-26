/* ide-read-stall: does a file read hold up tasks of a higher priority than the
 * reader? (hardware/best-practices/disk-reads-stall-lower-priorities.md)
 *
 * A task at priority 5, then one at priority 12, sleeps in 1 ms timer.device
 * requests and records how late each wake-up is: first idle, then while this
 * task (priority 0) reads the files named in AKB_READ_FILES in 64 KB pieces.
 * The first half of the files is read for priority 5, the second half for 12;
 * use cold files of a few MB (see ide-read-rate). The sleeping task cannot
 * starve anything, and it ends itself after 30 s.
 * v4:timeout 120 */
#include "../akbtest.h"
#include <stdlib.h>
#include <string.h>
#include <proto/dos.h>
#include <proto/timer.h>
#include <dos/dostags.h>
#include <devices/timer.h>

#define PIECE (64 * 1024)

struct Device *TimerBase;
static ULONG eclockHz;
static volatile int phase, wakerDone;   /* phase 0 idle, 1 reading, 2 stop */
static volatile ULONG wakes[2], lateMax[2];
static volatile double lateSum[2];
static UBYTE piece[PIECE];

static double seconds(void)
{
    struct EClockVal v;
    ReadEClock(&v);
    return ((double)v.ev_hi * 4294967296.0 + v.ev_lo) / eclockHz;
}

static void wakerMain(void)
{
    struct MsgPort *port = CreateMsgPort();
    struct timerequest *tr = port ? (struct timerequest *)CreateIORequest(port, sizeof(*tr)) : NULL;
    double start = seconds();
    if (tr && OpenDevice((CONST_STRPTR)TIMERNAME, UNIT_MICROHZ, (struct IORequest *)tr, 0) == 0) {
        while (phase < 2 && seconds() - start < 30.0) {
            int p = phase;
            double t0 = seconds(), late;
            tr->tr_node.io_Command = TR_ADDREQUEST;
            tr->tr_time.tv_secs = 0;
            tr->tr_time.tv_micro = 1000;
            DoIO((struct IORequest *)tr);
            late = (seconds() - t0) * 1e6 - 1000.0;
            wakes[p]++;
            lateSum[p] += late;
            if (late > lateMax[p])
                lateMax[p] = (ULONG)late;
        }
        CloseDevice((struct IORequest *)tr);
    }
    if (tr) DeleteIORequest((struct IORequest *)tr);
    if (port) DeleteMsgPort(port);
    wakerDone = 1;
}

static void measure(int priority, char **names, int count)
{
    char key[40];
    double t0, idleSecs, readSecs = 0, bytes = 0;
    int i;
    phase = 0; wakerDone = 0;
    wakes[0] = wakes[1] = lateMax[0] = lateMax[1] = 0;
    lateSum[0] = lateSum[1] = 0;
    if (!CreateNewProcTags(NP_Entry, (ULONG)wakerMain, NP_Name, (ULONG)"ide-read-stall waker",
                           NP_Priority, priority, NP_StackSize, 4096, TAG_DONE)) {
        AKB_FAIL("waker", "task at priority %d did not start", priority);
        return;
    }
    t0 = seconds(); Delay(100); idleSecs = seconds() - t0;
    phase = 1;
    for (i = 0; i < count; i++) {
        BPTR fh = Open((CONST_STRPTR)names[i], MODE_OLDFILE);
        LONG got;
        if (!fh) {
            AKB_FAIL("open", "%s", names[i]);
            continue;
        }
        t0 = seconds();
        while ((got = Read(fh, piece, PIECE)) > 0)
            bytes += got;
        readSecs += seconds() - t0;
        Close(fh);
    }
    phase = 2;
    while (!wakerDone)
        Delay(1);
    if (readSecs <= 0) {
        AKB_FAIL("files-read", "nothing read at priority %d", priority);
        return;
    }
    sprintf(key, "pri%d-idle-wakes", priority);        AKB_VALUE(key, wakes[0] / idleSecs, "/s");
    sprintf(key, "pri%d-idle-late-max", priority);     AKB_VALUE(key, lateMax[0], "us");
    sprintf(key, "pri%d-reading-wakes", priority);     AKB_VALUE(key, wakes[1] / readSecs, "/s");
    sprintf(key, "pri%d-reading-late-mean", priority); AKB_VALUE(key, wakes[1] && lateSum[1] > 0 ? lateSum[1] / wakes[1] : 0, "us");
    sprintf(key, "pri%d-reading-late-max", priority);  AKB_VALUE(key, lateMax[1], "us");
    sprintf(key, "pri%d-read-rate", priority);         AKB_VALUE(key, bytes / 1024 / readSecs, "KB/s");
}

int main(void)
{
    static char files[1024];
    char *names[32];
    struct timerequest tr;
    struct EClockVal v;
    int n = 0;
    char *name;

    AKB_BEGIN("ide-read-stall");
    akb_machine();
    if (GetVar((CONST_STRPTR)"AKB_READ_FILES", (STRPTR)files, sizeof(files), 0) <= 0) {
        AKB_FAIL("files", "set AKB_READ_FILES to cold files of a few MB on the drive under test");
        return AKB_END();
    }
    for (name = strtok(files, " "); name && n < 32; name = strtok(NULL, " "))
        names[n++] = name;
    if (n < 2) {
        AKB_FAIL("files", "need at least two files, one set per priority");
        return AKB_END();
    }
    if (OpenDevice((CONST_STRPTR)TIMERNAME, UNIT_ECLOCK, (struct IORequest *)&tr, 0)) {
        AKB_FAIL("timer", "timer.device did not open");
        return AKB_END();
    }
    TimerBase = tr.tr_node.io_Device;
    eclockHz = ReadEClock(&v);
    measure(5, names, n / 2);
    measure(12, names + n / 2, n - n / 2);
    CloseDevice((struct IORequest *)&tr);
    AKB_PASS("measured");
    return AKB_END();
}
