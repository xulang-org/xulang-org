#!/bin/sh
# Run the xu-site local server.
#
# The default lane is the hosted product lane. It resolves a hosted seed and
# invokes the repository's hermetic product wrapper; it never discovers or
# builds the Rust primer. The primer is an oracle/recovery implementation and
# can only be selected with an explicit --oracle (or --lane oracle) flag.
#
# A small provenance sidecar is kept next to a generated artifact. This is
# important for local development: an ignored artifact left by an oracle run must
# not silently become the product server on the next invocation.
set -eu

ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd -P)
XU_ROOT=$(CDPATH= cd -- "${XU_ROOT:-$ROOT/../xu}" && pwd -P)
SITE_ROOT=${XU_SITE_ROOT:-$ROOT}
export XU_SITE_ROOT="$SITE_ROOT"

LANE=product
LANE_EXPLICIT=0

die() {
    echo "xu-site: $*" >&2
    exit 1
}

# Lane selectors are deliberately accepted only before server arguments. A
# site program may still receive an ordinary -- flag after the first non-lane
# argument (or after --) without this launcher consuming it.
while [ "$#" -gt 0 ]; do
    case "$1" in
        --oracle)
            [ "$LANE_EXPLICIT" = 0 ] || [ "$LANE" = oracle ] || die "conflicting lane selectors"
            LANE=oracle
            LANE_EXPLICIT=1
            shift
            ;;
        --lane)
            [ "$#" -ge 2 ] || die "--lane requires product or oracle"
            case "$2" in
                product|hosted) next_lane=product ;;
                oracle|primer) next_lane=oracle ;;
                *) die "unknown lane '$2' (expected product or oracle)" ;;
            esac
            [ "$LANE_EXPLICIT" = 0 ] || [ "$LANE" = "$next_lane" ] || die "conflicting lane selectors"
            LANE=$next_lane
            LANE_EXPLICIT=1
            shift 2
            ;;
        --lane=product|--lane=hosted)
            [ "$LANE_EXPLICIT" = 0 ] || [ "$LANE" = product ] || die "conflicting lane selectors"
            LANE=product
            LANE_EXPLICIT=1
            shift
            ;;
        --lane=oracle|--lane=primer)
            [ "$LANE_EXPLICIT" = 0 ] || [ "$LANE" = oracle ] || die "conflicting lane selectors"
            LANE=oracle
            LANE_EXPLICIT=1
            shift
            ;;
        *)
            break
            ;;
    esac
done

# Both lanes publish an artifact without a suffix.
default_artifact="$ROOT/xu-site"
if [ "$LANE" = oracle ]; then
    default_artifact="$ROOT/xu-site-oracle"
