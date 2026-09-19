"""Record where Rau's frame goes on the shadow mapping project in
shadow-mapping/, on the desktop and in the browser, with Rau's own benchmark
mode on both: 30 seconds of frames after 10 of warm-up, as
copies/bench-internal.sh does.

usage: python web-shadow-mapping/bench-frames.py <run-name>

The browser cannot turn v-sync off, so the desktop keeps it on as well, and
both sides idle between frames the same way. The browser side runs in a fresh
Chrome driven by Playwright, with the build served as
web-load-save/rau_site.py describes.

Writes native-internal.csv and web-internal.csv to results/<run-name>.
"""

import os
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

here = Path(__file__).parent
sys.path[:0] = [str(here.parent / "copies"), str(here.parent / "web-load-save")]
from aggregate_spans import aggregate
from rau_site import serve_project, start

project = here / "shadow-mapping"
run_name = sys.argv[1]
out_dir = here / "results" / run_name
out_dir.mkdir(parents=True, exist_ok=True)

print("Recording shadow-mapping frame spans on the desktop", file=sys.stderr, flush=True)
raw = out_dir / ".native-raw.csv"
subprocess.run(
    # fmt: off
    [os.environ.get("RAU_BIN", "rau"), "open", str(project),
     "--present-mode", "auto-vsync",
     "--window-width", "1920", "--window-height", "1080",
     "--backend", "dx12",
     "--benchmark", str(raw),
     "--benchmark-seconds", "30",
     "--benchmark-warmup-seconds", "10"],
    # fmt: on
    check=True,
)
aggregate(raw, out_dir / "native-internal.csv")
raw.unlink()

print("Recording shadow-mapping frame spans in the browser", file=sys.stderr, flush=True)
site = start()
with sync_playwright() as playwright:
    browser = playwright.chromium.launch(channel="chrome", headless=False)
    context = browser.new_context(viewport={"width": 1920, "height": 1080})
    page = context.new_page()

    # Created into IndexedDB first, so the capture opens it from there as the
    # desktop opens it from its folder, and GitHub stays out of it.
    with page.expect_console_message(lambda message: "Opened project in" in message.text):
        page.goto(site + serve_project(context, project))

    with page.expect_download(timeout=120_000) as frames:
        page.goto(
            f"{site}?action=open&project={project.name}"
            "&benchmark=frames.csv&benchmark-warmup-seconds=10&benchmark-seconds=30"
        )
    aggregate(frames.value.path(), out_dir / "web-internal.csv")
    browser.close()
