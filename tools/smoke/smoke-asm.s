; Toolchain smoke test: vasm with 68080 target.
	section	code,code
	xdef	_smoke_asm
_smoke_asm:
	moveq	#0,d0
	rts
