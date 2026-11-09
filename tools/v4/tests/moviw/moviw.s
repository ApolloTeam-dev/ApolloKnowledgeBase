; MOVIW.L (core/cpu-68080/prm/integer/moviw.md), normal encoding
; 0011 rrr mmm 111101 + data word ($303D $8123 for moviw.l #$8123,d0).
; Not the LineA encoding. vasm wants the word as a signed value:
; #-32477 is $8123.

    xdef    _moviw_reg
    xdef    _moviw_mem
    xdef    _moviw_ccr

    section code,code

; unsigned long moviw_reg(void): moviw.l #$8123,d0
_moviw_reg:
    moveq   #0,d0
    moviw.l #-32477,d0
    rts

; void moviw_mem(unsigned long *p): moviw.l #$8123,(a0)
_moviw_mem:
    move.l  4(sp),a0
    moviw.l #-32477,(a0)
    rts

; unsigned long moviw_ccr(void): CCR after moviw.l #$8123,d1 (N set, Z clear)
; and after moviw.l #0,d1 (Z set) in the high and low word of d0.
_moviw_ccr:
    move.l  d2,-(sp)
    moviw.l #-32477,d1
    move.w  ccr,d0
    swap    d0
    moviw.l #0,d1
    move.w  ccr,d2
    move.w  d2,d0
    move.l  (sp)+,d2
    rts
