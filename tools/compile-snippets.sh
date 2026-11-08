#!/bin/sh
# Compile all extracted kb:compile snippets with ApolloCrossDev.
#
# Snippets are compiled to object files, not linked, so each one must be a
# complete translation unit. Flags follow the ApolloCrossDev Makefile template
# (Projects/_makefiles/Makefile). PREFIX is the ApolloCrossDev compiler folder,
# e.g. ~/ApolloCrossDev/Compilers/GCC-6.50-Dev. When APOLLOLIB is set to an
# ApolloLib folder (ApolloCrossDev Projects/ApolloLib), snippets can include
# "ApolloCrossDev_Lib.h".
#
# A snippet with a `kb:opts <flags>` line is built with those code-generation
# flags instead of the default OPTS (C, C++) or AOPTS (assembly). A snippet
# with `kb:expect` or `kb:expect-not` lines is also turned into the output
# that tools/check_emitted_code.py checks: assembly text (`-S`, <name>.asm)
# for C and C++, the assembled bytes (`-Fbin`, <name>.bin) for assembly.
#
#   compile-snippets.sh [dir]   compile all .c/.cpp/.s files in dir
#                               (default: build/snippets)
set -e

PREFIX="${PREFIX:?set PREFIX to the ApolloCrossDev compiler folder}"
TARGET=m68k-amigaos

CC="${CC:-$PREFIX/bin/m68k-amigaos-gcc}"
CXX="${CXX:-$PREFIX/bin/m68k-amigaos-g++}"
AS="${AS:-$PREFIX/bin/vasmm68k_mot}"

OPTS="-O2 -m68080 -m68881 -ffast-math -fomit-frame-pointer"
AOPTS="-m68080 -m68881 -opt-speed"
INCL="-I$PREFIX/$TARGET/libnix/include -I$PREFIX/$TARGET/sys-include -I$PREFIX/$TARGET/ndk32-include/Include_H"
[ -n "$APOLLOLIB" ] && INCL="$INCL -I$APOLLOLIB"
AINCL="-I$PREFIX/$TARGET/DevPac/Include"

cd "${1:-$(dirname "$0")/../build/snippets}"
fail=0
count=0
for f in *.c *.cpp *.s; do
  [ -e "$f" ] || continue
  count=$((count + 1))
  opts=$(sed -n 's/^[[:space:];/]*kb:opts[[:space:]]*//p' "$f" | head -n 1)
  expect=$(grep -c 'kb:expect' "$f" || true)
  case "$f" in
    *.c|*.cpp)
      if [ "${f%.cpp}" != "$f" ]; then cc=$CXX; base=${f%.cpp}; flags=$CXXFLAGS
      else cc=$CC; base=${f%.c}; flags=$CFLAGS; fi
      flags="${flags:--noixemul ${opts:-$OPTS} -Wall $INCL}"
      $cc $flags -c "$f" -o "$base.o" || { echo "::error::$f failed"; fail=1; continue; }
      if [ "$expect" -gt 0 ]; then
        $cc $flags -S "$f" -o "$base.asm" || { echo "::error::$f: -S failed"; fail=1; }
      fi ;;
    *.s)
      base=${f%.s}
      flags="${ASFLAGS:--quiet ${opts:-$AOPTS} $AINCL}"
      $AS $flags -Fhunk "$f" -o "$base.o" || { echo "::error::$f failed"; fail=1; continue; }
      if [ "$expect" -gt 0 ]; then
        $AS $flags -Fbin "$f" -o "$base.bin" || { echo "::error::$f: -Fbin failed"; fail=1; }
      fi ;;
  esac
done
echo "Compiled $count file(s) in $(pwd)"
exit $fail
