#!/bin/sh
# The product Xu compiler owns the backend; this repository owns the evaluator.
set -eu
SITE_ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd -P)
set -- --sdk "${XU_ROOT:-$SITE_ROOT/../xu}" "$@"
if [ -n "${XU_BIN:-}" ]; then
  set -- --compiler "$XU_BIN" "$@"
fi
python3 "$SITE_ROOT/scripts/build-typed-playground.py" "$@"
