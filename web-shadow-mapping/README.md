# Shadow Mapping in the Web

What Rau's frame costs in the browser, against Rau on the desktop and against SHADERed. SHADERed's browser build cannot upload models, so the SSAO scene of the desktop benchmarks cannot be built there, and the shadow mapping example is used instead.

## Requirements

Python 3 with [Playwright](https://playwright.dev/python/) (`pip install playwright`), Google Chrome, `rau` on the `PATH` built in the `dist` profile, and the web version built as described in `../web-load-save/README.md`, whose `rau_site.py` serves it. SHADERed's page is loaded from shadered.org, so the traces need to be connected to the network.

## The project

`shadow-mapping/` is Rau's [shadow mapping project](https://github.com/chicoferreira/rau/tree/main/projects/shadow-mapping) with two changes:

- The scene is drawn at a fixed 1920x1080 and scaled to fit its viewport, as SHADERed's version is. Its dimension is fixed and the scene viewport is not linked to it.
- The shadow map is read through a comparison sampler instead of `textureLoad`, which WebGL2 cannot do on a depth texture. Each tap still lands on the same texel, so the image is the same.

Both scripts create it in IndexedDB first, served as if it were on GitHub, and open it from there.

## Desktop against web

```sh
python web-shadow-mapping/bench-frames.py <run-name>
```

Opens the project in Rau's benchmark mode once on the desktop and once in Chrome, each time discarding 10 seconds and recording 30, as `../copies/bench-internal.sh` does. The browser cannot turn v-sync off, so the desktop keeps it on as well. Every span is averaged by `../copies/aggregate_spans.py` into `results/<run-name>/native-internal.csv` and `web-internal.csv`.

## Rau against SHADERed

```sh
python web-shadow-mapping/bench-traces.py <run-name>
```

Records a 35-second Chrome trace of each of these, after letting it run for 5 seconds:

- Rau on WebGPU;
- Rau on WebGL2, the same page with `backend=webgl2`;
- SHADERed, the same scene rebuilt at 1080p, published at https://shadered.org/app?fork=VUABxWMySb. It opens with the code editor opened, so a script closes it by clicking their close button, so the preview is similar to Rau's.

Chrome paces a page to the display's refresh rate, so the tools cannot be compared on how many frames they draw. What is compared instead is the CPU cost of a frame. `analyze-traces.py` takes each frame's `FireAnimationFrame`, where the page draws, together with the `GPUTask`s Chrome's GPU process runs for that page until the next frame starts, and discards the first 5 seconds. The traces are kept in `results/<run-name>/` and summarised in `traces.csv` there. They are not published, since a Chrome trace also records the rest of the browser.

Any trace saved from the Performance panel can be read the same way:

```sh
python web-shadow-mapping/analyze-traces.py <trace.json.gz>
```
