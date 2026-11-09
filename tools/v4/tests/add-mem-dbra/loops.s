; Loops for add-mem-dbra. Each takes the iteration count (1-65536) on the
; stack and returns the CCC cycles of the loop in d0. Timing reads CCC with
; movec ccc,Dn (core/cpu-68080/performance-counters.md).

    xdef    _loop_empty
    xdef    _loop_reg
    xdef    _loop_mem_abs
    xdef    _loop_mem_an
    xdef    _counter

    section code,code

; dbra alone
_loop_empty:
    move.l  4(sp),d1
    subq.l  #1,d1
    movec   ccc,a1
.l: dbra    d1,.l
    movec   ccc,d0
    sub.l   a1,d0
    rts

; addq.l #1,Dn + dbra
_loop_reg:
    move.l  4(sp),d1
    subq.l  #1,d1
    moveq   #0,d0
    movec   ccc,a1
.l: addq.l  #1,d0
    dbra    d1,.l
    movec   ccc,d0
    sub.l   a1,d0
    rts

; add.l #1,counter (absolute long) + dbra: Gunnar's loop. vasm assembles
; add.l #1 as addq.l #1 ($52B9 + address), as it would in any program.
_loop_mem_abs:
    move.l  4(sp),d1
    subq.l  #1,d1
    movec   ccc,a1
.l: add.l   #1,_counter
    dbra    d1,.l
    movec   ccc,d0
    sub.l   a1,d0
    rts

; add.l #1,(a0) + dbra
_loop_mem_an:
    move.l  4(sp),d1
    subq.l  #1,d1
    lea     _counter,a0
    movec   ccc,a1
.l: add.l   #1,(a0)
    dbra    d1,.l
    movec   ccc,d0
    sub.l   a1,d0
    rts

    section adata,data
    cnop    0,16
_counter:
    dc.l    0

; Distance test: add.l #1,(a0) + dbra with a0 = a counter at a fixed
; distance after the loop, in the same code section. Arguments: count,
; counter address. The loop starts on a 64-byte boundary.
    xdef    _loop_mem_ptr
    xdef    _near_0
    xdef    _near_64
    xdef    _near_128
    xdef    _near_256
    xdef    _near_1k
    xdef    _near_4k
    xdef    _near_16k

    section ncode,code
    cnop    0,64
_loop_mem_ptr:
    move.l  4(sp),d1
    move.l  8(sp),a0
    subq.l  #1,d1
    movec   ccc,a1
.l: add.l   #1,(a0)
    dbra    d1,.l
    movec   ccc,d0
    sub.l   a1,d0
    rts
    cnop    0,32
_near_0:        dc.l    0       ; loop start + 32
    cnop    0,64
    ds.b    32
_near_64:       dc.l    0       ; + 96
    cnop    0,64
    ds.b    64
_near_128:      dc.l    0
    ds.b    256
_near_256:      dc.l    0
    ds.b    1024
_near_1k:       dc.l    0
    ds.b    4096
_near_4k:       dc.l    0
    ds.b    16384
_near_16k:      dc.l    0
