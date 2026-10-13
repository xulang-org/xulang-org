#!/bin/sh
# Copy freshly built product compilers into the current site's release directory.
set -eu
ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd -P)
XU_ROOT=$(CDPATH= cd -- "${XU_ROOT:-$ROOT/../xu}" && pwd -P)
VERSION=$(cat "$XU_ROOT/VERSION")
DST="$ROOT/www/releases/$VERSION"
mkdir -p "$DST"
missing=0
for platform in macos-arm64 macos-x64 linux-arm64 linux-x64 linux-loongarch64 linux-riscv64 windows-x64 windows-arm64; do
    os=${platform%-*}
    arch=${platform#*-}
    suffix=""
    [ "$os" != windows ] || suffix=.exe
    source="$XU_ROOT/bin/platform/$platform/xu$suffix"
    name="xu.$os.$arch$suffix"
    if [ -f "$source" ]; then
        cp "$source" "$DST/$name"
        echo "copied $name"
    else
        echo "missing $source" >&2
        missing=$((missing + 1))
    fi
done
[ "$missing" = 0 ] || { echo "run make xu in $XU_ROOT before syncing downloads" >&2; exit 1; }
echo "release $VERSION -> $DST (gitignored)"
