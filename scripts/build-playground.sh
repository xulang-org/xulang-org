#!/bin/sh
# The backend, frontend and evaluator are Xu; JavaScript is only the host bridge.
set -eu
SITE_ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd -P)
if [ -z "${XU_PLAYGROUND_SEED:-}" ]; then
    case "$(uname -s)-$(uname -m)" in
        Linux-x86_64) seed_target=linux-x64 ;;
        Linux-aarch64) seed_target=linux-arm64 ;;
        Darwin-arm64) seed_target=macos-arm64 ;;
        Darwin-x86_64) seed_target=macos-x64 ;;
        *) echo "set XU_PLAYGROUND_SEED to an installed Xu bundle" >&2; exit 1 ;;
    esac
    XU_PLAYGROUND_SEED=$(python3 "$SITE_ROOT/scripts/fetch-playground-seed.py" --target "$seed_target")
fi
export XU_PLAYGROUND_SEED
python3 "$SITE_ROOT/scripts/build-xu-playground.py"
