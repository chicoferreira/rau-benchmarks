"""Time what the generated copy projects cost to load and to save in a web build
of Rau, the way copies/bench-load-save.py does on the desktop, in a fresh
Chrome driven by Playwright, over a number of launches the first of which is
discarded.

usage: python web-load-save/bench.py <run-name> [runs] [copies ...]

Each launch opens the project in Rau's benchmark mode, from the URL. The load
is timed by stamping the lines the application logs on its way up, in the
page's own clock, which starts when the navigation does. The save is typed
into the page once the project is ready, and read from the spans of the
capture the page downloads after that.

The build is served as rau_site.py describes, or RAU_SITE points at another
page, such as https://rau.chicoferreira.dev/.

Writes load.csv to results/<run-name>.
"""

import csv
import statistics
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

from rau_site import serve_project, start

SITE = start()

# The same capture as the desktop: the load, then a window long enough to
# cover a save, with no warm-up.
BENCHMARK = (
    "benchmark=capture.csv&benchmark-load=loading.csv"
    "&benchmark-warmup-seconds=0&benchmark-seconds=2"
)
TIMEOUT_MS = 120_000

LOADING = ("Selected renderer backend:", "Opened project in", "Recorded the load")

STAMP_LOGS = """
window.__logs = [];
for (const level of ["log", "info", "warn", "error"]) {
  const original = console[level];
  console[level] = (...args) => {
    window.__logs.push([performance.now(), level, args.join(" ")]);
    original.apply(console, args);
  };
}
"""

here = Path(__file__).parent
copies_dir = here.parent / "copies"
run_name, *arguments = sys.argv[1:]
runs = int(arguments[0]) if arguments else 10
every_copies = arguments[1:] or ["10", "100", "1000"]

out_dir = here / "results" / run_name
out_dir.mkdir(parents=True, exist_ok=True)


def stamp(page, text):
    """When the app first logged a line containing `text`, in ms since navigation."""
    found = page.wait_for_function(
        "text => window.__logs.find(([, , line]) => line.includes(text))?.[0]",
        arg=text,
        timeout=TIMEOUT_MS,
    )
    return found.json_value()


def read_saving(capture):
    """How long the save, its serialization and its write took, in milliseconds.

    The write to IndexedDB starts on the main thread, in the first poll of the
    save's job, so its part of the frame is the `consume task` of "save file".
    """
    save = serialize = write = 0.0

    with open(capture, encoding="utf-8") as file:
        for row in csv.DictReader(line for line in file if not line.startswith("#")):
            duration = int(row["duration_ns"]) / 1e6
            if row["scope"] == "ProjectSaveState::save":
                save += duration
            elif row["scope"] == "Project::serialize":
                serialize += duration
            elif row["scope"] == "consume task" and row["data"] == "save file":
                write += duration

    return [save, serialize, write]


def launch(page, project):
    """The startup, open, build, save, serialize and write times of one launch."""
    # Leaving through a blank page gives each launch a fresh page process, as
    # each desktop launch is a fresh process. Navigating straight from the last
    # launch would make this one wait on tearing that one down, longer the
    # larger its project.
    page.goto("about:blank")
    page.wait_for_timeout(1000)

    # The load capture is downloaded once the project is built.
    with page.expect_download(timeout=TIMEOUT_MS):
        page.goto(f"{SITE}?action=open&project={project}&{BENCHMARK}")
    stamps = [0.0] + [stamp(page, line) for line in LOADING]

    # The same pause as the desktop before the save.
    page.wait_for_timeout(100)
    with page.expect_download(timeout=TIMEOUT_MS) as capture:
        page.keyboard.press("Control+s")

    for _, level, line in page.evaluate("window.__logs"):
        if level == "error":
            print(f"  console error: {line}", file=sys.stderr, flush=True)

    loads = [end - start for start, end in zip(stamps, stamps[1:])]
    return loads + read_saving(capture.value.path())


header = (
    "copies,runs,startup_ms,open_ms,build_ms,ready_ms,total_ms,"
    "save_ms,serialize_ms,write_ms"
)
rows = [header]
print(header, flush=True)

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(channel="chrome", headless=False)

    for copies in every_copies:
        project = f"shadow-mapping-{copies}"
        print(f"Recording {runs} launches of {project}", file=sys.stderr, flush=True)

        # A context keeps its IndexedDB and HTTP cache across navigations, and
        # starts empty. Creating the project there fills both, so no launch
        # reaches GitHub or the network.
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        context.add_init_script(STAMP_LOGS)
        page = context.new_page()
        page.goto(SITE + serve_project(context, copies_dir / project))
        stamp(page, "Opened project in")

        # The first launch is a warm-up.
        launches = [launch(page, project) for _ in range(runs + 1)][1:]
        context.close()

        startup, opened, build, save, serialize, write = map(
            statistics.fmean, zip(*launches)
        )

        rows.append(
            f"{copies},{runs},{startup:.1f},{opened:.1f},{build:.1f},"
            f"{opened + build:.1f},{startup + opened + build:.1f},"
            f"{save:.1f},{serialize:.1f},{write:.1f}"
        )
        print(rows[-1], flush=True)

    browser.close()

(out_dir / "load.csv").write_text("\n".join(rows) + "\n", encoding="utf-8")
