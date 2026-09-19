#!/usr/bin/env bash

# usage: ./bench.sh <run-name> <launch-script> <process-name>
#        ./bench.sh baseline ssao/rau/launch.sh rau-bin.exe
#
# Only the summary is kept, unless KEEP_RAW=1.

set -uo pipefail

cd "$(dirname "$0")"

run_name="${1:-}"
launch_script="${2:-}"
process_name="${3:-}"

if [ -z "$run_name" ] || [ -z "$launch_script" ] || [ -z "$process_name" ]; then
    echo "usage: $(basename "$0") <run-name> <launch-script> <process-name>" >&2
    exit 1
fi

if [ ! -f "$launch_script" ]; then
    echo "error: no launch script at $launch_script" >&2
    exit 1
fi

tool_dir="$(cd "$(dirname "$launch_script")" && pwd)"
tool="$(basename "$tool_dir")"
suite="$(basename "$(dirname "$tool_dir")")"

out_dir="$tool_dir/results/$run_name"
mkdir -p "$out_dir"

raw="$out_dir/$tool-$suite-raw.csv"
output="$out_dir/$tool-$suite.csv"

if [ -n "${KEEP_RAW:-}" ]; then
    sink=(tee "$raw")
else
    sink=(cat)
fi

echo "Recording $tool $suite into $run_name"

bash "$launch_script" &

PresentMon-2.5.1-x64 \
    --process_name "$process_name" \
    --output_stdout \
    --delay 10 --timed 60 \
    --terminate_after_timed --stop_existing_session \
    --no_console_stats --v2_metrics \
    --set_circular_buffer_size 16384 |
    "${sink[@]}" |
    python aggregate-presentmon.py - "$output" \
        "run=$run_name" "tool=$tool" "suite=$suite" \
        "recorded=$(date -u +%Y-%m-%dT%H:%M:%SZ)"

status=$?

taskkill //F //IM "$process_name" >/dev/null 2>&1 || true
wait 2>/dev/null || true

if [ "$status" -ne 0 ] || [ ! -e "$output" ]; then
    echo "error: no summary was written to $output" >&2
    exit 1
fi
