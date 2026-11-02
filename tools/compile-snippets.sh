#!/bin/sh
# Compile all extracted kb:compile snippets with ApolloCrossDev.
#
# Snippets are compiled to object files, not linked, so each one must be a
# complete translation unit. Flags follow the ApolloCrossDev Makefile template
# (Projects/_makefiles/Makefile). PREFIX is the ApolloCrossDev compiler folder,
# e.g. ~/ApolloCrossDev/Compilers/GCC-6.50-Dev.
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
INCL="-I$PREFIX/$TARGET/libnix/include -I$PREFIX/$TARGET/sys-include -I$PREFIX/$TARGET/ndk32-include/Include_H"
CFLAGS="${CFLAGS:--noixemul $OPTS -Wall $INCL}"
CXXFLAGS="${CXXFLAGS:--noixemul $OPTS -Wall $INCL}"
ASFLAGS="${ASFLAGS:--quiet -Fhunk -m68080 -m68881 -opt-speed -I$PREFIX/$TARGET/DevPac/Include}"

cd "${1:-$(dirname "$0")/../build/snippets}"
fail=0
count=0
for f in *.c *.cpp *.s; do
  [ -e "$f" ] || continue
  count=$((count + 1))
  case "$f" in
    *.c)   $CC $CFLAGS -c "$f" -o "${f%.c}.o"     || { echo "::error::$f failed"; fail=1; } ;;
    *.cpp) $CXX $CXXFLAGS -c "$f" -o "${f%.cpp}.o" || { echo "::error::$f failed"; fail=1; } ;;
    *.s)   $AS $ASFLAGS "$f" -o "${f%.s}.o"         || { echo "::error::$f failed"; fail=1; } ;;
  esac
done
echo "Compiled $count file(s) in $(pwd)"
exit $fail
