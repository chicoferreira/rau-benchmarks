#!/usr/bin/env bash

# usage: ./bench-all.sh <run-name>

set -euo pipefail

cd "$(dirname "$0")"

run_name="${1:-}"
if [ -z "$run_name" ]; then
    echo "usage: $(basename "$0") <run-name>" >&2
    exit 1
fi

step() {
    echo
    echo "=== $* ==="
    "$@"
    sleep 5
}

step ./bench.sh "$run_name" ssao/baseline/launch.sh ssao-baseline.exe
step ./bench.sh "$run_name" ssao/rau/launch.sh rau-bin.exe
step ./bench.sh "$run_name" ssao/rau-focused/launch.sh rau-bin.exe
step ./bench.sh "$run_name" ssao/nau3d/launch.sh composerImGui.exe
step ./bench.sh "$run_name" ssao/shadered/launch.sh SHADERed.exe

step ./copies/bench-internal.sh "$run_name" 10
step ./copies/bench-internal.sh "$run_name" 100
step ./copies/bench-internal.sh "$run_name" 1000

step python copies/bench-load-save.py "$run_name"

./bench-memory-all.sh "$run_name"

