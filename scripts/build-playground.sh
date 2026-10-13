#!/bin/sh
# Build the real Xu frontend and interpreter for the browser. No Xu binary needed.
set -eu
SITE_ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd -P)
PLAYGROUND_SOURCE=${XU_BOOTSTRAP_ROOT:-$SITE_ROOT/../bootstrap}
[ -f "$PLAYGROUND_SOURCE/crates/xuplay/Cargo.toml" ] || {
    echo "missing xuplay sources: set XU_BOOTSTRAP_ROOT to the bootstrap checkout" >&2
    exit 1
}
PLAYGROUND_SOURCE=$(CDPATH= cd -- "$PLAYGROUND_SOURCE" && pwd -P)
CARGO_TARGET_DIR=${CARGO_TARGET_DIR:-$SITE_ROOT/build/playground-target}
export CARGO_TARGET_DIR
cargo build --manifest-path "$PLAYGROUND_SOURCE/Cargo.toml" \
    --locked --offline --package xuplay --target wasm32-unknown-unknown --release
cp "$CARGO_TARGET_DIR/wasm32-unknown-unknown/release/xuplay.wasm" "$SITE_ROOT/www/xu-play.wasm"
echo "Xu playground built: $SITE_ROOT/www/xu-play.wasm"
