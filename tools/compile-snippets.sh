#!/bin/sh
# Compile all extracted kb:compile snippets with ApolloCrossDev.
#
# TODO (ApolloTeam): fill in the real ApolloCrossDev commands below.
# CC and AS must point to the ApolloCrossDev C compiler and assembler,
# with the flags the team uses for 68080 targets (see toolchain/).
set -e

CC="${CC:?set CC to the ApolloCrossDev C compiler}"
AS="${AS:?set AS to the ApolloCrossDev assembler}"
CFLAGS="${CFLAGS:-}"
ASFLAGS="${ASFLAGS:-}"

cd "$(dirname "$0")/../build/snippets"
fail=0
for f in *.c *.s; do
  [ -e "$f" ] || continue
  case "$f" in
    *.c) $CC $CFLAGS -c "$f" -o "${f%.c}.o" || { echo "::error::$f failed"; fail=1; } ;;
    *.s) $AS $ASFLAGS "$f" -o "${f%.s}.o"   || { echo "::error::$f failed"; fail=1; } ;;
  esac
done
exit $fail
