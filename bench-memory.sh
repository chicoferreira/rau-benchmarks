#!/usr/bin/env bash

# usage: ./bench-memory.sh <run-name> <launch-script> <process-name>
#        ./bench-memory.sh baseline ssao/rau/launch.sh rau-bin.exe
#
# Launches the tool, waits BENCH_SECONDS (30 by default) and records how much
# memory it is holding at that point.

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

output="$out_dir/$tool-$suite-memory.csv"
seconds="${BENCH_SECONDS:-30}"

# count,working set,private bytes,peak working set — summed over every process
# with this name, so a tool that spawns helpers is still counted whole.
export BENCH_PROC="${process_name%.exe}"
read_memory() {
    powershell.exe -NoProfile -NonInteractive -Command '
        $p = @(Get-Process -Name $env:BENCH_PROC -ErrorAction SilentlyContinue)
        if ($p.Count -eq 0) { exit 1 }
        "{0},{1},{2},{3}" -f $p.Count,
            (($p | Measure-Object WorkingSet64 -Sum).Sum),
            (($p | Measure-Object PrivateMemorySize64 -Sum).Sum),
            (($p | Measure-Object PeakWorkingSet64 -Sum).Sum)
    ' | tr -d '\r'
}

echo "Recording $tool $suite memory into $run_name"

bash "$launch_script" &

for _ in $(seq 30); do
    read_memory >/dev/null && break
    sleep 1
done

sleep "$seconds"

sample="$(read_memory)"
status=$?

taskkill //F //IM "$process_name" >/dev/null 2>&1 || true
wait 2>/dev/null || true

if [ "$status" -ne 0 ] || [ -z "$sample" ]; then
    echo "error: $process_name was not running after $seconds seconds" >&2
    exit 1
fi

{
    echo "run,tool,suite,recorded,seconds,processes,working_set_mib,private_mib,peak_working_set_mib"
    echo "$sample" | awk -F, -v OFS=, \
        -v run="$run_name" -v tool="$tool" -v suite="$suite" \
        -v recorded="$(date -u +%Y-%m-%dT%H:%M:%SZ)" -v seconds="$seconds" \
        '{ printf "%s,%s,%s,%s,%s,%s,%.1f,%.1f,%.1f\n",
             run, tool, suite, recorded, seconds, $1,
             $2 / 1048576, $3 / 1048576, $4 / 1048576 }'
} > "$output"

cat "$output"
echo "$output"
