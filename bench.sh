#!/usr/bin/env bash

# usage: ./bench.sh <run-name> <launch-script> <process-name>
#        ./bench.sh baseline ssao/rau/launch.sh rau.exe
#
# Records 30 seconds of frames after 10 of warm-up, then the memory the tool
# holds at that point. Only the summary is kept, unless KEEP_RAW=1.

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
memory_output="$out_dir/$tool-$suite-memory.csv"

# count,working set,private bytes,peak working set,dedicated GPU memory — summed
# over every process with this name, so a tool that spawns helpers is still
# counted whole. The GPU counter has one instance per process and adapter.
export BENCH_PROC="${process_name%.exe}"
read_memory() {
    powershell.exe -NoProfile -NonInteractive -Command '
        $p = @(Get-Process -Name $env:BENCH_PROC -ErrorAction SilentlyContinue)
        if ($p.Count -eq 0) { exit 1 }
        $ids = $p.Id -join "|"
        $gpu = (Get-Counter "\GPU Process Memory(*)\Dedicated Usage").CounterSamples |
            Where-Object { $_.InstanceName -match "^pid_($ids)_" }
        "{0},{1},{2},{3},{4}" -f $p.Count,
            (($p | Measure-Object WorkingSet64 -Sum).Sum),
            (($p | Measure-Object PrivateMemorySize64 -Sum).Sum),
            (($p | Measure-Object PeakWorkingSet64 -Sum).Sum),
            [long](($gpu | Measure-Object CookedValue -Sum).Sum)
    ' | tr -d '\r'
}

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
    --delay 10 --timed 30 \
    --terminate_after_timed --stop_existing_session \
    --no_console_stats --v2_metrics \
    --set_circular_buffer_size 16384 |
    "${sink[@]}" |
    python aggregate-presentmon.py - "$output" \
        "run=$run_name" "tool=$tool" "suite=$suite" \
        "recorded=$(date -u +%Y-%m-%dT%H:%M:%SZ)"

status=$?

# Read once the frames are recorded, so the read itself stays out of them.
memory="$(read_memory)"
memory_status=$?

taskkill //F //IM "$process_name" >/dev/null 2>&1 || true
wait 2>/dev/null || true

if [ "$status" -ne 0 ] || [ ! -e "$output" ]; then
    echo "error: no summary was written to $output" >&2
    exit 1
fi

if [ "$memory_status" -ne 0 ] || [ -z "$memory" ]; then
    echo "error: $process_name was not running when its memory was read" >&2
    exit 1
fi

{
    echo "run,tool,suite,recorded,processes,working_set_mib,private_mib,peak_working_set_mib,gpu_dedicated_mib"
    echo "$memory" | awk -F, -v OFS=, \
        -v run="$run_name" -v tool="$tool" -v suite="$suite" \
        -v recorded="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        '{ printf "%s,%s,%s,%s,%s,%.1f,%.1f,%.1f,%.1f\n",
             run, tool, suite, recorded, $1,
             $2 / 1048576, $3 / 1048576, $4 / 1048576, $5 / 1048576 }'
} > "$memory_output"

cat "$memory_output"
