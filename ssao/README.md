# SSAO benchmark

The same SSAO scene drawn in Rau, in Rau's focus view, in Nau3D, in SHADERed, and in a baseline program written directly against WGPU. Each tool's folder holds a `launch.sh` that starts it with the scene open and v-sync off, in a 1920x1080 window with the scene drawn at a fixed 640x360. The low resolution makes the benchmark CPU-bound to test the editor's performance more accurately. The Nau3D and SHADERed folders also list, in their own `README.md`, how their version of the scene differs from Rau's.

The commands below are run from the root of this repository.

## Running

`bench.sh` takes the run name, the script that launches the tool, and the process name PresentMon attaches to.

```sh
./bench.sh <run-name> ssao/baseline/launch.sh ssao-baseline.exe
./bench.sh <run-name> ssao/rau/launch.sh rau.exe
./bench.sh <run-name> ssao/rau-focused/launch.sh rau.exe
./bench.sh <run-name> ssao/nau3d/launch.sh composerImGui.exe
./bench.sh <run-name> ssao/shadered/launch.sh SHADERed.exe
```

Each launch waits 10 seconds, records 30 seconds of frames with PresentMon, then reads how much memory the tool holds at that point, before closing it. The memory is read only after the frames are recorded.

## Output

Both files go to `ssao/<tool>/results/<run-name>/`:

- `<tool>-ssao.csv`, the average and percentiles of each PresentMon metric, `CPUBusy` and `GPUBusy` among them. PresentMon is piped into `aggregate-presentmon.py`, so only this summary is kept. `KEEP_RAW=1` also keeps the per-frame capture, `<tool>-ssao-raw.csv`, which can be summarised again with `python aggregate-presentmon.py <raw.csv> <summary.csv>`.
- `<tool>-ssao-memory.csv`, one row with the memory held in RAM (working set), the memory asked for (private bytes), and the dedicated GPU memory (Windows' `GPU Process Memory` counter), summed over every process of the tool.

Two runs of one tool are compared with:

```sh
python compare.py ssao/rau/results/<run-name> ssao/rau/results/<other-run-name>
```

And every tool's memory of a run is read as one table with:

```sh
awk 'FNR == 1 && NR != 1 { next } { print }' ssao/*/results/<run-name>/*-memory.csv
```
