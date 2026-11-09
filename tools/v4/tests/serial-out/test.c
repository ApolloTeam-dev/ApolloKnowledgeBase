/* serial-out: the V4's serial line reaches the test Mac. Writes a line to
 * the Paula UART at 115200 baud the way ApolloLib's ApolloDebugPutChar()
 * does (ApolloCrossDev Projects/ApolloLib/ApolloCrossDev_Debug.c), with no
 * OS call, so os-takeover tests can report the same way. v4test.py checks
 * that the serial log contains the line (v4:serial-expect).
 *
 * v4:serial-expect AKB-SERIAL-OK
 */
#include "../akbtest.h"

#define SERDATR 0xDFF018
#define SERDAT  0xDFF030
#define SERPER  0xDFF032
#define INTREQ  0xDFF09C
#define TBE     (1 << 13)
#define INTF_TBE 0x0001
/* PAL colour clock 3546895 Hz / 115200 baud - 1 */
#define SERPER_115200 ((3546895 + 115200 / 2) / 115200 - 1)

static void put(int c)
{
    while ((*(volatile unsigned short *)SERDATR & TBE) == 0)
        ;
    *(volatile unsigned short *)INTREQ = INTF_TBE;
    *(volatile unsigned short *)SERDAT = 0x100 | (c & 0xFF);   /* stop bit + 8 data bits */
}

static void puts_ser(const char *s)
{
    for (; *s; s++) {
        if (*s == '\n')
            put('\r');
        put(*s);
    }
}

int main(void)
{
    AKB_BEGIN("serial-out");
    akb_machine();
    *(volatile unsigned short *)SERPER = SERPER_115200;
    puts_ser("\nAKB-SERIAL-OK\n");
    AKB_PASS("written");
    return AKB_END();
}
