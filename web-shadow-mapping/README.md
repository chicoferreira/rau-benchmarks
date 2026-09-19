# Shadow Mapping Benchmark in the Web

SHADERed's browser build cannot upload models, so the SSAO scene the desktop benchmarks use cannot be built there. The shadow mapping example is used instead.

Chrome paces a page to the display's refresh rate, so the tools cannot be compared on how many frames they produce. It can be turned off with a command line flag, but the page is then allowed to run ahead of the GPU and the rate it reports stops meaning anything. What is compared instead is the CPU cost of one frame.

## The traces

- Rau on WebGPU, the featured [shadow mapping project](https://github.com/chicoferreira/rau/tree/main/projects/shadow-mapping) with its render texture fixed to 1080p.
- Rau on WebGL2, the same page with `backend=webgl2`.
- SHADERed, the same scene rebuilt at 1080p, published at https://shadered.org/app?fork=VUABxWMySb.

All three were captured with the Chrome Performance panel on an already running scene, for at least 30 seconds, in Chrome 152.0.7977.65, on the same machine as the desktop benchmarks (see `../README.md`). The traces are not published, since a Chrome trace also records the rest of the browser, such as its other tabs and extensions. `analyze-traces.py` reads them from the `results` folder.

## Results

Per-frame CPU cost in milliseconds, from `python analyze-traces.py`, discarding the first 5 seconds of each trace.

| | avg | p95 | frames |
| --- | --- | --- | --- |
| Rau, WebGPU | 0.757 | 0.912 | 4195 |
| Rau, WebGL2 | 0.916 | 1.062 | 5593 |
| SHADERed, WebGL2 | 1.137 | 1.234 | 4188 |
