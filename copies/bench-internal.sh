#!/usr/bin/env bash

# usage: ./bench-internal.sh <run-name> <copies>
#        ./bench-internal.sh baseline 10
#
# Supported copy counts are the generated projects next to this script: 10,
# 100 and 1000. Only the summary is kept, unless KEEP_RAW=1.

set -uo pipefail

script_dir="$(cd "$(dirname "$0")" && pwd)"

run_name="${1:-}"
copies="${2:-}"

if [ -z "$run_name" ] || [ -z "$copies" ]; then
    echo "usage: $(basename "$0") <run-name> <copies>" >&2
    exit 1
fi

case "$copies" in
    10|100|1000) ;;
    *)
        echo "error: copies must be one of: 10, 100, 1000" >&2
        exit 1
        ;;
esac

project="shadow-mapping-$copies"
project_dir="$script_dir/$project"

if [ ! -f "$project_dir/project.json" ]; then
    echo "error: no project at $project_dir" >&2
    exit 1
fi

out_dir="$script_dir/results/$run_name"
mkdir -p "$out_dir"

raw="$out_dir/$project-internal-raw.csv"
output="$out_dir/$project-internal.csv"

echo "Recording $project frame spans into $run_name"

"${RAU_BIN:-rau-bin}" open "$project_dir" \
    --present-mode auto-no-vsync \
    --window-width 1920 \
    --window-height 1080 \
    --backend dx12 \
    --benchmark "$raw" \
    --benchmark-seconds 30 \
    --benchmark-warmup-seconds 10

if [ ! -e "$raw" ]; then
    echo "error: no capture was written to $raw" >&2
    exit 1
fi

python "$script_dir/aggregate_spans.py" "$raw" "$output" || exit 1

if [ -z "${KEEP_RAW:-}" ]; then
    rm -f "$raw"
fi
