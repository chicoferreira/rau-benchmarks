#!/usr/bin/env bash

cd "$(dirname "$0")"

cargo build --release --quiet

exec ./target/release/ssao-baseline.exe
