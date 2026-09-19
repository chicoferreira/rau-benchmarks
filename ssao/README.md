# SSAO benchmark

The same SSAO scene drawn in Rau, in Rau's focus view, in Nau3D, in SHADERed, and in a baseline program written directly against WGPU. Each tool's folder holds a `launch.sh` that starts it with the scene open at 1920x1080 with v-sync off. The Nau3D and SHADERed folders also list, in their own `README.md`, how their version of the scene differs from Rau's.

The commands below are run from the root of this repository.

## Frame times

`bench.sh` takes the run name, the script that launches the tool, and the process name PresentMon attaches to. It records 60 seconds of frames after 10 seconds of warmup.

```sh
./bench.sh <run-name> ssao/baseline/launch.sh ssao-baseline.exe
./bench.sh <run-name> ssao/rau/launch.sh rau-bin.exe
./bench.sh <run-name> ssao/rau-focused/launch.sh rau-bin.exe
./bench.sh <run-name> ssao/nau3d/launch.sh composerImGui.exe
./bench.sh <run-name> ssao/shadered/launch.sh SHADERed.exe
```

PresentMon is piped into `aggregate-presentmon.py`, so a run only leaves the summary behind, in `ssao/<tool>/results/<run-name>/<tool>-ssao.csv`. `KEEP_RAW=1` also writes the per-frame capture next to it, which can be summarised again later with:

```sh
python aggregate-presentmon.py ssao/rau/results/<run-name>/rau-ssao-raw.csv ssao/rau/results/<run-name>/rau-ssao.csv
```

Two runs of the same tool are compared with:

```sh
python compare.py ssao/rau/results/<run-name> ssao/rau/results/<other-run-name>
```

## Memory

`bench-memory.sh` takes the same arguments as `bench.sh`. It launches the tool, waits 30 seconds (`BENCH_SECONDS` overrides it) and records how much memory the process is holding at that point, as a single row in `ssao/<tool>/results/<run-name>/<tool>-ssao-memory.csv`. `bench-memory-all.sh <run-name>` runs it for every tool.

```sh
./bench-memory.sh <run-name> ssao/rau/launch.sh rau-bin.exe
```

To read every tool of a run back as one table:

```sh
awk 'FNR == 1 && NR != 1 { next } { print }' ssao/*/results/<run-name>/*-memory.csv
```
