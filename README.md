# Rau benchmarks

The benchmarks behind the performance analysis of the dissertation on [Rau](https://github.com/chicoferreira/rau).

- `ssao/` draws the same SSAO scene in Rau, in Nau3D, in SHADERed, and in a baseline program written directly against WGPU, and compares their CPU time, GPU time and memory. `ssao/nau3d/README.md` and `ssao/shadered/README.md` list how those two versions of the scene differ from Rau's.
- `copies/` measures how Rau's frame, load and save times grow as a project holds 10, 100 and 1000 copies of the shadow mapping example.
- `web-load-save/` measures the same load and save times in the browser.
- `web-shadow-mapping/` measures Rau's frame on the shadow mapping scene in the browser, against Rau on the desktop and against SHADERed.

## Requirements

The desktop benchmarks run on Windows, from a Bash shell such as Git Bash, with Python 3 and these on the `PATH`:

- `rau`, built from the Rau repository in the `dist` profile;
- `PresentMon-2.5.1-x64`, [PresentMon](https://github.com/GameTechDev/PresentMon) 2.5.1;
- `composerImGui`, from the [Nau3D](https://github.com/Nau3D/nau) release;
- `SHADERed.exe`, [SHADERed](https://github.com/dfranx/SHADERed) 1.5.6.

The baseline program is built with Cargo from `ssao/baseline/`.

The browser benchmarks also need Google Chrome, [Playwright](https://playwright.dev/python/) for Python (`pip install playwright`), and the web version built in the Rau repository next to this one with `./web/build-web.sh`, with `wasm-opt` on the `PATH` (`web-load-save/README.md`). SHADERed's browser version is loaded from shadered.org, so it needs network access.

## Results

Unless stated otherwise, recorded on the main machine, an AMD Ryzen 7 7700X with 32 GB of DDR5-6000 and an AMD Radeon RX 9070 XT, Windows 11 Pro 26H2 (build 26300.9711), driver 32.0.31041.1004. Rau was run with version 0.1.3, on the DX12 backend on the desktop and in Chrome 155.0.8059.80 in the browser.

### SSAO on the desktop

| Tool                  | CPU avg | CPU p95 | GPU avg | GPU p95 | Working set | Private bytes | VRAM |
| --------------------- | ------- | ------- | ------- | ------- | ----------- | ------------- | ---------- |
| Baseline, DX12        | 0.153 ms | 0.228 ms | 0.149 ms | 0.193 ms | 138 MiB | 281 MiB | 230 MiB |
| Rau, DX12             | 0.343 ms | 0.374 ms | 0.252 ms | 0.330 ms | 239 MiB | 420 MiB | 233 MiB |
| Rau, DX12, focus view | 0.223 ms | 0.267 ms | 0.198 ms | 0.272 ms | 258 MiB | 438 MiB | 233 MiB |
| Nau3D, OpenGL         | 0.221 ms | 0.260 ms | 0.174 ms | 0.229 ms | 101 MiB | 360 MiB | 247 MiB |
| SHADERed, OpenGL      | 0.128 ms | 0.197 ms | 0.127 ms | 0.160 ms | 148 MiB | 377 MiB | 224 MiB |

The scene is drawn at 640x360 in a 1920x1080 window (`ssao/README.md`). Times are PresentMon's `CPUBusy` and `GPUBusy`. SHADERed's GPU is still busy for its whole frame, so its CPU time is an upper bound. The memory columns are read once, after the frames are recorded.

### Frame cost as a project grows

Average time of a frame in Rau, with the shadow mapping example copied 10, 100 and 1000 times into one project and only one copy drawn. Each indented row is part of the less indented row above it.

|  | 250 resources | 2,500 resources | 25,000 resources |
| --- | ---: | ---: | ---: |
| Frame | 0.355 ms | 0.516 ms | 2.244 ms |
| &emsp;Interface | 0.102 ms | 0.208 ms | 1.349 ms |
| &emsp;&emsp;Viewport tabs | 0.018 ms | 0.094 ms | 0.906 ms |
| &emsp;&emsp;Resource tree | 0.046 ms | 0.074 ms | 0.360 ms |
| &emsp;&emsp;Status bar | 0.007 ms | 0.008 ms | 0.025 ms |
| &emsp;&emsp;Remaining panels | 0.031 ms | 0.034 ms | 0.058 ms |
| &emsp;Engine | 0.108 ms | 0.162 ms | 0.714 ms |
| &emsp;&emsp;Sync step | 0.003 ms | 0.012 ms | 0.110 ms |
| &emsp;&emsp;Save check | 0.002 ms | 0.015 ms | 0.157 ms |
| &emsp;&emsp;Presentation errors | 0.002 ms | 0.013 ms | 0.125 ms |
| &emsp;&emsp;Submitted revision | 0.002 ms | 0.013 ms | 0.130 ms |
| &emsp;&emsp;Camera update | 0.001 ms | 0.006 ms | 0.062 ms |
| &emsp;&emsp;Encoding and submission | 0.068 ms | 0.070 ms | 0.086 ms |
| &emsp;&emsp;Other | 0.031 ms | 0.032 ms | 0.043 ms |
| &emsp;Painting (`eframe`) | 0.102 ms | 0.103 ms | 0.131 ms |

### Frame cost on other machines

The same frame cost on other machines, each with Rau 0.1.3 on its native backend.

| Machine | CPU | Memory | OS | Backend | 250 resources | 2,500 resources | 25,000 resources |
| --- | --- | --- | --- | --- | ---: | ---: | ---: |
| Main machine | Ryzen 7 7700X | DDR5-6000 | Windows 11 | DX12 | 0.318 ms | 0.477 ms | 2.197 ms |
| Desktop | Ryzen 9 9900X | DDR5-6000 | Arch Linux | Vulkan | 0.355 ms | 0.558 ms | 1.847 ms |
| MacBook Pro | Apple M1 Pro | LPDDR5-6400 | macOS | Metal | 1.012 ms | 1.113 ms | 2.685 ms |
| ThinkPad E14 Gen 7 | Ryzen 7 250 | DDR5-5600 | Windows 11 | DX12 | 1.116 ms | 1.539 ms | 4.232 ms |
| ThinkPad X13 Gen 1 | Ryzen 7 PRO 4750U | LPDDR4X-4266 | NixOS | Vulkan | 1.139 ms | 1.598 ms | 5.312 ms |
| TUF FX505DY | Ryzen 5 3550H | DDR4-2400 | Windows 10 | DX12 | 1.319 ms | 1.753 ms | 7.191 ms |

Wayland paces Rau to the display's refresh rate (144 Hz on the Ryzen 9 9900X desktop, 60 Hz on the X13), and macOS held the M1 Pro at about 360 fps by blocking on its next drawable, so on every machine the frame here leaves out the `get_current_texture` and `present` spans. This is why the main machine's row is below the frame in *Frame cost as a project grows*.

Because of the pacing, the Ryzen 9 9900X is slower than the main machine on the smaller projects, since it idles most of each frame and likely starts the next one at a lower clock and with colder caches.

### Loading and saving as a project grows

The same projects, launched with the project opened and then saved.

|  | 250 resources | 2,500 resources | 25,000 resources |
| --- | ---: | ---: | ---: |
| Launch | 354.5 ms | 454.6 ms | 1,679.1 ms |
| &emsp;Startup | 249.9 ms | 249.3 ms | 248.8 ms |
| &emsp;Load | 104.6 ms | 205.2 ms | 1,430.4 ms |
| &emsp;&emsp;Opening the project | 37.9 ms | 39.6 ms | 56.0 ms |
| &emsp;&emsp;Building the resources | 66.7 ms | 165.7 ms | 1,374.3 ms |
| Save | 0.7 ms | 5.7 ms | 60.2 ms |
| &emsp;Serializing the project | 0.7 ms | 5.7 ms | 60.0 ms |

### Breakdown of building time per resource kind

Largest project only. `Building` is the resources' own build, `Deciding` the rest of the sync step. Viewports are not synced, hence 23,000 of 25,000 resources.

| Resource | Count | Sync step | Building | Deciding |
| --- | ---: | ---: | ---: | ---: |
| Shader | 2,000 | 647.542 ms | 647.024 ms | 0.518 ms |
| Render pipeline | 2,000 | 395.279 ms | 374.931 ms | 20.349 ms |
| Texture view | 4,000 | 87.561 ms | 23.387 ms | 64.174 ms |
| Bind group | 3,000 | 74.165 ms | 4.644 ms | 69.521 ms |
| Uniform | 2,000 | 56.093 ms | 30.431 ms | 25.663 ms |
| Texture | 4,000 | 39.082 ms | 33.087 ms | 5.996 ms |
| Render pass | 2,000 | 14.139 ms | 0.301 ms | 13.837 ms |
| Camera | 2,000 | 3.131 ms | 0.178 ms | 2.952 ms |
| Dimension | 2,000 | 0.198 ms | 0.053 ms | 0.145 ms |
| Model | 0 | 0.003 ms | 0.000 ms | 0.003 ms |
| Sampler | 0 | 0.001 ms | 0.000 ms | 0.001 ms |
| Compute pass | 0 | 0.000 ms | 0.000 ms | 0.000 ms |
| **Total** | **23,000** | **1,317.194 ms** | **1,114.035 ms** | **203.159 ms** |

### Loading and saving in the browser

The same load and save times, in the web build (`web-load-save/`).

|  | 250 resources | 2,500 resources | 25,000 resources |
| --- | ---: | ---: | ---: |
| Launch | 402.6 ms | 574.4 ms | 3,829.3 ms |
| &emsp;Startup | 159.3 ms | 153.1 ms | 159.1 ms |
| &emsp;Load | 243.3 ms | 421.3 ms | 3,670.2 ms |
| &emsp;&emsp;Opening the project | 104.1 ms | 110.2 ms | 153.0 ms |
| &emsp;&emsp;Building the resources | 139.2 ms | 311.0 ms | 3,517.2 ms |
| Save | 3.1 ms | 11.4 ms | 88.6 ms |
| &emsp;Serializing the project | 2.0 ms | 10.4 ms | 87.4 ms |
| Handing the file to IndexedDB | 0.5 ms | 1.2 ms | 10.9 ms |

### Shadow mapping on the desktop and in the browser

Average time of a frame in Rau on the shadow mapping scene, from Rau's own profiler on both sides (`web-shadow-mapping/bench-frames.py`), with v-sync on, as the browser cannot turn it off.

|  | Desktop | Browser |
| --- | ---: | ---: |
| Frame | 0.286 ms | 0.383 ms |
| &emsp;Interface | 0.138 ms | 0.259 ms |
| &emsp;&emsp;Viewport tabs | 0.011 ms | 0.022 ms |
| &emsp;&emsp;Resource tree | 0.068 ms | 0.132 ms |
| &emsp;&emsp;Status bar | 0.010 ms | 0.017 ms |
| &emsp;&emsp;Remaining panels | 0.048 ms | 0.088 ms |
| &emsp;Engine | 0.148 ms | 0.119 ms |
| &emsp;&emsp;Encoding and submission | 0.098 ms | 0.063 ms |
| &emsp;&emsp;Other | 0.050 ms | 0.056 ms |

### Shadow mapping in the browser, against SHADERed

Per-frame CPU time, from Chrome traces recorded by `web-shadow-mapping/bench-traces.py` and read by `web-shadow-mapping/analyze-traces.py`.

| Tool             |   avg |   p95 |
| ---------------- | ----- | ----- |
| Rau, WebGPU      | 0.727 ms | 0.811 ms |
| Rau, WebGL2      | 0.910 ms | 1.061 ms |
| SHADERed, WebGL2 | 0.987 ms | 1.122 ms |

## Running everything

The shadow mapping copy projects have to be generated first, as described in `copies/README.md`. Then, from the root of this repository:

```sh
./bench-all.sh <run-name>
```

It runs every benchmark in turn, first the desktop ones and then the browser ones, and writes their results into a `results/<run-name>/` folder beside each one. Several of them open windows and type or click into them, so the machine should be left alone until it ends. How to run a single benchmark is described in each folder's `README.md`.

## Licence and credits

The scripts are under the MIT licence (`LICENSE.md`). The backpack model (`ssao/backpack.obj`) is [Survival Guitar Backpack](https://sketchfab.com/3d-models/survival-guitar-backpack-low-poly-799f8c4511f84fab8c3f12887f7e6b36) by Berk Gedik, licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), in the version distributed with [LearnOpenGL](https://learnopengl.com/Model-Loading/Model).
