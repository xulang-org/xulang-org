#!/bin/sh
# The product Xu compiler owns the backend; this repository owns the evaluator.
set -eu
SITE_ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd -P)
python3 "$SITE_ROOT/scripts/build-xu-playground.py"
