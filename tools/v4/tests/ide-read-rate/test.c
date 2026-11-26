/* ide-read-rate: read rate of whole files through dos.library Read(), and the
 * CPU left to other tasks while reading
 * (hardware/best-practices/disk-reads-stall-lower-priorities.md).
 *
 * Reads each file named in the environment variable AKB_READ_FILES (space
 * separated, e.g. SetEnv AKB_READ_FILES "Work:a.bin Work:b.bin") once, in
 * 64 KB pieces. Use files of a few MB that were not read since boot, so that
 * the filesystem cache does not answer. A task at priority -1 counts loop
 * passes meanwhile: its rate while reading, against its idle rate, is the CPU
 * the reads leave. It is below this task, so it cannot starve anything.
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
static volatile ULONG counter;
static volatile int stopCounter, counterDone;
static UBYTE piece[PIECE];

static double seconds(void)
{
    struct EClockVal v;
    ReadEClock(&v);
    return ((double)v.ev_hi * 4294967296.0 + v.ev_lo) / eclockHz;
}

static void counterMain(void)
{
    while (!stopCounter)
        counter++;
    counterDone = 1;
}

int main(void)
{
    static char files[1024];
    struct timerequest tr;
    struct EClockVal v;
    double t0, idleRate, readSecs = 0, bytes = 0, counts = 0;
    char *name;
    ULONG c0;

    AKB_BEGIN("ide-read-rate");
    akb_machine();
    if (GetVar((CONST_STRPTR)"AKB_READ_FILES", (STRPTR)files, sizeof(files), 0) <= 0) {
        AKB_FAIL("files", "set AKB_READ_FILES to cold files of a few MB on the drive under test");
        return AKB_END();
    }
    if (OpenDevice((CONST_STRPTR)TIMERNAME, UNIT_ECLOCK, (struct IORequest *)&tr, 0)) {
        AKB_FAIL("timer", "timer.device did not open");
        return AKB_END();
    }
    TimerBase = tr.tr_node.io_Device;
    eclockHz = ReadEClock(&v);
    if (!CreateNewProcTags(NP_Entry, (ULONG)counterMain, NP_Name, (ULONG)"ide-read-rate counter",
                           NP_Priority, -1, NP_StackSize, 4096, TAG_DONE)) {
        AKB_FAIL("counter", "task did not start");
        CloseDevice((struct IORequest *)&tr);
        return AKB_END();
    }
    Delay(10);
    c0 = counter; t0 = seconds(); Delay(100);
    idleRate = (counter - c0) / (seconds() - t0);

    for (name = strtok(files, " "); name; name = strtok(NULL, " ")) {
        BPTR fh = Open((CONST_STRPTR)name, MODE_OLDFILE);
        LONG got;
        if (!fh) {
            AKB_FAIL("open", "%s", name);
            continue;
        }
        c0 = counter; t0 = seconds();
        while ((got = Read(fh, piece, PIECE)) > 0)
            bytes += got;
        readSecs += seconds() - t0;
        counts += counter - c0;
        Close(fh);
    }
    stopCounter = 1;
    while (!counterDone)
        Delay(1);
    CloseDevice((struct IORequest *)&tr);

    AKB_CHECK("files-read", bytes > 0 && readSecs > 0, "nothing read");
    if (bytes > 0 && readSecs > 0) {
        AKB_VALUE("read-kb", bytes / 1024, "KB");
        AKB_VALUE("read-rate", bytes / 1024 / readSecs, "KB/s");
        AKB_VALUE("cpu-left", 100.0 * counts / (idleRate * readSecs), "%");
    }
    return AKB_END();
}
