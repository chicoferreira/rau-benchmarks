#!/usr/bin/env bash

# usage: ./launch.sh [extra rau flags...]

cd "$(dirname "$0")"

exec "${RAU_BIN:-rau-bin}" open "$PWD/project" \
    --present-mode auto-no-vsync \
    --window-width 1920 \
    --window-height 1080 \
    --backend dx12 \
    "$@"
