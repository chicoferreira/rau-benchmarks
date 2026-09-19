"""Record a Chrome trace of each tool drawing the shadow mapping scene, and
read the per-frame CPU cost from them with analyze-traces.py.

usage: python web-shadow-mapping/bench-traces.py <run-name>

Each trace covers 35 seconds of a scene already running, in a fresh Chrome
driven by Playwright, the first 5 of which analyze-traces.py throws away:

- Rau on WebGPU, the project in shadow-mapping/, served as
  web-load-save/rau_site.py describes;
- Rau on WebGL2, the same page with `backend=webgl2`;
- SHADERed, the same scene rebuilt at 1080p, published at shadered.org, so this
  one needs the network to load, though not to draw.

Writes the traces and traces.csv to results/<run-name>. The traces are not
published, as they record the rest of the browser too.
"""

import gzip
import importlib.util
import shutil
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

here = Path(__file__).parent
sys.path.insert(0, str(here.parent / "web-load-save"))
from rau_site import serve_project, start

spec = importlib.util.spec_from_file_location("analyze_traces", here / "analyze-traces.py")
analyze_traces = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analyze_traces)

SHADERED = "https://shadered.org/app?fork=VUABxWMySb"
# The events analyze-traces.py reads: FireAnimationFrame and GPUTask.
CATEGORIES = ["devtools.timeline", "disabled-by-default-devtools.timeline"]
SETTLE_MS = 5_000
TRACE_MS = 35_000

run_name = sys.argv[1]
out_dir = here / "results" / run_name
out_dir.mkdir(parents=True, exist_ok=True)

site = start()
project = here / "shadow-mapping"


def trace(browser, page, name):
    """Let the scene settle, then record a trace of it to results/<run>/<name>.json.gz."""
    print(f"Tracing {name}", file=sys.stderr, flush=True)
    page.wait_for_timeout(SETTLE_MS)

    raw = out_dir / f".{name}.json"
    browser.start_tracing(path=raw, categories=CATEGORIES)
    page.wait_for_timeout(TRACE_MS)
    browser.stop_tracing()

    path = out_dir / f"{name}.json.gz"
    with raw.open("rb") as source, gzip.open(path, "wb") as target:
        shutil.copyfileobj(source, target)
    raw.unlink()
    return path


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(channel="chrome", headless=False)
    viewport = {"width": 1920, "height": 1080}
    traces = []

    # Created into IndexedDB first, then opened from there, so GitHub stays
    # out of it.
    context = browser.new_context(viewport=viewport)
    page = context.new_page()
    with page.expect_console_message(lambda message: "Opened project in" in message.text):
        page.goto(site + serve_project(context, project))

    for name, query in (("rau-webgpu", ""), ("rau-webgl2", "&backend=webgl2")):
        with page.expect_console_message(lambda message: "Opened project in" in message.text):
            page.goto(f"{site}?action=open&project={project.name}{query}")
        traces.append(trace(browser, page, name))
    context.close()

    context = browser.new_context(viewport=viewport)
    page = context.new_page()
    page.goto(SHADERED)
    # SHADERed opens with the code of its six shaders in a tab each, which Rau
    # does not show, so they are closed with the tabs' close button, one per
    # click, leaving the preview in their place.
    page.wait_for_timeout(SETTLE_MS)
    for _ in range(6):
        page.mouse.click(780, 39)
        page.wait_for_timeout(300)
    traces.append(trace(browser, page, "shadered"))
    context.close()

    version = browser.version
    browser.close()

rows = [f"# chrome {version}", "trace,avg_ms,p95_ms,frames"]
for path in traces:
    avg, p95, frames = analyze_traces.cost(path)
    rows.append(f"{path.name.removesuffix('.json.gz')},{avg:.3f},{p95:.3f},{frames}")
    print(rows[-1], flush=True)

(out_dir / "traces.csv").write_text("\n".join(rows) + "\n", encoding="utf-8")
