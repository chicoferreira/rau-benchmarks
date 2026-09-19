"""Time what the generated copy projects cost to load and to save, and break the
load down by span, over a number of launches the first of which is discarded.

usage: python copies/bench-load-save.py <run-name> [runs] [copies ...]

One launch answers both. The load is timed by stamping the lines the
application logs on its way up, and recorded into a capture of its own. The save
is typed into the window once the project is ready, and read from the spans it
leaves in the frames after that.

Writes load.csv and a summary of the load's spans to results/<run-name>.
"""

import csv
import ctypes
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path

from aggregate_spans import aggregate

# Long enough to cover a save, which is all the window is for.
WINDOW_SECONDS = "2"

LOADING = ("Selected renderer backend:", "Opened project in", "Recorded the load")
SAVING = ("ProjectSaveState::save", "Project::serialize", "write file")

here = Path(__file__).parent
run_name, *arguments = sys.argv[1:]
runs = int(arguments[0]) if arguments else 10
every_copies = arguments[1:] or ["10", "100", "1000"]

out_dir = here / "results" / run_name
out_dir.mkdir(parents=True, exist_ok=True)


def press_save(project):
    """Type ctrl+S into the window of the launch, which saves it right away."""
    user32 = ctypes.windll.user32
    window = user32.FindWindowW(None, f"Rau - {project.name}")
    user32.SetForegroundWindow(window)

    for key, released in ((0x11, 0), (0x53, 0), (0x53, 2), (0x11, 2)):
        user32.keybd_event(key, 0, released, 0)


def read_saving(capture):
    """How long each of the scopes a save is made of took, in milliseconds."""
    totals = dict.fromkeys(SAVING, 0.0)

    with open(capture, encoding="utf-8") as file:
        for row in csv.DictReader(line for line in file if not line.startswith("#")):
            if row["scope"] in totals:
                totals[row["scope"]] += int(row["duration_ns"]) / 1e6

    return list(totals.values())


def launch(project, capture, loading):
    """The startup, open, build, save, serialize and write times of one launch."""
    stamps = [time.perf_counter()]

    process = subprocess.Popen(
        # fmt: off
        [os.environ.get("RAU_BIN", "rau-bin"), "open", str(project),
         "--present-mode", "auto-no-vsync",
         "--window-width", "1920", "--window-height", "1080",
         "--backend", "dx12",
         "--benchmark", str(capture),
         "--benchmark-load", str(loading),
         "--benchmark-warmup-seconds", "0",
         "--benchmark-seconds", WINDOW_SECONDS],
        # fmt: on
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    # Reading to the end of the output is what waits for the window to close.
    for line in process.stderr:
        if len(stamps) <= len(LOADING) and LOADING[len(stamps) - 1] in line:
            stamps.append(time.perf_counter())
            if len(stamps) > len(LOADING):
                # The frame the window opens on is thrown away, so let the
                # save land after it rather than in it.
                time.sleep(0.1)
                press_save(project)

    process.wait()

    loads = [(end - start) * 1000 for start, end in zip(stamps, stamps[1:])]
    return loads + read_saving(capture)


header = (
    "copies,runs,startup_ms,open_ms,build_ms,ready_ms,total_ms,"
    "save_ms,serialize_ms,write_ms"
)
rows = [header]
print(header, flush=True)

for copies in every_copies:
    project = here / f"shadow-mapping-{copies}"
    capture = out_dir / f".{project.name}-capture.csv"
    loading = out_dir / f".{project.name}-loading.csv"
    spans = out_dir / f".{project.name}-loading-raw.csv"

    print(f"Recording {runs} launches of {project.name}", file=sys.stderr, flush=True)

    spans.write_text("", encoding="utf-8")
    launches = []

    for index in range(runs + 1):
        times = launch(project, capture, loading)

        # The first launch is a warm-up, and only the first one kept keeps
        # its header.
        if index == 0:
            continue

        launches.append(times)
        recorded = loading.read_text(encoding="utf-8").splitlines(keepends=True)
        if index > 1:
            recorded = [line for line in recorded if not line.startswith("#")][1:]

        with spans.open("a", encoding="utf-8") as file:
            file.writelines(recorded)

    aggregate(spans, out_dir / f"{project.name}-loading.csv", runs)

    for temporary in (capture, loading, spans):
        temporary.unlink()

    startup, opened, build, save, serialize, write = map(
        statistics.fmean, zip(*launches)
    )

    rows.append(
        f"{copies},{runs},{startup:.1f},{opened:.1f},{build:.1f},"
        f"{opened + build:.1f},{startup + opened + build:.1f},"
        f"{save:.1f},{serialize:.1f},{write:.1f}"
    )
    print(rows[-1], flush=True)

(out_dir / "load.csv").write_text("\n".join(rows) + "\n", encoding="utf-8")