fi
ARTIFACT=${XU_SITE_ARTIFACT:-$default_artifact}
# Resolve a relative artifact against the caller's directory, preserving the
# historical run-local behaviour while making the sidecar comparison stable.
case "$ARTIFACT" in
    /*) ;;
    *) ARTIFACT="$(pwd -P)/$ARTIFACT" ;;
esac
ARTIFACT_DIR=$(dirname "$ARTIFACT")
ARTIFACT_NAME=$(basename "$ARTIFACT")
if [ ! -d "$ARTIFACT_DIR" ]; then
    mkdir -p "$ARTIFACT_DIR"
fi
ARTIFACT="$ARTIFACT_DIR/$ARTIFACT_NAME"
PROVENANCE=${XU_SITE_PROVENANCE:-$ARTIFACT.provenance}
case "$PROVENANCE" in
    /*) ;;
    *) PROVENANCE="$(pwd -P)/$PROVENANCE" ;;
esac

[ "$PROVENANCE" != "$ARTIFACT" ] || die "XU_SITE_PROVENANCE must not replace the artifact"

requested_compiler=${XU_COMPILER:-${XU:-${XU_SEED:-}}}

# The resolver canonicalizes paths and rejects a primer hidden behind a
# symlink. Product mode forces oracle opt-in off even when the caller has a
# broad XU_ALLOW_ORACLE_SEED=1 in its environment.
resolve_product_compiler() {
    if [ -n "$requested_compiler" ]; then
        (cd "$XU_ROOT" && XU_ALLOW_ORACLE_SEED=0 XU_SEED="$requested_compiler" \
            "$XU_ROOT/scripts/xu_host_seed.sh")
    else
        (cd "$XU_ROOT" && XU_ALLOW_ORACLE_SEED=0 XU_SEED= \
            "$XU_ROOT/scripts/xu_host_seed.sh")
    fi
}

has_symlink_component() {
    candidate=$1
    root=$2
    case "$candidate" in
        "$root"/*) rel=${candidate#"$root/"} ;;
        *) return 1 ;;
    esac
    current=$root
    old_ifs=$IFS
    IFS=/
    # Paths in this repository contain no whitespace; splitting on `/` keeps
    # this launcher POSIX-sh while still checking every component.
    set -- $rel
    IFS=$old_ifs
    for part do
        [ -n "$part" ] || continue
        current="$current/$part"
        [ -L "$current" ] && return 0
    done
    return 1
}

is_frozen_primer_path() {
    candidate=$1
    resolved=${2:-$1}
    case "$candidate" in
        /*) lexical=$candidate ;;
        *) lexical="$XU_ROOT/$candidate" ;;
    esac
    for expected in \
        "$XU_ROOT/bootstrap/target/debug/xu" \
        "$XU_ROOT/bootstrap/target/debug/xu.exe" \
        "$XU_ROOT/bootstrap/target/release/xu" \
        "$XU_ROOT/bootstrap/target/release/xu.exe"; do
        [ "$lexical" = "$expected" ] || continue
        [ -f "$expected" ] || continue
        [ -x "$expected" ] || continue
        has_symlink_component "$expected" "$XU_ROOT" && continue
        [ "$resolved" = "$expected" ] || continue
        return 0
    done
    return 1
}

# Oracle mode is intentionally explicit. It defaults to the checked-out
# primer for recovery, but still canonicalizes through the same resolver so a
# symlink cannot disguise the lane. No cargo build is performed here; callers
# must prepare the requested executable themselves.
resolve_oracle_compiler() {
    oracle_candidate=$requested_compiler
    if [ -z "$oracle_candidate" ]; then
        for primer in \
            "$XU_ROOT/bootstrap/target/debug/xu" \
            "$XU_ROOT/bootstrap/target/debug/xu.exe" \
            "$XU_ROOT/bootstrap/target/release/xu" \
            "$XU_ROOT/bootstrap/target/release/xu.exe"; do
            if [ -x "$primer" ]; then
                oracle_candidate=$primer
                break
            fi
        done
    fi
    resolved_oracle=$(cd "$XU_ROOT" && XU_ALLOW_ORACLE_SEED=1 XU_SEED="$oracle_candidate" \
        "$XU_ROOT/scripts/xu_host_seed.sh") || return 1
    is_frozen_primer_path "$oracle_candidate" "$resolved_oracle" || {
        echo "xu-site: oracle compiler must be the frozen bootstrap primer (bootstrap/target/{debug,release}/xu[.exe])" >&2
        return 1
    }
    printf '%s\n' "$resolved_oracle"
}

provenance_value() {
    # Keys are generated by this script and contain no newlines. Read only
    # the first matching line so a hand-edited sidecar cannot inject shell.
    key=$1
    sed -n "s/^$key=//p" "$PROVENANCE" | sed -n '1p'
}

provenance_matches() {
    [ -f "$PROVENANCE" ] || return 1
    [ "$(provenance_value lane)" = "$LANE" ] || return 1
    [ "$(provenance_value artifact)" = "$ARTIFACT" ] || return 1
    [ "$(provenance_value source_root)" = "$ROOT" ] || return 1
    return 0
}

write_provenance() {
    provenance_tmp="$PROVENANCE.tmp.$$"
    {
        printf '%s\n' 'schema=1'
        printf 'lane=%s\n' "$LANE"
        printf 'compiler=%s\n' "$COMPILER"
        printf 'artifact=%s\n' "$ARTIFACT"
        printf 'source_root=%s\n' "$ROOT"
    } > "$provenance_tmp" || die "cannot write provenance sidecar $PROVENANCE"
    mv "$provenance_tmp" "$PROVENANCE" || die "cannot install provenance sidecar $PROVENANCE"
}

needs_build=1
if [ -x "$ARTIFACT" ] && provenance_matches; then
    needs_build=0
fi

# An explicit compiler override must be resolved even when an artifact exists;
# this prevents XU_COMPILER=bootstrap/... from being silently ignored merely
# because a product-looking artifact is present.
if [ "$needs_build" = 0 ] && [ -n "$requested_compiler" ]; then
    if [ "$LANE" = product ]; then
        requested_resolved=$(resolve_product_compiler) || die "requested product compiler is unavailable"
    else
        requested_resolved=$(resolve_oracle_compiler) || die "requested oracle compiler is unavailable"
    fi
    recorded_compiler=$(provenance_value compiler)
    if [ "$recorded_compiler" != "$requested_resolved" ]; then
        needs_build=1
    fi
fi

if [ "$needs_build" = 1 ]; then
    if [ "$LANE" = product ]; then
        COMPILER=$(resolve_product_compiler) || die "no hosted product compiler available"
        echo "xu-site: building $ARTIFACT lane=product compiler=$COMPILER" >&2
        # Product Xu has one supported CLI seam. Do not probe for a primer
        # dialect or fall back to the Rust file-first command here.
        (
            cd "$XU_ROOT"
            XU_ALLOW_ORACLE_SEED=0 "$XU_ROOT/scripts/run_product_compiler.sh" \
                "$COMPILER" build "$ROOT" -o "$ARTIFACT"
        ) || die "hosted product compiler failed to build xu-site"
    else
        COMPILER=$(resolve_oracle_compiler) || die "no oracle compiler available"
        echo "xu-site: WARNING building lane=oracle compiler=$COMPILER; this is not product evidence" >&2
        # The frozen primer predates the hosted build subcommand. This dialect
        # probe is allowed only after --oracle/--lane oracle was explicitly
        # selected above.
        # A temporary dotted basename prevents older primers from adding an
        # output suffix. Install the result at the exact requested path.
        oracle_build_output=$(mktemp "$ARTIFACT.build.XXXXXX") \
            || die "cannot create temporary oracle output"
        trap 'rm -f "$oracle_build_output"' 0
        if "$COMPILER" --help 2>&1 | grep -Eq '^[[:space:]]*build[[:space:]]'; then
            (cd "$XU_ROOT" && "$COMPILER" build "$ROOT" -o "$oracle_build_output") \
                || die "oracle compiler failed to build xu-site"
        else
            (cd "$XU_ROOT" && "$COMPILER" "$ROOT" -o "$oracle_build_output") \
                || die "oracle compiler failed to build xu-site"
        fi
        [ -s "$oracle_build_output" ] || die "oracle compiler did not produce an artifact"
        mv -f "$oracle_build_output" "$ARTIFACT" || die "cannot install oracle artifact"
        trap - 0
    fi
    chmod +x "$ARTIFACT" 2>/dev/null || true
    [ -x "$ARTIFACT" ] || die "compiler did not produce executable artifact $ARTIFACT"
    write_provenance
else
    echo "xu-site: using existing $ARTIFACT lane=$LANE ($(provenance_value compiler))" >&2
fi

if [ "$#" -eq 0 ]; then
    set -- --port 18080
fi
exec "$ARTIFACT" "$@"
