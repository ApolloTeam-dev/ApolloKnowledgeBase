#!/bin/sh
# find-acd.sh - find ApolloCrossDev and check that it can build.
#
# Usage: sh find-acd.sh [project folder]
# Prints KEY=value lines (ACD_ROOT, PREFIX, GCC, TEMPLATE, MAKEFILE) and
# exits 0 when the GCC-6.50-Dev toolchain is complete; otherwise prints
# PROBLEM= lines and exits 1.
#
# Where it looks for ApolloCrossDev, in this order:
#   1. $APOLLOCROSSDEV
#   2. two folders above the project (the project is in ApolloCrossDev/Projects/)
#   3. $HOME/ApolloCrossDev

project=${1:-.}
problems=0
problem() { echo "PROBLEM=$1"; problems=1; }

if [ -n "$APOLLOCROSSDEV" ] && [ ! -d "$APOLLOCROSSDEV/Compilers" ]; then
    problem "APOLLOCROSSDEV=$APOLLOCROSSDEV has no Compilers folder; the Makefile uses it, so fix or unset it"
fi

root=""
for c in "$APOLLOCROSSDEV" "$project/../.." "$HOME/ApolloCrossDev"; do
    [ -n "$c" ] && [ -d "$c/Compilers" ] && { root=$(cd "$c" && pwd); break; }
done
if [ -z "$root" ]; then
    problem "ApolloCrossDev not found. Install it (github.com/WDrijver/ApolloCrossDev) and set APOLLOCROSSDEV to its folder."
    exit 1
fi
echo "ACD_ROOT=$root"
[ -n "$APOLLOCROSSDEV" ] || echo "NOTE=APOLLOCROSSDEV is not set; projects outside $root/Projects need it (export APOLLOCROSSDEV=$root)"

prefix="$root/Compilers/GCC-6.50-Dev"
echo "PREFIX=$prefix"
for b in m68k-amigaos-gcc m68k-amigaos-g++ vasmm68k_mot; do
    [ -x "$prefix/bin/$b" ] || problem "$prefix/bin/$b is missing: the GCC-6.50-Dev install is incomplete (see Compilers/GCC-6.50-Dev/_logs/*_err.log)"
done
[ -x "$prefix/bin/m68k-amigaos-gcc" ] && echo "GCC=$("$prefix/bin/m68k-amigaos-gcc" --version | head -n 1)"

template="$root/Projects/_makefiles/Makefile"
if [ -f "$template" ]; then
    echo "TEMPLATE=$(sed -n 's/^# ApolloCrossDev Makefile Template //p' "$template" | head -n 1)"
    grep -q '^compile:' "$template" || echo "NOTE=the Makefile template has no 'make compile' target: update ApolloCrossDev (git pull)"
else
    problem "$template is missing"
fi

if [ -f "$project/Makefile" ]; then
    echo "MAKEFILE=$(sed -n 's/^# ApolloCrossDev Makefile Template //p' "$project/Makefile" | head -n 1)"
    grep -q '^compile:' "$project/Makefile" || echo "NOTE=the project Makefile has no 'make compile' target; build with: make cleanbefore build"
fi

exit $problems
